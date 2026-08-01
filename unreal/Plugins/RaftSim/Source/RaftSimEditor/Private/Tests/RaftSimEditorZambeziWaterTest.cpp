#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionPanner.h"
#include "Materials/MaterialExpressionSingleLayerWaterMaterialOutput.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimZambeziSingleLayerWaterTest,
    "RaftSim.M9.FZambeziSingleLayerWater",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimZambeziSingleLayerWaterTest::RunTest(const FString& Parameters)
{
    UMaterialInstanceConstant* Instance = LoadObject<UMaterialInstanceConstant>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/"
             "MI_RaftSim_Zambezi_PhysicalCorridorWaterCandidate."
             "MI_RaftSim_Zambezi_PhysicalCorridorWaterCandidate"));
    TestNotNull(TEXT("Zambezi physical-corridor water instance exists"), Instance);
    if (!Instance)
    {
        return false;
    }

    UMaterial* Parent = Cast<UMaterial>(Instance->Parent);
    TestNotNull(TEXT("Zambezi water uses a material parent"), Parent);
    if (!Parent)
    {
        return false;
    }

    TestEqual(
        TEXT("Zambezi water has its isolated parent"),
        Parent->GetPathName(),
        FString(TEXT("/Game/RaftSim/Environment/ZambeziRun/Water/Materials/"
                     "M_RaftSim_Zambezi_SingleLayerWater."
                     "M_RaftSim_Zambezi_SingleLayerWater")));
    TestTrue(
        TEXT("Zambezi water uses the Single Layer Water shading model"),
        Parent->GetShadingModels().HasShadingModel(MSM_SingleLayerWater));
    TestEqual(TEXT("Zambezi water remains an opaque water-volume surface"),
        Parent->BlendMode, BLEND_Opaque);

    int32 PannerCount = 0;
    int32 WaterOutputCount = 0;
    for (const TObjectPtr<UMaterialExpression>& Expression :
         Parent->GetExpressionCollection().Expressions)
    {
        PannerCount += Cast<UMaterialExpressionPanner>(Expression.Get()) ? 1 : 0;
        WaterOutputCount +=
            Cast<UMaterialExpressionSingleLayerWaterMaterialOutput>(Expression.Get())
            ? 1
            : 0;
    }
    TestEqual(TEXT("Two opposed normal layers move independently"), PannerCount, 2);
    TestEqual(TEXT("One physical water-volume output is bound"), WaterOutputCount, 1);

    auto TestScalarParameter = [this, Instance](
        const TCHAR* Label,
        const TCHAR* ParameterName,
        float ExpectedValue)
    {
        float Value = 0.0f;
        TestTrue(
            FString::Printf(TEXT("%s parameter is bound"), Label),
            Instance->GetScalarParameterValue(
                FMaterialParameterInfo(ParameterName), Value));
        TestTrue(
            FString::Printf(
                TEXT("%s uses the renderer-reviewed value %.3f (actual %.3f)"),
                Label,
                ExpectedValue,
                Value),
            FMath::IsNearlyEqual(Value, ExpectedValue, 0.001f));
    };
    TestScalarParameter(TEXT("Opacity"), TEXT("Opacity"), 0.62f);
    TestScalarParameter(TEXT("Roughness"), TEXT("Roughness"), 0.42f);
    TestScalarParameter(TEXT("Specular"), TEXT("Specular"), 0.28f);
    TestScalarParameter(TEXT("Normal intensity"), TEXT("NormalIntensity"), 0.20f);
    TestScalarParameter(
        TEXT("Reflection fill"), TEXT("ReflectionFillIntensity"), 0.04f);
    TestScalarParameter(
        TEXT("Emissive fill"), TEXT("EmissiveFillScale"), 0.0f);
    TestScalarParameter(
        TEXT("Surface variation"), TEXT("SurfaceVariationStrength"), 0.12f);
    return !HasAnyErrors();
}

#endif
