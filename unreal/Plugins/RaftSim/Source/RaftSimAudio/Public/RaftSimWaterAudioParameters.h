#pragma once

#include "CoreMinimal.h"

#include "RaftSimWaterAudioParameters.generated.h"

USTRUCT(BlueprintType)
struct FRaftSimWaterAudioTelemetry
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Audio")
    float FlowSpeedMetersPerSecond = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Audio")
    float Aeration = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Audio")
    float Turbulence = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Audio")
    float RaftImpactImpulse = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Audio")
    float PaddleCatchStrength = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Audio")
    float RockScrapeStrength = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Audio")
    float WeatherWetness = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Audio")
    float CanyonEnclosure = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Audio")
    float CrewVoiceActivity = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Audio")
    FName CameraPerspective = TEXT("stern_guide");
};

USTRUCT(BlueprintType)
struct FRaftSimWaterAudioParameters
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float RiverRoar = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float RapidFeatureIntensity = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float SprayAndFoam = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float ImpactLayer = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float PaddleLayer = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float ScrapeLayer = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float WeatherLayer = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float CanyonReflection = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Audio")
    float CrewVoiceDuckAmount = 0.0f;
};

namespace RaftSimAudio
{
RAFTSIMAUDIO_API FRaftSimWaterAudioParameters BuildWaterAudioParameters(const FRaftSimWaterAudioTelemetry& Telemetry);
}
