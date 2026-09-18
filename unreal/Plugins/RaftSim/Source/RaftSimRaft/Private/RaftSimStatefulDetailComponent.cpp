#include "RaftSimStatefulDetailComponent.h"
#include "RaftSimDetailSnapshot.h"
#include "RaftSimFrothFlowHistory.h"
#include "RaftSimDetailFrameReadback.h"
#include "RaftSimDetailFrameUpload.h"
#include "RaftSimDetailFrameAudit.h"
#include "RaftSimDetailWaterGPU.h"
#include "RaftSimTotalDepthSourceGPU.h"
#include "RaftSimTemporalBoundaryAudit.h"
#include "RaftSimNonlinearEvolutionAudit.h"
#include "RaftSimWaterTextureHistory.h"
#include "RaftSimDetailEntrainment.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimRiverWaterStreamingActor.h"
#include "RaftSimDetailSourceFootprint.h"
#include "EngineUtils.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "RenderingThread.h"
#include "RHICommandList.h"
#include "ProfilingDebugging/CpuProfilerTrace.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

namespace
{
int32 LiveSourceSampleSide()
{
    static const bool Capture=FParse::Param(FCommandLine::Get(),TEXT("RaftSimCapturePressureStencil"));
    return Capture?69:67;
}
}

struct FRaftSimDetailRenderState
{
    FRaftSimDetailWaterGPU Simulation;
    FRaftSimTotalDepthSourceGPU TotalSource;
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
    TUniquePtr<FRaftSimTemporalBoundaryAudit> TemporalAudit;
    bool bTemporalAuditRequested=false;
    TUniquePtr<FRaftSimNonlinearEvolutionAudit> NonlinearAudit;
    FRaftSimFrothFlowHistory FrothFlowHistory;
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
    if(bMovingWindow && !WaterClock.Initialize(Water->GetCommittedStepSeconds()))return false;
    Accumulator=0;FlowAge=1;Elapsed=0;
    bSecondOrder=FParse::Param(FCommandLine::Get(),TEXT("RaftSimSecondOrderDetailReview"));
    bActivityMemory=FParse::Param(FCommandLine::Get(),TEXT("RaftSimActivityMemoryReview"));
    // Promote only the full-reach scenario verified with paired GPU/contact
    // captures. Other rivers remain explicit until their own depth/flow review.
    const bool bVerifiedFullReach=bMovingWindow && GetWorld() &&
        GetWorld()->GetMapName().EndsWith(TEXT("L_SouthForkAmerican_FullReach"));
    bFiniteDepthDispersion=(bVerifiedFullReach || FParse::Param(FCommandLine::Get(),TEXT("RaftSimFiniteDepthDetailReview"))) &&
        !FParse::Param(FCommandLine::Get(),TEXT("RaftSimShallowPressureReview"));
    if (bFiniteDepthDispersion)bSecondOrder=true;
    const bool bFineGrid=FParse::Param(FCommandLine::Get(),TEXT("RaftSimFineDetailReview")) &&
        FParse::Param(FCommandLine::Get(),TEXT("RaftSimStatefulCrestReview"));
    DetailSize=bFineGrid ? 256 : 128;
    DetailCellMeters=64.0f/DetailSize;
    // Preserve the physical texture borders exactly across resolutions.
    DetailOriginMeters=-32.25f+0.5f*DetailCellMeters;
#if !UE_BUILD_SHIPPING
    FParse::Value(FCommandLine::Get(),TEXT("RaftSimDetailSnapshot="),SnapshotPrefix);
    FParse::Value(FCommandLine::Get(),TEXT("RaftSimDetailContactAudit="),ContactAuditPath);
    FParse::Value(FCommandLine::Get(),TEXT("RaftSimTemporalBoundaryAudit="),TemporalBoundaryAuditPath);
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
    if (!EnsureSourceCoverage(WindowOriginMeters) || !CacheSampleCoordinates() || !UpdateMeanFlow())return false;
    const int32 TextureHeight=DetailSize+(bMovingWindow ? 1 : 0);
    SurfaceTexture=NewObject<UTextureRenderTarget2D>(this);
    SurfaceTexture->ClearColor=FLinearColor::Transparent;
    SurfaceTexture->bCanCreateUAV=true;
    SurfaceTexture->InitCustomFormat(DetailSize,TextureHeight,PF_A32B32G32R32F,true);
    SurfaceTexture->UpdateResourceImmediate(true);
    if(bVerifiedFullReach && !FParse::Param(FCommandLine::Get(),TEXT("RaftSimLegacyFoamFlow")))
    {
        FoamFlowTexture.Reset(NewObject<UTextureRenderTarget2D>(this));
        FoamFlowTexture->ClearColor=FLinearColor::Transparent;
        FoamFlowTexture->InitCustomFormat(DetailSize,TextureHeight,PF_A32B32G32R32F,true);
        FoamFlowTexture->UpdateResourceImmediate(true);
        SurfaceMaterial->SetTextureParameterValue(TEXT("StatefulFoamFlowTexture"),FoamFlowTexture.Get());
        UE_LOG(LogTemp,Display,TEXT("Paired foam flow: displayed density and captured mean current share one publication; no solver or geometry change"));
    }
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
    UE_LOG(LogTemp,Display,TEXT("Stateful detail initialized: %dx%d at %.3fm, moving_cartesian=%d center=(%.3f,%.3f)cm; one existing carrier, completed-frame contact=%d, finite_depth=%d pressure_iterations=%d, no GPU waits"),DetailSize,DetailSize,DetailCellMeters,bMovingWindow,Center.X,Center.Y,bMovingWindow,bFiniteDepthDispersion,FRaftSimDetailWaterGrid().PressureIterations);
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
        auto* FlowTarget=FoamFlowTexture.IsValid()?FoamFlowTexture->GameThread_GetRenderTargetResource():nullptr;
        auto Shared=RenderState;
        ENQUEUE_RENDER_COMMAND(RaftSimCommitDetailFrame)([Frame,Target,FlowTarget,Shared](FRHICommandListImmediate& Cmd)
        {
            if(!RaftSimUploadDetailFrame(Cmd,*Frame,Target->GetRenderTargetTexture(),
                FlowTarget?FlowTarget->GetRenderTargetTexture():nullptr))
            {
                Shared->bFailed.Store(true);
                UE_LOG(LogTemp,Error,TEXT("Paired detail publication rejected: incomplete or mismatched texture payload"));
            }
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

bool URaftSimStatefulDetailComponent::EnsureSourceCoverage(FVector2f NextOrigin)
{
    if(!bMovingWindow)return true;
    FBox2D Required,Current;
    if(!Water || !FRaftSimDetailSourceFootprint::Required(WindowOriginMeters,NextOrigin,LiveSourceSampleSide(),Required))return false;
    if(Water->GetLiveWaterFieldBoundsM(Current) && FRaftSimDetailSourceFootprint::Covered(Current,Required))return true;
    // Called after observing the current raft transform, immediately before
    // closing/current source sampling. No dependency on the periodic actor tick.
    for(TActorIterator<ARaftSimRiverWaterStreamingActor> It(GetWorld());It;++It)
        if(It->EnsureDetailSourceCoverage(Water,Required))return true;
    UE_LOG(LogTemp,Error,TEXT("No complete native crop for detail source footprint min=(%.9f,%.9f) max=(%.9f,%.9f); refusing fallback water"),
        Required.Min.X,Required.Min.Y,Required.Max.X,Required.Max.Y);
    return false;
}

bool URaftSimStatefulDetailComponent::CacheSampleCoordinates()
{
    if(!SampleGrid.Register(bMovingWindow ? WindowOriginMeters : FVector2f::ZeroVector))return false;
    const int32 Side=bMovingWindow?LiveSourceSampleSide():65,Halo=(Side-65)/2;
    SampleCoordinates.SetNumUninitialized(Side*Side);
    SampleBasisToDetail.SetNumUninitialized(Side*Side);
    for (int32 Y=0;Y<Side;++Y)for (int32 X=0;X<Side;++X)
    {
        const int32 I=Y*Side+X;
        // Keep the physical sampling lattice and its exterior halo world-fixed.
        const FVector World=bMovingWindow
            ? FVector(100.*(double(SampleGrid.CoarseOriginMeters.X)+X-Halo),
                100.*Left.Y*(double(SampleGrid.CoarseOriginMeters.Y)+Y-Halo),Center.Z)
            : Center+100*(Downstream*(X-32)+Left*(Y-32));
        FVector Tangent,Normal;
        if (!Water->WorldToRiverCoordinates(World,SampleCoordinates[I],Tangent,Normal))return false;
        SampleBasisToDetail[I]=FVector4f(FVector::DotProduct(Tangent,Downstream),FVector::DotProduct(Normal,Downstream),
            FVector::DotProduct(Tangent,Left),FVector::DotProduct(Normal,Left));
    }
    if(bMovingWindow)
    {
        FaceSampleCoordinates.SetNumUninitialized(512);FaceSampleBasisToDetail.SetNumUninitialized(512);
        for(int32 I=0;I<512;++I)
        {
            const auto P=WindowOriginMeters+.5f*FRaftSimTotalDepthSource::ExteriorFace(I);
            const FVector World(100.*P.X,100.*Left.Y*P.Y,Center.Z);FVector Tangent,Normal;
            if(!Water->WorldToRiverCoordinates(World,FaceSampleCoordinates[I],Tangent,Normal))return false;
            FaceSampleBasisToDetail[I]=FVector4f(FVector::DotProduct(Tangent,Downstream),FVector::DotProduct(Normal,Downstream),
                FVector::DotProduct(Tangent,Left),FVector::DotProduct(Normal,Left));
        }
    }
    return true;
}

TSharedPtr<const FRaftSimTotalDepthSource,ESPMode::ThreadSafe> URaftSimStatefulDetailComponent::SampleClosingWindow(FString& Error)
{
    double Time=0,FinalTime=0;
    const int32 Side=LiveSourceSampleSide();
    if(!Water || !Water->GetLiveFieldTimeSeconds(Time) || SampleCoordinates.Num()!=Side*Side || FaceSampleCoordinates.Num()!=512)
    {Error=TEXT("Closing window lacks an authoritative native field");return nullptr;}
    TArray<FVector4f> HUV,Geometry;TArray<float> Faces;
    HUV.Reserve(Side*Side);Geometry.Reserve(Side*Side);Faces.Reserve(512);
    for(int32 I=0;I<SampleCoordinates.Num();++I)
    {
        FRaftSimWaterSample S;
        if(!Water->SampleWaterFieldAtRiverCoordinates(SampleCoordinates[I],S))
        {Error=TEXT("Closing window left authoritative water domain");return nullptr;}
        const auto B=SampleBasisToDetail[I];
        HUV.Add(FVector4f(S.DepthMeters,B.X*S.VelocityMetersPerSecond.X+B.Y*S.VelocityMetersPerSecond.Y,
            B.Z*S.VelocityMetersPerSecond.X+B.W*S.VelocityMetersPerSecond.Y,0));
        Geometry.Add(FVector4f(S.BedHeightMeters,S.SurfaceHeightMeters,S.DepthMeters,S.bWet?1.f:0.f));
    }
    for(int32 I=0;I<512;++I)
    {
        FRaftSimWaterSample S;
        if(!Water->SampleWaterFieldAtRiverCoordinates(FaceSampleCoordinates[I],S))
        {Error=TEXT("Closing window has no actual exterior-face observation");return nullptr;}
        const auto B=FaceSampleBasisToDetail[I];
        Faces.Add(I<256?B.X*S.VelocityMetersPerSecond.X+B.Y*S.VelocityMetersPerSecond.Y:
            B.Z*S.VelocityMetersPerSecond.X+B.W*S.VelocityMetersPerSecond.Y);
    }
    if(!Water->GetLiveFieldTimeSeconds(FinalTime) || FinalTime!=Time)
    {Error=TEXT("Native field changed while sampling closing window");return nullptr;}
    return FRaftSimTotalDepthSource::Build(HUV,Geometry,Faces,WindowOriginMeters,Time,TotalDepthSourceRevision+1,Error);
}

bool URaftSimStatefulDetailComponent::UpdateMeanFlow()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(RaftSimDetail_UpdateMeanFlow);
    if (!Water || !Water->HasLiveWindow())
    { UE_LOG(LogTemp,Error,TEXT("Stateful detail lost live hydraulics; refusing fallback water"));return false; }
    const double Started=FPlatformTime::Seconds();
    double FieldTime=0;
    if(bMovingWindow && !Water->GetLiveFieldTimeSeconds(FieldTime))return false;
    TArray<FVector4f> Coarse;Coarse.SetNumZeroed(65*65);
    const bool bCaptureGeometry=!SnapshotPrefix.IsEmpty();
    const bool bNeedPairedGeometry=bCaptureGeometry || bMovingWindow;
    TArray<FVector4f> CoarseGeometry;
    if (bNeedPairedGeometry)CoarseGeometry.SetNumUninitialized(65*65);
    TArray<FVector4f> UnmaskedHUV;
    TArray<FVector4f> SourceGeometry;
    const int32 Side=bMovingWindow?LiveSourceSampleSide():65,Halo=(Side-65)/2;
    if(bMovingWindow){UnmaskedHUV.SetNumUninitialized(Side*Side);SourceGeometry.SetNumUninitialized(Side*Side);}
    float MaxSignal=0;
    for (int32 Y=0;Y<Side;++Y)for (int32 X=0;X<Side;++X)
    {
        const int32 I=Y*Side+X;
        FRaftSimWaterSample Sample;
        if (!Water->SampleWaterFieldAtRiverCoordinates(SampleCoordinates[I],Sample))
        { UE_LOG(LogTemp,Error,TEXT("Stateful detail window left authoritative water domain; refusing fallback water"));return false; }
        const FVector4f Geometry(Sample.BedHeightMeters,Sample.SurfaceHeightMeters,
            Sample.DepthMeters,Sample.bWet ? 1.f : 0.f);
        const FVector4f& Basis=SampleBasisToDetail[I];
        const float U=Basis.X*Sample.VelocityMetersPerSecond.X+Basis.Y*Sample.VelocityMetersPerSecond.Y;
        const float V=Basis.Z*Sample.VelocityMetersPerSecond.X+Basis.W*Sample.VelocityMetersPerSecond.Y;
        if(bMovingWindow)
        {UnmaskedHUV[I]=FVector4f(Sample.DepthMeters,U,V,0);SourceGeometry[I]=Geometry;}
        // The new outer samples feed only explicit source ghosts. Legacy mean,
        // entrainment and timestep inputs retain exactly their previous65x65 nodes.
        const int32 CX=X-Halo,CY=Y-Halo;
        if(CX<0 || CY<0 || CX>=65 || CY>=65)continue;
        const int32 J=CY*65+CX;
        if(bNeedPairedGeometry)CoarseGeometry[J]=Geometry;
        if (!Sample.bWet || Sample.DepthMeters<=0.01f)continue;
        const float Speed=FMath::Sqrt(U*U+V*V);
        const float Fr=Speed/FMath::Sqrt(9.81f*Sample.DepthMeters);
        Coarse[J]=FVector4f(Sample.DepthMeters,U,V,FMath::Clamp((Fr-0.65f)/0.7f,0.0f,1.0f));
        MaxSignal=FMath::Max(MaxSignal,FMath::Abs(U)+FMath::Abs(V)+2*FMath::Sqrt(9.81f*Sample.DepthMeters));
    }
    TSharedPtr<const FRaftSimTotalDepthSource,ESPMode::ThreadSafe> NextTotalSource;
    if(bMovingWindow)
    {
        TArray<float> FaceVelocity;FaceVelocity.SetNumUninitialized(512);
        for(int32 I=0;I<512;++I)
        {
            FRaftSimWaterSample Sample;
            if(!Water->SampleWaterFieldAtRiverCoordinates(FaceSampleCoordinates[I],Sample))return false;
            const auto Basis=FaceSampleBasisToDetail[I];
            FaceVelocity[I]=I<256?Basis.X*Sample.VelocityMetersPerSecond.X+Basis.Y*Sample.VelocityMetersPerSecond.Y:
                Basis.Z*Sample.VelocityMetersPerSecond.X+Basis.W*Sample.VelocityMetersPerSecond.Y;
        }
        double FinalFieldTime=0;
        if(!Water->GetLiveFieldTimeSeconds(FinalFieldTime) || FieldTime!=FinalFieldTime)return false;
        FString SourceError;
        const uint64 NextRevision=PendingClosingWindowSource?PendingClosingWindowSource->Revision+1:TotalDepthSourceRevision+1;
        NextTotalSource=FRaftSimTotalDepthSource::Build(UnmaskedHUV,SourceGeometry,FaceVelocity,WindowOriginMeters,FieldTime,NextRevision,SourceError);
        if(!NextTotalSource)
        {UE_LOG(LogTemp,Error,TEXT("Live total-depth source rejected: %s"),*SourceError);return false;}
        if(PendingClosingWindowSource)
        {
            if(PendingClosingWindowSource->SampleSeconds!=FieldTime)
            {UE_LOG(LogTemp,Error,TEXT("Window move lost its same-instant closing observation"));return false;}
            auto Paired=MakeShared<FRaftSimTotalDepthSource,ESPMode::ThreadSafe>(*NextTotalSource);
            Paired->ClosingWindowSource=PendingClosingWindowSource;NextTotalSource=Paired;
        }
    }
    TArray<FVector4f> BaseFlow;BaseFlow.SetNumUninitialized(128*128);
    TArray<FVector4f> BaseGeometry;
    if (bCaptureGeometry)BaseGeometry.SetNumUninitialized(128*128);
    for (int32 Y=0;Y<128;++Y)for (int32 X=0;X<128;++X)
    {
        BaseFlow[Y*128+X]=SampleGrid.Interpolate<FVector4f>(Coarse,X,Y);
        if (bCaptureGeometry)
            BaseGeometry[Y*128+X]=SampleGrid.Interpolate<FVector4f>(CoarseGeometry,X,Y);
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
    if (DetailSize==128)
    { CachedFlow=MoveTemp(BaseFlow);CachedMeanGeometry=MoveTemp(BaseGeometry); }
    else
    {
        // Hold the existing hydraulic/source field fixed while resolving the
        // perturbation PDE more finely. This is not a finer hydraulic cook.
        // Only the outer quarter-cell needs clamping; resolve fades it to zero.
        CachedFlow.SetNumUninitialized(DetailSize*DetailSize);
        if (bCaptureGeometry)CachedMeanGeometry.SetNumUninitialized(DetailSize*DetailSize);
        for (int32 Y=0;Y<DetailSize;++Y)for (int32 X=0;X<DetailSize;++X)
        {
            const float GX=FMath::Clamp((DetailOriginMeters+X*DetailCellMeters+32)*2,0.0f,127.0f);
            const float GY=FMath::Clamp((DetailOriginMeters+Y*DetailCellMeters+32)*2,0.0f,127.0f);
            const int32 C=FMath::Min(FMath::FloorToInt(GX),126),R=FMath::Min(FMath::FloorToInt(GY),126);
            CachedFlow[Y*DetailSize+X]=FMath::Lerp(FMath::Lerp(BaseFlow[R*128+C],BaseFlow[R*128+C+1],GX-C),
                FMath::Lerp(BaseFlow[(R+1)*128+C],BaseFlow[(R+1)*128+C+1],GX-C),GY-R);
            if (bCaptureGeometry)
                CachedMeanGeometry[Y*DetailSize+X]=FMath::Lerp(FMath::Lerp(BaseGeometry[R*128+C],BaseGeometry[R*128+C+1],GX-C),
                    FMath::Lerp(BaseGeometry[(R+1)*128+C],BaseGeometry[(R+1)*128+C+1],GX-C),GY-R);
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
    if(NextTotalSource)
    {
        if(CachedTotalDepthSource && CachedTotalDepthSource->OriginMeters!=NextTotalSource->OriginMeters)
        {
            const auto& Old=*CachedTotalDepthSource;const auto& Next=*NextTotalSource;
            const FVector2f Shift=(Next.OriginMeters-Old.OriginMeters)/Next.CellMeters;
            int32 Count=0,Changed=0;float Maximum=0;
            if(FMath::Abs(Shift.X)<128 && FMath::Abs(Shift.Y)<128)
                for(int32 Y=0;Y<128;++Y)for(int32 X=0;X<128;++X)
                {
                    const int32 PX=X+int32(Shift.X),PY=Y+int32(Shift.Y);
                    if(PX<0 || PY<0 || PX>=128 || PY>=128)continue;
                    const float Delta=FMath::Abs(Next.Bed[Y*128+X]-Old.Bed[PY*128+PX]);
                    ++Count;Changed+=Delta!=0;Maximum=FMath::Max(Maximum,Delta);
                }
            UE_LOG(LogTemp,Display,TEXT("Live source registration: overlap=%d bed_changed=%d max_bed_delta_m=%.9g origin=(%.3f,%.3f) coarse=(%.3f,%.3f); sampled flow remains time-varying"),
                Count,Changed,Maximum,Next.OriginMeters.X,Next.OriginMeters.Y,Next.CoarseSampleOriginMeters.X,Next.CoarseSampleOriginMeters.Y);
            int32 GhostCount=0,GhostChanged=0;float GhostMaximum=0;
            for(int32 I=0;I<Next.ExteriorState.Num();++I)
            {
                const auto P=FRaftSimTotalDepthSource::ExteriorCell(I)+FIntPoint(int32(Shift.X),int32(Shift.Y));
                if(P.X<0 || P.Y<0 || P.X>=128 || P.Y>=128)continue;
                const float Delta=FMath::Abs(Next.ExteriorBed[I]-Old.Bed[P.Y*128+P.X]);
                ++GhostCount;GhostChanged+=Delta!=0;GhostMaximum=FMath::Max(GhostMaximum,Delta);
            }
            UE_LOG(LogTemp,Display,TEXT("Live exterior registration: former_interior=%d bed_changed=%d max_bed_delta_m=%.9g; actual world halo, not clamped edge values"),
                GhostCount,GhostChanged,GhostMaximum);
        }
        CachedTotalDepthSource=MoveTemp(NextTotalSource);TotalDepthSourceRevision=CachedTotalDepthSource->Revision;
        PendingClosingWindowSource.Reset();
    }
    MeanSampleElapsed=Elapsed;FlowAge=0;return true;
}

void URaftSimStatefulDetailComponent::TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime,TickType,ThisTickFunction);
    if (!bReady)return;
    if (RenderState->bFailed.Load())
    { SurfaceMaterial->SetScalarParameterValue(TEXT("StatefulDetailEnable"),0);bReady=false;return; }
    double SimulationDelta=DeltaTime;
    if(!FMath::IsFinite(DeltaTime) || DeltaTime<0 ||
        (bMovingWindow && (!Water || Water->GetStatus()==ERaftSimWaterRuntimeStatus::Faulted ||
            !WaterClock.Observe(Water->GetCommittedStepSeconds(),SimulationDelta))))
    {
        SurfaceMaterial->SetScalarParameterValue(TEXT("StatefulDetailEnable"),0);bReady=false;
        UE_LOG(LogTemp,Error,TEXT("Detail committed-water clock invalid/regressed; refusing unpaired elapsed time"));return;
    }
    // Wall time remains presentation-age/refresh telemetry. The normal moving
    // field evolves only the duration actually committed by water, including
    // zero when the fixed-step owner has not advanced. Review tanks retain
    // their explicit standalone wall-clock behavior.
    FlowAge+=DeltaTime;Elapsed+=DeltaTime;Accumulator+=SimulationDelta;
    // The run manager may teleport the raft and replace the hydraulic window
    // AFTER the surface actor's tick. Read its current transform here, not a
    // stale early-frame position copied by that actor.
    if (bMovingWindow && FocusActor.IsValid())FocusWorldCm=FocusActor->GetActorLocation();
    const bool bMove=bMovingWindow && FMath::Max(FMath::Abs(FocusWorldCm.X-Center.X),FMath::Abs(FocusWorldCm.Y-Center.Y))>=800.0;
    const double NextX=bMove ? FMath::RoundToDouble(FocusWorldCm.X/50.0)*50.0 : Center.X;
    const double NextY=bMove ? FMath::RoundToDouble(FocusWorldCm.Y/50.0)*50.0 : Center.Y;
    const FVector2f NextOrigin=bMove ? FVector2f(NextX/100.0-32.0,NextY*Left.Y/100.0-32.0) : WindowOriginMeters;
    if(!EnsureSourceCoverage(NextOrigin))
    { SurfaceMaterial->SetScalarParameterValue(TEXT("StatefulDetailEnable"),0);bReady=false;return; }
    if (bMove)
    {
        const auto Shift=(NextOrigin-WindowOriginMeters)/.5f;
        PendingClosingWindowSource.Reset();
        if(FMath::Abs(Shift.X)<128 && FMath::Abs(Shift.Y)<128)
        {
            FString ClosingError;PendingClosingWindowSource=SampleClosingWindow(ClosingError);
            // A missing old-domain observation makes the candidate nonlinear
            // transfer inadmissible. It must not disable the existing solver
            // merely because scenario loading replaced its native domain.
            if(!PendingClosingWindowSource)
                UE_LOG(LogTemp,Warning,TEXT("No admissible nonlinear closing source: %s; existing playable path unchanged"),*ClosingError);
        }
        Center.X=NextX;Center.Y=NextY;WindowOriginMeters=NextOrigin;
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
    Grid.bFiniteDepthDispersion=bFiniteDepthDispersion;
    // The isolated strain term failed real shallow-bank evolution. Preserve
    // it for explicit research, never enable it through the normal scenario.
    static const bool bMeanStrainReview=FParse::Param(FCommandLine::Get(),TEXT("RaftSimMeanStrainReview"));
    Grid.bExperimentalMeanStrain=bMeanStrainReview;
    const auto Shared=RenderState;auto Flow=CachedFlow;
    const auto TotalSource=CachedTotalDepthSource;
    const auto TemporalAuditPath=TemporalBoundaryAuditPath;
    FString CapturePrefix;
    if (!SnapshotPrefix.IsEmpty() && SnapshotRequests<3 && Elapsed>=10+5*SnapshotRequests)
        CapturePrefix=FString::Printf(TEXT("%s_%02d"),*SnapshotPrefix,SnapshotRequests++);
    const double CaptureElapsed=Elapsed;
    const double CaptureMeanElapsed=MeanSampleElapsed;
    TArray<FVector4f> CaptureGeometry;
    if (!CapturePrefix.IsEmpty())CaptureGeometry=CachedMeanGeometry;
    const FVector CaptureCenter=bMovingWindow ? FVector::ZeroVector : Center;
    const FVector CaptureDownstream=Downstream,CaptureLeft=Left;
    const bool bFrameContact=bMovingWindow;
    const bool bPairedFoamFlow=FoamFlowTexture.IsValid();
    bool bCaptureFrothHistory=false;
#if !UE_BUILD_SHIPPING
    bCaptureFrothHistory=bMovingWindow && !SnapshotPrefix.IsEmpty() &&
        FParse::Param(FCommandLine::Get(),TEXT("RaftSimFrothHistoryAudit"));
#endif
    FTextureRenderTargetResource* Target=(bFrameContact ? ComputeTexture : SurfaceTexture)->GameThread_GetRenderTargetResource();
    ENQUEUE_RENDER_COMMAND(RaftSimDetailLive)([Shared,Grid,Flow=MoveTemp(Flow),TotalSource,TemporalAuditPath,CaptureGeometry=MoveTemp(CaptureGeometry),CaptureMeanElapsed,Steps,Target,CapturePrefix,CaptureElapsed,CaptureCenter,CaptureDownstream,CaptureLeft,bFrameContact,bPairedFoamFlow,bCaptureFrothHistory](FRHICommandListImmediate& Cmd)
    {
        if (Shared->ContactAudit && Shared->ContactAudit->Poll()) Shared->ContactAudit.Reset();
        if (Shared->TemporalAudit && Shared->TemporalAudit->Poll())Shared->TemporalAudit.Reset();
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
                Shared->Snapshot->MeanGeometry=CaptureGeometry; // Immutable render-command capture.
                Shared->Snapshot->MeanSampleElapsed=CaptureMeanElapsed;
                Shared->Snapshot->Size=Grid.Size;Shared->Snapshot->CellMeters=Grid.CellMeters;
                Shared->Snapshot->OriginMeters=Grid.OriginMeters;
                Shared->Snapshot->Elapsed=CaptureElapsed;Shared->Snapshot->Center=CaptureCenter;
                Shared->Snapshot->Downstream=CaptureDownstream;Shared->Snapshot->Left=CaptureLeft;
            }
        }
        const bool bCapture=Shared->Snapshot && Shared->Snapshot->Prefix==CapturePrefix;
        FString Error;
        if (Shared->bFailed.Load())return;
        if(bFrameContact && !Shared->TotalSource.Upload(Cmd,TotalSource,Error))
        {Shared->bFailed.Store(true);UE_LOG(LogTemp,Error,TEXT("Live total-depth source upload rejected: %s"),*Error);return;}
        if(bFrameContact)
        {
            static FString NonlinearAuditPath;
            static const bool Requested=FParse::Value(FCommandLine::Get(),TEXT("RaftSimNonlinearEvolutionAudit="),NonlinearAuditPath);
            if(Requested && !Shared->NonlinearAudit)Shared->NonlinearAudit=MakeUnique<FRaftSimNonlinearEvolutionAudit>(NonlinearAuditPath);
            if(Shared->NonlinearAudit)Shared->NonlinearAudit->Tick(Cmd,TotalSource);
        }
        if(!TemporalAuditPath.IsEmpty() && !Shared->bTemporalAuditRequested && Shared->TotalSource.HasTemporalBracket())
        {
            Shared->bTemporalAuditRequested=true;Shared->TemporalAudit=MakeUnique<FRaftSimTemporalBoundaryAudit>();
            if(!Shared->TemporalAudit->Start(Cmd,Shared->TotalSource,TemporalAuditPath,Error))
            {UE_LOG(LogTemp,Error,TEXT("Live temporal audit could not start: %s"),*Error);Shared->TemporalAudit.Reset();}
        }
        if (Shared->bHasWindow && Shared->OriginMeters!=Grid.OriginMeters)
        {
            const FVector2f Shift=(Grid.OriginMeters-Shared->OriginMeters)/Grid.CellMeters;
            if (FMath::Abs(Shift.X)>=Grid.Size.X || FMath::Abs(Shift.Y)>=Grid.Size.Y)
            {
                // An explicit teleport has no overlap. Never pretend to have
                // retained state from a different reach or wrap old foam in.
                Shared->Simulation.Reset();Shared->FrothFlowHistory.Reset();++Shared->Teleports;
            }
            else if (!Shared->Simulation.RemapWindow(Cmd,Grid,Flow,Error))
            { Shared->bFailed.Store(true);UE_LOG(LogTemp,Error,TEXT("Stateful detail remap rejected: %s"),*Error);return; }
            else ++Shared->Remaps;
        }
        const double IntervalStart=Shared->Simulation.GetSimulationSeconds();
        if (!Shared->Simulation.Advance(Cmd,Grid,Flow,Steps,nullptr,bCapture ? &Shared->Snapshot->StateReadback : nullptr,Error) ||
            !Shared->Simulation.Resolve(Cmd,Target->GetRenderTargetTexture(),Error))
        { Shared->bFailed.Store(true);UE_LOG(LogTemp,Error,TEXT("Stateful detail dispatch rejected: %s"),*Error);return; }
        if(bCaptureFrothHistory)
        {
            const bool Appended=Shared->FrothFlowHistory.Append(IntervalStart,Shared->Simulation.GetSimulationSeconds(),
                CaptureMeanElapsed,Grid.Size,Grid.OriginMeters,Grid.CellMeters,Flow);
            if(!Appended || (bCapture && !Shared->FrothFlowHistory.Save(CapturePrefix)))
                UE_LOG(LogTemp,Error,TEXT("Froth flow history capture failed: %s"),*CapturePrefix);
        }
        Shared->OriginMeters=Grid.OriginMeters;Shared->bHasWindow=true;
        if (bFrameContact)
        {
            ++Shared->FrameSequence;bool bCopied=false;
            for (auto& Slot:Shared->FrameReadbacks) if (!Slot->Sequence)
            {
                static const bool CaptureFoamFlow=[]{FString P;return FParse::Value(FCommandLine::Get(),TEXT("RaftSimFoamFlowPairAudit="),P);}();
                Slot->Enqueue(Cmd,Target->GetRenderTargetTexture(),Grid.Size,Shared->FrameSequence,
                    CaptureElapsed,Shared->Simulation.GetSimulationSeconds(),false,(CaptureFoamFlow || bPairedFoamFlow)?&Flow:nullptr);bCopied=true;break;
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
    if(bMovingWindow)
        UE_LOG(LogTemp,Display,TEXT("Detail committed-water clock: origin=%.9f water=%.9f target=%.9f backlog=%.9f wall=%.9f; no wall-time extrapolation"),
            WaterClock.Origin,WaterClock.Last,WaterClock.TargetSeconds(),Accumulator,Elapsed);
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
            if(Shared->TotalSource.Source)
            {
                const auto& Source=*Shared->TotalSource.Source;int32 Thin=0;
                for(const auto& S:Source.State)Thin+=S.X>0 && S.X<=.01f;
                UE_LOG(LogTemp,Display,TEXT("Live total-depth source: uploads=%llu revision=%llu cells=%d positive_le1cm=%d sampled_seconds=%.6f; unmasked h/M and paired bed/surface on GPU, evolving solver unchanged"),
                    Shared->TotalSource.Uploads,Source.Revision,Source.State.Num(),Thin,Source.SampleSeconds);
                int32 GhostWet=0,GhostThin=0;
                for(const auto& S:Source.ExteriorState){GhostWet+=S.X>0;GhostThin+=S.X>0 && S.X<=.01f;}
                UE_LOG(LogTemp,Display,TEXT("Live exterior source: cells=%d positive=%d positive_le1cm=%d sampled_seconds=%.6f; six paired GPU buffers,512 actual ghost centres and independent face velocities, no interior reset"),
                    Source.ExteriorState.Num(),GhostWet,GhostThin,Source.SampleSeconds);
                UE_LOG(LogTemp,Display,TEXT("Live boundary observations: faces=%d bracket=%d first_native_seconds=%.9f second_native_seconds=%.9f; source interpolation available, legacy evolution unchanged"),
                    Source.FaceNormalVelocity.Num(),Shared->TotalSource.HasTemporalBracket(),
                    Shared->TotalSource.PreviousSource?Shared->TotalSource.PreviousSource->SampleSeconds:Source.SampleSeconds,Source.SampleSeconds);
            }
            Shared->History.Stop();Shared->Simulation.Reset();
            if(Shared->TemporalAudit)
            {
                if(!Shared->TemporalAudit->Poll())UE_LOG(LogTemp,Error,TEXT("Live temporal boundary audit incomplete at teardown"));
                Shared->TemporalAudit.Reset();
            }
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
    FoamFlowTexture.Reset();
    Super::EndPlay(EndPlayReason);
}
