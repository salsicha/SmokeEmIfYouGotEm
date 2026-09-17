#pragma once
#include "Components/StaticMeshComponent.h"
#include "GameFramework/Actor.h"

namespace RaftSimTerrainProbeSources
{
inline bool IsSource(const UPrimitiveComponent* Component)
{
    const AActor* Actor=Component ? Component->GetOwner() : nullptr;
    if (!Actor) return false;
    // Preserve legacy terrain; reconstructed static meshes use exactly the
    // actor/component tag contract of FRaftSimGroundSourceRegistry.
    return Actor->ActorHasTag(TEXT("RaftSimFullReachTerrain")) ||
        (Cast<UStaticMeshComponent>(Component) &&
         (Actor->ActorHasTag(TEXT("RaftSimPhysicalGround")) ||
          Component->ComponentHasTag(TEXT("RaftSimPhysicalGround"))));
}

inline bool ActorHasSource(AActor* Actor)
{
    if (!Actor) return false;
    if (Actor->ActorHasTag(TEXT("RaftSimFullReachTerrain"))) return true;
    TInlineComponentArray<UStaticMeshComponent*> Components(Actor);
    for (const auto* Component : Components) if (IsSource(Component)) return true;
    return false;
}
}
