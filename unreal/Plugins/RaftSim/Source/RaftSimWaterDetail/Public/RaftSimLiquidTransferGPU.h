#pragma once
#include "RaftSimLiquidHaloGPU.h"

// Reverse the physical-owner -> halo map to sum independent P2G deposits.
// Input xyz = SUM(volume_m3 * kernel_weight * local_velocity_cm_s),
// w = SUM(volume_m3 * kernel_weight). All owners MUST use the same vector
// basis/metric and unique particle ownership, and complete the same P2G step.
// This does not migrate particles, enforce those caller contracts, or project.
struct FRaftSimLiquidTransferPlan
{
    FRDGBufferRef Groups=nullptr,Contributors=nullptr;
    TArray<FIntVector> Sizes;
    uint32 Count=0;
};
RAFTSIMWATERDETAIL_API FRaftSimLiquidTransferPlan RaftSimBuildLiquidTransferPlan(
    FRDGBuilder& Graph,TConstArrayView<FIntVector> Sizes,
    TConstArrayView<FRaftSimLiquidHaloColumn> Columns,FString& Error);

// Reads immutable RGBA32F deposits and produces separate RGBA32F totals. Sum
// each shared global cell ONCE and distribute the identical total to its
// physical owner and all subscribers. Unshared/exterior cells are preserved.
// Never feed the previous totals back as new deposits; doing so doubles mass.
RAFTSIMWATERDETAIL_API bool RaftSimReduceLiquidTransfer(
    FRDGBuilder& Graph,const FRaftSimLiquidTransferPlan& Plan,
    TConstArrayView<FRDGTextureRef> Deposits,TArray<FRDGTextureRef>& Totals,FString& Error);

// After reduction and BEFORE Compute Boundary: replace native local-only
// velocity and raster support with the shared totals. Native terrain/exterior
// classification and D/P/G still run afterwards. Inputs must be finite; the
// native RGBA16F velocity range remains a separate wet-simulation constraint.
RAFTSIMWATERDETAIL_API bool RaftSimResolveLiquidTransfer(FRDGBuilder& Graph,
    FRDGTextureRef Total,FRDGTextureRef NativeVelocity,FRDGTextureRef NativeSupport,FString& Error);
