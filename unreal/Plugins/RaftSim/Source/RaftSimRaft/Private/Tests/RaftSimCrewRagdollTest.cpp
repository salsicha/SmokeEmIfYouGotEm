#include "Misc/AutomationTest.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimCrewRagdoll.h"

#if WITH_AUTOMATION_TESTS
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FRaftSimCrewRagdollTest, "RaftSim.Crew.RagdollFall",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FRaftSimCrewRagdollTest::RunTest(const FString&)
{
    for (const int32 Side : {-1, 1})
    {
        // A paddler on a tube 40 cm above flat water running at 1.5 m/s,
        // thrown up and out over the side as gameplay puts them 80 cm out.
        const FRaftSimCrewAvatarPose Seated = URaftSimCrewAvatarPoseLibrary::EvaluatePose(
            ERaftSimCrewAvatarAction::SeatedIdle, 0.0f, Side);
        const FTransform Seat(FRotator(0.0, 0.0, 0.0), FVector(0.0, 0.0, 40.0));
        const FVector Out(0.0, double(Side), 0.0);
        FRaftSimCrewRagdoll Ragdoll;
        Ragdoll.Begin(Seat, Seated, FVector(150.0, 0.0, 0.0) + Out * 120.0 + FVector(0.0, 0.0, 150.0), FVector(2.0, -1.5, 0.8));
        const FVector Anchor = Seat.GetLocation() + Out * 80.0;
        const auto Water = [](const FVector&, float& SurfaceCm, FVector& VelocityCm)
            { SurfaceCm = 0.0f; VelocityCm = FVector(150.0, 0.0, 0.0); return true; };
        const FVector StartChest = Ragdoll.GetPoint(FRaftSimCrewRagdoll::Chest);
        TestTrue(TEXT("the lower hand, on the shaft, keeps the paddle"),
            Ragdoll.HoldsWithLeftHand() == (Side < 0) && Ragdoll.GetGripGapCm() < 0.01f);
        double HighestChest = StartChest.Z, WorstGrip = 0.0, WorstBone = 0.0;
        double SettledAt = -1.0;
        for (int32 Frame = 0; Frame < 4 * 60; ++Frame)
        {
            Ragdoll.Advance(1.0f / 60.0f, Anchor + FVector(150.0 * Frame / 60.0, 0.0, 0.0), Water);
            HighestChest = FMath::Max(HighestChest, Ragdoll.GetPoint(FRaftSimCrewRagdoll::Chest).Z);
            WorstGrip = FMath::Max(WorstGrip, double(Ragdoll.GetGripGapCm()));
            WorstBone = FMath::Max(WorstBone, double(Ragdoll.GetMaximumBoneErrorCm()));
            if (SettledAt < 0.0 && Ragdoll.IsSettled())
            {
                SettledAt = Ragdoll.GetSeconds();
            }
        }
        TestTrue(FString::Printf(TEXT("thrown up out of the boat (chest rose %.0f cm)"), HighestChest - StartChest.Z),
            HighestChest > StartChest.Z + 5.0);
        TestTrue(FString::Printf(TEXT("one hand never lets go of the shaft (worst gap %.2f cm)"), WorstGrip), WorstGrip < 1.0);
        TestTrue(FString::Printf(TEXT("bones keep their lengths (worst %.2f cm)"), WorstBone), WorstBone < 1.0);
        const double ChestZ = Ragdoll.GetPoint(FRaftSimCrewRagdoll::Chest).Z;
        TestTrue(FString::Printf(TEXT("the PFD floats the chest at the surface (%.1f cm)"), ChestZ), FMath::Abs(ChestZ) < 20.0);
        TestTrue(FString::Printf(TEXT("floating by four seconds (settled at %.2f s)"), SettledAt), SettledAt > 0.0 && SettledAt <= 4.0);
        const FVector Torso = Ragdoll.GetPoint(FRaftSimCrewRagdoll::Pelvis);
        TestTrue(TEXT("the body ends where gameplay has the swimmer, carried downstream"),
            FVector::Dist2D(Torso, Anchor + FVector(150.0 * 4.0, 0.0, 0.0)) < 80.0);
        FTransform Root;
        FRaftSimCrewAvatarPose Pose;
        Ragdoll.Read(Root, Pose);
        TestTrue(TEXT("the pose read back is finite, its paddle shown in one hand"),
            !Root.ContainsNaN() && Pose.bShowPaddle && Pose.bLeftHandFree != Pose.bRightHandFree &&
            !Pose.LeftHandCm.ContainsNaN() && !Pose.PaddleBottomCm.ContainsNaN());
        TestTrue(TEXT("the avatar's frame stands on the torso"),
            FVector::DotProduct((Pose.LeftShoulderCm + Pose.RightShoulderCm - Pose.LeftHipCm - Pose.RightHipCm).GetSafeNormal(),
                FVector::UpVector) > 0.999);
        TestTrue(TEXT("the holding hand is on the shaft in the pose"),
            FMath::PointDistToSegment(Pose.bLeftHandFree ? Pose.RightHandCm : Pose.LeftHandCm, Pose.PaddleTopCm, Pose.PaddleBottomCm) < 1.0);
    }
    return true;
}
#endif
