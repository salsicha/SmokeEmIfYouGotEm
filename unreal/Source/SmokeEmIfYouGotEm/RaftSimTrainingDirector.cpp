#include "RaftSimTrainingDirector.h"

#include "EngineUtils.h"
#include "RaftSimRaftActor.h"
#include "RaftSimSaveSubsystem.h"
#include "RaftSimVerticalSliceFrontend.h"

ARaftSimTrainingDirector::ARaftSimTrainingDirector()
{
    PrimaryActorTick.bCanEverTick = true;
    DrillIds = {
        TEXT("forward_stop_and_brace"),
        TEXT("eddy_scout_and_high_side"),
        TEXT("swimmer_recovery")
    };
}

void ARaftSimTrainingDirector::BeginPlay()
{
    Super::BeginPlay();
    const URaftSimSaveSubsystem* Save = GetGameInstance()
        ? GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>() : nullptr;
    if (Save == nullptr || Save->GetSave() == nullptr ||
        Save->GetSave()->ActiveGameMode != ERaftSimGameMode::TrainingEddy)
    {
        SetActorTickEnabled(false);
        return;
    }
    if (TActorIterator<ARaftSimRaftActor> It(GetWorld()); It)
    {
        Raft = *It;
    }
    State = ERaftSimTrainingState::Briefing;
    TransitionRemaining = 1.0f;
}

FName ARaftSimTrainingDirector::GetCurrentDrillId() const
{
    return DrillIds.IsValidIndex(CurrentDrillIndex) ? DrillIds[CurrentDrillIndex] : NAME_None;
}

FText ARaftSimTrainingDirector::GetCurrentPrompt() const
{
    if (State == ERaftSimTrainingState::CourseComplete)
    {
        return NSLOCTEXT("RaftSim", "TrainingComplete", "Guide School complete. Trip Leader career runs are unlocked.");
    }
    if (!DrillIds.IsValidIndex(CurrentDrillIndex))
    {
        return FText::GetEmpty();
    }
    switch (CurrentDrillIndex)
    {
        case 0:
            return NSLOCTEXT("RaftSim", "TrainingCalls", "Paddle once, call ALL FORWARD, then STOP. Use the command wheel or hotkeys.");
        case 1:
            return NSLOCTEXT("RaftSim", "TrainingScout", "Open the scout board, issue a LEFT/RIGHT turn, then high-side with Space / gamepad shoulder.");
        default:
            return NSLOCTEXT("RaftSim", "TrainingRescue", "Recover the swimmer: select, reach or throw, pull to the tube, then reseat.");
    }
}

void ARaftSimTrainingDirector::BeginCurrentDrill()
{
    if (Raft == nullptr || !DrillIds.IsValidIndex(CurrentDrillIndex))
    {
        return;
    }
    State = ERaftSimTrainingState::Practicing;
    InitialPaddleCount = Raft->GetPaddleStrokeCount();
    InitialHighSideCount = Raft->GetHighSideResponseCount();
    InitialRescueCount = Raft->GetCompletedRescueCount();
    if (CurrentDrillIndex == 2 && !bRescueDrillSpawned)
    {
        Raft->ForceCrewOverboardForTesting(1);
        bRescueDrillSpawned = true;
    }
}

void ARaftSimTrainingDirector::CompleteCurrentDrill()
{
    if (!DrillIds.IsValidIndex(CurrentDrillIndex))
    {
        return;
    }
    if (URaftSimSaveSubsystem* Save = GetGameInstance()->GetSubsystem<URaftSimSaveSubsystem>())
    {
        Save->RecordTrainingDrillCompleted(DrillIds[CurrentDrillIndex]);
    }
    ++CurrentDrillIndex;
    if (CurrentDrillIndex >= DrillIds.Num())
    {
        State = ERaftSimTrainingState::CourseComplete;
        return;
    }
    State = ERaftSimTrainingState::DrillComplete;
    TransitionRemaining = 1.5f;
}

void ARaftSimTrainingDirector::NotifyScoutReviewed()
{
    bScoutReviewed = true;
}

void ARaftSimTrainingDirector::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (Raft == nullptr)
    {
        if (TActorIterator<ARaftSimRaftActor> It(GetWorld()); It)
        {
            Raft = *It;
        }
        return;
    }
    if (State == ERaftSimTrainingState::Briefing || State == ERaftSimTrainingState::DrillComplete)
    {
        TransitionRemaining -= DeltaSeconds;
        if (TransitionRemaining <= 0.0f)
        {
            BeginCurrentDrill();
        }
        return;
    }
    if (State != ERaftSimTrainingState::Practicing)
    {
        return;
    }

    if (CurrentDrillIndex == 0)
    {
        bSawPaddle |= Raft->GetPaddleStrokeCount() > InitialPaddleCount;
        bSawForward |= Raft->GetActiveCrewCommand() == ERaftSimCrewCommand::AllForward;
        bSawStopAfterForward |= bSawForward && Raft->GetActiveCrewCommand() == ERaftSimCrewCommand::Stop;
        if (bSawPaddle && bSawForward && bSawStopAfterForward)
        {
            CompleteCurrentDrill();
        }
    }
    else if (CurrentDrillIndex == 1)
    {
        const ERaftSimCrewCommand Command = Raft->GetActiveCrewCommand();
        bSawTurn |= Command == ERaftSimCrewCommand::TurnLeft || Command == ERaftSimCrewCommand::TurnRight;
        if (bScoutReviewed && bSawTurn && Raft->GetHighSideResponseCount() > InitialHighSideCount)
        {
            CompleteCurrentDrill();
        }
    }
    else if (Raft->GetCompletedRescueCount() > InitialRescueCount)
    {
        CompleteCurrentDrill();
    }
}
