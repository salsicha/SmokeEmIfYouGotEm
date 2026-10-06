#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "RaftSimRaftActor.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "UObject/Script.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSwampedSeatTest, "RaftSim.Rescue.SwampedSeatWashout",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimSwampedSeatTest::RunTest(const FString&)
{
    FEditorScriptExecutionGuard Guard;
    UWorld* World = nullptr;
    for (const auto& C : GEngine->GetWorldContexts()) if (C.WorldType == EWorldType::Editor) { World = C.World(); break; }
    if (!TestNotNull(TEXT("editor world"), World)) return false;
    auto* Raft = World->SpawnActor<ARaftSimRaftActor>();
    ON_SCOPE_EXIT {
        for (TActorIterator<ARaftSimCrewAvatarActor> It(World); It; ++It) if (It->GetOwner() == Raft) World->DestroyActor(*It);
        World->DestroyActor(Raft);
    };
    Raft->InitializeCrewSeatingForValidation();
    auto* Runtime = NewObject<URaftSimChronoRuntimeAdapter>(Raft);
    FRaftSimFlexParameters Flex; Flex.MassKg = 220.; Flex.PassengerCount = 4;
    FRaftSimRaftBodyConfig Body; Body.Runtime = ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;
    Body.MassKg = Flex.TotalMassKg(); Body.InertiaTensorKgM2 = FVector(300, 400, 700);
    Runtime->ConfigureRaftBody(Body);
    Runtime->ConfigureFlexibleRaftModel(Flex, RaftSimFlex::BuildDefaultCrewSeats(Flex), 18000., true);
    if (!TestTrue(TEXT("actual production hull"), Raft->BindIsolatedFeatureHull(Runtime))) return false;
    Runtime->SetWaterSurfaceSampler([](const FVector&, float& H) { H = 0; return true; });

    // Water stands Depth metres over one passenger's hips and moves with the
    // boat (no breaking flow): the seat itself has gone under.
    FVector Hip; double Depth = .3; bool Wet = true;
    const auto Seat = [&](FName Id) {
        const auto* A = Raft->FindAvatar(Id); const auto& P = A->GetPublishedCrewPose();
        Hip = A->GetActorTransform().TransformPosition((P.LeftHipCm + P.RightHipCm) * .5);
    };
    Runtime->SetFlexibleWaterFieldSampler([&](const FVector& P, FRaftSimFlexUniformWater& W) {
        W = {}; W.bWet = Wet; W.SurfaceHeightM = 0.;
        if (FVector::DistSquared2D(P, Hip) < 25.) W.SurfaceHeightM = Hip.Z * .01 + Depth;
        return true;
    });
    const auto Hold = [&](float Seconds) { for (int32 I = 0; I < FMath::RoundToInt(Seconds * 60.f); ++I) Raft->UpdatePassengerWashouts(1.f / 60.f); };

    const FName Front(TEXT("paddler_1"));
    Seat(Front);
    Depth = .3; Hold(3.f);
    TestEqual(TEXT("waist-deep water over the seat does not float anyone off"), Raft->GetSwimmerCount(), 0);
    Depth = .7; Hold(.3f);
    TestEqual(TEXT("a brief chest-deep dunk is ridden out"), Raft->GetSwimmerCount(), 0);
    Wet = false; Hold(1.f); Wet = true;
    Depth = .7; Hold(1.f);
    TestEqual(TEXT("a seat held chest-deep under floats its passenger out"), Raft->GetSwimmerCount(), 1);
    TestTrue(TEXT("the swamped passenger is the one swimming"), Raft->IsPassengerSwimming(Front));
    for (const TCHAR* Other : {TEXT("paddler_2"), TEXT("paddler_3"), TEXT("paddler_4")})
        TestFalse(TEXT("dry seats keep their passengers"), Raft->IsPassengerSwimming(FName(Other)));
    TestTrue(TEXT("still water gives no ejection velocity"),
        Raft->Swimmers.Last().SwimmerDriftVelocityMetersPerSecond.Size() < .01);
    TestEqual(TEXT("the boat need not flip"), Raft->GetRaftMode(), ERaftSimRaftMode::Upright);

    // A passenger braced low with a hand on the line holds on longer.
    const FName Braced(TEXT("paddler_2"));
    Raft->FindAvatar(Braced)->SetAvatarAction(ERaftSimCrewAvatarAction::Brace);
    Seat(Braced);
    Hold(.9f);
    TestFalse(TEXT("bracing outlasts a dunk that would take an unbraced passenger"), Raft->IsPassengerSwimming(Braced));
    Hold(.8f);
    TestTrue(TEXT("but a seat that stays under still loses them"), Raft->IsPassengerSwimming(Braced));
    TestEqual(TEXT("two separate swamped seats, two swimmers"), Raft->GetSwimmerCount(), 2);
    return true;
}
#endif
