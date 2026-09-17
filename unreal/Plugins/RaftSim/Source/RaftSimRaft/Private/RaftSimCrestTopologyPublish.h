#pragma once
#include "CoreMinimal.h"
#include "Algo/IsSorted.h"
#include "Algo/BinarySearch.h"
#include "Async/ParallelFor.h"

// Only publishes existing topology. No selection, vertex, winding, or ownership changes.
namespace RaftSimCrestTopologyPublish
{
inline void Reference(const TArray<int32>& Triangles, const TArray<int32>& Origins,
    const TArray<int32>& SourceOffsets, TArray<uint32>& Indices, TArray<int32>& Offsets)
{
    Indices.Reset(Triangles.Num());
    for (int32 I : Triangles) Indices.Add(uint32(I));
    Offsets.SetNumUninitialized(SourceOffsets.Num());
    int32 Triangle=0;
    for (int32 Cell=0; Cell<SourceOffsets.Num(); ++Cell)
    {
        while (Triangle<Origins.Num() && Origins[Triangle]<SourceOffsets[Cell]/3) ++Triangle;
        Offsets[Cell]=Triangle*3;
    }
}

inline void Partitioned(const TArray<int32>& Triangles, const TArray<int32>& Origins,
    const TArray<int32>& SourceOffsets, TArray<uint32>& Indices, TArray<int32>& Offsets)
{
    // Refinement emits children grouped in original triangle order. Retain
    // the complete reference behavior even for callers with unordered inputs.
    if (!Algo::IsSorted(Origins) || !Algo::IsSorted(SourceOffsets))
    {
        Reference(Triangles,Origins,SourceOffsets,Indices,Offsets);
        return;
    }
    static_assert(sizeof(int32)==sizeof(uint32));
    Indices.SetNumUninitialized(Triangles.Num());
    // Corresponding signed/unsigned 32-bit integers have identical bits after
    // modulo conversion, including sentinel values; byte copy avoids per-Add checks.
    if (!Triangles.IsEmpty()) FMemory::Memcpy(Indices.GetData(),Triangles.GetData(),SIZE_T(Triangles.Num())*sizeof(int32));
    Offsets.SetNumUninitialized(SourceOffsets.Num());
    constexpr int32 BatchSize=1024;
    ParallelFor(FMath::DivideAndRoundUp(SourceOffsets.Num(),BatchSize),[&](int32 Batch)
    {
        const int32 Begin=Batch*BatchSize, End=FMath::Min(Begin+BatchSize,SourceOffsets.Num());
        int32 Triangle=Algo::LowerBound(Origins,SourceOffsets[Begin]/3);
        for (int32 Cell=Begin; Cell<End; ++Cell)
        {
            while (Triangle<Origins.Num() && Origins[Triangle]<SourceOffsets[Cell]/3) ++Triangle;
            Offsets[Cell]=Triangle*3;
        }
    });
}
}
