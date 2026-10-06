#pragma once

#include "RaftSimWaterFeatureKinematics.h"
#include "RaftSimHullContact.h"

// One bed-connected box owns rendering, dry water, foam exclusion and contact.
// Authored streamfunction around a solid boundary, not a solved wake/CFD model.
namespace RaftSimEddyDemoBoundary
{
constexpr double HalfLengthM=2.,HalfWidthM=4.,BedM=-1.8,TopM=1.7;
inline FBox BoxCm(){return FBox(FVector(-200,-400,BedM*100.),FVector(200,400,TopM*100.));}
inline bool Solid(const FVector& P)
{return FMath::Abs(P.X)<=HalfLengthM*100. && FMath::Abs(P.Y)<=HalfWidthM*100.;}
inline bool OverlapsFootprint(const FBox2D& B)
{return B.Max.X>-200. && B.Min.X<200. && B.Max.Y>-400. && B.Min.Y<400.;}

inline double WakePsi(double X,double Y)
{
    // One antisymmetric wake streamfunction, rather than two disjoint
    // ellipses whose zero-support seam left +U through-flow at Y=0.
    // The inner branch returns upstream; its upstream end turns outward,
    // and the outer branch runs downstream. The exact symmetry axis is a
    // separatrix: no invented lateral kick chooses a side for a boat.
    return RaftSimWaterFeatureKinematics::EddyWakePsi(X,Y,HalfWidthM,2.);
}
inline FVector WakeDelta(double X,double Y)
{
    return RaftSimWaterFeatureKinematics::EddyDelta(X,Y,HalfWidthM,2.);
}

inline FVector Velocity(const FVector& P)
{
    if(Solid(P))return FVector::ZeroVector;
    const double X=P.X*.01,Y=P.Y*.01;
    const double Dx=FMath::Max(FMath::Abs(X)-HalfLengthM,0.);
    const double Dy=FMath::Max(FMath::Abs(Y)-HalfWidthM,0.);
    const double D=FMath::Sqrt(Dx*Dx+Dy*Dy),S=FMath::Clamp(D/4.,0.,1.);
    // psi = (U*y + psi_wake)*quintic(distance/4 m). Its first derivatives
    // vanish at the box, preventing normal flux on every face and corner.
    const double F=S*S*S*(10.-15.*S+6.*S*S);
    const double DF=30.*S*S*(1.-S)*(1.-S)/4.;
    const double Gx=FMath::Sign(X)*Dx/D,Gy=FMath::Sign(Y)*Dy/D;
    const double Psi=2.*Y+WakePsi(X,Y);
    const FVector Free=FVector(2,0,0)+WakeDelta(X,Y);
    return FVector(Free.X*F+Psi*DF*Gy,Free.Y*F-Psi*DF*Gx,0.);
}

inline bool SegmentEntersSolid(const FVector& A,const FVector& B)
{
    double Lo=0.,Hi=1.;
    for(int32 Axis=0;Axis<2;++Axis)
    {
        const double Half=Axis==0 ? 200. : 400.,Delta=B[Axis]-A[Axis];
        if(FMath::Abs(Delta)<1.e-12){if(FMath::Abs(A[Axis])>Half)return false;continue;}
        double T0=(-Half-A[Axis])/Delta,T1=(Half-A[Axis])/Delta;
        if(T0>T1)Swap(T0,T1);
        Lo=FMath::Max(Lo,T0);Hi=FMath::Min(Hi,T1);
        if(Lo>Hi)return false;
    }
    return Lo<=Hi;
}

inline bool Advect(FVector& P,double Dt)
{
    const FVector Mid=P+Velocity(P)*(50.*Dt);
    const FVector Next=P+Velocity(Mid)*(100.*Dt);
    if(Solid(Mid) || Solid(Next) || SegmentEntersSolid(P,Next))return false;
    P=Next;return true;
}

inline void BoxGeometry(TArray<FVector>& V,TArray<FIntVector>& Faces)
{
    const FBox Box=BoxCm();V.Reset();Faces.Reset();
    for(int32 I=0;I<8;++I)V.Add(FVector(I&1?Box.Max.X:Box.Min.X,I&2?Box.Max.Y:Box.Min.Y,I&4?Box.Max.Z:Box.Min.Z));
    Faces={FIntVector(0,2,1),FIntVector(1,2,3),FIntVector(4,5,6),FIntVector(5,7,6),
        FIntVector(0,1,4),FIntVector(1,5,4),FIntVector(2,6,3),FIntVector(3,6,7),
        FIntVector(0,4,2),FIntVector(2,4,6),FIntVector(1,3,5),FIntVector(3,7,5)};
}

inline RaftSimSurfaceSweep::FResult Sweep(TConstArrayView<FVector> A,TConstArrayView<FVector> B,
    TConstArrayView<FIntVector> Faces,double SkinCm,double ClearanceCm)
{
    using namespace RaftSimSurfaceSweep;
    FResult Best;Best.Status=EStatus::Clear;Best.Time=1.;
    FBox Bounds(ForceInit);for(int32 I=0;I<A.Num();++I){Bounds+=A[I];Bounds+=B[I];}
    if(!Bounds.ExpandBy(SkinCm).Intersect(BoxCm()))return Best;
    TArray<FVector> V;TArray<FIntVector> BoxFaces;BoxGeometry(V,BoxFaces);
    uint64 Pairs=0;
    for(int32 I=0;I<Faces.Num();++I)
    {
        FTriangle Start,End;FBox FaceBounds(ForceInit);
        for(int32 J=0;J<3;++J)
        {Start.V[J]=A[Faces[I][J]]*.01;End.V[J]=B[Faces[I][J]]*.01;FaceBounds+=A[Faces[I][J]];FaceBounds+=B[Faces[I][J]];}
        FaceBounds=FaceBounds.ExpandBy(SkinCm);
        if(!FaceBounds.Intersect(BoxCm()))continue;
        for(int32 K=0;K<BoxFaces.Num();++K)
        {
            const auto& F=BoxFaces[K];const FTriangle Ground{{V[F.X]*.01,V[F.Y]*.01,V[F.Z]*.01}};
            FBox GroundBounds(ForceInit);GroundBounds+=V[F.X];GroundBounds+=V[F.Y];GroundBounds+=V[F.Z];
            if(!FaceBounds.Intersect(GroundBounds))continue;
            auto Hit=RaftSimSurfaceSweep::Sweep(Start,End,Ground,SkinCm*.01,128,ClearanceCm*.01);
            ++Pairs;Hit.MovingFace=I;Hit.GroundFace=K;
            if(Hit.Status!=EStatus::Clear && Hit.Status!=EStatus::Contact){Hit.TrianglePairs=Pairs;return Hit;}
            if(Hit.Status==EStatus::Contact && (Best.Status==EStatus::Clear || Hit.Time<Best.Time))Best=Hit;
        }
    }
    Best.TrianglePairs=Pairs;return Best;
}
}
