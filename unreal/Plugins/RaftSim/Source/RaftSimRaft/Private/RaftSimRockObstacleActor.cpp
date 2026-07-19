#include "RaftSimRockObstacleActor.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

ARaftSimRockObstacleActor::ARaftSimRockObstacleActor()
{
    PrimaryActorTick.bCanEverTick = false;

    RockMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("RockMesh"));
    SetRootComponent(RockMesh);
    RockMesh->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    RockMesh->SetCollisionObjectType(ECC_WorldStatic);

    static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(
        TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    if (SphereMesh.Succeeded())
    {
        RockMesh->SetStaticMesh(SphereMesh.Object);
    }
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> RockMaterial(
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverTerrain."
             "M_RaftSim_PhotorealRiverTerrain"));
    if (RockMaterial.Succeeded())
    {
        RockMesh->SetMaterial(0, RockMaterial.Object);
    }
    RefreshVisualScale();
}

void ARaftSimRockObstacleActor::ConfigureContact(
    float InRadiusM,
    float InFrictionCoefficient)
{
    ContactRadiusM = FMath::Max(0.1f, InRadiusM);
    FrictionCoefficient = FMath::Clamp(InFrictionCoefficient, 0.0f, 2.0f);
    RefreshVisualScale();
}

void ARaftSimRockObstacleActor::RefreshVisualScale()
{
    if (RockMesh != nullptr)
    {
        // Engine sphere is one metre in diameter. Slight vertical flattening
        // keeps the placeholder proxy boulder-like until a reviewed mesh is
        // assigned; contact remains the recorded horizontal radius.
        RockMesh->SetRelativeScale3D(
            FVector(2.0f * ContactRadiusM, 2.0f * ContactRadiusM, 1.45f * ContactRadiusM));
    }
}
