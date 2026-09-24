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
            TestFalse(TEXT("swimming does not retain a paddle"), Pose.bShowPaddle);
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
