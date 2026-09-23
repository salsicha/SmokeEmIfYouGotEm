#include "Environment/RaftSimEditorEnvironmentInternal.h"
#include "Materials/MaterialExpressionAppendVector.h"
#include "Materials/MaterialExpressionComponentMask.h"
#include "Materials/MaterialExpressionMax.h"
#include "Materials/MaterialExpressionCollectionParameter.h"
#include "Materials/MaterialExpressionNoise.h"
#include "Materials/MaterialExpressionPanner.h"
#include "Materials/MaterialExpressionSingleLayerWaterMaterialOutput.h"
#include "Materials/MaterialParameterCollection.h"

namespace RaftSimEditorEnvironment
{
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
        BatokaDetailCoordinates->UTiling = Candidate.HorizontalSpanXCm / 480.0f;
        BatokaDetailCoordinates->VTiling = Candidate.HorizontalSpanYCm / 480.0f;
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
    FMaterialExpressionOutputRef BatokaMacroSecondaryAlbedoRef;
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
        // A second incommensurate projection prevents the reviewed 50 m source
        // footprint from reading as a repeated square across the long gorge.
        // This is appearance-only: neither projection displaces vertices or
        // participates in collision, height queries, or hydraulic authority.
        BatokaMacroSecondaryAlbedoRef = AddWorldAlignedProjection(
            TEXT("BatokaAerialRocks02WorldAlignedSecondaryAlbedo"),
            RockGroundAlbedo,
            SAMPLERTYPE_Color,
            8300.0f,
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
            480.0f,
            false);
        BatokaDetailNormalRef = AddWorldAlignedProjection(
            TEXT("BatokaRock037WorldAlignedDetailNormal"),
            BatokaDetailNormal,
            SAMPLERTYPE_Normal,
            480.0f,
            true);
        BatokaDetailRoughnessRef = AddWorldAlignedProjection(
            TEXT("BatokaRock037WorldAlignedDetailRoughness"),
            BatokaDetailRoughness,
            SAMPLERTYPE_Masks,
            480.0f,
            false);
        if (!BatokaMacroAlbedoRef.Expression ||
            !BatokaMacroSecondaryAlbedoRef.Expression ||
            !BatokaMacroNormalRef.Expression ||
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
    VertexColorWeight->R = bZambezi ? 0.0f : (bFutaleufu ? 0.12f : (bRockCanyon ? 1.0f : 0.68f));
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
        RockSurfaceBaseColor = BuildBatokaOrganicBasaltBaseColor(
            Material,
            BaseColor,
            BatokaMacroAlbedoRef.Expression,
            BatokaMacroAlbedoRef.OutputIndex,
            BatokaMacroSecondaryAlbedoRef.Expression,
            BatokaMacroSecondaryAlbedoRef.OutputIndex,
            BatokaDetailAlbedoRef.Expression,
            BatokaDetailAlbedoRef.OutputIndex);
        if (!RockSurfaceBaseColor)
        {
            return nullptr;
        }
    }
    UMaterialExpressionLinearInterpolate* DetailedBaseColor =
        NewObject<UMaterialExpressionLinearInterpolate>(Material);
    DetailedBaseColor->A.Expression = ForestDetailedBaseColor;
    DetailedBaseColor->B.Expression = RockSurfaceBaseColor;
    DetailedBaseColor->Alpha.Expression = bBatokaTerrainIntegratedReview
        ? BuildBatokaOrganicBasaltColorCoverage(Material, RockSlopeMask)
        : RockSlopeMask;
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
        UMaterialExpressionScalarParameter* BatokaDetailRoughnessWeight =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        BatokaDetailRoughnessWeight->ParameterName = TEXT("BatokaDetailRoughnessWeight");
        BatokaDetailRoughnessWeight->DefaultValue = 0.30f;
        BatokaDetailRoughnessWeight->Group = TEXT("BatokaOrganicBasaltV16");
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
    RockNormalWeight->R = bZambezi ? 0.52f : (bFutaleufu ? 0.42f : 0.42f);
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
        UMaterialExpressionScalarParameter* BatokaDetailNormalWeight =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        BatokaDetailNormalWeight->ParameterName = TEXT("BatokaDetailNormalWeight");
        BatokaDetailNormalWeight->DefaultValue = 0.38f;
        BatokaDetailNormalWeight->Group = TEXT("BatokaOrganicBasaltV16");
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
        BatokaMacroAoWeight->R = 0.44f;
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
    Specular->R = bZambezi ? 0.06f : (bRockCanyon ? 0.10f : 0.16f);
    Material->GetExpressionCollection().AddExpression(Specular);
    UMaterialExpression* FinalBaseColor = DetailedBaseColor;
    UMaterialExpression* FinalRoughness = DetailedRoughness;
    UMaterialExpression* FinalSpecular = Specular;
    if (bBatokaWorldAlignedReview)
    {
        // Only the adaptive near-field bank writes vertex red. Zambezi's
        // source-albedo branch does not consume vertex color, leaving this
        // scalar channel exclusively available for the conditioned mask. It is derived
        // from the conditioned visual water profile and remains a procedural,
        // render-only stain: no displacement, collision, or hydraulic input is
        // connected to this branch.
        UMaterialExpressionComponentMask* WetBankMask =
            NewObject<UMaterialExpressionComponentMask>(Material);
        WetBankMask->Input.Expression = VertexColor;
        WetBankMask->R = true;
        Material->GetExpressionCollection().AddExpression(WetBankMask);
        UMaterialExpressionVectorParameter* WetBankTint =
            NewObject<UMaterialExpressionVectorParameter>(Material);
        WetBankTint->ParameterName = TEXT("BatokaWetBankTint");
        WetBankTint->DefaultValue = FLinearColor(0.78f, 0.82f, 0.86f, 1.0f);
        WetBankTint->Group = TEXT("BatokaConditionedWetBankV1");
        Material->GetExpressionCollection().AddExpression(WetBankTint);
        UMaterialExpressionScalarParameter* WetBankAlbedoScale =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        WetBankAlbedoScale->ParameterName = TEXT("BatokaWetBankAlbedoScale");
        WetBankAlbedoScale->DefaultValue = 0.62f;
        WetBankAlbedoScale->Group = TEXT("BatokaConditionedWetBankV1");
        Material->GetExpressionCollection().AddExpression(WetBankAlbedoScale);
        UMaterialExpressionMultiply* TintedWetBank =
            NewObject<UMaterialExpressionMultiply>(Material);
        TintedWetBank->A.Expression = DetailedBaseColor;
        TintedWetBank->B.Expression = WetBankTint;
        Material->GetExpressionCollection().AddExpression(TintedWetBank);
        UMaterialExpressionMultiply* DarkenedWetBank =
            NewObject<UMaterialExpressionMultiply>(Material);
        DarkenedWetBank->A.Expression = TintedWetBank;
        DarkenedWetBank->B.Expression = WetBankAlbedoScale;
        Material->GetExpressionCollection().AddExpression(DarkenedWetBank);
        UMaterialExpressionLinearInterpolate* ConditionedWetBaseColor =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        ConditionedWetBaseColor->A.Expression = DetailedBaseColor;
        ConditionedWetBaseColor->B.Expression = DarkenedWetBank;
        ConditionedWetBaseColor->Alpha.Expression = WetBankMask;
        Material->GetExpressionCollection().AddExpression(ConditionedWetBaseColor);
        FinalBaseColor = ConditionedWetBaseColor;

        UMaterialExpressionScalarParameter* WetBankRoughness =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        WetBankRoughness->ParameterName = TEXT("BatokaWetBankRoughness");
        WetBankRoughness->DefaultValue = 0.27f;
        WetBankRoughness->Group = TEXT("BatokaConditionedWetBankV1");
        Material->GetExpressionCollection().AddExpression(WetBankRoughness);
        UMaterialExpressionLinearInterpolate* ConditionedWetRoughness =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        ConditionedWetRoughness->A.Expression = DetailedRoughness;
        ConditionedWetRoughness->B.Expression = WetBankRoughness;
        ConditionedWetRoughness->Alpha.Expression = WetBankMask;
        Material->GetExpressionCollection().AddExpression(ConditionedWetRoughness);
        FinalRoughness = ConditionedWetRoughness;

        UMaterialExpressionScalarParameter* WetBankSpecular =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        WetBankSpecular->ParameterName = TEXT("BatokaWetBankSpecular");
        WetBankSpecular->DefaultValue = 0.34f;
        WetBankSpecular->Group = TEXT("BatokaConditionedWetBankV1");
        Material->GetExpressionCollection().AddExpression(WetBankSpecular);
        UMaterialExpressionLinearInterpolate* ConditionedWetSpecular =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        ConditionedWetSpecular->A.Expression = Specular;
        ConditionedWetSpecular->B.Expression = WetBankSpecular;
        ConditionedWetSpecular->Alpha.Expression = WetBankMask;
        Material->GetExpressionCollection().AddExpression(ConditionedWetSpecular);
        FinalSpecular = ConditionedWetSpecular;
    }
    UMaterialExpressionConstant* EmissiveScale = NewObject<UMaterialExpressionConstant>(Material);
    EmissiveScale->R = bZambezi ? 0.002f : (bRockCanyon ? 0.008f : 0.025f);
    Material->GetExpressionCollection().AddExpression(EmissiveScale);
    UMaterialExpressionMultiply* Emissive = NewObject<UMaterialExpressionMultiply>(Material);
    Emissive->A.Expression = FinalBaseColor;
    Emissive->B.Expression = EmissiveScale;
    Material->GetExpressionCollection().AddExpression(Emissive);

    UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    ConnectPreviewMaterialColorInput(EditorOnlyData->BaseColor, FinalBaseColor);
    ConnectPreviewMaterialVectorInput(EditorOnlyData->Normal, ValidatedNormal);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, FinalRoughness);
    ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, FinalSpecular);
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

} // namespace RaftSimEditorEnvironment
