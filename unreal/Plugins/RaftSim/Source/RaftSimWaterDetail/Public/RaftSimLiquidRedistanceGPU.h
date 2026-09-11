#pragma once
#include "CoreMinimal.h"
#include "RenderGraphFwd.h"
class FRHICommandListImmediate;
class FRHITexture;

RAFTSIMWATERDETAIL_API bool RaftSimLiquidRedistanceRDG(FRDGBuilder& Graph,
    FRDGTextureRef Source,FRDGTextureRef Target,FIntVector Size,FVector3f CellCm,
    float BandwidthCm,int32 Iterations,FString& Error,FRDGTextureRef CoverageSource=nullptr);

// Render-thread GPU-only reconstruction of Source.r == 0. Source and target
// must be distinct registered 3D textures. Cell size/bandwidth are centimeters.
// Source.gba (surface coverage and auxiliary metadata) is preserved on output.
// No CPU readback/upload, particle mutation or new water plane in this function.
RAFTSIMWATERDETAIL_API bool RaftSimLiquidRedistanceGPU(FRHICommandListImmediate& Cmd,
    FRHITexture* Source,FRHITexture* Target,FIntVector Size,FVector3f CellCm,
    float BandwidthCm,int32 Iterations,FString& Error);
