#pragma once
#include "CoreMinimal.h"
#include "RenderGraphFwd.h"

struct FRaftSimLiquidDensityGradient
{
    FRDGBufferRef Gradient=nullptr,Diagonal=nullptr,Diagnostics=nullptr;
};

// Position-level density objective derivative, not a physical velocity update.
// Positions: float4(local XYZ, conserved volume), with spacing/volume in the
// same length unit. Field: float2(particle density, fixed solid-kernel fraction),
// X fastest. All eight tent nodes participate regardless of native phase.
// No particle/count/mass writes. Contact solve and native integration are separate.
// Diagnostics: invalid inputs/overflow, incomplete support, invalid field, valid.
RAFTSIMWATERDETAIL_API FRaftSimLiquidDensityGradient RaftSimLiquidDensityGradientGPU(
    FRDGBuilder& Graph,FRDGBufferRef Positions,FRDGBufferRef LiveCount,uint32 Capacity,
    FRDGBufferRef DensitySolid,FIntVector Cells,FVector3f Spacing,FString& Error);
