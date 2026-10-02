#pragma once

#include "Components/ActorComponent.h"
#include "CoreMinimal.h"

#include "RaftSimTerrainRefinement.generated.h"

namespace RaftSimTerrainRefinement
{
/**
 * Split cells of a regular render-terrain grid tile (RowSize x Rows vertices,
 * triangles {A, C, B, B, C, D} per cell, row-major) N x N wherever a cell
 * touches a wall corner. New vertices take the bilinear base position and
 * the height FineZ returns for them, in creation order (Ordinal). An edge
 * whose two corners are both off the wall stays straight (bStraightEdge),
 * so cells left whole meet the split ones without cracks. The caller sets
 * the wall corners' own heights in Vertices first; Base holds the heights
 * before that. Normals of the re-meshed vertices are recomputed.
 * Returns the number of split cells.
 */
RAFTSIMRAFT_API int32 BuildRefinedGrid(
    int32 RowSize,
    int32 Rows,
    int32 N,
    const TArray<FVector>& Base,
    const TArray<bool>& WallCorner,
    TArray<FVector>& Vertices,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs,
    TArray<FLinearColor>& Colors,
    TArray<int32>& Triangles,
    TFunctionRef<float(int32 Ordinal, const FVector& BasePosition, bool bStraightEdge)> FineZ);
}

/**
 * Finer render terrain rebuilt when play begins. The editor computes the
 * refinement (for L_Zambezi, the inferred wall ledges) and stores only the
 * moved corner heights and the new vertices' heights here; the saved
 * procedural mesh keeps its plain grid. Procedural-mesh vertices serialise
 * at about 640 bytes each, so baking 0.7 M ledge vertices into the map
 * pushed L_Zambezi.umap past Git LFS's 2 GiB limit; these arrays add ~3 MB.
 * Applied in game worlds only, so an editor save never bakes the
 * refinement back into the map.
 */
UCLASS(ClassGroup = RaftSim)
class RAFTSIMRAFT_API URaftSimTerrainRefinementComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UPROPERTY()
    int32 GridRowSize = 0;

    UPROPERTY()
    int32 GridRows = 0;

    UPROPERTY()
    int32 SplitCount = 4;

    /** Grid vertices on the wall (sorted) and their refined heights (cm). */
    UPROPERTY()
    TArray<int32> WallCornerIndices;

    UPROPERTY()
    TArray<float> WallCornerZ;

    /** Heights (cm) of the vertices the split adds, in creation order. */
    UPROPERTY()
    TArray<float> FineZ;

    /** Rebuild the owner's procedural mesh section 0 with the refinement. */
    bool ApplyRefinement();

protected:
    virtual void BeginPlay() override;

private:
    bool bApplied = false;
};
