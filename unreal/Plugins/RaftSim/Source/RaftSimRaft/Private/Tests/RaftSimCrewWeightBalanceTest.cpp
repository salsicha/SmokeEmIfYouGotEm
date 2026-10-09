#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimRaftActor.h"
#include "UObject/Script.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrewWeightBalanceTest, "RaftSim.Physics.CrewWeightBalance",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

// The production raft on still water: each person's weight bears where they
// sit, so who is aboard, and where, sets how the boat sits.
bool FRaftSimCrewWeightBalanceTest::RunTest(const FString&)
{
    FEditorScriptExecutionGuard ScriptGuard;
    UWorld* World = nullptr;
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
        if (Context.WorldType == EWorldType::Editor) { World = Context.World(); break; }
    if (!TestNotNull(TEXT("editor world"), World)) return false;
    auto* Raft = World->SpawnActor<ARaftSimRaftActor>();
    if (!TestNotNull(TEXT("production raft"), Raft)) return false;
    ON_SCOPE_EXIT
    {
        for (TActorIterator<ARaftSimCrewAvatarActor> It(World); It; ++It) if (It->GetOwner() == Raft) World->DestroyActor(*It);
        World->DestroyActor(Raft);
    };
    Raft->InitializeCrewSeatingForValidation();
    auto* Runtime = NewObject<URaftSimChronoRuntimeAdapter>(Raft);
    Runtime->ConfigureRaftBody(Raft->MakeProductionBodyConfig());
    Raft->ConfigureProductionFlexModel(*Runtime);
    Runtime->SetWaterSurfaceSampler([](const FVector&, float& SurfaceCm) { SurfaceCm = 0.0f; return true; });
    Runtime->SetFlexibleWaterFieldSampler([](const FVector&, FRaftSimFlexUniformWater& Water)
        { Water.bWet = true; Water.SurfaceHeightM = 0.0; Water.VelocityMps = FVector::ZeroVector; return true; });
    Runtime->SetKinematicState(FRaftSimRaftKinematicState{});

    const FRaftSimRaftBodyConfig& Body = Runtime->GetRaftBodyConfig();
    const TArray<FRaftSimFlexCrewSeat> Seats = Runtime->GetFlexibleSeats();
    if (!TestTrue(TEXT("a guide and four paddlers"), Seats.Num() == 5)) return false;
    const FRaftSimFlexStepTelemetry& T = Runtime->GetLastFlexibleStepTelemetry();
    // Degrees the starboard (+Y) tube and the bow stand above level.
    const auto Trim = [Runtime]()
    {
        const FQuat Q = Runtime->GetKinematicState().WorldTransform.GetRotation();
        return FVector2D(FMath::RadiansToDegrees(FMath::Asin(Q.RotateVector(FVector::RightVector).Z)),
            FMath::RadiansToDegrees(FMath::Asin(Q.RotateVector(FVector::ForwardVector).Z)));
    };
    const auto Settle = [&](const TCHAR* Label)
    {
        for (int32 Step = 0; Step < 10 * 120; ++Step)
        {
            if (!Runtime->StepRaftDynamics(1.0f / 120.0f))
            {
                AddError(FString::Printf(TEXT("%s: the raft's step failed"), Label));
                return FVector2D::ZeroVector;
            }
        }
        const FVector2D Sit = Trim();
        AddInfo(FString::Printf(TEXT("%s: starboard %+.2f deg, bow %+.2f deg, mass %.0f kg, centre of mass %s m, inertia %s"),
            Label, Sit.X, Sit.Y, T.IntegratedMassKg, *T.CenterOfMassLocalM.ToString(), *T.IntegratedInertiaKgM2.ToString()));
        return Sit;
    };
    const auto Occupy = [Runtime](const FString& Id, bool bAboard) { Runtime->SetFlexibleCrewSeatOccupied(Id, bAboard); };
    const auto Expected = [&Seats, &Body](TFunctionRef<bool(const FRaftSimFlexCrewSeat&)> Aboard, double& OutMassKg)
    {
        double Mass = Body.MassKg;
        FVector Moment = FVector::ZeroVector;
        for (const FRaftSimFlexCrewSeat& Seat : Seats)
        {
            if (Aboard(Seat)) Moment += Seat.LocalPosition * Seat.OccupantMassKg;
            else Mass -= Seat.OccupantMassKg;
        }
        OutMassKg = Mass;
        return Moment / Mass;
    };

    // Full crew: the guide at the stern on one tube, two rows of paddlers.
    const FVector2D Full = Settle(TEXT("full crew"));
    double FullMass = 0.0;
    const FVector FullCom = Expected([](const FRaftSimFlexCrewSeat&) { return true; }, FullMass);
    TestTrue(TEXT("the centre of mass is the dry hull's centre plus each person at their seat"),
        T.CenterOfMassLocalM.Equals(FullCom, 1.0e-6) && FMath::IsNearlyEqual(T.IntegratedMassKg, FullMass, 1.0e-6));
    TestTrue(TEXT("a full crew at their seats keeps the configured inertia"),
        T.IntegratedInertiaKgM2.Equals(Body.InertiaTensorKgM2, 1.0e-3));
    TestTrue(FString::Printf(TEXT("the boat lists a little to the guide's side (%+.2f deg)"), Full.X),
        Full.X * FullCom.Y < 0.0 && FMath::Abs(Full.X) > 0.1 && FMath::Abs(Full.X) < 3.0);
    TestTrue(FString::Printf(TEXT("and trims within a few degrees fore and aft (%+.2f deg)"), Full.Y), FMath::Abs(Full.Y) < 3.0);

    // The two paddlers on the port (-Y) tube go overboard.
    TArray<FString> Port;
    for (const FRaftSimFlexCrewSeat& Seat : Seats) if (Seat.Role != TEXT("guide") && Seat.LocalPosition.Y < 0.0) Port.Add(Seat.SeatId);
    if (!TestEqual(TEXT("two port paddlers"), Port.Num(), 2)) return false;
    for (const FString& Id : Port) Occupy(Id, false);
    const FVector2D PortOut = Settle(TEXT("port paddlers out"));
    double PortOutMass = 0.0;
    const FVector PortOutCom = Expected([&Port](const FRaftSimFlexCrewSeat& Seat) { return !Port.Contains(Seat.SeatId); }, PortOutMass);
    TestTrue(TEXT("their weight leaves the boat and its centre of mass moves to starboard"),
        T.CenterOfMassLocalM.Equals(PortOutCom, 1.0e-6) && FMath::IsNearlyEqual(T.IntegratedMassKg, FullMass - 150.0, 1.0e-6) &&
        PortOutCom.Y > FullCom.Y + 0.1);
    TestTrue(FString::Printf(TEXT("the lightened port tube rises and starboard sinks (%+.2f -> %+.2f deg)"), Full.X, PortOut.X),
        PortOut.X < Full.X - 0.5);
    for (const FString& Id : Port) Occupy(Id, true);

    // Who leaves sets how much the boat's turning inertia drops: the guide at
    // the stern carries more pitch inertia than a paddler amidships.
    const FRaftSimFlexCrewSeat* Guide = Seats.FindByPredicate([](const FRaftSimFlexCrewSeat& Seat) { return Seat.Role == TEXT("guide"); });
    const FRaftSimFlexCrewSeat* Amidships = nullptr;
    for (const FRaftSimFlexCrewSeat& Seat : Seats)
        if (Seat.Role != TEXT("guide") && (!Amidships || FMath::Abs(Seat.LocalPosition.X) < FMath::Abs(Amidships->LocalPosition.X))) Amidships = &Seat;
    if (!TestTrue(TEXT("a guide and an amidships paddler"), Guide && Amidships)) return false;
    Occupy(Amidships->SeatId, false);
    Runtime->StepRaftDynamics(1.0f / 120.0f);
    const double PitchInertiaWithoutPaddler = T.IntegratedInertiaKgM2.Y;
    Occupy(Amidships->SeatId, true);
    Occupy(Guide->SeatId, false);
    const FVector2D GuideOut = Settle(TEXT("guide out"));
    TestTrue(FString::Printf(TEXT("the guide leaving takes more pitch inertia than a paddler amidships (%.0f < %.0f kg m2)"),
            T.IntegratedInertiaKgM2.Y, PitchInertiaWithoutPaddler),
        T.IntegratedInertiaKgM2.Y < PitchInertiaWithoutPaddler - 50.0);
    TestTrue(FString::Printf(TEXT("without the guide's weight the stern rises (bow %+.2f -> %+.2f deg)"), Full.Y, GuideOut.Y),
        GuideOut.Y < Full.Y - 0.3);
    TestTrue(FString::Printf(TEXT("and the guide's list goes (starboard %+.2f -> %+.2f deg)"), Full.X, GuideOut.X),
        FMath::Abs(GuideOut.X) < FMath::Abs(Full.X));
    Occupy(Guide->SeatId, true);

    // High-side: everyone onto the starboard tube.
    TArray<FRaftSimFlexCrewAction> HighSide;
    for (const FRaftSimFlexCrewSeat& Seat : Seats)
    {
        FRaftSimFlexCrewAction Action;
        Action.SeatId = Seat.SeatId;
        Action.HighSideDirection = 1;
        Action.bUseCrewTransfer = true;
        Action.CrewTransferOffsetM = FVector(0.0, FMath::Abs(Seat.LocalPosition.Y) - Seat.LocalPosition.Y, 0.0);
        HighSide.Add(Action);
    }
    Runtime->SetFlexibleCrewActions(HighSide);
    const FVector2D High = Settle(TEXT("high-side to starboard"));
    TestTrue(FString::Printf(TEXT("a high-side holds the starboard tube down (%+.2f deg) without rolling the boat over"), High.X),
        High.X < Full.X - 1.5 && High.X > -25.0);
    Runtime->SetFlexibleCrewActions({});

    // Everyone out: the empty hull floats level on its own inertia.
    for (const FRaftSimFlexCrewSeat& Seat : Seats) Occupy(Seat.SeatId, false);
    const FVector2D Empty = Settle(TEXT("empty"));
    double CrewKg = 0.0;
    for (const FRaftSimFlexCrewSeat& Seat : Seats) CrewKg += Seat.OccupantMassKg;
    const double DryShare = (Body.MassKg - CrewKg) / Body.MassKg;
    TestTrue(TEXT("the empty hull's centre of mass is its centre"), T.CenterOfMassLocalM.IsNearlyZero(1.0e-9));
    TestTrue(TEXT("and its inertia its own share"), T.IntegratedInertiaKgM2.Equals(Body.InertiaTensorKgM2 * DryShare, 1.0e-3));
    TestTrue(FString::Printf(TEXT("and it floats level (%+.3f, %+.3f deg)"), Empty.X, Empty.Y),
        FMath::Abs(Empty.X) < 0.05 && FMath::Abs(Empty.Y) < 0.05);
    return true;
}
#endif
