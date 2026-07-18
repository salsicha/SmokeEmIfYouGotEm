#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"

#include "RaftSimSaveSubsystem.generated.h"

class URaftSimVerticalSliceSaveGame;

/** Loads the single save slot at startup and persists it on demand. */
UCLASS()
class RAFTSIMUI_API URaftSimSaveSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    static const TCHAR* SlotName;

    virtual void Initialize(FSubsystemCollectionBase& Collection) override;

    UFUNCTION(BlueprintPure, Category = "RaftSim|Save")
    URaftSimVerticalSliceSaveGame* GetSave() const { return CurrentSave; }

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Save")
    bool SaveCurrent();

    UFUNCTION(BlueprintCallable, Category = "RaftSim|Save")
    void MarkScenarioCompleted(FName ScenarioId, float SafetyScore, float OverallScore);

private:
    UPROPERTY()
    TObjectPtr<URaftSimVerticalSliceSaveGame> CurrentSave;
};
