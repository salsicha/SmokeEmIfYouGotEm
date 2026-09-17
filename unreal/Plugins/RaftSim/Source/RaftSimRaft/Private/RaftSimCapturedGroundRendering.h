#pragma once
#include "RaftSimTerrainProbeSources.h"
#include "Engine/StaticMesh.h"
#include "StaticMeshResources.h"

namespace RaftSimCapturedGroundRendering
{
inline bool Apply(UStaticMeshComponent* Component)
{
    if (!Component || Component->IsDisallowNanite() ||
        !RaftSimTerrainProbeSources::IsSource(Component) ||
        !Component->GetOwner()->ActorHasTag(TEXT("RaftSimSouthForkReconstruction20260912"))) return false;
    const UStaticMesh* Mesh=Component->GetStaticMesh();
    if (!Mesh || Mesh->GetPathName()!=TEXT("/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround.SM_TroublemakerCapturedGround")) return false;
    const FStaticMeshRenderData* Data=Mesh->GetRenderData();
    // The captured source has one complete fallback LOD, not a reduced proxy.
    // Reject a changed asset contract instead of silently choosing coarse art.
    if (!Data || Data->LODResources.Num()!=1 || Data->LODResources[0].GetNumTriangles()!=803842)
    {
        UE_LOG(LogTemp, Error, TEXT("Captured ground exact-render contract unavailable: %s"), *Mesh->GetPathName());
        return false;
    }
    // Actual South Fork captures show a Nanite-only bank/depth discrepancy.
    // A ten-times-finer global threshold did not correct it either. The older
    // survey-candidate residency trial did not exercise this current source.
    // Render the same full source used by complex collision on this mesh only;
    // leave all other Nanite geometry, materials, water and collision unchanged.
    Component->bDisallowNanite=true;
    Component->MarkRenderStateDirty();
    UE_LOG(LogTemp, Display, TEXT("Captured ground exact fallback enabled: component=%s triangles=803842"), *Component->GetPathName());
    return true;
}

inline void ApplyToActor(AActor* Actor)
{
    if (!Actor || !Actor->ActorHasTag(TEXT("RaftSimSouthForkReconstruction20260912"))) return;
    TInlineComponentArray<UStaticMeshComponent*> Components(Actor);
    for (auto* Component:Components) Apply(Component);
}
}
