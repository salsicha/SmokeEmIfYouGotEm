// Paddle, T-grip and oar grips for the CC0 crew bodies (2026-10-07 rewrite).
//
// Every grip is a hand closed round a bar: the paddle shaft, the T-grip's
// crossbar, or an oar handle. A grip names only the bar's axis (pointing to
// the thumb's side of the fist) and the way the palm faces; the finger
// direction then follows from the hand's own anatomy, so a grip cannot come
// out mirrored. The wrist is placed so the bar lies across the palm just
// below the knuckles, the fingers flex toward the palm until their pads sit
// on the bar, the thumb closes round the other way over the fingers, and the
// forearm takes most of any twist so the wrist does not wring. Each grip
// turns about its bar toward the forearm that carries it, so the wrist bends
// only as far as a real one.
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
// A gripping finger closes this share of the way to the middle finger's line:
// the bodies' rest hands are spread, and gripped that way the fingers stood
// apart round the shaft like a claw.
constexpr float GripFingerAdduction = 0.85f;
// The thumb closes this far round the bar, the other way from the fingers,
// measured from where the palm meets the bar; its pad may stand this far off
// the bar's surface where it rides on the fingertips.
constexpr float ThumbWrapDegrees = 140.0f;
constexpr float ThumbHugCm = 0.6f;
// A grip lays its bar diagonally across the palm in steps of this many
// degrees (each step has its own solved finger and thumb shape).
constexpr float GripObliqueStepDegrees = 5.0f;
// Closing round a bar laid toward the fingers, the fingers converge toward
// the base of the thumb, the little finger most: up to this many degrees at
// GripObliqueFullConvergenceDegrees. Flexed in parallel, the little finger
// could not reach the bar under the heel of the hand and curled tight beside
// it ("the pinkie finger is wrapped tight and not around the t grip",
// 2026-10-07).
constexpr float GripFingerConvergenceDegrees = 20.0f;
constexpr float GripObliqueFullConvergenceDegrees = 40.0f;
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

// Angle round the bar in degrees, measured from where the palm meets it, in
// the sense the fingers close (IndexPip is the index finger's middle joint).
double WrapDegrees(const FVector& Point, const FVector& BarPoint, const FVector& BarAxis, const FVector& TowardPalm,
    const FVector& IndexPip)
{
    const FVector Axis = BarAxis.GetSafeNormal();
    const FVector E0 = FVector::VectorPlaneProject(TowardPalm, Axis).GetSafeNormal();
    const FVector E1 = FVector::CrossProduct(Axis, E0);
    const auto Angle = [&](const FVector& Q)
    {
        const FVector D = FVector::VectorPlaneProject(Q - BarPoint, Axis);
        return FMath::RadiansToDegrees(FMath::Atan2(FVector::DotProduct(D, E1), FVector::DotProduct(D, E0)));
    };
    return Angle(IndexPip) >= 0.0 ? Angle(Point) : -Angle(Point);
}

// How far a thumb pad falls short of closing round the bar against the
// fingers: its stand-off from the bar beyond a light hug, plus the arc it
// still lacks of ThumbWrapDegrees round the bar the other way.
float ThumbWrapShortfallCm(const FVector& Pad, const FVector& BarPoint, const FVector& BarAxis, const FVector& TowardPalm,
    const FVector& IndexPip, float RadiusCm)
{
    const double PadRadius = RadialCm(Pad, BarPoint, BarAxis.GetSafeNormal());
    const double Loose = FMath::Max(0.0, PadRadius - (RadiusCm + ThumbPadHalfThicknessCm + ThumbHugCm));
    const double Short = FMath::Max(0.0, ThumbWrapDegrees + WrapDegrees(Pad, BarPoint, BarAxis, TowardPalm, IndexPip));
    return static_cast<float>(Loose + FMath::DegreesToRadians(Short) * PadRadius);
}

// Flex axis that turns a digit toward the palm: rotating Direction a little
// about it moves it toward Palm.
FVector TowardPalmAxis(const FVector& Candidate, const FVector& Direction, const FVector& Palm)
{
    const FVector Axis = Candidate.GetSafeNormal();
    const FVector Moved = FQuat(Axis, 0.2f).RotateVector(Direction) - Direction;
    return FVector::DotProduct(Moved, Palm) >= 0.0f ? Axis : -Axis;
}

int32 GripShapeKey(bool bLeft, float RadiusCm, float ObliqueDegrees)
{
    return (bLeft ? 1 : 0) | (FMath::RoundToInt(RadiusCm * 100.0f) << 1) |
        ((FMath::RoundToInt(ObliqueDegrees / GripObliqueStepDegrees) + 64) << 20);
}

// The bar's axis in the reference hand: across the palm from the little
// finger's side to the thumb's, turned in the palm's plane by ObliqueDegrees
// (positive turns the thumb end toward the fingers).
FVector ObliqueBarAxis(const FVector& Thumb, const FVector& Fingers, const FVector& Palm, float ObliqueDegrees)
{
    const FVector Turned = FQuat(Palm, FMath::DegreesToRadians(ObliqueDegrees)).RotateVector(Thumb);
    return FVector::DotProduct(Turned - Thumb, Fingers) * ObliqueDegrees >= 0.0f
        ? Turned : FQuat(Palm, -FMath::DegreesToRadians(ObliqueDegrees)).RotateVector(Thumb);
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
            TurnGripTowardForearm(bLeft, OutBar, Handedness, 0.8f, 70.0f);
            LayGripAlongForearm(bLeft, OutBar, -15.0f, 40.0f);
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
    // The T-grip palm stays on top of the crossbar (the thumb under it), so it
    // turns only part way.
    TurnGripTowardForearm(bLeft, OutBar, Handedness, Pose.bOarGrip ? 0.6f : 0.5f, Pose.bOarGrip ? 45.0f : 40.0f);
    LayGripAlongForearm(bLeft, OutBar, -15.0f, 40.0f);
    return true;
}

void ARaftSimCC0CrewVisualActor::LayGripAlongForearm(
    bool bLeft,
    FRaftSimCC0GripBar& Bar,
    float MinDegrees,
    float MaxDegrees) const
{
    // A hand closed round a bar holds it diagonally across the palm as the
    // forearm needs: square across the palm, a bar the forearm meets at a
    // slant bent the wrist sideways past anything a wrist can do. The
    // crossbar of the T-grip runs nearly along the forearm reaching across
    // the body to it, and the shaft nearly along the forearm reaching down
    // to it: the wrists stood 75 and 55 degrees off the forearm sideways
    // ("the paddle should never be directly next to the character since a
    // person's wrists can't bend like that", 2026-10-07). Lay the bar so the
    // hand runs on from the forearm, within what a grip allows.
    const FVector Forearm = FVector::VectorPlaneProject(GripForearmHint[bLeft ? 0 : 1], Bar.PalmFacing).GetSafeNormal();
    const FVector Axis = Bar.ThumbAxis.GetSafeNormal();
    if (Forearm.IsNearlyZero() || Axis.IsNearlyZero())
    {
        Bar.ObliqueDegrees = 0.0f;
        return;
    }
    // The hand's line meets the thumb end at 90 degrees less the oblique
    // angle; make it meet it where the forearm does.
    const float ForearmToThumbEnd = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(
        static_cast<float>(FVector::DotProduct(Forearm, Axis)), -1.0f, 1.0f)));
    Bar.ObliqueDegrees = GripObliqueStepDegrees *
        FMath::RoundToFloat(FMath::Clamp(90.0f - ForearmToThumbEnd, MinDegrees, MaxDegrees) / GripObliqueStepDegrees);
}

void ARaftSimCC0CrewVisualActor::TurnGripTowardForearm(
    bool bLeft,
    FRaftSimCC0GripBar& Bar,
    float Handedness,
    float Share,
    float MaxDegrees) const
{
    // A hand round a bar can turn about it; a real one turns so the back of
    // the hand runs on from the forearm. Grips set by the bar alone (palm
    // flat down on the T, knuckles always out on the shaft) bent the wrists
    // to impossible angles mid-stroke ("both wrists look broken and twisted
    // at impossible angles", 2026-10-07). Turn the grip about the bar by a
    // share of the angle between the hand's line (wrist to knuckles) and the
    // forearm's, as seen down the bar.
    const FVector Forearm = GripForearmHint[bLeft ? 0 : 1];
    const FVector Axis = Bar.ThumbAxis.GetSafeNormal();
    const FVector HandLine = (FVector::CrossProduct(Axis, Bar.PalmFacing) * Handedness).GetSafeNormal();
    const FVector Wanted = FVector::VectorPlaneProject(Forearm, Axis).GetSafeNormal();
    if (Forearm.IsNearlyZero() || Axis.IsNearlyZero() || HandLine.IsNearlyZero() || Wanted.IsNearlyZero())
    {
        return;
    }
    const float Angle = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(
        static_cast<float>(FVector::DotProduct(HandLine, Wanted)), -1.0f, 1.0f)));
    const float Turn = FMath::Min(Angle * Share, MaxDegrees);
    // Whichever sense of turn brings the hand's line toward the forearm.
    const FQuat Plus(Axis, FMath::DegreesToRadians(Turn));
    const FQuat Minus(Axis, -FMath::DegreesToRadians(Turn));
    const FQuat Chosen = FVector::DotProduct(Plus.RotateVector(HandLine), Wanted) >=
        FVector::DotProduct(Minus.RotateVector(HandLine), Wanted) ? Plus : Minus;
    Bar.PalmFacing = Chosen.RotateVector(Bar.PalmFacing).GetSafeNormal();
}

FQuat ARaftSimCC0CrewVisualActor::ResolveGripHandDelta(bool bLeft, const FRaftSimCC0GripBar& Bar) const
{
    FVector Wrist, Fingers, Thumb, Palm;
    float Handedness = 1.0f;
    if (!ResolveHandAnatomy(bLeft, Wrist, Fingers, Thumb, Palm, Handedness))
    {
        return FQuat::Identity;
    }
    // The reference hand's bar (diagonal across the palm by the grip's
    // oblique angle) onto the bar, the palm onto the way it faces.
    const FQuat Reference = FRotationMatrix::MakeFromXZ(ObliqueBarAxis(Thumb, Fingers, Palm, Bar.ObliqueDegrees), Palm).ToQuat();
    const FQuat Target = FRotationMatrix::MakeFromXZ(Bar.ThumbAxis, Bar.PalmFacing).ToQuat();
    return (Target * Reference.Inverse()).GetNormalized();
}

FVector ARaftSimCC0CrewVisualActor::ResolveGripPointInReferenceHandCm(bool bLeft, float RadiusCm, float ObliqueDegrees) const
{
    FVector Wrist, Fingers, Thumb, Palm;
    float Handedness = 1.0f;
    const FTransform* Middle = ReferenceComponentTransforms.Find(SideBone(TEXT("middle_01"), bLeft));
    const FTransform* Pinky = ReferenceComponentTransforms.Find(SideBone(TEXT("pinky_01"), bLeft));
    if (!Middle || !Pinky || !ResolveHandAnatomy(bLeft, Wrist, Fingers, Thumb, Palm, Handedness))
    {
        return FVector::ZeroVector;
    }
    const FVector ToKnuckle = Middle->GetLocation() * BodyScale - Wrist;
    const FVector Point = Wrist +
        Fingers * (GripAlongPalmFraction * FVector::DotProduct(ToKnuckle, Fingers)) +
        Thumb * FVector::DotProduct(ToKnuckle, Thumb) +
        Palm * (MeasurePalmSurfaceOffsetCm(bLeft) - PalmCompressionCm + RadiusCm);
    if (ObliqueDegrees >= 0.0f)
    {
        return Point;
    }
    // A bar laid with its thumb end toward the wrist turns about the little
    // finger's line: the index end swings in toward the web of the thumb and
    // the little finger keeps its wrap. Turned about the middle finger, the
    // bar's little-finger end slid out under the finger's first segment,
    // which barely bent round it.
    const FVector Pivot = Point + Thumb * FVector::DotProduct(Pinky->GetLocation() * BodyScale - Middle->GetLocation() * BodyScale, Thumb);
    const FVector Axis = ObliqueBarAxis(Thumb, Fingers, Palm, ObliqueDegrees);
    return Pivot + Axis * FVector::DotProduct(Point - Pivot, Axis);
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
        ResolveGripHandDelta(bLeft, Bar).RotateVector(ResolveGripPointInReferenceHandCm(bLeft, Bar.RadiusCm, Bar.ObliqueDegrees) - WristCm);
}

const FRaftSimCC0HandGripShape& ARaftSimCC0CrewVisualActor::ResolveHandGripShape(bool bLeft, float RadiusCm, float ObliqueDegrees) const
{
    const int32 Key = GripShapeKey(bLeft, RadiusCm, ObliqueDegrees);
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
    const FVector Bar = ResolveGripPointInReferenceHandCm(bLeft, RadiusCm, ObliqueDegrees);
    // The bar crosses the palm at that point, diagonally by ObliqueDegrees.
    const FVector BarAxis = ObliqueBarAxis(Thumb, Fingers, Palm, ObliqueDegrees);
    const FVector FlexAxis = TowardPalmAxis(-Handedness * Thumb, Fingers, Palm);
    const auto Location = [this](const FName Bone) { return ReferenceComponentTransforms.FindChecked(Bone).GetLocation() * BodyScale; };
    const auto AddBone = [&](const FName Bone, const FQuat& Flex, const FVector& JointCm)
    {
        const FTransform& Reference = ReferenceComponentTransforms.FindChecked(Bone);
        Shape.Bones.Add(Bone);
        Shape.HandRelative.Add(FTransform((Flex * Reference.GetRotation()).GetNormalized(), JointCm / BodyScale,
            Reference.GetScale3D()).GetRelativeTransform(*RefHand));
    };
    FVector IndexPip = Bar;
    TArray<FVector, TInlineAllocator<28>> FingerPoints;
    const auto InPalmPlane = [&Palm](const FVector& V) { return FVector::VectorPlaneProject(V, Palm).GetSafeNormal(); };
    const FName MiddleBones[] = {DigitBone(TEXT("middle"), 1, bLeft), DigitBone(TEXT("middle"), 2, bLeft)};
    const FVector MiddleLine = ReferenceComponentTransforms.Contains(MiddleBones[0]) && ReferenceComponentTransforms.Contains(MiddleBones[1])
        ? InPalmPlane(Location(MiddleBones[1]) - Location(MiddleBones[0])) : Fingers;
    for (int32 FingerIndex = 0; FingerIndex < UE_ARRAY_COUNT(GripFingers); ++FingerIndex)
    {
        const TCHAR* Digit = GripFingers[FingerIndex];
        const FName Bones[] = {DigitBone(Digit, 1, bLeft), DigitBone(Digit, 2, bLeft), DigitBone(Digit, 3, bLeft)};
        if (!ReferenceComponentTransforms.Contains(Bones[0]) || !ReferenceComponentTransforms.Contains(Bones[1]) ||
            !ReferenceComponentTransforms.Contains(Bones[2]))
        {
            continue;
        }
        // Close the finger toward the middle finger's line, about the palm's
        // normal at its knuckle, before it flexes round the bar.
        const FVector J1 = Location(Bones[0]);
        const FVector Own = InPalmPlane(Location(Bones[1]) - J1);
        const float Spread = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(
            static_cast<float>(FVector::DotProduct(Own, MiddleLine)), -1.0f, 1.0f))) * GripFingerAdduction;
        const FQuat AddPlus(Palm, FMath::DegreesToRadians(Spread)), AddMinus(Palm, -FMath::DegreesToRadians(Spread));
        const FQuat Add = FVector::DotProduct(AddPlus.RotateVector(Own), MiddleLine) >=
            FVector::DotProduct(AddMinus.RotateVector(Own), MiddleLine) ? AddPlus : AddMinus;
        const FVector J2 = J1 + Add.RotateVector(Location(Bones[1]) - J1);
        const FVector J3 = J1 + Add.RotateVector(Location(Bones[2]) - J1);
        const FVector Tip = J3 + (J3 - J2) * 0.85;
        const double PadRadius = RadiusCm + FingerPadHalfThicknessCm[FingerIndex];
        // Closing, the finger converges toward the base of the thumb by its
        // share of the grip's convergence (none for the index finger).
        const float Converge = GripFingerConvergenceDegrees * FingerIndex / 3.0f *
            FMath::Clamp(ObliqueDegrees / GripObliqueFullConvergenceDegrees, 0.0f, 1.0f);
        const FVector ConvergePlus = FQuat(Palm, FMath::DegreesToRadians(Converge)).RotateVector(FlexAxis);
        const FVector ConvergeMinus = FQuat(Palm, -FMath::DegreesToRadians(Converge)).RotateVector(FlexAxis);
        const FVector FingerFlexAxis = FVector::DotProduct(FQuat(ConvergePlus, HALF_PI).RotateVector((J2 - J1).GetSafeNormal()), Thumb) >=
            FVector::DotProduct(FQuat(ConvergeMinus, HALF_PI).RotateVector((J2 - J1).GetSafeNormal()), Thumb) ? ConvergePlus : ConvergeMinus;
        // Knuckle (MCP) and middle (PIP) flexion; the end joint follows the
        // middle one, as it does in a closing hand.
        const auto Pose = [&](float A, float B, FVector& OutJ2, FVector& OutJ3, FVector& OutTip)
        {
            const float C = FMath::Min(0.8f * B, 80.0f);
            OutJ2 = J1 + FQuat(FingerFlexAxis, FMath::DegreesToRadians(A)).RotateVector(J2 - J1);
            OutJ3 = OutJ2 + FQuat(FingerFlexAxis, FMath::DegreesToRadians(A + B)).RotateVector(J3 - J2);
            OutTip = OutJ3 + FQuat(FingerFlexAxis, FMath::DegreesToRadians(A + B + C)).RotateVector(Tip - J3);
        };
        const auto Cost = [&](float A, float B)
        {
            FVector P2, P3, PTip;
            Pose(A, B, P2, P3, PTip);
            const FVector Pad = (P3 + PTip) * 0.5;
            const double PadMiss = RadialCm(Pad, Bar, BarAxis) - PadRadius;
            const double MiddleMiss = RadialCm(P2, Bar, BarAxis) - (PadRadius + 0.2);
            const double TipMiss = RadialCm(PTip, Bar, BarAxis) - (PadRadius - 0.1);
            // The pad seats on the bar first: a bar laid diagonally across
            // the palm crosses each finger's bending plane at a slant, so the
            // middle joint and the tip cannot all sit at the pad's radius.
            double Cost = 16.0 * PadMiss * PadMiss + MiddleMiss * MiddleMiss + 1.5 * TipMiss * TipMiss;
            for (const FVector& Point : {P2, Pad, PTip})
            {
                const double Inside = RadialCm(Point, Bar, BarAxis) - (PadRadius - 0.3);
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
        AddBone(Bones[0], FQuat(FingerFlexAxis, FMath::DegreesToRadians(BestA)) * Add, J1);
        AddBone(Bones[1], FQuat(FingerFlexAxis, FMath::DegreesToRadians(BestA + BestB)) * Add, P2);
        AddBone(Bones[2], FQuat(FingerFlexAxis, FMath::DegreesToRadians(BestA + BestB + C)) * Add, P3);
        Shape.MaximumPadErrorCm = FMath::Max(Shape.MaximumPadErrorCm,
            static_cast<float>(FMath::Abs(RadialCm((P3 + PTip) * 0.5, Bar, BarAxis) - PadRadius)));
        if (FingerIndex == 0)
        {
            IndexPip = P2;
        }
        FingerPoints.Append({J1, P2, P3, PTip, (J1 + P2) * 0.5, (P2 + P3) * 0.5, (P3 + PTip) * 0.5});
    }
    // The thumb closes round the bar the other way from the fingers, as in a
    // fist round a handle: from the palm's thumb side it wraps ThumbWrapDegrees
    // round the bar, its end curled round it and its pad on the bar or riding
    // on the fingertips, level with the index finger. The search swings the
    // whole thumb at its base (round the bar, across it, and about its own
    // length) and bends its two joints, keeping every part of it outside the
    // bar and off the fingers. Aimed at the outside of the index finger, which
    // lies out of the thumb's reach round the far side of the bar, the thumb
    // stopped short beside the T-grip and along the shaft instead of under and
    // round them ("the thumb should go under the t grip and around the shaft,
    // in both cases in opposition to the other fingers", 2026-10-07).
    const FName ThumbBones[] = {DigitBone(TEXT("thumb"), 1, bLeft), DigitBone(TEXT("thumb"), 2, bLeft), DigitBone(TEXT("thumb"), 3, bLeft)};
    if (ReferenceComponentTransforms.Contains(ThumbBones[0]) && ReferenceComponentTransforms.Contains(ThumbBones[1]) &&
        ReferenceComponentTransforms.Contains(ThumbBones[2]))
    {
        const FVector T1 = Location(ThumbBones[0]), T2 = Location(ThumbBones[1]), T3 = Location(ThumbBones[2]);
        const FVector TTip = T3 + (T3 - T2) * 0.85;
        const double AxialGoal = FVector::DotProduct(IndexPip - Bar, BarAxis);
        const FVector Length = (TTip - T1).GetSafeNormal();
        const FVector ThumbFlexAxis = TowardPalmAxis(FVector::CrossProduct(Length, Palm), Length, Palm);
        const FVector Across = FVector::CrossProduct(BarAxis, Length).GetSafeNormal();
        struct FThumbPose { FQuat Swing; FVector Axis, P2, P3, PTip; };
        const auto PoseThumb = [&](float Round, float Over_, float Roll, float Mcp, float Ip)
        {
            FThumbPose Out;
            Out.Swing = FQuat(BarAxis, FMath::DegreesToRadians(Round)) * FQuat(Across, FMath::DegreesToRadians(Over_)) *
                FQuat(Length, FMath::DegreesToRadians(Roll));
            Out.Axis = Out.Swing.RotateVector(ThumbFlexAxis);
            Out.P2 = T1 + Out.Swing.RotateVector(T2 - T1);
            const FQuat Base(Out.Axis, FMath::DegreesToRadians(Mcp));
            Out.P3 = Out.P2 + Base.RotateVector(Out.Swing.RotateVector(T3 - T2));
            const FVector Tip = Out.P2 + Base.RotateVector(Out.Swing.RotateVector(TTip - T2));
            Out.PTip = Out.P3 + FQuat(Out.Axis, FMath::DegreesToRadians(Ip)).RotateVector(Tip - Out.P3);
            return Out;
        };
        const auto ThumbCost = [&](float Round, float Over_, float Roll, float Mcp, float Ip)
        {
            const FThumbPose P = PoseThumb(Round, Over_, Roll, Mcp, Ip);
            const FVector Pad = (P.P3 + P.PTip) * 0.5;
            // Round the bar the other way from the fingers, hugging it, level
            // with the index finger.
            const double Short = FMath::Max(0.0, ThumbWrapDegrees + WrapDegrees(Pad, Bar, BarAxis, -Palm, IndexPip));
            double Cost = FMath::Square(Short / 10.0);
            const double Loose = RadialCm(Pad, Bar, BarAxis) - (RadiusCm + ThumbPadHalfThicknessCm + ThumbHugCm);
            if (Loose > 0.0)
            {
                Cost += 4.0 * Loose * Loose;
            }
            Cost += 0.5 * FMath::Square(FVector::DotProduct(Pad - Bar, BarAxis) - AxialGoal);
            const FVector Samples[] = {P.P2, (P.P2 + P.P3) * 0.5, P.P3, P.PTip, (T1 + P.P2) * 0.5, Pad};
            for (int32 SampleIndex = 0; SampleIndex < UE_ARRAY_COUNT(Samples); ++SampleIndex)
            {
                const double Inside = RadialCm(Samples[SampleIndex], Bar, BarAxis) - (RadiusCm + 0.75);
                if (Inside < 0.0)
                {
                    Cost += 60.0 * Inside * Inside;
                }
                if (SampleIndex == UE_ARRAY_COUNT(Samples) - 1)
                {
                    continue; // The pad may ride on the fingertips.
                }
                for (const FVector& Finger : FingerPoints)
                {
                    const double Gap = FVector::Distance(Samples[SampleIndex], Finger) - 1.1;
                    if (Gap < 0.0)
                    {
                        Cost += 15.0 * Gap * Gap;
                    }
                }
            }
            // The end of the thumb curls round the bar, not along it.
            Cost += 2.0 * FMath::Square(FVector::DotProduct((P.PTip - P.P3).GetSafeNormal(), BarAxis));
            Cost += 0.0001 * (Round * Round + Over_ * Over_ + Roll * Roll);
            return Cost;
        };
        constexpr float MaxMcp = 70.0f, MaxIp = 80.0f;
        float Best[5] = {0.0f, 0.0f, 0.0f, 0.0f, 0.0f};
        double BestCost = TNumericLimits<double>::Max();
        for (float Round = -90.0f; Round <= 90.0f; Round += 15.0f)
            for (float Over_ = -60.0f; Over_ <= 60.0f; Over_ += 15.0f)
                for (float Roll = -45.0f; Roll <= 45.0f; Roll += 15.0f)
                    for (float Mcp = 0.0f; Mcp <= MaxMcp; Mcp += 14.0f)
                        for (float Ip = 0.0f; Ip <= MaxIp; Ip += 20.0f)
                        {
                            const double Cost = ThumbCost(Round, Over_, Roll, Mcp, Ip);
                            if (Cost < BestCost)
                            {
                                BestCost = Cost;
                                Best[0] = Round; Best[1] = Over_; Best[2] = Roll; Best[3] = Mcp; Best[4] = Ip;
                            }
                        }
        for (const float Step : {5.0f, 2.0f})
        {
            const float Start[5] = {Best[0], Best[1], Best[2], Best[3], Best[4]};
            for (int32 Code = 0; Code < 243; ++Code)
            {
                float Trial[5];
                for (int32 Param = 0, Rest = Code; Param < 5; ++Param, Rest /= 3)
                {
                    Trial[Param] = Start[Param] + Step * static_cast<float>(Rest % 3 - 1);
                }
                // The thumb's joints bend one way only.
                Trial[3] = FMath::Clamp(Trial[3], 0.0f, MaxMcp);
                Trial[4] = FMath::Clamp(Trial[4], 0.0f, MaxIp);
                const double Cost = ThumbCost(Trial[0], Trial[1], Trial[2], Trial[3], Trial[4]);
                if (Cost < BestCost)
                {
                    BestCost = Cost;
                    FMemory::Memcpy(Best, Trial, sizeof(Best));
                }
            }
        }
        const FThumbPose P = PoseThumb(Best[0], Best[1], Best[2], Best[3], Best[4]);
        AddBone(ThumbBones[0], P.Swing, T1);
        AddBone(ThumbBones[1], FQuat(P.Axis, FMath::DegreesToRadians(Best[3])) * P.Swing, P.P2);
        AddBone(ThumbBones[2], FQuat(P.Axis, FMath::DegreesToRadians(Best[3] + Best[4])) * P.Swing, P.P3);
        Shape.ThumbPadErrorCm = ThumbWrapShortfallCm((P.P3 + P.PTip) * 0.5, Bar, BarAxis, -Palm, IndexPip, RadiusCm);
    }
    UE_LOG(LogTemp, Verbose, TEXT("RaftSim CC0 grip shape %s hand radius=%.2fcm oblique=%.0fdeg palm_surface=%.2fcm pad_error=%.2fcm thumb_error=%.2fcm"),
        bLeft ? TEXT("left") : TEXT("right"), RadiusCm, ObliqueDegrees, MeasurePalmSurfaceOffsetCm(bLeft), Shape.MaximumPadErrorCm, Shape.ThumbPadErrorCm);
    return Shape;
}

void ARaftSimCC0CrewVisualActor::ApplyHandGripShape(bool bLeft, const FRaftSimCC0GripBar& Bar)
{
    if (!Body)
    {
        return;
    }
    const FRaftSimCC0HandGripShape& Shape = ResolveHandGripShape(bLeft, Bar.RadiusCm, Bar.ObliqueDegrees);
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
        Delta.RotateVector(ResolveGripPointInReferenceHandCm(bLeft, Bar.RadiusCm, Bar.ObliqueDegrees) - RefHand->GetLocation() * BodyScale);
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
            // The pad as the solve places it: halfway along the end segment,
            // carried by the posed end bone, its own bend included. Run on
            // along the middle segment, the end joint's bend was left out and
            // the middle and ring fingers read up to half a centimetre off
            // the bar they touch.
            const FName MiddleBone = DigitBone(GripFingers[FingerIndex], 2, bLeft);
            const FName EndBone = DigitBone(GripFingers[FingerIndex], 3, bLeft);
            const FTransform* RefMiddle = ReferenceComponentTransforms.Find(MiddleBone);
            const FTransform* RefEnd = ReferenceComponentTransforms.Find(EndBone);
            if (!RefMiddle || !RefEnd)
            {
                return TNumericLimits<float>::Max();
            }
            const FVector RefPad = RefEnd->GetLocation() + (RefEnd->GetLocation() - RefMiddle->GetLocation()) * 0.425;
            const FVector Pad = Body->GetBoneTransformByName(EndBone, EBoneSpaces::ComponentSpace)
                .TransformPosition(RefEnd->InverseTransformPosition(RefPad)) * BodyScale;
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
        // The thumb closes round the bar the other way from the fingers.
        const FVector IndexPip = Body->GetBoneTransformByName(DigitBone(TEXT("index"), 2, bLeft), EBoneSpaces::ComponentSpace)
            .GetLocation() * BodyScale;
        // The pad as the solve places it: halfway along the end segment,
        // carried by the posed end bone (its own bend included).
        const FTransform* RefT2 = ReferenceComponentTransforms.Find(DigitBone(TEXT("thumb"), 2, bLeft));
        const FTransform* RefT3 = ReferenceComponentTransforms.Find(DigitBone(TEXT("thumb"), 3, bLeft));
        if (!RefT2 || !RefT3)
        {
            return TNumericLimits<float>::Max();
        }
        const FVector RefPad = RefT3->GetLocation() + (RefT3->GetLocation() - RefT2->GetLocation()) * 0.425;
        const FVector Pad = Body->GetBoneTransformByName(DigitBone(TEXT("thumb"), 3, bLeft), EBoneSpaces::ComponentSpace)
            .TransformPosition(RefT3->InverseTransformPosition(RefPad)) * BodyScale;
        Maximum = FMath::Max(Maximum, ThumbWrapShortfallCm(Pad, Bar.CenterCm, Bar.ThumbAxis, -Bar.PalmFacing, IndexPip, Bar.RadiusCm));
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
            (ResolveGripPointInReferenceHandCm(bLeft, Bar.RadiusCm, Bar.ObliqueDegrees) - Palm * Bar.RadiusCm) - Wrist);
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
