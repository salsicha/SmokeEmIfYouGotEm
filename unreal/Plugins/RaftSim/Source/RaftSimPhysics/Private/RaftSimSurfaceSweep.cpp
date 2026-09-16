#include "RaftSimSurfaceSweep.h"

namespace RaftSimSurfaceSweep
{
namespace
{
FVector UnitBary(int32 I){FVector B=FVector::ZeroVector;B[I]=1.;return B;}
FVector Point(const FTriangle& T,const FVector& B){return T.V[0]*B.X+T.V[1]*B.Y+T.V[2]*B.Z;}
bool Finite(const FTriangle& T)
{return !T.V[0].ContainsNaN() && !T.V[1].ContainsNaN() && !T.V[2].ContainsNaN();}
// Projection is interior only when all barycentric coordinates are nonnegative.
// Exterior closest points are found separately on all three closed edges.
bool FaceBary(const FVector& P,const FTriangle& T,FVector& B)
{
    const FVector U=T.V[1]-T.V[0],V=T.V[2]-T.V[0],W=P-T.V[0];
    const FVector N=FVector::CrossProduct(U,V);const double D=N.SizeSquared();
    if(D==0.)return false;
    B.Y=FVector::DotProduct(FVector::CrossProduct(W,V),N)/D;
    B.Z=FVector::DotProduct(FVector::CrossProduct(U,W),N)/D;
    B.X=1.-B.Y-B.Z;
    return B.X>=0. && B.Y>=0. && B.Z>=0.;
}
}

FDistance Distance(const FTriangle& A,const FTriangle& B)
{
    FDistance Best;
    if(!Finite(A) || !Finite(B))return Best;
    const auto Accept=[&](const FVector& BA,const FVector& BB)
    {
        const FVector PA=Point(A,BA),PB=Point(B,BB);
        const double D=(PA-PB).SizeSquared();
        if(D<Best.Squared){Best={D,PA,PB,BA,BB};}
    };
    for(int32 I=0;I<3;++I)
    {
        FVector Bary;
        if(FaceBary(A.V[I],B,Bary))Accept(UnitBary(I),Bary);
        if(FaceBary(B.V[I],A,Bary))Accept(Bary,UnitBary(I));
        const int32 J=(I+1)%3;
        const FVector U=A.V[J]-A.V[I];const double UU=U.SizeSquared();
        for(int32 K=0;K<3;++K)
        {
            const int32 L=(K+1)%3;
            const FVector V=B.V[L]-B.V[K],W=B.V[K]-A.V[I];
            const double VV=V.SizeSquared();
            // Four endpoint/edge candidates also cover parallel and degenerate
            // segments. Cross-product denominator avoids subtracting nearly
            // equal squared lengths in the interior/interior solve.
            for(int32 Endpoint=0;Endpoint<2;++Endpoint)
            {
                const double S=double(Endpoint);
                const double T=VV>0.?FMath::Clamp(FVector::DotProduct(U*S-W,V)/VV,0.,1.):0.;
                Accept(UnitBary(I)*(1.-S)+UnitBary(J)*S,UnitBary(K)*(1.-T)+UnitBary(L)*T);
                const double TB=double(Endpoint);
                const double SA=UU>0.?FMath::Clamp(FVector::DotProduct(W+V*TB,U)/UU,0.,1.):0.;
                Accept(UnitBary(I)*(1.-SA)+UnitBary(J)*SA,UnitBary(K)*(1.-TB)+UnitBary(L)*TB);
            }
            const FVector Cross=FVector::CrossProduct(U,V);const double Den=Cross.SizeSquared();
            if(Den>0.)
            {
                const double S=FVector::DotProduct(FVector::CrossProduct(W,V),Cross)/Den;
                const double T=FVector::DotProduct(FVector::CrossProduct(W,U),Cross)/Den;
                if(S>=0. && S<=1. && T>=0. && T<=1.)
                    Accept(UnitBary(I)*(1.-S)+UnitBary(J)*S,UnitBary(K)*(1.-T)+UnitBary(L)*T);
            }
        }
        // A triangle edge can pierce the other face with no vertex on it and
        // no edge/edge intersection. Test both directions explicitly.
        for(int32 Reverse=0;Reverse<2;++Reverse)
        {
            const auto& Edge=Reverse?B:A;const auto& Face=Reverse?A:B;
            const FVector N=FVector::CrossProduct(Face.V[1]-Face.V[0],Face.V[2]-Face.V[0]);
            const FVector Delta=Edge.V[J]-Edge.V[I];
            const double Den=FVector::DotProduct(Delta,N);
            if(Den==0.)continue;
            const double T=FVector::DotProduct(Face.V[0]-Edge.V[I],N)/Den;
            if(T<0. || T>1.)continue;
            FVector FB;
            if(!FaceBary(Edge.V[I]+Delta*T,Face,FB))continue;
            const FVector EB=UnitBary(I)*(1.-T)+UnitBary(J)*T;
            if(Reverse)Accept(FB,EB);else Accept(EB,FB);
        }
    }
    return Best;
}

FResult Sweep(const FTriangle& Start,const FTriangle& End,const FTriangle& Ground,
    double SkinM,int32 MaximumIterations)
{
    FResult R;
    constexpr double DistanceRoundoffM=1.e-10;
    if(!Finite(Start) || !Finite(End) || !Finite(Ground) ||
        !FMath::IsFinite(SkinM) || SkinM<=DistanceRoundoffM || MaximumIterations<=0)return R;
    FVector Motion[3];for(int32 I=0;I<3;++I)Motion[I]=End.V[I]-Start.V[I];
    for(int32 Iteration=0;Iteration<MaximumIterations;++Iteration)
    {
        R.Iterations=Iteration+1;
        FTriangle Current;
        for(int32 I=0;I<3;++I)Current.V[I]=Start.V[I]+Motion[I]*R.Time;
        R.Witness=Distance(Current,Ground);
        const double D=FMath::Sqrt(R.Witness.Squared);
        if(!FMath::IsFinite(D) || R.Witness.Squared==DBL_MAX)return R;
        if(D<=DistanceRoundoffM)
        {R.Status=R.Time==0.?EStatus::InitialIntersection:EStatus::Unresolved;return R;}
        R.Normal=(R.Witness.MovingPoint-R.Witness.GroundPoint)/D;
        if(R.Time==1. && D>SkinM+DistanceRoundoffM){R.Status=EStatus::Clear;return R;}
        // A closest-feature separating plane bounds EVERY moving vertex.
        // Its gap can close no faster than the fastest projected vertex.
        // Unlike time sampling, a fast crossing cannot skip this bound.
        const FVector Origin=Ground.V[0];
        double Gap=-DBL_MAX;
        FVector Axis=R.Normal;
        const auto ConsiderAxis=[&](FVector Candidate)
        {
            const double Length=Candidate.Length();if(Length==0.)return;
            Candidate/=Length;
            double AMin=DBL_MAX,AMax=-DBL_MAX,BMin=DBL_MAX,BMax=-DBL_MAX;
            for(int32 I=0;I<3;++I)
            {
                const double A=FVector::DotProduct(Current.V[I]-Origin,Candidate);
                const double B=FVector::DotProduct(Ground.V[I]-Origin,Candidate);
                AMin=FMath::Min(AMin,A);AMax=FMath::Max(AMax,A);
                BMin=FMath::Min(BMin,B);BMax=FMath::Max(BMax,B);
            }
            if(AMin-BMax>Gap){Gap=AMin-BMax;Axis=Candidate;}
            if(BMin-AMax>Gap){Gap=BMin-AMax;Axis=-Candidate;}
        };
        ConsiderAxis(R.Normal);
        const FVector AN=FVector::CrossProduct(Current.V[1]-Current.V[0],Current.V[2]-Current.V[0]);
        const FVector BN=FVector::CrossProduct(Ground.V[1]-Ground.V[0],Ground.V[2]-Ground.V[0]);
        ConsiderAxis(AN);ConsiderAxis(BN);
        for(int32 I=0;I<3;++I)
        {
            const FVector AE=Current.V[(I+1)%3]-Current.V[I],BE=Ground.V[(I+1)%3]-Ground.V[I];
            ConsiderAxis(FVector::CrossProduct(AN,AE));ConsiderAxis(FVector::CrossProduct(BN,BE));
            for(int32 J=0;J<3;++J)ConsiderAxis(FVector::CrossProduct(AE,Ground.V[(J+1)%3]-Ground.V[J]));
        }
        // Witness subtraction loses angular precision as clearance approaches
        // the skin, especially beside large ground triangles. Exact source
        // face/edge axes provide independently evaluated separating planes;
        // never turn a cancellation-damaged witness plane into a clear result.
        R.Normal=Axis;
        if(D<=SkinM+DistanceRoundoffM){R.Status=EStatus::Contact;return R;}
        double Closing=0.;
        for(int32 I=0;I<3;++I)Closing=FMath::Max(Closing,-FVector::DotProduct(Motion[I],Axis));
        if(Gap<=SkinM){R.Status=EStatus::Unresolved;return R;}
        if(Closing==0.){R.Status=EStatus::Clear;return R;}
        const double Advance=.9*(Gap-SkinM)/Closing;
        const double Next=FMath::Min(1.,R.Time+Advance);
        if(Next<=R.Time){R.Status=EStatus::Unresolved;return R;}
        R.Time=Next;
    }
    // Exhaustion is NOT a clear sweep. Callers must refuse or refine the step.
    R.Status=EStatus::Unresolved;return R;
}
}
