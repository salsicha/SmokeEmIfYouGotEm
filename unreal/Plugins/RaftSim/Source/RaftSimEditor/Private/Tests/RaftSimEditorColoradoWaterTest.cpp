#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionNoise.h"
#include "Materials/MaterialExpressionPanner.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimColoradoHanceWaterTest,
    "RaftSim.M9.FColoradoHanceWater",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimColoradoHanceWaterTest::RunTest(const FString& Parameters)
{
    UMaterialInstanceConstant* Instance = LoadObject<UMaterialInstanceConstant>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/"
             "MI_RaftSim_ColoradoRiver_PhysicalCorridorWaterCandidate."
             "MI_RaftSim_ColoradoRiver_PhysicalCorridorWaterCandidate"));
    TestNotNull(TEXT("Colorado Hance water instance exists"), Instance);
    if (!Instance)
    {
        return false;
    }

    UMaterial* Parent = Cast<UMaterial>(Instance->Parent);
    TestNotNull(TEXT("Colorado Hance water parent exists"), Parent);
    if (!Parent)
    {
        return false;
    }
    TestEqual(
        TEXT("Hance uses its isolated water parent"),
        Parent->GetPathName(),
        FString(TEXT("/Game/RaftSim/Environment/ColoradoRun/Water/Materials/"
                     "M_RaftSim_Colorado_HanceDefaultLitWater."
                     "M_RaftSim_Colorado_HanceDefaultLitWater")));
    TestTrue(
        TEXT("Hance water uses scene lighting"),
        Parent->GetShadingModels().HasShadingModel(MSM_DefaultLit));
    TestEqual(TEXT("Hance water remains opaque"), Parent->BlendMode, BLEND_Opaque);
    TestTrue(TEXT("Hance water remains two-sided"), Parent->TwoSided);
    TestTrue(TEXT("Hance water normals stay tangent-space"), Parent->bTangentSpaceNormal);
    const UMaterialEditorOnlyData* EditorOnlyData = Parent->GetEditorOnlyData();
    TestNotNull(TEXT("Hance water graph remains inspectable"), EditorOnlyData);
    if (EditorOnlyData)
    {
        TestNull(
            TEXT("Hance optics never displace cooked ribbon geometry"),
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
    TestTrue(TEXT("Reach-scale water variation exists"), NoiseScales.Contains(0.00029f));
    TestTrue(TEXT("Surface-scale water variation exists"), NoiseScales.Contains(0.00141f));

    auto TestScalar = [this, Instance](const TCHAR* ParameterName, float ExpectedValue)
    {
        float Value = 0.0f;
        TestTrue(
            FString::Printf(TEXT("%s is bound"), ParameterName),
            Instance->GetScalarParameterValue(FMaterialParameterInfo(ParameterName), Value));
        TestTrue(
            FString::Printf(TEXT("%s keeps its reviewed value"), ParameterName),
            FMath::IsNearlyEqual(Value, ExpectedValue, 0.001f));
    };
    TestScalar(TEXT("BaseColorScale"), 1.06f);
    TestScalar(TEXT("VertexTintWeight"), 0.74f);
    TestScalar(TEXT("EmissiveFillScale"), 0.20f);
    TestScalar(TEXT("ReflectionFillIntensity"), 0.14f);
    TestScalar(TEXT("Roughness"), 0.25f);
    TestScalar(TEXT("Specular"), 0.46f);
    TestScalar(TEXT("NormalIntensity"), 0.30f);
    TestScalar(TEXT("SurfaceVariationStrength"), 0.32f);
    TestScalar(TEXT("SolverFieldEnable"), 0.0f);
    TestScalar(TEXT("SolverMacroNormalWeight"), 0.0f);
    TestScalar(TEXT("SolverDepthColorWeight"), 0.0f);
    TestScalar(TEXT("SolverFieldRoughnessWeight"), 0.0f);
    TestScalar(TEXT("SolverFroudeAerationWeight"), 0.0f);

    UTexture* NormalAtlas = nullptr;
    TestTrue(
        TEXT("Colorado native normal atlas is bound"),
        Instance->GetTextureParameterValue(
            FMaterialParameterInfo(TEXT("WaterNormalAtlas")), NormalAtlas));
    TestNotNull(TEXT("Colorado native normal atlas exists"), NormalAtlas);
    if (NormalAtlas)
    {
        TestEqual(
            TEXT("Hance uses the Colorado water-normal atlas"),
            NormalAtlas->GetPathName(),
            FString(TEXT("/Game/RaftSim/Rendering/ProceduralTextureAtlases/Textures/"
                         "T_RaftSim_ColoradoRiver_NormalAtlas."
                         "T_RaftSim_ColoradoRiver_NormalAtlas")));
    }
    return !HasAnyErrors();
}

#endif // WITH_AUTOMATION_TESTS
