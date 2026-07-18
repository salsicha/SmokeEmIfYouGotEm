#pragma once

// Wraps the first-party finite-volume shallow-water solver (physics/cpp,
// linked as libraftsim_water.a) as a live simulation window for gameplay
// (release-1.0-plan.md §5 A-1). Fixture calibrations and reference playback
// are disabled unconditionally: game water is always the genuine solver.
//
// P2 slice one: a self-contained flat tank window (replaces the constant-depth
// placeholder). Slice two adds river windows seeded from cooked corridor
// fields with a moving-window recenter.

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
     * WorldOriginM anchors solver cell (0,0) in world space (meters, XY).
     */
    static TUniquePtr<FRaftSimLiveWaterWindow> CreateFlatTank(
        const FVector2D& WorldOriginM, float SizeXM, float SizeYM, float CellSizeM,
        float SurfaceHeightM, float DepthM);

    ~FRaftSimLiveWaterWindow();

    /** Advance the genuine FV solver by DtSeconds (internally CFL-substepped). */
    void Step(float DtSeconds);

    /** Bilinear sample at a world-space position (meters). */
    FRaftSimLiveWaterSampleResult Sample(const FVector2D& WorldPositionM) const;

    double SimTimeSeconds() const;
    uint64 StepCount() const { return StepCounter; }

private:
    FRaftSimLiveWaterWindow();

    TPimplPtr<raftsim::ReducedShallowWaterSolver> Solver;
    FVector2D OriginM = FVector2D::ZeroVector;
    float CellM = 1.0f;
    uint64 StepCounter = 0;
};
