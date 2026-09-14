#pragma once
#include "RaftSimTotalDepthStepGPU.h"

struct FRaftSimTemporalBoundaryEndpoint
{
    FRDGBufferRef State=nullptr,Bed=nullptr,FaceNormalVelocity=nullptr;
    double Seconds=0;
};
struct FRaftSimTemporalBoundaryResult
{
    FRaftSimTotalDepthBoundaryInput Input;
    FRDGBufferRef Diagnostics=nullptr; // uint4: invalid time, state, bed, face trace
};

// A declared piecewise-linear observation bracket, not a radiation condition.
// Both endpoints must describe the SAME world faces and immutable bed. Face
// normal velocities are independent observations, never inferred from ghosts.
// Sample actual compensated Progress.xy (+ Info.y for stage2); no extrapolation,
// endpoint clamping, interior overwrite, CPU readback or invented time derivative.
// Face acceleration is the secant of these observations within this bracket.
// Invalid samples emit NaN boundary input and diagnostics, so the trial rejects.
RAFTSIMWATERDETAIL_API FRaftSimTemporalBoundaryResult RaftSimSampleTemporalBoundaryGPU(
    FRDGBuilder& Graph,const FRaftSimTemporalBoundaryEndpoint& First,const FRaftSimTemporalBoundaryEndpoint& Second,
    FRDGBufferRef Progress,FRDGBufferRef TrialInfo,FIntPoint Size,FString& Error);
