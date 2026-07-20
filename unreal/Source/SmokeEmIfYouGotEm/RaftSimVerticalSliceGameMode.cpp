#include "RaftSimVerticalSliceGameMode.h"

#include "EngineUtils.h"
#include "RaftSimGuidePawn.h"
#include "RaftSimGuidePlayerController.h"
#include "RaftSimContentLockDirector.h"
#include "RaftSimPresentationDirector.h"
#include "RaftSimRunAudioDirector.h"
#include "RaftSimRunManager.h"
#include "RaftSimSaveSubsystem.h"
#include "RaftSimTrainingDirector.h"
#include "RaftSimVerticalSliceFrontend.h"

ARaftSimVerticalSliceGameMode::ARaftSimVerticalSliceGameMode()
{
    DefaultPawnClass = ARaftSimGuidePawn::StaticClass();
    PlayerControllerClass = ARaftSimGuidePlayerController::StaticClass();
    InitializeScenarioDefinitions();
}

void ARaftSimVerticalSliceGameMode::BeginPlay()
{
    Super::BeginPlay();

    if (ARaftSimContentLockDirector::IsPackagedRegressionRequested())
    {
        GetWorld()->SpawnActor<ARaftSimContentLockDirector>(
            ARaftSimContentLockDirector::StaticClass(), FTransform::Identity);
        return;
    }

    ERaftSimGameMode SessionMode = ERaftSimGameMode::FreeRun;
    FRaftSimCareerScenarioDefinition SessionScenario;
    bool bHasSessionScenario = false;
    if (URaftSimSaveSubsystem* Save = GetGameInstance()
            ? GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>() : nullptr)
    {
        if (Save->GetSave() != nullptr)
        {
            SessionMode = Save->GetSave()->ActiveGameMode;
            ActiveScenarioId = Save->GetSave()->Selection.ScenarioId;
            bHasSessionScenario = URaftSimProgressionLibrary::FindScenario(
                ActiveScenarioId, SessionScenario);
        }
    }

    // Ensure a run manager exists so any rapid/tank map is scored.
    bool bHasRunManager = false;
    ARaftSimRunManager* RunManager = nullptr;
    if (TActorIterator<ARaftSimRunManager> It(GetWorld()); It)
    {
        bHasRunManager = true;
        RunManager = *It;
    }
    if (!bHasRunManager)
    {
        ARaftSimRunManager* Manager = GetWorld()->SpawnActor<ARaftSimRunManager>(
            ARaftSimRunManager::StaticClass(), FTransform::Identity);
        if (Manager != nullptr)
        {
            Manager->ScenarioId = ActiveScenarioId;
            RunManager = Manager;
        }
    }
    if (RunManager != nullptr && bHasSessionScenario)
    {
        RunManager->ConfigureSession(SessionScenario, SessionMode);
    }

    if (SessionMode == ERaftSimGameMode::TrainingEddy)
    {
        bool bHasTrainingDirector = false;
        if (TActorIterator<ARaftSimTrainingDirector> It(GetWorld()); It)
        {
            bHasTrainingDirector = true;
        }
        if (!bHasTrainingDirector)
        {
            GetWorld()->SpawnActor<ARaftSimTrainingDirector>(
                ARaftSimTrainingDirector::StaticClass(), FTransform::Identity);
        }
    }

    // Deterministic weather/time presentation precedes the audio director so
    // the initial canyon/weather mix is valid on its first frame.
    bool bHasPresentation = false;
    if (TActorIterator<ARaftSimPresentationDirector> It(GetWorld()); It)
    {
        bHasPresentation = true;
    }
    if (!bHasPresentation)
    {
        GetWorld()->SpawnActor<ARaftSimPresentationDirector>(
            ARaftSimPresentationDirector::StaticClass(), FTransform::Identity);
    }

    // Layered production river/raft/crew/music audio director.
    bool bHasAudio = false;
    if (TActorIterator<ARaftSimRunAudioDirector> It(GetWorld()); It)
    {
        bHasAudio = true;
    }
    if (!bHasAudio)
    {
        GetWorld()->SpawnActor<ARaftSimRunAudioDirector>(
            ARaftSimRunAudioDirector::StaticClass(), FTransform::Identity);
    }

    if (ARaftSimContentLockDirector::IsPerformanceCaptureRequested())
    {
        GetWorld()->SpawnActor<ARaftSimContentLockDirector>(
            ARaftSimContentLockDirector::StaticClass(), FTransform::Identity);
    }
}

void ARaftSimVerticalSliceGameMode::RestartRapid()
{
    CurrentScore = FRaftSimRapidScoreBreakdown();
    AfterActionFeedback.Reset();
    ReplayFrame = 0;
    bRapidComplete = false;
}

bool ARaftSimVerticalSliceGameMode::SetActiveScenario(FName ScenarioId)
{
    for (const FRaftSimVerticalSliceScenarioDefinition& Scenario : ScenarioDefinitions)
    {
        if (Scenario.ScenarioId == ScenarioId)
        {
            ActiveScenarioId = ScenarioId;
            RestartRapid();
            return true;
        }
    }
    return false;
}

void ARaftSimVerticalSliceGameMode::CompleteRapid(
    const FRaftSimRapidScoreBreakdown& FinalScore,
    const TArray<FString>& FeedbackNotes
)
{
    CurrentScore = FinalScore;
    AfterActionFeedback = FeedbackNotes;
    bRapidComplete = true;
}

void ARaftSimVerticalSliceGameMode::SetReplayEnabled(bool bInReplayEnabled)
{
    bReplayEnabled = bInReplayEnabled;
}

void ARaftSimVerticalSliceGameMode::SetDebugForceVisualizationEnabled(bool bInEnabled)
{
    bDebugForceVisualizationEnabled = bInEnabled;
}

void ARaftSimVerticalSliceGameMode::InitializeScenarioDefinitions()
{
    FRaftSimVerticalSliceScenarioDefinition TrainingScenario;
    TrainingScenario.ScenarioId = TEXT("training_eddy_turn_intro");
    TrainingScenario.ScenarioKind = ERaftSimVerticalSliceScenarioKind::TrainingSection;
    TrainingScenario.DisplayName = TEXT("Training Eddy Turn Intro");
    TrainingScenario.FlowBand = TEXT("low_runnable");
    TrainingScenario.DifficultyPreset = TEXT("beginner");
    TrainingScenario.RequiredObjectives = {
        TEXT("forward_paddle_timing"),
        TEXT("brace_on_wave"),
        TEXT("hold_on_before_lateral"),
        TEXT("catch_recovery_eddy"),
        TEXT("quick_restart"),
        TEXT("after_action_feedback")
    };
    ScenarioDefinitions.Add(TrainingScenario);

    FRaftSimVerticalSliceScenarioDefinition TechnicalRapid;
    TechnicalRapid.ScenarioId = TEXT("first_technical_constriction_wave_train");
    TechnicalRapid.ScenarioKind = ERaftSimVerticalSliceScenarioKind::TechnicalRapid;
    TechnicalRapid.DisplayName = TEXT("First Technical Constriction Wave Train");
    TechnicalRapid.FlowBand = TEXT("median_runnable");
    TechnicalRapid.DifficultyPreset = TEXT("intermediate");
    TechnicalRapid.RequiredObjectives = {
        TEXT("read_entry_tongue"),
        TEXT("hold_boat_angle"),
        TEXT("manual_or_voice_crew_commands"),
        TEXT("brace_or_high_side_counterplay"),
        TEXT("recover_swimmer_if_ejected"),
        TEXT("score_and_replay_review")
    };
    ScenarioDefinitions.Add(TechnicalRapid);

    ActiveScenarioId = TrainingScenario.ScenarioId;
}
