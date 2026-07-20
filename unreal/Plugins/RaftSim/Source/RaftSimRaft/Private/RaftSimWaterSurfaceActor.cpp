#include "RaftSimWaterSurfaceActor.h"

#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "Materials/MaterialInterface.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimPhysicsBridgeSubsystem.h"
#include "RaftSimRaftActor.h"
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
    bUsesCurvedRiverCoordinates = WaterAdapter && WaterAdapter->HasRiverCoordinateMap();
    GridStationN = FMath::Max(
        2, FMath::RoundToInt(
            (bUsesCurvedRiverCoordinates ? CurvedGridLengthMeters : GridSizeMeters) /
            VertexSpacingMeters) + 1);
    GridLateralN = FMath::Max(
        2, FMath::RoundToInt(
            (bUsesCurvedRiverCoordinates ? CurvedGridWidthMeters : GridSizeMeters) /
            VertexSpacingMeters) + 1);
    const int32 VertCount = GridStationN * GridLateralN;
    Vertices.SetNum(VertCount);
    RiverCoordinatesM.SetNum(VertCount);
    Normals.SetNum(VertCount);
    UVs.SetNum(VertCount);
    VertexColors.SetNum(VertCount);
    Tangents.SetNum(VertCount);
    Triangles.Reset((GridStationN - 1) * (GridLateralN - 1) * 6);

    // Grid actor sits at world origin; vertices are in world cm relative to it.
    SetActorLocation(FVector::ZeroVector);

    if (bUsesCurvedRiverCoordinates)
    {
        TActorIterator<ARaftSimRaftActor> RaftIt(GetWorld());
        if (RaftIt)
        {
            FVector2D RiverPosition;
            FVector Tangent;
            FVector LeftNormal;
            if (WaterAdapter->WorldToRiverCoordinates(
                    RaftIt->GetActorLocation(), RiverPosition, Tangent, LeftNormal))
            {
                CurvedGridCenterStationM = RiverPosition.X;
            }
        }
        ClampCurvedGridCenter();
    }

    for (int32 LateralIndex = 0; LateralIndex < GridLateralN; ++LateralIndex)
    {
        for (int32 StationIndex = 0; StationIndex < GridStationN; ++StationIndex)
        {
            const int32 Index = LateralIndex * GridStationN + StationIndex;
            if (bUsesCurvedRiverCoordinates)
            {
                const float StationM = CurvedGridCenterStationM - CurvedGridLengthMeters * 0.5f +
                    StationIndex * VertexSpacingMeters;
                const float LateralM = -CurvedGridWidthMeters * 0.5f +
                    LateralIndex * VertexSpacingMeters;
                RiverCoordinatesM[Index] = FVector2D(StationM, LateralM);
                // Populated in one pass below so tangents can be derived from
                // adjacent curved-world vertices as well as positions.
                Vertices[Index] = FVector::ZeroVector;
            }
            else
            {
                const float WorldX = GridOriginCm.X +
                    StationIndex * VertexSpacingMeters * kSurfCmPerM;
                const float WorldY = GridOriginCm.Y +
                    LateralIndex * VertexSpacingMeters * kSurfCmPerM;
                Vertices[Index] = FVector(WorldX, WorldY, 0.0f);
                RiverCoordinatesM[Index] = FVector2D(
                    WorldX / kSurfCmPerM, WorldY / kSurfCmPerM);
            }
            Normals[Index] = FVector::UpVector;
            UVs[Index] = FVector2D(
                static_cast<float>(StationIndex) / (GridStationN - 1),
                static_cast<float>(LateralIndex) / (GridLateralN - 1));
            VertexColors[Index] = FLinearColor(0.0f, 0.0f, 0.0f, 1.0f);
            Tangents[Index] = FProcMeshTangent(1.0f, 0.0f, 0.0f);
        }
    }

    if (bUsesCurvedRiverCoordinates)
    {
        UpdateCurvedGridPlanarGeometry();
    }

    for (int32 Y = 0; Y < GridLateralN - 1; ++Y)
    {
        for (int32 X = 0; X < GridStationN - 1; ++X)
        {
            const int32 I0 = Y * GridStationN + X;
            const int32 I1 = I0 + 1;
            const int32 I2 = I0 + GridStationN;
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

void ARaftSimWaterSurfaceActor::RecenterCurvedGrid()
{
    if (!bUsesCurvedRiverCoordinates || !WaterAdapter)
    {
        return;
    }
    float DesiredCenterStationM = CurvedGridCenterStationM;
    TActorIterator<ARaftSimRaftActor> RaftIt(GetWorld());
    if (RaftIt)
    {
        FVector2D RiverPosition;
        FVector Tangent;
        FVector LeftNormal;
        if (WaterAdapter->WorldToRiverCoordinates(
                RaftIt->GetActorLocation(), RiverPosition, Tangent, LeftNormal))
        {
            DesiredCenterStationM = RiverPosition.X;
        }
    }
    if (FMath::Abs(DesiredCenterStationM - CurvedGridCenterStationM) <
        CurvedGridRecenterDistanceMeters)
    {
        return;
    }
    CurvedGridCenterStationM = DesiredCenterStationM;
    ClampCurvedGridCenter();
    for (int32 LateralIndex = 0; LateralIndex < GridLateralN; ++LateralIndex)
    {
        for (int32 StationIndex = 0; StationIndex < GridStationN; ++StationIndex)
        {
            const int32 Index = LateralIndex * GridStationN + StationIndex;
            RiverCoordinatesM[Index] = FVector2D(
                CurvedGridCenterStationM - CurvedGridLengthMeters * 0.5f +
                    StationIndex * VertexSpacingMeters,
                -CurvedGridWidthMeters * 0.5f + LateralIndex * VertexSpacingMeters);
        }
    }
    UpdateCurvedGridPlanarGeometry();
}

void ARaftSimWaterSurfaceActor::ClampCurvedGridCenter()
{
    float MinimumStationM = 0.0f;
    float MaximumStationM = 0.0f;
    if (!WaterAdapter ||
        !WaterAdapter->GetRiverStationRangeM(MinimumStationM, MaximumStationM))
    {
        return;
    }
    const float HalfLengthM = CurvedGridLengthMeters * 0.5f;
    if (MaximumStationM - MinimumStationM <= CurvedGridLengthMeters)
    {
        CurvedGridCenterStationM = 0.5f * (MinimumStationM + MaximumStationM);
        return;
    }
    CurvedGridCenterStationM = FMath::Clamp(
        CurvedGridCenterStationM,
        MinimumStationM + HalfLengthM,
        MaximumStationM - HalfLengthM);
}

void ARaftSimWaterSurfaceActor::UpdateCurvedGridPlanarGeometry()
{
    for (int32 LateralIndex = 0; LateralIndex < GridLateralN; ++LateralIndex)
    {
        for (int32 StationIndex = 0; StationIndex < GridStationN; ++StationIndex)
        {
            const int32 Index = LateralIndex * GridStationN + StationIndex;
            FVector WorldPosition;
            const bool bMapped = WaterAdapter && WaterAdapter->RiverToWorldPosition(
                RiverCoordinatesM[Index], WaterAdapter->GetRiverVerticalDatumM(),
                WorldPosition);
            checkf(bMapped, TEXT("Clamped curved water grid left its coordinate-map domain"));
            Vertices[Index].X = WorldPosition.X;
            Vertices[Index].Y = WorldPosition.Y;
        }
    }

    // The material's flow basis follows the river rather than world X, which
    // prevents visible UV/normal-map direction changes around tight bends.
    for (int32 LateralIndex = 0; LateralIndex < GridLateralN; ++LateralIndex)
    {
        for (int32 StationIndex = 0; StationIndex < GridStationN; ++StationIndex)
        {
            const int32 PreviousStationIndex = FMath::Max(StationIndex - 1, 0);
            const int32 NextStationIndex = FMath::Min(StationIndex + 1, GridStationN - 1);
            const FVector& Previous = Vertices[
                LateralIndex * GridStationN + PreviousStationIndex];
            const FVector& Next = Vertices[
                LateralIndex * GridStationN + NextStationIndex];
            const FVector FlowTangent = FVector(
                Next.X - Previous.X, Next.Y - Previous.Y, 0.0f).GetSafeNormal();
            Tangents[LateralIndex * GridStationN + StationIndex] =
                FProcMeshTangent(FlowTangent, false);
        }
    }
}

void ARaftSimWaterSurfaceActor::RefreshSurface()
{
    RecenterCurvedGrid();
    for (int32 Y = 0; Y < GridLateralN; ++Y)
    {
        for (int32 X = 0; X < GridStationN; ++X)
        {
            const int32 Index = Y * GridStationN + X;
            const FVector& V = Vertices[Index];
            // Dry cells are pushed 1.5 m below the bed so they hide under the
            // terrain rather than rendering as a flat sheet that the banks poke
            // through; only the genuinely wet channel shows water.
            float SurfaceZCm = -1.0e5f;
            FVector NormalOut = FVector::UpVector;
            float Foam = 0.0f;

            float DepthNorm = 0.0f;
            float SpeedNorm = 0.0f;
            if (WaterAdapter != nullptr)
            {
                FRaftSimWaterSample Sample;
                const bool bSampled = bUsesCurvedRiverCoordinates
                    ? WaterAdapter->SampleWaterFieldAtRiverCoordinates(
                        RiverCoordinatesM[Index], Sample)
                    : WaterAdapter->SampleWaterAtWorldPosition(
                        FVector(V.X, V.Y, 0.0f), Sample);
                if (bSampled)
                {
                    if (Sample.bWet)
                    {
                        // The authored seasonal surface remains beneath this
                        // live solver patch. A 2 cm presentation lift prevents
                        // depth fighting without changing any physics sample.
                        SurfaceZCm = Sample.SurfaceHeightMeters * kSurfCmPerM + 2.0f;
                        if (bUsesCurvedRiverCoordinates)
                        {
                            const FVector FlowTangent = Tangents[Index].TangentX;
                            const FVector LeftNormal(
                                -FlowTangent.Y, FlowTangent.X, 0.0f);
                            NormalOut = (
                                FlowTangent * Sample.SurfaceNormal.X +
                                LeftNormal * Sample.SurfaceNormal.Y +
                                FVector::UpVector * Sample.SurfaceNormal.Z).GetSafeNormal();
                        }
                        else
                        {
                            NormalOut = Sample.SurfaceNormal.GetSafeNormal();
                        }
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
                    else
                    {
                        // Bury under the terrain (bed sits ~here); keeps the
                        // dry banks free of a stray water sheet.
                        SurfaceZCm = Sample.BedHeightMeters * kSurfCmPerM - 150.0f;
                    }
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
