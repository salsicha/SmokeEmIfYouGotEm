#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
void AddPreviewNearFieldPhotorealReviewDressing(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* AerialDrape,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask)
{
    if (!World)
    {
        return;
    }

    const float WaterBaseZ = GetPreviewWaterSurfaceBaseZCm(Spec);
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const FLinearColor NearFieldCurrentShadow = Spec.bDesertCanyon
        ? FLinearColor(0.240f, 0.195f, 0.125f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.035f, 0.165f, 0.090f)
                                : FLinearColor(0.045f, 0.190f, 0.110f));
    const FLinearColor NearFieldCurrentDepth = Spec.bDesertCanyon
        ? FLinearColor(0.390f, 0.315f, 0.195f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.055f, 0.285f, 0.155f)
                                : FLinearColor(0.065f, 0.305f, 0.185f));
    const FLinearColor NearFieldCurrentHighlight = Spec.bDesertCanyon
        ? FLinearColor(0.670f, 0.560f, 0.360f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.210f, 0.545f, 0.330f)
                                : FLinearColor(0.235f, 0.565f, 0.360f));
    const FLinearColor NearFieldFoamFleck = Spec.bDesertCanyon
        ? FLinearColor(0.760f, 0.730f, 0.620f)
        : FLinearColor(0.750f, 0.880f, 0.780f);

    const bool bUseNearFieldCaptureQualityWaterTexture = true;
    if (bUseNearFieldCaptureQualityWaterTexture)
    {
        constexpr int32 XSteps = 720;
        constexpr int32 CrossSteps = 128;
        const float NearFieldCaptureQualityWaterApronMinX = -11600.0f;
        const float MinX = NearFieldCaptureQualityWaterApronMinX;
        const float MaxX = 19600.0f;

        TArray<FVector> Vertices;
        TArray<FVector> Normals;
        TArray<FVector2D> UVs;
        TArray<FLinearColor> VertexColors;
        TArray<int32> Triangles;
        Vertices.Reserve((XSteps + 1) * (CrossSteps + 1));
        Normals.Reserve((XSteps + 1) * (CrossSteps + 1));
        UVs.Reserve((XSteps + 1) * (CrossSteps + 1));
        VertexColors.Reserve((XSteps + 1) * (CrossSteps + 1));
        Triangles.Reserve(XSteps * CrossSteps * 6);

        for (int32 XIndex = 0; XIndex <= XSteps; ++XIndex)
        {
            const float U = static_cast<float>(XIndex) / static_cast<float>(XSteps);
            const float X = FMath::Lerp(MinX, MaxX, U);
            const float CenterY = GetPreviewRiverCenterY(Spec, X);
            const float Width = ActiveRiverHalfWidth *
                (Spec.bDesertCanyon ? 1.30f : 1.18f) *
                (0.95f + 0.06f * FMath::Sin(X * 0.0037f));
            const float LongFeather = SmoothPreviewStep(0.00f, 0.035f, U) *
                (1.0f - SmoothPreviewStep(0.90f, 1.0f, U));
            const float NearFieldSmoothedWaterTextureGain = Spec.bDesertCanyon ? 0.24f : 0.34f;
            const float NearFieldWaterSourceTileDemotionT = Spec.bDesertCanyon ? 0.62f : 0.48f;
            const float NearFieldWaterPatchTileBreakupDemotionT = Spec.bDesertCanyon ? 0.68f : 0.60f;
            const float ContinuousNearFieldWaterCurrentBlendT = Spec.bDesertCanyon ? 0.88f : 0.66f;
            const float ResidualNearFieldPatchPaletteGain = 1.0f - NearFieldWaterPatchTileBreakupDemotionT;
            for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
            {
                const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
                const float Lateral = FMath::Lerp(-Width, Width, V);
                const float EdgeT = FMath::Pow(FMath::Abs(V - 0.5f) * 2.0f, 1.12f);
                const float CenterT = FMath::Pow(1.0f - FMath::Clamp(EdgeT, 0.0f, 1.0f), 0.46f);
                const float ThreadNoise = FMath::Clamp(
                    0.50f +
                        0.31f * FMath::Sin(X * 0.016f + Lateral * 0.020f + Spec.FlowCurrentCueScale * 0.37f) +
                        0.24f * FMath::Sin(X * 0.043f - Lateral * 0.027f) +
                        0.16f * FMath::Sin(X * 0.087f + Lateral * 0.061f),
                    0.0f,
                    1.0f);
                const float CellNoise = FMath::Frac(
                    FMath::Sin(static_cast<float>((XIndex + 59) * 149 + (CrossIndex + 31) * 283) * 12.9898f) *
                    43758.5453f);
                const float TextureNoise = FMath::Clamp(CellNoise * 0.035f + ThreadNoise * 0.965f, 0.0f, 1.0f);
                const float ColorStrataNoise = FMath::Clamp(
                    0.50f +
                        0.28f * FMath::Sin(X * 0.011f - Lateral * 0.017f + Spec.FlowCurrentCueScale * 0.53f) +
                        0.24f * FMath::Sin(X * 0.032f + Lateral * 0.041f) +
                        0.15f * FMath::Sin(X * 0.069f - Lateral * 0.083f),
                    0.0f,
                    1.0f);
                const float TextureT = FMath::Clamp(
                    (0.52f + CenterT * 0.36f + EdgeT * 0.18f) *
                        LongFeather *
                        NearFieldSmoothedWaterTextureGain *
                        FMath::Clamp(Spec.FlowCurrentCueScale, 0.85f, 1.35f),
                    0.0f,
                    Spec.bDesertCanyon ? 1.05f : 1.12f);
                FLinearColor WaterColor = FMath::Lerp(NearFieldCurrentShadow, NearFieldCurrentDepth, CenterT * 0.68f);
                WaterColor = FMath::Lerp(
                    WaterColor,
                    NearFieldCurrentHighlight,
                    FMath::Clamp(SmoothPreviewStep(0.54f, 0.92f, TextureNoise) * TextureT * 0.52f, 0.0f, 0.54f));
                WaterColor = FMath::Lerp(
                    WaterColor,
                    NearFieldCurrentShadow,
                    FMath::Clamp(SmoothPreviewStep(0.06f, 0.40f, 1.0f - TextureNoise) * TextureT * 0.46f, 0.0f, 0.48f));
                WaterColor = FMath::Lerp(
                    WaterColor,
                    NearFieldFoamFleck,
                    FMath::Clamp(
                        SmoothPreviewStep(0.80f, 0.975f, TextureNoise) *
                            CenterT *
                            LongFeather *
                            FMath::Clamp(Spec.FlowFoamScale, 0.70f, 1.40f) *
                            (Spec.bDesertCanyon ? 0.28f : 0.36f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.30f : 0.38f));
                const FLinearColor RiverBedWarmMottle = Spec.bDesertCanyon
                    ? FLinearColor(0.620f, 0.420f, 0.235f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.080f, 0.285f, 0.145f)
                                            : FLinearColor(0.195f, 0.330f, 0.235f));
                const FLinearColor SkyReflectionMottle = Spec.bDesertCanyon
                    ? FLinearColor(0.385f, 0.540f, 0.600f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.225f, 0.520f, 0.455f)
                                            : FLinearColor(0.290f, 0.585f, 0.520f));
                const FLinearColor AeratedPocketMottle = Spec.bDesertCanyon
                    ? FLinearColor(0.865f, 0.800f, 0.620f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.560f, 0.780f, 0.610f)
                                            : FLinearColor(0.610f, 0.785f, 0.650f));
                WaterColor = FMath::Lerp(
                    WaterColor,
                    RiverBedWarmMottle,
                    FMath::Clamp(
                        SmoothPreviewStep(0.10f, 0.42f, 1.0f - ColorStrataNoise) *
                            TextureT *
                            (Spec.bDesertCanyon ? 0.30f : 0.22f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.32f : 0.24f));
                WaterColor = FMath::Lerp(
                    WaterColor,
                    SkyReflectionMottle,
                    FMath::Clamp(
                        SmoothPreviewStep(0.48f, 0.82f, ColorStrataNoise) *
                            TextureT *
                            (0.18f + CenterT * 0.16f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.26f : 0.34f));
                WaterColor = FMath::Lerp(
                    WaterColor,
                    AeratedPocketMottle,
                    FMath::Clamp(
                        SmoothPreviewStep(0.76f, 0.98f, TextureNoise) *
                            SmoothPreviewStep(0.22f, 0.82f, ColorStrataNoise) *
                            TextureT *
                            FMath::Clamp(Spec.FlowFoamScale, 0.70f, 1.45f) *
                            (Spec.bDesertCanyon ? 0.16f : 0.22f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.20f : 0.26f));
                WaterColor = ScalePreviewColor(
                    WaterColor,
                    FMath::Clamp(0.74f + TextureNoise * 0.46f + ThreadNoise * 0.20f, 0.62f, 1.42f));
                const FLinearColor NearFieldCurrentOliveMottle = Spec.bDesertCanyon
                    ? FLinearColor(0.500f, 0.405f, 0.245f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.075f, 0.355f, 0.175f)
                                            : FLinearColor(0.095f, 0.385f, 0.225f));
                const FLinearColor NearFieldCurrentDeepMottle = Spec.bDesertCanyon
                    ? FLinearColor(0.205f, 0.165f, 0.105f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.020f, 0.125f, 0.070f)
                                            : FLinearColor(0.030f, 0.145f, 0.085f));
                WaterColor = FMath::Lerp(
                    WaterColor,
                    NearFieldCurrentOliveMottle,
                    FMath::Clamp(SmoothPreviewStep(0.62f, 0.96f, ThreadNoise) * TextureT * 0.16f, 0.0f, 0.18f));
                WaterColor = FMath::Lerp(
                    WaterColor,
                    NearFieldCurrentDeepMottle,
                    FMath::Clamp(SmoothPreviewStep(0.04f, 0.36f, 1.0f - ThreadNoise) * TextureT * 0.14f, 0.0f, 0.16f));
                const float RiverSurfacePatchSeed = FMath::Clamp(
                    0.50f +
                        0.32f * FMath::Sin(X * 0.0048f + Lateral * 0.0064f + Spec.FlowCurrentCueScale * 0.23f) +
                        0.18f * FMath::Sin(X * 0.0125f - Lateral * 0.0038f + CenterT * 0.61f),
                    0.0f,
                    1.0f);
                const FLinearColor RiverSurfacePatchColor = RiverSurfacePatchSeed < 0.20f
                    ? RiverBedWarmMottle
                    : (RiverSurfacePatchSeed < 0.42f
                           ? (Spec.bDesertCanyon ? FLinearColor(0.235f, 0.285f, 0.330f) : NearFieldCurrentDepth)
                           : (RiverSurfacePatchSeed < 0.64f
                                  ? SkyReflectionMottle
                                  : (RiverSurfacePatchSeed < 0.84f ? NearFieldCurrentHighlight : AeratedPocketMottle)));
                WaterColor = FMath::Lerp(
                    WaterColor,
                    RiverSurfacePatchColor,
                    FMath::Clamp(
                        TextureT *
                            (0.24f + CenterT * 0.18f + CellNoise * 0.04f) *
                            (0.44f + ResidualNearFieldPatchPaletteGain * 0.56f) *
                            (Spec.bDesertCanyon ? 1.28f : 1.0f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.34f : 0.36f));
                const float IntegratedWaterFleckCell = FMath::Frac(
                    FMath::Sin(static_cast<float>((XIndex + 211) * 619 + (CrossIndex + 109) * 941) * 12.9898f) *
                    43758.5453f);
                const float IntegratedWaterFleckThread = FMath::Clamp(
                    0.50f +
                        0.34f * FMath::Sin(X * 0.028f + Lateral * 0.041f + Spec.FlowCurrentCueScale * 0.29f) +
                        0.23f * FMath::Sin(X * 0.072f - Lateral * 0.055f + CenterT * 0.67f) +
                        0.14f * FMath::Sin(X * 0.133f + Lateral * 0.089f),
                    0.0f,
                    1.0f);
                const float IntegratedWaterFleckNoise =
                    FMath::Clamp(IntegratedWaterFleckCell * 0.04f + IntegratedWaterFleckThread * 0.96f, 0.0f, 1.0f);
                const FLinearColor IntegratedWaterFleckSkyAccent = Spec.bDesertCanyon
                    ? FLinearColor(0.610f, 0.600f, 0.500f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.260f, 0.560f, 0.470f)
                                            : FLinearColor(0.340f, 0.640f, 0.545f));
                const FLinearColor IntegratedWaterFleckBedAccent = Spec.bDesertCanyon
                    ? FLinearColor(0.510f, 0.390f, 0.225f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.060f, 0.255f, 0.135f)
                                            : FLinearColor(0.170f, 0.350f, 0.235f));
                const FLinearColor IntegratedWaterFleckDeepAccent = Spec.bDesertCanyon
                    ? FLinearColor(0.190f, 0.235f, 0.285f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.020f, 0.135f, 0.070f)
                                            : FLinearColor(0.035f, 0.170f, 0.095f));
                const FLinearColor IntegratedWaterFleckFoamAccent = Spec.bDesertCanyon
                    ? FLinearColor(0.820f, 0.770f, 0.590f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.590f, 0.800f, 0.620f)
                                            : FLinearColor(0.640f, 0.800f, 0.660f));
                const FLinearColor IntegratedWaterFleckColor = IntegratedWaterFleckNoise < 0.22f
                    ? IntegratedWaterFleckDeepAccent
                    : (IntegratedWaterFleckNoise < 0.48f
                           ? IntegratedWaterFleckBedAccent
                           : (IntegratedWaterFleckNoise < 0.76f
                                  ? IntegratedWaterFleckSkyAccent
                                  : IntegratedWaterFleckFoamAccent));
                const float IntegratedWaterFleckT = FMath::Clamp(
                    TextureT *
                        (0.36f + CenterT * 0.20f + EdgeT * 0.18f) *
                        (0.84f + FMath::Clamp(Spec.FlowFoamScale, 0.70f, 1.45f) * 0.14f),
                    0.0f,
                    Spec.bDesertCanyon ? 0.76f : 0.70f);
                WaterColor = FMath::Lerp(
                    WaterColor,
                    IntegratedWaterFleckColor,
                    FMath::Clamp(
                        IntegratedWaterFleckT *
                            (0.38f + SmoothPreviewStep(0.72f, 0.98f, IntegratedWaterFleckNoise) * 0.18f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.30f : 0.29f));
                const float IntegratedWaterEntropyEdgeCell = FMath::Frac(
                    FMath::Sin(static_cast<float>((XIndex + 307) * 773 + (CrossIndex + 157) * 1013) * 12.9898f) *
                    43758.5453f);
                const float IntegratedWaterEntropyEdgeThread = FMath::Clamp(
                    0.50f +
                        0.36f * FMath::Sin(X * 0.046f + Lateral * 0.068f + TextureNoise * 0.91f) +
                        0.24f * FMath::Sin(X * 0.113f - Lateral * 0.094f + Spec.FlowFoamScale * 0.37f) +
                        0.14f * FMath::Sin(X * 0.181f + Lateral * 0.137f),
                    0.0f,
                    1.0f);
                const float IntegratedWaterEntropyEdgeNoise = FMath::Clamp(
                    IntegratedWaterEntropyEdgeCell * 0.035f + IntegratedWaterEntropyEdgeThread * 0.965f,
                    0.0f,
                    1.0f);
                const FLinearColor IntegratedWaterEntropyDeepPocket = Spec.bDesertCanyon
                    ? FLinearColor(0.170f, 0.230f, 0.300f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.018f, 0.115f, 0.055f)
                                            : FLinearColor(0.025f, 0.145f, 0.075f));
                const FLinearColor IntegratedWaterEntropyWarmShelf = Spec.bDesertCanyon
                    ? FLinearColor(0.690f, 0.435f, 0.215f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.090f, 0.335f, 0.140f)
                                            : FLinearColor(0.205f, 0.390f, 0.215f));
                const FLinearColor IntegratedWaterEntropyColdSky = Spec.bDesertCanyon
                    ? FLinearColor(0.300f, 0.565f, 0.690f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.210f, 0.610f, 0.500f)
                                            : FLinearColor(0.310f, 0.655f, 0.565f));
                const FLinearColor IntegratedWaterEntropyBrokenFoam = Spec.bDesertCanyon
                    ? FLinearColor(0.875f, 0.780f, 0.545f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.660f, 0.850f, 0.635f)
                                            : FLinearColor(0.705f, 0.850f, 0.675f));
                const FLinearColor IntegratedWaterEntropyColor = IntegratedWaterEntropyEdgeNoise < 0.20f
                    ? IntegratedWaterEntropyDeepPocket
                    : (IntegratedWaterEntropyEdgeNoise < 0.46f
                           ? IntegratedWaterEntropyWarmShelf
                           : (IntegratedWaterEntropyEdgeNoise < 0.74f
                                  ? IntegratedWaterEntropyColdSky
                                  : IntegratedWaterEntropyBrokenFoam));
                const float IntegratedWaterEntropyEdgeT = FMath::Clamp(
                    TextureT *
                        (0.38f + CenterT * 0.30f + EdgeT * 0.24f) *
                        (0.82f + FMath::Clamp(Spec.FlowCurrentCueScale, 0.80f, 1.40f) * 0.16f),
                    0.0f,
                    Spec.bDesertCanyon ? 0.92f : 0.86f);
                WaterColor = FMath::Lerp(
                    WaterColor,
                    IntegratedWaterEntropyColor,
                    FMath::Clamp(
                        IntegratedWaterEntropyEdgeT *
                            (0.42f + SmoothPreviewStep(0.54f, 0.96f, IntegratedWaterEntropyEdgeNoise) * 0.28f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.35f : 0.36f));
                WaterColor = ScalePreviewColor(
                    WaterColor,
                    FMath::Clamp(
                        0.72f + IntegratedWaterEntropyEdgeNoise * 0.54f + TextureNoise * 0.18f,
                        Spec.bDesertCanyon ? 0.66f : 0.62f,
                        Spec.bDesertCanyon ? 1.48f : 1.56f));
                const float NearCameraWaterEntropyCell = FMath::Frac(
                    FMath::Sin(static_cast<float>((XIndex + 419) * 1223 + (CrossIndex + 197) * 1613) * 12.9898f) *
                    43758.5453f);
                const float NearCameraWaterEntropyThread = FMath::Clamp(
                    0.50f +
                        0.35f * FMath::Sin(X * 0.084f + Lateral * 0.126f + NearCameraWaterEntropyCell * 0.71f) +
                        0.24f * FMath::Sin(X * 0.171f - Lateral * 0.098f + Spec.FlowCurrentCueScale * 0.53f) +
                        0.17f * FMath::Sin(X * 0.267f + Lateral * 0.193f),
                    0.0f,
                    1.0f);
                const float NearCameraWaterEntropyNoise = FMath::Clamp(
                    NearCameraWaterEntropyCell * 0.035f + NearCameraWaterEntropyThread * 0.965f,
                    0.0f,
                    1.0f);
                const FLinearColor NearCameraWaterEntropyDeep = Spec.bDesertCanyon
                    ? FLinearColor(0.155f, 0.205f, 0.255f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.014f, 0.105f, 0.050f)
                                            : FLinearColor(0.018f, 0.125f, 0.060f));
                const FLinearColor NearCameraWaterEntropyBed = Spec.bDesertCanyon
                    ? FLinearColor(0.710f, 0.445f, 0.210f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.075f, 0.310f, 0.120f)
                                            : FLinearColor(0.170f, 0.365f, 0.165f));
                const FLinearColor NearCameraWaterEntropySky = Spec.bDesertCanyon
                    ? FLinearColor(0.350f, 0.625f, 0.720f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.245f, 0.650f, 0.540f)
                                            : FLinearColor(0.350f, 0.690f, 0.595f));
                const FLinearColor NearCameraWaterEntropyFoam = Spec.bDesertCanyon
                    ? FLinearColor(0.920f, 0.830f, 0.570f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.700f, 0.900f, 0.665f)
                                            : FLinearColor(0.760f, 0.910f, 0.700f));
                const FLinearColor NearCameraWaterEntropyColor = NearCameraWaterEntropyNoise < 0.18f
                    ? NearCameraWaterEntropyDeep
                    : (NearCameraWaterEntropyNoise < 0.42f
                           ? NearCameraWaterEntropyBed
                           : (NearCameraWaterEntropyNoise < 0.72f
                                  ? NearCameraWaterEntropySky
                                  : NearCameraWaterEntropyFoam));
                const float NearCameraWaterEntropyT = FMath::Clamp(
                    LongFeather *
                        TextureT *
                        (0.32f + CenterT * 0.24f + EdgeT * 0.14f) *
                        (0.82f + Spec.FlowFoamScale * 0.12f),
                    0.0f,
                    Spec.bDesertCanyon ? 0.74f : 0.68f);
                WaterColor = FMath::Lerp(
                    WaterColor,
                    NearCameraWaterEntropyColor,
                    FMath::Clamp(
                        NearCameraWaterEntropyT *
                            (0.44f + SmoothPreviewStep(0.58f, 0.96f, NearCameraWaterEntropyNoise) * 0.26f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.36f : 0.38f));
                WaterColor = ScalePreviewColor(
                    WaterColor,
                    FMath::Clamp(
                        0.66f + NearCameraWaterEntropyNoise * 0.62f + NearCameraWaterEntropyThread * 0.20f,
                        Spec.bDesertCanyon ? 0.58f : 0.54f,
                        Spec.bDesertCanyon ? 1.62f : 1.72f));
                const float SmoothNearFieldBand = FMath::Clamp(
                    0.50f +
                        0.34f * FMath::Sin(X * 0.0046f + Lateral * 0.0062f + Spec.FlowCurrentCueScale * 0.24f) +
                        0.16f * FMath::Sin(X * 0.0110f - Lateral * 0.0034f + CenterT * 0.57f),
                    0.0f,
                    1.0f);
                const float SmoothNearFieldRipple = FMath::Clamp(
                    0.50f +
                        0.27f * FMath::Sin(X * 0.030f + Lateral * 0.019f + Spec.FlowCurrentCueScale * 0.49f) +
                        0.20f * FMath::Sin(X * 0.067f - Lateral * 0.043f + EdgeT * 0.83f) +
                        0.13f * FMath::Sin(X * 0.118f + Lateral * 0.081f),
                    0.0f,
                    1.0f);
                const float SmoothNearFieldFineRipple = FMath::Clamp(
                    0.50f +
                        0.23f * FMath::Sin(X * 0.036f + Lateral * 0.029f + Spec.FlowCurrentCueScale * 0.31f) +
                        0.18f * FMath::Sin(X * 0.064f - Lateral * 0.041f + CenterT * 0.79f) +
                        0.13f * FMath::Sin(X * 0.091f + Lateral * 0.067f + EdgeT * 0.47f),
                    0.0f,
                    1.0f);
                const float SmoothNearFieldCrossThread = FMath::Clamp(
                    0.50f +
                        0.29f * FMath::Sin(X * 0.0084f - Lateral * 0.0156f + Spec.FlowCurrentCueScale * 0.43f) +
                        0.23f * FMath::Sin(X * 0.0185f + Lateral * 0.0275f + CenterT * 0.72f) +
                        0.17f * FMath::Sin(X * 0.0410f - Lateral * 0.0520f + EdgeT * 0.66f) +
                        0.11f * FMath::Sin(X * 0.0730f + Lateral * 0.0800f),
                    0.0f,
                    1.0f);
                const float SmoothNearFieldRefractionThread = FMath::Clamp(
                    0.50f +
                        0.30f * FMath::Sin(X * 0.0120f + Lateral * 0.0105f + SmoothNearFieldRipple * 0.83f) +
                        0.21f * FMath::Sin(X * 0.0265f - Lateral * 0.0330f + SmoothNearFieldBand * 0.59f) +
                        0.16f * FMath::Sin(X * 0.0580f + Lateral * 0.0460f + SmoothNearFieldFineRipple * 0.41f),
                    0.0f,
                    1.0f);
                const float SmoothNearFieldDepthT = FMath::Clamp(
                    CenterT * 0.46f + SmoothNearFieldBand * 0.20f + SmoothNearFieldRipple * 0.18f +
                        SmoothNearFieldFineRipple * 0.12f + EdgeT * 0.08f,
                    0.0f,
                    1.0f);
                FLinearColor SmoothNearFieldWaterColor =
                    FMath::Lerp(NearFieldCurrentShadow, NearFieldCurrentDepth, SmoothNearFieldDepthT);
                SmoothNearFieldWaterColor = FMath::Lerp(
                    SmoothNearFieldWaterColor,
                    NearFieldCurrentShadow,
                    FMath::Clamp(
                        SmoothPreviewStep(0.08f, 0.34f, 1.0f - SmoothNearFieldRipple) * LongFeather *
                            (Spec.bDesertCanyon ? 0.32f : 0.38f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.34f : 0.40f));
                SmoothNearFieldWaterColor = FMath::Lerp(
                    SmoothNearFieldWaterColor,
                    NearFieldCurrentHighlight,
                    FMath::Clamp(
                        SmoothPreviewStep(0.56f, 0.94f, SmoothNearFieldRipple) * LongFeather *
                            (Spec.bDesertCanyon ? 0.34f : 0.42f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.36f : 0.44f));
                SmoothNearFieldWaterColor = FMath::Lerp(
                    SmoothNearFieldWaterColor,
                    SmoothNearFieldFineRipple > 0.5f ? NearFieldCurrentHighlight : NearFieldCurrentShadow,
                    FMath::Clamp(
                        SmoothPreviewStep(0.18f, 0.92f, FMath::Abs(SmoothNearFieldFineRipple - 0.5f) * 2.0f) *
                            LongFeather *
                            (Spec.bDesertCanyon ? 0.38f : 0.46f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.40f : 0.48f));
                SmoothNearFieldWaterColor = FMath::Lerp(
                    SmoothNearFieldWaterColor,
                    Spec.bDesertCanyon ? RiverBedWarmMottle : SkyReflectionMottle,
                    FMath::Clamp(
                        SmoothPreviewStep(0.58f, 0.90f, SmoothNearFieldBand) * LongFeather *
                            (Spec.bDesertCanyon ? 0.26f : 0.34f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.28f : 0.36f));
                SmoothNearFieldWaterColor = FMath::Lerp(
                    SmoothNearFieldWaterColor,
                    RiverBedWarmMottle,
                    FMath::Clamp(
                        SmoothPreviewStep(0.12f, 0.46f, 1.0f - SmoothNearFieldCrossThread) *
                            SmoothPreviewStep(0.14f, 0.90f, SmoothNearFieldRefractionThread) *
                            LongFeather *
                            (Spec.bDesertCanyon ? 0.34f : 0.24f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.36f : 0.26f));
                SmoothNearFieldWaterColor = FMath::Lerp(
                    SmoothNearFieldWaterColor,
                    SkyReflectionMottle,
                    FMath::Clamp(
                        SmoothPreviewStep(0.52f, 0.94f, SmoothNearFieldCrossThread) *
                            SmoothPreviewStep(0.28f, 0.86f, SmoothNearFieldRefractionThread) *
                            CenterT *
                            LongFeather *
                            (Spec.bDesertCanyon ? 0.26f : 0.36f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.28f : 0.38f));
                SmoothNearFieldWaterColor = FMath::Lerp(
                    SmoothNearFieldWaterColor,
                    AeratedPocketMottle,
                    FMath::Clamp(
                        SmoothPreviewStep(0.78f, 0.98f, SmoothNearFieldCrossThread) *
                            SmoothPreviewStep(0.60f, 0.96f, SmoothNearFieldFineRipple) *
                            CenterT *
                            LongFeather *
                            FMath::Clamp(Spec.FlowFoamScale, 0.70f, 1.40f) *
                            (Spec.bDesertCanyon ? 0.18f : 0.24f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.20f : 0.26f));
                if (Spec.bHasWaterfalls)
                {
                    const FLinearColor RainforestCanopyReflection = FLinearColor(0.018f, 0.185f, 0.060f);
                    const FLinearColor WetClayBedReflection = FLinearColor(0.155f, 0.215f, 0.082f);
                    const FLinearColor BrightMistSkyReflection = FLinearColor(0.265f, 0.700f, 0.570f);
                    SmoothNearFieldWaterColor = FMath::Lerp(
                        SmoothNearFieldWaterColor,
                        RainforestCanopyReflection,
                        FMath::Clamp(
                            SmoothPreviewStep(0.08f, 0.44f, 1.0f - SmoothNearFieldBand) *
                                SmoothPreviewStep(0.18f, 0.82f, SmoothNearFieldCrossThread) *
                                CenterT *
                                LongFeather *
                                0.34f,
                            0.0f,
                            0.36f));
                    SmoothNearFieldWaterColor = FMath::Lerp(
                        SmoothNearFieldWaterColor,
                        WetClayBedReflection,
                        FMath::Clamp(
                            SmoothPreviewStep(0.10f, 0.50f, 1.0f - SmoothNearFieldRefractionThread) *
                                SmoothPreviewStep(0.24f, 0.90f, SmoothNearFieldFineRipple) *
                                LongFeather *
                                0.30f,
                            0.0f,
                            0.32f));
                    SmoothNearFieldWaterColor = FMath::Lerp(
                        SmoothNearFieldWaterColor,
                        BrightMistSkyReflection,
                        FMath::Clamp(
                            SmoothPreviewStep(0.56f, 0.94f, SmoothNearFieldRefractionThread) *
                                SmoothPreviewStep(0.52f, 0.96f, SmoothNearFieldRipple) *
                                CenterT *
                                LongFeather *
                                FMath::Clamp(Spec.FlowFoamScale, 0.70f, 1.40f) *
                                0.30f,
                            0.0f,
                            0.32f));
                }
                SmoothNearFieldWaterColor = FMath::Lerp(
                    SmoothNearFieldWaterColor,
                    NearFieldFoamFleck,
                    FMath::Clamp(
                        SmoothPreviewStep(0.82f, 0.985f, SmoothNearFieldRipple) *
                            SmoothPreviewStep(0.55f, 0.96f, SmoothNearFieldFineRipple) *
                            CenterT *
                            LongFeather *
                            FMath::Clamp(Spec.FlowFoamScale, 0.70f, 1.40f) *
                            (Spec.bDesertCanyon ? 0.24f : 0.30f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.26f : 0.32f));
                const float ContinuousNearFieldCurrentThread = FMath::Clamp(
                    0.50f +
                        0.33f * FMath::Sin(X * 0.0058f + Lateral * 0.0042f + Spec.FlowCurrentCueScale * 0.21f) +
                        0.22f * FMath::Sin(X * 0.0145f - Lateral * 0.0105f + CenterT * 0.64f) +
                        0.13f * FMath::Sin(X * 0.0300f + Lateral * 0.0205f + SmoothNearFieldRipple * 0.43f),
                    0.0f,
                    1.0f);
                const float ContinuousNearFieldCurrentShear = FMath::Clamp(
                    0.50f +
                        0.30f * FMath::Sin(X * 0.0090f - Lateral * 0.0130f + SmoothNearFieldBand * 0.37f) +
                        0.21f * FMath::Sin(X * 0.0215f + Lateral * 0.0250f + Spec.FlowFoamScale * 0.29f) +
                        0.15f * FMath::Sin(X * 0.0430f - Lateral * 0.0390f + EdgeT * 0.58f),
                    0.0f,
                    1.0f);
                FLinearColor ContinuousNearFieldCurrentColor = FMath::Lerp(
                    NearFieldCurrentShadow,
                    NearFieldCurrentDepth,
                    FMath::Clamp(CenterT * 0.54f + ContinuousNearFieldCurrentThread * 0.22f, 0.0f, 1.0f));
                ContinuousNearFieldCurrentColor = FMath::Lerp(
                    ContinuousNearFieldCurrentColor,
                    NearFieldCurrentHighlight,
                    FMath::Clamp(
                        SmoothPreviewStep(0.58f, 0.94f, ContinuousNearFieldCurrentShear) *
                            (Spec.bDesertCanyon ? 0.24f : 0.16f + CenterT * 0.14f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.34f : 0.30f));
                ContinuousNearFieldCurrentColor = FMath::Lerp(
                    ContinuousNearFieldCurrentColor,
                    Spec.bDesertCanyon ? RiverBedWarmMottle : SkyReflectionMottle,
                    FMath::Clamp(
                        SmoothPreviewStep(0.42f, 0.88f, ContinuousNearFieldCurrentThread) *
                            (Spec.bDesertCanyon ? 0.26f : 0.22f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.30f : 0.24f));
                SmoothNearFieldWaterColor = FMath::Lerp(
                    SmoothNearFieldWaterColor,
                    ContinuousNearFieldCurrentColor,
                    FMath::Clamp(
                        ContinuousNearFieldWaterCurrentBlendT *
                            LongFeather *
                            (0.14f + CenterT * 0.16f +
                             SmoothPreviewStep(0.54f, 0.92f, ContinuousNearFieldCurrentShear) * 0.08f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.42f : 0.34f));
                const float ContinuousNearFieldWaterFineChromaThread = FMath::Clamp(
                    0.50f +
                        0.28f * FMath::Sin(X * 0.070f + Lateral * 0.049f + Spec.FlowCurrentCueScale * 0.17f) +
                        0.20f * FMath::Sin(X * 0.137f - Lateral * 0.081f + SmoothNearFieldCrossThread * 0.43f) +
                        0.12f * FMath::Sin(X * 0.211f + Lateral * 0.153f + CenterT * 0.51f),
                    0.0f,
                    1.0f);
                const float ContinuousNearFieldWaterFineValueThread = FMath::Clamp(
                    0.50f +
                        0.24f * FMath::Sin(X * 0.054f - Lateral * 0.061f + SmoothNearFieldFineRipple * 0.39f) +
                        0.18f * FMath::Sin(X * 0.122f + Lateral * 0.094f + Spec.FlowFoamScale * 0.23f) +
                        0.13f * FMath::Sin(X * 0.196f - Lateral * 0.141f + EdgeT * 0.47f),
                    0.0f,
                    1.0f);
                const FLinearColor ContinuousFineCurrentCool = Spec.bDesertCanyon
                    ? FLinearColor(0.210f, 0.285f, 0.285f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.018f, 0.155f, 0.070f)
                                            : FLinearColor(0.040f, 0.190f, 0.105f));
                const FLinearColor ContinuousFineCurrentWarm = Spec.bDesertCanyon
                    ? FLinearColor(0.685f, 0.500f, 0.255f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.145f, 0.500f, 0.205f)
                                            : FLinearColor(0.220f, 0.420f, 0.225f));
                const FLinearColor ContinuousFineCurrentFoam = Spec.bDesertCanyon
                    ? FLinearColor(0.820f, 0.760f, 0.555f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.710f, 0.900f, 0.670f)
                                            : FLinearColor(0.690f, 0.840f, 0.660f));
                FLinearColor ContinuousFineCurrentColor = FMath::Lerp(
                    ContinuousFineCurrentCool,
                    ContinuousFineCurrentWarm,
                    SmoothPreviewStep(0.16f, 0.88f, ContinuousNearFieldWaterFineChromaThread));
                ContinuousFineCurrentColor = ScalePreviewColor(
                    ContinuousFineCurrentColor,
                    FMath::Clamp(
                        0.72f + ContinuousNearFieldWaterFineValueThread * (Spec.bDesertCanyon ? 0.58f : 0.46f),
                        0.58f,
                        Spec.bDesertCanyon ? 1.44f : (Spec.bHasWaterfalls ? 1.68f : 1.34f)));
                ContinuousFineCurrentColor = FMath::Lerp(
                    ContinuousFineCurrentColor,
                    ContinuousFineCurrentFoam,
                    FMath::Clamp(
                        SmoothPreviewStep(0.84f, 0.985f, ContinuousNearFieldWaterFineChromaThread) *
                            SmoothPreviewStep(0.64f, 0.97f, ContinuousNearFieldWaterFineValueThread) *
                            CenterT *
                            LongFeather *
                            (Spec.bDesertCanyon ? 0.24f : 0.30f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.26f : 0.32f));
                SmoothNearFieldWaterColor = FMath::Lerp(
                    SmoothNearFieldWaterColor,
                    ContinuousFineCurrentColor,
                    FMath::Clamp(
                        LongFeather *
                            (Spec.bDesertCanyon ? 0.24f : (Spec.bHasWaterfalls ? 0.42f : 0.18f)) *
                            (0.68f + CenterT * 0.26f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.30f : (Spec.bHasWaterfalls ? 0.52f : 0.24f)));
                const float ResidualSourceConditionedWaterTextureT = FMath::Clamp(
                    (1.0f - NearFieldWaterSourceTileDemotionT) * 0.055f,
                    0.0f,
                    0.025f);
                SmoothNearFieldWaterColor = FMath::Lerp(
                    SmoothNearFieldWaterColor,
                    WaterColor,
                    ResidualSourceConditionedWaterTextureT);
                WaterColor = ScalePreviewColor(
                    SmoothNearFieldWaterColor,
                    FMath::Clamp(
                        0.38f + SmoothNearFieldRipple * 0.34f + SmoothNearFieldFineRipple * 0.42f +
                            SmoothNearFieldBand * 0.20f + SmoothNearFieldCrossThread * 0.28f +
                            SmoothNearFieldRefractionThread * 0.24f,
                        0.34f,
                        Spec.bDesertCanyon ? 1.56f : 1.62f));
                WaterColor.R = FMath::Clamp(
                    WaterColor.R *
                        (0.82f + SmoothNearFieldCrossThread * 0.26f +
                         SmoothPreviewStep(0.12f, 0.52f, 1.0f - SmoothNearFieldRefractionThread) * 0.24f),
                    0.0f,
                    1.0f);
                WaterColor.G = FMath::Clamp(
                    WaterColor.G *
                        (0.78f + SmoothNearFieldRipple * 0.30f + SmoothNearFieldRefractionThread * 0.30f +
                         (Spec.bHasWaterfalls ? SmoothNearFieldCrossThread * 0.08f : 0.0f)),
                    0.0f,
                    1.0f);
                WaterColor.B = FMath::Clamp(
                    WaterColor.B *
                        (0.74f + SmoothPreviewStep(0.52f, 0.94f, SmoothNearFieldCrossThread) * 0.34f +
                         SmoothNearFieldFineRipple * 0.28f +
                         (Spec.bHasWaterfalls ? SmoothNearFieldRefractionThread * 0.10f : 0.0f)),
                    0.0f,
                    1.0f);
                if (Spec.bHasWaterfalls)
                {
                    const float RainforestHueThread = FMath::Clamp(
                        0.50f +
                            0.32f * FMath::Sin(X * 0.0062f + Lateral * 0.0185f + SmoothNearFieldBand * 0.71f) +
                            0.25f * FMath::Sin(X * 0.0200f - Lateral * 0.0320f + SmoothNearFieldRipple * 0.53f) +
                            0.15f * FMath::Sin(X * 0.0470f + Lateral * 0.0560f + SmoothNearFieldFineRipple * 0.37f),
                        0.0f,
                        1.0f);
                    const FLinearColor DeepCanopySlick = FLinearColor(0.016f, 0.125f, 0.045f);
                    const FLinearColor ClayShelfGlow = FLinearColor(0.285f, 0.390f, 0.120f);
                    const FLinearColor MistSkyGlint = FLinearColor(0.420f, 0.900f, 0.700f);
                    WaterColor = FMath::Lerp(
                        WaterColor,
                        DeepCanopySlick,
                        FMath::Clamp(
                            SmoothPreviewStep(0.08f, 0.40f, 1.0f - RainforestHueThread) *
                                CenterT *
                                LongFeather *
                            0.44f,
                            0.0f,
                            0.32f));
                    WaterColor = FMath::Lerp(
                        WaterColor,
                        ClayShelfGlow,
                        FMath::Clamp(
                            SmoothPreviewStep(0.18f, 0.54f, 1.0f - SmoothNearFieldRefractionThread) *
                                SmoothPreviewStep(0.28f, 0.88f, RainforestHueThread) *
                                LongFeather *
                                0.42f,
                            0.0f,
                            0.42f));
                    WaterColor = FMath::Lerp(
                        WaterColor,
                        MistSkyGlint,
                        FMath::Clamp(
                            SmoothPreviewStep(0.58f, 0.96f, RainforestHueThread) *
                                SmoothPreviewStep(0.52f, 0.94f, SmoothNearFieldRipple) *
                                CenterT *
                                LongFeather *
                                FMath::Clamp(Spec.FlowFoamScale, 0.70f, 1.40f) *
                                0.46f,
                            0.0f,
                            0.48f));
                    WaterColor = ScalePreviewColor(
                        WaterColor,
                        FMath::Clamp(
                            0.58f + RainforestHueThread * 0.48f +
                                SmoothNearFieldRefractionThread * 0.30f + SmoothNearFieldFineRipple * 0.28f,
                            0.48f,
                            2.04f));
                }
                const float FirstPartyIntegratedRiverEyeWaterEntropyCell = FMath::Frac(
                    FMath::Sin(static_cast<float>((XIndex + 1499) * 3181 + (CrossIndex + 733) * 4447) * 12.9898f) *
                    43758.5453f);
                const float FirstPartyIntegratedRiverEyeWaterEntropyThread = FMath::Clamp(
                    0.50f +
                        0.34f * FMath::Sin(X * 0.083f + Lateral * 0.071f + SmoothNearFieldBand * 0.47f) +
                        0.25f * FMath::Sin(X * 0.171f - Lateral * 0.097f + SmoothNearFieldRipple * 0.61f) +
                        0.17f * FMath::Sin(X * 0.257f + Lateral * 0.189f + FirstPartyIntegratedRiverEyeWaterEntropyCell * 4.3f),
                    0.0f,
                    1.0f);
                const float FirstPartyIntegratedRiverEyeWaterEntropyNoise = FMath::Clamp(
                    FirstPartyIntegratedRiverEyeWaterEntropyThread * 0.82f +
                        FirstPartyIntegratedRiverEyeWaterEntropyCell * 0.18f,
                    0.0f,
                    1.0f);
                const FLinearColor IntegratedRiverEyeWaterEntropyDark = Spec.bDesertCanyon
                    ? FLinearColor(0.245f, 0.195f, 0.115f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.018f, 0.145f, 0.065f)
                                            : FLinearColor(0.035f, 0.165f, 0.090f));
                const FLinearColor IntegratedRiverEyeWaterEntropyMid = Spec.bDesertCanyon
                    ? FLinearColor(0.560f, 0.415f, 0.235f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.100f, 0.360f, 0.155f)
                                            : FLinearColor(0.150f, 0.360f, 0.205f));
                const FLinearColor IntegratedRiverEyeWaterEntropyBright = Spec.bDesertCanyon
                    ? FLinearColor(0.780f, 0.690f, 0.470f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.420f, 0.790f, 0.520f)
                                            : FLinearColor(0.480f, 0.760f, 0.560f));
                const FLinearColor IntegratedRiverEyeWaterEntropyColor =
                    FirstPartyIntegratedRiverEyeWaterEntropyNoise < 0.30f
                        ? IntegratedRiverEyeWaterEntropyDark
                        : (FirstPartyIntegratedRiverEyeWaterEntropyNoise < 0.70f
                               ? IntegratedRiverEyeWaterEntropyMid
                               : IntegratedRiverEyeWaterEntropyBright);
                WaterColor = FMath::Lerp(
                    WaterColor,
                    IntegratedRiverEyeWaterEntropyColor,
                    FMath::Clamp(
                        LongFeather *
                            (0.04f + CenterT * 0.05f + EdgeT * 0.02f) *
                            (Spec.bHasWaterfalls ? 1.34f : (Spec.bDesertCanyon ? 1.10f : 1.0f)) *
                            (0.68f + FirstPartyIntegratedRiverEyeWaterEntropyNoise * 0.32f),
                        0.0f,
                        Spec.bHasWaterfalls ? 0.12f : (Spec.bDesertCanyon ? 0.10f : 0.09f)));
                WaterColor = ScalePreviewColor(
                    WaterColor,
                    FMath::Clamp(
                        0.90f + FirstPartyIntegratedRiverEyeWaterEntropyNoise * 0.16f +
                            FirstPartyIntegratedRiverEyeWaterEntropyCell * 0.08f,
                        0.82f,
                        Spec.bHasWaterfalls ? 1.20f : 1.18f));
                const float NearFieldForegroundOverlayLongT =
                    1.0f - SmoothPreviewStep(-5400.0f, 1400.0f, X);
                const float NearFieldForegroundOverlayCenterT = SmoothPreviewStep(0.10f, 0.88f, CenterT);
                const float NearFieldForegroundOverlayDemotionT = FMath::Clamp(
                    NearFieldForegroundOverlayLongT * NearFieldForegroundOverlayCenterT * LongFeather,
                    0.0f,
                    1.0f);
                const FLinearColor NearFieldForegroundOverlayReviewFill = Spec.bDesertCanyon
                    ? FLinearColor(0.520f, 0.415f, 0.270f, 1.0f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.110f, 0.370f, 0.200f, 1.0f)
                                            : FLinearColor(0.145f, 0.380f, 0.230f, 1.0f));
                const FLinearColor NearFieldForegroundOverlayMutedWater = FMath::Lerp(
                    FMath::Lerp(Spec.WaterColor, NearFieldCurrentDepth, Spec.bDesertCanyon ? 0.18f : 0.22f),
                    NearFieldForegroundOverlayReviewFill,
                    Spec.bDesertCanyon ? 0.34f : 0.40f);
                WaterColor = FMath::Lerp(
                    WaterColor,
                    NearFieldForegroundOverlayMutedWater,
                    FMath::Clamp(NearFieldForegroundOverlayDemotionT * 0.96f, 0.0f, 0.96f));
                const float NearFieldForegroundOverlayLumaFloor =
                    Spec.bDesertCanyon ? 0.40f : (Spec.bHasWaterfalls ? 0.30f : 0.32f);
                const float NearFieldForegroundOverlayLuma = GetPreviewColorLuma(WaterColor);
                if (NearFieldForegroundOverlayLuma < NearFieldForegroundOverlayLumaFloor)
                {
                    WaterColor = FMath::Lerp(
                        WaterColor,
                        ScalePreviewColor(
                            WaterColor,
                            NearFieldForegroundOverlayLumaFloor /
                                FMath::Max(NearFieldForegroundOverlayLuma, 0.001f)),
                        FMath::Clamp(NearFieldForegroundOverlayDemotionT * 0.92f, 0.0f, 0.92f));
                }
                const float SurfaceWave =
                    (FMath::Sin(X * 0.011f + Lateral * 0.008f) * (Spec.bDesertCanyon ? 0.36f : 0.48f) +
                     FMath::Sin(X * 0.024f - Lateral * 0.015f) * (Spec.bDesertCanyon ? 0.20f : 0.28f) +
                     (SmoothNearFieldRipple - 0.5f) * (Spec.bDesertCanyon ? 0.34f : 0.46f) +
                     (SmoothNearFieldCrossThread - 0.5f) * (Spec.bDesertCanyon ? 0.22f : 0.30f) +
                     (SmoothNearFieldFineRipple - 0.5f) * (Spec.bDesertCanyon ? 0.18f : 0.24f)) *
                    LongFeather *
                    (1.0f - NearFieldForegroundOverlayDemotionT * 0.82f);
                const float NearFieldWaterTextureZOffsetCm = 26.0f;
                Vertices.Add(FVector(
                    X,
                    CenterY + Lateral,
                    WaterBaseZ + NearFieldWaterTextureZOffsetCm + SurfaceWave * 0.72f));
                UVs.Add(FVector2D(U * 18.0f, V * 3.4f));
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

        Normals.SetNum(Vertices.Num());
        for (FVector& Normal : Normals)
        {
            Normal = FVector::UpVector;
        }
        AddPreviewProceduralMeshActor(
            World,
            FString::Printf(TEXT("RaftSim_NearFieldCaptureQualityWaterTexture_%s"), *Spec.RiverId),
            Vertices,
            Triangles,
            Normals,
            UVs,
            Spec.WaterColor,
            LoadOrCreatePreviewWaterVertexColorMaterial(),
            &VertexColors);
    }

    {
        constexpr int32 RibbonCount = 24;
        constexpr int32 RibbonSegments = 9;
        TArray<FVector> Vertices;
        TArray<FVector> Normals;
        TArray<FVector2D> UVs;
        TArray<FLinearColor> VertexColors;
        TArray<int32> Triangles;
        Vertices.Reserve(RibbonCount * (RibbonSegments + 1) * 2);
        Normals.Reserve(RibbonCount * (RibbonSegments + 1) * 2);
        UVs.Reserve(RibbonCount * (RibbonSegments + 1) * 2);
        VertexColors.Reserve(RibbonCount * (RibbonSegments + 1) * 2);
        Triangles.Reserve(RibbonCount * RibbonSegments * 6);

        for (int32 RibbonIndex = 0; RibbonIndex < RibbonCount; ++RibbonIndex)
        {
            const int32 VertexStart = Vertices.Num();
            const float StartX = -5350.0f + static_cast<float>(RibbonIndex % 12) * 900.0f +
                95.0f * FMath::Sin(static_cast<float>(RibbonIndex) * 1.37f);
            const float Length = (Spec.bDesertCanyon ? 720.0f : 620.0f) *
                (0.72f + 0.34f * FMath::Abs(FMath::Sin(static_cast<float>(RibbonIndex) * 0.71f)));
            const float Side = (RibbonIndex % 2 == 0) ? -1.0f : 1.0f;
            const float LateralCenter = Side * ActiveRiverHalfWidth *
                (0.12f + 0.64f * FMath::Abs(FMath::Sin(static_cast<float>(RibbonIndex) * 0.53f)));
            const float RibbonHalfWidth = (Spec.bDesertCanyon ? 8.0f : 10.0f) +
                15.0f * FMath::Abs(FMath::Sin(static_cast<float>(RibbonIndex) * 0.97f));
            const float Phase = static_cast<float>(RibbonIndex) * 0.83f;

            for (int32 SegmentIndex = 0; SegmentIndex <= RibbonSegments; ++SegmentIndex)
            {
                const float T = static_cast<float>(SegmentIndex) / static_cast<float>(RibbonSegments);
                const float X = StartX + Length * T;
                const float CenterY = GetPreviewRiverCenterY(Spec, X) + LateralCenter +
                    FMath::Sin(Phase + T * UE_TWO_PI) * RibbonHalfWidth * 1.6f;
                const float Taper = FMath::Sin(T * PI);
                const float LocalHalfWidth = FMath::Max(3.0f, RibbonHalfWidth * (0.24f + Taper * 0.88f));
                const float SurfaceWave =
                    FMath::Sin(X * 0.022f + CenterY * 0.015f + Phase) * (Spec.bDesertCanyon ? 2.0f : 2.8f);
                const float Z = WaterBaseZ + 18.0f + SurfaceWave + 1.5f * Taper;
                const float Brightness = 0.72f + 0.24f * Taper +
                    0.10f * FMath::Sin(Phase * 1.3f + T * UE_TWO_PI * 2.0f);
                const FLinearColor FoamColor = ClampPreviewColor(ScalePreviewColor(NearFieldFoamFleck, Brightness));

                Vertices.Add(FVector(X, CenterY - LocalHalfWidth, Z));
                Vertices.Add(FVector(X, CenterY + LocalHalfWidth, Z + 0.8f));
                UVs.Add(FVector2D(T, 0.0f));
                UVs.Add(FVector2D(T, 1.0f));
                VertexColors.Add(FoamColor);
                VertexColors.Add(ScalePreviewColor(FoamColor, 0.86f));
            }

            for (int32 SegmentIndex = 0; SegmentIndex < RibbonSegments; ++SegmentIndex)
            {
                const int32 A = VertexStart + SegmentIndex * 2;
                const int32 B = A + 1;
                const int32 C = A + 2;
                const int32 D = A + 3;
                Triangles.Add(A);
                Triangles.Add(C);
                Triangles.Add(B);
                Triangles.Add(B);
                Triangles.Add(C);
                Triangles.Add(D);
            }
        }

        Normals = ComputePreviewMeshNormals(Vertices, Triangles);
        AddPreviewProceduralMeshActor(
            World,
            FString::Printf(TEXT("RaftSim_NearFieldCaptureQualityFoamLace_%s"), *Spec.RiverId),
            Vertices,
            Triangles,
            Normals,
            UVs,
            NearFieldFoamFleck,
            LoadOrCreatePreviewVertexColorMaterial(),
            &VertexColors);
    }

    for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
    {
        constexpr int32 XSteps = 86;
        constexpr int32 CrossSteps = 5;
        const float Side = SideIndex == 0 ? -1.0f : 1.0f;
        const float MinX = -5480.0f;
        const float MaxX = 6200.0f;
        const float NearFieldInboardBankShelfCullT = 1.0f;
        const float ContinuousNearFieldBankShelfRailDemotion = 0.0f;
        if (ContinuousNearFieldBankShelfRailDemotion <= KINDA_SMALL_NUMBER)
        {
            continue;
        }
        const float InnerOffset = ActiveRiverHalfWidth +
            (Spec.bDesertCanyon ? 164.0f : 92.0f) * NearFieldInboardBankShelfCullT;
        const float OuterOffset = ActiveRiverHalfWidth +
            (Spec.bDesertCanyon ? 960.0f : 620.0f) * NearFieldInboardBankShelfCullT;

        TArray<FVector> Vertices;
        TArray<FVector> Normals;
        TArray<FVector2D> UVs;
        TArray<FLinearColor> VertexColors;
        TArray<int32> Triangles;
        Vertices.Reserve((XSteps + 1) * (CrossSteps + 1));
        Normals.Reserve((XSteps + 1) * (CrossSteps + 1));
        UVs.Reserve((XSteps + 1) * (CrossSteps + 1));
        VertexColors.Reserve((XSteps + 1) * (CrossSteps + 1));
        Triangles.Reserve(XSteps * CrossSteps * 6);

        for (int32 XIndex = 0; XIndex <= XSteps; ++XIndex)
        {
            const float U = static_cast<float>(XIndex) / static_cast<float>(XSteps);
            const float X = FMath::Lerp(MinX, MaxX, U);
            const float CenterY = GetPreviewRiverCenterY(Spec, X);
            const float LongFeather = SmoothPreviewStep(0.0f, 0.05f, U) * (1.0f - SmoothPreviewStep(0.90f, 1.0f, U));
            for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
            {
                const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
                const float Offset = FMath::Lerp(InnerOffset, OuterOffset, V);
                const float Y = CenterY + Side * Offset;
                const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
                const float ShelfNoise = FMath::Clamp(
                    0.50f +
                        0.34f * FMath::Sin(X * 0.018f + Y * 0.011f) +
                        0.22f * FMath::Sin(X * 0.047f - Y * 0.025f),
                    0.0f,
                    1.0f);
                const float Z = FMath::Max(TerrainZ + 8.0f + ShelfNoise * 8.0f, WaterBaseZ + 11.0f + V * 22.0f) *
                    LongFeather +
                    (1.0f - LongFeather) * (WaterBaseZ - 40.0f);
                FLinearColor ShelfColor = FMath::Lerp(
                    ScalePreviewColor(Spec.RockColor, Spec.bDesertCanyon ? 0.86f : 0.74f),
                    ScalePreviewColor(Spec.FoliageColor, Spec.bDesertCanyon ? 0.78f : 1.10f),
                    Spec.bDesertCanyon ? FMath::Clamp(ShelfNoise * 0.28f, 0.0f, 0.24f)
                                       : FMath::Clamp(0.20f + ShelfNoise * 0.42f, 0.0f, 0.62f));
                ShelfColor = FMath::Lerp(
                    ShelfColor,
                    ScalePreviewColor(Spec.WaterColor, 0.58f),
                    FMath::Clamp((1.0f - V) * 0.34f, 0.0f, 0.34f));
                ShelfColor = ScalePreviewColor(
                    ShelfColor,
                    0.86f + 0.20f * ShelfNoise + 0.08f * FMath::Sin(X * 0.071f + Y * 0.037f));
                Vertices.Add(FVector(X, Y, Z));
                UVs.Add(FVector2D(U * 10.0f, V));
                VertexColors.Add(ClampPreviewColor(ShelfColor));
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
        AddPreviewProceduralMeshActor(
            World,
            FString::Printf(TEXT("RaftSim_NearFieldPhotorealBankShelf_%d_%s"), SideIndex, *Spec.RiverId),
            Vertices,
            Triangles,
            Normals,
            UVs,
            Spec.RockColor,
            LoadOrCreatePreviewVertexColorMaterial(),
            &VertexColors);
    }

    {
        const int32 NearFieldPebbleCount = Spec.bDesertCanyon ? 94 : (Spec.bHasWaterfalls ? 86 : 78);
        for (int32 PebbleIndex = 0; PebbleIndex < NearFieldPebbleCount; ++PebbleIndex)
        {
            const float Side = (PebbleIndex % 2 == 0) ? -1.0f : 1.0f;
            const float SequenceT = static_cast<float>(PebbleIndex / 2) /
                static_cast<float>(FMath::Max(1, NearFieldPebbleCount / 2 - 1));
            const float Phase = static_cast<float>(PebbleIndex) * 1.379f;
            const float BaseX = FMath::Lerp(-5320.0f, 7050.0f, SequenceT) +
                145.0f * FMath::Sin(Phase * 0.83f) +
                58.0f * FMath::Sin(Phase * 1.61f);

            float BestX = BaseX;
            float BestOffset = ActiveRiverHalfWidth * (Spec.bDesertCanyon ? 0.96f : 0.90f);
            float BestScore = -1000.0f;
            for (int32 CandidateIndex = 0; CandidateIndex < 6; ++CandidateIndex)
            {
                const float CandidateX = BaseX + 94.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.17f);
                const float CandidateOffset = ActiveRiverHalfWidth *
                        (Spec.bDesertCanyon ? 0.78f : 0.72f) +
                    (Spec.bDesertCanyon ? 112.0f : 76.0f) * static_cast<float>(CandidateIndex) +
                    (Spec.bDesertCanyon ? 48.0f : 36.0f) *
                        FMath::Abs(FMath::Sin(Phase * 0.57f + static_cast<float>(CandidateIndex) * 0.41f));
                const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
                const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
                const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
                const float WaterlineT = 1.0f - FMath::Clamp(FMath::Abs(WaterT - 0.46f) / 0.52f, 0.0f, 1.0f);
                const float NearCameraT = 1.0f - SmoothPreviewStep(6200.0f, 7800.0f, CandidateX);
                const float Score = WaterlineT * 1.10f + NearCameraT * 0.24f +
                    (Spec.bHasWaterfalls ? VegetationT * 0.14f : -VegetationT * 0.20f) +
                    0.04f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.71f);
                if (Score > BestScore)
                {
                    BestScore = Score;
                    BestX = CandidateX;
                    BestOffset = CandidateOffset;
                }
            }

            const float X = BestX;
            const float Y = GetPreviewRiverCenterY(Spec, X) + Side * BestOffset;
            const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, Y);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, X, Y);
            const float SizeNoise =
                0.70f + 0.10f * static_cast<float>(PebbleIndex % 7) + 0.12f * FMath::Abs(FMath::Sin(Phase * 0.91f));
            const FVector PebbleScale = Spec.bDesertCanyon
                ? FVector(0.078f * SizeNoise, 0.040f * SizeNoise, 0.012f * SizeNoise)
                : FVector(
                      (Spec.bHasWaterfalls ? 0.052f : 0.060f) * SizeNoise,
                      (Spec.bHasWaterfalls ? 0.032f : 0.035f) * SizeNoise,
                      0.010f * SizeNoise);
            const FLinearColor DryPebbleColor = Spec.bDesertCanyon
                ? FMath::Lerp(FLinearColor(0.50f, 0.34f, 0.20f), FLinearColor(0.70f, 0.52f, 0.33f), 0.32f + 0.18f * FMath::Sin(Phase))
                : (Spec.bHasWaterfalls
                      ? FMath::Lerp(FLinearColor(0.034f, 0.052f, 0.040f), FLinearColor(0.080f, 0.125f, 0.064f), VegetationT * 0.52f)
                      : FMath::Lerp(FLinearColor(0.165f, 0.160f, 0.122f), FLinearColor(0.300f, 0.268f, 0.170f), 0.30f + VegetationT * 0.22f));
            const FLinearColor WetPebbleColor = FMath::Lerp(
                ScalePreviewColor(Spec.RockColor, Spec.bDesertCanyon ? 0.42f : 0.36f),
                ScalePreviewColor(Spec.WaterColor, Spec.bDesertCanyon ? 0.32f : 0.28f),
                Spec.bDesertCanyon ? 0.22f : 0.40f);
            const FLinearColor PebbleColor = FMath::Lerp(
                DryPebbleColor,
                WetPebbleColor,
                FMath::Clamp(0.18f + WaterT * 0.48f, 0.0f, 0.64f));
            const float PebbleZ = FMath::Max(
                TerrainZ + (Spec.bDesertCanyon ? 5.0f : 4.5f),
                WaterBaseZ + 2.5f + WaterT * 4.0f);
            AActor* PebbleActor = AddPreviewIrregularRockActor(
                World,
                FString::Printf(TEXT("RaftSim_NearFieldRiverbedPebbleDressing_%03d_%s"), PebbleIndex, *Spec.RiverId),
                FVector(X, Y, PebbleZ),
                static_cast<float>((PebbleIndex * 47) % 360),
                PebbleScale,
                ScalePreviewColor(PebbleColor, 0.84f + 0.05f * static_cast<float>(PebbleIndex % 5)),
                PebbleIndex + 18100);
            DisablePreviewProceduralMeshCollision(PebbleActor);
        }
    }

    {
        const int32 DebrisCount = Spec.bDesertCanyon ? 112 : (Spec.bHasWaterfalls ? 154 : 128);
        TArray<FVector> Vertices;
        TArray<FVector> Normals;
        TArray<FVector2D> UVs;
        TArray<FLinearColor> VertexColors;
        TArray<int32> Triangles;
        Vertices.Reserve(DebrisCount * 4);
        UVs.Reserve(DebrisCount * 4);
        VertexColors.Reserve(DebrisCount * 4);
        Triangles.Reserve(DebrisCount * 6);

        for (int32 DebrisIndex = 0; DebrisIndex < DebrisCount; ++DebrisIndex)
        {
            const float Side = (DebrisIndex % 2 == 0) ? -1.0f : 1.0f;
            const float SequenceT = static_cast<float>(DebrisIndex / 2) /
                static_cast<float>(FMath::Max(1, DebrisCount / 2 - 1));
            const float Phase = static_cast<float>(DebrisIndex) * 1.231f;
            const float X = FMath::Lerp(-5420.0f, 8120.0f, SequenceT) +
                170.0f * FMath::Sin(Phase * 0.71f) +
                54.0f * FMath::Sin(Phase * 1.73f);
            const float BankBand = FMath::Frac(FMath::Sin(static_cast<float>(DebrisIndex + 23) * 23.517f) * 43758.5453f);
            const float NearCameraInWaterDebrisOcclusionCullT = 1.0f;
            const float Offset = ActiveRiverHalfWidth +
                FMath::Lerp(
                    Spec.bDesertCanyon ? 142.0f : 86.0f,
                    Spec.bDesertCanyon ? 1080.0f : (Spec.bHasWaterfalls ? 760.0f : 670.0f),
                    BankBand) *
                    NearCameraInWaterDebrisOcclusionCullT;
            const float Y = GetPreviewRiverCenterY(Spec, X) + Side * Offset;
            const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, Y);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, X, Y);
            const float Yaw = FMath::DegreesToRadians(38.0f * FMath::Sin(Phase * 0.61f));
            const float Length = (Spec.bDesertCanyon ? 38.0f : (Spec.bHasWaterfalls ? 30.0f : 34.0f)) *
                (0.50f + 0.68f * FMath::Abs(FMath::Sin(Phase * 0.87f)));
            const float Width = (Spec.bDesertCanyon ? 9.0f : (Spec.bHasWaterfalls ? 8.0f : 8.5f)) *
                (0.56f + 0.52f * FMath::Abs(FMath::Sin(Phase * 1.19f)));
            const FVector AxisX(FMath::Cos(Yaw) * Length, FMath::Sin(Yaw) * Length, 0.0f);
            const FVector AxisY(-FMath::Sin(Yaw) * Width, FMath::Cos(Yaw) * Width, 0.0f);
            const float TextureNoise = FMath::Frac(
                FMath::Sin(static_cast<float>((DebrisIndex + 71) * 487) * 12.9898f) * 43758.5453f);

            FLinearColor DebrisColor;
            if (Spec.bDesertCanyon)
            {
                const FLinearColor Sand = FLinearColor(0.68f, 0.50f, 0.30f);
                const FLinearColor WetSilt = FLinearColor(0.43f, 0.32f, 0.205f);
                const FLinearColor Driftwood = FLinearColor(0.36f, 0.265f, 0.170f);
                DebrisColor = TextureNoise < 0.34f ? Sand : (TextureNoise < 0.68f ? WetSilt : Driftwood);
            }
            else if (Spec.bHasWaterfalls)
            {
                const FLinearColor WetLeaf = FLinearColor(0.060f, 0.105f, 0.038f);
                const FLinearColor DarkLeaf = FLinearColor(0.030f, 0.055f, 0.024f);
                const FLinearColor MossStem = FLinearColor(0.090f, 0.160f, 0.055f);
                DebrisColor = TextureNoise < 0.40f ? DarkLeaf : (TextureNoise < 0.76f ? WetLeaf : MossStem);
            }
            else
            {
                const FLinearColor DryLeaf = FLinearColor(0.31f, 0.27f, 0.125f);
                const FLinearColor WetGrass = FLinearColor(0.15f, 0.205f, 0.075f);
                const FLinearColor GraniteFlake = FLinearColor(0.26f, 0.250f, 0.178f);
                DebrisColor = TextureNoise < 0.36f ? GraniteFlake : (TextureNoise < 0.72f ? DryLeaf : WetGrass);
            }
            DebrisColor = FMath::Lerp(
                DebrisColor,
                ScalePreviewColor(Spec.WaterColor, Spec.bDesertCanyon ? 0.42f : 0.34f),
                FMath::Clamp(WaterT * 0.22f, 0.0f, 0.30f));
            DebrisColor = FMath::Lerp(
                DebrisColor,
                Spec.FoliageColor,
                FMath::Clamp(VegetationT * (Spec.bDesertCanyon ? 0.08f : 0.16f), 0.0f, Spec.bDesertCanyon ? 0.12f : 0.22f));
            DebrisColor = ScalePreviewColor(DebrisColor, 0.76f + 0.36f * TextureNoise);

            const FVector Center(
                X,
                Y,
                FMath::Max(TerrainZ + 7.0f + 4.0f * TextureNoise, WaterBaseZ + 2.0f + WaterT * 2.0f));
            const int32 VertexStart = Vertices.Num();
            Vertices.Add(Center - AxisX - AxisY);
            Vertices.Add(Center + AxisX - AxisY);
            Vertices.Add(Center - AxisX + AxisY);
            Vertices.Add(Center + AxisX + AxisY);
            UVs.Add(FVector2D(0.0f, 0.0f));
            UVs.Add(FVector2D(1.0f, 0.0f));
            UVs.Add(FVector2D(0.0f, 1.0f));
            UVs.Add(FVector2D(1.0f, 1.0f));
            VertexColors.Add(ClampPreviewColor(ScalePreviewColor(DebrisColor, 0.78f)));
            VertexColors.Add(ClampPreviewColor(DebrisColor));
            VertexColors.Add(ClampPreviewColor(ScalePreviewColor(DebrisColor, 1.08f)));
            VertexColors.Add(ClampPreviewColor(ScalePreviewColor(DebrisColor, 0.88f)));
            Triangles.Add(VertexStart);
            Triangles.Add(VertexStart + 2);
            Triangles.Add(VertexStart + 1);
            Triangles.Add(VertexStart + 1);
            Triangles.Add(VertexStart + 2);
            Triangles.Add(VertexStart + 3);
        }

        Normals = ComputePreviewMeshNormals(Vertices, Triangles);
        AActor* DebrisActor = AddPreviewProceduralMeshActor(
            World,
            FString::Printf(TEXT("RaftSim_NearFieldRiverbedDebrisDressing_%s"), *Spec.RiverId),
            Vertices,
            Triangles,
            Normals,
            UVs,
            Spec.TerrainColor,
            LoadOrCreatePreviewVertexColorMaterial(),
            &VertexColors);
        DisablePreviewProceduralMeshCollision(DebrisActor);
    }

    for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
    {
        constexpr int32 XSteps = 132;
        constexpr int32 CrossSteps = 18;
        const float Side = SideIndex == 0 ? -1.0f : 1.0f;
        const float MinX = -5600.0f;
        const float MaxX = 24800.0f;
        const float InnerOffset = ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 420.0f : 260.0f);
        const float OuterOffset = Spec.bDesertCanyon ? 4700.0f : (Spec.bHasWaterfalls ? 3400.0f : 3600.0f);

        TArray<FVector> Vertices;
        TArray<FVector> Normals;
        TArray<FVector2D> UVs;
        TArray<FLinearColor> VertexColors;
        TArray<int32> Triangles;
        Vertices.Reserve((XSteps + 1) * (CrossSteps + 1));
        Normals.Reserve((XSteps + 1) * (CrossSteps + 1));
        UVs.Reserve((XSteps + 1) * (CrossSteps + 1));
        VertexColors.Reserve((XSteps + 1) * (CrossSteps + 1));
        Triangles.Reserve(XSteps * CrossSteps * 6);

        for (int32 XIndex = 0; XIndex <= XSteps; ++XIndex)
        {
            const float U = static_cast<float>(XIndex) / static_cast<float>(XSteps);
            const float X = FMath::Lerp(MinX, MaxX, U);
            const float CenterY = GetPreviewRiverCenterY(Spec, X);
            const float LongFeather = SmoothPreviewStep(0.0f, 0.035f, U) * (1.0f - SmoothPreviewStep(0.965f, 1.0f, U));
            for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
            {
                const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
                const float Offset = FMath::Lerp(InnerOffset, OuterOffset, V);
                const float Y = CenterY + Side * Offset;
                const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
                const float DrapeNoise = FMath::Clamp(
                    0.50f +
                        0.32f * FMath::Sin(X * 0.0064f + Y * 0.0048f) +
                        0.23f * FMath::Sin(X * 0.0180f - Y * 0.0120f) +
                        0.14f * FMath::Sin(X * 0.0410f + Y * 0.0290f),
                    0.0f,
                    1.0f);
                const float DrapeCell = FMath::Frac(
                    FMath::Sin(static_cast<float>((XIndex + 97) * 191 + (CrossIndex + 43) * 337) * 12.9898f) *
                    43758.5453f);
                const float TextureNoise = FMath::Clamp(DrapeNoise * 0.66f + DrapeCell * 0.34f, 0.0f, 1.0f);
                const float MaterialStrataNoise = FMath::Clamp(
                    0.50f +
                        0.29f * FMath::Sin(X * 0.010f + Y * 0.007f) +
                        0.23f * FMath::Sin(X * 0.026f - Y * 0.018f) +
                        0.17f * FMath::Sin(X * 0.063f + Y * 0.041f),
                    0.0f,
                    1.0f);
                const FLinearColor BankBase = Spec.bDesertCanyon
                    ? FMath::Lerp(Spec.TerrainColor, Spec.RockColor, 0.54f)
                    : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.TerrainColor, Spec.FoliageColor, 0.72f)
                                            : FMath::Lerp(Spec.TerrainColor, Spec.FoliageColor, 0.46f));
                const FLinearColor BankShadow = Spec.bDesertCanyon
                    ? FLinearColor(0.300f, 0.190f, 0.110f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.040f, 0.125f, 0.045f)
                                            : FLinearColor(0.135f, 0.180f, 0.075f));
                const FLinearColor BankHighlight = Spec.bDesertCanyon
                    ? FLinearColor(0.640f, 0.405f, 0.230f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.105f, 0.275f, 0.095f)
                                            : FLinearColor(0.405f, 0.365f, 0.205f));
                FLinearColor DrapeColor = FMath::Lerp(BankShadow, BankHighlight, TextureNoise);
                DrapeColor = FMath::Lerp(DrapeColor, BankBase, Spec.bDesertCanyon ? 0.32f : 0.24f);
                DrapeColor = FMath::Lerp(
                    DrapeColor,
                    ScalePreviewColor(Spec.WaterColor, Spec.bDesertCanyon ? 0.72f : 0.58f),
                    FMath::Clamp((1.0f - V) * 0.18f, 0.0f, 0.18f));
                const FLinearColor BankDryStrata = Spec.bDesertCanyon
                    ? FLinearColor(0.700f, 0.455f, 0.255f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.125f, 0.235f, 0.080f)
                                            : FLinearColor(0.455f, 0.405f, 0.210f));
                const FLinearColor BankWetStrata = Spec.bDesertCanyon
                    ? FLinearColor(0.315f, 0.220f, 0.145f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.025f, 0.155f, 0.060f)
                                            : FLinearColor(0.125f, 0.205f, 0.090f));
                const FLinearColor BankLeafLitterStrata = Spec.bDesertCanyon
                    ? FLinearColor(0.515f, 0.310f, 0.165f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.090f, 0.315f, 0.105f)
                                            : FLinearColor(0.290f, 0.320f, 0.125f));
                DrapeColor = FMath::Lerp(
                    DrapeColor,
                    BankDryStrata,
                    FMath::Clamp(
                        SmoothPreviewStep(0.58f, 0.94f, MaterialStrataNoise) *
                            (0.20f + V * 0.16f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.34f : 0.28f));
                DrapeColor = FMath::Lerp(
                    DrapeColor,
                    BankWetStrata,
                    FMath::Clamp(
                        SmoothPreviewStep(0.08f, 0.38f, 1.0f - MaterialStrataNoise) *
                            (0.18f + (1.0f - V) * 0.18f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.26f : 0.32f));
                DrapeColor = FMath::Lerp(
                    DrapeColor,
                    BankLeafLitterStrata,
                    FMath::Clamp(
                        SmoothPreviewStep(0.36f, 0.74f, TextureNoise) *
                            SmoothPreviewStep(0.20f, 0.86f, MaterialStrataNoise) *
                            (Spec.bDesertCanyon ? 0.16f : 0.24f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.20f : 0.30f));
                DrapeColor = ScalePreviewColor(
                    DrapeColor,
                    FMath::Clamp((Spec.bHasWaterfalls ? 1.18f : 1.06f) + TextureNoise * 0.24f, 0.80f, 1.46f));
                if (AerialDrape && AerialDrape->IsValid())
                {
                    float SourceU = 0.0f;
                    float SourceV = 0.0f;
                    GetPreviewMaskUv(Spec, X, Y, SourceU, SourceV);
                    const FLinearColor SourceDrapeColor = NormalizePreviewSourceDrapeAlbedo(
                        Spec,
                        AerialDrape->Sample(SourceU, SourceV),
                        0.0f,
                        Spec.bDesertCanyon ? 0.08f : 0.24f,
                        Spec.bDesertCanyon ? 0.34f : (Spec.bHasWaterfalls ? 0.30f : 0.32f));
                    DrapeColor = FMath::Lerp(
                        DrapeColor,
                        SourceDrapeColor,
                        FMath::Clamp(
                            (Spec.bDesertCanyon ? 0.18f : 0.20f) + TextureNoise * 0.10f + V * 0.04f,
                            0.0f,
                            Spec.bDesertCanyon ? 0.32f : 0.36f));
                }
                const float FinalBankPatchSeed = FMath::Frac(
                    FMath::Sin(static_cast<float>((XIndex + 151) * 367 + (CrossIndex + 89) * 557) * 12.9898f) *
                    43758.5453f);
                const FLinearColor FinalBankPatchColor = FinalBankPatchSeed < 0.24f
                    ? BankWetStrata
                    : (FinalBankPatchSeed < 0.50f
                           ? BankLeafLitterStrata
                           : (FinalBankPatchSeed < 0.74f ? BankDryStrata : BankHighlight));
                DrapeColor = FMath::Lerp(
                    DrapeColor,
                    FinalBankPatchColor,
                    FMath::Clamp(
                        (0.12f + MaterialStrataNoise * 0.18f + V * 0.06f) *
                            (Spec.bDesertCanyon ? 0.90f : 1.0f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.28f : 0.34f));
                const float IntegratedBankEntropyPatchSeed = FMath::Frac(
                    FMath::Sin(static_cast<float>((XIndex + 223) * 479 + (CrossIndex + 137) * 863) * 12.9898f) *
                    43758.5453f);
                const FLinearColor IntegratedBankEntropyShade = Spec.bDesertCanyon
                    ? FLinearColor(0.230f, 0.130f, 0.070f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.018f, 0.095f, 0.028f)
                                            : FLinearColor(0.105f, 0.130f, 0.050f));
                const FLinearColor IntegratedBankEntropyMineral = Spec.bDesertCanyon
                    ? FLinearColor(0.765f, 0.500f, 0.275f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.075f, 0.250f, 0.075f)
                                            : FLinearColor(0.475f, 0.425f, 0.210f));
                const FLinearColor IntegratedBankEntropyWetEdge = Spec.bDesertCanyon
                    ? FLinearColor(0.320f, 0.220f, 0.135f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.025f, 0.165f, 0.055f)
                                            : FLinearColor(0.135f, 0.220f, 0.085f));
                const FLinearColor IntegratedBankEntropyLeaf = Spec.bDesertCanyon
                    ? FLinearColor(0.545f, 0.320f, 0.155f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.105f, 0.350f, 0.095f)
                                            : FLinearColor(0.310f, 0.335f, 0.115f));
                const FLinearColor IntegratedBankEntropyColor = IntegratedBankEntropyPatchSeed < 0.22f
                    ? IntegratedBankEntropyShade
                    : (IntegratedBankEntropyPatchSeed < 0.48f
                           ? IntegratedBankEntropyWetEdge
                           : (IntegratedBankEntropyPatchSeed < 0.74f
                                  ? IntegratedBankEntropyMineral
                                  : IntegratedBankEntropyLeaf));
                DrapeColor = FMath::Lerp(
                    DrapeColor,
                    IntegratedBankEntropyColor,
                    FMath::Clamp(
                        (0.18f + TextureNoise * 0.16f + MaterialStrataNoise * 0.12f) *
                            (0.72f + V * 0.34f),
                        0.0f,
                        Spec.bDesertCanyon ? 0.34f : 0.38f));
                const FLinearColor IntegratedBankEntropyLumaFill = Spec.bDesertCanyon
                    ? FLinearColor(0.455f, 0.300f, 0.175f)
                    : (Spec.bHasWaterfalls ? FLinearColor(0.075f, 0.190f, 0.070f)
                                            : FLinearColor(0.285f, 0.310f, 0.135f));
                const float IntegratedBankEntropyLumaFloor = Spec.bDesertCanyon
                    ? 0.315f
                    : (Spec.bHasWaterfalls ? 0.170f : 0.235f);
                const float IntegratedBankEntropyExistingLuma = GetPreviewColorLuma(DrapeColor);
                if (IntegratedBankEntropyExistingLuma < IntegratedBankEntropyLumaFloor)
                {
                    DrapeColor = FMath::Lerp(
                        DrapeColor,
                        IntegratedBankEntropyLumaFill,
                        FMath::Clamp(
                            ((IntegratedBankEntropyLumaFloor - IntegratedBankEntropyExistingLuma) /
                             IntegratedBankEntropyLumaFloor) *
                                (0.38f + TextureNoise * 0.22f + V * 0.18f),
                            0.0f,
                            Spec.bDesertCanyon ? 0.48f : 0.54f));
                }
                const float Z = TerrainZ + 20.0f + LongFeather * (8.0f + TextureNoise * (Spec.bDesertCanyon ? 18.0f : 12.0f));
                Vertices.Add(FVector(X, Y, Z));
                UVs.Add(FVector2D(U * 12.0f, V * 3.0f));
                VertexColors.Add(ClampPreviewColor(DrapeColor));
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
        AddPreviewProceduralMeshActor(
            World,
            FString::Printf(TEXT("RaftSim_MidFieldSourceColorBankDrape_%d_%s"), SideIndex, *Spec.RiverId),
            Vertices,
            Triangles,
            Normals,
            UVs,
            Spec.TerrainColor,
            LoadOrCreatePreviewVertexColorMaterial(),
            &VertexColors);
    }

    {
        constexpr int32 FleckCount = 520;
        TArray<FVector> Vertices;
        TArray<FVector> Normals;
        TArray<FVector2D> UVs;
        TArray<FLinearColor> VertexColors;
        TArray<int32> Triangles;
        Vertices.Reserve(FleckCount * 4);
        UVs.Reserve(FleckCount * 4);
        VertexColors.Reserve(FleckCount * 4);
        Triangles.Reserve(FleckCount * 6);

        for (int32 FleckIndex = 0; FleckIndex < FleckCount; ++FleckIndex)
        {
            const float Side = (FleckIndex % 2 == 0) ? -1.0f : 1.0f;
            const float LongT = static_cast<float>(FleckIndex / 2) / static_cast<float>(FleckCount / 2);
            const float X = FMath::Lerp(-5350.0f, 23800.0f, LongT) +
                190.0f * FMath::Sin(static_cast<float>(FleckIndex) * 1.73f);
            const float CenterY = GetPreviewRiverCenterY(Spec, X);
            const float BankBandT = FMath::Frac(FMath::Sin(static_cast<float>(FleckIndex + 11) * 18.371f) * 43758.5453f);
            const float Offset = ActiveRiverHalfWidth +
                FMath::Lerp(Spec.bDesertCanyon ? 520.0f : 320.0f, Spec.bDesertCanyon ? 3600.0f : 2120.0f, BankBandT);
            const float Y = CenterY + Side * Offset;
            const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
            const float Yaw = FMath::DegreesToRadians(18.0f * FMath::Sin(static_cast<float>(FleckIndex) * 0.91f));
            const FVector AxisX(
                FMath::Cos(Yaw) * (Spec.bDesertCanyon ? 152.0f : 124.0f) *
                    (0.62f + 0.55f * FMath::Abs(FMath::Sin(static_cast<float>(FleckIndex) * 0.67f))),
                FMath::Sin(Yaw) * (Spec.bDesertCanyon ? 152.0f : 124.0f) *
                    (0.62f + 0.55f * FMath::Abs(FMath::Sin(static_cast<float>(FleckIndex) * 0.67f))),
                0.0f);
            const FVector AxisY(
                -FMath::Sin(Yaw) * (Spec.bDesertCanyon ? 60.0f : 48.0f) *
                    (0.60f + 0.50f * FMath::Abs(FMath::Sin(static_cast<float>(FleckIndex) * 1.07f))),
                FMath::Cos(Yaw) * (Spec.bDesertCanyon ? 60.0f : 48.0f) *
                    (0.60f + 0.50f * FMath::Abs(FMath::Sin(static_cast<float>(FleckIndex) * 1.07f))),
                0.0f);
            const float TextureNoise = FMath::Frac(
                FMath::Sin(static_cast<float>((FleckIndex + 37) * 379) * 12.9898f) * 43758.5453f);
            const FLinearColor BankDark = Spec.bDesertCanyon
                ? FLinearColor(0.250f, 0.150f, 0.085f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.025f, 0.110f, 0.035f)
                                        : FLinearColor(0.125f, 0.150f, 0.060f));
            const FLinearColor BankLight = Spec.bDesertCanyon
                ? FLinearColor(0.720f, 0.460f, 0.255f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.115f, 0.330f, 0.105f)
                                        : FLinearColor(0.455f, 0.410f, 0.225f));
            FLinearColor FleckColor = FMath::Lerp(BankDark, BankLight, TextureNoise);
            const FLinearColor BankMaterialAccent = Spec.bDesertCanyon
                ? FMath::Lerp(FLinearColor(0.755f, 0.495f, 0.280f), FLinearColor(0.350f, 0.205f, 0.110f), BankBandT)
                : (Spec.bHasWaterfalls ? FMath::Lerp(FLinearColor(0.045f, 0.240f, 0.075f), FLinearColor(0.145f, 0.335f, 0.115f), BankBandT)
                                        : FMath::Lerp(FLinearColor(0.485f, 0.430f, 0.215f), FLinearColor(0.135f, 0.225f, 0.085f), BankBandT));
            FleckColor = FMath::Lerp(
                FleckColor,
                BankMaterialAccent,
                FMath::Clamp(0.22f + TextureNoise * 0.18f, 0.0f, 0.42f));
            FleckColor = FMath::Lerp(
                FleckColor,
                Spec.bDesertCanyon ? Spec.RockColor : Spec.FoliageColor,
                Spec.bDesertCanyon ? 0.18f : 0.26f);
            if (AerialDrape && AerialDrape->IsValid())
            {
                float SourceU = 0.0f;
                float SourceV = 0.0f;
                GetPreviewMaskUv(Spec, X, Y, SourceU, SourceV);
                const FLinearColor SourceDrapeColor = NormalizePreviewSourceDrapeAlbedo(
                    Spec,
                    AerialDrape->Sample(SourceU, SourceV),
                    0.0f,
                    Spec.bDesertCanyon ? 0.08f : 0.24f,
                    Spec.bDesertCanyon ? 0.34f : (Spec.bHasWaterfalls ? 0.30f : 0.32f));
                FleckColor = FMath::Lerp(
                    FleckColor,
                    SourceDrapeColor,
                    FMath::Clamp(Spec.bDesertCanyon ? 0.34f : 0.42f, 0.0f, 0.48f));
            }
            FleckColor = ScalePreviewColor(FleckColor, 0.82f + 0.34f * TextureNoise);
            const FVector Center(X, Y, TerrainZ + 34.0f + 10.0f * TextureNoise);
            const int32 VertexStart = Vertices.Num();
            Vertices.Add(Center - AxisX - AxisY);
            Vertices.Add(Center + AxisX - AxisY);
            Vertices.Add(Center - AxisX + AxisY);
            Vertices.Add(Center + AxisX + AxisY);
            UVs.Add(FVector2D(0.0f, 0.0f));
            UVs.Add(FVector2D(1.0f, 0.0f));
            UVs.Add(FVector2D(0.0f, 1.0f));
            UVs.Add(FVector2D(1.0f, 1.0f));
            VertexColors.Add(ClampPreviewColor(ScalePreviewColor(FleckColor, 0.82f)));
            VertexColors.Add(ClampPreviewColor(FleckColor));
            VertexColors.Add(ClampPreviewColor(ScalePreviewColor(FleckColor, 1.08f)));
            VertexColors.Add(ClampPreviewColor(ScalePreviewColor(FleckColor, 0.94f)));
            Triangles.Add(VertexStart);
            Triangles.Add(VertexStart + 2);
            Triangles.Add(VertexStart + 1);
            Triangles.Add(VertexStart + 1);
            Triangles.Add(VertexStart + 2);
            Triangles.Add(VertexStart + 3);
        }

        Normals = ComputePreviewMeshNormals(Vertices, Triangles);
        AddPreviewProceduralMeshActor(
            World,
            FString::Printf(TEXT("RaftSim_CaptureQualityBankTextureFlecks_%s"), *Spec.RiverId),
            Vertices,
            Triangles,
            Normals,
            UVs,
            Spec.TerrainColor,
            LoadOrCreatePreviewVertexColorMaterial(),
            &VertexColors);
    }

    const bool bUseSeparateCaptureQualityWaterFleckCards = false;
    if (bUseSeparateCaptureQualityWaterFleckCards)
    {
        constexpr int32 FleckCount = 760;
        TArray<FVector> Vertices;
        TArray<FVector> Normals;
        TArray<FVector2D> UVs;
        TArray<FLinearColor> VertexColors;
        TArray<int32> Triangles;
        Vertices.Reserve(FleckCount * 4);
        UVs.Reserve(FleckCount * 4);
        VertexColors.Reserve(FleckCount * 4);
        Triangles.Reserve(FleckCount * 6);

        for (int32 FleckIndex = 0; FleckIndex < FleckCount; ++FleckIndex)
        {
            const float LongT = static_cast<float>(FleckIndex) / static_cast<float>(FleckCount - 1);
            const float X = FMath::Lerp(-5450.0f, 16500.0f, LongT) +
                120.0f * FMath::Sin(static_cast<float>(FleckIndex) * 1.49f);
            const float CenterY = GetPreviewRiverCenterY(Spec, X);
            const float LateralSeed = FMath::Sin(static_cast<float>(FleckIndex) * 2.17f);
            const float Lateral = ActiveRiverHalfWidth * 0.92f * LateralSeed;
            const float Y = CenterY + Lateral;
            const float Yaw = FMath::DegreesToRadians(10.0f * FMath::Sin(static_cast<float>(FleckIndex) * 0.57f));
            const float Length = (Spec.bDesertCanyon ? 112.0f : 94.0f) *
                (0.48f + 0.54f * FMath::Abs(FMath::Sin(static_cast<float>(FleckIndex) * 0.77f)));
            const float Width = (Spec.bDesertCanyon ? 14.0f : 16.0f) *
                (0.44f + 0.46f * FMath::Abs(FMath::Sin(static_cast<float>(FleckIndex) * 1.23f)));
            const FVector AxisX(FMath::Cos(Yaw) * Length, FMath::Sin(Yaw) * Length, 0.0f);
            const FVector AxisY(-FMath::Sin(Yaw) * Width, FMath::Cos(Yaw) * Width, 0.0f);
            const float TextureNoise = FMath::Frac(
                FMath::Sin(static_cast<float>((FleckIndex + 53) * 431) * 12.9898f) * 43758.5453f);
            const float CenterT = 1.0f - FMath::Clamp(FMath::Abs(Lateral) / FMath::Max(1.0f, ActiveRiverHalfWidth), 0.0f, 1.0f);
            FLinearColor FleckColor = FMath::Lerp(
                NearFieldCurrentHighlight,
                NearFieldFoamFleck,
                FMath::Clamp(0.10f + TextureNoise * 0.34f + CenterT * 0.08f, 0.0f, 0.54f));
            const FLinearColor WaterFleckSkyAccent = Spec.bDesertCanyon
                ? FLinearColor(0.610f, 0.600f, 0.500f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.260f, 0.560f, 0.470f)
                                        : FLinearColor(0.340f, 0.640f, 0.545f));
            const FLinearColor WaterFleckBedAccent = Spec.bDesertCanyon
                ? FLinearColor(0.510f, 0.390f, 0.225f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.060f, 0.255f, 0.135f)
                                        : FLinearColor(0.170f, 0.350f, 0.235f));
            FleckColor = FMath::Lerp(
                FleckColor,
                WaterFleckSkyAccent,
                FMath::Clamp(SmoothPreviewStep(0.48f, 0.86f, TextureNoise) * (0.22f + CenterT * 0.10f), 0.0f, 0.34f));
            FleckColor = FMath::Lerp(
                FleckColor,
                WaterFleckBedAccent,
                FMath::Clamp(
                    SmoothPreviewStep(0.08f, 0.40f, 1.0f - TextureNoise) *
                        (0.18f + (1.0f - CenterT) * 0.08f),
                    0.0f,
                    0.28f));
            FleckColor = FMath::Lerp(
                FleckColor,
                NearFieldCurrentShadow,
                FMath::Clamp((1.0f - TextureNoise) * 0.22f, 0.0f, 0.24f));
            const float SurfaceWave = FMath::Sin(X * 0.020f + Y * 0.017f + TextureNoise) * (Spec.bDesertCanyon ? 2.0f : 3.2f);
            const FVector Center(X, Y, WaterBaseZ + 22.0f + SurfaceWave + CenterT * 3.0f);
            const int32 VertexStart = Vertices.Num();
            Vertices.Add(Center - AxisX);
            Vertices.Add(Center - AxisY);
            Vertices.Add(Center + AxisY);
            Vertices.Add(Center + AxisX);
            UVs.Add(FVector2D(0.0f, 0.0f));
            UVs.Add(FVector2D(1.0f, 0.0f));
            UVs.Add(FVector2D(0.0f, 1.0f));
            UVs.Add(FVector2D(1.0f, 1.0f));
            VertexColors.Add(ClampPreviewColor(ScalePreviewColor(FleckColor, 0.62f)));
            VertexColors.Add(ClampPreviewColor(ScalePreviewColor(FleckColor, 0.82f)));
            VertexColors.Add(ClampPreviewColor(ScalePreviewColor(FleckColor, 0.98f)));
            VertexColors.Add(ClampPreviewColor(ScalePreviewColor(FleckColor, 0.74f)));
            Triangles.Add(VertexStart);
            Triangles.Add(VertexStart + 1);
            Triangles.Add(VertexStart + 3);
            Triangles.Add(VertexStart);
            Triangles.Add(VertexStart + 3);
            Triangles.Add(VertexStart + 2);
        }

        Normals = ComputePreviewMeshNormals(Vertices, Triangles);
        AddPreviewProceduralMeshActor(
            World,
            FString::Printf(TEXT("RaftSim_CaptureQualityWaterTextureFlecks_%s"), *Spec.RiverId),
            Vertices,
            Triangles,
            Normals,
            UVs,
            NearFieldFoamFleck,
            LoadOrCreatePreviewWaterVertexColorMaterial(),
            &VertexColors);
    }

    const bool bUseSeparateSourceAwareWaterChromaMicrobreakupGeometry = false;
    if (bUseSeparateSourceAwareWaterChromaMicrobreakupGeometry)
    {
        const int32 StreakCount = Spec.bDesertCanyon ? 3520 : 2640;
        TArray<FVector> Vertices;
        TArray<FVector> Normals;
        TArray<FVector2D> UVs;
        TArray<FLinearColor> VertexColors;
        TArray<int32> Triangles;
        Vertices.Reserve(StreakCount * 4);
        UVs.Reserve(StreakCount * 4);
        VertexColors.Reserve(StreakCount * 4);
        Triangles.Reserve(StreakCount * 6);

        const FLinearColor SourceAwareWaterChromaDeep = Spec.bDesertCanyon
            ? FLinearColor(0.210f, 0.330f, 0.430f)
            : (Spec.bHasWaterfalls ? FLinearColor(0.020f, 0.205f, 0.105f)
                                    : FLinearColor(0.045f, 0.260f, 0.165f));
        const FLinearColor SourceAwareWaterChromaBank = Spec.bDesertCanyon
            ? FLinearColor(0.720f, 0.360f, 0.155f)
            : (Spec.bHasWaterfalls ? FLinearColor(0.080f, 0.330f, 0.135f)
                                    : FLinearColor(0.220f, 0.405f, 0.215f));
        const FLinearColor SourceAwareWaterChromaSky = Spec.bDesertCanyon
            ? FLinearColor(0.300f, 0.555f, 0.700f)
            : (Spec.bHasWaterfalls ? FLinearColor(0.260f, 0.600f, 0.500f)
                                    : FLinearColor(0.330f, 0.650f, 0.555f));
        const FLinearColor SourceAwareWaterChromaFoam = Spec.bDesertCanyon
            ? FLinearColor(0.840f, 0.680f, 0.380f)
            : (Spec.bHasWaterfalls ? FLinearColor(0.640f, 0.820f, 0.625f)
                                    : FLinearColor(0.675f, 0.825f, 0.665f));

        for (int32 StreakIndex = 0; StreakIndex < StreakCount; ++StreakIndex)
        {
            const float LongT = static_cast<float>(StreakIndex) / static_cast<float>(StreakCount - 1);
            const float LocalSeedA = FMath::Frac(
                FMath::Sin(static_cast<float>((StreakIndex + 71) * 379) * 12.9898f) * 43758.5453f);
            const float LocalSeedB = FMath::Frac(
                FMath::Sin(static_cast<float>((StreakIndex + 113) * 521) * 12.9898f) * 43758.5453f);
            const float X = FMath::Lerp(-5550.0f, 19600.0f, LongT) +
                210.0f * FMath::Sin(static_cast<float>(StreakIndex) * 0.83f);
            const float CenterY = GetPreviewRiverCenterY(Spec, X);
            const float ReachFade =
                SmoothPreviewStep(-5550.0f, -4900.0f, X) * (1.0f - SmoothPreviewStep(17200.0f, 19600.0f, X));
            const float LateralSeed =
                0.72f * FMath::Sin(static_cast<float>(StreakIndex) * 2.31f) +
                0.28f * FMath::Sin(static_cast<float>(StreakIndex) * 0.47f + LocalSeedA * UE_TWO_PI);
            const float Lateral = ActiveRiverHalfWidth * 0.88f * FMath::Clamp(LateralSeed, -1.0f, 1.0f);
            const float CenterT = 1.0f -
                FMath::Clamp(FMath::Abs(Lateral) / FMath::Max(1.0f, ActiveRiverHalfWidth), 0.0f, 1.0f);
            const float Width = (Spec.bDesertCanyon ? 15.0f : 14.0f) *
                (0.42f + 0.70f * LocalSeedB) * (0.78f + CenterT * 0.26f);
            const float Length = (Spec.bDesertCanyon ? 168.0f : 122.0f) *
                (0.34f + 0.82f * LocalSeedA) * (0.74f + CenterT * 0.36f);
            const float Yaw =
                0.018f * FMath::Sin(X * 0.0038f) +
                0.040f * FMath::Sin(static_cast<float>(StreakIndex) * 0.29f);
            const FVector AxisX(FMath::Cos(Yaw) * Length, FMath::Sin(Yaw) * Length, 0.0f);
            const FVector AxisY(-FMath::Sin(Yaw) * Width, FMath::Cos(Yaw) * Width, 0.0f);
            const float PaletteNoise = FMath::Clamp(
                0.50f +
                    0.34f * FMath::Sin(X * 0.014f + Lateral * 0.021f + LocalSeedA) +
                    0.22f * FMath::Sin(X * 0.041f - Lateral * 0.017f + LocalSeedB),
                0.0f,
                1.0f);
            const float FlowThreadNoise = FMath::Clamp(
                0.50f +
                    0.30f * FMath::Sin(X * 0.0065f + Lateral * 0.0125f) +
                    0.20f * FMath::Sin(X * 0.0195f - Lateral * 0.0085f),
                0.0f,
                1.0f);
            FLinearColor StreakColor = PaletteNoise < 0.24f
                ? SourceAwareWaterChromaDeep
                : (PaletteNoise < 0.50f
                       ? SourceAwareWaterChromaBank
                       : (PaletteNoise < 0.76f ? SourceAwareWaterChromaSky : SourceAwareWaterChromaFoam));
            StreakColor = FMath::Lerp(StreakColor, Spec.WaterColor, Spec.bDesertCanyon ? 0.14f : 0.18f);
            StreakColor = ScalePreviewColor(
                StreakColor,
                FMath::Clamp(0.72f + FlowThreadNoise * 0.42f + CenterT * 0.10f, 0.68f, 1.28f));
            const float SurfaceWave =
                FMath::Sin(X * 0.020f + Lateral * 0.014f + LocalSeedA * UE_TWO_PI) *
                (Spec.bDesertCanyon ? 1.8f : 2.8f);
            const FVector Center(X, CenterY + Lateral, WaterBaseZ + 31.0f + SurfaceWave + ReachFade * 2.0f);
            const int32 VertexStart = Vertices.Num();
            Vertices.Add(Center - AxisX);
            Vertices.Add(Center - AxisY);
            Vertices.Add(Center + AxisY);
            Vertices.Add(Center + AxisX);
            UVs.Add(FVector2D(0.0f, 0.0f));
            UVs.Add(FVector2D(1.0f, 0.0f));
            UVs.Add(FVector2D(0.0f, 1.0f));
            UVs.Add(FVector2D(1.0f, 1.0f));
            VertexColors.Add(ClampPreviewColor(ScalePreviewColor(StreakColor, 0.72f + ReachFade * 0.08f)));
            VertexColors.Add(ClampPreviewColor(ScalePreviewColor(StreakColor, 0.90f + FlowThreadNoise * 0.08f)));
            VertexColors.Add(ClampPreviewColor(ScalePreviewColor(StreakColor, 1.06f)));
            VertexColors.Add(ClampPreviewColor(ScalePreviewColor(StreakColor, 0.78f + CenterT * 0.10f)));
            Triangles.Add(VertexStart);
            Triangles.Add(VertexStart + 1);
            Triangles.Add(VertexStart + 2);
            Triangles.Add(VertexStart);
            Triangles.Add(VertexStart + 3);
            Triangles.Add(VertexStart + 1);
        }

        Normals = ComputePreviewMeshNormals(Vertices, Triangles);
        AddPreviewProceduralMeshActor(
            World,
            FString::Printf(TEXT("RaftSim_SourceAwareWaterChromaMicrobreakup_%s"), *Spec.RiverId),
            Vertices,
            Triangles,
            Normals,
            UVs,
            Spec.WaterColor,
            LoadOrCreatePreviewWaterVertexColorMaterial(),
            &VertexColors);
    }

    for (int32 RockIndex = 0; RockIndex < 10; ++RockIndex)
    {
        const float Side = (RockIndex % 2 == 0) ? -1.0f : 1.0f;
        const float X = -4620.0f + static_cast<float>(RockIndex) * 980.0f +
            130.0f * FMath::Sin(static_cast<float>(RockIndex) * 1.71f);
        const float CenterY = GetPreviewRiverCenterY(Spec, X);
        const float LateralOffset = Side * ActiveRiverHalfWidth *
            (0.62f + 0.26f * FMath::Abs(FMath::Sin(static_cast<float>(RockIndex) * 0.83f)));
        const float Y = CenterY + LateralOffset;
        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
        const FVector RockScale(
            Spec.bDesertCanyon ? 0.54f : 0.42f,
            Spec.bDesertCanyon ? 0.42f : 0.34f,
            Spec.bDesertCanyon ? 0.22f : 0.18f);
        AddPreviewIrregularRockActor(
            World,
            FString::Printf(TEXT("RaftSim_NearFieldCaptureQualityWetRock_%02d_%s"), RockIndex, *Spec.RiverId),
            FVector(X, Y, FMath::Max(TerrainZ + 10.0f, WaterBaseZ + 12.0f)),
            21.0f * static_cast<float>(RockIndex),
            RockScale,
            ScalePreviewColor(Spec.RockColor, Spec.bDesertCanyon ? 0.76f : 0.66f),
            RockIndex + 9100);
    }
}

void AddPreviewLightRig(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec)
{
    if (!World || !GEditor)
    {
        return;
    }
    const FRaftSimPhotographicCaptureSettings CaptureSettings =
        GetPhotographicCaptureSettings(Spec.RiverId);

    ADirectionalLight* Sun = Cast<ADirectionalLight>(
        GEditor->AddActor(World->GetCurrentLevel(), ADirectionalLight::StaticClass(), FTransform(FRotator(-58.0f, -30.0f, 0.0f))));
    if (Sun)
    {
        Sun->SetActorLabel(TEXT("RaftSim_Sun_LumenPreview"));
        Sun->GetLightComponent()->SetIntensity(CaptureSettings.SunIntensity);
        Sun->GetLightComponent()->SetLightColor(CaptureSettings.SunColor);
    }

    ASkyLight* SkyLight = Cast<ASkyLight>(
        GEditor->AddActor(World->GetCurrentLevel(), ASkyLight::StaticClass(), FTransform(FRotator::ZeroRotator, FVector(0.0f, 0.0f, 1000.0f))));
    if (SkyLight)
    {
        SkyLight->SetActorLabel(TEXT("RaftSim_SkyLight_PhotorealPreview"));
        SkyLight->GetLightComponent()->SetMobility(EComponentMobility::Movable);
        SkyLight->GetLightComponent()->SourceType = SLS_CapturedScene;
        SkyLight->GetLightComponent()->SetIntensity(CaptureSettings.SkyLightIntensity);
    }

    ASkyAtmosphere* Atmosphere = Cast<ASkyAtmosphere>(
        GEditor->AddActor(World->GetCurrentLevel(), ASkyAtmosphere::StaticClass(), FTransform::Identity));
    if (Atmosphere)
    {
        Atmosphere->SetActorLabel(TEXT("RaftSim_SkyAtmosphere_SourceAware"));
    }

    AExponentialHeightFog* Fog = Cast<AExponentialHeightFog>(
        GEditor->AddActor(World->GetCurrentLevel(), AExponentialHeightFog::StaticClass(), FTransform(FRotator::ZeroRotator, FVector(0.0f, 0.0f, 220.0f))));
    if (Fog)
    {
        Fog->SetActorLabel(Spec.bHasWaterfalls ? TEXT("RaftSim_RainforestMist") : TEXT("RaftSim_CanyonAtmosphere"));
        Fog->GetComponent()->SetFogDensity(CaptureSettings.FogDensity);
        Fog->GetComponent()->SetFogInscatteringColor(CaptureSettings.FogColor);
    }

    if (SkyLight && SkyLight->GetLightComponent())
    {
        SkyLight->GetLightComponent()->RecaptureSky();
    }

    ASphereReflectionCapture* RiverReflectionCapture = Cast<ASphereReflectionCapture>(
        GEditor->AddActor(
            World->GetCurrentLevel(),
            ASphereReflectionCapture::StaticClass(),
            FTransform(
                FRotator::ZeroRotator,
                FVector(4200.0f, GetPreviewRiverCenterY(Spec, 4200.0f), 520.0f))));
    if (RiverReflectionCapture)
    {
        RiverReflectionCapture->SetActorLabel(TEXT("RaftSim_RiverCorridorReflectionCapture"));
        if (USphereReflectionCaptureComponent* ReflectionComponent =
                Cast<USphereReflectionCaptureComponent>(RiverReflectionCapture->GetCaptureComponent()))
        {
            ReflectionComponent->InfluenceRadius = 42000.0f;
            ReflectionComponent->Brightness = 1.0f;
            ReflectionComponent->ReflectionSourceType = EReflectionSourceType::CapturedScene;
            ReflectionComponent->bRuntimeCapture = true;
            ReflectionComponent->MarkDirtyForRecapture();
            World->SendAllEndOfFrameUpdates();
            UReflectionCaptureComponent::UpdateReflectionCaptureContents(
                World,
                TEXT("RaftSim photoreal river corridor"));
        }
    }
}
} // namespace RaftSimEditorEnvironment
