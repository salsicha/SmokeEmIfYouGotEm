#pragma once

#include "CoreMinimal.h"

/** Authored reduced-order currents, not measured or resolved CFD. SI units.
 * The compact streamfunctions have zero added section discharge in a flat,
 * constant-depth unobstructed control. Clipping, curved beds and owner overlap
 * do NOT inherit that proof. Surface tracers and immersed hulls share this code.
 */
namespace RaftSimWaterFeatureKinematics
{
// Bind to the playable map, not the retired longitudinal cooked-data path.
// PIE prefixes are allowed; unrelated rivers and review maps stay unchanged.
inline bool IsPlayableSouthFork(const FString& MapName)
{
    return MapName.EndsWith(TEXT("L_SouthForkAmerican_FullReach"));
}

inline double Compact(double T)
{
    const double B = 1.0 - T*T;
    return B > 0.0 ? B*B*B : 0.0;
}
inline double CompactDerivative(double T)
{
    const double B = 1.0 - T*T;
    return B > 0.0 ? -6.0*T*B*B : 0.0;
}

/** XZ roller: upstream at the surface, downstream below, no added flow
 * through either horizontal boundary. Integral of added u over depth is zero.
 * Vertical motion is turnover, not a constant downward attraction to a point.
 */
inline FVector HoleDelta(double X, double Y, double DepthFraction,
    double DepthM, double SpeedMps, double Strength)
{
    if (!FMath::IsFinite(X) || !FMath::IsFinite(Y) ||
        !FMath::IsFinite(DepthFraction) || !FMath::IsFinite(DepthM) ||
        !FMath::IsFinite(SpeedMps) || !FMath::IsFinite(Strength) ||
        DepthM <= 0.05 || SpeedMps <= 0.0 || Strength <= 0.0)
        return FVector::ZeroVector;
    const double T = (X-4.4)/4.0;
    const double Lane = Compact(Y/4.8);
    const double Z = FMath::Clamp(DepthFraction, 0.0, 1.0);
    const double A = 1.8*SpeedMps*FMath::Clamp(Strength, 0.0, 1.0)*Lane;
    // psi = A*Depth*f(X)*Z^2*(1-Z).
    return FVector(A*Compact(T)*(2.0*Z-3.0*Z*Z), 0.0,
        -A*DepthM*CompactDerivative(T)/4.0 * Z*Z*(1.0-Z));
}

/** Two horizontal circulation cells behind a rock. Derivatives of one XY
 * streamfunction, not inward-pointing attraction. Both components fade C1
 * to zero at the ellipse boundary; no added flow passes through the rock.
 */
inline FVector EddyDelta(double X, double Y, double RadiusM, double SpeedMps)
{
    if (!FMath::IsFinite(X) || !FMath::IsFinite(Y) ||
        !FMath::IsFinite(RadiusM) || !FMath::IsFinite(SpeedMps) ||
        RadiusM <= 0.0 || SpeedMps <= 0.0)
        return FVector::ZeroVector;
    const double R = FMath::Max(RadiusM, 0.75);
    const double Rx = 2.5*R, Ry = 0.9*R;
    FVector V = FVector::ZeroVector;
    for (const double Side : {-1.0, 1.0})
    {
        const double Tx = (X-3.0*R)/Rx;
        const double Ty = (Y-Side*Ry)/Ry;
        const double B = 1.0-Tx*Tx-Ty*Ty;
        if (B <= 0.0) continue;
        const double A = -Side*0.9*SpeedMps*Ry;
        V.X += -6.0*A*Ty*B*B/Ry;
        V.Y +=  6.0*A*Tx*B*B/Rx;
    }
    return V;
}
}
