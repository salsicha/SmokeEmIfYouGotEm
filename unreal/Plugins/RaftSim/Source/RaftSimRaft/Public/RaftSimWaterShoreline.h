#pragma once

#include "CoreMinimal.h"
#include "ProceduralMeshComponent.h"

namespace RaftSimWaterShoreline
{
struct FEdge
{
    int32 WetVertex, DryVertex, Node;
    double Crossing;
};
struct FBankTriangle
{
    uint32 A, B, C;
    int8 Orientation;
};
// Clip the Cartesian lattice in two dimensions. Original vertices plus one
// shared node per horizontal/vertical edge keep storage below 3N;
// adjacent cells cannot independently round their shared waterline. Dry islands
// and disconnected diagonal channels never acquire connecting triangles.
RAFTSIMRAFT_API bool Build(int32 Nx, int32 Ny, TArray<FProcMeshVertex>&& Source,
    TConstArrayView<uint8> Wet, TConstArrayView<uint8> Available,
    TConstArrayView<float> DepthM, TConstArrayView<float> BedM,
    TArray<FProcMeshVertex>& OutVertices, TArray<uint32>& OutIndices,
    TArray<int32>* OutCellOffsets = nullptr, TArray<FEdge>* OutEdges = nullptr,
    bool bCompactEdges = false);
RAFTSIMRAFT_API bool Sample(const FVector2D& PositionXY, int32 Begin, int32 End,
    TConstArrayView<FProcMeshVertex> Vertices, TConstArrayView<uint32> Indices, FVector& Position,
    FIntVector* Corners=nullptr,FVector* Weights=nullptr);

// Own this cache together with its output arrays. Exact input identity, not a
// tolerance or a hash, controls reuse. Moving crossings rewrite exact vertices
// and recheck every potentially affected triangle, including omitted degenerate
// triangles. Membership/winding changes, wetness, availability or XY rebuild.
class RAFTSIMRAFT_API FTopologyCache
{
public:
    bool Update(int32 Nx, int32 Ny, TArray<FProcMeshVertex>&& Source,
        TConstArrayView<uint8> Wet, TConstArrayView<uint8> Available,
        TConstArrayView<float> DepthM, TConstArrayView<float> BedM,
        TArray<FProcMeshVertex>& Vertices, TArray<uint32>& Indices,
        TArray<int32>& CellOffsets, bool& bTopologyRebuilt, bool bCompactEdges = false);
    void Reset();
    uint64 GetRebuildCount() const { return RebuildCount; }
    uint64 GetReuseCount() const { return ReuseCount; }
    const TArray<FEdge>& GetEdges() const { return Edges; }
private:
    int32 CachedNx=0, CachedNy=0, CachedIndexCount=0;
    bool bCachedCompactEdges=false;
    TArray<FVector2D> XY;
    TArray<uint8> WetMask, AvailableMask;
    TArray<FEdge> Edges;
    TArray<FBankTriangle> BankTriangles;
    uint64 RebuildCount=0, ReuseCount=0;
};
}
