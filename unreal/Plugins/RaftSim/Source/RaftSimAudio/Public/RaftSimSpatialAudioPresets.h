#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "RaftSimSpatialAudioPresets.generated.h"

UENUM(BlueprintType)
enum class ERaftSimSpatializationMode : uint8
{
    PointSource,
    LargeWaterSource,
    AmbisonicBed,
    CrewVoice,
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
    bool bUseBinauralForHeadphonesAndVR = true;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SpatialAudio")
    bool bUseReverbAndOcclusion = true;
};

UCLASS(BlueprintType)
class RAFTSIMAUDIO_API URaftSimSpatialAudioPresetSet : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|SpatialAudio")
    TArray<FRaftSimSpatialAudioPreset> Presets;
};
