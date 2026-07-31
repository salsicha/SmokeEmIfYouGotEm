#pragma once

#include "CoreMinimal.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimChronoRuntimeAdapter.h"

class UStaticMesh;

// Procedural geometry for a self-bailing paddle raft (P4 photoreal track).
// Builds a real inflatable-raft silhouette — a continuous outer tube loop with
// an upturned bow/stern kick, two cross thwarts, and an inset floor — so the
// craft reads as a raft rather than a blockout box. All sections are returned
// separately so the tubes (PVC), floor (grippy rubber), and perimeter safety
// rigging take different materials.
namespace RaftSimRaftMesh
{

struct FMeshData
{
    TArray<FVector> Vertices;
    TArray<int32> Triangles;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<FProcMeshTangent> Tangents;
};

/** Persistent presentation state derived from calibrated contact exposure. */
struct FRaftSimRaftVisualCondition
{
    /** Remaining inflation, where one is nominal pressure. */
    float PressureFraction = 1.0f;
    /** Remaining fabric integrity, where one is undamaged. */
    float Integrity = 1.0f;
    /** Permanent crease amplitude in metres. */
    float CreaseAmplitudeM = 0.0f;
};

/** One immutable Gaussian influence from a D1-D4 segment to an authored vertex. */
struct FProductionRaftDeformationInfluence
{
    int32 SegmentIndex = INDEX_NONE;
    float Weight = 0.0f;
    float GradientXFactor = 0.0f;
    float GradientYFactor = 0.0f;
};

/** Compact adjacency for one material section; Starts has vertex-count + 1 entries. */
struct FProductionRaftDeformationSectionCache
{
    TArray<int32> Starts;
    TArray<FProductionRaftDeformationInfluence> Influences;
};

/**
 * Reusable binding between fixed production topology and the fixed 12-segment
 * D1-D4 layout. Dynamic contact values still come from the current solve; only
 * rest-position Gaussian weights and gradients are retained between frames.
 */
struct FProductionRaftDeformationCache
{
    float TubeRadiusM = 0.0f;
    TArray<FVector> SegmentPositionsCm;
    TArray<FProductionRaftDeformationSectionCache> Sections;

    void Reset()
    {
        TubeRadiusM = 0.0f;
        SegmentPositionsCm.Reset();
        Sections.Reset();
    }
};

/**
 * Build the tube loop + thwarts (OutTubes), floor (OutFloor), and optional
 * perimeter grab line, metal D-rings, and rubber chamber details for a raft of
 * the given footprint. Every optional detail follows the same D4 deformation
 * field as the fabric. Units are centimetres, centred on the actor origin,
 * with tube bottoms at z=0.
 *
 * @param LengthM      bow-to-stern footprint (X)
 * @param WidthM       port-to-starboard footprint (Y)
 * @param TubeRadiusM  side-tube cross-section radius
 */
RAFTSIMRAFT_API void BuildInflatableRaft(
    float LengthM, float WidthM, float TubeRadiusM,
    FMeshData& OutTubes, FMeshData& OutFloor,
    const TArray<FRaftSimFlexVisualSegmentState>& Deformation = {},
    const FRaftSimRaftVisualCondition& Condition = {},
    FMeshData* OutRigging = nullptr,
    FMeshData* OutMetalFittings = nullptr,
    FMeshData* OutRubberDetails = nullptr);

/**
 * Read a cooked CPU-accessible production static mesh into five material
 * sections. The resulting rest data is collisionless presentation topology;
 * no StaticMesh collision or physics state is consulted.
 */
RAFTSIMRAFT_API bool ExtractProductionRaftRestMesh(
    const UStaticMesh* StaticMesh,
    TArray<FMeshData>& OutSections);

/**
 * Apply the existing D4-derived continuous deformation field to an authored
 * production rest mesh. Topology and UVs remain fixed so the procedural mesh
 * component can update vertices without replacing physics authority.
 */
RAFTSIMRAFT_API void DeformProductionRaftRestMesh(
    const TArray<FMeshData>& RestSections,
    float TubeRadiusM,
    const TArray<FRaftSimFlexVisualSegmentState>& Deformation,
    const FRaftSimRaftVisualCondition& Condition,
    TArray<FMeshData>& OutSections,
    FProductionRaftDeformationCache* ReusableCache = nullptr);

} // namespace RaftSimRaftMesh
