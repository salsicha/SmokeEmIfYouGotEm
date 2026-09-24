#pragma once
#include "CoreMinimal.h"
#include "RaftSimWaterRuntimeAdapter.h"

// The swim pose supplies body/head offsets above this datum. This is surface
// attachment, not a new buoyancy or dry-ground locomotion model.
inline bool RaftSimAttachSwimmerToSurface(FVector& PositionMeters, const FRaftSimWaterSample& Sample)
{
    if (!Sample.bWet || !FMath::IsFinite(Sample.SurfaceHeightMeters) || PositionMeters.ContainsNaN()) return false;
    PositionMeters.Z=Sample.SurfaceHeightMeters;
    return true;
}
