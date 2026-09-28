#pragma once
#include "RaftSimThreeWetBankContour.h"

// Candidate for the Cartesian shoreline path. Do not enable before the whole
// contour, attributes, cache and render packet use the SAME stored coordinates.
// A binary64-local root is not a proof of the binary32 position sent to the GPU.
namespace RaftSimSharedBankCrossing
{
struct FResult
{
    double Position=0.; // Exactly representable as binary32.
    double WetToDryFraction=0.; // Attribute interpolation, not a depth clamp.
    double MaximumRetreatCm=0.;
};

// W/D are semantic wet/dry endpoints, independent of neighboring cell winding.
// Only one varying Cartesian coordinate is handled here. The caller must
// establish an axis-aligned edge and preserve its other coordinate identically.
// The unmodified donor stage intersects the bed at W+(D-W)*H/(Bd-Bw).
inline bool Build(double W,double D,double Bw,double Bd,double H,double WidthCm,FResult& Out)
{
    using namespace RaftSimThreeWetBankContour;
    const FScopedIEEE Scope;
    Out={};
#if !PLATFORM_CPU_X86_FAMILY
    return false;
#endif
    if(!FMath::IsFinite(W) || !FMath::IsFinite(D) || !FMath::IsFinite(Bw) ||
        !FMath::IsFinite(Bd) || !FMath::IsFinite(H) || !FMath::IsFinite(WidthCm) ||
        W==D || H<=0. || WidthCm<=0. || double(float(W))!=W || double(float(D))!=D)return false;
    const FBound Drop=FBound(Bd)-FBound(Bw);
    if((Drop-FBound(H)).Lo<=0.)return false; // Advancing fronts have a different contract.
    const FBound T=DividePositive(FBound(H),Drop);
    const FBound Root=FBound(W)+(FBound(D)-FBound(W))*T;
    if(!FMath::IsFinite(Root.Lo) || !FMath::IsFinite(Root.Hi))return false;
    const bool Increasing=D>W;
    double Bound=Increasing ? Root.Lo : Root.Hi;
    // A nearest-wet root can leave no representable interior endcap when
    // the dry root approaches a corner. Reserve half of the SAME geometric
    // band toward the wet endpoint, after allowing for a full GPU step.
    // This is a shared-edge policy (only W,D and their original donors),
    // never a cell-specific offset, depth floor or enlarged error bound.
    double Spacing=0.;
    for(double Endpoint:{W,D})for(float Direction:{-std::numeric_limits<float>::infinity(),std::numeric_limits<float>::infinity()})
        Spacing=FMath::Max(Spacing,FMath::Abs(double(std::nextafter(float(Endpoint),Direction))-Endpoint));
    const double Reserve=WidthCm>Spacing ? Down((WidthCm-Spacing)*.5) : 0.;
    Bound=Increasing ? FMath::Max(W,Down(Bound-Reserve)) : FMath::Min(W,Up(Bound+Reserve));
    float Stored=float(Bound);
    if(Increasing ? double(Stored)>Bound : double(Stored)<Bound)
        Stored=std::nextafter(Stored,Increasing ? -std::numeric_limits<float>::infinity() : std::numeric_limits<float>::infinity());
    const double P=double(Stored);
    if(!FMath::IsFinite(P) || (Increasing ? P<W || P>D : P>W || P<D))return false;
    const FBound Distance=Increasing ? Root-FBound(P) : FBound(P)-Root;
    if(Distance.Lo<0. || Distance.Hi>WidthCm)return false;
    // Recheck the actual stored point against the original physical numerator;
    // inward root rounding alone is not used as an unchecked acceptance flag.
    const FBound Length=Increasing ? FBound(D)-FBound(W) : FBound(W)-FBound(D);
    const FBound Travel=Increasing ? FBound(P)-FBound(W) : FBound(W)-FBound(P);
    const FBound Wet=FBound(H)*Length-Drop*Travel;
    if(!FMath::IsFinite(Wet.Lo) || Wet.Lo<0.)return false;
    Out.Position=P;Out.WetToDryFraction=(P-W)/(D-W);Out.MaximumRetreatCm=Distance.Hi;
    return true;
}
}
