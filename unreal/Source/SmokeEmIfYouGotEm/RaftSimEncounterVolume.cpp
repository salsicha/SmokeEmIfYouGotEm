#include "RaftSimEncounterVolume.h"

#include "Components/BoxComponent.h"

ARaftSimEncounterVolume::ARaftSimEncounterVolume()
{
    PrimaryActorTick.bCanEverTick = false;

    Trigger = CreateDefaultSubobject<UBoxComponent>(TEXT("Trigger"));
    SetRootComponent(Trigger);
    Trigger->SetBoxExtent(FVector(500.0f, 500.0f, 300.0f));
    Trigger->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Trigger->SetCollisionResponseToAllChannels(ECR_Overlap);
    Trigger->SetGenerateOverlapEvents(true);
}
