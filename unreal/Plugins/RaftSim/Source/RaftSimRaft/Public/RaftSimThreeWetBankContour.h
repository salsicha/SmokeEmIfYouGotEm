#pragma once
#include "CoreMinimal.h"
#include "Math/VectorRegister.h"
#include <cmath>
#include <limits>

// Native candidate, deliberately not enabled by the normal shoreline builder
// until its construction cost, cache identity and rounded world mapping pass.
// Every inconclusive predicate fails closed; no negative-depth epsilon.
namespace RaftSimThreeWetBankContour
{
struct FScopedIEEE
{
    uint32 Previous=0;
    FScopedIEEE()
    {
#if PLATFORM_CPU_X86_FAMILY
        Previous=VectorGetControlRegister();
        VectorSetControlRegister(Previous & ~uint32(0x8040 | 0x6000)); // FTZ, DAZ, rounding mode.
#endif
    }
    ~FScopedIEEE()
    {
#if PLATFORM_CPU_X86_FAMILY
        VectorSetControlRegister(Previous);
#endif
    }
};
struct FBound
{
    double Lo=0.,Hi=0.;
    FBound()=default;
    explicit FBound(double V):Lo(V),Hi(V){}
    FBound(double L,double H):Lo(L),Hi(H){}
    bool Zero()const{return Lo==0. && Hi==0.;}
};
inline double Down(double X){return std::nextafter(X,-std::numeric_limits<double>::infinity());}
inline double Up(double X){return std::nextafter(X,std::numeric_limits<double>::infinity());}
inline FBound operator+(FBound A,FBound B)
{
    if(A.Zero())return B;if(B.Zero())return A;
    return {Down(A.Lo+B.Lo),Up(A.Hi+B.Hi)};
}
inline FBound operator-(FBound A){return {-A.Hi,-A.Lo};}
inline FBound operator-(FBound A,FBound B){return A+(-B);}
inline FBound operator*(FBound A,FBound B)
{
    if(A.Zero() || B.Zero())return FBound(0.);
    const double V[]={A.Lo*B.Lo,A.Lo*B.Hi,A.Hi*B.Lo,A.Hi*B.Hi};
    double L=V[0],H=V[0];for(int32 I=1;I<4;++I){L=FMath::Min(L,V[I]);H=FMath::Max(H,V[I]);}
    return {Down(L),Up(H)};
}
inline FBound DividePositive(FBound A,FBound B)
{
    if(B.Lo<=0.)return {-std::numeric_limits<double>::infinity(),std::numeric_limits<double>::infinity()};
    return A*FBound(Down(1./B.Hi),Up(1./B.Lo));
}
struct FPoint
{
    FVector2D XY;
    FBound X,Y;
    // Only original canonical edge roots and the exact dry origin may use
    // the analytic N=0 identity. No interior coefficient is clamped to zero.
    bool ExactZero=false;
    explicit FPoint(FVector2D P,bool Z=false):XY(P),X(P.X),Y(P.Y),ExactZero(Z){}
    FPoint(FVector2D P,FBound BX,FBound BY,bool Z=false):XY(P),X(BX),Y(BY),ExactZero(Z){}
};
inline bool SamePoint(const FPoint& A,const FPoint& B)
{
    return A.ExactZero==B.ExactZero && A.X.Lo==B.X.Lo && A.X.Hi==B.X.Hi && A.Y.Lo==B.Y.Lo && A.Y.Hi==B.Y.Hi;
}
inline FPoint Mid(const FPoint& A,const FPoint& B)
{
    if(SamePoint(A,B))return A;
    return FPoint((A.XY+B.XY)*.5,(A.X+B.X)*FBound(.5),(A.Y+B.Y)*FBound(.5));
}
struct FQuadratic{FBound C[6];};
struct FQuartic{FBound C[15];};
inline constexpr int32 Exponents[6][3]={{2,0,0},{0,2,0},{0,0,2},{1,1,0},{1,0,1},{0,1,1}};
inline int32 Index4(int32 A,int32 B){return A*5-A*(A-1)/2+B;}
inline FQuadratic Product(const FBound (&A)[3],const FBound (&B)[3])
{
    FQuadratic R;
    for(int32 I=0;I<3;++I)R.C[I]=A[I]*B[I];
    R.C[3]=A[0]*B[1]+A[1]*B[0];R.C[4]=A[0]*B[2]+A[2]*B[0];R.C[5]=A[1]*B[2]+A[2]*B[1];
    return R;
}
inline FQuartic Product(const FQuadratic& A,const FQuadratic& B)
{
    FQuartic R;
    for(int32 I=0;I<6;++I)for(int32 J=0;J<6;++J)
    {
        const int32 K=Index4(Exponents[I][0]+Exponents[J][0],Exponents[I][1]+Exponents[J][1]);
        R.C[K]=R.C[K]+A.C[I]*B.C[J];
    }
    return R;
}
struct FCurve
{
    double Bed[4]{},Depth[4]{};
    FBound Drop[4];
    FBound Roots[2];
    bool Valid=false;
    bool Init(const double (&B)[4],const double (&H)[4])
    {
        const FScopedIEEE FloatingPointScope;
        Valid=false;
        for(int32 I=0;I<4;++I)
        {
            if(!FMath::IsFinite(B[I]) || !FMath::IsFinite(H[I]))return false;
            Bed[I]=B[I];Depth[I]=H[I];Drop[I]=FBound(B[0])-FBound(B[I]);
            if(I && (H[I]<=0. || (Drop[I]-FBound(H[I])).Lo<=0.))return false;
        }
        Roots[0]=FBound(1.)-DividePositive(FBound(H[1]),Drop[1]);
        Roots[1]=FBound(1.)-DividePositive(FBound(H[2]),Drop[2]);
        Valid=H[0]==0.;return Valid;
    }
    FBound Value(const FPoint& P)const
    {
        if(P.ExactZero)return FBound(0.);
        // On an original edge use the factored root identity. This remains
        // informative a few representable steps onto the wet side without
        // subtracting nearly equal stage/bed products.
        if(P.Y.Zero())return P.X*Drop[1]*(P.X-Roots[0]);
        if(P.X.Zero())return P.Y*Drop[2]*(P.Y-Roots[1]);
        const FBound NX=FBound(1.)-P.X,NY=FBound(1.)-P.Y;
        const FBound W[]={NX*NY,P.X*NY,NX*P.Y,P.X*P.Y};
        FBound R;
        for(int32 I=1;I<4;++I)R=R+W[I]*(FBound(Depth[I])-W[0]*Drop[I]);
        return R;
    }
    FQuartic Coefficients(const FPoint& A,const FPoint& B,const FPoint& C)const
    {
        const FBound X[]={A.X,B.X,C.X},Y[]={A.Y,B.Y,C.Y};
        const FBound NX[]={FBound(1.)-X[0],FBound(1.)-X[1],FBound(1.)-X[2]};
        const FBound NY[]={FBound(1.)-Y[0],FBound(1.)-Y[1],FBound(1.)-Y[2]};
        const FQuadratic W[]={Product(NX,NY),Product(X,NY),Product(NX,Y),Product(X,Y)};
        FQuadratic Wet,Lower,One;
        for(int32 J=0;J<6;++J)
        {
            One.C[J]=FBound(J<3 ? 1. : 2.);
            for(int32 I=1;I<4;++I)
            {
                Wet.C[J]=Wet.C[J]+W[I].C[J]*FBound(Depth[I]);
                Lower.C[J]=Lower.C[J]+W[I].C[J]*Drop[I];
            }
        }
        FQuartic R=Product(Wet,One);const FQuartic L=Product(W[0],Lower);
        for(int32 I=0;I<15;++I)R.C[I]=R.C[I]-L.C[I];
        // Includes repeated endpoints in a segment represented as (P,Q,Q).
        // A monomial supported only on one point has the multinomial factor
        // times N at that point. Use its stable interval (or analytic zero),
        // not a cancellation-prone re-expansion of the same identity.
        const FBound VA=Value(A),VB=Value(B),VC=Value(C);
        R.C[Index4(4,0)]=VA;R.C[Index4(0,4)]=VB;R.C[Index4(0,0)]=VC;
        const bool AB=SamePoint(A,B),AC=SamePoint(A,C),BC=SamePoint(B,C);
        constexpr int32 Choose4[]={1,4,6,4,1},Factorial[]={1,1,2,6,24};
        if(AB && AC)for(int32 I=0;I<=4;++I)for(int32 J=0;J<=4-I;++J)
            R.C[Index4(I,J)]=VA*FBound(24./(Factorial[I]*Factorial[J]*Factorial[4-I-J]));
        else for(int32 I=0;I<=4;++I)
        {
            if(AB)R.C[Index4(I,4-I)]=VA*FBound(Choose4[I]);
            if(AC)R.C[Index4(I,0)]=VA*FBound(Choose4[I]);
            if(BC)R.C[Index4(0,I)]=VB*FBound(Choose4[I]);
        }
        return R;
    }
};
struct FStats
{
    int32 CoefficientTests=0,InitialSegments=0,RootSolves=0;
    int32 FailedStage=0;
    FVector2D FailedA=FVector2D::ZeroVector,FailedB=FVector2D::ZeroVector;
};
inline bool Certificate(const FCurve& C,const FPoint& A,const FPoint& B,const FPoint& D,
    bool Wet,FStats& Stats,int32 Remaining=9)
{
    if(++Stats.CoefficientTests>200000)return false; // Proof resource bound, never an acceptance tolerance.
    const FQuartic Q=C.Coefficients(A,B,D);
    bool Proven=true;
    for(const auto& V:Q.C)
    {
        if(!FMath::IsFinite(V.Lo) || !FMath::IsFinite(V.Hi))return false;
        Proven &= Wet ? V.Lo>=0. : V.Hi<=0.;
    }
    if(Proven)return true;
    for(int32 I:{Index4(4,0),Index4(0,4),Index4(0,0)})
        if(Wet ? Q.C[I].Hi<0. : Q.C[I].Lo>0.)return false;
    if(Remaining==0)return false;
    const FPoint AB=Mid(A,B),BD=Mid(B,D),DA=Mid(D,A);
    return Certificate(C,A,AB,DA,Wet,Stats,Remaining-1) &&
        Certificate(C,AB,B,BD,Wet,Stats,Remaining-1) &&
        Certificate(C,DA,BD,D,Wet,Stats,Remaining-1) &&
        Certificate(C,AB,BD,DA,Wet,Stats,Remaining-1);
}
inline FPoint IdealEdgeRoot(const FCurve& C,int32 Axis)
{
    const int32 Corner=Axis ? 2 : 1;
    const FBound R=C.Roots[Axis];
    const double V=1.-C.Depth[Corner]/(C.Bed[0]-C.Bed[Corner]);
    return Axis ? FPoint(FVector2D(0.,V),FBound(0.),R,true) : FPoint(FVector2D(V,0.),R,FBound(0.),true);
}
inline FPoint EdgeRoot(const FCurve& C,int32 Axis)
{
    const FPoint Ideal=IdealEdgeRoot(C,Axis);
    const double V=Up(Axis ? Ideal.Y.Hi : Ideal.X.Hi);
    // This policy must also be shared by adjacent cells at integration time.
    // The candidate's stored binary64 point itself is now proved wet, rather
    // than pretending that a rounded approximation is analytically zero.
    return FPoint(Axis ? FVector2D(0.,V) : FVector2D(V,0.));
}
inline FPoint Point(const FCurve& C,double T,double Width)
{
    if(T==0.)return EdgeRoot(C,0);if(T==1.)return EdgeRoot(C,1);
    const FVector2D Direction(1.-T,T),Ray=Direction/FMath::Max(Direction.X,Direction.Y);
    double Low=0.,High=1.;
    for(int32 I=0;I<56;++I)
    {
        const double M=(Low+High)*.5;
        const FBound V=C.Value(FPoint(Ray*M));
        if(V.Lo>=0.)High=M;else Low=M;
        // An ambiguous midpoint is only a search proposal, NOT certified dry.
        // High stays proved wet; whole wet/dry band tests below decide safety.
    }
    const FVector2D R=Ray*High;
    const double Advance=FMath::Min(Width*.5,FMath::Min((1.-R.X)/(2.*Direction.X),(1.-R.Y)/(2.*Direction.Y)));
    return FPoint(R+Direction*Advance);
}
inline FPoint Inner(const FPoint& P,double Width)
{
    // Leave an explicitly geometric machine-rounding reserve; final band
    // distance is itself interval checked against the unchanged width.
    const double StorageError=FMath::Max(FMath::Abs(P.X.Lo-P.XY.X),FMath::Abs(P.X.Hi-P.XY.X))+
        FMath::Max(FMath::Abs(P.Y.Lo-P.XY.Y),FMath::Abs(P.Y.Hi-P.XY.Y));
    const double W=FMath::Max(0.,Width-128.*std::numeric_limits<double>::epsilon()-2.*StorageError);
    const double Factor=FMath::Max(0.,1.-W/(P.XY.X+P.XY.Y));
    return FPoint(P.XY*Factor,Factor==0.);
}
inline FBound Cross(const FPoint& A,const FPoint& B,const FPoint& C)
{return (B.X-A.X)*(C.Y-A.Y)-(B.Y-A.Y)*(C.X-A.X);}
struct FResult
{
    TArray<FPoint> Boundary,InnerBoundary,Polygon;
    TArray<FIntVector> Triangles;
    FStats Stats;
};
// Store supplies the ACTUAL stored coordinates and enclosing inverse-map
// bounds. Certificates never silently switch back to ideal proposal points.
// RootWidth reserves part of the same geometric band for storage quantization.
template<typename FStore>
inline bool BuildStored(const FCurve& C,double Width,FResult& Out,const FStore& Store,
    double RootWidth,bool ReuseRoots=true)
{
    const FScopedIEEE FloatingPointScope;
#if !PLATFORM_CPU_X86_FAMILY
    return false; // Other floating-point control implementations are unverified.
#endif
    Out={};if(!C.Valid || !FMath::IsFinite(Width) || Width<=256.*std::numeric_limits<double>::epsilon() || Width>=1. ||
        !FMath::IsFinite(RootWidth) || RootWidth<0. || RootWidth>Width)return false;
    const FPoint Origin(FVector2D(0.,0.),true);
    const auto Interval=[&](const FPoint& P,const FPoint& Q)
    {
        const FPoint A=Inner(P,Width),B=Inner(Q,Width);
        // A storage policy can perturb ray ordering. Certify the partition,
        // not just depth signs on an accidentally reversed or overlapping span.
        if(!SamePoint(P,Q) && (Cross(Origin,P,Q).Lo<=0. || Cross(P,Q,B).Lo<0. || Cross(P,B,A).Lo<0.))return false;
        return Certificate(C,P,Q,Q,true,Out.Stats) && Certificate(C,Origin,A,B,false,Out.Stats);
    };
    const auto MakePoint=[&](double T){if(T>0. && T<1.)++Out.Stats.RootSolves;return Store(Point(C,T,RootWidth),T);};
    struct FSpan{double A,B;int32 Level;FPoint P,Q;};TArray<FSpan,TInlineAllocator<32>> Stack;
    const FPoint First=MakePoint(0.),Last=MakePoint(1.);Stack.Add({0.,1.,0,First,Last});
    Out.Boundary.Add(First);
    while(!Stack.IsEmpty())
    {
        const FSpan S=Stack.Pop(EAllowShrinking::No);
        const FPoint P=ReuseRoots ? S.P : MakePoint(S.A),Q=ReuseRoots ? S.Q : MakePoint(S.B);
        if(Interval(P,Q)){if(!SamePoint(Out.Boundary.Last(),Q))Out.Boundary.Add(Q);continue;}
        if(S.Level>=16 || Out.Stats.CoefficientTests>200000)
        {Out.Stats.FailedStage=1;Out.Stats.FailedA=P.XY;Out.Stats.FailedB=Q.XY;return false;}
        const double M=(S.A+S.B)*.5;
        const FPoint Middle=ReuseRoots ? MakePoint(M) : FPoint(FVector2D::ZeroVector);
        Stack.Add({M,S.B,S.Level+1,Middle,Q});Stack.Add({S.A,M,S.Level+1,P,Middle});
    }
    Out.Stats.InitialSegments=Out.Boundary.Num()-1;
    for(int32 I=1;I<Out.Boundary.Num()-1;)
    {
        if(Interval(Out.Boundary[I-1],Out.Boundary[I+1])){Out.Boundary.RemoveAt(I,1,EAllowShrinking::No);I=FMath::Max(1,I-1);}
        else ++I;
        if(Out.Stats.CoefficientTests>200000)return false;
    }
    for(const auto& P:Out.Boundary)
    {
        if(P.X.Lo<0. || P.X.Hi>1. || P.Y.Lo<0. || P.Y.Hi>1.)return false;
        const FPoint Q=Inner(P,Width);
        const FBound DX=P.X-Q.X,DY=P.Y-Q.Y;
        const double Bound=Up(FMath::Max(FMath::Abs(DX.Lo),FMath::Abs(DX.Hi))+FMath::Max(FMath::Abs(DY.Lo),FMath::Abs(DY.Hi)));
        if(Bound>Width){Out.Stats.FailedStage=2;Out.Stats.FailedA=P.XY;Out.Stats.FailedB=Q.XY;return false;}
        Out.InnerBoundary.Add(Q);
    }
    Out.Polygon.Add(Store(FPoint(FVector2D(1.,1.)),-1.));Out.Polygon.Add(Store(FPoint(FVector2D(1.,0.)),-1.));
    Out.Polygon.Append(Out.Boundary);Out.Polygon.Add(Store(FPoint(FVector2D(0.,1.)),-1.));
    TArray<int32> Live;for(int32 I=0;I<Out.Polygon.Num();++I)Live.Add(I);
    while(Live.Num()>3)
    {
        bool Found=false;
        for(int32 I=0;I<Live.Num() && !Found;++I)
        {
            const int32 Before=(I+Live.Num()-1)%Live.Num(),After=(I+1)%Live.Num();
            const auto& A=Out.Polygon[Live[Before]];const auto& B=Out.Polygon[Live[I]];const auto& D=Out.Polygon[Live[After]];
            if(Cross(A,B,D).Hi>=0.)continue;
            bool Contains=false;
            for(int32 J=0;J<Live.Num() && !Contains;++J)if(J!=Before && J!=I && J!=After)
            {
                const auto& P=Out.Polygon[Live[J]];
                Contains=Cross(A,B,P).Lo<=0. && Cross(B,D,P).Lo<=0. && Cross(D,A,P).Lo<=0.;
            }
            if(Contains || !Certificate(C,A,B,D,true,Out.Stats))continue;
            Out.Triangles.Add(FIntVector(Live[Before],Live[I],Live[After]));Live.RemoveAt(I,1,EAllowShrinking::No);Found=true;
        }
        if(!Found){Out.Stats.FailedStage=3;return false;}
    }
    if(!Certificate(C,Out.Polygon[Live[0]],Out.Polygon[Live[1]],Out.Polygon[Live[2]],true,Out.Stats))return false;
    Out.Triangles.Add(FIntVector(Live[0],Live[1],Live[2]));return true;
}
inline bool Build(const FCurve& C,double Width,FResult& Out,bool ReuseRoots=true)
{
    return BuildStored(C,Width,Out,[](const FPoint& P,double){return P;},Width,ReuseRoots);
}
}
