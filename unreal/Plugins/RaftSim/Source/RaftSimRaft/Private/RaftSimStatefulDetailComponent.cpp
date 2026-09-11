#include "RaftSimStatefulDetailComponent.h"
#include "RaftSimDetailSnapshot.h"
#include "RaftSimDetailWaterGPU.h"
#include "RaftSimWaterTextureHistory.h"
#include "RaftSimDetailEntrainment.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "RenderingThread.h"
#include "RHICommandList.h"
#include "ProfilingDebugging/CpuProfilerTrace.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

struct FRaftSimDetailRenderState
{
    FRaftSimDetailWaterGPU Simulation;
    FRaftSimWaterTextureHistory History;
    TAtomic<bool> bFailed{false};
    TAtomic<uint64> CompletedSteps{0};
    TUniquePtr<FRaftSimDetailSnapshot> Snapshot;
};

URaftSimStatefulDetailComponent::URaftSimStatefulDetailComponent()
{
    PrimaryComponentTick.bCanEverTick=true;
    PrimaryComponentTick.TickGroup=TG_PostUpdateWork;
}

bool URaftSimStatefulDetailComponent::Initialize(URaftSimWaterRuntimeAdapter* Adapter,
    UMaterialInstanceDynamic* Material,FVector CenterWorldCm,FVector DownstreamWorld,bool bMotionHistory)
{
    if (bReady || !Adapter || !Adapter->HasLiveWindow() || !Adapter->HasRiverCoordinateMap() || !Material || GUsingNullRHI)return false;
    Water=Adapter;SurfaceMaterial=Material;Center=CenterWorldCm;
    bSecondOrder=FParse::Param(FCommandLine::Get(),TEXT("RaftSimSecondOrderDetailReview"));
    bActivityMemory=FParse::Param(FCommandLine::Get(),TEXT("RaftSimActivityMemoryReview"));
    const bool bFineGrid=FParse::Param(FCommandLine::Get(),TEXT("RaftSimFineDetailReview")) &&
        FParse::Param(FCommandLine::Get(),TEXT("RaftSimStatefulCrestReview"));
    DetailSize=bFineGrid ? 256 : 128;
    DetailCellMeters=64.0f/DetailSize;
    // Preserve the physical texture borders exactly across resolutions.
    DetailOriginMeters=-32.25f+0.5f*DetailCellMeters;
#if !UE_BUILD_SHIPPING
    FParse::Value(FCommandLine::Get(),TEXT("RaftSimDetailSnapshot="),SnapshotPrefix);
#endif
    Downstream=FVector(DownstreamWorld.X,DownstreamWorld.Y,0).GetSafeNormal();
    if (Downstream.IsNearlyZero())return false;
    Left=FVector(-Downstream.Y,Downstream.X,0);
    SampleCoordinates.SetNumUninitialized(65*65);
    SampleBasisToDetail.SetNumUninitialized(65*65);
    for (int32 Y=0;Y<65;++Y)for (int32 X=0;X<65;++X)
    {
        const int32 I=Y*65+X;
        const FVector World=Center+100*(Downstream*(X-32)+Left*(Y-32));
        FVector Tangent,Normal;
        if (!Water->WorldToRiverCoordinates(World,SampleCoordinates[I],Tangent,Normal))return false;
        SampleBasisToDetail[I]=FVector4f(FVector::DotProduct(Tangent,Downstream),FVector::DotProduct(Normal,Downstream),
            FVector::DotProduct(Tangent,Left),FVector::DotProduct(Normal,Left));
    }
    if (!UpdateMeanFlow())return false;
    SurfaceTexture=NewObject<UTextureRenderTarget2D>(this);
    SurfaceTexture->ClearColor=FLinearColor::Transparent;
    SurfaceTexture->bCanCreateUAV=true;
    SurfaceTexture->InitCustomFormat(DetailSize,DetailSize,PF_A32B32G32R32F,true);
    SurfaceTexture->UpdateResourceImmediate(true);
    RenderState=MakeShared<FRaftSimDetailRenderState,ESPMode::ThreadSafe>();
    if (bMotionHistory)
    {
        PreviousSurfaceTexture=NewObject<UTextureRenderTarget2D>(this);
        PreviousSurfaceTexture->ClearColor=FLinearColor::Transparent;
        PreviousSurfaceTexture->InitCustomFormat(DetailSize,DetailSize,PF_A32B32G32R32F,true);
        PreviousSurfaceTexture->UpdateResourceImmediate(true);
        SurfaceMaterial->SetTextureParameterValue(TEXT("PreviousStatefulDetailTexture"),PreviousSurfaceTexture);
        auto Shared=RenderState;
        auto* Current=SurfaceTexture->GameThread_GetRenderTargetResource();
        auto* Previous=PreviousSurfaceTexture->GameThread_GetRenderTargetResource();
        ENQUEUE_RENDER_COMMAND(RaftSimDetailHistoryStart)([Shared,Current,Previous](FRHICommandListImmediate& Cmd)
        { if (!Shared->History.Start(Cmd,Current->GetRenderTargetTexture(),Previous->GetRenderTargetTexture()))Shared->bFailed.Store(true); });
    }
    SurfaceMaterial->SetTextureParameterValue(TEXT("StatefulDetailTexture"),SurfaceTexture);
    SurfaceMaterial->SetVectorParameterValue(TEXT("StatefulDetailCenterCm"),FLinearColor(Center.X,Center.Y,0,0));
    SurfaceMaterial->SetVectorParameterValue(TEXT("StatefulDetailBasis"),FLinearColor(Downstream.X,Downstream.Y,Left.X,Left.Y));
    // First cell centre is -32m. Texture border is half a cell earlier.
    SurfaceMaterial->SetVectorParameterValue(TEXT("StatefulDetailDomainM"),FLinearColor(-32.25f,-32.25f,64,64));
    SurfaceMaterial->SetScalarParameterValue(TEXT("StatefulDetailHalfCellM"),DetailCellMeters*0.5f);
    SurfaceMaterial->SetScalarParameterValue(TEXT("StatefulDetailEnable"),1);
    AddTickPrerequisiteActor(GetOwner());
    bReady=true;
    UE_LOG(LogTemp,Display,TEXT("Stateful detail initialized: %dx%d at %.3fm, fixed world crux center=(%.3f,%.3f)cm; one existing carrier, no readback"),DetailSize,DetailSize,DetailCellMeters,Center.X,Center.Y);
    return true;
}

bool URaftSimStatefulDetailComponent::UpdateMeanFlow()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(RaftSimDetail_UpdateMeanFlow);
    if (!Water || !Water->HasLiveWindow())
    { UE_LOG(LogTemp,Error,TEXT("Stateful detail lost live hydraulics; refusing fallback water"));return false; }
    const double Started=FPlatformTime::Seconds();
    TArray<FVector4f> Coarse;Coarse.SetNumZeroed(65*65);
    float MaxSignal=0;
    for (int32 Y=0;Y<65;++Y)for (int32 X=0;X<65;++X)
    {
        const int32 I=Y*65+X;
        FRaftSimWaterSample Sample;
        if (!Water->SampleWaterFieldAtRiverCoordinates(SampleCoordinates[I],Sample))
        { UE_LOG(LogTemp,Error,TEXT("Stateful detail window left authoritative water domain; refusing fallback water"));return false; }
        if (!Sample.bWet || Sample.DepthMeters<=0.01f)continue;
        const FVector4f& Basis=SampleBasisToDetail[I];
        const float U=Basis.X*Sample.VelocityMetersPerSecond.X+Basis.Y*Sample.VelocityMetersPerSecond.Y;
        const float V=Basis.Z*Sample.VelocityMetersPerSecond.X+Basis.W*Sample.VelocityMetersPerSecond.Y;
        const float Speed=FMath::Sqrt(U*U+V*V);
        const float Fr=Speed/FMath::Sqrt(9.81f*Sample.DepthMeters);
        Coarse[Y*65+X]=FVector4f(Sample.DepthMeters,U,V,FMath::Clamp((Fr-0.65f)/0.7f,0.0f,1.0f));
        MaxSignal=FMath::Max(MaxSignal,FMath::Abs(U)+FMath::Abs(V)+2*FMath::Sqrt(9.81f*Sample.DepthMeters));
    }
    TArray<FVector4f> BaseFlow;BaseFlow.SetNumUninitialized(128*128);
    for (int32 Y=0;Y<128;++Y)for (int32 X=0;X<128;++X)
    {
        const int32 R=Y/2,C=X/2;const float Fx=(X%2)*0.5f,Fy=(Y%2)*0.5f;
        BaseFlow[Y*128+X]=FMath::Lerp(FMath::Lerp(Coarse[R*65+C],Coarse[R*65+C+1],Fx),
            FMath::Lerp(Coarse[(R+1)*65+C],Coarse[(R+1)*65+C+1],Fx),Fy);
    }
    FRaftSimDetailEntrainment::Build(FIntPoint(128,128),0.5f,BaseFlow);
    if (DetailSize==128) CachedFlow=MoveTemp(BaseFlow);
    else
    {
        // Hold the existing hydraulic/source field fixed while resolving the
        // perturbation PDE more finely. This is not a finer hydraulic cook.
        // Only the outer quarter-cell needs clamping; resolve fades it to zero.
        CachedFlow.SetNumUninitialized(DetailSize*DetailSize);
        for (int32 Y=0;Y<DetailSize;++Y)for (int32 X=0;X<DetailSize;++X)
        {
            const float GX=FMath::Clamp((DetailOriginMeters+X*DetailCellMeters+32)*2,0.0f,127.0f);
            const float GY=FMath::Clamp((DetailOriginMeters+Y*DetailCellMeters+32)*2,0.0f,127.0f);
            const int32 C=FMath::Min(FMath::FloorToInt(GX),126),R=FMath::Min(FMath::FloorToInt(GY),126);
            CachedFlow[Y*DetailSize+X]=FMath::Lerp(FMath::Lerp(BaseFlow[R*128+C],BaseFlow[R*128+C+1],GX-C),
                FMath::Lerp(BaseFlow[(R+1)*128+C],BaseFlow[(R+1)*128+C+1],GX-C),GY-R);
        }
    }
    // Compute from the actual interpolated input too: averaging depth and
    // velocity does not commute with the nonlinear gravity-wave speed.
    for (const FVector4f& F:CachedFlow)
        MaxSignal=FMath::Max(MaxSignal,FMath::Abs(F.Y)+FMath::Abs(F.Z)+2*FMath::Sqrt(9.81f*F.X));
    StepSeconds=FMath::Min(1.0f/120.0f,0.4f*DetailCellMeters/FMath::Max(MaxSignal,1.0f));
    const double PreparationMs=(FPlatformTime::Seconds()-Started)*1000;
    FlowPreparationTotalMs+=PreparationMs;FlowPreparationMaxMs=FMath::Max(FlowPreparationMaxMs,PreparationMs);++FlowPreparationCount;
    UE_LOG(LogTemp,Verbose,TEXT("Stateful detail mean flow upload preparation %.3fms, max signal %.3f m/s"),PreparationMs,MaxSignal);
    FlowAge=0;return true;
}

void URaftSimStatefulDetailComponent::TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime,TickType,ThisTickFunction);
    if (!bReady)return;
    if (RenderState->bFailed.Load())
    { SurfaceMaterial->SetScalarParameterValue(TEXT("StatefulDetailEnable"),0);bReady=false;return; }
    FlowAge+=DeltaTime;Elapsed+=DeltaTime;Accumulator+=DeltaTime;
    if (FlowAge>=0.125 && !UpdateMeanFlow())
    { SurfaceMaterial->SetScalarParameterValue(TEXT("StatefulDetailEnable"),0);bReady=false;return; }
    const int32 Steps=FMath::Min(16,FMath::FloorToInt(Accumulator/StepSeconds));
    if (!Steps)return;
    // Retain backlog on a slow frame rather than taking an unstable long step.
    // This diagnostic logs lag; release acceptance must reject sustained lag.
    Accumulator-=Steps*double(StepSeconds);
    FRaftSimDetailWaterGrid Grid;Grid.Size=FIntPoint(DetailSize,DetailSize);Grid.CellMeters=DetailCellMeters;
    Grid.OriginMeters=FVector2f(DetailOriginMeters,DetailOriginMeters);Grid.StepSeconds=StepSeconds;Grid.TurbulentHeadMeters=0.06f;
    Grid.bSecondOrder=bSecondOrder;
    Grid.bActivityMemory=bActivityMemory;
    const auto Shared=RenderState;auto Flow=CachedFlow;
    FString CapturePrefix;
    if (!SnapshotPrefix.IsEmpty() && SnapshotRequests<3 && Elapsed>=10+5*SnapshotRequests)
        CapturePrefix=FString::Printf(TEXT("%s_%02d"),*SnapshotPrefix,SnapshotRequests++);
    const double CaptureElapsed=Elapsed;
    const FVector CaptureCenter=Center,CaptureDownstream=Downstream,CaptureLeft=Left;
    FTextureRenderTargetResource* Target=SurfaceTexture->GameThread_GetRenderTargetResource();
    ENQUEUE_RENDER_COMMAND(RaftSimDetailLive)([Shared,Grid,Flow=MoveTemp(Flow),Steps,Target,CapturePrefix,CaptureElapsed,CaptureCenter,CaptureDownstream,CaptureLeft](FRHICommandListImmediate& Cmd)
    {
        if (Shared->Snapshot && Shared->Snapshot->Poll())Shared->Snapshot.Reset();
        if (!CapturePrefix.IsEmpty())
        {
            if (Shared->Snapshot)
            { UE_LOG(LogTemp,Error,TEXT("Detail snapshot still pending; refusing overwrite: %s"),*CapturePrefix); }
            else
            {
                Shared->Snapshot=MakeUnique<FRaftSimDetailSnapshot>();
                Shared->Snapshot->Prefix=CapturePrefix;Shared->Snapshot->Flow=Flow;
                Shared->Snapshot->Size=Grid.Size;Shared->Snapshot->CellMeters=Grid.CellMeters;
                Shared->Snapshot->OriginMeters=Grid.OriginMeters;
                Shared->Snapshot->Elapsed=CaptureElapsed;Shared->Snapshot->Center=CaptureCenter;
                Shared->Snapshot->Downstream=CaptureDownstream;Shared->Snapshot->Left=CaptureLeft;
            }
        }
        const bool bCapture=Shared->Snapshot && Shared->Snapshot->Prefix==CapturePrefix;
        FString Error;
        if (!Shared->Simulation.Advance(Cmd,Grid,Flow,Steps,nullptr,bCapture ? &Shared->Snapshot->StateReadback : nullptr,Error) ||
            !Shared->Simulation.Resolve(Cmd,Target->GetRenderTargetTexture(),Error))
        { Shared->bFailed.Store(true);UE_LOG(LogTemp,Error,TEXT("Stateful detail dispatch rejected: %s"),*Error);return; }
        if (bCapture)
        {
            Shared->Snapshot->SimulationSeconds=Shared->Simulation.GetSimulationSeconds();
            auto Texture=Target->GetRenderTargetTexture();
            Cmd.Transition(FRHITransitionInfo(Texture,ERHIAccess::SRVMask,ERHIAccess::CopySrc));
            Shared->Snapshot->SurfaceReadback.EnqueueCopy(Cmd,Texture);
            Cmd.Transition(FRHITransitionInfo(Texture,ERHIAccess::CopySrc,ERHIAccess::SRVMask));
        }
        Shared->CompletedSteps.Store(Shared->Simulation.GetStepCount());
    });
    if (!bReported && Elapsed>10)
    {
        UE_LOG(LogTemp,Display,TEXT("Stateful detail active: completed_steps=%llu elapsed=%.3fs backlog=%.6fs second_order=%d activity_memory=%d; fixed world window, renderer texture bound"),
            RenderState->CompletedSteps.Load(),Elapsed,Accumulator,bSecondOrder,bActivityMemory);
        bReported=true;
    }
}

void URaftSimStatefulDetailComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (FlowPreparationCount>0)
        UE_LOG(LogTemp,Display,TEXT("Stateful detail flow preparation: updates=%d mean_ms=%.6f max_ms=%.6f elapsed=%.3fs backlog=%.6fs; geometry cached, live flow unchanged"),
            FlowPreparationCount,FlowPreparationTotalMs/FlowPreparationCount,FlowPreparationMaxMs,Elapsed,Accumulator);
    bReady=false;
    if (SurfaceMaterial)SurfaceMaterial->SetScalarParameterValue(TEXT("StatefulDetailEnable"),0);
    if (RenderState)
    {
        auto Shared=RenderState;
        ENQUEUE_RENDER_COMMAND(RaftSimDetailRelease)([Shared](FRHICommandListImmediate&)
        {
            UE_LOG(LogTemp,Display,TEXT("Detail water history: %llu rendered-frame snapshots"),Shared->History.GetCapturedFrames());
            Shared->History.Stop();Shared->Simulation.Reset();
            if (Shared->Snapshot)
            {
                if (!Shared->Snapshot->Poll())
                { UE_LOG(LogTemp,Error,TEXT("Detail snapshot incomplete at teardown")); }
                Shared->Snapshot.Reset();
            }
        });
        RenderState.Reset();
    }
    Super::EndPlay(EndPlayReason);
}
