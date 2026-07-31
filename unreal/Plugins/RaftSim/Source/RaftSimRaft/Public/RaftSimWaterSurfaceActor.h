#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ProceduralMeshComponent.h"

#include "RaftSimWaterSurfaceActor.generated.h"

class UProceduralMeshComponent;
class UMaterialInterface;
class URaftSimWaterRuntimeAdapter;

/**
 * Renders the live solver's free surface (water-rendering v1, P2): a procedural
 * grid mesh whose vertices track the water-runtime adapter's surface height and
 * normal each tick, with vertex-colour foam driven by the local Froude number.
 * Resolves the bridge subsystem's adapter at BeginPlay; falls back to a flat
 * plane when no live window is configured.
 */
UCLASS()
class RAFTSIMRAFT_API ARaftSimWaterSurfaceActor : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimWaterSurfaceActor();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    /** Reproduces the deterministic presentation-only displacement authored
     * into the full-reach seasonal water. It never changes a water sample,
     * collision, buoyancy, or any other solver authority. */
    static float ComputePresentationStandingWaveDisplacementMeters(
        const FVector2D& RiverCoordinatesMeters,
        float SpeedMetersPerSecond,
        float DepthMeters);

    /** Sharpens only relief already present in the sampled solver surface.
     * Symmetric station neighbours remove the local linear grade, so planar
     * or calm water receives no displacement. The bounded result is visual
     * only and never feeds collision, buoyancy, D3, or D4. */
    static float ComputePresentationHydraulicReliefDisplacementMeters(
        float CenterSurfaceHeightMeters,
        float UpstreamFarSurfaceHeightMeters,
        float UpstreamNearSurfaceHeightMeters,
        float DownstreamNearSurfaceHeightMeters,
        float DownstreamFarSurfaceHeightMeters,
        float SpeedMetersPerSecond,
        float DepthMeters);

    /** Deterministic cross-section for the presentation-only breaking-water
     * lip. X is downstream travel and Y is vertical lift in centimetres. The
     * final quarter curls back upstream and below the sampled free surface,
     * giving hydraulic jumps a genuine overhanging sheet without changing the
     * single-valued solver surface or any gameplay authority. */
    static FVector2D ComputeBreakingLipProfileCentimeters(
        float NormalizedCurl,
        float Intensity);

    /** Cross-section for the presentation-only entrained-air roller. The open
     * loop wraps from the downstream pile, over the aerated crown, and back
     * toward the plunge face. LayerNormalized distributes nested fallback
     * shells through that circulation without creating gameplay authority or
     * modifying the single-valued solver surface. */
    static FVector2D ComputeBreakingRollerVolumeProfileCentimeters(
        float NormalizedLoop,
        float Intensity,
        float LayerNormalized);

    /** Distance from one sampled live-water vertex to the nearest moving-grid
     * station edge or sampled wet/dry bank, in metres. Breaking-water sheets
     * use this to remain wholly inside the owned live-water presentation
     * surface instead of revealing a terrain/water seam at a fading edge. */
    static float ComputePresentationSurfaceEdgeClearanceMeters(
        int32 StationIndex,
        int32 StationCount,
        int32 LateralIndex,
        int32 MinimumWetLateralIndex,
        int32 MaximumWetLateralIndex,
        float VertexSpacingMeters);

    /** One detected breaking-water site (a supercritical-to-subcritical
     * hydraulic jump resolved by the live solver field), exposed so bounded
     * aerosol/mist presentation can anchor to genuine whitewater. Positions
     * are world centimetres on the displaced presentation surface. */
    struct FBreakingSite
    {
        FVector WorldPositionCm = FVector::ZeroVector;
        FVector WorldVelocityMps = FVector::ZeroVector;
        FVector2D RiverCoordinatesMeters = FVector2D::ZeroVector;
        float Intensity = 0.0f;
        float PresentationCoverage = 0.0f;
        float PresentationEdgeClearanceMeters = 0.0f;
    };

    /** Copies the breaking sites found during the most recent surface refresh,
     * strongest first, deduplicated to a minimum world spacing. */
    void GetBreakingSites(TArray<FBreakingSite>& OutSites) const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    int32 GetBreakingLipTriangleCount() const
    {
        return BreakingLipTriangleCount;
    }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    bool IsBreakingLipVisible() const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    int32 GetBreakingRollerVolumeTriangleCount() const
    {
        return BreakingRollerVolumeTriangleCount;
    }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    bool IsBreakingRollerVolumeVisible() const;

    /** Selects the non-colliding roller-mesh fallback. Production Niagara
     * disables it only after all required particle assets are bound. */
    void SetBreakingRollerVolumeRenderingEnabled(bool bEnabled);

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water")
    TObjectPtr<UProceduralMeshComponent> SurfaceMesh;

    /** Non-colliding curled sheets generated only at solver-detected hydraulic
     * jumps. Kept separate from SurfaceMesh so they can overhang without ever
     * feeding their multi-valued geometry back into D3, D4 or buoyancy. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    TObjectPtr<UProceduralMeshComponent> BreakingLipMesh;

    /** Nested shell fallback generated only at accepted live hydraulic jumps.
     * This is an explicitly visual entrained-air body: no collision,
     * navigation, water sampling, buoyancy, D3, or D4 authority. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    TObjectPtr<UProceduralMeshComponent> BreakingRollerVolumeMesh;

    /** Water material applied to the surface (single-layer water). */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water")
    TObjectPtr<UMaterialInterface> WaterMaterial;

    UPROPERTY(EditAnywhere, Category = "RaftSim|Water|Presentation")
    TObjectPtr<UMaterialInterface> BreakingWaterMaterial;

    /** Grid origin (world cm, lower corner). Centred on world origin, where the
     * loader re-centres the reach's hydraulic crux. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water")
    FVector2D GridOriginCm = FVector2D(-10000.0, -10000.0);

    /** Legacy straight-window grid extent in meters. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water")
    float GridSizeMeters = 200.0f;

    /** Curved full-reach surface length centred on the raft. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water|Full Reach")
    float CurvedGridLengthMeters = 240.0f;

    /** Curved full-reach surface width across the channel. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water|Full Reach")
    float CurvedGridWidthMeters = 96.0f;

    UPROPERTY(EditAnywhere, Category = "RaftSim|Water|Full Reach")
    float CurvedGridRecenterDistanceMeters = 32.0f;

    /** Presentation-only station-edge blend into the authored seasonal water.
     * Stored in vertex alpha; it never changes solver sampling or geometry. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water|Full Reach", meta = (ClampMin = "3.0"))
    float CurvedGridEdgeBlendMeters = 36.0f;

    /** Presentation-only feather across live wet/dry banks and the lateral
     * moving-window boundary. This prevents a one-cell translucent sheet edge
     * from reading as a second river surface. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water|Full Reach", meta = (ClampMin = "3.0"))
    float CurvedGridLateralEdgeBlendMeters = 9.0f;

    /** Minimum distance from a hydraulic jump to either a sampled riverbank
     * or moving-grid station edge before multi-valued breaking-water geometry
     * may be presented. The sheet width is fitted to this measured clearance,
     * retaining at least eleven metres of bank/background margin at its maximum
     * span. It does not change solver wet/dry authority. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water|Presentation", meta = (ClampMin = "9.0"))
    float BreakingSiteInteriorClearanceMeters = 15.0f;

    /** World-space spacing between surface vertices in meters. The production
     * hydraulic grid is four metres, so three-metre interpolation preserves
     * every resolved feature without wastefully oversampling the solver. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water")
    float VertexSpacingMeters = 3.0f;

    /** Surface refresh interval (s); physics remains fixed-step while this
     * presentation mesh interpolates the much more slowly changing FV field. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water")
    float RefreshIntervalSeconds = 1.0f / 15.0f;

    /** Half-life of persistent surface foam. Generated foam decays through this
     * while being advected downstream with the sampled flow, so whitewater
     * streaks and tails follow the current instead of sitting statically on the
     * generation cell. Presentation only. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water", meta = (ClampMin = "0.5"))
    float FoamHalfLifeSeconds = 4.0f;

    /** Presentation-only crest lift applied at a detected hydraulic jump so the
     * breaking face leans over its downstream pile. Bounded and visual only —
     * never fed back into sampling, collision, buoyancy, D3, or D4. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water", meta = (ClampMin = "0.0", ClampMax = "0.25"))
    float BreakingCrestLiftMeters = 0.10f;

private:
    void BuildGrid();
    void RefreshSurface();
    void RecenterCurvedGrid();
    void ClampCurvedGridCenter();
    void UpdateCurvedGridPlanarGeometry();
    void RebuildBreakingLipMesh();
    void HideBreakingLipMesh();
    void RebuildBreakingRollerVolumeMesh();
    void HideBreakingRollerVolumeMesh();

    UPROPERTY()
    TObjectPtr<URaftSimWaterRuntimeAdapter> WaterAdapter;

    int32 GridStationN = 0;
    int32 GridLateralN = 0;
    bool bUsesCurvedRiverCoordinates = false;
    float CurvedGridCenterStationM = 0.0f;
    TArray<FVector> Vertices;
    TArray<FVector2D> RiverCoordinatesM;
    TArray<int32> Triangles;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<FProcMeshTangent> Tangents;
    float TimeSinceRefresh = 0.0f;
    bool bLoggedPresentationDiagnostics = false;
    bool bLoggedHydraulicReliefDiagnostics = false;
    bool bLoggedBreakingSiteDiagnostics = false;

    // Persistent foam state advected between refreshes. The field lives on the
    // presentation grid in its 2D working coordinates (river station/lateral in
    // curved mode, world metres on the legacy rectangular grid); the recorded
    // origin lets a back-trace land in the previous field even across a grid
    // recenter.
    TArray<float> FoamField;
    FVector2D FoamFieldOriginM = FVector2D::ZeroVector;
    bool bFoamFieldValid = false;
    double LastRefreshRealSeconds = 0.0;
    TArray<FBreakingSite> BreakingSites;
    int32 BreakingLipTriangleCount = 0;
    int32 BreakingRollerVolumeTriangleCount = 0;
    bool bBreakingRollerVolumeRenderingEnabled = true;
};
