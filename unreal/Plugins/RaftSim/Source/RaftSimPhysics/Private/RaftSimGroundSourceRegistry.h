#pragma once
#include "Engine/World.h"
#include "EngineUtils.h"
#include "LandscapeProxy.h"
#include "Components/StaticMeshComponent.h"

// Game-thread contact sources. Keep weak references, but invalidate membership
// when world partition adds/removes levels or gameplay spawns an actor. A
// startup-only list silently misses the actual terrain later in a river run.
class FRaftSimGroundSourceRegistry
{
public:
    explicit FRaftSimGroundSourceRegistry(UWorld* InWorld) : World(InWorld)
    {
        LevelAdded=FWorldDelegates::LevelAddedToWorld.AddRaw(this,&FRaftSimGroundSourceRegistry::LevelChanged);
        LevelRemoved=FWorldDelegates::LevelRemovedFromWorld.AddRaw(this,&FRaftSimGroundSourceRegistry::LevelChanged);
        if (InWorld) ActorSpawned=InWorld->AddOnActorSpawnedHandler(
            FOnActorSpawned::FDelegate::CreateLambda([this](AActor*) { bDirty=true; }));
    }
    ~FRaftSimGroundSourceRegistry()
    {
        FWorldDelegates::LevelAddedToWorld.Remove(LevelAdded);
        FWorldDelegates::LevelRemovedFromWorld.Remove(LevelRemoved);
        if (UWorld* W=World.Get()) W->RemoveOnActorSpawnedHandler(ActorSpawned);
    }
    FRaftSimGroundSourceRegistry(const FRaftSimGroundSourceRegistry&)=delete;
    FRaftSimGroundSourceRegistry& operator=(const FRaftSimGroundSourceRegistry&)=delete;

    void RefreshIfDirty()
    {
        check(IsInGameThread());
        if (!bDirty) return;
        bDirty=false;
        ++RefreshCount;
        Landscapes.Reset(); Meshes.Reset();
        if (UWorld* W=World.Get())
        {
            for (TActorIterator<ALandscapeProxy> It(W); It; ++It) Landscapes.Add(*It);
            for (TActorIterator<AActor> It(W); It; ++It)
            {
                TInlineComponentArray<UStaticMeshComponent*> Components(*It);
                for (UStaticMeshComponent* Mesh:Components)
                    if (It->ActorHasTag(TEXT("RaftSimPhysicalGround")) || Mesh->ComponentHasTag(TEXT("RaftSimPhysicalGround")))
                        Meshes.Add(Mesh);
            }
        }
    }
    uint32 GetRefreshCount() const { return RefreshCount; }
    TArray<TWeakObjectPtr<ALandscapeProxy>> Landscapes;
    TArray<TWeakObjectPtr<UStaticMeshComponent>> Meshes;
private:
    friend class FRaftSimStreamedGroundSourcesTest;
    void LevelChanged(ULevel*,UWorld* ChangedWorld) { if (ChangedWorld==World.Get()) bDirty=true; }
    TWeakObjectPtr<UWorld> World;
    FDelegateHandle LevelAdded,LevelRemoved,ActorSpawned;
    bool bDirty=true;
    uint32 RefreshCount=0;
};
