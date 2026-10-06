#pragma once
#include "CoreMinimal.h"
#include "RenderGraphFwd.h"

struct FRaftSimLiquidHaloColumn
{
    int32 SourceOwner=INDEX_NONE,DestinationOwner=INDEX_NONE;
    FIntPoint Source,Destination; // Positive-scale Niagara grid coordinates.
};

// Pressure/boundary synchronization primitive, not a fluid solver. Caller must
// establish same-age, same-iteration completion of every owner before dispatch.
// Source cells MUST be physical owners; destinations MUST be unique halo cells.
// Therefore a single UAV pass can exchange in both directions without reading
// any value concurrently being written. No snapshot volume or per-face dispatch.
// Does not reduce P2G contributions or transfer particles/foam.
struct FRaftSimLiquidHaloPlan
{
    FRDGBufferRef Columns=nullptr; // Graph-local; never retain across frames.
    TArray<FIntVector> Sizes;
    uint32 Count=0;
};
RAFTSIMWATERDETAIL_API FRaftSimLiquidHaloPlan RaftSimBuildLiquidHaloPlan(
    FRDGBuilder& Graph,TConstArrayView<FIntVector> Sizes,
    TConstArrayView<FRaftSimLiquidHaloColumn> Columns,FString& Error);
RAFTSIMWATERDETAIL_API bool RaftSimExchangeLiquidPressureHalo(
    FRDGBuilder& Graph,const FRaftSimLiquidHaloPlan& Plan,
    TConstArrayView<FRDGTextureRef> Grids,FString& Error);
// Copy the owner's native SolidVelocity_Boundary RGBA16F (velocity + type),
// after ALL Compute Boundary stages and before velocity extrapolation / D/P/G.
// No averaging or rounding of type; this is not a P2G momentum reduction.
RAFTSIMWATERDETAIL_API bool RaftSimExchangeLiquidBoundaryHalo(
    FRDGBuilder& Graph,const FRaftSimLiquidHaloPlan& Plan,
    TConstArrayView<FRDGTextureRef> Grids,FString& Error);
// Same-age post-extrapolation RGBA16F velocity. Copy physical owner values into
// internal halos before BOTH particle and interface characteristic evaluation.
// Leaves physical owners and unmapped exteriors untouched; not velocity smoothing.
RAFTSIMWATERDETAIL_API bool RaftSimExchangeLiquidVelocityHalo(
    FRDGBuilder& Graph,const FRaftSimLiquidHaloPlan& Plan,
    TConstArrayView<FRDGTextureRef> Grids,FString& Error);
