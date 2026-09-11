#pragma once
#include "CoreMinimal.h"
#include "RenderGraphFwd.h"
class FRHIShaderResourceView;
class FRHIUnorderedAccessView;

// Exact integer snapshot of four selected native planar particle components.
// Output is int4 per allocated slot, zero for non-live slots; count is not
// clamped so consumers can detect an invalid native count. No particle writes.
RAFTSIMWATERDETAIL_API FRDGBufferRef RaftSimPackLiquidIdentityGPU(FRDGBuilder& Graph,
    FRHIShaderResourceView* Integers,FRHIShaderResourceView* Counts,
    FRHIUnorderedAccessView* CountsInUavState,uint32 IntStride,uint32 Components,
    FIntVector4 Offsets,uint32 CountOffset,uint32 Capacity,FRDGBufferRef& PackedCount);

// Shader-read snapshot for native buffers not created with BUF_SourceCopy.
// Returns a readback-capable int buffer; never mutates the source resource.
RAFTSIMWATERDETAIL_API FRDGBufferRef RaftSimSnapshotLiquidIntegersGPU(
    FRDGBuilder& Graph,FRDGBufferSRVRef Source,uint32 Elements);
