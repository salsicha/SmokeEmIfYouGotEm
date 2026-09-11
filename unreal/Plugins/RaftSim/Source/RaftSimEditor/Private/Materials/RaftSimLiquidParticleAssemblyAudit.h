#pragma once
#include "RaftSimLiquidParticleRoutingGPU.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "RHIGPUReadback.h"
#include "Misc/FileHelper.h"
#include "Dom/JsonObject.h"

// Diagnostic readback after simulation stops. Production assembly itself does
// not read back counts or payloads and does not mutate the native sources.
struct FRaftSimNativeAssemblySample
{
    TRefCountPtr<FRDGPooledBuffer> Words,References,Counts,Control;
    TRefCountPtr<FRDGPooledBuffer> Handles,IDToIndex,FreeIDs,FreeCounts;
    TRefCountPtr<FRDGPooledBuffer> ExitWords,ExitReferences,ExitRecords,ExitCounts;
    TArray<uint32> ExitCapacities;
    TArray<float> ExitVolumes;
    uint32 TotalExitCapacity=0;
    TArray<uint32> Capacities;
    TArray<uint32> IDCapacities;
    uint32 TotalCapacity=0,FloatComponents=0,IntComponents=0;
    uint32 IDComponent=MAX_uint32,NativeTag=0,TransferEpoch=1;
    void Adopt(FRDGBuilder& Graph,const FRaftSimLiquidParticleAssembly& A,const FRaftSimLiquidParticleHandles& H,
        uint32 InIDComponent,uint32 InNativeTag)
    {
        Capacities=A.DestinationCapacities;TotalCapacity=A.TotalCapacity;FloatComponents=A.FloatComponents;IntComponents=A.IntComponents;
        IDComponent=InIDComponent;NativeTag=InNativeTag;
        IDCapacities=H.IDCapacities;
        Graph.QueueBufferExtraction(A.Words,&Words);Graph.QueueBufferExtraction(A.References,&References);
        Graph.QueueBufferExtraction(A.Counts,&Counts);Graph.QueueBufferExtraction(A.Control,&Control);
        Graph.QueueBufferExtraction(H.Handles,&Handles);Graph.QueueBufferExtraction(H.IDToIndex,&IDToIndex);
        Graph.QueueBufferExtraction(H.FreeIDs,&FreeIDs);Graph.QueueBufferExtraction(H.FreeCounts,&FreeCounts);
        if(!A.ExitParticleVolumesM3.IsEmpty())
        {
            ExitVolumes=A.ExitParticleVolumesM3;ExitCapacities=A.ExitSourceCapacities;TotalExitCapacity=A.TotalExitCapacity;
            Graph.QueueBufferExtraction(A.ExitWords,&ExitWords);Graph.QueueBufferExtraction(A.ExitReferences,&ExitReferences);
            Graph.QueueBufferExtraction(A.ExitRecords,&ExitRecords);Graph.QueueBufferExtraction(A.ExitCounts,&ExitCounts);
        }
    }
    bool Capture(FRDGBuilder& Graph,TConstArrayView<FRaftSimLiquidParticleRoutePacket> Sources,FString& Error,
        uint32 InIDComponent=MAX_uint32,uint32 InNativeTag=0)
    {
        Capacities.Reset();
        // This bounded packet probe reserves every source particle as potential
        // incoming capacity at every destination, including empty native owners.
        // It is not a production allocation policy or native dispatch budget.
        uint32 Limit=0;for(const auto& S:Sources) Limit+=S.Capacity;
        if(Limit==0 || Limit>262144) { Error=TEXT("Assembly probe capacity unsupported");return false; }
        Capacities.Init(Limit,Sources.Num());
        auto A=RaftSimAssembleLiquidParticleDestinations(Graph,Sources,Capacities,Error);
        if(!A.Words) return false;
        TotalCapacity=A.TotalCapacity;FloatComponents=A.FloatComponents;IntComponents=A.IntComponents;
        IDComponent=InIDComponent;NativeTag=InNativeTag;
        if(IDComponent!=MAX_uint32)
        {
            auto H=RaftSimPrepareLiquidParticleHandles(Graph,A,Capacities,IDComponent,IDComponent+1,TransferEpoch,NativeTag,Error);
            if(!H.Handles) return false;
            IDCapacities=H.IDCapacities;
            Graph.QueueBufferExtraction(H.Handles,&Handles);Graph.QueueBufferExtraction(H.IDToIndex,&IDToIndex);
            Graph.QueueBufferExtraction(H.FreeIDs,&FreeIDs);Graph.QueueBufferExtraction(H.FreeCounts,&FreeCounts);
        }
        Graph.QueueBufferExtraction(A.Words,&Words);Graph.QueueBufferExtraction(A.References,&References);
        Graph.QueueBufferExtraction(A.Counts,&Counts);Graph.QueueBufferExtraction(A.Control,&Control);return true;
    }
    bool Save(FRHICommandListImmediate& Cmd,const FString& Directory,TSharedPtr<FJsonObject>& Record,FString& Error) const
    {
        if(!Words || !References || !Counts || !Control) { Error=TEXT("Missing native receiving assembly snapshot");return false; }
        Record=MakeShared<FJsonObject>();
        Record->SetNumberField(TEXT("total_capacity"),TotalCapacity);
        Record->SetNumberField(TEXT("float_components"),FloatComponents);Record->SetNumberField(TEXT("int_components"),IntComponents);
        TArray<TSharedPtr<FJsonValue>> Caps;for(uint32 C:Capacities) Caps.Add(MakeShared<FJsonValueNumber>(C));
        Record->SetArrayField(TEXT("destination_capacities"),Caps);Record->SetBoolField(TEXT("native_committed"),false);
        TArray<TPair<const TCHAR*,FRDGPooledBuffer*>> Buffers={{TEXT("words"),Words},{TEXT("references"),References},{TEXT("counts"),Counts},{TEXT("control"),Control}};
        TArray<uint32> Sizes={TotalCapacity*(FloatComponents+IntComponents)*4,TotalCapacity*8,uint32(Capacities.Num())*4,16};
        Record->SetBoolField(TEXT("handles_prepared"),IDComponent!=MAX_uint32);
        Record->SetBoolField(TEXT("exit_ledger_prepared"),!ExitVolumes.IsEmpty());
        if(!ExitVolumes.IsEmpty())
        {
            if(!ExitWords || !ExitReferences || !ExitRecords || !ExitCounts || ExitVolumes.Num()!=Capacities.Num() ||
                ExitCapacities.Num()!=Capacities.Num()) return false;
            Record->SetNumberField(TEXT("total_exit_capacity"),TotalExitCapacity);
            TArray<TSharedPtr<FJsonValue>> Limits,Volumes;
            for(uint32 C:ExitCapacities) Limits.Add(MakeShared<FJsonValueNumber>(C));
            for(float V:ExitVolumes) Volumes.Add(MakeShared<FJsonValueNumber>(V));
            Record->SetArrayField(TEXT("exit_source_capacities"),Limits);Record->SetArrayField(TEXT("exit_particle_volumes_m3"),Volumes);
            Buffers.Append({{TEXT("exit_words"),ExitWords},{TEXT("exit_references"),ExitReferences},{TEXT("exit_records"),ExitRecords},{TEXT("exit_counts"),ExitCounts}});
            Sizes.Append({TotalExitCapacity*(FloatComponents+IntComponents)*4,TotalExitCapacity*8,TotalExitCapacity*16,uint32(Capacities.Num())*5*4});
        }
        if(IDComponent!=MAX_uint32)
        {
            if(!Handles || !IDToIndex || !FreeIDs || !FreeCounts) return false;
            Record->SetNumberField(TEXT("id_component"),IDComponent);Record->SetNumberField(TEXT("native_acquire_tag"),NativeTag);
            Record->SetNumberField(TEXT("transfer_epoch"),TransferEpoch);
            uint32 TotalIDs=0;TArray<TSharedPtr<FJsonValue>> IDLimits;
            for(uint32 C:IDCapacities) { TotalIDs+=C;IDLimits.Add(MakeShared<FJsonValueNumber>(C)); }
            Record->SetArrayField(TEXT("id_capacities"),IDLimits);
            Buffers.Append({{TEXT("handles"),Handles},{TEXT("id_to_index"),IDToIndex},{TEXT("free_ids"),FreeIDs},{TEXT("free_counts"),FreeCounts}});
            Sizes.Append({TotalCapacity*8,TotalIDs*4,TotalIDs*4,uint32(Capacities.Num())*4});
        }
        for(int32 I=0;I<Buffers.Num();++I)
        {
            const auto& B=Buffers[I];const uint32 Size=Sizes[I];
            TArray<uint8> Bytes;
            if(Size)
            {
                FRHIGPUBufferReadback Readback(TEXT("NativeAssembly.Readback"));
                Cmd.Transition(FRHITransitionInfo(B.Value->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
                Readback.EnqueueCopy(Cmd,B.Value->GetRHI(),Size);Cmd.SubmitAndBlockUntilGPUIdle();
                const auto* Data=static_cast<const uint8*>(Readback.Lock(Size));if(!Data) return false;
                Bytes.Append(Data,Size);Readback.Unlock();
            }
            const FString Name=FString::Printf(TEXT("assembly-%s.bin"),B.Key);
            if(FPaths::FileExists(Directory/Name) || !FFileHelper::SaveArrayToFile(Bytes,*(Directory/Name))) return false;
            Record->SetStringField(B.Key,Name);
        }
        return true;
    }
};
