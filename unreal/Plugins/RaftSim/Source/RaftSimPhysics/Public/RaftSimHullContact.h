#pragma once
#include "RaftSimHullGeometry.h"
#include "RaftSimSurfaceSweep.h"
#include "RaftSimSweptGroundContact.h"

using FRaftSimHullGroundQuery=TFunction<RaftSimSurfaceSweep::FResult(
    TConstArrayView<FVector>,TConstArrayView<FVector>,TConstArrayView<FIntVector>,double,double)>;

struct FRaftSimHullArcPath
{
    FRaftSimFlexRigidState State;
    const FRaftSimHullGeometry* Before=nullptr;
    const FRaftSimHullGeometry* After=nullptr;
    double Now=0.,Interval=0.,Dt=0.,JerkBound=0.;
    void Derivatives(int32 I,FVector& V,FVector& A) const
    {
        const FVector B=(After->VerticesM[I]-Before->VerticesM[I])/Dt;
        const FVector R=State.Orientation.RotateVector(FMath::Lerp(Before->VerticesM[I],After->VerticesM[I],Now/Dt));
        const FVector D=State.Orientation.RotateVector(B),W=State.AngularVelocity;
        V=State.LinearVelocity+FVector::CrossProduct(W,R)+D;
        A=FVector::CrossProduct(W,FVector::CrossProduct(W,R))+2.*FVector::CrossProduct(W,D);
    }
};
using FRaftSimHullGroundArcQuery=TFunction<RaftSimSurfaceSweep::FResult(
    TConstArrayView<FVector>,TConstArrayView<FVector>,TConstArrayView<FIntVector>,double,double,const FRaftSimHullArcPath&)>;

struct FRaftSimHullContactResult : FRaftSimSweptContactResult
{
    int32 Queries=0;
    uint64 TrianglePairs=0;
    double MaximumCurveBoundM=0.,PrescribedShapeWorkJ=0.,DissipatedJ=0.,KineticChangeJ=0.;
    int32 MovingFace=INDEX_NONE,GroundFace=INDEX_NONE;
};

namespace RaftSimHullContact
{
// Rotation is not replaced by a straight chord: a second-derivative bound
// encloses the complete rotating AND linearly deforming path around each chord.
// Failed steps never assign State. Prescribed shape work is explicit, not free
// energy and not a claim that the D4 shape driver has a closed energy budget.
RAFTSIMPHYSICS_API FRaftSimHullContactResult Integrate(FRaftSimFlexRigidState& State,
    const FRaftSimFlexRigidState& Previous,const FRaftSimHullGeometry& Before,
    const FRaftSimHullGeometry& After,double Mass,const FVector& Inertia,double Dt,
    const FRaftSimHullGroundQuery& Query,const FRaftSimHullGroundArcQuery& ArcQuery={},bool bProbeClearFlight=true);
}
