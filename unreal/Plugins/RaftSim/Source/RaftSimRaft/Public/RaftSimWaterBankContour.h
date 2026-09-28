#pragma once
#include "CoreMinimal.h"

namespace RaftSimWaterBankContour
{
// A high, exactly dry corner bordered by three positive-depth donors has a
// curved shoreline even though its four source positions form a square. This
// specialization does not reinterpret dry films or connect diagonal channels.
inline bool Eligible(const double (&B)[4],const double (&H)[4],int32 Dry)
{
    if(Dry<0 || Dry>3 || H[Dry]!=0.)return false;
    for(int32 I=0;I<4;++I)if(I!=Dry && (H[I]<=0. || B[Dry]<=B[I]+H[I]))return false;
    return true;
}
inline double SignedDepth(const double (&B)[4],const double (&H)[4],const FVector2D& P)
{
    const double W[4]={(1.-P.X)*(1.-P.Y),P.X*(1.-P.Y),(1.-P.X)*P.Y,P.X*P.Y};
    double Bed=0.,Stage=0.,Weight=0.;
    for(int32 I=0;I<4;++I)
    {
        Bed+=W[I]*B[I];
        if(H[I]>0.){Weight+=W[I];Stage+=W[I]*(B[I]+H[I]);}
    }
    return Weight>0. ? Stage/Weight-Bed : -1.;
}
// Endpoints are the canonical shared-edge intersections. Each intermediate
// ray starts at the dry corner and ends on an opposite (entirely wet) edge.
// Keep the root at zero depth, not the gameplay wet threshold or a depth floor.
inline FVector2D Point(const double (&B)[4],const double (&H)[4],int32 Dry,
    const FVector2D& A,const FVector2D& C,double Fraction)
{
    const FVector2D Origin(Dry%2,Dry/2);
    const FVector2D Direction=FMath::Lerp(A,C,Fraction)-Origin;
    const double Extent=FMath::Max(FMath::Abs(Direction.X),FMath::Abs(Direction.Y));
    if(Extent<=0.)return Origin;
    const FVector2D Ray=Direction/Extent;
    // Cancel the removable dry-corner factor t. The radial depth numerator
    // is then a cubic; evaluating it avoids four donor reconstructions on
    // every root iteration. Safeguarded Newton accelerates ordinary banks;
    // the same 36 bisections remain the fallback, not a looser geometry gate.
    const double X=FMath::Abs(Ray.X),Y=FMath::Abs(Ray.Y),S=X+Y,Q=X*Y;
    const int32 IX=Dry^1,IY=Dry^2,IO=Dry^3;
    const double E0=X*(B[IX]+H[IX])+Y*(B[IY]+H[IY]);
    const double E1=Q*(B[IO]+H[IO]-B[IX]-H[IX]-B[IY]-H[IY]);
    const double L=X*(B[IX]-B[Dry])+Y*(B[IY]-B[Dry]);
    const double M=Q*(B[Dry]-B[IX]-B[IY]+B[IO]);
    const double C0=E0-S*B[Dry],C1=E1-S*L+Q*B[Dry],C2=Q*L-S*M,C3=Q*M;
    const auto Value=[&](double T){return ((C3*T+C2)*T+C1)*T+C0;};
    double Low=0.,High=1.,T=.5;
    for(int32 I=0;I<8;++I)
    {
        const double F=Value(T);
        if(F==0.)return Origin+Ray*T;
        if(F>0.)High=T;else Low=T;
        const double Derivative=(3.*C3*T+2.*C2)*T+C1;
        const double Next=Derivative!=0. ? T-F/Derivative : -1.;
        if(FMath::IsFinite(Next) && Next>=Low && Next<=High)
        {
            if(FMath::Abs(Next-T)<=1.e-12)return Origin+Ray*Next;
            T=Next;
        }
        else T=(Low+High)*.5;
    }
    for(int32 I=0;I<36;++I)
    {
        const double Mid=(Low+High)*.5;
        if(Value(Mid)>0.)High=Mid;else Low=Mid;
    }
    return Origin+Ray*((Low+High)*.5);
}
}
