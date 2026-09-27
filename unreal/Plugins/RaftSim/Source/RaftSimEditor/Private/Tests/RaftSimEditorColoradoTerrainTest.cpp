#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionTextureSample.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimColoradoHanceEvidenceTerrainTest,
    "RaftSim.M9.FColoradoHanceEvidenceTerrain",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimColoradoHanceEvidenceTerrainTest::RunTest(
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
            TEXT("Hance terrain shading never displaces measured terrain"),
            EditorOnlyData->WorldPositionOffset.Expression);
    }

    // The evidence-based Hance Landscape takes its colour from the 2021
    // corridor orthophoto drape; the former procedural organic palette (and
    // the flat rock-slope tint) no longer applies to this reach.
    const UTexture* Drape = LoadObject<UTexture>(nullptr,
        TEXT("/Game/RaftSim/Environment/ColoradoRun/Terrain/T_RaftSim_ColoradoHance_EvidenceDrape."
             "T_RaftSim_ColoradoHance_EvidenceDrape"));
    TestNotNull(TEXT("Hance evidence drape texture exists"), Drape);
    bool bSamplesDrape = false;
    TSet<FName> ScalarNames;
    for (const TObjectPtr<UMaterialExpression>& Expression :
         Material->GetExpressionCollection().Expressions)
    {
        if (const UMaterialExpressionTextureSample* Sample =
                Cast<UMaterialExpressionTextureSample>(Expression.Get()))
        {
            bSamplesDrape |= Drape && Sample->Texture == Drape;
        }
        if (const UMaterialExpressionScalarParameter* Scalar =
                Cast<UMaterialExpressionScalarParameter>(Expression.Get()))
        {
            ScalarNames.Add(Scalar->ParameterName);
        }
    }
    TestTrue(TEXT("Hance terrain samples the 2021 orthophoto drape"), bSamplesDrape);
    TestFalse(TEXT("Retired organic canyon palette is not layered over the photo"),
        ScalarNames.Contains(TEXT("ColoradoCanyonPaletteWeight")) ||
        ScalarNames.Contains(TEXT("ColoradoCliffPaletteWeight")));
    return !HasAnyErrors();
}

#endif // WITH_AUTOMATION_TESTS
