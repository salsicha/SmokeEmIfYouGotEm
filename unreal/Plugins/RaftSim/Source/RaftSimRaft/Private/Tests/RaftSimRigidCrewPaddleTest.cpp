#include "Misc/AutomationTest.h"
#include "RaftSimCrewAvatarActor.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimRigidCrewPaddleTest,
    "RaftSim.Crew.RigidPaddleAcrossActions",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimRigidCrewPaddleTest::RunTest(const FString&)
{
    int32 VisiblePoses = 0;
    for (int32 ActionIndex = 0; ActionIndex <= static_cast<int32>(ERaftSimCrewAvatarAction::Reentry); ++ActionIndex)
    {
        const auto Action = static_cast<ERaftSimCrewAvatarAction>(ActionIndex);
        for (int32 Side : {-1, 1})
        {
            for (int32 Sample = 0; Sample <= 100; ++Sample)
            {
                const float Phase = Sample / 100.0f;
                const auto Pose = URaftSimCrewAvatarPoseLibrary::EvaluatePose(Action, Phase, Side);
                if (!Pose.bShowPaddle) continue;
                ++VisiblePoses;
                TestTrue(TEXT("visible shaft is rigid through the entire action cycle"),
                    FMath::Abs(FVector::Distance(Pose.PaddleTopCm, Pose.PaddleBottomCm) - 120.0) < 0.0001);
                TestTrue(TEXT("both hands remain on the finite shaft, not its extended line"),
                    FMath::PointDistToSegment(Pose.LeftHandCm, Pose.PaddleTopCm, Pose.PaddleBottomCm) < 0.0001 &&
                    FMath::PointDistToSegment(Pose.RightHandCm, Pose.PaddleTopCm, Pose.PaddleBottomCm) < 0.0001);
                TestTrue(TEXT("blade remains outboard of its own seat"), Pose.PaddleBottomCm.Y * Side > 0);
                const auto Wrapped = URaftSimCrewAvatarPoseLibrary::EvaluatePose(Action, Phase + 1.0f, Side);
                TestTrue(TEXT("rigid constraint preserves phase periodicity"),
                    Pose.PaddleBottomCm.Equals(Wrapped.PaddleBottomCm, 0.001));
            }
        }
    }
    TestEqual(TEXT("eight paddle actions, both sides, 101 phases"), VisiblePoses, 8 * 2 * 101);
    for (int32 Side : {-1, 1})
    {
        const auto Idle = URaftSimCrewAvatarPoseLibrary::EvaluatePose(ERaftSimCrewAvatarAction::SeatedIdle, 0, Side);
        const double RestAuthoredLength = FVector(12, 82, 4).Size();
        TestTrue(TEXT("rest top, blade height and grip distances are unchanged"),
            Idle.PaddleTopCm.Equals(FVector(18, -30 * Side, 36), 0.0001) &&
            FMath::Abs(Idle.PaddleBottomCm.Z - 40.0) < 0.0001 &&
            FMath::Abs(FVector::Distance(Side < 0 ? Idle.RightHandCm : Idle.LeftHandCm, Idle.PaddleTopCm) - 0.15 * RestAuthoredLength) < 0.0001 &&
            FMath::Abs(FVector::Distance(Side < 0 ? Idle.LeftHandCm : Idle.RightHandCm, Idle.PaddleTopCm) - 0.45 * RestAuthoredLength) < 0.0001);
        const auto Catch = URaftSimCrewAvatarPoseLibrary::EvaluatePose(ERaftSimCrewAvatarAction::ForwardStroke, 0, Side);
        const auto Finish = URaftSimCrewAvatarPoseLibrary::EvaluatePose(ERaftSimCrewAvatarAction::ForwardStroke, 0.58f, Side);
        const auto Recovery = URaftSimCrewAvatarPoseLibrary::EvaluatePose(ERaftSimCrewAvatarAction::ForwardStroke, 0.79f, Side);
        TestTrue(TEXT("power still sweeps aft and recovery lifts the blade"),
            Catch.PaddleBottomCm.X - Finish.PaddleBottomCm.X >= 35 &&
            Recovery.PaddleBottomCm.Z - Catch.PaddleBottomCm.Z >= 24);
    }
    return true;
}
#endif
