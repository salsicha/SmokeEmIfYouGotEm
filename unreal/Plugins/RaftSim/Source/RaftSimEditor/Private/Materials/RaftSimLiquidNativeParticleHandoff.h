#pragma once
#include "RaftSimLiquidParticleAssemblyAudit.h"
#include "RaftSimLiquidParticleExitGPU.h"
#include "NiagaraComputeExecutionContext.h"
#include "NiagaraDataSet.h"
#include "NiagaraGpuComputeDispatchInterface.h"
#include "NiagaraGPUInstanceCountManager.h"
#include "HAL/FileManager.h"
#include "RaftSimLiquidLifetime.h"

struct FRaftSimNativeHandoffSnapshot
{
    uint32 Capacity=0;
    TRefCountPtr<FRDGPooledBuffer> Words,Counts;
};

// Bounded one-generation native handoff probe, no readback during simulation.
// Caller reserves native capacity/dispatch before ticks and invokes only after
// the last aligned particle stage, before Niagara rebuilds its free-ID lists.
struct FRaftSimNativeParticleHandoff
{
    bool Issued=false;
    uint32 NativeStep=0;
    FGuid Generation;
    uint32 FloatComponents=0,IntComponents=0,IDComponent=0;
    FRaftSimNativeAssemblySample Receiving;
    TArray<FRaftSimNativeHandoffSnapshot> Before,After;
    bool AuditRetained=true;
    TRefCountPtr<FRDGPooledBuffer> SummaryControl,SummaryCounts,SummaryExitCounts;
    uint32 SummaryOwners=0;

    bool Issue(FRDGBuilder& Graph,FNiagaraGpuComputeDispatchInterface* Dispatch,
        TConstArrayView<FNiagaraComputeExecutionContext*> Contexts,const FRaftSimLiquidParticleRoutePlan& Plan,
        uint32 PositionComponent,uint32 InIDComponent,FString& Error,FRaftSimLiquidLifetime& Lifetime,const FRaftSimLiquidTickToken& Token,
        const FRaftSimLiquidParticleExitPlan* ExitPlan=nullptr,uint32 StepStartComponent=MAX_uint32,TConstArrayView<float> Volumes={},
        bool RetainFullAudit=true,TConstArrayView<uint32> DestinationLimits={})
    {
        if(Issued || Contexts.Num()!=int32(Plan.Owners)) { Error=TEXT("Invalid native handoff ownership phase");return false; }
        if(NativeStep!=Token.Step) { Error=TEXT("Native handoff step differs from generation token");return false; }
        if(!Lifetime.ClaimTransfer(Token,Error)) return false;
        Generation=Token.Generation;const uint32 TransferEpoch=Token.TransferEpoch;
        AuditRetained=RetainFullAudit;SummaryOwners=Contexts.Num();
        FloatComponents=Contexts[0]->MainDataSet->GetNumFloatComponents();IntComponents=Contexts[0]->MainDataSet->GetNumInt32Components();IDComponent=InIDComponent;
        const auto& Counter=Dispatch->GetGPUInstanceCounterManager().GetInstanceCountBuffer();
        TArray<FRaftSimLiquidNativeParticleTarget> Targets;
        TArray<uint32> Capacities,IDCapacities;uint32 NativeTag=0;
        if(!DestinationLimits.IsEmpty() && DestinationLimits.Num()!=Contexts.Num())
        { Error=TEXT("Every native destination requires a dispatch reservation limit");return false; }
        for(const auto* C:Contexts)
        {
            auto* D=C->MainDataSet->GetCurrentData();
            if(!D || C->MainDataSet->GetNumHalfComponents() || C->MainDataSet->GetNumFloatComponents()!=FloatComponents ||
                C->MainDataSet->GetNumInt32Components()!=IntComponents)
            { Error=TEXT("Native handoff dataset ABI mismatch");return false; }
            auto& T=Targets.AddDefaulted_GetRef();T.Capacity=D->GetNumInstancesAllocated();
            if(T.Capacity)
            {
                T.Floats=D->GetGPUBufferFloat().UAV;T.Integers=D->GetGPUBufferInt().UAV;T.IDToIndex=D->GetGPUIDToIndexTable().UAV;
                T.FloatStride=D->GetFloatStride()/4;T.IntStride=D->GetInt32Stride()/4;T.IDCapacity=D->GetGPUIDToIndexTable().NumBytes/4;
                T.CountOffset=D->GetGPUInstanceCountBufferOffset();T.NativeCounts=Counter.UAV;
            }
            Capacities.Add(T.Capacity?FMath::Min(T.Capacity,T.IDCapacity):1);
            if(!DestinationLimits.IsEmpty())
            {
                const uint32 Limit=DestinationLimits[Capacities.Num()-1];
                if(!Limit || Limit>Capacities.Last()) { Error=TEXT("Native destination dispatch reservation exceeds allocated storage");return false; }
                Capacities.Last()=Limit;
            }
            // Native ID slots are a separate namespace, often much larger than
            // live particle storage. Births legitimately use those high slots.
            IDCapacities.Add(T.Capacity?T.IDCapacity:1);
            NativeTag=FMath::Max(NativeTag,D->GetIDAcquireTag());
        }
        auto Snapshot=[&](TArray<FRaftSimNativeHandoffSnapshot>& Snapshots,TArray<FRaftSimLiquidParticleRoutePacket>& Packets)
        {
            Snapshots.SetNum(Contexts.Num());Packets.SetNum(Contexts.Num());
            const auto Uav=Counter.UAV;
            Graph.AddPass(RDG_EVENT_NAME("Native Handoff Counter Read Barrier"),ERDGPassFlags::None,
                [Uav](FRHICommandList& Cmd){Cmd.Transition(FRHITransitionInfo(Uav,ERHIAccess::UAVCompute,ERHIAccess::UAVCompute));});
            for(int32 I=0;I<Contexts.Num();++I)
            {
                auto* D=Contexts[I]->MainDataSet->GetCurrentData();auto& P=Packets[I];auto& S=Snapshots[I];
                S.Capacity=D->GetNumInstancesAllocated();
                if(S.Capacity)
                    P=RaftSimStageLiquidParticleRoutes(Graph,Plan,I,D->GetGPUBufferFloat().SRV,D->GetGPUBufferInt().SRV,Counter.UAV,
                        D->GetGPUInstanceCountBufferOffset(),D->GetFloatStride()/4,D->GetInt32Stride()/4,
                        FloatComponents,IntComponents,0,PositionComponent,S.Capacity,Error);
                else
                {
                    const uint32 Zero=0;const FUintVector4 Empty(0,0,0,0);TArray<uint32> Zeros;Zeros.Init(0,Contexts.Num()+3);
                    P.Words=CreateStructuredBuffer(Graph,TEXT("NativeHandoff.EmptyWords"),TConstArrayView<uint32>(&Zero,1));
                    P.Routes=CreateStructuredBuffer(Graph,TEXT("NativeHandoff.EmptyRoutes"),TConstArrayView<FUintVector4>(&Empty,1));
                    P.Counts=CreateStructuredBuffer(Graph,TEXT("NativeHandoff.EmptyCounts"),TConstArrayView<uint32>(Zeros));
                    P.FloatComponents=FloatComponents;P.IntComponents=IntComponents;
                }
                if(!P.Words) return false;
                if(AuditRetained)
                { Graph.QueueBufferExtraction(P.Words,&S.Words);Graph.QueueBufferExtraction(P.Counts,&S.Counts); }
            }
            return true;
        };
        TArray<FRaftSimLiquidParticleRoutePacket> Sources;
        if(!Snapshot(Before,Sources)) return false;
        TArray<FRaftSimLiquidParticleExitCandidates> Exits;
        if(ExitPlan)
        {
            if(Volumes.Num()!=Contexts.Num() || ExitPlan->Routing.Bounds!=Plan.Bounds)
            { Error=TEXT("Native retirement must use this exact physical route plan and every native particle volume");return false; }
            for(int32 I=0;I<Contexts.Num();++I)
            {
                auto E=RaftSimClassifyLiquidParticleExits(Graph,*ExitPlan,Sources[I],I,PositionComponent,StepStartComponent,Volumes[I],Error);
                if(!E.Records) return false;Exits.Add(E);
            }
        }
        auto A=RaftSimAssembleLiquidParticleDestinations(Graph,Sources,Capacities,Error,Exits);if(!A.Words) return false;
        auto H=RaftSimPrepareLiquidParticleHandles(Graph,A,IDCapacities,IDComponent,IDComponent+1,TransferEpoch,NativeTag,Error);if(!H.Handles) return false;
        if(!RaftSimCommitLiquidParticleAssembly(Graph,A,H,Targets,IDComponent,IDComponent+1,Error)) return false;
        // Runtime transfer uses precisely the same source staging, exit policy,
        // handle validation and atomic native commit. Only diagnostic retention
        // and the redundant postcommit full-state read are optional.
        if(AuditRetained)
        {
            Receiving.Adopt(Graph,A,H,IDComponent,NativeTag);
            Receiving.TransferEpoch=TransferEpoch;
            TArray<FRaftSimLiquidParticleRoutePacket> Written;
            if(!Snapshot(After,Written)) return false;
        }
        else
        {
            Graph.QueueBufferExtraction(A.Control,&SummaryControl);
            Graph.QueueBufferExtraction(A.Counts,&SummaryCounts);
            Graph.QueueBufferExtraction(A.ExitCounts,&SummaryExitCounts);
        }
        Issued=true;return true;
    }

    bool Save(FRHICommandListImmediate& Cmd,const FString& Directory,TSharedPtr<FJsonObject>& Record,FString& Error) const
    {
        if(!Issued) { Error=TEXT("Native handoff was not issued");return false; }
        Record=MakeShared<FJsonObject>();Record->SetBoolField(TEXT("issued"),true);
        Record->SetNumberField(TEXT("native_step"),NativeStep);
        Record->SetStringField(TEXT("simulation_generation"),Generation.ToString(EGuidFormats::DigitsWithHyphens));
        Record->SetBoolField(TEXT("full_audit_retained"),AuditRetained);
        Record->SetNumberField(TEXT("float_components"),FloatComponents);Record->SetNumberField(TEXT("int_components"),IntComponents);
        Record->SetNumberField(TEXT("id_component"),IDComponent);
        if(!AuditRetained)
        {
            // Fixed-size telemetry, not a replacement for exact particle audits.
            // No per-step CPU readback is introduced; Save runs after stopping.
            if(!SummaryControl || !SummaryCounts || !SummaryExitCounts) return false;
            const TArray<TPair<const TCHAR*,FRDGPooledBuffer*>> Buffers={
                {TEXT("control"),SummaryControl},{TEXT("counts"),SummaryCounts},{TEXT("exit_counts"),SummaryExitCounts}};
            const uint32 Words[]={4,SummaryOwners,SummaryOwners*5};
            for(int32 I=0;I<Buffers.Num();++I)
            {
                FRHIGPUBufferReadback Read(TEXT("NativeHandoff.Summary"));const auto& B=Buffers[I];
                Cmd.Transition(FRHITransitionInfo(B.Value->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
                Read.EnqueueCopy(Cmd,B.Value->GetRHI(),Words[I]*4);Cmd.SubmitAndBlockUntilGPUIdle();
                const auto* P=static_cast<const uint32*>(Read.Lock(Words[I]*4));if(!P) return false;
                TArray<TSharedPtr<FJsonValue>> Values;
                for(uint32 J=0;J<Words[I];++J) Values.Add(MakeShared<FJsonValueNumber>(P[J]));
                Read.Unlock();Record->SetArrayField(B.Key,Values);
            }
            Record->SetNumberField(TEXT("retained_summary_bytes"),(4+SummaryOwners*6)*4);
            return true;
        }
        const FString ReceivingDir=Directory/TEXT("handoff-receiving");IFileManager::Get().MakeDirectory(*ReceivingDir,true);
        TSharedPtr<FJsonObject> Assembly;
        if(!Receiving.Save(Cmd,ReceivingDir,Assembly,Error)) return false;
        Record->SetObjectField(TEXT("receiving"),Assembly);
        for(int32 Phase=0;Phase<2;++Phase)
        {
            const auto& Snapshots=Phase==0?Before:After;TArray<TSharedPtr<FJsonValue>> Records;
            for(int32 I=0;I<Snapshots.Num();++I)
            {
                const auto& S=Snapshots[I];auto R=MakeShared<FJsonObject>();R->SetNumberField(TEXT("owner"),I);R->SetNumberField(TEXT("capacity"),S.Capacity);
                const TArray<TPair<const TCHAR*,FRDGPooledBuffer*>> Buffers={{TEXT("words"),S.Words},{TEXT("counts"),S.Counts}};
                for(const auto& B:Buffers)
                {
                    const uint32 Size=FCString::Strcmp(B.Key,TEXT("words"))==0?S.Capacity*(FloatComponents+IntComponents)*4:uint32(Snapshots.Num()+3)*4;
                    TArray<uint8> Bytes;
                    if(Size)
                    {
                        FRHIGPUBufferReadback Read(TEXT("NativeHandoff.Snapshot"));
                        Cmd.Transition(FRHITransitionInfo(B.Value->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
                        Read.EnqueueCopy(Cmd,B.Value->GetRHI(),Size);Cmd.SubmitAndBlockUntilGPUIdle();
                        const auto* P=static_cast<const uint8*>(Read.Lock(Size));if(!P) return false;Bytes.Append(P,Size);Read.Unlock();
                    }
                    const FString Name=FString::Printf(TEXT("handoff-%s-%03d-%s.bin"),Phase==0?TEXT("before"):TEXT("after"),I,B.Key);
                    if(FPaths::FileExists(Directory/Name) || !FFileHelper::SaveArrayToFile(Bytes,*(Directory/Name))) return false;
                    R->SetStringField(B.Key,Name);
                }
                Records.Add(MakeShared<FJsonValueObject>(R));
            }
            Record->SetArrayField(Phase==0?TEXT("before"):TEXT("after"),Records);
        }
        return true;
    }
};
