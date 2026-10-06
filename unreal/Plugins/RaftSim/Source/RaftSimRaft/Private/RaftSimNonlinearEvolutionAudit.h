#pragma once
#include "RaftSimNonlinearEvolutionGPU.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

// Explicit normal-map diagnostic: evolves the actual immutable source stream,
// but does not replace the displayed/contact surface or qualify scene FPS.
struct FRaftSimNonlinearEvolutionAudit
{
    FRaftSimNonlinearEvolutionGPU Owner;
    TArray<TSharedPtr<const FRaftSimTotalDepthSource,ESPMode::ThreadSafe>> Observations;
    FRHIGPUBufferReadback StateRead{TEXT("LiveNonlinear.State")},LedgerRead{TEXT("LiveNonlinear.Ledger")},ExchangeRead{TEXT("LiveNonlinear.WindowExchange")},
        ClockRead{TEXT("LiveNonlinear.Clock")},SummaryRead{TEXT("LiveNonlinear.Summary")},DiagnosticsRead{TEXT("LiveNonlinear.Diagnostics")};
    FString Path,Failure;
    bool bCapturing=false,bDone=false;
    int32 TargetIntervals=4,TargetMoves=0,TrialsPerGraph=4;
    bool bExchangeCaptured=false;
    TArray<FVector4f> CapturedExchange;
    bool RequestedComplete() const {return Owner.CompletedIntervals>=uint64(TargetIntervals) && Owner.CompletedMoves>=uint64(TargetMoves);}
    explicit FRaftSimNonlinearEvolutionAudit(const FString& Output):Path(Output)
    {
        if(FPaths::FileExists(Path)){Failure=TEXT("Refusing existing nonlinear audit output");bDone=true;UE_LOG(LogTemp,Error,TEXT("%s: %s"),*Failure,*Path);}
        FParse::Value(FCommandLine::Get(),TEXT("RaftSimNonlinearEvolutionIntervals="),TargetIntervals);
        FParse::Value(FCommandLine::Get(),TEXT("RaftSimNonlinearEvolutionMoves="),TargetMoves);
        FParse::Value(FCommandLine::Get(),TEXT("RaftSimNonlinearEvolutionTrialsPerGraph="),TrialsPerGraph);
        if(TargetIntervals<1 || TargetIntervals>128 || TargetMoves<0 || TargetMoves>32 || TrialsPerGraph<1 || TrialsPerGraph>RaftSimMaxTotalDepthTrialsPerGraph)
        {Failure=TEXT("Invalid bounded nonlinear audit target");bDone=true;UE_LOG(LogTemp,Error,TEXT("%s"),*Failure);}
    }
    static TArray<TSharedPtr<FJsonValue>> Vectors(const TArray<FVector4f>& Values)
    {
        TArray<TSharedPtr<FJsonValue>> Out;Out.Reserve(4*Values.Num());
        for(const auto& V:Values)for(int32 K=0;K<4;++K)
        {
            if(FMath::IsFinite(V[K]))Out.Add(MakeShared<FJsonValueNumber>(V[K]));
            else Out.Add(MakeShared<FJsonValueNull>());
        }
        return Out;
    }
    static TArray<TSharedPtr<FJsonValue>> Scalars(const TArray<float>& Values)
    {TArray<TSharedPtr<FJsonValue>> Out;for(float V:Values)Out.Add(MakeShared<FJsonValueNumber>(V));return Out;}
    void Tick(FRHICommandListImmediate& Cmd,TSharedPtr<const FRaftSimTotalDepthSource,ESPMode::ThreadSafe> Source)
    {
        if(bDone)return;
        if(bCapturing){Poll();return;}
        FString Error;
        if(!Owner.Poll(Error))Failure=Error;
        if(Failure.IsEmpty() && !RequestedComplete() && (!Observations.Num() || Observations.Last()!=Source))
        {
            // Capture only bounded accepted inputs; rejected source identity is
            // described by Failure and does not overwrite the retained queue.
            if(Observations.Num()>=254)Failure=TEXT("Bounded nonlinear capture source capacity reached; no inputs discarded");
            else if(!Owner.Observe(Source,Error))Failure=Error;
            else
            {
                if(Source->ClosingWindowSource && Observations.Num() && Source->OriginMeters!=Observations.Last()->OriginMeters &&
                    Source->ClosingWindowSource->SampleSeconds>Observations.Last()->SampleSeconds)
                    Observations.Add(Source->ClosingWindowSource);
                Observations.Add(Source);
            }
        }
        if(Failure.IsEmpty() && !RequestedComplete() && !Owner.Pump(Cmd,TrialsPerGraph,Error))Failure=Error;
        if(Failure.IsEmpty() && !RequestedComplete())return;
        if(!Owner.State){Finish({}, {}, {}, {}, {});return;}
        FRDGBuilder Graph(Cmd);
        AddEnqueueCopyPass(Graph,&StateRead,Graph.RegisterExternalBuffer(Owner.State),128*128*16);
        AddEnqueueCopyPass(Graph,&LedgerRead,Graph.RegisterExternalBuffer(Owner.BoundaryVolume),512*16);
        AddEnqueueCopyPass(Graph,&ClockRead,Graph.RegisterExternalBuffer(Owner.Progress),16);
        AddEnqueueCopyPass(Graph,&SummaryRead,Graph.RegisterExternalBuffer(Owner.Summary),16);
        AddEnqueueCopyPass(Graph,&DiagnosticsRead,Graph.RegisterExternalBuffer(Owner.Diagnostics),16);
        if(Owner.WindowExchange)
        {AddEnqueueCopyPass(Graph,&ExchangeRead,Graph.RegisterExternalBuffer(Owner.WindowExchange),128*128*16);bExchangeCaptured=true;}
        Graph.Execute();bCapturing=true;
    }
    void Poll()
    {
        if(!StateRead.IsReady() || !LedgerRead.IsReady() || !ClockRead.IsReady() || !SummaryRead.IsReady() || !DiagnosticsRead.IsReady() ||
            (bExchangeCaptured && !ExchangeRead.IsReady()))return;
        TArray<FVector4f> State,Ledger,Clock;TArray<uint32> Summary,Diagnostics;
        auto Read=[&](FRHIGPUBufferReadback& R,auto& Values,int32 Count)
        {
            const uint32 Bytes=Count*sizeof(Values[0]);const void* Data=R.Lock(Bytes);
            if(!Data){Failure=TEXT("Nonlinear audit readback failed");return;}
            Values.SetNumUninitialized(Count);FMemory::Memcpy(Values.GetData(),Data,Bytes);R.Unlock();
        };
        Read(StateRead,State,128*128);Read(LedgerRead,Ledger,512);Read(ClockRead,Clock,1);Read(SummaryRead,Summary,4);Read(DiagnosticsRead,Diagnostics,4);
        if(bExchangeCaptured)Read(ExchangeRead,CapturedExchange,128*128);
        else CapturedExchange.Init(FVector4f(0,0,0,0),128*128);
        Finish(State,Ledger,Clock,Summary,Diagnostics);
    }
    void Finish(const TArray<FVector4f>& State,const TArray<FVector4f>& Ledger,const TArray<FVector4f>& Clock,
        const TArray<uint32>& Summary,const TArray<uint32>& Diagnostics)
    {
        auto R=MakeShared<FJsonObject>();R->SetStringField(TEXT("schema"),TEXT("raftsim.live_nonlinear_owner_audit.v1"));
        R->SetStringField(TEXT("scope"),TEXT("Actual normal-map source stream, retained hybrid GPU evolution with explicit same-time moving control volumes. No outer-domain wave/foam return coupling, display/contact replacement, long-time, visual or FPS acceptance."));
        R->SetStringField(TEXT("failure"),Failure);R->SetBoolField(TEXT("completed_requested_intervals"),Failure.IsEmpty() && RequestedComplete());
        R->SetNumberField(TEXT("requested_intervals"),TargetIntervals);R->SetNumberField(TEXT("requested_moves"),TargetMoves);
        R->SetNumberField(TEXT("trials_per_graph"),TrialsPerGraph);
        R->SetNumberField(TEXT("completed_moves"),Owner.CompletedMoves);
        R->SetArrayField(TEXT("state_origin_meters"),Scalars({Owner.StateOriginMeters.X,Owner.StateOriginMeters.Y}));
        R->SetArrayField(TEXT("window_exchange"),Vectors(CapturedExchange));
        R->SetNumberField(TEXT("completed_intervals"),Owner.CompletedIntervals);R->SetNumberField(TEXT("completed_native_seconds"),Owner.CompletedSeconds);
        R->SetNumberField(TEXT("accepted_trials_in_completed_intervals"),Owner.AcceptedTrials);R->SetNumberField(TEXT("graphs"),Owner.DispatchedGraphs);
        R->SetNumberField(TEXT("continued_graphs_without_readback"),Owner.ContinuedGraphsWithoutReadback);
        R->SetNumberField(TEXT("retained_observations"),Owner.PendingObservations());R->SetBoolField(TEXT("owner_readback_pending"),Owner.HasPendingReadback());
        R->SetArrayField(TEXT("state"),Vectors(State));R->SetArrayField(TEXT("cumulative_boundary_volume"),Vectors(Ledger));R->SetArrayField(TEXT("progress"),Vectors(Clock));
        auto UInts=[](const TArray<uint32>& V){TArray<TSharedPtr<FJsonValue>> Out;for(auto X:V)Out.Add(MakeShared<FJsonValueNumber>(X));return Out;};
        R->SetArrayField(TEXT("summary"),UInts(Summary));R->SetArrayField(TEXT("diagnostics"),UInts(Diagnostics));
        TArray<TSharedPtr<FJsonValue>> Inputs;
        for(const auto& S:Observations)
        {
            auto O=MakeShared<FJsonObject>();O->SetNumberField(TEXT("revision"),S->Revision);O->SetNumberField(TEXT("native_seconds"),S->SampleSeconds);
            O->SetNumberField(TEXT("nx"),S->Size.X);O->SetNumberField(TEXT("ny"),S->Size.Y);O->SetNumberField(TEXT("cell_meters"),S->CellMeters);
            O->SetNumberField(TEXT("origin_x"),S->OriginMeters.X);O->SetNumberField(TEXT("origin_y"),S->OriginMeters.Y);
            O->SetArrayField(TEXT("state"),Vectors(S->State));O->SetArrayField(TEXT("bed"),Scalars(S->Bed));
            TArray<TSharedPtr<FJsonValue>> Reference;Reference.Reserve(2*S->Reference.Num());
            for(const auto& V:S->Reference){Reference.Add(MakeShared<FJsonValueNumber>(V.X));Reference.Add(MakeShared<FJsonValueNumber>(V.Y));}
            O->SetArrayField(TEXT("reference"),Reference);
            O->SetArrayField(TEXT("exterior_state"),Vectors(S->ExteriorState));O->SetArrayField(TEXT("exterior_bed"),Scalars(S->ExteriorBed));
            O->SetArrayField(TEXT("face_normal_velocity"),Scalars(S->FaceNormalVelocity));
            if(!S->PressureStencilState.IsEmpty())
            {
                O->SetNumberField(TEXT("pressure_stencil_width"),3);
                O->SetArrayField(TEXT("pressure_stencil_state"),Vectors(S->PressureStencilState));
                O->SetArrayField(TEXT("pressure_stencil_bed"),Scalars(S->PressureStencilBed));
            }
            Inputs.Add(MakeShared<FJsonValueObject>(O));
        }
        R->SetArrayField(TEXT("observations"),Inputs);
        FString Json;auto Writer=TJsonWriterFactory<>::Create(&Json);
        const bool Written=FJsonSerializer::Serialize(R,Writer) && !FPaths::FileExists(Path) && FFileHelper::SaveStringToFile(Json,*Path);
        UE_LOG(LogTemp,Display,TEXT("Live nonlinear owner audit: wrote=%d completed=%llu graphs=%llu failure=%s output=%s; diagnostic only, playable surface unchanged"),
            Written,Owner.CompletedIntervals,Owner.DispatchedGraphs,*Failure,*Path);
        bDone=true;
    }
};
