#include "RaftSimEditorModule.h"
#include "Foliage/RaftSimEditorFoliageInternal.h"
#include "Foliage/RaftSimEditorPveAuthoringInternal.h"

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

#define LOCTEXT_NAMESPACE "FRaftSimEditorModule"

DEFINE_LOG_CATEGORY_STATIC(LogRaftSimEditorPveAtlas, Log, All);
#define LogRaftSimEditor LogRaftSimEditorPveAtlas

using RaftSimEditorFoliage::AppendNativeCanopyAtlasCurvedCard;
using RaftSimEditorFoliage::AppendNativeCanopyLeafCard;
using RaftSimEditorFoliage::AppendNativeCanopyTaperedSegment;
using RaftSimEditorFoliage::AddComplementaryScreenDitherOpacity;
using RaftSimEditorFoliage::AddPreviewProceduralMeshActor;
using RaftSimEditorFoliage::AddPreviewTwoSectionProceduralMeshActor;
using RaftSimEditorFoliage::ComputePreviewMeshNormals;
using RaftSimEditorFoliage::ConfigureFutaleufuComplementaryTransitionCapture;
using RaftSimEditorFoliage::ConnectPreviewMaterialColorInput;
using RaftSimEditorFoliage::ConnectPreviewMaterialScalarInput;
using RaftSimEditorFoliage::ConnectPreviewMaterialVectorInput;
using RaftSimEditorFoliage::ConvertNativeCanopyProceduralActorToStaticMesh;
using RaftSimEditorFoliage::CreateFutaleufuCordilleraCypressTextureAssets;
using RaftSimEditorFoliage::CreateOrUpdateFutaleufuCypressFarProxyMaterial;
using RaftSimEditorFoliage::CreateOrUpdateFutaleufuNativeCanopyMaterial;
using RaftSimEditorFoliage::EscapeRaftSimJsonString;
using RaftSimEditorFoliage::FRaftSimEnvironmentPreviewSpec;
using RaftSimEditorFoliage::FRaftSimPhotographicCaptureSettings;
using RaftSimEditorFoliage::FindPreviewCaptureCamera;
using RaftSimEditorFoliage::GetPhotographicCaptureSettings;
using RaftSimEditorFoliage::GetRepoRoot;
using RaftSimEditorFoliage::LoadPreviewMesh;
using RaftSimEditorFoliage::SavePreviewWorld;
using RaftSimEditorFoliage::ScalePreviewColor;


namespace RaftSimEditorPve
{
enum class EPveAtlasMaterialLayer : uint8
{
    Combined,
    Trunk,
    Foliage,
};

bool SavePveAtlasPng(
    const FString& AbsolutePath,
    int32 Width,
    int32 Height,
    const TArray<FColor>& Pixels)
{
    if (Width <= 0 || Height <= 0 || Pixels.Num() != Width * Height)
    {
        return false;
    }
    TArray64<uint8> CompressedPng;
    FImageUtils::PNGCompressImageArray(
        Width,
        Height,
        MakeArrayView(Pixels),
        CompressedPng);
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(AbsolutePath), true);
    return !CompressedPng.IsEmpty() &&
        FFileHelper::SaveArrayToFile(CompressedPng, *AbsolutePath);
}

void DilatePveAtlasTileRgb(
    TArray<FColor>& Pixels,
    int32 AtlasWidth,
    int32 TileOriginX,
    int32 TileOriginY,
    int32 TileSize,
    int32 Iterations)
{
    if (Pixels.Num() != AtlasWidth * AtlasWidth || TileSize <= 0 || Iterations <= 0)
    {
        return;
    }
    TArray<uint8> Filled;
    Filled.SetNumZeroed(TileSize * TileSize);
    for (int32 Y = 0; Y < TileSize; ++Y)
    {
        for (int32 X = 0; X < TileSize; ++X)
        {
            Filled[Y * TileSize + X] =
                Pixels[(TileOriginY + Y) * AtlasWidth + TileOriginX + X].A > 0 ? 1 : 0;
        }
    }
    static const FIntPoint Neighbors[] = {
        FIntPoint(-1, 0), FIntPoint(1, 0), FIntPoint(0, -1), FIntPoint(0, 1),
        FIntPoint(-1, -1), FIntPoint(1, -1), FIntPoint(-1, 1), FIntPoint(1, 1)};
    for (int32 Iteration = 0; Iteration < Iterations; ++Iteration)
    {
        const TArray<uint8> PreviousFilled = Filled;
        const TArray<FColor> PreviousPixels = Pixels;
        bool bChanged = false;
        for (int32 Y = 0; Y < TileSize; ++Y)
        {
            for (int32 X = 0; X < TileSize; ++X)
            {
                const int32 LocalIndex = Y * TileSize + X;
                if (PreviousFilled[LocalIndex])
                {
                    continue;
                }
                int32 Red = 0;
                int32 Green = 0;
                int32 Blue = 0;
                int32 Count = 0;
                for (const FIntPoint& Offset : Neighbors)
                {
                    const int32 NeighborX = X + Offset.X;
                    const int32 NeighborY = Y + Offset.Y;
                    if (NeighborX < 0 || NeighborY < 0 ||
                        NeighborX >= TileSize || NeighborY >= TileSize ||
                        !PreviousFilled[NeighborY * TileSize + NeighborX])
                    {
                        continue;
                    }
                    const FColor& Neighbor = PreviousPixels[
                        (TileOriginY + NeighborY) * AtlasWidth + TileOriginX + NeighborX];
                    Red += Neighbor.R;
                    Green += Neighbor.G;
                    Blue += Neighbor.B;
                    ++Count;
                }
                if (Count > 0)
                {
                    FColor& Pixel = Pixels[
                        (TileOriginY + Y) * AtlasWidth + TileOriginX + X];
                    Pixel.R = static_cast<uint8>(Red / Count);
                    Pixel.G = static_cast<uint8>(Green / Count);
                    Pixel.B = static_cast<uint8>(Blue / Count);
                    Filled[LocalIndex] = 1;
                    bChanged = true;
                }
            }
        }
        if (!bChanged)
        {
            break;
        }
    }
}

UTexture2D* CreateOrUpdateLocalPveAtlasTexture(
    const FString& PackagePath,
    const TArray<FColor>& Pixels,
    int32 Resolution,
    TextureCompressionSettings CompressionSettings,
    bool bSrgb,
    bool bScaleAlphaCoverage,
    FString& OutSummary)
{
    if (Pixels.Num() != Resolution * Resolution || Resolution <= 0)
    {
        OutSummary += FString::Printf(TEXT("Invalid local PVE atlas pixels for %s.\n"), *PackagePath);
        return nullptr;
    }
    const FString AssetName = FPackageName::GetLongPackageAssetName(PackagePath);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, *AssetName);
    UTexture2D* Texture = LoadObject<UTexture2D>(nullptr, *ObjectPath);
    UPackage* Package = Texture ? Texture->GetOutermost() : CreatePackage(*PackagePath);
    if (!Package)
    {
        OutSummary += FString::Printf(TEXT("Could not create local PVE atlas package %s.\n"), *PackagePath);
        return nullptr;
    }
    if (!Texture)
    {
        Texture = NewObject<UTexture2D>(
            Package,
            *AssetName,
            RF_Public | RF_Standalone | RF_Transactional);
        if (Texture)
        {
            FAssetRegistryModule::AssetCreated(Texture);
        }
    }
    if (!Texture)
    {
        OutSummary += FString::Printf(TEXT("Could not create local PVE atlas texture %s.\n"), *ObjectPath);
        return nullptr;
    }

    Texture->Modify();
    Texture->Source.Init(Resolution, Resolution, 1, 1, TSF_BGRA8);
    uint8* MipData = Texture->Source.LockMip(0);
    for (int64 PixelIndex = 0; PixelIndex < Pixels.Num(); ++PixelIndex)
    {
        const FColor& Pixel = Pixels[PixelIndex];
        *MipData++ = Pixel.B;
        *MipData++ = Pixel.G;
        *MipData++ = Pixel.R;
        *MipData++ = Pixel.A;
    }
    Texture->Source.UnlockMip(0);
    Texture->SRGB = bSrgb;
    Texture->CompressionSettings = CompressionSettings;
    Texture->CompressionNoAlpha = !bScaleAlphaCoverage;
    Texture->MipGenSettings = TMGS_Sharpen4;
    Texture->LODGroup = bSrgb
        ? TEXTUREGROUP_Impostor
        : TEXTUREGROUP_ImpostorNormalDepth;
    Texture->AddressX = TA_Clamp;
    Texture->AddressY = TA_Clamp;
    Texture->VirtualTextureStreaming = false;
    // Exact-camera review runs immediately after generation, so the atlas must not
    // briefly fall back to a low resident mip while texture streaming catches up.

    Texture->NeverStream = true;
    Texture->bDoScaleMipsForAlphaCoverage = bScaleAlphaCoverage;
    Texture->AlphaCoverageThresholds = bScaleAlphaCoverage
        ? FVector4(0.0f, 0.0f, 0.0f, 0.38f)
        : FVector4::Zero();
    Texture->SetModernSettingsForNewOrChangedTexture();
    Texture->PostEditChange();
    Texture->MarkPackageDirty();
    Package->MarkPackageDirty();

    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath,
        FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Texture, *Filename, SaveArgs))
    {
        OutSummary += FString::Printf(TEXT("Could not save local PVE atlas texture %s.\n"), *ObjectPath);
        return nullptr;
    }
    OutSummary += FString::Printf(TEXT("Saved local PVE atlas texture %s.\n"), *ObjectPath);
    return Texture;
}

UMaterial* CreateOrUpdateLocalPveAtlasMaterial(
    const FString& PackagePath,
    UTexture2D* BaseColorTexture,
    UTexture2D* NormalTexture,
    UTexture2D* OpacityTexture,
    UTexture2D* DepthTexture,
    UTexture2D* MaterialIdentityTexture,
    bool bUseColorCorrectShading,
    const FLinearColor& AtlasColorGainDefault,
    float AtlasAzimuthOffsetDegrees,
    bool bUseDepthParallax,
    float DepthParallaxScaleCm,
    bool bEnableComplementaryTransition,
    bool bUseLitShading,
    EPveAtlasMaterialLayer MaterialLayer,
    FString& OutSummary)
{
    if (!BaseColorTexture || !NormalTexture || !OpacityTexture || !DepthTexture ||
        !MaterialIdentityTexture)
    {
        OutSummary += TEXT(
            "Local PVE atlas material is missing color, normal, depth, opacity, or material-identity texture.\n");
        return nullptr;
    }
    const FString AssetName = FPackageName::GetLongPackageAssetName(PackagePath);
    const FString ObjectPath = FString::Printf(TEXT("%s.%s"), *PackagePath, *AssetName);
    UMaterial* Material = LoadObject<UMaterial>(nullptr, *ObjectPath);
    UPackage* Package = Material ? Material->GetOutermost() : CreatePackage(*PackagePath);
    if (!Package)
    {
        OutSummary += FString::Printf(TEXT("Could not create local PVE atlas material package %s.\n"), *PackagePath);
        return nullptr;
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
        OutSummary += FString::Printf(TEXT("Could not create local PVE atlas material %s.\n"), *ObjectPath);
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    const bool bTrunkLayer = MaterialLayer == EPveAtlasMaterialLayer::Trunk;
    const bool bFoliageLayer = MaterialLayer == EPveAtlasMaterialLayer::Foliage;
    Material->SetShadingModel(
        bUseLitShading
            ? (bFoliageLayer ? MSM_TwoSidedFoliage : MSM_DefaultLit)
            : MSM_Unlit);
    Material->BlendMode = BLEND_Masked;
    Material->TwoSided = true;
    Material->bTangentSpaceNormal = !bUseLitShading;
    Material->DitheredLODTransition = true;
    Material->OpacityMaskClipValue = 0.38f;

    auto AddExpression = [Material](auto* Expression, int32 EditorX, int32 EditorY)
    {
        Expression->MaterialExpressionEditorX = EditorX;
        Expression->MaterialExpressionEditorY = EditorY;
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    UMaterialExpressionTextureCoordinate* TexCoord =
        AddExpression(NewObject<UMaterialExpressionTextureCoordinate>(Material), -1400, -480);
    UMaterialExpressionWorldPosition* WorldPosition =
        AddExpression(NewObject<UMaterialExpressionWorldPosition>(Material), -1400, 520);
    WorldPosition->WorldPositionShaderOffset = WPT_ExcludeAllShaderOffsets;
    UMaterialExpressionObjectPositionWS* ObjectPosition =
        AddExpression(NewObject<UMaterialExpressionObjectPositionWS>(Material), -1400, 700);
    UMaterialExpressionCameraPositionWS* CameraPosition =
        AddExpression(NewObject<UMaterialExpressionCameraPositionWS>(Material), -1400, 880);
    UMaterialExpressionScalarParameter* AtlasAzimuthOffsetTurns =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -1400, -240);
    AtlasAzimuthOffsetTurns->ParameterName = TEXT("AtlasAzimuthOffsetTurns");
    AtlasAzimuthOffsetTurns->DefaultValue = AtlasAzimuthOffsetDegrees / 360.0f;
    UMaterialExpressionScalarParameter* AtlasFrameOverride =
        AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -1400, -60);
    AtlasFrameOverride->ParameterName = TEXT("AtlasFrameOverride");
    AtlasFrameOverride->DefaultValue = -1.0f;
    AtlasFrameOverride->SliderMin = -1.0f;
    AtlasFrameOverride->SliderMax = 15.0f;

    UMaterialExpressionCustom* AtlasUv =
        AddExpression(NewObject<UMaterialExpressionCustom>(Material), -1060, -420);
    AtlasUv->Description = TEXT("Select nearest 8x2 upper-hemisphere frame in a 4x4 atlas");
    AtlasUv->OutputType = CMOT_Float2;
    AtlasUv->Code =
        TEXT("float3 ViewToCamera = normalize((float3)(CameraPos - ObjectPos));\n")
        TEXT("float Azimuth = atan2(ViewToCamera.y, ViewToCamera.x);\n")
        TEXT("float NormalizedAzimuth = frac(Azimuth / 6.28318530718 - AzimuthOffsetTurns + 1.0);\n")
        TEXT("float AzimuthFrame = floor(NormalizedAzimuth * 8.0 + 0.5);\n")
        TEXT("AzimuthFrame -= floor(AzimuthFrame / 8.0) * 8.0;\n")
        TEXT("float ElevationFrame = ViewToCamera.z > 0.2164396149 ? 1.0 : 0.0;\n")
        TEXT("float AutomaticFrame = ElevationFrame * 8.0 + AzimuthFrame;\n")
        TEXT("float Frame = FrameOverride >= -0.5 ? clamp(floor(FrameOverride + 0.5), 0.0, 15.0) : AutomaticFrame;\n")
        TEXT("float2 Cell = float2(Frame - floor(Frame / 4.0) * 4.0, floor(Frame / 4.0));\n")
        TEXT("float2 PlaneUv = float2(UV.x, 1.0 - UV.y);\n")
        TEXT("return (clamp(PlaneUv, 0.001, 0.999) + Cell) * 0.25;");
    FCustomInput& AtlasUvInput = AtlasUv->Inputs.AddDefaulted_GetRef();
    AtlasUvInput.InputName = TEXT("UV");
    AtlasUvInput.Input.Expression = TexCoord;
    FCustomInput& AtlasObjectInput = AtlasUv->Inputs.AddDefaulted_GetRef();
    AtlasObjectInput.InputName = TEXT("ObjectPos");
    AtlasObjectInput.Input.Expression = ObjectPosition;
    FCustomInput& AtlasCameraInput = AtlasUv->Inputs.AddDefaulted_GetRef();
    AtlasCameraInput.InputName = TEXT("CameraPos");
    AtlasCameraInput.Input.Expression = CameraPosition;
    FCustomInput& AtlasAzimuthOffsetInput = AtlasUv->Inputs.AddDefaulted_GetRef();
    AtlasAzimuthOffsetInput.InputName = TEXT("AzimuthOffsetTurns");
    AtlasAzimuthOffsetInput.Input.Expression = AtlasAzimuthOffsetTurns;
    FCustomInput& AtlasFrameOverrideInput = AtlasUv->Inputs.AddDefaulted_GetRef();
    AtlasFrameOverrideInput.InputName = TEXT("FrameOverride");
    AtlasFrameOverrideInput.Input.Expression = AtlasFrameOverride;


    UMaterialExpressionTextureSampleParameter2D* DepthSample = nullptr;
    UMaterialExpressionScalarParameter* DepthScale = nullptr;
    if (bUseDepthParallax)
    {
        DepthSample = AddExpression(
            NewObject<UMaterialExpressionTextureSampleParameter2D>(Material),
            -860,
            360);
        DepthSample->ParameterName = TEXT("AtlasDepth");
        DepthSample->Texture = DepthTexture;
        DepthSample->SamplerType = SAMPLERTYPE_LinearGrayscale;
        DepthSample->Coordinates.Expression = AtlasUv;
        DepthSample->MipValueMode = TMVM_MipLevel;
        DepthSample->ConstMipValue = 0;
        DepthScale = AddExpression(
            NewObject<UMaterialExpressionScalarParameter>(Material),
            -860,
            500);
        DepthScale->ParameterName = TEXT("AtlasDepthParallaxScaleCm");
        DepthScale->DefaultValue = DepthParallaxScaleCm;
    }

    UMaterialExpressionCustom* BillboardOffset =
        AddExpression(NewObject<UMaterialExpressionCustom>(Material), -900, 620);
    BillboardOffset->Description = TEXT("Rotate the source XY plane toward the active camera");
    BillboardOffset->OutputType = CMOT_Float3;
    BillboardOffset->Code = bUseDepthParallax
        ? TEXT("float3 ViewToCamera = normalize((float3)(CameraPos - ObjectPos));\n")
          TEXT("float3 Forward = -ViewToCamera;\n")
          TEXT("float3 Right = normalize(cross(float3(0.0, 0.0, 1.0), Forward));\n")
          TEXT("float3 Up = normalize(cross(Forward, Right));\n")
          TEXT("float3 LocalDelta = (float3)(WorldPos - ObjectPos);\n")
          TEXT("float DepthCentered = saturate(Depth.r) - 0.5;\n")
          TEXT("float3 BillboardPos = (float3)ObjectPos + Right * LocalDelta.x + Up * LocalDelta.y - Forward * DepthCentered * DepthScaleCm;\n")
          TEXT("return BillboardPos - (float3)WorldPos;")
        : TEXT("float3 ViewToCamera = normalize((float3)(CameraPos - ObjectPos));\n")
          TEXT("float3 Forward = -ViewToCamera;\n")
          TEXT("float3 Right = normalize(cross(float3(0.0, 0.0, 1.0), Forward));\n")
          TEXT("float3 Up = normalize(cross(Forward, Right));\n")
          TEXT("float3 LocalDelta = (float3)(WorldPos - ObjectPos);\n")
          TEXT("float3 BillboardPos = (float3)ObjectPos + Right * LocalDelta.x + Up * LocalDelta.y;\n")
          TEXT("return BillboardPos - (float3)WorldPos;");
    FCustomInput& BillboardWorldInput = BillboardOffset->Inputs.AddDefaulted_GetRef();
    BillboardWorldInput.InputName = TEXT("WorldPos");
    BillboardWorldInput.Input.Expression = WorldPosition;
    FCustomInput& BillboardObjectInput = BillboardOffset->Inputs.AddDefaulted_GetRef();
    BillboardObjectInput.InputName = TEXT("ObjectPos");
    BillboardObjectInput.Input.Expression = ObjectPosition;
    FCustomInput& BillboardCameraInput = BillboardOffset->Inputs.AddDefaulted_GetRef();
    BillboardCameraInput.InputName = TEXT("CameraPos");
    BillboardCameraInput.Input.Expression = CameraPosition;
    if (bUseDepthParallax)
    {
        FCustomInput& BillboardDepthInput = BillboardOffset->Inputs.AddDefaulted_GetRef();
        BillboardDepthInput.InputName = TEXT("Depth");
        BillboardDepthInput.Input.Expression = DepthSample;
        FCustomInput& BillboardDepthScaleInput = BillboardOffset->Inputs.AddDefaulted_GetRef();
        BillboardDepthScaleInput.InputName = TEXT("DepthScaleCm");
        BillboardDepthScaleInput.Input.Expression = DepthScale;
    }

    UMaterialExpressionTextureSampleParameter2D* BaseColorSample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -620, -520);
    BaseColorSample->ParameterName = TEXT("AtlasBaseColorOpacity");
    BaseColorSample->Texture = BaseColorTexture;
    BaseColorSample->SamplerType = SAMPLERTYPE_Color;
    BaseColorSample->Coordinates.Expression = AtlasUv;
    UMaterialExpressionTextureSampleParameter2D* OpacitySample =
        AddExpression(NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -620, -320);
    OpacitySample->ParameterName = TEXT("AtlasOpacity");
    OpacitySample->Texture = OpacityTexture;
    OpacitySample->SamplerType = SAMPLERTYPE_LinearGrayscale;
    OpacitySample->Coordinates.Expression = AtlasUv;
    UMaterialExpressionTextureSampleParameter2D* MaterialIdentitySample =
        AddExpression(
            NewObject<UMaterialExpressionTextureSampleParameter2D>(Material),
            -620,
            -200);
    MaterialIdentitySample->ParameterName = TEXT("AtlasMaterialIdentity");
    MaterialIdentitySample->Texture = MaterialIdentityTexture;
    MaterialIdentitySample->SamplerType = SAMPLERTYPE_LinearGrayscale;
    MaterialIdentitySample->Coordinates.Expression = AtlasUv;
    UMaterialExpressionComponentMask* AtlasFoliageMask =
        AddExpression(NewObject<UMaterialExpressionComponentMask>(Material), -420, -180);
    AtlasFoliageMask->Input.Expression = MaterialIdentitySample;
    AtlasFoliageMask->R = true;
    UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    UMaterialExpression* ConditionedColor = BaseColorSample;
    if (bUseColorCorrectShading)
    {
        UMaterialExpressionVectorParameter* AtlasColorGain =
            AddExpression(NewObject<UMaterialExpressionVectorParameter>(Material), -300, -520);
        AtlasColorGain->ParameterName = TEXT("AtlasColorGain");
        AtlasColorGain->DefaultValue = AtlasColorGainDefault;
        UMaterialExpressionMultiply* BaseGainColor =
            AddExpression(NewObject<UMaterialExpressionMultiply>(Material), -60, -540);
        BaseGainColor->A.Expression = BaseColorSample;
        BaseGainColor->B.Expression = AtlasColorGain;
        UMaterialExpressionScalarParameter* AtlasTrunkGainMultiplier =
            AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -300, -720);
        AtlasTrunkGainMultiplier->ParameterName = TEXT("AtlasTrunkGainMultiplier");
        AtlasTrunkGainMultiplier->DefaultValue = 1.0f;
        AtlasTrunkGainMultiplier->SliderMin = 0.5f;
        AtlasTrunkGainMultiplier->SliderMax = 2.5f;
        UMaterialExpressionScalarParameter* AtlasFoliageGainMultiplier =
            AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -300, -640);
        AtlasFoliageGainMultiplier->ParameterName = TEXT("AtlasFoliageGainMultiplier");
        AtlasFoliageGainMultiplier->DefaultValue = 1.0f;
        AtlasFoliageGainMultiplier->SliderMin = 0.5f;
        AtlasFoliageGainMultiplier->SliderMax = 2.5f;
        UMaterialExpressionLinearInterpolate* MaterialGainMultiplier =
            AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), -20, -660);
        MaterialGainMultiplier->A.Expression = AtlasTrunkGainMultiplier;
        MaterialGainMultiplier->B.Expression = AtlasFoliageGainMultiplier;
        MaterialGainMultiplier->Alpha.Expression = AtlasFoliageMask;
        UMaterialExpressionMultiply* ConditionedAtlasColor =
            AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 180, -520);
        ConditionedAtlasColor->A.Expression = BaseGainColor;
        ConditionedAtlasColor->B.Expression = MaterialGainMultiplier;
        ConditionedColor = ConditionedAtlasColor;
    }
    if (bUseLitShading)
    {
        ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, ConditionedColor);
        UMaterialExpressionTextureSampleParameter2D* WorldNormalSample =
            AddExpression(
                NewObject<UMaterialExpressionTextureSampleParameter2D>(Material),
                -620,
                -80);
        WorldNormalSample->ParameterName = TEXT("AtlasWorldNormal");
        WorldNormalSample->Texture = NormalTexture;
        WorldNormalSample->SamplerType = SAMPLERTYPE_LinearColor;
        WorldNormalSample->Coordinates.Expression = AtlasUv;
        UMaterialExpressionCustom* DecodedWorldNormal =
            AddExpression(NewObject<UMaterialExpressionCustom>(Material), -300, -40);
        DecodedWorldNormal->Description = TEXT(
            "Decode the captured world-space source normal for relighting");
        DecodedWorldNormal->OutputType = CMOT_Float3;
        DecodedWorldNormal->Code =
            TEXT("return normalize(WorldNormal.rgb * 2.0 - 1.0);");
        FCustomInput& WorldNormalInput =
            DecodedWorldNormal->Inputs.AddDefaulted_GetRef();
        WorldNormalInput.InputName = TEXT("WorldNormal");
        WorldNormalInput.Input.Expression = WorldNormalSample;
        ConnectPreviewMaterialVectorInput(EditorOnlyData->Normal, DecodedWorldNormal);
        if (bFoliageLayer)
        {
            UMaterialExpressionVectorParameter* AtlasFoliageTransmissionTint =
                AddExpression(
                    NewObject<UMaterialExpressionVectorParameter>(Material),
                    180,
                    20);
            AtlasFoliageTransmissionTint->ParameterName =
                TEXT("AtlasFoliageTransmissionTint");
            AtlasFoliageTransmissionTint->DefaultValue =
                FLinearColor(0.78f, 1.0f, 0.58f, 1.0f);
            UMaterialExpressionMultiply* AtlasFoliageSubsurfaceColor =
                AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 420, 20);
            AtlasFoliageSubsurfaceColor->A.Expression = ConditionedColor;
            AtlasFoliageSubsurfaceColor->B.Expression =
                AtlasFoliageTransmissionTint;
            ConnectPreviewMaterialColorInput(
                EditorOnlyData->SubsurfaceColor,
                AtlasFoliageSubsurfaceColor);
        }

        UMaterialExpressionScalarParameter* AtlasTrunkRoughness =
            AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -60, 180);
        AtlasTrunkRoughness->ParameterName = TEXT("AtlasTrunkRoughness");
        AtlasTrunkRoughness->DefaultValue = bTrunkLayer ? 0.62f : 0.68f;
        AtlasTrunkRoughness->SliderMin = 0.0f;

        AtlasTrunkRoughness->SliderMax = 1.0f;
        UMaterialExpressionScalarParameter* AtlasFoliageRoughness =
            AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -60, 260);
        AtlasFoliageRoughness->ParameterName = TEXT("AtlasFoliageRoughness");
        AtlasFoliageRoughness->DefaultValue = bFoliageLayer ? 0.72f : 0.68f;
        AtlasFoliageRoughness->SliderMin = 0.0f;
        AtlasFoliageRoughness->SliderMax = 1.0f;
        UMaterialExpressionLinearInterpolate* Roughness =
            AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 180, 180);
        Roughness->A.Expression = AtlasTrunkRoughness;
        Roughness->B.Expression = AtlasFoliageRoughness;
        Roughness->Alpha.Expression = AtlasFoliageMask;
        UMaterialExpressionScalarParameter* AtlasTrunkSpecular =
            AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -60, 340);
        AtlasTrunkSpecular->ParameterName = TEXT("AtlasTrunkSpecular");
        AtlasTrunkSpecular->DefaultValue = bTrunkLayer ? 0.12f : 0.18f;
        AtlasTrunkSpecular->SliderMin = 0.0f;
        AtlasTrunkSpecular->SliderMax = 1.0f;
        UMaterialExpressionScalarParameter* AtlasFoliageSpecular =
            AddExpression(NewObject<UMaterialExpressionScalarParameter>(Material), -60, 420);
        AtlasFoliageSpecular->ParameterName = TEXT("AtlasFoliageSpecular");
        AtlasFoliageSpecular->DefaultValue = 0.18f;
        AtlasFoliageSpecular->SliderMin = 0.0f;
        AtlasFoliageSpecular->SliderMax = 1.0f;
        UMaterialExpressionLinearInterpolate* Specular =
            AddExpression(NewObject<UMaterialExpressionLinearInterpolate>(Material), 180, 300);
        Specular->A.Expression = AtlasTrunkSpecular;
        Specular->B.Expression = AtlasFoliageSpecular;
        Specular->Alpha.Expression = AtlasFoliageMask;
        UMaterialExpressionConstant* AmbientOcclusion =
            AddExpression(NewObject<UMaterialExpressionConstant>(Material), 180, 340);
        AmbientOcclusion->R = 1.0f;
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, Roughness);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);
        ConnectPreviewMaterialScalarInput(
            EditorOnlyData->AmbientOcclusion,
            AmbientOcclusion);
    }
    else
    {
        ConnectPreviewMaterialColorInput(EditorOnlyData->EmissiveColor, ConditionedColor);
    }
    UMaterialExpression* FinalOpacity = OpacitySample;
    if (bTrunkLayer || bFoliageLayer)
    {
        UMaterialExpression* LayerIdentity = AtlasFoliageMask;
        if (bTrunkLayer)
        {
            UMaterialExpressionOneMinus* AtlasTrunkMask = AddExpression(
                NewObject<UMaterialExpressionOneMinus>(Material),
                -180,
                -260);
            AtlasTrunkMask->Input.Expression = AtlasFoliageMask;
            LayerIdentity = AtlasTrunkMask;
        }
        UMaterialExpressionMultiply* LayerOpacity =
            AddExpression(NewObject<UMaterialExpressionMultiply>(Material), 40, -280);
        LayerOpacity->A.Expression = OpacitySample;
        LayerOpacity->B.Expression = LayerIdentity;
        FinalOpacity = LayerOpacity;
    }
    if (bEnableComplementaryTransition)
    {
        FinalOpacity = AddComplementaryScreenDitherOpacity(
            Material,
            FinalOpacity,
            0,
            false,
            0.0f,
            -120,
            -300);
    }
    ConnectPreviewMaterialScalarInput(EditorOnlyData->OpacityMask, FinalOpacity);
    ConnectPreviewMaterialVectorInput(EditorOnlyData->WorldPositionOffset, BillboardOffset);

    Material->PostEditChange();
    Material->MarkPackageDirty();
    Package->MarkPackageDirty();
    Material->ForceRecompileForRendering();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
    }
    FMaterialResource* MaterialResource = Material->GetMaterialResource(GMaxRHIShaderPlatform);
    if (MaterialResource && !MaterialResource->IsGameThreadShaderMapComplete())
    {
        MaterialResource->SubmitCompileJobs_GameThread(EShaderCompileJobPriority::High);
        MaterialResource->FinishCompilation();
        if (GShaderCompilingManager)
        {
            GShaderCompilingManager->ProcessAsyncResults(false, true);
        }
        MaterialResource->IsCompilationFinished();
    }
    MaterialResource = Material->GetMaterialResource(GMaxRHIShaderPlatform);
    if (!MaterialResource ||
        Material->IsCompilingOrHadCompileError(GMaxRHIShaderPlatform) ||
        !MaterialResource->GetCompileErrors().IsEmpty())
    {
        UE_LOG(
            LogRaftSimEditor,
            Warning,
            TEXT("Local PVE atlas material shader gate failed for %s (resource=%s, compiling_or_error=%s, valid_shader_map=%s, errors=%d)."),
            *ObjectPath,
            MaterialResource ? TEXT("true") : TEXT("false"),
            Material->IsCompilingOrHadCompileError(GMaxRHIShaderPlatform) ? TEXT("true") : TEXT("false"),
            MaterialResource && MaterialResource->HasValidGameThreadShaderMap() ? TEXT("true") : TEXT("false"),
            MaterialResource ? MaterialResource->GetCompileErrors().Num() : -1);
        OutSummary += FString::Printf(
            TEXT("Local PVE atlas material failed shader validation for %s: %s\n"),
            *ObjectPath,
            MaterialResource
                ? *FString::Join(MaterialResource->GetCompileErrors(), TEXT(" | "))
                : TEXT("no material resource"));
        return nullptr;
    }
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath,
        FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
    {
        OutSummary += FString::Printf(TEXT("Could not save local PVE atlas material %s.\n"), *ObjectPath);
        return nullptr;
    }
    OutSummary += FString::Printf(TEXT("Saved local PVE atlas material %s.\n"), *ObjectPath);
    return Material;
}

bool BakeFutaleufuCypressMultiViewAtlas(
    UWorld* World,
    AActor* TrunkActor,
    AActor* FoliageActor,
    const FString& VariantId,
    const FString& AssetToken,
    const FString& LocalSavedNamespace,
    const FString& LocalReviewNamespace,
    bool bUseColorCorrectHlod,
    const FLinearColor& AtlasColorGain,
    bool bDeterministicValidationCapture,
    float AzimuthOffsetDegrees,
    bool bUsePerspectiveCapture,
    float RequestedPerspectiveCaptureRadiusCm,

    bool bUseDepthParallax,
    bool bEnableComplementaryTransition,
    int32 RequestedTileResolution,
    FRaftSimPveMultiViewAtlasBakeResult& OutResult,
    FString& OutSummary)
{
    OutResult = FRaftSimPveMultiViewAtlasBakeResult();
    if (!World || !TrunkActor || !FoliageActor)
    {
        OutSummary += TEXT("Multi-view atlas bake requires the live trunk and foliage actors.\n");
        return false;
    }
    if (RequestedTileResolution != 512 && RequestedTileResolution != 1024)
    {
        OutSummary += TEXT("Multi-view atlas tile resolution must be 512 or 1024.\n");
        return false;
    }
    if (!FMath::IsFinite(AzimuthOffsetDegrees) ||
        FMath::Abs(AzimuthOffsetDegrees) > 22.5f)
    {
        OutSummary += TEXT("Multi-view atlas azimuth offset must be finite and within half a frame.\n");
        return false;
    }
    if (bUsePerspectiveCapture &&
        (!FMath::IsFinite(RequestedPerspectiveCaptureRadiusCm) ||
         RequestedPerspectiveCaptureRadiusCm < 100.0f))
    {
        OutSummary += TEXT("Perspective multi-view capture radius must be finite and positive.\n");
        return false;
    }
    if (bUseDepthParallax && !bUsePerspectiveCapture)
    {
        OutSummary += TEXT("Depth-aware multi-view proxy requires perspective capture.\n");
        return false;
    }
    const int32 TileResolution = RequestedTileResolution;
    constexpr int32 AtlasGrid = 4;
    const int32 AtlasResolution = TileResolution * AtlasGrid;
    constexpr int32 AzimuthViewCount = 8;
    constexpr int32 ElevationViewCount = 2;
    constexpr int32 ViewCount = AzimuthViewCount * ElevationViewCount;
    static const float ElevationDegrees[ElevationViewCount] = {0.0f, 25.0f};
    OutResult.TileResolution = TileResolution;
    OutResult.AtlasResolution = AtlasResolution;
    OutResult.ViewCount = ViewCount;
    OutResult.ColorGain = AtlasColorGain;
    OutResult.AzimuthOffsetDegrees = AzimuthOffsetDegrees;

    FBox SourceBounds(EForceInit::ForceInit);
    SourceBounds += TrunkActor->GetComponentsBoundingBox(true);
    SourceBounds += FoliageActor->GetComponentsBoundingBox(true);
    if (!SourceBounds.IsValid)
    {
        OutSummary += TEXT("Multi-view atlas source bounds are invalid.\n");
        return false;
    }
    const FVector Target = SourceBounds.GetCenter();
    const FVector SourceSize = SourceBounds.GetSize();
    const float OrthoWidth = FMath::Max3(SourceSize.X, SourceSize.Y, SourceSize.Z) * 1.12f;
    const float CaptureRadius = bUsePerspectiveCapture
        ? RequestedPerspectiveCaptureRadiusCm
        : FMath::Max(OrthoWidth * 2.25f, 5000.0f);
    const float PerspectiveHorizontalFovDegrees = bUsePerspectiveCapture
        ? FMath::RadiansToDegrees(2.0f * FMath::Atan(OrthoWidth / (2.0f * CaptureRadius)))
        : 0.0f;
    const float DepthParallaxScaleCm = bUseDepthParallax
        ? FMath::Max(SourceSize.X, SourceSize.Y)
        : 0.0f;
    OutResult.OrthoWidthCm = OrthoWidth;
    OutResult.bPerspectiveCapture = bUsePerspectiveCapture;
    OutResult.CaptureRadiusCm = CaptureRadius;
    OutResult.PerspectiveHorizontalFovDegrees = PerspectiveHorizontalFovDegrees;
    OutResult.bDepthParallaxEnabled = bUseDepthParallax;
    OutResult.DepthParallaxScaleCm = DepthParallaxScaleCm;
    OutResult.bComplementaryTransitionEnabled = bEnableComplementaryTransition;

    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
    }
    World->SendAllEndOfFrameUpdates();
    FlushRenderingCommands();

    UTextureRenderTarget2D* RenderTarget = NewObject<UTextureRenderTarget2D>(
        GetTransientPackage(), NAME_None, RF_Transient);
    UTextureRenderTarget2D* ColorRenderTarget = NewObject<UTextureRenderTarget2D>(
        GetTransientPackage(), NAME_None, RF_Transient);
    ASceneCapture2D* SceneCapture = World->SpawnActor<ASceneCapture2D>(
        ASceneCapture2D::StaticClass(), Target, FRotator::ZeroRotator);
    if (!RenderTarget || !ColorRenderTarget || !SceneCapture ||
        !SceneCapture->GetCaptureComponent2D())
    {
        OutSummary += TEXT("Could not allocate multi-view atlas scene capture.\n");
        if (SceneCapture)
        {
            SceneCapture->Destroy();
        }
        return false;
    }
    RenderTarget->RenderTargetFormat = RTF_RGBA16f;
    RenderTarget->ClearColor = FLinearColor(0.0f, 0.0f, 0.0f, 1.0f);
    RenderTarget->InitAutoFormat(TileResolution, TileResolution);
    RenderTarget->UpdateResourceImmediate(true);
    ColorRenderTarget->RenderTargetFormat = RTF_RGBA8_SRGB;
    ColorRenderTarget->ClearColor = FLinearColor::Transparent;
    ColorRenderTarget->InitAutoFormat(TileResolution, TileResolution);
    ColorRenderTarget->UpdateResourceImmediate(true);

    USceneCaptureComponent2D* CaptureComponent = SceneCapture->GetCaptureComponent2D();
    CaptureComponent->TextureTarget = RenderTarget;
    CaptureComponent->ProjectionType = bUsePerspectiveCapture
        ? ECameraProjectionMode::Perspective
        : ECameraProjectionMode::Orthographic;
    CaptureComponent->OrthoWidth = OrthoWidth;
    if (bUsePerspectiveCapture)
    {
        CaptureComponent->FOVAngle = PerspectiveHorizontalFovDegrees;
    }
    CaptureComponent->PrimitiveRenderMode =
        ESceneCapturePrimitiveRenderMode::PRM_RenderScenePrimitives;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (Actor && Actor != TrunkActor && Actor != FoliageActor &&
            Actor->FindComponentByClass<UMeshComponent>())
        {
            CaptureComponent->HiddenActors.Add(Actor);
        }
    }
    CaptureComponent->bCaptureEveryFrame = false;
    CaptureComponent->bCaptureOnMovement = false;
    CaptureComponent->bAlwaysPersistRenderingState = true;
    CaptureComponent->bExcludeFromSceneTextureExtents = true;
    CaptureComponent->ShowFlags.SetSelection(false);
    CaptureComponent->ShowFlags.SetModeWidgets(false);
    CaptureComponent->ShowFlags.SetCompositeEditorPrimitives(false);
    CaptureComponent->ShowFlags.SetAtmosphere(false);
    CaptureComponent->ShowFlags.SetFog(false);
    if (bDeterministicValidationCapture)
    {
        CaptureComponent->ShowFlags.SetLighting(false);
        CaptureComponent->ShowFlags.SetPostProcessing(false);
        CaptureComponent->ShowFlags.SetAntiAliasing(false);
        CaptureComponent->ShowFlags.SetTemporalAA(false);
        CaptureComponent->ShowFlags.SetMotionBlur(false);
        CaptureComponent->ShowFlags.SetEyeAdaptation(false);
        CaptureComponent->ShowFlags.SetAmbientOcclusion(false);
        CaptureComponent->ShowFlags.SetGlobalIllumination(false);
        CaptureComponent->ShowFlags.SetLumenGlobalIllumination(false);
        CaptureComponent->ShowFlags.SetLumenReflections(false);
        CaptureComponent->ShowFlags.SetScreenSpaceReflections(false);
        CaptureComponent->ShowFlags.SetReflectionEnvironment(false);
    }
    const FRaftSimPhotographicCaptureSettings AtlasCaptureSettings =
        GetPhotographicCaptureSettings(TEXT("futaleufu_terminator"));
    CaptureComponent->PostProcessSettings.bOverride_AutoExposureMethod = true;
    CaptureComponent->PostProcessSettings.AutoExposureMethod = AEM_Manual;
    CaptureComponent->PostProcessSettings.bOverride_AutoExposureBias = true;
    CaptureComponent->PostProcessSettings.AutoExposureBias = AtlasCaptureSettings.ExposureBias;
    CaptureComponent->PostProcessSettings.bOverride_AutoExposureApplyPhysicalCameraExposure = true;
    CaptureComponent->PostProcessSettings.AutoExposureApplyPhysicalCameraExposure = 0;
    CaptureComponent->PostProcessSettings.bOverride_ColorSaturation = true;
    CaptureComponent->PostProcessSettings.ColorSaturation = FVector4(
        AtlasCaptureSettings.Saturation,
        AtlasCaptureSettings.Saturation,
        AtlasCaptureSettings.Saturation,
        1.0f);
    CaptureComponent->PostProcessSettings.bOverride_ColorContrast = true;
    CaptureComponent->PostProcessSettings.ColorContrast = FVector4(
        AtlasCaptureSettings.Contrast,
        AtlasCaptureSettings.Contrast,
        AtlasCaptureSettings.Contrast,

        1.0f);
    CaptureComponent->PostProcessBlendWeight = 1.0f;

    TArray<FColor> BaseColorAtlas;
    TArray<FColor> AlbedoAtlas;
    TArray<FColor> NormalAtlas;
    TArray<FColor> OpacityAtlas;
    TArray<FColor> DepthAtlas;
    TArray<FColor> MaterialIdentityAtlas;
    BaseColorAtlas.Init(FColor(0, 0, 0, 0), AtlasResolution * AtlasResolution);
    AlbedoAtlas.Init(FColor(0, 0, 0, 0), AtlasResolution * AtlasResolution);
    NormalAtlas.Init(FColor(128, 128, 255, 0), AtlasResolution * AtlasResolution);
    OpacityAtlas.Init(FColor::Black, AtlasResolution * AtlasResolution);
    DepthAtlas.Init(FColor(0, 0, 0, 0), AtlasResolution * AtlasResolution);
    MaterialIdentityAtlas.Init(FColor(0, 0, 0, 0), AtlasResolution * AtlasResolution);
    bool bUsedInverseOpacity = true;
    bool bAllPassesCaptured = true;

    auto CapturePass = [CaptureComponent, RenderTarget, TileResolution](
                           ESceneCaptureSource Source,
                           TArray<FLinearColor>& OutPixels)
    {
        CaptureComponent->CaptureSource = Source;
        CaptureComponent->CaptureScene();
        FlushRenderingCommands();
        FTextureRenderTargetResource* Resource = RenderTarget->GameThread_GetRenderTargetResource();
        return Resource && Resource->ReadLinearColorPixels(
            OutPixels,
            FReadSurfaceDataFlags(RCM_MinMax, CubeFace_MAX)) &&
            OutPixels.Num() == TileResolution * TileResolution;
    };
    auto CaptureColorPass = [
                                CaptureComponent,
                                ColorRenderTarget,
                                RenderTarget,
                                TileResolution](
                                TArray<FColor>& OutPixels)
    {
        CaptureComponent->TextureTarget = ColorRenderTarget;
        CaptureComponent->CaptureSource = SCS_FinalColorLDR;
        CaptureComponent->CaptureScene();
        FlushRenderingCommands();
        FTextureRenderTargetResource* Resource =
            ColorRenderTarget->GameThread_GetRenderTargetResource();
        const bool bRead = Resource && Resource->ReadPixels(
            OutPixels,
            FReadSurfaceDataFlags(RCM_UNorm, CubeFace_MAX)) &&
            OutPixels.Num() == TileResolution * TileResolution;
        CaptureComponent->TextureTarget = RenderTarget;
        return bRead;
    };

    TrunkActor->SetActorHiddenInGame(false);
    FoliageActor->SetActorHiddenInGame(false);
    for (int32 ElevationIndex = 0; ElevationIndex < ElevationViewCount; ++ElevationIndex)
    {
        const float ElevationRadians = FMath::DegreesToRadians(ElevationDegrees[ElevationIndex]);
        for (int32 AzimuthIndex = 0; AzimuthIndex < AzimuthViewCount; ++AzimuthIndex)
        {
            const int32 ViewIndex = ElevationIndex * AzimuthViewCount + AzimuthIndex;
            const float AzimuthRadians =
                FMath::DegreesToRadians(AzimuthOffsetDegrees) +
                2.0f * PI * static_cast<float>(AzimuthIndex) /
                    static_cast<float>(AzimuthViewCount);
            const FVector CameraDirection(
                FMath::Cos(AzimuthRadians) * FMath::Cos(ElevationRadians),
                FMath::Sin(AzimuthRadians) * FMath::Cos(ElevationRadians),
                FMath::Sin(ElevationRadians));
            const FVector CameraLocation = Target + CameraDirection * CaptureRadius;
            SceneCapture->SetActorLocationAndRotation(
                CameraLocation,
                (Target - CameraLocation).Rotation());

            TArray<FLinearColor> SceneColorPixels;
            TArray<FLinearColor> BaseColorPixels;
            TArray<FLinearColor> NormalPixels;
            TArray<FLinearColor> DepthPixels;
            TArray<FLinearColor> TrunkSceneColorPixels;
            TArray<FLinearColor> TrunkDepthPixels;
            TArray<FLinearColor> FoliageSceneColorPixels;
            TArray<FLinearColor> FoliageDepthPixels;
            TArray<FColor> FinalColorPixels;
            bool bViewCaptured =
                CapturePass(SCS_SceneColorHDR, SceneColorPixels) &&
                CapturePass(SCS_BaseColor, BaseColorPixels) &&
                CapturePass(SCS_Normal, NormalPixels) &&
                CapturePass(SCS_SceneDepth, DepthPixels) &&
                CaptureColorPass(FinalColorPixels);
            FoliageActor->SetActorHiddenInGame(true);
            World->SendAllEndOfFrameUpdates();
            FlushRenderingCommands();
            bViewCaptured &=
                CapturePass(SCS_SceneColorHDR, TrunkSceneColorPixels) &&
                CapturePass(SCS_SceneDepth, TrunkDepthPixels);
            FoliageActor->SetActorHiddenInGame(false);
            TrunkActor->SetActorHiddenInGame(true);
            World->SendAllEndOfFrameUpdates();
            FlushRenderingCommands();
            bViewCaptured &=
                CapturePass(SCS_SceneColorHDR, FoliageSceneColorPixels) &&
                CapturePass(SCS_SceneDepth, FoliageDepthPixels);
            TrunkActor->SetActorHiddenInGame(false);
            World->SendAllEndOfFrameUpdates();
            FlushRenderingCommands();
            bAllPassesCaptured &= bViewCaptured;
            if (!bViewCaptured)
            {
                continue;
            }

            TArray<float> Opacity;
            TArray<float> TrunkOpacity;
            TArray<float> FoliageOpacity;
            Opacity.SetNumUninitialized(TileResolution * TileResolution);
            TrunkOpacity.SetNumUninitialized(TileResolution * TileResolution);
            FoliageOpacity.SetNumUninitialized(TileResolution * TileResolution);
            int32 InverseOpacityCoveredPixels = 0;
            for (int32 PixelIndex = 0; PixelIndex < Opacity.Num(); ++PixelIndex)
            {
                Opacity[PixelIndex] = FMath::Clamp(1.0f - SceneColorPixels[PixelIndex].A, 0.0f, 1.0f);
                TrunkOpacity[PixelIndex] = FMath::Clamp(
                    1.0f - TrunkSceneColorPixels[PixelIndex].A,
                    0.0f,
                    1.0f);
                FoliageOpacity[PixelIndex] = FMath::Clamp(
                    1.0f - FoliageSceneColorPixels[PixelIndex].A,
                    0.0f,
                    1.0f);
                InverseOpacityCoveredPixels += Opacity[PixelIndex] > 0.02f ? 1 : 0;
            }
            float Coverage = static_cast<float>(InverseOpacityCoveredPixels) /
                static_cast<float>(Opacity.Num());
            if (Coverage < 0.002f || Coverage > 0.85f)
            {
                bUsedInverseOpacity = false;
                int32 BaseColorCoveredPixels = 0;
                for (int32 PixelIndex = 0; PixelIndex < Opacity.Num(); ++PixelIndex)
                {
                    const FLinearColor& Base = BaseColorPixels[PixelIndex];
                    const float BaseMagnitude = FMath::Abs(Base.R) + FMath::Abs(Base.G) + FMath::Abs(Base.B);
                    Opacity[PixelIndex] = BaseMagnitude > 0.002f ? 1.0f : 0.0f;
                    BaseColorCoveredPixels += Opacity[PixelIndex] > 0.02f ? 1 : 0;
                }
                Coverage = static_cast<float>(BaseColorCoveredPixels) /
                    static_cast<float>(Opacity.Num());
            }

            OutResult.MinimumCoverage = FMath::Min(OutResult.MinimumCoverage, Coverage);
            OutResult.MaximumCoverage = FMath::Max(OutResult.MaximumCoverage, Coverage);

            float MinimumDepth = TNumericLimits<float>::Max();
            float MaximumDepth = TNumericLimits<float>::Lowest();
            for (int32 PixelIndex = 0; PixelIndex < Opacity.Num(); ++PixelIndex)
            {
                const float Depth = DepthPixels[PixelIndex].R;
                if (Opacity[PixelIndex] > 0.02f && FMath::IsFinite(Depth) && Depth > 0.0f)
                {
                    MinimumDepth = FMath::Min(MinimumDepth, Depth);
                    MaximumDepth = FMath::Max(MaximumDepth, Depth);
                }
            }
            const float DepthRange = MaximumDepth > MinimumDepth
                ? MaximumDepth - MinimumDepth
                : 1.0f;
            const int32 TileOriginX = (ViewIndex % AtlasGrid) * TileResolution;
            const int32 TileOriginY = (ViewIndex / AtlasGrid) * TileResolution;
            for (int32 Y = 0; Y < TileResolution; ++Y)
            {
                for (int32 X = 0; X < TileResolution; ++X)
                {
                    const int32 TileIndex = Y * TileResolution + X;
                    const int32 AtlasIndex =
                        (TileOriginY + Y) * AtlasResolution + TileOriginX + X;
                    const uint8 Alpha = static_cast<uint8>(
                        FMath::RoundToInt(Opacity[TileIndex] * 255.0f));
                    FColor BaseColor = FinalColorPixels[TileIndex];
                    BaseColor.A = Alpha;
                    BaseColorAtlas[AtlasIndex] = BaseColor;
                    FColor AlbedoColor =
                        BaseColorPixels[TileIndex].GetClamped().ToFColor(true);
                    AlbedoColor.A = Alpha;
                    AlbedoAtlas[AtlasIndex] = AlbedoColor;
                    FColor NormalColor = NormalPixels[TileIndex].GetClamped().ToFColor(false);
                    NormalColor.A = Alpha;
                    NormalAtlas[AtlasIndex] = NormalColor;
                    OpacityAtlas[AtlasIndex] = FColor(Alpha, Alpha, Alpha, 255);
                    const float NormalizedDepth = FMath::Clamp(
                        1.0f - ((DepthPixels[TileIndex].R - MinimumDepth) / DepthRange),
                        0.0f,
                        1.0f);
                    const uint8 DepthValue = static_cast<uint8>(
                        FMath::RoundToInt(NormalizedDepth * 255.0f));
                    DepthAtlas[AtlasIndex] = FColor(DepthValue, DepthValue, DepthValue, Alpha);
                    const bool bTrunkCovered = TrunkOpacity[TileIndex] > 0.02f;
                    const bool bFoliageCovered = FoliageOpacity[TileIndex] > 0.02f;
                    bool bFoliageOwnsPixel = bFoliageCovered &&
                        (!bTrunkCovered ||
                         FoliageDepthPixels[TileIndex].R <=
                             TrunkDepthPixels[TileIndex].R + 0.5f);
                    if (Opacity[TileIndex] > 0.02f &&
                        !bTrunkCovered && !bFoliageCovered)
                    {
                        const FLinearColor& Base = BaseColorPixels[TileIndex];
                        bFoliageOwnsPixel = Base.G > FMath::Max(Base.R, Base.B);
                        ++OutResult.MaterialIdentityFallbackPixelCount;
                    }
                    const uint8 MaterialIdentity = bFoliageOwnsPixel ? 255 : 0;
                    MaterialIdentityAtlas[AtlasIndex] = FColor(
                        MaterialIdentity,
                        MaterialIdentity,
                        MaterialIdentity,
                        Alpha);
                }
            }
            DilatePveAtlasTileRgb(
                BaseColorAtlas, AtlasResolution, TileOriginX, TileOriginY, TileResolution, 12);
            DilatePveAtlasTileRgb(
                AlbedoAtlas, AtlasResolution, TileOriginX, TileOriginY, TileResolution, 12);
            DilatePveAtlasTileRgb(
                NormalAtlas, AtlasResolution, TileOriginX, TileOriginY, TileResolution, 12);
            DilatePveAtlasTileRgb(
                DepthAtlas, AtlasResolution, TileOriginX, TileOriginY, TileResolution, 12);
            DilatePveAtlasTileRgb(
                MaterialIdentityAtlas,
                AtlasResolution,
                TileOriginX,
                TileOriginY,
                TileResolution,
                12);
        }
    }
    SceneCapture->Destroy();
    RenderTarget->ReleaseResource();
    ColorRenderTarget->ReleaseResource();
    OutResult.OpacitySource = bUsedInverseOpacity
        ? TEXT("SceneColorHDR inverse opacity alpha")
        : TEXT("SceneColorHDR inverse opacity with BaseColor occupancy fallback");
    if (!bAllPassesCaptured || OutResult.MinimumCoverage < 0.002f ||
        OutResult.MaximumCoverage > 0.85f)
    {
        OutSummary += FString::Printf(
            TEXT("Multi-view atlas capture failed pass or coverage checks (%.6f to %.6f).\n"),
            OutResult.MinimumCoverage,
            OutResult.MaximumCoverage);
        return false;
    }

    const FString VariantLower = VariantId.ToLower();
    const FString OutputDirectory = FPaths::Combine(
        FPaths::ProjectSavedDir(), TEXT("RaftSimPveReview"), LocalSavedNamespace);
    const FString RelativeOutputRoot = FString::Printf(
        TEXT("unreal/Saved/RaftSimPveReview/%s/%s_multiview_atlas"),
        *LocalSavedNamespace,
        *VariantLower);
    OutResult.BaseColorRelativePath = RelativeOutputRoot + TEXT("_base_color_opacity.png");
    OutResult.AlbedoRelativePath = RelativeOutputRoot + TEXT("_albedo_opacity.png");
    OutResult.NormalRelativePath = RelativeOutputRoot + TEXT("_world_normal.png");
    OutResult.OpacityRelativePath = RelativeOutputRoot + TEXT("_opacity.png");
    OutResult.DepthRelativePath = RelativeOutputRoot + TEXT("_depth.png");
    OutResult.MaterialIdentityRelativePath =
        RelativeOutputRoot + TEXT("_material_identity.png");
    const FString BaseColorAbsolutePath = FPaths::Combine(
        OutputDirectory, VariantLower + TEXT("_multiview_atlas_base_color_opacity.png"));
    const FString AlbedoAbsolutePath = FPaths::Combine(
        OutputDirectory, VariantLower + TEXT("_multiview_atlas_albedo_opacity.png"));
    const FString NormalAbsolutePath = FPaths::Combine(
        OutputDirectory, VariantLower + TEXT("_multiview_atlas_world_normal.png"));
    const FString OpacityAbsolutePath = FPaths::Combine(
        OutputDirectory, VariantLower + TEXT("_multiview_atlas_opacity.png"));
    const FString DepthAbsolutePath = FPaths::Combine(
        OutputDirectory, VariantLower + TEXT("_multiview_atlas_depth.png"));
    const FString MaterialIdentityAbsolutePath = FPaths::Combine(
        OutputDirectory,
        VariantLower + TEXT("_multiview_atlas_material_identity.png"));
    OutResult.bAtlasFilesSaved =
        SavePveAtlasPng(BaseColorAbsolutePath, AtlasResolution, AtlasResolution, BaseColorAtlas) &&
        SavePveAtlasPng(AlbedoAbsolutePath, AtlasResolution, AtlasResolution, AlbedoAtlas) &&
        SavePveAtlasPng(NormalAbsolutePath, AtlasResolution, AtlasResolution, NormalAtlas) &&
        SavePveAtlasPng(OpacityAbsolutePath, AtlasResolution, AtlasResolution, OpacityAtlas) &&
        SavePveAtlasPng(DepthAbsolutePath, AtlasResolution, AtlasResolution, DepthAtlas) &&
        SavePveAtlasPng(
            MaterialIdentityAbsolutePath,
            AtlasResolution,
            AtlasResolution,
            MaterialIdentityAtlas);
    if (!OutResult.bAtlasFilesSaved)
    {
        OutSummary += TEXT("One or more multi-view atlas PNG files failed to save.\n");
        return false;
    }
    OutResult.BaseColorDigest = LexToString(FMD5Hash::HashFile(*BaseColorAbsolutePath));
    OutResult.AlbedoDigest = LexToString(FMD5Hash::HashFile(*AlbedoAbsolutePath));
    OutResult.NormalDigest = LexToString(FMD5Hash::HashFile(*NormalAbsolutePath));
    OutResult.OpacityDigest = LexToString(FMD5Hash::HashFile(*OpacityAbsolutePath));
    OutResult.DepthDigest = LexToString(FMD5Hash::HashFile(*DepthAbsolutePath));
    OutResult.MaterialIdentityDigest =
        LexToString(FMD5Hash::HashFile(*MaterialIdentityAbsolutePath));

    const FString AtlasPackageRoot = FString::Printf(
        TEXT("/Game/RaftSim/Environment/GeneratedLocalReview/%s/MultiViewAtlas"),
        *LocalReviewNamespace);
    OutResult.BaseColorAssetPath = FString::Printf(
        TEXT("%s/T_%s_%s_MultiViewBaseColorOpacity"),
        *AtlasPackageRoot, *AssetToken, *VariantLower);
    OutResult.AlbedoAssetPath = FString::Printf(
        TEXT("%s/T_%s_%s_MultiViewAlbedoOpacity"),
        *AtlasPackageRoot, *AssetToken, *VariantLower);
    OutResult.NormalAssetPath = FString::Printf(
        TEXT("%s/T_%s_%s_MultiViewWorldNormal"),
        *AtlasPackageRoot, *AssetToken, *VariantLower);
    OutResult.OpacityAssetPath = FString::Printf(
        TEXT("%s/T_%s_%s_MultiViewOpacity"),
        *AtlasPackageRoot, *AssetToken, *VariantLower);
    OutResult.DepthAssetPath = FString::Printf(
        TEXT("%s/T_%s_%s_MultiViewDepth"),
        *AtlasPackageRoot, *AssetToken, *VariantLower);
    OutResult.MaterialIdentityAssetPath = FString::Printf(
        TEXT("%s/T_%s_%s_MultiViewMaterialIdentity"),
        *AtlasPackageRoot, *AssetToken, *VariantLower);
    UTexture2D* BaseColorTexture = CreateOrUpdateLocalPveAtlasTexture(
        OutResult.BaseColorAssetPath,

        BaseColorAtlas,
        AtlasResolution,
        TC_Default,
        true,
        true,
        OutSummary);
    UTexture2D* AlbedoTexture = CreateOrUpdateLocalPveAtlasTexture(
        OutResult.AlbedoAssetPath,
        AlbedoAtlas,
        AtlasResolution,
        TC_Default,
        true,
        true,
        OutSummary);
    UTexture2D* NormalTexture = CreateOrUpdateLocalPveAtlasTexture(
        OutResult.NormalAssetPath,
        NormalAtlas,
        AtlasResolution,
        TC_VectorDisplacementmap,
        false,
        false,
        OutSummary);
    UTexture2D* OpacityTexture = CreateOrUpdateLocalPveAtlasTexture(
        OutResult.OpacityAssetPath,
        OpacityAtlas,
        AtlasResolution,
        TC_Grayscale,
        false,
        false,
        OutSummary);
    UTexture2D* DepthTexture = CreateOrUpdateLocalPveAtlasTexture(
        OutResult.DepthAssetPath,
        DepthAtlas,
        AtlasResolution,
        TC_Grayscale,
        false,
        false,
        OutSummary);
    UTexture2D* MaterialIdentityTexture = CreateOrUpdateLocalPveAtlasTexture(
        OutResult.MaterialIdentityAssetPath,
        MaterialIdentityAtlas,
        AtlasResolution,
        TC_Grayscale,
        false,
        false,
        OutSummary);
    OutResult.bTextureAssetsSaved =
        BaseColorTexture && AlbedoTexture && NormalTexture && OpacityTexture &&
        DepthTexture && MaterialIdentityTexture;
    if (!OutResult.bTextureAssetsSaved)
    {
        return false;
    }
    TArray<UTexture*> AtlasTextures = {
        BaseColorTexture,
        AlbedoTexture,
        NormalTexture,
        OpacityTexture,
        DepthTexture,
        MaterialIdentityTexture};
    FTextureCompilingManager::Get().FinishCompilation(AtlasTextures);
    for (UTexture* Texture : AtlasTextures)
    {
        Texture->UpdateResource();
    }
    FlushRenderingCommands();

    OutResult.MaterialAssetPath = FString::Printf(
        TEXT("%s/M_%s_%s_MultiViewHlodV2"),
        *AtlasPackageRoot, *AssetToken, *VariantLower);
    OutResult.Material = CreateOrUpdateLocalPveAtlasMaterial(
        OutResult.MaterialAssetPath,
        BaseColorTexture,
        NormalTexture,
        OpacityTexture,
        DepthTexture,
        MaterialIdentityTexture,
        bUseColorCorrectHlod,
        AtlasColorGain,
        AzimuthOffsetDegrees,
        bUseDepthParallax,
        DepthParallaxScaleCm,
        bEnableComplementaryTransition,
        false,
        EPveAtlasMaterialLayer::Combined,
        OutSummary);
    OutResult.bMaterialSaved = OutResult.Material != nullptr;
    OutResult.RelightableMaterialAssetPath = FString::Printf(
        TEXT("%s/M_%s_%s_MultiViewHlodV3Lit"),
        *AtlasPackageRoot,
        *AssetToken,
        *VariantLower);
    OutResult.RelightableMaterial = CreateOrUpdateLocalPveAtlasMaterial(
        OutResult.RelightableMaterialAssetPath,
        AlbedoTexture,
        NormalTexture,
        OpacityTexture,
        DepthTexture,
        MaterialIdentityTexture,
        true,
        FLinearColor(1.55f, 1.55f, 1.55f, 1.0f),
        AzimuthOffsetDegrees,
        bUseDepthParallax,
        DepthParallaxScaleCm,
        bEnableComplementaryTransition,
        true,
        EPveAtlasMaterialLayer::Combined,
        OutSummary);
    OutResult.bRelightableMaterialSaved =
        OutResult.RelightableMaterial != nullptr;
    OutResult.RelightableTrunkMaterialAssetPath = FString::Printf(
        TEXT("%s/M_%s_%s_MultiViewHlodV4LitTrunk"),
        *AtlasPackageRoot,
        *AssetToken,
        *VariantLower);
    OutResult.RelightableTrunkMaterial = CreateOrUpdateLocalPveAtlasMaterial(
        OutResult.RelightableTrunkMaterialAssetPath,
        AlbedoTexture,
        NormalTexture,
        OpacityTexture,
        DepthTexture,
        MaterialIdentityTexture,
        true,
        FLinearColor(1.55f, 1.55f, 1.55f, 1.0f),
        AzimuthOffsetDegrees,
        bUseDepthParallax,
        DepthParallaxScaleCm,
        bEnableComplementaryTransition,
        true,
        EPveAtlasMaterialLayer::Trunk,
        OutSummary);
    OutResult.bRelightableTrunkMaterialSaved =
        OutResult.RelightableTrunkMaterial != nullptr;
    OutResult.RelightableFoliageMaterialAssetPath = FString::Printf(
        TEXT("%s/M_%s_%s_MultiViewHlodV4LitFoliage"),
        *AtlasPackageRoot,
        *AssetToken,
        *VariantLower);
    OutResult.RelightableFoliageMaterial = CreateOrUpdateLocalPveAtlasMaterial(
        OutResult.RelightableFoliageMaterialAssetPath,
        AlbedoTexture,
        NormalTexture,
        OpacityTexture,
        DepthTexture,
        MaterialIdentityTexture,

        true,
        FLinearColor(1.55f, 1.55f, 1.55f, 1.0f),
        AzimuthOffsetDegrees,
        bUseDepthParallax,
        DepthParallaxScaleCm,
        bEnableComplementaryTransition,
        true,
        EPveAtlasMaterialLayer::Foliage,
        OutSummary);
    OutResult.bRelightableFoliageMaterialSaved =
        OutResult.RelightableFoliageMaterial != nullptr;
    UStaticMesh* ProxyMesh = LoadPreviewMesh(TEXT("/Engine/BasicShapes/Plane.Plane"));
    if (bUseDepthParallax && OutResult.Material)
    {
        constexpr int32 GridSegments = 32;
        constexpr int32 GridVerticesPerSide = GridSegments + 1;
        TArray<FVector> GridVertices;
        TArray<int32> GridTriangles;
        TArray<FVector> GridNormals;
        TArray<FVector2D> GridUVs;
        GridVertices.Reserve(GridVerticesPerSide * GridVerticesPerSide);
        GridNormals.Reserve(GridVerticesPerSide * GridVerticesPerSide);
        GridUVs.Reserve(GridVerticesPerSide * GridVerticesPerSide);
        GridTriangles.Reserve(GridSegments * GridSegments * 6);
        for (int32 Y = 0; Y <= GridSegments; ++Y)
        {
            const float V = static_cast<float>(Y) / static_cast<float>(GridSegments);
            for (int32 X = 0; X <= GridSegments; ++X)
            {
                const float U = static_cast<float>(X) / static_cast<float>(GridSegments);
                GridVertices.Add(FVector((U - 0.5f) * 100.0f, (V - 0.5f) * 100.0f, 0.0f));
                GridNormals.Add(FVector::UpVector);
                GridUVs.Add(FVector2D(U, V));
            }
        }
        for (int32 Y = 0; Y < GridSegments; ++Y)
        {
            for (int32 X = 0; X < GridSegments; ++X)
            {
                const int32 A = Y * GridVerticesPerSide + X;
                const int32 B = A + 1;
                const int32 C = A + GridVerticesPerSide;
                const int32 D = C + 1;
                GridTriangles.Append({A, C, B, B, C, D});
            }
        }
        AActor* GridSourceActor = AddPreviewProceduralMeshActor(
            World,
            TEXT("RaftSim_PveCypressDepthGridProxy_Source"),
            GridVertices,
            GridTriangles,
            GridNormals,
            GridUVs,
            FLinearColor::White,
            OutResult.Material,
            nullptr,
            false);
        const FString GridAssetPath = FString::Printf(
            TEXT("%s/SM_RaftSim_PveDepthGrid32"),
            *AtlasPackageRoot);
        ProxyMesh = ConvertNativeCanopyProceduralActorToStaticMesh(
            GridSourceActor,
            GridAssetPath,
            OutResult.Material,
            false,
            ENaniteShapePreservation::None,
            OutSummary);
        if (GridSourceActor)
        {
            GridSourceActor->Destroy();
        }
    }
    OutResult.ProxyVertexCount = ProxyMesh ? ProxyMesh->GetNumVertices(0) : 0;
    OutResult.ProxyTriangleCount = ProxyMesh ? ProxyMesh->GetNumTriangles(0) : 0;
    OutResult.ProxyActor = ProxyMesh && OutResult.Material
        ? World->SpawnActor<AStaticMeshActor>(
              AStaticMeshActor::StaticClass(),
              FTransform(
                  FRotator::ZeroRotator,
                  Target,
                  FVector(OrthoWidth / 100.0f, OrthoWidth / 100.0f, 1.0f)))
        : nullptr;
    if (OutResult.ProxyActor && OutResult.ProxyActor->GetStaticMeshComponent())
    {
        OutResult.ProxyActor->SetActorLabel(TEXT("RaftSim_PveCypressMultiViewAtlasHlod"));
        UStaticMeshComponent* Component = OutResult.ProxyActor->GetStaticMeshComponent();
        Component->SetStaticMesh(ProxyMesh);
        Component->SetMaterial(0, OutResult.Material);
        Component->SetMobility(EComponentMobility::Static);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetCastShadow(false);
        Component->BoundsScale = 2.5f;
        OutResult.ProxyActor->SetActorHiddenInGame(true);
        OutResult.bProxyActorCreated = true;
    }

    OutResult.ManifestRelativePath = FString::Printf(
        TEXT("unreal/Saved/RaftSimPveReview/%s/%s_multiview_atlas_manifest.json"),
        *LocalSavedNamespace,
        *VariantLower);
    const FString ManifestAbsolutePath = FPaths::Combine(
        OutputDirectory,
        VariantLower + TEXT("_multiview_atlas_manifest.json"));
    const FString Manifest = FString::Printf(
        TEXT("{\n")
        TEXT("  \"schema\": \"raftsim.unreal.pve_multiview_atlas.v1\",\n")
        TEXT("  \"variant\": \"%s\",\n")
        TEXT("  \"status\": \"%s\",\n")
        TEXT("  \"view_contract\": {\"type\": \"bounded_upper_hemisphere\", \"azimuth_offset_degrees\": %.6f, \"azimuth_degrees\": [%.6f, %.6f, %.6f, %.6f, %.6f, %.6f, %.6f, %.6f], \"elevation_degrees\": [0, 25], \"view_count\": 16},\n")
        TEXT("  \"atlas_contract\": {\"grid\": [4, 4], \"tile_resolution\": %d, \"atlas_resolution\": %d, \"padding_pixels\": 12, \"orthographic_width_cm\": %.6f},\n")
        TEXT("  \"projection_contract\": {\"type\": \"%s\", \"capture_radius_cm\": %.6f, \"perspective_horizontal_fov_degrees\": %.6f, \"proxy_plane_width_cm\": %.6f},\n")
        TEXT("  \"representation_shape_contract\": {\"type\": \"%s\", \"depth_parallax_enabled\": %s, \"depth_parallax_scale_cm\": %.6f, \"proxy_vertex_count\": %d, \"proxy_triangle_count\": %d},\n")
        TEXT("  \"capture_contract\": {\"source_lit_color\": \"%s\", \"relightable_albedo\": \"SCS_BaseColor linear converted to sRGB atlas texels\", \"normal\": \"SCS_Normal world space\", \"opacity\": \"%s\", \"depth\": \"SCS_SceneDepth normalized per view, near white\", \"material_identity\": \"frontmost owner from separate trunk and foliage opacity plus scene-depth passes; black trunk and white foliage\", \"material_identity_fallback_pixels\": %lld, \"primitive_filter\": \"all non-source mesh actors hidden while retaining the review light rig\"},\n")
        TEXT("  \"coverage_fraction_range\": [%.9f, %.9f],\n")
        TEXT("  \"outputs\": {\n")
        TEXT("    \"base_color_opacity\": {\"path\": \"%s\", \"md5\": \"%s\"},\n")
        TEXT("    \"albedo_opacity\": {\"path\": \"%s\", \"md5\": \"%s\"},\n")
        TEXT("    \"world_normal\": {\"path\": \"%s\", \"md5\": \"%s\"},\n")
        TEXT("    \"opacity\": {\"path\": \"%s\", \"md5\": \"%s\"},\n")
        TEXT("    \"depth\": {\"path\": \"%s\", \"md5\": \"%s\"},\n")
        TEXT("    \"material_identity\": {\"path\": \"%s\", \"md5\": \"%s\"}\n")
        TEXT("  },\n")
        TEXT("  \"assets\": {\"base_color_opacity\": \"%s\", \"albedo_opacity\": \"%s\", \"world_normal\": \"%s\", \"opacity\": \"%s\", \"depth\": \"%s\", \"material_identity\": \"%s\", \"legacy_unlit_material\": \"%s\", \"relightable_lit_material\": \"%s\", \"relightable_trunk_material\": \"%s\", \"relightable_foliage_material\": \"%s\"},\n")
        TEXT("  \"runtime_contract\": {\"geometry\": \"%s\", \"frame_selection\": \"nearest 45-degree azimuth plus 0/25-degree elevation row\", \"shading\": \"%s\", \"atlas_color_gain\": [%.6f, %.6f, %.6f], \"material_inputs\": [\"base_color_opacity\", \"opacity\", \"material_identity\"%s], \"captured_but_not_sampled\": [%s], \"texture_residency_for_immediate_exact_camera_review\": \"never_stream\", \"world_normal_relighting_enabled\": %s, \"depth_reserved_for_future_parallax\": %s, \"complementary_screen_dither_enabled\": %s, \"complementary_source_coverage_parameter\": \"ComplementarySourceCoverage\"},\n")
        TEXT("  \"relightable_runtime_contract\": {\"ready\": %s, \"split_layer_ready\": %s, \"shading\": \"masked DefaultLit combined control plus disjoint DefaultLit trunk and TwoSidedFoliage layers using captured world normal and frontmost material identity\", \"base_color_gain\": [1.55, 1.55, 1.55], \"emissive_connected\": false, \"world_normal_relighting_enabled\": true, \"material_identity_parameter\": \"AtlasMaterialIdentity\", \"layer_opacity\": {\"trunk\": \"opacity_times_one_minus_material_identity\", \"foliage\": \"opacity_times_material_identity\"}, \"layer_transition_order\": \"material_identity_layer_opacity_then_complementary_temporal_mask\", \"trunk_shading_model\": \"DefaultLit\", \"foliage_shading_model\": \"TwoSidedFoliage\", \"foliage_transmission_parameter\": \"AtlasFoliageTransmissionTint\", \"foliage_transmission_default\": [0.78, 1.0, 0.58], \"trunk_parameters\": [\"AtlasTrunkGainMultiplier\", \"AtlasTrunkRoughness\", \"AtlasTrunkSpecular\"], \"foliage_parameters\": [\"AtlasFoliageGainMultiplier\", \"AtlasFoliageRoughness\", \"AtlasFoliageSpecular\"], \"combined_default_roughness\": [0.68, 0.68], \"split_default_roughness\": [0.62, 0.72], \"combined_default_specular\": [0.18, 0.18], \"split_default_specular\": [0.12, 0.18], \"default_gain_multipliers\": [1.0, 1.0], \"transition_mode_parameter\": \"ComplementaryTransitionMode\", \"production_candidate_mode\": \"engine_DitherTemporalAA_with_exact_inverse_hlod_ownership\", \"legacy_ordered_control_retained\": true, \"atlas_frame_override_parameter\": \"AtlasFrameOverride\", \"automatic_frame_override_value\": -1.0},\n")
        TEXT("  \"git_policy\": \"generated atlases and assets are local and ignored\"\n")
        TEXT("}\n"),
        *EscapeRaftSimJsonString(VariantId),
        OutResult.IsReady() ? TEXT("generated_and_proxy_ready_for_exact_camera_review") : TEXT("generation_failed"),
        AzimuthOffsetDegrees,
        AzimuthOffsetDegrees,
        AzimuthOffsetDegrees + 45.0f,
        AzimuthOffsetDegrees + 90.0f,
        AzimuthOffsetDegrees + 135.0f,
        AzimuthOffsetDegrees + 180.0f,
        AzimuthOffsetDegrees + 225.0f,
        AzimuthOffsetDegrees + 270.0f,
        AzimuthOffsetDegrees + 315.0f,
        TileResolution,
        AtlasResolution,
        OrthoWidth,
        bUsePerspectiveCapture ? TEXT("perspective") : TEXT("orthographic"),
        CaptureRadius,
        PerspectiveHorizontalFovDegrees,
        OrthoWidth,
        bUseDepthParallax ? TEXT("32x32_tessellated_depth_displaced_billboard") : TEXT("flat_billboard"),
        bUseDepthParallax ? TEXT("true") : TEXT("false"),
        DepthParallaxScaleCm,
        OutResult.ProxyVertexCount,
        OutResult.ProxyTriangleCount,
        bUseColorCorrectHlod
            ? TEXT("SCS_FinalColorLDR source-lit RGB with inverse-opacity silhouette")
            : TEXT("SCS_FinalColorLDR lit RGB with Futaleufu photographic post process"),
        *EscapeRaftSimJsonString(OutResult.OpacitySource),
        static_cast<long long>(OutResult.MaterialIdentityFallbackPixelCount),
        OutResult.MinimumCoverage,
        OutResult.MaximumCoverage,
        *EscapeRaftSimJsonString(OutResult.BaseColorRelativePath),
        *OutResult.BaseColorDigest,
        *EscapeRaftSimJsonString(OutResult.AlbedoRelativePath),
        *OutResult.AlbedoDigest,
        *EscapeRaftSimJsonString(OutResult.NormalRelativePath),
        *OutResult.NormalDigest,
        *EscapeRaftSimJsonString(OutResult.OpacityRelativePath),
        *OutResult.OpacityDigest,
        *EscapeRaftSimJsonString(OutResult.DepthRelativePath),
        *OutResult.DepthDigest,
        *EscapeRaftSimJsonString(OutResult.MaterialIdentityRelativePath),
        *OutResult.MaterialIdentityDigest,
        *EscapeRaftSimJsonString(OutResult.BaseColorAssetPath),
        *EscapeRaftSimJsonString(OutResult.AlbedoAssetPath),
        *EscapeRaftSimJsonString(OutResult.NormalAssetPath),
        *EscapeRaftSimJsonString(OutResult.OpacityAssetPath),
        *EscapeRaftSimJsonString(OutResult.DepthAssetPath),
        *EscapeRaftSimJsonString(OutResult.MaterialIdentityAssetPath),

        *EscapeRaftSimJsonString(OutResult.MaterialAssetPath),
        *EscapeRaftSimJsonString(OutResult.RelightableMaterialAssetPath),
        *EscapeRaftSimJsonString(OutResult.RelightableTrunkMaterialAssetPath),
        *EscapeRaftSimJsonString(OutResult.RelightableFoliageMaterialAssetPath),
        bUseDepthParallax
            ? TEXT("camera-facing 32x32 tessellated XY grid with depth-atlas vertex displacement")
            : TEXT("camera-facing XY plane through world-position offset"),
        bUseColorCorrectHlod
            ? TEXT("masked unlit source-lit RGB with bounded color gain")
            : TEXT("masked unlit baked FinalColorLDR"),
        AtlasColorGain.R,
        AtlasColorGain.G,
        AtlasColorGain.B,
        bUseDepthParallax ? TEXT(", \"depth\"") : TEXT(""),
        bUseDepthParallax ? TEXT("\"world_normal\"") : TEXT("\"world_normal\", \"depth\""),
        TEXT("false"),
        bUseDepthParallax ? TEXT("false") : TEXT("true"),
        bEnableComplementaryTransition ? TEXT("true") : TEXT("false"),
        OutResult.IsRelightableReady() ? TEXT("true") : TEXT("false"),
        OutResult.IsSplitRelightableReady() ? TEXT("true") : TEXT("false"));
    const bool bManifestSaved = FFileHelper::SaveStringToFile(Manifest, *ManifestAbsolutePath);
    if (!bManifestSaved)
    {
        OutSummary += TEXT("Multi-view atlas manifest failed to save.\n");
    }
    OutSummary += FString::Printf(
        TEXT("Multi-view atlas generated 16 views at %d px into %d px outputs; coverage %.6f to %.6f.\n"),
        TileResolution,
        AtlasResolution,
        OutResult.MinimumCoverage,
        OutResult.MaximumCoverage);
    return bManifestSaved && OutResult.IsSplitRelightableReady();
}

} // namespace RaftSimEditorPve

#undef LogRaftSimEditor
#undef LOCTEXT_NAMESPACE
