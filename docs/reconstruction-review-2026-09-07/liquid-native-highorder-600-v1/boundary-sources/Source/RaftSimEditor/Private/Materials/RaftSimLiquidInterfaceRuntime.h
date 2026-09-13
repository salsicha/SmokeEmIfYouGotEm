#pragma once
#include "RaftSimLiquidDataset.h"
#include "RaftSimLiquidInterfaceGPU.h"
#include "RaftSimLiquidInterfaceHighOrderGPU.h"
#include "RaftSimLiquidHaloGPU.h"
#include "RenderGraphUtils.h"
#include "RHIGPUReadback.h"

struct FRaftSimLiquidInterfaceGraph
{
    TArray<FRDGTextureRef> Current;
    FRDGBufferRef Ledger=nullptr;
};

// Optional unsaved live integration. Pressure coupling is separately opt-in;
// the visible renderer is not connected yet. Retains scalar across native steps/graphs;
// fixed initial physical exterior/Z boundaries are explicitly provisional.
struct FRaftSimLiquidInterfaceRuntime
{
    TArray<TArray<uint8>> Initial;
    TArray<FIntVector> Sizes;
    TArray<FVector3f> Spacing;
    TArray<int32> DeltaOffsets;
    TArray<TRefCountPtr<IPooledRenderTarget>> Current,Before,SelectedAfter;
    TRefCountPtr<FRDGPooledBuffer> Ledger;
    TArray<float> FluidSeconds,EngineSeconds;
    FString InitialManifestHash;
    uint32 MaxSteps=0;
    bool InitialResetObserved=false;
    bool PressureCoupled=false;
    bool CompactTransport=false;
    bool HighOrder=false;
    uint32 DiagnosticWidth() const { return HighOrder?8u:3u; }
    uint32 TransportCount=0;
    const TCHAR* TransportStage() const { return CompactTransport?TEXT("Extrapolate Velocities Again"):TEXT("Project Pressure"); }

    bool Load(const FString& Directory,const FRaftSimLiquidDataset& Dataset,TConstArrayView<FIntVector> Expected,
        uint32 Steps,FString& Error)
    {
        auto J=FRaftSimLiquidDataset::Read(Directory/TEXT("manifest.json"));
        if(!J || Dataset.Key!=TEXT("reservoir-v1") || J->GetStringField(TEXT("native_dataset"))!=Dataset.Key ||
            J->GetStringField(TEXT("schema"))!=TEXT("raftsim.initial_liquid_interface.v1") ||
            J->GetStringField(TEXT("ownership_manifest_sha256"))!=FRaftSimLiquidDataset::Hash(Dataset.Regions/TEXT("manifest.json")) ||
            J->GetStringField(TEXT("source_geometry_sha256"))!=FRaftSimLiquidDataset::Hash(Dataset.Mesh) ||
            J->GetArrayField(TEXT("regions")).Num()!=12 || Expected.Num()!=12 || Steps<2 || Steps>3600)
        { Error=TEXT("Validated all-owner initial interface package required");return false; }
        InitialManifestHash=FRaftSimLiquidDataset::Hash(Directory/TEXT("manifest.json"));MaxSteps=Steps;
        for(int32 I=0;I<12;++I)
        {
            auto R=J->GetArrayField(TEXT("regions"))[I]->AsObject();
            if(R->GetStringField(TEXT("source_region_sha256"))!=FRaftSimLiquidDataset::Hash(Dataset.Regions/FString::Printf(TEXT("region-%03d.json"),I)))
            { Error=TEXT("Initial interface source region changed");return false; }
            const auto& C=R->GetArrayField(TEXT("cells"));const auto& H=R->GetArrayField(TEXT("spacing_cm"));
            if(C.Num()!=3 || H.Num()!=3 || R->GetNumberField(TEXT("region_id"))!=I)
            { Error=TEXT("Initial interface owner layout invalid");return false; }
            FIntVector Size;FVector3f Cell;
            for(int A=0;A<3;++A) { Size[A]=int32(C[A]->AsNumber());Cell[A]=float(H[A]->AsNumber()); }
            const FString Name=R->GetStringField(TEXT("initial_phi"));auto& Bytes=Initial.AddDefaulted_GetRef();
            if(Size!=Expected[I] || Cell.ContainsNaN() || Cell.GetMin()<=0 || FPaths::GetCleanFilename(Name)!=Name ||
                FRaftSimLiquidDataset::Hash(Directory/Name)!=R->GetStringField(TEXT("initial_phi_sha256")) ||
                !FFileHelper::LoadFileToArray(Bytes,*(Directory/Name)) || Bytes.Num()!=Size.X*Size.Y*Size.Z*4)
            { Error=TEXT("Changed or incompatible initial interface field");return false; }
            const float* Values=reinterpret_cast<const float*>(Bytes.GetData());
            for(int32 K=0;K<Bytes.Num()/4;++K) if(!FMath::IsFinite(Values[K]))
            { Error=TEXT("Nonfinite initial interface");return false; }
            Sizes.Add(Size);Spacing.Add(Cell);
        }
        Current.SetNum(12);Before.SetNum(12);SelectedAfter.SetNum(12);return true;
    }

    void Initialize(FRHICommandListImmediate& Cmd)
    {
        for(int32 I=0;I<Sizes.Num();++I)
        {
            const auto S=Sizes[I];
            auto Texture=Cmd.CreateTexture(FRHITextureCreateDesc::Create3D(TEXT("LiquidInterface.Initial"),S.X,S.Y,S.Z,PF_R32_FLOAT)
                .SetFlags(TexCreate_ShaderResource|TexCreate_UAV).SetInitialState(ERHIAccess::CopyDest));
            Cmd.UpdateTexture3D(Texture,0,FUpdateTextureRegion3D(0,0,0,0,0,0,S.X,S.Y,S.Z),S.X*4,S.X*S.Y*4,Initial[I].GetData());
            Cmd.Transition(FRHITransitionInfo(Texture,ERHIAccess::CopyDest,ERHIAccess::SRVCompute));
            Current[I]=CreateRenderTarget(Texture,TEXT("LiquidInterface.Persistent"));
        }
        Initial.Empty();
    }

    bool Bind(FRDGBuilder& Graph,FRaftSimLiquidInterfaceGraph& Local,FString& Error)
    {
        if(Local.Current.IsEmpty()) for(const auto& T:Current)
        {
            if(!T) { Error=TEXT("Persistent interface state missing");return false; }
            Local.Current.Add(Graph.RegisterExternalTexture(T));
        }
        return Local.Current.Num()==12;
    }

    bool Advance(FRDGBuilder& Graph,FRaftSimLiquidInterfaceGraph& Local,const FRaftSimLiquidHaloPlan& Halo,
        TConstArrayView<FRDGTextureRef> Velocity,TConstArrayView<FRDGTextureRef> Boundary,uint32 Step,float FluidDt,float EngineDt,FString& Error)
    {
        // Native step one initializes particles/grids and has no projection.
        // Transport starts at the selected post-projection stage, native step two.
        if(!InitialResetObserved || Step!=TransportCount+2 || (!PressureCoupled && Step>MaxSteps) || Velocity.Num()!=12 ||
            (HighOrder && (!CompactTransport || Boundary.Num()!=12)) ||
            !FMath::IsFinite(FluidDt) || FluidDt<0 || !FMath::IsFinite(EngineDt) || EngineDt<0 || (CompactTransport && FluidDt!=EngineDt))
        {
            Error=FString::Printf(TEXT("Interface native step sequence/clock invalid: step=%u expected=%d max=%u owners=%d fluid_dt=%.9g engine_dt=%.9g"),
                Step,int32(TransportCount+2),MaxSteps,Velocity.Num(),FluidDt,EngineDt);
            return false;
        }
        if(!Bind(Graph,Local,Error)) return false;
        if(!Local.Ledger)
        {
            if(Ledger) Local.Ledger=Graph.RegisterExternalBuffer(Ledger);
            else
            {
                auto Desc=FRDGBufferDesc::CreateStructuredDesc(4,(MaxSteps-1)*12*DiagnosticWidth());Desc.Usage|=BUF_SourceCopy;
                Local.Ledger=Graph.CreateBuffer(Desc,TEXT("LiquidInterface.StepDiagnostics"));
                AddClearUAVPass(Graph,Graph.CreateUAV(Local.Ledger),0u);
                Graph.QueueBufferExtraction(Local.Ledger,&Ledger);
            }
        }
        TArray<FRDGTextureRef> Next;
        TArray<FRaftSimLiquidInterfaceHighOrderRegion> Regions;
        for(int32 I=0;I<12;++I)
        {
            if(Step==MaxSteps)
            {
                auto Copy=Graph.CreateTexture(Local.Current[I]->Desc,TEXT("LiquidInterface.PairedBefore"));
                AddCopyTexturePass(Graph,Local.Current[I],Copy);Graph.QueueTextureExtraction(Copy,&Before[I]);
            }
            if(HighOrder)
            {
                if(Spacing[I]!=Spacing[0]) { Error=TEXT("High-order regional metrics differ");return false; }
                Regions.Add({Local.Current[I],Velocity[I],Boundary[I]});continue;
            }
            const auto Result=RaftSimAdvectLiquidInterface(Graph,Local.Current[I],Velocity[I],Spacing[I],FluidDt,
                FIntVector(2),Sizes[I]-FIntVector(2),Error,CompactTransport);
            if(!Result.Scalar) return false;
            if(Step<=MaxSteps) AddCopyBufferPass(Graph,Local.Ledger,((Step-2)*12+I)*3*4,Result.Diagnostics,0,3*4);
            Next.Add(Result.Scalar);
        }
        if(HighOrder)
        {
            const auto Results=RaftSimAdvectLiquidInterfaceHighOrderRegions(Graph,Halo,Regions,Spacing[0],FluidDt,Error,true);
            if(Results.Num()!=12) return false;
            for(int I=0;I<12;++I)
            {
                if(Step<=MaxSteps) AddCopyBufferPass(Graph,Local.Ledger,((Step-2)*12+I)*8*4,Results[I].Diagnostics,0,8*4);
                Next.Add(Results[I].Scalar);
            }
        }
        // R32 owner-to-halo copying is identical to pressure copying; this does
        // not touch the native pressure textures or their iteration count.
        if(!HighOrder && !RaftSimExchangeLiquidPressureHalo(Graph,Halo,Next,Error)) return false;
        Local.Current=MoveTemp(Next);
        for(int32 I=0;I<12;++I) Graph.QueueTextureExtraction(Local.Current[I],&Current[I]);
        if(Step==MaxSteps) for(int32 I=0;I<12;++I) Graph.QueueTextureExtraction(Local.Current[I],&SelectedAfter[I]);
        ++TransportCount;
        if(Step<=MaxSteps) { FluidSeconds.Add(FluidDt);EngineSeconds.Add(EngineDt); }
        return true;
    }

    bool Save(FRHICommandListImmediate& Cmd,const FString& Directory,TSharedPtr<FJsonObject>& Record,FString& Error) const
    {
        if(!InitialResetObserved || FluidSeconds.Num()!=MaxSteps-1 || !Ledger)
        { Error=TEXT("Continuous interface did not reach selected native step");return false; }
        Record=MakeShared<FJsonObject>();Record->SetStringField(TEXT("schema"),HighOrder?TEXT("raftsim.native_liquid_interface.v2"):TEXT("raftsim.native_liquid_interface.v1"));
        Record->SetBoolField(TEXT("high_order_transport"),HighOrder);
        Record->SetNumberField(TEXT("diagnostic_width"),DiagnosticWidth());
        Record->SetStringField(TEXT("scalar_transport"),HighOrder?TEXT("limited-bfecc-rk2-regional-v1"):TEXT("rk2-semi-lagrangian-v1"));
        Record->SetBoolField(TEXT("intermediate_scalar_validity_halos_exchanged"),HighOrder);
        Record->SetStringField(TEXT("solid_source"),HighOrder?TEXT("same-step-native-boundary-w-1-or-3"):TEXT("not-used"));
        Record->SetStringField(TEXT("initial_manifest_sha256"),InitialManifestHash);
        TArray<TSharedPtr<FJsonValue>> Dt,GlobalDt,Regions;
        double Total=0;for(float V:FluidSeconds) { Dt.Add(MakeShared<FJsonValueNumber>(V));Total+=V; }
        for(float V:EngineSeconds) GlobalDt.Add(MakeShared<FJsonValueNumber>(V));
        Record->SetArrayField(TEXT("fluid_delta_seconds"),Dt);Record->SetArrayField(TEXT("engine_delta_seconds"),GlobalDt);
        Record->SetNumberField(TEXT("native_steps"),MaxSteps);Record->SetNumberField(TEXT("fluid_elapsed_seconds"),Total);
        Record->SetNumberField(TEXT("initial_reset_native_step"),1);
        Record->SetNumberField(TEXT("first_transport_native_step"),2);
        Record->SetNumberField(TEXT("transport_steps"),FluidSeconds.Num());
        Record->SetStringField(TEXT("clock_source"),TEXT("Immutable native tick ExternalParamData Grid3D_FLIP_FluidControl_Emitter.DeltaTime (compiled Emitter.DeltaTime); engine global clock recorded separately"));
        Record->SetStringField(TEXT("update_stage"),FString(TransportStage())+TEXT(": after stage; internal interface halos exchanged after transport"));
        Record->SetBoolField(TEXT("compact_transport"),CompactTransport);
        Record->SetStringField(TEXT("velocity_interpolation"),CompactTransport?TEXT("averaged-quadratic-normal-tent-transverse-v1"):TEXT("trilinear"));
        Record->SetStringField(TEXT("boundary_model"),TEXT("Provisional fixed initial outer XY halo and two Z edge layers; no physical acceptance"));
        Record->SetBoolField(TEXT("pressure_or_renderer_coupled"),PressureCoupled);
        Record->SetBoolField(TEXT("pressure_coupled"),PressureCoupled);
        Record->SetBoolField(TEXT("renderer_coupled"),false);
        Record->SetNumberField(TEXT("total_observed_transport_steps"),TransportCount);
        for(int32 I=0;I<12;++I)
        {
            auto R=MakeShared<FJsonObject>();R->SetNumberField(TEXT("region_id"),I);
            for(int32 Which=0;Which<2;++Which)
            {
                const auto& Target=Which?SelectedAfter[I]:Before[I];const auto S=Sizes[I];
                if(!Target) { Error=TEXT("Paired interface surface missing");return false; }
                TArray<uint8> Bytes;Bytes.SetNumUninitialized(S.X*S.Y*S.Z*4);
                auto* Texture=Target->GetRHI();Cmd.Transition(FRHITransitionInfo(Texture,ERHIAccess::Unknown,ERHIAccess::CopySrc));
                for(int32 Z=0;Z<S.Z;++Z)
                {
                    FRHIGPUTextureReadback Read(TEXT("LiquidInterface.PairedRead"));
                    Read.EnqueueCopy(Cmd,Texture,FIntVector(0,0,Z),0,FIntVector(S.X,S.Y,1));Cmd.SubmitAndBlockUntilGPUIdle();
                    int32 Pitch=0;const auto* Data=static_cast<const float*>(Read.Lock(Pitch));
                    if(!Data || Pitch<S.X) { if(Data) Read.Unlock();Error=TEXT("Incomplete interface readback");return false; }
                    for(int32 Y=0;Y<S.Y;++Y) FMemory::Memcpy(Bytes.GetData()+(Z*S.Y+Y)*S.X*4,Data+Y*Pitch,S.X*4);
                    Read.Unlock();
                }
                const FString Key=Which?TEXT("after"):TEXT("before"),Name=FString::Printf(TEXT("interface-%03d-%s.r32f"),I,*Key);
                if(FPaths::FileExists(Directory/Name) || !FFileHelper::SaveArrayToFile(Bytes,*(Directory/Name)))
                { Error=TEXT("Cannot save unique interface field");return false; }
                R->SetStringField(Key,Name);
            }
            Regions.Add(MakeShared<FJsonValueObject>(R));
        }
        Record->SetArrayField(TEXT("regions"),Regions);
        const uint32 Width=DiagnosticWidth();
        FRHIGPUBufferReadback Read(TEXT("LiquidInterface.AllStepDiagnostics"));const uint32 Bytes=(MaxSteps-1)*12*Width*4;
        Cmd.Transition(FRHITransitionInfo(Ledger->GetRHI(),ERHIAccess::Unknown,ERHIAccess::CopySrc));
        Read.EnqueueCopy(Cmd,Ledger->GetRHI(),Bytes);Cmd.SubmitAndBlockUntilGPUIdle();
        const auto* Data=static_cast<const uint32*>(Read.Lock(Bytes));
        if(!Data) { Error=TEXT("Missing interface diagnostic ledger");return false; }
        TArray<TSharedPtr<FJsonValue>> Values;uint64 Rejected=0,Nonfinite=0,Reverse=0,Third=0;
        for(uint32 K=0;K<(MaxSteps-1)*12*Width;++K)
        {
            Values.Add(MakeShared<FJsonValueNumber>(Data[K]));
            if(K%Width==1) Rejected+=Data[K];if(K%Width==2) Nonfinite+=Data[K];
            if(HighOrder && K%Width==6) Reverse+=Data[K];if(HighOrder && K%Width==7) Third+=Data[K];
        }
        Read.Unlock();Record->SetArrayField(TEXT("diagnostic_words"),Values);
        Record->SetNumberField(TEXT("rejected_trace_cells"),double(Rejected));Record->SetNumberField(TEXT("nonfinite_cells"),double(Nonfinite));
        Record->SetNumberField(TEXT("invalid_scalar_or_solid_cells"),double(Nonfinite));
        Record->SetNumberField(TEXT("reverse_trace_failures"),double(Reverse));Record->SetNumberField(TEXT("third_forward_failures"),double(Third));
        if(Rejected || Nonfinite || Third) { Error=TEXT("Live interface transport has rejected traces/invalid values; not a valid coupled surface");return false; }
        return true;
    }
};
