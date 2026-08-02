#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionNoise.h"
#include "Materials/MaterialExpressionPanner.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimChilkoLavaCanyonWaterTest,
    "RaftSim.M9.FChilkoLavaCanyonWater",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimChilkoLavaCanyonWaterTest::RunTest(const FString& Parameters)
{
    UMaterialInstanceConstant* Instance = LoadObject<UMaterialInstanceConstant>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/"
             "MI_RaftSim_Chilko_PhysicalCorridorWaterCandidate."
             "MI_RaftSim_Chilko_PhysicalCorridorWaterCandidate"));
    TestNotNull(TEXT("Chilko water instance exists"), Instance);
    if (!Instance)
    {
        return false;
    }

    UMaterial* Parent = Cast<UMaterial>(Instance->Parent);
    TestNotNull(TEXT("Chilko water parent exists"), Parent);
    if (!Parent)
    {
        return false;
    }

    TestEqual(
        TEXT("Chilko uses its isolated water parent"),
        Parent->GetPathName(),
        FString(TEXT("/Game/RaftSim/Environment/ChilkoRun/Water/Materials/"
                     "M_RaftSim_Chilko_LavaCanyonDefaultLitWater."
                     "M_RaftSim_Chilko_LavaCanyonDefaultLitWater")));
    TestTrue(
        TEXT("Chilko water uses scene lighting"),
        Parent->GetShadingModels().HasShadingModel(MSM_DefaultLit));
    TestEqual(TEXT("Chilko water remains opaque"), Parent->BlendMode, BLEND_Opaque);
    TestTrue(TEXT("Chilko water remains two-sided"), Parent->TwoSided);
    TestTrue(TEXT("Chilko water normals remain tangent-space"), Parent->bTangentSpaceNormal);
    const UMaterialEditorOnlyData* EditorOnlyData = Parent->GetEditorOnlyData();
    TestNotNull(TEXT("Chilko water graph remains inspectable"), EditorOnlyData);
    if (EditorOnlyData)
    {
        TestNull(
            TEXT("Chilko optics never displace cooked ribbon geometry"),
            EditorOnlyData->WorldPositionOffset.Expression);
    }

    int32 PannerCount = 0;
    TArray<float> NoiseScales;
    for (const TObjectPtr<UMaterialExpression>& Expression :
         Parent->GetExpressionCollection().Expressions)
    {
        PannerCount += Cast<UMaterialExpressionPanner>(Expression.Get()) ? 1 : 0;
        if (const UMaterialExpressionNoise* Noise =
                Cast<UMaterialExpressionNoise>(Expression.Get()))
        {
            NoiseScales.Add(Noise->Scale);
        }
    }
    TestEqual(TEXT("Two moving normal layers exist"), PannerCount, 2);
    TestEqual(TEXT("Two world optical scales exist"), NoiseScales.Num(), 2);
    TestTrue(TEXT("Reach-scale water variation exists"), NoiseScales.Contains(0.00027f));
    TestTrue(TEXT("Surface-scale water variation exists"), NoiseScales.Contains(0.00147f));

    auto TestScalar = [this, Instance](
                          const TCHAR* ParameterName,
                          float ExpectedValue)
    {
        float Value = 0.0f;
        TestTrue(
            FString::Printf(TEXT("%s is bound"), ParameterName),
            Instance->GetScalarParameterValue(
                FMaterialParameterInfo(ParameterName), Value));
        TestTrue(
            FString::Printf(TEXT("%s keeps its reviewed value"), ParameterName),
            FMath::IsNearlyEqual(Value, ExpectedValue, 0.001f));
    };
    TestScalar(TEXT("BaseColorScale"), 1.10f);
    TestScalar(TEXT("VertexTintWeight"), 0.78f);
    TestScalar(TEXT("EmissiveFillScale"), 0.16f);
    TestScalar(TEXT("ReflectionFillIntensity"), 0.12f);
    TestScalar(TEXT("Roughness"), 0.22f);
    TestScalar(TEXT("Specular"), 0.48f);
    TestScalar(TEXT("NormalIntensity"), 0.34f);
    TestScalar(TEXT("SurfaceVariationStrength"), 0.34f);
    TestScalar(TEXT("SolverFieldEnable"), 0.0f);
    TestScalar(TEXT("SolverMacroNormalWeight"), 0.0f);
    TestScalar(TEXT("SolverDepthColorWeight"), 0.0f);
    TestScalar(TEXT("SolverFieldRoughnessWeight"), 0.0f);
    TestScalar(TEXT("SolverFroudeAerationWeight"), 0.0f);

    UTexture* NormalAtlas = nullptr;
    TestTrue(
        TEXT("Chilko native normal atlas is bound"),
        Instance->GetTextureParameterValue(
            FMaterialParameterInfo(TEXT("WaterNormalAtlas")), NormalAtlas));
    TestNotNull(TEXT("Chilko native normal atlas exists"), NormalAtlas);
    if (NormalAtlas)
    {
        TestEqual(
            TEXT("Chilko uses its own water-normal atlas"),
            NormalAtlas->GetPathName(),
            FString(TEXT("/Game/RaftSim/Rendering/ProceduralTextureAtlases/Textures/"
                         "T_RaftSim_Chilko_NormalAtlas."
                         "T_RaftSim_Chilko_NormalAtlas")));
    }
    return !HasAnyErrors();
}

#endif // WITH_AUTOMATION_TESTS
