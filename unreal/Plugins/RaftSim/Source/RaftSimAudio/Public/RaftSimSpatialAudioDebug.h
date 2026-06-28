#pragma once

#include "CoreMinimal.h"

#include "RaftSimSpatialAudioDebug.generated.h"

USTRUCT(BlueprintType)
struct FRaftSimSpatialAudioDebugEmitterState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudioDebug")
    FName EmitterId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudioDebug")
    FName PresetId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudioDebug")
    FVector WorldLocation = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudioDebug")
    float AttenuationRadiusMeters = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudioDebug")
    float SourceSpreadMeters = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudioDebug")
    bool bOcclusionTraceBlocked = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudioDebug")
    float OcclusionTraceDistanceMeters = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudioDebug")
    float ReverbSendDb = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudioDebug")
    float AmbisonicYawDegrees = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudioDebug")
    int32 ActiveVoiceCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudioDebug")
    int32 MixPriority = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudioDebug")
    float EstimatedRuntimeCostMs = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudioDebug")
    bool bVirtualized = false;
};

USTRUCT(BlueprintType)
struct FRaftSimSpatialAudioDebugFrame
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudioDebug")
    double AudioTimeSeconds = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudioDebug")
    TArray<FRaftSimSpatialAudioDebugEmitterState> Emitters;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudioDebug")
    int32 TotalVoiceCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudioDebug")
    float AudioRenderCostMs = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|SpatialAudioDebug")
    float SpatializationCostMs = 0.0f;
};
