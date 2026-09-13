#include "RaftSimCapturedCanopyActor.h"

#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"

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
