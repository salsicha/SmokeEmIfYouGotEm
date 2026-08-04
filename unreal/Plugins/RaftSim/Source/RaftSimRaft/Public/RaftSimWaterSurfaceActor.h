#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ProceduralMeshComponent.h"

#include "RaftSimWaterSurfaceActor.generated.h"

class UProceduralMeshComponent;
class UMaterialInterface;
class UMaterialParameterCollection;
class ARaftSimRaftActor;
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

    /** Reproduces deterministic presentation-only, phase-warped wave packets
     * over the full-reach seasonal water. It never changes a water sample,
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

    /** Plane-preserving cardinal filter used only by opted-in live rendering.
     * Symmetric neighbours preserve any linear grade exactly while reducing
     * one-cell cooked-field steps. */
    static float ComputePresentationSmoothedSurfaceHeightMeters(
        float CenterSurfaceHeightMeters,
        float UpstreamSurfaceHeightMeters,
        float DownstreamSurfaceHeightMeters,
        float RiverRightSurfaceHeightMeters,
        float RiverLeftSurfaceHeightMeters,
        float Strength);

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

    /** Render-only plan-view structure around an accepted hydraulic jump.
     * X is a bounded vertical displacement in metres and Y is local foam
     * generation. DownstreamMeters is positive with the river station and
     * AcrossMeters is signed river-left. The profile forms a dark plunge
     * pocket, broken side shoulders, and an aerated downstream return without
     * changing the sampled free surface or gameplay authority. */
    static FVector2D ComputeBreakingPlungePocketPresentation(
        float DownstreamMeters,
        float AcrossMeters,
        float Intensity);

    /** Animated render-only tailwater microrelief behind an accepted hydraulic
     * jump. Overlapping asymmetric cells create bounded upwellings and return
     * troughs without periodic rings. X is vertical displacement in metres;
     * Y is local foam generation. The phase and site offset affect only the
     * visible surface and never feed sampling, collision, buoyancy, D3, D4, or
     * raft forces. */
    static FVector2D ComputeBreakingDownstreamBoilPresentation(
        float DownstreamMeters,
        float AcrossMeters,
        float Intensity,
        float PhaseSeconds,
        float SitePhaseRadians);

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

    /** Presentation-only alpha coverage at a sampled wet bank. When enabled,
     * an incommensurate station-space profile shifts the interior feather but
     * never gives coverage to the outermost wet vertex or changes wet-cell
     * topology. */
    static float ComputePresentationBankCoverage(
        float StationMeters,
        int32 LateralIndex,
        int32 MinimumWetLateralIndex,
        int32 MaximumWetLateralIndex,
        float VertexSpacingMeters,
        float EdgeBlendMeters,
        bool bEnableNaturalism,
        float NaturalismAmplitudeMeters);

    /** Inward-only, sub-cell retreat for the optical core's outermost wet
     * vertex. This changes the visible volume silhouette without changing the
     * sampled surface or wet-cell topology. */
    static float ComputePresentationBankRetreatMeters(
        float StationMeters,
        bool bRiverLeft,
        float VertexSpacingMeters,
        bool bEnableNaturalism,
        float NaturalismAmplitudeMeters);

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
    int32 GetBreakingRollerVolumeVertexCount() const
    {
        return BreakingRollerVolumeVertexCount;
    }

    /** Maximum full front-to-back thickness of the connected aerated crest
     * envelope generated during the latest refresh. Presentation-only cm. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    float GetBreakingRollerVolumeMaximumThicknessCm() const
    {
        return BreakingRollerVolumeMaximumThicknessCm;
    }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    bool IsBreakingRollerVolumeVisible() const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    int32 GetActiveDownstreamBoilSiteCount() const
    {
        return ActiveDownstreamBoilSiteCount;
    }

    /** Largest absolute render-only boil displacement generated during the
     * latest refresh. This does not describe or modify the solver surface. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    float GetMaximumAbsoluteDownstreamBoilDisplacementMeters() const
    {
        return MaximumAbsoluteDownstreamBoilDisplacementMeters;
    }

    /** Number of live-water vertices currently contributing solver-owned,
     * advected rapid foam to the separate masked presentation sheet. The
     * sheet is visual-only and remains independent of sampling, collision,
     * buoyancy, D3, and D4. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    int32 GetVisibleRapidFoamVertexCount() const
    {
        return VisibleRapidFoamVertexCount;
    }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    bool IsRapidFoamMeshVisible() const;

    /** True when this mesh is the river-wide visible carrier instead of a
     * transparent detail overlay above an authored water surface. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    bool IsLiveSurfaceCarrierEnabled() const
    {
        return bLiveSurfaceCarrierEnabled;
    }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    float GetCalmLiveSurfaceCoverage() const
    {
        return ResolvedCalmLiveSurfaceCoverage;
    }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    float GetActiveLiveSurfaceCoverage() const
    {
        return ResolvedActiveLiveSurfaceCoverage;
    }

    /** True when a bank-clipped Single Layer Water mesh supplies optical
     * depth beneath the non-transmitting live detail surface. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    bool IsLiveVolumeCoreEnabled() const
    {
        return bLiveVolumeCoreEnabled;
    }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    bool IsLiveVolumeCoreVisible() const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    int32 GetLiveVolumeCoreTriangleCount() const
    {
        return LiveVolumeCoreTriangleCount;
    }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    bool IsLivePresentationSurfaceSmoothingEnabled() const
    {
        return bLivePresentationSurfaceSmoothingEnabled;
    }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    float GetLivePresentationSurfaceSmoothingStrength() const
    {
        return ResolvedPresentationSurfaceSmoothingStrength;
    }

    /** True when an authored river uses the render-only subdivided surface.
     * This changes presentation sampling only; the adapter and all gameplay
     * water authority remain at their authored resolution. */
    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    bool IsRiverPresentationGridRefined() const
    {
        return PresentationAnalysisStride > 1;
    }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    float GetPresentationVertexSpacingMeters() const
    {
        return ResolvedVertexSpacingMeters;
    }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    int32 GetSurfaceVertexCount() const
    {
        return Vertices.Num();
    }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water|Presentation")
    int32 GetSurfaceTriangleCount() const
    {
        return Triangles.Num() / 3;
    }

    /** Selects the non-colliding connected roller body. Production Niagara
     * complements this geometry with detached spray; it does not replace the
     * multi-valued water sheet. */
    void SetBreakingRollerVolumeRenderingEnabled(bool bEnabled);

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water")
    TObjectPtr<UProceduralMeshComponent> SurfaceMesh;

    /** Solver-conforming optical body rendered only through fully wet cells.
     * It is offset one centimetre beneath SurfaceMesh and has no collision,
     * shadow, navigation, sampling, buoyancy, D3, or D4 authority. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    TObjectPtr<UProceduralMeshComponent> LiveVolumeCoreMesh;

    /** Non-colliding curled sheets generated only at solver-detected hydraulic
     * jumps. Kept separate from SurfaceMesh so they can overhang without ever
     * feeding their multi-valued geometry back into D3, D4 or buoyancy. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    TObjectPtr<UProceduralMeshComponent> BreakingLipMesh;

    /** Single connected, thin two-skin aerated crest envelope generated only
     * at accepted live hydraulic jumps. Its skins join at the fully masked
     * plunge boundary while the visible crown stays open, avoiding a planar
     * cap or the old nested-shell dome cue. This is explicitly visual: no
     * collision, navigation, water sampling, buoyancy, D3, or D4 authority. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    TObjectPtr<UProceduralMeshComponent> BreakingRollerVolumeMesh;

    /** Masked lace sheet driven by the live solver's advected foam field.
     * Keeping it separate from the intentionally transparent live-water
     * carrier exposes rapid structure without restoring a rectangular water
     * overlay. The bound material applies the raft/crew exclusion mask. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "RaftSim|Water|Presentation")
    TObjectPtr<UProceduralMeshComponent> RapidFoamMesh;

    /** Water material applied to the surface (single-layer water). */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water")
    TObjectPtr<UMaterialInterface> WaterMaterial;

    UPROPERTY(EditAnywhere, Category = "RaftSim|Water|Presentation")
    TObjectPtr<UMaterialInterface> LiveVolumeCoreMaterial;

    UPROPERTY(EditAnywhere, Category = "RaftSim|Water|Presentation")
    TObjectPtr<UMaterialInterface> BreakingWaterMaterial;

    UPROPERTY(EditAnywhere, Category = "RaftSim|Water|Presentation")
    TObjectPtr<UMaterialInterface> RapidFoamMaterial;

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

    /** Base world-space analysis spacing in metres. Authored runtime rivers
     * subdivide this render-only mesh while retaining three-metre
     * neighbourhoods for solver-feature analysis. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water")
    float VertexSpacingMeters = 3.0f;

    /** Render-only subdivision applied to authored production-river windows.
     * Two resolves the bounded short-wave bands that cannot be represented by
     * the three-metre analysis grid. The adapter remains authoritative. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water|Presentation",
        meta = (ClampMin = "1", ClampMax = "2"))
    int32 RiverPresentationSubdivision = 2;

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
     * breaking face leans over its downstream pile, followed by a decaying
     * tailwater wave train. Bounded (comparable to the authored 26.8 cm
     * standing-wave envelope) and visual only — never fed back into sampling,
     * collision, buoyancy, D3, or D4. */
    UPROPERTY(EditAnywhere, Category = "RaftSim|Water", meta = (ClampMin = "0.0", ClampMax = "0.25"))
    float BreakingCrestLiftMeters = 0.22f;

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
    void UpdateRaftFoamExclusionParameters();

    UPROPERTY()
    TObjectPtr<URaftSimWaterRuntimeAdapter> WaterAdapter;

    /** Global presentation-only mask used by the static solver-foam sheet.
     * Updated from the visible raft transform; it never changes water samples,
     * forces, collision, or the solver's foam field. */
    UPROPERTY()
    TObjectPtr<UMaterialParameterCollection> RaftFoamOcclusionCollection;

    UPROPERTY()
    TObjectPtr<ARaftSimRaftActor> FoamOcclusionRaft;

    int32 GridStationN = 0;
    int32 GridLateralN = 0;
    bool bUsesCurvedRiverCoordinates = false;
    float ResolvedVertexSpacingMeters = 3.0f;
    int32 PresentationAnalysisStride = 1;
    float CurvedGridCenterStationM = 0.0f;
    TArray<FVector> Vertices;
    TArray<FVector2D> RiverCoordinatesM;
    TArray<int32> Triangles;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<FVector> LiveVolumeCoreVertices;
    TArray<int32> LiveVolumeCoreTriangles;
    TArray<FVector> RapidFoamVertices;
    TArray<FLinearColor> RapidFoamVertexColors;
    TArray<FProcMeshTangent> Tangents;
    float TimeSinceRefresh = 0.0f;
    float PresentationPhaseSeconds = 0.0f;
    bool bLoggedPresentationDiagnostics = false;
    bool bLoggedHydraulicReliefDiagnostics = false;
    bool bLoggedRaftInteriorWaterTransmission = false;
    FVector LastLoggedRaftInteriorWaterCenter = FVector::ZeroVector;
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
    int32 BreakingRollerVolumeVertexCount = 0;
    float BreakingRollerVolumeMaximumThicknessCm = 0.0f;
    int32 ActiveDownstreamBoilSiteCount = 0;
    float MaximumAbsoluteDownstreamBoilDisplacementMeters = 0.0f;
    int32 VisibleRapidFoamVertexCount = 0;
    int32 LiveVolumeCoreTriangleCount = 0;
    bool bBreakingRollerVolumeRenderingEnabled = true;
    bool bLiveSurfaceCarrierEnabled = false;
    bool bLiveVolumeCoreEnabled = false;
    float ResolvedCalmLiveSurfaceCoverage = 0.0f;
    float ResolvedActiveLiveSurfaceCoverage = 0.0f;
    bool bLivePresentationSurfaceSmoothingEnabled = false;
    float ResolvedPresentationSurfaceSmoothingStrength = 0.0f;
    float ResolvedPresentationStandingWaveScale = 1.0f;
    float ResolvedPresentationHydraulicReliefScale = 1.0f;
    float ResolvedRapidFoamFocusStart = 0.12f;
    float ResolvedRapidFoamFocusEnd = 0.72f;
    float ResolvedRapidFoamCoverageGain = 1.0f;
    bool bLivePresentationBankNaturalismEnabled = false;
    float ResolvedPresentationBankNaturalismAmplitudeMeters = 0.0f;
};
