#pragma once

#include "CoreMinimal.h"
#include "RaftSimChronoRuntimeAdapter.h"
#include "Subsystems/GameInstanceSubsystem.h"

#include "RaftSimReplaySubsystem.generated.h"

USTRUCT(BlueprintType)
struct FRaftSimReplayFrame
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Replay")
    int32 FrameIndex = 0;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Replay")
    float TimeSeconds = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Replay")
    FRaftSimRaftKinematicState RaftState;
};

USTRUCT(BlueprintType)
struct FRaftSimReplayPlaybackState
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Replay")
    FString ReplayManifestPath;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Replay")
    int32 CurrentFrameIndex = 0;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Replay")
    bool bLoaded = false;

    UPROPERTY(BlueprintReadOnly, Category = "RaftSim|Replay")
    bool bPlaying = false;
};

UCLASS()
class RAFTSIMPHYSICS_API URaftSimReplaySubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "RaftSim|Replay")
    bool LoadReplayManifest(const FString& ManifestPath);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Replay")
    void SetPlaying(bool bInPlaying);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Replay")
    FRaftSimReplayFrame AdvanceReplay(float DeltaSeconds);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Replay")
    const FRaftSimReplayPlaybackState& GetPlaybackState() const { return PlaybackState; }

private:
    UPROPERTY()
    FRaftSimReplayPlaybackState PlaybackState;

    float FixedFrameSeconds = 1.0f / 60.0f;
    float AccumulatorSeconds = 0.0f;
};
