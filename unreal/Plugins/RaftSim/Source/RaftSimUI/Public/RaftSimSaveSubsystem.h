#pragma once

#include "CoreMinimal.h"
#include "RaftSimVerticalSliceFrontend.h"
#include "Subsystems/GameInstanceSubsystem.h"

#include "RaftSimSaveSubsystem.generated.h"

/** Loads the single save slot at startup and persists it on demand. */
UCLASS()
class RAFTSIMUI_API URaftSimSaveSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    static const TCHAR* SlotName;
    static constexpr int32 CurrentSaveVersion = 3;

    virtual void Initialize(FSubsystemCollectionBase& Collection) override;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Save")
    URaftSimVerticalSliceSaveGame* GetSave() const { return CurrentSave; }

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Save")
    bool SaveCurrent();

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Save")
    void MarkScenarioCompleted(FName ScenarioId, float SafetyScore, float OverallScore);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Career")
    bool BeginSession(ERaftSimGameMode GameMode, FName ScenarioId);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Career")
    ERaftSimMedal RecordRunResult(const FRaftSimRunResult& Result);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Career")
    void RecordTrainingDrillCompleted(FName DrillId);

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Career")
    void RecordCareerCheckpoint(FName ScenarioId, FName SectionId, float StationM, FTransform Transform);

    UFUNCTION(BlueprintPure, Category = "RaftSim|Career")
    bool IsScenarioUnlocked(FName ScenarioId, ERaftSimGameMode GameMode) const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Career")
    bool GetScenarioProgress(FName ScenarioId, FRaftSimScenarioProgress& OutProgress) const;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Career")
    bool FindBestCheckpoint(float MinimumStationM, FTransform& OutTransform) const;

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Settings")
    void RestoreDefaultSettings();

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Input")
    bool RebindAction(FName ActionId, FName KeyName);

    /** Deterministic, disk-free helpers used by migration and automation. */
    static void NormalizeSave(URaftSimVerticalSliceSaveGame* Save);
    static ERaftSimMedal ApplyRunResult(
        URaftSimVerticalSliceSaveGame* Save, const FRaftSimRunResult& Result);

private:
    static FRaftSimScenarioProgress& FindOrAddProgress(
        URaftSimVerticalSliceSaveGame* Save, FName ScenarioId);
    static void RecalculateLicenseAndUnlocks(URaftSimVerticalSliceSaveGame* Save);

    UPROPERTY()
    TObjectPtr<URaftSimVerticalSliceSaveGame> CurrentSave;
};
