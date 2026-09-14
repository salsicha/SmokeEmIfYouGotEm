#pragma once
#include "RaftSimTotalDepthAdvanceGPU.h"

struct RAFTSIMWATERDETAIL_API FRaftSimTotalDepthFrameResult
{
    FRDGTextureRef Texture=nullptr; // float4, Nx by Ny+1, same surface for material/contact
    FRDGBufferRef Diagnostics=nullptr; // invalid state/inventory/reference/projection counts, interval bits
};

// Resolve only a completed requested interval. Metadata row pixel0 is the
// existing (origin x,y,cell metres,1) registration; pixel1 is accepted GPU
// (time hi,time lo,remaining=0,2). The readback owner must opt into GPU-clock
// metadata; never attach a CPU-estimated time to this payload. Incomplete,
// failed or invalid frames have invalid registration (w=0) and MUST NOT be
// published. This is not repaired/fallback water or normal-game enablement.
// Reference is the same-grid float2(actual bed,reference carrier surface).
// Open intervals must retain their per-face BoundaryVolume with the completed
// transaction. Missing/mismatched mode or nonfinite inventory invalidates the
// frame, even when the supplied state and summary otherwise look completed.
// The owner extracts Texture with its final access (SRVMask for presentation);
// the resolver leaves it graph-local for downstream passes.
RAFTSIMWATERDETAIL_API FRaftSimTotalDepthFrameResult RaftSimResolveTotalDepthFrameGPU(
    FRDGBuilder& Graph,const FRaftSimTotalDepthAdvanceResult& Completed,
    FRDGBufferRef Reference,FIntPoint Size,FVector2f OriginMeters,float CellMeters,FString& Error);
