#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "Engine/DataAsset.h"
#include "GameFramework/SaveGame.h"

#include "RaftSimVerticalSliceFrontend.generated.h"

UENUM(BlueprintType)
enum class ERaftSimGameMode : uint8
{
    GuidedDescent,
    FreeRun,
    TrainingEddy
};

UENUM(BlueprintType)
enum class ERaftSimLicenseTier : uint8
{
    Trainee,
    TripLeader,
    SeniorGuide,
    ExpeditionGuide
};

UENUM(BlueprintType)
enum class ERaftSimMedal : uint8
{
    None,
    Bronze,
    Silver,
    Gold
};

UENUM(BlueprintType)
enum class ERaftSimAssistLevel : uint8
{
    Authentic,
    Guided,
    Relaxed
};

UENUM(BlueprintType)
enum class ERaftSimColorCueMode : uint8
{
    Standard,
    DeuteranopiaSafe,
    ProtanopiaSafe,
    TritanopiaSafe,
    Monochrome
};

UENUM(BlueprintType)
enum class ERaftSimInteractionStyle : uint8
{
    Hold,
    Toggle
};

USTRUCT(BlueprintType)
struct FRaftSimCareerScenarioDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Career")
    FName ScenarioId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Career")
    FText DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Career")
    FText Briefing;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Career")
    FName LevelName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Career")
    ERaftSimLicenseTier RequiredLicense = ERaftSimLicenseTier::Trainee;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Career")
    int32 SectionIndex = 0;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Career")
    float StartStationM = -1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Career")
    float FinishStationM = -1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Career")
    bool bTraining = false;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "RaftSim|Career")
    bool bFullDescent = false;
};

USTRUCT(BlueprintType)
struct FRaftSimRunResult
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    FName ScenarioId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    ERaftSimGameMode GameMode = ERaftSimGameMode::GuidedDescent;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    float SafetyScore = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    float OverallScore = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    float RunTimeSeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    int32 SafetyIncidentCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    int32 SwimCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    float FurthestStationM = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    bool bAssistUsed = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    TArray<FVector> GhostRoute;
};

USTRUCT(BlueprintType)
struct FRaftSimScenarioProgress
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    FName ScenarioId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    ERaftSimMedal BestMedal = ERaftSimMedal::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    int32 AttemptCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    int32 CompletionCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    float BestSafetyScore = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    float BestOverallScore = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    float BestTimeSeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    float FurthestStationM = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    FTransform CheckpointTransform = FTransform::Identity;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    bool bHasCheckpoint = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    TArray<FVector> BestGhostRoute;
};

USTRUCT(BlueprintType)
struct FRaftSimCareerStats
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    int32 TotalRuns = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    int32 CompletedRuns = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    int32 CleanRuns = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    int32 TotalSwims = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    float TotalGuideTimeSeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    float LongestDescentStationM = 0.0f;
};

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

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Accessibility")
    float UiScale = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Accessibility")
    float TextScale = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Accessibility")
    float CameraShakeScale = 0.65f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Accessibility")
    float VignetteStrength = 0.35f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Accessibility")
    ERaftSimColorCueMode ColorCueMode = ERaftSimColorCueMode::Standard;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Accessibility")
    ERaftSimInteractionStyle CommandWheelStyle = ERaftSimInteractionStyle::Hold;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Accessibility")
    ERaftSimAssistLevel AssistLevel = ERaftSimAssistLevel::Guided;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Accessibility")
    bool bCaptionsEnabled = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Accessibility")
    bool bGamepadNavigationEnabled = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Accessibility")
    bool bCameraShakeEnabled = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Accessibility")
    bool bVignetteEnabled = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Accessibility")
    bool bGhostEnabled = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Accessibility")
    bool bRouteAssistEnabled = true;
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
    /** Additive schema version. Version zero is the pre-M6 vertical-slice save. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Save")
    int32 SaveVersion = 0;

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

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    ERaftSimGameMode ActiveGameMode = ERaftSimGameMode::TrainingEddy;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    ERaftSimLicenseTier LicenseTier = ERaftSimLicenseTier::Trainee;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    int32 CareerXp = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    TArray<FName> UnlockedScenarioIds;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    TArray<FName> CompletedTrainingDrillIds;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    TArray<FName> CompletedCareerSectionIds;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    TArray<FRaftSimScenarioProgress> ScenarioProgress;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Career")
    FRaftSimCareerStats CareerStats;

    /** Stable action -> key names used by the runtime rebinding screen. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Input")
    TMap<FName, FName> InputBindings;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    bool bCreditsViewed = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RaftSim|Frontend")
    bool bLegalViewed = false;
};

/** Pure catalog and presentation helpers shared by the menu, game mode, and tests. */
UCLASS()
class RAFTSIMUI_API URaftSimProgressionLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintPure, Category = "RaftSim|Career")
    static TArray<FRaftSimCareerScenarioDefinition> GetScenarioCatalog();

    UFUNCTION(BlueprintPure, Category = "RaftSim|Career")
    static bool FindScenario(FName ScenarioId, FRaftSimCareerScenarioDefinition& OutScenario);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Career")
    static ERaftSimMedal CalculateMedal(float OverallScore, float SafetyScore, bool bAssistUsed);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Career")
    static FText MedalDisplayName(ERaftSimMedal Medal);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Career")
    static FText LicenseDisplayName(ERaftSimLicenseTier Tier);
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
