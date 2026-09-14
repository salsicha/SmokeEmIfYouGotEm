#pragma once
#include "RaftSimTotalDepthAdvanceGPU.h"

// Admit a consecutive interval only after the previous GPU transaction completed
// successfully at exactly FirstSeconds. State and the cumulative accepted face
// ledger are aliased, never reinitialized; only interval counters and remaining
// time restart. The caller must retain all five records together and keep the
// same grid, bed, world faces, boundary mode and shoreline reconstruction.
// The persisted evolution bits reject switching models between intervals.
// This is not a moving-window remap
// or observation queue. No readback, clock snapping, gap filling or extrapolation.
// Nonrepresentable host times fail before dispatch. Invalid/pending/failed GPU
// records return fatal status2 and diagnostic bit64, retaining original state,
// clock (including remaining/proposed time), ledger and counters. Input buffers
// are immutable, so a refused request does not corrupt the previous transaction.
RAFTSIMWATERDETAIL_API FRaftSimTotalDepthAdvanceResult RaftSimBeginNextTotalDepthIntervalGPU(
    FRDGBuilder& Graph,const FRaftSimTotalDepthAdvanceResult& Previous,FIntPoint Size,
    double FirstSeconds,double SecondSeconds,FString& Error,bool bContinuousShoreline=false,bool bUnscaledShoreline=false);
