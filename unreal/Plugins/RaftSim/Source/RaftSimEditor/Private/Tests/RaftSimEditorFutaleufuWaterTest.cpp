#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionNoise.h"
#include "Materials/MaterialExpressionPanner.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimFutaleufuTerminatorWaterTest,
    "RaftSim.M9.FFutaleufuTerminatorWater",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimFutaleufuTerminatorWaterTest::RunTest(
    const FString& Parameters)
{
    UMaterialInstanceConstant* Instance = LoadObject<UMaterialInstanceConstant>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/"
             "MI_RaftSim_Futaleufu_PhysicalCorridorWaterCandidate."
             "MI_RaftSim_Futaleufu_PhysicalCorridorWaterCandidate"));
    TestNotNull(TEXT("Futaleufu water instance exists"), Instance);
    if (!Instance)
    {
        return false;
    }

    UMaterial* Parent = Cast<UMaterial>(Instance->Parent);
    TestNotNull(TEXT("Futaleufu water parent exists"), Parent);
    if (!Parent)
    {
        return false;
    }
    TestEqual(
        TEXT("Futaleufu uses its isolated water parent"),
        Parent->GetPathName(),
        FString(TEXT("/Game/RaftSim/Environment/FutaleufuRun/Water/Materials/"
                     "M_RaftSim_Futaleufu_TerminatorDefaultLitWater."
                     "M_RaftSim_Futaleufu_TerminatorDefaultLitWater")));
    TestTrue(
        TEXT("Futaleufu water uses scene lighting"),
        Parent->GetShadingModels().HasShadingModel(MSM_DefaultLit));
    TestEqual(TEXT("Futaleufu water remains opaque"), Parent->BlendMode, BLEND_Opaque);
    TestTrue(TEXT("Futaleufu water remains two-sided"), Parent->TwoSided);
    TestTrue(TEXT("Futaleufu water normals remain tangent-space"), Parent->bTangentSpaceNormal);
    const UMaterialEditorOnlyData* EditorOnlyData = Parent->GetEditorOnlyData();
    TestNotNull(TEXT("Futaleufu water graph remains inspectable"), EditorOnlyData);
    if (EditorOnlyData)
    {
        TestNull(
            TEXT("Futaleufu optics never displace cooked ribbon geometry"),
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
    TestTrue(TEXT("Reach-scale water variation exists"), NoiseScales.Contains(0.00031f));
    TestTrue(TEXT("Surface-scale water variation exists"), NoiseScales.Contains(0.00163f));

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
    TestScalar(TEXT("BaseColorScale"), 1.08f);
    TestScalar(TEXT("VertexTintWeight"), 0.76f);
    TestScalar(TEXT("EmissiveFillScale"), 0.14f);
    TestScalar(TEXT("ReflectionFillIntensity"), 0.10f);
    TestScalar(TEXT("Roughness"), 0.24f);
    TestScalar(TEXT("Specular"), 0.46f);
    TestScalar(TEXT("NormalIntensity"), 0.30f);
    TestScalar(TEXT("SurfaceVariationStrength"), 0.30f);
    TestScalar(TEXT("SolverFieldEnable"), 0.0f);
    TestScalar(TEXT("SolverMacroNormalWeight"), 0.0f);
    TestScalar(TEXT("SolverDepthColorWeight"), 0.0f);
    TestScalar(TEXT("SolverFroudeAerationWeight"), 0.0f);

    UTexture* NormalAtlas = nullptr;
    TestTrue(
        TEXT("Futaleufu native normal atlas is bound"),
        Instance->GetTextureParameterValue(
            FMaterialParameterInfo(TEXT("WaterNormalAtlas")), NormalAtlas));
    TestNotNull(TEXT("Futaleufu native normal atlas exists"), NormalAtlas);
    if (NormalAtlas)
    {
        TestEqual(
            TEXT("Futaleufu never reuses Pacuare water normals"),
            NormalAtlas->GetPathName(),
            FString(TEXT("/Game/RaftSim/Rendering/ProceduralTextureAtlases/Textures/"
                         "T_RaftSim_Futaleufu_NormalAtlas."
                         "T_RaftSim_Futaleufu_NormalAtlas")));
    }
    return !HasAnyErrors();
}

#endif // WITH_AUTOMATION_TESTS
