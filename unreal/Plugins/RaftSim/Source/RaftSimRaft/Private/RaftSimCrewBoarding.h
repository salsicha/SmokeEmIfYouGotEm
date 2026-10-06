#pragma once
#include "CoreMinimal.h"

namespace RaftSimCrewBoarding
{
// Two-bone control solve; does not establish skin clearance or joint limits.
inline bool SolveLeg(const FVector& Hip, const FVector& Foot, double Thigh, double Shin,
    const FVector& BendHint, FVector& Knee)
{
    const FVector Delta = Foot-Hip;
    const double D = Delta.Size();
    if (Hip.ContainsNaN() || Foot.ContainsNaN() || !FMath::IsFinite(D) ||
        Thigh <= 0. || Shin <= 0. || D < FMath::Abs(Thigh-Shin)+.001 || D > Thigh+Shin-.001) return false;
    const FVector Axis = Delta/D;
    const FVector Bend = (BendHint-Axis*FVector::DotProduct(BendHint,Axis)).GetSafeNormal();
    if (Bend.IsNearlyZero()) return false;
    const double Along = (Thigh*Thigh-Shin*Shin+D*D)/(2.*D);
    Knee = Hip + Axis*Along + Bend*FMath::Sqrt(FMath::Max(0.,Thigh*Thigh-Along*Along));
    return !Knee.ContainsNaN();
}
}
