#pragma once
#include "CoreMinimal.h"
#include "Engine/HitResult.h"
#include "RaftSimSurfaceSweep.h"

class UStaticMeshComponent;
class UStaticMesh;

namespace RaftSimTriangleSweep
{
// Double-precision translating sphere against one original triangle. Metres.
bool Triangle(const FVector& Start,const FVector& End,double Radius,
    const FVector& A,const FVector& B,const FVector& C,FHitResult& Hit);
}

// Immutable collision-provider triangles, transformed once per component pose.
// BVH only reorders triangle references: no simplification or substitute bed.
class FRaftSimTriangleSweepMesh
{
public:
    bool Build(UStaticMeshComponent* Component);
    bool Matches(UStaticMeshComponent* Component) const;
    bool Sweep(const FVector& StartCm,const FVector& EndCm,double RadiusCm,FHitResult& Hit) const;
    // Indexed full surface, world centimetres. Linear motion of every vertex;
    // no convex hull, support-point subset or fitted capsule replacement.
    RaftSimSurfaceSweep::FResult SweepSurface(TConstArrayView<FVector> StartCm,
        TConstArrayView<FVector> EndCm,TConstArrayView<FIntVector> Faces,double SkinCm,double ProvenClearanceCm=-1.) const;
    bool IsValid() const { return bValid; }
    int32 TriangleCount() const { return Triangles.Num(); }
private:
    struct FNode { FBox Bounds=FBox(ForceInit);int32 Left=INDEX_NONE,Right=INDEX_NONE,Begin=0,Count=0; };
    int32 BuildNode(int32 Begin,int32 Count);
    TWeakObjectPtr<UStaticMesh> Asset;
    TWeakObjectPtr<UStaticMesh> CollisionAsset;
    FGuid BodyGuid;
    FGuid CollisionLightingGuid;
    int32 TraceFlag=0;
    FTransform Transform;
    FVector OriginCm=FVector::ZeroVector;
    TArray<FVector> Vertices;
    TArray<FIntVector> Triangles;
    TArray<int32> Order;
    TArray<FNode> Nodes;
    bool bValid=false;
};
