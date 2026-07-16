#pragma once

#include "RaftSimEditorModule.h"
#include "Foliage/RaftSimEditorFoliageInternal.h"

#include "Algo/AllOf.h"
#include "Algo/AnyOf.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetCompilingManager.h"
#include "Animation/SkeletalMeshActor.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/DynamicMeshComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/LightComponent.h"
#include "Components/MeshComponent.h"
#include "Components/ReflectionCaptureComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/SphereReflectionCaptureComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkyAtmosphereComponent.h"
#include "Dom/JsonObject.h"
#include "UDynamicMesh.h"
#include "Editor.h"
#include "Engine/DirectionalLight.h"
#include "Engine/Engine.h"
#include "Engine/ExponentialHeightFog.h"
#include "Engine/PointLight.h"
#include "Engine/SceneCapture2D.h"
#include "Engine/SkeletalMesh.h"
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
#include "GeometryScript/MeshAssetFunctions.h"
#include "GeometryScript/MeshBasicEditFunctions.h"
#include "GeometryScript/MeshMaterialFunctions.h"
#include "Materials/MaterialExpressionLandscapeLayerCoords.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpressionAbs.h"
#include "Materials/MaterialExpressionAdd.h"
#include "Materials/MaterialExpressionComponentMask.h"
#include "Materials/MaterialExpressionConstant.h"
#include "Materials/MaterialExpressionConstant2Vector.h"
#include "Materials/MaterialExpressionConstant3Vector.h"
#include "Materials/MaterialExpressionCameraPositionWS.h"
#include "Materials/MaterialExpressionCustom.h"
#include "Materials/MaterialExpressionFrac.h"
#include "Materials/MaterialExpressionFresnel.h"
#include "Materials/MaterialExpressionLinearInterpolate.h"
#include "Materials/MaterialExpressionMaterialFunctionCall.h"
#include "Materials/MaterialExpressionMultiply.h"
#include "Materials/MaterialExpressionOneMinus.h"
#include "Materials/MaterialExpressionObjectPositionWS.h"
#include "Materials/MaterialExpressionSaturate.h"
#include "Materials/MaterialExpressionScalarParameter.h"
#include "Materials/MaterialExpressionSubtract.h"
#include "Materials/MaterialExpressionTextureCoordinate.h"
#include "Materials/MaterialExpressionTextureObjectParameter.h"
#include "Materials/MaterialExpressionTextureSampleParameter2D.h"
#include "Materials/MaterialExpressionTwoSidedSign.h"
#include "Materials/MaterialExpressionVertexColor.h"
#include "Materials/MaterialExpressionVertexNormalWS.h"
#include "Materials/MaterialExpressionVectorParameter.h"
#include "Materials/MaterialExpressionWorldPosition.h"
#include "Materials/MaterialInstanceConstant.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialFunctionInterface.h"
#include "MaterialShared.h"
#include "MeshUtilities.h"
#include "MeshDescription.h"
#include "Misc/CommandLine.h"
#include "Misc/CoreDelegates.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Misc/SecureHash.h"
#include "Modules/ModuleManager.h"
#include "NaniteSceneProxy.h"
#include "PlanarCut.h"
#include "PCGGraph.h"
#include "PCGDefaultExecutionSource.h"
#include "PCGData.h"
#include "PCGEdge.h"
#include "PCGNode.h"
#include "PCGPin.h"
#include "PCGSettings.h"
#include "ProceduralMeshComponent.h"
#include "ProceduralMeshConversion.h"
#include "ProceduralVegetation.h"
#include "DataTypes/PVFoliageInfo.h"
#include "DataTypes/PVMeshData.h"
#include "Facades/PVFoliageFacade.h"
#include "GeometryCollection/GeometryCollection.h"
#include "Utils/PVFloatRamp.h"
#include "RaftSimEditorToolRegistry.h"
#include "RaftSimFeatureTuningEditorShell.h"
#include "RaftSimRapidRiverEditorShell.h"
#include "RaftSimReplayDebugViewer.h"
#include "RaftSimToolValidationActions.h"
#include "Styling/CoreStyle.h"
#include "Subsystems/IPCGBaseSubsystem.h"
#include "ToolMenus.h"
#include "TextureCompiler.h"
#include "UObject/SavePackage.h"
#include "UObject/UnrealType.h"
#include "RenderingThread.h"
#include "RenderTimer.h"
#include "DynamicRHI.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "ShaderCompiler.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Input/SComboBox.h"
#include "Widgets/Input/SSearchBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SSeparator.h"
#include "Widgets/Layout/SUniformGridPanel.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Views/SListView.h"
#include "Widgets/SWindow.h"

DECLARE_LOG_CATEGORY_EXTERN(LogRaftSimEditorEnvironment, Log, All);

namespace RaftSimEditorEnvironment
{
using RaftSimEditorFoliage::FRaftSimEnvironmentPreviewSpec;

struct FRaftSimLandscapeImportCandidateSpec
{
    FRaftSimEnvironmentPreviewSpec PreviewSpec;
    FString HeightfieldRelativePath;
    FString HeightfieldManifestRelativePath;
    FString ImportContractRelativePath;
    FString LocalCenterlineRelativePath;
    FString MapPackagePath;
    int32 LandscapeSize = 1009;
    float HorizontalSpanXCm = 32300.0f;
    float HorizontalSpanYCm = 5500.0f;
    float TargetReliefCm = 1000.0f;
    bool bApplyPreviewAnalyticChannelBurn = true;
    bool bUseSolverVisualizationFields = true;
    bool bPhysicalScaleSourceCorridor = false;
    bool bEnableLandscapeNanite = true;
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
    float RenderWidthScale = 1.35f;
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
                    LogRaftSimEditorEnvironment,
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

struct FRaftSimLandscapeCandidateCenterlinePoint
{
    float StationMeters = 0.0f;
    FVector2D LocalCm = FVector2D::ZeroVector;
    float ConditionedVisualSurfaceNormalized = 0.0f;
    bool bHasConditionedVisualSurface = false;
};

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

struct FFutaleufuCoigueCrownForm
{
    FString Id;
    FString DisplayName;
    FString AssetToken;
    FString LifeStage;
    int32 SeedOffset = 0;
    int32 MainBranchCount = 26;
    int32 FarCrownVolumeAnchorCount = 370;
    float TrunkHeightScale = 1.0f;
    float TrunkRadiusScale = 1.0f;
    float CrownBaseZCm = 950.0f;
    float CrownSpanZCm = 1560.0f;
    float CrownWidthScale = 1.0f;
    float BranchUpliftScale = 1.0f;
    float AsymmetryScale = 1.0f;
    FVector2D TrunkLeanTopCm = FVector2D::ZeroVector;
    float SuppressedSectorCenterDegrees = 0.0f;
    float SuppressedSectorHalfWidthDegrees = 0.0f;
    float SuppressedSectorLengthScale = 1.0f;
    float CrownGapCenterT = -1.0f;
    float CrownGapHalfWidthT = 0.0f;
    float CrownGapLengthScale = 1.0f;
    int32 DamageModulo = 0;
    int32 DamageRemainder = 0;
    float DamagedBranchLengthScale = 1.0f;
};

struct FFutaleufuCoigueRoutingMetrics
{
    float MinNearBranchletClearanceCm = TNumericLimits<float>::Max();
    float MinNearTertiaryClearanceCm = TNumericLimits<float>::Max();
    int32 ReroutedBranchletCount = 0;
    int32 ReroutedTertiaryCount = 0;
    int32 UnresolvedBranchletClearanceCount = 0;
    int32 UnresolvedTertiaryClearanceCount = 0;
};

struct FFutaleufuCordilleraCypressForm
{
    FString Id;
    FString DisplayName;
    FString AssetToken;
    FString LifeStage;
    int32 SeedOffset = 0;
    int32 BranchCount = 38;
    float HeightCm = 2200.0f;
    float BaseRadiusCm = 72.0f;
    float CrownBaseCm = 420.0f;
    float CrownRadiusCm = 520.0f;
    float BranchUplift = 1.0f;
    float Asymmetry = 1.0f;
    FVector2D TrunkLeanTopCm = FVector2D::ZeroVector;
    float SuppressedSectorCenterDegrees = 0.0f;
    float SuppressedSectorHalfWidthDegrees = 0.0f;
    float SuppressedSectorLengthScale = 1.0f;
    float CrownGapCenterT = -1.0f;
    float CrownGapHalfWidthT = 0.0f;
    float CrownGapLengthScale = 1.0f;
    int32 DamageModulo = 0;
    int32 DamageRemainder = 0;
    float DamagedBranchLengthScale = 1.0f;
};

struct FZambeziCliffComparisonPlacement
{
    FVector Location = FVector::ZeroVector;
    FRotator Rotation = FRotator::ZeroRotator;
    FVector Scale = FVector::OneVector;
};

struct FZambeziBatokaCorridorPlacement
{
    FString ModuleAsset;
    FVector Location = FVector::ZeroVector;
    FRotator Rotation = FRotator::ZeroRotator;
    FVector Scale = FVector::OneVector;
};

struct FZambeziBatokaBasaltModuleDefinition
{
    FString Id;
    FString DisplayName;
    FString AssetToken;
    int32 Seed = 0;
    float WidthCm = 0.0f;
    float DepthCm = 0.0f;
    float HeightCm = 0.0f;
    int32 ColumnCount = 0;
    int32 MinimumLayerCount = 0;
    float GullyCenterT = -1.0f;
    float GullyHalfWidthT = 0.0f;
    float GullyDepthCm = 0.0f;
    float TalusDensity = 1.0f;
    float BrecciaWeight = 0.0f;
};

struct FZambeziBatokaBasaltModuleMetrics
{
    int32 WallCellCount = 0;
    int32 TalusBlockCount = 0;
    int32 VertexCount = 0;
    int32 TriangleCount = 0;
    FBox Bounds = FBox(EForceInit::ForceInit);
};

struct FFutaleufuCanopyCorridorComparisonStats
{
    bool bDenseLocalReview = false;
    bool bAreaSampledReview = false;
    bool bWorldStableReview = false;
    int32 CandidateCount = 0;
    int32 TargetTreeCount = 0;
    int32 AcceptedTreeCount = 0;
    int32 NearTreeCount = 0;
    int32 MidTreeCount = 0;
    int32 FarTreeCount = 0;
    int32 HiddenFallbackActorCount = 0;
    int32 RejectedNaturalGapCount = 0;
    int32 RejectedVegetationMaskCount = 0;
    int32 RejectedWaterMaskCount = 0;
    int32 RejectedRiverSetbackCount = 0;
    int32 RejectedStandDensityCount = 0;
    int32 RejectedElevationCount = 0;
    int32 RejectedSlopeCount = 0;
    int32 RejectedDryAspectCount = 0;
    int32 RejectedSpacingCount = 0;
    float MinimumAcceptedSlopeDegrees = TNumericLimits<float>::Max();
    float MaximumAcceptedSlopeDegrees = TNumericLimits<float>::Lowest();
    float MinimumAcceptedElevationCm = TNumericLimits<float>::Max();
    float MaximumAcceptedElevationCm = TNumericLimits<float>::Lowest();
    double AcceptedVegetationMaskSum = 0.0;
    double AcceptedWaterMaskSum = 0.0;
    float ProgressMinimum = 0.0f;
    float ProgressMaximum = 0.0f;
    float MinimumSpacingCm = 0.0f;
    float RiverSetbackCm = 0.0f;
    float MaximumLateralOffsetCm = 0.0f;
    float SamplingHalfExtentCm = 0.0f;
    float SamplingAlongHalfExtentCm = 0.0f;
    float SamplingCrossHalfExtentCm = 0.0f;
    int32 OccupancyFieldResolution = 0;
    float OccupancyFeatherDistanceCm = 0.0f;
    float MinimumAcceptedRiverDistanceCm = TNumericLimits<float>::Max();
    float MaximumAcceptedRiverDistanceCm = TNumericLimits<float>::Lowest();
    uint64 PlacementFingerprint = 1469598103934665603ull;
};

struct FFutaleufuCanopyCorridorVariant
{
    FString AssetToken;
    UStaticMesh* TrunkMesh = nullptr;
    UStaticMesh* BranchletMesh = nullptr;
    UStaticMesh* NearLeafMesh = nullptr;
    UStaticMesh* MidLeafMesh = nullptr;
    UStaticMesh* FarLeafMesh = nullptr;
    UHierarchicalInstancedStaticMeshComponent* TrunkInstances = nullptr;
    UHierarchicalInstancedStaticMeshComponent* BranchletInstances = nullptr;
    UHierarchicalInstancedStaticMeshComponent* NearLeafInstances = nullptr;
    UHierarchicalInstancedStaticMeshComponent* MidLeafInstances = nullptr;
    UHierarchicalInstancedStaticMeshComponent* FarLeafInstances = nullptr;
};

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
    int32 DressingCanopyTreeInstanceCount = 0;
    int32 DressingUnderstoryInstanceCount = 0;
    int32 DressingSourceSkeletalMeshCount = 0;
    int32 DressingConvertedStaticMeshCount = 0;
    int32 DressingFoliageMaterialAssetCount = 0;
    int32 DressingFoliageMaterialBoundSlotCount = 0;
    int32 DressingNativeFoliageMaterialFallbackSlotCount = 0;
    bool bDressingAssetsLoaded = false;
    bool bDressingSourceMasksLoaded = false;
    bool bDressingBoulderMeshNaniteEnabled = false;
    bool bDressingBroadleafMeshNaniteEnabled = false;
    bool bDressingConiferMeshNaniteEnabled = false;
    bool bDressingUnderstoryMeshNaniteEnabled = false;
    bool bDressingFoliageMaterialsValidated = false;
    int32 DressingExternalReviewAssetCount = 0;
    int32 DressingExternalRockMeshCount = 0;
    bool bDressingExternalRockMaterialsValidated = false;
    int32 DressingExternalPineMeshCount = 0;
    bool bDressingExternalPineMaterialsValidated = false;
    bool bDressingExternalBroadleafReviewAssetLoaded = false;
    bool bDressingExternalBroadleafMaterialsValidated = false;
    bool bDressingExternalConiferReviewAssetLoaded = false;
    bool bDressingExternalConiferMaterialsValidated = false;
    FString DressingBroadleafAssetPath =
        TEXT("/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_DeciduousTree01_Static");
    FString DressingConiferAssetPath =
        TEXT("/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_Conifer01_Static");
    bool bDressingValidated = false;
    FString WaterMaterialPath;
    int32 WaterMaterialBoundComponentCount = 0;
    bool bSolverSurfaceWaterMaterialBound = false;
    bool bNaniteRepresentationBuilt = false;
    bool bMaterialBindingsValidated = false;
    bool bNaniteMaterialBindingsValidated = false;
};

enum ERaftSimFirstPartyMaterialAtlasTile : int32
{
    TerrainBankLayeredMaterialTile = 0,
    WetBoulderContactMaterialTile = 1,
    BiomeFoliageGroundcoverMaterialTile = 2,
    FlowDependentWaterSurfaceMaterialTile = 3,
    FoamSprayMistAtmosphereMaterialTile = 4,
    RaftForegroundReviewMaterialTile = 5,
};

enum class EFutaleufuCanopyCorridorRenderMode : uint8
{
    Native,
    NativeLeavesNoShadow,
    OpaqueLeavesNoShadow,
    NativeAlphaScaleFourNoShadow,
    NativeAlphaScaleTwoNoShadow,
    NativeAlphaScaleThreeNoShadow,
    NativeAlphaScaleTwoBoundedShadow,
    NativeConstantOpacityNoShadow,
    NativeAlphaScaleFourAoOffNoShadow,
    NativeAlphaScaleFourFlatNormalNoShadow,
    NativeAlphaScaleFourEmissiveNoShadow,
    NativeAlphaScaleFourBaseColorDoubleNoShadow,
    NativeAlphaScaleFourTransmissionWhiteNoShadow,
    NativeAlphaScaleFourBaseColorDoubleTransmissionWhiteNoShadow,
    DefaultLitAlphaScaleFourNoShadow,
    DefaultLitAlphaScaleFourBaseColorDoubleNoShadow,
};

enum class EFutaleufuCanopyCorridorLightingTreatment : uint8
{
    Baseline,
    IsolatedReviewFill,
    SkyLightDouble,
};

inline constexpr int32 FutaleufuCoigueBranchletsPerParentShoot = 8;
inline constexpr int32 FutaleufuCoigueMainLeavesPerBranchlet = 10;
inline constexpr int32 FutaleufuCoigueTertiaryBranchesPerBranchlet = 3;
inline constexpr int32 FutaleufuCoigueLeavesPerTertiaryBranch = 4;
inline constexpr int32 FutaleufuCoigueAttachedLeavesPerBranchlet =
    FutaleufuCoigueMainLeavesPerBranchlet +
    FutaleufuCoigueTertiaryBranchesPerBranchlet * FutaleufuCoigueLeavesPerTertiaryBranch;

FRaftSimLandscapeCandidateWaterSettings GetLandscapeCandidateWaterSettings(const FString& RiverId);

FRaftSimPhotographicCaptureSettings GetPhotographicCaptureSettings(const FString& RiverId);

FRaftSimLandscapeCandidateFoliageSettings GetLandscapeCandidateFoliageSettings(
    const FString& RiverId);

FRaftSimPreviewWaterMaterialResponse GetPreviewWaterMaterialResponse(const FString& RiverId);

FString GetRepoRoot();

FString GetCaptureRoot();

FString GetEnvironmentCaptureRoot();

FString GetPhotorealRiverSourcePlanRelativePath();

FString GetPhotorealFlowVariantCapturePlanRelativePath();

FString GetFirstPartyProceduralEnvironmentAssetPlanRelativePath();

FString GetFirstPartyProceduralMaterialRecipePlanRelativePath();

FString GetFirstPartyMaterialTextureAtlasManifestRelativePath();

FString GetSourceConditionedMaterialMapManifestRelativePath();

FString GetProductionDetailTextureManifestRelativePath();

FString GetFirstPartyMaterialInstanceCandidateManifestRelativePath();

FString GetFirstPartyMaterialInstanceReviewAssetRootRelativePath();

FString GetFirstPartyMaterialInstanceReviewAssetStatus();

FString GetFirstPartyMaterialInstanceSceneAssignmentStatus();

FString GetFirstPartyMaterialTextureAssetRootRelativePath();

FString GetFirstPartyMaterialTextureAssetStatus();

FString GetSourceConditionedMaterialTextureAssetRootRelativePath();

FString GetSourceConditionedMaterialTextureAssetStatus();

FString GetProductionDetailTextureAssetRootRelativePath();

FString GetProductionDetailTextureAssetStatus();

FString GetSolverVisualizationFieldManifestRelativePath();

FString GetSolverVisualizationFieldTextureAssetRootRelativePath();

FString GetFirstPartyAtlasSampleReviewMaterialRelativePath();

FString GetFirstPartyAtlasSampleReviewMaterialStatus();

FString GetFirstPartyMaterialTextureAtlasAlbedoRelativePath(const FString& RiverId);

FString GetFirstPartyMaterialTextureAtlasNormalRelativePath(const FString& RiverId);

FString GetFirstPartyMaterialTextureAtlasPackedRelativePath(const FString& RiverId);

FString GetSourceConditionedMaterialMapRelativePath(const FString& RiverId, const FString& MapKey);

FString GetProductionDetailTextureRelativePath(const FString& RiverId, const FString& MapKey);

FString GetProductionGeospatialAttachmentLedgerRelativePath();

FString EscapeRaftSimJsonString(const FString& Value);

bool LoadLandscapeCandidateLocalCenterline(
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    TArray<FRaftSimLandscapeCandidateCenterlinePoint>& OutPoints,
    FString& OutSummary);

FVector2D SampleLandscapeCandidateCenterlineWorld(
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    const TArray<FRaftSimLandscapeCandidateCenterlinePoint>& Points,
    float Progress,
    FVector2D* OutTangent = nullptr);

bool SampleLandscapeCandidateConditionedVisualSurfaceWorldZ(
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    const TArray<FRaftSimLandscapeCandidateCenterlinePoint>& Points,
    float Progress,
    float& OutWorldZ);

TArray<FRaftSimEnvironmentPreviewSpec> GetEnvironmentPreviewSpecs();

TArray<FRaftSimLandscapeImportCandidateSpec> GetLandscapeImportCandidateSpecs();

FRaftSimLandscapeMaterialCandidateSettings GetLandscapeMaterialCandidateSettings(const FString& RiverId);

FString MakeFlowVariantPreviewMapPackagePath(const FRaftSimEnvironmentPreviewSpec& BaseSpec);

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
    float FlowWaterLevelOffsetCm);

TArray<FRaftSimEnvironmentPreviewSpec> GetEnvironmentPreviewFlowVariantSpecs();

UStaticMesh* LoadPreviewMesh(const TCHAR* MeshPath);

UMaterialInterface* LoadPreviewBaseMaterial();

UMaterialInterface* LoadPreviewMaterial(const TCHAR* MaterialPath);

void ConnectPreviewMaterialColorInput(FColorMaterialInput& Input, UMaterialExpression* Expression);

void ConnectPreviewMaterialVectorInput(FVectorMaterialInput& Input, UMaterialExpression* Expression);

void ConnectPreviewMaterialScalarInput(FScalarMaterialInput& Input, UMaterialExpression* Expression);

UMaterialInterface* LoadOrCreatePreviewColorMaterial();

UMaterialInterface* LoadOrCreateLandscapeCandidateMaterial(
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    FString& OutSummary);

UMaterialInterface* LoadOrCreatePreviewVertexColorMaterial();

UMaterialInterface* LoadOrCreatePreviewTerrainVertexColorMaterial();

UMaterialInterface* LoadOrCreatePhysicalSourceTerrainRenderMaterial(
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    bool bBatokaTerrainIntegratedReview = false,
    bool bBatokaWorldAlignedReview = false);

UMaterialInterface* LoadOrCreatePreviewTranslucentColorMaterial();

UMaterialInterface* LoadOrCreatePreviewWaterVertexColorMaterial();

UMaterial* LoadOrCreateLandscapeCandidateSolverSurfaceWaterParent(FString& OutSummary);

UMaterialInterface* LoadOrCreateLandscapeCandidateSolverFoamMaterial(FString& OutSummary);

UMaterialInterface* LoadOrCreateLandscapeCandidateWaterMaterial(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    FString& OutSummary,
    bool bDisableSolverVisualizationFields = false);

FString GetFirstPartyMaterialTextureAssetBindingKey(const FString& RiverId, const FString& MapKey);

bool LoadPreviewPngBgraPixels(const FString& RelativePath, int32& OutWidth, int32& OutHeight, TArray<FColor>& OutPixels);

TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> GetFirstPartyMaterialTextureAtlasAssetSpecs();

TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> GetSourceConditionedMaterialTextureAssetSpecs();

TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> GetProductionDetailMaterialTextureAssetSpecs();

TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> GetSolverVisualizationFieldTextureAssetSpecs();

TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> GetFutaleufuNativeCanopyTextureAssetSpecs();

TArray<FRaftSimFirstPartyMaterialTextureAssetSpec> GetFutaleufuCordilleraCypressTextureAssetSpecs();

void ApplyFirstPartyMaterialTextureImportSettings(
    UTexture2D* Texture,
    const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec);

bool UpdateFirstPartyMaterialTextureSource(
    UTexture2D* Texture,
    const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec,
    int32 Width,
    int32 Height,
    const TArray<FColor>& Pixels);

bool RebuildAndValidateFirstPartyTexturePlatformData(
    UTexture2D* Texture,
    const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec,
    FString& OutSummary);

UTexture2D* CreateOrUpdateFirstPartyMaterialTextureAsset(
    const FRaftSimFirstPartyMaterialTextureAssetSpec& Spec,
    FString& OutSummary,
    bool& bOutSaved);

bool CreateFirstPartyMaterialTextureAtlasAssets(
    TMap<FString, UTexture2D*>& OutTextureAssetsByKey,
    FString& OutSummary,
    const FString& RiverIdFilter = FString());

bool CreateSourceConditionedMaterialTextureAssets(
    TMap<FString, UTexture2D*>& InOutTextureAssetsByKey,
    FString& OutSummary,
    const FString& RiverIdFilter = FString());

bool CreateProductionDetailMaterialTextureAssets(
    TMap<FString, UTexture2D*>& InOutTextureAssetsByKey,
    FString& OutSummary,
    const FString& RiverIdFilter = FString());

bool CreateSolverVisualizationFieldTextureAssets(FString& OutSummary);

bool CreateFutaleufuNativeCanopyTextureAssets(
    TMap<FString, UTexture2D*>& OutTextureAssetsByKey,
    FString& OutSummary);

bool CreateFutaleufuCordilleraCypressTextureAssets(
    TMap<FString, UTexture2D*>& OutTextureAssetsByKey,
    FString& OutSummary);

UMaterialExpression* AddComplementaryScreenDitherOpacity(
    UMaterial* Material,
    UMaterialExpression* BaseOpacity,
    int32 BaseOpacityOutputIndex,
    bool bKeepSourceSide,
    float DefaultSourceCoverage,
    int32 EditorX,
    int32 EditorY);

UMaterial* CreateOrUpdateFutaleufuNativeCanopyMaterial(
    const FString& AssetName,
    bool bLeafMaterial,
    const TMap<FString, UTexture2D*>& Textures,
    FString& OutSummary,
    bool bDefaultLitLeafDiagnostic = false,
    const FString& LeafTextureKeyPrefix = FString(),
    bool bFreezeWindForDeterministicReview = false,
    bool bEnableComplementaryTransition = false);

UMaterial* CreateOrUpdateFutaleufuCypressNearSprayMaterial(
    const FString& AssetName,
    FString& OutSummary,
    bool bVolumetricScaleLeaves = false);

UMaterial* CreateOrUpdateFutaleufuCypressFarProxyMaterial(FString& OutSummary);

bool EnsureFutaleufuNativeCanopyInstancedMaterialUsage(
    UMaterial* Material,
    FString& OutSummary);

UMaterialInterface* LoadOrCreateFirstPartyAtlasSampleReviewMaterial(
    const TMap<FString, UTexture2D*>& TextureAssetsByKey,
    FString& OutSummary);

TArray<FRaftSimFirstPartyMaterialInstanceCandidateSpec> GetFirstPartyMaterialInstanceCandidateSpecs();

bool CreateOrUpdateFirstPartyMaterialInstanceCandidateAsset(
    const FRaftSimFirstPartyMaterialInstanceCandidateSpec& Spec,
    const TMap<FString, UTexture2D*>& TextureAssetsByKey,
    FString& OutSummary);

bool CreateFirstPartyMaterialInstanceCandidateAssets(FString& OutSummary);

FString GetFirstPartyMaterialRiverAssetName(const FString& RiverId);

UMaterialInterface* LoadFirstPartyMaterialInstanceCandidate(const FString& RiverId, const TCHAR* RecipeAssetName);

FRaftSimFirstPartyMaterialAssignmentSet LoadFirstPartyMaterialAssignmentSetForSpec(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    FString& OutSummary);

UMaterialInterface* SelectFirstPartyMaterialForPreviewActor(
    const FString& ActorLabel,
    const FRaftSimFirstPartyMaterialAssignmentSet& Assignments);

int32 AssignFirstPartyMaterialInstancesToPreviewScene(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimFirstPartyMaterialAssignmentSet& Assignments,
    FString& OutSummary);

UMaterialInstanceDynamic* CreatePreviewColorMaterial(UObject* Outer, const FLinearColor& Color);

UMaterialInstanceDynamic* CreatePreviewTranslucentColorMaterial(UObject* Outer, const FLinearColor& Color, float Opacity);

TArray<FVector> ComputePreviewMeshNormals(const TArray<FVector>& Vertices, const TArray<int32>& Triangles);

bool LoadPreviewPngImage(const FString& RelativePath, FRaftSimPreviewImage& OutImage);

void ApplyPreviewColor(UMeshComponent* Component, const FLinearColor& Color);

void ApplyPreviewTranslucentColor(UMeshComponent* Component, const FLinearColor& Color, float Opacity);

float SmoothPreviewStep(float Edge0, float Edge1, float Value);

FLinearColor ClampPreviewColor(const FLinearColor& Color);

FLinearColor ScalePreviewColor(const FLinearColor& Color, float Scale);

float GetPreviewColorLuma(const FLinearColor& Color);

FLinearColor SampleFirstPartyMaterialAtlasTile(
    const FRaftSimPreviewImage* Atlas,
    int32 TileIndex,
    float LocalU,
    float LocalV);

FLinearColor ApplyFirstPartyMaterialAtlasTint(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* Atlas,
    int32 TileIndex,
    const FLinearColor& BaseColor,
    float LocalU,
    float LocalV,
    float Weight);

float SampleFirstPartyMaterialAtlasPackedHeight(
    const FRaftSimPreviewImage* PackedAtlas,
    int32 TileIndex,
    float LocalU,
    float LocalV,
    float DefaultHeight = 0.5f);

FLinearColor ApplyFirstPartyMaterialAtlasSurfaceResponse(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* NormalAtlas,
    const FRaftSimPreviewImage* PackedAtlas,
    int32 TileIndex,
    const FLinearColor& BaseColor,
    float LocalU,
    float LocalV,
    float Weight);

float GetFirstPartyMaterialAtlasMicroReliefCm(
    const FRaftSimPreviewImage* PackedAtlas,
    int32 TileIndex,
    float LocalU,
    float LocalV,
    float AmplitudeCm,
    float Weight);

FLinearColor NormalizePreviewSourceDrapeAlbedo(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& RawColor,
    float SourceWaterT,
    float SourceVegetationT,
    float MaterialBlend);

FLinearColor NormalizePreviewTerrainProxyPatchColor(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& RawColor);

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
    float CellSeed);

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
    float CellSeed);

FLinearColor GetPreviewSoftTerrainPatchFeatherBaseColor(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    float X,
    float Y,
    float Phase);

float GetPreviewSoftTerrainPatchCoverage(float U, float V, float Phase);

FLinearColor BlendPreviewSoftTerrainPatchColor(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& FeatureColor,
    float X,
    float Y,
    float U,
    float V,
    float Phase,
    float Coverage);

float GetPreviewTerrainNormalSofteningBlend(const FRaftSimEnvironmentPreviewSpec& Spec);

void SoftenPreviewTerrainNormals(TArray<FVector>& Normals, float UpBlend);

float GetPreviewRiverCenterY(const FRaftSimEnvironmentPreviewSpec& Spec, float X);

float GetPreviewActiveRiverHalfWidthCm(const FRaftSimEnvironmentPreviewSpec& Spec);

float GetPreviewWaterSurfaceBaseZCm(const FRaftSimEnvironmentPreviewSpec& Spec);

void GetPreviewMaskUv(const FRaftSimEnvironmentPreviewSpec& Spec, float X, float Y, float& OutU, float& OutV);

float SamplePreviewMaskAtWorld(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* Mask,
    float X,
    float Y);

float SamplePreviewTerrainReliefCm(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    float X,
    float Y,
    float ChannelOffset);

float SamplePreviewHeightfieldCm(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* HeightfieldPreview,
    float X,
    float Y,
    float ChannelOffset);

float SamplePreviewBankUndercutShelfReliefCm(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    float X,
    float Y,
    float ChannelOffset);

float GetPreviewTerrainHeightCm(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    float X,
    float Y,
    const FRaftSimPreviewImage* TerrainRelief = nullptr,
    const FRaftSimPreviewImage* HeightfieldPreview = nullptr);

FLinearColor ApplyPreviewSourceAwareTerrainPhotoMottle(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FLinearColor& RawColor,
    float X,
    float Y,
    float BankT,
    float CanyonT,
    float WetT,
    float SourceWaterT,
    float SourceVegetationT);

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
    float ActiveRiverHalfWidth);

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
    float ActiveRiverHalfWidth);

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
    float ActiveRiverHalfWidth);

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
    float ActiveRiverHalfWidth);

AStaticMeshActor* AddPreviewMeshActor(
    UWorld* World,
    UStaticMesh* Mesh,
    const FString& Label,
    const FVector& Location,
    const FRotator& Rotation,
    const FVector& Scale,
    const FLinearColor& Color,
    UMaterialInterface* MaterialOverride = nullptr,
    bool bUseMeshDefaultMaterial = false);

AStaticMeshActor* AddPreviewTranslucentMeshActor(
    UWorld* World,
    UStaticMesh* Mesh,
    const FString& Label,
    const FVector& Location,
    const FRotator& Rotation,
    const FVector& Scale,
    const FLinearColor& Color,
    float Opacity);

UInstancedStaticMeshComponent* AddPreviewInstancedMeshComponent(
    UWorld* World,
    UStaticMesh* Mesh,
    const FString& Label,
    const FLinearColor& Color);

UHierarchicalInstancedStaticMeshComponent* AddLandscapeCandidateInstancedMeshComponent(
    UWorld* World,
    UStaticMesh* Mesh,
    const FString& Label,
    bool bCastShadow,
    UMaterialInterface* MaterialOverride = nullptr);

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
    bool bCreateCollision = true);

AActor* AddPreviewTwoSectionProceduralMeshActor(
    UWorld* World,
    const FString& Label,
    const TArray<FVector>& FirstVertices,
    const TArray<int32>& FirstTriangles,
    const TArray<FVector>& FirstNormals,
    const TArray<FVector2D>& FirstUVs,
    UMaterialInterface* FirstMaterial,
    const TArray<FVector>& SecondVertices,
    const TArray<int32>& SecondTriangles,
    const TArray<FVector>& SecondNormals,
    const TArray<FVector2D>& SecondUVs,
    UMaterialInterface* SecondMaterial);

void AppendNativeCanopyTaperedSegment(
    const FVector& Start,
    const FVector& End,
    float StartRadius,
    float EndRadius,
    int32 SegmentCount,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs);

void AppendNativeCanopyLeafCard(
    const FVector& Center,
    const FVector& Right,
    const FVector& Up,
    float Width,
    float Height,
    int32 AtlasTile,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs);

void AppendNativeCanopyAtlasCurvedCard(
    const FVector& Start,
    const FVector& Axis,
    const FVector& Right,
    float Width,
    float Length,
    float Camber,
    float LateralSweep,
    int32 SegmentCount,
    int32 AtlasTile,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs);

void AppendNativeCanopyCurvedSprayRibbon(
    const FVector& Start,
    const FVector& Control,
    const FVector& End,
    const FVector& NormalHint,
    float StartHalfWidth,
    float EndHalfWidth,
    float HalfThickness,
    int32 SegmentCount,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs);

float NativeCanopySegmentDistance(
    const FVector& A1,
    const FVector& B1,
    const FVector& A2,
    const FVector& B2);

void BuildFutaleufuCoiguePrototypeGeometry(
    const FFutaleufuCoigueCrownForm& Form,
    TArray<FVector>& TrunkVertices,
    TArray<int32>& TrunkTriangles,
    TArray<FVector>& TrunkNormals,
    TArray<FVector2D>& TrunkUVs,
    TArray<FVector>& BranchletVertices,
    TArray<int32>& BranchletTriangles,
    TArray<FVector>& BranchletNormals,
    TArray<FVector2D>& BranchletUVs,
    TArray<FVector>& LeafVertices,
    TArray<int32>& LeafTriangles,
    TArray<FVector>& LeafNormals,
    TArray<FVector2D>& LeafUVs,
    TArray<FVector>& FarLeafVertices,
    TArray<int32>& FarLeafTriangles,
    TArray<FVector>& FarLeafNormals,
    TArray<FVector2D>& FarLeafUVs,
    FVector& OutCloseupCamera,
    FVector& OutCloseupTarget,
    FFutaleufuCoigueRoutingMetrics& OutRoutingMetrics);

void AppendFutaleufuCordilleraCypressOpaqueScaleLeafCluster(
    const FVector& Base,
    const FVector& Direction,
    float WidthCm,
    float LengthCm,
    float FoldCm,
    float RollDegrees,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& UVs);

void AppendFutaleufuCordilleraCypressVolumetricScaleLeafCluster(
    const FVector& Base,
    const FVector& Direction,
    float WidthCm,
    float LengthCm,
    int32 Seed,
    TArray<FVector>& WoodyVertices,
    TArray<int32>& WoodyTriangles,
    TArray<FVector>& WoodyNormals,
    TArray<FVector2D>& WoodyUVs,
    TArray<FVector>& FoliageVertices,
    TArray<int32>& FoliageTriangles,
    TArray<FVector>& FoliageNormals,
    TArray<FVector2D>& FoliageUVs);

void BuildFutaleufuCordilleraCypressGeometry(
    const FFutaleufuCordilleraCypressForm& Form,
    bool bOpaqueNearGeometry,
    bool bVolumetricNearGeometry,
    TArray<FVector>& WoodyVertices,
    TArray<int32>& WoodyTriangles,
    TArray<FVector>& WoodyNormals,
    TArray<FVector2D>& WoodyUVs,
    TArray<FVector>& NearSprayVertices,
    TArray<int32>& NearSprayTriangles,
    TArray<FVector>& NearSprayNormals,
    TArray<FVector2D>& NearSprayUVs,
    TArray<FVector>& SprayVertices,
    TArray<int32>& SprayTriangles,
    TArray<FVector>& SprayNormals,
    TArray<FVector2D>& SprayUVs,
    FVector& OutCloseupCamera,
    FVector& OutCloseupTarget);

void BuildReducedNativeCanopyCardGeometry(
    const TArray<FVector>& SourceVertices,
    const TArray<int32>& SourceTriangles,
    const TArray<FVector>& SourceNormals,
    const TArray<FVector2D>& SourceUVs,
    int32 CardStride,
    float CardScale,
    TArray<FVector>& OutVertices,
    TArray<int32>& OutTriangles,
    TArray<FVector>& OutNormals,
    TArray<FVector2D>& OutUVs);

UStaticMesh* ConvertNativeCanopyProceduralActorToStaticMesh(
    AActor* Actor,
    const FString& PackagePath,
    UMaterialInterface* Material,
    bool bEnableNanite,
    ENaniteShapePreservation ShapePreservation,
    FString& OutSummary);

AActor* AddPreviewIrregularRockActor(
    UWorld* World,
    const FString& Label,
    const FVector& BaseLocation,
    float YawDegrees,
    const FVector& Scale,
    const FLinearColor& Color,
    int32 Seed);

AActor* AddPreviewProceduralLeafClusterActor(
    UWorld* World,
    const FString& Label,
    const FVector& BaseLocation,
    float YawDegrees,
    const FVector& Scale,
    const FLinearColor& Color,
    int32 Seed,
    bool bRainforest);

AActor* AddPreviewOrganicLeafSprayActor(
    UWorld* World,
    const FString& Label,
    const FVector& BaseLocation,
    float YawDegrees,
    const FVector& Scale,
    const FLinearColor& Color,
    int32 Seed,
    bool bRainforest);

AActor* AddPreviewOrganicBranchFrondActor(
    UWorld* World,
    const FString& Label,
    const FVector& BaseLocation,
    float YawDegrees,
    const FVector& Scale,
    const FLinearColor& Color,
    int32 Seed,
    bool bRainforest,
    bool bUnderstory);

AActor* AddPreviewFineTwigCanopyLaceActor(
    UWorld* World,
    const FString& Label,
    const FVector& BaseLocation,
    float YawDegrees,
    const FVector& Scale,
    const FLinearColor& Color,
    int32 Seed,
    bool bRainforest);

void AddPreviewFoliageCrownDepthAndLeafletBreakupDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask);

void AddPreviewBoulderSurfaceFacet(
    UWorld* World,
    const FString& Label,
    const FVector& Center,
    const FVector& LongAxis,
    const FVector& ShortAxis,
    const FLinearColor& InnerColor,
    const FLinearColor& OuterColor);

void AddPreviewBoulderSurfaceVariationDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FVector& BaseLocation,
    float YawDegrees,
    const FVector& Scale,
    int32 BoulderIndex,
    float WaterMaskT,
    float VegetationMaskT,
    bool bNearCameraReviewBoulder);

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
    const FRaftSimPreviewImage* MaterialAtlasPacked);

void AddPreviewAerialDrapeTiles(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* AerialDrape,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask);

AActor* AddPreviewRiverRibbonMesh(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* MaterialAtlasAlbedo,
    const FRaftSimPreviewImage* MaterialAtlasNormal,
    const FRaftSimPreviewImage* MaterialAtlasPacked,
    UMaterialInterface* MaterialOverride = nullptr,
    const FRaftSimPreviewImage* SolverVisualizationFields = nullptr,
    UMaterialInterface* SolverFoamMaterial = nullptr);

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
    const FLinearColor& OuterColor);

void AddPreviewWetBankDressing(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview);

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
    bool bClampAboveWaterSurface = false);

void AddPreviewIrregularShorelineEdgeBreakupDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask);

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
    const FLinearColor& RimColor);

void AddPreviewTerrainErosionRillDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask);

void AddPreviewSourceAwareBankBreakupDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask);

void AddPreviewTerrainMaterialLayerDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask);

void AddPreviewLandscapeNaniteMaterialScaffoldDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask);

void AddPreviewProceduralEnvironmentDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask,
    UStaticMesh* PebbleMesh);

void DisablePreviewProceduralMeshCollision(AActor* Actor);

void AddPreviewSourceMaskedShorelineLipOverhangDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask);

void AddPreviewSourceMaskedBankBarMicrogeometryDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask);

void AddPreviewProceduralBankTextureCards(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask,
    UStaticMesh* PlaneMesh);

void AddPreviewFoamRibbon(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FString& Label,
    float StartX,
    float Length,
    float LateralOffset,
    float Width,
    float Phase,
    const FLinearColor& Color);

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
    const FLinearColor& ShadowColor);

void AddPreviewFlowBandTextureDetail(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec);

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
    const FLinearColor& OuterColor);

void AddPreviewWaterSurfaceChopAndTurbidityDetail(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec);

void AddPreviewWaterShaderDepthReflectionScaffoldDetail(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec);

void AddPreviewShallowWaterClarityAndAerationDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* WaterMask,
    UStaticMesh* PlaneMesh);

void AddPreviewFoamAndHydraulics(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec);

void AddPreviewFlowDependentHydraulicAerationAndSprayDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    UStaticMesh* PlaneMesh,
    UStaticMesh* SphereMesh);

void AddPreviewWaterSurfaceDetail(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec);

void AddPreviewWaterMicroRippleGlintDetail(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec, UStaticMesh* PlaneMesh);

void AddPreviewSurfaceAtmosphereAndSprayDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    UStaticMesh* PlaneMesh);

void AddPreviewRiverAtmosphericBackdropDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    UStaticMesh* PlaneMesh);

void AddPreviewSourceAwareSkyGradientLayer(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    UStaticMesh* PlaneMesh);

void AddPreviewWaterfallAndPlungeMistDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    UStaticMesh* PlaneMesh,
    UStaticMesh* CubeMesh);

void AddPreviewBiomeBankEcologyDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask,
    UStaticMesh* CubeMesh,
    UStaticMesh* CylinderMesh,
    UStaticMesh* PlaneMesh);

void AddPreviewBiomeFoliageSilhouetteDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask,
    UStaticMesh* CylinderMesh,
    UStaticMesh* PlaneMesh);

void AddPreviewDenseBiomeFoliageLayerDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask,
    UStaticMesh* CylinderMesh,
    UStaticMesh* PlaneMesh);

void AddPreviewInstancedProceduralFoliageEquivalentDetail(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask,
    UStaticMesh* SphereMesh,
    UStaticMesh* CylinderMesh);

void AddPreviewRaftForeground(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    UStaticMesh* CubeMesh,
    UStaticMesh* CylinderMesh,
    const FRaftSimPreviewImage* MaterialAtlasAlbedo);

AActor* AddPreviewRiverEyeCenterArtifactCover(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec);

void AddPreviewNearFieldPhotorealReviewDressing(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* AerialDrape,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask);

void AddPreviewLightRig(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec);

void AddPreviewCameraAndStart(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec);

bool SavePreviewWorld(UWorld* World, const FString& PackagePath, FString& OutSummary);

FString GetPreviewCaptureRelativePath(const FRaftSimEnvironmentPreviewSpec& Spec, const FString& CaptureId);

FString GetPreviewFlowVariantCaptureRelativePath(const FRaftSimEnvironmentPreviewSpec& Spec, const FString& CaptureId);

FString GetPreviewFidelityNote(const FRaftSimEnvironmentPreviewSpec& Spec);

ACameraActor* FindPreviewCaptureCamera(UWorld* World, const FString& PreferredCameraLabel);

bool CapturePreviewImageForSpec(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FString& CaptureRoot,
    FString& OutRelativeCapturePath,
    const FString& CameraLabel,
    const FString& CaptureId,
    const FString& CaptureDescription,
    bool bHideForegroundRaftProxies,
    FString& OutSummary,
    const TFunction<bool(UWorld*, ACameraActor*, FString&)>& WorldSetup = {});

bool ConfigureFutaleufuComplementaryTransitionCapture(
    UWorld* LoadedWorld,
    ACameraActor* CaptureCamera,
    const FString& AuthorityMode,
    float SourceCoverage,
    FString& SetupSummary,
    float PatternSize = 4.0f,
    float TransitionMode = 0.0f);

bool SetFutaleufuMergedGeometryHlodBracketMode(
    UWorld* World,
    bool bShowFlatAtlas,
    bool bShowMergedGeometry,
    FString& OutSummary);

bool SetFutaleufuMergedGeometryComponentParityMode(
    UWorld* World,
    bool bShowSingleComponent,
    bool bShowSplitComponents,
    bool bBarkCastsShadow,
    FString& OutSummary);

bool SetFutaleufuHlodAtlasFrameOverride(
    UWorld* World,
    float FrameOverride,
    FString& OutSummary);

bool SetFutaleufuHlodSplitShadingOverrides(
    UWorld* World,
    float TrunkGainMultiplier,
    float FoliageGainMultiplier,
    float TrunkRoughness,
    float FoliageRoughness,
    float TrunkSpecular,
    float FoliageSpecular,
    FString& OutSummary);

bool SetFutaleufuHlodProxyLayerMode(
    UWorld* World,
    bool bUseDualLayer,
    FString& OutSummary);

bool SetFutaleufuHlodFoliageTransmissionTint(
    UWorld* World,
    const FLinearColor& TransmissionTint,
    FString& OutSummary);

ADirectionalLight* FindFutaleufuTransmissionBracketSun(UWorld* World);

bool SetFutaleufuTransmissionBracketLightDirection(
    UWorld* World,
    ACameraActor* ReferenceCamera,
    AActor* HlodActor,
    bool bBacklit,
    FString& OutSummary);

bool CaptureFutaleufuComplementaryTransitionMotionSequence(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FString& RelativeCaptureBase,
    const FString& AuthorityMode,
    int32 PatternSize,
    TArray<FString>& OutRelativeCapturePaths,
    FString& OutSummary,
    bool bLitRiverView = false,
    const TFunction<bool(
        UWorld*,
        ACameraActor*&,
        AActor*&,
        FVector&,
        FVector&,
        FVector&,
        FString&)>& SceneSetup = {},
    float TransitionMode = 0.0f,
    bool bHlodFrameSearch = false,
    int32* OutAutomaticHlodFrame = nullptr,
    bool bHlodSplitShadingSearch = false,
    bool bHlodDualLayerReview = false,
    bool bHlodTransmissionLightBracketReview = false,
    bool bHlodMergedGeometryShapeBracketReview = false,
    bool bHlodMergedComponentParityReview = false);

FBox GetZambeziCliffComparisonEffectiveBounds(UStaticMesh* Mesh);

bool AddZambeziCliffComparisonInstances(
    UWorld* World,
    ACameraActor* Camera,
    UStaticMesh* CliffMesh,
    TArray<FZambeziCliffComparisonPlacement>& OutPlacements,
    FString& OutSummary);

bool AddZambeziBatokaBasaltCorridorComparisonInstances(
    UWorld* World,
    ACameraActor* Camera,
    const TArray<UStaticMesh*>& ModuleMeshes,
    TArray<FZambeziBatokaCorridorPlacement>& OutPlacements,
    FString& OutSummary);

float GetBatokaDeterministicUnit(int32 Seed, int32 Channel);

void AddBatokaBasaltQuad(
    const FVector& A,
    const FVector& B,
    const FVector& C,
    const FVector& D,
    const FLinearColor& ColorA,
    const FLinearColor& ColorB,
    TArray<FVector>& OutVertices,
    TArray<int32>& OutTriangles,
    TArray<FVector>& OutNormals,
    TArray<FVector2D>& OutUVs,
    TArray<FLinearColor>& OutVertexColors);

void AddBatokaBasaltBlock(
    const FVector& Center,
    const FVector& Size,
    float YawDegrees,
    const FLinearColor& BaseColor,
    int32 Seed,
    TArray<FVector>& OutVertices,
    TArray<int32>& OutTriangles,
    TArray<FVector>& OutNormals,
    TArray<FVector2D>& OutUVs,
    TArray<FLinearColor>& OutVertexColors);

void AddBatokaTalusRock(
    const FVector& BaseLocation,
    const FVector& Size,
    float YawDegrees,
    const FLinearColor& BaseColor,
    int32 Seed,
    TArray<FVector>& OutVertices,
    TArray<int32>& OutTriangles,
    TArray<FVector2D>& OutUVs,
    TArray<FLinearColor>& OutVertexColors);

TArray<FVector> ComputeBatokaBasaltNormals(
    const TArray<FVector>& Vertices,
    const TArray<int32>& Triangles);

void BuildZambeziBatokaBasaltModuleGeometry(
    const FZambeziBatokaBasaltModuleDefinition& Definition,
    TArray<FVector>& OutVertices,
    TArray<int32>& OutTriangles,
    TArray<FVector>& OutNormals,
    TArray<FVector2D>& OutUVs,
    TArray<FLinearColor>& OutVertexColors,
    FZambeziBatokaBasaltModuleMetrics& OutMetrics);

UMaterialInterface* LoadOrCreateZambeziBatokaBasaltReviewMaterial(FString& OutSummary);

bool ApplyFutaleufuCanopyCorridorLightingTreatment(
    UWorld* World,
    EFutaleufuCanopyCorridorLightingTreatment Treatment,
    FString& OutSummary);

const TCHAR* GetFutaleufuCanopyCorridorRenderModeToken(
    EFutaleufuCanopyCorridorRenderMode RenderMode);

bool AddFutaleufuCanopyCorridorComparisonInstances(
    UWorld* World,
    ACameraActor* Camera,
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    EFutaleufuCanopyCorridorRenderMode RenderMode,
    FFutaleufuCanopyCorridorComparisonStats& OutStats,
    FString& OutSummary,
    bool bDenseLocalReview = false,
    bool bAreaSampledReview = false,
    bool bWorldStableReview = false);

UMaterialInstanceConstant* LoadOrCreateLandscapeCandidateFoliageMaterialInstance(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const TCHAR* FoliageType,
    const TCHAR* SourceParentObjectPath,
    const FLinearColor& FrontTint,
    const FLinearColor& BackTint,
    const FLinearColor& TransmissionTint,
    float RoughnessStrength,
    float NormalStrength,
    FString& OutSummary);

int32 BindLandscapeCandidateFoliageMaterial(
    UHierarchicalInstancedStaticMeshComponent* Component,
    UStaticMesh* Mesh,
    UMaterialInterface* FoliageMaterial);

bool ValidateLandscapeCandidateReviewedFirMaterials(UStaticMesh* Mesh);

bool ValidateLandscapeCandidateReviewedBroadleafMaterials(UStaticMesh* Mesh);

bool ValidateLandscapeCandidateReviewedRockMaterial(UStaticMesh* Mesh);

bool ValidateLandscapeCandidateReviewedPineMaterials(UStaticMesh* Mesh);

FBox GetLandscapeCandidateEffectiveMeshBounds(UStaticMesh* Mesh);

UStaticMesh* LoadOrCreateLandscapeCandidatePveStaticMesh(
    UWorld* World,
    const TCHAR* SourceSkeletalMeshPath,
    const TCHAR* OutputPackagePath,
    FString& OutSummary);

bool AddLandscapeCandidateBiomeDressing(
    UWorld* World,
    ALandscape* Landscape,
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    FRaftSimLandscapeImportCandidateResult& OutResult,
    FString& OutSummary);

FString GetLandscapeCandidateCaptureRelativePath(
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    const FString& CaptureId);

void ApplyPreviewOnlyLandscapeChannelBurn(
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    uint16 ChannelFloor,
    TArray<uint16>& HeightData,
    int32& OutModifiedSampleCount);

AActor* AddLandscapeCandidatePhysicalRiverRibbon(
    UWorld* World,
    ALandscape* Landscape,
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    UMaterialInterface* WaterMaterial,
    FString& OutSummary);

AActor* AddLandscapeCandidatePhysicalBankCorridorMesh(
    UWorld* World,
    ALandscape* Landscape,
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    FString& OutSummary);

void RepositionLandscapeCandidatePhysicalCameras(
    UWorld* World,
    ALandscape* Landscape,
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    FString& OutSummary);

bool BuildLandscapeImportCandidateMap(
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    FRaftSimLandscapeImportCandidateResult& OutResult,
    FString& OutSummary);

bool BuildPreviewMapForSpec(const FRaftSimEnvironmentPreviewSpec& Spec, FString& OutSummary);
} // namespace RaftSimEditorEnvironment
