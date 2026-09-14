#pragma once
#include "CoreMinimal.h"
#include "RenderGraphFwd.h"

struct RAFTSIMWATERDETAIL_API FRaftSimTotalDepthTransportResult
{
    FRDGBufferRef HydroRate=nullptr; // float4(h_t,hu_t,hv_t,foam_t), shared-flux foam advection
    FRDGBufferRef Geometry=nullptr; // float2(h,bed) from this same state
    FRDGBufferRef PhysicalBedSlope=nullptr; // float2, independent of wetness
    FRDGBufferRef Pairs=nullptr; // uint positive-x/y FINAL reconstructed wet graph
    FRDGBufferRef CFL=nullptr; // float4(max signal x,max signal y,.4*dx/sum,0)
    FRDGBufferRef Diagnostics=nullptr; // uint4(bad inputs,bad intermediates,0,0)
    FRDGBufferRef BoundaryFlux=nullptr; // optional float4 water/momentum/foam, positive-axis oriented
    // Existing scratch buffers exposed for opt-in diagnostics; no extra allocation/readback.
    FRDGBufferRef RawX=nullptr,RawY=nullptr,SlopeX=nullptr,SlopeY=nullptr,Velocity=nullptr;
};

// Conservative total-depth MC/hydrostatic Rusanov transport. State=float4
// (h,hu,hv,foam), Bed=float. No depth floor, velocity cap, state repair or
// readback. A single flattening decision uses the ORIGINAL MC polynomial.
// Closed edges reflect normal momentum; periodic edges wrap. Optional exterior
// buffers supply constant ghost centres one cell outside: west Ny, east Ny,
// south Nx, north Nx. State is float4(h,hu,hv,foam), bed float. Both required,
// incompatible with periodic. Interior state is never overwritten. BoundaryFlux
// uses the same packed order; negate west/south for outward flux. Pressure/bed
// source terms prevent general momentum conservation. Exterior pressure closure,
// foam production and RK acceptance are not supplied by this transport API.
// Foam uses upwind donor concentration and the same shared water mass flux.
// The returned graph/rate/geometry/slope form one coherent pressure input.
// Reject any Diagnostics error before applying this rate or publishing state.
// bContinuousShoreline is an opt-in candidate that blends the original slopes
// by surviving owning-face water fractions. It never changes cell averages.
// Keep the choice fixed throughout an evolved history; false preserves the
// original binary control until full-history/physical/cost qualification.
// bUnscaledShoreline instead keeps the original MC polynomial with no second
// shoreline pass. Diagnostic-only, mutually exclusive with bContinuousShoreline.
// Both flags default false; normal callers and historical model identity stay.
RAFTSIMWATERDETAIL_API FRaftSimTotalDepthTransportResult RaftSimTotalDepthTransportGPU(
    FRDGBuilder& Graph,FRDGBufferRef State,FRDGBufferRef Bed,FIntPoint Size,
    float CellMeters,bool bPeriodic,bool bSecondOrder,FString& Error,
    FRDGBufferRef ExteriorState=nullptr,FRDGBufferRef ExteriorBed=nullptr,bool bContinuousShoreline=false,
    bool bUnscaledShoreline=false);
