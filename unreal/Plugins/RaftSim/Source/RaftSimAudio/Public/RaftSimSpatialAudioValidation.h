#pragma once

#include "CoreMinimal.h"

#include "RaftSimSpatialAudioValidation.generated.h"

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
