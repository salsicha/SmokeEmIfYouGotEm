#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Engine/Texture2D.h"
#include "Materials/MaterialExpressionNoise.h"
#include "Materials/MaterialExpressionTextureBase.h"
#include "Materials/MaterialExpressionVectorParameter.h"
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

    // The evidence Terminator reach (futaleufu-terminator-evidence.md) is
    // coloured by the Sentinel-2 10 m drape; the invented procedural palette
    // (noise fields, litter/moss/granite tints) must not come back over it.
    const UTexture2D* EvidenceDrape = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/FutaleufuRun/Terrain/T_RaftSim_FutaleufuTerminator_EvidenceDrape."
             "T_RaftSim_FutaleufuTerminator_EvidenceDrape"));
    TestNotNull(TEXT("Futaleufu evidence Sentinel-2 drape exists"), EvidenceDrape);
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
            bHasPaletteTint |= Vector->ParameterName.ToString().StartsWith(TEXT("Futaleufu"));
        }
    }
    TestTrue(TEXT("Futaleufu terrain samples the evidence Sentinel-2 drape"), bSamplesEvidenceDrape);
    TestEqual(TEXT("No procedural noise palette over the satellite colour"), NoiseCount, 0);
    TestFalse(TEXT("No invented litter/moss/granite tints over the satellite colour"), bHasPaletteTint);
    return !HasAnyErrors();
}

#endif // WITH_AUTOMATION_TESTS
