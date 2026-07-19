#include "RaftSimWaterSurfaceActor.h"

#include "Engine/GameInstance.h"
#include "Materials/MaterialInterface.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
constexpr float kSurfCmPerM = 100.0f;
constexpr float kGravity = 9.80665f;
}

ARaftSimWaterSurfaceActor::ARaftSimWaterSurfaceActor()
{
    PrimaryActorTick.bCanEverTick = true;

    SurfaceMesh = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("SurfaceMesh"));
    SetRootComponent(SurfaceMesh);
    SurfaceMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    SurfaceMesh->bUseAsyncCooking = true;

    static ConstructorHelpers::FObjectFinder<UMaterialInterface> WaterMat(
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverWater.M_RaftSim_PhotorealRiverWater"));
    if (WaterMat.Succeeded())
    {
        WaterMaterial = WaterMat.Object;
    }
    else
    {
        // Fallback before the photoreal material is authored.
        static ConstructorHelpers::FObjectFinder<UMaterialInterface> FallbackMat(
            TEXT("/Game/RaftSim/Materials/LandscapeCandidates/M_RaftSim_SingleLayerWaterCandidate."
                 "M_RaftSim_SingleLayerWaterCandidate"));
        if (FallbackMat.Succeeded())
        {
            WaterMaterial = FallbackMat.Object;
        }
    }
}

void ARaftSimWaterSurfaceActor::BeginPlay()
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

    BuildGrid();
    RefreshSurface();
}

void ARaftSimWaterSurfaceActor::BuildGrid()
{
    GridN = FMath::Max(2, FMath::RoundToInt(GridSizeMeters / VertexSpacingMeters) + 1);
    const int32 VertCount = GridN * GridN;
    Vertices.SetNum(VertCount);
    Normals.SetNum(VertCount);
    UVs.SetNum(VertCount);
    VertexColors.SetNum(VertCount);
    Tangents.SetNum(VertCount);
    Triangles.Reset((GridN - 1) * (GridN - 1) * 6);

    // Grid actor sits at world origin; vertices are in world cm relative to it.
    SetActorLocation(FVector::ZeroVector);

    for (int32 Y = 0; Y < GridN; ++Y)
    {
        for (int32 X = 0; X < GridN; ++X)
        {
            const int32 Index = Y * GridN + X;
            const float WorldX = GridOriginCm.X + X * VertexSpacingMeters * kSurfCmPerM;
            const float WorldY = GridOriginCm.Y + Y * VertexSpacingMeters * kSurfCmPerM;
            Vertices[Index] = FVector(WorldX, WorldY, 0.0f);
            Normals[Index] = FVector::UpVector;
            UVs[Index] = FVector2D(
                static_cast<float>(X) / (GridN - 1), static_cast<float>(Y) / (GridN - 1));
            VertexColors[Index] = FLinearColor(0.0f, 0.0f, 0.0f, 1.0f);
            Tangents[Index] = FProcMeshTangent(1.0f, 0.0f, 0.0f);
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

    SurfaceMesh->CreateMeshSection_LinearColor(
        0, Vertices, Triangles, Normals, UVs, VertexColors, Tangents,
        /*bCreateCollision=*/false);
    if (WaterMaterial != nullptr)
    {
        SurfaceMesh->SetMaterial(0, WaterMaterial);
    }
}

void ARaftSimWaterSurfaceActor::RefreshSurface()
{
    for (int32 Y = 0; Y < GridN; ++Y)
    {
        for (int32 X = 0; X < GridN; ++X)
        {
            const int32 Index = Y * GridN + X;
            const FVector& V = Vertices[Index];
            float SurfaceZCm = 0.0f;
            FVector NormalOut = FVector::UpVector;
            float Foam = 0.0f;

            float DepthNorm = 0.0f;
            float SpeedNorm = 0.0f;
            if (WaterAdapter != nullptr)
            {
                FRaftSimWaterSample Sample;
                if (WaterAdapter->SampleWaterAtWorldPosition(
                        FVector(V.X, V.Y, 0.0f), Sample) &&
                    Sample.bWet)
                {
                    SurfaceZCm = Sample.SurfaceHeightMeters * kSurfCmPerM;
                    NormalOut = Sample.SurfaceNormal.GetSafeNormal();
                    const float Speed = Sample.VelocityMetersPerSecond.Size2D();
                    const float Depth = FMath::Max(Sample.DepthMeters, 0.05f);
                    // Froude number = speed / sqrt(g * depth). Foam only where
                    // the flow is genuinely supercritical (the holes and wave
                    // crests), not across all moderately fast water, so the
                    // whitewater stays tight to the real hydraulic features.
                    const float Froude = Speed / FMath::Sqrt(kGravity * Depth);
                    Foam = FMath::Clamp((Froude - 1.0f) / 1.1f, 0.0f, 1.0f);
                    // Depth (over ~4 m) drives the base-colour deepening; speed
                    // (over ~8 m/s) is available for flow-driven shading.
                    DepthNorm = FMath::Clamp(Sample.DepthMeters / 4.0f, 0.0f, 1.0f);
                    SpeedNorm = FMath::Clamp(Speed / 8.0f, 0.0f, 1.0f);
                }
            }

            Vertices[Index].Z = SurfaceZCm;
            Normals[Index] = NormalOut;
            // R = foam, G = depth, B = flow speed (consumed by the photoreal
            // water material for whitewater, depth colour, and flow response).
            VertexColors[Index] = FLinearColor(Foam, DepthNorm, SpeedNorm, 1.0f);
        }
    }

    SurfaceMesh->UpdateMeshSection_LinearColor(
        0, Vertices, Normals, UVs, VertexColors, Tangents);
}

void ARaftSimWaterSurfaceActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    TimeSinceRefresh += DeltaSeconds;
    if (TimeSinceRefresh >= RefreshIntervalSeconds)
    {
        TimeSinceRefresh = 0.0f;
        RefreshSurface();
    }
}
