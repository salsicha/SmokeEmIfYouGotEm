// Paddle, T-grip and oar grips for the CC0 crew bodies (2026-10-07 rewrite).
//
// Every grip is a hand closed round a bar: the paddle shaft, the T-grip's
// crossbar, or an oar handle. A grip names only the bar's axis (pointing to
// the thumb's side of the fist) and the way the palm faces; the finger
// direction then follows from the hand's own anatomy, so a grip cannot come
// out mirrored. The wrist is placed so the bar lies across the palm just
// below the knuckles, the fingers flex toward the palm until their pads sit
// on the bar, the thumb closes round the other way over the fingers, and the
// forearm takes most of any twist so the wrist does not wring.
//
// The former solver treated the palm as the back of the hand: every grip
// pressed the back of the hand to the handle and wrapped the fingers round it
// backwards ("the t grip hand ... has the wrist facing away from the grip
// with the fingers bent backwards", 2026-10-07).

#include "RaftSimCC0CrewVisualActor.h"

#include "Components/PoseableMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "Rendering/SkinWeightVertexBuffer.h"

namespace
{
const TCHAR* const GripFingers[] = {TEXT("index"), TEXT("middle"), TEXT("ring"), TEXT("pinky")};
// The pad centre of each finger rides this far off the bar's surface (cm).
constexpr float FingerPadHalfThicknessCm[] = {0.85f, 0.88f, 0.82f, 0.72f};
constexpr float ThumbPadHalfThicknessCm = 0.95f;
// RaftSimCrewAvatarActor draws the shaft and the T-grip crossbar at these radii.
constexpr float PaddleShaftRadiusCm = 1.65f;
constexpr float PaddleTGripRadiusCm = 2.2f;
constexpr float OarHandleRadiusCm = 1.9f;
// The bar crosses the palm this fraction of the way from the wrist to the
// middle knuckle: on the palm, just below the knuckle crease.
constexpr float GripAlongPalmFraction = 0.78f;
// The palm's soft tissue gives a little under the bar.
constexpr float PalmCompressionCm = 0.25f;
// Off a capped T-grip the shaft leaves the crossbar between the middle and
// ring fingers: the fist sits this far toward the index side.
constexpr float TGripFistOffsetCm = 0.9f;
// Relaxed curl of an open or fisted hand off any handle.
constexpr float RelaxedFingerCurlDegrees[] = {42.0f, 62.0f, 42.0f};
constexpr float RelaxedThumbCurlDegrees[] = {15.0f, 25.0f};

FName SideBone(const TCHAR* Base, bool bLeft)
{
    return FName(*FString::Printf(TEXT("%s_%s"), Base, bLeft ? TEXT("l") : TEXT("r")));
}

FName DigitBone(const TCHAR* Digit, int32 Segment, bool bLeft)
{
    return FName(*FString::Printf(TEXT("%s_%02d_%s"), Digit, Segment, bLeft ? TEXT("l") : TEXT("r")));
}

double RadialCm(const FVector& Point, const FVector& BarPoint, const FVector& BarAxis)
{
    return FVector::VectorPlaneProject(Point - BarPoint, BarAxis).Size();
}

// Flex axis that turns a digit toward the palm: rotating Direction a little
// about it moves it toward Palm.
FVector TowardPalmAxis(const FVector& Candidate, const FVector& Direction, const FVector& Palm)
{
    const FVector Axis = Candidate.GetSafeNormal();
    const FVector Moved = FQuat(Axis, 0.2f).RotateVector(Direction) - Direction;
    return FVector::DotProduct(Moved, Palm) >= 0.0f ? Axis : -Axis;
}

int32 GripShapeKey(bool bLeft, float RadiusCm)
{
    return (bLeft ? 1 : 0) | (FMath::RoundToInt(RadiusCm * 100.0f) << 1);
}
}

bool ARaftSimCC0CrewVisualActor::ResolveHandAnatomy(
    bool bLeft,
    FVector& OutWristCm,
    FVector& OutFingers,
    FVector& OutThumb,
    FVector& OutPalm,
    float& OutHandedness) const
{
    const FTransform* Hand = ReferenceComponentTransforms.Find(SideBone(TEXT("hand"), bLeft));
    const FTransform* Index = ReferenceComponentTransforms.Find(SideBone(TEXT("index_01"), bLeft));
    const FTransform* Middle = ReferenceComponentTransforms.Find(SideBone(TEXT("middle_01"), bLeft));
    const FTransform* Pinky = ReferenceComponentTransforms.Find(SideBone(TEXT("pinky_01"), bLeft));
    const FTransform* ThumbMiddle = ReferenceComponentTransforms.Find(SideBone(TEXT("thumb_02"), bLeft));
    const FTransform* ThumbEnd = ReferenceComponentTransforms.Find(SideBone(TEXT("thumb_03"), bLeft));
    if (!Hand || !Index || !Middle || !Pinky || !ThumbMiddle || !ThumbEnd)
    {
        return false;
    }
    OutWristCm = Hand->GetLocation() * BodyScale;
    OutFingers = (Middle->GetLocation() - Hand->GetLocation()).GetSafeNormal();
    OutThumb = FVector::VectorPlaneProject(Index->GetLocation() - Pinky->GetLocation(), OutFingers).GetSafeNormal();
    // Measured on all five CC0 bodies (2026-10-07): the fingers' rest flexion,
    // the thumb, and the side each hand turns to the thigh in the rest pose
    // all put the palm on this side.
    OutPalm = (bLeft ? FVector::CrossProduct(OutThumb, OutFingers)
                     : FVector::CrossProduct(OutFingers, OutThumb)).GetSafeNormal();
    // Self-check on this body: the resting thumb tip sits palm-side of the
    // knuckles.
    const FVector ThumbTip = ThumbEnd->GetLocation() +
        (ThumbEnd->GetLocation() - ThumbMiddle->GetLocation()) * 0.85;
    const FVector Knuckles = (Index->GetLocation() + Pinky->GetLocation()) * 0.5;
    if (FVector::DotProduct(ThumbTip - Knuckles, OutPalm) < 0.0)
    {
        OutPalm = -OutPalm;
    }
    OutHandedness = FVector::DotProduct(FVector::CrossProduct(OutFingers, OutThumb), OutPalm) >= 0.0 ? 1.0f : -1.0f;
    return !OutFingers.IsNearlyZero() && !OutThumb.IsNearlyZero() && !OutPalm.IsNearlyZero();
}

float ARaftSimCC0CrewVisualActor::MeasurePalmSurfaceOffsetCm(bool bLeft) const
{
    float& Cached = PalmSurfaceOffsetCm[bLeft ? 0 : 1];
    if (Cached >= 0.0f)
    {
        return Cached;
    }
    Cached = 1.9f;
    FVector Wrist, Fingers, Thumb, Palm;
    float Handedness = 1.0f;
    const FTransform* Middle = ReferenceComponentTransforms.Find(SideBone(TEXT("middle_01"), bLeft));
    const USkeletalMesh* Mesh = Body ? Cast<USkeletalMesh>(Body->GetSkinnedAsset()) : nullptr;
    const FSkeletalMeshRenderData* Data = Mesh ? Mesh->GetResourceForRendering() : nullptr;
    const FSkinWeightVertexBuffer* Weights = Body ? Body->GetSkinWeightBuffer(0) : nullptr;
    if (!Middle || !Data || Data->LODRenderData.IsEmpty() || !Weights ||
        !ResolveHandAnatomy(bLeft, Wrist, Fingers, Thumb, Palm, Handedness))
    {
        return Cached;
    }
    const FName HandName = SideBone(TEXT("hand"), bLeft);
    const float Reach = FVector::DotProduct(Middle->GetLocation() * BodyScale - Wrist, Fingers);
    const FSkeletalMeshLODRenderData& LOD = Data->LODRenderData[0];
    const FReferenceSkeleton& Ref = Mesh->GetRefSkeleton();
    float Deepest = -1.0f;
    for (const FSkelMeshRenderSection& Section : LOD.RenderSections)
    {
        for (uint32 V = Section.BaseVertexIndex; V < Section.BaseVertexIndex + Section.NumVertices; ++V)
        {
            int32 Best = INDEX_NONE;
            float BestWeight = 0.0f;
            for (uint32 I = 0; I < Weights->GetMaxBoneInfluences(); ++I)
            {
                const float W = Weights->GetBoneWeight(V, I) / 65535.0f;
                if (W > BestWeight) { BestWeight = W; Best = Weights->GetBoneIndex(V, I); }
            }
            if (Best == INDEX_NONE || BestWeight < 0.5f || !Section.BoneMap.IsValidIndex(Best) ||
                Ref.GetBoneName(Section.BoneMap[Best]) != HandName)
            {
                continue;
            }
            const FVector Offset =
                FVector(LOD.StaticVertexBuffers.PositionVertexBuffer.VertexPosition(V)) * BodyScale - Wrist;
            const float Along = FVector::DotProduct(Offset, Fingers);
            if (Along >= 0.5f * Reach && Along <= Reach &&
                FMath::Abs(FVector::DotProduct(Offset, Thumb)) < 3.0f)
            {
                Deepest = FMath::Max(Deepest, static_cast<float>(FVector::DotProduct(Offset, Palm)));
            }
        }
    }
    if (Deepest > 0.5f && Deepest < 4.0f)
    {
        Cached = Deepest;
    }
    return Cached;
}

bool ARaftSimCC0CrewVisualActor::ResolveGripBar(
    bool bLeft,
    const FRaftSimCrewAvatarPose& Pose,
    FRaftSimCC0GripBar& OutBar) const
{
    FVector Wrist, Fingers, Thumb, Palm;
    float Handedness = 1.0f;
    if (!ResolveHandAnatomy(bLeft, Wrist, Fingers, Thumb, Palm, Handedness))
    {
        return false;
    }
    const FVector GripCm = bLeft ? Pose.LeftHandCm : Pose.RightHandCm;
    FVector BarAxis, PalmFacing, FingerHint;
    if (Pose.bOarGrip)
    {
        // Overhand on an oar handle: the palm over the top, the fingers
        // round the far side, away from the rower.
        BarAxis = (FVector::DistSquared(GripCm, Pose.LeftHandCm) <= FVector::DistSquared(GripCm, Pose.RightHandCm)
            ? Pose.LeftOarAxis : Pose.RightOarAxis).GetSafeNormal();
        OutBar.CenterCm = GripCm;
        OutBar.RadiusCm = OarHandleRadiusCm;
        PalmFacing = -FVector::UpVector;
        FingerHint = GripCm - (bLeft ? Pose.LeftShoulderCm : Pose.RightShoulderCm);
    }
    else
    {
        const FVector Shaft = (Pose.PaddleBottomCm - Pose.PaddleTopCm).GetSafeNormal();
        if (Shaft.IsNearlyZero())
        {
            return false;
        }
        if (!IsUpperTGrip(Pose, GripCm))
        {
            // The shaft hand: thumb up the shaft toward the T-grip, knuckles
            // out over the water when the paddle stands up, and up when it
            // lies across the lap.
            OutBar.CenterCm = FMath::ClosestPointOnSegment(GripCm, Pose.PaddleTopCm, Pose.PaddleBottomCm);
            OutBar.RadiusCm = PaddleShaftRadiusCm;
            OutBar.ThumbAxis = -Shaft;
            const FVector Outboard(0.0f, Pose.PaddleBottomCm.Y >= 0.0f ? 1.0f : -1.0f, 0.0f);
            const FVector Knuckles = FVector::VectorPlaneProject(Outboard + FVector::UpVector * 0.35f, OutBar.ThumbAxis)
                .GetSafeNormal(SMALL_NUMBER, FVector::UpVector);
            OutBar.PalmFacing = -Knuckles;
            return true;
        }
        // The T-grip hand caps the T: the palm presses down the shaft when
        // the paddle stands up and straight down onto the T when it lies
        // across the lap, the fingers round the crossbar's far side.
        const bool bResting = PoseAction == ERaftSimCrewAvatarAction::SeatedIdle;
        BarAxis = URaftSimCrewAvatarPoseLibrary::GetPaddleBladeWidthAxis(Shaft, bResting);
        OutBar.CenterCm = Pose.PaddleTopCm;
        OutBar.RadiusCm = PaddleTGripRadiusCm;
        PalmFacing = FMath::Lerp(-FVector::UpVector, Shaft, FMath::Abs(static_cast<float>(Shaft.Z)));
        FingerHint = FVector::ForwardVector - Shaft;
    }
    if (BarAxis.IsNearlyZero())
    {
        return false;
    }
    PalmFacing = FVector::VectorPlaneProject(PalmFacing, BarAxis)
        .GetSafeNormal(SMALL_NUMBER, FVector::VectorPlaneProject(-FVector::UpVector, BarAxis).GetSafeNormal());
    // The bar's thumb end is whichever leaves the fingers pointing the hinted
    // way for this hand.
    const FVector FingersIfPlus = FVector::CrossProduct(BarAxis, PalmFacing) * Handedness;
    OutBar.ThumbAxis = FVector::DotProduct(FingersIfPlus, FingerHint) >= 0.0 ? BarAxis : -BarAxis;
    OutBar.PalmFacing = PalmFacing;
    if (!Pose.bOarGrip)
    {
        OutBar.CenterCm -= OutBar.ThumbAxis * TGripFistOffsetCm;
    }
    return true;
}

FQuat ARaftSimCC0CrewVisualActor::ResolveGripHandDelta(bool bLeft, const FRaftSimCC0GripBar& Bar) const
{
    FVector Wrist, Fingers, Thumb, Palm;
    float Handedness = 1.0f;
    if (!ResolveHandAnatomy(bLeft, Wrist, Fingers, Thumb, Palm, Handedness))
    {
        return FQuat::Identity;
    }
    const FVector TargetFingers = (FVector::CrossProduct(Bar.ThumbAxis, Bar.PalmFacing) * Handedness).GetSafeNormal();
    const FQuat Reference = FRotationMatrix::MakeFromXZ(Fingers, Palm).ToQuat();
    const FQuat Target = FRotationMatrix::MakeFromXZ(TargetFingers, Bar.PalmFacing).ToQuat();
    return (Target * Reference.Inverse()).GetNormalized();
}

FVector ARaftSimCC0CrewVisualActor::ResolveGripPointInReferenceHandCm(bool bLeft, float RadiusCm) const
{
    FVector Wrist, Fingers, Thumb, Palm;
    float Handedness = 1.0f;
    const FTransform* Middle = ReferenceComponentTransforms.Find(SideBone(TEXT("middle_01"), bLeft));
    if (!Middle || !ResolveHandAnatomy(bLeft, Wrist, Fingers, Thumb, Palm, Handedness))
    {
        return FVector::ZeroVector;
    }
    const FVector ToKnuckle = Middle->GetLocation() * BodyScale - Wrist;
    return Wrist +
        Fingers * (GripAlongPalmFraction * FVector::DotProduct(ToKnuckle, Fingers)) +
        Thumb * FVector::DotProduct(ToKnuckle, Thumb) +
        Palm * (MeasurePalmSurfaceOffsetCm(bLeft) - PalmCompressionCm + RadiusCm);
}

FVector ARaftSimCC0CrewVisualActor::ResolveGripWristCm(bool bLeft, const FRaftSimCC0GripBar& Bar) const
{
    const FTransform* Hand = ReferenceComponentTransforms.Find(SideBone(TEXT("hand"), bLeft));
    if (!Hand)
    {
        return Bar.CenterCm;
    }
    const FVector WristCm = Hand->GetLocation() * BodyScale;
    return Bar.CenterCm -
        ResolveGripHandDelta(bLeft, Bar).RotateVector(ResolveGripPointInReferenceHandCm(bLeft, Bar.RadiusCm) - WristCm);
}

const FRaftSimCC0HandGripShape& ARaftSimCC0CrewVisualActor::ResolveHandGripShape(bool bLeft, float RadiusCm) const
{
    const int32 Key = GripShapeKey(bLeft, RadiusCm);
    if (const FRaftSimCC0HandGripShape* Found = HandGripShapes.Find(Key))
    {
        return *Found;
    }
    FRaftSimCC0HandGripShape& Shape = HandGripShapes.Add(Key);
    FVector Wrist, Fingers, Thumb, Palm;
    float Handedness = 1.0f;
    const FTransform* RefHand = ReferenceComponentTransforms.Find(SideBone(TEXT("hand"), bLeft));
    if (!RefHand || !ResolveHandAnatomy(bLeft, Wrist, Fingers, Thumb, Palm, Handedness))
    {
        return Shape;
    }
    // Everything here is in the reference pose: the bar lies across the
    // resting palm, and each digit is flexed round it.
    const FVector Bar = ResolveGripPointInReferenceHandCm(bLeft, RadiusCm);
    const FVector FlexAxis = TowardPalmAxis(-Handedness * Thumb, Fingers, Palm);
    const auto Location = [this](const FName Bone) { return ReferenceComponentTransforms.FindChecked(Bone).GetLocation() * BodyScale; };
    const auto AddBone = [&](const FName Bone, const FQuat& Flex, const FVector& JointCm)
    {
        const FTransform& Reference = ReferenceComponentTransforms.FindChecked(Bone);
        Shape.Bones.Add(Bone);
        Shape.HandRelative.Add(FTransform((Flex * Reference.GetRotation()).GetNormalized(), JointCm / BodyScale,
            Reference.GetScale3D()).GetRelativeTransform(*RefHand));
    };
    FVector PhalanxMid[2];
    for (int32 FingerIndex = 0; FingerIndex < UE_ARRAY_COUNT(GripFingers); ++FingerIndex)
    {
        const TCHAR* Digit = GripFingers[FingerIndex];
        const FName Bones[] = {DigitBone(Digit, 1, bLeft), DigitBone(Digit, 2, bLeft), DigitBone(Digit, 3, bLeft)};
        if (!ReferenceComponentTransforms.Contains(Bones[0]) || !ReferenceComponentTransforms.Contains(Bones[1]) ||
            !ReferenceComponentTransforms.Contains(Bones[2]))
        {
            continue;
        }
        const FVector J1 = Location(Bones[0]), J2 = Location(Bones[1]), J3 = Location(Bones[2]);
        const FVector Tip = J3 + (J3 - J2) * 0.85;
        const double PadRadius = RadiusCm + FingerPadHalfThicknessCm[FingerIndex];
        // Knuckle (MCP) and middle (PIP) flexion; the end joint follows the
        // middle one, as it does in a closing hand.
        const auto Pose = [&](float A, float B, FVector& OutJ2, FVector& OutJ3, FVector& OutTip)
        {
            const float C = FMath::Min(0.8f * B, 80.0f);
            OutJ2 = J1 + FQuat(FlexAxis, FMath::DegreesToRadians(A)).RotateVector(J2 - J1);
            OutJ3 = OutJ2 + FQuat(FlexAxis, FMath::DegreesToRadians(A + B)).RotateVector(J3 - J2);
            OutTip = OutJ3 + FQuat(FlexAxis, FMath::DegreesToRadians(A + B + C)).RotateVector(Tip - J3);
        };
        const auto Cost = [&](float A, float B)
        {
            FVector P2, P3, PTip;
            Pose(A, B, P2, P3, PTip);
            const FVector Pad = (P3 + PTip) * 0.5;
            const double PadMiss = RadialCm(Pad, Bar, Thumb) - PadRadius;
            const double MiddleMiss = RadialCm(P2, Bar, Thumb) - (PadRadius + 0.2);
            const double TipMiss = RadialCm(PTip, Bar, Thumb) - (PadRadius - 0.1);
            double Cost = 4.0 * PadMiss * PadMiss + MiddleMiss * MiddleMiss + 1.5 * TipMiss * TipMiss;
            for (const FVector& Point : {P2, Pad, PTip})
            {
                const double Inside = RadialCm(Point, Bar, Thumb) - (PadRadius - 0.3);
                if (Inside < 0.0)
                {
                    Cost += 40.0 * Inside * Inside;
                }
            }
            return Cost;
        };
        float BestA = 0.0f, BestB = 0.0f;
        double BestCost = TNumericLimits<double>::Max();
        for (float A = 0.0f; A <= 100.0f; A += 2.5f)
        {
            for (float B = 0.0f; B <= 110.0f; B += 2.5f)
            {
                const double Value = Cost(A, B);
                if (Value < BestCost) { BestCost = Value; BestA = A; BestB = B; }
            }
        }
        const float CoarseA = BestA, CoarseB = BestB;
        for (float A = CoarseA - 2.5f; A <= CoarseA + 2.5f; A += 0.5f)
        {
            for (float B = CoarseB - 2.5f; B <= CoarseB + 2.5f; B += 0.5f)
            {
                const double Value = Cost(A, B);
                if (Value < BestCost) { BestCost = Value; BestA = A; BestB = B; }
            }
        }
        FVector P2, P3, PTip;
        Pose(BestA, BestB, P2, P3, PTip);
        const float C = FMath::Min(0.8f * BestB, 80.0f);
        AddBone(Bones[0], FQuat(FlexAxis, FMath::DegreesToRadians(BestA)), J1);
        AddBone(Bones[1], FQuat(FlexAxis, FMath::DegreesToRadians(BestA + BestB)), P2);
        AddBone(Bones[2], FQuat(FlexAxis, FMath::DegreesToRadians(BestA + BestB + C)), P3);
        Shape.MaximumPadErrorCm = FMath::Max(Shape.MaximumPadErrorCm,
            static_cast<float>(FMath::Abs(RadialCm((P3 + PTip) * 0.5, Bar, Thumb) - PadRadius)));
        if (FingerIndex < 2)
        {
            PhalanxMid[FingerIndex] = (P2 + P3) * 0.5;
        }
    }
    // The thumb closes round the bar the other way, its pad over the middle
    // phalanges of the index and middle fingers.
    const FName ThumbBones[] = {DigitBone(TEXT("thumb"), 1, bLeft), DigitBone(TEXT("thumb"), 2, bLeft), DigitBone(TEXT("thumb"), 3, bLeft)};
    if (ReferenceComponentTransforms.Contains(ThumbBones[0]) && ReferenceComponentTransforms.Contains(ThumbBones[1]) &&
        ReferenceComponentTransforms.Contains(ThumbBones[2]))
    {
        const FVector T1 = Location(ThumbBones[0]), T2 = Location(ThumbBones[1]), T3 = Location(ThumbBones[2]);
        const FVector TTip = T3 + (T3 - T2) * 0.85;
        const FVector Over = (PhalanxMid[0] + PhalanxMid[1]) * 0.5;
        const FVector Outward = FVector::VectorPlaneProject(Over - Bar, Thumb).GetSafeNormal();
        const FVector Target = Over + Outward * (FingerPadHalfThicknessCm[0] + ThumbPadHalfThicknessCm);
        const FVector ThumbFlexAxis = TowardPalmAxis(FVector::CrossProduct((TTip - T1).GetSafeNormal(), Palm), (TTip - T1).GetSafeNormal(), Palm);
        float BestFlex = 0.0f;
        double BestMiss = TNumericLimits<double>::Max();
        FQuat BestSwing = FQuat::Identity;
        for (float Flex = 0.0f; Flex <= 70.0f; Flex += 1.0f)
        {
            const float EndFlex = FMath::Min(1.1f * Flex, 75.0f);
            const FVector P3 = T2 + FQuat(ThumbFlexAxis, FMath::DegreesToRadians(Flex)).RotateVector(T3 - T2);
            const FVector PTip = P3 + FQuat(ThumbFlexAxis, FMath::DegreesToRadians(Flex + EndFlex)).RotateVector(TTip - T3);
            const FVector Pad = (P3 + PTip) * 0.5;
            const FQuat Swing = FQuat::FindBetweenNormals((Pad - T1).GetSafeNormal(), (Target - T1).GetSafeNormal());
            const double Miss = FVector::Distance(T1 + Swing.RotateVector(Pad - T1), Target);
            if (Miss < BestMiss) { BestMiss = Miss; BestFlex = Flex; BestSwing = Swing; }
        }
        const float EndFlex = FMath::Min(1.1f * BestFlex, 75.0f);
        const FQuat Flex2(ThumbFlexAxis, FMath::DegreesToRadians(BestFlex));
        const FQuat Flex3(ThumbFlexAxis, FMath::DegreesToRadians(BestFlex + EndFlex));
        const FVector P3 = T2 + Flex2.RotateVector(T3 - T2);
        AddBone(ThumbBones[0], BestSwing, T1);
        AddBone(ThumbBones[1], BestSwing * Flex2, T1 + BestSwing.RotateVector(T2 - T1));
        AddBone(ThumbBones[2], BestSwing * Flex3, T1 + BestSwing.RotateVector(P3 - T1));
        Shape.ThumbPadErrorCm = static_cast<float>(BestMiss);
    }
    UE_LOG(LogTemp, Display, TEXT("RaftSim CC0 grip shape %s hand radius=%.2fcm palm_surface=%.2fcm pad_error=%.2fcm thumb_error=%.2fcm"),
        bLeft ? TEXT("left") : TEXT("right"), RadiusCm, MeasurePalmSurfaceOffsetCm(bLeft), Shape.MaximumPadErrorCm, Shape.ThumbPadErrorCm);
    return Shape;
}

void ARaftSimCC0CrewVisualActor::ApplyHandGripShape(bool bLeft, float RadiusCm)
{
    if (!Body)
    {
        return;
    }
    const FRaftSimCC0HandGripShape& Shape = ResolveHandGripShape(bLeft, RadiusCm);
    const FTransform Hand = Body->GetBoneTransformByName(SideBone(TEXT("hand"), bLeft), EBoneSpaces::ComponentSpace);
    for (int32 Index = 0; Index < Shape.Bones.Num(); ++Index)
    {
        Body->SetBoneTransformByName(Shape.Bones[Index], Shape.HandRelative[Index] * Hand, EBoneSpaces::ComponentSpace);
    }
}

void ARaftSimCC0CrewVisualActor::ApplyFingerChain(bool bLeft, const TCHAR* Digit, float GripAlpha)
{
    if (!Body || !Digit)
    {
        return;
    }
    FVector Wrist, Fingers, Thumb, Palm;
    float Handedness = 1.0f;
    const FTransform* RefHand = ReferenceComponentTransforms.Find(SideBone(TEXT("hand"), bLeft));
    const bool bThumb = FCString::Strcmp(Digit, TEXT("thumb")) == 0;
    const FName Bones[] = {DigitBone(Digit, 1, bLeft), DigitBone(Digit, 2, bLeft), DigitBone(Digit, 3, bLeft)};
    if (!RefHand || !ResolveHandAnatomy(bLeft, Wrist, Fingers, Thumb, Palm, Handedness) ||
        !ReferenceComponentTransforms.Contains(Bones[0]) || !ReferenceComponentTransforms.Contains(Bones[1]) ||
        !ReferenceComponentTransforms.Contains(Bones[2]))
    {
        return;
    }
    // A relaxed curl toward the palm, built in the reference hand and carried
    // by the hand bone as it stands now.
    const FVector J1 = ReferenceComponentTransforms.FindChecked(Bones[0]).GetLocation();
    const FVector J2 = ReferenceComponentTransforms.FindChecked(Bones[1]).GetLocation();
    const FVector J3 = ReferenceComponentTransforms.FindChecked(Bones[2]).GetLocation();
    const FVector Direction = (J3 - J1).GetSafeNormal();
    const FVector Axis = bThumb
        ? TowardPalmAxis(FVector::CrossProduct(Direction, Palm), Direction, Palm)
        : TowardPalmAxis(-Handedness * Thumb, Fingers, Palm);
    const float Angles[] = {
        bThumb ? 0.0f : RelaxedFingerCurlDegrees[0] * GripAlpha,
        (bThumb ? RelaxedThumbCurlDegrees[0] : RelaxedFingerCurlDegrees[1]) * GripAlpha,
        (bThumb ? RelaxedThumbCurlDegrees[1] : RelaxedFingerCurlDegrees[2]) * GripAlpha};
    const FQuat Q1(Axis, FMath::DegreesToRadians(Angles[0]));
    const FQuat Q2(Axis, FMath::DegreesToRadians(Angles[0] + Angles[1]));
    const FQuat Q3(Axis, FMath::DegreesToRadians(Angles[0] + Angles[1] + Angles[2]));
    const FVector P2 = J1 + Q1.RotateVector(J2 - J1);
    const FVector P3 = P2 + Q2.RotateVector(J3 - J2);
    const FTransform Hand = Body->GetBoneTransformByName(SideBone(TEXT("hand"), bLeft), EBoneSpaces::ComponentSpace);
    const FQuat Flex[] = {Q1, Q2, Q3};
    const FVector Joints[] = {J1, P2, P3};
    for (int32 Segment = 0; Segment < 3; ++Segment)
    {
        const FTransform& Reference = ReferenceComponentTransforms.FindChecked(Bones[Segment]);
        const FTransform Relative = FTransform((Flex[Segment] * Reference.GetRotation()).GetNormalized(), Joints[Segment],
            Reference.GetScale3D()).GetRelativeTransform(*RefHand);
        Body->SetBoneTransformByName(Bones[Segment], Relative * Hand, EBoneSpaces::ComponentSpace);
    }
}

float ARaftSimCC0CrewVisualActor::ForearmTwistDegrees(
    bool bLeft,
    const FVector& ElbowCm,
    const FVector& WristCm,
    const FQuat& HandRotation) const
{
    const FTransform* RefLower = ReferenceComponentTransforms.Find(SideBone(TEXT("lowerarm"), bLeft));
    const FTransform* RefHand = ReferenceComponentTransforms.Find(SideBone(TEXT("hand"), bLeft));
    const FVector Along = (WristCm - ElbowCm).GetSafeNormal();
    if (!RefLower || !RefHand || Along.IsNearlyZero())
    {
        return 0.0f;
    }
    const FVector RestAlong = (RefHand->GetLocation() - RefLower->GetLocation()).GetSafeNormal();
    // The hand as the swung forearm carries it, with a straight wrist.
    const FQuat Neutral = (FQuat::FindBetweenNormals(RestAlong, Along) * RefHand->GetRotation()).GetNormalized();
    const FQuat Relative = (HandRotation * Neutral.Inverse()).GetNormalized();
    const double Twist = 2.0 * FMath::Atan2(FVector::DotProduct(FVector(Relative.X, Relative.Y, Relative.Z), Along), Relative.W);
    return static_cast<float>(FMath::RadiansToDegrees(FMath::UnwindRadians(Twist)));
}

float ARaftSimCC0CrewVisualActor::MeasurePaddleGripAnchorErrorCm(bool bLeft, const FRaftSimCrewAvatarPose& Pose) const
{
    FRaftSimCC0GripBar Bar;
    const FTransform* RefHand = ReferenceComponentTransforms.Find(SideBone(TEXT("hand"), bLeft));
    if (!Body || !RefHand || !ResolveGripBar(bLeft, Pose, Bar))
    {
        return TNumericLimits<float>::Max();
    }
    const FTransform Hand = Body->GetBoneTransformByName(SideBone(TEXT("hand"), bLeft), EBoneSpaces::ComponentSpace);
    const FQuat Delta = (Hand.GetRotation() * RefHand->GetRotation().Inverse()).GetNormalized();
    const FVector Rendered = Hand.GetLocation() * BodyScale +
        Delta.RotateVector(ResolveGripPointInReferenceHandCm(bLeft, Bar.RadiusCm) - RefHand->GetLocation() * BodyScale);
    return FVector::Distance(Rendered, Bar.CenterCm);
}

float ARaftSimCC0CrewVisualActor::MeasureMaximumPaddleFingerContactErrorCm(const FRaftSimCrewAvatarPose& Pose) const
{
    if (!Body || !HasHeldGrip(Pose))
    {
        return 0.0f;
    }
    float Maximum = 0.0f;
    for (const bool bLeft : {true, false})
    {
        FRaftSimCC0GripBar Bar;
        if (!ResolveGripBar(bLeft, Pose, Bar))
        {
            return TNumericLimits<float>::Max();
        }
        for (int32 FingerIndex = 0; FingerIndex < UE_ARRAY_COUNT(GripFingers); ++FingerIndex)
        {
            const FVector J2 = Body->GetBoneTransformByName(DigitBone(GripFingers[FingerIndex], 2, bLeft), EBoneSpaces::ComponentSpace).GetLocation() * BodyScale;
            const FVector J3 = Body->GetBoneTransformByName(DigitBone(GripFingers[FingerIndex], 3, bLeft), EBoneSpaces::ComponentSpace).GetLocation() * BodyScale;
            const FVector Pad = J3 + (J3 - J2) * 0.425;
            Maximum = FMath::Max(Maximum, static_cast<float>(FMath::Abs(
                RadialCm(Pad, Bar.CenterCm, Bar.ThumbAxis) - (Bar.RadiusCm + FingerPadHalfThicknessCm[FingerIndex]))));
        }
    }
    return Maximum;
}

float ARaftSimCC0CrewVisualActor::MeasureMaximumPaddleThumbContactErrorCm(const FRaftSimCrewAvatarPose& Pose) const
{
    if (!Body || !HasHeldGrip(Pose))
    {
        return 0.0f;
    }
    float Maximum = 0.0f;
    for (const bool bLeft : {true, false})
    {
        FRaftSimCC0GripBar Bar;
        if (!ResolveGripBar(bLeft, Pose, Bar))
        {
            return TNumericLimits<float>::Max();
        }
        // The thumb pad rides on the index and middle fingers' middle
        // phalanges, outside the bar.
        const auto Mid = [&](const TCHAR* Digit)
        {
            return (Body->GetBoneTransformByName(DigitBone(Digit, 2, bLeft), EBoneSpaces::ComponentSpace).GetLocation() +
                Body->GetBoneTransformByName(DigitBone(Digit, 3, bLeft), EBoneSpaces::ComponentSpace).GetLocation()) * 0.5 * BodyScale;
        };
        const FVector Over = (Mid(TEXT("index")) + Mid(TEXT("middle"))) * 0.5;
        const FVector Target = Over + FVector::VectorPlaneProject(Over - Bar.CenterCm, Bar.ThumbAxis).GetSafeNormal() *
            (FingerPadHalfThicknessCm[0] + ThumbPadHalfThicknessCm);
        const FVector T2 = Body->GetBoneTransformByName(DigitBone(TEXT("thumb"), 2, bLeft), EBoneSpaces::ComponentSpace).GetLocation() * BodyScale;
        const FVector T3 = Body->GetBoneTransformByName(DigitBone(TEXT("thumb"), 3, bLeft), EBoneSpaces::ComponentSpace).GetLocation() * BodyScale;
        const FVector Pad = T3 + (T3 - T2) * 0.425;
        Maximum = FMath::Max(Maximum, static_cast<float>(FVector::Distance(Pad, Target)));
    }
    return Maximum;
}

void ARaftSimCC0CrewVisualActor::MeasurePaddleGripOrientation(
    const FRaftSimCrewAvatarPose& Pose,
    float& OutMinimumPalmFacingDot,
    float& OutMinimumFingerCurlTowardPalm) const
{
    OutMinimumPalmFacingDot = 1.0f;
    OutMinimumFingerCurlTowardPalm = 1.0f;
    if (!Body || !HasHeldGrip(Pose))
    {
        return;
    }
    for (const bool bLeft : {true, false})
    {
        FVector Wrist, Fingers, Thumb, Palm;
        float Handedness = 1.0f;
        FRaftSimCC0GripBar Bar;
        const FTransform* RefHand = ReferenceComponentTransforms.Find(SideBone(TEXT("hand"), bLeft));
        if (!RefHand || !ResolveGripBar(bLeft, Pose, Bar) || !ResolveHandAnatomy(bLeft, Wrist, Fingers, Thumb, Palm, Handedness))
        {
            OutMinimumPalmFacingDot = -1.0f;
            continue;
        }
        const FTransform Hand = Body->GetBoneTransformByName(SideBone(TEXT("hand"), bLeft), EBoneSpaces::ComponentSpace);
        const FQuat Delta = (Hand.GetRotation() * RefHand->GetRotation().Inverse()).GetNormalized();
        const FVector RenderedPalm = Delta.RotateVector(Palm);
        // From the middle of the palm to the bar's axis.
        const FVector PalmMiddle = Hand.GetLocation() * BodyScale + Delta.RotateVector(
            (ResolveGripPointInReferenceHandCm(bLeft, Bar.RadiusCm) - Palm * Bar.RadiusCm) - Wrist);
        const FVector ToBar = FVector::VectorPlaneProject(Bar.CenterCm - PalmMiddle, Bar.ThumbAxis).GetSafeNormal();
        OutMinimumPalmFacingDot = FMath::Min(OutMinimumPalmFacingDot, static_cast<float>(FVector::DotProduct(RenderedPalm, ToBar)));
        // Each finger bends about the knuckle line in the palm's sense: the
        // turn from its first to its second bone is about the flex axis, not
        // against it (a finger bent backwards turns the other way).
        const FVector FlexAxis = Delta.RotateVector(TowardPalmAxis(-Handedness * Thumb, Fingers, Palm));
        for (const TCHAR* Digit : GripFingers)
        {
            const FVector J1 = Body->GetBoneTransformByName(DigitBone(Digit, 1, bLeft), EBoneSpaces::ComponentSpace).GetLocation();
            const FVector J2 = Body->GetBoneTransformByName(DigitBone(Digit, 2, bLeft), EBoneSpaces::ComponentSpace).GetLocation();
            const FVector J3 = Body->GetBoneTransformByName(DigitBone(Digit, 3, bLeft), EBoneSpaces::ComponentSpace).GetLocation();
            const FVector Turn = FVector::CrossProduct((J2 - J1).GetSafeNormal(), (J3 - J2).GetSafeNormal()).GetSafeNormal();
            OutMinimumFingerCurlTowardPalm = FMath::Min(OutMinimumFingerCurlTowardPalm,
                static_cast<float>(FVector::DotProduct(Turn, FlexAxis)));
        }
    }
}
