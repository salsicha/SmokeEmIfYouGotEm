#include "RaftSimPhysicsClockSubsystem.h"

void URaftSimPhysicsClockSubsystem::CommitPhysicsPose(const FRaftSimPoseHistorySample& Sample)
{
    if (bHasCurrent)
    {
        PreviousSample = CurrentSample;
        bHasPrevious = true;
    }

    CurrentSample = Sample;
    bHasCurrent = true;
}

FRaftSimInterpolatedPose URaftSimPhysicsClockSubsystem::InterpolateForRender(float RenderTimeSeconds) const
{
    FRaftSimInterpolatedPose Result;
    if (!bHasCurrent)
    {
        return Result;
    }

    if (!bHasPrevious || FMath::IsNearlyEqual(CurrentSample.TimeSeconds, PreviousSample.TimeSeconds))
    {
        Result.Transform = CurrentSample.RaftState.WorldTransform;
        Result.FromFrame = CurrentSample.PhysicsFrame;
        Result.ToFrame = CurrentSample.PhysicsFrame;
        return Result;
    }

    const float Span = CurrentSample.TimeSeconds - PreviousSample.TimeSeconds;
    Result.Alpha = FMath::Clamp((RenderTimeSeconds - PreviousSample.TimeSeconds) / Span, 0.0f, 1.0f);
    Result.Transform.Blend(PreviousSample.RaftState.WorldTransform, CurrentSample.RaftState.WorldTransform, Result.Alpha);
    Result.FromFrame = PreviousSample.PhysicsFrame;
    Result.ToFrame = CurrentSample.PhysicsFrame;
    return Result;
}
