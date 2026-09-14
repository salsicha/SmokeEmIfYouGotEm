#pragma once
#include "RaftSimTotalDepthSource.h"
#include "RenderGraphUtils.h"
#include "RenderingThread.h"
#include "RaftSimTemporalBoundaryGPU.h"

// Render-thread source owner. Revisions upload once, independently of capture
// flags. These are mean/entering-state inputs; never overwrite evolving h/M.
struct FRaftSimTotalDepthSourceGPU
{
    TRefCountPtr<FRDGPooledBuffer> State,Bed,Reference,ExteriorState,ExteriorBed,FaceNormalVelocity;
    TRefCountPtr<FRDGPooledBuffer> PreviousExteriorState,PreviousExteriorBed,PreviousFaceNormalVelocity;
    TSharedPtr<const FRaftSimTotalDepthSource,ESPMode::ThreadSafe> Source;
    TSharedPtr<const FRaftSimTotalDepthSource,ESPMode::ThreadSafe> PreviousSource;
    uint64 Uploads=0;
    bool HasTemporalBracket() const {return PreviousSource.IsValid();}
    FRaftSimTemporalBoundaryResult SampleBoundary(FRDGBuilder& Graph,FRDGBufferRef Progress,FRDGBufferRef Info,FString& Error) const
    {
        if(!HasTemporalBracket()){Error=TEXT("Live boundary has no same-window increasing-time observation bracket");return {};}
        const FRaftSimTemporalBoundaryEndpoint A{Graph.RegisterExternalBuffer(PreviousExteriorState),Graph.RegisterExternalBuffer(PreviousExteriorBed),
            Graph.RegisterExternalBuffer(PreviousFaceNormalVelocity),PreviousSource->SampleSeconds};
        const FRaftSimTemporalBoundaryEndpoint B{Graph.RegisterExternalBuffer(ExteriorState),Graph.RegisterExternalBuffer(ExteriorBed),
            Graph.RegisterExternalBuffer(FaceNormalVelocity),Source->SampleSeconds};
        return RaftSimSampleTemporalBoundaryGPU(Graph,A,B,Progress,Info,Source->Size,Error);
    }
    bool Upload(FRHICommandListImmediate& Cmd,TSharedPtr<const FRaftSimTotalDepthSource,ESPMode::ThreadSafe> Next,FString& Error)
    {
        check(IsInRenderingThread());Error.Reset();
        if(Next==Source && Next)return true;
        if(!Next || (Source && Next->Revision<=Source->Revision) || !Next->Validate(Error))
        {if(Error.IsEmpty())Error=TEXT("Invalid or stale live total-depth source revision");return false;}
        FRDGBuilder Graph(Cmd);
        auto S=CreateStructuredBuffer(Graph,TEXT("LiveTotalSource.State"),Next->State);
        auto B=CreateStructuredBuffer(Graph,TEXT("LiveTotalSource.Bed"),Next->Bed);
        auto R=CreateStructuredBuffer(Graph,TEXT("LiveTotalSource.Reference"),Next->Reference);
        auto ES=CreateStructuredBuffer(Graph,TEXT("LiveTotalSource.ExteriorState"),Next->ExteriorState);
        auto EB=CreateStructuredBuffer(Graph,TEXT("LiveTotalSource.ExteriorBed"),Next->ExteriorBed);
        auto FV=CreateStructuredBuffer(Graph,TEXT("LiveTotalSource.FaceNormalVelocity"),Next->FaceNormalVelocity);
        const auto OldES=ExteriorState,OldEB=ExteriorBed,OldFV=FaceNormalVelocity;
        Graph.QueueBufferExtraction(S,&State);Graph.QueueBufferExtraction(B,&Bed);Graph.QueueBufferExtraction(R,&Reference);
        Graph.QueueBufferExtraction(ES,&ExteriorState);Graph.QueueBufferExtraction(EB,&ExteriorBed);
        Graph.QueueBufferExtraction(FV,&FaceNormalVelocity);Graph.Execute();
        // A moved crop or unchanged/regressed clock is NOT a temporal bracket.
        // The future evolution owner must obtain fresh paired observations;
        // never extrapolate new faces or invent a zero time derivative.
        if(Source && Next->OriginMeters==Source->OriginMeters && Next->SampleSeconds>Source->SampleSeconds && Next->ExteriorBed==Source->ExteriorBed)
        {PreviousSource=Source;PreviousExteriorState=OldES;PreviousExteriorBed=OldEB;PreviousFaceNormalVelocity=OldFV;}
        else {PreviousSource.Reset();PreviousExteriorState.SafeRelease();PreviousExteriorBed.SafeRelease();PreviousFaceNormalVelocity.SafeRelease();}
        Source=MoveTemp(Next);++Uploads;return true;
    }
};
