#pragma once

#include "CoreMinimal.h"

namespace RaftSimSpraySourceFootprint
{
// Bounded presentation-source check, NOT continuous particle/terrain collision.
// Sample the centre, edge midpoints and corners in the source's FLOW frame.
// Axis-aligned river-coordinate offsets rotate incorrectly on Cartesian rivers.
template<class FSampler>
bool Sample(const FVector2D& CentreM,const FVector2D& Flow,FSampler&& Sampler,FVector& OutCentreCm)
{
    OutCentreCm=FVector::ZeroVector;
    if (CentreM.ContainsNaN() || Flow.ContainsNaN() || Flow.SizeSquared()<=0.) return false;
    const FVector2D Along=Flow.GetSafeNormal(),Across(-Along.Y,Along.X);
    FVector Centre;
    if (!Sampler(CentreM,Centre) || Centre.ContainsNaN()) return false;
    for (double D:{-.8,0.,.8}) for (double A:{-1.5,0.,1.5})
    {
        if (D==0. && A==0.) continue;
        FVector Point;
        if (!Sampler(CentreM+Along*D+Across*A,Point) || Point.ContainsNaN()) return false;
    }
    OutCentreCm=Centre;
    return true;
}
}
