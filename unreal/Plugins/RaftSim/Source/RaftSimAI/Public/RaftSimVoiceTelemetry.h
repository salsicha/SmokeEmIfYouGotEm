#pragma once

#include "CoreMinimal.h"
#include "RaftSimGuideCommands.h"

#include "RaftSimVoiceTelemetry.generated.h"

UENUM(BlueprintType)
enum class ERaftSimCommandOutcome : uint8
{
    IgnoredLowConfidence,
    ConfirmationRequested,
    Executed,
    RejectedUnsafe,
    TimedOut
};

USTRUCT(BlueprintType)
struct FRaftSimVoiceCommandTelemetryEvent
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|VoiceTelemetry")
    int32 PhysicsFrame = 0;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|VoiceTelemetry")
    FString RecognizedPhrase;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|VoiceTelemetry")
    ERaftSimGuideCommandIntent Intent = ERaftSimGuideCommandIntent::None;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|VoiceTelemetry")
    FName DeterministicCrewIntent;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|VoiceTelemetry")
    float Confidence = 0.0f;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|VoiceTelemetry")
    float CommandLatencyMs = 0.0f;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|VoiceTelemetry")
    FName CrewResponseId;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|VoiceTelemetry")
    FName ConversationStateId;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|VoiceTelemetry")
    ERaftSimCommandOutcome Outcome = ERaftSimCommandOutcome::IgnoredLowConfidence;
};
