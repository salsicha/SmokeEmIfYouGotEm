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

    float Opacity = 0.0f;
    TestTrue(
        TEXT("The instance binds a water-volume opacity override"),
        Instance->GetScalarParameterValue(
            FMaterialParameterInfo(TEXT("Opacity")), Opacity));
    TestTrue(
        TEXT("Zambezi opacity remains transmissive but substantial"),
        Opacity >= 0.45f && Opacity <= 0.70f);
    return !HasAnyErrors();
}

#endif
