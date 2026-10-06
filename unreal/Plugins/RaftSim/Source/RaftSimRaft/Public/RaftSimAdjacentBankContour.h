#pragma once
#include "CoreMinimal.h"

namespace RaftSimAdjacentBankContour
{
// Canonical order is wet-left, wet-right, dry-left, dry-right. Side order:
// bottom, right, top, left in the source cell's local coordinates.
inline int32 Corner(int32 Side,int32 I)
{
    static constexpr int32 Ids[4][4]={{0,1,2,3},{1,3,0,2},{2,3,0,1},{0,2,1,3}};
    return Ids[Side][I];
}
inline FVector2D Local(int32 Side,const FVector2D& P)
{
    switch(Side)
    {
    case 0:return P;
    case 1:return FVector2D(1.-P.Y,P.X);
    case 2:return FVector2D(P.X,1.-P.Y);
    default:return FVector2D(P.Y,P.X);
    }
}
inline double Along(int32 Side,const FVector2D& P){return Side%2 ? P.Y : P.X;}
struct FCurve
{
    double H0,H1,D0,D1,K,Delta;
    double H(double X) const {return (1.-X)*H0+X*H1;}
    double D(double X) const {return (1.-X)*D0+X*D1;}
    double Value(double X) const {return H(X)/D(X);}
    bool Convex() const {return -Delta*K>0.;}
};
inline FCurve Make(const double (&B)[4],const double (&H)[4],int32 Side)
{
    const int32 W0=Corner(Side,0),W1=Corner(Side,1),D0=Corner(Side,2),D1=Corner(Side,3);
    FCurve C{H[W0],H[W1],B[D0]-B[W0],B[D1]-B[W1],0.,0.};
    C.K=C.H1*C.D0-C.H0*C.D1;C.Delta=C.D1-C.D0;
    return C;
}
inline int32 Eligible(const double (&B)[4],const double (&H)[4])
{
    for(int32 Side=0;Side<4;++Side)
    {
        const int32 W0=Corner(Side,0),W1=Corner(Side,1),D0=Corner(Side,2),D1=Corner(Side,3);
        if(H[W0]<=0. || H[W1]<=0. || H[D0]!=0. || H[D1]!=0.)continue;
        const double High=FMath::Max(B[W0]+H[W0],B[W1]+H[W1]);
        if(B[D0]<=High || B[D1]<=High)continue;
        const auto C=Make(B,H,Side);
        // The existing common-edge chord is already exact in linear cases.
        if(C.Delta!=0. && C.K!=0.)return Side;
    }
    return INDEX_NONE;
}

// Width, not a hydraulic depth floor. Adaptive subdivision preserves this
// 1mm geometric bound; no fixed segment budget silently replaces the bound.
inline constexpr double MaximumBoundaryWidthErrorCm=.1;
inline bool Build(const FCurve& C,double AcrossCm,TArray<FVector2D>& Interior)
{
    Interior.Reset();
    if(!FMath::IsFinite(AcrossCm) || AcrossCm<=0. || C.D0<=0. || C.D1<=0.)return false;
    struct FInterval{double U,V;};
    TArray<FInterval,TInlineAllocator<32>> Stack;Stack.Add({0.,1.});
    while(!Stack.IsEmpty())
    {
        const FInterval I=Stack.Pop(EAllowShrinking::No);
        const double Du=C.D(I.U),Dv=C.D(I.V),Span=I.V-I.U;
        const double Strength=FMath::Abs(C.Delta*C.K);
        // Convex: exact error at the tangent intersection (the maximum of
        // either tangent's error on its piece). Concave: |f''| dx^2 / 8,
        // with the exact minimum denominator on this entire interval.
        const double Error=C.Convex()
            ? Strength*Span*Span/(2.*Du*Dv*(Du+Dv))
            : Strength*Span*Span/(4.*FMath::Pow(FMath::Min(Du,Dv),3.));
        if(!FMath::IsFinite(Error))return false;
        if(Error*AcrossCm>MaximumBoundaryWidthErrorCm)
        {
            const double Mid=(I.U+I.V)*.5;
            if(Mid<=I.U || Mid>=I.V)return false; // Not representable; never coarsen.
            Stack.Add({Mid,I.V});Stack.Add({I.U,Mid});continue;
        }
        if(C.Convex())
        {
            // Stable intersection, including near-linear curvature. Do not
            // subtract nearly equal tangent slopes or divide by curvature.
            Interior.Add(FVector2D((I.U*Dv+I.V*Du)/(Du+Dv),(C.H(I.U)+C.H(I.V))/(Du+Dv)));
        }
        else if(I.V<1.)Interior.Add(FVector2D(I.V,C.Value(I.V)));
    }
    double Previous=0.;
    for(const auto& P:Interior)
    {
        if(P.ContainsNaN() || P.X<=Previous || P.X>=1. || P.Y<0. || P.Y>1.)return false;
        Previous=P.X;
    }
    return true;
}
}
