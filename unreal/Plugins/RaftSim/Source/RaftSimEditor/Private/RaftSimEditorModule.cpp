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

#define LOCTEXT_NAMESPACE "FRaftSimEditorModule"

DEFINE_LOG_CATEGORY_STATIC(LogRaftSimEditor, Log, All);

using RaftSimEditorFoliage::FRaftSimEnvironmentPreviewSpec;

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
        TEXT("Import review-gated source DEMs as isolated Unreal Landscape candidate maps and capture them; optionally pass one river_id."),
        FConsoleCommandWithArgsDelegate::CreateRaw(this, &FRaftSimEditorModule::HandleCreateLandscapeImportCandidateMapsCommand));
    CreateSouthForkFullReachEnvironmentConsoleCommand = MakeUnique<FAutoConsoleCommand>(
        TEXT("RaftSim.CreateSouthForkFullReachEnvironment"),
        TEXT("Build and capture the World Partition South Fork full-reach gameplay environment."),
        FConsoleCommandWithArgsDelegate::CreateRaw(
            this, &FRaftSimEditorModule::HandleCreateSouthForkFullReachEnvironmentCommand));
    CaptureZambeziCliffComparisonConsoleCommand = MakeUnique<FAutoConsoleCommand>(
        TEXT("RaftSim.CaptureZambeziCliffComparison"),
        TEXT("Capture paired baseline and transient Namaqualand cliff analog views in the Zambezi candidate map."),
        FConsoleCommandWithArgsDelegate::CreateRaw(
            this,
            &FRaftSimEditorModule::HandleCaptureZambeziCliffComparisonCommand));
    CreateZambeziBatokaBasaltFamilyConsoleCommand = MakeUnique<FAutoConsoleCommand>(
        TEXT("RaftSim.CreateZambeziBatokaBasaltFamily"),
        TEXT("Create the project-owned four-form Batoka basalt isolated review family and captures."),
        FConsoleCommandWithArgsDelegate::CreateRaw(
            this,
            &FRaftSimEditorModule::HandleCreateZambeziBatokaBasaltFamilyCommand));
    CaptureZambeziBatokaBasaltCorridorComparisonConsoleCommand =
        MakeUnique<FAutoConsoleCommand>(
            TEXT("RaftSim.CaptureZambeziBatokaBasaltCorridorComparison"),
            TEXT("Capture paired baseline and transient non-colliding V10 Batoka module views in the Zambezi corridor."),
            FConsoleCommandWithArgsDelegate::CreateRaw(
                this,
                &FRaftSimEditorModule::HandleCaptureZambeziBatokaBasaltCorridorComparisonCommand));
    CaptureZambeziBatokaTerrainIntegratedComparisonConsoleCommand =
        MakeUnique<FAutoConsoleCommand>(
            TEXT("RaftSim.CaptureZambeziBatokaTerrainIntegratedComparison"),
            TEXT("Capture paired baseline and transient V11 Batoka material views on the continuous Zambezi visual terrain."),
            FConsoleCommandWithArgsDelegate::CreateRaw(
                this,
                &FRaftSimEditorModule::HandleCaptureZambeziBatokaTerrainIntegratedComparisonCommand));
    CaptureZambeziBatokaWorldAlignedTerrainComparisonConsoleCommand =
        MakeUnique<FAutoConsoleCommand>(
            TEXT("RaftSim.CaptureZambeziBatokaWorldAlignedTerrainComparison"),
            TEXT("Capture paired baseline and transient V12 world-aligned Batoka material views on the continuous Zambezi visual terrain."),
            FConsoleCommandWithArgsDelegate::CreateRaw(
                this,
                &FRaftSimEditorModule::HandleCaptureZambeziBatokaWorldAlignedTerrainComparisonCommand));
    CaptureZambeziBatokaVisualMorphologyComparisonConsoleCommand =
        MakeUnique<FAutoConsoleCommand>(
            TEXT("RaftSim.CaptureZambeziBatokaVisualMorphologyComparison"),
            TEXT("Capture paired V12-material baseline and bounded render-only V13 Batoka morphology views."),
            FConsoleCommandWithArgsDelegate::CreateRaw(
                this,
                &FRaftSimEditorModule::HandleCaptureZambeziBatokaVisualMorphologyComparisonCommand));
    CaptureFutaleufuNativeCanopyCorridorComparisonConsoleCommand =
        MakeUnique<FAutoConsoleCommand>(
            TEXT("RaftSim.CaptureFutaleufuNativeCanopyCorridorComparison"),
            TEXT("Capture paired baseline and source-masked project-owned coigue views in the Futaleufu physical corridor."),
            FConsoleCommandWithArgsDelegate::CreateRaw(
                this,
                &FRaftSimEditorModule::HandleCaptureFutaleufuNativeCanopyCorridorComparisonCommand));
    CaptureFutaleufuDenseCanopyComparisonConsoleCommand =
        MakeUnique<FAutoConsoleCommand>(
            TEXT("RaftSim.CaptureFutaleufuDenseCanopyComparison"),
            TEXT("Capture paired retained-sparse and dense camera-local source-masked Futaleufu canopy views."),
            FConsoleCommandWithArgsDelegate::CreateRaw(
                this,
                &FRaftSimEditorModule::HandleCaptureFutaleufuDenseCanopyComparisonCommand));
    CaptureFutaleufuAreaSampledCanopyComparisonConsoleCommand =
        MakeUnique<FAutoConsoleCommand>(
            TEXT("RaftSim.CaptureFutaleufuAreaSampledCanopyComparison"),
            TEXT("Capture paired centerline and 2D area-sampled camera-local Futaleufu canopy views."),
            FConsoleCommandWithArgsDelegate::CreateRaw(
                this,
                &FRaftSimEditorModule::HandleCaptureFutaleufuAreaSampledCanopyComparisonCommand));
    CaptureFutaleufuWorldStableCanopyComparisonConsoleCommand =
        MakeUnique<FAutoConsoleCommand>(
            TEXT("RaftSim.CaptureFutaleufuWorldStableCanopyComparison"),
            TEXT("Capture paired camera-local and spatial-occupancy world-stable Futaleufu canopy views."),
            FConsoleCommandWithArgsDelegate::CreateRaw(
                this,
                &FRaftSimEditorModule::HandleCaptureFutaleufuWorldStableCanopyComparisonCommand));
    CaptureFutaleufuNativeCanopyRenderDiagnosticsConsoleCommand =
        MakeUnique<FAutoConsoleCommand>(
            TEXT("RaftSim.CaptureFutaleufuNativeCanopyRenderDiagnostics"),
            TEXT("Capture controlled leaf-shadow and opaque-card diagnostics in the Futaleufu physical corridor."),
            FConsoleCommandWithArgsDelegate::CreateRaw(
                this,
                &FRaftSimEditorModule::HandleCaptureFutaleufuNativeCanopyRenderDiagnosticsCommand));
    CaptureFutaleufuNativeCanopyOpacityDiagnosticsConsoleCommand =
        MakeUnique<FAutoConsoleCommand>(
            TEXT("RaftSim.CaptureFutaleufuNativeCanopyOpacityDiagnostics"),
            TEXT("Capture same-shader native leaf alpha-scale and constant-opacity diagnostics in the Futaleufu corridor."),
            FConsoleCommandWithArgsDelegate::CreateRaw(
                this,
                &FRaftSimEditorModule::HandleCaptureFutaleufuNativeCanopyOpacityDiagnosticsCommand));
    CaptureFutaleufuNativeCanopyLightingDiagnosticsConsoleCommand =
        MakeUnique<FAutoConsoleCommand>(
            TEXT("RaftSim.CaptureFutaleufuNativeCanopyLightingDiagnostics"),
            TEXT("Capture same-shader AO, flat-normal, and diagnostic-emissive foliage response splits."),
            FConsoleCommandWithArgsDelegate::CreateRaw(
                this,
                &FRaftSimEditorModule::HandleCaptureFutaleufuNativeCanopyLightingDiagnosticsCommand));
    CaptureFutaleufuNativeCanopyCorridorLightRigDiagnosticsConsoleCommand =
        MakeUnique<FAutoConsoleCommand>(
            TEXT("RaftSim.CaptureFutaleufuNativeCanopyCorridorLightRigDiagnostics"),
            TEXT("Capture fixed-canopy baseline, isolated-fill, and skylight-only corridor lighting splits."),
            FConsoleCommandWithArgsDelegate::CreateRaw(
                this,
                &FRaftSimEditorModule::HandleCaptureFutaleufuNativeCanopyCorridorLightRigDiagnosticsCommand));
    CaptureFutaleufuNativeCanopyReflectanceDiagnosticsConsoleCommand =
        MakeUnique<FAutoConsoleCommand>(
            TEXT("RaftSim.CaptureFutaleufuNativeCanopyReflectanceDiagnostics"),
            TEXT("Capture fixed-light leaf base-color, transmission, and interaction diagnostics."),
            FConsoleCommandWithArgsDelegate::CreateRaw(
                this,
                &FRaftSimEditorModule::HandleCaptureFutaleufuNativeCanopyReflectanceDiagnosticsCommand));
    CaptureFutaleufuNativeCanopyShadingModelDiagnosticsConsoleCommand =
        MakeUnique<FAutoConsoleCommand>(
            TEXT("RaftSim.CaptureFutaleufuNativeCanopyShadingModelDiagnostics"),
            TEXT("Capture same-texture masked TwoSidedFoliage and DefaultLit canopy diagnostics."),
            FConsoleCommandWithArgsDelegate::CreateRaw(
                this,
                &FRaftSimEditorModule::HandleCaptureFutaleufuNativeCanopyShadingModelDiagnosticsCommand));
    CaptureFutaleufuNativeCanopyMipPaddingDiagnosticsConsoleCommand =
        MakeUnique<FAutoConsoleCommand>(
            TEXT("RaftSim.CaptureFutaleufuNativeCanopyMipPaddingDiagnostics"),
            TEXT("Reimport the alpha-preserving leaf RGB padding and capture the fixed native corridor pair."),
            FConsoleCommandWithArgsDelegate::CreateRaw(
                this,
                &FRaftSimEditorModule::HandleCaptureFutaleufuNativeCanopyMipPaddingDiagnosticsCommand));
    CaptureFutaleufuNativeCanopyOpacitySelectionDiagnosticsConsoleCommand =
        MakeUnique<FAutoConsoleCommand>(
            TEXT("RaftSim.CaptureFutaleufuNativeCanopyOpacitySelectionDiagnostics"),
            TEXT("Capture corrected-atlas native alpha scales 2 and 3 against the retained alpha4 reference."),
            FConsoleCommandWithArgsDelegate::CreateRaw(
                this,
                &FRaftSimEditorModule::HandleCaptureFutaleufuNativeCanopyOpacitySelectionDiagnosticsCommand));
    CaptureFutaleufuNativeCanopyBoundedShadowDiagnosticsConsoleCommand =
        MakeUnique<FAutoConsoleCommand>(
            TEXT("RaftSim.CaptureFutaleufuNativeCanopyBoundedShadowDiagnostics"),
            TEXT("Capture alpha2 near-canopy dynamic shadows with contact and indirect effects disabled."),
            FConsoleCommandWithArgsDelegate::CreateRaw(
                this,
                &FRaftSimEditorModule::HandleCaptureFutaleufuNativeCanopyBoundedShadowDiagnosticsCommand));
    InspectProceduralVegetationSampleConsoleCommand = MakeUnique<FAutoConsoleCommand>(
        TEXT("RaftSim.InspectProceduralVegetationSample"),
        TEXT("Log the installed UE Procedural Vegetation sample graph contract for reproducible asset generation."),
        FConsoleCommandWithArgsDelegate::CreateRaw(this, &FRaftSimEditorModule::HandleInspectProceduralVegetationSampleCommand));
    EvaluateProceduralBeechCandidateConsoleCommand = MakeUnique<FAutoConsoleCommand>(
        TEXT("RaftSim.EvaluateProceduralBeechCandidate"),
        TEXT("Execute one installed UE PVE European Beech growth-data variant and record structural review evidence."),
        FConsoleCommandWithArgsDelegate::CreateRaw(this, &FRaftSimEditorModule::HandleEvaluateProceduralBeechCandidateCommand));
    EvaluateFutaleufuCordilleraCypressPveCandidateConsoleCommand =
        MakeUnique<FAutoConsoleCommand>(
            TEXT("RaftSim.EvaluateFutaleufuCordilleraCypressPveCandidate"),
            TEXT("Build one project-owned cordilleran-cypress PVE form with a named retained or experimental foliage palette."),
            FConsoleCommandWithArgsDelegate::CreateRaw(
                this,
                &FRaftSimEditorModule::HandleEvaluateFutaleufuCordilleraCypressPveCandidateCommand));
    CreateFutaleufuNativeCanopyPrototypeConsoleCommand = MakeUnique<FAutoConsoleCommand>(
        TEXT("RaftSim.CreateFutaleufuNativeCanopyPrototype"),
        TEXT("Create the project-owned coigue texture, material, Nanite mesh, map, and capture review assets."),
        FConsoleCommandWithArgsDelegate::CreateRaw(
            this,
            &FRaftSimEditorModule::HandleCreateFutaleufuNativeCanopyPrototypeCommand));
    CreateFutaleufuCordilleraCypressFamilyConsoleCommand = MakeUnique<FAutoConsoleCommand>(
        TEXT("RaftSim.CreateFutaleufuCordilleraCypressFamily"),
        TEXT("Create the project-owned eight-form cordilleran-cypress isolated review family and captures."),
        FConsoleCommandWithArgsDelegate::CreateRaw(
            this,
            &FRaftSimEditorModule::HandleCreateFutaleufuCordilleraCypressFamilyCommand));
    CreateFutaleufuCordilleraCypressOpaqueNearReviewConsoleCommand =
        MakeUnique<FAutoConsoleCommand>(
            TEXT("RaftSim.CreateFutaleufuCordilleraCypressOpaqueNearReview"),
            TEXT("Create the V14 project-owned opaque connected-scale-leaf cypress review family."),
            FConsoleCommandWithArgsDelegate::CreateRaw(
                this,
                &FRaftSimEditorModule::HandleCreateFutaleufuCordilleraCypressOpaqueNearReviewCommand));
    CreateFutaleufuCordilleraCypressVolumetricNearReviewConsoleCommand =
        MakeUnique<FAutoConsoleCommand>(
            TEXT("RaftSim.CreateFutaleufuCordilleraCypressVolumetricNearReview"),
            TEXT("Create the V15 rounded volumetric scale-leaf cypress review family."),
            FConsoleCommandWithArgsDelegate::CreateRaw(
                this,
                &FRaftSimEditorModule::HandleCreateFutaleufuCordilleraCypressVolumetricNearReviewCommand));
    CreateFutaleufuCordilleraCypressDonorReviewConsoleCommand = MakeUnique<FAutoConsoleCommand>(
        TEXT("RaftSim.CreateFutaleufuCordilleraCypressDonorReview"),
        TEXT("Create the non-native CC0 connected-geometry morphology-donor review map and captures."),
        FConsoleCommandWithArgsDelegate::CreateRaw(
            this,
            &FRaftSimEditorModule::HandleCreateFutaleufuCordilleraCypressDonorReviewCommand));

    bCreatePhotorealEnvironmentPreviewMapsOnStartup =
        FParse::Param(FCommandLine::Get(), TEXT("RaftSimCreatePhotorealEnvironmentPreviewMaps"));
    bCapturePhotorealEnvironmentPreviewsOnStartup =
        FParse::Param(FCommandLine::Get(), TEXT("RaftSimCapturePhotorealEnvironmentPreviews"));
    bCreateLandscapeImportCandidateMapsOnStartup =
        FParse::Param(FCommandLine::Get(), TEXT("RaftSimCreateLandscapeImportCandidateMaps"));
    bCreateSouthForkFullReachEnvironmentOnStartup =
        FParse::Param(FCommandLine::Get(), TEXT("RaftSimCreateSouthForkFullReachEnvironment"));
    bCreateZambeziBatokaBasaltFamilyOnStartup =
        FParse::Param(FCommandLine::Get(), TEXT("RaftSimCreateZambeziBatokaBasaltFamily"));
    bCaptureZambeziBatokaBasaltCorridorComparisonOnStartup =
        FParse::Param(
            FCommandLine::Get(),
            TEXT("RaftSimCaptureZambeziBatokaBasaltCorridorComparison"));
    bCaptureZambeziBatokaTerrainIntegratedComparisonOnStartup =
        FParse::Param(
            FCommandLine::Get(),
            TEXT("RaftSimCaptureZambeziBatokaTerrainIntegratedComparison"));
    bCaptureZambeziBatokaWorldAlignedTerrainComparisonOnStartup =
        FParse::Param(
            FCommandLine::Get(),
            TEXT("RaftSimCaptureZambeziBatokaWorldAlignedTerrainComparison"));
    bCaptureZambeziBatokaVisualMorphologyComparisonOnStartup =
        FParse::Param(
            FCommandLine::Get(),
            TEXT("RaftSimCaptureZambeziBatokaVisualMorphologyComparison"));
    bCaptureFutaleufuDenseCanopyComparisonOnStartup =
        FParse::Param(
            FCommandLine::Get(),
            TEXT("RaftSimCaptureFutaleufuDenseCanopyComparison"));
    bCaptureFutaleufuAreaSampledCanopyComparisonOnStartup =
        FParse::Param(
            FCommandLine::Get(),
            TEXT("RaftSimCaptureFutaleufuAreaSampledCanopyComparison"));
    bCaptureFutaleufuWorldStableCanopyComparisonOnStartup =
        FParse::Param(
            FCommandLine::Get(),
            TEXT("RaftSimCaptureFutaleufuWorldStableCanopyComparison"));
    bCreateFutaleufuCordilleraCypressFamilyOnStartup =
        FParse::Param(FCommandLine::Get(), TEXT("RaftSimCreateFutaleufuCordilleraCypressFamily"));
    bCreateFutaleufuCordilleraCypressOpaqueNearReviewOnStartup =
        FParse::Param(
            FCommandLine::Get(),
            TEXT("RaftSimCreateFutaleufuCordilleraCypressOpaqueNearReview"));
    bCreateFutaleufuCordilleraCypressVolumetricNearReviewOnStartup =
        FParse::Param(
            FCommandLine::Get(),
            TEXT("RaftSimCreateFutaleufuCordilleraCypressVolumetricNearReview"));
    bCreateFutaleufuCordilleraCypressDonorReviewOnStartup =
        FParse::Param(
            FCommandLine::Get(),
            TEXT("RaftSimCreateFutaleufuCordilleraCypressDonorReview"));
    bExitAfterPhotorealEnvironmentAutomation =
        FParse::Param(FCommandLine::Get(), TEXT("RaftSimExitAfterEnvironmentAutomation"));

    if (bCreatePhotorealEnvironmentPreviewMapsOnStartup ||
        bCapturePhotorealEnvironmentPreviewsOnStartup ||
        bCreateLandscapeImportCandidateMapsOnStartup ||
        bCreateSouthForkFullReachEnvironmentOnStartup ||
        bCreateZambeziBatokaBasaltFamilyOnStartup ||
        bCaptureZambeziBatokaBasaltCorridorComparisonOnStartup ||
        bCaptureZambeziBatokaTerrainIntegratedComparisonOnStartup ||
        bCaptureZambeziBatokaWorldAlignedTerrainComparisonOnStartup ||
        bCaptureZambeziBatokaVisualMorphologyComparisonOnStartup ||
        bCaptureFutaleufuDenseCanopyComparisonOnStartup ||
        bCaptureFutaleufuAreaSampledCanopyComparisonOnStartup ||
        bCaptureFutaleufuWorldStableCanopyComparisonOnStartup ||
        bCreateFutaleufuCordilleraCypressFamilyOnStartup ||
        bCreateFutaleufuCordilleraCypressOpaqueNearReviewOnStartup ||
        bCreateFutaleufuCordilleraCypressVolumetricNearReviewOnStartup ||
        bCreateFutaleufuCordilleraCypressDonorReviewOnStartup)
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
    CreateSouthForkFullReachEnvironmentConsoleCommand.Reset();
    CaptureZambeziCliffComparisonConsoleCommand.Reset();
    CreateZambeziBatokaBasaltFamilyConsoleCommand.Reset();
    CaptureZambeziBatokaBasaltCorridorComparisonConsoleCommand.Reset();
    CaptureZambeziBatokaTerrainIntegratedComparisonConsoleCommand.Reset();
    CaptureZambeziBatokaWorldAlignedTerrainComparisonConsoleCommand.Reset();
    CaptureZambeziBatokaVisualMorphologyComparisonConsoleCommand.Reset();
    CaptureFutaleufuNativeCanopyCorridorComparisonConsoleCommand.Reset();
    CaptureFutaleufuDenseCanopyComparisonConsoleCommand.Reset();
    CaptureFutaleufuAreaSampledCanopyComparisonConsoleCommand.Reset();
    CaptureFutaleufuWorldStableCanopyComparisonConsoleCommand.Reset();
    CaptureFutaleufuNativeCanopyRenderDiagnosticsConsoleCommand.Reset();
    CaptureFutaleufuNativeCanopyOpacityDiagnosticsConsoleCommand.Reset();
    CaptureFutaleufuNativeCanopyLightingDiagnosticsConsoleCommand.Reset();
    CaptureFutaleufuNativeCanopyCorridorLightRigDiagnosticsConsoleCommand.Reset();
    CaptureFutaleufuNativeCanopyReflectanceDiagnosticsConsoleCommand.Reset();
    CaptureFutaleufuNativeCanopyShadingModelDiagnosticsConsoleCommand.Reset();
    CaptureFutaleufuNativeCanopyMipPaddingDiagnosticsConsoleCommand.Reset();
    CaptureFutaleufuNativeCanopyOpacitySelectionDiagnosticsConsoleCommand.Reset();
    CaptureFutaleufuNativeCanopyBoundedShadowDiagnosticsConsoleCommand.Reset();
    InspectProceduralVegetationSampleConsoleCommand.Reset();
    EvaluateProceduralBeechCandidateConsoleCommand.Reset();
    EvaluateFutaleufuCordilleraCypressPveCandidateConsoleCommand.Reset();
    CreateFutaleufuNativeCanopyPrototypeConsoleCommand.Reset();
    CreateFutaleufuCordilleraCypressFamilyConsoleCommand.Reset();
    CreateFutaleufuCordilleraCypressOpaqueNearReviewConsoleCommand.Reset();
    CreateFutaleufuCordilleraCypressVolumetricNearReviewConsoleCommand.Reset();
    CreateFutaleufuCordilleraCypressDonorReviewConsoleCommand.Reset();

    if (ProceduralBeechCandidateTickerHandle.IsValid())
    {
        FTSTicker::RemoveTicker(ProceduralBeechCandidateTickerHandle);
        ProceduralBeechCandidateTickerHandle.Reset();
    }
    if (ProceduralBeechExecutionSource || ProceduralBeechCandidateAsset || ProceduralBeechGrowthAsset)
    {
        FinishProceduralBeechCandidate(false, TEXT("module shutdown interrupted an active evaluation"));
    }
    UnregisterToolTabs();

    if (UObjectInitialized())
    {
        UToolMenus::UnRegisterStartupCallback(this);
        UToolMenus::UnregisterOwner(this);
    }
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

void FRaftSimEditorModule::HandleCreateLandscapeImportCandidateMapsCommand(
    const TArray<FString>& Args)
{
    FString Summary;
    CreateLandscapeImportCandidateMaps(
        Summary,
        Args.IsEmpty() ? FString() : Args[0]);
    UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
}

void FRaftSimEditorModule::HandleCreateSouthForkFullReachEnvironmentCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CreateSouthForkFullReachEnvironment(Summary);
    if (bSucceeded)
    {
        UE_LOG(
            LogRaftSimEditor, Display,
            TEXT("South Fork full-reach environment build completed.\n%s"),
            *Summary);
    }
    else
    {
        UE_LOG(
            LogRaftSimEditor, Error,
            TEXT("South Fork full-reach environment build failed.\n%s"),
            *Summary);
    }
}

void FRaftSimEditorModule::HandleCaptureZambeziCliffComparisonCommand(const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CaptureZambeziCliffComparison(Summary);
    if (bSucceeded)
    {
        UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
    }
    else
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("%s"), *Summary);
    }
}

void FRaftSimEditorModule::HandleCreateZambeziBatokaBasaltFamilyCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CreateZambeziBatokaBasaltFamily(Summary);
    if (bSucceeded)
    {
        UE_LOG(LogRaftSimEditor, Display, TEXT("Zambezi Batoka basalt family completed.\n%s"), *Summary);
    }
    else
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("Zambezi Batoka basalt family failed.\n%s"), *Summary);
    }
}

void FRaftSimEditorModule::HandleCaptureZambeziBatokaBasaltCorridorComparisonCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CaptureZambeziBatokaBasaltCorridorComparison(Summary);
    if (bSucceeded)
    {
        UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
    }
    else
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("%s"), *Summary);
    }
}

void FRaftSimEditorModule::HandleCaptureZambeziBatokaTerrainIntegratedComparisonCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CaptureZambeziBatokaTerrainIntegratedComparison(Summary);
    if (bSucceeded)
    {
        UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
    }
    else
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("%s"), *Summary);
    }
}

void FRaftSimEditorModule::HandleCaptureZambeziBatokaWorldAlignedTerrainComparisonCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CaptureZambeziBatokaWorldAlignedTerrainComparison(Summary);
    if (bSucceeded)
    {
        UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
    }
    else
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("%s"), *Summary);
    }
}

void FRaftSimEditorModule::HandleCaptureZambeziBatokaVisualMorphologyComparisonCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CaptureZambeziBatokaVisualMorphologyComparison(Summary);
    if (bSucceeded)
    {
        UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
    }
    else
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("%s"), *Summary);
    }
}

void FRaftSimEditorModule::HandleCaptureFutaleufuNativeCanopyCorridorComparisonCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CaptureFutaleufuNativeCanopyCorridorComparison(Summary);
    if (bSucceeded)
    {
        UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
    }
    else
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("%s"), *Summary);
    }
}

void FRaftSimEditorModule::HandleCaptureFutaleufuDenseCanopyComparisonCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CaptureFutaleufuDenseCanopyComparison(Summary);
    if (bSucceeded)
    {
        UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
    }
    else
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("%s"), *Summary);
    }
}

void FRaftSimEditorModule::HandleCaptureFutaleufuAreaSampledCanopyComparisonCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CaptureFutaleufuAreaSampledCanopyComparison(Summary);
    if (bSucceeded)
    {
        UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
    }
    else
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("%s"), *Summary);
    }
}

void FRaftSimEditorModule::HandleCaptureFutaleufuWorldStableCanopyComparisonCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CaptureFutaleufuWorldStableCanopyComparison(Summary);
    if (bSucceeded)
    {
        UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
    }
    else
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("%s"), *Summary);
    }
}

void FRaftSimEditorModule::HandleCaptureFutaleufuNativeCanopyRenderDiagnosticsCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CaptureFutaleufuNativeCanopyRenderDiagnostics(Summary);
    if (bSucceeded)
    {
        UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
    }
    else
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("%s"), *Summary);
    }
}

void FRaftSimEditorModule::HandleCaptureFutaleufuNativeCanopyOpacityDiagnosticsCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CaptureFutaleufuNativeCanopyOpacityDiagnostics(Summary);
    if (bSucceeded)
    {
        UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
    }
    else
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("%s"), *Summary);
    }
}

void FRaftSimEditorModule::HandleCaptureFutaleufuNativeCanopyLightingDiagnosticsCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CaptureFutaleufuNativeCanopyLightingDiagnostics(Summary);
    if (bSucceeded)
    {
        UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
    }
    else
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("%s"), *Summary);
    }
}

void FRaftSimEditorModule::HandleCaptureFutaleufuNativeCanopyCorridorLightRigDiagnosticsCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CaptureFutaleufuNativeCanopyCorridorLightRigDiagnostics(Summary);
    if (bSucceeded)
    {
        UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
    }
    else
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("%s"), *Summary);
    }
}

void FRaftSimEditorModule::HandleCaptureFutaleufuNativeCanopyReflectanceDiagnosticsCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CaptureFutaleufuNativeCanopyReflectanceDiagnostics(Summary);
    if (bSucceeded)
    {
        UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
    }
    else
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("%s"), *Summary);
    }
}

void FRaftSimEditorModule::HandleCaptureFutaleufuNativeCanopyShadingModelDiagnosticsCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CaptureFutaleufuNativeCanopyShadingModelDiagnostics(Summary);
    if (bSucceeded)
    {
        UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
    }
    else
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("%s"), *Summary);
    }
}

void FRaftSimEditorModule::HandleCaptureFutaleufuNativeCanopyMipPaddingDiagnosticsCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CaptureFutaleufuNativeCanopyMipPaddingDiagnostics(Summary);
    if (bSucceeded)
    {
        UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
    }
    else
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("%s"), *Summary);
    }
}

void FRaftSimEditorModule::HandleCaptureFutaleufuNativeCanopyOpacitySelectionDiagnosticsCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CaptureFutaleufuNativeCanopyOpacitySelectionDiagnostics(Summary);
    if (bSucceeded)
    {
        UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
    }
    else
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("%s"), *Summary);
    }
}

void FRaftSimEditorModule::HandleCaptureFutaleufuNativeCanopyBoundedShadowDiagnosticsCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CaptureFutaleufuNativeCanopyBoundedShadowDiagnostics(Summary);
    if (bSucceeded)
    {
        UE_LOG(LogRaftSimEditor, Display, TEXT("%s"), *Summary);
    }
    else
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("%s"), *Summary);
    }
}

void FRaftSimEditorModule::HandleInspectProceduralVegetationSampleCommand(const TArray<FString>& Args)
{
    const FString SamplePath = Args.IsEmpty()
        ? TEXT("/ProceduralVegetationEditor/SampleAssets/StarterContent/DeciduousTree_01/"
               "PVE_Sample_Deciduous_Tree_01.PVE_Sample_Deciduous_Tree_01")
        : Args[0];
    UProceduralVegetation* Sample = LoadObject<UProceduralVegetation>(nullptr, *SamplePath);
    if (!Sample)
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("PVE sample inspection could not load %s."), *SamplePath);
        return;
    }

    UPCGGraph* Graph = Cast<UPCGGraph>(Sample->GetGraph());
    if (!Graph)
    {
        UE_LOG(LogRaftSimEditor, Error, TEXT("PVE sample %s has no readable PCG graph."), *SamplePath);
        return;
    }

    UE_LOG(
        LogRaftSimEditor,
        Display,
        TEXT("PVE_SAMPLE graph=%s nodes=%d source=%s"),
        *Graph->GetPathName(),
        Graph->GetNodes().Num(),
        *SamplePath);
    const UPCGNode* GraphOutputNode = Graph->GetOutputNode();
    FString GraphOutputPins;
    if (GraphOutputNode)
    {
        for (const UPCGPin* Pin : GraphOutputNode->GetInputPins())
        {
            GraphOutputPins += GraphOutputPins.IsEmpty()
                ? Pin->Properties.Label.ToString()
                : TEXT(",") + Pin->Properties.Label.ToString();
        }
    }
    UE_LOG(LogRaftSimEditor, Display, TEXT("PVE_SAMPLE graph_output_inputs=[%s]"), *GraphOutputPins);
    for (int32 EdgeIndex = 0; EdgeIndex < Graph->GetAllEdges().Num(); ++EdgeIndex)
    {
        const UPCGEdge* Edge = Graph->GetAllEdges()[EdgeIndex];
        if (!Edge || !Edge->IsValid())
        {
            continue;
        }
        UE_LOG(
            LogRaftSimEditor,
            Display,
            TEXT("PVE_SAMPLE edge=%d from=%s.%s to=%s.%s"),
            EdgeIndex,
            Edge->GetInputNode() ? *Edge->GetInputNode()->GetName() : TEXT("None"),
            *Edge->GetInputPinLabel().ToString(),
            Edge->GetOutputNode() ? *Edge->GetOutputNode()->GetName() : TEXT("None"),
            *Edge->GetOutputPinLabel().ToString());
    }
    for (int32 NodeIndex = 0; NodeIndex < Graph->GetNodes().Num(); ++NodeIndex)
    {
        UPCGNode* Node = Graph->GetNodes()[NodeIndex];
        UPCGSettings* Settings = Node ? Node->GetSettings() : nullptr;
        if (!Node || !Settings)
        {
            UE_LOG(LogRaftSimEditor, Warning, TEXT("PVE_SAMPLE node=%d missing node or settings."), NodeIndex);
            continue;
        }

        int32 PositionX = 0;
        int32 PositionY = 0;
        Node->GetNodePosition(PositionX, PositionY);
        FString InputPins;
        for (const UPCGPin* Pin : Node->GetInputPins())
        {
            InputPins += InputPins.IsEmpty() ? Pin->Properties.Label.ToString() : TEXT(",") + Pin->Properties.Label.ToString();
        }
        FString OutputPins;
        for (const UPCGPin* Pin : Node->GetOutputPins())
        {
            OutputPins += OutputPins.IsEmpty() ? Pin->Properties.Label.ToString() : TEXT(",") + Pin->Properties.Label.ToString();
        }
        UE_LOG(
            LogRaftSimEditor,
            Display,
            TEXT("PVE_SAMPLE node=%d name=%s position=%d,%d settings=%s inputs=[%s] outputs=[%s]"),
            NodeIndex,
            *Node->GetName(),
            PositionX,
            PositionY,
            *Settings->GetClass()->GetPathName(),
            *InputPins,
            *OutputPins);

        for (TFieldIterator<FProperty> PropertyIt(Settings->GetClass(), EFieldIterationFlags::IncludeSuper); PropertyIt; ++PropertyIt)
        {
            FProperty* Property = *PropertyIt;
            if (!Property->HasAnyPropertyFlags(CPF_Edit | CPF_BlueprintVisible))
            {
                continue;
            }
            FString Value;
            if (!Property->ExportText_InContainer(0, Value, Settings, Settings, Settings, PPF_Copy))
            {
                continue;
            }
            Value.ReplaceInline(TEXT("\r"), TEXT(" "));
            Value.ReplaceInline(TEXT("\n"), TEXT(" "));
            Value.LeftInline(600);
            UE_LOG(
                LogRaftSimEditor,
                Display,
                TEXT("PVE_SAMPLE property node=%d name=%s class=%s value=%s"),
                NodeIndex,
                *Property->GetName(),
                *Property->GetClass()->GetName(),
                *Value);
        }
    }
}

void FRaftSimEditorModule::HandleCreateFutaleufuCordilleraCypressFamilyCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CreateFutaleufuCordilleraCypressFamily(Summary);
    if (bSucceeded)
    {
        UE_LOG(
            LogRaftSimEditor,
            Display,
            TEXT("Futaleufu cordilleran-cypress family completed.\n%s"),
            *Summary);
    }
    else
    {
        UE_LOG(
            LogRaftSimEditor,
            Error,
            TEXT("Futaleufu cordilleran-cypress family failed.\n%s"),
            *Summary);
    }
}

void FRaftSimEditorModule::HandleCreateFutaleufuCordilleraCypressOpaqueNearReviewCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CreateFutaleufuCordilleraCypressOpaqueNearReview(Summary);
    if (bSucceeded)
    {
        UE_LOG(
            LogRaftSimEditor,
            Display,
            TEXT("Futaleufu V14 opaque cypress review completed.\n%s"),
            *Summary);
    }
    else
    {
        UE_LOG(
            LogRaftSimEditor,
            Error,
            TEXT("Futaleufu V14 opaque cypress review failed.\n%s"),
            *Summary);
    }
}

void FRaftSimEditorModule::HandleCreateFutaleufuCordilleraCypressVolumetricNearReviewCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CreateFutaleufuCordilleraCypressVolumetricNearReview(Summary);
    if (bSucceeded)
    {
        UE_LOG(
            LogRaftSimEditor,
            Display,
            TEXT("Futaleufu V15 volumetric cypress review completed.\n%s"),
            *Summary);
    }
    else
    {
        UE_LOG(
            LogRaftSimEditor,
            Error,
            TEXT("Futaleufu V15 volumetric cypress review failed.\n%s"),
            *Summary);
    }
}

void FRaftSimEditorModule::HandleCreateFutaleufuCordilleraCypressDonorReviewCommand(
    const TArray<FString>&)
{
    FString Summary;
    const bool bSucceeded = CreateFutaleufuCordilleraCypressDonorReview(Summary);
    if (bSucceeded)
    {
        UE_LOG(
            LogRaftSimEditor,
            Display,
            TEXT("Futaleufu cypress morphology-donor review completed.\n%s"),
            *Summary);
    }
    else
    {
        UE_LOG(
            LogRaftSimEditor,
            Error,
            TEXT("Futaleufu cypress morphology-donor review failed.\n%s"),
            *Summary);
    }
}

IMPLEMENT_MODULE(FRaftSimEditorModule, RaftSimEditor)

#undef LOCTEXT_NAMESPACE
