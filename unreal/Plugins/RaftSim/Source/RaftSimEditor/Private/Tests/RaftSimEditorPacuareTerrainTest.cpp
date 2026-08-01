#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionNoise.h"
#include "Materials/MaterialExpressionPanner.h"
#include "Materials/MaterialExpressionSingleLayerWaterMaterialOutput.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimPacuareOrganicRainforestTerrainTest,
    "RaftSim.M9.FPacuareOrganicRainforestTerrain",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimPacuareOrganicRainforestTerrainTest::RunTest(
    const FString& Parameters)
{
    UMaterial* Material = LoadObject<UMaterial>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/"
             "M_RaftSim_pacuare_physicalcorridor_SourceLandscapeCandidate."
             "M_RaftSim_pacuare_physicalcorridor_SourceLandscapeCandidate"));
    TestNotNull(TEXT("Pacuare source Landscape material exists"), Material);
    if (!Material)
    {
        return false;
    }

    TestEqual(TEXT("Pacuare terrain stays opaque"), Material->BlendMode, BLEND_Opaque);
    TestTrue(
        TEXT("Pacuare terrain uses scene lighting"),
        Material->GetShadingModels().HasShadingModel(MSM_DefaultLit));
    TestTrue(TEXT("Pacuare terrain remains two-sided"), Material->TwoSided);
    TestTrue(
        TEXT("Pacuare detail normals remain tangent-space"),
        Material->bTangentSpaceNormal);
    const UMaterialEditorOnlyData* EditorOnlyData = Material->GetEditorOnlyData();
    TestNotNull(TEXT("Pacuare material exposes editor graph data"), EditorOnlyData);
    if (EditorOnlyData)
    {
        TestNull(
            TEXT("Organic shading never displaces reviewed terrain"),
            EditorOnlyData->WorldPositionOffset.Expression);
    }

    TMap<FName, float> ScalarDefaults;
    TMap<FName, FLinearColor> VectorDefaults;
    TArray<float> NoiseScales;
    for (const TObjectPtr<UMaterialExpression>& Expression :
         Material->GetExpressionCollection().Expressions)
    {
        if (const UMaterialExpressionScalarParameter* Scalar =
                Cast<UMaterialExpressionScalarParameter>(Expression.Get()))
        {
            ScalarDefaults.Add(Scalar->ParameterName, Scalar->DefaultValue);
        }
        if (const UMaterialExpressionVectorParameter* Vector =
                Cast<UMaterialExpressionVectorParameter>(Expression.Get()))
        {
            VectorDefaults.Add(Vector->ParameterName, Vector->DefaultValue);
        }
        if (const UMaterialExpressionNoise* Noise =
                Cast<UMaterialExpressionNoise>(Expression.Get()))
        {
            NoiseScales.Add(Noise->Scale);
        }
    }

    TestEqual(
        TEXT("Three world-space scales break terrain repetition"),
        NoiseScales.Num(),
        3);
    auto HasNoiseScale = [&NoiseScales](float ExpectedScale)
    {
        return NoiseScales.ContainsByPredicate(
            [ExpectedScale](float Value)
            {
                return FMath::IsNearlyEqual(Value, ExpectedScale, 0.000001f);
            });
    };
    TestTrue(TEXT("Broad rainforest macro field exists"), HasNoiseScale(0.00021f));
    TestTrue(TEXT("Moss and litter patch field exists"), HasNoiseScale(0.00095f));
    TestTrue(TEXT("Fine mineral field exists"), HasNoiseScale(0.00350f));

    auto TestScalar = [this, &ScalarDefaults](
                          const TCHAR* ParameterName,
                          float ExpectedValue)
    {
        const float* Value = ScalarDefaults.Find(ParameterName);
        TestNotNull(FString::Printf(TEXT("%s exists"), ParameterName), Value);
        if (Value)
        {
            TestTrue(
                FString::Printf(TEXT("%s keeps its accepted default"), ParameterName),
                FMath::IsNearlyEqual(*Value, ExpectedValue, 0.001f));
        }
    };
    TestScalar(TEXT("PacuareMacroShadowScale"), 0.62f);
    TestScalar(TEXT("PacuareMacroHighlightScale"), 1.16f);
    TestScalar(TEXT("PacuareForestFloorPaletteWeight"), 0.38f);
    TestScalar(TEXT("PacuareWetRockSlopeStart"), 0.025f);
    TestScalar(TEXT("PacuareWetRockSlopeGain"), 5.50f);
    TestScalar(TEXT("PacuareRockMossPatchStrength"), 0.62f);
    TestScalar(TEXT("PacuareFineShadowScale"), 0.86f);
    TestScalar(TEXT("PacuareFineHighlightScale"), 1.12f);

    const FLinearColor* LeafLitter =
        VectorDefaults.Find(TEXT("PacuareLeafLitterTint"));
    const FLinearColor* Moss = VectorDefaults.Find(TEXT("PacuareMossTint"));
    const FLinearColor* WetRock =
        VectorDefaults.Find(TEXT("PacuareWetRockTint"));
    TestNotNull(TEXT("Leaf-litter response exists"), LeafLitter);
    TestNotNull(TEXT("Moss response exists"), Moss);
    TestNotNull(TEXT("Wet-rock response exists"), WetRock);
    if (LeafLitter && Moss && WetRock)
    {
        TestTrue(TEXT("Leaf litter remains warmer than moss"), LeafLitter->R > Moss->R);
        TestTrue(TEXT("Moss remains the greenest ground response"), Moss->G > Moss->R);
        TestTrue(TEXT("Wet rock remains darker than moss"), WetRock->G < Moss->G);
    }
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimPacuareRainforestDefaultLitWaterTest,
    "RaftSim.M9.FPacuareRainforestDefaultLitWater",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimPacuareRainforestDefaultLitWaterTest::RunTest(
    const FString& Parameters)
{
    UMaterialInstanceConstant* Instance = LoadObject<UMaterialInstanceConstant>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/"
             "MI_RaftSim_Pacuare_PhysicalCorridorWaterCandidate."
             "MI_RaftSim_Pacuare_PhysicalCorridorWaterCandidate"));
    TestNotNull(TEXT("Pacuare water instance exists"), Instance);
    if (!Instance)
    {
        return false;
    }

    UMaterial* Parent = Cast<UMaterial>(Instance->Parent);
    TestNotNull(TEXT("Pacuare water parent exists"), Parent);
    if (!Parent)
    {
        return false;
    }
    TestEqual(
        TEXT("Pacuare water has an isolated rainforest parent"),
        Parent->GetPathName(),
        FString(TEXT("/Game/RaftSim/Environment/PacuareRun/Water/Materials/"
                     "M_RaftSim_Pacuare_RainforestDefaultLitWater."
                     "M_RaftSim_Pacuare_RainforestDefaultLitWater")));
    TestTrue(
        TEXT("Pacuare uses capture-accepted Default Lit water"),
        Parent->GetShadingModels().HasShadingModel(MSM_DefaultLit));
    TestFalse(
        TEXT("Rejected Pacuare Single Layer Water stays inactive"),
        Parent->GetShadingModels().HasShadingModel(MSM_SingleLayerWater));
    TestEqual(TEXT("Pacuare water stays opaque"), Parent->BlendMode, BLEND_Opaque);
    const UMaterialEditorOnlyData* EditorOnlyData = Parent->GetEditorOnlyData();
    TestNotNull(TEXT("Pacuare water graph is inspectable"), EditorOnlyData);
    if (EditorOnlyData)
    {
        TestNull(
            TEXT("Pacuare presentation never displaces solver geometry"),
            EditorOnlyData->WorldPositionOffset.Expression);
    }

    int32 PannerCount = 0;
    int32 WaterOutputCount = 0;
    TArray<float> NoiseScales;
    for (const TObjectPtr<UMaterialExpression>& Expression :
         Parent->GetExpressionCollection().Expressions)
    {
        PannerCount += Cast<UMaterialExpressionPanner>(Expression.Get()) ? 1 : 0;
        WaterOutputCount +=
            Cast<UMaterialExpressionSingleLayerWaterMaterialOutput>(Expression.Get())
            ? 1
            : 0;
        if (const UMaterialExpressionNoise* Noise =
                Cast<UMaterialExpressionNoise>(Expression.Get()))
        {
            NoiseScales.Add(Noise->Scale);
        }
    }
    TestEqual(TEXT("Two independently moving normal layers exist"), PannerCount, 2);
    TestEqual(TEXT("Rejected water-volume output is absent"), WaterOutputCount, 0);
    TestEqual(TEXT("Two world-space variation fields exist"), NoiseScales.Num(), 2);
    TestTrue(TEXT("Rainforest reach-scale variation exists"), NoiseScales.Contains(0.00042f));
    TestTrue(TEXT("Rainforest surface-scale variation exists"), NoiseScales.Contains(0.00210f));

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
    auto TestVector = [this, Instance](
                          const TCHAR* ParameterName,
                          const FLinearColor& ExpectedValue)
    {
        FLinearColor Value = FLinearColor::Black;
        TestTrue(
            FString::Printf(TEXT("%s is bound"), ParameterName),
            Instance->GetVectorParameterValue(
                FMaterialParameterInfo(ParameterName), Value));
        TestTrue(
            FString::Printf(TEXT("%s keeps its reviewed value"), ParameterName),
            Value.Equals(ExpectedValue, 0.0001f));
    };
    TestScalar(TEXT("BaseColorScale"), 1.08f);
    TestScalar(TEXT("Opacity"), 0.28f);
    TestScalar(TEXT("Roughness"), 0.32f);
    TestScalar(TEXT("Specular"), 0.42f);
    TestScalar(TEXT("NormalIntensity"), 0.20f);
    TestScalar(TEXT("SurfaceVariationStrength"), 0.32f);
    TestScalar(TEXT("RefractionIor"), 1.333f);
    TestScalar(TEXT("SolverFieldEnable"), 1.0f);
    TestVector(
        TEXT("SurfaceTint"),
        FLinearColor(0.075f, 0.160f, 0.120f, 0.0f));
    TestVector(
        TEXT("ScatteringCoefficients"),
        FLinearColor(0.00055f, 0.00080f, 0.00065f, 0.0f));
    TestVector(
        TEXT("AbsorptionCoefficients"),
        FLinearColor(0.0055f, 0.0020f, 0.0035f, 0.0f));
    TestVector(
        TEXT("ColorScaleBehindWater"),
        FLinearColor(0.60f, 0.65f, 0.55f, 0.0f));
    return !HasAnyErrors();
}

#endif // WITH_AUTOMATION_TESTS
