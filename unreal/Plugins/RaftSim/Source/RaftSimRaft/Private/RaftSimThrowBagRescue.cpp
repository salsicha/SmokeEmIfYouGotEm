#include "RaftSimRaftActor.h"
#include "RaftSimCrewAvatarActor.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInterface.h"
#include "ProceduralMeshComponent.h"

// Throw-bag rescue as river guides teach it (NRS "Throw Bag Basics", Paddling
// Magazine and Boreal River rescue notes): hold the free end, call "ROPE!",
// toss underhand PAST the swimmer so the line lands across them; the swimmer
// takes the rope (not the bag) over the shoulder, on their back with feet
// downstream, and is hauled hand over hand; at the boat the guide grabs the
// PFD shoulder straps, dunks them and falls back to pull them over the tube.

namespace
{
constexpr double kCm = 100.0;
constexpr float kWindUpSeconds = .32f;
constexpr float kReleaseSeconds = .16f;
constexpr float kHaulCycleSeconds = 1.0f;
constexpr float kRopeRecoverSeconds = 1.4f;
constexpr double kGuideArmReachCm = 58.0;

float Smooth(float A)
{
    A = FMath::Clamp(A, 0.f, 1.f);
    return A * A * (3.f - 2.f * A);
}

bool IsFinitePoint(const FVector& V)
{
    return FMath::IsFinite(V.X) && FMath::IsFinite(V.Y) && FMath::IsFinite(V.Z);
}

FVector& Hand(FRaftSimCrewAvatarPose& Pose, float Side)
{
    return Side < 0.f ? Pose.LeftHandCm : Pose.RightHandCm;
}

// Torso landmarks pivoting about the waist exactly as the pose library does.
void SetUpperBody(FRaftSimCrewAvatarPose& Pose, const FVector& TorsoCm, const FRotator& Lean)
{
    Pose.TorsoCenterCm = TorsoCm;
    Pose.TorsoRotation = Lean;
    const FQuat Rotation = Lean.Quaternion();
    Pose.HeadCenterCm = TorsoCm + Rotation.RotateVector(FVector(4.f, 0.f, 37.f));
    Pose.LeftShoulderCm = TorsoCm + Rotation.RotateVector(FVector(2.f, -17.f, 12.f));
    Pose.RightShoulderCm = TorsoCm + Rotation.RotateVector(FVector(2.f, 17.f, 12.f));
}

// Keep a hand target within the arm's reach of its shoulder.
FVector Reach(const FVector& Shoulder, const FVector& Target)
{
    const FVector Delta = Target - Shoulder;
    return Delta.Size() <= kGuideArmReachCm ? Target : Shoulder + Delta.GetSafeNormal() * kGuideArmReachCm;
}

FRaftSimCrewAvatarPose Blend(const FRaftSimCrewAvatarPose& A, const FRaftSimCrewAvatarPose& B, float Alpha)
{
    static FVector FRaftSimCrewAvatarPose::* const Points[] = {
        &FRaftSimCrewAvatarPose::TorsoCenterCm, &FRaftSimCrewAvatarPose::HeadCenterCm,
        &FRaftSimCrewAvatarPose::LeftShoulderCm, &FRaftSimCrewAvatarPose::RightShoulderCm,
        &FRaftSimCrewAvatarPose::LeftHandCm, &FRaftSimCrewAvatarPose::RightHandCm,
        &FRaftSimCrewAvatarPose::LeftHipCm, &FRaftSimCrewAvatarPose::RightHipCm,
        &FRaftSimCrewAvatarPose::LeftKneeCm, &FRaftSimCrewAvatarPose::RightKneeCm,
        &FRaftSimCrewAvatarPose::LeftFootCm, &FRaftSimCrewAvatarPose::RightFootCm,
        &FRaftSimCrewAvatarPose::PaddleTopCm, &FRaftSimCrewAvatarPose::PaddleBottomCm};
    const float S = Smooth(Alpha);
    FRaftSimCrewAvatarPose Out = S < .5f ? A : B;
    for (auto Point : Points) Out.*Point = FMath::Lerp(A.*Point, B.*Point, S);
    Out.TorsoRotation = FQuat::Slerp(A.TorsoRotation.Quaternion(), B.TorsoRotation.Quaternion(), S).Rotator();
    Out.FistGripBlend = FMath::Lerp(A.FistGripBlend, B.FistGripBlend, S);
    Out.bFeetPlanted = false;
    return Out;
}

// One hand of a hand-over-hand haul in a frame whose +X runs out along the
// rope. Returns how hard this hand is drawing the line (0 while reaching).
float HaulHand(float Phase, const FVector& Near, const FVector& Far, FVector& Out)
{
    const float P = FMath::Frac(Phase);
    if (P < .5f)
    {
        // Reach out over the rope for a fresh grip.
        Out = FMath::Lerp(Near, Far, Smooth(P / .5f)) + FVector(0.f, 0.f, 7.f * FMath::Sin(PI * P / .5f));
        return 0.f;
    }
    const float X = (P - .5f) / .5f;
    Out = FMath::Lerp(Far, Near, Smooth(X));
    // Smoothstep speed 6x(1-x), normalised to its 1.5 peak.
    return 4.f * X * (1.f - X);
}

FVector FrameToGuide(float AzimuthDeg, const FVector& P)
{
    return FRotator(0.f, AzimuthDeg, 0.f).RotateVector(P);
}
}

bool ARaftSimRaftActor::GetTubeOutlineLocalCm(FBox& OutBounds) const
{
    const FProcMeshSection* Tube = RaftVisual ? RaftVisual->GetProcMeshSection(0) : nullptr;
    if (!Tube || !Tube->SectionLocalBox.IsValid) return false;
    const FTransform ToRaft = RaftVisual->GetRelativeTransform();
    OutBounds = Tube->SectionLocalBox.TransformBy(ToRaft);
    return OutBounds.IsValid != 0;
}

bool ARaftSimRaftActor::GetGuideHaulStation(FName PassengerId, const FVector& SwimmerM, FVector& TargetM) const
{
    // The guide hauls the swimmer to their own tube, just forward of the
    // stern seat where they can reach the shoulder straps. A swimmer on the
    // far side is drawn round behind the stern, never through the boat.
    const auto* Avatar = FindAvatar(PassengerId);
    const auto* Guide = FindAvatar(TEXT("guide"));
    FBox Tube;
    if (!Avatar || !Guide || !IsFinitePoint(SwimmerM) || !GetTubeOutlineLocalCm(Tube)) return false;
    const FTransform& Raft = GetActorTransform();
    const FVector GuideLocal = Raft.InverseTransformPosition(Guide->GetActorLocation());
    const double G = GuideLocal.Y >= 0. ? 1. : -1.;
    const double HalfWidth = FMath::Max(FMath::Abs(Tube.Max.Y), FMath::Abs(Tube.Min.Y));
    const FVector Swimmer = Raft.InverseTransformPosition(SwimmerM * kCm);
    // Posed-body clearance toward the tube, as GetSwimmerTubeTarget measures it.
    FBox Body(ForceInit);
    TInlineComponentArray<UPrimitiveComponent*> Parts(Avatar);
    for (const UPrimitiveComponent* Part : Parts)
        if (Part && Part->IsRegistered() && Part->IsVisible())
            Body += Part->CalcBounds(Part->GetComponentTransform()).GetBox();
    const FVector Inward = Raft.TransformVectorNoScale(FVector(0., -G, 0.)).GetSafeNormal2D();
    const double Clearance = Body.IsValid
        ? FVector::DotProduct(Body.GetCenter() - Avatar->GetActorLocation(), Inward) +
            FVector::DotProduct(Body.GetExtent(), Inward.GetAbs())
        : 35.;
    FVector Local;
    if (Swimmer.Y * G > .5 * HalfWidth)
        Local = FVector(GuideLocal.X + 25., G * (HalfWidth + FMath::Clamp(Clearance, 20., 120.) + 6.), Swimmer.Z);
    // Round the stern a body length clear of it: the towed swimmer's head
    // leads toward the rope by ~30 cm.
    else if (Swimmer.X > Tube.Min.X - 50.)
        Local = FVector(Tube.Min.X - 95., (Swimmer.Y >= 0. ? 1. : -1.) * (HalfWidth + 45.), Swimmer.Z);
    else
        Local = FVector(Tube.Min.X - 95., G * (HalfWidth + 45.), Swimmer.Z);
    TargetM = Raft.TransformPosition(Local) / kCm;
    TargetM.Z = SwimmerM.Z;
    return IsFinitePoint(TargetM);
}

void ARaftSimRaftActor::PoseGuideForRescue(float DeltaSeconds)
{
    auto* Guide = FindAvatar(TEXT("guide"));
    const ERaftSimRescueInteractionPhase Phase = RescueInteraction.Phase;
    if (Phase != LastChoreographyPhase)
    {
        LastChoreographyPhase = Phase;
        RescueChoreographySeconds = 0.f;
    }
    RescueChoreographySeconds += FMath::Max(0.f, DeltaSeconds);
    const bool bAboard = Guide && Guide->GetAttachParentActor() == this && !IsPassengerSwimming(TEXT("guide")) &&
        !Guide->HasHighSideTransfer() && !IsFlipLineActive() && BoardingPassenger.IsNone();
    const bool bRope = RescueInteraction.Method == ERaftSimRescueMethod::ThrowLine;
    const bool bBoardingHelp = IsGuideBusyWithBoarding();
    const bool bActive = bAboard && !bBoardingHelp && (RopeRecoverRemaining > 0.f || (bRope &&
        (Phase == ERaftSimRescueInteractionPhase::LineInFlight || Phase == ERaftSimRescueInteractionPhase::Pulling ||
         Phase == ERaftSimRescueInteractionPhase::ReadyForReentry)));
    if (!bActive)
    {
        // Settle back square on the seat once the rope is put away.
        if (Guide && bAboard && !bBoardingHelp && !FMath::IsNearlyZero(GuideRescueYawDeg))
        {
            GuideRescueYawDeg = FMath::FInterpConstantTo(GuideRescueYawDeg, 0.f, DeltaSeconds, 120.f);
            Guide->SetActorRelativeRotation(FRotator(0.f, GuideRescueYawDeg, 0.f));
        }
        if (Guide && bGuideRescuePoseActive && !bBoardingHelp)
        {
            Guide->ClearExternalPose();
            bGuideRescuePoseActive = false;
        }
        if (!bActive && !bBoardingHelp && RopeRecoverRemaining <= 0.f && !IsGuideRescuing() &&
            Phase != ERaftSimRescueInteractionPhase::Completed) bThrowBagDeployed = false;
        return;
    }
    // Turn on the tube toward the swimmer (hips a little, the chest more),
    // keeping the legs inside the boat.
    FVector TargetWorld = ThrowBagWorldCm;
    const int32 TargetIndex = FindSwimmerIndex(RescueInteraction.TargetPassengerId);
    if (Swimmers.IsValidIndex(TargetIndex)) TargetWorld = Swimmers[TargetIndex].SwimmerWorldPositionMeters * kCm;
    const FVector Seat = Guide->GetRootComponent()->GetRelativeLocation();
    const FVector ToTarget = GetActorTransform().InverseTransformPosition(TargetWorld) - Seat;
    const float SeatAzimuth = FMath::RadiansToDegrees(FMath::Atan2(ToTarget.Y, ToTarget.X));
    GuideRescueYawDeg = FMath::FInterpConstantTo(GuideRescueYawDeg, FMath::Clamp(SeatAzimuth, -35.f, 35.f),
        DeltaSeconds, 160.f);
    Guide->SetActorRelativeRotation(FRotator(0.f, GuideRescueYawDeg, 0.f));
    const float Az = FMath::Clamp(FMath::FindDeltaAngleDegrees(GuideRescueYawDeg, SeatAzimuth), -110.f, 110.f);
    const float Twist = FMath::Clamp(Az, -70.f, 70.f);

    // Seated base with the legs the guide actually planted; the paddle is
    // stowed under a thigh while both hands work the rope.
    FRaftSimCrewAvatarPose Pose = URaftSimCrewAvatarPoseLibrary::EvaluatePose(
        ERaftSimCrewAvatarAction::SeatedIdle, 0.f, Seat.Y < 0. ? -1 : 1);
    if (!bGuideRescuePoseActive)
    {
        // Snapshot once: the published pose already carries fitted feet.
        const auto& Published = Guide->GetPublishedCrewPose();
        GuideRescueLegs = Published;
    }
    Pose.LeftHipCm = GuideRescueLegs.LeftHipCm; Pose.RightHipCm = GuideRescueLegs.RightHipCm;
    Pose.LeftKneeCm = GuideRescueLegs.LeftKneeCm; Pose.RightKneeCm = GuideRescueLegs.RightKneeCm;
    Pose.LeftFootCm = GuideRescueLegs.LeftFootCm; Pose.RightFootCm = GuideRescueLegs.RightFootCm;
    Pose.bShowPaddle = false;
    Pose.FistGripBlend = 1.f;
    const FVector Torso(2.f, 0.f, 59.f);
    const auto At = [Az](const FVector& P) { return FrameToGuide(Az, P); };
    if (RopeRecoverRemaining > 0.f && Phase != ERaftSimRescueInteractionPhase::LineInFlight)
    {
        // Missed: strip the rope back in fast, hand over hand, to re-throw.
        const float Clock = RescueChoreographySeconds / .6f;
        HaulHand(Clock, At(FVector(2.f, -16.f, 46.f)), At(FVector(50.f, -5.f, 60.f)), Pose.LeftHandCm);
        HaulHand(Clock + .5f, At(FVector(2.f, 16.f, 46.f)), At(FVector(50.f, 5.f, 60.f)), Pose.RightHandCm);
        SetUpperBody(Pose, Torso + At(FVector(2.f, 0.f, -3.f)), FRotator(-14.f, Twist, 0.f));
    }
    else if (Phase == ERaftSimRescueInteractionPhase::LineInFlight)
    {
        // Free end in the left fist; the bag swings back low on the right,
        // comes through underhand past the knee and follows through high.
        const float Elapsed = kWindUpSeconds + kReleaseSeconds - ThrowWindUpRemaining + ThrowFlightElapsed;
        const FVector RopeHand = At(FVector(28.f, -14.f, 54.f));
        const FVector Back = At(FVector(-24.f, 26.f, 36.f));
        const FVector Low = At(FVector(20.f, 20.f, 30.f));
        const FVector High = At(FVector(60.f, 12.f, 90.f));
        const FVector Rest = At(FVector(32.f, -2.f, 56.f));
        FVector Right;
        float Pitch, Yaw;
        if (Elapsed < kWindUpSeconds)
        {
            const float W = Smooth(Elapsed / kWindUpSeconds);
            Right = FMath::Lerp(FMath::Lerp(Pose.RightHandCm, Low, .5f), Back, W);
            Pitch = 8.f * W; Yaw = Twist + 28.f * W;
        }
        else if (Elapsed < kWindUpSeconds + kReleaseSeconds)
        {
            const float R = (Elapsed - kWindUpSeconds) / kReleaseSeconds;
            Right = R < .5f ? FMath::Lerp(Back, Low, Smooth(R / .5f)) : FMath::Lerp(Low, High, Smooth((R - .5f) / .5f));
            Pitch = FMath::Lerp(8.f, -16.f, Smooth(R)); Yaw = Twist + FMath::Lerp(28.f, -14.f, Smooth(R));
        }
        else
        {
            // Watch the bag land, then bring the throwing hand to the rope.
            const float F = Smooth((Elapsed - kWindUpSeconds - kReleaseSeconds - .25f) / .35f);
            Right = FMath::Lerp(High, Rest, F);
            Pitch = FMath::Lerp(-16.f, -10.f, F); Yaw = Twist + FMath::Lerp(-14.f, 0.f, F);
        }
        SetUpperBody(Pose, Torso + At(FVector(2.f * FMath::Abs(Pitch) / 16.f, 0.f, -2.f)), FRotator(Pitch, Yaw, 0.f));
        Pose.LeftHandCm = RopeHand;
        Pose.RightHandCm = Right;
    }
    else if (Phase == ERaftSimRescueInteractionPhase::Pulling)
    {
        const float Clock = RescueChoreographySeconds / kHaulCycleSeconds;
        HaulHand(Clock, At(FVector(4.f, -16.f, 46.f)), At(FVector(58.f, -5.f, 63.f)), Pose.LeftHandCm);
        HaulHand(Clock + .5f, At(FVector(4.f, 16.f, 46.f)), At(FVector(58.f, 5.f, 63.f)), Pose.RightHandCm);
        // Each draw rocks the chest back; each reach leans it out.
        const float Rock = FMath::Sin(4.f * PI * Clock);
        SetUpperBody(Pose, Torso + At(FVector(2.f * Rock, 0.f, -2.f)), FRotator(-11.f + 8.f * Rock, Twist, 0.f));
    }
    else
    {
        // Swimmer at the tube: lean out, rope pinned in the left fist, the
        // right hand down at the tube ready for the shoulder strap.
        SetUpperBody(Pose, Torso + At(FVector(8.f, 0.f, -6.f)), FRotator(-30.f, Twist, 0.f));
        Pose.LeftHandCm = At(FVector(10.f, -15.f, 46.f));
        Pose.RightHandCm = At(FVector(50.f, 8.f, 30.f));
    }
    Pose.LeftHandCm = Reach(Pose.LeftShoulderCm, Pose.LeftHandCm);
    Pose.RightHandCm = Reach(Pose.RightShoulderCm, Pose.RightHandCm);
    Guide->SetAvatarAction(Phase == ERaftSimRescueInteractionPhase::LineInFlight
        ? ERaftSimCrewAvatarAction::ThrowLine : ERaftSimCrewAvatarAction::HaulLine);
    Guide->SetExternalPose(Pose, true);
    bGuideRescuePoseActive = true;
}

float ARaftSimRaftActor::GetHaulPullFraction() const
{
    // The swimmer comes in on the guide's draws: one hand always pulling,
    // fastest mid-draw, slowest as the hands change over.
    const float Clock = RescueChoreographySeconds / kHaulCycleSeconds;
    FVector Unused;
    const float Pull = FMath::Max(HaulHand(Clock, FVector::ZeroVector, FVector::OneVector, Unused),
        HaulHand(Clock + .5f, FVector::ZeroVector, FVector::OneVector, Unused));
    return .35f + .65f * FMath::Clamp(Pull, 0.f, 1.f);
}

void ARaftSimRaftActor::StartThrowChoreography()
{
    // Called with the library already in LineInFlight from the left hand.
    ThrowWindUpRemaining = kWindUpSeconds + kReleaseSeconds;
    ThrowFlightElapsed = 0.f;
    const double Distance = FVector::Dist2D(RescueInteraction.ThrowOriginMeters, RescueInteraction.ThrowLandingMeters);
    // An underhand toss carries ~9-12 m/s: about 0.7 s to 5 m, 1 s to 8 m.
    ThrowFlightSeconds = FMath::Clamp(.28f + .085f * float(Distance), .45f, 1.05f);
    RescueChoreographySeconds = 0.f;
    RopeRecoverRemaining = 0.f;
    bThrowBagDeployed = true;
    bRopeSwimmerAtStation = false;
    if (const auto* Guide = FindAvatar(TEXT("guide")))
        ThrowBagWorldCm = Guide->GetActorTransform().TransformPosition(Guide->GetPublishedCrewPose().RightHandCm);
    ThrowReleaseWorldCm = ThrowBagWorldCm;
}

void ARaftSimRaftActor::AdvanceThrowBag(float DeltaSeconds)
{
    if (!bThrowBagDeployed) return;
    const float Dt = FMath::Clamp(DeltaSeconds, 0.f, .25f);
    const FVector HandCm = GetRescueHandWorldM() * kCm;
    const ERaftSimRescueInteractionPhase Phase = RescueInteraction.Phase;
    const int32 Index = FindSwimmerIndex(RescueInteraction.TargetPassengerId);
    if ((Phase == ERaftSimRescueInteractionPhase::Pulling || Phase == ERaftSimRescueInteractionPhase::ReadyForReentry) &&
        Swimmers.IsValidIndex(Index))
    {
        // Rope in both fists at the swimmer's chest; the bag and the rest of
        // the line float on beyond them where the throw carried it.
        if (const auto* Swimmer = FindAvatar(RescueInteraction.TargetPassengerId))
        {
            const auto& Pose = Swimmer->GetPublishedCrewPose();
            RopeSwimmerGripWorldCm = Swimmer->GetActorTransform().TransformPosition((Pose.LeftHandCm + Pose.RightHandCm) * .5);
        }
        FVector Float = RopeSwimmerGripWorldCm + (RopeSwimmerGripWorldCm - HandCm).GetSafeNormal2D() * 90.;
        Float.Z = Swimmers[Index].SwimmerWorldPositionMeters.Z * kCm + 4.;
        ThrowBagWorldCm = FMath::VInterpTo(ThrowBagWorldCm, Float, Dt, 3.f);
    }
    else if (RopeRecoverRemaining > 0.f)
    {
        // Stripped in across the water, then lifted aboard over the tube.
        const FVector Water(ThrowBagWorldCm.X, ThrowBagWorldCm.Y, RescueInteraction.ThrowLandingMeters.Z * kCm + 4.);
        const FVector ToHand = HandCm - Water;
        const double Step = ToHand.Size2D() / FMath::Max(RopeRecoverRemaining, Dt) * Dt;
        ThrowBagWorldCm = ToHand.Size2D() > 70. ? Water + ToHand.GetSafeNormal2D() * Step
            : FMath::VInterpTo(ThrowBagWorldCm, HandCm - FVector(0, 0, 15), Dt, 6.f);
    }
}

void ARaftSimRaftActor::BuildRopeMesh(const TArray<FVector>& WorldPointsCm, const TArray<float>& SegmentSagCm)
{
    if (!RescueLineVisual) return;
    if (WorldPointsCm.Num() < 2)
    {
        RescueLineVisual->SetVisibility(false);
        return;
    }
    // Sample a rope through the points; each span hangs under gravity in
    // WORLD down, so a line off an overturned hull still droops to the water.
    TArray<FVector> Centers;
    for (int32 Span = 0; Span + 1 < WorldPointsCm.Num(); ++Span)
    {
        const FVector A = WorldPointsCm[Span], B = WorldPointsCm[Span + 1];
        const float Sag = SegmentSagCm.IsValidIndex(Span) ? SegmentSagCm[Span] : 0.f;
        const int32 Steps = FMath::Clamp(int32(FVector::Distance(A, B) / 30.0), 2, 18);
        for (int32 Step = Span == 0 ? 0 : 1; Step <= Steps; ++Step)
        {
            const float T = float(Step) / Steps;
            Centers.Add(FMath::Lerp(A, B, double(T)) - FVector(0, 0, 4.f * Sag * T * (1.f - T)));
        }
    }
    constexpr int32 Sides = 6;
    // A little over a real 3/8" line so it reads at gameplay distance.
    constexpr float RadiusCm = 1.1f;
    const FTransform& Raft = GetActorTransform();
    TArray<FVector> Vertices, Normals;
    TArray<int32> Triangles;
    TArray<FVector2D> UVs;
    TArray<FProcMeshTangent> Tangents;
    float Along = 0.f;
    for (int32 Ring = 0; Ring < Centers.Num(); ++Ring)
    {
        const FVector Prev = Centers[FMath::Max(Ring - 1, 0)], Next = Centers[FMath::Min(Ring + 1, Centers.Num() - 1)];
        const FVector Tangent = (Next - Prev).GetSafeNormal();
        FVector Side = FVector::CrossProduct(Tangent, FVector::UpVector).GetSafeNormal();
        if (Side.IsNearlyZero()) Side = FVector::RightVector;
        const FVector Up = FVector::CrossProduct(Side, Tangent).GetSafeNormal();
        if (Ring > 0) Along += float(FVector::Distance(Centers[Ring], Centers[Ring - 1]));
        for (int32 S = 0; S < Sides; ++S)
        {
            const float Angle = 2.f * PI * S / Sides;
            const FVector Normal = FMath::Cos(Angle) * Side + FMath::Sin(Angle) * Up;
            Vertices.Add(Raft.InverseTransformPosition(Centers[Ring] + Normal * RadiusCm));
            Normals.Add(Raft.InverseTransformVectorNoScale(Normal));
            UVs.Add(FVector2D(Along / 12.f, float(S) / Sides));
            Tangents.Add(FProcMeshTangent(Raft.InverseTransformVectorNoScale(Tangent), false));
        }
    }
    for (int32 Ring = 0; Ring + 1 < Centers.Num(); ++Ring)
        for (int32 S = 0; S < Sides; ++S)
        {
            const int32 N = (S + 1) % Sides;
            const int32 A = Ring * Sides + S, B = (Ring + 1) * Sides + S, C = Ring * Sides + N, D = (Ring + 1) * Sides + N;
            Triangles.Append({A, B, C, C, B, D});
        }
    const TArray<FLinearColor> Colors;
    RescueLineVisual->CreateMeshSection_LinearColor(0, Vertices, Triangles, Normals, UVs, Colors, Tangents, false);
    if (!RopeMaterial)
        RopeMaterial = LoadObject<UMaterialInterface>(nullptr,
            TEXT("/Game/RaftSim/Materials/M_RaftSim_PFD_Yellow.M_RaftSim_PFD_Yellow"));
    if (RopeMaterial && RescueLineVisual->GetMaterial(0) != RopeMaterial) RescueLineVisual->SetMaterial(0, RopeMaterial);
    RescueLineVisual->SetVisibility(true);
}

void ARaftSimRaftActor::UpdateRescueLineVisual()
{
    UpdateGuideWaistLine();
    // The stowed bag leaves the floor while it is out on the water.
    for (int32 Section = 0; RaftGear && Section < FMath::Min(RaftGearThrowBagSectionCount, RaftGear->GetNumSections()); ++Section)
        RaftGear->SetMeshSectionVisible(Section, !bThrowBagDeployed);
    if (ThrowBagVisual && RaftGear && RaftGear->GetMaterial(0) && ThrowBagVisual->GetMaterial(0) != RaftGear->GetMaterial(0))
        ThrowBagVisual->SetMaterial(0, RaftGear->GetMaterial(0));
    TArray<FVector> Points;
    TArray<float> Sag;
    bool bShowBag = false;
    FVector BagAxis = FVector::UpVector;
    const auto* Guide = FindAvatar(TEXT("guide"));
    const auto HandWorld = [Guide](bool bLeft)
    {
        const auto& Pose = Guide->GetPublishedCrewPose();
        return Guide->GetActorTransform().TransformPosition(bLeft ? Pose.LeftHandCm : Pose.RightHandCm);
    };
    const ERaftSimRescueInteractionPhase Phase = RescueInteraction.Phase;
    if (IsFlipLineActive() || FlipLineRopeVisible())
    {
        BuildFlipLineRope(Points, Sag);
    }
    else if (Guide && bThrowBagDeployed && Phase == ERaftSimRescueInteractionPhase::LineInFlight)
    {
        const FVector Rope = HandWorld(true);
        if (ThrowWindUpRemaining > 0.f)
        {
            // Bag swinging in the throwing fist, a loop of line to the free end.
            ThrowBagWorldCm = HandWorld(false) - FVector(0, 0, 12);
            Points = {Rope, ThrowBagWorldCm};
            Sag = {14.f};
        }
        else
        {
            const float T = FMath::Clamp(ThrowFlightElapsed / FMath::Max(ThrowFlightSeconds, .01f), 0.f, 1.f);
            const FVector Landing = RescueInteraction.ThrowLandingMeters * kCm;
            const double Span = FVector::Dist2D(ThrowReleaseWorldCm, Landing);
            const FVector Previous = ThrowBagWorldCm;
            ThrowBagWorldCm = FMath::Lerp(ThrowReleaseWorldCm, Landing, double(T)) +
                FVector(0, 0, (90. + 12. * Span / kCm) * 4. * T * (1. - T));
            if (!(ThrowBagWorldCm - Previous).IsNearlyZero()) BagAxis = (ThrowBagWorldCm - Previous).GetSafeNormal();
            // The rope pays out of the bag and trails it nearly straight.
            Points = {Rope, ThrowBagWorldCm};
            Sag = {6.f + 10.f * T};
        }
        bShowBag = true;
    }
    else if (Guide && bThrowBagDeployed && (Phase == ERaftSimRescueInteractionPhase::Pulling ||
        Phase == ERaftSimRescueInteractionPhase::ReadyForReentry))
    {
        const FVector Left = HandWorld(true), Right = HandWorld(false);
        const FVector Grip = RopeSwimmerGripWorldCm;
        const FVector Out = (Grip - (Left + Right) * .5).GetSafeNormal2D();
        const bool bLeftFore = FVector::DotProduct(Left - Right, Out) > 0.;
        const FVector Fore = bLeftFore ? Left : Right, Rear = bLeftFore ? Right : Left;
        // Slack behind the rear hand falls into the boat; the working line
        // is nearly taut; the bag floats on beyond the swimmer.
        const FVector Pile = Rear - Out * 25. - FVector(0, 0, 45);
        Points = {Pile, Rear, Fore, Grip, ThrowBagWorldCm};
        const float Taut = Phase == ERaftSimRescueInteractionPhase::Pulling ? .03f : .08f;
        Sag = {12.f, 2.f, float(FVector::Distance(Fore, Grip)) * Taut, 10.f};
        bShowBag = true;
    }
    else if (Guide && bThrowBagDeployed && RopeRecoverRemaining > 0.f)
    {
        // A miss: the bag skips back across the water as the rope comes in.
        const FVector Rope = HandWorld(true);
        Points = {Rope, ThrowBagWorldCm};
        Sag = {12.f};
        bShowBag = true;
    }
    if (ThrowBagVisual)
    {
        ThrowBagVisual->SetVisibility(bShowBag);
        if (bShowBag)
        {
            ThrowBagVisual->SetWorldLocation(ThrowBagWorldCm);
            ThrowBagVisual->SetWorldRotation(FRotationMatrix::MakeFromZ(BagAxis).Rotator());
        }
    }
    if (Points.Num() < 2)
    {
        if (RescueLineVisual) RescueLineVisual->SetVisibility(false);
        return;
    }
    BuildRopeMesh(Points, Sag);
}

void ARaftSimRaftActor::BeginAssistedBoarding(ARaftSimCrewAvatarActor* Avatar, FName PassengerId,
    const FTransform& StartWorld, const FRaftSimCrewAvatarPose& StartPose)
{
    FinishAssistedBoarding();
    FBox Tube;
    if (!Avatar || Avatar->GetAttachParentActor() != this || !StartWorld.IsValid() || !GetTubeOutlineLocalCm(Tube)) return;
    AssistedBoardingSeatLocal = Avatar->GetRootComponent()->GetRelativeTransform();
    AssistedBoardingSeatPose = Avatar->GetPublishedCrewPose();
    AssistedBoardingStartLocal = StartWorld.GetRelativeTransform(GetActorTransform());
    AssistedBoardingStartPose = StartPose;
    const FVector Start = AssistedBoardingStartLocal.GetLocation();
    const double Side = Start.Y >= 0. ? 1. : -1.;
    const double HalfWidth = FMath::Max(FMath::Abs(Tube.Max.Y), FMath::Abs(Tube.Min.Y));
    // Come over the side tube abeam, clear of the bow and stern kick.
    const double X = FMath::Clamp(Start.X, Tube.Min.X + 70., Tube.Max.X - 70.);
    bool bTop = false, bFloor = false;
    const float TopZ = ComputeSeatTubeTopZCm(FVector(X, Side * (HalfWidth - 28.), 0.), bTop);
    const float FloorZ = ComputeSeatTubeTopZCm(FVector(X, Side * (HalfWidth - 80.), 0.), bFloor);
    const double Top = bTop ? TopZ : Tube.Max.Z;
    AssistedBoardingTubeLocalCm = FVector(X, Side * (HalfWidth - 16.), Top - 24.);
    AssistedBoardingFloorZ = bFloor ? FloorZ : Top - 26.;
    AssistedBoardingInsideLocalCm = FVector(X, Side * (HalfWidth - 74.), AssistedBoardingFloorZ - 16.);
    // A boat that came over on top of its swimmer is climbed from beside the
    // tube, never up through the floor: swim out from under it first.
    AssistedBoardingOutsideLocalCm = FVector(X, Side * FMath::Max(FMath::Abs(Start.Y), HalfWidth + 22.), Start.Z);
    const auto* Guide = FindAvatar(TEXT("guide"));
    bAssistedBoardingByGuide = PassengerId != TEXT("guide") && Guide && Guide->GetAttachParentActor() == this &&
        !Guide->HasHighSideTransfer() && !IsPassengerSwimming(TEXT("guide")) &&
        FVector::Dist2D(Guide->GetActorLocation(), StartWorld.GetLocation()) < 190.;
    AssistedBoardingAvatar = Avatar;
    AssistedBoardingPassenger = PassengerId;
    AssistedBoardingElapsed = 0.f;
    // The rope is dropped in the boat; the guide re-stuffs the bag later.
    bThrowBagDeployed = false;
    // A practised PFD haul is a couple of seconds; climbing in alone takes
    // longer. Then a crawl across the floor to their own seat.
    AssistedBoardingHaulSeconds = bAssistedBoardingByGuide ? 2.2f : 2.9f;
    AssistedBoardingCrawlSeconds = FMath::Clamp(float(FVector::Dist2D(AssistedBoardingInsideLocalCm,
        AssistedBoardingSeatLocal.GetLocation())) / 70.f, .8f, 3.5f);
    AssistedBoardingDuration = AssistedBoardingHaulSeconds + AssistedBoardingCrawlSeconds;
    if (bAssistedBoardingByGuide) GuideRescueLegs = Guide->GetPublishedCrewPose();
    Avatar->SetActorRelativeTransform(AssistedBoardingStartLocal);
    Avatar->SetAvatarAction(ERaftSimCrewAvatarAction::Reentry);
    UpdateAssistedBoarding(0.f);
}

void ARaftSimRaftActor::UpdateAssistedBoarding(float DeltaSeconds)
{
    ARaftSimCrewAvatarActor* Avatar = AssistedBoardingAvatar.Get();
    if (!Avatar)
    {
        if (!AssistedBoardingPassenger.IsNone()) FinishAssistedBoarding();
        return;
    }
    if (Avatar->GetAttachParentActor() != this || RaftMode == ERaftSimRaftMode::Capsized ||
        IsPassengerSwimming(AssistedBoardingPassenger))
    {
        FinishAssistedBoarding();
        return;
    }
    AssistedBoardingElapsed = FMath::Min(AssistedBoardingDuration,
        AssistedBoardingElapsed + FMath::Clamp(DeltaSeconds, 0.f, .25f));
    // The haul over the tube runs on its own clock (A reaches .78 as the
    // swimmer rolls onto the floor); the crawl to the seat follows.
    const float Haul = FMath::Max(AssistedBoardingHaulSeconds, .01f);
    const float A = FMath::Min(1.f, AssistedBoardingElapsed / (Haul / .78f));
    const float CrawlA = FMath::Clamp((AssistedBoardingElapsed - Haul) / FMath::Max(AssistedBoardingCrawlSeconds, .01f), 0.f, 1.f);
    const FVector Start = AssistedBoardingStartLocal.GetLocation();
    const double Side = Start.Y >= 0. ? 1. : -1.;
    const FVector Inward(0., -Side, 0.);
    // Root: water (out from under the hull if it landed on them) -> dunk
    // (or the self-rescue sink before the kick) -> hips onto the tube crest
    // -> rolled in on the floor -> crawl -> up onto the seat.
    const FVector Dunk = AssistedBoardingOutsideLocalCm + Inward * 8. - FVector(0, 0, 22);
    const FVector Keys[] = {Start, Dunk, AssistedBoardingTubeLocalCm, AssistedBoardingInsideLocalCm};
    const float Times[] = {0.f, .22f, .55f, .78f};
    int32 Stage = 0;
    while (Stage < 2 && A > Times[Stage + 1]) ++Stage;
    const bool bCrawling = AssistedBoardingElapsed > Haul;
    if (bCrawling) Stage = 3;
    const float StageT = bCrawling ? CrawlA : FMath::Clamp((A - Times[Stage]) / (Times[Stage + 1] - Times[Stage]), 0.f, 1.f);
    const FVector Seat = AssistedBoardingSeatLocal.GetLocation();
    const FVector Crawl(Seat.X, Seat.Y, AssistedBoardingFloorZ + 2.);
    FVector Location;
    if (!bCrawling)
    {
        Location = FMath::Lerp(Keys[Stage], Keys[Stage + 1], double(Smooth(StageT)));
        // Swim out from under the hull before the dunk; heave up and over.
        if (Stage == 0) Location = FMath::Lerp(FMath::Lerp(Start, AssistedBoardingOutsideLocalCm, double(Smooth(StageT * 1.6f))),
            Dunk, double(Smooth(StageT)));
        if (Stage == 1) Location.Z += 14. * FMath::Sin(PI * StageT);
    }
    else
    {
        // Hands and knees across the floor, then up onto the seat.
        const FVector Floor(AssistedBoardingInsideLocalCm.X, AssistedBoardingInsideLocalCm.Y, AssistedBoardingFloorZ + 2.);
        Location = StageT < .7f
            ? FMath::Lerp(FMath::Lerp(AssistedBoardingInsideLocalCm, Floor, double(Smooth(StageT / .15f))), Crawl, double(Smooth(StageT / .7f)))
            : FMath::Lerp(Crawl, Seat, double(Smooth((StageT - .7f) / .3f)));
    }
    const FQuat FacingIn = FRotator(0.f, Side > 0. ? -90.f : 90.f, 0.f).Quaternion();
    const FVector Travel = Crawl - AssistedBoardingInsideLocalCm;
    const FQuat FacingTravel = Travel.Size2D() > 10. ? FRotator(0.f, Travel.Rotation().Yaw, 0.f).Quaternion() : FacingIn;
    FQuat Rotation = FacingIn;
    if (A < .15f) Rotation = FQuat::Slerp(AssistedBoardingStartLocal.GetRotation(), FacingIn, Smooth(A / .15f));
    else if (bCrawling) Rotation = StageT < .7f ? FQuat::Slerp(FacingIn, FacingTravel, Smooth(StageT / .25f))
        : FQuat::Slerp(FacingTravel, AssistedBoardingSeatLocal.GetRotation(), Smooth((StageT - .7f) / .3f));
    Avatar->SetActorRelativeTransform(FTransform(Rotation, Location, AssistedBoardingSeatLocal.GetScale3D()));

    // Swimmer keys in a frame facing the tube (+X inboard).
    const bool bHelped = bAssistedBoardingByGuide;
    FRaftSimCrewAvatarPose Grabbed = URaftSimCrewAvatarPoseLibrary::EvaluatePose(ERaftSimCrewAvatarAction::Reentry, 0.f, 1);
    SetUpperBody(Grabbed, FVector(4.f, 0.f, 46.f), FRotator(-12.f, 0.f, 0.f));
    Grabbed.LeftHandCm = bHelped ? FVector(34.f, -16.f, 70.f) : FVector(40.f, -24.f, 58.f);
    Grabbed.RightHandCm = bHelped ? FVector(34.f, 16.f, 70.f) : FVector(40.f, 24.f, 58.f);
    Grabbed.LeftHipCm = FVector(-2.f, -10.f, 24.f); Grabbed.RightHipCm = FVector(-2.f, 10.f, 24.f);
    Grabbed.LeftKneeCm = FVector(6.f, -11.f, -8.f); Grabbed.RightKneeCm = FVector(6.f, 11.f, -8.f);
    Grabbed.LeftFootCm = FVector(-6.f, -12.f, -40.f); Grabbed.RightFootCm = FVector(-6.f, 12.f, -40.f);
    Grabbed.FistGripBlend = 1.f;
    Grabbed.bShowPaddle = false;
    // Belly over the tube, hands down on the floor, legs still outside.
    FRaftSimCrewAvatarPose OverTube = Grabbed;
    SetUpperBody(OverTube, FVector(26.f, 0.f, 34.f), FRotator(-72.f, 0.f, 0.f));
    OverTube.LeftHandCm = FVector(70.f, -24.f, -8.f); OverTube.RightHandCm = FVector(70.f, 24.f, -8.f);
    OverTube.LeftHipCm = FVector(-4.f, -10.f, 26.f); OverTube.RightHipCm = FVector(-4.f, 10.f, 26.f);
    OverTube.LeftKneeCm = FVector(-18.f, -11.f, 0.f); OverTube.RightKneeCm = FVector(-18.f, 11.f, 0.f);
    OverTube.LeftFootCm = FVector(-32.f, -12.f, -30.f); OverTube.RightFootCm = FVector(-32.f, 12.f, -30.f);
    OverTube.FistGripBlend = 0.f;
    // Rolled in on the floor, legs swinging over the tube behind.
    FRaftSimCrewAvatarPose RolledIn = OverTube;
    SetUpperBody(RolledIn, FVector(20.f, 0.f, 26.f), FRotator(-60.f, 0.f, 0.f));
    RolledIn.LeftHandCm = FVector(30.f, -26.f, 6.f); RolledIn.RightHandCm = FVector(30.f, 26.f, 6.f);
    RolledIn.LeftHipCm = FVector(-6.f, -10.f, 22.f); RolledIn.RightHipCm = FVector(-6.f, 10.f, 22.f);
    RolledIn.LeftKneeCm = FVector(-30.f, -11.f, 50.f); RolledIn.RightKneeCm = FVector(-30.f, 11.f, 50.f);
    RolledIn.LeftFootCm = FVector(-52.f, -12.f, 44.f); RolledIn.RightFootCm = FVector(-52.f, 12.f, 44.f);
    // On hands and knees, alternate hand and knee reaching forward.
    FRaftSimCrewAvatarPose Crawling = RolledIn;
    {
        const float Step = FMath::Sin(2.f * PI * StageT * FMath::Max(1.f, float(Travel.Size2D()) / 30.f));
        SetUpperBody(Crawling, FVector(6.f, 0.f, 40.f), FRotator(-62.f, 0.f, 0.f));
        Crawling.LeftHipCm = FVector(-18.f, -10.f, 34.f); Crawling.RightHipCm = FVector(-18.f, 10.f, 34.f);
        Crawling.LeftKneeCm = FVector(-8.f - 6.f * Step, -11.f, 2.f + 3.f * FMath::Max(0.f, -Step));
        Crawling.RightKneeCm = FVector(-8.f + 6.f * Step, 11.f, 2.f + 3.f * FMath::Max(0.f, Step));
        Crawling.LeftFootCm = Crawling.LeftKneeCm + FVector(-34.f, -1.f, 4.f);
        Crawling.RightFootCm = Crawling.RightKneeCm + FVector(-34.f, 1.f, 4.f);
        Crawling.LeftHandCm = FVector(28.f + 6.f * Step, -16.f, 2.f + 4.f * FMath::Max(0.f, Step));
        Crawling.RightHandCm = FVector(28.f - 6.f * Step, 16.f, 2.f + 4.f * FMath::Max(0.f, -Step));
    }
    FRaftSimCrewAvatarPose Pose;
    if (!bCrawling)
    {
        const FRaftSimCrewAvatarPose* Poses[] = {&AssistedBoardingStartPose, &Grabbed, &OverTube, &RolledIn};
        Pose = Blend(*Poses[Stage], *Poses[Stage + 1], StageT);
    }
    else
        Pose = StageT < .7f ? Blend(RolledIn, Crawling, StageT / .2f)
            : Blend(Crawling, AssistedBoardingSeatPose, (StageT - .7f) / .3f);
    Pose.bShowPaddle = bCrawling && StageT > .95f && AssistedBoardingSeatPose.bShowPaddle;
    Avatar->SetExternalPose(Pose, true);

    // The guide's part ends once the swimmer is down on the floor; they are
    // free to throw again while the rescued paddler crawls to their seat.
    if (bHelped && A >= 1.f) ReleaseGuideFromBoarding();
    if (bHelped && A < 1.f)
    {
        ARaftSimCrewAvatarActor* Guide = FindAvatar(TEXT("guide"));
        if (Guide && Guide->GetAttachParentActor() == this)
        {
            // Both fists on the swimmer's PFD shoulder straps (vest-local
            // webbing at y +/-11 cm near the shoulder line), wherever the
            // straps are as the swimmer is dunked and hauled over.
            const FTransform SwimmerWorld = Avatar->GetActorTransform();
            const FQuat Vest = Pose.TorsoRotation.Quaternion();
            const FTransform GuideWorld = Guide->GetActorTransform();
            const auto Strap = [&](float Y)
            {
                return GuideWorld.InverseTransformPosition(SwimmerWorld.TransformPosition(
                    Pose.TorsoCenterCm + Vest.RotateVector(FVector(3.f, Y, 19.f))));
            };
            const FVector GuideSeat = Guide->GetRootComponent()->GetRelativeLocation();
            const FVector ToSwimmer = GetActorTransform().InverseTransformPosition(SwimmerWorld.GetLocation()) - GuideSeat;
            const float SeatAzimuth = FMath::RadiansToDegrees(FMath::Atan2(ToSwimmer.Y, ToSwimmer.X));
            GuideRescueYawDeg = FMath::FInterpConstantTo(GuideRescueYawDeg,
                A < .8f ? FMath::Clamp(SeatAzimuth, -35.f, 35.f) : 0.f, DeltaSeconds, 120.f);
            Guide->SetActorRelativeRotation(FRotator(0.f, GuideRescueYawDeg, 0.f));
            const float Az = FMath::Clamp(FMath::FindDeltaAngleDegrees(GuideRescueYawDeg, SeatAzimuth), -110.f, 110.f);
            const float Twist = FMath::Clamp(Az, -70.f, 70.f);
            const auto At = [Az](const FVector& P) { return FrameToGuide(Az, P); };
            FRaftSimCrewAvatarPose G = URaftSimCrewAvatarPoseLibrary::EvaluatePose(
                ERaftSimCrewAvatarAction::SeatedIdle, 0.f, GuideSeat.Y < 0. ? -1 : 1);
            const FRaftSimCrewAvatarPose Seated = G;
            G.LeftKneeCm = GuideRescueLegs.LeftKneeCm; G.RightKneeCm = GuideRescueLegs.RightKneeCm;
            G.LeftFootCm = GuideRescueLegs.LeftFootCm; G.RightFootCm = GuideRescueLegs.RightFootCm;
            G.bShowPaddle = false;
            // Lean out to grab, push down for the dunk, then throw the
            // weight back and fall into the boat with the swimmer.
            float Pitch, Back, Drop;
            if (A < .22f) { const float T = Smooth(A / .22f); Pitch = FMath::Lerp(-30.f, -46.f, T); Back = -14.f * T; Drop = 6.f * T; }
            else if (A < .55f) { const float T = Smooth((A - .22f) / .33f); Pitch = FMath::Lerp(-46.f, 20.f, T); Back = FMath::Lerp(-14.f, 8.f, T); Drop = FMath::Lerp(6.f, 4.f, T); }
            else { const float T = Smooth((A - .55f) / .23f); Pitch = FMath::Lerp(20.f, 32.f, T); Back = FMath::Lerp(8.f, 16.f, T); Drop = FMath::Lerp(4.f, 12.f, T); }
            const FVector HipShift = At(FVector(-Back * .6f, 0.f, -Drop));
            G.LeftHipCm = GuideRescueLegs.LeftHipCm + HipShift; G.RightHipCm = GuideRescueLegs.RightHipCm + HipShift;
            SetUpperBody(G, FVector(2.f, 0.f, 59.f - Drop) + At(FVector(-Back, 0.f, 0.f)), FRotator(Pitch, Twist, 0.f));
            const float Hold = A < .7f ? 1.f : 1.f - Smooth((A - .7f) / .08f);
            const FVector Release[] = {At(FVector(-16.f, -24.f, 30.f)), At(FVector(-16.f, 24.f, 30.f))};
            G.LeftHandCm = Reach(G.LeftShoulderCm, FMath::Lerp(Release[0], Strap(-11.f), Hold));
            G.RightHandCm = Reach(G.RightShoulderCm, FMath::Lerp(Release[1], Strap(11.f), Hold));
            G.FistGripBlend = Hold;
            // From the lean-out the haul ended in, back to the seat at the end.
            if (A < .12f) G = Blend(GuideRescueLegs, G, A / .12f);
            if (A > .82f) G = Blend(G, Seated, (A - .82f) / .18f);
            Guide->SetAvatarAction(ERaftSimCrewAvatarAction::ReachRescue);
            Guide->SetExternalPose(G, true);
            bGuideRescuePoseActive = true;
        }
    }
    if (AssistedBoardingElapsed >= AssistedBoardingDuration) FinishAssistedBoarding();
}

void ARaftSimRaftActor::ReleaseGuideFromBoarding()
{
    if (!bAssistedBoardingByGuide || bAssistedGuideReleased) return;
    bAssistedGuideReleased = true;
    if (auto* Guide = FindAvatar(TEXT("guide")); Guide && Guide->GetAttachParentActor() == this)
    {
        Guide->ClearExternalPose();
        Guide->SetAvatarAction(ERaftSimCrewAvatarAction::SeatedIdle);
        bGuideRescuePoseActive = false;
    }
}

void ARaftSimRaftActor::FinishAssistedBoarding()
{
    ReleaseGuideFromBoarding();
    ARaftSimCrewAvatarActor* Avatar = AssistedBoardingAvatar.Get();
    const FName PassengerId = AssistedBoardingPassenger;
    AssistedBoardingAvatar = nullptr;
    AssistedBoardingPassenger = NAME_None;
    bAssistedBoardingByGuide = bAssistedGuideReleased = false;
    AssistedBoardingElapsed = AssistedBoardingDuration = 0.f;
    if (Avatar)
    {
        Avatar->ClearExternalPose();
        // Seat exactly as the completed rescue already recorded it.
        if (Avatar->GetAttachParentActor() == this && !IsPassengerSwimming(PassengerId))
            AttachAvatarToSeat(Avatar, PassengerId);
    }
}

FText ARaftSimRaftActor::GetRescuePrompt() const
{
    if (IsGuideBusyWithBoarding())
        return FText::FromString(AssistedBoardingPassenger == TEXT("guide")
            ? TEXT("CLIMBING IN - kick, pull on the perimeter line, roll over the tube")
            : (bAssistedBoardingByGuide ? TEXT("PFD HAUL - grab the shoulder straps, dunk, lean back and fall in")
                : TEXT("CLIMBING IN - swimmer pulls over the tube")));
    switch (RescueInteraction.Phase)
    {
    case ERaftSimRescueInteractionPhase::LineInFlight:
        if (RescueInteraction.Method == ERaftSimRescueMethod::ThrowLine)
            return FText::FromString(ThrowWindUpRemaining > 0.f ? TEXT("ROPE! - holding the free end, underhand toss past the swimmer")
                : TEXT("ROPE! - bag in the air; the line lands across the swimmer"));
        break;
    case ERaftSimRescueInteractionPhase::Pulling:
        if (RescueInteraction.Method == ERaftSimRescueMethod::ThrowLine)
            return FText::FromString(TEXT("HAULING - hand over hand; swimmer on their back, rope over the shoulder"));
        break;
    case ERaftSimRescueInteractionPhase::ReadyForReentry:
        return FText::FromString(TEXT("AT THE TUBE - F / B: grab the PFD and haul them in"));
    default:
        break;
    }
    if (RopeRecoverRemaining > 0.f)
        return FText::FromString(TEXT("MISSED - pulling the rope back in to throw again"));
    if (FlipLinePhase == ERaftSimFlipLinePhase::Completed && RaftMode != ERaftSimRaftMode::Capsized &&
        !IsPassengerSwimming(TEXT("guide")) && !Swimmers.IsEmpty())
        return FText::FromString(TEXT("BOAT RIGHTED - paddle to the swimmers (W/A/S/D) or throw the bag (R)"));
    return FText::GetEmpty();
}
