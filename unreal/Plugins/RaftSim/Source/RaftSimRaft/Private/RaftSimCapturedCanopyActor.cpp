#include "RaftSimCapturedCanopyActor.h"

#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"
#include "HAL/IConsoleManager.h"
#include "WorldPartition/WorldPartition.h"

ARaftSimCapturedCanopyActor::ARaftSimCapturedCanopyActor()
{
    PrimaryActorTick.bCanEverTick = false;
    USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("CapturedCanopyRoot"));
    Root->SetMobility(EComponentMobility::Static);
    SetRootComponent(Root);
    CanopyA = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("CanopyA"));
    CanopyB = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("CanopyB"));
    CanopyC = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("CanopyC"));
    for (UHierarchicalInstancedStaticMeshComponent* Component : {CanopyA.Get(), CanopyB.Get(), CanopyC.Get()})
    {
        Component->SetupAttachment(Root);
        Component->SetMobility(EComponentMobility::Static);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetGenerateOverlapEvents(false);
        Component->SetCanEverAffectNavigation(false);
        Component->SetCullDistances(0, 0);
        Component->SetCastShadow(true);
    }
}

// A 256 m canopy cell loads when its bounds touch the World Partition loading
// range, so its far trees can stand up to one cell beyond the terrain that
// streamed out under them (South Fork: 809 trees at 2.07-2.36 km had no ground
// in a game-world trace audit and hung over the coarse far terrain). Streamed
// worlds therefore cull canopy just inside the terrain loading range.
static TAutoConsoleVariable<float> CVarRaftSimStreamedCanopyCullDistanceM(
    TEXT("raftsim.StreamedCanopyCullDistanceM"), 1950.0f,
    TEXT("World Partition streamed maps: cull canopy instances farther than this from the view (m); 0 disables."),
    ECVF_Default);

void ARaftSimCapturedCanopyActor::BeginPlay()
{
    Super::BeginPlay();
    const UWorld* World = GetWorld();
    const float CullM = CVarRaftSimStreamedCanopyCullDistanceM.GetValueOnGameThread();
    const UWorldPartition* Partition = World ? World->GetWorldPartition() : nullptr;
    if (!World || !World->IsGameWorld() || CullM <= 0.0f || !Partition || !Partition->IsStreamingEnabled())
    {
        return;
    }
    const int32 EndCm = FMath::RoundToInt(CullM * 100.0f);
    const int32 StartCm = FMath::Max(EndCm - 15000, 0);
    for (UHierarchicalInstancedStaticMeshComponent* Component : {CanopyA.Get(), CanopyB.Get(), CanopyC.Get()})
    {
        if (Component)
        {
            Component->SetCullDistances(StartCm, EndCm);
        }
    }
}
