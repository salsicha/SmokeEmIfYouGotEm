#pragma once

#include "CoreMinimal.h"
#include "ProceduralMeshComponent.h"

// Procedural geometry for a self-bailing paddle raft (P4 photoreal track).
// Builds a real inflatable-raft silhouette — a continuous outer tube loop with
// an upturned bow/stern kick, two cross thwarts, and an inset floor — so the
// craft reads as a raft rather than a blockout box. All sections are returned
// separately so the tubes (PVC) and floor (grippy rubber) take different
// materials.
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

/**
 * Build the tube loop + thwarts (OutTubes) and the floor (OutFloor) for a raft
 * of the given footprint. Units are centimetres, centred on the actor origin,
 * with the tube bottoms at z=0 (so it sits on the waterline like the old box).
 *
 * @param LengthM      bow-to-stern footprint (X)
 * @param WidthM       port-to-starboard footprint (Y)
 * @param TubeRadiusM  side-tube cross-section radius
 */
void BuildInflatableRaft(
    float LengthM, float WidthM, float TubeRadiusM,
    FMeshData& OutTubes, FMeshData& OutFloor);

} // namespace RaftSimRaftMesh
