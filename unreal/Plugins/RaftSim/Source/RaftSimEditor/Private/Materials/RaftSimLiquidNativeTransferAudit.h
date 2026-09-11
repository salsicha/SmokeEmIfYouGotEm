#pragma once
#include "RaftSimLiquidDensityGPU.h"
#include "RaftSimLiquidParticleIdentityGPU.h"
#include "RaftSimLiquidParticleRoutingGPU.h"
#include "NiagaraComputeExecutionContext.h"
#include "NiagaraDataSet.h"
#include "NiagaraGpuComputeDispatchInterface.h"
#include "NiagaraGPUInstanceCountManager.h"
#include "RenderGraphUtils.h"
#include "RHIGPUReadback.h"
#include "Misc/FileHelper.h"
#include "NiagaraDataInterfaceNeighborQuery.h"

// One retained, actual native P2G step. Diagnostic snapshots only; no particle
// or solver writes. Inputs and totals are preserved before subsequent ticks.
struct FRaftSimNativeTransferSample
{
    int32 RegionId=0,ExpectedCount=0;
    FGuid Generation;
    uint32 PositionOffset=0,VelocityOffset=0,StepStartOffset=MAX_uint32,Capacity=0;
    FIntVector InletOffsets=FIntVector(-1,-1,-1);
    FIntVector4 IdentityOffsets=FIntVector4(-1,-1,-1,-1);
    FIntVector Cells;
    FVector Origin,AxisX,AxisY,Extent;
    double Volume=0;
    TRefCountPtr<FRDGPooledBuffer> Positions,Velocities,Count;
    TRefCountPtr<FRDGPooledBuffer> Identities,IdentityCount;
    uint32 BirthCapacity=0;
    TRefCountPtr<FRDGPooledBuffer> BirthIdentities,BirthCount,BirthPositions;
    TArray<int32> InitialSeedIds;
    TRefCountPtr<IPooledRenderTarget> Raw,Total;
    uint32 RouteFloatComponents=0,RouteIntComponents=0,RouteOwners=0;
    TRefCountPtr<FRDGPooledBuffer> RouteWords,RouteDestinations,RouteCounts;
    FNiagaraDataInterfaceProxyNeighborQuery* NeighborProxy=nullptr;
    uint64 NeighborSystem=0;
    uint32 NeighborParticles=0,NeighborSlots=0;
    FIntVector NeighborCells=FIntVector::ZeroValue;
    TRefCountPtr<FRDGPooledBuffer> NeighborBuffers[7];
    static constexpr const TCHAR* NeighborNames[]={TEXT("nq_cells"),TEXT("nq_ids"),TEXT("nq_tags"),
        TEXT("nq_counts"),TEXT("nq_offsets"),TEXT("nq_sorted_ids"),TEXT("nq_sorted_tags")};

    bool CaptureBirthIdentities(FRDGBuilder& Graph,FNiagaraComputeExecutionContext* Context,
        FNiagaraGpuComputeDispatchInterface* Dispatch,FString& Error)
    {
        auto* Data=Context->MainDataSet->GetCurrentData();
        if (!Data || !Dispatch || BirthIdentities) { Error=TEXT("Invalid native birth snapshot state");return false; }
        BirthCapacity=Data->GetNumInstancesAllocated();
        FRDGBufferRef Ids=nullptr,Counts=nullptr,PositionsAtBirth=nullptr,PositionCount=nullptr;
        if (!BirthCapacity && !ExpectedCount)
        {
            const FIntVector4 Empty(0,0,0,0);const uint32 Zero=0;
            auto EmptyBuffer=[&](const TCHAR* Name,uint32 Stride,const void* Data)
            {
                auto Desc=FRDGBufferDesc::CreateStructuredDesc(Stride,1);Desc.Usage|=BUF_SourceCopy;
                auto Buffer=Graph.CreateBuffer(Desc,Name);Graph.QueueBufferUpload(Buffer,Data,Stride,ERDGInitialDataFlags::None);return Buffer;
            };
            Ids=EmptyBuffer(TEXT("NativeBirth.Unallocated"),16,&Empty);
            Counts=EmptyBuffer(TEXT("NativeBirth.EmptyCount"),4,&Zero);
            const FVector4f EmptyPosition(0,0,0,0);
            PositionsAtBirth=EmptyBuffer(TEXT("NativeBirth.EmptyPosition"),16,&EmptyPosition);
        }
        else
        {
            const auto& Counter=Dispatch->GetGPUInstanceCounterManager().GetInstanceCountBuffer();
            auto Uav=Counter.UAV;
            Graph.AddPass(RDG_EVENT_NAME("Native Birth Counter Handoff"),ERDGPassFlags::None,
                [Uav](FRHICommandList& Cmd){Cmd.Transition(FRHITransitionInfo(Uav,ERHIAccess::UAVCompute,ERHIAccess::UAVCompute));});
            Ids=RaftSimPackLiquidIdentityGPU(Graph,Data->GetGPUBufferInt().SRV,Counter.SRV,Counter.UAV,
                Data->GetInt32Stride()/sizeof(int32),Context->MainDataSet->GetNumInt32Components(),
                IdentityOffsets,Data->GetGPUInstanceCountBufferOffset(),BirthCapacity,Counts);
            PositionsAtBirth=RaftSimPackLiquidParticlesGPU(Graph,Data->GetGPUBufferFloat().SRV,Counter.SRV,
                Data->GetFloatStride()/4,PositionOffset,Data->GetGPUInstanceCountBufferOffset(),BirthCapacity,
                FMatrix44f::Identity,PositionCount,Counter.UAV,1.f);
        }
        if (!Ids || !Counts || !PositionsAtBirth) { Error=TEXT("Native birth identity/position snapshot packing failed");return false; }
        Graph.QueueBufferExtraction(Ids,&BirthIdentities);Graph.QueueBufferExtraction(Counts,&BirthCount);
        Graph.QueueBufferExtraction(PositionsAtBirth,&BirthPositions);return true;
    }

    bool Capture(FRDGBuilder& Graph,FNiagaraComputeExecutionContext* Context,
        FNiagaraGpuComputeDispatchInterface* Dispatch,FRDGTextureRef RawGrid,FRDGTextureRef TotalGrid,FString& Error,
        const FRaftSimLiquidParticleRoutePlan* RoutePlan=nullptr,FRaftSimLiquidParticleRoutePacket* RoutePacket=nullptr)
    {
        auto* Particles=Context->MainDataSet->GetCurrentData();
        if (!Particles || !Dispatch) { Error=TEXT("Native P2G particle dataset missing");return false; }
        Capacity=Particles->GetNumInstancesAllocated();
        const uint32 Offset=Particles->GetGPUInstanceCountBufferOffset();
        if (Capacity>262144 || (Capacity && Offset==INDEX_NONE) || (!Capacity && ExpectedCount))
        { Error=TEXT("Native P2G particle allocation/count unsupported");return false; }
        FRDGBufferRef P=nullptr,V=nullptr,PCount=nullptr,VCount=nullptr;
        FRDGBufferRef Ids=nullptr,ICount=nullptr;
        if (!Capacity)
        {
            // An actually unallocated dataset cannot hold live particles.
            // Retain that distinction from a counted allocated-empty dataset.
            const FVector4f Empty(0,0,0,0);const uint32 Zero=0;
            P=CreateStructuredBuffer(Graph,TEXT("NativeP2G.Unallocated"),TConstArrayView<FVector4f>(&Empty,1));V=P;
            PCount=CreateStructuredBuffer(Graph,TEXT("NativeP2G.NoAllocationCount"),TConstArrayView<uint32>(&Zero,1));
            const FIntVector4 EmptyId(0,0,0,0);
            Ids=CreateStructuredBuffer(Graph,TEXT("NativeP2G.UnallocatedIdentity"),TConstArrayView<FIntVector4>(&EmptyId,1));ICount=PCount;
        }
        else
        {
            const auto& Counter=Dispatch->GetGPUInstanceCounterManager().GetInstanceCountBuffer();
            auto CounterUav=Counter.UAV;
            Graph.AddPass(RDG_EVENT_NAME("Native P2G Counter Snapshot Handoff"),ERDGPassFlags::None,
                [CounterUav](FRHICommandList& Cmd){Cmd.Transition(FRHITransitionInfo(CounterUav,ERHIAccess::UAVCompute,ERHIAccess::UAVCompute));});
            P=RaftSimPackLiquidParticlesGPU(Graph,Particles->GetGPUBufferFloat().SRV,Counter.SRV,
                Particles->GetFloatStride()/sizeof(float),PositionOffset,Offset,Capacity,FMatrix44f::Identity,PCount,Counter.UAV,1.f);
            V=RaftSimPackLiquidParticlesGPU(Graph,Particles->GetGPUBufferFloat().SRV,Counter.SRV,
                Particles->GetFloatStride()/sizeof(float),VelocityOffset,Offset,Capacity,FMatrix44f::Identity,VCount,Counter.UAV,1.f);
            if (!P || !V) { Error=TEXT("Native particle snapshot packing failed");return false; }
            Ids=RaftSimPackLiquidIdentityGPU(Graph,Particles->GetGPUBufferInt().SRV,Counter.SRV,Counter.UAV,
                Particles->GetInt32Stride()/sizeof(int32),Context->MainDataSet->GetNumInt32Components(),
                IdentityOffsets,Offset,Capacity,ICount);
            if (!Ids) { Error=TEXT("Native integer particle identity snapshot failed");return false; }
        }
        Graph.QueueBufferExtraction(P,&Positions);Graph.QueueBufferExtraction(V,&Velocities);Graph.QueueBufferExtraction(PCount,&Count);
        Graph.QueueBufferExtraction(Ids,&Identities);Graph.QueueBufferExtraction(ICount,&IdentityCount);
        if (RoutePlan)
        {
            RouteFloatComponents=Context->MainDataSet->GetNumFloatComponents();RouteIntComponents=Context->MainDataSet->GetNumInt32Components();RouteOwners=RoutePlan->Owners;
            if (Context->MainDataSet->GetNumHalfComponents()) { Error=TEXT("Native half particle ABI requires exact half routing support");return false; }
            FRaftSimLiquidParticleRoutePacket R;
            if (Capacity)
            {
                const auto& Counter=Dispatch->GetGPUInstanceCounterManager().GetInstanceCountBuffer();
                R=RaftSimStageLiquidParticleRoutes(Graph,*RoutePlan,RegionId,Particles->GetGPUBufferFloat().SRV,
                    Particles->GetGPUBufferInt().SRV,Counter.UAV,Offset,Particles->GetFloatStride()/4,Particles->GetInt32Stride()/4,
                    RouteFloatComponents,RouteIntComponents,0,PositionOffset,Capacity,Error);
                if (!R.Words) return false;
            }
            else
            {
                const uint32 Zero=0;const FUintVector4 Empty(0,0,0,0);TArray<uint32> Counts;Counts.Init(0,RouteOwners+3);
                R.Words=CreateStructuredBuffer(Graph,TEXT("NativeRoute.EmptyState"),TConstArrayView<uint32>(&Zero,1));
                R.Routes=CreateStructuredBuffer(Graph,TEXT("NativeRoute.EmptyRoutes"),TConstArrayView<FUintVector4>(&Empty,1));
                R.Counts=CreateStructuredBuffer(Graph,TEXT("NativeRoute.EmptyCounts"),TConstArrayView<uint32>(Counts));
            }
            R.Capacity=Capacity;R.FloatComponents=RouteFloatComponents;R.IntComponents=RouteIntComponents;
            if (RoutePacket) *RoutePacket=R;
            Graph.QueueBufferExtraction(R.Words,&RouteWords);Graph.QueueBufferExtraction(R.Routes,&RouteDestinations);Graph.QueueBufferExtraction(R.Counts,&RouteCounts);
        }
        auto RawCopy=Graph.CreateTexture(RawGrid->Desc,TEXT("NativeP2G.RawSnapshot"));AddCopyTexturePass(Graph,RawGrid,RawCopy);
        Graph.QueueTextureExtraction(RawCopy,&Raw);Graph.QueueTextureExtraction(TotalGrid,&Total);
        if (NeighborProxy)
        {
            auto* N=NeighborProxy->SystemInstancesToProxyData_RT.Find(NeighborSystem);
            if (!N || N->MaxCellsPerParticle!=1 || !N->bUsePersistentIDs)
            { Error=TEXT("Native neighbor diagnostic layout unavailable");return false; }
            NeighborParticles=N->NumParticles;NeighborSlots=N->AllocatedNumSlots;NeighborCells=N->NumCells;
            FNiagaraPooledRWBuffer* Buffers[]={&N->CellIdBuffer,&N->ParticleIdIndexBuffer,&N->AcquireTagBuffer,
                &N->CellCountBuffer,&N->CellOffsetBuffer,&N->ParticleListBuffer,&N->AcquireTagListBuffer};
            for (int32 I=0;I<7;++I)
            {
                if (!Buffers[I]->IsValid()) { Error=TEXT("Native neighbor diagnostic buffer missing");return false; }
                auto* Source=Buffers[I]->GetOrCreateBuffer(Graph);
                auto* Copy=RaftSimSnapshotLiquidIntegersGPU(Graph,Buffers[I]->GetOrCreateSRV(Graph),Source->Desc.NumElements);
                if (!Copy) { Error=TEXT("Native neighbor shader snapshot failed");return false; }
                Graph.QueueBufferExtraction(Copy,&NeighborBuffers[I]);
            }
        }
        return true;
    }

    bool Save(FRHICommandListImmediate& Cmd,const FString& Directory,TSharedPtr<FJsonObject>& Record,FString& Error) const
    {
        if (!Positions || !Velocities || !Count || !Raw || !Total || !Identities || !IdentityCount || !BirthIdentities || !BirthCount || !BirthPositions)
        { Error=TEXT("Incomplete native P2G snapshots");return false; }
        Record=MakeShared<FJsonObject>();Record->SetNumberField(TEXT("region_id"),RegionId);
        Record->SetNumberField(TEXT("expected_count"),ExpectedCount);Record->SetNumberField(TEXT("particle_volume_m3"),Volume);
        Record->SetStringField(TEXT("simulation_generation"),Generation.ToString(EGuidFormats::DigitsWithHyphens));
        Record->SetNumberField(TEXT("particle_capacity"),Capacity);
        auto Vector=[](FVector V) { TArray<TSharedPtr<FJsonValue>> A;for (int32 I=0;I<3;++I) A.Add(MakeShared<FJsonValueNumber>(V[I]));return A; };
        Record->SetArrayField(TEXT("cells"),Vector(FVector(Cells)));Record->SetArrayField(TEXT("world_origin_cm"),Vector(Origin));
        Record->SetArrayField(TEXT("world_axis_x"),Vector(AxisX));Record->SetArrayField(TEXT("world_axis_y"),Vector(AxisY));
        Record->SetArrayField(TEXT("extent_cm"),Vector(Extent));
        auto ReadBuffer=[&](FRDGPooledBuffer* B,TArray<uint8>& Bytes)
        {
            const uint32 Size=B->GetSize();FRHIGPUBufferReadback R(TEXT("NativeP2G.Particles"));
            Cmd.Transition(FRHITransitionInfo(B->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
            R.EnqueueCopy(Cmd,B->GetRHI(),Size);Cmd.SubmitAndBlockUntilGPUIdle();
            const auto* Data=static_cast<const uint8*>(R.Lock(Size));if (!Data) return false;
            Bytes.Append(Data,Size);R.Unlock();return true;
        };
        auto SaveBytes=[&](const TCHAR* Kind,const TArray<uint8>& Bytes)
        {
            const FString Name=FString::Printf(TEXT("p2g-%03d-%s.bin"),RegionId,Kind);
            if (FPaths::FileExists(Directory/Name) || !FFileHelper::SaveArrayToFile(Bytes,*(Directory/Name))) return false;
            Record->SetStringField(Kind,Name);return true;
        };
        if (NeighborProxy)
        {
            Record->SetNumberField(TEXT("nq_particles"),NeighborParticles);
            Record->SetNumberField(TEXT("nq_slots"),NeighborSlots);
            Record->SetArrayField(TEXT("nq_dimensions"),Vector(FVector(NeighborCells)));
            for (int32 I=0;I<7;++I)
            {
                TArray<uint8> Bytes;
                if (!NeighborBuffers[I] || !ReadBuffer(NeighborBuffers[I],Bytes) || !SaveBytes(NeighborNames[I],Bytes)) return false;
            }
        }
        TArray<uint8> CountBytes;if (!ReadBuffer(Count,CountBytes) || CountBytes.Num()<4) return false;
        uint32 Live=0;FMemory::Memcpy(&Live,CountBytes.GetData(),4);
        if (Live>Capacity) { Error=TEXT("Actual native count exceeds particle allocation");return false; }
        TArray<uint8> IdentityCountBytes;
        if (!ReadBuffer(IdentityCount,IdentityCountBytes) || IdentityCountBytes.Num()<4 ||
            FMemory::Memcmp(IdentityCountBytes.GetData(),CountBytes.GetData(),4)!=0)
        { Error=TEXT("Native particle and identity snapshots have different live counts");return false; }
        Record->SetNumberField(TEXT("particle_count"),Live);
        Record->SetStringField(TEXT("identity_layout"),TEXT("int32:birth_owner,birth_sequence,native_unique_id,native_persistent_index"));
        TArray<uint8> BirthCountBytes,BirthBytes;
        if (!ReadBuffer(BirthCount,BirthCountBytes) || BirthCountBytes.Num()<4 || !ReadBuffer(BirthIdentities,BirthBytes)) return false;
        uint32 Born=0;FMemory::Memcpy(&Born,BirthCountBytes.GetData(),4);
        if (Born>BirthCapacity || Born!=uint32(ExpectedCount) || BirthBytes.Num()<int64(Born)*16)
        { Error=TEXT("Native first-step birth count differs from packet initialization");return false; }
        Record->SetNumberField(TEXT("birth_particle_count"),Born);
        BirthBytes.SetNum(Born*16);if (!SaveBytes(TEXT("birth_identities"),BirthBytes)) return false;
        TArray<uint8> BirthPositionBytes;
        if(InitialSeedIds.Num()!=int32(Born) || !ReadBuffer(BirthPositions,BirthPositionBytes) || BirthPositionBytes.Num()<int64(Born)*16) return false;
        BirthPositionBytes.SetNum(Born*16);if(!SaveBytes(TEXT("birth_positions"),BirthPositionBytes)) return false;
        TArray<TSharedPtr<FJsonValue>> SeedIds;for(int32 Id:InitialSeedIds) SeedIds.Add(MakeShared<FJsonValueNumber>(Id));
        Record->SetArrayField(TEXT("seed_parent_ids"),SeedIds);
        for (const auto& Pair:TArray<TPair<const TCHAR*,FRDGPooledBuffer*>>{{TEXT("positions"),Positions},{TEXT("velocities"),Velocities},{TEXT("identities"),Identities}})
        {
            TArray<uint8> Bytes;if (!ReadBuffer(Pair.Value,Bytes) || Bytes.Num()<int64(Live)*16) return false;
            Bytes.SetNum(Live*16);if (!SaveBytes(Pair.Key,Bytes)) return false;
        }
        if (RouteOwners)
        {
            Record->SetNumberField(TEXT("route_float_components"),RouteFloatComponents);Record->SetNumberField(TEXT("route_int_components"),RouteIntComponents);
            Record->SetNumberField(TEXT("route_position_offset"),PositionOffset);Record->SetNumberField(TEXT("route_velocity_offset"),VelocityOffset);
            Record->SetNumberField(TEXT("route_step_start_offset"),StepStartOffset);
            if(InletOffsets.X>=0 && InletOffsets.Y>=0 && InletOffsets.Z>=0)
                Record->SetArrayField(TEXT("route_inlet_offsets"),{
                    MakeShared<FJsonValueNumber>(InletOffsets.X),MakeShared<FJsonValueNumber>(InletOffsets.Y),MakeShared<FJsonValueNumber>(InletOffsets.Z)});
            TArray<TSharedPtr<FJsonValue>> Offsets;for(int32 I=0;I<4;++I) Offsets.Add(MakeShared<FJsonValueNumber>(IdentityOffsets[I]));
            Record->SetArrayField(TEXT("route_identity_offsets"),Offsets);
            TArray<uint8> Words,Destinations,Counts;
            if (!RouteWords || !RouteDestinations || !RouteCounts || !ReadBuffer(RouteWords,Words) ||
                !ReadBuffer(RouteDestinations,Destinations) || !ReadBuffer(RouteCounts,Counts)) return false;
            const uint32 Size=Capacity*(RouteFloatComponents+RouteIntComponents)*4;
            if (Words.Num()<int64(Size) || Destinations.Num()<int64(Live)*16 || Counts.Num()<int64(RouteOwners+3)*4) return false;
            Words.SetNum(Size);Destinations.SetNum(Live*16);Counts.SetNum((RouteOwners+3)*4);
            if (!SaveBytes(TEXT("route_words"),Words) || !SaveBytes(TEXT("route_destinations"),Destinations) || !SaveBytes(TEXT("route_counts"),Counts)) return false;
        }
        for (const auto& Pair:TArray<TPair<const TCHAR*,IPooledRenderTarget*>>{{TEXT("raw"),Raw},{TEXT("total"),Total}})
        {
            auto* Texture=Pair.Value->GetRHI();if (Texture->GetDesc().Format!=PF_A32B32G32R32F) return false;
            TArray<uint8> Bytes;Bytes.SetNumUninitialized(Cells.X*Cells.Y*Cells.Z*16);
            Cmd.Transition(FRHITransitionInfo(Texture,ERHIAccess::Unknown,ERHIAccess::CopySrc));
            for (int32 Z=0;Z<Cells.Z;++Z)
            {
                FRHIGPUTextureReadback R(TEXT("NativeP2G.Grid"));
                R.EnqueueCopy(Cmd,Texture,FIntVector(0,0,Z),0,FIntVector(Cells.X,Cells.Y,1));Cmd.SubmitAndBlockUntilGPUIdle();
                int32 Pitch=0;const auto* Data=static_cast<const uint8*>(R.Lock(Pitch));if (!Data || Pitch<Cells.X) return false;
                for (int32 Y=0;Y<Cells.Y;++Y) FMemory::Memcpy(Bytes.GetData()+(Z*Cells.Y+Y)*Cells.X*16,Data+Y*Pitch*16,Cells.X*16);
                R.Unlock();
            }
            if (!SaveBytes(Pair.Key,Bytes)) return false;
        }
        return true;
    }
};
