#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionNoise.h"

namespace RaftSimEditorEnvironment
{
UMaterialExpression* BuildColoradoOrganicHanceBaseColor(
    UMaterial* Material,
    UMaterialExpression* SourceBaseColor)
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
        Parameter->Group = TEXT("ColoradoOrganicHanceV1");
        Add(Parameter);
        return Parameter;
    };
    auto Vector = [Material, &Add](const TCHAR* Name, const FLinearColor& Value)
    {
        UMaterialExpressionVectorParameter* Parameter =
            NewObject<UMaterialExpressionVectorParameter>(Material);
        Parameter->ParameterName = Name;
        Parameter->DefaultValue = Value;
        Parameter->Group = TEXT("ColoradoOrganicHanceV1");
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

    // The available Hance heightfield is interpreted reach-local geometry,
    // not surveyed canyon geology. Four incommensurate world-space fields
    // therefore add only review-gated mineral, bench, cliff, talus, and fine
    // value response over the registered source textures. They do not move
    // terrain or claim strata, bathymetry, collision, or geospatial authority.
    UMaterialExpressionNoise* CanyonValueNoise = Noise(0.00014f, 3);
    UMaterialExpressionNoise* MineralPatchNoise = Noise(0.00053f, 3);
    UMaterialExpressionNoise* TalusPatchNoise = Noise(0.00230f, 2);
    UMaterialExpressionNoise* FineGrainNoise = Noise(0.00680f, 2);

    UMaterialExpression* MacroValue = Lerp(
        Scalar(TEXT("ColoradoMacroShadowScale"), 0.58f),
        Scalar(TEXT("ColoradoMacroHighlightScale"), 0.98f),
        CanyonValueNoise);
    UMaterialExpression* SourceVariation = Multiply(SourceBaseColor, MacroValue);

    UMaterialExpression* SandyBench = Vector(
        TEXT("ColoradoSandyBenchTint"),
        FLinearColor(0.245f, 0.135f, 0.058f, 1.0f));
    UMaterialExpression* WeatheredRock = Vector(
        TEXT("ColoradoWeatheredRockTint"),
        FLinearColor(0.285f, 0.145f, 0.066f, 1.0f));
    UMaterialExpression* BenchPalette = Lerp(
        SandyBench,
        WeatheredRock,
        MineralPatchNoise);
    UMaterialExpression* OrganicBench = Lerp(
        SourceVariation,
        BenchPalette,
        Scalar(TEXT("ColoradoCanyonPaletteWeight"), 0.52f));

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
        Scalar(TEXT("ColoradoCliffSlopeStart"), 0.030f);
    Add(SlopeAboveThreshold);
    UMaterialExpression* AmplifiedSlope = Multiply(
        SlopeAboveThreshold,
        Scalar(TEXT("ColoradoCliffSlopeGain"), 4.80f));
    UMaterialExpressionSaturate* CliffSlopeMask =
        NewObject<UMaterialExpressionSaturate>(Material);
    CliffSlopeMask->Input.Expression = AmplifiedSlope;
    Add(CliffSlopeMask);

    UMaterialExpression* DarkBasementRock = Vector(
        TEXT("ColoradoDarkBasementRockTint"),
        FLinearColor(0.052f, 0.044f, 0.043f, 1.0f));
    UMaterialExpression* IronCliff = Vector(
        TEXT("ColoradoIronCliffTint"),
        FLinearColor(0.185f, 0.064f, 0.032f, 1.0f));
    UMaterialExpression* CliffPalette = Lerp(
        DarkBasementRock,
        IronCliff,
        Multiply(
            MineralPatchNoise,
            Scalar(TEXT("ColoradoIronRockPatchStrength"), 0.44f)));
    UMaterialExpression* CliffConditioned = Lerp(
        OrganicBench,
        CliffPalette,
        Multiply(
            CliffSlopeMask,
            Scalar(TEXT("ColoradoCliffPaletteWeight"), 0.78f)));

    UMaterialExpression* PaleTalus = Vector(
        TEXT("ColoradoPaleTalusTint"),
        FLinearColor(0.220f, 0.176f, 0.132f, 1.0f));
    UMaterialExpression* TalusMask = Multiply(
        CliffSlopeMask,
        Multiply(
            TalusPatchNoise,
            Scalar(TEXT("ColoradoTalusPatchWeight"), 0.30f)));
    UMaterialExpression* RockAndTalus = Lerp(
        CliffConditioned,
        PaleTalus,
        TalusMask);

    UMaterialExpression* FineValue = Lerp(
        Scalar(TEXT("ColoradoFineShadowScale"), 0.86f),
        Scalar(TEXT("ColoradoFineHighlightScale"), 1.08f),
        FineGrainNoise);
    return Multiply(RockAndTalus, FineValue);
}
} // namespace RaftSimEditorEnvironment
