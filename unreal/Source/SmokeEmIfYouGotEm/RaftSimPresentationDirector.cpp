#include "RaftSimPresentationDirector.h"

#include "Components/DirectionalLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/VolumetricCloudComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/ExponentialHeightFog.h"
#include "Engine/SkyLight.h"
#include "EngineUtils.h"
#include "RaftSimSaveSubsystem.h"

namespace
{
template <typename T>
T* FindFirst(UWorld* World)
{
    if (World != nullptr)
    {
        if (TActorIterator<T> It(World); It)
        {
            return *It;
        }
    }
    return nullptr;
}

float Blend(float Current, float Target, float DeltaSeconds, float Speed = 0.65f)
{
    return FMath::FInterpTo(Current, Target, DeltaSeconds, Speed);
}
}

ARaftSimPresentationDirector::ARaftSimPresentationDirector()
{
    PrimaryActorTick.bCanEverTick = true;
}

FRaftSimPresentationEnvironmentState ARaftSimPresentationDirector::MakePreset(
    ERaftSimWeatherVariant Variant)
{
    FRaftSimPresentationEnvironmentState State;
    State.Weather = Variant;
    switch (Variant)
    {
        case ERaftSimWeatherVariant::ClearMorning:
            State.TimeOfDayHours = 8.25f;
            State.WeatherWetness = 0.05f;
            State.CanyonEnclosure = 0.25f;
            State.ReverbStrength = 0.2f;
            State.SunIntensity = 6.5f;
            State.FogDensity = 0.009f;
            State.CloudLayerHeightKm = 8.0f;
            break;
        case ERaftSimWeatherVariant::OvercastAfternoon:
            State.TimeOfDayHours = 14.0f;
            State.WeatherWetness = 0.35f;
            State.CanyonEnclosure = 0.4f;
            State.ReverbStrength = 0.42f;
            State.SunIntensity = 3.8f;
            State.FogDensity = 0.018f;
            State.CloudLayerHeightKm = 5.5f;
            break;
        case ERaftSimWeatherVariant::StormDusk:
            State.TimeOfDayHours = 18.4f;
            State.WeatherWetness = 0.9f;
            State.CanyonEnclosure = 0.62f;
            State.ReverbStrength = 0.72f;
            State.SunIntensity = 1.55f;
            State.FogDensity = 0.035f;
            State.CloudLayerHeightKm = 3.2f;
            break;
    }
    return State;
}

void ARaftSimPresentationDirector::BeginPlay()
{
    Super::BeginPlay();
    ResolveEnvironmentActors();

    ERaftSimWeatherVariant Initial = ERaftSimWeatherVariant::ClearMorning;
    if (const URaftSimSaveSubsystem* Save = GetGameInstance()
            ? GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>() : nullptr)
    {
        if (Save->GetSave() != nullptr)
        {
            const FString Id = Save->GetSave()->Selection.ScenarioId.ToString();
            const uint32 StableScenarioHash = GetTypeHash(Id.ToLower());
            Initial = static_cast<ERaftSimWeatherVariant>(StableScenarioHash % 3u);
            if (Save->GetSave()->ActiveGameMode == ERaftSimGameMode::TrainingEddy)
            {
                Initial = ERaftSimWeatherVariant::ClearMorning;
            }
        }
    }
    SetWeatherVariant(Initial, true);
}

void ARaftSimPresentationDirector::ResolveEnvironmentActors()
{
    Sun = FindFirst<ADirectionalLight>(GetWorld());
    SkyLight = FindFirst<ASkyLight>(GetWorld());
    HeightFog = FindFirst<AExponentialHeightFog>(GetWorld());
    VolumetricCloud = FindFirst<AVolumetricCloud>(GetWorld());

    if (Sun == nullptr)
    {
        Sun = GetWorld()->SpawnActor<ADirectionalLight>(
            ADirectionalLight::StaticClass(), FTransform(FRotator(-42.0f, -128.0f, 0.0f)));
    }
    if (Sun != nullptr && Sun->GetLightComponent() != nullptr)
    {
        Sun->GetLightComponent()->SetMobility(EComponentMobility::Movable);
    }
    if (SkyLight == nullptr)
    {
        SkyLight = GetWorld()->SpawnActor<ASkyLight>(ASkyLight::StaticClass(), FTransform::Identity);
    }
    if (SkyLight != nullptr && SkyLight->GetLightComponent() != nullptr)
    {
        SkyLight->GetLightComponent()->SetMobility(EComponentMobility::Movable);
        // Weather changes alter skylight intensity directly. Recapturing the
        // entire atmosphere and cloud volume every frame added ~3.7 ms on the
        // Apple M5 reference machine without a visible gameplay benefit.
        SkyLight->GetLightComponent()->SetRealTimeCaptureEnabled(false);
    }
    if (HeightFog == nullptr)
    {
        HeightFog = GetWorld()->SpawnActor<AExponentialHeightFog>(
            AExponentialHeightFog::StaticClass(), FTransform::Identity);
    }
    if (VolumetricCloud == nullptr)
    {
        VolumetricCloud = GetWorld()->SpawnActor<AVolumetricCloud>(
            AVolumetricCloud::StaticClass(), FTransform::Identity);
    }
    if (VolumetricCloud != nullptr)
    {
        if (UVolumetricCloudComponent* Cloud =
                VolumetricCloud->FindComponentByClass<UVolumetricCloudComponent>())
        {
            Cloud->SetViewSampleCountScale(0.083333f);
            Cloud->SetReflectionViewSampleCountScale(0.4f);
            Cloud->SetShadowViewSampleCountScale(0.4f);
            Cloud->SetShadowReflectionViewSampleCountScale(0.2f);
        }
    }
}

void ARaftSimPresentationDirector::SetWeatherVariant(
    ERaftSimWeatherVariant Variant, bool bImmediate)
{
    TargetState = MakePreset(Variant);
    switch (Variant)
    {
        case ERaftSimWeatherVariant::ClearMorning:
            TargetSunPitch = -38.0f;
            TargetSunYaw = -128.0f;
            break;
        case ERaftSimWeatherVariant::OvercastAfternoon:
            TargetSunPitch = -62.0f;
            TargetSunYaw = -162.0f;
            break;
        case ERaftSimWeatherVariant::StormDusk:
            TargetSunPitch = -16.0f;
            TargetSunYaw = -205.0f;
            break;
    }
    if (bImmediate)
    {
        CurrentState = TargetState;
        if (Sun != nullptr)
        {
            Sun->SetActorRotation(FRotator(TargetSunPitch, TargetSunYaw, 0.0f));
        }
        ApplyEnvironmentState();
    }
}

void ARaftSimPresentationDirector::CycleWeatherVariant()
{
    const uint8 Next = (static_cast<uint8>(TargetState.Weather) + 1u) % 3u;
    SetWeatherVariant(static_cast<ERaftSimWeatherVariant>(Next), false);
}

void ARaftSimPresentationDirector::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    ElapsedSeconds += DeltaSeconds;
    CurrentState.Weather = TargetState.Weather;
    CurrentState.TimeOfDayHours = Blend(CurrentState.TimeOfDayHours, TargetState.TimeOfDayHours, DeltaSeconds);
    CurrentState.WeatherWetness = Blend(CurrentState.WeatherWetness, TargetState.WeatherWetness, DeltaSeconds);
    CurrentState.CanyonEnclosure = Blend(CurrentState.CanyonEnclosure, TargetState.CanyonEnclosure, DeltaSeconds);
    CurrentState.ReverbStrength = Blend(CurrentState.ReverbStrength, TargetState.ReverbStrength, DeltaSeconds);
    CurrentState.SunIntensity = Blend(CurrentState.SunIntensity, TargetState.SunIntensity, DeltaSeconds);
    CurrentState.FogDensity = Blend(CurrentState.FogDensity, TargetState.FogDensity, DeltaSeconds);
    CurrentState.CloudLayerHeightKm = Blend(
        CurrentState.CloudLayerHeightKm, TargetState.CloudLayerHeightKm, DeltaSeconds);
    ApplyEnvironmentState();
}

void ARaftSimPresentationDirector::ApplyEnvironmentState()
{
    if (Sun != nullptr)
    {
        const FRotator CurrentRotation = Sun->GetActorRotation();
        float NewPitch = FMath::FInterpTo(
            CurrentRotation.Pitch, TargetSunPitch, GetWorld()->GetDeltaSeconds(), 0.5f);
        float NewYaw = FMath::FInterpTo(
            CurrentRotation.Yaw, TargetSunYaw, GetWorld()->GetDeltaSeconds(), 0.5f);
        if (FMath::IsNearlyEqual(NewPitch, TargetSunPitch, 0.02f))
        {
            NewPitch = TargetSunPitch;
        }
        if (FMath::IsNearlyEqual(NewYaw, TargetSunYaw, 0.02f))
        {
            NewYaw = TargetSunYaw;
        }
        if (!FMath::IsNearlyEqual(CurrentRotation.Pitch, NewPitch, 0.001f) ||
            !FMath::IsNearlyEqual(CurrentRotation.Yaw, NewYaw, 0.001f))
        {
            Sun->SetActorRotation(FRotator(NewPitch, NewYaw, 0.0f));
        }
        if (UDirectionalLightComponent* Light = Cast<UDirectionalLightComponent>(Sun->GetLightComponent()))
        {
            Light->SetIntensity(CurrentState.SunIntensity);
            const FLinearColor Color = CurrentState.Weather == ERaftSimWeatherVariant::StormDusk
                ? FLinearColor(1.0f, 0.58f, 0.38f)
                : CurrentState.Weather == ERaftSimWeatherVariant::OvercastAfternoon
                    ? FLinearColor(0.72f, 0.82f, 0.95f)
                    : FLinearColor(1.0f, 0.93f, 0.82f);
            Light->SetLightColor(Color);
        }
    }
    if (SkyLight != nullptr && SkyLight->GetLightComponent() != nullptr)
    {
        const float SkyIntensity = FMath::Lerp(0.9f, 0.48f, CurrentState.WeatherWetness);
        SkyLight->GetLightComponent()->SetIntensity(SkyIntensity);
    }
    if (HeightFog != nullptr && HeightFog->GetComponent() != nullptr)
    {
        HeightFog->GetComponent()->SetFogDensity(CurrentState.FogDensity);
        HeightFog->GetComponent()->SetFogHeightFalloff(
            FMath::Lerp(0.2f, 0.08f, CurrentState.WeatherWetness));
        HeightFog->GetComponent()->SetVolumetricFog(true);
        HeightFog->GetComponent()->SetVolumetricFogExtinctionScale(
            FMath::Lerp(0.7f, 2.2f, CurrentState.WeatherWetness));
    }
    if (VolumetricCloud != nullptr)
    {
        if (UVolumetricCloudComponent* Cloud =
                VolumetricCloud->FindComponentByClass<UVolumetricCloudComponent>())
        {
            Cloud->SetLayerBottomAltitude(
                FMath::Max(0.5f, CurrentState.CloudLayerHeightKm - 2.0f));
            Cloud->SetLayerHeight(CurrentState.CloudLayerHeightKm);
        }
    }
}

FText ARaftSimPresentationDirector::GetWeatherDisplayName() const
{
    switch (TargetState.Weather)
    {
        case ERaftSimWeatherVariant::ClearMorning:
            return NSLOCTEXT("RaftSim", "ClearMorning", "Clear morning");
        case ERaftSimWeatherVariant::OvercastAfternoon:
            return NSLOCTEXT("RaftSim", "OvercastAfternoon", "Overcast afternoon");
        default:
            return NSLOCTEXT("RaftSim", "StormDusk", "Storm dusk");
    }
}

bool ARaftSimPresentationDirector::HasBoundEnvironmentActors() const
{
    return Sun != nullptr && SkyLight != nullptr && HeightFog != nullptr && VolumetricCloud != nullptr;
}
