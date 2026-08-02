#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionNoise.h"
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
                FMath::IsNearlyEqual(Noise->Scale, 0.00790f, 0.000001f))
            {
                OrganicNoiseScales.Add(Noise->Scale);
            }
        }
    }

    TestEqual(
        TEXT("Four world-space scales break terrain repetition"),
        OrganicNoiseScales.Num(),
        4);
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
    TestScalar(TEXT("ChilkoMacroShadowScale"), 0.78f);
    TestScalar(TEXT("ChilkoMacroHighlightScale"), 1.22f);
    TestScalar(TEXT("ChilkoOpenBenchPaletteWeight"), 0.40f);
    TestScalar(TEXT("ChilkoBasaltSlopeStart"), 0.035f);
    TestScalar(TEXT("ChilkoBasaltSlopeGain"), 4.60f);
    TestScalar(TEXT("ChilkoBasaltOxidationPatchStrength"), 0.62f);
    TestScalar(TEXT("ChilkoBasaltSlopePaletteWeight"), 0.84f);
    TestScalar(TEXT("ChilkoScreePatchWeight"), 0.24f);
    TestScalar(TEXT("ChilkoFineShadowScale"), 0.90f);
    TestScalar(TEXT("ChilkoFineHighlightScale"), 1.13f);

    const FLinearColor* Soil = VectorDefaults.Find(TEXT("ChilkoMineralSoilTint"));
    const FLinearColor* Grass = VectorDefaults.Find(TEXT("ChilkoDryGrassTint"));
    const FLinearColor* WetBasalt = VectorDefaults.Find(TEXT("ChilkoWetBasaltTint"));
    const FLinearColor* OxidizedBasalt =
        VectorDefaults.Find(TEXT("ChilkoOxidizedBasaltTint"));
    const FLinearColor* Scree = VectorDefaults.Find(TEXT("ChilkoScreeTint"));
    TestNotNull(TEXT("Mineral-soil response exists"), Soil);
    TestNotNull(TEXT("Dry-grass response exists"), Grass);
    TestNotNull(TEXT("Wet-basalt response exists"), WetBasalt);
    TestNotNull(TEXT("Oxidized-basalt response exists"), OxidizedBasalt);
    TestNotNull(TEXT("Scree response exists"), Scree);
    if (Soil && Grass && WetBasalt && OxidizedBasalt && Scree)
    {
        TestTrue(TEXT("Dry grass stays warmer than wet basalt"), Grass->R > WetBasalt->R);
        TestTrue(TEXT("Wet basalt stays neutral"), FMath::Abs(WetBasalt->R - WetBasalt->B) < 0.02f);
        TestTrue(TEXT("Oxidized basalt stays iron-warm"), OxidizedBasalt->R > OxidizedBasalt->G);
        TestTrue(TEXT("Scree stays brighter than wet basalt"), Scree->R > WetBasalt->R);
    }
    return !HasAnyErrors();
}

#endif // WITH_AUTOMATION_TESTS
