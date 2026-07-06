#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "RaftSimWaterDebugViews.h"
#include "UObject/Object.h"

#include "RaftSimReplayDebugViewer.generated.h"

USTRUCT(BlueprintType)
struct RAFTSIMEDITOR_API FRaftSimReplayDebugBookmark
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReplayDebug")
    FName BookmarkId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReplayDebug")
    FText DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReplayDebug")
    float TimeSeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReplayDebug")
    TArray<FName> Tags;
};

USTRUCT(BlueprintType)
struct RAFTSIMEDITOR_API FRaftSimReplayDebugOverlayToggle
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReplayDebug")
    ERaftSimWaterDebugView View = ERaftSimWaterDebugView::Depth;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReplayDebug")
    FName OverlayId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReplayDebug")
    FText DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReplayDebug")
    bool bDefaultEnabled = false;
};

UCLASS(BlueprintType)
class RAFTSIMEDITOR_API URaftSimReplayDebugViewerConfig : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReplayDebug")
    FString Schema = TEXT("raftsim.unreal.replay_debug_viewer.v1");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReplayDebug")
    FString SourceManifestPath = TEXT("unreal/Content/RaftSim/Tools/replay_debug_viewer.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReplayDebug")
    FString ReplayManifestPath = TEXT("physics/data/readiness/milestone_10/unreal_visualization/manifest.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReplayDebug")
    FString ReplayJsonPath = TEXT("physics/data/readiness/milestone_10/unreal_visualization/replay.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReplayDebug")
    FString ForceTelemetryCsvPath = TEXT("physics/data/readiness/milestone_10/unreal_visualization/telemetry_forces.csv");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReplayDebug")
    FString DebugViewManifestPath = TEXT("unreal/Content/RaftSim/Debug/live_water_debug_views.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReplayDebug")
    int32 FrameCount = 5;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReplayDebug")
    float FixedDeltaSeconds = 1.0f / 60.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReplayDebug")
    TArray<FRaftSimReplayDebugBookmark> Bookmarks;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|ReplayDebug")
    TArray<FRaftSimReplayDebugOverlayToggle> Overlays;
};

UCLASS(BlueprintType)
class RAFTSIMEDITOR_API URaftSimReplayDebugViewerViewModel : public UObject
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "RaftSim|ReplayDebug")
    void Configure(URaftSimReplayDebugViewerConfig* InConfig);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|ReplayDebug")
    bool SetPlaybackTime(float InTimeSeconds);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|ReplayDebug")
    bool JumpToBookmark(FName BookmarkId);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|ReplayDebug")
    void SetOverlayEnabled(ERaftSimWaterDebugView View, bool bEnabled);

    UFUNCTION(BlueprintPure, Category = "RaftSim|ReplayDebug")
    bool IsOverlayEnabled(ERaftSimWaterDebugView View) const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|ReplayDebug")
    float GetPlaybackTimeSeconds() const { return PlaybackTimeSeconds; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|ReplayDebug")
    FName GetCurrentBookmarkId() const { return CurrentBookmarkId; }

private:
    const FRaftSimReplayDebugBookmark* FindBookmark(FName BookmarkId) const;
    float GetMaxPlaybackTimeSeconds() const;

    UPROPERTY()
    TObjectPtr<URaftSimReplayDebugViewerConfig> Config;

    UPROPERTY()
    TMap<ERaftSimWaterDebugView, bool> OverlayStates;

    UPROPERTY()
    FName CurrentBookmarkId;

    UPROPERTY()
    float PlaybackTimeSeconds = 0.0f;
};
