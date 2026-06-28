#include "RaftSimVerticalSliceGameMode.h"

#include "RaftSimGuidePawn.h"

ARaftSimVerticalSliceGameMode::ARaftSimVerticalSliceGameMode()
{
    DefaultPawnClass = ARaftSimGuidePawn::StaticClass();
}

void ARaftSimVerticalSliceGameMode::RestartRapid()
{
    CurrentScore = FRaftSimRapidScoreBreakdown();
}

void ARaftSimVerticalSliceGameMode::SetReplayEnabled(bool bInReplayEnabled)
{
    bReplayEnabled = bInReplayEnabled;
}

void ARaftSimVerticalSliceGameMode::SetDebugForceVisualizationEnabled(bool bInEnabled)
{
    bDebugForceVisualizationEnabled = bInEnabled;
}
