#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "GameFramework/GameModeBase.h"
#include "GameFramework/WorldSettings.h"
#include "RaftSimRaftActor.h"
#include "RaftSimRiverWaterConfig.h"
#include "RaftSimRockObstacleActor.h"

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
        Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon") &&
        Candidate.HorizontalSpanXCm > 1000000.0f;
    const FRaftSimLandscapeCandidateWaterSettings WaterSettings =
        GetLandscapeCandidateWaterSettings(Candidate.PreviewSpec.RiverId);
    const bool bUseSolverVisualizationFields =
        Candidate.bUseSolverVisualizationFields &&
        WaterSettings.SolverFieldEnable > 0.5f &&
        SolverVisualizationFields &&
        SolverVisualizationFields->IsValid() &&
        SolverFoamMaterial;
    const bool bColoradoHancePresentation =
        Candidate.PreviewSpec.RiverId == TEXT("colorado_river");
    const bool bFutaleufuTerminatorPresentation =
        Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator");
    const bool bChilkoLavaCanyonPresentation =
        Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon");
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

    const int32 CrossSteps = bChilkoSourceScale
        ? 16
        : FMath::Max(8, WaterSettings.RibbonCrossSectionSteps);
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
            const float SolverPersistenceStepU = 4.0f /
                FMath::Max(StationsCm.Last() * 0.01f, 1.0f);
            const float SolverLateralStepV = 4.0f / FMath::Max(
                Candidate.SolverVisualizationLateralMaxM -
                    Candidate.SolverVisualizationLateralMinM,
                1.0f);
            const FLinearColor SolverField = bUseSolverVisualizationFields
                ? SolverVisualizationFields->SampleRawBilinear(
                      SolverU,
                      1.0f - SolverLateralV)
                : FLinearColor::Black;
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
            const FLinearColor SolverFieldDownstream4M =
                bUseSolverVisualizationFields && bColoradoHancePresentation
                ? SolverVisualizationFields->SampleRawBilinear(
                      FMath::Clamp(SolverU + SolverPersistenceStepU, 0.0f, 1.0f),
                      1.0f - SolverLateralV)
                : SolverField;
            const FLinearColor SolverFieldRiverRight4M =
                bUseSolverVisualizationFields && bColoradoHancePresentation
                ? SolverVisualizationFields->SampleRawBilinear(
                      SolverU,
                      1.0f - FMath::Clamp(
                          SolverLateralV - SolverLateralStepV, 0.0f, 1.0f))
                : SolverField;
            const FLinearColor SolverFieldRiverLeft4M =
                bUseSolverVisualizationFields && bColoradoHancePresentation
                ? SolverVisualizationFields->SampleRawBilinear(
                      SolverU,
                      1.0f - FMath::Clamp(
                          SolverLateralV + SolverLateralStepV, 0.0f, 1.0f))
                : SolverField;
            const float MinimumHanceFilterDepthNormalized =
                0.03f / FMath::Max(
                    Candidate.SolverVisualizationDepthCapM, 0.01f);
            const bool bUseHanceSubcellFilter =
                bUseSolverVisualizationFields && bColoradoHancePresentation &&
                SolverField.R > MinimumHanceFilterDepthNormalized &&
                SolverFieldUpstream4M.R > MinimumHanceFilterDepthNormalized &&
                SolverFieldDownstream4M.R > MinimumHanceFilterDepthNormalized &&
                SolverFieldRiverRight4M.R > MinimumHanceFilterDepthNormalized &&
                SolverFieldRiverLeft4M.R > MinimumHanceFilterDepthNormalized;
            const FLinearColor SolverPresentationField = bUseHanceSubcellFilter
                ? SolverField * 0.44f +
                      (SolverFieldUpstream4M + SolverFieldDownstream4M +
                          SolverFieldRiverRight4M + SolverFieldRiverLeft4M) * 0.14f
                : SolverField;
            const float SolverDepthM = SolverPresentationField.R *
                Candidate.SolverVisualizationDepthCapM;
            const float SolverSpeedMps = SolverPresentationField.G *
                Candidate.SolverVisualizationSpeedCapMps;
            const float SolverFroude = SolverPresentationField.B *
                Candidate.SolverVisualizationFroudeCap;
            const float SolverPersistentSpeedMps = FMath::Max3(
                SolverSpeedMps,
                SolverFieldUpstream4M.G * Candidate.SolverVisualizationSpeedCapMps * 0.94f,
                SolverFieldUpstream8M.G * Candidate.SolverVisualizationSpeedCapMps * 0.84f);
            const float SolverPersistentFroude = FMath::Max3(
                SolverFroude,
                SolverFieldUpstream4M.B * Candidate.SolverVisualizationFroudeCap * 0.94f,
                SolverFieldUpstream8M.B * Candidate.SolverVisualizationFroudeCap * 0.84f);
            const float EdgeT = FMath::Abs(V - 0.5f) * 2.0f;
            const float ReliefEdgeEnvelope = 1.0f -
                SmoothPreviewStep(0.68f, 1.0f, EdgeT);
            const float SolverHydraulicPresence = bUseSolverVisualizationFields
                ? SmoothPreviewStep(0.03f, 0.16f, SolverDepthM)
                : 0.0f;
            const float SolverSurfaceReliefCm = bUseSolverVisualizationFields
                ? (SolverPresentationField.A - 0.5f) * 2.0f *
                      Candidate.SolverVisualizationSurfaceReliefCapM * 100.0f *
                      WaterSettings.SolverSurfaceReliefScale * SolverHydraulicPresence *
                      ReliefEdgeEnvelope
                : 0.0f;
            const float SolverHydraulicAerationT = bUseSolverVisualizationFields
                ? SmoothPreviewStep(0.60f, 1.10f, SolverPersistentFroude) *
                      SmoothPreviewStep(0.65f, 2.10f, SolverPersistentSpeedMps) *
                      SolverHydraulicPresence
                : 0.0f;
            const float FlowCueScale = Candidate.PreviewSpec.FlowCurrentCueScale;
            const float WaveEnvelope = ReliefEdgeEnvelope;
            const float SolverAnalyticChopScale = bUseSolverVisualizationFields
                ? WaterSettings.AnalyticChopScale
                : 1.0f;
            const float CrossCurrentPhase =
                FMath::PerlinNoise2D(FVector2D(
                    StationsCm[CenterIndex] * 0.00043f,
                    Lateral * 0.00071f)) * 1.85f;
            const float CrossCurrentChop =
                WaterSettings.CrossCurrentChopAmplitudeCm *
                FMath::Sin(
                    StationsCm[CenterIndex] * 0.0023f -
                    Lateral * 0.0067f + CrossCurrentPhase);
            const float Wave = FlowCueScale * WaveEnvelope * (
                12.0f * FMath::Sin(StationsCm[CenterIndex] * 0.0041f + Lateral * 0.011f) +
                5.0f * FMath::Sin(StationsCm[CenterIndex] * 0.0107f - Lateral * 0.021f) +
                2.5f * FMath::Sin(StationsCm[CenterIndex] * 0.0183f + Lateral * 0.037f) +
                CrossCurrentChop) * SolverAnalyticChopScale;
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
            const float EmbeddedAerationBreakup = SmoothPreviewStep(
                0.70f,
                0.91f,
                BreakerSignal * 0.72f +
                    (FMath::PerlinNoise2D(FVector2D(
                         StationsCm[CenterIndex] * 0.0047f,
                         Lateral * 0.0093f)) * 0.5f + 0.5f) * 0.28f);
            const float EmbeddedAeration = bUseSolverVisualizationFields
                ? WaterSettings.EmbeddedAerationWeight *
                      SmoothPreviewStep(0.75f, 2.80f, SolverPersistentSpeedMps) *
                      SolverHydraulicPresence * EmbeddedAerationBreakup *
                      ReliefEdgeEnvelope
                : 0.0f;
            const float Breaker = bUseSolverVisualizationFields
                ? SolverHydraulicAerationT * WaterSettings.SolverFroudeAerationWeight
                : FlowCueScale * WaveEnvelope *
                      SmoothPreviewStep(0.72f, 0.92f, BreakerSignal) * 0.72f;
            const float CombinedBreaker = FMath::Max(Breaker, EmbeddedAeration);
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
                CombinedBreaker);
            if (bColoradoHancePresentation && bUseSolverVisualizationFields)
            {
                // Suspended sediment makes Hance less transparent than the
                // clear-water runs, but the V1 opaque card was not plausible.
                // Alpha follows only the already sampled solver depth, wet-bank
                // edge, and aeration. It never changes geometry, wetness,
                // collision, bathymetry, hydraulics, or raft forces.
                const float DepthOpacityT = SmoothPreviewStep(
                    0.20f, 2.90f, SolverDepthM);
                const float BankTransmission = FMath::Lerp(
                    1.0f,
                    0.42f,
                    SmoothPreviewStep(0.70f, 1.0f, EdgeT));
                const float WaterOpacity = FMath::Lerp(
                    0.46f, 0.76f, DepthOpacityT) * BankTransmission;
                SurfaceColor.A = FMath::Lerp(
                    WaterOpacity, 0.93f, CombinedBreaker);
            }
            if (bFutaleufuTerminatorPresentation &&
                bUseSolverVisualizationFields)
            {
                // The V3 capture ribbon is transmitting rather than an opaque
                // card. CPU-authored alpha follows the already sampled local
                // depth, fades through the wet-bank edge, and becomes nearly
                // opaque only in solver-conditioned aeration. It changes no
                // geometry, wet mask, collision, or runtime force input.
                const float DepthOpacityT = SmoothPreviewStep(
                    0.18f, 2.80f, SolverDepthM);
                const float BankTransmission = FMath::Lerp(
                    1.0f,
                    0.48f,
                    SmoothPreviewStep(0.72f, 1.0f, EdgeT));
                const float WaterOpacity = FMath::Lerp(
                    0.44f, 0.80f, DepthOpacityT) * BankTransmission;
                SurfaceColor.A = FMath::Lerp(
                    WaterOpacity, 0.93f, CombinedBreaker);
            }
            if (bChilkoLavaCanyonPresentation &&
                bUseSolverVisualizationFields)
            {
                // Clear glacial water remains more transmitting than the
                // shared cold-water V2 card. Alpha uses only local depth,
                // wet-bank feather, and solver aeration already sampled here.
                const float DepthOpacityT = SmoothPreviewStep(
                    0.16f, 2.60f, SolverDepthM);
                const float BankTransmission = FMath::Lerp(
                    1.0f,
                    0.44f,
                    SmoothPreviewStep(0.72f, 1.0f, EdgeT));
                const float WaterOpacity = FMath::Lerp(
                    0.38f, 0.72f, DepthOpacityT) * BankTransmission;
                SurfaceColor.A = FMath::Lerp(
                    WaterOpacity, 0.91f, CombinedBreaker);
            }
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
                    bColoradoHancePresentation ? 0.42f : 0.34f,
                    bColoradoHancePresentation ? 0.74f : 0.70f,
                    FMath::Clamp(FoamNoiseA * 0.68f + FoamNoiseB * 0.32f, 0.0f, 1.0f));
                const float FoamBaseCoverage =
                    bColoradoHancePresentation ? 0.22f : 0.28f;
                const float FoamBreakupCoverage = 1.0f - FoamBaseCoverage;
                const float FoamGain = bColoradoHancePresentation ? 0.96f : 0.94f;
                const float FoamOpacity = FMath::Clamp(
                    SolverHydraulicAerationT *
                        (FoamBaseCoverage + FoamBreakup * FoamBreakupCoverage) *
                        FoamGain,
                    0.0f,
                    bColoradoHancePresentation ? 0.82f : 0.94f);
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
        Normal = FMath::Lerp(
            Normal,
            FVector::UpVector,
            bColoradoHancePresentation
                ? WaterSettings.RenderNormalUpBlend
                : 0.24f).GetSafeNormal();
    }
    OutSummary += FString::Printf(
        TEXT("Built source-aligned physical river ribbon with %d center samples at %.1f m spacing (%d using the manifest-recorded conditioned visual surface), %d cross steps, bounded render-only current relief below %.1f centimetres, and %s breaker coloration across %.1f m.\n"),
        Centers.Num(),
        CenterSampleSpacingCm * 0.01f,
        ConditionedProfileCenterCount,
        CrossSteps,
        Candidate.SolverVisualizationSurfaceReliefCapM * 100.0f *
            WaterSettings.SolverSurfaceReliefScale,
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
            WaterActor->Tags.AddUnique(TEXT("RaftSimZambeziDefaultLitWater"));
            WaterActor->Tags.AddUnique(TEXT("RaftSimMovingMultiScaleWaterNormals"));
            WaterActor->Tags.AddUnique(TEXT("RaftSimSingleLayerWaterCaptureRejected"));
        }
        else if (Candidate.PreviewSpec.RiverId == TEXT("pacuare"))
        {
            WaterActor->Tags.AddUnique(TEXT("RaftSimPacuareDefaultLitWater"));
            WaterActor->Tags.AddUnique(TEXT("RaftSimMovingMultiScaleWaterNormals"));
            WaterActor->Tags.AddUnique(TEXT("RaftSimSingleLayerWaterCaptureRejected"));
        }
        else if (Candidate.PreviewSpec.RiverId == TEXT("colorado_river"))
        {
            WaterActor->Tags.AddUnique(TEXT("RaftSimColoradoHanceDefaultLitWater"));
            WaterActor->Tags.AddUnique(TEXT("RaftSimMovingMultiScaleWaterNormals"));
            WaterActor->Tags.AddUnique(TEXT("RaftSimCpuAuthoredCookedFieldColor"));
            WaterActor->Tags.AddUnique(
                TEXT("RaftSimColoradoHanceSubcellSmoothedWaterV1"));
            WaterActor->Tags.AddUnique(TEXT("RaftSimRenderOnlyHydraulicSmoothing"));
            WaterActor->Tags.AddUnique(TEXT("RaftSimNoSolverStateMutation"));
        }
        else if (Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator"))
        {
            WaterActor->Tags.AddUnique(TEXT("RaftSimFutaleufuDefaultLitWater"));
            WaterActor->Tags.AddUnique(TEXT("RaftSimMovingMultiScaleWaterNormals"));
            WaterActor->Tags.AddUnique(TEXT("RaftSimCpuAuthoredCookedFieldColor"));
            WaterActor->Tags.AddUnique(TEXT("RaftSimColdWaterCpuChopV2"));
            WaterActor->Tags.AddUnique(TEXT("RaftSimColdWaterEmbeddedAerationV2"));
        }
        else if (Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon"))
        {
            WaterActor->Tags.AddUnique(TEXT("RaftSimChilkoDefaultLitWater"));
            WaterActor->Tags.AddUnique(TEXT("RaftSimMovingMultiScaleWaterNormals"));
            WaterActor->Tags.AddUnique(TEXT("RaftSimCpuAuthoredCookedFieldColor"));
            WaterActor->Tags.AddUnique(TEXT("RaftSimColdWaterCpuChopV2"));
            WaterActor->Tags.AddUnique(TEXT("RaftSimColdWaterEmbeddedAerationV2"));
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
                FoamActor->Tags.AddUnique(TEXT("RaftSimColoradoHanceLaceFoamV1"));
                FoamActor->Tags.AddUnique(TEXT("RaftSimNoSolverStateMutation"));
            }
            else if (Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon"))
            {
                FoamActor->Tags.AddUnique(
                    TEXT("RaftSimChilkoLavaCanyonSolverVisualization"));
                FoamActor->Tags.AddUnique(TEXT("RaftSimChilkoCaptureOnlyWater"));
            }
            else if (Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator"))
            {
                FoamActor->Tags.AddUnique(
                    TEXT("RaftSimFutaleufuTerminatorSolverVisualization"));
                FoamActor->Tags.AddUnique(TEXT("RaftSimFutaleufuCaptureOnlyWater"));
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
                // Batoka's adaptive near-field mesh authors the only approved
                // wet-bank red channel. Keep the coarse source-terrain tiles at zero
                // so the shared material cannot turn the full gorge wet.
                if (bZambezi)
                {
                    SourceLinear.R = 0.0f;
                }
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

bool AddZambeziAdaptiveNearFieldTerrain(
    UWorld* World,
    ALandscape* Landscape,
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    UMaterialInterface* TerrainMaterial,
    FZambeziAdaptiveNearFieldTerrainStats& OutStats,
    FString& OutSummary)
{
    OutStats = FZambeziAdaptiveNearFieldTerrainStats();
    if (!World || !Landscape || !TerrainMaterial ||
        Candidate.PreviewSpec.RiverId != TEXT("zambezi_batoka_gorge"))
    {
        return false;
    }

    TArray<FRaftSimLandscapeCandidateCenterlinePoint> Centerline;
    if (!LoadLandscapeCandidateLocalCenterline(Candidate, Centerline, OutSummary) ||
        Centerline.Num() < 2 || Centerline.Last().StationMeters <= 1000.0f)
    {
        OutSummary += TEXT(
            "Zambezi adaptive near-field terrain requires at least one kilometre "
            "of source-aligned centerline.\n");
        return false;
    }

    FRaftSimPreviewImage SourceAlbedo;
    if (!LoadPreviewPngImage(Candidate.PreviewSpec.AerialDrapeImage, SourceAlbedo))
    {
        OutSummary += TEXT(
            "Zambezi adaptive near-field terrain could not load the source-conditioned "
            "albedo image.\n");
        return false;
    }

    struct FDenseTerrainTile
    {
        AActor* Actor = nullptr;
        FProcMeshSection* Section = nullptr;
        int32 RowSize = 0;
        int32 RowCount = 0;
        float FirstX = 0.0f;
        float FirstY = 0.0f;
        float StepX = 0.0f;
        float StepY = 0.0f;
        float MinimumX = 0.0f;
        float MaximumX = 0.0f;
        float MinimumY = 0.0f;
        float MaximumY = 0.0f;
    };

    TArray<FDenseTerrainTile> DenseTiles;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (!Actor || !Actor->GetActorLabel().StartsWith(
                TEXT("RaftSim_PhysicalCorridorDenseSourceTerrainTile_")))
        {
            continue;
        }
        UProceduralMeshComponent* Component =
            Actor->FindComponentByClass<UProceduralMeshComponent>();
        FProcMeshSection* Section = Component
            ? Component->GetProcMeshSection(0)
            : nullptr;
        if (!Section || Section->ProcVertexBuffer.Num() < 4)
        {
            continue;
        }

        int32 RowSize = 0;
        const float FirstRowY = Section->ProcVertexBuffer[0].Position.Y;
        while (RowSize < Section->ProcVertexBuffer.Num() &&
               FMath::IsNearlyEqual(
                   Section->ProcVertexBuffer[RowSize].Position.Y,
                   FirstRowY,
                   0.1f))
        {
            ++RowSize;
        }
        if (RowSize < 2 || Section->ProcVertexBuffer.Num() % RowSize != 0)
        {
            OutSummary += FString::Printf(
                TEXT("Zambezi adaptive terrain refused non-grid source tile %s.\n"),
                *Actor->GetActorLabel());
            return false;
        }
        const int32 RowCount = Section->ProcVertexBuffer.Num() / RowSize;
        if (RowCount < 2)
        {
            return false;
        }

        const FVector First = FVector(Section->ProcVertexBuffer[0].Position);
        const FVector LastX = FVector(
            Section->ProcVertexBuffer[RowSize - 1].Position);
        const FVector LastY = FVector(
            Section->ProcVertexBuffer[(RowCount - 1) * RowSize].Position);
        FDenseTerrainTile& Tile = DenseTiles.AddDefaulted_GetRef();
        Tile.Actor = Actor;
        Tile.Section = Section;
        Tile.RowSize = RowSize;
        Tile.RowCount = RowCount;
        Tile.FirstX = First.X;
        Tile.FirstY = First.Y;
        Tile.StepX = (LastX.X - First.X) / static_cast<float>(RowSize - 1);
        Tile.StepY = (LastY.Y - First.Y) / static_cast<float>(RowCount - 1);
        Tile.MinimumX = FMath::Min(First.X, LastX.X);
        Tile.MaximumX = FMath::Max(First.X, LastX.X);
        Tile.MinimumY = FMath::Min(First.Y, LastY.Y);
        Tile.MaximumY = FMath::Max(First.Y, LastY.Y);
        if (FMath::Abs(Tile.StepX) < 1.0f || FMath::Abs(Tile.StepY) < 1.0f)
        {
            OutSummary += TEXT(
                "Zambezi adaptive terrain found an invalid dense-tile sample spacing.\n");
            return false;
        }
    }
    if (DenseTiles.Num() != 4)
    {
        OutSummary += FString::Printf(
            TEXT("Zambezi adaptive terrain requires all four conditioned dense tiles; found %d.\n"),
            DenseTiles.Num());
        return false;
    }

    auto SampleDenseTerrainWorldZ = [&DenseTiles](
                                        const FVector2D& WorldPoint,
                                        float& OutWorldZ)
    {
        for (const FDenseTerrainTile& Tile : DenseTiles)
        {
            const FTransform Transform = Tile.Actor->GetActorTransform();
            const FVector LocalPoint = Transform.InverseTransformPosition(
                FVector(WorldPoint.X, WorldPoint.Y, Transform.GetLocation().Z));
            if (LocalPoint.X < Tile.MinimumX - 0.5f ||
                LocalPoint.X > Tile.MaximumX + 0.5f ||
                LocalPoint.Y < Tile.MinimumY - 0.5f ||
                LocalPoint.Y > Tile.MaximumY + 0.5f)
            {
                continue;
            }
            const float GridX = (LocalPoint.X - Tile.FirstX) / Tile.StepX;
            const float GridY = (LocalPoint.Y - Tile.FirstY) / Tile.StepY;
            const int32 X0 = FMath::Clamp(
                FMath::FloorToInt(GridX), 0, Tile.RowSize - 2);
            const int32 Y0 = FMath::Clamp(
                FMath::FloorToInt(GridY), 0, Tile.RowCount - 2);
            const float FracX = FMath::Clamp(GridX - static_cast<float>(X0), 0.0f, 1.0f);
            const float FracY = FMath::Clamp(GridY - static_cast<float>(Y0), 0.0f, 1.0f);
            const int32 A = Y0 * Tile.RowSize + X0;
            const int32 B = A + 1;
            const int32 C = (Y0 + 1) * Tile.RowSize + X0;
            const int32 D = C + 1;
            const float LowerZ = FMath::Lerp(
                Tile.Section->ProcVertexBuffer[A].Position.Z,
                Tile.Section->ProcVertexBuffer[B].Position.Z,
                FracX);
            const float UpperZ = FMath::Lerp(
                Tile.Section->ProcVertexBuffer[C].Position.Z,
                Tile.Section->ProcVertexBuffer[D].Position.Z,
                FracX);
            const float LocalZ = FMath::Lerp(LowerZ, UpperZ, FracY);
            OutWorldZ = Transform.TransformPosition(
                FVector(LocalPoint.X, LocalPoint.Y, LocalZ)).Z;
            return true;
        }
        return false;
    };

    constexpr float StartStationM = 0.0f;
    constexpr float EndStationM = 1000.0f;
    // V2 resolves the source-missing guide-eye bank at 2.5 m, then moves only
    // interior presentation vertices by less than one quarter of a cell. The
    // non-colliding mesh can therefore break the regular DEM tessellation
    // without changing the source Landscape's collision or height authority.
    constexpr float LongitudinalSpacingCm = 250.0f;
    constexpr float LateralSpacingCm = 250.0f;
    constexpr float MaximumStationJitterCm = 55.0f;
    constexpr float MaximumLateralJitterCm = 42.0f;
    constexpr float OuterBankDistanceCm = 60000.0f;
    constexpr float SurfaceLiftCm = 3.0f;
    constexpr float MaximumDryShorelineInfillCm = 180.0f;
    constexpr float MaximumUpperDryScarpRefinementCm = 440.0f;
    constexpr float UpperDryScarpRefinementStartAboveWaterCm = 600.0f;
    constexpr float UpperDryScarpRefinementFullStrengthAboveWaterCm = 1800.0f;
    const float ActiveWaterHalfWidthCm =
        GetPreviewActiveRiverHalfWidthCm(Candidate.PreviewSpec);
    const float InnerBankDistanceCm = ActiveWaterHalfWidthCm + 300.0f;
    const int32 LongitudinalStepCount = FMath::RoundToInt(
        (EndStationM - StartStationM) * 100.0f / LongitudinalSpacingCm);
    const int32 LateralStepCount = FMath::RoundToInt(
        (OuterBankDistanceCm - InnerBankDistanceCm) / LateralSpacingCm);
    const int32 RowSize = LateralStepCount + 1;
    const int32 RowCount = LongitudinalStepCount + 1;
    OutStats.LongitudinalSpacingCm = LongitudinalSpacingCm;
    OutStats.LateralSpacingCm = LateralSpacingCm;

    const float LandscapeMinX = GetLandscapeCandidateWorldMinX(Candidate);
    const float LandscapeMinY = -Candidate.HorizontalSpanYCm * 0.5f;
    const float RouteStartStation = Centerline[0].StationMeters;
    const float RouteStationSpan =
        Centerline.Last().StationMeters - RouteStartStation;
    for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
    {
        const float Side = SideIndex == 0 ? -1.0f : 1.0f;
        TArray<FVector> Vertices;
        TArray<FVector2D> Uvs;
        TArray<FLinearColor> VertexColors;
        TArray<int32> Triangles;
        TArray<float> WaterSurfaceZ;
        TArray<float> RefinementFades;
        TArray<bool> RenderableVertices;
        const int32 VertexCapacity = RowSize * RowCount;
        Vertices.Reserve(VertexCapacity);
        Uvs.Reserve(VertexCapacity);
        VertexColors.Reserve(VertexCapacity);
        WaterSurfaceZ.Reserve(VertexCapacity);
        RefinementFades.Reserve(VertexCapacity);
        RenderableVertices.Reserve(VertexCapacity);
        Triangles.Reserve(LongitudinalStepCount * LateralStepCount * 6);

        for (int32 StationIndex = 0;
             StationIndex <= LongitudinalStepCount;
             ++StationIndex)
        {
            const float StationT = static_cast<float>(StationIndex) /
                static_cast<float>(LongitudinalStepCount);
            const float StationM = FMath::Lerp(
                StartStationM, EndStationM, StationT);
            const float Progress = FMath::Clamp(
                (StationM - RouteStartStation) / RouteStationSpan,
                0.0f,
                1.0f);
            FVector2D Tangent;
            const FVector2D Center = SampleLandscapeCandidateCenterlineWorld(
                Candidate,
                Centerline,
                Progress,
                &Tangent);
            const FVector2D BankNormal(-Tangent.Y, Tangent.X);
            float ConditionedWaterZ = 0.0f;
            if (!SampleLandscapeCandidateConditionedVisualSurfaceWorldZ(
                    Candidate,
                    Centerline,
                    Progress,
                    ConditionedWaterZ))
            {
                OutSummary += TEXT(
                    "Zambezi adaptive terrain requires the conditioned visual water profile.\n");
                return false;
            }

            for (int32 LateralIndex = 0;
                 LateralIndex <= LateralStepCount;
                 ++LateralIndex)
            {
                const float LateralT = static_cast<float>(LateralIndex) /
                    static_cast<float>(LateralStepCount);
                const float BankDistanceCm = FMath::Lerp(
                    InnerBankDistanceCm, OuterBankDistanceCm, LateralT);
                const float PlanarJitterFade =
                    SmoothPreviewStep(0.0f, 2000.0f, StationM * 100.0f) *
                    (1.0f - SmoothPreviewStep(
                        EndStationM * 100.0f - 2000.0f,
                        EndStationM * 100.0f,
                        StationM * 100.0f)) *
                    FMath::Sin(PI * LateralT);
                const FVector2D JitterCoordinate(
                    StationM * 0.071f + Side * 17.0f,
                    BankDistanceCm * 0.00023f - Side * 29.0f);
                const float StationJitterCm = PlanarJitterFade *
                    MaximumStationJitterCm * FMath::PerlinNoise2D(
                        JitterCoordinate);
                const float LateralJitterCm = PlanarJitterFade *
                    MaximumLateralJitterCm * FMath::PerlinNoise2D(FVector2D(
                        JitterCoordinate.Y * 1.73f + 41.0f,
                        JitterCoordinate.X * 0.67f - 37.0f));
                const float PlanarJitterCm = FVector2D(
                    StationJitterCm, LateralJitterCm).Size();
                if (PlanarJitterCm > 0.5f)
                {
                    ++OutStats.PlanarJitteredVertexCount;
                    OutStats.MaximumPlanarJitterCm = FMath::Max(
                        OutStats.MaximumPlanarJitterCm,
                        PlanarJitterCm);
                }
                const FVector2D WorldPoint =
                    Center + Tangent * StationJitterCm +
                    BankNormal * (Side * (BankDistanceCm + LateralJitterCm));
                float DenseTerrainZ = 0.0f;
                const bool bSampled = SampleDenseTerrainWorldZ(
                    WorldPoint, DenseTerrainZ);
                const float ShorelineRiseT = SmoothPreviewStep(
                    InnerBankDistanceCm,
                    InnerBankDistanceCm + 3000.0f,
                    BankDistanceCm);
                const float RequiredDryHeightCm = FMath::Lerp(
                    35.0f, 130.0f, ShorelineRiseT);
                const float ExistingDryHeightCm =
                    DenseTerrainZ - ConditionedWaterZ;
                const float DryInfillCm = bSampled
                    ? FMath::Clamp(
                          RequiredDryHeightCm - ExistingDryHeightCm,
                          0.0f,
                          MaximumDryShorelineInfillCm)
                    : 0.0f;
                const bool bRenderable = bSampled &&
                    ExistingDryHeightCm + DryInfillCm >= 30.0f;
                if (DryInfillCm > 0.5f)
                {
                    ++OutStats.DryShorelineInfillVertexCount;
                    OutStats.MaximumDryShorelineInfillCm = FMath::Max(
                        OutStats.MaximumDryShorelineInfillCm,
                        DryInfillCm);
                }

                Vertices.Add(FVector(
                    WorldPoint.X,
                    WorldPoint.Y,
                    DenseTerrainZ + DryInfillCm + SurfaceLiftCm));
                const float SourceU = FMath::Clamp(
                    (WorldPoint.X - LandscapeMinX) /
                        Candidate.HorizontalSpanXCm,
                    0.0f,
                    1.0f);
                const float SourceV = FMath::Clamp(
                    1.0f -
                        (WorldPoint.Y - LandscapeMinY) /
                            Candidate.HorizontalSpanYCm,
                    0.0f,
                    1.0f);
                Uvs.Add(FVector2D(SourceU, SourceV));
                const FLinearColor SourceSrgb =
                    SourceAlbedo.SampleRawBilinear(SourceU, SourceV);
                const FColor SourceColor8(
                    static_cast<uint8>(FMath::Clamp(
                        FMath::RoundToInt(SourceSrgb.R * 255.0f), 0, 255)),
                    static_cast<uint8>(FMath::Clamp(
                        FMath::RoundToInt(SourceSrgb.G * 255.0f), 0, 255)),
                    static_cast<uint8>(FMath::Clamp(
                        FMath::RoundToInt(SourceSrgb.B * 255.0f), 0, 255)),
                    0);
                VertexColors.Add(FLinearColor::FromSRGBColor(SourceColor8));
                WaterSurfaceZ.Add(ConditionedWaterZ);
                const float StationEdgeFade =
                    SmoothPreviewStep(0.0f, 8000.0f, StationM * 100.0f) *
                    (1.0f - SmoothPreviewStep(
                        EndStationM * 100.0f - 8000.0f,
                        EndStationM * 100.0f,
                        StationM * 100.0f));
                const float LateralEdgeFade = SmoothPreviewStep(
                        InnerBankDistanceCm + 400.0f,
                        InnerBankDistanceCm + 3600.0f,
                        BankDistanceCm) *
                    (1.0f - SmoothPreviewStep(
                        OuterBankDistanceCm - 8000.0f,
                        OuterBankDistanceCm,
                        BankDistanceCm));
                RefinementFades.Add(
                    StationEdgeFade * LateralEdgeFade *
                    SmoothPreviewStep(80.0f, 500.0f,
                        ExistingDryHeightCm + DryInfillCm));
                RenderableVertices.Add(bRenderable);
            }
        }

        const TArray<FVector> BaseNormals =
            ComputePreviewGridHeightfieldNormals(Vertices, RowSize);
        for (int32 VertexIndex = 0;
             VertexIndex < Vertices.Num();
             ++VertexIndex)
        {
            if (!RenderableVertices[VertexIndex])
            {
                continue;
            }
            const FVector& Position = Vertices[VertexIndex];
            const float Steepness = 1.0f - FMath::Clamp(
                BaseNormals[VertexIndex].Z, 0.0f, 1.0f);
            const float SlopeResponse = FMath::Lerp(
                0.28f,
                1.0f,
                SmoothPreviewStep(0.035f, 0.48f, Steepness));
            // Domain warping prevents the three geomorphic bands from sharing
            // the regular source-grid axes. The broad term follows weathered
            // gorge mass, the middle term breaks basalt-scale faces, and the
            // fine term gives talus-sized normal variation. A narrow paired
            // joint network cuts rather than raises isolated ridges.
            const float WarpX = FMath::PerlinNoise2D(FVector2D(
                Position.X * 0.00017f + Side * 7.0f,
                Position.Y * 0.00017f - Side * 13.0f));
            const float WarpY = FMath::PerlinNoise2D(FVector2D(
                Position.X * 0.00021f - Side * 19.0f,
                Position.Y * 0.00021f + Side * 23.0f));
            const FVector2D WarpedPosition(
                Position.X + WarpX * 4200.0f,
                Position.Y + WarpY * 4200.0f);
            const float BroadErosion = FMath::PerlinNoise2D(
                FVector2D(
                    WarpedPosition.X * 0.00012f + Side * 17.0f,
                    WarpedPosition.Y * 0.00012f - Side * 11.0f));
            const float LocalFracture = FMath::PerlinNoise2D(
                FVector2D(
                    WarpedPosition.X * 0.00047f - Side * 29.0f,
                    WarpedPosition.Y * 0.00047f + Side * 23.0f));
            const float FineTalus = FMath::PerlinNoise2D(
                FVector2D(
                    WarpedPosition.X * 0.00108f + 41.0f,
                    WarpedPosition.Y * 0.00108f - 37.0f));
            const float JointA = FMath::Abs(FMath::Sin(
                WarpedPosition.X * 0.00119f +
                WarpedPosition.Y * 0.00061f + BroadErosion * 1.7f));
            const float JointB = FMath::Abs(FMath::Sin(
                WarpedPosition.X * -0.00073f +
                WarpedPosition.Y * 0.00131f - LocalFracture * 1.3f));
            const float JointCut = -24.0f *
                FMath::Pow(1.0f - FMath::Min(JointA, JointB), 5.0f);
            const float BaseRefinementCm = RefinementFades[VertexIndex] * SlopeResponse *
                (BroadErosion * 72.0f + LocalFracture * 43.0f +
                 FineTalus * 19.0f + JointCut);
            const float PreRefinementDryHeightCm =
                Position.Z - WaterSurfaceZ[VertexIndex];
            const float UpperDryScarpFade = RefinementFades[VertexIndex] *
                SmoothPreviewStep(
                    UpperDryScarpRefinementStartAboveWaterCm,
                    UpperDryScarpRefinementFullStrengthAboveWaterCm,
                    PreRefinementDryHeightCm);
            const float UpperDryScarpSignalCm = SlopeResponse *
                (BroadErosion * 240.0f + LocalFracture * 150.0f +
                 FineTalus * 55.0f + JointCut * 2.8f);
            const float EffectiveRefinementClampCm = FMath::Lerp(
                135.0f,
                MaximumUpperDryScarpRefinementCm,
                UpperDryScarpFade);
            float RefinementCm = FMath::Clamp(
                BaseRefinementCm + UpperDryScarpFade * UpperDryScarpSignalCm,
                -EffectiveRefinementClampCm,
                EffectiveRefinementClampCm);
            const float MinimumRefinementCm =
                WaterSurfaceZ[VertexIndex] + 30.0f - Position.Z;
            RefinementCm = FMath::Max(RefinementCm, MinimumRefinementCm);
            const float AppliedUpperDryScarpRefinementCm =
                RefinementCm - FMath::Clamp(
                    BaseRefinementCm,
                    -135.0f,
                    135.0f);
            Vertices[VertexIndex].Z += RefinementCm;
            if (FMath::Abs(RefinementCm) > 0.5f)
            {
                ++OutStats.RefinedVertexCount;
                OutStats.MaximumAbsoluteRefinementCm = FMath::Max(
                    OutStats.MaximumAbsoluteRefinementCm,
                    FMath::Abs(RefinementCm));
            }
            if (UpperDryScarpFade > KINDA_SMALL_NUMBER &&
                FMath::Abs(AppliedUpperDryScarpRefinementCm) > 0.5f)
            {
                ++OutStats.UpperDryScarpRefinedVertexCount;
                OutStats.MaximumAbsoluteUpperDryScarpRefinementCm = FMath::Max(
                    OutStats.MaximumAbsoluteUpperDryScarpRefinementCm,
                    FMath::Abs(AppliedUpperDryScarpRefinementCm));
                OutStats.MinimumUpperDryScarpHeightAboveWaterCm = FMath::Min(
                    OutStats.MinimumUpperDryScarpHeightAboveWaterCm,
                    PreRefinementDryHeightCm);
            }
            OutStats.MinimumRenderedHeightAboveWaterCm = FMath::Min(
                OutStats.MinimumRenderedHeightAboveWaterCm,
                Vertices[VertexIndex].Z - WaterSurfaceZ[VertexIndex]);

            // The conditioned surface is already sampled at this station. Use
            // its local height to author a bounded procedural wet stain into
            // vertex alpha rather than adding a rectangular shoreline overlay.
            // Two incommensurate noise fields break the edge while the mask is
            // still explicit about having no measured wet-bank authority.
            const float DryHeightAboveWaterCm =
                Vertices[VertexIndex].Z - WaterSurfaceZ[VertexIndex];
            const float BroadWetEdge = FMath::PerlinNoise2D(FVector2D(
                Vertices[VertexIndex].X * 0.00031f + Side * 13.0f,
                Vertices[VertexIndex].Y * 0.00031f - Side * 19.0f));
            const float FineWetEdge = FMath::PerlinNoise2D(FVector2D(
                Vertices[VertexIndex].X * 0.00117f - Side * 31.0f,
                Vertices[VertexIndex].Y * 0.00117f + Side * 37.0f));
            const float WetStainCeilingCm = FMath::Clamp(
                250.0f + BroadWetEdge * 55.0f + FineWetEdge * 24.0f,
                175.0f,
                325.0f);
            const float WetMask = 1.0f - SmoothPreviewStep(
                45.0f,
                WetStainCeilingCm,
                DryHeightAboveWaterCm);
            VertexColors[VertexIndex].R = WetMask;
            if (WetMask > 0.02f)
            {
                ++OutStats.WetBankVertexCount;
                OutStats.MaximumWetBankMask = FMath::Max(
                    OutStats.MaximumWetBankMask,
                    WetMask);
                OutStats.MaximumWetBankHeightAboveWaterCm = FMath::Max(
                    OutStats.MaximumWetBankHeightAboveWaterCm,
                    DryHeightAboveWaterCm);
            }
        }

        for (int32 StationIndex = 0;
             StationIndex < LongitudinalStepCount;
             ++StationIndex)
        {
            for (int32 LateralIndex = 0;
                 LateralIndex < LateralStepCount;
                 ++LateralIndex)
            {
                const int32 A = StationIndex * RowSize + LateralIndex;
                const int32 B = A + 1;
                const int32 C = (StationIndex + 1) * RowSize + LateralIndex;
                const int32 D = C + 1;
                if (!RenderableVertices[A] || !RenderableVertices[B] ||
                    !RenderableVertices[C] || !RenderableVertices[D])
                {
                    continue;
                }
                ++OutStats.TopologyCandidateCellCount;
                const FVector2D A2(Vertices[A].X, Vertices[A].Y);
                const FVector2D B2(Vertices[B].X, Vertices[B].Y);
                const FVector2D C2(Vertices[C].X, Vertices[C].Y);
                const FVector2D D2(Vertices[D].X, Vertices[D].Y);
                const float CrossAbc = FVector2D::CrossProduct(
                    B2 - A2, C2 - A2);
                const float CrossBdc = FVector2D::CrossProduct(
                    D2 - B2, C2 - B2);
                const float AreaAbcCm2 = FMath::Abs(CrossAbc) * 0.5f;
                const float AreaBdcCm2 = FMath::Abs(CrossBdc) * 0.5f;
                constexpr float kMinimumPlanarTriangleAreaCm2 = 2500.0f;
                const bool bExpectedWinding =
                    CrossAbc * Side < 0.0f && CrossBdc * Side < 0.0f;
                if (!bExpectedWinding ||
                    AreaAbcCm2 < kMinimumPlanarTriangleAreaCm2 ||
                    AreaBdcCm2 < kMinimumPlanarTriangleAreaCm2)
                {
                    ++OutStats.TopologyRejectedCellCount;
                    continue;
                }
                OutStats.MinimumPlanarCellAreaCm2 = FMath::Min(
                    OutStats.MinimumPlanarCellAreaCm2,
                    FMath::Min(AreaAbcCm2, AreaBdcCm2));
                if (Side < 0.0f)
                {
                    Triangles.Append({A, C, B, B, C, D});
                }
                else
                {
                    Triangles.Append({A, B, C, B, D, C});
                }
            }
        }
        if (Triangles.IsEmpty())
        {
            OutSummary += TEXT(
                "Zambezi adaptive near-field terrain produced no dry bank triangles.\n");
            return false;
        }

        const TArray<FVector> Normals = ComputePreviewMeshNormals(
            Vertices, Triangles);
        AActor* Actor = AddPreviewProceduralMeshActor(
            World,
            FString::Printf(
                TEXT("RaftSim_ZambeziAdaptiveNearFieldTerrainV2_%sBank"),
                Side < 0.0f ? TEXT("Left") : TEXT("Right")),
            Vertices,
            Triangles,
            Normals,
            Uvs,
            Candidate.PreviewSpec.TerrainColor,
            TerrainMaterial,
            &VertexColors,
            false);
        if (!Actor)
        {
            return false;
        }
        Actor->Tags.AddUnique(TEXT("RaftSimZambeziRun"));
        Actor->Tags.AddUnique(TEXT("RaftSimZambeziAdaptiveNearFieldTerrainV2"));
        Actor->Tags.AddUnique(TEXT("RaftSimIrregularPlanarTopologyV2"));
        Actor->Tags.AddUnique(TEXT("RaftSimDomainWarpedGeomorphicReliefV2"));
        Actor->Tags.AddUnique(TEXT("RaftSimAdaptiveUpperDryScarpReliefV20"));
        Actor->Tags.AddUnique(TEXT("RaftSimSourceConditionedTerrain"));
        Actor->Tags.AddUnique(TEXT("RaftSimProceduralInfill"));
        Actor->Tags.AddUnique(TEXT("RaftSimProtectedDryShoreline"));
        Actor->Tags.AddUnique(TEXT("RaftSimNonCollisionRenderSurface"));
        Actor->Tags.AddUnique(TEXT("RaftSimNearFieldSelfShadowSuppressed"));
        Actor->Tags.AddUnique(TEXT("RaftSimConditionedWaterlineWetBankV1"));
        Actor->Tags.AddUnique(TEXT("RaftSimVertexRedWetBankMask"));
        Actor->Tags.AddUnique(TEXT("RaftSimProceduralWetBankNoMeasuredAuthority"));
        if (UProceduralMeshComponent* Component =
                Actor->FindComponentByClass<UProceduralMeshComponent>())
        {
            Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            Component->SetCastShadow(false);
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimZambeziAdaptiveNearFieldTerrainV2"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimIrregularPlanarTopologyV2"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimDomainWarpedGeomorphicReliefV2"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimAdaptiveUpperDryScarpReliefV20"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimNonCollisionRenderSurface"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimNearFieldSelfShadowSuppressed"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimConditionedWaterlineWetBankV1"));
            Component->ComponentTags.AddUnique(
                TEXT("RaftSimVertexRedWetBankMask"));
            ++OutStats.ShadowSuppressedActorCount;
            if (Component->GetCollisionEnabled() != ECollisionEnabled::NoCollision)
            {
                ++OutStats.CollisionEnabledActorCount;
            }
        }
        ++OutStats.ActorCount;
        OutStats.VertexCount += Vertices.Num();
        OutStats.TriangleCount += Triangles.Num() / 3;
    }

    OutSummary += FString::Printf(
        TEXT("Built %d source-conditioned Zambezi adaptive near-field V2 bank actors "
             "over stations %.0f-%.0f m: %lld vertices, %lld triangles, %.1f m grid, "
             "%lld irregular-plan vertices (maximum jitter %.2f m, minimum triangle "
             "area %.3f m2), %lld/%lld curved-offset cells rejected for inverted or "
             "sub-0.25m2 topology, %lld bounded refinement vertices (maximum %.2f m), "
             "%lld dry-shoreline "
             "infill vertices (maximum %.2f m), minimum rendered clearance %.2f m; "
             "%lld upper dry-scarp vertices received V20 facade refinement "
             "(maximum %.2f m; minimum source height %.2f m above local water); "
             "%lld vertices carry a bounded conditioned-waterline wet-bank mask "
             "(maximum mask %.3f, maximum affected dry height %.2f m); "
             "collision remains disabled and overlay self-shadow is suppressed "
             "after the rejected shadow-wedge bracket.\n"),
        OutStats.ActorCount,
        StartStationM,
        EndStationM,
        OutStats.VertexCount,
        OutStats.TriangleCount,
        LongitudinalSpacingCm * 0.01f,
        OutStats.PlanarJitteredVertexCount,
        OutStats.MaximumPlanarJitterCm * 0.01f,
        OutStats.MinimumPlanarCellAreaCm2 * 0.0001f,
        OutStats.TopologyRejectedCellCount,
        OutStats.TopologyCandidateCellCount,
        OutStats.RefinedVertexCount,
        OutStats.MaximumAbsoluteRefinementCm * 0.01f,
        OutStats.DryShorelineInfillVertexCount,
        OutStats.MaximumDryShorelineInfillCm * 0.01f,
        OutStats.MinimumRenderedHeightAboveWaterCm * 0.01f,
        OutStats.UpperDryScarpRefinedVertexCount,
        OutStats.MaximumAbsoluteUpperDryScarpRefinementCm * 0.01f,
        OutStats.MinimumUpperDryScarpHeightAboveWaterCm * 0.01f,
        OutStats.WetBankVertexCount,
        OutStats.MaximumWetBankMask,
        OutStats.MaximumWetBankHeightAboveWaterCm * 0.01f);
    return OutStats.ActorCount == 2 && OutStats.VertexCount >= 160000 &&
        OutStats.TriangleCount >= 240000 &&
        OutStats.PlanarJitteredVertexCount > 0 &&
        OutStats.MaximumPlanarJitterCm <= 70.0f &&
        OutStats.MinimumPlanarCellAreaCm2 >= 2500.0f &&
        OutStats.TopologyCandidateCellCount > 0 &&
        OutStats.TopologyRejectedCellCount * 20 <=
            OutStats.TopologyCandidateCellCount &&
        OutStats.RefinedVertexCount > 0 &&
        OutStats.UpperDryScarpRefinedVertexCount > 0 &&
        OutStats.MinimumUpperDryScarpHeightAboveWaterCm + 0.5f >=
            UpperDryScarpRefinementStartAboveWaterCm &&
        OutStats.MaximumAbsoluteUpperDryScarpRefinementCm <=
            MaximumUpperDryScarpRefinementCm + 0.5f &&
        OutStats.WetBankVertexCount > 0 &&
        OutStats.MaximumWetBankMask > 0.5f &&
        OutStats.MaximumWetBankHeightAboveWaterCm <= 325.5f &&
        OutStats.MinimumRenderedHeightAboveWaterCm >= 29.5f &&
        OutStats.MaximumAbsoluteRefinementCm <=
            MaximumUpperDryScarpRefinementCm + 0.5f &&
        OutStats.MaximumDryShorelineInfillCm <=
            MaximumDryShorelineInfillCm + 0.5f &&
        OutStats.ShadowSuppressedActorCount == 2 &&
        OutStats.CollisionEnabledActorCount == 0;
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
    const bool bChilkoLavaCanyon =
        Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon");
    const bool bFutaleufuTerminator =
        Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator");
    const bool bReachLocalRun =
        bPacuare || bColoradoHance || bChilkoLavaCanyon || bFutaleufuTerminator;
    const bool bSolverOwnedRuntimeWater = bReachLocalRun || bZambezi;
    if (!bZambezi && !bPacuare && !bColoradoHance && !bChilkoLavaCanyon &&
        !bFutaleufuTerminator)
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
    else if (bChilkoLavaCanyon)
    {
        RuntimeConfigLabel = TEXT("RaftSim_ChilkoLavaCanyon_RuntimeWaterConfig");
        CookedFieldsDir =
            TEXT("physics/data/real_world/chilko_river_lava_canyon/"
                 "scenario_lava_canyon/cooked_flow_fields");
        FlowBand = FName(TEXT("median_runnable"));
        WindowCenterM = FVector2D(300.0f, 0.0f);
        WindowExtentM = 700.0f;
        CoordinateMapPath =
            TEXT("physics/data/real_world/chilko_river_lava_canyon/terrain/"
                 "lava_canyon_visual/lava_canyon_runtime_coordinate_map.json");
        RunTag = FName(TEXT("RaftSimChilkoLavaCanyonRun"));
        PlayerRaftLabel = TEXT("RaftSim_ChilkoLavaCanyon_PlayerRaft");
        DisplayName = TEXT("Chilko Lava Canyon");
    }
    else if (bFutaleufuTerminator)
    {
        RuntimeConfigLabel = TEXT("RaftSim_FutaleufuTerminator_RuntimeWaterConfig");
        CookedFieldsDir =
            TEXT("physics/data/real_world/futaleufu_river_chile/"
                 "scenario_terminator/cooked_flow_fields");
        FlowBand = FName(TEXT("median_runnable"));
        WindowCenterM = FVector2D(300.0f, 0.0f);
        WindowExtentM = 700.0f;
        CoordinateMapPath =
            TEXT("physics/data/real_world/futaleufu_river_chile/terrain/"
                 "terminator_visual/terminator_runtime_coordinate_map.json");
        RunTag = FName(TEXT("RaftSimFutaleufuTerminatorRun"));
        PlayerRaftLabel = TEXT("RaftSim_FutaleufuTerminator_PlayerRaft");
        DisplayName = TEXT("Futaleufu Terminator");
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

    // Hance and Lava Canyon both have genuine cooked-field rapid structure
    // outside the generic station-24 m launch carrier. Hance starts at 56% of
    // its 600 m reach (station 336 m): all three committed release bands are
    // deep and subcritical there, and each has an accepted interior breaking
    // transition about 69 m downstream. Lava Canyon retains its independently
    // reviewed station-228 m approach. These values change scenario framing
    // only; cooked hydraulics, wet masks, collision, and raft forces are not
    // synthesized or modified.
    const float StartProgress = bColoradoHance
        ? 0.56f
        : (bChilkoLavaCanyon
               ? 0.38f
               : (bReachLocalRun ? 0.04f : 0.0025f));
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
    WaterConfig->bLiveSolverOwnsRuntimeRendering = bSolverOwnedRuntimeWater;
    if (bPacuare)
    {
        WaterConfig->bEnforceTaggedHeightFogPresentation = true;
        WaterConfig->RuntimeHeightFogActorTag =
            TEXT("RaftSimLayeredRainforestHumidity");
        WaterConfig->RuntimeHeightFogDensity = 0.0075f;
        WaterConfig->bRuntimeVolumetricFogEnabled = false;
        // A wet-cell-clipped transmitting core replaces the opaque rainforest
        // carrier as the river body. The low-coverage Default Lit surface is
        // retained only for solver geometry normals and a soft bank feather.
        WaterConfig->bEnableLiveSolverVolumeCore = true;
        WaterConfig->LiveVolumeCoreMaterialOverride =
            LoadOrCreatePacuareUpperHuacasLiveWaterInstance(OutSummary);
        WaterConfig->LiveWaterFlowNormalTexture = LoadObject<UTexture2D>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/PacuareRun/Water/Textures/"
                 "T_RaftSim_PacuareUpperHuacasWaterV1_FlowNormal."
                 "T_RaftSim_PacuareUpperHuacasWaterV1_FlowNormal"));
        WaterConfig->LiveWaterFoamLaceTexture = LoadObject<UTexture2D>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/PacuareRun/Water/Textures/"
                 "T_RaftSim_PacuareUpperHuacasWaterV1_FoamLace."
                 "T_RaftSim_PacuareUpperHuacasWaterV1_FoamLace"));
        if (!WaterConfig->LiveVolumeCoreMaterialOverride ||
            !WaterConfig->LiveWaterFlowNormalTexture ||
            !WaterConfig->LiveWaterFoamLaceTexture)
        {
            OutSummary += TEXT(
                "Pacuare Upper Huacas live-water assets are incomplete.\n");
            return false;
        }
        WaterConfig->LiveSurfaceCalmCoverage = 0.035f;
        WaterConfig->LiveSurfaceActiveCoverage = 0.14f;
        WaterConfig->LiveSurfaceSpecular = 0.30f;
        WaterConfig->LiveSurfaceRoughness = 0.33f;
        WaterConfig->LiveSkyReflectionStrength = 0.30f;
        WaterConfig->LiveRippleStrength = 0.30f;
        WaterConfig->LiveFoamIntensity = 0.62f;
        WaterConfig->bEnableLivePresentationSurfaceSmoothing = true;
        WaterConfig->LivePresentationSurfaceSmoothingStrength = 0.62f;
        WaterConfig->LivePresentationStandingWaveScale = 0.78f;
        WaterConfig->LivePresentationHydraulicReliefScale = 0.78f;
        WaterConfig->LiveRapidFoamFocusStart = 0.10f;
        WaterConfig->LiveRapidFoamFocusEnd = 0.66f;
        WaterConfig->LiveRapidFoamCoverageGain = 0.86f;
        WaterConfig->LiveSurfaceBankBlendMeters = 4.0f;
        WaterConfig->LiveShallowSurfaceColor =
            FLinearColor(0.035f, 0.130f, 0.095f, 1.0f);
        WaterConfig->LiveDeepSurfaceColor =
            FLinearColor(0.008f, 0.033f, 0.024f, 1.0f);
        WaterConfig->LiveReflectedSkyColor =
            FLinearColor(0.095f, 0.180f, 0.160f, 1.0f);
        WaterConfig->LiveWaterScattering =
            FLinearColor(0.00016f, 0.00024f, 0.00018f, 0.0f);
        WaterConfig->LiveWaterAbsorption =
            FLinearColor(0.0070f, 0.0035f, 0.0055f, 0.0f);
        WaterConfig->LiveRiverbedColorScale =
            FLinearColor(0.12f, 0.16f, 0.09f, 0.0f);
        WaterConfig->LiveShallowWaterOpacity = 0.46f;
        WaterConfig->LiveDeepWaterOpacity = 0.72f;
        WaterConfig->LiveFoamWaterOpacity = 0.88f;
        WaterConfig->Tags.AddUnique(TEXT("RaftSimPacuareTransmittingWaterV1"));
        WaterConfig->Tags.AddUnique(TEXT("RaftSimSolverMaskedFoamLace"));
        WaterConfig->Tags.AddUnique(TEXT("RaftSimNoSolverStateMutation"));
    }
    else if (bColoradoHance)
    {
        // A solver-clipped transmitting core supplies the sediment-bearing
        // river body. The existing Default Lit mesh becomes a low-coverage
        // hydraulic detail skin, retaining geometry normals and lace foam
        // without reading as an opaque stepped card.
        WaterConfig->bEnableLiveSolverVolumeCore = true;
        WaterConfig->LiveVolumeCoreMaterialOverride =
            LoadOrCreateColoradoHanceLiveWaterInstance(OutSummary);
        WaterConfig->LiveWaterFlowNormalTexture = LoadObject<UTexture2D>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ColoradoRun/Water/Textures/"
                 "T_RaftSim_ColoradoHanceWaterV1_FlowNormal."
                 "T_RaftSim_ColoradoHanceWaterV1_FlowNormal"));
        WaterConfig->LiveWaterFoamLaceTexture = LoadObject<UTexture2D>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ColoradoRun/Water/Textures/"
                 "T_RaftSim_ColoradoHanceWaterV1_FoamLace."
                 "T_RaftSim_ColoradoHanceWaterV1_FoamLace"));
        if (!WaterConfig->LiveVolumeCoreMaterialOverride ||
            !WaterConfig->LiveWaterFlowNormalTexture ||
            !WaterConfig->LiveWaterFoamLaceTexture)
        {
            OutSummary += TEXT(
                "Colorado Hance river-local live-water assets are incomplete.\n");
            return false;
        }
        WaterConfig->LiveSurfaceCalmCoverage = 0.035f;
        WaterConfig->LiveSurfaceActiveCoverage = 0.14f;
        WaterConfig->LiveSurfaceSpecular = 0.30f;
        WaterConfig->LiveSurfaceRoughness = 0.32f;
        WaterConfig->LiveSkyReflectionStrength = 0.26f;
        WaterConfig->LiveRippleStrength = 0.24f;
        WaterConfig->LiveFoamIntensity = 0.55f;
        WaterConfig->bEnableLivePresentationSurfaceSmoothing = true;
        WaterConfig->LivePresentationSurfaceSmoothingStrength = 0.72f;
        WaterConfig->LivePresentationStandingWaveScale = 0.55f;
        WaterConfig->LivePresentationHydraulicReliefScale = 0.55f;
        WaterConfig->LiveRapidFoamFocusStart = 0.30f;
        WaterConfig->LiveRapidFoamFocusEnd = 0.82f;
        WaterConfig->LiveRapidFoamCoverageGain = 0.82f;
        WaterConfig->LiveSurfaceBankBlendMeters = 4.5f;
        WaterConfig->LiveShallowSurfaceColor =
            FLinearColor(0.070f, 0.110f, 0.080f, 1.0f);
        WaterConfig->LiveDeepSurfaceColor =
            FLinearColor(0.018f, 0.038f, 0.028f, 1.0f);
        WaterConfig->LiveReflectedSkyColor =
            FLinearColor(0.12f, 0.17f, 0.18f, 1.0f);
    }
    else if (bChilkoLavaCanyon)
    {
        // The wet-cell-clipped core owns optical depth while a low-coverage
        // live skin preserves solver geometry and bank feather. River-local
        // textures add sub-grid detail only after solver wetness/aeration.
        WaterConfig->bEnableLiveSolverVolumeCore = true;
        WaterConfig->LiveVolumeCoreMaterialOverride =
            LoadOrCreateChilkoLavaCanyonLiveWaterInstance(OutSummary);
        WaterConfig->LiveWaterFlowNormalTexture = LoadObject<UTexture2D>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ChilkoRun/Water/Textures/"
                 "T_RaftSim_ChilkoLavaCanyonWaterV1_FlowNormal."
                 "T_RaftSim_ChilkoLavaCanyonWaterV1_FlowNormal"));
        WaterConfig->LiveWaterFoamLaceTexture = LoadObject<UTexture2D>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ChilkoRun/Water/Textures/"
                 "T_RaftSim_ChilkoLavaCanyonWaterV1_FoamLace."
                 "T_RaftSim_ChilkoLavaCanyonWaterV1_FoamLace"));
        if (!WaterConfig->LiveVolumeCoreMaterialOverride ||
            !WaterConfig->LiveWaterFlowNormalTexture ||
            !WaterConfig->LiveWaterFoamLaceTexture)
        {
            OutSummary += TEXT(
                "Chilko river-local live-water assets are incomplete.\n");
            return false;
        }
        WaterConfig->LiveSurfaceCalmCoverage = 0.035f;
        WaterConfig->LiveSurfaceActiveCoverage = 0.14f;
        // Preserve water's dielectric F0 while replacing the former polished
        // sheet response with a turbulent Lava Canyon roughness/ripple range.
        // The lower fallback sky term affects presentation only; it does not
        // alter solver wetness, geometry, sampling, buoyancy, or raft forces.
        WaterConfig->LiveSurfaceSpecular = 0.18f;
        WaterConfig->LiveSurfaceRoughness = 0.42f;
        WaterConfig->LiveSkyReflectionStrength = 0.05f;
        WaterConfig->LiveRippleStrength = 0.72f;
        WaterConfig->LiveFoamIntensity = 0.56f;
        WaterConfig->bEnableLivePresentationSurfaceSmoothing = true;
        WaterConfig->LivePresentationSurfaceSmoothingStrength = 0.58f;
        WaterConfig->LivePresentationStandingWaveScale = 0.78f;
        WaterConfig->LivePresentationHydraulicReliefScale = 0.78f;
        WaterConfig->LiveRapidFoamFocusStart = 0.12f;
        WaterConfig->LiveRapidFoamFocusEnd = 0.72f;
        WaterConfig->LiveRapidFoamCoverageGain = 0.90f;
        WaterConfig->LiveSurfaceBankBlendMeters = 4.5f;
        WaterConfig->bEnableLivePresentationBankNaturalism = true;
        WaterConfig->LivePresentationBankNaturalismAmplitudeMeters = 0.90f;
        WaterConfig->LiveShallowSurfaceColor =
            FLinearColor(0.012f, 0.075f, 0.105f, 1.0f);
        WaterConfig->LiveDeepSurfaceColor =
            FLinearColor(0.002f, 0.018f, 0.032f, 1.0f);
        WaterConfig->LiveReflectedSkyColor =
            FLinearColor(0.025f, 0.050f, 0.075f, 1.0f);
        WaterConfig->LiveWaterScattering =
            FLinearColor(0.00004f, 0.00009f, 0.00014f, 0.0f);
        WaterConfig->LiveWaterAbsorption =
            FLinearColor(0.0110f, 0.0065f, 0.0045f, 0.0f);
        WaterConfig->LiveRiverbedColorScale =
            FLinearColor(0.060f, 0.080f, 0.095f, 0.0f);
        WaterConfig->LiveShallowWaterOpacity = 0.36f;
        WaterConfig->LiveOpticalDepthResponseExponent = 0.25f;
        WaterConfig->LiveDeepWaterOpacity = 0.84f;
        WaterConfig->LiveFoamWaterOpacity = 0.86f;
        WaterConfig->bEnforceTaggedDirectionalLightPresentation = true;
        WaterConfig->RuntimeDirectionalLightActorTag =
            TEXT("RaftSimColdWaterHighlightNaturalismV1");
        WaterConfig->RuntimeDirectionalLightIntensity = 2.90f;
        WaterConfig->RuntimeDirectionalLightRotation =
            FRotator(-50.0f, 55.0f, 0.0f);
        WaterConfig->Tags.AddUnique(TEXT("RaftSimChilkoTransmittingWaterV2"));
        WaterConfig->Tags.AddUnique(
            TEXT("RaftSimChilkoLocalizedReflectionWaterV3"));
        WaterConfig->Tags.AddUnique(
            TEXT("RaftSimColdWaterHighlightNaturalismV1"));
        WaterConfig->Tags.AddUnique(
            TEXT("RaftSimColdWaterDepthAttenuationV2"));
        WaterConfig->Tags.AddUnique(
            TEXT("RaftSimColdWaterNonlinearOpticalDepthV1"));
        WaterConfig->Tags.AddUnique(TEXT("RaftSimSolverMaskedFoamLace"));
        WaterConfig->Tags.AddUnique(TEXT("RaftSimNoSolverStateMutation"));
    }
    else if (bFutaleufuTerminator)
    {
        // Terminator has the same reviewed cold-water sheet defect as Chilko
        // and five interior solver breaking sites. Its bank-clipped volume
        // core supplies optical depth while this low-coverage skin retains
        // geometric normals, rapid colour response, and the soft bank edge.
        WaterConfig->bEnableLiveSolverVolumeCore = true;
        WaterConfig->LiveVolumeCoreMaterialOverride =
            LoadOrCreateFutaleufuTerminatorLiveWaterInstance(OutSummary);
        WaterConfig->LiveWaterFlowNormalTexture = LoadObject<UTexture2D>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/FutaleufuRun/Water/Textures/"
                 "T_RaftSim_FutaleufuTerminatorWaterV1_FlowNormal."
                 "T_RaftSim_FutaleufuTerminatorWaterV1_FlowNormal"));
        WaterConfig->LiveWaterFoamLaceTexture = LoadObject<UTexture2D>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/FutaleufuRun/Water/Textures/"
                 "T_RaftSim_FutaleufuTerminatorWaterV1_FoamLace."
                 "T_RaftSim_FutaleufuTerminatorWaterV1_FoamLace"));
        if (!WaterConfig->LiveVolumeCoreMaterialOverride ||
            !WaterConfig->LiveWaterFlowNormalTexture ||
            !WaterConfig->LiveWaterFoamLaceTexture)
        {
            OutSummary += TEXT(
                "Futaleufu river-local live-water assets are incomplete.\n");
            return false;
        }
        WaterConfig->LiveSurfaceCalmCoverage = 0.035f;
        WaterConfig->LiveSurfaceActiveCoverage = 0.14f;
        // Match Terminator's direct-light and capture fallback energy to the
        // accepted turbulent cold-water bracket. This changes presentation
        // only; the cooked field still owns wetness, geometry and forces.
        WaterConfig->LiveSurfaceSpecular = 0.18f;
        WaterConfig->LiveSurfaceRoughness = 0.42f;
        WaterConfig->LiveSkyReflectionStrength = 0.05f;
        WaterConfig->LiveRippleStrength = 0.72f;
        WaterConfig->LiveFoamIntensity = 0.58f;
        WaterConfig->LiveRapidFoamFocusStart = 0.08f;
        WaterConfig->LiveRapidFoamFocusEnd = 0.58f;
        WaterConfig->LiveSurfaceBankBlendMeters = 4.5f;
        WaterConfig->bEnableLivePresentationBankNaturalism = true;
        WaterConfig->LivePresentationBankNaturalismAmplitudeMeters = 0.90f;
        WaterConfig->LiveShallowSurfaceColor =
            FLinearColor(0.008f, 0.055f, 0.130f, 1.0f);
        WaterConfig->LiveDeepSurfaceColor =
            FLinearColor(0.001f, 0.014f, 0.050f, 1.0f);
        WaterConfig->LiveReflectedSkyColor =
            FLinearColor(0.018f, 0.080f, 0.160f, 1.0f);
        // Preserve dark bed detail in shallows while using the solver depth
        // channel to absorb the broad, pale deep-water sheet. These values
        // affect only Single Layer Water transmission; cooked depth, wetness,
        // surface geometry, collision, and raft forces remain authoritative.
        WaterConfig->LiveWaterScattering =
            FLinearColor(0.000035f, 0.000070f, 0.000110f, 0.0f);
        WaterConfig->LiveWaterAbsorption =
            FLinearColor(0.0120f, 0.0080f, 0.0060f, 0.0f);
        WaterConfig->LiveRiverbedColorScale =
            FLinearColor(0.055f, 0.075f, 0.090f, 0.0f);
        WaterConfig->LiveShallowWaterOpacity = 0.36f;
        WaterConfig->LiveOpticalDepthResponseExponent = 0.25f;
        WaterConfig->LiveDeepWaterOpacity = 0.86f;
        WaterConfig->LiveFoamWaterOpacity = 0.88f;
        WaterConfig->bEnforceTaggedDirectionalLightPresentation = true;
        WaterConfig->RuntimeDirectionalLightActorTag =
            TEXT("RaftSimColdWaterHighlightNaturalismV1");
        WaterConfig->RuntimeDirectionalLightIntensity = 2.40f;
        WaterConfig->RuntimeDirectionalLightRotation =
            FRotator(-50.0f, 30.0f, 0.0f);
        WaterConfig->Tags.AddUnique(
            TEXT("RaftSimColdWaterHighlightNaturalismV1"));
        WaterConfig->Tags.AddUnique(
            TEXT("RaftSimColdWaterDepthAttenuationV2"));
        WaterConfig->Tags.AddUnique(
            TEXT("RaftSimColdWaterNonlinearOpticalDepthV1"));
        WaterConfig->Tags.AddUnique(TEXT("RaftSimNoSolverStateMutation"));
    }
    else if (bZambezi)
    {
        // A transmitting wet-cell core replaces the opaque physical-corridor
        // card during play. The cooked Zambezi field still owns geometry,
        // wet/dry, stationing, forces, and foam masks; these river-local assets
        // contribute only sediment-water optics and sub-grid surface breakup.
        WaterConfig->bEnableLiveSolverVolumeCore = true;
        WaterConfig->LiveVolumeCoreMaterialOverride =
            LoadOrCreateZambeziBatokaLiveWaterV2Instance(OutSummary);
        WaterConfig->LiveWaterFlowNormalTexture = LoadObject<UTexture2D>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ZambeziRun/Water/Textures/"
                 "T_RaftSim_ZambeziBatokaWaterV1_FlowNormal."
                 "T_RaftSim_ZambeziBatokaWaterV1_FlowNormal"));
        WaterConfig->LiveWaterFoamLaceTexture = LoadObject<UTexture2D>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ZambeziRun/Water/Textures/"
                 "T_RaftSim_ZambeziBatokaWaterV1_FoamLace."
                 "T_RaftSim_ZambeziBatokaWaterV1_FoamLace"));
        if (!WaterConfig->LiveVolumeCoreMaterialOverride ||
            !WaterConfig->LiveWaterFlowNormalTexture ||
            !WaterConfig->LiveWaterFoamLaceTexture)
        {
            OutSummary += TEXT(
                "Zambezi Batoka river-local live-water assets are incomplete.\n");
            return false;
        }
        WaterConfig->LiveSurfaceCalmCoverage = 0.0f;
        WaterConfig->LiveSurfaceActiveCoverage = 0.06f;
        WaterConfig->LiveSurfaceSpecular = 0.15f;
        WaterConfig->LiveSurfaceRoughness = 0.66f;
        WaterConfig->LiveSkyReflectionStrength = 0.055f;
        WaterConfig->LiveRippleStrength = 0.48f;
        WaterConfig->LiveFoamIntensity = 0.64f;
        WaterConfig->bEnableLivePresentationSurfaceSmoothing = true;
        WaterConfig->LivePresentationSurfaceSmoothingStrength = 0.62f;
        WaterConfig->LivePresentationStandingWaveScale = 0.82f;
        WaterConfig->LivePresentationHydraulicReliefScale = 0.82f;
        WaterConfig->LiveRapidFoamFocusStart = 0.10f;
        WaterConfig->LiveRapidFoamFocusEnd = 0.66f;
        WaterConfig->LiveRapidFoamCoverageGain = 0.92f;
        // The transmitting core now consumes the same smooth vertex-alpha
        // coverage as the detail skin. Three sampled cells provide a visible
        // 0-to-1 transition instead of terminating the optical body as a hard
        // rectangular polygon against either bank.
        WaterConfig->LiveSurfaceBankBlendMeters = 7.5f;
        WaterConfig->LiveShallowSurfaceColor =
            FLinearColor(0.058f, 0.095f, 0.050f, 1.0f);
        WaterConfig->LiveDeepSurfaceColor =
            FLinearColor(0.013f, 0.030f, 0.016f, 1.0f);
        WaterConfig->LiveReflectedSkyColor =
            FLinearColor(0.030f, 0.052f, 0.064f, 1.0f);
        WaterConfig->LiveWaterScattering =
            FLinearColor(0.00018f, 0.00015f, 0.00009f, 0.0f);
        WaterConfig->LiveWaterAbsorption =
            FLinearColor(0.0060f, 0.0038f, 0.0068f, 0.0f);
        WaterConfig->LiveRiverbedColorScale =
            FLinearColor(0.17f, 0.14f, 0.085f, 0.0f);
        WaterConfig->LiveShallowWaterOpacity = 0.42f;
        WaterConfig->LiveDeepWaterOpacity = 0.64f;
        WaterConfig->LiveFoamWaterOpacity = 0.84f;
        WaterConfig->Tags.AddUnique(TEXT("RaftSimZambeziTransmittingWaterV2"));
        WaterConfig->Tags.AddUnique(TEXT("RaftSimOpacityFeatheredVolumeEdgeV2"));
        WaterConfig->Tags.AddUnique(TEXT("RaftSimRestrainedSolarGlareV2"));
        WaterConfig->Tags.AddUnique(
            TEXT("RaftSimZambeziLocalizedReflectionWaterV18"));
        WaterConfig->Tags.AddUnique(TEXT("RaftSimSolverMaskedFoamLace"));
        WaterConfig->Tags.AddUnique(TEXT("RaftSimNoSolverStateMutation"));
    }
    // Shared rapid-water contract for every physical river: a half-metre
    // bounded carrier plus a 100 m raft-local GPU heightfield. Both deform the
    // solver-owned surface; neither adds another water sheet.
    WaterConfig->bEnableLiveRapidSurfaceRefinement = true;
    WaterConfig->LiveRapidSurfaceSubdivision = 6;
    WaterConfig->bEnableLiveRaftLocalFluidHeightfield = true;
    WaterConfig->LiveRaftLocalFluidWindowMeters = 100.0f;
    WaterConfig->LiveRaftLocalFluidHeightfieldStrength = 0.65f;
    WaterConfig->Tags.AddUnique(TEXT("RaftSimHalfMeterRapidCarrierV1"));
    WaterConfig->Tags.AddUnique(TEXT("RaftSimRaftLocalGpuFluidV2"));
    WaterConfig->Tags.AddUnique(RunTag);
    WaterConfig->Tags.AddUnique(TEXT("RaftSimProceduralRuntimeWater"));
    WaterConfig->Tags.AddUnique(TEXT("RaftSimGlobalRiverStationAuthority"));
    WaterConfig->Tags.AddUnique(TEXT("RaftSimSafeLaunchApron"));
    if (bColoradoHance)
    {
        WaterConfig->Tags.AddUnique(
            TEXT("RaftSimColoradoHanceRapidApproachLaunchV1"));
        WaterConfig->Tags.AddUnique(
            TEXT("RaftSimColoradoHanceSubcellSmoothedWaterV1"));
        WaterConfig->Tags.AddUnique(TEXT("RaftSimRenderOnlyHydraulicSmoothing"));
        WaterConfig->Tags.AddUnique(TEXT("RaftSimNoSolverStateMutation"));
        WaterConfig->Tags.AddUnique(TEXT("RaftSimColoradoHanceLaceFoamV1"));
    }
    if (bSolverOwnedRuntimeWater)
    {
        WaterConfig->Tags.AddUnique(
            TEXT("RaftSimLiveSolverWaterOwnsRuntimeRendering"));
    }

    // Author the launch at loaded hydrostatic equilibrium instead of dropping
    // the raft from above the surface. The reduced body saturates over one
    // tube diameter and provides 3.4x weight at full immersion, so the calm
    // tube-center waterline is 2R / 3.4 below the sampled surface. Starting at
    // +58 cm caused an underdamped first plunge, false deck-water retention,
    // and a capsize before the guide could issue a command.
    constexpr float LaunchTubeRadiusCm = 28.0f;
    constexpr float LaunchBuoyancyWeightMultiple = 3.4f;
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
    if (bColoradoHance)
    {
        Raft->Tags.AddUnique(
            TEXT("RaftSimColoradoHanceRapidApproachLaunchV1"));
    }
    else if (bChilkoLavaCanyon)
    {
        Raft->Tags.AddUnique(TEXT("RaftSimChilkoRapidApproachLaunchV1"));
    }

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

    if (bChilkoLavaCanyon)
    {
        // These four D4 contacts mirror three manifest-recorded broach rocks
        // plus the first fixed-seed boulder in the interpreted C3 bed. Their
        // placement is deliberately review-gated: it enables wrap/pin physics
        // without presenting the coarse feature-tag interpretation as survey.
        struct FInterpretedRockSpec
        {
            float StationM;
            float LateralM;
            float RadiusM;
            float CrestBelowSurfaceM;
            float Friction;
            const TCHAR* Label;
        };
        const FInterpretedRockSpec InterpretedRocks[] = {
            {250.0f, 3.5f, 2.4f, 1.1f, 0.76f, TEXT("BroachRockUpper")},
            {300.0f, -4.0f, 2.4f, 1.1f, 0.78f, TEXT("BroachRockCenter")},
            {392.0f, 2.0f, 2.4f, 1.1f, 0.74f, TEXT("BroachRockLower")},
            {405.8667f, 10.6160f, 1.9816f, 1.0270f, 0.72f, TEXT("SeededBoulder01")},
        };
        int32 SpawnedRockCount = 0;
        for (const FInterpretedRockSpec& RockSpec : InterpretedRocks)
        {
            const float Progress = RockSpec.StationM /
                FMath::Max(Points.Last().StationMeters, 1.0f);
            FVector2D Tangent2D(1.0f, 0.0f);
            FVector2D RockXY = SampleLandscapeCandidateCenterlineWorld(
                Candidate,
                Points,
                Progress,
                &Tangent2D);
            const FVector2D RiverLeftNormal(-Tangent2D.Y, Tangent2D.X);
            RockXY += RiverLeftNormal * RockSpec.LateralM * 100.0f;
            float RockSurfaceZ = 0.0f;
            if (!SampleLandscapeCandidateConditionedVisualSurfaceWorldZ(
                    Candidate,
                    Points,
                    Progress,
                    RockSurfaceZ))
            {
                OutSummary += TEXT("Could not align a Lava Canyon D4 rock to water.\n");
                return false;
            }
            const float RockCenterZ = RockSurfaceZ -
                (RockSpec.CrestBelowSurfaceM + RockSpec.RadiusM) * 100.0f;
            ARaftSimRockObstacleActor* Rock =
                World->SpawnActor<ARaftSimRockObstacleActor>(
                    ARaftSimRockObstacleActor::StaticClass(),
                    FTransform(FVector(RockXY.X, RockXY.Y, RockCenterZ)));
            if (!Rock)
            {
                OutSummary += TEXT("Could not spawn a Lava Canyon D4 rock.\n");
                return false;
            }
            Rock->ConfigureContact(RockSpec.RadiusM, RockSpec.Friction);
            Rock->SetActorLabel(FString::Printf(
                TEXT("RaftSim_ChilkoLavaCanyon_D4_%s"), RockSpec.Label));
            Rock->Tags.AddUnique(RunTag);
            Rock->Tags.AddUnique(TEXT("RaftSimInterpretedC3Obstacle"));
            Rock->Tags.AddUnique(TEXT("RaftSimReviewGatedGeometry"));
            ++SpawnedRockCount;
        }
        if (SpawnedRockCount != UE_ARRAY_COUNT(InterpretedRocks))
        {
            return false;
        }
        OutSummary += TEXT(
            "Added four review-gated D4 contacts from Lava Canyon interpreted "
            "broach-rock and fixed-seed boulder geometry.\n");
    }
    else if (bFutaleufuTerminator)
    {
        // The entry marker boulder is the only discrete rock in the authored
        // C3 bed. It is an interpretation of published feature tags rather
        // than surveyed geometry, so keep the runtime contact review-gated.
        constexpr float StationM = 266.0f;
        constexpr float LateralM = -8.0f;
        constexpr float RadiusM = 3.2f;
        constexpr float CrestAboveSurfaceM = 0.7f;
        const float Progress = StationM /
            FMath::Max(Points.Last().StationMeters, 1.0f);
        FVector2D Tangent2D(1.0f, 0.0f);
        FVector2D RockXY = SampleLandscapeCandidateCenterlineWorld(
            Candidate,
            Points,
            Progress,
            &Tangent2D);
        const FVector2D RiverLeftNormal(-Tangent2D.Y, Tangent2D.X);
        RockXY += RiverLeftNormal * LateralM * 100.0f;
        float RockSurfaceZ = 0.0f;
        if (!SampleLandscapeCandidateConditionedVisualSurfaceWorldZ(
                Candidate,
                Points,
                Progress,
                RockSurfaceZ))
        {
            OutSummary += TEXT("Could not align the Terminator marker boulder to water.\n");
            return false;
        }
        const float RockCenterZ = RockSurfaceZ -
            (RadiusM - CrestAboveSurfaceM) * 100.0f;
        ARaftSimRockObstacleActor* Rock =
            World->SpawnActor<ARaftSimRockObstacleActor>(
                ARaftSimRockObstacleActor::StaticClass(),
                FTransform(FVector(RockXY.X, RockXY.Y, RockCenterZ)));
        if (!Rock)
        {
            OutSummary += TEXT("Could not spawn the Terminator marker boulder.\n");
            return false;
        }
        Rock->ConfigureContact(RadiusM, 0.76f);
        Rock->SetActorLabel(TEXT("RaftSim_FutaleufuTerminator_D4_EntryMarkerBoulder"));
        Rock->Tags.AddUnique(RunTag);
        Rock->Tags.AddUnique(TEXT("RaftSimInterpretedC3Obstacle"));
        Rock->Tags.AddUnique(TEXT("RaftSimReviewGatedGeometry"));
        OutSummary += TEXT(
            "Added one review-gated D4 contact from Terminator's interpreted "
            "entry-marker-boulder geometry.\n");
    }

    if (bSolverOwnedRuntimeWater)
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
        SetCamera(TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"), 0.143333f, 0.243333f, 330.0f, 170.0f);
        SetCamera(TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"), 0.178333f, 0.278333f, 270.0f, 160.0f);
    }
    else if (Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon"))
    {
        SetCamera(TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"), 0.383f, 0.483f, 330.0f, 170.0f);
        SetCamera(TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"), 0.418f, 0.518f, 270.0f, 160.0f);
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
        const bool bChilko =
            Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon");
        const bool bFutaleufu =
            Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator");
        SetCamera(
            TEXT("RaftSim_SolverRapid_RiverEyeCaptureCamera"),
            bChilko ? 0.438f : (bFutaleufu ? 0.198333f : 0.530f),
            bChilko ? 0.538f : (bFutaleufu ? 0.298333f : 0.645f),
            bChilko ? 270.0f : 275.0f,
            bChilko ? 160.0f : 165.0f);
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
