#include "RaftSimWaterSurfaceActor.h"

#include "Async/ParallelFor.h"
#include "Engine/World.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformTime.h"
#include "Misc/Crc.h"
#include "ProfilingDebugging/CsvProfiler.h"
#include "RaftSimShorelineMeshComponent.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "RaftSimWaterSourcePacking.h"

// Render-only far field for the Cartesian single-surface river.
//
// The live carrier is a raft-centred square (224 m on South Fork) and the
// authored static band meshes are hidden in play, so nothing drew the river
// beyond about 112 m: elevated and downstream views showed the water ending
// in a straight line over dry bed. This ring draws the SAME cooked state the
// carrier already falls back to outside the live crop (the verified shared
// Cartesian atlas: bed, depth and velocity of the cooked field) on a coarser
// lattice, with the carrier's material instance and vertex encoding, and cuts
// a hole where the carrier is. It never feeds physics, support, buoyancy, D3,
// D4 or any sampler, and it carries no solver-evolved state: it is the cooked
// field, not live water.
static TAutoConsoleVariable<int32> CVarRaftSimFarFieldWater(
    TEXT("raftsim.FarFieldWater"), 1,
    TEXT("Render the cooked-atlas water ring beyond the live Cartesian carrier (South Fork full reach)."),
    ECVF_Default);
static TAutoConsoleVariable<float> CVarRaftSimFarFieldWaterSpacingM(
    TEXT("raftsim.FarFieldWaterSpacingM"), 4.0f,
    TEXT("Far-field water lattice spacing in metres (1-16)."),
    ECVF_Default);
static TAutoConsoleVariable<float> CVarRaftSimFarFieldWaterRadiusM(
    TEXT("raftsim.FarFieldWaterRadiusM"), 640.0f,
    TEXT("Half extent of the far-field water square around the carrier centre, metres."),
    ECVF_Default);
static TAutoConsoleVariable<float> CVarRaftSimFarFieldWaterDropCm(
    TEXT("raftsim.FarFieldWaterDropCm"), 3.0f,
    TEXT("Far-field water sits this far below the cooked surface so the live carrier wins where they overlap."),
    ECVF_Default);

CSV_DEFINE_CATEGORY(RaftSimFarField, true);

namespace
{
constexpr float kFarFieldTextureRepeatMeters = 3.0f; // Matches the carrier's UV0 repeat.
constexpr float kFarFieldMinimumDepthM = 1.0e-4f;    // Same presentation wet threshold as the atlas sampler.
}

int32 ARaftSimWaterSurfaceActor::GetFarFieldWaterTriangleCount() const
{
    return CartesianFarFieldMesh && CartesianFarFieldMesh->IsVisible()
        ? CartesianFarFieldMesh->GetWaterIndices().Num() / 3 : 0;
}

void ARaftSimWaterSurfaceActor::HideCartesianFarFieldWater()
{
    bFarFieldWaterKeyValid = false;
    if (CartesianFarFieldMesh && CartesianFarFieldMesh->IsVisible())
    {
        CartesianFarFieldMesh->SetVisibility(false);
    }
}

void ARaftSimWaterSurfaceActor::UpdateCartesianFarFieldWater(float CarrierDrawCoverage)
{
    CSV_SCOPED_TIMING_STAT(RaftSimFarField, Update);
    const int32 N = GridStationN * GridLateralN;
    const bool bEnabled = CVarRaftSimFarFieldWater.GetValueOnGameThread() != 0 &&
        bCartesianFarFieldScene && CartesianFarFieldMesh && CartesianShorelineMesh &&
        CartesianShorelineMesh->IsVisible() && WaterAdapter &&
        WaterAdapter->HasCartesianWaterCoordinates() && bUsesCurvedRiverCoordinates &&
        bSingleLiveWaterSurfaceEnabled && GridStationN > 1 && GridLateralN > 1 &&
        RiverCoordinatesM.Num() == N && CartesianShoreAvailable.Num() == N;
    if (!bEnabled)
    {
        HideCartesianFarFieldWater();
        return;
    }
    // Where the carrier can draw: it has a live or baseline sample and its
    // station edge coverage passes the same threshold its wet mask uses. The
    // carrier's outer station rows (about 20 m) are never drawn, so a hole cut
    // from its square alone left a dry strip along those two sides. A dry
    // verdict inside the drawable region stays the carrier's decision.
    TArray<int32> UndrawnPrefix;
    uint32 DrawableCrc = 0;
    {
        CSV_SCOPED_TIMING_STAT(RaftSimFarField, CarrierMask);
        TArray<float> StationCoverage;
        StationCoverage.SetNumUninitialized(GridStationN);
        for (int32 X = 0; X < GridStationN; ++X) StationCoverage[X] = StationEdgeCoverage(X);
        TArray<uint8> Drawable;
        Drawable.SetNumUninitialized(N);
        for (int32 I = 0; I < N; ++I)
        {
            Drawable[I] = CartesianShoreAvailable[I] &&
                StationCoverage[I % GridStationN] >= CarrierDrawCoverage ? 1 : 0;
        }
        DrawableCrc = FCrc::MemCrc32(Drawable.GetData(), Drawable.Num());
        // Inclusive 2-D prefix count of undrawable carrier vertices.
        const int32 PX = GridStationN + 1;
        UndrawnPrefix.SetNumZeroed(PX * (GridLateralN + 1));
        for (int32 Y = 0; Y < GridLateralN; ++Y)
        {
            int32 Row = 0;
            for (int32 X = 0; X < GridStationN; ++X)
            {
                Row += Drawable[Y * GridStationN + X] ? 0 : 1;
                UndrawnPrefix[(Y + 1) * PX + X + 1] = UndrawnPrefix[Y * PX + X + 1] + Row;
            }
        }
    }
    FBox2D DomainM;
    if (!WaterAdapter->GetCartesianWaterBoundsM(DomainM))
    {
        HideCartesianFarFieldWater();
        return;
    }
    const float SpacingM = FMath::Clamp(CVarRaftSimFarFieldWaterSpacingM.GetValueOnGameThread(), 1.0f, 16.0f);
    const float RadiusM = FMath::Clamp(CVarRaftSimFarFieldWaterRadiusM.GetValueOnGameThread(), 128.0f, 2048.0f);
    const float DropCm = FMath::Clamp(CVarRaftSimFarFieldWaterDropCm.GetValueOnGameThread(), 0.0f, 50.0f);
    // The carrier's actual lattice corners, in hydraulic east/north metres.
    const FVector2D NearMin = RiverCoordinatesM[0];
    const FVector2D NearMax = RiverCoordinatesM[N - 1];
    const FFarFieldWaterKey Key{NearMin, NearMax, WaterTextureOriginMeters, SpacingM, RadiusM, DropCm, DrawableCrc};
    if (bFarFieldWaterKeyValid && Key == FarFieldWaterKey)
    {
        return;
    }
    const double StartSeconds = FPlatformTime::Seconds();

    // Global lattice: the same world points are re-sampled after every
    // carrier recentre, so the ring never swims; only the hole and the outer
    // rim move.
    const FVector2D Centre = 0.5 * (NearMin + NearMax);
    const double OriginX = FMath::FloorToDouble((Centre.X - RadiusM) / SpacingM) * SpacingM;
    const double OriginY = FMath::FloorToDouble((Centre.Y - RadiusM) / SpacingM) * SpacingM;
    const int32 Nx = FMath::CeilToInt(2.0 * RadiusM / SpacingM) + 2;
    const int32 Ny = Nx;
    const int32 Count = Nx * Ny;
    // A far vertex is unavailable (dropping every far cell that touches it)
    // only when every carrier vertex within one far cell plus one carrier
    // cell of it is drawable. Any point the carrier cannot draw therefore lies
    // in a kept far cell, and kept cells overlap drawn carrier water by at
    // most one far cell, DropCm beneath it.
    const double NearSpacingM = FMath::Max(double(ResolvedVertexSpacingMeters), 1.0e-3);
    const double HoleReachM = SpacingM + NearSpacingM;
    const auto IsHole = [&](const FVector2D& P)
    {
        const int32 X0 = FMath::CeilToInt((P.X - HoleReachM - NearMin.X) / NearSpacingM - 1.0e-6);
        const int32 X1 = FMath::FloorToInt((P.X + HoleReachM - NearMin.X) / NearSpacingM + 1.0e-6);
        const int32 Y0 = FMath::CeilToInt((P.Y - HoleReachM - NearMin.Y) / NearSpacingM - 1.0e-6);
        const int32 Y1 = FMath::FloorToInt((P.Y + HoleReachM - NearMin.Y) / NearSpacingM + 1.0e-6);
        if (X0 < 0 || Y0 < 0 || X1 >= GridStationN || Y1 >= GridLateralN || X0 > X1 || Y0 > Y1) return false;
        const int32 PX = GridStationN + 1;
        const int32 Undrawn = UndrawnPrefix[(Y1 + 1) * PX + X1 + 1] - UndrawnPrefix[Y0 * PX + X1 + 1] -
            UndrawnPrefix[(Y1 + 1) * PX + X0] + UndrawnPrefix[Y0 * PX + X0];
        return Undrawn == 0;
    };
    const double YSign = WaterAdapter->GetRiverWorldYSign();

    TArray<FVector> Positions; Positions.SetNumUninitialized(Count);
    TArray<FVector> VertexNormals; VertexNormals.SetNumUninitialized(Count);
    TArray<FLinearColor> Colors; Colors.SetNumUninitialized(Count);
    TArray<FVector2D> TextureUVs; TextureUVs.SetNumUninitialized(Count);
    TArray<FVector2D> Flow; Flow.SetNumUninitialized(Count);
    TArray<FVector2D> Wake; Wake.SetNumZeroed(Count);
    TArray<FProcMeshTangent> VertexTangents;
    VertexTangents.Init(FProcMeshTangent(FVector::ForwardVector, YSign < 0.0), Count);
    TArray<uint8> Wet; Wet.SetNumZeroed(Count);
    TArray<uint8> Available; Available.SetNumZeroed(Count);
    TArray<float> DepthM; DepthM.SetNumZeroed(Count);
    TArray<float> BedM; BedM.SetNumZeroed(Count);
    TArray<uint8> SampledRows; SampledRows.SetNumZeroed(Ny);
    {
        CSV_SCOPED_TIMING_STAT(RaftSimFarField, Sample);
        ParallelFor(TEXT("RaftSimFarFieldSample"), Ny, 1, [&](int32 Y)
        {
            for (int32 X = 0; X < Nx; ++X)
            {
                const int32 I = Y * Nx + X;
                const FVector2D P(OriginX + X * double(SpacingM), OriginY + Y * double(SpacingM));
                Positions[I] = FVector(P.X * 100.0, YSign * P.Y * 100.0, 0.0);
                VertexNormals[I] = FVector::UpVector;
                Colors[I] = FLinearColor(0.f, 0.f, 0.f, 0.f);
                TextureUVs[I] = (P - WaterTextureOriginMeters) / kFarFieldTextureRepeatMeters;
                Flow[I] = FVector2D::ZeroVector;
                if (!DomainM.IsInsideOrOn(P)) continue;
                if (IsHole(P)) continue;
                FRaftSimWaterSample Sample;
                if (!WaterAdapter->SamplePresentationBaselineFieldAtRiverCoordinates(P, Sample, true)) continue;
                SampledRows[Y] = 1;
                Available[I] = 1;
                const bool bWet = Sample.bWet && Sample.DepthMeters > kFarFieldMinimumDepthM;
                Wet[I] = bWet ? 1 : 0;
                DepthM[I] = bWet ? Sample.DepthMeters : 0.0f;
                BedM[I] = Sample.BedHeightMeters;
                Positions[I].Z = (bWet ? Sample.SurfaceHeightMeters : Sample.BedHeightMeters) * 100.0 - DropCm;
                const FVector2D Velocity(Sample.VelocityMetersPerSecond.X, Sample.VelocityMetersPerSecond.Y);
                Flow[I] = bWet ? Velocity : FVector2D::ZeroVector;
                // R foam, G depth, B speed, A wet: the carrier's channel
                // meanings. No foam is invented for cooked-only water.
                Colors[I] = FLinearColor(
                    0.0f,
                    FMath::Clamp(DepthM[I] / 4.0f, 0.0f, 1.0f),
                    bWet ? FMath::Clamp(float(Velocity.Size()) / 8.0f, 0.0f, 1.0f) : 0.0f,
                    bWet ? 1.0f : 0.0f);
            }
        });
    }
    int32 SampledRowCount = 0;
    for (uint8 Row : SampledRows) SampledRowCount += Row;
    if (SampledRowCount == 0)
    {
        // A streaming handoff can leave no presentation source for a moment.
        // Keep the previous ring and retry on the next refresh.
        return;
    }
    {
        CSV_SCOPED_TIMING_STAT(RaftSimFarField, Normals);
        const double TwoCellsCm = 2.0 * SpacingM * 100.0;
        ParallelFor(TEXT("RaftSimFarFieldNormals"), Ny, 4, [&](int32 Y)
        {
            for (int32 X = 0; X < Nx; ++X)
            {
                const int32 I = Y * Nx + X;
                if (!Wet[I]) continue;
                const auto Height = [&](int32 NX, int32 NY)
                {
                    if (NX < 0 || NY < 0 || NX >= Nx || NY >= Ny) return Positions[I].Z;
                    const int32 J = NY * Nx + NX;
                    return Wet[J] ? Positions[J].Z : Positions[I].Z;
                };
                const double DzDx = (Height(X + 1, Y) - Height(X - 1, Y)) / TwoCellsCm;
                // Rows advance hydraulic north; world Y is YSign * north.
                const double DzDy = YSign * (Height(X, Y + 1) - Height(X, Y - 1)) / TwoCellsCm;
                VertexNormals[I] = FVector(-DzDx, -DzDy, 1.0).GetSafeNormal();
            }
        });
    }
    TArray<FProcMeshVertex> Source;
    {
        CSV_SCOPED_TIMING_STAT(RaftSimFarField, Pack);
        if (!RaftSimWaterSourcePacking::Pack(Positions, VertexNormals, Colors, TextureUVs, Flow, Wake,
                VertexTangents, Source, true, Flow))
        {
            return;
        }
    }
    UMaterialInterface* CarrierMaterial = LiveVolumeCoreMesh ? LiveVolumeCoreMesh->GetMaterial(0) : nullptr;
    if (CarrierMaterial && CartesianFarFieldMesh->GetMaterial(0) != CarrierMaterial)
    {
        CartesianFarFieldMesh->SetMaterial(0, CarrierMaterial);
    }
    bool bSubmitted = false;
    {
        CSV_SCOPED_TIMING_STAT(RaftSimFarField, Submit);
        bSubmitted = CartesianFarFieldMesh->SetClippedWaterMesh(Nx, Ny, MoveTemp(Source),
            Wet, Available, DepthM, BedM, nullptr);
    }
    if (!bSubmitted)
    {
        UE_LOG(LogTemp, Warning, TEXT("RaftSim far-field water submission refused (%d x %d)"), Nx, Ny);
        return;
    }
    if (!CartesianFarFieldMesh->IsVisible())
    {
        CartesianFarFieldMesh->SetVisibility(true);
    }
    FarFieldWaterKey = Key;
    bFarFieldWaterKeyValid = true;
    ++FarFieldWaterBuildCount;
    LastFarFieldWaterBuildMs = (FPlatformTime::Seconds() - StartSeconds) * 1000.0;
    if (FarFieldWaterBuildCount == 1 || FarFieldWaterBuildCount % 32 == 0)
    {
        UE_LOG(LogTemp, Display,
            TEXT("RaftSim far-field water: build=%d lattice=%dx%d spacing_m=%.1f radius_m=%.0f triangles=%d ms=%.3f"),
            FarFieldWaterBuildCount, Nx, Ny, SpacingM, RadiusM,
            CartesianFarFieldMesh->GetWaterIndices().Num() / 3, LastFarFieldWaterBuildMs);
    }
}
