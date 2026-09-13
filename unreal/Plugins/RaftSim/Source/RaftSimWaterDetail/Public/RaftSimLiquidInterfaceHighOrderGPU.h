#pragma once
#include "CoreMinimal.h"
#include "RenderGraphFwd.h"
struct FRaftSimLiquidHaloPlan;

struct FRaftSimLiquidInterfaceHighOrderStep
{
    FRDGTextureRef Scalar=nullptr;
    // uint32[8]: forward updated, forward failures, invalid scalar/solid values,
    // higher-order used, extrema limited, accuracy fallback, reverse failures,
    // third-forward failures. Entries 1,2,7 invalidate the whole step.
    // Reverse failures are only allowed with explicitly counted first-order
    // fallback; never mistaken for successful high-order transport.
    FRDGBufferRef Diagnostics=nullptr;
};

// Limited BFECC using the existing RK2 characteristics. Source R32F, velocity
// RGBA16F/RGBA32F, solid R32_UINT (0 free, 1 solid) or native RGBA16F boundary
// (w: 0 fluid, 1 solid, 2 air, 3 prescribed exterior). Types 1 and 3 block
// the higher-order correction, retaining first-order transport. Caller owns time,
// physical boundary values and inter-region halo exchange between steps.
// This single-owner operator reverts to first order where intermediate owned
// support is missing. It is not a global high-order halo exchange or a volume
// correction, does not change markers, and does not install a visible surface.
RAFTSIMWATERDETAIL_API FRaftSimLiquidInterfaceHighOrderStep RaftSimAdvectLiquidInterfaceHighOrder(
    FRDGBuilder& Graph,FRDGTextureRef Source,FRDGTextureRef Velocity,FRDGTextureRef Solid,
    FVector3f CellCm,float Dt,FIntVector UpdateMin,FIntVector UpdateMax,FString& Error,bool CompactTransport=true);

struct FRaftSimLiquidInterfaceHighOrderRegion
{
    FRDGTextureRef Source=nullptr,Velocity=nullptr,Solid=nullptr;
};

// Same-age, identically oriented grids with two-cell XY/Z margins. Inputs must
// already have current physical-owner halos. Synchronizes intermediate scalar
// AND validity fields, so artificial owner cuts do not trigger accuracy fallback.
// Unmapped physical exterior validity remains zero. Does not prescribe exterior
// data, change particles or correct volume. Returns empty on invalid input.
RAFTSIMWATERDETAIL_API TArray<FRaftSimLiquidInterfaceHighOrderStep> RaftSimAdvectLiquidInterfaceHighOrderRegions(
    FRDGBuilder& Graph,const FRaftSimLiquidHaloPlan& Halo,
    TConstArrayView<FRaftSimLiquidInterfaceHighOrderRegion> Regions,
    FVector3f CellCm,float Dt,FString& Error,bool CompactTransport=true);
