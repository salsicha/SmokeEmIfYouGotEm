#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Engine/Texture2D.h"
#include "Materials/MaterialExpressionNoise.h"
#include "Materials/MaterialExpressionTextureBase.h"
#include "Materials/MaterialExpressionVectorParameter.h"
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

    // The evidence Lava Canyon reach (chilko-lava-canyon-evidence.md) is
    // coloured by the Sentinel-2 10 m drape; the invented procedural palette
    // (seven noise fields, basalt/scree/grass/wet-bank tints) must not come
    // back over it.
    const UTexture2D* EvidenceDrape = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ChilkoRun/Terrain/T_RaftSim_ChilkoLavaCanyon_EvidenceDrape."
             "T_RaftSim_ChilkoLavaCanyon_EvidenceDrape"));
    TestNotNull(TEXT("Chilko evidence Sentinel-2 drape exists"), EvidenceDrape);
    bool bSamplesEvidenceDrape = false;
    int32 NoiseCount = 0;
    bool bHasPaletteTint = false;
    for (const TObjectPtr<UMaterialExpression>& Expression :
         Material->GetExpressionCollection().Expressions)
    {
        if (const UMaterialExpressionTextureBase* Texture =
                Cast<UMaterialExpressionTextureBase>(Expression.Get()))
        {
            bSamplesEvidenceDrape |= EvidenceDrape && Texture->Texture == EvidenceDrape;
        }
        NoiseCount += Cast<UMaterialExpressionNoise>(Expression.Get()) ? 1 : 0;
        if (const UMaterialExpressionVectorParameter* Vector =
                Cast<UMaterialExpressionVectorParameter>(Expression.Get()))
        {
            bHasPaletteTint |= Vector->ParameterName.ToString().StartsWith(TEXT("Chilko"));
        }
    }
    TestTrue(TEXT("Chilko terrain samples the evidence Sentinel-2 drape"), bSamplesEvidenceDrape);
    TestEqual(TEXT("No procedural noise palette over the satellite colour"), NoiseCount, 0);
    TestFalse(TEXT("No invented basalt/scree/grass tints over the satellite colour"), bHasPaletteTint);
    return !HasAnyErrors();
}

#endif // WITH_AUTOMATION_TESTS
