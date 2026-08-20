#include "RaftSimSaveSubsystem.h"

#include "Kismet/GameplayStatics.h"
#include "RaftSimVerticalSliceFrontend.h"

namespace
{
int32 MedalPoints(ERaftSimMedal Medal)
{
    switch (Medal)
    {
        case ERaftSimMedal::Bronze: return 1;
        case ERaftSimMedal::Silver: return 2;
        case ERaftSimMedal::Gold: return 3;
        default: return 0;
    }
}

void AddDefaultBinding(TMap<FName, FName>& Bindings, const TCHAR* Action, const TCHAR* Key)
{
    Bindings.FindOrAdd(FName(Action), FName(Key));
}
}

const TCHAR* URaftSimSaveSubsystem::SlotName = TEXT("RaftSimVerticalSlice");

void URaftSimSaveSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);

    const bool bExistingSlot = UGameplayStatics::DoesSaveGameExist(SlotName, 0);
    if (bExistingSlot)
    {
        CurrentSave = Cast<URaftSimVerticalSliceSaveGame>(
            UGameplayStatics::LoadGameFromSlot(SlotName, 0));
    }
    if (CurrentSave == nullptr)
    {
        CurrentSave = Cast<URaftSimVerticalSliceSaveGame>(
            UGameplayStatics::CreateSaveGameObject(URaftSimVerticalSliceSaveGame::StaticClass()));
    }
    bFreshProfileCreatedThisSession = !bExistingSlot && CurrentSave != nullptr;
    bCurrentSaveWritable = NormalizeSave(CurrentSave);
    if (bCurrentSaveWritable)
    {
        SaveCurrent();
    }
}

bool URaftSimSaveSubsystem::SaveCurrent()
{
    if (CurrentSave == nullptr || !bCurrentSaveWritable)
    {
        return false;
    }
    return UGameplayStatics::SaveGameToSlot(CurrentSave, SlotName, 0);
}

void URaftSimSaveSubsystem::MarkScenarioCompleted(
    FName ScenarioId, float SafetyScore, float OverallScore)
{
    if (CurrentSave == nullptr || !bCurrentSaveWritable)
    {
        return;
    }
    FRaftSimRunResult Result;
    Result.ScenarioId = ScenarioId;
    Result.GameMode = CurrentSave->ActiveGameMode;
    Result.SafetyScore = SafetyScore;
    Result.OverallScore = OverallScore;
    ApplyRunResult(CurrentSave, Result);
    SaveCurrent();
}

FRaftSimScenarioProgress& URaftSimSaveSubsystem::FindOrAddProgress(
    URaftSimVerticalSliceSaveGame* Save, FName ScenarioId)
{
    check(Save != nullptr);
    for (FRaftSimScenarioProgress& Progress : Save->ScenarioProgress)
    {
        if (Progress.ScenarioId == ScenarioId)
        {
            return Progress;
        }
    }
    FRaftSimScenarioProgress& Progress = Save->ScenarioProgress.AddDefaulted_GetRef();
    Progress.ScenarioId = ScenarioId;
    return Progress;
}

bool URaftSimSaveSubsystem::NormalizeSave(URaftSimVerticalSliceSaveGame* Save)
{
    if (Save == nullptr)
    {
        return false;
    }
    // Never downgrade or rewrite data authored by a newer schema. Unreal keeps
    // unknown reflected fields only while that newer build owns the file, so
    // saving it here could irreversibly discard progress.
    if (Save->SaveVersion > CurrentSaveVersion)
    {
        return false;
    }

    // Version-zero saves only had CompletedScenarioIds and two global bests.
    // Convert them without discarding fields that a future build may know.
    for (const FName& CompletedId : Save->CompletedScenarioIds)
    {
        FRaftSimScenarioProgress& Progress = FindOrAddProgress(Save, CompletedId);
        Progress.CompletionCount = FMath::Max(Progress.CompletionCount, 1);
        Progress.AttemptCount = FMath::Max(Progress.AttemptCount, 1);
        Progress.BestSafetyScore = FMath::Max(Progress.BestSafetyScore, Save->BestSafetyScore);
        Progress.BestOverallScore = FMath::Max(Progress.BestOverallScore, Save->BestOverallScore);
        Progress.BestMedal = static_cast<ERaftSimMedal>(FMath::Max(
            static_cast<int32>(Progress.BestMedal),
            static_cast<int32>(URaftSimProgressionLibrary::CalculateMedal(
                Progress.BestOverallScore, Progress.BestSafetyScore, false))));
    }

    Save->Settings.UiScale = FMath::Clamp(Save->Settings.UiScale, 0.75f, 1.5f);
    Save->Settings.TextScale = FMath::Clamp(Save->Settings.TextScale, 0.85f, 1.6f);
    Save->Settings.MotionIntensity = FMath::Clamp(Save->Settings.MotionIntensity, 0.0f, 1.0f);
    Save->Settings.CameraShakeScale = FMath::Clamp(Save->Settings.CameraShakeScale, 0.0f, 1.0f);
    Save->Settings.VignetteStrength = FMath::Clamp(Save->Settings.VignetteStrength, 0.0f, 1.0f);
    Save->Settings.MasterVolume = FMath::Clamp(Save->Settings.MasterVolume, 0.0f, 1.0f);

    AddDefaultBinding(Save->InputBindings, TEXT("Pause"), TEXT("Escape"));
    AddDefaultBinding(Save->InputBindings, TEXT("Scout"), TEXT("M"));
    AddDefaultBinding(Save->InputBindings, TEXT("CommandWheel"), TEXT("Tab"));
    AddDefaultBinding(Save->InputBindings, TEXT("PhotoMode"), TEXT("P"));
    AddDefaultBinding(Save->InputBindings, TEXT("PaddleStroke"), TEXT("W"));
    AddDefaultBinding(Save->InputBindings, TEXT("HighSide"), TEXT("SpaceBar"));
    AddDefaultBinding(Save->InputBindings, TEXT("RescueReachGrab"), TEXT("E"));
    AddDefaultBinding(Save->InputBindings, TEXT("RescueThrowLine"), TEXT("R"));
    AddDefaultBinding(Save->InputBindings, TEXT("ReseatCrew"), TEXT("F"));

    Save->SaveVersion = CurrentSaveVersion;
    RecalculateLicenseAndUnlocks(Save);
    return true;
}

void URaftSimSaveSubsystem::RecalculateLicenseAndUnlocks(URaftSimVerticalSliceSaveGame* Save)
{
    if (Save == nullptr)
    {
        return;
    }
    int32 Points = 0;
    for (const FRaftSimScenarioProgress& Progress : Save->ScenarioProgress)
    {
        Points += MedalPoints(Progress.BestMedal);
    }
    Points += Save->CompletedTrainingDrillIds.Num();
    Save->CareerXp = FMath::Max(Save->CareerXp, Points * 100);
    Save->LicenseTier = Points >= 10
        ? ERaftSimLicenseTier::ExpeditionGuide
        : Points >= 6
            ? ERaftSimLicenseTier::SeniorGuide
            : Points >= 2
                ? ERaftSimLicenseTier::TripLeader
                : ERaftSimLicenseTier::Trainee;

    // Guide license is retained as career rank/progression feedback, but it no
    // longer gates playable content. Every shipped scenario is available on a
    // fresh or migrated profile; medals and XP describe accomplishment rather
    // than withholding river access.
    Save->UnlockedScenarioIds.Reset();
    for (const FRaftSimCareerScenarioDefinition& Scenario : URaftSimProgressionLibrary::GetScenarioCatalog())
    {
        Save->UnlockedScenarioIds.AddUnique(Scenario.ScenarioId);
    }
}

ERaftSimMedal URaftSimSaveSubsystem::ApplyRunResult(
    URaftSimVerticalSliceSaveGame* Save, const FRaftSimRunResult& Result)
{
    if (Save == nullptr || Result.ScenarioId.IsNone())
    {
        return ERaftSimMedal::None;
    }
    FRaftSimScenarioProgress& Progress = FindOrAddProgress(Save, Result.ScenarioId);
    const bool bNewBestRoute = Result.OverallScore >= Progress.BestOverallScore;
    ++Progress.AttemptCount;
    Progress.FurthestStationM = FMath::Max(Progress.FurthestStationM, Result.FurthestStationM);
    Save->CareerStats.TotalRuns++;
    Save->CareerStats.TotalSwims += FMath::Max(0, Result.SwimCount);
    Save->CareerStats.TotalGuideTimeSeconds += FMath::Max(0.0f, Result.RunTimeSeconds);
    Save->CareerStats.LongestDescentStationM = FMath::Max(
        Save->CareerStats.LongestDescentStationM, Result.FurthestStationM);

    const ERaftSimMedal Medal = URaftSimProgressionLibrary::CalculateMedal(
        Result.OverallScore, Result.SafetyScore, Result.bAssistUsed);
    if (Result.OverallScore > 0.0f)
    {
        ++Progress.CompletionCount;
        ++Save->CareerStats.CompletedRuns;
        if (Result.SafetyIncidentCount == 0 && Result.SwimCount == 0)
        {
            ++Save->CareerStats.CleanRuns;
        }
        Save->CompletedScenarioIds.AddUnique(Result.ScenarioId);
    }
    if (Result.GameMode == ERaftSimGameMode::GuidedDescent)
    {
        Progress.BestMedal = static_cast<ERaftSimMedal>(FMath::Max(
            static_cast<int32>(Progress.BestMedal), static_cast<int32>(Medal)));
    }
    Progress.BestSafetyScore = FMath::Max(Progress.BestSafetyScore, Result.SafetyScore);
    Progress.BestOverallScore = FMath::Max(Progress.BestOverallScore, Result.OverallScore);
    if (bNewBestRoute && Result.GhostRoute.Num() >= 2)
    {
        Progress.BestGhostRoute = Result.GhostRoute;
    }
    if (Result.RunTimeSeconds > 0.0f &&
        (Progress.BestTimeSeconds <= 0.0f || Result.RunTimeSeconds < Progress.BestTimeSeconds))
    {
        Progress.BestTimeSeconds = Result.RunTimeSeconds;
    }
    Save->BestSafetyScore = FMath::Max(Save->BestSafetyScore, Result.SafetyScore);
    Save->BestOverallScore = FMath::Max(Save->BestOverallScore, Result.OverallScore);
    RecalculateLicenseAndUnlocks(Save);
    return Medal;
}

bool URaftSimSaveSubsystem::BeginSession(ERaftSimGameMode GameMode, FName ScenarioId)
{
    if (CurrentSave == nullptr || !bCurrentSaveWritable || !IsScenarioUnlocked(ScenarioId, GameMode))
    {
        return false;
    }
    FRaftSimCareerScenarioDefinition Scenario;
    if (!URaftSimProgressionLibrary::FindScenario(ScenarioId, Scenario))
    {
        return false;
    }
    CurrentSave->ActiveGameMode = GameMode;
    CurrentSave->Selection.ScenarioId = ScenarioId;
    return SaveCurrent();
}

ERaftSimMedal URaftSimSaveSubsystem::RecordRunResult(const FRaftSimRunResult& Result)
{
    if (!bCurrentSaveWritable)
    {
        return ERaftSimMedal::None;
    }
    const ERaftSimMedal Medal = ApplyRunResult(CurrentSave, Result);
    SaveCurrent();
    return Medal;
}

void URaftSimSaveSubsystem::RecordTrainingDrillCompleted(FName DrillId)
{
    if (CurrentSave == nullptr || !bCurrentSaveWritable || DrillId.IsNone())
    {
        return;
    }
    CurrentSave->CompletedTrainingDrillIds.AddUnique(DrillId);
    RecalculateLicenseAndUnlocks(CurrentSave);
    SaveCurrent();
}

void URaftSimSaveSubsystem::RecordCareerCheckpoint(
    FName ScenarioId, FName SectionId, float StationM, FTransform Transform)
{
    if (CurrentSave == nullptr || !bCurrentSaveWritable || ScenarioId.IsNone() || !Transform.IsValid())
    {
        return;
    }
    FRaftSimScenarioProgress& Progress = FindOrAddProgress(CurrentSave, ScenarioId);
    if (!Progress.bHasCheckpoint || StationM >= Progress.FurthestStationM)
    {
        Progress.FurthestStationM = StationM;
        Progress.CheckpointTransform = Transform;
        Progress.bHasCheckpoint = true;
    }
    if (!SectionId.IsNone())
    {
        CurrentSave->CompletedCareerSectionIds.AddUnique(SectionId);
    }
    SaveCurrent();
}

bool URaftSimSaveSubsystem::IsScenarioUnlocked(FName ScenarioId, ERaftSimGameMode GameMode) const
{
    if (CurrentSave == nullptr)
    {
        return false;
    }
    FRaftSimCareerScenarioDefinition Scenario;
    if (!URaftSimProgressionLibrary::FindScenario(ScenarioId, Scenario))
    {
        return false;
    }
    if (GameMode == ERaftSimGameMode::TrainingEddy)
    {
        return Scenario.bTraining;
    }
    // Guided Descent and Free Run expose every valid catalog entry. License
    // tier remains a visible career rank only and never disables Start.
    return true;
}

bool URaftSimSaveSubsystem::GetScenarioProgress(
    FName ScenarioId, FRaftSimScenarioProgress& OutProgress) const
{
    if (CurrentSave == nullptr)
    {
        return false;
    }
    for (const FRaftSimScenarioProgress& Progress : CurrentSave->ScenarioProgress)
    {
        if (Progress.ScenarioId == ScenarioId)
        {
            OutProgress = Progress;
            return true;
        }
    }
    return false;
}

bool URaftSimSaveSubsystem::FindBestCheckpoint(
    float MinimumStationM, FTransform& OutTransform) const
{
    if (CurrentSave == nullptr)
    {
        return false;
    }
    const FRaftSimScenarioProgress* Best = nullptr;
    for (const FRaftSimScenarioProgress& Progress : CurrentSave->ScenarioProgress)
    {
        if (Progress.bHasCheckpoint && Progress.FurthestStationM >= MinimumStationM &&
            (Best == nullptr || Progress.FurthestStationM < Best->FurthestStationM))
        {
            Best = &Progress;
        }
    }
    if (Best == nullptr)
    {
        return false;
    }
    OutTransform = Best->CheckpointTransform;
    return OutTransform.IsValid();
}

void URaftSimSaveSubsystem::RestoreDefaultSettings()
{
    if (CurrentSave == nullptr || !bCurrentSaveWritable)
    {
        return;
    }
    CurrentSave->Settings = FRaftSimVerticalSliceUserSettings{};
    NormalizeSave(CurrentSave);
    SaveCurrent();
}

bool URaftSimSaveSubsystem::RebindAction(FName ActionId, FName KeyName)
{
    if (CurrentSave == nullptr || !bCurrentSaveWritable || ActionId.IsNone() || KeyName.IsNone())
    {
        return false;
    }
    CurrentSave->InputBindings.FindOrAdd(ActionId) = KeyName;
    return SaveCurrent();
}
