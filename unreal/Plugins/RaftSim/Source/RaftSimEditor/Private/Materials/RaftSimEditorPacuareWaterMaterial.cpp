#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionNoise.h"
#include "Materials/MaterialExpressionPanner.h"
#include "Materials/MaterialExpressionSingleLayerWaterMaterialOutput.h"

namespace RaftSimEditorEnvironment
{
namespace
{
template <typename ExpressionType>
ExpressionType* AddPacuareWaterExpression(UMaterial* Material)
{
    ExpressionType* Expression = NewObject<ExpressionType>(Material);
    Material->GetExpressionCollection().AddExpression(Expression);
    return Expression;
}
} // namespace

UMaterial* LoadOrCreatePacuareRainforestWaterParent(FString& OutSummary)
{
    static const FString MaterialPackagePath =
        TEXT("/Game/RaftSim/Environment/PacuareRun/Water/Materials/"
             "M_RaftSim_Pacuare_RainforestSingleLayerWater");
    static const FString MaterialObjectName =
        TEXT("M_RaftSim_Pacuare_RainforestSingleLayerWater");
    const FString MaterialObjectPath = FString::Printf(
        TEXT("%s.%s"), *MaterialPackagePath, *MaterialObjectName);

    UPackage* Package = CreatePackage(*MaterialPackagePath);
    if (!Package)
    {
        OutSummary += TEXT("Failed to create the Pacuare rainforest water package.\n");
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
        OutSummary += TEXT("Failed to create the Pacuare rainforest water material.\n");
        return nullptr;
    }

    UTexture2D* DefaultNormalTexture = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Engine/EngineMaterials/DefaultNormal.DefaultNormal"));
    if (!DefaultNormalTexture)
    {
        OutSummary += TEXT("Failed to load the default Pacuare water normal texture.\n");
        return nullptr;
    }

    Material->Modify();
    Material->GetExpressionCollection().Empty();
    Material->SetShadingModel(MSM_SingleLayerWater);
    Material->BlendMode = BLEND_Opaque;
    Material->TwoSided = true;
    Material->bTangentSpaceNormal = true;
    Material->RefractionMethod = RM_IndexOfRefraction;

    auto Scalar = [Material](const TCHAR* Name, float Value)
    {
        UMaterialExpressionScalarParameter* Parameter =
            AddPacuareWaterExpression<UMaterialExpressionScalarParameter>(Material);
        Parameter->ParameterName = Name;
        Parameter->DefaultValue = Value;
        Parameter->Group = TEXT("PacuareRainforestWaterV1");
        return Parameter;
    };
    auto Vector = [Material](const TCHAR* Name, const FLinearColor& Value)
    {
        UMaterialExpressionVectorParameter* Parameter =
            AddPacuareWaterExpression<UMaterialExpressionVectorParameter>(Material);
        Parameter->ParameterName = Name;
        Parameter->DefaultValue = Value;
        Parameter->Group = TEXT("PacuareRainforestWaterV1");
        return Parameter;
    };
    auto Multiply = [Material](UMaterialExpression* A, UMaterialExpression* B)
    {
        UMaterialExpressionMultiply* Result =
            AddPacuareWaterExpression<UMaterialExpressionMultiply>(Material);
        Result->A.Expression = A;
        Result->B.Expression = B;
        return Result;
    };
    auto Add = [Material](UMaterialExpression* A, UMaterialExpression* B)
    {
        UMaterialExpressionAdd* Result =
            AddPacuareWaterExpression<UMaterialExpressionAdd>(Material);
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
            AddPacuareWaterExpression<UMaterialExpressionLinearInterpolate>(Material);
        Result->A.Expression = A;
        Result->B.Expression = B;
        Result->Alpha.Expression = Alpha;
        return Result;
    };
    auto Constant = [Material](float Value)
    {
        UMaterialExpressionConstant* Result =
            AddPacuareWaterExpression<UMaterialExpressionConstant>(Material);
        Result->R = Value;
        return Result;
    };

    UMaterialExpressionVertexColor* VertexColor =
        AddPacuareWaterExpression<UMaterialExpressionVertexColor>(Material);
    UMaterialExpression* PhysicalSurfaceTint = Lerp(
        Vector(TEXT("SurfaceTint"), FLinearColor(0.050f, 0.085f, 0.060f, 0.0f)),
        VertexColor,
        Scalar(TEXT("VertexTintWeight"), 0.30f));
    UMaterialExpression* BaseColor = Multiply(
        PhysicalSurfaceTint,
        Scalar(TEXT("BaseColorScale"), 0.90f));

    // Two incommensurate world-space fields break up the former uniform green
    // plate without changing water geometry, collision, or solver authority.
    UMaterialExpressionNoise* MacroVariation =
        AddPacuareWaterExpression<UMaterialExpressionNoise>(Material);
    MacroVariation->Scale = 0.00042f;
    MacroVariation->bTurbulence = true;
    MacroVariation->Levels = 3;
    MacroVariation->OutputMin = 0.0f;
    MacroVariation->OutputMax = 1.0f;
    UMaterialExpressionNoise* FineVariation =
        AddPacuareWaterExpression<UMaterialExpressionNoise>(Material);
    FineVariation->Scale = 0.00210f;
    FineVariation->bTurbulence = true;
    FineVariation->Levels = 2;
    FineVariation->OutputMin = 0.0f;
    FineVariation->OutputMax = 1.0f;
    UMaterialExpression* VariationField = Multiply(
        Add(MacroVariation, FineVariation), Constant(0.5f));
    UMaterialExpression* PatternedColor = Lerp(
        Multiply(BaseColor, Constant(0.68f)),
        Multiply(BaseColor, Constant(1.32f)),
        VariationField);
    UMaterialExpression* OpticallyVariedBaseColor = Lerp(
        BaseColor,
        PatternedColor,
        Scalar(TEXT("SurfaceVariationStrength"), 0.32f));

    UMaterialExpressionVectorParameter* AtlasTileOriginParameter = Vector(
        TEXT("AtlasTileOrigin"), FLinearColor(0.0f, 0.5f, 0.0f, 0.0f));
    UMaterialExpressionVectorParameter* AtlasTileScaleParameter = Vector(
        TEXT("AtlasTileScale"), FLinearColor(1.0f / 3.0f, 1.0f / 2.0f, 0.0f, 0.0f));
    UMaterialExpressionComponentMask* AtlasTileOrigin =
        AddPacuareWaterExpression<UMaterialExpressionComponentMask>(Material);
    AtlasTileOrigin->Input.Expression = AtlasTileOriginParameter;
    AtlasTileOrigin->R = true;
    AtlasTileOrigin->G = true;
    UMaterialExpressionComponentMask* AtlasTileScale =
        AddPacuareWaterExpression<UMaterialExpressionComponentMask>(Material);
    AtlasTileScale->Input.Expression = AtlasTileScaleParameter;
    AtlasTileScale->R = true;
    AtlasTileScale->G = true;

    auto AddNormalSample =
        [Material, AtlasTileOrigin, AtlasTileScale, DefaultNormalTexture](
            float UTiling,
            float VTiling,
            float SpeedX,
            float SpeedY) -> UMaterialExpression*
    {
        UMaterialExpressionTextureCoordinate* TexCoord =
            AddPacuareWaterExpression<UMaterialExpressionTextureCoordinate>(Material);
        TexCoord->UTiling = UTiling;
        TexCoord->VTiling = VTiling;
        UMaterialExpressionPanner* Panner =
            AddPacuareWaterExpression<UMaterialExpressionPanner>(Material);
        Panner->SpeedX = SpeedX;
        Panner->SpeedY = SpeedY;
        Panner->Coordinate.Expression = TexCoord;

        UMaterialExpressionFrac* WrappedUvPrimary =
            AddPacuareWaterExpression<UMaterialExpressionFrac>(Material);
        WrappedUvPrimary->Input.Expression = Panner;
        UMaterialExpressionConstant2Vector* HalfPeriodOffset =
            AddPacuareWaterExpression<UMaterialExpressionConstant2Vector>(Material);
        HalfPeriodOffset->R = 0.5f;
        HalfPeriodOffset->G = 0.0f;
        UMaterialExpressionAdd* OffsetTexCoord =
            AddPacuareWaterExpression<UMaterialExpressionAdd>(Material);
        OffsetTexCoord->A.Expression = Panner;
        OffsetTexCoord->B.Expression = HalfPeriodOffset;
        UMaterialExpressionFrac* WrappedUvOffset =
            AddPacuareWaterExpression<UMaterialExpressionFrac>(Material);
        WrappedUvOffset->Input.Expression = OffsetTexCoord;

        auto SampleAtlas =
            [Material, AtlasTileOrigin, AtlasTileScale, DefaultNormalTexture](
                UMaterialExpression* WrappedUv)
        {
            UMaterialExpressionMultiply* ScaledUv =
                AddPacuareWaterExpression<UMaterialExpressionMultiply>(Material);
            ScaledUv->A.Expression = WrappedUv;
            ScaledUv->B.Expression = AtlasTileScale;
            UMaterialExpressionAdd* AtlasUv =
                AddPacuareWaterExpression<UMaterialExpressionAdd>(Material);
            AtlasUv->A.Expression = ScaledUv;
            AtlasUv->B.Expression = AtlasTileOrigin;
            UMaterialExpressionTextureSampleParameter2D* Sample =
                AddPacuareWaterExpression<UMaterialExpressionTextureSampleParameter2D>(Material);
            Sample->ParameterName = TEXT("WaterNormalAtlas");
            Sample->Texture = DefaultNormalTexture;
            Sample->SamplerType = SAMPLERTYPE_Normal;
            Sample->Coordinates.Expression = AtlasUv;
            Sample->Group = TEXT("PacuareRainforestWaterV1");
            return Sample;
        };
        UMaterialExpression* PrimarySample = SampleAtlas(WrappedUvPrimary);
        UMaterialExpression* OffsetSample = SampleAtlas(WrappedUvOffset);
        UMaterialExpressionComponentMask* WrappedPrimaryU =
            AddPacuareWaterExpression<UMaterialExpressionComponentMask>(Material);
        WrappedPrimaryU->Input.Expression = WrappedUvPrimary;
        WrappedPrimaryU->R = true;
        UMaterialExpressionSubtract* DistanceFromHalfPeriod =
            AddPacuareWaterExpression<UMaterialExpressionSubtract>(Material);
        DistanceFromHalfPeriod->A.Expression = WrappedPrimaryU;
        UMaterialExpressionConstant* HalfPeriodCenter =
            AddPacuareWaterExpression<UMaterialExpressionConstant>(Material);
        HalfPeriodCenter->R = 0.5f;
        DistanceFromHalfPeriod->B.Expression = HalfPeriodCenter;
        UMaterialExpressionAbs* AbsoluteDistance =
            AddPacuareWaterExpression<UMaterialExpressionAbs>(Material);
        AbsoluteDistance->Input.Expression = DistanceFromHalfPeriod;
        UMaterialExpressionMultiply* SeamBlend =
            AddPacuareWaterExpression<UMaterialExpressionMultiply>(Material);
        SeamBlend->A.Expression = AbsoluteDistance;
        UMaterialExpressionConstant* DoubleDistance =
            AddPacuareWaterExpression<UMaterialExpressionConstant>(Material);
        DoubleDistance->R = 2.0f;
        SeamBlend->B.Expression = DoubleDistance;
        UMaterialExpressionLinearInterpolate* ContinuousNormal =
            AddPacuareWaterExpression<UMaterialExpressionLinearInterpolate>(Material);
        ContinuousNormal->A.Expression = PrimarySample;
        ContinuousNormal->B.Expression = OffsetSample;
        ContinuousNormal->Alpha.Expression = SeamBlend;
        return ContinuousNormal;
    };

    UMaterialExpression* NormalA = AddNormalSample(0.58f, 1.65f, 0.022f, 0.004f);
    UMaterialExpression* NormalB = AddNormalSample(0.91f, 2.40f, -0.009f, 0.017f);
    UMaterialExpressionConstant3Vector* FlatNormal =
        AddPacuareWaterExpression<UMaterialExpressionConstant3Vector>(Material);
    FlatNormal->Constant = FLinearColor(0.0f, 0.0f, 1.0f, 0.0f);
    UMaterialExpression* WaterNormal = Lerp(
        FlatNormal,
        Lerp(NormalA, NormalB, Constant(0.42f)),
        Scalar(TEXT("NormalIntensity"), 0.20f));

    UMaterialExpression* BaseEmissive = Multiply(
        OpticallyVariedBaseColor,
        Scalar(TEXT("EmissiveFillScale"), 0.32f));
    UMaterialExpressionFresnel* ReflectionFresnel =
        AddPacuareWaterExpression<UMaterialExpressionFresnel>(Material);
    ReflectionFresnel->Exponent = 5.0f;
    ReflectionFresnel->BaseReflectFraction = 0.02f;
    UMaterialExpression* ReflectionFill = Multiply(
        Vector(TEXT("ReflectionTint"), FLinearColor(0.30f, 0.38f, 0.40f, 0.0f)),
        Multiply(
            ReflectionFresnel,
            Scalar(TEXT("ReflectionFillIntensity"), 0.06f)));

    UMaterialExpressionScalarParameter* Roughness =
        Scalar(TEXT("Roughness"), 0.32f);
    UMaterialExpressionScalarParameter* Specular =
        Scalar(TEXT("Specular"), 0.42f);
    UMaterialExpressionScalarParameter* Opacity =
        Scalar(TEXT("Opacity"), 0.28f);
    UMaterialExpressionScalarParameter* RefractionIor =
        Scalar(TEXT("RefractionIor"), 1.333f);

    UMaterialExpressionSingleLayerWaterMaterialOutput* WaterOutput =
        AddPacuareWaterExpression<UMaterialExpressionSingleLayerWaterMaterialOutput>(Material);
    WaterOutput->ScatteringCoefficients.Expression = Vector(
        TEXT("ScatteringCoefficients"),
        FLinearColor(0.00055f, 0.00080f, 0.00065f, 0.0f));
    WaterOutput->AbsorptionCoefficients.Expression = Vector(
        TEXT("AbsorptionCoefficients"),
        FLinearColor(0.0055f, 0.0020f, 0.0035f, 0.0f));
    WaterOutput->PhaseG.Expression = Scalar(TEXT("PhaseG"), 0.15f);
    WaterOutput->ColorScaleBehindWater.Expression = Vector(
        TEXT("ColorScaleBehindWater"),
        FLinearColor(0.60f, 0.65f, 0.55f, 0.0f));

    // Retain the shared instance interface at explicit zero defaults. Pacuare
    // has no validated river-specific solver visualization field to reuse.
    Scalar(TEXT("SolverFieldEnable"), 0.0f);
    Scalar(TEXT("SolverMacroNormalWeight"), 0.0f);
    Scalar(TEXT("SolverDepthColorWeight"), 0.0f);
    Scalar(TEXT("SolverFieldRoughnessWeight"), 0.0f);
    Scalar(TEXT("SolverFroudeAerationWeight"), 0.0f);
    Scalar(TEXT("SolverSpeedVisualGain"), 0.0f);
    Scalar(TEXT("SolverFroudeVisualGain"), 0.0f);
    Vector(TEXT("SolverDeepWaterTint"), FLinearColor(0.012f, 0.072f, 0.060f, 0.0f));
    Vector(TEXT("SolverAerationTint"), FLinearColor(0.74f, 0.82f, 0.76f, 0.0f));

    if (UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData())
    {
        ConnectPreviewMaterialColorInput(
            EditorOnlyData->BaseColor, OpticallyVariedBaseColor);
        ConnectPreviewMaterialColorInput(
            EditorOnlyData->EmissiveColor, Add(BaseEmissive, ReflectionFill));
        ConnectPreviewMaterialVectorInput(EditorOnlyData->Normal, WaterNormal);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Roughness, Roughness);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Specular, Specular);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Opacity, Opacity);
        ConnectPreviewMaterialScalarInput(EditorOnlyData->Refraction, RefractionIor);
    }

    Material->PostEditChange();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if (!Material->SetMaterialUsage(MATUSAGE_Water))
    {
        OutSummary += TEXT("Failed to enable Water usage for Pacuare rainforest water.\n");
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
        OutSummary += TEXT("Failed to save the Pacuare rainforest water material.\n");
        return nullptr;
    }
    FAssetCompilingManager::Get().FinishAllCompilation();
    OutSummary += TEXT(
        "Built Pacuare rainforest Single Layer Water with two moving normal "
        "scales, two world variation fields, and no visual displacement.\n");
    return Material;
}
} // namespace RaftSimEditorEnvironment
