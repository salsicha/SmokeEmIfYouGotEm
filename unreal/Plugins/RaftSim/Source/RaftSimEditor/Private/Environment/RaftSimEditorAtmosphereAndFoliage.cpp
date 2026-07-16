#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
void AddPreviewSurfaceAtmosphereAndSprayDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    UStaticMesh* PlaneMesh)
{
    if (!World || !PlaneMesh)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float WaterBaseZ = GetPreviewWaterSurfaceBaseZCm(Spec);
    const int32 GlintCount = Spec.bDesertCanyon ? 18 : (Spec.bHasWaterfalls ? 26 : 22);
    const FLinearColor GlintColor = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.72f, 0.66f, 0.50f, 1.0f), 0.38f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.54f, 0.92f, 0.82f, 1.0f), 0.36f)
                                : FMath::Lerp(Spec.WaterColor, FLinearColor(0.60f, 0.94f, 0.92f, 1.0f), 0.36f));

    for (int32 GlintIndex = 0; GlintIndex < GlintCount; ++GlintIndex)
    {
        const float T = static_cast<float>(GlintIndex) / static_cast<float>(FMath::Max(1, GlintCount - 1));
        const float X = FMath::Lerp(6200.0f, 24800.0f, T);
        const float RiverCenterY = GetPreviewRiverCenterY(Spec, X);
        const float Lateral = FMath::Sin(static_cast<float>(GlintIndex) * 2.31f) * ActiveRiverHalfWidth * 0.62f;
        const float WidthScale = 0.040f + 0.010f * static_cast<float>(GlintIndex % 4);
        const float LengthScale = (Spec.bDesertCanyon ? 0.62f : 0.46f) + 0.06f * static_cast<float>(GlintIndex % 5);
        const float Opacity = Spec.bDesertCanyon ? 0.060f : (Spec.bHasWaterfalls ? 0.080f : 0.070f);
        AddPreviewTranslucentMeshActor(
            World,
            PlaneMesh,
            FString::Printf(TEXT("RaftSim_SurfaceGlint_%03d_%s"), GlintIndex, *Spec.RiverId),
            FVector(X, RiverCenterY + Lateral, WaterBaseZ + 22.0f + 1.6f * FMath::Sin(static_cast<float>(GlintIndex))),
            FRotator(0.0f, static_cast<float>((GlintIndex * 19) % 360), 0.0f),
            FVector(LengthScale, WidthScale, 1.0f),
            GlintColor,
            Opacity);
    }

    const int32 FleckCount = Spec.bDesertCanyon ? 22 : (Spec.bHasWaterfalls ? 46 : 32);
    for (int32 FleckIndex = 0; FleckIndex < FleckCount; ++FleckIndex)
    {
        const float T = FMath::Frac(0.173f * static_cast<float>(FleckIndex) + 0.19f);
        const float X = FMath::Lerp(-3600.0f, 24400.0f, T);
        const float RiverCenterY = GetPreviewRiverCenterY(Spec, X);
        const float Lateral = FMath::Sin(static_cast<float>(FleckIndex) * 1.83f) * ActiveRiverHalfWidth * 0.84f;
        const float FleckOpacity = Spec.bDesertCanyon ? 0.14f : 0.22f;
        AddPreviewTranslucentMeshActor(
            World,
            PlaneMesh,
            FString::Printf(TEXT("RaftSim_FoamFleck_%03d_%s"), FleckIndex, *Spec.RiverId),
            FVector(X, RiverCenterY + Lateral, WaterBaseZ + 25.0f),
            FRotator(0.0f, static_cast<float>((FleckIndex * 47) % 360), 0.0f),
            FVector(0.18f + 0.04f * static_cast<float>(FleckIndex % 3), 0.035f, 1.0f),
            Spec.bDesertCanyon ? FLinearColor(0.78f, 0.76f, 0.66f, 1.0f) : FLinearColor(0.86f, 0.96f, 0.90f, 1.0f),
            FleckOpacity);
    }

    if (Spec.bDesertCanyon)
    {
        const float RemainingAtmosphericCardCull = 0.18f;
        for (int32 HazeIndex = 0; HazeIndex < 3; ++HazeIndex)
        {
            const float X = 2400.0f + static_cast<float>(HazeIndex) * 3600.0f;
            const float CenterY = GetPreviewRiverCenterY(Spec, X);
            const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, CenterY, TerrainRelief, HeightfieldPreview);
            AddPreviewTranslucentMeshActor(
                World,
                PlaneMesh,
                FString::Printf(TEXT("RaftSim_CanyonDistanceHaze_%02d_%s"), HazeIndex, *Spec.RiverId),
                FVector(X, CenterY, TerrainZ + 560.0f + 30.0f * static_cast<float>(HazeIndex % 2)),
                FRotator(82.0f, 0.0f, 0.0f),
                FVector(12.0f, 1.7f, 1.0f),
                FLinearColor(0.72f, 0.64f, 0.50f, 1.0f),
                0.12f * RemainingAtmosphericCardCull);
        }
    }

    if (Spec.bHasWaterfalls)
    {
        const float RemainingAtmosphericCardCull = 0.18f;
        for (int32 SprayIndex = 0; SprayIndex < 6; ++SprayIndex)
        {
            const float X = 3650.0f + static_cast<float>(SprayIndex % 7) * 4300.0f + 170.0f * FMath::Sin(static_cast<float>(SprayIndex));
            const float Side = (SprayIndex % 2 == 0) ? -1.0f : 1.0f;
            const float Y = GetPreviewRiverCenterY(Spec, X) + Side * (1750.0f + 120.0f * static_cast<float>(SprayIndex % 3));
            AddPreviewTranslucentMeshActor(
                World,
                PlaneMesh,
                FString::Printf(TEXT("RaftSim_RainforestSprayMist_%02d_%s"), SprayIndex, *Spec.RiverId),
                FVector(X, Y, 245.0f + 28.0f * static_cast<float>(SprayIndex % 4)),
                FRotator(74.0f, 0.0f, static_cast<float>((SprayIndex * 29) % 360)),
                FVector(2.2f + 0.18f * static_cast<float>(SprayIndex % 3), 0.30f, 1.0f),
                FLinearColor(0.58f, 0.88f, 0.78f, 1.0f),
                0.20f * RemainingAtmosphericCardCull);
        }
    }
}

void AddPreviewRiverAtmosphericBackdropDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    UStaticMesh* PlaneMesh)
{
    if (!World || !PlaneMesh)
    {
        return;
    }

    const FLinearColor CloudColor = Spec.bDesertCanyon
        ? FLinearColor(0.78f, 0.69f, 0.54f, 1.0f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.58f, 0.82f, 0.72f, 1.0f) : FLinearColor(0.78f, 0.86f, 0.82f, 1.0f));
    const FLinearColor HorizonColor = Spec.bDesertCanyon
        ? FLinearColor(0.62f, 0.50f, 0.38f, 1.0f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.28f, 0.48f, 0.34f, 1.0f) : FLinearColor(0.48f, 0.58f, 0.46f, 1.0f));
    const float RemainingAtmosphericCardCull = 0.16f;
    const int32 CloudCount = Spec.bDesertCanyon ? 3 : (Spec.bHasWaterfalls ? 4 : 3);

    for (int32 CloudIndex = 0; CloudIndex < CloudCount; ++CloudIndex)
    {
        const float T = static_cast<float>(CloudIndex) / static_cast<float>(FMath::Max(1, CloudCount - 1));
        const float X = FMath::Lerp(5200.0f, 24600.0f, T) + 380.0f * FMath::Sin(static_cast<float>(CloudIndex) * 1.13f);
        const float CenterY = GetPreviewRiverCenterY(Spec, X);
        const float Side = (CloudIndex % 2 == 0) ? -1.0f : 1.0f;
        const float CloudY = CenterY + Side * (Spec.bDesertCanyon ? 620.0f : 520.0f) +
            260.0f * FMath::Sin(static_cast<float>(CloudIndex) * 0.71f);
        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, CenterY, TerrainRelief, HeightfieldPreview);
        const float CloudZ = TerrainZ + (Spec.bDesertCanyon ? 1120.0f : (Spec.bHasWaterfalls ? 760.0f : 880.0f)) +
            95.0f * FMath::Sin(static_cast<float>(CloudIndex) * 0.83f);
        const float LengthScale = Spec.bDesertCanyon ? 13.0f : (Spec.bHasWaterfalls ? 11.5f : 12.0f);
        const float HeightScale = Spec.bDesertCanyon ? 1.55f : (Spec.bHasWaterfalls ? 1.95f : 1.45f);
        AddPreviewTranslucentMeshActor(
            World,
            PlaneMesh,
            FString::Printf(TEXT("RaftSim_RiverSpecificCloudHaze_%02d_%s"), CloudIndex, *Spec.RiverId),
            FVector(X, CloudY, CloudZ),
            FRotator(78.0f, 0.0f, static_cast<float>((CloudIndex * 23) % 360)),
            FVector(LengthScale * (0.58f + 0.04f * static_cast<float>(CloudIndex % 4)), HeightScale * 0.46f, 1.0f),
            ScalePreviewColor(CloudColor, 0.92f + 0.05f * static_cast<float>(CloudIndex % 3)),
            (Spec.bDesertCanyon ? 0.17f : (Spec.bHasWaterfalls ? 0.24f : 0.19f)) *
                RemainingAtmosphericCardCull);
    }

    const int32 HorizonBandCount = Spec.bDesertCanyon ? 2 : (Spec.bHasWaterfalls ? 3 : 2);
    for (int32 BandIndex = 0; BandIndex < HorizonBandCount; ++BandIndex)
    {
        const float X = 6200.0f + static_cast<float>(BandIndex) * (Spec.bDesertCanyon ? 3300.0f : 2700.0f);
        const float CenterY = GetPreviewRiverCenterY(Spec, X);
        const float Side = (BandIndex % 2 == 0) ? -1.0f : 1.0f;
        const float Offset = Spec.bDesertCanyon ? 1180.0f : (Spec.bHasWaterfalls ? 850.0f : 980.0f);
        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, CenterY + Side * Offset, TerrainRelief, HeightfieldPreview);
        AddPreviewTranslucentMeshActor(
            World,
            PlaneMesh,
            FString::Printf(TEXT("RaftSim_RiverSpecificHorizonVeil_%02d_%s"), BandIndex, *Spec.RiverId),
            FVector(X, CenterY + Side * Offset, TerrainZ + (Spec.bDesertCanyon ? 520.0f : 360.0f)),
            FRotator(83.0f, 0.0f, static_cast<float>((BandIndex * 31) % 360)),
            FVector(Spec.bDesertCanyon ? 9.0f : 7.5f, Spec.bHasWaterfalls ? 1.5f : 1.3f, 1.0f),
            ScalePreviewColor(HorizonColor, 0.90f + 0.04f * static_cast<float>(BandIndex % 4)),
            (Spec.bDesertCanyon ? 0.19f : (Spec.bHasWaterfalls ? 0.26f : 0.20f)) *
                RemainingAtmosphericCardCull);
    }
}

void AddPreviewSourceAwareSkyGradientLayer(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    UStaticMesh* PlaneMesh)
{
    if (!World || !PlaneMesh)
    {
        return;
    }

    const FLinearColor UpperSkyColor = Spec.bDesertCanyon
        ? FLinearColor(0.54f, 0.63f, 0.76f, 1.0f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.42f, 0.60f, 0.62f, 1.0f)
                                : FLinearColor(0.56f, 0.69f, 0.82f, 1.0f));
    const FLinearColor HorizonWarmthColor = Spec.bDesertCanyon
        ? FLinearColor(0.86f, 0.57f, 0.34f, 1.0f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.45f, 0.70f, 0.54f, 1.0f)
                                : FLinearColor(0.82f, 0.72f, 0.52f, 1.0f));
    const FLinearColor DepthSheetColor = Spec.bDesertCanyon
        ? FLinearColor(0.54f, 0.42f, 0.30f, 1.0f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.18f, 0.40f, 0.32f, 1.0f)
                                : FLinearColor(0.38f, 0.48f, 0.46f, 1.0f));

    const float RemainingAtmosphericCardCull = 0.16f;
    const int32 GradientBandCount = Spec.bDesertCanyon ? 6 : (Spec.bHasWaterfalls ? 6 : 5);
    for (int32 BandIndex = 0; BandIndex < GradientBandCount; ++BandIndex)
    {
        const float T = static_cast<float>(BandIndex) / static_cast<float>(FMath::Max(1, GradientBandCount - 1));
        const float X = FMath::Lerp(3600.0f, 26400.0f, T);
        const float CenterY = GetPreviewRiverCenterY(Spec, X);
        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, CenterY, TerrainRelief, HeightfieldPreview);
        const float HeightLift = Spec.bDesertCanyon ? 1480.0f : (Spec.bHasWaterfalls ? 1050.0f : 1220.0f);
        FLinearColor BandColor = FMath::Lerp(HorizonWarmthColor, UpperSkyColor, FMath::Clamp(T * 0.82f + 0.12f, 0.0f, 1.0f));
        const FLinearColor SkyDetailAccent = Spec.bDesertCanyon
            ? (BandIndex % 2 == 0 ? FLinearColor(0.74f, 0.49f, 0.30f, 1.0f) : FLinearColor(0.42f, 0.59f, 0.72f, 1.0f))
            : (Spec.bHasWaterfalls
                   ? (BandIndex % 2 == 0 ? FLinearColor(0.30f, 0.62f, 0.48f, 1.0f) : FLinearColor(0.50f, 0.68f, 0.68f, 1.0f))
                   : (BandIndex % 2 == 0 ? FLinearColor(0.72f, 0.66f, 0.48f, 1.0f) : FLinearColor(0.46f, 0.66f, 0.78f, 1.0f)));
        BandColor = FMath::Lerp(BandColor, SkyDetailAccent, 0.24f + 0.06f * static_cast<float>(BandIndex % 3));
        AddPreviewTranslucentMeshActor(
            World,
            PlaneMesh,
            FString::Printf(TEXT("RaftSim_SourceAwareSkyGradientBand_%02d_%s"), BandIndex, *Spec.RiverId),
            FVector(
                X,
                CenterY + 90.0f * FMath::Sin(static_cast<float>(BandIndex) * 0.91f),
                TerrainZ + HeightLift + 70.0f * static_cast<float>(BandIndex)),
            FRotator(82.0f, 0.0f, 3.0f * FMath::Sin(static_cast<float>(BandIndex) * 0.67f)),
            FVector(Spec.bDesertCanyon ? 13.0f : 11.5f, Spec.bHasWaterfalls ? 1.9f : 1.6f, 1.0f),
            ScalePreviewColor(BandColor, 0.82f + 0.04f * static_cast<float>(BandIndex % 3)),
            (Spec.bDesertCanyon ? 0.12f : (Spec.bHasWaterfalls ? 0.15f : 0.13f)) *
                RemainingAtmosphericCardCull);
    }

    const float SunVeilX = Spec.bDesertCanyon ? 18500.0f : (Spec.bHasWaterfalls ? 14600.0f : 16200.0f);
    const float SunVeilCenterY = GetPreviewRiverCenterY(Spec, SunVeilX);
    const float SunVeilTerrainZ = GetPreviewTerrainHeightCm(Spec, SunVeilX, SunVeilCenterY, TerrainRelief, HeightfieldPreview);
    AddPreviewTranslucentMeshActor(
        World,
        PlaneMesh,
        FString::Printf(TEXT("RaftSim_SourceAwareSunWarmthVeil_%s"), *Spec.RiverId),
        FVector(
            SunVeilX,
            SunVeilCenterY + (Spec.bDesertCanyon ? -980.0f : (Spec.bHasWaterfalls ? 520.0f : -620.0f)),
            SunVeilTerrainZ + (Spec.bDesertCanyon ? 1260.0f : (Spec.bHasWaterfalls ? 880.0f : 980.0f))),
        FRotator(79.0f, 0.0f, Spec.bHasWaterfalls ? -18.0f : 16.0f),
        FVector(Spec.bDesertCanyon ? 11.0f : 9.0f, Spec.bHasWaterfalls ? 1.5f : 1.3f, 1.0f),
        ScalePreviewColor(HorizonWarmthColor, Spec.bDesertCanyon ? 0.86f : 0.78f),
        (Spec.bDesertCanyon ? 0.16f : (Spec.bHasWaterfalls ? 0.12f : 0.13f)) *
            RemainingAtmosphericCardCull);

    const int32 DepthSheetCount = Spec.bDesertCanyon ? 5 : (Spec.bHasWaterfalls ? 5 : 4);
    for (int32 SheetIndex = 0; SheetIndex < DepthSheetCount; ++SheetIndex)
    {
        const float T = static_cast<float>(SheetIndex) / static_cast<float>(FMath::Max(1, DepthSheetCount - 1));
        const float X = FMath::Lerp(7600.0f, 26200.0f, T);
        const float CenterY = GetPreviewRiverCenterY(Spec, X);
        const float Side = (SheetIndex % 2 == 0) ? -1.0f : 1.0f;
        const float Offset = Spec.bDesertCanyon ? 1560.0f : (Spec.bHasWaterfalls ? 1040.0f : 1180.0f);
        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, CenterY + Side * Offset, TerrainRelief, HeightfieldPreview);
        const float SheetLift = Spec.bDesertCanyon ? 640.0f : (Spec.bHasWaterfalls ? 520.0f : 560.0f);
        AddPreviewTranslucentMeshActor(
            World,
            PlaneMesh,
            FString::Printf(TEXT("RaftSim_SourceAwareAtmosphereDepthSheet_%02d_%s"), SheetIndex, *Spec.RiverId),
            FVector(X, CenterY + Side * Offset, TerrainZ + SheetLift + 42.0f * static_cast<float>(SheetIndex % 3)),
            FRotator(84.0f, 0.0f, static_cast<float>((SheetIndex * 27) % 360)),
            FVector(Spec.bDesertCanyon ? 9.0f : 7.5f, Spec.bHasWaterfalls ? 1.6f : 1.3f, 1.0f),
            ScalePreviewColor(
                FMath::Lerp(
                    DepthSheetColor,
                    SheetIndex % 2 == 0 ? HorizonWarmthColor : UpperSkyColor,
                    Spec.bDesertCanyon ? 0.28f : 0.22f),
                0.84f + 0.04f * static_cast<float>(SheetIndex % 4)),
            (Spec.bDesertCanyon ? 0.15f : (Spec.bHasWaterfalls ? 0.20f : 0.16f)) *
                RemainingAtmosphericCardCull);
    }
}

void AddPreviewWaterfallAndPlungeMistDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    UStaticMesh* PlaneMesh,
    UStaticMesh* CubeMesh)
{
    if (!World || !Spec.bHasWaterfalls || !PlaneMesh || !CubeMesh)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float WaterBaseZ = GetPreviewWaterSurfaceBaseZCm(Spec);
    const int32 WaterfallCount = 7;

    for (int32 WaterfallIndex = 0; WaterfallIndex < WaterfallCount; ++WaterfallIndex)
    {
        const float T = static_cast<float>(WaterfallIndex) / static_cast<float>(FMath::Max(1, WaterfallCount - 1));
        const float X = FMath::Lerp(2700.0f, 24200.0f, T) +
            260.0f * FMath::Sin(static_cast<float>(WaterfallIndex) * 1.37f);
        const float Side = (WaterfallIndex % 2 == 0) ? -1.0f : 1.0f;
        const float RiverCenterY = GetPreviewRiverCenterY(Spec, X);
        const float FootY = RiverCenterY + Side * (ActiveRiverHalfWidth + 86.0f + 24.0f * static_cast<float>(WaterfallIndex % 3));
        const float CurtainY = RiverCenterY + Side * (ActiveRiverHalfWidth + 250.0f + 46.0f * static_cast<float>(WaterfallIndex % 2));
        const float CliffY = RiverCenterY + Side * (ActiveRiverHalfWidth + 620.0f + 90.0f * static_cast<float>(WaterfallIndex % 4));
        const float FootZ = FMath::Max(
            WaterBaseZ + 50.0f,
            GetPreviewTerrainHeightCm(Spec, X, FootY, TerrainRelief, HeightfieldPreview) + 42.0f);
        const float TopZ = FMath::Max(
            FootZ + 430.0f + 42.0f * static_cast<float>(WaterfallIndex % 4),
            GetPreviewTerrainHeightCm(Spec, X, CliffY, TerrainRelief, HeightfieldPreview) + 145.0f);
        const float MidZ = (FootZ + TopZ) * 0.5f;
        const float CurtainHeightScale = FMath::Clamp((TopZ - FootZ) / 100.0f, 4.8f, 12.0f);
        const float CurtainWidthScale = 2.55f + 0.24f * static_cast<float>(WaterfallIndex % 4);
        const float Yaw = Side > 0.0f ? -5.0f : 5.0f;

        AddPreviewMeshActor(
            World,
            CubeMesh,
            FString::Printf(TEXT("RaftSim_PacuareWaterfallWetCliff_%02d_%s"), WaterfallIndex, *Spec.RiverId),
            FVector(X - 18.0f, CurtainY + Side * 24.0f, MidZ - 10.0f),
            FRotator(0.0f, Yaw, 0.0f),
            FVector(1.10f + 0.12f * static_cast<float>(WaterfallIndex % 3), 0.045f, CurtainHeightScale * 0.54f),
            ScalePreviewColor(FMath::Lerp(Spec.RockColor, Spec.FoliageColor, 0.22f), 0.48f));

        AddPreviewTranslucentMeshActor(
            World,
            PlaneMesh,
            FString::Printf(TEXT("RaftSim_PacuareWaterfallCurtain_%02d_%s"), WaterfallIndex, *Spec.RiverId),
            FVector(X, CurtainY, MidZ),
            FRotator(90.0f, Yaw * 0.25f, 0.0f),
            FVector(CurtainHeightScale, CurtainWidthScale, 1.0f),
            FLinearColor(0.66f, 0.94f, 0.90f, 1.0f),
            0.43f);

        AddPreviewTranslucentMeshActor(
            World,
            PlaneMesh,
            FString::Printf(TEXT("RaftSim_PacuareWaterfallBrightCore_%02d_%s"), WaterfallIndex, *Spec.RiverId),
            FVector(X + 14.0f * Side, CurtainY - Side * 5.0f, MidZ - 8.0f),
            FRotator(90.0f, Yaw * 0.25f, 0.0f),
            FVector(CurtainHeightScale * 0.96f, CurtainWidthScale * 0.36f, 1.0f),
            FLinearColor(0.82f, 0.98f, 0.94f, 1.0f),
            0.52f);

        const float RunoutLengthScale = FMath::Clamp(FMath::Abs(CurtainY - FootY) / 100.0f, 2.0f, 4.6f);
        AddPreviewTranslucentMeshActor(
            World,
            PlaneMesh,
            FString::Printf(TEXT("RaftSim_PacuareWaterfallRunout_%02d_%s"), WaterfallIndex, *Spec.RiverId),
            FVector(X + 44.0f, (CurtainY + FootY) * 0.5f, FootZ + 24.0f),
            FRotator(0.0f, Side > 0.0f ? 90.0f : -90.0f, 0.0f),
            FVector(RunoutLengthScale, 0.20f + 0.03f * static_cast<float>(WaterfallIndex % 2), 1.0f),
            FLinearColor(0.46f, 0.84f, 0.76f, 1.0f),
            0.28f);

        for (int32 MistIndex = 0; MistIndex < 3; ++MistIndex)
        {
            const float MistPhase = static_cast<float>(WaterfallIndex * 3 + MistIndex);
            AddPreviewTranslucentMeshActor(
                World,
                PlaneMesh,
                FString::Printf(TEXT("RaftSim_PacuareWaterfallPlungeMist_%02d_%02d_%s"), WaterfallIndex, MistIndex, *Spec.RiverId),
                FVector(
                    X + 58.0f * FMath::Sin(MistPhase * 1.11f),
                    FootY + Side * (30.0f + 38.0f * static_cast<float>(MistIndex)),
                    FootZ + 54.0f + 34.0f * static_cast<float>(MistIndex)),
                FRotator(72.0f, 0.0f, static_cast<float>((WaterfallIndex * 41 + MistIndex * 23) % 360)),
                FVector(1.20f + 0.26f * static_cast<float>(MistIndex), 0.48f + 0.06f * static_cast<float>(WaterfallIndex % 2), 1.0f),
                FLinearColor(0.62f, 0.90f, 0.82f, 1.0f),
                0.23f);
        }

        AddPreviewTranslucentMeshActor(
            World,
            PlaneMesh,
            FString::Printf(TEXT("RaftSim_PacuareWaterfallPlungeFoam_%02d_%s"), WaterfallIndex, *Spec.RiverId),
            FVector(X + 36.0f, FootY, FootZ + 18.0f),
            FRotator(0.0f, static_cast<float>((WaterfallIndex * 37) % 360), 0.0f),
            FVector(0.88f + 0.08f * static_cast<float>(WaterfallIndex % 3), 0.30f, 1.0f),
            FLinearColor(0.84f, 0.96f, 0.88f, 1.0f),
            0.34f);
    }
}

void AddPreviewBiomeBankEcologyDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask,
    UStaticMesh* CubeMesh,
    UStaticMesh* CylinderMesh,
    UStaticMesh* PlaneMesh)
{
    if (!World || !CylinderMesh || !PlaneMesh)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float FirstPartyOrganicDeadfallCylinderReplacement = 1.0f;
    const float FirstPartyOrganicRootRunnerCylinderReplacement = 1.0f;
    const int32 DeadfallCount = Spec.bDesertCanyon ? 14 : (Spec.bHasWaterfalls ? 42 : 28);
    for (int32 DeadfallIndex = 0; DeadfallIndex < DeadfallCount; ++DeadfallIndex)
    {
        const float Side = (DeadfallIndex % 2 == 0) ? -1.0f : 1.0f;
        const float T = static_cast<float>(DeadfallIndex) / static_cast<float>(FMath::Max(1, DeadfallCount - 1));
        const float Phase = static_cast<float>(DeadfallIndex) * 1.271f;
        const float BaseX = FMath::Lerp(1250.0f, 25200.0f, T) + 220.0f * FMath::Sin(Phase);
        const float BaseOffset = ActiveRiverHalfWidth +
            (Spec.bDesertCanyon ? 920.0f : (Spec.bHasWaterfalls ? 430.0f : 520.0f)) +
            (Spec.bDesertCanyon ? 360.0f : 260.0f) * FMath::Abs(FMath::Sin(Phase * 0.71f));
        float X = BaseX;
        float Y = GetPreviewRiverCenterY(Spec, X) + Side * BaseOffset;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 5; ++CandidateIndex)
        {
            const float CandidateX = BaseX + 170.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.17f);
            const float CandidateOffset = BaseOffset + 180.0f * FMath::Sin(Phase * 0.57f + static_cast<float>(CandidateIndex) * 0.83f);
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
            const float Score = VegetationT * (Spec.bDesertCanyon ? 0.30f : 1.05f) - WaterT * 0.48f +
                0.08f * FMath::Sin(Phase + static_cast<float>(CandidateIndex));
            if (Score > BestScore)
            {
                BestScore = Score;
                X = CandidateX;
                Y = CandidateY;
            }
        }

        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
        const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, Y);
        const FLinearColor DryWoodColor = Spec.bDesertCanyon
            ? FLinearColor(0.28f, 0.20f, 0.13f)
            : (Spec.bHasWaterfalls ? FLinearColor(0.045f, 0.035f, 0.024f) : FLinearColor(0.24f, 0.17f, 0.10f));
        const FLinearColor WetWoodColor = Spec.bHasWaterfalls
            ? FLinearColor(0.020f, 0.028f, 0.020f)
            : FMath::Lerp(DryWoodColor, ScalePreviewColor(Spec.WaterColor, 0.32f), 0.32f);
        const FLinearColor DeadfallColor = ScalePreviewColor(
            FMath::Lerp(DryWoodColor, WetWoodColor, FMath::Clamp(WaterT * 0.42f + (Spec.bHasWaterfalls ? 0.18f : 0.0f), 0.0f, 0.62f)),
            0.86f + 0.06f * static_cast<float>(DeadfallIndex % 4));
        const float LengthScale = Spec.bDesertCanyon ? 1.35f : (Spec.bHasWaterfalls ? 1.85f : 1.55f);
        const float ThicknessScale = Spec.bHasWaterfalls ? 0.085f : 0.070f;
        AddPreviewMeshActor(
            World,
            CylinderMesh,
            FString::Printf(TEXT("RaftSim_BiomeDeadfallLog_%03d_%s"), DeadfallIndex, *Spec.RiverId),
            FVector(X, Y, TerrainZ + 18.0f),
            FRotator(90.0f + 3.0f * FMath::Sin(Phase * 0.53f), static_cast<float>((DeadfallIndex * 41) % 360), 4.0f * FMath::Sin(Phase)),
            FVector(
                ThicknessScale,
                ThicknessScale * 0.72f,
                LengthScale * (0.74f + 0.10f * static_cast<float>(DeadfallIndex % 5)) *
                    FirstPartyOrganicDeadfallCylinderReplacement),
            DeadfallColor);
    }

    const float RemainingSquareFoliageCardCull = 0.48f;
    const float RemainingSquareCardOpacityDemotion = 0.42f;
    const float SquareFoliageCardArtifactDemotion = 0.16f;
    const int32 GrassCardCount = Spec.bDesertCanyon ? 10 : (Spec.bHasWaterfalls ? 18 : 14);
    for (int32 CardIndex = 0; CardIndex < GrassCardCount; ++CardIndex)
    {
        const float Side = (CardIndex % 2 == 0) ? -1.0f : 1.0f;
        const float T = static_cast<float>(CardIndex) / static_cast<float>(FMath::Max(1, GrassCardCount - 1));
        const float Phase = static_cast<float>(CardIndex) * 1.619f;
        const float BaseX = FMath::Lerp(950.0f, 25700.0f, T) + 150.0f * FMath::Sin(Phase * 1.13f);
        const float BaseOffset = ActiveRiverHalfWidth +
            (Spec.bDesertCanyon ? 740.0f : 290.0f) +
            (Spec.bDesertCanyon ? 1250.0f : (Spec.bHasWaterfalls ? 880.0f : 720.0f)) *
                FMath::Pow(FMath::Abs(FMath::Sin(Phase * 0.67f)), Spec.bHasWaterfalls ? 0.50f : 0.62f);
        float X = BaseX;
        float Y = GetPreviewRiverCenterY(Spec, X) + Side * BaseOffset;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 4; ++CandidateIndex)
        {
            const float CandidateX = BaseX + 95.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.29f);
            const float CandidateOffset = BaseOffset + 120.0f * FMath::Cos(Phase * 0.61f + static_cast<float>(CandidateIndex) * 0.97f);
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
            const float Score = VegetationT * (Spec.bDesertCanyon ? 0.45f : 1.35f) - WaterT * 0.55f +
                0.05f * FMath::Sin(Phase + static_cast<float>(CandidateIndex));
            if (Score > BestScore)
            {
                BestScore = Score;
                X = CandidateX;
                Y = CandidateY;
            }
        }

        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
        const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, X, Y);
        const FLinearColor BaseGrassColor = Spec.bDesertCanyon
            ? FLinearColor(0.30f, 0.30f, 0.15f)
            : (Spec.bHasWaterfalls ? FLinearColor(0.035f, 0.22f, 0.070f) : FLinearColor(0.16f, 0.34f, 0.12f));
        const FLinearColor TipColor = Spec.bDesertCanyon
            ? FLinearColor(0.47f, 0.42f, 0.20f)
            : (Spec.bHasWaterfalls ? FLinearColor(0.10f, 0.36f, 0.12f) : FLinearColor(0.28f, 0.44f, 0.15f));
        const FLinearColor CardColor = ScalePreviewColor(
            FMath::Lerp(BaseGrassColor, TipColor, FMath::Clamp(0.24f + VegetationT * 0.58f, 0.0f, 1.0f)),
            0.86f + 0.07f * static_cast<float>(CardIndex % 5));
        AddPreviewTranslucentMeshActor(
            World,
            PlaneMesh,
            FString::Printf(TEXT("RaftSim_BiomeBankGrassCard_%03d_%s"), CardIndex, *Spec.RiverId),
            FVector(X, Y, TerrainZ + (Spec.bHasWaterfalls ? 62.0f : 42.0f)),
            FRotator(64.0f + 5.0f * FMath::Sin(Phase), static_cast<float>((CardIndex * 37) % 360), 0.0f),
            FVector(
                (Spec.bHasWaterfalls ? 0.62f : (Spec.bDesertCanyon ? 0.42f : 0.48f)) *
                    SquareFoliageCardArtifactDemotion,
                (Spec.bHasWaterfalls ? 0.18f : 0.13f) * 0.28f,
                1.0f),
            CardColor,
            (Spec.bHasWaterfalls ? 0.09f : 0.08f) * RemainingSquareCardOpacityDemotion);
        if (!Spec.bDesertCanyon && CardIndex % 3 == 0)
        {
            AddPreviewOrganicBranchFrondActor(
                World,
                FString::Printf(TEXT("RaftSim_BiomeBankGrassOrganicCull_%03d_%s"), CardIndex, *Spec.RiverId),
                FVector(X + Side * 18.0f, Y - Side * 24.0f, TerrainZ + (Spec.bHasWaterfalls ? 52.0f : 34.0f)),
                static_cast<float>((CardIndex * 41 + 13) % 360),
                FVector(
                    (Spec.bHasWaterfalls ? 0.36f : 0.28f) * RemainingSquareFoliageCardCull,
                    (Spec.bHasWaterfalls ? 0.44f : 0.34f) * RemainingSquareFoliageCardCull,
                    (Spec.bHasWaterfalls ? 0.42f : 0.30f) * RemainingSquareFoliageCardCull),
                ScalePreviewColor(CardColor, Spec.bHasWaterfalls ? 0.72f : 0.76f),
                CardIndex + 19200,
                Spec.bHasWaterfalls,
                true);
        }
    }

    const int32 RootRunnerCount = Spec.bDesertCanyon ? 8 : (Spec.bHasWaterfalls ? 52 : 22);
    for (int32 RootIndex = 0; RootIndex < RootRunnerCount; ++RootIndex)
    {
        const float Side = (RootIndex % 2 == 0) ? -1.0f : 1.0f;
        const float T = static_cast<float>(RootIndex) / static_cast<float>(FMath::Max(1, RootRunnerCount - 1));
        const float Phase = static_cast<float>(RootIndex) * 1.047f;
        const float X = FMath::Lerp(1350.0f, 25400.0f, T) + 120.0f * FMath::Sin(Phase);
        const float Offset = ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 820.0f : 230.0f) +
            (Spec.bDesertCanyon ? 320.0f : 210.0f) * FMath::Abs(FMath::Sin(Phase * 0.79f));
        const float Y = GetPreviewRiverCenterY(Spec, X) + Side * Offset;
        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
        const FLinearColor RootColor = Spec.bHasWaterfalls
            ? FLinearColor(0.018f, 0.028f, 0.018f)
            : (Spec.bDesertCanyon ? FLinearColor(0.20f, 0.16f, 0.10f) : FLinearColor(0.18f, 0.12f, 0.070f));
        AddPreviewMeshActor(
            World,
            CylinderMesh,
            FString::Printf(TEXT("RaftSim_BiomeRootRunner_%03d_%s"), RootIndex, *Spec.RiverId),
            FVector(X, Y, TerrainZ + 11.0f),
            FRotator(90.0f + 2.5f * FMath::Sin(Phase * 0.61f), static_cast<float>((RootIndex * 53) % 360), 2.0f * FMath::Sin(Phase)),
            FVector(
                Spec.bHasWaterfalls ? 0.036f : 0.030f,
                Spec.bHasWaterfalls ? 0.026f : 0.022f,
                (Spec.bHasWaterfalls ? 1.05f : 0.72f) * FirstPartyOrganicRootRunnerCylinderReplacement),
            ScalePreviewColor(RootColor, 0.82f + 0.06f * static_cast<float>(RootIndex % 4)));
    }
}

void AddPreviewBiomeFoliageSilhouetteDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask,
    UStaticMesh* CylinderMesh,
    UStaticMesh* PlaneMesh)
{
    if (!World || !CylinderMesh || !PlaneMesh)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const int32 SilhouetteCount = Spec.bDesertCanyon ? 8 : (Spec.bHasWaterfalls ? 14 : 10);
    const float NearBankOffset = Spec.bDesertCanyon ? 760.0f : (Spec.bHasWaterfalls ? 520.0f : 560.0f);
    const float FarBankOffset = Spec.bDesertCanyon ? 2120.0f : (Spec.bHasWaterfalls ? 1550.0f : 1240.0f);
    const float RemainingSquareFoliageCardCull = 0.46f;
    const float FoliageCardVisibilityBreakupT = Spec.bHasWaterfalls ? 0.09f : 0.13f;

    for (int32 FoliageIndex = 0; FoliageIndex < SilhouetteCount; ++FoliageIndex)
    {
        const float T = static_cast<float>(FoliageIndex) / static_cast<float>(FMath::Max(1, SilhouetteCount - 1));
        const float Phase = static_cast<float>(FoliageIndex) * 1.427f;
        const float Side = (FoliageIndex % 2 == 0) ? -1.0f : 1.0f;
        const float BaseX = FMath::Lerp(1450.0f, 25800.0f, T) +
            180.0f * FMath::Sin(Phase * 1.17f) +
            80.0f * FMath::Sin(Phase * 0.43f);
        const float BaseOffset = ActiveRiverHalfWidth + NearBankOffset +
            FarBankOffset * FMath::Pow(FMath::Abs(FMath::Sin(Phase * 0.61f)), Spec.bDesertCanyon ? 0.80f : 0.56f);

        float X = BaseX;
        float SignedOffset = Side * BaseOffset;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 5; ++CandidateIndex)
        {
            const float CandidateX = BaseX + 155.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.09f);
            const float CandidateOffset = BaseOffset +
                180.0f * FMath::Sin(Phase * 0.52f + static_cast<float>(CandidateIndex) * 0.91f);
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
            const float BankPreference =
                1.0f - FMath::Clamp(FMath::Abs(CandidateOffset - (ActiveRiverHalfWidth + NearBankOffset + FarBankOffset * 0.38f)) / FMath::Max(1.0f, FarBankOffset), 0.0f, 1.0f);
            const float Score = Spec.bDesertCanyon
                ? BankPreference * 1.12f + (1.0f - WaterT) * 0.42f - VegetationT * 0.12f
                : BankPreference * 0.78f + VegetationT * (Spec.bHasWaterfalls ? 1.18f : 0.82f) - WaterT * 0.28f;
            if (Score > BestScore)
            {
                BestScore = Score;
                X = CandidateX;
                SignedOffset = Side * CandidateOffset;
            }
        }

        if (X < 2150.0f && FMath::Abs(SignedOffset) < ActiveRiverHalfWidth + 720.0f)
        {
            continue;
        }

        const float Y = GetPreviewRiverCenterY(Spec, X) + SignedOffset;
        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
        const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, Y);
        const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, X, Y);
        const float Yaw = static_cast<float>((FoliageIndex * 43) % 360);

        if (Spec.bHasWaterfalls && FoliageIndex % 8 == 0)
        {
            const FLinearColor VineColor = ScalePreviewColor(
                FMath::Lerp(FLinearColor(0.018f, 0.10f, 0.035f), Spec.FoliageColor, 0.64f + VegetationT * 0.22f),
                (0.72f + 0.06f * static_cast<float>(FoliageIndex % 4)) * FoliageCardVisibilityBreakupT);
            AddPreviewOrganicBranchFrondActor(
                World,
                FString::Printf(TEXT("RaftSim_RainforestVineCurtainOrganicCull_%03d_%s"), FoliageIndex, *Spec.RiverId),
                FVector(X, Y, TerrainZ + 215.0f + 20.0f * static_cast<float>(FoliageIndex % 3)),
                Yaw,
                FVector(
                    (0.34f + 0.05f * FMath::Abs(FMath::Sin(Phase))) * RemainingSquareFoliageCardCull,
                    (0.50f + 0.08f * static_cast<float>(FoliageIndex % 3)) * RemainingSquareFoliageCardCull,
                    (0.76f + 0.08f * static_cast<float>(FoliageIndex % 3)) * RemainingSquareFoliageCardCull),
                VineColor,
                FoliageIndex + 19400,
                true,
                true);
        }
        else if (Spec.bDesertCanyon)
        {
            const FLinearColor ScrubColor = ScalePreviewColor(
                FMath::Lerp(FLinearColor(0.22f, 0.23f, 0.12f), Spec.FoliageColor, 0.42f),
                0.78f + 0.07f * static_cast<float>(FoliageIndex % 5));
            AddPreviewOrganicBranchFrondActor(
                World,
                FString::Printf(TEXT("RaftSim_DesertScrubSilhouetteOrganicCull_%03d_%s"), FoliageIndex, *Spec.RiverId),
                FVector(X, Y, TerrainZ + 54.0f),
                Yaw,
                FVector(
                    (0.28f + 0.04f * static_cast<float>(FoliageIndex % 4)) * RemainingSquareFoliageCardCull,
                    0.24f * RemainingSquareFoliageCardCull,
                    0.22f * RemainingSquareFoliageCardCull),
                ScrubColor,
                FoliageIndex + 19500,
                false,
                true);
        }
        else
        {
            const FLinearColor BranchColor = Spec.bHasWaterfalls
                ? ScalePreviewColor(FMath::Lerp(FLinearColor(0.035f, 0.18f, 0.055f), Spec.FoliageColor, 0.70f + VegetationT * 0.18f), 0.92f)
                : ScalePreviewColor(FMath::Lerp(FLinearColor(0.12f, 0.25f, 0.075f), Spec.FoliageColor, 0.58f + VegetationT * 0.20f), 0.88f);
            AddPreviewOrganicBranchFrondActor(
                World,
                FString::Printf(TEXT("RaftSim_OrganicFoliageSilhouetteBranch_%03d_%s"), FoliageIndex, *Spec.RiverId),
                FVector(X, Y, TerrainZ + (Spec.bHasWaterfalls ? 170.0f : 118.0f)),
                Yaw,
                FVector(
                    Spec.bHasWaterfalls ? 0.88f + 0.12f * static_cast<float>(FoliageIndex % 5) : 0.58f + 0.08f * static_cast<float>(FoliageIndex % 4),
                    Spec.bHasWaterfalls ? 1.06f : 0.72f,
                    Spec.bHasWaterfalls ? 1.08f : 0.76f),
                BranchColor,
                FoliageIndex * 53 + 9400,
                Spec.bHasWaterfalls,
                false);
        }

        if (!Spec.bDesertCanyon && FoliageIndex % 7 == 0)
        {
            const FLinearColor StemColor = Spec.bHasWaterfalls
                ? ScalePreviewColor(FLinearColor(0.030f, 0.030f, 0.020f), 0.80f + WaterT * 0.18f)
                : ScalePreviewColor(FLinearColor(0.18f, 0.12f, 0.070f), 0.86f);
            AddPreviewMeshActor(
                World,
                CylinderMesh,
                FString::Printf(TEXT("RaftSim_RiparianBranchCluster_%03d_%s"), FoliageIndex, *Spec.RiverId),
                FVector(X + 22.0f * FMath::Sin(Phase), Y + 18.0f * FMath::Cos(Phase), TerrainZ + (Spec.bHasWaterfalls ? 88.0f : 58.0f)),
                FRotator(8.0f * FMath::Sin(Phase), Yaw + 18.0f, 0.0f),
                FVector(0.030f, 0.030f, Spec.bHasWaterfalls ? 1.28f : 0.78f),
                StemColor);
        }
    }
}

void AddPreviewDenseBiomeFoliageLayerDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask,
    UStaticMesh* CylinderMesh,
    UStaticMesh* PlaneMesh)
{
    if (!World || !CylinderMesh || !PlaneMesh)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const bool bRainforest = Spec.bHasWaterfalls;
    const float RemainingBlockyFoliageProxyCull = 0.38f;
    const int32 ClusterCount = Spec.bDesertCanyon ? 14 : (bRainforest ? 32 : 22);
    const float NearBankOffset = Spec.bDesertCanyon ? 1080.0f : (bRainforest ? 620.0f : 660.0f);
    const float FarBankOffset = Spec.bDesertCanyon ? 2200.0f : (bRainforest ? 1720.0f : 1360.0f);
    const float FirstPartyProceduralCanopyBlobDemotion =
        Spec.bDesertCanyon ? 0.60f : (bRainforest ? 0.48f : 0.54f);
    const float FoliageCardSilhouetteDemotion =
        (Spec.bDesertCanyon ? 0.64f : (bRainforest ? 0.44f : 0.50f)) * RemainingBlockyFoliageProxyCull;

    for (int32 ClusterIndex = 0; ClusterIndex < ClusterCount; ++ClusterIndex)
    {
        const float T = static_cast<float>(ClusterIndex) / static_cast<float>(FMath::Max(1, ClusterCount - 1));
        const float Phase = static_cast<float>(ClusterIndex) * 1.183f;
        const float Side = (ClusterIndex % 2 == 0) ? -1.0f : 1.0f;
        const float BaseX = FMath::Lerp(2200.0f, 26000.0f, T) +
            210.0f * FMath::Sin(Phase * 1.11f) +
            95.0f * FMath::Sin(Phase * 0.37f);
        const float OffsetWave = FMath::Pow(
            FMath::Abs(FMath::Sin(Phase * (Spec.bDesertCanyon ? 0.54f : 0.67f))),
            Spec.bDesertCanyon ? 0.78f : 0.50f);
        const float BaseOffset = ActiveRiverHalfWidth + NearBankOffset + FarBankOffset * OffsetWave;

        float X = BaseX;
        float SignedOffset = Side * BaseOffset;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 6; ++CandidateIndex)
        {
            const float CandidateX = BaseX + 180.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 0.89f);
            const float CandidateOffset = FMath::Max(
                ActiveRiverHalfWidth + NearBankOffset * 0.74f,
                BaseOffset + 210.0f * FMath::Sin(Phase * 0.47f + static_cast<float>(CandidateIndex) * 1.13f));
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
            const float BankPreference =
                1.0f - FMath::Clamp(
                    FMath::Abs(CandidateOffset - (ActiveRiverHalfWidth + NearBankOffset + FarBankOffset * 0.36f)) /
                        FMath::Max(1.0f, FarBankOffset),
                    0.0f,
                    1.0f);
            const float Score = Spec.bDesertCanyon
                ? BankPreference * 0.92f + (1.0f - WaterT) * 0.44f + (1.0f - VegetationT) * 0.12f
                : BankPreference * 0.62f + VegetationT * (bRainforest ? 1.34f : 0.94f) - WaterT * 0.52f;
            if (Score > BestScore)
            {
                BestScore = Score;
                X = CandidateX;
                SignedOffset = Side * CandidateOffset;
            }
        }

        if (X < 2600.0f && FMath::Abs(SignedOffset) < ActiveRiverHalfWidth + 950.0f)
        {
            continue;
        }

        const float Y = GetPreviewRiverCenterY(Spec, X) + SignedOffset;
        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
        const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, X, Y);
        const float Yaw = static_cast<float>((ClusterIndex * 41) % 360);
        const float SideNudge = 42.0f * Side;

        if (Spec.bDesertCanyon)
        {
            const FLinearColor ScrubColor = ScalePreviewColor(
                FMath::Lerp(FLinearColor(0.24f, 0.26f, 0.13f), FLinearColor(0.48f, 0.42f, 0.24f), 0.28f + 0.22f * VegetationT),
                0.78f + 0.08f * static_cast<float>(ClusterIndex % 5));
            AddPreviewOrganicBranchFrondActor(
                World,
                FString::Printf(TEXT("RaftSim_DenseBiomeFoliageDesertThicket_%03d_%s"), ClusterIndex, *Spec.RiverId),
                FVector(X, Y, TerrainZ + 48.0f + 6.0f * static_cast<float>(ClusterIndex % 3)),
                Yaw,
                FVector(
                    (0.22f + 0.04f * static_cast<float>(ClusterIndex % 4)) * RemainingBlockyFoliageProxyCull,
                    0.26f * RemainingBlockyFoliageProxyCull,
                    0.20f * RemainingBlockyFoliageProxyCull),
                ScrubColor,
                ClusterIndex + 20500,
                false,
                true);
            if (ClusterIndex % 3 == 0)
            {
                AddPreviewOrganicBranchFrondActor(
                    World,
                    FString::Printf(TEXT("RaftSim_DenseBiomeFoliageDesertThicket_%03dB_%s"), ClusterIndex, *Spec.RiverId),
                    FVector(X + 80.0f * FMath::Sin(Phase), Y + SideNudge, TerrainZ + 38.0f),
                    Yaw + 64.0f,
                    FVector(0.18f, 0.20f + 0.03f * static_cast<float>(ClusterIndex % 4), 0.16f) *
                        RemainingBlockyFoliageProxyCull,
                    ScalePreviewColor(ScrubColor, 0.86f),
                    ClusterIndex + 20600,
                    false,
                    true);
            }
            if (ClusterIndex % 7 == 0)
            {
                AddPreviewMeshActor(
                    World,
                    CylinderMesh,
                    FString::Printf(TEXT("RaftSim_DenseBiomeFoliageTrunkCluster_%03d_%s"), ClusterIndex, *Spec.RiverId),
                    FVector(X - 28.0f * Side, Y - 22.0f * Side, TerrainZ + 33.0f),
                    FRotator(5.0f * FMath::Sin(Phase), Yaw + 19.0f, 0.0f),
                    FVector(0.026f, 0.026f, 0.48f),
                    ScalePreviewColor(FLinearColor(0.18f, 0.14f, 0.085f), 0.82f));
            }
            continue;
        }

        const FLinearColor CanopyLow = bRainforest ? FLinearColor(0.020f, 0.095f, 0.030f) : FLinearColor(0.080f, 0.18f, 0.055f);
        const FLinearColor CanopyHigh = bRainforest ? FLinearColor(0.095f, 0.34f, 0.075f) : FLinearColor(0.19f, 0.34f, 0.095f);
        const FLinearColor CanopyColor = ScalePreviewColor(
            FMath::Lerp(CanopyLow, FMath::Lerp(Spec.FoliageColor, CanopyHigh, 0.42f), 0.54f + VegetationT * 0.26f),
            0.82f + 0.08f * static_cast<float>(ClusterIndex % 5));
        AddPreviewOrganicBranchFrondActor(
            World,
            FString::Printf(TEXT("RaftSim_DenseBiomeOrganicBranchFrondCanopy_%03d_%s"), ClusterIndex, *Spec.RiverId),
            FVector(X, Y, TerrainZ + (bRainforest ? 335.0f : 192.0f) + 22.0f * FMath::Sin(Phase)),
            Yaw,
            FVector(
                (bRainforest ? 1.28f + 0.14f * static_cast<float>(ClusterIndex % 5) : 0.84f + 0.10f * static_cast<float>(ClusterIndex % 4)) * FirstPartyProceduralCanopyBlobDemotion,
                (bRainforest ? 1.74f : 1.12f) * FirstPartyProceduralCanopyBlobDemotion,
                (bRainforest ? 1.44f : 0.96f) * (bRainforest ? 0.80f : 0.86f)),
            ScalePreviewColor(CanopyColor, bRainforest ? 0.84f : 0.88f),
            ClusterIndex * 59 + 10100,
            bRainforest,
            false);
        if (ClusterIndex % (bRainforest ? 2 : 3) == 0)
        {
            AddPreviewFineTwigCanopyLaceActor(
                World,
                FString::Printf(TEXT("RaftSim_DenseBiomeFineTwigCanopyLace_%03d_%s"), ClusterIndex, *Spec.RiverId),
                FVector(
                    X + 38.0f * FMath::Sin(Phase * 0.77f),
                    Y - Side * 36.0f,
                    TerrainZ + (bRainforest ? 354.0f : 206.0f) + 18.0f * FMath::Sin(Phase)),
                Yaw + 29.0f,
                FVector(
                    (bRainforest ? 1.04f + 0.10f * static_cast<float>(ClusterIndex % 4) : 0.66f + 0.08f * static_cast<float>(ClusterIndex % 3)) * FoliageCardSilhouetteDemotion,
                    (bRainforest ? 1.16f : 0.72f) * FoliageCardSilhouetteDemotion,
                    (bRainforest ? 0.78f : 0.46f) * (bRainforest ? 0.82f : 0.88f)),
                ScalePreviewColor(CanopyColor, bRainforest ? 0.62f : 0.62f),
                ClusterIndex * 89 + 16100,
                bRainforest);
        }

        const FLinearColor UnderstoryColor = ScalePreviewColor(
            FMath::Lerp(bRainforest ? FLinearColor(0.012f, 0.070f, 0.022f) : FLinearColor(0.085f, 0.17f, 0.050f), Spec.FoliageColor, 0.45f + VegetationT * 0.24f),
            0.74f + 0.07f * static_cast<float>(ClusterIndex % 4));
        AddPreviewOrganicBranchFrondActor(
            World,
            FString::Printf(TEXT("RaftSim_DenseBiomeOrganicBranchFrondUnderstory_%03d_%s"), ClusterIndex, *Spec.RiverId),
            FVector(X + 62.0f * FMath::Sin(Phase * 0.91f), Y + SideNudge, TerrainZ + (bRainforest ? 132.0f : 74.0f)),
            Yaw + 73.0f,
            FVector(
                (bRainforest ? 0.82f + 0.10f * static_cast<float>(ClusterIndex % 4) : 0.52f + 0.08f * static_cast<float>(ClusterIndex % 4)) * FoliageCardSilhouetteDemotion,
                (bRainforest ? 1.08f : 0.66f) * FoliageCardSilhouetteDemotion,
                (bRainforest ? 0.84f : 0.48f) * (bRainforest ? 0.84f : 0.88f)),
            UnderstoryColor,
            ClusterIndex * 61 + 11700,
            bRainforest,
            true);

        if (ClusterIndex % (bRainforest ? 3 : 4) == 0)
        {
            const FLinearColor TrunkColor = bRainforest
                ? ScalePreviewColor(FLinearColor(0.020f, 0.018f, 0.014f), 0.70f + 0.10f * VegetationT)
                : ScalePreviewColor(FLinearColor(0.16f, 0.10f, 0.060f), 0.82f);
            AddPreviewMeshActor(
                World,
                CylinderMesh,
                FString::Printf(TEXT("RaftSim_DenseBiomeFoliageTrunkCluster_%03d_%s"), ClusterIndex, *Spec.RiverId),
                FVector(X - 35.0f * Side, Y - 28.0f * Side, TerrainZ + (bRainforest ? 128.0f : 72.0f)),
                FRotator(7.0f * FMath::Sin(Phase), Yaw + 21.0f, 0.0f),
                FVector(0.034f, 0.034f, bRainforest ? 1.92f : 1.02f),
                TrunkColor);
        }

        if (bRainforest && ClusterIndex % 8 == 0)
        {
            const FLinearColor FrondColor = ScalePreviewColor(
                FMath::Lerp(FLinearColor(0.018f, 0.12f, 0.035f), Spec.FoliageColor, 0.72f),
                0.90f + 0.08f * static_cast<float>(ClusterIndex % 3));
            AddPreviewOrganicBranchFrondActor(
                World,
                FString::Printf(TEXT("RaftSim_DenseBiomeOrganicPalmFrondLattice_%03d_%s"), ClusterIndex, *Spec.RiverId),
                FVector(X + 88.0f * FMath::Cos(Phase), Y - SideNudge, TerrainZ + 235.0f + 20.0f * FMath::Sin(Phase)),
                Yaw + 116.0f,
                FVector(0.42f, 1.18f + 0.12f * static_cast<float>(ClusterIndex % 4), 0.84f),
                ScalePreviewColor(FrondColor, 0.72f),
                ClusterIndex * 67 + 12900,
                true,
                false);
        }
    }
}

void AddPreviewInstancedProceduralFoliageEquivalentDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask,
    UStaticMesh* SphereMesh,
    UStaticMesh* CylinderMesh)
{
    if (!World || !SphereMesh || !CylinderMesh)
    {
        return;
    }

    const bool bRainforest = Spec.bHasWaterfalls;
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float RemainingBlockyFoliageProxyCull = 0.42f;
    const float RemainingInstancedSphereFoliageBlobCull = 0.0f;
    const int32 ClusterCount = Spec.bDesertCanyon ? 12 : (bRainforest ? 28 : 18);
    const float NearBankOffset = Spec.bDesertCanyon ? 980.0f : (bRainforest ? 720.0f : 760.0f);
    const float FarBankOffset = Spec.bDesertCanyon ? 2350.0f : (bRainforest ? 1820.0f : 1480.0f);
    const float FirstPartyProceduralCanopyBlobDemotion =
        Spec.bDesertCanyon ? 0.62f : (bRainforest ? 0.46f : 0.52f);

    UInstancedStaticMeshComponent* CanopyInstances = AddPreviewInstancedMeshComponent(
        World,
        SphereMesh,
        FString::Printf(TEXT("RaftSim_InstancedProceduralFoliageCanopyLibrary_%s"), *Spec.RiverId),
        Spec.bDesertCanyon ? FLinearColor(0.22f, 0.25f, 0.12f) : ScalePreviewColor(Spec.FoliageColor, bRainforest ? 0.74f : 0.76f));
    UInstancedStaticMeshComponent* TrunkInstances = AddPreviewInstancedMeshComponent(
        World,
        CylinderMesh,
        FString::Printf(TEXT("RaftSim_InstancedProceduralFoliageTrunkLibrary_%s"), *Spec.RiverId),
        Spec.bDesertCanyon ? FLinearColor(0.18f, 0.13f, 0.075f) : FLinearColor(0.13f, 0.080f, 0.045f));
    UInstancedStaticMeshComponent* UnderstoryInstances = AddPreviewInstancedMeshComponent(
        World,
        SphereMesh,
        FString::Printf(TEXT("RaftSim_InstancedProceduralFoliageUnderstoryLibrary_%s"), *Spec.RiverId),
        Spec.bDesertCanyon ? FLinearColor(0.34f, 0.33f, 0.17f) : (bRainforest ? FLinearColor(0.025f, 0.14f, 0.045f) : FLinearColor(0.10f, 0.22f, 0.070f)));

    if (!CanopyInstances || !TrunkInstances || !UnderstoryInstances)
    {
        return;
    }

    for (int32 ClusterIndex = 0; ClusterIndex < ClusterCount; ++ClusterIndex)
    {
        const float T = static_cast<float>(ClusterIndex) / static_cast<float>(FMath::Max(1, ClusterCount - 1));
        const float Phase = static_cast<float>(ClusterIndex) * 1.307f;
        const float Side = (ClusterIndex % 2 == 0) ? -1.0f : 1.0f;
        const float BaseX = FMath::Lerp(2850.0f, 26050.0f, T) +
            265.0f * FMath::Sin(Phase * 0.94f) +
            110.0f * FMath::Sin(Phase * 0.31f);
        const float BaseOffset = ActiveRiverHalfWidth + NearBankOffset +
            FarBankOffset * FMath::Pow(FMath::Abs(FMath::Sin(Phase * 0.59f)), Spec.bDesertCanyon ? 0.76f : 0.52f);

        float X = BaseX;
        float SignedOffset = Side * BaseOffset;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 6; ++CandidateIndex)
        {
            const float CandidateX = BaseX + 210.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 0.97f);
            const float CandidateOffset = FMath::Max(
                ActiveRiverHalfWidth + NearBankOffset * 0.68f,
                BaseOffset + 230.0f * FMath::Sin(Phase * 0.42f + static_cast<float>(CandidateIndex) * 1.21f));
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
            const float BankPreference =
                1.0f - FMath::Clamp(
                    FMath::Abs(CandidateOffset - (ActiveRiverHalfWidth + NearBankOffset + FarBankOffset * 0.32f)) /
                        FMath::Max(1.0f, FarBankOffset),
                    0.0f,
                    1.0f);
            const float Score = Spec.bDesertCanyon
                ? BankPreference * 0.78f + (1.0f - WaterT) * 0.50f - VegetationT * 0.05f
                : BankPreference * 0.52f + VegetationT * (bRainforest ? 1.48f : 1.08f) - WaterT * 0.62f;
            if (Score > BestScore)
            {
                BestScore = Score;
                X = CandidateX;
                SignedOffset = Side * CandidateOffset;
            }
        }

        if (X < 3050.0f && FMath::Abs(SignedOffset) < ActiveRiverHalfWidth + 1120.0f)
        {
            continue;
        }

        const float Y = GetPreviewRiverCenterY(Spec, X) + SignedOffset;
        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
        const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, X, Y);
        const float Yaw = static_cast<float>((ClusterIndex * 37) % 360);

        if (Spec.bDesertCanyon)
        {
            const FVector ScrubScale(
                0.24f + 0.04f * static_cast<float>(ClusterIndex % 4),
                0.19f + 0.03f * static_cast<float>((ClusterIndex + 2) % 3),
                0.10f + 0.02f * static_cast<float>(ClusterIndex % 3));
            if (RemainingInstancedSphereFoliageBlobCull > 0.0f)
            {
                UnderstoryInstances->AddInstance(
                    FTransform(
                        FRotator(0.0f, Yaw, 0.0f),
                        FVector(X, Y, TerrainZ + 36.0f),
                        ScrubScale * RemainingInstancedSphereFoliageBlobCull),
                    true);
                if (ClusterIndex % 3 == 0)
                {
                    UnderstoryInstances->AddInstance(
                        FTransform(
                            FRotator(0.0f, Yaw + 58.0f, 0.0f),
                            FVector(X + 115.0f * FMath::Sin(Phase), Y + 68.0f * Side, TerrainZ + 30.0f),
                            FVector(ScrubScale.X * 0.78f, ScrubScale.Y * 0.90f, ScrubScale.Z * 0.86f) *
                                RemainingInstancedSphereFoliageBlobCull),
                        true);
                }
            }
            if (ClusterIndex % 8 == 0)
            {
                TrunkInstances->AddInstance(
                    FTransform(
                        FRotator(6.0f * FMath::Sin(Phase), Yaw + 20.0f, 0.0f),
                        FVector(X - 32.0f * Side, Y - 26.0f * Side, TerrainZ + 32.0f),
                        FVector(0.020f, 0.020f, 0.43f)),
                    true);
            }
            continue;
        }

        const int32 LobeCount = 3;
        const float CrownBaseZ = TerrainZ + (bRainforest ? 315.0f : 185.0f) + 22.0f * FMath::Sin(Phase);
        if (RemainingInstancedSphereFoliageBlobCull > 0.0f)
        {
            for (int32 LobeIndex = 0; LobeIndex < LobeCount; ++LobeIndex)
            {
                const float LobeAngle = FMath::DegreesToRadians(Yaw + static_cast<float>(LobeIndex) * (360.0f / static_cast<float>(LobeCount)));
                const float Radius = (LobeIndex == 0) ? 0.0f : (bRainforest ? 92.0f : 64.0f);
                const float LobeX = X + FMath::Cos(LobeAngle) * Radius;
                const float LobeY = Y + FMath::Sin(LobeAngle) * Radius;
                const float SizeNoise =
                    0.86f + 0.08f * static_cast<float>((ClusterIndex + LobeIndex) % 5) + VegetationT * 0.08f;
                CanopyInstances->AddInstance(
                    FTransform(
                        FRotator(0.0f, Yaw + static_cast<float>(LobeIndex) * 21.0f, 0.0f),
                        FVector(LobeX, LobeY, CrownBaseZ + 18.0f * static_cast<float>(LobeIndex % 3)),
                        FVector(
                            (bRainforest ? 0.44f : 0.30f) * SizeNoise * FirstPartyProceduralCanopyBlobDemotion *
                                RemainingBlockyFoliageProxyCull * RemainingInstancedSphereFoliageBlobCull,
                            (bRainforest ? 0.34f : 0.24f) * SizeNoise * FirstPartyProceduralCanopyBlobDemotion *
                                RemainingBlockyFoliageProxyCull * RemainingInstancedSphereFoliageBlobCull,
                            (bRainforest ? 0.22f : 0.17f) * SizeNoise * (bRainforest ? 0.78f : 0.84f) *
                                RemainingBlockyFoliageProxyCull * RemainingInstancedSphereFoliageBlobCull)),
                    true);
            }
        }

        TrunkInstances->AddInstance(
            FTransform(
                FRotator(6.0f * FMath::Sin(Phase), Yaw + 16.0f, 0.0f),
                FVector(X, Y, TerrainZ + (bRainforest ? 145.0f : 88.0f)),
                FVector(0.030f, 0.030f, bRainforest ? 2.22f : 1.32f)),
            true);

        const int32 UnderstoryCount = bRainforest ? 3 : 2;
        if (RemainingInstancedSphereFoliageBlobCull > 0.0f)
        {
            for (int32 UnderstoryIndex = 0; UnderstoryIndex < UnderstoryCount; ++UnderstoryIndex)
            {
                const float UnderstoryPhase = Phase + static_cast<float>(UnderstoryIndex) * 2.11f;
                const float UnderstoryX = X + 126.0f * FMath::Sin(UnderstoryPhase);
                const float UnderstoryY = Y + Side * (78.0f + 66.0f * static_cast<float>(UnderstoryIndex)) +
                    52.0f * FMath::Cos(UnderstoryPhase);
                const float UnderstoryZ =
                    GetPreviewTerrainHeightCm(Spec, UnderstoryX, UnderstoryY, TerrainRelief, HeightfieldPreview);
                UnderstoryInstances->AddInstance(
                    FTransform(
                        FRotator(0.0f, Yaw + 77.0f * static_cast<float>(UnderstoryIndex + 1), 0.0f),
                        FVector(UnderstoryX, UnderstoryY, UnderstoryZ + (bRainforest ? 72.0f : 45.0f)),
                        FVector(
                            bRainforest ? 0.22f + 0.03f * static_cast<float>(UnderstoryIndex) : 0.16f,
                            bRainforest ? 0.17f : 0.13f,
                            bRainforest ? 0.12f : 0.09f) *
                            RemainingInstancedSphereFoliageBlobCull),
                    true);
            }
        }
    }
}

void AddPreviewRaftForeground(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    UStaticMesh* CubeMesh,
    UStaticMesh* CylinderMesh,
    const FRaftSimPreviewImage* MaterialAtlasAlbedo)
{
    if (!World || !CubeMesh || !CylinderMesh)
    {
        return;
    }

    const FName ForegroundRaftProxyTag(TEXT("RaftSim_ForegroundRaft"));
    auto AddRaftProxyPart = [&](UStaticMesh* Mesh, const FString& Label, const FVector& Location, const FRotator& Rotation, const FVector& Scale, const FLinearColor& Color)
    {
        AStaticMeshActor* Actor = AddPreviewMeshActor(World, Mesh, Label, Location, Rotation, Scale, Color);
        if (Actor && Actor->GetStaticMeshComponent())
        {
            Actor->Tags.AddUnique(ForegroundRaftProxyTag);
            Actor->GetStaticMeshComponent()->SetCastShadow(false);
            Actor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        }
    };

    const float BaseX = -4100.0f;
    const float CenterY = GetPreviewRiverCenterY(Spec, BaseX);
    const float Z = -18.0f;
    const FLinearColor TubeColor = ApplyFirstPartyMaterialAtlasTint(
        Spec,
        MaterialAtlasAlbedo,
        RaftForegroundReviewMaterialTile,
        FMath::Lerp(ScalePreviewColor(Spec.RaftColor, 0.78f), FLinearColor(0.82f, 0.22f, 0.075f), 0.28f),
        0.28f,
        0.36f,
        0.18f);
    const FLinearColor TubeShadowColor = ApplyFirstPartyMaterialAtlasTint(
        Spec,
        MaterialAtlasAlbedo,
        RaftForegroundReviewMaterialTile,
        ScalePreviewColor(TubeColor, 0.72f),
        0.64f,
        0.54f,
        0.12f);
    const FLinearColor TubeHighlightColor = ApplyFirstPartyMaterialAtlasTint(
        Spec,
        MaterialAtlasAlbedo,
        RaftForegroundReviewMaterialTile,
        FMath::Lerp(TubeColor, FLinearColor(0.90f, 0.36f, 0.13f), 0.18f),
        0.18f,
        0.18f,
        0.10f);
    const FLinearColor FrameColor = ApplyFirstPartyMaterialAtlasTint(
        Spec,
        MaterialAtlasAlbedo,
        RaftForegroundReviewMaterialTile,
        Spec.bDesertCanyon ? FLinearColor(0.310f, 0.245f, 0.155f) : FLinearColor(0.245f, 0.215f, 0.150f),
        0.50f,
        0.70f,
        0.12f);
    const FLinearColor OarShaftColor = ApplyFirstPartyMaterialAtlasTint(
        Spec,
        MaterialAtlasAlbedo,
        RaftForegroundReviewMaterialTile,
        Spec.bDesertCanyon ? FLinearColor(0.600f, 0.410f, 0.220f) : FLinearColor(0.560f, 0.365f, 0.185f),
        0.30f,
        0.52f,
        0.10f);
    const FLinearColor OarBladeColor = ApplyFirstPartyMaterialAtlasTint(
        Spec,
        MaterialAtlasAlbedo,
        RaftForegroundReviewMaterialTile,
        Spec.bDesertCanyon ? FLinearColor(0.720f, 0.500f, 0.275f) : FLinearColor(0.680f, 0.295f, 0.125f),
        0.24f,
        0.46f,
        0.10f);
    const FLinearColor BowLineColor = FMath::Lerp(FLinearColor(0.40f, 0.34f, 0.22f), TubeColor, 0.25f);

    AddRaftProxyPart(
        CylinderMesh,
        FString::Printf(TEXT("RaftSim_ForegroundRaft_LeftTube_%s"), *Spec.RiverId),
        FVector(BaseX + 12.0f, CenterY - 88.0f, Z),
        FRotator(90.0f, 0.0f, 0.0f),
        FVector(0.145f, 0.145f, 1.20f),
        TubeColor);
    AddRaftProxyPart(
        CylinderMesh,
        FString::Printf(TEXT("RaftSim_ForegroundRaft_RightTube_%s"), *Spec.RiverId),
        FVector(BaseX + 12.0f, CenterY + 88.0f, Z),
        FRotator(90.0f, 0.0f, 0.0f),
        FVector(0.145f, 0.145f, 1.20f),
        TubeShadowColor);
    AddRaftProxyPart(
        CylinderMesh,
        FString::Printf(TEXT("RaftSim_ForegroundRaft_BowRounded_%s"), *Spec.RiverId),
        FVector(BaseX + 165.0f, CenterY, Z - 1.0f),
        FRotator(0.0f, 0.0f, 90.0f),
        FVector(0.080f, 0.080f, 0.82f),
        TubeColor);
    AddRaftProxyPart(
        CubeMesh,
        FString::Printf(TEXT("RaftSim_ForegroundRaft_Floor_%s"), *Spec.RiverId),
        FVector(BaseX - 24.0f, CenterY, -126.0f),
        FRotator::ZeroRotator,
        FVector(0.040f, 0.020f, 0.002f),
        ScalePreviewColor(FrameColor, 0.58f));
    AddRaftProxyPart(
        CylinderMesh,
        FString::Printf(TEXT("RaftSim_ForegroundRaft_FrameBarRounded_%s"), *Spec.RiverId),
        FVector(BaseX - 62.0f, CenterY, -4.0f),
        FRotator(0.0f, 0.0f, 90.0f),
        FVector(0.018f, 0.018f, 0.46f),
        ScalePreviewColor(FrameColor, 0.72f));

    for (int32 SeamIndex = 0; SeamIndex < 2; ++SeamIndex)
    {
        const float Side = (SeamIndex == 0) ? -1.0f : 1.0f;
        AddRaftProxyPart(
            CylinderMesh,
            FString::Printf(TEXT("RaftSim_ForegroundRaft_TubeSeamRounded_%d_%s"), SeamIndex, *Spec.RiverId),
            FVector(BaseX + 38.0f, CenterY + Side * 88.0f, Z + 16.0f),
            FRotator(90.0f, 0.0f, Side * 4.0f),
            FVector(0.010f, 0.010f, 0.38f),
            TubeHighlightColor);
    }

    const float OarLengthScale = Spec.bDesertCanyon ? 0.76f : 0.64f;
    const float OarBladeOffset = Spec.bDesertCanyon ? 372.0f : 330.0f;
    for (int32 OarIndex = 0; OarIndex < 2; ++OarIndex)
    {
        const float Side = (OarIndex == 0) ? -1.0f : 1.0f;
        AddRaftProxyPart(
            CylinderMesh,
            FString::Printf(TEXT("RaftSim_ForegroundRaft_OarShaftRounded_%d_%s"), OarIndex, *Spec.RiverId),
            FVector(BaseX + 42.0f, CenterY + Side * 196.0f, -9.0f + 1.0f * static_cast<float>(OarIndex)),
            FRotator(0.0f, Side * 4.0f, 90.0f + (Side > 0.0f ? 7.0f : -7.0f)),
            FVector(0.0065f, 0.0065f, OarLengthScale * 0.88f),
            OarShaftColor);
        AddRaftProxyPart(
            CubeMesh,
            FString::Printf(TEXT("RaftSim_ForegroundRaft_OarBlade_%d_%s"), OarIndex, *Spec.RiverId),
            FVector(BaseX + 158.0f, CenterY + Side * OarBladeOffset, -9.0f),
            FRotator(0.0f, 8.0f * Side, Side > 0.0f ? 13.0f : -13.0f),
            FVector(0.020f, 0.054f, 0.0025f),
            OarBladeColor);
    }

    AddRaftProxyPart(
        CylinderMesh,
        FString::Printf(TEXT("RaftSim_ForegroundRaft_BowLineRounded_%s"), *Spec.RiverId),
        FVector(BaseX + 118.0f, CenterY, -3.0f),
        FRotator(90.0f, 0.0f, 2.0f),
        FVector(0.006f, 0.006f, 0.32f),
        BowLineColor);
}

AActor* AddPreviewRiverEyeCenterArtifactCover(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec)
{
    if (!World)
    {
        return nullptr;
    }

    constexpr int32 XSteps = 320;
    constexpr int32 CrossSteps = 48;
    const float MinX = -5600.0f;
    const float MaxX = 11200.0f;
    const float WaterBaseZ = GetPreviewWaterSurfaceBaseZCm(Spec);
    const float HalfCoverWidthCm = Spec.bDesertCanyon ? 520.0f : 460.0f;
    const float RiverEyeTexturedCenterCoverT = 1.0f;
    const float RiverEyeCenterCoverFlowMottleGain = 1.0f;
    const FLinearColor RiverEyeCenterCoverDeepCurrentColor = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.30f, 0.245f, 0.145f, 1.0f), 0.18f)
        : FMath::Lerp(
              Spec.WaterColor,
              Spec.bHasWaterfalls ? FLinearColor(0.055f, 0.220f, 0.120f, 1.0f)
                                  : FLinearColor(0.065f, 0.260f, 0.155f, 1.0f),
              Spec.bHasWaterfalls ? 0.22f : 0.18f);
    const FLinearColor RiverEyeCenterCoverSkyHighlightColor = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.53f, 0.44f, 0.32f, 1.0f), 0.10f)
        : FMath::Lerp(
              Spec.WaterColor,
              Spec.bHasWaterfalls ? FLinearColor(0.28f, 0.44f, 0.27f, 1.0f)
                                  : FLinearColor(0.28f, 0.46f, 0.30f, 1.0f),
              0.11f);
    const float RiverEyeCenterCoverMacroRippleMottleT = 1.0f;
    const FLinearColor RiverEyeCenterCoverMacroShadowColor = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.22f, 0.185f, 0.125f, 1.0f), 0.30f)
        : FMath::Lerp(
              Spec.WaterColor,
              Spec.bHasWaterfalls ? FLinearColor(0.018f, 0.145f, 0.075f, 1.0f)
                                  : FLinearColor(0.026f, 0.180f, 0.095f, 1.0f),
              Spec.bHasWaterfalls ? 0.32f : 0.28f);
    const FLinearColor RiverEyeCenterCoverMacroHighlightColor = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.56f, 0.47f, 0.32f, 1.0f), 0.24f)
        : FMath::Lerp(
              Spec.WaterColor,
              Spec.bHasWaterfalls ? FLinearColor(0.18f, 0.46f, 0.26f, 1.0f)
                                  : FLinearColor(0.20f, 0.48f, 0.30f, 1.0f),
              0.28f);
    const FLinearColor RiverEyeCenterCoverCaptureQualityShadowColor = Spec.bDesertCanyon
        ? FLinearColor(0.300f, 0.250f, 0.175f, 1.0f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.060f, 0.255f, 0.135f, 1.0f)
                                : FLinearColor(0.070f, 0.275f, 0.160f, 1.0f));
    const FLinearColor RiverEyeCenterCoverCaptureQualityHighlightColor = Spec.bDesertCanyon
        ? FLinearColor(0.650f, 0.555f, 0.385f, 1.0f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.245f, 0.505f, 0.305f, 1.0f)
                                : FLinearColor(0.265f, 0.535f, 0.340f, 1.0f));

    TArray<FVector> Vertices;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve((XSteps + 1) * (CrossSteps + 1));
    UVs.Reserve((XSteps + 1) * (CrossSteps + 1));
    VertexColors.Reserve((XSteps + 1) * (CrossSteps + 1));
    Triangles.Reserve(XSteps * CrossSteps * 6);

    for (int32 XIndex = 0; XIndex <= XSteps; ++XIndex)
    {
        const float U = static_cast<float>(XIndex) / static_cast<float>(XSteps);
        const float X = FMath::Lerp(MinX, MaxX, U);
        const float CenterY = GetPreviewRiverCenterY(Spec, X);
        const float Width =
            HalfCoverWidthCm * (0.80f + 0.10f * FMath::Sin(X * 0.0021f) + 0.045f * FMath::Sin(X * 0.0056f));
        const float LongFeather =
            SmoothPreviewStep(0.0f, 0.06f, U) * (1.0f - SmoothPreviewStep(0.94f, 1.0f, U));
        for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
        {
            const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
            const float Lateral = FMath::Lerp(-Width, Width, V);
            const float EdgeT = FMath::Pow(FMath::Abs(V - 0.5f) * 2.0f, 1.25f);
            const float ChannelT = FMath::Pow(1.0f - FMath::Clamp(EdgeT, 0.0f, 1.0f), 0.58f);
            const float FlowMottle = FMath::Clamp(
                0.50f +
                    RiverEyeCenterCoverFlowMottleGain *
                        (0.21f * FMath::Sin(X * 0.0064f + Lateral * 0.0037f) +
                         0.13f * FMath::Sin(X * 0.0150f - Lateral * 0.0080f) +
                         0.08f * FMath::Sin((X + Lateral) * 0.0210f)),
                0.0f,
                1.0f);
            const float CoverMacroRippleNoise = FMath::Clamp(
                0.50f +
                    0.24f * FMath::Sin(X * 0.0044f + Lateral * 0.012f + EdgeT * 0.61f) +
                    0.20f * FMath::Sin(X * 0.0130f - Lateral * 0.021f) +
                    0.11f * FMath::Sin(X * 0.0300f + Lateral * 0.037f),
                0.0f,
                1.0f);
            const float CoverMacroRipplePatchT = FMath::Clamp(
                (0.46f + ChannelT * 0.34f + EdgeT * 0.12f) *
                    LongFeather *
                    RiverEyeCenterCoverMacroRippleMottleT,
                0.0f,
                1.0f);
            const float CoverMacroRippleShadowT =
                SmoothPreviewStep(0.12f, 0.43f, 1.0f - CoverMacroRippleNoise) * CoverMacroRipplePatchT;
            const float CoverMacroRippleHighlightT =
                SmoothPreviewStep(0.56f, 0.91f, CoverMacroRippleNoise) * CoverMacroRipplePatchT;
            const float DepthBandT = SmoothPreviewStep(0.36f, 0.78f, FlowMottle) * ChannelT * LongFeather;
            const float HighlightT =
                SmoothPreviewStep(0.66f, 0.95f, FlowMottle) * (Spec.bDesertCanyon ? 0.050f : 0.070f) * LongFeather;
            const float EdgeReblendT = FMath::Clamp(EdgeT * 0.26f, 0.0f, 0.22f);
            const float SurfaceWave =
                (FMath::Sin(X * 0.011f + Lateral * 0.016f) * (Spec.bDesertCanyon ? 0.9f : 1.4f) +
                 FMath::Sin(X * 0.023f - Lateral * 0.011f) * (Spec.bDesertCanyon ? 0.35f : 0.55f) * ChannelT +
                 (FlowMottle - 0.5f) * (Spec.bDesertCanyon ? 1.15f : 1.75f) * ChannelT +
                 (CoverMacroRippleNoise - 0.5f) * (Spec.bDesertCanyon ? 1.35f : 2.35f) * CoverMacroRipplePatchT) *
                LongFeather * RiverEyeTexturedCenterCoverT;
            FLinearColor CoverColor = FMath::Lerp(
                Spec.WaterColor,
                RiverEyeCenterCoverDeepCurrentColor,
                DepthBandT * (Spec.bDesertCanyon ? 0.42f : 0.50f) * RiverEyeTexturedCenterCoverT);
            CoverColor = FMath::Lerp(CoverColor, RiverEyeCenterCoverSkyHighlightColor, HighlightT);
            CoverColor = FMath::Lerp(
                CoverColor,
                RiverEyeCenterCoverMacroShadowColor,
                FMath::Clamp(CoverMacroRippleShadowT * (Spec.bDesertCanyon ? 0.120f : 0.150f), 0.0f, 0.160f));
            CoverColor = FMath::Lerp(
                CoverColor,
                RiverEyeCenterCoverMacroHighlightColor,
                FMath::Clamp(CoverMacroRippleHighlightT * (Spec.bDesertCanyon ? 0.110f : 0.145f), 0.0f, 0.154f));
            CoverColor = FMath::Lerp(CoverColor, Spec.WaterColor, EdgeReblendT);
            CoverColor = ScalePreviewColor(
                CoverColor,
                (Spec.bHasWaterfalls ? 1.085f : 1.025f) +
                    0.018f * FMath::Sin(X * 0.0180f + Lateral * 0.0100f) +
                    0.012f * FMath::Sin(X * 0.0410f - Lateral * 0.0170f));
            const float RiverEyeCenterCoverCaptureQualityTextureCell = FMath::Frac(
                FMath::Sin(static_cast<float>((XIndex + 41) * 173 + (CrossIndex + 19) * 269) * 12.9898f) *
                43758.5453f);
            const float RiverEyeCenterCoverCaptureQualityTextureFine = FMath::Clamp(
                0.50f +
                    0.28f * FMath::Sin(X * 0.108f + Lateral * 0.086f) +
                    0.22f * FMath::Sin(X * 0.177f - Lateral * 0.052f + ChannelT * 0.73f),
                0.0f,
                1.0f);
            const float RiverEyeCenterCoverCaptureQualityTextureNoise = FMath::Clamp(
                RiverEyeCenterCoverCaptureQualityTextureCell * 0.60f +
                    RiverEyeCenterCoverCaptureQualityTextureFine * 0.40f,
                0.0f,
                1.0f);
            const float RiverEyeCenterCoverCaptureQualityTextureT = FMath::Clamp(
                (0.34f + ChannelT * 0.42f + EdgeT * 0.16f) * LongFeather *
                    RiverEyeTexturedCenterCoverT,
                0.0f,
                Spec.bDesertCanyon ? 0.48f : 0.56f);
            CoverColor = FMath::Lerp(
                CoverColor,
                RiverEyeCenterCoverCaptureQualityShadowColor,
                FMath::Clamp(
                    SmoothPreviewStep(0.06f, 0.35f, 1.0f - RiverEyeCenterCoverCaptureQualityTextureNoise) *
                        RiverEyeCenterCoverCaptureQualityTextureT *
                        (Spec.bDesertCanyon ? 0.42f : 0.48f),
                    0.0f,
                    Spec.bDesertCanyon ? 0.44f : 0.50f));
            CoverColor = FMath::Lerp(
                CoverColor,
                RiverEyeCenterCoverCaptureQualityHighlightColor,
                FMath::Clamp(
                    SmoothPreviewStep(0.58f, 0.94f, RiverEyeCenterCoverCaptureQualityTextureNoise) *
                        RiverEyeCenterCoverCaptureQualityTextureT *
                        (Spec.bDesertCanyon ? 0.40f : 0.46f),
                    0.0f,
                    Spec.bDesertCanyon ? 0.42f : 0.48f));
            CoverColor = ScalePreviewColor(
                CoverColor,
                FMath::Clamp(
                    0.70f + RiverEyeCenterCoverCaptureQualityTextureNoise * 0.58f +
                        FlowMottle * 0.18f,
                    0.62f,
                    1.48f));
            const float RiverEyeCenterCoverPaletteSeed = FMath::Frac(
                FMath::Sin(static_cast<float>((XIndex + 227) * 503 + (CrossIndex + 137) * 661) * 12.9898f) *
                43758.5453f);
            const FLinearColor RiverEyeCenterCoverSedimentReflection = Spec.bDesertCanyon
                ? FLinearColor(0.625f, 0.410f, 0.225f, 1.0f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.065f, 0.300f, 0.145f, 1.0f)
                                        : FLinearColor(0.160f, 0.360f, 0.235f, 1.0f));
            const FLinearColor RiverEyeCenterCoverSkyReflection = Spec.bDesertCanyon
                ? FLinearColor(0.350f, 0.535f, 0.625f, 1.0f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.230f, 0.560f, 0.480f, 1.0f)
                                        : FLinearColor(0.315f, 0.610f, 0.540f, 1.0f));
            const FLinearColor RiverEyeCenterCoverDarkPocket = Spec.bDesertCanyon
                ? FLinearColor(0.230f, 0.285f, 0.330f, 1.0f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.018f, 0.175f, 0.095f, 1.0f)
                                        : FLinearColor(0.035f, 0.215f, 0.135f, 1.0f));
            const FLinearColor RiverEyeCenterCoverAeratedPatch = Spec.bDesertCanyon
                ? FLinearColor(0.835f, 0.785f, 0.610f, 1.0f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.590f, 0.810f, 0.630f, 1.0f)
                                        : FLinearColor(0.650f, 0.805f, 0.660f, 1.0f));
            const FLinearColor RiverEyeCenterCoverPaletteColor = RiverEyeCenterCoverPaletteSeed < 0.24f
                ? RiverEyeCenterCoverDarkPocket
                : (RiverEyeCenterCoverPaletteSeed < 0.50f
                       ? RiverEyeCenterCoverSedimentReflection
                       : (RiverEyeCenterCoverPaletteSeed < 0.76f
                              ? RiverEyeCenterCoverSkyReflection
                              : RiverEyeCenterCoverAeratedPatch));
            CoverColor = FMath::Lerp(
                CoverColor,
                RiverEyeCenterCoverPaletteColor,
                FMath::Clamp(
                    RiverEyeCenterCoverCaptureQualityTextureT *
                        (Spec.bDesertCanyon ? 0.54f : 0.46f) *
                        (0.72f + ChannelT * 0.20f + EdgeT * 0.08f),
                    0.0f,
                    Spec.bDesertCanyon ? 0.48f : 0.42f));
            const float RiverEyeCenterCoverLongBandNoise = FMath::Clamp(
                0.50f +
                    0.34f * FMath::Sin(X * 0.0058f + Lateral * 0.0115f + ChannelT * 0.33f) +
                    0.24f * FMath::Sin(X * 0.0140f - Lateral * 0.0068f) +
                    0.14f * FMath::Sin(X * 0.0300f + Lateral * 0.0210f),
                0.0f,
                1.0f);
            const FLinearColor RiverEyeCenterCoverLongBandA = Spec.bDesertCanyon
                ? FLinearColor(0.710f, 0.450f, 0.245f, 1.0f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.050f, 0.355f, 0.175f, 1.0f)
                                        : FLinearColor(0.115f, 0.405f, 0.255f, 1.0f));
            const FLinearColor RiverEyeCenterCoverLongBandB = Spec.bDesertCanyon
                ? FLinearColor(0.260f, 0.420f, 0.505f, 1.0f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.195f, 0.585f, 0.460f, 1.0f)
                                        : FLinearColor(0.255f, 0.585f, 0.505f, 1.0f));
            const FLinearColor RiverEyeCenterCoverLongBandC = Spec.bDesertCanyon
                ? FLinearColor(0.835f, 0.720f, 0.445f, 1.0f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.455f, 0.760f, 0.455f, 1.0f)
                                        : FLinearColor(0.540f, 0.750f, 0.520f, 1.0f));
            const FLinearColor RiverEyeCenterCoverLongBandColor = RiverEyeCenterCoverLongBandNoise < 0.34f
                ? RiverEyeCenterCoverLongBandA
                : (RiverEyeCenterCoverLongBandNoise < 0.68f ? RiverEyeCenterCoverLongBandB : RiverEyeCenterCoverLongBandC);
            CoverColor = FMath::Lerp(
                CoverColor,
                RiverEyeCenterCoverLongBandColor,
                FMath::Clamp(
                    SmoothPreviewStep(0.12f, 0.88f, FMath::Abs(RiverEyeCenterCoverLongBandNoise - 0.5f) * 2.0f) *
                        RiverEyeCenterCoverCaptureQualityTextureT *
                        (0.30f + ChannelT * 0.18f + EdgeT * 0.08f) *
                        (Spec.bDesertCanyon ? 1.14f : 1.0f),
                    0.0f,
                    Spec.bDesertCanyon ? 0.56f : 0.48f));
            const float RiverEyeIntegratedWaterEntropyCell = FMath::Frac(
                FMath::Sin(static_cast<float>((XIndex + 311) * 887 + (CrossIndex + 173) * 1117) * 12.9898f) *
                43758.5453f);
            const float RiverEyeIntegratedWaterEntropyFine = FMath::Clamp(
                0.50f +
                    0.34f * FMath::Sin(X * 0.122f + Lateral * 0.094f + ChannelT * 0.47f) +
                    0.24f * FMath::Sin(X * 0.207f - Lateral * 0.071f + FlowMottle * 0.59f) +
                    0.16f * FMath::Sin(X * 0.303f + Lateral * 0.151f),
                0.0f,
                1.0f);
            const float RiverEyeIntegratedWaterEntropyNoise = FMath::Clamp(
                RiverEyeIntegratedWaterEntropyCell * 0.48f + RiverEyeIntegratedWaterEntropyFine * 0.52f,
                0.0f,
                1.0f);
            const FLinearColor RiverEyeIntegratedWaterEntropyColor = RiverEyeIntegratedWaterEntropyNoise < 0.20f
                ? RiverEyeCenterCoverDarkPocket
                : (RiverEyeIntegratedWaterEntropyNoise < 0.46f
                       ? RiverEyeCenterCoverSedimentReflection
                       : (RiverEyeIntegratedWaterEntropyNoise < 0.74f
                              ? RiverEyeCenterCoverSkyReflection
                              : RiverEyeCenterCoverAeratedPatch));
            CoverColor = FMath::Lerp(
                CoverColor,
                RiverEyeIntegratedWaterEntropyColor,
                FMath::Clamp(
                    RiverEyeCenterCoverCaptureQualityTextureT *
                        (0.42f + ChannelT * 0.22f + EdgeT * 0.10f) *
                        (0.80f + RiverEyeIntegratedWaterEntropyNoise * 0.28f),
                    0.0f,
                    Spec.bDesertCanyon ? 0.60f : 0.54f));
            CoverColor = ScalePreviewColor(
                CoverColor,
                FMath::Clamp(
                    0.72f + RiverEyeIntegratedWaterEntropyNoise * 0.54f + RiverEyeCenterCoverLongBandNoise * 0.16f,
                    Spec.bDesertCanyon ? 0.66f : 0.62f,
                    Spec.bDesertCanyon ? 1.50f : 1.56f));
            const FLinearColor RiverEyeCenterCoverForegroundLumaFloor = Spec.bDesertCanyon
                ? FLinearColor(0.300f, 0.250f, 0.175f)
                : (Spec.bHasWaterfalls ? FLinearColor(0.060f, 0.255f, 0.135f)
                                        : FLinearColor(0.070f, 0.275f, 0.160f));
            CoverColor.R = FMath::Max(CoverColor.R, RiverEyeCenterCoverForegroundLumaFloor.R);
            CoverColor.G = FMath::Max(CoverColor.G, RiverEyeCenterCoverForegroundLumaFloor.G);
            CoverColor.B = FMath::Max(CoverColor.B, RiverEyeCenterCoverForegroundLumaFloor.B);
            CoverColor.A = 1.0f;
            const float RiverEyeCenterCoverCaptureQualityMicroReliefCm =
                (RiverEyeCenterCoverCaptureQualityTextureNoise - 0.5f) *
                (Spec.bDesertCanyon ? 10.5f : (Spec.bHasWaterfalls ? 14.0f : 12.0f)) *
                (0.46f + RiverEyeCenterCoverCaptureQualityTextureT) *
                FMath::Clamp(0.58f + ChannelT * 0.30f + EdgeT * 0.12f, 0.0f, 1.0f) +
                (RiverEyeIntegratedWaterEntropyNoise - 0.5f) *
                    (Spec.bDesertCanyon ? 7.0f : (Spec.bHasWaterfalls ? 9.5f : 8.5f)) *
                    RiverEyeCenterCoverCaptureQualityTextureT;
            Vertices.Add(FVector(
                X,
                CenterY + Lateral,
                WaterBaseZ + 132.0f + SurfaceWave + RiverEyeCenterCoverCaptureQualityMicroReliefCm));
            UVs.Add(FVector2D(U * 8.0f, V));
            VertexColors.Add(CoverColor);
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
    return AddPreviewProceduralMeshActor(
        World,
        FString::Printf(TEXT("RaftSim_RiverEyeCenterArtifactCover_%s"), *Spec.RiverId),
        Vertices,
        Triangles,
        Normals,
        UVs,
        Spec.WaterColor,
        LoadOrCreatePreviewWaterVertexColorMaterial(),
        &VertexColors);
}
} // namespace RaftSimEditorEnvironment
