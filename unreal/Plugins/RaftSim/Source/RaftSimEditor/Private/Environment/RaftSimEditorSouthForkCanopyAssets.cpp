#include "Environment/RaftSimEditorEnvironmentInternal.h"
#include "Materials/MaterialExpressionPerInstanceRandom.h"

namespace RaftSimEditorEnvironment
{
namespace
{
constexpr TCHAR PonderosaMatureBillboardSourceRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_PonderosaPine_Mature_PhotorealV2.png");
constexpr TCHAR PonderosaIntermediateBillboardSourceRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_PonderosaPine_Intermediate_PhotorealV2.png");
constexpr TCHAR PonderosaYoungerBillboardSourceRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_PonderosaPine_Young_PhotorealV2.png");
constexpr TCHAR InteriorLiveOakBillboardSourceRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_InteriorLiveOak_PhotorealV2.png");
constexpr TCHAR WhiteAlderBillboardSourceRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_WhiteAlder_PhotorealV2.png");
constexpr TCHAR DeerbrushBillboardSourceRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_DeerbrushShrub_PhotorealV2.png");
constexpr TCHAR InteriorLiveOakBranchAlbedoOpacityRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_InteriorLiveOak_BranchAtlasV1.png");
constexpr TCHAR InteriorLiveOakBranchNormalRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_InteriorLiveOak_BranchAtlasV1_Normal.png");
constexpr TCHAR InteriorLiveOakBranchPackedRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_InteriorLiveOak_BranchAtlasV1_AORoughnessSubsurface.png");
constexpr TCHAR InteriorLiveOakBranchV2AlbedoOpacityRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_InteriorLiveOak_BranchAtlasV2_AlbedoOpacity.png");
constexpr TCHAR InteriorLiveOakBranchV2NormalRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_InteriorLiveOak_BranchAtlasV2_Normal.png");
constexpr TCHAR InteriorLiveOakBranchV2PackedRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_InteriorLiveOak_BranchAtlasV2_AORoughnessSubsurface.png");
constexpr TCHAR InteriorLiveOakLeafClustersV3AlbedoOpacityRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_InteriorLiveOak_LeafClustersV3_AlbedoOpacity.png");
constexpr TCHAR InteriorLiveOakLeafClustersV3NormalRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_InteriorLiveOak_LeafClustersV3_Normal.png");
constexpr TCHAR InteriorLiveOakLeafClustersV3PackedRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_InteriorLiveOak_LeafClustersV3_AORoughnessSubsurface.png");
constexpr TCHAR InteriorLiveOakBarkV1AlbedoRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_InteriorLiveOak_BarkV1_Albedo.png");
constexpr TCHAR InteriorLiveOakBarkV1NormalRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_InteriorLiveOak_BarkV1_Normal.png");
constexpr TCHAR InteriorLiveOakBarkV1PackedRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_InteriorLiveOak_BarkV1_AORoughnessHeight.png");
constexpr TCHAR PonderosaBranchAlbedoOpacityRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_PonderosaPine_BranchAtlasV1.png");
constexpr TCHAR PonderosaBranchNormalRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_PonderosaPine_BranchAtlasV1_Normal.png");
constexpr TCHAR PonderosaBranchPackedRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_PonderosaPine_BranchAtlasV1_AORoughnessSubsurface.png");
constexpr TCHAR WhiteAlderBranchAlbedoOpacityRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_WhiteAlder_BranchAtlasV1.png");
constexpr TCHAR WhiteAlderBranchNormalRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_WhiteAlder_BranchAtlasV1_Normal.png");
constexpr TCHAR WhiteAlderBranchPackedRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_WhiteAlder_BranchAtlasV1_AORoughnessSubsurface.png");
constexpr TCHAR DeerbrushBranchAlbedoOpacityRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_Deerbrush_BranchAtlasV1.png");
constexpr TCHAR DeerbrushBranchNormalRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_Deerbrush_BranchAtlasV1_Normal.png");
constexpr TCHAR DeerbrushBranchPackedRelativePath[] =
    TEXT("unreal/SourceArt/RaftSim/Environment/GeneratedCanopy/"
         "T_Deerbrush_BranchAtlasV1_AORoughnessSubsurface.png");

UTexture2D* CreateSouthForkCanopyTextureMap(
    const FString& SpeciesAssetName,
    const FString& SourceRelativePath,
    const FString& MapKey,
    const FString& MapKind,
    TextureCompressionSettings CompressionSettings,
    bool bSRGB,
    FString& OutSummary,
    TextureAddress AddressMode = TA_Clamp)
{
    FRaftSimFirstPartyMaterialTextureAssetSpec Spec;
    Spec.RiverId = TEXT("south_fork_generated_canopy");
    Spec.RiverAssetName = SpeciesAssetName;
    Spec.MapKey = MapKey;
    Spec.MapKind = MapKind;
    Spec.SourceRelativePath = SourceRelativePath;
    Spec.TextureAssetRootPackagePath =
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Textures");
    Spec.CompressionSettings = CompressionSettings;
    Spec.bSRGB = bSRGB;
    Spec.LODGroup = TEXTUREGROUP_Impostor;
    Spec.AddressX = AddressMode;
    Spec.AddressY = AddressMode;
    Spec.bCompressionNoAlpha = false;
    bool bSaved = false;
    UTexture2D* Texture = CreateOrUpdateFirstPartyMaterialTextureAsset(
        Spec, OutSummary, bSaved);
    if (!Texture || !bSaved ||
        !RebuildAndValidateFirstPartyTexturePlatformData(Texture, Spec, OutSummary))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to build generated South Fork canopy texture %s.\n"),
            *SourceRelativePath);
        return nullptr;
    }
    return Texture;
}

struct FSouthForkCanopyBranchTextureSet
{
    UTexture2D* AlbedoOpacity = nullptr;
    UTexture2D* Normal = nullptr;
    UTexture2D* Packed = nullptr;

    bool IsComplete() const
    {
        return AlbedoOpacity && Normal && Packed;
    }
};

FSouthForkCanopyBranchTextureSet CreateSouthForkCanopyBranchTextureSet(
    const FString& SpeciesAssetName,
    const FString& AlbedoOpacityRelativePath,
    const FString& NormalRelativePath,
    const FString& PackedRelativePath,
    FString& OutSummary)
{
    FSouthForkCanopyBranchTextureSet Textures;
    Textures.AlbedoOpacity = CreateSouthForkCanopyTextureMap(
        SpeciesAssetName,
        AlbedoOpacityRelativePath,
        TEXT("AlbedoOpacity"),
        TEXT("generated_canopy_branch_albedo_opacity"),
        TC_Default,
        /*bSRGB=*/true,
        OutSummary);
    Textures.Normal = CreateSouthForkCanopyTextureMap(
        SpeciesAssetName,
        NormalRelativePath,
        TEXT("Normal"),
        TEXT("generated_canopy_branch_normal"),
        TC_Normalmap,
        /*bSRGB=*/false,
        OutSummary);
    Textures.Packed = CreateSouthForkCanopyTextureMap(
        SpeciesAssetName,
        PackedRelativePath,
        TEXT("AORoughnessSubsurface"),
        TEXT("generated_canopy_branch_ao_roughness_subsurface"),
        TC_Masks,
        /*bSRGB=*/false,
        OutSummary);
    return Textures;
}

struct FSouthForkCanopyBarkTextureSet
{
    UTexture2D* Albedo = nullptr;
    UTexture2D* Normal = nullptr;
    UTexture2D* Packed = nullptr;

    bool IsComplete() const
    {
        return Albedo && Normal && Packed;
    }
};

FSouthForkCanopyBarkTextureSet CreateSouthForkCanopyBarkTextureSet(
    const FString& SpeciesAssetName,
    const FString& AlbedoRelativePath,
    const FString& NormalRelativePath,
    const FString& PackedRelativePath,
    FString& OutSummary)
{
    FSouthForkCanopyBarkTextureSet Textures;
    Textures.Albedo = CreateSouthForkCanopyTextureMap(
        SpeciesAssetName,
        AlbedoRelativePath,
        TEXT("BarkAlbedo"),
        TEXT("generated_canopy_bark_albedo"),
        TC_Default,
        /*bSRGB=*/true,
        OutSummary,
        TA_Wrap);
    Textures.Normal = CreateSouthForkCanopyTextureMap(
        SpeciesAssetName,
        NormalRelativePath,
        TEXT("BarkNormal"),
        TEXT("generated_canopy_bark_normal"),
        TC_Normalmap,
        /*bSRGB=*/false,
        OutSummary,
        TA_Wrap);
    Textures.Packed = CreateSouthForkCanopyTextureMap(
        SpeciesAssetName,
        PackedRelativePath,
        TEXT("BarkAORoughnessHeight"),
        TEXT("generated_canopy_bark_ao_roughness_height"),
        TC_Masks,
        /*bSRGB=*/false,
        OutSummary,
        TA_Wrap);
    return Textures;
}

UTexture2D* CreateSouthForkCanopyTexture(
    const FString& SpeciesAssetName,
    const FString& SourceRelativePath,
    FString& OutSummary)
{
    return CreateSouthForkCanopyTextureMap(
        SpeciesAssetName,
        SourceRelativePath,
        TEXT("BillboardAlbedoOpacity"),
        TEXT("generated_canopy_albedo_opacity"),
        TC_Default,
        /*bSRGB=*/true,
        OutSummary);
}

UMaterial* CreateSouthForkCanopyMaterial(
    const FString& SpeciesAssetName,
    UTexture2D* AlbedoOpacity,
    FString& OutSummary)
{
    if (!AlbedoOpacity)
    {
        return nullptr;
    }
    const FString PackagePath = FString::Printf(
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Materials/"
             "M_RaftSim_%s_Billboard"),
        *SpeciesAssetName);
    const FString AssetName = FPackageName::GetLongPackageAssetName(PackagePath);
    const FString ObjectPath = FString::Printf(
        TEXT("%s.%s"), *PackagePath, *AssetName);
    UMaterial* Material = LoadObject<UMaterial>(nullptr, *ObjectPath);
    UPackage* Package = Material ? Material->GetOutermost() : CreatePackage(*PackagePath);
    if (!Package)
    {
        return nullptr;
    }
    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package, *AssetName,
            RF_Public | RF_Standalone | RF_Transactional);
        if (Material)
        {
            FAssetRegistryModule::AssetCreated(Material);
        }
    }
    if (!Material)
    {
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    // Photo-derived cards need transmission from every guide-eye azimuth.
    // TwoSidedFoliage retains the masked source while providing relightable,
    // physically plausible leaf transmission without emissive compensation.
    Material->SetShadingModel(MSM_TwoSidedFoliage);
    Material->BlendMode = BLEND_Masked;
    Material->TwoSided = true;
    Material->DitheredLODTransition = true;
    // The V2 alpha mattes retain fine needles and alder twigs. A lower masked
    // cutoff preserves those source-authored silhouettes while the two-plane
    // topology keeps the additional overdraw bounded.
    Material->OpacityMaskClipValue = 0.20f;

    auto AddExpression = [Material](auto* Expression, int32 EditorX, int32 EditorY)
    {
        Expression->MaterialExpressionEditorX = EditorX;
        Expression->MaterialExpressionEditorY = EditorY;
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    UMaterialExpressionTextureSampleParameter2D* CanopySample = AddExpression(
        NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -520, -140);
    CanopySample->ParameterName = TEXT("CanopyAlbedoOpacity");
    CanopySample->Texture = AlbedoOpacity;
    CanopySample->SamplerType = SAMPLERTYPE_Color;
    UMaterialExpressionConstant* Roughness = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material), -260, 150);
    Roughness->R = 0.84f;
    UMaterialExpressionConstant* Specular = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material), -260, 240);
    Specular->R = 0.08f;
    UMaterialExpressionConstant* AmbientOcclusion = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material), -260, 330);
    AmbientOcclusion->R = 1.0f;
    UMaterialExpressionConstant3Vector* CanopyTint = AddExpression(
        NewObject<UMaterialExpressionConstant3Vector>(Material), -260, -230);
    // The source cutouts already carry bark and leaf albedo. Keep their
    // energy below the sunlit terrain and vary the retained spectrum by
    // species; near-white multipliers plus strong foliage transmission made
    // whole canyon stands read as a uniform beige wall at guide-eye exposure.
    // V2 sources use neutral scan lighting and need less destructive energy
    // compression than the first generated set.
    CanopyTint->Constant = SpeciesAssetName.Contains(TEXT("Ponderosa"))
        ? FLinearColor(0.82f, 0.86f, 0.74f, 1.0f)
        : SpeciesAssetName.Contains(TEXT("AtlasV2Review"))
            ? FLinearColor(0.82f, 0.87f, 0.72f, 1.0f)
        : SpeciesAssetName.Contains(TEXT("WhiteAlder"))
            ? FLinearColor(0.80f, 0.86f, 0.72f, 1.0f)
            : FLinearColor(0.70f, 0.78f, 0.62f, 1.0f);
    UMaterialExpressionMultiply* Fill = AddExpression(
        NewObject<UMaterialExpressionMultiply>(Material), 0, -200);
    Fill->A.Expression = CanopySample;
    Fill->B.Expression = CanopyTint;
    // Aerial masks resolve stand-scale cover, not identical individual-tree
    // radiometry. Deterministic HISM variation breaks the single-value wall
    // produced by repeated source profiles while keeping the mean energy near
    // the retained v95 calibration. The same bounded signal slightly changes
    // fine alpha-edge survival, but never removes source-authored trunks or
    // promotes a new silhouette, ecology claim, collision, or hydraulic input.
    UMaterialExpressionPerInstanceRandom* InstanceRandom = AddExpression(
        NewObject<UMaterialExpressionPerInstanceRandom>(Material), -260, -50);
    UMaterialExpressionConstant* EnergyMinimum = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material), -260, 20);
    EnergyMinimum->R = 0.88f;
    UMaterialExpressionConstant* EnergyMaximum = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material), -260, 80);
    EnergyMaximum->R = 1.14f;
    UMaterialExpressionLinearInterpolate* InstanceEnergy = AddExpression(
        NewObject<UMaterialExpressionLinearInterpolate>(Material), 0, -80);
    InstanceEnergy->A.Expression = EnergyMinimum;
    InstanceEnergy->B.Expression = EnergyMaximum;
    InstanceEnergy->Alpha.Expression = InstanceRandom;
    UMaterialExpressionMultiply* VariedFill = AddExpression(
        NewObject<UMaterialExpressionMultiply>(Material), 210, -200);
    VariedFill->A.Expression = Fill;
    VariedFill->B.Expression = InstanceEnergy;
    UMaterialExpressionConstant* OpacityMinimum = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material), -20, 75);
    OpacityMinimum->R = 0.92f;
    UMaterialExpressionConstant* OpacityMaximum = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material), -20, 135);
    OpacityMaximum->R = 1.10f;
    UMaterialExpressionLinearInterpolate* InstanceOpacity = AddExpression(
        NewObject<UMaterialExpressionLinearInterpolate>(Material), 210, 70);
    InstanceOpacity->A.Expression = OpacityMinimum;
    InstanceOpacity->B.Expression = OpacityMaximum;
    InstanceOpacity->Alpha.Expression = InstanceRandom;
    UMaterialExpressionMultiply* VariedOpacity = AddExpression(
        NewObject<UMaterialExpressionMultiply>(Material), 420, 65);
    VariedOpacity->A.Expression = CanopySample;
    VariedOpacity->A.OutputIndex = 4;
    VariedOpacity->B.Expression = InstanceOpacity;
    UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, VariedFill);
    UMaterialExpressionConstant3Vector* TransmissionTint = AddExpression(
        NewObject<UMaterialExpressionConstant3Vector>(Material), 0, 10);
    TransmissionTint->Constant = SpeciesAssetName.Contains(TEXT("Ponderosa"))
        ? FLinearColor(0.050f, 0.085f, 0.025f, 1.0f)
        : SpeciesAssetName.Contains(TEXT("WhiteAlder"))
            ? FLinearColor(0.070f, 0.115f, 0.035f, 1.0f)
            : FLinearColor(0.060f, 0.100f, 0.030f, 1.0f);
    ConnectPreviewMaterialColorInput(
        EditorOnlyData->SubsurfaceColor, TransmissionTint);
    EditorOnlyData->OpacityMask.Connect(/*OutputIndex=*/0, VariedOpacity);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, Roughness);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);
    ConnectPreviewMaterialScalarInput(
        EditorOnlyData->AmbientOcclusion, AmbientOcclusion);

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (!Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to enable HISM usage for canopy material %s.\n"),
            *ObjectPath);
        return nullptr;
    }
    Material->PostEditChange();
    Material->ForceRecompileForRendering();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
        GShaderCompilingManager->ProcessAsyncResults(false, true);
    }
    const FMaterialResource* Resource =
        Material->GetMaterialResource(GMaxRHIShaderPlatform);
    if (!Resource ||
        Material->IsCompilingOrHadCompileError(GMaxRHIShaderPlatform) ||
        !Resource->GetCompileErrors().IsEmpty())
    {
        OutSummary += FString::Printf(
            TEXT("Generated canopy material shader gate failed for %s.\n"),
            *ObjectPath);
        return nullptr;
    }
    Material->MarkPackageDirty();
    Package->MarkPackageDirty();
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
    {
        return nullptr;
    }
    OutSummary += FString::Printf(
        TEXT("Saved generated South Fork canopy material %s.\n"), *ObjectPath);
    return Material;
}

UMaterial* CreateSouthForkCanopyBranchMaterial(
    const FString& SpeciesAssetName,
    UTexture2D* AlbedoOpacity,
    UTexture2D* Normal,
    UTexture2D* Packed,
    const FLinearColor& TintColor,
    const FLinearColor& ScatterColor,
    FString& OutSummary,
    bool bCalibratedReviewLighting = false)
{
    if (!AlbedoOpacity || !Normal || !Packed)
    {
        return nullptr;
    }
    const FString PackagePath = FString::Printf(
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Materials/"
             "M_RaftSim_%s_BranchAtlasV1"),
        *SpeciesAssetName);
    const FString AssetName = FPackageName::GetLongPackageAssetName(PackagePath);
    const FString ObjectPath = FString::Printf(
        TEXT("%s.%s"), *PackagePath, *AssetName);
    UMaterial* Material = LoadObject<UMaterial>(nullptr, *ObjectPath);
    UPackage* Package = Material ? Material->GetOutermost() : CreatePackage(*PackagePath);
    if (!Package)
    {
        return nullptr;
    }
    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package, *AssetName, RF_Public | RF_Standalone | RF_Transactional);
        if (Material)
        {
            FAssetRegistryModule::AssetCreated(Material);
        }
    }
    if (!Material)
    {
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->SetShadingModel(MSM_TwoSidedFoliage);
    Material->BlendMode = BLEND_Masked;
    Material->TwoSided = true;
    Material->DitheredLODTransition = true;
    Material->OpacityMaskClipValue = bCalibratedReviewLighting ? 0.28f : 0.22f;
    auto AddExpression = [Material](auto* Expression, int32 EditorX, int32 EditorY)
    {
        Expression->MaterialExpressionEditorX = EditorX;
        Expression->MaterialExpressionEditorY = EditorY;
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    UMaterialExpressionTextureSampleParameter2D* AlbedoSample = AddExpression(
        NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -640, -220);
    AlbedoSample->ParameterName = TEXT("BranchAlbedoOpacity");
    AlbedoSample->Texture = AlbedoOpacity;
    AlbedoSample->SamplerType = SAMPLERTYPE_Color;
    UMaterialExpressionTextureSampleParameter2D* NormalSample = AddExpression(
        NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -640, 180);
    NormalSample->ParameterName = TEXT("BranchNormal");
    NormalSample->Texture = Normal;
    NormalSample->SamplerType = SAMPLERTYPE_Normal;
    UMaterialExpressionTextureSampleParameter2D* PackedSample = AddExpression(
        NewObject<UMaterialExpressionTextureSampleParameter2D>(Material), -640, 380);
    PackedSample->ParameterName = TEXT("BranchAORoughnessSubsurface");
    PackedSample->Texture = Packed;
    PackedSample->SamplerType = SAMPLERTYPE_Masks;

    UMaterialExpressionConstant3Vector* Tint = AddExpression(
        NewObject<UMaterialExpressionConstant3Vector>(Material), -380, -120);
    Tint->Constant = TintColor;
    UMaterialExpressionMultiply* TintedAlbedo = AddExpression(
        NewObject<UMaterialExpressionMultiply>(Material), -120, -200);
    TintedAlbedo->A.Expression = AlbedoSample;
    TintedAlbedo->B.Expression = Tint;
    UMaterialExpressionPerInstanceRandom* InstanceRandom = AddExpression(
        NewObject<UMaterialExpressionPerInstanceRandom>(Material), -380, 20);
    UMaterialExpressionConstant* EnergyMinimum = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material), -380, 80);
    EnergyMinimum->R = bCalibratedReviewLighting ? 0.98f : 0.88f;
    UMaterialExpressionConstant* EnergyMaximum = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material), -380, 140);
    EnergyMaximum->R = bCalibratedReviewLighting ? 1.14f : 1.10f;
    UMaterialExpressionLinearInterpolate* InstanceEnergy = AddExpression(
        NewObject<UMaterialExpressionLinearInterpolate>(Material), -120, -20);
    InstanceEnergy->A.Expression = EnergyMinimum;
    InstanceEnergy->B.Expression = EnergyMaximum;
    InstanceEnergy->Alpha.Expression = InstanceRandom;
    UMaterialExpressionMultiply* VariedAlbedo = AddExpression(
        NewObject<UMaterialExpressionMultiply>(Material), 120, -180);
    VariedAlbedo->A.Expression = TintedAlbedo;
    VariedAlbedo->B.Expression = InstanceEnergy;

    auto ChannelMask = [&](bool R, bool G, bool B, int32 EditorY)
    {
        UMaterialExpressionComponentMask* Mask = AddExpression(
            NewObject<UMaterialExpressionComponentMask>(Material), -300, EditorY);
        Mask->Input.Expression = PackedSample;
        Mask->R = R;
        Mask->G = G;
        Mask->B = B;
        return Mask;
    };
    UMaterialExpressionComponentMask* AmbientOcclusion =
        ChannelMask(true, false, false, 310);
    UMaterialExpressionComponentMask* Roughness =
        ChannelMask(false, true, false, 390);
    UMaterialExpressionComponentMask* Subsurface =
        ChannelMask(false, false, true, 470);
    UMaterialExpressionConstant3Vector* ScatterTint = AddExpression(
        NewObject<UMaterialExpressionConstant3Vector>(Material), -40, 520);
    ScatterTint->Constant = ScatterColor;
    UMaterialExpressionMultiply* Scatter = AddExpression(
        NewObject<UMaterialExpressionMultiply>(Material), 190, 450);
    Scatter->A.Expression = ScatterTint;
    Scatter->B.Expression = Subsurface;

    UMaterialExpression* CalibratedNormal = NormalSample;
    UMaterialExpression* CalibratedAmbientOcclusion = AmbientOcclusion;
    if (bCalibratedReviewLighting)
    {
        // Leaf-card tangents and baked crevice AO should add local structure,
        // not turn an entire repeated crown into a black clump.  Preserve a
        // majority of the authored normal while bounding AO at 0.62.  This is
        // still lit TwoSidedFoliage; no emissive or unlit compensation is used.
        UMaterialExpressionConstant3Vector* FlatTangentNormal = AddExpression(
            NewObject<UMaterialExpressionConstant3Vector>(Material), -40, 170);
        FlatTangentNormal->Constant = FLinearColor(0.0f, 0.0f, 1.0f, 1.0f);
        UMaterialExpressionConstant* NormalDetail = AddExpression(
            NewObject<UMaterialExpressionConstant>(Material), -40, 230);
        NormalDetail->R = 0.64f;
        UMaterialExpressionLinearInterpolate* FlattenedNormal = AddExpression(
            NewObject<UMaterialExpressionLinearInterpolate>(Material), 190, 190);
        FlattenedNormal->A.Expression = FlatTangentNormal;
        FlattenedNormal->B.Expression = NormalSample;
        FlattenedNormal->Alpha.Expression = NormalDetail;
        CalibratedNormal = FlattenedNormal;

        UMaterialExpressionConstant* AmbientOcclusionFloor = AddExpression(
            NewObject<UMaterialExpressionConstant>(Material), -40, 300);
        AmbientOcclusionFloor->R = 0.62f;
        UMaterialExpressionConstant* AmbientOcclusionCeiling = AddExpression(
            NewObject<UMaterialExpressionConstant>(Material), -40, 350);
        AmbientOcclusionCeiling->R = 1.0f;
        UMaterialExpressionLinearInterpolate* BoundedAmbientOcclusion = AddExpression(
            NewObject<UMaterialExpressionLinearInterpolate>(Material), 190, 320);
        BoundedAmbientOcclusion->A.Expression = AmbientOcclusionFloor;
        BoundedAmbientOcclusion->B.Expression = AmbientOcclusionCeiling;
        BoundedAmbientOcclusion->Alpha.Expression = AmbientOcclusion;
        CalibratedAmbientOcclusion = BoundedAmbientOcclusion;
    }

    UMaterialEditorOnlyData* EditorData = Material->GetEditorOnlyData();
    ConnectPreviewMaterialColorInput(EditorData->BaseColor, VariedAlbedo);
    EditorData->OpacityMask.Connect(/*OutputIndex=*/4, AlbedoSample);
    EditorData->Normal.Connect(/*OutputIndex=*/0, CalibratedNormal);
    ConnectPreviewMaterialScalarInput(EditorData->Roughness, Roughness);
    ConnectPreviewMaterialScalarInput(
        EditorData->AmbientOcclusion, CalibratedAmbientOcclusion);
    ConnectPreviewMaterialColorInput(EditorData->SubsurfaceColor, Scatter);

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (!Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to enable HISM usage for branch material %s.\n"),
            *ObjectPath);
        return nullptr;
    }
    Material->PostEditChange();
    Material->ForceRecompileForRendering();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
        GShaderCompilingManager->ProcessAsyncResults(false, true);
    }
    const FMaterialResource* Resource =
        Material->GetMaterialResource(GMaxRHIShaderPlatform);
    if (!Resource ||
        Material->IsCompilingOrHadCompileError(GMaxRHIShaderPlatform) ||
        !Resource->GetCompileErrors().IsEmpty())
    {
        OutSummary += FString::Printf(
            TEXT("Generated branch material shader gate failed for %s.\n"),
            *ObjectPath);
        return nullptr;
    }
    Material->MarkPackageDirty();
    Package->MarkPackageDirty();
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
    {
        return nullptr;
    }
    OutSummary += FString::Printf(
        TEXT("Saved generated South Fork branch material %s "
             "(calibrated_review_lighting=%d).\n"),
        *ObjectPath,
        bCalibratedReviewLighting ? 1 : 0);
    return Material;
}

UMaterial* CreateSouthForkIslandTreeFoliageMaterialV1Review(
    UTexture2D* Albedo,
    UTexture2D* Opacity,
    UTexture2D* Normal,
    UTexture2D* Roughness,
    FString& OutSummary)
{
    if (!Albedo || !Opacity || !Normal || !Roughness)
    {
        OutSummary += TEXT(
            "Island-tree foliage material review is missing a source texture.\n");
        return nullptr;
    }
    FAssetCompilingManager::Get().FinishAllCompilation();
    const UTexture2D* Textures[] = {Albedo, Opacity, Normal, Roughness};
    for (const UTexture2D* Texture : Textures)
    {
        const FTexturePlatformData* PlatformData = Texture->GetPlatformData();
        if (!PlatformData || PlatformData->SizeX != 1024 ||
            PlatformData->SizeY != 1024 || PlatformData->Mips.Num() < 10)
        {
            OutSummary += FString::Printf(
                TEXT("Island-tree foliage source %s failed the running-platform "
                     "1024-square / ten-mip gate.\n"),
                *Texture->GetPathName());
            return nullptr;
        }
    }

    const FString PackagePath =
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Materials/"
             "M_RaftSim_SouthForkInteriorLiveOakIslandTreeMaterialV1Review_Leaves");
    const FString AssetName = FPackageName::GetLongPackageAssetName(PackagePath);
    const FString ObjectPath = FString::Printf(
        TEXT("%s.%s"), *PackagePath, *AssetName);
    UMaterial* Material = LoadObject<UMaterial>(nullptr, *ObjectPath);
    UPackage* Package = Material
        ? Material->GetOutermost()
        : CreatePackage(*PackagePath);
    if (!Package)
    {
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
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->SetShadingModel(MSM_TwoSidedFoliage);
    Material->BlendMode = BLEND_Masked;
    Material->TwoSided = true;
    Material->DitheredLODTransition = true;
    Material->OpacityMaskClipValue = 0.30f;
    auto AddExpression = [Material](auto* Expression, int32 EditorX, int32 EditorY)
    {
        Expression->MaterialExpressionEditorX = EditorX;
        Expression->MaterialExpressionEditorY = EditorY;
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    auto TextureSample = [&](
        UTexture2D* Texture,
        FName ParameterName,
        EMaterialSamplerType SamplerType,
        int32 EditorY)
    {
        UMaterialExpressionTextureSampleParameter2D* Sample = AddExpression(
            NewObject<UMaterialExpressionTextureSampleParameter2D>(Material),
            -680, EditorY);
        Sample->ParameterName = ParameterName;
        Sample->Texture = Texture;
        Sample->SamplerType = SamplerType;
        return Sample;
    };
    UMaterialExpressionTextureSampleParameter2D* AlbedoSample = TextureSample(
        Albedo, TEXT("IslandTreeLeafAlbedo"), SAMPLERTYPE_Color, -260);
    UMaterialExpressionTextureSampleParameter2D* OpacitySample = TextureSample(
        Opacity, TEXT("IslandTreeLeafOpacity"), SAMPLERTYPE_Masks, -60);
    UMaterialExpressionTextureSampleParameter2D* NormalSample = TextureSample(
        Normal, TEXT("IslandTreeLeafNormal"), SAMPLERTYPE_Normal, 180);
    UMaterialExpressionTextureSampleParameter2D* RoughnessSample = TextureSample(
        Roughness, TEXT("IslandTreeLeafRoughness"), SAMPLERTYPE_Masks, 420);

    UMaterialExpressionConstant3Vector* ColorCalibration = AddExpression(
        NewObject<UMaterialExpressionConstant3Vector>(Material), -400, -300);
    ColorCalibration->Constant = FLinearColor(1.18f, 1.24f, 1.10f, 1.0f);
    UMaterialExpressionMultiply* CalibratedAlbedo = AddExpression(
        NewObject<UMaterialExpressionMultiply>(Material), -140, -240);
    CalibratedAlbedo->A.Expression = AlbedoSample;
    CalibratedAlbedo->B.Expression = ColorCalibration;
    UMaterialExpressionPerInstanceRandom* InstanceRandom = AddExpression(
        NewObject<UMaterialExpressionPerInstanceRandom>(Material), -400, -170);
    UMaterialExpressionConstant* EnergyMinimum = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material), -400, -120);
    EnergyMinimum->R = 1.00f;
    UMaterialExpressionConstant* EnergyMaximum = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material), -400, -70);
    EnergyMaximum->R = 1.12f;
    UMaterialExpressionLinearInterpolate* InstanceEnergy = AddExpression(
        NewObject<UMaterialExpressionLinearInterpolate>(Material), -140, -100);
    InstanceEnergy->A.Expression = EnergyMinimum;
    InstanceEnergy->B.Expression = EnergyMaximum;
    InstanceEnergy->Alpha.Expression = InstanceRandom;
    UMaterialExpressionMultiply* VariedAlbedo = AddExpression(
        NewObject<UMaterialExpressionMultiply>(Material), 100, -210);
    VariedAlbedo->A.Expression = CalibratedAlbedo;
    VariedAlbedo->B.Expression = InstanceEnergy;

    // Preserve leaf area through the 1K source's distant mips without using
    // emissive or unlit compensation. This is a shader-only review override;
    // the rights-reviewed source texture packages remain byte-identical.
    UMaterialExpressionConstant* OpacityCoverageScale = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material), -400, 10);
    OpacityCoverageScale->R = 2.0f;
    UMaterialExpressionMultiply* ScaledOpacity = AddExpression(
        NewObject<UMaterialExpressionMultiply>(Material), -140, 0);
    ScaledOpacity->A.Expression = OpacitySample;
    ScaledOpacity->B.Expression = OpacityCoverageScale;

    UMaterialExpressionConstant3Vector* FlatTangentNormal = AddExpression(
        NewObject<UMaterialExpressionConstant3Vector>(Material), -400, 180);
    FlatTangentNormal->Constant = FLinearColor(0.0f, 0.0f, 1.0f, 1.0f);
    UMaterialExpressionConstant* NormalDetail = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material), -400, 240);
    NormalDetail->R = 0.55f;
    UMaterialExpressionLinearInterpolate* CalibratedNormal = AddExpression(
        NewObject<UMaterialExpressionLinearInterpolate>(Material), -140, 200);
    CalibratedNormal->A.Expression = FlatTangentNormal;
    CalibratedNormal->B.Expression = NormalSample;
    CalibratedNormal->Alpha.Expression = NormalDetail;

    UMaterialExpressionConstant* RoughnessMinimum = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material), -400, 410);
    RoughnessMinimum->R = 0.45f;
    UMaterialExpressionConstant* RoughnessMaximum = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material), -400, 470);
    RoughnessMaximum->R = 0.85f;
    UMaterialExpressionLinearInterpolate* CalibratedRoughness = AddExpression(
        NewObject<UMaterialExpressionLinearInterpolate>(Material), -140, 430);
    CalibratedRoughness->A.Expression = RoughnessMinimum;
    CalibratedRoughness->B.Expression = RoughnessMaximum;
    CalibratedRoughness->Alpha.Expression = RoughnessSample;
    UMaterialExpressionConstant* AmbientOcclusion = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material), -140, 520);
    AmbientOcclusion->R = 0.78f;
    UMaterialExpressionConstant3Vector* Subsurface = AddExpression(
        NewObject<UMaterialExpressionConstant3Vector>(Material), 100, 360);
    Subsurface->Constant = FLinearColor(0.10f, 0.20f, 0.045f, 1.0f);

    UMaterialEditorOnlyData* EditorData = Material->GetEditorOnlyData();
    ConnectPreviewMaterialColorInput(EditorData->BaseColor, VariedAlbedo);
    ConnectPreviewMaterialScalarInput(EditorData->OpacityMask, ScaledOpacity);
    EditorData->Normal.Connect(/*OutputIndex=*/0, CalibratedNormal);
    ConnectPreviewMaterialScalarInput(
        EditorData->Roughness, CalibratedRoughness);
    ConnectPreviewMaterialScalarInput(
        EditorData->AmbientOcclusion, AmbientOcclusion);
    ConnectPreviewMaterialColorInput(EditorData->SubsurfaceColor, Subsurface);

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (!Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to enable HISM usage for island-tree review material %s.\n"),
            *ObjectPath);
        return nullptr;
    }
    Material->PostEditChange();
    Material->ForceRecompileForRendering();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
        GShaderCompilingManager->ProcessAsyncResults(false, true);
    }
    const FMaterialResource* Resource =
        Material->GetMaterialResource(GMaxRHIShaderPlatform);
    if (!Resource ||
        Material->IsCompilingOrHadCompileError(GMaxRHIShaderPlatform) ||
        !Resource->GetCompileErrors().IsEmpty())
    {
        OutSummary += FString::Printf(
            TEXT("Island-tree review material shader gate failed for %s.\n"),
            *ObjectPath);
        return nullptr;
    }
    Material->MarkPackageDirty();
    Package->MarkPackageDirty();
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
    {
        return nullptr;
    }
    OutSummary += FString::Printf(
        TEXT("Saved isolated island-tree foliage material review %s with "
             "opacity_coverage=2.00 clip=0.30 normal_detail=0.55 "
             "ao=0.78 roughness=0.45-0.85 and no emissive compensation.\n"),
        *ObjectPath);
    return Material;
}

UMaterial* CreateSouthForkCanopyBarkMaterial(
    const FString& SpeciesAssetName,
    const FSouthForkCanopyBarkTextureSet& Textures,
    FString& OutSummary)
{
    if (!Textures.IsComplete())
    {
        return nullptr;
    }
    const FString PackagePath = FString::Printf(
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Materials/"
             "M_RaftSim_%s_Bark"),
        *SpeciesAssetName);
    const FString AssetName = FPackageName::GetLongPackageAssetName(PackagePath);
    const FString ObjectPath = FString::Printf(
        TEXT("%s.%s"), *PackagePath, *AssetName);
    UMaterial* Material = LoadObject<UMaterial>(nullptr, *ObjectPath);
    UPackage* Package = Material
        ? Material->GetOutermost()
        : CreatePackage(*PackagePath);
    if (!Package)
    {
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
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->SetShadingModel(MSM_DefaultLit);
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = false;
    Material->DitheredLODTransition = true;
    auto AddExpression = [Material](auto* Expression, int32 EditorX, int32 EditorY)
    {
        Expression->MaterialExpressionEditorX = EditorX;
        Expression->MaterialExpressionEditorY = EditorY;
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    UMaterialExpressionTextureSampleParameter2D* AlbedoSample = AddExpression(
        NewObject<UMaterialExpressionTextureSampleParameter2D>(Material),
        -620,
        -220);
    AlbedoSample->ParameterName = TEXT("BarkAlbedo");
    AlbedoSample->Texture = Textures.Albedo;
    AlbedoSample->SamplerType = SAMPLERTYPE_Color;
    UMaterialExpressionTextureSampleParameter2D* NormalSample = AddExpression(
        NewObject<UMaterialExpressionTextureSampleParameter2D>(Material),
        -620,
        120);
    NormalSample->ParameterName = TEXT("BarkNormal");
    NormalSample->Texture = Textures.Normal;
    NormalSample->SamplerType = SAMPLERTYPE_Normal;
    UMaterialExpressionTextureSampleParameter2D* PackedSample = AddExpression(
        NewObject<UMaterialExpressionTextureSampleParameter2D>(Material),
        -620,
        340);
    PackedSample->ParameterName = TEXT("BarkAORoughnessHeight");
    PackedSample->Texture = Textures.Packed;
    PackedSample->SamplerType = SAMPLERTYPE_Masks;

    UMaterialExpressionConstant3Vector* BarkTint = AddExpression(
        NewObject<UMaterialExpressionConstant3Vector>(Material),
        -360,
        -120);
    BarkTint->Constant = FLinearColor(0.86f, 0.84f, 0.78f, 1.0f);
    UMaterialExpressionMultiply* TintedAlbedo = AddExpression(
        NewObject<UMaterialExpressionMultiply>(Material),
        -120,
        -180);
    TintedAlbedo->A.Expression = AlbedoSample;
    TintedAlbedo->B.Expression = BarkTint;
    UMaterialExpressionPerInstanceRandom* InstanceRandom = AddExpression(
        NewObject<UMaterialExpressionPerInstanceRandom>(Material),
        -360,
        10);
    UMaterialExpressionConstant* EnergyMinimum = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material),
        -360,
        70);
    EnergyMinimum->R = 0.90f;
    UMaterialExpressionConstant* EnergyMaximum = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material),
        -360,
        130);
    EnergyMaximum->R = 1.06f;
    UMaterialExpressionLinearInterpolate* InstanceEnergy = AddExpression(
        NewObject<UMaterialExpressionLinearInterpolate>(Material),
        -110,
        0);
    InstanceEnergy->A.Expression = EnergyMinimum;
    InstanceEnergy->B.Expression = EnergyMaximum;
    InstanceEnergy->Alpha.Expression = InstanceRandom;
    UMaterialExpressionMultiply* VariedAlbedo = AddExpression(
        NewObject<UMaterialExpressionMultiply>(Material),
        130,
        -170);
    VariedAlbedo->A.Expression = TintedAlbedo;
    VariedAlbedo->B.Expression = InstanceEnergy;

    auto ChannelMask = [&](bool R, bool G, bool B, int32 EditorY)
    {
        UMaterialExpressionComponentMask* Mask = AddExpression(
            NewObject<UMaterialExpressionComponentMask>(Material),
            -300,
            EditorY);
        Mask->Input.Expression = PackedSample;
        Mask->R = R;
        Mask->G = G;
        Mask->B = B;
        return Mask;
    };
    UMaterialExpressionComponentMask* AmbientOcclusion =
        ChannelMask(true, false, false, 300);
    UMaterialExpressionComponentMask* Roughness =
        ChannelMask(false, true, false, 390);
    UMaterialExpressionConstant* Specular = AddExpression(
        NewObject<UMaterialExpressionConstant>(Material),
        -30,
        480);
    Specular->R = 0.10f;

    UMaterialEditorOnlyData* EditorData = Material->GetEditorOnlyData();
    ConnectPreviewMaterialColorInput(EditorData->BaseColor, VariedAlbedo);
    EditorData->Normal.Connect(/*OutputIndex=*/0, NormalSample);
    ConnectPreviewMaterialScalarInput(EditorData->Roughness, Roughness);
    ConnectPreviewMaterialScalarInput(
        EditorData->AmbientOcclusion, AmbientOcclusion);
    ConnectPreviewMaterialScalarInput(EditorData->Specular, Specular);

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (!Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to enable HISM usage for bark material %s.\n"),
            *ObjectPath);
        return nullptr;
    }
    Material->PostEditChange();
    Material->ForceRecompileForRendering();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (GShaderCompilingManager)
    {
        GShaderCompilingManager->FinishAllCompilation();
        GShaderCompilingManager->ProcessAsyncResults(false, true);
    }
    const FMaterialResource* Resource =
        Material->GetMaterialResource(GMaxRHIShaderPlatform);
    if (!Resource ||
        Material->IsCompilingOrHadCompileError(GMaxRHIShaderPlatform) ||
        !Resource->GetCompileErrors().IsEmpty())
    {
        OutSummary += FString::Printf(
            TEXT("Generated bark material shader gate failed for %s.\n"),
            *ObjectPath);
        return nullptr;
    }
    Material->MarkPackageDirty();
    Package->MarkPackageDirty();
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
    {
        return nullptr;
    }
    OutSummary += FString::Printf(
        TEXT("Saved generated South Fork bark material %s.\n"),
        *ObjectPath);
    return Material;
}

UStaticMesh* CreateSouthForkCanopyRadialCardMesh(
    UWorld* World,
    const FString& SpeciesAssetName,
    float WidthCm,
    float HeightCm,
    UMaterialInterface* Material,
    FString& OutSummary)
{
    if (!World || !Material || WidthCm <= 0.0f || HeightCm <= 0.0f)
    {
        return nullptr;
    }
    const float HalfWidthCm = WidthCm * 0.5f;
    constexpr int32 PlaneCount = 2;
    TArray<FVector> Vertices;
    TArray<int32> Triangles;
    TArray<FVector> Normals;
    TArray<FVector2D> Uvs;
    TArray<FLinearColor> VertexColors;
    TArray<FProcMeshTangent> Tangents;
    Vertices.Reserve(PlaneCount * 4);
    Triangles.Reserve(PlaneCount * 6);
    Normals.Reserve(PlaneCount * 4);
    Uvs.Reserve(PlaneCount * 4);
    VertexColors.Reserve(PlaneCount * 4);
    Tangents.Reserve(PlaneCount * 4);
    // A two-plane orthogonal cross keeps a complete native-species silhouette
    // from every guide-eye azimuth without superimposing three identical
    // source trunks through each crown. Instance yaw variation supplies the
    // unresolved stand-scale orientation diversity.
    for (int32 PlaneIndex = 0; PlaneIndex < PlaneCount; ++PlaneIndex)
    {
        const float AngleRadians = FMath::DegreesToRadians(
            90.0f * static_cast<float>(PlaneIndex));
        const FVector WidthAxis(
            FMath::Cos(AngleRadians), FMath::Sin(AngleRadians), 0.0f);
        const FVector PlaneNormal(
            -FMath::Sin(AngleRadians), FMath::Cos(AngleRadians), 0.0f);
        const int32 BaseVertex = Vertices.Num();
        Vertices.Add(-WidthAxis * HalfWidthCm);
        Vertices.Add(WidthAxis * HalfWidthCm);
        Vertices.Add(-WidthAxis * HalfWidthCm + FVector::UpVector * HeightCm);
        Vertices.Add(WidthAxis * HalfWidthCm + FVector::UpVector * HeightCm);
        Triangles.Append({
            BaseVertex + 0, BaseVertex + 2, BaseVertex + 1,
            BaseVertex + 1, BaseVertex + 2, BaseVertex + 3});
        for (int32 VertexIndex = 0; VertexIndex < 4; ++VertexIndex)
        {
            Normals.Add(PlaneNormal);
            VertexColors.Add(FLinearColor::White);
            Tangents.Add(FProcMeshTangent(WidthAxis, false));
        }
        Uvs.Append({
            FVector2D(0.0f, 1.0f), FVector2D(1.0f, 1.0f),
            FVector2D(0.0f, 0.0f), FVector2D(1.0f, 0.0f)});
    }

    const FString PackagePath = FString::Printf(TEXT(
        "/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
        "SM_RaftSim_%s_Billboard"), *SpeciesAssetName);
    AActor* TemporaryActor = World->SpawnActor<AActor>(
        AActor::StaticClass(), FTransform::Identity);
    if (!TemporaryActor)
    {
        return nullptr;
    }
    TemporaryActor->SetActorLabel(SpeciesAssetName + TEXT("_Billboard_BuildSource"));
    USceneComponent* Root = NewObject<USceneComponent>(TemporaryActor, TEXT("Root"));
    TemporaryActor->AddInstanceComponent(Root);
    Root->RegisterComponent();
    TemporaryActor->SetRootComponent(Root);
    UProceduralMeshComponent* Procedural =
        NewObject<UProceduralMeshComponent>(TemporaryActor, TEXT("SourceMesh"));
    TemporaryActor->AddInstanceComponent(Procedural);
    Procedural->SetupAttachment(Root);
    Procedural->RegisterComponent();
    Procedural->CreateMeshSection_LinearColor(
        0, Vertices, Triangles, Normals, Uvs, VertexColors, Tangents,
        /*bCreateCollision=*/false);
    Procedural->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Procedural->SetMaterial(0, Material);
    UStaticMesh* Mesh = ConvertNativeCanopyProceduralActorToStaticMesh(
        TemporaryActor, PackagePath, Material,
        /*bEnableNanite=*/false,
        ENaniteShapePreservation::None,
        OutSummary);
    TemporaryActor->Destroy();
    return Mesh;
}

void AppendSouthForkCanopyUvPatchCard(
    const FVector& Center,
    const FVector& Right,
    float WidthCm,
    float HeightCm,
    const FVector2D& UvMinimum,
    const FVector2D& UvMaximum,
    TArray<FVector>& Vertices,
    TArray<int32>& Triangles,
    TArray<FVector>& Normals,
    TArray<FVector2D>& Uvs)
{
    const FVector SafeRight = Right.GetSafeNormal();
    const FVector Up = FVector::UpVector;
    const FVector Normal = FVector::CrossProduct(SafeRight, Up).GetSafeNormal();
    const FVector HalfRight = SafeRight * (0.5f * WidthCm);
    const FVector HalfUp = Up * (0.5f * HeightCm);
    const int32 BaseVertex = Vertices.Num();
    Vertices.Append({
        Center - HalfRight - HalfUp,
        Center + HalfRight - HalfUp,
        Center - HalfRight + HalfUp,
        Center + HalfRight + HalfUp});
    Triangles.Append({
        BaseVertex + 0, BaseVertex + 2, BaseVertex + 1,
        BaseVertex + 1, BaseVertex + 2, BaseVertex + 3});
    Normals.Append({Normal, Normal, Normal, Normal});
    Uvs.Append({
        FVector2D(UvMinimum.X, UvMaximum.Y),
        FVector2D(UvMaximum.X, UvMaximum.Y),
        FVector2D(UvMinimum.X, UvMinimum.Y),
        FVector2D(UvMaximum.X, UvMinimum.Y)});
}

enum class ESouthForkConnectedCrownForm : uint8
{
    Ponderosa,
    BroadTree,
    Shrub,
};

UStaticMesh* CreateSouthForkConnectedCrownMesh(
    UWorld* World,
    const FString& SpeciesAssetName,
    float WidthCm,
    float HeightCm,
    ESouthForkConnectedCrownForm CrownForm,
    UMaterialInterface* CoreMaterial,
    UMaterialInterface* BranchMaterial,
    FString& OutSummary)
{
    if (!World || !CoreMaterial || !BranchMaterial ||
        WidthCm <= 0.0f || HeightCm <= 0.0f)
    {
        return nullptr;
    }

    TArray<FVector> CoreVertices;
    TArray<int32> CoreTriangles;
    TArray<FVector> CoreNormals;
    TArray<FVector2D> CoreUvs;
    const float HalfWidthCm = WidthCm * 0.5f;
    // Pine and low shrub fallbacks keep the restrained two-plane silhouette
    // accepted in v140.  At guide distance those same crossed full-tree
    // profiles make live oak and alder read as dark cardboard cut-outs, so the
    // broad-tree candidate retains only one coherent source profile and lets a
    // denser, smaller branch-spray volume supply the other viewing azimuths.
    const bool bVolumetricBroadCrown =
        CrownForm == ESouthForkConnectedCrownForm::BroadTree;
    const bool bExpandedLiveOakAtlasReview =
        SpeciesAssetName.Contains(TEXT("AtlasV2Review"));
    const int32 CorePlaneCount = bVolumetricBroadCrown ? 1 : 2;
    for (int32 PlaneIndex = 0; PlaneIndex < CorePlaneCount; ++PlaneIndex)
    {
        const float Angle = FMath::DegreesToRadians(90.0f * PlaneIndex);
        const FVector Right(FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
        const FVector Normal(-Right.Y, Right.X, 0.0f);
        const int32 BaseVertex = CoreVertices.Num();
        CoreVertices.Append({
            -Right * HalfWidthCm,
            Right * HalfWidthCm,
            -Right * HalfWidthCm + FVector::UpVector * HeightCm,
            Right * HalfWidthCm + FVector::UpVector * HeightCm});
        CoreTriangles.Append({
            BaseVertex + 0, BaseVertex + 2, BaseVertex + 1,
            BaseVertex + 1, BaseVertex + 2, BaseVertex + 3});
        CoreNormals.Append({Normal, Normal, Normal, Normal});
        CoreUvs.Append({
            FVector2D(0.0f, 1.0f), FVector2D(1.0f, 1.0f),
            FVector2D(0.0f, 0.0f), FVector2D(1.0f, 0.0f)});
    }

    // The full-profile core preserves the reviewed silhouette and trunk while
    // source-separated branch sprays add bounded azimuthal depth. Every spray
    // uses one occupied cell from a project-owned 4x4 atlas. Broad trees use
    // three atlas cycles of smaller sprays around the single profile; unlike
    // v124-v126, no independently rotated full-tree fragments are introduced.
    TArray<FVector> BranchVertices;
    TArray<int32> BranchTriangles;
    TArray<FVector> BranchNormals;
    TArray<FVector2D> BranchUvs;
    constexpr int32 StandardBranchCardCount = 12;
    constexpr int32 VolumetricBroadBranchCardCount = 36;
    constexpr int32 ExpandedReviewBranchCardCount = 48;
    const int32 BranchCardCount = bExpandedLiveOakAtlasReview
        ? ExpandedReviewBranchCardCount
        : (bVolumetricBroadCrown
            ? VolumetricBroadBranchCardCount
            : StandardBranchCardCount);
    constexpr float AtlasInset = 0.018f;
    for (int32 CardIndex = 0; CardIndex < BranchCardCount; ++CardIndex)
    {
        const int32 LayerCount = bVolumetricBroadCrown ? 6 : 4;
        const int32 LayerIndex = bVolumetricBroadCrown
            ? (CardIndex * 5) % LayerCount
            : CardIndex % LayerCount;
        const int32 TileIndex = CardIndex % 12;
        const int32 TileX = TileIndex % 4;
        const int32 TileY = TileIndex / 4;
        const float Angle = FMath::DegreesToRadians(
            FMath::Fmod(CardIndex * 137.50776f + LayerIndex * 23.0f, 360.0f));
        const float RadialMinimum = CrownForm == ESouthForkConnectedCrownForm::Ponderosa
            ? 0.16f
            : (bExpandedLiveOakAtlasReview
                ? 0.14f
                : (bVolumetricBroadCrown ? 0.10f : 0.26f));
        const float RadialStep = CrownForm == ESouthForkConnectedCrownForm::Shrub
            ? 0.12f
            : (bExpandedLiveOakAtlasReview
                ? 0.11f
                : (bVolumetricBroadCrown ? 0.095f : 0.11f));
        const float RadialT = RadialMinimum + RadialStep *
            static_cast<float>((CardIndex * 7) % (bVolumetricBroadCrown ? 6 : 5));
        const float Radius = HalfWidthCm * RadialT;
        const float BaseHeightT = CrownForm == ESouthForkConnectedCrownForm::Ponderosa
            ? 0.43f
            : (bVolumetricBroadCrown ? 0.21f : 0.28f);
        const float LayerHeightStep = CrownForm == ESouthForkConnectedCrownForm::Ponderosa
            ? 0.15f
            : (bVolumetricBroadCrown ? 0.125f : 0.17f);
        const float HeightT = FMath::Clamp(
            BaseHeightT + LayerHeightStep * LayerIndex +
                0.045f * FMath::Sin(CardIndex * 1.71f),
            0.24f,
            CrownForm == ESouthForkConnectedCrownForm::Ponderosa ? 0.94f : 0.88f);
        const FVector Center(
            FMath::Cos(Angle) * Radius,
            FMath::Sin(Angle) * Radius,
            HeightCm * HeightT);
        const float CardYaw = Angle + FMath::DegreesToRadians(
            54.0f + 19.0f * static_cast<float>(CardIndex % 3));
        const FVector Right(
            FMath::Cos(CardYaw), FMath::Sin(CardYaw), 0.0f);
        const float MinimumCardWidthT =
            CrownForm == ESouthForkConnectedCrownForm::Ponderosa
                ? 0.28f
                : (bExpandedLiveOakAtlasReview
                    ? 0.22f
                    : (bVolumetricBroadCrown ? 0.16f : 0.25f));
        const float MaximumCardWidthT =
            CrownForm == ESouthForkConnectedCrownForm::Shrub
                ? 0.44f
                : (bExpandedLiveOakAtlasReview
                    ? 0.38f
                    : (bVolumetricBroadCrown ? 0.29f : 0.39f));
        const float CardWidth = FMath::Lerp(
            WidthCm * MinimumCardWidthT,
            WidthCm * MaximumCardWidthT,
            static_cast<float>((CardIndex * 11) % 7) / 6.0f);
        const float MinimumCardHeightT =
            CrownForm == ESouthForkConnectedCrownForm::Ponderosa
                ? 0.16f
                : (bExpandedLiveOakAtlasReview
                    ? 0.18f
                    : (bVolumetricBroadCrown ? 0.14f : 0.22f));
        const float MaximumCardHeightT =
            CrownForm == ESouthForkConnectedCrownForm::Shrub
                ? 0.44f
                : (bExpandedLiveOakAtlasReview
                    ? 0.34f
                    : (bVolumetricBroadCrown ? 0.27f : 0.34f));
        const float CardHeight = FMath::Lerp(
            HeightCm * MinimumCardHeightT,
            HeightCm * MaximumCardHeightT,
            static_cast<float>((CardIndex * 5) % 9) / 8.0f);
        const FVector2D UvMinimum(
            (TileX + AtlasInset) * 0.25f,
            (TileY + AtlasInset) * 0.25f);
        const FVector2D UvMaximum(
            (TileX + 1.0f - AtlasInset) * 0.25f,
            (TileY + 1.0f - AtlasInset) * 0.25f);
        AppendSouthForkCanopyUvPatchCard(
            Center, Right, CardWidth, CardHeight,
            UvMinimum, UvMaximum,
            BranchVertices, BranchTriangles, BranchNormals, BranchUvs);
    }

    const TCHAR* CrownVersion = bVolumetricBroadCrown
        ? TEXT("ConnectedCrownV2")
        : TEXT("ConnectedCrownV1");
    const FString PackagePath = FString::Printf(
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
             "SM_RaftSim_%s_%s"),
        *SpeciesAssetName, CrownVersion);
    AActor* TemporaryActor = AddPreviewTwoSectionProceduralMeshActor(
        World,
        SpeciesAssetName + TEXT("_") + CrownVersion + TEXT("_BuildSource"),
        CoreVertices,
        CoreTriangles,
        CoreNormals,
        CoreUvs,
        CoreMaterial,
        BranchVertices,
        BranchTriangles,
        BranchNormals,
        BranchUvs,
        BranchMaterial);
    UStaticMesh* Mesh = ConvertNativeCanopyProceduralActorToStaticMesh(
        TemporaryActor,
        *PackagePath,
        BranchMaterial,
        /*bEnableNanite=*/false,
        ENaniteShapePreservation::None,
        OutSummary);
    if (TemporaryActor)
    {
        TemporaryActor->Destroy();
    }
    if (Mesh)
    {
        OutSummary += FString::Printf(
            TEXT("Created South Fork %s connected crown: "
                 "crown_version=%s core_planes=%d core_triangles=%d "
                 "branch_cards=%d branch_triangles=%d "
                 "total_triangles=%d materials=%d.\n"),
            *SpeciesAssetName,
            CrownVersion,
            CorePlaneCount,
            CoreTriangles.Num() / 3,
            BranchCardCount,
            BranchTriangles.Num() / 3,
            (CoreTriangles.Num() + BranchTriangles.Num()) / 3,
            Mesh->GetStaticMaterials().Num());
    }
    return Mesh;
}

bool ConfigureSouthForkLiveOakReviewLods(
    UStaticMesh* Mesh,
    FString& OutSummary)
{
    if (!Mesh)
    {
        return false;
    }

    Mesh->Modify();
    Mesh->SetNumSourceModels(3);
    Mesh->SetAutoComputeLODScreenSize(false);
    Mesh->GetSourceModel(0).ScreenSize.Default = 1.0f;
    struct FReductionTarget
    {
        float ScreenSize;
        float PercentTriangles;
    };
    const FReductionTarget Targets[] = {
        {/*ScreenSize=*/0.34f, /*PercentTriangles=*/0.58f},
        {/*ScreenSize=*/0.12f, /*PercentTriangles=*/0.32f}};
    for (int32 TargetIndex = 0; TargetIndex < UE_ARRAY_COUNT(Targets); ++TargetIndex)
    {
        FStaticMeshSourceModel& SourceModel =
            Mesh->GetSourceModel(TargetIndex + 1);
        SourceModel.ScreenSize.Default = Targets[TargetIndex].ScreenSize;
        SourceModel.ReductionSettings.BaseLODModel = 0;
        SourceModel.ReductionSettings.TerminationCriterion =
            EStaticMeshReductionTerimationCriterion::Triangles;
        SourceModel.ReductionSettings.PercentTriangles =
            Targets[TargetIndex].PercentTriangles;
        SourceModel.ReductionSettings.PercentVertices = 1.0f;
        SourceModel.ReductionSettings.SilhouetteImportance =
            EMeshFeatureImportance::Highest;
        SourceModel.ReductionSettings.TextureImportance =
            EMeshFeatureImportance::High;
        SourceModel.ReductionSettings.ShadingImportance =
            EMeshFeatureImportance::High;
        SourceModel.ReductionSettings.bRecalculateNormals = false;
    }

    Mesh->Build(false);
    Mesh->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    const FStaticMeshRenderData* RenderData = Mesh->GetRenderData();
    if (!RenderData || RenderData->LODResources.Num() != 3)
    {
        OutSummary += FString::Printf(
            TEXT("Live-oak review LOD build failed for %s: expected 3 "
                 "render LODs.\n"),
            *Mesh->GetPathName());
        return false;
    }
    const int32 Lod0Triangles = RenderData->LODResources[0].GetNumTriangles();
    const int32 Lod1Triangles = RenderData->LODResources[1].GetNumTriangles();
    const int32 Lod2Triangles = RenderData->LODResources[2].GetNumTriangles();
    if (Lod0Triangles <= 0 || Lod1Triangles <= 0 || Lod2Triangles <= 0 ||
        Lod1Triangles >= Lod0Triangles || Lod2Triangles >= Lod1Triangles)
    {
        OutSummary += FString::Printf(
            TEXT("Live-oak review LOD triangle gate failed for %s: "
                 "lod0=%d lod1=%d lod2=%d.\n"),
            *Mesh->GetPathName(), Lod0Triangles, Lod1Triangles, Lod2Triangles);
        return false;
    }

    Mesh->MarkPackageDirty();
    Mesh->GetOutermost()->MarkPackageDirty();
    const FString Filename = FPackageName::LongPackageNameToFilename(
        Mesh->GetOutermost()->GetName(),
        FPackageName::GetAssetPackageExtension());
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(
            Mesh->GetOutermost(), Mesh, *Filename, SaveArgs))
    {
        OutSummary += FString::Printf(
            TEXT("Failed to save live-oak review LODs for %s.\n"),
            *Mesh->GetPathName());
        return false;
    }
    OutSummary += FString::Printf(
        TEXT("Authored deterministic live-oak near/mid/far LODs for %s: "
             "screen_sizes=1.00/0.34/0.12 triangles=%d/%d/%d "
             "dithered_transition=1.\n"),
        *Mesh->GetPathName(), Lod0Triangles, Lod1Triangles, Lod2Triangles);
    return true;
}

UStaticMesh* CreateSouthForkLiveOakWoodyCanopyMesh(
    UWorld* World,
    UMaterialInterface* BarkMaterial,
    UMaterialInterface* LeafMaterial,
    const FString& VariantToken,
    int32 LeafAtlasTileCount,
    float LeafCardScale,
    FString& OutSummary,
    int32 MorphologySeedSalt = 0,
    int32 ScaffoldCount = 5,
    float CrownWidthScale = 1.0f,
    float CrownHeightScale = 1.0f,
    float DirectionalAsymmetry = 0.0f,
    const TCHAR* FormToken = TEXT("OpenGrownMature"),
    bool bGenerateReductionLods = false)
{
    if (!World || !BarkMaterial || !LeafMaterial || VariantToken.IsEmpty() ||
        LeafAtlasTileCount <= 0 || LeafCardScale <= 0.0f ||
        ScaffoldCount < 3 || CrownWidthScale <= 0.0f ||
        CrownHeightScale <= 0.0f || !FormToken || FormToken[0] == '\0')
    {
        return nullptr;
    }

    const float CrownWidthCm = 1250.0f * CrownWidthScale;
    const float TreeHeightCm = 920.0f * CrownHeightScale;
    TArray<FVector> BarkVertices;
    TArray<int32> BarkTriangles;
    TArray<FVector> BarkNormals;
    TArray<FVector2D> BarkUvs;
    TArray<FVector> LeafVertices;
    TArray<int32> LeafTriangles;
    TArray<FVector> LeafNormals;
    TArray<FVector2D> LeafUvs;
    struct FTerminalBranch
    {
        FVector Start = FVector::ZeroVector;
        FVector End = FVector::ZeroVector;
        int32 Seed = 0;
    };
    TArray<FTerminalBranch> TerminalBranches;

    auto Noise01 = [MorphologySeedSalt](int32 Seed)
    {
        const float Value = FMath::Sin(
            static_cast<float>(Seed + MorphologySeedSalt * 4099 + 911) *
                12.9898f + 0.431f) *
            43758.5453f;
        return FMath::Abs(FMath::Frac(Value));
    };

    const FVector LowerTrunkEnd(
        FMath::Lerp(-9.0f, 9.0f, Noise01(2)),
        FMath::Lerp(-7.0f, 7.0f, Noise01(3)),
        TreeHeightCm * FMath::Lerp(0.17f, 0.21f, Noise01(5)));
    const FVector ForkCenter(
        FMath::Lerp(-14.0f, 14.0f, Noise01(7)),
        FMath::Lerp(-13.0f, 13.0f, Noise01(11)),
        TreeHeightCm * FMath::Lerp(0.29f, 0.34f, Noise01(13)));
    AppendNativeCanopyTaperedSegment(
        FVector::ZeroVector,
        LowerTrunkEnd,
        36.0f,
        27.0f,
        12,
        BarkVertices,
        BarkTriangles,
        BarkNormals,
        BarkUvs);
    AppendNativeCanopyTaperedSegment(
        LowerTrunkEnd,
        ForkCenter,
        27.0f,
        19.0f,
        11,
        BarkVertices,
        BarkTriangles,
        BarkNormals,
        BarkUvs);

    constexpr int32 SecondaryCount = 3;
    constexpr int32 TerminalCountPerSecondary = 3;
    const float BiasAzimuth = FMath::DegreesToRadians(
        FMath::Fmod(31.0f + MorphologySeedSalt * 53.0f, 360.0f));
    const FVector CrownBiasDirection(
        FMath::Cos(BiasAzimuth), FMath::Sin(BiasAzimuth), 0.0f);
    for (int32 ScaffoldIndex = 0;
         ScaffoldIndex < ScaffoldCount;
         ++ScaffoldIndex)
    {
        const float Azimuth = FMath::DegreesToRadians(
            FMath::Fmod(
                19.0f + MorphologySeedSalt * 47.0f +
                    ScaffoldIndex * 137.50776f,
                360.0f));
        const FVector Horizontal(
            FMath::Cos(Azimuth), FMath::Sin(Azimuth), 0.0f);
        const FVector Side(-Horizontal.Y, Horizontal.X, 0.0f);
        const float ScaffoldNoise = Noise01(ScaffoldIndex * 31 + 5);
        const float BiasProjection = FVector::DotProduct(
            Horizontal, CrownBiasDirection);
        const float NormalizedScaffoldIndex = ScaffoldCount > 1
            ? static_cast<float>(ScaffoldIndex) /
                static_cast<float>(ScaffoldCount - 1)
            : 0.0f;
        const FVector Start = FMath::Lerp(
            LowerTrunkEnd,
            ForkCenter,
            0.18f + 0.62f * NormalizedScaffoldIndex);
        const float PrimaryLength = CrownWidthCm * FMath::Lerp(
            0.27f, 0.36f, ScaffoldNoise) *
            FMath::Max(0.68f, 1.0f + DirectionalAsymmetry * BiasProjection);
        const FVector Mid = Start + Horizontal * PrimaryLength * 0.47f +
            Side * FMath::Lerp(
                -46.0f, 46.0f, Noise01(ScaffoldIndex * 37 + 7)) +
            FVector::UpVector * TreeHeightCm *
                FMath::Lerp(0.09f, 0.16f, Noise01(ScaffoldIndex * 41 + 11));
        const FVector End = Start + Horizontal * PrimaryLength +
            Side * FMath::Lerp(
                -82.0f, 82.0f, Noise01(ScaffoldIndex * 43 + 13)) +
            FVector::UpVector * TreeHeightCm *
                FMath::Lerp(0.22f, 0.34f, Noise01(ScaffoldIndex * 47 + 17)) +
            CrownBiasDirection * CrownWidthCm *
                DirectionalAsymmetry * 0.055f;
        AppendNativeCanopyTaperedSegment(
            Start,
            Mid,
            19.0f,
            11.0f,
            10,
            BarkVertices,
            BarkTriangles,
            BarkNormals,
            BarkUvs);
        AppendNativeCanopyTaperedSegment(
            Mid,
            End,
            11.0f,
            5.2f,
            9,
            BarkVertices,
            BarkTriangles,
            BarkNormals,
            BarkUvs);

        for (int32 SecondaryIndex = 0;
             SecondaryIndex < SecondaryCount;
             ++SecondaryIndex)
        {
            const float AlongPrimary = 0.38f + 0.25f * SecondaryIndex;
            const FVector SecondaryStart = FMath::Lerp(
                Mid, End, AlongPrimary);
            const float SecondaryOffsetDegrees =
                -47.0f + 48.0f * SecondaryIndex +
                FMath::Lerp(
                    -12.0f,
                    12.0f,
                    Noise01(ScaffoldIndex * 101 + SecondaryIndex * 17));
            const float SecondaryAzimuth = Azimuth +
                FMath::DegreesToRadians(SecondaryOffsetDegrees);
            const FVector SecondaryHorizontal(
                FMath::Cos(SecondaryAzimuth),
                FMath::Sin(SecondaryAzimuth),
                0.0f);
            const float SecondaryLength = CrownWidthCm * FMath::Lerp(
                0.11f,
                0.17f,
                Noise01(ScaffoldIndex * 109 + SecondaryIndex * 23));
            const FVector SecondaryEnd = SecondaryStart +
                SecondaryHorizontal * SecondaryLength +
                FVector::UpVector * SecondaryLength * FMath::Lerp(
                    0.36f,
                    0.68f,
                    Noise01(ScaffoldIndex * 113 + SecondaryIndex * 29));
            AppendNativeCanopyTaperedSegment(
                SecondaryStart,
                SecondaryEnd,
                5.6f,
                2.4f,
                8,
                BarkVertices,
                BarkTriangles,
                BarkNormals,
                BarkUvs);

            for (int32 TerminalIndex = 0;
                 TerminalIndex < TerminalCountPerSecondary;
                 ++TerminalIndex)
            {
                const int32 Seed = MorphologySeedSalt * 10000 +
                    ScaffoldIndex * 1000 +
                    SecondaryIndex * 100 + TerminalIndex * 11;
                const FVector TerminalStart = FMath::Lerp(
                    SecondaryStart,
                    SecondaryEnd,
                    0.42f + 0.24f * TerminalIndex);
                const float TerminalAzimuth = SecondaryAzimuth +
                    FMath::DegreesToRadians(
                        -31.0f + TerminalIndex * 34.0f +
                        FMath::Lerp(-9.0f, 9.0f, Noise01(Seed + 3)));
                const FVector TerminalHorizontal(
                    FMath::Cos(TerminalAzimuth),
                    FMath::Sin(TerminalAzimuth),
                    0.0f);
                const float TerminalLength = CrownWidthCm * FMath::Lerp(
                    0.055f, 0.085f, Noise01(Seed + 7));
                const FVector TerminalEnd = TerminalStart +
                    TerminalHorizontal * TerminalLength +
                    FVector::UpVector * TerminalLength * FMath::Lerp(
                        0.30f, 0.82f, Noise01(Seed + 13));
                AppendNativeCanopyTaperedSegment(
                    TerminalStart,
                    TerminalEnd,
                    2.6f,
                    0.8f,
                    6,
                    BarkVertices,
                    BarkTriangles,
                    BarkNormals,
                    BarkUvs);
                FTerminalBranch& Terminal =
                    TerminalBranches.Emplace_GetRef();
                Terminal.Start = TerminalStart;
                Terminal.End = TerminalEnd;
                Terminal.Seed = Seed;
            }
        }
    }

    constexpr int32 LeafCardsPerTerminal = 2;
    for (int32 TerminalIndex = 0;
         TerminalIndex < TerminalBranches.Num();
         ++TerminalIndex)
    {
        const FTerminalBranch& Terminal = TerminalBranches[TerminalIndex];
        FVector CardUp = (Terminal.End - Terminal.Start).GetSafeNormal();
        CardUp = (CardUp + FVector::UpVector * 0.28f).GetSafeNormal();
        FVector BaseRight = FVector::CrossProduct(
            CardUp, FVector::UpVector).GetSafeNormal();
        if (BaseRight.IsNearlyZero())
        {
            BaseRight = FVector::RightVector;
        }
        const FVector OrthogonalRight = FVector::CrossProduct(
            CardUp, BaseRight).GetSafeNormal();
        for (int32 CardIndex = 0;
             CardIndex < LeafCardsPerTerminal;
             ++CardIndex)
        {
            const int32 Seed = Terminal.Seed + CardIndex * 53;
            const float CardHeight = FMath::Lerp(
                145.0f, 215.0f, Noise01(Seed + 17)) * LeafCardScale;
            const float CardWidth = FMath::Lerp(
                170.0f, 255.0f, Noise01(Seed + 19)) * LeafCardScale;
            const FVector Right = CardIndex == 0
                ? BaseRight
                : OrthogonalRight;
            const FVector Center = Terminal.End +
                CardUp * (0.48f * CardHeight) +
                Right * FMath::Lerp(-18.0f, 18.0f, Noise01(Seed + 23));
            AppendNativeCanopyLeafCard(
                Center,
                Right,
                CardUp,
                CardWidth,
                CardHeight,
                (TerminalIndex * 5 + CardIndex * 3) % LeafAtlasTileCount,
                LeafVertices,
                LeafTriangles,
                LeafNormals,
                LeafUvs);
        }
    }

    const FString PackagePath = FString::Printf(
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
             "SM_RaftSim_SouthForkInteriorLiveOak%s_%s"),
        *VariantToken,
        FormToken);
    AActor* TemporaryActor = AddPreviewTwoSectionProceduralMeshActor(
        World,
        FString::Printf(
            TEXT("SouthForkInteriorLiveOak%s_%s_BuildSource"),
            *VariantToken,
            FormToken),
        BarkVertices,
        BarkTriangles,
        BarkNormals,
        BarkUvs,
        BarkMaterial,
        LeafVertices,
        LeafTriangles,
        LeafNormals,
        LeafUvs,
        LeafMaterial);
    UStaticMesh* Mesh = ConvertNativeCanopyProceduralActorToStaticMesh(
        TemporaryActor,
        PackagePath,
        LeafMaterial,
        /*bEnableNanite=*/false,
        ENaniteShapePreservation::None,
        OutSummary);
    if (TemporaryActor)
    {
        TemporaryActor->Destroy();
    }
    if (Mesh && bGenerateReductionLods &&
        !ConfigureSouthForkLiveOakReviewLods(Mesh, OutSummary))
    {
        return nullptr;
    }
    if (Mesh)
    {
        OutSummary += FString::Printf(
            TEXT("Created true-woody South Fork interior-live-oak %s review: "
                 "woody_segments=%d bark_triangles=%d terminal_branches=%d "
                 "leaf_cards=%d leaf_triangles=%d total_triangles=%d "
                 "leaf_atlas_tiles=%d leaf_card_scale=%.3f billboard_core=0 "
                 "morphology_seed=%d scaffold_count=%d crown_width_scale=%.3f "
                 "crown_height_scale=%.3f directional_asymmetry=%.3f "
                 "form=%s render_lods=%d collision=0 materials=%d.\n"),
            *VariantToken,
            2 + ScaffoldCount *
                (2 + SecondaryCount * (1 + TerminalCountPerSecondary)),
            BarkTriangles.Num() / 3,
            TerminalBranches.Num(),
            TerminalBranches.Num() * LeafCardsPerTerminal,
            LeafTriangles.Num() / 3,
            (BarkTriangles.Num() + LeafTriangles.Num()) / 3,
            LeafAtlasTileCount,
            LeafCardScale,
            MorphologySeedSalt,
            ScaffoldCount,
            CrownWidthScale,
            CrownHeightScale,
            DirectionalAsymmetry,
            FormToken,
            bGenerateReductionLods ? 3 : 1,
            Mesh->GetStaticMaterials().Num());
    }
    return Mesh;
}

UStaticMesh* CreateSouthForkCanopyPhotoPatchVolumeMesh(
    UWorld* World,
    const FString& SpeciesAssetName,
    float WidthCm,
    float HeightCm,
    bool bColumnar,
    UMaterialInterface* BarkMaterial,
    UMaterialInterface* LeafMaterial,
    FString& OutSummary)
{
    // M9 v124-v126 review-only experiment. The production South Fork canopy
    // does not call this generator because its matched captures did not beat
    // the simpler two-plane card baseline.
    if (!World || !BarkMaterial || !LeafMaterial ||
        WidthCm <= 0.0f || HeightCm <= 0.0f)
    {
        return nullptr;
    }

    TArray<FVector> BarkVertices;
    TArray<int32> BarkTriangles;
    TArray<FVector> BarkNormals;
    TArray<FVector2D> BarkUvs;
    TArray<FVector> LeafVertices;
    TArray<int32> LeafTriangles;
    TArray<FVector> LeafNormals;
    TArray<FVector2D> LeafUvs;
    const int32 SpeciesSalt = bColumnar ? 613 : 379;
    auto Noise01 = [SpeciesSalt](int32 Seed)
    {
        const float Value = FMath::Sin(
            static_cast<float>(Seed + SpeciesSalt) * 12.9898f + 0.731f) *
            43758.5453f;
        return FMath::Abs(FMath::Frac(Value));
    };

    if (bColumnar)
    {
        // White alder grows as a narrow multi-leader riparian tree. Keep the
        // base connected while separating the upper stems enough to give real
        // parallax behind the source-photo foliage patches.
        AppendNativeCanopyTaperedSegment(
            FVector::ZeroVector,
            FVector(6.0f, -4.0f, HeightCm * 0.62f),
            18.0f, 8.0f, 10,
            BarkVertices, BarkTriangles, BarkNormals, BarkUvs);
        constexpr int32 LeaderCount = 4;
        for (int32 LeaderIndex = 0; LeaderIndex < LeaderCount; ++LeaderIndex)
        {
            const float Angle = 2.0f * PI * LeaderIndex / LeaderCount + 0.23f;
            const FVector Horizontal(
                FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const FVector Start = FVector::UpVector *
                (HeightCm * (0.10f + 0.035f * LeaderIndex));
            const FVector Mid = Start + Horizontal *
                (42.0f + 12.0f * LeaderIndex) +
                FVector::UpVector * (HeightCm * 0.38f);
            const FVector End = Mid + Horizontal *
                (55.0f + 9.0f * (LeaderIndex % 3)) +
                FVector::UpVector * (HeightCm * (0.38f + 0.025f * LeaderIndex));
            AppendNativeCanopyTaperedSegment(
                Start, Mid, 12.0f, 7.0f, 8,
                BarkVertices, BarkTriangles, BarkNormals, BarkUvs);
            AppendNativeCanopyTaperedSegment(
                Mid, End, 7.0f, 2.0f, 7,
                BarkVertices, BarkTriangles, BarkNormals, BarkUvs);
        }
        constexpr int32 BranchCount = 8;
        for (int32 BranchIndex = 0; BranchIndex < BranchCount; ++BranchIndex)
        {
            const float HeightT = FMath::Lerp(
                0.30f, 0.88f,
                static_cast<float>(BranchIndex) / (BranchCount - 1));
            const float Angle = FMath::DegreesToRadians(
                FMath::Fmod(BranchIndex * 137.50776f + 19.0f, 360.0f));
            const FVector Direction(
                FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const FVector Start = FVector(
                5.0f * FMath::Sin(Angle * 2.0f),
                5.0f * FMath::Cos(Angle * 3.0f),
                HeightCm * HeightT);
            const float Length = FMath::Lerp(
                WidthCm * 0.33f, WidthCm * 0.16f, HeightT);
            const FVector End = Start + Direction * Length +
                FVector::UpVector * Length * FMath::Lerp(0.32f, 0.62f, HeightT);
            AppendNativeCanopyTaperedSegment(
                Start, End,
                FMath::Lerp(5.0f, 2.5f, HeightT), 1.0f, 6,
                BarkVertices, BarkTriangles, BarkNormals, BarkUvs);
        }
    }
    else
    {
        // Interior live oak uses a low fork and broad, irregular scaffold.
        AppendNativeCanopyTaperedSegment(
            FVector::ZeroVector,
            FVector(8.0f, -6.0f, HeightCm * 0.31f),
            28.0f, 16.0f, 10,
            BarkVertices, BarkTriangles, BarkNormals, BarkUvs);
        constexpr int32 ScaffoldCount = 5;
        for (int32 BranchIndex = 0; BranchIndex < ScaffoldCount; ++BranchIndex)
        {
            const float Angle = FMath::DegreesToRadians(
                FMath::Fmod(BranchIndex * 137.50776f + 11.0f, 360.0f));
            const FVector Horizontal(
                FMath::Cos(Angle), FMath::Sin(Angle), 0.0f);
            const FVector Side(-Horizontal.Y, Horizontal.X, 0.0f);
            const FVector Start = FVector(
                4.0f * BranchIndex,
                -3.0f * BranchIndex,
                HeightCm * FMath::Lerp(0.22f, 0.38f,
                    static_cast<float>(BranchIndex) / (ScaffoldCount - 1)));
            const float Length = WidthCm *
                FMath::Lerp(0.24f, 0.36f, Noise01(BranchIndex * 17));
            const FVector Mid = Start + Horizontal * Length * 0.48f +
                Side * FMath::Lerp(-48.0f, 48.0f, Noise01(BranchIndex * 19)) +
                FVector::UpVector * Length * 0.23f;
            const FVector End = Start + Horizontal * Length +
                Side * FMath::Lerp(-72.0f, 72.0f, Noise01(BranchIndex * 23)) +
                FVector::UpVector * Length * 0.42f;
            AppendNativeCanopyTaperedSegment(
                Start, Mid, 18.0f, 9.0f, 8,
                BarkVertices, BarkTriangles, BarkNormals, BarkUvs);
            AppendNativeCanopyTaperedSegment(
                Mid, End, 9.0f, 2.0f, 7,
                BarkVertices, BarkTriangles, BarkNormals, BarkUvs);
        }
    }

    // Reconstruct the complete source photograph as two perpendicular sets of
    // contiguous vertical strips. Shallow depth offsets add guide-visible
    // parallax without chopping the tree into independently rotated tiles.
    // Each orientation retains a coherent photographic crown and trunk; the
    // internal procedural scaffold only fills oblique gaps between the strips.
    constexpr int32 OrientationCount = 4;
    const int32 StripCount = bColumnar ? 7 : 8;
    for (int32 OrientationIndex = 0;
         OrientationIndex < OrientationCount;
         ++OrientationIndex)
    {
        const float CardAngle = 0.25f * PI * OrientationIndex;
        const FVector Right(
            FMath::Cos(CardAngle), FMath::Sin(CardAngle), 0.0f);
        const FVector Normal = FVector::CrossProduct(
            Right, FVector::UpVector).GetSafeNormal();
        for (int32 StripIndex = 0; StripIndex < StripCount; ++StripIndex)
        {
            const float UMinimum =
                static_cast<float>(StripIndex) / StripCount;
            const float UMaximum =
                static_cast<float>(StripIndex + 1) / StripCount;
            const float UCenter = 0.5f * (UMinimum + UMaximum);
            const float SourceX = (UCenter - 0.5f) * WidthCm;
            const float DepthWave = FMath::Sin(
                2.0f * PI * UCenter + OrientationIndex * 1.37f);
            const float DepthNoise = FMath::Lerp(
                -1.0f, 1.0f,
                Noise01(OrientationIndex * 101 + StripIndex * 47 + 7));
            const float DepthScale = bColumnar ? 0.025f : 0.035f;
            const float Depth = WidthCm * DepthScale *
                (0.72f * DepthWave + 0.28f * DepthNoise);
            AppendSouthForkCanopyUvPatchCard(
                Right * SourceX + Normal * Depth +
                    FVector::UpVector * (0.5f * HeightCm),
                Right,
                WidthCm / StripCount * 1.12f,
                HeightCm,
                FVector2D(UMinimum, 0.0f),
                FVector2D(UMaximum, 1.0f),
                LeafVertices,
                LeafTriangles,
                LeafNormals,
                LeafUvs);
        }
    }

    const FString PackagePath = FString::Printf(
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
             "SM_RaftSim_%s_PhotoPatchVolume"),
        *SpeciesAssetName);
    AActor* TemporaryActor = AddPreviewTwoSectionProceduralMeshActor(
        World,
        SpeciesAssetName + TEXT("_PhotoPatchVolume_BuildSource"),
        BarkVertices,
        BarkTriangles,
        BarkNormals,
        BarkUvs,
        BarkMaterial,
        LeafVertices,
        LeafTriangles,
        LeafNormals,
        LeafUvs,
        LeafMaterial);
    UStaticMesh* Mesh = ConvertNativeCanopyProceduralActorToStaticMesh(
        TemporaryActor,
        PackagePath,
        LeafMaterial,
        /*bEnableNanite=*/false,
        ENaniteShapePreservation::None,
        OutSummary);
    if (TemporaryActor)
    {
        TemporaryActor->Destroy();
    }
    if (Mesh)
    {
        OutSummary += FString::Printf(
            TEXT("Created South Fork %s photo-patch volume: bark_triangles=%d "
                 "leaf_patch_triangles=%d total_triangles=%d materials=%d.\n"),
            *SpeciesAssetName,
            BarkTriangles.Num() / 3,
            LeafTriangles.Num() / 3,
            (BarkTriangles.Num() + LeafTriangles.Num()) / 3,
            Mesh->GetStaticMaterials().Num());
    }
    return Mesh;
}
} // namespace

bool CreateSouthForkGeneratedCanopyAssets(
    UWorld* World,
    UStaticMesh*& OutPonderosaMeshA,
    UStaticMesh*& OutPonderosaMeshB,
    UStaticMesh*& OutPonderosaMeshC,
    UStaticMesh*& OutInteriorLiveOakMesh,
    UStaticMesh*& OutWhiteAlderMesh,
    UStaticMesh*& OutDeerbrushMesh,
    FString& OutSummary)
{
    UTexture2D* PonderosaTextureA = CreateSouthForkCanopyTexture(
        TEXT("SouthForkPonderosaMature"),
        PonderosaMatureBillboardSourceRelativePath, OutSummary);
    UTexture2D* PonderosaTextureB = CreateSouthForkCanopyTexture(
        TEXT("SouthForkPonderosaIntermediate"),
        PonderosaIntermediateBillboardSourceRelativePath, OutSummary);
    UTexture2D* PonderosaTextureC = CreateSouthForkCanopyTexture(
        TEXT("SouthForkPonderosaYounger"),
        PonderosaYoungerBillboardSourceRelativePath, OutSummary);
    UTexture2D* OakTexture = CreateSouthForkCanopyTexture(
        TEXT("SouthForkInteriorLiveOak"),
        InteriorLiveOakBillboardSourceRelativePath, OutSummary);
    const FSouthForkCanopyBranchTextureSet PonderosaBranches =
        CreateSouthForkCanopyBranchTextureSet(
            TEXT("SouthForkPonderosaBranchAtlasV1"),
            PonderosaBranchAlbedoOpacityRelativePath,
            PonderosaBranchNormalRelativePath,
            PonderosaBranchPackedRelativePath,
            OutSummary);
    const FSouthForkCanopyBranchTextureSet OakBranches =
        CreateSouthForkCanopyBranchTextureSet(
            TEXT("SouthForkInteriorLiveOakBranchAtlasV1"),
            InteriorLiveOakBranchAlbedoOpacityRelativePath,
            InteriorLiveOakBranchNormalRelativePath,
            InteriorLiveOakBranchPackedRelativePath,
            OutSummary);
    const FSouthForkCanopyBranchTextureSet AlderBranches =
        CreateSouthForkCanopyBranchTextureSet(
            TEXT("SouthForkWhiteAlderBranchAtlasV1"),
            WhiteAlderBranchAlbedoOpacityRelativePath,
            WhiteAlderBranchNormalRelativePath,
            WhiteAlderBranchPackedRelativePath,
            OutSummary);
    const FSouthForkCanopyBranchTextureSet DeerbrushBranches =
        CreateSouthForkCanopyBranchTextureSet(
            TEXT("SouthForkDeerbrushBranchAtlasV1"),
            DeerbrushBranchAlbedoOpacityRelativePath,
            DeerbrushBranchNormalRelativePath,
            DeerbrushBranchPackedRelativePath,
            OutSummary);
    UTexture2D* AlderTexture = CreateSouthForkCanopyTexture(
        TEXT("SouthForkWhiteAlder"),
        WhiteAlderBillboardSourceRelativePath, OutSummary);
    UTexture2D* DeerbrushTexture = CreateSouthForkCanopyTexture(
        TEXT("SouthForkDeerbrush"),
        DeerbrushBillboardSourceRelativePath, OutSummary);
    UMaterial* PonderosaMaterialA = CreateSouthForkCanopyMaterial(
        TEXT("SouthForkPonderosaMature"), PonderosaTextureA, OutSummary);
    UMaterial* PonderosaMaterialB = CreateSouthForkCanopyMaterial(
        TEXT("SouthForkPonderosaIntermediate"), PonderosaTextureB, OutSummary);
    UMaterial* PonderosaMaterialC = CreateSouthForkCanopyMaterial(
        TEXT("SouthForkPonderosaYounger"), PonderosaTextureC, OutSummary);
    UMaterial* OakMaterial = CreateSouthForkCanopyMaterial(
        TEXT("SouthForkInteriorLiveOak"), OakTexture, OutSummary);
    UMaterial* AlderMaterial = CreateSouthForkCanopyMaterial(
        TEXT("SouthForkWhiteAlder"), AlderTexture, OutSummary);
    UMaterial* DeerbrushMaterial = CreateSouthForkCanopyMaterial(
        TEXT("SouthForkDeerbrush"), DeerbrushTexture, OutSummary);
    UMaterial* PonderosaBranchMaterial = CreateSouthForkCanopyBranchMaterial(
        TEXT("SouthForkPonderosa"),
        PonderosaBranches.AlbedoOpacity,
        PonderosaBranches.Normal,
        PonderosaBranches.Packed,
        FLinearColor(0.76f, 0.82f, 0.70f, 1.0f),
        FLinearColor(0.050f, 0.100f, 0.030f, 1.0f),
        OutSummary);
    UMaterial* OakBranchMaterial = CreateSouthForkCanopyBranchMaterial(
        TEXT("SouthForkInteriorLiveOak"),
        OakBranches.AlbedoOpacity,
        OakBranches.Normal,
        OakBranches.Packed,
        FLinearColor(0.78f, 0.84f, 0.70f, 1.0f),
        FLinearColor(0.080f, 0.145f, 0.040f, 1.0f),
        OutSummary);
    UMaterial* AlderBranchMaterial = CreateSouthForkCanopyBranchMaterial(
        TEXT("SouthForkWhiteAlder"),
        AlderBranches.AlbedoOpacity,
        AlderBranches.Normal,
        AlderBranches.Packed,
        FLinearColor(0.82f, 0.90f, 0.76f, 1.0f),
        FLinearColor(0.090f, 0.160f, 0.050f, 1.0f),
        OutSummary);
    UMaterial* DeerbrushBranchMaterial = CreateSouthForkCanopyBranchMaterial(
        TEXT("SouthForkDeerbrush"),
        DeerbrushBranches.AlbedoOpacity,
        DeerbrushBranches.Normal,
        DeerbrushBranches.Packed,
        FLinearColor(0.74f, 0.82f, 0.68f, 1.0f),
        FLinearColor(0.070f, 0.130f, 0.040f, 1.0f),
        OutSummary);
    if (!PonderosaMaterialA || !PonderosaMaterialB || !PonderosaMaterialC ||
        !OakMaterial || !AlderMaterial || !DeerbrushMaterial ||
        !PonderosaBranches.IsComplete() || !OakBranches.IsComplete() ||
        !AlderBranches.IsComplete() || !DeerbrushBranches.IsComplete() ||
        !PonderosaBranchMaterial || !OakBranchMaterial ||
        !AlderBranchMaterial || !DeerbrushBranchMaterial)
    {
        return false;
    }
    OutPonderosaMeshA = CreateSouthForkConnectedCrownMesh(
        World, TEXT("SouthForkPonderosaMature"),
        /*WidthCm=*/1050.0f, /*HeightCm=*/2200.0f,
        ESouthForkConnectedCrownForm::Ponderosa,
        PonderosaMaterialA, PonderosaBranchMaterial, OutSummary);
    OutPonderosaMeshB = CreateSouthForkConnectedCrownMesh(
        World, TEXT("SouthForkPonderosaIntermediate"),
        /*WidthCm=*/820.0f, /*HeightCm=*/1650.0f,
        ESouthForkConnectedCrownForm::Ponderosa,
        PonderosaMaterialB, PonderosaBranchMaterial, OutSummary);
    OutPonderosaMeshC = CreateSouthForkConnectedCrownMesh(
        World, TEXT("SouthForkPonderosaYounger"),
        /*WidthCm=*/590.0f, /*HeightCm=*/1120.0f,
        ESouthForkConnectedCrownForm::Ponderosa,
        PonderosaMaterialC, PonderosaBranchMaterial, OutSummary);
    OutInteriorLiveOakMesh = CreateSouthForkConnectedCrownMesh(
        World, TEXT("SouthForkInteriorLiveOak"),
        /*WidthCm=*/1250.0f, /*HeightCm=*/920.0f,
        ESouthForkConnectedCrownForm::BroadTree,
        OakMaterial, OakBranchMaterial, OutSummary);
    OutWhiteAlderMesh = CreateSouthForkConnectedCrownMesh(
        World, TEXT("SouthForkWhiteAlder"),
        /*WidthCm=*/840.0f, /*HeightCm=*/1350.0f,
        ESouthForkConnectedCrownForm::BroadTree,
        AlderMaterial, AlderBranchMaterial, OutSummary);
    OutDeerbrushMesh = CreateSouthForkConnectedCrownMesh(
        World, TEXT("SouthForkDeerbrush"),
        /*WidthCm=*/330.0f, /*HeightCm=*/230.0f,
        ESouthForkConnectedCrownForm::Shrub,
        DeerbrushMaterial, DeerbrushBranchMaterial, OutSummary);
    const bool bCreated = OutPonderosaMeshA && OutPonderosaMeshB &&
        OutPonderosaMeshC && OutInteriorLiveOakMesh && OutWhiteAlderMesh &&
        OutDeerbrushMesh;
    OutSummary += bCreated
        ? TEXT("Created project-owned connected-crown candidates for all six South Fork canopy profiles, including thirty-six-spray V2 broadleaf volumes.\n")
        : TEXT("Failed to create project-owned South Fork canopy assets.\n");
    return bCreated;
}

bool CreateSouthForkLiveOakBranchAtlasV2ReviewAsset(
    UWorld* World,
    FString& OutSummary)
{
    if (!World)
    {
        OutSummary += TEXT("Live-oak branch-atlas V2 review has no editor world.\n");
        return false;
    }
    UTexture2D* CoreTexture = CreateSouthForkCanopyTexture(
        TEXT("SouthForkInteriorLiveOakAtlasV2ReviewCore"),
        InteriorLiveOakBillboardSourceRelativePath,
        OutSummary);
    UMaterialInterface* CoreMaterial = CreateSouthForkCanopyMaterial(
        TEXT("SouthForkInteriorLiveOakAtlasV2ReviewCore"),
        CoreTexture,
        OutSummary);
    const FSouthForkCanopyBranchTextureSet Branches =
        CreateSouthForkCanopyBranchTextureSet(
            TEXT("SouthForkInteriorLiveOakBranchAtlasV2Review"),
            InteriorLiveOakBranchV2AlbedoOpacityRelativePath,
            InteriorLiveOakBranchV2NormalRelativePath,
            InteriorLiveOakBranchV2PackedRelativePath,
            OutSummary);
    UMaterial* BranchMaterial = Branches.IsComplete()
        ? CreateSouthForkCanopyBranchMaterial(
            TEXT("SouthForkInteriorLiveOakAtlasV2Review"),
            Branches.AlbedoOpacity,
            Branches.Normal,
            Branches.Packed,
            FLinearColor(0.92f, 0.95f, 0.86f, 1.0f),
            FLinearColor(0.075f, 0.135f, 0.038f, 1.0f),
            OutSummary)
        : nullptr;
    if (!CoreMaterial || !BranchMaterial)
    {
        OutSummary += TEXT(
            "Live-oak branch-atlas V2 review material set is incomplete.\n");
        return false;
    }
    UStaticMesh* ReviewMesh = CreateSouthForkConnectedCrownMesh(
        World,
        TEXT("SouthForkInteriorLiveOakAtlasV2Review"),
        /*WidthCm=*/1250.0f,
        /*HeightCm=*/920.0f,
        ESouthForkConnectedCrownForm::BroadTree,
        CoreMaterial,
        BranchMaterial,
        OutSummary);
    if (!ReviewMesh)
    {
        OutSummary += TEXT(
            "Failed to build the live-oak branch-atlas V2 review mesh.\n");
        return false;
    }
    OutSummary += FString::Printf(
        TEXT("Created review-only live-oak branch-atlas V2 mesh %s; the "
             "production canopy and ecology placement remain unchanged.\n"),
        *ReviewMesh->GetPathName());
    return true;
}

bool CreateSouthForkLiveOakWoodyCanopyV1ReviewAsset(
    UWorld* World,
    FString& OutSummary)
{
    if (!World)
    {
        OutSummary += TEXT(
            "Live-oak true-woody V1 review has no editor world.\n");
        return false;
    }
    const FSouthForkCanopyBarkTextureSet BarkTextures =
        CreateSouthForkCanopyBarkTextureSet(
            TEXT("SouthForkInteriorLiveOakWoodyV1Review"),
            InteriorLiveOakBarkV1AlbedoRelativePath,
            InteriorLiveOakBarkV1NormalRelativePath,
            InteriorLiveOakBarkV1PackedRelativePath,
            OutSummary);
    const FSouthForkCanopyBranchTextureSet LeafTextures =
        CreateSouthForkCanopyBranchTextureSet(
            TEXT("SouthForkInteriorLiveOakWoodyV1Review"),
            InteriorLiveOakBranchV2AlbedoOpacityRelativePath,
            InteriorLiveOakBranchV2NormalRelativePath,
            InteriorLiveOakBranchV2PackedRelativePath,
            OutSummary);
    UMaterial* BarkMaterial = CreateSouthForkCanopyBarkMaterial(
        TEXT("SouthForkInteriorLiveOakWoodyV1Review"),
        BarkTextures,
        OutSummary);
    UMaterial* LeafMaterial = LeafTextures.IsComplete()
        ? CreateSouthForkCanopyBranchMaterial(
            TEXT("SouthForkInteriorLiveOakWoodyV1Review"),
            LeafTextures.AlbedoOpacity,
            LeafTextures.Normal,
            LeafTextures.Packed,
            FLinearColor(0.76f, 0.80f, 0.68f, 1.0f),
            FLinearColor(0.065f, 0.120f, 0.034f, 1.0f),
            OutSummary)
        : nullptr;
    if (!BarkMaterial || !LeafMaterial)
    {
        OutSummary += TEXT(
            "Live-oak true-woody V1 review material set is incomplete.\n");
        return false;
    }
    UStaticMesh* ReviewMesh = CreateSouthForkLiveOakWoodyCanopyMesh(
        World,
        BarkMaterial,
        LeafMaterial,
        TEXT("WoodyV1"),
        /*LeafAtlasTileCount=*/12,
        /*LeafCardScale=*/1.0f,
        OutSummary);
    if (!ReviewMesh)
    {
        OutSummary += TEXT(
            "Failed to build the live-oak true-woody V1 review mesh.\n");
        return false;
    }
    OutSummary += FString::Printf(
        TEXT("Created review-only true-woody live-oak mesh %s; production "
             "canopy references and ecology placement remain unchanged.\n"),
        *ReviewMesh->GetPathName());
    return true;
}

bool CreateSouthForkLiveOakDenseWoodyV2ReviewAsset(
    UWorld* World,
    FString& OutSummary)
{
    if (!World)
    {
        OutSummary += TEXT(
            "Live-oak dense-woody V2 review has no editor world.\n");
        return false;
    }
    const FSouthForkCanopyBarkTextureSet BarkTextures =
        CreateSouthForkCanopyBarkTextureSet(
            TEXT("SouthForkInteriorLiveOakDenseWoodyV2Review"),
            InteriorLiveOakBarkV1AlbedoRelativePath,
            InteriorLiveOakBarkV1NormalRelativePath,
            InteriorLiveOakBarkV1PackedRelativePath,
            OutSummary);
    const FSouthForkCanopyBranchTextureSet LeafTextures =
        CreateSouthForkCanopyBranchTextureSet(
            TEXT("SouthForkInteriorLiveOakDenseWoodyV2Review"),
            InteriorLiveOakLeafClustersV3AlbedoOpacityRelativePath,
            InteriorLiveOakLeafClustersV3NormalRelativePath,
            InteriorLiveOakLeafClustersV3PackedRelativePath,
            OutSummary);
    UMaterial* BarkMaterial = CreateSouthForkCanopyBarkMaterial(
        TEXT("SouthForkInteriorLiveOakDenseWoodyV2Review"),
        BarkTextures,
        OutSummary);
    UMaterial* LeafMaterial = LeafTextures.IsComplete()
        ? CreateSouthForkCanopyBranchMaterial(
            TEXT("SouthForkInteriorLiveOakDenseWoodyV2Review"),
            LeafTextures.AlbedoOpacity,
            LeafTextures.Normal,
            LeafTextures.Packed,
            FLinearColor(0.94f, 0.98f, 0.88f, 1.0f),
            FLinearColor(0.075f, 0.135f, 0.038f, 1.0f),
            OutSummary)
        : nullptr;
    if (!BarkMaterial || !LeafMaterial)
    {
        OutSummary += TEXT(
            "Live-oak dense-woody V2 review material set is incomplete.\n");
        return false;
    }
    UStaticMesh* ReviewMesh = CreateSouthForkLiveOakWoodyCanopyMesh(
        World,
        BarkMaterial,
        LeafMaterial,
        TEXT("DenseWoodyV2"),
        /*LeafAtlasTileCount=*/4,
        /*LeafCardScale=*/1.12f,
        OutSummary);
    if (!ReviewMesh)
    {
        OutSummary += TEXT(
            "Failed to build the live-oak dense-woody V2 review mesh.\n");
        return false;
    }
    OutSummary += FString::Printf(
        TEXT("Created review-only dense-woody live-oak mesh %s from the V3 "
             "leaf-dominant cluster atlas; production canopy references and "
             "ecology placement remain unchanged.\n"),
        *ReviewMesh->GetPathName());
    return true;
}

bool CreateSouthForkLiveOakCrownFamilyV3ReviewAssets(
    UWorld* World,
    FString& OutSummary)
{
    if (!World)
    {
        OutSummary += TEXT(
            "Live-oak crown-family V3 review has no editor world.\n");
        return false;
    }
    const FString AssetFamilyName =
        TEXT("SouthForkInteriorLiveOakCrownFamilyV3Review");
    const FSouthForkCanopyBarkTextureSet BarkTextures =
        CreateSouthForkCanopyBarkTextureSet(
            AssetFamilyName,
            InteriorLiveOakBarkV1AlbedoRelativePath,
            InteriorLiveOakBarkV1NormalRelativePath,
            InteriorLiveOakBarkV1PackedRelativePath,
            OutSummary);
    const FSouthForkCanopyBranchTextureSet LeafTextures =
        CreateSouthForkCanopyBranchTextureSet(
            AssetFamilyName,
            InteriorLiveOakLeafClustersV3AlbedoOpacityRelativePath,
            InteriorLiveOakLeafClustersV3NormalRelativePath,
            InteriorLiveOakLeafClustersV3PackedRelativePath,
            OutSummary);
    UMaterial* BarkMaterial = CreateSouthForkCanopyBarkMaterial(
        AssetFamilyName, BarkTextures, OutSummary);
    UMaterial* LeafMaterial = LeafTextures.IsComplete()
        ? CreateSouthForkCanopyBranchMaterial(
            AssetFamilyName,
            LeafTextures.AlbedoOpacity,
            LeafTextures.Normal,
            LeafTextures.Packed,
            FLinearColor(0.98f, 1.02f, 0.93f, 1.0f),
            FLinearColor(0.105f, 0.180f, 0.055f, 1.0f),
            OutSummary,
            /*bCalibratedReviewLighting=*/true)
        : nullptr;
    if (!BarkMaterial || !LeafMaterial)
    {
        OutSummary += TEXT(
            "Live-oak crown-family V3 review material set is incomplete.\n");
        return false;
    }

    struct FCrownForm
    {
        const TCHAR* FormToken;
        int32 SeedSalt;
        int32 ScaffoldCount;
        float CrownWidthScale;
        float CrownHeightScale;
        float DirectionalAsymmetry;
    };
    const FCrownForm CrownForms[] = {
        {TEXT("SpreadingMature"), 17, 6, 1.06f, 1.02f, 0.06f},
        {TEXT("CompactRiverEdge"), 29, 4, 0.78f, 0.84f, 0.04f},
        {TEXT("AsymmetricCompetition"), 43, 5, 0.98f, 0.94f, 0.24f}};
    TArray<UStaticMesh*> ReviewMeshes;
    for (const FCrownForm& CrownForm : CrownForms)
    {
        UStaticMesh* ReviewMesh = CreateSouthForkLiveOakWoodyCanopyMesh(
            World,
            BarkMaterial,
            LeafMaterial,
            TEXT("CrownFamilyV3"),
            /*LeafAtlasTileCount=*/4,
            /*LeafCardScale=*/1.08f,
            OutSummary,
            CrownForm.SeedSalt,
            CrownForm.ScaffoldCount,
            CrownForm.CrownWidthScale,
            CrownForm.CrownHeightScale,
            CrownForm.DirectionalAsymmetry,
            CrownForm.FormToken,
            /*bGenerateReductionLods=*/true);
        if (!ReviewMesh)
        {
            OutSummary += FString::Printf(
                TEXT("Failed to build live-oak crown-family V3 form %s.\n"),
                CrownForm.FormToken);
            return false;
        }
        ReviewMeshes.Add(ReviewMesh);
    }
    OutSummary += FString::Printf(
        TEXT("Created %d review-only deterministic live-oak crown-family V3 "
             "meshes with shared calibrated foliage and explicit near/mid/far "
             "LODs; production canopy references and ecology placement remain "
             "unchanged.\n"),
        ReviewMeshes.Num());
    return ReviewMeshes.Num() == UE_ARRAY_COUNT(CrownForms);
}

bool CreateSouthForkLiveOakIslandTreeMaterialV1ReviewAsset(
    FString& OutSummary)
{
    constexpr TCHAR DonorRoot[] =
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/"
             "FutaleufuIslandTreeSet_1K/");
    UTexture2D* Albedo = LoadObject<UTexture2D>(
        nullptr,
        *(FString(DonorRoot) +
          TEXT("T_IslandTree01_IslandTree01LeavesDiff1K."
               "T_IslandTree01_IslandTree01LeavesDiff1K")));
    UTexture2D* Opacity = LoadObject<UTexture2D>(
        nullptr,
        *(FString(DonorRoot) +
          TEXT("T_IslandTree01_IslandTree01LeavesAlpha1K."
               "T_IslandTree01_IslandTree01LeavesAlpha1K")));
    UTexture2D* Normal = LoadObject<UTexture2D>(
        nullptr,
        *(FString(DonorRoot) +
          TEXT("T_IslandTree01_IslandTree01LeavesNorGl1K."
               "T_IslandTree01_IslandTree01LeavesNorGl1K")));
    UTexture2D* Roughness = LoadObject<UTexture2D>(
        nullptr,
        *(FString(DonorRoot) +
          TEXT("T_IslandTree01_IslandTree01LeavesRough1K."
               "T_IslandTree01_IslandTree01LeavesRough1K")));
    UMaterial* Material = CreateSouthForkIslandTreeFoliageMaterialV1Review(
        Albedo, Opacity, Normal, Roughness, OutSummary);
    if (!Material)
    {
        OutSummary += TEXT(
            "Failed to author the isolated island-tree foliage material V1 review.\n");
        return false;
    }
    OutSummary += FString::Printf(
        TEXT("Created isolated South Fork island-tree foliage material bracket "
             "%s; donor meshes, donor textures, production canopy references, "
             "and ecology placement remain unchanged.\n"),
        *Material->GetPathName());
    return true;
}
} // namespace RaftSimEditorEnvironment

bool FRaftSimEditorModule::RefreshSouthForkGeneratedCanopyAssets(FString& OutSummary)
{
    UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
    if (!World)
    {
        OutSummary += TEXT("No editor world is available for canopy authoring.\n");
        return false;
    }
    if (FParse::Param(
            FCommandLine::Get(),
            TEXT("RaftSimOnlyLiveOakBranchAtlasV2Review")))
    {
        return RaftSimEditorEnvironment::
            CreateSouthForkLiveOakBranchAtlasV2ReviewAsset(World, OutSummary);
    }
    if (FParse::Param(
            FCommandLine::Get(),
            TEXT("RaftSimOnlyLiveOakWoodyCanopyV1Review")))
    {
        return RaftSimEditorEnvironment::
            CreateSouthForkLiveOakWoodyCanopyV1ReviewAsset(
                World, OutSummary);
    }
    if (FParse::Param(
            FCommandLine::Get(),
            TEXT("RaftSimOnlyLiveOakDenseWoodyV2Review")))
    {
        return RaftSimEditorEnvironment::
            CreateSouthForkLiveOakDenseWoodyV2ReviewAsset(
                World, OutSummary);
    }
    if (FParse::Param(
            FCommandLine::Get(),
            TEXT("RaftSimOnlyLiveOakCrownFamilyV3Review")))
    {
        return RaftSimEditorEnvironment::
            CreateSouthForkLiveOakCrownFamilyV3ReviewAssets(
                World, OutSummary);
    }
    if (FParse::Param(
            FCommandLine::Get(),
            TEXT("RaftSimOnlyLiveOakIslandTreeMaterialV1Review")))
    {
        return RaftSimEditorEnvironment::
            CreateSouthForkLiveOakIslandTreeMaterialV1ReviewAsset(OutSummary);
    }
    UStaticMesh* PonderosaMeshA = nullptr;
    UStaticMesh* PonderosaMeshB = nullptr;
    UStaticMesh* PonderosaMeshC = nullptr;
    UStaticMesh* InteriorLiveOakMesh = nullptr;
    UStaticMesh* WhiteAlderMesh = nullptr;
    UStaticMesh* DeerbrushMesh = nullptr;
    return RaftSimEditorEnvironment::CreateSouthForkGeneratedCanopyAssets(
        World, PonderosaMeshA, PonderosaMeshB, PonderosaMeshC,
        InteriorLiveOakMesh, WhiteAlderMesh,
        DeerbrushMesh, OutSummary);
}
