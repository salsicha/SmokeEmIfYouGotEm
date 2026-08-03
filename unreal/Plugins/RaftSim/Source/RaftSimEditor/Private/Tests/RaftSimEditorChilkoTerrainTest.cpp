#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionNoise.h"
#include "Materials/MaterialExpressionLandscapeLayerCoords.h"
#include "Materials/MaterialExpressionTextureSampleParameter2D.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimChilkoOrganicLavaCanyonTerrainTest,
    "RaftSim.M9.FChilkoOrganicLavaCanyonTerrain",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimChilkoOrganicLavaCanyonTerrainTest::RunTest(
    const FString& Parameters)
{
    UMaterial* Material = LoadObject<UMaterial>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/"
             "M_RaftSim_chilkoriverlavacanyon_physicalcorridor_SourceLandscapeCandidate."
             "M_RaftSim_chilkoriverlavacanyon_physicalcorridor_SourceLandscapeCandidate"));
    TestNotNull(TEXT("Chilko source Landscape material exists"), Material);
    if (!Material)
    {
        return false;
    }

    TestEqual(TEXT("Chilko terrain stays opaque"), Material->BlendMode, BLEND_Opaque);
    TestTrue(
        TEXT("Chilko terrain uses scene lighting"),
        Material->GetShadingModels().HasShadingModel(MSM_DefaultLit));
    TestTrue(TEXT("Chilko terrain remains two-sided"), Material->TwoSided);
    TestTrue(
        TEXT("Chilko detail normals remain tangent-space"),
        Material->bTangentSpaceNormal);
    const UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    TestNotNull(TEXT("Chilko material exposes editor graph data"), EditorOnlyData);
    if (EditorOnlyData)
    {
        TestNull(
            TEXT("Organic shading never displaces reviewed terrain"),
            EditorOnlyData->WorldPositionOffset.Expression);
    }

    TMap<FName, float> ScalarDefaults;
    TMap<FName, FLinearColor> VectorDefaults;
    TArray<float> OrganicNoiseScales;
    bool bHasRotatedDetailProjection = false;
    bool bHasRotatedDetailTextureSample = false;
    for (const TObjectPtr<UMaterialExpression>& Expression :
         Material->GetExpressionCollection().Expressions)
    {
        if (const UMaterialExpressionScalarParameter* Scalar =
                Cast<UMaterialExpressionScalarParameter>(Expression.Get()))
        {
            ScalarDefaults.Add(Scalar->ParameterName, Scalar->DefaultValue);
        }
        if (const UMaterialExpressionVectorParameter* Vector =
                Cast<UMaterialExpressionVectorParameter>(Expression.Get()))
        {
            VectorDefaults.Add(Vector->ParameterName, Vector->DefaultValue);
        }
        if (const UMaterialExpressionNoise* Noise =
                Cast<UMaterialExpressionNoise>(Expression.Get()))
        {
            if (FMath::IsNearlyEqual(Noise->Scale, 0.00016f, 0.000001f) ||
                FMath::IsNearlyEqual(Noise->Scale, 0.00059f, 0.000001f) ||
                FMath::IsNearlyEqual(Noise->Scale, 0.00270f, 0.000001f) ||
                FMath::IsNearlyEqual(Noise->Scale, 0.00790f, 0.000001f) ||
                FMath::IsNearlyEqual(Noise->Scale, 0.00091f, 0.000001f) ||
                FMath::IsNearlyEqual(Noise->Scale, 0.00347f, 0.000001f) ||
                FMath::IsNearlyEqual(Noise->Scale, 0.01570f, 0.000001f))
            {
                OrganicNoiseScales.Add(Noise->Scale);
            }
        }
        if (const UMaterialExpressionLandscapeLayerCoords* Coordinates =
                Cast<UMaterialExpressionLandscapeLayerCoords>(Expression.Get()))
        {
            bHasRotatedDetailProjection |=
                FMath::IsNearlyEqual(Coordinates->MappingScale, 217.0f, 0.001f) &&
                FMath::IsNearlyEqual(Coordinates->MappingRotation, 37.0f, 0.001f);
        }
        if (const UMaterialExpressionTextureSampleParameter2D* TextureSample =
                Cast<UMaterialExpressionTextureSampleParameter2D>(Expression.Get()))
        {
            bHasRotatedDetailTextureSample |=
                TextureSample->ParameterName == TEXT("ChilkoRotatedBroadDetailAlbedo");
        }
    }

    TestEqual(
        TEXT("Seven world-space scales break terrain and wet-bank repetition"),
        OrganicNoiseScales.Num(),
        7);
    auto HasNoiseScale = [&OrganicNoiseScales](float ExpectedScale)
    {
        return OrganicNoiseScales.ContainsByPredicate(
            [ExpectedScale](float Value)
            {
                return FMath::IsNearlyEqual(Value, ExpectedScale, 0.000001f);
            });
    };
    TestTrue(TEXT("Broad open-bench field exists"), HasNoiseScale(0.00016f));
    TestTrue(TEXT("Dry-ground patch field exists"), HasNoiseScale(0.00059f));
    TestTrue(TEXT("Basalt and scree field exists"), HasNoiseScale(0.00270f));
    TestTrue(TEXT("Fine mineral field exists"), HasNoiseScale(0.00790f));
    TestTrue(TEXT("Wet-bank macro sediment field exists"), HasNoiseScale(0.00091f));
    TestTrue(TEXT("Wet-bank meso gravel field exists"), HasNoiseScale(0.00347f));
    TestTrue(TEXT("Wet-bank fine mineral field exists"), HasNoiseScale(0.01570f));
    TestTrue(TEXT("Non-harmonic rotated detail projection exists"), bHasRotatedDetailProjection);
    TestTrue(TEXT("Rotated broad detail albedo exists"), bHasRotatedDetailTextureSample);

    auto TestScalar = [this, &ScalarDefaults](
                          const TCHAR* ParameterName,
                          float ExpectedValue)
    {
        const float* Value = ScalarDefaults.Find(ParameterName);
        TestNotNull(FString::Printf(TEXT("%s exists"), ParameterName), Value);
        if (Value)
        {
            TestTrue(
                FString::Printf(TEXT("%s keeps its retained default"), ParameterName),
                FMath::IsNearlyEqual(*Value, ExpectedValue, 0.001f));
        }
    };
    TestScalar(TEXT("ChilkoRotatedDetailInfluence"), 0.24f);
    TestScalar(TEXT("ChilkoMacroShadowScale"), 0.72f);
    TestScalar(TEXT("ChilkoMacroHighlightScale"), 1.28f);
    TestScalar(TEXT("ChilkoOpenBenchPaletteWeight"), 0.48f);
    TestScalar(TEXT("ChilkoBasaltSlopeStart"), 0.035f);
    TestScalar(TEXT("ChilkoBasaltSlopeGain"), 4.60f);
    TestScalar(TEXT("ChilkoBasaltOxidationPatchStrength"), 0.62f);
    TestScalar(TEXT("ChilkoBasaltSlopePaletteWeight"), 0.84f);
    TestScalar(TEXT("ChilkoScreePatchWeight"), 0.24f);
    TestScalar(TEXT("ChilkoFineShadowScale"), 0.86f);
    TestScalar(TEXT("ChilkoFineHighlightScale"), 1.17f);
    TestScalar(TEXT("ChilkoWetBankMacroPatchThreshold"), 0.40f);
    TestScalar(TEXT("ChilkoWetBankMacroPatchGain"), 3.80f);
    TestScalar(TEXT("ChilkoWetBankMesoPatchThreshold"), 0.38f);
    TestScalar(TEXT("ChilkoWetBankMesoPatchGain"), 4.20f);
    TestScalar(TEXT("ChilkoWetBankOxidePatchStrength"), 0.72f);
    TestScalar(TEXT("ChilkoWetBankPaletteWeight"), 0.84f);
    TestScalar(TEXT("ChilkoWetBankFineShadowScale"), 0.70f);
    TestScalar(TEXT("ChilkoWetBankFineHighlightScale"), 1.32f);
    TestScalar(TEXT("ChilkoWetBankOrganicBlendWeight"), 0.92f);

    const FLinearColor* Soil = VectorDefaults.Find(TEXT("ChilkoMineralSoilTint"));
    const FLinearColor* Grass = VectorDefaults.Find(TEXT("ChilkoDryGrassTint"));
    const FLinearColor* WetBasalt = VectorDefaults.Find(TEXT("ChilkoWetBasaltTint"));
    const FLinearColor* OxidizedBasalt =
        VectorDefaults.Find(TEXT("ChilkoOxidizedBasaltTint"));
    const FLinearColor* Scree = VectorDefaults.Find(TEXT("ChilkoScreeTint"));
    const FLinearColor* WetBankSilt =
        VectorDefaults.Find(TEXT("ChilkoWetBankSiltTint"));
    const FLinearColor* WetBankGravel =
        VectorDefaults.Find(TEXT("ChilkoWetBankGravelTint"));
    const FLinearColor* WetBankOxide =
        VectorDefaults.Find(TEXT("ChilkoWetBankOxideTint"));
    TestNotNull(TEXT("Mineral-soil response exists"), Soil);
    TestNotNull(TEXT("Dry-grass response exists"), Grass);
    TestNotNull(TEXT("Wet-basalt response exists"), WetBasalt);
    TestNotNull(TEXT("Oxidized-basalt response exists"), OxidizedBasalt);
    TestNotNull(TEXT("Scree response exists"), Scree);
    TestNotNull(TEXT("Wet-bank silt response exists"), WetBankSilt);
    TestNotNull(TEXT("Wet-bank gravel response exists"), WetBankGravel);
    TestNotNull(TEXT("Wet-bank oxidation response exists"), WetBankOxide);
    if (Soil && Grass && WetBasalt && OxidizedBasalt && Scree)
    {
        TestTrue(TEXT("Dry grass stays warmer than wet basalt"), Grass->R > WetBasalt->R);
        TestTrue(TEXT("Wet basalt stays neutral"), FMath::Abs(WetBasalt->R - WetBasalt->B) < 0.02f);
        TestTrue(TEXT("Oxidized basalt stays iron-warm"), OxidizedBasalt->R > OxidizedBasalt->G);
        TestTrue(TEXT("Scree stays brighter than wet basalt"), Scree->R > WetBasalt->R);
    }
    if (WetBankSilt && WetBankGravel && WetBankOxide)
    {
        TestTrue(
            TEXT("Wet-bank gravel remains brighter than fine silt"),
            WetBankGravel->R > WetBankSilt->R);
        TestTrue(
            TEXT("Wet-bank oxidation remains iron-warm"),
            WetBankOxide->R > WetBankOxide->G);
        TestTrue(
            TEXT("Wet-bank silt remains muted and neutral"),
            FMath::Abs(WetBankSilt->R - WetBankSilt->B) < 0.01f);
    }
    return !HasAnyErrors();
}

#endif // WITH_AUTOMATION_TESTS
