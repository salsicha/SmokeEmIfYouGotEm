#pragma once
#include "CoreMinimal.h"
#include "ProceduralMeshComponent.h"
#include "Async/ParallelFor.h"
#include "RaftSimWaterVertexCopy.h"

namespace RaftSimWaterSourcePacking
{
// Output must not alias an input. Every worker writes one complete vertex;
// no UObject query, shared accumulation, color-space change or reordering.
inline bool Pack(TConstArrayView<FVector> Positions,TConstArrayView<FVector> Normals,
    TConstArrayView<FLinearColor> Colors,TConstArrayView<FVector2D> UVs,
    TConstArrayView<FVector2D> Flow,TConstArrayView<FVector2D> Wake,
    TConstArrayView<FProcMeshTangent> Tangents,TArray<FProcMeshVertex>& Output,
    bool bParallel=false,TConstArrayView<FVector2D> SurfaceTransport={})
{
    const int32 N=Positions.Num();
    if (Normals.Num()!=N || Colors.Num()!=N || UVs.Num()!=N || Flow.Num()!=N ||
        Wake.Num()!=N || Tangents.Num()!=N || (SurfaceTransport.Num()!=0 && SurfaceTransport.Num()!=N)) return false;
    // Every member is assigned below. Avoid constructing a second set of
    // default positions/normals/UVs immediately before overwriting all of it.
    Output.SetNumUninitialized(N,EAllowShrinking::No);
    const auto PackVertex=[&](int32 I)
    {
        auto& V=Output[I];
        V.Position=Positions[I]; V.Normal=Normals[I]; V.Color=Colors[I].ToFColor(false);
        V.UV0=UVs[I]; V.UV1=Flow[I]; V.UV2=Wake[I];
        V.UV3=SurfaceTransport.Num() ? SurfaceTransport[I] : FVector2D::ZeroVector;
        V.Tangent=Tangents[I];
    };
    if (bParallel) ParallelFor(TEXT("RaftSimWaterSourcePack"),N,512,PackVertex,EParallelForFlags::Unbalanced);
    else for (int32 I=0; I<N; ++I) PackVertex(I);
    return true;
}
}
