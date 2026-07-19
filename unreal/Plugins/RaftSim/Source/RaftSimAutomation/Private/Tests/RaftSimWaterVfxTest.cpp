#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/PostProcessComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "RaftSimWaterVfxActor.h"
#include "Tests/AutomationCommon.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimWaterVfxClassifierTest,
    "RaftSim.M4.WaterVfxClassifierUsesHydraulicsAndContacts",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimWaterVfxClassifierTest::RunTest(const FString&)
{
    FRaftSimWaterSample Calm;
    Calm.bWet = true;
    Calm.DepthMeters = 3.0f;
    Calm.VelocityMetersPerSecond = FVector(0.2f, 0.0f, 0.0f);
    const FRaftSimWaterVfxState CalmState =
        ARaftSimWaterVfxActor::EvaluatePresentation(
            Calm, FVector(0.2f, 0.0f, 0.0f), 0, 0.0f, false);
    TestTrue(TEXT("calm water does not manufacture spray"), CalmState.Spray < 0.05f);

    FRaftSimWaterSample Rapid = Calm;
    Rapid.DepthMeters = 0.75f;
    Rapid.VelocityMetersPerSecond = FVector(6.8f, 0.4f, 0.0f);
    const FRaftSimWaterVfxState RapidState =
        ARaftSimWaterVfxActor::EvaluatePresentation(
            Rapid, FVector(2.0f, 0.0f, 0.0f), 4, 0.16f, true);
    TestTrue(TEXT("supercritical contact makes spray"), RapidState.Spray > 0.8f);
    TestTrue(TEXT("contact makes an impact sheet"), RapidState.ImpactSheet > 0.8f);
    TestTrue(TEXT("spray creates droplets"), RapidState.Droplets > 0.8f);
    TestTrue(TEXT("aeration creates mist"), RapidState.Mist > 0.6f);
    TestEqual(TEXT("underwater state is explicit"), RapidState.Underwater, 1.0f);

    FRaftSimWaterSample Dry;
    const FRaftSimWaterVfxState DryState =
        ARaftSimWaterVfxActor::EvaluatePresentation(
            Dry, FVector::ZeroVector, 8, 0.22f, false);
    TestEqual(TEXT("dry terrain has no spray"), DryState.Spray, 0.0f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimWaterVfxRuntimePoolTest,
    "RaftSim.M4.WaterVfxRuntimePoolSpawnsWithRaft",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

namespace
{
UWorld* GetWaterVfxTestWorld()
{
    for (const FWorldContext& Context : GEngine->GetWorldContexts())
    {
        if (Context.World() &&
            (Context.WorldType == EWorldType::PIE || Context.WorldType == EWorldType::Game))
        {
            return Context.World();
        }
    }
    return nullptr;
}

DEFINE_LATENT_AUTOMATION_COMMAND_ONE_PARAMETER(
    FRaftSimAssertWaterVfxPoolCommand, FAutomationTestBase*, Test);
bool FRaftSimAssertWaterVfxPoolCommand::Update()
{
    UWorld* World = GetWaterVfxTestWorld();
    if (!World)
    {
        Test->AddError(TEXT("No active game world"));
        return true;
    }
    ARaftSimWaterVfxActor* Vfx = nullptr;
    if (TActorIterator<ARaftSimWaterVfxActor> It(World); It)
    {
        Vfx = *It;
    }
    Test->TestNotNull(TEXT("raft spawns live-water VFX actor"), Vfx);
    if (Vfx)
    {
        TArray<UHierarchicalInstancedStaticMeshComponent*> Pools;
        Vfx->GetComponents(Pools);
        Test->TestEqual(TEXT("spray/mist/sheet/droplet pools exist"), Pools.Num(), 4);
        Test->TestNotNull(
            TEXT("underwater post process exists"),
            Vfx->FindComponentByClass<UPostProcessComponent>());
        Test->TestTrue(TEXT("VFX actor binds live solver water"), Vfx->IsLiveWaterBound());
    }
    return true;
}
}

bool FRaftSimWaterVfxRuntimePoolTest::RunTest(const FString&)
{
    AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.0f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimAssertWaterVfxPoolCommand(this));
    return true;
}

#endif
