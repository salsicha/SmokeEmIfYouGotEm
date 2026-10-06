#pragma once
#include "RaftSimHullContact.h"
#include "RaftSimHullArcClearance.h"
#include "RaftSimFlipHullBroadphase.h"

// Bed-connected authored block; identical indexed faces for rendering and the
// game's full deforming-hull CCD. No hidden sphere or animation-only obstacle.
namespace RaftSimFlipObstacle
{
inline double TopCm(double Xcm,bool bPinned=false,bool bPillow=false)
{return bPillow && !bPinned ? FMath::Lerp(-35.,110.,FMath::Clamp((Xcm+60.)/120.,0.,1.)) : (bPinned ? 150. : 55.);}
inline FVector TopNormal(bool bPillow=false,bool bPinned=false)
{return bPillow && !bPinned ? FVector(-145./120.,0,1).GetSafeNormal() : FVector::UpVector;}
inline FBox BoxCm(bool bPinned=false,bool bPillow=false){return FBox(FVector(-60,-120,bPinned && bPillow ? -400. : -200.),FVector(60,120,TopCm(60.,bPinned,bPillow)));}
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
    TConstArrayView<FIntVector> Faces,double SkinCm,double ClearanceCm,bool bPinned=false,bool bPillow=false,const FRaftSimHullArcPath* Arc=nullptr,bool bUseBroadphase=true)
{
    using namespace RaftSimSurfaceSweep;
    FResult Best;Best.Status=EStatus::Clear;Best.Time=1.;
    FBox Bounds(ForceInit);for(int32 I=0;I<A.Num();++I){Bounds+=A[I];Bounds+=B[I];}
    if(!Bounds.ExpandBy(SkinCm).Intersect(BoxCm(bPinned,bPillow)))return Best;
    TArray<FVector> V;TArray<FIntVector> GroundFaces;Geometry(V,GroundFaces,bPinned,bPillow);uint64 Pairs=0;
    TArray<int32> Candidates;
    if(bUseBroadphase)Candidates=RaftSimFlipHullBroadphase::Candidates(Arc,Faces,V,GroundFaces,SkinCm,ClearanceCm);
    else for(int32 I=0;I<Faces.Num();++I)Candidates.Add(I);
    for(int32 I:Candidates)
    {
        FTriangle Start,End,Velocity,Acceleration;FBox FaceBounds(ForceInit);
        for(int32 J=0;J<3;++J)
        {Start.V[J]=A[Faces[I][J]]*.01;End.V[J]=B[Faces[I][J]]*.01;FaceBounds+=A[Faces[I][J]];FaceBounds+=B[Faces[I][J]];}
        FaceBounds=FaceBounds.ExpandBy(SkinCm);if(!FaceBounds.Intersect(BoxCm(bPinned,bPillow)))continue;
        if(Arc)for(int32 J=0;J<3;++J)Arc->Derivatives(Faces[I][J],Velocity.V[J],Acceleration.V[J]);
        for(int32 K=0;K<GroundFaces.Num();++K)
        {
            const auto F=GroundFaces[K];const FTriangle Ground{{V[F.X]*.01,V[F.Y]*.01,V[F.Z]*.01}};
            FBox GB(ForceInit);GB+=V[F.X];GB+=V[F.Y];GB+=V[F.Z];if(!FaceBounds.Intersect(GB))continue;
            if(Arc)
            {
                const auto ClearAxis=[&](const FVector& N)
                {return RaftSimHullArcClearance::PlaneSeparated(Start,Velocity,Acceleration,Ground,N,Arc->Interval,Arc->JerkBound)
                    || RaftSimHullArcClearance::PlaneSeparated(Start,Velocity,Acceleration,Ground,-N,Arc->Interval,Arc->JerkBound);};
                bool Clear=ClearAxis(FVector::CrossProduct(Ground.V[1]-Ground.V[0],Ground.V[2]-Ground.V[0]))
                    || ClearAxis(FVector::CrossProduct(Start.V[1]-Start.V[0],Start.V[2]-Start.V[0]));
                for(int32 M=0;M<3 && !Clear;++M)for(int32 N=0;N<3 && !Clear;++N)
                    Clear=ClearAxis(FVector::CrossProduct(Start.V[(M+1)%3]-Start.V[M],Ground.V[(N+1)%3]-Ground.V[N]));
                // Only genuinely rigid source faces may use the inverse-frame
                // proof. A prescribed deformation never becomes a rigid proxy.
                if(!Clear && Arc->Before->VerticesM[Faces[I].X]==Arc->After->VerticesM[Faces[I].X]
                    && Arc->Before->VerticesM[Faces[I].Y]==Arc->After->VerticesM[Faces[I].Y]
                    && Arc->Before->VerticesM[Faces[I].Z]==Arc->After->VerticesM[Faces[I].Z])
                {
                    const auto SourceFace=Faces[I];
                    const FTriangle Local{{Arc->Before->VerticesM[SourceFace.X],Arc->Before->VerticesM[SourceFace.Y],Arc->Before->VerticesM[SourceFace.Z]}};
                    Clear=RaftSimHullArcClearance::RigidFaceSeparated(Local,Ground,Arc->State.Orientation,
                        Arc->State.Position,Arc->State.LinearVelocity,Arc->State.AngularVelocity,Arc->Interval);
                    for(int32 M=0;M<3 && !Clear;++M)for(int32 N=0;N<3 && !Clear;++N)
                        Clear=RaftSimHullArcClearance::RigidEdgeAxisSeparated(Local,Ground,Arc->State.Orientation,
                            Arc->State.Position,Arc->State.LinearVelocity,Arc->State.AngularVelocity,Arc->Interval,M,N);
                }
                if(Clear){++Pairs;continue;}
            }
            auto Hit=RaftSimSurfaceSweep::Sweep(Start,End,Ground,SkinCm*.01,128,ClearanceCm*.01);
            ++Pairs;Hit.MovingFace=I;Hit.GroundFace=K;
            if(Hit.Status==EStatus::Contact)
            {
                TArray<int32,TInlineAllocator<3>> Feature;
                for(int32 M=0;M<3;++M)if(Hit.Witness.GroundBary[M]>1.e-10)Feature.Add(M);
                if(Feature.Num()==1 || Feature.Num()==2)
                {
                    Hit.bHasGroundFeature=true;Hit.GroundFeatureA=Ground.V[Feature[0]];
                    Hit.GroundFeatureB=Ground.V[Feature.Last()];
                    const auto A0=Hit.GroundFeatureA,B0=Hit.GroundFeatureB;
                    if(A0.X>B0.X || (A0.X==B0.X && (A0.Y>B0.Y || (A0.Y==B0.Y && A0.Z>B0.Z))))
                        Swap(Hit.GroundFeatureA,Hit.GroundFeatureB);
                }
            }
            if(Hit.Status!=EStatus::Clear && Hit.Status!=EStatus::Contact){Hit.TrianglePairs=Pairs;return Hit;}
            if(Hit.Status==EStatus::Contact && (Best.Status==EStatus::Clear || Hit.Time<Best.Time))Best=Hit;
        }
    }
    Best.TrianglePairs=Pairs;return Best;
}
}
