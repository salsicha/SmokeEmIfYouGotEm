#pragma once
#include "CoreMinimal.h"
class UStaticMeshComponent;

// Double precision, metres. All three vertices move linearly between endpoints.
// This is NOT exact rotational CCD; the caller must bound any curved trajectory.
namespace RaftSimSurfaceSweep
{
struct FTriangle { FVector V[3]; };
struct FDistance
{
    double Squared=DBL_MAX;
    FVector MovingPoint=FVector::ZeroVector,GroundPoint=FVector::ZeroVector;
    FVector MovingBary=FVector::ZeroVector,GroundBary=FVector::ZeroVector;
};
enum class EStatus : uint8 { Clear,Contact,InitialIntersection,Unresolved,Invalid };
struct FResult
{
    EStatus Status=EStatus::Invalid;
    double Time=0;
    FDistance Witness;
    FVector Normal=FVector::ZeroVector;
    int32 Iterations=0,MovingFace=INDEX_NONE,GroundFace=INDEX_NONE;
    uint64 TrianglePairs=0;
    TWeakObjectPtr<UStaticMeshComponent> GroundComponent;
};
// Includes both vertex/face directions, every edge pair, and crossing faces.
// Degenerate source faces retain their segment/point geometry rather than vanish.
RAFTSIMPHYSICS_API FDistance Distance(const FTriangle& Moving,const FTriangle& Ground);
RAFTSIMPHYSICS_API FResult Sweep(const FTriangle& Start,const FTriangle& End,const FTriangle& Ground,
    double SkinM=1.e-5,int32 MaximumIterations=128,double ProvenClearanceM=-1.,bool bPreflightSeparation=true);
}
