#pragma once

#include "CoreMinimal.h"
#include "EngineDefines.h"

namespace RaftSimWorldPositionGuard
{
inline bool IsValid(const FVector& Location)
{
    return !Location.ContainsNaN() && FMath::Abs(Location.X) <= HALF_WORLD_MAX &&
        FMath::Abs(Location.Y) <= HALF_WORLD_MAX && FMath::Abs(Location.Z) <= HALF_WORLD_MAX;
}

// Absolute river coordinates are not a measure of solver divergence. Preserve
// valid high-elevation/long-river poses; recover invalid positions to the last
// presented pose, never to a fabricated 500 m elevation or 50 km boundary.
inline bool Recover(FVector& Location, FVector& Velocity, const FVector& LastValidLocation)
{
    if (IsValid(Location)) return false;
    Location = IsValid(LastValidLocation) ? LastValidLocation : FVector::ZeroVector;
    Velocity = FVector::ZeroVector;
    return true;
}
}
