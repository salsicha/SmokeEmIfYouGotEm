#pragma once

#include "CoreMinimal.h"
#include "Components/MeshComponent.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimWaterShoreline.h"
#include "RaftSimShorelineCrests.h"
#include "RaftSimReferencedWaterVertices.h"
#include "RaftSimShorelineCrestWeights.h"
#include "Tasks/Task.h"
#include <atomic>
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
    // SetClippedWaterMesh in two parts. Compute touches only this component's
    // own mesh state and may run off the game thread while nothing else reads
    // it; Finish (game thread) then updates bounds and the render state.
    bool ComputeClippedWaterMesh(int32 Nx, int32 Ny, TArray<FProcMeshVertex>&& Source,
        TConstArrayView<uint8> Wet, TConstArrayView<uint8> Available,
        TConstArrayView<float> DepthM, TConstArrayView<float> BedM,
        const FRaftSimShorelineCrestInput* Crests=nullptr);
    void FinishClippedWaterMesh();
    // A worker running ComputeClippedWaterMesh for this component. Every
    // mesh accessor and render path below waits for it; the owner clears it
    // on the game thread once the task has completed, then calls Finish.
    void SetPendingCompute(const UE::Tasks::FTask& Task) { PendingCompute=Task; bComputePending=true; }
    void ClearPendingCompute() { bComputePending=false; }
    bool IsComputePending() const { return bComputePending; }
    void WaitForPendingCompute() const { if (bComputePending) PendingCompute.Wait(); }
    const TArray<FProcMeshVertex>& GetWaterVertices() const { WaitForPendingCompute(); return WaterVertices; }
    const TArray<uint32>& GetWaterIndices() const { WaitForPendingCompute(); return WaterIndices; }
    int32 GetIndexCapacity() const { WaitForPendingCompute(); return WaterIndexCapacity; }
    FVector GetWaterRenderOrigin() const { WaitForPendingCompute(); return WaterRenderOrigin; }
    const TArray<int32>& GetCellOffsets() const { WaitForPendingCompute(); return CellOffsets; }
    uint64 GetTopologyRebuildCount() const { return TopologyCache.GetRebuildCount(); }
    uint64 GetTopologyReuseCount() const { return TopologyCache.GetReuseCount(); }
    const FRaftSimShorelineCrests& GetCrestRefinement() const { WaitForPendingCompute(); return CrestRefinement; }
    void PrefetchCrestProfile(const FRaftSimShorelineCrestInput& Input) { WaitForPendingCompute(); CrestRefinement.PrefetchProfile(Input); }
    int32 GetActiveVertexCount() const { WaitForPendingCompute(); return ActiveVertexCount; }
    // Source anchors precede new crest midpoints, but may be index-compacted.
    // Diagnostics must not confuse compact anchor IDs with hydraulic grid IDs.
    int32 GetCrestSourceVertexCount() const { return CrestSourceVertexCount; }
    int32 GetCrestSourceOriginalIndex(int32 Anchor) const
    { return bCompactCrestSource ? ReferencedCrestSource.Sources[Anchor] : Anchor; }
    bool HasCompactCrestSource() const { return bCompactCrestSource; }
    virtual int32 GetNumMaterials() const override { return 1; }
    virtual FPrimitiveSceneProxy* CreateSceneProxy() override;
    virtual FBoxSphereBounds CalcBounds(const FTransform& Transform) const override;
    virtual void SendRenderDynamicData_Concurrent() override;
private:
    mutable UE::Tasks::FTask PendingCompute;
    std::atomic<bool> bComputePending{false};
    int32 FinishBeforeVertices=0,FinishBeforeCapacity=0;
    TArray<FProcMeshVertex> WaterVertices;
    FVector WaterRenderOrigin=FVector::ZeroVector;
    TArray<uint32> WaterIndices;
    int32 WaterIndexCapacity = 0;
    FBox WaterBounds = FBox(ForceInit);
    TArray<int32> CellOffsets;
    TArray<FProcMeshVertex> ClippedVertices;
    TArray<uint32> ClippedIndices;
    TArray<int32> ClippedCellOffsets;
    FRaftSimShorelineCrests CrestRefinement;
    FRaftSimReferencedWaterVertices ReferencedCrestSource;
    FRaftSimShorelineCrestWeights CrestWeights;
    // Separate evolving reference/candidate history only for explicit audits.
    FRaftSimShorelineCrests AuditCrestRefinement;
    TArray<FProcMeshVertex> AuditCrestVertices;
    TArray<uint32> AuditCrestIndices;
    TArray<int32> AuditCrestOffsets;
    int32 ActiveVertexCount=0;
    int32 CrestSourceVertexCount=0;
    bool bCompactCrestSource=false;
    RaftSimWaterShoreline::FTopologyCache TopologyCache;
    bool bPendingIndexUpdate = true;
    TArray<uint32> RenderVertexSources;
    bool bHasRenderVertexSources = false;
};
