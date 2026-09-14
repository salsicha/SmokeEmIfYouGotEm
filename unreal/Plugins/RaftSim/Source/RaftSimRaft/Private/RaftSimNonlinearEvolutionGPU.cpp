#include "RaftSimNonlinearEvolutionGPU.h"
#include "RaftSimBreakingFrontGPU.h"
#include "RaftSimTotalDepthIntervalGPU.h"
#include "RaftSimTotalDepthStateGPU.h"
#include "RaftSimWindowSourceTransition.h"

bool FRaftSimNonlinearEvolutionGPU::Observe(TSharedPtr<const FRaftSimTotalDepthSource,ESPMode::ThreadSafe> Next,FString& Error)
{
    check(IsInRenderingThread());Error.Reset();
    if(HasFailed()){Error=Failure;return false;}
    if(Queue.Num() && Next==Queue.Last())return true;
    if(Capacity<2 || Capacity>64 || ReadbackRunAhead<0 || ReadbackRunAhead>2 || !Next || !Next->Validate(Error))
        return Fail(Error.IsEmpty()?TEXT("Invalid nonlinear observation or queue capacity"):Error,Error);
    if(Queue.Num())
    {
        const auto& Last=*Queue.Last();
        if(Next->OriginMeters!=Last.OriginMeters && Next->ClosingWindowSource)
        {
            const auto Closing=Next->ClosingWindowSource;FIntPoint Offset;
            if(!FRaftSimWindowSourceTransition::Validate(Last,*Closing,*Next,Offset,Error))return Fail(Error,Error);
            const bool AddClosing=Closing->SampleSeconds>Last.SampleSeconds;
            const double Span=Closing->SampleSeconds-Last.SampleSeconds;
            if(!FMath::IsFinite(float(Span)) || double(float(Span))!=Span)
                return Fail(TEXT("Closing observation interval exceeds exact clock representation"),Error);
            if(Queue.Num()+(AddClosing?2:1)>Capacity)
                return Fail(TEXT("Nonlinear queue cannot retain both window endpoints; no partial move accepted"),Error);
            if(AddClosing)Queue.Add(Closing);
            Queue.Add(MoveTemp(Next));return true;
        }
        if(Next->Revision<=Last.Revision || Next->SampleSeconds<=Last.SampleSeconds)
            return Fail(TEXT("Nonlinear observations must have increasing revision and native time"),Error);
        if(Next->Size!=Last.Size || Next->CellMeters!=Last.CellMeters || Next->OriginMeters!=Last.OriginMeters ||
            Next->Bed!=Last.Bed || Next->ExteriorBed!=Last.ExteriorBed)
            return Fail(TEXT("Nonlinear observation changes world window or bed; explicit state/face exchange required"),Error);
        const double Span=Next->SampleSeconds-Last.SampleSeconds;
        const float Hi=float(Last.SampleSeconds),Lo=float(Last.SampleSeconds-double(Hi));
        if(!FMath::IsFinite(float(Span)) || double(float(Span))!=Span ||
            double(Hi)+double(Lo)!=Last.SampleSeconds)
            return Fail(TEXT("Nonlinear observation interval exceeds exact clock representation"),Error);
    }
    if(Queue.Num()>=Capacity)
        return Fail(TEXT("Nonlinear observation queue full; unconsumed time retained, source not discarded"),Error);
    Queue.Add(MoveTemp(Next));return true;
}

bool FRaftSimNonlinearEvolutionGPU::Poll(FString& Error)
{
    check(IsInRenderingThread());Error.Reset();
    if(HasFailed()){Error=Failure;return false;}
    if(bMovePending)
    {
        if(!MoveRead.IsReady())return true;
        const auto* D=static_cast<const uint32*>(MoveRead.Lock(16));
        if(!D)return Fail(TEXT("Window-transfer diagnostics unavailable; old state retained"),Error);
        const bool Valid=D[0]==0 && D[1]==0 && D[2]==ExpectedOverlap && D[3]==16384-ExpectedOverlap;
        MoveRead.Unlock();bMovePending=false;
        if(!Valid)return Fail(TEXT("Window-transfer candidate invalid; old state and endpoints retained"),Error);
        State=MoveTemp(CandidateState);WindowExchange=MoveTemp(CandidateExchange);
        StateOriginMeters=Queue[1]->OriginMeters;
        Queue.RemoveAt(0,1,EAllowShrinking::No);++CompletedMoves;
    }
    if(!bReadbackPending || !ProgressRead.IsReady() || !SummaryRead.IsReady() || !DiagnosticsRead.IsReady())return true;
    const auto* P=static_cast<const FVector4f*>(ProgressRead.Lock(16));
    const auto* S=static_cast<const uint32*>(SummaryRead.Lock(16));
    const auto* D=static_cast<const uint32*>(DiagnosticsRead.Lock(16));
    if(!P || !S || !D)
    {
        if(P)ProgressRead.Unlock();if(S)SummaryRead.Unlock();if(D)DiagnosticsRead.Unlock();
        return Fail(TEXT("Nonlinear transaction readback unavailable"),Error);
    }
    LastProgress=*P;const uint32 Status=S[2],Mode=S[3],Accepted=S[1],Bits=D[0]|D[1]|D[2];
    ProgressRead.Unlock();SummaryRead.Unlock();DiagnosticsRead.Unlock();bReadbackPending=false;GraphsSinceReadback=0;
    if(Status==2 || Status==4 || Status>4 || Mode!=RaftSimTotalDepthEvolutionMode(true,bContinuousShoreline,bUnscaledShoreline) || LastProgress.ContainsNaN())
        return Fail(FString::Printf(TEXT("Nonlinear GPU interval failed: status%u bits%u remaining%.12g"),Status,Bits,LastProgress.Z),Error);
    // A rejected retry can be pending with nonzero diagnostics; do not clear it,
    // invent completion, or discard the retained remainder.
    if(Status==0)return true;
    if(Status!=1 || Bits || LastProgress.Z!=0 || double(LastProgress.X)+LastProgress.Y!=ActiveEndSeconds || Queue.Num()<2)
        return Fail(TEXT("Nonlinear GPU completion does not match its owned observation endpoint"),Error);
    CompletedSeconds=ActiveEndSeconds;++CompletedIntervals;AcceptedTrials+=Accepted;
    Queue.RemoveAt(0,1,EAllowShrinking::No);bIntervalActive=false;
    return true;
}

bool FRaftSimNonlinearEvolutionGPU::Pump(FRHICommandListImmediate& Cmd,int32 TrialsThisGraph,FString& Error)
{
    check(IsInRenderingThread());
    if(!Poll(Error))return false;
    if(TrialsThisGraph<1 || TrialsThisGraph>RaftSimMaxTotalDepthTrialsPerGraph)return Fail(TEXT("Invalid nonlinear graph trial budget"),Error);
    if(bMovePending || Queue.Num()<2 || (bReadbackPending && GraphsSinceReadback>=ReadbackRunAhead))return true;
    const auto First=Queue[0],Second=Queue[1];
    if(First->OriginMeters!=Second->OriginMeters)
    {
        if(bIntervalActive || !Second->ClosingWindowSource || First->SampleSeconds!=Second->SampleSeconds)
            return Fail(TEXT("Window transfer attempted before its old interval completed"),Error);
        const auto Shift=(Second->OriginMeters-First->OriginMeters)/First->CellMeters;
        const FIntPoint Offset(int32(Shift.X),int32(Shift.Y));
        FRDGBuilder Graph(Cmd);
        FRDGBufferRef OldState=State?Graph.RegisterExternalBuffer(State):CreateStructuredBuffer(Graph,TEXT("NonlinearOwner.InitialMoveState"),First->State);
        const auto Move=RaftSimTransferTotalDepthStateGPU(Graph,OldState,
            CreateStructuredBuffer(Graph,TEXT("NonlinearOwner.EnteringState"),Second->State),
            CreateStructuredBuffer(Graph,TEXT("NonlinearOwner.EnteringReference"),Second->Reference),
            First->Size,Offset,First->CellMeters,Error,WindowExchange?Graph.RegisterExternalBuffer(WindowExchange):nullptr);
        if(!Move.State){Graph.Execute();return Fail(Error,Error);}
        if(!State)
        {
            const float Hi=float(First->SampleSeconds),Lo=float(First->SampleSeconds-double(Hi));
            TArray<FVector4f> Clock={FVector4f(Hi,Lo,0,1.f/120.f)},Volume;Volume.Init(FVector4f(0,0,0,0),512);
            // Moving the initial packet accepts no physical trial. Match the
            // zero counters so the first real interval can be admitted normally.
            TArray<uint32> Info={0,0,1,RaftSimTotalDepthEvolutionMode(true,bContinuousShoreline,bUnscaledShoreline)},Flags={0,0,0,0};
            auto P=CreateStructuredBuffer(Graph,TEXT("NonlinearOwner.InitialMoveClock"),Clock);
            auto S=CreateStructuredBuffer(Graph,TEXT("NonlinearOwner.InitialMoveSummary"),Info);
            auto D=CreateStructuredBuffer(Graph,TEXT("NonlinearOwner.InitialMoveDiagnostics"),Flags);
            auto V=CreateStructuredBuffer(Graph,TEXT("NonlinearOwner.InitialMoveVolume"),Volume);
            Graph.QueueBufferExtraction(OldState,&State);Graph.QueueBufferExtraction(P,&Progress);
            Graph.QueueBufferExtraction(S,&Summary);Graph.QueueBufferExtraction(D,&Diagnostics);Graph.QueueBufferExtraction(V,&BoundaryVolume);
            CompletedSeconds=First->SampleSeconds;
            StateOriginMeters=First->OriginMeters;
        }
        Graph.QueueBufferExtraction(Move.State,&CandidateState);Graph.QueueBufferExtraction(Move.WindowExchange,&CandidateExchange);
        AddEnqueueCopyPass(Graph,&MoveRead,Move.Diagnostics,16);Graph.Execute();
        ExpectedOverlap=(First->Size.X-FMath::Abs(Offset.X))*(First->Size.Y-FMath::Abs(Offset.Y));
        bMovePending=true;++DispatchedGraphs;return true;
    }
    const bool Begin=!bIntervalActive;
    if(Begin)
    {
        if(!Boundary.Upload(Cmd,First,Error) || !Boundary.Upload(Cmd,Second,Error) || !Boundary.HasTemporalBracket())
            return Fail(Error.IsEmpty()?TEXT("Nonlinear owner lost its boundary bracket"):Error,Error);
    }
    FRDGBuilder Graph(Cmd);FRaftSimTotalDepthAdvanceResult Previous;
    if(State)
    {
        Previous.State=Graph.RegisterExternalBuffer(State);Previous.Progress=Graph.RegisterExternalBuffer(Progress);
        Previous.Summary=Graph.RegisterExternalBuffer(Summary);Previous.Diagnostics=Graph.RegisterExternalBuffer(Diagnostics);
        Previous.BoundaryVolume=Graph.RegisterExternalBuffer(BoundaryVolume);
        if(Begin)Previous=RaftSimBeginNextTotalDepthIntervalGPU(Graph,Previous,First->Size,First->SampleSeconds,Second->SampleSeconds,Error,bContinuousShoreline,bUnscaledShoreline);
    }
    else
    {
        // Initialize from the intended native total-depth packet exactly once.
        // The most recent uploaded mean is Second, so never use Boundary.State.
        Previous.State=CreateStructuredBuffer(Graph,TEXT("NonlinearOwner.InitialState"),First->State);
        StateOriginMeters=First->OriginMeters;
        const float Hi=float(First->SampleSeconds),Lo=float(First->SampleSeconds-double(Hi));
        TArray<FVector4f> Clock={FVector4f(Hi,Lo,float(Second->SampleSeconds-First->SampleSeconds),1.f/120.f)};
        Previous.Progress=CreateStructuredBuffer(Graph,TEXT("NonlinearOwner.InitialClock"),Clock);
    }
    if(!Previous.State){Graph.Execute();return Fail(Error,Error);}
    auto Select=[&](FRDGBuilder& G,FRDGBufferRef,const FRaftSimTotalDepthTransportResult& Stage)
    {return RaftSimClassifyBreakingFrontGPU(G,Stage.Geometry,Stage.HydroRate,Stage.Pairs,First->Size,First->CellMeters,false,Error).Fraction;};
    FRaftSimTotalDepthBoundaryProvider Provider=[&](FRDGBuilder& G,FRDGBufferRef,FRDGBufferRef P,FRDGBufferRef Info)
    {return Boundary.SampleBoundary(G,P,Info,Error).Input;};
    const auto R=RaftSimAdvanceTotalDepthGPU(Graph,Previous.State,Graph.RegisterExternalBuffer(Boundary.Bed),Previous.Progress,
        Previous.Summary,Previous.Diagnostics,First->Size,First->CellMeters,false,true,TrialsThisGraph,4096,Select,Error,Provider,Previous.BoundaryVolume,true,Second->SampleSeconds,bContinuousShoreline,bUnscaledShoreline);
    if(!R.State || !R.BoundaryVolume){Graph.Execute();return Fail(Error.IsEmpty()?TEXT("Nonlinear graph construction failed"):Error,Error);}
    Graph.QueueBufferExtraction(R.State,&State);Graph.QueueBufferExtraction(R.Progress,&Progress);
    Graph.QueueBufferExtraction(R.Summary,&Summary);Graph.QueueBufferExtraction(R.Diagnostics,&Diagnostics);
    Graph.QueueBufferExtraction(R.BoundaryVolume,&BoundaryVolume);
    const bool CaptureStatus=!bReadbackPending;
    if(CaptureStatus)
    {
        AddEnqueueCopyPass(Graph,&ProgressRead,R.Progress,16);AddEnqueueCopyPass(Graph,&SummaryRead,R.Summary,16);
        AddEnqueueCopyPass(Graph,&DiagnosticsRead,R.Diagnostics,16);
    }
    // The GPU transaction already preserves complete/failed intervals exactly.
    // Continue only this same immutable bracket while its earlier status copy
    // travels back; never recycle the pending readbacks or switch endpoints.
    // A completed earlier copy implies all later graphs were no-ops. At most
    // two additional graphs can be outstanding per readback snapshot.
    Graph.Execute();bIntervalActive=true;ActiveEndSeconds=Second->SampleSeconds;++DispatchedGraphs;
    if(CaptureStatus){bReadbackPending=true;GraphsSinceReadback=0;}
    else {++GraphsSinceReadback;++ContinuedGraphsWithoutReadback;}
    return true;
}
