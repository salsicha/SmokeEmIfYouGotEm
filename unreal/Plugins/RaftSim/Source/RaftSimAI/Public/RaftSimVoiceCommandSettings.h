#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "RaftSimVoiceCommandSettings.generated.h"

UENUM(BlueprintType)
enum class ERaftSimVoiceActivationMode : uint8
{
    PushToTalk,
    OpenMic,
    DisabledManualOnly
};

USTRUCT(BlueprintType)
struct FRaftSimVoiceCommandSafetySettings
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Voice")
    ERaftSimVoiceActivationMode ActivationMode = ERaftSimVoiceActivationMode::PushToTalk;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Voice")
    float ExecuteConfidenceThreshold = 0.78f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Voice")
    float ConfirmConfidenceThreshold = 0.58f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Voice")
    float MaxCommandLatencyMs = 240.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Voice")
    bool bSubtitlesRequired = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Voice")
    bool bManualInputParityRequired = true;
};

UCLASS(BlueprintType)
class RAFTSIMAI_API URaftSimVoiceCommandSettingsAsset : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Voice")
    FRaftSimVoiceCommandSafetySettings Settings;
};
