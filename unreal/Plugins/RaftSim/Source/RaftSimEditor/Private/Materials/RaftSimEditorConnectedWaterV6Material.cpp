// Isolated connected-contact-water V6 review material. The runtime V6 mesh is
// solver-contact shaped; the retained photographic V5 atlas contributes only
// aeration breakup and never supplies geometry, collision, or hydraulic state.

#include "AssetRegistry/AssetRegistryModule.h"
#include "Engine/Texture2D.h"
#include "HAL/IConsoleManager.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpressionAdd.h"
#include "Materials/MaterialExpressionComponentMask.h"
#include "Materials/MaterialExpressionConstant2Vector.h"
#include "Materials/MaterialExpressionLinearInterpolate.h"
#include "Materials/MaterialExpressionMultiply.h"
#include "Materials/MaterialExpressionPanner.h"
#include "Materials/MaterialExpressionSaturate.h"
#include "Materials/MaterialExpressionScalarParameter.h"
#include "Materials/MaterialExpressionTextureCoordinate.h"
#include "Materials/MaterialExpressionTextureSampleParameter2D.h"
#include "Materials/MaterialExpressionVectorParameter.h"
#include "Materials/MaterialExpressionVertexColor.h"
#include "Misc/PackageName.h"
#include "UObject/Package.h"
#include "UObject/SavePackage.h"

namespace RaftSimConnectedWaterV6Material
{
static UMaterial* BuildMaterial()
{
    static const TCHAR* AssetName =
        TEXT("M_RaftSim_ConnectedContactWater_V6Review");
    static const TCHAR* PackagePath =
        TEXT("/Game/RaftSim/VFX/Water/ConnectedContactWaterV6Review/"
             "M_RaftSim_ConnectedContactWater_V6Review");
    static const TCHAR* ObjectPath =
        TEXT("/Game/RaftSim/VFX/Water/ConnectedContactWaterV6Review/"
             "M_RaftSim_ConnectedContactWater_V6Review."
             "M_RaftSim_ConnectedContactWater_V6Review");
    UPackage* Package = CreatePackage(PackagePath);
    if (!Package)
    {
        return nullptr;
    }
    UMaterial* Material = Cast<UMaterial>(StaticLoadObject(
        UMaterial::StaticClass(), nullptr, ObjectPath));
    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package, AssetName,
            RF_Public | RF_Standalone | RF_Transactional);
        FAssetRegistryModule::AssetCreated(Material);
    }
    if (!Material)
    {
        return nullptr;
    }

    UTexture2D* PhotographicAtlas = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/VFX/Water/PhotographicSubUVV5Review/Textures/"
             "T_RaftSim_WaterParticleV5Review_SubUV."
             "T_RaftSim_WaterParticleV5Review_SubUV"));
    UTexture2D* FoamLace = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/Textures/"
             "T_RaftSim_SouthForkWater_FoamLace."
             "T_RaftSim_SouthForkWater_FoamLace"));
    UTexture2D* FlowNormal = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/Textures/"
             "T_RaftSim_SouthForkWater_FlowNormal."
             "T_RaftSim_SouthForkWater_FlowNormal"));
    if (!PhotographicAtlas || !FoamLace || !FlowNormal)
    {
        UE_LOG(
            LogTemp, Error,
            TEXT("RaftSim: connected-water V6 inputs missing photo=%d lace=%d normal=%d"),
            PhotographicAtlas ? 1 : 0,
            FoamLace ? 1 : 0,
            FlowNormal ? 1 : 0);
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->BlendMode = BLEND_Translucent;
    Material->TranslucencyLightingMode = TLM_SurfacePerPixelLighting;
    Material->SetShadingModel(MSM_DefaultLit);
    Material->TwoSided = true;
    Material->bTangentSpaceNormal = true;
    Material->SetMaterialUsage(MATUSAGE_StaticMesh);

    auto AddExpression = [Material](UMaterialExpression* Expression)
        -> UMaterialExpression*
    {
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    auto Scalar = [&](const TCHAR* Name, float DefaultValue)
        -> UMaterialExpressionScalarParameter*
    {
        UMaterialExpressionScalarParameter* Expression =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        Expression->ParameterName = Name;
        Expression->DefaultValue = DefaultValue;
        Expression->Group = TEXT("RaftSimConnectedWaterV6");
        return Cast<UMaterialExpressionScalarParameter>(
            AddExpression(Expression));
    };
    auto Vector = [&](const TCHAR* Name, const FLinearColor& DefaultValue)
        -> UMaterialExpressionVectorParameter*
    {
        UMaterialExpressionVectorParameter* Expression =
            NewObject<UMaterialExpressionVectorParameter>(Material);
        Expression->ParameterName = Name;
        Expression->DefaultValue = DefaultValue;
        Expression->Group = TEXT("RaftSimConnectedWaterV6");
        return Cast<UMaterialExpressionVectorParameter>(
            AddExpression(Expression));
    };
    auto Multiply = [&](UMaterialExpression* A, UMaterialExpression* B)
        -> UMaterialExpressionMultiply*
    {
        UMaterialExpressionMultiply* Expression =
            NewObject<UMaterialExpressionMultiply>(Material);
        Expression->A.Expression = A;
        Expression->B.Expression = B;
        return Cast<UMaterialExpressionMultiply>(AddExpression(Expression));
    };
    auto AddValues = [&](UMaterialExpression* A, UMaterialExpression* B)
        -> UMaterialExpressionAdd*
    {
        UMaterialExpressionAdd* Expression =
            NewObject<UMaterialExpressionAdd>(Material);
        Expression->A.Expression = A;
        Expression->B.Expression = B;
        return Cast<UMaterialExpressionAdd>(AddExpression(Expression));
    };
    auto Lerp = [&](UMaterialExpression* A, UMaterialExpression* B,
                    UMaterialExpression* Alpha)
        -> UMaterialExpressionLinearInterpolate*
    {
        UMaterialExpressionLinearInterpolate* Expression =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        Expression->A.Expression = A;
        Expression->B.Expression = B;
        Expression->Alpha.Expression = Alpha;
        return Cast<UMaterialExpressionLinearInterpolate>(
            AddExpression(Expression));
    };
    auto Mask = [&](UMaterialExpression* Input, bool bR, bool bG, bool bB)
        -> UMaterialExpressionComponentMask*
    {
        UMaterialExpressionComponentMask* Expression =
            NewObject<UMaterialExpressionComponentMask>(Material);
        Expression->Input.Expression = Input;
        Expression->R = bR;
        Expression->G = bG;
        Expression->B = bB;
        return Cast<UMaterialExpressionComponentMask>(
            AddExpression(Expression));
    };
    auto SamplePhotographicCell = [&] (
        float OffsetU, float OffsetV, const TCHAR* ParameterName)
        -> UMaterialExpression*
    {
        UMaterialExpressionTextureCoordinate* Uv =
            NewObject<UMaterialExpressionTextureCoordinate>(Material);
        Uv->UTiling = 0.25f;
        Uv->VTiling = 0.25f;
        AddExpression(Uv);
        UMaterialExpressionConstant2Vector* Offset =
            NewObject<UMaterialExpressionConstant2Vector>(Material);
        Offset->R = OffsetU;
        Offset->G = OffsetV;
        AddExpression(Offset);
        UMaterialExpressionAdd* CellUv =
            NewObject<UMaterialExpressionAdd>(Material);
        CellUv->A.Expression = Uv;
        CellUv->B.Expression = Offset;
        AddExpression(CellUv);
        UMaterialExpressionTextureSampleParameter2D* Sample =
            NewObject<UMaterialExpressionTextureSampleParameter2D>(Material);
        Sample->ParameterName = ParameterName;
        Sample->Texture = PhotographicAtlas;
        Sample->SamplerType = SAMPLERTYPE_Masks;
        Sample->Coordinates.Expression = CellUv;
        AddExpression(Sample);
        return Mask(Sample, true, false, false);
    };

    UMaterialExpressionVertexColor* VertexColor =
        NewObject<UMaterialExpressionVertexColor>(Material);
    AddExpression(VertexColor);
    UMaterialExpression* Intensity = Mask(VertexColor, true, false, false);
    UMaterialExpression* AeratedCore = Mask(VertexColor, false, false, true);
    UMaterialExpressionComponentMask* EdgeFeather =
        Mask(VertexColor, true, false, false);
    EdgeFeather->Input.OutputIndex = 4;

    // Frames 11 and 12 are broad aerated-foam donors. Their cell-safe masks
    // modulate coverage inside the connected mesh; neither frame defines the
    // mesh boundary or authorizes an event.
    UMaterialExpression* PhotoA = SamplePhotographicCell(
        0.75f, 0.50f, TEXT("ConnectedPhotoBreakupA"));
    UMaterialExpression* PhotoB = SamplePhotographicCell(
        0.00f, 0.75f, TEXT("ConnectedPhotoBreakupB"));
    UMaterialExpressionSaturate* PhotoMacro =
        NewObject<UMaterialExpressionSaturate>(Material);
    PhotoMacro->Input.Expression = AddValues(
        Multiply(PhotoA, Scalar(TEXT("PhotoBreakupAGain"), 0.72f)),
        Multiply(PhotoB, Scalar(TEXT("PhotoBreakupBGain"), 0.46f)));
    AddExpression(PhotoMacro);

    UMaterialExpressionTextureCoordinate* LaceUv =
        NewObject<UMaterialExpressionTextureCoordinate>(Material);
    LaceUv->UTiling = 1.8f;
    LaceUv->VTiling = 2.7f;
    AddExpression(LaceUv);
    UMaterialExpressionPanner* LacePan =
        NewObject<UMaterialExpressionPanner>(Material);
    LacePan->Coordinate.Expression = LaceUv;
    LacePan->SpeedX = 0.019f;
    LacePan->SpeedY = 0.094f;
    AddExpression(LacePan);
    UMaterialExpressionTextureSampleParameter2D* LaceSample =
        NewObject<UMaterialExpressionTextureSampleParameter2D>(Material);
    LaceSample->ParameterName = TEXT("ConnectedFoamLace");
    LaceSample->Texture = FoamLace;
    LaceSample->SamplerType = SAMPLERTYPE_Masks;
    LaceSample->Coordinates.Expression = LacePan;
    AddExpression(LaceSample);
    UMaterialExpression* Lace = Mask(LaceSample, true, false, false);

    UMaterialExpressionSaturate* Foam =
        NewObject<UMaterialExpressionSaturate>(Material);
    Foam->Input.Expression = AddValues(
        Scalar(TEXT("BreakingFoamFloor"), 0.025f),
        AddValues(
            Multiply(
                PhotoMacro,
                Scalar(TEXT("PhotographicBreakupGain"), 0.68f)),
            AddValues(
                Multiply(Lace, Scalar(TEXT("PrimaryLaceGain"), 0.38f)),
                Multiply(
                    AeratedCore,
                    Scalar(TEXT("BreakingFoamCoreGain"), 0.52f)))));
    AddExpression(Foam);
    UMaterialExpression* FoamCoverage = Multiply(Foam, Foam);
    UMaterialExpression* WeightedFoamCoverage = Multiply(
        FoamCoverage,
        AddValues(
            Scalar(TEXT("BreakingFoamBaseGain"), 0.55f),
            Multiply(
                Intensity,
                Scalar(TEXT("BreakingFoamIntensityGain"), 0.45f))));

    UMaterialExpression* BaseColor = Lerp(
        Vector(
            TEXT("BreakingWaterColor"),
            FLinearColor(0.10f, 0.24f, 0.29f, 1.0f)),
        Vector(
            TEXT("BreakingFoamColor"),
            FLinearColor(0.69f, 0.76f, 0.77f, 1.0f)),
        WeightedFoamCoverage);
    UMaterialExpression* Opacity = Multiply(
        EdgeFeather,
        AddValues(
            Scalar(TEXT("BreakingWaterOpacity"), 0.020f),
            Multiply(
                WeightedFoamCoverage,
                Scalar(TEXT("BreakingFoamOpacity"), 0.70f))));
    UMaterialExpression* Roughness = Lerp(
        Scalar(TEXT("BreakingWaterRoughness"), 0.17f),
        Scalar(TEXT("BreakingFoamRoughness"), 0.76f),
        WeightedFoamCoverage);

    UMaterialExpressionTextureCoordinate* NormalUv =
        NewObject<UMaterialExpressionTextureCoordinate>(Material);
    NormalUv->UTiling = 1.35f;
    NormalUv->VTiling = 2.4f;
    AddExpression(NormalUv);
    UMaterialExpressionPanner* NormalPan =
        NewObject<UMaterialExpressionPanner>(Material);
    NormalPan->Coordinate.Expression = NormalUv;
    NormalPan->SpeedX = 0.012f;
    NormalPan->SpeedY = 0.087f;
    AddExpression(NormalPan);
    UMaterialExpressionTextureSampleParameter2D* NormalSample =
        NewObject<UMaterialExpressionTextureSampleParameter2D>(Material);
    NormalSample->ParameterName = TEXT("BreakingFlowNormal");
    NormalSample->Texture = FlowNormal;
    NormalSample->SamplerType = SAMPLERTYPE_Normal;
    NormalSample->Coordinates.Expression = NormalPan;
    AddExpression(NormalSample);

    UMaterialEditorOnlyData* EditorData = Material->GetEditorOnlyData();
    EditorData->BaseColor.Connect(0, BaseColor);
    EditorData->Opacity.Connect(0, Opacity);
    EditorData->Roughness.Connect(0, Roughness);
    EditorData->Specular.Connect(
        0, Scalar(TEXT("BreakingWaterSpecular"), 0.31f));
    EditorData->Normal.Connect(0, NormalSample);

    Material->PostEditChange();
    Package->MarkPackageDirty();
    FSavePackageArgs SaveArgs;
    SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
    SaveArgs.SaveFlags = SAVE_NoError;
    const FString Filename = FPackageName::LongPackageNameToFilename(
        PackagePath, FPackageName::GetAssetPackageExtension());
    const bool bSaved = UPackage::SavePackage(
        Package, Material, *Filename, SaveArgs);
    UE_LOG(
        LogTemp, Display,
        TEXT("RaftSim: connected-contact-water V6 review material saved=%d"),
        bSaved ? 1 : 0);
    return bSaved ? Material : nullptr;
}

static void HandleCreateMaterial(const TArray<FString>&)
{
    BuildMaterial();
}

static FAutoConsoleCommand GCreateConnectedWaterV6ReviewMaterialCommand(
    TEXT("RaftSim.CreateConnectedContactWaterV6ReviewMaterial"),
    TEXT("Author the isolated connected solver-contact water V6 review material."),
    FConsoleCommandWithArgsDelegate::CreateStatic(&HandleCreateMaterial));
} // namespace RaftSimConnectedWaterV6Material
