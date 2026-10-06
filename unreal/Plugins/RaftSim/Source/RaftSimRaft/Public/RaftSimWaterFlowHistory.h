#pragma once

#include "CoreMinimal.h"

namespace RaftSimWaterFlowHistory
{
// Presentation velocity in the source/UV frame. Preserve history across wet
// refreshes; dry cells are cleared by the caller. Never alter solver momentum.
inline FVector2D Advance(const FVector2D& Previous, const FVector2D& Sample, float DeltaSeconds)
{
    if ((Sample-Previous).SizeSquared()>25.0) return Sample;
    const float Alpha=1.0f-FMath::Exp(-4.0f*FMath::Max(DeltaSeconds,0.0f));
    return FMath::Lerp(Previous,Sample,Alpha);
}
}
