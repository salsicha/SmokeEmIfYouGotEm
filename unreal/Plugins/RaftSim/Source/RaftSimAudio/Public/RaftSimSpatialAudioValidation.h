#pragma once

#include "CoreMinimal.h"

#include "RaftSimSpatialAudioValidation.generated.h"

UENUM(BlueprintType)
enum class ERaftSimSpatialAudioPlaybackTarget : uint8
{
    StereoSpeakers,
    Headphones,
    VRBinauralHRTF,
    Surround5_1,
    Surround7_1
};

USTRUCT(BlueprintType)
struct FRaftSimSpatialAudioValidationCase
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudio")
    FName CaseId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudio")
    FName SourceType;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudio")
    FString ExpectedReadability;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudio")
    TArray<FName> Metrics;
};

USTRUCT(BlueprintType)
struct FRaftSimSpatialAudioPlatformValidation
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudio")
    ERaftSimSpatialAudioPlaybackTarget PlaybackTarget = ERaftSimSpatialAudioPlaybackTarget::Headphones;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudio")
    TArray<FName> RequiredCases;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudio")
    TArray<FName> RequiredMetrics;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudio")
    bool bRequiresPhysicalDevice = false;
};
