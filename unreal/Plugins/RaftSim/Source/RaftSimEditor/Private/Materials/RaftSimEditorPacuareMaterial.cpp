#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionNoise.h"

namespace RaftSimEditorEnvironment
{
UMaterialExpression* BuildPacuareOrganicRainforestBaseColor(
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
        Parameter->Group = TEXT("PacuareOrganicRainforestV1");
        Add(Parameter);
        return Parameter;
    };
    auto Vector = [Material, &Add](const TCHAR* Name, const FLinearColor& Value)
    {
        UMaterialExpressionVectorParameter* Parameter =
            NewObject<UMaterialExpressionVectorParameter>(Material);
        Parameter->ParameterName = Name;
        Parameter->DefaultValue = Value;
        Parameter->Group = TEXT("PacuareOrganicRainforestV1");
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

    // These incommensurate world-space fields replace the repeated green plate
    // with broad humid-forest value changes, patchy moss/leaf litter, and
    // metre-scale mineral variation. They only shade the existing Landscape.
    UMaterialExpressionNoise* MacroForestNoise = Noise(0.00021f, 3);
    UMaterialExpressionNoise* MossLitterNoise = Noise(0.00095f, 3);
    UMaterialExpressionNoise* FineSurfaceNoise = Noise(0.00350f, 2);

    UMaterialExpression* MacroValue = Lerp(
        Scalar(TEXT("PacuareMacroShadowScale"), 0.62f),
        Scalar(TEXT("PacuareMacroHighlightScale"), 1.16f),
        MacroForestNoise);
    UMaterialExpression* SourceVariation = Multiply(SourceBaseColor, MacroValue);

    UMaterialExpression* LeafLitter = Vector(
        TEXT("PacuareLeafLitterTint"),
        FLinearColor(0.22f, 0.135f, 0.060f, 1.0f));
    UMaterialExpression* Moss = Vector(
        TEXT("PacuareMossTint"),
        FLinearColor(0.13f, 0.235f, 0.075f, 1.0f));
    UMaterialExpression* ForestFloorPalette = Lerp(
        LeafLitter,
        Moss,
        MossLitterNoise);
    UMaterialExpression* ForestFloor = Lerp(
        SourceVariation,
        ForestFloorPalette,
        Scalar(TEXT("PacuareForestFloorPaletteWeight"), 0.38f));

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
        Scalar(TEXT("PacuareWetRockSlopeStart"), 0.025f);
    Add(SlopeAboveThreshold);
    UMaterialExpression* AmplifiedSlope = Multiply(
        SlopeAboveThreshold,
        Scalar(TEXT("PacuareWetRockSlopeGain"), 5.50f));
    UMaterialExpressionSaturate* WetRockSlopeMask =
        NewObject<UMaterialExpressionSaturate>(Material);
    WetRockSlopeMask->Input.Expression = AmplifiedSlope;
    Add(WetRockSlopeMask);

    UMaterialExpression* WetRock = Vector(
        TEXT("PacuareWetRockTint"),
        FLinearColor(0.080f, 0.095f, 0.075f, 1.0f));
    UMaterialExpression* MossedRock = Lerp(
        WetRock,
        Multiply(Moss, Scalar(TEXT("PacuareRockMossValueScale"), 0.72f)),
        Multiply(
            MossLitterNoise,
            Scalar(TEXT("PacuareRockMossPatchStrength"), 0.62f)));
    UMaterialExpression* SlopeConditioned = Lerp(
        ForestFloor,
        MossedRock,
        WetRockSlopeMask);

    UMaterialExpression* FineValue = Lerp(
        Scalar(TEXT("PacuareFineShadowScale"), 0.86f),
        Scalar(TEXT("PacuareFineHighlightScale"), 1.12f),
        FineSurfaceNoise);
    return Multiply(SlopeConditioned, FineValue);
}
} // namespace RaftSimEditorEnvironment
