#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"

#include "RaftSimTelemetryPresentationCues.generated.h"

USTRUCT(BlueprintType)
struct FRaftSimPresentationTelemetrySample
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Presentation")
    float WaterDepthMeters = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Presentation")
    float FlowSpeedMetersPerSecond = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Presentation")
    float FroudeNumber = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Presentation")
    float Aeration = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Presentation")
    float Turbulence = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Presentation")
    float SurfaceShear = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Presentation")
    float Wetness = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Presentation")
    float RaftContactImpulse = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Presentation")
    float RockScrapeStrength = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Presentation")
    float PaddleCatchStrength = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Presentation")
    float PaddleBladeDepth = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Presentation")
    float WeatherWetness = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Presentation")
    float CanyonEnclosure = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Presentation")
    float ReverbZoneStrength = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Presentation")
    float OcclusionStrength = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Presentation")
    float HazardProximity = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Presentation")
    float BoatSubmersion = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Presentation")
    float SwimmerUrgency = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Presentation")
    float SwimmerVisibility = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Presentation")
    float RescueInteraction = 0.0f;
};

USTRUCT(BlueprintType)
struct FRaftSimVisualPresentationCues
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float WaterReadability = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float FoamAmount = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float SprayAmount = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float WetRockAmount = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float SurfaceStreakAmount = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float AeratedWaterAmount = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float HazardContrast = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float RaftContactCue = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float PaddleCue = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float WeatherCue = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float RescueCue = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float DebugContrast = 0.0f;
};

USTRUCT(BlueprintType)
struct FRaftSimSpatialAudioPresentationCues
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float RiverBed = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float LargeRapid = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float NearWaterDetail = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float RaftContact = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float Paddle = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float Weather = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float AmbisonicBed = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float ReverbSend = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float OcclusionAmount = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float RescueCallout = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    float UnderwaterNearWater = 0.0f;
};

USTRUCT(BlueprintType)
struct FRaftSimTelemetryPresentationCueFrame
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    FRaftSimVisualPresentationCues Visuals;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    FRaftSimSpatialAudioPresentationCues Audio;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Presentation")
    FName PrimaryCue = TEXT("water_readability");
};

UCLASS()
class RAFTSIMAUDIO_API URaftSimTelemetryPresentationCueLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintPure, Category = "RaftSim|Presentation")
    static FRaftSimTelemetryPresentationCueFrame BuildPresentationCues(const FRaftSimPresentationTelemetrySample& Telemetry);
};
