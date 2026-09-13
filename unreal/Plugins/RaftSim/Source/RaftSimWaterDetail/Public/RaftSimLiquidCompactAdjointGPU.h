#pragma once
#include "CoreMinimal.h"
#include "RenderGraphFwd.h"

struct FRaftSimLiquidCompactAdjoint
{
    FRDGBufferRef Field=nullptr,Diagnostics=nullptr;
};

// Exact component-wise compact interpolation transpose, up to float summation.
// Positions float4(local XYZ,volume); particle gradients float4(XYZ,valid=1).
// Mobility is an XYZ bit mask per X-fastest grid node (0..7). It fixes field
// unknowns, not density residuals. Linked-bin gather avoids quantized/floating
// atomic accumulation. No particle, momentum, surface or terrain writes.
// Diagnostics[0..5]: invalid input/count, incomplete support, invalid mobility/
// field, binned particles, written nodes, corrupt neighbor chain. Consumers must
// reject the entire result if diagnostics0/1/2/5 are nonzero.
RAFTSIMWATERDETAIL_API FRaftSimLiquidCompactAdjoint RaftSimLiquidCompactAdjointGPU(
    FRDGBuilder& Graph,FRDGBufferRef Positions,FRDGBufferRef ParticleGradient,
    FRDGBufferRef LiveCount,uint32 Capacity,FRDGBufferRef Mobility,
    FIntVector Cells,FVector3f Spacing,FString& Error);
