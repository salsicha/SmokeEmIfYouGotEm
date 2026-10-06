#pragma once
#include "RaftSimTotalDepthSourceGPU.h"
#include "RaftSimTotalDepthAdvanceGPU.h"
#include "RHIGPUReadback.h"

// Render-thread cell-aligned moving-window evolution owner. Mean observations are a
// bounded FIFO, not replacements for evolving state. A bracket stays alive
// until its asynchronous GPU transaction confirms completion. A move requires
// an actual closing old-window observation at the entering source's instant.
class FRaftSimNonlinearEvolutionGPU
{
public:
    explicit FRaftSimNonlinearEvolutionGPU(int32 InCapacity=16,int32 InReadbackRunAhead=2,bool InContinuousShoreline=false,bool InUnscaledShoreline=false)
        :Capacity(InCapacity),bContinuousShoreline(InContinuousShoreline),bUnscaledShoreline(InUnscaledShoreline),ReadbackRunAhead(InReadbackRunAhead)
    {if(bContinuousShoreline && bUnscaledShoreline)Failure=TEXT("Owner shoreline models are mutually exclusive");}
    bool UsesContinuousShoreline() const {return bContinuousShoreline;}
    bool UsesUnscaledShoreline() const {return bUnscaledShoreline;}
    bool Observe(TSharedPtr<const FRaftSimTotalDepthSource,ESPMode::ThreadSafe> Next,FString& Error);
    bool Pump(FRHICommandListImmediate& Cmd,int32 TrialsThisGraph,FString& Error);
    bool Poll(FString& Error);
    int32 PendingObservations() const {return Queue.Num();}
    uint64 CompletedIntervals=0,CompletedMoves=0,DispatchedGraphs=0,AcceptedTrials=0;
    uint64 ContinuedGraphsWithoutReadback=0;
    double CompletedSeconds=0;
    FVector2f StateOriginMeters=FVector2f::ZeroVector;
    FVector4f LastProgress=FVector4f(0,0,0,0);
    TRefCountPtr<FRDGPooledBuffer> State,Progress,Summary,Diagnostics,BoundaryVolume;
    TRefCountPtr<FRDGPooledBuffer> WindowExchange;
    bool HasPendingReadback() const {return bReadbackPending || bMovePending;}
    bool HasFailed() const {return !Failure.IsEmpty();}
private:
    int32 Capacity;
    // Construction-time numerical model, retained through every interval/move.
    const bool bContinuousShoreline;
    const bool bUnscaledShoreline;
    int32 ReadbackRunAhead=2,GraphsSinceReadback=0;
    TArray<TSharedPtr<const FRaftSimTotalDepthSource,ESPMode::ThreadSafe>> Queue;
    FRaftSimTotalDepthSourceGPU Boundary;
    FRHIGPUBufferReadback ProgressRead{TEXT("NonlinearOwner.Progress")};
    FRHIGPUBufferReadback SummaryRead{TEXT("NonlinearOwner.Summary")};
    FRHIGPUBufferReadback DiagnosticsRead{TEXT("NonlinearOwner.Diagnostics")};
    FRHIGPUBufferReadback MoveRead{TEXT("NonlinearOwner.Move")};
    TRefCountPtr<FRDGPooledBuffer> CandidateState,CandidateExchange;
    bool bMovePending=false;
    uint32 ExpectedOverlap=0;
    bool bReadbackPending=false,bIntervalActive=false;
    double ActiveEndSeconds=0;
    FString Failure;
    bool Fail(const FString& Message,FString& Error){Failure=Message;Error=Message;return false;}
};
