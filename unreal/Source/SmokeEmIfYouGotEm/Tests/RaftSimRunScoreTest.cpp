// P3 test: a scored run starts, the raft paddles across the finish line, a
// score is computed, and the best score is persisted to the save game.

#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "RaftSimRaftActor.h"
#include "../RaftSimRunManager.h"
#include "RaftSimSaveSubsystem.h"
#include "RaftSimVerticalSliceFrontend.h"
#include "Tests/AutomationCommon.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimRunScoresAndSavesTest,
    "RaftSim.P3.RunScoresAndSaves",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

namespace
{

UWorld* GetRunTestWorld()
{
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
    {
        if (Context.World() != nullptr &&
            (Context.WorldType == EWorldType::PIE || Context.WorldType == EWorldType::Game))
        {
            return Context.World();
        }
    }
    return nullptr;
}

template <typename T>
T* FindOne(UWorld* World)
{
    if (World == nullptr)
    {
        return nullptr;
    }
    if (TActorIterator<T> It(World); It)
    {
        return *It;
    }
    return nullptr;
}

// Configure a short finish line so the run completes in bounded paddling time.
DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimConfigureRunCommand, FAutomationTestBase*, Test);
bool FRaftSimConfigureRunCommand::Update()
{
    ARaftSimRunManager* Run = FindOne<ARaftSimRunManager>(GetRunTestWorld());
    if (Run == nullptr)
    {
        Test->AddError(TEXT("No run manager spawned by the game mode"));
        return true;
    }
    Run->ScenarioId = TEXT("test_tank_run");
    Run->StartLineX = -100000.0f;  // already started
    Run->FinishLineX = 400.0f;     // 4 m downstream
    return true;
}

// Paddle the raft forward each tick until it finishes (bounded by the wait).
DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimPaddleUntilFinishCommand, FAutomationTestBase*, Test);
bool FRaftSimPaddleUntilFinishCommand::Update()
{
    ARaftSimRaftActor* Raft = FindOne<ARaftSimRaftActor>(GetRunTestWorld());
    ARaftSimRunManager* Run = FindOne<ARaftSimRunManager>(GetRunTestWorld());
    if (Raft == nullptr || Run == nullptr)
    {
        Test->AddError(TEXT("Raft or run manager missing"));
        return true; // stop
    }
    if (Run->GetRunState() == ERaftSimRunState::Finished)
    {
        return true; // done
    }
    Raft->ApplyPaddleStroke(ERaftSimPaddleSide::Both, 1.0f);
    return false; // keep paddling
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimAssertScoredCommand, FAutomationTestBase*, Test);
bool FRaftSimAssertScoredCommand::Update()
{
    UWorld* World = GetRunTestWorld();
    ARaftSimRunManager* Run = FindOne<ARaftSimRunManager>(World);
    if (Run == nullptr)
    {
        Test->AddError(TEXT("Run manager missing at assert"));
        return true;
    }
    Test->TestEqual(
        TEXT("run finished after paddling to the line"),
        static_cast<int32>(Run->GetRunState()),
        static_cast<int32>(ERaftSimRunState::Finished));
    Test->TestTrue(
        FString::Printf(TEXT("clean run scored (%.0f)"), Run->GetFinalScore().TotalScore),
        Run->GetFinalScore().TotalScore > 0.0f);

    if (const UGameInstance* GI = World->GetGameInstance())
    {
        if (const URaftSimSaveSubsystem* Save = GI->GetSubsystem<URaftSimSaveSubsystem>())
        {
            Test->TestTrue(
                FString::Printf(TEXT("run scenario '%s' recorded as completed in save"),
                    *Run->ScenarioId.ToString()),
                Save->GetSave() != nullptr &&
                    Save->GetSave()->CompletedScenarioIds.Contains(Run->ScenarioId));
            Test->TestTrue(
                TEXT("best overall score persisted"),
                Save->GetSave() != nullptr && Save->GetSave()->BestOverallScore > 0.0f);
        }
    }
    return true;
}

} // namespace

bool FRaftSimRunScoresAndSavesTest::RunTest(const FString&)
{
    AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.5f));  // settle
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimConfigureRunCommand(this));
    // Paddle each tick, capped at 25 s of engine time.
    ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(0.1f));
    for (int32 Step = 0; Step < 250; ++Step)
    {
        ADD_LATENT_AUTOMATION_COMMAND(FRaftSimPaddleUntilFinishCommand(this));
        ADD_LATENT_AUTOMATION_COMMAND(FEngineWaitLatentCommand(0.1f));
    }
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimAssertScoredCommand(this));
    return true;
}

#endif // WITH_AUTOMATION_TESTS
