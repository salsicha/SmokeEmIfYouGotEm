#pragma once
#include "CoreMinimal.h"
namespace RaftSimCapsizePolicy
{
inline bool PhysicallyInverted(const FQuat& Orientation,double MinimumTiltDegrees)
{
    if(Orientation.ContainsNaN() || !Orientation.IsNormalized())return false;
    // Euler roll can report 180 degrees for a boat that merely pitched past
    // vertical. The actual hull-up vector is independent of Euler conventions.
    const double Tilt=FMath::Clamp(MinimumTiltDegrees,90.01,170.);
    return Orientation.GetUpVector().Z<=FMath::Cos(FMath::DegreesToRadians(Tilt));
}
}
