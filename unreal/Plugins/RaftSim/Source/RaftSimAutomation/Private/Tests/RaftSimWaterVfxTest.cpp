#include "Components/InstancedStaticMeshComponent.h"
#include "Components/PostProcessComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/AutomationTest.h"
#include "ProceduralMeshComponent.h"
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
    TestTrue(
        TEXT("calm water remains below visible mist threshold"),
        CalmState.Mist < 0.22f);

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
        TArray<UInstancedStaticMeshComponent*> Pools;
        Vfx->GetComponents(Pools);
        Test->TestEqual(
            TEXT("spray/mist/sheet/droplet/rapid-aerosol pools exist"), Pools.Num(), 5);
        for (const UInstancedStaticMeshComponent* Pool : Pools)
        {
            const UStaticMesh* CardMesh = Pool->GetStaticMesh().Get();
            Test->TestNotNull(TEXT("water VFX pool has a card mesh"), CardMesh);
            if (CardMesh)
            {
                Test->TestTrue(
                    TEXT("water VFX uses soft plane cards rather than geometric spheres"),
                    CardMesh->GetPathName().Contains(TEXT("Plane")));
            }
            Test->TestNotNull(
                TEXT("water VFX pool receives a channel-specific dynamic material"),
                Cast<UMaterialInstanceDynamic>(Pool->GetMaterial(0)));
        }
        Test->TestNotNull(
            TEXT("underwater post process exists"),
            Vfx->FindComponentByClass<UPostProcessComponent>());
        const UProceduralMeshComponent* ContactPatch =
            Vfx->FindComponentByClass<UProceduralMeshComponent>();
        Test->TestNotNull(TEXT("bounded contact-water patch exists"), ContactPatch);
        if (ContactPatch)
        {
            Test->TestEqual(
                TEXT("contact-water patch never affects collision"),
                ContactPatch->GetCollisionEnabled(),
                ECollisionEnabled::NoCollision);
            Test->TestNotNull(
                TEXT("contact-water patch receives a dynamic material"),
                Cast<UMaterialInstanceDynamic>(ContactPatch->GetMaterial(0)));
        }
        Test->TestTrue(
            TEXT("contact-water patch starts fail-closed without D4 contact"),
            !Vfx->IsContactWaterPatchVisible() &&
                Vfx->GetContactWaterPatchTriangleCount() == 0);
        Test->TestTrue(TEXT("VFX actor binds live solver water"), Vfx->IsLiveWaterBound());
        Test->TestTrue(
            TEXT("production Niagara water VFX replaces visible card rendering"),
            Vfx->IsProductionNiagaraReady());
        Test->TestEqual(
            TEXT("three contact and sixteen rapid Niagara components are asset-bound"),
            Vfx->GetProductionNiagaraComponentCount(),
            19);
    }
    return true;
}
}

bool FRaftSimWaterVfxRuntimePoolTest::RunTest(const FString&)
{
#if PLATFORM_MAC
    // UE 5.8 can tear down an offscreen PIE text-input context after its
    // NSWindow has already gone away. This engine diagnostic is unrelated to
    // the runtime VFX pool assertions.
    AddExpectedErrorPlain(
        TEXT("LogMacTextInputMethodSystem: Deactivating a context failed when its window couldn't be found."),
        EAutomationExpectedErrorFlags::Contains,
        -1);
#endif
    AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.0f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimAssertWaterVfxPoolCommand(this));
    return true;
}

#endif
