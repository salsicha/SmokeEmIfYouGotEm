// P2 exit-gate behavioral test (release-1.0-plan.md §7 P2): forced upstream
// overwash drives the D3 flip moment negative, the raft capsizes, crew become
// swimmers, and a guide re-flip reseats them.

#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "RaftSimRaftActor.h"
#include "Tests/AutomationCommon.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimRaftFlipsAndRecoversTest,
    "RaftSim.P2.RaftFlipsAndRecovers",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

namespace
{

UWorld* GetFlipTestWorld()
{
    UWorld* NewestGameWorld = nullptr;
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
    {
        if (Context.World() != nullptr &&
            (Context.WorldType == EWorldType::PIE || Context.WorldType == EWorldType::Game))
        {
            // During AutomationOpenMap turnover the old PIE context can remain
            // first in the engine list for a few frames. The newest context is
            // appended last; retaining it prevents commands targeting a world
            // that is already tearing down.
            NewestGameWorld = Context.World();
        }
    }
    return NewestGameWorld;
}

ARaftSimRaftActor* FindRaft()
{
    UWorld* World = GetFlipTestWorld();
    if (World == nullptr)
    {
        return nullptr;
    }
    if (TActorIterator<ARaftSimRaftActor> It(World); It)
    {
        return *It;
    }
    return nullptr;
}

// Step 1: settle done — impose strong upstream (lateral) overwash.
DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimForceOverwashCommand, FAutomationTestBase*, Test);
bool FRaftSimForceOverwashCommand::Update()
{
    ARaftSimRaftActor* Raft = FindRaft();
    if (Raft == nullptr)
    {
        Test->AddError(TEXT("No raft in the test tank"));
        return true;
    }
    // Surface 0.8 m above the deck, 6 m/s across the port tube: the upstream
    // tube overtops far more than the lee tube, so retained water piles to one
    // side and the D3 roll moment beats the flip threshold.
    Raft->ForceOverwashForTesting(0.8f, FVector(0.0f, 6.0f, 0.0f));
    return true;
}

// Step 2: assert capsize + swimmers, then clear overwash and re-flip.
DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimAssertCapsizeAndReflipCommand, FAutomationTestBase*, Test);
bool FRaftSimAssertCapsizeAndReflipCommand::Update()
{
    ARaftSimRaftActor* Raft = FindRaft();
    if (Raft == nullptr)
    {
        Test->AddError(TEXT("Raft disappeared before capsize check"));
        return true;
    }
    Test->TestEqual(
        TEXT("raft capsized under sustained overwash"),
        static_cast<int32>(Raft->GetRaftMode()),
        static_cast<int32>(ERaftSimRaftMode::Capsized));
    Test->TestTrue(
        FString::Printf(TEXT("crew ejected as swimmers (%d)"), Raft->GetSwimmerCount()),
        Raft->GetSwimmerCount() > 0);

    // Clear the overwash and re-right the raft.
    Raft->ForceOverwashForTesting(-1.0f, FVector::ZeroVector);
    Raft->RequestReflip();
    return true;
}

// Step 3: assert recovery completes — swimmers reseated, raft upright.
DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimAssertRecoveredCommand, FAutomationTestBase*, Test);
bool FRaftSimAssertRecoveredCommand::Update()
{
    ARaftSimRaftActor* Raft = FindRaft();
    if (Raft == nullptr)
    {
        Test->AddError(TEXT("Raft disappeared before recovery check"));
        return true;
    }
    Test->TestEqual(
        TEXT("raft returned upright after re-flip and reseat"),
        static_cast<int32>(Raft->GetRaftMode()),
        static_cast<int32>(ERaftSimRaftMode::Upright));
    Test->TestEqual(
        TEXT("all swimmers reseated"), Raft->GetSwimmerCount(), 0);
    Test->TestTrue(
        TEXT("raft roll returned near level (< 30 deg)"),
        FMath::Abs(Raft->GetActorRotation().Roll) < 30.0f);
    return true;
}

} // namespace

bool FRaftSimRaftFlipsAndRecoversTest::RunTest(const FString&)
{
    AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(3.0f));    // settle
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimForceOverwashCommand(this));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.5f));    // accumulate → flip
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimAssertCapsizeAndReflipCommand(this));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(3.0f));    // drift + reseat
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimAssertRecoveredCommand(this));
    return true;
}

#endif // WITH_AUTOMATION_TESTS
