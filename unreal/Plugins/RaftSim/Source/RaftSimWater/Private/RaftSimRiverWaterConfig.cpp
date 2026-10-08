#include "RaftSimRiverWaterConfig.h"
#include "RaftSimRapidChallengeProfiles.h"

#include "Components/BillboardComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/ExponentialHeightFog.h"
#include "EngineUtils.h"

bool ARaftSimRiverWaterConfig::AllowsRiverDiagnostics(const FString& Map,
    const URaftSimWaterRuntimeAdapter& Water) const
{
    if(!RaftSimWaterFeatureKinematics::IsPlayableRiver(Map) && RegisteredRapidChartFingerprint.IsEmpty())
        return false;
    TArray<FRaftSimRapidFeature> Checked;
    FString Error;
    return ResolveRapidFeatures(Map,Water,Checked,Error);
}

bool ARaftSimRiverWaterConfig::ResolveRapidFeatures(const FString& Map,
    const URaftSimWaterRuntimeAdapter& Water,TArray<FRaftSimRapidFeature>& Out,FString& Error) const
{
    Out.Reset();Error.Reset();
    if(RegisteredRapidChartFingerprint.IsEmpty())
    {
        if(!RegisteredRapidFeatures.IsEmpty())
        {Error=TEXT("Registered rapids lack coordinate identity");return false;}
        Out=RaftSimRapidChallengeProfiles::Features(Map);return true;
    }
    double Minimum=0.,Maximum=0.;
    FBox2D Bounds(ForceInit);
    const bool Cartesian=Water.HasCartesianWaterCoordinates();
    if(RegisteredRapidChartFingerprint!=Water.GetRiverCoordinateMapFingerprint() ||
        !(Cartesian ? Water.GetCartesianWaterBoundsM(Bounds) : Water.GetExactRiverStationRangeM(Minimum,Maximum)))
    {Error=TEXT("Registered rapids belong to a different or unavailable coordinate chart");return false;}
    for(const auto& F:RegisteredRapidFeatures)
        if(!RaftSimRapidChallengeProfiles::IsValid(F) ||
            (Cartesian ? !Bounds.IsInsideOrOn(FVector2D(F.Station,F.Lateral)) : F.Station<Minimum || F.Station>Maximum))
        {Error=TEXT("Invalid registered rapid parameters or coordinates");return false;}
    Out=RegisteredRapidFeatures;return true;
}

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

    if (!GetWorld())
    {
        return;
    }

    const bool bMigratedFutaleufuHighlightResponse =
        CookedFieldsDir.Contains(
            TEXT("futaleufu_river_chile"),
            ESearchCase::CaseSensitive);
    const bool bMigratedChilkoHighlightResponse =
        CookedFieldsDir.Contains(
            TEXT("chilko_river_lava_canyon"),
            ESearchCase::CaseSensitive);
    if (bMigratedFutaleufuHighlightResponse ||
        bMigratedChilkoHighlightResponse)
    {
        // Backward-compatible presentation migration for the shipped cold-
        // water maps. Their 4.1-4.2 capture lights spread into a clipped white
        // sheet on the live Single Layer Water surface. Regenerated maps
        // serialize the same tagged intensity explicitly below.
        bEnforceTaggedDirectionalLightPresentation = true;
        RuntimeDirectionalLightActorTag =
            TEXT("RaftSimColdWaterHighlightNaturalismV1");
        RuntimeDirectionalLightIntensity =
            bMigratedFutaleufuHighlightResponse ? 2.40f : 2.90f;
        RuntimeDirectionalLightRotation = bMigratedFutaleufuHighlightResponse
            ? FRotator(-50.0f, 30.0f, 0.0f)
            : FRotator(-50.0f, 55.0f, 0.0f);
    }

    const bool bApplyHeightFog =
        bEnforceTaggedHeightFogPresentation &&
        !RuntimeHeightFogActorTag.IsNone();
    const bool bApplyDirectionalLight =
        bEnforceTaggedDirectionalLightPresentation &&
        !RuntimeDirectionalLightActorTag.IsNone();
    if (!bApplyHeightFog && !bApplyDirectionalLight)
    {
        return;
    }

    // UE 5.8 can reapply an older fog state-stream snapshot after normal actor
    // ticks. This river-local PostUpdateWork tick keeps reviewed environment
    // values at the end of each frame; all other maps leave ticking disabled.
    SetActorTickEnabled(true);
    if (bApplyHeightFog)
    {
        ApplyTaggedHeightFogPresentation();
    }
    if (bApplyDirectionalLight)
    {
        ApplyTaggedDirectionalLightPresentation();
    }
}

void ARaftSimRiverWaterConfig::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);

    ApplyTaggedHeightFogPresentation();
    ApplyTaggedDirectionalLightPresentation();
}

void ARaftSimRiverWaterConfig::ApplyTaggedDirectionalLightPresentation()
{
    if (!GetWorld() || !bEnforceTaggedDirectionalLightPresentation ||
        RuntimeDirectionalLightActorTag.IsNone())
    {
        return;
    }

    for (TActorIterator<ADirectionalLight> It(GetWorld()); It; ++It)
    {
        ADirectionalLight* Light = *It;
        if (!Light || !Light->Tags.Contains(RuntimeDirectionalLightActorTag))
        {
            continue;
        }
        if (UDirectionalLightComponent* LightComponent =
                Cast<UDirectionalLightComponent>(
                    Light->GetLightComponent()))
        {
            Light->SetActorRotation(RuntimeDirectionalLightRotation);
            LightComponent->SetIntensity(RuntimeDirectionalLightIntensity);
        }
    }
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
