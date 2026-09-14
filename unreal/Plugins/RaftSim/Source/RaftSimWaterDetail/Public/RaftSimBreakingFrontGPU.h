#pragma once
#include "CoreMinimal.h"
#include "RenderGraphFwd.h"
#include "RaftSimTotalDepthStepGPU.h"

struct RAFTSIMWATERDETAIL_API FRaftSimBreakingFrontResult
{
    FRDGBufferRef Fraction=nullptr; // float, nonbreaking fraction of each cell
    FRDGBufferRef Diagnostics=nullptr; // uint4(error bits,fronts,truncated runs,subcell fronts)
    FRDGBufferRef SurfaceJumps=nullptr; // cached float2, exact-cancellation/range-aware cardinal jumps
};

// Cardinal-front adaptation of Filippini/Kazolea/Ricchiuto section6, matching
// breaking_front_reference.py; not a validated 2D overturning/entrainment law.
// Consume the SAME stage's float2(depth,bed), float4 hydro rate and uint wet
// graph. No state mutation or readback. Invalid input yields NaN fractions so
// the existing pressure/trial validation refuses publication, never silently
// treating a failed classifier as a nonbreaking field. Closed/truncated fronts
// are not invented and bands cannot cross disconnected wet components.
RAFTSIMWATERDETAIL_API FRaftSimBreakingFrontResult RaftSimClassifyBreakingFrontGPU(
    FRDGBuilder& Graph,FRDGBufferRef Geometry,FRDGBufferRef HydroRate,FRDGBufferRef Pairs,
    FIntPoint Size,float CellMeters,bool bPeriodic,FString& Error);

// Full nonlinear RK2 coupling: classify each stage's own reconstructed graph
// and mass rate, then use its fraction in forcing, elliptic pressure and force
// reconstruction. Retains the original transactional state/clock/error gates.
RAFTSIMWATERDETAIL_API FRaftSimTotalDepthStepResult RaftSimTryHybridBreakingStepGPU(
    FRDGBuilder& Graph,FRDGBufferRef State,FRDGBufferRef Bed,FRDGBufferRef Progress,
    FIntPoint Size,float CellMeters,bool bPeriodic,bool bSecondOrder,FString& Error,
    FRaftSimTotalDepthBoundaryProvider BoundaryForStage={},FRDGBufferRef IterationDispatchArgs=nullptr);
