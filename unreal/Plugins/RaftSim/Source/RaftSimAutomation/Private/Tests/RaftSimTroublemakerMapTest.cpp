// P4 test: each generated river map loads a live cooked-field river window (or
// falls back to the dev tank if its fields are not cooked yet) and the raft
// rests on wet, finite water. Runs once per map that exists.

#include "AssetRegistry/AssetRegistryModule.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRaftActor.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Tests/AutomationCommon.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_COMPLEX_AUTOMATION_TEST(
    FRaftSimRiverMapLoadsTest,
    "RaftSim.P4.RiverMapLoads",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

namespace
{

const TCHAR* GRiverMapPaths[] = {
    TEXT("/Game/RaftSim/Maps/L_Troublemaker"),
    TEXT("/Game/RaftSim/Maps/L_Hance"),
    TEXT("/Game/RaftSim/Maps/L_UpperHuacas"),
    TEXT("/Game/RaftSim/Maps/L_Terminator"),
    TEXT("/Game/RaftSim/Maps/L_LavaCanyon"),
};

UWorld* GetRiverTestWorld()
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

bool MapExists(const FString& PackagePath)
{
    const FString FileName = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetMapPackageExtension());
    return FPaths::FileExists(FileName);
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimAssertRiverMapCommand, FAutomationTestBase*, Test);
bool FRaftSimAssertRiverMapCommand::Update()
{
    UWorld* World = GetRiverTestWorld();
    if (World == nullptr)
    {
        Test->AddError(TEXT("No world for river map"));
        return true;
    }

    // A live water window must be configured (river window, or the dev-tank
    // fallback if this river's cooked fields are not present yet). Either way,
    // wet finite water the raft can float on.
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
                        FString::Printf(TEXT("window is wet (%.2f) and finite"), Stats.WetFraction),
                        Stats.WetFraction > 0.02f && !Stats.bHasNonFinite);
                }
            }
        }
    }

    if (TActorIterator<ARaftSimRaftActor> It(World); It)
    {
        ARaftSimRaftActor* Raft = *It;
        Test->TestTrue(
            FString::Printf(TEXT("raft rests within depth envelope (z=%.0f)"), Raft->GetActorLocation().Z),
            FMath::Abs(Raft->GetActorLocation().Z) < 20000.0f);
    }
    return true;
}

} // namespace

void FRaftSimRiverMapLoadsTest::GetTests(
    TArray<FString>& OutBeautifiedNames, TArray<FString>& OutTestCommands) const
{
    for (const TCHAR* MapPath : GRiverMapPaths)
    {
        if (MapExists(MapPath))
        {
            OutBeautifiedNames.Add(FPackageName::GetShortName(MapPath));
            OutTestCommands.Add(MapPath);
        }
    }
}

bool FRaftSimRiverMapLoadsTest::RunTest(const FString& MapPath)
{
    AutomationOpenMap(MapPath);
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(3.0f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimAssertRiverMapCommand(this));
    return true;
}

#endif // WITH_AUTOMATION_TESTS
