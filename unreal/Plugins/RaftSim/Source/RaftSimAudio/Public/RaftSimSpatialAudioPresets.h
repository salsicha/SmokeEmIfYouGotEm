#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "RaftSimSpatialAudioPresets.generated.h"

UENUM(BlueprintType)
enum class ERaftSimSpatializationMode : uint8
{
    PointSource,
    LineAreaWaterSource,
    LargeRapid,
    AmbisonicBed,
    OccludedBank,
    RaftContact,
    UnderwaterNearWater,
    CrewVoice,
    GuideCommand,
    MultiplayerVoice
};

USTRUCT(BlueprintType)
struct FRaftSimSpatialAudioPreset
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SpatialAudio")
    FName PresetId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SpatialAudio")
    ERaftSimSpatializationMode SpatializationMode = ERaftSimSpatializationMode::PointSource;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SpatialAudio")
    float AttenuationRadiusMeters = 20.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SpatialAudio")
    float SourceSpreadMeters = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SpatialAudio")
    float NearFieldGainDb = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SpatialAudio")
    int32 AmbisonicOrder = 0;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SpatialAudio")
    FName MixBus;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SpatialAudio")
    float OcclusionLowPassHz = 1800.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SpatialAudio")
    bool bUseBinauralForHeadphonesAndVR = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SpatialAudio")
    bool bUseReverbAndOcclusion = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SpatialAudio")
    bool bHeadLockedInVR = false;
};

UCLASS(BlueprintType)
class RAFTSIMAUDIO_API URaftSimSpatialAudioPresetSet : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SpatialAudio")
    TArray<FRaftSimSpatialAudioPreset> Presets;
};
