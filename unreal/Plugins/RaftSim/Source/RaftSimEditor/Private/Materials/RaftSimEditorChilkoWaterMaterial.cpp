#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionAppendVector.h"
#include "Materials/MaterialExpressionNoise.h"
#include "Materials/MaterialExpressionPanner.h"

namespace RaftSimEditorEnvironment
{
namespace
{
template <typename ExpressionType>
ExpressionType* AddChilkoWaterExpression(UMaterial* Material)
{
    ExpressionType* Expression = NewObject<ExpressionType>(Material);
    Material->GetExpressionCollection().AddExpression(Expression);
    return Expression;
}
} // namespace

UMaterial* LoadOrCreateChilkoLavaCanyonWaterParent(FString& OutSummary)
{
    static const FString MaterialPackagePath =
        TEXT("/Game/RaftSim/Environment/ChilkoRun/Water/Materials/"
             "M_RaftSim_Chilko_LavaCanyonDefaultLitWater");
    static const FString MaterialObjectName =
        TEXT("M_RaftSim_Chilko_LavaCanyonDefaultLitWater");
    const FString MaterialObjectPath = FString::Printf(
        TEXT("%s.%s"), *MaterialPackagePath, *MaterialObjectName);

    UPackage* Package = CreatePackage(*MaterialPackagePath);
    if (!Package)
    {
        OutSummary += TEXT("Failed to create the Chilko water package.\n");
        return nullptr;
    }

    UMaterial* Material = Cast<UMaterial>(StaticLoadObject(
        UMaterial::StaticClass(), nullptr, *MaterialObjectPath));
    if (!Material)
    {
        Material = FindObject<UMaterial>(Package, *MaterialObjectName);
    }
    if (!Material)
    {
        Material = NewObject<UMaterial>(
            Package,
            *MaterialObjectName,
            RF_Public | RF_Standalone | RF_Transactional);
        if (Material)
        {
            FAssetRegistryModule::AssetCreated(Material);
        }
    }
    if (!Material)
    {
        OutSummary += TEXT("Failed to create the Chilko water material.\n");
        return nullptr;
    }

    UTexture2D* DefaultNormalTexture = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Engine/EngineMaterials/DefaultNormal.DefaultNormal"));
    if (!DefaultNormalTexture)
    {
        OutSummary += TEXT("Failed to load the Chilko water normal fallback.\n");
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->SetShadingModel(MSM_DefaultLit);
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = true;
    Material->bTangentSpaceNormal = true;

    auto Scalar = [Material](const TCHAR* Name, float Value)
    {
        UMaterialExpressionScalarParameter* Parameter =
            AddChilkoWaterExpression<UMaterialExpressionScalarParameter>(Material);
        Parameter->ParameterName = Name;
        Parameter->DefaultValue = Value;
        Parameter->Group = TEXT("ChilkoLavaCanyonWaterV2");
        return Parameter;
    };
    auto Vector = [Material](const TCHAR* Name, const FLinearColor& Value)
    {
        UMaterialExpressionVectorParameter* Parameter =
            AddChilkoWaterExpression<UMaterialExpressionVectorParameter>(Material);
        Parameter->ParameterName = Name;
        Parameter->DefaultValue = Value;
        Parameter->Group = TEXT("ChilkoLavaCanyonWaterV2");
        return Parameter;
    };
    auto Constant = [Material](float Value)
    {
        UMaterialExpressionConstant* Result =
            AddChilkoWaterExpression<UMaterialExpressionConstant>(Material);
        Result->R = Value;
        return Result;
    };
    auto Multiply = [Material](UMaterialExpression* A, UMaterialExpression* B)
    {
        UMaterialExpressionMultiply* Result =
            AddChilkoWaterExpression<UMaterialExpressionMultiply>(Material);
        Result->A.Expression = A;
        Result->B.Expression = B;
        return Result;
    };
    auto Add = [Material](UMaterialExpression* A, UMaterialExpression* B)
    {
        UMaterialExpressionAdd* Result =
            AddChilkoWaterExpression<UMaterialExpressionAdd>(Material);
        Result->A.Expression = A;
        Result->B.Expression = B;
        return Result;
    };
    auto Lerp = [Material](
                    UMaterialExpression* A,
                    UMaterialExpression* B,
                    UMaterialExpression* Alpha)
    {
        UMaterialExpressionLinearInterpolate* Result =
            AddChilkoWaterExpression<UMaterialExpressionLinearInterpolate>(Material);
        Result->A.Expression = A;
        Result->B.Expression = B;
        Result->Alpha.Expression = Alpha;
        return Result;
    };

    // The reach-local packed field has already authored geometry and vertex
    // color on the CPU. This material adds only river-local optics and never
    // samples the shared South Fork shader field a second time.
    UMaterialExpressionVertexColor* VertexColor =
        AddChilkoWaterExpression<UMaterialExpressionVertexColor>(Material);
    UMaterialExpression* PhysicalSurfaceTint = Lerp(
        Vector(TEXT("SurfaceTint"), FLinearColor(0.028f, 0.20f, 0.25f, 0.0f)),
        VertexColor,
        Scalar(TEXT("VertexTintWeight"), 0.78f));
    UMaterialExpression* BaseColor = Multiply(
        PhysicalSurfaceTint,
        Scalar(TEXT("BaseColorScale"), 1.10f));

    UMaterialExpressionNoise* ReachVariation =
        AddChilkoWaterExpression<UMaterialExpressionNoise>(Material);
    ReachVariation->Scale = 0.00027f;
    ReachVariation->bTurbulence = true;
    ReachVariation->Levels = 3;
    ReachVariation->OutputMin = 0.0f;
    ReachVariation->OutputMax = 1.0f;
    UMaterialExpressionNoise* SurfaceVariation =
        AddChilkoWaterExpression<UMaterialExpressionNoise>(Material);
    SurfaceVariation->Scale = 0.00147f;
    SurfaceVariation->bTurbulence = true;
    SurfaceVariation->Levels = 2;
    SurfaceVariation->OutputMin = 0.0f;
    SurfaceVariation->OutputMax = 1.0f;
    UMaterialExpressionNoise* FineVariation =
        AddChilkoWaterExpression<UMaterialExpressionNoise>(Material);
    FineVariation->Scale = 0.00611f;
    FineVariation->bTurbulence = true;
    FineVariation->Levels = 2;
    FineVariation->OutputMin = 0.0f;
    FineVariation->OutputMax = 1.0f;
    UMaterialExpression* VariationField = Add(
        Add(
            Multiply(ReachVariation, Constant(0.52f)),
            Multiply(SurfaceVariation, Constant(0.31f))),
        Multiply(FineVariation, Constant(0.17f)));
    UMaterialExpression* PatternedColor = Lerp(
        Multiply(BaseColor, Constant(0.70f)),
        Multiply(BaseColor, Constant(1.30f)),
        VariationField);
    UMaterialExpression* OpticallyVariedBaseColor = Lerp(
        BaseColor,
        PatternedColor,
        Scalar(TEXT("SurfaceVariationStrength"), 0.46f));

    UMaterialExpressionVectorParameter* AtlasTileOriginParameter = Vector(
        TEXT("AtlasTileOrigin"), FLinearColor(0.0f, 0.5f, 0.0f, 0.0f));
    UMaterialExpressionVectorParameter* AtlasTileScaleParameter = Vector(
        TEXT("AtlasTileScale"),
        FLinearColor(1.0f / 3.0f, 1.0f / 2.0f, 0.0f, 0.0f));
    UMaterialExpressionComponentMask* AtlasTileOrigin =
        AddChilkoWaterExpression<UMaterialExpressionComponentMask>(Material);
    AtlasTileOrigin->Input.Expression = AtlasTileOriginParameter;
    AtlasTileOrigin->R = true;
    AtlasTileOrigin->G = true;
    UMaterialExpressionComponentMask* AtlasTileScale =
        AddChilkoWaterExpression<UMaterialExpressionComponentMask>(Material);
    AtlasTileScale->Input.Expression = AtlasTileScaleParameter;
    AtlasTileScale->R = true;
    AtlasTileScale->G = true;

    auto AddNormalSample =
        [Material, AtlasTileOrigin, AtlasTileScale, DefaultNormalTexture](
            float UTiling,
            float VTiling,
            float SpeedX,
            float SpeedY,
            bool bSwapCoordinates) -> UMaterialExpression*
    {
        UMaterialExpressionTextureCoordinate* TexCoord =
            AddChilkoWaterExpression<UMaterialExpressionTextureCoordinate>(Material);
        TexCoord->UTiling = UTiling;
        TexCoord->VTiling = VTiling;
        UMaterialExpression* BaseCoordinates = TexCoord;
        if (bSwapCoordinates)
        {
            UMaterialExpressionComponentMask* CoordinateU =
                AddChilkoWaterExpression<UMaterialExpressionComponentMask>(Material);
            CoordinateU->Input.Expression = TexCoord;
            CoordinateU->R = true;
            UMaterialExpressionComponentMask* CoordinateV =
                AddChilkoWaterExpression<UMaterialExpressionComponentMask>(Material);
            CoordinateV->Input.Expression = TexCoord;
            CoordinateV->G = true;
            UMaterialExpressionAppendVector* SwappedCoordinates =
                AddChilkoWaterExpression<UMaterialExpressionAppendVector>(Material);
            SwappedCoordinates->A.Expression = CoordinateV;
            SwappedCoordinates->B.Expression = CoordinateU;
            BaseCoordinates = SwappedCoordinates;
        }
        UMaterialExpressionPanner* Panner =
            AddChilkoWaterExpression<UMaterialExpressionPanner>(Material);
        Panner->SpeedX = SpeedX;
        Panner->SpeedY = SpeedY;
        Panner->Coordinate.Expression = BaseCoordinates;
        UMaterialExpressionFrac* WrappedUv =
            AddChilkoWaterExpression<UMaterialExpressionFrac>(Material);
        WrappedUv->Input.Expression = Panner;
        UMaterialExpressionMultiply* ScaledUv =
            AddChilkoWaterExpression<UMaterialExpressionMultiply>(Material);
        ScaledUv->A.Expression = WrappedUv;
        ScaledUv->B.Expression = AtlasTileScale;
        UMaterialExpressionAdd* AtlasUv =
            AddChilkoWaterExpression<UMaterialExpressionAdd>(Material);
        AtlasUv->A.Expression = ScaledUv;
        AtlasUv->B.Expression = AtlasTileOrigin;
        UMaterialExpressionTextureSampleParameter2D* Sample =
            AddChilkoWaterExpression<UMaterialExpressionTextureSampleParameter2D>(Material);
        Sample->ParameterName = TEXT("WaterNormalAtlas");
        Sample->Texture = DefaultNormalTexture;
        Sample->SamplerType = SAMPLERTYPE_Normal;
        Sample->Coordinates.Expression = AtlasUv;
        Sample->Group = TEXT("ChilkoLavaCanyonWaterV2");
        return Sample;
    };

    UMaterialExpression* NormalA =
        AddNormalSample(0.61f, 1.67f, 0.031f, 0.006f, false);
    UMaterialExpression* NormalB =
        AddNormalSample(1.13f, 2.71f, -0.013f, 0.023f, false);
    UMaterialExpression* CrossCurrentNormal =
        AddNormalSample(2.31f, 0.83f, 0.019f, -0.029f, true);
    UMaterialExpressionConstant3Vector* FlatNormal =
        AddChilkoWaterExpression<UMaterialExpressionConstant3Vector>(Material);
    FlatNormal->Constant = FLinearColor(0.0f, 0.0f, 1.0f, 0.0f);
    UMaterialExpression* WaterNormal = Lerp(
        FlatNormal,
        Lerp(
            Lerp(NormalA, NormalB, Constant(0.46f)),
            CrossCurrentNormal,
            Scalar(TEXT("CrossCurrentNormalWeight"), 0.38f)),
        Scalar(TEXT("NormalIntensity"), 0.34f));

    UMaterialExpression* BaseEmissive = Multiply(
        OpticallyVariedBaseColor,
        Scalar(TEXT("EmissiveFillScale"), 0.16f));
    UMaterialExpressionFresnel* ReflectionFresnel =
        AddChilkoWaterExpression<UMaterialExpressionFresnel>(Material);
    ReflectionFresnel->Exponent = 5.0f;
    ReflectionFresnel->BaseReflectFraction = 0.02f;
    UMaterialExpression* ReflectionFill = Multiply(
        Vector(TEXT("ReflectionTint"), FLinearColor(0.34f, 0.55f, 0.66f, 0.0f)),
        Multiply(
            ReflectionFresnel,
            Scalar(TEXT("ReflectionFillIntensity"), 0.12f)));
    UMaterialExpressionScalarParameter* Roughness =
        Scalar(TEXT("Roughness"), 0.22f);
    UMaterialExpression* VariedRoughness = Lerp(
        Roughness,
        Add(
            Roughness,
            Scalar(TEXT("RoughnessVariationAmplitude"), 0.14f)),
        VariationField);
    UMaterialExpressionScalarParameter* Specular =
        Scalar(TEXT("Specular"), 0.48f);

    // Compatibility parameters stay present but unbound: CPU-authored color
    // is the only cooked-field source on this capture ribbon.
    Scalar(TEXT("SolverFieldEnable"), 0.0f);
    Scalar(TEXT("SolverMacroNormalWeight"), 0.0f);
    Scalar(TEXT("SolverDepthColorWeight"), 0.0f);
    Scalar(TEXT("SolverFieldRoughnessWeight"), 0.0f);
    Scalar(TEXT("SolverFroudeAerationWeight"), 0.0f);
    Scalar(TEXT("SolverSpeedVisualGain"), 0.0f);
    Scalar(TEXT("SolverFroudeVisualGain"), 0.0f);
    Vector(TEXT("SolverDeepWaterTint"), FLinearColor(0.012f, 0.11f, 0.15f, 0.0f));
    Vector(TEXT("SolverAerationTint"), FLinearColor(0.86f, 0.93f, 0.94f, 0.0f));
    Scalar(TEXT("Opacity"), 0.34f);
    Scalar(TEXT("RefractionIor"), 1.333f);
    Scalar(TEXT("PhaseG"), 0.15f);
    Vector(TEXT("ScatteringCoefficients"), FLinearColor(0.0012f, 0.0025f, 0.0018f, 0.0f));
    Vector(TEXT("AbsorptionCoefficients"), FLinearColor(0.0045f, 0.0018f, 0.0013f, 0.0f));
    Vector(TEXT("ColorScaleBehindWater"), FLinearColor(0.90f, 0.96f, 0.92f, 0.0f));

    if (UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData())
    {
        ConnectPreviewMaterialColorInput(
            EditorOnlyData->BaseColor, OpticallyVariedBaseColor);
        ConnectPreviewMaterialColorInput(
            EditorOnlyData->EmissiveColor, Add(BaseEmissive, ReflectionFill));
        ConnectPreviewMaterialVectorInput(EditorOnlyData->Normal, WaterNormal);
        ConnectPreviewMaterialScalarInput(
            EditorOnlyData->Roughness, VariedRoughness);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);
    }

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (!Material->SetMaterialUsage(MATUSAGE_Water))
    {
        OutSummary += TEXT("Failed to enable Water usage for Chilko water.\n");
        return nullptr;
    }
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
        OutSummary += TEXT("Failed to save the Chilko water material.\n");
        return nullptr;
    }
    FAssetCompilingManager::Get().FinishAllCompilation();
    OutSummary += TEXT(
        "Built Chilko Lava Canyon opaque Default Lit water V2 with three "
        "moving normal directions, three world optical scales, varied "
        "roughness, CPU-authored cooked-field color authority, and no "
        "displacement.\n");
    return Material;
}
} // namespace RaftSimEditorEnvironment
