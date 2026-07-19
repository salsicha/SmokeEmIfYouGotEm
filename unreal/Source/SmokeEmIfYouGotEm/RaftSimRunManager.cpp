#include "RaftSimRunManager.h"

#include "Components/BoxComponent.h"
#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "RaftSimEncounterVolume.h"
#include "RaftSimRaftActor.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRiverWaterConfig.h"
#include "RaftSimRouteGhostActor.h"
#include "RaftSimSaveSubsystem.h"
#include "RaftSimWaterRuntimeAdapter.h"

ARaftSimRunManager::ARaftSimRunManager()
{
    PrimaryActorTick.bCanEverTick = true;
}

void ARaftSimRunManager::BeginPlay()
{
    Super::BeginPlay();

    if (TActorIterator<ARaftSimRaftActor> It(GetWorld()); It)
    {
        Raft = *It;
    }
    for (TActorIterator<ARaftSimEncounterVolume> It(GetWorld()); It; ++It)
    {
        Volumes.Add(*It);
    }
    if (Raft != nullptr)
    {
        LastSwimmerCount = Raft->GetSwimmerCount();
    }

    if (URaftSimSaveSubsystem* Save = GetGameInstance()
            ? GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>() : nullptr)
    {
        if (Save->GetSave() != nullptr)
        {
            FRaftSimCareerScenarioDefinition Scenario;
            if (URaftSimProgressionLibrary::FindScenario(
                    Save->GetSave()->Selection.ScenarioId, Scenario))
            {
                ConfigureSession(Scenario, Save->GetSave()->ActiveGameMode);
            }
            FRaftSimScenarioProgress Progress;
            if (Save->GetScenarioProgress(ScenarioId, Progress))
            {
                BestGhostRoute = Progress.BestGhostRoute;
            }
            const FRaftSimVerticalSliceUserSettings& Settings = Save->GetSave()->Settings;
            bAssistUsed = Settings.AssistLevel != ERaftSimAssistLevel::Authentic ||
                Settings.bRouteAssistEnabled;
            if (Settings.bGhostEnabled && BestGhostRoute.Num() >= 2)
            {
                if (ARaftSimRouteGhostActor* Ghost = GetWorld()->SpawnActor<ARaftSimRouteGhostActor>(
                        ARaftSimRouteGhostActor::StaticClass(), FTransform::Identity))
                {
                    Ghost->SetRoute(BestGhostRoute);
                }
            }
        }
    }
}

void ARaftSimRunManager::ConfigureSession(
    const FRaftSimCareerScenarioDefinition& Scenario, ERaftSimGameMode InGameMode)
{
    ScenarioId = Scenario.ScenarioId;
    GameModeKind = InGameMode;
    StartStationM = Scenario.StartStationM;
    FinishStationM = Scenario.FinishStationM;
    bCheckpointRestorePending = StartStationM > 200.0f && !Scenario.bFullDescent;
}

float ARaftSimRunManager::GetProgressFraction() const
{
    if (StartStationM >= 0.0f && FinishStationM > StartStationM)
    {
        return FMath::Clamp(
            (CurrentStationM - StartStationM) / (FinishStationM - StartStationM),
            0.0f, 1.0f);
    }
    if (FinishLineX > StartLineX && Raft != nullptr)
    {
        return FMath::Clamp(
            (Raft->GetActorLocation().X - StartLineX) / (FinishLineX - StartLineX),
            0.0f, 1.0f);
    }
    return 0.0f;
}

bool ARaftSimRunManager::SampleRiverStation(float& OutStationM, FVector* OutTangent) const
{
    if (Raft == nullptr || GetGameInstance() == nullptr)
    {
        return false;
    }
    const URaftSimPhysicsBridgeSubsystem* Bridge =
        GetGameInstance()->GetSubsystem<URaftSimPhysicsBridgeSubsystem>();
    const URaftSimWaterRuntimeAdapter* Water = Bridge ? Bridge->GetWaterRuntime() : nullptr;
    if (Water == nullptr || !Water->HasRiverCoordinateMap())
    {
        return false;
    }
    FVector2D StationLateral;
    FVector Tangent;
    FVector Left;
    if (!Water->WorldToRiverCoordinates(Raft->GetActorLocation(), StationLateral, Tangent, Left))
    {
        return false;
    }
    OutStationM = StationLateral.X;
    if (OutTangent != nullptr)
    {
        *OutTangent = Tangent;
    }
    return FMath::IsFinite(OutStationM);
}

void ARaftSimRunManager::TryRestoreSessionCheckpoint()
{
    if (!bCheckpointRestorePending || bCheckpointRestoreAttempted || Raft == nullptr)
    {
        return;
    }
    URaftSimSaveSubsystem* Save = GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>();
    URaftSimPhysicsBridgeSubsystem* Bridge =
        GetGameInstance()->GetSubsystem<URaftSimPhysicsBridgeSubsystem>();
    URaftSimWaterRuntimeAdapter* Water = Bridge ? Bridge->GetWaterRuntime() : nullptr;
    if (Save == nullptr || Water == nullptr || !Water->HasRiverCoordinateMap())
    {
        return;
    }
    bCheckpointRestoreAttempted = true;
    FTransform Checkpoint;
    if (!Save->FindBestCheckpoint(StartStationM - 25.0f, Checkpoint))
    {
        bCheckpointRestorePending = false;
        return;
    }
    // A resumed section is an intentional discontinuity. Seed a fresh live
    // window at its saved station before moving the authoritative raft body;
    // normal downstream handoffs remain overlap-preserving after this point.
    if (TActorIterator<ARaftSimRiverWaterConfig> It(GetWorld()); It)
    {
        ARaftSimRiverWaterConfig* Config = *It;
        Water->ConfigureRiverWindow(
            Config->CookedFieldsDir, Config->FlowBand.ToString(),
            FVector2D(StartStationM, 0.0f),
            FVector2D(Config->MovingWindowStationExtentM, Config->MovingWindowLateralExtentM),
            0.041f);
    }
    Raft->SetCheckpointTransform(Checkpoint, true);
    CurrentStationM = StartStationM;
    FurthestStationM = StartStationM;
    LastCheckpointStationM = StartStationM;
    bCheckpointRestorePending = false;
}

void ARaftSimRunManager::StartRun()
{
    RunState = ERaftSimRunState::Running;
    RunTimeSeconds = 0.0f;
    SafetyIncidents = 0;
    SwimCount = 0;
    AngleErrorAccumDeg = 0.0f;
    AngleSampleSeconds = 0.0f;
    CurrentGhostRoute.Reset();
    GhostSampleRemaining = 0.0f;
    if (Raft != nullptr)
    {
        LastSwimmerCount = Raft->GetSwimmerCount();
    }
}

void ARaftSimRunManager::AccumulateSignals(float DeltaSeconds)
{
    if (Raft == nullptr)
    {
        return;
    }

    // A fresh batch of swimmers = a swim/flip incident.
    const int32 Swimmers = Raft->GetSwimmerCount();
    if (Swimmers > LastSwimmerCount)
    {
        ++SwimCount;
        ++SafetyIncidents;
    }
    LastSwimmerCount = Swimmers;

    // Boat-angle error uses the curved river tangent when available.
    const float Yaw = Raft->GetActorRotation().Yaw;
    FVector RiverTangent;
    float Station = CurrentStationM;
    const float DownstreamYaw = SampleRiverStation(Station, &RiverTangent)
        ? RiverTangent.Rotation().Yaw : 0.0f;
    float AngleErr = FMath::Abs(FMath::FindDeltaAngleDegrees(Yaw, DownstreamYaw));
    AngleErrorAccumDeg += AngleErr * DeltaSeconds;
    AngleSampleSeconds += DeltaSeconds;

    GhostSampleRemaining -= DeltaSeconds;
    if (GhostSampleRemaining <= 0.0f)
    {
        if (CurrentGhostRoute.IsEmpty() ||
            FVector::DistSquared(CurrentGhostRoute.Last(), Raft->GetActorLocation()) > FMath::Square(2500.0f))
        {
            CurrentGhostRoute.Add(Raft->GetActorLocation());
        }
        GhostSampleRemaining = 1.0f;
    }

    // Hazard overlaps (off the clean line) count as incidents, throttled by
    // being inside the volume — counted once per entry via overlap state.
    for (const TObjectPtr<ARaftSimEncounterVolume>& Volume : Volumes)
    {
        if (Volume == nullptr || Volume->Kind != ERaftSimEncounterKind::Hazard)
        {
            continue;
        }
        if (Volume->GetTrigger()->IsOverlappingActor(Raft))
        {
            // Only count the transition into a hazard, tracked by a tag.
            const FName Tag(*FString::Printf(TEXT("InHazard_%s"), *Volume->GetName()));
            if (!Raft->Tags.Contains(Tag))
            {
                Raft->Tags.Add(Tag);
                ++SafetyIncidents;
            }
        }
    }
}

void ARaftSimRunManager::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (Raft == nullptr)
    {
        return;
    }

    TryRestoreSessionCheckpoint();

    float SampledStation = CurrentStationM;
    const bool bHasStation = SampleRiverStation(SampledStation);
    if (bHasStation)
    {
        CurrentStationM = SampledStation;
        FurthestStationM = FMath::Max(FurthestStationM, CurrentStationM);
    }

    const float RaftX = Raft->GetActorLocation().X;

    if (RunState == ERaftSimRunState::Ready)
    {
        // Start once the raft leaves the scout eddy / passes the start line.
        const bool bCrossedStart = StartStationM >= 0.0f && bHasStation
            ? CurrentStationM >= StartStationM - 10.0f
            : RaftX >= StartLineX;
        if (bCrossedStart)
        {
            StartRun();
        }
        return;
    }

    if (RunState == ERaftSimRunState::Running)
    {
        RunTimeSeconds += DeltaSeconds;
        AccumulateSignals(DeltaSeconds);
        RecordCheckpointIfNeeded();

        // Finish at the Finish volume if present, else the fallback line.
        bool bFinished = FinishStationM >= 0.0f && bHasStation
            ? CurrentStationM >= FinishStationM
            : RaftX >= FinishLineX;
        for (const TObjectPtr<ARaftSimEncounterVolume>& Volume : Volumes)
        {
            if (Volume != nullptr && Volume->Kind == ERaftSimEncounterKind::Finish &&
                Volume->GetTrigger()->IsOverlappingActor(Raft))
            {
                bFinished = true;
            }
        }
        if (bFinished)
        {
            FinishRun();
        }
    }
}

void ARaftSimRunManager::RecordCheckpointIfNeeded()
{
    if (GameModeKind != ERaftSimGameMode::GuidedDescent || StartStationM < 0.0f ||
        CurrentStationM < LastCheckpointStationM + 1000.0f || Raft == nullptr)
    {
        return;
    }
    LastCheckpointStationM = CurrentStationM;
    Raft->SetCheckpointTransform(Raft->GetActorTransform(), false);
    if (URaftSimSaveSubsystem* Save = GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>())
    {
        Save->RecordCareerCheckpoint(
            ScenarioId,
            FName(*FString::Printf(TEXT("%s_%05d"), *ScenarioId.ToString(),
                FMath::RoundToInt(CurrentStationM))),
            CurrentStationM, Raft->GetActorTransform());
    }
}

void ARaftSimRunManager::RestartRun()
{
    if (Raft != nullptr)
    {
        Raft->ResetToCheckpoint();
    }
    RunState = ERaftSimRunState::Ready;
    FinalScore = FRaftSimGameplayScoreBreakdown{};
    AwardedMedal = ERaftSimMedal::None;
    AfterActionSummary = FText::GetEmpty();
}

void ARaftSimRunManager::FinishRun()
{
    RunState = ERaftSimRunState::Finished;

    FRaftSimGameplayScoringSignals Signals;
    Signals.SafetyIncidentCount = SafetyIncidents;
    Signals.SwimCount = SwimCount;
    Signals.CleanLineRatio = (SafetyIncidents == 0) ? 1.0f : FMath::Max(0.0f, 1.0f - 0.2f * SafetyIncidents);
    Signals.MeanBoatAngleErrorDegrees =
        AngleSampleSeconds > 0.0f ? AngleErrorAccumDeg / AngleSampleSeconds : 0.0f;
    Signals.RescueMethod =
        (SwimCount > 0) ? ERaftSimRescueMethod::ThrowLine : ERaftSimRescueMethod::None;

    FinalScore = URaftSimGameplayScoringLibrary::EvaluateGameplayScore(Signals);

    if (const UGameInstance* GameInstance = GetGameInstance())
    {
        if (URaftSimSaveSubsystem* Save = GameInstance->GetSubsystem<URaftSimSaveSubsystem>())
        {
            FRaftSimRunResult Result;
            Result.ScenarioId = ScenarioId;
            Result.GameMode = GameModeKind;
            Result.SafetyScore = FinalScore.SafetyScore;
            Result.OverallScore = FinalScore.TotalScore;
            Result.RunTimeSeconds = RunTimeSeconds;
            Result.SafetyIncidentCount = SafetyIncidents;
            Result.SwimCount = SwimCount;
            Result.FurthestStationM = FurthestStationM;
            Result.bAssistUsed = bAssistUsed;
            Result.GhostRoute = CurrentGhostRoute;
            AwardedMedal = Save->RecordRunResult(Result);
        }
    }
    AfterActionSummary = FText::Format(
        NSLOCTEXT("RaftSim", "AfterActionSummary",
            "{0} — score {1}, safety {2}, line {3}, angle {4}; {5} incident(s), {6} swim(s), {7}s"),
        URaftSimProgressionLibrary::MedalDisplayName(AwardedMedal),
        FText::AsNumber(FMath::RoundToInt(FinalScore.TotalScore * 100.0f)),
        FText::AsNumber(FMath::RoundToInt(FinalScore.SafetyScore * 100.0f)),
        FText::AsNumber(FMath::RoundToInt(FinalScore.LineChoiceScore * 100.0f)),
        FText::AsNumber(FMath::RoundToInt(FinalScore.BoatAngleScore * 100.0f)),
        FText::AsNumber(SafetyIncidents), FText::AsNumber(SwimCount),
        FText::AsNumber(FMath::RoundToInt(RunTimeSeconds)));
}
