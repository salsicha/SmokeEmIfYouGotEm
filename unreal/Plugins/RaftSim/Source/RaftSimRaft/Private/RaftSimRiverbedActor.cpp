#include "RaftSimRiverbedActor.h"

#include "Engine/GameInstance.h"
#include "Materials/MaterialInterface.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
constexpr float kBedCmPerM = 100.0f;
}

ARaftSimRiverbedActor::ARaftSimRiverbedActor()
{
    PrimaryActorTick.bCanEverTick = false;

    BedMesh = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("BedMesh"));
    SetRootComponent(BedMesh);
    BedMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    BedMesh->bUseAsyncCooking = true;

    // World-aligned (triplanar) terrain material renders correctly on this
    // procedural mesh; the landscape material needs LandscapeLayerCoords.
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> TerrainMat(
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverTerrain."
             "M_RaftSim_PhotorealRiverTerrain"));
    if (TerrainMat.Succeeded())
    {
        TerrainMaterial = TerrainMat.Object;
    }
}

void ARaftSimRiverbedActor::BeginPlay()
{
    Super::BeginPlay();

    if (const UGameInstance* GameInstance = GetGameInstance())
    {
        if (URaftSimPhysicsBridgeSubsystem* Bridge =
                GameInstance->GetSubsystem<URaftSimPhysicsBridgeSubsystem>())
        {
            WaterAdapter = Bridge->GetWaterRuntime();
        }
    }

    BuildBed();
}

void ARaftSimRiverbedActor::BuildBed()
{
    const int32 GridN =
        FMath::Max(2, FMath::RoundToInt(GridSizeMeters / VertexSpacingMeters) + 1);
    const int32 VertCount = GridN * GridN;

    TArray<FVector> Vertices;
    TArray<int32> Triangles;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<FProcMeshTangent> Tangents;
    Vertices.SetNum(VertCount);
    Normals.SetNum(VertCount);
    UVs.SetNum(VertCount);
    VertexColors.SetNum(VertCount);
    Tangents.SetNum(VertCount);
    Triangles.Reset((GridN - 1) * (GridN - 1) * 6);

    SetActorLocation(FVector::ZeroVector);

    // Height sampled from the adapter's bed (already re-zeroed to the local
    // datum). Beyond the cooked window the adapter clamps to the edge, so the
    // valley walls extend outward at bank height.
    auto BedZCm = [this](float WorldXCm, float WorldYCm) -> float
    {
        if (WaterAdapter != nullptr)
        {
            FRaftSimWaterSample Sample;
            if (WaterAdapter->SampleWaterAtWorldPosition(
                    FVector(WorldXCm, WorldYCm, 0.0f), Sample))
            {
                return Sample.BedHeightMeters * kBedCmPerM - BedSinkCm;
            }
        }
        return -300.0f - BedSinkCm;
    };

    for (int32 Y = 0; Y < GridN; ++Y)
    {
        for (int32 X = 0; X < GridN; ++X)
        {
            const int32 Index = Y * GridN + X;
            const float WorldX = GridOriginCm.X + X * VertexSpacingMeters * kBedCmPerM;
            const float WorldY = GridOriginCm.Y + Y * VertexSpacingMeters * kBedCmPerM;
            Vertices[Index] = FVector(WorldX, WorldY, BedZCm(WorldX, WorldY));
            // World-aligned material ignores UVs, but provide sane ones anyway.
            UVs[Index] = FVector2D(WorldX / (8.0f * kBedCmPerM), WorldY / (8.0f * kBedCmPerM));
            VertexColors[Index] = FLinearColor::White;
            Tangents[Index] = FProcMeshTangent(1.0f, 0.0f, 0.0f);
            Normals[Index] = FVector::UpVector;
        }
    }

    // Central-difference normals from the sampled heightfield.
    const float StepCm = VertexSpacingMeters * kBedCmPerM;
    for (int32 Y = 0; Y < GridN; ++Y)
    {
        for (int32 X = 0; X < GridN; ++X)
        {
            const int32 Index = Y * GridN + X;
            const int32 XL = FMath::Max(X - 1, 0);
            const int32 XR = FMath::Min(X + 1, GridN - 1);
            const int32 YD = FMath::Max(Y - 1, 0);
            const int32 YU = FMath::Min(Y + 1, GridN - 1);
            const float DzDx =
                (Vertices[Y * GridN + XR].Z - Vertices[Y * GridN + XL].Z) /
                (StepCm * static_cast<float>(FMath::Max(XR - XL, 1)));
            const float DzDy =
                (Vertices[YU * GridN + X].Z - Vertices[YD * GridN + X].Z) /
                (StepCm * static_cast<float>(FMath::Max(YU - YD, 1)));
            Normals[Index] = FVector(-DzDx, -DzDy, 1.0f).GetSafeNormal();
            Tangents[Index] = FProcMeshTangent(
                FVector(1.0f, 0.0f, DzDx).GetSafeNormal(), false);
        }
    }

    for (int32 Y = 0; Y < GridN - 1; ++Y)
    {
        for (int32 X = 0; X < GridN - 1; ++X)
        {
            const int32 I0 = Y * GridN + X;
            const int32 I1 = I0 + 1;
            const int32 I2 = I0 + GridN;
            const int32 I3 = I2 + 1;
            Triangles.Add(I0); Triangles.Add(I2); Triangles.Add(I1);
            Triangles.Add(I1); Triangles.Add(I2); Triangles.Add(I3);
        }
    }

    BedMesh->CreateMeshSection_LinearColor(
        0, Vertices, Triangles, Normals, UVs, VertexColors, Tangents,
        /*bCreateCollision=*/false);
    if (TerrainMaterial != nullptr)
    {
        BedMesh->SetMaterial(0, TerrainMaterial);
    }
}
