// Project-owned breaking-water lip material. The runtime lip is a separate,
// non-colliding mesh driven only by solver-detected hydraulic jumps; this
// focused authoring unit gives that multi-valued geometry flow-lace breakup
// without adding to the bounded legacy photoreal-material implementation.

#include "AssetRegistry/AssetRegistryModule.h"
#include "Environment/RaftSimEditorEnvironmentInternal.h"
#include "Engine/Texture2D.h"
#include "HAL/IConsoleManager.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpressionAdd.h"
#include "Materials/MaterialExpressionComponentMask.h"
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

namespace RaftSimBreakingWaterMaterial
{
static UMaterial* BuildBreakingWaterLipMaterial()
{
    static const TCHAR* AssetName = TEXT("M_RaftSim_BreakingWaterLip");
    static const TCHAR* PackagePath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_BreakingWaterLip");
    static const TCHAR* ObjectPath =
        TEXT("/Game/RaftSim/Materials/M_RaftSim_BreakingWaterLip."
             "M_RaftSim_BreakingWaterLip");
    UPackage* Package = CreatePackage(PackagePath);
    if (Package == nullptr)
    {
        return nullptr;
    }
    UMaterial* Material = Cast<UMaterial>(StaticLoadObject(
        UMaterial::StaticClass(), nullptr, ObjectPath));
    if (Material == nullptr)
    {
        Material = NewObject<UMaterial>(
            Package,
            AssetName,
            RF_Public | RF_Standalone | RF_Transactional);
        FAssetRegistryModule::AssetCreated(Material);
    }
    if (Material == nullptr)
    {
        return nullptr;
    }

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
    if (FoamLace == nullptr || FlowNormal == nullptr)
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("RaftSim: breaking-water material inputs missing lace=%d normal=%d"),
            FoamLace != nullptr ? 1 : 0,
            FlowNormal != nullptr ? 1 : 0);
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

    auto Add = [Material](UMaterialExpression* Expression)
        -> UMaterialExpression*
    {
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    auto Scalar = [&](const TCHAR* Name, float Value)
        -> UMaterialExpressionScalarParameter*
    {
        UMaterialExpressionScalarParameter* Expression =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        Expression->ParameterName = Name;
        Expression->DefaultValue = Value;
        Expression->Group = TEXT("RaftSimBreakingWater");
        return Cast<UMaterialExpressionScalarParameter>(Add(Expression));
    };
    auto Vector = [&](const TCHAR* Name, const FLinearColor& Value)
        -> UMaterialExpressionVectorParameter*
    {
        UMaterialExpressionVectorParameter* Expression =
            NewObject<UMaterialExpressionVectorParameter>(Material);
        Expression->ParameterName = Name;
        Expression->DefaultValue = Value;
        Expression->Group = TEXT("RaftSimBreakingWater");
        return Cast<UMaterialExpressionVectorParameter>(Add(Expression));
    };
    auto Multiply = [&](UMaterialExpression* A, UMaterialExpression* B)
        -> UMaterialExpressionMultiply*
    {
        UMaterialExpressionMultiply* Expression =
            NewObject<UMaterialExpressionMultiply>(Material);
        Expression->A.Expression = A;
        Expression->B.Expression = B;
        return Cast<UMaterialExpressionMultiply>(Add(Expression));
    };
    auto AddValues = [&](UMaterialExpression* A, UMaterialExpression* B)
        -> UMaterialExpressionAdd*
    {
        UMaterialExpressionAdd* Expression =
            NewObject<UMaterialExpressionAdd>(Material);
        Expression->A.Expression = A;
        Expression->B.Expression = B;
        return Cast<UMaterialExpressionAdd>(Add(Expression));
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
        return Cast<UMaterialExpressionLinearInterpolate>(Add(Expression));
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
        return Cast<UMaterialExpressionComponentMask>(Add(Expression));
    };
    auto SampleLace = [&](float UTiling, float VTiling, float SpeedX, float SpeedY,
                          const TCHAR* Name) -> UMaterialExpression*
    {
        UMaterialExpressionTextureCoordinate* Uv =
            NewObject<UMaterialExpressionTextureCoordinate>(Material);
        Uv->UTiling = UTiling;
        Uv->VTiling = VTiling;
        Add(Uv);
        UMaterialExpressionPanner* Pan =
            NewObject<UMaterialExpressionPanner>(Material);
        Pan->Coordinate.Expression = Uv;
        Pan->SpeedX = SpeedX;
        Pan->SpeedY = SpeedY;
        Add(Pan);
        UMaterialExpressionTextureSampleParameter2D* Sample =
            NewObject<UMaterialExpressionTextureSampleParameter2D>(Material);
        Sample->ParameterName = Name;
        Sample->Texture = FoamLace;
        Sample->SamplerType = SAMPLERTYPE_Masks;
        Sample->Coordinates.Expression = Pan;
        Add(Sample);
        return Mask(Sample, true, false, false);
    };

    UMaterialExpressionVertexColor* VertexColor =
        NewObject<UMaterialExpressionVertexColor>(Material);
    Add(VertexColor);
    UMaterialExpressionComponentMask* Intensity =
        Mask(VertexColor, true, false, false);
    UMaterialExpressionComponentMask* AeratedCore =
        Mask(VertexColor, false, false, true);
    UMaterialExpressionComponentMask* EdgeFeather =
        Mask(VertexColor, true, false, false);
    EdgeFeather->Input.OutputIndex = 4;

    UMaterialExpression* LaceA = SampleLace(
        1.35f, 2.80f, 0.014f, 0.082f, TEXT("BreakingFoamLacePrimary"));
    UMaterialExpression* LaceB = SampleLace(
        2.45f, 4.10f, -0.021f, 0.117f, TEXT("BreakingFoamLaceDetail"));
    UMaterialExpressionSaturate* Lace =
        NewObject<UMaterialExpressionSaturate>(Material);
    Lace->Input.Expression = AddValues(
        Multiply(LaceA, Scalar(TEXT("PrimaryLaceGain"), 0.78f)),
        Multiply(LaceB, Scalar(TEXT("DetailLaceGain"), 0.48f)));
    Add(Lace);
    UMaterialExpressionSaturate* Foam =
        NewObject<UMaterialExpressionSaturate>(Material);
    Foam->Input.Expression = AddValues(
        Multiply(
            Lace,
            AddValues(
                Scalar(TEXT("BreakingFoamFloor"), 0.48f),
                Multiply(
                    Intensity,
                    Scalar(TEXT("BreakingFoamIntensityGain"), 0.95f)))),
        Multiply(
            AeratedCore,
            Scalar(TEXT("BreakingFoamCoreGain"), 0.70f)));
    Add(Foam);
    // Whitewater coverage needs a visibly aerated, perforated boundary. Using
    // the raw linear mask in color and opacity let the solver crest-core
    // channel turn a moderate jump into one translucent white slab even when
    // the project-owned lace texture contained dark holes. Squaring retains
    // dense bubbles while quickly clearing the interstitial water.
    UMaterialExpression* FoamCoverage = Multiply(Foam, Foam);

    UMaterialExpression* BaseColor = Lerp(
        Vector(
            TEXT("BreakingWaterColor"),
            FLinearColor(0.18f, 0.31f, 0.32f, 1.0f)),
        Vector(
            TEXT("BreakingFoamColor"),
            FLinearColor(0.73f, 0.78f, 0.77f, 1.0f)),
        FoamCoverage);
    UMaterialExpression* Opacity = Multiply(
        EdgeFeather,
        Lerp(
            Scalar(TEXT("BreakingWaterOpacity"), 0.38f),
            Scalar(TEXT("BreakingFoamOpacity"), 0.84f),
            FoamCoverage));
    UMaterialExpression* Roughness = Lerp(
        Scalar(TEXT("BreakingWaterRoughness"), 0.24f),
        Scalar(TEXT("BreakingFoamRoughness"), 0.74f),
        FoamCoverage);

    UMaterialExpressionTextureCoordinate* NormalUv =
        NewObject<UMaterialExpressionTextureCoordinate>(Material);
    NormalUv->UTiling = 1.55f;
    NormalUv->VTiling = 3.20f;
    Add(NormalUv);
    UMaterialExpressionPanner* NormalPan =
        NewObject<UMaterialExpressionPanner>(Material);
    NormalPan->Coordinate.Expression = NormalUv;
    NormalPan->SpeedX = 0.011f;
    NormalPan->SpeedY = 0.096f;
    Add(NormalPan);
    UMaterialExpressionTextureSampleParameter2D* NormalSample =
        NewObject<UMaterialExpressionTextureSampleParameter2D>(Material);
    NormalSample->ParameterName = TEXT("BreakingFlowNormal");
    NormalSample->Texture = FlowNormal;
    NormalSample->SamplerType = SAMPLERTYPE_Normal;
    NormalSample->Coordinates.Expression = NormalPan;
    Add(NormalSample);

    UMaterialEditorOnlyData* EditorData = Material->GetEditorOnlyData();
    EditorData->BaseColor.Connect(0, BaseColor);
    EditorData->Opacity.Connect(0, Opacity);
    EditorData->Roughness.Connect(0, Roughness);
    EditorData->Specular.Connect(0, Scalar(TEXT("BreakingWaterSpecular"), 0.42f));
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
        LogTemp,
        Display,
        TEXT("RaftSim: production breaking-water lip material saved=%d"),
        bSaved ? 1 : 0);
    return bSaved ? Material : nullptr;
}

static void HandleCreateBreakingWaterLipMaterial(const TArray<FString>&)
{
    if (!RaftSimPhotorealMaterials::BuildSouthForkWaterTextureAssets())
    {
        UE_LOG(
            LogTemp,
            Error,
            TEXT("RaftSim: cannot author breaking water without current source textures"));
        return;
    }
    BuildBreakingWaterLipMaterial();
}

static FAutoConsoleCommand GCreateBreakingWaterLipMaterialCommand(
    TEXT("RaftSim.CreateBreakingWaterLipMaterial"),
    TEXT("Author the project-owned solver-driven breaking-water lip material."),
    FConsoleCommandWithArgsDelegate::CreateStatic(
        &HandleCreateBreakingWaterLipMaterial));
} // namespace RaftSimBreakingWaterMaterial
