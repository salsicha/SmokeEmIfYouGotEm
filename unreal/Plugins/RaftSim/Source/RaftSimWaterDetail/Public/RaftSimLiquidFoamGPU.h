#pragma once
#include "CoreMinimal.h"
#include "RenderGraphFwd.h"

struct FRaftSimLiquidFoamResult
{
    FRDGTextureRef Surface=nullptr;
    // Render-voxel float4: source rate /s, advected coverage, dt, unrounded result.
    FRDGBufferRef Audit=nullptr;
};

// Persistent foam on the CURRENT reconstructed metric SDF. Centimeters/seconds.
// Clock is the GPU simulation-age timeline, never a render-frame delta.
// Null history initializes cleanly. Output keeps current R/B/A unchanged.
RAFTSIMWATERDETAIL_API FRaftSimLiquidFoamResult RaftSimLiquidFoamGPU(
    FRDGBuilder& Graph,FRDGTextureRef Current,FRDGTextureRef History,
    FRDGTextureRef Velocity,FRDGTextureRef Boundary,FRDGBufferRef Clock,uint32 ClockIndex,
    FVector3f ExtentCm,FVector2f PhysicalHalfExtentCm,float SourceScale,float DecayRate,
    FRDGBufferRef Diagnostics,FString& Error);

// Existing square fixtures keep exactly the same physical edge policy.
inline FRaftSimLiquidFoamResult RaftSimLiquidFoamGPU(
    FRDGBuilder& Graph,FRDGTextureRef Current,FRDGTextureRef History,
    FRDGTextureRef Velocity,FRDGTextureRef Boundary,FRDGBufferRef Clock,uint32 ClockIndex,
    FVector3f ExtentCm,float PhysicalHalfWidthCm,float SourceScale,float DecayRate,
    FRDGBufferRef Diagnostics,FString& Error)
{
    return RaftSimLiquidFoamGPU(Graph,Current,History,Velocity,Boundary,Clock,ClockIndex,ExtentCm,
        FVector2f(PhysicalHalfWidthCm,PhysicalHalfWidthCm),SourceScale,DecayRate,Diagnostics,Error);
}
