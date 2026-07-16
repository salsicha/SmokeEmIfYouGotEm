#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
FString GetLandscapeCandidateCaptureRelativePath(
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    const FString& CaptureId)
{
    return FPaths::Combine(
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates"),
        Candidate.PreviewSpec.RiverId + TEXT("_") + CaptureId + TEXT(".png"));
}

void ApplyPreviewOnlyLandscapeChannelBurn(
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    uint16 ChannelFloor,
    TArray<uint16>& HeightData,
    int32& OutModifiedSampleCount)
{
    const int32 LandscapeSize = Candidate.LandscapeSize;
    constexpr float MinX = -5800.0f;
    const float MaxX = MinX + Candidate.HorizontalSpanXCm;
    const float HalfSpanY = Candidate.HorizontalSpanYCm * 0.5f;
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Candidate.PreviewSpec);
    const float BurnFeatherWidth = FMath::Max(260.0f, Candidate.PreviewSpec.BankWidthCm * 0.72f);

    OutModifiedSampleCount = 0;
    for (int32 YIndex = 0; YIndex < LandscapeSize; ++YIndex)
    {
        const float V = static_cast<float>(YIndex) / static_cast<float>(LandscapeSize - 1);
        const float WorldY = FMath::Lerp(-HalfSpanY, HalfSpanY, V);
        for (int32 XIndex = 0; XIndex < LandscapeSize; ++XIndex)
        {
            const float U = static_cast<float>(XIndex) / static_cast<float>(LandscapeSize - 1);
            const float WorldX = FMath::Lerp(MinX, MaxX, U);
            const float CenterY = GetPreviewRiverCenterY(Candidate.PreviewSpec, WorldX);
            const float DistanceFromCenterline = FMath::Abs(WorldY - CenterY);
            if (DistanceFromCenterline >= ActiveRiverHalfWidth + BurnFeatherWidth)
            {
                continue;
            }

            const int32 SampleIndex = YIndex * LandscapeSize + XIndex;
            const uint16 SourceHeight = HeightData[SampleIndex];
            const float SourceBlend = SmoothPreviewStep(
                ActiveRiverHalfWidth * 0.82f,
                ActiveRiverHalfWidth + BurnFeatherWidth,
                DistanceFromCenterline);
            const uint16 BurnedHeight = static_cast<uint16>(FMath::Clamp(
                FMath::RoundToInt(FMath::Lerp(static_cast<float>(ChannelFloor), static_cast<float>(SourceHeight), SourceBlend)),
                0,
                65535));
            const uint16 ConditionedHeight = FMath::Min(SourceHeight, BurnedHeight);
            if (ConditionedHeight != SourceHeight)
            {
                HeightData[SampleIndex] = ConditionedHeight;
                ++OutModifiedSampleCount;
            }
        }
    }
}

AActor* AddLandscapeCandidatePhysicalRiverRibbon(
    UWorld* World,
    ALandscape* Landscape,
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    UMaterialInterface* WaterMaterial,
    FString& OutSummary)
{
    if (!World || !Landscape || !WaterMaterial)
    {
        return nullptr;
    }
    TArray<FRaftSimLandscapeCandidateCenterlinePoint> SourcePoints;
    if (!LoadLandscapeCandidateLocalCenterline(Candidate, SourcePoints, OutSummary) ||
        SourcePoints.Num() < 2)
    {
        return nullptr;
    }

    TArray<FVector2D> Centers;
    TArray<float> StationsCm;
    TArray<float> ConditionedSurfaceWorldZ;
    int32 ConditionedProfileCenterCount = 0;
    const bool bChilkoSourceScale =
        Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon");
    const float CenterSampleSpacingCm = bChilkoSourceScale ? 500.0f : 100.0f;
    for (int32 SegmentIndex = 0; SegmentIndex + 1 < SourcePoints.Num(); ++SegmentIndex)
    {
        const FRaftSimLandscapeCandidateCenterlinePoint& A = SourcePoints[SegmentIndex];
        const FRaftSimLandscapeCandidateCenterlinePoint& B = SourcePoints[SegmentIndex + 1];
        const float SegmentLengthCm = (B.LocalCm - A.LocalCm).Size();
        const int32 Steps = FMath::Max(
            1,
            FMath::CeilToInt(SegmentLengthCm / CenterSampleSpacingCm));
        for (int32 Step = 0; Step < Steps; ++Step)
        {
            const float T = static_cast<float>(Step) / static_cast<float>(Steps);
            const FVector2D Local = FMath::Lerp(A.LocalCm, B.LocalCm, T);
            Centers.Add(FVector2D(
                -5800.0f + Local.X,
                -Candidate.HorizontalSpanYCm * 0.5f + Local.Y));
            StationsCm.Add(FMath::Lerp(A.StationMeters, B.StationMeters, T) * 100.0f);
            if (A.bHasConditionedVisualSurface && B.bHasConditionedVisualSurface)
            {
                ConditionedSurfaceWorldZ.Add(
                    FMath::Lerp(
                        A.ConditionedVisualSurfaceNormalized,
                        B.ConditionedVisualSurfaceNormalized,
                        T) * Candidate.TargetReliefCm);
                ++ConditionedProfileCenterCount;
            }
            else
            {
                const FVector2D& Center = Centers.Last();
                const float TerrainZ = Landscape->GetHeightAtLocation(
                    FVector(Center.X, Center.Y, 0.0f),
                    EHeightfieldSource::Editor).Get(0.0f);
                ConditionedSurfaceWorldZ.Add(TerrainZ + 140.0f);
            }
        }
    }
    const FRaftSimLandscapeCandidateCenterlinePoint& Last = SourcePoints.Last();
    Centers.Add(FVector2D(
        -5800.0f + Last.LocalCm.X,
        -Candidate.HorizontalSpanYCm * 0.5f + Last.LocalCm.Y));
    StationsCm.Add(Last.StationMeters * 100.0f);
    if (Last.bHasConditionedVisualSurface)
    {
        ConditionedSurfaceWorldZ.Add(
            Last.ConditionedVisualSurfaceNormalized * Candidate.TargetReliefCm);
        ++ConditionedProfileCenterCount;
    }
    else
    {
        const FVector2D& Center = Centers.Last();
        const float TerrainZ = Landscape->GetHeightAtLocation(
            FVector(Center.X, Center.Y, 0.0f),
            EHeightfieldSource::Editor).Get(0.0f);
        ConditionedSurfaceWorldZ.Add(TerrainZ + 140.0f);
    }

    const int32 CrossSteps = bChilkoSourceScale ? 16 : 32;
    TArray<FVector> Vertices;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve(Centers.Num() * (CrossSteps + 1));
    UVs.Reserve(Centers.Num() * (CrossSteps + 1));
    VertexColors.Reserve(Centers.Num() * (CrossSteps + 1));
    for (int32 CenterIndex = 0; CenterIndex < Centers.Num(); ++CenterIndex)
    {
        const FVector2D Previous = Centers[FMath::Max(0, CenterIndex - 1)];
        const FVector2D Next = Centers[FMath::Min(Centers.Num() - 1, CenterIndex + 1)];
        const FVector2D Tangent = (Next - Previous).GetSafeNormal();
        const FVector2D Normal(-Tangent.Y, Tangent.X);
        const float HalfWidth = GetPreviewActiveRiverHalfWidthCm(Candidate.PreviewSpec) *
            (0.92f + 0.10f * FMath::Sin(StationsCm[CenterIndex] * 0.00031f));
        const float SurfaceZ = ConditionedSurfaceWorldZ[CenterIndex] +
            Candidate.PreviewSpec.FlowWaterLevelOffsetCm;
        for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
        {
            const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
            const float Lateral = FMath::Lerp(-HalfWidth, HalfWidth, V);
            const float EdgeT = FMath::Abs(V - 0.5f) * 2.0f;
            const float FlowCueScale = Candidate.PreviewSpec.FlowCurrentCueScale;
            const float WaveEnvelope = 1.0f - EdgeT * 0.48f;
            const float Wave = FlowCueScale * WaveEnvelope * (
                12.0f * FMath::Sin(StationsCm[CenterIndex] * 0.0041f + Lateral * 0.011f) +
                5.0f * FMath::Sin(StationsCm[CenterIndex] * 0.0107f - Lateral * 0.021f) +
                2.5f * FMath::Sin(StationsCm[CenterIndex] * 0.0183f + Lateral * 0.037f));
            Vertices.Add(FVector(
                Centers[CenterIndex].X + Normal.X * Lateral,
                Centers[CenterIndex].Y + Normal.Y * Lateral,
                SurfaceZ + Wave));
            UVs.Add(FVector2D(StationsCm[CenterIndex] / 8000.0f, V));
            FLinearColor Deep = Candidate.PreviewSpec.bDesertCanyon
                ? FMath::Lerp(
                      Candidate.PreviewSpec.WaterColor,
                      FLinearColor(0.095f, 0.085f, 0.058f),
                      0.42f)
                : FMath::Lerp(
                      Candidate.PreviewSpec.WaterColor,
                      FLinearColor(0.018f, 0.115f, 0.085f),
                      0.52f);
            const FLinearColor Shallow = Candidate.PreviewSpec.bDesertCanyon
                ? FLinearColor(0.235f, 0.185f, 0.115f)
                : FLinearColor(0.085f, 0.255f, 0.145f);
            const float CurrentThread = 0.5f + 0.5f * FMath::Sin(
                StationsCm[CenterIndex] * 0.0027f + Lateral * 0.0061f);
            const float FineCurrent = 0.5f + 0.5f * FMath::Sin(
                StationsCm[CenterIndex] * 0.0091f - Lateral * 0.0173f);
            const float CrestCue = 0.5f + 0.5f * FMath::Sin(
                StationsCm[CenterIndex] * 0.0147f + Lateral * 0.028f);
            Deep = FMath::Lerp(
                Deep * 0.76f,
                Candidate.PreviewSpec.bDesertCanyon
                    ? FLinearColor(0.195f, 0.155f, 0.095f)
                    : FLinearColor(0.075f, 0.235f, 0.190f),
                0.18f * CurrentThread + 0.08f * FineCurrent);
            FLinearColor SurfaceColor = FMath::Lerp(
                Deep,
                Shallow,
                FMath::Pow(EdgeT, 1.8f));
            const float BreakerSignal =
                CurrentThread * 0.52f + FineCurrent * 0.28f + CrestCue * 0.20f;
            const float Breaker = FlowCueScale * WaveEnvelope *
                SmoothPreviewStep(0.72f, 0.92f, BreakerSignal) * 0.72f;
            SurfaceColor = FMath::Lerp(
                SurfaceColor,
                Candidate.PreviewSpec.bDesertCanyon
                    ? FLinearColor(0.72f, 0.68f, 0.58f)
                    : FLinearColor(0.75f, 0.84f, 0.80f),
                Breaker);
            VertexColors.Add(SurfaceColor);
        }
    }
    const int32 RowSize = CrossSteps + 1;
    for (int32 CenterIndex = 0; CenterIndex + 1 < Centers.Num(); ++CenterIndex)
    {
        for (int32 CrossIndex = 0; CrossIndex < CrossSteps; ++CrossIndex)
        {
            const int32 A = CenterIndex * RowSize + CrossIndex;
            const int32 B = A + 1;
            const int32 C = (CenterIndex + 1) * RowSize + CrossIndex;
            const int32 D = C + 1;
            Triangles.Add(A);
            Triangles.Add(C);
            Triangles.Add(B);
            Triangles.Add(B);
            Triangles.Add(C);
            Triangles.Add(D);
        }
    }
    TArray<FVector> Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    for (FVector& Normal : Normals)
    {
        Normal = FMath::Lerp(Normal, FVector::UpVector, 0.24f).GetSafeNormal();
    }
    OutSummary += FString::Printf(
        TEXT("Built source-aligned physical river ribbon with %d center samples at %.1f m spacing (%d using the manifest-recorded conditioned visual surface), %d cross steps, bounded render-only current relief below 20 centimetres, and sparse flow-scaled breaker coloration across %.1f m.\n"),
        Centers.Num(),
        CenterSampleSpacingCm * 0.01f,
        ConditionedProfileCenterCount,
        CrossSteps,
        Last.StationMeters);
    return AddPreviewProceduralMeshActor(
        World,
        FString::Printf(
            TEXT("RaftSim_PhysicalCorridorRiverRibbon_%s"),
            *Candidate.PreviewSpec.RiverId),
        Vertices,
        Triangles,
        Normals,
        UVs,
        Candidate.PreviewSpec.WaterColor,
        WaterMaterial,
        &VertexColors,
        false);
}

AActor* AddLandscapeCandidatePhysicalBankCorridorMesh(
    UWorld* World,
    ALandscape* Landscape,
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    FString& OutSummary)
{
    if (!World || !Landscape || !Candidate.bPhysicalScaleSourceCorridor)
    {
        return nullptr;
    }

    const bool bColorado = Candidate.PreviewSpec.RiverId == TEXT("colorado_river");
    const bool bZambezi = Candidate.PreviewSpec.RiverId == TEXT("zambezi_batoka_gorge");
    const bool bFutaleufu = Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator");
    const bool bRockCanyon = bColorado || bZambezi;
    FRaftSimPreviewImage SourceAlbedo;
    FString SourceAlbedoPath = Candidate.PreviewSpec.AerialDrapeImage;
    if (Candidate.PreviewSpec.RiverId == TEXT("colorado_river"))
    {
        SourceAlbedoPath =
            TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/production_corridor/"
                 "lees_ferry_reach_2200_4700m/derived/"
                 "colorado_lees_ferry_reach_terrain_albedo_2048.png");
    }
    else if (Candidate.PreviewSpec.RiverId == TEXT("american_south_fork"))
    {
        SourceAlbedoPath =
            TEXT("physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
                 "chili_bar_reach_0_2500m/derived/"
                 "south_fork_chili_bar_reach_source_albedo_2048.png");
    }
    if (!LoadPreviewPngImage(SourceAlbedoPath, SourceAlbedo))
    {
        OutSummary += TEXT("Failed to load physical corridor source albedo for the dense bank mesh.\n");
        return nullptr;
    }

    constexpr float LandscapeMinX = -5800.0f;
    const float LandscapeMaxX = LandscapeMinX + Candidate.HorizontalSpanXCm;
    const float LandscapeMinY = -Candidate.HorizontalSpanYCm * 0.5f;
    const float LandscapeMaxY = Candidate.HorizontalSpanYCm * 0.5f;
    const bool bInternationalPhysicalCorridor =
        Candidate.PreviewSpec.RiverId == TEXT("zambezi_batoka_gorge") ||
        Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator");
    const float TargetGridSpacingCm =
        Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon")
        ? 3000.0f
        : (bInternationalPhysicalCorridor
               ? 1250.0f
               : (Candidate.HorizontalSpanXCm > 500000.0f ? 2500.0f : 400.0f));
    constexpr float SurfaceLiftCm = 6.0f;
    constexpr int32 TileCountX = 4;
    const int32 TotalXSteps = FMath::CeilToInt(Candidate.HorizontalSpanXCm / TargetGridSpacingCm);
    const int32 TotalYSteps = FMath::CeilToInt(Candidate.HorizontalSpanYCm / TargetGridSpacingCm);
    UMaterialInterface* TerrainMaterial = LoadOrCreatePhysicalSourceTerrainRenderMaterial(Candidate);
    if (!TerrainMaterial)
    {
        OutSummary += TEXT("Failed to load the dense source-terrain vertex-color material.\n");
        return nullptr;
    }

    const FLinearColor RockTint = FMath::Lerp(
        Candidate.PreviewSpec.RockColor,
        FLinearColor(0.22f, 0.24f, 0.20f),
        0.38f);
    AActor* FirstActor = nullptr;
    int32 TotalVertexCount = 0;
    int32 TotalTriangleCount = 0;
    for (int32 TileIndex = 0; TileIndex < TileCountX; ++TileIndex)
    {
        const int32 StartXStep = TotalXSteps * TileIndex / TileCountX;
        const int32 EndXStep = TotalXSteps * (TileIndex + 1) / TileCountX;
        const int32 TileXSteps = EndXStep - StartXStep;
        const int32 RowSize = TileXSteps + 1;

        TArray<FVector> Vertices;
        TArray<FVector2D> UVs;
        TArray<FLinearColor> VertexColors;
        TArray<int32> Triangles;
        Vertices.Reserve(RowSize * (TotalYSteps + 1));
        UVs.Reserve(RowSize * (TotalYSteps + 1));
        VertexColors.Reserve(RowSize * (TotalYSteps + 1));
        Triangles.Reserve(TileXSteps * TotalYSteps * 6);

        for (int32 YStep = 0; YStep <= TotalYSteps; ++YStep)
        {
            const float SourceSouthV = static_cast<float>(YStep) / static_cast<float>(TotalYSteps);
            const float WorldY = FMath::Lerp(LandscapeMinY, LandscapeMaxY, SourceSouthV);
            const float SourceV = 1.0f - SourceSouthV;
            for (int32 XStep = StartXStep; XStep <= EndXStep; ++XStep)
            {
                const float SourceU = static_cast<float>(XStep) / static_cast<float>(TotalXSteps);
                const float WorldX = FMath::Lerp(LandscapeMinX, LandscapeMaxX, SourceU);
                const float TerrainZ = Landscape->GetHeightAtLocation(
                    FVector(WorldX, WorldY, 0.0f),
                    EHeightfieldSource::Editor).Get(0.0f);
                Vertices.Add(FVector(WorldX, WorldY, TerrainZ + SurfaceLiftCm));
                // World Y advances south-to-north, while the north-up source image advances
                // top-to-bottom. Match the direct material sample to the proven CPU drape sample.
                UVs.Add(FVector2D(SourceU, SourceV));

                const FLinearColor SourceSrgb = SourceAlbedo.SampleRawBilinear(SourceU, SourceV);
                const FColor SourceColor8(
                    static_cast<uint8>(FMath::Clamp(FMath::RoundToInt(SourceSrgb.R * 255.0f), 0, 255)),
                    static_cast<uint8>(FMath::Clamp(FMath::RoundToInt(SourceSrgb.G * 255.0f), 0, 255)),
                    static_cast<uint8>(FMath::Clamp(FMath::RoundToInt(SourceSrgb.B * 255.0f), 0, 255)),
                    255);
                FLinearColor SourceLinear = FLinearColor::FromSRGBColor(SourceColor8);
                SourceLinear.R = FMath::Max(SourceLinear.R, 0.012f);
                SourceLinear.G = FMath::Max(SourceLinear.G, 0.012f);
                SourceLinear.B = FMath::Max(SourceLinear.B, 0.012f);
                SourceLinear.A = 1.0f;
                VertexColors.Add(SourceLinear);
            }
        }

        for (int32 YStep = 0; YStep < TotalYSteps; ++YStep)
        {
            for (int32 LocalXStep = 0; LocalXStep < TileXSteps; ++LocalXStep)
            {
                const int32 A = YStep * RowSize + LocalXStep;
                const int32 B = A + 1;
                const int32 C = (YStep + 1) * RowSize + LocalXStep;
                const int32 D = C + 1;
                Triangles.Append({A, C, B, B, C, D});
            }
        }

        TArray<FVector> Normals = ComputePreviewMeshNormals(Vertices, Triangles);
        if (bRockCanyon || bFutaleufu)
        {
            const float RenderReliefCapCm = bZambezi ? 420.0f : (bFutaleufu ? 240.0f : 180.0f);
            for (int32 VertexIndex = 0; VertexIndex < Vertices.Num(); ++VertexIndex)
            {
                const float Steepness = 1.0f - FMath::Clamp(Normals[VertexIndex].Z, 0.0f, 1.0f);
                const float SteepReliefT = SmoothPreviewStep(
                    bFutaleufu ? 0.14f : 0.22f,
                    bFutaleufu ? 0.62f : 0.72f,
                    Steepness);
                if (SteepReliefT <= KINDA_SMALL_NUMBER)
                {
                    continue;
                }
                const FVector& Vertex = Vertices[VertexIndex];
                const float BroadFacet = FMath::PerlinNoise2D(
                    FVector2D(Vertex.X * 0.00024f, Vertex.Y * 0.00024f));
                const float LocalFracture = FMath::PerlinNoise2D(
                    FVector2D(Vertex.X * 0.00082f + 17.0f, Vertex.Y * 0.00082f - 9.0f));
                const float Strata = FMath::Sin(
                    Vertex.Z * 0.0115f + Vertex.X * 0.00031f - Vertex.Y * 0.00019f);
                const float ReliefCm = FMath::Clamp(
                    SteepReliefT *
                        (BroadFacet * (bZambezi ? 230.0f : (bFutaleufu ? 135.0f : 105.0f)) +
                         LocalFracture * (bZambezi ? 125.0f : (bFutaleufu ? 88.0f : 62.0f)) +
                         Strata * (bZambezi ? 82.0f : (bFutaleufu ? 55.0f : 38.0f))),
                    -RenderReliefCapCm,
                    RenderReliefCapCm);
                Vertices[VertexIndex].Z += ReliefCm;
            }
            Normals = ComputePreviewMeshNormals(Vertices, Triangles);
        }
        for (int32 VertexIndex = 0; VertexIndex < Normals.Num(); ++VertexIndex)
        {
            const float Steepness = 1.0f - FMath::Clamp(Normals[VertexIndex].Z, 0.0f, 1.0f);
            const float RockBlend =
                SmoothPreviewStep(0.42f, 0.88f, Steepness) * (bRockCanyon ? 0.05f : 0.24f);
            VertexColors[VertexIndex] = FMath::Lerp(VertexColors[VertexIndex], RockTint, RockBlend);
            Normals[VertexIndex] =
                FMath::Lerp(
                    Normals[VertexIndex],
                    FVector::UpVector,
                    bRockCanyon ? 0.04f : 0.18f).GetSafeNormal();
        }

        AActor* Actor = AddPreviewProceduralMeshActor(
            World,
            FString::Printf(
                TEXT("RaftSim_PhysicalCorridorDenseSourceTerrainTile_%02d_%s"),
                TileIndex,
                *Candidate.PreviewSpec.RiverId),
            Vertices,
            Triangles,
            Normals,
            UVs,
            Candidate.PreviewSpec.TerrainColor,
            TerrainMaterial,
            &VertexColors,
            false);
        if (!Actor)
        {
            OutSummary += FString::Printf(
                TEXT("Failed to create dense physical source-terrain tile %d.\n"),
                TileIndex);
            return nullptr;
        }
        if (!FirstActor)
        {
            FirstActor = Actor;
        }
        if (UProceduralMeshComponent* MeshComponent =
                Actor->FindComponentByClass<UProceduralMeshComponent>())
        {
            MeshComponent->SetCastShadow(true);
        }
        TotalVertexCount += Vertices.Num();
        TotalTriangleCount += Triangles.Num() / 3;
    }

    OutSummary += FString::Printf(
        TEXT("Built four non-self-intersecting dense source-terrain tiles for %s with %d vertices and %d triangles at %.2f m target spacing.\n"),
        *Candidate.PreviewSpec.RiverId,
        TotalVertexCount,
        TotalTriangleCount,
        TargetGridSpacingCm * 0.01f);
    return FirstActor;
}

void RepositionLandscapeCandidatePhysicalCameras(
    UWorld* World,
    ALandscape* Landscape,
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    FString& OutSummary)
{
    if (!World || !Landscape || !Candidate.bPhysicalScaleSourceCorridor)
    {
        return;
    }
    TArray<FRaftSimLandscapeCandidateCenterlinePoint> Points;
    if (!LoadLandscapeCandidateLocalCenterline(Candidate, Points, OutSummary) || Points.Num() < 2)
    {
        return;
    }
    auto RiverLocation = [&Candidate, &Points, Landscape](float Progress, float HeightAboveTerrain)
    {
        const FVector2D XY = SampleLandscapeCandidateCenterlineWorld(Candidate, Points, Progress);
        float ConditionedVisualSurfaceZ = 0.0f;
        if (SampleLandscapeCandidateConditionedVisualSurfaceWorldZ(
                Candidate,
                Points,
                Progress,
                ConditionedVisualSurfaceZ))
        {
            const float OriginalWaterOffset =
                140.0f + Candidate.PreviewSpec.FlowWaterLevelOffsetCm;
            const float ClearanceAboveWater = FMath::Max(
                8.0f,
                HeightAboveTerrain - OriginalWaterOffset);
            return FVector(
                XY.X,
                XY.Y,
                ConditionedVisualSurfaceZ + Candidate.PreviewSpec.FlowWaterLevelOffsetCm +
                    ClearanceAboveWater);
        }
        const float TerrainZ = Landscape->GetHeightAtLocation(
            FVector(XY.X, XY.Y, 0.0f),
            EHeightfieldSource::Editor).Get(0.0f);
        return FVector(XY.X, XY.Y, TerrainZ + HeightAboveTerrain);
    };
    auto SetCamera = [World, &RiverLocation, &OutSummary](
                         const TCHAR* Label,
                         float Progress,
                         float TargetProgress,
                         float Height,
                         float TargetHeight)
    {
        for (TActorIterator<ACameraActor> It(World); It; ++It)
        {
            if (It->GetActorLabel() != Label)
            {
                continue;
            }
            const FVector Location = RiverLocation(Progress, Height);
            const FVector Target = RiverLocation(TargetProgress, TargetHeight);
            It->SetActorLocationAndRotation(Location, (Target - Location).Rotation());
            OutSummary += FString::Printf(
                TEXT("Positioned %s at progress %.4f (%.1f, %.1f, %.1f cm), targeting %.4f (%.1f, %.1f, %.1f cm).\n"),
                Label,
                Progress,
                Location.X,
                Location.Y,
                Location.Z,
                TargetProgress,
                Target.X,
                Target.Y,
                Target.Z);
            return;
        }
    };
    if (Candidate.PreviewSpec.RiverId == TEXT("colorado_river"))
    {
        SetCamera(TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"), 0.250f, 0.365f, 230.0f, 150.0f);
        SetCamera(TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"), 0.450f, 0.565f, 175.0f, 125.0f);
    }
    else if (Candidate.PreviewSpec.RiverId == TEXT("zambezi_batoka_gorge"))
    {
        SetCamera(TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"), 0.100f, 0.104f, 330.0f, 170.0f);
        SetCamera(TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"), 0.285f, 0.289f, 270.0f, 160.0f);
    }
    else if (Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator"))
    {
        SetCamera(TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"), 0.815f, 0.825f, 330.0f, 170.0f);
        SetCamera(TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"), 0.644f, 0.654f, 270.0f, 160.0f);
    }
    else if (Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon"))
    {
        SetCamera(TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"), 0.250f, 0.254f, 280.0f, 150.0f);
        SetCamera(TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"), 0.420f, 0.424f, 210.0f, 125.0f);
    }
    else
    {
        SetCamera(TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"), 0.250f, 0.365f, 330.0f, 180.0f);
        SetCamera(TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"), 0.275f, 0.390f, 270.0f, 165.0f);
    }
    SetCamera(TEXT("RaftSim_SolverRapid_RiverEyeCaptureCamera"), 0.530f, 0.645f, 275.0f, 165.0f);
    for (TActorIterator<APlayerStart> It(World); It; ++It)
    {
        if (It->GetActorLabel() == TEXT("RaftSim_GuideSeat_PlayerStart"))
        {
            It->SetActorLocation(RiverLocation(0.032f, 120.0f));
        }
    }
    for (TActorIterator<ASphereReflectionCapture> It(World); It; ++It)
    {
        if (It->GetActorLabel() == TEXT("RaftSim_RiverCorridorReflectionCapture"))
        {
            It->SetActorLocation(RiverLocation(0.09f, 520.0f));
        }
    }
}
} // namespace RaftSimEditorEnvironment
