#include "RaftSimRiverWaterConfig.h"

#include "Components/BillboardComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Engine/ExponentialHeightFog.h"
#include "EngineUtils.h"

ARaftSimRiverWaterConfig::ARaftSimRiverWaterConfig()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = false;
    PrimaryActorTick.TickGroup = TG_PostUpdateWork;
    PrimaryActorTick.EndTickGroup = TG_PostUpdateWork;
    USceneComponent* SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(SceneRoot);
}

void ARaftSimRiverWaterConfig::BeginPlay()
{
    Super::BeginPlay();

    if (!bEnforceTaggedHeightFogPresentation ||
        RuntimeHeightFogActorTag.IsNone() ||
        !GetWorld())
    {
        return;
    }

    // UE 5.8 can reapply an older fog state-stream snapshot after normal actor
    // ticks. This river-local PostUpdateWork tick keeps the reviewed values at
    // the end of each frame; all other maps leave the actor tick disabled.
    SetActorTickEnabled(true);
    ApplyTaggedHeightFogPresentation();
}

void ARaftSimRiverWaterConfig::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);

    ApplyTaggedHeightFogPresentation();
}

void ARaftSimRiverWaterConfig::ApplyTaggedHeightFogPresentation()
{
    if (!GetWorld())
    {
        return;
    }

    for (TActorIterator<AExponentialHeightFog> It(GetWorld()); It; ++It)
    {
        AExponentialHeightFog* Fog = *It;
        if (!Fog || !Fog->Tags.Contains(RuntimeHeightFogActorTag))
        {
            continue;
        }
        if (UExponentialHeightFogComponent* FogComponent = Fog->GetComponent())
        {
            FogComponent->SetFogDensity(RuntimeHeightFogDensity);
            FogComponent->SetVolumetricFog(bRuntimeVolumetricFogEnabled);
            FogComponent->FogDensity = RuntimeHeightFogDensity;
            FogComponent->bEnableVolumetricFog =
                bRuntimeVolumetricFogEnabled;
            FogComponent->MarkRenderStateDirty();
        }
    }
}
