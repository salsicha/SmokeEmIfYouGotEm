#pragma once
#include "RaftSimFlexibleRaftModel.h"

namespace RaftSimOverwashLoads
{
struct FLoad { FVector ForceN=FVector::ZeroVector,TorqueNm=FVector::ZeroVector; };
// Reduced upper-face pressure loading, additional to the submerged chamber
// drag. Unlike the D3 risk magnitude, this has a signed force and a geometric
// application point. It does not prescribe a capsize angle or angular rate.
inline FLoad UpperFace(const FRaftSimFlexSegmentOverwash& Wet,
    const FRaftSimFlexTubeSegment& Tube,const FQuat& Orientation,double RadiusM)
{
    FLoad Load;
    if(!Wet.bWet || !Wet.bUpstreamExposed || RadiusM<=0.)return Load;
    const double Depth=FMath::Clamp(Wet.OvertoppingDepthM,0.,2.*RadiusM);
    const double Speed=FMath::Clamp(Wet.IncomingSpeedMps,0.,8.);
    const double PressurePa=.5*1000.*Speed*Speed;
    const FVector Normal=Orientation.RotateVector(Tube.OutwardNormal).GetSafeNormal();
    Load.ForceN=-Normal*(PressurePa*Depth*Tube.TributaryLengthM);
    const FVector Offset=Orientation.RotateVector(Wet.LocalPosition+FVector(0,0,RadiusM));
    Load.TorqueNm=FVector::CrossProduct(Offset,Load.ForceN);
    return Load;
}
}
