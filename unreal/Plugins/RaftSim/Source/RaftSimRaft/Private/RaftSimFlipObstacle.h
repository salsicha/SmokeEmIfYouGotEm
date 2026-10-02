#pragma once
#include "RaftSimHullContact.h"

// Bed-connected authored block; identical indexed faces for rendering and the
// game's full deforming-hull CCD. No hidden sphere or animation-only obstacle.
namespace RaftSimFlipObstacle
{
inline double TopCm(double Xcm,bool bPinned=false,bool bPillow=false)
{return bPillow ? FMath::Lerp(-35.,110.,FMath::Clamp((Xcm+60.)/120.,0.,1.)) : (bPinned ? 150. : 55.);}
inline FVector TopNormal(bool bPillow=false)
{return bPillow ? FVector(-145./120.,0,1).GetSafeNormal() : FVector::UpVector;}
inline FBox BoxCm(bool bPinned=false,bool bPillow=false){return FBox(FVector(-60,-120,-200),FVector(60,120,TopCm(60.,bPinned,bPillow)));}
inline void Geometry(TArray<FVector>& V,TArray<FIntVector>& Faces,bool bPinned=false,bool bPillow=false)
{
    const FBox Box=BoxCm(bPinned,bPillow);V.Reset();Faces.Reset();
    for(int32 I=0;I<8;++I)
    {const double X=I&1?Box.Max.X:Box.Min.X;V.Add(FVector(X,I&2?Box.Max.Y:Box.Min.Y,I&4?TopCm(X,bPinned,bPillow):Box.Min.Z));}
    Faces={FIntVector(0,2,1),FIntVector(1,2,3),FIntVector(4,5,6),FIntVector(5,7,6),
        FIntVector(0,1,4),FIntVector(1,5,4),FIntVector(2,6,3),FIntVector(3,6,7),
        FIntVector(0,4,2),FIntVector(2,4,6),FIntVector(1,3,5),FIntVector(3,7,5)};
}
inline RaftSimSurfaceSweep::FResult Sweep(TConstArrayView<FVector> A,TConstArrayView<FVector> B,
    TConstArrayView<FIntVector> Faces,double SkinCm,double ClearanceCm,bool bPinned=false,bool bPillow=false)
{
    using namespace RaftSimSurfaceSweep;
    FResult Best;Best.Status=EStatus::Clear;Best.Time=1.;
    FBox Bounds(ForceInit);for(int32 I=0;I<A.Num();++I){Bounds+=A[I];Bounds+=B[I];}
    if(!Bounds.ExpandBy(SkinCm).Intersect(BoxCm(bPinned,bPillow)))return Best;
    TArray<FVector> V;TArray<FIntVector> GroundFaces;Geometry(V,GroundFaces,bPinned,bPillow);uint64 Pairs=0;
    for(int32 I=0;I<Faces.Num();++I)
    {
        FTriangle Start,End;FBox FaceBounds(ForceInit);
        for(int32 J=0;J<3;++J)
        {Start.V[J]=A[Faces[I][J]]*.01;End.V[J]=B[Faces[I][J]]*.01;FaceBounds+=A[Faces[I][J]];FaceBounds+=B[Faces[I][J]];}
        FaceBounds=FaceBounds.ExpandBy(SkinCm);if(!FaceBounds.Intersect(BoxCm(bPinned,bPillow)))continue;
        for(int32 K=0;K<GroundFaces.Num();++K)
        {
            const auto F=GroundFaces[K];const FTriangle Ground{{V[F.X]*.01,V[F.Y]*.01,V[F.Z]*.01}};
            FBox GB(ForceInit);GB+=V[F.X];GB+=V[F.Y];GB+=V[F.Z];if(!FaceBounds.Intersect(GB))continue;
            auto Hit=RaftSimSurfaceSweep::Sweep(Start,End,Ground,SkinCm*.01,128,ClearanceCm*.01);
            ++Pairs;Hit.MovingFace=I;Hit.GroundFace=K;
            if(Hit.Status!=EStatus::Clear && Hit.Status!=EStatus::Contact){Hit.TrianglePairs=Pairs;return Hit;}
            if(Hit.Status==EStatus::Contact && (Best.Status==EStatus::Clear || Hit.Time<Best.Time))Best=Hit;
        }
    }
    Best.TrianglePairs=Pairs;return Best;
}
}
