#pragma once

// Wraps the first-party finite-volume shallow-water solver (physics/cpp,
// linked as libraftsim_water.a) as a live simulation window for gameplay
// (release-1.0-plan.md §5 A-1). Fixture calibrations and reference playback
// are disabled unconditionally: game water is always the genuine solver.
//
// P2 slice one: a self-contained flat tank window (replaces the constant-depth
// placeholder). River windows are seeded from cooked per-flow-band steady
// fields (raftsim.cooked_flow_fields.v1) and can hand overlapping state to a
// downstream crop without resetting solver time.

#include "CoreMinimal.h"

#if !defined(RAFTSIM_HAS_LIVE_SOLVER)
#define RAFTSIM_HAS_LIVE_SOLVER 0
#endif

#include <memory>

namespace raftsim
{
class ReducedShallowWaterSolver;
}

struct FRaftSimLiveWaterSampleResult
{
    bool bValid = false;
    bool bWet = false;
    /** Absolute source-data elevations; cooked windows restore their internal solver datum. */
    float SurfaceHeightM = 0.0f;
    float BedHeightM = 0.0f;
    float DepthM = 0.0f;
    FVector2D VelocityMps = FVector2D::ZeroVector;
    FVector SurfaceNormal = FVector::UpVector;
};

class FRaftSimLiveWaterWindow
{
public:
    /**
     * Build a still rectangular tank: SizeX/SizeY meters at CellSize meters
     * per cell, flat bed BedHeightM below a still surface at SurfaceHeightM.
     * WorldOriginM anchors the lower corner of solver cell (0,0) in world
     * space (meters, XY).
     */
    static TUniquePtr<FRaftSimLiveWaterWindow> CreateFlatTank(
        const FVector2D& WorldOriginM, float SizeXM, float SizeYM, float CellSizeM,
        float SurfaceHeightM, float DepthM);

    /**
     * Build a river window seeded from cooked steady-state flow fields
     * (schema raftsim.cooked_flow_fields.v1). Loads the band's bed/h/u/v/
     * wet_mask .npy arrays from CookedFieldsDir, verifies each file's sha256
     * against the manifest, crops the region covered by WindowCenterM +/-
     * WindowExtentM/2 (world meters, clamped to the cooked grid), and runs
     * the genuine FV solver with the manifest's solver settings (notably
     * roughness_scale and bed_slope_source_scale; see manifest notes).
     *
     * RoughnessManning is the seed scenario's Manning n: manifest v1 does not
     * record it, so callers pass the band's authored value (the South Fork
     * median seed uses 0.041). Cut edges get transmissive (copy-neighbor)
     * boundaries; window edges coinciding with the cooked grid's cross-stream
     * banks keep the bank condition the fields were cooked with.
     * Explicit Cartesian coupled manifests instead retain MUSCL2 and two
     * exact source ghost layers on all four crop edges. They require matching
     * authored Manning roughness and bRecenterHydraulicCrux=false; incomplete
     * halos fail closed. Their surface has no legacy travelling bake wave.
     *
     * Returns nullptr with a populated OutError on any manifest, hash, or
     * array mismatch. Only available with the solver library linked.
     */
    static TUniquePtr<FRaftSimLiveWaterWindow> CreateFromCookedFields(
        const FString& CookedFieldsDir, const FString& BandId,
        const FVector2D& WindowCenterM, const FVector2D& WindowExtentM,
        float RoughnessManning, FString& OutError,
        bool bRecenterHydraulicCrux = true);

#if WITH_AUTOMATION_TESTS && RAFTSIM_HAS_LIVE_SOLVER
    static int32 GetSharedAtlasLoadCountForTesting();
#endif

    ~FRaftSimLiveWaterWindow();

    /** Advance the genuine FV solver by DtSeconds (internally CFL-substepped). */
    void Step(float DtSeconds);

    /** World-space point sample (meters). Bilinear bed/current; mixed wet/dry
     * surface reconstruction excludes high dry terrain from water elevation.
     * Does not alter the finite-volume state or its transfer representation. */
    FRaftSimLiveWaterSampleResult Sample(const FVector2D& WorldPositionM) const;

    /** Immutable shared river source for presentation outside the live crop.
     * Never a fallback for gameplay sampling. Missing source remains invalid;
     * valid dry cells retain their source bed/depth. Velocity/normal use field XY. */
    FRaftSimLiveWaterSampleResult SamplePresentationSource(const FVector2D& PositionM) const;
    bool HasSharedPresentationSource() const { return PresentationState.IsValid(); }
    /** Exact inclusive live cell-center bounds, excluding source ghost cells. */
    bool GetFieldBoundsM(FBox2D& OutBounds) const;

    double SimTimeSeconds() const;
    uint64 StepCount() const { return StepCounter; }

    /** Total water volume in the window (sum of h * dx * dy), cubic meters. */
    double TotalWaterVolumeM3() const;

    /** Fraction of cells currently wet (depth above the dry tolerance). */
    double WetCellFraction() const;

    /** Wet fraction of the seeded state (cooked wet_mask crop; 1 for tanks). */
    double SeedWetFraction() const { return SeedWetFractionValue; }

    /** True if any h/u/v cell is NaN or infinite. */
    bool HasNonFiniteState() const;

    /**
     * True when the rendered surface above this window carries the
     * travelling bake-wave WPO (cooked river bands). The adapter couples
     * the presentation wave into sampled heights only then; a flat tank
     * renders a flat sheet, and coupling a wave the camera cannot see is
     * exactly the render/physics divergence the coupling exists to close.
     */
    bool HasTravelingWavePresentation() const
    {
        return bHasTravelingWavePresentation;
    }

    /**
     * Copy depth and velocity from every world-space cell shared with the
     * previous window, preserve its solver clock, and return the number of
     * transferred cells. Aligned equal-resolution grids copy solver values
     * directly, without float sampling or a rendering wet/dry threshold.
     * Nonaligned legacy grids retain bilinear transfer. Zero means no transfer.
     */
    int32 TransferOverlapStateFrom(const FRaftSimLiveWaterWindow& PreviousWindow);

private:
    friend class FRaftSimExactWaterOverlapTest;
    friend class FRaftSimCartesianCropBoundaryTest;
    friend class FRaftSimSharedCartesianAtlasTest;
    friend class FRaftSimWaterDryRockSamplingTest;
    FRaftSimLiveWaterWindow();

    struct FPresentationState;
    TSharedPtr<const FPresentationState, ESPMode::ThreadSafe> PresentationState;

    TPimplPtr<raftsim::ReducedShallowWaterSolver> Solver;
    /** World position (meters) of the center of solver cell (0,0). */
    FVector2D OriginM = FVector2D::ZeroVector;
    float CellXM = 1.0f;
    float CellYM = 1.0f;
    /** Datum removed from cooked bed/stage fields before solving, restored when sampling. */
    double ElevationDatumM = 0.0;
    double SeedWetFractionValue = 1.0;
    bool bHasTravelingWavePresentation = false;
    uint64 StepCounter = 0;
};
