#include "RaftSimRaftActor.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimCrewBoarding.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "ProceduralMeshComponent.h"
#include "Materials/MaterialInterface.h"

// Flip line, as guides carry and use it (NRS "How to make a flip line",
// Rafting Magazine BRS flip recovery, Boreal River webbing notes): webbing
// double-wrapped round the waist and closed with a locking carabiner. Climb
// onto the overturned hull, unclip it, clip it to a D-ring at the middle of
// one side, back across to the opposite tube and stand on its edge, then
// lean back. Rope tension and body weight lift the D-ring side; the hull
// rolls up and over toward the guide, who falls back into the water still
// holding the line, then climbs in to paddle or throw to the swimmers.

namespace
{
constexpr float kClimbEndSeconds = 2.0f;
constexpr float kUnclipSeconds = 2.35f;
constexpr float kClipSeconds = 3.1f;
constexpr float kAttachEndSeconds = 3.6f;
constexpr float kCrossEndSeconds = 5.4f;
constexpr double kFlipGuideMassKg = 85.0;
constexpr double kStandingLegCm = 44.0;

float Ease(float A)
{
    A = FMath::Clamp(A, 0.f, 1.f);
    return A * A * (3.f - 2.f * A);
}

void Upper(FRaftSimCrewAvatarPose& Pose, const FVector& TorsoCm, const FRotator& Lean)
{
    Pose.TorsoCenterCm = TorsoCm;
    Pose.TorsoRotation = Lean;
    const FQuat Rotation = Lean.Quaternion();
    Pose.HeadCenterCm = TorsoCm + Rotation.RotateVector(FVector(4.f, 0.f, 37.f));
    Pose.LeftShoulderCm = TorsoCm + Rotation.RotateVector(FVector(2.f, -17.f, 12.f));
    Pose.RightShoulderCm = TorsoCm + Rotation.RotateVector(FVector(2.f, 17.f, 12.f));
}

// Standing legs: hips either side of a centre, two-bone knees bent forward.
void Legs(FRaftSimCrewAvatarPose& Pose, const FVector& HipCenter, const FVector& LeftFoot, const FVector& RightFoot)
{
    Pose.LeftHipCm = HipCenter + FVector(0.f, -10.f, 0.f);
    Pose.RightHipCm = HipCenter + FVector(0.f, 10.f, 0.f);
    Pose.LeftFootCm = LeftFoot;
    Pose.RightFootCm = RightFoot;
    const auto Knee = [](const FVector& Hip, const FVector& Foot, FVector& Out)
    {
        if (!RaftSimCrewBoarding::SolveLeg(Hip, Foot, kStandingLegCm, kStandingLegCm, FVector(1.0, 0.0, 0.0), Out))
            Out = (Hip + Foot) * .5f + FVector(8.f, 0.f, 0.f);
    };
    Knee(Pose.LeftHipCm, LeftFoot, Pose.LeftKneeCm);
    Knee(Pose.RightHipCm, RightFoot, Pose.RightKneeCm);
}

FRaftSimCrewAvatarPose Mix(const FRaftSimCrewAvatarPose& A, const FRaftSimCrewAvatarPose& B, float Alpha)
{
    static FVector FRaftSimCrewAvatarPose::* const Points[] = {
        &FRaftSimCrewAvatarPose::TorsoCenterCm, &FRaftSimCrewAvatarPose::HeadCenterCm,
        &FRaftSimCrewAvatarPose::LeftShoulderCm, &FRaftSimCrewAvatarPose::RightShoulderCm,
        &FRaftSimCrewAvatarPose::LeftHandCm, &FRaftSimCrewAvatarPose::RightHandCm,
        &FRaftSimCrewAvatarPose::LeftHipCm, &FRaftSimCrewAvatarPose::RightHipCm,
        &FRaftSimCrewAvatarPose::LeftKneeCm, &FRaftSimCrewAvatarPose::RightKneeCm,
        &FRaftSimCrewAvatarPose::LeftFootCm, &FRaftSimCrewAvatarPose::RightFootCm};
    const float S = Ease(Alpha);
    FRaftSimCrewAvatarPose Out = S < .5f ? A : B;
    for (auto Point : Points) Out.*Point = FMath::Lerp(A.*Point, B.*Point, S);
    Out.TorsoRotation = FQuat::Slerp(A.TorsoRotation.Quaternion(), B.TorsoRotation.Quaternion(), S).Rotator();
    Out.FistGripBlend = FMath::Lerp(A.FistGripBlend, B.FistGripBlend, S);
    return Out;
}

FRaftSimCrewAvatarPose BarePose()
{
    FRaftSimCrewAvatarPose Pose = URaftSimCrewAvatarPoseLibrary::EvaluatePose(ERaftSimCrewAvatarAction::FlipLineStand, 1.f, 1);
    Pose.bShowPaddle = false;
    Pose.bFeetPlanted = true;
    Pose.FistGripBlend = 1.f;
    return Pose;
}

// Upright stance facing +X, hips at the given height, an optional lean.
FRaftSimCrewAvatarPose Stance(float HipZ, float HipBack, float Pitch, float Step = 0.f)
{
    FRaftSimCrewAvatarPose Pose = BarePose();
    const FVector Hip(-HipBack, 0.f, HipZ);
    Legs(Pose, Hip, FVector(10.f * Step, -15.f, 8.f * FMath::Max(0.f, Step)),
        FVector(-10.f * Step, 15.f, 8.f * FMath::Max(0.f, -Step)));
    Upper(Pose, Hip + FRotator(Pitch, 0.f, 0.f).RotateVector(FVector(0.f, 0.f, 22.f)), FRotator(Pitch, 0.f, 0.f));
    return Pose;
}

// Straight arms along the rope toward a point, fists a hand-width apart.
void ArmsAlongRope(FRaftSimCrewAvatarPose& Pose, const FVector& TowardCm, float ReachCm)
{
    for (const float Side : {-1.f, 1.f})
    {
        const FVector Shoulder = Side < 0.f ? Pose.LeftShoulderCm : Pose.RightShoulderCm;
        const FVector Grip = Shoulder + (TowardCm - Shoulder).GetSafeNormal() * (ReachCm + (Side < 0.f ? 0.f : 9.f));
        (Side < 0.f ? Pose.LeftHandCm : Pose.RightHandCm) = Grip + FVector(0.f, -2.f * Side, 0.f);
    }
}
}

bool ARaftSimRaftActor::IsFlipLineActive() const
{
    return FlipLinePhase >= ERaftSimFlipLinePhase::Climbing && FlipLinePhase <= ERaftSimFlipLinePhase::Pulling;
}

bool ARaftSimRaftActor::IsGuideRescuing() const
{
    // The guide's hands are busy while stripping in a missed rope or hauling
    // someone (or themselves) over the tube by the PFD.
    return RescueInteraction.Phase == ERaftSimRescueInteractionPhase::LineInFlight ||
        RescueInteraction.Phase == ERaftSimRescueInteractionPhase::Pulling ||
        RescueInteraction.Phase == ERaftSimRescueInteractionPhase::ReadyForReentry ||
        RescueInteraction.Phase == ERaftSimRescueInteractionPhase::Reseating ||
        RopeRecoverRemaining > 0.f || IsGuideBusyWithBoarding();
}

bool ARaftSimRaftActor::IsGuideBusyWithBoarding() const
{
    // The guide's own climb in, or their hands on someone's PFD; once that
    // swimmer is down on the floor and crawling to a seat the guide is free.
    if (!AssistedBoardingAvatar.IsValid()) return false;
    if (AssistedBoardingPassenger == TEXT("guide")) return true;
    return bAssistedBoardingByGuide && AssistedBoardingElapsed < AssistedBoardingHaulSeconds / .78f;
}

FVector ARaftSimRaftActor::GetRescueHandWorldM() const
{
    const auto* Guide = FindAvatar(TEXT("guide"));
    return Guide ? Guide->GetActorTransform().TransformPosition(Guide->GetPublishedCrewPose().LeftHandCm) * .01
        : GetActorLocation() * .01;
}

FText ARaftSimRaftActor::GetFlipLinePrompt() const
{
    switch (FlipLinePhase)
    {
    case ERaftSimFlipLinePhase::Climbing: return FText::FromString(TEXT("FLIP LINE - climbing onto the overturned hull"));
    case ERaftSimFlipLinePhase::Attaching:
        return FText::FromString(FlipLineSeconds < kUnclipSeconds + .2f
            ? TEXT("FLIP LINE - unclipping the carabiner, unwrapping the line from your waist")
            : TEXT("FLIP LINE - clipping the carabiner into the D-ring"));
    case ERaftSimFlipLinePhase::Crossing: return FText::FromString(TEXT("FLIP LINE - backing across to the far tube, paying out line"));
    case ERaftSimFlipLinePhase::Pulling: return FText::FromString(TEXT("FLIP LINE - feet on the tube edge, lean back and pull; fall clear as it rolls"));
    case ERaftSimFlipLinePhase::Failed: return FText::FromString(TEXT("FLIP LINE - pull interrupted; swim to the tube and retry SPACE / X"));
    default: return FText::FromString(TEXT("CAPSIZED - swim to the overturned raft; SPACE / X to climb and use flip line"));
    }
}

bool ARaftSimRaftActor::FindInvertedHullSupport(FVector& P) const
{
    // Ray through the actual published tube/floor mesh, from beneath in raft
    // coordinates. No guessed bounding-box deck or substitute collision hull.
    // Vertices are in the visual's frame, which sits a tube radius below the
    // actor origin; measure in actor space so the guide stands ON the hull.
    if (!RaftVisual) return false;
    const FTransform ToActor = RaftVisual->GetRelativeTransform();
    double Lowest = DBL_MAX;
    for (int Section=0; Section<RaftVisual->GetNumSections(); ++Section)
    {
    const auto* S = RaftVisual->GetProcMeshSection(Section);
    if (!S || !S->bSectionVisible) continue;
    for (int I=0; I+2<S->ProcIndexBuffer.Num(); I+=3)
    {
        const FVector A=ToActor.TransformPosition(FVector(S->ProcVertexBuffer[S->ProcIndexBuffer[I]].Position));
        const FVector B=ToActor.TransformPosition(FVector(S->ProcVertexBuffer[S->ProcIndexBuffer[I+1]].Position));
        const FVector C=ToActor.TransformPosition(FVector(S->ProcVertexBuffer[S->ProcIndexBuffer[I+2]].Position));
        const double D=(B.Y-C.Y)*(A.X-C.X)+(C.X-B.X)*(A.Y-C.Y);
        if (FMath::Abs(D)<1.e-8) continue;
        const double U=((B.Y-C.Y)*(P.X-C.X)+(C.X-B.X)*(P.Y-C.Y))/D;
        const double V=((C.Y-A.Y)*(P.X-C.X)+(A.X-C.X)*(P.Y-C.Y))/D;
        if (U>=0. && V>=0. && U+V<=1.) Lowest=FMath::Min(Lowest,U*A.Z+V*B.Z+(1.-U-V)*C.Z);
    }
    }
    if (Lowest==DBL_MAX) return false;
    P.Z=Lowest-3.;
    return true;
}

bool ARaftSimRaftActor::PrepareFlipLineStations()
{
    // Clip to the D-ring at the middle of the climbing side: the procedural
    // hull carries them at +/-0.23 L on the upper-outer tube shoulder
    // (RaftSimRaftMesh); the production hull has rings at x -26 / +30 cm.
    FBox Tube;
    if (!GetTubeOutlineLocalCm(Tube)) return false;
    const double HalfWidth = FMath::Max(FMath::Abs(Tube.Max.Y), FMath::Abs(Tube.Min.Y));
    const bool bForward = FlipClimbStartLocalCm.X >= 0.;
    const double RingX = bUsingProductionRaftRestMesh ? (bForward ? 30. : -26.)
        : (bForward ? 1. : -1.) * .23 * (Tube.Max.X - Tube.Min.X);
    FlipDRingLocalCm = FVector(RingX, FlipLineSide * (HalfWidth - 3.), 12.7);
    FlipEdgeLocalCm = FVector(RingX, FlipLineSide * (HalfWidth - 12.), 0.);
    FlipKneelLocalCm = FVector(RingX, FlipLineSide * (HalfWidth - 26.), 0.);
    FlipHookLocalCm = FVector(RingX, FlipLineSide * (HalfWidth - 34.), 0.);
    FlipStandLocalCm = FVector(RingX, -FlipLineSide * (HalfWidth - 20.), 0.);
    if (!FindInvertedHullSupport(FlipEdgeLocalCm) || !FindInvertedHullSupport(FlipKneelLocalCm) ||
        !FindInvertedHullSupport(FlipHookLocalCm) || !FindInvertedHullSupport(FlipStandLocalCm)) return false;
    // Hips at the outer edge, a body-depth below the exposed top.
    FlipEdgeLocalCm += FVector(0., FlipLineSide * 16., 20.);
    return true;
}

void ARaftSimRaftActor::CancelFlipLine()
{
    if (IsFlipLineActive())
    {
        if (auto* Guide=FindAvatar(TEXT("guide")))
        {
            Guide->ClearExternalPose();
            Guide->SetAvatarAction(ERaftSimCrewAvatarAction::Swimming);
        }
        RescueInteraction = FRaftSimRescueInteractionState{};
    }
    FlipLinePhase=ERaftSimFlipLinePhase::Idle;
    FlipLineSeconds=0.f;
    bFlipLineClipped=false;
}

void ARaftSimRaftActor::ReleaseFlipGuide()
{
    if (bFlipGuideReleased) return;
    bFlipGuideReleased=true;
    const int32 Id=FindSwimmerIndex(TEXT("guide"));
    if (auto* Guide=FindAvatar(TEXT("guide")))
    {
        Guide->ClearExternalPose();
        Guide->SetAvatarAction(ERaftSimCrewAvatarAction::Swimming);
        Guide->SetActorRotation(FRotator(0.f,Guide->GetActorRotation().Yaw,0.f));
        if (Swimmers.IsValidIndex(Id)) Swimmers[Id].SwimmerWorldPositionMeters=Guide->GetActorLocation()*.01;
    }
    // Into the water off the far tube with the boat's own drift, line in hand.
    if (Swimmers.IsValidIndex(Id) && RaftAdapter)
        Swimmers[Id].SwimmerDriftVelocityMetersPerSecond=RaftAdapter->GetKinematicState().LinearVelocityMetersPerSecond;
}

void ARaftSimRaftActor::UpdateFlipLine(float Dt)
{
    if (!IsFlipLineActive() || !FMath::IsFinite(Dt) || Dt<=0.f) return;
    const int32 Id=FindSwimmerIndex(TEXT("guide"));
    auto* Guide=FindAvatar(TEXT("guide"));
    if (!Swimmers.IsValidIndex(Id) || !Guide || !RaftAdapter)
    { CancelFlipLine(); return; }
    FlipLineSeconds+=FMath::Min(Dt,.25f);
    const float T=FlipLineSeconds;
    const float Up=GetActorUpVector().Z;
    // Completion follows integrated orientation, never a prescribed upright
    // transform. Position, downstream velocity, contact and damage survive.
    if (FlipLinePhase==ERaftSimFlipLinePhase::Pulling && Up>.65f)
    {
        ReleaseFlipGuide();
        FlipLinePhase=ERaftSimFlipLinePhase::Completed;
        FlipLineSeconds=0.f;
        RescueInteraction = FRaftSimRescueInteractionState{};
        RaftMode=ERaftSimRaftMode::Upright;
        RaftAdapter->SetFlexibleCapsized(false);
        return;
    }
    if (T>18.f || (FlipLinePhase!=ERaftSimFlipLinePhase::Pulling && Up>-.25f))
    {
        CancelFlipLine(); FlipLinePhase=ERaftSimFlipLinePhase::Failed; return;
    }
    FlipLinePhase=T<kClimbEndSeconds ? ERaftSimFlipLinePhase::Climbing : T<kAttachEndSeconds ? ERaftSimFlipLinePhase::Attaching
        : T<kCrossEndSeconds ? ERaftSimFlipLinePhase::Crossing : ERaftSimFlipLinePhase::Pulling;
    bFlipLineClipped=T>=kClipSeconds;
    const FTransform& Raft=GetActorTransform();
    const FVector ExposedUp=-GetActorUpVector();
    // The guide faces the D-ring side throughout: climbing on facing in,
    // turning at the top, then backing across with the line in front.
    const FVector RingSide=Raft.TransformVectorNoScale(FVector(0.,FlipLineSide,0.)).GetSafeNormal();
    FVector Local=FlipHookLocalCm;
    FVector Facing=RingSide;
    FVector BodyUp=ExposedUp;
    float FallBack=0.f;
    FRaftSimCrewAvatarPose Pose=Stance(70.f,4.f,-10.f);
    auto Action=ERaftSimCrewAvatarAction::FlipLineStand;
    if (FlipLinePhase==ERaftSimFlipLinePhase::Climbing)
    {
        Action=ERaftSimCrewAvatarAction::FlipLineClimb;
        const float A=T/kClimbEndSeconds;
        // Reach up onto the hull, kick and slide the belly over the edge,
        // get a knee on, then stand and turn to face the ring.
        FRaftSimCrewAvatarPose Reach=BarePose();
        Upper(Reach,FVector(4.f,0.f,40.f),FRotator(-20.f,0.f,0.f));
        Reach.LeftHandCm=FVector(36.f,-22.f,64.f); Reach.RightHandCm=FVector(36.f,22.f,64.f);
        Reach.LeftHipCm=FVector(-2.f,-10.f,22.f); Reach.RightHipCm=FVector(-2.f,10.f,22.f);
        Reach.LeftKneeCm=FVector(4.f,-11.f,-8.f); Reach.RightKneeCm=FVector(4.f,11.f,-8.f);
        Reach.LeftFootCm=FVector(-6.f,-12.f,-40.f); Reach.RightFootCm=FVector(-6.f,12.f,-40.f);
        FRaftSimCrewAvatarPose Belly=Reach;
        Upper(Belly,FVector(22.f,0.f,10.f),FRotator(-72.f,0.f,0.f));
        Belly.LeftHandCm=FVector(62.f,-24.f,16.f); Belly.RightHandCm=FVector(62.f,24.f,16.f);
        Belly.LeftHipCm=FVector(-4.f,-10.f,0.f); Belly.RightHipCm=FVector(-4.f,10.f,0.f);
        Belly.LeftKneeCm=FVector(-16.f,-11.f,-24.f); Belly.RightKneeCm=FVector(-16.f,11.f,-24.f);
        Belly.LeftFootCm=FVector(-30.f,-12.f,-52.f); Belly.RightFootCm=FVector(-30.f,12.f,-52.f);
        FRaftSimCrewAvatarPose Kneel=BarePose();
        Kneel.LeftHipCm=FVector(-6.f,-10.f,34.f); Kneel.RightHipCm=FVector(-6.f,10.f,34.f);
        Kneel.LeftKneeCm=FVector(12.f,-11.f,4.f); Kneel.LeftFootCm=FVector(-30.f,-12.f,3.f);
        Kneel.RightKneeCm=FVector(22.f,11.f,40.f); Kneel.RightFootCm=FVector(24.f,12.f,0.f);
        Upper(Kneel,FVector(2.f,0.f,56.f),FRotator(-24.f,0.f,0.f));
        Kneel.LeftHandCm=FVector(26.f,-20.f,8.f); Kneel.RightHandCm=FVector(24.f,14.f,40.f);
        const FRaftSimCrewAvatarPose Up0=Stance(66.f,4.f,-14.f);
        const FVector Start=FlipClimbStartLocalCm;
        if (A<.4f)
        {
            const float B=A/.4f;
            Local=FMath::Lerp(Start,FlipEdgeLocalCm,double(Ease(B)));
            // Clear the outside of the tube before crossing onto its underside.
            Local.Y+=FlipLineSide*25.f*FMath::Sin(PI*B);
            Pose=Mix(Reach,Belly,B);
        }
        else if (A<.75f) { const float B=(A-.4f)/.35f; Local=FMath::Lerp(FlipEdgeLocalCm,FlipKneelLocalCm,double(Ease(B))); Pose=Mix(Belly,Kneel,B); }
        else { const float B=(A-.75f)/.25f; Local=FMath::Lerp(FlipKneelLocalCm,FlipHookLocalCm,double(Ease(B))); Pose=Mix(Kneel,Up0,B); }
        // Facing into the hull until on top, then turn round to the ring.
        Facing=-RingSide;
        if (A>.75f) Facing=(-RingSide).RotateAngleAxis(180.f*Ease((A-.75f)/.25f),ExposedUp);
        Pose.FistGripBlend=A<.75f ? .6f : 0.f;
    }
    else if (FlipLinePhase==ERaftSimFlipLinePhase::Attaching)
    {
        Local=FlipHookLocalCm;
        const FTransform GuideFrame(FRotationMatrix::MakeFromXZ(Facing,BodyUp).ToQuat(),Raft.TransformPosition(Local));
        const FVector Ring=GuideFrame.InverseTransformPosition(Raft.TransformPosition(FlipDRingLocalCm));
        if (T<kUnclipSeconds+.25f)
        {
            // Hands to the locking carabiner at the front of the waist,
            // unscrew the gate and pull the double wrap free.
            const float U=Ease((T-kClimbEndSeconds)/(kUnclipSeconds+.25f-kClimbEndSeconds));
            Pose=Stance(70.f,4.f,-16.f);
            Pose.RightHandCm=FMath::Lerp(FVector(14.f,4.f,72.f),FVector(26.f,10.f,80.f),U);
            Pose.LeftHandCm=FMath::Lerp(FVector(8.f,-18.f,74.f),FVector(20.f,-8.f,84.f),U);
        }
        else
        {
            // Crouch at the edge, reach over and clip the D-ring, stand back up.
            const float Down=T<kClipSeconds ? Ease((T-kUnclipSeconds-.25f)/(kClipSeconds-kUnclipSeconds-.25f))
                : 1.f-Ease((T-kClipSeconds-.2f)/(kAttachEndSeconds-kClipSeconds-.2f));
            Pose=Mix(Stance(70.f,4.f,-16.f),Stance(36.f,10.f,-55.f),Down);
            Pose.RightHandCm=FMath::Lerp(FVector(28.f,8.f,84.f),Ring,double(Down));
            Pose.LeftHandCm=FMath::Lerp(FVector(22.f,-8.f,82.f),FVector(26.f,-10.f,34.f),Down);
        }
        Pose.FistGripBlend=1.f;
    }
    else if (FlipLinePhase==ERaftSimFlipLinePhase::Crossing)
    {
        const float A=Ease((T-kAttachEndSeconds)/(kCrossEndSeconds-kAttachEndSeconds));
        Local=FMath::Lerp(FlipHookLocalCm,FlipStandLocalCm,double(A));
        if (!FindInvertedHullSupport(Local))
        {CancelFlipLine(); FlipLinePhase=ERaftSimFlipLinePhase::Failed; return;}
        // Backing across, short steps, paying the line out through both fists.
        Pose=Stance(80.f,6.f,-6.f,FMath::Sin((T-kAttachEndSeconds)*PI*3.f));
        const FTransform GuideFrame(FRotationMatrix::MakeFromXZ(Facing,BodyUp).ToQuat(),Raft.TransformPosition(Local));
        ArmsAlongRope(Pose,GuideFrame.InverseTransformPosition(Raft.TransformPosition(FlipDRingLocalCm)),34.f);
    }
    else
    {
        Action=ERaftSimCrewAvatarAction::FlipLinePull;
        Local=FlipStandLocalCm;
        // Stand upright in the world while the hull rolls under the feet.
        // Face across the hull as it lay when the pull began: the raft's own
        // side axis swings through vertical as it comes over, and following
        // it would spin the guide round and drop them on the rising side.
        BodyUp=FVector::UpVector;
        if (FlipPullFacing.IsNearlyZero())
        {
            FlipPullFacing=FVector::VectorPlaneProject(RingSide,BodyUp).GetSafeNormal();
            if (FlipPullFacing.IsNearlyZero()) FlipPullFacing=FVector::ForwardVector;
        }
        Facing=FlipPullFacing;
        // Heave in pulses, sitting further back on each one.
        const float Heave=FMath::Max(0.f,FMath::Sin(2.f*PI*(T-kCrossEndSeconds)/1.3f));
        FallBack=Ease((Up+.45f)/.5f);
        FRaftSimCrewAvatarPose Lean=Stance(64.f-6.f*Heave,26.f+6.f*Heave,30.f+8.f*Heave);
        FRaftSimCrewAvatarPose Fall=BarePose();
        Upper(Fall,FVector(-30.f,0.f,46.f),FRotator(68.f,0.f,0.f));
        Fall.LeftHipCm=FVector(-30.f,-10.f,40.f); Fall.RightHipCm=FVector(-30.f,10.f,40.f);
        Fall.LeftKneeCm=FVector(6.f,-11.f,52.f); Fall.RightKneeCm=FVector(6.f,11.f,52.f);
        Fall.LeftFootCm=FVector(34.f,-12.f,34.f); Fall.RightFootCm=FVector(34.f,12.f,34.f);
        Pose=Mix(Lean,Fall,FallBack);
        const FVector Stand=Raft.TransformPosition(Local);
        const FTransform GuideFrame(FRotationMatrix::MakeFromXZ(Facing,BodyUp).ToQuat(),Stand);
        ArmsAlongRope(Pose,GuideFrame.InverseTransformPosition(Raft.TransformPosition(FlipDRingLocalCm)),50.f);
        Pose.FistGripBlend=1.f;
        if (Up>.05f) ReleaseFlipGuide();
    }
    if (!bFlipGuideReleased)
    {
        FVector World=Raft.TransformPosition(Local);
        // Falling back off the far tube into the water, still on the line,
        // landing at the surface the guide climbed out of.
        if (FallBack>0.f)
        {
            World+=-Facing*70.f*FallBack;
            World.Z=FMath::Lerp(World.Z,double(FlipWaterWorldZCm),double(FallBack));
        }
        Swimmers[Id].SwimmerWorldPositionMeters=World*.01;
        Guide->SetActorLocationAndRotation(World,FRotationMatrix::MakeFromXZ(Facing,BodyUp).ToQuat());
        Guide->SetAvatarAction(Action);
        Pose.bShowPaddle=false;
        Guide->SetExternalPose(Pose,true);
    }
    RescueInteraction.bLineVisible=false;
    if (FlipLinePhase==ERaftSimFlipLinePhase::Pulling && !bFlipGuideReleased)
    {
        // Statics of the lean: the rope pulls the D-ring toward the guide's
        // fists, the guide's feet push back on the far tube and carry their
        // weight. Net force is the guide's weight; the couple between rope
        // and feet plus the weight on the far edge roll the ring side up.
        const double CmToM=.01;
        const FVector Center=Raft.GetLocation()*CmToM;
        const FVector Ring=Raft.TransformPosition(FlipDRingLocalCm)*CmToM;
        const FVector Feet=Guide->GetActorLocation()*CmToM;
        const auto& Published=Guide->GetPublishedCrewPose();
        const FVector Fists=Guide->GetActorTransform().TransformPosition((Published.LeftHandCm+Published.RightHandCm)*.5)*CmToM;
        FVector Rope=(Fists-Ring).GetSafeNormal();
        if (Rope.IsNearlyZero()) Rope=(Feet-Ring).GetSafeNormal();
        const FVector Lift=FVector::CrossProduct(Ring-Center,FVector::UpVector).GetSafeNormal();
        const double Rate=FVector::DotProduct(RaftAdapter->GetKinematicState().AngularVelocityRadiansPerSecond,Lift);
        // Lean harder while the hull resists; ease off once it is rolling.
        const double Effort=FMath::Clamp((.75-Rate)*1.5,.3,1.);
        const double Heave=1.+.35*FMath::Max(0.,FMath::Sin(2.*PI*(T-kCrossEndSeconds)/1.3));
        // Once the feet leave the tube there is nothing to lean against: the
        // couple and the weight fade together and the hull rolls on by its
        // own momentum and buoyancy, never jerked by an unbalanced line.
        const double OnHull=1.-FallBack;
        const double Weight=kFlipGuideMassKg*9.81*OnHull;
        const double Tension=FlipLineLeverage*kFlipGuideMassKg*9.81*(.55+1.2*Effort)*Heave*OnHull;
        const FVector OnRing=Rope*Tension;
        const FVector OnFeet=-FVector::UpVector*Weight-Rope*Tension;
        const FVector Torque=FVector::CrossProduct(Ring-Center,OnRing)+FVector::CrossProduct(Feet-Center,OnFeet);
        RaftAdapter->AddExternalImpulse((OnRing+OnFeet)*Dt,Torque*Dt);
        LastFlipLineTorqueNm=Torque.Size();
        FlipLineLogSeconds+=Dt;
        if (FlipLineLogSeconds>=.5f)
        {
            FlipLineLogSeconds=0.f;
            UE_LOG(LogTemp,Display,TEXT("FLIP_LINE_PULL t=%.2f up_z=%.3f righting_rate=%.3f tension_n=%.0f torque_nm=%.0f lift_torque_nm=%.0f"),
                T,Up,Rate,Tension,LastFlipLineTorqueNm,FVector::DotProduct(Torque,Lift));
        }
    }
}

bool ARaftSimRaftActor::FlipLineRopeVisible() const
{
    // Out of its waist wrap from the unclip until the guide is aboard again.
    return (IsFlipLineActive() && FlipLineSeconds>=kUnclipSeconds) ||
        (FlipLinePhase==ERaftSimFlipLinePhase::Completed && bFlipGuideReleased && IsPassengerSwimming(TEXT("guide")));
}

void ARaftSimRaftActor::BuildFlipLineRope(TArray<FVector>& Points, TArray<float>& Sag) const
{
    const auto* Guide=FindAvatar(TEXT("guide"));
    if (!Guide) return;
    const auto& Pose=Guide->GetPublishedCrewPose();
    const FTransform& G=Guide->GetActorTransform();
    const FVector Left=G.TransformPosition(Pose.LeftHandCm), Right=G.TransformPosition(Pose.RightHandCm);
    if (!bFlipLineClipped)
    {
        // Unwrapped: carabiner end in one fist, the coil in the other.
        Points={Right,Left,Left-FVector(0,0,40)};
        Sag={10.f,6.f};
        return;
    }
    const FVector Ring=GetActorTransform().TransformPosition(FlipDRingLocalCm);
    const bool bLeftFore=FVector::DistSquared(Left,Ring)<FVector::DistSquared(Right,Ring);
    const FVector Fore=bLeftFore?Left:Right, Rear=bLeftFore?Right:Left;
    const bool bTaut=FlipLinePhase==ERaftSimFlipLinePhase::Pulling;
    Points={Ring,Fore,Rear,Rear-FVector(0,0,45)+(Rear-Fore).GetSafeNormal()*15.};
    Sag={bTaut?2.f:float(FVector::Distance(Ring,Fore))*.08f,2.f,8.f};
}

void ARaftSimRaftActor::UpdateGuideWaistLine()
{
    // The guide's flip line lives double-wrapped round the waist, closed by
    // a locking carabiner at the front, whenever it is not in use.
    const auto* Guide=FindAvatar(TEXT("guide"));
    const bool bWorn=Guide && !FlipLineRopeVisible() && !Guide->IsHidden();
    if (!GuideWaistLineVisual && bWorn)
    {
        GuideWaistLineVisual=NewObject<UProceduralMeshComponent>(this,TEXT("GuideWaistLine"));
        GuideWaistLineVisual->SetupAttachment(Root);
        GuideWaistLineVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        GuideWaistLineVisual->SetCastShadow(false);
        GuideWaistLineVisual->RegisterComponent();
    }
    if (!GuideWaistLineVisual) return;
    GuideWaistLineVisual->SetVisibility(bWorn);
    if (!bWorn) return;
    const auto& Pose=Guide->GetPublishedCrewPose();
    const FTransform Body=FTransform(Pose.TorsoRotation,(Pose.LeftHipCm+Pose.RightHipCm)*.5)*Guide->GetActorTransform();
    const FTransform ToRaft=Body.GetRelativeTransform(GetActorTransform());
    TArray<FVector> Vertices,Normals; TArray<int32> Triangles; TArray<FVector2D> UVs; TArray<FProcMeshTangent> Tangents;
    const auto Tube=[&](const TArray<FVector>& Path,float Radius,bool bClosed)
    {
        constexpr int32 Sides=5;
        const int32 Base=Vertices.Num();
        const int32 Count=Path.Num();
        for (int32 I=0;I<Count;++I)
        {
            const FVector Tangent=(Path[(I+1)%Count]-Path[(I+Count-1)%Count]).GetSafeNormal();
            FVector Side=FVector::CrossProduct(Tangent,FVector::UpVector).GetSafeNormal();
            if (Side.IsNearlyZero()) Side=FVector::ForwardVector;
            const FVector UpAxis=FVector::CrossProduct(Side,Tangent);
            for (int32 S=0;S<Sides;++S)
            {
                const float Angle=2.f*PI*S/Sides;
                const FVector Normal=FMath::Cos(Angle)*Side+FMath::Sin(Angle)*UpAxis;
                Vertices.Add(ToRaft.TransformPosition(Path[I]+Normal*Radius));
                Normals.Add(ToRaft.TransformVectorNoScale(Normal));
                UVs.Add(FVector2D(float(I)/Count,float(S)/Sides));
                Tangents.Add(FProcMeshTangent(ToRaft.TransformVectorNoScale(Tangent),false));
            }
        }
        for (int32 I=0;I<(bClosed?Count:Count-1);++I)
            for (int32 S=0;S<Sides;++S)
            {
                const int32 N=(S+1)%Sides, J=(I+1)%Count;
                Triangles.Append({Base+I*Sides+S,Base+J*Sides+S,Base+I*Sides+N,Base+I*Sides+N,Base+J*Sides+S,Base+J*Sides+N});
            }
    };
    // Two wraps just below the vest hem, then the carabiner at the front.
    for (const float Z : {4.f,7.f})
    {
        TArray<FVector> Ring;
        for (int32 I=0;I<20;++I)
        {
            const float Angle=2.f*PI*I/20.f;
            Ring.Add(FVector(20.f*FMath::Cos(Angle),23.f*FMath::Sin(Angle),Z+.6f*FMath::Sin(3.f*Angle)));
        }
        Tube(Ring,1.1f,true);
    }
    TArray<FVector> Biner;
    for (int32 I=0;I<12;++I)
    {
        const float Angle=2.f*PI*I/12.f;
        Biner.Add(FVector(21.f,2.4f*FMath::Cos(Angle),5.5f+4.f*FMath::Sin(Angle)));
    }
    Tube(Biner,.45f,true);
    const TArray<FLinearColor> Colors;
    GuideWaistLineVisual->CreateMeshSection_LinearColor(0,Vertices,Triangles,Normals,UVs,Colors,Tangents,false);
    if (!RopeMaterial)
        RopeMaterial=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/RaftSim/Materials/M_RaftSim_PFD_Yellow.M_RaftSim_PFD_Yellow"));
    if (RopeMaterial && GuideWaistLineVisual->GetMaterial(0)!=RopeMaterial) GuideWaistLineVisual->SetMaterial(0,RopeMaterial);
}
