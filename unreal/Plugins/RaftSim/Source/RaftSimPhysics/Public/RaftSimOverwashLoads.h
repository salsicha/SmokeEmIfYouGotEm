#pragma once
#include "RaftSimFlexibleRaftModel.h"

namespace RaftSimOverwashLoads
{
struct FLoad { FVector ForceN=FVector::ZeroVector,TorqueNm=FVector::ZeroVector; };
struct FDiagnostics {FLoad Load;int32 WetUpperFaces=0;double MinimumFaceOffsetM=DBL_MAX,MaximumIncomingNormalMps=0.;};
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
// Water entering a dipped upper face transfers momentum
// into that face. Only incoming relative NORMAL flow loads it; tangential or
// outgoing flow cannot manufacture a downward force. This is a reduced patch
// pressure model, not a resolved flexible-tube pressure distribution.
inline FLoad ScoopingFace(const FRaftSimFlexSegmentOverwash& Wet,
    const FRaftSimFlexTubeSegment& Tube,const FQuat& Orientation,double RadiusM,
    const FVector& RelativeWaterVelocityMps)
{
    FLoad Load;
    if(!Wet.bWet || !Wet.bUpstreamExposed || RadiusM<=0.)return Load;
    const double Depth=FMath::Clamp(Wet.OvertoppingDepthM,0.,2.*RadiusM);
    const FVector Normal=Orientation.GetUpVector();
    const double Incoming=FMath::Clamp(-FVector::DotProduct(RelativeWaterVelocityMps,Normal),0.,8.);
    Load.ForceN=-Normal*(.5*1000.*Incoming*Incoming*Depth*Tube.TributaryLengthM);
    const FVector Offset=Orientation.RotateVector(Wet.LocalPosition+FVector(0,0,RadiusM));
    Load.TorqueNm=FVector::CrossProduct(Offset,Load.ForceN);
    return Load;
}
}
