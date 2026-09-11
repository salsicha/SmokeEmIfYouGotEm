#pragma once
#include "CoreMinimal.h"
#include "RenderGraphFwd.h"
class FRHIShaderResourceView;
class FRHIUnorderedAccessView;

// Diagnostic timeline from the current GPU surface's split-age B/A channels.
// One float4 per update: age, elapsed since preceding record, reset, tick flag.
RAFTSIMWATERDETAIL_API void RaftSimRecordLiquidClockGPU(FRDGBuilder& Graph,
    FRDGTextureRef Surface,FRDGBufferRef Timeline,uint32 Index,bool HasTick);

// Pack Niagara's planar GPU float attributes and its live count directly into
// the reconstruction input. Matrix maps simulation-space cm into local cm.
// Default scale converts to metres; diagnostics may use 1 to retain native cm.
RAFTSIMWATERDETAIL_API FRDGBufferRef RaftSimPackLiquidParticlesGPU(FRDGBuilder& Graph,
    FRHIShaderResourceView* Floats,FRHIShaderResourceView* Counts,uint32 FloatStride,
    uint32 PositionOffset,uint32 SourceCountOffset,uint32 Capacity,
    FMatrix44f SimulationToLocalCm,FRDGBufferRef& PackedCount,
    FRHIUnorderedAccessView* CountsInUavState=nullptr,float PackedUnitsScale=0.01f);

struct FRaftSimLiquidDensityResult
{
    FRDGTextureRef Scalar=nullptr;
    FRDGBufferRef KernelRows=nullptr;
    FRDGBufferRef Diagnostics=nullptr;
    FRDGBufferRef DensityFixed=nullptr;
};

// GPU particle-to-density reconstruction. Positions are local METERS, float4
// records (xyz position; w unused). Unshifted centers, weighted covariance,
// number-density normalization and moment-matched voxel prefilter.
// CountBuffer is an optional structured uint buffer for a live GPU count.
// No particle data or count is read back to the CPU by this function.
RAFTSIMWATERDETAIL_API FRaftSimLiquidDensityResult RaftSimLiquidDensityGPU(
    FRDGBuilder& Graph,FRDGBufferRef Positions,uint32 Capacity,
    FRDGBufferRef CountBuffer,uint32 CountOffset,FVector3f MinimumMeters,
    FVector3f ExtentMeters,FIntVector Cells,float RadiusMeters,
    float FootprintMeters,FString& Error,bool SmoothSparse=false);

struct FRaftSimLiquidOccupancyResult
{
    FRDGTextureRef Scalar=nullptr;
    // float2 per render voxel: corrected phi and interpolated interior support.
    FRDGBufferRef Audit=nullptr;
};

// Render-only interior support. Boundary.w is the current solver classification:
// 0 fluid, 1 solid, 2 air, 3 external stage. Same registered domain required;
// uniform 1x/2x/4x refinement. Never writes the solver or original density.
RAFTSIMWATERDETAIL_API FRaftSimLiquidOccupancyResult RaftSimLiquidOccupancyGPU(
    FRDGBuilder& Graph,FRDGTextureRef Scalar,FRDGTextureRef Boundary,
    FRDGBufferRef Diagnostics,FString& Error);
