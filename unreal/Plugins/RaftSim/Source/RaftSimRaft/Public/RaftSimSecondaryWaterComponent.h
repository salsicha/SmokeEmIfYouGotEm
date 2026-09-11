#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "RaftSimSecondaryWater.h"
#include "RaftSimSecondaryWaterComponent.generated.h"

class UInstancedStaticMeshComponent;
class ARaftSimWaterSurfaceActor;
class URaftSimWaterRuntimeAdapter;

/** Explicit registered-scene experiment; absent from the production VFX path. */
UCLASS()
class RAFTSIMRAFT_API URaftSimSecondaryWaterComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    URaftSimSecondaryWaterComponent();
    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaSeconds, ELevelTick TickType,
        FActorComponentTickFunction* ThisTickFunction) override;
    bool IsReviewReady() const { return bReady; }
    static void InitializeInstanceHistory(UInstancedStaticMeshComponent* Component,
        TArray<FTransform>& History);
private:
    bool Sample(const FVector& PositionM, FRaftSimSecondaryWater::FCarrier& Out) const;
    UPROPERTY(Transient) TObjectPtr<UInstancedStaticMeshComponent> Instances;
    UPROPERTY(Transient) TObjectPtr<URaftSimWaterRuntimeAdapter> Adapter;
    TWeakObjectPtr<ARaftSimWaterSurfaceActor> Surface;
    FRaftSimSecondaryWater Simulation;
    FRandomStream Random{731901};
    TArray<FTransform> PreviousTransforms;
    uint64 PreviousBirthIds[FRaftSimSecondaryWater::Capacity] = {};
    double PendingSeconds = 0, EmissionCredit = 0, Elapsed = 0, CpuSeconds = 0;
    int32 FrameCount = 0, NextReportSeconds = 10;
    bool bReady = false;
};
