#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "GameFramework/GameModeBase.h"
#include "GameFramework/WorldSettings.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRiverWaterConfig.h"

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
    const FRaftSimPreviewImage* SolverVisualizationFields,
    UMaterialInterface* SolverFoamMaterial,
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
    const FRaftSimLandscapeCandidateWaterSettings WaterSettings =
        GetLandscapeCandidateWaterSettings(Candidate.PreviewSpec.RiverId);
    const bool bUseSolverVisualizationFields =
        Candidate.bUseSolverVisualizationFields &&
        WaterSettings.SolverFieldEnable > 0.5f &&
        SolverVisualizationFields &&
        SolverVisualizationFields->IsValid() &&
        SolverFoamMaterial;
    const float LandscapeMinX = GetLandscapeCandidateWorldMinX(Candidate);
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
                LandscapeMinX + Local.X,
                -Candidate.HorizontalSpanYCm * 0.5f + Local.Y));
            StationsCm.Add(FMath::Lerp(A.StationMeters, B.StationMeters, T) * 100.0f);
            if (A.bHasConditionedVisualSurface && B.bHasConditionedVisualSurface)
            {
                ConditionedSurfaceWorldZ.Add(
                    FMath::Lerp(
                        A.ConditionedVisualSurfaceNormalized,
                        B.ConditionedVisualSurfaceNormalized,
                        T) * Candidate.TargetReliefCm +
                    Candidate.WorldVerticalOffsetCm);
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
        LandscapeMinX + Last.LocalCm.X,
        -Candidate.HorizontalSpanYCm * 0.5f + Last.LocalCm.Y));
    StationsCm.Add(Last.StationMeters * 100.0f);
    if (Last.bHasConditionedVisualSurface)
    {
        ConditionedSurfaceWorldZ.Add(
            Last.ConditionedVisualSurfaceNormalized * Candidate.TargetReliefCm +
            Candidate.WorldVerticalOffsetCm);
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
    TArray<FLinearColor> SolverFoamVertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve(Centers.Num() * (CrossSteps + 1));
    UVs.Reserve(Centers.Num() * (CrossSteps + 1));
    VertexColors.Reserve(Centers.Num() * (CrossSteps + 1));
    if (bUseSolverVisualizationFields)
    {
        SolverFoamVertexColors.Reserve(Centers.Num() * (CrossSteps + 1));
    }
    for (int32 CenterIndex = 0; CenterIndex < Centers.Num(); ++CenterIndex)
    {
        const FVector2D Previous = Centers[FMath::Max(0, CenterIndex - 1)];
        const FVector2D Next = Centers[FMath::Min(Centers.Num() - 1, CenterIndex + 1)];
        const FVector2D Tangent = (Next - Previous).GetSafeNormal();
        const FVector2D Normal(-Tangent.Y, Tangent.X);
        const float HalfWidth = GetPreviewActiveRiverHalfWidthCm(Candidate.PreviewSpec) *
            (bUseSolverVisualizationFields ? WaterSettings.RenderWidthScale : 1.0f) *
            (0.92f + 0.10f * FMath::Sin(StationsCm[CenterIndex] * 0.00031f));
        const float SurfaceZ = ConditionedSurfaceWorldZ[CenterIndex] +
            Candidate.PreviewSpec.FlowWaterLevelOffsetCm;
        for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
        {
            const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
            const float Lateral = FMath::Lerp(-HalfWidth, HalfWidth, V);
            const float SolverU = StationsCm[CenterIndex] /
                FMath::Max(StationsCm.Last(), 1.0f);
            const float SolverLateralV = FMath::GetMappedRangeValueClamped(
                FVector2D(
                    Candidate.SolverVisualizationLateralMinM,
                    Candidate.SolverVisualizationLateralMaxM),
                FVector2D(0.0f, 1.0f),
                Lateral * 0.01f);
            const FLinearColor SolverField = bUseSolverVisualizationFields
                ? SolverVisualizationFields->SampleRawBilinear(
                      SolverU,
                      1.0f - SolverLateralV)
                : FLinearColor::Black;
            const float SolverPersistenceStepU = 4.0f /
                FMath::Max(StationsCm.Last() * 0.01f, 1.0f);
            const FLinearColor SolverFieldUpstream4M = bUseSolverVisualizationFields
                ? SolverVisualizationFields->SampleRawBilinear(
                      FMath::Clamp(SolverU - SolverPersistenceStepU, 0.0f, 1.0f),
                      1.0f - SolverLateralV)
                : FLinearColor::Black;
            const FLinearColor SolverFieldUpstream8M = bUseSolverVisualizationFields
                ? SolverVisualizationFields->SampleRawBilinear(
                      FMath::Clamp(SolverU - SolverPersistenceStepU * 2.0f, 0.0f, 1.0f),
                      1.0f - SolverLateralV)
                : FLinearColor::Black;
            const float SolverDepthM = SolverField.R *
                Candidate.SolverVisualizationDepthCapM;
            const float SolverSpeedMps = SolverField.G *
                Candidate.SolverVisualizationSpeedCapMps;
            const float SolverFroude = SolverField.B *
                Candidate.SolverVisualizationFroudeCap;
            const float SolverPersistentSpeedMps = FMath::Max3(
                SolverSpeedMps,
                SolverFieldUpstream4M.G * Candidate.SolverVisualizationSpeedCapMps * 0.94f,
                SolverFieldUpstream8M.G * Candidate.SolverVisualizationSpeedCapMps * 0.84f);
            const float SolverPersistentFroude = FMath::Max3(
                SolverFroude,
                SolverFieldUpstream4M.B * Candidate.SolverVisualizationFroudeCap * 0.94f,
                SolverFieldUpstream8M.B * Candidate.SolverVisualizationFroudeCap * 0.84f);
            const float SolverHydraulicPresence = bUseSolverVisualizationFields
                ? SmoothPreviewStep(0.03f, 0.16f, SolverDepthM)
                : 0.0f;
            const float SolverSurfaceReliefCm = bUseSolverVisualizationFields
                ? (SolverField.A - 0.5f) * 2.0f *
                      Candidate.SolverVisualizationSurfaceReliefCapM * 100.0f *
                      WaterSettings.SolverSurfaceReliefScale * SolverHydraulicPresence
                : 0.0f;
            const float SolverHydraulicAerationT = bUseSolverVisualizationFields
                ? SmoothPreviewStep(0.60f, 1.10f, SolverPersistentFroude) *
                      SmoothPreviewStep(0.65f, 2.10f, SolverPersistentSpeedMps) *
                      SolverHydraulicPresence
                : 0.0f;
            const float EdgeT = FMath::Abs(V - 0.5f) * 2.0f;
            const float FlowCueScale = Candidate.PreviewSpec.FlowCurrentCueScale;
            const float WaveEnvelope = 1.0f - EdgeT * 0.48f;
            const float Wave = FlowCueScale * WaveEnvelope * (
                12.0f * FMath::Sin(StationsCm[CenterIndex] * 0.0041f + Lateral * 0.011f) +
                5.0f * FMath::Sin(StationsCm[CenterIndex] * 0.0107f - Lateral * 0.021f) +
                2.5f * FMath::Sin(StationsCm[CenterIndex] * 0.0183f + Lateral * 0.037f)) *
                (bUseSolverVisualizationFields ? 0.22f : 1.0f);
            Vertices.Add(FVector(
                Centers[CenterIndex].X + Normal.X * Lateral,
                Centers[CenterIndex].Y + Normal.Y * Lateral,
                SurfaceZ + Wave + SolverSurfaceReliefCm));
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
            const float Breaker = bUseSolverVisualizationFields
                ? SolverHydraulicAerationT * WaterSettings.SolverFroudeAerationWeight
                : FlowCueScale * WaveEnvelope *
                      SmoothPreviewStep(0.72f, 0.92f, BreakerSignal) * 0.72f;
            if (bUseSolverVisualizationFields)
            {
                const float DepthColorT = SmoothPreviewStep(0.20f, 2.60f, SolverDepthM) *
                    WaterSettings.SolverDepthColorWeight * SolverHydraulicPresence;
                const float SpeedColorT = SmoothPreviewStep(0.60f, 3.40f, SolverSpeedMps) *
                    0.18f * SolverHydraulicPresence;
                SurfaceColor = FMath::Lerp(
                    SurfaceColor,
                    WaterSettings.SolverDeepWaterTint,
                    DepthColorT);
                SurfaceColor = FMath::Lerp(
                    SurfaceColor,
                    FLinearColor(0.10f, 0.30f, 0.24f),
                    SpeedColorT);
            }
            SurfaceColor = FMath::Lerp(
                SurfaceColor,
                bUseSolverVisualizationFields
                    ? WaterSettings.SolverAerationTint
                    : Candidate.PreviewSpec.bDesertCanyon
                    ? FLinearColor(0.72f, 0.68f, 0.58f)
                    : FLinearColor(0.75f, 0.84f, 0.80f),
                Breaker);
            VertexColors.Add(SurfaceColor);
            if (bUseSolverVisualizationFields)
            {
                const float FoamNoiseA = FMath::PerlinNoise2D(FVector2D(
                    StationsCm[CenterIndex] * 0.0065f + SolverFroude * 1.7f,
                    Lateral * 0.0120f + SolverSpeedMps * 2.3f)) * 0.5f + 0.5f;
                const float FoamNoiseB = FMath::PerlinNoise2D(FVector2D(
                    StationsCm[CenterIndex] * 0.0170f - Lateral * 0.0040f + 19.7f,
                    Lateral * 0.0290f + SolverFroude * 3.1f - 7.4f)) * 0.5f + 0.5f;
                const float FoamBreakup = SmoothPreviewStep(
                    0.34f,
                    0.70f,
                    FMath::Clamp(FoamNoiseA * 0.68f + FoamNoiseB * 0.32f, 0.0f, 1.0f));
                const bool bColoradoHanceFoam =
                    Candidate.PreviewSpec.RiverId == TEXT("colorado_river");
                const float FoamBaseCoverage = bColoradoHanceFoam ? 0.46f : 0.28f;
                const float FoamBreakupCoverage = 1.0f - FoamBaseCoverage;
                const float FoamGain = bColoradoHanceFoam ? 1.10f : 0.94f;
                const float FoamOpacity = FMath::Clamp(
                    SolverHydraulicAerationT *
                        (FoamBaseCoverage + FoamBreakup * FoamBreakupCoverage) *
                        FoamGain,
                    0.0f,
                    0.94f);
                SolverFoamVertexColors.Add(
                    FLinearColor(0.86f, 0.92f, 0.88f, FoamOpacity));
            }
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
        TEXT("Built source-aligned physical river ribbon with %d center samples at %.1f m spacing (%d using the manifest-recorded conditioned visual surface), %d cross steps, bounded render-only current relief below 20 centimetres, and %s breaker coloration across %.1f m.\n"),
        Centers.Num(),
        CenterSampleSpacingCm * 0.01f,
        ConditionedProfileCenterCount,
        CrossSteps,
        bUseSolverVisualizationFields
            ? TEXT("cooked-field-derived")
            : TEXT("sparse flow-scaled analytic"),
        Last.StationMeters);
    AActor* WaterActor = AddPreviewProceduralMeshActor(
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
    if (WaterActor)
    {
        WaterActor->Tags.AddUnique(TEXT("RaftSimNonCollisionRenderSurface"));
        WaterActor->Tags.AddUnique(TEXT("RaftSimPhysicalCorridorWater"));
        if (Candidate.PreviewSpec.RiverId == TEXT("zambezi_batoka_gorge"))
        {
            WaterActor->Tags.AddUnique(TEXT("RaftSimZambeziSingleLayerWater"));
            WaterActor->Tags.AddUnique(TEXT("RaftSimMovingMultiScaleWaterNormals"));
        }
        else if (Candidate.PreviewSpec.RiverId == TEXT("pacuare"))
        {
            WaterActor->Tags.AddUnique(TEXT("RaftSimPacuareDefaultLitWater"));
            WaterActor->Tags.AddUnique(TEXT("RaftSimMovingMultiScaleWaterNormals"));
            WaterActor->Tags.AddUnique(TEXT("RaftSimSingleLayerWaterCaptureRejected"));
        }
    }
    if (bUseSolverVisualizationFields &&
        SolverFoamVertexColors.Num() == Vertices.Num())
    {
        TArray<FVector> SolverFoamVertices = Vertices;
        for (int32 VertexIndex = 0; VertexIndex < SolverFoamVertices.Num(); ++VertexIndex)
        {
            SolverFoamVertices[VertexIndex] += Normals[VertexIndex] * 1.4f;
        }
        AActor* FoamActor = AddPreviewProceduralMeshActor(
            World,
            FString::Printf(
                TEXT("RaftSim_SolverFieldFoam_%s"),
                *Candidate.PreviewSpec.RiverId),
            SolverFoamVertices,
            Triangles,
            Normals,
            UVs,
            FLinearColor(0.86f, 0.92f, 0.88f, 0.0f),
            SolverFoamMaterial,
            &SolverFoamVertexColors,
            false);
        if (FoamActor)
        {
            FoamActor->Tags.AddUnique(TEXT("RaftSimNonCollisionRenderSurface"));
            FoamActor->Tags.AddUnique(TEXT("RaftSimSolverFieldFoam"));
            FoamActor->Tags.AddUnique(TEXT("RaftSimCaptureOnlyWater"));
            if (Candidate.PreviewSpec.RiverId == TEXT("pacuare"))
            {
                FoamActor->Tags.AddUnique(
                    TEXT("RaftSimPacuareUpperHuacasSolverVisualization"));
                FoamActor->Tags.AddUnique(TEXT("RaftSimPacuareCaptureOnlyWater"));
            }
            else if (Candidate.PreviewSpec.RiverId == TEXT("colorado_river"))
            {
                FoamActor->Tags.AddUnique(
                    TEXT("RaftSimColoradoHanceSolverVisualization"));
                FoamActor->Tags.AddUnique(TEXT("RaftSimColoradoHanceCaptureOnlyWater"));
            }
        }
    }
    return WaterActor;
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

    const float LandscapeMinX = GetLandscapeCandidateWorldMinX(Candidate);
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

        TArray<FVector> Normals = bZambezi
            ? ComputePreviewGridHeightfieldNormals(Vertices, RowSize)
            : ComputePreviewMeshNormals(Vertices, Triangles);
        if (bRockCanyon || bFutaleufu)
        {
            // The earlier Batoka overlay sampled a 12 m noise octave on a
            // 12.5 m grid and amplified it by more than four metres. That
            // near-Nyquist displacement exposed the grid as regular ribs in
            // gameplay. Keep only resolvable 40-150 m basalt-scale relief in
            // geometry; the world-aligned material owns sub-grid detail.
            const float RenderReliefCapCm = bZambezi ? 220.0f : (bFutaleufu ? 240.0f : 180.0f);
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
                    FVector2D(
                        Vertex.X * (bZambezi ? 0.000065f : 0.00024f),
                        Vertex.Y * (bZambezi ? 0.000065f : 0.00024f)));
                const float LocalFracture = FMath::PerlinNoise2D(
                    FVector2D(
                        Vertex.X * (bZambezi ? 0.00020f : 0.00082f) + 17.0f,
                        Vertex.Y * (bZambezi ? 0.00020f : 0.00082f) - 9.0f));
                const float Strata = FMath::Sin(
                    Vertex.Z * (bZambezi ? 0.0028f : 0.0115f) +
                    Vertex.X * (bZambezi ? 0.00011f : 0.00031f) -
                    Vertex.Y * (bZambezi ? 0.00007f : 0.00019f));
                const float ReliefCm = FMath::Clamp(
                    SteepReliefT *
                        (BroadFacet * (bZambezi ? 125.0f : (bFutaleufu ? 135.0f : 105.0f)) +
                         LocalFracture * (bZambezi ? 65.0f : (bFutaleufu ? 88.0f : 62.0f)) +
                         Strata * (bZambezi ? 35.0f : (bFutaleufu ? 55.0f : 38.0f))),
                    -RenderReliefCapCm,
                    RenderReliefCapCm);
                Vertices[VertexIndex].Z += ReliefCm;
            }
            Normals = bZambezi
                ? ComputePreviewGridHeightfieldNormals(Vertices, RowSize)
                : ComputePreviewMeshNormals(Vertices, Triangles);
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

bool AddLandscapeCandidateScenarioMarkers(
    UWorld* World,
    ALandscape* Landscape,
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    FString& OutSummary)
{
    if (Candidate.ScenarioRelativePath.IsEmpty())
    {
        return true;
    }
    if (!World || !Landscape)
    {
        return false;
    }

    TArray<FRaftSimLandscapeCandidateCenterlinePoint> SourcePoints;
    if (!LoadLandscapeCandidateLocalCenterline(Candidate, SourcePoints, OutSummary) ||
        SourcePoints.Num() < 2)
    {
        return false;
    }

    const FString ScenarioPath = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(GetRepoRoot(), Candidate.ScenarioRelativePath));
    FString ScenarioText;
    if (!FFileHelper::LoadFileToString(ScenarioText, *ScenarioPath))
    {
        OutSummary += FString::Printf(TEXT("Could not read scenario %s.\n"), *ScenarioPath);
        return false;
    }
    TSharedPtr<FJsonObject> ScenarioRoot;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ScenarioText);
    if (!FJsonSerializer::Deserialize(Reader, ScenarioRoot) || !ScenarioRoot.IsValid())
    {
        OutSummary += FString::Printf(TEXT("Could not parse scenario %s.\n"), *ScenarioPath);
        return false;
    }
    if (ScenarioRoot->GetStringField(TEXT("river_id")) != Candidate.PreviewSpec.RiverId ||
        ScenarioRoot->GetBoolField(TEXT("production_promoted")))
    {
        OutSummary += TEXT("Scenario river mismatch or unsafe production-promotion flag.\n");
        return false;
    }
    const TArray<TSharedPtr<FJsonValue>>* RapidValues = nullptr;
    if (!ScenarioRoot->TryGetArrayField(TEXT("rapids"), RapidValues) || !RapidValues ||
        RapidValues->Num() < 1)
    {
        OutSummary += TEXT("Scenario has no rapid marker definitions.\n");
        return false;
    }

    UStaticMesh* ConeMesh = LoadPreviewMesh(TEXT("/Engine/BasicShapes/Cone.Cone"));
    if (!ConeMesh)
    {
        OutSummary += TEXT("Could not load the engine cone used for scenario markers.\n");
        return false;
    }
    const float LandscapeMinX = GetLandscapeCandidateWorldMinX(Candidate);
    const float LandscapeMinY = -Candidate.HorizontalSpanYCm * 0.5f;
    float PreviousStationM = -1.0f;
    int32 SpawnedCount = 0;
    for (const TSharedPtr<FJsonValue>& RapidValue : *RapidValues)
    {
        const TSharedPtr<FJsonObject> Rapid = RapidValue ? RapidValue->AsObject() : nullptr;
        if (!Rapid.IsValid())
        {
            return false;
        }
        const float StationM = static_cast<float>(Rapid->GetNumberField(TEXT("station_m")));
        if (StationM < PreviousStationM || StationM > SourcePoints.Last().StationMeters)
        {
            OutSummary += TEXT("Scenario rapid stations are not monotonic or leave the candidate centerline.\n");
            return false;
        }
        PreviousStationM = StationM;

        FVector2D LocalCm = SourcePoints.Last().LocalCm;
        FVector2D Tangent = FVector2D(1.0f, 0.0f);
        for (int32 PointIndex = 0; PointIndex + 1 < SourcePoints.Num(); ++PointIndex)
        {
            const FRaftSimLandscapeCandidateCenterlinePoint& A = SourcePoints[PointIndex];
            const FRaftSimLandscapeCandidateCenterlinePoint& B = SourcePoints[PointIndex + 1];
            if (StationM > B.StationMeters)
            {
                continue;
            }
            const float SpanM = FMath::Max(B.StationMeters - A.StationMeters, KINDA_SMALL_NUMBER);
            const float Alpha = FMath::Clamp((StationM - A.StationMeters) / SpanM, 0.0f, 1.0f);
            LocalCm = FMath::Lerp(A.LocalCm, B.LocalCm, Alpha);
            Tangent = (B.LocalCm - A.LocalCm).GetSafeNormal();
            break;
        }
        const FVector2D WorldXY(LandscapeMinX + LocalCm.X, LandscapeMinY + LocalCm.Y);
        const float TerrainZ = Landscape->GetHeightAtLocation(
            FVector(WorldXY.X, WorldXY.Y, 0.0f),
            EHeightfieldSource::Editor).Get(0.0f);
        const FString RapidNumber = Rapid->GetStringField(TEXT("rapid_number"));
        const FString DisplayName = Rapid->GetStringField(TEXT("display_name"));
        const bool bMandatoryPortage = Rapid->GetBoolField(TEXT("mandatory_commercial_portage"));

        AStaticMeshActor* MarkerActor = World->SpawnActor<AStaticMeshActor>(
            FVector(WorldXY.X, WorldXY.Y, TerrainZ + 650.0f),
            FRotator::ZeroRotator);
        if (!MarkerActor)
        {
            return false;
        }
        UStaticMeshComponent* MarkerMesh = MarkerActor->GetStaticMeshComponent();
        MarkerMesh->SetStaticMesh(ConeMesh);
        MarkerMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        MarkerMesh->SetWorldScale3D(FVector(4.0f, 4.0f, 12.0f));
        MarkerMesh->SetCastShadow(false);
        MarkerActor->SetActorHiddenInGame(true);
        MarkerActor->SetActorLabel(FString::Printf(
            TEXT("RaftSim_ZambeziRapid_%s_%s"),
            *RapidNumber,
            *DisplayName.Replace(TEXT(" "), TEXT("_"))));
        MarkerActor->Tags.Add(TEXT("RaftSimScenarioMarker"));
        MarkerActor->Tags.Add(TEXT("RaftSimZambeziRun"));
        if (bMandatoryPortage)
        {
            MarkerActor->Tags.Add(TEXT("RaftSimMandatoryPortage"));
        }

        UTextRenderComponent* Label = NewObject<UTextRenderComponent>(MarkerActor);
        Label->SetupAttachment(MarkerMesh);
        Label->SetText(FText::FromString(FString::Printf(
            TEXT("%s  %s%s"),
            *RapidNumber,
            *DisplayName,
            bMandatoryPortage ? TEXT("  PORTAGE") : TEXT(""))));
        Label->SetTextRenderColor(bMandatoryPortage ? FColor::Red : FColor(255, 170, 45));
        Label->SetHorizontalAlignment(EHorizTextAligment::EHTA_Center);
        Label->SetWorldSize(1100.0f);
        Label->SetRelativeLocation(FVector(0.0f, 0.0f, 150.0f));
        Label->SetRelativeRotation(FRotator(-90.0f, FMath::RadiansToDegrees(
            FMath::Atan2(Tangent.Y, Tangent.X)), 0.0f));
        Label->SetHiddenInGame(true);
        Label->RegisterComponent();
        ++SpawnedCount;
    }
    OutSummary += FString::Printf(
        TEXT("Added %d review-gated Zambezi scenario rapid markers from %s; map labels are editor-only and Rapid 9 carries the mandatory-portage tag.\n"),
        SpawnedCount,
        *Candidate.ScenarioRelativePath);
    return SpawnedCount == RapidValues->Num();
}

bool AddLandscapeCandidateRunnableGameplay(
    UWorld* World,
    ALandscape* Landscape,
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    FString& OutSummary)
{
    if (!World || !Landscape)
    {
        return false;
    }
    const bool bZambezi =
        Candidate.PreviewSpec.RiverId == TEXT("zambezi_batoka_gorge");
    const bool bPacuare = Candidate.PreviewSpec.RiverId == TEXT("pacuare");
    const bool bColoradoHance =
        Candidate.PreviewSpec.RiverId == TEXT("colorado_river");
    if (!bZambezi && !bPacuare && !bColoradoHance)
    {
        return true;
    }

    FString RuntimeConfigLabel;
    FString CookedFieldsDir;
    FName FlowBand;
    FVector2D WindowCenterM;
    float WindowExtentM = 0.0f;
    FString CoordinateMapPath;
    FName RunTag;
    FString PlayerRaftLabel;
    FString DisplayName;
    if (bPacuare)
    {
        RuntimeConfigLabel = TEXT("RaftSim_PacuareUpperHuacas_RuntimeWaterConfig");
        CookedFieldsDir =
            TEXT("physics/data/real_world/pacuare_river_costa_rica/"
                 "scenario_upper_huacas/cooked_flow_fields");
        FlowBand = FName(TEXT("rainfed_runnable_planning"));
        WindowCenterM = FVector2D(300.0f, 0.0f);
        WindowExtentM = 700.0f;
        CoordinateMapPath =
            TEXT("physics/data/real_world/pacuare_river_costa_rica/terrain/"
                 "upper_huacas_visual/upper_huacas_runtime_coordinate_map.json");
        RunTag = FName(TEXT("RaftSimPacuareUpperHuacasRun"));
        PlayerRaftLabel = TEXT("RaftSim_PacuareUpperHuacas_PlayerRaft");
        DisplayName = TEXT("Pacuare Upper Huacas");
    }
    else if (bColoradoHance)
    {
        RuntimeConfigLabel = TEXT("RaftSim_ColoradoHance_RuntimeWaterConfig");
        CookedFieldsDir =
            TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/"
                 "scenario_hance/cooked_flow_fields");
        FlowBand = FName(TEXT("moderate_release_planning"));
        WindowCenterM = FVector2D(300.0f, 0.0f);
        WindowExtentM = 700.0f;
        CoordinateMapPath =
            TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/terrain/"
                 "hance_visual/hance_runtime_coordinate_map.json");
        RunTag = FName(TEXT("RaftSimColoradoHanceRun"));
        PlayerRaftLabel = TEXT("RaftSim_ColoradoHance_PlayerRaft");
        DisplayName = TEXT("Colorado Hance");
    }
    else
    {
        RuntimeConfigLabel = TEXT("RaftSim_Zambezi_RuntimeWaterConfig");
        CookedFieldsDir =
            TEXT("physics/data/real_world/zambezi_batoka_gorge/"
                 "scenario_zambezi_run/runtime/cooked_flow_fields");
        FlowBand = FName(TEXT("normal_big_water"));
        WindowCenterM = FVector2D(15000.0f, 0.0f);
        WindowExtentM = 32000.0f;
        CoordinateMapPath =
            TEXT("physics/data/real_world/zambezi_batoka_gorge/"
                 "scenario_zambezi_run/runtime/river_coordinate_map.json");
        RunTag = FName(TEXT("RaftSimZambeziRun"));
        PlayerRaftLabel = TEXT("RaftSim_Zambezi_PlayerRaft");
        DisplayName = TEXT("Zambezi");
    }

    TArray<FRaftSimLandscapeCandidateCenterlinePoint> Points;
    if (!LoadLandscapeCandidateLocalCenterline(Candidate, Points, OutSummary) ||
        Points.Num() < 2)
    {
        return false;
    }

    const bool bReachLocalRun = bPacuare || bColoradoHance;
    const float StartProgress = bReachLocalRun ? 0.04f : 0.0025f;
    FVector2D StartTangent2D(1.0f, 0.0f);
    const FVector2D StartXY = SampleLandscapeCandidateCenterlineWorld(
        Candidate,
        Points,
        StartProgress,
        &StartTangent2D);
    float SurfaceWorldZ = 0.0f;
    if (!SampleLandscapeCandidateConditionedVisualSurfaceWorldZ(
            Candidate,
            Points,
            StartProgress,
            SurfaceWorldZ))
    {
        SurfaceWorldZ = Landscape->GetHeightAtLocation(
            FVector(StartXY.X, StartXY.Y, 0.0f),
            EHeightfieldSource::Editor).Get(0.0f) + 140.0f;
    }
    SurfaceWorldZ += Candidate.PreviewSpec.FlowWaterLevelOffsetCm;
    const FVector StartTangent(StartTangent2D.X, StartTangent2D.Y, 0.0f);
    const FRotator StartRotation = StartTangent.Rotation();

    UClass* RuntimeGameMode = LoadClass<AGameModeBase>(
        nullptr,
        TEXT("/Script/SmokeEmIfYouGotEm.RaftSimVerticalSliceGameMode"));
    if (!RuntimeGameMode)
    {
        OutSummary += FString::Printf(
            TEXT("Could not load RaftSimVerticalSliceGameMode for %s.\n"),
            *Candidate.PreviewSpec.RiverId);
        return false;
    }
    World->GetWorldSettings()->DefaultGameMode = RuntimeGameMode;

    ARaftSimRiverWaterConfig* WaterConfig =
        World->SpawnActor<ARaftSimRiverWaterConfig>(
            ARaftSimRiverWaterConfig::StaticClass(),
            FTransform::Identity);
    if (!WaterConfig)
    {
        OutSummary += FString::Printf(
            TEXT("Could not spawn the runtime water config for %s.\n"),
            *Candidate.PreviewSpec.RiverId);
        return false;
    }
    WaterConfig->SetActorLabel(RuntimeConfigLabel);
    WaterConfig->CookedFieldsDir = CookedFieldsDir;
    WaterConfig->FlowBand = FlowBand;
    WaterConfig->WindowCenterM = WindowCenterM;
    WaterConfig->WindowExtentM = WindowExtentM;
    WaterConfig->bRecenterHydraulicCrux = false;
    WaterConfig->CoordinateMapPath = CoordinateMapPath;
    WaterConfig->bEnableMovingWindowStreaming = false;
    WaterConfig->bMapProvidesTerrain = true;
    WaterConfig->Tags.AddUnique(RunTag);
    WaterConfig->Tags.AddUnique(TEXT("RaftSimProceduralRuntimeWater"));
    WaterConfig->Tags.AddUnique(TEXT("RaftSimGlobalRiverStationAuthority"));
    WaterConfig->Tags.AddUnique(TEXT("RaftSimSafeLaunchApron"));

    // Author the launch at loaded hydrostatic equilibrium instead of dropping
    // the raft from above the surface. The reduced body saturates over one
    // tube diameter and provides 2.6x weight at full immersion, so the calm
    // tube-center waterline is 2R / 2.6 below the sampled surface. Starting at
    // +58 cm caused an underdamped first plunge, false deck-water retention,
    // and a capsize before the guide could issue a command.
    constexpr float LaunchTubeRadiusCm = 28.0f;
    constexpr float LaunchBuoyancyWeightMultiple = 2.6f;
    constexpr float LaunchHydrostaticOffsetCm =
        -(2.0f * LaunchTubeRadiusCm) / LaunchBuoyancyWeightMultiple;
    ARaftSimRaftActor* Raft = World->SpawnActor<ARaftSimRaftActor>(
        ARaftSimRaftActor::StaticClass(),
        FTransform(
            StartRotation,
            FVector(StartXY.X, StartXY.Y, SurfaceWorldZ + LaunchHydrostaticOffsetCm)));
    if (!Raft)
    {
        OutSummary += FString::Printf(
            TEXT("Could not spawn the player raft for %s.\n"),
            *Candidate.PreviewSpec.RiverId);
        return false;
    }
    Raft->SetActorLabel(PlayerRaftLabel);
    Raft->Tags.AddUnique(RunTag);
    Raft->Tags.AddUnique(TEXT("RaftSimReferenceRunnable"));

    bool bPlayerStartPositioned = false;
    for (TActorIterator<APlayerStart> It(World); It; ++It)
    {
        if (It->GetActorLabel() != TEXT("RaftSim_GuideSeat_PlayerStart"))
        {
            continue;
        }
        It->SetActorLocationAndRotation(
            FVector(StartXY.X, StartXY.Y, SurfaceWorldZ + 170.0f) -
                StartTangent * 500.0f,
            StartRotation);
        It->Tags.AddUnique(RunTag);
        bPlayerStartPositioned = true;
        break;
    }
    if (!bPlayerStartPositioned)
    {
        OutSummary += FString::Printf(
            TEXT("Could not position the player start for %s.\n"),
            *Candidate.PreviewSpec.RiverId);
        return false;
    }

    if (bReachLocalRun)
    {
        // The authored ribbon is used for deterministic editor captures. In
        // gameplay, hide it so the solver-driven ARaftSimWaterSurfaceActor is
        // the only visible surface and the same cooked field owns forces and
        // hydraulics.
        const FString RibbonLabel = FString::Printf(
            TEXT("RaftSim_PhysicalCorridorRiverRibbon_%s"),
            *Candidate.PreviewSpec.RiverId);
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            if (!It->GetActorLabel().Contains(RibbonLabel) &&
                !It->Tags.Contains(TEXT("RaftSimCaptureOnlyWater")))
            {
                continue;
            }
            It->SetActorHiddenInGame(true);
            It->Tags.AddUnique(TEXT("RaftSimCaptureOnlyStaticWater"));
            It->Tags.AddUnique(TEXT("RaftSimLiveSolverWaterOwnsRuntimeRendering"));
        }
    }

    OutSummary += FString::Printf(
        TEXT("Added reference-runnable %s gameplay at station %.1f m: "
             "live cooked-field water, player raft, player start, and vertical-slice "
             "game mode; terrain, flow calibration, and production art remain review-gated.\n"),
        *DisplayName,
        Points.Last().StationMeters * StartProgress);
    return true;
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
        SetCamera(TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"), 0.650f, 0.750f, 260.0f, 105.0f);
        SetCamera(TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"), 0.685f, 0.785f, 170.0f, 85.0f);
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
    else if (Candidate.PreviewSpec.RiverId == TEXT("pacuare"))
    {
        SetCamera(TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"), 0.405f, 0.490f, 420.0f, 145.0f);
        SetCamera(TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"), 0.445f, 0.505f, 285.0f, 125.0f);
    }
    else
    {
        SetCamera(TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"), 0.250f, 0.365f, 330.0f, 180.0f);
        SetCamera(TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"), 0.275f, 0.390f, 270.0f, 165.0f);
    }
    if (Candidate.PreviewSpec.RiverId == TEXT("colorado_river"))
    {
        SetCamera(TEXT("RaftSim_SolverRapid_RiverEyeCaptureCamera"), 0.705f, 0.805f, 185.0f, 90.0f);
    }
    else if (Candidate.PreviewSpec.RiverId == TEXT("pacuare"))
    {
        SetCamera(TEXT("RaftSim_SolverRapid_RiverEyeCaptureCamera"), 0.430f, 0.515f, 330.0f, 130.0f);
    }
    else
    {
        SetCamera(TEXT("RaftSim_SolverRapid_RiverEyeCaptureCamera"), 0.530f, 0.645f, 275.0f, 165.0f);
    }
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
