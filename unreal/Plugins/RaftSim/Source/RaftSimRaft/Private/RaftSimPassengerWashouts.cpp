#include "RaftSimRaftActor.h"
#include "RaftSimCrewAvatarActor.h"
#include "RaftSimChronoRuntimeAdapter.h"

void ARaftSimRaftActor::UpdatePassengerWashouts(float DeltaSeconds)
{
    if (!RaftAdapter || RaftMode != ERaftSimRaftMode::Upright ||
        !FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.f) return;
    // Reduced gameplay retention model, not a human injury/force prediction.
    // Bound hitch exposure: a stale field sample cannot supply a long impact.
    const float Dt = FMath::Min(DeltaSeconds, .05f);
    const auto& K = RaftAdapter->GetKinematicState();
    for (int32 Index = 0; Index < PaddlerCount; ++Index)
    {
        const FName Id(*FString::Printf(TEXT("paddler_%d"), Index + 1));
        auto* Avatar = FindAvatar(Id);
        float& Exposure = PassengerWashImpulseNs.FindOrAdd(Id);
        if (!Avatar || Avatar->GetAttachParentActor() != this ||
            IsPassengerSwimming(Id) || Id == BoardingPassenger || Avatar == AssistedBoardingAvatar.Get())
        { Exposure = 0.f; PassengerSwampedSeconds.FindOrAdd(Id) = 0.f; continue; }

        // Sample each actual posed passenger, including high-side movement.
        // Speed alone, foam labels, and a river's catalog class never eject.
        const auto& Pose = Avatar->GetPublishedCrewPose();
        const FVector Hip = Avatar->GetActorTransform().TransformPosition(
            (Pose.LeftHipCm + Pose.RightHipCm) * .5);
        FRaftSimFlexUniformWater Water;
        const bool Wet = RaftAdapter->SampleBoundFlexibleWater(Hip, Water) && Water.bWet &&
            FMath::IsFinite(Water.SurfaceHeightM) && !Water.VelocityMps.ContainsNaN();
        const FVector PointVelocity = K.LinearVelocityMetersPerSecond +
            FVector::CrossProduct(K.AngularVelocityRadiansPerSecond, (Hip - GetActorLocation()) * .01);
        const FVector Relative = Wet ? (Water.VelocityMps - PointVelocity).GetClampedToMaxSize(8.) : FVector::ZeroVector;
        const double Depth = Wet ? Water.SurfaceHeightM - Hip.Z * .01 : 0.;
        const auto Action = Avatar->GetAvatarAction();
        // Bracing low or high-siding means a hand on the line and feet tucked:
        // twice the budget for either mechanism, never immunity.
        const bool Braced = Action == ERaftSimCrewAvatarAction::Brace ||
            Action == ERaftSimCrewAvatarAction::HighSidePort || Action == ERaftSimCrewAvatarAction::HighSideStarboard ||
            Avatar->HasHighSideTransfer();

        // Swamped seat: when this passenger's part of the boat is driven
        // under (a buried bow, a tube shoved under in a hole, the low side of
        // a hard heel) and water stands at their chest, the PFD floats them
        // off the tube. Any flow past them, or the boat tipping toward their
        // side, takes them away sooner. Waist-deep water alone does not.
        float& Swamped = PassengerSwampedSeconds.FindOrAdd(Id);
        if (Depth >= .5)
        {
            const FVector Out = GetActorRightVector() * (FVector::DotProduct(Hip - GetActorLocation(), GetActorRightVector()) >= 0. ? 1. : -1.);
            // Positive when this passenger's tube is the low one.
            const double Heel = -FVector::DotProduct(Out, GetActorUpVector());
            const double Carry = 1. + Relative.Size() / 1.5 + FMath::Clamp((Heel - .35) * 4., 0., 2.);
            Swamped += float(Carry) * Dt;
        }
        else Swamped = FMath::Max(0.f, Swamped - 3.f * Dt);
        if (Swamped >= (Braced ? 1.4f : .6f))
        {
            const float Held = Swamped;
            Swamped = Exposure = 0.f;
            // They leave with the water around them, not with the hull.
            SpawnSwimmers(1, false, Id, Relative * .5);
            UE_LOG(LogTemp, Display, TEXT("PASSENGER_SWAMPED id=%s depth_m=%.3f relative_mps=%.3f held_s=%.2f braced=%d"),
                *Id.ToString(), Depth, Relative.Size(), Held, Braced);
            continue;
        }

        if (Depth <= .15 || Relative.Size() < 2.)
        { Exposure = FMath::Max(0.f, Exposure - 880.f * Dt); continue; }

        // Wetted torso area grows with depth; sustained breaking-water drag
        // must overcome grip. Bracing doubles the impulse budget, not immunity.
        const double Force = FMath::Min(1800., .5 * 1000. * .45 * FMath::Min(Depth, .65) * Relative.SizeSquared());
        Exposure += float(Force) * Dt;
        if (Exposure < (Braced ? 440.f : 220.f)) continue;

        const float DeliveredImpulse = Exposure;
        Exposure = Swamped = 0.f;
        SpawnSwimmers(1, false, Id, Relative * .4);
        UE_LOG(LogTemp, Display, TEXT("PASSENGER_WASHOUT id=%s depth_m=%.3f relative_mps=%.3f impulse_ns=%.1f braced=%d"),
            *Id.ToString(), Depth, Relative.Size(), DeliveredImpulse, Braced);
    }
}
