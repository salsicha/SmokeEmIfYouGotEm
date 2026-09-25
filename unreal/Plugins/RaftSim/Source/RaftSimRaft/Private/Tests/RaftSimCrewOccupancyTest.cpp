#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimRaftActor.h"
#include "UObject/Script.h"
#include "ProceduralMeshComponent.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrewOccupancyTest,
    "RaftSim.Crew.OccupancyControlsLoadsAndIntegratedMass",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimCrewOccupancyTest::RunTest(const FString&)
{
    FEditorScriptExecutionGuard ScriptGuard;
    UWorld* World = nullptr;
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
        if (Context.WorldType == EWorldType::Editor) { World = Context.World(); break; }
    if (!TestNotNull(TEXT("editor world"), World)) return false;
    auto* Raft = World->SpawnActor<ARaftSimRaftActor>();
    if (!TestNotNull(TEXT("production raft"), Raft)) return false;
    ON_SCOPE_EXIT {
        TArray<AActor*> Owned;
        for (TActorIterator<ARaftSimCrewAvatarActor> It(World); It; ++It)
            if (It->GetOwner() == Raft) Owned.Add(*It);
        for (auto* Actor : Owned) World->DestroyActor(Actor);
        World->DestroyActor(Raft);
    };
    Raft->InitializeCrewSeatingForValidation();
    Raft->SetActorRotation(FRotator(12.f, -137.f, 21.f));
    const auto* FirstAvatar = Raft->FindAvatar(TEXT("paddler_1"));
    if (!TestNotNull(TEXT("first seated avatar"), FirstAvatar)) return false;
    const float EjectionYaw = FirstAvatar->GetActorRotation().Yaw;
    auto* Adapter = NewObject<URaftSimChronoRuntimeAdapter>(Raft);
    Raft->RaftAdapter = Adapter;
    FRaftSimFlexParameters Flex;
    Flex.MassKg = 220.; Flex.PassengerCount = 4;
    FRaftSimRaftBodyConfig Body;
    Body.Runtime = ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;
    Body.MassKg = float(Flex.TotalMassKg());
    Body.InertiaTensorKgM2 = FVector(300, 400, 700);
    Adapter->ConfigureRaftBody(Body);
    Adapter->ConfigureFlexibleRaftModel(Flex, RaftSimFlex::BuildDefaultCrewSeats(Flex), 18000., true);
    const auto Step = [&](double CrewMass) {
        const double ExpectedMass = 220. + CrewMass;
        Adapter->SetKinematicState(FRaftSimRaftKinematicState{});
        Adapter->AddExternalImpulse(FVector(ExpectedMass, 0, 0), FVector::ZeroVector);
        TestTrue(TEXT("real occupied-mass integration succeeds"), Adapter->StepRaftDynamics(1.f / 120.f));
        const auto& T = Adapter->GetLastFlexibleStepTelemetry();
        TestTrue(TEXT("seat-load occupied mass"), FMath::IsNearlyEqual(T.OccupiedCrewMassKg, CrewMass));
        TestTrue(TEXT("integrator uses dry plus occupied mass"), FMath::IsNearlyEqual(T.IntegratedMassKg, ExpectedMass));
        TestTrue(TEXT("impulse response uses actual mass, not merely telemetry"),
            FMath::IsNearlyEqual(Adapter->GetKinematicState().LinearVelocityMetersPerSecond.X, 1.0, 1.e-6));
        TestTrue(TEXT("hull buoyancy capacity does not lose crew-sized volume"),
            FMath::IsNearlyEqual(T.BuoyancyReferenceMassKg, 605.));
        TestTrue(TEXT("documented shape-inertia scale uses current mass"),
            T.IntegratedInertiaKgM2.Equals(Body.InertiaTensorKgM2 * (ExpectedMass / 605.), 1.e-6));
        AddInfo(FString::Printf(TEXT("OCCUPANCY crew=%.0f integrated=%.0f buoyancy_reference=%.0f"),
            T.OccupiedCrewMassKg, T.IntegratedMassKg, T.BuoyancyReferenceMassKg));
    };
    Step(385.);
    Raft->HandleHighSideResponse(-1);
    const auto Before = Adapter->GetKinematicState();
    Raft->ForceCrewOverboardForTesting(2);
    TestEqual(TEXT("two swimmers"), Raft->GetSwimmerCount(), 2);
    const auto* SwimmingAvatar = Raft->FindAvatar(TEXT("paddler_1"));
    TestTrue(TEXT("ejection preserves world heading instead of resetting to world +X"),
        FMath::Abs(FMath::FindDeltaAngleDegrees(SwimmingAvatar->GetActorRotation().Yaw, EjectionYaw)) < .001f);
    TestTrue(TEXT("ejection releases seat tilt for the authored horizontal swim"),
        FMath::Abs(SwimmingAvatar->GetActorRotation().Pitch) < .001f &&
        FMath::Abs(SwimmingAvatar->GetActorRotation().Roll) < .001f);
    const FBox HullBox = Raft->RaftVisual->CalcBounds(Raft->RaftVisual->GetComponentTransform()).GetBox();
    int32 CheckedParts = 0;
    TInlineComponentArray<UPrimitiveComponent*> Parts(SwimmingAvatar);
    for (const UPrimitiveComponent* Part : Parts)
    {
        if (!Part || !Part->IsRegistered() || !Part->IsVisible()) continue;
        const FBox PartBox = Part->CalcBounds(Part->GetComponentTransform()).GetBox();
        if (!PartBox.IsValid) continue;
        ++CheckedParts;
        // The first ejection is world +X. Check every visible component,
        // independently of the production aggregate-box projection.
        TestTrue(TEXT("whole posed swimmer starts beyond the rendered hull, including feet"),
            PartBox.Min.X >= HullBox.Max.X + 4.99);
    }
    TestTrue(TEXT("clearance test covers actual visible body components"), CheckedParts > 0);
    const double DriftZ=Raft->Swimmers[0].SwimmerWorldPositionMeters.Z;
    Raft->Swimmers[0].SwimmerWorldPositionMeters=Raft->GetActorLocation()/100.+FVector(.2,0,0);
    Raft->Swimmers[0].SwimmerWorldPositionMeters.Z=DriftZ;
    Raft->DriftSwimmers(0.f);
    TestEqual(TEXT("hull separation does not lift a swimmer"),Raft->Swimmers[0].SwimmerWorldPositionMeters.Z,DriftZ);
    for(const auto* Part:Parts)
        if(Part && Part->IsRegistered() && Part->IsVisible())
            TestTrue(TEXT("drift restores every visible part beyond the hull"),
                Part->CalcBounds(Part->GetComponentTransform()).GetBox().Min.X>=HullBox.Max.X+4.99);
    const FVector Separated=Raft->Swimmers[0].SwimmerWorldPositionMeters;
    Raft->DriftSwimmers(0.f);
    TestTrue(TEXT("repeated zero-step contact does not creep"),Raft->Swimmers[0].SwimmerWorldPositionMeters.Equals(Separated,1.e-6));
    FVector TubeTarget;
    const FVector StartM = Raft->Swimmers[0].SwimmerWorldPositionMeters;
    TestTrue(TEXT("published hull supplies a pulling target"),
        Raft->GetSwimmerTubeTarget(TEXT("paddler_1"), StartM, TubeTarget));
    TestTrue(TEXT("pull target preserves water elevation"), FMath::IsNearlyEqual(TubeTarget.Z, StartM.Z, 1.e-6));
    const auto* HullSection = Raft->RaftVisual->GetProcMeshSection(0);
    if (!TestNotNull(TEXT("rendered hull section"), HullSection)) return false;
    const FVector SurfaceM = Raft->RaftVisual->GetComponentTransform().TransformPosition(
        HullSection->ProcVertexBuffer[0].Position) / 100.0;
    TestTrue(TEXT("exact published surface has zero hull distance"), Raft->GetRenderedHullDistanceM(SurfaceM) < .0001);
    const auto SavedInteraction = Raft->RescueInteraction;
    Raft->RescueInteraction.TargetPassengerId = TEXT("paddler_1");
    Raft->RescueInteraction.Phase = ERaftSimRescueInteractionPhase::ReadyForReentry;
    Raft->Swimmers[0].SwimmerWorldPositionMeters = SurfaceM + FVector(100,0,0);
    TestFalse(TEXT("ready state cannot board from far outside the actual hull"), Raft->RequestSelectedReentry());
    TestEqual(TEXT("far reentry keeps both swimmers"), Raft->GetSwimmerCount(), 2);
    TestEqual(TEXT("physical distance failure asks for tube contact"),
        Raft->RescueInteraction.FeedbackCode, FName(TEXT("rescue_bring_to_tube")));
    Raft->Swimmers[0].SwimmerWorldPositionMeters = StartM;
    Raft->RescueInteraction = SavedInteraction;
    TestTrue(TEXT("occupancy change preserves body velocity"),
        Adapter->GetKinematicState().LinearVelocityMetersPerSecond == Before.LinearVelocityMetersPerSecond);
    TestFalse(TEXT("ejected seat loses stale action immediately"), Adapter->FlexActions.ContainsByPredicate(
        [](const auto& A) { return A.SeatId == TEXT("passenger_0"); }));
    Raft->IssueCrewCommand(ERaftSimCrewCommand::Rest);
    Raft->UpdateCrew(1.f);
    Step(235.);
    Raft->Swimmers[0].TimeInWaterSeconds = 10.f;
    Raft->RescueInteraction.Phase = ERaftSimRescueInteractionPhase::Pulling;
    Raft->ForceCrewOverboardForTesting(1);
    Raft->ForceCrewOverboardForTesting(0);
    TestEqual(TEXT("repeated/zero ejection does not orphan another swimmer"), Raft->GetSwimmerCount(), 2);
    TestEqual(TEXT("existing rescue clock is preserved"), Raft->Swimmers[0].TimeInWaterSeconds, 10.f);
    TestEqual(TEXT("duplicate event preserves active rescue phase"),
        Raft->RescueInteraction.Phase, ERaftSimRescueInteractionPhase::Pulling);
    Step(235.);
    // Exercise the public successful boarding branch, not just its removal helper.
    // Capture discontinuity separately: occupancy correctness is not animation acceptance.
    const int32 BoardingIndex = Raft->FindSwimmerIndex(TEXT("paddler_1"));
    TestTrue(TEXT("boarding target remains present"), Raft->Swimmers.IsValidIndex(BoardingIndex));
    if (!Raft->Swimmers.IsValidIndex(BoardingIndex)) return false;
    auto* BoardingAvatar = Raft->FindAvatar(TEXT("paddler_1"));
    if (!TestNotNull(TEXT("boarding keeps the existing avatar"), BoardingAvatar)) return false;
    BoardingAvatar->SetAvatarAction(ERaftSimCrewAvatarAction::Reentry);
    TestTrue(TEXT("current reentry pose supplies current tube target"),
        Raft->GetSwimmerTubeTarget(TEXT("paddler_1"), Raft->Swimmers[BoardingIndex].SwimmerWorldPositionMeters, TubeTarget));
    Raft->Swimmers[BoardingIndex].SwimmerWorldPositionMeters = TubeTarget;
    BoardingAvatar->SetActorLocation(TubeTarget * 100.);
    AddInfo(FString::Printf(TEXT("REENTRY_TARGET hull_distance_m=%.9f"), Raft->GetRenderedHullDistanceM(TubeTarget)));
    const FVector BeforeBoarding = BoardingAvatar->GetActorLocation();
    const int32 PreviousRescues = Raft->GetCompletedRescueCount();
    Raft->RescueInteraction.TargetPassengerId = TEXT("paddler_1");
    Raft->RescueInteraction.Phase = ERaftSimRescueInteractionPhase::ReadyForReentry;
    TestTrue(TEXT("ready swimmer at rendered tube boards through public request"), Raft->RequestSelectedReentry());
    TestTrue(TEXT("boarding preserves avatar identity"), Raft->FindAvatar(TEXT("paddler_1")) == BoardingAvatar);
    TestEqual(TEXT("successful public boarding counts exactly one rescue"), Raft->GetCompletedRescueCount(), PreviousRescues + 1);
    TestFalse(TEXT("boarded passenger leaves swimming state"), Raft->IsPassengerSwimming(TEXT("paddler_1")));
    TestTrue(TEXT("boarded visual remains finite"), BoardingAvatar->HasFiniteVisualTransforms());
    AddInfo(FString::Printf(TEXT("REENTRY_DISCONTINUITY elapsed_s=0 root_jump_cm=%.9f"),
        FVector::Distance(BeforeBoarding, BoardingAvatar->GetActorLocation())));
    TestFalse(TEXT("repeat boarding cannot rescue the already boarded passenger"), Raft->RequestSelectedReentry());
    TestEqual(TEXT("repeat boarding does not increment rescue count"), Raft->GetCompletedRescueCount(), PreviousRescues + 1);
    TestEqual(TEXT("one swimmer remains after single reseat"), Raft->GetSwimmerCount(), 1);
    Step(310.);
    Raft->RaftMode = ERaftSimRaftMode::Capsized;
    Adapter->SetFlexibleCapsized(true);
    Raft->SpawnSwimmers(5, true);
    TestEqual(TEXT("capsize adds missing crew without duplicate swimmers"), Raft->GetSwimmerCount(), 5);
    Step(0.);
    Raft->RequestReflip();
    TestEqual(TEXT("real reflip enters recovery"), Raft->GetRaftMode(), ERaftSimRaftMode::Recovering);
    Step(0.);
    Raft->RemoveSwimmerAt(Raft->FindSwimmerIndex(TEXT("guide")));
    Step(85.);
    TestTrue(TEXT("checkpoint restores seated roster"), Raft->TryRestoreCheckpoint(FTransform::Identity));
    TestEqual(TEXT("checkpoint clears swimmers"), Raft->GetSwimmerCount(), 0);
    Step(385.);
    TestFalse(TEXT("unknown physical seat rejected"), Adapter->SetFlexibleCrewSeatOccupied(TEXT("paddler_1"), false));
    Step(385.);
    // Malformed combined-body configuration must not integrate near-zero mass.
    Body.MassKg = 100.f;
    Adapter->ConfigureRaftBody(Body);
    AddExpectedError(TEXT("Invalid combined crew mass contract"), EAutomationExpectedErrorFlags::Contains, 1);
    Adapter->ConfigureFlexibleRaftModel(Flex, RaftSimFlex::BuildDefaultCrewSeats(Flex), 18000., true);
    TestFalse(TEXT("invalid combined mass fails closed"), Adapter->StepRaftDynamics(1.f / 120.f));
    return true;
}
#endif
