#pragma once

#include "CoreMinimal.h"
#include "Components/MeshComponent.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimWaterShoreline.h"
#include "RaftSimShorelineCrests.h"
#include "RaftSimShorelineMeshComponent.generated.h"

// One non-colliding water section. Unlike a procedural mesh section, its index
// membership can change without replacing the scene proxy and its view history.
UCLASS()
class RAFTSIMRAFT_API URaftSimShorelineMeshComponent : public UMeshComponent
{
    GENERATED_BODY()
public:
    URaftSimShorelineMeshComponent();
    bool SetWaterMesh(TArray<FProcMeshVertex>&& Vertices, TArray<uint32>&& Indices,
        int32 IndexCapacity);
    bool SetClippedWaterMesh(int32 Nx, int32 Ny, TArray<FProcMeshVertex>&& Source,
        TConstArrayView<uint8> Wet, TConstArrayView<uint8> Available,
        TConstArrayView<float> DepthM, TConstArrayView<float> BedM,
        const FRaftSimShorelineCrestInput* Crests=nullptr);
    const TArray<FProcMeshVertex>& GetWaterVertices() const { return WaterVertices; }
    const TArray<uint32>& GetWaterIndices() const { return WaterIndices; }
    int32 GetIndexCapacity() const { return WaterIndexCapacity; }
    const TArray<int32>& GetCellOffsets() const { return CellOffsets; }
    uint64 GetTopologyRebuildCount() const { return TopologyCache.GetRebuildCount(); }
    uint64 GetTopologyReuseCount() const { return TopologyCache.GetReuseCount(); }
    const FRaftSimShorelineCrests& GetCrestRefinement() const { return CrestRefinement; }
    void PrefetchCrestProfile(const FRaftSimShorelineCrestInput& Input) { CrestRefinement.PrefetchProfile(Input); }
    int32 GetActiveVertexCount() const { return ActiveVertexCount; }
    virtual int32 GetNumMaterials() const override { return 1; }
    virtual FPrimitiveSceneProxy* CreateSceneProxy() override;
    virtual FBoxSphereBounds CalcBounds(const FTransform& Transform) const override;
    virtual void SendRenderDynamicData_Concurrent() override;
private:
    TArray<FProcMeshVertex> WaterVertices;
    TArray<uint32> WaterIndices;
    int32 WaterIndexCapacity = 0;
    FBox WaterBounds = FBox(ForceInit);
    TArray<int32> CellOffsets;
    TArray<FProcMeshVertex> ClippedVertices;
    TArray<uint32> ClippedIndices;
    TArray<int32> ClippedCellOffsets;
    FRaftSimShorelineCrests CrestRefinement;
    int32 ActiveVertexCount=0;
    RaftSimWaterShoreline::FTopologyCache TopologyCache;
    bool bPendingIndexUpdate = true;
    TArray<uint32> RenderVertexSources;
    bool bHasRenderVertexSources = false;
};
