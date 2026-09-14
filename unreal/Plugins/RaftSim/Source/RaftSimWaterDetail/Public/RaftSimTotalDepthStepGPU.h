#pragma once
#include "CoreMinimal.h"
#include "RenderGraphFwd.h"
#include "RaftSimTotalDepthTransportGPU.h"
#include "RaftSimNonlinearPressureGPU.h"

struct FRaftSimTotalDepthBoundaryInput
{
    FRDGBufferRef ExteriorState=nullptr;
    FRDGBufferRef ExteriorBed=nullptr;
    FRDGBufferRef FaceVelocity=nullptr; // float2(normal velocity, time derivative)
};

// Called once per stage with its actual state and the original compensated
// progress. TrialInfo is null at the first stage; at the second it is the GPU
// float4 info whose .y is the actual CFL-limited trial dt. Time is progress.xy
// plus that dt, NOT a CPU estimate/proposed dt. A provider may schedule GPU
// evaluation of temporal data or reflecting ghost states; it must never mutate
// input state/progress. All three returned buffers are mandatory, nonperiodic.
using FRaftSimTotalDepthBoundaryProvider=TFunction<FRaftSimTotalDepthBoundaryInput(
    FRDGBuilder&,FRDGBufferRef,FRDGBufferRef,FRDGBufferRef)>;

struct RAFTSIMWATERDETAIL_API FRaftSimTotalDepthStepResult
{
    FRDGBufferRef State=nullptr; // accepted candidate or bit-exact original on rejection
    FRDGBufferRef Progress=nullptr; // float4(time hi,time lo,remaining seconds,next proposed dt)
    FRDGBufferRef Info=nullptr; // float4(accepted dt,attempted dt,first CFL,second CFL)
    FRDGBufferRef Diagnostics=nullptr; // uint4(first-stage bits,second-stage bits,candidate/clock bits,accepted 0/1)
    // Optional float4 per exterior face: accepted dt * trapezoidal FV flux.
    // Positive-axis orientation, per unit face length. Exactly zero on rejection.
    // Water/foam inventory ledger; momentum also has pressure/bed volume sources.
    FRDGBufferRef BoundaryVolume=nullptr;
    // Same-stage forces retained as graph-local references for diagnostic
    // consumers. No extra dispatch, copy, readback or ownership in normal use.
    FRDGBufferRef FirstPressureForce=nullptr,SecondPressureForce=nullptr;
    FRaftSimNonlinearPressureResult PressureStages[2];
    // Existing intermediates, exposed only for graph-local fault isolation.
    // No additional buffer, dispatch or readback is introduced here.
    FRDGBufferRef EulerState=nullptr,CandidateState=nullptr;
};

// One transactional SSP-RK2 trial, with both FV and nonhydrostatic pressure
// recomputed on each stage. Calls FractionForStage separately with that stage's
// actual state/rate/graph; never freezes a state-dependent breaking mask.
// InputProgress is one float4(time hi,time lo,remaining,proposed dt). Hi/lo time
// is compensated; rejected trials preserve both words and remaining exactly.
// Max dt1/120, CFL.4 and minimum retry dt1e-9 retain the CPU reference policy.
// Bits:1 component error,2 true residual,4 second-stage CFL,8 invalid state,
// 16 invalid/unrepresentable clock or exhausted minimum step. First-stage
// errors are fatal (next dt0); later trial rejection proposes half dt. Caller
// must obey flags, stop on exhaustion, enforce its total trial budget, and
// publish State/Progress only together after the completed graph. No readback.
// Foam advects with the same-stage shared mass flux and is positivity checked;
// it has no production/decay here. An optional explicit stage boundary provider
// couples exterior FV and prescribed-face pressure, with an accepted-only flux
// ledger. Temporal source policy, nonreflecting qualification, mean/window/frame
// ownership and GPU breaking classification remain separate integrations.
// IterationDispatchArgs is owned by the bounded interval: active records retain
// all 40 iterations; inactive records may suppress recurrence only. It does not
// bypass any trial/residual checks or authorize publishing an incomplete solve.
// An explicit immutable IntervalEndSeconds computes remaining time from that
// endpoint and the compensated accepted clock, avoiding float subtraction drift.
// Proposed dt rounds down if needed; residual time is evolved, never snapped or
// discarded. The legacy duration-only comparison path remains when omitted.
// Optional continuous shoreline reconstruction is identical at both RK stages;
// it does not bypass CFL, true-residual, rejection, clock or ledger checks.
RAFTSIMWATERDETAIL_API FRaftSimTotalDepthStepResult RaftSimTryTotalDepthStepGPU(
    FRDGBuilder& Graph,FRDGBufferRef InputState,FRDGBufferRef Bed,FRDGBufferRef InputProgress,
    FIntPoint Size,float CellMeters,bool bPeriodic,bool bSecondOrder,
    TFunctionRef<FRDGBufferRef(FRDGBuilder&,FRDGBufferRef,const FRaftSimTotalDepthTransportResult&)> FractionForStage,
    FString& Error,FRaftSimTotalDepthBoundaryProvider BoundaryForStage={},FRDGBufferRef IterationDispatchArgs=nullptr,
    TOptional<double> IntervalEndSeconds={},bool bContinuousShoreline=false,bool bUnscaledShoreline=false);
