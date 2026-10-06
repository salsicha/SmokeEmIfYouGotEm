#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionNoise.h"

namespace RaftSimEditorEnvironment
{
UMaterialExpression* BuildSouthForkOrganicFoothillBaseColor(
    UMaterial* Material,
    UMaterialExpression* SourceBaseColor,
    float DefaultPaletteWeight)
{
    if (!Material || !SourceBaseColor)
    {
        return nullptr;
    }

    auto Add = [Material](UMaterialExpression* Expression)
    {
        Material->GetExpressionCollection().AddExpression(Expression);
        return Expression;
    };
    auto Scalar = [Material, &Add](const TCHAR* Name, float Value)
    {
        UMaterialExpressionScalarParameter* Parameter =
            NewObject<UMaterialExpressionScalarParameter>(Material);
        Parameter->ParameterName = Name;
        Parameter->DefaultValue = Value;
        Parameter->Group = TEXT("SouthForkOrganicFoothillV1");
        Add(Parameter);
        return Parameter;
    };
    auto Vector = [Material, &Add](const TCHAR* Name, const FLinearColor& Value)
    {
        UMaterialExpressionVectorParameter* Parameter =
            NewObject<UMaterialExpressionVectorParameter>(Material);
        Parameter->ParameterName = Name;
        Parameter->DefaultValue = Value;
        Parameter->Group = TEXT("SouthForkOrganicFoothillV1");
        Add(Parameter);
        return Parameter;
    };
    auto Multiply = [Material, &Add](
                        UMaterialExpression* A,
                        UMaterialExpression* B)
    {
        UMaterialExpressionMultiply* Result =
            NewObject<UMaterialExpressionMultiply>(Material);
        Result->A.Expression = A;
        Result->B.Expression = B;
        Add(Result);
        return Result;
    };
    auto Lerp = [Material, &Add](
                    UMaterialExpression* A,
                    UMaterialExpression* B,
                    UMaterialExpression* Alpha)
    {
        UMaterialExpressionLinearInterpolate* Result =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        Result->A.Expression = A;
        Result->B.Expression = B;
        Result->Alpha.Expression = Alpha;
        Add(Result);
        return Result;
    };
    auto Noise = [Material, &Add](float Scale, int32 Levels)
    {
        UMaterialExpressionNoise* Result =
            NewObject<UMaterialExpressionNoise>(Material);
        Result->Scale = Scale;
        Result->bTurbulence = true;
        Result->Levels = Levels;
        Result->OutputMin = 0.0f;
        Result->OutputMax = 1.0f;
        Add(Result);
        return Result;
    };

    // Incommensurate world-space fields interrupt the repeated close-range
    // scan without adding another UV tile: broad foothill exposure, oak-litter
    // and dry-grass patches, then metre-scale mineral value. This is strictly
    // a material response over existing DEM/static-mesh terrain.
    UMaterialExpressionNoise* MacroFoothillNoise = Noise(0.00013f, 3);
    UMaterialExpressionNoise* LitterGrassNoise = Noise(0.00073f, 3);
    UMaterialExpressionNoise* FineMineralNoise = Noise(0.00310f, 2);

    UMaterialExpression* MacroValue = Lerp(
        Scalar(TEXT("SouthForkMacroShadowScale"), 0.66f),
        Scalar(TEXT("SouthForkMacroHighlightScale"), 1.10f),
        MacroFoothillNoise);
    UMaterialExpression* SourceVariation = Multiply(SourceBaseColor, MacroValue);

    UMaterialExpression* OakLitter = Vector(
        TEXT("SouthForkOakLitterTint"),
        FLinearColor(0.135f, 0.078f, 0.030f, 1.0f));
    UMaterialExpression* DryGrass = Vector(
        TEXT("SouthForkDryGrassTint"),
        FLinearColor(0.255f, 0.215f, 0.095f, 1.0f));
    UMaterialExpression* GraniticSoil = Vector(
        TEXT("SouthForkGraniticSoilTint"),
        FLinearColor(0.225f, 0.165f, 0.095f, 1.0f));
    UMaterialExpression* DryGroundMosaic = Lerp(
        OakLitter,
        DryGrass,
        LitterGrassNoise);
    UMaterialExpression* MineralGround = Lerp(
        DryGroundMosaic,
        GraniticSoil,
        Multiply(
            MacroFoothillNoise,
            Scalar(TEXT("SouthForkGraniticPatchStrength"), 0.54f)));
    UMaterialExpression* OrganicGround = Lerp(
        SourceVariation,
        MineralGround,
        Scalar(
            TEXT("SouthForkFoothillPaletteWeight"),
            FMath::Clamp(DefaultPaletteWeight, 0.0f, 1.0f)));

    UMaterialExpressionVertexNormalWS* VertexNormal =
        NewObject<UMaterialExpressionVertexNormalWS>(Material);
    Add(VertexNormal);
    UMaterialExpressionComponentMask* VertexNormalZ =
        NewObject<UMaterialExpressionComponentMask>(Material);
    VertexNormalZ->Input.Expression = VertexNormal;
    VertexNormalZ->B = true;
    Add(VertexNormalZ);
    UMaterialExpressionOneMinus* RawSlope =
        NewObject<UMaterialExpressionOneMinus>(Material);
    RawSlope->Input.Expression = VertexNormalZ;
    Add(RawSlope);
    UMaterialExpressionSubtract* SlopeAboveThreshold =
        NewObject<UMaterialExpressionSubtract>(Material);
    SlopeAboveThreshold->A.Expression = RawSlope;
    SlopeAboveThreshold->B.Expression =
        Scalar(TEXT("SouthForkWeatheredGraniteSlopeStart"), 0.035f);
    Add(SlopeAboveThreshold);
    UMaterialExpression* AmplifiedSlope = Multiply(
        SlopeAboveThreshold,
        Scalar(TEXT("SouthForkWeatheredGraniteSlopeGain"), 4.60f));
    UMaterialExpressionSaturate* GraniteSlopeMask =
        NewObject<UMaterialExpressionSaturate>(Material);
    GraniteSlopeMask->Input.Expression = AmplifiedSlope;
    Add(GraniteSlopeMask);

    UMaterialExpression* WeatheredGranite = Vector(
        TEXT("SouthForkWeatheredGraniteTint"),
        FLinearColor(0.245f, 0.235f, 0.205f, 1.0f));
    UMaterialExpression* LichenGranite = Lerp(
        WeatheredGranite,
        GraniticSoil,
        Multiply(
            LitterGrassNoise,
            Scalar(TEXT("SouthForkGraniteSoilPatchStrength"), 0.46f)));
    UMaterialExpression* SlopeConditioned = Lerp(
        OrganicGround,
        LichenGranite,
        GraniteSlopeMask);

    UMaterialExpression* FineValue = Lerp(
        Scalar(TEXT("SouthForkFineShadowScale"), 0.90f),
        Scalar(TEXT("SouthForkFineHighlightScale"), 1.08f),
        FineMineralNoise);
    return Multiply(SlopeConditioned, FineValue);
}
} // namespace RaftSimEditorEnvironment
