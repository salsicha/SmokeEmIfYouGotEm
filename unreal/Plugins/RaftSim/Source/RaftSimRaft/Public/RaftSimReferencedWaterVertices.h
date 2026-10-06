#pragma once
#include "CoreMinimal.h"
#include "ProceduralMeshComponent.h"

// Remove only unreferenced storage. No welding, tolerance, attribute conversion,
// triangle removal or triangle reordering. Ascending source order keeps every
// canonical parent/edge ordering invariant under the index remapping.
struct FRaftSimReferencedWaterVertices
{
    TArray<FProcMeshVertex> Vertices;
    TArray<uint32> Indices;
    TArray<float> Coarse, Shore;
    TArray<int32> Sources;
    TArray<uint32> CachedIndices;
    int32 CachedSourceCount = -1;

    bool Update(TConstArrayView<FProcMeshVertex> Input, const TArray<uint32>& Triangles,
        TConstArrayView<float> InputCoarse, TConstArrayView<float> InputShore)
    {
        if (Input.IsEmpty() || Input.Num()!=InputCoarse.Num() ||
            Input.Num()!=InputShore.Num() || Triangles.Num()%3) return false;
        for (uint32 I:Triangles) if (I>=uint32(Input.Num())) return false;
        if (CachedSourceCount!=Input.Num() || CachedIndices!=Triangles)
        {
            TBitArray<> Referenced(false,Input.Num());
            for (uint32 I:Triangles) Referenced[I]=true;
            // Empty draw lists still retain one valid anchor for scene buffers.
            if (Triangles.IsEmpty()) Referenced[0]=true;
            TArray<int32> Remap; Remap.SetNumUninitialized(Input.Num());
            Sources.Reset();
            for (int32 I=0;I<Input.Num();++I) if(Referenced[I])
            { Remap[I]=Sources.Num(); Sources.Add(I); }
            Indices.SetNumUninitialized(Triangles.Num());
            for(int32 I=0;I<Triangles.Num();++I) Indices[I]=Remap[Triangles[I]];
            CachedIndices=Triangles; CachedSourceCount=Input.Num();
        }
        Vertices.SetNumUninitialized(Sources.Num(),EAllowShrinking::No);
        Coarse.SetNumUninitialized(Sources.Num(),EAllowShrinking::No);
        Shore.SetNumUninitialized(Sources.Num(),EAllowShrinking::No);
        for(int32 I=0;I<Sources.Num();++I)
        {
            const int32 Source=Sources[I];
            Vertices[I]=Input[Source]; Coarse[I]=InputCoarse[Source]; Shore[I]=InputShore[Source];
        }
        return true;
    }
};
