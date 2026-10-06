#pragma once

#include "CoreMinimal.h"
#include "ProceduralMeshComponent.h"

/**
 * Shared commercial whitewater paddle blade geometry. Lives outside the crew
 * avatar's translation unit so the guide pawn's first-person paddle renders
 * the identical blade the crew holds (2026-08-10: the pawn's hand/paddle
 * anchors had existed since the pawn's creation with nothing attached).
 */
namespace RaftSimPaddleBladeMesh
{
void BuildCommercialPaddleBladeMesh(
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs,
    TArray<FProcMeshTangent>& Tangents);
}
