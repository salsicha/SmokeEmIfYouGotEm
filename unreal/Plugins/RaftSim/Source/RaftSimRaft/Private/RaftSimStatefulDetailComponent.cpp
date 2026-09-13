#include "RaftSimStatefulDetailComponent.h"
#include "RaftSimDetailSnapshot.h"
#include "RaftSimDetailFrameReadback.h"
#include "RaftSimDetailFrameAudit.h"
#include "RaftSimDetailWaterGPU.h"
#include "RaftSimWaterTextureHistory.h"
#include "RaftSimDetailEntrainment.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Engine/TextureRenderTarget2D.h"
#include "GameFramework/Actor.h"
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
    bool bHasWindow=false;
    FVector2f OriginMeters=FVector2f::ZeroVector;
    uint64 Remaps=0,Teleports=0;
    TUniquePtr<FRaftSimDetailSnapshot> Snapshot;
    FRaftSimDetailFrameMailbox Mailbox;
    TUniquePtr<FRaftSimDetailFrameReadback> FrameReadbacks[3];
    uint64 FrameSequence=0,SkippedFrameCopies=0;
    TUniquePtr<FRaftSimDetailFrameAudit> ContactAudit;
};

URaftSimStatefulDetailComponent::URaftSimStatefulDetailComponent()
{
    PrimaryComponentTick.bCanEverTick=true;
    PrimaryComponentTick.TickGroup=TG_PostUpdateWork;
}

void URaftSimStatefulDetailComponent::SetFocusActor(AActor* Actor)
{
    if (FocusActor.Get()==Actor)return;
    if (FocusActor.IsValid())RemoveTickPrerequisiteActor(FocusActor.Get());
    FocusActor=Actor;
    if (Actor)AddTickPrerequisiteActor(Actor);
}

bool URaftSimStatefulDetailComponent::Initialize(URaftSimWaterRuntimeAdapter* Adapter,
    UMaterialInstanceDynamic* Material,FVector CenterWorldCm,FVector DownstreamWorld,bool bMotionHistory,bool bMovingCartesian)
{
    if (bReady || !Adapter || !Adapter->HasLiveWindow() || !Adapter->HasRiverCoordinateMap() || !Material || GUsingNullRHI)return false;
    if (bMovingCartesian && !Adapter->HasCartesianWaterCoordinates())return false;
    Water=Adapter;SurfaceMaterial=Material;Center=CenterWorldCm;FocusWorldCm=CenterWorldCm;
    bMovingWindow=bMovingCartesian;
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
    FParse::Value(FCommandLine::Get(),TEXT("RaftSimDetailContactAudit="),ContactAuditPath);
#endif
    Downstream=FVector(DownstreamWorld.X,DownstreamWorld.Y,0).GetSafeNormal();
    if (Downstream.IsNearlyZero())return false;
    Left=FVector(-Downstream.Y,Downstream.X,0);
    if (bMovingWindow)
    {
        // Fixed east/north metric frame, independent of raft heading. Float
        // origins remain exactly half-metre aligned at this river's extents.
        Downstream=FVector::ForwardVector;Left=FVector(0,Water->GetRiverWorldYSign(),0);
        DetailSize=128;DetailCellMeters=0.5f;DetailOriginMeters=-32.0f;
        Center.X=FMath::RoundToDouble(Center.X/50.0)*50.0;
        Center.Y=FMath::RoundToDouble(Center.Y/50.0)*50.0;
        bSecondOrder=true;bActivityMemory=true;bMotionHistory=true;
    }
    WindowOriginMeters=bMovingWindow
        ? FVector2f(Center.X/100.0-32.0,Center.Y*Left.Y/100.0-32.0)
        : FVector2f(DetailOriginMeters,DetailOriginMeters);
    if (!CacheSampleCoordinates() || !UpdateMeanFlow())return false;
    const int32 TextureHeight=DetailSize+(bMovingWindow ? 1 : 0);
    SurfaceTexture=NewObject<UTextureRenderTarget2D>(this);
    SurfaceTexture->ClearColor=FLinearColor::Transparent;
    SurfaceTexture->bCanCreateUAV=true;
    SurfaceTexture->InitCustomFormat(DetailSize,TextureHeight,PF_A32B32G32R32F,true);
    SurfaceTexture->UpdateResourceImmediate(true);
    if (bMovingWindow)
    {
        ComputeTexture=NewObject<UTextureRenderTarget2D>(this);
        ComputeTexture->ClearColor=FLinearColor::Transparent;
        ComputeTexture->bCanCreateUAV=true;
        ComputeTexture->InitCustomFormat(DetailSize,TextureHeight,PF_A32B32G32R32F,true);
        ComputeTexture->UpdateResourceImmediate(true);
    }
    RenderState=MakeShared<FRaftSimDetailRenderState,ESPMode::ThreadSafe>();
    if (bMotionHistory)
    {
        PreviousSurfaceTexture=NewObject<UTextureRenderTarget2D>(this);
        PreviousSurfaceTexture->ClearColor=FLinearColor::Transparent;
        PreviousSurfaceTexture->InitCustomFormat(DetailSize,TextureHeight,PF_A32B32G32R32F,true);
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
    SurfaceMaterial->SetVectorParameterValue(TEXT("StatefulDetailDomainM"),FLinearColor(-32.25f,-32.25f,64,64));
    SurfaceMaterial->SetScalarParameterValue(TEXT("StatefulDetailHalfCellM"),DetailCellMeters*0.5f);
    SurfaceMaterial->SetScalarParameterValue(TEXT("StatefulDetailEnable"),1);
    SurfaceMaterial->SetScalarParameterValue(TEXT("StatefulDetailWorldYSign"),Left.Y);
    AddTickPrerequisiteActor(GetOwner());
    bReady=true;
    UE_LOG(LogTemp,Display,TEXT("Stateful detail initialized: %dx%d at %.3fm, moving_cartesian=%d center=(%.3f,%.3f)cm; one existing carrier, completed-frame contact=%d, no GPU waits"),DetailSize,DetailSize,DetailCellMeters,bMovingWindow,Center.X,Center.Y,bMovingWindow);
    return true;
}

void URaftSimStatefulDetailComponent::CommitCompletedFrame()
{
    check(IsInGameThread());
    if (!bReady || !bMovingWindow || !RenderState || LastCommitGameFrame==GFrameCounter) return;
    LastCommitGameFrame=GFrameCounter;
    if (RenderState->bFailed.Load())
    {
        SurfaceMaterial->SetScalarParameterValue(TEXT("StatefulDetailEnable"),0);
        PresentedFrame.Reset();bReady=false;return;
    }
    const auto Frame=RenderState->Mailbox.TakeLatest();
    if (Frame && (!PresentedFrame || Frame->Sequence>PresentedFrame->Sequence))
    {
        PresentedFrame=Frame;++PresentationCommits;
        auto* Target=SurfaceTexture->GameThread_GetRenderTargetResource();
        ENQUEUE_RENDER_COMMAND(RaftSimCommitDetailFrame)([Frame,Target](FRHICommandListImmediate& Cmd)
        {
            auto Texture=Target->GetRenderTargetTexture();
            Cmd.Transition(FRHITransitionInfo(Texture,ERHIAccess::Unknown,ERHIAccess::CopyDest));
            Cmd.UpdateTexture2D(Texture,0,FUpdateTextureRegion2D(0,0,0,0,Frame->Size.X,Frame->Size.Y+1),
                Frame->Size.X*sizeof(FVector4f),reinterpret_cast<const uint8*>(Frame->Pixels.GetData()));
            Cmd.Transition(FRHITransitionInfo(Texture,ERHIAccess::CopyDest,ERHIAccess::SRVMask));
        });
    }
    else ++PresentationHolds;
    if (PresentedFrame) MaximumPresentationAge=FMath::Max(MaximumPresentationAge,Elapsed-PresentedFrame->ElapsedSeconds);
}

bool URaftSimStatefulDetailComponent::AuditPresentedFrame()
{
#if !UE_BUILD_SHIPPING
    if (!PresentedFrame || !RenderState || bContactAuditRequested || ContactAuditPath.IsEmpty() ||
        FPaths::FileExists(ContactAuditPath)) return false;
    bContactAuditRequested=true;
    auto Shared=RenderState;auto Frame=PresentedFrame;auto Path=ContactAuditPath;
    auto* Target=SurfaceTexture->GameThread_GetRenderTargetResource();
    ENQUEUE_RENDER_COMMAND(RaftSimDetailContactAudit)([Shared,Frame,Path,Target](FRHICommandListImmediate& Cmd)
    {
        Shared->ContactAudit=MakeUnique<FRaftSimDetailFrameAudit>();
        Shared->ContactAudit->Frame=Frame;Shared->ContactAudit->Path=Path;FString Error;
        if (!Shared->ContactAudit->Start(Cmd,Target->GetRenderTargetTexture(),Error))
        { UE_LOG(LogTemp,Error,TEXT("Detail contact audit dispatch failed: %s"),*Error);Shared->ContactAudit.Reset(); }
    });
    return true;
#else
    return false;
#endif
}

bool URaftSimStatefulDetailComponent::CacheSampleCoordinates()
{
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
    if (bMovingWindow)
    {
        int32 Augmented=0;float MaxAdded=0,MaxCrestSource=0;
        for (int32 Y=0;Y<128;++Y)for (int32 X=0;X<128;++X)
        {
            auto& F=BaseFlow[Y*128+X];
            if (F.X<=.01f)continue;
            // Texture origin and the adapter both use Cartesian east/north
            // metres. Never reinterpret absolute Y as a route lateral offset.
            const FVector2D P(double(WindowOriginMeters.X)+X*.5,double(WindowOriginMeters.Y)+Y*.5);
            const float Crest=Water->SampleAcceptedBreakingSource(P);
            const float Merged=FRaftSimDetailEntrainment::MergeBreakingSource(F,Crest);
            Augmented+=Merged>F.W;MaxAdded=FMath::Max(MaxAdded,Merged-F.W);
            MaxCrestSource=FMath::Max(MaxCrestSource,Crest);F.W=Merged;
        }
        if (!bReportedBreakingSource && Elapsed>=10.)
        {
            UE_LOG(LogTemp,Display,TEXT("Moving detail accepted-crest source: augmented_wet_cells=%d max_added=%.9g max_crest=%.9g origin_m=(%.3f,%.3f); max union, no extra surface or density reset"),
                Augmented,MaxAdded,MaxCrestSource,WindowOriginMeters.X,WindowOriginMeters.Y);
            bReportedBreakingSource=true;
        }
    }
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
    // The run manager may teleport the raft and replace the hydraulic window
    // AFTER the surface actor's tick. Read its current transform here, not a
    // stale early-frame position copied by that actor.
    if (bMovingWindow && FocusActor.IsValid())FocusWorldCm=FocusActor->GetActorLocation();
    if (bMovingWindow && FMath::Max(FMath::Abs(FocusWorldCm.X-Center.X),FMath::Abs(FocusWorldCm.Y-Center.Y))>=800.0)
    {
        Center.X=FMath::RoundToDouble(FocusWorldCm.X/50.0)*50.0;
        Center.Y=FMath::RoundToDouble(FocusWorldCm.Y/50.0)*50.0;
        WindowOriginMeters=FVector2f(Center.X/100.0-32.0,Center.Y*Left.Y/100.0-32.0);
        if (!CacheSampleCoordinates())
        { SurfaceMaterial->SetScalarParameterValue(TEXT("StatefulDetailEnable"),0);bReady=false;return; }
        FlowAge=1;
    }
    if (FlowAge>=0.125 && !UpdateMeanFlow())
    { SurfaceMaterial->SetScalarParameterValue(TEXT("StatefulDetailEnable"),0);bReady=false;return; }
    const int32 Steps=FMath::Min(16,FMath::FloorToInt(Accumulator/StepSeconds));
    if (!Steps)return;
    // Retain backlog on a slow frame rather than taking an unstable long step.
    // This diagnostic logs lag; release acceptance must reject sustained lag.
    Accumulator-=Steps*double(StepSeconds);
    FRaftSimDetailWaterGrid Grid;Grid.Size=FIntPoint(DetailSize,DetailSize);Grid.CellMeters=DetailCellMeters;
    Grid.OriginMeters=WindowOriginMeters;Grid.StepSeconds=StepSeconds;Grid.TurbulentHeadMeters=0.06f;
    Grid.bSecondOrder=bSecondOrder;
    Grid.bActivityMemory=bActivityMemory;
    const auto Shared=RenderState;auto Flow=CachedFlow;
    FString CapturePrefix;
    if (!SnapshotPrefix.IsEmpty() && SnapshotRequests<3 && Elapsed>=10+5*SnapshotRequests)
        CapturePrefix=FString::Printf(TEXT("%s_%02d"),*SnapshotPrefix,SnapshotRequests++);
    const double CaptureElapsed=Elapsed;
    const FVector CaptureCenter=bMovingWindow ? FVector::ZeroVector : Center;
    const FVector CaptureDownstream=Downstream,CaptureLeft=Left;
    const bool bFrameContact=bMovingWindow;
    FTextureRenderTargetResource* Target=(bFrameContact ? ComputeTexture : SurfaceTexture)->GameThread_GetRenderTargetResource();
    ENQUEUE_RENDER_COMMAND(RaftSimDetailLive)([Shared,Grid,Flow=MoveTemp(Flow),Steps,Target,CapturePrefix,CaptureElapsed,CaptureCenter,CaptureDownstream,CaptureLeft,bFrameContact](FRHICommandListImmediate& Cmd)
    {
        if (Shared->ContactAudit && Shared->ContactAudit->Poll()) Shared->ContactAudit.Reset();
        if (bFrameContact) for (auto& Slot:Shared->FrameReadbacks)
        {
            if (!Slot) Slot=MakeUnique<FRaftSimDetailFrameReadback>();
            if (!Slot->Poll(Shared->Mailbox))
            { Shared->bFailed.Store(true);UE_LOG(LogTemp,Error,TEXT("Invalid completed detail frame; refusing unmatched support"));return; }
        }
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
        if (Shared->bFailed.Load())return;
        if (Shared->bHasWindow && Shared->OriginMeters!=Grid.OriginMeters)
        {
            const FVector2f Shift=(Grid.OriginMeters-Shared->OriginMeters)/Grid.CellMeters;
            if (FMath::Abs(Shift.X)>=Grid.Size.X || FMath::Abs(Shift.Y)>=Grid.Size.Y)
            {
                // An explicit teleport has no overlap. Never pretend to have
                // retained state from a different reach or wrap old foam in.
                Shared->Simulation.Reset();++Shared->Teleports;
            }
            else if (!Shared->Simulation.RemapWindow(Cmd,Grid,Flow,Error))
            { Shared->bFailed.Store(true);UE_LOG(LogTemp,Error,TEXT("Stateful detail remap rejected: %s"),*Error);return; }
            else ++Shared->Remaps;
        }
        if (!Shared->Simulation.Advance(Cmd,Grid,Flow,Steps,nullptr,bCapture ? &Shared->Snapshot->StateReadback : nullptr,Error) ||
            !Shared->Simulation.Resolve(Cmd,Target->GetRenderTargetTexture(),Error))
        { Shared->bFailed.Store(true);UE_LOG(LogTemp,Error,TEXT("Stateful detail dispatch rejected: %s"),*Error);return; }
        Shared->OriginMeters=Grid.OriginMeters;Shared->bHasWindow=true;
        if (bFrameContact)
        {
            ++Shared->FrameSequence;bool bCopied=false;
            for (auto& Slot:Shared->FrameReadbacks) if (!Slot->Sequence)
            {
                Slot->Enqueue(Cmd,Target->GetRenderTargetTexture(),Grid.Size,Shared->FrameSequence,
                    CaptureElapsed,Shared->Simulation.GetSimulationSeconds());bCopied=true;break;
            }
            if (!bCopied) ++Shared->SkippedFrameCopies; // Hold the paired presented frame, never stall the PDE.
        }
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
        UE_LOG(LogTemp,Display,TEXT("Stateful detail active: completed_steps=%llu elapsed=%.3fs backlog=%.6fs second_order=%d activity_memory=%d moving_cartesian=%d; renderer texture bound"),
            RenderState->CompletedSteps.Load(),Elapsed,Accumulator,bSecondOrder,bActivityMemory,bMovingWindow);
        bReported=true;
    }
}

void URaftSimStatefulDetailComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (bMovingWindow)
        UE_LOG(LogTemp,Display,TEXT("Detail paired presentation: commits=%llu holds=%llu last_sequence=%llu max_queue_age_s=%.6f; CPU payload equals uploaded texture, no GPU waits"),
            PresentationCommits,PresentationHolds,PresentedFrame ? PresentedFrame->Sequence : 0,MaximumPresentationAge);
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
            UE_LOG(LogTemp,Display,TEXT("Detail water moving window: exact_remaps=%llu teleports=%llu simulated_seconds=%.6f"),Shared->Remaps,Shared->Teleports,Shared->Simulation.GetSimulationSeconds());
            UE_LOG(LogTemp,Display,TEXT("Detail completed-frame copies: sequences=%llu skipped_busy_ring=%llu"),Shared->FrameSequence,Shared->SkippedFrameCopies);
            Shared->History.Stop();Shared->Simulation.Reset();
            if (Shared->ContactAudit)
            {
                if (!Shared->ContactAudit->Poll()) { UE_LOG(LogTemp,Error,TEXT("Detail contact audit incomplete at teardown")); }
                Shared->ContactAudit.Reset();
            }
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
