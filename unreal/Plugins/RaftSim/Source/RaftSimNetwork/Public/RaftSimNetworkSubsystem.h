#pragma once

#include "CoreMinimal.h"
#include "RaftSimNetworkTypes.h"
#include "Subsystems/GameInstanceSubsystem.h"

#include "RaftSimNetworkSubsystem.generated.h"

USTRUCT(BlueprintType)
struct FRaftSimNetworkSessionConfig
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    ERaftSimNetworkArchitecture Architecture = ERaftSimNetworkArchitecture::ListenServer;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    int32 MaxHumanPlayers = 8;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    bool bAllowAIFillForEmptySeats = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    bool bEnableHostMigrationPlanning = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Network")
    FRaftSimVoiceCommunicationSettings VoiceSettings;
};

USTRUCT(BlueprintType)
struct FRaftSimNetworkSessionState
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Network")
    FRaftSimNetworkSessionConfig Config;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Network")
    TArray<FRaftSimSeatAssignment> SeatAssignments;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Network")
    TArray<FRaftSimNetworkTelemetryFrame> RecentTelemetry;
};

UCLASS()
class RAFTSIMNETWORK_API URaftSimNetworkSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Network")
    void ConfigureSession(const FRaftSimNetworkSessionConfig& InConfig);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Network")
    bool AssignSeat(const FName& SeatId, const FString& PlayerId, ERaftSimSeatOccupantKind OccupantKind);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Network")
    bool SetPlayerReady(const FString& PlayerId, bool bReady);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Network")
    bool ApplyAIFallbackToSeat(const FName& SeatId);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Network")
    void RecordTelemetryFrame(const FRaftSimNetworkTelemetryFrame& TelemetryFrame);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Network")
    const FRaftSimNetworkSessionState& GetSessionState() const { return SessionState; }

private:
    UPROPERTY()
    FRaftSimNetworkSessionState SessionState;
};
