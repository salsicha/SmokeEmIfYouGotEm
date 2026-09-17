#pragma once

#include "CoreMinimal.h"

namespace RaftSimSpraySourceFootprint
{
// Bounded presentation-source check, NOT continuous particle/terrain collision.
// Sample the centre, edge midpoints and corners in the source's FLOW frame.
// Retain the original +/-0.8 m probes and add +/-1.05 m: the aerosol
// half-length at maximum scale plus downstream offset is .48*1.35+.35=.998 m.
// Across-flow 1.5 m includes the largest half-width (1.05*1.35=1.4175 m).
// Axis-aligned river-coordinate offsets rotate incorrectly on Cartesian rivers.
template<class FSampler>
bool Sample(const FVector2D& CentreM,const FVector2D& Flow,FSampler&& Sampler,FVector& OutCentreCm)
{
    OutCentreCm=FVector::ZeroVector;
    if (CentreM.ContainsNaN() || Flow.ContainsNaN() || Flow.SizeSquared()<=0.) return false;
    const FVector2D Along=Flow.GetSafeNormal(),Across(-Along.Y,Along.X);
    FVector Centre;
    if (!Sampler(CentreM,Centre) || Centre.ContainsNaN()) return false;
    for (double D:{-1.05,-.8,0.,.8,1.05}) for (double A:{-1.5,0.,1.5})
    {
        if (D==0. && A==0.) continue;
        FVector Point;
        if (!Sampler(CentreM+Along*D+Across*A,Point) || Point.ContainsNaN()) return false;
    }
    OutCentreCm=Centre;
    return true;
}
}
