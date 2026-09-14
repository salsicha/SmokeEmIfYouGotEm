#pragma once
#include "CoreMinimal.h"
#include "RenderGraphFwd.h"

struct RAFTSIMWATERDETAIL_API FRaftSimNonlinearAccelerationResult
{
    FRDGBufferRef Solution=nullptr; // sqrt(h)*a for two poles: ax0, ay0, ax1, ay1
    FRDGBufferRef Residual=nullptr; // true A*Solution-RHS, not PCG recurrence residual
    FRDGBufferRef Diagnostics=nullptr; // invalid inputs, solve-failure bits, iterations0, iterations1
};

// Same depth-weighted completed-square operator as the CPU nonlinear reference:
// A = I + length*(W^T W + .75*b*b^T). Geometry=float2(h,bed), Pairs=uint
// (bit0 positive-x face, bit1 positive-y face), RHS=float4(two normalized RHSs).
// Caller supplies the FINAL reconstructed transport wet graph, not a mean mask.
// Supply PhysicalBedSlope=float2(db/dx,db/dy) from fixed geometry, independent
// of water depth. Null retains only the historical weighted-bed control.
// This is the acceleration solve only; it neither builds nonlinear forcing nor
// evolves state, and is not enabled in play. Reject nonzero Diagnostics[0/1]
// and qualify the returned true residual before publication; iteration counts
// in Diagnostics[2/3] are informational, not errors. Distributed vector phases
// and global reductions retain whole-grid coupling, with RDG device ordering.
// bDistributed=false retains the one-workgroup diagnostic control.
// Both controls dynamically normalize residual/search vectors with integer
// power-of-two exponents while accumulating the solution in original units.
// The initial-global-residual early exit is not used: it can hide physically
// important rows behind a large thin-cell RHS. Exact zero may finish early;
// otherwise the existing 40 iterations and true-residual qualification remain.
// Optional DispersionFraction=float in [0,1] embeds hybrid breaking in the
// symmetric operator W^T*fraction*W + .75*fraction*b*b^T; null means all ones.
// Caller must apply the same fraction in forcing AND pressure reconstruction.
// bFusedReductions combines alpha/update and beta/direction dispatches using
// separate read/write partial/control buffers. Same global PCG equations;
// false retains the six-dispatch-per-iteration comparison path.
// Optional IterationDispatchArgs is the bounded owner's two uint3 indirect
// records (whole-grid groups, single group). It may suppress ONLY recurrence
// work for an inactive interval. Prepare/init/true-residual still run; a skipped
// result is not a qualified pressure solution. Active records must dispatch
// the complete grid for every one of the unchanged 40 iterations.
RAFTSIMWATERDETAIL_API FRaftSimNonlinearAccelerationResult RaftSimSolveNonlinearAccelerationGPU(
    FRDGBuilder& Graph,FRDGBufferRef Geometry,FRDGBufferRef Pairs,FRDGBufferRef RHS,
    FIntPoint Size,float CellMeters,FVector2f Lengths,bool bPeriodic,int32 Iterations,FString& Error,
    FRDGBufferRef PhysicalBedSlope=nullptr,bool bDistributed=true,FRDGBufferRef DispersionFraction=nullptr,
    bool bFusedReductions=true,FRDGBufferRef IterationDispatchArgs=nullptr);
