#pragma once

#include "CoreMinimal.h"

namespace RaftSimFoamTransport
{
// A smooth descending chute is not a breaking source merely because it is
// steep. Use rise along the current, in the same hydraulic coordinate frame.
// This is an optical source-onset proxy, not a measured air-entrainment rate.
// Resolved crest/wake sources and previously transported foam are independent.
inline float RisingSurfaceSlope(const FVector2D& Gradient,const FVector2D& Velocity)
{
    const double Speed=Velocity.Size();
    if (!FMath::IsFinite(Speed) || Speed<=0. || !FMath::IsFinite(Gradient.X) ||
        !FMath::IsFinite(Gradient.Y)) return 0.f;
    return float(FMath::Max(0.,FVector2D::DotProduct(Gradient,Velocity/Speed)));
}

// Source-generation budget only. Existing advected foam is not multiplied by
// this weight: a nonspilling wave can still receive a transported foam trail.
inline float BreakingSourceWeight(float PresentationWeight,float SpillingFraction,bool bUseHydraulicBudget)
{
    if (!FMath::IsFinite(PresentationWeight)) return 0.f;
    const float Weight=FMath::Clamp(PresentationWeight,0.f,1.f);
    if (!bUseHydraulicBudget) return Weight;
    if (!FMath::IsFinite(SpillingFraction)) return 0.f;
    return Weight*FMath::Clamp(SpillingFraction,0.f,1.f);
}

inline FVector2D SourceLeftDirection(const FVector2D& WorldTangent, const float WorldYSign)
{
    return FVector2D(-WorldTangent.Y, WorldTangent.X) * WorldYSign;
}

// The field is always station/source-left, even when the rendered world maps
// ENU north to -Y. Rotating the reflected tangent alone produces source-right.
inline FVector2D ProjectWorldVelocity(
    const FVector2D& WorldVelocity,
    const FVector2D& WorldTangent,
    const float WorldYSign)
{
    const FVector2D SourceLeft = SourceLeftDirection(WorldTangent, WorldYSign);
    return FVector2D(
        FVector2D::DotProduct(WorldVelocity, WorldTangent),
        FVector2D::DotProduct(WorldVelocity, SourceLeft));
}

inline FVector2D TransformFieldVelocity(
    const FVector2D& FieldVelocity,
    const FVector2D& WorldTangent,
    const float WorldYSign)
{
    return WorldTangent * FieldVelocity.X +
        SourceLeftDirection(WorldTangent, WorldYSign) * FieldVelocity.Y;
}

inline FVector TransformSurfaceNormal(
    const FVector& LocalNormal, const FVector& WorldTangent, const float WorldYSign)
{
    const FVector2D Left = SourceLeftDirection(FVector2D(WorldTangent.X,WorldTangent.Y),WorldYSign);
    return (WorldTangent*LocalNormal.X + FVector(Left.X,Left.Y,0)*LocalNormal.Y +
        FVector::UpVector*LocalNormal.Z).GetSafeNormal();
}
}
