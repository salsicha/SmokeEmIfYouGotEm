#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "GameFramework/SaveGame.h"

#include "RaftSimVerticalSliceFrontend.generated.h"

UENUM(BlueprintType)
enum class ERaftSimVerticalSliceScreenKind : uint8
{
    MainMenu,
    RiverSelection,
    Settings,
    SaveSlots,
    ScenarioBriefing,
    PauseMenu,
    ReplayReview,
    DebugOverlays,
    ScoreAndAfterAction
};

USTRUCT(BlueprintType)
struct FRaftSimVerticalSliceSelectionState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    FName RiverId = TEXT("american_south_fork");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    FName SectionId = TEXT("chili_bar_to_coloma");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    FName SeasonId = TEXT("summer_commercial");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    FName FlowBandId = TEXT("median_runnable");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    FName DifficultyId = TEXT("intermediate");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    FName RaftSetupId = TEXT("standard_14ft_paddle_raft");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    FName CrewSetupId = TEXT("ai_training_crew");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    FName ScenarioId = TEXT("first_technical_constriction_wave_train");
};

USTRUCT(BlueprintType)
struct FRaftSimVerticalSliceUserSettings
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    bool bVRComfortMode = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    bool bVoiceCommandsEnabled = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    bool bPushToTalk = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    bool bSubtitlesEnabled = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    bool bDebugOverlaysAllowed = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    float MasterVolume = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    float VoiceCommandSensitivity = 0.7f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    float MotionIntensity = 0.65f;
};

USTRUCT(BlueprintType)
struct FRaftSimVerticalSliceScreenDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Frontend")
    FName ScreenId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Frontend")
    ERaftSimVerticalSliceScreenKind ScreenKind = ERaftSimVerticalSliceScreenKind::MainMenu;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Frontend")
    FText DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Frontend")
    TArray<FName> RequiredActions;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Frontend")
    bool bAvailableInVerticalSlice = true;
};

USTRUCT(BlueprintType)
struct FRaftSimReplayReviewBookmark
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    FName BookmarkId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    float TimeSeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    TArray<FName> Tags;
};

USTRUCT(BlueprintType)
struct FRaftSimDebugOverlayToggle
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    FName OverlayId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    FString SourceManifest;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    bool bDefaultEnabled = false;
};

UCLASS(BlueprintType)
class RAFTSIMUI_API URaftSimVerticalSliceSaveGame : public USaveGame
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    FRaftSimVerticalSliceSelectionState Selection;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    FRaftSimVerticalSliceUserSettings Settings;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    FString LastReplayManifestPath;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    TArray<FName> CompletedScenarioIds;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    float BestSafetyScore = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    float BestOverallScore = 0.0f;
};

UCLASS(BlueprintType)
class RAFTSIMUI_API URaftSimVerticalSliceFrontendConfig : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Frontend")
    FString Schema = TEXT("raftsim.unreal.vertical_slice_frontend.v1");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Frontend")
    FString RiverSelectionCatalog = TEXT("unreal/Content/RaftSim/UI/river_selection_catalog.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Frontend")
    FString VerticalSliceManifest = TEXT("unreal/Content/RaftSim/VerticalSlice/first_rapid_vertical_slice.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Frontend")
    FString ReplayManifest = TEXT("physics/data/readiness/milestone_10/unreal_visualization/manifest.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Frontend")
    FString DebugViewManifest = TEXT("unreal/Content/RaftSim/Debug/live_water_debug_views.json");

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Frontend")
    TArray<FRaftSimVerticalSliceScreenDefinition> Screens;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Frontend")
    FRaftSimVerticalSliceSelectionState DefaultSelection;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Frontend")
    FRaftSimVerticalSliceUserSettings DefaultSettings;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Frontend")
    TArray<FRaftSimReplayReviewBookmark> ReplayBookmarks;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Frontend")
    TArray<FRaftSimDebugOverlayToggle> DebugOverlays;
};
