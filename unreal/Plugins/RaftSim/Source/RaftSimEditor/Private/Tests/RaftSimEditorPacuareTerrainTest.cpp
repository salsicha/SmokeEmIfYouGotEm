#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionNoise.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimPacuareOrganicRainforestTerrainTest,
    "RaftSim.M9.FPacuareOrganicRainforestTerrain",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimPacuareOrganicRainforestTerrainTest::RunTest(
    const FString& Parameters)
{
    UMaterial* Material = LoadObject<UMaterial>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/"
             "M_RaftSim_pacuare_SourceLandscapeCandidate."
             "M_RaftSim_pacuare_SourceLandscapeCandidate"));
    TestNotNull(TEXT("Pacuare source Landscape material exists"), Material);
    if (!Material)
    {
        return false;
    }

    TestEqual(TEXT("Pacuare terrain stays opaque"), Material->BlendMode, BLEND_Opaque);
    TestTrue(
        TEXT("Pacuare terrain uses scene lighting"),
        Material->GetShadingModels().HasShadingModel(MSM_DefaultLit));
    TestTrue(TEXT("Pacuare terrain remains two-sided"), Material->TwoSided);
    TestTrue(
        TEXT("Pacuare detail normals remain tangent-space"),
        Material->bTangentSpaceNormal);
    const UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    TestNotNull(TEXT("Pacuare material exposes editor graph data"), EditorOnlyData);
    if (EditorOnlyData)
    {
        TestNull(
            TEXT("Organic shading never displaces reviewed terrain"),
            EditorOnlyData->WorldPositionOffset.Expression);
    }

    TMap<FName, float> ScalarDefaults;
    TMap<FName, FLinearColor> VectorDefaults;
    TArray<float> NoiseScales;
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
            NoiseScales.Add(Noise->Scale);
        }
    }

    TestEqual(
        TEXT("Three world-space scales break terrain repetition"),
        NoiseScales.Num(),
        3);
    auto HasNoiseScale = [&NoiseScales](float ExpectedScale)
    {
        return NoiseScales.ContainsByPredicate(
            [ExpectedScale](float Value)
            {
                return FMath::IsNearlyEqual(Value, ExpectedScale, 0.000001f);
            });
    };
    TestTrue(TEXT("Broad rainforest macro field exists"), HasNoiseScale(0.00021f));
    TestTrue(TEXT("Moss and litter patch field exists"), HasNoiseScale(0.00095f));
    TestTrue(TEXT("Fine mineral field exists"), HasNoiseScale(0.00350f));

    auto TestScalar = [this, &ScalarDefaults](
                          const TCHAR* ParameterName,
                          float ExpectedValue)
    {
        const float* Value = ScalarDefaults.Find(ParameterName);
        TestNotNull(FString::Printf(TEXT("%s exists"), ParameterName), Value);
        if (Value)
        {
            TestTrue(
                FString::Printf(TEXT("%s keeps its accepted default"), ParameterName),
                FMath::IsNearlyEqual(*Value, ExpectedValue, 0.001f));
        }
    };
    TestScalar(TEXT("PacuareMacroShadowScale"), 0.62f);
    TestScalar(TEXT("PacuareMacroHighlightScale"), 1.16f);
    TestScalar(TEXT("PacuareForestFloorPaletteWeight"), 0.38f);
    TestScalar(TEXT("PacuareWetRockSlopeStart"), 0.025f);
    TestScalar(TEXT("PacuareWetRockSlopeGain"), 5.50f);
    TestScalar(TEXT("PacuareRockMossPatchStrength"), 0.62f);
    TestScalar(TEXT("PacuareFineShadowScale"), 0.86f);
    TestScalar(TEXT("PacuareFineHighlightScale"), 1.12f);

    const FLinearColor* LeafLitter =
        VectorDefaults.Find(TEXT("PacuareLeafLitterTint"));
    const FLinearColor* Moss = VectorDefaults.Find(TEXT("PacuareMossTint"));
    const FLinearColor* WetRock =
        VectorDefaults.Find(TEXT("PacuareWetRockTint"));
    TestNotNull(TEXT("Leaf-litter response exists"), LeafLitter);
    TestNotNull(TEXT("Moss response exists"), Moss);
    TestNotNull(TEXT("Wet-rock response exists"), WetRock);
    if (LeafLitter && Moss && WetRock)
    {
        TestTrue(TEXT("Leaf litter remains warmer than moss"), LeafLitter->R > Moss->R);
        TestTrue(TEXT("Moss remains the greenest ground response"), Moss->G > Moss->R);
        TestTrue(TEXT("Wet rock remains darker than moss"), WetRock->G < Moss->G);
    }
    return !HasAnyErrors();
}

#endif // WITH_AUTOMATION_TESTS
