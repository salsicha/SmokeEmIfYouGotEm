#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionNoise.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimColoradoOrganicHanceTerrainTest,
    "RaftSim.M9.FColoradoOrganicHanceTerrain",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimColoradoOrganicHanceTerrainTest::RunTest(
    const FString& Parameters)
{
    UMaterial* Material = LoadObject<UMaterial>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/"
             "M_RaftSim_coloradoriver_physicalcorridor_SourceLandscapeCandidate."
             "M_RaftSim_coloradoriver_physicalcorridor_SourceLandscapeCandidate"));
    TestNotNull(TEXT("Colorado Hance Landscape material exists"), Material);
    if (!Material)
    {
        return false;
    }

    TestEqual(TEXT("Hance terrain stays opaque"), Material->BlendMode, BLEND_Opaque);
    TestTrue(
        TEXT("Hance terrain uses scene lighting"),
        Material->GetShadingModels().HasShadingModel(MSM_DefaultLit));
    TestTrue(TEXT("Hance terrain remains two-sided"), Material->TwoSided);
    TestTrue(TEXT("Hance detail normals remain tangent-space"), Material->bTangentSpaceNormal);
    const UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    TestNotNull(TEXT("Hance material exposes editor graph data"), EditorOnlyData);
    if (EditorOnlyData)
    {
        TestNull(
            TEXT("Organic Hance shading never displaces reviewed terrain"),
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
            if (FMath::IsNearlyEqual(Noise->Scale, 0.00014f, 0.000001f) ||
                FMath::IsNearlyEqual(Noise->Scale, 0.00053f, 0.000001f) ||
                FMath::IsNearlyEqual(Noise->Scale, 0.00230f, 0.000001f) ||
                FMath::IsNearlyEqual(Noise->Scale, 0.00680f, 0.000001f))
            {
                OrganicNoiseScales.Add(Noise->Scale);
            }
        }
    }
    TestEqual(TEXT("Four world scales break canyon repetition"), OrganicNoiseScales.Num(), 4);
    auto HasNoiseScale = [&OrganicNoiseScales](float ExpectedScale)
    {
        return OrganicNoiseScales.ContainsByPredicate(
            [ExpectedScale](float Value)
            {
                return FMath::IsNearlyEqual(Value, ExpectedScale, 0.000001f);
            });
    };
    TestTrue(TEXT("Broad canyon value field exists"), HasNoiseScale(0.00014f));
    TestTrue(TEXT("Mineral patch field exists"), HasNoiseScale(0.00053f));
    TestTrue(TEXT("Talus breakup field exists"), HasNoiseScale(0.00230f));
    TestTrue(TEXT("Fine grain field exists"), HasNoiseScale(0.00680f));

    auto TestScalar = [this, &ScalarDefaults](
                          const TCHAR* ParameterName,
                          float ExpectedValue)
    {
        const float* Value = ScalarDefaults.Find(ParameterName);
        TestNotNull(FString::Printf(TEXT("%s exists"), ParameterName), Value);
        if (Value)
        {
            TestTrue(
                FString::Printf(TEXT("%s keeps its reviewed value"), ParameterName),
                FMath::IsNearlyEqual(*Value, ExpectedValue, 0.001f));
        }
    };
    TestScalar(TEXT("ColoradoMacroShadowScale"), 0.58f);
    TestScalar(TEXT("ColoradoMacroHighlightScale"), 0.98f);
    TestScalar(TEXT("ColoradoCanyonPaletteWeight"), 0.52f);
    TestScalar(TEXT("ColoradoCliffSlopeStart"), 0.030f);
    TestScalar(TEXT("ColoradoCliffSlopeGain"), 4.80f);
    TestScalar(TEXT("ColoradoIronRockPatchStrength"), 0.44f);
    TestScalar(TEXT("ColoradoCliffPaletteWeight"), 0.78f);
    TestScalar(TEXT("ColoradoTalusPatchWeight"), 0.30f);
    TestScalar(TEXT("ColoradoFineShadowScale"), 0.86f);
    TestScalar(TEXT("ColoradoFineHighlightScale"), 1.08f);

    const FLinearColor* SandyBench = VectorDefaults.Find(TEXT("ColoradoSandyBenchTint"));
    const FLinearColor* DarkRock = VectorDefaults.Find(TEXT("ColoradoDarkBasementRockTint"));
    const FLinearColor* IronCliff = VectorDefaults.Find(TEXT("ColoradoIronCliffTint"));
    const FLinearColor* Talus = VectorDefaults.Find(TEXT("ColoradoPaleTalusTint"));
    TestNotNull(TEXT("Sandy bench response exists"), SandyBench);
    TestNotNull(TEXT("Dark rock response exists"), DarkRock);
    TestNotNull(TEXT("Iron cliff response exists"), IronCliff);
    TestNotNull(TEXT("Talus response exists"), Talus);
    if (SandyBench && DarkRock && IronCliff && Talus)
    {
        TestTrue(TEXT("Sandy bench stays warmer than dark rock"), SandyBench->R > DarkRock->R);
        TestTrue(TEXT("Dark rock stays near-neutral"), FMath::Abs(DarkRock->R - DarkRock->B) < 0.02f);
        TestTrue(TEXT("Iron cliff stays red-dominant"), IronCliff->R > IronCliff->G);
        TestTrue(TEXT("Talus stays brighter than dark rock"), Talus->R > DarkRock->R);
    }
    return !HasAnyErrors();
}

#endif // WITH_AUTOMATION_TESTS
