#include "RaftSimEditorModule.h"

#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetCompilingManager.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/LightComponent.h"
#include "Components/MeshComponent.h"
#include "Components/ReflectionCaptureComponent.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/SkyLightComponent.h"
#include "Components/SphereReflectionCaptureComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkyAtmosphereComponent.h"
#include "Editor.h"
#include "Engine/DirectionalLight.h"
#include "Engine/Engine.h"
#include "Engine/ExponentialHeightFog.h"
#include "Engine/PointLight.h"
#include "Engine/SceneCapture2D.h"
#include "Engine/SkyLight.h"
#include "Engine/SphereReflectionCapture.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/Texture2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "EngineUtils.h"
#include "FileHelpers.h"
#include "Framework/Application/SlateApplication.h"
#include "Framework/Commands/UIAction.h"
#include "Framework/Docking/TabManager.h"
#include "GameFramework/Actor.h"
#include "GameFramework/PlayerStart.h"
#include "HAL/IConsoleManager.h"
#include "HAL/PlatformProcess.h"
#include "HAL/PlatformMisc.h"
#include "ImageUtils.h"
#include "IImageWrapper.h"
#include "IImageWrapperModule.h"
#include "Landscape.h"
#include "LandscapeComponent.h"
#include "LandscapeEditorModule.h"
#include "LandscapeFileFormatInterface.h"
#include "LandscapeNaniteComponent.h"
#include "LandscapeProxy.h"
#include "Materials/MaterialExpressionLandscapeLayerCoords.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpressionAbs.h"
#include "Materials/MaterialExpressionAdd.h"
#include "Materials/MaterialExpressionComponentMask.h"
#include "Materials/MaterialExpressionConstant.h"
#include "Materials/MaterialExpressionConstant2Vector.h"
#include "Materials/MaterialExpressionConstant3Vector.h"
#include "Materials/MaterialExpressionFrac.h"
#include "Materials/MaterialExpressionFresnel.h"
#include "Materials/MaterialExpressionLinearInterpolate.h"
#include "Materials/MaterialExpressionMultiply.h"
#include "Materials/MaterialExpressionOneMinus.h"
#include "Materials/MaterialExpressionSaturate.h"
#include "Materials/MaterialExpressionScalarParameter.h"
#include "Materials/MaterialExpressionSubtract.h"
#include "Materials/MaterialExpressionTextureCoordinate.h"
#include "Materials/MaterialExpressionTextureSampleParameter2D.h"
#include "Materials/MaterialExpressionVertexColor.h"
#include "Materials/MaterialExpressionVectorParameter.h"
#include "Materials/MaterialInstanceConstant.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/CommandLine.h"
#include "Misc/CoreDelegates.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Modules/ModuleManager.h"
#include "NaniteSceneProxy.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimEditorToolRegistry.h"
#include "RaftSimFeatureTuningEditorShell.h"
#include "RaftSimRapidRiverEditorShell.h"
#include "RaftSimReplayDebugViewer.h"
#include "RaftSimToolValidationActions.h"
#include "Styling/CoreStyle.h"
#include "ToolMenus.h"
#include "UObject/SavePackage.h"
#include "UObject/UnrealType.h"
#include "RenderingThread.h"
#include "ShaderCompiler.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SSeparator.h"
#include "Widgets/Layout/SUniformGridPanel.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/SWindow.h"

#define LOCTEXT_NAMESPACE "FRaftSimEditorModule"

DEFINE_LOG_CATEGORY_STATIC(LogRaftSimEditor, Log, All);

namespace
{
static const FName ReplayDebugViewerTabId(TEXT("RaftSim.ReplayDebugViewer"));
static const FName RapidRiverEditorTabId(TEXT("RaftSim.RapidRiverEditor"));
static const FName FeatureTuningEditorTabId(TEXT("RaftSim.FeatureTuningEditor"));
static const FName GeospatialValidatorTabId(TEXT("RaftSim.GeospatialValidator"));
static const FName VerticalSliceLauncherTabId(TEXT("RaftSim.VerticalSliceLauncher"));

struct FRaftSimEnvironmentPreviewSpec
{
    FString RiverId;
    FString DisplayName;
    FString MapPackagePath;
    FString SourceManifest;
    FString AerialDrapeImage;
    FString TerrainReliefImage;
    FString HeightfieldPreviewImage;
    FString WaterMaskImage;
    FString VegetationMaskImage;
    FString ElevationSample;
    FString SourceDrapeDescription;
    FString FlowBandId;
    FString FlowBandDisplayName;
    FString FlowBandSource;
    FString FlowVisualDescription;
    FLinearColor WaterColor = FLinearColor(0.05f, 0.26f, 0.32f);
    FLinearColor TerrainColor = FLinearColor(0.26f, 0.23f, 0.18f);
    FLinearColor RockColor = FLinearColor(0.35f, 0.33f, 0.29f);
    FLinearColor FoliageColor = FLinearColor(0.18f, 0.34f, 0.16f);
    FLinearColor RaftColor = FLinearColor(0.90f, 0.28f, 0.08f);
    float FlowReferenceDischargeCfs = -1.0f;
    float FlowWidthScale = 1.0f;
    float FlowFoamScale = 1.0f;
    float FlowWetBankScale = 1.0f;
    float FlowCurrentCueScale = 1.0f;
    float FlowWaterLevelOffsetCm = 0.0f;
    float CanyonHeightCm = 850.0f;
    float RiverHalfWidthCm = 360.0f;
    float BankWidthCm = 760.0f;
    float BendAmplitudeCm = 240.0f;
    float TerrainReliefAmplitudeCm = 0.0f;
    float HeightfieldPreviewAmplitudeCm = 0.0f;
    float HeightfieldLocalReliefAmplitudeCm = 0.0f;
    float HeightfieldSeamFeatherUv = 0.0f;
    float TerrainNormalSofteningBlend = 0.45f;
    int32 BoulderCount = 18;
    int32 FoliageCount = 32;
    int32 FoamTrainCount = 12;
    bool bHasWaterfalls = false;
    bool bDesertCanyon = false;
};

struct FRaftSimLandscapeImportCandidateSpec
{
    FRaftSimEnvironmentPreviewSpec PreviewSpec;
    FString HeightfieldRelativePath;
    FString HeightfieldManifestRelativePath;
    FString ImportContractRelativePath;
    FString MapPackagePath;
    float HorizontalSpanXCm = 32300.0f;
    float HorizontalSpanYCm = 5500.0f;
    float TargetReliefCm = 1000.0f;
};

struct FRaftSimLandscapeMaterialCandidateSettings
{
    float MacroMappingScale = 1008.0f;
    float DetailMappingScale = 128.0f;
    float DetailAlbedoWeight = 0.18f;
    float DetailNormalWeight = 0.32f;
    float DetailSurfaceResponseWeight = 0.30f;
    float EmissiveFillScale = 0.045f;
    float SpecularLevel = 0.16f;
    float RiverbedBlendWeight = 0.82f;
    float WetBankBlendWeight = 0.65f;
    float RiverbedRoughness = 0.78f;
    FLinearColor RiverbedColorScale = FLinearColor(0.22f, 0.32f, 0.28f, 0.0f);
    FLinearColor WetBankColorScale = FLinearColor(0.52f, 0.56f, 0.50f, 0.0f);
};

struct FRaftSimPreviewWaterMaterialResponse
{
    float EmissiveFillScale = 0.26f;
    float RoughnessScale = 0.18f;
    float RoughnessFloor = 0.28f;
    float SpecularLevel = 0.22f;
    float MeshNormalUpBlend = 0.15f;
    float NormalIntensity = 0.32f;
};

struct FRaftSimLandscapeCandidateWaterSettings
{
    float BaseColorScale = 1.05f;
    float EmissiveFillScale = 0.080f;
    float Roughness = 0.30f;
    float Specular = 0.45f;
    float Opacity = 0.30f;
    float NormalIntensity = 0.62f;
    float RefractionIor = 1.333f;
    float PhaseG = 0.15f;
    float VertexTintWeight = 0.65f;
    float RenderWidthScale = 1.20f;
    float RenderNormalUpBlend = 0.52f;
    float RenderDisplacementScale = 0.70f;
    float ReflectionFillIntensity = 0.16f;
    float SolverFieldEnable = 1.0f;
    float SolverMacroNormalWeight = 0.22f;
    float SolverDepthColorWeight = 0.20f;
    float SolverFieldRoughnessWeight = 0.10f;
    float SolverFroudeAerationWeight = 0.34f;
    float SolverSpeedVisualGain = 1.50f;
    float SolverFroudeVisualGain = 3.00f;
    float SolverSurfaceReliefScale = 0.09f;
    FLinearColor SurfaceTint = FLinearColor(0.025f, 0.115f, 0.095f, 0.0f);
    FLinearColor SolverDeepWaterTint = FLinearColor(0.012f, 0.072f, 0.060f, 0.0f);
    FLinearColor SolverAerationTint = FLinearColor(0.74f, 0.82f, 0.76f, 0.0f);
    FLinearColor ReflectionTint = FLinearColor(0.38f, 0.55f, 0.62f, 0.0f);
    FLinearColor ScatteringCoefficients = FLinearColor(0.0012f, 0.0025f, 0.0018f, 0.0f);
    FLinearColor AbsorptionCoefficients = FLinearColor(0.0045f, 0.0018f, 0.0013f, 0.0f);
    FLinearColor ColorScaleBehindWater = FLinearColor(0.90f, 0.96f, 0.92f, 0.0f);
};

FRaftSimLandscapeCandidateWaterSettings GetLandscapeCandidateWaterSettings(const FString& RiverId)
{
    FRaftSimLandscapeCandidateWaterSettings Settings;
    if (RiverId == TEXT("colorado_river"))
    {
        Settings.BaseColorScale = 0.88f;
        Settings.EmissiveFillScale = 0.065f;
        Settings.Roughness = 0.38f;
        Settings.Specular = 0.38f;
        Settings.Opacity = 0.55f;
        Settings.NormalIntensity = 0.45f;
        Settings.PhaseG = 0.05f;
        Settings.VertexTintWeight = 0.58f;
        Settings.RenderWidthScale = 1.17f;
        Settings.RenderNormalUpBlend = 0.60f;
        Settings.RenderDisplacementScale = 0.55f;
        Settings.ReflectionFillIntensity = 0.14f;
        Settings.SolverFieldEnable = 0.0f;
        Settings.SolverMacroNormalWeight = 0.0f;
        Settings.SolverDepthColorWeight = 0.0f;
        Settings.SolverFieldRoughnessWeight = 0.0f;
        Settings.SolverFroudeAerationWeight = 0.0f;
        Settings.SolverSpeedVisualGain = 0.0f;
        Settings.SolverFroudeVisualGain = 0.0f;
        Settings.SolverSurfaceReliefScale = 0.0f;
        Settings.SurfaceTint = FLinearColor(0.105f, 0.090f, 0.055f, 0.0f);
        Settings.ReflectionTint = FLinearColor(0.46f, 0.58f, 0.67f, 0.0f);
        Settings.ScatteringCoefficients = FLinearColor(0.0042f, 0.0023f, 0.0007f, 0.0f);
        Settings.AbsorptionCoefficients = FLinearColor(0.0014f, 0.0022f, 0.0040f, 0.0f);
        Settings.ColorScaleBehindWater = FLinearColor(0.84f, 0.76f, 0.62f, 0.0f);
    }
    else if (RiverId == TEXT("pacuare"))
    {
        Settings.BaseColorScale = 1.00f;
        Settings.EmissiveFillScale = 0.075f;
        Settings.Roughness = 0.32f;
        Settings.Specular = 0.42f;
        Settings.Opacity = 0.40f;
        Settings.NormalIntensity = 0.68f;
        Settings.PhaseG = 0.25f;
        Settings.VertexTintWeight = 0.62f;
        Settings.RenderWidthScale = 1.22f;
        Settings.RenderNormalUpBlend = 0.48f;
        Settings.RenderDisplacementScale = 0.78f;
        Settings.ReflectionFillIntensity = 0.15f;
        Settings.SolverFieldEnable = 0.0f;
        Settings.SolverMacroNormalWeight = 0.0f;
        Settings.SolverDepthColorWeight = 0.0f;
        Settings.SolverFieldRoughnessWeight = 0.0f;
        Settings.SolverFroudeAerationWeight = 0.0f;
        Settings.SolverSpeedVisualGain = 0.0f;
        Settings.SolverFroudeVisualGain = 0.0f;
        Settings.SolverSurfaceReliefScale = 0.0f;
        Settings.SurfaceTint = FLinearColor(0.018f, 0.095f, 0.065f, 0.0f);
        Settings.ReflectionTint = FLinearColor(0.32f, 0.48f, 0.54f, 0.0f);
        Settings.ScatteringCoefficients = FLinearColor(0.0008f, 0.0030f, 0.0018f, 0.0f);
        Settings.AbsorptionCoefficients = FLinearColor(0.0050f, 0.0012f, 0.0022f, 0.0f);
        Settings.ColorScaleBehindWater = FLinearColor(0.82f, 0.94f, 0.84f, 0.0f);
    }
    return Settings;
}

struct FRaftSimPhotographicCaptureSettings
{
    float SunIntensity = 5.20f;
    float SkyLightIntensity = 1.25f;
    float FogDensity = 0.0025f;
    float ExposureBias = -0.32f;
    float Saturation = 1.06f;
    float Contrast = 1.04f;
    float Sharpen = 0.24f;
    float Vignette = 0.06f;
    float FilmGrainIntensity = 0.0f;
    FLinearColor SunColor = FLinearColor(0.98f, 0.965f, 0.91f);
    FLinearColor FogColor = FLinearColor(0.52f, 0.57f, 0.50f);
};

FRaftSimPhotographicCaptureSettings GetPhotographicCaptureSettings(const FString& RiverId)
{
    FRaftSimPhotographicCaptureSettings Settings;
    if (RiverId == TEXT("colorado_river"))
    {
        Settings.SunIntensity = 6.40f;
        Settings.SkyLightIntensity = 1.05f;
        Settings.FogDensity = 0.0016f;
        Settings.ExposureBias = -0.38f;
        Settings.Saturation = 1.10f;
        Settings.Contrast = 1.07f;
        Settings.Sharpen = 0.26f;
        Settings.SunColor = FLinearColor(1.0f, 0.88f, 0.72f);
        Settings.FogColor = FLinearColor(0.64f, 0.57f, 0.47f);
    }
    else if (RiverId == TEXT("pacuare"))
    {
        Settings.SunIntensity = 4.60f;
        Settings.SkyLightIntensity = 1.45f;
        Settings.FogDensity = 0.0075f;
        Settings.ExposureBias = -0.18f;
        Settings.Saturation = 1.04f;
        Settings.Contrast = 1.03f;
        Settings.Sharpen = 0.22f;
        Settings.Vignette = 0.05f;
        Settings.SunColor = FLinearColor(0.90f, 0.97f, 0.91f);
        Settings.FogColor = FLinearColor(0.43f, 0.57f, 0.46f);
    }
    return Settings;
}

struct FRaftSimLandscapeCandidateFoliageSettings
{
    FLinearColor BroadleafFrontTint = FLinearColor(0.86f, 1.18f, 0.72f);
    FLinearColor BroadleafBackTint = FLinearColor(0.62f, 0.91f, 0.48f);
    FLinearColor BroadleafTransmissionTint = FLinearColor(0.48f, 0.80f, 0.36f);
    FLinearColor ConiferFrontTint = FLinearColor(0.72f, 1.00f, 0.52f);
    FLinearColor ConiferBackTint = FLinearColor(0.48f, 0.74f, 0.32f);
    FLinearColor ConiferTransmissionTint = FLinearColor(0.36f, 0.62f, 0.24f);
    float RoughnessStrength = 0.68f;
    float NormalStrength = 0.65f;
};

FRaftSimLandscapeCandidateFoliageSettings GetLandscapeCandidateFoliageSettings(
    const FString& RiverId)
{
    FRaftSimLandscapeCandidateFoliageSettings Settings;
    if (RiverId == TEXT("colorado_river"))
    {
        Settings.BroadleafFrontTint = FLinearColor(0.96f, 1.04f, 0.58f);
        Settings.BroadleafBackTint = FLinearColor(0.74f, 0.82f, 0.40f);
        Settings.BroadleafTransmissionTint = FLinearColor(0.62f, 0.72f, 0.34f);
        Settings.ConiferFrontTint = FLinearColor(0.82f, 0.90f, 0.48f);
        Settings.ConiferBackTint = FLinearColor(0.64f, 0.72f, 0.34f);
        Settings.ConiferTransmissionTint = FLinearColor(0.54f, 0.62f, 0.30f);
        Settings.RoughnessStrength = 0.82f;
        Settings.NormalStrength = 0.52f;
    }
    else if (RiverId == TEXT("pacuare"))
    {
        Settings.BroadleafFrontTint = FLinearColor(0.70f, 1.15f, 0.62f);
        Settings.BroadleafBackTint = FLinearColor(0.46f, 0.86f, 0.42f);
        Settings.BroadleafTransmissionTint = FLinearColor(0.34f, 0.72f, 0.30f);
        Settings.ConiferFrontTint = FLinearColor(0.60f, 1.00f, 0.50f);
        Settings.ConiferBackTint = FLinearColor(0.40f, 0.76f, 0.34f);
        Settings.ConiferTransmissionTint = FLinearColor(0.30f, 0.64f, 0.26f);
        Settings.RoughnessStrength = 0.74f;
        Settings.NormalStrength = 0.58f;
    }
    return Settings;
}

FRaftSimPreviewWaterMaterialResponse GetPreviewWaterMaterialResponse(const FString& RiverId)
{
    FRaftSimPreviewWaterMaterialResponse Response;
    if (RiverId == TEXT("colorado_river"))
    {
        Response.EmissiveFillScale = 0.28f;
        Response.RoughnessScale = 0.22f;
        Response.RoughnessFloor = 0.34f;
        Response.SpecularLevel = 0.18f;
        Response.MeshNormalUpBlend = 0.18f;
        Response.NormalIntensity = 0.22f;
    }
    else if (RiverId == TEXT("pacuare"))
    {
        Response.EmissiveFillScale = 0.26f;
        Response.RoughnessScale = 0.18f;
        Response.RoughnessFloor = 0.30f;
        Response.SpecularLevel = 0.22f;
        Response.MeshNormalUpBlend = 0.12f;
        Response.NormalIntensity = 0.36f;
    }
    return Response;
}

struct FRaftSimPreviewImage
{
    int32 Width = 0;
    int32 Height = 0;
    TArray<FLinearColor> Pixels;

    bool IsValid() const
    {
        return Width > 0 && Height > 0 && Pixels.Num() == Width * Height;
    }

    FLinearColor Sample(float U, float V) const
    {
        if (!IsValid())
        {
            return FLinearColor::Black;
        }

        const int32 X = FMath::Clamp(FMath::RoundToInt(U * static_cast<float>(Width - 1)), 0, Width - 1);
        const int32 Y = FMath::Clamp(FMath::RoundToInt((1.0f - V) * static_cast<float>(Height - 1)), 0, Height - 1);
        FLinearColor Sampled = Pixels[Y * Width + X];
        const float Luma = Sampled.R * 0.30f + Sampled.G * 0.59f + Sampled.B * 0.11f;
        Sampled.R = FMath::Clamp((Luma + (Sampled.R - Luma) * 1.45f) * 1.28f, 0.0f, 1.0f);
        Sampled.G = FMath::Clamp((Luma + (Sampled.G - Luma) * 1.65f) * 1.36f, 0.0f, 1.0f);
        Sampled.B = FMath::Clamp((Luma + (Sampled.B - Luma) * 1.35f) * 1.18f, 0.0f, 1.0f);
        Sampled.A = 1.0f;
        return Sampled;
    }

    FLinearColor SampleRaw(float U, float V) const
    {
        if (!IsValid())
        {
            return FLinearColor::Black;
        }

        const int32 X = FMath::Clamp(FMath::RoundToInt(U * static_cast<float>(Width - 1)), 0, Width - 1);
        const int32 Y = FMath::Clamp(FMath::RoundToInt((1.0f - V) * static_cast<float>(Height - 1)), 0, Height - 1);
        FLinearColor Sampled = Pixels[Y * Width + X];
        Sampled.A = 1.0f;
        return Sampled;
    }

    FLinearColor SampleRawBilinear(float U, float V) const
    {
        if (!IsValid())
        {
            return FLinearColor::Black;
        }

        const float PixelX = FMath::Clamp(U, 0.0f, 1.0f) * static_cast<float>(Width - 1);
        const float PixelY = (1.0f - FMath::Clamp(V, 0.0f, 1.0f)) * static_cast<float>(Height - 1);
        const int32 X0 = FMath::Clamp(FMath::FloorToInt(PixelX), 0, Width - 1);
        const int32 Y0 = FMath::Clamp(FMath::FloorToInt(PixelY), 0, Height - 1);
        const int32 X1 = FMath::Min(X0 + 1, Width - 1);
        const int32 Y1 = FMath::Min(Y0 + 1, Height - 1);
        const float FracX = PixelX - static_cast<float>(X0);
        const float FracY = PixelY - static_cast<float>(Y0);
        const FLinearColor Top = FMath::Lerp(Pixels[Y0 * Width + X0], Pixels[Y0 * Width + X1], FracX);
        const FLinearColor Bottom = FMath::Lerp(Pixels[Y1 * Width + X0], Pixels[Y1 * Width + X1], FracX);
        return FMath::Lerp(Top, Bottom, FracY);
    }

    float SampleLuma(float U, float V) const
    {
        if (!IsValid())
        {
            return 0.5f;
        }

        const int32 X = FMath::Clamp(FMath::RoundToInt(U * static_cast<float>(Width - 1)), 0, Width - 1);
        const int32 Y = FMath::Clamp(FMath::RoundToInt((1.0f - V) * static_cast<float>(Height - 1)), 0, Height - 1);
        const FLinearColor Sampled = Pixels[Y * Width + X];
        return FMath::Clamp(Sampled.R * 0.30f + Sampled.G * 0.59f + Sampled.B * 0.11f, 0.0f, 1.0f);
    }

    float SampleLumaBilinear(float U, float V) const
    {
        if (!IsValid())
        {
            return 0.5f;
        }

        const float PixelX = FMath::Clamp(U, 0.0f, 1.0f) * static_cast<float>(Width - 1);
        const float PixelY = (1.0f - FMath::Clamp(V, 0.0f, 1.0f)) * static_cast<float>(Height - 1);
        const int32 X0 = FMath::Clamp(FMath::FloorToInt(PixelX), 0, Width - 1);
        const int32 Y0 = FMath::Clamp(FMath::FloorToInt(PixelY), 0, Height - 1);
        const int32 X1 = FMath::Min(X0 + 1, Width - 1);
        const int32 Y1 = FMath::Min(Y0 + 1, Height - 1);
        const float FracX = PixelX - static_cast<float>(X0);
        const float FracY = PixelY - static_cast<float>(Y0);
        const auto LumaAt = [this](int32 X, int32 Y)
        {
            const FLinearColor& Pixel = Pixels[Y * Width + X];
            return FMath::Clamp(Pixel.R * 0.30f + Pixel.G * 0.59f + Pixel.B * 0.11f, 0.0f, 1.0f);
        };
        const float Top = FMath::Lerp(LumaAt(X0, Y0), LumaAt(X1, Y0), FracX);
        const float Bottom = FMath::Lerp(LumaAt(X0, Y1), LumaAt(X1, Y1), FracX);
        return FMath::Lerp(Top, Bottom, FracY);
    }
};

FRaftSimEditorToolDescriptor MakeToolDescriptor(
    FName ToolId,
    ERaftSimEditorToolKind ToolKind,
    const FText& DisplayName,
    const FText& Description,
    const FString& SourceManifest,
    const FString& RequiredModule,
    bool bRequiresValidationBeforeExport)
{
    FRaftSimEditorToolDescriptor Descriptor;
    Descriptor.ToolId = ToolId;
    Descriptor.ToolKind = ToolKind;
    Descriptor.DisplayName = DisplayName;
    Descriptor.Description = Description;
    Descriptor.SourceManifest = SourceManifest;
    Descriptor.RequiredModule = RequiredModule;
    Descriptor.bRequiresValidationBeforeExport = bRequiresValidationBeforeExport;
    return Descriptor;
}

FString GetRepoRoot()
{
    return FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectDir(), TEXT("..")));
}

FString GetCaptureRoot()
{
    return FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), TEXT("docs/tool-captures/milestone25a")));
}

FString GetEnvironmentCaptureRoot()
{
    return FPaths::ConvertRelativePathToFull(
        FPaths::Combine(GetRepoRoot(), TEXT("docs/environment-captures/photoreal_river_previews")));
}

FString GetPhotorealRiverSourcePlanRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json");
}

FString GetPhotorealFlowVariantCapturePlanRelativePath()
{
    return TEXT("docs/environment-captures/photoreal_river_previews/photoreal_flow_variant_capture_plan.json");
}

FString GetFirstPartyProceduralEnvironmentAssetPlanRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/first_party_procedural_environment_assets.json");
}

FString GetFirstPartyProceduralMaterialRecipePlanRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/first_party_procedural_material_recipes.json");
}

FString GetFirstPartyMaterialTextureAtlasManifestRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/ProceduralTextureAtlases/first_party_material_texture_atlas_manifest.json");
}

FString GetSourceConditionedMaterialMapManifestRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/SourceConditionedMaterialMaps/first_party_source_conditioned_material_map_manifest.json");
}

FString GetProductionDetailTextureManifestRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/ProductionDetailTextures/first_party_production_detail_texture_manifest.json");
}

FString GetFirstPartyMaterialInstanceCandidateManifestRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/first_party_material_instance_candidates.json");
}

FString GetFirstPartyMaterialInstanceReviewAssetRootRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Materials/MaterialInstances");
}

FString GetFirstPartyMaterialInstanceReviewAssetStatus()
{
    return TEXT("created_unreal_material_instance_constant_review_assets_with_texture_bindings_sampler_parent_and_scene_assignment_not_lifelike");
}

FString GetFirstPartyMaterialInstanceSceneAssignmentStatus()
{
    return TEXT("assigned_review_material_instances_to_preview_map_surface_proxies_not_lifelike");
}

FString GetFirstPartyMaterialTextureAssetRootRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/ProceduralTextureAtlases/Textures");
}

FString GetFirstPartyMaterialTextureAssetStatus()
{
    return TEXT("created_unreal_texture2d_review_assets_bound_to_material_instance_candidates_not_lifelike");
}

FString GetSourceConditionedMaterialTextureAssetRootRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/SourceConditionedMaterialMaps/Textures");
}

FString GetSourceConditionedMaterialTextureAssetStatus()
{
    return TEXT("created_unreal_texture2d_review_assets_bound_to_source_conditioned_material_instances_not_lifelike");
}

FString GetProductionDetailTextureAssetRootRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/ProductionDetailTextures/Textures");
}

FString GetProductionDetailTextureAssetStatus()
{
    return TEXT("created_unreal_first_party_terrain_detail_texture_candidates_bound_to_review_material_not_lifelike");
}

FString GetSolverVisualizationFieldManifestRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/SolverVisualizationFields/cpp_solver_visualization_field_manifest.json");
}

FString GetSolverVisualizationFieldTextureAssetRootRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/SolverVisualizationFields/Textures");
}

FString GetFirstPartyAtlasSampleReviewMaterialRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Materials/M_RaftSim_AtlasSampleReview.uasset");
}

FString GetFirstPartyAtlasSampleReviewMaterialStatus()
{
    return TEXT("created_unreal_atlas_sampler_review_parent_material_not_lifelike");
}

FString GetFirstPartyMaterialTextureAtlasAlbedoRelativePath(const FString& RiverId)
{
    return FString::Printf(
        TEXT("unreal/Content/RaftSim/Rendering/ProceduralTextureAtlases/%s_first_party_material_texture_atlas_albedo.png"),
        *RiverId);
}

FString GetFirstPartyMaterialTextureAtlasNormalRelativePath(const FString& RiverId)
{
    return FString::Printf(
        TEXT("unreal/Content/RaftSim/Rendering/ProceduralTextureAtlases/%s_first_party_material_texture_atlas_normal.png"),
        *RiverId);
}

FString GetFirstPartyMaterialTextureAtlasPackedRelativePath(const FString& RiverId)
{
    return FString::Printf(
        TEXT("unreal/Content/RaftSim/Rendering/ProceduralTextureAtlases/%s_first_party_material_texture_atlas_ao_roughness_height.png"),
        *RiverId);
}

FString GetSourceConditionedMaterialMapRelativePath(const FString& RiverId, const FString& MapKey)
{
    FString MapSuffix = TEXT("macro_albedo");
    if (MapKey == TEXT("SourceConditionedMaterialZones"))
    {
        MapSuffix = TEXT("material_zones");
    }
    else if (MapKey == TEXT("SourceConditionedAORoughnessHeight"))
    {
        MapSuffix = TEXT("ao_roughness_height");
    }
    else if (MapKey == TEXT("SourceConditionedNormalDetail"))
    {
        MapSuffix = TEXT("normal_detail");
    }

    return FString::Printf(
        TEXT("unreal/Content/RaftSim/Rendering/SourceConditionedMaterialMaps/%s_source_conditioned_%s.png"),
        *RiverId,
        *MapSuffix);
}

FString GetProductionDetailTextureRelativePath(const FString& RiverId, const FString& MapKey)
{
    FString MapSuffix = TEXT("albedo");
    if (MapKey == TEXT("TerrainDetailNormal"))
    {
        MapSuffix = TEXT("normal");
    }
    else if (MapKey == TEXT("TerrainDetailAORoughnessHeight"))
    {
        MapSuffix = TEXT("ao_roughness_height");
    }

    return FString::Printf(
        TEXT("unreal/Content/RaftSim/Rendering/ProductionDetailTextures/%s_terrain_bank_detail_v1_%s.png"),
        *RiverId,
        *MapSuffix);
}

FString GetProductionGeospatialAttachmentLedgerRelativePath()
{
    return TEXT("physics/data/real_world/production_geospatial_attachment_ledger.json");
}

class FScopedPhotorealPreviewWorldGcLeakFatalOverride
{
public:
    FScopedPhotorealPreviewWorldGcLeakFatalOverride()
    {
        WorldGcLeakFatalCVar =
            IConsoleManager::Get().FindConsoleVariable(TEXT("Editor.CheckForWorldGCLeaksAreFatal"));
        if (WorldGcLeakFatalCVar)
        {
            bPreviousValue = WorldGcLeakFatalCVar->GetBool();
            if (bPreviousValue)
            {
                WorldGcLeakFatalCVar->Set(false, ECVF_SetByCode);
                bChanged = true;
                UE_LOG(
                    LogRaftSimEditor,
                    Display,
                    TEXT("Temporarily setting Editor.CheckForWorldGCLeaksAreFatal=0 for photoreal preview automation."));
            }
        }
    }

    ~FScopedPhotorealPreviewWorldGcLeakFatalOverride()
    {
        if (bChanged && WorldGcLeakFatalCVar)
        {
            WorldGcLeakFatalCVar->Set(bPreviousValue, ECVF_SetByCode);
        }
    }

private:
    IConsoleVariable* WorldGcLeakFatalCVar = nullptr;
    bool bPreviousValue = false;
    bool bChanged = false;
};

FString EscapeRaftSimJsonString(const FString& Value)
{
    FString Escaped = Value.Replace(TEXT("\\"), TEXT("\\\\"));
    Escaped = Escaped.Replace(TEXT("\""), TEXT("\\\""));
    Escaped = Escaped.Replace(TEXT("\r"), TEXT("\\r"));
    Escaped = Escaped.Replace(TEXT("\n"), TEXT("\\n"));
    return Escaped;
}

TArray<FRaftSimEnvironmentPreviewSpec> GetEnvironmentPreviewSpecs()
{
    TArray<FRaftSimEnvironmentPreviewSpec> Specs;

    FRaftSimEnvironmentPreviewSpec SouthFork;
    SouthFork.RiverId = TEXT("american_south_fork");
    SouthFork.DisplayName = TEXT("South Fork American River");
    SouthFork.MapPackagePath = TEXT("/Game/RaftSim/Maps/EnvironmentPreviews/L_SouthForkAmerican_PhotorealPreview");
    SouthFork.SourceManifest = TEXT("physics/data/real_world/south_fork_american_chili_bar/source_manifest.json");
    SouthFork.AerialDrapeImage =
        TEXT("physics/data/real_world/south_fork_american_chili_bar/imagery/production_import_pilot/source_drape_4096.png");
    SouthFork.TerrainReliefImage =
        TEXT("physics/data/real_world/south_fork_american_chili_bar/terrain/production_import_pilot/dem_relief_2048.png");
    SouthFork.HeightfieldPreviewImage =
        TEXT("physics/data/real_world/south_fork_american_chili_bar/terrain/production_import_pilot/heightfield_candidate_2017.png");
    SouthFork.WaterMaskImage =
        TEXT("physics/data/real_world/south_fork_american_chili_bar/imagery/production_import_pilot/water_mask_2048.png");
    SouthFork.VegetationMaskImage =
        TEXT("physics/data/real_world/south_fork_american_chili_bar/imagery/production_import_pilot/vegetation_mask_2048.png");
    SouthFork.ElevationSample =
        TEXT("physics/data/real_world/south_fork_american_chili_bar/terrain/production_import_pilot/3dep_tiles");
    SouthFork.SourceDrapeDescription =
        TEXT("stitched South Fork production-import pilot source drape generated from four official USDA/APFO NAIP 2048px tiles, plus stitched USGS 3DEP pilot DEM relief and a review-gated 2017px heightfield candidate sampled into bank and valley preview geometry; pilot source water/vegetation masks are sampled into terrain color, source-aware terrain photo mottle/microrelief, source-conditioned far-bank albedo/microrelief calibration, first-party photographic color-grade palette compression, broad-slope terrain exposure fill and relief, source-aware macro terrain ridge/facet relief, source-aware terrain slope facet texture, first-party source-aware terrain surface granularity, source-aware riparian canopy mass texture, minimized source overlay plate artifacts, graphic waterline ribbon demotion, remaining water overlay slab demotion, long dark water streak demotion, current streak and waterline rail artifact demotion, central water scaffold plate demotion, base-water center guide-stripe breakup, base-water cross-channel breakup, base-water residual center-seam erase, dark micro-ripple artifact demotion, source-aware bank breakup patches, first-party source-masked bank/bar microgeometry, first-party near-field riverbed pebble/debris dressing, first-party irregular shoreline edge breakup, first-party source-masked shoreline lip/overhang edge breakup, first-party terrain material layer facets, first-party Landscape/Nanite material scaffold microfacets/strata/slope occlusion, first-party terrain erosion-rill/bank-gully strips, source-aware boulder wetness/abrasion/moss facets, biome-specific deadfall/log/grass/root ecology props, first-party biome foliage silhouette cards, dense layered riparian canopy/understory proxy clusters, first-party instanced procedural foliage-equivalent canopy/trunk/understory scaffold, first-party procedural-only foliage review path with stylized PCG sample tree meshes disabled, first-party procedural canopy height and massing profile, first-party procedural canopy tone compression and shadow profile, first-party foliage card/canopy artifact demotion, square foliage/source-card artifact demotion, remaining square card cull, first-party organic branch/frond lattice foliage, first-party fine twig canopy lace foliage, first-party foliage crown depth and leaflet breakup, lit water variation, first-party lit water normal-response scaffold, base-water flow-thread texture, flow-cued water foam/slick mottle, flow-dependent hydraulic aeration/spray mats and beads, flow-band depth texture ribbons, flow-aware surface chop/turbidity patches, turbidity-depth patch artifact demotion, first-party water shader depth/reflection/refraction scaffold, source-aware shallow-water clarity/aeration layers, deterministic wet-rock, talus, foliage, understory, mask-aware ground-cover cards, disabled guide-seat raft/oar foreground proxy hooks, river-specific atmospheric backdrop cards, and source-aware sky-gradient/depth layers; all pilot derivatives remain review-gated until metadata review, mosaic/clip, hydrologic conditioning, channel burning, masks, and guide/geospatial approval pass; rocks, foliage, water, foam, raft, and lighting still include first-party procedural proxy layers");
    SouthFork.FlowBandId = TEXT("median_runnable");
    SouthFork.FlowBandDisplayName = TEXT("Median Runnable / Summer Commercial");
    SouthFork.FlowBandSource = TEXT("physics/data/real_world/south_fork_american_chili_bar/flow_presets.json");
    SouthFork.FlowVisualDescription =
        TEXT("Default South Fork summer-commercial validation band from USGS-11445500 planning presets; keeps moderate tongues, wet rocks, and foam lines visible while low/high seasonal variants remain future capture targets.");
    SouthFork.FlowReferenceDischargeCfs = 1600.0f;
    SouthFork.WaterColor = FLinearColor(0.070f, 0.205f, 0.115f);
    SouthFork.TerrainColor = FLinearColor(0.35f, 0.30f, 0.21f);
    SouthFork.RockColor = FLinearColor(0.38f, 0.36f, 0.31f);
    SouthFork.FoliageColor = FLinearColor(0.16f, 0.29f, 0.105f);
    SouthFork.CanyonHeightCm = 850.0f;
    SouthFork.RiverHalfWidthCm = 335.0f;
    SouthFork.BankWidthCm = 720.0f;
    SouthFork.BendAmplitudeCm = 290.0f;
    SouthFork.TerrainReliefAmplitudeCm = 180.0f;
    SouthFork.HeightfieldPreviewAmplitudeCm = 620.0f;
    SouthFork.HeightfieldLocalReliefAmplitudeCm = 620.0f;
    SouthFork.HeightfieldSeamFeatherUv = 0.030f;
    SouthFork.TerrainNormalSofteningBlend = 0.52f;
    SouthFork.BoulderCount = 24;
    SouthFork.FoliageCount = 36;
    SouthFork.FoamTrainCount = 14;
    Specs.Add(SouthFork);

    FRaftSimEnvironmentPreviewSpec Colorado;
    Colorado.RiverId = TEXT("colorado_river");
    Colorado.DisplayName = TEXT("Colorado River Grand Canyon");
    Colorado.MapPackagePath = TEXT("/Game/RaftSim/Maps/EnvironmentPreviews/L_ColoradoGrandCanyon_PhotorealPreview");
    Colorado.SourceManifest = TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/source_manifest.json");
    Colorado.AerialDrapeImage =
        TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/imagery/production_import_pilot/source_drape_4096.png");
    Colorado.TerrainReliefImage =
        TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/terrain/production_import_pilot/dem_relief_2048.png");
    Colorado.HeightfieldPreviewImage =
        TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/terrain/production_import_pilot/heightfield_candidate_2017.png");
    Colorado.WaterMaskImage =
        TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/imagery/production_import_pilot/water_mask_2048.png");
    Colorado.VegetationMaskImage =
        TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/imagery/production_import_pilot/vegetation_mask_2048.png");
    Colorado.ElevationSample =
        TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/terrain/production_import_pilot/3dep_tiles");
    Colorado.SourceDrapeDescription =
        TEXT("stitched Colorado/Lees Ferry production-import pilot source drape generated from four official USDA/APFO NAIP 2048px tiles, plus stitched USGS 3DEP pilot DEM relief and a review-gated 2017px heightfield candidate sampled into canyon bank preview geometry; pilot source water/vegetation masks are sampled into terrain color, source-aware terrain photo mottle/microrelief, source-conditioned far-bank albedo/microrelief calibration, first-party photographic color-grade palette compression, broad-slope terrain exposure fill and relief, source-aware macro terrain ridge/facet relief, source-aware terrain slope facet texture, first-party source-aware terrain surface granularity, source-aware riparian canopy mass texture, minimized source overlay plate artifacts, graphic waterline ribbon demotion, remaining water overlay slab demotion, long dark water streak demotion, current streak and waterline rail artifact demotion, central water scaffold plate demotion, base-water center guide-stripe breakup, base-water cross-channel breakup, base-water residual center-seam erase, dark micro-ripple artifact demotion, source-aware bank breakup patches, first-party source-masked bank/bar microgeometry, first-party near-field riverbed pebble/debris dressing, first-party irregular shoreline edge breakup, first-party source-masked shoreline lip/overhang edge breakup, first-party terrain material layer facets, first-party Landscape/Nanite material scaffold microfacets/strata/slope occlusion, first-party terrain erosion-rill/bank-gully strips, source-aware boulder wetness/abrasion/sediment facets, biome-specific sparse deadfall/grass/root ecology props, first-party sparse desert scrub silhouettes, sparse desert riparian thicket proxy clusters, first-party instanced procedural desert-thicket/trunk scaffold, first-party procedural-only foliage review path with stylized PCG sample tree meshes disabled, first-party procedural canopy height and massing profile, first-party procedural canopy tone compression and shadow profile, first-party foliage card/canopy artifact demotion, square foliage/source-card artifact demotion, remaining square card cull, first-party foliage crown depth and leaflet breakup, lit water variation, first-party lit water normal-response scaffold, base-water flow-thread texture, flow-cued water foam/slick mottle, flow-dependent hydraulic aeration/spray mats and beads, flow-band depth texture ribbons, flow-aware surface chop/turbidity patches, turbidity-depth patch artifact demotion, first-party water shader depth/reflection/refraction scaffold, source-aware shallow-water clarity/aeration layers, deterministic wet-rock, talus, sparse scrub, boulder placement, mask-aware canyon ground-cover cards, disabled guide-seat raft/oar foreground proxy hooks, river-specific atmospheric backdrop cards, and source-aware sky-gradient/depth layers; all pilot derivatives remain review-gated until metadata review, mosaic/clip, river-mile stationing, hydrologic conditioning, release-aware masks, and guide/oarsman approval pass; rocks, foliage, water, foam, raft, and lighting still include first-party procedural proxy layers");
    Colorado.FlowBandId = TEXT("moderate_release_planning");
    Colorado.FlowBandDisplayName = TEXT("Moderate Release Planning");
    Colorado.FlowBandSource = TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/flow_presets.json");
    Colorado.FlowVisualDescription =
        TEXT("Default Grand Canyon rowing preview band from release-planning presets; slightly widens the big-water ribbon and strengthens long wave/current cues while release history and guide review remain required.");
    Colorado.FlowReferenceDischargeCfs = 12000.0f;
    Colorado.FlowWidthScale = 1.08f;
    Colorado.FlowFoamScale = 1.15f;
    Colorado.FlowWetBankScale = 1.10f;
    Colorado.FlowCurrentCueScale = 1.15f;
    Colorado.FlowWaterLevelOffsetCm = 8.0f;
    Colorado.WaterColor = FLinearColor(0.320f, 0.255f, 0.175f);
    Colorado.TerrainColor = FLinearColor(0.48f, 0.30f, 0.18f);
    Colorado.RockColor = FLinearColor(0.55f, 0.32f, 0.20f);
    Colorado.FoliageColor = FLinearColor(0.30f, 0.32f, 0.18f);
    Colorado.CanyonHeightCm = 2600.0f;
    Colorado.RiverHalfWidthCm = 520.0f;
    Colorado.BankWidthCm = 1500.0f;
    Colorado.BendAmplitudeCm = 360.0f;
    Colorado.TerrainReliefAmplitudeCm = 650.0f;
    Colorado.HeightfieldPreviewAmplitudeCm = 2200.0f;
    Colorado.HeightfieldLocalReliefAmplitudeCm = 1500.0f;
    Colorado.HeightfieldSeamFeatherUv = 0.035f;
    Colorado.TerrainNormalSofteningBlend = 0.38f;
    Colorado.BoulderCount = 20;
    Colorado.FoliageCount = 16;
    Colorado.FoamTrainCount = 9;
    Colorado.bDesertCanyon = true;
    Specs.Add(Colorado);

    FRaftSimEnvironmentPreviewSpec Pacuare;
    Pacuare.RiverId = TEXT("pacuare");
    Pacuare.DisplayName = TEXT("Pacuare River Rainforest");
    Pacuare.MapPackagePath = TEXT("/Game/RaftSim/Maps/EnvironmentPreviews/L_PacuareRainforest_PhotorealPreview");
    Pacuare.SourceManifest = TEXT("physics/data/real_world/pacuare_river_costa_rica/source_manifest.json");
    Pacuare.AerialDrapeImage =
        TEXT("physics/data/real_world/pacuare_river_costa_rica/imagery/production_import_pilot/sentinel_augmented_source_drape_preview_4096.png");
    Pacuare.TerrainReliefImage =
        TEXT("physics/data/real_world/pacuare_river_costa_rica/terrain/production_import_pilot/dem_relief_2048.png");
    Pacuare.HeightfieldPreviewImage =
        TEXT("physics/data/real_world/pacuare_river_costa_rica/terrain/production_import_pilot/heightfield_candidate_2017.png");
    Pacuare.WaterMaskImage =
        TEXT("physics/data/real_world/pacuare_river_costa_rica/imagery/production_import_pilot/water_mask_2048.png");
    Pacuare.VegetationMaskImage =
        TEXT("physics/data/real_world/pacuare_river_costa_rica/imagery/production_import_pilot/vegetation_mask_2048.png");
    Pacuare.ElevationSample =
        TEXT("physics/data/real_world/pacuare_river_costa_rica/terrain/copernicus_dem_glo30_N09_W084.tif; physics/data/real_world/pacuare_river_costa_rica/terrain/copernicus_dem_glo30_N10_W084.tif");
    Pacuare.SourceDrapeDescription =
        TEXT("review-gated Pacuare Sentinel-augmented preview calibration drape generated from the coarse NASA GIBS/Copernicus 4096px placeholder plus low-opacity March 20 2025 Sentinel bbox clip color/detail; this is an Unreal preview input only, not a production source-drape replacement, route imagery claim, mask source, photoreal material source, or lifelike evidence; DEM relief, heightfield, and masks remain the production-import derivative placeholders until higher-resolution cloud-screened imagery, local hydrology/hydrography, protected-area review, and guide/outfitter validation are attached; first-party procedural rainforest leaf-litter, wet-rock, talus, mist, source-aware terrain photo mottle/microrelief, source-conditioned far-bank albedo/microrelief calibration, first-party photographic color-grade palette compression, broad-slope terrain exposure fill and relief, source-aware macro terrain ridge/facet relief, source-aware terrain slope facet texture, first-party source-aware terrain surface granularity, source-aware riparian canopy mass texture, minimized source overlay plate artifacts, graphic waterline ribbon demotion, remaining water overlay slab demotion, long dark water streak demotion, current streak and waterline rail artifact demotion, central water scaffold plate demotion, base-water center guide-stripe breakup, base-water cross-channel breakup, base-water residual center-seam erase, dark micro-ripple artifact demotion, source-aware bank breakup patches, first-party source-masked bank/bar microgeometry, first-party near-field riverbed pebble/debris dressing, first-party irregular shoreline edge breakup, first-party source-masked shoreline lip/overhang edge breakup, first-party terrain material layer facets, first-party Landscape/Nanite material scaffold microfacets/strata/slope occlusion, first-party terrain erosion-rill/bank-gully strips, source-aware boulder wetness/abrasion/moss facets, biome-specific deadfall/log/grass/root ecology props, rainforest canopy/vine silhouette cards, dense layered rainforest canopy/understory proxy clusters, first-party instanced procedural rainforest canopy/trunk/understory scaffold, first-party procedural-only foliage review path with stylized PCG sample tree meshes disabled, first-party procedural canopy height and massing profile, first-party procedural canopy tone compression and shadow profile, first-party foliage card/canopy artifact demotion, square foliage/source-card artifact demotion, remaining square card cull, first-party organic branch/frond lattice foliage, first-party fine twig canopy lace foliage, first-party foliage crown depth and leaflet breakup, waterfall curtain/plunge-mist proxy layers, lit water variation, first-party lit water normal-response scaffold, base-water flow-thread texture, flow-cued water foam/slick mottle, flow-dependent hydraulic aeration/spray mats and beads, flow-band depth texture ribbons, flow-aware surface chop/turbidity patches, turbidity-depth patch artifact demotion, first-party water shader depth/reflection/refraction scaffold, source-aware shallow-water clarity/aeration layers, dense mask-aware ground-cover/canopy cards, disabled guide-seat raft/oar foreground proxy hooks, humid atmospheric backdrop cards, and source-aware sky-gradient/depth layers remain rights-safe proxy dressing; rocks, foliage, water, foam, raft, and lighting still include first-party procedural proxy layers");
    Pacuare.FlowBandId = TEXT("rainfed_runnable_planning");
    Pacuare.FlowBandDisplayName = TEXT("Rain-Fed Runnable Planning");
    Pacuare.FlowBandSource = TEXT("physics/data/real_world/pacuare_river_costa_rica/flow_presets.json");
    Pacuare.FlowVisualDescription =
        TEXT("Default Pacuare planning band uses relative rainfed-runnable context only; numeric discharge stays unset until Costa Rica gauge, rainfall, flash-response, and guide review clear it.");
    Pacuare.FlowWidthScale = 1.05f;
    Pacuare.FlowFoamScale = 1.20f;
    Pacuare.FlowWetBankScale = 1.20f;
    Pacuare.FlowCurrentCueScale = 1.18f;
    Pacuare.FlowWaterLevelOffsetCm = 7.0f;
    Pacuare.WaterColor = FLinearColor(0.050f, 0.190f, 0.095f);
    Pacuare.TerrainColor = FLinearColor(0.17f, 0.22f, 0.13f);
    Pacuare.RockColor = FLinearColor(0.20f, 0.24f, 0.20f);
    Pacuare.FoliageColor = FLinearColor(0.035f, 0.20f, 0.055f);
    Pacuare.CanyonHeightCm = 1450.0f;
    Pacuare.RiverHalfWidthCm = 305.0f;
    Pacuare.BankWidthCm = 680.0f;
    Pacuare.BendAmplitudeCm = 340.0f;
    Pacuare.TerrainReliefAmplitudeCm = 420.0f;
    Pacuare.HeightfieldPreviewAmplitudeCm = 1500.0f;
    Pacuare.HeightfieldLocalReliefAmplitudeCm = 1050.0f;
    Pacuare.HeightfieldSeamFeatherUv = 0.035f;
    Pacuare.TerrainNormalSofteningBlend = 0.42f;
    Pacuare.BoulderCount = 22;
    Pacuare.FoliageCount = 62;
    Pacuare.FoamTrainCount = 16;
    Pacuare.bHasWaterfalls = true;
    Specs.Add(Pacuare);

    return Specs;
}

TArray<FRaftSimLandscapeImportCandidateSpec> GetLandscapeImportCandidateSpecs()
{
    TArray<FRaftSimLandscapeImportCandidateSpec> Candidates;
    for (const FRaftSimEnvironmentPreviewSpec& PreviewSpec : GetEnvironmentPreviewSpecs())
    {
        FRaftSimLandscapeImportCandidateSpec Candidate;
        Candidate.PreviewSpec = PreviewSpec;
        Candidate.HorizontalSpanYCm = PreviewSpec.bDesertCanyon ? 8600.0f : 5500.0f;
        Candidate.TargetReliefCm = PreviewSpec.HeightfieldPreviewAmplitudeCm;

        if (PreviewSpec.RiverId == TEXT("american_south_fork"))
        {
            Candidate.HeightfieldRelativePath =
                TEXT("physics/data/real_world/south_fork_american_chili_bar/terrain/usgs_3dep_chili_bar_corridor_heightfield_1009.png");
            Candidate.HeightfieldManifestRelativePath =
                TEXT("physics/data/real_world/south_fork_american_chili_bar/terrain/usgs_3dep_chili_bar_corridor_heightfield_manifest.json");
            Candidate.ImportContractRelativePath =
                TEXT("unreal/Content/RaftSim/River/south_fork_heightfield_import_test.json");
            Candidate.MapPackagePath =
                TEXT("/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/L_SouthForkAmerican_SourceLandscapeCandidate");
        }
        else if (PreviewSpec.RiverId == TEXT("colorado_river"))
        {
            Candidate.HeightfieldRelativePath =
                TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/terrain/usgs_3dep_lees_ferry_corridor_heightfield_1009.png");
            Candidate.HeightfieldManifestRelativePath =
                TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/terrain/usgs_3dep_lees_ferry_corridor_heightfield_manifest.json");
            Candidate.ImportContractRelativePath =
                TEXT("unreal/Content/RaftSim/River/colorado_heightfield_import_test.json");
            Candidate.MapPackagePath =
                TEXT("/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/L_ColoradoGrandCanyon_SourceLandscapeCandidate");
        }
        else if (PreviewSpec.RiverId == TEXT("pacuare"))
        {
            Candidate.HeightfieldRelativePath =
                TEXT("physics/data/real_world/pacuare_river_costa_rica/terrain/pacuare_copernicus_dem_corridor_heightfield_1009.png");
            Candidate.HeightfieldManifestRelativePath =
                TEXT("physics/data/real_world/pacuare_river_costa_rica/terrain/pacuare_copernicus_dem_corridor_heightfield_manifest.json");
            Candidate.ImportContractRelativePath =
                TEXT("unreal/Content/RaftSim/River/pacuare_heightfield_import_test.json");
            Candidate.MapPackagePath =
                TEXT("/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/L_Pacuare_SourceLandscapeCandidate");
        }
        else
        {
            continue;
        }

        Candidate.PreviewSpec.MapPackagePath = Candidate.MapPackagePath;
        Candidates.Add(MoveTemp(Candidate));
    }
    return Candidates;
}

FRaftSimLandscapeMaterialCandidateSettings GetLandscapeMaterialCandidateSettings(const FString& RiverId)
{
    FRaftSimLandscapeMaterialCandidateSettings Settings;
    if (RiverId == TEXT("american_south_fork"))
    {
        Settings.DetailMappingScale = 128.0f;
    }
    else if (RiverId == TEXT("colorado_river"))
    {
        Settings.DetailMappingScale = 144.0f;
        Settings.DetailAlbedoWeight = 0.16f;
        Settings.DetailNormalWeight = 0.28f;
        Settings.EmissiveFillScale = 0.035f;
        Settings.SpecularLevel = 0.14f;
        Settings.RiverbedBlendWeight = 0.78f;
        Settings.WetBankBlendWeight = 0.58f;
        Settings.RiverbedRoughness = 0.84f;
        Settings.RiverbedColorScale = FLinearColor(0.36f, 0.28f, 0.20f, 0.0f);
        Settings.WetBankColorScale = FLinearColor(0.58f, 0.44f, 0.34f, 0.0f);
    }
    else if (RiverId == TEXT("pacuare"))
    {
        Settings.DetailMappingScale = 112.0f;
        Settings.DetailAlbedoWeight = 0.20f;
        Settings.DetailNormalWeight = 0.36f;
        Settings.DetailSurfaceResponseWeight = 0.32f;
        Settings.EmissiveFillScale = 0.055f;
        Settings.RiverbedBlendWeight = 0.84f;
        Settings.WetBankBlendWeight = 0.72f;
        Settings.RiverbedRoughness = 0.72f;
        Settings.RiverbedColorScale = FLinearColor(0.22f, 0.30f, 0.24f, 0.0f);
        Settings.WetBankColorScale = FLinearColor(0.42f, 0.50f, 0.40f, 0.0f);
    }
    return Settings;
}

FString MakeFlowVariantPreviewMapPackagePath(const FRaftSimEnvironmentPreviewSpec& BaseSpec)
{
    const FString BaseDirectory = FPaths::GetPath(BaseSpec.MapPackagePath);
    const FString BaseName = FPackageName::GetShortName(BaseSpec.MapPackagePath);
    return FPaths::Combine(
        BaseDirectory,
        TEXT("FlowVariants"),
        FString::Printf(TEXT("%s_%s"), *BaseName, *BaseSpec.FlowBandId));
}

FRaftSimEnvironmentPreviewSpec MakeFlowVariantPreviewSpec(
    const FRaftSimEnvironmentPreviewSpec& BaseSpec,
    const FString& FlowBandId,
    const FString& FlowBandDisplayName,
    const FString& FlowVisualDescription,
    float FlowReferenceDischargeCfs,
    float FlowWidthScale,
    float FlowFoamScale,
    float FlowWetBankScale,
    float FlowCurrentCueScale,
    float FlowWaterLevelOffsetCm)
{
    FRaftSimEnvironmentPreviewSpec Variant = BaseSpec;
    Variant.FlowBandId = FlowBandId;
    Variant.FlowBandDisplayName = FlowBandDisplayName;
    Variant.FlowVisualDescription = FlowVisualDescription;
    Variant.FlowReferenceDischargeCfs = FlowReferenceDischargeCfs;
    Variant.FlowWidthScale = FlowWidthScale;
    Variant.FlowFoamScale = FlowFoamScale;
    Variant.FlowWetBankScale = FlowWetBankScale;
    Variant.FlowCurrentCueScale = FlowCurrentCueScale;
    Variant.FlowWaterLevelOffsetCm = FlowWaterLevelOffsetCm;
    Variant.MapPackagePath = MakeFlowVariantPreviewMapPackagePath(Variant);
    return Variant;
}

TArray<FRaftSimEnvironmentPreviewSpec> GetEnvironmentPreviewFlowVariantSpecs()
{
    TArray<FRaftSimEnvironmentPreviewSpec> Variants;
    const TArray<FRaftSimEnvironmentPreviewSpec> BaseSpecs = GetEnvironmentPreviewSpecs();
    for (const FRaftSimEnvironmentPreviewSpec& BaseSpec : BaseSpecs)
    {
        if (BaseSpec.RiverId == TEXT("american_south_fork"))
        {
            Variants.Add(MakeFlowVariantPreviewSpec(
                BaseSpec,
                TEXT("low_runnable"),
                TEXT("Low Runnable"),
                TEXT("South Fork low-runnable review band: expose more rocks and shallows, tighten tongues, reduce foam, and preserve rescue/hazard readability before guide approval."),
                900.0f,
                0.92f,
                0.75f,
                0.85f,
                0.82f,
                -8.0f));
            Variants.Add(MakeFlowVariantPreviewSpec(
                BaseSpec,
                TEXT("median_runnable"),
                TEXT("Median Runnable / Summer Commercial"),
                TEXT("South Fork median summer-commercial review band with readable tongues, wet rocks, eddy lines, and moderate wave trains."),
                1600.0f,
                1.0f,
                1.0f,
                1.0f,
                1.0f,
                0.0f));
            Variants.Add(MakeFlowVariantPreviewSpec(
                BaseSpec,
                TEXT("high_runnable"),
                TEXT("High Runnable"),
                TEXT("South Fork high-water review band: raise wet banks, strengthen laterals and wave trains, and keep boulder hazards visible instead of visually washing them away."),
                3000.0f,
                1.12f,
                1.25f,
                1.25f,
                1.25f,
                12.0f));
        }
        else if (BaseSpec.RiverId == TEXT("colorado_river"))
        {
            Variants.Add(MakeFlowVariantPreviewSpec(
                BaseSpec,
                TEXT("low_release_planning"),
                TEXT("Low Release Planning"),
                TEXT("Colorado low-release planning band with more exposed bars and sharper ferry setup while preserving big-water scale and swimmer visibility."),
                8000.0f,
                0.96f,
                0.85f,
                0.88f,
                0.90f,
                -6.0f));
            Variants.Add(MakeFlowVariantPreviewSpec(
                BaseSpec,
                TEXT("moderate_release_planning"),
                TEXT("Moderate Release Planning"),
                TEXT("Colorado moderate-release planning band with longer tongues, lateral waves, broad current streaks, and default oar-rig sightline readability."),
                12000.0f,
                1.08f,
                1.15f,
                1.10f,
                1.15f,
                8.0f));
            Variants.Add(MakeFlowVariantPreviewSpec(
                BaseSpec,
                TEXT("high_release_planning"),
                TEXT("High Release Planning"),
                TEXT("Colorado high-release review band with faster big-water read, stronger wave trains, eddy fences, and inspectable shore/rescue cues."),
                18000.0f,
                1.18f,
                1.35f,
                1.30f,
                1.35f,
                18.0f));
        }
        else if (BaseSpec.RiverId == TEXT("pacuare"))
        {
            Variants.Add(MakeFlowVariantPreviewSpec(
                BaseSpec,
                TEXT("clear_season_low_planning"),
                TEXT("Clear-Season Low Planning"),
                TEXT("Pacuare clear-season low planning band with exposed rocks, tighter tongues, clearer shallow-water cues, and reduced bank-pressure visuals."),
                -1.0f,
                0.90f,
                0.80f,
                0.88f,
                0.82f,
                -9.0f));
            Variants.Add(MakeFlowVariantPreviewSpec(
                BaseSpec,
                TEXT("rainfed_runnable_planning"),
                TEXT("Rain-Fed Runnable Planning"),
                TEXT("Pacuare rainfed runnable planning band with pushy tongues, active wave trains, wet banks, and vegetation pressure after rain."),
                -1.0f,
                1.05f,
                1.20f,
                1.20f,
                1.18f,
                7.0f));
            Variants.Add(MakeFlowVariantPreviewSpec(
                BaseSpec,
                TEXT("rainy_season_high_planning"),
                TEXT("Rainy-Season High Planning"),
                TEXT("Pacuare rainy-season high planning band with faster reaction windows, larger laterals, fewer visible eddies, and stronger swimmer drift cues."),
                -1.0f,
                1.18f,
                1.40f,
                1.35f,
                1.35f,
                20.0f));
            Variants.Add(MakeFlowVariantPreviewSpec(
                BaseSpec,
                TEXT("flash_response_review_only"),
                TEXT("Flash Response Review Only"),
                TEXT("Pacuare flash-response review-only band blocked from playable use until hydrology and guide review define safe visual and gameplay boundaries."),
                -1.0f,
                1.30f,
                1.55f,
                1.50f,
                1.55f,
                34.0f));
        }
    }

    return Variants;
}

UStaticMesh* LoadPreviewMesh(const TCHAR* MeshPath)
{
    return Cast<UStaticMesh>(StaticLoadObject(UStaticMesh::StaticClass(), nullptr, MeshPath));
}

UMaterialInterface* LoadPreviewBaseMaterial()
{
    return Cast<UMaterialInterface>(
        StaticLoadObject(UMaterialInterface::StaticClass(), nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")));
}

UMaterialInterface* LoadPreviewMaterial(const TCHAR* MaterialPath)
{
    return Cast<UMaterialInterface>(StaticLoadObject(UMaterialInterface::StaticClass(), nullptr, MaterialPath));
}

void ConnectPreviewMaterialColorInput(FColorMaterialInput& Input, UMaterialExpression* Expression)
{
    Input.Expression = Expression;
    Input.Mask = 1;
    Input.MaskR = 1;
    Input.MaskG = 1;
    Input.MaskB = 1;
    Input.MaskA = 0;
}

void ConnectPreviewMaterialVectorInput(FVectorMaterialInput& Input, UMaterialExpression* Expression)
{
    Input.Expression = Expression;
    Input.Mask = 1;
    Input.MaskR = 1;
    Input.MaskG = 1;
    Input.MaskB = 1;
    Input.MaskA = 0;
}

void ConnectPreviewMaterialScalarInput(FScalarMaterialInput& Input, UMaterialExpression* Expression)
{
    Input.Expression = Expression;
}

UMaterialInterface* LoadOrCreatePreviewColorMaterial()
{
    static const TCHAR* MaterialPackagePath = TEXT("/Game/RaftSim/Materials/M_RaftSim_LitColorPreview");
    static const TCHAR* MaterialObjectPath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_LitColorPreview.M_RaftSim_LitColorPreview");

    UMaterial* Material = Cast<UMaterial>(StaticLoadObject(UMaterial::StaticClass(), nullptr, MaterialObjectPath));
    if (!Material)
    {
        UPackage* Package = CreatePackage(MaterialPackagePath);
        if (!Package)
        {
            return nullptr;
        }

        Material = NewObject<UMaterial>(
            Package,
            TEXT("M_RaftSim_LitColorPreview"),
            RF_Public | RF_Standalone | RF_Transactional);
        if (!Material)
        {
            return nullptr;
        }

        FAssetRegistryModule::AssetCreated(Material);
        Material->Modify();
        Material->SetShadingModel(MSM_DefaultLit);
        Material->BlendMode = BLEND_Opaque;
        Material->TwoSided = true;

        UMaterialExpressionVectorParameter* ColorParameter = NewObject<UMaterialExpressionVectorParameter>(Material);
        ColorParameter->ParameterName = TEXT("PreviewColor");
        ColorParameter->DefaultValue = FLinearColor::White;
        Material->GetExpressionCollection().AddExpression(ColorParameter);

        UMaterialExpressionConstant* EmissiveScale = NewObject<UMaterialExpressionConstant>(Material);
        EmissiveScale->R = 0.22f;
        Material->GetExpressionCollection().AddExpression(EmissiveScale);

        UMaterialExpressionMultiply* EmissiveColor = NewObject<UMaterialExpressionMultiply>(Material);
        EmissiveColor->A.Expression = ColorParameter;
        EmissiveColor->B.Expression = EmissiveScale;
        Material->GetExpressionCollection().AddExpression(EmissiveColor);

        UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
        ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, ColorParameter);
        ConnectPreviewMaterialColorInput(EditorOnlyData->EmissiveColor, EmissiveColor);

        Material->PostEditChange();
        Package->MarkPackageDirty();

        const FString Filename =
            FPackageName::LongPackageNameToFilename(MaterialPackagePath, FPackageName::GetAssetPackageExtension());
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);

        FSavePackageArgs SaveArgs;
        SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
        SaveArgs.SaveFlags = SAVE_NoError;
        UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
    }

    static bool bLitColorMaterialConfigured = false;
    if (Material && !bLitColorMaterialConfigured)
    {
        Material->Modify();
        int32 ConstantIndex = 0;
        for (TObjectPtr<UMaterialExpression>& Expression : Material->GetExpressionCollection().Expressions)
        {
            if (UMaterialExpressionConstant* Constant = Cast<UMaterialExpressionConstant>(Expression.Get()))
            {
                if (ConstantIndex == 0)
                {
                    Constant->R = 0.22f;
                }
                ++ConstantIndex;
            }
        }
        Material->PostEditChange();
        if (UPackage* Package = Material->GetOutermost())
        {
            Package->MarkPackageDirty();
            const FString Filename =
                FPackageName::LongPackageNameToFilename(MaterialPackagePath, FPackageName::GetAssetPackageExtension());
            FSavePackageArgs SaveArgs;
            SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
            SaveArgs.SaveFlags = SAVE_NoError;
            UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
        }
        bLitColorMaterialConfigured = true;
    }

    return Material;
}

UMaterialInterface* LoadOrCreateLandscapeCandidateMaterial(
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    FString& OutSummary)
{
    FString RiverAssetName;
    if (Candidate.PreviewSpec.RiverId == TEXT("american_south_fork"))
    {
        RiverAssetName = TEXT("AmericanSouthFork");
    }
    else if (Candidate.PreviewSpec.RiverId == TEXT("colorado_river"))
    {
        RiverAssetName = TEXT("ColoradoRiver");
    }
    else if (Candidate.PreviewSpec.RiverId == TEXT("pacuare"))
    {
        RiverAssetName = TEXT("Pacuare");
    }
    if (RiverAssetName.IsEmpty())
    {
        OutSummary += FString::Printf(
            TEXT("No Landscape material texture asset token exists for %s.\n"),
            *Candidate.PreviewSpec.RiverId);
        return nullptr;
    }

    auto LoadCandidateTexture = [&RiverAssetName](const TCHAR* AssetRoot, const TCHAR* MapSuffix)
    {
        const FString AssetName = FString::Printf(
            TEXT("T_RaftSim_%s_%s"),
            *RiverAssetName,
            MapSuffix);
        const FString ObjectPath = FString::Printf(
            TEXT("%s/%s.%s"),
            AssetRoot,
            *AssetName,
            *AssetName);
        return LoadObject<UTexture2D>(nullptr, *ObjectPath);
    };

    UTexture2D* SourceMacroAlbedo = LoadCandidateTexture(
        TEXT("/Game/RaftSim/Rendering/SourceConditionedMaterialMaps/Textures"),
        TEXT("SourceConditionedMacroAlbedo"));
    UTexture2D* SourcePackedSurface = LoadCandidateTexture(
        TEXT("/Game/RaftSim/Rendering/SourceConditionedMaterialMaps/Textures"),
        TEXT("SourceConditionedAORoughnessHeight"));
    UTexture2D* SourceNormalDetail = LoadCandidateTexture(
        TEXT("/Game/RaftSim/Rendering/SourceConditionedMaterialMaps/Textures"),
        TEXT("SourceConditionedNormalDetail"));
    UTexture2D* SourceMaterialZones = LoadCandidateTexture(
        TEXT("/Game/RaftSim/Rendering/SourceConditionedMaterialMaps/Textures"),
        TEXT("SourceConditionedMaterialZones"));
    UTexture2D* TerrainDetailAlbedo = LoadCandidateTexture(
        TEXT("/Game/RaftSim/Rendering/ProductionDetailTextures/Textures"),
        TEXT("TerrainDetailAlbedo"));
    UTexture2D* TerrainDetailPackedSurface = LoadCandidateTexture(
        TEXT("/Game/RaftSim/Rendering/ProductionDetailTextures/Textures"),
        TEXT("TerrainDetailAORoughnessHeight"));
    UTexture2D* TerrainDetailNormal = LoadCandidateTexture(
        TEXT("/Game/RaftSim/Rendering/ProductionDetailTextures/Textures"),
        TEXT("TerrainDetailNormal"));
    if (!SourceMacroAlbedo || !SourcePackedSurface || !SourceNormalDetail || !SourceMaterialZones ||
        !TerrainDetailAlbedo || !TerrainDetailPackedSurface || !TerrainDetailNormal)
    {
        OutSummary += FString::Printf(
            TEXT("Missing one or more source-conditioned/detail Texture2D assets for %s Landscape material.\n"),
            *Candidate.PreviewSpec.RiverId);
        return nullptr;
    }

    const FRaftSimLandscapeMaterialCandidateSettings Settings =
        GetLandscapeMaterialCandidateSettings(Candidate.PreviewSpec.RiverId);
    FString AssetToken = Candidate.PreviewSpec.RiverId;
    AssetToken.ReplaceInline(TEXT("_"), TEXT(""));
    const FString AssetName = FString::Printf(TEXT("M_RaftSim_%s_SourceLandscapeCandidate"), *AssetToken);
    const FString PackagePath = FString::Printf(
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/%s"),
        *AssetName);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, *AssetName);
    UPackage* Package = CreatePackage(*PackagePath);
    if (!Package)
    {
        OutSummary += FString::Printf(TEXT("Failed to create Landscape material package %s.\n"), *PackagePath);
        return nullptr;
    }

    UMaterial* Material = Cast<UMaterial>(StaticLoadObject(UMaterial::StaticClass(), nullptr, *ObjectPath));
    if (!Material)
    {
        Material = FindObject<UMaterial>(Package, *AssetName);
    }
    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package,
            *AssetName,
            RF_Public | RF_Standalone | RF_Transactional);
        if (Material)
        {
            FAssetRegistryModule::AssetCreated(Material);
        }
    }
    if (!Material)
    {
        OutSummary += FString::Printf(TEXT("Failed to create Landscape material %s.\n"), *ObjectPath);
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->SetShadingModel(MSM_DefaultLit);
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = false;
    Material->bTangentSpaceNormal = true;

    UMaterialExpressionLandscapeLayerCoords* MacroCoordinates =
        NewObject<UMaterialExpressionLandscapeLayerCoords>(Material);
    MacroCoordinates->MappingType = TCMT_XY;
    MacroCoordinates->MappingScale = Settings.MacroMappingScale;
    Material->GetExpressionCollection().AddExpression(MacroCoordinates);

    UMaterialExpressionLandscapeLayerCoords* DetailCoordinates =
        NewObject<UMaterialExpressionLandscapeLayerCoords>(Material);
    DetailCoordinates->MappingType = TCMT_XY;
    DetailCoordinates->MappingScale = Settings.DetailMappingScale;
    Material->GetExpressionCollection().AddExpression(DetailCoordinates);

    auto AddTextureSample = [Material](
                                const TCHAR* ParameterName,
                                UTexture2D* Texture,
                                EMaterialSamplerType SamplerType,
                                UMaterialExpression* Coordinates)
    {
        UMaterialExpressionTextureSampleParameter2D* Sample =
            NewObject<UMaterialExpressionTextureSampleParameter2D>(Material);
        Sample->ParameterName = ParameterName;
        Sample->Texture = Texture;
        Sample->SamplerType = SamplerType;
        Sample->Coordinates.Expression = Coordinates;
        Sample->Group = TEXT("RaftSimLandscapeCandidate");
        Material->GetExpressionCollection().AddExpression(Sample);
        return Sample;
    };

    UMaterialExpressionTextureSampleParameter2D* MacroAlbedoSample = AddTextureSample(
        TEXT("SourceConditionedMacroAlbedo"),
        SourceMacroAlbedo,
        SAMPLERTYPE_Color,
        MacroCoordinates);
    UMaterialExpressionTextureSampleParameter2D* DetailAlbedoSample = AddTextureSample(
        TEXT("TerrainDetailAlbedo"),
        TerrainDetailAlbedo,
        SAMPLERTYPE_Color,
        DetailCoordinates);
    UMaterialExpressionTextureSampleParameter2D* MacroPackedSample = AddTextureSample(
        TEXT("SourceConditionedAORoughnessHeight"),
        SourcePackedSurface,
        SAMPLERTYPE_Masks,
        MacroCoordinates);
    UMaterialExpressionTextureSampleParameter2D* DetailPackedSample = AddTextureSample(
        TEXT("TerrainDetailAORoughnessHeight"),
        TerrainDetailPackedSurface,
        SAMPLERTYPE_Masks,
        DetailCoordinates);
    UMaterialExpressionTextureSampleParameter2D* MacroNormalSample = AddTextureSample(
        TEXT("SourceConditionedNormalDetail"),
        SourceNormalDetail,
        SAMPLERTYPE_Normal,
        MacroCoordinates);
    UMaterialExpressionTextureSampleParameter2D* DetailNormalSample = AddTextureSample(
        TEXT("TerrainDetailNormal"),
        TerrainDetailNormal,
        SAMPLERTYPE_Normal,
        DetailCoordinates);
    UMaterialExpressionTextureSampleParameter2D* MaterialZonesSample = AddTextureSample(
        TEXT("SourceConditionedMaterialZones"),
        SourceMaterialZones,
        SAMPLERTYPE_Masks,
        MacroCoordinates);

    UMaterialExpressionConstant* DetailAlbedoWeight = NewObject<UMaterialExpressionConstant>(Material);
    DetailAlbedoWeight->R = Settings.DetailAlbedoWeight;
    Material->GetExpressionCollection().AddExpression(DetailAlbedoWeight);

    UMaterialExpressionLinearInterpolate* BaseColor =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    BaseColor->A.Expression = MacroAlbedoSample;
    BaseColor->B.Expression = DetailAlbedoSample;
    BaseColor->Alpha.Expression = DetailAlbedoWeight;
    Material->GetExpressionCollection().AddExpression(BaseColor);

    UMaterialExpressionComponentMask* MaterialWaterZone =
        NewObject<UMaterialExpressionComponentMask>(Material);
    MaterialWaterZone->Input.Expression = MaterialZonesSample;
    MaterialWaterZone->B = true;
    Material->GetExpressionCollection().AddExpression(MaterialWaterZone);
    UMaterialExpressionConstant* RiverbedMaskGain = NewObject<UMaterialExpressionConstant>(Material);
    RiverbedMaskGain->R = 1.15f;
    Material->GetExpressionCollection().AddExpression(RiverbedMaskGain);
    UMaterialExpressionMultiply* AmplifiedRiverbedMask = NewObject<UMaterialExpressionMultiply>(Material);
    AmplifiedRiverbedMask->A.Expression = MaterialWaterZone;
    AmplifiedRiverbedMask->B.Expression = RiverbedMaskGain;
    Material->GetExpressionCollection().AddExpression(AmplifiedRiverbedMask);
    UMaterialExpressionSaturate* RiverbedMask = NewObject<UMaterialExpressionSaturate>(Material);
    RiverbedMask->Input.Expression = AmplifiedRiverbedMask;
    Material->GetExpressionCollection().AddExpression(RiverbedMask);

    UMaterialExpressionConstant* WetBankProximityGain = NewObject<UMaterialExpressionConstant>(Material);
    WetBankProximityGain->R = 3.0f;
    Material->GetExpressionCollection().AddExpression(WetBankProximityGain);
    UMaterialExpressionMultiply* WetBankProximityRaw = NewObject<UMaterialExpressionMultiply>(Material);
    WetBankProximityRaw->A.Expression = MaterialWaterZone;
    WetBankProximityRaw->B.Expression = WetBankProximityGain;
    Material->GetExpressionCollection().AddExpression(WetBankProximityRaw);
    UMaterialExpressionSaturate* WetBankProximity = NewObject<UMaterialExpressionSaturate>(Material);
    WetBankProximity->Input.Expression = WetBankProximityRaw;
    Material->GetExpressionCollection().AddExpression(WetBankProximity);
    UMaterialExpressionOneMinus* DrySideOfWaterZone = NewObject<UMaterialExpressionOneMinus>(Material);
    DrySideOfWaterZone->Input.Expression = MaterialWaterZone;
    Material->GetExpressionCollection().AddExpression(DrySideOfWaterZone);
    UMaterialExpressionMultiply* WetBankBand = NewObject<UMaterialExpressionMultiply>(Material);
    WetBankBand->A.Expression = WetBankProximity;
    WetBankBand->B.Expression = DrySideOfWaterZone;
    Material->GetExpressionCollection().AddExpression(WetBankBand);

    UMaterialExpressionConstant* WetBankBlendWeight = NewObject<UMaterialExpressionConstant>(Material);
    WetBankBlendWeight->R = Settings.WetBankBlendWeight;
    Material->GetExpressionCollection().AddExpression(WetBankBlendWeight);
    UMaterialExpressionMultiply* WetBankBlendMask = NewObject<UMaterialExpressionMultiply>(Material);
    WetBankBlendMask->A.Expression = WetBankBand;
    WetBankBlendMask->B.Expression = WetBankBlendWeight;
    Material->GetExpressionCollection().AddExpression(WetBankBlendMask);
    UMaterialExpressionConstant3Vector* WetBankColorScale =
        NewObject<UMaterialExpressionConstant3Vector>(Material);
    WetBankColorScale->Constant = Settings.WetBankColorScale;
    Material->GetExpressionCollection().AddExpression(WetBankColorScale);
    UMaterialExpressionMultiply* WetBankColor = NewObject<UMaterialExpressionMultiply>(Material);
    WetBankColor->A.Expression = BaseColor;
    WetBankColor->B.Expression = WetBankColorScale;
    Material->GetExpressionCollection().AddExpression(WetBankColor);
    UMaterialExpressionLinearInterpolate* BaseColorWithWetBank =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    BaseColorWithWetBank->A.Expression = BaseColor;
    BaseColorWithWetBank->B.Expression = WetBankColor;
    BaseColorWithWetBank->Alpha.Expression = WetBankBlendMask;
    Material->GetExpressionCollection().AddExpression(BaseColorWithWetBank);

    UMaterialExpressionConstant* RiverbedBlendWeight = NewObject<UMaterialExpressionConstant>(Material);
    RiverbedBlendWeight->R = Settings.RiverbedBlendWeight;
    Material->GetExpressionCollection().AddExpression(RiverbedBlendWeight);
    UMaterialExpressionMultiply* RiverbedBlendMask = NewObject<UMaterialExpressionMultiply>(Material);
    RiverbedBlendMask->A.Expression = RiverbedMask;
    RiverbedBlendMask->B.Expression = RiverbedBlendWeight;
    Material->GetExpressionCollection().AddExpression(RiverbedBlendMask);
    UMaterialExpressionConstant3Vector* RiverbedColorScale =
        NewObject<UMaterialExpressionConstant3Vector>(Material);
    RiverbedColorScale->Constant = Settings.RiverbedColorScale;
    Material->GetExpressionCollection().AddExpression(RiverbedColorScale);
    UMaterialExpressionMultiply* RiverbedColor = NewObject<UMaterialExpressionMultiply>(Material);
    RiverbedColor->A.Expression = BaseColor;
    RiverbedColor->B.Expression = RiverbedColorScale;
    Material->GetExpressionCollection().AddExpression(RiverbedColor);
    UMaterialExpressionLinearInterpolate* ConditionedBaseColor =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    ConditionedBaseColor->A.Expression = BaseColorWithWetBank;
    ConditionedBaseColor->B.Expression = RiverbedColor;
    ConditionedBaseColor->Alpha.Expression = RiverbedBlendMask;
    Material->GetExpressionCollection().AddExpression(ConditionedBaseColor);

    UMaterialExpressionConstant* DetailNormalWeight = NewObject<UMaterialExpressionConstant>(Material);
    DetailNormalWeight->R = Settings.DetailNormalWeight;
    Material->GetExpressionCollection().AddExpression(DetailNormalWeight);

    UMaterialExpressionLinearInterpolate* Normal =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    Normal->A.Expression = MacroNormalSample;
    Normal->B.Expression = DetailNormalSample;
    Normal->Alpha.Expression = DetailNormalWeight;
    Material->GetExpressionCollection().AddExpression(Normal);

    auto AddChannelMask = [Material](UMaterialExpression* Input, bool bRed, bool bGreen)
    {
        UMaterialExpressionComponentMask* Mask = NewObject<UMaterialExpressionComponentMask>(Material);
        Mask->Input.Expression = Input;
        Mask->R = bRed;
        Mask->G = bGreen;
        Material->GetExpressionCollection().AddExpression(Mask);
        return Mask;
    };
    UMaterialExpressionComponentMask* MacroAo = AddChannelMask(MacroPackedSample, true, false);
    UMaterialExpressionComponentMask* DetailAo = AddChannelMask(DetailPackedSample, true, false);
    UMaterialExpressionComponentMask* MacroRoughness = AddChannelMask(MacroPackedSample, false, true);
    UMaterialExpressionComponentMask* DetailRoughness = AddChannelMask(DetailPackedSample, false, true);

    UMaterialExpressionConstant* DetailSurfaceResponseWeight =
        NewObject<UMaterialExpressionConstant>(Material);
    DetailSurfaceResponseWeight->R = Settings.DetailSurfaceResponseWeight;
    Material->GetExpressionCollection().AddExpression(DetailSurfaceResponseWeight);

    UMaterialExpressionLinearInterpolate* AmbientOcclusion =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    AmbientOcclusion->A.Expression = MacroAo;
    AmbientOcclusion->B.Expression = DetailAo;
    AmbientOcclusion->Alpha.Expression = DetailSurfaceResponseWeight;
    Material->GetExpressionCollection().AddExpression(AmbientOcclusion);

    UMaterialExpressionLinearInterpolate* Roughness =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    Roughness->A.Expression = MacroRoughness;
    Roughness->B.Expression = DetailRoughness;
    Roughness->Alpha.Expression = DetailSurfaceResponseWeight;
    Material->GetExpressionCollection().AddExpression(Roughness);

    UMaterialExpressionConstant* RiverbedRoughness = NewObject<UMaterialExpressionConstant>(Material);
    RiverbedRoughness->R = Settings.RiverbedRoughness;
    Material->GetExpressionCollection().AddExpression(RiverbedRoughness);
    UMaterialExpressionLinearInterpolate* ConditionedRoughness =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    ConditionedRoughness->A.Expression = Roughness;
    ConditionedRoughness->B.Expression = RiverbedRoughness;
    ConditionedRoughness->Alpha.Expression = RiverbedBlendMask;
    Material->GetExpressionCollection().AddExpression(ConditionedRoughness);

    UMaterialExpressionConstant* EmissiveScale = NewObject<UMaterialExpressionConstant>(Material);
    EmissiveScale->R = Settings.EmissiveFillScale;
    Material->GetExpressionCollection().AddExpression(EmissiveScale);

    UMaterialExpressionMultiply* EmissiveColor = NewObject<UMaterialExpressionMultiply>(Material);
    EmissiveColor->A.Expression = ConditionedBaseColor;
    EmissiveColor->B.Expression = EmissiveScale;
    Material->GetExpressionCollection().AddExpression(EmissiveColor);

    UMaterialExpressionConstant* Specular = NewObject<UMaterialExpressionConstant>(Material);
    Specular->R = Settings.SpecularLevel;
    Material->GetExpressionCollection().AddExpression(Specular);

    UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, ConditionedBaseColor);
    ConnectPreviewMaterialColorInput(EditorOnlyData->EmissiveColor, EmissiveColor);
    ConnectPreviewMaterialVectorInput(EditorOnlyData->Normal, Normal);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->AmbientOcclusion, AmbientOcclusion);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, ConditionedRoughness);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);

    Material->SetMaterialUsage(MATUSAGE_Nanite);
    Material->SetMaterialUsage(MATUSAGE_StaticLighting);
    Material->PostEditChange();
    Package->MarkPackageDirty();

    const FString Filename =
        FPackageName::LongPackageNameToFilename(PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
    {
        OutSummary += FString::Printf(TEXT("Failed to save Landscape material %s.\n"), *Filename);
        return nullptr;
    }
    FAssetCompilingManager::Get().FinishAllCompilation();

    OutSummary += FString::Printf(
        TEXT("Built %s Landscape material from source-conditioned macro/zones maps plus first-party terrain detail (macro scale %.2f, detail scale %.2f, albedo %.2f, normal %.2f, surface %.2f, riverbed %.2f, wet bank %.2f).\n"),
        *Candidate.PreviewSpec.RiverId,
        Settings.MacroMappingScale,
        Settings.DetailMappingScale,
        Settings.DetailAlbedoWeight,
        Settings.DetailNormalWeight,
        Settings.DetailSurfaceResponseWeight,
        Settings.RiverbedBlendWeight,
        Settings.WetBankBlendWeight);

    return Material;
}

UMaterialInterface* LoadOrCreatePreviewVertexColorMaterial()
{
    static const TCHAR* MaterialPackagePath = TEXT("/Game/RaftSim/Materials/M_RaftSim_VertexColorPreview");
    static const TCHAR* MaterialObjectPath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_VertexColorPreview.M_RaftSim_VertexColorPreview");

    UMaterial* Material = Cast<UMaterial>(StaticLoadObject(UMaterial::StaticClass(), nullptr, MaterialObjectPath));
    if (!Material)
    {
        UPackage* Package = CreatePackage(MaterialPackagePath);
        if (!Package)
        {
            return nullptr;
        }

        Material = NewObject<UMaterial>(
            Package,
            TEXT("M_RaftSim_VertexColorPreview"),
            RF_Public | RF_Standalone | RF_Transactional);
        if (!Material)
        {
            return nullptr;
        }

        FAssetRegistryModule::AssetCreated(Material);
        Material->Modify();
        Material->SetShadingModel(MSM_DefaultLit);
        Material->BlendMode = BLEND_Opaque;
        Material->TwoSided = true;

        UMaterialExpressionVertexColor* VertexColor = NewObject<UMaterialExpressionVertexColor>(Material);
        Material->GetExpressionCollection().AddExpression(VertexColor);

        UMaterialExpressionConstant* EmissiveScale = NewObject<UMaterialExpressionConstant>(Material);
        EmissiveScale->R = 0.10f;
        Material->GetExpressionCollection().AddExpression(EmissiveScale);

        UMaterialExpressionMultiply* EmissiveColor = NewObject<UMaterialExpressionMultiply>(Material);
        EmissiveColor->A.Expression = VertexColor;
        EmissiveColor->B.Expression = EmissiveScale;
        Material->GetExpressionCollection().AddExpression(EmissiveColor);

        UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
        ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, VertexColor);
        ConnectPreviewMaterialColorInput(EditorOnlyData->EmissiveColor, EmissiveColor);

        Material->PostEditChange();
        Package->MarkPackageDirty();

        const FString Filename =
            FPackageName::LongPackageNameToFilename(MaterialPackagePath, FPackageName::GetAssetPackageExtension());
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);

        FSavePackageArgs SaveArgs;
        SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
        SaveArgs.SaveFlags = SAVE_NoError;
        UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
    }

    static bool bVertexColorMaterialConfigured = false;
    if (Material && !bVertexColorMaterialConfigured)
    {
        Material->Modify();
        int32 ConstantIndex = 0;
        for (TObjectPtr<UMaterialExpression>& Expression : Material->GetExpressionCollection().Expressions)
        {
            if (UMaterialExpressionConstant* Constant = Cast<UMaterialExpressionConstant>(Expression.Get()))
            {
                if (ConstantIndex == 0)
                {
                    Constant->R = 0.10f;
                }
                ++ConstantIndex;
            }
        }
        Material->PostEditChange();
        if (UPackage* Package = Material->GetOutermost())
        {
            Package->MarkPackageDirty();
            const FString Filename =
                FPackageName::LongPackageNameToFilename(MaterialPackagePath, FPackageName::GetAssetPackageExtension());
            FSavePackageArgs SaveArgs;
            SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
            SaveArgs.SaveFlags = SAVE_NoError;
            UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
        }
        bVertexColorMaterialConfigured = true;
    }

    return Material;
}

UMaterialInterface* LoadOrCreatePreviewTerrainVertexColorMaterial()
{
    static const TCHAR* MaterialPackagePath = TEXT("/Game/RaftSim/Materials/M_RaftSim_TerrainVertexColorLitPreview");
    static const TCHAR* MaterialObjectPath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_TerrainVertexColorLitPreview.M_RaftSim_TerrainVertexColorLitPreview");

    UMaterial* Material = Cast<UMaterial>(StaticLoadObject(UMaterial::StaticClass(), nullptr, MaterialObjectPath));
    if (!Material)
    {
        UPackage* Package = CreatePackage(MaterialPackagePath);
        if (!Package)
        {
            return nullptr;
        }

        Material = NewObject<UMaterial>(
            Package,
            TEXT("M_RaftSim_TerrainVertexColorLitPreview"),
            RF_Public | RF_Standalone | RF_Transactional);
        if (!Material)
        {
            return nullptr;
        }

        FAssetRegistryModule::AssetCreated(Material);
        Material->Modify();
        Material->SetShadingModel(MSM_DefaultLit);
        Material->BlendMode = BLEND_Opaque;
        Material->TwoSided = true;

        UMaterialExpressionVertexColor* VertexColor = NewObject<UMaterialExpressionVertexColor>(Material);
        Material->GetExpressionCollection().AddExpression(VertexColor);

        UMaterialExpressionConstant* Roughness = NewObject<UMaterialExpressionConstant>(Material);
        Roughness->R = 0.86f;
        Material->GetExpressionCollection().AddExpression(Roughness);

        UMaterialExpressionConstant* Specular = NewObject<UMaterialExpressionConstant>(Material);
        Specular->R = 0.16f;
        Material->GetExpressionCollection().AddExpression(Specular);

        UMaterialExpressionConstant* EmissiveScale = NewObject<UMaterialExpressionConstant>(Material);
        EmissiveScale->R = 0.22f;
        Material->GetExpressionCollection().AddExpression(EmissiveScale);

        UMaterialExpressionMultiply* EmissiveColor = NewObject<UMaterialExpressionMultiply>(Material);
        EmissiveColor->A.Expression = VertexColor;
        EmissiveColor->B.Expression = EmissiveScale;
        Material->GetExpressionCollection().AddExpression(EmissiveColor);

        UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
        ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, VertexColor);
        ConnectPreviewMaterialColorInput(EditorOnlyData->EmissiveColor, EmissiveColor);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, Roughness);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);

        Material->PostEditChange();
        Package->MarkPackageDirty();

        const FString Filename =
            FPackageName::LongPackageNameToFilename(MaterialPackagePath, FPackageName::GetAssetPackageExtension());
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);

        FSavePackageArgs SaveArgs;
        SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
        SaveArgs.SaveFlags = SAVE_NoError;
        UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
    }

    static bool bTerrainMaterialConfigured = false;
    if (Material && !bTerrainMaterialConfigured)
    {
        Material->Modify();
        Material->SetShadingModel(MSM_DefaultLit);
        Material->BlendMode = BLEND_Opaque;
        Material->TwoSided = true;
        int32 TerrainConstantIndex = 0;
        for (TObjectPtr<UMaterialExpression>& Expression : Material->GetExpressionCollection().Expressions)
        {
            if (UMaterialExpressionConstant* Constant = Cast<UMaterialExpressionConstant>(Expression.Get()))
            {
                if (TerrainConstantIndex == 0)
                {
                    Constant->R = 0.92f;
                }
                else if (TerrainConstantIndex == 1)
                {
                    Constant->R = 0.08f;
                }
                else
                {
                    Constant->R = 0.22f;
                }
                ++TerrainConstantIndex;
            }
        }
        Material->PostEditChange();
        UPackage* Package = Material->GetOutermost();
        if (Package)
        {
            Package->MarkPackageDirty();
            const FString Filename =
                FPackageName::LongPackageNameToFilename(MaterialPackagePath, FPackageName::GetAssetPackageExtension());
            FSavePackageArgs SaveArgs;
            SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
            SaveArgs.SaveFlags = SAVE_NoError;
            UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
        }
        bTerrainMaterialConfigured = true;
    }

    return Material;
}

UMaterialInterface* LoadOrCreatePreviewTranslucentColorMaterial()
{
    static const TCHAR* MaterialPackagePath = TEXT("/Game/RaftSim/Materials/M_RaftSim_TranslucentColorPreview");
    static const TCHAR* MaterialObjectPath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_TranslucentColorPreview.M_RaftSim_TranslucentColorPreview");

    UMaterial* Material = Cast<UMaterial>(StaticLoadObject(UMaterial::StaticClass(), nullptr, MaterialObjectPath));
    if (!Material)
    {
        UPackage* Package = CreatePackage(MaterialPackagePath);
        if (!Package)
        {
            return nullptr;
        }

        Material = NewObject<UMaterial>(
            Package,
            TEXT("M_RaftSim_TranslucentColorPreview"),
            RF_Public | RF_Standalone | RF_Transactional);
        if (!Material)
        {
            return nullptr;
        }

        FAssetRegistryModule::AssetCreated(Material);
        Material->Modify();
        Material->SetShadingModel(MSM_DefaultLit);
        Material->BlendMode = BLEND_Translucent;
        Material->TwoSided = true;

        UMaterialExpressionVectorParameter* ColorParameter = NewObject<UMaterialExpressionVectorParameter>(Material);
        ColorParameter->ParameterName = TEXT("PreviewColor");
        ColorParameter->DefaultValue = FLinearColor(0.78f, 0.92f, 0.94f, 1.0f);
        Material->GetExpressionCollection().AddExpression(ColorParameter);

        UMaterialExpressionScalarParameter* OpacityParameter = NewObject<UMaterialExpressionScalarParameter>(Material);
        OpacityParameter->ParameterName = TEXT("PreviewOpacity");
        OpacityParameter->DefaultValue = 0.28f;
        Material->GetExpressionCollection().AddExpression(OpacityParameter);

        UMaterialExpressionConstant* EmissiveScale = NewObject<UMaterialExpressionConstant>(Material);
        EmissiveScale->R = 0.85f;
        Material->GetExpressionCollection().AddExpression(EmissiveScale);

        UMaterialExpressionMultiply* EmissiveColor = NewObject<UMaterialExpressionMultiply>(Material);
        EmissiveColor->A.Expression = ColorParameter;
        EmissiveColor->B.Expression = EmissiveScale;
        Material->GetExpressionCollection().AddExpression(EmissiveColor);

        UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
        ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, ColorParameter);
        ConnectPreviewMaterialColorInput(EditorOnlyData->EmissiveColor, EmissiveColor);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Opacity, OpacityParameter);

        Material->PostEditChange();
        Package->MarkPackageDirty();

        const FString Filename =
            FPackageName::LongPackageNameToFilename(MaterialPackagePath, FPackageName::GetAssetPackageExtension());
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);

        FSavePackageArgs SaveArgs;
        SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
        SaveArgs.SaveFlags = SAVE_NoError;
        UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
    }

    return Material;
}

UMaterialInterface* LoadOrCreatePreviewWaterVertexColorMaterial()
{
    static const TCHAR* MaterialPackagePath = TEXT("/Game/RaftSim/Materials/M_RaftSim_VertexColorWaterPreview");
    static const TCHAR* MaterialObjectPath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_VertexColorWaterPreview.M_RaftSim_VertexColorWaterPreview");
    const float FirstPartyLitWaterNormalResponseEmissiveFill = 0.38f;
    const float FirstPartyLitWaterNormalResponseRoughness = 0.96f;
    const float FirstPartyLitWaterNormalResponseSpecular = 0.0f;

    UMaterial* Material = Cast<UMaterial>(StaticLoadObject(UMaterial::StaticClass(), nullptr, MaterialObjectPath));
    if (!Material)
    {
        UPackage* Package = CreatePackage(MaterialPackagePath);
        if (!Package)
        {
            return nullptr;
        }

        Material = NewObject<UMaterial>(
            Package,
            TEXT("M_RaftSim_VertexColorWaterPreview"),
            RF_Public | RF_Standalone | RF_Transactional);
        if (!Material)
        {
            return nullptr;
        }

        FAssetRegistryModule::AssetCreated(Material);
        Material->Modify();
        Material->SetShadingModel(MSM_DefaultLit);
        Material->BlendMode = BLEND_Opaque;
        Material->TwoSided = true;

        UMaterialExpressionVertexColor* VertexColor = NewObject<UMaterialExpressionVertexColor>(Material);
        Material->GetExpressionCollection().AddExpression(VertexColor);

        UMaterialExpressionConstant* EmissiveScale = NewObject<UMaterialExpressionConstant>(Material);
        EmissiveScale->R = FirstPartyLitWaterNormalResponseEmissiveFill;
        Material->GetExpressionCollection().AddExpression(EmissiveScale);

        UMaterialExpressionConstant* Roughness = NewObject<UMaterialExpressionConstant>(Material);
        Roughness->R = FirstPartyLitWaterNormalResponseRoughness;
        Material->GetExpressionCollection().AddExpression(Roughness);

        UMaterialExpressionConstant* Specular = NewObject<UMaterialExpressionConstant>(Material);
        Specular->R = FirstPartyLitWaterNormalResponseSpecular;
        Material->GetExpressionCollection().AddExpression(Specular);

        UMaterialExpressionMultiply* EmissiveColor = NewObject<UMaterialExpressionMultiply>(Material);
        EmissiveColor->A.Expression = VertexColor;
        EmissiveColor->B.Expression = EmissiveScale;
        Material->GetExpressionCollection().AddExpression(EmissiveColor);

        UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
        ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, VertexColor);
        ConnectPreviewMaterialColorInput(EditorOnlyData->EmissiveColor, EmissiveColor);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, Roughness);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);

        Material->PostEditChange();
        Package->MarkPackageDirty();

        const FString Filename =
            FPackageName::LongPackageNameToFilename(MaterialPackagePath, FPackageName::GetAssetPackageExtension());
        IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);

        FSavePackageArgs SaveArgs;
        SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
        SaveArgs.SaveFlags = SAVE_NoError;
        UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
    }

    static bool bWaterMaterialConfigured = false;
    if (Material && !bWaterMaterialConfigured)
    {
        Material->Modify();
        Material->GetExpressionCollection().Empty();
        Material->SetShadingModel(MSM_DefaultLit);
        Material->BlendMode = BLEND_Opaque;
        Material->TwoSided = true;

        UMaterialExpressionVertexColor* VertexColor = NewObject<UMaterialExpressionVertexColor>(Material);
        Material->GetExpressionCollection().AddExpression(VertexColor);

        UMaterialExpressionTextureCoordinate* TexCoord = NewObject<UMaterialExpressionTextureCoordinate>(Material);
        Material->GetExpressionCollection().AddExpression(TexCoord);

        UMaterialExpressionFrac* WrappedUv = NewObject<UMaterialExpressionFrac>(Material);
        WrappedUv->Input.Expression = TexCoord;
        Material->GetExpressionCollection().AddExpression(WrappedUv);

        UMaterialExpressionVectorParameter* AtlasTileOriginParameter =
            NewObject<UMaterialExpressionVectorParameter>(Material);
        AtlasTileOriginParameter->ParameterName = TEXT("AtlasTileOrigin");
        AtlasTileOriginParameter->DefaultValue = FLinearColor(0.0f, 0.5f, 0.0f, 0.0f);
        AtlasTileOriginParameter->Group = TEXT("RaftSimWaterReview");
        Material->GetExpressionCollection().AddExpression(AtlasTileOriginParameter);

        UMaterialExpressionVectorParameter* AtlasTileScaleParameter =
            NewObject<UMaterialExpressionVectorParameter>(Material);
        AtlasTileScaleParameter->ParameterName = TEXT("AtlasTileScale");
        AtlasTileScaleParameter->DefaultValue = FLinearColor(1.0f / 3.0f, 1.0f / 2.0f, 0.0f, 0.0f);
        AtlasTileScaleParameter->Group = TEXT("RaftSimWaterReview");
        Material->GetExpressionCollection().AddExpression(AtlasTileScaleParameter);

        UMaterialExpressionComponentMask* AtlasTileOrigin = NewObject<UMaterialExpressionComponentMask>(Material);
        AtlasTileOrigin->Input.Expression = AtlasTileOriginParameter;
        AtlasTileOrigin->R = 1;
        AtlasTileOrigin->G = 1;
        Material->GetExpressionCollection().AddExpression(AtlasTileOrigin);

        UMaterialExpressionComponentMask* AtlasTileScale = NewObject<UMaterialExpressionComponentMask>(Material);
        AtlasTileScale->Input.Expression = AtlasTileScaleParameter;
        AtlasTileScale->R = 1;
        AtlasTileScale->G = 1;
        Material->GetExpressionCollection().AddExpression(AtlasTileScale);

        UMaterialExpressionMultiply* AtlasScaledUv = NewObject<UMaterialExpressionMultiply>(Material);
        AtlasScaledUv->A.Expression = WrappedUv;
        AtlasScaledUv->B.Expression = AtlasTileScale;
        Material->GetExpressionCollection().AddExpression(AtlasScaledUv);

        UMaterialExpressionAdd* AtlasUv = NewObject<UMaterialExpressionAdd>(Material);
        AtlasUv->A.Expression = AtlasScaledUv;
        AtlasUv->B.Expression = AtlasTileOrigin;
        Material->GetExpressionCollection().AddExpression(AtlasUv);

        UMaterialExpressionTextureSampleParameter2D* NormalSample =
            NewObject<UMaterialExpressionTextureSampleParameter2D>(Material);
        NormalSample->ParameterName = TEXT("NormalAtlas");
        NormalSample->Texture = LoadObject<UTexture2D>(nullptr, TEXT("/Engine/EngineMaterials/DefaultNormal.DefaultNormal"));
        NormalSample->SamplerType = SAMPLERTYPE_Normal;
        NormalSample->Coordinates.Expression = AtlasUv;
        NormalSample->Group = TEXT("RaftSimWaterReview");
        Material->GetExpressionCollection().AddExpression(NormalSample);

        UMaterialExpressionConstant3Vector* FlatNormal = NewObject<UMaterialExpressionConstant3Vector>(Material);
        FlatNormal->Constant = FLinearColor(0.0f, 0.0f, 1.0f);
        Material->GetExpressionCollection().AddExpression(FlatNormal);

        UMaterialExpressionScalarParameter* NormalIntensity =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        NormalIntensity->ParameterName = TEXT("NormalIntensity");
        NormalIntensity->DefaultValue = 0.32f;
        NormalIntensity->Group = TEXT("RaftSimWaterReview");
        Material->GetExpressionCollection().AddExpression(NormalIntensity);

        UMaterialExpressionLinearInterpolate* WaterNormal =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        WaterNormal->A.Expression = FlatNormal;
        WaterNormal->B.Expression = NormalSample;
        WaterNormal->Alpha.Expression = NormalIntensity;
        Material->GetExpressionCollection().AddExpression(WaterNormal);

        UMaterialExpressionScalarParameter* EmissiveFillScale =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        EmissiveFillScale->ParameterName = TEXT("EmissiveFillScale");
        EmissiveFillScale->DefaultValue = 0.26f;
        EmissiveFillScale->Group = TEXT("RaftSimWaterReview");
        Material->GetExpressionCollection().AddExpression(EmissiveFillScale);

        UMaterialExpressionScalarParameter* RoughnessScale =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        RoughnessScale->ParameterName = TEXT("RoughnessScale");
        RoughnessScale->DefaultValue = 0.18f;
        RoughnessScale->Group = TEXT("RaftSimWaterReview");
        Material->GetExpressionCollection().AddExpression(RoughnessScale);

        UMaterialExpressionScalarParameter* RoughnessFloor =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        RoughnessFloor->ParameterName = TEXT("RoughnessFloor");
        RoughnessFloor->DefaultValue = 0.28f;
        RoughnessFloor->Group = TEXT("RaftSimWaterReview");
        Material->GetExpressionCollection().AddExpression(RoughnessFloor);

        UMaterialExpressionAdd* Roughness = NewObject<UMaterialExpressionAdd>(Material);
        Roughness->A.Expression = RoughnessScale;
        Roughness->B.Expression = RoughnessFloor;
        Material->GetExpressionCollection().AddExpression(Roughness);

        UMaterialExpressionScalarParameter* SpecularLevel =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        SpecularLevel->ParameterName = TEXT("SpecularLevel");
        SpecularLevel->DefaultValue = 0.22f;
        SpecularLevel->Group = TEXT("RaftSimWaterReview");
        Material->GetExpressionCollection().AddExpression(SpecularLevel);

        UMaterialExpressionMultiply* EmissiveColor = NewObject<UMaterialExpressionMultiply>(Material);
        EmissiveColor->A.Expression = VertexColor;
        EmissiveColor->B.Expression = EmissiveFillScale;
        Material->GetExpressionCollection().AddExpression(EmissiveColor);

        if (UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData())
        {
            ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, VertexColor);
            ConnectPreviewMaterialColorInput(EditorOnlyData->EmissiveColor, EmissiveColor);
            ConnectPreviewMaterialVectorInput(EditorOnlyData->Normal, WaterNormal);
            ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, Roughness);
            ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, SpecularLevel);
        }
        Material->PostEditChange();
        UPackage* Package = Material->GetOutermost();
        if (Package)
        {
            Package->MarkPackageDirty();
            const FString Filename =
                FPackageName::LongPackageNameToFilename(MaterialPackagePath, FPackageName::GetAssetPackageExtension());
            FSavePackageArgs SaveArgs;
            SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
            SaveArgs.SaveFlags = SAVE_NoError;
            UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
        }
        bWaterMaterialConfigured = true;
    }

    return Material;
}

UMaterial* LoadOrCreateLandscapeCandidateSolverSurfaceWaterParent(FString& OutSummary)
{
    static const TCHAR* MaterialPackagePath =
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/M_RaftSim_SolverSurfaceWaterCandidate");
    static const TCHAR* MaterialObjectPath =
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/M_RaftSim_SolverSurfaceWaterCandidate.M_RaftSim_SolverSurfaceWaterCandidate");

    UPackage* Package = CreatePackage(MaterialPackagePath);
    if (!Package)
    {
        OutSummary += TEXT("Failed to create the solver-surface water candidate material package.\n");
        return nullptr;
    }

    UMaterial* Material = Cast<UMaterial>(StaticLoadObject(UMaterial::StaticClass(), nullptr, MaterialObjectPath));
    if (!Material)
    {
        Material = FindObject<UMaterial>(Package, TEXT("M_RaftSim_SolverSurfaceWaterCandidate"));
    }
    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package,
            TEXT("M_RaftSim_SolverSurfaceWaterCandidate"),
            RF_Public | RF_Standalone | RF_Transactional);
        if (Material)
        {
            FAssetRegistryModule::AssetCreated(Material);
        }
    }
    if (!Material)
    {
        OutSummary += TEXT("Failed to create the solver-surface water candidate material.\n");
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->SetShadingModel(MSM_DefaultLit);
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = true;
    Material->bTangentSpaceNormal = true;
    Material->RefractionMethod = RM_IndexOfRefraction;

    auto AddScalarParameter = [Material](const TCHAR* Name, float DefaultValue)
    {
        UMaterialExpressionScalarParameter* Parameter =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        Parameter->ParameterName = Name;
        Parameter->DefaultValue = DefaultValue;
        Parameter->Group = TEXT("RaftSimSingleLayerWater");
        Material->GetExpressionCollection().AddExpression(Parameter);
        return Parameter;
    };
    auto AddVectorParameter = [Material](const TCHAR* Name, const FLinearColor& DefaultValue)
    {
        UMaterialExpressionVectorParameter* Parameter =
            NewObject<UMaterialExpressionVectorParameter>(Material);
        Parameter->ParameterName = Name;
        Parameter->DefaultValue = DefaultValue;
        Parameter->Group = TEXT("RaftSimSingleLayerWater");
        Material->GetExpressionCollection().AddExpression(Parameter);
        return Parameter;
    };

    UMaterialExpressionVertexColor* VertexColor = NewObject<UMaterialExpressionVertexColor>(Material);
    Material->GetExpressionCollection().AddExpression(VertexColor);
    UMaterialExpressionVectorParameter* SurfaceTint =
        AddVectorParameter(TEXT("SurfaceTint"), FLinearColor(0.025f, 0.115f, 0.095f, 0.0f));
    UMaterialExpressionScalarParameter* VertexTintWeight =
        AddScalarParameter(TEXT("VertexTintWeight"), 0.12f);
    UMaterialExpressionLinearInterpolate* PhysicalSurfaceTint =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    PhysicalSurfaceTint->A.Expression = SurfaceTint;
    PhysicalSurfaceTint->B.Expression = VertexColor;
    PhysicalSurfaceTint->Alpha.Expression = VertexTintWeight;
    Material->GetExpressionCollection().AddExpression(PhysicalSurfaceTint);

    UTexture2D* DefaultNormalTexture = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Engine/EngineMaterials/DefaultNormal.DefaultNormal"));
    UTexture2D* DefaultFieldTexture = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Rendering/SolverVisualizationFields/Textures/"
             "T_RaftSim_AmericanSouthFork_CppSolverDepthSpeedFroude."
             "T_RaftSim_AmericanSouthFork_CppSolverDepthSpeedFroude"));
    if (!DefaultNormalTexture || !DefaultFieldTexture)
    {
        OutSummary += TEXT("Failed to load default textures for Single Layer Water.\n");
        return nullptr;
    }

    // The candidate mesh stores longitudinal UV as U*18 for tiled micro-normal sampling.
    // Divide that coordinate back to [0,1] for the single whole-window solver field.
    UMaterialExpressionTextureCoordinate* SolverFieldUv =
        NewObject<UMaterialExpressionTextureCoordinate>(Material);
    SolverFieldUv->UTiling = 1.0f / 18.0f;
    SolverFieldUv->VTiling = 1.0f;
    Material->GetExpressionCollection().AddExpression(SolverFieldUv);
    UMaterialExpressionTextureSampleParameter2D* SolverFieldSample =
        NewObject<UMaterialExpressionTextureSampleParameter2D>(Material);
    SolverFieldSample->ParameterName = TEXT("SolverVisualizationFields");
    SolverFieldSample->Texture = DefaultFieldTexture;
    SolverFieldSample->SamplerType = SAMPLERTYPE_Masks;
    SolverFieldSample->Coordinates.Expression = SolverFieldUv;
    SolverFieldSample->Group = TEXT("RaftSimSolverVisualization");
    Material->GetExpressionCollection().AddExpression(SolverFieldSample);
    UMaterialExpressionTextureSampleParameter2D* SolverNormalSample =
        NewObject<UMaterialExpressionTextureSampleParameter2D>(Material);
    SolverNormalSample->ParameterName = TEXT("SolverVisualizationNormal");
    SolverNormalSample->Texture = DefaultNormalTexture;
    SolverNormalSample->SamplerType = SAMPLERTYPE_Normal;
    SolverNormalSample->Coordinates.Expression = SolverFieldUv;
    SolverNormalSample->Group = TEXT("RaftSimSolverVisualization");
    Material->GetExpressionCollection().AddExpression(SolverNormalSample);

    auto AddSolverFieldMask = [Material, SolverFieldSample](bool bR, bool bG, bool bB)
    {
        UMaterialExpressionComponentMask* Mask = NewObject<UMaterialExpressionComponentMask>(Material);
        Mask->Input.Expression = SolverFieldSample;
        Mask->R = bR;
        Mask->G = bG;
        Mask->B = bB;
        Material->GetExpressionCollection().AddExpression(Mask);
        return Mask;
    };
    UMaterialExpressionComponentMask* SolverDepth = AddSolverFieldMask(true, false, false);
    UMaterialExpressionComponentMask* SolverSpeed = AddSolverFieldMask(false, true, false);
    UMaterialExpressionComponentMask* SolverFroude = AddSolverFieldMask(false, false, true);
    UMaterialExpressionScalarParameter* SolverSpeedVisualGain =
        AddScalarParameter(TEXT("SolverSpeedVisualGain"), 0.0f);
    UMaterialExpressionMultiply* SolverSpeedGained = NewObject<UMaterialExpressionMultiply>(Material);
    SolverSpeedGained->A.Expression = SolverSpeed;
    SolverSpeedGained->B.Expression = SolverSpeedVisualGain;
    Material->GetExpressionCollection().AddExpression(SolverSpeedGained);
    UMaterialExpressionSaturate* SolverSpeedVisual = NewObject<UMaterialExpressionSaturate>(Material);
    SolverSpeedVisual->Input.Expression = SolverSpeedGained;
    Material->GetExpressionCollection().AddExpression(SolverSpeedVisual);
    UMaterialExpressionScalarParameter* SolverFroudeVisualGain =
        AddScalarParameter(TEXT("SolverFroudeVisualGain"), 0.0f);
    UMaterialExpressionMultiply* SolverFroudeGained = NewObject<UMaterialExpressionMultiply>(Material);
    SolverFroudeGained->A.Expression = SolverFroude;
    SolverFroudeGained->B.Expression = SolverFroudeVisualGain;
    Material->GetExpressionCollection().AddExpression(SolverFroudeGained);
    UMaterialExpressionSaturate* SolverFroudeVisual = NewObject<UMaterialExpressionSaturate>(Material);
    SolverFroudeVisual->Input.Expression = SolverFroudeGained;
    Material->GetExpressionCollection().AddExpression(SolverFroudeVisual);
    UMaterialExpressionScalarParameter* SolverFieldEnable =
        AddScalarParameter(TEXT("SolverFieldEnable"), 0.0f);
    UMaterialExpressionScalarParameter* SolverDepthColorWeight =
        AddScalarParameter(TEXT("SolverDepthColorWeight"), 0.0f);
    UMaterialExpressionMultiply* SolverDepthEnabled = NewObject<UMaterialExpressionMultiply>(Material);
    SolverDepthEnabled->A.Expression = SolverDepth;
    SolverDepthEnabled->B.Expression = SolverFieldEnable;
    Material->GetExpressionCollection().AddExpression(SolverDepthEnabled);
    UMaterialExpressionMultiply* SolverDepthColorAlpha = NewObject<UMaterialExpressionMultiply>(Material);
    SolverDepthColorAlpha->A.Expression = SolverDepthEnabled;
    SolverDepthColorAlpha->B.Expression = SolverDepthColorWeight;
    Material->GetExpressionCollection().AddExpression(SolverDepthColorAlpha);
    UMaterialExpressionVectorParameter* SolverDeepWaterTint = AddVectorParameter(
        TEXT("SolverDeepWaterTint"),
        FLinearColor(0.012f, 0.072f, 0.060f, 0.0f));
    UMaterialExpressionLinearInterpolate* SolverDepthTintedSurface =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    SolverDepthTintedSurface->A.Expression = PhysicalSurfaceTint;
    SolverDepthTintedSurface->B.Expression = SolverDeepWaterTint;
    SolverDepthTintedSurface->Alpha.Expression = SolverDepthColorAlpha;
    Material->GetExpressionCollection().AddExpression(SolverDepthTintedSurface);
    UMaterialExpressionScalarParameter* SolverFroudeAerationWeight =
        AddScalarParameter(TEXT("SolverFroudeAerationWeight"), 0.0f);
    UMaterialExpressionMultiply* SolverFroudeEnabled = NewObject<UMaterialExpressionMultiply>(Material);
    SolverFroudeEnabled->A.Expression = SolverFroudeVisual;
    SolverFroudeEnabled->B.Expression = SolverFieldEnable;
    Material->GetExpressionCollection().AddExpression(SolverFroudeEnabled);
    UMaterialExpressionMultiply* SolverAerationAlpha = NewObject<UMaterialExpressionMultiply>(Material);
    SolverAerationAlpha->A.Expression = SolverFroudeEnabled;
    SolverAerationAlpha->B.Expression = SolverFroudeAerationWeight;
    Material->GetExpressionCollection().AddExpression(SolverAerationAlpha);
    UMaterialExpressionVectorParameter* SolverAerationTint = AddVectorParameter(
        TEXT("SolverAerationTint"),
        FLinearColor(0.74f, 0.82f, 0.76f, 0.0f));
    UMaterialExpressionLinearInterpolate* SolverConditionedSurface =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    SolverConditionedSurface->A.Expression = SolverDepthTintedSurface;
    SolverConditionedSurface->B.Expression = SolverAerationTint;
    SolverConditionedSurface->Alpha.Expression = SolverAerationAlpha;
    Material->GetExpressionCollection().AddExpression(SolverConditionedSurface);
    UMaterialExpressionScalarParameter* BaseColorScale =
        AddScalarParameter(TEXT("BaseColorScale"), 0.78f);
    UMaterialExpressionMultiply* BaseColor = NewObject<UMaterialExpressionMultiply>(Material);
    BaseColor->A.Expression = SolverConditionedSurface;
    BaseColor->B.Expression = BaseColorScale;
    Material->GetExpressionCollection().AddExpression(BaseColor);

    UMaterialExpressionVectorParameter* AtlasTileOriginParameter =
        AddVectorParameter(TEXT("AtlasTileOrigin"), FLinearColor(0.0f, 0.5f, 0.0f, 0.0f));
    UMaterialExpressionVectorParameter* AtlasTileScaleParameter =
        AddVectorParameter(TEXT("AtlasTileScale"), FLinearColor(1.0f / 3.0f, 1.0f / 2.0f, 0.0f, 0.0f));
    UMaterialExpressionComponentMask* AtlasTileOrigin = NewObject<UMaterialExpressionComponentMask>(Material);
    AtlasTileOrigin->Input.Expression = AtlasTileOriginParameter;
    AtlasTileOrigin->R = true;
    AtlasTileOrigin->G = true;
    Material->GetExpressionCollection().AddExpression(AtlasTileOrigin);
    UMaterialExpressionComponentMask* AtlasTileScale = NewObject<UMaterialExpressionComponentMask>(Material);
    AtlasTileScale->Input.Expression = AtlasTileScaleParameter;
    AtlasTileScale->R = true;
    AtlasTileScale->G = true;
    Material->GetExpressionCollection().AddExpression(AtlasTileScale);

    auto AddWaterNormalSample =
        [Material, AtlasTileOrigin, AtlasTileScale, DefaultNormalTexture](float UTiling, float VTiling) -> UMaterialExpression*
    {
        UMaterialExpressionTextureCoordinate* TexCoord =
            NewObject<UMaterialExpressionTextureCoordinate>(Material);
        TexCoord->UTiling = UTiling;
        TexCoord->VTiling = VTiling;
        Material->GetExpressionCollection().AddExpression(TexCoord);

        UMaterialExpressionFrac* WrappedUvPrimary = NewObject<UMaterialExpressionFrac>(Material);
        WrappedUvPrimary->Input.Expression = TexCoord;
        Material->GetExpressionCollection().AddExpression(WrappedUvPrimary);
        UMaterialExpressionConstant2Vector* HalfPeriodOffset =
            NewObject<UMaterialExpressionConstant2Vector>(Material);
        HalfPeriodOffset->R = 0.5f;
        HalfPeriodOffset->G = 0.0f;
        Material->GetExpressionCollection().AddExpression(HalfPeriodOffset);
        UMaterialExpressionAdd* OffsetTexCoord = NewObject<UMaterialExpressionAdd>(Material);
        OffsetTexCoord->A.Expression = TexCoord;
        OffsetTexCoord->B.Expression = HalfPeriodOffset;
        Material->GetExpressionCollection().AddExpression(OffsetTexCoord);
        UMaterialExpressionFrac* WrappedUvOffset = NewObject<UMaterialExpressionFrac>(Material);
        WrappedUvOffset->Input.Expression = OffsetTexCoord;
        Material->GetExpressionCollection().AddExpression(WrappedUvOffset);

        auto AddAtlasNormalSample =
            [Material, AtlasTileOrigin, AtlasTileScale, DefaultNormalTexture](UMaterialExpression* WrappedUv)
        {
            UMaterialExpressionMultiply* ScaledUv = NewObject<UMaterialExpressionMultiply>(Material);
            ScaledUv->A.Expression = WrappedUv;
            ScaledUv->B.Expression = AtlasTileScale;
            Material->GetExpressionCollection().AddExpression(ScaledUv);
            UMaterialExpressionAdd* AtlasUv = NewObject<UMaterialExpressionAdd>(Material);
            AtlasUv->A.Expression = ScaledUv;
            AtlasUv->B.Expression = AtlasTileOrigin;
            Material->GetExpressionCollection().AddExpression(AtlasUv);
            UMaterialExpressionTextureSampleParameter2D* NormalSample =
                NewObject<UMaterialExpressionTextureSampleParameter2D>(Material);
            NormalSample->ParameterName = TEXT("WaterNormalAtlas");
            NormalSample->Texture = DefaultNormalTexture;
            NormalSample->SamplerType = SAMPLERTYPE_Normal;
            NormalSample->Coordinates.Expression = AtlasUv;
            NormalSample->Group = TEXT("RaftSimSingleLayerWater");
            Material->GetExpressionCollection().AddExpression(NormalSample);
            return NormalSample;
        };
        UMaterialExpressionTextureSampleParameter2D* PrimaryNormalSample =
            AddAtlasNormalSample(WrappedUvPrimary);
        UMaterialExpressionTextureSampleParameter2D* OffsetNormalSample =
            AddAtlasNormalSample(WrappedUvOffset);

        UMaterialExpressionComponentMask* WrappedPrimaryU =
            NewObject<UMaterialExpressionComponentMask>(Material);
        WrappedPrimaryU->Input.Expression = WrappedUvPrimary;
        WrappedPrimaryU->R = true;
        Material->GetExpressionCollection().AddExpression(WrappedPrimaryU);
        UMaterialExpressionConstant* HalfPeriodCenter = NewObject<UMaterialExpressionConstant>(Material);
        HalfPeriodCenter->R = 0.5f;
        Material->GetExpressionCollection().AddExpression(HalfPeriodCenter);
        UMaterialExpressionSubtract* DistanceFromHalfPeriod =
            NewObject<UMaterialExpressionSubtract>(Material);
        DistanceFromHalfPeriod->A.Expression = WrappedPrimaryU;
        DistanceFromHalfPeriod->B.Expression = HalfPeriodCenter;
        Material->GetExpressionCollection().AddExpression(DistanceFromHalfPeriod);
        UMaterialExpressionAbs* AbsoluteDistanceFromHalfPeriod =
            NewObject<UMaterialExpressionAbs>(Material);
        AbsoluteDistanceFromHalfPeriod->Input.Expression = DistanceFromHalfPeriod;
        Material->GetExpressionCollection().AddExpression(AbsoluteDistanceFromHalfPeriod);
        UMaterialExpressionConstant* DoubleDistance = NewObject<UMaterialExpressionConstant>(Material);
        DoubleDistance->R = 2.0f;
        Material->GetExpressionCollection().AddExpression(DoubleDistance);
        UMaterialExpressionMultiply* AtlasNormalSeamBlend =
            NewObject<UMaterialExpressionMultiply>(Material);
        AtlasNormalSeamBlend->A.Expression = AbsoluteDistanceFromHalfPeriod;
        AtlasNormalSeamBlend->B.Expression = DoubleDistance;
        Material->GetExpressionCollection().AddExpression(AtlasNormalSeamBlend);

        UMaterialExpressionLinearInterpolate* SeamContinuousNormal =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        SeamContinuousNormal->A.Expression = PrimaryNormalSample;
        SeamContinuousNormal->B.Expression = OffsetNormalSample;
        SeamContinuousNormal->Alpha.Expression = AtlasNormalSeamBlend;
        Material->GetExpressionCollection().AddExpression(SeamContinuousNormal);
        return SeamContinuousNormal;
    };

    UMaterialExpression* NormalSampleA = AddWaterNormalSample(0.73f, 2.15f);
    UMaterialExpression* NormalSampleB = AddWaterNormalSample(1.11f, 3.30f);
    UMaterialExpressionConstant* NormalLayerBlend = NewObject<UMaterialExpressionConstant>(Material);
    NormalLayerBlend->R = 0.46f;
    Material->GetExpressionCollection().AddExpression(NormalLayerBlend);
    UMaterialExpressionLinearInterpolate* LayeredNormal =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    LayeredNormal->A.Expression = NormalSampleA;
    LayeredNormal->B.Expression = NormalSampleB;
    LayeredNormal->Alpha.Expression = NormalLayerBlend;
    Material->GetExpressionCollection().AddExpression(LayeredNormal);
    UMaterialExpressionAdd* SolverHydraulicPresenceRG = NewObject<UMaterialExpressionAdd>(Material);
    SolverHydraulicPresenceRG->A.Expression = SolverDepth;
    SolverHydraulicPresenceRG->B.Expression = SolverSpeedVisual;
    Material->GetExpressionCollection().AddExpression(SolverHydraulicPresenceRG);
    UMaterialExpressionAdd* SolverHydraulicPresenceRgb = NewObject<UMaterialExpressionAdd>(Material);
    SolverHydraulicPresenceRgb->A.Expression = SolverHydraulicPresenceRG;
    SolverHydraulicPresenceRgb->B.Expression = SolverFroudeVisual;
    Material->GetExpressionCollection().AddExpression(SolverHydraulicPresenceRgb);
    UMaterialExpressionSaturate* SolverHydraulicPresence = NewObject<UMaterialExpressionSaturate>(Material);
    SolverHydraulicPresence->Input.Expression = SolverHydraulicPresenceRgb;
    Material->GetExpressionCollection().AddExpression(SolverHydraulicPresence);
    UMaterialExpressionScalarParameter* SolverMacroNormalWeight =
        AddScalarParameter(TEXT("SolverMacroNormalWeight"), 0.0f);
    UMaterialExpressionMultiply* SolverNormalEnabled = NewObject<UMaterialExpressionMultiply>(Material);
    SolverNormalEnabled->A.Expression = SolverFieldEnable;
    SolverNormalEnabled->B.Expression = SolverMacroNormalWeight;
    Material->GetExpressionCollection().AddExpression(SolverNormalEnabled);
    UMaterialExpressionMultiply* SolverNormalAlpha = NewObject<UMaterialExpressionMultiply>(Material);
    SolverNormalAlpha->A.Expression = SolverNormalEnabled;
    SolverNormalAlpha->B.Expression = SolverHydraulicPresence;
    Material->GetExpressionCollection().AddExpression(SolverNormalAlpha);
    UMaterialExpressionLinearInterpolate* SolverLayeredNormal =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    SolverLayeredNormal->A.Expression = LayeredNormal;
    SolverLayeredNormal->B.Expression = SolverNormalSample;
    SolverLayeredNormal->Alpha.Expression = SolverNormalAlpha;
    Material->GetExpressionCollection().AddExpression(SolverLayeredNormal);
    UMaterialExpressionConstant3Vector* FlatNormal =
        NewObject<UMaterialExpressionConstant3Vector>(Material);
    FlatNormal->Constant = FLinearColor(0.0f, 0.0f, 1.0f);
    Material->GetExpressionCollection().AddExpression(FlatNormal);
    UMaterialExpressionScalarParameter* NormalIntensity =
        AddScalarParameter(TEXT("NormalIntensity"), 0.48f);
    UMaterialExpressionLinearInterpolate* WaterNormal =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    WaterNormal->A.Expression = FlatNormal;
    WaterNormal->B.Expression = SolverLayeredNormal;
    WaterNormal->Alpha.Expression = NormalIntensity;
    Material->GetExpressionCollection().AddExpression(WaterNormal);

    UMaterialExpressionScalarParameter* EmissiveFillScale =
        AddScalarParameter(TEXT("EmissiveFillScale"), 0.004f);
    UMaterialExpressionMultiply* BaseEmissiveColor = NewObject<UMaterialExpressionMultiply>(Material);
    BaseEmissiveColor->A.Expression = BaseColor;
    BaseEmissiveColor->B.Expression = EmissiveFillScale;
    Material->GetExpressionCollection().AddExpression(BaseEmissiveColor);
    UMaterialExpressionFresnel* ReflectionFresnel = NewObject<UMaterialExpressionFresnel>(Material);
    ReflectionFresnel->Exponent = 5.0f;
    ReflectionFresnel->BaseReflectFraction = 0.02f;
    Material->GetExpressionCollection().AddExpression(ReflectionFresnel);
    UMaterialExpressionVectorParameter* ReflectionTint = AddVectorParameter(
        TEXT("ReflectionTint"),
        FLinearColor(0.38f, 0.55f, 0.62f, 0.0f));
    UMaterialExpressionScalarParameter* ReflectionFillIntensity =
        AddScalarParameter(TEXT("ReflectionFillIntensity"), 0.11f);
    UMaterialExpressionMultiply* ReflectionFillMask = NewObject<UMaterialExpressionMultiply>(Material);
    ReflectionFillMask->A.Expression = ReflectionFresnel;
    ReflectionFillMask->B.Expression = ReflectionFillIntensity;
    Material->GetExpressionCollection().AddExpression(ReflectionFillMask);
    UMaterialExpressionMultiply* ReflectionFill = NewObject<UMaterialExpressionMultiply>(Material);
    ReflectionFill->A.Expression = ReflectionTint;
    ReflectionFill->B.Expression = ReflectionFillMask;
    Material->GetExpressionCollection().AddExpression(ReflectionFill);
    UMaterialExpressionAdd* EmissiveColor = NewObject<UMaterialExpressionAdd>(Material);
    EmissiveColor->A.Expression = BaseEmissiveColor;
    EmissiveColor->B.Expression = ReflectionFill;
    Material->GetExpressionCollection().AddExpression(EmissiveColor);
    UMaterialExpressionScalarParameter* BaseRoughness =
        AddScalarParameter(TEXT("Roughness"), 0.09f);
    UMaterialExpressionAdd* SolverRoughnessField = NewObject<UMaterialExpressionAdd>(Material);
    SolverRoughnessField->A.Expression = SolverSpeedVisual;
    SolverRoughnessField->B.Expression = SolverFroudeVisual;
    Material->GetExpressionCollection().AddExpression(SolverRoughnessField);
    UMaterialExpressionSaturate* SolverRoughnessFieldSaturated =
        NewObject<UMaterialExpressionSaturate>(Material);
    SolverRoughnessFieldSaturated->Input.Expression = SolverRoughnessField;
    Material->GetExpressionCollection().AddExpression(SolverRoughnessFieldSaturated);
    UMaterialExpressionScalarParameter* SolverFieldRoughnessWeight =
        AddScalarParameter(TEXT("SolverFieldRoughnessWeight"), 0.0f);
    UMaterialExpressionMultiply* SolverRoughnessWeightEnabled =
        NewObject<UMaterialExpressionMultiply>(Material);
    SolverRoughnessWeightEnabled->A.Expression = SolverFieldRoughnessWeight;
    SolverRoughnessWeightEnabled->B.Expression = SolverFieldEnable;
    Material->GetExpressionCollection().AddExpression(SolverRoughnessWeightEnabled);
    UMaterialExpressionMultiply* SolverRoughnessResponse =
        NewObject<UMaterialExpressionMultiply>(Material);
    SolverRoughnessResponse->A.Expression = SolverRoughnessFieldSaturated;
    SolverRoughnessResponse->B.Expression = SolverRoughnessWeightEnabled;
    Material->GetExpressionCollection().AddExpression(SolverRoughnessResponse);
    UMaterialExpressionAdd* RoughnessWithSolverResponse = NewObject<UMaterialExpressionAdd>(Material);
    RoughnessWithSolverResponse->A.Expression = BaseRoughness;
    RoughnessWithSolverResponse->B.Expression = SolverRoughnessResponse;
    Material->GetExpressionCollection().AddExpression(RoughnessWithSolverResponse);
    UMaterialExpressionSaturate* Roughness = NewObject<UMaterialExpressionSaturate>(Material);
    Roughness->Input.Expression = RoughnessWithSolverResponse;
    Material->GetExpressionCollection().AddExpression(Roughness);
    UMaterialExpressionScalarParameter* Specular =
        AddScalarParameter(TEXT("Specular"), 0.52f);
    if (UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData())
    {
        ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, BaseColor);
        ConnectPreviewMaterialColorInput(EditorOnlyData->EmissiveColor, EmissiveColor);
        ConnectPreviewMaterialVectorInput(EditorOnlyData->Normal, WaterNormal);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, Roughness);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);
    }

    // SetMaterialUsage compiles immediately. Refresh cached expression data first so
    // refraction and default textures match the newly generated graph during that compile.
    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (!Material->SetMaterialUsage(MATUSAGE_Water))
    {
        OutSummary += TEXT("Failed to enable Water material usage for solver-surface water.\n");
        return nullptr;
    }
    Material->PostEditChange();
    Package->MarkPackageDirty();
    const FString Filename =
        FPackageName::LongPackageNameToFilename(MaterialPackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
    {
        OutSummary += TEXT("Failed to save the solver-surface water candidate material.\n");
        return nullptr;
    }
    FAssetCompilingManager::Get().FinishAllCompilation();
    return Material;
}

UMaterialInterface* LoadOrCreateLandscapeCandidateSolverFoamMaterial(FString& OutSummary)
{
    static const TCHAR* MaterialPackagePath =
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/M_RaftSim_SolverFieldFoamCandidate");
    static const TCHAR* MaterialObjectPath =
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/"
             "M_RaftSim_SolverFieldFoamCandidate.M_RaftSim_SolverFieldFoamCandidate");

    UPackage* Package = CreatePackage(MaterialPackagePath);
    if (!Package)
    {
        OutSummary += TEXT("Failed to create the solver-field foam material package.\n");
        return nullptr;
    }
    UMaterial* Material = Cast<UMaterial>(
        StaticLoadObject(UMaterial::StaticClass(), nullptr, MaterialObjectPath));
    if (!Material)
    {
        Material = FindObject<UMaterial>(Package, TEXT("M_RaftSim_SolverFieldFoamCandidate"));
    }
    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package,
            TEXT("M_RaftSim_SolverFieldFoamCandidate"),
            RF_Public | RF_Standalone | RF_Transactional);
        if (Material)
        {
            FAssetRegistryModule::AssetCreated(Material);
        }
    }
    if (!Material)
    {
        OutSummary += TEXT("Failed to create the solver-field foam material.\n");
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->SetShadingModel(MSM_DefaultLit);
    Material->BlendMode = BLEND_Translucent;
    Material->TwoSided = true;

    UMaterialExpressionVertexColor* VertexColor = NewObject<UMaterialExpressionVertexColor>(Material);
    Material->GetExpressionCollection().AddExpression(VertexColor);
    UMaterialExpressionConstant* Roughness = NewObject<UMaterialExpressionConstant>(Material);
    Roughness->R = 0.82f;
    Material->GetExpressionCollection().AddExpression(Roughness);
    UMaterialExpressionConstant* Specular = NewObject<UMaterialExpressionConstant>(Material);
    Specular->R = 0.18f;
    Material->GetExpressionCollection().AddExpression(Specular);
    UMaterialExpressionConstant* EmissiveScale = NewObject<UMaterialExpressionConstant>(Material);
    EmissiveScale->R = 0.025f;
    Material->GetExpressionCollection().AddExpression(EmissiveScale);
    UMaterialExpressionMultiply* EmissiveColor = NewObject<UMaterialExpressionMultiply>(Material);
    EmissiveColor->A.Expression = VertexColor;
    EmissiveColor->B.Expression = EmissiveScale;
    Material->GetExpressionCollection().AddExpression(EmissiveColor);

    if (UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData())
    {
        ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, VertexColor);
        ConnectPreviewMaterialColorInput(EditorOnlyData->EmissiveColor, EmissiveColor);
        EditorOnlyData->Opacity.Expression = VertexColor;
        EditorOnlyData->Opacity.OutputIndex = 4;
        EditorOnlyData->Opacity.Mask = 1;
        EditorOnlyData->Opacity.MaskR = 0;
        EditorOnlyData->Opacity.MaskG = 0;
        EditorOnlyData->Opacity.MaskB = 0;
        EditorOnlyData->Opacity.MaskA = 1;
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, Roughness);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);
    }

    Material->PostEditChange();
    Package->MarkPackageDirty();
    const FString Filename =
        FPackageName::LongPackageNameToFilename(MaterialPackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
    {
        OutSummary += TEXT("Failed to save the solver-field foam material.\n");
        return nullptr;
    }
    FAssetCompilingManager::Get().FinishAllCompilation();
    return Material;
}

UMaterialInterface* LoadOrCreateLandscapeCandidateWaterMaterial(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    FString& OutSummary)
{
    FString RiverAssetName;
    if (Spec.RiverId == TEXT("american_south_fork"))
    {
        RiverAssetName = TEXT("AmericanSouthFork");
    }
    else if (Spec.RiverId == TEXT("colorado_river"))
    {
        RiverAssetName = TEXT("ColoradoRiver");
    }
    else if (Spec.RiverId == TEXT("pacuare"))
    {
        RiverAssetName = TEXT("Pacuare");
    }
    if (RiverAssetName.IsEmpty())
    {
        OutSummary += FString::Printf(
            TEXT("No solver-surface water asset token exists for %s.\n"),
            *Spec.RiverId);
        return nullptr;
    }

    UMaterial* Parent = LoadOrCreateLandscapeCandidateSolverSurfaceWaterParent(OutSummary);
    if (!Parent)
    {
        return nullptr;
    }
    const FString NormalAtlasName = FString::Printf(
        TEXT("T_RaftSim_%s_NormalAtlas"),
        *RiverAssetName);
    const FString NormalAtlasObjectPath = FString::Printf(
        TEXT("/Game/RaftSim/Rendering/ProceduralTextureAtlases/Textures/%s.%s"),
        *NormalAtlasName,
        *NormalAtlasName);
    UTexture2D* WaterNormalAtlas = LoadObject<UTexture2D>(nullptr, *NormalAtlasObjectPath);
    if (!WaterNormalAtlas)
    {
        OutSummary += FString::Printf(
            TEXT("Missing water normal atlas %s for %s.\n"),
            *NormalAtlasObjectPath,
            *Spec.RiverId);
        return nullptr;
    }
    UTexture2D* SolverVisualizationNormal = nullptr;
    UTexture2D* SolverVisualizationFields = nullptr;
    if (Spec.RiverId == TEXT("american_south_fork"))
    {
        SolverVisualizationNormal = LoadObject<UTexture2D>(
            nullptr,
            TEXT("/Game/RaftSim/Rendering/SolverVisualizationFields/Textures/"
                 "T_RaftSim_AmericanSouthFork_CppSolverSurfaceNormal."
                 "T_RaftSim_AmericanSouthFork_CppSolverSurfaceNormal"));
        SolverVisualizationFields = LoadObject<UTexture2D>(
            nullptr,
            TEXT("/Game/RaftSim/Rendering/SolverVisualizationFields/Textures/"
                 "T_RaftSim_AmericanSouthFork_CppSolverDepthSpeedFroude."
                 "T_RaftSim_AmericanSouthFork_CppSolverDepthSpeedFroude"));
        if (!SolverVisualizationNormal || !SolverVisualizationFields)
        {
            OutSummary += TEXT("Missing validated South Fork C++ solver visualization Texture2D assets.\n");
            return nullptr;
        }
    }

    const FString AssetName = FString::Printf(
        TEXT("MI_RaftSim_%s_SolverSurfaceWaterCandidate"),
        *RiverAssetName);
    const FString PackagePath = FString::Printf(
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/%s"),
        *AssetName);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, *AssetName);
    UPackage* Package = CreatePackage(*PackagePath);
    if (!Package)
    {
        return nullptr;
    }
    UMaterialInstanceConstant* Instance = Cast<UMaterialInstanceConstant>(
        StaticLoadObject(UMaterialInstanceConstant::StaticClass(), nullptr, *ObjectPath));
    if (!Instance)
    {
        Instance = FindObject<UMaterialInstanceConstant>(Package, *AssetName);
    }
    if (!Instance)
    {
        Instance = NewObject<UMaterialInstanceConstant>(
            Package,
            *AssetName,
            RF_Public | RF_Standalone | RF_Transactional);
        if (Instance)
        {
            FAssetRegistryModule::AssetCreated(Instance);
        }
    }
    if (!Instance)
    {
        return nullptr;
    }

    const FRaftSimLandscapeCandidateWaterSettings Settings =
        GetLandscapeCandidateWaterSettings(Spec.RiverId);
    Instance->Modify();
    Instance->SetParentEditorOnly(Parent);
    auto SetScalar = [Instance](const TCHAR* Name, float Value)
    {
        Instance->SetScalarParameterValueEditorOnly(FMaterialParameterInfo(Name), Value);
    };
    auto SetVector = [Instance](const TCHAR* Name, const FLinearColor& Value)
    {
        Instance->SetVectorParameterValueEditorOnly(FMaterialParameterInfo(Name), Value);
    };
    SetScalar(TEXT("BaseColorScale"), Settings.BaseColorScale);
    SetScalar(TEXT("VertexTintWeight"), Settings.VertexTintWeight);
    SetScalar(TEXT("EmissiveFillScale"), Settings.EmissiveFillScale);
    SetScalar(TEXT("ReflectionFillIntensity"), Settings.ReflectionFillIntensity);
    SetScalar(TEXT("Roughness"), Settings.Roughness);
    SetScalar(TEXT("Specular"), Settings.Specular);
    SetScalar(TEXT("NormalIntensity"), Settings.NormalIntensity);
    SetScalar(TEXT("SolverFieldEnable"), Settings.SolverFieldEnable);
    SetScalar(TEXT("SolverMacroNormalWeight"), Settings.SolverMacroNormalWeight);
    SetScalar(TEXT("SolverDepthColorWeight"), Settings.SolverDepthColorWeight);
    SetScalar(TEXT("SolverFieldRoughnessWeight"), Settings.SolverFieldRoughnessWeight);
    SetScalar(TEXT("SolverFroudeAerationWeight"), Settings.SolverFroudeAerationWeight);
    SetScalar(TEXT("SolverSpeedVisualGain"), Settings.SolverSpeedVisualGain);
    SetScalar(TEXT("SolverFroudeVisualGain"), Settings.SolverFroudeVisualGain);
    SetVector(TEXT("SurfaceTint"), Settings.SurfaceTint);
    SetVector(TEXT("SolverDeepWaterTint"), Settings.SolverDeepWaterTint);
    SetVector(TEXT("SolverAerationTint"), Settings.SolverAerationTint);
    SetVector(TEXT("ReflectionTint"), Settings.ReflectionTint);
    SetVector(TEXT("AtlasTileOrigin"), FLinearColor(0.0f, 0.5f, 0.0f, 0.0f));
    SetVector(TEXT("AtlasTileScale"), FLinearColor(1.0f / 3.0f, 1.0f / 2.0f, 0.0f, 0.0f));
    Instance->SetTextureParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("WaterNormalAtlas")),
        WaterNormalAtlas);
    if (SolverVisualizationNormal && SolverVisualizationFields)
    {
        Instance->SetTextureParameterValueEditorOnly(
            FMaterialParameterInfo(TEXT("SolverVisualizationNormal")),
            SolverVisualizationNormal);
        Instance->SetTextureParameterValueEditorOnly(
            FMaterialParameterInfo(TEXT("SolverVisualizationFields")),
            SolverVisualizationFields);
    }
    Instance->PostEditChange();
    Package->MarkPackageDirty();

    const FString Filename =
        FPackageName::LongPackageNameToFilename(PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Instance, *Filename, SaveArgs))
    {
        OutSummary += FString::Printf(TEXT("Failed to save %s.\n"), *ObjectPath);
        return nullptr;
    }
    FAssetCompilingManager::Get().FinishAllCompilation();
    OutSummary += FString::Printf(
        TEXT("Built %s opaque DefaultLit solver-surface water candidate (roughness %.3f, normal %.3f, solver field %.0f).\n"),
        *Spec.RiverId,
        Settings.Roughness,
        Settings.NormalIntensity,
        Settings.SolverFieldEnable);
    return Instance;
}

struct FRaftSimFirstPartyMaterialTextureAssetSpec
{
    FString RiverId;
    FString RiverAssetName;
    FString MapKey;
    FString MapKind;
    FString SourceRelativePath;
    FString TextureAssetRootPackagePath = TEXT("/Game/RaftSim/Rendering/ProceduralTextureAtlases/Textures");
    TextureCompressionSettings CompressionSettings = TC_Default;
    bool bSRGB = true;
    TextureGroup LODGroup = TEXTUREGROUP_World;
    TextureAddress AddressX = TA_Wrap;
    TextureAddress AddressY = TA_Wrap;
    bool bCompressionNoAlpha = true;

    FString GetTextureAssetName() const
    {
        return FString::Printf(TEXT("T_RaftSim_%s_%s"), *RiverAssetName, *MapKey);
    }

    FString GetTextureAssetPath() const
    {
        const FString TextureAssetName = GetTextureAssetName();
        return FString::Printf(TEXT("%s/%s"), *TextureAssetRootPackagePath, *TextureAssetName);
    }
};

FString GetFirstPartyMaterialTextureAssetBindingKey(const FString& RiverId, const FString& MapKey)
{
    return FString::Printf(TEXT("%s|%s"), *RiverId, *MapKey);
}

bool LoadPreviewPngBgraPixels(const FString& RelativePath, int32& OutWidth, int32& OutHeight, TArray<FColor>& OutPixels)
{
    OutWidth = 0;
    OutHeight = 0;
    OutPixels.Reset();
    if (RelativePath.IsEmpty())
    {
        return false;
    }

    const FString AbsolutePath = FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), RelativePath));
    TArray<uint8> CompressedImage;
    if (!FFileHelper::LoadFileToArray(CompressedImage, *AbsolutePath))
    {
        UE_LOG(LogRaftSimEditor, Warning, TEXT("Failed to load first-party material PNG: %s"), *AbsolutePath);
        return false;
    }

    IImageWrapperModule& ImageWrapperModule =
        FModuleManager::LoadModuleChecked<IImageWrapperModule>(FName(TEXT("ImageWrapper")));
    TSharedPtr<IImageWrapper> ImageWrapper = ImageWrapperModule.CreateImageWrapper(EImageFormat::PNG, *AbsolutePath);
    if (!ImageWrapper.IsValid() || !ImageWrapper->SetCompressed(CompressedImage.GetData(), CompressedImage.Num()))
    {
        UE_LOG(LogRaftSimEditor, Warning, TEXT("Failed to decode first-party material PNG header: %s"), *AbsolutePath);
        return false;
    }

    TArray<uint8> RawBgra;
    if (!ImageWrapper->GetRaw(ERGBFormat::BGRA, 8, RawBgra))
    {
        UE_LOG(LogRaftSimEditor, Warning, TEXT("Failed to decode first-party material PNG pixels: %s"), *AbsolutePath);
        return false;
    }

    OutWidth = ImageWrapper->GetWidth();
    OutHeight = ImageWrapper->GetHeight();
    if (OutWidth <= 0 || OutHeight <= 0 || RawBgra.Num() != OutWidth * OutHeight * 4)
    {
        UE_LOG(LogRaftSimEditor, Warning, TEXT("First-party material PNG dimensions are invalid: %s"), *AbsolutePath);
        OutWidth = 0;
        OutHeight = 0;
        return false;
    }

    OutPixels.Reserve(OutWidth * OutHeight);
    for (int32 PixelIndex = 0; PixelIndex < OutWidth * OutHeight; ++PixelIndex)
    {
        const int32 ByteIndex = PixelIndex * 4;
        OutPixels.Add(FColor(
            RawBgra[ByteIndex + 2],
            RawBgra[ByteIndex + 1],
            RawBgra[ByteIndex],
            RawBgra[ByteIndex + 3]));
    }

    return true;
}

TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> GetFirstPartyMaterialTextureAtlasAssetSpecs()
{
    struct FRiverSpec
    {
        const TCHAR* RiverId;
        const TCHAR* RiverAssetName;
    };

    const FRiverSpec RiverSpecs[] = {
        {TEXT("american_south_fork"), TEXT("AmericanSouthFork")},
        {TEXT("colorado_river"), TEXT("ColoradoRiver")},
        {TEXT("pacuare"), TEXT("Pacuare")},
    };

    TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> Specs;
    for (const FRiverSpec& RiverSpec : RiverSpecs)
    {
        FRaftSimFirstPartyMaterialTextureAssetSpec Albedo;
        Albedo.RiverId = RiverSpec.RiverId;
        Albedo.RiverAssetName = RiverSpec.RiverAssetName;
        Albedo.MapKey = TEXT("AlbedoAtlas");
        Albedo.MapKind = TEXT("albedo");
        Albedo.SourceRelativePath = GetFirstPartyMaterialTextureAtlasAlbedoRelativePath(RiverSpec.RiverId);
        Albedo.CompressionSettings = TC_Default;
        Albedo.bSRGB = true;
        Albedo.LODGroup = TEXTUREGROUP_World;
        Specs.Add(Albedo);

        FRaftSimFirstPartyMaterialTextureAssetSpec Normal;
        Normal.RiverId = RiverSpec.RiverId;
        Normal.RiverAssetName = RiverSpec.RiverAssetName;
        Normal.MapKey = TEXT("NormalAtlas");
        Normal.MapKind = TEXT("normal");
        Normal.SourceRelativePath = GetFirstPartyMaterialTextureAtlasNormalRelativePath(RiverSpec.RiverId);
        Normal.CompressionSettings = TC_Normalmap;
        Normal.bSRGB = false;
        Normal.LODGroup = TEXTUREGROUP_WorldNormalMap;
        Specs.Add(Normal);

        FRaftSimFirstPartyMaterialTextureAssetSpec Packed;
        Packed.RiverId = RiverSpec.RiverId;
        Packed.RiverAssetName = RiverSpec.RiverAssetName;
        Packed.MapKey = TEXT("AORoughnessHeightAtlas");
        Packed.MapKind = TEXT("ao_roughness_height");
        Packed.SourceRelativePath = GetFirstPartyMaterialTextureAtlasPackedRelativePath(RiverSpec.RiverId);
        Packed.CompressionSettings = TC_Masks;
        Packed.bSRGB = false;
        Packed.LODGroup = TEXTUREGROUP_World;
        Specs.Add(Packed);

        FRaftSimFirstPartyMaterialTextureAssetSpec NormalDetail;
        NormalDetail.RiverId = RiverSpec.RiverId;
        NormalDetail.RiverAssetName = RiverSpec.RiverAssetName;
        NormalDetail.MapKey = TEXT("SourceConditionedNormalDetail");
        NormalDetail.MapKind = TEXT("source_conditioned_normal_detail");
        NormalDetail.SourceRelativePath =
            GetSourceConditionedMaterialMapRelativePath(RiverSpec.RiverId, NormalDetail.MapKey);
        NormalDetail.TextureAssetRootPackagePath = TEXT("/Game/RaftSim/Rendering/SourceConditionedMaterialMaps/Textures");
        NormalDetail.CompressionSettings = TC_Normalmap;
        NormalDetail.bSRGB = false;
        NormalDetail.LODGroup = TEXTUREGROUP_WorldNormalMap;
        Specs.Add(NormalDetail);
    }

    return Specs;
}

TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> GetSourceConditionedMaterialTextureAssetSpecs()
{
    struct FRiverSpec
    {
        const TCHAR* RiverId;
        const TCHAR* RiverAssetName;
    };

    const FRiverSpec RiverSpecs[] = {
        {TEXT("american_south_fork"), TEXT("AmericanSouthFork")},
        {TEXT("colorado_river"), TEXT("ColoradoRiver")},
        {TEXT("pacuare"), TEXT("Pacuare")},
    };

    TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> Specs;
    for (const FRiverSpec& RiverSpec : RiverSpecs)
    {
        FRaftSimFirstPartyMaterialTextureAssetSpec MacroAlbedo;
        MacroAlbedo.RiverId = RiverSpec.RiverId;
        MacroAlbedo.RiverAssetName = RiverSpec.RiverAssetName;
        MacroAlbedo.MapKey = TEXT("SourceConditionedMacroAlbedo");
        MacroAlbedo.MapKind = TEXT("source_conditioned_macro_albedo");
        MacroAlbedo.SourceRelativePath = GetSourceConditionedMaterialMapRelativePath(RiverSpec.RiverId, MacroAlbedo.MapKey);
        MacroAlbedo.TextureAssetRootPackagePath = TEXT("/Game/RaftSim/Rendering/SourceConditionedMaterialMaps/Textures");
        MacroAlbedo.CompressionSettings = TC_Default;
        MacroAlbedo.bSRGB = true;
        MacroAlbedo.LODGroup = TEXTUREGROUP_World;
        Specs.Add(MacroAlbedo);

        FRaftSimFirstPartyMaterialTextureAssetSpec MaterialZones;
        MaterialZones.RiverId = RiverSpec.RiverId;
        MaterialZones.RiverAssetName = RiverSpec.RiverAssetName;
        MaterialZones.MapKey = TEXT("SourceConditionedMaterialZones");
        MaterialZones.MapKind = TEXT("source_conditioned_material_zones");
        MaterialZones.SourceRelativePath =
            GetSourceConditionedMaterialMapRelativePath(RiverSpec.RiverId, MaterialZones.MapKey);
        MaterialZones.TextureAssetRootPackagePath = TEXT("/Game/RaftSim/Rendering/SourceConditionedMaterialMaps/Textures");
        MaterialZones.CompressionSettings = TC_Masks;
        MaterialZones.bSRGB = false;
        MaterialZones.LODGroup = TEXTUREGROUP_World;
        Specs.Add(MaterialZones);

        FRaftSimFirstPartyMaterialTextureAssetSpec Packed;
        Packed.RiverId = RiverSpec.RiverId;
        Packed.RiverAssetName = RiverSpec.RiverAssetName;
        Packed.MapKey = TEXT("SourceConditionedAORoughnessHeight");
        Packed.MapKind = TEXT("source_conditioned_ao_roughness_height");
        Packed.SourceRelativePath = GetSourceConditionedMaterialMapRelativePath(RiverSpec.RiverId, Packed.MapKey);
        Packed.TextureAssetRootPackagePath = TEXT("/Game/RaftSim/Rendering/SourceConditionedMaterialMaps/Textures");
        Packed.CompressionSettings = TC_Masks;
        Packed.bSRGB = false;
        Packed.LODGroup = TEXTUREGROUP_World;
        Specs.Add(Packed);
    }

    return Specs;
}

TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> GetProductionDetailMaterialTextureAssetSpecs()
{
    struct FRiverSpec
    {
        const TCHAR* RiverId;
        const TCHAR* RiverAssetName;
    };

    const FRiverSpec RiverSpecs[] = {
        {TEXT("american_south_fork"), TEXT("AmericanSouthFork")},
        {TEXT("colorado_river"), TEXT("ColoradoRiver")},
        {TEXT("pacuare"), TEXT("Pacuare")},
    };

    TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> Specs;
    for (const FRiverSpec& RiverSpec : RiverSpecs)
    {
        FRaftSimFirstPartyMaterialTextureAssetSpec Albedo;
        Albedo.RiverId = RiverSpec.RiverId;
        Albedo.RiverAssetName = RiverSpec.RiverAssetName;
        Albedo.MapKey = TEXT("TerrainDetailAlbedo");
        Albedo.MapKind = TEXT("first_party_terrain_detail_albedo");
        Albedo.SourceRelativePath = GetProductionDetailTextureRelativePath(RiverSpec.RiverId, Albedo.MapKey);
        Albedo.TextureAssetRootPackagePath = TEXT("/Game/RaftSim/Rendering/ProductionDetailTextures/Textures");
        Albedo.CompressionSettings = TC_Default;
        Albedo.bSRGB = true;
        Albedo.LODGroup = TEXTUREGROUP_World;
        Specs.Add(Albedo);

        FRaftSimFirstPartyMaterialTextureAssetSpec Normal;
        Normal.RiverId = RiverSpec.RiverId;
        Normal.RiverAssetName = RiverSpec.RiverAssetName;
        Normal.MapKey = TEXT("TerrainDetailNormal");
        Normal.MapKind = TEXT("first_party_terrain_detail_normal");
        Normal.SourceRelativePath = GetProductionDetailTextureRelativePath(RiverSpec.RiverId, Normal.MapKey);
        Normal.TextureAssetRootPackagePath = TEXT("/Game/RaftSim/Rendering/ProductionDetailTextures/Textures");
        Normal.CompressionSettings = TC_Normalmap;
        Normal.bSRGB = false;
        Normal.LODGroup = TEXTUREGROUP_WorldNormalMap;
        Specs.Add(Normal);

        FRaftSimFirstPartyMaterialTextureAssetSpec Packed;
        Packed.RiverId = RiverSpec.RiverId;
        Packed.RiverAssetName = RiverSpec.RiverAssetName;
        Packed.MapKey = TEXT("TerrainDetailAORoughnessHeight");
        Packed.MapKind = TEXT("first_party_terrain_detail_ao_roughness_height");
        Packed.SourceRelativePath = GetProductionDetailTextureRelativePath(RiverSpec.RiverId, Packed.MapKey);
        Packed.TextureAssetRootPackagePath = TEXT("/Game/RaftSim/Rendering/ProductionDetailTextures/Textures");
        Packed.CompressionSettings = TC_Masks;
        Packed.bSRGB = false;
        Packed.LODGroup = TEXTUREGROUP_World;
        Specs.Add(Packed);
    }

    return Specs;
}

TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> GetSolverVisualizationFieldTextureAssetSpecs()
{
    TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> Specs;

    FRaftSimFirstPartyMaterialTextureAssetSpec Normal;
    Normal.RiverId = TEXT("american_south_fork");
    Normal.RiverAssetName = TEXT("AmericanSouthFork");
    Normal.MapKey = TEXT("CppSolverSurfaceNormal");
    Normal.MapKind = TEXT("validated_cpp_solver_surface_normal");
    Normal.SourceRelativePath =
        TEXT("unreal/Content/RaftSim/Rendering/SolverVisualizationFields/"
             "american_south_fork_median_cpp_solver_surface_normal_v1.png");
    Normal.TextureAssetRootPackagePath = TEXT("/Game/RaftSim/Rendering/SolverVisualizationFields/Textures");
    Normal.CompressionSettings = TC_Normalmap;
    Normal.bSRGB = false;
    Normal.LODGroup = TEXTUREGROUP_WorldNormalMap;
    Normal.AddressX = TA_Clamp;
    Normal.AddressY = TA_Clamp;
    Specs.Add(Normal);

    FRaftSimFirstPartyMaterialTextureAssetSpec Packed;
    Packed.RiverId = TEXT("american_south_fork");
    Packed.RiverAssetName = TEXT("AmericanSouthFork");
    Packed.MapKey = TEXT("CppSolverDepthSpeedFroude");
    Packed.MapKind = TEXT("validated_cpp_solver_depth_speed_froude");
    Packed.SourceRelativePath =
        TEXT("unreal/Content/RaftSim/Rendering/SolverVisualizationFields/"
             "american_south_fork_median_cpp_solver_depth_speed_froude_v1.png");
    Packed.TextureAssetRootPackagePath = TEXT("/Game/RaftSim/Rendering/SolverVisualizationFields/Textures");
    Packed.CompressionSettings = TC_Masks;
    Packed.bSRGB = false;
    Packed.LODGroup = TEXTUREGROUP_World;
    Packed.AddressX = TA_Clamp;
    Packed.AddressY = TA_Clamp;
    Packed.bCompressionNoAlpha = false;
    Specs.Add(Packed);

    return Specs;
}

void ApplyFirstPartyMaterialTextureImportSettings(
    UTexture2D* Texture,
    const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec)
{
    if (!Texture)
    {
        return;
    }

    Texture->SRGB = Spec.bSRGB;
    Texture->CompressionSettings = Spec.CompressionSettings;
    Texture->MipGenSettings = TMGS_FromTextureGroup;
    Texture->LODGroup = Spec.LODGroup;
    Texture->AddressX = Spec.AddressX;
    Texture->AddressY = Spec.AddressY;
    Texture->CompressionNoAlpha = Spec.bCompressionNoAlpha;
    Texture->DeferCompression = false;
    Texture->VirtualTextureStreaming = false;
    Texture->SetModernSettingsForNewOrChangedTexture();
}

bool UpdateFirstPartyMaterialTextureSource(
    UTexture2D* Texture,
    const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec,
    int32 Width,
    int32 Height,
    const TArray<FColor>& Pixels)
{
    if (!Texture || Width <= 0 || Height <= 0 || Pixels.Num() != Width * Height)
    {
        return false;
    }

    Texture->Modify();
    Texture->Source.Init(Width, Height, 1, 1, TSF_BGRA8);
    uint8* MipData = Texture->Source.LockMip(0);
    for (int32 Y = 0; Y < Height; ++Y)
    {
        uint8* DestPtr = &MipData[static_cast<int64>(Y) * Width * sizeof(FColor)];
        const FColor* SrcPtr = &Pixels[static_cast<int64>(Y) * Width];
        for (int32 X = 0; X < Width; ++X)
        {
            *DestPtr++ = SrcPtr->B;
            *DestPtr++ = SrcPtr->G;
            *DestPtr++ = SrcPtr->R;
            *DestPtr++ = SrcPtr->A;
            ++SrcPtr;
        }
    }
    Texture->Source.UnlockMip(0);
    ApplyFirstPartyMaterialTextureImportSettings(Texture, Spec);
    Texture->PostEditChange();
    return true;
}

UTexture2D* CreateOrUpdateFirstPartyMaterialTextureAsset(
    const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec,
    FString& OutSummary,
    bool& bOutSaved)
{
    bOutSaved = false;

    int32 Width = 0;
    int32 Height = 0;
    TArray<FColor> Pixels;
    if (!LoadPreviewPngBgraPixels(Spec.SourceRelativePath, Width, Height, Pixels))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to load first-party material texture source %s for %s/%s\n"),
            *Spec.SourceRelativePath,
            *Spec.RiverId,
            *Spec.MapKey);
        return nullptr;
    }

    const FString PackagePath = Spec.GetTextureAssetPath();
    const FString AssetName = FPackageName::GetLongPackageAssetName(PackagePath);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, *AssetName);

    UPackage* Package = CreatePackage(*PackagePath);
    if (!Package)
    {
        OutSummary += FString::Printf(TEXT("Failed to create texture package %s\n"), *PackagePath);
        return nullptr;
    }

    UObject* ExistingObject = StaticLoadObject(UObject::StaticClass(), nullptr, *ObjectPath);
    UTexture2D* Texture = Cast<UTexture2D>(ExistingObject);
    if (!Texture)
    {
        Texture = FindObject<UTexture2D>(Package, *AssetName);
    }
    if (!Texture && ExistingObject)
    {
        OutSummary += FString::Printf(TEXT("Existing first-party material texture asset is not a Texture2D: %s\n"), *ObjectPath);
        return nullptr;
    }
    if (!Texture)
    {
        Texture = NewObject<UTexture2D>(Package, *AssetName, RF_Public | RF_Standalone | RF_Transactional);
        FAssetRegistryModule::AssetCreated(Texture);
    }
    if (!Texture)
    {
        OutSummary += FString::Printf(TEXT("Failed to create first-party material texture asset %s\n"), *ObjectPath);
        return nullptr;
    }

    if (!UpdateFirstPartyMaterialTextureSource(Texture, Spec, Width, Height, Pixels))
    {
        OutSummary += FString::Printf(TEXT("Failed to update first-party material texture source %s\n"), *ObjectPath);
        return nullptr;
    }

    Package->MarkPackageDirty();
    const FString Filename =
        FPackageName::LongPackageNameToFilename(PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);

    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;

    bOutSaved = UPackage::SavePackage(Package, Texture, *Filename, SaveArgs);
    OutSummary += FString::Printf(
        TEXT("%s first-party material Texture2D review asset %s (%s/%s) from %s -> %s\n"),
        bOutSaved ? TEXT("Saved") : TEXT("Failed"),
        *ObjectPath,
        *Spec.RiverId,
        *Spec.MapKey,
        *Spec.SourceRelativePath,
        *Filename);
    return bOutSaved ? Texture : nullptr;
}

bool CreateFirstPartyMaterialTextureAtlasAssets(
    TMap<FString, UTexture2D*>& OutTextureAssetsByKey,
    FString& OutSummary)
{
    bool bAllSaved = true;
    OutTextureAssetsByKey.Reset();

    for (const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec : GetFirstPartyMaterialTextureAtlasAssetSpecs())
    {
        bool bSaved = false;
        UTexture2D* Texture = CreateOrUpdateFirstPartyMaterialTextureAsset(Spec, OutSummary, bSaved);
        bAllSaved &= bSaved && Texture != nullptr;
        if (Texture)
        {
            OutTextureAssetsByKey.Add(GetFirstPartyMaterialTextureAssetBindingKey(Spec.RiverId, Spec.MapKey), Texture);
        }
    }

    return bAllSaved;
}

bool CreateSourceConditionedMaterialTextureAssets(
    TMap<FString, UTexture2D*>& InOutTextureAssetsByKey,
    FString& OutSummary)
{
    bool bAllSaved = true;

    for (const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec : GetSourceConditionedMaterialTextureAssetSpecs())
    {
        bool bSaved = false;
        UTexture2D* Texture = CreateOrUpdateFirstPartyMaterialTextureAsset(Spec, OutSummary, bSaved);
        bAllSaved &= bSaved && Texture != nullptr;
        if (Texture)
        {
            InOutTextureAssetsByKey.Add(GetFirstPartyMaterialTextureAssetBindingKey(Spec.RiverId, Spec.MapKey), Texture);
        }
    }

    return bAllSaved;
}

bool CreateProductionDetailMaterialTextureAssets(
    TMap<FString, UTexture2D*>& InOutTextureAssetsByKey,
    FString& OutSummary)
{
    bool bAllSaved = true;

    for (const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec : GetProductionDetailMaterialTextureAssetSpecs())
    {
        bool bSaved = false;
        UTexture2D* Texture = CreateOrUpdateFirstPartyMaterialTextureAsset(Spec, OutSummary, bSaved);
        bAllSaved &= bSaved && Texture != nullptr;
        if (Texture)
        {
            InOutTextureAssetsByKey.Add(GetFirstPartyMaterialTextureAssetBindingKey(Spec.RiverId, Spec.MapKey), Texture);
        }
    }

    return bAllSaved;
}

bool CreateSolverVisualizationFieldTextureAssets(FString& OutSummary)
{
    bool bAllSaved = true;
    for (const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec : GetSolverVisualizationFieldTextureAssetSpecs())
    {
        bool bSaved = false;
        UTexture2D* Texture = CreateOrUpdateFirstPartyMaterialTextureAsset(Spec, OutSummary, bSaved);
        bAllSaved &= bSaved && Texture != nullptr;
    }
    return bAllSaved;
}

UMaterialInterface* LoadOrCreateFirstPartyAtlasSampleReviewMaterial(
    const TMap<FString, UTexture2D*>& TextureAssetsByKey,
    FString& OutSummary)
{
    static const TCHAR* MaterialPackagePath = TEXT("/Game/RaftSim/Materials/M_RaftSim_AtlasSampleReview");
    static const TCHAR* MaterialObjectPath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_AtlasSampleReview.M_RaftSim_AtlasSampleReview");

    UMaterial* Material = Cast<UMaterial>(StaticLoadObject(UMaterial::StaticClass(), nullptr, MaterialObjectPath));
    UPackage* Package = Material ? Material->GetOutermost() : CreatePackage(MaterialPackagePath);
    if (!Package)
    {
        OutSummary += FString::Printf(TEXT("Failed to create atlas sample review material package %s\n"), MaterialPackagePath);
        return nullptr;
    }

    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package,
            TEXT("M_RaftSim_AtlasSampleReview"),
            RF_Public | RF_Standalone | RF_Transactional);
        if (!Material)
        {
            OutSummary += FString::Printf(TEXT("Failed to create atlas sample review material %s\n"), MaterialObjectPath);
            return nullptr;
        }
        FAssetRegistryModule::AssetCreated(Material);
    }

    UTexture2D* DefaultAlbedo =
        TextureAssetsByKey.FindRef(GetFirstPartyMaterialTextureAssetBindingKey(TEXT("american_south_fork"), TEXT("AlbedoAtlas")));
    UTexture2D* DefaultNormal =
        TextureAssetsByKey.FindRef(GetFirstPartyMaterialTextureAssetBindingKey(TEXT("american_south_fork"), TEXT("NormalAtlas")));
    UTexture2D* DefaultPacked = TextureAssetsByKey.FindRef(
        GetFirstPartyMaterialTextureAssetBindingKey(TEXT("american_south_fork"), TEXT("AORoughnessHeightAtlas")));
    UTexture2D* DefaultSourceMacroAlbedo = TextureAssetsByKey.FindRef(
        GetFirstPartyMaterialTextureAssetBindingKey(TEXT("american_south_fork"), TEXT("SourceConditionedMacroAlbedo")));
    UTexture2D* DefaultSourceMaterialZones = TextureAssetsByKey.FindRef(
        GetFirstPartyMaterialTextureAssetBindingKey(TEXT("american_south_fork"), TEXT("SourceConditionedMaterialZones")));
    UTexture2D* DefaultSourcePacked = TextureAssetsByKey.FindRef(
        GetFirstPartyMaterialTextureAssetBindingKey(TEXT("american_south_fork"), TEXT("SourceConditionedAORoughnessHeight")));
    UTexture2D* DefaultSourceNormalDetail = TextureAssetsByKey.FindRef(
        GetFirstPartyMaterialTextureAssetBindingKey(TEXT("american_south_fork"), TEXT("SourceConditionedNormalDetail")));
    UTexture2D* DefaultTerrainDetailAlbedo = TextureAssetsByKey.FindRef(
        GetFirstPartyMaterialTextureAssetBindingKey(TEXT("american_south_fork"), TEXT("TerrainDetailAlbedo")));
    UTexture2D* DefaultTerrainDetailNormal = TextureAssetsByKey.FindRef(
        GetFirstPartyMaterialTextureAssetBindingKey(TEXT("american_south_fork"), TEXT("TerrainDetailNormal")));
    UTexture2D* DefaultTerrainDetailPacked = TextureAssetsByKey.FindRef(
        GetFirstPartyMaterialTextureAssetBindingKey(TEXT("american_south_fork"), TEXT("TerrainDetailAORoughnessHeight")));

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->SetShadingModel(MSM_DefaultLit);
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = true;

    auto AddExpression = [Material](auto* Expression, int32 EditorX, int32 EditorY)
    {
        Expression->MaterialExpressionEditorX = EditorX;
        Expression->MaterialExpressionEditorY = EditorY;
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };

    UMaterialExpressionTextureCoordinate* TexCoord =
        AddExpression(NewObject<UMaterialExpressionTextureCoordinate>(Material), -1120, -120);

    UMaterialExpressionVectorParameter* AtlasTileOriginParameter =
        AddExpression(NewObject<UMaterialExpressionVectorParameter>(Material), -1120, 40);
    AtlasTileOriginParameter->ParameterName = TEXT("AtlasTileOrigin");
    AtlasTileOriginParameter->DefaultValue = FLinearColor(0.0f, 0.0f, 0.0f, 0.0f);

    UMaterialExpressionVectorParameter* AtlasTileScaleParameter =
        AddExpression(NewObject<UMaterialExpressionVectorParameter>(Material), -1120, 180);
    AtlasTileScaleParameter->ParameterName = TEXT("AtlasTileScale");
    AtlasTileScaleParameter->DefaultValue = FLinearColor(1.0f / 3.0f, 1.0f / 2.0f, 0.0f, 0.0f);

    UMaterialExpressionComponentMask* AtlasOrigin =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), -880, 40);
    AtlasOrigin->Input.Expression = AtlasTileOriginParameter;
    AtlasOrigin->R = 1;
    AtlasOrigin->G = 1;

    UMaterialExpressionComponentMask* AtlasScale =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), -880, 180);
    AtlasScale->Input.Expression = AtlasTileScaleParameter;
    AtlasScale->R = 1;
    AtlasScale->G = 1;

    UMaterialExpressionMultiply* ScaledUv = AddExpression(NewObject<UMaterialExpressionMultiply>(Material), -640, -40);
    ScaledUv->A.Expression = TexCoord;
    ScaledUv->B.Expression = AtlasScale;

    UMaterialExpressionAdd* AtlasUv = AddExpression(NewObject<UMaterialExpressionAdd>(Material), -420, -40);
    AtlasUv->A.Expression = ScaledUv;
    AtlasUv->B.Expression = AtlasOrigin;

    UMaterialExpressionTextureSampleParameter2D* AlbedoSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -180, -220);
    AlbedoSample->ParameterName = TEXT("AlbedoAtlas");
    AlbedoSample->Texture = DefaultAlbedo;
    AlbedoSample->SamplerType = SAMPLERTYPE_Color;
    AlbedoSample->Coordinates.Expression = AtlasUv;
    AlbedoSample->Group = TEXT("FirstPartyAtlas");
    AlbedoSample->SortPriority = 10;

    UMaterialExpressionTextureSampleParameter2D* NormalSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -180, 20);
    NormalSample->ParameterName = TEXT("NormalAtlas");
    NormalSample->Texture = DefaultNormal;
    NormalSample->SamplerType = SAMPLERTYPE_Normal;
    NormalSample->Coordinates.Expression = AtlasUv;
    NormalSample->Group = TEXT("FirstPartyAtlas");
    NormalSample->SortPriority = 20;

    UMaterialExpressionConstant3Vector* FlatNormal =
        AddExpression(NewObject<UMaterialExpressionConstant3Vector>(Material), 120, -20);
    FlatNormal->Constant = FLinearColor(0.0f, 0.0f, 1.0f);

    UMaterialExpressionScalarParameter* NormalIntensity =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 120, 100);
    NormalIntensity->ParameterName = TEXT("NormalIntensity");
    NormalIntensity->DefaultValue = 0.30f;
    NormalIntensity->Group = TEXT("FirstPartyAtlas");
    NormalIntensity->SortPriority = 45;

    UMaterialExpressionLinearInterpolate* ReviewNormal =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 360, 40);
    ReviewNormal->A.Expression = FlatNormal;
    ReviewNormal->B.Expression = NormalSample;
    ReviewNormal->Alpha.Expression = NormalIntensity;

    UMaterialExpressionTextureSampleParameter2D* PackedSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -180, 260);
    PackedSample->ParameterName = TEXT("AORoughnessHeightAtlas");
    PackedSample->Texture = DefaultPacked;
    PackedSample->SamplerType = SAMPLERTYPE_Masks;
    PackedSample->Coordinates.Expression = AtlasUv;
    PackedSample->Group = TEXT("FirstPartyAtlas");
    PackedSample->SortPriority = 30;

    UMaterialExpressionTextureSampleParameter2D* SourceMacroAlbedoSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -180, -40);
    SourceMacroAlbedoSample->ParameterName = TEXT("SourceConditionedMacroAlbedo");
    SourceMacroAlbedoSample->Texture = DefaultSourceMacroAlbedo;
    SourceMacroAlbedoSample->SamplerType = SAMPLERTYPE_Color;
    SourceMacroAlbedoSample->Coordinates.Expression = TexCoord;
    SourceMacroAlbedoSample->Group = TEXT("SourceConditionedMaps");
    SourceMacroAlbedoSample->SortPriority = 70;

    UMaterialExpressionTextureSampleParameter2D* SourceMaterialZonesSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -180, 920);
    SourceMaterialZonesSample->ParameterName = TEXT("SourceConditionedMaterialZones");
    SourceMaterialZonesSample->Texture = DefaultSourceMaterialZones;
    SourceMaterialZonesSample->SamplerType = SAMPLERTYPE_Masks;
    SourceMaterialZonesSample->Coordinates.Expression = TexCoord;
    SourceMaterialZonesSample->Group = TEXT("SourceConditionedMaps");
    SourceMaterialZonesSample->SortPriority = 80;

    UMaterialExpressionTextureSampleParameter2D* SourcePackedSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -180, 1160);
    SourcePackedSample->ParameterName = TEXT("SourceConditionedAORoughnessHeight");
    SourcePackedSample->Texture = DefaultSourcePacked;
    SourcePackedSample->SamplerType = SAMPLERTYPE_Masks;
    SourcePackedSample->Coordinates.Expression = TexCoord;
    SourcePackedSample->Group = TEXT("SourceConditionedMaps");
    SourcePackedSample->SortPriority = 90;

    UMaterialExpressionTextureSampleParameter2D* SourceNormalDetailSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -180, 1500);
    SourceNormalDetailSample->ParameterName = TEXT("SourceConditionedNormalDetail");
    SourceNormalDetailSample->Texture = DefaultSourceNormalDetail;
    SourceNormalDetailSample->SamplerType = SAMPLERTYPE_Normal;
    SourceNormalDetailSample->Coordinates.Expression = TexCoord;
    SourceNormalDetailSample->Group = TEXT("SourceConditionedMaps");
    SourceNormalDetailSample->SortPriority = 95;

    UMaterialExpressionVectorParameter* TerrainDetailUvScaleParameter =
        AddExpression(NewObject<UMaterialExpressionVectorParameter>(Material), -1120, 1780);
    TerrainDetailUvScaleParameter->ParameterName = TEXT("TerrainDetailUvScale");
    TerrainDetailUvScaleParameter->DefaultValue = FLinearColor(8.0f, 8.0f, 0.0f, 0.0f);
    TerrainDetailUvScaleParameter->Group = TEXT("FirstPartyProductionDetail");
    TerrainDetailUvScaleParameter->SortPriority = 130;

    UMaterialExpressionVectorParameter* TerrainDetailUvOffsetParameter =
        AddExpression(NewObject<UMaterialExpressionVectorParameter>(Material), -1120, 1920);
    TerrainDetailUvOffsetParameter->ParameterName = TEXT("TerrainDetailUvOffset");
    TerrainDetailUvOffsetParameter->DefaultValue = FLinearColor(0.17f, 0.31f, 0.0f, 0.0f);
    TerrainDetailUvOffsetParameter->Group = TEXT("FirstPartyProductionDetail");
    TerrainDetailUvOffsetParameter->SortPriority = 135;

    UMaterialExpressionComponentMask* TerrainDetailUvScale =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), -880, 1740);
    TerrainDetailUvScale->Input.Expression = TerrainDetailUvScaleParameter;
    TerrainDetailUvScale->R = 1;
    TerrainDetailUvScale->G = 1;

    UMaterialExpressionComponentMask* TerrainDetailUvOffset =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), -880, 1880);
    TerrainDetailUvOffset->Input.Expression = TerrainDetailUvOffsetParameter;
    TerrainDetailUvOffset->R = 1;
    TerrainDetailUvOffset->G = 1;

    UMaterialExpressionMultiply* TerrainDetailScaledUv =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), -640, 1740);
    TerrainDetailScaledUv->A.Expression = TexCoord;
    TerrainDetailScaledUv->B.Expression = TerrainDetailUvScale;

    UMaterialExpressionAdd* TerrainDetailUv =
        AddExpression(NewObject<UMaterialExpressionAdd>(Material), -420, 1780);
    TerrainDetailUv->A.Expression = TerrainDetailScaledUv;
    TerrainDetailUv->B.Expression = TerrainDetailUvOffset;

    UMaterialExpressionTextureSampleParameter2D* TerrainDetailAlbedoSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -180, 1760);
    TerrainDetailAlbedoSample->ParameterName = TEXT("TerrainDetailAlbedo");
    TerrainDetailAlbedoSample->Texture = DefaultTerrainDetailAlbedo;
    TerrainDetailAlbedoSample->SamplerType = SAMPLERTYPE_Color;
    TerrainDetailAlbedoSample->Coordinates.Expression = TerrainDetailUv;
    TerrainDetailAlbedoSample->Group = TEXT("FirstPartyProductionDetail");
    TerrainDetailAlbedoSample->SortPriority = 140;

    UMaterialExpressionTextureSampleParameter2D* TerrainDetailNormalSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -180, 1980);
    TerrainDetailNormalSample->ParameterName = TEXT("TerrainDetailNormal");
    TerrainDetailNormalSample->Texture = DefaultTerrainDetailNormal;
    TerrainDetailNormalSample->SamplerType = SAMPLERTYPE_Normal;
    TerrainDetailNormalSample->Coordinates.Expression = TerrainDetailUv;
    TerrainDetailNormalSample->Group = TEXT("FirstPartyProductionDetail");
    TerrainDetailNormalSample->SortPriority = 150;

    UMaterialExpressionTextureSampleParameter2D* TerrainDetailPackedSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -180, 2200);
    TerrainDetailPackedSample->ParameterName = TEXT("TerrainDetailAORoughnessHeight");
    TerrainDetailPackedSample->Texture = DefaultTerrainDetailPacked;
    TerrainDetailPackedSample->SamplerType = SAMPLERTYPE_Masks;
    TerrainDetailPackedSample->Coordinates.Expression = TerrainDetailUv;
    TerrainDetailPackedSample->Group = TEXT("FirstPartyProductionDetail");
    TerrainDetailPackedSample->SortPriority = 160;

    UMaterialExpressionVectorParameter* SourceZoneWeights =
        AddExpression(NewObject<UMaterialExpressionVectorParameter>(Material), -180, 700);
    SourceZoneWeights->ParameterName = TEXT("SourceConditionedZoneWeights");
    SourceZoneWeights->DefaultValue = FLinearColor(1.0f, 0.0f, 0.0f, 0.0f);
    SourceZoneWeights->Group = TEXT("SourceConditionedMaps");
    SourceZoneWeights->SortPriority = 100;

    UMaterialExpressionComponentMask* SourceZoneTerrain =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 840);
    SourceZoneTerrain->Input.Expression = SourceMaterialZonesSample;
    SourceZoneTerrain->R = 1;

    UMaterialExpressionComponentMask* SourceZoneVegetation =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 940);
    SourceZoneVegetation->Input.Expression = SourceMaterialZonesSample;
    SourceZoneVegetation->G = 1;

    UMaterialExpressionComponentMask* SourceZoneWater =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 1040);
    SourceZoneWater->Input.Expression = SourceMaterialZonesSample;
    SourceZoneWater->B = 1;

    UMaterialExpressionComponentMask* SourceZoneWeightTerrain =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 680);
    SourceZoneWeightTerrain->Input.Expression = SourceZoneWeights;
    SourceZoneWeightTerrain->R = 1;

    UMaterialExpressionComponentMask* SourceZoneWeightVegetation =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 760);
    SourceZoneWeightVegetation->Input.Expression = SourceZoneWeights;
    SourceZoneWeightVegetation->G = 1;

    UMaterialExpressionComponentMask* SourceZoneWeightWater =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 1120);
    SourceZoneWeightWater->Input.Expression = SourceZoneWeights;
    SourceZoneWeightWater->B = 1;

    UMaterialExpressionMultiply* SourceTerrainZoneWeighted =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 360, 820);
    SourceTerrainZoneWeighted->A.Expression = SourceZoneTerrain;
    SourceTerrainZoneWeighted->B.Expression = SourceZoneWeightTerrain;

    UMaterialExpressionMultiply* SourceVegetationZoneWeighted =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 360, 940);
    SourceVegetationZoneWeighted->A.Expression = SourceZoneVegetation;
    SourceVegetationZoneWeighted->B.Expression = SourceZoneWeightVegetation;

    UMaterialExpressionMultiply* SourceWaterZoneWeighted =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 360, 1060);
    SourceWaterZoneWeighted->A.Expression = SourceZoneWater;
    SourceWaterZoneWeighted->B.Expression = SourceZoneWeightWater;

    UMaterialExpressionAdd* SourceTerrainVegetationZones =
        AddExpression(NewObject<UMaterialExpressionAdd>(Material), 560, 900);
    SourceTerrainVegetationZones->A.Expression = SourceTerrainZoneWeighted;
    SourceTerrainVegetationZones->B.Expression = SourceVegetationZoneWeighted;

    UMaterialExpressionAdd* SourceWeightedZones =
        AddExpression(NewObject<UMaterialExpressionAdd>(Material), 760, 980);
    SourceWeightedZones->A.Expression = SourceTerrainVegetationZones;
    SourceWeightedZones->B.Expression = SourceWaterZoneWeighted;

    UMaterialExpressionSaturate* SourceZoneMask =
        AddExpression(NewObject<UMaterialExpressionSaturate>(Material), 960, 980);
    SourceZoneMask->Input.Expression = SourceWeightedZones;

    UMaterialExpressionScalarParameter* SourceConditionedMacroAlbedoWeight =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 120, -220);
    SourceConditionedMacroAlbedoWeight->ParameterName = TEXT("SourceConditionedMacroAlbedoWeight");
    SourceConditionedMacroAlbedoWeight->DefaultValue = 0.12f;
    SourceConditionedMacroAlbedoWeight->Group = TEXT("SourceConditionedMaps");
    SourceConditionedMacroAlbedoWeight->SortPriority = 110;

    UMaterialExpressionMultiply* SourceConditionedMacroAlbedoAlpha =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 360, -220);
    SourceConditionedMacroAlbedoAlpha->A.Expression = SourceConditionedMacroAlbedoWeight;
    SourceConditionedMacroAlbedoAlpha->B.Expression = SourceZoneMask;

    UMaterialExpressionScalarParameter* SourceConditionedSurfaceResponseWeight =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 960, 760);
    SourceConditionedSurfaceResponseWeight->ParameterName = TEXT("SourceConditionedSurfaceResponseWeight");
    SourceConditionedSurfaceResponseWeight->DefaultValue = 0.10f;
    SourceConditionedSurfaceResponseWeight->Group = TEXT("SourceConditionedMaps");
    SourceConditionedSurfaceResponseWeight->SortPriority = 120;

    UMaterialExpressionMultiply* SourceConditionedSurfaceResponseAlpha =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 1160, 900);
    SourceConditionedSurfaceResponseAlpha->A.Expression = SourceConditionedSurfaceResponseWeight;
    SourceConditionedSurfaceResponseAlpha->B.Expression = SourceZoneMask;

    UMaterialExpressionScalarParameter* SourceConditionedNormalDetailWeight =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 960, 620);
    SourceConditionedNormalDetailWeight->ParameterName = TEXT("SourceConditionedNormalDetailWeight");
    SourceConditionedNormalDetailWeight->DefaultValue = 0.08f;
    SourceConditionedNormalDetailWeight->Group = TEXT("SourceConditionedMaps");
    SourceConditionedNormalDetailWeight->SortPriority = 125;

    UMaterialExpressionMultiply* SourceConditionedNormalDetailAlpha =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 1160, 660);
    SourceConditionedNormalDetailAlpha->A.Expression = SourceConditionedNormalDetailWeight;
    SourceConditionedNormalDetailAlpha->B.Expression = SourceZoneMask;

    UMaterialExpressionVertexColor* VertexColor =
        AddExpression(NewObject<UMaterialExpressionVertexColor>(Material), -180, -560);

    UMaterialExpressionVectorParameter* PreviewColor =
        AddExpression(NewObject<UMaterialExpressionVectorParameter>(Material), -180, -420);
    PreviewColor->ParameterName = TEXT("PreviewColor");
    PreviewColor->DefaultValue = FLinearColor(0.30f, 0.31f, 0.27f);
    PreviewColor->Group = TEXT("FirstPartyAtlas");
    PreviewColor->SortPriority = 35;

    UMaterialExpressionScalarParameter* VertexColorWeight =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -180, -300);
    VertexColorWeight->ParameterName = TEXT("VertexColorWeight");
    VertexColorWeight->DefaultValue = 1.0f;
    VertexColorWeight->Group = TEXT("FirstPartyAtlas");
    VertexColorWeight->SortPriority = 38;

    UMaterialExpressionLinearInterpolate* ReviewSurfaceBaseColor =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 120, -500);
    ReviewSurfaceBaseColor->A.Expression = PreviewColor;
    ReviewSurfaceBaseColor->B.Expression = VertexColor;
    ReviewSurfaceBaseColor->Alpha.Expression = VertexColorWeight;

    UMaterialExpressionScalarParameter* AtlasBlendWeight =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -180, -360);
    AtlasBlendWeight->ParameterName = TEXT("AtlasBlendWeight");
    AtlasBlendWeight->DefaultValue = 0.16f;
    AtlasBlendWeight->Group = TEXT("FirstPartyAtlas");
    AtlasBlendWeight->SortPriority = 40;

    UMaterialExpressionLinearInterpolate* ReviewBaseColor =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 120, -320);
    ReviewBaseColor->A.Expression = ReviewSurfaceBaseColor;
    ReviewBaseColor->B.Expression = AlbedoSample;
    ReviewBaseColor->Alpha.Expression = AtlasBlendWeight;

    UMaterialExpressionLinearInterpolate* SourceConditionedBaseColor =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 560, -260);
    SourceConditionedBaseColor->A.Expression = ReviewBaseColor;
    SourceConditionedBaseColor->B.Expression = SourceMacroAlbedoSample;
    SourceConditionedBaseColor->Alpha.Expression = SourceConditionedMacroAlbedoAlpha;

    UMaterialExpressionScalarParameter* TerrainDetailAlbedoWeight =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 120, 1760);
    TerrainDetailAlbedoWeight->ParameterName = TEXT("TerrainDetailAlbedoWeight");
    TerrainDetailAlbedoWeight->DefaultValue = 0.0f;
    TerrainDetailAlbedoWeight->Group = TEXT("FirstPartyProductionDetail");
    TerrainDetailAlbedoWeight->SortPriority = 170;

    UMaterialExpressionLinearInterpolate* ProductionDetailBaseColor =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 560, -120);
    ProductionDetailBaseColor->A.Expression = SourceConditionedBaseColor;
    ProductionDetailBaseColor->B.Expression = TerrainDetailAlbedoSample;
    ProductionDetailBaseColor->Alpha.Expression = TerrainDetailAlbedoWeight;

    UMaterialExpressionConstant* FirstPartyAtlasReviewEmissiveFillScale =
        AddExpression(NewObject<UMaterialExpressionConstant>(Material), 120, -80);
    FirstPartyAtlasReviewEmissiveFillScale->R = 0.42f;

    UMaterialExpressionMultiply* EmissiveColor =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 360, -160);
    EmissiveColor->A.Expression = ProductionDetailBaseColor;
    EmissiveColor->B.Expression = FirstPartyAtlasReviewEmissiveFillScale;

    UMaterialExpressionComponentMask* AmbientOcclusionMask =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 180);
    AmbientOcclusionMask->Input.Expression = PackedSample;
    AmbientOcclusionMask->R = 1;

    UMaterialExpressionComponentMask* RoughnessMask =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 320);
    RoughnessMask->Input.Expression = PackedSample;
    RoughnessMask->G = 1;

    UMaterialExpressionScalarParameter* RoughnessScale =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 120, 460);
    RoughnessScale->ParameterName = TEXT("RoughnessScale");
    RoughnessScale->DefaultValue = 0.75f;
    RoughnessScale->Group = TEXT("FirstPartyAtlas");
    RoughnessScale->SortPriority = 50;

    UMaterialExpressionMultiply* RoughnessScaled =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 360, 360);
    RoughnessScaled->A.Expression = RoughnessMask;
    RoughnessScaled->B.Expression = RoughnessScale;

    UMaterialExpressionScalarParameter* RoughnessFloor =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 360, 500);
    RoughnessFloor->ParameterName = TEXT("RoughnessFloor");
    RoughnessFloor->DefaultValue = 0.62f;
    RoughnessFloor->Group = TEXT("FirstPartyAtlas");
    RoughnessFloor->SortPriority = 55;

    UMaterialExpressionAdd* RoughnessWithFloor =
        AddExpression(NewObject<UMaterialExpressionAdd>(Material), 560, 420);
    RoughnessWithFloor->A.Expression = RoughnessScaled;
    RoughnessWithFloor->B.Expression = RoughnessFloor;

    UMaterialExpressionSaturate* RoughnessSaturated =
        AddExpression(NewObject<UMaterialExpressionSaturate>(Material), 760, 420);
    RoughnessSaturated->Input.Expression = RoughnessWithFloor;

    UMaterialExpressionComponentMask* SourceAmbientOcclusionMask =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 1220);
    SourceAmbientOcclusionMask->Input.Expression = SourcePackedSample;
    SourceAmbientOcclusionMask->R = 1;

    UMaterialExpressionComponentMask* SourceRoughnessMask =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 1320);
    SourceRoughnessMask->Input.Expression = SourcePackedSample;
    SourceRoughnessMask->G = 1;

    UMaterialExpressionLinearInterpolate* SourceConditionedAmbientOcclusion =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 1160, 1180);
    SourceConditionedAmbientOcclusion->A.Expression = AmbientOcclusionMask;
    SourceConditionedAmbientOcclusion->B.Expression = SourceAmbientOcclusionMask;
    SourceConditionedAmbientOcclusion->Alpha.Expression = SourceConditionedSurfaceResponseAlpha;

    UMaterialExpressionLinearInterpolate* SourceConditionedRoughness =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 1160, 1320);
    SourceConditionedRoughness->A.Expression = RoughnessSaturated;
    SourceConditionedRoughness->B.Expression = SourceRoughnessMask;
    SourceConditionedRoughness->Alpha.Expression = SourceConditionedSurfaceResponseAlpha;

    UMaterialExpressionComponentMask* HeightMask =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 620);
    HeightMask->Input.Expression = PackedSample;
    HeightMask->B = 1;

    UMaterialExpressionScalarParameter* HeightScale =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 120, 760);
    HeightScale->ParameterName = TEXT("HeightScale");
    HeightScale->DefaultValue = 0.08f;
    HeightScale->Group = TEXT("FirstPartyAtlas");
    HeightScale->SortPriority = 60;

    UMaterialExpressionMultiply* HeightOffset =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 360, 680);
    HeightOffset->A.Expression = HeightMask;
    HeightOffset->B.Expression = HeightScale;

    UMaterialExpressionComponentMask* SourceHeightMask =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 1420);
    SourceHeightMask->Input.Expression = SourcePackedSample;
    SourceHeightMask->B = 1;

    UMaterialExpressionMultiply* SourceHeightOffset =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 360, 1420);
    SourceHeightOffset->A.Expression = SourceHeightMask;
    SourceHeightOffset->B.Expression = HeightScale;

    UMaterialExpressionLinearInterpolate* SourceConditionedHeightOffset =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 1160, 1440);
    SourceConditionedHeightOffset->A.Expression = HeightOffset;
    SourceConditionedHeightOffset->B.Expression = SourceHeightOffset;
    SourceConditionedHeightOffset->Alpha.Expression = SourceConditionedSurfaceResponseAlpha;

    UMaterialExpressionLinearInterpolate* SourceConditionedNormal =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 760, 80);
    SourceConditionedNormal->A.Expression = ReviewNormal;
    SourceConditionedNormal->B.Expression = SourceNormalDetailSample;
    SourceConditionedNormal->Alpha.Expression = SourceConditionedNormalDetailAlpha;

    UMaterialExpressionScalarParameter* TerrainDetailNormalWeight =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 120, 1980);
    TerrainDetailNormalWeight->ParameterName = TEXT("TerrainDetailNormalWeight");
    TerrainDetailNormalWeight->DefaultValue = 0.0f;
    TerrainDetailNormalWeight->Group = TEXT("FirstPartyProductionDetail");
    TerrainDetailNormalWeight->SortPriority = 180;

    UMaterialExpressionScalarParameter* TerrainDetailSurfaceResponseWeight =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), 120, 2440);
    TerrainDetailSurfaceResponseWeight->ParameterName = TEXT("TerrainDetailSurfaceResponseWeight");
    TerrainDetailSurfaceResponseWeight->DefaultValue = 0.0f;
    TerrainDetailSurfaceResponseWeight->Group = TEXT("FirstPartyProductionDetail");
    TerrainDetailSurfaceResponseWeight->SortPriority = 190;

    UMaterialExpressionComponentMask* TerrainDetailAmbientOcclusion =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 2180);
    TerrainDetailAmbientOcclusion->Input.Expression = TerrainDetailPackedSample;
    TerrainDetailAmbientOcclusion->R = 1;

    UMaterialExpressionComponentMask* TerrainDetailRoughness =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 2280);
    TerrainDetailRoughness->Input.Expression = TerrainDetailPackedSample;
    TerrainDetailRoughness->G = 1;

    UMaterialExpressionComponentMask* TerrainDetailHeight =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), 120, 2380);
    TerrainDetailHeight->Input.Expression = TerrainDetailPackedSample;
    TerrainDetailHeight->B = 1;

    UMaterialExpressionMultiply* TerrainDetailHeightOffset =
        AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 360, 2380);
    TerrainDetailHeightOffset->A.Expression = TerrainDetailHeight;
    TerrainDetailHeightOffset->B.Expression = HeightScale;

    UMaterialExpressionLinearInterpolate* ProductionDetailNormal =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 1460, 80);
    ProductionDetailNormal->A.Expression = SourceConditionedNormal;
    ProductionDetailNormal->B.Expression = TerrainDetailNormalSample;
    ProductionDetailNormal->Alpha.Expression = TerrainDetailNormalWeight;

    UMaterialExpressionLinearInterpolate* ProductionDetailAmbientOcclusion =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 1460, 1180);
    ProductionDetailAmbientOcclusion->A.Expression = SourceConditionedAmbientOcclusion;
    ProductionDetailAmbientOcclusion->B.Expression = TerrainDetailAmbientOcclusion;
    ProductionDetailAmbientOcclusion->Alpha.Expression = TerrainDetailSurfaceResponseWeight;

    UMaterialExpressionLinearInterpolate* ProductionDetailRoughness =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 1460, 1320);
    ProductionDetailRoughness->A.Expression = SourceConditionedRoughness;
    ProductionDetailRoughness->B.Expression = TerrainDetailRoughness;
    ProductionDetailRoughness->Alpha.Expression = TerrainDetailSurfaceResponseWeight;

    UMaterialExpressionLinearInterpolate* ProductionDetailHeightOffset =
        AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 1460, 1440);
    ProductionDetailHeightOffset->A.Expression = SourceConditionedHeightOffset;
    ProductionDetailHeightOffset->B.Expression = TerrainDetailHeightOffset;
    ProductionDetailHeightOffset->Alpha.Expression = TerrainDetailSurfaceResponseWeight;

    UMaterialExpressionConstant* Specular = AddExpression(NewObject<UMaterialExpressionConstant>(Material), 560, 520);
    Specular->R = 0.0f;

    if (UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData())
    {
        ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, ProductionDetailBaseColor);
        ConnectPreviewMaterialColorInput(EditorOnlyData->EmissiveColor, EmissiveColor);
        ConnectPreviewMaterialVectorInput(EditorOnlyData->Normal, ProductionDetailNormal);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->AmbientOcclusion, ProductionDetailAmbientOcclusion);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, ProductionDetailRoughness);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->PixelDepthOffset, ProductionDetailHeightOffset);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);
    }

    Material->PostEditChange();
    Package->MarkPackageDirty();

    const FString Filename =
        FPackageName::LongPackageNameToFilename(MaterialPackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);

    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    const bool bSaved = UPackage::SavePackage(Package, Material, *Filename, SaveArgs);
    OutSummary += FString::Printf(
        TEXT("%s first-party atlas sampler review material %s -> %s\n"),
        bSaved ? TEXT("Saved") : TEXT("Failed"),
        MaterialObjectPath,
        *Filename);
    return bSaved ? Material : nullptr;
}

struct FRaftSimFirstPartyMaterialInstanceCandidateSpec
{
    FString RiverId;
    FString RiverAssetName;
    FString RecipeId;
    FString RecipeAssetName;
    FString ParentMaterialObjectPath;
    int32 AtlasTileIndex = 0;
    float AtlasBlendWeight = 0.25f;
    float NormalIntensity = 0.15f;
    float RoughnessScale = 0.75f;
    float HeightScale = 0.08f;
    FLinearColor PreviewColor = FLinearColor(0.30f, 0.31f, 0.27f);
    float VertexColorWeight = 1.0f;
    float RoughnessFloor = 0.62f;
    float EmissiveFillScale = 0.42f;
    float SpecularLevel = 0.0f;
    FLinearColor SourceConditionedZoneWeights = FLinearColor(1.0f, 0.0f, 0.0f, 0.0f);
    float SourceConditionedMacroAlbedoWeight = 0.0f;
    float SourceConditionedSurfaceResponseWeight = 0.0f;
    float SourceConditionedNormalDetailWeight = 0.0f;
    FLinearColor TerrainDetailUvScaleOffset = FLinearColor(8.0f, 8.0f, 0.17f, 0.31f);
    float TerrainDetailAlbedoWeight = 0.0f;
    float TerrainDetailNormalWeight = 0.0f;
    float TerrainDetailSurfaceResponseWeight = 0.0f;

    FString GetMaterialInstancePath() const
    {
        return FString::Printf(
            TEXT("/Game/RaftSim/Materials/MaterialInstances/MI_RaftSim_%s_%s_AtlasCandidate"),
            *RiverAssetName,
            *RecipeAssetName);
    }
};

TArray<FRaftSimFirstPartyMaterialInstanceCandidateSpec> GetFirstPartyMaterialInstanceCandidateSpecs()
{
    struct FRecipeSpec
    {
        const TCHAR* RecipeId;
        const TCHAR* RecipeAssetName;
        const TCHAR* ParentMaterialObjectPath;
        int32 AtlasTileIndex;
        float AtlasBlendWeight;
        float NormalIntensity;
        float RoughnessScale;
        float HeightScale;
        FLinearColor PreviewColor;
        float VertexColorWeight;
        float RoughnessFloor;
        float EmissiveFillScale;
        float SpecularLevel;
        FLinearColor SourceConditionedZoneWeights;
        float SourceConditionedMacroAlbedoWeight;
        float SourceConditionedSurfaceResponseWeight;
        float SourceConditionedNormalDetailWeight;
    };

    const FRecipeSpec RecipeSpecs[] = {
        {
            TEXT("terrain_bank_layered_material"),
            TEXT("TerrainBank"),
            TEXT("/Game/RaftSim/Materials/M_RaftSim_AtlasSampleReview.M_RaftSim_AtlasSampleReview"),
            0,
            0.16f,
            0.22f,
            0.92f,
            0.08f,
            FLinearColor(0.34f, 0.32f, 0.24f),
            1.0f,
            0.72f,
            0.42f,
            0.0f,
            FLinearColor(1.0f, 0.0f, 0.0f, 0.0f),
            0.28f,
            0.22f,
            0.16f,
        },
        {
            TEXT("wet_boulder_contact_material_set"),
            TEXT("WetBoulderContact"),
            TEXT("/Game/RaftSim/Materials/M_RaftSim_AtlasSampleReview.M_RaftSim_AtlasSampleReview"),
            1,
            0.18f,
            0.30f,
            0.64f,
            0.10f,
            FLinearColor(0.24f, 0.23f, 0.20f),
            1.0f,
            0.66f,
            0.42f,
            0.0f,
            FLinearColor(1.0f, 0.0f, 0.0f, 0.0f),
            0.08f,
            0.10f,
            0.12f,
        },
        {
            TEXT("biome_foliage_groundcover_materials"),
            TEXT("BiomeFoliageGroundcover"),
            TEXT("/Game/RaftSim/Materials/M_RaftSim_AtlasSampleReview.M_RaftSim_AtlasSampleReview"),
            2,
            0.14f,
            0.18f,
            0.78f,
            0.06f,
            FLinearColor(0.055f, 0.15f, 0.055f),
            0.72f,
            0.68f,
            0.42f,
            0.0f,
            FLinearColor(0.0f, 1.0f, 0.0f, 0.0f),
            0.20f,
            0.12f,
            0.08f,
        },
        {
            TEXT("flow_dependent_water_surface_material"),
            TEXT("FlowDependentWaterSurface"),
            TEXT("/Game/RaftSim/Materials/M_RaftSim_VertexColorWaterPreview.M_RaftSim_VertexColorWaterPreview"),
            3,
            0.0f,
            0.32f,
            0.18f,
            0.0f,
            FLinearColor(0.095f, 0.300f, 0.170f),
            1.0f,
            0.28f,
            0.26f,
            0.22f,
            FLinearColor(0.0f, 0.0f, 1.0f, 0.0f),
            0.0f,
            0.0f,
            0.0f,
        },
        {
            TEXT("foam_spray_mist_atmosphere_materials"),
            TEXT("FoamSprayMistAtmosphere"),
            TEXT("/Game/RaftSim/Materials/M_RaftSim_AtlasSampleReview.M_RaftSim_AtlasSampleReview"),
            4,
            0.10f,
            0.06f,
            0.40f,
            0.015f,
            FLinearColor(0.78f, 0.84f, 0.75f),
            0.0f,
            0.74f,
            0.42f,
            0.0f,
            FLinearColor(0.0f, 0.0f, 1.0f, 0.0f),
            0.04f,
            0.04f,
            0.01f,
        },
        {
            TEXT("raft_foreground_review_materials"),
            TEXT("RaftForegroundReview"),
            TEXT("/Game/RaftSim/Materials/M_RaftSim_AtlasSampleReview.M_RaftSim_AtlasSampleReview"),
            5,
            0.16f,
            0.10f,
            0.56f,
            0.035f,
            FLinearColor(0.680f, 0.220f, 0.080f),
            1.0f,
            0.70f,
            0.42f,
            0.0f,
            FLinearColor(0.0f, 0.0f, 0.0f, 0.0f),
            0.0f,
            0.0f,
            0.0f,
        },
    };

    struct FRiverSpec
    {
        const TCHAR* RiverId;
        const TCHAR* RiverAssetName;
    };

    const FRiverSpec RiverSpecs[] = {
        {TEXT("american_south_fork"), TEXT("AmericanSouthFork")},
        {TEXT("colorado_river"), TEXT("ColoradoRiver")},
        {TEXT("pacuare"), TEXT("Pacuare")},
    };

    TArray<FRaftSimFirstPartyMaterialInstanceCandidateSpec> Specs;
    for (const FRiverSpec& RiverSpec : RiverSpecs)
    {
        for (const FRecipeSpec& RecipeSpec : RecipeSpecs)
        {
            FRaftSimFirstPartyMaterialInstanceCandidateSpec Spec;
            Spec.RiverId = RiverSpec.RiverId;
            Spec.RiverAssetName = RiverSpec.RiverAssetName;
            Spec.RecipeId = RecipeSpec.RecipeId;
            Spec.RecipeAssetName = RecipeSpec.RecipeAssetName;
            Spec.ParentMaterialObjectPath = RecipeSpec.ParentMaterialObjectPath;
            Spec.AtlasTileIndex = RecipeSpec.AtlasTileIndex;
            Spec.AtlasBlendWeight = RecipeSpec.AtlasBlendWeight;
            Spec.NormalIntensity = RecipeSpec.NormalIntensity;
            Spec.RoughnessScale = RecipeSpec.RoughnessScale;
            Spec.HeightScale = RecipeSpec.HeightScale;
            Spec.PreviewColor = RecipeSpec.PreviewColor;
            Spec.VertexColorWeight = RecipeSpec.VertexColorWeight;
            Spec.RoughnessFloor = RecipeSpec.RoughnessFloor;
            Spec.EmissiveFillScale = RecipeSpec.EmissiveFillScale;
            Spec.SpecularLevel = RecipeSpec.SpecularLevel;
            Spec.SourceConditionedZoneWeights = RecipeSpec.SourceConditionedZoneWeights;
            Spec.SourceConditionedMacroAlbedoWeight = RecipeSpec.SourceConditionedMacroAlbedoWeight;
            Spec.SourceConditionedSurfaceResponseWeight = RecipeSpec.SourceConditionedSurfaceResponseWeight;
            Spec.SourceConditionedNormalDetailWeight = RecipeSpec.SourceConditionedNormalDetailWeight;
            if (FCString::Strcmp(RecipeSpec.RecipeId, TEXT("terrain_bank_layered_material")) == 0)
            {
                if (FCString::Strcmp(RiverSpec.RiverId, TEXT("colorado_river")) == 0)
                {
                    Spec.TerrainDetailUvScaleOffset = FLinearColor(4.5f, 4.5f, 0.41f, 0.13f);
                    Spec.TerrainDetailAlbedoWeight = 0.76f;
                    Spec.TerrainDetailNormalWeight = 0.22f;
                    Spec.TerrainDetailSurfaceResponseWeight = 0.24f;
                }
                else if (FCString::Strcmp(RiverSpec.RiverId, TEXT("pacuare")) == 0)
                {
                    Spec.TerrainDetailUvScaleOffset = FLinearColor(5.0f, 5.0f, 0.29f, 0.47f);
                    Spec.TerrainDetailAlbedoWeight = 0.74f;
                    Spec.TerrainDetailNormalWeight = 0.18f;
                    Spec.TerrainDetailSurfaceResponseWeight = 0.20f;
                }
                else
                {
                    Spec.TerrainDetailUvScaleOffset = FLinearColor(5.0f, 5.0f, 0.17f, 0.31f);
                    Spec.TerrainDetailAlbedoWeight = 0.74f;
                    Spec.TerrainDetailNormalWeight = 0.20f;
                    Spec.TerrainDetailSurfaceResponseWeight = 0.22f;
                }
            }
            else if (FCString::Strcmp(RecipeSpec.RecipeId, TEXT("flow_dependent_water_surface_material")) == 0)
            {
                const FRaftSimPreviewWaterMaterialResponse WaterResponse =
                    GetPreviewWaterMaterialResponse(RiverSpec.RiverId);
                Spec.RoughnessScale = WaterResponse.RoughnessScale;
                Spec.RoughnessFloor = WaterResponse.RoughnessFloor;
                Spec.EmissiveFillScale = WaterResponse.EmissiveFillScale;
                Spec.SpecularLevel = WaterResponse.SpecularLevel;
                Spec.NormalIntensity = WaterResponse.NormalIntensity;
            }
            Specs.Add(Spec);
        }
    }

    return Specs;
}

bool CreateOrUpdateFirstPartyMaterialInstanceCandidateAsset(
    const FRaftSimFirstPartyMaterialInstanceCandidateSpec& Spec,
    const TMap<FString, UTexture2D*>& TextureAssetsByKey,
    FString& OutSummary)
{
    UMaterialInterface* ParentMaterial = LoadPreviewMaterial(*Spec.ParentMaterialObjectPath);
    if (!ParentMaterial)
    {
        OutSummary += FString::Printf(
            TEXT("Missing parent material for candidate %s: %s\n"),
            *Spec.GetMaterialInstancePath(),
            *Spec.ParentMaterialObjectPath);
        return false;
    }

    const FString PackagePath = Spec.GetMaterialInstancePath();
    const FString AssetName = FPackageName::GetLongPackageAssetName(PackagePath);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, *AssetName);

    UPackage* Package = CreatePackage(*PackagePath);
    if (!Package)
    {
        OutSummary += FString::Printf(TEXT("Failed to create material instance package %s\n"), *PackagePath);
        return false;
    }

    UMaterialInstanceConstant* Instance =
        Cast<UMaterialInstanceConstant>(StaticLoadObject(UMaterialInstanceConstant::StaticClass(), nullptr, *ObjectPath));
    if (!Instance)
    {
        Instance = FindObject<UMaterialInstanceConstant>(Package, *AssetName);
    }
    if (!Instance)
    {
        Instance = NewObject<UMaterialInstanceConstant>(Package, *AssetName, RF_Public | RF_Standalone | RF_Transactional);
        FAssetRegistryModule::AssetCreated(Instance);
    }
    if (!Instance)
    {
        OutSummary += FString::Printf(TEXT("Failed to create material instance candidate %s\n"), *ObjectPath);
        return false;
    }

    const int32 AtlasColumn = Spec.AtlasTileIndex % 3;
    const int32 AtlasRow = Spec.AtlasTileIndex / 3;
    const FLinearColor AtlasTileOriginScale(
        static_cast<float>(AtlasColumn) / 3.0f,
        static_cast<float>(AtlasRow) / 2.0f,
        1.0f / 3.0f,
        1.0f / 2.0f);

    Instance->Modify();
    Instance->SetParentEditorOnly(ParentMaterial);
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("AtlasTileOriginScale")),
        AtlasTileOriginScale);
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("AtlasTileOrigin")),
        FLinearColor(AtlasTileOriginScale.R, AtlasTileOriginScale.G, 0.0f, 0.0f));
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("AtlasTileScale")),
        FLinearColor(AtlasTileOriginScale.B, AtlasTileOriginScale.A, 0.0f, 0.0f));
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("PreviewColor")),
        Spec.PreviewColor);
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("SourceConditionedZoneWeights")),
        Spec.SourceConditionedZoneWeights);
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("TerrainDetailUvScaleOffset")),
        Spec.TerrainDetailUvScaleOffset);
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("TerrainDetailUvScale")),
        FLinearColor(Spec.TerrainDetailUvScaleOffset.R, Spec.TerrainDetailUvScaleOffset.G, 0.0f, 0.0f));
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("TerrainDetailUvOffset")),
        FLinearColor(Spec.TerrainDetailUvScaleOffset.B, Spec.TerrainDetailUvScaleOffset.A, 0.0f, 0.0f));
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("AtlasTileIndex")),
        static_cast<float>(Spec.AtlasTileIndex));
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("AtlasBlendWeight")),
        Spec.AtlasBlendWeight);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("NormalIntensity")),
        Spec.NormalIntensity);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("RoughnessScale")),
        Spec.RoughnessScale);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("RoughnessFloor")),
        Spec.RoughnessFloor);
    if (Spec.RecipeId == TEXT("flow_dependent_water_surface_material"))
    {
        Instance->SetScalarParameterValueEditorOnly(
            FMaterialParameterInfo(TEXT("EmissiveFillScale")),
            Spec.EmissiveFillScale);
        Instance->SetScalarParameterValueEditorOnly(
            FMaterialParameterInfo(TEXT("SpecularLevel")),
            Spec.SpecularLevel);
    }
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("HeightScale")),
        Spec.HeightScale);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("VertexColorWeight")),
        Spec.VertexColorWeight);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("ReviewAssetOnlyNotLifelike")),
        1.0f);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("SourceConditionedMacroAlbedoWeight")),
        Spec.SourceConditionedMacroAlbedoWeight);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("SourceConditionedSurfaceResponseWeight")),
        Spec.SourceConditionedSurfaceResponseWeight);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("SourceConditionedNormalDetailWeight")),
        Spec.SourceConditionedNormalDetailWeight);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("TerrainDetailAlbedoWeight")),
        Spec.TerrainDetailAlbedoWeight);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("TerrainDetailNormalWeight")),
        Spec.TerrainDetailNormalWeight);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("TerrainDetailSurfaceResponseWeight")),
        Spec.TerrainDetailSurfaceResponseWeight);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("SourceConditionedMaterialAssignmentReviewOnlyNotLifelike")),
        1.0f);

    bool bAllTexturesBound = true;
    auto BindTextureParameter = [&TextureAssetsByKey, &Spec, &Instance, &OutSummary, &bAllTexturesBound](
                                    const TCHAR* ParameterName,
                                    const TCHAR* MapKey)
    {
        UTexture2D* const* Texture = TextureAssetsByKey.Find(GetFirstPartyMaterialTextureAssetBindingKey(Spec.RiverId, MapKey));
        if (!Texture || !*Texture)
        {
            OutSummary += FString::Printf(
                TEXT("Missing first-party material texture asset for %s parameter %s (%s/%s)\n"),
                *Spec.GetMaterialInstancePath(),
                ParameterName,
                *Spec.RiverId,
                MapKey);
            bAllTexturesBound = false;
            return;
        }

        Instance->SetTextureParameterValueEditorOnly(FMaterialParameterInfo(FName(ParameterName)), *Texture);
    };

    BindTextureParameter(TEXT("AlbedoAtlas"), TEXT("AlbedoAtlas"));
    BindTextureParameter(TEXT("NormalAtlas"), TEXT("NormalAtlas"));
    BindTextureParameter(TEXT("AORoughnessHeightAtlas"), TEXT("AORoughnessHeightAtlas"));
    BindTextureParameter(TEXT("SourceConditionedMacroAlbedo"), TEXT("SourceConditionedMacroAlbedo"));
    BindTextureParameter(TEXT("SourceConditionedMaterialZones"), TEXT("SourceConditionedMaterialZones"));
    BindTextureParameter(TEXT("SourceConditionedAORoughnessHeight"), TEXT("SourceConditionedAORoughnessHeight"));
    BindTextureParameter(TEXT("SourceConditionedNormalDetail"), TEXT("SourceConditionedNormalDetail"));
    BindTextureParameter(TEXT("TerrainDetailAlbedo"), TEXT("TerrainDetailAlbedo"));
    BindTextureParameter(TEXT("TerrainDetailNormal"), TEXT("TerrainDetailNormal"));
    BindTextureParameter(TEXT("TerrainDetailAORoughnessHeight"), TEXT("TerrainDetailAORoughnessHeight"));
    if (!bAllTexturesBound)
    {
        return false;
    }

    Instance->PostEditChange();
    Package->MarkPackageDirty();

    const FString Filename =
        FPackageName::LongPackageNameToFilename(PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);

    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;

    const bool bSaved = UPackage::SavePackage(Package, Instance, *Filename, SaveArgs);
    OutSummary += FString::Printf(
        TEXT("%s first-party material instance review asset %s (%s/%s) -> %s\n"),
        bSaved ? TEXT("Saved") : TEXT("Failed"),
        *ObjectPath,
        *Spec.RiverId,
        *Spec.RecipeId,
        *Filename);
    return bSaved;
}

bool CreateFirstPartyMaterialInstanceCandidateAssets(FString& OutSummary)
{
    bool bAllSaved = true;
    TMap<FString, UTexture2D*> TextureAssetsByKey;
    LoadOrCreatePreviewColorMaterial();
    LoadOrCreatePreviewTerrainVertexColorMaterial();
    LoadOrCreatePreviewTranslucentColorMaterial();
    LoadOrCreatePreviewWaterVertexColorMaterial();
    bAllSaved &= CreateFirstPartyMaterialTextureAtlasAssets(TextureAssetsByKey, OutSummary);
    bAllSaved &= CreateSourceConditionedMaterialTextureAssets(TextureAssetsByKey, OutSummary);
    bAllSaved &= CreateProductionDetailMaterialTextureAssets(TextureAssetsByKey, OutSummary);
    bAllSaved &= LoadOrCreateFirstPartyAtlasSampleReviewMaterial(TextureAssetsByKey, OutSummary) != nullptr;

    for (const FRaftSimFirstPartyMaterialInstanceCandidateSpec& Spec : GetFirstPartyMaterialInstanceCandidateSpecs())
    {
        bAllSaved &= CreateOrUpdateFirstPartyMaterialInstanceCandidateAsset(Spec, TextureAssetsByKey, OutSummary);
    }

    return bAllSaved;
}

FString GetFirstPartyMaterialRiverAssetName(const FString& RiverId)
{
    if (RiverId == TEXT("american_south_fork"))
    {
        return TEXT("AmericanSouthFork");
    }
    if (RiverId == TEXT("colorado_river"))
    {
        return TEXT("ColoradoRiver");
    }
    if (RiverId == TEXT("pacuare"))
    {
        return TEXT("Pacuare");
    }

    return FString();
}

UMaterialInterface* LoadFirstPartyMaterialInstanceCandidate(const FString& RiverId, const TCHAR* RecipeAssetName)
{
    const FString RiverAssetName = GetFirstPartyMaterialRiverAssetName(RiverId);
    if (RiverAssetName.IsEmpty())
    {
        return nullptr;
    }

    const FString MaterialPath = FString::Printf(
        TEXT("/Game/RaftSim/Materials/MaterialInstances/MI_RaftSim_%s_%s_AtlasCandidate.MI_RaftSim_%s_%s_AtlasCandidate"),
        *RiverAssetName,
        RecipeAssetName,
        *RiverAssetName,
        RecipeAssetName);
    return LoadPreviewMaterial(*MaterialPath);
}

struct FRaftSimFirstPartyMaterialAssignmentSet
{
    UMaterialInterface* TerrainBank = nullptr;
    UMaterialInterface* WetBoulderContact = nullptr;
    UMaterialInterface* BiomeFoliageGroundcover = nullptr;
    UMaterialInterface* FlowDependentWaterSurface = nullptr;
    UMaterialInterface* RaftForegroundReview = nullptr;

    bool IsCompleteForDurableSurfaceReview() const
    {
        return TerrainBank && WetBoulderContact && BiomeFoliageGroundcover && FlowDependentWaterSurface && RaftForegroundReview;
    }
};

FRaftSimFirstPartyMaterialAssignmentSet LoadFirstPartyMaterialAssignmentSetForSpec(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    FString& OutSummary)
{
    FRaftSimFirstPartyMaterialAssignmentSet Assignments;
    Assignments.TerrainBank = LoadFirstPartyMaterialInstanceCandidate(Spec.RiverId, TEXT("TerrainBank"));
    Assignments.WetBoulderContact = LoadFirstPartyMaterialInstanceCandidate(Spec.RiverId, TEXT("WetBoulderContact"));
    Assignments.BiomeFoliageGroundcover =
        LoadFirstPartyMaterialInstanceCandidate(Spec.RiverId, TEXT("BiomeFoliageGroundcover"));
    Assignments.FlowDependentWaterSurface =
        LoadFirstPartyMaterialInstanceCandidate(Spec.RiverId, TEXT("FlowDependentWaterSurface"));
    Assignments.RaftForegroundReview = LoadFirstPartyMaterialInstanceCandidate(Spec.RiverId, TEXT("RaftForegroundReview"));

    OutSummary += FString::Printf(
        TEXT("%s review material-instance scene assignment set for %s.\n"),
        Assignments.IsCompleteForDurableSurfaceReview() ? TEXT("Loaded") : TEXT("Incomplete"),
        *Spec.RiverId);
    return Assignments;
}

UMaterialInterface* SelectFirstPartyMaterialForPreviewActor(
    const FString& ActorLabel,
    const FRaftSimFirstPartyMaterialAssignmentSet& Assignments)
{
    if (ActorLabel.StartsWith(TEXT("RaftSim_ProceduralValleyTerrain_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_SourceAerialDrapeMicroTile_")))
    {
        return nullptr;
    }

    if (ActorLabel.StartsWith(TEXT("RaftSim_ProceduralRiverRibbon_")))
    {
        return Assignments.FlowDependentWaterSurface;
    }

    if (ActorLabel.StartsWith(TEXT("RaftSim_SourceAwareBoulder_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_BoulderSurfaceVariation_")))
    {
        return Assignments.WetBoulderContact;
    }

    if (ActorLabel.StartsWith(TEXT("RaftSim_SourceAwareFoliage_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_FoliageTrunk_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_FoliageCanopy_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_ProceduralLeafClusterSupplement_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_OrganicCanopyLeafSpray_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_OrganicBranchFrondSupplement_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_FineTwigCanopyLace_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_SourceAwareUnderstory_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_Understory_")) ||
        ActorLabel.StartsWith(TEXT("RaftSim_CanyonScrub_")))
    {
        return Assignments.BiomeFoliageGroundcover;
    }

    if (ActorLabel.StartsWith(TEXT("RaftSim_ForegroundRaft_")))
    {
        return Assignments.RaftForegroundReview;
    }

    return nullptr;
}

int32 AssignFirstPartyMaterialInstancesToPreviewScene(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimFirstPartyMaterialAssignmentSet& Assignments,
    FString& OutSummary)
{
    if (!World)
    {
        return 0;
    }

    int32 AssignedComponentCount = 0;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (!Actor)
        {
            continue;
        }

        UMaterialInterface* Material = SelectFirstPartyMaterialForPreviewActor(Actor->GetActorLabel(), Assignments);
        if (!Material)
        {
            continue;
        }

        TArray<UMeshComponent*> MeshComponents;
        Actor->GetComponents<UMeshComponent>(MeshComponents);
        for (UMeshComponent* MeshComponent : MeshComponents)
        {
            if (!MeshComponent)
            {
                continue;
            }

            const int32 MaterialCount = FMath::Max(1, MeshComponent->GetNumMaterials());
            for (int32 MaterialIndex = 0; MaterialIndex < MaterialCount; ++MaterialIndex)
            {
                MeshComponent->SetMaterial(MaterialIndex, Material);
            }
            ++AssignedComponentCount;
        }
    }

    OutSummary += FString::Printf(
        TEXT("Assigned %d review material-instance surface components in %s (%s).\n"),
        AssignedComponentCount,
        *Spec.RiverId,
        *GetFirstPartyMaterialInstanceSceneAssignmentStatus());
    return AssignedComponentCount;
}

UMaterialInstanceDynamic* CreatePreviewColorMaterial(UObject* Outer, const FLinearColor& Color)
{
    UMaterialInterface* BaseMaterial = LoadOrCreatePreviewColorMaterial();
    if (!BaseMaterial)
    {
        BaseMaterial = LoadPreviewBaseMaterial();
    }

    if (BaseMaterial)
    {
        UMaterialInstanceDynamic* Material = UMaterialInstanceDynamic::Create(BaseMaterial, Outer);
        Material->SetVectorParameterValue(TEXT("PreviewColor"), Color);
        Material->SetVectorParameterValue(TEXT("Color"), Color);
        Material->SetVectorParameterValue(TEXT("BaseColor"), Color);
        Material->SetVectorParameterValue(TEXT("Albedo"), Color);
        return Material;
    }

    return nullptr;
}

UMaterialInstanceDynamic* CreatePreviewTranslucentColorMaterial(UObject* Outer, const FLinearColor& Color, float Opacity)
{
    UMaterialInterface* BaseMaterial = LoadOrCreatePreviewTranslucentColorMaterial();
    if (BaseMaterial)
    {
        UMaterialInstanceDynamic* Material = UMaterialInstanceDynamic::Create(BaseMaterial, Outer);
        Material->SetVectorParameterValue(TEXT("PreviewColor"), Color);
        Material->SetScalarParameterValue(TEXT("PreviewOpacity"), FMath::Clamp(Opacity, 0.02f, 0.85f));
        return Material;
    }

    return nullptr;
}

TArray<FVector> ComputePreviewMeshNormals(const TArray<FVector>& Vertices, const TArray<int32>& Triangles)
{
    TArray<FVector> Normals;
    Normals.Init(FVector::ZeroVector, Vertices.Num());

    for (int32 TriangleIndex = 0; TriangleIndex + 2 < Triangles.Num(); TriangleIndex += 3)
    {
        const int32 A = Triangles[TriangleIndex];
        const int32 B = Triangles[TriangleIndex + 1];
        const int32 C = Triangles[TriangleIndex + 2];
        if (!Vertices.IsValidIndex(A) || !Vertices.IsValidIndex(B) || !Vertices.IsValidIndex(C))
        {
            continue;
        }

        const FVector FaceNormal = FVector::CrossProduct(Vertices[B] - Vertices[A], Vertices[C] - Vertices[A]).GetSafeNormal();
        Normals[A] += FaceNormal;
        Normals[B] += FaceNormal;
        Normals[C] += FaceNormal;
    }

    for (FVector& Normal : Normals)
    {
        Normal = Normal.GetSafeNormal(UE_SMALL_NUMBER, FVector::UpVector);
        if (Normal.Z < 0.0f)
        {
            Normal *= -1.0f;
        }
    }

    return Normals;
}

bool LoadPreviewPngImage(const FString& RelativePath, FRaftSimPreviewImage& OutImage)
{
    OutImage = FRaftSimPreviewImage();
    if (RelativePath.IsEmpty())
    {
        return false;
    }

    const FString AbsolutePath = FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), RelativePath));
    TArray<uint8> CompressedImage;
    if (!FFileHelper::LoadFileToArray(CompressedImage, *AbsolutePath))
    {
        UE_LOG(LogRaftSimEditor, Warning, TEXT("Failed to load preview drape image: %s"), *AbsolutePath);
        return false;
    }

    IImageWrapperModule& ImageWrapperModule =
        FModuleManager::LoadModuleChecked<IImageWrapperModule>(FName(TEXT("ImageWrapper")));
    TSharedPtr<IImageWrapper> ImageWrapper = ImageWrapperModule.CreateImageWrapper(EImageFormat::PNG, *AbsolutePath);
    if (!ImageWrapper.IsValid() || !ImageWrapper->SetCompressed(CompressedImage.GetData(), CompressedImage.Num()))
    {
        UE_LOG(LogRaftSimEditor, Warning, TEXT("Failed to decode preview drape image header: %s"), *AbsolutePath);
        return false;
    }

    TArray<uint8> RawBgra;
    if (!ImageWrapper->GetRaw(ERGBFormat::BGRA, 8, RawBgra))
    {
        UE_LOG(LogRaftSimEditor, Warning, TEXT("Failed to decode preview drape pixels: %s"), *AbsolutePath);
        return false;
    }

    OutImage.Width = ImageWrapper->GetWidth();
    OutImage.Height = ImageWrapper->GetHeight();
    if (OutImage.Width <= 0 || OutImage.Height <= 0 || RawBgra.Num() != OutImage.Width * OutImage.Height * 4)
    {
        UE_LOG(LogRaftSimEditor, Warning, TEXT("Preview drape image dimensions are invalid: %s"), *AbsolutePath);
        OutImage = FRaftSimPreviewImage();
        return false;
    }

    OutImage.Pixels.Reserve(OutImage.Width * OutImage.Height);
    for (int32 PixelIndex = 0; PixelIndex < OutImage.Width * OutImage.Height; ++PixelIndex)
    {
        const int32 ByteIndex = PixelIndex * 4;
        OutImage.Pixels.Add(FLinearColor(
            static_cast<float>(RawBgra[ByteIndex + 2]) / 255.0f,
            static_cast<float>(RawBgra[ByteIndex + 1]) / 255.0f,
            static_cast<float>(RawBgra[ByteIndex]) / 255.0f,
            static_cast<float>(RawBgra[ByteIndex + 3]) / 255.0f));
    }

    return true;
}

void ApplyPreviewColor(UMeshComponent* Component, const FLinearColor& Color)
{
    if (!Component)
    {
        return;
    }

    if (UMaterialInstanceDynamic* Material = CreatePreviewColorMaterial(Component, Color))
    {
        const int32 MaterialCount = FMath::Max(1, Component->GetNumMaterials());
        for (int32 MaterialIndex = 0; MaterialIndex < MaterialCount; ++MaterialIndex)
        {
            Component->SetMaterial(MaterialIndex, Material);
        }
    }
}

void ApplyPreviewTranslucentColor(UMeshComponent* Component, const FLinearColor& Color, float Opacity)
{
    if (!Component)
    {
        return;
    }

    if (UMaterialInstanceDynamic* Material = CreatePreviewTranslucentColorMaterial(Component, Color, Opacity))
    {
        const int32 MaterialCount = FMath::Max(1, Component->GetNumMaterials());
        for (int32 MaterialIndex = 0; MaterialIndex < MaterialCount; ++MaterialIndex)
        {
            Component->SetMaterial(MaterialIndex, Material);
        }
    }
}

float SmoothPreviewStep(float Edge0, float Edge1, float Value)
{
    if (FMath::IsNearlyEqual(Edge0, Edge1))
    {
        return Value >= Edge1 ? 1.0f : 0.0f;
    }

    const float T = FMath::Clamp((Value - Edge0) / (Edge1 - Edge0), 0.0f, 1.0f);
    return T * T * (3.0f - 2.0f * T);
}

FLinearColor ClampPreviewColor(const FLinearColor& Color)
{
    return FLinearColor(
        FMath::Clamp(Color.R, 0.0f, 1.0f),
        FMath::Clamp(Color.G, 0.0f, 1.0f),
        FMath::Clamp(Color.B, 0.0f, 1.0f),
        FMath::Clamp(Color.A, 0.0f, 1.0f));
}

FLinearColor ScalePreviewColor(const FLinearColor& Color, float Scale)
{
    return ClampPreviewColor(FLinearColor(Color.R * Scale, Color.G * Scale, Color.B * Scale, Color.A));
}

float GetPreviewColorLuma(const FLinearColor& Color)
{
    return FMath::Max(0.001f, Color.R * 0.2126f + Color.G * 0.7152f + Color.B * 0.0722f);
}

enum ERaftSimFirstPartyMaterialAtlasTile : int32
{
    TerrainBankLayeredMaterialTile = 0,
    WetBoulderContactMaterialTile = 1,
    BiomeFoliageGroundcoverMaterialTile = 2,
    FlowDependentWaterSurfaceMaterialTile = 3,
    FoamSprayMistAtmosphereMaterialTile = 4,
    RaftForegroundReviewMaterialTile = 5,
};

FLinearColor SampleFirstPartyMaterialAtlasTile(
    const FRaftSimPreviewImage* Atlas,
    int32 TileIndex,
    float LocalU,
    float LocalV)
{
    if (!Atlas || !Atlas->IsValid())
    {
        return FLinearColor::Black;
    }

    constexpr int32 AtlasColumns = 3;
    constexpr int32 AtlasRows = 2;
    const int32 ClampedTileIndex = FMath::Clamp(TileIndex, 0, AtlasColumns * AtlasRows - 1);
    const int32 Column = ClampedTileIndex % AtlasColumns;
    const int32 Row = ClampedTileIndex / AtlasColumns;
    const float WrappedU = FMath::Fmod(FMath::Fmod(LocalU, 1.0f) + 1.0f, 1.0f);
    const float WrappedV = FMath::Fmod(FMath::Fmod(LocalV, 1.0f) + 1.0f, 1.0f);
    const float AtlasU = (static_cast<float>(Column) + WrappedU) / static_cast<float>(AtlasColumns);
    const float TopOriginAtlasV = (static_cast<float>(Row) + WrappedV) / static_cast<float>(AtlasRows);
    return Atlas->SampleRaw(AtlasU, 1.0f - TopOriginAtlasV);
}

FLinearColor ApplyFirstPartyMaterialAtlasTint(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* Atlas,
    int32 TileIndex,
    const FLinearColor& BaseColor,
    float LocalU,
    float LocalV,
    float Weight)
{
    if (!Atlas || !Atlas->IsValid() || Weight <= 0.0f)
    {
        return BaseColor;
    }

    FLinearColor AtlasColor = ClampPreviewColor(SampleFirstPartyMaterialAtlasTile(Atlas, TileIndex, LocalU, LocalV));
    AtlasColor.A = BaseColor.A;
    const float BaseLuma = GetPreviewColorLuma(BaseColor);
    const float AtlasLuma = GetPreviewColorLuma(AtlasColor);
    const float MinAtlasLuma = BaseLuma * (Spec.bHasWaterfalls ? 0.50f : 0.58f);
    const float MaxAtlasLuma = BaseLuma * (Spec.bDesertCanyon ? 1.28f : 1.22f);
    const float TargetAtlasLuma = FMath::Clamp(AtlasLuma, MinAtlasLuma, MaxAtlasLuma);
    AtlasColor = ScalePreviewColor(AtlasColor, TargetAtlasLuma / AtlasLuma);
    AtlasColor.A = BaseColor.A;

    return ClampPreviewColor(FMath::Lerp(BaseColor, AtlasColor, FMath::Clamp(Weight, 0.0f, 0.32f)));
}

float SampleFirstPartyMaterialAtlasPackedHeight(
    const FRaftSimPreviewImage* PackedAtlas,
    int32 TileIndex,
    float LocalU,
    float LocalV,
    float DefaultHeight = 0.5f)
{
    if (!PackedAtlas || !PackedAtlas->IsValid())
    {
        return DefaultHeight;
    }

    return FMath::Clamp(SampleFirstPartyMaterialAtlasTile(PackedAtlas, TileIndex, LocalU, LocalV).B, 0.0f, 1.0f);
}

FLinearColor ApplyFirstPartyMaterialAtlasSurfaceResponse(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* NormalAtlas,
    const FRaftSimPreviewImage* PackedAtlas,
    int32 TileIndex,
    const FLinearColor& BaseColor,
    float LocalU,
    float LocalV,
    float Weight)
{
    if (Weight <= 0.0f)
    {
        return BaseColor;
    }

    const float ClampedWeight = FMath::Clamp(Weight, 0.0f, 0.30f);
    float ResponseScale = 1.0f;
    if (PackedAtlas && PackedAtlas->IsValid())
    {
        const FLinearColor Packed = ClampPreviewColor(SampleFirstPartyMaterialAtlasTile(PackedAtlas, TileIndex, LocalU, LocalV));
        const float AmbientOcclusion = FMath::Clamp(Packed.R, 0.0f, 1.0f);
        const float Roughness = FMath::Clamp(Packed.G, 0.0f, 1.0f);
        const float Height = FMath::Clamp(Packed.B, 0.0f, 1.0f);
        ResponseScale *= FMath::Clamp(
            1.0f - (1.0f - AmbientOcclusion) * 0.22f * ClampedWeight +
                (Roughness - 0.5f) * 0.10f * ClampedWeight +
                (Height - 0.5f) * 0.18f * ClampedWeight,
            0.86f,
            1.12f);
    }
    if (NormalAtlas && NormalAtlas->IsValid())
    {
        const FLinearColor Normal = ClampPreviewColor(SampleFirstPartyMaterialAtlasTile(NormalAtlas, TileIndex, LocalU, LocalV));
        const float SlopeEnergy = FMath::Clamp(FMath::Abs(Normal.R - 0.5f) + FMath::Abs(Normal.G - 0.5f), 0.0f, 1.0f);
        const float UpFacing = FMath::Clamp(Normal.B, 0.0f, 1.0f);
        ResponseScale *= FMath::Clamp(
            1.0f + SlopeEnergy * (Spec.bDesertCanyon ? 0.10f : 0.075f) * ClampedWeight -
                (1.0f - UpFacing) * 0.12f * ClampedWeight,
            0.90f,
            1.10f);
    }

    FLinearColor Result = ScalePreviewColor(BaseColor, ResponseScale);
    Result.A = BaseColor.A;
    return ClampPreviewColor(Result);
}

float GetFirstPartyMaterialAtlasMicroReliefCm(
    const FRaftSimPreviewImage* PackedAtlas,
    int32 TileIndex,
    float LocalU,
    float LocalV,
    float AmplitudeCm,
    float Weight)
{
    if (!PackedAtlas || !PackedAtlas->IsValid() || Weight <= 0.0f)
    {
        return 0.0f;
    }

    const float Height = SampleFirstPartyMaterialAtlasPackedHeight(PackedAtlas, TileIndex, LocalU, LocalV);
    return (Height - 0.5f) * AmplitudeCm * FMath::Clamp(Weight, 0.0f, 0.35f);
}

FLinearColor NormalizePreviewSourceDrapeAlbedo(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& RawColor,
    float SourceWaterT,
    float SourceVegetationT,
    float MaterialBlend)
{
    FLinearColor SourceColor = ClampPreviewColor(RawColor);
    SourceColor.A = 1.0f;

    const float Luma = FMath::Max(0.001f, SourceColor.R * 0.2126f + SourceColor.G * 0.7152f + SourceColor.B * 0.0722f);
    const float MinLuma = Spec.bDesertCanyon ? 0.23f : (Spec.bHasWaterfalls ? 0.125f : 0.18f);
    const float MaxLuma = Spec.bDesertCanyon ? 0.38f : (Spec.bHasWaterfalls ? 0.24f : 0.34f);
    float TargetLuma = Luma;
    if (Luma < MinLuma)
    {
        TargetLuma = FMath::Lerp(MinLuma, Luma, 0.22f);
        const float ShadowLiftT = FMath::Clamp((MinLuma - Luma) / MinLuma, 0.0f, 1.0f);
        const FLinearColor ShadowFill = Spec.bDesertCanyon
            ? FLinearColor(TargetLuma * 1.17f, TargetLuma * 0.92f, TargetLuma * 0.66f, 1.0f)
            : (Spec.bHasWaterfalls
                   ? FLinearColor(TargetLuma * 0.50f, TargetLuma * 0.86f, TargetLuma * 0.54f, 1.0f)
                   : FLinearColor(TargetLuma * 0.92f, TargetLuma * 0.86f, TargetLuma * 0.64f, 1.0f));
        SourceColor = FMath::Lerp(SourceColor, ShadowFill, FMath::Clamp(0.68f + ShadowLiftT * 0.24f, 0.0f, 0.92f));
    }
    else if (Luma > MaxLuma)
    {
        TargetLuma = FMath::Lerp(MaxLuma, Luma, 0.06f);
    }
    const float AdjustedLuma = FMath::Max(
        0.001f,
        SourceColor.R * 0.2126f + SourceColor.G * 0.7152f + SourceColor.B * 0.0722f);
    SourceColor = ScalePreviewColor(SourceColor, TargetLuma / AdjustedLuma);

    const FLinearColor BankMaterial = Spec.bDesertCanyon
        ? FLinearColor(0.48f, 0.32f, 0.20f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.060f, 0.105f, 0.060f) : Spec.TerrainColor);
    const FLinearColor VegetationMaterial = Spec.bDesertCanyon
        ? FLinearColor(0.27f, 0.29f, 0.15f)
        : ScalePreviewColor(Spec.FoliageColor, Spec.bHasWaterfalls ? 0.86f : 0.78f);
    const FLinearColor WetMaterial = Spec.bDesertCanyon
        ? FLinearColor(0.23f, 0.19f, 0.14f)
        : FMath::Lerp(ScalePreviewColor(Spec.RockColor, 0.42f), ScalePreviewColor(Spec.WaterColor, 0.30f), 0.36f);
    FLinearColor GuidedMaterial = FMath::Lerp(
        BankMaterial,
        VegetationMaterial,
        FMath::Clamp(SourceVegetationT * (Spec.bDesertCanyon ? 0.34f : 0.68f), 0.0f, 0.74f));
    GuidedMaterial = FMath::Lerp(
        GuidedMaterial,
        WetMaterial,
        FMath::Clamp(SourceWaterT * (Spec.bDesertCanyon ? 0.32f : 0.42f), 0.0f, 0.48f));

    return ClampPreviewColor(FMath::Lerp(SourceColor, GuidedMaterial, FMath::Clamp(MaterialBlend, 0.0f, 1.0f)));
}

FLinearColor NormalizePreviewTerrainProxyPatchColor(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& RawColor)
{
    FLinearColor Color = ClampPreviewColor(RawColor);
    Color.A = RawColor.A;

    const float Luma = GetPreviewColorLuma(Color);
    const float MinLuma = Spec.bDesertCanyon ? 0.300f : (Spec.bHasWaterfalls ? 0.220f : 0.260f);
    if (Luma >= MinLuma)
    {
        return Color;
    }

    const FLinearColor FillColor = Spec.bDesertCanyon
        ? FLinearColor(0.42f, 0.30f, 0.19f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.075f, 0.185f, 0.085f, Color.A)
                                : FLinearColor(0.27f, 0.25f, 0.17f, Color.A));
    const float LiftT = FMath::Clamp((MinLuma - Luma) / MinLuma, 0.0f, 1.0f);
    FLinearColor LiftedColor = FMath::Lerp(Color, FillColor, FMath::Clamp(LiftT * 0.78f, 0.0f, 0.78f));
    const float LiftedLuma = GetPreviewColorLuma(LiftedColor);
    const float TargetLuma = FMath::Lerp(MinLuma, Luma, Spec.bHasWaterfalls ? 0.18f : 0.14f);
    LiftedColor = ScalePreviewColor(LiftedColor, TargetLuma / LiftedLuma);
    LiftedColor.A = Color.A;
    return ClampPreviewColor(LiftedColor);
}

FLinearColor ApplyPreviewIntegratedTerrainCorridorTexture(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& RawColor,
    float X,
    float Y,
    float BankT,
    float CanyonT,
    float WetT,
    float SourceWaterT,
    float SourceVegetationT,
    float ChannelOffset,
    float ActiveRiverHalfWidth,
    float CellSeed)
{
    FLinearColor Color = ClampPreviewColor(RawColor);
    const float CorridorT = FMath::Clamp(
        SmoothPreviewStep(
            ActiveRiverHalfWidth + 110.0f,
            ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 2300.0f : 1420.0f),
            ChannelOffset) *
            (0.34f + BankT * 0.24f + CanyonT * 0.34f +
             SourceVegetationT * (Spec.bDesertCanyon ? 0.08f : 0.30f)) *
            (1.0f - FMath::Clamp(SourceWaterT * 0.72f + WetT * 0.18f, 0.0f, 0.82f)),
        0.0f,
        1.0f);
    if (CorridorT <= KINDA_SMALL_NUMBER)
    {
        return Color;
    }

    const float FineTextureNoise = FMath::Clamp(
        0.50f +
            0.31f * FMath::Sin(X * 0.018f + Y * (Spec.bDesertCanyon ? 0.011f : 0.017f) + CellSeed * 0.73f) +
            0.23f * FMath::Sin(X * 0.043f - Y * (Spec.bDesertCanyon ? 0.022f : 0.031f) + SourceVegetationT * 2.4f) +
            0.15f * FMath::Sin((X + Y) * 0.079f + CellSeed * 1.31f),
        0.0f,
        1.0f);
    const float FacetTextureNoise = FMath::Clamp(CellSeed * 0.46f + FineTextureNoise * 0.54f, 0.0f, 1.0f);

    FLinearColor TextureShadow;
    FLinearColor TextureMineral;
    FLinearColor TextureSunFace;
    FLinearColor TextureVegetation;
    FLinearColor TextureWetToe;
    if (Spec.bDesertCanyon)
    {
        TextureShadow = FLinearColor(0.245f, 0.145f, 0.085f, Color.A);
        TextureMineral = FLinearColor(0.665f, 0.390f, 0.205f, Color.A);
        TextureSunFace = FLinearColor(0.825f, 0.635f, 0.365f, Color.A);
        TextureVegetation = FLinearColor(0.375f, 0.400f, 0.235f, Color.A);
        TextureWetToe = FLinearColor(0.310f, 0.215f, 0.135f, Color.A);
    }
    else if (Spec.bHasWaterfalls)
    {
        TextureShadow = FLinearColor(0.020f, 0.070f, 0.030f, Color.A);
        TextureMineral = FLinearColor(0.085f, 0.145f, 0.060f, Color.A);
        TextureSunFace = FLinearColor(0.145f, 0.360f, 0.105f, Color.A);
        TextureVegetation = FLinearColor(0.070f, 0.310f, 0.075f, Color.A);
        TextureWetToe = FLinearColor(0.055f, 0.115f, 0.065f, Color.A);
    }
    else
    {
        TextureShadow = FLinearColor(0.135f, 0.130f, 0.075f, Color.A);
        TextureMineral = FLinearColor(0.430f, 0.390f, 0.215f, Color.A);
        TextureSunFace = FLinearColor(0.560f, 0.505f, 0.265f, Color.A);
        TextureVegetation = FLinearColor(0.210f, 0.365f, 0.125f, Color.A);
        TextureWetToe = FLinearColor(0.170f, 0.230f, 0.120f, Color.A);
    }

    const FLinearColor PaletteColor = FacetTextureNoise < 0.20f
        ? TextureShadow
        : (FacetTextureNoise < 0.44f
               ? TextureWetToe
               : (FacetTextureNoise < 0.66f
                      ? TextureMineral
                      : (FacetTextureNoise < 0.84f ? TextureVegetation : TextureSunFace)));
    const float PaletteBlend = FMath::Clamp(
        CorridorT *
            (Spec.bDesertCanyon ? 0.56f : (Spec.bHasWaterfalls ? 0.48f : 0.46f)) *
            (0.68f + FMath::Abs(FacetTextureNoise - 0.5f) * 0.62f),
        0.0f,
        Spec.bDesertCanyon ? 0.62f : 0.54f);
    Color = FMath::Lerp(Color, PaletteColor, PaletteBlend);

    const float LumaScale = FMath::Clamp(
        0.82f + FineTextureNoise * 0.34f + CellSeed * 0.10f,
        Spec.bHasWaterfalls ? 0.66f : 0.70f,
        Spec.bDesertCanyon ? 1.48f : 1.40f);
    Color = ScalePreviewColor(Color, LumaScale);

    const float LumaFloor =
        (Spec.bDesertCanyon ? 0.330f : (Spec.bHasWaterfalls ? 0.185f : 0.245f)) +
        SourceVegetationT * (Spec.bDesertCanyon ? 0.006f : 0.024f) +
        CanyonT * (Spec.bDesertCanyon ? 0.028f : 0.010f);
    const float ExistingLuma = GetPreviewColorLuma(Color);
    if (ExistingLuma < LumaFloor)
    {
        const FLinearColor FillColor = Spec.bDesertCanyon
            ? FLinearColor(0.455f, 0.305f, 0.180f, Color.A)
            : (Spec.bHasWaterfalls ? FLinearColor(0.075f, 0.185f, 0.075f, Color.A)
                                    : FLinearColor(0.295f, 0.285f, 0.155f, Color.A));
        Color = FMath::Lerp(
            Color,
            FillColor,
            FMath::Clamp(((LumaFloor - ExistingLuma) / LumaFloor) * CorridorT * 0.68f, 0.0f, 0.58f));
    }

    Color.A = RawColor.A;
    return ClampPreviewColor(Color);
}

FLinearColor ApplyPreviewSourceAwareTerrainSurfaceGranularity(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& RawColor,
    float X,
    float Y,
    float BankT,
    float CanyonT,
    float WetT,
    float SourceWaterT,
    float SourceVegetationT,
    float ChannelOffset,
    float ActiveRiverHalfWidth,
    float CellSeed)
{
    FLinearColor Color = ClampPreviewColor(RawColor);
    const float FirstPartyTerrainSurfaceGranularityT = FMath::Clamp(
        SmoothPreviewStep(
            ActiveRiverHalfWidth + 95.0f,
            ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 2600.0f : 1560.0f),
            ChannelOffset) *
            (0.38f + BankT * 0.28f + CanyonT * 0.34f +
             SourceVegetationT * (Spec.bDesertCanyon ? 0.10f : 0.34f)) *
            (1.0f - FMath::Clamp(SourceWaterT * 0.78f + WetT * 0.22f, 0.0f, 0.86f)),
        0.0f,
        1.0f);
    if (FirstPartyTerrainSurfaceGranularityT <= KINDA_SMALL_NUMBER)
    {
        return Color;
    }

    const float FirstPartyTerrainSurfaceGranularityNoise = FMath::Clamp(
        0.50f +
            0.24f * FMath::Sin(X * 0.031f + Y * (Spec.bDesertCanyon ? 0.019f : 0.028f) + CellSeed * 2.7f) +
            0.22f * FMath::Sin(X * 0.071f - Y * (Spec.bDesertCanyon ? 0.040f : 0.052f) + SourceVegetationT * 4.3f) +
            0.16f * FMath::Sin((X - Y) * 0.113f + CellSeed * 5.1f),
        0.0f,
        1.0f);
    const float FirstPartyTerrainSurfaceGranularityCell =
        FMath::Clamp(CellSeed * 0.58f + FirstPartyTerrainSurfaceGranularityNoise * 0.42f, 0.0f, 1.0f);

    FLinearColor DarkFleck;
    FLinearColor MidFleck;
    FLinearColor BrightFleck;
    FLinearColor OrganicFleck;
    if (Spec.bDesertCanyon)
    {
        DarkFleck = FLinearColor(0.225f, 0.135f, 0.080f, Color.A);
        MidFleck = FLinearColor(0.500f, 0.315f, 0.175f, Color.A);
        BrightFleck = FLinearColor(0.735f, 0.560f, 0.315f, Color.A);
        OrganicFleck = FLinearColor(0.340f, 0.360f, 0.205f, Color.A);
    }
    else if (Spec.bHasWaterfalls)
    {
        DarkFleck = FLinearColor(0.014f, 0.052f, 0.026f, Color.A);
        MidFleck = FLinearColor(0.055f, 0.125f, 0.050f, Color.A);
        BrightFleck = FLinearColor(0.130f, 0.270f, 0.090f, Color.A);
        OrganicFleck = FLinearColor(0.034f, 0.185f, 0.052f, Color.A);
    }
    else
    {
        DarkFleck = FLinearColor(0.120f, 0.115f, 0.070f, Color.A);
        MidFleck = FLinearColor(0.285f, 0.260f, 0.145f, Color.A);
        BrightFleck = FLinearColor(0.475f, 0.430f, 0.230f, Color.A);
        OrganicFleck = FLinearColor(0.155f, 0.275f, 0.090f, Color.A);
    }

    const FLinearColor GranularityColor = FirstPartyTerrainSurfaceGranularityCell < 0.22f
        ? DarkFleck
        : (FirstPartyTerrainSurfaceGranularityCell < 0.52f
               ? MidFleck
               : (FirstPartyTerrainSurfaceGranularityCell < (Spec.bDesertCanyon ? 0.76f : 0.70f)
                      ? OrganicFleck
                      : BrightFleck));
    const float FirstPartyTerrainGranularityBlend = FMath::Clamp(
        FirstPartyTerrainSurfaceGranularityT *
            (Spec.bDesertCanyon ? 0.34f : (Spec.bHasWaterfalls ? 0.32f : 0.30f)) *
            (0.66f + FMath::Abs(FirstPartyTerrainSurfaceGranularityCell - 0.5f) * 0.96f),
        0.0f,
        Spec.bDesertCanyon ? 0.36f : 0.33f);
    Color = FMath::Lerp(Color, GranularityColor, FirstPartyTerrainGranularityBlend);

    const float FirstPartyTerrainGranularityLumaScale = FMath::Clamp(
        0.86f + FirstPartyTerrainSurfaceGranularityNoise * 0.28f + CellSeed * 0.08f,
        Spec.bHasWaterfalls ? 0.68f : 0.72f,
        Spec.bDesertCanyon ? 1.42f : 1.36f);
    Color = ScalePreviewColor(Color, FirstPartyTerrainGranularityLumaScale);
    Color.A = RawColor.A;
    return ClampPreviewColor(Color);
}

FLinearColor GetPreviewSoftTerrainPatchFeatherBaseColor(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    float X,
    float Y,
    float Phase)
{
    const float BroadNoise = FMath::Clamp(
        0.50f + 0.34f * FMath::Sin(Phase * 0.67f + X * 0.00042f) +
            0.16f * FMath::Sin(Phase * 1.31f - Y * 0.00058f),
        0.0f,
        1.0f);

    FLinearColor BaseColor;
    if (Spec.bDesertCanyon)
    {
        BaseColor = FMath::Lerp(FLinearColor(0.33f, 0.23f, 0.15f), FLinearColor(0.57f, 0.40f, 0.24f), BroadNoise);
    }
    else if (Spec.bHasWaterfalls)
    {
        BaseColor = FMath::Lerp(FLinearColor(0.028f, 0.060f, 0.038f), FLinearColor(0.070f, 0.130f, 0.060f), BroadNoise);
        BaseColor = FMath::Lerp(BaseColor, ScalePreviewColor(Spec.FoliageColor, 0.52f), 0.24f);
    }
    else
    {
        BaseColor = FMath::Lerp(FLinearColor(0.18f, 0.17f, 0.12f), FLinearColor(0.30f, 0.28f, 0.16f), BroadNoise);
        BaseColor = FMath::Lerp(BaseColor, ScalePreviewColor(Spec.TerrainColor, 0.88f), 0.38f);
    }

    const float LumaJitter = 0.94f + 0.07f * FMath::Sin(Phase * 0.43f + X * 0.00071f - Y * 0.00039f);
    return NormalizePreviewTerrainProxyPatchColor(Spec, ScalePreviewColor(BaseColor, LumaJitter));
}

float GetPreviewSoftTerrainPatchCoverage(float U, float V, float Phase)
{
    const float StartFeather = SmoothPreviewStep(0.035f, 0.24f, U);
    const float EndFeather = 1.0f - SmoothPreviewStep(0.76f, 0.965f, U);
    const float CrossCenterT = 1.0f - FMath::Clamp(FMath::Abs(V - 0.5f) * 2.0f, 0.0f, 1.0f);
    const float CrossFeather = SmoothPreviewStep(0.0f, 0.70f, CrossCenterT);
    const float OrganicFeather = FMath::Clamp(
        0.82f + 0.12f * FMath::Sin(Phase + U * 5.9f + V * 2.7f) +
            0.06f * FMath::Sin(Phase * 0.47f + U * 13.0f - V * 4.1f),
        0.62f,
        1.0f);
    return FMath::Clamp(StartFeather * EndFeather * CrossFeather * OrganicFeather, 0.0f, 1.0f);
}

FLinearColor BlendPreviewSoftTerrainPatchColor(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& FeatureColor,
    float X,
    float Y,
    float U,
    float V,
    float Phase,
    float Coverage)
{
    const FLinearColor FeatherBase = GetPreviewSoftTerrainPatchFeatherBaseColor(Spec, X, Y, Phase);
    const float MaxFeatureBlend = Spec.bDesertCanyon ? 0.14f : (Spec.bHasWaterfalls ? 0.12f : 0.13f);
    const float Blend = FMath::Clamp(Coverage * MaxFeatureBlend, 0.0f, 0.16f);
    return ClampPreviewColor(FMath::Lerp(FeatherBase, FeatureColor, Blend));
}

float GetPreviewTerrainNormalSofteningBlend(const FRaftSimEnvironmentPreviewSpec& Spec)
{
    return Spec.TerrainNormalSofteningBlend;
}

void SoftenPreviewTerrainNormals(TArray<FVector>& Normals, float UpBlend)
{
    const float Blend = FMath::Clamp(UpBlend, 0.0f, 0.85f);
    for (FVector& Normal : Normals)
    {
        FVector SourceNormal = Normal.GetSafeNormal(UE_SMALL_NUMBER, FVector::UpVector);
        if (SourceNormal.Z < 0.0f)
        {
            SourceNormal *= -1.0f;
        }
        Normal = (SourceNormal * (1.0f - Blend) + FVector::UpVector * Blend).GetSafeNormal();
    }
}

float GetPreviewRiverCenterY(const FRaftSimEnvironmentPreviewSpec& Spec, float X)
{
    const float Primary = FMath::Sin((X + 3800.0f) * 0.00043f) * Spec.BendAmplitudeCm;
    const float Secondary = FMath::Sin((X - 600.0f) * 0.00019f) * Spec.BendAmplitudeCm * 0.35f;
    return Primary + Secondary;
}

float GetPreviewActiveRiverHalfWidthCm(const FRaftSimEnvironmentPreviewSpec& Spec)
{
    return FMath::Max(80.0f, Spec.RiverHalfWidthCm * FMath::Max(0.35f, Spec.FlowWidthScale));
}

float GetPreviewWaterSurfaceBaseZCm(const FRaftSimEnvironmentPreviewSpec& Spec)
{
    return 10.0f + Spec.FlowWaterLevelOffsetCm;
}

void GetPreviewMaskUv(const FRaftSimEnvironmentPreviewSpec& Spec, float X, float Y, float& OutU, float& OutV)
{
    const float MinX = -5800.0f;
    const float MaxX = 26500.0f;
    const float HalfWidth = Spec.bDesertCanyon ? 4300.0f : 2750.0f;
    OutU = FMath::Clamp((X - MinX) / (MaxX - MinX), 0.0f, 1.0f);
    OutV = FMath::Clamp((Y + HalfWidth) / (HalfWidth * 2.0f), 0.0f, 1.0f);
}

float SamplePreviewMaskAtWorld(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* Mask,
    float X,
    float Y)
{
    if (!Mask || !Mask->IsValid())
    {
        return 0.0f;
    }

    float U = 0.0f;
    float V = 0.0f;
    GetPreviewMaskUv(Spec, X, Y, U, V);
    return Mask->SampleLuma(U, V);
}

float SamplePreviewTerrainReliefCm(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    float X,
    float Y,
    float ChannelOffset)
{
    if (!TerrainRelief || !TerrainRelief->IsValid() || Spec.TerrainReliefAmplitudeCm <= 0.0f)
    {
        return 0.0f;
    }

    const float MinX = -5800.0f;
    const float MaxX = 26500.0f;
    const float HalfWidth = Spec.bDesertCanyon ? 4300.0f : 2750.0f;
    const float U = FMath::Clamp((X - MinX) / (MaxX - MinX), 0.0f, 1.0f);
    const float V = FMath::Clamp((Y + HalfWidth) / (HalfWidth * 2.0f), 0.0f, 1.0f);
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float ReliefMask = SmoothPreviewStep(
        ActiveRiverHalfWidth + 110.0f,
        ActiveRiverHalfWidth + Spec.BankWidthCm + 740.0f,
        ChannelOffset);
    return (TerrainRelief->SampleLuma(U, V) - 0.5f) * Spec.TerrainReliefAmplitudeCm * ReliefMask;
}

float SamplePreviewHeightfieldCm(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* HeightfieldPreview,
    float X,
    float Y,
    float ChannelOffset)
{
    if (!HeightfieldPreview || !HeightfieldPreview->IsValid() || Spec.HeightfieldPreviewAmplitudeCm <= 0.0f)
    {
        return 0.0f;
    }

    const float MinX = -5800.0f;
    const float MaxX = 26500.0f;
    const float HalfWidth = Spec.bDesertCanyon ? 4300.0f : 2750.0f;
    const float U = FMath::Clamp((X - MinX) / (MaxX - MinX), 0.0f, 1.0f);
    const float V = FMath::Clamp((Y + HalfWidth) / (HalfWidth * 2.0f), 0.0f, 1.0f);
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const auto SampleSeamFeatheredLuma = [HeightfieldPreview, &Spec](float SampleU, float SampleV)
    {
        const float Feather = FMath::Clamp(Spec.HeightfieldSeamFeatherUv, 0.0f, 0.12f);
        const auto SampleAcrossU = [HeightfieldPreview, Feather](float UValue, float VValue)
        {
            const float DistanceToSeam = FMath::Abs(UValue - 0.5f);
            if (Feather <= KINDA_SMALL_NUMBER || DistanceToSeam >= Feather)
            {
                return HeightfieldPreview->SampleLumaBilinear(UValue, VValue);
            }

            const float Left = HeightfieldPreview->SampleLumaBilinear(0.5f - Feather, VValue);
            const float Right = HeightfieldPreview->SampleLumaBilinear(0.5f + Feather, VValue);
            return FMath::Lerp(Left, Right, FMath::Clamp((UValue - (0.5f - Feather)) / (2.0f * Feather), 0.0f, 1.0f));
        };

        const float DistanceToVSeam = FMath::Abs(SampleV - 0.5f);
        if (Feather <= KINDA_SMALL_NUMBER || DistanceToVSeam >= Feather)
        {
            return SampleAcrossU(SampleU, SampleV);
        }

        const float Lower = SampleAcrossU(SampleU, 0.5f - Feather);
        const float Upper = SampleAcrossU(SampleU, 0.5f + Feather);
        return FMath::Lerp(Lower, Upper, FMath::Clamp((SampleV - (0.5f - Feather)) / (2.0f * Feather), 0.0f, 1.0f));
    };
    const float HeightfieldMask = SmoothPreviewStep(
        ActiveRiverHalfWidth + 45.0f,
        ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 920.0f : 560.0f),
        ChannelOffset);
    const float SourceHeight = SampleSeamFeatheredLuma(U, V);
    const float FineRadiusU = 4.0f / static_cast<float>(FMath::Max(1, HeightfieldPreview->Width - 1));
    const float FineRadiusV = 4.0f / static_cast<float>(FMath::Max(1, HeightfieldPreview->Height - 1));
    const float BroadRadiusU = FineRadiusU * 3.5f;
    const float BroadRadiusV = FineRadiusV * 3.5f;
    const float FineMean = 0.25f * (
        SampleSeamFeatheredLuma(U - FineRadiusU, V) +
        SampleSeamFeatheredLuma(U + FineRadiusU, V) +
        SampleSeamFeatheredLuma(U, V - FineRadiusV) +
        SampleSeamFeatheredLuma(U, V + FineRadiusV));
    const float BroadMean = 0.25f * (
        SampleSeamFeatheredLuma(U - BroadRadiusU, V) +
        SampleSeamFeatheredLuma(U + BroadRadiusU, V) +
        SampleSeamFeatheredLuma(U, V - BroadRadiusV) +
        SampleSeamFeatheredLuma(U, V + BroadRadiusV));
    const float SourceLocalRelief = FMath::Clamp(
        (SourceHeight - FineMean) * 0.62f + (SourceHeight - BroadMean) * 0.38f,
        -0.12f,
        0.12f);
    const float MacroReliefCm = (SourceHeight - 0.5f) * Spec.HeightfieldPreviewAmplitudeCm;
    const float LocalReliefCm = SourceLocalRelief * Spec.HeightfieldLocalReliefAmplitudeCm;
    return (MacroReliefCm + LocalReliefCm) * HeightfieldMask;
}

float SamplePreviewBankUndercutShelfReliefCm(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    float X,
    float Y,
    float ChannelOffset)
{
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float WetBankScale = FMath::Max(0.35f, Spec.FlowWetBankScale);
    const float BankDistance = FMath::Max(0.0f, ChannelOffset - ActiveRiverHalfWidth);
    const float BankToeT = 1.0f - FMath::Clamp(
        FMath::Abs(BankDistance - 115.0f * WetBankScale) / FMath::Max(1.0f, 210.0f * WetBankScale),
        0.0f,
        1.0f);
    const float ShelfT = SmoothPreviewStep(120.0f * WetBankScale, 420.0f * WetBankScale, BankDistance) *
        (1.0f - SmoothPreviewStep(640.0f * WetBankScale, 1120.0f * WetBankScale, BankDistance));
    const float RootBenchT = SmoothPreviewStep(
        ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 360.0f : 260.0f),
        ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 940.0f : 620.0f),
        ChannelOffset);
    const float SideSign = Y >= GetPreviewRiverCenterY(Spec, X) ? 1.0f : -1.0f;
    const float LongNoise = 0.55f + 0.45f * FMath::Sin(X * 0.0027f + SideSign * 1.73f);
    const float CrossNoise = 0.50f + 0.50f * FMath::Sin(X * 0.0061f + Y * 0.0038f);
    const float UndercutDrop = (Spec.bDesertCanyon ? 20.0f : (Spec.bHasWaterfalls ? 36.0f : 26.0f)) *
        BankToeT * (0.58f + 0.42f * LongNoise);
    const float ShelfLift = (Spec.bDesertCanyon ? 58.0f : (Spec.bHasWaterfalls ? 42.0f : 36.0f)) *
        ShelfT * (0.46f + 0.54f * CrossNoise);
    const float RootBenchLift = Spec.bHasWaterfalls
        ? 34.0f * RootBenchT * (0.40f + 0.60f * LongNoise)
        : (Spec.bDesertCanyon ? 22.0f : 16.0f) * RootBenchT * (0.30f + 0.70f * CrossNoise);
    return ShelfLift + RootBenchLift - UndercutDrop;
}

float GetPreviewTerrainHeightCm(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    float X,
    float Y,
    const FRaftSimPreviewImage* TerrainRelief = nullptr,
    const FRaftSimPreviewImage* HeightfieldPreview = nullptr)
{
    const float CenterY = GetPreviewRiverCenterY(Spec, X);
    const float Offset = FMath::Abs(Y - CenterY);
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float InnerBank = ActiveRiverHalfWidth;
    const float OuterBank = ActiveRiverHalfWidth + Spec.BankWidthCm;
    const float CanyonShoulder = OuterBank + (Spec.bDesertCanyon ? 1300.0f : 720.0f);
    const float BankT = SmoothPreviewStep(InnerBank, OuterBank, Offset);
    const float CanyonT = SmoothPreviewStep(OuterBank, CanyonShoulder, Offset);
    const float DownstreamSlope = -0.004f * (X + 5200.0f);
    const float GravelNoise =
        FMath::Sin(X * 0.0048f + Y * 0.0021f) * 18.0f + FMath::Sin(X * 0.0014f - Y * 0.0044f) * 11.0f;
    const float BankLift = Spec.bDesertCanyon ? 250.0f : 145.0f;
    const float CanyonLift = Spec.CanyonHeightCm * (Spec.bDesertCanyon ? 0.72f : 0.38f);

    return -82.0f + DownstreamSlope + BankT * BankLift + CanyonT * CanyonLift +
        GravelNoise * (0.35f + BankT * 0.75f) +
        SamplePreviewBankUndercutShelfReliefCm(Spec, X, Y, Offset) +
        SamplePreviewHeightfieldCm(Spec, HeightfieldPreview, X, Y, Offset) +
        SamplePreviewTerrainReliefCm(Spec, TerrainRelief, X, Y, Offset);
}

FLinearColor ApplyPreviewSourceAwareTerrainPhotoMottle(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& RawColor,
    float X,
    float Y,
    float BankT,
    float CanyonT,
    float WetT,
    float SourceWaterT,
    float SourceVegetationT)
{
    FLinearColor Color = ClampPreviewColor(RawColor);
    const float BroadMottle = FMath::Clamp(
        0.50f + 0.24f * FMath::Sin(X * 0.0021f + Y * 0.0038f) +
            0.18f * FMath::Sin(X * 0.0047f - Y * 0.0019f) +
            0.08f * FMath::Sin((X + Y) * 0.0093f),
        0.0f,
        1.0f);
    const float FineMottle = FMath::Clamp(
        0.50f + 0.28f * FMath::Sin(X * 0.020f + Y * 0.017f) +
            0.18f * FMath::Sin(X * 0.037f - Y * 0.029f),
        0.0f,
        1.0f);
    const float SurfaceCoverage = FMath::Clamp(
        (BankT * 0.52f + CanyonT * 0.58f + WetT * 0.18f +
         SourceVegetationT * (Spec.bDesertCanyon ? 0.08f : 0.24f)) *
            (1.0f - SourceWaterT * 0.32f),
        0.0f,
        1.0f);

    FLinearColor ShadowColor;
    FLinearColor HighlightColor;
    FLinearColor MaterialFleckColor;
    if (Spec.bDesertCanyon)
    {
        ShadowColor = FLinearColor(0.28f, 0.19f, 0.12f, Color.A);
        HighlightColor = FLinearColor(0.66f, 0.50f, 0.31f, Color.A);
        MaterialFleckColor = FLinearColor(0.43f, 0.27f, 0.17f, Color.A);
    }
    else if (Spec.bHasWaterfalls)
    {
        ShadowColor = FLinearColor(0.030f, 0.066f, 0.044f, Color.A);
        HighlightColor = FLinearColor(0.095f, 0.170f, 0.075f, Color.A);
        MaterialFleckColor = FLinearColor(0.080f, 0.070f, 0.044f, Color.A);
    }
    else
    {
        ShadowColor = FLinearColor(0.17f, 0.165f, 0.125f, Color.A);
        HighlightColor = FLinearColor(0.34f, 0.31f, 0.20f, Color.A);
        MaterialFleckColor = FLinearColor(0.24f, 0.25f, 0.145f, Color.A);
    }

    Color = FMath::Lerp(
        Color,
        ShadowColor,
        FMath::Clamp((1.0f - BroadMottle) * SurfaceCoverage * (Spec.bHasWaterfalls ? 0.10f : 0.13f), 0.0f, 0.14f));
    Color = FMath::Lerp(
        Color,
        HighlightColor,
        FMath::Clamp(BroadMottle * SurfaceCoverage * (Spec.bDesertCanyon ? 0.15f : 0.10f), 0.0f, 0.16f));
    Color = FMath::Lerp(
        Color,
        MaterialFleckColor,
        FMath::Clamp(FineMottle * SurfaceCoverage * (Spec.bHasWaterfalls ? 0.18f : 0.12f), 0.0f, 0.18f));

    const FLinearColor WetToeColor = Spec.bDesertCanyon
        ? FLinearColor(0.25f, 0.19f, 0.13f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.018f, 0.050f, 0.040f, Color.A)
                                : FLinearColor(0.12f, 0.145f, 0.115f, Color.A));
    Color = FMath::Lerp(
        Color,
        WetToeColor,
        FMath::Clamp(FMath::Max(WetT * 0.18f, SourceWaterT * 0.20f) * SurfaceCoverage, 0.0f, 0.24f));

    return ClampPreviewColor(Color);
}

FLinearColor ApplyPreviewSourceConditionedFarBankAlbedoCalibration(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& RawColor,
    const FLinearColor& SourceDrapeColor,
    bool bHasSourceDrapeColor,
    float X,
    float Y,
    float BankT,
    float CanyonT,
    float WetT,
    float SourceWaterT,
    float SourceVegetationT,
    float ChannelOffset,
    float ActiveRiverHalfWidth)
{
    FLinearColor Color = ClampPreviewColor(RawColor);
    if (!bHasSourceDrapeColor)
    {
        return Color;
    }

    const float FarBankT = SmoothPreviewStep(
        ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 720.0f : 520.0f),
        ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 1320.0f : 820.0f),
        ChannelOffset);
    const float WaterReadabilityClearanceT = SmoothPreviewStep(
        ActiveRiverHalfWidth + 260.0f * FMath::Max(0.35f, Spec.FlowWetBankScale),
        ActiveRiverHalfWidth + 980.0f * FMath::Max(0.35f, Spec.FlowWetBankScale),
        ChannelOffset);
    const float FarBankSourceDrapeGain = Spec.bDesertCanyon ? 0.28f : (Spec.bHasWaterfalls ? 0.22f : 0.24f);
    const float SourceConditionedFarBankAlbedoT = FMath::Clamp(
        FarBankSourceDrapeGain *
            FarBankT *
            WaterReadabilityClearanceT *
            (0.44f + BankT * 0.18f + CanyonT * 0.28f + SourceVegetationT * (Spec.bDesertCanyon ? 0.06f : 0.18f)) *
            (1.0f - SourceWaterT * 0.62f),
        0.0f,
        Spec.bDesertCanyon ? 0.24f : 0.20f);
    Color = FMath::Lerp(Color, SourceDrapeColor, SourceConditionedFarBankAlbedoT);

    const float SourceConditionedTerrainLumaTarget =
        (Spec.bDesertCanyon ? 0.345f : (Spec.bHasWaterfalls ? 0.255f : 0.292f)) +
        SourceVegetationT * (Spec.bDesertCanyon ? 0.010f : 0.018f);
    const float ExistingLuma = GetPreviewColorLuma(Color);
    if (ExistingLuma < SourceConditionedTerrainLumaTarget)
    {
        const FLinearColor SourceConditionedFill = Spec.bDesertCanyon
            ? FLinearColor(0.46f, 0.32f, 0.20f, Color.A)
            : (Spec.bHasWaterfalls ? FLinearColor(0.065f, 0.160f, 0.070f, Color.A)
                                    : FLinearColor(0.29f, 0.280f, 0.165f, Color.A));
        const float LiftT = FMath::Clamp(
            ((SourceConditionedTerrainLumaTarget - ExistingLuma) / SourceConditionedTerrainLumaTarget) *
                FarBankT *
                WaterReadabilityClearanceT *
                (1.0f - WetT * 0.34f),
            0.0f,
            0.55f);
        Color = FMath::Lerp(Color, SourceConditionedFill, LiftT);
    }

    const float SourceConditionedSlopePhotoMottleT = FMath::Clamp(
        (0.48f + 0.26f * FMath::Sin(X * 0.0017f + Y * 0.0029f) +
         0.18f * FMath::Sin(X * 0.0046f - Y * 0.0011f)) *
            FarBankT *
            WaterReadabilityClearanceT,
        0.0f,
        1.0f);
    const FLinearColor SlopeHighlight = Spec.bDesertCanyon
        ? FLinearColor(0.58f, 0.40f, 0.25f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.082f, 0.190f, 0.080f, Color.A)
                                : FLinearColor(0.33f, 0.31f, 0.18f, Color.A));
    const FLinearColor SlopeShadow = Spec.bDesertCanyon
        ? FLinearColor(0.24f, 0.17f, 0.11f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.020f, 0.055f, 0.030f, Color.A)
                                : FLinearColor(0.14f, 0.13f, 0.085f, Color.A));
    Color = FMath::Lerp(
        Color,
        SourceConditionedSlopePhotoMottleT > 0.50f ? SlopeHighlight : SlopeShadow,
        FMath::Clamp(FMath::Abs(SourceConditionedSlopePhotoMottleT - 0.50f) * 0.20f, 0.0f, 0.10f));

    return ClampPreviewColor(Color);
}

FLinearColor ApplyPreviewBroadSlopeTerrainExposureFill(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& RawColor,
    const FLinearColor& SourceDrapeColor,
    bool bHasSourceDrapeColor,
    float X,
    float Y,
    float BankT,
    float CanyonT,
    float WetT,
    float SourceWaterT,
    float SourceVegetationT,
    float ChannelOffset,
    float ActiveRiverHalfWidth)
{
    FLinearColor Color = ClampPreviewColor(RawColor);
    const float BroadSlopeTerrainExposureFillT = FMath::Clamp(
        SmoothPreviewStep(
            ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 560.0f : 420.0f),
            ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 1800.0f : 1040.0f),
            ChannelOffset) *
            SmoothPreviewStep(
                ActiveRiverHalfWidth + 260.0f * FMath::Max(0.35f, Spec.FlowWetBankScale),
                ActiveRiverHalfWidth + 920.0f * FMath::Max(0.35f, Spec.FlowWetBankScale),
                ChannelOffset) *
            (0.46f + BankT * 0.20f + CanyonT * 0.32f + SourceVegetationT * (Spec.bDesertCanyon ? 0.04f : 0.12f)) *
            (1.0f - FMath::Clamp(SourceWaterT * 0.78f + WetT * 0.30f, 0.0f, 0.86f)),
        0.0f,
        1.0f);
    if (BroadSlopeTerrainExposureFillT <= KINDA_SMALL_NUMBER)
    {
        return Color;
    }

    if (bHasSourceDrapeColor)
    {
        const float BroadSlopeSourceDrapeT = FMath::Clamp(
            BroadSlopeTerrainExposureFillT * (Spec.bDesertCanyon ? 0.085f : (Spec.bHasWaterfalls ? 0.060f : 0.070f)),
            0.0f,
            Spec.bDesertCanyon ? 0.085f : 0.070f);
        Color = FMath::Lerp(Color, SourceDrapeColor, BroadSlopeSourceDrapeT);
    }

    const float BroadSlopeTerrainLumaTarget =
        (Spec.bDesertCanyon ? 0.405f : (Spec.bHasWaterfalls ? 0.238f : 0.318f)) +
        SourceVegetationT * (Spec.bDesertCanyon ? 0.004f : 0.010f);
    const float ExistingLuma = GetPreviewColorLuma(Color);
    if (ExistingLuma < BroadSlopeTerrainLumaTarget)
    {
        const float ExposureScale = FMath::Clamp(
            BroadSlopeTerrainLumaTarget / FMath::Max(ExistingLuma, 0.010f),
            1.0f,
            Spec.bDesertCanyon ? 1.58f : 1.48f);
        const FLinearColor ExposureLiftedColor = ClampPreviewColor(FLinearColor(
            Color.R * ExposureScale,
            Color.G * ExposureScale,
            Color.B * ExposureScale,
            Color.A));
        const FLinearColor BroadSlopeTerrainExposureFillColor = Spec.bDesertCanyon
            ? FLinearColor(0.56f, 0.38f, 0.23f, Color.A)
            : (Spec.bHasWaterfalls ? FLinearColor(0.120f, 0.240f, 0.105f, Color.A)
                                    : FLinearColor(0.34f, 0.320f, 0.195f, Color.A));
        const FLinearColor FilledColor = FMath::Lerp(ExposureLiftedColor, BroadSlopeTerrainExposureFillColor, 0.36f);
        const float BroadSlopeTerrainExposureLiftT = FMath::Clamp(
            ((BroadSlopeTerrainLumaTarget - ExistingLuma) / BroadSlopeTerrainLumaTarget) *
                BroadSlopeTerrainExposureFillT *
                (Spec.bDesertCanyon ? 0.78f : 0.70f),
            0.0f,
            Spec.bDesertCanyon ? 0.62f : 0.56f);
        Color = FMath::Lerp(Color, FilledColor, BroadSlopeTerrainExposureLiftT);
    }

    const float BroadSlopeTerrainMaterialVariationT = FMath::Clamp(
        0.50f + 0.24f * FMath::Sin(X * 0.0013f + Y * 0.0019f) +
            0.18f * FMath::Sin(X * 0.0036f - Y * 0.0024f) +
            0.08f * FMath::Sin((X - Y) * 0.0065f),
        0.0f,
        1.0f);
    const FLinearColor BroadSlopeSunFaceColor = Spec.bDesertCanyon
        ? FLinearColor(0.64f, 0.44f, 0.27f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.150f, 0.285f, 0.115f, Color.A)
                                : FLinearColor(0.38f, 0.355f, 0.215f, Color.A));
    const FLinearColor BroadSlopeAmbientCreaseColor = Spec.bDesertCanyon
        ? FLinearColor(0.30f, 0.20f, 0.13f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.045f, 0.105f, 0.052f, Color.A)
                                : FLinearColor(0.18f, 0.165f, 0.108f, Color.A));
    Color = FMath::Lerp(
        Color,
        BroadSlopeTerrainMaterialVariationT >= 0.50f ? BroadSlopeSunFaceColor : BroadSlopeAmbientCreaseColor,
        FMath::Clamp(
            FMath::Abs(BroadSlopeTerrainMaterialVariationT - 0.50f) *
                BroadSlopeTerrainExposureFillT *
                (Spec.bDesertCanyon ? 0.22f : 0.18f),
            0.0f,
            Spec.bDesertCanyon ? 0.14f : 0.11f));

    return ClampPreviewColor(Color);
}

FLinearColor ApplyPreviewSourceAwareTerrainSlopeFacetTexture(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& RawColor,
    float X,
    float Y,
    float BankT,
    float CanyonT,
    float WetT,
    float SourceWaterT,
    float SourceVegetationT,
    float ChannelOffset,
    float ActiveRiverHalfWidth)
{
    FLinearColor Color = ClampPreviewColor(RawColor);
    const float SourceAwareTerrainSlopeFacetTextureT = FMath::Clamp(
        SmoothPreviewStep(
            ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 420.0f : 300.0f),
            ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 2300.0f : 1380.0f),
            ChannelOffset) *
            (0.34f + BankT * 0.24f + CanyonT * 0.40f +
             SourceVegetationT * (Spec.bDesertCanyon ? 0.04f : 0.18f)) *
            (1.0f - FMath::Clamp(SourceWaterT * 0.82f + WetT * 0.28f, 0.0f, 0.90f)),
        0.0f,
        1.0f);
    if (SourceAwareTerrainSlopeFacetTextureT <= KINDA_SMALL_NUMBER)
    {
        return Color;
    }

    const float SourceAwareTerrainSlopeFacetNoise = FMath::Clamp(
        0.50f +
            0.31f * FMath::Sin(X * 0.0024f + Y * (Spec.bDesertCanyon ? 0.0033f : 0.0041f)) +
            0.19f * FMath::Sin(X * 0.0060f - Y * (Spec.bDesertCanyon ? 0.0021f : 0.0037f)) +
            0.10f * FMath::Sin((X + Y) * 0.011f + SourceVegetationT * 3.2f),
        0.0f,
        1.0f);
    const float SourceAwareTerrainSlopeFacetSunFaceT =
        SmoothPreviewStep(0.56f, 0.90f, SourceAwareTerrainSlopeFacetNoise) *
        SourceAwareTerrainSlopeFacetTextureT;
    const float SourceAwareTerrainSlopeFacetCreaseT =
        SmoothPreviewStep(0.12f, 0.48f, 1.0f - SourceAwareTerrainSlopeFacetNoise) *
        SourceAwareTerrainSlopeFacetTextureT;
    const float SourceAwareTerrainSlopeFacetStrataT = FMath::Clamp(
        (0.50f + 0.50f * FMath::Sin(Y * (Spec.bDesertCanyon ? 0.010f : 0.014f) + X * 0.0012f)) *
            SourceAwareTerrainSlopeFacetTextureT,
        0.0f,
        1.0f);

    const FLinearColor SlopeSunColor = Spec.bDesertCanyon
        ? FLinearColor(0.67f, 0.46f, 0.28f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.105f, 0.215f, 0.085f, Color.A)
                                : FLinearColor(0.365f, 0.335f, 0.205f, Color.A));
    const FLinearColor SlopeCreaseColor = Spec.bDesertCanyon
        ? FLinearColor(0.25f, 0.165f, 0.105f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.020f, 0.060f, 0.034f, Color.A)
                                : FLinearColor(0.135f, 0.125f, 0.082f, Color.A));
    const FLinearColor SlopeStrataColor = Spec.bDesertCanyon
        ? FLinearColor(0.48f, 0.315f, 0.190f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.060f, 0.130f, 0.060f, Color.A)
                                : FLinearColor(0.245f, 0.225f, 0.140f, Color.A));

    Color = FMath::Lerp(
        Color,
        SlopeCreaseColor,
        FMath::Clamp(
            SourceAwareTerrainSlopeFacetCreaseT * (Spec.bDesertCanyon ? 0.24f : 0.18f),
            0.0f,
            Spec.bDesertCanyon ? 0.20f : 0.16f));
    Color = FMath::Lerp(
        Color,
        SlopeSunColor,
        FMath::Clamp(
            SourceAwareTerrainSlopeFacetSunFaceT * (Spec.bDesertCanyon ? 0.22f : 0.16f),
            0.0f,
            Spec.bDesertCanyon ? 0.19f : 0.14f));
    Color = FMath::Lerp(
        Color,
        SlopeStrataColor,
        FMath::Clamp(
            FMath::Abs(SourceAwareTerrainSlopeFacetStrataT - 0.50f) *
                SourceAwareTerrainSlopeFacetTextureT *
                (Spec.bDesertCanyon ? 0.20f : 0.13f),
            0.0f,
            Spec.bDesertCanyon ? 0.14f : 0.10f));

    return ClampPreviewColor(Color);
}

FLinearColor ApplyPreviewSourceAwareRiparianCanopyMassTexture(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& RawColor,
    float X,
    float Y,
    float BankT,
    float CanyonT,
    float WetT,
    float SourceWaterT,
    float SourceVegetationT,
    float ChannelOffset,
    float ActiveRiverHalfWidth)
{
    FLinearColor Color = ClampPreviewColor(RawColor);
    const float SourceAwareRiparianCanopyMassTextureT = FMath::Clamp(
        SmoothPreviewStep(
            ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 520.0f : 260.0f),
            ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 2100.0f : 1280.0f),
            ChannelOffset) *
            (Spec.bDesertCanyon
                 ? (0.12f + BankT * 0.20f + SourceVegetationT * 0.26f)
                 : (Spec.bHasWaterfalls
                        ? (0.18f + BankT * 0.28f + CanyonT * 0.24f + SourceVegetationT * 0.62f)
                        : (0.16f + BankT * 0.30f + CanyonT * 0.12f + SourceVegetationT * 0.48f))) *
            (1.0f - FMath::Clamp(SourceWaterT * 0.88f + WetT * 0.42f, 0.0f, 0.92f)),
        0.0f,
        1.0f);
    if (SourceAwareRiparianCanopyMassTextureT <= KINDA_SMALL_NUMBER)
    {
        return Color;
    }

    const float SourceAwareRiparianCanopyMassNoise = FMath::Clamp(
        0.50f +
            0.28f * FMath::Sin(X * 0.0032f + Y * (Spec.bDesertCanyon ? 0.0021f : 0.0065f)) +
            0.18f * FMath::Sin(X * 0.0090f - Y * (Spec.bDesertCanyon ? 0.0035f : 0.0054f)) +
            0.12f * FMath::Sin((X - Y) * 0.0140f + SourceVegetationT * 2.7f),
        0.0f,
        1.0f);
    const float SourceAwareRiparianCanopyUnderstoryShadowT =
        SmoothPreviewStep(0.10f, 0.48f, 1.0f - SourceAwareRiparianCanopyMassNoise) *
        SourceAwareRiparianCanopyMassTextureT;
    const float SourceAwareRiparianCanopyLeafHighlightT =
        SmoothPreviewStep(0.56f, 0.92f, SourceAwareRiparianCanopyMassNoise) *
        SourceAwareRiparianCanopyMassTextureT;
    const float SourceAwareRiparianCanopyPatchBreakupT = FMath::Clamp(
        (0.50f + 0.50f * FMath::Sin(X * 0.0041f + Y * 0.0087f)) *
            SourceAwareRiparianCanopyMassTextureT,
        0.0f,
        1.0f);

    const FLinearColor CanopyShadowColor = Spec.bDesertCanyon
        ? FLinearColor(0.18f, 0.165f, 0.105f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.006f, 0.052f, 0.022f, Color.A)
                                : FLinearColor(0.095f, 0.145f, 0.060f, Color.A));
    const FLinearColor CanopyMidColor = Spec.bDesertCanyon
        ? FLinearColor(0.28f, 0.245f, 0.145f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.024f, 0.125f, 0.038f, Color.A)
                                : FLinearColor(0.155f, 0.240f, 0.090f, Color.A));
    const FLinearColor CanopyLeafHighlightColor = Spec.bDesertCanyon
        ? FLinearColor(0.36f, 0.315f, 0.180f, Color.A)
        : (Spec.bHasWaterfalls ? FLinearColor(0.052f, 0.205f, 0.064f, Color.A)
                                : FLinearColor(0.235f, 0.330f, 0.120f, Color.A));

    Color = FMath::Lerp(
        Color,
        CanopyMidColor,
        FMath::Clamp(
            SourceAwareRiparianCanopyMassTextureT * (Spec.bDesertCanyon ? 0.10f : (Spec.bHasWaterfalls ? 0.20f : 0.16f)),
            0.0f,
            Spec.bDesertCanyon ? 0.09f : (Spec.bHasWaterfalls ? 0.18f : 0.14f)));
    Color = FMath::Lerp(
        Color,
        CanopyShadowColor,
        FMath::Clamp(
            SourceAwareRiparianCanopyUnderstoryShadowT *
                (Spec.bDesertCanyon ? 0.12f : (Spec.bHasWaterfalls ? 0.28f : 0.22f)),
            0.0f,
            Spec.bDesertCanyon ? 0.10f : (Spec.bHasWaterfalls ? 0.24f : 0.19f)));
    Color = FMath::Lerp(
        Color,
        CanopyLeafHighlightColor,
        FMath::Clamp(
            SourceAwareRiparianCanopyLeafHighlightT *
                (0.45f + SourceAwareRiparianCanopyPatchBreakupT * 0.55f) *
                (Spec.bDesertCanyon ? 0.10f : (Spec.bHasWaterfalls ? 0.19f : 0.15f)),
            0.0f,
            Spec.bDesertCanyon ? 0.08f : (Spec.bHasWaterfalls ? 0.17f : 0.13f)));

    return ClampPreviewColor(Color);
}

AStaticMeshActor* AddPreviewMeshActor(
    UWorld* World,
    UStaticMesh* Mesh,
    const FString& Label,
    const FVector& Location,
    const FRotator& Rotation,
    const FVector& Scale,
    const FLinearColor& Color,
    UMaterialInterface* MaterialOverride = nullptr,
    bool bUseMeshDefaultMaterial = false)
{
    if (!World || !Mesh || !GEditor)
    {
        return nullptr;
    }

    AStaticMeshActor* Actor = Cast<AStaticMeshActor>(
        GEditor->AddActor(World->GetCurrentLevel(), AStaticMeshActor::StaticClass(), FTransform(Rotation, Location, Scale), true, RF_Transactional, false));
    if (!Actor)
    {
        return nullptr;
    }

    Actor->SetActorLabel(Label);
    UStaticMeshComponent* Component = Actor->GetStaticMeshComponent();
    Component->SetStaticMesh(Mesh);
    Component->SetMobility(EComponentMobility::Static);
    Component->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Component->SetCastShadow(false);
    if (MaterialOverride)
    {
        Component->SetMaterial(0, MaterialOverride);
    }
    else if (!bUseMeshDefaultMaterial)
    {
        ApplyPreviewColor(Component, Color);
    }
    return Actor;
}

AStaticMeshActor* AddPreviewTranslucentMeshActor(
    UWorld* World,
    UStaticMesh* Mesh,
    const FString& Label,
    const FVector& Location,
    const FRotator& Rotation,
    const FVector& Scale,
    const FLinearColor& Color,
    float Opacity)
{
    AStaticMeshActor* Actor = AddPreviewMeshActor(World, Mesh, Label, Location, Rotation, Scale, Color);
    if (Actor && Actor->GetStaticMeshComponent())
    {
        Actor->GetStaticMeshComponent()->SetCastShadow(false);
        Actor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        ApplyPreviewTranslucentColor(Actor->GetStaticMeshComponent(), Color, Opacity);
    }
    return Actor;
}

UInstancedStaticMeshComponent* AddPreviewInstancedMeshComponent(
    UWorld* World,
    UStaticMesh* Mesh,
    const FString& Label,
    const FLinearColor& Color)
{
    if (!World || !Mesh)
    {
        return nullptr;
    }

    AActor* Actor = World->SpawnActor<AActor>(AActor::StaticClass(), FTransform::Identity);
    if (!Actor)
    {
        return nullptr;
    }

    Actor->SetActorLabel(Label);
    UInstancedStaticMeshComponent* Component =
        NewObject<UInstancedStaticMeshComponent>(Actor, *FString::Printf(TEXT("%s_Instances"), *Label));
    if (!Component)
    {
        Actor->Destroy();
        return nullptr;
    }

    Component->SetStaticMesh(Mesh);
    Component->SetMobility(EComponentMobility::Static);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCastShadow(false);
    Actor->SetRootComponent(Component);
    Actor->AddInstanceComponent(Component);
    Component->RegisterComponent();
    ApplyPreviewColor(Component, Color);
    return Component;
}

UHierarchicalInstancedStaticMeshComponent* AddLandscapeCandidateInstancedMeshComponent(
    UWorld* World,
    UStaticMesh* Mesh,
    const FString& Label,
    bool bCastShadow,
    UMaterialInterface* MaterialOverride = nullptr)
{
    if (!World || !Mesh)
    {
        return nullptr;
    }

    AActor* Actor = World->SpawnActor<AActor>(AActor::StaticClass(), FTransform::Identity);
    if (!Actor)
    {
        return nullptr;
    }

    Actor->SetActorLabel(Label);
    UHierarchicalInstancedStaticMeshComponent* Component =
        NewObject<UHierarchicalInstancedStaticMeshComponent>(
            Actor,
            *FString::Printf(TEXT("%s_Instances"), *Label));
    if (!Component)
    {
        Actor->Destroy();
        return nullptr;
    }

    Component->SetStaticMesh(Mesh);
    Component->SetMobility(EComponentMobility::Static);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCastShadow(bCastShadow);
    Component->SetCullDistances(0, 60000);
    if (MaterialOverride)
    {
        for (int32 MaterialIndex = 0; MaterialIndex < Mesh->GetStaticMaterials().Num(); ++MaterialIndex)
        {
            Component->SetMaterial(MaterialIndex, MaterialOverride);
        }
    }
    Actor->SetRootComponent(Component);
    Actor->AddInstanceComponent(Component);
    Component->RegisterComponent();
    return Component;
}

AActor* AddPreviewProceduralMeshActor(
    UWorld* World,
    const FString& Label,
    const TArray<FVector>& Vertices,
    const TArray<int32>& Triangles,
    const TArray<FVector>& Normals,
    const TArray<FVector2D>& UVs,
    const FLinearColor& Color,
    UMaterialInterface* MaterialOverride = nullptr,
    const TArray<FLinearColor>* VertexColorOverride = nullptr,
    bool bCreateCollision = true)
{
    if (!World || Vertices.IsEmpty() || Triangles.IsEmpty())
    {
        return nullptr;
    }

    AActor* Actor = World->SpawnActor<AActor>(AActor::StaticClass(), FTransform::Identity);
    if (!Actor)
    {
        return nullptr;
    }

    Actor->SetActorLabel(Label);
    UProceduralMeshComponent* MeshComponent =
        NewObject<UProceduralMeshComponent>(Actor, *FString::Printf(TEXT("%s_Mesh"), *Label));
    if (!MeshComponent)
    {
        Actor->Destroy();
        return nullptr;
    }

    Actor->SetRootComponent(MeshComponent);
    Actor->AddInstanceComponent(MeshComponent);
    MeshComponent->RegisterComponent();
    MeshComponent->SetMobility(EComponentMobility::Static);
    MeshComponent->SetCastShadow(false);
    MeshComponent->bUseComplexAsSimpleCollision = bCreateCollision;
    MeshComponent->SetCollisionEnabled(
        bCreateCollision ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);

    TArray<FLinearColor> VertexColors;
    if (VertexColorOverride && VertexColorOverride->Num() == Vertices.Num())
    {
        VertexColors = *VertexColorOverride;
    }
    else
    {
        VertexColors.Init(Color, Vertices.Num());
    }
    TArray<FProcMeshTangent> Tangents;
    Tangents.Init(FProcMeshTangent(1.0f, 0.0f, 0.0f), Vertices.Num());

    MeshComponent->CreateMeshSection_LinearColor(
        0,
        Vertices,
        Triangles,
        Normals,
        UVs,
        VertexColors,
        Tangents,
        bCreateCollision);
    if (MaterialOverride)
    {
        MeshComponent->SetMaterial(0, MaterialOverride);
    }
    else
    {
        ApplyPreviewColor(MeshComponent, Color);
    }

    return Actor;
}

AActor* AddPreviewIrregularRockActor(
    UWorld* World,
    const FString& Label,
    const FVector& BaseLocation,
    float YawDegrees,
    const FVector& Scale,
    const FLinearColor& Color,
    int32 Seed)
{
    if (!World)
    {
        return nullptr;
    }

    constexpr int32 RingCount = 8;
    constexpr int32 SegmentCount = 20;
    const float YawRadians = FMath::DegreesToRadians(YawDegrees);
    const float CosYaw = FMath::Cos(YawRadians);
    const float SinYaw = FMath::Sin(YawRadians);
    const FVector Radii(
        FMath::Max(4.0f, Scale.X * 100.0f),
        FMath::Max(4.0f, Scale.Y * 100.0f),
        FMath::Max(3.0f, Scale.Z * 100.0f));

    TArray<FVector> Vertices;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve(RingCount * SegmentCount + 2);
    UVs.Reserve(RingCount * SegmentCount + 2);
    VertexColors.Reserve(RingCount * SegmentCount + 2);
    Triangles.Reserve(RingCount * SegmentCount * 6);

    for (int32 RingIndex = 0; RingIndex < RingCount; ++RingIndex)
    {
        const float V = static_cast<float>(RingIndex) / static_cast<float>(RingCount);
        const float AngleFromBase = V * HALF_PI;
        const float RingRadius = FMath::Cos(AngleFromBase);
        const float Height = FMath::Sin(AngleFromBase);
        for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
        {
            const float U = static_cast<float>(SegmentIndex) / static_cast<float>(SegmentCount);
            const float Angle = U * 2.0f * PI;
            const float Noise =
                0.82f +
                0.20f * FMath::Sin(static_cast<float>(Seed) * 0.37f + static_cast<float>(RingIndex) * 1.19f + static_cast<float>(SegmentIndex) * 0.73f) +
                0.10f * FMath::Sin(static_cast<float>(Seed) * 0.11f - static_cast<float>(RingIndex) * 0.61f + static_cast<float>(SegmentIndex) * 1.47f);
            const float LocalX = FMath::Cos(Angle) * RingRadius * Radii.X * Noise;
            const float LocalY = FMath::Sin(Angle) * RingRadius * Radii.Y *
                (0.92f + 0.10f * FMath::Sin(static_cast<float>(Seed + SegmentIndex) * 0.53f));
            const float LocalZ = Height * Radii.Z *
                (0.88f + 0.10f * FMath::Sin(static_cast<float>(Seed) * 0.23f + static_cast<float>(SegmentIndex) * 0.91f));
            Vertices.Add(FVector(
                BaseLocation.X + LocalX * CosYaw - LocalY * SinYaw,
                BaseLocation.Y + LocalX * SinYaw + LocalY * CosYaw,
                BaseLocation.Z + LocalZ));
            UVs.Add(FVector2D(U, V));
            VertexColors.Add(ScalePreviewColor(Color, 0.58f + 0.10f * Noise + 0.03f * Height));
        }
    }

    const int32 TopIndex = Vertices.Num();
    Vertices.Add(FVector(BaseLocation.X, BaseLocation.Y, BaseLocation.Z + Radii.Z * 1.04f));
    UVs.Add(FVector2D(0.5f, 1.0f));
    VertexColors.Add(ScalePreviewColor(Color, 0.74f));

    const int32 BottomIndex = Vertices.Num();
    Vertices.Add(BaseLocation);
    UVs.Add(FVector2D(0.5f, 0.0f));
    VertexColors.Add(ScalePreviewColor(Color, 0.46f));

    for (int32 RingIndex = 0; RingIndex < RingCount - 1; ++RingIndex)
    {
        const int32 CurrentRing = RingIndex * SegmentCount;
        const int32 NextRing = (RingIndex + 1) * SegmentCount;
        for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
        {
            const int32 NextSegment = (SegmentIndex + 1) % SegmentCount;
            const int32 A = CurrentRing + SegmentIndex;
            const int32 B = CurrentRing + NextSegment;
            const int32 C = NextRing + SegmentIndex;
            const int32 D = NextRing + NextSegment;
            Triangles.Add(A);
            Triangles.Add(C);
            Triangles.Add(B);
            Triangles.Add(B);
            Triangles.Add(C);
            Triangles.Add(D);
        }
    }

    const int32 LastRing = (RingCount - 1) * SegmentCount;
    for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
    {
        const int32 NextSegment = (SegmentIndex + 1) % SegmentCount;
        Triangles.Add(LastRing + SegmentIndex);
        Triangles.Add(TopIndex);
        Triangles.Add(LastRing + NextSegment);

        Triangles.Add(BottomIndex);
        Triangles.Add(NextSegment);
        Triangles.Add(SegmentIndex);
    }

    const TArray<FVector> Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    return AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        Color,
        LoadOrCreatePreviewVertexColorMaterial(),
        &VertexColors);
}

AActor* AddPreviewProceduralLeafClusterActor(
    UWorld* World,
    const FString& Label,
    const FVector& BaseLocation,
    float YawDegrees,
    const FVector& Scale,
    const FLinearColor& Color,
    int32 Seed,
    bool bRainforest)
{
    if (!World)
    {
        return nullptr;
    }

    constexpr int32 RingCount = 5;
    constexpr int32 SegmentCount = 8;
    const float YawRadians = FMath::DegreesToRadians(YawDegrees);
    const float CosYaw = FMath::Cos(YawRadians);
    const float SinYaw = FMath::Sin(YawRadians);
    const float FirstPartyProceduralCanopyBlobDemotion = bRainforest ? 0.72f : 0.82f;
    const FVector Radii(
        FMath::Max(8.0f, Scale.X * 100.0f * FirstPartyProceduralCanopyBlobDemotion),
        FMath::Max(8.0f, Scale.Y * 100.0f * FirstPartyProceduralCanopyBlobDemotion),
        FMath::Max(6.0f, Scale.Z * 100.0f * (bRainforest ? 0.86f : 0.90f)));

    TArray<FVector> Vertices;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve(RingCount * SegmentCount + 2);
    UVs.Reserve(RingCount * SegmentCount + 2);
    VertexColors.Reserve(RingCount * SegmentCount + 2);
    Triangles.Reserve(RingCount * SegmentCount * 6);

    for (int32 RingIndex = 0; RingIndex < RingCount; ++RingIndex)
    {
        const float RingT = static_cast<float>(RingIndex) / static_cast<float>(RingCount - 1);
        const float LocalZUnit = FMath::Lerp(-0.58f, 0.72f, RingT);
        const float RingRadius = FMath::Sqrt(FMath::Max(0.0f, 1.0f - LocalZUnit * LocalZUnit));
        for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
        {
            const float SegmentT = static_cast<float>(SegmentIndex) / static_cast<float>(SegmentCount);
            const float Angle = SegmentT * 2.0f * PI;
            const float LobeNoise =
                0.72f +
                0.22f * FMath::Sin(static_cast<float>(Seed) * 0.31f + static_cast<float>(RingIndex) * 1.13f + static_cast<float>(SegmentIndex) * 0.91f) +
                0.18f * FMath::Sin(static_cast<float>(Seed) * 0.17f - static_cast<float>(RingIndex) * 0.47f + static_cast<float>(SegmentIndex) * 1.61f);
            const float LeafGap =
                0.90f + 0.12f * FMath::Sin(static_cast<float>(SegmentIndex) * (bRainforest ? 2.31f : 1.73f) + static_cast<float>(Seed) * 0.07f);
            const float LocalX = FMath::Cos(Angle) * RingRadius * Radii.X * LobeNoise;
            const float LocalY = FMath::Sin(Angle) * RingRadius * Radii.Y * LeafGap;
            const float LocalZ = LocalZUnit * Radii.Z *
                (0.86f + 0.14f * FMath::Sin(static_cast<float>(Seed) * 0.19f + static_cast<float>(SegmentIndex) * 0.67f));
            Vertices.Add(FVector(
                BaseLocation.X + LocalX * CosYaw - LocalY * SinYaw,
                BaseLocation.Y + LocalX * SinYaw + LocalY * CosYaw,
                BaseLocation.Z + LocalZ));
            UVs.Add(FVector2D(SegmentT, RingT));
            const float HeightTint = 0.82f + 0.16f * RingT;
            const float LeafTint = 0.82f + 0.12f * LobeNoise + (bRainforest ? 0.04f : 0.0f);
            VertexColors.Add(ScalePreviewColor(Color, HeightTint * LeafTint * (bRainforest ? 0.86f : 0.90f)));
        }
    }

    const int32 TopIndex = Vertices.Num();
    Vertices.Add(FVector(BaseLocation.X, BaseLocation.Y, BaseLocation.Z + Radii.Z * 0.86f));
    UVs.Add(FVector2D(0.5f, 1.0f));
    VertexColors.Add(ScalePreviewColor(Color, bRainforest ? 0.90f : 0.88f));

    const int32 BottomIndex = Vertices.Num();
    Vertices.Add(FVector(BaseLocation.X, BaseLocation.Y, BaseLocation.Z - Radii.Z * 0.56f));
    UVs.Add(FVector2D(0.5f, 0.0f));
    VertexColors.Add(ScalePreviewColor(Color, 0.58f));

    for (int32 RingIndex = 0; RingIndex < RingCount - 1; ++RingIndex)
    {
        const int32 CurrentRing = RingIndex * SegmentCount;
        const int32 NextRing = (RingIndex + 1) * SegmentCount;
        for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
        {
            const int32 NextSegment = (SegmentIndex + 1) % SegmentCount;
            const int32 A = CurrentRing + SegmentIndex;
            const int32 B = CurrentRing + NextSegment;
            const int32 C = NextRing + SegmentIndex;
            const int32 D = NextRing + NextSegment;
            Triangles.Add(A);
            Triangles.Add(C);
            Triangles.Add(B);
            Triangles.Add(B);
            Triangles.Add(C);
            Triangles.Add(D);
        }
    }

    const int32 FirstRing = 0;
    const int32 LastRing = (RingCount - 1) * SegmentCount;
    for (int32 SegmentIndex = 0; SegmentIndex < SegmentCount; ++SegmentIndex)
    {
        const int32 NextSegment = (SegmentIndex + 1) % SegmentCount;
        Triangles.Add(LastRing + SegmentIndex);
        Triangles.Add(TopIndex);
        Triangles.Add(LastRing + NextSegment);

        Triangles.Add(BottomIndex);
        Triangles.Add(FirstRing + NextSegment);
        Triangles.Add(FirstRing + SegmentIndex);
    }

    const TArray<FVector> Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    return AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        Color,
        LoadOrCreatePreviewVertexColorMaterial(),
        &VertexColors);
}

AActor* AddPreviewOrganicLeafSprayActor(
    UWorld* World,
    const FString& Label,
    const FVector& BaseLocation,
    float YawDegrees,
    const FVector& Scale,
    const FLinearColor& Color,
    int32 Seed,
    bool bRainforest)
{
    if (!World)
    {
        return nullptr;
    }

    const int32 LeafCount = bRainforest ? 18 : 12;
    const float YawRadians = FMath::DegreesToRadians(YawDegrees);
    const FVector BaseForward(FMath::Cos(YawRadians), FMath::Sin(YawRadians), 0.0f);
    const FVector BaseRight(-FMath::Sin(YawRadians), FMath::Cos(YawRadians), 0.0f);
    const FVector Up(0.0f, 0.0f, 1.0f);
    const FVector Radii(
        FMath::Max(16.0f, Scale.X * 100.0f),
        FMath::Max(12.0f, Scale.Y * 100.0f),
        FMath::Max(10.0f, Scale.Z * 100.0f));
    const float FoliageCardSilhouetteDemotion = bRainforest ? 0.62f : 0.70f;
    const float LeafCardWidthScale = bRainforest ? 0.54f : 0.62f;

    TArray<FVector> Vertices;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve(LeafCount * 4);
    UVs.Reserve(LeafCount * 4);
    VertexColors.Reserve(LeafCount * 4);
    Triangles.Reserve(LeafCount * 6);

    for (int32 LeafIndex = 0; LeafIndex < LeafCount; ++LeafIndex)
    {
        const float LeafT = static_cast<float>(LeafIndex) / static_cast<float>(FMath::Max(1, LeafCount - 1));
        const float Angle = YawRadians + static_cast<float>(LeafIndex) * (bRainforest ? 2.399f : 2.117f) +
            static_cast<float>(Seed) * 0.013f;
        const float RadialT = FMath::Sqrt(FMath::Frac(0.211f + 0.618034f * static_cast<float>(LeafIndex)));
        const float VerticalT = FMath::Sin(static_cast<float>(Seed) * 0.071f + static_cast<float>(LeafIndex) * 1.317f);
        const FVector RadialDir(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
        const FVector TangentDir = (RadialDir * (0.78f + 0.12f * FMath::Sin(LeafT * PI)) +
            Up * (bRainforest ? 0.34f : 0.22f) * FMath::Sin(Angle * 1.7f + static_cast<float>(Seed) * 0.031f)).GetSafeNormal();
        const FVector WidthDir = FVector::CrossProduct(TangentDir, Up).GetSafeNormal();
        const FVector FallbackWidthDir =
            (BaseRight * (0.72f + 0.18f * FMath::Sin(Angle)) + BaseForward * 0.18f).GetSafeNormal();
        const FVector LeafWidthDir = WidthDir.IsNearlyZero() ? FallbackWidthDir : WidthDir;

        const FVector LeafCenter = BaseLocation +
            RadialDir * (Radii.X * RadialT * (0.28f + 0.44f * FMath::Abs(FMath::Sin(Angle * 0.73f)))) +
            BaseRight * (Radii.Y * 0.20f * FMath::Sin(static_cast<float>(LeafIndex) * 1.91f + static_cast<float>(Seed) * 0.017f)) +
            Up * (Radii.Z * (0.14f + 0.52f * LeafT + 0.18f * VerticalT));
        const float LeafLength = Radii.X * (bRainforest ? 0.20f : 0.15f) * FoliageCardSilhouetteDemotion *
            (0.62f + 0.26f * FMath::Abs(FMath::Sin(static_cast<float>(LeafIndex) * 0.83f + static_cast<float>(Seed) * 0.029f)));
        const float LeafWidth = Radii.Y * (bRainforest ? 0.050f : 0.040f) * LeafCardWidthScale *
            (0.78f + 0.18f * FMath::Abs(FMath::Cos(static_cast<float>(LeafIndex) * 1.23f)));
        const float TipLift = Radii.Z * (bRainforest ? 0.030f : 0.020f) *
            FMath::Sin(static_cast<float>(LeafIndex) * 0.61f + static_cast<float>(Seed) * 0.043f);

        const int32 BaseVertexIndex = Vertices.Num();
        Vertices.Add(LeafCenter - TangentDir * LeafLength - LeafWidthDir * LeafWidth);
        Vertices.Add(LeafCenter - TangentDir * LeafLength * 0.30f + LeafWidthDir * LeafWidth * 0.82f + Up * TipLift);
        Vertices.Add(LeafCenter + TangentDir * LeafLength + LeafWidthDir * LeafWidth * 0.34f + Up * TipLift * 1.4f);
        Vertices.Add(LeafCenter + TangentDir * LeafLength * 0.22f - LeafWidthDir * LeafWidth * 0.92f);
        UVs.Add(FVector2D(0.0f, 0.0f));
        UVs.Add(FVector2D(0.0f, 1.0f));
        UVs.Add(FVector2D(1.0f, 1.0f));
        UVs.Add(FVector2D(1.0f, 0.0f));

        const float LeafShade = 0.76f + 0.20f * LeafT +
            0.10f * FMath::Sin(static_cast<float>(Seed) * 0.037f + static_cast<float>(LeafIndex) * 0.97f);
        const FLinearColor InnerLeafColor = ScalePreviewColor(Color, LeafShade * (bRainforest ? 0.92f : 0.88f));
        const FLinearColor OuterLeafColor = ScalePreviewColor(Color, LeafShade * (bRainforest ? 0.92f : 0.90f));
        VertexColors.Add(InnerLeafColor);
        VertexColors.Add(OuterLeafColor);
        VertexColors.Add(ScalePreviewColor(OuterLeafColor, 0.96f));
        VertexColors.Add(ScalePreviewColor(InnerLeafColor, 0.90f));

        Triangles.Add(BaseVertexIndex);
        Triangles.Add(BaseVertexIndex + 1);
        Triangles.Add(BaseVertexIndex + 2);
        Triangles.Add(BaseVertexIndex);
        Triangles.Add(BaseVertexIndex + 2);
        Triangles.Add(BaseVertexIndex + 3);
    }

    const TArray<FVector> Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    AActor* Actor = AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        Color,
        LoadOrCreatePreviewVertexColorMaterial(),
        &VertexColors);
    if (Actor)
    {
        TArray<UProceduralMeshComponent*> MeshComponents;
        Actor->GetComponents<UProceduralMeshComponent>(MeshComponents);
        for (UProceduralMeshComponent* MeshComponent : MeshComponents)
        {
            if (MeshComponent)
            {
                MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            }
        }
    }
    return Actor;
}

AActor* AddPreviewOrganicBranchFrondActor(
    UWorld* World,
    const FString& Label,
    const FVector& BaseLocation,
    float YawDegrees,
    const FVector& Scale,
    const FLinearColor& Color,
    int32 Seed,
    bool bRainforest,
    bool bUnderstory)
{
    if (!World)
    {
        return nullptr;
    }

    const float YawRadians = FMath::DegreesToRadians(YawDegrees);
    const FVector BaseForward(FMath::Cos(YawRadians), FMath::Sin(YawRadians), 0.0f);
    const FVector BaseRight(-FMath::Sin(YawRadians), FMath::Cos(YawRadians), 0.0f);
    const FVector Up(0.0f, 0.0f, 1.0f);
    const FVector Radii(
        FMath::Max(18.0f, Scale.X * 100.0f),
        FMath::Max(14.0f, Scale.Y * 100.0f),
        FMath::Max(12.0f, Scale.Z * 100.0f));
    const int32 BranchCount = bRainforest ? (bUnderstory ? 7 : 9) : (bUnderstory ? 5 : 7);
    const int32 LeavesPerBranch = bRainforest ? (bUnderstory ? 6 : 8) : (bUnderstory ? 4 : 6);

    TArray<FVector> Vertices;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve(BranchCount * (LeavesPerBranch * 4 + 8));
    UVs.Reserve(BranchCount * (LeavesPerBranch * 4 + 8));
    VertexColors.Reserve(BranchCount * (LeavesPerBranch * 4 + 8));
    Triangles.Reserve(BranchCount * (LeavesPerBranch * 6 + 12));

    auto AddQuad = [&Vertices, &UVs, &VertexColors, &Triangles](
                       const FVector& A,
                       const FVector& B,
                       const FVector& C,
                       const FVector& D,
                       const FLinearColor& ColorA,
                       const FLinearColor& ColorB)
    {
        const int32 BaseVertexIndex = Vertices.Num();
        Vertices.Add(A);
        Vertices.Add(B);
        Vertices.Add(C);
        Vertices.Add(D);
        UVs.Add(FVector2D(0.0f, 0.0f));
        UVs.Add(FVector2D(0.0f, 1.0f));
        UVs.Add(FVector2D(1.0f, 1.0f));
        UVs.Add(FVector2D(1.0f, 0.0f));
        VertexColors.Add(ColorA);
        VertexColors.Add(ColorA);
        VertexColors.Add(ColorB);
        VertexColors.Add(ColorB);
        Triangles.Add(BaseVertexIndex);
        Triangles.Add(BaseVertexIndex + 1);
        Triangles.Add(BaseVertexIndex + 2);
        Triangles.Add(BaseVertexIndex);
        Triangles.Add(BaseVertexIndex + 2);
        Triangles.Add(BaseVertexIndex + 3);
    };

    const FLinearColor BranchColor = ScalePreviewColor(
        bRainforest ? FLinearColor(0.018f, 0.020f, 0.014f) : FLinearColor(0.115f, 0.072f, 0.038f),
        bUnderstory ? 0.82f : 0.92f);
    for (int32 BranchIndex = 0; BranchIndex < BranchCount; ++BranchIndex)
    {
        const float BranchT = static_cast<float>(BranchIndex) / static_cast<float>(FMath::Max(1, BranchCount - 1));
        const float Angle = YawRadians +
            (BranchT - 0.5f) * (bRainforest ? 2.8f : 2.2f) +
            FMath::Sin(static_cast<float>(Seed) * 0.023f + static_cast<float>(BranchIndex) * 1.71f) * 0.48f;
        const FVector RadialDir(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
        const FVector BranchDir = (RadialDir * (bRainforest ? 0.78f : 0.86f) +
                                   Up * (bRainforest ? (bUnderstory ? 0.34f : 0.48f) : (bUnderstory ? 0.25f : 0.36f)))
                                      .GetSafeNormal();
        const FVector WidthDirRaw = FVector::CrossProduct(BranchDir, Up).GetSafeNormal();
        const FVector WidthDir = WidthDirRaw.IsNearlyZero() ? BaseRight : WidthDirRaw;
        const float BranchLength = Radii.X * (bRainforest ? 0.72f : 0.56f) *
            (0.78f + 0.18f * FMath::Abs(FMath::Sin(static_cast<float>(Seed) * 0.031f + static_cast<float>(BranchIndex) * 0.83f)));
        const FVector BranchBase = BaseLocation +
            BaseRight * (Radii.Y * 0.20f * FMath::Sin(static_cast<float>(BranchIndex) * 1.19f + static_cast<float>(Seed) * 0.017f)) +
            Up * (Radii.Z * (bUnderstory ? 0.08f : 0.16f) * FMath::Sin(static_cast<float>(BranchIndex) * 0.67f));
        const float BranchHalfWidth = FMath::Max(1.8f, Radii.Y * (bRainforest ? 0.010f : 0.012f));

        const FVector BranchMid = BranchBase + BranchDir * (BranchLength * 0.52f) +
            Up * (Radii.Z * 0.10f * FMath::Sin(static_cast<float>(BranchIndex) * 1.37f));
        const FVector BranchTip = BranchBase + BranchDir * BranchLength +
            RadialDir * (Radii.Y * 0.10f * FMath::Sin(static_cast<float>(Seed) * 0.011f + static_cast<float>(BranchIndex))) +
            Up * (Radii.Z * (bRainforest ? 0.12f : 0.07f));
        AddQuad(
            BranchBase - WidthDir * BranchHalfWidth,
            BranchBase + WidthDir * BranchHalfWidth,
            BranchMid + WidthDir * BranchHalfWidth * 0.70f,
            BranchMid - WidthDir * BranchHalfWidth * 0.70f,
            BranchColor,
            ScalePreviewColor(BranchColor, 0.78f));
        AddQuad(
            BranchMid - WidthDir * BranchHalfWidth * 0.70f,
            BranchMid + WidthDir * BranchHalfWidth * 0.70f,
            BranchTip + WidthDir * BranchHalfWidth * 0.36f,
            BranchTip - WidthDir * BranchHalfWidth * 0.36f,
            ScalePreviewColor(BranchColor, 0.82f),
            ScalePreviewColor(BranchColor, 0.58f));

        for (int32 LeafIndex = 0; LeafIndex < LeavesPerBranch; ++LeafIndex)
        {
            const float LeafT = (static_cast<float>(LeafIndex) + 1.0f) / static_cast<float>(LeavesPerBranch + 1);
            const float SideSign = (LeafIndex % 2 == 0) ? -1.0f : 1.0f;
            const FVector LeafForward = (BranchDir * 0.72f + RadialDir * (0.22f * SideSign) + Up * (bRainforest ? 0.10f : 0.06f)).GetSafeNormal();
            const FVector LeafWidthDirRaw = FVector::CrossProduct(LeafForward, Up).GetSafeNormal();
            const FVector LeafWidthDir = LeafWidthDirRaw.IsNearlyZero() ? WidthDir : LeafWidthDirRaw;
            const float LeafNoise =
                0.72f +
                0.18f * FMath::Sin(static_cast<float>(Seed) * 0.037f + static_cast<float>(LeafIndex) * 1.27f) +
                0.12f * FMath::Sin(static_cast<float>(BranchIndex) * 1.09f + static_cast<float>(LeafIndex) * 0.73f);
            const FVector LeafCenter = BranchBase +
                BranchDir * (BranchLength * LeafT) +
                WidthDir * (SideSign * Radii.Y * (bRainforest ? 0.055f : 0.045f) * (0.8f + LeafT)) +
                Up * (Radii.Z * 0.045f * FMath::Sin(static_cast<float>(LeafIndex) * 1.53f + static_cast<float>(Seed) * 0.019f));
            const float LeafLength = Radii.X * (bRainforest ? 0.075f : 0.058f) *
                (0.72f + 0.22f * FMath::Abs(LeafNoise));
            const float LeafHalfWidth = Radii.Y * (bRainforest ? 0.024f : 0.020f) *
                (0.66f + 0.18f * FMath::Abs(FMath::Cos(static_cast<float>(LeafIndex) * 0.91f)));
            const float Shade = 0.70f + 0.22f * LeafT + 0.08f * FMath::Sin(static_cast<float>(Seed) * 0.041f + static_cast<float>(LeafIndex) * 0.61f);
            const FLinearColor LeafBaseColor = ScalePreviewColor(Color, Shade * (bRainforest ? 0.78f : 0.76f));
            const FLinearColor LeafTipColor = ScalePreviewColor(Color, Shade * (bRainforest ? 0.94f : 0.88f));
            AddQuad(
                LeafCenter - LeafForward * LeafLength * 0.70f,
                LeafCenter + LeafWidthDir * LeafHalfWidth,
                LeafCenter + LeafForward * LeafLength + Up * (LeafLength * 0.12f),
                LeafCenter - LeafWidthDir * LeafHalfWidth,
                LeafBaseColor,
                LeafTipColor);
        }
    }

    const TArray<FVector> Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    AActor* Actor = AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        Color,
        LoadOrCreatePreviewVertexColorMaterial(),
        &VertexColors);
    if (Actor)
    {
        TArray<UProceduralMeshComponent*> MeshComponents;
        Actor->GetComponents<UProceduralMeshComponent>(MeshComponents);
        for (UProceduralMeshComponent* MeshComponent : MeshComponents)
        {
            if (MeshComponent)
            {
                MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            }
        }
    }
    return Actor;
}

AActor* AddPreviewFineTwigCanopyLaceActor(
    UWorld* World,
    const FString& Label,
    const FVector& BaseLocation,
    float YawDegrees,
    const FVector& Scale,
    const FLinearColor& Color,
    int32 Seed,
    bool bRainforest)
{
    if (!World)
    {
        return nullptr;
    }

    const float YawRadians = FMath::DegreesToRadians(YawDegrees);
    const FVector BaseForward(FMath::Cos(YawRadians), FMath::Sin(YawRadians), 0.0f);
    const FVector BaseRight(-FMath::Sin(YawRadians), FMath::Cos(YawRadians), 0.0f);
    const FVector Up(0.0f, 0.0f, 1.0f);
    const FVector Radii(
        FMath::Max(20.0f, Scale.X * 100.0f),
        FMath::Max(16.0f, Scale.Y * 100.0f),
        FMath::Max(14.0f, Scale.Z * 100.0f));
    const int32 TwigCount = bRainforest ? 20 : 14;
    const int32 LeafletsPerTwig = bRainforest ? 5 : 4;

    TArray<FVector> Vertices;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve(TwigCount * (LeafletsPerTwig + 2) * 4);
    UVs.Reserve(TwigCount * (LeafletsPerTwig + 2) * 4);
    VertexColors.Reserve(TwigCount * (LeafletsPerTwig + 2) * 4);
    Triangles.Reserve(TwigCount * (LeafletsPerTwig + 2) * 6);

    auto AddQuad = [&Vertices, &UVs, &VertexColors, &Triangles](
                       const FVector& A,
                       const FVector& B,
                       const FVector& C,
                       const FVector& D,
                       const FLinearColor& ColorA,
                       const FLinearColor& ColorB)
    {
        const int32 BaseVertexIndex = Vertices.Num();
        Vertices.Add(A);
        Vertices.Add(B);
        Vertices.Add(C);
        Vertices.Add(D);
        UVs.Add(FVector2D(0.0f, 0.0f));
        UVs.Add(FVector2D(0.0f, 1.0f));
        UVs.Add(FVector2D(1.0f, 1.0f));
        UVs.Add(FVector2D(1.0f, 0.0f));
        VertexColors.Add(ColorA);
        VertexColors.Add(ColorA);
        VertexColors.Add(ColorB);
        VertexColors.Add(ColorB);
        Triangles.Add(BaseVertexIndex);
        Triangles.Add(BaseVertexIndex + 1);
        Triangles.Add(BaseVertexIndex + 2);
        Triangles.Add(BaseVertexIndex);
        Triangles.Add(BaseVertexIndex + 2);
        Triangles.Add(BaseVertexIndex + 3);
    };

    const FLinearColor TwigColor = bRainforest
        ? FLinearColor(0.014f, 0.020f, 0.012f)
        : FLinearColor(0.075f, 0.052f, 0.030f);
    for (int32 TwigIndex = 0; TwigIndex < TwigCount; ++TwigIndex)
    {
        const float TwigT = static_cast<float>(TwigIndex) / static_cast<float>(FMath::Max(1, TwigCount - 1));
        const float Angle = YawRadians + static_cast<float>(TwigIndex) * (bRainforest ? 2.033f : 2.417f) +
            static_cast<float>(Seed) * 0.019f;
        const FVector RadialDir(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
        const FVector SweepDir = (RadialDir * (0.70f + 0.10f * FMath::Sin(TwigT * PI)) +
                                  BaseForward * (0.10f * FMath::Sin(static_cast<float>(TwigIndex) * 0.91f)) +
                                  Up * (bRainforest ? 0.42f : 0.30f))
                                     .GetSafeNormal();
        const FVector WidthDirRaw = FVector::CrossProduct(SweepDir, Up).GetSafeNormal();
        const FVector WidthDir = WidthDirRaw.IsNearlyZero() ? BaseRight : WidthDirRaw;
        const float RadiusT = FMath::Sqrt(FMath::Frac(0.173f + 0.618034f * static_cast<float>(TwigIndex)));
        const FVector TwigRoot = BaseLocation +
            RadialDir * (Radii.X * RadiusT * 0.18f) +
            BaseRight * (Radii.Y * 0.18f * FMath::Sin(static_cast<float>(Seed) * 0.011f + static_cast<float>(TwigIndex) * 1.73f)) +
            Up * (Radii.Z * (0.10f + 0.28f * TwigT));
        const float TwigLength = Radii.X * (bRainforest ? 0.46f : 0.36f) *
            (0.72f + 0.18f * FMath::Abs(FMath::Sin(static_cast<float>(Seed) * 0.023f + static_cast<float>(TwigIndex) * 0.79f)));
        const float TwigHalfWidth = FMath::Max(0.85f, Radii.Y * (bRainforest ? 0.0045f : 0.0055f));
        const FVector TwigMid = TwigRoot + SweepDir * (TwigLength * 0.56f) +
            Up * (Radii.Z * 0.045f * FMath::Sin(static_cast<float>(TwigIndex) * 1.37f));
        const FVector TwigTip = TwigRoot + SweepDir * TwigLength +
            RadialDir * (Radii.Y * 0.08f * FMath::Sin(static_cast<float>(Seed) * 0.017f + static_cast<float>(TwigIndex))) +
            Up * (Radii.Z * (bRainforest ? 0.070f : 0.045f));

        AddQuad(
            TwigRoot - WidthDir * TwigHalfWidth,
            TwigRoot + WidthDir * TwigHalfWidth,
            TwigMid + WidthDir * TwigHalfWidth * 0.58f,
            TwigMid - WidthDir * TwigHalfWidth * 0.58f,
            ScalePreviewColor(TwigColor, 0.90f),
            ScalePreviewColor(TwigColor, 0.68f));
        AddQuad(
            TwigMid - WidthDir * TwigHalfWidth * 0.58f,
            TwigMid + WidthDir * TwigHalfWidth * 0.58f,
            TwigTip + WidthDir * TwigHalfWidth * 0.22f,
            TwigTip - WidthDir * TwigHalfWidth * 0.22f,
            ScalePreviewColor(TwigColor, 0.74f),
            ScalePreviewColor(TwigColor, 0.50f));

        for (int32 LeafletIndex = 0; LeafletIndex < LeafletsPerTwig; ++LeafletIndex)
        {
            const float LeafT = (static_cast<float>(LeafletIndex) + 1.0f) / static_cast<float>(LeafletsPerTwig + 1);
            const float SideSign = (LeafletIndex % 2 == 0) ? -1.0f : 1.0f;
            const FVector LeafForward = (SweepDir * 0.68f + RadialDir * (0.24f * SideSign) + Up * (bRainforest ? 0.12f : 0.06f)).GetSafeNormal();
            const FVector LeafWidthDirRaw = FVector::CrossProduct(LeafForward, Up).GetSafeNormal();
            const FVector LeafWidthDir = LeafWidthDirRaw.IsNearlyZero() ? WidthDir : LeafWidthDirRaw;
            const FVector LeafCenter = TwigRoot +
                SweepDir * (TwigLength * LeafT) +
                WidthDir * (SideSign * Radii.Y * (bRainforest ? 0.030f : 0.024f) * (0.70f + LeafT)) +
                Up * (Radii.Z * 0.030f * FMath::Sin(static_cast<float>(LeafletIndex) * 1.41f + static_cast<float>(Seed) * 0.031f));
            const float LeafLength = Radii.X * (bRainforest ? 0.036f : 0.028f) *
                (0.70f + 0.16f * FMath::Abs(FMath::Sin(static_cast<float>(TwigIndex) * 0.83f + static_cast<float>(LeafletIndex))));
            const float LeafHalfWidth = Radii.Y * (bRainforest ? 0.012f : 0.009f) *
                (0.68f + 0.14f * FMath::Abs(FMath::Cos(static_cast<float>(LeafletIndex) * 0.91f + static_cast<float>(Seed) * 0.013f)));
            const float LeafShade = 0.64f + 0.22f * LeafT +
                0.08f * FMath::Sin(static_cast<float>(Seed) * 0.037f + static_cast<float>(TwigIndex) * 0.53f + static_cast<float>(LeafletIndex));
            const FLinearColor LeafBaseColor = ScalePreviewColor(Color, LeafShade * (bRainforest ? 0.74f : 0.70f));
            const FLinearColor LeafTipColor = ScalePreviewColor(Color, LeafShade * (bRainforest ? 0.92f : 0.84f));
            AddQuad(
                LeafCenter - LeafForward * LeafLength * 0.72f,
                LeafCenter + LeafWidthDir * LeafHalfWidth,
                LeafCenter + LeafForward * LeafLength + Up * (LeafLength * 0.10f),
                LeafCenter - LeafWidthDir * LeafHalfWidth,
                LeafBaseColor,
                LeafTipColor);
        }
    }

    const TArray<FVector> Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    AActor* Actor = AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        Color,
        LoadOrCreatePreviewVertexColorMaterial(),
        &VertexColors);
    if (Actor)
    {
        TArray<UProceduralMeshComponent*> MeshComponents;
        Actor->GetComponents<UProceduralMeshComponent>(MeshComponents);
        for (UProceduralMeshComponent* MeshComponent : MeshComponents)
        {
            if (MeshComponent)
            {
                MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            }
        }
    }
    return Actor;
}

void AddPreviewFoliageCrownDepthAndLeafletBreakupDetail(
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

    const bool bRainforest = Spec.bHasWaterfalls;
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float RemainingBlockyFoliageProxyCull = 0.38f;
    const int32 CrownCount = Spec.bDesertCanyon ? 10 : (bRainforest ? 32 : 20);
    const int32 ShadowQuadsPerCrown = 1;
    const int32 LeafletsPerCrown = Spec.bDesertCanyon ? 3 : (bRainforest ? 7 : 5);
    const float NearBankOffset = Spec.bDesertCanyon ? 1120.0f : (bRainforest ? 700.0f : 720.0f);
    const float FarBankOffset = Spec.bDesertCanyon ? 2200.0f : (bRainforest ? 1680.0f : 1260.0f);
    const float FoliageCardSilhouetteDemotion =
        (Spec.bDesertCanyon ? 0.66f : (bRainforest ? 0.42f : 0.48f)) * RemainingBlockyFoliageProxyCull;
    const float FirstPartyProceduralCanopyBlobDemotion =
        Spec.bDesertCanyon ? 0.64f : (bRainforest ? 0.48f : 0.54f);
    const FVector Up(0.0f, 0.0f, 1.0f);

    TArray<FVector> Vertices;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve(CrownCount * (ShadowQuadsPerCrown + LeafletsPerCrown) * 4);
    UVs.Reserve(CrownCount * (ShadowQuadsPerCrown + LeafletsPerCrown) * 4);
    VertexColors.Reserve(CrownCount * (ShadowQuadsPerCrown + LeafletsPerCrown) * 4);
    Triangles.Reserve(CrownCount * (ShadowQuadsPerCrown + LeafletsPerCrown) * 6);

    auto AddQuad = [&Vertices, &UVs, &VertexColors, &Triangles](
                       const FVector& A,
                       const FVector& B,
                       const FVector& C,
                       const FVector& D,
                       const FLinearColor& ColorA,
                       const FLinearColor& ColorB)
    {
        const int32 BaseVertexIndex = Vertices.Num();
        Vertices.Add(A);
        Vertices.Add(B);
        Vertices.Add(C);
        Vertices.Add(D);
        UVs.Add(FVector2D(0.0f, 0.0f));
        UVs.Add(FVector2D(0.0f, 1.0f));
        UVs.Add(FVector2D(1.0f, 1.0f));
        UVs.Add(FVector2D(1.0f, 0.0f));
        VertexColors.Add(ColorA);
        VertexColors.Add(ScalePreviewColor(ColorA, 0.94f));
        VertexColors.Add(ColorB);
        VertexColors.Add(ScalePreviewColor(ColorB, 0.90f));
        Triangles.Add(BaseVertexIndex);
        Triangles.Add(BaseVertexIndex + 1);
        Triangles.Add(BaseVertexIndex + 2);
        Triangles.Add(BaseVertexIndex);
        Triangles.Add(BaseVertexIndex + 2);
        Triangles.Add(BaseVertexIndex + 3);
    };

    for (int32 CrownIndex = 0; CrownIndex < CrownCount; ++CrownIndex)
    {
        const float T = static_cast<float>(CrownIndex) / static_cast<float>(FMath::Max(1, CrownCount - 1));
        const float Phase = static_cast<float>(CrownIndex) * 1.237f;
        const float Side = (CrownIndex % 2 == 0) ? -1.0f : 1.0f;
        const float BaseX = FMath::Lerp(2700.0f, 26050.0f, T) +
            220.0f * FMath::Sin(Phase * 1.09f) +
            90.0f * FMath::Sin(Phase * 0.41f);
        const float OffsetWave = FMath::Pow(
            FMath::Abs(FMath::Sin(Phase * (Spec.bDesertCanyon ? 0.58f : 0.63f))),
            Spec.bDesertCanyon ? 0.72f : 0.48f);
        const float BaseOffset = ActiveRiverHalfWidth + NearBankOffset + FarBankOffset * OffsetWave;

        float X = BaseX;
        float SignedOffset = Side * BaseOffset;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 6; ++CandidateIndex)
        {
            const float CandidateX = BaseX + 185.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 0.93f);
            const float CandidateOffset = FMath::Max(
                ActiveRiverHalfWidth + NearBankOffset * 0.70f,
                BaseOffset + 215.0f * FMath::Sin(Phase * 0.46f + static_cast<float>(CandidateIndex) * 1.17f));
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
            const float BankPreference =
                1.0f - FMath::Clamp(
                    FMath::Abs(CandidateOffset - (ActiveRiverHalfWidth + NearBankOffset + FarBankOffset * 0.34f)) /
                        FMath::Max(1.0f, FarBankOffset),
                    0.0f,
                    1.0f);
            const float Score = Spec.bDesertCanyon
                ? BankPreference * 0.82f + (1.0f - WaterT) * 0.44f + (1.0f - VegetationT) * 0.08f
                : BankPreference * 0.58f + VegetationT * (bRainforest ? 1.44f : 1.02f) - WaterT * 0.58f;
            if (Score > BestScore)
            {
                BestScore = Score;
                X = CandidateX;
                SignedOffset = Side * CandidateOffset;
            }
        }

        if (X < 3150.0f && FMath::Abs(SignedOffset) < ActiveRiverHalfWidth + 1060.0f)
        {
            continue;
        }

        const float Y = GetPreviewRiverCenterY(Spec, X) + SignedOffset;
        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
        const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, X, Y);
        const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, Y);
        const float YawDegrees = static_cast<float>((CrownIndex * 47) % 360);
        const float YawRadians = FMath::DegreesToRadians(YawDegrees);
        const FVector BaseForward(FMath::Cos(YawRadians), FMath::Sin(YawRadians), 0.0f);
        const FVector BaseRight(-FMath::Sin(YawRadians), FMath::Cos(YawRadians), 0.0f);
        const FVector CrownCenter(
            X,
            Y,
            TerrainZ + (Spec.bDesertCanyon ? 82.0f : (bRainforest ? 350.0f : 214.0f)) +
                18.0f * FMath::Sin(Phase));
        const float CrownRadiusX = (Spec.bDesertCanyon ? 70.0f : (bRainforest ? 210.0f : 138.0f)) * FirstPartyProceduralCanopyBlobDemotion;
        const float CrownRadiusY = (Spec.bDesertCanyon ? 42.0f : (bRainforest ? 148.0f : 96.0f)) * FirstPartyProceduralCanopyBlobDemotion;
        const float CrownRadiusZ = (Spec.bDesertCanyon ? 42.0f : (bRainforest ? 145.0f : 86.0f)) * (Spec.bDesertCanyon ? 0.88f : (bRainforest ? 0.78f : 0.82f));
        const FLinearColor CanopyLow = Spec.bDesertCanyon
            ? FLinearColor(0.19f, 0.20f, 0.10f)
            : (bRainforest ? FLinearColor(0.014f, 0.070f, 0.024f) : FLinearColor(0.070f, 0.150f, 0.045f));
        const FLinearColor CanopyHigh = Spec.bDesertCanyon
            ? FLinearColor(0.38f, 0.35f, 0.18f)
            : (bRainforest ? FLinearColor(0.070f, 0.245f, 0.060f) : FLinearColor(0.165f, 0.280f, 0.080f));
        const FLinearColor CrownBaseColor = ScalePreviewColor(
            FMath::Lerp(CanopyLow, FMath::Lerp(Spec.FoliageColor, CanopyHigh, 0.50f), 0.48f + VegetationT * 0.30f),
            0.78f + 0.06f * static_cast<float>(CrownIndex % 5) - WaterT * 0.05f);
        const FLinearColor CrownShadowColor = Spec.bDesertCanyon
            ? ScalePreviewColor(FLinearColor(0.090f, 0.090f, 0.050f), 0.78f)
            : ScalePreviewColor(
                  bRainforest ? FLinearColor(0.008f, 0.025f, 0.012f) : FLinearColor(0.030f, 0.055f, 0.022f),
                  0.86f);

        for (int32 ShadowIndex = 0; ShadowIndex < ShadowQuadsPerCrown; ++ShadowIndex)
        {
            const float ShadowT =
                (static_cast<float>(ShadowIndex) + 1.0f) / static_cast<float>(ShadowQuadsPerCrown + 1);
            const float Angle = YawRadians +
                (ShadowT - 0.5f) * (bRainforest ? 2.20f : 1.65f) +
                0.35f * FMath::Sin(Phase + static_cast<float>(ShadowIndex));
            const FVector RadialDir(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const FVector WidthDir = (BaseRight * 0.68f + RadialDir * 0.32f).GetSafeNormal();
            const FVector ShadowCenter = CrownCenter +
                RadialDir * (CrownRadiusX * (0.10f + 0.18f * ShadowT)) -
                BaseForward * (CrownRadiusY * 0.10f) -
                Up * (CrownRadiusZ * (0.18f + 0.08f * FMath::Sin(Phase)));
            const float ShadowWidth =
                CrownRadiusY * (Spec.bDesertCanyon ? 0.36f : (bRainforest ? 0.58f : 0.50f)) * FoliageCardSilhouetteDemotion;
            const float ShadowHeight =
                CrownRadiusZ * (Spec.bDesertCanyon ? 0.50f : (bRainforest ? 0.64f : 0.58f)) * FoliageCardSilhouetteDemotion;
            AddQuad(
                ShadowCenter - WidthDir * ShadowWidth - Up * ShadowHeight * 0.48f,
                ShadowCenter + WidthDir * ShadowWidth - Up * ShadowHeight * 0.40f,
                ShadowCenter + WidthDir * ShadowWidth * 0.78f + Up * ShadowHeight * 0.48f,
                ShadowCenter - WidthDir * ShadowWidth * 0.72f + Up * ShadowHeight * 0.42f,
                ScalePreviewColor(CrownShadowColor, 0.74f + ShadowT * 0.08f),
                ScalePreviewColor(CrownBaseColor, 0.54f + ShadowT * 0.10f));
        }

        for (int32 LeafletIndex = 0; LeafletIndex < LeafletsPerCrown; ++LeafletIndex)
        {
            const float LeafT = static_cast<float>(LeafletIndex) / static_cast<float>(FMath::Max(1, LeafletsPerCrown - 1));
            const float Angle = YawRadians +
                static_cast<float>(LeafletIndex) * (bRainforest ? 2.399f : 2.117f) +
                static_cast<float>(CrownIndex) * 0.037f;
            const float RadialT = FMath::Sqrt(FMath::Frac(0.257f + 0.618034f * static_cast<float>(LeafletIndex)));
            const FVector RadialDir(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const FVector LeafForward =
                (RadialDir * (0.78f + 0.10f * FMath::Sin(LeafT * PI)) +
                 BaseForward * (0.12f * FMath::Sin(Phase + static_cast<float>(LeafletIndex) * 0.77f)) +
                 Up * (Spec.bDesertCanyon ? 0.08f : (bRainforest ? 0.30f : 0.20f)))
                    .GetSafeNormal();
            const FVector LeafWidthDirRaw = FVector::CrossProduct(LeafForward, Up).GetSafeNormal();
            const FVector LeafWidthDir = LeafWidthDirRaw.IsNearlyZero() ? BaseRight : LeafWidthDirRaw;
            const FVector LeafCenter = CrownCenter +
                RadialDir * (CrownRadiusX * (0.22f + 0.58f * RadialT)) +
                BaseRight * (CrownRadiusY * 0.16f * FMath::Sin(Phase * 0.73f + static_cast<float>(LeafletIndex) * 1.31f)) +
                Up * (CrownRadiusZ * (-0.18f + 0.70f * LeafT + 0.12f * FMath::Sin(Angle)));
            const float LeafLength = CrownRadiusX * (Spec.bDesertCanyon ? 0.16f : (bRainforest ? 0.12f : 0.11f)) *
                FoliageCardSilhouetteDemotion *
                (0.70f + 0.20f * FMath::Abs(FMath::Sin(Phase + static_cast<float>(LeafletIndex) * 0.91f)));
            const float LeafHalfWidth = CrownRadiusY * (Spec.bDesertCanyon ? 0.038f : (bRainforest ? 0.026f : 0.030f)) *
                (Spec.bDesertCanyon ? 0.72f : (bRainforest ? 0.52f : 0.58f)) *
                (0.70f + 0.16f * FMath::Abs(FMath::Cos(Angle * 0.73f)));
            const float Shade = 0.66f + 0.24f * LeafT +
                0.08f * FMath::Sin(Phase * 0.91f + static_cast<float>(LeafletIndex) * 0.83f);
            const FLinearColor LeafBaseColor = ScalePreviewColor(CrownBaseColor, Shade * (bRainforest ? 0.74f : 0.78f));
            const FLinearColor LeafTipColor = ScalePreviewColor(CrownBaseColor, Shade * (bRainforest ? 0.88f : 0.86f));
            AddQuad(
                LeafCenter - LeafForward * LeafLength * 0.74f,
                LeafCenter + LeafWidthDir * LeafHalfWidth,
                LeafCenter + LeafForward * LeafLength + Up * (LeafLength * (bRainforest ? 0.16f : 0.10f)),
                LeafCenter - LeafWidthDir * LeafHalfWidth,
                LeafBaseColor,
                LeafTipColor);
        }
    }

    if (Vertices.IsEmpty() || Triangles.IsEmpty())
    {
        return;
    }

    const TArray<FVector> Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    AActor* Actor = AddPreviewProceduralMeshActor(
        World,
        FString::Printf(TEXT("RaftSim_FoliageCrownDepthAndLeafletBreakup_%s"), *Spec.RiverId),
        Vertices,
        Triangles,
        Normals,
        UVs,
        Spec.FoliageColor,
        LoadOrCreatePreviewVertexColorMaterial(),
        &VertexColors);
    if (Actor)
    {
        TArray<UProceduralMeshComponent*> MeshComponents;
        Actor->GetComponents<UProceduralMeshComponent>(MeshComponents);
        for (UProceduralMeshComponent* MeshComponent : MeshComponents)
        {
            if (MeshComponent)
            {
                MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            }
        }
    }
}

void AddPreviewBoulderSurfaceFacet(
    UWorld* World,
    const FString& Label,
    const FVector& Center,
    const FVector& LongAxis,
    const FVector& ShortAxis,
    const FLinearColor& InnerColor,
    const FLinearColor& OuterColor)
{
    if (!World)
    {
        return;
    }

    TArray<FVector> Vertices;
    Vertices.Add(Center - LongAxis - ShortAxis * 0.70f);
    Vertices.Add(Center - LongAxis * 0.35f + ShortAxis);
    Vertices.Add(Center + LongAxis + ShortAxis * 0.62f);
    Vertices.Add(Center + LongAxis * 0.48f - ShortAxis);

    TArray<int32> Triangles = {0, 1, 2, 0, 2, 3};
    TArray<FVector> Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    TArray<FVector2D> UVs = {
        FVector2D(0.0f, 0.0f),
        FVector2D(0.0f, 1.0f),
        FVector2D(1.0f, 1.0f),
        FVector2D(1.0f, 0.0f)};
    TArray<FLinearColor> VertexColors = {
        ScalePreviewColor(InnerColor, 0.88f),
        ScalePreviewColor(OuterColor, 0.96f),
        ScalePreviewColor(OuterColor, 1.08f),
        ScalePreviewColor(InnerColor, 1.02f)};

    AActor* Actor = AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        InnerColor,
        LoadOrCreatePreviewVertexColorMaterial(),
        &VertexColors);
    if (Actor)
    {
        TArray<UProceduralMeshComponent*> MeshComponents;
        Actor->GetComponents<UProceduralMeshComponent>(MeshComponents);
        for (UProceduralMeshComponent* MeshComponent : MeshComponents)
        {
            if (MeshComponent)
            {
                MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            }
        }
    }
}

void AddPreviewBoulderSurfaceVariationDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FVector& BaseLocation,
    float YawDegrees,
    const FVector& Scale,
    int32 BoulderIndex,
    float WaterMaskT,
    float VegetationMaskT,
    bool bNearCameraReviewBoulder)
{
    if (!World)
    {
        return;
    }

    const float YawRadians = FMath::DegreesToRadians(YawDegrees);
    const FVector Forward(FMath::Cos(YawRadians), FMath::Sin(YawRadians), 0.0f);
    const FVector Right(-FMath::Sin(YawRadians), FMath::Cos(YawRadians), 0.0f);
    const float RadiusX = FMath::Max(18.0f, Scale.X * 100.0f);
    const float RadiusY = FMath::Max(12.0f, Scale.Y * 100.0f);
    const float RadiusZ = FMath::Max(8.0f, Scale.Z * 100.0f);
    const float Wetness = FMath::Clamp(0.22f + WaterMaskT * 0.62f, 0.0f, 0.86f);
    const float MossSediment = FMath::Clamp((Spec.bHasWaterfalls ? 0.28f : 0.08f) + VegetationMaskT * 0.48f, 0.0f, 0.70f);
    const float NearCameraFacetScale = bNearCameraReviewBoulder ? (Spec.bDesertCanyon ? 0.58f : 0.48f) : 1.0f;

    const FLinearColor WetFacet = FMath::Lerp(
        ScalePreviewColor(Spec.RockColor, Spec.bDesertCanyon ? 0.44f : 0.34f),
        ScalePreviewColor(Spec.WaterColor, Spec.bDesertCanyon ? 0.38f : 0.30f),
        Spec.bDesertCanyon ? 0.22f : 0.44f);
    const FLinearColor WetHighlight = Spec.bDesertCanyon
        ? FLinearColor(0.42f, 0.36f, 0.25f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.08f, 0.22f, 0.17f) : FLinearColor(0.34f, 0.38f, 0.31f));
    const FLinearColor Abrasion = Spec.bDesertCanyon
        ? FLinearColor(0.68f, 0.52f, 0.33f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.17f, 0.19f, 0.16f) : FLinearColor(0.48f, 0.46f, 0.38f));
    const FLinearColor TopHighlight = Spec.bDesertCanyon
        ? FLinearColor(0.66f, 0.52f, 0.34f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.16f, 0.20f, 0.15f) : FLinearColor(0.48f, 0.47f, 0.38f));
    const FLinearColor MossOrSediment = Spec.bDesertCanyon
        ? FLinearColor(0.42f, 0.30f, 0.16f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.035f, 0.16f, 0.055f) : FLinearColor(0.18f, 0.25f, 0.11f));
    const FLinearColor CreviceShadow = Spec.bDesertCanyon
        ? FLinearColor(0.15f, 0.10f, 0.065f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.010f, 0.028f, 0.020f) : FLinearColor(0.10f, 0.10f, 0.080f));

    const FVector UpLift(0.0f, 0.0f, 1.0f);
    const FVector WetCenter = BaseLocation +
        Forward * (RadiusX * (0.12f + 0.10f * FMath::Sin(static_cast<float>(BoulderIndex)))) -
        Right * (RadiusY * (0.60f + 0.12f * FMath::Cos(static_cast<float>(BoulderIndex) * 0.71f))) +
        UpLift * (RadiusZ * (0.26f + Wetness * 0.24f) + 4.0f);
    AddPreviewBoulderSurfaceFacet(
        World,
        FString::Printf(TEXT("RaftSim_BoulderWetSheenFacet_%02d_%s"), BoulderIndex, *Spec.RiverId),
        WetCenter,
        Forward * (RadiusX * (0.22f + 0.10f * Wetness)),
        (Right * (RadiusY * 0.10f) + UpLift * (RadiusZ * 0.035f)),
        WetFacet,
        ScalePreviewColor(FMath::Lerp(WetFacet, WetHighlight, 0.36f + Wetness * 0.28f), NearCameraFacetScale));

    const FVector AbrasionCenter = BaseLocation +
        Forward * (RadiusX * (0.10f + 0.22f * FMath::Sin(static_cast<float>(BoulderIndex) * 0.57f))) +
        Right * (RadiusY * (0.42f + 0.10f * FMath::Sin(static_cast<float>(BoulderIndex) * 1.11f))) +
        UpLift * (RadiusZ * 0.58f + 8.0f);
    AddPreviewBoulderSurfaceFacet(
        World,
        FString::Printf(TEXT("RaftSim_BoulderAbrasionFacet_%02d_%s"), BoulderIndex, *Spec.RiverId),
        AbrasionCenter,
        (Forward * (RadiusX * 0.18f) + UpLift * (RadiusZ * 0.045f)),
        Right * (RadiusY * 0.10f),
        FMath::Lerp(ScalePreviewColor(Spec.RockColor, 0.64f), Abrasion, 0.38f),
        ScalePreviewColor(Abrasion, NearCameraFacetScale));

    const FVector TopCenter = BaseLocation +
        Forward * (RadiusX * (0.02f + 0.16f * FMath::Sin(static_cast<float>(BoulderIndex) * 0.41f))) +
        Right * (RadiusY * (0.04f + 0.12f * FMath::Cos(static_cast<float>(BoulderIndex) * 0.73f))) +
        UpLift * (RadiusZ * 0.96f + 10.0f);
    AddPreviewBoulderSurfaceFacet(
        World,
        FString::Printf(TEXT("RaftSim_BoulderTopHighlightFacet_%02d_%s"), BoulderIndex, *Spec.RiverId),
        TopCenter,
        Forward * (RadiusX * 0.34f),
        Right * (RadiusY * 0.18f),
        ScalePreviewColor(FMath::Lerp(Abrasion, TopHighlight, 0.28f), NearCameraFacetScale),
        ScalePreviewColor(TopHighlight, bNearCameraReviewBoulder ? NearCameraFacetScale * 0.82f : 1.0f));

    const FVector MossCenter = BaseLocation -
        Forward * (RadiusX * (0.18f + 0.06f * FMath::Cos(static_cast<float>(BoulderIndex) * 0.63f))) +
        Right * (RadiusY * (0.18f - 0.34f * FMath::Sin(static_cast<float>(BoulderIndex) * 0.83f))) +
        UpLift * (RadiusZ * (0.36f + MossSediment * 0.30f) + 5.0f);
    AddPreviewBoulderSurfaceFacet(
        World,
        FString::Printf(TEXT("RaftSim_BoulderMossSedimentFacet_%02d_%s"), BoulderIndex, *Spec.RiverId),
        MossCenter,
        Forward * (RadiusX * (0.15f + MossSediment * 0.08f)),
        (Right * (RadiusY * 0.12f) + UpLift * (RadiusZ * 0.030f)),
        FMath::Lerp(ScalePreviewColor(Spec.RockColor, 0.40f), MossOrSediment, MossSediment),
        MossOrSediment);

    const FVector CreviceCenter = BaseLocation -
        Forward * (RadiusX * (0.06f + 0.14f * FMath::Sin(static_cast<float>(BoulderIndex) * 0.49f))) -
        Right * (RadiusY * (0.34f + 0.10f * FMath::Cos(static_cast<float>(BoulderIndex) * 1.17f))) +
        UpLift * (RadiusZ * (0.30f + Wetness * 0.12f) + 3.0f);
    AddPreviewBoulderSurfaceFacet(
        World,
        FString::Printf(TEXT("RaftSim_BoulderCreviceShadowFacet_%02d_%s"), BoulderIndex, *Spec.RiverId),
        CreviceCenter,
        Forward * (RadiusX * (0.18f + 0.05f * Wetness)),
        (Right * (RadiusY * 0.075f) + UpLift * (RadiusZ * 0.020f)),
        CreviceShadow,
        FMath::Lerp(CreviceShadow, ScalePreviewColor(Spec.RockColor, 0.30f), 0.28f));
}

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
    UMaterialInterface* MaterialOverride = nullptr,
    const FRaftSimPreviewImage* SolverVisualizationFields = nullptr,
    UMaterialInterface* SolverFoamMaterial = nullptr)
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
    bool bClampAboveWaterSurface = false)
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

void DisablePreviewProceduralMeshCollision(AActor* Actor)
{
    if (!Actor)
    {
        return;
    }

    TArray<UProceduralMeshComponent*> MeshComponents;
    Actor->GetComponents<UProceduralMeshComponent>(MeshComponents);
    for (UProceduralMeshComponent* MeshComponent : MeshComponents)
    {
        if (MeshComponent)
        {
            MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        }
    }
}

void AddPreviewSourceMaskedShorelineLipOverhangDetail(
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

    constexpr int32 SegmentSteps = 18;
    constexpr int32 CrossSteps = 4;
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float WetBankScale = FMath::Max(0.35f, Spec.FlowWetBankScale);
    const float WaterSurfaceZ = GetPreviewWaterSurfaceBaseZCm(Spec);
    const int32 LipCount = Spec.bDesertCanyon ? 78 : (Spec.bHasWaterfalls ? 104 : 88);
    const FLinearColor InnerWetShadow = Spec.bDesertCanyon
        ? FLinearColor(0.205f, 0.150f, 0.092f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.015f, 0.050f, 0.030f) : FLinearColor(0.055f, 0.082f, 0.060f));
    const FLinearColor LipFaceColor = Spec.bDesertCanyon
        ? FLinearColor(0.365f, 0.245f, 0.145f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.034f, 0.086f, 0.042f) : FLinearColor(0.130f, 0.128f, 0.092f));
    const FLinearColor OuterBankColor = Spec.bDesertCanyon
        ? FLinearColor(0.560f, 0.390f, 0.230f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.060f, 0.128f, 0.052f) : FLinearColor(0.210f, 0.190f, 0.128f));

    for (int32 LipIndex = 0; LipIndex < LipCount; ++LipIndex)
    {
        const float SequenceT = FMath::Frac(0.113f + 0.618034f * static_cast<float>(LipIndex));
        const float Side = (LipIndex % 2 == 0) ? -1.0f : 1.0f;
        const float Phase = static_cast<float>(LipIndex) * 0.923f + (Spec.bHasWaterfalls ? 0.37f : 0.0f);
        const float BaseX = FMath::Lerp(-5200.0f, 25700.0f, SequenceT) +
            145.0f * FMath::Sin(Phase * 1.41f) +
            62.0f * FMath::Sin(Phase * 0.53f);

        float SelectedX = BaseX;
        float SelectedOffset = ActiveRiverHalfWidth + 32.0f * WetBankScale;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 6; ++CandidateIndex)
        {
            const float CandidateX = BaseX +
                74.0f * FMath::Sin(Phase * 0.81f + static_cast<float>(CandidateIndex) * 1.13f);
            const float CandidateOffset = ActiveRiverHalfWidth + WetBankScale *
                (-12.0f + 22.0f * static_cast<float>(CandidateIndex) +
                 30.0f * FMath::Abs(FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 0.71f)));
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
            const float EdgePreference = 1.0f -
                FMath::Clamp(
                    FMath::Abs(CandidateOffset - (ActiveRiverHalfWidth + 34.0f * WetBankScale)) /
                        FMath::Max(1.0f, 128.0f * WetBankScale),
                    0.0f,
                    1.0f);
            const float WetToePreference = 1.0f - FMath::Clamp(FMath::Abs(WaterT - 0.48f) / 0.52f, 0.0f, 1.0f);
            const float Score = EdgePreference * 1.42f + WetToePreference * 0.42f + WaterT * 0.22f -
                VegetationT * (Spec.bDesertCanyon ? 0.12f : 0.46f) +
                0.04f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.77f);
            if (Score > BestScore)
            {
                BestScore = Score;
                SelectedX = CandidateX;
                SelectedOffset = CandidateOffset;
            }
        }

        const float PatchLength = (Spec.bDesertCanyon ? 720.0f : (Spec.bHasWaterfalls ? 470.0f : 560.0f)) *
            (0.70f + 0.08f * static_cast<float>(LipIndex % 7));
        const float PatchWidth = (Spec.bDesertCanyon ? 116.0f : (Spec.bHasWaterfalls ? 84.0f : 94.0f)) *
            WetBankScale * (0.76f + 0.06f * static_cast<float>(LipIndex % 5));
        const float WaterOverlap = (Spec.bDesertCanyon ? 38.0f : 30.0f) * WetBankScale *
            (0.70f + 0.08f * static_cast<float>(LipIndex % 4));

        TArray<FVector> Vertices;
        TArray<FVector> Normals;
        TArray<FVector2D> UVs;
        TArray<FLinearColor> VertexColors;
        TArray<int32> Triangles;
        Vertices.Reserve((SegmentSteps + 1) * (CrossSteps + 1));
        Normals.Reserve((SegmentSteps + 1) * (CrossSteps + 1));
        UVs.Reserve((SegmentSteps + 1) * (CrossSteps + 1));
        VertexColors.Reserve((SegmentSteps + 1) * (CrossSteps + 1));
        Triangles.Reserve(SegmentSteps * CrossSteps * 6);

        for (int32 SegmentIndex = 0; SegmentIndex <= SegmentSteps; ++SegmentIndex)
        {
            const float U = static_cast<float>(SegmentIndex) / static_cast<float>(SegmentSteps);
            const float LongTaper = FMath::Sin(U * PI);
            const float X = SelectedX - PatchLength * 0.50f + PatchLength * U +
                FMath::Sin(Phase * 0.61f + U * UE_TWO_PI * 1.3f) * PatchWidth * 0.16f * LongTaper;
            const float CenterY = GetPreviewRiverCenterY(Spec, X);
            const float EdgeMeander = WetBankScale *
                (18.0f * FMath::Sin(Phase + U * UE_TWO_PI * 1.15f) +
                 9.0f * FMath::Sin(Phase * 0.33f + U * UE_TWO_PI * 2.70f));

            for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
            {
                const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
                const float InnerT = 1.0f - V;
                const float CrossOffset = FMath::Lerp(-WaterOverlap, PatchWidth - WaterOverlap, V);
                const float EdgeScallop =
                    FMath::Sin(Phase * 1.19f + U * UE_TWO_PI * 2.2f + V * 3.1f) * PatchWidth * 0.045f +
                    FMath::Sin(Phase * 0.47f + U * UE_TWO_PI * 4.8f) * PatchWidth * 0.026f * InnerT;
                const float Offset = SelectedOffset + EdgeMeander + CrossOffset + EdgeScallop;
                const float Y = CenterY + Side * Offset;
                const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
                const float SourceWaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, Y);
                const float SourceVegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, X, Y);
                const float LipCrownT = FMath::Sin(V * PI) * LongTaper;
                const float WetEdgeLift = FMath::Lerp(2.0f, Spec.bDesertCanyon ? 9.0f : 7.0f, V);
                const float LipLift = WetEdgeLift + LipCrownT * (Spec.bDesertCanyon ? 10.0f : 7.5f);
                const float Z = FMath::Max(
                    TerrainZ + LipLift,
                    WaterSurfaceZ + 1.8f + InnerT * (Spec.bDesertCanyon ? 1.7f : 1.2f));
                const float Fleck = FMath::Clamp(
                    0.84f + 0.10f * FMath::Sin(Phase + U * 7.2f) + 0.06f * FMath::Sin(Phase * 0.73f + V * 5.4f),
                    0.66f,
                    1.04f);
                const FLinearColor InnerToFace = FMath::Lerp(InnerWetShadow, LipFaceColor, FMath::Clamp(V * 1.35f, 0.0f, 1.0f));
                FLinearColor LipColor = FMath::Lerp(InnerToFace, OuterBankColor, SmoothPreviewStep(0.48f, 1.0f, V));
                LipColor = FMath::Lerp(
                    LipColor,
                    ScalePreviewColor(Spec.WaterColor, Spec.bDesertCanyon ? 0.32f : 0.24f),
                    FMath::Clamp(SourceWaterT * InnerT * 0.28f, 0.0f, 0.30f));
                LipColor = FMath::Lerp(
                    LipColor,
                    ScalePreviewColor(Spec.FoliageColor, Spec.bHasWaterfalls ? 0.42f : 0.28f),
                    FMath::Clamp(SourceVegetationT * V * (Spec.bDesertCanyon ? 0.08f : 0.22f), 0.0f, 0.24f));

                Vertices.Add(FVector(X, Y, Z));
                UVs.Add(FVector2D(U * 5.2f, V));
                VertexColors.Add(NormalizePreviewTerrainProxyPatchColor(Spec, ScalePreviewColor(LipColor, Fleck)));
            }
        }

        const int32 RowSize = CrossSteps + 1;
        for (int32 SegmentIndex = 0; SegmentIndex < SegmentSteps; ++SegmentIndex)
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
        AActor* LipActor = AddPreviewProceduralMeshActor(
            World,
            FString::Printf(TEXT("RaftSim_SourceMaskedShorelineLipOverhang_%03d_%s"), LipIndex, *Spec.RiverId),
            Vertices,
            Triangles,
            Normals,
            UVs,
            LipFaceColor,
            LoadOrCreatePreviewTerrainVertexColorMaterial(),
            &VertexColors);
        DisablePreviewProceduralMeshCollision(LipActor);
    }
}

void AddPreviewSourceMaskedBankBarMicrogeometryDetail(
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
    const float WaterSurfaceZ = GetPreviewWaterSurfaceBaseZCm(Spec);
    const int32 BarPebbleCount = Spec.bDesertCanyon ? 178 : (Spec.bHasWaterfalls ? 150 : 132);
    const int32 SlopeFlakeCount = Spec.bDesertCanyon ? 128 : (Spec.bHasWaterfalls ? 156 : 118);

    for (int32 PebbleIndex = 0; PebbleIndex < BarPebbleCount; ++PebbleIndex)
    {
        const float T = FMath::Frac(0.073f + 0.618034f * static_cast<float>(PebbleIndex));
        const float Side = (PebbleIndex % 2 == 0) ? -1.0f : 1.0f;
        const float Phase = static_cast<float>(PebbleIndex) * 1.173f;
        const float BaseX = FMath::Lerp(-4200.0f, 25800.0f, T) +
            135.0f * FMath::Sin(Phase * 1.31f) +
            70.0f * FMath::Sin(Phase * 0.47f);

        float X = BaseX;
        float Y = GetPreviewRiverCenterY(Spec, X) + Side * (ActiveRiverHalfWidth + 150.0f * WetBankScale);
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 5; ++CandidateIndex)
        {
            const float CandidateX = BaseX + 92.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.07f);
            const float CandidateOffset = ActiveRiverHalfWidth + WetBankScale *
                (70.0f + 58.0f * static_cast<float>(CandidateIndex) +
                 96.0f * FMath::Abs(FMath::Sin(Phase * 0.83f + static_cast<float>(CandidateIndex) * 0.37f)));
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
            const float ExposedBarT =
                1.0f - FMath::Clamp(FMath::Abs(CandidateOffset - (ActiveRiverHalfWidth + 185.0f * WetBankScale)) /
                                         FMath::Max(1.0f, 320.0f * WetBankScale),
                                     0.0f,
                                     1.0f);
            const float WetToeT = 1.0f - FMath::Clamp(FMath::Abs(WaterT - 0.36f) / 0.54f, 0.0f, 1.0f);
            const float Score = ExposedBarT * 1.30f + WetToeT * 0.36f - VegetationT * (Spec.bHasWaterfalls ? 0.42f : 0.58f) +
                0.04f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.9f);
            if (Score > BestScore)
            {
                BestScore = Score;
                X = CandidateX;
                Y = CandidateY;
            }
        }

        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
        const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, Y);
        const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, X, Y);
        const float SizeNoise = 0.72f + 0.10f * static_cast<float>(PebbleIndex % 7) +
            0.08f * FMath::Abs(FMath::Sin(Phase));
        const FVector Scale = Spec.bDesertCanyon
            ? FVector(0.105f * SizeNoise, 0.058f * SizeNoise, 0.012f * SizeNoise)
            : FVector(
                  (Spec.bHasWaterfalls ? 0.072f : 0.082f) * SizeNoise,
                  (Spec.bHasWaterfalls ? 0.046f : 0.050f) * SizeNoise,
                  0.010f * SizeNoise);
        const FLinearColor DryBarColor = Spec.bDesertCanyon
            ? FMath::Lerp(FLinearColor(0.44f, 0.31f, 0.20f), FLinearColor(0.62f, 0.48f, 0.31f), 0.32f + 0.16f * FMath::Sin(Phase))
            : (Spec.bHasWaterfalls
                  ? FMath::Lerp(FLinearColor(0.038f, 0.055f, 0.044f), FLinearColor(0.085f, 0.105f, 0.060f), VegetationT * 0.48f)
                  : FMath::Lerp(FLinearColor(0.15f, 0.145f, 0.112f), FLinearColor(0.25f, 0.225f, 0.155f), 0.26f + VegetationT * 0.26f));
        const FLinearColor WetBarColor = FMath::Lerp(
            ScalePreviewColor(Spec.RockColor, Spec.bDesertCanyon ? 0.45f : 0.38f),
            ScalePreviewColor(Spec.WaterColor, Spec.bDesertCanyon ? 0.34f : 0.30f),
            Spec.bDesertCanyon ? 0.24f : 0.42f);
        const FLinearColor BarColor = FMath::Lerp(
            DryBarColor,
            WetBarColor,
            FMath::Clamp(0.18f + WaterT * 0.46f, 0.0f, 0.62f));

        AActor* PebbleActor = AddPreviewIrregularRockActor(
            World,
            FString::Printf(TEXT("RaftSim_SourceMaskedExposedBarMicroPebble_%03d_%s"), PebbleIndex, *Spec.RiverId),
            FVector(X, Y, FMath::Max(TerrainZ + 5.5f, WaterSurfaceZ + 2.0f)),
            static_cast<float>((PebbleIndex * 31) % 360),
            Scale,
            ScalePreviewColor(BarColor, 0.86f + 0.05f * static_cast<float>(PebbleIndex % 5)),
            PebbleIndex + 9100);
        DisablePreviewProceduralMeshCollision(PebbleActor);
    }

    for (int32 FlakeIndex = 0; FlakeIndex < SlopeFlakeCount; ++FlakeIndex)
    {
        const float T = FMath::Frac(0.191f + 0.618034f * static_cast<float>(FlakeIndex));
        const float Side = (FlakeIndex % 2 == 0) ? -1.0f : 1.0f;
        const float Phase = static_cast<float>(FlakeIndex) * 1.407f;
        const float BaseX = FMath::Lerp(-4500.0f, 25700.0f, T) +
            180.0f * FMath::Sin(Phase * 0.91f) +
            85.0f * FMath::Sin(Phase * 1.61f);
        const float NearOffset = Spec.bDesertCanyon ? 560.0f : (Spec.bHasWaterfalls ? 360.0f : 380.0f);
        const float FarOffset = Spec.bDesertCanyon ? 2480.0f : (Spec.bHasWaterfalls ? 1180.0f : 1020.0f);

        float X = BaseX;
        float SignedOffset = Side * (ActiveRiverHalfWidth + NearOffset);
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 5; ++CandidateIndex)
        {
            const float OffsetWave = FMath::Pow(
                FMath::Abs(FMath::Sin(Phase * 0.59f + static_cast<float>(CandidateIndex) * 0.73f)),
                Spec.bDesertCanyon ? 0.82f : 0.58f);
            const float CandidateOffset = ActiveRiverHalfWidth + NearOffset + FarOffset * OffsetWave;
            const float CandidateX = BaseX + 190.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.23f);
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
            const float SlopeT = SmoothPreviewStep(
                ActiveRiverHalfWidth + NearOffset * 0.60f,
                ActiveRiverHalfWidth + NearOffset + FarOffset * 0.86f,
                CandidateOffset);
            const float Score = Spec.bDesertCanyon
                ? SlopeT * 0.98f + (1.0f - WaterT) * 0.34f - VegetationT * 0.18f
                : SlopeT * 0.56f + VegetationT * (Spec.bHasWaterfalls ? 0.66f : 0.38f) + (1.0f - WaterT) * 0.24f;
            if (Score > BestScore)
            {
                BestScore = Score;
                X = CandidateX;
                SignedOffset = Side * CandidateOffset;
            }
        }

        const float Y = GetPreviewRiverCenterY(Spec, X) + SignedOffset;
        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
        const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, Y);
        const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, X, Y);
        const float SizeNoise = 0.74f + 0.09f * static_cast<float>(FlakeIndex % 6) +
            0.07f * FMath::Abs(FMath::Sin(Phase * 0.77f));
        const FVector Scale = Spec.bDesertCanyon
            ? FVector(0.155f * SizeNoise, 0.036f * SizeNoise, 0.009f * SizeNoise)
            : FVector(
                  (Spec.bHasWaterfalls ? 0.112f : 0.124f) * SizeNoise,
                  (Spec.bHasWaterfalls ? 0.032f : 0.034f) * SizeNoise,
                  0.008f * SizeNoise);
        const FLinearColor SlopeBaseColor = Spec.bDesertCanyon
            ? FMath::Lerp(FLinearColor(0.32f, 0.22f, 0.14f), FLinearColor(0.55f, 0.40f, 0.25f), 0.34f + 0.18f * FMath::Sin(Phase))
            : (Spec.bHasWaterfalls
                  ? FMath::Lerp(FLinearColor(0.030f, 0.055f, 0.035f), FLinearColor(0.065f, 0.135f, 0.055f), VegetationT * 0.58f)
                  : FMath::Lerp(FLinearColor(0.18f, 0.165f, 0.118f), FLinearColor(0.27f, 0.25f, 0.155f), VegetationT * 0.32f));
        const FLinearColor SlopeWetColor = FMath::Lerp(
            ScalePreviewColor(Spec.RockColor, Spec.bDesertCanyon ? 0.50f : 0.42f),
            ScalePreviewColor(Spec.WaterColor, Spec.bDesertCanyon ? 0.26f : 0.24f),
            Spec.bDesertCanyon ? 0.16f : 0.28f);
        const FLinearColor FlakeColor = FMath::Lerp(
            SlopeBaseColor,
            SlopeWetColor,
            FMath::Clamp(WaterT * 0.22f, 0.0f, 0.34f));

        AActor* FlakeActor = AddPreviewIrregularRockActor(
            World,
            FString::Printf(TEXT("RaftSim_SourceMaskedBankSlopeMaterialFlake_%03d_%s"), FlakeIndex, *Spec.RiverId),
            FVector(X, Y, TerrainZ + (Spec.bDesertCanyon ? 9.0f : 7.0f)),
            static_cast<float>((FlakeIndex * 43) % 360),
            Scale,
            ScalePreviewColor(FlakeColor, 0.82f + 0.05f * static_cast<float>(FlakeIndex % 6)),
            FlakeIndex + 11700);
        DisablePreviewProceduralMeshCollision(FlakeActor);
    }
}

void AddPreviewProceduralBankTextureCards(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask,
    UStaticMesh* PlaneMesh)
{
    if (!World || !PlaneMesh)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float RemainingSquareSourceCardCull = 0.54f;
    const float RemainingSquareCardOpacityDemotion = 0.42f;
    const float SquareFoliageSourceCardArtifactDemotion = 0.16f;
    const int32 CardsPerSide = Spec.bDesertCanyon ? 14 : (Spec.bHasWaterfalls ? 18 : 16);
    const float NearBankOffset = Spec.bDesertCanyon ? 520.0f : 260.0f;
    const float FarBankOffset = Spec.bDesertCanyon ? 1880.0f : (Spec.bHasWaterfalls ? 1180.0f : 980.0f);
    const float FoliageCardVisibilityBreakupT = Spec.bHasWaterfalls ? 0.09f : 0.12f;

    for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
    {
        const float Side = SideIndex == 0 ? -1.0f : 1.0f;
        for (int32 CardIndex = 0; CardIndex < CardsPerSide; ++CardIndex)
        {
            const float T = static_cast<float>(CardIndex) / static_cast<float>(FMath::Max(1, CardsPerSide - 1));
            const float Phase = static_cast<float>(CardIndex) * 1.618f + static_cast<float>(SideIndex) * 0.73f;
            const float BaseX = FMath::Lerp(-5050.0f, 25400.0f, T) +
                210.0f * FMath::Sin(Phase * 1.21f) +
                90.0f * FMath::Sin(Phase * 0.37f);
            const float BaseOffset = ActiveRiverHalfWidth + NearBankOffset +
                FarBankOffset * FMath::Pow(FMath::Abs(FMath::Sin(Phase * 0.83f)), Spec.bDesertCanyon ? 0.72f : 0.58f);
            float X = BaseX;
            float Y = GetPreviewRiverCenterY(Spec, X) + Side * BaseOffset;
            float BestScore = -1000.0f;
            for (int32 CandidateIndex = 0; CandidateIndex < 4; ++CandidateIndex)
            {
                const float CandidateX = BaseX +
                    115.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.19f);
                const float CandidateOffset = BaseOffset +
                    Side * 155.0f * FMath::Cos(Phase * 0.67f + static_cast<float>(CandidateIndex) * 1.41f);
                const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
                const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, CandidateX, CandidateY);
                const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY);
                const float Score = Spec.bDesertCanyon
                    ? (0.35f - WaterT * 0.55f + 0.20f * FMath::Sin(Phase + static_cast<float>(CandidateIndex)))
                    : (VegetationT * 1.55f - WaterT * 0.90f +
                          0.06f * FMath::Sin(Phase + static_cast<float>(CandidateIndex)));
                if (Score > BestScore)
                {
                    BestScore = Score;
                    X = CandidateX;
                    Y = CandidateY;
                }
            }

            const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMask, X, Y);
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, Y);
            const bool bCanopyCard =
                Spec.bHasWaterfalls &&
                CardIndex % 13 == 0 &&
                BaseOffset < ActiveRiverHalfWidth + NearBankOffset + FarBankOffset * 0.48f;
            const float Noise = 0.86f + 0.10f * FMath::Sin(Phase * 1.77f) + 0.05f * FMath::Sin(Phase * 0.43f);

            FLinearColor GroundColor;
            if (Spec.bDesertCanyon)
            {
                GroundColor = FMath::Lerp(
                    FLinearColor(0.32f, 0.22f, 0.14f),
                    FLinearColor(0.56f, 0.42f, 0.25f),
                    FMath::Clamp(0.35f + 0.24f * FMath::Sin(Phase * 0.91f), 0.0f, 1.0f));
            }
            else if (Spec.bHasWaterfalls)
            {
                GroundColor = FMath::Lerp(
                    FLinearColor(0.025f, 0.075f, 0.035f),
                    FLinearColor(0.075f, 0.19f, 0.070f),
                    FMath::Clamp(0.28f + VegetationT * 0.64f, 0.0f, 1.0f));
            }
            else
            {
                GroundColor = FMath::Lerp(
                    FLinearColor(0.12f, 0.11f, 0.075f),
                    FLinearColor(0.22f, 0.30f, 0.12f),
                    FMath::Clamp(0.22f + VegetationT * 0.55f, 0.0f, 1.0f));
            }
            GroundColor = FMath::Lerp(
                GroundColor,
                ScalePreviewColor(Spec.WaterColor, 0.45f),
                FMath::Clamp(WaterT * 0.18f, 0.0f, 0.24f));
            GroundColor = ScalePreviewColor(GroundColor, Noise);

            const float Yaw = static_cast<float>((CardIndex * 47 + SideIndex * 113) % 360);
            if (bCanopyCard)
            {
                const FLinearColor CanopyCardColor = ScalePreviewColor(
                    FMath::Lerp(GroundColor, Spec.FoliageColor, Spec.bHasWaterfalls ? 0.62f : 0.48f),
                    (Spec.bHasWaterfalls ? 0.82f : 0.90f) * FoliageCardVisibilityBreakupT);
                AddPreviewOrganicBranchFrondActor(
                    World,
                    FString::Printf(TEXT("RaftSim_MaskAwareCanopyCardOrganicCull_%03d_%s"), CardIndex + SideIndex * CardsPerSide, *Spec.RiverId),
                    FVector(X, Y, TerrainZ + 82.0f),
                    Yaw,
                    FVector(
                        (0.32f + 0.08f * FMath::Abs(FMath::Sin(Phase))) * RemainingSquareSourceCardCull,
                        0.30f * RemainingSquareSourceCardCull,
                        0.36f * RemainingSquareSourceCardCull),
                    CanopyCardColor,
                    CardIndex + SideIndex * 97 + 18100,
                    true,
                    true);
            }
            else
            {
                AddPreviewTranslucentMeshActor(
                    World,
                    PlaneMesh,
                    FString::Printf(TEXT("RaftSim_MaskAwareGroundCover_%03d_%s"), CardIndex + SideIndex * CardsPerSide, *Spec.RiverId),
                    FVector(X, Y, TerrainZ + (Spec.bDesertCanyon ? 18.0f : 15.0f)),
                    FRotator(0.0f, Yaw, 0.0f),
                    FVector(
                        (Spec.bDesertCanyon ? 0.74f : (Spec.bHasWaterfalls ? 0.66f : 0.54f)) *
                            SquareFoliageSourceCardArtifactDemotion,
                        (Spec.bDesertCanyon ? 0.28f : (Spec.bHasWaterfalls ? 0.32f : 0.26f)) * 0.28f,
                        1.0f),
                    GroundColor,
                    (Spec.bDesertCanyon ? 0.09f : (Spec.bHasWaterfalls ? 0.08f : 0.085f)) *
                        RemainingSquareCardOpacityDemotion);
            }
        }
    }
}

void AddPreviewFoamRibbon(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FString& Label,
    float StartX,
    float Length,
    float LateralOffset,
    float Width,
    float Phase,
    const FLinearColor& Color)
{
    if (!World)
    {
        return;
    }

    constexpr int32 Segments = 28;
    TArray<FVector> Vertices;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve(Segments * 6);
    UVs.Reserve(Segments * 6);
    VertexColors.Reserve(Segments * 6);
    Triangles.Reserve(Segments * 12);

    const float RibbonMidX = StartX + Length * 0.50f;
    const float RemainingWaterOverlaySlabDemotion = SmoothPreviewStep(5600.0f, 10800.0f, RibbonMidX);
    const float PaleFoamSlashArtifactDemotion = 0.26f;
    const float FoamRailContinuityBreakupT =
        FMath::Lerp(0.62f, 0.42f, RemainingWaterOverlaySlabDemotion);
    const bool bNearFrameWaterRibbon = RibbonMidX < 7800.0f;
    const float NearFrameRibbonWidthScale =
        FMath::Lerp(0.08f, 0.31f, RemainingWaterOverlaySlabDemotion) *
        PaleFoamSlashArtifactDemotion;
    const FLinearColor RibbonColor = ClampPreviewColor(FMath::Lerp(
        Spec.WaterColor,
        Color,
        FMath::Lerp(Spec.bDesertCanyon ? 0.030f : 0.034f, Spec.bDesertCanyon ? 0.18f : 0.16f, RemainingWaterOverlaySlabDemotion) *
            PaleFoamSlashArtifactDemotion));

    auto AddFoamLaceCrossSection = [&](float T, float WidthFade, float SegmentFade) -> int32
    {
        const float X = StartX + Length * T;
        const float RiverCenterY = GetPreviewRiverCenterY(Spec, X);
        const float Sway = FMath::Sin(Phase + T * UE_TWO_PI) * Width * 0.32f * NearFrameRibbonWidthScale;
        const float Taper = FMath::Sin(T * PI);
        const float LocalHalfWidth =
            FMath::Max(1.1f, Width * NearFrameRibbonWidthScale * (0.10f + 0.50f * Taper) * WidthFade);
        const float CenterY = RiverCenterY + LateralOffset + Sway;
        const float SurfaceWave = FMath::Sin(X * 0.011f + CenterY * 0.015f) * (Spec.bDesertCanyon ? 2.0f : 4.5f);
        const float Z = GetPreviewWaterSurfaceBaseZCm(Spec) + (bNearFrameWaterRibbon ? 5.0f : 12.0f) +
            SurfaceWave + 2.0f * FMath::Sin(Phase * 1.7f + T * PI);

        const int32 BaseVertex = Vertices.Num();
        Vertices.Add(FVector(X, CenterY - LocalHalfWidth, Z));
        Vertices.Add(FVector(X, CenterY + LocalHalfWidth, Z + 0.6f));
        UVs.Add(FVector2D(T, 0.0f));
        UVs.Add(FVector2D(T, 1.0f));
        const FLinearColor LaceColor = ClampPreviewColor(FMath::Lerp(
            Spec.WaterColor,
            RibbonColor,
            FMath::Clamp(0.36f + SegmentFade * 0.38f, 0.0f, 0.72f)));
        VertexColors.Add(LaceColor);
        VertexColors.Add(LaceColor);
        return BaseVertex;
    };

    for (int32 SegmentIndex = 0; SegmentIndex < Segments; ++SegmentIndex)
    {
        const float SegmentStartT = static_cast<float>(SegmentIndex) / static_cast<float>(Segments);
        const float SegmentEndT = static_cast<float>(SegmentIndex + 1) / static_cast<float>(Segments);
        const float SegmentMidT = (SegmentStartT + SegmentEndT) * 0.50f;
        const float LacePulse =
            0.50f + 0.50f * FMath::Sin(Phase * 2.17f + SegmentMidT * UE_TWO_PI * 7.0f) +
            0.18f * FMath::Sin(Phase * 0.91f + SegmentMidT * UE_TWO_PI * 19.0f);
        const float SegmentFade = SmoothPreviewStep(FoamRailContinuityBreakupT, 1.10f, LacePulse);
        if (SegmentFade <= 0.02f)
        {
            continue;
        }

        const float EndWidthFade = FMath::Clamp(0.18f + SegmentFade * 0.24f, 0.14f, 0.42f);
        const int32 A = AddFoamLaceCrossSection(SegmentStartT, EndWidthFade, SegmentFade);
        const int32 C = AddFoamLaceCrossSection(SegmentMidT, SegmentFade, SegmentFade);
        const int32 E = AddFoamLaceCrossSection(SegmentEndT, EndWidthFade, SegmentFade);
        const int32 B = A + 1;
        const int32 D = C + 1;
        const int32 F = E + 1;
        Triangles.Add(A);
        Triangles.Add(C);
        Triangles.Add(B);
        Triangles.Add(B);
        Triangles.Add(C);
        Triangles.Add(D);
        Triangles.Add(C);
        Triangles.Add(E);
        Triangles.Add(D);
        Triangles.Add(D);
        Triangles.Add(E);
        Triangles.Add(F);
    }

    if (Vertices.IsEmpty() || Triangles.IsEmpty())
    {
        return;
    }

    Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        RibbonColor,
        LoadOrCreatePreviewWaterVertexColorMaterial(),
        &VertexColors);
}

void AddPreviewFlowTextureRibbon(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FString& Label,
    float StartX,
    float Length,
    float LateralOffset,
    float Width,
    float Phase,
    const FLinearColor& HighlightColor,
    const FLinearColor& ShadowColor)
{
    if (!World)
    {
        return;
    }

    constexpr int32 Segments = 16;
    const float FlowTextureRailArtifactDemotion = 0.34f;
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float ResidualCenterFlowTextureRibbonCullT =
        SmoothPreviewStep(0.32f, 0.58f, FMath::Abs(LateralOffset) / FMath::Max(1.0f, ActiveRiverHalfWidth));
    const float CenterGuideRibbonDemotion = ResidualCenterFlowTextureRibbonCullT;
    if (CenterGuideRibbonDemotion <= 0.16f)
    {
        return;
    }
    TArray<FVector> Vertices;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<FLinearColor> VertexColors;
    TArray<int32> Triangles;
    Vertices.Reserve((Segments + 1) * 2);
    UVs.Reserve((Segments + 1) * 2);
    VertexColors.Reserve((Segments + 1) * 2);
    Triangles.Reserve(Segments * 6);

    const float WaterBaseZ = GetPreviewWaterSurfaceBaseZCm(Spec);
    for (int32 SegmentIndex = 0; SegmentIndex <= Segments; ++SegmentIndex)
    {
        const float T = static_cast<float>(SegmentIndex) / static_cast<float>(Segments);
        const float X = StartX + Length * T;
        const float RiverCenterY = GetPreviewRiverCenterY(Spec, X);
        const float Sway =
            FMath::Sin(Phase + T * UE_TWO_PI) * Width * 0.34f +
            FMath::Sin(Phase * 0.67f + T * UE_TWO_PI * 2.0f) * Width * 0.16f;
        const float Taper = FMath::Sin(T * PI);
        const float RemainingWaterOverlaySlabDemotion = SmoothPreviewStep(12600.0f, 19800.0f, X);
        const float NearFrameWaterRibbonDemotion = RemainingWaterOverlaySlabDemotion;
        const float NearFrameWidthScale =
            FMath::Lerp(0.05f, 0.34f, NearFrameWaterRibbonDemotion) * FlowTextureRailArtifactDemotion *
            CenterGuideRibbonDemotion;
        const float LocalHalfWidth = FMath::Max(0.9f, Width * NearFrameWidthScale * (0.10f + 0.30f * Taper));
        const float CenterY = RiverCenterY + LateralOffset + Sway;
        const float SurfaceWave = FMath::Sin(X * 0.011f + CenterY * 0.015f) * (Spec.bDesertCanyon ? 2.0f : 4.5f);
        const float Z = WaterBaseZ + FMath::Lerp(3.0f, 12.0f, NearFrameWaterRibbonDemotion) +
            SurfaceWave + 1.6f * FMath::Sin(Phase * 1.3f + T * PI);
        const float Pulse =
            FMath::Clamp(0.44f + 0.34f * FMath::Sin(Phase + T * UE_TWO_PI * 3.0f) + 0.16f * Taper, 0.0f, 1.0f);
        const FLinearColor RawFlowColor = ClampPreviewColor(FMath::Lerp(ShadowColor, HighlightColor, Pulse));
        const FLinearColor FlowColor = ClampPreviewColor(FMath::Lerp(
            Spec.WaterColor,
            RawFlowColor,
            FMath::Lerp(0.025f, 0.28f, NearFrameWaterRibbonDemotion) * FlowTextureRailArtifactDemotion *
                CenterGuideRibbonDemotion));

        Vertices.Add(FVector(X, CenterY - LocalHalfWidth, Z));
        Vertices.Add(FVector(X, CenterY + LocalHalfWidth, Z + 0.7f));
        UVs.Add(FVector2D(T * 5.0f, 0.0f));
        UVs.Add(FVector2D(T * 5.0f, 1.0f));
        VertexColors.Add(ScalePreviewColor(FlowColor, 0.88f + 0.08f * Taper));
        VertexColors.Add(ScalePreviewColor(FlowColor, 0.98f));
    }

    for (int32 SegmentIndex = 0; SegmentIndex < Segments; ++SegmentIndex)
    {
        const int32 A = SegmentIndex * 2;
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

    Normals = ComputePreviewMeshNormals(Vertices, Triangles);
    AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        HighlightColor,
        LoadOrCreatePreviewWaterVertexColorMaterial(),
        &VertexColors);
}

void AddPreviewFlowBandTextureDetail(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec)
{
    if (!World)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float TextureScale = FMath::Clamp(0.65f * Spec.FlowCurrentCueScale + 0.35f * Spec.FlowFoamScale, 0.45f, 1.45f);
    const int32 BaseRibbonCount = Spec.bDesertCanyon ? 10 : (Spec.bHasWaterfalls ? 16 : 14);
    const int32 RibbonCount =
        FMath::Max(1, FMath::RoundToInt(static_cast<float>(BaseRibbonCount) * FMath::Clamp(TextureScale, 0.55f, 1.35f)));
    const FLinearColor HighlightColor = Spec.bDesertCanyon
        ? FLinearColor(0.50f, 0.43f, 0.31f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.11f, 0.58f, 0.48f) : FLinearColor(0.15f, 0.64f, 0.62f));
    const FLinearColor ShadowColor = Spec.bDesertCanyon
        ? FLinearColor(0.26f, 0.22f, 0.16f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.025f, 0.28f, 0.22f) : FLinearColor(0.035f, 0.34f, 0.36f));

    for (int32 RibbonIndex = 0; RibbonIndex < RibbonCount; ++RibbonIndex)
    {
        const float T = FMath::Frac(0.127f + 0.6180339f * static_cast<float>(RibbonIndex));
        const float X = FMath::Lerp(8800.0f, 25300.0f, T);
        const float LateralJitter =
            FMath::Sin(static_cast<float>(RibbonIndex) * 1.63f) * ActiveRiverHalfWidth * 0.74f +
            FMath::Sin(static_cast<float>(RibbonIndex) * 0.41f) * ActiveRiverHalfWidth * 0.12f;
        const float Length =
            (Spec.bDesertCanyon ? 420.0f : (Spec.bHasWaterfalls ? 320.0f : 350.0f)) *
            (0.66f + 0.12f * static_cast<float>(RibbonIndex % 5)) * TextureScale;
        const float Width =
            (Spec.bDesertCanyon ? 9.0f : 7.0f) *
            (0.72f + 0.10f * static_cast<float>(RibbonIndex % 4)) *
            FMath::Clamp(TextureScale, 0.70f, 1.22f);
        AddPreviewFlowTextureRibbon(
            World,
            Spec,
            FString::Printf(TEXT("RaftSim_FlowTextureRibbon_%03d_%s"), RibbonIndex, *Spec.RiverId),
            X - Length * 0.42f,
            Length,
            LateralJitter,
            Width,
            static_cast<float>(RibbonIndex) * 0.77f,
            HighlightColor,
            ShadowColor);
    }
}

void AddPreviewWaterTurbidityPatch(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FString& Label,
    float StartX,
    float Length,
    float LateralOffset,
    float Width,
    float Phase,
    const FLinearColor& InnerColor,
    const FLinearColor& OuterColor)
{
    if (!World)
    {
        return;
    }

    constexpr int32 Segments = 14;
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

    const float WaterBaseZ = GetPreviewWaterSurfaceBaseZCm(Spec);
    for (int32 SegmentIndex = 0; SegmentIndex <= Segments; ++SegmentIndex)
    {
        const float U = static_cast<float>(SegmentIndex) / static_cast<float>(Segments);
        const float X = StartX + Length * U;
        const float RiverCenterY = GetPreviewRiverCenterY(Spec, X);
        const float LongitudinalTaper = FMath::Sin(U * PI);
        for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
        {
            const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
            const float Cross = (V - 0.5f) * Width * (0.42f + 0.58f * LongitudinalTaper);
            const float Sway =
                FMath::Sin(Phase + U * UE_TWO_PI) * Width * 0.23f +
                FMath::Sin(Phase * 0.59f + U * UE_TWO_PI * 2.0f) * Width * 0.10f;
            const float CenterY = RiverCenterY + LateralOffset + Sway;
            const float SurfaceWave =
                FMath::Sin(X * 0.011f + CenterY * 0.015f) * (Spec.bDesertCanyon ? 2.0f : 4.5f) +
                FMath::Sin(Phase + U * UE_TWO_PI * 2.4f + V * 1.7f) * (Spec.bDesertCanyon ? 1.2f : 2.4f);
            const float Fleck =
                FMath::Clamp(0.78f + 0.16f * LongitudinalTaper + 0.06f * FMath::Sin(Phase + V * 3.3f), 0.62f, 1.04f);
            Vertices.Add(FVector(X, CenterY + Cross, WaterBaseZ + 17.0f + SurfaceWave));
            UVs.Add(FVector2D(U * 5.0f, V));
            VertexColors.Add(ScalePreviewColor(FMath::Lerp(InnerColor, OuterColor, V), Fleck));
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
    AddPreviewProceduralMeshActor(
        World,
        Label,
        Vertices,
        Triangles,
        Normals,
        UVs,
        InnerColor,
        LoadOrCreatePreviewWaterVertexColorMaterial(),
        &VertexColors);
}

void AddPreviewWaterSurfaceChopAndTurbidityDetail(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec)
{
    if (!World)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float FlowEnergy = FMath::Clamp(0.58f * Spec.FlowCurrentCueScale + 0.42f * Spec.FlowFoamScale, 0.52f, 1.42f);
    const int32 BaseChopCount = Spec.bDesertCanyon ? 22 : (Spec.bHasWaterfalls ? 34 : 28);
    const int32 ChopCount =
        FMath::Max(1, FMath::RoundToInt(static_cast<float>(BaseChopCount) * FMath::Clamp(FlowEnergy, 0.62f, 1.32f)));
    const FLinearColor ChopHighlight = Spec.bDesertCanyon
        ? FLinearColor(0.60f, 0.52f, 0.38f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.18f, 0.66f, 0.55f) : FLinearColor(0.17f, 0.70f, 0.70f));
    const FLinearColor ChopShadow = Spec.bDesertCanyon
        ? FLinearColor(0.32f, 0.27f, 0.20f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.03f, 0.30f, 0.24f) : FLinearColor(0.04f, 0.36f, 0.40f));

    for (int32 ChopIndex = 0; ChopIndex < ChopCount; ++ChopIndex)
    {
        const float T = FMath::Frac(0.211f + 0.381966f * static_cast<float>(ChopIndex));
        const float X = FMath::Lerp(-4400.0f, 25300.0f, T);
        const float Lateral =
            FMath::Sin(static_cast<float>(ChopIndex) * 1.17f) * ActiveRiverHalfWidth * 0.64f +
            FMath::Sin(static_cast<float>(ChopIndex) * 0.37f) * ActiveRiverHalfWidth * 0.16f;
        const float Length =
            (Spec.bDesertCanyon ? 520.0f : 420.0f) *
            (0.72f + 0.16f * static_cast<float>(ChopIndex % 5)) * FlowEnergy;
        const float Width =
            (Spec.bDesertCanyon ? 18.0f : 16.0f) *
            (0.74f + 0.18f * static_cast<float>(ChopIndex % 4)) * FMath::Clamp(FlowEnergy, 0.72f, 1.24f);
        AddPreviewFlowTextureRibbon(
            World,
            Spec,
            FString::Printf(TEXT("RaftSim_FlowSurfaceChopCrest_%03d_%s"), ChopIndex, *Spec.RiverId),
            X - Length * 0.42f,
            Length,
            Lateral,
            Width,
            static_cast<float>(ChopIndex) * 0.93f,
            ChopHighlight,
            ChopShadow);
    }

    const float TurbidityDepthPatchArtifactDemotion = 0.0f;
    const int32 BaseTurbidityCount = Spec.bDesertCanyon ? 18 : (Spec.bHasWaterfalls ? 22 : 18);
    const int32 TurbidityCount = TurbidityDepthPatchArtifactDemotion > 0.0f
        ? FMath::Max(1, FMath::RoundToInt(static_cast<float>(BaseTurbidityCount) * FMath::Clamp(FlowEnergy, 0.70f, 1.20f)))
        : 0;
    const FLinearColor InnerTurbidity = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.52f, 0.40f, 0.26f), 0.58f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.08f, 0.42f, 0.32f), 0.45f)
                               : FMath::Lerp(Spec.WaterColor, FLinearColor(0.07f, 0.52f, 0.54f), 0.38f));
    const FLinearColor OuterTurbidity = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.66f, 0.50f, 0.30f), 0.42f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.12f, 0.55f, 0.38f), 0.36f)
                               : FMath::Lerp(Spec.WaterColor, FLinearColor(0.14f, 0.62f, 0.60f), 0.30f));

    for (int32 PatchIndex = 0; PatchIndex < TurbidityCount; ++PatchIndex)
    {
        const float T = FMath::Frac(0.097f + 0.618034f * static_cast<float>(PatchIndex));
        const float X = FMath::Lerp(-4800.0f, 25000.0f, T);
        const float EdgeBias = (PatchIndex % 3 == 0) ? 0.68f : 0.38f;
        const float Side = (PatchIndex % 2 == 0) ? -1.0f : 1.0f;
        const float Lateral =
            Side * ActiveRiverHalfWidth * EdgeBias +
            FMath::Sin(static_cast<float>(PatchIndex) * 1.53f) * ActiveRiverHalfWidth * 0.18f;
        const float Length =
            (Spec.bDesertCanyon ? 1260.0f : 980.0f) *
            (0.74f + 0.12f * static_cast<float>(PatchIndex % 6)) * FMath::Clamp(FlowEnergy, 0.74f, 1.18f);
        const float Width =
            (Spec.bDesertCanyon ? 88.0f : 74.0f) *
            (0.72f + 0.12f * static_cast<float>(PatchIndex % 5));
        AddPreviewWaterTurbidityPatch(
            World,
            Spec,
            FString::Printf(TEXT("RaftSim_FlowTurbidityDepthPatch_%03d_%s"), PatchIndex, *Spec.RiverId),
            X - Length * 0.45f,
            Length,
            Lateral,
            Width,
            static_cast<float>(PatchIndex) * 0.71f,
            InnerTurbidity,
            OuterTurbidity);
    }
}

void AddPreviewWaterShaderDepthReflectionScaffoldDetail(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec)
{
    if (!World)
    {
        return;
    }

    constexpr int32 XSteps = 92;
    // Odd cross-step count plus center reblending avoids a visible shader-scaffold center rail in review captures.
    constexpr int32 CrossSteps = 13;
    const float NearCameraWaterScaffoldClearanceMinX = 25200.0f;
    const float CentralWaterScaffoldPlateDemotion = 0.12f;
    const float ResidualCenterWaterShaderPlateDemotion = 0.82f;
    const float MinX = NearCameraWaterScaffoldClearanceMinX;
    const float MaxX = 26000.0f;
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float WaterBaseZ = GetPreviewWaterSurfaceBaseZCm(Spec);
    const float FlowEnergy = FMath::Clamp(0.55f * Spec.FlowCurrentCueScale + 0.45f * Spec.FlowFoamScale, 0.48f, 1.45f);

    const FLinearColor DeepCore = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.19f, 0.20f, 0.16f), 0.32f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.010f, 0.17f, 0.145f), 0.28f)
                                : FMath::Lerp(Spec.WaterColor, FLinearColor(0.012f, 0.22f, 0.245f), 0.30f));
    const FLinearColor ShallowTint = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.47f, 0.40f, 0.27f), 0.26f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.055f, 0.36f, 0.25f), 0.25f)
                                : FMath::Lerp(Spec.WaterColor, FLinearColor(0.060f, 0.44f, 0.48f), 0.26f));
    const FLinearColor SkyReflection = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.64f, 0.58f, 0.43f), 0.30f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.22f, 0.64f, 0.56f), 0.28f)
                                : FMath::Lerp(Spec.WaterColor, FLinearColor(0.24f, 0.66f, 0.68f), 0.30f));
    const FLinearColor BankReflection = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FMath::Lerp(Spec.RockColor, FLinearColor(0.55f, 0.43f, 0.28f), 0.45f), 0.32f)
        : FMath::Lerp(Spec.WaterColor, Spec.FoliageColor, Spec.bHasWaterfalls ? 0.22f : 0.18f);

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
            (Spec.bDesertCanyon ? 0.28f : 0.24f) *
            CentralWaterScaffoldPlateDemotion *
            (0.95f + 0.05f * FMath::Sin(X * 0.0012f));
        const float LongitudinalFeather = SmoothPreviewStep(0.0f, 0.13f, U);
        for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
        {
            const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
            const float Lateral = FMath::Lerp(-Width, Width, V);
            const float EdgeT = FMath::Pow(FMath::Abs(V - 0.5f) * 2.0f, 1.22f);
            const float DeepT = 1.0f - FMath::Clamp(EdgeT, 0.0f, 1.0f);
            const float CenterFeather = SmoothPreviewStep(0.0f, 0.72f, DeepT);
            const float ResidualCenterShaderScaffoldEraseT = SmoothPreviewStep(0.72f, 0.99f, DeepT);
            const float FlowLine =
                FMath::Clamp(
                    0.48f + 0.28f * FMath::Sin(X * 0.0039f - Lateral * 0.0068f) +
                        0.18f * FMath::Sin(X * 0.011f + Lateral * 0.0032f),
                    0.0f,
                    1.0f);
            const float FresnelEdge = FMath::Pow(FMath::Clamp(EdgeT, 0.0f, 1.0f), 2.15f);
            const float ReflectionT = FMath::Clamp(
                ((0.055f + 0.085f * FlowLine) * FlowEnergy + FresnelEdge * 0.060f) *
                    LongitudinalFeather *
                    CentralWaterScaffoldPlateDemotion *
                    (1.0f - ResidualCenterShaderScaffoldEraseT * ResidualCenterWaterShaderPlateDemotion),
                0.0f,
                0.040f);
            FLinearColor WaterColor = FMath::Lerp(ShallowTint, DeepCore, DeepT);
            WaterColor = FMath::Lerp(
                WaterColor,
                BankReflection,
                FMath::Clamp(FresnelEdge * 0.075f * CentralWaterScaffoldPlateDemotion, 0.0f, 0.040f));
            WaterColor = FMath::Lerp(WaterColor, SkyReflection, ReflectionT);
            WaterColor = FMath::Lerp(
                WaterColor,
                Spec.WaterColor,
                FMath::Clamp(
                    0.72f + 0.12f * (1.0f - CenterFeather) +
                        0.06f * FMath::Sin(X * 0.0023f + Lateral * 0.0051f),
                    0.64f,
                    0.90f));
            WaterColor = FMath::Lerp(
                WaterColor,
                Spec.WaterColor,
                FMath::Clamp(ResidualCenterShaderScaffoldEraseT * ResidualCenterWaterShaderPlateDemotion * 0.42f, 0.0f, 0.36f));

            const float SurfaceWave =
                (FMath::Sin(X * 0.011f + Lateral * 0.015f) * (Spec.bDesertCanyon ? 1.2f : 2.4f) +
                 FMath::Sin(X * 0.018f - Lateral * 0.006f) * (Spec.bDesertCanyon ? 0.5f : 0.9f)) *
                LongitudinalFeather *
                (1.0f - ResidualCenterShaderScaffoldEraseT * ResidualCenterWaterShaderPlateDemotion * 0.32f);
            Vertices.Add(FVector(X, CenterY + Lateral, WaterBaseZ + 3.6f + SurfaceWave));
            UVs.Add(FVector2D(U * 22.0f, V));
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
    AddPreviewProceduralMeshActor(
        World,
        FString::Printf(TEXT("RaftSim_WaterShaderDepthReflectionScaffold_%s"), *Spec.RiverId),
        Vertices,
        Triangles,
        Normals,
        UVs,
        Spec.WaterColor,
        LoadOrCreatePreviewWaterVertexColorMaterial(),
        &VertexColors);

    const int32 ReflectionRibbonCount = Spec.bDesertCanyon ? 2 : (Spec.bHasWaterfalls ? 3 : 3);
    for (int32 ReflectionIndex = 0; ReflectionIndex < ReflectionRibbonCount; ++ReflectionIndex)
    {
        const float T = FMath::Frac(0.081f + 0.618034f * static_cast<float>(ReflectionIndex));
        const float X = FMath::Lerp(NearCameraWaterScaffoldClearanceMinX, 25300.0f, T);
        const float Side = (ReflectionIndex % 2 == 0) ? -1.0f : 1.0f;
        const float Lateral = Side * ActiveRiverHalfWidth * (0.58f + 0.22f * FMath::Sin(static_cast<float>(ReflectionIndex) * 0.73f));
        const float Length =
            (Spec.bDesertCanyon ? 560.0f : 440.0f) *
            (0.72f + 0.12f * static_cast<float>(ReflectionIndex % 5)) * FMath::Clamp(FlowEnergy, 0.68f, 1.22f);
        const float Width =
            (Spec.bDesertCanyon ? 9.0f : 7.0f) *
            (0.74f + 0.10f * static_cast<float>(ReflectionIndex % 4));
        AddPreviewFlowTextureRibbon(
            World,
            Spec,
            FString::Printf(TEXT("RaftSim_WaterShaderFresnelBankReflection_%03d_%s"), ReflectionIndex, *Spec.RiverId),
            X - Length * 0.44f,
            Length,
            Lateral,
            Width,
            static_cast<float>(ReflectionIndex) * 0.67f,
            FMath::Lerp(Spec.WaterColor, SkyReflection, 0.48f),
            FMath::Lerp(Spec.WaterColor, BankReflection, 0.44f));
    }

    const int32 RefractionSeamCount = 0;
    for (int32 SeamIndex = 0; SeamIndex < RefractionSeamCount; ++SeamIndex)
    {
        const float T = FMath::Frac(0.143f + 0.414214f * static_cast<float>(SeamIndex));
        const float X = FMath::Lerp(NearCameraWaterScaffoldClearanceMinX, 24800.0f, T);
        const float Side = (SeamIndex % 2 == 0) ? -1.0f : 1.0f;
        const float Lateral = Side * ActiveRiverHalfWidth * (0.28f + 0.32f * FMath::Abs(FMath::Sin(static_cast<float>(SeamIndex) * 0.89f)));
        const FLinearColor SeamHighlight = Spec.bDesertCanyon
            ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.58f, 0.50f, 0.34f), 0.34f)
            : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.12f, 0.55f, 0.42f), 0.32f)
                                    : FMath::Lerp(Spec.WaterColor, FLinearColor(0.12f, 0.58f, 0.58f), 0.34f));
        const FLinearColor SeamShadow = Spec.bDesertCanyon
            ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.27f, 0.23f, 0.16f), 0.30f)
            : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.020f, 0.22f, 0.17f), 0.28f)
                                    : FMath::Lerp(Spec.WaterColor, FLinearColor(0.025f, 0.27f, 0.29f), 0.30f));
        AddPreviewFlowTextureRibbon(
            World,
            Spec,
            FString::Printf(TEXT("RaftSim_WaterShaderRefractionSeam_%03d_%s"), SeamIndex, *Spec.RiverId),
            X - 170.0f,
            Spec.bDesertCanyon ? 360.0f : 300.0f,
            Lateral,
            Spec.bDesertCanyon ? 4.5f : 3.5f,
            static_cast<float>(SeamIndex) * 0.91f,
            SeamHighlight,
            SeamShadow);
    }
}

void AddPreviewShallowWaterClarityAndAerationDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* WaterMask,
    UStaticMesh* PlaneMesh)
{
    if (!World)
    {
        return;
    }

    constexpr int32 Segments = 156;
    constexpr int32 CrossSteps = 4;
    const float ShallowWaterEdgeBandDemotion = 0.20f;
    const float ShallowEdgeRailArtifactDemotion = 0.30f;
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float WaterBaseZ = GetPreviewWaterSurfaceBaseZCm(Spec);
    const float FlowEnergy = FMath::Clamp(0.52f * Spec.FlowCurrentCueScale + 0.48f * Spec.FlowFoamScale, 0.52f, 1.48f);

    const FLinearColor CoreTint = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.34f, 0.30f, 0.22f), 0.30f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.020f, 0.25f, 0.19f), 0.26f)
                                : FMath::Lerp(Spec.WaterColor, FLinearColor(0.030f, 0.36f, 0.38f), 0.24f));
    const FLinearColor ShallowBedTint = Spec.bDesertCanyon
        ? FLinearColor(0.42f, 0.34f, 0.23f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.035f, 0.13f, 0.075f) : FLinearColor(0.075f, 0.25f, 0.22f));
    const FLinearColor AeratedTint = Spec.bDesertCanyon
        ? FLinearColor(0.50f, 0.47f, 0.35f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.22f, 0.52f, 0.39f) : FLinearColor(0.24f, 0.54f, 0.52f));

    for (int32 SideIndex = 0; SideIndex < 2; ++SideIndex)
    {
        const float Side = SideIndex == 0 ? -1.0f : 1.0f;
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
            const float X = FMath::Lerp(8600.0f, 25800.0f, U);
            const float RiverCenterY = GetPreviewRiverCenterY(Spec, X);
            const float Width = ActiveRiverHalfWidth *
                (0.98f + 0.055f * FMath::Sin(X * 0.0012f) + (Spec.bDesertCanyon ? 0.14f : 0.04f));
            const float LongitudinalFeather = FMath::Clamp(
                SmoothPreviewStep(0.0f, 0.055f, U) * (1.0f - SmoothPreviewStep(0.965f, 1.0f, U)),
                0.0f,
                1.0f);
            const float NearFrameShallowWaterBandDemotion = SmoothPreviewStep(10800.0f, 16800.0f, X);
            const float BandInnerEdge = FMath::Lerp(0.993f, 0.986f, NearFrameShallowWaterBandDemotion);
            const float BandOuterEdge = FMath::Lerp(0.997f, 0.993f, NearFrameShallowWaterBandDemotion);

            for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
            {
                const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
                const float EdgeT = FMath::Pow(FMath::Clamp(V, 0.0f, 1.0f), 1.12f);
                const float Lateral = Side * FMath::Lerp(Width * BandInnerEdge, Width * BandOuterEdge, EdgeT);
                const float Sway =
                    Side * (FMath::Sin(X * 0.0049f + EdgeT * 2.2f) * 18.0f +
                            FMath::Sin(X * 0.013f + static_cast<float>(SideIndex) * 1.7f) * 8.0f) *
                    LongitudinalFeather;
                const float Y = RiverCenterY + Lateral + Sway;
                const float SourceWaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, Y);
                const float Mottle =
                    FMath::Clamp(
                        0.50f + 0.24f * FMath::Sin(X * 0.0063f + EdgeT * 3.1f) +
                            0.18f * FMath::Sin(X * 0.017f - EdgeT * 5.2f),
                        0.0f,
                        1.0f);
                const float BedRevealT =
                    FMath::Clamp(0.025f + EdgeT * 0.055f + (1.0f - SourceWaterT) * 0.020f + Mottle * 0.018f, 0.0f, 0.12f);
                const float AerationT =
                    FMath::Clamp((0.006f + 0.010f * FlowEnergy) * (1.0f - EdgeT * 0.70f) * Mottle, 0.0f, 0.016f);
                FLinearColor WaterColor = FMath::Lerp(CoreTint, ShallowBedTint, BedRevealT);
                WaterColor = FMath::Lerp(WaterColor, AeratedTint, AerationT);
                WaterColor = FMath::Lerp(WaterColor, Spec.WaterColor, FMath::Clamp(0.82f + SourceWaterT * 0.10f, 0.80f, 0.94f));
                WaterColor = FMath::Lerp(
                    Spec.WaterColor,
                    WaterColor,
                    FMath::Lerp(0.003f, 0.018f, NearFrameShallowWaterBandDemotion) *
                        LongitudinalFeather *
                        ShallowWaterEdgeBandDemotion *
                        ShallowEdgeRailArtifactDemotion);

                const float SurfaceWave =
                    (FMath::Sin(X * 0.012f + EdgeT * 2.7f) * (Spec.bDesertCanyon ? 1.4f : 2.6f) +
                     FMath::Sin(X * 0.023f - EdgeT * 4.1f) * (Spec.bDesertCanyon ? 0.7f : 1.2f)) *
                    LongitudinalFeather;
                Vertices.Add(FVector(X, Y, WaterBaseZ + 3.6f + SurfaceWave));
                UVs.Add(FVector2D(U * 18.0f, V));
                VertexColors.Add(ClampPreviewColor(WaterColor));
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

        Normals.SetNum(Vertices.Num());
        for (FVector& Normal : Normals)
        {
            Normal = FVector::UpVector;
        }
        AddPreviewProceduralMeshActor(
            World,
            FString::Printf(
                TEXT("RaftSim_ShallowWaterClarityBand_%s_%s"),
                Side < 0.0f ? TEXT("Left") : TEXT("Right"),
                *Spec.RiverId),
            Vertices,
            Triangles,
            Normals,
            UVs,
            CoreTint,
            LoadOrCreatePreviewWaterVertexColorMaterial(),
            &VertexColors);
    }

    if (!PlaneMesh)
    {
        return;
    }

    const int32 BaseBubbleCount = Spec.bDesertCanyon ? 42 : (Spec.bHasWaterfalls ? 96 : 72);
    const int32 BubbleCount =
        FMath::Max(1, FMath::RoundToInt(static_cast<float>(BaseBubbleCount) * FMath::Clamp(FlowEnergy, 0.70f, 1.26f)));
    const FLinearColor BubbleColor = Spec.bDesertCanyon
        ? FLinearColor(0.72f, 0.68f, 0.54f, 1.0f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.72f, 0.92f, 0.80f, 1.0f) : FLinearColor(0.76f, 0.92f, 0.88f, 1.0f));

    for (int32 BubbleIndex = 0; BubbleIndex < BubbleCount; ++BubbleIndex)
    {
        const float T = FMath::Frac(0.059f + 0.6180339f * static_cast<float>(BubbleIndex));
        const float X = FMath::Lerp(-4300.0f, 25000.0f, T);
        const float Side = (BubbleIndex % 2 == 0) ? -1.0f : 1.0f;
        const float RiverCenterY = GetPreviewRiverCenterY(Spec, X);
        const float Width = ActiveRiverHalfWidth *
            (0.96f + 0.06f * FMath::Sin(X * 0.0012f) + (Spec.bDesertCanyon ? 0.14f : 0.04f));
        const float EdgeLane = 0.48f + 0.36f * FMath::Abs(FMath::Sin(static_cast<float>(BubbleIndex) * 1.31f));
        const float Lateral = Side * Width * EdgeLane +
            FMath::Sin(static_cast<float>(BubbleIndex) * 2.17f) * Width * 0.08f;
        const float SourceWaterT = SamplePreviewMaskAtWorld(Spec, WaterMask, X, RiverCenterY + Lateral);
        const float NearFrameBubbleDemotion = SmoothPreviewStep(2200.0f, 7600.0f, X);
        const float Opacity =
            (Spec.bDesertCanyon ? 0.070f : (Spec.bHasWaterfalls ? 0.145f : 0.110f)) *
            FMath::Clamp(0.74f + SourceWaterT * 0.42f + FlowEnergy * 0.18f, 0.55f, 1.25f) *
            FMath::Lerp(0.20f, 1.0f, NearFrameBubbleDemotion);
        const float LengthScale =
            (Spec.bDesertCanyon ? 0.14f : 0.11f) *
            (0.70f + 0.10f * static_cast<float>(BubbleIndex % 5)) *
            FMath::Lerp(0.42f, 1.0f, NearFrameBubbleDemotion);
        const float WidthScale =
            (Spec.bDesertCanyon ? 0.026f : 0.022f) *
            (0.74f + 0.10f * static_cast<float>(BubbleIndex % 4)) *
            FMath::Lerp(0.50f, 1.0f, NearFrameBubbleDemotion);

        AddPreviewTranslucentMeshActor(
            World,
            PlaneMesh,
            FString::Printf(TEXT("RaftSim_ShallowWaterAerationBubbleLace_%03d_%s"), BubbleIndex, *Spec.RiverId),
            FVector(
                X,
                RiverCenterY + Lateral,
                WaterBaseZ + 27.0f + 1.8f * FMath::Sin(static_cast<float>(BubbleIndex) * 0.73f)),
            FRotator(0.0f, static_cast<float>((BubbleIndex * 23) % 360), 0.0f),
            FVector(LengthScale, WidthScale, 1.0f),
            BubbleColor,
            Opacity);
    }
}

void AddPreviewFoamAndHydraulics(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec)
{
    if (!World)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float FoamScale = FMath::Max(0.35f, Spec.FlowFoamScale);
    const int32 FlowAwareFoamTrainCount =
        FMath::Max(1, FMath::RoundToInt(static_cast<float>(Spec.FoamTrainCount) * FMath::Clamp(FoamScale, 0.5f, 1.35f)));

    for (int32 FoamIndex = 0; FoamIndex < FlowAwareFoamTrainCount; ++FoamIndex)
    {
        const float X = -4050.0f + static_cast<float>(FoamIndex) * (28000.0f / FMath::Max(1, FlowAwareFoamTrainCount));
        const float Offset = FMath::Sin(static_cast<float>(FoamIndex) * 1.7f) * ActiveRiverHalfWidth * 0.42f;
        const float Length = (Spec.bDesertCanyon ? 1420.0f : 1050.0f) * FoamScale;
        AddPreviewFoamRibbon(
            World,
            Spec,
            FString::Printf(TEXT("RaftSim_FoamTongue_%02d_%s"), FoamIndex, *Spec.RiverId),
            X - Length * 0.48f,
            Length,
            Offset,
            (54.0f + 12.0f * static_cast<float>(FoamIndex % 3)) * FoamScale,
            static_cast<float>(FoamIndex) * 0.83f,
            FLinearColor(0.82f, 0.90f, 0.86f));
        AddPreviewFoamRibbon(
            World,
            Spec,
            FString::Printf(TEXT("RaftSim_WaveHighlight_%02d_%s"), FoamIndex, *Spec.RiverId),
            X - Length * 0.26f,
            Length * 0.55f,
            Offset * 0.55f,
            (22.0f + 5.0f * static_cast<float>(FoamIndex % 2)) * FoamScale,
            static_cast<float>(FoamIndex) * 1.19f + 0.4f,
            Spec.bDesertCanyon ? FLinearColor(0.78f, 0.82f, 0.76f) : FLinearColor(0.72f, 0.88f, 0.84f));

        if (!Spec.bDesertCanyon && FoamIndex % 3 == 0)
        {
            AddPreviewFoamRibbon(
                World,
                Spec,
                FString::Printf(TEXT("RaftSim_EddyLine_%02d_%s"), FoamIndex, *Spec.RiverId),
                X + 80.0f,
                720.0f * FoamScale,
                ActiveRiverHalfWidth * 0.76f,
                18.0f * FoamScale,
                static_cast<float>(FoamIndex) * 0.47f,
                FLinearColor(0.88f, 0.94f, 0.90f));
        }
    }
}

void AddPreviewFlowDependentHydraulicAerationAndSprayDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    UStaticMesh* PlaneMesh,
    UStaticMesh* SphereMesh)
{
    if (!World || !PlaneMesh)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float WaterBaseZ = GetPreviewWaterSurfaceBaseZCm(Spec);
    const float FlowEnergy = FMath::Clamp(0.54f * Spec.FlowFoamScale + 0.46f * Spec.FlowCurrentCueScale, 0.46f, 1.42f);
    const int32 BaseHydraulicCount = Spec.bDesertCanyon ? 12 : (Spec.bHasWaterfalls ? 24 : 18);
    const int32 HydraulicCount =
        FMath::Max(1, FMath::RoundToInt(static_cast<float>(BaseHydraulicCount) * FMath::Clamp(FlowEnergy, 0.58f, 1.28f)));
    const float HazardReadabilityOpacityLimit = Spec.bDesertCanyon ? 0.080f : (Spec.bHasWaterfalls ? 0.115f : 0.105f);
    const float WaterOverlaySlabOpacityDemotion = 0.54f;
    const FLinearColor AerationCore = Spec.bDesertCanyon
        ? FLinearColor(0.70f, 0.67f, 0.53f, 1.0f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.78f, 0.96f, 0.84f, 1.0f) : FLinearColor(0.80f, 0.94f, 0.88f, 1.0f));
    const FLinearColor AerationShadow = Spec.bDesertCanyon
        ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.48f, 0.42f, 0.30f, 1.0f), 0.42f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(Spec.WaterColor, FLinearColor(0.18f, 0.52f, 0.36f, 1.0f), 0.38f)
                                : FMath::Lerp(Spec.WaterColor, FLinearColor(0.24f, 0.60f, 0.56f, 1.0f), 0.34f));

    for (int32 HydraulicIndex = 0; HydraulicIndex < HydraulicCount; ++HydraulicIndex)
    {
        const float SequenceT = static_cast<float>(HydraulicIndex) / static_cast<float>(FMath::Max(1, HydraulicCount - 1));
        const float Phase = static_cast<float>(HydraulicIndex) * 1.6180339f;
        const float BaseX =
            FMath::Lerp(3600.0f, 25000.0f, FMath::Frac(0.089f + SequenceT * 0.94f + 0.031f * FMath::Sin(Phase)));
        float X = BaseX;
        float Y = GetPreviewRiverCenterY(Spec, BaseX);
        float BestLateral = 0.0f;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 5; ++CandidateIndex)
        {
            const float CandidatePhase = Phase + static_cast<float>(CandidateIndex) * 0.73f;
            const float Side = ((HydraulicIndex + CandidateIndex) % 2 == 0) ? -1.0f : 1.0f;
            const float CenterHydraulicLaneMinimum = 0.34f;
            const float LaneBias = (HydraulicIndex % 5 == 0)
                ? CenterHydraulicLaneMinimum
                : (CenterHydraulicLaneMinimum + 0.44f * FMath::Abs(FMath::Sin(CandidatePhase * 0.91f)));
            const float CandidateX = BaseX + 190.0f * FMath::Sin(CandidatePhase * 1.19f);
            const float CandidateLateral =
                Side * ActiveRiverHalfWidth * LaneBias +
                FMath::Sin(CandidatePhase * 1.71f) * ActiveRiverHalfWidth * 0.10f;
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + CandidateLateral;
            const float SourceWaterT = WaterMask ? SamplePreviewMaskAtWorld(Spec, WaterMask, CandidateX, CandidateY) : 0.78f;
            const float CenterLaneT =
                1.0f - FMath::Clamp(FMath::Abs(CandidateLateral) / FMath::Max(1.0f, ActiveRiverHalfWidth), 0.0f, 1.0f);
            const float HydraulicPulse =
                0.50f + 0.36f * FMath::Sin(CandidatePhase * 1.37f) + 0.14f * FMath::Sin(CandidateX * 0.004f);
            const float Score = SourceWaterT * 0.58f + CenterLaneT * 0.26f + HydraulicPulse * 0.18f;
            if (Score > BestScore)
            {
                BestScore = Score;
                X = CandidateX;
                Y = CandidateY;
                BestLateral = CandidateLateral;
            }
        }

        const float NearFrameDemotion = SmoothPreviewStep(7600.0f, 12600.0f, X);
        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
        const float EdgeT = FMath::Clamp(FMath::Abs(BestLateral) / FMath::Max(1.0f, ActiveRiverHalfWidth), 0.0f, 1.0f);
        const float FlowPulse =
            FMath::Clamp(0.58f + 0.23f * FMath::Sin(Phase * 1.11f) + 0.16f * FMath::Sin(X * 0.0061f), 0.34f, 0.98f);
        const float MatLengthCm =
            (Spec.bDesertCanyon ? 430.0f : (Spec.bHasWaterfalls ? 340.0f : 380.0f)) *
            (0.74f + 0.16f * static_cast<float>(HydraulicIndex % 5)) *
            FMath::Clamp(FlowEnergy, 0.68f, 1.18f) *
            FMath::Lerp(0.28f, 0.78f, NearFrameDemotion);
        const float MatWidthCm =
            (Spec.bDesertCanyon ? 64.0f : (Spec.bHasWaterfalls ? 78.0f : 70.0f)) *
            (0.72f + 0.12f * static_cast<float>(HydraulicIndex % 4)) *
            FMath::Clamp(0.86f + (1.0f - EdgeT) * 0.22f, 0.74f, 1.14f) *
            FMath::Lerp(0.34f, 0.72f, NearFrameDemotion);
        const float Opacity =
            FMath::Clamp(
                HazardReadabilityOpacityLimit *
                    FMath::Clamp(0.56f + FlowPulse * 0.40f + FlowEnergy * 0.16f, 0.48f, 1.10f) *
                    FMath::Lerp(0.18f, 0.72f, NearFrameDemotion) *
                    WaterOverlaySlabOpacityDemotion,
                0.010f,
                HazardReadabilityOpacityLimit);
        const FLinearColor RawMatColor = ClampPreviewColor(FMath::Lerp(
            FMath::Lerp(Spec.WaterColor, AerationShadow, 0.56f),
            AerationCore,
            FMath::Clamp(0.28f + FlowPulse * 0.48f + (1.0f - EdgeT) * 0.10f, 0.0f, 0.84f)));
        const FLinearColor MatColor = ClampPreviewColor(FMath::Lerp(
            Spec.WaterColor,
            RawMatColor,
            FMath::Lerp(0.10f, 0.52f, NearFrameDemotion)));
        AddPreviewTranslucentMeshActor(
            World,
            PlaneMesh,
            FString::Printf(TEXT("RaftSim_FlowDependentHydraulicAerationMat_%03d_%s"), HydraulicIndex, *Spec.RiverId),
            FVector(X, Y, FMath::Max(WaterBaseZ + 32.0f + 3.6f * FMath::Sin(Phase), TerrainZ + 6.0f)),
            FRotator(0.0f, static_cast<float>((HydraulicIndex * 31) % 360), 0.0f),
            FVector(MatLengthCm / 100.0f, MatWidthCm / 100.0f, 1.0f),
            MatColor,
            Opacity);

        if (NearFrameDemotion > 0.18f || HydraulicIndex % 3 == 0)
        {
            AddPreviewFoamRibbon(
                World,
                Spec,
                FString::Printf(TEXT("RaftSim_FlowDependentWaveTrainFoamLace_%03d_%s"), HydraulicIndex, *Spec.RiverId),
                X - MatLengthCm * 0.54f,
                MatLengthCm * 0.82f,
                BestLateral + FMath::Sin(Phase * 1.73f) * MatWidthCm * 0.30f,
                FMath::Max(4.0f, MatWidthCm * 0.10f),
                Phase,
                MatColor);
        }

        if (SphereMesh)
        {
            const int32 BaseSprayBeads = Spec.bDesertCanyon ? 1 : (Spec.bHasWaterfalls ? 3 : 2);
            const int32 SprayBeadCount = FMath::Max(
                0,
                FMath::RoundToInt(static_cast<float>(BaseSprayBeads) * FMath::Clamp(FlowEnergy * NearFrameDemotion, 0.28f, 1.18f)));
            for (int32 SprayBeadIndex = 0; SprayBeadIndex < SprayBeadCount; ++SprayBeadIndex)
            {
                const float BeadPhase = Phase + static_cast<float>(SprayBeadIndex) * 1.27f;
                const float BeadX = X + FMath::Sin(BeadPhase * 1.41f) * MatLengthCm * 0.33f;
                const float BeadY = Y + FMath::Cos(BeadPhase * 1.19f) * MatWidthCm * 0.56f;
                const float BeadLift =
                    (Spec.bDesertCanyon ? 28.0f : (Spec.bHasWaterfalls ? 58.0f : 40.0f)) *
                    (0.72f + 0.16f * static_cast<float>(SprayBeadIndex)) *
                    FMath::Clamp(FlowEnergy, 0.60f, 1.16f);
                const float BeadScale =
                    (Spec.bDesertCanyon ? 0.020f : (Spec.bHasWaterfalls ? 0.030f : 0.025f)) *
                    (0.78f + 0.10f * static_cast<float>((HydraulicIndex + SprayBeadIndex) % 4));
                AddPreviewTranslucentMeshActor(
                    World,
                    SphereMesh,
                    FString::Printf(
                        TEXT("RaftSim_FlowDependentSprayBead_%03d_%02d_%s"),
                        HydraulicIndex,
                        SprayBeadIndex,
                        *Spec.RiverId),
                    FVector(BeadX, BeadY, FMath::Max(WaterBaseZ + 44.0f + BeadLift, TerrainZ + 16.0f)),
                    FRotator::ZeroRotator,
                    FVector(BeadScale, BeadScale, BeadScale),
                    MatColor,
                    FMath::Clamp(Opacity * (Spec.bHasWaterfalls ? 0.82f : 0.66f), 0.025f, 0.155f));
            }
        }
    }
}

void AddPreviewWaterSurfaceDetail(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec)
{
    if (!World)
    {
        return;
    }

    const FLinearColor CurrentHighlight = Spec.bDesertCanyon
        ? FLinearColor(0.38f, 0.31f, 0.21f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.05f, 0.39f, 0.32f) : FLinearColor(0.07f, 0.46f, 0.49f));
    const FLinearColor CurrentShadow = Spec.bDesertCanyon
        ? FLinearColor(0.30f, 0.24f, 0.17f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.03f, 0.31f, 0.25f) : FLinearColor(0.04f, 0.36f, 0.39f));
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float CurrentCueScale = FMath::Max(0.35f, Spec.FlowCurrentCueScale);
    const float CurrentStreakNearFrameStartX = 13800.0f;
    const float CurrentStreakLengthScale = 0.15f;
    const float CurrentStreakArtifactDemotion = 0.0f;
    const int32 BaseCurrentCount = Spec.bDesertCanyon ? 2 : (Spec.bHasWaterfalls ? 3 : 3);
    const int32 CurrentCount =
        FMath::Max(1, FMath::RoundToInt(static_cast<float>(BaseCurrentCount) * FMath::Clamp(CurrentCueScale, 0.5f, 1.3f)));
    for (int32 CurrentIndex = 0; CurrentIndex < CurrentCount; ++CurrentIndex)
    {
        const float X = FMath::Lerp(
            CurrentStreakNearFrameStartX,
            23800.0f,
            static_cast<float>(CurrentIndex) / static_cast<float>(FMath::Max(1, CurrentCount - 1)));
        const float SideBias = (CurrentIndex % 2 == 0) ? -1.0f : 1.0f;
        const float Lateral =
            (SideBias * 0.18f + FMath::Sin(static_cast<float>(CurrentIndex) * 1.37f) * 0.18f) *
            ActiveRiverHalfWidth;
        const float Length = (Spec.bDesertCanyon ? 1380.0f : 980.0f) * CurrentCueScale * CurrentStreakLengthScale;
        const FLinearColor DetailColor =
            ClampPreviewColor(FMath::Lerp(
                Spec.WaterColor,
                FMath::Lerp(CurrentShadow, CurrentHighlight, 0.50f + 0.18f * FMath::Sin(static_cast<float>(CurrentIndex) * 0.91f)),
                0.20f * CurrentStreakArtifactDemotion));
        AddPreviewFlowTextureRibbon(
            World,
            Spec,
            FString::Printf(TEXT("RaftSim_CurrentStreak_%02d_%s"), CurrentIndex, *Spec.RiverId),
            X,
            Length,
            Lateral,
            (2.6f + 0.9f * static_cast<float>(CurrentIndex % 3)) * CurrentCueScale,
            static_cast<float>(CurrentIndex) * 0.61f,
            DetailColor,
            FMath::Lerp(Spec.WaterColor, DetailColor, 0.18f * CurrentStreakArtifactDemotion));
    }
}

void AddPreviewWaterMicroRippleGlintDetail(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec, UStaticMesh* PlaneMesh)
{
    if (!World || !PlaneMesh)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float FlowEnergy = FMath::Clamp(0.55f * Spec.FlowCurrentCueScale + 0.45f * Spec.FlowFoamScale, 0.55f, 1.45f);
    const int32 BaseRippleCount = Spec.bDesertCanyon ? 86 : (Spec.bHasWaterfalls ? 132 : 112);
    const int32 RippleCount =
        FMath::Max(1, FMath::RoundToInt(static_cast<float>(BaseRippleCount) * FMath::Clamp(FlowEnergy, 0.68f, 1.28f)));

    const FLinearColor BrightGlint = Spec.bDesertCanyon
        ? FLinearColor(0.78f, 0.70f, 0.52f, 1.0f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.48f, 0.92f, 0.76f, 1.0f) : FLinearColor(0.52f, 0.92f, 0.92f, 1.0f));
    const float DarkMicroRippleArtifactDemotion = 0.0f;
    const FLinearColor RawDarkRipple = Spec.bDesertCanyon
        ? FLinearColor(0.26f, 0.24f, 0.17f, 1.0f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.020f, 0.22f, 0.17f, 1.0f) : FLinearColor(0.025f, 0.27f, 0.30f, 1.0f));
    const FLinearColor DarkRipple =
        FMath::Lerp(Spec.WaterColor, RawDarkRipple, DarkMicroRippleArtifactDemotion);
    const FLinearColor BankTint = Spec.bDesertCanyon
        ? FLinearColor(0.50f, 0.40f, 0.26f, 1.0f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.11f, 0.36f, 0.24f, 1.0f) : FLinearColor(0.12f, 0.42f, 0.38f, 1.0f));
    for (int32 RippleIndex = 0; RippleIndex < RippleCount; ++RippleIndex)
    {
        const float SequenceT = static_cast<float>(RippleIndex) / static_cast<float>(FMath::Max(1, RippleCount - 1));
        const float Phase = static_cast<float>(RippleIndex) * 1.6180339f;
        const float X = FMath::Lerp(-4300.0f, 24850.0f, FMath::Frac(0.071f + SequenceT * 0.91f + 0.019f * FMath::Sin(Phase)));
        const float Width =
            ActiveRiverHalfWidth * (0.93f + 0.09f * FMath::Sin(X * 0.0012f) + (Spec.bDesertCanyon ? 0.15f : 0.04f));
        const float LateralT = FMath::Sin(Phase * 0.77f) * 0.62f + FMath::Sin(Phase * 1.31f) * 0.22f;
        const float Lateral = FMath::Clamp(LateralT, -0.92f, 0.92f) * Width;
        const float EdgeT = FMath::Pow(FMath::Abs(Lateral) / FMath::Max(1.0f, Width), 1.35f);
        const bool bBright = (RippleIndex % 4) != 0;
        const FLinearColor RippleColor = bBright
            ? FMath::Lerp(BrightGlint, BankTint, FMath::Clamp(EdgeT * 0.42f, 0.0f, 0.48f))
            : FMath::Lerp(DarkRipple, BankTint, FMath::Clamp(EdgeT * 0.32f, 0.0f, 0.42f));
        const float LengthCm =
            (Spec.bDesertCanyon ? 620.0f : 520.0f) *
            (0.74f + 0.24f * static_cast<float>(RippleIndex % 5)) *
            FMath::Clamp(FlowEnergy, 0.72f, 1.18f);
        const float WidthCm =
            (Spec.bDesertCanyon ? 13.0f : 11.0f) *
            (0.82f + 0.18f * static_cast<float>(RippleIndex % 4));
        const FLinearColor RibbonHighlight = bBright ? RippleColor : FMath::Lerp(RippleColor, BrightGlint, 0.18f);
        const FLinearColor RibbonShadow = bBright ? FMath::Lerp(DarkRipple, RippleColor, 0.35f) : RippleColor;

        AddPreviewFlowTextureRibbon(
            World,
            Spec,
            FString::Printf(TEXT("RaftSim_WaterMicroRippleGlint_%03d_%s"), RippleIndex, *Spec.RiverId),
            X - LengthCm * 0.50f,
            LengthCm,
            Lateral,
            WidthCm,
            Phase,
            RibbonHighlight,
            RibbonShadow);
    }
}

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

void AddPreviewCameraAndStart(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec)
{
    if (!World || !GEditor)
    {
        return;
    }
    const FRaftSimPhotographicCaptureSettings CaptureSettings =
        GetPhotographicCaptureSettings(Spec.RiverId);

    ACameraActor* Camera = Cast<ACameraActor>(
        GEditor->AddActor(World->GetCurrentLevel(), ACameraActor::StaticClass(), FTransform(FRotator(-13.5f, 0.0f, 0.0f), FVector(-5250.0f, GetPreviewRiverCenterY(Spec, -5250.0f), 140.0f))));
    if (Camera)
    {
        Camera->SetActorLabel(TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"));
        Camera->GetCameraComponent()->FieldOfView = Spec.bDesertCanyon ? 66.0f : 68.0f;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_VignetteIntensity = true;
        Camera->GetCameraComponent()->PostProcessSettings.VignetteIntensity = CaptureSettings.Vignette;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_Sharpen = true;
        Camera->GetCameraComponent()->PostProcessSettings.Sharpen = CaptureSettings.Sharpen;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_ColorSaturation = true;
        Camera->GetCameraComponent()->PostProcessSettings.ColorSaturation =
            FVector4(
                CaptureSettings.Saturation,
                CaptureSettings.Saturation,
                CaptureSettings.Saturation,
                1.0f);
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_ColorContrast = true;
        Camera->GetCameraComponent()->PostProcessSettings.ColorContrast =
            FVector4(
                CaptureSettings.Contrast,
                CaptureSettings.Contrast,
                CaptureSettings.Contrast,
                1.0f);
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_AutoExposureMethod = true;
        Camera->GetCameraComponent()->PostProcessSettings.AutoExposureMethod = AEM_Manual;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_AutoExposureBias = true;
        Camera->GetCameraComponent()->PostProcessSettings.AutoExposureBias =
            CaptureSettings.ExposureBias;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_AutoExposureApplyPhysicalCameraExposure = true;
        Camera->GetCameraComponent()->PostProcessSettings.AutoExposureApplyPhysicalCameraExposure = 0;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_FilmGrainIntensity = true;
        Camera->GetCameraComponent()->PostProcessSettings.FilmGrainIntensity =
            CaptureSettings.FilmGrainIntensity;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_FilmGrainIntensityShadows = true;
        Camera->GetCameraComponent()->PostProcessSettings.FilmGrainIntensityShadows = 0.0f;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_FilmGrainIntensityMidtones = true;
        Camera->GetCameraComponent()->PostProcessSettings.FilmGrainIntensityMidtones = 0.0f;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_FilmGrainIntensityHighlights = true;
        Camera->GetCameraComponent()->PostProcessSettings.FilmGrainIntensityHighlights = 0.0f;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_FilmGrainScale = true;
        Camera->GetCameraComponent()->PostProcessSettings.FilmGrainScale = FVector2f(1.0f, 1.0f);
        GEditor->SelectActor(Camera, true, false, true);
    }

    const float RiverEyeCameraX = Spec.bDesertCanyon ? -3620.0f : -5250.0f;
    const float RiverEyeCameraY = GetPreviewRiverCenterY(Spec, RiverEyeCameraX);
    const float RiverEyeTargetX = RiverEyeCameraX + (Spec.bHasWaterfalls ? 7200.0f : 6400.0f);
    const float RiverEyeTargetY = GetPreviewRiverCenterY(Spec, RiverEyeTargetX);
    const float RiverEyeCenterlineFollowingYawDeg =
        FMath::RadiansToDegrees(FMath::Atan2(RiverEyeTargetY - RiverEyeCameraY, RiverEyeTargetX - RiverEyeCameraX));
    ACameraActor* RiverEyeCamera = Cast<ACameraActor>(
        GEditor->AddActor(
            World->GetCurrentLevel(),
            ACameraActor::StaticClass(),
            FTransform(
                FRotator(Spec.bDesertCanyon ? -10.5f : -12.75f, RiverEyeCenterlineFollowingYawDeg, 0.0f),
                FVector(
                    RiverEyeCameraX,
                    RiverEyeCameraY,
                    Spec.bDesertCanyon ? 152.0f : 162.0f))));
    if (RiverEyeCamera)
    {
        RiverEyeCamera->SetActorLabel(TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"));
        RiverEyeCamera->GetCameraComponent()->FieldOfView =
            Spec.bDesertCanyon ? 64.0f : 66.0f;
        if (Camera && Camera->GetCameraComponent())
        {
            RiverEyeCamera->GetCameraComponent()->PostProcessSettings =
                Camera->GetCameraComponent()->PostProcessSettings;
            RiverEyeCamera->GetCameraComponent()->PostProcessBlendWeight =
                Camera->GetCameraComponent()->PostProcessBlendWeight;
        }
    }

    if (Spec.RiverId == TEXT("american_south_fork"))
    {
        constexpr float SolverRapidCameraX = 240.0f;
        constexpr float SolverRapidTargetX = 4740.0f;
        const float SolverRapidCameraY = GetPreviewRiverCenterY(Spec, SolverRapidCameraX);
        const float SolverRapidTargetY = GetPreviewRiverCenterY(Spec, SolverRapidTargetX);
        const float SolverRapidYawDeg = FMath::RadiansToDegrees(
            FMath::Atan2(
                SolverRapidTargetY - SolverRapidCameraY,
                SolverRapidTargetX - SolverRapidCameraX));
        ACameraActor* SolverRapidCamera = Cast<ACameraActor>(
            GEditor->AddActor(
                World->GetCurrentLevel(),
                ACameraActor::StaticClass(),
                FTransform(
                    FRotator(-9.5f, SolverRapidYawDeg, 0.0f),
                    FVector(SolverRapidCameraX, SolverRapidCameraY, 168.0f))));
        if (SolverRapidCamera)
        {
            SolverRapidCamera->SetActorLabel(TEXT("RaftSim_SolverRapid_RiverEyeCaptureCamera"));
            SolverRapidCamera->GetCameraComponent()->FieldOfView = 70.0f;
            if (RiverEyeCamera && RiverEyeCamera->GetCameraComponent())
            {
                SolverRapidCamera->GetCameraComponent()->PostProcessSettings =
                    RiverEyeCamera->GetCameraComponent()->PostProcessSettings;
                SolverRapidCamera->GetCameraComponent()->PostProcessBlendWeight =
                    RiverEyeCamera->GetCameraComponent()->PostProcessBlendWeight;
            }
        }
    }

    APlayerStart* PlayerStart = Cast<APlayerStart>(
        GEditor->AddActor(World->GetCurrentLevel(), APlayerStart::StaticClass(), FTransform(FRotator::ZeroRotator, FVector(-5350.0f, GetPreviewRiverCenterY(Spec, -5350.0f), 120.0f))));
    if (PlayerStart)
    {
        PlayerStart->SetActorLabel(TEXT("RaftSim_GuideSeat_PlayerStart"));
    }

}

bool SavePreviewWorld(UWorld* World, const FString& PackagePath, FString& OutSummary)
{
    if (!World)
    {
        OutSummary += TEXT("No world to save.\n");
        return false;
    }

    World->MarkPackageDirty();
    const FString Filename = FPackageName::LongPackageNameToFilename(PackagePath, FPackageName::GetMapPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    const bool bSaved = FEditorFileUtils::SaveMap(World, Filename);
    OutSummary += FString::Printf(TEXT("%s %s -> %s\n"), bSaved ? TEXT("Saved") : TEXT("Failed"), *PackagePath, *Filename);
    return bSaved;
}

FString GetPreviewCaptureRelativePath(const FRaftSimEnvironmentPreviewSpec& Spec, const FString& CaptureId)
{
    return FPaths::Combine(
        TEXT("docs/environment-captures/photoreal_river_previews"),
        Spec.RiverId + TEXT("_") + CaptureId + TEXT(".png"));
}

FString GetPreviewFlowVariantCaptureRelativePath(const FRaftSimEnvironmentPreviewSpec& Spec, const FString& CaptureId)
{
    return FPaths::Combine(
        TEXT("docs/environment-captures/photoreal_river_previews/flow_variants"),
        Spec.RiverId + TEXT("_") + Spec.FlowBandId + TEXT("_") + CaptureId + TEXT(".png"));
}

FString GetPreviewFidelityNote(const FRaftSimEnvironmentPreviewSpec& Spec)
{
    const FString AtlasApplicationNote = TEXT("; first-party material texture atlas albedo tiles are sampled into terrain, primary boulder, and foliage vertex colors, while raft/oar atlas materials remain available for future foreground-art approval and river water keeps generated vertex-current color with review-material atlas/source texture weights culled to avoid repeated corridor-map tile artifacts; normal plus packed AO/roughness/height atlases drive bounded preview material response for non-water surfaces; first-party generated close-range terrain albedo, normal, and packed AO/roughness/height detail textures now use dedicated per-river tiled UV scale and bounded terrain-only blends beneath the corridor-scale source drape; source DEM/heightfield geometry uses bilinear sampling, bounded center-seam feathering, meter-scale macro relief, multi-scale local erosion residuals, and reduced normal flattening as the authoritative preview terrain mesh; the authoritative river ribbon preserves normals from its flow-dependent wave geometry, samples tile-safe first-party water normal detail, and uses river-specific bounded emissive, roughness, specular, and normal response instead of a flat up-normal high-roughness surface; water, boulder, foliage, and raft review material instances remain assigned, while source-baked terrain stays on its proven lit vertex-color material after the loaded atlas terrain candidate rendered black; lifelike-candidate maps skip placeholder raft/oar proxy generation and capture exports still cull any legacy foreground raft/oar proxies until approved production foreground art exists; all detail assets, source-derived terrain, and water light-response values remain candidate-only until Landscape/Nanite and WaterBody/custom shader promotion, reflection/refraction, capture, art, guide/geospatial, hazard readability, rights/provenance, and desktop/VR performance review pass");
    if (!Spec.SourceDrapeDescription.IsEmpty())
    {
        return Spec.SourceDrapeDescription + AtlasApplicationNote;
    }

    return FString(TEXT("source-aware procedural blockout with generated valley, river, foam, rocks, foliage, and raft proxies; not yet production photoreal")) +
        AtlasApplicationNote;
}

ACameraActor* FindPreviewCaptureCamera(UWorld* World, const FString& PreferredCameraLabel)
{
    ACameraActor* FallbackCamera = nullptr;
    for (TActorIterator<ACameraActor> It(World); It; ++It)
    {
        ACameraActor* Camera = *It;
        if (!FallbackCamera)
        {
            FallbackCamera = Camera;
        }

        if (Camera && Camera->GetActorLabel() == PreferredCameraLabel)
        {
            return Camera;
        }
    }

    return FallbackCamera;
}

bool CapturePreviewImageForSpec(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FString& CaptureRoot,
    FString& OutRelativeCapturePath,
    const FString& CameraLabel,
    const FString& CaptureId,
    const FString& CaptureDescription,
    bool bHideForegroundRaftProxies,
    FString& OutSummary)
{
    const FString MapFilename =
        FPackageName::LongPackageNameToFilename(Spec.MapPackagePath, FPackageName::GetMapPackageExtension());
    if (!FPaths::FileExists(MapFilename))
    {
        OutSummary += FString::Printf(TEXT("Missing preview map for capture: %s\n"), *MapFilename);
        return false;
    }

    UWorld* World = UEditorLoadingAndSavingUtils::LoadMap(MapFilename);
    if (!World)
    {
        OutSummary += FString::Printf(TEXT("Failed to load preview map for capture: %s\n"), *Spec.MapPackagePath);
        return false;
    }

    FlushAsyncLoading();
    World->FlushLevelStreaming(EFlushLevelStreamingType::Full);
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
    }
    for (TActorIterator<ALandscapeProxy> It(World); It; ++It)
    {
        ALandscapeProxy* LandscapeProxy = *It;
        if (LandscapeProxy)
        {
            LandscapeProxy->RecreateComponentsState();
        }
    }
    World->SendAllEndOfFrameUpdates();
    FlushRenderingCommands();
    if (GEditor)
    {
        GEditor->SelectNone(false, true, false);
    }

    ACameraActor* Camera = FindPreviewCaptureCamera(World, CameraLabel);
    if (!Camera || !Camera->GetCameraComponent())
    {
        OutSummary += FString::Printf(TEXT("No %s capture camera found in %s\n"), *CaptureDescription, *Spec.MapPackagePath);
        return false;
    }

    UTextureRenderTarget2D* RenderTarget =
        NewObject<UTextureRenderTarget2D>(GetTransientPackage(), NAME_None, RF_Transient);
    if (!RenderTarget)
    {
        OutSummary += FString::Printf(TEXT("Failed to allocate render target for %s\n"), *Spec.RiverId);
        return false;
    }

    constexpr int32 CaptureWidth = 1280;
    constexpr int32 CaptureHeight = 720;
    RenderTarget->RenderTargetFormat = RTF_RGBA8_SRGB;
    RenderTarget->ClearColor = FLinearColor::Black;
    RenderTarget->InitAutoFormat(CaptureWidth, CaptureHeight);
    RenderTarget->UpdateResourceImmediate(true);

    ASceneCapture2D* SceneCapture =
        World->SpawnActor<ASceneCapture2D>(ASceneCapture2D::StaticClass(), Camera->GetActorLocation(), Camera->GetActorRotation());
    if (!SceneCapture || !SceneCapture->GetCaptureComponent2D())
    {
        OutSummary += FString::Printf(TEXT("Failed to spawn scene capture for %s\n"), *Spec.RiverId);
        return false;
    }

    USceneCaptureComponent2D* CaptureComponent = SceneCapture->GetCaptureComponent2D();
    FMinimalViewInfo CameraView;
    Camera->GetCameraComponent()->GetCameraView(0.0f, CameraView);
    CaptureComponent->SetCameraView(CameraView);
    CaptureComponent->PostProcessSettings = Camera->GetCameraComponent()->PostProcessSettings;
    CaptureComponent->PostProcessSettings.bOverride_ScreenSpaceReflectionIntensity = true;
    CaptureComponent->PostProcessSettings.ScreenSpaceReflectionIntensity = 100.0f;
    CaptureComponent->PostProcessSettings.bOverride_ScreenSpaceReflectionQuality = true;
    CaptureComponent->PostProcessSettings.ScreenSpaceReflectionQuality = 100.0f;
    CaptureComponent->PostProcessSettings.bOverride_ScreenSpaceReflectionMaxRoughness = true;
    CaptureComponent->PostProcessSettings.ScreenSpaceReflectionMaxRoughness = 0.85f;
    CaptureComponent->PostProcessBlendWeight = 1.0f;
    CaptureComponent->TextureTarget = RenderTarget;
    CaptureComponent->CaptureSource = SCS_FinalColorLDR;
    CaptureComponent->bCaptureEveryFrame = false;
    CaptureComponent->bCaptureOnMovement = false;
    CaptureComponent->bAlwaysPersistRenderingState = true;
    CaptureComponent->ShowFlags.SetScreenSpaceReflections(true);
    CaptureComponent->ShowFlags.SetReflectionEnvironment(true);
    CaptureComponent->ShowFlags.SetSelection(false);
    CaptureComponent->ShowFlags.SetModeWidgets(false);
    CaptureComponent->ShowFlags.SetCompositeEditorPrimitives(false);

    struct FForegroundRaftProxyHiddenState
    {
        struct FComponentHiddenState
        {
            UPrimitiveComponent* Component = nullptr;
            bool bWasVisible = true;
            bool bWasHiddenInGame = false;
        };

        AActor* Actor = nullptr;
        bool bWasHiddenInGame = false;
        bool bWasTemporarilyHiddenInEditor = false;
        FVector OriginalLocation = FVector::ZeroVector;
        TArray<FComponentHiddenState> ComponentStates;
    };
    TArray<FForegroundRaftProxyHiddenState> ForegroundRaftProxyHiddenStates;
    auto RestoreForegroundRaftProxyVisibility = [&ForegroundRaftProxyHiddenStates]()
    {
        for (const FForegroundRaftProxyHiddenState& HiddenState : ForegroundRaftProxyHiddenStates)
        {
            if (HiddenState.Actor)
            {
                HiddenState.Actor->SetActorLocation(HiddenState.OriginalLocation, false, nullptr, ETeleportType::TeleportPhysics);
                HiddenState.Actor->SetActorHiddenInGame(HiddenState.bWasHiddenInGame);
                HiddenState.Actor->SetIsTemporarilyHiddenInEditor(HiddenState.bWasTemporarilyHiddenInEditor);
            }
            for (const FForegroundRaftProxyHiddenState::FComponentHiddenState& ComponentState : HiddenState.ComponentStates)
            {
                if (ComponentState.Component)
                {
                    ComponentState.Component->SetVisibility(ComponentState.bWasVisible, true);
                    ComponentState.Component->SetHiddenInGame(ComponentState.bWasHiddenInGame, true);
                }
            }
        }
    };
    int32 CulledReviewOnlyForegroundActorCount = 0;
    int32 CulledReviewOnlyForegroundComponentCount = 0;
    if (bHideForegroundRaftProxies)
    {
        const FName ForegroundRaftProxyTag(TEXT("RaftSim_ForegroundRaft"));
        auto HasReviewOnlyForegroundToken = [](const FString& Value)
        {
            return Value.Contains(TEXT("RaftSim_ForegroundRaft_")) ||
                Value.Contains(TEXT("ForegroundRaft")) ||
                Value.Contains(TEXT("RaftForegroundReview")) ||
                Value.Contains(TEXT("OarBlade")) ||
                Value.Contains(TEXT("OarShaft"));
        };
        auto HasReviewOnlyNearFieldToken = [](const FString& Value)
        {
            return Value.Contains(TEXT("RaftSim_NearFieldRiverbedDebrisDressing_")) ||
                Value.Contains(TEXT("RaftSim_NearFieldRiverbedPebbleDressing_")) ||
                Value.Contains(TEXT("RaftSim_NearFieldPhotorealBankShelf_")) ||
                Value.Contains(TEXT("RaftSim_NearFieldCaptureQualityWetRock_"));
        };
        auto ComponentUsesReviewOnlyForegroundMaterial = [&HasReviewOnlyForegroundToken](UPrimitiveComponent* PrimitiveComponent)
        {
            UMeshComponent* MeshComponent = Cast<UMeshComponent>(PrimitiveComponent);
            if (!MeshComponent)
            {
                return false;
            }
            const int32 MaterialCount = MeshComponent->GetNumMaterials();
            for (int32 MaterialIndex = 0; MaterialIndex < MaterialCount; ++MaterialIndex)
            {
                UMaterialInterface* Material = MeshComponent->GetMaterial(MaterialIndex);
                if (Material &&
                    (HasReviewOnlyForegroundToken(Material->GetName()) ||
                     HasReviewOnlyForegroundToken(Material->GetPathName())))
                {
                    return true;
                }
            }
            return false;
        };
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            AActor* Actor = *It;
            if (!Actor)
            {
                continue;
            }

            const FString ActorLabel = Actor->GetActorLabel();
            const FString ActorName = Actor->GetName();
            const bool bIsReviewOnlyActor =
                Actor->ActorHasTag(ForegroundRaftProxyTag) ||
                HasReviewOnlyForegroundToken(ActorLabel) ||
                HasReviewOnlyForegroundToken(ActorName) ||
                HasReviewOnlyNearFieldToken(ActorLabel) ||
                HasReviewOnlyNearFieldToken(ActorName);

            TArray<UPrimitiveComponent*> PrimitiveComponents;
            Actor->GetComponents<UPrimitiveComponent>(PrimitiveComponents);
            TArray<UPrimitiveComponent*> ComponentsToHide;
            for (UPrimitiveComponent* PrimitiveComponent : PrimitiveComponents)
            {
                if (!PrimitiveComponent)
                {
                    continue;
                }

                const bool bIsReviewOnlyComponent =
                    bIsReviewOnlyActor ||
                    HasReviewOnlyForegroundToken(PrimitiveComponent->GetName()) ||
                    HasReviewOnlyForegroundToken(PrimitiveComponent->GetPathName()) ||
                    ComponentUsesReviewOnlyForegroundMaterial(PrimitiveComponent);
                if (bIsReviewOnlyComponent)
                {
                    ComponentsToHide.Add(PrimitiveComponent);
                }
            }

            if (ComponentsToHide.IsEmpty())
            {
                continue;
            }

            const bool bHideWholeActor = bIsReviewOnlyActor || ComponentsToHide.Num() == PrimitiveComponents.Num();
            if (bHideWholeActor)
            {
                CaptureComponent->HideActorComponents(Actor);
                CaptureComponent->HiddenActors.AddUnique(Actor);
                ++CulledReviewOnlyForegroundActorCount;
            }

            FForegroundRaftProxyHiddenState HiddenState;
            HiddenState.Actor = Actor;
            HiddenState.bWasHiddenInGame = Actor->IsHidden();
            HiddenState.bWasTemporarilyHiddenInEditor = Actor->IsTemporarilyHiddenInEditor(false);
            HiddenState.OriginalLocation = Actor->GetActorLocation();
            for (UPrimitiveComponent* PrimitiveComponent : ComponentsToHide)
            {
                if (PrimitiveComponent)
                {
                    CaptureComponent->HideComponent(PrimitiveComponent);
                    HiddenState.ComponentStates.Add(
                        {PrimitiveComponent, PrimitiveComponent->IsVisible(), PrimitiveComponent->bHiddenInGame});
                    PrimitiveComponent->SetVisibility(false, true);
                    PrimitiveComponent->SetHiddenInGame(true, true);
                    ++CulledReviewOnlyForegroundComponentCount;
                }
            }

            ForegroundRaftProxyHiddenStates.Add(MoveTemp(HiddenState));
            if (bHideWholeActor)
            {
                Actor->SetActorHiddenInGame(true);
                Actor->SetIsTemporarilyHiddenInEditor(true);
                Actor->SetActorLocation(
                    Actor->GetActorLocation() + FVector(0.0f, 0.0f, -100000.0f),
                    false,
                    nullptr,
                    ETeleportType::TeleportPhysics);
            }
        }
        OutSummary += FString::Printf(
            TEXT("Culled %d review-only foreground/near-field actors and %d primitive components for %s capture.\n"),
            CulledReviewOnlyForegroundActorCount,
            CulledReviewOnlyForegroundComponentCount,
            *Spec.RiverId);
    }
    const bool bUseTemporaryRiverEyeCenterArtifactCover = false;
    AActor* RiverEyeCenterArtifactCoverActor = bHideForegroundRaftProxies && bUseTemporaryRiverEyeCenterArtifactCover
        ? AddPreviewRiverEyeCenterArtifactCover(World, Spec)
        : nullptr;
    auto DestroyRiverEyeCenterArtifactCover = [&RiverEyeCenterArtifactCoverActor]()
    {
        if (RiverEyeCenterArtifactCoverActor)
        {
            RiverEyeCenterArtifactCoverActor->Destroy();
            RiverEyeCenterArtifactCoverActor = nullptr;
        }
    };
    CaptureComponent->CaptureScene();
    FlushRenderingCommands();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
    }
    for (TActorIterator<ALandscapeProxy> It(World); It; ++It)
    {
        ALandscapeProxy* LandscapeProxy = *It;
        if (LandscapeProxy)
        {
            LandscapeProxy->RecreateComponentsState();
        }
    }
    World->SendAllEndOfFrameUpdates();
    FlushRenderingCommands();
    FPlatformProcess::Sleep(0.03f);
    CaptureComponent->CaptureScene();
    FlushRenderingCommands();

    FTextureRenderTargetResource* RenderTargetResource = RenderTarget->GameThread_GetRenderTargetResource();
    TArray<FColor> ImageData;
    if (!RenderTargetResource || !RenderTargetResource->ReadPixels(ImageData) ||
        ImageData.Num() != CaptureWidth * CaptureHeight)
    {
        DestroyRiverEyeCenterArtifactCover();
        RestoreForegroundRaftProxyVisibility();
        SceneCapture->Destroy();
        RenderTarget->ReleaseResource();
        OutSummary += FString::Printf(TEXT("Failed to read rendered pixels for %s\n"), *Spec.RiverId);
        return false;
    }

    const bool bApplyFirstPartyCaptureFilmGrainDither = false;
    const uint32 FirstPartyCaptureFilmGrainDitherSeed =
        GetTypeHash(Spec.RiverId) ^ (GetTypeHash(CaptureId) * 16777619u);
    for (int32 PixelIndex = 0; PixelIndex < ImageData.Num(); ++PixelIndex)
    {
        FColor& Pixel = ImageData[PixelIndex];
        Pixel.A = 255;
        if (bApplyFirstPartyCaptureFilmGrainDither)
        {
            const int32 PixelX = PixelIndex % CaptureWidth;
            const int32 PixelY = PixelIndex / CaptureWidth;
            const uint32 DitherCellX = static_cast<uint32>(PixelX / 4);
            const uint32 DitherCellY = static_cast<uint32>(PixelY / 4);
            uint32 DitherHash =
                FirstPartyCaptureFilmGrainDitherSeed ^
                (DitherCellX * 73856093u) ^
                (DitherCellY * 19349663u);
            DitherHash ^= (DitherHash >> 13);
            DitherHash *= 1274126177u;
            DitherHash ^= (DitherHash >> 16);

            const int32 FirstPartyCaptureFilmGrainDitherStrength =
                bHideForegroundRaftProxies ? 13 : 9;
            const int32 RedOffset =
                (static_cast<int32>(DitherHash & 0x1Fu) - 15) *
                FirstPartyCaptureFilmGrainDitherStrength / 15;
            const int32 GreenOffset =
                (static_cast<int32>((DitherHash >> 5) & 0x1Fu) - 15) *
                FirstPartyCaptureFilmGrainDitherStrength / 15;
            const int32 BlueOffset =
                (static_cast<int32>((DitherHash >> 10) & 0x1Fu) - 15) *
                FirstPartyCaptureFilmGrainDitherStrength / 15;
            Pixel.R = static_cast<uint8>(FMath::Clamp(static_cast<int32>(Pixel.R) + RedOffset, 0, 255));
            Pixel.G = static_cast<uint8>(FMath::Clamp(static_cast<int32>(Pixel.G) + GreenOffset, 0, 255));
            Pixel.B = static_cast<uint8>(FMath::Clamp(static_cast<int32>(Pixel.B) + BlueOffset, 0, 255));
        }
    }

    TArray64<uint8> CompressedPng;
    FImageUtils::PNGCompressImageArray(CaptureWidth, CaptureHeight, MakeArrayView(ImageData), CompressedPng);

    if (OutRelativeCapturePath.IsEmpty())
    {
        OutRelativeCapturePath = GetPreviewCaptureRelativePath(Spec, CaptureId);
    }
    const FString AbsoluteCapturePath = FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), OutRelativeCapturePath));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(AbsoluteCapturePath), true);
    const bool bSaved = FFileHelper::SaveArrayToFile(CompressedPng, *AbsoluteCapturePath);

    DestroyRiverEyeCenterArtifactCover();
    RestoreForegroundRaftProxyVisibility();
    SceneCapture->Destroy();
    RenderTarget->ReleaseResource();

    OutSummary += FString::Printf(
        TEXT("%s rendered %s capture for %s -> %s\n"),
        bSaved ? TEXT("Saved") : TEXT("Failed"),
        *CaptureDescription,
        *Spec.DisplayName,
        *AbsoluteCapturePath);
    return bSaved;
}

UMaterialInstanceConstant* LoadOrCreateLandscapeCandidateFoliageMaterialInstance(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const TCHAR* FoliageType,
    const TCHAR* SourceParentObjectPath,
    const FLinearColor& FrontTint,
    const FLinearColor& BackTint,
    const FLinearColor& TransmissionTint,
    float RoughnessStrength,
    float NormalStrength,
    FString& OutSummary)
{
    UMaterialInterface* SourceParent = LoadObject<UMaterialInterface>(nullptr, SourceParentObjectPath);
    const FString RiverAssetName = GetFirstPartyMaterialRiverAssetName(Spec.RiverId);
    if (!SourceParent || RiverAssetName.IsEmpty())
    {
        OutSummary += FString::Printf(
            TEXT("Failed to load %s foliage parent for %s.\n"),
            FoliageType,
            *Spec.RiverId);
        return nullptr;
    }

    const FString AssetName = FString::Printf(
        TEXT("MI_RaftSim_%s_%s_BiomeFoliageCandidate"),
        *RiverAssetName,
        FoliageType);
    const FString PackagePath = FString::Printf(
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/%s"),
        *AssetName);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, *AssetName);
    UPackage* Package = CreatePackage(*PackagePath);
    if (!Package)
    {
        return nullptr;
    }

    UMaterialInstanceConstant* Instance = Cast<UMaterialInstanceConstant>(
        StaticLoadObject(UMaterialInstanceConstant::StaticClass(), nullptr, *ObjectPath));
    if (!Instance)
    {
        Instance = FindObject<UMaterialInstanceConstant>(Package, *AssetName);
    }
    if (!Instance)
    {
        Instance = NewObject<UMaterialInstanceConstant>(
            Package,
            *AssetName,
            RF_Public | RF_Standalone | RF_Transactional);
        if (Instance)
        {
            FAssetRegistryModule::AssetCreated(Instance);
        }
    }
    if (!Instance)
    {
        return nullptr;
    }

    Instance->Modify();
    Instance->SetParentEditorOnly(SourceParent);
    Instance->SetVectorParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("BaseColor Tint Leaves")),
        FrontTint);
    for (const TCHAR* ParameterName : {
             TEXT("BaseColor Tint Leaf Backside"),
             TEXT("Tint Leaf Backside")})
    {
        Instance->SetVectorParameterValueEditorOnly(
            FMaterialParameterInfo(ParameterName),
            BackTint);
    }
    for (const TCHAR* ParameterName : {
             TEXT("Translucency Tint Leaves"),
             TEXT("Translucency Tint"),
             TEXT("Tint Translucency")})
    {
        Instance->SetVectorParameterValueEditorOnly(
            FMaterialParameterInfo(ParameterName),
            TransmissionTint);
    }
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("Roughness Leaves Strength")),
        RoughnessStrength);
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("Roughness Leaf Backside")),
        FMath::Clamp(RoughnessStrength + 0.06f, 0.0f, 1.0f));
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("Roughness Min")),
        FMath::Clamp(RoughnessStrength - 0.12f, 0.0f, 1.0f));
    Instance->SetScalarParameterValueEditorOnly(
        FMaterialParameterInfo(TEXT("Normal Strength")),
        NormalStrength);
    Instance->PostEditChange();
    Package->MarkPackageDirty();

    const FString Filename =
        FPackageName::LongPackageNameToFilename(PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Instance, *Filename, SaveArgs))
    {
        OutSummary += FString::Printf(TEXT("Failed to save %s.\n"), *ObjectPath);
        return nullptr;
    }

    OutSummary += FString::Printf(
        TEXT("Built %s %s texture-preserving foliage candidate (roughness %.3f, normal %.3f).\n"),
        *Spec.RiverId,
        FoliageType,
        RoughnessStrength,
        NormalStrength);
    return Instance;
}

int32 BindLandscapeCandidateFoliageMaterial(
    UHierarchicalInstancedStaticMeshComponent* Component,
    UStaticMesh* Mesh,
    UMaterialInterface* FoliageMaterial)
{
    if (!Component || !Mesh || !FoliageMaterial)
    {
        return 0;
    }

    int32 BoundSlotCount = 0;
    const TArray<FStaticMaterial>& StaticMaterials = Mesh->GetStaticMaterials();
    for (int32 MaterialIndex = 0; MaterialIndex < StaticMaterials.Num(); ++MaterialIndex)
    {
        const FString SlotName = StaticMaterials[MaterialIndex].MaterialSlotName.ToString();
        UMaterialInterface* SourceMaterial = Mesh->GetMaterial(MaterialIndex);
        const bool bIsFoliageSlot =
            SlotName.Equals(TEXT("TwoSided"), ESearchCase::IgnoreCase) ||
            (SourceMaterial && SourceMaterial->GetName().Contains(TEXT("Foliage"), ESearchCase::IgnoreCase));
        if (bIsFoliageSlot)
        {
            Component->SetMaterial(MaterialIndex, FoliageMaterial);
            ++BoundSlotCount;
        }
    }
    return BoundSlotCount;
}

struct FRaftSimLandscapeImportCandidateResult
{
    uint16 SourceHeightMin = 0;
    uint16 SourceHeightMax = 0;
    uint16 ChannelFloor = 0;
    int32 ChannelModifiedSampleCount = 0;
    FVector LandscapeLocation = FVector::ZeroVector;
    FVector LandscapeScale = FVector::OneVector;
    int32 MaterialBoundComponentCount = 0;
    int32 NaniteComponentCount = 0;
    int32 NaniteMaterialSlotCount = 0;
    int32 NaniteMaterialBoundSlotCount = 0;
    int32 NaniteMaterialAuditErrorCount = 0;
    int32 DressingAssetCount = 0;
    int32 DressingBoulderInstanceCount = 0;
    int32 DressingFoliageInstanceCount = 0;
    int32 DressingTrunkInstanceCount = 0;
    int32 DressingFoliageMaterialAssetCount = 0;
    int32 DressingFoliageMaterialBoundSlotCount = 0;
    bool bDressingAssetsLoaded = false;
    bool bDressingSourceMasksLoaded = false;
    bool bDressingBoulderMeshNaniteEnabled = false;
    bool bDressingBroadleafMeshNaniteEnabled = false;
    bool bDressingConiferMeshNaniteEnabled = false;
    bool bDressingFoliageMaterialsValidated = false;
    bool bDressingValidated = false;
    FString WaterMaterialPath;
    int32 WaterMaterialBoundComponentCount = 0;
    bool bSolverSurfaceWaterMaterialBound = false;
    bool bNaniteRepresentationBuilt = false;
    bool bMaterialBindingsValidated = false;
    bool bNaniteMaterialBindingsValidated = false;
};

bool AddLandscapeCandidateBiomeDressing(
    UWorld* World,
    ALandscape* Landscape,
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    FRaftSimLandscapeImportCandidateResult& OutResult,
    FString& OutSummary)
{
    if (!World || !Landscape)
    {
        return false;
    }

    static const TCHAR* BroadleafMeshAPath =
        TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/DeciduousTree_01/Instances/Leaf_Twig_01.Leaf_Twig_01");
    static const TCHAR* BroadleafMeshBPath =
        TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/DeciduousTree_01/Instances/Leaf_Twig_03.Leaf_Twig_03");
    static const TCHAR* ConiferMeshPath =
        TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/ConiferTree_01/Instances/Conifer_Twig_01.Conifer_Twig_01");
    static const TCHAR* TrunkMeshPath = TEXT("/Engine/BasicShapes/Cylinder.Cylinder");

    UStaticMesh* BroadleafMeshA = LoadPreviewMesh(BroadleafMeshAPath);
    UStaticMesh* BroadleafMeshB = LoadPreviewMesh(BroadleafMeshBPath);
    UStaticMesh* ConiferMesh = LoadPreviewMesh(ConiferMeshPath);
    UStaticMesh* TrunkMesh = LoadPreviewMesh(TrunkMeshPath);
    for (UStaticMesh* Mesh : {BroadleafMeshA, BroadleafMeshB, ConiferMesh, TrunkMesh})
    {
        OutResult.DressingAssetCount += Mesh ? 1 : 0;
    }
    OutResult.bDressingAssetsLoaded = OutResult.DressingAssetCount == 4;
    if (!OutResult.bDressingAssetsLoaded)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape biome dressing for %s loaded %d/4 required meshes.\n"),
            *Candidate.PreviewSpec.RiverId,
            OutResult.DressingAssetCount);
        return false;
    }

    OutResult.bDressingBoulderMeshNaniteEnabled = false;
    OutResult.bDressingBroadleafMeshNaniteEnabled =
        BroadleafMeshA->IsNaniteEnabled() && BroadleafMeshB->IsNaniteEnabled();
    OutResult.bDressingConiferMeshNaniteEnabled = ConiferMesh->IsNaniteEnabled();

    FRaftSimPreviewImage WaterMask;
    FRaftSimPreviewImage VegetationMask;
    const bool bWaterMaskLoaded =
        !Candidate.PreviewSpec.WaterMaskImage.IsEmpty() &&
        LoadPreviewPngImage(Candidate.PreviewSpec.WaterMaskImage, WaterMask);
    const bool bVegetationMaskLoaded =
        !Candidate.PreviewSpec.VegetationMaskImage.IsEmpty() &&
        LoadPreviewPngImage(Candidate.PreviewSpec.VegetationMaskImage, VegetationMask);
    OutResult.bDressingSourceMasksLoaded = bWaterMaskLoaded && bVegetationMaskLoaded;
    if (!OutResult.bDressingSourceMasksLoaded)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape biome dressing for %s requires both water and vegetation masks.\n"),
            *Candidate.PreviewSpec.RiverId);
        return false;
    }

    const FRaftSimEnvironmentPreviewSpec& Spec = Candidate.PreviewSpec;
    UMaterialInterface* BarkMaterial = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/DeciduousTree_01/Materials/MI_LeafTree_01_Bark.MI_LeafTree_01_Bark"));
    const FRaftSimLandscapeCandidateFoliageSettings FoliageSettings =
        GetLandscapeCandidateFoliageSettings(Spec.RiverId);
    UMaterialInstanceConstant* BroadleafFoliageMaterial =
        LoadOrCreateLandscapeCandidateFoliageMaterialInstance(
            Spec,
            TEXT("Broadleaf"),
            TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/DeciduousTree_01/Materials/MI_LeafTree_01_Foliage.MI_LeafTree_01_Foliage"),
            FoliageSettings.BroadleafFrontTint,
            FoliageSettings.BroadleafBackTint,
            FoliageSettings.BroadleafTransmissionTint,
            FoliageSettings.RoughnessStrength,
            FoliageSettings.NormalStrength,
            OutSummary);
    UMaterialInstanceConstant* ConiferFoliageMaterial =
        LoadOrCreateLandscapeCandidateFoliageMaterialInstance(
            Spec,
            TEXT("Conifer"),
            TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/ConiferTree_01/Materials/MI_Conifer_Foliage_01.MI_Conifer_Foliage_01"),
            FoliageSettings.ConiferFrontTint,
            FoliageSettings.ConiferBackTint,
            FoliageSettings.ConiferTransmissionTint,
            FoliageSettings.RoughnessStrength,
            FoliageSettings.NormalStrength,
            OutSummary);
    OutResult.DressingFoliageMaterialAssetCount =
        (BroadleafFoliageMaterial ? 1 : 0) + (ConiferFoliageMaterial ? 1 : 0);
    if (OutResult.DressingFoliageMaterialAssetCount != 2)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape biome dressing for %s loaded %d/2 required foliage materials.\n"),
            *Spec.RiverId,
            OutResult.DressingFoliageMaterialAssetCount);
        return false;
    }
    UHierarchicalInstancedStaticMeshComponent* BroadleafInstancesA =
        AddLandscapeCandidateInstancedMeshComponent(
            World,
            BroadleafMeshA,
            FString::Printf(TEXT("RaftSim_LandscapeCandidate_PveBroadleafA_%s"), *Candidate.PreviewSpec.RiverId),
            true);
    UHierarchicalInstancedStaticMeshComponent* BroadleafInstancesB =
        AddLandscapeCandidateInstancedMeshComponent(
            World,
            BroadleafMeshB,
            FString::Printf(TEXT("RaftSim_LandscapeCandidate_PveBroadleafB_%s"), *Candidate.PreviewSpec.RiverId),
            true);
    UHierarchicalInstancedStaticMeshComponent* ConiferInstances =
        AddLandscapeCandidateInstancedMeshComponent(
            World,
            ConiferMesh,
            FString::Printf(TEXT("RaftSim_LandscapeCandidate_PveConifer_%s"), *Candidate.PreviewSpec.RiverId),
            true);
    UHierarchicalInstancedStaticMeshComponent* TrunkInstances =
        AddLandscapeCandidateInstancedMeshComponent(
            World,
            TrunkMesh,
            FString::Printf(TEXT("RaftSim_LandscapeCandidate_Trunks_%s"), *Candidate.PreviewSpec.RiverId),
            true,
            BarkMaterial);
    if (!BroadleafInstancesA || !BroadleafInstancesB ||
        !ConiferInstances || !TrunkInstances)
    {
        OutSummary += FString::Printf(
            TEXT("Failed to create one or more Landscape biome dressing instance components for %s.\n"),
            *Candidate.PreviewSpec.RiverId);
        return false;
    }
    OutResult.DressingFoliageMaterialBoundSlotCount =
        BindLandscapeCandidateFoliageMaterial(
            BroadleafInstancesA,
            BroadleafMeshA,
            BroadleafFoliageMaterial) +
        BindLandscapeCandidateFoliageMaterial(
            BroadleafInstancesB,
            BroadleafMeshB,
            BroadleafFoliageMaterial) +
        BindLandscapeCandidateFoliageMaterial(
            ConiferInstances,
            ConiferMesh,
            ConiferFoliageMaterial);
    OutResult.bDressingFoliageMaterialsValidated =
        OutResult.DressingFoliageMaterialBoundSlotCount == 3;
    if (!OutResult.bDressingFoliageMaterialsValidated)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape biome dressing for %s bound %d/3 required foliage material slots.\n"),
            *Spec.RiverId,
            OutResult.DressingFoliageMaterialBoundSlotCount);
        return false;
    }

    const bool bRainforest = Spec.bHasWaterfalls;
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float LandscapeHalfWidth = Candidate.HorizontalSpanYCm * 0.5f;
    const float MaxBankOffset = FMath::Max(
        ActiveRiverHalfWidth + 300.0f,
        LandscapeHalfWidth - 220.0f);
    auto GetLandscapeHeight = [Landscape, &Spec](float X, float Y)
    {
        return Landscape->GetHeightAtLocation(FVector(X, Y, 0.0f), EHeightfieldSource::Editor)
            .Get(Spec.FlowWaterLevelOffsetCm - 24.0f);
    };
    auto AddGroundedInstance = [](UHierarchicalInstancedStaticMeshComponent* Component,
                                  UStaticMesh* Mesh,
                                  const FVector2D& GroundLocation,
                                  float GroundZ,
                                  const FRotator& Rotation,
                                  const FVector& Scale)
    {
        const FBox Bounds = Mesh->GetBoundingBox();
        const float GroundedPivotZ = GroundZ - Bounds.Min.Z * Scale.Z;
        Component->AddInstance(
            FTransform(
                Rotation,
                FVector(GroundLocation.X, GroundLocation.Y, GroundedPivotZ),
                Scale),
            true);
    };

    const int32 BoulderCount = Spec.bDesertCanyon ? 62 : (bRainforest ? 48 : 44);
    for (int32 BoulderIndex = 0; BoulderIndex < BoulderCount; ++BoulderIndex)
    {
        const float T = (static_cast<float>(BoulderIndex) + 0.5f) / static_cast<float>(BoulderCount);
        const float Phase = static_cast<float>(BoulderIndex) * 1.6180339f;
        const float Side = (BoulderIndex % 2 == 0) ? -1.0f : 1.0f;
        const bool bChannelRock = BoulderIndex % 9 == 0;
        const float BaseX = FMath::Lerp(-1600.0f, 25500.0f, T) + 180.0f * FMath::Sin(Phase);
        const float BaseOffset = bChannelRock
            ? ActiveRiverHalfWidth * (0.62f + 0.24f * FMath::Abs(FMath::Sin(Phase * 0.77f)))
            : FMath::Lerp(
                  ActiveRiverHalfWidth + 100.0f,
                  MaxBankOffset * 0.78f,
                  FMath::Pow(FMath::Abs(FMath::Sin(Phase * 0.43f)), 0.72f));

        float BestX = BaseX;
        float BestY = GetPreviewRiverCenterY(Spec, BaseX) + Side * BaseOffset;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 7; ++CandidateIndex)
        {
            const float CandidateX = BaseX +
                155.0f * FMath::Sin(Phase * 0.61f + static_cast<float>(CandidateIndex) * 1.17f);
            const float CandidateOffset = FMath::Clamp(
                BaseOffset + 135.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 0.93f),
                ActiveRiverHalfWidth * 0.20f,
                MaxBankOffset);
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, &WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, &VegetationMask, CandidateX, CandidateY);
            const float TargetWaterT = bChannelRock ? 0.68f : 0.20f;
            const float Score = 1.0f - FMath::Abs(WaterT - TargetWaterT) -
                VegetationT * (bChannelRock ? 0.12f : 0.34f) +
                0.06f * FMath::Sin(Phase + static_cast<float>(CandidateIndex));
            if (Score > BestScore)
            {
                BestScore = Score;
                BestX = CandidateX;
                BestY = CandidateY;
            }
        }

        const float TargetBoulderHeightCm = (Spec.bDesertCanyon
            ? 82.0f + 20.0f * static_cast<float>(BoulderIndex % 5)
            : (bRainforest ? 74.0f + 18.0f * static_cast<float>(BoulderIndex % 5)
                           : 66.0f + 16.0f * static_cast<float>(BoulderIndex % 5))) *
            (bChannelRock ? 0.72f : 1.0f);
        const float BoulderScaleZ = TargetBoulderHeightCm / 100.0f;
        const FLinearColor BoulderColor = FMath::Lerp(
            ScalePreviewColor(Spec.RockColor, Spec.bDesertCanyon ? 0.70f : 0.52f),
            ScalePreviewColor(Spec.WaterColor, 0.28f),
            bChannelRock ? 0.24f : (bRainforest ? 0.16f : 0.10f));
        AActor* BoulderActor = AddPreviewIrregularRockActor(
            World,
            FString::Printf(TEXT("RaftSim_LandscapeCandidate_IrregularBoulder_%03d_%s"), BoulderIndex, *Spec.RiverId),
            FVector(BestX, BestY, GetLandscapeHeight(BestX, BestY)),
            static_cast<float>((BoulderIndex * 47) % 360),
            FVector(
                BoulderScaleZ * (1.15f + 0.08f * static_cast<float>(BoulderIndex % 4)),
                BoulderScaleZ * (0.76f + 0.07f * static_cast<float>((BoulderIndex + 2) % 5)),
                BoulderScaleZ),
            BoulderColor,
            BoulderIndex + 42000);
        if (BoulderActor)
        {
            if (UProceduralMeshComponent* BoulderComponent =
                    BoulderActor->FindComponentByClass<UProceduralMeshComponent>())
            {
                BoulderComponent->SetCastShadow(true);
                BoulderComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            }
        }
        ++OutResult.DressingBoulderInstanceCount;
    }

    const int32 FoliageClusterCount = Spec.bDesertCanyon ? 32 : (bRainforest ? 320 : 180);
    const int32 BranchesPerCluster = Spec.bDesertCanyon ? 5 : (bRainforest ? 16 : 12);
    const int32 UnderstoryBranchesPerCluster = Spec.bDesertCanyon ? 2 : (bRainforest ? 6 : 3);
    const FBox TrunkBounds = TrunkMesh->GetBoundingBox();
    const FVector TrunkSize = TrunkBounds.GetSize();
    for (int32 ClusterIndex = 0; ClusterIndex < FoliageClusterCount; ++ClusterIndex)
    {
        const float T = (static_cast<float>(ClusterIndex) + 0.5f) /
            static_cast<float>(FoliageClusterCount);
        const float Phase = static_cast<float>(ClusterIndex) * 1.3247179f;
        const float Side = (ClusterIndex % 2 == 0) ? -1.0f : 1.0f;
        const float BaseX = FMath::Lerp(-2500.0f, 25400.0f, T) + 230.0f * FMath::Sin(Phase * 0.71f);
        const float BaseOffset = FMath::Lerp(
            ActiveRiverHalfWidth + (Spec.bDesertCanyon ? 260.0f : 180.0f),
            MaxBankOffset,
            FMath::Pow(FMath::Abs(FMath::Sin(Phase * 0.47f)), bRainforest ? 0.42f : 0.66f));

        float BestX = BaseX;
        float BestY = GetPreviewRiverCenterY(Spec, BaseX) + Side * BaseOffset;
        float BestScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 8; ++CandidateIndex)
        {
            const float CandidateX = BaseX +
                190.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.07f);
            const float NearCameraMinimumOffset = CandidateX < 2600.0f
                ? ActiveRiverHalfWidth + (bRainforest ? 860.0f : (Spec.bDesertCanyon ? 720.0f : 660.0f))
                : ActiveRiverHalfWidth + 120.0f;
            const float CandidateOffset = FMath::Clamp(
                BaseOffset + 210.0f * FMath::Sin(Phase * 0.69f + static_cast<float>(CandidateIndex) * 0.89f),
                NearCameraMinimumOffset,
                MaxBankOffset);
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, &WaterMask, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, &VegetationMask, CandidateX, CandidateY);
            const float Score = VegetationT * (bRainforest ? 1.85f : (Spec.bDesertCanyon ? 0.58f : 1.34f)) -
                WaterT * 1.18f +
                0.07f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 0.83f);
            if (Score > BestScore)
            {
                BestScore = Score;
                BestX = CandidateX;
                BestY = CandidateY;
            }
        }

        const float TerrainZ = GetLandscapeHeight(BestX, BestY);
        const float TrunkHeightCm = Spec.bDesertCanyon
            ? 64.0f + 12.0f * static_cast<float>(ClusterIndex % 4)
            : (bRainforest ? 460.0f + 44.0f * static_cast<float>(ClusterIndex % 6)
                           : 330.0f + 34.0f * static_cast<float>(ClusterIndex % 5));
        const float TrunkRadiusCm = Spec.bDesertCanyon
            ? 4.0f
            : (bRainforest ? 12.0f + 1.5f * static_cast<float>(ClusterIndex % 4)
                           : 8.0f + 1.2f * static_cast<float>(ClusterIndex % 4));
        if (!Spec.bDesertCanyon || ClusterIndex % 4 == 0)
        {
            const FVector TrunkScale(
                (TrunkRadiusCm * 2.0f) / FMath::Max(1.0f, TrunkSize.X),
                (TrunkRadiusCm * 2.0f) / FMath::Max(1.0f, TrunkSize.Y),
                TrunkHeightCm / FMath::Max(1.0f, TrunkSize.Z));
            AddGroundedInstance(
                TrunkInstances,
                TrunkMesh,
                FVector2D(BestX, BestY),
                TerrainZ,
                FRotator(
                    2.5f * FMath::Sin(Phase),
                    static_cast<float>((ClusterIndex * 31) % 360),
                    2.0f * FMath::Cos(Phase * 0.73f)),
                TrunkScale);
            ++OutResult.DressingTrunkInstanceCount;
        }

        UStaticMesh* FoliageMesh = BroadleafMeshA;
        UHierarchicalInstancedStaticMeshComponent* FoliageInstances = BroadleafInstancesA;
        if (!Spec.bDesertCanyon && !bRainforest && ClusterIndex % 4 == 0)
        {
            FoliageMesh = ConiferMesh;
            FoliageInstances = ConiferInstances;
        }
        else if (ClusterIndex % 2 == 1)
        {
            FoliageMesh = BroadleafMeshB;
            FoliageInstances = BroadleafInstancesB;
        }
        const float FoliageMeshSpanCm = FMath::Max(1.0f, FoliageMesh->GetBoundingBox().GetSize().GetMax());
        const float BranchTargetSpanCm = Spec.bDesertCanyon
            ? 78.0f + 12.0f * static_cast<float>(ClusterIndex % 4)
            : (bRainforest ? 190.0f + 26.0f * static_cast<float>(ClusterIndex % 5)
                           : 145.0f + 20.0f * static_cast<float>(ClusterIndex % 4));
        const float BranchScale = BranchTargetSpanCm / FoliageMeshSpanCm;
        const float CrownBaseZ = TerrainZ + TrunkHeightCm * (Spec.bDesertCanyon ? 0.22f : 0.46f);
        const float CrownRadiusCm = Spec.bDesertCanyon ? 72.0f : (bRainforest ? 165.0f : 126.0f);
        for (int32 BranchIndex = 0; BranchIndex < BranchesPerCluster; ++BranchIndex)
        {
            const float BranchPhase = Phase + static_cast<float>(BranchIndex) * 2.3999632f;
            const float RadialT = BranchIndex == 0
                ? 0.0f
                : 0.45f + 0.12f * static_cast<float>(BranchIndex % 4);
            const FVector BranchLocation(
                BestX + FMath::Cos(BranchPhase) * CrownRadiusCm * RadialT,
                BestY + FMath::Sin(BranchPhase) * CrownRadiusCm * RadialT,
                CrownBaseZ +
                    (Spec.bDesertCanyon ? 32.0f : (bRainforest ? 78.0f : 55.0f)) *
                        FMath::Sin(BranchPhase * 0.83f) +
                    static_cast<float>(BranchIndex % 3) * (Spec.bDesertCanyon ? 18.0f : 34.0f));
            FoliageInstances->AddInstance(
                FTransform(
                    FRotator(
                        -18.0f + 8.0f * static_cast<float>(BranchIndex % 5),
                        FMath::RadiansToDegrees(BranchPhase),
                        11.0f * FMath::Sin(BranchPhase * 0.61f)),
                    BranchLocation,
                    FVector(
                        BranchScale * (0.88f + 0.06f * static_cast<float>(BranchIndex % 4)),
                        BranchScale * (0.82f + 0.07f * static_cast<float>((BranchIndex + 2) % 4)),
                        BranchScale)),
                true);
            ++OutResult.DressingFoliageInstanceCount;
        }

        const float BroadleafSpanCm = FMath::Max(
            1.0f,
            BroadleafMeshA->GetBoundingBox().GetSize().GetMax());
        const float UnderstoryTargetSpanCm = Spec.bDesertCanyon
            ? 54.0f + 8.0f * static_cast<float>(ClusterIndex % 4)
            : (bRainforest ? 92.0f + 14.0f * static_cast<float>(ClusterIndex % 5)
                           : 72.0f + 10.0f * static_cast<float>(ClusterIndex % 4));
        const float UnderstoryScale = UnderstoryTargetSpanCm / BroadleafSpanCm;
        for (int32 UnderstoryIndex = 0; UnderstoryIndex < UnderstoryBranchesPerCluster; ++UnderstoryIndex)
        {
            const float UnderstoryPhase =
                Phase * 0.83f + static_cast<float>(UnderstoryIndex) * 2.3999632f;
            const float UnderstoryRadiusCm = Spec.bDesertCanyon ? 76.0f : (bRainforest ? 150.0f : 112.0f);
            BroadleafInstancesA->AddInstance(
                FTransform(
                    FRotator(
                        -24.0f + 9.0f * static_cast<float>(UnderstoryIndex % 5),
                        FMath::RadiansToDegrees(UnderstoryPhase),
                        14.0f * FMath::Sin(UnderstoryPhase)),
                    FVector(
                        BestX + FMath::Cos(UnderstoryPhase) * UnderstoryRadiusCm,
                        BestY + FMath::Sin(UnderstoryPhase) * UnderstoryRadiusCm,
                        TerrainZ +
                            (Spec.bDesertCanyon ? 28.0f : (bRainforest ? 68.0f : 48.0f)) +
                            14.0f * static_cast<float>(UnderstoryIndex % 3)),
                    FVector(
                        UnderstoryScale * (0.82f + 0.06f * static_cast<float>(UnderstoryIndex % 4)),
                        UnderstoryScale * (0.78f + 0.05f * static_cast<float>((UnderstoryIndex + 1) % 4)),
                        UnderstoryScale)),
                true);
            ++OutResult.DressingFoliageInstanceCount;
        }
    }

    OutResult.bDressingValidated =
        OutResult.DressingBoulderInstanceCount == BoulderCount &&
        OutResult.DressingFoliageInstanceCount ==
            FoliageClusterCount * (BranchesPerCluster + UnderstoryBranchesPerCluster) &&
        OutResult.DressingTrunkInstanceCount > 0 &&
        OutResult.bDressingFoliageMaterialsValidated;
    OutSummary += FString::Printf(
        TEXT("Landscape biome dressing for %s: %d dense irregular procedural boulders, %d PVE twig instances, %d bark-material trunks, %d/3 river-specific foliage slots; Nanite mesh flags boulder=%d broadleaf=%d conifer=%d.\n"),
        *Spec.RiverId,
        OutResult.DressingBoulderInstanceCount,
        OutResult.DressingFoliageInstanceCount,
        OutResult.DressingTrunkInstanceCount,
        OutResult.DressingFoliageMaterialBoundSlotCount,
        OutResult.bDressingBoulderMeshNaniteEnabled,
        OutResult.bDressingBroadleafMeshNaniteEnabled,
        OutResult.bDressingConiferMeshNaniteEnabled);
    return OutResult.bDressingValidated;
}

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
    constexpr int32 LandscapeSize = 1009;
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

bool BuildLandscapeImportCandidateMap(
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    FRaftSimLandscapeImportCandidateResult& OutResult,
    FString& OutSummary)
{
    constexpr int32 LandscapeSize = 1009;
    constexpr int32 LandscapeQuads = LandscapeSize - 1;
    constexpr int32 NumSubsections = 1;
    constexpr int32 SubsectionSizeQuads = 63;
    constexpr float MinX = -5800.0f;

    const FString HeightfieldAbsolutePath = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(GetRepoRoot(), Candidate.HeightfieldRelativePath));
    if (!FPaths::FileExists(HeightfieldAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing Landscape heightfield: %s\n"), *HeightfieldAbsolutePath);
        return false;
    }

    ILandscapeEditorModule& LandscapeEditorModule =
        FModuleManager::LoadModuleChecked<ILandscapeEditorModule>(TEXT("LandscapeEditor"));
    const ILandscapeHeightmapFileFormat* HeightmapFormat =
        LandscapeEditorModule.GetHeightmapFormatByExtension(TEXT(".png"));
    if (!HeightmapFormat)
    {
        OutSummary += TEXT("Unreal LandscapeEditor did not register a PNG heightmap importer.\n");
        return false;
    }

    const FLandscapeHeightmapInfo HeightmapInfo = HeightmapFormat->Validate(*HeightfieldAbsolutePath);
    if (HeightmapInfo.ResultCode == ELandscapeImportResult::Error)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape heightfield validation failed for %s: %s\n"),
            *Candidate.PreviewSpec.RiverId,
            *HeightmapInfo.ErrorMessage.ToString());
        return false;
    }

    const FLandscapeFileResolution ExpectedResolution(LandscapeSize, LandscapeSize);
    if (!HeightmapInfo.PossibleResolutions.Contains(ExpectedResolution))
    {
        OutSummary += FString::Printf(
            TEXT("Landscape heightfield %s does not advertise the required 1009x1009 resolution.\n"),
            *Candidate.HeightfieldRelativePath);
        return false;
    }

    FLandscapeHeightmapImportData ImportedHeightmap =
        HeightmapFormat->Import(*HeightfieldAbsolutePath, ExpectedResolution);
    if (ImportedHeightmap.ResultCode == ELandscapeImportResult::Error ||
        ImportedHeightmap.Data.Num() != LandscapeSize * LandscapeSize)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape heightfield import failed for %s: %s (%d samples).\n"),
            *Candidate.PreviewSpec.RiverId,
            *ImportedHeightmap.ErrorMessage.ToString(),
            ImportedHeightmap.Data.Num());
        return false;
    }

    OutResult.SourceHeightMin = MAX_uint16;
    OutResult.SourceHeightMax = 0;
    for (uint16 Height : ImportedHeightmap.Data)
    {
        OutResult.SourceHeightMin = FMath::Min(OutResult.SourceHeightMin, Height);
        OutResult.SourceHeightMax = FMath::Max(OutResult.SourceHeightMax, Height);
    }
    const int32 SourceRange = static_cast<int32>(OutResult.SourceHeightMax) -
        static_cast<int32>(OutResult.SourceHeightMin);
    OutResult.ChannelFloor = static_cast<uint16>(FMath::Clamp(
        static_cast<int32>(OutResult.SourceHeightMin) + FMath::RoundToInt(static_cast<float>(SourceRange) * 0.12f),
        0,
        65535));
    ApplyPreviewOnlyLandscapeChannelBurn(
        Candidate,
        OutResult.ChannelFloor,
        ImportedHeightmap.Data,
        OutResult.ChannelModifiedSampleCount);

    UWorld* World = UEditorLoadingAndSavingUtils::NewBlankMap(false);
    if (!World)
    {
        OutSummary += FString::Printf(TEXT("Failed to create Landscape candidate map for %s.\n"), *Candidate.PreviewSpec.RiverId);
        return false;
    }

    UMaterialInterface* LandscapeMaterial = LoadOrCreateLandscapeCandidateMaterial(Candidate, OutSummary);
    if (!LandscapeMaterial)
    {
        return false;
    }
    UMaterialInterface* CandidateWaterMaterial =
        LoadOrCreateLandscapeCandidateWaterMaterial(Candidate.PreviewSpec, OutSummary);
    if (!CandidateWaterMaterial)
    {
        return false;
    }
    const FRaftSimLandscapeCandidateWaterSettings CandidateWaterSettings =
        GetLandscapeCandidateWaterSettings(Candidate.PreviewSpec.RiverId);
    FRaftSimPreviewImage SolverVisualizationFields;
    const FRaftSimPreviewImage* SolverVisualizationFieldsPtr = nullptr;
    UMaterialInterface* SolverFoamMaterial = nullptr;
    if (CandidateWaterSettings.SolverFieldEnable > 0.5f)
    {
        const FString SolverFieldImage =
            TEXT("unreal/Content/RaftSim/Rendering/SolverVisualizationFields/"
                 "american_south_fork_median_cpp_solver_depth_speed_froude_v1.png");
        if (!LoadPreviewPngImage(SolverFieldImage, SolverVisualizationFields))
        {
            OutSummary += FString::Printf(
                TEXT("Failed to load solver render-geometry fields for %s.\n"),
                *Candidate.PreviewSpec.RiverId);
            return false;
        }
        SolverVisualizationFieldsPtr = &SolverVisualizationFields;
        SolverFoamMaterial = LoadOrCreateLandscapeCandidateSolverFoamMaterial(OutSummary);
        if (!SolverFoamMaterial)
        {
            return false;
        }
    }
    const float ScaleX = Candidate.HorizontalSpanXCm / static_cast<float>(LandscapeQuads);
    const float ScaleY = Candidate.HorizontalSpanYCm / static_cast<float>(LandscapeQuads);
    const float ScaleZ = Candidate.TargetReliefCm / 512.0f;
    const float EncodedChannelFloorCm =
        (static_cast<float>(OutResult.ChannelFloor) - 32768.0f) / 128.0f * ScaleZ;
    const float ChannelBedWorldZ = Candidate.PreviewSpec.FlowWaterLevelOffsetCm - 24.0f;
    OutResult.LandscapeLocation = FVector(
        MinX,
        -Candidate.HorizontalSpanYCm * 0.5f,
        ChannelBedWorldZ - EncodedChannelFloorCm);
    OutResult.LandscapeScale = FVector(ScaleX, ScaleY, ScaleZ);

    ALandscape* Landscape = World->SpawnActor<ALandscape>(
        OutResult.LandscapeLocation,
        FRotator::ZeroRotator);
    if (!Landscape)
    {
        OutSummary += FString::Printf(TEXT("Failed to spawn ALandscape for %s.\n"), *Candidate.PreviewSpec.RiverId);
        return false;
    }

    Landscape->SetActorScale3D(OutResult.LandscapeScale);
    Landscape->LandscapeMaterial = LandscapeMaterial;
    if (FBoolProperty* EnableNaniteProperty =
            FindFProperty<FBoolProperty>(ALandscapeProxy::StaticClass(), TEXT("bEnableNanite")))
    {
        EnableNaniteProperty->SetPropertyValue_InContainer(Landscape, true);
    }
    else
    {
        OutSummary += TEXT("Unable to find the reflected Landscape Nanite setting.\n");
        return false;
    }
    Landscape->StaticLightingLOD = 0;
    Landscape->SetActorLabel(FString::Printf(
        TEXT("RaftSim_SourceLandscapeCandidate_%s"),
        *Candidate.PreviewSpec.RiverId));

    TMap<FGuid, TArray<uint16>> HeightDataPerLayers;
    HeightDataPerLayers.Add(FGuid(), MoveTemp(ImportedHeightmap.Data));
    TMap<FGuid, TArray<FLandscapeImportLayerInfo>> MaterialLayerDataPerLayers;
    MaterialLayerDataPerLayers.Add(FGuid(), TArray<FLandscapeImportLayerInfo>());
    Landscape->Import(
        FGuid::NewGuid(),
        0,
        0,
        LandscapeQuads,
        LandscapeQuads,
        NumSubsections,
        SubsectionSizeQuads,
        HeightDataPerLayers,
        *HeightfieldAbsolutePath,
        MaterialLayerDataPerLayers,
        ELandscapeImportAlphamapType::Additive,
        TArrayView<const FLandscapeLayer>());
    Landscape->LandscapeMaterial = LandscapeMaterial;
    for (ULandscapeComponent* LandscapeComponent : Landscape->LandscapeComponents)
    {
        if (LandscapeComponent)
        {
            LandscapeComponent->OverrideMaterial = LandscapeMaterial;
            LandscapeComponent->MarkRenderStateDirty();
        }
    }
    Landscape->UpdateAllComponentMaterialInstances(true);
    Landscape->RecreateComponentsState();
    Landscape->PostEditChange();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
    }

    OutResult.MaterialBoundComponentCount = 0;
    for (ULandscapeComponent* LandscapeComponent : Landscape->LandscapeComponents)
    {
        if (!LandscapeComponent || LandscapeComponent->GetLandscapeMaterial() != LandscapeMaterial ||
            LandscapeComponent->GetMaterialInstanceCount() < 1)
        {
            continue;
        }

        UMaterialInstance* ComponentMaterial = LandscapeComponent->GetMaterialInstance(0);
        if (ComponentMaterial && ComponentMaterial->IsChildOf(LandscapeMaterial))
        {
            ++OutResult.MaterialBoundComponentCount;
        }
    }
    OutResult.bMaterialBindingsValidated =
        OutResult.MaterialBoundComponentCount == Landscape->LandscapeComponents.Num();
    if (!OutResult.bMaterialBindingsValidated)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape material binding validation failed for %s: %d/%d components use %s.\n"),
            *Candidate.PreviewSpec.RiverId,
            OutResult.MaterialBoundComponentCount,
            Landscape->LandscapeComponents.Num(),
            *LandscapeMaterial->GetPathName());
        return false;
    }
    if (!AddLandscapeCandidateBiomeDressing(World, Landscape, Candidate, OutResult, OutSummary))
    {
        OutSummary += FString::Printf(
            TEXT("Landscape biome dressing validation failed for %s.\n"),
            *Candidate.PreviewSpec.RiverId);
        return false;
    }
    AddPreviewLightRig(World, Candidate.PreviewSpec);
    AActor* WaterActor = AddPreviewRiverRibbonMesh(
        World,
        Candidate.PreviewSpec,
        nullptr,
        nullptr,
        nullptr,
        CandidateWaterMaterial,
        SolverVisualizationFieldsPtr,
        SolverFoamMaterial);
    OutResult.WaterMaterialPath = CandidateWaterMaterial->GetPathName();
    if (WaterActor)
    {
        if (UProceduralMeshComponent* WaterComponent =
                WaterActor->FindComponentByClass<UProceduralMeshComponent>())
        {
            if (WaterComponent->GetMaterial(0) == CandidateWaterMaterial)
            {
                OutResult.WaterMaterialBoundComponentCount = 1;
            }
        }
    }
    OutResult.bSolverSurfaceWaterMaterialBound =
        OutResult.WaterMaterialBoundComponentCount == 1 &&
        CandidateWaterMaterial->GetShadingModels().HasShadingModel(MSM_DefaultLit);
    if (!OutResult.bSolverSurfaceWaterMaterialBound)
    {
        OutSummary += FString::Printf(
            TEXT("Solver-surface water material binding failed for %s.\n"),
            *Candidate.PreviewSpec.RiverId);
        return false;
    }
    AddPreviewCameraAndStart(World, Candidate.PreviewSpec);

    OutSummary += FString::Printf(
        TEXT("Imported %s as a 16x16-component ALandscape candidate; preview channel burn modified %d samples.\n"),
        *Candidate.HeightfieldRelativePath,
        OutResult.ChannelModifiedSampleCount);
    const bool bSaved = SavePreviewWorld(World, Candidate.MapPackagePath, OutSummary);
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
    }
    OutResult.bNaniteRepresentationBuilt = Landscape->IsNaniteMeshUpToDate();
    if (!OutResult.bNaniteRepresentationBuilt)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape Nanite representation is not up to date for %s.\n"),
            *Candidate.PreviewSpec.RiverId);
    }

    OutResult.NaniteComponentCount = Landscape->NaniteComponents.Num();
    for (ULandscapeNaniteComponent* NaniteComponent : Landscape->NaniteComponents)
    {
        UStaticMesh* NaniteMesh = NaniteComponent ? NaniteComponent->GetStaticMesh() : nullptr;
        if (!NaniteMesh)
        {
            continue;
        }

        for (const FStaticMaterial& StaticMaterial : NaniteMesh->GetStaticMaterials())
        {
            ++OutResult.NaniteMaterialSlotCount;
            UMaterialInterface* SlotMaterial = StaticMaterial.MaterialInterface;
            UMaterialInstance* SlotMaterialInstance = Cast<UMaterialInstance>(SlotMaterial);
            if (SlotMaterial == LandscapeMaterial ||
                (SlotMaterialInstance && SlotMaterialInstance->IsChildOf(LandscapeMaterial)))
            {
                ++OutResult.NaniteMaterialBoundSlotCount;
            }
        }

        Nanite::FMaterialAudit MaterialAudit;
        Nanite::AuditMaterials(NaniteComponent, MaterialAudit, false);
        for (const Nanite::FMaterialAuditEntry& Entry : MaterialAudit.Entries)
        {
            if (Entry.bHasAnyError)
            {
                ++OutResult.NaniteMaterialAuditErrorCount;
                OutSummary += FString::Printf(
                    TEXT("Nanite material audit rejected %s slot %d for %s: null=%d blend=%d shading=%d usage=%d.\n"),
                    Entry.Material ? *Entry.Material->GetPathName() : TEXT("<null>"),
                    Entry.MaterialIndex,
                    *Candidate.PreviewSpec.RiverId,
                    Entry.bHasNullMaterial,
                    Entry.bHasUnsupportedBlendMode,
                    Entry.bHasUnsupportedShadingModel,
                    Entry.bHasInvalidUsage);
            }
        }
    }
    OutResult.bNaniteMaterialBindingsValidated =
        OutResult.NaniteComponentCount > 0 &&
        OutResult.NaniteMaterialSlotCount > 0 &&
        OutResult.NaniteMaterialBoundSlotCount == OutResult.NaniteMaterialSlotCount &&
        OutResult.NaniteMaterialAuditErrorCount == 0;
    OutSummary += FString::Printf(
        TEXT("Landscape material audit for %s: %d/%d source components and %d/%d Nanite slots use %s; %d Nanite audit errors.\n"),
        *Candidate.PreviewSpec.RiverId,
        OutResult.MaterialBoundComponentCount,
        Landscape->LandscapeComponents.Num(),
        OutResult.NaniteMaterialBoundSlotCount,
        OutResult.NaniteMaterialSlotCount,
        *LandscapeMaterial->GetPathName(),
        OutResult.NaniteMaterialAuditErrorCount);
    if (!OutResult.bNaniteMaterialBindingsValidated)
    {
        OutSummary += FString::Printf(
            TEXT("Landscape Nanite material binding validation failed for %s across %d Nanite components.\n"),
            *Candidate.PreviewSpec.RiverId,
            OutResult.NaniteComponentCount);
    }
    return bSaved && OutResult.bNaniteRepresentationBuilt && OutResult.bMaterialBindingsValidated &&
        OutResult.bDressingValidated && OutResult.bSolverSurfaceWaterMaterialBound &&
        OutResult.bNaniteMaterialBindingsValidated;
}

bool BuildPreviewMapForSpec(const FRaftSimEnvironmentPreviewSpec& Spec, FString& OutSummary)
{
    UWorld* World = UEditorLoadingAndSavingUtils::NewBlankMap(false);
    if (!World)
    {
        OutSummary += FString::Printf(TEXT("Failed to create blank map for %s\n"), *Spec.RiverId);
        return false;
    }

    UStaticMesh* CubeMesh = LoadPreviewMesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
    UStaticMesh* PlaneMesh = LoadPreviewMesh(TEXT("/Engine/BasicShapes/Plane.Plane"));
    UStaticMesh* SphereMesh = LoadPreviewMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    UStaticMesh* CylinderMesh = LoadPreviewMesh(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    const bool bUseFirstPartyProceduralFoliageOnly = true;
    UStaticMesh* PcgTreeMeshA = bUseFirstPartyProceduralFoliageOnly
        ? nullptr
        : LoadPreviewMesh(TEXT("/PCG/SampleContent/SimpleForest/Meshes/PCG_Tree_01.PCG_Tree_01"));
    UStaticMesh* PcgTreeMeshB = bUseFirstPartyProceduralFoliageOnly
        ? nullptr
        : LoadPreviewMesh(TEXT("/PCG/SampleContent/SimpleForest/Meshes/PCG_Tree_02.PCG_Tree_02"));
    UStaticMesh* PcgTreeMeshC = bUseFirstPartyProceduralFoliageOnly
        ? nullptr
        : LoadPreviewMesh(TEXT("/PCG/SampleContent/SimpleForest/Meshes/PCG_Tree_03.PCG_Tree_03"));
    UStaticMesh* PcgSeedlingMesh = bUseFirstPartyProceduralFoliageOnly
        ? nullptr
        : LoadPreviewMesh(TEXT("/PCG/SampleContent/SimpleForest/Meshes/PCG_Seedling_01.PCG_Seedling_01"));

    FRaftSimPreviewImage AerialDrape;
    const FRaftSimPreviewImage* AerialDrapePtr = nullptr;
    if (!Spec.AerialDrapeImage.IsEmpty() && LoadPreviewPngImage(Spec.AerialDrapeImage, AerialDrape))
    {
        AerialDrapePtr = &AerialDrape;
    }
    FRaftSimPreviewImage TerrainRelief;
    const FRaftSimPreviewImage* TerrainReliefPtr = nullptr;
    if (!Spec.TerrainReliefImage.IsEmpty() && LoadPreviewPngImage(Spec.TerrainReliefImage, TerrainRelief))
    {
        TerrainReliefPtr = &TerrainRelief;
    }
    FRaftSimPreviewImage HeightfieldPreview;
    const FRaftSimPreviewImage* HeightfieldPreviewPtr = nullptr;
    if (!Spec.HeightfieldPreviewImage.IsEmpty() && LoadPreviewPngImage(Spec.HeightfieldPreviewImage, HeightfieldPreview))
    {
        HeightfieldPreviewPtr = &HeightfieldPreview;
    }
    FRaftSimPreviewImage WaterMask;
    const FRaftSimPreviewImage* WaterMaskPtr = nullptr;
    if (!Spec.WaterMaskImage.IsEmpty() && LoadPreviewPngImage(Spec.WaterMaskImage, WaterMask))
    {
        WaterMaskPtr = &WaterMask;
    }
    FRaftSimPreviewImage VegetationMask;
    const FRaftSimPreviewImage* VegetationMaskPtr = nullptr;
    if (!Spec.VegetationMaskImage.IsEmpty() && LoadPreviewPngImage(Spec.VegetationMaskImage, VegetationMask))
    {
        VegetationMaskPtr = &VegetationMask;
    }
    FRaftSimPreviewImage MaterialAtlasAlbedo;
    const FRaftSimPreviewImage* MaterialAtlasAlbedoPtr = nullptr;
    const FString MaterialAtlasAlbedoPath = GetFirstPartyMaterialTextureAtlasAlbedoRelativePath(Spec.RiverId);
    if (LoadPreviewPngImage(MaterialAtlasAlbedoPath, MaterialAtlasAlbedo))
    {
        MaterialAtlasAlbedoPtr = &MaterialAtlasAlbedo;
    }
    FRaftSimPreviewImage MaterialAtlasNormal;
    const FRaftSimPreviewImage* MaterialAtlasNormalPtr = nullptr;
    const FString MaterialAtlasNormalPath = GetFirstPartyMaterialTextureAtlasNormalRelativePath(Spec.RiverId);
    if (LoadPreviewPngImage(MaterialAtlasNormalPath, MaterialAtlasNormal))
    {
        MaterialAtlasNormalPtr = &MaterialAtlasNormal;
    }
    FRaftSimPreviewImage MaterialAtlasPacked;
    const FRaftSimPreviewImage* MaterialAtlasPackedPtr = nullptr;
    const FString MaterialAtlasPackedPath = GetFirstPartyMaterialTextureAtlasPackedRelativePath(Spec.RiverId);
    if (LoadPreviewPngImage(MaterialAtlasPackedPath, MaterialAtlasPacked))
    {
        MaterialAtlasPackedPtr = &MaterialAtlasPacked;
    }
    const FRaftSimFirstPartyMaterialAssignmentSet FirstPartyMaterialAssignments =
        LoadFirstPartyMaterialAssignmentSetForSpec(Spec, OutSummary);

    AddPreviewLightRig(World, Spec);

    AddPreviewTerrainMesh(
        World,
        Spec,
        AerialDrapePtr,
        TerrainReliefPtr,
        HeightfieldPreviewPtr,
        WaterMaskPtr,
        VegetationMaskPtr,
        MaterialAtlasAlbedoPtr,
        MaterialAtlasNormalPtr,
        MaterialAtlasPackedPtr);
    AddPreviewRiverRibbonMesh(World, Spec, MaterialAtlasAlbedoPtr, MaterialAtlasNormalPtr, MaterialAtlasPackedPtr);
    const bool bCreateLegacyTerrainOverlayProxyGeometry = false;
    if (bCreateLegacyTerrainOverlayProxyGeometry)
    {
        AddPreviewAerialDrapeTiles(
            World,
            Spec,
            AerialDrapePtr,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            VegetationMaskPtr);
        AddPreviewWetBankDressing(World, Spec, TerrainReliefPtr, HeightfieldPreviewPtr);
        AddPreviewIrregularShorelineEdgeBreakupDetail(
            World,
            Spec,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            VegetationMaskPtr);
        AddPreviewSourceAwareBankBreakupDetail(
            World,
            Spec,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            VegetationMaskPtr);
        AddPreviewTerrainMaterialLayerDetail(
            World,
            Spec,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            VegetationMaskPtr);
        AddPreviewLandscapeNaniteMaterialScaffoldDetail(
            World,
            Spec,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            VegetationMaskPtr);
        AddPreviewTerrainErosionRillDetail(
            World,
            Spec,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            VegetationMaskPtr);
        AddPreviewSourceMaskedBankBarMicrogeometryDetail(
            World,
            Spec,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            VegetationMaskPtr);
        AddPreviewSourceMaskedShorelineLipOverhangDetail(
            World,
            Spec,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            VegetationMaskPtr);
        AddPreviewProceduralBankTextureCards(
            World,
            Spec,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            VegetationMaskPtr,
            PlaneMesh);
        AddPreviewNearFieldPhotorealReviewDressing(
            World,
            Spec,
            AerialDrapePtr,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            VegetationMaskPtr);
    }
    else
    {
        OutSummary += FString::Printf(
            TEXT("Skipped legacy terrain/bank overlay proxy geometry for %s; the textured terrain mesh is authoritative.\n"),
            *Spec.RiverId);
    }
    AddPreviewProceduralEnvironmentDetail(World, Spec, TerrainReliefPtr, HeightfieldPreviewPtr, WaterMaskPtr, VegetationMaskPtr, SphereMesh);
    AddPreviewBiomeBankEcologyDetail(
        World,
        Spec,
        TerrainReliefPtr,
        HeightfieldPreviewPtr,
        WaterMaskPtr,
        VegetationMaskPtr,
        CubeMesh,
        CylinderMesh,
        PlaneMesh);
    AddPreviewBiomeFoliageSilhouetteDetail(
        World,
        Spec,
        TerrainReliefPtr,
        HeightfieldPreviewPtr,
        WaterMaskPtr,
        VegetationMaskPtr,
        CylinderMesh,
        PlaneMesh);
    AddPreviewDenseBiomeFoliageLayerDetail(
        World,
        Spec,
        TerrainReliefPtr,
        HeightfieldPreviewPtr,
        WaterMaskPtr,
        VegetationMaskPtr,
        CylinderMesh,
        PlaneMesh);
    AddPreviewInstancedProceduralFoliageEquivalentDetail(
        World,
        Spec,
        TerrainReliefPtr,
        HeightfieldPreviewPtr,
        WaterMaskPtr,
        VegetationMaskPtr,
        SphereMesh,
        CylinderMesh);
    AddPreviewFoliageCrownDepthAndLeafletBreakupDetail(
        World,
        Spec,
        TerrainReliefPtr,
        HeightfieldPreviewPtr,
        WaterMaskPtr,
        VegetationMaskPtr);
    const bool bCreateLegacyWaterOverlayProxyGeometry = false;
    if (bCreateLegacyWaterOverlayProxyGeometry)
    {
        AddPreviewWaterSurfaceDetail(World, Spec);
        AddPreviewFlowBandTextureDetail(World, Spec);
        AddPreviewWaterSurfaceChopAndTurbidityDetail(World, Spec);
        AddPreviewWaterShaderDepthReflectionScaffoldDetail(World, Spec);
        AddPreviewShallowWaterClarityAndAerationDetail(World, Spec, WaterMaskPtr, PlaneMesh);
        AddPreviewWaterMicroRippleGlintDetail(World, Spec, PlaneMesh);
        AddPreviewFoamAndHydraulics(World, Spec);
        AddPreviewFlowDependentHydraulicAerationAndSprayDetail(
            World,
            Spec,
            TerrainReliefPtr,
            HeightfieldPreviewPtr,
            WaterMaskPtr,
            PlaneMesh,
            SphereMesh);
    }
    else
    {
        OutSummary += FString::Printf(
            TEXT("Skipped legacy water overlay proxy geometry for %s; integrated base-water relief and color remain active.\n"),
            *Spec.RiverId);
    }
    AddPreviewSurfaceAtmosphereAndSprayDetail(World, Spec, TerrainReliefPtr, HeightfieldPreviewPtr, PlaneMesh);
    AddPreviewWaterfallAndPlungeMistDetail(World, Spec, TerrainReliefPtr, HeightfieldPreviewPtr, PlaneMesh, CubeMesh);
    AddPreviewRiverAtmosphericBackdropDetail(World, Spec, TerrainReliefPtr, HeightfieldPreviewPtr, PlaneMesh);
    AddPreviewSourceAwareSkyGradientLayer(World, Spec, TerrainReliefPtr, HeightfieldPreviewPtr, PlaneMesh);

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    for (int32 BoulderIndex = 0; BoulderIndex < Spec.BoulderCount; ++BoulderIndex)
    {
        const float Side = (BoulderIndex % 2 == 0) ? -1.0f : 1.0f;
        const float BaseX = -3600.0f + static_cast<float>(BoulderIndex) * (28200.0f / FMath::Max(1, Spec.BoulderCount));
        const float BaseOffset = ActiveRiverHalfWidth * (0.32f + 0.55f * FMath::Abs(FMath::Sin(static_cast<float>(BoulderIndex) * 1.91f)));
        float X = BaseX;
        float Y = GetPreviewRiverCenterY(Spec, X) + Side * BaseOffset;
        float BestBoulderScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 5; ++CandidateIndex)
        {
            const float CandidateX = BaseX + 145.0f * FMath::Sin(static_cast<float>(BoulderIndex) * 0.67f + static_cast<float>(CandidateIndex) * 1.21f);
            const float CandidateOffset = BaseOffset + Side * 125.0f * (static_cast<float>(CandidateIndex) - 2.0f);
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMaskPtr, CandidateX, CandidateY);
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMaskPtr, CandidateX, CandidateY);
            const float Score = WaterT * 1.15f - VegetationT * 0.70f +
                0.05f * FMath::Sin(static_cast<float>(BoulderIndex) * 0.97f + static_cast<float>(CandidateIndex));
            if (Score > BestBoulderScore)
            {
                BestBoulderScore = Score;
                X = CandidateX;
                Y = CandidateY;
            }
        }
        float BoulderCenterY = GetPreviewRiverCenterY(Spec, X);
        float BoulderLateralOffset = Y - BoulderCenterY;
        const bool bNearCameraReviewBoulder = X < 3600.0f;
        if (bNearCameraReviewBoulder && FMath::Abs(BoulderLateralOffset) < ActiveRiverHalfWidth * 0.78f)
        {
            const float ReviewClearanceSide = (BoulderIndex % 2 == 0) ? -1.0f : 1.0f;
            X += Spec.bDesertCanyon ? 1420.0f : 1160.0f;
            BoulderCenterY = GetPreviewRiverCenterY(Spec, X);
            BoulderLateralOffset =
                ReviewClearanceSide * ActiveRiverHalfWidth * (Spec.bDesertCanyon ? 0.96f : 0.88f);
            Y = BoulderCenterY + BoulderLateralOffset;
        }

        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainReliefPtr, HeightfieldPreviewPtr);
        const float BaseScale = Spec.bDesertCanyon ? 1.6f : 1.0f + 0.35f * static_cast<float>(BoulderIndex % 3);
        const float Scale = BaseScale * (bNearCameraReviewBoulder ? (Spec.bDesertCanyon ? 0.50f : 0.44f) : 1.0f);
        const float BoulderWaterT = SamplePreviewMaskAtWorld(Spec, WaterMaskPtr, X, Y);
        const float BoulderVegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMaskPtr, X, Y);
        const FLinearColor BoulderBaseColor = ScalePreviewColor(Spec.RockColor, Spec.bDesertCanyon ? 0.90f : 0.78f);
        FLinearColor UnadjustedBoulderColor = FMath::Lerp(
            BoulderBaseColor,
            FMath::Lerp(ScalePreviewColor(Spec.RockColor, 0.46f), ScalePreviewColor(Spec.WaterColor, 0.34f), 0.30f),
            FMath::Clamp(BoulderWaterT * 0.36f, 0.0f, 0.42f));
        UnadjustedBoulderColor = ApplyFirstPartyMaterialAtlasTint(
            Spec,
            MaterialAtlasAlbedoPtr,
            WetBoulderContactMaterialTile,
            UnadjustedBoulderColor,
            X * 0.0021f + static_cast<float>(BoulderIndex) * 0.137f,
            Y * 0.0033f + BoulderWaterT * 0.29f + BoulderVegetationT * 0.41f,
            FMath::Clamp(0.14f + BoulderWaterT * 0.08f + BoulderVegetationT * 0.03f, 0.0f, 0.24f));
        UnadjustedBoulderColor = ApplyFirstPartyMaterialAtlasSurfaceResponse(
            Spec,
            MaterialAtlasNormalPtr,
            MaterialAtlasPackedPtr,
            WetBoulderContactMaterialTile,
            UnadjustedBoulderColor,
            X * 0.0021f + static_cast<float>(BoulderIndex) * 0.137f,
            Y * 0.0033f + BoulderWaterT * 0.29f + BoulderVegetationT * 0.41f,
            FMath::Clamp(0.14f + BoulderWaterT * 0.08f + BoulderVegetationT * 0.03f, 0.0f, 0.24f));
        const FLinearColor BoulderColor =
            bNearCameraReviewBoulder ? ScalePreviewColor(UnadjustedBoulderColor, Spec.bDesertCanyon ? 0.56f : 0.48f) : UnadjustedBoulderColor;
        const FVector BoulderScale(Scale * 1.18f, Scale * 0.92f, Scale * 0.54f);
        const FVector BoulderLocation(X, Y, FMath::Max(20.0f, TerrainZ + 18.0f + 8.0f * static_cast<float>(BoulderIndex % 4)));
        AddPreviewIrregularRockActor(
            World,
            FString::Printf(TEXT("RaftSim_SourceAwareBoulder_%02d_%s"), BoulderIndex, *Spec.RiverId),
            BoulderLocation,
            static_cast<float>(BoulderIndex * 31),
            BoulderScale,
            BoulderColor,
            BoulderIndex + 3900);
        AddPreviewBoulderSurfaceVariationDetail(
            World,
            Spec,
            BoulderLocation,
            static_cast<float>(BoulderIndex * 31),
            BoulderScale,
            BoulderIndex,
            BoulderWaterT,
            BoulderVegetationT,
            bNearCameraReviewBoulder);
        const float ContactFoamStrength =
            FMath::Clamp(0.45f + BoulderWaterT * 0.55f + Spec.FlowFoamScale * 0.20f, 0.0f, 1.0f);
        if (ContactFoamStrength > 0.52f)
        {
            const float ContactLength = (Spec.bDesertCanyon ? 420.0f : 330.0f) * FMath::Max(0.55f, Spec.FlowFoamScale);
            const float ContactWidth = (Spec.bDesertCanyon ? 26.0f : 34.0f) * ContactFoamStrength;
            AddPreviewFoamRibbon(
                World,
                Spec,
                FString::Printf(TEXT("RaftSim_BoulderContactFoam_%02d_%s"), BoulderIndex, *Spec.RiverId),
                X - ContactLength * 0.34f,
                ContactLength,
                BoulderLateralOffset,
                ContactWidth,
                static_cast<float>(BoulderIndex) * 0.59f,
                Spec.bDesertCanyon ? FLinearColor(0.78f, 0.78f, 0.68f) : FLinearColor(0.86f, 0.94f, 0.88f));
        }
    }

    const float RemainingBlockyFoliageProxyCull =
        Spec.bDesertCanyon ? 0.46f : (Spec.bHasWaterfalls ? 0.38f : 0.42f);
    const int32 VisibleFoliageCount =
        FMath::Max(1, FMath::RoundToInt(static_cast<float>(Spec.FoliageCount) * RemainingBlockyFoliageProxyCull));
    for (int32 FoliageIndex = 0; FoliageIndex < VisibleFoliageCount; ++FoliageIndex)
    {
        const float Side = (FoliageIndex % 2 == 0) ? -1.0f : 1.0f;
        const float BankOffset = Spec.bDesertCanyon ? ActiveRiverHalfWidth + 1350.0f : ActiveRiverHalfWidth + 620.0f;
        const float FoliageT = static_cast<float>(FoliageIndex) / static_cast<float>(FMath::Max(1, VisibleFoliageCount - 1));
        const float BaseX = FMath::Lerp(850.0f, 25800.0f, FoliageT);
        float X = BaseX;
        float Y = GetPreviewRiverCenterY(Spec, X) + Side * (BankOffset + 210.0f * FMath::Sin(static_cast<float>(FoliageIndex) * 1.31f));
        float BestFoliageScore = -1000.0f;
        for (int32 CandidateIndex = 0; CandidateIndex < 5; ++CandidateIndex)
        {
            const float CandidateX = BaseX + 210.0f * FMath::Sin(static_cast<float>(FoliageIndex) * 0.49f + static_cast<float>(CandidateIndex) * 1.51f);
            const float CandidateOffset = BankOffset +
                300.0f * FMath::Sin(static_cast<float>(FoliageIndex) * 0.83f + static_cast<float>(CandidateIndex) * 0.91f);
            const float CandidateY = GetPreviewRiverCenterY(Spec, CandidateX) + Side * CandidateOffset;
            const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMaskPtr, CandidateX, CandidateY);
            const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMaskPtr, CandidateX, CandidateY);
            const float Score = VegetationT * (Spec.bDesertCanyon ? 0.65f : 1.45f) - WaterT * 1.10f +
                0.05f * FMath::Sin(static_cast<float>(FoliageIndex) * 1.17f + static_cast<float>(CandidateIndex));
            if (Score > BestFoliageScore)
            {
                BestFoliageScore = Score;
                X = CandidateX;
                Y = CandidateY;
            }
        }
        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainReliefPtr, HeightfieldPreviewPtr);
        const float Height = Spec.bHasWaterfalls ? 2.35f + 0.28f * static_cast<float>(FoliageIndex % 5) : (Spec.bDesertCanyon ? 0.50f : 1.45f + 0.18f * static_cast<float>(FoliageIndex % 3));
        const float CanopyWidth = Spec.bHasWaterfalls ? 1.35f + 0.18f * static_cast<float>(FoliageIndex % 4) : (Spec.bDesertCanyon ? 0.55f : 0.92f + 0.10f * static_cast<float>(FoliageIndex % 3));
        const float FirstPartyProceduralCanopyHeightCm = Spec.bDesertCanyon
            ? 92.0f + 10.0f * static_cast<float>(FoliageIndex % 3)
            : (Spec.bHasWaterfalls ? 405.0f + 34.0f * static_cast<float>(FoliageIndex % 5)
                                    : 278.0f + 22.0f * static_cast<float>(FoliageIndex % 4));
        const float FirstPartyProceduralTrunkHeightCm = Spec.bDesertCanyon
            ? 78.0f + 8.0f * static_cast<float>(FoliageIndex % 3)
            : (Spec.bHasWaterfalls ? 330.0f + 28.0f * static_cast<float>(FoliageIndex % 5)
                                    : 218.0f + 18.0f * static_cast<float>(FoliageIndex % 4));
        const float FirstPartyProceduralCanopyBlobDemotion =
            Spec.bDesertCanyon ? 0.64f : (Spec.bHasWaterfalls ? 0.46f : 0.52f);
        const float FoliageCardSilhouetteDemotion =
            Spec.bDesertCanyon ? 0.48f : (Spec.bHasWaterfalls ? 0.34f : 0.40f);
        const float FirstPartyProceduralCanopyWidthScale =
            (Spec.bDesertCanyon ? 1.0f : (Spec.bHasWaterfalls ? 1.22f : 1.16f)) * FirstPartyProceduralCanopyBlobDemotion;
        const float FirstPartyProceduralCanopyVerticalScale =
            (Spec.bDesertCanyon ? 1.0f : (Spec.bHasWaterfalls ? 1.26f : 1.18f)) * (Spec.bHasWaterfalls ? 0.82f : 0.88f);
        const float FirstPartyProceduralCrownZ = TerrainZ + FirstPartyProceduralCanopyHeightCm;
        const float FirstPartyProceduralTrunkCenterZ = TerrainZ + FirstPartyProceduralTrunkHeightCm * 0.50f;
        const float FoliageMaskT = SamplePreviewMaskAtWorld(Spec, VegetationMaskPtr, X, Y);
        const FLinearColor CanopyColor = Spec.bDesertCanyon
            ? FLinearColor(0.22f, 0.28f, 0.13f)
            : FLinearColor(
                  FMath::Clamp(Spec.FoliageColor.R + 0.025f * static_cast<float>(FoliageIndex % 3), 0.0f, 1.0f),
                  FMath::Clamp(Spec.FoliageColor.G + 0.035f * static_cast<float>((FoliageIndex + 1) % 4) + FoliageMaskT * 0.035f, 0.0f, 1.0f),
                  FMath::Clamp(Spec.FoliageColor.B + 0.025f * static_cast<float>((FoliageIndex + 2) % 3), 0.0f, 1.0f));
        const FLinearColor FirstPartyProceduralCanopyToneAnchor = Spec.bDesertCanyon
            ? FLinearColor(0.18f, 0.21f, 0.105f)
            : (Spec.bHasWaterfalls ? FLinearColor(0.020f, 0.120f, 0.038f)
                                    : FLinearColor(0.085f, 0.175f, 0.055f));
        const float FirstPartyProceduralCanopyToneCompression =
            Spec.bDesertCanyon ? 0.20f : (Spec.bHasWaterfalls ? 0.54f : 0.42f);
        FLinearColor FirstPartyProceduralCanopyToneColor = ScalePreviewColor(
            FMath::Lerp(CanopyColor, FirstPartyProceduralCanopyToneAnchor, FirstPartyProceduralCanopyToneCompression),
            Spec.bDesertCanyon ? 0.94f : (Spec.bHasWaterfalls ? 0.80f : 0.84f));
        FirstPartyProceduralCanopyToneColor = ApplyFirstPartyMaterialAtlasTint(
            Spec,
            MaterialAtlasAlbedoPtr,
            BiomeFoliageGroundcoverMaterialTile,
            FirstPartyProceduralCanopyToneColor,
            X * 0.0017f + static_cast<float>(FoliageIndex) * 0.071f,
            Y * 0.0024f + FoliageMaskT * 0.36f,
            Spec.bDesertCanyon ? 0.10f : (Spec.bHasWaterfalls ? 0.18f : 0.15f));
        FirstPartyProceduralCanopyToneColor = ApplyFirstPartyMaterialAtlasSurfaceResponse(
            Spec,
            MaterialAtlasNormalPtr,
            MaterialAtlasPackedPtr,
            BiomeFoliageGroundcoverMaterialTile,
            FirstPartyProceduralCanopyToneColor,
            X * 0.0017f + static_cast<float>(FoliageIndex) * 0.071f,
            Y * 0.0024f + FoliageMaskT * 0.36f,
            Spec.bDesertCanyon ? 0.10f : (Spec.bHasWaterfalls ? 0.18f : 0.15f));
        const FLinearColor FirstPartyProceduralCanopyShadowColor = Spec.bDesertCanyon
            ? ScalePreviewColor(FirstPartyProceduralCanopyToneColor, 0.62f)
            : FMath::Lerp(
                  FirstPartyProceduralCanopyToneColor,
                  Spec.bHasWaterfalls ? FLinearColor(0.006f, 0.032f, 0.014f) : FLinearColor(0.030f, 0.060f, 0.024f),
                  Spec.bHasWaterfalls ? 0.46f : 0.34f);
        UStaticMesh* PcgFoliageMesh = nullptr;
        if (Spec.bDesertCanyon)
        {
            PcgFoliageMesh = PcgSeedlingMesh;
        }
        else if (FoliageIndex % 3 == 0)
        {
            PcgFoliageMesh = PcgTreeMeshA;
        }
        else if (FoliageIndex % 3 == 1)
        {
            PcgFoliageMesh = PcgTreeMeshB ? PcgTreeMeshB : PcgTreeMeshA;
        }
        else
        {
            PcgFoliageMesh = PcgTreeMeshC ? PcgTreeMeshC : PcgTreeMeshA;
        }

        if (PcgFoliageMesh)
        {
            const float BaseScale = Spec.bHasWaterfalls
                ? 0.30f + 0.035f * static_cast<float>(FoliageIndex % 4)
                : (Spec.bDesertCanyon ? 0.30f + 0.035f * static_cast<float>(FoliageIndex % 3) : 0.27f + 0.03f * static_cast<float>(FoliageIndex % 3));
            AddPreviewMeshActor(
                World,
                PcgFoliageMesh,
                FString::Printf(TEXT("RaftSim_SourceAwareFoliage_%02d_%s"), FoliageIndex, *Spec.RiverId),
                FVector(X, Y, TerrainZ),
                FRotator(0.0f, static_cast<float>((FoliageIndex * 43) % 360), 0.0f),
                FVector(BaseScale, BaseScale, BaseScale * (Spec.bHasWaterfalls ? 1.22f : 1.0f)),
                FirstPartyProceduralCanopyToneColor);

            const int32 SupplementalLeafLobes = Spec.bDesertCanyon ? 1 : (Spec.bHasWaterfalls ? 3 : 2);
            const float CrownZ = TerrainZ + (Spec.bHasWaterfalls ? 305.0f : (Spec.bDesertCanyon ? 82.0f : 205.0f));
            for (int32 LobeIndex = 0; LobeIndex < SupplementalLeafLobes; ++LobeIndex)
            {
                const float AngleRadians = FMath::DegreesToRadians(static_cast<float>((FoliageIndex * 61 + LobeIndex * 127) % 360));
                const float Radius = Spec.bDesertCanyon ? 24.0f : (Spec.bHasWaterfalls ? 84.0f : 58.0f);
                const FVector ClusterLocation(
                    X + FMath::Cos(AngleRadians) * Radius,
                    Y + FMath::Sin(AngleRadians) * Radius,
                    CrownZ + 24.0f * FMath::Sin(static_cast<float>(LobeIndex) * 1.17f));
                const FVector ClusterScale = Spec.bDesertCanyon
                    ? FVector(0.20f, 0.15f, 0.090f)
                    : (Spec.bHasWaterfalls ? FVector(0.70f, 0.52f, 0.34f) : FVector(0.44f, 0.34f, 0.22f));
                AddPreviewProceduralLeafClusterActor(
                    World,
                    FString::Printf(TEXT("RaftSim_ProceduralLeafClusterSupplement_%02d_%02d_%s"), FoliageIndex, LobeIndex, *Spec.RiverId),
                    ClusterLocation,
                    static_cast<float>((FoliageIndex * 43 + LobeIndex * 31) % 360),
                    ClusterScale,
                    ScalePreviewColor(FirstPartyProceduralCanopyToneColor, 0.86f + 0.035f * static_cast<float>(LobeIndex)),
                    FoliageIndex * 19 + LobeIndex + 6100,
                    Spec.bHasWaterfalls);
            }
        }
        else
        {
            AddPreviewMeshActor(
                World,
                CylinderMesh,
                FString::Printf(TEXT("RaftSim_FoliageTrunk_%02d_%s"), FoliageIndex, *Spec.RiverId),
                FVector(X, Y, FirstPartyProceduralTrunkCenterZ),
                FRotator::ZeroRotator,
                FVector(
                    Spec.bDesertCanyon ? 0.11f : (Spec.bHasWaterfalls ? 0.16f : 0.145f),
                    Spec.bDesertCanyon ? 0.11f : (Spec.bHasWaterfalls ? 0.16f : 0.145f),
                    FirstPartyProceduralTrunkHeightCm * 0.010f),
                Spec.bDesertCanyon ? FLinearColor(0.21f, 0.18f, 0.10f) : FLinearColor(0.20f, 0.12f, 0.07f));

            const int32 CanopyLobes = Spec.bHasWaterfalls ? 3 : (Spec.bDesertCanyon ? 2 : 2);
            for (int32 LobeIndex = 0; LobeIndex < CanopyLobes; ++LobeIndex)
            {
                const float AngleRadians = FMath::DegreesToRadians(static_cast<float>((FoliageIndex * 47 + LobeIndex * 83) % 360));
                const float Radius = ((LobeIndex == 0) ? 0.0f : (Spec.bHasWaterfalls ? 112.0f : 76.0f)) * FirstPartyProceduralCanopyBlobDemotion;
                const float LobeX = X + FMath::Cos(AngleRadians) * Radius;
                const float LobeY = Y + FMath::Sin(AngleRadians) * Radius;
                AddPreviewProceduralLeafClusterActor(
                    World,
                    FString::Printf(TEXT("RaftSim_FoliageCanopy_%02d_%02d_%s"), FoliageIndex, LobeIndex, *Spec.RiverId),
                    FVector(LobeX, LobeY, FirstPartyProceduralCrownZ + 26.0f * static_cast<float>(LobeIndex % 3)),
                    static_cast<float>((FoliageIndex * 47 + LobeIndex * 19) % 360),
                    FVector(
                        CanopyWidth * FirstPartyProceduralCanopyWidthScale * (1.08f - 0.08f * static_cast<float>(LobeIndex % 2)),
                        CanopyWidth * FirstPartyProceduralCanopyWidthScale * (0.82f + 0.07f * static_cast<float>(LobeIndex % 3)),
                        Height * FirstPartyProceduralCanopyVerticalScale * (Spec.bHasWaterfalls ? 0.36f : 0.30f)),
                    LobeIndex == 0 ? FirstPartyProceduralCanopyShadowColor : FirstPartyProceduralCanopyToneColor,
                    FoliageIndex * 23 + LobeIndex + 6700,
                    Spec.bHasWaterfalls);
            }
        }

        const int32 OrganicLeafSprayCount = Spec.bDesertCanyon ? 1 : (Spec.bHasWaterfalls ? 3 : 2);
        for (int32 SprayIndex = 0; SprayIndex < OrganicLeafSprayCount; ++SprayIndex)
        {
            const float SprayAngleRadians =
                FMath::DegreesToRadians(static_cast<float>((FoliageIndex * 71 + SprayIndex * 113) % 360));
            const float SprayRadius = (Spec.bDesertCanyon ? 46.0f : (Spec.bHasWaterfalls ? 132.0f : 88.0f)) * FirstPartyProceduralCanopyBlobDemotion;
            const FVector SprayLocation(
                X + FMath::Cos(SprayAngleRadians) * SprayRadius,
                Y + FMath::Sin(SprayAngleRadians) * SprayRadius,
                FirstPartyProceduralCrownZ + (Spec.bHasWaterfalls ? 42.0f : 22.0f) * static_cast<float>(SprayIndex));
            const FVector SprayScale = Spec.bDesertCanyon
                ? FVector(0.28f, 0.20f, 0.090f)
                : (Spec.bHasWaterfalls ? FVector(1.18f, 0.84f, 0.54f) * FoliageCardSilhouetteDemotion : FVector(0.76f, 0.54f, 0.32f) * FoliageCardSilhouetteDemotion);
            AddPreviewOrganicLeafSprayActor(
                World,
                FString::Printf(TEXT("RaftSim_OrganicCanopyLeafSpray_%02d_%02d_%s"), FoliageIndex, SprayIndex, *Spec.RiverId),
                SprayLocation,
                static_cast<float>((FoliageIndex * 59 + SprayIndex * 37) % 360),
                SprayScale,
                ScalePreviewColor(FirstPartyProceduralCanopyToneColor, 0.70f + 0.045f * static_cast<float>(SprayIndex % 4)),
                FoliageIndex * 41 + SprayIndex + 8300,
                Spec.bHasWaterfalls);
        }

        if (!Spec.bDesertCanyon)
        {
            AddPreviewOrganicBranchFrondActor(
                World,
                FString::Printf(TEXT("RaftSim_OrganicBranchFrondSupplement_%02d_%s"), FoliageIndex, *Spec.RiverId),
                FVector(
                    X + Side * (Spec.bHasWaterfalls ? 42.0f : 30.0f),
                    Y - Side * (Spec.bHasWaterfalls ? 58.0f : 38.0f),
                    FirstPartyProceduralCrownZ - (Spec.bHasWaterfalls ? 46.0f : 32.0f)),
                static_cast<float>((FoliageIndex * 67 + 19) % 360),
                FVector(
                    CanopyWidth * (Spec.bHasWaterfalls ? 0.94f : 0.74f) * FoliageCardSilhouetteDemotion,
                    CanopyWidth * (Spec.bHasWaterfalls ? 0.78f : 0.60f) * FoliageCardSilhouetteDemotion,
                    Height * (Spec.bHasWaterfalls ? 0.46f : 0.32f) * (Spec.bHasWaterfalls ? 0.84f : 0.88f)),
                ScalePreviewColor(FirstPartyProceduralCanopyShadowColor, Spec.bHasWaterfalls ? 0.92f : 0.88f),
                FoliageIndex * 71 + 13600,
                Spec.bHasWaterfalls,
                false);
            AddPreviewFineTwigCanopyLaceActor(
                World,
                FString::Printf(TEXT("RaftSim_FineTwigCanopyLace_%02d_%s"), FoliageIndex, *Spec.RiverId),
                FVector(
                    X - Side * (Spec.bHasWaterfalls ? 28.0f : 18.0f),
                    Y + Side * (Spec.bHasWaterfalls ? 34.0f : 22.0f),
                    FirstPartyProceduralCrownZ + (Spec.bHasWaterfalls ? 34.0f : 20.0f)),
                static_cast<float>((FoliageIndex * 73 + 11) % 360),
                FVector(
                    CanopyWidth * (Spec.bHasWaterfalls ? 1.08f : 0.82f) * FoliageCardSilhouetteDemotion,
                    CanopyWidth * (Spec.bHasWaterfalls ? 0.88f : 0.66f) * FoliageCardSilhouetteDemotion,
                    Height * (Spec.bHasWaterfalls ? 0.52f : 0.36f) * (Spec.bHasWaterfalls ? 0.84f : 0.88f)),
                ScalePreviewColor(FirstPartyProceduralCanopyToneColor, Spec.bHasWaterfalls ? 0.68f : 0.66f),
                FoliageIndex * 83 + 15100,
                Spec.bHasWaterfalls);
        }

        if (!Spec.bDesertCanyon && FoliageIndex % 2 == 0)
        {
            const int32 UnderstoryClusterCount = Spec.bHasWaterfalls ? 3 : 2;
            for (int32 UnderstoryIndex = 0; UnderstoryIndex < UnderstoryClusterCount; ++UnderstoryIndex)
            {
                const float Phase = static_cast<float>(FoliageIndex) * 0.77f + static_cast<float>(UnderstoryIndex) * 1.93f;
                float UnderstoryX = X + 95.0f * FMath::Cos(Phase) + 70.0f * static_cast<float>(UnderstoryIndex);
                float UnderstoryY =
                    Y - Side * (155.0f + 70.0f * static_cast<float>(UnderstoryIndex)) + 54.0f * FMath::Sin(Phase);
                float BestUnderstoryScore = -1000.0f;
                for (int32 CandidateIndex = 0; CandidateIndex < 4; ++CandidateIndex)
                {
                    const float CandidateX = UnderstoryX + 72.0f * FMath::Sin(Phase + static_cast<float>(CandidateIndex) * 1.31f);
                    const float CandidateY = UnderstoryY + Side * 86.0f * FMath::Cos(Phase * 0.73f + static_cast<float>(CandidateIndex) * 1.17f);
                    const float VegetationT = SamplePreviewMaskAtWorld(Spec, VegetationMaskPtr, CandidateX, CandidateY);
                    const float WaterT = SamplePreviewMaskAtWorld(Spec, WaterMaskPtr, CandidateX, CandidateY);
                    const float Score = VegetationT * 1.30f - WaterT * 0.95f +
                        0.04f * FMath::Sin(Phase + static_cast<float>(CandidateIndex));
                    if (Score > BestUnderstoryScore)
                    {
                        BestUnderstoryScore = Score;
                        UnderstoryX = CandidateX;
                        UnderstoryY = CandidateY;
                    }
                }
                const float UnderstoryZ = GetPreviewTerrainHeightCm(Spec, UnderstoryX, UnderstoryY, TerrainReliefPtr, HeightfieldPreviewPtr);
                const float UnderstoryMaskT = SamplePreviewMaskAtWorld(Spec, VegetationMaskPtr, UnderstoryX, UnderstoryY);
                const FLinearColor UnderstoryColor = FMath::Lerp(
                    FirstPartyProceduralCanopyShadowColor,
                    Spec.bHasWaterfalls ? FLinearColor(0.035f, 0.20f, 0.07f) : FLinearColor(0.13f, 0.26f, 0.10f),
                    FMath::Clamp(0.22f + UnderstoryMaskT * 0.14f, 0.22f, 0.42f));
                if (PcgSeedlingMesh)
                {
                    const float SeedlingScale = Spec.bHasWaterfalls ? 0.24f + 0.03f * static_cast<float>(UnderstoryIndex) : 0.18f;
                    AddPreviewMeshActor(
                        World,
                        PcgSeedlingMesh,
                        FString::Printf(TEXT("RaftSim_SourceAwareUnderstory_%02d_%02d_%s"), FoliageIndex, UnderstoryIndex, *Spec.RiverId),
                        FVector(UnderstoryX, UnderstoryY, UnderstoryZ),
                        FRotator(0.0f, static_cast<float>((FoliageIndex * 29 + UnderstoryIndex * 67) % 360), 0.0f),
                        FVector(SeedlingScale, SeedlingScale, SeedlingScale * (Spec.bHasWaterfalls ? 1.16f : 0.94f)),
                        UnderstoryColor);
                }
                else
                {
                    AddPreviewProceduralLeafClusterActor(
                        World,
                        FString::Printf(TEXT("RaftSim_Understory_%02d_%02d_%s"), FoliageIndex, UnderstoryIndex, *Spec.RiverId),
                        FVector(UnderstoryX, UnderstoryY, UnderstoryZ + 30.0f),
                        static_cast<float>((FoliageIndex * 29 + UnderstoryIndex * 67) % 360),
                        FVector(0.48f, 0.36f, 0.22f),
                        UnderstoryColor,
                        FoliageIndex * 31 + UnderstoryIndex + 7100,
                        Spec.bHasWaterfalls);
                }
            }
        }
        else if (Spec.bDesertCanyon && FoliageIndex % 2 == 0)
        {
            const float ScrubX = X + 130.0f * FMath::Sin(static_cast<float>(FoliageIndex) * 0.53f);
            const float ScrubY = Y - Side * (310.0f + 80.0f * FMath::Cos(static_cast<float>(FoliageIndex) * 0.41f));
            const float ScrubZ = GetPreviewTerrainHeightCm(Spec, ScrubX, ScrubY, TerrainReliefPtr, HeightfieldPreviewPtr);
            const FLinearColor ScrubColor = FLinearColor(0.24f, 0.27f, 0.15f);
            if (PcgSeedlingMesh)
            {
                AddPreviewMeshActor(
                    World,
                    PcgSeedlingMesh,
                    FString::Printf(TEXT("RaftSim_CanyonScrub_%02d_%s"), FoliageIndex, *Spec.RiverId),
                    FVector(ScrubX, ScrubY, ScrubZ),
                    FRotator(0.0f, static_cast<float>((FoliageIndex * 37) % 360), 0.0f),
                    FVector(0.10f, 0.10f, 0.08f),
                    ScrubColor);
            }
            else
            {
                AddPreviewProceduralLeafClusterActor(
                    World,
                    FString::Printf(TEXT("RaftSim_CanyonScrub_%02d_%s"), FoliageIndex, *Spec.RiverId),
                    FVector(ScrubX, ScrubY, ScrubZ + 18.0f),
                    static_cast<float>((FoliageIndex * 37) % 360),
                    FVector(0.24f, 0.18f, 0.12f),
                    ScrubColor,
                    FoliageIndex + 7500,
                    false);
            }
        }
    }

    const bool bCreateReviewOnlyForegroundRaftProxyInLifelikeCandidateMaps = false;
    if (bCreateReviewOnlyForegroundRaftProxyInLifelikeCandidateMaps)
    {
        AddPreviewRaftForeground(World, Spec, CubeMesh, CylinderMesh, MaterialAtlasAlbedoPtr);
    }
    else
    {
        OutSummary += FString::Printf(
            TEXT("Skipped review-only foreground raft/oar proxy generation for %s lifelike-candidate map.\n"),
            *Spec.RiverId);
    }
    const int32 AssignedReviewMaterialComponentCount = FirstPartyMaterialAssignments.IsCompleteForDurableSurfaceReview()
        ? AssignFirstPartyMaterialInstancesToPreviewScene(World, Spec, FirstPartyMaterialAssignments, OutSummary)
        : 0;
    AddPreviewCameraAndStart(World, Spec);
    if (!FirstPartyMaterialAssignments.IsCompleteForDurableSurfaceReview() || AssignedReviewMaterialComponentCount <= 0)
    {
        OutSummary += FString::Printf(
            TEXT("Failed first-party review material-instance scene assignment gate for %s.\n"),
            *Spec.RiverId);
        return false;
    }
    return SavePreviewWorld(World, Spec.MapPackagePath, OutSummary);
}

FText SeverityText(ERaftSimToolValidationSeverity Severity)
{
    switch (Severity)
    {
        case ERaftSimToolValidationSeverity::Blocking:
            return LOCTEXT("ValidationSeverityBlocking", "Blocking");
        case ERaftSimToolValidationSeverity::Warning:
            return LOCTEXT("ValidationSeverityWarning", "Warning");
        case ERaftSimToolValidationSeverity::Info:
        default:
            return LOCTEXT("ValidationSeverityInfo", "Info");
    }
}

TSharedRef<SWidget> MakePathRow(const FText& Label, const FString& Path)
{
    return SNew(SVerticalBox)
        + SVerticalBox::Slot()
            .AutoHeight()
            .Padding(0.0f, 2.0f)
        [
            SNew(STextBlock)
                .Text(Label)
                .Font(FCoreStyle::GetDefaultFontStyle("Bold", 9))
        ]
        + SVerticalBox::Slot()
            .AutoHeight()
            .Padding(0.0f, 0.0f, 0.0f, 4.0f)
        [
            SNew(STextBlock)
                .Text(FText::FromString(Path))
                .AutoWrapText(true)
        ];
}

TSharedRef<SWidget> MakeSectionHeader(const FText& Text)
{
    return SNew(STextBlock)
        .Text(Text)
        .Font(FCoreStyle::GetDefaultFontStyle("Bold", 12));
}

void PumpSlateForCapture(int32 FrameCount)
{
    if (!FSlateApplication::IsInitialized())
    {
        return;
    }

    FSlateApplication& SlateApplication = FSlateApplication::Get();
    for (int32 FrameIndex = 0; FrameIndex < FrameCount; ++FrameIndex)
    {
        SlateApplication.PumpMessages();
        SlateApplication.Tick(ESlateTickType::All);
        FPlatformProcess::Sleep(0.03f);
    }
}

template <typename AssetType, typename PopulateFunc>
bool CreateReviewedAsset(const FString& AssetName, PopulateFunc Populate, FString& OutSummary)
{
    const FString PackagePath = FString::Printf(TEXT("/Game/RaftSim/Tools/Reviewed/%s"), *AssetName);
    UPackage* Package = CreatePackage(*PackagePath);
    if (!Package)
    {
        OutSummary += FString::Printf(TEXT("Failed to create package %s\n"), *PackagePath);
        return false;
    }

    AssetType* Asset = FindObject<AssetType>(Package, *AssetName);
    if (!Asset)
    {
        Asset = NewObject<AssetType>(Package, *AssetName, RF_Public | RF_Standalone);
        FAssetRegistryModule::AssetCreated(Asset);
    }

    if (!Asset)
    {
        OutSummary += FString::Printf(TEXT("Failed to create asset %s\n"), *AssetName);
        return false;
    }

    Asset->Modify();
    Populate(Asset);
    Package->MarkPackageDirty();

    const FString Filename = FPackageName::LongPackageNameToFilename(PackagePath, FPackageName::GetAssetPackageExtension());
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;

    const bool bSaved = UPackage::SavePackage(Package, Asset, *Filename, SaveArgs);
    OutSummary += FString::Printf(TEXT("%s %s -> %s\n"), bSaved ? TEXT("Saved") : TEXT("Failed"), *AssetName, *Filename);
    return bSaved;
}

FRaftSimReplayDebugBookmark MakeBookmark(const TCHAR* Id, const TCHAR* Label, float TimeSeconds, TArray<FName> Tags)
{
    FRaftSimReplayDebugBookmark Bookmark;
    Bookmark.BookmarkId = FName(Id);
    Bookmark.DisplayName = FText::FromString(FString(Label));
    Bookmark.TimeSeconds = TimeSeconds;
    Bookmark.Tags = MoveTemp(Tags);
    return Bookmark;
}

FRaftSimReplayDebugOverlayToggle MakeOverlay(
    ERaftSimWaterDebugView View,
    const TCHAR* Id,
    const TCHAR* Label,
    bool bDefaultEnabled)
{
    FRaftSimReplayDebugOverlayToggle Overlay;
    Overlay.View = View;
    Overlay.OverlayId = FName(Id);
    Overlay.DisplayName = FText::FromString(FString(Label));
    Overlay.bDefaultEnabled = bDefaultEnabled;
    return Overlay;
}

FRaftSimToolValidationMessage MakeValidationMessage(
    const TCHAR* Id,
    ERaftSimToolValidationSeverity Severity,
    const TCHAR* Summary,
    const FString& SourcePath,
    bool bBlocksExport)
{
    FRaftSimToolValidationMessage Message;
    Message.MessageId = FName(Id);
    Message.Severity = Severity;
    Message.Summary = FText::FromString(FString(Summary));
    Message.SourcePath = SourcePath;
    Message.bBlocksExport = bBlocksExport;
    return Message;
}
} // namespace

void FRaftSimEditorModule::StartupModule()
{
    RegisterToolTabs();

    OpenToolConsoleCommand = MakeUnique<FAutoConsoleCommand>(
        TEXT("RaftSim.OpenTool"),
        TEXT("Open one RaftSim editor tool tab by tool id."),
        FConsoleCommandWithArgsDelegate::CreateRaw(this, &FRaftSimEditorModule::HandleOpenToolCommand));
    OpenAllToolsConsoleCommand = MakeUnique<FAutoConsoleCommand>(
        TEXT("RaftSim.OpenAllTools"),
        TEXT("Open every RaftSim editor tool tab."),
        FConsoleCommandWithArgsDelegate::CreateLambda([this](const TArray<FString>&) { OpenAllTools(); }));
    CreateReviewedDataAssetsConsoleCommand = MakeUnique<FAutoConsoleCommand>(
        TEXT("RaftSim.CreateReviewedDataAssets"),
        TEXT("Create reviewed RaftSim tool DataAssets from source-controlled manifests."),
        FConsoleCommandWithArgsDelegate::CreateRaw(this, &FRaftSimEditorModule::HandleCreateReviewedDataAssetsCommand));
    CaptureToolEvidenceConsoleCommand = MakeUnique<FAutoConsoleCommand>(
        TEXT("RaftSim.CaptureToolEvidence"),
        TEXT("Open RaftSim tool tabs and capture screenshot evidence."),
        FConsoleCommandWithArgsDelegate::CreateRaw(this, &FRaftSimEditorModule::HandleCaptureToolEvidenceCommand));
    CreatePhotorealEnvironmentPreviewMapsConsoleCommand = MakeUnique<FAutoConsoleCommand>(
        TEXT("RaftSim.CreatePhotorealEnvironmentPreviewMaps"),
        TEXT("Generate source-aware procedural preview maps for the runnable river environments."),
        FConsoleCommandWithArgsDelegate::CreateRaw(this, &FRaftSimEditorModule::HandleCreatePhotorealEnvironmentPreviewMapsCommand));
    CapturePhotorealEnvironmentPreviewsConsoleCommand = MakeUnique<FAutoConsoleCommand>(
        TEXT("RaftSim.CapturePhotorealEnvironmentPreviews"),
        TEXT("Record the river environment preview capture manifest placeholder."),
        FConsoleCommandWithArgsDelegate::CreateRaw(this, &FRaftSimEditorModule::HandleCapturePhotorealEnvironmentPreviewsCommand));
    CreateLandscapeImportCandidateMapsConsoleCommand = MakeUnique<FAutoConsoleCommand>(
        TEXT("RaftSim.CreateLandscapeImportCandidateMaps"),
        TEXT("Import review-gated source DEMs as isolated Unreal Landscape candidate maps and capture them."),
        FConsoleCommandWithArgsDelegate::CreateRaw(this, &FRaftSimEditorModule::HandleCreateLandscapeImportCandidateMapsCommand));

    bCreatePhotorealEnvironmentPreviewMapsOnStartup =
        FParse::Param(FCommandLine::Get(), TEXT("RaftSimCreatePhotorealEnvironmentPreviewMaps"));
    bCapturePhotorealEnvironmentPreviewsOnStartup =
        FParse::Param(FCommandLine::Get(), TEXT("RaftSimCapturePhotorealEnvironmentPreviews"));
    bCreateLandscapeImportCandidateMapsOnStartup =
        FParse::Param(FCommandLine::Get(), TEXT("RaftSimCreateLandscapeImportCandidateMaps"));
    bExitAfterPhotorealEnvironmentAutomation =
        FParse::Param(FCommandLine::Get(), TEXT("RaftSimExitAfterEnvironmentAutomation"));

    if (bCreatePhotorealEnvironmentPreviewMapsOnStartup ||
        bCapturePhotorealEnvironmentPreviewsOnStartup ||
        bCreateLandscapeImportCandidateMapsOnStartup)
    {
        PhotorealEnvironmentAutomationPostEngineInitHandle =
            FCoreDelegates::GetOnPostEngineInit().AddRaw(this, &FRaftSimEditorModule::HandlePhotorealEnvironmentAutomationStartup);
    }

    UToolMenus::RegisterStartupCallback(
        FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FRaftSimEditorModule::RegisterMenus));
}

void FRaftSimEditorModule::ShutdownModule()
{
    if (PhotorealEnvironmentAutomationPostEngineInitHandle.IsValid())
    {
        FCoreDelegates::GetOnPostEngineInit().Remove(PhotorealEnvironmentAutomationPostEngineInitHandle);
        PhotorealEnvironmentAutomationPostEngineInitHandle.Reset();
    }
    if (PhotorealEnvironmentAutomationTickerHandle.IsValid())
    {
        FTSTicker::RemoveTicker(PhotorealEnvironmentAutomationTickerHandle);
        PhotorealEnvironmentAutomationTickerHandle.Reset();
    }

    OpenToolConsoleCommand.Reset();
    OpenAllToolsConsoleCommand.Reset();
    CreateReviewedDataAssetsConsoleCommand.Reset();
    CaptureToolEvidenceConsoleCommand.Reset();
    CreatePhotorealEnvironmentPreviewMapsConsoleCommand.Reset();
    CapturePhotorealEnvironmentPreviewsConsoleCommand.Reset();
    CreateLandscapeImportCandidateMapsConsoleCommand.Reset();
    UnregisterToolTabs();

    if (UObjectInitialized())
    {
        UToolMenus::UnRegisterStartupCallback(this);
        UToolMenus::UnregisterOwner(this);
    }
}

void FRaftSimEditorModule::RegisterMenus()
{
    FToolMenuOwnerScoped OwnerScoped(this);

    UToolMenu* MainMenu = UToolMenus::Get()->ExtendMenu(TEXT("LevelEditor.MainMenu"));
    if (!MainMenu)
    {
        return;
    }

    FToolMenuSection& Section = MainMenu->FindOrAddSection(TEXT("RaftSimTools"));
    Section.AddSubMenu(
        TEXT("RaftSimToolsSubMenu"),
        LOCTEXT("RaftSimToolsLabel", "RaftSim Tools"),
        LOCTEXT("RaftSimToolsTooltip", "Open RaftSim validation, replay, river authoring, and playtest tools."),
        FNewToolMenuDelegate::CreateRaw(this, &FRaftSimEditorModule::PopulateRaftSimToolsMenu));
}

void FRaftSimEditorModule::RegisterToolTabs()
{
    for (const FRaftSimEditorToolDescriptor& Descriptor : GetToolDescriptors())
    {
        const FName TabId = GetTabIdForTool(Descriptor.ToolId);
        FGlobalTabmanager::Get()->RegisterNomadTabSpawner(
            TabId,
            FOnSpawnTab::CreateRaw(this, &FRaftSimEditorModule::SpawnToolTab, Descriptor.ToolId))
            .SetDisplayName(Descriptor.DisplayName)
            .SetTooltipText(Descriptor.Description)
            .SetMenuType(ETabSpawnerMenuType::Hidden);
    }
}

void FRaftSimEditorModule::UnregisterToolTabs()
{
    for (const FRaftSimEditorToolDescriptor& Descriptor : GetToolDescriptors())
    {
        FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(GetTabIdForTool(Descriptor.ToolId));
    }
}

void FRaftSimEditorModule::PopulateRaftSimToolsMenu(UToolMenu* Menu)
{
    if (!Menu)
    {
        return;
    }

    FToolMenuSection& ToolSection =
        Menu->AddSection(TEXT("RaftSimToolSurfaces"), LOCTEXT("RaftSimToolSurfaces", "Tool Surfaces"));

    for (const FRaftSimEditorToolDescriptor& Descriptor : GetToolDescriptors())
    {
        ToolSection.AddMenuEntry(
            Descriptor.ToolId,
            Descriptor.DisplayName,
            Descriptor.Description,
            FSlateIcon(),
            FUIAction(FExecuteAction::CreateRaw(this, &FRaftSimEditorModule::LaunchTool, Descriptor.ToolId)));
    }

    FToolMenuSection& UtilitySection =
        Menu->AddSection(TEXT("RaftSimToolUtilities"), LOCTEXT("RaftSimToolUtilities", "Utilities"));
    UtilitySection.AddMenuEntry(
        TEXT("OpenAllRaftSimTools"),
        LOCTEXT("OpenAllRaftSimTools", "Open All Tool Tabs"),
        LOCTEXT("OpenAllRaftSimToolsTooltip", "Open every RaftSim tool surface for review or screenshot capture."),
        FSlateIcon(),
        FUIAction(FExecuteAction::CreateRaw(this, &FRaftSimEditorModule::OpenAllTools)));
    UtilitySection.AddMenuEntry(
        TEXT("CreateReviewedRaftSimDataAssets"),
        LOCTEXT("CreateReviewedRaftSimDataAssets", "Create Reviewed Tool DataAssets"),
        LOCTEXT("CreateReviewedRaftSimDataAssetsTooltip", "Generate reviewed DataAssets from the source-controlled tool manifests."),
        FSlateIcon(),
        FUIAction(FExecuteAction::CreateLambda(
            [this]()
            {
                FString Summary;
                CreateReviewedToolDataAssets(Summary);
                UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
            })));
    UtilitySection.AddMenuEntry(
        TEXT("CaptureRaftSimToolEvidence"),
        LOCTEXT("CaptureRaftSimToolEvidence", "Capture Tool Screenshots"),
        LOCTEXT("CaptureRaftSimToolEvidenceTooltip", "Capture screenshot evidence for all currently open RaftSim tool tabs."),
        FSlateIcon(),
        FUIAction(FExecuteAction::CreateLambda(
            [this]()
            {
                FString Summary;
                CaptureToolEvidence(Summary);
                UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
            })));
    UtilitySection.AddMenuEntry(
        TEXT("CreatePhotorealEnvironmentPreviewMaps"),
        LOCTEXT("CreatePhotorealEnvironmentPreviewMaps", "Create River Preview Maps"),
        LOCTEXT("CreatePhotorealEnvironmentPreviewMapsTooltip", "Generate source-aware procedural Unreal preview maps for South Fork, Colorado, and Pacuare."),
        FSlateIcon(),
        FUIAction(FExecuteAction::CreateLambda(
            [this]()
            {
                FString Summary;
                CreatePhotorealEnvironmentPreviewMaps(Summary);
                UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
            })));
    UtilitySection.AddMenuEntry(
        TEXT("CapturePhotorealEnvironmentPreviews"),
        LOCTEXT("CapturePhotorealEnvironmentPreviews", "Capture River Preview Evidence"),
        LOCTEXT("CapturePhotorealEnvironmentPreviewsTooltip", "Record capture evidence placeholders for generated river environment previews."),
        FSlateIcon(),
        FUIAction(FExecuteAction::CreateLambda(
            [this]()
            {
                FString Summary;
                CapturePhotorealEnvironmentPreviews(Summary);
                UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
            })));
    UtilitySection.AddMenuEntry(
        TEXT("CreateLandscapeImportCandidateMaps"),
        LOCTEXT("CreateLandscapeImportCandidateMaps", "Create Source Landscape Candidates"),
        LOCTEXT("CreateLandscapeImportCandidateMapsTooltip", "Import the review-gated source DEMs into isolated Landscape candidate maps and capture geometry-review evidence."),
        FSlateIcon(),
        FUIAction(FExecuteAction::CreateLambda(
            [this]()
            {
                FString Summary;
                CreateLandscapeImportCandidateMaps(Summary);
                UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
            })));
}

void FRaftSimEditorModule::LaunchTool(FName ToolId)
{
    const FName TabId = GetTabIdForTool(ToolId);
    TSharedPtr<SDockTab> Tab = FGlobalTabmanager::Get()->TryInvokeTab(TabId);
    if (Tab.IsValid())
    {
        OpenedToolTabs.Add(ToolId, Tab);
    }

    UE_LOG(
        LogRaftSimEditor,
        Display,
        TEXT("RaftSim editor tool opened: %s. Registry manifest: %s"),
        *ToolId.ToString(),
        RaftSimEditorTools::ToolRegistryManifestPath);
}

void FRaftSimEditorModule::OpenAllTools()
{
    for (const FRaftSimEditorToolDescriptor& Descriptor : GetToolDescriptors())
    {
        LaunchTool(Descriptor.ToolId);
    }
}

void FRaftSimEditorModule::HandleOpenToolCommand(const TArray<FString>& Args)
{
    if (Args.IsEmpty())
    {
        UE_LOG(LogRaftSimEditor, Warning, TEXT("RaftSim.OpenTool requires a tool id."));
        return;
    }

    LaunchTool(FName(*Args[0]));
}

void FRaftSimEditorModule::HandleCreateReviewedDataAssetsCommand(const TArray<FString>&)
{
    FString Summary;
    CreateReviewedToolDataAssets(Summary);
    UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
}

void FRaftSimEditorModule::HandleCaptureToolEvidenceCommand(const TArray<FString>&)
{
    FString Summary;
    CaptureToolEvidence(Summary);
    UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
}

void FRaftSimEditorModule::HandleCreatePhotorealEnvironmentPreviewMapsCommand(const TArray<FString>&)
{
    FString Summary;
    CreatePhotorealEnvironmentPreviewMaps(Summary);
    UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
}

void FRaftSimEditorModule::HandleCapturePhotorealEnvironmentPreviewsCommand(const TArray<FString>&)
{
    FString Summary;
    CapturePhotorealEnvironmentPreviews(Summary);
    UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
}

void FRaftSimEditorModule::HandleCreateLandscapeImportCandidateMapsCommand(const TArray<FString>&)
{
    FString Summary;
    CreateLandscapeImportCandidateMaps(Summary);
    UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
}

void FRaftSimEditorModule::HandlePhotorealEnvironmentAutomationStartup()
{
    if (PhotorealEnvironmentAutomationPostEngineInitHandle.IsValid())
    {
        FCoreDelegates::GetOnPostEngineInit().Remove(PhotorealEnvironmentAutomationPostEngineInitHandle);
        PhotorealEnvironmentAutomationPostEngineInitHandle.Reset();
    }

    PhotorealEnvironmentAutomationTickerHandle = FTSTicker::GetCoreTicker().AddTicker(
        FTickerDelegate::CreateRaw(this, &FRaftSimEditorModule::TickPhotorealEnvironmentAutomationStartup),
        0.5f);
}

bool FRaftSimEditorModule::TickPhotorealEnvironmentAutomationStartup(float)
{
    ++PhotorealEnvironmentAutomationStartupAttempts;
    if (!GEditor || !GEditor->GetEditorWorldContext().World())
    {
        if (PhotorealEnvironmentAutomationStartupAttempts < 120)
        {
            return true;
        }

        UE_LOG(LogRaftSimEditor, Error, TEXT("Timed out waiting for an editor world before photoreal environment automation."));
        if (bExitAfterPhotorealEnvironmentAutomation)
        {
            FPlatformMisc::RequestExit(true, TEXT("RaftSim photoreal environment automation timed out"));
        }
        return false;
    }

    PhotorealEnvironmentAutomationTickerHandle.Reset();

    FString Summary;
    bool bSucceeded = true;

    if (bCreatePhotorealEnvironmentPreviewMapsOnStartup)
    {
        bSucceeded &= CreatePhotorealEnvironmentPreviewMaps(Summary);
    }

    if (bCapturePhotorealEnvironmentPreviewsOnStartup)
    {
        bSucceeded &= CapturePhotorealEnvironmentPreviews(Summary);
    }

    if (bCreateLandscapeImportCandidateMapsOnStartup)
    {
        bSucceeded &= CreateLandscapeImportCandidateMaps(Summary);
    }

    UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);

    if (bExitAfterPhotorealEnvironmentAutomation)
    {
        FPlatformMisc::RequestExit(!bSucceeded, TEXT("RaftSim photoreal environment automation complete"));
    }

    return false;
}

void FRaftSimEditorModule::ExecuteValidationAction(FName ActionId)
{
    const FRaftSimToolValidationAction* Action = RaftSimEditorValidation::FindDefaultValidationAction(ActionId);
    if (!Action)
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("Unknown RaftSim validation action: %s"), *ActionId.ToString());
        return;
    }

    const FRaftSimToolValidationActionResult Result = RaftSimEditorValidation::ExecuteAction(*Action);
    UE_LOG(
        LogRaftSimEditor,
        Display,
        TEXT("Validation action %s: %s"),
        *ActionId.ToString(),
        *Result.Message.Summary.ToString());
}

const TArray<FRaftSimEditorToolDescriptor>& FRaftSimEditorModule::GetToolDescriptors()
{
    if (ToolDescriptors.IsEmpty())
    {
        ToolDescriptors.Add(MakeToolDescriptor(
            TEXT("ReplayDebugViewer"),
            ERaftSimEditorToolKind::ReplayDebugViewer,
            LOCTEXT("ReplayDebugViewerLabel", "Replay + Debug Viewer"),
            LOCTEXT("ReplayDebugViewerTooltip", "Review replay bookmarks, water fields, contacts, and runtime overlays."),
            TEXT("unreal/Content/RaftSim/Tools/replay_debug_viewer.json"),
            TEXT("RaftSimDebug"),
            false));

        ToolDescriptors.Add(MakeToolDescriptor(
            TEXT("RapidRiverEditor"),
            ERaftSimEditorToolKind::RapidRiverEditor,
            LOCTEXT("RapidRiverEditorLabel", "Rapid/River Editor"),
            LOCTEXT("RapidRiverEditorTooltip", "Author river annotations, source evidence, expected raft outcomes, and export readiness."),
            TEXT("unreal/Content/RaftSim/Tools/rapid_river_editor_shell.json"),
            TEXT("RaftSimRiver"),
            true));

        ToolDescriptors.Add(MakeToolDescriptor(
            TEXT("FeatureTuningEditor"),
            ERaftSimEditorToolKind::FeatureTuningEditor,
            LOCTEXT("FeatureTuningEditorLabel", "Feature Tuning Editor"),
            LOCTEXT("FeatureTuningEditorTooltip", "Tune flow-dependent feature forcing and presentation cues with validation guards."),
            TEXT("unreal/Content/RaftSim/Tools/feature_tuning_editor_shell.json"),
            TEXT("RaftSimRiver"),
            true));

        ToolDescriptors.Add(MakeToolDescriptor(
            TEXT("GeospatialValidator"),
            ERaftSimEditorToolKind::GeospatialValidator,
            LOCTEXT("GeospatialValidatorLabel", "Geospatial Import/Export Validator"),
            LOCTEXT("GeospatialValidatorTooltip", "Check source manifests, CRS, reach-local grids, stitched exports, and solver regeneration."),
            TEXT("unreal/Content/RaftSim/River/geospatial_import_pipeline.json"),
            TEXT("RaftSimGeo"),
            true));

        ToolDescriptors.Add(MakeToolDescriptor(
            TEXT("VerticalSliceLauncher"),
            ERaftSimEditorToolKind::VerticalSliceLauncher,
            LOCTEXT("VerticalSliceLauncherLabel", "Vertical Slice Playtest Launcher"),
            LOCTEXT("VerticalSliceLauncherTooltip", "Launch the selected South Fork vertical-slice scenario and capture review evidence."),
            TEXT("unreal/Content/RaftSim/VerticalSlice/first_rapid_vertical_slice.json"),
            TEXT("RaftSimUI"),
            false));
    }

    return ToolDescriptors;
}

const FRaftSimEditorToolDescriptor* FRaftSimEditorModule::FindToolDescriptor(FName ToolId)
{
    return GetToolDescriptors().FindByPredicate(
        [ToolId](const FRaftSimEditorToolDescriptor& Descriptor)
        {
            return Descriptor.ToolId == ToolId;
        });
}

FName FRaftSimEditorModule::GetTabIdForTool(FName ToolId) const
{
    if (ToolId == TEXT("ReplayDebugViewer"))
    {
        return ReplayDebugViewerTabId;
    }
    if (ToolId == TEXT("RapidRiverEditor"))
    {
        return RapidRiverEditorTabId;
    }
    if (ToolId == TEXT("FeatureTuningEditor"))
    {
        return FeatureTuningEditorTabId;
    }
    if (ToolId == TEXT("GeospatialValidator"))
    {
        return GeospatialValidatorTabId;
    }
    if (ToolId == TEXT("VerticalSliceLauncher"))
    {
        return VerticalSliceLauncherTabId;
    }

    return ReplayDebugViewerTabId;
}

TSharedRef<SDockTab> FRaftSimEditorModule::SpawnToolTab(const FSpawnTabArgs& Args, FName ToolId)
{
    const FRaftSimEditorToolDescriptor* Descriptor = FindToolDescriptor(ToolId);

    TSharedRef<SDockTab> Tab = SNew(SDockTab)
        .TabRole(ETabRole::NomadTab)
        .Label(Descriptor ? Descriptor->DisplayName : FText::FromName(ToolId));

    if (Descriptor)
    {
        TSharedRef<SWidget> ToolPanel = BuildToolPanel(*Descriptor);
        Tab->SetContent(ToolPanel);
        OpenedToolTabs.Add(ToolId, Tab);
        OpenedToolPanels.Add(ToolId, ToolPanel);
    }
    else
    {
        Tab->SetContent(
            SNew(STextBlock)
                .Text(FText::Format(LOCTEXT("UnknownRaftSimTool", "Unknown RaftSim tool: {0}"), FText::FromName(ToolId))));
    }

    return Tab;
}

TSharedRef<SWidget> FRaftSimEditorModule::BuildToolPanel(const FRaftSimEditorToolDescriptor& Descriptor)
{
    TSharedRef<SVerticalBox> Root = SNew(SVerticalBox);

    Root->AddSlot()
        .AutoHeight()
        .Padding(12.0f, 10.0f)
    [
        SNew(STextBlock)
            .Text(Descriptor.DisplayName)
            .Font(FCoreStyle::GetDefaultFontStyle("Bold", 16))
    ];

    Root->AddSlot()
        .AutoHeight()
        .Padding(12.0f, 0.0f, 12.0f, 8.0f)
    [
        SNew(STextBlock)
            .Text(Descriptor.Description)
            .AutoWrapText(true)
    ];

    Root->AddSlot()
        .AutoHeight()
        .Padding(12.0f, 0.0f, 12.0f, 8.0f)
    [
        MakePathRow(LOCTEXT("ToolSourceManifest", "Source Manifest"), Descriptor.SourceManifest)
    ];

    Root->AddSlot()
        .FillHeight(1.0f)
        .Padding(12.0f, 0.0f)
    [
        SNew(SScrollBox)
        + SScrollBox::Slot()
        [
            BuildToolSpecificBody(Descriptor)
        ]
    ];

    TSharedRef<SUniformGridPanel> ButtonGrid = SNew(SUniformGridPanel).SlotPadding(FMargin(4.0f));
    const TArray<FRaftSimToolValidationAction> Actions = RaftSimEditorValidation::BuildDefaultValidationActions();
    for (int32 Index = 0; Index < Actions.Num(); ++Index)
    {
        const FRaftSimToolValidationAction& Action = Actions[Index];
        ButtonGrid->AddSlot(Index % 4, Index / 4)
        [
            SNew(SButton)
                .Text(Action.DisplayName)
                .ToolTipText(FText::FromString(Action.CommandPreview))
                .OnClicked_Lambda(
                    [this, ActionId = Action.ActionId]()
                    {
                        ExecuteValidationAction(ActionId);
                        return FReply::Handled();
                    })
        ];
    }

    Root->AddSlot()
        .AutoHeight()
        .Padding(12.0f, 8.0f)
    [
        SNew(SBorder)
            .Padding(8.0f)
        [
            SNew(SVerticalBox)
            + SVerticalBox::Slot()
                .AutoHeight()
                .Padding(0.0f, 0.0f, 0.0f, 6.0f)
            [
                MakeSectionHeader(LOCTEXT("ValidationActionsHeader", "Validation Actions"))
            ]
            + SVerticalBox::Slot()
                .AutoHeight()
            [
                ButtonGrid
            ]
        ]
    ];

    return Root;
}

TSharedRef<SWidget> FRaftSimEditorModule::BuildToolSpecificBody(const FRaftSimEditorToolDescriptor& Descriptor)
{
    TSharedRef<SVerticalBox> Body = SNew(SVerticalBox);

    Body->AddSlot()
        .AutoHeight()
        .Padding(0.0f, 4.0f)
    [
        MakeSectionHeader(LOCTEXT("ToolReadinessHeader", "Readiness"))
    ];

    Body->AddSlot()
        .AutoHeight()
        .Padding(0.0f, 2.0f, 0.0f, 8.0f)
    [
        SNew(STextBlock)
            .Text(Descriptor.bRequiresValidationBeforeExport
                ? LOCTEXT("ToolRequiresValidation", "Exports are blocked until validation actions and source evidence pass.")
                : LOCTEXT("ToolReviewOnly", "This tool is review/playtest oriented and does not export authoritative river data."))
            .AutoWrapText(true)
    ];

    if (Descriptor.ToolId == TEXT("ReplayDebugViewer"))
    {
        Body->AddSlot().AutoHeight().Padding(0.0f, 4.0f)[MakeSectionHeader(LOCTEXT("ReplayTimelineHeader", "Timeline And Overlays"))];
        Body->AddSlot().AutoHeight()[MakePathRow(LOCTEXT("ReplayManifest", "Replay Manifest"), TEXT("physics/data/readiness/milestone_10/unreal_visualization/manifest.json"))];
        Body->AddSlot().AutoHeight()[MakePathRow(LOCTEXT("DebugManifest", "Debug Views"), TEXT("unreal/Content/RaftSim/Debug/live_water_debug_views.json"))];
        Body->AddSlot().AutoHeight().Padding(0.0f, 6.0f)[SNew(STextBlock).Text(LOCTEXT("ReplayOverlayList", "Default overlays: depth, velocity, raft trajectory, contact probes, and runtime budgets. Optional overlays: Froude, wet/dry mask, feature tags, and conservation deltas.")).AutoWrapText(true)];
    }
    else if (Descriptor.ToolId == TEXT("RapidRiverEditor"))
    {
        Body->AddSlot().AutoHeight().Padding(0.0f, 4.0f)[MakeSectionHeader(LOCTEXT("RiverEditorPanelsHeader", "Authoring Panels"))];
        Body->AddSlot().AutoHeight()[SNew(STextBlock).Text(LOCTEXT("RiverEditorPanels", "Map view, annotation list, evidence refs, guide notes, expected outcomes, source provenance, validation warnings, and export readiness.")).AutoWrapText(true)];
        Body->AddSlot().AutoHeight()[MakePathRow(LOCTEXT("SouthForkPass", "South Fork Sample"), TEXT("unreal/Content/RaftSim/River/south_fork_first_river_editor_pass.json"))];
    }
    else if (Descriptor.ToolId == TEXT("FeatureTuningEditor"))
    {
        Body->AddSlot().AutoHeight().Padding(0.0f, 4.0f)[MakeSectionHeader(LOCTEXT("FeatureTuningControlsHeader", "Feature Tuning Controls"))];
        Body->AddSlot().AutoHeight()[SNew(STextBlock).Text(LOCTEXT("FeatureTuningControls", "Controls separate solver-state, raft-coupling, visual-only, and audio-only domains. Physics-facing edits require manifest records, GeoClaw comparison, and conservation guards.")).AutoWrapText(true)];
        Body->AddSlot().AutoHeight()[MakePathRow(LOCTEXT("FeatureDefaults", "Feature Defaults"), TEXT("physics/config/feature_forcing_defaults.json"))];
    }
    else if (Descriptor.ToolId == TEXT("GeospatialValidator"))
    {
        Body->AddSlot().AutoHeight().Padding(0.0f, 4.0f)[MakeSectionHeader(LOCTEXT("GeospatialValidationHeader", "Geospatial Validation"))];
        Body->AddSlot().AutoHeight()[SNew(STextBlock).Text(LOCTEXT("GeospatialValidation", "Validates source manifests, CRS/transform metadata, reach-local grids, stitched whole-window outputs, and solver package regeneration evidence.")).AutoWrapText(true)];
    }
    else if (Descriptor.ToolId == TEXT("VerticalSliceLauncher"))
    {
        Body->AddSlot().AutoHeight().Padding(0.0f, 4.0f)[MakeSectionHeader(LOCTEXT("VerticalSliceHeader", "Vertical Slice Review"))];
        Body->AddSlot().AutoHeight()[SNew(STextBlock).Text(LOCTEXT("VerticalSliceReview", "Launches the selected South Fork scenario after replay/debug and validation evidence is clean. Current launcher exposes acceptance reports and playtest evidence hooks.")).AutoWrapText(true)];
    }

    Body->AddSlot().AutoHeight().Padding(0.0f, 10.0f)[SNew(SSeparator)];
    Body->AddSlot().AutoHeight().Padding(0.0f, 4.0f)[MakeSectionHeader(LOCTEXT("CommandLineHeader", "Command Line Hooks"))];
    Body->AddSlot().AutoHeight()[SNew(STextBlock).Text(LOCTEXT("CommandLineHooks", "Use RaftSim.OpenAllTools, RaftSim.CreateReviewedDataAssets, and RaftSim.CaptureToolEvidence from the Unreal console or ExecCmds for repeatable review runs.")).AutoWrapText(true)];

    return Body;
}

bool FRaftSimEditorModule::CreateReviewedToolDataAssets(FString& OutSummary)
{
    bool bAllSaved = true;

    bAllSaved &= CreateReviewedAsset<URaftSimEditorToolRegistry>(
        TEXT("DA_RaftSimToolRegistry"),
        [this](URaftSimEditorToolRegistry* Asset)
        {
            Asset->Tools = GetToolDescriptors();
        },
        OutSummary);

    bAllSaved &= CreateReviewedAsset<URaftSimReplayDebugViewerConfig>(
        TEXT("DA_ReplayDebugViewer"),
        [](URaftSimReplayDebugViewerConfig* Asset)
        {
            Asset->Bookmarks = {
                MakeBookmark(TEXT("entry"), TEXT("Entry"), 0.0f, {TEXT("line_choice"), TEXT("initial_raft_pose")}),
                MakeBookmark(TEXT("first_contact_window"), TEXT("First Contact Window"), 1.0f / 60.0f, {TEXT("raft_contact"), TEXT("force_sample")}),
                MakeBookmark(TEXT("force_peak_review"), TEXT("Force Peak Review"), 0.05f, {TEXT("buoyancy"), TEXT("drag"), TEXT("contact_probe")}),
                MakeBookmark(TEXT("exit_pose"), TEXT("Exit Pose"), 4.0f / 60.0f, {TEXT("finish"), TEXT("runtime_budget")})};
            Asset->Overlays = {
                MakeOverlay(ERaftSimWaterDebugView::Depth, TEXT("depth"), TEXT("Depth"), true),
                MakeOverlay(ERaftSimWaterDebugView::Velocity, TEXT("velocity"), TEXT("Velocity"), true),
                MakeOverlay(ERaftSimWaterDebugView::Froude, TEXT("froude"), TEXT("Froude"), false),
                MakeOverlay(ERaftSimWaterDebugView::WetDryMask, TEXT("wet_dry_mask"), TEXT("Wet/Dry Mask"), false),
                MakeOverlay(ERaftSimWaterDebugView::FeatureTags, TEXT("feature_tags"), TEXT("Feature Tags"), false),
                MakeOverlay(ERaftSimWaterDebugView::ConservationDeltas, TEXT("conservation_deltas"), TEXT("Conservation Deltas"), false),
                MakeOverlay(ERaftSimWaterDebugView::RaftTrajectory, TEXT("raft_trajectory"), TEXT("Raft Trajectory"), true),
                MakeOverlay(ERaftSimWaterDebugView::ContactProbes, TEXT("contact_probes"), TEXT("Contact Probes"), true),
                MakeOverlay(ERaftSimWaterDebugView::RuntimeBudgets, TEXT("runtime_budgets"), TEXT("Runtime Budgets"), true)};
        },
        OutSummary);

    bAllSaved &= CreateReviewedAsset<URaftSimRapidRiverEditorShellConfig>(
        TEXT("DA_RapidRiverEditorShell"),
        [](URaftSimRapidRiverEditorShellConfig* Asset)
        {
            Asset->RequiredPanelIds = {
                TEXT("map_view"),
                TEXT("annotation_list"),
                TEXT("evidence_refs"),
                TEXT("guide_notes"),
                TEXT("expected_outcomes"),
                TEXT("source_provenance"),
                TEXT("validation_warnings"),
                TEXT("export_readiness")};

            FRaftSimRiverEditorShellEvidenceRef Evidence;
            Evidence.EvidenceId = TEXT("round_trip_validation");
            Evidence.LayerId = TEXT("stitched_validation_overlay");
            Evidence.SourceManifest = TEXT("unreal/Content/RaftSim/River/round_trip_validation.json");
            Evidence.RightsStatus = TEXT("internal_validation_artifact");
            Evidence.Confidence = 0.7f;

            FRaftSimRiverEditorShellAnnotation Annotation;
            Annotation.AnnotationId = TEXT("first_technical_raft_line");
            Annotation.DisplayName = FText::FromString(TEXT("First Technical Raft Line"));
            Annotation.GeometryKind = ERaftSimRiverAnnotationGeometryKind::RaftLine;
            Annotation.StationStartMeters = 90.0f;
            Annotation.StationEndMeters = 135.0f;
            Annotation.ExpectedOutcomes = {
                ERaftSimRiverExpectedOutcome::Surf,
                ERaftSimRiverExpectedOutcome::Flush,
                ERaftSimRiverExpectedOutcome::Pin,
                ERaftSimRiverExpectedOutcome::Release,
                ERaftSimRiverExpectedOutcome::Flip};
            Annotation.Evidence = {Evidence};
            Annotation.GuideNote = FText::FromString(TEXT("Reviewed shell sample for surf/flush/pin/release/flip trajectory review."));
            Annotation.bRightsCleared = true;
            Annotation.bHasValidationOverlay = true;
            Asset->SampleAnnotations = {Annotation};
            Asset->ValidationMessages = {
                MakeValidationMessage(
                    TEXT("stitched_export_required"),
                    ERaftSimToolValidationSeverity::Warning,
                    TEXT("Every playable window must preserve stitched whole-window validation outputs."),
                    TEXT("unreal/Content/RaftSim/River/reach_local_streaming.json"),
                    false)};
        },
        OutSummary);

    bAllSaved &= CreateReviewedAsset<URaftSimFeatureTuningEditorShellConfig>(
        TEXT("DA_FeatureTuningEditorShell"),
        [](URaftSimFeatureTuningEditorShellConfig* Asset)
        {
            Asset->RequiredPanelIds = {
                TEXT("flow_band_curve_editor"),
                TEXT("feature_gain_bounds"),
                TEXT("hole_stickiness_washout"),
                TEXT("eddy_lateral_wave_train_tuning"),
                TEXT("boulder_shelf_pin_release_tuning"),
                TEXT("visual_audio_only_tuning"),
                TEXT("manifest_recording_and_validation")};

            FRaftSimFeatureTuningShellControl Hole;
            Hole.ControlId = TEXT("hole_retention_gain");
            Hole.DisplayName = FText::FromString(TEXT("Hole Retention Gain"));
            Hole.FeatureKind = ERaftSimRiverFeatureTuningKind::Hole;
            Hole.Domain = ERaftSimRiverFeatureTuningDomain::SolverState;
            Hole.DefaultValue = 0.05f;
            Hole.bAffectsSolverState = true;
            Hole.bAffectsRaftCoupling = true;
            Hole.bGeoClawComparisonRequired = true;
            Hole.bConservationGuardRequired = true;

            FRaftSimFeatureTuningShellControl Foam;
            Foam.ControlId = TEXT("wave_train_foam_density");
            Foam.DisplayName = FText::FromString(TEXT("Wave Train Foam Density"));
            Foam.FeatureKind = ERaftSimRiverFeatureTuningKind::WaveTrain;
            Foam.Domain = ERaftSimRiverFeatureTuningDomain::VisualOnly;
            Foam.DefaultValue = 0.25f;
            Foam.bEnabledByDefault = true;
            Foam.bGeoClawComparisonRequired = false;
            Foam.bConservationGuardRequired = false;
            Asset->Controls = {Hole, Foam};
            Asset->ValidationMessages = {
                MakeValidationMessage(
                    TEXT("physics_edits_require_geoclaw"),
                    ERaftSimToolValidationSeverity::Warning,
                    TEXT("Changed physics-facing controls must be manifest-recorded, GeoClaw-compared, and conservation-guarded."),
                    TEXT("unreal/Content/RaftSim/River/feature_tuning_editor.json"),
                    false)};
        },
        OutSummary);

    bAllSaved &= CreateReviewedAsset<URaftSimToolValidationActionRegistry>(
        TEXT("DA_ToolValidationActions"),
        [](URaftSimToolValidationActionRegistry* Asset)
        {
            Asset->Actions = RaftSimEditorValidation::BuildDefaultValidationActions();
        },
        OutSummary);

    return bAllSaved;
}

bool FRaftSimEditorModule::CaptureToolEvidence(FString& OutSummary)
{
    OpenAllTools();
    PumpSlateForCapture(12);

    const FString CaptureRoot = GetCaptureRoot();
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);

    TArray<FString> CapturedFiles;
    bool bAllCaptured = true;

    for (const FRaftSimEditorToolDescriptor& Descriptor : GetToolDescriptors())
    {
        TSharedPtr<SDockTab> Tab = OpenedToolTabs.FindRef(Descriptor.ToolId).Pin();
        if (!Tab.IsValid())
        {
            Tab = FGlobalTabmanager::Get()->TryInvokeTab(GetTabIdForTool(Descriptor.ToolId));
        }

        if (!Tab.IsValid())
        {
            bAllCaptured = false;
            OutSummary += FString::Printf(TEXT("No tab available for %s\n"), *Descriptor.ToolId.ToString());
            continue;
        }

        TSharedPtr<SWidget> ToolPanel = OpenedToolPanels.FindRef(Descriptor.ToolId).Pin();
        const TSharedRef<SWidget> CaptureTarget = ToolPanel.IsValid() ? ToolPanel.ToSharedRef() : Tab.ToSharedRef();

        FString ScreenshotPath;
        const FString BaseFileName = FPaths::Combine(CaptureRoot, Descriptor.ToolId.ToString());
        const bool bCaptured = SaveWidgetScreenshot(CaptureTarget, BaseFileName, ScreenshotPath);
        bAllCaptured &= bCaptured;
        if (bCaptured)
        {
            FString CapturedPath = ScreenshotPath;
            FString RepoRootWithSlash = GetRepoRoot();
            if (!RepoRootWithSlash.EndsWith(TEXT("/")) && !RepoRootWithSlash.EndsWith(TEXT("\\")))
            {
                RepoRootWithSlash += TEXT("/");
            }
            FPaths::MakePathRelativeTo(CapturedPath, *RepoRootWithSlash);
            CapturedFiles.Add(CapturedPath);
            OutSummary += FString::Printf(TEXT("Captured %s\n"), *ScreenshotPath);
        }
        else
        {
            OutSummary += FString::Printf(TEXT("Failed to capture %s\n"), *Descriptor.ToolId.ToString());
        }
    }

    FString FilesJson;
    for (int32 Index = 0; Index < CapturedFiles.Num(); ++Index)
    {
        FilesJson += FString::Printf(
            TEXT("%s\"%s\""),
            Index == 0 ? TEXT("") : TEXT(", "),
            *CapturedFiles[Index].Replace(TEXT("\\"), TEXT("\\\\")));
    }

    const FString Manifest = FString::Printf(
        TEXT("{\n")
        TEXT("  \"schema\": \"raftsim.unreal.tool_capture_manifest.v1\",\n")
        TEXT("  \"capture_type\": \"slate_screenshot_sequence\",\n")
        TEXT("  \"video_capture_status\": \"not_recorded; automated Slate screenshots captured; video requires native recorder integration or macOS Screen Recording permission\",\n")
        TEXT("  \"captured_files\": [%s]\n")
        TEXT("}\n"),
        *FilesJson);
    FFileHelper::SaveStringToFile(Manifest, *FPaths::Combine(CaptureRoot, TEXT("tool_capture_manifest.json")));

    return bAllCaptured;
}

bool FRaftSimEditorModule::CreatePhotorealEnvironmentPreviewMaps(FString& OutSummary)
{
    FScopedPhotorealPreviewWorldGcLeakFatalOverride WorldGcLeakFatalOverride;

    const FString SourcePlanRelativePath = GetPhotorealRiverSourcePlanRelativePath();
    const FString SourcePlanAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), SourcePlanRelativePath));
    const FString ProceduralAssetPlanRelativePath = GetFirstPartyProceduralEnvironmentAssetPlanRelativePath();
    const FString ProceduralAssetPlanAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), ProceduralAssetPlanRelativePath));
    const FString ProceduralMaterialRecipePlanRelativePath = GetFirstPartyProceduralMaterialRecipePlanRelativePath();
    const FString ProceduralMaterialRecipePlanAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), ProceduralMaterialRecipePlanRelativePath));
    const FString MaterialTextureAtlasManifestRelativePath = GetFirstPartyMaterialTextureAtlasManifestRelativePath();
    const FString MaterialTextureAtlasManifestAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), MaterialTextureAtlasManifestRelativePath));
    const FString SourceConditionedMaterialMapManifestRelativePath = GetSourceConditionedMaterialMapManifestRelativePath();
    const FString SourceConditionedMaterialMapManifestAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), SourceConditionedMaterialMapManifestRelativePath));
    const FString ProductionDetailTextureManifestRelativePath = GetProductionDetailTextureManifestRelativePath();
    const FString ProductionDetailTextureManifestAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), ProductionDetailTextureManifestRelativePath));
    const FString MaterialInstanceCandidateManifestRelativePath = GetFirstPartyMaterialInstanceCandidateManifestRelativePath();
    const FString MaterialInstanceCandidateManifestAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), MaterialInstanceCandidateManifestRelativePath));
    const FString MaterialTextureAssetRootRelativePath = GetFirstPartyMaterialTextureAssetRootRelativePath();
    const FString SourceConditionedMaterialTextureAssetRootRelativePath =
        GetSourceConditionedMaterialTextureAssetRootRelativePath();
    const FString ProductionDetailTextureAssetRootRelativePath = GetProductionDetailTextureAssetRootRelativePath();
    const FString MaterialShaderParentRelativePath = GetFirstPartyAtlasSampleReviewMaterialRelativePath();
    const FString MaterialInstanceReviewAssetRootRelativePath = GetFirstPartyMaterialInstanceReviewAssetRootRelativePath();
    const FString GeospatialAttachmentLedgerRelativePath = GetProductionGeospatialAttachmentLedgerRelativePath();
    const FString GeospatialAttachmentLedgerAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), GeospatialAttachmentLedgerRelativePath));

    if (!FPaths::FileExists(SourcePlanAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing photoreal river source plan: %s\n"), *SourcePlanAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(ProceduralAssetPlanAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing first-party procedural environment asset plan: %s\n"), *ProceduralAssetPlanAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(ProceduralMaterialRecipePlanAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing first-party procedural material recipe plan: %s\n"), *ProceduralMaterialRecipePlanAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(MaterialTextureAtlasManifestAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing first-party material texture atlas manifest: %s\n"), *MaterialTextureAtlasManifestAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(SourceConditionedMaterialMapManifestAbsolutePath))
    {
        OutSummary += FString::Printf(
            TEXT("Missing source-conditioned material map manifest: %s\n"),
            *SourceConditionedMaterialMapManifestAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(ProductionDetailTextureManifestAbsolutePath))
    {
        OutSummary += FString::Printf(
            TEXT("Missing first-party production detail texture manifest: %s\n"),
            *ProductionDetailTextureManifestAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(MaterialInstanceCandidateManifestAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing first-party material instance candidate manifest: %s\n"), *MaterialInstanceCandidateManifestAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(GeospatialAttachmentLedgerAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing production geospatial attachment ledger: %s\n"), *GeospatialAttachmentLedgerAbsolutePath);
        return false;
    }

    OutSummary += FString::Printf(TEXT("Using photoreal river source plan: %s\n"), *SourcePlanRelativePath);
    OutSummary += FString::Printf(TEXT("Using first-party procedural environment asset plan: %s\n"), *ProceduralAssetPlanRelativePath);
    OutSummary += FString::Printf(TEXT("Using first-party procedural material recipe plan: %s\n"), *ProceduralMaterialRecipePlanRelativePath);
    OutSummary += FString::Printf(TEXT("Using first-party material texture atlas manifest: %s\n"), *MaterialTextureAtlasManifestRelativePath);
    OutSummary += FString::Printf(
        TEXT("Using source-conditioned material map manifest: %s\n"),
        *SourceConditionedMaterialMapManifestRelativePath);
    OutSummary += FString::Printf(
        TEXT("Using first-party production detail texture manifest: %s\n"),
        *ProductionDetailTextureManifestRelativePath);
    OutSummary += FString::Printf(TEXT("Using first-party material instance candidate manifest: %s\n"), *MaterialInstanceCandidateManifestRelativePath);
    OutSummary += FString::Printf(TEXT("Using first-party material texture asset root: %s\n"), *MaterialTextureAssetRootRelativePath);
    OutSummary += FString::Printf(
        TEXT("Using source-conditioned material texture asset root: %s\n"),
        *SourceConditionedMaterialTextureAssetRootRelativePath);
    OutSummary += FString::Printf(
        TEXT("Using first-party production detail texture asset root: %s\n"),
        *ProductionDetailTextureAssetRootRelativePath);
    OutSummary += FString::Printf(TEXT("Using first-party atlas sampler review material: %s\n"), *MaterialShaderParentRelativePath);
    OutSummary += FString::Printf(TEXT("Using first-party material instance review asset root: %s\n"), *MaterialInstanceReviewAssetRootRelativePath);
    OutSummary += FString::Printf(TEXT("Using production geospatial attachment ledger: %s\n"), *GeospatialAttachmentLedgerRelativePath);

    bool bAllSaved = CreateFirstPartyMaterialInstanceCandidateAssets(OutSummary);
    for (const FRaftSimEnvironmentPreviewSpec& Spec : GetEnvironmentPreviewSpecs())
    {
        OutSummary += FString::Printf(TEXT("Generating %s preview map.\n"), *Spec.DisplayName);
        bAllSaved &= BuildPreviewMapForSpec(Spec, OutSummary);
    }

    return bAllSaved;
}

bool FRaftSimEditorModule::CreateLandscapeImportCandidateMaps(FString& OutSummary)
{
    FScopedPhotorealPreviewWorldGcLeakFatalOverride WorldGcLeakFatalOverride;

    const FString CandidateCaptureRelativeRoot =
        TEXT("docs/environment-captures/photoreal_river_previews/landscape_candidates");
    const FString CandidateCaptureRoot = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(GetRepoRoot(), CandidateCaptureRelativeRoot));
    IFileManager::Get().MakeDirectory(*CandidateCaptureRoot, true);

    const FString SolverVisualizationManifestRelativePath =
        GetSolverVisualizationFieldManifestRelativePath();
    const FString SolverVisualizationManifestAbsolutePath = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(GetRepoRoot(), SolverVisualizationManifestRelativePath));
    if (!FPaths::FileExists(SolverVisualizationManifestAbsolutePath))
    {
        OutSummary += FString::Printf(
            TEXT("Missing validated solver visualization field manifest: %s\n"),
            *SolverVisualizationManifestAbsolutePath);
        return false;
    }
    OutSummary += FString::Printf(
        TEXT("Using validated solver visualization field manifest: %s\n"),
        *SolverVisualizationManifestRelativePath);
    OutSummary += FString::Printf(
        TEXT("Using solver visualization Texture2D asset root: %s\n"),
        *GetSolverVisualizationFieldTextureAssetRootRelativePath());

    FString EntriesJson;
    bool bAllSucceeded = CreateSolverVisualizationFieldTextureAssets(OutSummary);
    const TArray<FRaftSimLandscapeImportCandidateSpec> Candidates = GetLandscapeImportCandidateSpecs();
    for (int32 Index = 0; Index < Candidates.Num(); ++Index)
    {
        const FRaftSimLandscapeImportCandidateSpec& Candidate = Candidates[Index];
        const FString HeightfieldManifestAbsolutePath = FPaths::ConvertRelativePathToFull(
            FPaths::Combine(GetRepoRoot(), Candidate.HeightfieldManifestRelativePath));
        const FString ImportContractAbsolutePath = FPaths::ConvertRelativePathToFull(
            FPaths::Combine(GetRepoRoot(), Candidate.ImportContractRelativePath));
        const bool bSourceContractsPresent =
            FPaths::FileExists(HeightfieldManifestAbsolutePath) && FPaths::FileExists(ImportContractAbsolutePath);
        if (!bSourceContractsPresent)
        {
            OutSummary += FString::Printf(
                TEXT("Missing source Landscape manifest or import contract for %s.\n"),
                *Candidate.PreviewSpec.RiverId);
        }

        FRaftSimLandscapeImportCandidateResult Result;
        const bool bMapBuilt = bSourceContractsPresent &&
            BuildLandscapeImportCandidateMap(Candidate, Result, OutSummary);

        FString GuideSeatCapturePath = GetLandscapeCandidateCaptureRelativePath(
            Candidate,
            TEXT("guide_seat_downstream"));
        FString RiverEyeCapturePath = GetLandscapeCandidateCaptureRelativePath(
            Candidate,
            TEXT("river_eye_downstream"));
        const bool bGuideSeatCaptured = bMapBuilt && CapturePreviewImageForSpec(
            Candidate.PreviewSpec,
            CandidateCaptureRoot,
            GuideSeatCapturePath,
            TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
            TEXT("landscape_candidate_guide_seat_downstream"),
            TEXT("source Landscape candidate guide-seat downstream"),
            true,
            OutSummary);
        const bool bRiverEyeCaptured = bMapBuilt && CapturePreviewImageForSpec(
            Candidate.PreviewSpec,
            CandidateCaptureRoot,
            RiverEyeCapturePath,
            TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
            TEXT("landscape_candidate_river_eye_downstream"),
            TEXT("source Landscape candidate river-eye downstream"),
            true,
            OutSummary);
        FString SolverRapidCapturePath;
        bool bSolverRapidCaptured = true;
        if (Candidate.PreviewSpec.RiverId == TEXT("american_south_fork"))
        {
            SolverRapidCapturePath = GetLandscapeCandidateCaptureRelativePath(
                Candidate,
                TEXT("solver_rapid_river_eye_downstream"));
            bSolverRapidCaptured = bMapBuilt && CapturePreviewImageForSpec(
                Candidate.PreviewSpec,
                CandidateCaptureRoot,
                SolverRapidCapturePath,
                TEXT("RaftSim_SolverRapid_RiverEyeCaptureCamera"),
                TEXT("landscape_candidate_solver_rapid_river_eye_downstream"),
                TEXT("source Landscape candidate solver-rapid river-eye downstream"),
                true,
                OutSummary);
        }
        const bool bCandidateSucceeded =
            bSourceContractsPresent && bMapBuilt && bGuideSeatCaptured && bRiverEyeCaptured && bSolverRapidCaptured;
        bAllSucceeded &= bCandidateSucceeded;
        const FRaftSimLandscapeMaterialCandidateSettings MaterialSettings =
            GetLandscapeMaterialCandidateSettings(Candidate.PreviewSpec.RiverId);
        const FRaftSimLandscapeCandidateWaterSettings WaterSettings =
            GetLandscapeCandidateWaterSettings(Candidate.PreviewSpec.RiverId);
        const FRaftSimPhotographicCaptureSettings CaptureSettings =
            GetPhotographicCaptureSettings(Candidate.PreviewSpec.RiverId);
        const FRaftSimLandscapeCandidateFoliageSettings FoliageSettings =
            GetLandscapeCandidateFoliageSettings(Candidate.PreviewSpec.RiverId);
        const FString RiverAssetName =
            GetFirstPartyMaterialRiverAssetName(Candidate.PreviewSpec.RiverId);

        EntriesJson += FString::Printf(
            TEXT("%s    {\n")
            TEXT("      \"river_id\": \"%s\",\n")
            TEXT("      \"display_name\": \"%s\",\n")
            TEXT("      \"source_heightfield\": \"%s\",\n")
            TEXT("      \"source_heightfield_manifest\": \"%s\",\n")
            TEXT("      \"unreal_import_contract\": \"%s\",\n")
            TEXT("      \"map_package\": \"%s\",\n")
            TEXT("      \"guide_seat_capture\": \"%s\",\n")
            TEXT("      \"river_eye_capture\": \"%s\",\n")
            TEXT("      \"solver_rapid_river_eye_capture\": \"%s\",\n")
            TEXT("      \"solver_rapid_capture_status\": \"%s\",\n")
            TEXT("      \"status\": \"%s\",\n")
            TEXT("      \"photographic_capture_status\": \"river_specific_recorded_capture_photometry_no_camera_film_grain\",\n")
            TEXT("      \"photographic_sun_intensity\": %.6f,\n")
            TEXT("      \"photographic_skylight_intensity\": %.6f,\n")
            TEXT("      \"photographic_fog_density\": %.6f,\n")
            TEXT("      \"photographic_exposure_bias\": %.6f,\n")
            TEXT("      \"photographic_saturation\": %.6f,\n")
            TEXT("      \"photographic_contrast\": %.6f,\n")
            TEXT("      \"photographic_sharpen\": %.6f,\n")
            TEXT("      \"photographic_vignette\": %.6f,\n")
            TEXT("      \"photographic_film_grain_intensity\": %.6f,\n")
            TEXT("      \"heightfield_format\": \"16-bit grayscale PNG\",\n")
            TEXT("      \"heightfield_width_px\": 1009,\n")
            TEXT("      \"heightfield_height_px\": 1009,\n")
            TEXT("      \"component_count_x\": 16,\n")
            TEXT("      \"component_count_y\": 16,\n")
            TEXT("      \"component_count_total\": 256,\n")
            TEXT("      \"num_subsections\": 1,\n")
            TEXT("      \"subsection_size_quads\": 63,\n")
            TEXT("      \"source_height_min_uint16\": %u,\n")
            TEXT("      \"source_height_max_uint16\": %u,\n")
            TEXT("      \"preview_channel_floor_uint16\": %u,\n")
            TEXT("      \"preview_channel_modified_sample_count\": %d,\n")
            TEXT("      \"channel_burn_policy\": \"preview_only_analytic_channel_burn_for_landscape_import_validation\",\n")
            TEXT("      \"channel_burn_promotion_status\": \"not_solver_geometry_not_geospatially_approved_not_for_gameplay\",\n")
            TEXT("      \"landscape_location_cm\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"landscape_scale\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"horizontal_span_x_cm\": %.3f,\n")
            TEXT("      \"horizontal_span_y_cm\": %.3f,\n")
            TEXT("      \"target_relief_cm\": %.3f,\n")
            TEXT("      \"landscape_material_status\": \"source_conditioned_macro_zones_plus_first_party_close_range_detail_review_candidate\",\n")
            TEXT("      \"landscape_material_texture_asset_count\": 7,\n")
            TEXT("      \"landscape_material_zone_parameter\": \"SourceConditionedMaterialZones\",\n")
            TEXT("      \"landscape_material_zone_semantics\": \"rgb_r_terrain_wet_bank_g_vegetation_b_visible_water\",\n")
            TEXT("      \"landscape_material_macro_mapping_scale\": %.3f,\n")
            TEXT("      \"landscape_material_detail_mapping_scale\": %.3f,\n")
            TEXT("      \"landscape_material_detail_albedo_weight\": %.3f,\n")
            TEXT("      \"landscape_material_detail_normal_weight\": %.3f,\n")
            TEXT("      \"landscape_material_detail_surface_response_weight\": %.3f,\n")
            TEXT("      \"landscape_material_emissive_fill_scale\": %.3f,\n")
            TEXT("      \"landscape_material_specular_level\": %.3f,\n")
            TEXT("      \"landscape_material_riverbed_blend_weight\": %.3f,\n")
            TEXT("      \"landscape_material_wet_bank_blend_weight\": %.3f,\n")
            TEXT("      \"landscape_material_riverbed_roughness\": %.3f,\n")
            TEXT("      \"landscape_material_riverbed_color_scale\": [%.3f, %.3f, %.3f],\n")
            TEXT("      \"landscape_material_wet_bank_color_scale\": [%.3f, %.3f, %.3f],\n")
            TEXT("      \"landscape_material_zone_conditioning_policy\": \"source_visible_water_darkens_submerged_riverbed_and_feathered_source_water_edge_conditions_wet_bank_without_changing_landscape_geometry_or_solver_authority\",\n")
            TEXT("      \"landscape_material_promotion_status\": \"review_only_not_lifelike_not_gameplay_promoted\",\n")
            TEXT("      \"landscape_dressing_status\": \"%s\",\n")
            TEXT("      \"landscape_dressing_asset_count\": %d,\n")
            TEXT("      \"landscape_dressing_boulder_asset\": \"first_party_8_ring_20_segment_irregular_procedural_mesh_with_river_specific_lit_color\",\n")
            TEXT("      \"landscape_dressing_broadleaf_assets\": [\"/ProceduralVegetationEditor/SampleAssets/StarterContent/DeciduousTree_01/Instances/Leaf_Twig_01\", \"/ProceduralVegetationEditor/SampleAssets/StarterContent/DeciduousTree_01/Instances/Leaf_Twig_03\"],\n")
            TEXT("      \"landscape_dressing_conifer_asset\": \"/ProceduralVegetationEditor/SampleAssets/StarterContent/ConiferTree_01/Instances/Conifer_Twig_01\",\n")
            TEXT("      \"landscape_dressing_trunk_asset\": \"/Engine/BasicShapes/Cylinder\",\n")
            TEXT("      \"landscape_dressing_instance_implementation\": \"pve_hierarchical_instancing_plus_dense_irregular_procedural_boulder_meshes\",\n")
            TEXT("      \"landscape_dressing_boulder_instance_count\": %d,\n")
            TEXT("      \"landscape_dressing_foliage_instance_count\": %d,\n")
            TEXT("      \"landscape_dressing_trunk_instance_count\": %d,\n")
            TEXT("      \"landscape_dressing_source_mask_status\": \"%s\",\n")
            TEXT("      \"landscape_dressing_foliage_material_status\": \"%s\",\n")
            TEXT("      \"landscape_dressing_foliage_material_asset_count\": %d,\n")
            TEXT("      \"landscape_dressing_foliage_material_bound_slot_count\": %d,\n")
            TEXT("      \"landscape_dressing_broadleaf_material_asset\": \"/Game/RaftSim/Materials/LandscapeCandidates/MI_RaftSim_%s_Broadleaf_BiomeFoliageCandidate\",\n")
            TEXT("      \"landscape_dressing_conifer_material_asset\": \"/Game/RaftSim/Materials/LandscapeCandidates/MI_RaftSim_%s_Conifer_BiomeFoliageCandidate\",\n")
            TEXT("      \"landscape_dressing_broadleaf_front_tint\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"landscape_dressing_broadleaf_back_tint\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"landscape_dressing_broadleaf_transmission_tint\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"landscape_dressing_conifer_front_tint\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"landscape_dressing_conifer_back_tint\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"landscape_dressing_conifer_transmission_tint\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"landscape_dressing_foliage_roughness_strength\": %.6f,\n")
            TEXT("      \"landscape_dressing_foliage_normal_strength\": %.6f,\n")
            TEXT("      \"procedural_vegetation_editor_plugin_enabled\": true,\n")
            TEXT("      \"nanite_foliage_project_setting_enabled\": true,\n")
            TEXT("      \"landscape_dressing_boulder_mesh_nanite_enabled\": %s,\n")
            TEXT("      \"landscape_dressing_broadleaf_mesh_nanite_enabled\": %s,\n")
            TEXT("      \"landscape_dressing_conifer_mesh_nanite_enabled\": %s,\n")
            TEXT("      \"landscape_dressing_promotion_status\": \"pve_engine_sample_and_first_party_procedural_rock_evaluation_only_requires_exported_species_production_rock_asset_guide_and_performance_review\",\n")
            TEXT("      \"water_material_status\": \"%s\",\n")
            TEXT("      \"water_material_asset\": \"%s\",\n")
            TEXT("      \"water_material_parent\": \"/Game/RaftSim/Materials/LandscapeCandidates/M_RaftSim_SolverSurfaceWaterCandidate\",\n")
            TEXT("      \"water_shading_model\": \"DefaultLit\",\n")
            TEXT("      \"water_blend_mode\": \"Opaque\",\n")
            TEXT("      \"water_custom_output\": \"none_surface_only_solver_conditioned_shading\",\n")
            TEXT("      \"water_volume_parameter_status\": \"inactive_single_layer_evaluation_values_retained_in_manifest_only\",\n")
            TEXT("      \"water_normal_source\": \"river_specific_first_party_normal_atlas_plus_optional_validated_cpp_solver_macro_normal\",\n")
            TEXT("      \"water_solver_visualization_field_status\": \"%s\",\n")
            TEXT("      \"water_solver_visualization_field_manifest\": \"%s\",\n")
            TEXT("      \"water_solver_visualization_field_texture_count\": %d,\n")
            TEXT("      \"water_solver_visualization_field_feature_strength_scale\": %s,\n")
            TEXT("      \"water_solver_visualization_field_enable\": %.6f,\n")
            TEXT("      \"water_solver_macro_normal_weight\": %.6f,\n")
            TEXT("      \"water_solver_depth_color_weight\": %.6f,\n")
            TEXT("      \"water_solver_field_roughness_weight\": %.6f,\n")
            TEXT("      \"water_solver_froude_aeration_weight\": %.6f,\n")
            TEXT("      \"water_solver_speed_visual_gain\": %.6f,\n")
            TEXT("      \"water_solver_froude_visual_gain\": %.6f,\n")
            TEXT("      \"water_solver_surface_relief_scale\": %.6f,\n")
            TEXT("      \"water_solver_surface_relief_cap_cm\": %.6f,\n")
            TEXT("      \"water_solver_analytic_displacement_residual_scale\": %.6f,\n")
            TEXT("      \"water_solver_render_geometry_collision_enabled\": false,\n")
            TEXT("      \"water_solver_foam_status\": \"%s\",\n")
            TEXT("      \"water_solver_foam_material\": \"/Game/RaftSim/Materials/LandscapeCandidates/M_RaftSim_SolverFieldFoamCandidate\",\n")
            TEXT("      \"water_solver_foam_max_opacity\": %.6f,\n")
            TEXT("      \"water_solver_foam_surface_offset_cm\": %.6f,\n")
            TEXT("      \"water_solver_visualization_authority\": \"review_only_noncolliding_render_geometry_and_material_derivative_does_not_change_solver_collision_raft_forces_or_feature_forcing\",\n")
            TEXT("      \"water_material_bound_component_count\": %d,\n")
            TEXT("      \"water_base_color_scale\": %.6f,\n")
            TEXT("      \"water_surface_tint\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"water_vertex_tint_weight\": %.6f,\n")
            TEXT("      \"water_emissive_fill_scale\": %.6f,\n")
            TEXT("      \"water_reflection_fill_intensity\": %.6f,\n")
            TEXT("      \"water_reflection_tint\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"water_roughness\": %.6f,\n")
            TEXT("      \"water_specular\": %.6f,\n")
            TEXT("      \"water_surface_opacity\": %.6f,\n")
            TEXT("      \"water_normal_intensity\": %.6f,\n")
            TEXT("      \"water_normal_atlas_sampling_policy\": \"half_period_dual_sample_crossfade_prevents_frac_tile_boundaries\",\n")
            TEXT("      \"water_normal_atlas_phase_offset\": 0.500000,\n")
            TEXT("      \"water_inactive_single_layer_refraction_ior\": %.6f,\n")
            TEXT("      \"water_inactive_single_layer_phase_g\": %.6f,\n")
            TEXT("      \"water_inactive_single_layer_scattering_coefficients_per_cm\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"water_inactive_single_layer_absorption_coefficients_per_cm\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"water_inactive_single_layer_color_scale_behind_water\": [%.6f, %.6f, %.6f],\n")
            TEXT("      \"water_render_width_scale\": %.6f,\n")
            TEXT("      \"water_render_normal_up_blend\": %.6f,\n")
            TEXT("      \"water_render_displacement_scale\": %.6f,\n")
            TEXT("      \"water_near_camera_synthetic_wedge_fill_enabled\": false,\n")
            TEXT("      \"water_near_camera_synthetic_wedge_fill_policy\": \"disabled_for_solver_surface_water_candidates_legacy_diagnostic_branch_retained\",\n")
            TEXT("      \"water_geometry_authority\": \"custom_cpp_solver_informed_ribbon_geometry_and_vertex_flow_cues_no_visual_forcing_authority\",\n")
            TEXT("      \"waterbody_dependency\": \"none_default_lit_solver_surface_runs_on_generated_procedural_mesh_ribbon\",\n")
            TEXT("      \"water_reflection_capture_policy\": \"default_lit_surface_uses_movable_skylight_runtime_corridor_sphere_capture_screen_space_reflections_and_bounded_fresnel_sky_fill\",\n")
            TEXT("      \"water_material_promotion_status\": \"review_only_requires_visual_guide_solver_hazard_and_performance_validation\",\n")
            TEXT("      \"material_usage_contract\": \"nanite_and_static_lighting\",\n")
            TEXT("      \"material_bound_component_count\": %d,\n")
            TEXT("      \"material_binding_status\": \"%s\",\n")
            TEXT("      \"nanite_enabled\": true,\n")
            TEXT("      \"nanite_component_count\": %d,\n")
            TEXT("      \"nanite_material_slot_count\": %d,\n")
            TEXT("      \"nanite_material_bound_slot_count\": %d,\n")
            TEXT("      \"nanite_material_audit_error_count\": %d,\n")
            TEXT("      \"nanite_representation_status\": \"%s\",\n")
            TEXT("      \"capture_shader_warmup_policy\": \"render_then_finish_compilation_recreate_landscape_components_render_again\",\n")
            TEXT("      \"promotion_status\": \"review_gated_isolated_candidate_not_enabled_for_gameplay_or_active_previews\"\n")
            TEXT("    }"),
            Index == 0 ? TEXT("") : TEXT(",\n"),
            *EscapeRaftSimJsonString(Candidate.PreviewSpec.RiverId),
            *EscapeRaftSimJsonString(Candidate.PreviewSpec.DisplayName),
            *EscapeRaftSimJsonString(Candidate.HeightfieldRelativePath),
            *EscapeRaftSimJsonString(Candidate.HeightfieldManifestRelativePath),
            *EscapeRaftSimJsonString(Candidate.ImportContractRelativePath),
            *EscapeRaftSimJsonString(Candidate.MapPackagePath),
            *EscapeRaftSimJsonString(GuideSeatCapturePath),
            *EscapeRaftSimJsonString(RiverEyeCapturePath),
            *EscapeRaftSimJsonString(SolverRapidCapturePath),
            Candidate.PreviewSpec.RiverId == TEXT("american_south_fork")
                ? (bSolverRapidCaptured
                       ? TEXT("captured_at_validated_median_field_high_froude_approach")
                       : TEXT("solver_rapid_capture_failed"))
                : TEXT("not_available_without_river_specific_validated_solver_field"),
            bCandidateSucceeded ? TEXT("captured_source_landscape_import_candidate") : TEXT("candidate_generation_or_capture_failed"),
            CaptureSettings.SunIntensity,
            CaptureSettings.SkyLightIntensity,
            CaptureSettings.FogDensity,
            CaptureSettings.ExposureBias,
            CaptureSettings.Saturation,
            CaptureSettings.Contrast,
            CaptureSettings.Sharpen,
            CaptureSettings.Vignette,
            CaptureSettings.FilmGrainIntensity,
            static_cast<uint32>(Result.SourceHeightMin),
            static_cast<uint32>(Result.SourceHeightMax),
            static_cast<uint32>(Result.ChannelFloor),
            Result.ChannelModifiedSampleCount,
            Result.LandscapeLocation.X,
            Result.LandscapeLocation.Y,
            Result.LandscapeLocation.Z,
            Result.LandscapeScale.X,
            Result.LandscapeScale.Y,
            Result.LandscapeScale.Z,
            Candidate.HorizontalSpanXCm,
            Candidate.HorizontalSpanYCm,
            Candidate.TargetReliefCm,
            MaterialSettings.MacroMappingScale,
            MaterialSettings.DetailMappingScale,
            MaterialSettings.DetailAlbedoWeight,
            MaterialSettings.DetailNormalWeight,
            MaterialSettings.DetailSurfaceResponseWeight,
            MaterialSettings.EmissiveFillScale,
            MaterialSettings.SpecularLevel,
            MaterialSettings.RiverbedBlendWeight,
            MaterialSettings.WetBankBlendWeight,
            MaterialSettings.RiverbedRoughness,
            MaterialSettings.RiverbedColorScale.R,
            MaterialSettings.RiverbedColorScale.G,
            MaterialSettings.RiverbedColorScale.B,
            MaterialSettings.WetBankColorScale.R,
            MaterialSettings.WetBankColorScale.G,
            MaterialSettings.WetBankColorScale.B,
            Result.bDressingValidated
                ? TEXT("source_mask_placed_pve_foliage_and_dense_irregular_rock_evaluation_captured")
                : TEXT("dressing_generation_or_validation_failed"),
            Result.DressingAssetCount,
            Result.DressingBoulderInstanceCount,
            Result.DressingFoliageInstanceCount,
            Result.DressingTrunkInstanceCount,
            Result.bDressingSourceMasksLoaded
                ? TEXT("water_and_vegetation_masks_loaded_and_used_for_candidate_selection")
                : TEXT("required_source_masks_missing"),
            Result.bDressingFoliageMaterialsValidated
                ? TEXT("river_specific_texture_preserving_two_sided_foliage_material_instances_bound")
                : TEXT("foliage_material_generation_or_binding_failed"),
            Result.DressingFoliageMaterialAssetCount,
            Result.DressingFoliageMaterialBoundSlotCount,
            *RiverAssetName,
            *RiverAssetName,
            FoliageSettings.BroadleafFrontTint.R,
            FoliageSettings.BroadleafFrontTint.G,
            FoliageSettings.BroadleafFrontTint.B,
            FoliageSettings.BroadleafBackTint.R,
            FoliageSettings.BroadleafBackTint.G,
            FoliageSettings.BroadleafBackTint.B,
            FoliageSettings.BroadleafTransmissionTint.R,
            FoliageSettings.BroadleafTransmissionTint.G,
            FoliageSettings.BroadleafTransmissionTint.B,
            FoliageSettings.ConiferFrontTint.R,
            FoliageSettings.ConiferFrontTint.G,
            FoliageSettings.ConiferFrontTint.B,
            FoliageSettings.ConiferBackTint.R,
            FoliageSettings.ConiferBackTint.G,
            FoliageSettings.ConiferBackTint.B,
            FoliageSettings.ConiferTransmissionTint.R,
            FoliageSettings.ConiferTransmissionTint.G,
            FoliageSettings.ConiferTransmissionTint.B,
            FoliageSettings.RoughnessStrength,
            FoliageSettings.NormalStrength,
            Result.bDressingBoulderMeshNaniteEnabled ? TEXT("true") : TEXT("false"),
            Result.bDressingBroadleafMeshNaniteEnabled ? TEXT("true") : TEXT("false"),
            Result.bDressingConiferMeshNaniteEnabled ? TEXT("true") : TEXT("false"),
            Result.bSolverSurfaceWaterMaterialBound
                ? TEXT("solver_surface_default_lit_candidate_bound_and_captured")
                : TEXT("solver_surface_water_generation_or_binding_failed"),
            *EscapeRaftSimJsonString(Result.WaterMaterialPath),
            Candidate.PreviewSpec.RiverId == TEXT("american_south_fork")
                ? TEXT("validated_cpp_solver_visualization_fields_bound_review_only")
                : TEXT("not_available_for_river_no_cross_river_field_reuse"),
            *EscapeRaftSimJsonString(GetSolverVisualizationFieldManifestRelativePath()),
            Candidate.PreviewSpec.RiverId == TEXT("american_south_fork") ? 2 : 0,
            Candidate.PreviewSpec.RiverId == TEXT("american_south_fork") ? TEXT("0") : TEXT("null"),
            WaterSettings.SolverFieldEnable,
            WaterSettings.SolverMacroNormalWeight,
            WaterSettings.SolverDepthColorWeight,
            WaterSettings.SolverFieldRoughnessWeight,
            WaterSettings.SolverFroudeAerationWeight,
            WaterSettings.SolverSpeedVisualGain,
            WaterSettings.SolverFroudeVisualGain,
            WaterSettings.SolverSurfaceReliefScale,
            WaterSettings.SolverSurfaceReliefScale * 400.0f,
            Candidate.PreviewSpec.RiverId == TEXT("american_south_fork") ? 0.42f : 1.0f,
            Candidate.PreviewSpec.RiverId == TEXT("american_south_fork")
                ? TEXT("validated_speed_froude_masked_noncolliding_translucent_surface_bound")
                : TEXT("not_available_without_river_specific_validated_solver_field"),
            Candidate.PreviewSpec.RiverId == TEXT("american_south_fork") ? 0.72f : 0.0f,
            Candidate.PreviewSpec.RiverId == TEXT("american_south_fork") ? 1.4f : 0.0f,
            Result.WaterMaterialBoundComponentCount,
            WaterSettings.BaseColorScale,
            WaterSettings.SurfaceTint.R,
            WaterSettings.SurfaceTint.G,
            WaterSettings.SurfaceTint.B,
            WaterSettings.VertexTintWeight,
            WaterSettings.EmissiveFillScale,
            WaterSettings.ReflectionFillIntensity,
            WaterSettings.ReflectionTint.R,
            WaterSettings.ReflectionTint.G,
            WaterSettings.ReflectionTint.B,
            WaterSettings.Roughness,
            WaterSettings.Specular,
            1.0f,
            WaterSettings.NormalIntensity,
            WaterSettings.RefractionIor,
            WaterSettings.PhaseG,
            WaterSettings.ScatteringCoefficients.R,
            WaterSettings.ScatteringCoefficients.G,
            WaterSettings.ScatteringCoefficients.B,
            WaterSettings.AbsorptionCoefficients.R,
            WaterSettings.AbsorptionCoefficients.G,
            WaterSettings.AbsorptionCoefficients.B,
            WaterSettings.ColorScaleBehindWater.R,
            WaterSettings.ColorScaleBehindWater.G,
            WaterSettings.ColorScaleBehindWater.B,
            WaterSettings.RenderWidthScale,
            WaterSettings.RenderNormalUpBlend,
            WaterSettings.RenderDisplacementScale,
            Result.MaterialBoundComponentCount,
            Result.bMaterialBindingsValidated ? TEXT("all_source_components_bound") : TEXT("source_component_binding_failed"),
            Result.NaniteComponentCount,
            Result.NaniteMaterialSlotCount,
            Result.NaniteMaterialBoundSlotCount,
            Result.NaniteMaterialAuditErrorCount,
            Result.bNaniteRepresentationBuilt ? TEXT("enabled_and_built_up_to_date") : TEXT("enabled_candidate_build_failed_or_stale"));
    }

    const FString Manifest = FString::Printf(
        TEXT("{\n")
        TEXT("  \"schema\": \"raftsim.unreal.landscape_import_candidate_manifest.v1\",\n")
        TEXT("  \"capture_type\": \"isolated_source_landscape_import_geometry_review\",\n")
        TEXT("  \"status\": \"%s\",\n")
        TEXT("  \"canonical_importer\": \"Unreal LandscapeEditor PNG heightmap file format\",\n")
        TEXT("  \"candidate_policy\": \"Source DEM values remain authoritative outside a bounded preview-only analytic channel burn; candidates cannot replace gameplay or active preview terrain until CRS, vertical datum, hydrologic conditioning, guide, solver, capture, Nanite-build, and performance gates pass.\",\n")
        TEXT("  \"candidates\": [\n")
        TEXT("%s\n")
        TEXT("  ]\n")
        TEXT("}\n"),
        bAllSucceeded ? TEXT("three_source_landscape_candidates_captured_review_gated") : TEXT("one_or_more_landscape_candidates_failed"),
        *EntriesJson);
    const FString ManifestPath = FPaths::Combine(CandidateCaptureRoot, TEXT("landscape_candidate_manifest.json"));
    const bool bManifestSaved = FFileHelper::SaveStringToFile(Manifest, *ManifestPath);
    OutSummary += FString::Printf(
        TEXT("%s source Landscape candidate manifest -> %s\n"),
        bManifestSaved ? TEXT("Saved") : TEXT("Failed"),
        *ManifestPath);
    return bAllSucceeded && bManifestSaved;
}

bool FRaftSimEditorModule::CapturePhotorealEnvironmentPreviews(FString& OutSummary)
{
    FScopedPhotorealPreviewWorldGcLeakFatalOverride WorldGcLeakFatalOverride;

    const FString CaptureRoot = GetEnvironmentCaptureRoot();
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);
    const FString SourcePlanRelativePath = GetPhotorealRiverSourcePlanRelativePath();
    const FString ProceduralAssetPlanRelativePath = GetFirstPartyProceduralEnvironmentAssetPlanRelativePath();
    const FString ProceduralAssetPlanAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), ProceduralAssetPlanRelativePath));
    const FString ProceduralMaterialRecipePlanRelativePath = GetFirstPartyProceduralMaterialRecipePlanRelativePath();
    const FString ProceduralMaterialRecipePlanAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), ProceduralMaterialRecipePlanRelativePath));
    const FString MaterialTextureAtlasManifestRelativePath = GetFirstPartyMaterialTextureAtlasManifestRelativePath();
    const FString MaterialTextureAtlasManifestAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), MaterialTextureAtlasManifestRelativePath));
    const FString SourceConditionedMaterialMapManifestRelativePath = GetSourceConditionedMaterialMapManifestRelativePath();
    const FString SourceConditionedMaterialMapManifestAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), SourceConditionedMaterialMapManifestRelativePath));
    const FString ProductionDetailTextureManifestRelativePath = GetProductionDetailTextureManifestRelativePath();
    const FString ProductionDetailTextureManifestAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), ProductionDetailTextureManifestRelativePath));
    const FString MaterialInstanceCandidateManifestRelativePath = GetFirstPartyMaterialInstanceCandidateManifestRelativePath();
    const FString MaterialInstanceCandidateManifestAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), MaterialInstanceCandidateManifestRelativePath));
    const FString MaterialTextureAssetRootRelativePath = GetFirstPartyMaterialTextureAssetRootRelativePath();
    const FString SourceConditionedMaterialTextureAssetRootRelativePath =
        GetSourceConditionedMaterialTextureAssetRootRelativePath();
    const FString ProductionDetailTextureAssetRootRelativePath = GetProductionDetailTextureAssetRootRelativePath();
    const FString MaterialShaderParentRelativePath = GetFirstPartyAtlasSampleReviewMaterialRelativePath();
    const FString MaterialInstanceReviewAssetRootRelativePath = GetFirstPartyMaterialInstanceReviewAssetRootRelativePath();
    const FString GeospatialAttachmentLedgerRelativePath = GetProductionGeospatialAttachmentLedgerRelativePath();
    const FString GeospatialAttachmentLedgerAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), GeospatialAttachmentLedgerRelativePath));

    if (!FPaths::FileExists(ProceduralAssetPlanAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing first-party procedural environment asset plan for capture: %s\n"), *ProceduralAssetPlanAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(ProceduralMaterialRecipePlanAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing first-party procedural material recipe plan for capture: %s\n"), *ProceduralMaterialRecipePlanAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(MaterialTextureAtlasManifestAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing first-party material texture atlas manifest for capture: %s\n"), *MaterialTextureAtlasManifestAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(SourceConditionedMaterialMapManifestAbsolutePath))
    {
        OutSummary += FString::Printf(
            TEXT("Missing source-conditioned material map manifest for capture: %s\n"),
            *SourceConditionedMaterialMapManifestAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(ProductionDetailTextureManifestAbsolutePath))
    {
        OutSummary += FString::Printf(
            TEXT("Missing first-party production detail texture manifest for capture: %s\n"),
            *ProductionDetailTextureManifestAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(MaterialInstanceCandidateManifestAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing first-party material instance candidate manifest for capture: %s\n"), *MaterialInstanceCandidateManifestAbsolutePath);
        return false;
    }
    if (!FPaths::FileExists(GeospatialAttachmentLedgerAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing production geospatial attachment ledger for capture: %s\n"), *GeospatialAttachmentLedgerAbsolutePath);
        return false;
    }
    OutSummary += FString::Printf(TEXT("Using first-party material texture atlas manifest: %s\n"), *MaterialTextureAtlasManifestRelativePath);
    OutSummary += FString::Printf(
        TEXT("Using source-conditioned material map manifest: %s\n"),
        *SourceConditionedMaterialMapManifestRelativePath);
    OutSummary += FString::Printf(
        TEXT("Using first-party production detail texture manifest: %s\n"),
        *ProductionDetailTextureManifestRelativePath);
    OutSummary += FString::Printf(TEXT("Using first-party material instance candidate manifest: %s\n"), *MaterialInstanceCandidateManifestRelativePath);
    OutSummary += FString::Printf(TEXT("Using first-party material texture asset root: %s\n"), *MaterialTextureAssetRootRelativePath);
    OutSummary += FString::Printf(
        TEXT("Using source-conditioned material texture asset root: %s\n"),
        *SourceConditionedMaterialTextureAssetRootRelativePath);
    OutSummary += FString::Printf(
        TEXT("Using first-party production detail texture asset root: %s\n"),
        *ProductionDetailTextureAssetRootRelativePath);
    OutSummary += FString::Printf(TEXT("Using first-party atlas sampler review material: %s\n"), *MaterialShaderParentRelativePath);
    OutSummary += FString::Printf(TEXT("Using first-party material instance review asset root: %s\n"), *MaterialInstanceReviewAssetRootRelativePath);
    OutSummary += FString::Printf(TEXT("Using production geospatial attachment ledger: %s\n"), *GeospatialAttachmentLedgerRelativePath);

    FString EntriesJson;
    bool bAllCaptured = true;
    const bool bCullReviewOnlyForegroundRaftForGuideSeatCaptures = true;
    const TArray<FRaftSimEnvironmentPreviewSpec> Specs = GetEnvironmentPreviewSpecs();
    for (int32 Index = 0; Index < Specs.Num(); ++Index)
    {
        const FRaftSimEnvironmentPreviewSpec& Spec = Specs[Index];
        const FRaftSimPreviewWaterMaterialResponse WaterResponse = GetPreviewWaterMaterialResponse(Spec.RiverId);
        FString GuideSeatCapturePath = GetPreviewCaptureRelativePath(Spec, TEXT("guide_seat_downstream"));
        FString RiverEyeCapturePath = GetPreviewCaptureRelativePath(Spec, TEXT("river_eye_downstream"));
        const bool bGuideSeatCaptured = CapturePreviewImageForSpec(
            Spec,
            CaptureRoot,
            GuideSeatCapturePath,
            TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
            TEXT("guide_seat_downstream"),
            TEXT("guide-seat downstream"),
            bCullReviewOnlyForegroundRaftForGuideSeatCaptures,
            OutSummary);
        const bool bRiverEyeCaptured = CapturePreviewImageForSpec(
            Spec,
            CaptureRoot,
            RiverEyeCapturePath,
            TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
            TEXT("river_eye_downstream"),
            TEXT("river-eye downstream"),
            true,
            OutSummary);
        bAllCaptured &= bGuideSeatCaptured && bRiverEyeCaptured;
        const FString FlowReferenceDischargeJson = Spec.FlowReferenceDischargeCfs >= 0.0f
            ? FString::Printf(TEXT("%.1f"), Spec.FlowReferenceDischargeCfs)
            : FString(TEXT("null"));

        EntriesJson += FString::Printf(
            TEXT("%s    {\n")
            TEXT("      \"river_id\": \"%s\",\n")
            TEXT("      \"display_name\": \"%s\",\n")
            TEXT("      \"map_package\": \"%s\",\n")
            TEXT("      \"source_manifest\": \"%s\",\n")
            TEXT("      \"flow_band_id\": \"%s\",\n")
            TEXT("      \"flow_band_display_name\": \"%s\",\n")
            TEXT("      \"flow_band_source\": \"%s\",\n")
            TEXT("      \"flow_reference_discharge_cfs\": %s,\n")
            TEXT("      \"flow_visual_width_scale\": %.3f,\n")
            TEXT("      \"flow_visual_foam_scale\": %.3f,\n")
            TEXT("      \"flow_visual_wet_bank_scale\": %.3f,\n")
            TEXT("      \"flow_visual_current_cue_scale\": %.3f,\n")
            TEXT("      \"flow_visual_water_level_offset_cm\": %.3f,\n")
            TEXT("      \"flow_visual_note\": \"%s\",\n")
            TEXT("      \"capture\": \"%s\",\n")
            TEXT("      \"guide_seat_capture\": \"%s\",\n")
            TEXT("      \"river_eye_capture\": \"%s\",\n")
            TEXT("      \"status\": \"%s\",\n")
            TEXT("      \"aerial_drape_image\": \"%s\",\n")
            TEXT("      \"terrain_relief_image\": \"%s\",\n")
            TEXT("      \"heightfield_preview_image\": \"%s\",\n")
            TEXT("      \"source_terrain_macro_amplitude_cm\": %.3f,\n")
            TEXT("      \"source_terrain_local_relief_amplitude_cm\": %.3f,\n")
            TEXT("      \"source_terrain_seam_feather_uv\": %.5f,\n")
            TEXT("      \"source_terrain_normal_softening_blend\": %.3f,\n")
            TEXT("      \"water_material_emissive_fill_scale\": %.3f,\n")
            TEXT("      \"water_material_roughness_scale\": %.3f,\n")
            TEXT("      \"water_material_roughness_floor\": %.3f,\n")
            TEXT("      \"water_material_specular_level\": %.3f,\n")
            TEXT("      \"water_material_normal_intensity\": %.3f,\n")
            TEXT("      \"water_mesh_normal_up_blend\": %.3f,\n")
            TEXT("      \"water_mask_image\": \"%s\",\n")
            TEXT("      \"vegetation_mask_image\": \"%s\",\n")
            TEXT("      \"source_conditioned_macro_albedo_image\": \"%s\",\n")
            TEXT("      \"source_conditioned_material_zones_image\": \"%s\",\n")
            TEXT("      \"source_conditioned_ao_roughness_height_image\": \"%s\",\n")
            TEXT("      \"source_conditioned_normal_detail_image\": \"%s\",\n")
            TEXT("      \"terrain_detail_albedo_image\": \"%s\",\n")
            TEXT("      \"terrain_detail_normal_image\": \"%s\",\n")
            TEXT("      \"terrain_detail_ao_roughness_height_image\": \"%s\",\n")
            TEXT("      \"elevation_sample\": \"%s\",\n")
            TEXT("      \"fidelity_note\": \"%s\",\n")
            TEXT("      \"first_party_material_instance_scene_assignment_status\": \"%s\"\n")
            TEXT("    }"),
            Index == 0 ? TEXT("") : TEXT(",\n"),
            *EscapeRaftSimJsonString(Spec.RiverId),
            *EscapeRaftSimJsonString(Spec.DisplayName),
            *EscapeRaftSimJsonString(Spec.MapPackagePath),
            *EscapeRaftSimJsonString(Spec.SourceManifest),
            *EscapeRaftSimJsonString(Spec.FlowBandId),
            *EscapeRaftSimJsonString(Spec.FlowBandDisplayName),
            *EscapeRaftSimJsonString(Spec.FlowBandSource),
            *FlowReferenceDischargeJson,
            Spec.FlowWidthScale,
            Spec.FlowFoamScale,
            Spec.FlowWetBankScale,
            Spec.FlowCurrentCueScale,
            Spec.FlowWaterLevelOffsetCm,
            *EscapeRaftSimJsonString(Spec.FlowVisualDescription),
            *EscapeRaftSimJsonString(GuideSeatCapturePath),
            *EscapeRaftSimJsonString(GuideSeatCapturePath),
            *EscapeRaftSimJsonString(RiverEyeCapturePath),
            bGuideSeatCaptured && bRiverEyeCaptured && !Spec.SourceDrapeDescription.IsEmpty() ? TEXT("captured_source_derived_guide_and_river_eye_preview_renders") : (bGuideSeatCaptured && bRiverEyeCaptured ? TEXT("captured_procedural_guide_and_river_eye_blockout_renders") : TEXT("capture_failed")),
            *EscapeRaftSimJsonString(Spec.AerialDrapeImage),
            *EscapeRaftSimJsonString(Spec.TerrainReliefImage),
            *EscapeRaftSimJsonString(Spec.HeightfieldPreviewImage),
            Spec.HeightfieldPreviewAmplitudeCm,
            Spec.HeightfieldLocalReliefAmplitudeCm,
            Spec.HeightfieldSeamFeatherUv,
            Spec.TerrainNormalSofteningBlend,
            WaterResponse.EmissiveFillScale,
            WaterResponse.RoughnessScale,
            WaterResponse.RoughnessFloor,
            WaterResponse.SpecularLevel,
            WaterResponse.NormalIntensity,
            WaterResponse.MeshNormalUpBlend,
            *EscapeRaftSimJsonString(Spec.WaterMaskImage),
            *EscapeRaftSimJsonString(Spec.VegetationMaskImage),
            *EscapeRaftSimJsonString(
                GetSourceConditionedMaterialMapRelativePath(Spec.RiverId, TEXT("SourceConditionedMacroAlbedo"))),
            *EscapeRaftSimJsonString(
                GetSourceConditionedMaterialMapRelativePath(Spec.RiverId, TEXT("SourceConditionedMaterialZones"))),
            *EscapeRaftSimJsonString(
                GetSourceConditionedMaterialMapRelativePath(Spec.RiverId, TEXT("SourceConditionedAORoughnessHeight"))),
            *EscapeRaftSimJsonString(
                GetSourceConditionedMaterialMapRelativePath(Spec.RiverId, TEXT("SourceConditionedNormalDetail"))),
            *EscapeRaftSimJsonString(
                GetProductionDetailTextureRelativePath(Spec.RiverId, TEXT("TerrainDetailAlbedo"))),
            *EscapeRaftSimJsonString(
                GetProductionDetailTextureRelativePath(Spec.RiverId, TEXT("TerrainDetailNormal"))),
            *EscapeRaftSimJsonString(
                GetProductionDetailTextureRelativePath(Spec.RiverId, TEXT("TerrainDetailAORoughnessHeight"))),
            *EscapeRaftSimJsonString(Spec.ElevationSample),
            *EscapeRaftSimJsonString(GetPreviewFidelityNote(Spec)),
            *EscapeRaftSimJsonString(GetFirstPartyMaterialInstanceSceneAssignmentStatus()));
    }

    const FString Manifest = FString::Printf(
        TEXT("{\n")
        TEXT("  \"schema\": \"raftsim.unreal.environment_capture_manifest.v1\",\n")
        TEXT("  \"capture_type\": \"guide_seat_and_river_eye_downstream_unreal_preview\",\n")
        TEXT("  \"source_plan\": \"%s\",\n")
        TEXT("  \"procedural_asset_plan\": \"%s\",\n")
        TEXT("  \"procedural_material_recipe_plan\": \"%s\",\n")
        TEXT("  \"first_party_material_texture_atlas_manifest\": \"%s\",\n")
        TEXT("  \"source_conditioned_material_map_manifest\": \"%s\",\n")
        TEXT("  \"production_detail_texture_manifest\": \"%s\",\n")
        TEXT("  \"first_party_material_instance_candidate_manifest\": \"%s\",\n")
        TEXT("  \"first_party_material_texture_asset_root\": \"%s\",\n")
        TEXT("  \"first_party_material_texture_asset_status\": \"%s\",\n")
        TEXT("  \"source_conditioned_material_texture_asset_root\": \"%s\",\n")
        TEXT("  \"source_conditioned_material_texture_asset_status\": \"%s\",\n")
        TEXT("  \"production_detail_texture_asset_root\": \"%s\",\n")
        TEXT("  \"production_detail_texture_asset_status\": \"%s\",\n")
        TEXT("  \"first_party_atlas_sampler_review_material\": \"%s\",\n")
        TEXT("  \"first_party_atlas_sampler_review_material_status\": \"%s\",\n")
        TEXT("  \"first_party_material_instance_review_asset_root\": \"%s\",\n")
        TEXT("  \"first_party_material_instance_review_asset_status\": \"%s\",\n")
        TEXT("  \"first_party_material_instance_scene_assignment_status\": \"%s\",\n")
        TEXT("  \"geospatial_attachment_ledger\": \"%s\",\n")
        TEXT("  \"status\": \"%s\",\n")
        TEXT("  \"captures\": [\n")
        TEXT("%s\n")
        TEXT("  ]\n")
        TEXT("}\n"),
        *EscapeRaftSimJsonString(SourcePlanRelativePath),
        *EscapeRaftSimJsonString(ProceduralAssetPlanRelativePath),
        *EscapeRaftSimJsonString(ProceduralMaterialRecipePlanRelativePath),
        *EscapeRaftSimJsonString(MaterialTextureAtlasManifestRelativePath),
        *EscapeRaftSimJsonString(SourceConditionedMaterialMapManifestRelativePath),
        *EscapeRaftSimJsonString(ProductionDetailTextureManifestRelativePath),
        *EscapeRaftSimJsonString(MaterialInstanceCandidateManifestRelativePath),
        *EscapeRaftSimJsonString(MaterialTextureAssetRootRelativePath),
        *EscapeRaftSimJsonString(GetFirstPartyMaterialTextureAssetStatus()),
        *EscapeRaftSimJsonString(SourceConditionedMaterialTextureAssetRootRelativePath),
        *EscapeRaftSimJsonString(GetSourceConditionedMaterialTextureAssetStatus()),
        *EscapeRaftSimJsonString(ProductionDetailTextureAssetRootRelativePath),
        *EscapeRaftSimJsonString(GetProductionDetailTextureAssetStatus()),
        *EscapeRaftSimJsonString(MaterialShaderParentRelativePath),
        *EscapeRaftSimJsonString(GetFirstPartyAtlasSampleReviewMaterialStatus()),
        *EscapeRaftSimJsonString(MaterialInstanceReviewAssetRootRelativePath),
        *EscapeRaftSimJsonString(GetFirstPartyMaterialInstanceReviewAssetStatus()),
        *EscapeRaftSimJsonString(GetFirstPartyMaterialInstanceSceneAssignmentStatus()),
        *EscapeRaftSimJsonString(GeospatialAttachmentLedgerRelativePath),
        bAllCaptured ? TEXT("south_fork_colorado_and_pacuare_source_draped_guide_and_river_eye_previews_available; photoreal source_data_and_asset_replacement_required") : TEXT("one_or_more_captures_failed"),
        *EntriesJson);

    const FString ManifestPath = FPaths::Combine(CaptureRoot, TEXT("environment_capture_manifest.json"));
    const bool bSaved = FFileHelper::SaveStringToFile(Manifest, *ManifestPath);
    OutSummary += FString::Printf(
        TEXT("%s environment preview capture manifest -> %s\n"),
        bSaved ? TEXT("Saved") : TEXT("Failed"),
        *ManifestPath);

    if (FParse::Param(FCommandLine::Get(), TEXT("RaftSimSkipPhotorealFlowVariantCaptures")))
    {
        OutSummary += TEXT("Skipped flow-variant environment captures for this base-capture iteration.\n");
        return bAllCaptured && bSaved;
    }

    const FString FlowVariantCapturePlanRelativePath = GetPhotorealFlowVariantCapturePlanRelativePath();
    const FString FlowVariantCapturePlanAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), FlowVariantCapturePlanRelativePath));
    bool bFlowVariantCapturePlanAvailable = FPaths::FileExists(FlowVariantCapturePlanAbsolutePath);
    if (!bFlowVariantCapturePlanAvailable)
    {
        OutSummary += FString::Printf(TEXT("Missing flow-variant capture plan: %s\n"), *FlowVariantCapturePlanAbsolutePath);
    }
    else
    {
        OutSummary += FString::Printf(TEXT("Using photoreal flow-variant capture plan: %s\n"), *FlowVariantCapturePlanRelativePath);
    }

    FString FlowVariantEntriesJson;
    bool bAllFlowVariantCaptured = bFlowVariantCapturePlanAvailable;
    const bool bCullReviewOnlyForegroundRaftForFlowVariantGuideSeatCaptures = true;
    const TArray<FRaftSimEnvironmentPreviewSpec> FlowVariantSpecs = GetEnvironmentPreviewFlowVariantSpecs();
    for (int32 VariantIndex = 0; VariantIndex < FlowVariantSpecs.Num(); ++VariantIndex)
    {
        const FRaftSimEnvironmentPreviewSpec& VariantSpec = FlowVariantSpecs[VariantIndex];
        const FRaftSimPreviewWaterMaterialResponse VariantWaterResponse =
            GetPreviewWaterMaterialResponse(VariantSpec.RiverId);
        OutSummary += FString::Printf(
            TEXT("Generating %s %s flow-variant preview map.\n"),
            *VariantSpec.DisplayName,
            *VariantSpec.FlowBandId);
        const bool bVariantMapBuilt = BuildPreviewMapForSpec(VariantSpec, OutSummary);

        FString GuideSeatVariantCapturePath =
            GetPreviewFlowVariantCaptureRelativePath(VariantSpec, TEXT("guide_seat_downstream"));
        FString RiverEyeVariantCapturePath =
            GetPreviewFlowVariantCaptureRelativePath(VariantSpec, TEXT("river_eye_downstream"));
        const bool bGuideSeatVariantCaptured =
            bVariantMapBuilt &&
            CapturePreviewImageForSpec(
                VariantSpec,
                CaptureRoot,
                GuideSeatVariantCapturePath,
                TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
                TEXT("guide_seat_downstream"),
                TEXT("flow-variant guide-seat downstream"),
                bCullReviewOnlyForegroundRaftForFlowVariantGuideSeatCaptures,
                OutSummary);
        const bool bRiverEyeVariantCaptured =
            bVariantMapBuilt &&
            CapturePreviewImageForSpec(
                VariantSpec,
                CaptureRoot,
                RiverEyeVariantCapturePath,
                TEXT("RaftSim_RiverEye_DownstreamCaptureCamera"),
                TEXT("river_eye_downstream"),
                TEXT("flow-variant river-eye downstream"),
                true,
                OutSummary);
        bAllFlowVariantCaptured &= bGuideSeatVariantCaptured && bRiverEyeVariantCaptured;
        const FString VariantFlowReferenceDischargeJson = VariantSpec.FlowReferenceDischargeCfs >= 0.0f
            ? FString::Printf(TEXT("%.1f"), VariantSpec.FlowReferenceDischargeCfs)
            : FString(TEXT("null"));

        FlowVariantEntriesJson += FString::Printf(
            TEXT("%s    {\n")
            TEXT("      \"river_id\": \"%s\",\n")
            TEXT("      \"display_name\": \"%s\",\n")
            TEXT("      \"map_package\": \"%s\",\n")
            TEXT("      \"source_manifest\": \"%s\",\n")
            TEXT("      \"flow_band_id\": \"%s\",\n")
            TEXT("      \"flow_band_display_name\": \"%s\",\n")
            TEXT("      \"flow_band_source\": \"%s\",\n")
            TEXT("      \"flow_reference_discharge_cfs\": %s,\n")
            TEXT("      \"flow_visual_width_scale\": %.3f,\n")
            TEXT("      \"flow_visual_foam_scale\": %.3f,\n")
            TEXT("      \"flow_visual_wet_bank_scale\": %.3f,\n")
            TEXT("      \"flow_visual_current_cue_scale\": %.3f,\n")
            TEXT("      \"flow_visual_water_level_offset_cm\": %.3f,\n")
            TEXT("      \"flow_visual_note\": \"%s\",\n")
            TEXT("      \"guide_seat_capture\": \"%s\",\n")
            TEXT("      \"river_eye_capture\": \"%s\",\n")
            TEXT("      \"status\": \"%s\",\n")
            TEXT("      \"source_terrain_macro_amplitude_cm\": %.3f,\n")
            TEXT("      \"source_terrain_local_relief_amplitude_cm\": %.3f,\n")
            TEXT("      \"source_terrain_seam_feather_uv\": %.5f,\n")
            TEXT("      \"source_terrain_normal_softening_blend\": %.3f,\n")
            TEXT("      \"water_material_emissive_fill_scale\": %.3f,\n")
            TEXT("      \"water_material_roughness_scale\": %.3f,\n")
            TEXT("      \"water_material_roughness_floor\": %.3f,\n")
            TEXT("      \"water_material_specular_level\": %.3f,\n")
            TEXT("      \"water_material_normal_intensity\": %.3f,\n")
            TEXT("      \"water_mesh_normal_up_blend\": %.3f,\n")
            TEXT("      \"fidelity_note\": \"%s\"\n")
            TEXT("    }"),
            VariantIndex == 0 ? TEXT("") : TEXT(",\n"),
            *EscapeRaftSimJsonString(VariantSpec.RiverId),
            *EscapeRaftSimJsonString(VariantSpec.DisplayName),
            *EscapeRaftSimJsonString(VariantSpec.MapPackagePath),
            *EscapeRaftSimJsonString(VariantSpec.SourceManifest),
            *EscapeRaftSimJsonString(VariantSpec.FlowBandId),
            *EscapeRaftSimJsonString(VariantSpec.FlowBandDisplayName),
            *EscapeRaftSimJsonString(VariantSpec.FlowBandSource),
            *VariantFlowReferenceDischargeJson,
            VariantSpec.FlowWidthScale,
            VariantSpec.FlowFoamScale,
            VariantSpec.FlowWetBankScale,
            VariantSpec.FlowCurrentCueScale,
            VariantSpec.FlowWaterLevelOffsetCm,
            *EscapeRaftSimJsonString(VariantSpec.FlowVisualDescription),
            *EscapeRaftSimJsonString(GuideSeatVariantCapturePath),
            *EscapeRaftSimJsonString(RiverEyeVariantCapturePath),
            bGuideSeatVariantCaptured && bRiverEyeVariantCaptured ? TEXT("captured_band_named_flow_variant_preview_renders") : TEXT("capture_failed"),
            VariantSpec.HeightfieldPreviewAmplitudeCm,
            VariantSpec.HeightfieldLocalReliefAmplitudeCm,
            VariantSpec.HeightfieldSeamFeatherUv,
            VariantSpec.TerrainNormalSofteningBlend,
            VariantWaterResponse.EmissiveFillScale,
            VariantWaterResponse.RoughnessScale,
            VariantWaterResponse.RoughnessFloor,
            VariantWaterResponse.SpecularLevel,
            VariantWaterResponse.NormalIntensity,
            VariantWaterResponse.MeshNormalUpBlend,
            *EscapeRaftSimJsonString(GetPreviewFidelityNote(VariantSpec)));
    }

    const FString FlowVariantManifest = FString::Printf(
        TEXT("{\n")
        TEXT("  \"schema\": \"raftsim.unreal.environment_flow_variant_capture_manifest.v1\",\n")
        TEXT("  \"capture_type\": \"band_named_guide_seat_and_river_eye_downstream_unreal_preview\",\n")
        TEXT("  \"source_capture_manifest\": \"docs/environment-captures/photoreal_river_previews/environment_capture_manifest.json\",\n")
        TEXT("  \"source_flow_variant_capture_plan\": \"%s\",\n")
        TEXT("  \"status\": \"%s\",\n")
        TEXT("  \"captures\": [\n")
        TEXT("%s\n")
        TEXT("  ]\n")
        TEXT("}\n"),
        *EscapeRaftSimJsonString(FlowVariantCapturePlanRelativePath),
        bAllFlowVariantCaptured ? TEXT("all_band_named_flow_variant_previews_captured_not_lifelike_approved") : TEXT("one_or_more_flow_variant_captures_failed"),
        *FlowVariantEntriesJson);

    const FString FlowVariantManifestPath = FPaths::Combine(CaptureRoot, TEXT("flow_variant_capture_manifest.json"));
    const bool bFlowVariantManifestSaved = FFileHelper::SaveStringToFile(FlowVariantManifest, *FlowVariantManifestPath);
    OutSummary += FString::Printf(
        TEXT("%s flow-variant environment preview capture manifest -> %s\n"),
        bFlowVariantManifestSaved ? TEXT("Saved") : TEXT("Failed"),
        *FlowVariantManifestPath);

    return bSaved && bAllCaptured && bFlowVariantManifestSaved && bAllFlowVariantCaptured;
}

bool FRaftSimEditorModule::SaveWidgetScreenshot(
    const TSharedRef<SWidget>& Widget,
    const FString& BaseFileName,
    FString& OutPath) const
{
    if (!FSlateApplication::IsInitialized())
    {
        return false;
    }

    auto CaptureWidget = [&BaseFileName, &OutPath](const TSharedRef<SWidget>& TargetWidget) -> bool
    {
        PumpSlateForCapture(2);

        TArray<FColor> ImageData;
        FIntVector ImageSize;
        if (!FSlateApplication::Get().TakeScreenshot(TargetWidget, ImageData, ImageSize) || ImageData.IsEmpty() ||
            ImageSize.X <= 0 || ImageSize.Y <= 0)
        {
            return false;
        }

        TArray64<uint8> CompressedPng;
        FImageUtils::PNGCompressImageArray(ImageSize.X, ImageSize.Y, MakeArrayView(ImageData), CompressedPng);
        OutPath = BaseFileName + TEXT(".png");
        return FFileHelper::SaveArrayToFile(CompressedPng, *OutPath);
    };

    if (CaptureWidget(Widget))
    {
        return true;
    }

    TSharedPtr<SWindow> ParentWindow = FSlateApplication::Get().FindWidgetWindow(Widget);
    return ParentWindow.IsValid() ? CaptureWidget(ParentWindow.ToSharedRef()) : false;
}

IMPLEMENT_MODULE(FRaftSimEditorModule, RaftSimEditor)

#undef LOCTEXT_NAMESPACE
