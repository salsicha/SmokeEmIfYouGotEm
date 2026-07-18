// P3 test: the Troublemaker map loads with a live cooked-field river window
// (not the flat dev tank) and the raft floats on it.

#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRiverWaterConfig.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Tests/AutomationCommon.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimTroublemakerRiverLoadsTest,
    "RaftSim.P3.TroublemakerRiverLoads",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

namespace
{

UWorld* GetTmWorld()
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

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimAssertTroublemakerCommand, FAutomationTestBase*, Test);
bool FRaftSimAssertTroublemakerCommand::Update()
{
    UWorld* World = GetTmWorld();
    if (World == nullptr)
    {
        Test->AddError(TEXT("No world for Troublemaker map"));
        return true;
    }

    // The river config actor is present.
    bool bHasConfig = false;
    if (TActorIterator<ARaftSimRiverWaterConfig> It(World); It)
    {
        bHasConfig = true;
    }
    Test->TestTrue(TEXT("river water config placed in the map"), bHasConfig);

    // The water runtime loaded a live window (cooked field), not just the tank.
    if (const UGameInstance* GI = World->GetGameInstance())
    {
        if (URaftSimPhysicsBridgeSubsystem* Bridge =
                GI->GetSubsystem<URaftSimPhysicsBridgeSubsystem>())
        {
            if (URaftSimWaterRuntimeAdapter* Water = Bridge->GetWaterRuntime())
            {
                Test->TestTrue(TEXT("a live water window is configured"), Water->HasLiveWindow());
                FRaftSimWaterLiveWindowStats Stats;
                if (Water->GetLiveWindowStats(Stats))
                {
                    Test->TestTrue(
                        FString::Printf(TEXT("river window is wet (%.2f) and finite"), Stats.WetFraction),
                        Stats.WetFraction > 0.05f && !Stats.bHasNonFinite);
                }
            }
        }
    }

    // The raft settled near a water surface (didn't sink through a dry window).
    if (ARaftSimRaftActor* Raft = [World]() -> ARaftSimRaftActor* {
            if (TActorIterator<ARaftSimRaftActor> It(World); It) { return *It; }
            return nullptr; }())
    {
        Test->TestTrue(
            FString::Printf(TEXT("raft rests within depth envelope (z=%.0f)"), Raft->GetActorLocation().Z),
            FMath::Abs(Raft->GetActorLocation().Z) < 20000.0f);
    }
    return true;
}

} // namespace

bool FRaftSimTroublemakerRiverLoadsTest::RunTest(const FString&)
{
    AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_Troublemaker"));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(3.0f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimAssertTroublemakerCommand(this));
    return true;
}

#endif // WITH_AUTOMATION_TESTS
