#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "HAL/IConsoleManager.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimCrewSeatLayout.h"
#include "RaftSimRaftActor.h"
#include "UObject/Script.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimBackToSeatsTest, "RaftSim.Crew.BackToSeats",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimBackToSeatsTest::RunTest(const FString&)
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
        for (AActor* Actor : Owned) World->DestroyActor(Actor);
        World->DestroyActor(Raft);
    };
    Raft->InitializeCrewSeatingForValidation();
    auto* Adapter = NewObject<URaftSimChronoRuntimeAdapter>(Raft);
    Raft->RaftAdapter = Adapter;
    FRaftSimRaftBodyConfig Body;
    Body.Runtime = ERaftSimRaftDynamicsRuntime::CustomReducedRigidBody;
    Adapter->ConfigureRaftBody(Body);
    FRaftSimFlexParameters Flex;
    Flex.PassengerCount = Raft->PaddlerCount;
    Flex.GuideMassKg = 85.0;
    Flex.PassengerMassKg = 75.0;
    const bool bLeftGuide = IConsoleManager::Get().FindConsoleVariable(TEXT("raftsim.GuideLeftHanded"))->GetInt() != 0;
    const auto Seats = RaftSimCrewSeatLayout::BuildNormalSeats(Flex, bLeftGuide);
    Adapter->ConfigureFlexibleRaftModel(Flex, Seats);
    const int32 CrewCount = Raft->CrewAvatars.Num();
    if (!TestEqual(TEXT("four paddlers and a guide"), CrewCount, 5)) return false;

    constexpr float Dt = 1.f / 60.f;
    const auto Step = [&]()
    {
        Raft->UpdateCrew(Dt);
        for (const auto& Avatar : Raft->CrewAvatars) Avatar->Tick(Dt);
    };
    TArray<FVector> Home;
    for (const auto& Avatar : Raft->CrewAvatars) Home.Add(Avatar->GetRootComponent()->GetRelativeLocation());

    // Everyone over to the port tube and holding there.
    Raft->SetActorRotation(FRotator(0, 0, 10));
    Raft->HandleHighSideResponse(-1);
    for (int32 Frame = 0; Frame < 90; ++Frame) Step();
    TArray<FVector> HighSide;
    for (const auto& Avatar : Raft->CrewAvatars)
    {
        TestTrue(TEXT("crew holding the high side"), Avatar->HasHighSideTransfer());
        HighSide.Add(Avatar->GetRootComponent()->GetRelativeLocation());
    }

    // "Back to your seats!"
    Raft->IssueCrewCommand(ERaftSimCrewCommand::Seats);
    TestEqual(TEXT("the call is pending while the crew react"), Raft->GetPendingCrewCommand(), ERaftSimCrewCommand::Seats);
    TArray<float> LowestHip, LowestFreeHand;
    LowestHip.Init(FLT_MAX, CrewCount); LowestFreeHand.Init(FLT_MAX, CrewCount);
    // Frames where the body is crossing, and of those, frames where the free
    // hand stands still on the floor (planted) while the body moves over it.
    TArray<int32> CrossingFrames, PlantedFrames;
    CrossingFrames.Init(0, CrewCount); PlantedFrames.Init(0, CrewCount);
    TArray<TOptional<FVector>> LastHand, LastRoot; LastHand.SetNum(CrewCount); LastRoot.SetNum(CrewCount);
    float FastestLandmark = 0.f, SeatedAt = -1.f;
    FString FastestDetail;
    bool bAirborne = false, bAboveTube = false;
    TArray<TArray<FVector>> Previous; Previous.SetNum(CrewCount);
    const FTransform RaftToWorld = Raft->GetActorTransform();
    for (int32 Frame = 0; Frame < 180 && SeatedAt < 0.f; ++Frame)
    {
        Step();
        bool bAllSeated = true;
        for (int32 Index = 0; Index < CrewCount; ++Index)
        {
            auto* Avatar = Raft->CrewAvatars[Index].Get();
            bAllSeated &= !Avatar->HasHighSideTransfer();
            bAirborne |= Avatar->IsHighSideAirborne();
            const FVector Root = Avatar->GetRootComponent()->GetRelativeLocation();
            bAboveTube |= Root.Z > FMath::Max(Home[Index].Z, HighSide[Index].Z) + .5;
            if (!Avatar->HasHighSideTransfer()) continue;
            const auto& Pose = Avatar->GetPublishedCrewPose();
            LowestHip[Index] = FMath::Min(LowestHip[Index], float(.5 * (Pose.LeftHipCm.Z + Pose.RightHipCm.Z)));
            // The port hold keeps the paddle in the right fist; the left hand
            // comes off the line and goes down to the floor. (Planted height
            // follows the seat's height change a little while it is down.)
            LowestFreeHand[Index] = FMath::Min(LowestFreeHand[Index], float(Pose.LeftHandCm.Z));
            const FVector Hand = RaftToWorld.InverseTransformPosition(
                Avatar->GetActorTransform().TransformPosition(Pose.LeftHandCm));
            if (LastHand[Index] && LastRoot[Index] && FVector::Dist(Root, *LastRoot[Index]) > .3)
            {
                ++CrossingFrames[Index];
                PlantedFrames[Index] += FVector::Dist(Hand, *LastHand[Index]) < .25 ? 1 : 0;
            }
            LastHand[Index] = Hand;
            LastRoot[Index] = Root;
            TArray<FVector> Points;
            for (const FVector& Local : {Pose.HeadCenterCm, Pose.TorsoCenterCm, Pose.LeftHandCm, Pose.RightHandCm,
                     Pose.LeftHipCm, Pose.RightHipCm, Pose.LeftFootCm, Pose.RightFootCm})
                Points.Add(Avatar->GetActorTransform().TransformPosition(Local));
            for (int32 P = 0; P < Points.Num() && Previous[Index].Num() == Points.Num(); ++P)
            {
                const float Jump = float(FVector::Dist(Points[P], Previous[Index][P]));
                if (Jump > FastestLandmark)
                    FastestDetail = FString::Printf(TEXT("avatar %d landmark %d frame %d alpha %.3f scale %s"),
                        Index, P, Frame, Avatar->GetHighSideMotionAlpha(), *Avatar->GetActorScale3D().ToString());
                FastestLandmark = FMath::Max(FastestLandmark, Jump);
            }
            Previous[Index] = Points;
        }
        if (bAllSeated) SeatedAt = (Frame + 1) * Dt;
    }
    TestTrue(FString::Printf(TEXT("whole crew back in their seats within 2.7 s of the call (%.2f s)"), SeatedAt),
        SeatedAt > 0.f && SeatedAt <= 2.7f);
    TestTrue(TEXT("nobody takes off: the scramble stays in the boat"), !bAirborne && !bAboveTube);
    AddInfo(FString::Printf(TEXT("fastest landmark: %s"), *FastestDetail));
    // A scrambling hand flicks forward at up to ~6 m/s; nothing teleports.
    TestTrue(FString::Printf(TEXT("no landmark jumps more than 10 cm in a frame (%.1f cm)"), FastestLandmark),
        FastestLandmark <= 10.f);
    for (int32 Index = 0; Index < CrewCount; ++Index)
    {
        auto* Avatar = Raft->CrewAvatars[Index].Get();
        TestTrue(TEXT("back exactly on the home seat"),
            Avatar->GetRootComponent()->GetRelativeLocation().Equals(Home[Index], .5));
        TestEqual(TEXT("sitting ready, paddle across the lap"), Avatar->GetAvatarAction(), ERaftSimCrewAvatarAction::SeatedIdle);
        TestTrue(TEXT("no weight left on the high side"), Avatar->GetHighSideTransferOffsetCm().IsNearlyZero(.01));
        // Crossing the boat (from the port tube to a starboard seat) is a
        // low scramble with a hand on the floor; along the same tube, a shuffle.
        if (Home[Index].Y > 0.)
        {
            TestTrue(FString::Printf(TEXT("%s gets low to cross (hips %.1f cm)"), *Avatar->GetName(), LowestHip[Index]),
                LowestHip[Index] <= 32.f);
            TestTrue(FString::Printf(TEXT("%s puts a hand down to the floor (%.1f cm)"), *Avatar->GetName(), LowestFreeHand[Index]),
                LowestFreeHand[Index] <= 12.f);
            // Planted about half of each step: a hand that slid along the
            // floor instead would never be still while the body moves.
            TestTrue(FString::Printf(TEXT("%s hand stays planted while the body passes (%d of %d crossing frames)"),
                *Avatar->GetName(), PlantedFrames[Index], CrossingFrames[Index]),
                CrossingFrames[Index] > 20 && PlantedFrames[Index] >= .4f * CrossingFrames[Index]);
        }
    }
    TestEqual(TEXT("the order stands once seated"), Raft->GetActiveCrewCommand(), ERaftSimCrewCommand::Seats);

    // A paddle call after a high-side brings them back the same way, then paddles.
    Raft->HandleHighSideResponse(1);
    for (int32 Frame = 0; Frame < 90; ++Frame) Step();
    Raft->IssueCrewCommand(ERaftSimCrewCommand::AllForward);
    for (int32 Frame = 0; Frame < 180; ++Frame) Step();
    for (const auto& Avatar : Raft->CrewAvatars)
        TestFalse(TEXT("a paddle call also brings the crew back"), Avatar->HasHighSideTransfer());
    return true;
}
#endif
