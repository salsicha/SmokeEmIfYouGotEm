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

static TAutoConsoleVariable<float> CVarRaftSimFarFieldWaterFoam(
    TEXT("raftsim.FarFieldWaterFoam"), 1.0f,
    TEXT("Scale of the far ring's supercritical whitewater cue (0 disables)."),
    ECVF_Default);

CSV_DEFINE_CATEGORY(RaftSimFarField, true);

static TAutoConsoleVariable<int32> CVarRaftSimFarFieldReusePacking(
    TEXT("raftsim.FarFieldReusePacking"), 0,
    TEXT("Candidate Cartesian far-field source capacity reuse; default remains fresh until native and whole-frame qualification."),
    ECVF_Default);

namespace
{
constexpr float kFarFieldTextureRepeatMeters = 3.0f; // Matches the carrier's UV0 repeat.
constexpr float kFarFieldMinimumDepthM = 1.0e-4f;    // Same presentation wet threshold as the atlas sampler.
}

// One far-field lattice sampled on the game thread. Packing and shoreline
// clipping (up to ~23 ms of a South Fork refresh) use only these arrays and
// the far-field component, so a tick-driven rebuild runs them on a worker.
struct FRaftSimFarFieldBuild
{
    int32 Nx = 0, Ny = 0;
    TArray<FVector> Positions, Normals;
    TArray<FLinearColor> Colors;
    TArray<FVector2D> UVs, Flow, Wake;
    TArray<FProcMeshTangent> Tangents;
    TArray<uint8> Wet, Available;
    TArray<float> DepthM, BedM;
    double GameThreadMs = 0.0, WorkerMs = 0.0;
    bool bCurved = false, bComputed = false;
    int32 WetCount = 0;
    float SpacingM = 0.0f, RadiusM = 0.0f;
    FVector2D HoleStations = FVector2D::ZeroVector;
};

namespace
{
void LogFarFieldBuild(int32 BuildCount, const FRaftSimFarFieldBuild& Build, int32 Triangles, double Ms)
{
    if (Build.bCurved)
    {
        if (BuildCount <= 4 || BuildCount % 32 == 0)
        {
            UE_LOG(LogTemp, Display,
                TEXT("RaftSim curved far-field water: build=%d lattice=%dx%d spacing_m=%.1f hole_station=%.0f..%.0f wet=%d triangles=%d ms=%.3f"),
                BuildCount, Build.Nx, Build.Ny, Build.SpacingM, Build.HoleStations.X, Build.HoleStations.Y,
                Build.WetCount, Triangles, Ms);
        }
    }
    else if (BuildCount == 1 || BuildCount % 32 == 0)
    {
        UE_LOG(LogTemp, Display,
            TEXT("RaftSim far-field water: build=%d lattice=%dx%d spacing_m=%.1f radius_m=%.0f triangles=%d ms=%.3f"),
            BuildCount, Build.Nx, Build.Ny, Build.SpacingM, Build.RadiusM, Triangles, Ms);
    }
}
}

void ARaftSimWaterSurfaceActor::SubmitFarFieldBuild(
    const TSharedRef<FRaftSimFarFieldBuild, ESPMode::ThreadSafe>& Build, const FFarFieldWaterKey& Key)
{
    URaftSimShorelineMeshComponent* Mesh = CartesianFarFieldMesh;
    // The first publication (startup shaders) and the retained-scratch
    // candidate stay synchronous, as does every direct, non-tick call.
    if (bAllowBackgroundFarField && CVarRaftSimFarFieldReusePacking.GetValueOnGameThread() == 0 &&
        Mesh->GetActiveVertexCount() > 0)
    {
        PendingFarFieldBuild = Build;
        PendingFarFieldKey = Key;
        bDiscardPendingFarField = false;
        PendingFarFieldTask = UE::Tasks::Launch(UE_SOURCE_LOCATION, [Mesh, Build]
        {
            const double Begin = FPlatformTime::Seconds();
            TArray<FProcMeshVertex> Source;
            {
                CSV_SCOPED_TIMING_STAT(RaftSimFarField, Pack);
                Build->bComputed = RaftSimWaterSourcePacking::Pack(Build->Positions, Build->Normals, Build->Colors,
                    Build->UVs, Build->Flow, Build->Wake, Build->Tangents, Source, true, Build->Flow);
            }
            if (Build->bComputed)
            {
                CSV_SCOPED_TIMING_STAT(RaftSimFarField, Submit);
                Build->bComputed = Mesh->ComputeClippedWaterMesh(Build->Nx, Build->Ny, MoveTemp(Source),
                    Build->Wet, Build->Available, Build->DepthM, Build->BedM, nullptr);
            }
            Build->WorkerMs = (FPlatformTime::Seconds() - Begin) * 1000.0;
        });
        Mesh->SetPendingCompute(PendingFarFieldTask);
        return;
    }
    const double Begin = FPlatformTime::Seconds();
    TArray<FProcMeshVertex> FreshSource;
    auto& Source = CVarRaftSimFarFieldReusePacking.GetValueOnGameThread() != 0
        ? FarFieldSourcePackingScratch : FreshSource;
    {
        CSV_SCOPED_TIMING_STAT(RaftSimFarField, Pack);
        if (!RaftSimWaterSourcePacking::Pack(Build->Positions, Build->Normals, Build->Colors, Build->UVs,
                Build->Flow, Build->Wake, Build->Tangents, Source, true, Build->Flow))
        {
            return;
        }
    }
    bool bSubmitted = false;
    {
        CSV_SCOPED_TIMING_STAT(RaftSimFarField, Submit);
        bSubmitted = Mesh->SetClippedWaterMesh(Build->Nx, Build->Ny, MoveTemp(Source),
            Build->Wet, Build->Available, Build->DepthM, Build->BedM, nullptr);
    }
    if (!bSubmitted)
    {
        UE_LOG(LogTemp, Warning, TEXT("RaftSim %sfar-field water submission refused (%d x %d)"),
            Build->bCurved ? TEXT("curved ") : TEXT(""), Build->Nx, Build->Ny);
        return;
    }
    if (!Mesh->IsVisible())
    {
        Mesh->SetVisibility(true);
    }
    FarFieldWaterKey = Key;
    bFarFieldWaterKeyValid = true;
    ++FarFieldWaterBuildCount;
    LastFarFieldWaterBuildMs = Build->GameThreadMs + (FPlatformTime::Seconds() - Begin) * 1000.0;
    LogFarFieldBuild(FarFieldWaterBuildCount, *Build, Mesh->GetWaterIndices().Num() / 3, LastFarFieldWaterBuildMs);
}

bool ARaftSimWaterSurfaceActor::FinishFarFieldBuild(bool bWait)
{
    if (!PendingFarFieldBuild) return true;
    if (!bWait && !PendingFarFieldTask.IsCompleted()) return false;
    PendingFarFieldTask.Wait();
    const TSharedRef<FRaftSimFarFieldBuild, ESPMode::ThreadSafe> Build = PendingFarFieldBuild.ToSharedRef();
    PendingFarFieldBuild.Reset();
    URaftSimShorelineMeshComponent* Mesh = CartesianFarFieldMesh;
    if (!Mesh) return true;
    Mesh->ClearPendingCompute();
    if (!Build->bComputed)
    {
        UE_LOG(LogTemp, Warning, TEXT("RaftSim %sfar-field water submission refused (%d x %d)"),
            Build->bCurved ? TEXT("curved ") : TEXT(""), Build->Nx, Build->Ny);
        return true;
    }
    Mesh->FinishClippedWaterMesh();
    // Hidden while it was building: the next enabled update rebuilds.
    if (bDiscardPendingFarField) return true;
    if (!Mesh->IsVisible())
    {
        Mesh->SetVisibility(true);
    }
    FarFieldWaterKey = PendingFarFieldKey;
    bFarFieldWaterKeyValid = true;
    ++FarFieldWaterBuildCount;
    LastFarFieldWaterBuildMs = Build->GameThreadMs + Build->WorkerMs;
    LogFarFieldBuild(FarFieldWaterBuildCount, *Build, Mesh->GetWaterIndices().Num() / 3, LastFarFieldWaterBuildMs);
    return true;
}

int32 ARaftSimWaterSurfaceActor::GetFarFieldWaterTriangleCount() const
{
    return CartesianFarFieldMesh && CartesianFarFieldMesh->IsVisible()
        ? CartesianFarFieldMesh->GetWaterIndices().Num() / 3 : 0;
}

void ARaftSimWaterSurfaceActor::HideCartesianFarFieldWater()
{
    bFarFieldWaterKeyValid = false;
    if (PendingFarFieldBuild) bDiscardPendingFarField = true;
    if (CartesianFarFieldMesh && CartesianFarFieldMesh->IsVisible())
    {
        CartesianFarFieldMesh->SetVisibility(false);
    }
}

void ARaftSimWaterSurfaceActor::UpdateCartesianFarFieldWater(float CarrierDrawCoverage)
{
    CSV_SCOPED_TIMING_STAT(RaftSimFarField, Update);
    // A background rebuild still running keeps the previous ring for now.
    if (!FinishFarFieldBuild(!bAllowBackgroundFarField)) return;
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
    const float FoamScale = FMath::Clamp(CVarRaftSimFarFieldWaterFoam.GetValueOnGameThread(), 0.0f, 1.0f);
    // The carrier's actual lattice corners, in hydraulic east/north metres.
    const FVector2D NearMin = RiverCoordinatesM[0];
    const FVector2D NearMax = RiverCoordinatesM[N - 1];
    const FFarFieldWaterKey Key{NearMin, NearMax, WaterTextureOriginMeters, SpacingM, RadiusM, DropCm, DrawableCrc, FoamScale};
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
                // meanings. Beyond the carrier there is no breaking or foam
                // transport, so distant rapids read as flat fast water. A
                // presentation cue aerates fast, near-critical cooked water
                // with the carrier generator's Froude onset (0.78); its
                // surface-roughness gate cannot be resolved on a 4 m lattice,
                // so a speed gate stands in (on the v2 cook, Fr > 0.8 with
                // v > 2 m/s marks 3-12% of rapid reaches and <= 1% of flats
                // and pools). Inferred appearance, not measured foam.
                const float Speed = float(Velocity.Size());
                const float Froude = bWet && Sample.DepthMeters > 0.05f
                    ? Speed / FMath::Sqrt(9.81f * Sample.DepthMeters) : 0.0f;
                const float FoamCue = FoamScale * 0.72f * FMath::SmoothStep(0.75f, 1.3f, Froude) *
                    FMath::SmoothStep(1.7f, 2.6f, Speed);
                Colors[I] = FLinearColor(
                    FoamCue,
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
    UMaterialInterface* CarrierMaterial = LiveVolumeCoreMesh ? LiveVolumeCoreMesh->GetMaterial(0) : nullptr;
    if (CarrierMaterial && CartesianFarFieldMesh->GetMaterial(0) != CarrierMaterial)
    {
        CartesianFarFieldMesh->SetMaterial(0, CarrierMaterial);
    }
    const auto Build = MakeShared<FRaftSimFarFieldBuild, ESPMode::ThreadSafe>();
    Build->Nx = Nx; Build->Ny = Ny;
    Build->Positions = MoveTemp(Positions); Build->Normals = MoveTemp(VertexNormals);
    Build->Colors = MoveTemp(Colors); Build->UVs = MoveTemp(TextureUVs);
    Build->Flow = MoveTemp(Flow); Build->Wake = MoveTemp(Wake); Build->Tangents = MoveTemp(VertexTangents);
    Build->Wet = MoveTemp(Wet); Build->Available = MoveTemp(Available);
    Build->DepthM = MoveTemp(DepthM); Build->BedM = MoveTemp(BedM);
    Build->SpacingM = SpacingM; Build->RadiusM = RadiusM;
    Build->GameThreadMs = (FPlatformTime::Seconds() - StartSeconds) * 1000.0;
    SubmitFarFieldBuild(Build, Key);
}

// Curved station/lateral maps (for example the 2.5 km geographic Hance reach)
// draw their live water on a raft-following strip that fades over its first
// and last 36 m. Beyond it, draw the cooked presentation baseline the strip
// already falls back to outside the solver crop, on a global station/lateral
// lattice mapped through the coordinate map, with the strip's own vertex
// encoding (UV0 station/lateral texture metres, UV1 flow in river axes,
// along-station tangents). A hole covers the strip's drawn rows; the kept
// cells overlap it by at most one far cell, DropCm below. Render only.
void ARaftSimWaterSurfaceActor::UpdateCurvedFarFieldWater(float CarrierDrawCoverage)
{
    CSV_SCOPED_TIMING_STAT(RaftSimFarField, CurvedUpdate);
    if (!FinishFarFieldBuild(!bAllowBackgroundFarField)) return;
    const int32 N = GridStationN * GridLateralN;
    const bool bEnabled = CVarRaftSimFarFieldWater.GetValueOnGameThread() != 0 &&
        bCurvedFarFieldScene && CartesianFarFieldMesh && LiveVolumeCoreMesh &&
        LiveVolumeCoreMesh->IsVisible() && WaterAdapter &&
        !WaterAdapter->HasCartesianWaterCoordinates() && bUsesCurvedRiverCoordinates &&
        bSingleLiveWaterSurfaceEnabled && GridStationN > 1 && GridLateralN > 1 &&
        RiverCoordinatesM.Num() == N;
    float MinimumStationM = 0.0f, MaximumStationM = 0.0f;
    if (!bEnabled || !WaterAdapter->GetRiverStationRangeM(MinimumStationM, MaximumStationM))
    {
        HideCartesianFarFieldWater();
        return;
    }
    // Station interval the strip draws (its rows at or above the core's
    // coverage threshold) and its lateral span.
    int32 FirstDrawn = INDEX_NONE, LastDrawn = INDEX_NONE;
    for (int32 X = 0; X < GridStationN; ++X)
    {
        if (StationEdgeCoverage(X) >= CarrierDrawCoverage)
        {
            if (FirstDrawn == INDEX_NONE) FirstDrawn = X;
            LastDrawn = X;
        }
    }
    const float SpacingM = FMath::Clamp(CVarRaftSimFarFieldWaterSpacingM.GetValueOnGameThread(), 1.0f, 16.0f);
    const float DropCm = FMath::Clamp(CVarRaftSimFarFieldWaterDropCm.GetValueOnGameThread(), 0.0f, 50.0f);
    const float FoamScale = FMath::Clamp(CVarRaftSimFarFieldWaterFoam.GetValueOnGameThread(), 0.0f, 1.0f);
    const float StripMinN = float(RiverCoordinatesM[0].Y);
    const float StripMaxN = float(RiverCoordinatesM[(GridLateralN - 1) * GridStationN].Y);
    const FVector2D HoleMin = FirstDrawn == INDEX_NONE ? FVector2D(1.0e9, 1.0e9)
        : FVector2D(RiverCoordinatesM[FirstDrawn].X + SpacingM, StripMinN + SpacingM);
    const FVector2D HoleMax = FirstDrawn == INDEX_NONE ? FVector2D(-1.0e9, -1.0e9)
        : FVector2D(RiverCoordinatesM[LastDrawn].X - SpacingM, StripMaxN - SpacingM);
    FBox2D BaselineBounds;
    if (!WaterAdapter->GetCurvedPresentationBaselineBoundsM(BaselineBounds))
    {
        HideCartesianFarFieldWater();
        return;
    }
    // A continuous coordinate map may describe hundreds of kilometres while
    // the resident presentation source covers only a short connected reach.
    // Outside these bounds SamplePresentationBaselineField always returns false.
    // Retain a dry border cell for identical shoreline clipping and keep the
    // original globally aligned lattice; do not stretch or invent source water.
    MinimumStationM = FMath::Max(MinimumStationM, float(BaselineBounds.Min.X - SpacingM));
    MaximumStationM = FMath::Min(MaximumStationM, float(BaselineBounds.Max.X + SpacingM));
    const uint32 BoundsHash = HashCombine(GetTypeHash(MinimumStationM), GetTypeHash(MaximumStationM));
    const FFarFieldWaterKey Key{HoleMin, HoleMax, WaterTextureOriginMeters, SpacingM, 0.0f, DropCm, BoundsHash, FoamScale};
    if (bFarFieldWaterKeyValid && Key == FarFieldWaterKey)
    {
        return;
    }
    const double StartSeconds = FPlatformTime::Seconds();
    // Global lattice: fixed station/lateral nodes, so the far water never swims.
    const double MarginM = 32.0;
    const double S0 = FMath::FloorToDouble(MinimumStationM / SpacingM) * SpacingM;
    const double L0 = FMath::FloorToDouble((StripMinN - MarginM) / SpacingM) * SpacingM;
    const int32 Nx = FMath::FloorToInt((MaximumStationM - S0) / SpacingM) + 1;
    const int32 Ny = FMath::CeilToInt((StripMaxN + MarginM - L0) / SpacingM) + 1;
    if (Nx < 2 || Ny < 2)
    {
        HideCartesianFarFieldWater();
        return;
    }
    const int32 Count = Nx * Ny;
    const float DatumM = WaterAdapter->GetRiverVerticalDatumM();
    const bool bFlipBinormal = WaterAdapter->GetRiverWorldYSign() < 0.0;
    TArray<FVector> Positions; Positions.SetNumZeroed(Count);
    TArray<FVector> VertexNormals; VertexNormals.Init(FVector::UpVector, Count);
    TArray<FLinearColor> Colors; Colors.Init(FLinearColor(0.f, 0.f, 0.f, 0.f), Count);
    TArray<FVector2D> TextureUVs; TextureUVs.SetNumZeroed(Count);
    TArray<FVector2D> Flow; Flow.SetNumZeroed(Count);
    TArray<FVector2D> Wake; Wake.SetNumZeroed(Count);
    TArray<FProcMeshTangent> VertexTangents; VertexTangents.Init(FProcMeshTangent(FVector::ForwardVector, bFlipBinormal), Count);
    TArray<uint8> Wet; Wet.SetNumZeroed(Count);
    TArray<uint8> Available; Available.SetNumZeroed(Count);
    TArray<uint8> Mapped; Mapped.SetNumZeroed(Count);
    TArray<float> DepthM; DepthM.SetNumZeroed(Count);
    TArray<float> BedM; BedM.SetNumZeroed(Count);
    {
        CSV_SCOPED_TIMING_STAT(RaftSimFarField, CurvedSample);
        // Rows advance lateral (river-left), columns advance station, as the strip.
        ParallelFor(TEXT("RaftSimCurvedFarFieldSample"), Ny, 1, [&](int32 Y)
        {
            for (int32 X = 0; X < Nx; ++X)
            {
                const int32 I = Y * Nx + X;
                const FVector2D P(S0 + X * double(SpacingM), L0 + Y * double(SpacingM));
                TextureUVs[I] = (P - WaterTextureOriginMeters) / kFarFieldTextureRepeatMeters;
                FVector World;
                if (!WaterAdapter->RiverToWorldPosition(P, DatumM, World)) continue;
                Mapped[I] = 1;
                Positions[I] = World;
                if (P.X >= HoleMin.X && P.X <= HoleMax.X && P.Y >= HoleMin.Y && P.Y <= HoleMax.Y) continue;
                FRaftSimWaterSample Sample;
                if (!WaterAdapter->SamplePresentationBaselineFieldAtRiverCoordinates(P, Sample)) continue;
                const bool bWet = Sample.bWet && Sample.DepthMeters > kFarFieldMinimumDepthM;
                if (!bWet) continue;
                Available[I] = 1;
                Wet[I] = 1;
                DepthM[I] = Sample.DepthMeters;
                BedM[I] = Sample.BedHeightMeters;
                Positions[I].Z = Sample.SurfaceHeightMeters * 100.0 - DropCm;
                const FVector2D Velocity(Sample.VelocityMetersPerSecond.X, Sample.VelocityMetersPerSecond.Y);
                Flow[I] = Velocity;
                const float Speed = float(Velocity.Size());
                // The curved baseline stores one presentation energy per cell
                // and reports depth = lerp(0.8, 2.4, energy); its exporter
                // encodes cooked speed and Froude there, so read the
                // whitewater cue back from it (a Froude from these derived
                // depth/speed pairs never exceeds 0.58).
                const float Energy = FMath::Clamp((Sample.DepthMeters - 0.8f) / 1.6f, 0.0f, 1.0f);
                float FoamCue = FoamScale * 0.72f * FMath::SmoothStep(0.7f, 0.95f, Energy);
                if (ResolvedObservedWhitewaterGain > 0.0f)
                {
                    FoamCue = FMath::Max(FoamCue, FoamScale * ResolvedObservedWhitewaterGain *
                        WaterAdapter->SampleObservedWhitewaterAtRiverCoordinates(P));
                }
                Colors[I] = FLinearColor(FoamCue, FMath::Clamp(DepthM[I] / 4.0f, 0.0f, 1.0f),
                    FMath::Clamp(Speed / 8.0f, 0.0f, 1.0f), 1.0f);
            }
        });
    }
    int32 WetCount = 0;
    for (uint8 W : Wet) WetCount += W;
    if (WetCount == 0)
    {
        HideCartesianFarFieldWater();
        return;
    }
    // The curved baseline stores only wet cells. Give mapped dry vertices
    // beside water a nominal bank 0.25 m above their highest wet neighbour so
    // the shoreline clipper cuts cells instead of dropping them (a 4 m stair
    // along every bank). Hole vertices stay unavailable.
    {
        TArray<float> BankM; BankM.Init(-1.0e9f, Count);
        for (int32 Y = 0; Y < Ny; ++Y)
        {
            for (int32 X = 0; X < Nx; ++X)
            {
                const int32 I = Y * Nx + X;
                if (Wet[I] || !Mapped[I]) continue;
                const FVector2D P(S0 + X * double(SpacingM), L0 + Y * double(SpacingM));
                if (P.X >= HoleMin.X && P.X <= HoleMax.X && P.Y >= HoleMin.Y && P.Y <= HoleMax.Y) continue;
                for (int32 DY = -1; DY <= 1; ++DY)
                {
                    for (int32 DX = -1; DX <= 1; ++DX)
                    {
                        const int32 NX = X + DX, NY = Y + DY;
                        if (NX < 0 || NY < 0 || NX >= Nx || NY >= Ny) continue;
                        const int32 J = NY * Nx + NX;
                        if (Wet[J]) BankM[I] = FMath::Max(BankM[I], float((Positions[J].Z + DropCm) / 100.0) + 0.25f);
                    }
                }
            }
        }
        for (int32 I = 0; I < Count; ++I)
        {
            if (BankM[I] < -1.0e8f) continue;
            Available[I] = 1;
            BedM[I] = BankM[I];
            DepthM[I] = 0.0f;
            Positions[I].Z = BankM[I] * 100.0 - DropCm;
        }
    }
    {
        CSV_SCOPED_TIMING_STAT(RaftSimFarField, CurvedNormals);
        ParallelFor(TEXT("RaftSimCurvedFarFieldNormals"), Ny, 4, [&](int32 Y)
        {
            for (int32 X = 0; X < Nx; ++X)
            {
                const int32 I = Y * Nx + X;
                if (!Mapped[I]) continue;
                const auto At = [&](int32 NX, int32 NY)
                {
                    NX = FMath::Clamp(NX, 0, Nx - 1); NY = FMath::Clamp(NY, 0, Ny - 1);
                    const int32 J = NY * Nx + NX;
                    return Mapped[J] && Wet[J] ? Positions[J] : FVector(Mapped[J] ? Positions[J].X : Positions[I].X,
                        Mapped[J] ? Positions[J].Y : Positions[I].Y, Positions[I].Z);
                };
                const FVector Along = At(X + 1, Y) - At(X - 1, Y);
                const FVector Across = At(X, Y + 1) - At(X, Y - 1);
                const FVector Tangent = FVector(Along.X, Along.Y, 0.0).GetSafeNormal();
                VertexTangents[I] = FProcMeshTangent(Tangent.IsNearlyZero() ? FVector::ForwardVector : Tangent, bFlipBinormal);
                if (!Wet[I]) continue;
                FVector Normal = FVector::CrossProduct(Along, Across).GetSafeNormal();
                if (Normal.Z < 0.0) Normal = -Normal;
                VertexNormals[I] = Normal.IsNearlyZero() ? FVector::UpVector : Normal;
            }
        });
    }
    UMaterialInterface* CarrierMaterial = LiveVolumeCoreMesh->GetMaterial(0);
    if (CarrierMaterial && CartesianFarFieldMesh->GetMaterial(0) != CarrierMaterial)
    {
        CartesianFarFieldMesh->SetMaterial(0, CarrierMaterial);
    }
    const auto Build = MakeShared<FRaftSimFarFieldBuild, ESPMode::ThreadSafe>();
    Build->Nx = Nx; Build->Ny = Ny;
    Build->Positions = MoveTemp(Positions); Build->Normals = MoveTemp(VertexNormals);
    Build->Colors = MoveTemp(Colors); Build->UVs = MoveTemp(TextureUVs);
    Build->Flow = MoveTemp(Flow); Build->Wake = MoveTemp(Wake); Build->Tangents = MoveTemp(VertexTangents);
    Build->Wet = MoveTemp(Wet); Build->Available = MoveTemp(Available);
    Build->DepthM = MoveTemp(DepthM); Build->BedM = MoveTemp(BedM);
    Build->bCurved = true; Build->SpacingM = SpacingM; Build->WetCount = WetCount;
    Build->HoleStations = FVector2D(HoleMin.X, HoleMax.X);
    Build->GameThreadMs = (FPlatformTime::Seconds() - StartSeconds) * 1000.0;
    SubmitFarFieldBuild(Build, Key);
}
