#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Engine/Texture2D.h"
#include "Materials/MaterialInstanceConstant.h"
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
    TestEqual(
        TEXT("Chilko capture water transmits the riverbed"),
        Parent->BlendMode,
        BLEND_Translucent);
    TestEqual(
        TEXT("Chilko capture water uses per-pixel translucent lighting"),
        Parent->TranslucencyLightingMode,
        TLM_SurfacePerPixelLighting);
    TestTrue(TEXT("Chilko water remains two-sided"), Parent->TwoSided);
    TestTrue(TEXT("Chilko water normals remain tangent-space"), Parent->bTangentSpaceNormal);
    const UMaterialEditorOnlyData* EditorOnlyData = Parent->GetEditorOnlyData();
    TestNotNull(TEXT("Chilko water graph remains inspectable"), EditorOnlyData);
    if (EditorOnlyData)
    {
        TestNull(
            TEXT("Chilko optics never displace cooked ribbon geometry"),
            EditorOnlyData->WorldPositionOffset.Expression);
        TestNotNull(
            TEXT("Chilko capture water binds depth/bank opacity"),
            EditorOnlyData->Opacity.Expression);
        TestNotNull(
            TEXT("Chilko capture water binds physical refraction"),
            EditorOnlyData->Refraction.Expression);
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
    TestEqual(TEXT("Three moving normal layers exist"), PannerCount, 3);
    TestEqual(TEXT("Three world optical scales exist"), NoiseScales.Num(), 3);
    TestTrue(TEXT("Reach-scale water variation exists"), NoiseScales.Contains(0.00027f));
    TestTrue(TEXT("Surface-scale water variation exists"), NoiseScales.Contains(0.00147f));
    TestTrue(TEXT("Fine-scale water variation exists"), NoiseScales.Contains(0.00611f));

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
    TestScalar(TEXT("BaseColorScale"), 0.94f);
    TestScalar(TEXT("VertexTintWeight"), 0.78f);
    TestScalar(TEXT("EmissiveFillScale"), 0.060f);
    TestScalar(TEXT("ReflectionFillIntensity"), 0.06f);
    TestScalar(TEXT("Roughness"), 0.34f);
    TestScalar(TEXT("Specular"), 0.34f);
    TestScalar(TEXT("Opacity"), 0.90f);
    TestScalar(TEXT("RefractionIor"), 1.333f);
    TestScalar(TEXT("NormalIntensity"), 0.26f);
    TestScalar(TEXT("SurfaceVariationStrength"), 0.30f);
    TestScalar(TEXT("CrossCurrentNormalWeight"), 0.38f);
    TestScalar(TEXT("RoughnessVariationAmplitude"), 0.14f);
    TestScalar(TEXT("SolverFieldEnable"), 0.0f);
    TestScalar(TEXT("SolverMacroNormalWeight"), 0.0f);
    TestScalar(TEXT("SolverDepthColorWeight"), 0.0f);
    TestScalar(TEXT("SolverFieldRoughnessWeight"), 0.0f);
    TestScalar(TEXT("SolverFroudeAerationWeight"), 0.0f);

    const RaftSimEditorEnvironment::FRaftSimLandscapeCandidateWaterSettings WaterSettings =
        RaftSimEditorEnvironment::GetLandscapeCandidateWaterSettings(
            TEXT("chilko_river_lava_canyon"));
    TestEqual(TEXT("Chilko ribbon has 48 cross-current samples"), WaterSettings.RibbonCrossSectionSteps, 48);
    TestTrue(TEXT("Chilko CPU chop keeps reviewed scale"), FMath::IsNearlyEqual(WaterSettings.AnalyticChopScale, 0.72f));
    TestTrue(TEXT("Chilko cross-current chop keeps reviewed amplitude"), FMath::IsNearlyEqual(WaterSettings.CrossCurrentChopAmplitudeCm, 7.0f));
    TestTrue(TEXT("Chilko embeds restrained aeration into the water surface"), FMath::IsNearlyEqual(WaterSettings.EmbeddedAerationWeight, 0.18f));

    UTexture* NormalAtlas = nullptr;
    TestTrue(
        TEXT("Chilko river-local flow normal is bound"),
        Instance->GetTextureParameterValue(
            FMaterialParameterInfo(TEXT("WaterNormalAtlas")), NormalAtlas));
    TestNotNull(TEXT("Chilko river-local flow normal exists"), NormalAtlas);
    if (NormalAtlas)
    {
        TestEqual(
            TEXT("Chilko uses its first-party flow normal"),
            NormalAtlas->GetPathName(),
            FString(TEXT("/Game/RaftSim/Environment/ChilkoRun/Water/Textures/"
                         "T_RaftSim_ChilkoLavaCanyonWaterV1_FlowNormal."
                         "T_RaftSim_ChilkoLavaCanyonWaterV1_FlowNormal")));
    }

    FString AuthoringSummary;
    UMaterialInstanceConstant* LiveInstance =
        RaftSimEditorEnvironment::LoadOrCreateChilkoLavaCanyonLiveWaterInstance(
            AuthoringSummary);
    TestNotNull(TEXT("Chilko live-volume authoring succeeds"), LiveInstance);
    if (LiveInstance)
    {
        TestNotNull(TEXT("Chilko live-volume parent exists"), LiveInstance->Parent.Get());
        if (LiveInstance->Parent)
        {
            TestTrue(
                TEXT("Chilko uses the shared raft-transmitting parent"),
                LiveInstance->Parent->GetPathName().Contains(
                    TEXT("M_RaftSim_SouthForkRaftTransmissionWater")));
        }
        UTexture* LiveFlowNormal = nullptr;
        UTexture* LiveFoamLace = nullptr;
        TestTrue(
            TEXT("Chilko live volume binds the river-local flow normal"),
            LiveInstance->GetTextureParameterValue(
                FMaterialParameterInfo(TEXT("WaterFlowNormalPrimary")),
                LiveFlowNormal));
        TestTrue(
            TEXT("Chilko live volume binds solver-masked foam lace"),
            LiveInstance->GetTextureParameterValue(
                FMaterialParameterInfo(TEXT("WhitewaterFoamLace")),
                LiveFoamLace));
        TestTrue(
            TEXT("Chilko live flow normal resolves to its own texture"),
            LiveFlowNormal && LiveFlowNormal->GetPathName().Contains(
                TEXT("T_RaftSim_ChilkoLavaCanyonWaterV1_FlowNormal")));
        TestTrue(
            TEXT("Chilko live foam lace resolves to its own texture"),
            LiveFoamLace && LiveFoamLace->GetPathName().Contains(
                TEXT("T_RaftSim_ChilkoLavaCanyonWaterV1_FoamLace")));
        float FoamCoverage = 0.0f;
        TestTrue(
            TEXT("Chilko live volume binds restrained hydraulic foam coverage"),
            LiveInstance->GetScalarParameterValue(
                FMaterialParameterInfo(TEXT("HydraulicFoamCoverageGain")),
                FoamCoverage));
        TestTrue(
            TEXT("Chilko hydraulic foam coverage remains reviewed"),
            FMath::IsNearlyEqual(FoamCoverage, 0.64f, 0.001f));

        auto TestLiveScalar = [this, LiveInstance](
                                  const TCHAR* ParameterName,
                                  float ExpectedValue)
        {
            float Value = 0.0f;
            TestTrue(
                FString::Printf(TEXT("live %s is bound"), ParameterName),
                LiveInstance->GetScalarParameterValue(
                    FMaterialParameterInfo(ParameterName), Value));
            TestTrue(
                FString::Printf(
                    TEXT("live %s keeps its reviewed V3 value"),
                    ParameterName),
                FMath::IsNearlyEqual(Value, ExpectedValue, 0.001f));
        };
        TestLiveScalar(TEXT("ReachHueVariation"), 0.12f);
        TestLiveScalar(TEXT("CalmSurfaceColorVariation"), 0.22f);
        TestLiveScalar(TEXT("FallbackSkyReflectionFloor"), 0.08f);
        TestLiveScalar(TEXT("FallbackSkyReflectionVariation"), 0.24f);
        TestLiveScalar(TEXT("RippleGrazingFloor"), 0.75f);
        TestLiveScalar(TEXT("SlickNormalFloor"), 0.85f);
        TestLiveScalar(TEXT("SlickRoughnessScale"), 1.0f);
        TestLiveScalar(TEXT("FresnelSpecular"), 0.01f);
    }
    return !HasAnyErrors();
}

#endif // WITH_AUTOMATION_TESTS
