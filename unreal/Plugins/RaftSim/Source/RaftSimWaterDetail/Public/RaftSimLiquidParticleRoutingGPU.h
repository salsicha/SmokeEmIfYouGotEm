#pragma once
#include "CoreMinimal.h"
#include "RenderGraphFwd.h"
class FRHIShaderResourceView;
class FRHIUnorderedAccessView;

// Immutable candidate transaction. Every native float/int component is kept as
// uint32 bits. Routes contain destination owner, source owner, source index,
// status (0 unused,1 owned,2 exterior,4 nonfinite). No native state is modified.
// Exterior/overflow records must be accounted for, not silently discarded by a
// future commit. The current native ABI has no half components; reject other ABIs.
struct FRaftSimLiquidParticleRoutePlan
{
    FRDGBufferRef Bounds=nullptr;
    uint32 Owners=0;
    FIntPoint ParentCells=FIntPoint::ZeroValue;
    FVector3f LowerWorldCm=FVector3f::ZeroVector,AxisX=FVector3f::ZeroVector,AxisY=FVector3f::ZeroVector;
    FVector2f SpacingCm=FVector2f::ZeroVector;
};
RAFTSIMWATERDETAIL_API FRaftSimLiquidParticleRoutePlan RaftSimBuildLiquidParticleRoutePlan(FRDGBuilder& Graph,
    FIntPoint ParentCells,TConstArrayView<FIntRect> Regions,FVector LowerWorldCm,FVector AxisX,FVector AxisY,
    FVector2D SpacingCm,FString& Error);

struct FRaftSimLiquidParticleRoutePacket
{
    FRDGBufferRef Words=nullptr,Routes=nullptr,Counts=nullptr;
    uint32 Capacity=0,FloatComponents=0,IntComponents=0;
};
struct FRaftSimLiquidParticleExitCandidates
{
    FRDGBufferRef Records=nullptr,Counts=nullptr;
    // Bind evidence to the exact immutable source snapshot it classified.
    FRDGBufferRef SourceWords=nullptr,SourceRoutes=nullptr,SourceCounts=nullptr;
    float ParticleVolumeM3=0;
};
RAFTSIMWATERDETAIL_API FRaftSimLiquidParticleRoutePacket RaftSimStageLiquidParticleRoutes(FRDGBuilder& Graph,
    const FRaftSimLiquidParticleRoutePlan& Plan,uint32 SourceOwner,
    FRHIShaderResourceView* Floats,FRHIShaderResourceView* Integers,FRHIUnorderedAccessView* NativeCounts,
    uint32 CountOffset,uint32 FloatStride,uint32 IntStride,uint32 FloatComponents,uint32 IntComponents,
    uint32 HalfComponents,uint32 PositionOffset,uint32 Capacity,FString& Error);

// Receiving-side staging, not a native Niagara commit. Owner ranges address a
// shared component-major word buffer. Reference entries retain (source, index).
// Control uint4 = (valid transaction, error bits, source live sum, exterior sum).
// Error bits: 1 invalid/overflow input, 2 exterior pending an outflow policy,
// 4 destination capacity exceeded, 8 inconsistent source/route accounting.
// 64 rejected/inconsistent outlet evidence. With exit evidence supplied, approved
// exterior particles are copied into a separate exact ledger before commit.
// No native state is modified, including on failed GPU capacity checks.
struct FRaftSimLiquidParticleAssembly
{
    FRDGBufferRef Words=nullptr,References=nullptr,Counts=nullptr,Control=nullptr,OwnerRanges=nullptr;
    uint32 TotalCapacity=0,FloatComponents=0,IntComponents=0;
    TArray<uint32> DestinationCapacities;
    FRDGBufferRef ExitWords=nullptr,ExitReferences=nullptr,ExitRecords=nullptr,ExitCounts=nullptr,ExitOwnerRanges=nullptr;
    uint32 TotalExitCapacity=0;
    // Source-indexed ledger counts: four face counts followed by total retired.
    // Exact volume accounting is count * this source's declared native volume.
    TArray<float> ExitParticleVolumesM3;
    TArray<uint32> ExitSourceCapacities;
};
RAFTSIMWATERDETAIL_API FRaftSimLiquidParticleAssembly RaftSimAssembleLiquidParticleDestinations(
    FRDGBuilder& Graph,TConstArrayView<FRaftSimLiquidParticleRoutePacket> Sources,
    TConstArrayView<uint32> DestinationCapacities,FString& Error,
    TConstArrayView<FRaftSimLiquidParticleExitCandidates> Exits={});

// Local persistent handles for a receiving assembly. Staying particles retain
// index AND acquire tag. Incoming particles use free destination indices and a
// caller-owned fresh negative acquire tag (high-bit namespace, positive native
// TickCounter namespace). Caller must reject either counter's wrap and must not
// reuse epochs while references to that simulation generation remain valid.
// Adds error bit16 for invalid/duplicate local handles. No native writes.
struct FRaftSimLiquidParticleHandles
{
    FRDGBufferRef Handles=nullptr,IDToIndex=nullptr,FreeIDs=nullptr,FreeCounts=nullptr,TableRanges=nullptr;
    uint32 TotalIDs=0;
    TArray<uint32> IDCapacities;
};
RAFTSIMWATERDETAIL_API FRaftSimLiquidParticleHandles RaftSimPrepareLiquidParticleHandles(FRDGBuilder& Graph,
    const FRaftSimLiquidParticleAssembly& Assembly,TConstArrayView<uint32> IDCapacities,uint32 IDIndexComponent,uint32 IDTagComponent,
    uint32 TransferEpoch,uint32 NativeAcquireTag,FString& Error);

struct FRaftSimLiquidNativeParticleTarget
{
    FRHIUnorderedAccessView* Floats=nullptr;
    FRHIUnorderedAccessView* Integers=nullptr;
    FRHIUnorderedAccessView* IDToIndex=nullptr;
    FRHIUnorderedAccessView* NativeCounts=nullptr;
    uint32 Capacity=0,FloatStride=0,IntStride=0,IDCapacity=0,CountOffset=MAX_uint32;
};
// Applies the entire valid receiving transaction to native buffers. Source
// snapshotting, final-stage ordering, next-tick dispatch reservations and native
// free-ID recomputation are caller responsibilities. GPU failure (control bit32)
// prevents ALL native writes. Unallocated targets accept only zero live count.
// Particle buffers enter/leave SRVMask; ID lookup enters/leaves SRVCompute;
// native counters stay UAVCompute, matching Niagara's final-stage resources.
RAFTSIMWATERDETAIL_API bool RaftSimCommitLiquidParticleAssembly(FRDGBuilder& Graph,
    const FRaftSimLiquidParticleAssembly& Assembly,const FRaftSimLiquidParticleHandles& Handles,
    TConstArrayView<FRaftSimLiquidNativeParticleTarget> Targets,uint32 IDIndexComponent,uint32 IDTagComponent,FString& Error);
