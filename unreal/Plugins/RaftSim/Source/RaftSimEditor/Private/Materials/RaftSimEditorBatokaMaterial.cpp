#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionNoise.h"

namespace RaftSimEditorEnvironment
{
UMaterialExpression* BuildBatokaOrganicBasaltBaseColor(
    UMaterial* Material,
    UMaterialExpression* SourceBaseColor,
    UMaterialExpression* PrimaryMacroAlbedo,
    int32 PrimaryMacroOutputIndex,
    UMaterialExpression* SecondaryMacroAlbedo,
    int32 SecondaryMacroOutputIndex,
    UMaterialExpression* DetailAlbedo,
    int32 DetailOutputIndex)
{
    if (!Material || !SourceBaseColor || !PrimaryMacroAlbedo ||
        !SecondaryMacroAlbedo || !DetailAlbedo)
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
        Parameter->Group = TEXT("BatokaOrganicBasaltV16");
        Add(Parameter);
        return Parameter;
    };
    auto Vector = [Material, &Add](const TCHAR* Name, const FLinearColor& Value)
    {
        UMaterialExpressionVectorParameter* Parameter =
            NewObject<UMaterialExpressionVectorParameter>(Material);
        Parameter->ParameterName = Name;
        Parameter->DefaultValue = Value;
        Parameter->Group = TEXT("BatokaOrganicBasaltV16");
        Add(Parameter);
        return Parameter;
    };
    auto Multiply = [Material, &Add](
                        UMaterialExpression* A,
                        UMaterialExpression* B,
                        int32 AOutputIndex = 0,
                        int32 BOutputIndex = 0)
    {
        UMaterialExpressionMultiply* Result =
            NewObject<UMaterialExpressionMultiply>(Material);
        Result->A.Expression = A;
        Result->A.OutputIndex = AOutputIndex;
        Result->B.Expression = B;
        Result->B.OutputIndex = BOutputIndex;
        Add(Result);
        return Result;
    };
    auto Lerp = [Material, &Add](
                    UMaterialExpression* A,
                    UMaterialExpression* B,
                    UMaterialExpression* Alpha,
                    int32 AOutputIndex = 0,
                    int32 BOutputIndex = 0)
    {
        UMaterialExpressionLinearInterpolate* Result =
            NewObject<UMaterialExpressionLinearInterpolate>(Material);
        Result->A.Expression = A;
        Result->A.OutputIndex = AOutputIndex;
        Result->B.Expression = B;
        Result->B.OutputIndex = BOutputIndex;
        Result->Alpha.Expression = Alpha;
        Add(Result);
        return Result;
    };

    // The two incommensurate world-aligned albedo projections are blended by
    // a very-low-frequency world field. This breaks the visible square repeat
    // without displacing the reviewed terrain or changing collision authority.
    UMaterialExpressionNoise* MacroAntiTileNoise =
        NewObject<UMaterialExpressionNoise>(Material);
    MacroAntiTileNoise->Scale = 0.00013f;
    MacroAntiTileNoise->bTurbulence = true;
    MacroAntiTileNoise->Levels = 3;
    MacroAntiTileNoise->OutputMin = 0.0f;
    MacroAntiTileNoise->OutputMax = 1.0f;
    Add(MacroAntiTileNoise);
    UMaterialExpression* MacroAntiTileAlpha = Multiply(
        MacroAntiTileNoise,
        Scalar(TEXT("BatokaMacroAntiTileStrength"), 0.78f));
    UMaterialExpression* DeTiledMacro = Lerp(
        PrimaryMacroAlbedo,
        SecondaryMacroAlbedo,
        MacroAntiTileAlpha,
        PrimaryMacroOutputIndex,
        SecondaryMacroOutputIndex);

    UMaterialExpression* DarkMacro = Multiply(
        DeTiledMacro,
        Vector(TEXT("BatokaBasaltTint"), FLinearColor(0.38f, 0.42f, 0.48f, 1.0f)));
    UMaterialExpression* WeatheredMacro = Multiply(
        DeTiledMacro,
        Vector(
            TEXT("BatokaWeatheredInterflowTint"),
            FLinearColor(0.58f, 0.43f, 0.40f, 1.0f)));
    UMaterialExpression* WeatheringAlpha = Multiply(
        MacroAntiTileNoise,
        Scalar(TEXT("BatokaWeatheringVariationStrength"), 0.28f));
    UMaterialExpression* WeatheredSurface =
        Lerp(DarkMacro, WeatheredMacro, WeatheringAlpha);

    // A separate finer field varies mineral value at roughly cliff-feature
    // scale. It keeps the result irregular while the explicit bounds prevent
    // crushed black faces or returning the former chalky highlights.
    UMaterialExpressionNoise* FineMineralNoise =
        NewObject<UMaterialExpressionNoise>(Material);
    FineMineralNoise->Scale = 0.00072f;
    FineMineralNoise->bTurbulence = true;
    FineMineralNoise->Levels = 2;
    FineMineralNoise->OutputMin = 0.0f;
    FineMineralNoise->OutputMax = 1.0f;
    Add(FineMineralNoise);
    UMaterialExpression* MineralValueScale = Lerp(
        Scalar(TEXT("BatokaMineralShadowScale"), 0.78f),
        Scalar(TEXT("BatokaMineralHighlightScale"), 1.02f),
        FineMineralNoise);
    UMaterialExpression* OrganicMacro =
        Multiply(WeatheredSurface, MineralValueScale);
    UMaterialExpression* MacroBaseColor = Lerp(
        SourceBaseColor,
        OrganicMacro,
        Scalar(TEXT("BatokaMacroWeight"), 0.86f));

    UMaterialExpression* ScaledDetail = Multiply(
        DetailAlbedo,
        Scalar(TEXT("BatokaDetailColorScale"), 0.86f),
        DetailOutputIndex);
    return Lerp(
        MacroBaseColor,
        ScaledDetail,
        Scalar(TEXT("BatokaDetailColorWeight"), 0.07f));
}

UMaterialExpression* BuildBatokaOrganicBasaltColorCoverage(
    UMaterial* Material,
    UMaterialExpression* RockSlopeMask)
{
    if (!Material || !RockSlopeMask)
    {
        return nullptr;
    }
    UMaterialExpressionScalarParameter* CoverageFloor =
        NewObject<UMaterialExpressionScalarParameter>(Material);
    CoverageFloor->ParameterName = TEXT("BatokaTerrainColorCoverageFloor");
    CoverageFloor->DefaultValue = 0.78f;
    CoverageFloor->Group = TEXT("BatokaOrganicBasaltV16");
    Material->GetExpressionCollection().AddExpression(CoverageFloor);
    UMaterialExpressionAdd* BiasedCoverage =
        NewObject<UMaterialExpressionAdd>(Material);
    BiasedCoverage->A.Expression = RockSlopeMask;
    BiasedCoverage->B.Expression = CoverageFloor;
    Material->GetExpressionCollection().AddExpression(BiasedCoverage);
    UMaterialExpressionSaturate* Coverage =
        NewObject<UMaterialExpressionSaturate>(Material);
    Coverage->Input.Expression = BiasedCoverage;
    Material->GetExpressionCollection().AddExpression(Coverage);
    return Coverage;
}
} // namespace RaftSimEditorEnvironment
