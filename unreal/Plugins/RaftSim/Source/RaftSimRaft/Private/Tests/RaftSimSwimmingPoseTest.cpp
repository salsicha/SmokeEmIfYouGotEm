#include "Misc/AutomationTest.h"
#include "RaftSimCrewAvatarActor.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimSwimmingPoseTest,
    "RaftSim.Crew.SwimmingTorsoAlignment",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimSwimmingPoseTest::RunTest(const FString&)
{
    for (int32 Side : {-1, 1})
    {
        for (int32 Sample = 0; Sample <= 100; ++Sample)
        {
            const float Phase = Sample / 100.f;
            const auto Pose = URaftSimCrewAvatarPoseLibrary::EvaluatePose(
                ERaftSimCrewAvatarAction::Swimming, Phase, Side);
            const FVector Spine = ((Pose.LeftShoulderCm + Pose.RightShoulderCm) -
                (Pose.LeftHipCm + Pose.RightHipCm)).GetSafeNormal();
            const FVector TorsoLongAxis = Pose.TorsoRotation.RotateVector(FVector::UpVector);
            TestTrue(TEXT("torso and worn PFD follow hip-to-shoulder swimming axis"),
                FVector::DotProduct(Spine, TorsoLongAxis) > .995);
            TestTrue(TEXT("swimming long axis is near horizontal"), FMath::Abs(TorsoLongAxis.Z) < .05);
            TestTrue(TEXT("neck points toward the head rather than the feet"),
                FVector::DotProduct(Pose.HeadCenterCm - Pose.TorsoCenterCm, TorsoLongAxis) > 25.);
            // A swimmer keeps their paddle in the hand that held its shaft
            // in the boat (2026-10-08); the other hand strokes.
            TestTrue(TEXT("a swimmer keeps their paddle in one hand"),
                Pose.bShowPaddle && Pose.bLeftHandFree != Pose.bRightHandFree &&
                Pose.bLeftHandFree == (Side > 0));
            TestTrue(TEXT("the holding hand is on the shaft"),
                FMath::PointDistToSegment(Pose.bLeftHandFree ? Pose.RightHandCm : Pose.LeftHandCm,
                    Pose.PaddleTopCm, Pose.PaddleBottomCm) < 0.001);
            const auto Wrapped = URaftSimCrewAvatarPoseLibrary::EvaluatePose(
                ERaftSimCrewAvatarAction::Swimming, Phase + 1.f, Side);
            TestTrue(TEXT("swimming torso and head loop continuously"),
                Pose.TorsoCenterCm.Equals(Wrapped.TorsoCenterCm, .001) &&
                Pose.HeadCenterCm.Equals(Wrapped.HeadCenterCm, .001));
        }
    }
    return true;
}
#endif
