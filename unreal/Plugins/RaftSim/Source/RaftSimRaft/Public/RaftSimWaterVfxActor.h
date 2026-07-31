#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "RaftSimWaterRuntimeAdapter.h"

#include "RaftSimWaterVfxActor.generated.h"

class APostProcessVolume;
class ARaftSimRaftActor;
class UInstancedStaticMeshComponent;
class UNiagaraComponent;
class UPostProcessComponent;
class UProceduralMeshComponent;
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
 * Solver-driven live-water VFX bridge. Production rendering uses bounded,
 * project-owned Niagara systems for volumetric spray, mist and droplets;
 * deterministic fixed card pools remain as a fail-closed automation and
 * unsupported-platform fallback. The same classifier also blends an
 * underwater camera grade when the player camera crosses the sampled surface.
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

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    float GetUnderwaterBlendWeight() const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    int32 GetSprayInstanceCount() const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    int32 GetMistInstanceCount() const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    int32 GetImpactFoamInstanceCount() const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    int32 GetDropletInstanceCount() const;

    /** River-aerosol population count for the current refresh: mist suspended
     * above solver-detected breaking water, independent of raft contact. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    int32 GetRapidAerosolInstanceCount() const;

    /** True only when every project-owned Niagara water system loaded and the
     * legacy card renderer has been hidden in favor of particle volumes. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    bool IsProductionNiagaraReady() const { return bProductionNiagaraReady; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    int32 GetProductionNiagaraComponentCount() const;

    /** Number of camera-local solver-jump aerosol volumes currently emitting. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    int32 GetActiveRapidAerosolNiagaraCount() const
    {
        return ActiveRapidNiagaraCount;
    }

    /** Number of solver-jump roller particle volumes currently emitting. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    int32 GetActiveRapidRollerNiagaraCount() const
    {
        return ActiveRapidRollerNiagaraCount;
    }

    /** Presentation-only high-resolution water shoulder at the authoritative
     * D4 contact. Zero means the patch is fail-closed and not being rendered. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    int32 GetContactWaterPatchTriangleCount() const
    {
        return ContactWaterPatchTriangleCount;
    }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    bool IsContactWaterPatchVisible() const;

    /** Triangle count for the opt-in connected contact-water V6 review. The
     * review mesh is presentation-only and remains zero in production. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    int32 GetConnectedContactWaterV6TriangleCount() const
    {
        return ConnectedContactWaterV6TriangleCount;
    }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    bool IsConnectedContactWaterV6Visible() const;

    /** Combined triangle count for the opt-in, three-layer connected contact
     * water V7 review. It remains zero in production. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    int32 GetConnectedContactWaterV7TriangleCount() const
    {
        return ConnectedContactWaterV7TriangleCount;
    }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    bool IsConnectedContactWaterV7Visible() const;

    /** Combined triangle count for the opt-in V8 closed-lobe contact-water
     * review. It remains zero in production. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    int32 GetConnectedContactWaterV8TriangleCount() const
    {
        return ConnectedContactWaterV8TriangleCount;
    }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    bool IsConnectedContactWaterV8Visible() const;

    /** Triangle count for the currently displayed frame of the opt-in V10
     * closed implicit-volume cache. It remains zero in production. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    int32 GetDepthBearingContactWaterV10TriangleCount() const
    {
        return DepthBearingContactWaterV10TriangleCount;
    }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    bool IsDepthBearingContactWaterV10Visible() const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    int32 GetDepthBearingContactWaterV10CachedFrameCount() const
    {
        return DepthBearingContactWaterV10FrameTriangleCounts.Num();
    }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    int32 GetDepthBearingContactWaterV10CurrentFrame() const
    {
        return DepthBearingContactWaterV10CurrentFrame;
    }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|VFX")
    float GetDepthBearingContactWaterV10DepthCm() const
    {
        return DepthBearingContactWaterV10DepthCm;
    }

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TObjectPtr<USceneComponent> Root;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TObjectPtr<UInstancedStaticMeshComponent> SprayInstances;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TObjectPtr<UInstancedStaticMeshComponent> MistInstances;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TObjectPtr<UInstancedStaticMeshComponent> SheetInstances;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TObjectPtr<UInstancedStaticMeshComponent> DropletInstances;

    /** Suspended aerosol above solver-detected breaking water (hydraulic
     * jumps), sourced from the live water surface's breaking sites rather than
     * raft contact, so rapids mist even before the raft arrives. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TObjectPtr<UInstancedStaticMeshComponent> RapidAerosolInstances;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TObjectPtr<UNiagaraComponent> SolverSprayNiagara;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TObjectPtr<UNiagaraComponent> ContactDropletNiagara;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TObjectPtr<UNiagaraComponent> AeratedMistNiagara;

    /** Bounded pool, one looping local-space mist volume per strongest live
     * breaking-water site. No transient Niagara actors are ever spawned. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TArray<TObjectPtr<UNiagaraComponent>> RapidAerosolNiagara;

    /** Bounded pool of short-lived, velocity-aligned whitewater fragments.
     * Each component is anchored to one live hydraulic jump and replaces the
     * procedural roller mesh only when every production Niagara asset loads. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TArray<TObjectPtr<UNiagaraComponent>> RapidRollerNiagara;

    /** Non-colliding, solver-sampled contact-water shoulder. This mesh is
     * deliberately separate from the 3 m live-river mesh so a local contact
     * cannot invent a coarse hydraulic spike or influence physics. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TObjectPtr<UProceduralMeshComponent> ContactWaterPatch;

    /** Opt-in, non-colliding solver-contact sheet used to test connected
     * gameplay-scale water volume before any production-art promotion. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TObjectPtr<UProceduralMeshComponent> ConnectedContactWaterV6Review;

    /** Opt-in V7 surface attachment, aerated crest, and breakup layers. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TObjectPtr<UProceduralMeshComponent> ConnectedContactWaterV7Review;

    /** Opt-in V8 sampled attachment plus short closed entrained-air lobes. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TObjectPtr<UProceduralMeshComponent> ConnectedContactWaterV8Review;

    /** Opt-in V10 six-frame, closed implicit-volume cache. Geometry is built
     * once, has no collision or navigation, and is transformed only by the
     * existing D4 contact presentation frame. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TObjectPtr<UProceduralMeshComponent> DepthBearingContactWaterV10Review;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|VFX")
    TObjectPtr<UPostProcessComponent> UnderwaterPostProcess;

    UPROPERTY(EditAnywhere, Category = "RaftSim|Water|VFX")
    float RefreshIntervalSeconds = 1.0f / 20.0f;

private:
    void RefreshVfx(float DeltaSeconds);
    void RefreshRapidAerosol();
    void ClearInstances();
    void HideContactWaterPatch();
    void HideConnectedContactWaterV6Review();
    void HideConnectedContactWaterV7Review();
    void HideConnectedContactWaterV8Review();
    void HideDepthBearingContactWaterV10Review();
    bool BuildDepthBearingContactWaterV10Cache();
    void UpdateContactWaterPatch(
        const FVector& SurfaceCenterCm,
        const FVector& FlowDirection,
        const FVector& AcrossDirection,
        float ImpactEnergy,
        float ContactScale);
    void UpdateConnectedContactWaterV6Review(
        const FVector& SurfaceCenterCm,
        const FVector& FlowDirection,
        const FVector& AcrossDirection,
        const FVector& ContactOutward,
        const FVector& ImpactDirection,
        float ImpactEnergy,
        float ContactScale);
    void UpdateConnectedContactWaterV7Review(
        const FVector& SurfaceCenterCm,
        const FVector& FlowDirection,
        const FVector& AcrossDirection,
        const FVector& ContactOutward,
        const FVector& ImpactDirection,
        float ImpactEnergy,
        float ContactScale);
    void UpdateConnectedContactWaterV8Review(
        const FVector& SurfaceCenterCm,
        const FVector& FlowDirection,
        const FVector& AcrossDirection,
        const FVector& ContactOutward,
        const FVector& ImpactDirection,
        float ImpactEnergy,
        float ContactScale);
    void UpdateDepthBearingContactWaterV10Review(
        const FVector& SurfaceCenterCm,
        const FVector& FlowDirection,
        const FVector& AcrossDirection,
        const FVector& ContactOutward,
        const FVector& ImpactDirection,
        float ImpactEnergy,
        float ContactScale);
    bool SampleCameraUnderwater() const;

    UPROPERTY()
    TObjectPtr<URaftSimWaterRuntimeAdapter> WaterAdapter;

    UPROPERTY()
    TObjectPtr<ARaftSimRaftActor> TrackedRaft;

    TWeakObjectPtr<class ARaftSimWaterSurfaceActor> BreakingSurface;

    UPROPERTY()
    FRaftSimWaterVfxState LastPresentationState;

    float TimeSinceRefresh = 0.0f;
    float SimulationPhase = 0.0f;
    int32 ContactWaterPatchTriangleCount = 0;
    int32 ConnectedContactWaterV6TriangleCount = 0;
    int32 ConnectedContactWaterV7TriangleCount = 0;
    int32 ConnectedContactWaterV8TriangleCount = 0;
    TArray<int32> DepthBearingContactWaterV10FrameTriangleCounts;
    int32 DepthBearingContactWaterV10TriangleCount = 0;
    int32 DepthBearingContactWaterV10CurrentFrame = -1;
    float DepthBearingContactWaterV10DepthCm = 0.0f;
    int32 ActiveRapidNiagaraCount = 0;
    int32 ActiveRapidRollerNiagaraCount = 0;
    bool bConnectedContactWaterV6Review = false;
    bool bConnectedContactWaterV7Review = false;
    bool bConnectedContactWaterV8Review = false;
    bool bDepthBearingContactWaterV10Review = false;
    bool bProductionNiagaraReady = false;
};
