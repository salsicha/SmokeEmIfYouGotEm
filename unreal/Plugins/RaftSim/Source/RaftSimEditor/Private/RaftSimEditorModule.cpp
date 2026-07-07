#include "RaftSimEditorModule.h"

#include "AssetRegistry/AssetRegistryModule.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/LightComponent.h"
#include "Components/MeshComponent.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/SkyLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SkyAtmosphereComponent.h"
#include "Editor.h"
#include "Engine/DirectionalLight.h"
#include "Engine/ExponentialHeightFog.h"
#include "Engine/PointLight.h"
#include "Engine/SceneCapture2D.h"
#include "Engine/SkyLight.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
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
#include "Materials/Material.h"
#include "Materials/MaterialExpressionConstant.h"
#include "Materials/MaterialExpressionMultiply.h"
#include "Materials/MaterialExpressionScalarParameter.h"
#include "Materials/MaterialExpressionVertexColor.h"
#include "Materials/MaterialExpressionVectorParameter.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/CommandLine.h"
#include "Misc/CoreDelegates.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Modules/ModuleManager.h"
#include "ProceduralMeshComponent.h"
#include "RaftSimEditorToolRegistry.h"
#include "RaftSimFeatureTuningEditorShell.h"
#include "RaftSimRapidRiverEditorShell.h"
#include "RaftSimReplayDebugViewer.h"
#include "RaftSimToolValidationActions.h"
#include "Styling/CoreStyle.h"
#include "ToolMenus.h"
#include "UObject/SavePackage.h"
#include "RenderingThread.h"
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
    int32 BoulderCount = 18;
    int32 FoliageCount = 32;
    int32 FoamTrainCount = 12;
    bool bHasWaterfalls = false;
    bool bDesertCanyon = false;
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

FString GetFirstPartyProceduralEnvironmentAssetPlanRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/first_party_procedural_environment_assets.json");
}

FString GetFirstPartyProceduralMaterialRecipePlanRelativePath()
{
    return TEXT("unreal/Content/RaftSim/Rendering/first_party_procedural_material_recipes.json");
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
        TEXT("stitched South Fork production-import pilot source drape generated from four official USDA/APFO NAIP 2048px tiles, plus stitched USGS 3DEP pilot DEM relief and a review-gated 2017px heightfield candidate sampled into bank and valley preview geometry; pilot source water/vegetation masks are sampled into terrain color, source-aware bank breakup patches, biome-specific deadfall/log/grass/root ecology props, lit water variation, flow-band depth texture ribbons, flow-aware surface chop/turbidity patches, deterministic wet-rock, talus, foliage, understory, mask-aware ground-cover cards, and river-specific atmospheric backdrop cards; all pilot derivatives remain review-gated until metadata review, mosaic/clip, hydrologic conditioning, channel burning, masks, and guide/geospatial approval pass; rocks, foliage, water, foam, raft, and lighting still include first-party procedural proxy layers");
    SouthFork.FlowBandId = TEXT("median_runnable");
    SouthFork.FlowBandDisplayName = TEXT("Median Runnable / Summer Commercial");
    SouthFork.FlowBandSource = TEXT("physics/data/real_world/south_fork_american_chili_bar/flow_presets.json");
    SouthFork.FlowVisualDescription =
        TEXT("Default South Fork summer-commercial validation band from USGS-11445500 planning presets; keeps moderate tongues, wet rocks, and foam lines visible while low/high seasonal variants remain future capture targets.");
    SouthFork.FlowReferenceDischargeCfs = 1600.0f;
    SouthFork.WaterColor = FLinearColor(0.045f, 0.36f, 0.38f);
    SouthFork.TerrainColor = FLinearColor(0.35f, 0.30f, 0.21f);
    SouthFork.RockColor = FLinearColor(0.38f, 0.36f, 0.31f);
    SouthFork.FoliageColor = FLinearColor(0.22f, 0.38f, 0.15f);
    SouthFork.CanyonHeightCm = 850.0f;
    SouthFork.RiverHalfWidthCm = 335.0f;
    SouthFork.BankWidthCm = 720.0f;
    SouthFork.BendAmplitudeCm = 290.0f;
    SouthFork.TerrainReliefAmplitudeCm = 180.0f;
    SouthFork.HeightfieldPreviewAmplitudeCm = 115.0f;
    SouthFork.BoulderCount = 24;
    SouthFork.FoliageCount = 46;
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
        TEXT("stitched Colorado/Lees Ferry production-import pilot source drape generated from four official USDA/APFO NAIP 2048px tiles, plus stitched USGS 3DEP pilot DEM relief and a review-gated 2017px heightfield candidate sampled into canyon bank preview geometry; pilot source water/vegetation masks are sampled into terrain color, source-aware bank breakup patches, biome-specific sparse deadfall/grass/root ecology props, lit water variation, flow-band depth texture ribbons, flow-aware surface chop/turbidity patches, deterministic wet-rock, talus, sparse scrub, boulder placement, mask-aware canyon ground-cover cards, and river-specific atmospheric backdrop cards; all pilot derivatives remain review-gated until metadata review, mosaic/clip, river-mile stationing, hydrologic conditioning, release-aware masks, and guide/oarsman approval pass; rocks, foliage, water, foam, raft, and lighting still include first-party procedural proxy layers");
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
    Colorado.WaterColor = FLinearColor(0.34f, 0.28f, 0.19f);
    Colorado.TerrainColor = FLinearColor(0.48f, 0.30f, 0.18f);
    Colorado.RockColor = FLinearColor(0.55f, 0.32f, 0.20f);
    Colorado.FoliageColor = FLinearColor(0.30f, 0.32f, 0.18f);
    Colorado.CanyonHeightCm = 2600.0f;
    Colorado.RiverHalfWidthCm = 520.0f;
    Colorado.BankWidthCm = 1500.0f;
    Colorado.BendAmplitudeCm = 360.0f;
    Colorado.TerrainReliefAmplitudeCm = 650.0f;
    Colorado.HeightfieldPreviewAmplitudeCm = 360.0f;
    Colorado.BoulderCount = 20;
    Colorado.FoliageCount = 18;
    Colorado.FoamTrainCount = 9;
    Colorado.bDesertCanyon = true;
    Specs.Add(Colorado);

    FRaftSimEnvironmentPreviewSpec Pacuare;
    Pacuare.RiverId = TEXT("pacuare");
    Pacuare.DisplayName = TEXT("Pacuare River Rainforest");
    Pacuare.MapPackagePath = TEXT("/Game/RaftSim/Maps/EnvironmentPreviews/L_PacuareRainforest_PhotorealPreview");
    Pacuare.SourceManifest = TEXT("physics/data/real_world/pacuare_river_costa_rica/source_manifest.json");
    Pacuare.AerialDrapeImage =
        TEXT("physics/data/real_world/pacuare_river_costa_rica/imagery/production_import_pilot/source_drape_4096.png");
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
        TEXT("review-gated Pacuare production-import derivative placeholders generated from the selected NASA GIBS MODIS/Terra true-color seed and Copernicus DEM GLO-30 relief, normalized into a 4096px source drape, 2048px DEM relief, 2017px heightfield candidate, and 2048px water/vegetation masks; these remain coarse/cloudy proxy inputs until higher-resolution cloud-screened imagery, local hydrology/hydrography, protected-area review, and guide/outfitter validation are attached; first-party procedural rainforest leaf-litter, wet-rock, talus, mist, source-aware bank breakup patches, biome-specific deadfall/log/grass/root ecology props, waterfall curtain/plunge-mist proxy layers, lit water variation, flow-band depth texture ribbons, flow-aware surface chop/turbidity patches, dense mask-aware ground-cover/canopy cards, and humid atmospheric backdrop cards remain rights-safe proxy dressing; rocks, foliage, water, foam, raft, and lighting still include first-party procedural proxy layers");
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
    Pacuare.WaterColor = FLinearColor(0.035f, 0.32f, 0.27f);
    Pacuare.TerrainColor = FLinearColor(0.17f, 0.22f, 0.13f);
    Pacuare.RockColor = FLinearColor(0.20f, 0.24f, 0.20f);
    Pacuare.FoliageColor = FLinearColor(0.06f, 0.30f, 0.09f);
    Pacuare.CanyonHeightCm = 1450.0f;
    Pacuare.RiverHalfWidthCm = 305.0f;
    Pacuare.BankWidthCm = 680.0f;
    Pacuare.BendAmplitudeCm = 340.0f;
    Pacuare.TerrainReliefAmplitudeCm = 420.0f;
    Pacuare.HeightfieldPreviewAmplitudeCm = 260.0f;
    Pacuare.BoulderCount = 22;
    Pacuare.FoliageCount = 84;
    Pacuare.FoamTrainCount = 16;
    Pacuare.bHasWaterfalls = true;
    Specs.Add(Pacuare);

    return Specs;
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
        EmissiveScale->R = 0.34f;
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
        EmissiveScale->R = 0.18f;
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
        Material->SetShadingModel(MSM_Unlit);
        Material->BlendMode = BLEND_Opaque;
        Material->TwoSided = true;

        UMaterialExpressionVertexColor* VertexColor = NewObject<UMaterialExpressionVertexColor>(Material);
        Material->GetExpressionCollection().AddExpression(VertexColor);

        UMaterialExpressionConstant* EmissiveScale = NewObject<UMaterialExpressionConstant>(Material);
        EmissiveScale->R = 0.42f;
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

    static bool bWaterMaterialConfigured = false;
    if (Material && !bWaterMaterialConfigured)
    {
        Material->Modify();
        Material->SetShadingModel(MSM_DefaultLit);
        Material->BlendMode = BLEND_Opaque;
        Material->TwoSided = true;
        for (TObjectPtr<UMaterialExpression>& Expression : Material->GetExpressionCollection().Expressions)
        {
            if (UMaterialExpressionConstant* Constant = Cast<UMaterialExpressionConstant>(Expression.Get()))
            {
                Constant->R = 0.42f;
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
        bWaterMaterialConfigured = true;
    }

    return Material;
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
    const float HeightfieldMask = SmoothPreviewStep(
        ActiveRiverHalfWidth + 180.0f,
        ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 1450.0f : 820.0f),
        ChannelOffset);
    const float RidgePattern = (HeightfieldPreview->SampleLuma(U, V) - 0.5f) * Spec.HeightfieldPreviewAmplitudeCm;
    return RidgePattern * HeightfieldMask;
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
        SamplePreviewHeightfieldCm(Spec, HeightfieldPreview, X, Y, Offset) +
        SamplePreviewTerrainReliefCm(Spec, TerrainRelief, X, Y, Offset);
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

AActor* AddPreviewProceduralMeshActor(
    UWorld* World,
    const FString& Label,
    const TArray<FVector>& Vertices,
    const TArray<int32>& Triangles,
    const TArray<FVector>& Normals,
    const TArray<FVector2D>& UVs,
    const FLinearColor& Color,
    UMaterialInterface* MaterialOverride = nullptr,
    const TArray<FLinearColor>* VertexColorOverride = nullptr)
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
    MeshComponent->bUseComplexAsSimpleCollision = true;

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

    MeshComponent->CreateMeshSection_LinearColor(0, Vertices, Triangles, Normals, UVs, VertexColors, Tangents, true);
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

    constexpr int32 RingCount = 4;
    constexpr int32 SegmentCount = 9;
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
        Triangles.Add(SegmentIndex + NextSegment);
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

void AddPreviewTerrainMesh(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* AerialDrape,
    const FRaftSimPreviewImage* TerrainRelief,
    const FRaftSimPreviewImage* HeightfieldPreview,
    const FRaftSimPreviewImage* WaterMask,
    const FRaftSimPreviewImage* VegetationMask)
{
    constexpr int32 XSteps = 160;
    constexpr int32 YSteps = 56;
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
            const float Z = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
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
            FLinearColor TerrainColor = FMath::Lerp(Spec.TerrainColor, ShoulderColor, FMath::Clamp(BankT * 0.45f + CanyonT * 0.35f, 0.0f, 1.0f));
            if (AerialDrape && AerialDrape->IsValid())
            {
                FLinearColor SourceDrapeColor = AerialDrape->Sample(U, V);
                SourceDrapeColor = FMath::Lerp(
                    SourceDrapeColor,
                    Spec.bDesertCanyon ? FLinearColor(0.54f, 0.36f, 0.23f) : Spec.TerrainColor,
                    Spec.bHasWaterfalls ? 0.28f : 0.20f);
                SourceDrapeColor.R = FMath::Max(SourceDrapeColor.R, Spec.TerrainColor.R * 0.34f + 0.035f);
                SourceDrapeColor.G = FMath::Max(SourceDrapeColor.G, Spec.TerrainColor.G * 0.34f + 0.035f);
                SourceDrapeColor.B = FMath::Max(SourceDrapeColor.B, Spec.TerrainColor.B * 0.34f + 0.035f);
                SourceDrapeColor.A = 1.0f;
                const float SourceBlend = FMath::Clamp(
                    (Spec.bDesertCanyon ? 0.46f : (Spec.bHasWaterfalls ? 0.36f : 0.40f)) *
                        (0.35f + BankT * 0.45f + CanyonT * 0.32f + SourceVegetationT * 0.18f + SourceWaterT * 0.08f),
                    0.0f,
                    Spec.bDesertCanyon ? 0.46f : 0.40f);
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
            TerrainColor = ScalePreviewColor(TerrainColor, ColorNoise);
            Vertices.Add(FVector(X, Y, Z));
            UVs.Add(FVector2D(U * 12.0f, V * 4.0f));
            VertexColors.Add(TerrainColor);
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

    AddPreviewProceduralMeshActor(
        World,
        FString::Printf(TEXT("RaftSim_ProceduralValleyTerrain_%s"), *Spec.RiverId),
        Vertices,
        Triangles,
        Normals,
        UVs,
        Spec.TerrainColor,
        LoadOrCreatePreviewVertexColorMaterial(),
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

    constexpr int32 XTiles = 64;
    constexpr int32 YTiles = 20;
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

            const float DrapeWeight = Spec.bDesertCanyon ? 0.26f : (Spec.bHasWaterfalls ? 0.20f : 0.24f);
            FLinearColor SourceDrapeColor = AerialDrape->Sample(U, V);
            SourceDrapeColor = FMath::Lerp(
                SourceDrapeColor,
                Spec.bDesertCanyon ? FLinearColor(0.50f, 0.34f, 0.21f) : Spec.TerrainColor,
                Spec.bHasWaterfalls ? 0.44f : 0.34f);
            FLinearColor AerialColor = FMath::Lerp(Spec.TerrainColor, SourceDrapeColor, DrapeWeight);
            const float SourceWaterT = WaterMask && WaterMask->IsValid() ? WaterMask->SampleLuma(U, V) : 0.0f;
            const float SourceVegetationT = VegetationMask && VegetationMask->IsValid() ? VegetationMask->SampleLuma(U, V) : 0.0f;
            AerialColor = FMath::Lerp(
                AerialColor,
                ScalePreviewColor(Spec.FoliageColor, Spec.bHasWaterfalls ? 1.24f : 1.08f),
                FMath::Clamp(SourceVegetationT * (Spec.bDesertCanyon ? 0.10f : 0.22f), 0.0f, 0.28f));
            AerialColor = FMath::Lerp(
                AerialColor,
                ScalePreviewColor(Spec.WaterColor, 0.68f),
                FMath::Clamp(SourceWaterT * 0.16f, 0.0f, 0.18f));
            AerialColor.R = FMath::Max(AerialColor.R, Spec.TerrainColor.R * 0.80f + 0.04f);
            AerialColor.G = FMath::Max(AerialColor.G, Spec.TerrainColor.G * 0.80f + 0.04f);
            AerialColor.B = FMath::Max(AerialColor.B, Spec.TerrainColor.B * 0.80f + 0.04f);
            AerialColor.A = 1.0f;
            const float HalfLength = TileLength * 0.56f;
            const float HalfTileWidth = TileWidth * 0.56f;
            const float TileZOffset = 14.0f;
            const float X0 = X - HalfLength;
            const float X1 = X + HalfLength;
            const float Y0 = Y - HalfTileWidth;
            const float Y1 = Y + HalfTileWidth;

            TArray<FVector> Vertices;
            Vertices.Add(FVector(X0, Y0, GetPreviewTerrainHeightCm(Spec, X0, Y0, TerrainRelief, HeightfieldPreview) + TileZOffset));
            Vertices.Add(FVector(X0, Y1, GetPreviewTerrainHeightCm(Spec, X0, Y1, TerrainRelief, HeightfieldPreview) + TileZOffset));
            Vertices.Add(FVector(X1, Y0, GetPreviewTerrainHeightCm(Spec, X1, Y0, TerrainRelief, HeightfieldPreview) + TileZOffset));
            Vertices.Add(FVector(X1, Y1, GetPreviewTerrainHeightCm(Spec, X1, Y1, TerrainRelief, HeightfieldPreview) + TileZOffset));

            TArray<int32> Triangles = {0, 2, 1, 1, 2, 3};
            TArray<FVector> Normals = ComputePreviewMeshNormals(Vertices, Triangles);
            TArray<FVector2D> UVs = {
                FVector2D(0.0f, 0.0f),
                FVector2D(0.0f, 1.0f),
                FVector2D(1.0f, 0.0f),
                FVector2D(1.0f, 1.0f)};

            AddPreviewProceduralMeshActor(
                World,
                FString::Printf(TEXT("RaftSim_SourceAerialDrapeTile_%02d_%02d_%s"), XIndex, YIndex, *Spec.RiverId),
                Vertices,
                Triangles,
                Normals,
                UVs,
                AerialColor);
        }
    }
}

void AddPreviewRiverRibbonMesh(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec)
{
    constexpr int32 XSteps = 120;
    constexpr int32 CrossSteps = 10;
    const float MinX = -5600.0f;
    const float MaxX = 26200.0f;

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

    const FLinearColor DeepWater = ScalePreviewColor(Spec.WaterColor, Spec.bDesertCanyon ? 1.02f : 1.10f);
    const FLinearColor ShallowWater = Spec.bDesertCanyon
        ? FLinearColor(0.42f, 0.36f, 0.24f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.035f, 0.42f, 0.33f) : FLinearColor(0.055f, 0.50f, 0.53f));
    const FLinearColor SurfaceGlint = Spec.bDesertCanyon
        ? FLinearColor(0.58f, 0.49f, 0.34f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.13f, 0.58f, 0.48f) : FLinearColor(0.14f, 0.62f, 0.64f));
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float WaterBaseZ = GetPreviewWaterSurfaceBaseZCm(Spec);

    for (int32 XIndex = 0; XIndex <= XSteps; ++XIndex)
    {
        const float U = static_cast<float>(XIndex) / static_cast<float>(XSteps);
        const float X = FMath::Lerp(MinX, MaxX, U);
        const float CenterY = GetPreviewRiverCenterY(Spec, X);
        const float Width =
            ActiveRiverHalfWidth * (1.0f + 0.10f * FMath::Sin(X * 0.0012f) + (Spec.bDesertCanyon ? 0.18f : 0.05f));
        for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
        {
            const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
            const float Lateral = FMath::Lerp(-Width, Width, V);
            const float Wave = FMath::Sin(X * 0.011f + Lateral * 0.015f) * (Spec.bDesertCanyon ? 2.0f : 4.5f);
            const float EdgeT = FMath::Pow(FMath::Abs(V - 0.5f) * 2.0f, 1.35f);
            const float FlowNoise =
                0.50f + 0.30f * FMath::Sin(X * 0.0048f + Lateral * 0.010f) +
                0.20f * FMath::Sin(X * 0.013f - Lateral * 0.006f);
            FLinearColor WaterColor = FMath::Lerp(DeepWater, ShallowWater, FMath::Clamp(EdgeT * 0.55f, 0.0f, 1.0f));
            WaterColor = FMath::Lerp(
                WaterColor,
                SurfaceGlint,
                FMath::Clamp((1.0f - EdgeT * 0.45f) * FlowNoise * (Spec.bDesertCanyon ? 0.12f : 0.16f), 0.0f, 0.22f));
            Vertices.Add(FVector(X, CenterY + Lateral, WaterBaseZ + Wave));
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

    AddPreviewProceduralMeshActor(
        World,
        FString::Printf(TEXT("RaftSim_ProceduralRiverRibbon_%s"), *Spec.RiverId),
        Vertices,
        Triangles,
        Normals,
        UVs,
        Spec.WaterColor,
        LoadOrCreatePreviewWaterVertexColorMaterial(),
        &VertexColors);
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

    constexpr int32 Segments = 96;
    constexpr int32 CrossSteps = 2;
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
            const float Offset = SignedCenterOffset + Side * Width * (V - 0.5f);
            const float Y = CenterY + Offset;
            const float SurfaceWave = FMath::Sin(X * 0.011f + Y * 0.015f) * (Spec.bDesertCanyon ? 2.0f : 4.5f);
            const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview);
            const float Z = FMath::Max(TerrainZ + ZOffset, GetPreviewWaterSurfaceBaseZCm(Spec) + 3.0f + SurfaceWave + ZOffset * 0.25f);
            const float Fleck = 0.92f + 0.08f * FMath::Sin(X * 0.0053f + Y * 0.0037f);
            Vertices.Add(FVector(X, Y, Z));
            UVs.Add(FVector2D(U * 16.0f, V));
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
        LoadOrCreatePreviewVertexColorMaterial(),
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
        ? FLinearColor(0.24f, 0.18f, 0.13f)
        : FMath::Lerp(ScalePreviewColor(Spec.WaterColor, 0.48f), ScalePreviewColor(Spec.RockColor, 0.60f), 0.45f);
    const FLinearColor BankBand = Spec.bDesertCanyon
        ? FLinearColor(0.50f, 0.34f, 0.22f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.045f, 0.10f, 0.055f) : FLinearColor(0.16f, 0.17f, 0.13f));
    const FLinearColor GravelBand = Spec.bDesertCanyon
        ? FLinearColor(0.64f, 0.43f, 0.26f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.08f, 0.13f, 0.08f) : FLinearColor(0.22f, 0.22f, 0.17f));
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
            Side * (ActiveRiverHalfWidth + 82.0f * WetBankScale),
            (Spec.bDesertCanyon ? 145.0f : 105.0f) * WetBankScale,
            20.0f,
            WetEdge,
            BankBand);
        AddPreviewShoreRibbon(
            World,
            Spec,
            TerrainRelief,
            HeightfieldPreview,
            FString::Printf(TEXT("RaftSim_GravelMudBank_%s_%s"), Side < 0.0f ? TEXT("Left") : TEXT("Right"), *Spec.RiverId),
            Side * (ActiveRiverHalfWidth + 260.0f * WetBankScale),
            (Spec.bDesertCanyon ? 230.0f : 125.0f) * WetBankScale,
            24.0f,
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
    float ZOffset)
{
    if (!World)
    {
        return;
    }

    constexpr int32 Segments = 8;
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
            const float Cross = (V - 0.5f) * Width * (0.45f + 0.55f * LongitudinalTaper);
            const float Sway =
                FMath::Sin(Phase + U * UE_TWO_PI) * Width * 0.18f +
                FMath::Sin(Phase * 0.37f + U * UE_TWO_PI * 2.0f) * Width * 0.07f;
            const float Y = RiverCenterY + SignedCenterOffset + Side * Sway + Cross;
            const float Z = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief, HeightfieldPreview) + ZOffset;
            const float Fleck = FMath::Clamp(
                0.86f + 0.10f * FMath::Sin(Phase + U * 5.7f) + 0.06f * FMath::Sin(Phase * 0.71f + V * 4.3f),
                0.68f,
                1.04f);
            Vertices.Add(FVector(X, Y, Z));
            UVs.Add(FVector2D(U * 3.0f, V));
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
        LoadOrCreatePreviewVertexColorMaterial(),
        &VertexColors);
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
    const int32 PatchCount = Spec.bDesertCanyon ? 96 : (Spec.bHasWaterfalls ? 118 : 104);
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
            X - (Spec.bDesertCanyon ? 310.0f : 230.0f),
            (Spec.bDesertCanyon ? 660.0f : 470.0f) * (0.78f + 0.10f * static_cast<float>(PatchIndex % 5)),
            SignedOffset,
            (Spec.bDesertCanyon ? 155.0f : 118.0f) * (0.74f + 0.08f * static_cast<float>(PatchIndex % 4)),
            Phase,
            InnerColor,
            OuterColor,
            Spec.bDesertCanyon ? 19.0f : 16.0f);
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

    const int32 BandCount = Spec.bDesertCanyon ? 7 : (Spec.bHasWaterfalls ? 5 : 4);
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float BaseBandOffset = ActiveRiverHalfWidth +
        (Spec.bDesertCanyon ? Spec.BankWidthCm * 0.72f + 380.0f : Spec.BankWidthCm * 0.35f + 190.0f);
    const float BandSpacing = Spec.bDesertCanyon ? 315.0f : (Spec.bHasWaterfalls ? 150.0f : 180.0f);
    const float BandWidth = Spec.bDesertCanyon ? 125.0f : (Spec.bHasWaterfalls ? 78.0f : 92.0f);

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
                InnerColor = ScalePreviewColor(FLinearColor(0.42f, 0.28f, 0.17f), Warmth);
                OuterColor = ScalePreviewColor(FLinearColor(0.70f, 0.51f, 0.32f), 0.90f + 0.03f * static_cast<float>(BandIndex % 2));
            }
            else if (Spec.bHasWaterfalls)
            {
                InnerColor = ScalePreviewColor(FLinearColor(0.030f, 0.070f, 0.038f), 0.92f + 0.04f * static_cast<float>(BandIndex % 2));
                OuterColor = ScalePreviewColor(FLinearColor(0.075f, 0.120f, 0.060f), 0.86f + 0.05f * static_cast<float>(BandIndex % 3));
            }
            else
            {
                InnerColor = ScalePreviewColor(FLinearColor(0.14f, 0.13f, 0.10f), 0.92f + 0.04f * static_cast<float>(BandIndex % 2));
                OuterColor = ScalePreviewColor(FLinearColor(0.29f, 0.25f, 0.17f), 0.88f + 0.04f * static_cast<float>(BandIndex % 3));
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
    const int32 CardsPerSide = Spec.bDesertCanyon ? 74 : (Spec.bHasWaterfalls ? 178 : 126);
    const float NearBankOffset = Spec.bDesertCanyon ? 520.0f : 260.0f;
    const float FarBankOffset = Spec.bDesertCanyon ? 1880.0f : (Spec.bHasWaterfalls ? 1180.0f : 980.0f);

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
                CardIndex % 9 == 0 &&
                BaseOffset < ActiveRiverHalfWidth + NearBankOffset + FarBankOffset * 0.62f;
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
                    Spec.bHasWaterfalls ? 1.18f : 1.08f);
                AddPreviewMeshActor(
                    World,
                    PlaneMesh,
                    FString::Printf(TEXT("RaftSim_MaskAwareCanopyCard_%03d_%s"), CardIndex + SideIndex * CardsPerSide, *Spec.RiverId),
                    FVector(X, Y, TerrainZ + 78.0f),
                    FRotator(48.0f + 4.0f * FMath::Sin(Phase), Yaw, 0.0f),
                    FVector(
                        0.86f + 0.18f * FMath::Abs(FMath::Sin(Phase)),
                        0.22f,
                        1.0f),
                    CanopyCardColor);
            }
            else
            {
                AddPreviewMeshActor(
                    World,
                    PlaneMesh,
                    FString::Printf(TEXT("RaftSim_MaskAwareGroundCover_%03d_%s"), CardIndex + SideIndex * CardsPerSide, *Spec.RiverId),
                    FVector(X, Y, TerrainZ + (Spec.bDesertCanyon ? 18.0f : 15.0f)),
                    FRotator(0.0f, Yaw, 0.0f),
                    FVector(
                        Spec.bDesertCanyon ? 0.74f : (Spec.bHasWaterfalls ? 0.66f : 0.54f),
                        Spec.bDesertCanyon ? 0.28f : (Spec.bHasWaterfalls ? 0.32f : 0.26f),
                        1.0f),
                    GroundColor);
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

    constexpr int32 Segments = 10;
    TArray<FVector> Vertices;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<int32> Triangles;
    Vertices.Reserve((Segments + 1) * 2);
    UVs.Reserve((Segments + 1) * 2);
    Triangles.Reserve(Segments * 6);

    for (int32 SegmentIndex = 0; SegmentIndex <= Segments; ++SegmentIndex)
    {
        const float T = static_cast<float>(SegmentIndex) / static_cast<float>(Segments);
        const float X = StartX + Length * T;
        const float RiverCenterY = GetPreviewRiverCenterY(Spec, X);
        const float Sway = FMath::Sin(Phase + T * UE_TWO_PI) * Width * 0.32f;
        const float Taper = FMath::Sin(T * PI);
        const float LocalHalfWidth = FMath::Max(6.0f, Width * (0.18f + 0.62f * Taper));
        const float CenterY = RiverCenterY + LateralOffset + Sway;
        const float SurfaceWave = FMath::Sin(X * 0.011f + CenterY * 0.015f) * (Spec.bDesertCanyon ? 2.0f : 4.5f);
        const float Z = GetPreviewWaterSurfaceBaseZCm(Spec) + 15.0f + SurfaceWave + 2.0f * FMath::Sin(Phase * 1.7f + T * PI);

        Vertices.Add(FVector(X, CenterY - LocalHalfWidth, Z));
        Vertices.Add(FVector(X, CenterY + LocalHalfWidth, Z + 0.6f));
        UVs.Add(FVector2D(T, 0.0f));
        UVs.Add(FVector2D(T, 1.0f));
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
    AddPreviewProceduralMeshActor(World, Label, Vertices, Triangles, Normals, UVs, Color);
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
        const float LocalHalfWidth = FMath::Max(5.0f, Width * (0.16f + 0.48f * Taper));
        const float CenterY = RiverCenterY + LateralOffset + Sway;
        const float SurfaceWave = FMath::Sin(X * 0.011f + CenterY * 0.015f) * (Spec.bDesertCanyon ? 2.0f : 4.5f);
        const float Z = WaterBaseZ + 20.0f + SurfaceWave + 1.6f * FMath::Sin(Phase * 1.3f + T * PI);
        const float Pulse =
            FMath::Clamp(0.44f + 0.34f * FMath::Sin(Phase + T * UE_TWO_PI * 3.0f) + 0.16f * Taper, 0.0f, 1.0f);
        const FLinearColor FlowColor = ClampPreviewColor(FMath::Lerp(ShadowColor, HighlightColor, Pulse));

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
    const int32 BaseRibbonCount = Spec.bDesertCanyon ? 30 : (Spec.bHasWaterfalls ? 58 : 46);
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
        const float X = FMath::Lerp(-5050.0f, 25300.0f, T);
        const float LateralJitter =
            FMath::Sin(static_cast<float>(RibbonIndex) * 1.63f) * ActiveRiverHalfWidth * 0.74f +
            FMath::Sin(static_cast<float>(RibbonIndex) * 0.41f) * ActiveRiverHalfWidth * 0.12f;
        const float Length =
            (Spec.bDesertCanyon ? 1040.0f : (Spec.bHasWaterfalls ? 760.0f : 850.0f)) *
            (0.72f + 0.18f * static_cast<float>(RibbonIndex % 5)) * TextureScale;
        const float Width =
            (Spec.bDesertCanyon ? 26.0f : 18.0f) *
            (0.78f + 0.12f * static_cast<float>(RibbonIndex % 4)) *
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

    const int32 BaseTurbidityCount = Spec.bDesertCanyon ? 18 : (Spec.bHasWaterfalls ? 22 : 18);
    const int32 TurbidityCount =
        FMath::Max(1, FMath::RoundToInt(static_cast<float>(BaseTurbidityCount) * FMath::Clamp(FlowEnergy, 0.70f, 1.20f)));
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
    const int32 BaseCurrentCount = Spec.bDesertCanyon ? 7 : (Spec.bHasWaterfalls ? 10 : 9);
    const int32 CurrentCount =
        FMath::Max(1, FMath::RoundToInt(static_cast<float>(BaseCurrentCount) * FMath::Clamp(CurrentCueScale, 0.5f, 1.3f)));
    for (int32 CurrentIndex = 0; CurrentIndex < CurrentCount; ++CurrentIndex)
    {
        const float X = -2600.0f + static_cast<float>(CurrentIndex) * (26000.0f / FMath::Max(1, CurrentCount));
        const float Lateral = FMath::Sin(static_cast<float>(CurrentIndex) * 1.37f) * ActiveRiverHalfWidth * 0.30f;
        const float Length = (Spec.bDesertCanyon ? 1380.0f : 980.0f) * CurrentCueScale;
        const FLinearColor DetailColor =
            FMath::Lerp(CurrentShadow, CurrentHighlight, 0.50f + 0.18f * FMath::Sin(static_cast<float>(CurrentIndex) * 0.91f));
        AddPreviewFoamRibbon(
            World,
            Spec,
            FString::Printf(TEXT("RaftSim_CurrentStreak_%02d_%s"), CurrentIndex, *Spec.RiverId),
            X,
            Length,
            Lateral,
            (9.0f + 3.0f * static_cast<float>(CurrentIndex % 3)) * CurrentCueScale,
            static_cast<float>(CurrentIndex) * 0.61f,
            DetailColor);
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
    const int32 GlintCount = Spec.bDesertCanyon ? 34 : (Spec.bHasWaterfalls ? 58 : 44);
    const FLinearColor GlintColor = Spec.bDesertCanyon
        ? FLinearColor(0.72f, 0.66f, 0.50f, 1.0f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.54f, 0.92f, 0.82f, 1.0f) : FLinearColor(0.60f, 0.94f, 0.92f, 1.0f));

    for (int32 GlintIndex = 0; GlintIndex < GlintCount; ++GlintIndex)
    {
        const float T = static_cast<float>(GlintIndex) / static_cast<float>(FMath::Max(1, GlintCount - 1));
        const float X = FMath::Lerp(-4300.0f, 24800.0f, T);
        const float RiverCenterY = GetPreviewRiverCenterY(Spec, X);
        const float Lateral = FMath::Sin(static_cast<float>(GlintIndex) * 2.31f) * ActiveRiverHalfWidth * 0.62f;
        const float WidthScale = 0.09f + 0.022f * static_cast<float>(GlintIndex % 4);
        const float LengthScale = (Spec.bDesertCanyon ? 1.10f : 0.78f) + 0.12f * static_cast<float>(GlintIndex % 5);
        const float Opacity = Spec.bDesertCanyon ? 0.16f : (Spec.bHasWaterfalls ? 0.24f : 0.20f);
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
        for (int32 HazeIndex = 0; HazeIndex < 7; ++HazeIndex)
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
                FVector(16.0f, 3.4f, 1.0f),
                FLinearColor(0.72f, 0.64f, 0.50f, 1.0f),
                0.12f);
        }
    }

    if (Spec.bHasWaterfalls)
    {
        for (int32 SprayIndex = 0; SprayIndex < 14; ++SprayIndex)
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
                FVector(3.6f + 0.35f * static_cast<float>(SprayIndex % 3), 0.72f, 1.0f),
                FLinearColor(0.58f, 0.88f, 0.78f, 1.0f),
                0.20f);
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
    const int32 CloudCount = Spec.bDesertCanyon ? 6 : (Spec.bHasWaterfalls ? 10 : 7);

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
            FVector(LengthScale * (0.82f + 0.06f * static_cast<float>(CloudIndex % 4)), HeightScale, 1.0f),
            ScalePreviewColor(CloudColor, 0.92f + 0.05f * static_cast<float>(CloudIndex % 3)),
            Spec.bDesertCanyon ? 0.17f : (Spec.bHasWaterfalls ? 0.24f : 0.19f));
    }

    const int32 HorizonBandCount = Spec.bDesertCanyon ? 5 : (Spec.bHasWaterfalls ? 8 : 6);
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
            FVector(Spec.bDesertCanyon ? 15.5f : 11.0f, Spec.bHasWaterfalls ? 3.4f : 2.8f, 1.0f),
            ScalePreviewColor(HorizonColor, 0.90f + 0.04f * static_cast<float>(BandIndex % 4)),
            Spec.bDesertCanyon ? 0.19f : (Spec.bHasWaterfalls ? 0.26f : 0.20f));
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
    if (!World || !CubeMesh || !CylinderMesh || !PlaneMesh)
    {
        return;
    }

    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
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
            CubeMesh,
            FString::Printf(TEXT("RaftSim_BiomeDeadfallLog_%03d_%s"), DeadfallIndex, *Spec.RiverId),
            FVector(X, Y, TerrainZ + 18.0f),
            FRotator(0.0f, static_cast<float>((DeadfallIndex * 41) % 360), 4.0f * FMath::Sin(Phase)),
            FVector(LengthScale * (0.74f + 0.10f * static_cast<float>(DeadfallIndex % 5)), ThicknessScale, ThicknessScale * 0.72f),
            DeadfallColor);
    }

    const int32 GrassCardCount = Spec.bDesertCanyon ? 74 : (Spec.bHasWaterfalls ? 178 : 126);
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
        AddPreviewMeshActor(
            World,
            PlaneMesh,
            FString::Printf(TEXT("RaftSim_BiomeBankGrassCard_%03d_%s"), CardIndex, *Spec.RiverId),
            FVector(X, Y, TerrainZ + (Spec.bHasWaterfalls ? 62.0f : 42.0f)),
            FRotator(64.0f + 5.0f * FMath::Sin(Phase), static_cast<float>((CardIndex * 37) % 360), 0.0f),
            FVector(
                Spec.bHasWaterfalls ? 0.62f : (Spec.bDesertCanyon ? 0.42f : 0.48f),
                Spec.bHasWaterfalls ? 0.18f : 0.13f,
                1.0f),
            CardColor);
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
            CubeMesh,
            FString::Printf(TEXT("RaftSim_BiomeRootRunner_%03d_%s"), RootIndex, *Spec.RiverId),
            FVector(X, Y, TerrainZ + 11.0f),
            FRotator(0.0f, static_cast<float>((RootIndex * 53) % 360), 2.0f * FMath::Sin(Phase)),
            FVector(Spec.bHasWaterfalls ? 1.05f : 0.72f, 0.030f, 0.025f),
            ScalePreviewColor(RootColor, 0.82f + 0.06f * static_cast<float>(RootIndex % 4)));
    }
}

void AddPreviewRaftForeground(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec, UStaticMesh* CubeMesh, UStaticMesh* CylinderMesh)
{
    if (!World || !CubeMesh || !CylinderMesh)
    {
        return;
    }

    auto AddRaftProxyPart = [&](UStaticMesh* Mesh, const FString& Label, const FVector& Location, const FRotator& Rotation, const FVector& Scale, const FLinearColor& Color)
    {
        AStaticMeshActor* Actor = AddPreviewMeshActor(World, Mesh, Label, Location, Rotation, Scale, Color);
        if (Actor && Actor->GetStaticMeshComponent())
        {
            Actor->GetStaticMeshComponent()->SetCastShadow(false);
        }
    };

    const float BaseX = -4920.0f;
    const float CenterY = GetPreviewRiverCenterY(Spec, BaseX);
    const float Z = 30.0f;
    AddRaftProxyPart(
        CylinderMesh,
        FString::Printf(TEXT("RaftSim_ForegroundRaft_LeftTube_%s"), *Spec.RiverId),
        FVector(BaseX + 180.0f, CenterY - 92.0f, Z),
        FRotator(0.0f, 90.0f, 0.0f),
        FVector(0.38f, 0.38f, 2.9f),
        Spec.RaftColor);
    AddRaftProxyPart(
        CylinderMesh,
        FString::Printf(TEXT("RaftSim_ForegroundRaft_RightTube_%s"), *Spec.RiverId),
        FVector(BaseX + 180.0f, CenterY + 92.0f, Z),
        FRotator(0.0f, 90.0f, 0.0f),
        FVector(0.38f, 0.38f, 2.9f),
        Spec.RaftColor);
    AddRaftProxyPart(
        CylinderMesh,
        FString::Printf(TEXT("RaftSim_ForegroundRaft_Bow_%s"), *Spec.RiverId),
        FVector(BaseX + 470.0f, CenterY, Z + 3.0f),
        FRotator(90.0f, 0.0f, 0.0f),
        FVector(0.36f, 0.36f, 1.9f),
        Spec.RaftColor);
    AddRaftProxyPart(
        CubeMesh,
        FString::Printf(TEXT("RaftSim_ForegroundRaft_Floor_%s"), *Spec.RiverId),
        FVector(BaseX + 92.0f, CenterY, 11.0f),
        FRotator::ZeroRotator,
        FVector(1.35f, 0.42f, 0.04f),
        FLinearColor(0.08f, 0.085f, 0.075f));
}

void AddPreviewLightRig(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec)
{
    if (!World || !GEditor)
    {
        return;
    }

    ADirectionalLight* Sun = Cast<ADirectionalLight>(
        GEditor->AddActor(World->GetCurrentLevel(), ADirectionalLight::StaticClass(), FTransform(FRotator(-32.0f, -38.0f, 0.0f))));
    if (Sun)
    {
        Sun->SetActorLabel(TEXT("RaftSim_Sun_LumenPreview"));
        Sun->GetLightComponent()->SetIntensity(Spec.bDesertCanyon ? 18.0f : 14.0f);
        Sun->GetLightComponent()->SetLightColor(Spec.bDesertCanyon ? FLinearColor(1.0f, 0.84f, 0.66f) : FLinearColor(0.93f, 0.97f, 1.0f));
    }

    ASkyLight* SkyLight = Cast<ASkyLight>(
        GEditor->AddActor(World->GetCurrentLevel(), ASkyLight::StaticClass(), FTransform(FRotator::ZeroRotator, FVector(0.0f, 0.0f, 1000.0f))));
    if (SkyLight)
    {
        SkyLight->SetActorLabel(TEXT("RaftSim_SkyLight_PhotorealPreview"));
        SkyLight->GetLightComponent()->SetIntensity(Spec.bDesertCanyon ? 2.20f : 1.75f);
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
        Fog->GetComponent()->SetFogDensity(Spec.bHasWaterfalls ? 0.026f : (Spec.bDesertCanyon ? 0.006f : 0.010f));
    }
}

void AddPreviewCameraAndStart(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec)
{
    if (!World || !GEditor)
    {
        return;
    }

    ACameraActor* Camera = Cast<ACameraActor>(
        GEditor->AddActor(World->GetCurrentLevel(), ACameraActor::StaticClass(), FTransform(FRotator(-6.5f, 0.0f, 0.0f), FVector(-5250.0f, GetPreviewRiverCenterY(Spec, -5250.0f), 165.0f))));
    if (Camera)
    {
        Camera->SetActorLabel(TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"));
        Camera->GetCameraComponent()->FieldOfView = Spec.bDesertCanyon ? 73.0f : 76.0f;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_VignetteIntensity = true;
        Camera->GetCameraComponent()->PostProcessSettings.VignetteIntensity = 0.10f;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_Sharpen = true;
        Camera->GetCameraComponent()->PostProcessSettings.Sharpen = 0.35f;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_AutoExposureMethod = true;
        Camera->GetCameraComponent()->PostProcessSettings.AutoExposureMethod = AEM_Manual;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_AutoExposureBias = true;
        Camera->GetCameraComponent()->PostProcessSettings.AutoExposureBias = 0.0f;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_AutoExposureApplyPhysicalCameraExposure = true;
        Camera->GetCameraComponent()->PostProcessSettings.AutoExposureApplyPhysicalCameraExposure = 0;
        GEditor->SelectActor(Camera, true, false, true);
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

FString GetPreviewFidelityNote(const FRaftSimEnvironmentPreviewSpec& Spec)
{
    if (!Spec.SourceDrapeDescription.IsEmpty())
    {
        return Spec.SourceDrapeDescription;
    }

    return TEXT("source-aware procedural blockout with generated valley, river, foam, rocks, foliage, and raft proxies; not yet production photoreal");
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
    CaptureComponent->TextureTarget = RenderTarget;
    CaptureComponent->CaptureSource = SCS_FinalColorLDR;
    CaptureComponent->bCaptureEveryFrame = false;
    CaptureComponent->bCaptureOnMovement = false;
    if (bHideForegroundRaftProxies)
    {
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            AActor* Actor = *It;
            if (Actor && Actor->GetActorLabel().StartsWith(TEXT("RaftSim_ForegroundRaft_")))
            {
                CaptureComponent->HideActorComponents(Actor);
            }
        }
    }
    CaptureComponent->CaptureScene();
    FlushRenderingCommands();
    FPlatformProcess::Sleep(0.06f);
    CaptureComponent->CaptureScene();
    FlushRenderingCommands();

    FTextureRenderTargetResource* RenderTargetResource = RenderTarget->GameThread_GetRenderTargetResource();
    TArray<FColor> ImageData;
    if (!RenderTargetResource || !RenderTargetResource->ReadPixels(ImageData) ||
        ImageData.Num() != CaptureWidth * CaptureHeight)
    {
        SceneCapture->Destroy();
        RenderTarget->ReleaseResource();
        OutSummary += FString::Printf(TEXT("Failed to read rendered pixels for %s\n"), *Spec.RiverId);
        return false;
    }

    for (FColor& Pixel : ImageData)
    {
        Pixel.A = 255;
    }

    TArray64<uint8> CompressedPng;
    FImageUtils::PNGCompressImageArray(CaptureWidth, CaptureHeight, MakeArrayView(ImageData), CompressedPng);

    OutRelativeCapturePath = GetPreviewCaptureRelativePath(Spec, CaptureId);
    const FString AbsoluteCapturePath = FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), OutRelativeCapturePath));
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);
    const bool bSaved = FFileHelper::SaveArrayToFile(CompressedPng, *AbsoluteCapturePath);

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
    UStaticMesh* PcgTreeMeshA = LoadPreviewMesh(TEXT("/PCG/SampleContent/SimpleForest/Meshes/PCG_Tree_01.PCG_Tree_01"));
    UStaticMesh* PcgTreeMeshB = LoadPreviewMesh(TEXT("/PCG/SampleContent/SimpleForest/Meshes/PCG_Tree_02.PCG_Tree_02"));
    UStaticMesh* PcgTreeMeshC = LoadPreviewMesh(TEXT("/PCG/SampleContent/SimpleForest/Meshes/PCG_Tree_03.PCG_Tree_03"));
    UStaticMesh* PcgSeedlingMesh =
        LoadPreviewMesh(TEXT("/PCG/SampleContent/SimpleForest/Meshes/PCG_Seedling_01.PCG_Seedling_01"));

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

    AddPreviewLightRig(World, Spec);

    AddPreviewTerrainMesh(World, Spec, AerialDrapePtr, TerrainReliefPtr, HeightfieldPreviewPtr, WaterMaskPtr, VegetationMaskPtr);
    AddPreviewAerialDrapeTiles(World, Spec, AerialDrapePtr, TerrainReliefPtr, HeightfieldPreviewPtr, WaterMaskPtr, VegetationMaskPtr);
    AddPreviewRiverRibbonMesh(World, Spec);
    AddPreviewWetBankDressing(World, Spec, TerrainReliefPtr, HeightfieldPreviewPtr);
    AddPreviewSourceAwareBankBreakupDetail(World, Spec, TerrainReliefPtr, HeightfieldPreviewPtr, WaterMaskPtr, VegetationMaskPtr);
    AddPreviewProceduralEnvironmentDetail(World, Spec, TerrainReliefPtr, HeightfieldPreviewPtr, WaterMaskPtr, VegetationMaskPtr, SphereMesh);
    AddPreviewProceduralBankTextureCards(
        World,
        Spec,
        TerrainReliefPtr,
        HeightfieldPreviewPtr,
        WaterMaskPtr,
        VegetationMaskPtr,
        PlaneMesh);
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
    AddPreviewWaterSurfaceDetail(World, Spec);
    AddPreviewFlowBandTextureDetail(World, Spec);
    AddPreviewWaterSurfaceChopAndTurbidityDetail(World, Spec);
    AddPreviewFoamAndHydraulics(World, Spec);
    AddPreviewSurfaceAtmosphereAndSprayDetail(World, Spec, TerrainReliefPtr, HeightfieldPreviewPtr, PlaneMesh);
    AddPreviewWaterfallAndPlungeMistDetail(World, Spec, TerrainReliefPtr, HeightfieldPreviewPtr, PlaneMesh, CubeMesh);
    AddPreviewRiverAtmosphericBackdropDetail(World, Spec, TerrainReliefPtr, HeightfieldPreviewPtr, PlaneMesh);

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
        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainReliefPtr, HeightfieldPreviewPtr);
        const float Scale = Spec.bDesertCanyon ? 1.6f : 1.0f + 0.35f * static_cast<float>(BoulderIndex % 3);
        const float BoulderWaterT = SamplePreviewMaskAtWorld(Spec, WaterMaskPtr, X, Y);
        const FLinearColor BoulderColor = FMath::Lerp(
            Spec.RockColor,
            FMath::Lerp(ScalePreviewColor(Spec.RockColor, 0.46f), ScalePreviewColor(Spec.WaterColor, 0.34f), 0.30f),
            FMath::Clamp(BoulderWaterT * 0.36f, 0.0f, 0.42f));
        AddPreviewIrregularRockActor(
            World,
            FString::Printf(TEXT("RaftSim_SourceAwareBoulder_%02d_%s"), BoulderIndex, *Spec.RiverId),
            FVector(X, Y, FMath::Max(20.0f, TerrainZ + 18.0f + 8.0f * static_cast<float>(BoulderIndex % 4))),
            static_cast<float>(BoulderIndex * 31),
            FVector(Scale * 1.18f, Scale * 0.92f, Scale * 0.54f),
            BoulderColor,
            BoulderIndex + 3900);
        const float BoulderLateralOffset = Y - GetPreviewRiverCenterY(Spec, X);
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

    for (int32 FoliageIndex = 0; FoliageIndex < Spec.FoliageCount; ++FoliageIndex)
    {
        const float Side = (FoliageIndex % 2 == 0) ? -1.0f : 1.0f;
        const float BankOffset = Spec.bDesertCanyon ? ActiveRiverHalfWidth + 1350.0f : ActiveRiverHalfWidth + 620.0f;
        const float FoliageT = static_cast<float>(FoliageIndex) / static_cast<float>(FMath::Max(1, Spec.FoliageCount - 1));
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
        const float FoliageMaskT = SamplePreviewMaskAtWorld(Spec, VegetationMaskPtr, X, Y);
        const FLinearColor CanopyColor = Spec.bDesertCanyon
            ? FLinearColor(0.22f, 0.28f, 0.13f)
            : FLinearColor(
                  FMath::Clamp(Spec.FoliageColor.R + 0.025f * static_cast<float>(FoliageIndex % 3), 0.0f, 1.0f),
                  FMath::Clamp(Spec.FoliageColor.G + 0.055f * static_cast<float>((FoliageIndex + 1) % 4) + FoliageMaskT * 0.055f, 0.0f, 1.0f),
                  FMath::Clamp(Spec.FoliageColor.B + 0.025f * static_cast<float>((FoliageIndex + 2) % 3), 0.0f, 1.0f));
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
                CanopyColor);
        }
        else
        {
            AddPreviewMeshActor(
                World,
                CylinderMesh,
                FString::Printf(TEXT("RaftSim_FoliageTrunk_%02d_%s"), FoliageIndex, *Spec.RiverId),
                FVector(X, Y, TerrainZ + 78.0f * Height * 0.46f),
                FRotator::ZeroRotator,
                FVector(Spec.bDesertCanyon ? 0.11f : 0.14f, Spec.bDesertCanyon ? 0.11f : 0.14f, Height * 0.82f),
                Spec.bDesertCanyon ? FLinearColor(0.21f, 0.18f, 0.10f) : FLinearColor(0.20f, 0.12f, 0.07f));

            const int32 CanopyLobes = Spec.bHasWaterfalls ? 5 : (Spec.bDesertCanyon ? 2 : 3);
            for (int32 LobeIndex = 0; LobeIndex < CanopyLobes; ++LobeIndex)
            {
                const float AngleRadians = FMath::DegreesToRadians(static_cast<float>((FoliageIndex * 47 + LobeIndex * 83) % 360));
                const float Radius = (LobeIndex == 0) ? 0.0f : (Spec.bHasWaterfalls ? 82.0f : 56.0f);
                const float LobeX = X + FMath::Cos(AngleRadians) * Radius;
                const float LobeY = Y + FMath::Sin(AngleRadians) * Radius;
                AddPreviewMeshActor(
                    World,
                    SphereMesh,
                    FString::Printf(TEXT("RaftSim_FoliageCanopy_%02d_%02d_%s"), FoliageIndex, LobeIndex, *Spec.RiverId),
                    FVector(LobeX, LobeY, TerrainZ + 112.0f * Height + 18.0f * static_cast<float>(LobeIndex % 3)),
                    FRotator(0.0f, static_cast<float>((FoliageIndex * 47 + LobeIndex * 19) % 360), 0.0f),
                    FVector(CanopyWidth * (1.08f - 0.08f * static_cast<float>(LobeIndex % 2)), CanopyWidth * (0.82f + 0.07f * static_cast<float>(LobeIndex % 3)), Height * (Spec.bHasWaterfalls ? 0.34f : 0.28f)),
                    CanopyColor);
            }
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
                    CanopyColor,
                    Spec.bHasWaterfalls ? FLinearColor(0.035f, 0.20f, 0.07f) : FLinearColor(0.13f, 0.26f, 0.10f),
                    FMath::Clamp(0.35f + UnderstoryMaskT * 0.18f, 0.35f, 0.55f));
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
                    AddPreviewMeshActor(
                        World,
                        SphereMesh,
                        FString::Printf(TEXT("RaftSim_Understory_%02d_%02d_%s"), FoliageIndex, UnderstoryIndex, *Spec.RiverId),
                        FVector(UnderstoryX, UnderstoryY, UnderstoryZ + 30.0f),
                        FRotator(0.0f, static_cast<float>((FoliageIndex * 29 + UnderstoryIndex * 67) % 360), 0.0f),
                        FVector(0.48f, 0.36f, 0.22f),
                        UnderstoryColor);
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
                AddPreviewMeshActor(
                    World,
                    SphereMesh,
                    FString::Printf(TEXT("RaftSim_CanyonScrub_%02d_%s"), FoliageIndex, *Spec.RiverId),
                    FVector(ScrubX, ScrubY, ScrubZ + 18.0f),
                    FRotator(0.0f, static_cast<float>((FoliageIndex * 37) % 360), 0.0f),
                    FVector(0.24f, 0.18f, 0.12f),
                    ScrubColor);
            }
        }
    }

    AddPreviewCameraAndStart(World, Spec);
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

    bCreatePhotorealEnvironmentPreviewMapsOnStartup =
        FParse::Param(FCommandLine::Get(), TEXT("RaftSimCreatePhotorealEnvironmentPreviewMaps"));
    bCapturePhotorealEnvironmentPreviewsOnStartup =
        FParse::Param(FCommandLine::Get(), TEXT("RaftSimCapturePhotorealEnvironmentPreviews"));
    bExitAfterPhotorealEnvironmentAutomation =
        FParse::Param(FCommandLine::Get(), TEXT("RaftSimExitAfterEnvironmentAutomation"));

    if (bCreatePhotorealEnvironmentPreviewMapsOnStartup || bCapturePhotorealEnvironmentPreviewsOnStartup)
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
    if (!FPaths::FileExists(GeospatialAttachmentLedgerAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing production geospatial attachment ledger: %s\n"), *GeospatialAttachmentLedgerAbsolutePath);
        return false;
    }

    OutSummary += FString::Printf(TEXT("Using photoreal river source plan: %s\n"), *SourcePlanRelativePath);
    OutSummary += FString::Printf(TEXT("Using first-party procedural environment asset plan: %s\n"), *ProceduralAssetPlanRelativePath);
    OutSummary += FString::Printf(TEXT("Using first-party procedural material recipe plan: %s\n"), *ProceduralMaterialRecipePlanRelativePath);
    OutSummary += FString::Printf(TEXT("Using production geospatial attachment ledger: %s\n"), *GeospatialAttachmentLedgerRelativePath);

    bool bAllSaved = true;
    for (const FRaftSimEnvironmentPreviewSpec& Spec : GetEnvironmentPreviewSpecs())
    {
        OutSummary += FString::Printf(TEXT("Generating %s preview map.\n"), *Spec.DisplayName);
        bAllSaved &= BuildPreviewMapForSpec(Spec, OutSummary);
    }

    return bAllSaved;
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
    if (!FPaths::FileExists(GeospatialAttachmentLedgerAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing production geospatial attachment ledger for capture: %s\n"), *GeospatialAttachmentLedgerAbsolutePath);
        return false;
    }
    OutSummary += FString::Printf(TEXT("Using production geospatial attachment ledger: %s\n"), *GeospatialAttachmentLedgerRelativePath);

    FString EntriesJson;
    bool bAllCaptured = true;
    const TArray<FRaftSimEnvironmentPreviewSpec> Specs = GetEnvironmentPreviewSpecs();
    for (int32 Index = 0; Index < Specs.Num(); ++Index)
    {
        const FRaftSimEnvironmentPreviewSpec& Spec = Specs[Index];
        FString GuideSeatCapturePath = GetPreviewCaptureRelativePath(Spec, TEXT("guide_seat_downstream"));
        FString RiverEyeCapturePath = GetPreviewCaptureRelativePath(Spec, TEXT("river_eye_downstream"));
        FString WarmupGuideSeatCapturePath = GuideSeatCapturePath;
        CapturePreviewImageForSpec(
            Spec,
            CaptureRoot,
            WarmupGuideSeatCapturePath,
            TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
            TEXT("guide_seat_downstream"),
            TEXT("guide-seat downstream warm-up"),
            true,
            OutSummary);
        const bool bGuideSeatCaptured = CapturePreviewImageForSpec(
            Spec,
            CaptureRoot,
            GuideSeatCapturePath,
            TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
            TEXT("guide_seat_downstream"),
            TEXT("guide-seat downstream"),
            true,
            OutSummary);
        const bool bRiverEyeCaptured = CapturePreviewImageForSpec(
            Spec,
            CaptureRoot,
            RiverEyeCapturePath,
            TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
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
            TEXT("      \"water_mask_image\": \"%s\",\n")
            TEXT("      \"vegetation_mask_image\": \"%s\",\n")
            TEXT("      \"elevation_sample\": \"%s\",\n")
            TEXT("      \"fidelity_note\": \"%s\"\n")
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
            *EscapeRaftSimJsonString(Spec.WaterMaskImage),
            *EscapeRaftSimJsonString(Spec.VegetationMaskImage),
            *EscapeRaftSimJsonString(Spec.ElevationSample),
            *EscapeRaftSimJsonString(GetPreviewFidelityNote(Spec)));
    }

    const FString Manifest = FString::Printf(
        TEXT("{\n")
        TEXT("  \"schema\": \"raftsim.unreal.environment_capture_manifest.v1\",\n")
        TEXT("  \"capture_type\": \"guide_seat_and_river_eye_downstream_unreal_preview\",\n")
        TEXT("  \"source_plan\": \"%s\",\n")
        TEXT("  \"procedural_asset_plan\": \"%s\",\n")
        TEXT("  \"procedural_material_recipe_plan\": \"%s\",\n")
        TEXT("  \"geospatial_attachment_ledger\": \"%s\",\n")
        TEXT("  \"status\": \"%s\",\n")
        TEXT("  \"captures\": [\n")
        TEXT("%s\n")
        TEXT("  ]\n")
        TEXT("}\n"),
        *EscapeRaftSimJsonString(SourcePlanRelativePath),
        *EscapeRaftSimJsonString(ProceduralAssetPlanRelativePath),
        *EscapeRaftSimJsonString(ProceduralMaterialRecipePlanRelativePath),
        *EscapeRaftSimJsonString(GeospatialAttachmentLedgerRelativePath),
        bAllCaptured ? TEXT("south_fork_colorado_and_pacuare_source_draped_guide_and_river_eye_previews_available; photoreal source_data_and_asset_replacement_required") : TEXT("one_or_more_captures_failed"),
        *EntriesJson);

    const FString ManifestPath = FPaths::Combine(CaptureRoot, TEXT("environment_capture_manifest.json"));
    const bool bSaved = FFileHelper::SaveStringToFile(Manifest, *ManifestPath);
    OutSummary += FString::Printf(
        TEXT("%s environment preview capture manifest -> %s\n"),
        bSaved ? TEXT("Saved") : TEXT("Failed"),
        *ManifestPath);
    return bSaved && bAllCaptured;
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
