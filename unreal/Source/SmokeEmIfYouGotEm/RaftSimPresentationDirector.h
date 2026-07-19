#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "RaftSimPresentationDirector.generated.h"

class ADirectionalLight;
class AExponentialHeightFog;
class ASkyLight;
class AVolumetricCloud;

UENUM(BlueprintType)
enum class ERaftSimWeatherVariant : uint8
{
    ClearMorning,
    OvercastAfternoon,
    StormDusk
};

USTRUCT(BlueprintType)
struct FRaftSimPresentationEnvironmentState
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    ERaftSimWeatherVariant Weather = ERaftSimWeatherVariant::ClearMorning;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float TimeOfDayHours = 8.25f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float WeatherWetness = 0.05f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float CanyonEnclosure = 0.25f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float ReverbStrength = 0.2f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float SunIntensity = 6.5f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float FogDensity = 0.009f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float CloudLayerHeightKm = 8.0f;
};

/**
 * Deterministic runtime presentation authority for the shipping weather/time
 * variants. It only drives rendering and audio mix cues; river hydraulics and
 * gameplay remain sourced from the fixed-step water/raft authorities.
 */
UCLASS()
class SMOKEEMIFYOUGOTEM_API ARaftSimPresentationDirector : public AActor
{
    GENERATED_BODY()

public:
    ARaftSimPresentationDirector();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Presentation")
    void CycleWeatherVariant();

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Presentation")
    void SetWeatherVariant(ERaftSimWeatherVariant Variant, bool bImmediate = false);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Presentation")
    FRaftSimPresentationEnvironmentState GetEnvironmentState() const { return CurrentState; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|Presentation")
    FText GetWeatherDisplayName() const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Presentation")
    bool HasBoundEnvironmentActors() const;

private:
    static FRaftSimPresentationEnvironmentState MakePreset(ERaftSimWeatherVariant Variant);
    void ResolveEnvironmentActors();
    void ApplyEnvironmentState();

    UPROPERTY()
    TObjectPtr<ADirectionalLight> Sun;

    UPROPERTY()
    TObjectPtr<ASkyLight> SkyLight;

    UPROPERTY()
    TObjectPtr<AExponentialHeightFog> HeightFog;

    UPROPERTY()
    TObjectPtr<AVolumetricCloud> VolumetricCloud;

    FRaftSimPresentationEnvironmentState CurrentState;
    FRaftSimPresentationEnvironmentState TargetState;
    float ElapsedSeconds = 0.0f;
    float TargetSunPitch = -42.0f;
    float TargetSunYaw = -128.0f;
};
