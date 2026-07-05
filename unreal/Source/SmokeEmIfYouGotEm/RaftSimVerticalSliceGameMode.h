#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"

#include "RaftSimVerticalSliceGameMode.generated.h"

UENUM(BlueprintType)
enum class ERaftSimVerticalSliceScenarioKind : uint8
{
    TrainingSection,
    TechnicalRapid
};

USTRUCT(BlueprintType)
struct FRaftSimRapidScoreBreakdown
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|VerticalSlice")
    float Safety = 0.0f;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|VerticalSlice")
    float LineChoice = 0.0f;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|VerticalSlice")
    float BoatAngle = 0.0f;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|VerticalSlice")
    float PaddleEfficiency = 0.0f;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "RaftSim|VerticalSlice")
    float CrewTrust = 0.0f;

    float Total() const { return Safety + LineChoice + BoatAngle + PaddleEfficiency + CrewTrust; }
};

USTRUCT(BlueprintType)
struct FRaftSimVerticalSliceScenarioDefinition
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "RaftSim|VerticalSlice")
    FName ScenarioId;

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "RaftSim|VerticalSlice")
    ERaftSimVerticalSliceScenarioKind ScenarioKind = ERaftSimVerticalSliceScenarioKind::TrainingSection;

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "RaftSim|VerticalSlice")
    FString DisplayName;

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "RaftSim|VerticalSlice")
    FName RiverId = TEXT("american_south_fork");

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "RaftSim|VerticalSlice")
    FName SectionId = TEXT("chili_bar_to_coloma");

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "RaftSim|VerticalSlice")
    FName FlowBand;

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "RaftSim|VerticalSlice")
    FName DifficultyPreset;

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "RaftSim|VerticalSlice")
    FString ScenarioPackagePath = TEXT("physics/data/real_world/south_fork_american_chili_bar/scenario/scenario.json");

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "RaftSim|VerticalSlice")
    FString LiveWaterManifest = TEXT("unreal/Content/RaftSim/Physics/live_water_bridge.json");

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "RaftSim|VerticalSlice")
    FString RaftContactAuthorityManifest = TEXT("unreal/Content/RaftSim/Physics/raft_contact_authority_integration.json");

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "RaftSim|VerticalSlice")
    FString CrewSafetyManifest = TEXT("unreal/Content/RaftSim/Crew/crew_overboard_safety_states.json");

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "RaftSim|VerticalSlice")
    FString ScoringManifest = TEXT("unreal/Content/RaftSim/Crew/gameplay_telemetry_scoring.json");

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "RaftSim|VerticalSlice")
    TArray<FName> RequiredObjectives;

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "RaftSim|VerticalSlice")
    bool bUsesLiveCustomWater = true;

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "RaftSim|VerticalSlice")
    bool bUsesSelectedRaftContactAuthority = true;

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "RaftSim|VerticalSlice")
    bool bUsesCrewSafetyStates = true;

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "RaftSim|VerticalSlice")
    bool bAfterActionFeedbackRequired = true;
};

UCLASS()
class SMOKEEMIFYOUGOTEM_API ARaftSimVerticalSliceGameMode : public AGameModeBase
{
    GENERATED_BODY()

public:
    ARaftSimVerticalSliceGameMode();

    UFUNCTION(BlueprintCallable, Category = "RaftSim|VerticalSlice")
    void RestartRapid();

    UFUNCTION(BlueprintCallable, Category = "RaftSim|VerticalSlice")
    bool SetActiveScenario(FName ScenarioId);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|VerticalSlice")
    void CompleteRapid(const FRaftSimRapidScoreBreakdown& FinalScore, const TArray<FString>& FeedbackNotes);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|VerticalSlice")
    void SetReplayEnabled(bool bInReplayEnabled);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|VerticalSlice")
    void SetDebugForceVisualizationEnabled(bool bInEnabled);

    UFUNCTION(BlueprintPure, Category = "RaftSim|VerticalSlice")
    const FRaftSimRapidScoreBreakdown& GetCurrentScore() const { return CurrentScore; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|VerticalSlice")
    TArray<FRaftSimVerticalSliceScenarioDefinition> GetScenarioDefinitions() const { return ScenarioDefinitions; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|VerticalSlice")
    FName GetActiveScenarioId() const { return ActiveScenarioId; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|VerticalSlice")
    TArray<FString> GetAfterActionFeedback() const { return AfterActionFeedback; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|VerticalSlice")
    bool IsRapidComplete() const { return bRapidComplete; }

    UFUNCTION(BlueprintPure, Category = "RaftSim|VerticalSlice")
    int32 GetReplayFrame() const { return ReplayFrame; }

private:
    void InitializeScenarioDefinitions();

    UPROPERTY()
    FRaftSimRapidScoreBreakdown CurrentScore;

    UPROPERTY()
    TArray<FRaftSimVerticalSliceScenarioDefinition> ScenarioDefinitions;

    UPROPERTY()
    FName ActiveScenarioId;

    UPROPERTY()
    TArray<FString> AfterActionFeedback;

    UPROPERTY()
    int32 ReplayFrame = 0;

    UPROPERTY()
    bool bRapidComplete = false;

    bool bReplayEnabled = true;
    bool bDebugForceVisualizationEnabled = true;
};
