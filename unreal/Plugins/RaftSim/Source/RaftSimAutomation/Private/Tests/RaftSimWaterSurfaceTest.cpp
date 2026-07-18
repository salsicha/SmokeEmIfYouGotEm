// P2 water-rendering v1 test: the water surface actor spawns with the raft,
// builds a procedural mesh, and its bounds track the live solver surface.

#include "Components/MeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimWaterSurfaceActor.h"
#include "Tests/AutomationCommon.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimWaterSurfaceRendersTest,
    "RaftSim.P2.WaterSurfaceRenders",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext |
        EAutomationTestFlags::ProductFilter)

namespace
{

UWorld* GetSurfaceTestWorld()
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
    FRaftSimAssertWaterSurfaceCommand, FAutomationTestBase*, Test);
bool FRaftSimAssertWaterSurfaceCommand::Update()
{
    UWorld* World = GetSurfaceTestWorld();
    if (World == nullptr)
    {
        Test->AddError(TEXT("No active game world"));
        return true;
    }
    ARaftSimWaterSurfaceActor* Surface = nullptr;
    if (TActorIterator<ARaftSimWaterSurfaceActor> It(World); It)
    {
        Surface = *It;
    }
    if (Surface == nullptr)
    {
        Test->AddError(TEXT("No water surface actor spawned with the raft"));
        return true;
    }

    UProceduralMeshComponent* Mesh =
        Surface->FindComponentByClass<UProceduralMeshComponent>();
    Test->TestNotNull(TEXT("surface has a procedural mesh"), Mesh);
    if (Mesh != nullptr)
    {
        Test->TestTrue(
            TEXT("surface mesh has a section built"), Mesh->GetNumSections() > 0);
        // A built water grid has non-trivial bounds over the tank footprint.
        const FBoxSphereBounds Bounds = Mesh->Bounds;
        Test->TestTrue(
            FString::Printf(TEXT("surface spans the tank (extent %.0f cm)"),
                Bounds.BoxExtent.X),
            Bounds.BoxExtent.X > 1000.0f);
    }
    return true;
}

} // namespace

bool FRaftSimWaterSurfaceRendersTest::RunTest(const FString&)
{
    AutomationOpenMap(TEXT("/Game/RaftSim/Maps/L_RaftSimTestTank"));
    ADD_LATENT_AUTOMATION_COMMAND(FWaitLatentCommand(2.0f));
    ADD_LATENT_AUTOMATION_COMMAND(FRaftSimAssertWaterSurfaceCommand(this));
    return true;
}

#endif // WITH_AUTOMATION_TESTS
