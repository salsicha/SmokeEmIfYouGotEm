#pragma once

#include "CoreMinimal.h"
#include "RaftSimCrewAvatarActor.h"

/**
 * A crew member thrown out of the raft, tumbling as a rag doll until they
 * float. The body is a few joints joined by bones of fixed length: a rigid
 * torso block with the head on it, arms and legs swinging free from it
 * (never folded flat), and the paddle, a rigid shaft one hand keeps hold of.
 * Gravity, the throw, the water's buoyancy (the PFD floats the chest) and its
 * current act on every joint. Its horizontal place follows the gameplay
 * swimmer, so the body leaves the boat where the rescue logic has the
 * swimmer; how it tumbles on the way is its own. Presentation only.
 *
 * Positions are world centimetres; the pose read back is in the avatar's
 * own frame, built about the torso so the body solver poses an upright
 * torso and the limbs about it.
 */
class FRaftSimCrewRagdoll
{
public:
    /** Water surface height (cm) and velocity (cm/s) at a world point (cm); false where dry. */
    using FWaterSampler = TFunction<bool(const FVector&, float&, FVector&)>;

    /**
     * Start from the pose held at release (avatar-local cm, in AvatarWorld),
     * moving at VelocityCmPerSecond and turning at SpinRadiansPerSecond
     * (world axis times rate). The hand on the paddle's shaft (the lower
     * hand) keeps it.
     */
    void Begin(const FTransform& AvatarWorld, const FRaftSimCrewAvatarPose& Pose,
        const FVector& VelocityCmPerSecond, const FVector& SpinRadiansPerSecond);
    /** Step it. AnchorCm: where gameplay has the swimmer (its avatar root). */
    void Advance(float DeltaSeconds, const FVector& AnchorCm, const FWaterSampler& Water);
    /** The body as an avatar root and a pose in that root's frame. */
    void Read(FTransform& OutRoot, FRaftSimCrewAvatarPose& OutPose) const;

    float GetSeconds() const { return Seconds; }
    /** Floating (torso in the water) for long enough to start swimming. */
    bool IsSettled() const;
    /** Which way the body lies, head end, flattened onto the water. */
    FVector GetHeading() const;
    bool HoldsWithLeftHand() const { return GripHand == LeftHand; }
    /** Hand-to-shaft gap, cm (0 while held). For tests. */
    float GetGripGapCm() const;
    /** Largest bone length error, cm. For tests. */
    float GetMaximumBoneErrorCm() const;
    FVector GetPoint(int32 Index) const { return X[Index]; }

    enum EPoint : int32
    {
        Pelvis, LeftHip, RightHip, Chest, LeftShoulder, RightShoulder, Head,
        LeftElbow, LeftHand, RightElbow, RightHand,
        LeftKnee, LeftFoot, RightKnee, RightFoot,
        PaddleTop, PaddleBottom,
        PointCount
    };

private:
    struct FLink
    {
        int32 A = 0, B = 0;
        float LengthCm = 0.0f;
        /** 0: a bone, held at its length. Otherwise only kept at least this
         * fraction of its length (a limb never folded flat). */
        float MinimumFraction = 0.0f;
    };

    void AddLink(int32 A, int32 B, float MinimumFraction = 0.0f);
    void SatisfyLinks();
    FVector GripPoint() const;
    FVector TorsoCentre() const;

    FVector X[PointCount];
    FVector Previous[PointCount];
    float InverseMass[PointCount] = {};
    /** Upward pull while submerged, cm/s^2 (gravity is separate). */
    float BuoyancyCmPerSecond2[PointCount] = {};
    TArray<FLink> Links;
    int32 GripHand = LeftHand;
    /** Where along the shaft the hand holds it, from the top (0..1). */
    float GripAlong = 0.5f;
    /** The pelvis in the avatar's frame, and how far up the torso its
     * centre sits, as at release. */
    FVector PelvisLocalCm = FVector(-4.0, 0.0, 40.0);
    float TorsoCentreFraction = 0.6f;
    float Seconds = 0.0f;
    float FloatingSeconds = 0.0f;
    float SubstepDebt = 0.0f;
};
