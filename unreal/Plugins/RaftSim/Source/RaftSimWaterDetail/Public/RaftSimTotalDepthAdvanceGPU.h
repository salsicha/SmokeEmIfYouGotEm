#pragma once
#include "RaftSimTotalDepthStepGPU.h"

inline constexpr int32 RaftSimMaxTotalDepthTrialsPerGraph=16;

// Persisted transaction identity: bit0 owns open faces, bit1 selects the
// continuous shoreline polynomial; bit2 selects unscaled MC instead. The two
// model bits are mutually exclusive. Never change this identity in a history.
inline constexpr uint32 RaftSimTotalDepthEvolutionMode(bool Boundary,bool Continuous,bool Unscaled=false)
{return (Boundary?1u:0u)|(Continuous?2u:0u)|(Unscaled?4u:0u);}

struct RAFTSIMWATERDETAIL_API FRaftSimTotalDepthAdvanceResult
{
    FRDGBufferRef State=nullptr;
    FRDGBufferRef Progress=nullptr; // same compensated record as the single trial
    FRDGBufferRef Summary=nullptr; // uint4(cumulative trials,accepted,status,evolution mode bits)
    FRDGBufferRef Diagnostics=nullptr; // last effective trial, retained across inactive slots
    FRDGBufferRef BoundaryVolume=nullptr; // optional cumulative per-face accepted FV inventory, per unit face length
};

// Continue ONE requested interval with bounded graph work. PreviousSummary and
// PreviousDiagnostics are both null for an explicitly new interval, otherwise
// both are the previous result. State/progress/summary/diagnostics are one
// transaction with BoundaryVolume when present: retain/extract them together, never rebuild progress from wall
// time. Status:0 pending,1 complete,2 fatal trial,4 total trial budget exhausted.
// Terminal status is latched across calls; changing a limit does not reset it.
// Invalid boundary ownership/inventory overrides even a completed status with
// fatal status; corruption must never remain publishable as a complete frame.
// BoundaryForStage is optional for a NEW interval. Continued open intervals
// require its previous BoundaryVolume (float4 per face) and provider; closed
// intervals require neither. The GPU summary records this mode to reject a
// silent switch. Boundary inventory failure (Diagnostics[2] bit32) rejects the
// whole trial state/time/inventory transaction, latches fatal status and dt0.
// TrialsThisGraph is 1..16; TotalTrialLimit is 1..4096, cumulative across graphs.
// This batches the same individually accepted/retried steps, not a larger dt.
// Inactive slots use zero-work indirect pressure recurrence dispatches. All
// preparation/final checks and state/clock/inventory selection still execute.
// False bCullInactiveIterations retains the direct-dispatch comparison path.
// This does not add new elapsed time, drive game-thread ownership or resolve a
// render/contact frame. No CPU readback, no gameplay opt-in, no cost acceptance.
RAFTSIMWATERDETAIL_API FRaftSimTotalDepthAdvanceResult RaftSimAdvanceTotalDepthGPU(
    FRDGBuilder& Graph,FRDGBufferRef InputState,FRDGBufferRef Bed,FRDGBufferRef InputProgress,
    FRDGBufferRef PreviousSummary,FRDGBufferRef PreviousDiagnostics,FIntPoint Size,
    float CellMeters,bool bPeriodic,bool bSecondOrder,int32 TrialsThisGraph,int32 TotalTrialLimit,
    TFunctionRef<FRDGBufferRef(FRDGBuilder&,FRDGBufferRef,const FRaftSimTotalDepthTransportResult&)> FractionForStage,
    FString& Error,FRaftSimTotalDepthBoundaryProvider BoundaryForStage={},
    FRDGBufferRef PreviousBoundaryVolume=nullptr,bool bCullInactiveIterations=true,TOptional<double> IntervalEndSeconds={},
    bool bContinuousShoreline=false,bool bUnscaledShoreline=false);
