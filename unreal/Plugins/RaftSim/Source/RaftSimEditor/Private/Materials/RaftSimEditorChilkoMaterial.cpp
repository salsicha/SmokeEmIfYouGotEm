#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionNoise.h"

namespace RaftSimEditorEnvironment
{
UMaterialExpression* BuildChilkoOrganicLavaCanyonBaseColor(
    UMaterial* Material,
    UMaterialExpression* SourceBaseColor,
    UMaterialExpression* RotatedDetailAlbedo,
    UMaterialExpression* WetBankMask)
{
    if (!Material || !SourceBaseColor || !RotatedDetailAlbedo || !WetBankMask)
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
        Parameter->Group = TEXT("ChilkoOrganicLavaCanyonV2");
        Add(Parameter);
        return Parameter;
    };
    auto Vector = [Material, &Add](const TCHAR* Name, const FLinearColor& Value)
    {
        UMaterialExpressionVectorParameter* Parameter =
            NewObject<UMaterialExpressionVectorParameter>(Material);
        Parameter->ParameterName = Name;
        Parameter->DefaultValue = Value;
        Parameter->Group = TEXT("ChilkoOrganicLavaCanyonV2");
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
    auto Contrast = [Material, &Add, &Multiply, &Scalar](
                        UMaterialExpression* Input,
                        const TCHAR* ThresholdName,
                        float Threshold,
                        const TCHAR* GainName,
                        float Gain)
    {
        UMaterialExpressionSubtract* AboveThreshold =
            NewObject<UMaterialExpressionSubtract>(Material);
        AboveThreshold->A.Expression = Input;
        AboveThreshold->B.Expression = Scalar(ThresholdName, Threshold);
        Add(AboveThreshold);
        UMaterialExpressionSaturate* Result =
            NewObject<UMaterialExpressionSaturate>(Material);
        Result->Input.Expression = Multiply(
            AboveThreshold,
            Scalar(GainName, Gain));
        Add(Result);
        return Result;
    };

    // Seven non-harmonic world-space fields preserve registered source color
    // while breaking the nearly black bank plate into open-bench value,
    // dry-grass/mineral-soil patches, slope-bound basalt and scree, and
    // metre-scale mineral response. Three additional fields vary only the
    // existing source-conditioned wet-bank band with silt, gravel, oxidation,
    // and fine mineral response so the waterline does not read as a uniform
    // repeated strip. This graph shades the existing Landscape only; it never
    // invents terrain, rock, bathymetry, or collision geometry.
    UMaterialExpressionNoise* MacroBenchNoise = Noise(0.00016f, 3);
    UMaterialExpressionNoise* GroundPatchNoise = Noise(0.00059f, 3);
    UMaterialExpressionNoise* ScreePatchNoise = Noise(0.00270f, 2);
    UMaterialExpressionNoise* FineMineralNoise = Noise(0.00790f, 2);
    UMaterialExpressionNoise* WetBankMacroNoise = Noise(0.00091f, 3);
    UMaterialExpressionNoise* WetBankMesoNoise = Noise(0.00347f, 2);
    UMaterialExpressionNoise* WetBankFineNoise = Noise(0.01570f, 2);

    UMaterialExpression* RotatedDetailInfluence = Lerp(
        SourceBaseColor,
        RotatedDetailAlbedo,
        Scalar(TEXT("ChilkoRotatedDetailInfluence"), 0.24f));
    UMaterialExpression* NonRepeatingSourceBaseColor = Lerp(
        SourceBaseColor,
        RotatedDetailInfluence,
        GroundPatchNoise);

    UMaterialExpression* MacroValue = Lerp(
        Scalar(TEXT("ChilkoMacroShadowScale"), 0.72f),
        Scalar(TEXT("ChilkoMacroHighlightScale"), 1.28f),
        MacroBenchNoise);
    UMaterialExpression* SourceVariation = Multiply(
        NonRepeatingSourceBaseColor,
        MacroValue);

    UMaterialExpression* MineralSoil = Vector(
        TEXT("ChilkoMineralSoilTint"),
        FLinearColor(0.145f, 0.085f, 0.035f, 1.0f));
    UMaterialExpression* DryGrass = Vector(
        TEXT("ChilkoDryGrassTint"),
        FLinearColor(0.255f, 0.215f, 0.082f, 1.0f));
    UMaterialExpression* GroundPalette = Lerp(
        MineralSoil,
        DryGrass,
        GroundPatchNoise);
    UMaterialExpression* OpenBenchSurface = Lerp(
        SourceVariation,
        GroundPalette,
        Scalar(TEXT("ChilkoOpenBenchPaletteWeight"), 0.48f));

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
        Scalar(TEXT("ChilkoBasaltSlopeStart"), 0.035f);
    Add(SlopeAboveThreshold);
    UMaterialExpression* AmplifiedSlope = Multiply(
        SlopeAboveThreshold,
        Scalar(TEXT("ChilkoBasaltSlopeGain"), 4.60f));
    UMaterialExpressionSaturate* BasaltSlopeMask =
        NewObject<UMaterialExpressionSaturate>(Material);
    BasaltSlopeMask->Input.Expression = AmplifiedSlope;
    Add(BasaltSlopeMask);

    UMaterialExpression* WetBasalt = Vector(
        TEXT("ChilkoWetBasaltTint"),
        FLinearColor(0.070f, 0.086f, 0.082f, 1.0f));
    UMaterialExpression* OxidizedBasalt = Vector(
        TEXT("ChilkoOxidizedBasaltTint"),
        FLinearColor(0.185f, 0.112f, 0.058f, 1.0f));
    UMaterialExpression* BasaltPalette = Lerp(
        WetBasalt,
        OxidizedBasalt,
        Multiply(
            ScreePatchNoise,
            Scalar(TEXT("ChilkoBasaltOxidationPatchStrength"), 0.62f)));
    UMaterialExpression* SlopeConditioned = Lerp(
        OpenBenchSurface,
        BasaltPalette,
        Multiply(
            BasaltSlopeMask,
            Scalar(TEXT("ChilkoBasaltSlopePaletteWeight"), 0.84f)));

    UMaterialExpression* Scree = Vector(
        TEXT("ChilkoScreeTint"),
        FLinearColor(0.235f, 0.205f, 0.145f, 1.0f));
    UMaterialExpression* ScreeMask = Multiply(
        BasaltSlopeMask,
        Multiply(
            ScreePatchNoise,
            Scalar(TEXT("ChilkoScreePatchWeight"), 0.24f)));
    UMaterialExpression* RockAndScree = Lerp(
        SlopeConditioned,
        Scree,
        ScreeMask);

    UMaterialExpression* FineValue = Lerp(
        Scalar(TEXT("ChilkoFineShadowScale"), 0.86f),
        Scalar(TEXT("ChilkoFineHighlightScale"), 1.17f),
        FineMineralNoise);
    UMaterialExpression* OrganicDrySurface = Multiply(RockAndScree, FineValue);

    UMaterialExpression* WetBankSilt = Vector(
        TEXT("ChilkoWetBankSiltTint"),
        FLinearColor(0.032f, 0.046f, 0.040f, 1.0f));
    UMaterialExpression* WetBankGravel = Vector(
        TEXT("ChilkoWetBankGravelTint"),
        FLinearColor(0.235f, 0.188f, 0.118f, 1.0f));
    UMaterialExpression* WetBankOxide = Vector(
        TEXT("ChilkoWetBankOxideTint"),
        FLinearColor(0.205f, 0.084f, 0.034f, 1.0f));
    UMaterialExpression* WetBankMacroPatch = Contrast(
        WetBankMacroNoise,
        TEXT("ChilkoWetBankMacroPatchThreshold"),
        0.40f,
        TEXT("ChilkoWetBankMacroPatchGain"),
        3.80f);
    UMaterialExpression* WetBankMesoPatch = Contrast(
        WetBankMesoNoise,
        TEXT("ChilkoWetBankMesoPatchThreshold"),
        0.38f,
        TEXT("ChilkoWetBankMesoPatchGain"),
        4.20f);
    UMaterialExpression* WetBankSiltGravel = Lerp(
        WetBankSilt,
        WetBankGravel,
        WetBankMesoPatch);
    UMaterialExpression* WetBankPalette = Lerp(
        WetBankSiltGravel,
        WetBankOxide,
        Multiply(
            WetBankMacroPatch,
            Scalar(TEXT("ChilkoWetBankOxidePatchStrength"), 0.72f)));
    UMaterialExpression* SourceInfluencedWetBank = Lerp(
        OrganicDrySurface,
        WetBankPalette,
        Scalar(TEXT("ChilkoWetBankPaletteWeight"), 0.84f));
    UMaterialExpression* WetBankFineValue = Lerp(
        Scalar(TEXT("ChilkoWetBankFineShadowScale"), 0.70f),
        Scalar(TEXT("ChilkoWetBankFineHighlightScale"), 1.32f),
        WetBankFineNoise);
    UMaterialExpression* OrganicWetBank = Multiply(
        SourceInfluencedWetBank,
        WetBankFineValue);
    UMaterialExpression* OrganicWetBankMask = Multiply(
        WetBankMask,
        Scalar(TEXT("ChilkoWetBankOrganicBlendWeight"), 0.92f));
    return Lerp(OrganicDrySurface, OrganicWetBank, OrganicWetBankMask);
}
} // namespace RaftSimEditorEnvironment
