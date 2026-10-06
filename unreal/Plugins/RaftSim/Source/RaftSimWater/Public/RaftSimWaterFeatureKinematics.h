#pragma once

#include "CoreMinimal.h"

/** Authored reduced-order currents, not measured or resolved CFD. SI units.
 * The compact streamfunctions have zero added section discharge in a flat,
 * constant-depth unobstructed control. Clipping, curved beds and owner overlap
 * do NOT inherit that proof. Surface tracers and immersed hulls share this code.
 */
namespace RaftSimWaterFeatureKinematics
{
// Exact production river allowlist; review maps and training remain unchanged.
inline bool IsPlayableRiver(const FString& MapName)
{
    FString Leaf=MapName;
    int32 Slash=INDEX_NONE;
    if(Leaf.FindLastChar(TEXT('/'),Slash))Leaf=Leaf.Mid(Slash+1);
    if(Leaf.StartsWith(TEXT("UEDPIE_")))
    {
        const FString Tail=Leaf.Mid(7);
        int32 Separator=INDEX_NONE;
        if(!Tail.FindChar(TEXT('_'),Separator) || Separator==0)return false;
        for(int32 I=0;I<Separator;++I)if(!FChar::IsDigit(Tail[I]))return false;
        Leaf=Tail.Mid(Separator+1);
    }
    for(const TCHAR* Name : {TEXT("L_SouthForkAmerican_FullReach"),TEXT("L_SouthFork_Troublemaker"),
        TEXT("L_Hance"),TEXT("L_LavaCanyon"),TEXT("L_Terminator"),TEXT("L_UpperHuacas"),
        TEXT("L_Zambezi"),TEXT("L_ZambeziUpperGorge"),TEXT("L_Colorado_BadgerCreek"),
        TEXT("L_Colorado_HouseRock")})
        if(Leaf==Name)return true;
    return false;
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

// Compact C2 oblique-current potential. Its derivative is one through the
// return lane AND inlet, avoiding a centre-only correction that merely moves
// harmful drift from the head to the entry. The two exterior shoulders return
// the potential to zero at the unchanged wake support. Authored/inferred,
// not a measured channel or a velocity clamp; wet/contact authority is intact.
inline double EddyCrossPotential(double X,double R,double& Derivative)
{
    Derivative=0.;
    if (X<=0. || X>=6.5*R) return 0.;
    double W=1.,D=0.;
    const auto Ramp=[](double T,double& S,double& DS)
    {
        S=T*T*T*(10.+T*(-15.+6.*T));
        DS=30.*T*T*(1.-T)*(1.-T);
    };
    if (X<1.25*R){Ramp(X/(1.25*R),W,D);D/=1.25*R;}
    else if (X>4.5*R){Ramp((6.5*R-X)/(2.*R),W,D);D/=-2.*R;}
    const double Center=2.875*R;
    Derivative=W+(X-Center)*D;
    return (X-Center)*W;
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

/** One antisymmetric wake streamfunction. Unlike two disjoint ellipses, its
 * inner return branch includes the centreline behind the obstacle. Its head
 * turns outward and its outer branch returns to the downstream current.
 * Radius is an authored/inferred wake scale, not a measured boundary or collider.
 * The wake is additive: actual solid/wet exclusion remains authoritative.
 * The isolated box demo additionally masks the TOTAL streamfunction at its
 * box boundary; that boundary proof does not transfer to clipped river cells.
 */
inline double EddyWakePsi(double X, double Y, double RadiusM, double SpeedMps,double AcrossMps=0.)
{
    if (!FMath::IsFinite(X) || !FMath::IsFinite(Y) ||
        !FMath::IsFinite(RadiusM) || !FMath::IsFinite(SpeedMps) || !FMath::IsFinite(AcrossMps) ||
        RadiusM <= 0.0 || SpeedMps <= 0.0)
        return 0.0;
    const double R = FMath::Max(RadiusM, 0.75);
    const double Rx=3.25*R,Tx=(X-Rx)/Rx,Ty=Y/(2.*R);
    // Cancel incident cross-current at the wake core with a SECOND compact
    // streamfunction, not a direct side-force or velocity clamp. Its return
    // lobes rejoin the untouched ambient flow outside the same support.
    double CrossDerivative;
    const double CrossPotential=EddyCrossPotential(X,R,CrossDerivative);
    return (-3.0*SpeedMps*Y*Compact(Tx)+AcrossMps*CrossPotential)*Compact(Ty);
}

inline FVector EddyDelta(double X, double Y, double RadiusM, double SpeedMps,double AcrossMps=0.)
{
    if (!FMath::IsFinite(X) || !FMath::IsFinite(Y) ||
        !FMath::IsFinite(RadiusM) || !FMath::IsFinite(SpeedMps) || !FMath::IsFinite(AcrossMps) ||
        RadiusM <= 0.0 || SpeedMps <= 0.0)
        return FVector::ZeroVector;
    const double R = FMath::Max(RadiusM, 0.75);
    const double Rx = 3.25*R, Ry = 2.0*R;
    if (X <= 0.0 || X >= 2.0*Rx || FMath::Abs(Y) >= Ry)
        return FVector::ZeroVector;
    const double Tx = (X-Rx)/Rx, Ty = Y/Ry;
    double CrossDerivative;
    const double CrossPotential=EddyCrossPotential(X,R,CrossDerivative);
    return FVector(-3.0*SpeedMps*Compact(Tx)*
        (Compact(Ty)+Ty*CompactDerivative(Ty))+
            AcrossMps*CrossPotential*CompactDerivative(Ty)/Ry,
        3.0*SpeedMps*Y*CompactDerivative(Tx)*Compact(Ty)/Rx-
            AcrossMps*CrossDerivative*Compact(Ty),0.0);
}
}
