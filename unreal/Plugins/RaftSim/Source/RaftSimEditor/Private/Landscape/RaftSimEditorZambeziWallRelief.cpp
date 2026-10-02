#include "Landscape/RaftSimEditorZambeziWallRelief.h"

#include "RaftSimTerrainRefinement.h"

namespace RaftSimEditorEnvironment
{
namespace
{
constexpr float WaterGridCellCm = 2500.0f;
constexpr float WaterGridReachCm = 50000.0f;
constexpr float WallReachCm = 48000.0f;
constexpr float SlopeBaselineCm = 625.0f;
// Wall cells of the 12.5 m tiles are split N x N (3.1 m): coarser cells
// zigzag diagonal ledge lines into rows of pocket-like shadows.
constexpr int32 SplitCount = 4;
}

bool FZambeziWallRelief::Initialize(
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    ALandscape* InLandscape,
    FString& OutSummary)
{
    Landscape = nullptr;
    WaterZ.Reset();
    RiverDistanceCm.Reset();
    TArray<FRaftSimLandscapeCandidateCenterlinePoint> Centerline;
    if (!InLandscape || !LoadLandscapeCandidateLocalCenterline(Candidate, Centerline, OutSummary) ||
        Centerline.Num() < 2)
    {
        OutSummary += TEXT("Zambezi wall ledges skipped: no Landscape or centreline.\n");
        return false;
    }
    GridMinX = GetLandscapeCandidateWorldMinX(Candidate);
    GridMinY = -Candidate.HorizontalSpanYCm * 0.5f;
    GridX = FMath::CeilToInt(Candidate.HorizontalSpanXCm / WaterGridCellCm) + 1;
    GridY = FMath::CeilToInt(Candidate.HorizontalSpanYCm / WaterGridCellCm) + 1;
    WaterZ.Init(0.0f, GridX * GridY);
    RiverDistanceCm.Init(TNumericLimits<float>::Max(), GridX * GridY);
    // The river's water surface along the run, written into every 25 m cell
    // within 500 m (nearest sample wins).
    constexpr int32 Samples = 6000;
    const int32 ReachCells = FMath::CeilToInt(WaterGridReachCm / WaterGridCellCm);
    for (int32 Sample = 0; Sample < Samples; ++Sample)
    {
        const float Progress = static_cast<float>(Sample) / static_cast<float>(Samples - 1);
        const FVector2D Point = SampleLandscapeCandidateCenterlineWorld(Candidate, Centerline, Progress);
        float SurfaceZ = 0.0f;
        const float SampleWaterZ = SampleLandscapeCandidateConditionedVisualSurfaceWorldZ(
                Candidate, Centerline, Progress, SurfaceZ)
            ? SurfaceZ + Candidate.PreviewSpec.FlowWaterLevelOffsetCm
            : Candidate.PreviewSpec.FlowWaterLevelOffsetCm;
        const int32 CX = FMath::RoundToInt((Point.X - GridMinX) / WaterGridCellCm);
        const int32 CY = FMath::RoundToInt((Point.Y - GridMinY) / WaterGridCellCm);
        for (int32 Y = FMath::Max(CY - ReachCells, 0); Y <= FMath::Min(CY + ReachCells, GridY - 1); ++Y)
        {
            for (int32 X = FMath::Max(CX - ReachCells, 0); X <= FMath::Min(CX + ReachCells, GridX - 1); ++X)
            {
                const FVector2D Cell(GridMinX + X * WaterGridCellCm, GridMinY + Y * WaterGridCellCm);
                const float Distance = FVector2D::Distance(Cell, Point);
                const int32 Index = Y * GridX + X;
                if (Distance <= WaterGridReachCm && Distance < RiverDistanceCm[Index])
                {
                    RiverDistanceCm[Index] = Distance;
                    WaterZ[Index] = SampleWaterZ;
                }
            }
        }
    }
    Landscape = InLandscape;
    return true;
}

float FZambeziWallRelief::RawHeightCm(float X, float Y, float Fallback) const
{
    return Landscape
        ? Landscape->GetHeightAtLocation(FVector(X, Y, 0.0f), EHeightfieldSource::Editor).Get(Fallback)
        : Fallback;
}

float FZambeziWallRelief::WeightAt(float X, float Y, float& OutRawZ, float* OutGradient) const
{
    OutRawZ = RawHeightCm(X, Y);
    if (OutGradient)
    {
        *OutGradient = 0.0f;
    }
    if (!IsValid())
    {
        return 0.0f;
    }
    const int32 CX = FMath::RoundToInt((X - GridMinX) / WaterGridCellCm);
    const int32 CY = FMath::RoundToInt((Y - GridMinY) / WaterGridCellCm);
    if (CX < 0 || CY < 0 || CX >= GridX || CY >= GridY)
    {
        return 0.0f;
    }
    const int32 Index = CY * GridX + CX;
    const float Distance = RiverDistanceCm[Index];
    if (Distance > WallReachCm)
    {
        return 0.0f;
    }
    // Clear of the water: the ledges fade in from 4 m to 14 m above it, so
    // the bank and the waterline boulders keep their ground.
    const float DryWeight = SmoothPreviewStep(400.0f, 1400.0f, OutRawZ - WaterZ[Index]);
    if (DryWeight <= 0.0f)
    {
        return 0.0f;
    }
    const float GradientX = (RawHeightCm(X + SlopeBaselineCm, Y, OutRawZ) -
        RawHeightCm(X - SlopeBaselineCm, Y, OutRawZ)) / (2.0f * SlopeBaselineCm);
    const float GradientY = (RawHeightCm(X, Y + SlopeBaselineCm, OutRawZ) -
        RawHeightCm(X, Y - SlopeBaselineCm, OutRawZ)) / (2.0f * SlopeBaselineCm);
    const float Gradient = FMath::Sqrt(GradientX * GradientX + GradientY * GradientY);
    if (OutGradient)
    {
        *OutGradient = Gradient;
    }
    const float SlopeDegrees = FMath::RadiansToDegrees(FMath::Atan(Gradient));
    return SmoothPreviewStep(20.0f, 32.0f, SlopeDegrees) * DryWeight *
        (1.0f - SmoothPreviewStep(38000.0f, WallReachCm, Distance));
}

float FZambeziWallRelief::ReliefCm(float X, float Y, float RawZ, float Weight, float Gradient) const
{
    if (Weight <= 0.0f)
    {
        return 0.0f;
    }
    const FVector2D P(X, Y);
    // Flow units of 9-14 m; ledge lines wander up to ~7 m along the wall
    // (buttresses and embayments); risers take 18-40 % of each unit.
    const float UnitCm = 1150.0f + 280.0f * FMath::PerlinNoise2D(P / 21000.0f + FVector2D(11.3f, 5.7f));
    const float WanderCm = 520.0f * FMath::PerlinNoise2D(P / 13000.0f + FVector2D(-3.1f, 8.9f)) +
        190.0f * FMath::PerlinNoise2D(P / 3600.0f + FVector2D(7.7f, -2.3f));
    // A riser spans Riser * Unit / Gradient horizontally; keep it at least
    // about 1.3 render cells (4 m) wide: narrower risers alias into rows of
    // pocket-like shadows on 35-45 deg walls seen from afar.
    const float AntiAliasRiser = 400.0f * FMath::Max(Gradient, 0.0f) / UnitCm;
    const float Riser = FMath::Clamp(FMath::Max(
        0.28f + 0.08f * FMath::PerlinNoise2D(P / 7000.0f + FVector2D(2.2f, 13.1f)), AntiAliasRiser), 0.18f, 0.85f);
    const float Phase = (RawZ + WanderCm) / UnitCm;
    const float T = Phase - FMath::FloorToFloat(Phase);
    const float S = T < Riser ? FMath::SmoothStep(0.0f, 1.0f, T / Riser) : 1.0f;
    // Zero mean over a unit: the riser averages Riser/2, the tread 1.
    const float Step = S - T - (0.5f - 0.5f * Riser);
    // Block-scale jointing on top of the banding.
    const float JointCm = 55.0f * FMath::PerlinNoise2D(P / 900.0f + FVector2D(4.4f, -6.6f));
    // Gullies and buttresses: V-valleyed noise in plan, which a steep face
    // stretches into vertical flutes (columnar-jointed basalt). Its 11-26 m
    // wavelengths are safe on the 3.1 m cells; strongest on the steepest
    // faces, where the ledges are softest.
    const float Steep = FMath::SmoothStep(0.0f, 1.0f, FMath::Clamp((Gradient - 0.55f) / 0.9f, 0.0f, 1.0f));
    const float FluteA = FMath::Abs(FMath::PerlinNoise2D(P / 1100.0f + FVector2D(-8.2f, 3.9f)));
    const float FluteB = FMath::Abs(FMath::PerlinNoise2D(P / 2600.0f + FVector2D(5.1f, 9.4f)));
    const float GullyCm = (90.0f + 330.0f * Steep) * (FluteA - 0.42f) + (60.0f + 200.0f * Steep) * (FluteB - 0.42f);
    return Weight * (UnitCm * Step + JointCm + GullyCm);
}

float FZambeziWallRelief::HeightWithReliefCm(float X, float Y, float Fallback) const
{
    if (!Landscape)
    {
        return Fallback;
    }
    const TOptional<float> Raw = Landscape->GetHeightAtLocation(FVector(X, Y, 0.0f), EHeightfieldSource::Editor);
    if (!Raw.IsSet())
    {
        return Fallback;
    }
    float RawZ = 0.0f;
    float Gradient = 0.0f;
    const float Weight = WeightAt(X, Y, RawZ, &Gradient);
    return RawZ + ReliefCm(X, Y, RawZ, Weight, Gradient);
}

int32 ApplyZambeziWallLedges(
    UWorld* World,
    ALandscape* Landscape,
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    FString& OutSummary)
{
    FZambeziWallRelief Relief;
    if (!World || !Relief.Initialize(Candidate, Landscape, OutSummary))
    {
        return 0;
    }
    static const FString DenseTerrainActorPrefix = TEXT("RaftSim_PhysicalCorridorDenseSourceTerrainTile_");
    FZambeziWallLedgeStats Stats;
    int32 Tiles = 0;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (!Actor || !Actor->GetActorLabel().StartsWith(DenseTerrainActorPrefix) ||
            !Actor->GetActorTransform().Equals(FTransform::Identity))
        {
            continue;
        }
        UProceduralMeshComponent* Mesh = Actor->FindComponentByClass<UProceduralMeshComponent>();
        const FProcMeshSection* Section = Mesh ? Mesh->GetProcMeshSection(0) : nullptr;
        if (!Section || Section->ProcVertexBuffer.Num() < 4 || Section->bEnableCollision)
        {
            continue;
        }
        TArray<FVector> Vertices;
        TArray<FVector> Normals;
        TArray<FVector2D> UVs;
        TArray<FLinearColor> Colors;
        TArray<int32> Triangles;
        for (const FProcMeshVertex& Vertex : Section->ProcVertexBuffer)
        {
            Vertices.Add(FVector(Vertex.Position));
            Normals.Add(FVector(Vertex.Normal));
            UVs.Add(FVector2D(Vertex.UV0));
            Colors.Add(Vertex.Color.ReinterpretAsLinear());
        }
        for (const uint32 Index : Section->ProcIndexBuffer)
        {
            Triangles.Add(static_cast<int32>(Index));
        }
        int32 RowSize = 0;
        while (RowSize < Vertices.Num() && FMath::IsNearlyEqual(Vertices[RowSize].Y, Vertices[0].Y, 0.1f))
        {
            ++RowSize;
        }
        if (RowSize < 2 || Vertices.Num() % RowSize != 0)
        {
            continue;
        }
        // Wall corners take their ledge height; every cell touching one is
        // split and its new vertices take theirs (computed once, here).
        const TArray<FVector> Base = Vertices;
        TArray<bool> WallCorner;
        WallCorner.Init(false, Vertices.Num());
        TArray<int32> WallCornerIndices;
        TArray<float> WallCornerZ;
        for (int32 Index = 0; Index < Vertices.Num(); ++Index)
        {
            float RawZ = 0.0f;
            float Gradient = 0.0f;
            const float Weight = Relief.WeightAt(Vertices[Index].X, Vertices[Index].Y, RawZ, &Gradient);
            if (Weight > 0.0f)
            {
                WallCorner[Index] = true;
                Vertices[Index].Z += Relief.ReliefCm(Vertices[Index].X, Vertices[Index].Y, RawZ, Weight, Gradient);
                WallCornerIndices.Add(Index);
                WallCornerZ.Add(static_cast<float>(Vertices[Index].Z));
            }
        }
        if (WallCornerIndices.IsEmpty())
        {
            continue;
        }
        TArray<float> FineZ;
        const int32 SplitCells = RaftSimTerrainRefinement::BuildRefinedGrid(
            RowSize, Vertices.Num() / RowSize, SplitCount, Base, WallCorner, Vertices, Normals, UVs, Colors,
            Triangles,
            [&Relief, &FineZ](int32, const FVector& BasePosition, bool bStraightEdge)
            {
                float Z = static_cast<float>(BasePosition.Z);
                if (!bStraightEdge)
                {
                    float RawZ = 0.0f;
                    float Gradient = 0.0f;
                    const float Weight = Relief.WeightAt(BasePosition.X, BasePosition.Y, RawZ, &Gradient);
                    Z += Relief.ReliefCm(BasePosition.X, BasePosition.Y, RawZ, Weight, Gradient);
                }
                FineZ.Add(Z);
                return Z;
            });
        if (SplitCells <= 0)
        {
            continue;
        }
        // Stored, not baked: procedural-mesh vertices serialise at ~640 bytes
        // each and the ledges would push L_Zambezi.umap past Git LFS's 2 GiB
        // limit. The component rebuilds the ledged mesh when play begins.
        URaftSimTerrainRefinementComponent* Refinement =
            Actor->FindComponentByClass<URaftSimTerrainRefinementComponent>();
        if (!Refinement)
        {
            Refinement = NewObject<URaftSimTerrainRefinementComponent>(Actor, TEXT("WallLedgeRefinement"));
            Actor->AddInstanceComponent(Refinement);
            Refinement->RegisterComponent();
        }
        Refinement->GridRowSize = RowSize;
        Refinement->GridRows = Base.Num() / RowSize;
        Refinement->SplitCount = SplitCount;
        Refinement->WallCornerIndices = MoveTemp(WallCornerIndices);
        Refinement->WallCornerZ = MoveTemp(WallCornerZ);
        Refinement->FineZ = MoveTemp(FineZ);
        // The ledges shade each other; the coarse facet comb that made V17
        // drop these tiles' shadows is replaced on the walls in play.
        Mesh->SetCastShadow(true);
        Actor->Tags.Remove(TEXT("RaftSimCoarseSourceSelfShadowSuppressed"));
        Actor->Tags.AddUnique(TEXT("RaftSimZambeziWallLedges"));
        Actor->Tags.AddUnique(TEXT("InferredLedgesNotSurveyed"));
        Stats.SubdividedCells += SplitCells;
        Stats.AddedVertices += Refinement->FineZ.Num();
        ++Tiles;
    }
    OutSummary += FString::Printf(
        TEXT("Zambezi wall ledges (inferred lava-flow banding): %d tiles, %d wall cells split %dx%d (3.1 m), "
             "%d vertices added when play begins (stored on URaftSimTerrainRefinementComponent); the ledged "
             "tiles cast shadows.\n"),
        Tiles, Stats.SubdividedCells, SplitCount, SplitCount, Stats.AddedVertices);
    return Tiles;
}
}
