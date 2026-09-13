#pragma once
#include "CoreMinimal.h"
#include "RenderGraphFwd.h"

struct FRaftSimLiquidInterfaceStep
{
    FRDGTextureRef Scalar=nullptr;
    // uint32[3]: updated cells, out-of-grid traces, nonfinite inputs/results.
    // Either error count makes the candidate step INVALID. Retained old values
    // on rejected cells are diagnostic containment, not a boundary condition.
    FRDGBufferRef Diagnostics=nullptr;
};

// Carry a current explicit liquid/air scalar with the SAME grid-local cm/s
// velocity used by the native solver. Centred samples, RK2 backtrace, trilinear
// scalar interpolation; optional compact divergence-compatible velocity basis.
// No density threshold, level reset, frame-relative scrolling,
// or particle modification. Source R32F; velocity RGBA16F or RGBA32F.
// Caller owns temporal ordering, external boundary values, halo exchange and
// particle correction. Only the half-open XYZ box is updated; other cells are
// preserved. Outputs are separate from inputs. This operator alone does not
// install a native pressure/render interface or prove volume conservation.
RAFTSIMWATERDETAIL_API FRaftSimLiquidInterfaceStep RaftSimAdvectLiquidInterface(
    FRDGBuilder& Graph,FRDGTextureRef Source,FRDGTextureRef Velocity,
    FVector3f CellCm,float Dt,FIntVector UpdateMin,FIntVector UpdateMax,FString& Error,bool CompactTransport=false);
