#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionNoise.h"

namespace RaftSimEditorEnvironment
{
UMaterialExpression* BuildFutaleufuOrganicTemperateBaseColor(
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
        Parameter->Group = TEXT("FutaleufuOrganicTemperateV1");
        Add(Parameter);
        return Parameter;
    };
    auto Vector = [Material, &Add](const TCHAR* Name, const FLinearColor& Value)
    {
        UMaterialExpressionVectorParameter* Parameter =
            NewObject<UMaterialExpressionVectorParameter>(Material);
        Parameter->ParameterName = Name;
        Parameter->DefaultValue = Value;
        Parameter->Group = TEXT("FutaleufuOrganicTemperateV1");
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

    // Three incommensurate world-space fields preserve the registered source
    // macro color while breaking the former near-black plate into broad humid
    // forest value, moss/leaf-litter patches, and metre-scale mineral detail.
    // This graph shades only the existing reach-local Landscape.
    UMaterialExpressionNoise* MacroForestNoise = Noise(0.00018f, 3);
    UMaterialExpressionNoise* MossLitterNoise = Noise(0.00071f, 3);
    UMaterialExpressionNoise* FineSurfaceNoise = Noise(0.00420f, 2);

    UMaterialExpression* MacroValue = Lerp(
        Scalar(TEXT("FutaleufuMacroShadowScale"), 0.72f),
        Scalar(TEXT("FutaleufuMacroHighlightScale"), 1.15f),
        MacroForestNoise);
    UMaterialExpression* SourceVariation = Multiply(SourceBaseColor, MacroValue);

    UMaterialExpression* LeafLitter = Vector(
        TEXT("FutaleufuLeafLitterTint"),
        FLinearColor(0.17f, 0.105f, 0.040f, 1.0f));
    UMaterialExpression* Moss = Vector(
        TEXT("FutaleufuMossTint"),
        FLinearColor(0.065f, 0.155f, 0.060f, 1.0f));
    UMaterialExpression* ForestFloorPalette = Lerp(
        LeafLitter,
        Moss,
        MossLitterNoise);
    UMaterialExpression* ForestFloor = Lerp(
        SourceVariation,
        ForestFloorPalette,
        Scalar(TEXT("FutaleufuForestFloorPaletteWeight"), 0.34f));

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
        Scalar(TEXT("FutaleufuWetGraniteSlopeStart"), 0.045f);
    Add(SlopeAboveThreshold);
    UMaterialExpression* AmplifiedSlope = Multiply(
        SlopeAboveThreshold,
        Scalar(TEXT("FutaleufuWetGraniteSlopeGain"), 4.20f));
    UMaterialExpressionSaturate* WetGraniteSlopeMask =
        NewObject<UMaterialExpressionSaturate>(Material);
    WetGraniteSlopeMask->Input.Expression = AmplifiedSlope;
    Add(WetGraniteSlopeMask);

    UMaterialExpression* WetGranite = Vector(
        TEXT("FutaleufuWetGraniteTint"),
        FLinearColor(0.17f, 0.19f, 0.18f, 1.0f));
    UMaterialExpression* LichenGranite = Lerp(
        WetGranite,
        Vector(
            TEXT("FutaleufuLichenGraniteTint"),
            FLinearColor(0.105f, 0.155f, 0.090f, 1.0f)),
        Multiply(
            MossLitterNoise,
            Scalar(TEXT("FutaleufuGraniteLichenPatchStrength"), 0.56f)));
    UMaterialExpression* SlopeConditioned = Lerp(
        ForestFloor,
        LichenGranite,
        WetGraniteSlopeMask);

    UMaterialExpression* FineValue = Lerp(
        Scalar(TEXT("FutaleufuFineShadowScale"), 0.88f),
        Scalar(TEXT("FutaleufuFineHighlightScale"), 1.12f),
        FineSurfaceNoise);
    return Multiply(SlopeConditioned, FineValue);
}
} // namespace RaftSimEditorEnvironment
