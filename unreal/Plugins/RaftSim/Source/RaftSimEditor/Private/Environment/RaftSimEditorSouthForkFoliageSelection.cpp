#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
namespace
{
float FoliageVariantRandom(int32 CoordinateIndex, int32 Column, int32 Salt)
{
    uint32 Hash = static_cast<uint32>(CoordinateIndex) * 0xA24BAED5u;
    Hash ^= static_cast<uint32>(Column) * 0x9FB21C65u;
    Hash ^= static_cast<uint32>(Salt) * 0xC13FA9A9u;
    Hash ^= Hash >> 16;
    Hash *= 0x7FEB352Du;
    Hash ^= Hash >> 15;
    Hash *= 0x846CA68Bu;
    Hash ^= Hash >> 16;
    return static_cast<float>(Hash & 0x00FFFFFFu) / 16777215.0f;
}
} // namespace

void SelectSouthForkDetailedFoliage(
    UHierarchicalInstancedStaticMeshComponent* const* Conifers,
    UHierarchicalInstancedStaticMeshComponent* Broadleaf,
    UHierarchicalInstancedStaticMeshComponent* Riparian,
    UHierarchicalInstancedStaticMeshComponent* Understory,
    const FLinearColor& SourceDensity,
    float LateralM,
    int32 CoordinateIndex,
    int32 Column,
    UHierarchicalInstancedStaticMeshComponent*& OutTarget,
    float& OutProbability,
    float& OutBaseScale)
{
    OutTarget = nullptr;
    OutProbability = 0.0f;
    OutBaseScale = 1.0f;
    if (SourceDensity.B > 0.12f && FMath::Abs(LateralM) < 105.0f)
    {
        // The source raster resolves riparian cover, not each individual tree.
        // Keep white alder dominant while allowing a bounded live-oak analog
        // population to break the long repeated columnar silhouette.
        const bool bUseWhiteAlder =
            FoliageVariantRandom(CoordinateIndex, Column, 401) < 0.70f;
        OutTarget = bUseWhiteAlder ? Riparian : Broadleaf;
        OutProbability = FMath::Clamp(
            0.12f + SourceDensity.B * 1.05f, 0.0f, 0.88f);
        OutBaseScale = bUseWhiteAlder ? 0.92f : 1.01f;
    }
    else if (SourceDensity.R >= SourceDensity.G && SourceDensity.R > 0.12f)
    {
        const int32 VariantIndex = FMath::Clamp(
            FMath::FloorToInt(
                FoliageVariantRandom(CoordinateIndex, Column, 409) * 3.0f),
            0, 2);
        OutTarget = Conifers ? Conifers[VariantIndex] : nullptr;
        OutProbability = FMath::Clamp(
            0.10f + SourceDensity.R * 0.96f, 0.0f, 0.82f);
        OutBaseScale = 1.0f;
    }
    else if (SourceDensity.G > 0.12f)
    {
        OutTarget = Broadleaf;
        OutProbability = FMath::Clamp(
            0.10f + SourceDensity.G * 0.98f, 0.0f, 0.84f);
        OutBaseScale = 1.10f;
    }
    else if (SourceDensity.A > 0.15f)
    {
        OutTarget = Understory;
        OutProbability = FMath::Clamp(
            0.08f + SourceDensity.A * 0.78f, 0.0f, 0.74f);
        OutBaseScale = 0.75f;
    }
    else
    {
        // Aerial masks become sparse on shadowed banks. Low-density deerbrush
        // is explicit procedural infill, not a claim about a surveyed stem.
        OutTarget = Understory;
        OutProbability = 0.17f;
        OutBaseScale = 0.64f;
    }
}
} // namespace RaftSimEditorEnvironment
