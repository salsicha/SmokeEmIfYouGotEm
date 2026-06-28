#pragma once

#include "CoreMinimal.h"

#include "RaftSimNetworkTypes.generated.h"

UENUM(BlueprintType)
enum class ERaftSimNetworkArchitecture : uint8
{
    ListenServer,
    DedicatedServer,
    RelaySession,
    LanOfflineCoop
};

UENUM(BlueprintType)
enum class ERaftSimCrewRole : uint8
{
    SternGuide,
    BowLeftPaddler,
    BowRightPaddler,
    MidLeftPaddler,
    MidRightPaddler,
    SafetyRescue,
    SpectatorScout
};

UENUM(BlueprintType)
enum class ERaftSimSeatOccupantKind : uint8
{
    Empty,
    HumanPlayer,
    AIFallback
};

UENUM(BlueprintType)
enum class ERaftSimVoiceMode : uint8
{
    PushToTalk,
    OpenMic,
    Muted
};

UENUM(BlueprintType)
enum class ERaftSimReplicatedIntentType : uint8
{
    GuideCommand,
    PaddleStroke,
    Brace,
    HoldOn,
    HighSide,
    Rescue,
    Recovery,
    CrewAnimation,
    RaftContact,
    ScoreEvent
};

USTRUCT(BlueprintType)
struct FRaftSimSeatDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    FName SeatId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    ERaftSimCrewRole Role = ERaftSimCrewRole::MidLeftPaddler;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    FVector LocalPositionMeters = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    bool bCanBeHuman = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    bool bCanAIFill = true;
};

USTRUCT(BlueprintType)
struct FRaftSimSeatAssignment
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    FName SeatId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    FString PlayerId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    ERaftSimSeatOccupantKind OccupantKind = ERaftSimSeatOccupantKind::Empty;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    bool bReady = false;
};

USTRUCT(BlueprintType)
struct FRaftSimVoiceCommunicationSettings
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    ERaftSimVoiceMode DefaultVoiceMode = ERaftSimVoiceMode::PushToTalk;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    bool bSpatializeBySeat = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    bool bEnableMute = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    bool bEnablePerPlayerVolume = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    bool bEnableSubtitlesOrTranscription = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    bool bEnableModerationHooks = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    bool bRequirePrivacySettings = true;
};

USTRUCT(BlueprintType)
struct FRaftSimReplicatedCrewIntent
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    int32 PhysicsFrame = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    FString PlayerId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    FName SeatId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    ERaftSimReplicatedIntentType IntentType = ERaftSimReplicatedIntentType::PaddleStroke;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    FVector InputVector = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    float ClientTimestampSeconds = 0.0f;
};

USTRUCT(BlueprintType)
struct FRaftSimMultiplayerScoreBreakdown
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    float CrewCoordination = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    float CommandClarity = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    float Safety = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    float LineExecution = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    float RescueTiming = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    float Communication = 0.0f;
};

USTRUCT(BlueprintType)
struct FRaftSimNetworkTelemetryFrame
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    int32 PhysicsFrame = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    float PingMs = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    float JitterMs = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    float PacketLossPercent = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    float CommandLatencyMs = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    float VoiceActivity = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    float PaddleTimingErrorMs = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    float RaftStateDivergenceCm = 0.0f;
};
