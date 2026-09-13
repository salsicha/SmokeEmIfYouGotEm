#pragma once
#include "CoreMinimal.h"
#include "ProceduralMeshComponent.h"
#include <type_traits>

namespace RaftSimWaterVertexCopy
{
// Complete value copies only: no conversion, welding, reordering or removal.
// Fail compilation if an engine update gives this vertex owning/nontrivial
// members. Callers size the destination and must provide disjoint buffers.
static_assert(std::is_trivially_copyable_v<FProcMeshVertex>);
static_assert(std::is_trivially_destructible_v<FProcMeshVertex>);
inline void Prefix(TConstArrayView<FProcMeshVertex> Source,TArray<FProcMeshVertex>& Destination)
{
    check(Destination.Num()>=Source.Num());
    if (!Source.IsEmpty())
        FMemory::Memcpy(Destination.GetData(),Source.GetData(),SIZE_T(Source.Num())*sizeof(FProcMeshVertex));
}
}
