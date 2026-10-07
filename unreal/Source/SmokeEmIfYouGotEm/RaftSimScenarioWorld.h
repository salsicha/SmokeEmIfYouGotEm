#pragma once

#include "CoreMinimal.h"
#include "Engine/World.h"
#include "Misc/PackageName.h"

namespace RaftSimScenarioWorld
{
// A saved menu selection is not authority for a different directly opened map.
// Strip only the PIE prefix on the leaf, retaining the complete package path.
inline bool Matches(const UWorld* World, FName LevelName)
{
    if (!World || LevelName.IsNone()) return false;
    const FString Package = World->GetOutermost()->GetName();
    FString Leaf = FPackageName::GetShortName(Package);
    if (!World->StreamingLevelsPrefix.IsEmpty())
        Leaf.RemoveFromStart(World->StreamingLevelsPrefix);
    const FString Canonical = FPackageName::GetLongPackagePath(Package) + TEXT("/") + Leaf;
    return Canonical.Equals(LevelName.ToString(), ESearchCase::IgnoreCase);
}
}
