#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Engine/TextureRenderTarget2D.h"
#include "RaftSimDetailPresentationFrame.h"
#include "RaftSimDetailSampleGrid.h"
#include "RaftSimCommittedWaterClock.h"
#include "UObject/StrongObjectPtr.h"
#include "RaftSimStatefulDetailComponent.generated.h"
class URaftSimWaterRuntimeAdapter;
class UMaterialInstanceDynamic;
struct FRaftSimDetailRenderState;
struct FRaftSimTotalDepthSource;

// Existing carrier: Cartesian windows remap exact state; legacy reviews may use a fixed basis.
UCLASS()
class RAFTSIMRAFT_API URaftSimStatefulDetailComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    URaftSimStatefulDetailComponent();
    bool Initialize(URaftSimWaterRuntimeAdapter* Adapter,UMaterialInstanceDynamic* Material,
        FVector CenterWorldCm,FVector DownstreamWorld,bool bMotionHistory=false,bool bMovingCartesian=false);
    void SetFocusActor(AActor* Actor);
    bool IsReady() const { return bReady; }
    void CommitCompletedFrame();
    bool AuditPresentedFrame();
    TSharedPtr<const FRaftSimDetailPresentationFrame,ESPMode::ThreadSafe> GetPresentedFrame() const { return bReady ? PresentedFrame : nullptr; }
    virtual void TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* ThisTickFunction) override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
private:
    friend class FRaftSimDetailNativeHandoffTest;
    bool EnsureSourceCoverage(FVector2f NextOrigin);
    bool CacheSampleCoordinates();
    bool UpdateMeanFlow();
    TSharedPtr<const FRaftSimTotalDepthSource,ESPMode::ThreadSafe> SampleClosingWindow(FString& Error);
    UPROPERTY(Transient) TObjectPtr<URaftSimWaterRuntimeAdapter> Water;
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> SurfaceMaterial;
    UPROPERTY(Transient) TObjectPtr<UTextureRenderTarget2D> SurfaceTexture;
    UPROPERTY(Transient) TObjectPtr<UTextureRenderTarget2D> PreviousSurfaceTexture;
    UPROPERTY(Transient) TObjectPtr<UTextureRenderTarget2D> ComputeTexture;
    TSharedPtr<const FRaftSimDetailPresentationFrame,ESPMode::ThreadSafe> PresentedFrame;
    uint64 LastCommitGameFrame=MAX_uint64,PresentationCommits=0,PresentationHolds=0;
    double MaximumPresentationAge=0;
    FString ContactAuditPath;
    FString TemporalBoundaryAuditPath;
    bool bContactAuditRequested=false;
    TSharedPtr<FRaftSimDetailRenderState,ESPMode::ThreadSafe> RenderState;
    TArray<FVector4f> CachedFlow;
    // Paired source geometry: live Cartesian total-state inputs and captures.
    // Bed, sampled mean surface, unmasked depth, interpolated wet indicator.
    TArray<FVector4f> CachedMeanGeometry;
    TSharedPtr<const FRaftSimTotalDepthSource,ESPMode::ThreadSafe> CachedTotalDepthSource;
    TSharedPtr<const FRaftSimTotalDepthSource,ESPMode::ThreadSafe> PendingClosingWindowSource;
    uint64 TotalDepthSourceRevision=0;
    double MeanSampleElapsed=0;
    // Recompute coordinates only on initialization/remap. Live fields update
    // at 8 Hz; cached geometry never freezes hydraulics. Moving windows sample
    // 67x67 fixed-world nodes (65x65 interior plus one coarse exterior ring).
    TArray<FVector2D> SampleCoordinates;
    TArray<FVector4f> SampleBasisToDetail;
    TArray<FVector2D> FaceSampleCoordinates;
    TArray<FVector4f> FaceSampleBasisToDetail;
    FRaftSimDetailSampleGrid SampleGrid; // Fixed world lattice for moving Cartesian windows.
    FVector Center=FVector::ZeroVector,Downstream=FVector::ForwardVector,Left=FVector::RightVector;
    double Accumulator=0,FlowAge=1,Elapsed=0;
    FRaftSimCommittedWaterClock WaterClock;
    float StepSeconds=1.0f/120.0f;
    double FlowPreparationTotalMs=0,FlowPreparationMaxMs=0;
    int32 FlowPreparationCount=0;
    bool bReady=false,bReported=false;
    bool bReportedBreakingSource=false;
    bool bSecondOrder=false;
    bool bActivityMemory=false;
    bool bFiniteDepthDispersion=false;
    bool bMovingWindow=false;
    FVector FocusWorldCm=FVector::ZeroVector;
    TWeakObjectPtr<AActor> FocusActor;
    FVector2f WindowOriginMeters=FVector2f::ZeroVector;
    int32 DetailSize=128;
    float DetailCellMeters=0.5f;
    float DetailOriginMeters=-32.0f;
    FString SnapshotPrefix;
    int32 SnapshotRequests=0;
    // Native GC ownership for the paired optical texture, released at EndPlay.
    TStrongObjectPtr<UTextureRenderTarget2D> FoamFlowTexture;
};
