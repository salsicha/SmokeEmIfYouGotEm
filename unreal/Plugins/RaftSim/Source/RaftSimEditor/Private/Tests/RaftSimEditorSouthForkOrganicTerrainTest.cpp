#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/Material.h"
#include "Materials/MaterialExpressionNoise.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimSouthForkOrganicFoothillTerrainTest,
    "RaftSim.M9.FSouthForkOrganicFoothillTerrain",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

namespace
{
void AuditOrganicMaterial(
    FAutomationTestBase& Test,
    UMaterial* Material,
    float ExpectedPaletteWeight,
    const FString& Label)
{
    Test.TestNotNull(Label + TEXT(" material exists"), Material);
    if (!Material)
    {
        return;
    }
    Test.TestEqual(Label + TEXT(" stays opaque"), Material->BlendMode, BLEND_Opaque);
    Test.TestTrue(
        Label + TEXT(" uses scene lighting"),
        Material->GetShadingModels().HasShadingModel(MSM_DefaultLit));
    const UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    Test.TestNotNull(Label + TEXT(" graph is inspectable"), EditorOnlyData);
    if (EditorOnlyData)
    {
        Test.TestNull(
            Label + TEXT(" organic shading never displaces terrain"),
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

    auto HasNoiseScale = [&NoiseScales](float ExpectedScale)
    {
        return NoiseScales.ContainsByPredicate(
            [ExpectedScale](float Value)
            {
                return FMath::IsNearlyEqual(Value, ExpectedScale, 0.000001f);
            });
    };
    Test.TestTrue(Label + TEXT(" has broad foothill breakup"), HasNoiseScale(0.00013f));
    Test.TestTrue(Label + TEXT(" has litter/grass breakup"), HasNoiseScale(0.00073f));
    Test.TestTrue(Label + TEXT(" has fine mineral breakup"), HasNoiseScale(0.00310f));

    const float* PaletteWeight =
        ScalarDefaults.Find(TEXT("SouthForkFoothillPaletteWeight"));
    Test.TestNotNull(Label + TEXT(" exposes its palette strength"), PaletteWeight);
    if (PaletteWeight)
    {
        Test.TestTrue(
            Label + TEXT(" keeps its authored palette strength"),
            FMath::IsNearlyEqual(*PaletteWeight, ExpectedPaletteWeight, 0.001f));
    }
    const FLinearColor* OakLitter =
        VectorDefaults.Find(TEXT("SouthForkOakLitterTint"));
    const FLinearColor* DryGrass =
        VectorDefaults.Find(TEXT("SouthForkDryGrassTint"));
    const FLinearColor* WeatheredGranite =
        VectorDefaults.Find(TEXT("SouthForkWeatheredGraniteTint"));
    Test.TestNotNull(Label + TEXT(" has oak litter"), OakLitter);
    Test.TestNotNull(Label + TEXT(" has dry grass"), DryGrass);
    Test.TestNotNull(Label + TEXT(" has weathered granite"), WeatheredGranite);
    if (OakLitter && DryGrass && WeatheredGranite)
    {
        Test.TestTrue(
            Label + TEXT(" dry grass is brighter than litter"),
            DryGrass->GetLuminance() > OakLitter->GetLuminance());
        Test.TestTrue(
            Label + TEXT(" granite remains neutral relative to grass"),
            FMath::Abs(WeatheredGranite->R - WeatheredGranite->G) <
                FMath::Abs(DryGrass->R - DryGrass->G));
    }
}
} // namespace

bool FRaftSimSouthForkOrganicFoothillTerrainTest::RunTest(
    const FString& Parameters)
{
    UMaterial* LandscapeMaterial = LoadObject<UMaterial>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/"
             "M_RaftSim_americansouthfork_physicalcorridor_SourceLandscapeCandidate."
             "M_RaftSim_americansouthfork_physicalcorridor_SourceLandscapeCandidate"));
    AuditOrganicMaterial(*this, LandscapeMaterial, 0.58f, TEXT("Review Landscape"));

    UMaterial* FullReachMaterial = LoadObject<UMaterial>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverTerrain."
             "M_RaftSim_PhotorealRiverTerrain"));
    AuditOrganicMaterial(*this, FullReachMaterial, 0.30f, TEXT("Runnable full reach"));
    return !HasAnyErrors();
}

#endif
