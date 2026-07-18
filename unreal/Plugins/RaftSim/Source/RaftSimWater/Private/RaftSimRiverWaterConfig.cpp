#include "RaftSimRiverWaterConfig.h"

#include "Components/BillboardComponent.h"

ARaftSimRiverWaterConfig::ARaftSimRiverWaterConfig()
{
    PrimaryActorTick.bCanEverTick = false;
    USceneComponent* SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(SceneRoot);
}
