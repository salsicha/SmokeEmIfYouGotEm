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
    TestEqual(
        TEXT("Futaleufu capture water transmits the reviewed riverbed"),
        Parent->BlendMode,
        BLEND_Translucent);
    TestTrue(TEXT("Futaleufu water remains two-sided"), Parent->TwoSided);
    TestTrue(TEXT("Futaleufu water normals remain tangent-space"), Parent->bTangentSpaceNormal);
    const UMaterialEditorOnlyData* EditorOnlyData = Parent->GetEditorOnlyData();
    TestNotNull(TEXT("Futaleufu water graph remains inspectable"), EditorOnlyData);
    if (EditorOnlyData)
    {
        TestNotNull(
            TEXT("Futaleufu capture water binds CPU-authored transmission coverage"),
            EditorOnlyData->Opacity.Expression);
        TestNotNull(
            TEXT("Futaleufu capture water binds physical refraction"),
            EditorOnlyData->Refraction.Expression);
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
    TestEqual(TEXT("Three moving normal layers exist"), PannerCount, 3);
    TestEqual(TEXT("Three world optical scales exist"), NoiseScales.Num(), 3);
    TestTrue(TEXT("Reach-scale water variation exists"), NoiseScales.Contains(0.00031f));
    TestTrue(TEXT("Surface-scale water variation exists"), NoiseScales.Contains(0.00163f));
    TestTrue(TEXT("Fine-scale water variation exists"), NoiseScales.Contains(0.00673f));

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
    TestScalar(TEXT("SurfaceVariationStrength"), 0.44f);
    TestScalar(TEXT("CrossCurrentNormalWeight"), 0.34f);
    TestScalar(TEXT("RoughnessVariationAmplitude"), 0.12f);
    // The saved physical-corridor instance is authored from the river-local
    // water settings, whose reviewed transmitting value is 0.34.  The parent
    // retains 0.88 only as its fallback default when no river override exists.
    TestScalar(TEXT("Opacity"), 0.34f);
    TestScalar(TEXT("RefractionIor"), 1.333f);
    TestScalar(TEXT("SolverFieldEnable"), 0.0f);
    TestScalar(TEXT("SolverMacroNormalWeight"), 0.0f);
    TestScalar(TEXT("SolverDepthColorWeight"), 0.0f);
    TestScalar(TEXT("SolverFroudeAerationWeight"), 0.0f);

    const RaftSimEditorEnvironment::FRaftSimLandscapeCandidateWaterSettings WaterSettings =
        RaftSimEditorEnvironment::GetLandscapeCandidateWaterSettings(
            TEXT("futaleufu_terminator"));
    TestEqual(TEXT("Futaleufu ribbon has 48 cross-current samples"), WaterSettings.RibbonCrossSectionSteps, 48);
    TestTrue(TEXT("Futaleufu CPU chop keeps reviewed scale"), FMath::IsNearlyEqual(WaterSettings.AnalyticChopScale, 0.78f));
    TestTrue(TEXT("Futaleufu cross-current chop keeps reviewed amplitude"), FMath::IsNearlyEqual(WaterSettings.CrossCurrentChopAmplitudeCm, 8.0f));
    TestTrue(TEXT("Futaleufu embeds restrained aeration into the water surface"), FMath::IsNearlyEqual(WaterSettings.EmbeddedAerationWeight, 0.22f));

    UTexture* NormalAtlas = nullptr;
    TestTrue(
        TEXT("Futaleufu river-local normal is bound"),
        Instance->GetTextureParameterValue(
            FMaterialParameterInfo(TEXT("WaterNormalAtlas")), NormalAtlas));
    TestNotNull(TEXT("Futaleufu river-local normal exists"), NormalAtlas);
    if (NormalAtlas)
    {
        TestEqual(
            TEXT("Futaleufu uses its project-owned live flow normal"),
            NormalAtlas->GetPathName(),
            FString(TEXT("/Game/RaftSim/Environment/FutaleufuRun/Water/Textures/"
                         "T_RaftSim_FutaleufuTerminatorWaterV1_FlowNormal."
                         "T_RaftSim_FutaleufuTerminatorWaterV1_FlowNormal")));
    }

    FLinearColor AtlasTileOrigin;
    TestTrue(
        TEXT("Futaleufu standalone normal origin is bound"),
        Instance->GetVectorParameterValue(
            FMaterialParameterInfo(TEXT("AtlasTileOrigin")),
            AtlasTileOrigin));
    TestTrue(
        TEXT("Futaleufu standalone normal starts at zero UV"),
        AtlasTileOrigin.Equals(
            FLinearColor(0.0f, 0.0f, 0.0f, 0.0f), 0.001f));
    FLinearColor AtlasTileScale;
    TestTrue(
        TEXT("Futaleufu standalone normal scale is bound"),
        Instance->GetVectorParameterValue(
            FMaterialParameterInfo(TEXT("AtlasTileScale")),
            AtlasTileScale));
    TestTrue(
        TEXT("Futaleufu standalone normal uses its complete texture"),
        AtlasTileScale.Equals(
            FLinearColor(1.0f, 1.0f, 0.0f, 0.0f), 0.001f));

    UMaterialInstanceConstant* LiveVolumeInstance =
        LoadObject<UMaterialInstanceConstant>(
            nullptr,
            TEXT("/Game/RaftSim/Environment/FutaleufuRun/Water/Materials/"
                 "MI_RaftSim_FutaleufuTerminator_LiveVolumeWaterV3."
                 "MI_RaftSim_FutaleufuTerminator_LiveVolumeWaterV3"));
    TestNotNull(
        TEXT("Futaleufu river-local live-volume instance exists"),
        LiveVolumeInstance);
    if (LiveVolumeInstance)
    {
        UTexture* LiveNormal = nullptr;
        UTexture* LiveFoam = nullptr;
        TestTrue(
            TEXT("Futaleufu live volume binds river-local normal"),
            LiveVolumeInstance->GetTextureParameterValue(
                FMaterialParameterInfo(TEXT("WaterFlowNormalPrimary")),
                LiveNormal));
        TestTrue(
            TEXT("Futaleufu live volume binds river-local foam lace"),
            LiveVolumeInstance->GetTextureParameterValue(
                FMaterialParameterInfo(TEXT("WhitewaterFoamLace")),
                LiveFoam));
        TestTrue(
            TEXT("Futaleufu live normal path is river-local"),
            LiveNormal && LiveNormal->GetPathName().Contains(
                TEXT("T_RaftSim_FutaleufuTerminatorWaterV1_FlowNormal")));
        TestTrue(
            TEXT("Futaleufu live foam path is river-local"),
            LiveFoam && LiveFoam->GetPathName().Contains(
                TEXT("T_RaftSim_FutaleufuTerminatorWaterV1_FoamLace")));
        auto TestLiveScalar = [this, LiveVolumeInstance](
                                  const TCHAR* ParameterName,
                                  float ExpectedValue)
        {
            float Value = 0.0f;
            TestTrue(
                FString::Printf(TEXT("live %s is bound"), ParameterName),
                LiveVolumeInstance->GetScalarParameterValue(
                    FMaterialParameterInfo(ParameterName), Value));
            TestTrue(
                FString::Printf(
                    TEXT("live %s keeps its reviewed V4 value"),
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
