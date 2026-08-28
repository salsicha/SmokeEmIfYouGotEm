#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "UObject/ObjectMacros.h"

#include "RaftSimLiveWaterWindow.h"
#include "Templates/UniquePtr.h"

#include "RaftSimWaterRuntimeAdapter.generated.h"

UENUM(BlueprintType)
enum class ERaftSimWaterRuntimeStatus : uint8
{
    Uninitialized,
    ScenarioBound,
    Running,
    Faulted
};

USTRUCT(BlueprintType)
struct FRaftSimWaterReportManifestState
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    FString ManifestPath;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    FString LockHash;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    int32 LockedArtifactCount = 0;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    bool bLoaded = false;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    bool bAccepted = false;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    bool bLiveWaterBridgeUnblocked = false;
};

USTRUCT(BlueprintType)
struct FRaftSimWaterDeterministicCaptureState
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    FString CapturePath;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    FString LastFrameHash;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    int32 CapturedFrameCount = 0;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    bool bEnabled = false;
};

USTRUCT(BlueprintType)
struct FRaftSimWaterRuntimeConfig
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    FString RuntimeName = TEXT(RAFTSIM_WATER_RUNTIME_NAME);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    FString ScenarioPackagePath;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    FString AcceptedReportSetManifestPath = TEXT("physics/reports/milestone20/report_set_lock.json");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    FString ExpectedReportSetLockHash;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    FString DeterministicCapturePath = TEXT("Saved/Automation/RaftSim/Water/live_water_capture.jsonl");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    float FixedStepSeconds = 1.0f / 60.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    int32 DeterministicSeed = 20;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    bool bUseFiniteVolumeMode = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    bool bRequireAcceptedReportManifest = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    bool bEnableDeterministicCapture = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Water")
    bool bEnableRenderInterpolation = true;
};

USTRUCT(BlueprintType)
struct FRaftSimWaterLiveWindowStats
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    float TotalWaterVolumeM3 = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    float WetFraction = 0.0f;

    /** Wet fraction of the state the window was seeded with (cooked wet_mask). */
    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    float SeedWetFraction = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    bool bHasNonFinite = false;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    float SimTimeSeconds = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    float LastSolverStepMilliseconds = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    float AverageSolverStepMilliseconds = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    float MaxSolverStepMilliseconds = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    int32 LastHandoffTransferredCellCount = 0;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    int32 MovingWindowHandoffCount = 0;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    bool bLastHandoffPreservedState = false;
};

USTRUCT(BlueprintType)
struct FRaftSimWaterSample
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    FVector WorldPosition = FVector::ZeroVector;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    float SurfaceHeightMeters = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    float BedHeightMeters = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    float DepthMeters = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    FVector VelocityMetersPerSecond = FVector::ZeroVector;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    FVector SurfaceNormal = FVector::UpVector;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Water")
    bool bWet = false;
};

/** Deterministic sub-grid rapid displacement shared by rendering and raft support. */
struct FRaftSimWaterStandingWave
{
    float DisplacementMeters = 0.0f;
    float StationSlope = 0.0f;
    float LateralSlope = 0.0f;
};

UCLASS(BlueprintType)
class RAFTSIMWATER_API URaftSimWaterRuntimeAdapter : public UObject
{
    GENERATED_BODY()

public:
    virtual ~URaftSimWaterRuntimeAdapter() override;

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Water")
    void Configure(const FRaftSimWaterRuntimeConfig& InConfig);

    /**
     * Configure a live flat-tank solver window (genuine FV solver, order 2,
     * calibrations disabled). Dev water for the P1/P2 test tank; river
     * windows replace this in P2 slice three. No-op without the solver lib.
     */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Water")
    bool ConfigureDevTankWindow(
        FVector2D WorldOriginM, float SizeXM, float SizeYM, float CellSizeM,
        float SurfaceHeightM, float DepthM);

    /**
     * Configure a live river window seeded from cooked steady-state flow
     * fields (raftsim.cooked_flow_fields.v1). CookedFieldsManifestDir may be
     * repo-relative (e.g. "physics/data/.../cooked_flow_fields"). The window
     * covers WindowCenterM +/- WindowExtentM/2 in scenario-local meters,
     * clamped to the cooked grid. RoughnessManning is the band seed
     * scenario's Manning n (not recorded by manifest v1; the South Fork
     * median band authored 0.041). No-op without the solver lib.
     */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Water")
    bool ConfigureRiverWindow(
        const FString& CookedFieldsManifestDir, const FString& BandId,
        FVector2D WindowCenterM, FVector2D WindowExtentM,
        float RoughnessManning = 0.041f,
        bool bRecenterHydraulicCrux = true);

    /**
     * Load a globally stationed river crop and, when a live crop already
     * exists, transfer every overlapping water cell and preserve solver time.
     * A non-overlapping replacement (the raft teleported or restored far
     * away) reboots the window cold at the new station with a logged
     * warning; during a continuous descent windows always overlap, so
     * ordinary gameplay never resets silently.
     */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Water")
    bool ConfigureMovingRiverWindow(
        const FString& CookedFieldsManifestDir, const FString& BandId,
        FVector2D WindowCenterM, FVector2D WindowExtentM,
        float RoughnessManning = 0.041f);

    /**
     * Bind a dense station/lateral -> curved-world coordinate map. Once bound,
     * world-space water probes are projected onto the real river axis before
     * sampling the solver, and velocities/normals are rotated back into world
     * space. Elevations are shifted by the map's vertical datum so the Unreal
     * world remains near its local origin.
     */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Water")
    bool ConfigureRiverCoordinateMap(const FString& CoordinateMapPath);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water")
    bool HasRiverCoordinateMap() const { return RiverCoordinatePoints.Num() >= 2; }

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Water")
    bool WorldToRiverCoordinates(
        const FVector& WorldPositionCm, FVector2D& OutStationLateralM,
        FVector& OutWorldTangent, FVector& OutWorldLeftNormal) const;

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Water")
    bool RiverToWorldPosition(
        FVector2D StationLateralM, float ElevationM, FVector& OutWorldPositionCm) const;

    /** Inclusive station domain authored by the bound coordinate map. */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Water")
    bool GetRiverStationRangeM(float& OutMinimumStationM, float& OutMaximumStationM) const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water")
    float GetRiverVerticalDatumM() const { return RiverVerticalDatumM; }

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Water")
    bool GetLiveWindowStats(FRaftSimWaterLiveWindowStats& OutStats) const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water")
    bool HasLiveWindow() const;

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Water")
    bool LoadAcceptedReportManifest(const FString& ManifestPath);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water")
    const FRaftSimWaterRuntimeConfig& GetConfig() const { return Config; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water")
    const FRaftSimWaterReportManifestState& GetReportManifestState() const { return ReportManifestState; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water")
    const FRaftSimWaterDeterministicCaptureState& GetCaptureState() const { return CaptureState; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water")
    ERaftSimWaterRuntimeStatus GetStatus() const { return Status; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water")
    int32 GetCommittedWaterFrame() const { return CommittedWaterFrame; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Water")
    float GetSimTimeSeconds() const { return static_cast<float>(SimTimeSeconds); }

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Water")
    bool StepWater(float DeltaSeconds);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Water")
    bool SampleWaterAtWorldPosition(const FVector& WorldPosition, FRaftSimWaterSample& OutSample) const;

    /**
     * Configure the solver-derived surface terms used by the visible live
     * river, then sampled by raft support. D3/overwash keeps its existing
     * water field and does not receive these amplified support terms.
     */
    void ConfigureRaftSupportSurface(
        bool bEnabled,
        float SurfaceSmoothingStrength,
        float StandingWaveScale,
        float HydraulicReliefScale);

    /** One breaking-water site mirrored from the presentation surface. */
    struct FSupportBreakingSite
    {
        FVector2D RiverCoordinatesMeters = FVector2D::ZeroVector;
        float Intensity = 0.0f;
    };

    /** Cooked obstruction footprint shared by the visible solver carrier and
     * rigid raft support. Coordinates are (station, river-left, radius). */
    struct FSupportBoulderFootprint
    {
        FVector2D RiverCoordinatesMeters = FVector2D::ZeroVector;
        float RadiusMeters = 0.75f;
    };

    void ConfigureRaftSupportBoulderFootprints(
        TConstArrayView<FSupportBoulderFootprint> Footprints);
    int32 GetRaftSupportBoulderFootprintCount() const
    {
        return RaftSupportBoulderFootprints.Num();
    }

    /** Signed rolling Y-wake displacement (X) and crest foam (Y). */
    static FVector2D ComputeCoupledBoulderWakePresentation(
        float DownstreamMeters,
        float AcrossMeters,
        float BoulderRadiusMeters,
        float WaterSpeedMetersPerSecond,
        float PhaseSeconds);

    /** Positive upstream pressure pillow around a boulder nose. */
    static float ComputeCoupledBoulderPillowDisplacementMeters(
        float DownstreamMeters,
        float AcrossMeters,
        float BoulderRadiusMeters,
        float WaterSpeedMetersPerSecond);

    /** Strongest configured pillow/Y-wake term at one river coordinate. */
    float ComputeConfiguredBoulderSupportDisplacementMeters(
        const FVector2D& RiverCoordinatesMeters,
        float WaterSpeedMetersPerSecond,
        float PhaseSeconds) const;

    /**
     * Station-indexed mirror of the authored band-water bake: absolute baked
     * surface elevation and hydraulic band energy per (station row, lateral
     * column). Lets rigid support carry the baked sculpt delta and the same
     * halved energetic WPO term the legacy detail-overlay water renders, so
     * the first rapid no longer draws above the ridden surface.
     */
    struct FSupportBandField
    {
        int32 Width = 0;
        float LateralOriginM = 0.0f;
        float LateralSpacingM = 1.0f;
        TArray<float> RowStationsM;
        TArray<float> ElevationAbsM;
        TArray<float> Energy;
        TArray<uint8> Wet;

        bool IsValid() const
        {
            const int32 Cells = Width * RowStationsM.Num();
            return Width > 1 && RowStationsM.Num() > 1 &&
                ElevationAbsM.Num() == Cells && Energy.Num() == Cells &&
                Wet.Num() == Cells;
        }
        void Reset()
        {
            *this = FSupportBandField();
        }
        /** Bilinear sample; false when out of range or any corner is dry. */
        bool Sample(
            float StationM,
            float LateralM,
            float& OutElevationAbsM,
            float& OutEnergy) const;
    };

    /** Load the cooked support band field written by the editor export. */
    bool LoadRaftSupportBandFieldFromFile(const FString& AbsolutePath);

    /**
     * Load the full-reach, terrain-clipped seed used only to continue the
     * visible river beyond a smaller moving hydraulic crop. This field never
     * participates in buoyancy, force, contact, or gameplay sampling.
     */
    bool LoadPresentationBaselineFieldFromFile(const FString& AbsolutePath);

    /**
     * Sample the render-only full-reach baseline in station/lateral space.
     * Returns false outside its organic wet mask. Velocity and depth are
     * conservative presentation values derived from its cooked energy field;
     * the live solver remains authoritative wherever its crop is valid.
     */
    bool SamplePresentationBaselineFieldAtRiverCoordinates(
        FVector2D StationLateralM, FRaftSimWaterSample& OutSample) const;

    /**
     * Flow-warped presentation wave clock pushed by the visible water surface
     * each frame. The coupled swell and band phases consume it so they stay
     * paired with the rendered WPO when waves accelerate in fast water.
     * Negative means unset; world seconds are used as the fallback.
     */
    void SetPresentationWaveClockSeconds(float Seconds)
    {
        PresentationWaveClockSeconds = Seconds;
    }

    /**
     * Mirror the visible carrier's accepted breaking sites into raft support
     * so the ridden surface rises with the rendered crest, dip, and tailwater
     * train instead of leaving them render-only ("the boat submerges as it
     * approaches the rapid"). StationSpacingMeters is the presentation vertex
     * spacing the crest/dip/tail profile is authored against.
     */
    void ConfigureRaftSupportBreakingSites(
        TConstArrayView<FSupportBreakingSite> Sites,
        float CrestLiftMeters,
        float StationSpacingMeters);

    /** Sample the same live crest/hole surface used by the visible carrier. */
    bool SampleRaftSupportSurfaceAtWorldPosition(
        const FVector& WorldPosition,
        FRaftSimWaterSample& OutSample) const;
    bool IsRaftSupportSurfaceEnabled() const
    {
        return bRaftSupportSurfaceEnabled;
    }
    float GetRaftSupportSurfaceSmoothingStrength() const
    {
        return RaftSupportSurfaceSmoothingStrength;
    }
    float GetRaftSupportStandingWaveScale() const
    {
        return RaftSupportStandingWaveScale;
    }
    float GetRaftSupportHydraulicReliefScale() const
    {
        return RaftSupportHydraulicReliefScale;
    }

    static FRaftSimWaterStandingWave ComputeCoupledStandingWave(
        const FVector2D& RiverCoordinatesMeters,
        float SpeedMetersPerSecond,
        float DepthMeters);

    static float ComputeCoupledHydraulicReliefMeters(
        float CenterSurfaceHeightMeters,
        float UpstreamFarSurfaceHeightMeters,
        float UpstreamNearSurfaceHeightMeters,
        float DownstreamNearSurfaceHeightMeters,
        float DownstreamFarSurfaceHeightMeters,
        float SpeedMetersPerSecond,
        float DepthMeters);

    static float ComputeCoupledSmoothedSurfaceHeightMeters(
        float CenterSurfaceHeightMeters,
        float UpstreamSurfaceHeightMeters,
        float DownstreamSurfaceHeightMeters,
        float RiverRightSurfaceHeightMeters,
        float RiverLeftSurfaceHeightMeters,
        float Strength);

    static float ComputeCoupledBreakingReliefMeters(
        const FVector2D& RiverCoordinatesMeters,
        TConstArrayView<FSupportBreakingSite> Sites,
        float CrestLiftMeters,
        float StationSpacingMeters);

    /**
     * Sample the live solver directly in station/lateral coordinates. This is
     * the preferred path for river-aligned render meshes and other systems
     * that already know their authored river coordinates, because it avoids
     * the substantially more expensive world-to-curved-river inversion.
     */
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Water")
    bool SampleWaterAtRiverCoordinates(
        FVector2D StationLateralM, FRaftSimWaterSample& OutSample) const;

    /**
     * Lightweight river-field sample for render grids. Velocity XY and the
     * surface-normal XY components remain in station/lateral solver space;
     * callers that cache their curved-world basis can transform them without
     * repeating coordinate-map searches for every vertex.
     */
    bool SampleWaterFieldAtRiverCoordinates(
        FVector2D StationLateralM, FRaftSimWaterSample& OutSample) const;

    /** Resolve repository-relative source data in editor and staged NonUFS data in builds. */
    static FString ResolveRuntimeDataPath(const FString& Path);

private:
    UPROPERTY()
    FRaftSimWaterRuntimeConfig Config;

    UPROPERTY()
    FRaftSimWaterReportManifestState ReportManifestState;

    UPROPERTY()
    FRaftSimWaterDeterministicCaptureState CaptureState;

    UPROPERTY()
    ERaftSimWaterRuntimeStatus Status = ERaftSimWaterRuntimeStatus::Uninitialized;

    int32 CommittedWaterFrame = 0;
    double SimTimeSeconds = 0.0;
    int32 LastHandoffTransferredCellCount = 0;
    int32 MovingWindowHandoffCount = 0;
    bool bLastHandoffPreservedState = false;
    double TotalSolverStepMilliseconds = 0.0;
    double LastSolverStepMillisecondsValue = 0.0;
    double MaxSolverStepMilliseconds = 0.0;
    int32 TimedSolverStepCount = 0;

    FString BuildDeterministicFrameHash() const;
    void AppendDeterministicCaptureFrame();
    struct FRiverCoordinatePoint
    {
        double StationM = 0.0;
        FVector2D LocalPositionM = FVector2D::ZeroVector;
        FVector2D LeftNormal = FVector2D(0.0, 1.0);
    };

    static constexpr float RiverSpatialHashCellM = 128.0f;
    FIntPoint RiverSpatialHashKey(const FVector2D& PositionM) const;
    void RebuildRiverSpatialHash();
    bool ResolveRiverBasis(
        FVector2D StationLateralM, float ElevationM,
        FVector& OutWorldPositionCm, FVector& OutWorldTangent,
        FVector& OutWorldLeftNormal) const;

    TArray<FRiverCoordinatePoint> RiverCoordinatePoints;
    TMap<FIntPoint, TArray<int32>> RiverSpatialHash;
    /**
     * Consecutive raft probes are only a few metres apart. Preserve the exact
     * ruled-corridor inverse, but seed it from the previous segment instead of
     * rebuilding a several-hundred-segment broad phase for every tube probe.
     * Mutable is safe here because all runtime water sampling is game-thread
     * authority; distant queries automatically fall back to the spatial hash.
     */
    mutable int32 LastWorldToRiverSegment = INDEX_NONE;
    mutable FVector2D LastWorldToRiverPositionM = FVector2D::ZeroVector;
    mutable bool bHasLastWorldToRiverQuery = false;
    float RiverVerticalDatumM = 0.0f;
    FString RiverCoordinateMapPath;

    bool bRaftSupportSurfaceEnabled = false;
    float RaftSupportSurfaceSmoothingStrength = 0.0f;
    float RaftSupportStandingWaveScale = 0.0f;
    float RaftSupportHydraulicReliefScale = 0.0f;
    TArray<FSupportBreakingSite> RaftSupportBreakingSites;
    TArray<FSupportBoulderFootprint> RaftSupportBoulderFootprints;
    float RaftSupportBreakingCrestLiftMeters = 0.0f;
    float RaftSupportBreakingStationSpacingMeters = 1.0f;
    FSupportBandField RaftSupportBandField;
    FSupportBandField PresentationBaselineField;
    float PresentationWaveClockSeconds = -1.0f;

#if RAFTSIM_HAS_LIVE_SOLVER
    TUniquePtr<FRaftSimLiveWaterWindow> LiveWindow;
#endif
};
