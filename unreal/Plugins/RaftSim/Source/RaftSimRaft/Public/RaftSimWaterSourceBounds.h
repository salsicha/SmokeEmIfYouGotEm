#pragma once
#include "CoreMinimal.h"
#include "Async/ParallelFor.h"
#include "ProceduralMeshComponent.h"

namespace RaftSimWaterSourceBounds
{
inline FBox Reference(TConstArrayView<FProcMeshVertex> Source)
{
    FBox Result(ForceInit);
    for (const auto& V : Source) Result += V.Position;
    return Result;
}

inline FBox Parallel(TConstArrayView<FProcMeshVertex> Source)
{
    constexpr int32 BlockSize = 1024;
    if (Source.Num() <= BlockSize) return Reference(Source);
    const int32 Blocks = FMath::DivideAndRoundUp(Source.Num(), BlockSize);
    TArray<FBox> Partial;
    Partial.SetNum(Blocks);
    ParallelFor(Blocks, [&](int32 Block)
    {
        const int32 Begin = Block * BlockSize;
        Partial[Block] = Reference(Source.Slice(Begin, FMath::Min(BlockSize, Source.Num() - Begin)));
    });
    FBox Result(ForceInit);
    // Preserve block order, including equal extrema. No source omission,
    // approximate bounds, reused height, or change to crest padding.
    for (const FBox& Bounds : Partial) Result += Bounds;
    return Result;
}
}
