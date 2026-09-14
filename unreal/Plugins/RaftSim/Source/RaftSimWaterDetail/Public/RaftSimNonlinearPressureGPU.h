#pragma once
#include "CoreMinimal.h"
#include "RenderGraphFwd.h"

struct RAFTSIMWATERDETAIL_API FRaftSimNonlinearPressureResult
{
    FRDGBufferRef Force=nullptr; // float2: conservative nonhydrostatic momentum rate
    FRDGBufferRef RightHandSide=nullptr; // float4: two normalized correction RHSs
    FRDGBufferRef Correction=nullptr;
    FRDGBufferRef Pressure=nullptr; // float4: integrated0,bottom0,integrated1,bottom1
    FRDGBufferRef Residual=nullptr;
    FRDGBufferRef Diagnostics=nullptr; // uint4: bad inputs, nonfinite intermediates, reserved, reserved
    FRDGBufferRef SolverDiagnostics=nullptr; // uint4: bad solver inputs, failure bits, iterations0/1
};

// Full kinematic rational-SGN pressure rate, matching the CPU reference. State
// is float4(h,hu,hv,foam); HydroRate=float4(h_t,(hu)_t,(hv)_t,reserved), from the
// SAME reconstructed FV stage. Geometry=float2(h,bed) must agree with State.h.
// Pairs is its final wet-face graph; PhysicalBedSlope is fixed float2(db/dx,db/dy).
// DispersionFraction is float in [0,1], with ones for nonbreaking water.
// No CPU readback. Does not itself transport/integrate state or classify fronts.
// Reject either diagnostic error counter/flag and qualify true residual before
// applying Force. Failure outputs are not a substitute physical solution.
// Fused global reductions are the default; false retains the comparison path.
// Optional BoundaryVelocity=float2(prescribed normal velocity, its time derivative)
// at faces in west Ny/east Ny/south Nx/north Nx order, positive x/y orientation.
// It supplies an affine kinematic divergence lift; the velocity-correction
// operator retains its paired pressure adjoint (zero normal pressure gradient).
// Not compatible with periodic. This is NOT a nonreflecting-wave condition and
// does not infer traces/time derivatives from exterior ghost-centre observations.
// IterationDispatchArgs forwards the bounded owner's inactive recurrence mask;
// see the acceleration API. Final residual checks remain mandatory.
RAFTSIMWATERDETAIL_API FRaftSimNonlinearPressureResult RaftSimNonlinearPressureGPU(
    FRDGBuilder& Graph,FRDGBufferRef State,FRDGBufferRef HydroRate,FRDGBufferRef Geometry,
    FRDGBufferRef Pairs,FRDGBufferRef PhysicalBedSlope,FRDGBufferRef DispersionFraction,
    FIntPoint Size,float CellMeters,bool bPeriodic,FString& Error,bool bFusedReductions=true,
    FRDGBufferRef BoundaryVelocity=nullptr,FRDGBufferRef IterationDispatchArgs=nullptr);
