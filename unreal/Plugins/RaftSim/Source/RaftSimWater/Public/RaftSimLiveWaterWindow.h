#pragma once

// Wraps the first-party finite-volume shallow-water solver (physics/cpp,
// linked as libraftsim_water.a) as a live simulation window for gameplay
// (release-1.0-plan.md §5 A-1). Fixture calibrations and reference playback
// are disabled unconditionally: game water is always the genuine solver.
//
// P2 slice one: a self-contained flat tank window (replaces the constant-depth
// placeholder). This slice adds river windows seeded from cooked per-flow-band
// steady fields (raftsim.cooked_flow_fields.v1); the moving-window recenter
// lands with the corridor streaming slice.

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
     *
     * Returns nullptr with a populated OutError on any manifest, hash, or
     * array mismatch. Only available with the solver library linked.
     */
    static TUniquePtr<FRaftSimLiveWaterWindow> CreateFromCookedFields(
        const FString& CookedFieldsDir, const FString& BandId,
        const FVector2D& WindowCenterM, const FVector2D& WindowExtentM,
        float RoughnessManning, FString& OutError);

    ~FRaftSimLiveWaterWindow();

    /** Advance the genuine FV solver by DtSeconds (internally CFL-substepped). */
    void Step(float DtSeconds);

    /** Bilinear sample at a world-space position (meters). */
    FRaftSimLiveWaterSampleResult Sample(const FVector2D& WorldPositionM) const;

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

private:
    FRaftSimLiveWaterWindow();

    TPimplPtr<raftsim::ReducedShallowWaterSolver> Solver;
    /** World position (meters) of the center of solver cell (0,0). */
    FVector2D OriginM = FVector2D::ZeroVector;
    float CellXM = 1.0f;
    float CellYM = 1.0f;
    double SeedWetFractionValue = 1.0;
    uint64 StepCounter = 0;
};
