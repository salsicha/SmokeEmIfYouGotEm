#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RaftSimWaterRuntimeAdapter.h"

#include "RaftSimWaterVfxActor.generated.h"

class APostProcessVolume;
class ARaftSimRaftActor;
class UHierarchicalInstancedStaticMeshComponent;
class UPostProcessComponent;
class URaftSimWaterRuntimeAdapter;

/** Solver/contact-derived presentation channels used by the runtime VFX pool. */
USTRUCT(BlueprintType)
struct RAFTSIMRAFT_API FRaftSimWaterVfxState
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    float Spray = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    float Mist = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    float ImpactSheet = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    float Droplets = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    float Underwater = 0.0f;
};

/**
 * Niagara-free live-water VFX pool. It converts genuine solver samples and
 * flexible raft/rock contacts into moving spray, mist, water sheets, and
 * droplets, and blends an underwater camera grade when the player camera
 * crosses the sampled free surface. The fixed instance pools avoid spawning
 * transient actors while preserving a deterministic automation path.
 */
UCLASS()
class RAFTSIMRAFT_API ARaftSimWaterVfxActor : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimWaterVfxActor();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    /** Pure presentation classifier shared with automation. */
    static FRaftSimWaterVfxState EvaluatePresentation(
        const FRaftSimWaterSample& Sample,
        const FVector& RaftVelocityMps,
        int32 ContactCount,
        float MaximumIndentationM,
        bool bCameraUnderwater);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    const FRaftSimWaterVfxState& GetLastPresentationState() const
    {
        return LastPresentationState;
    }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    bool IsLiveWaterBound() const { return WaterAdapter != nullptr; }

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TObjectPtr<USceneComponent> Root;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> SprayInstances;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> MistInstances;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> SheetInstances;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> DropletInstances;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TObjectPtr<UPostProcessComponent> UnderwaterPostProcess;

    UPROPERTY(EditAnywhere, Category = "RaftSim|Water|VFX")
    float RefreshIntervalSeconds = 1.0f / 20.0f;

private:
    void RefreshVfx(float DeltaSeconds);
    void ClearInstances();
    bool SampleCameraUnderwater() const;

    UPROPERTY()
    TObjectPtr<URaftSimWaterRuntimeAdapter> WaterAdapter;

    UPROPERTY()
    TObjectPtr<ARaftSimRaftActor> TrackedRaft;

    UPROPERTY()
    FRaftSimWaterVfxState LastPresentationState;

    float TimeSinceRefresh = 0.0f;
    float SimulationPhase = 0.0f;
};
