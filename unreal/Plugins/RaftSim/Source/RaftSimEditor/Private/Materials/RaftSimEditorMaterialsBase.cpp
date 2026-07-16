#include "Environment/RaftSimEditorEnvironmentInternal.h"

namespace RaftSimEditorEnvironment
{
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
        if (!Material->SetMaterialUsage(MATUSAGE_InstancedStaticMeshes))
        {
            return nullptr;
        }
        Material->PostEditChange();
        FAssetCompilingManager::Get().FinishAllCompilation();
        if (GShaderCompilingManager)
        {
            GShaderCompilingManager->FinishAllCompilation();
        }
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
    else if (Candidate.PreviewSpec.RiverId == TEXT("zambezi_batoka_gorge"))
    {
        RiverAssetName = TEXT("Zambezi");
    }
    else if (Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator"))
    {
        RiverAssetName = TEXT("Futaleufu");
    }
    else if (Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon"))
    {
        RiverAssetName = TEXT("Chilko");
    }
    if (RiverAssetName.IsEmpty())
    {
        OutSummary += FString::Printf(
            TEXT("No Landscape material texture asset token exists for %s.\n"),
            *Candidate.PreviewSpec.RiverId);
        return nullptr;
    }

    auto LoadCandidateTextureForAsset = [](const FString& AssetToken, const TCHAR* AssetRoot, const TCHAR* MapSuffix)
    {
        const FString AssetName = FString::Printf(
            TEXT("T_RaftSim_%s_%s"),
            *AssetToken,
            MapSuffix);
        const FString ObjectPath = FString::Printf(
            TEXT("%s/%s.%s"),
            AssetRoot,
            *AssetName,
            *AssetName);
        return LoadObject<UTexture2D>(nullptr, *ObjectPath);
    };
    auto LoadCandidateTexture = [&LoadCandidateTextureForAsset, &RiverAssetName](
        const TCHAR* AssetRoot,
        const TCHAR* MapSuffix)
    {
        return LoadCandidateTextureForAsset(RiverAssetName, AssetRoot, MapSuffix);
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
    FString DetailAssetName = RiverAssetName;
    if (Candidate.PreviewSpec.RiverId == TEXT("zambezi_batoka_gorge"))
    {
        DetailAssetName = TEXT("ColoradoRiver");
    }
    else if (Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator"))
    {
        DetailAssetName = TEXT("Pacuare");
    }
    UTexture2D* TerrainDetailAlbedo = LoadCandidateTextureForAsset(
        DetailAssetName,
        TEXT("/Game/RaftSim/Rendering/ProductionDetailTextures/Textures"),
        TEXT("TerrainDetailAlbedo"));
    UTexture2D* TerrainDetailPackedSurface = LoadCandidateTextureForAsset(
        DetailAssetName,
        TEXT("/Game/RaftSim/Rendering/ProductionDetailTextures/Textures"),
        TEXT("TerrainDetailAORoughnessHeight"));
    UTexture2D* TerrainDetailNormal = LoadCandidateTextureForAsset(
        DetailAssetName,
        TEXT("/Game/RaftSim/Rendering/ProductionDetailTextures/Textures"),
        TEXT("TerrainDetailNormal"));
    if (Candidate.bPhysicalScaleSourceCorridor)
    {
        SourceMacroAlbedo = LoadCandidateTexture(
            TEXT("/Game/RaftSim/Rendering/PhysicalCorridor/Textures"),
            TEXT("PhysicalCorridorSourceAlbedo"));
        SourcePackedSurface = LoadCandidateTexture(
            TEXT("/Game/RaftSim/Rendering/PhysicalCorridor/Textures"),
            TEXT("PhysicalCorridorAORoughnessHeight"));
        SourceNormalDetail = LoadCandidateTexture(
            TEXT("/Game/RaftSim/Rendering/PhysicalCorridor/Textures"),
            TEXT("PhysicalCorridorNormal"));
        SourceMaterialZones = LoadCandidateTexture(
            TEXT("/Game/RaftSim/Rendering/PhysicalCorridor/Textures"),
            TEXT("PhysicalCorridorMaterialZones"));
    }
    if (!SourceMacroAlbedo || !SourcePackedSurface || !SourceNormalDetail || !SourceMaterialZones ||
        !TerrainDetailAlbedo || !TerrainDetailPackedSurface || !TerrainDetailNormal)
    {
        OutSummary += FString::Printf(
            TEXT("Missing one or more source-conditioned/detail Texture2D assets for %s Landscape material.\n"),
            *Candidate.PreviewSpec.RiverId);
        return nullptr;
    }

    FRaftSimLandscapeMaterialCandidateSettings Settings =
        GetLandscapeMaterialCandidateSettings(Candidate.PreviewSpec.RiverId);
    if (Candidate.bPhysicalScaleSourceCorridor)
    {
        Settings.MacroMappingScale = static_cast<float>(Candidate.LandscapeSize - 1);
        if (Candidate.PreviewSpec.RiverId == TEXT("american_south_fork"))
        {
            Settings.DetailMappingScale = 96.0f;
            Settings.DetailAlbedoWeight = 0.10f;
            Settings.DetailNormalWeight = 0.22f;
            Settings.DetailSurfaceResponseWeight = 0.18f;
            Settings.RiverbedBlendWeight = 0.18f;
            Settings.WetBankBlendWeight = 0.24f;
        }
    }
    FString AssetToken = Candidate.PreviewSpec.RiverId;
    AssetToken.ReplaceInline(TEXT("_"), TEXT(""));
    if (Candidate.bPhysicalScaleSourceCorridor)
    {
        AssetToken += TEXT("_physicalcorridor");
    }
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
    Material->SetShadingModel(MSM_Unlit);
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = true;
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
    UMaterialExpressionMultiply* WetBankBlendMaskRaw = NewObject<UMaterialExpressionMultiply>(Material);
    WetBankBlendMaskRaw->A.Expression = WetBankBand;
    WetBankBlendMaskRaw->B.Expression = WetBankBlendWeight;
    Material->GetExpressionCollection().AddExpression(WetBankBlendMaskRaw);
    UMaterialExpressionConstant* WetBankArtifactSuppressionGain =
        NewObject<UMaterialExpressionConstant>(Material);
    WetBankArtifactSuppressionGain->R = 2.4f;
    Material->GetExpressionCollection().AddExpression(WetBankArtifactSuppressionGain);
    UMaterialExpressionMultiply* WetBankBlendMaskAmplified =
        NewObject<UMaterialExpressionMultiply>(Material);
    WetBankBlendMaskAmplified->A.Expression = WetBankBlendMaskRaw;
    WetBankBlendMaskAmplified->B.Expression = WetBankArtifactSuppressionGain;
    Material->GetExpressionCollection().AddExpression(WetBankBlendMaskAmplified);
    UMaterialExpressionSaturate* WetBankBlendMask = NewObject<UMaterialExpressionSaturate>(Material);
    WetBankBlendMask->Input.Expression = WetBankBlendMaskAmplified;
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

    UMaterialExpression* FinalBaseColor = ConditionedBaseColor;
    if (Candidate.bPhysicalScaleSourceCorridor)
    {
        UMaterialExpressionVertexNormalWS* VertexNormalWs =
            NewObject<UMaterialExpressionVertexNormalWS>(Material);
        Material->GetExpressionCollection().AddExpression(VertexNormalWs);
        UMaterialExpressionComponentMask* VertexNormalZ =
            NewObject<UMaterialExpressionComponentMask>(Material);
        VertexNormalZ->Input.Expression = VertexNormalWs;
        VertexNormalZ->B = true;
        Material->GetExpressionCollection().AddExpression(VertexNormalZ);
        UMaterialExpressionOneMinus* RawSlope = NewObject<UMaterialExpressionOneMinus>(Material);
        RawSlope->Input.Expression = VertexNormalZ;
        Material->GetExpressionCollection().AddExpression(RawSlope);
        UMaterialExpressionConstant* RockSlopeStart = NewObject<UMaterialExpressionConstant>(Material);
        RockSlopeStart->R = 0.22f;
        Material->GetExpressionCollection().AddExpression(RockSlopeStart);
        UMaterialExpressionSubtract* RockSlopeAboveThreshold =
            NewObject<UMaterialExpressionSubtract>(Material);
        RockSlopeAboveThreshold->A.Expression = RawSlope;
        RockSlopeAboveThreshold->B.Expression = RockSlopeStart;
        Material->GetExpressionCollection().AddExpression(RockSlopeAboveThreshold);
        UMaterialExpressionConstant* RockSlopeGain = NewObject<UMaterialExpressionConstant>(Material);
        RockSlopeGain->R = 2.6f;
        Material->GetExpressionCollection().AddExpression(RockSlopeGain);
        UMaterialExpressionMultiply* AmplifiedRockSlope =
            NewObject<UMaterialExpressionMultiply>(Material);
        AmplifiedRockSlope->A.Expression = RockSlopeAboveThreshold;
        AmplifiedRockSlope->B.Expression = RockSlopeGain;
        Material->GetExpressionCollection().AddExpression(AmplifiedRockSlope);
        UMaterialExpressionSaturate* RockSlopeMask = NewObject<UMaterialExpressionSaturate>(Material);
        RockSlopeMask->Input.Expression = AmplifiedRockSlope;
        Material->GetExpressionCollection().AddExpression(RockSlopeMask);
        UMaterialExpressionConstant3Vector* RockColor =
            NewObject<UMaterialExpressionConstant3Vector>(Material);
        RockColor->Constant = FLinearColor(0.30f, 0.29f, 0.25f);
        Material->GetExpressionCollection().AddExpression(RockColor);
        UMaterialExpressionLinearInterpolate* SlopeConditionedBaseColor =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        SlopeConditionedBaseColor->A.Expression = ConditionedBaseColor;
        SlopeConditionedBaseColor->B.Expression = RockColor;
        SlopeConditionedBaseColor->Alpha.Expression = RockSlopeMask;
        Material->GetExpressionCollection().AddExpression(SlopeConditionedBaseColor);
        FinalBaseColor = SlopeConditionedBaseColor;
    }

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
    EmissiveColor->A.Expression = FinalBaseColor;
    EmissiveColor->B.Expression = EmissiveScale;
    Material->GetExpressionCollection().AddExpression(EmissiveColor);

    UMaterialExpressionConstant* Specular = NewObject<UMaterialExpressionConstant>(Material);
    Specular->R = Settings.SpecularLevel;
    Material->GetExpressionCollection().AddExpression(Specular);

    UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, FinalBaseColor);
    ConnectPreviewMaterialColorInput(EditorOnlyData->EmissiveColor, EmissiveColor);
    ConnectPreviewMaterialVectorInput(EditorOnlyData->Normal, Normal);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->AmbientOcclusion, AmbientOcclusion);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, ConditionedRoughness);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (Candidate.bEnableLandscapeNanite)
    {
        Material->SetMaterialUsage(MATUSAGE_Nanite);
    }
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

UMaterialInterface* LoadOrCreatePhysicalSourceTerrainRenderMaterial(
    const FRaftSimLandscapeImportCandidateSpec& Candidate,
    bool bBatokaTerrainIntegratedReview,
    bool bBatokaWorldAlignedReview)
{
    const bool bColorado = Candidate.PreviewSpec.RiverId == TEXT("colorado_river");
    const bool bZambezi = Candidate.PreviewSpec.RiverId == TEXT("zambezi_batoka_gorge");
    const bool bFutaleufu = Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator");
    const bool bChilko = Candidate.PreviewSpec.RiverId == TEXT("chilko_river_lava_canyon");
    const bool bRockCanyon = bColorado || bZambezi;
    FString RiverAssetName = TEXT("AmericanSouthFork");
    if (bColorado)
    {
        RiverAssetName = TEXT("ColoradoRiver");
    }
    else if (bZambezi)
    {
        RiverAssetName = TEXT("Zambezi");
    }
    else if (bFutaleufu)
    {
        RiverAssetName = TEXT("Futaleufu");
    }
    else if (bChilko)
    {
        RiverAssetName = TEXT("Chilko");
    }
    if ((bBatokaTerrainIntegratedReview || bBatokaWorldAlignedReview) && !bZambezi)
    {
        return nullptr;
    }
    const FString MaterialAssetName = bBatokaWorldAlignedReview
        ? TEXT("M_RaftSim_Zambezi_BatokaV12_WorldAlignedTerrainReview")
        : (bBatokaTerrainIntegratedReview
               ? TEXT("M_RaftSim_Zambezi_BatokaV11_TerrainIntegratedReview")
               : FString::Printf(
                     TEXT("M_RaftSim_%s_PhysicalSourceTerrainRender"),
                     *RiverAssetName));
    const FString MaterialPackagePath = FString::Printf(
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/%s"),
        *MaterialAssetName);
    const FString MaterialObjectPath = FString::Printf(
        TEXT("%s.%s"),
        *MaterialPackagePath,
        *MaterialAssetName);
    UMaterial* Material = Cast<UMaterial>(
        StaticLoadObject(UMaterial::StaticClass(), nullptr, *MaterialObjectPath));

    const FString SourceTextureRoot =
        TEXT("/Game/RaftSim/Rendering/PhysicalCorridor/Textures");
    const FString SourceTexturePrefix = FString::Printf(
        TEXT("T_RaftSim_%s_PhysicalCorridor"),
        *RiverAssetName);
    auto LoadSourceTexture = [&SourceTextureRoot, &SourceTexturePrefix](const FString& Token)
    {
        const FString AssetName = SourceTexturePrefix + Token;
        const FString ObjectPath = FString::Printf(
            TEXT("%s/%s.%s"),
            *SourceTextureRoot,
            *AssetName,
            *AssetName);
        return LoadObject<UTexture2D>(nullptr, *ObjectPath);
    };
    UTexture2D* SourceAlbedo = LoadSourceTexture(TEXT("SourceAlbedo"));
    UTexture2D* SourceNormal = LoadSourceTexture(TEXT("Normal"));
    UTexture2D* SourcePacked = LoadSourceTexture(TEXT("AORoughnessHeight"));
    UTexture2D* ForestFloorAlbedo = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/ForestGround03_4K/"
             "T_ForestGround03_BaseColor_4K.T_ForestGround03_BaseColor_4K"));
    UTexture2D* ForestFloorNormal = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/ForestGround03_4K/"
             "T_ForestGround03_NormalGL_4K.T_ForestGround03_NormalGL_4K"));
    UTexture2D* ForestFloorRoughness = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/ForestGround03_4K/"
             "T_ForestGround03_Roughness_4K.T_ForestGround03_Roughness_4K"));
    UTexture2D* RockGroundAlbedo = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/RockGround_4K/"
             "T_RockGround_BaseColor_4K.T_RockGround_BaseColor_4K"));
    UTexture2D* RockGroundNormal = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/RockGround_4K/"
             "T_RockGround_NormalGL_4K.T_RockGround_NormalGL_4K"));
    UTexture2D* RockGroundRoughness = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/RockGround_4K/"
             "T_RockGround_Roughness_4K.T_RockGround_Roughness_4K"));
    UTexture2D* BatokaMacroAo = nullptr;
    UTexture2D* BatokaDetailAlbedo = nullptr;
    UTexture2D* BatokaDetailNormal = nullptr;
    UTexture2D* BatokaDetailRoughness = nullptr;
    if (bBatokaTerrainIntegratedReview)
    {
        RockGroundAlbedo = LoadObject<UTexture2D>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/AerialRocks02_4K/"
                 "T_RaftSim_Batoka_AerialRocks02_Diffuse_4K."
                 "T_RaftSim_Batoka_AerialRocks02_Diffuse_4K"));
        RockGroundNormal = LoadObject<UTexture2D>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/AerialRocks02_4K/"
                 "T_RaftSim_Batoka_AerialRocks02_NormalDX_4K."
                 "T_RaftSim_Batoka_AerialRocks02_NormalDX_4K"));
        RockGroundRoughness = LoadObject<UTexture2D>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/AerialRocks02_4K/"
                 "T_RaftSim_Batoka_AerialRocks02_Roughness_4K."
                 "T_RaftSim_Batoka_AerialRocks02_Roughness_4K"));
        BatokaMacroAo = LoadObject<UTexture2D>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/AerialRocks02_4K/"
                 "T_RaftSim_Batoka_AerialRocks02_AO_4K."
                 "T_RaftSim_Batoka_AerialRocks02_AO_4K"));
        BatokaDetailAlbedo = LoadObject<UTexture2D>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/AmbientCG/Rock037_2K/"
                 "T_RaftSim_Batoka_Rock037_Color_2K.T_RaftSim_Batoka_Rock037_Color_2K"));
        BatokaDetailNormal = LoadObject<UTexture2D>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/AmbientCG/Rock037_2K/"
                 "T_RaftSim_Batoka_Rock037_NormalDX_2K."
                 "T_RaftSim_Batoka_Rock037_NormalDX_2K"));
        BatokaDetailRoughness = LoadObject<UTexture2D>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/ExternalReview/AmbientCG/Rock037_2K/"
                 "T_RaftSim_Batoka_Rock037_Roughness_2K."
                 "T_RaftSim_Batoka_Rock037_Roughness_2K"));
    }
    if (bColorado || bZambezi)
    {
        ForestFloorAlbedo = RockGroundAlbedo;
        ForestFloorNormal = RockGroundNormal;
        ForestFloorRoughness = RockGroundRoughness;
    }
    if (!SourceAlbedo || !SourceNormal || !SourcePacked || !ForestFloorAlbedo ||
        !ForestFloorNormal || !ForestFloorRoughness || !RockGroundAlbedo ||
        !RockGroundNormal || !RockGroundRoughness ||
        (bBatokaTerrainIntegratedReview &&
         (!BatokaMacroAo || !BatokaDetailAlbedo || !BatokaDetailNormal ||
          !BatokaDetailRoughness)))
    {
        return nullptr;
    }

    UPackage* Package = Material ? Material->GetOutermost() : CreatePackage(*MaterialPackagePath);
    if (!Package)
    {
        return nullptr;
    }
    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package,
            *MaterialAssetName,
            RF_Public | RF_Standalone | RF_Transactional);
        if (!Material)
        {
            return nullptr;
        }
        FAssetRegistryModule::AssetCreated(Material);
    }
    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->SetShadingModel(MSM_DefaultLit);
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = true;
    Material->bTangentSpaceNormal = !bBatokaWorldAlignedReview;

    UMaterialExpressionTextureCoordinate* Coordinates =
        NewObject<UMaterialExpressionTextureCoordinate>(Material);
    Material->GetExpressionCollection().AddExpression(Coordinates);
    const float DetailTileSizeCm = bZambezi ? 1800.0f : (bFutaleufu ? 1400.0f : 200.0f);
    const float RockTileSizeCm = bBatokaTerrainIntegratedReview
        ? 5000.0f
        : (bZambezi ? 1200.0f : (bFutaleufu ? 900.0f : 150.0f));
    UMaterialExpressionTextureCoordinate* DetailCoordinates =
        NewObject<UMaterialExpressionTextureCoordinate>(Material);
    DetailCoordinates->UTiling = Candidate.HorizontalSpanXCm / DetailTileSizeCm;
    DetailCoordinates->VTiling = Candidate.HorizontalSpanYCm / DetailTileSizeCm;
    Material->GetExpressionCollection().AddExpression(DetailCoordinates);
    UMaterialExpressionTextureCoordinate* RockCoordinates =
        NewObject<UMaterialExpressionTextureCoordinate>(Material);
    RockCoordinates->UTiling = Candidate.HorizontalSpanXCm / RockTileSizeCm;
    RockCoordinates->VTiling = Candidate.HorizontalSpanYCm / RockTileSizeCm;
    Material->GetExpressionCollection().AddExpression(RockCoordinates);
    UMaterialExpressionTextureCoordinate* BatokaDetailCoordinates = nullptr;
    if (bBatokaTerrainIntegratedReview)
    {
        BatokaDetailCoordinates = NewObject<UMaterialExpressionTextureCoordinate>(Material);
        BatokaDetailCoordinates->UTiling = Candidate.HorizontalSpanXCm / 240.0f;
        BatokaDetailCoordinates->VTiling = Candidate.HorizontalSpanYCm / 240.0f;
        Material->GetExpressionCollection().AddExpression(BatokaDetailCoordinates);
    }

    auto AddTextureSample = [Material](
                                const TCHAR* ParameterName,
                                UTexture2D* Texture,
                                EMaterialSamplerType SamplerType,
                                UMaterialExpressionTextureCoordinate* TextureCoordinates)
    {
        UMaterialExpressionTextureSampleParameter2D* Sample =
            NewObject<UMaterialExpressionTextureSampleParameter2D>(Material);
        Sample->ParameterName = ParameterName;
        Sample->Texture = Texture;
        Sample->SamplerType = SamplerType;
        Sample->Coordinates.Expression = TextureCoordinates;
        Sample->Group = TEXT("RaftSimPhysicalSourceTerrain");
        Material->GetExpressionCollection().AddExpression(Sample);
        return Sample;
    };
    UMaterialExpressionTextureSampleParameter2D* AlbedoSample = AddTextureSample(
        TEXT("PhysicalSourceAlbedo"),
        SourceAlbedo,
        SAMPLERTYPE_Color,
        Coordinates);
    UMaterialExpressionTextureSampleParameter2D* NormalSample = AddTextureSample(
        TEXT("PhysicalSourceNormal"),
        SourceNormal,
        SAMPLERTYPE_Normal,
        Coordinates);
    UMaterialExpressionTextureSampleParameter2D* PackedSample = AddTextureSample(
        TEXT("PhysicalSourceAORoughnessHeight"),
        SourcePacked,
        SAMPLERTYPE_Masks,
        Coordinates);
    UMaterialExpressionTextureSampleParameter2D* ForestFloorAlbedoSample = AddTextureSample(
        TEXT("ForestFloorDetailAlbedo"),
        ForestFloorAlbedo,
        SAMPLERTYPE_Color,
        DetailCoordinates);
    UMaterialExpressionTextureSampleParameter2D* ForestFloorNormalSample = AddTextureSample(
        TEXT("ForestFloorDetailNormal"),
        ForestFloorNormal,
        SAMPLERTYPE_Normal,
        DetailCoordinates);
    UMaterialExpressionTextureSampleParameter2D* ForestFloorRoughnessSample = AddTextureSample(
        TEXT("ForestFloorDetailRoughness"),
        ForestFloorRoughness,
        SAMPLERTYPE_Masks,
        DetailCoordinates);
    UMaterialExpressionTextureSampleParameter2D* RockGroundAlbedoSample = AddTextureSample(
        TEXT("RockGroundDetailAlbedo"),
        RockGroundAlbedo,
        SAMPLERTYPE_Color,
        RockCoordinates);
    UMaterialExpressionTextureSampleParameter2D* RockGroundNormalSample = AddTextureSample(
        TEXT("RockGroundDetailNormal"),
        RockGroundNormal,
        SAMPLERTYPE_Normal,
        RockCoordinates);
    UMaterialExpressionTextureSampleParameter2D* RockGroundRoughnessSample = AddTextureSample(
        TEXT("RockGroundDetailRoughness"),
        RockGroundRoughness,
        SAMPLERTYPE_Masks,
        RockCoordinates);
    UMaterialExpressionTextureSampleParameter2D* BatokaMacroAoSample = nullptr;
    UMaterialExpressionTextureSampleParameter2D* BatokaDetailAlbedoSample = nullptr;
    UMaterialExpressionTextureSampleParameter2D* BatokaDetailNormalSample = nullptr;
    UMaterialExpressionTextureSampleParameter2D* BatokaDetailRoughnessSample = nullptr;
    if (bBatokaTerrainIntegratedReview)
    {
        BatokaMacroAoSample = AddTextureSample(
            TEXT("BatokaAerialRocks02AO"),
            BatokaMacroAo,
            SAMPLERTYPE_Masks,
            RockCoordinates);
        BatokaDetailAlbedoSample = AddTextureSample(
            TEXT("BatokaRock037DetailAlbedo"),
            BatokaDetailAlbedo,
            SAMPLERTYPE_Color,
            BatokaDetailCoordinates);
        BatokaDetailNormalSample = AddTextureSample(
            TEXT("BatokaRock037DetailNormal"),
            BatokaDetailNormal,
            SAMPLERTYPE_Normal,
            BatokaDetailCoordinates);
        BatokaDetailRoughnessSample = AddTextureSample(
            TEXT("BatokaRock037DetailRoughness"),
            BatokaDetailRoughness,
            SAMPLERTYPE_Masks,
            BatokaDetailCoordinates);
    }

    struct FMaterialExpressionOutputRef
    {
        UMaterialExpression* Expression = nullptr;
        int32 OutputIndex = 0;
    };
    auto MakeOutputRef = [](UMaterialExpression* Expression)
    {
        FMaterialExpressionOutputRef Result;
        Result.Expression = Expression;
        return Result;
    };
    FMaterialExpressionOutputRef BatokaMacroAlbedoRef = MakeOutputRef(RockGroundAlbedoSample);
    FMaterialExpressionOutputRef BatokaMacroNormalRef = MakeOutputRef(RockGroundNormalSample);
    FMaterialExpressionOutputRef BatokaMacroRoughnessRef = MakeOutputRef(RockGroundRoughnessSample);
    FMaterialExpressionOutputRef BatokaMacroAoRef = MakeOutputRef(BatokaMacroAoSample);
    FMaterialExpressionOutputRef BatokaDetailAlbedoRef = MakeOutputRef(BatokaDetailAlbedoSample);
    FMaterialExpressionOutputRef BatokaDetailNormalRef = MakeOutputRef(BatokaDetailNormalSample);
    FMaterialExpressionOutputRef BatokaDetailRoughnessRef =
        MakeOutputRef(BatokaDetailRoughnessSample);
    if (bBatokaWorldAlignedReview)
    {
        auto AddWorldAlignedProjection = [Material](
                                             const TCHAR* ParameterName,
                                             UTexture2D* Texture,
                                             EMaterialSamplerType SamplerType,
                                             float TileSizeCm,
                                             bool bNormalProjection)
        {
            FMaterialExpressionOutputRef Result;
            UMaterialExpressionTextureObjectParameter* TextureObject =
                NewObject<UMaterialExpressionTextureObjectParameter>(Material);
            TextureObject->ParameterName = ParameterName;
            TextureObject->Texture = Texture;
            TextureObject->SamplerType = SamplerType;
            TextureObject->Group = TEXT("BatokaV12WorldAlignedTerrainReview");
            Material->GetExpressionCollection().AddExpression(TextureObject);

            UMaterialExpressionConstant3Vector* TextureSize =
                NewObject<UMaterialExpressionConstant3Vector>(Material);
            TextureSize->Constant = FLinearColor(
                TileSizeCm,
                TileSizeCm,
                TileSizeCm,
                1.0f);
            Material->GetExpressionCollection().AddExpression(TextureSize);

            const TCHAR* FunctionPath = bNormalProjection
                ? TEXT("/Engine/Functions/Engine_MaterialFunctions01/Texturing/"
                       "WorldAlignedNormal.WorldAlignedNormal")
                : TEXT("/Engine/Functions/Engine_MaterialFunctions01/Texturing/"
                       "WorldAlignedTexture.WorldAlignedTexture");
            UMaterialFunctionInterface* ProjectionFunction =
                LoadObject<UMaterialFunctionInterface>(nullptr, FunctionPath);
            UMaterialExpressionMaterialFunctionCall* ProjectionCall =
                NewObject<UMaterialExpressionMaterialFunctionCall>(Material);
            Material->GetExpressionCollection().AddExpression(ProjectionCall);
            if (!ProjectionFunction || !ProjectionCall->SetMaterialFunction(ProjectionFunction))
            {
                return Result;
            }
            for (int32 InputIndex = 0;
                 InputIndex < ProjectionCall->FunctionInputs.Num();
                 ++InputIndex)
            {
                const FString InputName = ProjectionCall->GetInputName(InputIndex).ToString();
                FExpressionInput& Input = ProjectionCall->FunctionInputs[InputIndex].Input;
                if (InputName.Contains(TEXT("TextureObject"), ESearchCase::IgnoreCase))
                {
                    Input.Expression = TextureObject;
                }
                else if (InputName.Contains(TEXT("TextureSize"), ESearchCase::IgnoreCase))
                {
                    Input.Expression = TextureSize;
                }
            }
            for (int32 OutputIndex = 0;
                 OutputIndex < ProjectionCall->FunctionOutputs.Num();
                 ++OutputIndex)
            {
                const FString OutputName =
                    ProjectionCall->FunctionOutputs[OutputIndex].Output.OutputName.ToString();
                if (OutputName.Equals(TEXT("XYZ Texture"), ESearchCase::IgnoreCase))
                {
                    Result.Expression = ProjectionCall;
                    Result.OutputIndex = OutputIndex;
                    break;
                }
            }
            return Result;
        };

        BatokaMacroAlbedoRef = AddWorldAlignedProjection(
            TEXT("BatokaAerialRocks02WorldAlignedAlbedo"),
            RockGroundAlbedo,
            SAMPLERTYPE_Color,
            5000.0f,
            false);
        BatokaMacroNormalRef = AddWorldAlignedProjection(
            TEXT("BatokaAerialRocks02WorldAlignedNormal"),
            RockGroundNormal,
            SAMPLERTYPE_Normal,
            5000.0f,
            true);
        BatokaMacroRoughnessRef = AddWorldAlignedProjection(
            TEXT("BatokaAerialRocks02WorldAlignedRoughness"),
            RockGroundRoughness,
            SAMPLERTYPE_Masks,
            5000.0f,
            false);
        BatokaMacroAoRef = AddWorldAlignedProjection(
            TEXT("BatokaAerialRocks02WorldAlignedAO"),
            BatokaMacroAo,
            SAMPLERTYPE_Masks,
            5000.0f,
            false);
        BatokaDetailAlbedoRef = AddWorldAlignedProjection(
            TEXT("BatokaRock037WorldAlignedDetailAlbedo"),
            BatokaDetailAlbedo,
            SAMPLERTYPE_Color,
            240.0f,
            false);
        BatokaDetailNormalRef = AddWorldAlignedProjection(
            TEXT("BatokaRock037WorldAlignedDetailNormal"),
            BatokaDetailNormal,
            SAMPLERTYPE_Normal,
            240.0f,
            true);
        BatokaDetailRoughnessRef = AddWorldAlignedProjection(
            TEXT("BatokaRock037WorldAlignedDetailRoughness"),
            BatokaDetailRoughness,
            SAMPLERTYPE_Masks,
            240.0f,
            false);
        if (!BatokaMacroAlbedoRef.Expression || !BatokaMacroNormalRef.Expression ||
            !BatokaMacroRoughnessRef.Expression || !BatokaMacroAoRef.Expression ||
            !BatokaDetailAlbedoRef.Expression || !BatokaDetailNormalRef.Expression ||
            !BatokaDetailRoughnessRef.Expression)
        {
            return nullptr;
        }
    }

    UMaterialExpressionVertexNormalWS* VertexNormalWs =
        NewObject<UMaterialExpressionVertexNormalWS>(Material);
    Material->GetExpressionCollection().AddExpression(VertexNormalWs);
    UMaterialExpressionComponentMask* VertexNormalZ =
        NewObject<UMaterialExpressionComponentMask>(Material);
    VertexNormalZ->Input.Expression = VertexNormalWs;
    VertexNormalZ->B = true;
    Material->GetExpressionCollection().AddExpression(VertexNormalZ);
    UMaterialExpressionOneMinus* RawSlope = NewObject<UMaterialExpressionOneMinus>(Material);
    RawSlope->Input.Expression = VertexNormalZ;
    Material->GetExpressionCollection().AddExpression(RawSlope);
    UMaterialExpressionConstant* RockSlopeStart = NewObject<UMaterialExpressionConstant>(Material);
    RockSlopeStart->R = bRockCanyon ? 0.10f : 0.16f;
    Material->GetExpressionCollection().AddExpression(RockSlopeStart);
    UMaterialExpressionSubtract* RockSlopeAboveThreshold =
        NewObject<UMaterialExpressionSubtract>(Material);
    RockSlopeAboveThreshold->A.Expression = RawSlope;
    RockSlopeAboveThreshold->B.Expression = RockSlopeStart;
    Material->GetExpressionCollection().AddExpression(RockSlopeAboveThreshold);
    UMaterialExpressionConstant* RockSlopeGain = NewObject<UMaterialExpressionConstant>(Material);
    RockSlopeGain->R = 3.3f;
    Material->GetExpressionCollection().AddExpression(RockSlopeGain);
    UMaterialExpressionMultiply* AmplifiedRockSlope = NewObject<UMaterialExpressionMultiply>(Material);
    AmplifiedRockSlope->A.Expression = RockSlopeAboveThreshold;
    AmplifiedRockSlope->B.Expression = RockSlopeGain;
    Material->GetExpressionCollection().AddExpression(AmplifiedRockSlope);
    UMaterialExpressionSaturate* RockSlopeMask = NewObject<UMaterialExpressionSaturate>(Material);
    RockSlopeMask->Input.Expression = AmplifiedRockSlope;
    Material->GetExpressionCollection().AddExpression(RockSlopeMask);

    UMaterialExpressionVertexColor* VertexColor = NewObject<UMaterialExpressionVertexColor>(Material);
    Material->GetExpressionCollection().AddExpression(VertexColor);
    UMaterialExpressionConstant* VertexColorWeight = NewObject<UMaterialExpressionConstant>(Material);
    VertexColorWeight->R = bZambezi ? 0.16f : (bFutaleufu ? 0.12f : (bRockCanyon ? 1.0f : 0.68f));
    Material->GetExpressionCollection().AddExpression(VertexColorWeight);
    UMaterialExpressionLinearInterpolate* BaseColor =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    BaseColor->A.Expression = AlbedoSample;
    BaseColor->B.Expression = VertexColor;
    BaseColor->Alpha.Expression = VertexColorWeight;
    Material->GetExpressionCollection().AddExpression(BaseColor);
    UMaterialExpressionConstant* DetailAlbedoWeight = NewObject<UMaterialExpressionConstant>(Material);
    DetailAlbedoWeight->R = bZambezi ? 0.16f : (bFutaleufu ? 0.18f : (bRockCanyon ? 0.08f : 0.24f));
    Material->GetExpressionCollection().AddExpression(DetailAlbedoWeight);
    UMaterialExpressionLinearInterpolate* ForestDetailedBaseColor =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    ForestDetailedBaseColor->A.Expression = BaseColor;
    ForestDetailedBaseColor->B.Expression = ForestFloorAlbedoSample;
    ForestDetailedBaseColor->Alpha.Expression = DetailAlbedoWeight;
    Material->GetExpressionCollection().AddExpression(ForestDetailedBaseColor);
    UMaterialExpressionConstant* RockAlbedoWeight = NewObject<UMaterialExpressionConstant>(Material);
    RockAlbedoWeight->R = bZambezi ? 0.20f : (bFutaleufu ? 0.24f : (bRockCanyon ? 0.12f : 0.30f));
    Material->GetExpressionCollection().AddExpression(RockAlbedoWeight);
    UMaterialExpressionLinearInterpolate* RockDetailedBaseColor =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    RockDetailedBaseColor->A.Expression = BaseColor;
    RockDetailedBaseColor->B.Expression = RockGroundAlbedoSample;
    RockDetailedBaseColor->Alpha.Expression = RockAlbedoWeight;
    Material->GetExpressionCollection().AddExpression(RockDetailedBaseColor);
    UMaterialExpression* RockSurfaceBaseColor = RockDetailedBaseColor;
    if (bBatokaTerrainIntegratedReview)
    {
        UMaterialExpressionConstant3Vector* BatokaMacroColorBalance =
            NewObject<UMaterialExpressionConstant3Vector>(Material);
        BatokaMacroColorBalance->Constant = FLinearColor(0.78f, 0.58f, 0.72f, 1.0f);
        Material->GetExpressionCollection().AddExpression(BatokaMacroColorBalance);
        UMaterialExpressionMultiply* BalancedBatokaMacro =
            NewObject<UMaterialExpressionMultiply>(Material);
        BalancedBatokaMacro->A.Expression = BatokaMacroAlbedoRef.Expression;
        BalancedBatokaMacro->A.OutputIndex = BatokaMacroAlbedoRef.OutputIndex;
        BalancedBatokaMacro->B.Expression = BatokaMacroColorBalance;
        Material->GetExpressionCollection().AddExpression(BalancedBatokaMacro);
        UMaterialExpressionConstant* BatokaMacroWeight =
            NewObject<UMaterialExpressionConstant>(Material);
        BatokaMacroWeight->R = 0.56f;
        Material->GetExpressionCollection().AddExpression(BatokaMacroWeight);
        UMaterialExpressionLinearInterpolate* BatokaMacroBaseColor =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        BatokaMacroBaseColor->A.Expression = BaseColor;
        BatokaMacroBaseColor->B.Expression = BalancedBatokaMacro;
        BatokaMacroBaseColor->Alpha.Expression = BatokaMacroWeight;
        Material->GetExpressionCollection().AddExpression(BatokaMacroBaseColor);
        UMaterialExpressionConstant* BatokaDetailColorScale =
            NewObject<UMaterialExpressionConstant>(Material);
        BatokaDetailColorScale->R = 1.18f;
        Material->GetExpressionCollection().AddExpression(BatokaDetailColorScale);
        UMaterialExpressionMultiply* ScaledBatokaDetail =
            NewObject<UMaterialExpressionMultiply>(Material);
        ScaledBatokaDetail->A.Expression = BatokaDetailAlbedoRef.Expression;
        ScaledBatokaDetail->A.OutputIndex = BatokaDetailAlbedoRef.OutputIndex;
        ScaledBatokaDetail->B.Expression = BatokaDetailColorScale;
        Material->GetExpressionCollection().AddExpression(ScaledBatokaDetail);
        UMaterialExpressionConstant* BatokaDetailColorWeight =
            NewObject<UMaterialExpressionConstant>(Material);
        BatokaDetailColorWeight->R = 0.16f;
        Material->GetExpressionCollection().AddExpression(BatokaDetailColorWeight);
        UMaterialExpressionLinearInterpolate* BatokaTwoScaleBaseColor =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        BatokaTwoScaleBaseColor->A.Expression = BatokaMacroBaseColor;
        BatokaTwoScaleBaseColor->B.Expression = ScaledBatokaDetail;
        BatokaTwoScaleBaseColor->Alpha.Expression = BatokaDetailColorWeight;
        Material->GetExpressionCollection().AddExpression(BatokaTwoScaleBaseColor);
        RockSurfaceBaseColor = BatokaTwoScaleBaseColor;
    }
    UMaterialExpressionLinearInterpolate* DetailedBaseColor =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    DetailedBaseColor->A.Expression = ForestDetailedBaseColor;
    DetailedBaseColor->B.Expression = RockSurfaceBaseColor;
    DetailedBaseColor->Alpha.Expression = RockSlopeMask;
    Material->GetExpressionCollection().AddExpression(DetailedBaseColor);

    UMaterialExpressionComponentMask* AmbientOcclusion =
        NewObject<UMaterialExpressionComponentMask>(Material);
    AmbientOcclusion->Input.Expression = PackedSample;
    AmbientOcclusion->R = true;
    Material->GetExpressionCollection().AddExpression(AmbientOcclusion);
    UMaterialExpressionComponentMask* Roughness =
        NewObject<UMaterialExpressionComponentMask>(Material);
    Roughness->Input.Expression = PackedSample;
    Roughness->G = true;
    Material->GetExpressionCollection().AddExpression(Roughness);
    UMaterialExpressionComponentMask* ForestFloorRoughnessMask =
        NewObject<UMaterialExpressionComponentMask>(Material);
    ForestFloorRoughnessMask->Input.Expression = ForestFloorRoughnessSample;
    ForestFloorRoughnessMask->R = true;
    Material->GetExpressionCollection().AddExpression(ForestFloorRoughnessMask);
    UMaterialExpressionComponentMask* RockGroundRoughnessMask =
        NewObject<UMaterialExpressionComponentMask>(Material);
    RockGroundRoughnessMask->Input.Expression = bBatokaTerrainIntegratedReview
        ? BatokaMacroRoughnessRef.Expression
        : RockGroundRoughnessSample;
    RockGroundRoughnessMask->Input.OutputIndex = bBatokaTerrainIntegratedReview
        ? BatokaMacroRoughnessRef.OutputIndex
        : 0;
    RockGroundRoughnessMask->R = true;
    Material->GetExpressionCollection().AddExpression(RockGroundRoughnessMask);
    UMaterialExpressionConstant* DetailRoughnessWeight = NewObject<UMaterialExpressionConstant>(Material);
    DetailRoughnessWeight->R = 0.38f;
    Material->GetExpressionCollection().AddExpression(DetailRoughnessWeight);
    UMaterialExpressionLinearInterpolate* ForestDetailedRoughness =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    ForestDetailedRoughness->A.Expression = Roughness;
    ForestDetailedRoughness->B.Expression = ForestFloorRoughnessMask;
    ForestDetailedRoughness->Alpha.Expression = DetailRoughnessWeight;
    Material->GetExpressionCollection().AddExpression(ForestDetailedRoughness);
    UMaterialExpressionConstant* RockRoughnessWeight = NewObject<UMaterialExpressionConstant>(Material);
    RockRoughnessWeight->R = 0.44f;
    Material->GetExpressionCollection().AddExpression(RockRoughnessWeight);
    UMaterialExpressionLinearInterpolate* RockDetailedRoughness =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    RockDetailedRoughness->A.Expression = Roughness;
    RockDetailedRoughness->B.Expression = RockGroundRoughnessMask;
    RockDetailedRoughness->Alpha.Expression = RockRoughnessWeight;
    Material->GetExpressionCollection().AddExpression(RockDetailedRoughness);
    UMaterialExpression* RockSurfaceRoughness = RockDetailedRoughness;
    if (bBatokaTerrainIntegratedReview)
    {
        UMaterialExpressionComponentMask* BatokaDetailRoughnessMask =
            NewObject<UMaterialExpressionComponentMask>(Material);
        BatokaDetailRoughnessMask->Input.Expression = BatokaDetailRoughnessRef.Expression;
        BatokaDetailRoughnessMask->Input.OutputIndex = BatokaDetailRoughnessRef.OutputIndex;
        BatokaDetailRoughnessMask->R = true;
        Material->GetExpressionCollection().AddExpression(BatokaDetailRoughnessMask);
        UMaterialExpressionConstant* BatokaDetailRoughnessWeight =
            NewObject<UMaterialExpressionConstant>(Material);
        BatokaDetailRoughnessWeight->R = 0.28f;
        Material->GetExpressionCollection().AddExpression(BatokaDetailRoughnessWeight);
        UMaterialExpressionLinearInterpolate* BatokaTwoScaleRoughness =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        BatokaTwoScaleRoughness->A.Expression = RockDetailedRoughness;
        BatokaTwoScaleRoughness->B.Expression = BatokaDetailRoughnessMask;
        BatokaTwoScaleRoughness->Alpha.Expression = BatokaDetailRoughnessWeight;
        Material->GetExpressionCollection().AddExpression(BatokaTwoScaleRoughness);
        RockSurfaceRoughness = BatokaTwoScaleRoughness;
    }
    UMaterialExpressionLinearInterpolate* DetailedRoughness =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    DetailedRoughness->A.Expression = ForestDetailedRoughness;
    DetailedRoughness->B.Expression = RockSurfaceRoughness;
    DetailedRoughness->Alpha.Expression = RockSlopeMask;
    Material->GetExpressionCollection().AddExpression(DetailedRoughness);

    UMaterialExpressionConstant3Vector* FlatNormal =
        NewObject<UMaterialExpressionConstant3Vector>(Material);
    FlatNormal->Constant = FLinearColor(0.0f, 0.0f, 1.0f);
    Material->GetExpressionCollection().AddExpression(FlatNormal);
    UMaterialExpressionConstant* DetailNormalWeight = NewObject<UMaterialExpressionConstant>(Material);
    DetailNormalWeight->R = bBatokaWorldAlignedReview
        ? 0.0f
        : (bZambezi ? 0.30f : (bFutaleufu ? 0.34f : 0.34f));
    Material->GetExpressionCollection().AddExpression(DetailNormalWeight);
    UMaterialExpressionLinearInterpolate* ForestDetailedNormal =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    ForestDetailedNormal->A.Expression = FlatNormal;
    ForestDetailedNormal->B.Expression = ForestFloorNormalSample;
    ForestDetailedNormal->Alpha.Expression = DetailNormalWeight;
    Material->GetExpressionCollection().AddExpression(ForestDetailedNormal);
    UMaterialExpressionConstant* RockNormalWeight = NewObject<UMaterialExpressionConstant>(Material);
    RockNormalWeight->R = bZambezi ? 0.38f : (bFutaleufu ? 0.42f : 0.42f);
    Material->GetExpressionCollection().AddExpression(RockNormalWeight);
    UMaterialExpressionLinearInterpolate* RockDetailedNormal =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    RockDetailedNormal->A.Expression = FlatNormal;
    RockDetailedNormal->B.Expression = bBatokaTerrainIntegratedReview
        ? BatokaMacroNormalRef.Expression
        : RockGroundNormalSample;
    RockDetailedNormal->B.OutputIndex = bBatokaTerrainIntegratedReview
        ? BatokaMacroNormalRef.OutputIndex
        : 0;
    RockDetailedNormal->Alpha.Expression = RockNormalWeight;
    Material->GetExpressionCollection().AddExpression(RockDetailedNormal);
    UMaterialExpression* RockSurfaceNormal = RockDetailedNormal;
    if (bBatokaTerrainIntegratedReview)
    {
        UMaterialExpressionConstant* BatokaDetailNormalWeight =
            NewObject<UMaterialExpressionConstant>(Material);
        BatokaDetailNormalWeight->R = 0.42f;
        Material->GetExpressionCollection().AddExpression(BatokaDetailNormalWeight);
        UMaterialExpressionLinearInterpolate* BatokaTwoScaleNormal =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        BatokaTwoScaleNormal->A.Expression = RockDetailedNormal;
        BatokaTwoScaleNormal->B.Expression = BatokaDetailNormalRef.Expression;
        BatokaTwoScaleNormal->B.OutputIndex = BatokaDetailNormalRef.OutputIndex;
        BatokaTwoScaleNormal->Alpha.Expression = BatokaDetailNormalWeight;
        Material->GetExpressionCollection().AddExpression(BatokaTwoScaleNormal);
        RockSurfaceNormal = BatokaTwoScaleNormal;
    }
    UMaterialExpressionLinearInterpolate* DetailedNormal =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    DetailedNormal->A.Expression = ForestDetailedNormal;
    DetailedNormal->B.Expression = RockSurfaceNormal;
    DetailedNormal->Alpha.Expression = RockSlopeMask;
    Material->GetExpressionCollection().AddExpression(DetailedNormal);
    UMaterialExpressionConstant* SourceNormalWeight = NewObject<UMaterialExpressionConstant>(Material);
    SourceNormalWeight->R = 0.0f;
    Material->GetExpressionCollection().AddExpression(SourceNormalWeight);
    UMaterialExpressionLinearInterpolate* ValidatedNormal =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    ValidatedNormal->A.Expression = DetailedNormal;
    ValidatedNormal->B.Expression = NormalSample;
    ValidatedNormal->Alpha.Expression = SourceNormalWeight;
    Material->GetExpressionCollection().AddExpression(ValidatedNormal);

    UMaterialExpressionConstant* FullAmbientOcclusion = NewObject<UMaterialExpressionConstant>(Material);
    FullAmbientOcclusion->R = 1.0f;
    Material->GetExpressionCollection().AddExpression(FullAmbientOcclusion);
    UMaterialExpressionConstant* SourceAoWeight = NewObject<UMaterialExpressionConstant>(Material);
    SourceAoWeight->R = (bZambezi || bFutaleufu) ? 0.18f : 0.0f;
    Material->GetExpressionCollection().AddExpression(SourceAoWeight);
    UMaterialExpressionLinearInterpolate* ValidatedAmbientOcclusion =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    ValidatedAmbientOcclusion->A.Expression = FullAmbientOcclusion;
    ValidatedAmbientOcclusion->B.Expression = AmbientOcclusion;
    ValidatedAmbientOcclusion->Alpha.Expression = SourceAoWeight;
    Material->GetExpressionCollection().AddExpression(ValidatedAmbientOcclusion);
    UMaterialExpression* FinalAmbientOcclusion = ValidatedAmbientOcclusion;
    if (bBatokaTerrainIntegratedReview)
    {
        UMaterialExpressionComponentMask* BatokaMacroAoMask =
            NewObject<UMaterialExpressionComponentMask>(Material);
        BatokaMacroAoMask->Input.Expression = BatokaMacroAoRef.Expression;
        BatokaMacroAoMask->Input.OutputIndex = BatokaMacroAoRef.OutputIndex;
        BatokaMacroAoMask->R = true;
        Material->GetExpressionCollection().AddExpression(BatokaMacroAoMask);
        UMaterialExpressionConstant* BatokaMacroAoWeight =
            NewObject<UMaterialExpressionConstant>(Material);
        BatokaMacroAoWeight->R = 0.32f;
        Material->GetExpressionCollection().AddExpression(BatokaMacroAoWeight);
        UMaterialExpressionLinearInterpolate* BatokaRockAo =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        BatokaRockAo->A.Expression = ValidatedAmbientOcclusion;
        BatokaRockAo->B.Expression = BatokaMacroAoMask;
        BatokaRockAo->Alpha.Expression = BatokaMacroAoWeight;
        Material->GetExpressionCollection().AddExpression(BatokaRockAo);
        UMaterialExpressionLinearInterpolate* BatokaSlopeAo =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        BatokaSlopeAo->A.Expression = ValidatedAmbientOcclusion;
        BatokaSlopeAo->B.Expression = BatokaRockAo;
        BatokaSlopeAo->Alpha.Expression = RockSlopeMask;
        Material->GetExpressionCollection().AddExpression(BatokaSlopeAo);
        FinalAmbientOcclusion = BatokaSlopeAo;
    }

    UMaterialExpressionConstant* Specular = NewObject<UMaterialExpressionConstant>(Material);
    Specular->R = bRockCanyon ? 0.10f : 0.16f;
    Material->GetExpressionCollection().AddExpression(Specular);
    UMaterialExpressionConstant* EmissiveScale = NewObject<UMaterialExpressionConstant>(Material);
    EmissiveScale->R = bRockCanyon ? 0.008f : 0.025f;
    Material->GetExpressionCollection().AddExpression(EmissiveScale);
    UMaterialExpressionMultiply* Emissive = NewObject<UMaterialExpressionMultiply>(Material);
    Emissive->A.Expression = DetailedBaseColor;
    Emissive->B.Expression = EmissiveScale;
    Material->GetExpressionCollection().AddExpression(Emissive);

    UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, DetailedBaseColor);
    ConnectPreviewMaterialVectorInput(EditorOnlyData->Normal, ValidatedNormal);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, DetailedRoughness);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->AmbientOcclusion, FinalAmbientOcclusion);
    ConnectPreviewMaterialColorInput(EditorOnlyData->EmissiveColor, Emissive);

    Material->PostEditChange();
    Package->MarkPackageDirty();
    const FString Filename = FPackageName::LongPackageNameToFilename(
        MaterialPackagePath,
        FPackageName::GetAssetPackageExtension());
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(Filename), true);
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    if (!UPackage::SavePackage(Package, Material, *Filename, SaveArgs))
    {
        return nullptr;
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
    FString& OutSummary,
    bool bDisableSolverVisualizationFields)
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
    else if (Spec.RiverId == TEXT("zambezi_batoka_gorge"))
    {
        RiverAssetName = TEXT("Zambezi");
    }
    else if (Spec.RiverId == TEXT("futaleufu_terminator"))
    {
        RiverAssetName = TEXT("Futaleufu");
    }
    else if (Spec.RiverId == TEXT("chilko_river_lava_canyon"))
    {
        RiverAssetName = TEXT("Chilko");
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
    FString WaterNormalAssetName = RiverAssetName;
    if (Spec.RiverId == TEXT("zambezi_batoka_gorge"))
    {
        WaterNormalAssetName = TEXT("ColoradoRiver");
    }
    else if (Spec.RiverId == TEXT("futaleufu_terminator"))
    {
        WaterNormalAssetName = TEXT("Pacuare");
    }
    const FString NormalAtlasName = FString::Printf(
        TEXT("T_RaftSim_%s_NormalAtlas"),
        *WaterNormalAssetName);
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

    const FString AssetName = bDisableSolverVisualizationFields
        ? FString::Printf(
              TEXT("MI_RaftSim_%s_PhysicalCorridorWaterCandidate"),
              *RiverAssetName)
        : FString::Printf(
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

    FRaftSimLandscapeCandidateWaterSettings Settings =
        GetLandscapeCandidateWaterSettings(Spec.RiverId);
    if (bDisableSolverVisualizationFields && Spec.RiverId == TEXT("american_south_fork"))
    {
        Settings.BaseColorScale = 1.00f;
        Settings.SurfaceTint = FLinearColor(0.025f, 0.120f, 0.100f);
        Settings.VertexTintWeight = 0.72f;
        Settings.EmissiveFillScale = 0.080f;
        Settings.ReflectionFillIntensity = 0.26f;
        Settings.ReflectionTint = FLinearColor(0.36f, 0.52f, 0.60f);
        Settings.Roughness = 0.14f;
        Settings.Specular = 0.65f;
        Settings.NormalIntensity = 0.60f;
        Settings.SolverFieldEnable = 0.0f;
        Settings.SolverMacroNormalWeight = 0.0f;
        Settings.SolverDepthColorWeight = 0.0f;
        Settings.SolverFieldRoughnessWeight = 0.0f;
        Settings.SolverFroudeAerationWeight = 0.0f;
    }
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
} // namespace RaftSimEditorEnvironment
