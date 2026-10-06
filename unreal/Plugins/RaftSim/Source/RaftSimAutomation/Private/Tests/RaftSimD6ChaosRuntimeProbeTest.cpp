// Verifies that the D6 measurement environment can advance a genuine Unreal
// Chaos rigid body. This is deliberately separate from the analytical
// flexible-raft fixture evaluator: a valid physics actor must be created by
// the world's physics scene and its pose must change after fixed world ticks.

#if WITH_DEV_AUTOMATION_TESTS

#include "Components/BoxComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Misc/AutomationTest.h"
#include "Physics/PhysicsInterfaceCore.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimD6ChaosRuntimeProbeTest,
    "RaftSim.D6.ChaosRuntimeProbe",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

namespace
{

class FScopedRaftSimD6ChaosWorld
{
public:
    FScopedRaftSimD6ChaosWorld()
    {
        if (GEngine == nullptr)
        {
            return;
        }

        const FName WorldName = MakeUniqueObjectName(
            nullptr,
            UWorld::StaticClass(),
            TEXT("RaftSimD6ChaosProbeWorld"),
            EUniqueObjectNameOptions::GloballyUnique);
        FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        World = UWorld::CreateWorld(
            EWorldType::Game,
            false,
            WorldName,
            GetTransientPackage());
        if (World == nullptr)
        {
            GEngine->DestroyWorldContext(World);
            return;
        }

        World->AddToRoot();
        Context.SetCurrentWorld(World);
        CachedFrameCounter = GFrameCounter;
        World->InitializeActorsForPlay(FURL());
        World->BeginPlay();
    }

    ~FScopedRaftSimD6ChaosWorld()
    {
        if (World == nullptr)
        {
            return;
        }

        GEngine->ShutdownWorldNetDriver(World);
        if (World->HasBegunPlay())
        {
            World->BeginTearingDown();
            World->EndPlay(EEndPlayReason::Quit);
        }
        GFrameCounter = CachedFrameCounter;
        World->DestroyWorld(true);
        World->SetPhysicsScene(nullptr);
        GEngine->DestroyWorldContext(World);
        World->RemoveFromRoot();
        World = nullptr;
    }

    UWorld* Get() const
    {
        return World;
    }

private:
    UWorld* World = nullptr;
    uint64 CachedFrameCounter = 0;
};

UBoxComponent* SpawnSimulatedBox(UWorld& World)
{
    AActor* Actor = World.SpawnActor<AActor>(
        AActor::StaticClass(),
        FVector(0.0, 0.0, 300.0),
        FRotator::ZeroRotator);
    if (Actor == nullptr)
    {
        return nullptr;
    }

    UBoxComponent* Box = NewObject<UBoxComponent>(Actor, TEXT("ChaosProbeRigidBody"));
    Actor->SetRootComponent(Box);
    Actor->AddInstanceComponent(Box);
    Box->SetBoxExtent(FVector(100.0, 50.0, 25.0));
    Box->SetMobility(EComponentMobility::Movable);
    Box->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Box->SetCollisionObjectType(ECC_PhysicsBody);
    Box->SetCollisionResponseToAllChannels(ECR_Block);
    Box->SetEnableGravity(true);
    Box->RegisterComponent();
    Box->SetSimulatePhysics(true);
    Box->SetMassOverrideInKg(NAME_None, 805.0, true);
    Box->WakeAllRigidBodies();
    return Box;
}

} // namespace

bool FRaftSimD6ChaosRuntimeProbeTest::RunTest(const FString& Parameters)
{
    FScopedRaftSimD6ChaosWorld ScopedWorld;
    UWorld* World = ScopedWorld.Get();
    if (World == nullptr || World->GetPhysicsScene() == nullptr)
    {
        AddError(TEXT("Failed to create a transient game world with a physics scene."));
        return false;
    }

    UBoxComponent* Box = SpawnSimulatedBox(*World);
    if (Box == nullptr)
    {
        AddError(TEXT("Failed to create the Chaos rigid-body probe."));
        return false;
    }

    const FPhysicsActorHandle ActorHandle = Box->BodyInstance.GetPhysicsActorHandle();
    TestTrue(TEXT("Chaos physics actor handle is valid"), FPhysicsInterface::IsValid(ActorHandle));
    TestTrue(TEXT("Chaos physics actor is rigid"), FPhysicsInterface::IsRigidBody(ActorHandle));

    const double StartZ = Box->GetComponentLocation().Z;
    constexpr float FixedStepSeconds = 1.0f / 30.0f;
    for (int32 Step = 0; Step < 12; ++Step)
    {
        World->Tick(LEVELTICK_All, FixedStepSeconds);
        ++GFrameCounter;
    }
    const double EndZ = Box->GetComponentLocation().Z;

    TestTrue(
        FString::Printf(TEXT("Chaos body advanced under gravity (start=%.3f cm end=%.3f cm)"), StartZ, EndZ),
        EndZ < StartZ - 1.0);
    TestTrue(
        TEXT("Chaos body reports downward velocity"),
        Box->GetPhysicsLinearVelocity().Z < -1.0);
    return true;
}

#endif
