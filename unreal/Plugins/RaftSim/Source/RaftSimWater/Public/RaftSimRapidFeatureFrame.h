#pragma once
#include "CoreMinimal.h"

// Coordinate transfer only. The crest normal and the downstream activation
// axis are distinct: a diagonal wave must not redefine what downstream means.
// Both axes must be transferred when a curved profile enters an east/north grid.
namespace RaftSimRapidFeatureFrame
{
inline bool IsPlanarBasis(const FVector& Tangent,const FVector& Lateral)
{
    return !Tangent.ContainsNaN() && !Lateral.ContainsNaN() &&
        FMath::Abs(Tangent.Z)<=1.e-6 && FMath::Abs(Lateral.Z)<=1.e-6 &&
        FMath::Abs(Tangent.SizeSquared()-1.)<=1.e-6 &&
        FMath::Abs(Lateral.SizeSquared()-1.)<=1.e-6 &&
        FMath::Abs(FVector::DotProduct(Tangent,Lateral))<=1.e-6;
}

inline bool ReexpressAngle(double Degrees,const FVector& SourceTangent,
    const FVector& SourceLateral,const FVector& TargetTangent,
    const FVector& TargetLateral,double& OutDegrees)
{
    OutDegrees=0.;
    if(!FMath::IsFinite(Degrees) || !IsPlanarBasis(SourceTangent,SourceLateral) ||
        !IsPlanarBasis(TargetTangent,TargetLateral))return false;
    const double A=FMath::DegreesToRadians(Degrees);
    const FVector Direction=SourceTangent*FMath::Cos(A)+SourceLateral*FMath::Sin(A);
    OutDegrees=FMath::RadiansToDegrees(FMath::Atan2(
        FVector::DotProduct(Direction,TargetLateral),FVector::DotProduct(Direction,TargetTangent)));
    return FMath::IsFinite(OutDegrees);
}

// The caller retains the existing wetness, depth and finite-velocity gates.
// Zero degrees preserves the old curved-chart positive-X activation test.
inline double DownstreamSpeed(const FVector& FieldVelocity,double FlowAxisDegrees)
{
    const double A=FMath::DegreesToRadians(FlowAxisDegrees);
    return FieldVelocity.X*FMath::Cos(A)+FieldVelocity.Y*FMath::Sin(A);
}
}
