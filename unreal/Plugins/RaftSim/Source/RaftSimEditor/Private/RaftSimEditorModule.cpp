#include "RaftSimEditorModule.h"

#include "AssetRegistry/AssetRegistryModule.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
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
        TEXT("stitched South Fork production-import pilot source drape generated from four official USDA/APFO NAIP 2048px tiles, plus stitched USGS 3DEP pilot DEM relief and a review-gated 2017px heightfield candidate sampled into bank and valley preview geometry; pilot source water/vegetation masks are sampled into terrain color, source-aware bank breakup patches, first-party irregular shoreline edge breakup, first-party terrain material layer facets, first-party Landscape/Nanite material scaffold microfacets/strata/slope occlusion, first-party terrain erosion-rill/bank-gully strips, source-aware boulder wetness/abrasion/moss facets, biome-specific deadfall/log/grass/root ecology props, first-party biome foliage silhouette cards, dense layered riparian canopy/understory proxy clusters, first-party instanced procedural foliage-equivalent canopy/trunk/understory scaffold, first-party organic branch/frond lattice foliage, lit water variation, flow-band depth texture ribbons, flow-aware surface chop/turbidity patches, first-party water shader depth/reflection/refraction scaffold, source-aware shallow-water clarity/aeration layers, deterministic wet-rock, talus, foliage, understory, mask-aware ground-cover cards, refined guide-seat raft/oar foreground proxies, and river-specific atmospheric backdrop cards; all pilot derivatives remain review-gated until metadata review, mosaic/clip, hydrologic conditioning, channel burning, masks, and guide/geospatial approval pass; rocks, foliage, water, foam, raft, and lighting still include first-party procedural proxy layers");
    SouthFork.FlowBandId = TEXT("median_runnable");
    SouthFork.FlowBandDisplayName = TEXT("Median Runnable / Summer Commercial");
    SouthFork.FlowBandSource = TEXT("physics/data/real_world/south_fork_american_chili_bar/flow_presets.json");
    SouthFork.FlowVisualDescription =
        TEXT("Default South Fork summer-commercial validation band from USGS-11445500 planning presets; keeps moderate tongues, wet rocks, and foam lines visible while low/high seasonal variants remain future capture targets.");
    SouthFork.FlowReferenceDischargeCfs = 1600.0f;
    SouthFork.WaterColor = FLinearColor(0.038f, 0.285f, 0.300f);
    SouthFork.TerrainColor = FLinearColor(0.35f, 0.30f, 0.21f);
    SouthFork.RockColor = FLinearColor(0.38f, 0.36f, 0.31f);
    SouthFork.FoliageColor = FLinearColor(0.16f, 0.29f, 0.105f);
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
        TEXT("stitched Colorado/Lees Ferry production-import pilot source drape generated from four official USDA/APFO NAIP 2048px tiles, plus stitched USGS 3DEP pilot DEM relief and a review-gated 2017px heightfield candidate sampled into canyon bank preview geometry; pilot source water/vegetation masks are sampled into terrain color, source-aware bank breakup patches, first-party irregular shoreline edge breakup, first-party terrain material layer facets, first-party Landscape/Nanite material scaffold microfacets/strata/slope occlusion, first-party terrain erosion-rill/bank-gully strips, source-aware boulder wetness/abrasion/sediment facets, biome-specific sparse deadfall/grass/root ecology props, first-party sparse desert scrub silhouettes, sparse desert riparian thicket proxy clusters, first-party instanced procedural desert-thicket/trunk scaffold, lit water variation, flow-band depth texture ribbons, flow-aware surface chop/turbidity patches, first-party water shader depth/reflection/refraction scaffold, source-aware shallow-water clarity/aeration layers, deterministic wet-rock, talus, sparse scrub, boulder placement, mask-aware canyon ground-cover cards, refined guide-seat raft/oar foreground proxies, and river-specific atmospheric backdrop cards; all pilot derivatives remain review-gated until metadata review, mosaic/clip, river-mile stationing, hydrologic conditioning, release-aware masks, and guide/oarsman approval pass; rocks, foliage, water, foam, raft, and lighting still include first-party procedural proxy layers");
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
        TEXT("review-gated Pacuare production-import derivative placeholders generated from the selected NASA GIBS MODIS/Terra true-color seed and Copernicus DEM GLO-30 relief, normalized into a 4096px source drape, 2048px DEM relief, 2017px heightfield candidate, and 2048px water/vegetation masks; these remain coarse/cloudy proxy inputs until higher-resolution cloud-screened imagery, local hydrology/hydrography, protected-area review, and guide/outfitter validation are attached; first-party procedural rainforest leaf-litter, wet-rock, talus, mist, source-aware bank breakup patches, first-party irregular shoreline edge breakup, first-party terrain material layer facets, first-party Landscape/Nanite material scaffold microfacets/strata/slope occlusion, first-party terrain erosion-rill/bank-gully strips, source-aware boulder wetness/abrasion/moss facets, biome-specific deadfall/log/grass/root ecology props, rainforest canopy/vine silhouette cards, dense layered rainforest canopy/understory proxy clusters, first-party instanced procedural rainforest canopy/trunk/understory scaffold, first-party organic branch/frond lattice foliage, waterfall curtain/plunge-mist proxy layers, lit water variation, flow-band depth texture ribbons, flow-aware surface chop/turbidity patches, first-party water shader depth/reflection/refraction scaffold, source-aware shallow-water clarity/aeration layers, dense mask-aware ground-cover/canopy cards, refined guide-seat raft/oar foreground proxies, and humid atmospheric backdrop cards remain rights-safe proxy dressing; rocks, foliage, water, foam, raft, and lighting still include first-party procedural proxy layers");
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
    Pacuare.WaterColor = FLinearColor(0.026f, 0.255f, 0.205f);
    Pacuare.TerrainColor = FLinearColor(0.17f, 0.22f, 0.13f);
    Pacuare.RockColor = FLinearColor(0.20f, 0.24f, 0.20f);
    Pacuare.FoliageColor = FLinearColor(0.035f, 0.20f, 0.055f);
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
        EmissiveScale->R = 0.26f;
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
                Constant->R = 0.26f;
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

float GetPreviewColorLuma(const FLinearColor& Color)
{
    return FMath::Max(0.001f, Color.R * 0.2126f + Color.G * 0.7152f + Color.B * 0.0722f);
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
    return Spec.bDesertCanyon ? 0.62f : (Spec.bHasWaterfalls ? 0.74f : 0.70f);
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
    const float HeightfieldMask = SmoothPreviewStep(
        ActiveRiverHalfWidth + 180.0f,
        ActiveRiverHalfWidth + Spec.BankWidthCm + (Spec.bDesertCanyon ? 1450.0f : 820.0f),
        ChannelOffset);
    const float RidgePattern = (HeightfieldPreview->SampleLuma(U, V) - 0.5f) * Spec.HeightfieldPreviewAmplitudeCm;
    return RidgePattern * HeightfieldMask;
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
    MeshComponent->SetCastShadow(false);
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
    const FVector Radii(
        FMath::Max(8.0f, Scale.X * 100.0f),
        FMath::Max(8.0f, Scale.Y * 100.0f),
        FMath::Max(6.0f, Scale.Z * 100.0f));

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
            VertexColors.Add(ScalePreviewColor(Color, HeightTint * LeafTint));
        }
    }

    const int32 TopIndex = Vertices.Num();
    Vertices.Add(FVector(BaseLocation.X, BaseLocation.Y, BaseLocation.Z + Radii.Z * 0.86f));
    UVs.Add(FVector2D(0.5f, 1.0f));
    VertexColors.Add(ScalePreviewColor(Color, bRainforest ? 1.08f : 1.02f));

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

    const int32 LeafCount = bRainforest ? 26 : 18;
    const float YawRadians = FMath::DegreesToRadians(YawDegrees);
    const FVector BaseForward(FMath::Cos(YawRadians), FMath::Sin(YawRadians), 0.0f);
    const FVector BaseRight(-FMath::Sin(YawRadians), FMath::Cos(YawRadians), 0.0f);
    const FVector Up(0.0f, 0.0f, 1.0f);
    const FVector Radii(
        FMath::Max(16.0f, Scale.X * 100.0f),
        FMath::Max(12.0f, Scale.Y * 100.0f),
        FMath::Max(10.0f, Scale.Z * 100.0f));

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
        const float LeafLength = Radii.X * (bRainforest ? 0.20f : 0.15f) *
            (0.62f + 0.26f * FMath::Abs(FMath::Sin(static_cast<float>(LeafIndex) * 0.83f + static_cast<float>(Seed) * 0.029f)));
        const float LeafWidth = Radii.Y * (bRainforest ? 0.050f : 0.040f) *
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
        const FLinearColor OuterLeafColor = ScalePreviewColor(Color, LeafShade * (bRainforest ? 1.08f : 1.02f));
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
    const FRaftSimPreviewImage* VegetationMask)
{
    constexpr int32 XSteps = 220;
    constexpr int32 YSteps = 84;
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
                FLinearColor SourceDrapeColor = NormalizePreviewSourceDrapeAlbedo(
                    Spec,
                    AerialDrape->Sample(U, V),
                    SourceWaterT,
                    SourceVegetationT,
                    Spec.bHasWaterfalls ? 0.42f : (Spec.bDesertCanyon ? 0.36f : 0.34f));
                const float SourceBlend = FMath::Clamp(
                    (Spec.bDesertCanyon ? 0.10f : (Spec.bHasWaterfalls ? 0.075f : 0.09f)) *
                        (0.24f + BankT * 0.22f + CanyonT * 0.16f + SourceVegetationT * 0.08f + SourceWaterT * 0.03f),
                    0.0f,
                    Spec.bDesertCanyon ? 0.10f : 0.09f);
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

    constexpr int32 XTiles = 48;
    constexpr int32 YTiles = 18;
    constexpr int32 MicrotileSubdivisions = 4;
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

            const float DrapeWeight = Spec.bDesertCanyon ? 0.024f : (Spec.bHasWaterfalls ? 0.018f : 0.022f);
            const float HalfLength = TileLength * 0.48f;
            const float HalfTileWidth = TileWidth * 0.48f;
            const float TileZOffset = 9.0f;
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
                        FMath::Clamp(DrapeWeight * EdgeFeather * PatchMottle, 0.0f, 0.028f));
                    AerialColor.R = FMath::Max(AerialColor.R, Spec.TerrainColor.R * 0.78f + 0.035f);
                    AerialColor.G = FMath::Max(AerialColor.G, Spec.TerrainColor.G * 0.78f + 0.035f);
                    AerialColor.B = FMath::Max(AerialColor.B, Spec.TerrainColor.B * 0.78f + 0.035f);
                    AerialColor.A = 1.0f;
                    AerialColor = NormalizePreviewTerrainProxyPatchColor(Spec, AerialColor);

                    Vertices.Add(FVector(
                        SampleX,
                        SampleY,
                        GetPreviewTerrainHeightCm(Spec, SampleX, SampleY, TerrainRelief, HeightfieldPreview) +
                            TileZOffset + EdgeFeather * 2.5f));
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

void AddPreviewRiverRibbonMesh(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec)
{
    constexpr int32 XSteps = 320;
    constexpr int32 CrossSteps = 34;
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

    const FLinearColor DeepWaterBase = ScalePreviewColor(Spec.WaterColor, Spec.bDesertCanyon ? 0.98f : 1.02f);
    const FLinearColor DeepWater = Spec.bDesertCanyon
        ? FMath::Lerp(DeepWaterBase, FLinearColor(0.20f, 0.18f, 0.13f), 0.35f)
        : (Spec.bHasWaterfalls ? FMath::Lerp(DeepWaterBase, FLinearColor(0.010f, 0.19f, 0.145f), 0.34f)
                                : FMath::Lerp(DeepWaterBase, FLinearColor(0.012f, 0.25f, 0.28f), 0.32f));
    const FLinearColor ShallowWater = Spec.bDesertCanyon
        ? FLinearColor(0.34f, 0.30f, 0.22f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.030f, 0.34f, 0.27f) : FLinearColor(0.048f, 0.42f, 0.43f));
    const FLinearColor SurfaceGlint = Spec.bDesertCanyon
        ? FLinearColor(0.58f, 0.49f, 0.34f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.13f, 0.58f, 0.48f) : FLinearColor(0.14f, 0.62f, 0.64f));
    const FLinearColor NearFieldBrightRipple = Spec.bDesertCanyon
        ? FLinearColor(0.42f, 0.37f, 0.27f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.070f, 0.37f, 0.30f) : FLinearColor(0.075f, 0.42f, 0.43f));
    const FLinearColor NearFieldDarkSlick = Spec.bDesertCanyon
        ? FLinearColor(0.16f, 0.14f, 0.105f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.010f, 0.105f, 0.085f) : FLinearColor(0.012f, 0.135f, 0.155f));
    const FLinearColor BaseWaterDeepCurrentTongue = Spec.bDesertCanyon
        ? FLinearColor(0.17f, 0.15f, 0.11f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.006f, 0.095f, 0.075f) : FLinearColor(0.008f, 0.12f, 0.145f));
    const FLinearColor BaseWaterSedimentThread = Spec.bDesertCanyon
        ? FLinearColor(0.36f, 0.30f, 0.20f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.045f, 0.21f, 0.14f) : FLinearColor(0.065f, 0.29f, 0.25f));
    const FLinearColor BaseWaterSkyThread = Spec.bDesertCanyon
        ? FLinearColor(0.46f, 0.42f, 0.32f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.085f, 0.34f, 0.29f) : FLinearColor(0.095f, 0.40f, 0.42f));
    const float ActiveRiverHalfWidth = GetPreviewActiveRiverHalfWidthCm(Spec);
    const float WaterBaseZ = GetPreviewWaterSurfaceBaseZCm(Spec);
    const float FlowEnergy = FMath::Clamp(Spec.FlowCurrentCueScale, 0.65f, 1.60f);
    const float BaseWaveAmplitudeCm =
        (Spec.bDesertCanyon ? 5.0f : (Spec.bHasWaterfalls ? 9.0f : 7.0f)) * FlowEnergy;
    const float StandingWaveAmplitudeCm =
        (Spec.bDesertCanyon ? 3.5f : (Spec.bHasWaterfalls ? 5.8f : 4.6f)) *
        FMath::Clamp(Spec.FlowFoamScale, 0.70f, 1.55f);
    const float NearFieldFineRippleAmplitudeCm =
        (Spec.bDesertCanyon ? 1.6f : (Spec.bHasWaterfalls ? 3.1f : 2.6f)) * FlowEnergy;

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
            const float BaseWaterDepthCurrentGradingT = FMath::Clamp(
                CenterT *
                    (0.52f + 0.28f * FMath::Sin(X * 0.0037f + Lateral * 0.0019f + FlowEnergy) +
                     0.20f * FMath::Sin(X * 0.011f - Lateral * 0.0047f)),
                0.0f,
                1.0f);
            const float BaseWaterCurrentTongueT = FMath::Clamp(
                FMath::Pow(BaseWaterDepthCurrentGradingT, 1.35f) * FlowEnergy * 0.18f,
                0.0f,
                Spec.bDesertCanyon ? 0.15f : 0.18f);
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
            FLinearColor WaterColor = FMath::Lerp(DeepWater, ShallowWater, FMath::Clamp(EdgeT * 0.55f, 0.0f, 1.0f));
            WaterColor = FMath::Lerp(WaterColor, BaseWaterDeepCurrentTongue, BaseWaterCurrentTongueT);
            WaterColor = FMath::Lerp(WaterColor, BaseWaterSedimentThread, BaseWaterSedimentThreadT);
            WaterColor = FMath::Lerp(WaterColor, BaseWaterSkyThread, BaseWaterSkyThreadT);
            WaterColor = FMath::Lerp(
                WaterColor,
                SurfaceGlint,
                FMath::Clamp((1.0f - EdgeT * 0.45f) * FlowNoise * FlowEnergy * (Spec.bDesertCanyon ? 0.12f : 0.16f), 0.0f, 0.22f));
            const float NearFieldTextureGain = FMath::Clamp(0.36f + NearFieldWaterSurfaceGrainT * 0.64f, 0.0f, 1.0f);
            WaterColor = FMath::Lerp(
                WaterColor,
                NearFieldDarkSlick,
                FMath::Clamp(FineSlick * CenterT * NearFieldTextureGain * 0.070f, 0.0f, 0.085f));
            WaterColor = FMath::Lerp(
                WaterColor,
                NearFieldBrightRipple,
                FMath::Clamp(FineRipple * (0.58f + CenterT * 0.42f) * NearFieldTextureGain * 0.055f, 0.0f, 0.065f));
            const float FineRippleWave =
                (FineRipple - 0.5f) * NearFieldFineRippleAmplitudeCm * (0.45f + CenterT * 0.55f) * NearFieldTextureGain;
            Vertices.Add(FVector(X, CenterY + Lateral, WaterBaseZ + Wave + FineRippleWave));
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

    constexpr int32 Segments = 72;
    constexpr int32 CrossSteps = 3;
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
            const float SegmentFade = SmoothPreviewStep(0.22f, 0.78f, Breakup);
            const float LocalWidthScale = 0.26f + 0.48f * SegmentFade;
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
            VertexColors.Add(ClampPreviewColor(FMath::Lerp(TerrainBase, RibbonColor, SegmentFade * 0.32f)));
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
        ? FLinearColor(0.20f, 0.16f, 0.12f)
        : FMath::Lerp(ScalePreviewColor(Spec.WaterColor, 0.36f), ScalePreviewColor(Spec.RockColor, 0.48f), 0.48f);
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
            (Spec.bDesertCanyon ? 72.0f : 54.0f) * WetBankScale,
            12.0f,
            WetEdge,
            BankBand);
        AddPreviewShoreRibbon(
            World,
            Spec,
            TerrainRelief,
            HeightfieldPreview,
            FString::Printf(TEXT("RaftSim_GravelMudBank_%s_%s"), Side < 0.0f ? TEXT("Left") : TEXT("Right"), *Spec.RiverId),
            Side * (ActiveRiverHalfWidth + 205.0f * WetBankScale),
            (Spec.bDesertCanyon ? 92.0f : 62.0f) * WetBankScale,
            15.0f,
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
    const int32 LayerCount = Spec.bDesertCanyon ? 42 : (Spec.bHasWaterfalls ? 48 : 38);
    const int32 BandCount = Spec.bDesertCanyon ? 6 : (Spec.bHasWaterfalls ? 5 : 4);
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

        const float Length = (Spec.bDesertCanyon ? 400.0f : (Spec.bHasWaterfalls ? 285.0f : 260.0f)) *
            (0.56f + 0.06f * static_cast<float>(LayerIndex % 5));
        const float Width = (Spec.bDesertCanyon ? 84.0f : (Spec.bHasWaterfalls ? 58.0f : 54.0f)) *
            (0.56f + 0.05f * static_cast<float>(LayerIndex % 4));
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
            Spec.bDesertCanyon ? 28.0f : 22.0f);
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
    const int32 FacetCount = Spec.bDesertCanyon ? 54 : (bRainforest ? 50 : 44);
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

        const float Length = (Spec.bDesertCanyon ? 255.0f : (bRainforest ? 190.0f : 205.0f)) *
            (0.52f + 0.06f * static_cast<float>(FacetIndex % 7));
        const float Width = (Spec.bDesertCanyon ? 46.0f : (bRainforest ? 36.0f : 38.0f)) *
            (0.52f + 0.05f * static_cast<float>(FacetIndex % 5));
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
            Spec.bDesertCanyon ? 36.0f : 28.0f);
    }

    const int32 BandPerSide = Spec.bDesertCanyon ? 10 : (bRainforest ? 8 : 7);
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
        AddPreviewBankBreakupPatch(
            World,
            Spec,
            TerrainRelief,
            HeightfieldPreview,
            FString::Printf(TEXT("RaftSim_LandscapeNaniteStrataMicroBand_%03d_%s"), BandIndex, *Spec.RiverId),
            X - (Spec.bDesertCanyon ? 630.0f : 420.0f),
            Spec.bDesertCanyon ? 390.0f : 270.0f,
            SignedOffset,
            Spec.bDesertCanyon ? 18.0f : 14.0f,
            Phase,
            InnerColor,
            OuterColor,
            Spec.bDesertCanyon ? 34.0f : 24.0f);
    }

    const int32 OcclusionCount = Spec.bDesertCanyon ? 18 : (bRainforest ? 16 : 14);
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
        AddPreviewBankBreakupPatch(
            World,
            Spec,
            TerrainRelief,
            HeightfieldPreview,
            FString::Printf(TEXT("RaftSim_LandscapeNaniteSlopeOcclusionPatch_%03d_%s"), OcclusionIndex, *Spec.RiverId),
            X - (Spec.bDesertCanyon ? 250.0f : 185.0f),
            Spec.bDesertCanyon ? 310.0f : 220.0f,
            SignedOffset,
            Spec.bDesertCanyon ? 28.0f : 22.0f,
            Phase,
            ShadowColor,
            RimColor,
            Spec.bDesertCanyon ? 34.0f : 24.0f);
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
                AddPreviewTranslucentMeshActor(
                    World,
                    PlaneMesh,
                    FString::Printf(TEXT("RaftSim_MaskAwareGroundCover_%03d_%s"), CardIndex + SideIndex * CardsPerSide, *Spec.RiverId),
                    FVector(X, Y, TerrainZ + (Spec.bDesertCanyon ? 18.0f : 15.0f)),
                    FRotator(0.0f, Yaw, 0.0f),
                    FVector(
                        Spec.bDesertCanyon ? 0.74f : (Spec.bHasWaterfalls ? 0.66f : 0.54f),
                        Spec.bDesertCanyon ? 0.28f : (Spec.bHasWaterfalls ? 0.32f : 0.26f),
                        1.0f),
                    GroundColor,
                    Spec.bDesertCanyon ? 0.34f : (Spec.bHasWaterfalls ? 0.38f : 0.36f));
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

    const bool bNearFrameWaterRibbon = StartX + Length * 0.50f < 4200.0f;
    const float NearFrameRibbonWidthScale = bNearFrameWaterRibbon ? 0.36f : 1.0f;
    const FLinearColor RibbonColor = bNearFrameWaterRibbon
        ? ClampPreviewColor(FMath::Lerp(Spec.WaterColor, Color, Spec.bDesertCanyon ? 0.20f : 0.26f))
        : Color;

    for (int32 SegmentIndex = 0; SegmentIndex <= Segments; ++SegmentIndex)
    {
        const float T = static_cast<float>(SegmentIndex) / static_cast<float>(Segments);
        const float X = StartX + Length * T;
        const float RiverCenterY = GetPreviewRiverCenterY(Spec, X);
        const float Sway = FMath::Sin(Phase + T * UE_TWO_PI) * Width * 0.32f * NearFrameRibbonWidthScale;
        const float Taper = FMath::Sin(T * PI);
        const float LocalHalfWidth = FMath::Max(3.0f, Width * NearFrameRibbonWidthScale * (0.18f + 0.62f * Taper));
        const float CenterY = RiverCenterY + LateralOffset + Sway;
        const float SurfaceWave = FMath::Sin(X * 0.011f + CenterY * 0.015f) * (Spec.bDesertCanyon ? 2.0f : 4.5f);
        const float Z = GetPreviewWaterSurfaceBaseZCm(Spec) + (bNearFrameWaterRibbon ? 8.0f : 15.0f) +
            SurfaceWave + 2.0f * FMath::Sin(Phase * 1.7f + T * PI);

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
    AddPreviewProceduralMeshActor(World, Label, Vertices, Triangles, Normals, UVs, RibbonColor);
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
        const float NearFrameWaterRibbonDemotion = SmoothPreviewStep(1800.0f, 5200.0f, X);
        const float NearFrameWidthScale = FMath::Lerp(0.42f, 1.0f, NearFrameWaterRibbonDemotion);
        const float LocalHalfWidth = FMath::Max(3.0f, Width * NearFrameWidthScale * (0.12f + 0.38f * Taper));
        const float CenterY = RiverCenterY + LateralOffset + Sway;
        const float SurfaceWave = FMath::Sin(X * 0.011f + CenterY * 0.015f) * (Spec.bDesertCanyon ? 2.0f : 4.5f);
        const float Z = WaterBaseZ + FMath::Lerp(8.0f, 20.0f, NearFrameWaterRibbonDemotion) +
            SurfaceWave + 1.6f * FMath::Sin(Phase * 1.3f + T * PI);
        const float Pulse =
            FMath::Clamp(0.44f + 0.34f * FMath::Sin(Phase + T * UE_TWO_PI * 3.0f) + 0.16f * Taper, 0.0f, 1.0f);
        const FLinearColor RawFlowColor = ClampPreviewColor(FMath::Lerp(ShadowColor, HighlightColor, Pulse));
        const FLinearColor FlowColor = ClampPreviewColor(FMath::Lerp(
            Spec.WaterColor,
            RawFlowColor,
            FMath::Lerp(0.18f, 1.0f, NearFrameWaterRibbonDemotion)));

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

void AddPreviewWaterShaderDepthReflectionScaffoldDetail(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec)
{
    if (!World)
    {
        return;
    }

    constexpr int32 XSteps = 136;
    constexpr int32 CrossSteps = 12;
    const float NearCameraWaterScaffoldClearanceMinX = 3600.0f;
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
            (Spec.bDesertCanyon ? 0.62f : 0.56f) *
            (0.95f + 0.05f * FMath::Sin(X * 0.0012f));
        const float LongitudinalFeather = SmoothPreviewStep(0.0f, 0.13f, U);
        for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
        {
            const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
            const float Lateral = FMath::Lerp(-Width, Width, V);
            const float EdgeT = FMath::Pow(FMath::Abs(V - 0.5f) * 2.0f, 1.22f);
            const float DeepT = 1.0f - FMath::Clamp(EdgeT, 0.0f, 1.0f);
            const float CenterFeather = SmoothPreviewStep(0.0f, 0.72f, DeepT);
            const float FlowLine =
                FMath::Clamp(
                    0.48f + 0.28f * FMath::Sin(X * 0.0039f - Lateral * 0.0068f) +
                        0.18f * FMath::Sin(X * 0.011f + Lateral * 0.0032f),
                    0.0f,
                    1.0f);
            const float FresnelEdge = FMath::Pow(FMath::Clamp(EdgeT, 0.0f, 1.0f), 2.15f);
            const float ReflectionT = FMath::Clamp(
                ((0.055f + 0.085f * FlowLine) * FlowEnergy + FresnelEdge * 0.060f) * LongitudinalFeather,
                0.0f,
                0.18f);
            FLinearColor WaterColor = FMath::Lerp(ShallowTint, DeepCore, DeepT);
            WaterColor = FMath::Lerp(WaterColor, BankReflection, FMath::Clamp(FresnelEdge * 0.075f, 0.0f, 0.12f));
            WaterColor = FMath::Lerp(WaterColor, SkyReflection, ReflectionT);
            WaterColor = FMath::Lerp(
                WaterColor,
                Spec.WaterColor,
                FMath::Clamp(0.44f + 0.16f * (1.0f - CenterFeather) + 0.10f * FMath::Sin(X * 0.0023f + Lateral * 0.0051f), 0.32f, 0.68f));

            const float SurfaceWave =
                (FMath::Sin(X * 0.011f + Lateral * 0.015f) * (Spec.bDesertCanyon ? 1.2f : 2.4f) +
                 FMath::Sin(X * 0.018f - Lateral * 0.006f) * (Spec.bDesertCanyon ? 0.5f : 0.9f)) *
                LongitudinalFeather;
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

    const int32 ReflectionRibbonCount = Spec.bDesertCanyon ? 16 : (Spec.bHasWaterfalls ? 28 : 22);
    for (int32 ReflectionIndex = 0; ReflectionIndex < ReflectionRibbonCount; ++ReflectionIndex)
    {
        const float T = FMath::Frac(0.081f + 0.618034f * static_cast<float>(ReflectionIndex));
        const float X = FMath::Lerp(NearCameraWaterScaffoldClearanceMinX, 25300.0f, T);
        const float Side = (ReflectionIndex % 2 == 0) ? -1.0f : 1.0f;
        const float Lateral = Side * ActiveRiverHalfWidth * (0.58f + 0.22f * FMath::Sin(static_cast<float>(ReflectionIndex) * 0.73f));
        const float Length =
            (Spec.bDesertCanyon ? 920.0f : 720.0f) *
            (0.72f + 0.12f * static_cast<float>(ReflectionIndex % 5)) * FMath::Clamp(FlowEnergy, 0.68f, 1.22f);
        const float Width =
            (Spec.bDesertCanyon ? 20.0f : 17.0f) *
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

    const int32 RefractionSeamCount = Spec.bDesertCanyon ? 14 : (Spec.bHasWaterfalls ? 26 : 20);
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
            X - 260.0f,
            Spec.bDesertCanyon ? 620.0f : 500.0f,
            Lateral,
            Spec.bDesertCanyon ? 10.0f : 8.0f,
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
            const float X = FMath::Lerp(-5200.0f, 25800.0f, U);
            const float RiverCenterY = GetPreviewRiverCenterY(Spec, X);
            const float Width = ActiveRiverHalfWidth *
                (0.98f + 0.055f * FMath::Sin(X * 0.0012f) + (Spec.bDesertCanyon ? 0.14f : 0.04f));
            const float LongitudinalFeather = FMath::Clamp(
                SmoothPreviewStep(0.0f, 0.055f, U) * (1.0f - SmoothPreviewStep(0.965f, 1.0f, U)),
                0.0f,
                1.0f);

            for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
            {
                const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
                const float EdgeT = FMath::Pow(FMath::Clamp(V, 0.0f, 1.0f), 1.12f);
                const float Lateral = Side * FMath::Lerp(Width * 0.94f, Width * 0.985f, EdgeT);
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
                WaterColor = FMath::Lerp(Spec.WaterColor, WaterColor, 0.18f * LongitudinalFeather);

                const float SurfaceWave =
                    (FMath::Sin(X * 0.012f + EdgeT * 2.7f) * (Spec.bDesertCanyon ? 1.4f : 2.6f) +
                     FMath::Sin(X * 0.023f - EdgeT * 4.1f) * (Spec.bDesertCanyon ? 0.7f : 1.2f)) *
                    LongitudinalFeather;
                Vertices.Add(FVector(X, Y, WaterBaseZ + 5.2f + SurfaceWave));
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

        Normals = ComputePreviewMeshNormals(Vertices, Triangles);
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
        const float Opacity =
            (Spec.bDesertCanyon ? 0.070f : (Spec.bHasWaterfalls ? 0.145f : 0.110f)) *
            FMath::Clamp(0.74f + SourceWaterT * 0.42f + FlowEnergy * 0.18f, 0.55f, 1.25f);
        const float LengthScale =
            (Spec.bDesertCanyon ? 0.14f : 0.11f) *
            (0.70f + 0.10f * static_cast<float>(BubbleIndex % 5));
        const float WidthScale =
            (Spec.bDesertCanyon ? 0.026f : 0.022f) *
            (0.74f + 0.10f * static_cast<float>(BubbleIndex % 4));

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
    const FLinearColor DarkRipple = Spec.bDesertCanyon
        ? FLinearColor(0.26f, 0.24f, 0.17f, 1.0f)
        : (Spec.bHasWaterfalls ? FLinearColor(0.020f, 0.22f, 0.17f, 1.0f) : FLinearColor(0.025f, 0.27f, 0.30f, 1.0f));
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
    const int32 SilhouetteCount = Spec.bDesertCanyon ? 34 : (Spec.bHasWaterfalls ? 140 : 86);
    const float NearBankOffset = Spec.bDesertCanyon ? 760.0f : (Spec.bHasWaterfalls ? 520.0f : 560.0f);
    const float FarBankOffset = Spec.bDesertCanyon ? 2120.0f : (Spec.bHasWaterfalls ? 1550.0f : 1240.0f);

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

        if (Spec.bHasWaterfalls && FoliageIndex % 5 == 0)
        {
            const FLinearColor VineColor = ScalePreviewColor(
                FMath::Lerp(FLinearColor(0.018f, 0.10f, 0.035f), Spec.FoliageColor, 0.64f + VegetationT * 0.22f),
                0.86f + 0.10f * static_cast<float>(FoliageIndex % 4));
            AddPreviewMeshActor(
                World,
                PlaneMesh,
                FString::Printf(TEXT("RaftSim_RainforestVineCurtain_%03d_%s"), FoliageIndex, *Spec.RiverId),
                FVector(X, Y, TerrainZ + 215.0f + 20.0f * static_cast<float>(FoliageIndex % 3)),
                FRotator(78.0f + 4.0f * FMath::Sin(Phase), Yaw, 0.0f),
                FVector(0.62f + 0.12f * FMath::Abs(FMath::Sin(Phase)), 1.90f + 0.24f * static_cast<float>(FoliageIndex % 3), 1.0f),
                VineColor);
        }
        else if (Spec.bDesertCanyon)
        {
            const FLinearColor ScrubColor = ScalePreviewColor(
                FMath::Lerp(FLinearColor(0.22f, 0.23f, 0.12f), Spec.FoliageColor, 0.42f),
                0.78f + 0.07f * static_cast<float>(FoliageIndex % 5));
            AddPreviewMeshActor(
                World,
                PlaneMesh,
                FString::Printf(TEXT("RaftSim_DesertScrubSilhouette_%03d_%s"), FoliageIndex, *Spec.RiverId),
                FVector(X, Y, TerrainZ + 54.0f),
                FRotator(58.0f, Yaw, 0.0f),
                FVector(0.38f + 0.05f * static_cast<float>(FoliageIndex % 4), 0.46f, 1.0f),
                ScrubColor);
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
    const int32 ClusterCount = Spec.bDesertCanyon ? 56 : (bRainforest ? 180 : 118);
    const float NearBankOffset = Spec.bDesertCanyon ? 1080.0f : (bRainforest ? 620.0f : 660.0f);
    const float FarBankOffset = Spec.bDesertCanyon ? 2200.0f : (bRainforest ? 1720.0f : 1360.0f);

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
            AddPreviewMeshActor(
                World,
                PlaneMesh,
                FString::Printf(TEXT("RaftSim_DenseBiomeFoliageDesertThicket_%03d_%s"), ClusterIndex, *Spec.RiverId),
                FVector(X, Y, TerrainZ + 48.0f + 6.0f * static_cast<float>(ClusterIndex % 3)),
                FRotator(52.0f + 4.0f * FMath::Sin(Phase), Yaw, 0.0f),
                FVector(0.54f + 0.08f * static_cast<float>(ClusterIndex % 4), 0.42f, 1.0f),
                ScrubColor);
            if (ClusterIndex % 3 == 0)
            {
                AddPreviewMeshActor(
                    World,
                    PlaneMesh,
                    FString::Printf(TEXT("RaftSim_DenseBiomeFoliageDesertThicket_%03dB_%s"), ClusterIndex, *Spec.RiverId),
                    FVector(X + 80.0f * FMath::Sin(Phase), Y + SideNudge, TerrainZ + 38.0f),
                    FRotator(43.0f, Yaw + 64.0f, 0.0f),
                    FVector(0.40f, 0.34f + 0.05f * static_cast<float>(ClusterIndex % 4), 1.0f),
                    ScalePreviewColor(ScrubColor, 0.86f));
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
                bRainforest ? 1.28f + 0.14f * static_cast<float>(ClusterIndex % 5) : 0.84f + 0.10f * static_cast<float>(ClusterIndex % 4),
                bRainforest ? 1.74f : 1.12f,
                bRainforest ? 1.44f : 0.96f),
            CanopyColor,
            ClusterIndex * 59 + 10100,
            bRainforest,
            false);

        const FLinearColor UnderstoryColor = ScalePreviewColor(
            FMath::Lerp(bRainforest ? FLinearColor(0.012f, 0.070f, 0.022f) : FLinearColor(0.085f, 0.17f, 0.050f), Spec.FoliageColor, 0.45f + VegetationT * 0.24f),
            0.74f + 0.07f * static_cast<float>(ClusterIndex % 4));
        AddPreviewOrganicBranchFrondActor(
            World,
            FString::Printf(TEXT("RaftSim_DenseBiomeOrganicBranchFrondUnderstory_%03d_%s"), ClusterIndex, *Spec.RiverId),
            FVector(X + 62.0f * FMath::Sin(Phase * 0.91f), Y + SideNudge, TerrainZ + (bRainforest ? 132.0f : 74.0f)),
            Yaw + 73.0f,
            FVector(
                bRainforest ? 0.82f + 0.10f * static_cast<float>(ClusterIndex % 4) : 0.52f + 0.08f * static_cast<float>(ClusterIndex % 4),
                bRainforest ? 1.08f : 0.66f,
                bRainforest ? 0.84f : 0.48f),
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

        if (bRainforest && ClusterIndex % 5 == 0)
        {
            const FLinearColor FrondColor = ScalePreviewColor(
                FMath::Lerp(FLinearColor(0.018f, 0.12f, 0.035f), Spec.FoliageColor, 0.72f),
                0.90f + 0.08f * static_cast<float>(ClusterIndex % 3));
            AddPreviewOrganicBranchFrondActor(
                World,
                FString::Printf(TEXT("RaftSim_DenseBiomeOrganicPalmFrondLattice_%03d_%s"), ClusterIndex, *Spec.RiverId),
                FVector(X + 88.0f * FMath::Cos(Phase), Y - SideNudge, TerrainZ + 235.0f + 20.0f * FMath::Sin(Phase)),
                Yaw + 116.0f,
                FVector(0.58f, 1.78f + 0.16f * static_cast<float>(ClusterIndex % 4), 1.12f),
                FrondColor,
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
    const int32 ClusterCount = Spec.bDesertCanyon ? 44 : (bRainforest ? 128 : 88);
    const float NearBankOffset = Spec.bDesertCanyon ? 980.0f : (bRainforest ? 720.0f : 760.0f);
    const float FarBankOffset = Spec.bDesertCanyon ? 2350.0f : (bRainforest ? 1820.0f : 1480.0f);

    UInstancedStaticMeshComponent* CanopyInstances = AddPreviewInstancedMeshComponent(
        World,
        SphereMesh,
        FString::Printf(TEXT("RaftSim_InstancedProceduralFoliageCanopyLibrary_%s"), *Spec.RiverId),
        Spec.bDesertCanyon ? FLinearColor(0.24f, 0.29f, 0.13f) : ScalePreviewColor(Spec.FoliageColor, bRainforest ? 0.92f : 0.86f));
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
            UnderstoryInstances->AddInstance(
                FTransform(
                    FRotator(0.0f, Yaw, 0.0f),
                    FVector(X, Y, TerrainZ + 36.0f),
                    ScrubScale),
                true);
            if (ClusterIndex % 3 == 0)
            {
                UnderstoryInstances->AddInstance(
                    FTransform(
                        FRotator(0.0f, Yaw + 58.0f, 0.0f),
                        FVector(X + 115.0f * FMath::Sin(Phase), Y + 68.0f * Side, TerrainZ + 30.0f),
                        FVector(ScrubScale.X * 0.78f, ScrubScale.Y * 0.90f, ScrubScale.Z * 0.86f)),
                    true);
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

        const int32 LobeCount = bRainforest ? 5 : 4;
        const float CrownBaseZ = TerrainZ + (bRainforest ? 315.0f : 185.0f) + 22.0f * FMath::Sin(Phase);
        for (int32 LobeIndex = 0; LobeIndex < LobeCount; ++LobeIndex)
        {
            const float LobeAngle = FMath::DegreesToRadians(Yaw + static_cast<float>(LobeIndex) * (360.0f / static_cast<float>(LobeCount)));
            const float Radius = (LobeIndex == 0) ? 0.0f : (bRainforest ? 92.0f : 64.0f);
            const float LobeX = X + FMath::Cos(LobeAngle) * Radius;
            const float LobeY = Y + FMath::Sin(LobeAngle) * Radius;
            const float SizeNoise = 0.86f + 0.08f * static_cast<float>((ClusterIndex + LobeIndex) % 5) + VegetationT * 0.08f;
            CanopyInstances->AddInstance(
                FTransform(
                    FRotator(0.0f, Yaw + static_cast<float>(LobeIndex) * 21.0f, 0.0f),
                    FVector(LobeX, LobeY, CrownBaseZ + 18.0f * static_cast<float>(LobeIndex % 3)),
                    FVector(
                        (bRainforest ? 0.44f : 0.30f) * SizeNoise,
                        (bRainforest ? 0.34f : 0.24f) * SizeNoise,
                        (bRainforest ? 0.22f : 0.17f) * SizeNoise)),
                true);
        }

        TrunkInstances->AddInstance(
            FTransform(
                FRotator(6.0f * FMath::Sin(Phase), Yaw + 16.0f, 0.0f),
                FVector(X, Y, TerrainZ + (bRainforest ? 145.0f : 88.0f)),
                FVector(0.030f, 0.030f, bRainforest ? 2.22f : 1.32f)),
            true);

        const int32 UnderstoryCount = bRainforest ? 3 : 2;
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
                        bRainforest ? 0.12f : 0.09f)),
                true);
        }
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

    const float BaseX = -4100.0f;
    const float CenterY = GetPreviewRiverCenterY(Spec, BaseX);
    const float Z = -18.0f;
    const FLinearColor TubeColor = FMath::Lerp(ScalePreviewColor(Spec.RaftColor, 0.42f), FLinearColor(0.34f, 0.095f, 0.035f), 0.60f);
    const FLinearColor TubeShadowColor = ScalePreviewColor(TubeColor, 0.44f);
    const FLinearColor TubeHighlightColor = FMath::Lerp(TubeColor, FLinearColor(0.70f, 0.25f, 0.09f), 0.14f);
    const FLinearColor FrameColor = Spec.bDesertCanyon ? FLinearColor(0.12f, 0.095f, 0.065f) : FLinearColor(0.065f, 0.075f, 0.058f);
    const FLinearColor OarShaftColor = Spec.bDesertCanyon ? FLinearColor(0.24f, 0.15f, 0.075f) : FLinearColor(0.27f, 0.16f, 0.075f);
    const FLinearColor OarBladeColor = Spec.bDesertCanyon ? FLinearColor(0.22f, 0.15f, 0.075f) : FLinearColor(0.24f, 0.10f, 0.045f);
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
        ScalePreviewColor(FrameColor, 0.22f));
    AddRaftProxyPart(
        CylinderMesh,
        FString::Printf(TEXT("RaftSim_ForegroundRaft_FrameBarRounded_%s"), *Spec.RiverId),
        FVector(BaseX - 62.0f, CenterY, -4.0f),
        FRotator(0.0f, 0.0f, 90.0f),
        FVector(0.018f, 0.018f, 0.46f),
        FLinearColor(0.045f, 0.045f, 0.038f));

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
    const float OarBladeOffset = Spec.bDesertCanyon ? 330.0f : 295.0f;
    for (int32 OarIndex = 0; OarIndex < 2; ++OarIndex)
    {
        const float Side = (OarIndex == 0) ? -1.0f : 1.0f;
        AddRaftProxyPart(
            CylinderMesh,
            FString::Printf(TEXT("RaftSim_ForegroundRaft_OarShaftRounded_%d_%s"), OarIndex, *Spec.RiverId),
            FVector(BaseX + 38.0f, CenterY + Side * 178.0f, -14.0f + 1.0f * static_cast<float>(OarIndex)),
            FRotator(0.0f, Side * 4.0f, 90.0f + (Side > 0.0f ? 7.0f : -7.0f)),
            FVector(0.010f, 0.010f, OarLengthScale),
            OarShaftColor);
        AddRaftProxyPart(
            CubeMesh,
            FString::Printf(TEXT("RaftSim_ForegroundRaft_OarBlade_%d_%s"), OarIndex, *Spec.RiverId),
            FVector(BaseX + 140.0f, CenterY + Side * OarBladeOffset, -16.0f),
            FRotator(0.0f, 8.0f * Side, Side > 0.0f ? 13.0f : -13.0f),
            FVector(0.040f, 0.10f, 0.004f),
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

void AddPreviewLightRig(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec)
{
    if (!World || !GEditor)
    {
        return;
    }

    ADirectionalLight* Sun = Cast<ADirectionalLight>(
        GEditor->AddActor(World->GetCurrentLevel(), ADirectionalLight::StaticClass(), FTransform(FRotator(-58.0f, -30.0f, 0.0f))));
    if (Sun)
    {
        Sun->SetActorLabel(TEXT("RaftSim_Sun_LumenPreview"));
        Sun->GetLightComponent()->SetIntensity(Spec.bDesertCanyon ? 9.2f : (Spec.bHasWaterfalls ? 7.4f : 7.8f));
        Sun->GetLightComponent()->SetLightColor(
            Spec.bDesertCanyon ? FLinearColor(1.0f, 0.84f, 0.66f)
                                : (Spec.bHasWaterfalls ? FLinearColor(0.88f, 0.96f, 0.90f)
                                                       : FLinearColor(0.98f, 0.96f, 0.88f)));
    }

    ASkyLight* SkyLight = Cast<ASkyLight>(
        GEditor->AddActor(World->GetCurrentLevel(), ASkyLight::StaticClass(), FTransform(FRotator::ZeroRotator, FVector(0.0f, 0.0f, 1000.0f))));
    if (SkyLight)
    {
        SkyLight->SetActorLabel(TEXT("RaftSim_SkyLight_PhotorealPreview"));
        SkyLight->GetLightComponent()->SetIntensity(Spec.bDesertCanyon ? 3.35f : (Spec.bHasWaterfalls ? 2.95f : 2.70f));
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
        Camera->GetCameraComponent()->PostProcessSettings.Sharpen = 0.18f;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_AutoExposureMethod = true;
        Camera->GetCameraComponent()->PostProcessSettings.AutoExposureMethod = AEM_Manual;
        Camera->GetCameraComponent()->PostProcessSettings.bOverride_AutoExposureBias = true;
        Camera->GetCameraComponent()->PostProcessSettings.AutoExposureBias = Spec.bDesertCanyon ? 0.0f : -0.04f;
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
    AddPreviewIrregularShorelineEdgeBreakupDetail(
        World,
        Spec,
        TerrainReliefPtr,
        HeightfieldPreviewPtr,
        WaterMaskPtr,
        VegetationMaskPtr);
    AddPreviewSourceAwareBankBreakupDetail(World, Spec, TerrainReliefPtr, HeightfieldPreviewPtr, WaterMaskPtr, VegetationMaskPtr);
    AddPreviewTerrainMaterialLayerDetail(World, Spec, TerrainReliefPtr, HeightfieldPreviewPtr, WaterMaskPtr, VegetationMaskPtr);
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
    AddPreviewWaterSurfaceDetail(World, Spec);
    AddPreviewFlowBandTextureDetail(World, Spec);
    AddPreviewWaterSurfaceChopAndTurbidityDetail(World, Spec);
    AddPreviewWaterShaderDepthReflectionScaffoldDetail(World, Spec);
    AddPreviewShallowWaterClarityAndAerationDetail(World, Spec, WaterMaskPtr, PlaneMesh);
    AddPreviewWaterMicroRippleGlintDetail(World, Spec, PlaneMesh);
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
        const FLinearColor UnadjustedBoulderColor = FMath::Lerp(
            BoulderBaseColor,
            FMath::Lerp(ScalePreviewColor(Spec.RockColor, 0.46f), ScalePreviewColor(Spec.WaterColor, 0.34f), 0.30f),
            FMath::Clamp(BoulderWaterT * 0.36f, 0.0f, 0.42f));
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
                  FMath::Clamp(Spec.FoliageColor.G + 0.035f * static_cast<float>((FoliageIndex + 1) % 4) + FoliageMaskT * 0.035f, 0.0f, 1.0f),
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
                    ScalePreviewColor(CanopyColor, 0.92f + 0.05f * static_cast<float>(LobeIndex)),
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
                AddPreviewProceduralLeafClusterActor(
                    World,
                    FString::Printf(TEXT("RaftSim_FoliageCanopy_%02d_%02d_%s"), FoliageIndex, LobeIndex, *Spec.RiverId),
                    FVector(LobeX, LobeY, TerrainZ + 112.0f * Height + 18.0f * static_cast<float>(LobeIndex % 3)),
                    static_cast<float>((FoliageIndex * 47 + LobeIndex * 19) % 360),
                    FVector(CanopyWidth * (1.08f - 0.08f * static_cast<float>(LobeIndex % 2)), CanopyWidth * (0.82f + 0.07f * static_cast<float>(LobeIndex % 3)), Height * (Spec.bHasWaterfalls ? 0.34f : 0.28f)),
                    CanopyColor,
                    FoliageIndex * 23 + LobeIndex + 6700,
                    Spec.bHasWaterfalls);
            }
        }

        const int32 OrganicLeafSprayCount = Spec.bDesertCanyon ? 2 : (Spec.bHasWaterfalls ? 5 : 3);
        for (int32 SprayIndex = 0; SprayIndex < OrganicLeafSprayCount; ++SprayIndex)
        {
            const float SprayAngleRadians =
                FMath::DegreesToRadians(static_cast<float>((FoliageIndex * 71 + SprayIndex * 113) % 360));
            const float SprayRadius = Spec.bDesertCanyon ? 46.0f : (Spec.bHasWaterfalls ? 132.0f : 88.0f);
            const FVector SprayLocation(
                X + FMath::Cos(SprayAngleRadians) * SprayRadius,
                Y + FMath::Sin(SprayAngleRadians) * SprayRadius,
                TerrainZ + 112.0f * Height + (Spec.bHasWaterfalls ? 36.0f : 18.0f) * static_cast<float>(SprayIndex));
            const FVector SprayScale = Spec.bDesertCanyon
                ? FVector(0.28f, 0.20f, 0.090f)
                : (Spec.bHasWaterfalls ? FVector(1.00f, 0.72f, 0.42f) : FVector(0.62f, 0.44f, 0.25f));
            AddPreviewOrganicLeafSprayActor(
                World,
                FString::Printf(TEXT("RaftSim_OrganicCanopyLeafSpray_%02d_%02d_%s"), FoliageIndex, SprayIndex, *Spec.RiverId),
                SprayLocation,
                static_cast<float>((FoliageIndex * 59 + SprayIndex * 37) % 360),
                SprayScale,
                ScalePreviewColor(CanopyColor, 0.78f + 0.07f * static_cast<float>(SprayIndex % 4)),
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
                    TerrainZ + 94.0f * Height),
                static_cast<float>((FoliageIndex * 67 + 19) % 360),
                FVector(
                    CanopyWidth * (Spec.bHasWaterfalls ? 0.78f : 0.62f),
                    CanopyWidth * (Spec.bHasWaterfalls ? 0.64f : 0.50f),
                    Height * (Spec.bHasWaterfalls ? 0.34f : 0.24f)),
                ScalePreviewColor(CanopyColor, Spec.bHasWaterfalls ? 0.82f : 0.78f),
                FoliageIndex * 71 + 13600,
                Spec.bHasWaterfalls,
                false);
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

    AddPreviewRaftForeground(World, Spec, CubeMesh, CylinderMesh);
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
            false,
            OutSummary);
        const bool bGuideSeatCaptured = CapturePreviewImageForSpec(
            Spec,
            CaptureRoot,
            GuideSeatCapturePath,
            TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"),
            TEXT("guide_seat_downstream"),
            TEXT("guide-seat downstream"),
            false,
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
