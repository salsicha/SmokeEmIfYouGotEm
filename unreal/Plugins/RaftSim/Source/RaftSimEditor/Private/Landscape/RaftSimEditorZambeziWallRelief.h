#pragma once

#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
/**
 * Lava-flow ledges for the 30 km Zambezi run's gorge walls (L_Zambezi).
 *
 * The physical-source Landscape (about 10 x 6 m quads from a 30-50 m
 * reference) and its 12.5 m render tiles can only carry smooth slopes, so the
 * walls read as a half-pipe. Batoka's walls are stacked basalt flows: steep
 * risers and narrow ledges. This field adds that banding as a deterministic
 * function of position and height, applied where the raw ground is a wall
 * (steeper than about 20-32 deg), well above the water (fading in from 4 to
 * 14 m) and within about 480 m of the river:
 * - flow units of 9-14 m whose ledge lines wander up and down along the wall;
 * - a smoothstep riser over the lower 18-40 % of each unit and a flat tread
 *   above it, offset to zero mean so the wall keeps its overall shape.
 * The geometry is INFERRED (generic banding, not measured relief). The
 * Landscape stays the collision authority; only the render tiles and the
 * dressing placement height (so trees and rocks sit on the ledges) use it.
 */
class FZambeziWallRelief
{
public:
    bool Initialize(const FRaftSimLandscapeImportCandidateSpec& Candidate, ALandscape* InLandscape,
        FString& OutSummary);
    bool IsValid() const { return Landscape != nullptr && WaterZ.Num() > 0; }

    /** Raw Landscape height (cm); Fallback when off the Landscape. */
    float RawHeightCm(float X, float Y, float Fallback = 0.0f) const;
    /** 0-1 wall weight from the raw ground's slope, height above the river
     * and distance from it; OutRawZ is the raw height there and OutGradient
     * the raw slope's tangent. */
    float WeightAt(float X, float Y, float& OutRawZ, float* OutGradient = nullptr) const;
    /** The ledge offset (cm) at a point of raw height RawZ on a slope of
     * tangent Gradient. Risers narrower than about 1.3 render cells (4 m)
     * are widened so steep walls step smoothly instead of aliasing into
     * rows of pockets. */
    float ReliefCm(float X, float Y, float RawZ, float Weight, float Gradient) const;
    /** Raw height plus the weighted ledge offset (the dressing's ground). */
    float HeightWithReliefCm(float X, float Y, float Fallback = 0.0f) const;

private:
    ALandscape* Landscape = nullptr;
    float GridMinX = 0.0f;
    float GridMinY = 0.0f;
    int32 GridX = 0;
    int32 GridY = 0;
    /** Nearest river sample per 25 m cell: its water surface and distance. */
    TArray<float> WaterZ;
    TArray<float> RiverDistanceCm;
};

struct FZambeziWallLedgeStats
{
    int32 SubdividedCells = 0;
    int32 AddedVertices = 0;
};

/**
 * The last pass over L_Zambezi's dense render tiles, after the Batoka V17
 * conditioning and the adaptive near-field bank (both read the tiles as
 * grids): compute the 4 x 4 (3.1 m) split of the wall cells and their ledge
 * heights, and store them on a URaftSimTerrainRefinementComponent that
 * rebuilds the mesh when play begins (the saved mesh keeps its plain grid).
 * The tiles cast shadows so the ledges shade each other. Returns the number
 * of tiles done.
 */
int32 ApplyZambeziWallLedges(
    UWorld* World,
    ALandscape* Landscape,
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    FString& OutSummary);
}
