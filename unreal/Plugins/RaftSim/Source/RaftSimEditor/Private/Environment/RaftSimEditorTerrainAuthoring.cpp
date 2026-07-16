#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
void AddPreviewTerrainMesh(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* AerialDrape,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask,
    const FRaftSimPreviewImage* MaterialAtlasAlbedo,
    const FRaftSimPreviewImage* MaterialAtlasNormal,
    const FRaftSimPreviewImage* MaterialAtlasPacked)
{
    constexpr int32 XSteps = 560;
    constexpr int32 YSteps = 224;
    const float MinX = -5800.0f;
    const float MaxX = 26500.0f;
    const float HalfWidth = Spec.bDesertCanyon ? 4300.0f : 2750.0f;

    TArray<FVector> Vertices;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve((XSteps + 1) * (YSteps + 1));
    Normals.Reserve((XSteps + 1) * (YSteps + 1));
    UVs.Reserve((XSteps + 1) * (YSteps + 1));
    VertexColors.Reserve((XSteps + 1) * (YSteps + 1));
    Triangles.Reserve(XSteps * YSteps * 6);

    for (int32 XIndex = 0; XIndex <= XSteps; ++XIndex)
    {
        const float U = static_cast<float>(XIndex) / static_cast<float>(XSteps);
        const float X = FMath::Lerp(MinX, MaxX, U);
        for (int32 YIndex = 0; YIndex <= YSteps; ++YIndex)
        {
            const float V = static_cast<float>(YIndex) / static_cast<float>(YSteps);
            const float Y = FMath::Lerp(-HalfWidth, HalfWidth, V);
            const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
            const float CenterY = GetPreviewRiverCenterY(Spec, X);
            const float Offset = FMath::Abs(Y - CenterY);
            const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
            const float BankT = SmoothPreviewStep(ActiveRiverHalfWidth, ActiveRiverHalfWidth + Spec.BankWidthCm, Offset);
            const float CanyonT = SmoothPreviewStep(
                ActiveRiverHalfWidth + Spec.BankWidthCm,
                ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 1400.0f : 820.0f),
                Offset);
            const float WetT = 1.0f -
                SmoothPreviewStep(ActiveRiverHalfWidth + 35.0f, ActiveRiverHalfWidth + 360.0f * Spec.FlowWetBankScale, Offset);
            const float SourceWaterT = WaterMask && WaterMask->IsValid() ? WaterMask->SampleLuma(U, V) : 0.0f;
            const float SourceVegetationT = VegetationMask && VegetationMask->IsValid() ? VegetationMask->SampleLuma(U, V) : 0.0f;
            const float ColorNoise = 0.88f + 0.10f * FMath::Sin(X * 0.0031f + Y * 0.0047f) +
                0.06f * FMath::Sin(X * 0.0013f - Y * 0.0029f);
            const FLinearColor ShoulderColor = Spec.bDesertCanyon
                ? FLinearColor(0.62f, 0.40f, 0.24f)
                : ScalePreviewColor(Spec.TerrainColor, Spec.bHasWaterfalls ? 0.72f : 1.12f);
            const FLinearColor WetBankColor = Spec.bDesertCanyon
                ? FLinearColor(0.30f, 0.23f, 0.16f)
                : FMath::Lerp(ScalePreviewColor(Spec.WaterColor, 0.55f), ScalePreviewColor(Spec.RockColor, 0.62f), 0.48f);
            const FLinearColor SourceVegetationColor = Spec.bDesertCanyon
                ? FLinearColor(0.30f, 0.31f, 0.17f)
                : ScalePreviewColor(Spec.FoliageColor, Spec.bHasWaterfalls ? 1.18f : 1.05f);
            const FLinearColor BaseTerrainMaterialGrainShadow = Spec.bDesertCanyon
                ? FLinearColor(0.24f, 0.17f, 0.11f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.030f, 0.070f, 0.040f) : FLinearColor(0.16f, 0.15f, 0.10f));
            const FLinearColor BaseTerrainMaterialGrainHighlight = Spec.bDesertCanyon
                ? FLinearColor(0.56f, 0.40f, 0.25f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.075f, 0.160f, 0.070f) : FLinearColor(0.30f, 0.28f, 0.18f));
            const float BaseTerrainSourceAwareMaterialGrainT = FMath::Clamp(
                0.44f + 0.20f * FMath::Sin(X * 0.014f + Y * 0.010f) +
                    0.18f * FMath::Sin(X * 0.031f - Y * 0.018f) +
                    0.10f * FMath::Sin(X * 0.007f + Y * 0.027f + SourceVegetationT * 2.7f),
                0.0f,
                1.0f);
            const float BaseTerrainMaterialBreakupT = FMath::Clamp(
                0.24f + BankT * 0.34f + CanyonT * 0.42f + SourceVegetationT * 0.18f + (1.0f - WetT) * 0.10f,
                0.0f,
                1.0f);
            const float BaseTerrainMicroReliefCm =
                (BaseTerrainSourceAwareMaterialGrainT - 0.5f) *
                (Spec.bDesertCanyon ? 16.0f : (Spec.bHasWaterfalls ? 12.0f : 10.0f)) *
                BaseTerrainMaterialBreakupT *
                SmoothPreviewStep(ActiveRiverHalfWidth + 80.0f, ActiveRiverHalfWidth + Spec.BankWidthCm + 880.0f, Offset);
            const float SourceAwareTerrainPhotoMottleReliefT = FMath::Clamp(
                BankT * 0.48f + CanyonT * 0.54f + SourceVegetationT * (Spec.bDesertCanyon ? 0.04f : 0.18f),
                0.0f,
                1.0f);
            const float SourceAwareTerrainPhotoMottleReliefCm =
                (0.42f * FMath::Sin(X * 0.012f + Y * 0.015f) +
                 0.26f * FMath::Sin(X * 0.027f - Y * 0.021f)) *
                (Spec.bDesertCanyon ? 12.0f : (Spec.bHasWaterfalls ? 8.0f : 9.0f)) *
                SourceAwareTerrainPhotoMottleReliefT;
            const float SourceConditionedFarBankMicroReliefT =
                SmoothPreviewStep(
                    ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 740.0f : 560.0f),
                    ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 1280.0f : 780.0f),
                    Offset) *
                (1.0f - FMath::Clamp(SourceWaterT * 0.72f + WetT * 0.22f, 0.0f, 1.0f));
            const float SourceConditionedFarBankMicroReliefCm =
                (0.36f * FMath::Sin(X * 0.009f + Y * 0.007f) +
                 0.22f * FMath::Sin(X * 0.019f - Y * 0.014f)) *
                (Spec.bDesertCanyon ? 9.0f : (Spec.bHasWaterfalls ? 6.0f : 7.0f)) *
                SourceConditionedFarBankMicroReliefT;
            const float BroadSlopeTerrainExposureFillT = FMath::Clamp(
                SmoothPreviewStep(
                    ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 560.0f : 420.0f),
                    ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 1800.0f : 1040.0f),
                    Offset) *
                    SmoothPreviewStep(
                        ActiveRiverHalfWidth + 260.0f * FMath::Max(0.35f, Spec.FlowWetBankScale),
                        ActiveRiverHalfWidth + 920.0f * FMath::Max(0.35f, Spec.FlowWetBankScale),
                        Offset) *
                    (0.46f + BankT * 0.20f + CanyonT * 0.32f +
                     SourceVegetationT * (Spec.bDesertCanyon ? 0.04f : 0.12f)) *
                    (1.0f - FMath::Clamp(SourceWaterT * 0.78f + WetT * 0.30f, 0.0f, 0.86f)),
                0.0f,
                1.0f);
            const float BroadSlopeTerrainLowFrequencyReliefCm =
                (0.44f * FMath::Sin(X * 0.0032f + Y * 0.0020f) +
                 0.26f * FMath::Sin(X * 0.0068f - Y * 0.0036f)) *
                (Spec.bDesertCanyon ? 18.0f : (Spec.bHasWaterfalls ? 11.0f : 12.0f)) *
                BroadSlopeTerrainExposureFillT;
            const float SourceAwareMacroTerrainRidgeFacetT = FMath::Clamp(
                SmoothPreviewStep(
                    ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 520.0f : 380.0f),
                    ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 2100.0f : 1180.0f),
                    Offset) *
                    (0.34f + BankT * 0.22f + CanyonT * 0.42f +
                     SourceVegetationT * (Spec.bDesertCanyon ? 0.02f : 0.10f)) *
                    (1.0f - FMath::Clamp(SourceWaterT * 0.86f + WetT * 0.38f, 0.0f, 0.92f)),
                0.0f,
                1.0f);
            const float SourceAwareMacroTerrainRidgeNoise = FMath::Clamp(
                0.50f +
                    0.30f * FMath::Sin(X * 0.0017f + Y * (Spec.bDesertCanyon ? 0.0028f : 0.0036f)) +
                    0.20f * FMath::Sin(X * 0.0046f - Y * (Spec.bDesertCanyon ? 0.0019f : 0.0027f)) +
                    0.12f * FMath::Sin(X * 0.0092f + Y * 0.0061f + SourceVegetationT * 2.1f),
                0.0f,
                1.0f);
            const float SourceAwareMacroTerrainRidgeReliefCm =
                (SourceAwareMacroTerrainRidgeNoise - 0.5f) *
                (Spec.bDesertCanyon ? 46.0f : (Spec.bHasWaterfalls ? 32.0f : 34.0f)) *
                SourceAwareMacroTerrainRidgeFacetT;
            const float SourceAwareTerrainSlopeFacetTextureT = FMath::Clamp(
                SmoothPreviewStep(
                    ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 420.0f : 300.0f),
                    ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 2300.0f : 1380.0f),
                    Offset) *
                    (0.34f + BankT * 0.24f + CanyonT * 0.40f +
                     SourceVegetationT * (Spec.bDesertCanyon ? 0.04f : 0.18f)) *
                    (1.0f - FMath::Clamp(SourceWaterT * 0.82f + WetT * 0.28f, 0.0f, 0.90f)),
                0.0f,
                1.0f);
            const float SourceAwareTerrainSlopeFacetNoise = FMath::Clamp(
                0.50f +
                    0.31f * FMath::Sin(X * 0.0024f + Y * (Spec.bDesertCanyon ? 0.0033f : 0.0041f)) +
                    0.19f * FMath::Sin(X * 0.0060f - Y * (Spec.bDesertCanyon ? 0.0021f : 0.0037f)) +
                    0.10f * FMath::Sin((X + Y) * 0.011f + SourceVegetationT * 3.2f),
                0.0f,
                1.0f);
            const float SourceAwareTerrainSlopeFacetReliefCm =
                (SourceAwareTerrainSlopeFacetNoise - 0.5f) *
                (Spec.bDesertCanyon ? 38.0f : (Spec.bHasWaterfalls ? 24.0f : 26.0f)) *
                SourceAwareTerrainSlopeFacetTextureT;
            const float SourceAwareRiparianCanopyMassTextureT = FMath::Clamp(
                SmoothPreviewStep(
                    ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 520.0f : 260.0f),
                    ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 2100.0f : 1280.0f),
                    Offset) *
                    (Spec.bDesertCanyon
                         ? (0.12f + BankT * 0.20f + SourceVegetationT * 0.26f)
                         : (Spec.bHasWaterfalls
                                ? (0.18f + BankT * 0.28f + CanyonT * 0.24f + SourceVegetationT * 0.62f)
                                : (0.16f + BankT * 0.30f + CanyonT * 0.12f + SourceVegetationT * 0.48f))) *
                    (1.0f - FMath::Clamp(SourceWaterT * 0.88f + WetT * 0.42f, 0.0f, 0.92f)),
                0.0f,
                1.0f);
            const float SourceAwareRiparianCanopyMassNoise = FMath::Clamp(
                0.50f +
                    0.28f * FMath::Sin(X * 0.0032f + Y * (Spec.bDesertCanyon ? 0.0021f : 0.0065f)) +
                    0.18f * FMath::Sin(X * 0.0090f - Y * (Spec.bDesertCanyon ? 0.0035f : 0.0054f)) +
                    0.12f * FMath::Sin((X - Y) * 0.0140f + SourceVegetationT * 2.7f),
                0.0f,
                1.0f);
            const float SourceAwareRiparianCanopyMassReliefCm =
                (SourceAwareRiparianCanopyMassNoise - 0.5f) *
                (Spec.bDesertCanyon ? 8.0f : (Spec.bHasWaterfalls ? 20.0f : 14.0f)) *
                SourceAwareRiparianCanopyMassTextureT;
            FLinearColor TerrainColor = FMath::Lerp(Spec.TerrainColor, ShoulderColor, FMath::Clamp(BankT * 0.45f + CanyonT * 0.35f, 0.0f, 1.0f));
            FLinearColor SourceDrapeColorForTerrain = TerrainColor;
            bool bHasSourceDrapeColorForTerrain = false;
            if (AerialDrape && AerialDrape->IsValid())
            {
                FLinearColor SourceDrapeColor = NormalizePreviewSourceDrapeAlbedo(
                    Spec,
                    AerialDrape->Sample(U, V),
                    SourceWaterT,
                    SourceVegetationT,
                    Spec.bHasWaterfalls ? 0.42f : (Spec.bDesertCanyon ? 0.36f : 0.34f));
                SourceDrapeColorForTerrain = SourceDrapeColor;
                bHasSourceDrapeColorForTerrain = true;
                const float SourceBlend = FMath::Clamp(
                    (Spec.bDesertCanyon ? 0.34f : (Spec.bHasWaterfalls ? 0.30f : 0.32f)) *
                        (0.36f + BankT * 0.30f + CanyonT * 0.24f + SourceVegetationT * 0.14f -
                         SourceWaterT * 0.12f),
                    0.0f,
                    Spec.bDesertCanyon ? 0.34f : (Spec.bHasWaterfalls ? 0.30f : 0.32f));
                TerrainColor = FMath::Lerp(TerrainColor, SourceDrapeColor, SourceBlend);
            }
            TerrainColor = FMath::Lerp(
                TerrainColor,
                SourceVegetationColor,
                FMath::Clamp(SourceVegetationT * (Spec.bDesertCanyon ? 0.20f : 0.38f), 0.0f, 0.42f));
            TerrainColor = FMath::Lerp(
                TerrainColor,
                WetBankColor,
                FMath::Clamp(FMath::Max(WetT * 0.70f, SourceWaterT * 0.48f), 0.0f, 0.78f));
            TerrainColor = FMath::Lerp(
                TerrainColor,
                BaseTerrainMaterialGrainShadow,
                FMath::Clamp((1.0f - BaseTerrainSourceAwareMaterialGrainT) * BaseTerrainMaterialBreakupT * 0.11f, 0.0f, 0.12f));
            TerrainColor = FMath::Lerp(
                TerrainColor,
                BaseTerrainMaterialGrainHighlight,
                FMath::Clamp(BaseTerrainSourceAwareMaterialGrainT * BaseTerrainMaterialBreakupT * 0.14f, 0.0f, 0.15f));
            TerrainColor = ScalePreviewColor(TerrainColor, ColorNoise);
            TerrainColor = ApplyPreviewSourceAwareTerrainPhotoMottle(
                Spec,
                TerrainColor,
                X,
                Y,
                BankT,
                CanyonT,
                WetT,
                SourceWaterT,
                SourceVegetationT);
            TerrainColor = ApplyPreviewSourceConditionedFarBankAlbedoCalibration(
                Spec,
                TerrainColor,
                SourceDrapeColorForTerrain,
                bHasSourceDrapeColorForTerrain,
                X,
                Y,
                BankT,
                CanyonT,
                WetT,
                SourceWaterT,
                SourceVegetationT,
                Offset,
                ActiveRiverHalfWidth);
            TerrainColor = ApplyPreviewBroadSlopeTerrainExposureFill(
                Spec,
                TerrainColor,
                SourceDrapeColorForTerrain,
                bHasSourceDrapeColorForTerrain,
                X,
                Y,
                BankT,
                CanyonT,
                WetT,
                SourceWaterT,
                SourceVegetationT,
                Offset,
                ActiveRiverHalfWidth);
            TerrainColor = ApplyPreviewSourceAwareTerrainSlopeFacetTexture(
                Spec,
                TerrainColor,
                X,
                Y,
                BankT,
                CanyonT,
                WetT,
                SourceWaterT,
                SourceVegetationT,
                Offset,
                ActiveRiverHalfWidth);
            TerrainColor = ApplyPreviewSourceAwareRiparianCanopyMassTexture(
                Spec,
                TerrainColor,
                X,
                Y,
                BankT,
                CanyonT,
                WetT,
                SourceWaterT,
                SourceVegetationT,
                Offset,
                ActiveRiverHalfWidth);
            const FLinearColor MacroTerrainRidgeShadowColor = Spec.bDesertCanyon
                ? FLinearColor(0.28f, 0.18f, 0.105f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.024f, 0.070f, 0.036f) : FLinearColor(0.145f, 0.135f, 0.090f));
            const FLinearColor MacroTerrainRidgeHighlightColor = Spec.bDesertCanyon
                ? FLinearColor(0.58f, 0.38f, 0.22f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.080f, 0.170f, 0.075f) : FLinearColor(0.315f, 0.290f, 0.180f));
            const float MacroTerrainRidgeShadowT =
                SmoothPreviewStep(0.08f, 0.42f, 1.0f - SourceAwareMacroTerrainRidgeNoise) *
                SourceAwareMacroTerrainRidgeFacetT;
            const float MacroTerrainRidgeHighlightT =
                SmoothPreviewStep(0.58f, 0.92f, SourceAwareMacroTerrainRidgeNoise) *
                SourceAwareMacroTerrainRidgeFacetT;
            TerrainColor = FMath::Lerp(
                TerrainColor,
                MacroTerrainRidgeShadowColor,
                FMath::Clamp(MacroTerrainRidgeShadowT * (Spec.bDesertCanyon ? 0.18f : 0.14f), 0.0f, Spec.bDesertCanyon ? 0.18f : 0.14f));
            TerrainColor = FMath::Lerp(
                TerrainColor,
                MacroTerrainRidgeHighlightColor,
                FMath::Clamp(MacroTerrainRidgeHighlightT * (Spec.bDesertCanyon ? 0.16f : 0.12f), 0.0f, Spec.bDesertCanyon ? 0.16f : 0.12f));
            if (Spec.bDesertCanyon)
            {
                const float CanyonStrataNoise = FMath::Clamp(
                    0.50f +
                        0.31f * FMath::Sin(X * 0.0045f + Y * 0.0062f) +
                        0.25f * FMath::Sin(X * 0.0160f - Y * 0.0105f) +
                        0.18f * FMath::Sin((TerrainZ + CanyonT * 180.0f) * 0.018f),
                    0.0f,
                    1.0f);
                const float CanyonStrataBandSeed = FMath::Frac(
                    FMath::Sin(FMath::Floor((TerrainZ + Y * 0.055f + X * 0.018f) * 0.012f) * 57.173f) *
                    43758.5453f);
                const FLinearColor CanyonRust = FLinearColor(0.675f, 0.335f, 0.165f);
                const FLinearColor CanyonLimestone = FLinearColor(0.790f, 0.660f, 0.430f);
                const FLinearColor CanyonVarnish = FLinearColor(0.245f, 0.145f, 0.095f);
                const FLinearColor CanyonSageWash = FLinearColor(0.395f, 0.405f, 0.285f);
                const FLinearColor CanyonStrataColor = CanyonStrataBandSeed < 0.24f
                    ? CanyonRust
                    : (CanyonStrataBandSeed < 0.52f
                           ? CanyonLimestone
                           : (CanyonStrataBandSeed < 0.76f ? CanyonVarnish : CanyonSageWash));
                TerrainColor = FMath::Lerp(
                    TerrainColor,
                    CanyonStrataColor,
                    FMath::Clamp(
                        (0.10f + CanyonT * 0.24f + BankT * 0.06f) *
                            (0.62f + CanyonStrataNoise * 0.38f),
                        0.0f,
                        0.52f));
            }
            const float FirstPartyMaterialAtlasTerrainBlend = FMath::Clamp(
                0.055f + BankT * 0.048f + CanyonT * 0.044f +
                    SourceVegetationT * (Spec.bDesertCanyon ? 0.010f : 0.026f) -
                    SourceWaterT * 0.030f - WetT * 0.016f,
                0.0f,
                Spec.bDesertCanyon ? 0.135f : 0.125f);
            TerrainColor = ApplyFirstPartyMaterialAtlasTint(
                Spec,
                MaterialAtlasAlbedo,
                TerrainBankLayeredMaterialTile,
                TerrainColor,
                U * (Spec.bDesertCanyon ? 8.0f : 9.5f) + SourceVegetationT * 0.37f,
                V * (Spec.bDesertCanyon ? 3.5f : 4.8f) + BankT * 0.23f + CanyonT * 0.41f,
                FirstPartyMaterialAtlasTerrainBlend);
            TerrainColor = ApplyFirstPartyMaterialAtlasSurfaceResponse(
                Spec,
                MaterialAtlasNormal,
                MaterialAtlasPacked,
                TerrainBankLayeredMaterialTile,
                TerrainColor,
                U * (Spec.bDesertCanyon ? 8.0f : 9.5f) + SourceVegetationT * 0.37f,
                V * (Spec.bDesertCanyon ? 3.5f : 4.8f) + BankT * 0.23f + CanyonT * 0.41f,
                FirstPartyMaterialAtlasTerrainBlend);
            const float IntegratedTerrainCorridorTextureCell = FMath::Frac(
                FMath::Sin(static_cast<float>((XIndex + 401) * 997 + (YIndex + 211) * 1297) * 12.9898f) *
                43758.5453f);
            TerrainColor = ApplyPreviewIntegratedTerrainCorridorTexture(
                Spec,
                TerrainColor,
                X,
                Y,
                BankT,
                CanyonT,
                WetT,
                SourceWaterT,
                SourceVegetationT,
                Offset,
                ActiveRiverHalfWidth,
                IntegratedTerrainCorridorTextureCell);
            const float FirstPartyMaterialAtlasTerrainReliefCm = GetFirstPartyMaterialAtlasMicroReliefCm(
                MaterialAtlasPacked,
                TerrainBankLayeredMaterialTile,
                U * (Spec.bDesertCanyon ? 8.0f : 9.5f) + SourceVegetationT * 0.37f,
                V * (Spec.bDesertCanyon ? 3.5f : 4.8f) + BankT * 0.23f + CanyonT * 0.41f,
                Spec.bDesertCanyon ? 18.0f : (Spec.bHasWaterfalls ? 14.0f : 12.0f),
                FirstPartyMaterialAtlasTerrainBlend);
            const float FirstPartySourceAwareTerrainGranularityCell = FMath::Frac(
                FMath::Sin(static_cast<float>((XIndex + 719) * 1777 + (YIndex + 353) * 2131) * 12.9898f) *
                43758.5453f);
            const float FirstPartyTerrainSurfaceGranularityT = FMath::Clamp(
                SmoothPreviewStep(
                    ActiveRiverHalfWidth + 95.0f,
                    ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 2600.0f : 1560.0f),
                    Offset) *
                    (0.38f + BankT * 0.28f + CanyonT * 0.34f +
                     SourceVegetationT * (Spec.bDesertCanyon ? 0.10f : 0.34f)) *
                    (1.0f - FMath::Clamp(SourceWaterT * 0.78f + WetT * 0.22f, 0.0f, 0.86f)),
                0.0f,
                1.0f);
            const float FirstPartyTerrainSurfaceGranularityNoise = FMath::Clamp(
                0.50f +
                    0.24f * FMath::Sin(X * 0.031f + Y * (Spec.bDesertCanyon ? 0.019f : 0.028f) +
                                        FirstPartySourceAwareTerrainGranularityCell * 2.7f) +
                    0.22f * FMath::Sin(X * 0.071f - Y * (Spec.bDesertCanyon ? 0.040f : 0.052f) +
                                        SourceVegetationT * 4.3f) +
                    0.16f * FMath::Sin((X - Y) * 0.113f + FirstPartySourceAwareTerrainGranularityCell * 5.1f),
                0.0f,
                1.0f);
            const float FirstPartyTerrainSurfaceGranularityReliefCm =
                (FirstPartyTerrainSurfaceGranularityNoise - 0.5f) *
                (Spec.bDesertCanyon ? 28.0f : (Spec.bHasWaterfalls ? 19.0f : 21.0f)) *
                FirstPartyTerrainSurfaceGranularityT;
            TerrainColor = ApplyPreviewSourceAwareTerrainSurfaceGranularity(
                Spec,
                TerrainColor,
                X,
                Y,
                BankT,
                CanyonT,
                WetT,
                SourceWaterT,
                SourceVegetationT,
                Offset,
                ActiveRiverHalfWidth,
                FirstPartySourceAwareTerrainGranularityCell);
            float FirstPartyRainforestRiverEyeSlopeReliefCm = 0.0f;
            if (Spec.bHasWaterfalls)
            {
                const float FirstPartyRainforestRiverEyeSlopeTextureT = FMath::Clamp(
                    SmoothPreviewStep(
                        ActiveRiverHalfWidth + 120.0f,
                        ActiveRiverHalfWidth + Spec.BankWidthCm + 1740.0f,
                        Offset) *
                        (0.42f + BankT * 0.28f + CanyonT * 0.30f + SourceVegetationT * 0.28f) *
                        (1.0f - FMath::Clamp(SourceWaterT * 0.82f + WetT * 0.24f, 0.0f, 0.88f)),
                    0.0f,
                    1.0f);
                if (FirstPartyRainforestRiverEyeSlopeTextureT > KINDA_SMALL_NUMBER)
                {
                    const float FirstPartyRainforestRiverEyeSlopeTextureCell = FMath::Frac(
                        FMath::Sin(static_cast<float>((XIndex + 947) * 2381 + (YIndex + 467) * 3253) * 12.9898f) *
                        43758.5453f);
                    const float FirstPartyRainforestRiverEyeSlopeTextureNoise = FMath::Clamp(
                        0.50f +
                            0.32f * FMath::Sin(X * 0.026f + Y * 0.037f + SourceVegetationT * 3.7f) +
                            0.24f * FMath::Sin(X * 0.061f - Y * 0.049f + BankT * 1.9f) +
                            0.16f * FMath::Sin((X + Y) * 0.118f + FirstPartyRainforestRiverEyeSlopeTextureCell * 5.1f),
                        0.0f,
                        1.0f);
                    const float FirstPartyRainforestRiverEyeSlopeRootVeinNoise = FMath::Clamp(
                        0.50f +
                            0.36f * FMath::Sin(X * 0.0068f + Y * 0.017f + CanyonT * 2.4f) +
                            0.22f * FMath::Sin(X * 0.019f - Y * 0.025f),
                        0.0f,
                        1.0f);
                    const float FirstPartyRainforestRiverEyeSlopeTextureMix = FMath::Clamp(
                        FirstPartyRainforestRiverEyeSlopeTextureNoise * 0.72f +
                            FirstPartyRainforestRiverEyeSlopeTextureCell * 0.28f,
                        0.0f,
                        1.0f);
                    const FLinearColor RainforestSlopeShadow = FLinearColor(0.016f, 0.070f, 0.030f);
                    const FLinearColor RainforestSlopeMoss = FLinearColor(0.060f, 0.185f, 0.065f);
                    const FLinearColor RainforestSlopeLeafLitter = FLinearColor(0.130f, 0.245f, 0.082f);
                    const FLinearColor RainforestSlopeWetClay = FLinearColor(0.105f, 0.155f, 0.064f);
                    const FLinearColor RainforestRiverEyeSlopeTextureColor =
                        FirstPartyRainforestRiverEyeSlopeTextureMix < 0.24f
                            ? RainforestSlopeShadow
                            : (FirstPartyRainforestRiverEyeSlopeTextureMix < 0.52f
                                   ? RainforestSlopeMoss
                                   : (FirstPartyRainforestRiverEyeSlopeTextureMix < 0.78f
                                          ? RainforestSlopeLeafLitter
                                          : RainforestSlopeWetClay));
                    TerrainColor = FMath::Lerp(
                        TerrainColor,
                        RainforestRiverEyeSlopeTextureColor,
                        FMath::Clamp(
                            FirstPartyRainforestRiverEyeSlopeTextureT *
                                (0.18f + FMath::Abs(FirstPartyRainforestRiverEyeSlopeTextureMix - 0.5f) * 0.42f +
                                 SourceVegetationT * 0.14f),
                            0.0f,
                            0.38f));
                    TerrainColor = ScalePreviewColor(
                        TerrainColor,
                        FMath::Clamp(
                            0.82f + FirstPartyRainforestRiverEyeSlopeTextureMix * 0.42f +
                                FirstPartyRainforestRiverEyeSlopeTextureCell * 0.16f -
                                SmoothPreviewStep(0.05f, 0.36f, 1.0f - FirstPartyRainforestRiverEyeSlopeRootVeinNoise) * 0.08f,
                            0.72f,
                            1.48f));
                    FirstPartyRainforestRiverEyeSlopeReliefCm =
                        (FirstPartyRainforestRiverEyeSlopeTextureMix - 0.5f) * 18.0f *
                            FirstPartyRainforestRiverEyeSlopeTextureT +
                        (FirstPartyRainforestRiverEyeSlopeRootVeinNoise - 0.5f) * 8.0f *
                            FirstPartyRainforestRiverEyeSlopeTextureT;
                }
            }
            Vertices.Add(FVector(
                X,
                Y,
                TerrainZ + BaseTerrainMicroReliefCm + SourceAwareTerrainPhotoMottleReliefCm +
                    SourceConditionedFarBankMicroReliefCm + BroadSlopeTerrainLowFrequencyReliefCm +
                    SourceAwareMacroTerrainRidgeReliefCm + SourceAwareTerrainSlopeFacetReliefCm +
                    SourceAwareRiparianCanopyMassReliefCm + FirstPartyMaterialAtlasTerrainReliefCm +
                    FirstPartyTerrainSurfaceGranularityReliefCm + FirstPartyRainforestRiverEyeSlopeReliefCm));
            UVs.Add(FVector2D(U * 12.0f, V * 4.0f));
            VertexColors.Add(NormalizePreviewTerrainProxyPatchColor(Spec, TerrainColor));
        }
    }

    const int32 RowSize = YSteps + 1;
    for (int32 XIndex = 0; XIndex < XSteps; ++XIndex)
    {
        for (int32 YIndex = 0; YIndex < YSteps; ++YIndex)
        {
            const int32 A = XIndex * RowSize + YIndex;
            const int32 B = A + 1;
            const int32 C = (XIndex + 1) * RowSize + YIndex;
            const int32 D = C + 1;
            Triangles.Add(A);
            Triangles.Add(C);
            Triangles.Add(B);
            Triangles.Add(B);
            Triangles.Add(C);
            Triangles.Add(D);
        }
    }
    Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    SoftenPreviewTerrainNormals(Normals, GetPreviewTerrainNormalSofteningBlend(Spec));

    AddPreviewProceduralMeshActor(
        World,
        FString::Printf(TEXT("RaftSim_ProceduralValleyTerrain_%s"), *Spec.RiverId),
        Vertices,
        Triangles,
        Normals,
        UVs,
        Spec.TerrainColor,
        LoadOrCreatePreviewTerrainVertexColorMaterial(),
        &VertexColors);
}

void AddPreviewAerialDrapeTiles(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* AerialDrape,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask)
{
    if (!World || !AerialDrape || !AerialDrape->IsValid())
    {
        return;
    }

    constexpr int32 XTiles = 44;
    constexpr int32 YTiles = 16;
    constexpr int32 MicrotileSubdivisions = 8;
    const float SourceOverlayPlateArtifactDemotion = 0.72f;
    const float MinX = -5600.0f;
    const float MaxX = 26000.0f;
    const float HalfWidth = Spec.bDesertCanyon ? 4300.0f : 2750.0f;
    const float TileLength = (MaxX - MinX) / static_cast<float>(XTiles);
    const float TileWidth = (HalfWidth * 2.0f) / static_cast<float>(YTiles);

    for (int32 XIndex = 0; XIndex < XTiles; ++XIndex)
    {
        const float U = (static_cast<float>(XIndex) + 0.5f) / static_cast<float>(XTiles);
        const float X = FMath::Lerp(MinX, MaxX, U);
        const float CenterY = GetPreviewRiverCenterY(Spec, X);
        for (int32 YIndex = 0; YIndex < YTiles; ++YIndex)
        {
            const float V = (static_cast<float>(YIndex) + 0.5f) / static_cast<float>(YTiles);
            const float Y = FMath::Lerp(-HalfWidth, HalfWidth, V);
            if (FMath::Abs(Y - CenterY) < GetPreviewActiveRiverHalfWidthCm(Spec) + 180.0f)
            {
                continue;
            }

            const float DemotedSourceAerialMicrotileWeight =
                (Spec.bDesertCanyon ? 0.44f : (Spec.bHasWaterfalls ? 0.36f : 0.40f)) *
                SourceOverlayPlateArtifactDemotion;
            const float DrapeWeight = DemotedSourceAerialMicrotileWeight;
            const float HalfLength = TileLength * 0.48f;
            const float HalfTileWidth = TileWidth * 0.48f;
            const float SourceOverlayMicrotileEdgeLiftCm = 4.0f;
            const float TileZOffset = 56.0f;
            const float X0 = X - HalfLength;
            const float X1 = X + HalfLength;
            const float Y0 = Y - HalfTileWidth;
            const float Y1 = Y + HalfTileWidth;

            TArray<FVector> Vertices;
            TArray<FLinearColor> VertexColors;
            TArray<FVector2D> UVs;
            TArray<int32> Triangles;
            Vertices.Reserve((MicrotileSubdivisions + 1) * (MicrotileSubdivisions + 1));
            VertexColors.Reserve((MicrotileSubdivisions + 1) * (MicrotileSubdivisions + 1));
            UVs.Reserve((MicrotileSubdivisions + 1) * (MicrotileSubdivisions + 1));
            Triangles.Reserve(MicrotileSubdivisions * MicrotileSubdivisions * 6);
            for (int32 LocalXIndex = 0; LocalXIndex <= MicrotileSubdivisions; ++LocalXIndex)
            {
                const float LocalU = static_cast<float>(LocalXIndex) / static_cast<float>(MicrotileSubdivisions);
                for (int32 LocalYIndex = 0; LocalYIndex <= MicrotileSubdivisions; ++LocalYIndex)
                {
                    const float LocalV = static_cast<float>(LocalYIndex) / static_cast<float>(MicrotileSubdivisions);
                    const float SampleX = FMath::Lerp(X0, X1, LocalU);
                    const float SampleY = FMath::Lerp(Y0, Y1, LocalV);
                    const float SampleSceneU = FMath::Clamp((SampleX - MinX) / (MaxX - MinX), 0.0f, 1.0f);
                    const float SampleSceneV = FMath::Clamp((SampleY + HalfWidth) / (HalfWidth * 2.0f), 0.0f, 1.0f);
                    const float SampleCenterY = GetPreviewRiverCenterY(Spec, SampleX);
                    const float Offset = FMath::Abs(SampleY - SampleCenterY);
                    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
                    const float BankT = SmoothPreviewStep(ActiveRiverHalfWidth, ActiveRiverHalfWidth + Spec.BankWidthCm, Offset);
                    const float CanyonT = SmoothPreviewStep(
                        ActiveRiverHalfWidth + Spec.BankWidthCm,
                        ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 1400.0f : 820.0f),
                        Offset);
                    const float WetT = 1.0f - SmoothPreviewStep(
                        ActiveRiverHalfWidth + 35.0f,
                        ActiveRiverHalfWidth + 360.0f * Spec.FlowWetBankScale,
                        Offset);
                    const float SourceWaterT =
                        WaterMask && WaterMask->IsValid() ? WaterMask->SampleLuma(SampleSceneU, SampleSceneV) : 0.0f;
                    const float SourceVegetationT = VegetationMask && VegetationMask->IsValid()
                        ? VegetationMask->SampleLuma(SampleSceneU, SampleSceneV)
                        : 0.0f;
                    const FLinearColor ShoulderColor = Spec.bDesertCanyon
                        ? FLinearColor(0.62f, 0.40f, 0.24f)
                        : ScalePreviewColor(Spec.TerrainColor, Spec.bHasWaterfalls ? 0.72f : 1.12f);
                    const FLinearColor WetBankColor = Spec.bDesertCanyon
                        ? FLinearColor(0.30f, 0.23f, 0.16f)
                        : FMath::Lerp(ScalePreviewColor(Spec.WaterColor, 0.55f), ScalePreviewColor(Spec.RockColor, 0.62f), 0.48f);
                    const FLinearColor SourceVegetationColor = Spec.bDesertCanyon
                        ? FLinearColor(0.30f, 0.31f, 0.17f)
                        : ScalePreviewColor(Spec.FoliageColor, Spec.bHasWaterfalls ? 1.18f : 1.05f);
                    FLinearColor TerrainColor = FMath::Lerp(
                        Spec.TerrainColor,
                        ShoulderColor,
                        FMath::Clamp(BankT * 0.45f + CanyonT * 0.35f, 0.0f, 1.0f));
                    TerrainColor = FMath::Lerp(
                        TerrainColor,
                        SourceVegetationColor,
                        FMath::Clamp(SourceVegetationT * (Spec.bDesertCanyon ? 0.12f : 0.26f), 0.0f, 0.32f));
                    TerrainColor = FMath::Lerp(
                        TerrainColor,
                        WetBankColor,
                        FMath::Clamp(FMath::Max(WetT * 0.42f, SourceWaterT * 0.28f), 0.0f, 0.54f));
                    TerrainColor = ScalePreviewColor(
                        TerrainColor,
                        0.92f + 0.06f * FMath::Sin(SampleX * 0.0059f + SampleY * 0.0042f));
                    FLinearColor SourceDrapeColor = NormalizePreviewSourceDrapeAlbedo(
                        Spec,
                        AerialDrape->Sample(SampleSceneU, SampleSceneV),
                        SourceWaterT,
                        SourceVegetationT,
                        Spec.bHasWaterfalls ? 0.44f : (Spec.bDesertCanyon ? 0.38f : 0.38f));
                    const float EdgeDistance = FMath::Min(
                        FMath::Min(LocalU, 1.0f - LocalU),
                        FMath::Min(LocalV, 1.0f - LocalV));
                    const float EdgeFeather = SmoothPreviewStep(0.02f, 0.34f, EdgeDistance);
                    const float PatchMottle = 0.84f + 0.08f * FMath::Sin(SampleX * 0.017f + SampleY * 0.013f + static_cast<float>(XIndex + YIndex) * 0.31f);
                    FLinearColor AerialColor = FMath::Lerp(
                        TerrainColor,
                        SourceDrapeColor,
                        FMath::Clamp(
                            DrapeWeight *
                                EdgeFeather *
                                PatchMottle *
                                FMath::Clamp(0.70f + BankT * 0.20f + CanyonT * 0.18f, 0.0f, 1.0f),
                            0.0f,
                            Spec.bDesertCanyon ? 0.30f : (Spec.bHasWaterfalls ? 0.26f : 0.28f)));
                    AerialColor.R = FMath::Max(AerialColor.R, Spec.TerrainColor.R * 0.68f + 0.015f);
                    AerialColor.G = FMath::Max(AerialColor.G, Spec.TerrainColor.G * 0.68f + 0.015f);
                    AerialColor.B = FMath::Max(AerialColor.B, Spec.TerrainColor.B * 0.68f + 0.015f);
                    AerialColor.A = 1.0f;
                    const float IntegratedTerrainCorridorTextureCell = FMath::Frac(
                        FMath::Sin(static_cast<float>((XIndex + 503) * 811 + (YIndex + 307) * 1031 +
                                                      (LocalXIndex + 17) * 131 + (LocalYIndex + 29) * 197) *
                                   12.9898f) *
                        43758.5453f);
                    AerialColor = ApplyPreviewIntegratedTerrainCorridorTexture(
                        Spec,
                        AerialColor,
                        SampleX,
                        SampleY,
                        BankT,
                        CanyonT,
                        WetT,
                        SourceWaterT,
                        SourceVegetationT,
                        Offset,
                        ActiveRiverHalfWidth,
                        IntegratedTerrainCorridorTextureCell);
                    AerialColor = NormalizePreviewTerrainProxyPatchColor(Spec, AerialColor);

                    Vertices.Add(FVector(
                        SampleX,
                        SampleY,
                        GetPreviewTerrainHeightCm(Spec, SampleX, SampleY, TerrainRelief, HeightfieldPreview) +
                            TileZOffset + EdgeFeather * SourceOverlayMicrotileEdgeLiftCm));
                    UVs.Add(FVector2D(LocalU, LocalV));
                    VertexColors.Add(AerialColor);
                }
            }

            const int32 RowSize = MicrotileSubdivisions + 1;
            for (int32 LocalXIndex = 0; LocalXIndex < MicrotileSubdivisions; ++LocalXIndex)
            {
                for (int32 LocalYIndex = 0; LocalYIndex < MicrotileSubdivisions; ++LocalYIndex)
                {
                    const int32 A = LocalXIndex * RowSize + LocalYIndex;
                    const int32 B = A + 1;
                    const int32 C = (LocalXIndex + 1) * RowSize + LocalYIndex;
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
            SoftenPreviewTerrainNormals(Normals, GetPreviewTerrainNormalSofteningBlend(Spec));

            AddPreviewProceduralMeshActor(
                World,
                FString::Printf(TEXT("RaftSim_SourceAerialDrapeMicroTile_%02d_%02d_%s"), XIndex, YIndex, *Spec.RiverId),
                Vertices,
                Triangles,
                Normals,
                UVs,
                Spec.TerrainColor,
                LoadOrCreatePreviewTerrainVertexColorMaterial(),
                &VertexColors);
        }
    }
}

AActor* AddPreviewRiverRibbonMesh(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* MaterialAtlasAlbedo,
    const FRaftSimPreviewImage* MaterialAtlasNormal,
    const FRaftSimPreviewImage* MaterialAtlasPacked,
    UMaterialInterface* MaterialOverride,
    const FRaftSimPreviewImage* SolverVisualizationFields,
    UMaterialInterface* SolverFoamMaterial)
{
    constexpr int32 XSteps = 640;
    // Odd cross-step count avoids a persistent vertex-color row exactly on the river centerline.
    constexpr int32 CrossSteps = 81;
    const float NearCameraUpstreamWaterApronMinX = -11600.0f;
    const float MinX = NearCameraUpstreamWaterApronMinX;
    const float MaxX = 26200.0f;

    TArray<FVector> Vertices;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<FLinearColor> SolverFoamVertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve((XSteps + 1) * (CrossSteps + 1));
    Normals.Reserve((XSteps + 1) * (CrossSteps + 1));
    UVs.Reserve((XSteps + 1) * (CrossSteps + 1));
    VertexColors.Reserve((XSteps + 1) * (CrossSteps + 1));
    SolverFoamVertexColors.Reserve((XSteps + 1) * (CrossSteps + 1));
    Triangles.Reserve(XSteps * CrossSteps * 6);

    const FLinearColor DeepWaterBase = ScalePreviewColor(Spec.WaterColor, Spec.bDesertCanyon ? 0.98f : 1.02f);
    const FLinearColor DeepWater = Spec.bDesertCanyon
        ? FMath::Lerp(DeepWaterBase, FLinearColor(0.20f, 0.18f, 0.13f), 0.35f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(DeepWaterBase, FLinearColor(0.018f, 0.170f, 0.090f), 0.34f)
                                : FMath::Lerp(DeepWaterBase, FLinearColor(0.028f, 0.205f, 0.115f), 0.32f));
    const FLinearColor ShallowWater = Spec.bDesertCanyon
        ? FLinearColor(0.34f, 0.30f, 0.22f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.050f, 0.310f, 0.170f) : FLinearColor(0.078f, 0.340f, 0.205f));
    const FLinearColor SurfaceGlint = Spec.bDesertCanyon
        ? FLinearColor(0.58f, 0.49f, 0.34f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.18f, 0.520f, 0.320f) : FLinearColor(0.20f, 0.540f, 0.360f));
    const FLinearColor NearFieldBrightRipple = Spec.bDesertCanyon
        ? FLinearColor(0.42f, 0.37f, 0.27f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.080f, 0.330f, 0.190f) : FLinearColor(0.095f, 0.360f, 0.220f));
    const FLinearColor NearFieldDarkSlick = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.16f, 0.14f, 0.105f), 0.46f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.010f, 0.105f, 0.085f), 0.38f)
                                : FMath::Lerp(Spec.WaterColor, FLinearColor(0.012f, 0.135f, 0.155f), 0.40f));
    const FLinearColor BaseWaterDeepCurrentTongue = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.17f, 0.15f, 0.11f), 0.44f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.006f, 0.095f, 0.075f), 0.36f)
                                : FMath::Lerp(Spec.WaterColor, FLinearColor(0.008f, 0.12f, 0.145f), 0.38f));
    const FLinearColor BaseWaterSedimentThread = Spec.bDesertCanyon
        ? FLinearColor(0.36f, 0.30f, 0.20f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.045f, 0.21f, 0.14f) : FLinearColor(0.065f, 0.29f, 0.25f));
    const FLinearColor BaseWaterSkyThread = Spec.bDesertCanyon
        ? FLinearColor(0.46f, 0.42f, 0.32f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.100f, 0.300f, 0.185f) : FLinearColor(0.120f, 0.340f, 0.220f));
    const FLinearColor FlowCuedWaterFoamMottleColor = Spec.bDesertCanyon
        ? FLinearColor(0.58f, 0.53f, 0.40f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.48f, 0.70f, 0.54f) : FLinearColor(0.50f, 0.70f, 0.56f));
    const FLinearColor FlowCuedWaterSlickMottleColor = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.12f, 0.105f, 0.082f), 0.42f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.004f, 0.070f, 0.058f), 0.34f)
                                : FMath::Lerp(Spec.WaterColor, FLinearColor(0.006f, 0.095f, 0.120f), 0.36f));
    const FLinearColor BaseWaterCrossChannelShadow = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.18f, 0.155f, 0.112f), 0.30f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.008f, 0.145f, 0.115f), 0.26f)
                                : FMath::Lerp(Spec.WaterColor, FLinearColor(0.010f, 0.185f, 0.205f), 0.24f));
    const FLinearColor BaseWaterCrossChannelHighlight = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.46f, 0.39f, 0.265f), 0.24f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.100f, 0.400f, 0.240f), 0.22f)
                                : FMath::Lerp(Spec.WaterColor, FLinearColor(0.115f, 0.430f, 0.270f), 0.20f));
    const FLinearColor BaseWaterFlowThreadShadow = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.23f, 0.195f, 0.135f), 0.32f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.006f, 0.150f, 0.115f), 0.30f)
                                : FMath::Lerp(Spec.WaterColor, FLinearColor(0.008f, 0.185f, 0.205f), 0.28f));
    const FLinearColor BaseWaterFlowThreadHighlight = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.56f, 0.49f, 0.34f), 0.28f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.140f, 0.480f, 0.290f), 0.28f)
                                : FMath::Lerp(Spec.WaterColor, FLinearColor(0.155f, 0.500f, 0.320f), 0.25f));
    const FLinearColor BaseWaterFlowThreadFoamGlint = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.70f, 0.64f, 0.48f), 0.20f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.42f, 0.72f, 0.52f), 0.18f)
                                : FMath::Lerp(Spec.WaterColor, FLinearColor(0.45f, 0.74f, 0.54f), 0.16f));
    const FLinearColor NearCameraWaterMacroRippleShadow = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.22f, 0.185f, 0.125f), 0.34f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.004f, 0.145f, 0.112f), 0.30f)
                                : FMath::Lerp(Spec.WaterColor, FLinearColor(0.006f, 0.190f, 0.205f), 0.28f));
    const FLinearColor NearCameraWaterMacroRippleHighlight = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.54f, 0.47f, 0.330f), 0.26f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.140f, 0.460f, 0.270f), 0.28f)
                                : FMath::Lerp(Spec.WaterColor, FLinearColor(0.150f, 0.480f, 0.300f), 0.24f));
    const bool bUsePhysicalCandidateShading = MaterialOverride != nullptr;
    const FRaftSimLandscapeCandidateWaterSettings CandidateWaterSettings =
        GetLandscapeCandidateWaterSettings(Spec.RiverId);
    const bool bUseSolverVisualizationFields =
        bUsePhysicalCandidateShading &&
        Spec.RiverId == TEXT("american_south_fork") &&
        CandidateWaterSettings.SolverFieldEnable > 0.5f &&
        SolverVisualizationFields &&
        SolverVisualizationFields->IsValid() &&
        SolverFoamMaterial;
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float WaterBaseZ = GetPreviewWaterSurfaceBaseZCm(Spec);
    const float FlowEnergy = FMath::Clamp(Spec.FlowCurrentCueScale, 0.65f, 1.60f);
    const float LongDarkWaterStreakDemotion = 0.0f;
    const float BaseWaterCenterGuideStripeDemotion = 0.0f;
    const float WaterLineArtifactColorReblend = Spec.bDesertCanyon ? 0.10f : 0.14f;
    const float BaseWaveAmplitudeCm =
        (Spec.bDesertCanyon ? 5.0f : (Spec.bHasWaterfalls ? 9.0f : 7.0f)) * FlowEnergy;
    const float StandingWaveAmplitudeCm =
        (Spec.bDesertCanyon ? 3.5f : (Spec.bHasWaterfalls ? 5.8f : 4.6f)) *
        FMath::Clamp(Spec.FlowFoamScale, 0.70f, 1.55f);
    const float NearFieldFineRippleAmplitudeCm =
        (Spec.bDesertCanyon ? 1.6f : (Spec.bHasWaterfalls ? 3.1f : 2.6f)) * FlowEnergy;
    const float NearCameraWaterMacroRippleMottleT = 1.0f;
    const float NearCameraWaterMacroRippleReliefT = 1.0f;

    for (int32 XIndex = 0; XIndex <= XSteps; ++XIndex)
    {
        const float U = static_cast<float>(XIndex) / static_cast<float>(XSteps);
        const float X = FMath::Lerp(MinX, MaxX, U);
        const float CenterY = GetPreviewRiverCenterY(Spec, X);
        const float Width =
            ActiveRiverHalfWidth *
            (1.0f + 0.10f * FMath::Sin(X * 0.0012f) + (Spec.bDesertCanyon ? 0.18f : 0.05f)) *
            (bUsePhysicalCandidateShading ? CandidateWaterSettings.RenderWidthScale : 1.0f);
        for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
        {
            const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
            const FLinearColor SolverField = bUseSolverVisualizationFields
                ? SolverVisualizationFields->SampleRawBilinear(U, 1.0f - V)
                : FLinearColor::Black;
            const float SolverSpeedVisual = FMath::Clamp(
                SolverField.G * CandidateWaterSettings.SolverSpeedVisualGain,
                0.0f,
                1.0f);
            const float SolverFroudeVisual = FMath::Clamp(
                SolverField.B * CandidateWaterSettings.SolverFroudeVisualGain,
                0.0f,
                1.0f);
            const float SolverHydraulicPresence = bUseSolverVisualizationFields
                ? SmoothPreviewStep(
                      0.015f,
                      0.12f,
                      FMath::Clamp(SolverField.R + SolverSpeedVisual + SolverFroudeVisual, 0.0f, 1.0f))
                : 0.0f;
            const float SolverSurfaceReliefCm = bUseSolverVisualizationFields
                ? (SolverField.A - 0.5f) * 8.0f * 100.0f *
                      CandidateWaterSettings.SolverSurfaceReliefScale * SolverHydraulicPresence
                : 0.0f;
            const float SolverHydraulicAerationT = bUseSolverVisualizationFields
                ? SmoothPreviewStep(0.18f, 0.88f, SolverFroudeVisual) *
                      SmoothPreviewStep(0.12f, 0.82f, SolverSpeedVisual) *
                      SolverHydraulicPresence
                : 0.0f;
            const float Lateral = FMath::Lerp(-Width, Width, V);
            const float EdgeT = FMath::Pow(FMath::Abs(V - 0.5f) * 2.0f, 1.35f);
            const float CenterT = 1.0f - FMath::Clamp(EdgeT, 0.0f, 1.0f);
            const float CrossWaveT = FMath::Sin((V - 0.5f) * PI);
            const float Wave =
                BaseWaveAmplitudeCm *
                    (0.58f * FMath::Sin(X * 0.010f * FlowEnergy + Lateral * 0.010f) +
                     0.28f * FMath::Sin(X * 0.021f - Lateral * 0.004f + FlowEnergy * 1.7f)) *
                    (0.58f + CenterT * 0.42f) +
                StandingWaveAmplitudeCm *
                    FMath::Sin(X * (Spec.bDesertCanyon ? 0.0032f : 0.0049f) + CrossWaveT * 1.85f) *
                    FMath::Pow(CenterT, Spec.bDesertCanyon ? 0.90f : 0.72f);
            const float NearFieldWaterSurfaceGrainT =
                1.0f - SmoothPreviewStep(4200.0f, 7600.0f, X);
            const float NearFieldFacetedWaterSmoothingT =
                FMath::Clamp(1.0f - SmoothPreviewStep(9800.0f, 19000.0f, X), 0.0f, 1.0f);
            const float FirstPartyWaterCellularFacetGain =
                FMath::Lerp(0.18f, 0.025f, NearFieldFacetedWaterSmoothingT);
            const float FirstPartyWaterBaseWaveGain =
                FMath::Lerp(0.78f, 0.38f, NearFieldFacetedWaterSmoothingT);
            const float FirstPartyWaterColorFacetGain =
                FMath::Lerp(0.74f, 0.58f, NearFieldFacetedWaterSmoothingT);
            const float FirstPartyWaterMicroReliefGain =
                FMath::Lerp(0.28f, 0.12f, NearFieldFacetedWaterSmoothingT);
            const float FirstPartyWaterLargeReliefGain =
                FMath::Lerp(0.62f, 0.24f, NearFieldFacetedWaterSmoothingT);
            const float FineRipple =
                FMath::Clamp(
                    0.50f +
                        0.28f * FMath::Sin(X * 0.032f + Lateral * 0.018f + FlowEnergy * 0.73f) +
                        0.22f * FMath::Sin(X * 0.055f - Lateral * 0.009f),
                    0.0f,
                    1.0f);
            const float FineSlick =
                FMath::Clamp(
                    0.50f +
                        0.30f * FMath::Sin(X * 0.020f - Lateral * 0.021f) +
                        0.20f * FMath::Sin(X * 0.061f + Lateral * 0.004f + FlowEnergy),
                    0.0f,
                    1.0f);
            const float FlowNoise =
                0.50f + 0.30f * FMath::Sin(X * 0.0048f + Lateral * 0.010f) +
                0.20f * FMath::Sin(X * 0.013f - Lateral * 0.006f);
            const float CenterGuideStripeT = FMath::Pow(CenterT, 3.0f);
            const float NearFieldCenterStripeDemotionT = 1.0f - SmoothPreviewStep(8800.0f, 17200.0f, X);
            const float CenterStripeBreakupSeed = FMath::Clamp(
                0.50f + 0.34f * FMath::Sin(X * 0.0087f + Lateral * 0.015f + FlowEnergy * 0.33f) +
                    0.16f * FMath::Sin(X * 0.031f - Lateral * 0.006f),
                0.0f,
                1.0f);
            const float CenterStripeBreakupT = SmoothPreviewStep(0.38f, 0.82f, CenterStripeBreakupSeed);
            const float BaseWaterCenterGuideStripeGain = FMath::Lerp(
                1.0f,
                FMath::Lerp(BaseWaterCenterGuideStripeDemotion, 0.22f, CenterStripeBreakupT),
                FMath::Clamp(CenterGuideStripeT * (0.82f + 0.18f * NearFieldCenterStripeDemotionT), 0.0f, 1.0f));
            const float BaseWaterDepthCurrentGradingT = FMath::Clamp(
                CenterT *
                    (0.52f + 0.28f * FMath::Sin(X * 0.0037f + Lateral * 0.0019f + FlowEnergy) +
                     0.20f * FMath::Sin(X * 0.011f - Lateral * 0.0047f)),
                0.0f,
                1.0f);
            const float BaseWaterCurrentTongueT = FMath::Clamp(
                FMath::Pow(BaseWaterDepthCurrentGradingT, 1.35f) * FlowEnergy * 0.18f * LongDarkWaterStreakDemotion *
                    BaseWaterCenterGuideStripeGain,
                0.0f,
                Spec.bDesertCanyon ? 0.020f : 0.024f);
            const float BaseWaterSedimentThreadT = FMath::Clamp(
                (0.40f + EdgeT * 0.60f) *
                    (0.50f + 0.50f * FMath::Sin(X * 0.0068f + Lateral * 0.0036f + 2.1f)) *
                    (Spec.bDesertCanyon ? 0.15f : 0.10f),
                0.0f,
                Spec.bDesertCanyon ? 0.15f : 0.10f);
            const float BaseWaterSkyThreadT = FMath::Clamp(
                CenterT *
                    (0.50f + 0.50f * FMath::Sin(X * 0.015f + Lateral * 0.0023f - FlowEnergy * 0.6f)) *
                    (Spec.bDesertCanyon ? 0.060f : 0.080f),
                0.0f,
                Spec.bDesertCanyon ? 0.060f : 0.080f);
            const float FlowCuedWaterFoamSeed =
                FMath::Clamp(
                    0.50f +
                        0.30f * FMath::Sin(X * 0.018f + Lateral * 0.012f + FlowEnergy * 1.37f) +
                        0.20f * FMath::Sin(X * 0.041f - Lateral * 0.020f),
                    0.0f,
                    1.0f);
            const float FlowCuedWaterSlickSeed =
                FMath::Clamp(
                    0.50f +
                        0.34f * FMath::Sin(X * 0.009f - Lateral * 0.014f + FlowEnergy * 0.61f) +
                        0.16f * FMath::Sin(X * 0.026f + Lateral * 0.006f),
                    0.0f,
                    1.0f);
            const float FlowCuedWaterFoamMottleT = FMath::Clamp(
                FlowCuedWaterFoamSeed *
                    (0.34f + CenterT * 0.50f + EdgeT * 0.20f) *
                    Spec.FlowFoamScale *
                    (Spec.bDesertCanyon ? 0.055f : (Spec.bHasWaterfalls ? 0.095f : 0.075f)),
                0.0f,
                Spec.bDesertCanyon ? 0.060f : (Spec.bHasWaterfalls ? 0.105f : 0.085f));
            const float FlowCuedWaterSlickMottleT = FMath::Clamp(
                FlowCuedWaterSlickSeed *
                    CenterT *
                    FlowEnergy *
                    (Spec.bDesertCanyon ? 0.070f : 0.090f) *
                    LongDarkWaterStreakDemotion *
                    BaseWaterCenterGuideStripeGain,
                0.0f,
                Spec.bDesertCanyon ? 0.010f : 0.012f);
            const float BaseWaterCrossChannelBreakupNoise = FMath::Clamp(
                0.50f +
                    0.24f * FMath::Sin(X * 0.0061f + Lateral * 0.017f + FlowEnergy * 0.29f) +
                    0.18f * FMath::Sin(X * 0.017f - Lateral * 0.010f + EdgeT * 1.7f) +
                    0.12f * FMath::Sin(X * 0.041f + Lateral * 0.027f),
                0.0f,
                1.0f);
            const float BaseWaterCrossChannelCenterGuardT =
                1.0f - SmoothPreviewStep(0.88f, 1.0f, CenterT) * 0.35f;
            const float BaseWaterCrossChannelBreakupT = FMath::Clamp(
                (0.24f + EdgeT * 0.32f + CenterT * 0.22f) *
                    (0.74f + FlowEnergy * 0.18f) *
                    BaseWaterCrossChannelCenterGuardT,
                0.0f,
                1.0f);
            const float BaseWaterCrossChannelShadowT =
                SmoothPreviewStep(0.10f, 0.44f, 1.0f - BaseWaterCrossChannelBreakupNoise) *
                BaseWaterCrossChannelBreakupT;
            const float BaseWaterCrossChannelHighlightT =
                SmoothPreviewStep(0.56f, 0.92f, BaseWaterCrossChannelBreakupNoise) *
                BaseWaterCrossChannelBreakupT;
            const float NearCameraWaterMacroRippleReachT = FMath::Clamp(
                SmoothPreviewStep(-5600.0f, -5000.0f, X) * (1.0f - SmoothPreviewStep(10200.0f, 22400.0f, X)),
                0.0f,
                1.0f);
            const float NearCameraBottomCenterWaterWedgeLongitudinalT =
                1.0f - SmoothPreviewStep(-5250.0f, -1700.0f, X);
            const float NearCameraBottomCenterWaterWedgeLateralT =
                FMath::Clamp(0.56f + 0.44f * SmoothPreviewStep(0.05f, 0.88f, CenterT), 0.0f, 1.0f);
            const float NearCameraBottomCenterWaterWedgeDemotionT = FMath::Clamp(
                NearCameraBottomCenterWaterWedgeLongitudinalT * NearCameraBottomCenterWaterWedgeLateralT,
                0.0f,
                1.0f);
            const float NearCameraWaterMacroRippleNoise = FMath::Clamp(
                0.50f +
                    0.24f * FMath::Sin(X * 0.0044f + Lateral * 0.012f + FlowEnergy * 0.17f) +
                    0.21f * FMath::Sin(X * 0.0130f - Lateral * 0.021f + FlowEnergy * 0.77f) +
                    0.11f * FMath::Sin(X * 0.0300f + Lateral * 0.037f),
                0.0f,
                1.0f);
            const float NearCameraWaterMacroRippleSeamGuardT =
                1.0f - SmoothPreviewStep(0.92f, 1.0f, CenterT) * 0.32f;
            const float NearCameraWaterMacroRipplePatchT = FMath::Clamp(
                (0.42f + CenterT * 0.30f + EdgeT * 0.18f) *
                    NearCameraWaterMacroRippleReachT *
                    NearCameraWaterMacroRippleSeamGuardT *
                    NearCameraWaterMacroRippleMottleT *
                    (0.84f + FlowEnergy * 0.14f),
                0.0f,
                1.0f);
            const float NearCameraWaterMacroRippleShadowT =
                SmoothPreviewStep(0.12f, 0.43f, 1.0f - NearCameraWaterMacroRippleNoise) *
                NearCameraWaterMacroRipplePatchT;
            const float NearCameraWaterMacroRippleHighlightT =
                SmoothPreviewStep(0.56f, 0.91f, NearCameraWaterMacroRippleNoise) *
                NearCameraWaterMacroRipplePatchT;
            const float BaseWaterFlowThreadNoise = FMath::Clamp(
                0.50f +
                    0.22f * FMath::Sin(X * 0.0062f + Lateral * 0.014f + FlowEnergy * 0.41f) +
                    0.20f * FMath::Sin(X * 0.0180f - Lateral * 0.010f + EdgeT * 1.4f) +
                    0.12f * FMath::Sin(X * 0.0400f + Lateral * 0.024f),
                0.0f,
                1.0f);
            const float BaseWaterFlowThreadLongBand = FMath::Clamp(
                0.50f +
                    0.31f * FMath::Sin(X * 0.0028f + Lateral * 0.0040f + FlowEnergy * 0.23f) +
                    0.19f * FMath::Sin(X * 0.0074f - Lateral * 0.0024f),
                0.0f,
                1.0f);
            const float BaseWaterFlowThreadTextureT = FMath::Clamp(
                (0.32f + CenterT * 0.50f + EdgeT * 0.18f) *
                    (0.84f + FlowEnergy * 0.18f) *
                    (0.62f + BaseWaterFlowThreadLongBand * 0.38f),
                0.0f,
                1.0f);
            const float BaseWaterFlowThreadShadowT =
                SmoothPreviewStep(0.12f, 0.44f, 1.0f - BaseWaterFlowThreadNoise) *
                BaseWaterFlowThreadTextureT;
            const float BaseWaterFlowThreadHighlightT =
                SmoothPreviewStep(0.56f, 0.92f, BaseWaterFlowThreadNoise) *
                BaseWaterFlowThreadTextureT;
            const float BaseWaterFlowThreadFoamGlintT = FMath::Clamp(
                SmoothPreviewStep(0.78f, 0.97f, BaseWaterFlowThreadNoise) *
                    SmoothPreviewStep(0.22f, 0.74f, CenterT) *
                    Spec.FlowFoamScale *
                    (Spec.bDesertCanyon ? 0.040f : (Spec.bHasWaterfalls ? 0.070f : 0.060f)),
                0.0f,
                Spec.bDesertCanyon ? 0.044f : (Spec.bHasWaterfalls ? 0.074f : 0.064f));
            const float BaseWaterCenterSeamDiffusionT =
                SmoothPreviewStep(0.72f, 0.98f, CenterT) *
                (0.62f + CenterStripeBreakupT * 0.20f) *
                (0.86f + NearFieldCenterStripeDemotionT * 0.14f);
            const float BaseWaterResidualCenterSeamEraseT =
                SmoothPreviewStep(0.68f, 0.965f, CenterT) *
                (0.90f + 0.06f * NearFieldCenterStripeDemotionT + 0.04f * CenterStripeBreakupT);
            FLinearColor WaterColor = FMath::Lerp(DeepWater, ShallowWater, FMath::Clamp(EdgeT * 0.55f, 0.0f, 1.0f));
            WaterColor = FMath::Lerp(WaterColor, BaseWaterDeepCurrentTongue, BaseWaterCurrentTongueT);
            WaterColor = FMath::Lerp(WaterColor, BaseWaterSedimentThread, BaseWaterSedimentThreadT);
            WaterColor = FMath::Lerp(WaterColor, BaseWaterSkyThread, BaseWaterSkyThreadT);
            WaterColor = FMath::Lerp(WaterColor, FlowCuedWaterSlickMottleColor, FlowCuedWaterSlickMottleT);
            WaterColor = FMath::Lerp(WaterColor, FlowCuedWaterFoamMottleColor, FlowCuedWaterFoamMottleT);
            WaterColor = FMath::Lerp(
                WaterColor,
                SurfaceGlint,
                FMath::Clamp((1.0f - EdgeT * 0.45f) * FlowNoise * FlowEnergy * (Spec.bDesertCanyon ? 0.12f : 0.16f), 0.0f, 0.22f));
            const float NearFieldTextureGain = FMath::Clamp(0.36f + NearFieldWaterSurfaceGrainT * 0.64f, 0.0f, 1.0f);
            WaterColor = FMath::Lerp(
                WaterColor,
                NearFieldDarkSlick,
                FMath::Clamp(
                    FineSlick * CenterT * NearFieldTextureGain * 0.070f * LongDarkWaterStreakDemotion *
                        BaseWaterCenterGuideStripeGain,
                    0.0f,
                    0.010f));
            WaterColor = FMath::Lerp(
                WaterColor,
                NearFieldBrightRipple,
                FMath::Clamp(FineRipple * (0.58f + CenterT * 0.42f) * NearFieldTextureGain * 0.055f, 0.0f, 0.065f));
            WaterColor = FMath::Lerp(
                WaterColor,
                Spec.WaterColor,
                FMath::Clamp(
                    CenterT * WaterLineArtifactColorReblend +
                        CenterGuideStripeT * (0.18f + 0.18f * NearFieldCenterStripeDemotionT),
                    0.0f,
                    0.42f));
            const FLinearColor CenterLaneEraseColor = Spec.WaterColor;
            const float CenterLaneBroadEraseT = SmoothPreviewStep(0.12f, 0.68f, CenterT);
            WaterColor = FMath::Lerp(
                WaterColor,
                CenterLaneEraseColor,
                FMath::Clamp(CenterLaneBroadEraseT * (0.14f + 0.16f * NearFieldCenterStripeDemotionT), 0.0f, 0.34f));
            WaterColor = FMath::Lerp(
                WaterColor,
                BaseWaterCrossChannelShadow,
                FMath::Clamp(BaseWaterCrossChannelShadowT * (Spec.bDesertCanyon ? 0.050f : 0.045f), 0.0f, 0.055f));
            WaterColor = FMath::Lerp(
                WaterColor,
                BaseWaterCrossChannelHighlight,
                FMath::Clamp(BaseWaterCrossChannelHighlightT * (Spec.bDesertCanyon ? 0.060f : 0.055f), 0.0f, 0.065f));
            const FLinearColor BaseWaterCenterSeamDiffusionColor = Spec.WaterColor;
            WaterColor = FMath::Lerp(
                WaterColor,
                BaseWaterCenterSeamDiffusionColor,
                FMath::Clamp(BaseWaterCenterSeamDiffusionT * (Spec.bDesertCanyon ? 0.080f : 0.105f), 0.0f, 0.12f));
            const FLinearColor BaseWaterResidualCenterSeamEraseColor = Spec.WaterColor;
            WaterColor = FMath::Lerp(
                WaterColor,
                BaseWaterResidualCenterSeamEraseColor,
                FMath::Clamp(BaseWaterResidualCenterSeamEraseT * (Spec.bDesertCanyon ? 0.28f : 0.34f), 0.0f, 0.38f));
            WaterColor = FMath::Lerp(
                WaterColor,
                NearCameraWaterMacroRippleShadow,
                FMath::Clamp(
                    NearCameraWaterMacroRippleShadowT * (Spec.bDesertCanyon ? 0.092f : (Spec.bHasWaterfalls ? 0.112f : 0.104f)),
                    0.0f,
                    Spec.bDesertCanyon ? 0.092f : 0.112f));
            WaterColor = FMath::Lerp(
                WaterColor,
                NearCameraWaterMacroRippleHighlight,
                FMath::Clamp(
                    NearCameraWaterMacroRippleHighlightT *
                        (Spec.bDesertCanyon ? 0.092f : (Spec.bHasWaterfalls ? 0.112f : 0.104f)),
                    0.0f,
                    Spec.bDesertCanyon ? 0.098f : 0.118f));
            WaterColor = FMath::Lerp(
                WaterColor,
                BaseWaterFlowThreadShadow,
                FMath::Clamp(
                    BaseWaterFlowThreadShadowT * (Spec.bDesertCanyon ? 0.085f : (Spec.bHasWaterfalls ? 0.105f : 0.096f)),
                    0.0f,
                    Spec.bDesertCanyon ? 0.088f : 0.108f));
            WaterColor = FMath::Lerp(
                WaterColor,
                BaseWaterFlowThreadHighlight,
                FMath::Clamp(
                    BaseWaterFlowThreadHighlightT *
                        (Spec.bDesertCanyon ? 0.095f : (Spec.bHasWaterfalls ? 0.118f : 0.108f)),
                    0.0f,
                    Spec.bDesertCanyon ? 0.098f : 0.122f));
            WaterColor = FMath::Lerp(WaterColor, BaseWaterFlowThreadFoamGlint, BaseWaterFlowThreadFoamGlintT);
            const float FirstPartyMaterialAtlasWaterBlend = FMath::Clamp(
                (0.048f + EdgeT * 0.032f + CenterT * 0.026f + FlowEnergy * 0.014f) *
                    (1.0f - BaseWaterResidualCenterSeamEraseT * 0.18f),
                0.0f,
                Spec.bHasWaterfalls ? 0.145f : (Spec.bDesertCanyon ? 0.105f : 0.130f));
            WaterColor = ApplyFirstPartyMaterialAtlasTint(
                Spec,
                MaterialAtlasAlbedo,
                FlowDependentWaterSurfaceMaterialTile,
                WaterColor,
                U * 16.0f + FlowNoise * 0.43f,
                V * 2.7f + BaseWaterFlowThreadLongBand * 0.31f,
                FirstPartyMaterialAtlasWaterBlend);
            WaterColor = ApplyFirstPartyMaterialAtlasSurfaceResponse(
                Spec,
                MaterialAtlasNormal,
                MaterialAtlasPacked,
                FlowDependentWaterSurfaceMaterialTile,
                WaterColor,
                U * 16.0f + FlowNoise * 0.43f,
                V * 2.7f + BaseWaterFlowThreadLongBand * 0.31f,
                FirstPartyMaterialAtlasWaterBlend);
            const float FirstPartyPostSeamWaterSurfaceGrainNoise = FMath::Clamp(
                0.50f +
                    0.31f * FMath::Sin(X * 0.019f + Lateral * 0.031f + FlowEnergy * 0.43f) +
                    0.24f * FMath::Sin(X * 0.047f - Lateral * 0.017f) +
                    0.14f * FMath::Sin(X * 0.083f + Lateral * 0.061f),
                0.0f,
                1.0f);
            const float FirstPartyPostSeamWaterSurfaceGrainT = FMath::Clamp(
                (0.26f + CenterT * 0.34f + EdgeT * 0.28f) *
                    (0.72f + NearFieldWaterSurfaceGrainT * 0.28f) *
                    FirstPartyWaterColorFacetGain *
                    (1.0f - BaseWaterResidualCenterSeamEraseT * 0.18f),
                0.0f,
                1.0f);
            const FLinearColor FirstPartyPostSeamWaterSurfaceGrainShadow = Spec.bDesertCanyon
                ? FLinearColor(0.250f, 0.215f, 0.145f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.030f, 0.220f, 0.115f)
                                        : FLinearColor(0.045f, 0.255f, 0.145f));
            const FLinearColor FirstPartyPostSeamWaterSurfaceGrainHighlight = Spec.bDesertCanyon
                ? FLinearColor(0.550f, 0.490f, 0.340f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.180f, 0.440f, 0.260f)
                                        : FLinearColor(0.200f, 0.470f, 0.300f));
            WaterColor = FMath::Lerp(
                WaterColor,
                FirstPartyPostSeamWaterSurfaceGrainShadow,
                FMath::Clamp(
                    SmoothPreviewStep(0.10f, 0.44f, 1.0f - FirstPartyPostSeamWaterSurfaceGrainNoise) *
                        FirstPartyPostSeamWaterSurfaceGrainT *
                        (Spec.bDesertCanyon ? 0.085f : 0.105f),
                    0.0f,
                    Spec.bDesertCanyon ? 0.090f : 0.112f));
            WaterColor = FMath::Lerp(
                WaterColor,
                FirstPartyPostSeamWaterSurfaceGrainHighlight,
                FMath::Clamp(
                    SmoothPreviewStep(0.56f, 0.92f, FirstPartyPostSeamWaterSurfaceGrainNoise) *
                        FirstPartyPostSeamWaterSurfaceGrainT *
                        (Spec.bDesertCanyon ? 0.095f : 0.118f),
                    0.0f,
                    Spec.bDesertCanyon ? 0.100f : 0.124f));
            const FLinearColor BaseWaterResidualDarkStreakLumaFloor = Spec.bDesertCanyon
                ? FLinearColor(0.310f, 0.260f, 0.185f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.050f, 0.255f, 0.140f)
                                        : FLinearColor(0.060f, 0.280f, 0.170f));
            WaterColor.R = FMath::Max(WaterColor.R, BaseWaterResidualDarkStreakLumaFloor.R);
            WaterColor.G = FMath::Max(WaterColor.G, BaseWaterResidualDarkStreakLumaFloor.G);
            WaterColor.B = FMath::Max(WaterColor.B, BaseWaterResidualDarkStreakLumaFloor.B);
            const float FirstPartyCaptureQualityWaterTextureCell = FMath::Frac(
                FMath::Sin(static_cast<float>((XIndex + 17) * 127 + (CrossIndex + 23) * 311) * 12.9898f) *
                43758.5453f);
            const float FirstPartyCaptureQualityWaterTextureFine = FMath::Clamp(
                0.50f +
                    0.29f * FMath::Sin(X * 0.091f + Lateral * 0.073f + FlowEnergy * 0.37f) +
                    0.21f * FMath::Sin(X * 0.163f - Lateral * 0.047f + EdgeT * 0.91f),
                0.0f,
                1.0f);
            const float FirstPartyCaptureQualityWaterTextureNoise = FMath::Clamp(
                FirstPartyCaptureQualityWaterTextureCell * FirstPartyWaterCellularFacetGain +
                    FirstPartyCaptureQualityWaterTextureFine * (1.0f - FirstPartyWaterCellularFacetGain),
                0.0f,
                1.0f);
            const float FirstPartyCaptureQualityWaterTextureMottleT = FMath::Clamp(
                (0.22f + CenterT * 0.31f + EdgeT * 0.21f) *
                    (0.74f + NearFieldWaterSurfaceGrainT * 0.26f) *
                    (0.82f + FlowEnergy * 0.12f) *
                    FirstPartyWaterColorFacetGain *
                    (1.0f - BaseWaterResidualCenterSeamEraseT * 0.12f),
                0.0f,
                Spec.bDesertCanyon ? 0.36f : 0.42f);
            const FLinearColor FirstPartyCaptureQualityWaterTextureShadow = Spec.bDesertCanyon
                ? FLinearColor(0.285f, 0.235f, 0.160f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.045f, 0.230f, 0.115f)
                                        : FLinearColor(0.055f, 0.250f, 0.140f));
            const FLinearColor FirstPartyCaptureQualityWaterTextureHighlight = Spec.bDesertCanyon
                ? FLinearColor(0.620f, 0.535f, 0.370f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.210f, 0.480f, 0.280f)
                                        : FLinearColor(0.235f, 0.510f, 0.320f));
            WaterColor = FMath::Lerp(
                WaterColor,
                FirstPartyCaptureQualityWaterTextureShadow,
                FMath::Clamp(
                    SmoothPreviewStep(0.08f, 0.36f, 1.0f - FirstPartyCaptureQualityWaterTextureNoise) *
                        FirstPartyCaptureQualityWaterTextureMottleT *
                        (Spec.bDesertCanyon ? 0.19f : 0.22f),
                    0.0f,
                    Spec.bDesertCanyon ? 0.20f : 0.23f));
            WaterColor = FMath::Lerp(
                WaterColor,
                FirstPartyCaptureQualityWaterTextureHighlight,
                FMath::Clamp(
                    SmoothPreviewStep(0.58f, 0.94f, FirstPartyCaptureQualityWaterTextureNoise) *
                        FirstPartyCaptureQualityWaterTextureMottleT *
                        (Spec.bDesertCanyon ? 0.17f : 0.20f),
                    0.0f,
                    Spec.bDesertCanyon ? 0.18f : 0.21f));
            const float FirstPartyWaterPaletteCell = FMath::Frac(
                FMath::Sin(static_cast<float>((XIndex + 199) * 463 + (CrossIndex + 109) * 719) * 12.9898f) *
                43758.5453f);
            const float FirstPartyWaterPaletteBandSeed = FMath::Clamp(
                0.50f +
                    0.31f * FMath::Sin(X * 0.0042f + Lateral * 0.0068f + FlowEnergy * 0.19f) +
                    0.19f * FMath::Sin(X * 0.0108f - Lateral * 0.0037f + EdgeT * 0.64f),
                0.0f,
                1.0f);
            const float FirstPartyWaterPaletteSeed = FMath::Clamp(
                FirstPartyWaterPaletteCell * FirstPartyWaterCellularFacetGain +
                    FirstPartyWaterPaletteBandSeed * (1.0f - FirstPartyWaterCellularFacetGain),
                0.0f,
                1.0f);
            const FLinearColor FirstPartyWaterSedimentReflection = Spec.bDesertCanyon
                ? FLinearColor(0.630f, 0.415f, 0.225f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.070f, 0.300f, 0.150f)
                                        : FLinearColor(0.165f, 0.355f, 0.235f));
            const FLinearColor FirstPartyWaterSkyReflection = Spec.bDesertCanyon
                ? FLinearColor(0.360f, 0.545f, 0.625f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.235f, 0.565f, 0.485f)
                                        : FLinearColor(0.320f, 0.615f, 0.545f));
            const FLinearColor FirstPartyWaterDeepPocket = Spec.bDesertCanyon
                ? FLinearColor(0.235f, 0.285f, 0.330f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.018f, 0.175f, 0.095f)
                                        : FLinearColor(0.035f, 0.215f, 0.135f));
            const FLinearColor FirstPartyWaterAeration = Spec.bDesertCanyon
                ? FLinearColor(0.835f, 0.785f, 0.610f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.590f, 0.810f, 0.630f)
                                        : FLinearColor(0.650f, 0.805f, 0.660f));
            const FLinearColor FirstPartyWaterPaletteColor = FirstPartyWaterPaletteSeed < 0.24f
                ? FirstPartyWaterDeepPocket
                : (FirstPartyWaterPaletteSeed < 0.50f
                       ? FirstPartyWaterSedimentReflection
                       : (FirstPartyWaterPaletteSeed < 0.76f ? FirstPartyWaterSkyReflection : FirstPartyWaterAeration));
            WaterColor = FMath::Lerp(
                WaterColor,
                FirstPartyWaterPaletteColor,
                FMath::Clamp(
                    FirstPartyCaptureQualityWaterTextureMottleT *
                        (Spec.bDesertCanyon ? 0.46f : 0.38f) *
                        (0.74f + CenterT * 0.18f + EdgeT * 0.08f),
                    0.0f,
                    Spec.bDesertCanyon ? 0.42f : 0.36f));
            const float FirstPartyWaterLongBandNoise = FMath::Clamp(
                0.50f +
                    0.34f * FMath::Sin(X * 0.0060f + Lateral * 0.0105f + FlowEnergy * 0.27f) +
                    0.24f * FMath::Sin(X * 0.0145f - Lateral * 0.0065f) +
                    0.15f * FMath::Sin(X * 0.0310f + Lateral * 0.0190f),
                0.0f,
                1.0f);
            const FLinearColor FirstPartyWaterLongReflectionA = Spec.bDesertCanyon
                ? FLinearColor(0.710f, 0.450f, 0.245f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.050f, 0.355f, 0.175f)
                                        : FLinearColor(0.115f, 0.405f, 0.255f));
            const FLinearColor FirstPartyWaterLongReflectionB = Spec.bDesertCanyon
                ? FLinearColor(0.260f, 0.420f, 0.505f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.195f, 0.585f, 0.460f)
                                        : FLinearColor(0.255f, 0.585f, 0.505f));
            const FLinearColor FirstPartyWaterLongReflectionC = Spec.bDesertCanyon
                ? FLinearColor(0.835f, 0.720f, 0.445f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.455f, 0.760f, 0.455f)
                                        : FLinearColor(0.540f, 0.750f, 0.520f));
            const FLinearColor FirstPartyWaterLongReflectionColor = FirstPartyWaterLongBandNoise < 0.34f
                ? FirstPartyWaterLongReflectionA
                : (FirstPartyWaterLongBandNoise < 0.68f ? FirstPartyWaterLongReflectionB : FirstPartyWaterLongReflectionC);
            WaterColor = FMath::Lerp(
                WaterColor,
                FirstPartyWaterLongReflectionColor,
                FMath::Clamp(
                    SmoothPreviewStep(0.12f, 0.88f, FMath::Abs(FirstPartyWaterLongBandNoise - 0.5f) * 2.0f) *
                        (0.18f + CenterT * 0.16f + EdgeT * 0.08f) *
                        FirstPartyWaterColorFacetGain *
                        (Spec.bDesertCanyon ? 1.08f : 0.92f),
                    0.0f,
                    Spec.bDesertCanyon ? 0.44f : 0.36f));
            const float IntegratedWaterShaderChromaCell = FMath::Frac(
                FMath::Sin(static_cast<float>((XIndex + 313) * 601 + (CrossIndex + 173) * 887) * 12.9898f) *
                43758.5453f);
            const float IntegratedWaterShaderChromaThread = FMath::Clamp(
                0.50f +
                    0.32f * FMath::Sin(X * 0.0185f + Lateral * 0.0225f + FlowEnergy * 0.41f) +
                    0.24f * FMath::Sin(X * 0.0520f - Lateral * 0.0310f + EdgeT * 0.73f) +
                    0.12f * FMath::Sin(X * 0.0910f + Lateral * 0.0740f),
                0.0f,
                1.0f);
            const float IntegratedWaterShaderChromaNoise = FMath::Clamp(
                IntegratedWaterShaderChromaCell * (FirstPartyWaterCellularFacetGain * 0.82f) +
                    IntegratedWaterShaderChromaThread * (1.0f - FirstPartyWaterCellularFacetGain * 0.82f),
                0.0f,
                1.0f);
            const float IntegratedWaterShaderChromaT = FMath::Clamp(
                (0.32f + CenterT * 0.44f + EdgeT * 0.30f) *
                    (0.88f + FlowEnergy * 0.18f) *
                    FirstPartyWaterColorFacetGain *
                    (1.0f - BaseWaterResidualCenterSeamEraseT * 0.06f),
                0.0f,
                Spec.bDesertCanyon ? 0.86f : 0.80f);
            const FLinearColor IntegratedWaterShaderDeep = Spec.bDesertCanyon
                ? FLinearColor(0.185f, 0.285f, 0.370f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.012f, 0.160f, 0.080f)
                                        : FLinearColor(0.030f, 0.205f, 0.130f));
            const FLinearColor IntegratedWaterShaderBank = Spec.bDesertCanyon
                ? FLinearColor(0.700f, 0.405f, 0.200f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.065f, 0.345f, 0.130f)
                                        : FLinearColor(0.225f, 0.415f, 0.215f));
            const FLinearColor IntegratedWaterShaderSky = Spec.bDesertCanyon
                ? FLinearColor(0.300f, 0.555f, 0.700f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.235f, 0.610f, 0.505f)
                                        : FLinearColor(0.335f, 0.660f, 0.555f));
            const FLinearColor IntegratedWaterShaderAeration = Spec.bDesertCanyon
                ? FLinearColor(0.850f, 0.750f, 0.500f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.610f, 0.825f, 0.625f)
                                        : FLinearColor(0.675f, 0.825f, 0.665f));
            const FLinearColor IntegratedWaterShaderChromaColor = IntegratedWaterShaderChromaNoise < 0.24f
                ? IntegratedWaterShaderDeep
                : (IntegratedWaterShaderChromaNoise < 0.50f
                       ? IntegratedWaterShaderBank
                       : (IntegratedWaterShaderChromaNoise < 0.76f
                              ? IntegratedWaterShaderSky
                              : IntegratedWaterShaderAeration));
            WaterColor = FMath::Lerp(
                WaterColor,
                IntegratedWaterShaderChromaColor,
                FMath::Clamp(
                    IntegratedWaterShaderChromaT *
                        (Spec.bDesertCanyon ? 0.54f : (Spec.bHasWaterfalls ? 0.46f : 0.50f)) *
                        (0.76f + CenterT * 0.18f + EdgeT * 0.12f),
                    0.0f,
                    Spec.bDesertCanyon ? 0.48f : 0.44f));
            const float BaseWaterEdgeRailArtifactDemotion = SmoothPreviewStep(0.84f, 0.995f, EdgeT);
            const FLinearColor BaseWaterEdgeRailMutedColor = FMath::Lerp(
                Spec.WaterColor,
                ShallowWater,
                Spec.bDesertCanyon ? 0.18f : (Spec.bHasWaterfalls ? 0.12f : 0.14f));
            WaterColor = FMath::Lerp(
                WaterColor,
                BaseWaterEdgeRailMutedColor,
                FMath::Clamp(
                    BaseWaterEdgeRailArtifactDemotion *
                        (Spec.bDesertCanyon ? 0.58f : (Spec.bHasWaterfalls ? 0.66f : 0.62f)),
                    0.0f,
                    Spec.bHasWaterfalls ? 0.70f : 0.64f));
            const float BaseWaterEdgeRailLumaCeiling =
                Spec.bDesertCanyon ? 0.52f : (Spec.bHasWaterfalls ? 0.36f : 0.39f);
            const float BaseWaterEdgeRailLuma = GetPreviewColorLuma(WaterColor);
            if (BaseWaterEdgeRailLuma > BaseWaterEdgeRailLumaCeiling)
            {
                const float LumaScale = BaseWaterEdgeRailLumaCeiling / FMath::Max(BaseWaterEdgeRailLuma, 0.001f);
                WaterColor = FMath::Lerp(
                    WaterColor,
                    ScalePreviewColor(WaterColor, LumaScale),
                    FMath::Clamp(BaseWaterEdgeRailArtifactDemotion * 0.86f, 0.0f, 0.86f));
            }
            WaterColor.R = FMath::Max(WaterColor.R, BaseWaterResidualDarkStreakLumaFloor.R);
            WaterColor.G = FMath::Max(WaterColor.G, BaseWaterResidualDarkStreakLumaFloor.G);
            WaterColor.B = FMath::Max(WaterColor.B, BaseWaterResidualDarkStreakLumaFloor.B);
            const float NearCameraBottomCenterWaterWedgeArtifactDemotion =
                bUsePhysicalCandidateShading ? 0.0f : 0.48f;
            const FLinearColor NearCameraBottomCenterWaterWedgeReviewFill = Spec.bDesertCanyon
                ? FLinearColor(0.560f, 0.455f, 0.300f, 1.0f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.155f, 0.420f, 0.230f, 1.0f)
                                        : FLinearColor(0.185f, 0.390f, 0.245f, 1.0f));
            const FLinearColor NearCameraBottomCenterWaterWedgeMutedColor = FMath::Lerp(
                FMath::Lerp(Spec.WaterColor, ShallowWater, Spec.bDesertCanyon ? 0.16f : 0.20f),
                NearCameraBottomCenterWaterWedgeReviewFill,
                Spec.bDesertCanyon ? 0.34f : 0.42f);
            const float NearCameraBottomCenterWaterWedgeBlendT = FMath::Clamp(
                NearCameraBottomCenterWaterWedgeDemotionT * NearCameraBottomCenterWaterWedgeArtifactDemotion,
                0.0f,
                0.98f);
            WaterColor = FMath::Lerp(WaterColor, NearCameraBottomCenterWaterWedgeMutedColor, NearCameraBottomCenterWaterWedgeBlendT);
            const float NearCameraBottomCenterWaterWedgeLumaFloor =
                Spec.bDesertCanyon ? 0.43f : (Spec.bHasWaterfalls ? 0.32f : 0.34f);
            const float NearCameraBottomCenterWaterWedgeLuma = GetPreviewColorLuma(WaterColor);
            if (NearCameraBottomCenterWaterWedgeLuma < NearCameraBottomCenterWaterWedgeLumaFloor)
            {
                const float LumaScale =
                    NearCameraBottomCenterWaterWedgeLumaFloor / FMath::Max(NearCameraBottomCenterWaterWedgeLuma, 0.001f);
                WaterColor = FMath::Lerp(
                    WaterColor,
                    ScalePreviewColor(WaterColor, LumaScale),
                    FMath::Clamp(NearCameraBottomCenterWaterWedgeBlendT * 0.95f, 0.0f, 0.95f));
            }
            const FLinearColor SolverHydraulicAerationColor(0.88f, 0.92f, 0.88f, 1.0f);
            WaterColor = FMath::Lerp(
                WaterColor,
                SolverHydraulicAerationColor,
                FMath::Clamp(
                    SolverHydraulicAerationT * CandidateWaterSettings.SolverFroudeAerationWeight,
                    0.0f,
                    0.24f));
            if (bUseSolverVisualizationFields)
            {
                const float SolverFoamNoiseA = FMath::PerlinNoise2D(FVector2D(
                    X * 0.0065f + SolverFroudeVisual * 1.7f,
                    Lateral * 0.0120f + SolverSpeedVisual * 2.3f)) * 0.5f + 0.5f;
                const float SolverFoamNoiseB = FMath::PerlinNoise2D(FVector2D(
                    X * 0.0170f - Lateral * 0.0040f + 19.7f,
                    Lateral * 0.0290f + SolverFroudeVisual * 3.1f - 7.4f)) * 0.5f + 0.5f;
                const float SolverFoamBreakupNoise = FMath::Clamp(
                    SolverFoamNoiseA * 0.68f + SolverFoamNoiseB * 0.32f,
                    0.0f,
                    1.0f);
                const float SolverFoamBreakupT = SmoothPreviewStep(0.38f, 0.74f, SolverFoamBreakupNoise);
                const float SolverFoamOpacity = FMath::Clamp(
                    SolverHydraulicAerationT * (0.16f + SolverFoamBreakupT * 0.84f) * 0.72f,
                    0.0f,
                    0.72f);
                SolverFoamVertexColors.Add(FLinearColor(0.86f, 0.91f, 0.86f, SolverFoamOpacity));
            }
            const float FineRippleWave =
                (FineRipple - 0.5f) * NearFieldFineRippleAmplitudeCm * (0.45f + CenterT * 0.55f) * NearFieldTextureGain;
            const float FlowCuedWaterMottleRippleCm =
                (FlowCuedWaterFoamSeed - 0.5f) *
                (Spec.bDesertCanyon ? 0.45f : (Spec.bHasWaterfalls ? 0.85f : 0.65f)) *
                FMath::Clamp(Spec.FlowFoamScale, 0.70f, 1.55f) *
                (0.35f + CenterT * 0.65f);
            const float BaseWaterCrossChannelReliefCm =
                (BaseWaterCrossChannelBreakupNoise - 0.5f) *
                (Spec.bDesertCanyon ? 0.90f : (Spec.bHasWaterfalls ? 1.80f : 1.40f)) *
                FMath::Clamp(0.35f + CenterT * 0.35f + EdgeT * 0.30f, 0.0f, 1.0f);
            const float BaseWaterResidualCenterSeamReliefDampingT =
                FMath::Clamp(BaseWaterResidualCenterSeamEraseT * 0.88f, 0.0f, 0.94f);
            const float NearCameraWaterMacroRippleReliefCm =
                (NearCameraWaterMacroRippleNoise - 0.5f) *
                (Spec.bDesertCanyon ? 1.35f : (Spec.bHasWaterfalls ? 3.10f : 2.45f)) *
                NearCameraWaterMacroRipplePatchT *
                NearCameraWaterMacroRippleReliefT *
                FirstPartyWaterLargeReliefGain *
                FMath::Clamp(0.55f + CenterT * 0.28f + EdgeT * 0.17f, 0.0f, 1.0f);
            const float BaseWaterFlowThreadReliefCm =
                (BaseWaterFlowThreadNoise - 0.5f) *
                (Spec.bDesertCanyon ? 1.85f : (Spec.bHasWaterfalls ? 3.80f : 3.10f)) *
                BaseWaterFlowThreadTextureT *
                FirstPartyWaterLargeReliefGain *
                FMath::Clamp(0.50f + CenterT * 0.35f + EdgeT * 0.15f, 0.0f, 1.0f);
            const float FirstPartyMaterialAtlasWaterReliefCm = GetFirstPartyMaterialAtlasMicroReliefCm(
                MaterialAtlasPacked,
                FlowDependentWaterSurfaceMaterialTile,
                U * 16.0f + FlowNoise * 0.43f,
                V * 2.7f + BaseWaterFlowThreadLongBand * 0.31f,
                Spec.bHasWaterfalls ? 2.4f : (Spec.bDesertCanyon ? 1.2f : 1.8f),
                FirstPartyMaterialAtlasWaterBlend) *
                (1.0f - BaseWaterResidualCenterSeamReliefDampingT * 0.55f);
            const float FirstPartyCaptureQualityWaterMicroReliefCm =
                (FirstPartyCaptureQualityWaterTextureNoise - 0.5f) *
                (Spec.bDesertCanyon ? 2.2f : (Spec.bHasWaterfalls ? 3.2f : 2.8f)) *
                (0.38f + FirstPartyCaptureQualityWaterTextureMottleT) *
                FirstPartyWaterMicroReliefGain *
                FMath::Clamp(0.52f + CenterT * 0.32f + EdgeT * 0.16f, 0.0f, 1.0f) *
                (1.0f - BaseWaterResidualCenterSeamReliefDampingT * 0.18f);
            const float IntegratedWaterShaderChromaReliefCm =
                (IntegratedWaterShaderChromaNoise - 0.5f) *
                (Spec.bDesertCanyon ? 2.0f : (Spec.bHasWaterfalls ? 3.0f : 2.6f)) *
                (0.34f + IntegratedWaterShaderChromaT) *
                FirstPartyWaterMicroReliefGain *
                FMath::Clamp(0.50f + CenterT * 0.30f + EdgeT * 0.20f, 0.0f, 1.0f) *
                (1.0f - BaseWaterResidualCenterSeamReliefDampingT * 0.16f);
            Vertices.Add(FVector(
                X,
                CenterY + Lateral,
                WaterBaseZ + (Wave * FirstPartyWaterBaseWaveGain +
                    FineRippleWave * FirstPartyWaterMicroReliefGain *
                        (1.0f - BaseWaterResidualCenterSeamReliefDampingT * 0.26f) +
                    FlowCuedWaterMottleRippleCm * FirstPartyWaterMicroReliefGain *
                        (1.0f - BaseWaterResidualCenterSeamReliefDampingT * 0.34f) +
                    BaseWaterCrossChannelReliefCm * FirstPartyWaterLargeReliefGain *
                        (1.0f - BaseWaterResidualCenterSeamReliefDampingT) +
                    NearCameraWaterMacroRippleReliefCm *
                        (1.0f - BaseWaterResidualCenterSeamReliefDampingT * 0.22f) *
                        (1.0f - NearCameraBottomCenterWaterWedgeBlendT * 0.72f) +
                    BaseWaterFlowThreadReliefCm *
                        (1.0f - BaseWaterResidualCenterSeamReliefDampingT * 0.18f) +
                    FirstPartyCaptureQualityWaterMicroReliefCm +
                    IntegratedWaterShaderChromaReliefCm +
                    FirstPartyMaterialAtlasWaterReliefCm) *
                    (bUsePhysicalCandidateShading ? CandidateWaterSettings.RenderDisplacementScale : 1.0f) *
                    (bUseSolverVisualizationFields ? 0.42f : 1.0f) +
                    SolverSurfaceReliefCm));
            UVs.Add(FVector2D(U * 18.0f, V));
            VertexColors.Add(ClampPreviewColor(WaterColor));
        }
    }

    const int32 RowSize = CrossSteps + 1;
    for (int32 XIndex = 0; XIndex < XSteps; ++XIndex)
    {
        for (int32 CrossIndex = 0; CrossIndex < CrossSteps; ++CrossIndex)
        {
            const int32 A = XIndex * RowSize + CrossIndex;
            const int32 B = A + 1;
            const int32 C = (XIndex + 1) * RowSize + CrossIndex;
            const int32 D = C + 1;
            Triangles.Add(A);
            Triangles.Add(C);
            Triangles.Add(B);
            Triangles.Add(B);
            Triangles.Add(C);
            Triangles.Add(D);
        }
    }
    Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    const FRaftSimPreviewWaterMaterialResponse WaterResponse = GetPreviewWaterMaterialResponse(Spec.RiverId);
    const float MeshNormalUpBlend = bUsePhysicalCandidateShading
        ? CandidateWaterSettings.RenderNormalUpBlend
        : WaterResponse.MeshNormalUpBlend;
    for (FVector& Normal : Normals)
    {
        Normal = FMath::Lerp(Normal, FVector::UpVector, MeshNormalUpBlend).GetSafeNormal();
    }

    AActor* WaterActor = AddPreviewProceduralMeshActor(
        World,
        FString::Printf(TEXT("RaftSim_ProceduralRiverRibbon_%s"), *Spec.RiverId),
        Vertices,
        Triangles,
        Normals,
        UVs,
        Spec.WaterColor,
        MaterialOverride ? MaterialOverride : LoadOrCreatePreviewWaterVertexColorMaterial(),
        &VertexColors,
        !bUsePhysicalCandidateShading);
    if (bUseSolverVisualizationFields && SolverFoamVertexColors.Num() == Vertices.Num())
    {
        TArray<FVector> SolverFoamVertices = Vertices;
        for (int32 VertexIndex = 0; VertexIndex < SolverFoamVertices.Num(); ++VertexIndex)
        {
            SolverFoamVertices[VertexIndex] += Normals[VertexIndex] * 1.4f;
        }
        AddPreviewProceduralMeshActor(
            World,
            FString::Printf(TEXT("RaftSim_SolverFieldFoam_%s"), *Spec.RiverId),
            SolverFoamVertices,
            Triangles,
            Normals,
            UVs,
            FLinearColor(0.86f, 0.91f, 0.86f, 0.0f),
            SolverFoamMaterial,
            &SolverFoamVertexColors,
            false);
    }
    return WaterActor;
}

void AddPreviewShoreRibbon(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FString& Label,
    float SignedCenterOffset,
    float Width,
    float ZOffset,
    const FLinearColor& InnerColor,
    const FLinearColor& OuterColor)
{
    if (!World)
    {
        return;
    }

    constexpr int32 Segments = 72;
    constexpr int32 CrossSteps = 3;
    const float PaleShorelineSlashArtifactDemotion = 0.46f;
    const float GraphicWaterlineRibbonDemotion = 0.16f;
    const float WaterlineRailArtifactDemotion = 0.24f;
    const float MinX = -5520.0f;
    const float MaxX = 26000.0f;
    const float Side = SignedCenterOffset < 0.0f ? -1.0f : 1.0f;

    TArray<FVector> Vertices;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve((Segments + 1) * (CrossSteps + 1));
    Normals.Reserve((Segments + 1) * (CrossSteps + 1));
    UVs.Reserve((Segments + 1) * (CrossSteps + 1));
    VertexColors.Reserve((Segments + 1) * (CrossSteps + 1));
    Triangles.Reserve(Segments * CrossSteps * 6);

    for (int32 SegmentIndex = 0; SegmentIndex <= Segments; ++SegmentIndex)
    {
        const float U = static_cast<float>(SegmentIndex) / static_cast<float>(Segments);
        const float X = FMath::Lerp(MinX, MaxX, U);
        const float CenterY = GetPreviewRiverCenterY(Spec, X);
        for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
        {
            const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
            const float Breakup = FMath::Clamp(
                0.50f + 0.34f * FMath::Sin(X * 0.0023f + SignedCenterOffset * 0.0061f) +
                    0.16f * FMath::Sin(X * 0.0067f - SignedCenterOffset * 0.0029f),
                0.0f,
                1.0f);
            const float RibbonContinuityBreakupT = FMath::Clamp(
                0.50f + 0.34f * FMath::Sin(X * 0.011f + SignedCenterOffset * 0.0047f) +
                    0.16f * FMath::Sin(X * 0.019f - SignedCenterOffset * 0.0023f),
                0.0f,
                1.0f);
            const float SegmentFade =
                SmoothPreviewStep(0.34f, 0.80f, Breakup) *
                SmoothPreviewStep(0.28f, 0.72f, RibbonContinuityBreakupT);
            const float NearFrameShorelineRibbonDemotion = SmoothPreviewStep(7600.0f, 13600.0f, X);
            const float LocalWidthScale =
                (0.035f + 0.095f * SegmentFade) *
                FMath::Lerp(0.07f, 0.28f, NearFrameShorelineRibbonDemotion) *
                PaleShorelineSlashArtifactDemotion *
                GraphicWaterlineRibbonDemotion *
                WaterlineRailArtifactDemotion;
            const float Offset = SignedCenterOffset + Side * Width * LocalWidthScale * (V - 0.5f);
            const float Y = CenterY + Offset;
            const float SurfaceWave = FMath::Sin(X * 0.011f + Y * 0.015f) * (Spec.bDesertCanyon ? 2.0f : 4.5f);
            const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
            const float Z = FMath::Max(TerrainZ + ZOffset, GetPreviewWaterSurfaceBaseZCm(Spec) + 3.0f + SurfaceWave + ZOffset * 0.25f);
            const float Fleck = 0.95f + 0.04f * FMath::Sin(X * 0.0053f + Y * 0.0037f);
            const FLinearColor TerrainBase = GetPreviewSoftTerrainPatchFeatherBaseColor(
                Spec,
                X,
                Y,
                SignedCenterOffset * 0.013f);
            const FLinearColor RibbonColor = NormalizePreviewTerrainProxyPatchColor(
                Spec,
                ScalePreviewColor(FMath::Lerp(InnerColor, OuterColor, V), Fleck));
            Vertices.Add(FVector(X, Y, Z));
            UVs.Add(FVector2D(U * 16.0f, V));
            VertexColors.Add(ClampPreviewColor(FMath::Lerp(
		                TerrainBase,
		                RibbonColor,
		                SegmentFade *
		                    FMath::Lerp(0.002f, 0.012f, NearFrameShorelineRibbonDemotion) *
		                    PaleShorelineSlashArtifactDemotion *
		                    GraphicWaterlineRibbonDemotion *
		                    WaterlineRailArtifactDemotion)));
        }
    }

    const int32 RowSize = CrossSteps + 1;
    for (int32 SegmentIndex = 0; SegmentIndex < Segments; ++SegmentIndex)
    {
        for (int32 CrossIndex = 0; CrossIndex < CrossSteps; ++CrossIndex)
        {
            const int32 A = SegmentIndex * RowSize + CrossIndex;
            const int32 B = A + 1;
            const int32 C = (SegmentIndex + 1) * RowSize + CrossIndex;
            const int32 D = C + 1;
            Triangles.Add(A);
            Triangles.Add(C);
            Triangles.Add(B);
            Triangles.Add(B);
            Triangles.Add(C);
            Triangles.Add(D);
        }
    }

    Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    SoftenPreviewTerrainNormals(Normals, GetPreviewTerrainNormalSofteningBlend(Spec));
    AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        InnerColor,
        LoadOrCreatePreviewTerrainVertexColorMaterial(),
        &VertexColors);
}

void AddPreviewWetBankDressing(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview)
{
    if (!World)
    {
        return;
    }

    const FLinearColor WetEdge = Spec.bDesertCanyon
        ? FLinearColor(0.18f, 0.14f, 0.105f)
        : FMath::Lerp(ScalePreviewColor(Spec.WaterColor, 0.30f), ScalePreviewColor(Spec.RockColor, 0.40f), 0.48f);
    const FLinearColor BankBand = Spec.bDesertCanyon
        ? FLinearColor(0.34f, 0.24f, 0.17f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.035f, 0.075f, 0.045f) : FLinearColor(0.13f, 0.14f, 0.11f));
    const FLinearColor GravelBand = Spec.bDesertCanyon
        ? FLinearColor(0.45f, 0.32f, 0.22f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.052f, 0.095f, 0.058f) : FLinearColor(0.17f, 0.17f, 0.13f));
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float WetBankScale = FMath::Max(0.35f, Spec.FlowWetBankScale);

    for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
    {
        const float Side = SideIndex == 0 ? -1.0f : 1.0f;
        AddPreviewShoreRibbon(
            World,
            Spec,
            TerrainRelief,
            HeightfieldPreview,
            FString::Printf(TEXT("RaftSim_WetWaterline_%s_%s"), Side < 0.0f ? TEXT("Left") : TEXT("Right"), *Spec.RiverId),
            Side * (ActiveRiverHalfWidth + 66.0f * WetBankScale),
            (Spec.bDesertCanyon ? 44.0f : 32.0f) * WetBankScale,
            7.0f,
            WetEdge,
            BankBand);
        AddPreviewShoreRibbon(
            World,
            Spec,
            TerrainRelief,
            HeightfieldPreview,
            FString::Printf(TEXT("RaftSim_GravelMudBank_%s_%s"), Side < 0.0f ? TEXT("Left") : TEXT("Right"), *Spec.RiverId),
            Side * (ActiveRiverHalfWidth + 176.0f * WetBankScale),
            (Spec.bDesertCanyon ? 52.0f : 38.0f) * WetBankScale,
            8.0f,
            BankBand,
            GravelBand);
    }
}

void AddPreviewBankBreakupPatch(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FString& Label,
    float StartX,
    float Length,
    float SignedCenterOffset,
    float Width,
    float Phase,
    const FLinearColor& InnerColor,
    const FLinearColor& OuterColor,
    float ZOffset,
    bool bClampAboveWaterSurface)
{
    if (!World)
    {
        return;
    }

    constexpr int32 Segments = 16;
    constexpr int32 CrossSteps = 6;
    TArray<FVector> Vertices;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve((Segments + 1) * (CrossSteps + 1));
    Normals.Reserve((Segments + 1) * (CrossSteps + 1));
    UVs.Reserve((Segments + 1) * (CrossSteps + 1));
    VertexColors.Reserve((Segments + 1) * (CrossSteps + 1));
    Triangles.Reserve(Segments * CrossSteps * 6);

    const float Side = SignedCenterOffset < 0.0f ? -1.0f : 1.0f;
    for (int32 SegmentIndex = 0; SegmentIndex <= Segments; ++SegmentIndex)
    {
        const float U = static_cast<float>(SegmentIndex) / static_cast<float>(Segments);
        const float X = StartX + Length * U;
        const float RiverCenterY = GetPreviewRiverCenterY(Spec, X);
        const float LongitudinalTaper = FMath::Sin(U * PI);
        for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
        {
            const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
            const float CrossCenterT = 1.0f - FMath::Clamp(FMath::Abs(V - 0.5f) * 2.0f, 0.0f, 1.0f);
            const float EdgeT = 1.0f - CrossCenterT;
            const float PatchCoverage = GetPreviewSoftTerrainPatchCoverage(U, V, Phase);
            const float Cross =
                (V - 0.5f) * Width * (0.45f + 0.55f * LongitudinalTaper) +
                FMath::Sin(Phase * 1.17f + U * 8.3f + V * 5.1f) * Width * 0.035f * EdgeT;
            const float Sway =
                FMath::Sin(Phase + U * UE_TWO_PI) * Width * 0.18f +
                FMath::Sin(Phase * 0.37f + U * UE_TWO_PI * 2.0f) * Width * 0.07f;
            const float Y = RiverCenterY + SignedCenterOffset + Side * Sway + Cross;
            const float ZFeather = 0.42f + 0.58f * PatchCoverage;
            const float TerrainPatchZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview) +
                FMath::Max(Spec.bDesertCanyon ? 8.0f : 5.0f, ZOffset * ZFeather);
            const float Z = bClampAboveWaterSurface
                ? FMath::Max(TerrainPatchZ, GetPreviewWaterSurfaceBaseZCm(Spec) + 6.0f + ZOffset * 0.30f)
                : TerrainPatchZ;
            const float Fleck = FMath::Clamp(
                0.86f + 0.10f * FMath::Sin(Phase + U * 5.7f) + 0.06f * FMath::Sin(Phase * 0.71f + V * 4.3f),
                0.68f,
                1.04f);
            Vertices.Add(FVector(X, Y, Z));
            UVs.Add(FVector2D(U * 4.5f, V));
            const FLinearColor FeatureColor = NormalizePreviewTerrainProxyPatchColor(
                Spec,
                ScalePreviewColor(FMath::Lerp(InnerColor, OuterColor, V), Fleck));
            VertexColors.Add(BlendPreviewSoftTerrainPatchColor(Spec, FeatureColor, X, Y, U, V, Phase, PatchCoverage));
        }
    }

    const int32 RowSize = CrossSteps + 1;
    for (int32 SegmentIndex = 0; SegmentIndex < Segments; ++SegmentIndex)
    {
        for (int32 CrossIndex = 0; CrossIndex < CrossSteps; ++CrossIndex)
        {
            const int32 A = SegmentIndex * RowSize + CrossIndex;
            const int32 B = A + 1;
            const int32 C = (SegmentIndex + 1) * RowSize + CrossIndex;
            const int32 D = C + 1;
            Triangles.Add(A);
            Triangles.Add(C);
            Triangles.Add(B);
            Triangles.Add(B);
            Triangles.Add(C);
            Triangles.Add(D);
        }
    }

    Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    SoftenPreviewTerrainNormals(Normals, GetPreviewTerrainNormalSofteningBlend(Spec));
    AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        InnerColor,
        LoadOrCreatePreviewTerrainVertexColorMaterial(),
        &VertexColors);
}

void AddPreviewIrregularShorelineEdgeBreakupDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask)
{
    if (!World)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float WetBankScale = FMath::Max(0.35f, Spec.FlowWetBankScale);
    const int32 PatchCount = Spec.bDesertCanyon ? 58 : (Spec.bHasWaterfalls ? 86 : 72);
    const FLinearColor WetShadowColor = Spec.bDesertCanyon
        ? FLinearColor(0.25f, 0.19f, 0.13f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.014f, 0.045f, 0.030f) : FLinearColor(0.070f, 0.100f, 0.080f));
    const FLinearColor BankDepositColor = Spec.bDesertCanyon
        ? FLinearColor(0.50f, 0.35f, 0.22f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.045f, 0.105f, 0.050f) : FLinearColor(0.19f, 0.18f, 0.135f));
    const FLinearColor FreshEdgeColor = Spec.bDesertCanyon
        ? FLinearColor(0.58f, 0.42f, 0.27f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.060f, 0.135f, 0.060f) : FLinearColor(0.24f, 0.22f, 0.16f));

    for (int32 PatchIndex = 0; PatchIndex < PatchCount; ++PatchIndex)
    {
        const float SequenceT = static_cast<float>(PatchIndex) / static_cast<float>(FMath::Max(1, PatchCount - 1));
        const float Side = (PatchIndex % 2 == 0) ? -1.0f : 1.0f;
        const float Phase = static_cast<float>(PatchIndex) * 0.791f + (Spec.bDesertCanyon ? 0.41f : 0.0f);
        const float BaseX = FMath::Lerp(-5100.0f, 25200.0f, FMath::Frac(0.037f + SequenceT * 0.94f)) +
            160.0f * FMath::Sin(Phase * 1.47f);
        float X = BaseX;
        float SignedOffset = Side * (ActiveRiverHalfWidth + 58.0f * WetBankScale);
        float BestScore = -1000.0f;

        for (int32 CandidateIndex = 0; CandidateIndex < 5; ++CandidateIndex)
        {
            const float CandidateX = BaseX +
                85.0f * FMath::Sin(Phase * 0.83f + static_cast<float>(CandidateIndex) * 1.17f);
            const float CandidateOffset = ActiveRiverHalfWidth + WetBankScale *
                (18.0f + 26.0f * static_cast<float>(CandidateIndex) +
                 34.0f * FMath::Abs(FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 0.61f)));
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
            const float EdgePreference = 1.0f -
                FMath::Clamp(
                    FMath::Abs(CandidateOffset - (ActiveRiverHalfWidth + 70.0f * WetBankScale)) /
                        FMath::Max(1.0f, 155.0f * WetBankScale),
                    0.0f,
                    1.0f);
            const float Score = EdgePreference * 1.25f + WaterT * 0.28f -
                VegetationT * (Spec.bDesertCanyon ? 0.12f : 0.34f) +
                0.05f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.9f);
            if (Score > BestScore)
            {
                BestScore = Score;
                X = CandidateX;
                SignedOffset = Side * CandidateOffset;
            }
        }

        const bool bDepositPatch = (PatchIndex % 5) == 0;
        const FLinearColor InnerColor = bDepositPatch
            ? FMath::Lerp(WetShadowColor, BankDepositColor, Spec.bDesertCanyon ? 0.42f : 0.34f)
            : WetShadowColor;
        const FLinearColor OuterColor = bDepositPatch
            ? FMath::Lerp(BankDepositColor, FreshEdgeColor, 0.46f)
            : FMath::Lerp(WetShadowColor, FreshEdgeColor, Spec.bHasWaterfalls ? 0.28f : 0.34f);
        const float Length = (Spec.bDesertCanyon ? 780.0f : (Spec.bHasWaterfalls ? 520.0f : 620.0f)) *
            (0.68f + 0.11f * static_cast<float>(PatchIndex % 6));
        const float Width = (Spec.bDesertCanyon ? 118.0f : (Spec.bHasWaterfalls ? 82.0f : 94.0f)) *
            (0.78f + 0.10f * static_cast<float>(PatchIndex % 5)) * WetBankScale;

        AddPreviewBankBreakupPatch(
            World,
            Spec,
            TerrainRelief,
            HeightfieldPreview,
            FString::Printf(TEXT("RaftSim_IrregularShorelineEdgeBreakup_%03d_%s"), PatchIndex, *Spec.RiverId),
            X - Length * 0.48f,
            Length,
            SignedOffset,
            Width,
            Phase,
            InnerColor,
            OuterColor,
            Spec.bDesertCanyon ? 15.0f : 12.0f,
            true);
    }
}

void AddPreviewTerrainErosionRillActor(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FString& Label,
    float StartX,
    float Side,
    float InnerOffset,
    float RillLength,
    float Width,
    float Phase,
    const FLinearColor& CenterColor,
    const FLinearColor& RimColor)
{
    if (!World)
    {
        return;
    }

    constexpr int32 Segments = 12;
    constexpr int32 CrossSteps = 2;
    TArray<FVector> Vertices;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve((Segments + 1) * (CrossSteps + 1));
    Normals.Reserve((Segments + 1) * (CrossSteps + 1));
    UVs.Reserve((Segments + 1) * (CrossSteps + 1));
    VertexColors.Reserve((Segments + 1) * (CrossSteps + 1));
    Triangles.Reserve(Segments * CrossSteps * 6);

    for (int32 SegmentIndex = 0; SegmentIndex <= Segments; ++SegmentIndex)
    {
        const float U = static_cast<float>(SegmentIndex) / static_cast<float>(Segments);
        const float LongTaper = FMath::Sin(U * PI);
        const float Offset = InnerOffset + RillLength * U;
        const float X =
            StartX +
            FMath::Sin(Phase + U * UE_TWO_PI * 1.30f) * Width * 0.68f +
            FMath::Sin(Phase * 0.37f + U * UE_TWO_PI * 2.40f) * Width * 0.26f;
        const float RiverCenterY = GetPreviewRiverCenterY(Spec, X);
        const float CenterY = RiverCenterY + Side * Offset;
        for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
        {
            const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
            const float CenterT = 1.0f - FMath::Clamp(FMath::Abs(V - 0.5f) * 2.0f, 0.0f, 1.0f);
            const float Cross = (V - 0.5f) * Width * (0.46f + 0.54f * LongTaper);
            const float Y = CenterY + Side * 5.0f * FMath::Sin(Phase + U * 4.1f + V * 2.3f);
            const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X + Cross, Y, TerrainRelief, HeightfieldPreview);
            const float Incision =
                CenterT * (Spec.bDesertCanyon ? -5.0f : -3.0f) + (1.0f - CenterT) * (Spec.bDesertCanyon ? 9.0f : 6.0f);
            const float Lift = (Spec.bDesertCanyon ? 16.0f : 11.0f) + Incision;
            const float Fleck = FMath::Clamp(
                0.84f + 0.10f * FMath::Sin(Phase + U * 5.3f) + 0.06f * FMath::Sin(Phase * 0.73f + V * 4.7f),
                0.66f,
                1.04f);
            Vertices.Add(FVector(X + Cross, Y, TerrainZ + Lift));
            UVs.Add(FVector2D(U * 5.0f, V));
            const FLinearColor RillColor = FMath::Lerp(RimColor, CenterColor, CenterT);
            VertexColors.Add(NormalizePreviewTerrainProxyPatchColor(Spec, ScalePreviewColor(RillColor, Fleck)));
        }
    }

    const int32 RowSize = CrossSteps + 1;
    for (int32 SegmentIndex = 0; SegmentIndex < Segments; ++SegmentIndex)
    {
        for (int32 CrossIndex = 0; CrossIndex < CrossSteps; ++CrossIndex)
        {
            const int32 A = SegmentIndex * RowSize + CrossIndex;
            const int32 B = A + 1;
            const int32 C = (SegmentIndex + 1) * RowSize + CrossIndex;
            const int32 D = C + 1;
            Triangles.Add(A);
            Triangles.Add(C);
            Triangles.Add(B);
            Triangles.Add(B);
            Triangles.Add(C);
            Triangles.Add(D);
        }
    }

    Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    SoftenPreviewTerrainNormals(Normals, GetPreviewTerrainNormalSofteningBlend(Spec));
    AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        CenterColor,
        LoadOrCreatePreviewTerrainVertexColorMaterial(),
        &VertexColors);
}

void AddPreviewTerrainErosionRillDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask)
{
    if (!World)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const int32 RillCount = Spec.bDesertCanyon ? 30 : (Spec.bHasWaterfalls ? 34 : 30);
    const float InnerOffset = ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 760.0f : 420.0f);
    const float RillLength = Spec.bDesertCanyon ? 760.0f : (Spec.bHasWaterfalls ? 460.0f : 520.0f);
    const FLinearColor CenterShadow = Spec.bDesertCanyon
        ? FLinearColor(0.21f, 0.15f, 0.10f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.014f, 0.038f, 0.026f) : FLinearColor(0.095f, 0.105f, 0.078f));
    const FLinearColor RimDeposit = Spec.bDesertCanyon
        ? FLinearColor(0.54f, 0.39f, 0.24f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.055f, 0.125f, 0.058f) : FLinearColor(0.24f, 0.22f, 0.15f));

    for (int32 RillIndex = 0; RillIndex < RillCount; ++RillIndex)
    {
        const float SequenceT = static_cast<float>(RillIndex) / static_cast<float>(FMath::Max(1, RillCount - 1));
        const float Side = (RillIndex % 2 == 0) ? -1.0f : 1.0f;
        const float Phase = static_cast<float>(RillIndex) * 1.217f;
        const float BaseX = FMath::Lerp(-4700.0f, 25000.0f, SequenceT) +
            210.0f * FMath::Sin(Phase * 0.71f) +
            95.0f * FMath::Sin(Phase * 1.31f);
        float X = BaseX;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 4; ++CandidateIndex)
        {
            const float CandidateX = BaseX + 190.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.41f);
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * (InnerOffset + RillLength * 0.52f);
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
            const float Score = Spec.bDesertCanyon
                ? (1.0f - VegetationT) * 0.52f + (1.0f - WaterT) * 0.32f
                : VegetationT * (Spec.bHasWaterfalls ? 0.52f : 0.34f) + (1.0f - WaterT) * 0.26f;
            if (Score > BestScore)
            {
                BestScore = Score;
                X = CandidateX;
            }
        }

        const float Width = (Spec.bDesertCanyon ? 42.0f : (Spec.bHasWaterfalls ? 30.0f : 34.0f)) *
            (0.66f + 0.07f * static_cast<float>(RillIndex % 5));
        const FLinearColor LocalCenter = FMath::Lerp(
            CenterShadow,
            ScalePreviewColor(Spec.WaterColor, Spec.bDesertCanyon ? 0.34f : 0.28f),
            Spec.bDesertCanyon ? 0.10f : 0.18f);
        const FLinearColor LocalRim = FMath::Lerp(
            RimDeposit,
            ScalePreviewColor(Spec.FoliageColor, Spec.bHasWaterfalls ? 0.40f : 0.22f),
            Spec.bDesertCanyon ? 0.04f : 0.16f);

        AddPreviewTerrainErosionRillActor(
            World,
            Spec,
            TerrainRelief,
            HeightfieldPreview,
            FString::Printf(TEXT("RaftSim_TerrainErosionRill_%03d_%s"), RillIndex, *Spec.RiverId),
            X,
            Side,
            InnerOffset,
            RillLength * (0.72f + 0.08f * static_cast<float>(RillIndex % 4)),
            Width,
            Phase,
            LocalCenter,
            LocalRim);
    }
}

void AddPreviewSourceAwareBankBreakupDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask)
{
    if (!World)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const int32 PatchCount = Spec.bDesertCanyon ? 48 : (Spec.bHasWaterfalls ? 54 : 46);
    const float NearOffset = Spec.bDesertCanyon ? 430.0f : 190.0f;
    const float FarOffset = Spec.bDesertCanyon ? 2500.0f : (Spec.bHasWaterfalls ? 1420.0f : 1220.0f);

    for (int32 PatchIndex = 0; PatchIndex < PatchCount; ++PatchIndex)
    {
        const float Side = (PatchIndex % 2 == 0) ? -1.0f : 1.0f;
        const float T = static_cast<float>(PatchIndex) / static_cast<float>(FMath::Max(1, PatchCount - 1));
        const float Phase = static_cast<float>(PatchIndex) * 1.383f;
        const float BaseX = FMath::Lerp(-4900.0f, 25200.0f, T) +
            240.0f * FMath::Sin(Phase * 1.27f) +
            85.0f * FMath::Sin(Phase * 0.43f);
        const float BaseOffset = ActiveRiverHalfWidth + NearOffset +
            FarOffset * FMath::Pow(FMath::Abs(FMath::Sin(Phase * 0.73f)), Spec.bDesertCanyon ? 0.80f : 0.62f);
        float X = BaseX;
        float SignedOffset = Side * BaseOffset;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 5; ++CandidateIndex)
        {
            const float CandidateX = BaseX + 165.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.11f);
            const float CandidateOffset = BaseOffset +
                210.0f * FMath::Sin(Phase * 0.49f + static_cast<float>(CandidateIndex) * 0.91f);
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
            const float BankPreference =
                1.0f - FMath::Clamp(FMath::Abs(CandidateOffset - (ActiveRiverHalfWidth + NearOffset + FarOffset * 0.38f)) / FMath::Max(1.0f, FarOffset), 0.0f, 1.0f);
            const float Score = Spec.bDesertCanyon
                ? BankPreference * 0.90f + (1.0f - WaterT) * 0.28f - VegetationT * 0.18f
                : BankPreference * 0.68f + VegetationT * (Spec.bHasWaterfalls ? 0.76f : 0.46f) + WaterT * 0.18f;
            if (Score > BestScore)
            {
                BestScore = Score;
                X = CandidateX;
                SignedOffset = Side * CandidateOffset;
            }
        }

        const float MaskY = GetPreviewRiverCenterY(Spec, X) + SignedOffset;
        const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, MaskY);
        const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, X, MaskY);
        FLinearColor InnerColor;
        FLinearColor OuterColor;
        if (Spec.bDesertCanyon)
        {
            InnerColor = FMath::Lerp(FLinearColor(0.32f, 0.20f, 0.13f), FLinearColor(0.67f, 0.48f, 0.29f), 0.28f + 0.18f * FMath::Sin(Phase));
            OuterColor = FMath::Lerp(FLinearColor(0.17f, 0.13f, 0.10f), FLinearColor(0.78f, 0.59f, 0.36f), 0.36f + 0.15f * FMath::Cos(Phase * 0.77f));
        }
        else if (Spec.bHasWaterfalls)
        {
            InnerColor = FMath::Lerp(FLinearColor(0.018f, 0.050f, 0.028f), FLinearColor(0.08f, 0.16f, 0.07f), VegetationT);
            OuterColor = FMath::Lerp(FLinearColor(0.028f, 0.038f, 0.030f), FLinearColor(0.11f, 0.21f, 0.09f), FMath::Clamp(0.28f + VegetationT * 0.70f, 0.0f, 1.0f));
        }
        else
        {
            InnerColor = FMath::Lerp(FLinearColor(0.13f, 0.12f, 0.085f), FLinearColor(0.24f, 0.28f, 0.12f), VegetationT * 0.70f);
            OuterColor = FMath::Lerp(FLinearColor(0.20f, 0.18f, 0.13f), FLinearColor(0.31f, 0.34f, 0.16f), VegetationT * 0.55f);
        }
        const FLinearColor WetTint = FMath::Lerp(ScalePreviewColor(Spec.RockColor, 0.44f), ScalePreviewColor(Spec.WaterColor, 0.34f), 0.40f);
        InnerColor = FMath::Lerp(InnerColor, WetTint, FMath::Clamp(WaterT * 0.32f, 0.0f, 0.38f));
        OuterColor = FMath::Lerp(OuterColor, WetTint, FMath::Clamp(WaterT * 0.24f, 0.0f, 0.30f));

        AddPreviewBankBreakupPatch(
            World,
            Spec,
            TerrainRelief,
            HeightfieldPreview,
            FString::Printf(TEXT("RaftSim_SourceAwareBankBreakupPatch_%03d_%s"), PatchIndex, *Spec.RiverId),
            X - (Spec.bDesertCanyon ? 210.0f : 155.0f),
            (Spec.bDesertCanyon ? 430.0f : 310.0f) * (0.64f + 0.07f * static_cast<float>(PatchIndex % 5)),
            SignedOffset,
            (Spec.bDesertCanyon ? 88.0f : 70.0f) * (0.62f + 0.06f * static_cast<float>(PatchIndex % 4)),
            Phase,
            InnerColor,
            OuterColor,
            Spec.bDesertCanyon ? 19.0f : 16.0f);
    }
}

void AddPreviewTerrainMaterialLayerDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask)
{
    if (!World)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float PaleBankMaterialSlashDemotion = 0.68f;
    const float TerrainMaterialOverlayPlateDemotion = 0.38f;
    const int32 LayerCount = Spec.bDesertCanyon ? 26 : (Spec.bHasWaterfalls ? 28 : 24);
    const int32 BandCount = Spec.bDesertCanyon ? 3 : (Spec.bHasWaterfalls ? 3 : 2);
    const float NearOffset = Spec.bDesertCanyon ? 780.0f : (Spec.bHasWaterfalls ? 430.0f : 390.0f);
    const float BandSpacing = Spec.bDesertCanyon ? 470.0f : (Spec.bHasWaterfalls ? 285.0f : 250.0f);

    for (int32 LayerIndex = 0; LayerIndex < LayerCount; ++LayerIndex)
    {
        const float Side = (LayerIndex % 2 == 0) ? -1.0f : 1.0f;
        const int32 BandIndex = (LayerIndex / 2) % BandCount;
        const float BandT = static_cast<float>(BandIndex) / static_cast<float>(FMath::Max(1, BandCount - 1));
        const float SequenceT = static_cast<float>(LayerIndex) / static_cast<float>(FMath::Max(1, LayerCount - 1));
        const float Phase = static_cast<float>(LayerIndex) * 1.217f;
        const float BaseX = FMath::Lerp(-5200.0f, 25500.0f, SequenceT) +
            410.0f * FMath::Sin(Phase * 0.79f) +
            120.0f * FMath::Sin(Phase * 1.61f);
        const float BaseOffset = ActiveRiverHalfWidth + NearOffset + BandSpacing * static_cast<float>(BandIndex) +
            (Spec.bDesertCanyon ? 190.0f : 110.0f) * FMath::Sin(Phase * 0.53f);

        float X = BaseX;
        float SignedOffset = Side * BaseOffset;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 4; ++CandidateIndex)
        {
            const float CandidateX = BaseX + 180.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.37f);
            const float CandidateOffset = BaseOffset +
                155.0f * FMath::Sin(Phase * 0.47f + static_cast<float>(CandidateIndex) * 0.83f);
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
            const float SlopePreference = SmoothPreviewStep(
                ActiveRiverHalfWidth + NearOffset * 0.35f,
                ActiveRiverHalfWidth + NearOffset + BandSpacing * static_cast<float>(BandCount),
                CandidateOffset);
            const float Score = SlopePreference * 0.78f + (1.0f - WaterT) * 0.36f +
                (Spec.bHasWaterfalls ? VegetationT * 0.20f : -VegetationT * 0.06f) +
                0.04f * FMath::Sin(Phase + static_cast<float>(CandidateIndex));
            if (Score > BestScore)
            {
                BestScore = Score;
                X = CandidateX;
                SignedOffset = Side * CandidateOffset;
            }
        }

        const float SampleY = GetPreviewRiverCenterY(Spec, X) + SignedOffset;
        const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, SampleY);
        const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, X, SampleY);
        const float ShadowT = 0.5f + 0.5f * FMath::Sin(Phase * 0.91f);
        FLinearColor InnerColor;
        FLinearColor OuterColor;
        if (Spec.bDesertCanyon)
        {
            const FLinearColor DarkStrata = FLinearColor(0.26f, 0.18f, 0.12f);
            const FLinearColor Redwall = FLinearColor(0.46f, 0.29f, 0.18f);
            const FLinearColor SunlitSandstone = FLinearColor(0.62f, 0.47f, 0.30f);
            InnerColor = FMath::Lerp(DarkStrata, Redwall, 0.32f + BandT * 0.30f);
            OuterColor = FMath::Lerp(Redwall, SunlitSandstone, 0.18f + BandT * 0.38f);
            InnerColor = FMath::Lerp(InnerColor, DarkStrata, ShadowT * 0.12f);
        }
        else if (Spec.bHasWaterfalls)
        {
            const FLinearColor WetStone = FLinearColor(0.055f, 0.085f, 0.060f);
            const FLinearColor Moss = FLinearColor(0.060f, 0.165f, 0.070f);
            const FLinearColor LeafHumus = FLinearColor(0.085f, 0.100f, 0.060f);
            InnerColor = FMath::Lerp(WetStone, Moss, FMath::Clamp(0.18f + VegetationT * 0.48f, 0.0f, 0.76f));
            OuterColor = FMath::Lerp(LeafHumus, Moss, FMath::Clamp(0.22f + VegetationT * 0.38f + BandT * 0.12f, 0.0f, 0.74f));
            InnerColor = FMath::Lerp(InnerColor, ScalePreviewColor(Spec.WaterColor, 0.34f), FMath::Clamp(WaterT * 0.22f, 0.0f, 0.30f));
        }
        else
        {
            const FLinearColor GraniteShadow = FLinearColor(0.20f, 0.20f, 0.16f);
            const FLinearColor DryGrass = FLinearColor(0.30f, 0.28f, 0.18f);
            const FLinearColor FoothillSoil = FLinearColor(0.25f, 0.22f, 0.15f);
            InnerColor = FMath::Lerp(GraniteShadow, FoothillSoil, 0.28f + BandT * 0.22f);
            OuterColor = FMath::Lerp(FoothillSoil, DryGrass, FMath::Clamp(0.16f + VegetationT * 0.28f + BandT * 0.12f, 0.0f, 0.64f));
            InnerColor = FMath::Lerp(InnerColor, ScalePreviewColor(Spec.RockColor, 0.54f), ShadowT * 0.10f);
        }

        const FLinearColor WetTint = FMath::Lerp(ScalePreviewColor(Spec.RockColor, 0.42f), ScalePreviewColor(Spec.WaterColor, 0.32f), 0.36f);
        InnerColor = FMath::Lerp(InnerColor, WetTint, FMath::Clamp(WaterT * 0.18f, 0.0f, 0.24f));
        OuterColor = FMath::Lerp(OuterColor, WetTint, FMath::Clamp(WaterT * 0.12f, 0.0f, 0.18f));
        InnerColor = FMath::Lerp(Spec.TerrainColor, InnerColor, TerrainMaterialOverlayPlateDemotion);
        OuterColor = FMath::Lerp(Spec.TerrainColor, OuterColor, TerrainMaterialOverlayPlateDemotion);

        const float Length = (Spec.bDesertCanyon ? 400.0f : (Spec.bHasWaterfalls ? 285.0f : 260.0f)) *
            (0.56f + 0.06f * static_cast<float>(LayerIndex % 5)) *
            TerrainMaterialOverlayPlateDemotion *
            PaleBankMaterialSlashDemotion;
        const float Width = (Spec.bDesertCanyon ? 84.0f : (Spec.bHasWaterfalls ? 58.0f : 54.0f)) *
            (0.56f + 0.05f * static_cast<float>(LayerIndex % 4)) *
            TerrainMaterialOverlayPlateDemotion *
            PaleBankMaterialSlashDemotion;
        AddPreviewBankBreakupPatch(
            World,
            Spec,
            TerrainRelief,
            HeightfieldPreview,
            FString::Printf(TEXT("RaftSim_TerrainMaterialLayerFacet_%03d_%s"), LayerIndex, *Spec.RiverId),
            X - Length * 0.50f,
            Length,
            SignedOffset,
            Width,
            Phase,
            InnerColor,
            OuterColor,
            (Spec.bDesertCanyon ? 28.0f : 22.0f) *
                TerrainMaterialOverlayPlateDemotion *
                PaleBankMaterialSlashDemotion);
    }
}

void AddPreviewLandscapeNaniteMaterialScaffoldDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask)
{
    if (!World)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const bool bRainforest = Spec.bHasWaterfalls;
    const float PaleLandscapeScaffoldSlashDemotion = 0.64f;
    const float LandscapeNaniteOverlayPlateDemotion = 0.34f;
    const int32 FacetCount = Spec.bDesertCanyon ? 30 : (bRainforest ? 28 : 24);
    const float NearOffset = Spec.bDesertCanyon ? 610.0f : (bRainforest ? 315.0f : 340.0f);
    const float FarOffset = Spec.bDesertCanyon ? 3050.0f : (bRainforest ? 1750.0f : 1480.0f);

    for (int32 FacetIndex = 0; FacetIndex < FacetCount; ++FacetIndex)
    {
        const float Side = (FacetIndex % 2 == 0) ? -1.0f : 1.0f;
        const float T = static_cast<float>(FacetIndex) / static_cast<float>(FMath::Max(1, FacetCount - 1));
        const float Phase = static_cast<float>(FacetIndex) * 1.137f;
        const float BaseX = FMath::Lerp(-5200.0f, 25600.0f, T) +
            285.0f * FMath::Sin(Phase * 0.89f) +
            120.0f * FMath::Sin(Phase * 1.71f);
        const float BaseOffset = ActiveRiverHalfWidth + NearOffset +
            FarOffset * FMath::Pow(FMath::Abs(FMath::Sin(Phase * 0.58f)), Spec.bDesertCanyon ? 0.74f : 0.55f);

        float X = BaseX;
        float SignedOffset = Side * BaseOffset;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 5; ++CandidateIndex)
        {
            const float CandidateX = BaseX + 210.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.03f);
            const float CandidateOffset = BaseOffset +
                225.0f * FMath::Sin(Phase * 0.51f + static_cast<float>(CandidateIndex) * 1.19f);
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
            const float MaterialSlopeT = SmoothPreviewStep(
                ActiveRiverHalfWidth + NearOffset * 0.40f,
                ActiveRiverHalfWidth + NearOffset + FarOffset * 0.86f,
                CandidateOffset);
            const float Score = Spec.bDesertCanyon
                ? MaterialSlopeT * 0.88f + (1.0f - WaterT) * 0.32f - VegetationT * 0.16f
                : MaterialSlopeT * 0.56f + VegetationT * (bRainforest ? 0.72f : 0.34f) + (1.0f - WaterT) * 0.22f;
            if (Score > BestScore)
            {
                BestScore = Score;
                X = CandidateX;
                SignedOffset = Side * CandidateOffset;
            }
        }

        const float SampleY = GetPreviewRiverCenterY(Spec, X) + SignedOffset;
        const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, SampleY);
        const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, X, SampleY);
        const float NoiseT = FMath::Clamp(0.50f + 0.35f * FMath::Sin(Phase * 0.83f) + 0.15f * FMath::Sin(Phase * 1.91f), 0.0f, 1.0f);
        FLinearColor InnerColor;
        FLinearColor OuterColor;
        if (Spec.bDesertCanyon)
        {
            const FLinearColor DeepStrata = FLinearColor(0.26f, 0.17f, 0.11f);
            const FLinearColor Oxide = FLinearColor(0.50f, 0.31f, 0.19f);
            const FLinearColor Sand = FLinearColor(0.64f, 0.50f, 0.33f);
            InnerColor = FMath::Lerp(DeepStrata, Oxide, 0.24f + NoiseT * 0.30f);
            OuterColor = FMath::Lerp(Oxide, Sand, 0.16f + NoiseT * 0.38f);
        }
        else if (bRainforest)
        {
            const FLinearColor WetBasalt = FLinearColor(0.050f, 0.078f, 0.056f);
            const FLinearColor Moss = FLinearColor(0.060f, 0.155f, 0.064f);
            const FLinearColor LeafLitter = FLinearColor(0.090f, 0.085f, 0.052f);
            InnerColor = FMath::Lerp(WetBasalt, Moss, FMath::Clamp(0.16f + VegetationT * 0.52f, 0.0f, 0.78f));
            OuterColor = FMath::Lerp(LeafLitter, Moss, FMath::Clamp(0.18f + VegetationT * 0.42f + NoiseT * 0.12f, 0.0f, 0.76f));
        }
        else
        {
            const FLinearColor Granite = FLinearColor(0.20f, 0.20f, 0.16f);
            const FLinearColor FoothillSoil = FLinearColor(0.26f, 0.23f, 0.16f);
            const FLinearColor DryGrass = FLinearColor(0.32f, 0.29f, 0.18f);
            InnerColor = FMath::Lerp(Granite, FoothillSoil, 0.22f + NoiseT * 0.24f);
            OuterColor = FMath::Lerp(FoothillSoil, DryGrass, FMath::Clamp(0.10f + VegetationT * 0.24f + NoiseT * 0.18f, 0.0f, 0.62f));
        }

        const FLinearColor WetTint = FMath::Lerp(ScalePreviewColor(Spec.RockColor, 0.38f), ScalePreviewColor(Spec.WaterColor, 0.30f), 0.42f);
        InnerColor = FMath::Lerp(InnerColor, WetTint, FMath::Clamp(WaterT * 0.24f, 0.0f, 0.32f));
        OuterColor = FMath::Lerp(OuterColor, WetTint, FMath::Clamp(WaterT * 0.16f, 0.0f, 0.24f));
        InnerColor = FMath::Lerp(Spec.TerrainColor, InnerColor, LandscapeNaniteOverlayPlateDemotion);
        OuterColor = FMath::Lerp(Spec.TerrainColor, OuterColor, LandscapeNaniteOverlayPlateDemotion);

        const float Length = (Spec.bDesertCanyon ? 255.0f : (bRainforest ? 190.0f : 205.0f)) *
            (0.52f + 0.06f * static_cast<float>(FacetIndex % 7)) *
            LandscapeNaniteOverlayPlateDemotion *
            PaleLandscapeScaffoldSlashDemotion;
        const float Width = (Spec.bDesertCanyon ? 46.0f : (bRainforest ? 36.0f : 38.0f)) *
            (0.52f + 0.05f * static_cast<float>(FacetIndex % 5)) *
            LandscapeNaniteOverlayPlateDemotion *
            PaleLandscapeScaffoldSlashDemotion;
        AddPreviewBankBreakupPatch(
            World,
            Spec,
            TerrainRelief,
            HeightfieldPreview,
            FString::Printf(TEXT("RaftSim_LandscapeNaniteMaterialScaffoldFacet_%03d_%s"), FacetIndex, *Spec.RiverId),
            X - Length * 0.48f,
            Length,
            SignedOffset,
            Width,
            Phase,
            InnerColor,
            OuterColor,
            (Spec.bDesertCanyon ? 36.0f : 28.0f) *
                LandscapeNaniteOverlayPlateDemotion *
                PaleLandscapeScaffoldSlashDemotion);
    }

    const int32 BandPerSide = Spec.bDesertCanyon ? 4 : (bRainforest ? 3 : 3);
    for (int32 BandIndex = 0; BandIndex < BandPerSide * 2; ++BandIndex)
    {
        const float Side = (BandIndex % 2 == 0) ? -1.0f : 1.0f;
        const float T = static_cast<float>(BandIndex / 2) / static_cast<float>(FMath::Max(1, BandPerSide - 1));
        const float Phase = static_cast<float>(BandIndex) * 0.917f;
        const float X = FMath::Lerp(-4920.0f, 25500.0f, T) + 260.0f * FMath::Sin(Phase * 0.73f);
        const float OffsetBand = ActiveRiverHalfWidth +
            (Spec.bDesertCanyon ? 1160.0f + 520.0f * static_cast<float>((BandIndex / 2) % 5)
                                : (bRainforest ? 560.0f + 230.0f * static_cast<float>((BandIndex / 2) % 4)
                                               : 520.0f + 240.0f * static_cast<float>((BandIndex / 2) % 4)));
        const float SignedOffset = Side * (OffsetBand + 110.0f * FMath::Sin(Phase * 1.21f));
        FLinearColor InnerColor;
        FLinearColor OuterColor;
        if (Spec.bDesertCanyon)
        {
            InnerColor = FLinearColor(0.30f, 0.21f, 0.14f);
            OuterColor = FLinearColor(0.52f, 0.38f, 0.24f);
        }
        else if (bRainforest)
        {
            InnerColor = FLinearColor(0.055f, 0.090f, 0.060f);
            OuterColor = FLinearColor(0.075f, 0.140f, 0.065f);
        }
        else
        {
            InnerColor = FLinearColor(0.20f, 0.19f, 0.14f);
            OuterColor = FLinearColor(0.28f, 0.25f, 0.17f);
        }
        InnerColor = FMath::Lerp(Spec.TerrainColor, InnerColor, LandscapeNaniteOverlayPlateDemotion);
        OuterColor = FMath::Lerp(Spec.TerrainColor, OuterColor, LandscapeNaniteOverlayPlateDemotion);
        AddPreviewBankBreakupPatch(
            World,
            Spec,
            TerrainRelief,
            HeightfieldPreview,
            FString::Printf(TEXT("RaftSim_LandscapeNaniteStrataMicroBand_%03d_%s"), BandIndex, *Spec.RiverId),
            X - (Spec.bDesertCanyon ? 630.0f : 420.0f),
            (Spec.bDesertCanyon ? 390.0f : 270.0f) *
                LandscapeNaniteOverlayPlateDemotion *
                PaleLandscapeScaffoldSlashDemotion,
            SignedOffset,
            (Spec.bDesertCanyon ? 18.0f : 14.0f) *
                LandscapeNaniteOverlayPlateDemotion *
                PaleLandscapeScaffoldSlashDemotion,
            Phase,
            InnerColor,
            OuterColor,
            (Spec.bDesertCanyon ? 34.0f : 24.0f) *
                LandscapeNaniteOverlayPlateDemotion *
                PaleLandscapeScaffoldSlashDemotion);
    }

    const int32 OcclusionCount = Spec.bDesertCanyon ? 9 : (bRainforest ? 8 : 7);
    for (int32 OcclusionIndex = 0; OcclusionIndex < OcclusionCount; ++OcclusionIndex)
    {
        const float Side = (OcclusionIndex % 2 == 0) ? -1.0f : 1.0f;
        const float T = FMath::Frac(0.211f + 0.618034f * static_cast<float>(OcclusionIndex));
        const float Phase = static_cast<float>(OcclusionIndex) * 1.419f;
        const float X = FMath::Lerp(-5000.0f, 25200.0f, T) + 160.0f * FMath::Sin(Phase);
        const float SignedOffset = Side * (ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 660.0f : 330.0f) +
            (Spec.bDesertCanyon ? 1260.0f : 520.0f) * FMath::Abs(FMath::Sin(Phase * 0.67f)));
        const FLinearColor ShadowColor = Spec.bDesertCanyon
            ? FLinearColor(0.30f, 0.22f, 0.15f)
            : (bRainforest ? FLinearColor(0.070f, 0.130f, 0.070f) : FLinearColor(0.21f, 0.20f, 0.15f));
        const FLinearColor RimColor = Spec.bDesertCanyon
            ? FLinearColor(0.44f, 0.31f, 0.20f)
            : (bRainforest ? FLinearColor(0.085f, 0.155f, 0.075f) : FLinearColor(0.27f, 0.25f, 0.17f));
        const FLinearColor DemotedShadowColor =
            FMath::Lerp(Spec.TerrainColor, ShadowColor, LandscapeNaniteOverlayPlateDemotion);
        const FLinearColor DemotedRimColor =
            FMath::Lerp(Spec.TerrainColor, RimColor, LandscapeNaniteOverlayPlateDemotion);
        AddPreviewBankBreakupPatch(
            World,
            Spec,
            TerrainRelief,
            HeightfieldPreview,
            FString::Printf(TEXT("RaftSim_LandscapeNaniteSlopeOcclusionPatch_%03d_%s"), OcclusionIndex, *Spec.RiverId),
            X - (Spec.bDesertCanyon ? 250.0f : 185.0f),
            (Spec.bDesertCanyon ? 310.0f : 220.0f) *
                LandscapeNaniteOverlayPlateDemotion *
                PaleLandscapeScaffoldSlashDemotion,
            SignedOffset,
            (Spec.bDesertCanyon ? 28.0f : 22.0f) *
                LandscapeNaniteOverlayPlateDemotion *
                PaleLandscapeScaffoldSlashDemotion,
            Phase,
            DemotedShadowColor,
            DemotedRimColor,
            (Spec.bDesertCanyon ? 34.0f : 24.0f) *
                LandscapeNaniteOverlayPlateDemotion *
                PaleLandscapeScaffoldSlashDemotion);
    }
}

void AddPreviewProceduralEnvironmentDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask,
    UStaticMesh* PebbleMesh)
{
    if (!World)
    {
        return;
    }

    const int32 BandCount = 0;
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float BaseBandOffset = ActiveRiverHalfWidth +
        (Spec.bDesertCanyon ? Spec.BankWidthCm * 0.72f + 380.0f : Spec.BankWidthCm * 0.35f + 190.0f);
    const float BandSpacing = Spec.bDesertCanyon ? 360.0f : (Spec.bHasWaterfalls ? 190.0f : 220.0f);
    const float BandWidth = Spec.bDesertCanyon ? 54.0f : (Spec.bHasWaterfalls ? 34.0f : 38.0f);

    for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
    {
        const float Side = SideIndex == 0 ? -1.0f : 1.0f;
        for (int32 BandIndex = 0; BandIndex < BandCount; ++BandIndex)
        {
            const float Offset = BaseBandOffset + BandSpacing * static_cast<float>(BandIndex);
            const float Lift = Spec.bDesertCanyon ? 34.0f + 8.0f * static_cast<float>(BandIndex) : 26.0f;
            const float Warmth = 0.88f + 0.04f * static_cast<float>(BandIndex % 3);
            FLinearColor InnerColor;
            FLinearColor OuterColor;
            if (Spec.bDesertCanyon)
            {
                InnerColor = ScalePreviewColor(FLinearColor(0.30f, 0.21f, 0.15f), Warmth);
                OuterColor = ScalePreviewColor(FLinearColor(0.43f, 0.31f, 0.21f), 0.88f + 0.03f * static_cast<float>(BandIndex % 2));
            }
            else if (Spec.bHasWaterfalls)
            {
                InnerColor = ScalePreviewColor(FLinearColor(0.028f, 0.060f, 0.036f), 0.88f + 0.04f * static_cast<float>(BandIndex % 2));
                OuterColor = ScalePreviewColor(FLinearColor(0.052f, 0.088f, 0.050f), 0.84f + 0.05f * static_cast<float>(BandIndex % 3));
            }
            else
            {
                InnerColor = ScalePreviewColor(FLinearColor(0.12f, 0.12f, 0.095f), 0.88f + 0.04f * static_cast<float>(BandIndex % 2));
                OuterColor = ScalePreviewColor(FLinearColor(0.20f, 0.18f, 0.13f), 0.86f + 0.04f * static_cast<float>(BandIndex % 3));
            }

            AddPreviewShoreRibbon(
                World,
                Spec,
                TerrainRelief,
                HeightfieldPreview,
                FString::Printf(TEXT("RaftSim_ProceduralSourceDetailBand_%02d_%s_%s"), BandIndex, Side < 0.0f ? TEXT("Left") : TEXT("Right"), *Spec.RiverId),
                Side * Offset,
                BandWidth,
                Lift,
                InnerColor,
                OuterColor);
        }
    }

    if (!PebbleMesh)
    {
        return;
    }

    const int32 WaterlinePebbleCount = Spec.bDesertCanyon ? 128 : (Spec.bHasWaterfalls ? 138 : 112);
    const float WetBankScale = FMath::Max(0.35f, Spec.FlowWetBankScale);
    const float WaterSurfaceZ = GetPreviewWaterSurfaceBaseZCm(Spec);
    for (int32 PebbleIndex = 0; PebbleIndex < WaterlinePebbleCount; ++PebbleIndex)
    {
        const float T = static_cast<float>(PebbleIndex) / static_cast<float>(FMath::Max(1, WaterlinePebbleCount - 1));
        const float Side = (PebbleIndex % 2 == 0) ? -1.0f : 1.0f;
        const float BaseX = FMath::Lerp(850.0f, 25800.0f, T) +
            95.0f * FMath::Sin(static_cast<float>(PebbleIndex) * 1.71f);
        float X = BaseX;
        float Y = GetPreviewRiverCenterY(Spec, X) + Side * (ActiveRiverHalfWidth + 48.0f * WetBankScale);
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 4; ++CandidateIndex)
        {
            const float CandidateX = BaseX +
                56.0f * FMath::Sin(static_cast<float>(PebbleIndex) * 0.47f + static_cast<float>(CandidateIndex) * 1.21f);
            const float ShoreOffset = ActiveRiverHalfWidth + WetBankScale *
                (24.0f + 42.0f * static_cast<float>(CandidateIndex) + 38.0f * FMath::Abs(FMath::Sin(static_cast<float>(PebbleIndex) * 1.19f)));
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * ShoreOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
            const float EdgePreference = 1.0f -
                FMath::Clamp(FMath::Abs(ShoreOffset - (ActiveRiverHalfWidth + 76.0f * WetBankScale)) / (170.0f * WetBankScale), 0.0f, 1.0f);
            const float Score = EdgePreference * 1.35f + WaterT * 0.46f - VegetationT * 0.52f +
                0.04f * FMath::Sin(static_cast<float>(PebbleIndex) * 0.91f + static_cast<float>(CandidateIndex));
            if (Score > BestScore)
            {
                BestScore = Score;
                X = CandidateX;
                Y = CandidateY;
            }
        }

        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
        const float PebbleScale = 0.62f + 0.16f * static_cast<float>(PebbleIndex % 6);
        const FVector Scale = Spec.bDesertCanyon
            ? FVector(0.115f * PebbleScale, 0.064f * PebbleScale, 0.014f * PebbleScale)
            : FVector(0.084f * PebbleScale, 0.052f * PebbleScale, 0.013f * PebbleScale);
        const FLinearColor DryPebbleColor = Spec.bDesertCanyon
            ? ScalePreviewColor(FLinearColor(0.42f, 0.30f, 0.20f), 0.88f + 0.05f * static_cast<float>(PebbleIndex % 4))
            : (Spec.bHasWaterfalls
                  ? ScalePreviewColor(FLinearColor(0.035f, 0.055f, 0.045f), 0.86f + 0.05f * static_cast<float>(PebbleIndex % 5))
                  : ScalePreviewColor(FLinearColor(0.16f, 0.15f, 0.12f), 0.88f + 0.04f * static_cast<float>(PebbleIndex % 4)));
        const FLinearColor WetPebbleColor = FMath::Lerp(
            ScalePreviewColor(Spec.RockColor, Spec.bDesertCanyon ? 0.50f : 0.42f),
            ScalePreviewColor(Spec.WaterColor, Spec.bDesertCanyon ? 0.40f : 0.34f),
            Spec.bDesertCanyon ? 0.22f : 0.36f);
        const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, Y);
        const FLinearColor PebbleColor = FMath::Lerp(
            DryPebbleColor,
            WetPebbleColor,
            FMath::Clamp(0.24f + WaterT * 0.48f, 0.0f, 0.72f));

        AddPreviewIrregularRockActor(
            World,
            FString::Printf(TEXT("RaftSim_FlowAwareWaterlinePebble_%03d_%s"), PebbleIndex, *Spec.RiverId),
            FVector(X, Y, FMath::Max(TerrainZ + 5.0f, WaterSurfaceZ + 3.0f)),
            static_cast<float>((PebbleIndex * 37) % 360),
            Scale,
            PebbleColor,
            PebbleIndex + 1700);
    }

    const int32 PebbleCount = Spec.bDesertCanyon ? 96 : (Spec.bHasWaterfalls ? 86 : 72);
    for (int32 PebbleIndex = 0; PebbleIndex < PebbleCount; ++PebbleIndex)
    {
        const float T = static_cast<float>(PebbleIndex) / static_cast<float>(FMath::Max(1, PebbleCount - 1));
        const float Side = (PebbleIndex % 2 == 0) ? -1.0f : 1.0f;
        const float BarJitter = FMath::Abs(FMath::Sin(static_cast<float>(PebbleIndex) * 1.31f));
        const float BaseX = FMath::Lerp(-4300.0f, 24600.0f, T) + 190.0f * FMath::Sin(static_cast<float>(PebbleIndex) * 2.13f);
        const float BaseOffset = ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 120.0f : 85.0f) +
            BarJitter * (Spec.bDesertCanyon ? 520.0f : 310.0f) +
            static_cast<float>(PebbleIndex % 4) * (Spec.bDesertCanyon ? 68.0f : 42.0f);
        float X = BaseX;
        float Y = GetPreviewRiverCenterY(Spec, X) + Side * BaseOffset;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 4; ++CandidateIndex)
        {
            const float CandidateX = BaseX + 72.0f * FMath::Sin(static_cast<float>(PebbleIndex) * 0.41f + static_cast<float>(CandidateIndex) * 1.37f);
            const float CandidateOffset = BaseOffset + Side * 92.0f * (static_cast<float>(CandidateIndex) - 1.5f);
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
            const float Score = WaterT * 1.25f - VegetationT * 0.42f +
                0.04f * FMath::Sin(static_cast<float>(PebbleIndex) * 0.73f + static_cast<float>(CandidateIndex));
            if (Score > BestScore)
            {
                BestScore = Score;
                X = CandidateX;
                Y = CandidateY;
            }
        }
        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
        const float PebbleScale = 0.72f + 0.18f * static_cast<float>(PebbleIndex % 5);
        const FVector Scale = Spec.bDesertCanyon
            ? FVector(0.42f * PebbleScale, 0.24f * PebbleScale, 0.055f * PebbleScale)
            : FVector(0.28f * PebbleScale, 0.18f * PebbleScale, 0.045f * PebbleScale);
        const FLinearColor PebbleColor = Spec.bDesertCanyon
            ? ScalePreviewColor(FMath::Lerp(FLinearColor(0.44f, 0.31f, 0.21f), Spec.RockColor, 0.45f), 0.90f + 0.06f * static_cast<float>(PebbleIndex % 4))
            : (Spec.bHasWaterfalls
                  ? ScalePreviewColor(FMath::Lerp(FLinearColor(0.045f, 0.060f, 0.050f), Spec.RockColor, 0.58f), 0.86f + 0.05f * static_cast<float>(PebbleIndex % 5))
                  : ScalePreviewColor(FMath::Lerp(FLinearColor(0.20f, 0.18f, 0.14f), Spec.RockColor, 0.52f), 0.88f + 0.05f * static_cast<float>(PebbleIndex % 4)));
        const float WetMaskT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, Y);
        const FLinearColor MaskAwarePebbleColor = FMath::Lerp(
            PebbleColor,
            FMath::Lerp(ScalePreviewColor(Spec.RockColor, 0.45f), ScalePreviewColor(Spec.WaterColor, 0.36f), 0.35f),
            FMath::Clamp(WetMaskT * 0.42f, 0.0f, 0.50f));

        AddPreviewIrregularRockActor(
            World,
            FString::Printf(TEXT("RaftSim_ProceduralTalusPebble_%03d_%s"), PebbleIndex, *Spec.RiverId),
            FVector(X, Y, TerrainZ + (Spec.bDesertCanyon ? 7.0f : 6.0f)),
            static_cast<float>((PebbleIndex * 29) % 360),
            Scale,
            MaskAwarePebbleColor,
            PebbleIndex + 2800);
    }
}
} // namespace RaftSimEditorEnvironment
