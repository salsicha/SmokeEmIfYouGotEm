#include "HAL/IConsoleManager.h"
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Serialization/JsonSerializer.h"
#include "Engine/World.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "NiagaraEmitterInstance.h"
#include "NiagaraEmitterHandle.h"
#include "NiagaraSystemInstanceController.h"
#include "NiagaraComputeExecutionContext.h"
#include "NiagaraGPUSystemTick.h"
#include "NiagaraGpuComputeDispatchInterface.h"
#include "NiagaraDataInterfaceRenderTargetVolume.h"
#include "NiagaraDataInterfaceGrid3DCollection.h"
#include "RaftSimLiquidDensityGPU.h"
#include "RaftSimLiquidRedistanceGPU.h"
#include "RaftSimLiquidFoamGPU.h"
#include "RaftSimLiquidSecondarySurface.h"
#include "RaftSimLiquidStageInterface.h"
#include "RaftSimLiquidGraphHistory.h"
#include "RaftSimLiquidReconstructionLayout.h"
#include "HAL/ThreadSafeCounter64.h"
#include "NiagaraSimStageData.h"
#include "RenderGraphBuilder.h"
#include "RenderGraphUtils.h"
#include "RHIGPUReadback.h"
#include "RenderingThread.h"
#include "UObject/StrongObjectPtr.h"
#include "UObject/UObjectIterator.h"

namespace
{
FThreadSafeCounter64 NextLiquidHistoryAttachment;
struct FLiveDensityReview
{
    struct FTimingSlot
    {
        FRHIPooledRenderQuery Queries[4];
        uint64 Update=0;
        bool Pending=false;
    };
    TStrongObjectPtr<UNiagaraComponent> Component;
    FNiagaraComputeExecutionContext* Context=nullptr;
    FNiagaraGpuComputeDispatchInterface* Dispatch=nullptr;
    FNiagaraDataInterfaceProxyRenderTargetVolumeProxy* Volume=nullptr;
    FNiagaraDataInterfaceProxyRenderTargetVolumeProxy* SecondarySurface=nullptr;
    TRefCountPtr<IPooledRenderTarget> LastSecondarySurface;
    uint64 SecondarySurfacePublishes=0;
    FNiagaraDataInterfaceProxyGrid3DCollectionProxy* Boundary=nullptr;
    FNiagaraDataInterfaceProxyGrid3DCollectionProxy* Velocity=nullptr;
    FNiagaraSystemInstanceID SystemId;
    uint64 HistoryAttachment=0;
    FRaftSimLiquidReconstructionLayout Layout;
    FDelegateHandle Callback;
    FDelegateHandle PreViewCallback;
    FDelegateHandle StageCallback;
    FNiagaraComputeExecutionContext* SecondaryContext=nullptr;
    bool CurrentSurface=false;
    bool SmoothSparse=false;
    bool ParticleSurfaceOnly=false;
    uint64 BeforeSecondaryUpdates=0;
    uint64 StageEvents=0;
    uint64 SecondaryFirstStageEvents=0;
    uint32 MaxSecondaryStepsPerGraph=0;
    FMatrix44f SimulationToLocalCm;
    uint32 PositionOffset=0;
    uint64 Updates=0;
    uint64 SimulationFrameUpdates=0;
    uint64 RenderOnlyUpdates=0;
    uint64 LastFrame=MAX_uint64;
    FString Error;
    TRefCountPtr<FRDGPooledBuffer> LastPositions,LastCount,LastDiagnostics;
    TRefCountPtr<IPooledRenderTarget> LastSurface;
    TRefCountPtr<IPooledRenderTarget> LastBoundary;
    TRefCountPtr<FRDGPooledBuffer> LastDensityFixed,LastOccupancyAudit;
    TRefCountPtr<FRDGPooledBuffer> ClockTimeline;
    bool Bulk=false;
    bool SurfaceFoam=false;
    TRefCountPtr<IPooledRenderTarget> FoamHistory,LastFoamInputHistory,LastFoamCurrent,LastFoamVelocity;
    TRefCountPtr<FRDGPooledBuffer> LastFoamAudit;
    bool Profile=false;
    FRenderQueryPoolRHIRef QueryPool;
    TArray<FTimingSlot> Timing;
    bool TimingAvailable=false;
    TArray<TSharedPtr<FJsonValue>> TimingSamples;
    uint32 TimingSkipped=0;
};
TSharedPtr<FLiveDensityReview,ESPMode::ThreadSafe> Live;

void RemoveLiveDensity()
{
    if (!Live) return;
    auto State=Live;
    ENQUEUE_RENDER_COMMAND(RaftSimRemoveLiveDensity)([State](FRHICommandListImmediate&)
    {
        if (State->Callback.IsValid()) State->Dispatch->GetOnPostRenderEvent().Remove(State->Callback);
        if (State->PreViewCallback.IsValid()) State->Dispatch->GetOnPreInitViewsEvent().Remove(State->PreViewCallback);
        State->PreViewCallback.Reset();
        if (State->StageCallback.IsValid()) URaftSimLiquidStageInterface::PreStageEvent().Remove(State->StageCallback);
        State->StageCallback.Reset();
        State->Callback.Reset();
        // Even an empty pooled-query object's destructor is render-thread only.
        // Destroy the array here, before the shared review state returns to GT.
        State->Timing.Empty();State->QueryPool.SafeRelease();
    });
    FlushRenderingCommands();Live.Reset();
}

// Remove the raw render-thread references before the pinned component's world
// tears down its Niagara instance. Explicit stop is the normal diagnostic path.
FDelegateHandle LiveDensityWorldCleanupHandle=FWorldDelegates::OnWorldCleanup.AddLambda([](UWorld* World,bool,bool)
{ if (Live && Live->Component->GetWorld()==World) RemoveLiveDensity(); });

FAutoConsoleCommandWithWorldAndArgs LiveCommand(TEXT("RaftSim.LiquidLiveDensityReview"),
    TEXT("start [profile] [bulk] [foam] | stop/inspect unused-report-dir. Unsaved terrain fixture only; never modifies particles or solver grids."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args,UWorld* World)
    {
        if (Args.Num()>=1 && Args.Num()<=4 && Args[0]==TEXT("start"))
        {
            for (int32 I=1;I<Args.Num();++I) if (Args[I]!=TEXT("profile") && Args[I]!=TEXT("bulk") && Args[I]!=TEXT("foam")) return;
            if (Live) return;
            auto State=MakeShared<FLiveDensityReview,ESPMode::ThreadSafe>();
            State->HistoryAttachment=uint64(NextLiquidHistoryAttachment.Increment());
            State->Profile=Args.Contains(TEXT("profile"));State->Bulk=Args.Contains(TEXT("bulk"));
            State->SurfaceFoam=Args.Contains(TEXT("foam"));
            State->CurrentSurface=FParse::Param(FCommandLine::Get(),TEXT("RaftSimLiquidSecondaryCurrentSurface"));
            State->SmoothSparse=FParse::Param(FCommandLine::Get(),TEXT("RaftSimLiquidSmoothSparse"));
            State->ParticleSurfaceOnly=FParse::Param(FCommandLine::Get(),TEXT("RaftSimLiquidParticleSurfaceOnly"));
            if (State->SurfaceFoam && !State->Bulk) return;
            for (TObjectIterator<UNiagaraComponent> It;It;++It)
            {
                auto* Asset=It->GetAsset();
                if (It->GetWorld()!=World || !Asset || Asset->GetOutermost()!=GetTransientPackage() || !Asset->GetName().Contains(TEXT("_Foam_"))) continue;
                if (State->Component.IsValid()) { UE_LOG(LogTemp,Error,TEXT("Ambiguous live liquid fixture"));return; }
                State->Component.Reset(*It);
            }
            if (!State->Component.IsValid() || !State->Component->GetSystemInstanceController()) return;
            auto Controller=State->Component->GetSystemInstanceController();
            State->SystemId=Controller->GetSystemInstanceID();
            const auto& Parameters=State->Component->GetAsset()->GetExposedParameters();
            const FNiagaraVariable Allocation(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.RaftSim Allocation Cells"));
            const FNiagaraVariable Extents(FNiagaraTypeDefinition::GetVec3Def(),TEXT("User.World Grid Extents"));
            if (Parameters.IndexOf(Allocation)!=INDEX_NONE)
            {
                if (Parameters.IndexOf(Extents)==INDEX_NONE || !State->Layout.Configure(
                    Parameters.GetParameterValue<FVector3f>(Allocation),Parameters.GetParameterValue<FVector3f>(Extents),State->Error))
                { UE_LOG(LogTemp,Error,TEXT("Live reconstruction layout: %s"),*State->Error);return; }
            }
            if (State->Component->GetAsset()->GetExposedParameters().IndexOf(RaftSimLiquidSecondarySurface::Variable())!=INDEX_NONE)
            {
                auto* Interface=Cast<UNiagaraDataInterfaceRenderTargetVolume>(State->Component->GetOverrideParameters().GetDataInterface(RaftSimLiquidSecondarySurface::Variable()));
                if (!Interface) { UE_LOG(LogTemp,Error,TEXT("Missing runtime secondary surface interface"));return; }
                State->SecondarySurface=static_cast<FNiagaraDataInterfaceProxyRenderTargetVolumeProxy*>(Interface->GetProxy());
            }
            if (State->Bulk)
            {
                for (TObjectIterator<UNiagaraDataInterfaceGrid3DCollection> It;It;++It)
                {
                    if (It->GetClass()!=UNiagaraDataInterfaceGrid3DCollection::StaticClass()) continue;
                    const auto* const* Found=It->GetSystemInstancesToProxyData_GT().Find(State->SystemId);
                    if (!Found || !*Found) continue;
                    const auto* Data=*Found;
                    if (State->SurfaceFoam && Data->Vars.Num()==1 && Data->Vars[0].GetName()==TEXT("Velocity"))
                    {
                        if (State->Velocity || !Data->UseRGBATexture || Data->NumCells!=State->Layout.Solver ||
                            Data->Offsets.Num()!=1 || Data->Offsets[0]!=0 || Data->Vars[0].GetType()!=FNiagaraTypeDefinition::GetVec3Def())
                        { UE_LOG(LogTemp,Error,TEXT("Unsupported actual foam velocity grid"));return; }
                        State->Velocity=static_cast<FNiagaraDataInterfaceProxyGrid3DCollectionProxy*>(It->GetProxy());
                    }
                    if (Data->Vars.Num()!=1 || Data->Vars[0].GetName()!=TEXT("SolidVelocity_Boundary")) continue;
                    if (State->Boundary || !Data->UseRGBATexture || Data->NumCells!=State->Layout.Solver ||
                        Data->Offsets.Num()!=1 || Data->Offsets[0]!=0 || Data->Vars[0].GetType()!=FNiagaraTypeDefinition::GetVec4Def())
                    { UE_LOG(LogTemp,Error,TEXT("Ambiguous or unsupported live solver classification grid"));return; }
                    State->Boundary=static_cast<FNiagaraDataInterfaceProxyGrid3DCollectionProxy*>(It->GetProxy());
                }
                if (!State->Boundary) { UE_LOG(LogTemp,Error,TEXT("Missing live solver classification"));return; }
                if (State->SurfaceFoam && !State->Velocity) { UE_LOG(LogTemp,Error,TEXT("Missing live foam velocity"));return; }
            }
            const FTransform Transform=State->Component->GetComponentTransform();
            // Current captured fixture is in the origin LWC tile. Supporting
            // a shifted large-world tile requires its explicit simulation basis.
            if (Transform.GetLocation().GetAbsMax()>100000) return;
            State->SimulationToLocalCm=FMatrix44f(Transform.ToInverseMatrixWithScale());
            for (const auto& Emitter:Controller->GetSystemInstance_Unsafe()->GetEmitters())
            {
                if (Emitter->GetEmitterHandle().GetName()==TEXT("Grid3D_FLIP_Secondary_Emitter")) State->SecondaryContext=Emitter->GetGPUContext();
                if (Emitter->GetEmitterHandle().GetName()!=TEXT("Grid3D_FLIP_FluidControl_Emitter")) continue;
                State->Context=Emitter->GetGPUContext();
                int32 Found=0;
                const auto& ParticleData=Emitter->GetParticleData();
                for (const auto& Variable:ParticleData.GetVariables())
                    if (Variable.GetName()==TEXT("Position") || Variable.GetName()==TEXT("Particles.Position"))
                    {
                        if (Variable.GetType()!=FNiagaraTypeDefinition::GetPositionDef() && Variable.GetType()!=FNiagaraTypeDefinition::GetVec3Def()) return;
                        State->PositionOffset=ParticleData.GetVariableLayout(Variable)->GetFloatComponentStart();++Found;
                    }
                if (Found!=1) { UE_LOG(LogTemp,Error,TEXT("Expected one full-precision GPU particle position attribute"));return; }
            }
            State->Dispatch=FNiagaraGpuComputeDispatchInterface::Get(World);
            if (!State->Context || !State->Dispatch) return;
            if (State->CurrentSurface && (!State->SecondarySurface || !State->SecondaryContext)) return;
            TArray<FNiagaraDataInterfaceProxyRenderTargetVolumeProxy*> Candidates;
            for (TObjectIterator<UNiagaraDataInterfaceRenderTargetVolume> It;It;++It)
                Candidates.Add(static_cast<FNiagaraDataInterfaceProxyRenderTargetVolumeProxy*>(It->GetProxy()));
            ENQUEUE_RENDER_COMMAND(RaftSimInstallLiveDensity)([State,Candidates](FRHICommandListImmediate&)
            {
                int32 Found=0;
                for (auto* Proxy:Candidates)
                    if (auto* Data=Proxy->SystemInstancesToProxyData_RT.Find(State->SystemId);Data && Data->RenderTarget.IsValid())
                    { if (Proxy!=State->SecondarySurface) { State->Volume=Proxy;++Found; } }
                if (Found!=1) { State->Error=TEXT("Expected one actual live SimRT volume");return; }
                if (State->SecondarySurface)
                {
                    auto* Cached=State->SecondarySurface->SystemInstancesToProxyData_RT.Find(State->SystemId);
                    if (!Cached || !Cached->RenderTarget.IsValid())
                    { State->Error=TEXT("Secondary surface interface has no actual allocated runtime volume");return; }
                }
                if (State->Profile && GSupportsTimestampRenderQueries)
                {
                    State->QueryPool=RHICreateRenderQueryPool(RQT_AbsoluteTime,64);
                    State->Timing.SetNum(16);State->TimingAvailable=true;
                    for (auto& Slot:State->Timing)
                        for (auto& Query:Slot.Queries) Query=State->QueryPool->AllocateQuery();
                }
                // The material reads SimRT through an external texture binding,
                // including depth prepasses that precede PostRenderOpaque. Tell
                // RDG about that graphics read before any scene passes, so a
                // later compute read cannot hoist a compute-only transition
                // ahead of the untracked material draw in a paused view family.
                State->PreViewCallback=State->Dispatch->GetOnPreInitViewsEvent().AddLambda([State](FRDGBuilder& Graph)
                {
                    auto* Volume=State->Volume->SystemInstancesToProxyData_RT.Find(State->SystemId);
                    if (Volume && Volume->RenderTarget.IsValid())
                        Graph.UseExternalAccessMode(Graph.RegisterExternalTexture(Volume->RenderTarget),ERHIAccess::SRVMask);
                });
                const auto Reconstruct=[State](FRDGBuilder& Graph,bool BeforeSecondary)
                {
                    if (!BeforeSecondary && State->LastFrame==GFrameNumberRenderThread) return;
                    auto& History=Graph.Blackboard.GetOrCreate<FRaftSimLiquidGraphHistories>().ForOwner(State->HistoryAttachment);
                    // Rendering pointers are only promoted at the final tick
                    // of a multi-tick flush. CurrentData is advanced after each
                    // primary dispatch group, before the dependent secondary.
                    auto* Particles=BeforeSecondary?State->Context->MainDataSet->GetCurrentData():State->Context->GetDataToRender(Graph.RHICmdList,true);
                    auto* Volume=State->Volume->SystemInstancesToProxyData_RT.Find(State->SystemId);
                    if (!Particles || !Volume || !Volume->RenderTarget.IsValid()) return;
                    const uint32 Capacity=Particles->GetNumInstancesAllocated();
                    const uint32 CountOffset=Particles->GetGPUInstanceCountBufferOffset();
                    if (!Capacity || Capacity>262144 || CountOffset==INDEX_NONE)
                    { State->Error=TEXT("Unsupported live particle allocation/count offset");return; }
                    auto Target=Graph.RegisterExternalTexture(Volume->RenderTarget);
                    Graph.UseInternalAccessMode(Target);
                    const auto& Layout=State->Layout;
                    if (Target->Desc.Extent!=FIntPoint(Layout.Render.X,Layout.Render.Y) || Target->Desc.Depth!=Layout.Render.Z || Target->Desc.Format!=PF_FloatRGBA)
                    { State->Error=TEXT("Live renderer domain/format mismatch");return; }
                    if (State->Updates>=4096) { State->Error=TEXT("Bounded GPU clock timeline exhausted");return; }
                    auto ClockDesc=FRDGBufferDesc::CreateStructuredDesc(sizeof(FVector4f),4096);ClockDesc.Usage|=BUF_SourceCopy;
                    if (!History.Clock) History.Clock=State->ClockTimeline?Graph.RegisterExternalBuffer(State->ClockTimeline):
                        Graph.CreateBuffer(ClockDesc,TEXT("LiquidDensity.ClockTimeline"));
                    auto Clock=History.Clock;
                    RaftSimRecordLiquidClockGPU(Graph,Target,Clock,uint32(State->Updates),BeforeSecondary || State->Context->bHasTickedThisFrame_RT);
                    Graph.QueueBufferExtraction(Clock,&State->ClockTimeline);
                    // Never wait for a timing result. Busy slots are skipped,
                    // not overwritten, and no particle/grid readback occurs.
                    FLiveDensityReview::FTimingSlot* Timing=nullptr;
                    if (State->QueryPool)
                    {
                        for (auto& Slot:State->Timing)
                        {
                            if (Slot.Pending && State->Updates>=Slot.Update+4)
                            {
                                uint64 T[4];bool Ready=true;
                                for (int32 I=0;I<4;++I)
                                    Ready=RHIGetRenderQueryResult(Slot.Queries[I].GetQuery(),T[I],false) && Ready;
                                if (Ready)
                                {
                                    auto Sample=MakeShared<FJsonObject>();
                                    Sample->SetNumberField(TEXT("update"),Slot.Update);
                                    const bool Ordered=T[0]<=T[1] && T[1]<=T[2] && T[2]<=T[3];
                                    Sample->SetBoolField(TEXT("ordered"),Ordered);
                                    if (Ordered)
                                    {
                                        Sample->SetNumberField(TEXT("pack_density_ms"),(T[1]-T[0])/1000.);
                                        Sample->SetNumberField(TEXT("distance_ms"),(T[2]-T[1])/1000.);
                                        Sample->SetNumberField(TEXT("copy_ms"),(T[3]-T[2])/1000.);
                                        Sample->SetNumberField(TEXT("total_ms"),(T[3]-T[0])/1000.);
                                    }
                                    State->TimingSamples.Add(MakeShared<FJsonValueObject>(Sample));Slot.Pending=false;
                                }
                            }
                            if (!Slot.Pending && !Timing) Timing=&Slot;
                        }
                        if (Timing) { Timing->Update=State->Updates;Timing->Pending=true; }
                        else ++State->TimingSkipped;
                    }
                    auto Timestamp=[&](int32 Index)
                    {
                        if (Timing) Graph.AddPass(RDG_EVENT_NAME("Liquid Live Timestamp %d",Index),ERDGPassFlags::None,
                            [State,Timing,Index](FRHICommandList& Cmd){Cmd.EndRenderQuery(Timing->Queries[Index].GetQuery());});
                    };
                    Timestamp(0);
                    if (BeforeSecondary)
                    {
                        // The preceding Niagara group ended UAV overlap but
                        // deliberately leaves the counter in UAV state. Make
                        // those completed writes visible before our read.
                        auto Counter=State->Dispatch->GetGPUInstanceCounterManager().GetInstanceCountBuffer().UAV;
                        Graph.AddPass(RDG_EVENT_NAME("Liquid Current Stage Counter Handoff"),ERDGPassFlags::None,
                            [Counter](FRHICommandList& Cmd){Cmd.Transition(FRHITransitionInfo(Counter,ERHIAccess::UAVCompute,ERHIAccess::UAVCompute));});
                    }
                    FRDGBufferRef Count=nullptr;
                    auto Positions=RaftSimPackLiquidParticlesGPU(Graph,Particles->GetGPUBufferFloat().SRV,
                        State->Dispatch->GetGPUInstanceCounterManager().GetInstanceCountBuffer().SRV,
                        Particles->GetFloatStride()/sizeof(float),State->PositionOffset,CountOffset,Capacity,State->SimulationToLocalCm,Count,
                        BeforeSecondary?State->Dispatch->GetGPUInstanceCounterManager().GetInstanceCountBuffer().UAV.GetReference():nullptr);
                    if (!Positions) { State->Error=TEXT("Live GPU particle packing failed");return; }
                    auto Density=RaftSimLiquidDensityGPU(Graph,Positions,Capacity,Count,0,Layout.MinimumMeters(),
                        Layout.ExtentMeters(),Layout.Render,.4f,1.f/6,State->Error,State->SmoothSparse);
                    if (!Density.Scalar) return;
                    auto SourceScalar=Density.Scalar;
                    FRDGTextureRef NativeBoundary=nullptr;
                    if (State->Bulk)
                    {
                        auto* Boundary=State->Boundary->SystemInstancesToProxyData_RT.Find(State->SystemId);
                        if (!Boundary || !Boundary->CurrentData || !Boundary->CurrentData->IsValid())
                        { State->Error=TEXT("Missing current solver boundary texture");return; }
                        NativeBoundary=Graph.RegisterExternalTexture(Boundary->CurrentData->GetPooledTexture());
                        if (NativeBoundary->Desc.Extent!=FIntPoint(Layout.Solver.X,Layout.Solver.Y) || NativeBoundary->Desc.Depth!=Layout.Solver.Z)
                        { State->Error=TEXT("Live solver occupancy domain mismatch");return; }
                        auto Bulk=RaftSimLiquidOccupancyGPU(Graph,SourceScalar,NativeBoundary,Density.Diagnostics,State->Error);
                        if (!Bulk.Scalar) return;
                        // The categorical core floor can manufacture exposed
                        // solver-cell shelves. Keep its audit as an A/B control,
                        // but let the particle field alone define this candidate's
                        // surface. Foam still uses the real boundary/flow fields.
                        if (!State->ParticleSurfaceOnly) SourceScalar=Bulk.Scalar;
                        Graph.QueueBufferExtraction(Bulk.Audit,&State->LastOccupancyAudit);
                        Graph.QueueBufferExtraction(Density.DensityFixed,&State->LastDensityFixed);
                        Graph.QueueTextureExtraction(NativeBoundary,&State->LastBoundary);
                    }
                    Timestamp(1);
                    auto Surface=Graph.CreateTexture(Target->Desc,TEXT("LiquidDensity.LiveSurface"));
                    if (!RaftSimLiquidRedistanceRDG(Graph,SourceScalar,Surface,Layout.Render,
                        Layout.RenderSpacingCm(),50,12,State->Error,Target)) return;
                    Timestamp(2);
                    if (State->SurfaceFoam)
                    {
                        auto* Flow=State->Velocity->SystemInstancesToProxyData_RT.Find(State->SystemId);
                        if (!Flow || !Flow->CurrentData || !Flow->CurrentData->IsValid())
                        { State->Error=TEXT("Current GPU foam velocity unavailable");return; }
                        auto NativeVelocity=Graph.RegisterExternalTexture(Flow->CurrentData->GetPooledTexture());
                        auto Previous=History.Foam?History.Foam:State->FoamHistory?Graph.RegisterExternalTexture(State->FoamHistory):nullptr;
                        auto Foam=RaftSimLiquidFoamGPU(Graph,Surface,Previous,NativeVelocity,NativeBoundary,Clock,uint32(State->Updates),
                            Layout.ExtentCm,Layout.PhysicalHalfCm,1,.25f,Density.Diagnostics,State->Error);
                        if (!Foam.Surface) return;
                        if (Previous) Graph.QueueTextureExtraction(Previous,&State->LastFoamInputHistory);
                        else State->LastFoamInputHistory.SafeRelease();
                        Graph.QueueTextureExtraction(Surface,&State->LastFoamCurrent);
                        Graph.QueueTextureExtraction(NativeVelocity,&State->LastFoamVelocity);
                        Graph.QueueTextureExtraction(Foam.Surface,&State->FoamHistory);
                        Graph.QueueBufferExtraction(Foam.Audit,&State->LastFoamAudit);
                        Surface=Foam.Surface;
                        History.Foam=Foam.Surface;
                    }
                    // SimRT is the existing single visible surface. Its green
                    // history is preserved, or evolved by the enabled foam
                    // pass using simulation time. No separate water mesh or physics
                    // grid is changed; next native tick regenerates it on stop.
                    Graph.UseInternalAccessMode(Target);
                    AddCopyTexturePass(Graph,Surface,Target);
                    Graph.UseExternalAccessMode(Target,ERHIAccess::SRVMask);
                    if (State->SecondarySurface)
                    {
                        auto* Cached=State->SecondarySurface->SystemInstancesToProxyData_RT.Find(State->SystemId);
                        if (!Cached || !Cached->RenderTarget.IsValid())
                        { State->Error=TEXT("Secondary rendered-surface cache lost");return; }
                        auto Cache=Graph.RegisterExternalTexture(Cached->RenderTarget);
                        if (Cache==Target || Cache->Desc.Extent!=Target->Desc.Extent || Cache->Desc.Depth!=Target->Desc.Depth || Cache->Desc.Format!=Target->Desc.Format)
                        { State->Error=TEXT("Secondary surface cache aliases renderer or differs in layout");return; }
                        // Publish the same completed field for the next Niagara
                        // step. It must survive the native SimRT write next tick.
                        // This is data history, not an additional visible mesh.
                        Graph.UseInternalAccessMode(Cache);
                        AddCopyTexturePass(Graph,Surface,Cache);
                        Graph.UseExternalAccessMode(Cache,ERHIAccess::SRVMask);
                        State->LastSecondarySurface=Cached->RenderTarget;++State->SecondarySurfacePublishes;
                    }
                    Timestamp(3);
                    Graph.QueueBufferExtraction(Positions,&State->LastPositions);
                    Graph.QueueBufferExtraction(Count,&State->LastCount);
                    Graph.QueueBufferExtraction(Density.Diagnostics,&State->LastDiagnostics);
                    State->LastSurface=Volume->RenderTarget;
                    if (BeforeSecondary || State->Context->bHasTickedThisFrame_RT) ++State->SimulationFrameUpdates;
                    else ++State->RenderOnlyUpdates;
                    State->LastFrame=GFrameNumberRenderThread;++State->Updates;
                    if (BeforeSecondary)
                    {
                        ++State->BeforeSecondaryUpdates;++History.SecondarySteps;
                        State->MaxSecondaryStepsPerGraph=FMath::Max(State->MaxSecondaryStepsPerGraph,History.SecondarySteps);
                    }
                };
                if (State->CurrentSurface)
                    State->StageCallback=URaftSimLiquidStageInterface::PreStageEvent().AddLambda([State,Reconstruct](const FNDIGpuComputePreStageContext& Stage)
                    {
                        if (Stage.GetSystemInstanceID()!=State->SystemId || Stage.GetComputeInstanceData().Context!=State->SecondaryContext) return;
                        ++State->StageEvents;
                        if (Stage.GetSimStageData().bFirstStage)
                        { ++State->SecondaryFirstStageEvents;Reconstruct(Stage.GetGraphBuilder(),true); }
                    });
                State->Callback=State->Dispatch->GetOnPostRenderEvent().AddLambda([State,Reconstruct](FRDGBuilder& Graph)
                {
                    if (State->CurrentSurface && State->Context->bHasTickedThisFrame_RT && State->LastFrame!=GFrameNumberRenderThread)
                    { State->Error=TEXT("Current-surface reconstruction missed secondary pre-stage; refusing late simulation fallback");return; }
                    Reconstruct(Graph,false);
                });
            });
            FlushRenderingCommands();
            if (!State->Callback.IsValid()) { UE_LOG(LogTemp,Error,TEXT("Live density install: %s"),*State->Error);return; }
            Live=State;UE_LOG(LogTemp,Display,TEXT("Live density installed; current-secondary-prestage=%d, no CPU particle upload/readback"),State->CurrentSurface);
        }
        else if (Args.Num()==2 && (Args[0]==TEXT("stop") || Args[0]==TEXT("inspect")) && Live)
        {
            const FString Root=FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()/TEXT("../docs/reconstruction-review-2026-09-07"));
            const FString Output=FPaths::ConvertRelativePathToFull(Args[1]);
            if (!FPaths::IsUnderDirectory(Output,Root) || IFileManager::Get().DirectoryExists(*Output) || IFileManager::Get().FileExists(*Output)) return;
            auto State=Live;
            if (Args[0]==TEXT("stop")) RemoveLiveDensity();else FlushRenderingCommands();
            TArray<uint8> Positions,Status,RawDensity,OccupancyAudit,ClockBytes;TArray<FFloat16Color> Surface,BoundaryPixels;uint32 Count=0;
            TArray<uint8> FoamAudit;TArray<FFloat16Color> FoamCurrent,FoamPrevious,FoamVelocity,SecondarySurfacePixels;
            ENQUEUE_RENDER_COMMAND(RaftSimReadLastLiveDensity)([&](FRHICommandListImmediate& Cmd)
            {
                if (!State->LastCount || !State->LastPositions || !State->LastDiagnostics || !State->LastSurface) return;
                const auto R=State->Layout.Render,S=State->Layout.Solver;
                // Inspection remains blocking, but resource transitions must
                // still be tracked. Raw EnqueueCopy left pooled buffers in
                // their previous UAV/SRV state and omitted SourceCopy usage.
                const auto QueueRead=[&](FRHIGPUBufferReadback& Read,FRDGPooledBuffer* Buffer,uint32 Bytes)
                {
                    FRDGBuilder ReadGraph(Cmd);
                    AddEnqueueCopyPass(ReadGraph,&Read,ReadGraph.RegisterExternalBuffer(Buffer),Bytes);
                    ReadGraph.Execute();
                };
                FRHIGPUBufferReadback CountRead(TEXT("LiveDensity.Count")),PointRead(TEXT("LiveDensity.Positions")),StatusRead(TEXT("LiveDensity.Status"));
                QueueRead(CountRead,State->LastCount,sizeof(uint32));
                QueueRead(StatusRead,State->LastDiagnostics,4*sizeof(uint32));Cmd.SubmitAndBlockUntilGPUIdle();
                Count=*static_cast<const uint32*>(CountRead.Lock(4));CountRead.Unlock();
                const auto* Data=static_cast<const uint8*>(StatusRead.Lock(16));Status.Append(Data,16);StatusRead.Unlock();
                if (Count>262144) return;
                if (Count)
                {
                    QueueRead(PointRead,State->LastPositions,Count*sizeof(FVector4f));Cmd.SubmitAndBlockUntilGPUIdle();
                    const auto* P=static_cast<const uint8*>(PointRead.Lock(Count*sizeof(FVector4f)));Positions.Append(P,Count*sizeof(FVector4f));PointRead.Unlock();
                }
                Cmd.Read3DSurfaceFloatData(State->LastSurface->GetRHI(),FIntRect(0,0,R.X,R.Y),FIntPoint(0,R.Z),Surface);
                if (State->LastSecondarySurface)
                    Cmd.Read3DSurfaceFloatData(State->LastSecondarySurface->GetRHI(),FIntRect(0,0,R.X,R.Y),FIntPoint(0,R.Z),SecondarySurfacePixels);
                if (State->ClockTimeline && State->Updates)
                {
                    const uint32 Size=uint32(State->Updates)*sizeof(FVector4f);
                    FRHIGPUBufferReadback ClockRead(TEXT("LiveDensity.ClockRead"));
                    QueueRead(ClockRead,State->ClockTimeline,Size);Cmd.SubmitAndBlockUntilGPUIdle();
                    ClockBytes.Append(static_cast<const uint8*>(ClockRead.Lock(Size)),Size);ClockRead.Unlock();
                }
                if (State->Bulk && State->LastBoundary && State->LastDensityFixed && State->LastOccupancyAudit)
                {
                    auto ReadBuffer=[&](FRDGPooledBuffer* Buffer,TArray<uint8>& Bytes)
                    {
                        const uint32 Size=Buffer->GetSize();FRHIGPUBufferReadback Readback(TEXT("LiveDensity.BulkAudit"));
                        QueueRead(Readback,Buffer,Size);Cmd.SubmitAndBlockUntilGPUIdle();
                        const auto* Data=static_cast<const uint8*>(Readback.Lock(Size));Bytes.Append(Data,Size);Readback.Unlock();
                    };
                    ReadBuffer(State->LastDensityFixed,RawDensity);ReadBuffer(State->LastOccupancyAudit,OccupancyAudit);
                    Cmd.Read3DSurfaceFloatData(State->LastBoundary->GetRHI(),FIntRect(0,0,S.X,S.Y),FIntPoint(0,S.Z),BoundaryPixels);
                }
                if (State->SurfaceFoam && State->LastFoamCurrent && State->LastFoamInputHistory && State->LastFoamVelocity && State->LastFoamAudit)
                {
                    Cmd.Read3DSurfaceFloatData(State->LastFoamCurrent->GetRHI(),FIntRect(0,0,R.X,R.Y),FIntPoint(0,R.Z),FoamCurrent);
                    Cmd.Read3DSurfaceFloatData(State->LastFoamInputHistory->GetRHI(),FIntRect(0,0,R.X,R.Y),FIntPoint(0,R.Z),FoamPrevious);
                    Cmd.Read3DSurfaceFloatData(State->LastFoamVelocity->GetRHI(),FIntRect(0,0,S.X,S.Y),FIntPoint(0,S.Z),FoamVelocity);
                    const uint32 Size=State->LastFoamAudit->GetSize();FRHIGPUBufferReadback Read(TEXT("LiveFoam.Audit"));
                    QueueRead(Read,State->LastFoamAudit,Size);Cmd.SubmitAndBlockUntilGPUIdle();
                    FoamAudit.Append(static_cast<const uint8*>(Read.Lock(Size)),Size);Read.Unlock();
                }
            });
            FlushRenderingCommands();
            if (!IFileManager::Get().MakeDirectory(*Output,true)) return;
            FFileHelper::SaveArrayToFile(Positions,*(Output/TEXT("positions.rgba32f")));
            FFileHelper::SaveArrayToFile(ClockBytes,*(Output/TEXT("clock.rgba32f")));
            TArray<uint8> Bytes;Bytes.Append(reinterpret_cast<const uint8*>(Surface.GetData()),Surface.Num()*sizeof(FFloat16Color));
            FFileHelper::SaveArrayToFile(Bytes,*(Output/TEXT("surface.rgba16f")));
            if (State->SecondarySurface)
            {
                TArray<uint8> Raw;Raw.Append(reinterpret_cast<const uint8*>(SecondarySurfacePixels.GetData()),SecondarySurfacePixels.Num()*sizeof(FFloat16Color));
                FFileHelper::SaveArrayToFile(Raw,*(Output/TEXT("secondary_surface.rgba16f")));
            }
            if (State->SurfaceFoam)
            {
                FFileHelper::SaveArrayToFile(FoamAudit,*(Output/TEXT("foam_audit.rgba32f")));
                auto SaveHalf=[&](const TCHAR* Name,const TArray<FFloat16Color>& Pixels)
                { TArray<uint8> Raw;Raw.Append(reinterpret_cast<const uint8*>(Pixels.GetData()),Pixels.Num()*sizeof(FFloat16Color));FFileHelper::SaveArrayToFile(Raw,*(Output/Name)); };
                SaveHalf(TEXT("foam_current.rgba16f"),FoamCurrent);SaveHalf(TEXT("foam_previous.rgba16f"),FoamPrevious);
                SaveHalf(TEXT("foam_velocity.rgba16f"),FoamVelocity);
            }
            if (State->Bulk)
            {
                FFileHelper::SaveArrayToFile(RawDensity,*(Output/TEXT("density.u32")));
                FFileHelper::SaveArrayToFile(OccupancyAudit,*(Output/TEXT("occupancy.rg32f")));
                TArray<uint8> BoundaryBytes;BoundaryBytes.Append(reinterpret_cast<const uint8*>(BoundaryPixels.GetData()),BoundaryPixels.Num()*sizeof(FFloat16Color));
                FFileHelper::SaveArrayToFile(BoundaryBytes,*(Output/TEXT("boundary.rgba16f")));
            }
            auto Report=MakeShared<FJsonObject>();Report->SetNumberField(TEXT("gpu_update_count"),State->Updates);
            const auto Vector=[](FVector3f V) { return TArray<TSharedPtr<FJsonValue>>{
                MakeShared<FJsonValueNumber>(V.X),MakeShared<FJsonValueNumber>(V.Y),MakeShared<FJsonValueNumber>(V.Z)}; };
            Report->SetArrayField(TEXT("solver_cells"),Vector(FVector3f(State->Layout.Solver)));
            Report->SetArrayField(TEXT("render_cells"),Vector(FVector3f(State->Layout.Render)));
            Report->SetArrayField(TEXT("computational_extents_cm"),Vector(State->Layout.ExtentCm));
            Report->SetArrayField(TEXT("minimum_m"),Vector(State->Layout.MinimumMeters()));
            Report->SetBoolField(TEXT("graph_history_is_owner_scoped"),true);
            Report->SetNumberField(TEXT("graph_history_attachment"),State->HistoryAttachment);
            Report->SetNumberField(TEXT("updates_with_simulation_tick"),State->SimulationFrameUpdates);
            Report->SetNumberField(TEXT("render_only_updates"),State->RenderOnlyUpdates);
            Report->SetBoolField(TEXT("simulation_tick_flag_is_substep_count"),false);
            Report->SetNumberField(TEXT("last_gpu_particle_count"),Count);Report->SetStringField(TEXT("error"),State->Error);
            TArray<TSharedPtr<FJsonValue>> Values;
            for (int32 I=0;I<Status.Num()/4;++I) Values.Add(MakeShared<FJsonValueNumber>(reinterpret_cast<const uint32*>(Status.GetData())[I]));
            Report->SetArrayField(TEXT("diagnostics"),Values);Report->SetBoolField(TEXT("live_gpu_input"),true);
            Report->SetBoolField(TEXT("per_frame_cpu_readback"),false);Report->SetBoolField(TEXT("stop_readback_is_blocking"),true);
            Report->SetBoolField(TEXT("solver_or_particle_state_modified"),false);Report->SetBoolField(TEXT("photoreal_or_performance_acceptance"),false);
            Report->SetBoolField(TEXT("gpu_timing_requested"),State->Profile);
            Report->SetBoolField(TEXT("gpu_timing_available"),State->TimingAvailable);
            Report->SetBoolField(TEXT("gpu_timing_waits_for_results"),false);
            Report->SetNumberField(TEXT("gpu_timing_skipped_busy_slots"),State->TimingSkipped);
            Report->SetArrayField(TEXT("gpu_timing_samples"),State->TimingSamples);
            Report->SetBoolField(TEXT("live_solver_occupancy_support"),State->Bulk);
            Report->SetStringField(TEXT("kernel_sparse_transition"),State->SmoothSparse?TEXT("continuous-weight-8-24"):TEXT("hard-neighbor-count-25"));
            Report->SetBoolField(TEXT("particle_surface_only"),State->ParticleSurfaceOnly);
            Report->SetBoolField(TEXT("solver_occupancy_floor_applied"),State->Bulk && !State->ParticleSurfaceOnly);
            Report->SetBoolField(TEXT("pack_density_timing_includes_occupancy"),State->Bulk);
            Report->SetBoolField(TEXT("current_surface_foam"),State->SurfaceFoam);
            Report->SetStringField(TEXT("current_surface_foam_revision"),TEXT("surface-strain-v3"));
            Report->SetBoolField(TEXT("copy_timing_includes_surface_foam"),State->SurfaceFoam);
            Report->SetBoolField(TEXT("live_connection_stopped"),Args[0]==TEXT("stop"));
            Report->SetBoolField(TEXT("secondary_shared_render_surface"),State->SecondarySurface!=nullptr);
            Report->SetBoolField(TEXT("current_surface_before_secondary"),State->CurrentSurface);
            Report->SetNumberField(TEXT("secondary_pre_stage_events"),State->StageEvents);
            Report->SetNumberField(TEXT("secondary_first_stage_events"),State->SecondaryFirstStageEvents);
            Report->SetNumberField(TEXT("max_secondary_steps_per_graph"),State->MaxSecondaryStepsPerGraph);
            Report->SetNumberField(TEXT("reconstruction_before_secondary_updates"),State->BeforeSecondaryUpdates);
            Report->SetNumberField(TEXT("secondary_surface_publishes"),State->SecondarySurfacePublishes);
            Report->SetStringField(TEXT("secondary_surface_timing"),State->CurrentSurface
                ? TEXT("Current reconstruction before every secondary first stage; intermediate clock/foam history retained within each render graph")
                : TEXT("Completed post-simulation surface, consumed by next Niagara step; not same-step secondary feedback"));
            FString Json;FJsonSerializer::Serialize(Report,TJsonWriterFactory<>::Create(&Json));FFileHelper::SaveStringToFile(Json,*(Output/TEXT("report.json")));
        }
    }));
}
