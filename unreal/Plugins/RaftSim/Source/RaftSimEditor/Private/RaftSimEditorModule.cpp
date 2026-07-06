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
    FString ElevationSample;
    FString SourceDrapeDescription;
    FLinearColor WaterColor = FLinearColor(0.05f, 0.26f, 0.32f);
    FLinearColor TerrainColor = FLinearColor(0.26f, 0.23f, 0.18f);
    FLinearColor RockColor = FLinearColor(0.35f, 0.33f, 0.29f);
    FLinearColor FoliageColor = FLinearColor(0.18f, 0.34f, 0.16f);
    FLinearColor RaftColor = FLinearColor(0.90f, 0.28f, 0.08f);
    float CanyonHeightCm = 850.0f;
    float RiverHalfWidthCm = 360.0f;
    float BankWidthCm = 760.0f;
    float BendAmplitudeCm = 240.0f;
    float TerrainReliefAmplitudeCm = 0.0f;
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
        TEXT("physics/data/real_world/south_fork_american_chili_bar/imagery/usda_naip_chili_bar_sample_512.png");
    SouthFork.TerrainReliefImage =
        TEXT("physics/data/real_world/south_fork_american_chili_bar/terrain/usgs_3dep_chili_bar_relief_preview_512.png");
    SouthFork.ElevationSample =
        TEXT("physics/data/real_world/south_fork_american_chili_bar/terrain/usgs_3dep_chili_bar_sample_256.tif");
    SouthFork.SourceDrapeDescription =
        TEXT("official USDA/APFO NAIP 512px aerial sample sampled into visible terrain overlay tiles; derived USGS 3DEP relief preview sampled into bank and valley terrain geometry; full elevation conditioning remains pending; rocks, foliage, water, foam, raft, and lighting remain proxy layers");
    SouthFork.WaterColor = FLinearColor(0.05f, 0.42f, 0.47f);
    SouthFork.TerrainColor = FLinearColor(0.35f, 0.30f, 0.21f);
    SouthFork.RockColor = FLinearColor(0.38f, 0.36f, 0.31f);
    SouthFork.FoliageColor = FLinearColor(0.22f, 0.38f, 0.15f);
    SouthFork.CanyonHeightCm = 850.0f;
    SouthFork.RiverHalfWidthCm = 335.0f;
    SouthFork.BankWidthCm = 720.0f;
    SouthFork.BendAmplitudeCm = 290.0f;
    SouthFork.TerrainReliefAmplitudeCm = 180.0f;
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
        TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/imagery/usda_naip_lees_ferry_sample_512.png");
    Colorado.TerrainReliefImage =
        TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/terrain/usgs_3dep_lees_ferry_relief_preview_512.png");
    Colorado.ElevationSample =
        TEXT("physics/data/real_world/colorado_river_grand_canyon_rowing/terrain/usgs_3dep_lees_ferry_sample_256.tif");
    Colorado.SourceDrapeDescription =
        TEXT("official USDA/APFO NAIP 512px Lees Ferry aerial sample sampled into visible canyon terrain overlay tiles; derived USGS 3DEP relief preview sampled into canyon bank geometry; full canyon heightfield conditioning remains pending; rocks, foliage, water, foam, raft, and lighting remain proxy layers");
    Colorado.WaterColor = FLinearColor(0.34f, 0.28f, 0.19f);
    Colorado.TerrainColor = FLinearColor(0.48f, 0.30f, 0.18f);
    Colorado.RockColor = FLinearColor(0.55f, 0.32f, 0.20f);
    Colorado.FoliageColor = FLinearColor(0.30f, 0.32f, 0.18f);
    Colorado.CanyonHeightCm = 2600.0f;
    Colorado.RiverHalfWidthCm = 520.0f;
    Colorado.BankWidthCm = 1500.0f;
    Colorado.BendAmplitudeCm = 360.0f;
    Colorado.TerrainReliefAmplitudeCm = 650.0f;
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
        TEXT("physics/data/real_world/pacuare_river_costa_rica/imagery/pacuare_nasa_gibs_2025-04-02_demshade_source_drape_512.png");
    Pacuare.TerrainReliefImage =
        TEXT("physics/data/real_world/pacuare_river_costa_rica/terrain/pacuare_dem_relief_preview_512.png");
    Pacuare.ElevationSample =
        TEXT("physics/data/real_world/pacuare_river_costa_rica/terrain/copernicus_dem_glo30_N09_W084.tif; physics/data/real_world/pacuare_river_costa_rica/terrain/copernicus_dem_glo30_N10_W084.tif");
    Pacuare.SourceDrapeDescription =
        TEXT("deterministic preview drape generated from the selected official NASA GIBS MODIS/Terra true-color sample and Copernicus DEM GLO-30 relief, with cloud gaps filled by DEM-derived rainforest shading; Copernicus DEM COG tiles remain recorded for follow-on Pacuare gorge heightfield conditioning; rocks, foliage, water, waterfalls, foam, raft, and lighting remain proxy layers");
    Pacuare.WaterColor = FLinearColor(0.04f, 0.35f, 0.28f);
    Pacuare.TerrainColor = FLinearColor(0.17f, 0.22f, 0.13f);
    Pacuare.RockColor = FLinearColor(0.20f, 0.24f, 0.20f);
    Pacuare.FoliageColor = FLinearColor(0.06f, 0.30f, 0.09f);
    Pacuare.CanyonHeightCm = 1450.0f;
    Pacuare.RiverHalfWidthCm = 305.0f;
    Pacuare.BankWidthCm = 680.0f;
    Pacuare.BendAmplitudeCm = 340.0f;
    Pacuare.TerrainReliefAmplitudeCm = 420.0f;
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

float SmoothPreviewStep(float Edge0, float Edge1, float Value)
{
    if (FMath::IsNearlyEqual(Edge0, Edge1))
    {
        return Value >= Edge1 ? 1.0f : 0.0f;
    }

    const float T = FMath::Clamp((Value - Edge0) / (Edge1 - Edge0), 0.0f, 1.0f);
    return T * T * (3.0f - 2.0f * T);
}

float GetPreviewRiverCenterY(const FRaftSimEnvironmentPreviewSpec& Spec, float X)
{
    const float Primary = FMath::Sin((X + 3800.0f) * 0.00043f) * Spec.BendAmplitudeCm;
    const float Secondary = FMath::Sin((X - 600.0f) * 0.00019f) * Spec.BendAmplitudeCm * 0.35f;
    return Primary + Secondary;
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
    const float ReliefMask = SmoothPreviewStep(
        Spec.RiverHalfWidthCm + 110.0f,
        Spec.RiverHalfWidthCm + Spec.BankWidthCm + 740.0f,
        ChannelOffset);
    return (TerrainRelief->SampleLuma(U, V) - 0.5f) * Spec.TerrainReliefAmplitudeCm * ReliefMask;
}

float GetPreviewTerrainHeightCm(
    const FRaftSimEnvironmentPreviewSpec& Spec,
    float X,
    float Y,
    const FRaftSimPreviewImage* TerrainRelief = nullptr)
{
    const float CenterY = GetPreviewRiverCenterY(Spec, X);
    const float Offset = FMath::Abs(Y - CenterY);
    const float InnerBank = Spec.RiverHalfWidthCm;
    const float OuterBank = Spec.RiverHalfWidthCm + Spec.BankWidthCm;
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

void AddPreviewTerrainMesh(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief)
{
    constexpr int32 XSteps = 112;
    constexpr int32 YSteps = 38;
    const float MinX = -5800.0f;
    const float MaxX = 26500.0f;
    const float HalfWidth = Spec.bDesertCanyon ? 4300.0f : 2750.0f;

    TArray<FVector> Vertices;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<int32> Triangles;
    Vertices.Reserve((XSteps + 1) * (YSteps + 1));
    Normals.Reserve((XSteps + 1) * (YSteps + 1));
    UVs.Reserve((XSteps + 1) * (YSteps + 1));
    Triangles.Reserve(XSteps * YSteps * 6);

    for (int32 XIndex = 0; XIndex <= XSteps; ++XIndex)
    {
        const float U = static_cast<float>(XIndex) / static_cast<float>(XSteps);
        const float X = FMath::Lerp(MinX, MaxX, U);
        for (int32 YIndex = 0; YIndex <= YSteps; ++YIndex)
        {
            const float V = static_cast<float>(YIndex) / static_cast<float>(YSteps);
            const float Y = FMath::Lerp(-HalfWidth, HalfWidth, V);
            const float Z = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainRelief);
            Vertices.Add(FVector(X, Y, Z));
            UVs.Add(FVector2D(U * 12.0f, V * 4.0f));
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
        Spec.TerrainColor);
}

void AddPreviewAerialDrapeTiles(
    UWorld* World,
    const FRaftSimEnvironmentPreviewSpec& Spec,
    const FRaftSimPreviewImage* TerrainRelief)
{
    if (!World || Spec.AerialDrapeImage.IsEmpty())
    {
        return;
    }

    FRaftSimPreviewImage AerialDrape;
    if (!LoadPreviewPngImage(Spec.AerialDrapeImage, AerialDrape))
    {
        return;
    }

    constexpr int32 XTiles = 40;
    constexpr int32 YTiles = 12;
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
            if (FMath::Abs(Y - CenterY) < Spec.RiverHalfWidthCm + 180.0f)
            {
                continue;
            }

            const FLinearColor AerialColor = FMath::Lerp(AerialDrape.Sample(U, V), Spec.TerrainColor, 0.08f);
            const float HalfLength = TileLength * 0.50f;
            const float HalfTileWidth = TileWidth * 0.50f;
            const float TileZOffset = 14.0f;
            const float X0 = X - HalfLength;
            const float X1 = X + HalfLength;
            const float Y0 = Y - HalfTileWidth;
            const float Y1 = Y + HalfTileWidth;

            TArray<FVector> Vertices;
            Vertices.Add(FVector(X0, Y0, GetPreviewTerrainHeightCm(Spec, X0, Y0, TerrainRelief) + TileZOffset));
            Vertices.Add(FVector(X0, Y1, GetPreviewTerrainHeightCm(Spec, X0, Y1, TerrainRelief) + TileZOffset));
            Vertices.Add(FVector(X1, Y0, GetPreviewTerrainHeightCm(Spec, X1, Y0, TerrainRelief) + TileZOffset));
            Vertices.Add(FVector(X1, Y1, GetPreviewTerrainHeightCm(Spec, X1, Y1, TerrainRelief) + TileZOffset));

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
    constexpr int32 CrossSteps = 6;
    const float MinX = -5600.0f;
    const float MaxX = 26200.0f;

    TArray<FVector> Vertices;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<int32> Triangles;
    Vertices.Reserve((XSteps + 1) * (CrossSteps + 1));
    Normals.Reserve((XSteps + 1) * (CrossSteps + 1));
    UVs.Reserve((XSteps + 1) * (CrossSteps + 1));
    Triangles.Reserve(XSteps * CrossSteps * 6);

    for (int32 XIndex = 0; XIndex <= XSteps; ++XIndex)
    {
        const float U = static_cast<float>(XIndex) / static_cast<float>(XSteps);
        const float X = FMath::Lerp(MinX, MaxX, U);
        const float CenterY = GetPreviewRiverCenterY(Spec, X);
        const float Width =
            Spec.RiverHalfWidthCm * (1.0f + 0.10f * FMath::Sin(X * 0.0012f) + (Spec.bDesertCanyon ? 0.18f : 0.05f));
        for (int32 CrossIndex = 0; CrossIndex <= CrossSteps; ++CrossIndex)
        {
            const float V = static_cast<float>(CrossIndex) / static_cast<float>(CrossSteps);
            const float Lateral = FMath::Lerp(-Width, Width, V);
            const float Wave = FMath::Sin(X * 0.011f + Lateral * 0.015f) * (Spec.bDesertCanyon ? 2.0f : 4.5f);
            Vertices.Add(FVector(X, CenterY + Lateral, 10.0f + Wave));
            UVs.Add(FVector2D(U * 18.0f, V));
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
        Spec.WaterColor);
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
        const float Z = 25.0f + SurfaceWave + 2.0f * FMath::Sin(Phase * 1.7f + T * PI);

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

void AddPreviewFoamAndHydraulics(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec)
{
    if (!World)
    {
        return;
    }

    for (int32 FoamIndex = 0; FoamIndex < Spec.FoamTrainCount; ++FoamIndex)
    {
        const float X = -4050.0f + static_cast<float>(FoamIndex) * (28000.0f / FMath::Max(1, Spec.FoamTrainCount));
        const float Offset = FMath::Sin(static_cast<float>(FoamIndex) * 1.7f) * Spec.RiverHalfWidthCm * 0.42f;
        const float Length = Spec.bDesertCanyon ? 1420.0f : 1050.0f;
        AddPreviewFoamRibbon(
            World,
            Spec,
            FString::Printf(TEXT("RaftSim_FoamTongue_%02d_%s"), FoamIndex, *Spec.RiverId),
            X - Length * 0.48f,
            Length,
            Offset,
            54.0f + 12.0f * static_cast<float>(FoamIndex % 3),
            static_cast<float>(FoamIndex) * 0.83f,
            FLinearColor(0.82f, 0.90f, 0.86f));
        AddPreviewFoamRibbon(
            World,
            Spec,
            FString::Printf(TEXT("RaftSim_WaveHighlight_%02d_%s"), FoamIndex, *Spec.RiverId),
            X - Length * 0.26f,
            Length * 0.55f,
            Offset * 0.55f,
            22.0f + 5.0f * static_cast<float>(FoamIndex % 2),
            static_cast<float>(FoamIndex) * 1.19f + 0.4f,
            Spec.bDesertCanyon ? FLinearColor(0.78f, 0.82f, 0.76f) : FLinearColor(0.72f, 0.88f, 0.84f));

        if (!Spec.bDesertCanyon && FoamIndex % 3 == 0)
        {
            AddPreviewFoamRibbon(
                World,
                Spec,
                FString::Printf(TEXT("RaftSim_EddyLine_%02d_%s"), FoamIndex, *Spec.RiverId),
                X + 80.0f,
                720.0f,
                Spec.RiverHalfWidthCm * 0.76f,
                18.0f,
                static_cast<float>(FoamIndex) * 0.47f,
                FLinearColor(0.88f, 0.94f, 0.90f));
        }
    }
}

void AddPreviewRaftForeground(UWorld* World, const FRaftSimEnvironmentPreviewSpec& Spec, UStaticMesh* CubeMesh, UStaticMesh* CylinderMesh)
{
    if (!World || !CubeMesh || !CylinderMesh)
    {
        return;
    }

    const float BaseX = -4920.0f;
    const float CenterY = GetPreviewRiverCenterY(Spec, BaseX);
    const float Z = 30.0f;
    AddPreviewMeshActor(
        World,
        CylinderMesh,
        FString::Printf(TEXT("RaftSim_ForegroundRaft_LeftTube_%s"), *Spec.RiverId),
        FVector(BaseX + 180.0f, CenterY - 92.0f, Z),
        FRotator(0.0f, 90.0f, 0.0f),
        FVector(0.38f, 0.38f, 2.9f),
        Spec.RaftColor);
    AddPreviewMeshActor(
        World,
        CylinderMesh,
        FString::Printf(TEXT("RaftSim_ForegroundRaft_RightTube_%s"), *Spec.RiverId),
        FVector(BaseX + 180.0f, CenterY + 92.0f, Z),
        FRotator(0.0f, 90.0f, 0.0f),
        FVector(0.38f, 0.38f, 2.9f),
        Spec.RaftColor);
    AddPreviewMeshActor(
        World,
        CylinderMesh,
        FString::Printf(TEXT("RaftSim_ForegroundRaft_Bow_%s"), *Spec.RiverId),
        FVector(BaseX + 470.0f, CenterY, Z + 3.0f),
        FRotator(90.0f, 0.0f, 0.0f),
        FVector(0.36f, 0.36f, 1.9f),
        Spec.RaftColor);
    AddPreviewMeshActor(
        World,
        CubeMesh,
        FString::Printf(TEXT("RaftSim_ForegroundRaft_Floor_%s"), *Spec.RiverId),
        FVector(BaseX + 180.0f, CenterY, 16.0f),
        FRotator::ZeroRotator,
        FVector(2.6f, 1.0f, 0.05f),
        FLinearColor(0.04f, 0.045f, 0.04f));
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

FString GetPreviewCaptureRelativePath(const FRaftSimEnvironmentPreviewSpec& Spec)
{
    return FPaths::Combine(
        TEXT("docs/environment-captures/photoreal_river_previews"),
        Spec.RiverId + TEXT("_guide_seat_downstream.png"));
}

FString GetPreviewFidelityNote(const FRaftSimEnvironmentPreviewSpec& Spec)
{
    if (!Spec.SourceDrapeDescription.IsEmpty())
    {
        return Spec.SourceDrapeDescription;
    }

    return TEXT("source-aware procedural blockout with generated valley, river, foam, rocks, foliage, and raft proxies; not yet production photoreal");
}

ACameraActor* FindPreviewCaptureCamera(UWorld* World)
{
    ACameraActor* FallbackCamera = nullptr;
    for (TActorIterator<ACameraActor> It(World); It; ++It)
    {
        ACameraActor* Camera = *It;
        if (!FallbackCamera)
        {
            FallbackCamera = Camera;
        }

        if (Camera && Camera->GetActorLabel() == TEXT("RaftSim_GuideSeat_DownstreamCaptureCamera"))
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

    ACameraActor* Camera = FindPreviewCaptureCamera(World);
    if (!Camera || !Camera->GetCameraComponent())
    {
        OutSummary += FString::Printf(TEXT("No guide-seat capture camera found in %s\n"), *Spec.MapPackagePath);
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

    OutRelativeCapturePath = GetPreviewCaptureRelativePath(Spec);
    const FString AbsoluteCapturePath = FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), OutRelativeCapturePath));
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);
    const bool bSaved = FFileHelper::SaveArrayToFile(CompressedPng, *AbsoluteCapturePath);

    SceneCapture->Destroy();
    RenderTarget->ReleaseResource();

    OutSummary += FString::Printf(
        TEXT("%s rendered guide-seat capture for %s -> %s\n"),
        bSaved ? TEXT("Saved") : TEXT("Failed"),
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
    UStaticMesh* PcgBoulderMesh = LoadPreviewMesh(TEXT("/PCG/SampleContent/SimpleForest/Meshes/PCG_Boulder_02.PCG_Boulder_02"));
    UStaticMesh* PcgTreeMeshA = LoadPreviewMesh(TEXT("/PCG/SampleContent/SimpleForest/Meshes/PCG_Tree_01.PCG_Tree_01"));
    UStaticMesh* PcgTreeMeshB = LoadPreviewMesh(TEXT("/PCG/SampleContent/SimpleForest/Meshes/PCG_Tree_02.PCG_Tree_02"));
    UStaticMesh* PcgTreeMeshC = LoadPreviewMesh(TEXT("/PCG/SampleContent/SimpleForest/Meshes/PCG_Tree_03.PCG_Tree_03"));
    UStaticMesh* PcgSeedlingMesh =
        LoadPreviewMesh(TEXT("/PCG/SampleContent/SimpleForest/Meshes/PCG_Seedling_01.PCG_Seedling_01"));

    FRaftSimPreviewImage TerrainRelief;
    const FRaftSimPreviewImage* TerrainReliefPtr = nullptr;
    if (!Spec.TerrainReliefImage.IsEmpty() && LoadPreviewPngImage(Spec.TerrainReliefImage, TerrainRelief))
    {
        TerrainReliefPtr = &TerrainRelief;
    }

    AddPreviewLightRig(World, Spec);

    AddPreviewTerrainMesh(World, Spec, TerrainReliefPtr);
    AddPreviewAerialDrapeTiles(World, Spec, TerrainReliefPtr);
    AddPreviewRiverRibbonMesh(World, Spec);
    AddPreviewRaftForeground(World, Spec, CubeMesh, CylinderMesh);
    AddPreviewFoamAndHydraulics(World, Spec);

    for (int32 BoulderIndex = 0; BoulderIndex < Spec.BoulderCount; ++BoulderIndex)
    {
        const float X = -3600.0f + static_cast<float>(BoulderIndex) * (28200.0f / FMath::Max(1, Spec.BoulderCount));
        const float CenterY = GetPreviewRiverCenterY(Spec, X);
        const float Side = (BoulderIndex % 2 == 0) ? -1.0f : 1.0f;
        const float Y = CenterY + Side * (Spec.RiverHalfWidthCm * (0.32f + 0.55f * FMath::Abs(FMath::Sin(static_cast<float>(BoulderIndex) * 1.91f))));
        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainReliefPtr);
        const float Scale = Spec.bDesertCanyon ? 1.6f : 1.0f + 0.35f * static_cast<float>(BoulderIndex % 3);
        AddPreviewMeshActor(
            World,
            PcgBoulderMesh ? PcgBoulderMesh : SphereMesh,
            FString::Printf(TEXT("RaftSim_SourceAwareBoulder_%02d_%s"), BoulderIndex, *Spec.RiverId),
            FVector(X, Y, FMath::Max(24.0f, TerrainZ + 44.0f + 12.0f * static_cast<float>(BoulderIndex % 4))),
            FRotator(0.0f, static_cast<float>(BoulderIndex * 31), 0.0f),
            PcgBoulderMesh ? FVector(Scale * 1.25f, Scale * 1.05f, Scale * 0.72f) : FVector(Scale * 1.4f, Scale, Scale * 0.62f),
            Spec.RockColor);
    }

    for (int32 FoliageIndex = 0; FoliageIndex < Spec.FoliageCount; ++FoliageIndex)
    {
        const float X = -2400.0f + static_cast<float>(FoliageIndex) * (28600.0f / FMath::Max(1, Spec.FoliageCount));
        const float CenterY = GetPreviewRiverCenterY(Spec, X);
        const float Side = (FoliageIndex % 2 == 0) ? -1.0f : 1.0f;
        const float BankOffset = Spec.bDesertCanyon ? Spec.RiverHalfWidthCm + 1350.0f : Spec.RiverHalfWidthCm + 620.0f;
        const float Y = CenterY + Side * (BankOffset + 210.0f * FMath::Sin(static_cast<float>(FoliageIndex) * 1.31f));
        const float TerrainZ = GetPreviewTerrainHeightCm(Spec, X, Y, TerrainReliefPtr);
        const float Height = Spec.bHasWaterfalls ? 2.35f + 0.28f * static_cast<float>(FoliageIndex % 5) : (Spec.bDesertCanyon ? 0.50f : 1.45f + 0.18f * static_cast<float>(FoliageIndex % 3));
        const float CanopyWidth = Spec.bHasWaterfalls ? 1.35f + 0.18f * static_cast<float>(FoliageIndex % 4) : (Spec.bDesertCanyon ? 0.55f : 0.92f + 0.10f * static_cast<float>(FoliageIndex % 3));
        const FLinearColor CanopyColor = Spec.bDesertCanyon
            ? FLinearColor(0.22f, 0.28f, 0.13f)
            : FLinearColor(
                  FMath::Clamp(Spec.FoliageColor.R + 0.025f * static_cast<float>(FoliageIndex % 3), 0.0f, 1.0f),
                  FMath::Clamp(Spec.FoliageColor.G + 0.055f * static_cast<float>((FoliageIndex + 1) % 4), 0.0f, 1.0f),
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
                ? 0.46f + 0.05f * static_cast<float>(FoliageIndex % 4)
                : (Spec.bDesertCanyon ? 0.34f + 0.04f * static_cast<float>(FoliageIndex % 3) : 0.36f + 0.04f * static_cast<float>(FoliageIndex % 3));
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

        if (!Spec.bDesertCanyon && FoliageIndex % 4 == 0)
        {
            const float UnderstoryX = X + 140.0f;
            const float UnderstoryY = Y - Side * 180.0f;
            if (PcgSeedlingMesh)
            {
                AddPreviewMeshActor(
                    World,
                    PcgSeedlingMesh,
                    FString::Printf(TEXT("RaftSim_SourceAwareUnderstory_%02d_%s"), FoliageIndex, *Spec.RiverId),
                    FVector(
                        UnderstoryX,
                        UnderstoryY,
                        GetPreviewTerrainHeightCm(Spec, UnderstoryX, UnderstoryY, TerrainReliefPtr)),
                    FRotator(0.0f, static_cast<float>((FoliageIndex * 29) % 360), 0.0f),
                    FVector(0.20f, 0.20f, 0.20f),
                    CanopyColor);
            }
            else
            {
                AddPreviewMeshActor(
                    World,
                    SphereMesh,
                    FString::Printf(TEXT("RaftSim_Understory_%02d_%s"), FoliageIndex, *Spec.RiverId),
                    FVector(
                        UnderstoryX,
                        UnderstoryY,
                        GetPreviewTerrainHeightCm(Spec, UnderstoryX, UnderstoryY, TerrainReliefPtr) + 34.0f),
                    FRotator(0.0f, static_cast<float>((FoliageIndex * 29) % 360), 0.0f),
                    FVector(0.56f, 0.42f, 0.28f),
                    CanopyColor);
            }
        }
    }

    if (Spec.bHasWaterfalls)
    {
        for (int32 WaterfallIndex = 0; WaterfallIndex < 5; ++WaterfallIndex)
        {
            const float X = 4000.0f + static_cast<float>(WaterfallIndex) * 4300.0f;
            const float Side = (WaterfallIndex % 2 == 0) ? -1.0f : 1.0f;
            const float Y = GetPreviewRiverCenterY(Spec, X) + Side * 2200.0f;
            AddPreviewMeshActor(
                World,
                PlaneMesh,
                FString::Printf(TEXT("RaftSim_RainforestWaterfall_%02d"), WaterfallIndex),
                FVector(X, Y, 660.0f),
                FRotator(0.0f, 0.0f, 90.0f),
                FVector(4.2f, 12.0f, 1.0f),
                FLinearColor(0.72f, 0.92f, 0.94f));
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
    const FString SourcePlanRelativePath =
        TEXT("unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json");
    const FString SourcePlanAbsolutePath =
        FPaths::ConvertRelativePathToFull(FPaths::Combine(GetRepoRoot(), SourcePlanRelativePath));

    if (!FPaths::FileExists(SourcePlanAbsolutePath))
    {
        OutSummary += FString::Printf(TEXT("Missing photoreal river source plan: %s\n"), *SourcePlanAbsolutePath);
        return false;
    }

    OutSummary += FString::Printf(TEXT("Using photoreal river source plan: %s\n"), *SourcePlanRelativePath);

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
    const FString CaptureRoot = GetEnvironmentCaptureRoot();
    IFileManager::Get().MakeDirectory(*CaptureRoot, true);

    FString EntriesJson;
    bool bAllCaptured = true;
    const TArray<FRaftSimEnvironmentPreviewSpec> Specs = GetEnvironmentPreviewSpecs();
    for (int32 Index = 0; Index < Specs.Num(); ++Index)
    {
        const FRaftSimEnvironmentPreviewSpec& Spec = Specs[Index];
        FString CapturePath = GetPreviewCaptureRelativePath(Spec);
        const bool bCaptured = CapturePreviewImageForSpec(Spec, CaptureRoot, CapturePath, OutSummary);
        bAllCaptured &= bCaptured;

        EntriesJson += FString::Printf(
            TEXT("%s    {\n")
            TEXT("      \"river_id\": \"%s\",\n")
            TEXT("      \"display_name\": \"%s\",\n")
            TEXT("      \"map_package\": \"%s\",\n")
            TEXT("      \"source_manifest\": \"%s\",\n")
            TEXT("      \"capture\": \"%s\",\n")
            TEXT("      \"status\": \"%s\",\n")
            TEXT("      \"aerial_drape_image\": \"%s\",\n")
            TEXT("      \"terrain_relief_image\": \"%s\",\n")
            TEXT("      \"elevation_sample\": \"%s\",\n")
            TEXT("      \"fidelity_note\": \"%s\"\n")
            TEXT("    }"),
            Index == 0 ? TEXT("") : TEXT(",\n"),
            *EscapeRaftSimJsonString(Spec.RiverId),
            *EscapeRaftSimJsonString(Spec.DisplayName),
            *EscapeRaftSimJsonString(Spec.MapPackagePath),
            *EscapeRaftSimJsonString(Spec.SourceManifest),
            *EscapeRaftSimJsonString(CapturePath),
            bCaptured && !Spec.SourceDrapeDescription.IsEmpty() ? TEXT("captured_source_derived_preview_render") : (bCaptured ? TEXT("captured_procedural_blockout_render") : TEXT("capture_failed")),
            *EscapeRaftSimJsonString(Spec.AerialDrapeImage),
            *EscapeRaftSimJsonString(Spec.TerrainReliefImage),
            *EscapeRaftSimJsonString(Spec.ElevationSample),
            *EscapeRaftSimJsonString(GetPreviewFidelityNote(Spec)));
    }

    const FString Manifest = FString::Printf(
        TEXT("{\n")
        TEXT("  \"schema\": \"raftsim.unreal.environment_capture_manifest.v1\",\n")
        TEXT("  \"capture_type\": \"guide_seat_downstream_unreal_preview\",\n")
        TEXT("  \"source_plan\": \"unreal/Content/RaftSim/Rendering/photoreal_river_environment_sources.json\",\n")
        TEXT("  \"status\": \"%s\",\n")
        TEXT("  \"captures\": [\n")
        TEXT("%s\n")
        TEXT("  ]\n")
        TEXT("}\n"),
        bAllCaptured ? TEXT("south_fork_colorado_and_pacuare_source_draped_previews_available; photoreal source_data_and_asset_replacement_required") : TEXT("one_or_more_captures_failed"),
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
