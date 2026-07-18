#include "RaftSimSaveSubsystem.h"

#include "Kismet/GameplayStatics.h"
#include "RaftSimVerticalSliceFrontend.h"

const TCHAR* URaftSimSaveSubsystem::SlotName = TEXT("RaftSimVerticalSlice");

void URaftSimSaveSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);

    if (UGameplayStatics::DoesSaveGameExist(SlotName, 0))
    {
        CurrentSave = Cast<URaftSimVerticalSliceSaveGame>(
            UGameplayStatics::LoadGameFromSlot(SlotName, 0));
    }
    if (CurrentSave == nullptr)
    {
        CurrentSave = Cast<URaftSimVerticalSliceSaveGame>(
            UGameplayStatics::CreateSaveGameObject(URaftSimVerticalSliceSaveGame::StaticClass()));
    }
}

bool URaftSimSaveSubsystem::SaveCurrent()
{
    if (CurrentSave == nullptr)
    {
        return false;
    }
    return UGameplayStatics::SaveGameToSlot(CurrentSave, SlotName, 0);
}

void URaftSimSaveSubsystem::MarkScenarioCompleted(
    FName ScenarioId, float SafetyScore, float OverallScore)
{
    if (CurrentSave == nullptr)
    {
        return;
    }
    CurrentSave->CompletedScenarioIds.AddUnique(ScenarioId);
    CurrentSave->BestSafetyScore = FMath::Max(CurrentSave->BestSafetyScore, SafetyScore);
    CurrentSave->BestOverallScore = FMath::Max(CurrentSave->BestOverallScore, OverallScore);
    SaveCurrent();
}
