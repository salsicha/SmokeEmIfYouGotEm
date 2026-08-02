#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionAppendVector.h"
#include "Materials/MaterialExpressionNoise.h"
#include "Materials/MaterialExpressionPanner.h"

namespace RaftSimEditorEnvironment
{
namespace
{
template <typename ExpressionType>
ExpressionType* AddFutaleufuWaterExpression(UMaterial* Material)
{
    ExpressionType* Expression = NewObject<ExpressionType>(Material);
    Material->GetExpressionCollection().AddExpression(Expression);
    return Expression;
}
} // namespace

UMaterial* LoadOrCreateFutaleufuTerminatorWaterParent(FString& OutSummary)
{
    static const FString MaterialPackagePath =
        TEXT("/Game/RaftSim/Environment/FutaleufuRun/Water/Materials/"
             "M_RaftSim_Futaleufu_TerminatorDefaultLitWater");
    static const FString MaterialObjectName =
        TEXT("M_RaftSim_Futaleufu_TerminatorDefaultLitWater");
    const FString MaterialObjectPath = FString::Printf(
        TEXT("%s.%s"), *MaterialPackagePath, *MaterialObjectName);

    UPackage* Package = CreatePackage(*MaterialPackagePath);
    if (!Package)
    {
        OutSummary += TEXT("Failed to create the Futaleufu water package.\n");
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
        OutSummary += TEXT("Failed to create the Futaleufu water material.\n");
        return nullptr;
    }

    UTexture2D* DefaultNormalTexture = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Engine/EngineMaterials/DefaultNormal.DefaultNormal"));
    if (!DefaultNormalTexture)
    {
        OutSummary += TEXT("Failed to load the Futaleufu water normal fallback.\n");
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
            AddFutaleufuWaterExpression<UMaterialExpressionScalarParameter>(Material);
        Parameter->ParameterName = Name;
        Parameter->DefaultValue = Value;
        Parameter->Group = TEXT("FutaleufuTerminatorWaterV2");
        return Parameter;
    };
    auto Vector = [Material](const TCHAR* Name, const FLinearColor& Value)
    {
        UMaterialExpressionVectorParameter* Parameter =
            AddFutaleufuWaterExpression<UMaterialExpressionVectorParameter>(Material);
        Parameter->ParameterName = Name;
        Parameter->DefaultValue = Value;
        Parameter->Group = TEXT("FutaleufuTerminatorWaterV2");
        return Parameter;
    };
    auto Multiply = [Material](UMaterialExpression* A, UMaterialExpression* B)
    {
        UMaterialExpressionMultiply* Result =
            AddFutaleufuWaterExpression<UMaterialExpressionMultiply>(Material);
        Result->A.Expression = A;
        Result->B.Expression = B;
        return Result;
    };
    auto Add = [Material](UMaterialExpression* A, UMaterialExpression* B)
    {
        UMaterialExpressionAdd* Result =
            AddFutaleufuWaterExpression<UMaterialExpressionAdd>(Material);
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
            AddFutaleufuWaterExpression<UMaterialExpressionLinearInterpolate>(Material);
        Result->A.Expression = A;
        Result->B.Expression = B;
        Result->Alpha.Expression = Alpha;
        return Result;
    };
    auto Constant = [Material](float Value)
    {
        UMaterialExpressionConstant* Result =
            AddFutaleufuWaterExpression<UMaterialExpressionConstant>(Material);
        Result->R = Value;
        return Result;
    };

    // The physical ribbon's vertex RGB already contains the river-local cooked
    // depth, speed, Froude, and aeration interpretation. Do not sample a second
    // shader field: that previously injected the shared South Fork fallback
    // into Terminator. The material only adds optical response to these pixels.
    UMaterialExpressionVertexColor* VertexColor =
        AddFutaleufuWaterExpression<UMaterialExpressionVertexColor>(Material);
    UMaterialExpression* PhysicalSurfaceTint = Lerp(
        Vector(TEXT("SurfaceTint"), FLinearColor(0.025f, 0.185f, 0.225f, 0.0f)),
        VertexColor,
        Scalar(TEXT("VertexTintWeight"), 0.76f));
    UMaterialExpression* BaseColor = Multiply(
        PhysicalSurfaceTint,
        Scalar(TEXT("BaseColorScale"), 1.08f));

    // Three non-harmonic world scales break the broad dark plate without
    // inventing hydraulic crests or moving the reviewed ribbon geometry. The
    // third metre-scale field also drives bounded roughness variation, so the
    // surface does not retain one uniform plastic highlight response.
    UMaterialExpressionNoise* ReachVariation =
        AddFutaleufuWaterExpression<UMaterialExpressionNoise>(Material);
    ReachVariation->Scale = 0.00031f;
    ReachVariation->bTurbulence = true;
    ReachVariation->Levels = 3;
    ReachVariation->OutputMin = 0.0f;
    ReachVariation->OutputMax = 1.0f;
    UMaterialExpressionNoise* SurfaceVariation =
        AddFutaleufuWaterExpression<UMaterialExpressionNoise>(Material);
    SurfaceVariation->Scale = 0.00163f;
    SurfaceVariation->bTurbulence = true;
    SurfaceVariation->Levels = 2;
    SurfaceVariation->OutputMin = 0.0f;
    SurfaceVariation->OutputMax = 1.0f;
    UMaterialExpressionNoise* FineVariation =
        AddFutaleufuWaterExpression<UMaterialExpressionNoise>(Material);
    FineVariation->Scale = 0.00673f;
    FineVariation->bTurbulence = true;
    FineVariation->Levels = 2;
    FineVariation->OutputMin = 0.0f;
    FineVariation->OutputMax = 1.0f;
    UMaterialExpression* VariationField = Add(
        Add(
            Multiply(ReachVariation, Constant(0.54f)),
            Multiply(SurfaceVariation, Constant(0.30f))),
        Multiply(FineVariation, Constant(0.16f)));
    UMaterialExpression* PatternedColor = Lerp(
        Multiply(BaseColor, Constant(0.72f)),
        Multiply(BaseColor, Constant(1.28f)),
        VariationField);
    UMaterialExpression* OpticallyVariedBaseColor = Lerp(
        BaseColor,
        PatternedColor,
        Scalar(TEXT("SurfaceVariationStrength"), 0.44f));

    UMaterialExpressionVectorParameter* AtlasTileOriginParameter = Vector(
        TEXT("AtlasTileOrigin"), FLinearColor(0.0f, 0.5f, 0.0f, 0.0f));
    UMaterialExpressionVectorParameter* AtlasTileScaleParameter = Vector(
        TEXT("AtlasTileScale"),
        FLinearColor(1.0f / 3.0f, 1.0f / 2.0f, 0.0f, 0.0f));
    UMaterialExpressionComponentMask* AtlasTileOrigin =
        AddFutaleufuWaterExpression<UMaterialExpressionComponentMask>(Material);
    AtlasTileOrigin->Input.Expression = AtlasTileOriginParameter;
    AtlasTileOrigin->R = true;
    AtlasTileOrigin->G = true;
    UMaterialExpressionComponentMask* AtlasTileScale =
        AddFutaleufuWaterExpression<UMaterialExpressionComponentMask>(Material);
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
            AddFutaleufuWaterExpression<UMaterialExpressionTextureCoordinate>(Material);
        TexCoord->UTiling = UTiling;
        TexCoord->VTiling = VTiling;
        UMaterialExpression* BaseCoordinates = TexCoord;
        if (bSwapCoordinates)
        {
            UMaterialExpressionComponentMask* CoordinateU =
                AddFutaleufuWaterExpression<UMaterialExpressionComponentMask>(Material);
            CoordinateU->Input.Expression = TexCoord;
            CoordinateU->R = true;
            UMaterialExpressionComponentMask* CoordinateV =
                AddFutaleufuWaterExpression<UMaterialExpressionComponentMask>(Material);
            CoordinateV->Input.Expression = TexCoord;
            CoordinateV->G = true;
            UMaterialExpressionAppendVector* SwappedCoordinates =
                AddFutaleufuWaterExpression<UMaterialExpressionAppendVector>(Material);
            SwappedCoordinates->A.Expression = CoordinateV;
            SwappedCoordinates->B.Expression = CoordinateU;
            BaseCoordinates = SwappedCoordinates;
        }
        UMaterialExpressionPanner* Panner =
            AddFutaleufuWaterExpression<UMaterialExpressionPanner>(Material);
        Panner->SpeedX = SpeedX;
        Panner->SpeedY = SpeedY;
        Panner->Coordinate.Expression = BaseCoordinates;

        UMaterialExpressionFrac* WrappedUvPrimary =
            AddFutaleufuWaterExpression<UMaterialExpressionFrac>(Material);
        WrappedUvPrimary->Input.Expression = Panner;
        UMaterialExpressionConstant2Vector* HalfPeriodOffset =
            AddFutaleufuWaterExpression<UMaterialExpressionConstant2Vector>(Material);
        HalfPeriodOffset->R = 0.5f;
        HalfPeriodOffset->G = 0.0f;
        UMaterialExpressionAdd* OffsetTexCoord =
            AddFutaleufuWaterExpression<UMaterialExpressionAdd>(Material);
        OffsetTexCoord->A.Expression = Panner;
        OffsetTexCoord->B.Expression = HalfPeriodOffset;
        UMaterialExpressionFrac* WrappedUvOffset =
            AddFutaleufuWaterExpression<UMaterialExpressionFrac>(Material);
        WrappedUvOffset->Input.Expression = OffsetTexCoord;

        auto SampleAtlas =
            [Material, AtlasTileOrigin, AtlasTileScale, DefaultNormalTexture](
                UMaterialExpression* WrappedUv)
        {
            UMaterialExpressionMultiply* ScaledUv =
                AddFutaleufuWaterExpression<UMaterialExpressionMultiply>(Material);
            ScaledUv->A.Expression = WrappedUv;
            ScaledUv->B.Expression = AtlasTileScale;
            UMaterialExpressionAdd* AtlasUv =
                AddFutaleufuWaterExpression<UMaterialExpressionAdd>(Material);
            AtlasUv->A.Expression = ScaledUv;
            AtlasUv->B.Expression = AtlasTileOrigin;
            UMaterialExpressionTextureSampleParameter2D* Sample =
                AddFutaleufuWaterExpression<UMaterialExpressionTextureSampleParameter2D>(Material);
            Sample->ParameterName = TEXT("WaterNormalAtlas");
            Sample->Texture = DefaultNormalTexture;
            Sample->SamplerType = SAMPLERTYPE_Normal;
            Sample->Coordinates.Expression = AtlasUv;
            Sample->Group = TEXT("FutaleufuTerminatorWaterV2");
            return Sample;
        };
        UMaterialExpression* PrimarySample = SampleAtlas(WrappedUvPrimary);
        UMaterialExpression* OffsetSample = SampleAtlas(WrappedUvOffset);
        UMaterialExpressionComponentMask* WrappedPrimaryU =
            AddFutaleufuWaterExpression<UMaterialExpressionComponentMask>(Material);
        WrappedPrimaryU->Input.Expression = WrappedUvPrimary;
        WrappedPrimaryU->R = true;
        UMaterialExpressionConstant* HalfPeriodCenter =
            AddFutaleufuWaterExpression<UMaterialExpressionConstant>(Material);
        HalfPeriodCenter->R = 0.5f;
        UMaterialExpressionSubtract* DistanceFromHalfPeriod =
            AddFutaleufuWaterExpression<UMaterialExpressionSubtract>(Material);
        DistanceFromHalfPeriod->A.Expression = WrappedPrimaryU;
        DistanceFromHalfPeriod->B.Expression = HalfPeriodCenter;
        UMaterialExpressionAbs* AbsoluteDistance =
            AddFutaleufuWaterExpression<UMaterialExpressionAbs>(Material);
        AbsoluteDistance->Input.Expression = DistanceFromHalfPeriod;
        UMaterialExpressionMultiply* SeamBlend =
            AddFutaleufuWaterExpression<UMaterialExpressionMultiply>(Material);
        SeamBlend->A.Expression = AbsoluteDistance;
        UMaterialExpressionConstant* DoubleDistance =
            AddFutaleufuWaterExpression<UMaterialExpressionConstant>(Material);
        DoubleDistance->R = 2.0f;
        SeamBlend->B.Expression = DoubleDistance;
        UMaterialExpressionLinearInterpolate* ContinuousNormal =
            AddFutaleufuWaterExpression<UMaterialExpressionLinearInterpolate>(Material);
        ContinuousNormal->A.Expression = PrimarySample;
        ContinuousNormal->B.Expression = OffsetSample;
        ContinuousNormal->Alpha.Expression = SeamBlend;
        return ContinuousNormal;
    };

    UMaterialExpression* NormalA =
        AddNormalSample(0.64f, 1.72f, 0.029f, 0.004f, false);
    UMaterialExpression* NormalB =
        AddNormalSample(1.07f, 2.83f, -0.011f, 0.021f, false);
    UMaterialExpression* CrossCurrentNormal =
        AddNormalSample(2.17f, 0.79f, 0.017f, -0.026f, true);
    UMaterialExpressionConstant3Vector* FlatNormal =
        AddFutaleufuWaterExpression<UMaterialExpressionConstant3Vector>(Material);
    FlatNormal->Constant = FLinearColor(0.0f, 0.0f, 1.0f, 0.0f);
    UMaterialExpression* WaterNormal = Lerp(
        FlatNormal,
        Lerp(
            Lerp(NormalA, NormalB, Constant(0.43f)),
            CrossCurrentNormal,
            Scalar(TEXT("CrossCurrentNormalWeight"), 0.34f)),
        Scalar(TEXT("NormalIntensity"), 0.30f));

    UMaterialExpression* BaseEmissive = Multiply(
        OpticallyVariedBaseColor,
        Scalar(TEXT("EmissiveFillScale"), 0.14f));
    UMaterialExpressionFresnel* ReflectionFresnel =
        AddFutaleufuWaterExpression<UMaterialExpressionFresnel>(Material);
    ReflectionFresnel->Exponent = 5.0f;
    ReflectionFresnel->BaseReflectFraction = 0.02f;
    UMaterialExpression* ReflectionFill = Multiply(
        Vector(TEXT("ReflectionTint"), FLinearColor(0.32f, 0.53f, 0.63f, 0.0f)),
        Multiply(
            ReflectionFresnel,
            Scalar(TEXT("ReflectionFillIntensity"), 0.10f)));
    UMaterialExpressionScalarParameter* Roughness =
        Scalar(TEXT("Roughness"), 0.24f);
    UMaterialExpression* VariedRoughness = Lerp(
        Roughness,
        Add(
            Roughness,
            Scalar(TEXT("RoughnessVariationAmplitude"), 0.12f)),
        VariationField);
    UMaterialExpressionScalarParameter* Specular =
        Scalar(TEXT("Specular"), 0.46f);

    // Preserve the common instance interface as explicit, unbound metadata.
    // The cooked field has already been sampled once on the CPU-authored mesh.
    Scalar(TEXT("SolverFieldEnable"), 0.0f);
    Scalar(TEXT("SolverMacroNormalWeight"), 0.0f);
    Scalar(TEXT("SolverDepthColorWeight"), 0.0f);
    Scalar(TEXT("SolverFieldRoughnessWeight"), 0.0f);
    Scalar(TEXT("SolverFroudeAerationWeight"), 0.0f);
    Scalar(TEXT("SolverSpeedVisualGain"), 0.0f);
    Scalar(TEXT("SolverFroudeVisualGain"), 0.0f);
    Vector(TEXT("SolverDeepWaterTint"), FLinearColor(0.006f, 0.095f, 0.13f, 0.0f));
    Vector(TEXT("SolverAerationTint"), FLinearColor(0.88f, 0.95f, 0.96f, 0.0f));
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
        OutSummary += TEXT("Failed to enable Water usage for Futaleufu water.\n");
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
        OutSummary += TEXT("Failed to save the Futaleufu water material.\n");
        return nullptr;
    }
    FAssetCompilingManager::Get().FinishAllCompilation();
    OutSummary += TEXT(
        "Built Futaleufu Terminator opaque Default Lit water V2 with three "
        "moving normal directions, three world optical scales, varied "
        "roughness, CPU-authored cooked-field color authority, and no "
        "displacement.\n");
    return Material;
}
} // namespace RaftSimEditorEnvironment
