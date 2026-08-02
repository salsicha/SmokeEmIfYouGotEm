#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionNoise.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimFutaleufuOrganicTemperateTerrainTest,
    "RaftSim.M9.FFutaleufuOrganicTemperateTerrain",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimFutaleufuOrganicTemperateTerrainTest::RunTest(
    const FString& Parameters)
{
    UMaterial* Material = LoadObject<UMaterial>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/"
             "M_RaftSim_futaleufuterminator_physicalcorridor_SourceLandscapeCandidate."
             "M_RaftSim_futaleufuterminator_physicalcorridor_SourceLandscapeCandidate"));
    TestNotNull(TEXT("Futaleufu source Landscape material exists"), Material);
    if (!Material)
    {
        return false;
    }

    TestEqual(
        TEXT("Futaleufu terrain stays opaque"),
        Material->BlendMode,
        BLEND_Opaque);
    TestTrue(
        TEXT("Futaleufu terrain uses scene lighting"),
        Material->GetShadingModels().HasShadingModel(MSM_DefaultLit));
    TestTrue(TEXT("Futaleufu terrain remains two-sided"), Material->TwoSided);
    TestTrue(
        TEXT("Futaleufu detail normals remain tangent-space"),
        Material->bTangentSpaceNormal);
    const UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    TestNotNull(TEXT("Futaleufu material exposes editor graph data"), EditorOnlyData);
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
            if (FMath::IsNearlyEqual(Noise->Scale, 0.00018f, 0.000001f) ||
                FMath::IsNearlyEqual(Noise->Scale, 0.00071f, 0.000001f) ||
                FMath::IsNearlyEqual(Noise->Scale, 0.00420f, 0.000001f))
            {
                OrganicNoiseScales.Add(Noise->Scale);
            }
        }
    }

    TestEqual(
        TEXT("Three world-space scales break terrain repetition"),
        OrganicNoiseScales.Num(),
        3);
    auto HasNoiseScale = [&OrganicNoiseScales](float ExpectedScale)
    {
        return OrganicNoiseScales.ContainsByPredicate(
            [ExpectedScale](float Value)
            {
                return FMath::IsNearlyEqual(Value, ExpectedScale, 0.000001f);
            });
    };
    TestTrue(TEXT("Broad temperate macro field exists"), HasNoiseScale(0.00018f));
    TestTrue(TEXT("Moss and litter patch field exists"), HasNoiseScale(0.00071f));
    TestTrue(TEXT("Fine mineral field exists"), HasNoiseScale(0.00420f));

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
    TestScalar(TEXT("FutaleufuMacroShadowScale"), 0.72f);
    TestScalar(TEXT("FutaleufuMacroHighlightScale"), 1.15f);
    TestScalar(TEXT("FutaleufuForestFloorPaletteWeight"), 0.34f);
    TestScalar(TEXT("FutaleufuWetGraniteSlopeStart"), 0.045f);
    TestScalar(TEXT("FutaleufuWetGraniteSlopeGain"), 4.20f);
    TestScalar(TEXT("FutaleufuGraniteLichenPatchStrength"), 0.56f);
    TestScalar(TEXT("FutaleufuFineShadowScale"), 0.88f);
    TestScalar(TEXT("FutaleufuFineHighlightScale"), 1.12f);

    const FLinearColor* LeafLitter =
        VectorDefaults.Find(TEXT("FutaleufuLeafLitterTint"));
    const FLinearColor* Moss =
        VectorDefaults.Find(TEXT("FutaleufuMossTint"));
    const FLinearColor* WetGranite =
        VectorDefaults.Find(TEXT("FutaleufuWetGraniteTint"));
    const FLinearColor* LichenGranite =
        VectorDefaults.Find(TEXT("FutaleufuLichenGraniteTint"));
    TestNotNull(TEXT("Leaf-litter response exists"), LeafLitter);
    TestNotNull(TEXT("Moss response exists"), Moss);
    TestNotNull(TEXT("Wet-granite response exists"), WetGranite);
    TestNotNull(TEXT("Lichen-granite response exists"), LichenGranite);
    if (LeafLitter && Moss && WetGranite && LichenGranite)
    {
        TestTrue(TEXT("Leaf litter remains warmer than moss"), LeafLitter->R > Moss->R);
        TestTrue(TEXT("Moss remains the greenest floor response"), Moss->G > Moss->R);
        TestTrue(
            TEXT("Wet granite remains neutral"),
            FMath::Abs(WetGranite->R - WetGranite->B) < 0.02f);
        TestTrue(
            TEXT("Lichen granite remains greener than red"),
            LichenGranite->G > LichenGranite->R);
    }
    return !HasAnyErrors();
}

#endif // WITH_AUTOMATION_TESTS
