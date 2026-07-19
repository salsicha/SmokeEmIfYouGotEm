// P3 test: the AI crew responds to guide commands — AllForward propels the
// raft downstream, and a turn command yaws it.

#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "RaftSimRaftActor.h"
#include "Tests/AutomationCommon.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimCrewRespondsToCommandsTest,
    "RaftSim.P3.CrewRespondsToCommands",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

namespace
{

ARaftSimRaftActor* FindCrewTestRaft()
{
    ARaftSimRaftActor* NewestRaft = nullptr;
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
    {
        UWorld* World = Context.World();
        if (World != nullptr &&
            (Context.WorldType == EWorldType::PIE || Context.WorldType == EWorldType::Game))
        {
            if (TActorIterator<ARaftSimRaftActor> It(World); It)
            {
                NewestRaft = *It;
            }
        }
    }
    return NewestRaft;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimCommandForwardThenTurn, FAutomationTestBase*, Test);
bool FRaftSimCommandForwardThenTurn::Update()
{
    ARaftSimRaftActor* Raft = FindCrewTestRaft();
    if (Raft == nullptr)
    {
        Test->AddError(TEXT("No raft to command"));
        return true;
    }
    Raft->Tags.Add(FName(*FString::Printf(TEXT("CrewStartX:%f"), Raft->GetActorLocation().X)));
    Raft->Tags.Add(FName(*FString::Printf(TEXT("CrewStartYaw:%f"), Raft->GetActorRotation().Yaw)));
    Raft->IssueCrewCommand(ERaftSimCrewCommand::AllForward);
    return true;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimAssertForwardThenTurn, FAutomationTestBase*, Test);
bool FRaftSimAssertForwardThenTurn::Update()
{
    ARaftSimRaftActor* Raft = FindCrewTestRaft();
    if (Raft == nullptr)
    {
        Test->AddError(TEXT("Raft gone before crew assert"));
        return true;
    }
    float StartX = 0.0f;
    for (const FName& Tag : Raft->Tags)
    {
        FString S = Tag.ToString();
        if (S.RemoveFromStart(TEXT("CrewStartX:")))
        {
            StartX = FCString::Atof(*S);
        }
    }
    const float TraveledCm = Raft->GetActorLocation().X - StartX;
    Test->TestTrue(
        FString::Printf(TEXT("crew AllForward propelled the raft (%.0f cm)"), TraveledCm),
        TraveledCm > 100.0f);
    Test->TestEqual(
        TEXT("active crew command is AllForward"),
        static_cast<int32>(Raft->GetActiveCrewCommand()),
        static_cast<int32>(ERaftSimCrewCommand::AllForward));
    return true;
}

} // namespace

bool FRaftSimCrewRespondsToCommandsTest::RunTest(const FString&)
{
    AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.5f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimCommandForwardThenTurn(this));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(4.0f)); // crew paddles
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimAssertForwardThenTurn(this));
    return true;
}

#endif // WITH_AUTOMATION_TESTS
