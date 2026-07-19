// P3 test: the run audio director produces a river-roar mix that rises as the
// raft speeds up (gameplay-reactive water ambience).

#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "RaftSimRaftActor.h"
#include "Tests/AutomationCommon.h"

#include "../RaftSimRunAudioDirector.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimRunAudioReactsTest,
    "RaftSim.P3.RunAudioReactsToFlow",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

namespace
{

template <typename T>
T* FindAudioTestActor()
{
    T* NewestActor = nullptr;
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
    {
        UWorld* World = Context.World();
        if (World != nullptr &&
            (Context.WorldType == EWorldType::PIE || Context.WorldType == EWorldType::Game))
        {
            if (TActorIterator<T> It(World); It)
            {
                NewestActor = *It;
            }
        }
    }
    return NewestActor;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimAudioResetCommand, FAutomationTestBase*, Test);
bool FRaftSimAudioResetCommand::Update()
{
    ARaftSimRaftActor* Raft = FindAudioTestActor<ARaftSimRaftActor>();
    if (Raft == nullptr)
    {
        Test->AddError(TEXT("Raft missing before audio reset"));
        return true;
    }
    Raft->ResetMotionForTesting();
    return true;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimAudioBaselineCommand, FAutomationTestBase*, Test);
bool FRaftSimAudioBaselineCommand::Update()
{
    ARaftSimRunAudioDirector* Audio = FindAudioTestActor<ARaftSimRunAudioDirector>();
    ARaftSimRaftActor* Raft = FindAudioTestActor<ARaftSimRaftActor>();
    if (Audio == nullptr || Raft == nullptr)
    {
        Test->AddError(TEXT("Audio director or raft missing"));
        return true;
    }
    Audio->Tags.Add(FName(*FString::Printf(
        TEXT("RoarBase:%f"), Audio->GetCurrentAudioParameters().RiverRoar)));
    Raft->IssueCrewCommand(ERaftSimCrewCommand::AllForward);
    return true;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimAudioAssertCommand, FAutomationTestBase*, Test);
bool FRaftSimAudioAssertCommand::Update()
{
    ARaftSimRunAudioDirector* Audio = FindAudioTestActor<ARaftSimRunAudioDirector>();
    if (Audio == nullptr)
    {
        Test->AddError(TEXT("Audio director missing at assert"));
        return true;
    }
    float RoarBase = 0.0f;
    for (const FName& Tag : Audio->Tags)
    {
        FString S = Tag.ToString();
        if (S.RemoveFromStart(TEXT("RoarBase:")))
        {
            RoarBase = FCString::Atof(*S);
        }
    }
    const float RoarNow = Audio->GetCurrentAudioParameters().RiverRoar;
    Test->TestTrue(
        FString::Printf(TEXT("river roar rose with speed (%.2f -> %.2f)"), RoarBase, RoarNow),
        RoarNow > RoarBase + 0.02f);
    return true;
}

} // namespace

bool FRaftSimRunAudioReactsTest::RunTest(const FString&)
{
    AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.5f));
    // This test can follow the crew-propulsion test in one editor process.
    // Clear inherited motion, then allow the mix one frame-window to settle so
    // the baseline cannot start at the roar clamp.
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimAudioResetCommand(this));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(1.0f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimAudioBaselineCommand(this));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(4.0f)); // crew paddles up to speed
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimAudioAssertCommand(this));
    return true;
}

#endif // WITH_AUTOMATION_TESTS
