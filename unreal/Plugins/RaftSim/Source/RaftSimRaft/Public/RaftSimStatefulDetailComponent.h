#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "RaftSimStatefulDetailComponent.generated.h"
class URaftSimWaterRuntimeAdapter;
class UMaterialInstanceDynamic;
class UTextureRenderTarget2D;
struct FRaftSimDetailRenderState;

// Optional, fixed world-space crux window. Camera/raft motion never changes
// its origin or reseeds state. A future moving window needs explicit remapping.
UCLASS()
class RAFTSIMRAFT_API URaftSimStatefulDetailComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    URaftSimStatefulDetailComponent();
    bool Initialize(URaftSimWaterRuntimeAdapter* Adapter,UMaterialInstanceDynamic* Material,
        FVector CenterWorldCm,FVector DownstreamWorld,bool bMotionHistory=false);
    virtual void TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* ThisTickFunction) override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
private:
    bool UpdateMeanFlow();
    UPROPERTY(Transient) TObjectPtr<URaftSimWaterRuntimeAdapter> Water;
    UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> SurfaceMaterial;
    UPROPERTY(Transient) TObjectPtr<UTextureRenderTarget2D> SurfaceTexture;
    UPROPERTY(Transient) TObjectPtr<UTextureRenderTarget2D> PreviousSurfaceTexture;
    TSharedPtr<FRaftSimDetailRenderState,ESPMode::ThreadSafe> RenderState;
    TArray<FVector4f> CachedFlow;
    // Fixed window: invert world coordinates only at initialization. The live
    // field still updates at 8 Hz; cached geometry never freezes hydraulics.
    TArray<FVector2D> SampleCoordinates;
    TArray<FVector4f> SampleBasisToDetail;
    FVector Center=FVector::ZeroVector,Downstream=FVector::ForwardVector,Left=FVector::RightVector;
    double Accumulator=0,FlowAge=1,Elapsed=0;
    float StepSeconds=1.0f/120.0f;
    double FlowPreparationTotalMs=0,FlowPreparationMaxMs=0;
    int32 FlowPreparationCount=0;
    bool bReady=false,bReported=false;
    bool bSecondOrder=false;
    bool bActivityMemory=false;
    int32 DetailSize=128;
    float DetailCellMeters=0.5f;
    float DetailOriginMeters=-32.0f;
    FString SnapshotPrefix;
    int32 SnapshotRequests=0;
};
