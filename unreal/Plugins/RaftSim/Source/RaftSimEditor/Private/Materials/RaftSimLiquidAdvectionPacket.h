#pragma once
#include "RaftSimLiquidNativeTransferAudit.h"

// A selected-step read-only snapshot AFTER native particle transport/contact.
// The P2G packet contains the step's INPUT positions and stale contact outputs;
// those stale outputs must never be compared to this step's projected grid.
struct FRaftSimLiquidAdvectionPacket
{
    TRefCountPtr<FRDGPooledBuffer> Values[5],Counts[5];
    uint32 Step=0,Capacity=0;
    float DeltaSeconds=0;
    FMatrix44f WorldToUnit=FMatrix44f::Identity,LocalToWorld=FMatrix44f::Identity,UnitToWorld=FMatrix44f::Identity;
    static constexpr const TCHAR* Names[]={TEXT("advection_raw_positions"),TEXT("advection_positions"),
        TEXT("advection_raw_velocities"),TEXT("advection_velocities"),TEXT("advection_identities")};

    bool Capture(FRDGBuilder& Graph,FNiagaraComputeExecutionContext* Context,
        FNiagaraGpuComputeDispatchInterface* Dispatch,const FRaftSimNativeTransferSample& Input,
        uint32 NativeStep,float Dt,const uint8* Parameters,uint32 ParameterBytes,FIntVector MatrixOffsets,FString& Error)
    {
        auto* Data=Context->MainDataSet->GetCurrentData();
        if(Step || !NativeStep || !FMath::IsFinite(Dt) || Dt<=0 || !Data || !Dispatch ||
            Input.InletOffsets.X<0 || Input.InletOffsets.Y<0 || !Parameters || MatrixOffsets.GetMin()<0 ||
            uint32(MatrixOffsets.GetMax()+sizeof(FMatrix44f))>ParameterBytes)
        { Error=TEXT("Invalid same-step post-advection packet");return false; }
        FMemory::Memcpy(&WorldToUnit,Parameters+MatrixOffsets.X,sizeof(FMatrix44f));
        FMemory::Memcpy(&LocalToWorld,Parameters+MatrixOffsets.Y,sizeof(FMatrix44f));
        FMemory::Memcpy(&UnitToWorld,Parameters+MatrixOffsets.Z,sizeof(FMatrix44f));
        if(WorldToUnit.ContainsNaN() || LocalToWorld.ContainsNaN() || UnitToWorld.ContainsNaN())
        { Error=TEXT("Invalid immutable native advection matrices");return false; }
        Capacity=Data->GetNumInstancesAllocated();
        if(Capacity>262144 || (Capacity && Data->GetGPUInstanceCountBufferOffset()==INDEX_NONE))
        { Error=TEXT("Unsupported post-advection allocation");return false; }
        if(Capacity)
        {
            // The just-completed Niagara dispatch used counter UAV overlap.
            // End that dependency before our read-only packing accesses it,
            // even when the required access state remains UAVCompute.
            auto CounterUav=Dispatch->GetGPUInstanceCounterManager().GetInstanceCountBuffer().UAV;
            Graph.AddPass(RDG_EVENT_NAME("Advection Counter Snapshot Handoff"),ERDGPassFlags::None,
                [CounterUav](FRHICommandList& Cmd)
                { Cmd.Transition(FRHITransitionInfo(CounterUav,ERHIAccess::UAVCompute,ERHIAccess::UAVCompute)); });
        }
        const uint32 Offsets[]={uint32(Input.InletOffsets.X),Input.PositionOffset,uint32(Input.InletOffsets.Y),Input.VelocityOffset};
        for(int32 I=0;I<5;++I)
        {
            FRDGBufferRef Packed=nullptr,Count=nullptr;
            if(!Capacity)
            {
                const FUintVector4 Zero(0,0,0,0);const uint32 Empty=0;
                Packed=CreateStructuredBuffer(Graph,TEXT("Advection.Empty"),TConstArrayView<FUintVector4>(&Zero,1));
                Count=CreateStructuredBuffer(Graph,TEXT("Advection.EmptyCount"),TConstArrayView<uint32>(&Empty,1));
            }
            else
            {
                const auto& Counter=Dispatch->GetGPUInstanceCounterManager().GetInstanceCountBuffer();
                if(I<4) Packed=RaftSimPackLiquidParticlesGPU(Graph,Data->GetGPUBufferFloat().SRV,Counter.SRV,
                    Data->GetFloatStride()/4,Offsets[I],Data->GetGPUInstanceCountBufferOffset(),Capacity,
                    FMatrix44f::Identity,Count,Counter.UAV,1.f);
                else Packed=RaftSimPackLiquidIdentityGPU(Graph,Data->GetGPUBufferInt().SRV,Counter.SRV,Counter.UAV,
                    Data->GetInt32Stride()/4,Context->MainDataSet->GetNumInt32Components(),Input.IdentityOffsets,
                    Data->GetGPUInstanceCountBufferOffset(),Capacity,Count);
            }
            if(!Packed || !Count) { Error=TEXT("Post-advection packing failed");return false; }
            Graph.QueueBufferExtraction(Packed,&Values[I]);Graph.QueueBufferExtraction(Count,&Counts[I]);
        }
        Step=NativeStep;DeltaSeconds=Dt;return true;
    }

    bool Save(FRHICommandListImmediate& Cmd,const FString& Directory,int32 Owner,uint32 ExpectedStep,
        TSharedPtr<FJsonObject> Record,FString& Error) const
    {
        if(Step!=ExpectedStep || !Step) { Error=TEXT("Missing selected post-advection step");return false; }
        auto Read=[&](FRDGPooledBuffer* Buffer,TArray<uint8>& Bytes)
        {
            if(!Buffer) return false;
            FRHIGPUBufferReadback R(TEXT("Advection.SelectedStep"));const uint32 Size=Buffer->GetSize();
            Cmd.Transition(FRHITransitionInfo(Buffer->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
            R.EnqueueCopy(Cmd,Buffer->GetRHI(),Size);Cmd.SubmitAndBlockUntilGPUIdle();
            const auto* Data=static_cast<const uint8*>(R.Lock(Size));if(!Data) return false;
            Bytes.Append(Data,Size);R.Unlock();return true;
        };
        uint32 Live=0;
        for(int32 I=0;I<5;++I)
        {
            TArray<uint8> Count,Bytes;uint32 N=0;
            if(!Read(Counts[I],Count) || Count.Num()<4 || !Read(Values[I],Bytes))
            { Error=TEXT("Post-advection readback failed");return false; }
            FMemory::Memcpy(&N,Count.GetData(),4);
            if(N>Capacity || (I && N!=Live) || Bytes.Num()<int64(N)*16)
            { Error=TEXT("Post-advection field counts disagree");return false; }
            Live=N;Bytes.SetNum(N*16);
            const FString Name=FString::Printf(TEXT("p2g-%03d-%s.bin"),Owner,Names[I]);
            if(FPaths::FileExists(Directory/Name) || !FFileHelper::SaveArrayToFile(Bytes,*(Directory/Name)))
            { Error=TEXT("Could not save unique post-advection packet");return false; }
            Record->SetStringField(Names[I],Name);
        }
        Record->SetNumberField(TEXT("advection_native_step"),Step);
        Record->SetNumberField(TEXT("advection_particle_count"),Live);
        Record->SetNumberField(TEXT("advection_engine_delta_seconds"),DeltaSeconds);
        auto Matrix=[](const FMatrix44f& M)
        {
            TArray<TSharedPtr<FJsonValue>> Rows;
            for(int32 R=0;R<4;++R) for(int32 C=0;C<4;++C) Rows.Add(MakeShared<FJsonValueNumber>(M.M[R][C]));
            return Rows;
        };
        Record->SetArrayField(TEXT("advection_world_to_unit"),Matrix(WorldToUnit));
        Record->SetArrayField(TEXT("advection_local_to_world"),Matrix(LocalToWorld));
        Record->SetArrayField(TEXT("advection_unit_to_world"),Matrix(UnitToWorld));
        Record->SetStringField(TEXT("advection_particle_stage"),TEXT("FLIP / PIC force: after stage, before owner handoff"));
        return true;
    }
};
