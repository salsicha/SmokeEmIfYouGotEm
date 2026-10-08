#include "RaftSimCrewRagdoll.h"

namespace
{
constexpr float kSubstepSeconds = 1.0f / 120.0f;
constexpr float kGravityCmPerSecond2 = 981.0f;
// Arm and leg bones, cm: the elbow is not in the pose, so the arm's are set.
constexpr float kUpperArmCm = 29.0f;
constexpr float kForearmCm = 27.0f;
// A limb swings but never folds flat: shoulder to hand stays at least this
// share of the arm's length, hip to foot of the leg's.
constexpr float kArmFoldFraction = 0.4f;
constexpr float kLegFoldFraction = 0.45f;
// Water deeper than this over a joint bears it fully.
constexpr float kSubmergenceCm = 15.0f;
// The body follows the gameplay swimmer across the water this quickly.
constexpr float kFollowSeconds = 0.3f;
// The water's up or down rush carries the body only this fast, cm/s: a
// PFD keeps a pour-over from driving a swimmer far under (they vanished
// beneath the white water of a hole).
constexpr float kVerticalCarryCmPerSecond = 60.0f;

// Masses (kg) and the water's upward pull on each joint, fully under
// (cm/s^2; gravity is 981): the PFD floats the chest and shoulders hard, so
// a swimmer is back up within a second or so, the hips less, arms and legs
// about neutrally, the feet a little heavy. The paddle floats.
struct FJoint
{
    float MassKg;
    float BuoyancyCmPerSecond2;
};
const FJoint kJoints[FRaftSimCrewRagdoll::PointCount] = {
    {11.0f, 1300.0f}, // Pelvis
    {4.0f, 1200.0f},  // LeftHip
    {4.0f, 1200.0f},  // RightHip
    {12.0f, 1900.0f}, // Chest
    {4.0f, 1900.0f},  // LeftShoulder
    {4.0f, 1900.0f},  // RightShoulder
    {5.0f, 1100.0f},  // Head
    {1.6f, 1000.0f},  // LeftElbow
    {0.6f, 950.0f},   // LeftHand
    {1.6f, 1000.0f},  // RightElbow
    {0.6f, 950.0f},   // RightHand
    {4.5f, 990.0f},   // LeftKnee
    {2.2f, 960.0f},   // LeftFoot
    {4.5f, 990.0f},   // RightKnee
    {2.2f, 960.0f},   // RightFoot
    {0.45f, 1600.0f}, // PaddleTop
    {0.45f, 1600.0f}, // PaddleBottom
};

bool IsTorso(int32 Point)
{
    return Point <= FRaftSimCrewRagdoll::Head;
}
}

void FRaftSimCrewRagdoll::AddLink(int32 A, int32 B, float MinimumFraction)
{
    FLink Link;
    Link.A = A;
    Link.B = B;
    Link.LengthCm = float(FVector::Distance(X[A], X[B]));
    Link.MinimumFraction = MinimumFraction;
    Links.Add(Link);
}

void FRaftSimCrewRagdoll::Begin(const FTransform& AvatarWorld, const FRaftSimCrewAvatarPose& Pose,
    const FVector& VelocityCmPerSecond, const FVector& SpinRadiansPerSecond)
{
    const auto World = [&AvatarWorld](const FVector& LocalCm) { return AvatarWorld.TransformPosition(LocalCm); };
    const FVector HipsCm = (Pose.LeftHipCm + Pose.RightHipCm) * 0.5;
    const FVector ShouldersCm = (Pose.LeftShoulderCm + Pose.RightShoulderCm) * 0.5;
    const FVector TorsoAxis = ShouldersCm - HipsCm;
    PelvisLocalCm = HipsCm;
    TorsoCentreFraction = TorsoAxis.SizeSquared() > 1.0
        ? float(FMath::Clamp(FVector::DotProduct(Pose.TorsoCenterCm - HipsCm, TorsoAxis) / TorsoAxis.SizeSquared(), 0.2, 0.9))
        : 0.6f;
    // The elbow bends down and out between shoulder and hand.
    const auto Elbow = [](const FVector& ShoulderCm, const FVector& HandCm, float OutSign)
    {
        const FVector Reach = HandCm - ShoulderCm;
        const double Half = 0.5 * FMath::Min(Reach.Size(), double(kUpperArmCm + kForearmCm));
        FVector Bend = FVector(0.0, OutSign, -1.0).GetSafeNormal();
        Bend = (Bend - FVector::DotProduct(Bend, Reach.GetSafeNormal()) * Reach.GetSafeNormal()).GetSafeNormal();
        return ShoulderCm + Reach.GetSafeNormal() * Half + Bend * FMath::Sqrt(FMath::Max(0.0, FMath::Square(double(kUpperArmCm)) - Half * Half));
    };
    X[Pelvis] = World(HipsCm);
    X[LeftHip] = World(Pose.LeftHipCm);
    X[RightHip] = World(Pose.RightHipCm);
    X[Chest] = World(ShouldersCm);
    X[LeftShoulder] = World(Pose.LeftShoulderCm);
    X[RightShoulder] = World(Pose.RightShoulderCm);
    X[Head] = World(Pose.HeadCenterCm);
    X[LeftElbow] = World(Elbow(Pose.LeftShoulderCm, Pose.LeftHandCm, -1.0f));
    X[LeftHand] = World(Pose.LeftHandCm);
    X[RightElbow] = World(Elbow(Pose.RightShoulderCm, Pose.RightHandCm, 1.0f));
    X[RightHand] = World(Pose.RightHandCm);
    X[LeftKnee] = World(Pose.LeftKneeCm);
    X[LeftFoot] = World(Pose.LeftFootCm);
    X[RightKnee] = World(Pose.RightKneeCm);
    X[RightFoot] = World(Pose.RightFootCm);
    // The paddle as held; the hand lower down it, on the shaft, keeps it.
    FVector TopCm = Pose.PaddleTopCm, BottomCm = Pose.PaddleBottomCm;
    if (!Pose.bShowPaddle || FVector::DistSquared(TopCm, BottomCm) < 100.0)
    {
        TopCm = Pose.LeftHandCm + FVector(0.0, 0.0, 50.0);
        BottomCm = TopCm - FVector(0.0, 0.0, 120.0);
    }
    GripHand = FVector::DistSquared(Pose.LeftHandCm, TopCm) >= FVector::DistSquared(Pose.RightHandCm, TopCm) ? LeftHand : RightHand;
    const FVector HeldCm = GripHand == LeftHand ? Pose.LeftHandCm : Pose.RightHandCm;
    const FVector Shaft = BottomCm - TopCm;
    GripAlong = float(FMath::Clamp(FVector::DotProduct(HeldCm - TopCm, Shaft) / Shaft.SizeSquared(), 0.15, 0.95));
    X[PaddleTop] = World(TopCm);
    X[PaddleBottom] = World(BottomCm);

    Links.Reset();
    // The torso is one block, the head fixed on it.
    const int32 Torso[] = {Pelvis, LeftHip, RightHip, Chest, LeftShoulder, RightShoulder};
    for (int32 I = 0; I < UE_ARRAY_COUNT(Torso); ++I)
    {
        for (int32 J = I + 1; J < UE_ARRAY_COUNT(Torso); ++J)
        {
            AddLink(Torso[I], Torso[J]);
        }
    }
    AddLink(Head, Chest);
    AddLink(Head, LeftShoulder);
    AddLink(Head, RightShoulder);
    // Arms and legs swing from it on bones of fixed length.
    AddLink(LeftShoulder, LeftElbow);
    AddLink(LeftElbow, LeftHand);
    AddLink(RightShoulder, RightElbow);
    AddLink(RightElbow, RightHand);
    AddLink(LeftHip, LeftKnee);
    AddLink(LeftKnee, LeftFoot);
    AddLink(RightHip, RightKnee);
    AddLink(RightKnee, RightFoot);
    for (const TPair<int32, int32>& Limb : {TPair<int32, int32>(LeftShoulder, LeftHand), TPair<int32, int32>(RightShoulder, RightHand)})
    {
        AddLink(Limb.Key, Limb.Value, kArmFoldFraction);
        Links.Last().LengthCm = kUpperArmCm + kForearmCm;
    }
    for (const TPair<int32, int32>& Limb : {TPair<int32, int32>(LeftHip, LeftFoot), TPair<int32, int32>(RightHip, RightFoot)})
    {
        const float LegCm = float(FVector::Distance(X[Limb.Key], X[Limb.Key == LeftHip ? LeftKnee : RightKnee]) +
            FVector::Distance(X[Limb.Key == LeftHip ? LeftKnee : RightKnee], X[Limb.Value]));
        AddLink(Limb.Key, Limb.Value, kLegFoldFraction);
        Links.Last().LengthCm = LegCm;
    }
    AddLink(PaddleTop, PaddleBottom);

    FVector Centre = FVector::ZeroVector;
    float TotalKg = 0.0f;
    for (int32 I = 0; I < PointCount; ++I)
    {
        InverseMass[I] = 1.0f / kJoints[I].MassKg;
        BuoyancyCmPerSecond2[I] = kJoints[I].BuoyancyCmPerSecond2;
        Centre += X[I] * kJoints[I].MassKg;
        TotalKg += kJoints[I].MassKg;
    }
    Centre /= TotalKg;
    for (int32 I = 0; I < PointCount; ++I)
    {
        const FVector Velocity = VelocityCmPerSecond + FVector::CrossProduct(SpinRadiansPerSecond, X[I] - Centre);
        Previous[I] = X[I] - Velocity * kSubstepSeconds;
    }
    Seconds = FloatingSeconds = SubstepDebt = 0.0f;
}

FVector FRaftSimCrewRagdoll::GripPoint() const
{
    return FMath::Lerp(X[PaddleTop], X[PaddleBottom], GripAlong);
}

FVector FRaftSimCrewRagdoll::TorsoCentre() const
{
    return FMath::Lerp(X[Pelvis], X[Chest], TorsoCentreFraction);
}

void FRaftSimCrewRagdoll::SatisfyLinks()
{
    for (const FLink& Link : Links)
    {
        const FVector Delta = X[Link.B] - X[Link.A];
        const double Length = Delta.Size();
        if (Length < 1.0e-3)
        {
            continue;
        }
        double Target = Link.LengthCm;
        if (Link.MinimumFraction > 0.0f)
        {
            const double Shortest = Link.LengthCm * Link.MinimumFraction;
            if (Length >= Shortest && Length <= Link.LengthCm)
            {
                continue;
            }
            Target = Length < Shortest ? Shortest : Link.LengthCm;
        }
        const float Weight = InverseMass[Link.A] + InverseMass[Link.B];
        const FVector Correction = Delta * ((Length - Target) / (Length * Weight));
        X[Link.A] += Correction * InverseMass[Link.A];
        X[Link.B] -= Correction * InverseMass[Link.B];
    }
    // The hand keeps hold of the shaft: hand and paddle meet at the grip,
    // each moving as its weight lets it.
    const FVector Gap = X[GripHand] - GripPoint();
    const float A = GripAlong;
    const float Weight = InverseMass[GripHand] + FMath::Square(1.0f - A) * InverseMass[PaddleTop] + FMath::Square(A) * InverseMass[PaddleBottom];
    if (Weight > 0.0f)
    {
        X[GripHand] -= Gap * (InverseMass[GripHand] / Weight);
        X[PaddleTop] += Gap * ((1.0f - A) * InverseMass[PaddleTop] / Weight);
        X[PaddleBottom] += Gap * (A * InverseMass[PaddleBottom] / Weight);
    }
}

void FRaftSimCrewRagdoll::Advance(float DeltaSeconds, const FVector& AnchorCm, const FWaterSampler& Water)
{
    SubstepDebt += FMath::Clamp(DeltaSeconds, 0.0f, 0.1f);
    // The water where the body is: one sample at the torso, for every joint.
    float SurfaceCm = -TNumericLimits<float>::Max();
    FVector WaterVelocity = FVector::ZeroVector;
    const bool bWet = Water && Water(TorsoCentre(), SurfaceCm, WaterVelocity);
    WaterVelocity.Z = FMath::Clamp(WaterVelocity.Z, -kVerticalCarryCmPerSecond, kVerticalCarryCmPerSecond);
    while (SubstepDebt >= kSubstepSeconds)
    {
        SubstepDebt -= kSubstepSeconds;
        Seconds += kSubstepSeconds;
        for (int32 I = 0; I < PointCount; ++I)
        {
            FVector Velocity = (X[I] - Previous[I]) / kSubstepSeconds;
            const float Under = bWet ? FMath::Clamp(float(SurfaceCm - X[I].Z) / kSubmergenceCm, 0.0f, 1.0f) : 0.0f;
            const FVector Acceleration(0.0, 0.0, -kGravityCmPerSecond2 + BuoyancyCmPerSecond2[I] * Under);
            // In the water a joint is carried by the current, the torso
            // (with its PFD) a little more slowly than a flailing limb; in
            // the air it hardly slows.
            if (Under > 0.0f)
            {
                const float Rate = (IsTorso(I) ? 2.5f : 4.0f) * Under;
                Velocity += (WaterVelocity - Velocity) * (1.0f - FMath::Exp(-Rate * kSubstepSeconds));
            }
            else
            {
                Velocity *= 1.0f - 0.05f * kSubstepSeconds;
            }
            Previous[I] = X[I];
            X[I] += Velocity * kSubstepSeconds + Acceleration * FMath::Square(kSubstepSeconds);
        }
        for (int32 Pass = 0; Pass < 6; ++Pass)
        {
            SatisfyLinks();
        }
        // Follow the gameplay swimmer across the water; up and down the body
        // floats as it floats.
        FVector Pull = (AnchorCm - TorsoCentre()) * (1.0f - FMath::Exp(-kSubstepSeconds / kFollowSeconds));
        Pull.Z = 0.0;
        for (int32 I = 0; I < PointCount; ++I)
        {
            X[I] += Pull;
            Previous[I] += Pull;
        }
        const bool bFloating = bWet && X[Chest].Z < SurfaceCm + 10.0f && X[Pelvis].Z < SurfaceCm + 10.0f;
        FloatingSeconds = bFloating ? FloatingSeconds + kSubstepSeconds : 0.0f;
    }
}

bool FRaftSimCrewRagdoll::IsSettled() const
{
    return (Seconds >= 1.2f && FloatingSeconds >= 0.7f) || Seconds >= 4.0f;
}

FVector FRaftSimCrewRagdoll::GetHeading() const
{
    const FVector Heading = (X[Head] - X[Pelvis]).GetSafeNormal2D();
    return Heading.IsNearlyZero() ? FVector::ForwardVector : Heading;
}

float FRaftSimCrewRagdoll::GetGripGapCm() const
{
    return float(FVector::Distance(X[GripHand], GripPoint()));
}

float FRaftSimCrewRagdoll::GetMaximumBoneErrorCm() const
{
    float Worst = 0.0f;
    for (const FLink& Link : Links)
    {
        if (Link.MinimumFraction <= 0.0f)
        {
            Worst = FMath::Max(Worst, float(FMath::Abs(FVector::Distance(X[Link.A], X[Link.B]) - Link.LengthCm)));
        }
    }
    return Worst;
}

void FRaftSimCrewRagdoll::Read(FTransform& OutRoot, FRaftSimCrewAvatarPose& OutPose) const
{
    // The avatar's frame stands on the torso: up the spine, right across
    // the shoulders.
    const FVector Up = (X[Chest] - X[Pelvis]).GetSafeNormal();
    FVector Right = X[RightShoulder] - X[LeftShoulder];
    Right = (Right - FVector::DotProduct(Right, Up) * Up).GetSafeNormal();
    const FQuat Rotation = FRotationMatrix::MakeFromZY(Up, Right).ToQuat();
    const FVector Root = X[Pelvis] - Rotation.RotateVector(PelvisLocalCm);
    OutRoot = FTransform(Rotation, Root);
    const auto Local = [&](int32 Point) { return Rotation.UnrotateVector(X[Point] - Root); };
    OutPose = FRaftSimCrewAvatarPose();
    OutPose.TorsoCenterCm = FMath::Lerp(Local(Pelvis), Local(Chest), TorsoCentreFraction);
    OutPose.TorsoRotation = FRotator::ZeroRotator;
    OutPose.HeadCenterCm = Local(Head);
    OutPose.LeftShoulderCm = Local(LeftShoulder);
    OutPose.RightShoulderCm = Local(RightShoulder);
    OutPose.LeftHandCm = Local(LeftHand);
    OutPose.RightHandCm = Local(RightHand);
    OutPose.LeftHipCm = Local(LeftHip);
    OutPose.RightHipCm = Local(RightHip);
    OutPose.LeftKneeCm = Local(LeftKnee);
    OutPose.RightKneeCm = Local(RightKnee);
    OutPose.LeftFootCm = Local(LeftFoot);
    OutPose.RightFootCm = Local(RightFoot);
    OutPose.PaddleTopCm = Local(PaddleTop);
    OutPose.PaddleBottomCm = Local(PaddleBottom);
    OutPose.bShowPaddle = true;
    OutPose.bLeftHandFree = GripHand != LeftHand;
    OutPose.bRightHandFree = GripHand != RightHand;
}
