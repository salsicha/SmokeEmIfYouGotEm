#pragma once
#include "RaftSimHullArcClearance.h"
#include "RaftSimHullContact.h"

// Shared production/lab proof. Original indexed face and full curved path;
// never a proxy, enlarged obstacle, relaxed clearance or prescribed rotation.
namespace RaftSimHullArcPair
{
inline bool Separated(const FIntVector& Face,const RaftSimSurfaceSweep::FTriangle& Start,
    const RaftSimSurfaceSweep::FTriangle& Ground,const FRaftSimHullArcPath& Arc)
{
    using namespace RaftSimHullArcClearance;
    RaftSimSurfaceSweep::FTriangle Velocity,Acceleration;
    for(int32 J=0;J<3;++J)Arc.Derivatives(Face[J],Velocity.V[J],Acceleration.V[J]);
    const auto Axis=[&](const FVector& N)
    {return PlaneSeparated(Start,Velocity,Acceleration,Ground,N,Arc.Interval,Arc.JerkBound)
        || PlaneSeparated(Start,Velocity,Acceleration,Ground,-N,Arc.Interval,Arc.JerkBound);};
    bool Clear=Axis(FVector::CrossProduct(Ground.V[1]-Ground.V[0],Ground.V[2]-Ground.V[0]))
        || Axis(FVector::CrossProduct(Start.V[1]-Start.V[0],Start.V[2]-Start.V[0]));
    for(int32 M=0;M<3 && !Clear;++M)for(int32 N=0;N<3 && !Clear;++N)
        Clear=Axis(FVector::CrossProduct(Start.V[(M+1)%3]-Start.V[M],Ground.V[(N+1)%3]-Ground.V[N]));
    if(!Clear && Arc.Before->VerticesM[Face.X]==Arc.After->VerticesM[Face.X]
        && Arc.Before->VerticesM[Face.Y]==Arc.After->VerticesM[Face.Y]
        && Arc.Before->VerticesM[Face.Z]==Arc.After->VerticesM[Face.Z])
    {
        const RaftSimSurfaceSweep::FTriangle Local{{Arc.Before->VerticesM[Face.X],Arc.Before->VerticesM[Face.Y],Arc.Before->VerticesM[Face.Z]}};
        Clear=RigidFaceSeparated(Local,Ground,Arc.State.Orientation,Arc.State.Position,
            Arc.State.LinearVelocity,Arc.State.AngularVelocity,Arc.Interval);
        for(int32 M=0;M<3 && !Clear;++M)for(int32 N=0;N<3 && !Clear;++N)
            Clear=RigidEdgeAxisSeparated(Local,Ground,Arc.State.Orientation,Arc.State.Position,
                Arc.State.LinearVelocity,Arc.State.AngularVelocity,Arc.Interval,M,N);
    }
    return Clear;
}
inline void GroundFeature(RaftSimSurfaceSweep::FResult& Hit,const RaftSimSurfaceSweep::FTriangle& Ground)
{
    if(Hit.Status!=RaftSimSurfaceSweep::EStatus::Contact)return;
    TArray<int32,TInlineAllocator<3>> Feature;
    for(int32 I=0;I<3;++I)if(Hit.Witness.GroundBary[I]>1.e-10)Feature.Add(I);
    if(Feature.Num()!=1 && Feature.Num()!=2)return;
    Hit.bHasGroundFeature=true;Hit.GroundFeatureA=Ground.V[Feature[0]];Hit.GroundFeatureB=Ground.V[Feature.Last()];
    const auto A=Hit.GroundFeatureA,B=Hit.GroundFeatureB;
    if(A.X>B.X || (A.X==B.X && (A.Y>B.Y || (A.Y==B.Y && A.Z>B.Z))))Swap(Hit.GroundFeatureA,Hit.GroundFeatureB);
}
}
