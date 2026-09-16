#pragma once
#include "RaftSimHullGeometry.h"
#include "RaftSimSurfaceSweep.h"
#include "RaftSimSweptGroundContact.h"

using FRaftSimHullGroundQuery=TFunction<RaftSimSurfaceSweep::FResult(
    TConstArrayView<FVector>,TConstArrayView<FVector>,TConstArrayView<FIntVector>,double,double)>;

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
    const FRaftSimHullGroundQuery& Query);
}
