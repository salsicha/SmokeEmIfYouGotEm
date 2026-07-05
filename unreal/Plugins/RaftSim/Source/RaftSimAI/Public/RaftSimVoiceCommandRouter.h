#pragma once

#include "CoreMinimal.h"
#include "RaftSimGuideCommands.h"
#include "RaftSimLocalAIInterfaces.h"
#include "RaftSimVoiceCommandSettings.h"
#include "RaftSimVoiceTelemetry.h"
#include "UObject/Object.h"

#include "RaftSimVoiceCommandRouter.generated.h"

UENUM(BlueprintType)
enum class ERaftSimVoiceGameplayMode : uint8
{
    GuidedPaddleRaft,
    RowingOarRig
};

USTRUCT(BlueprintType)
struct FRaftSimVoiceCommandRoute
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Voice")
    FRaftSimGuideCommand Command;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Voice")
    ERaftSimCommandOutcome Outcome = ERaftSimCommandOutcome::IgnoredLowConfidence;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Voice")
    FName DeterministicCrewIntent;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Voice")
    bool bShouldExecute = false;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Voice")
    bool bRequiresConfirmation = false;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Voice")
    FRaftSimVoiceCommandTelemetryEvent Telemetry;
};

UCLASS(BlueprintType)
class RAFTSIMAI_API URaftSimVoiceCommandRouter : public UObject
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Voice")
    FRaftSimVoiceCommandRoute RouteRecognizedSpeech(
        const FRaftSimRecognizedSpeech& RecognizedSpeech,
        ERaftSimVoiceGameplayMode GameplayMode,
        const FRaftSimVoiceCommandSafetySettings& Settings,
        int32 PhysicsFrame,
        FName ConversationStateId
    ) const;

private:
    UPROPERTY()
    TObjectPtr<URaftSimGuideCommandParser> Parser;
};
