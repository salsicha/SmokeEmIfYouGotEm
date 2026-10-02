#pragma once
#include "CoreMinimal.h"

// A witness may be removed only when BOTH deformation endpoint positions are
// a convex combination of retained witnesses on the same ground plane. Its
// position, deformation velocity and normal velocity then remain the same
// convex combination at every interpolated time and common rigid orientation.
// This is not spatial clustering, a proxy hull, or an increased contact cap.
namespace RaftSimContactWitnessPrune
{
struct FWitness
{
    FVector Before,After,Normal,Ground;
    int32 MovingFace=INDEX_NONE;
};
inline bool SamePlane(const FWitness& A,const FWitness& B,double Eps)
{
    return A.Normal.Equals(B.Normal,1.e-14) &&
        FMath::Abs(FVector::DotProduct(A.Ground-B.Ground,A.Normal))<=Eps;
}
inline bool Represented(const FWitness& P,const FWitness& A,const FWitness& B,double T,double Eps)
{
    return T>=0. && T<=1. && SamePlane(P,A,Eps) && SamePlane(P,B,Eps) &&
        P.Before.Equals(FMath::Lerp(A.Before,B.Before,T),Eps) &&
        P.After.Equals(FMath::Lerp(A.After,B.After,T),Eps);
}
template<typename Allocator>
bool Redundant(const FWitness& P,const TArray<FWitness,Allocator>& C,int32 Exclude,double Eps)
{
    for(int32 I=0;I<C.Num();++I)
    {
        if(I==Exclude || !SamePlane(P,C[I],Eps))continue;
        if(P.Before.Equals(C[I].Before,Eps) && P.After.Equals(C[I].After,Eps))return true;
        for(int32 J=I+1;J<C.Num();++J)
        {
            if(J==Exclude || !SamePlane(P,C[J],Eps))continue;
            const FVector D0=C[J].Before-C[I].Before,D1=C[J].After-C[I].After;
            const double Length=D0.SizeSquared()+D1.SizeSquared();
            if(Length<=1.e-24)continue;
            const double T=(FVector::DotProduct(P.Before-C[I].Before,D0)+
                FVector::DotProduct(P.After-C[I].After,D1))/Length;
            if(Represented(P,C[I],C[J],T,Eps))return true;
            // Interior witnesses on one source triangle have a 2-D affine
            // endpoint mapping even when its deformation is not rigid.
            if(P.MovingFace!=C[I].MovingFace || P.MovingFace!=C[J].MovingFace)continue;
            for(int32 K=J+1;K<C.Num();++K)
            {
                if(K==Exclude || C[K].MovingFace!=P.MovingFace || !SamePlane(P,C[K],Eps))continue;
                const FVector E0=C[K].Before-C[I].Before,E1=C[K].After-C[I].After;
                const double EE=E0.SizeSquared()+E1.SizeSquared(),DE=FVector::DotProduct(D0,E0)+FVector::DotProduct(D1,E1);
                const double Det=Length*EE-DE*DE;if(Det<=1.e-20)continue;
                const FVector P0=P.Before-C[I].Before,P1=P.After-C[I].After;
                const double PD=FVector::DotProduct(P0,D0)+FVector::DotProduct(P1,D1),PE=FVector::DotProduct(P0,E0)+FVector::DotProduct(P1,E1);
                const double U=(PD*EE-PE*DE)/Det,V=(PE*Length-PD*DE)/Det;
                if(U<0. || V<0. || U+V>1.)continue;
                if(P.Before.Equals(C[I].Before+U*D0+V*E0,Eps) && P.After.Equals(C[I].After+U*D1+V*E1,Eps))return true;
            }
        }
    }
    return false;
}
}
