#include "RaftSimPresentationDirector.h"

#include "Components/DirectionalLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/VolumetricCloudComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/ExponentialHeightFog.h"
#include "Engine/SkyLight.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "HAL/IConsoleManager.h"
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

    // Every run opens in the map's authored daylight; T / left-stick click
    // cycles variants in-run. The former scenario-name hash silently
    // condemned specific runs to fixed non-authored weather — measured
    // 2026-08-10: hash("south_fork_upper") selects StormDusk, so South
    // Fork I always played at a -16-degree, 1.55-intensity dusk sun over
    // the authored -42/8.2 Sierra morning, and every reviewer session on
    // the flagship section ran in the dark. Per-scenario weather belongs
    // in the scenario catalog as an authored field, not in a hash.
    SetWeatherVariant(ERaftSimWeatherVariant::ClearMorning, true);
    if (bClearMorningCloudsEnabled &&
        SkyLight != nullptr && SkyLight->GetLightComponent() != nullptr)
    {
        // Capture after ApplyEnvironmentState has made the high clouds
        // visible. A single coherent cubemap lets water reflect the cloudy
        // sky without real-time capture time-slicing different cubemap faces
        // across frames, which appeared as intermittent water flashes.
        SkyLight->GetLightComponent()->RecaptureSky();
    }
}

void ARaftSimPresentationDirector::ResolveEnvironmentActors()
{
    bClearMorningCloudsEnabled =
        GetWorld() != nullptr &&
        GetWorld()->GetMapName().Contains(
            TEXT("L_SouthForkAmerican_FullReach"),
            ESearchCase::IgnoreCase);
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
        // Cloud visibility is applied below and South Fork performs one
        // explicit post-visibility recapture in BeginPlay. Continuous capture
        // time-slices cubemap faces and can flash on broad smooth water.
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
            // The former half-resolution budget still produced visibly
            // stippled cloud edges in the river reflection review. South Fork
            // uses full view and reflection sampling; other maps retain their
            // bounded weather-variant budget.
            const float ViewSamples = bClearMorningCloudsEnabled ? 1.0f : 0.5f;
            const float ReflectionSamples =
                bClearMorningCloudsEnabled ? 1.0f : 0.4f;
            Cloud->SetViewSampleCountScale(ViewSamples);
            Cloud->SetReflectionViewSampleCountScale(ReflectionSamples);
            Cloud->SetShadowViewSampleCountScale(
                bClearMorningCloudsEnabled ? 0.75f : 0.4f);
            Cloud->SetShadowReflectionViewSampleCountScale(
                bClearMorningCloudsEnabled ? 0.75f : 0.2f);
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
        // SetActorRotation normalizes yaw into (-180, 180], so a raw preset
        // like StormDusk's -205 can never be read back; interpolating toward
        // the un-normalized value chased the wrap forever and orbited the
        // sun around the scene (2026-08-09 playtest, and the mid-orbit
        // rotation once saved into the South Fork map). Interpolate along
        // the shortest arc to the normalized-equivalent goal instead.
        const float YawGoal = CurrentRotation.Yaw +
            FMath::FindDeltaAngleDegrees(CurrentRotation.Yaw, TargetSunYaw);
        float NewPitch = FMath::FInterpTo(
            CurrentRotation.Pitch, TargetSunPitch, GetWorld()->GetDeltaSeconds(), 0.5f);
        float NewYaw = FMath::FInterpTo(
            CurrentRotation.Yaw, YawGoal, GetWorld()->GetDeltaSeconds(), 0.5f);
        if (FMath::IsNearlyEqual(NewPitch, TargetSunPitch, 0.02f))
        {
            NewPitch = TargetSunPitch;
        }
        if (FMath::IsNearlyEqual(NewYaw, YawGoal, 0.02f))
        {
            NewYaw = YawGoal;
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
        // Preserve the captured-scene fill authored for the South Fork map.
        // The former 0.9 clear-weather ceiling crushed backlit faces, PPE,
        // and wet rock into black silhouettes in normal gameplay cameras.
        const float SkyIntensity = FMath::Lerp(1.25f, 0.62f, CurrentState.WeatherWetness);
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
            Cloud->SetVisibility(
                bClearMorningCloudsEnabled ||
                    CurrentState.Weather != ERaftSimWeatherVariant::ClearMorning,
                true);
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

bool ARaftSimPresentationDirector::IsCloudLayerVisible() const
{
    const UVolumetricCloudComponent* Cloud = VolumetricCloud
        ? VolumetricCloud->FindComponentByClass<UVolumetricCloudComponent>()
        : nullptr;
    return Cloud != nullptr && Cloud->IsVisible();
}

namespace
{
void HandleSetRaftSimWeather(const TArray<FString>& Args, UWorld* World)
{
    ARaftSimPresentationDirector* Director = FindFirst<ARaftSimPresentationDirector>(World);
    if (Director == nullptr)
    {
        UE_LOG(LogTemp, Error, TEXT("RaftSim.SetWeather: presentation director unavailable"));
        return;
    }
    const FString Requested = Args.Num() > 0 ? Args[0].ToLower() : TEXT("clear_morning");
    ERaftSimWeatherVariant Variant = ERaftSimWeatherVariant::ClearMorning;
    if (Requested == TEXT("overcast") || Requested == TEXT("overcast_afternoon"))
    {
        Variant = ERaftSimWeatherVariant::OvercastAfternoon;
    }
    else if (Requested == TEXT("storm") || Requested == TEXT("storm_dusk"))
    {
        Variant = ERaftSimWeatherVariant::StormDusk;
    }
    Director->SetWeatherVariant(Variant, true);
    UE_LOG(
        LogTemp,
        Display,
        TEXT("RaftSim.SetWeather: %s"),
        *Director->GetWeatherDisplayName().ToString());
}

static FAutoConsoleCommandWithWorldAndArgs GSetRaftSimWeatherCommand(
    TEXT("RaftSim.SetWeather"),
    TEXT("Select a production weather preset immediately: clear_morning, "
         "overcast_afternoon, or storm_dusk."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&HandleSetRaftSimWeather));
}
