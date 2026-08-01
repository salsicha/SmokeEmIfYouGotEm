#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Materials/MaterialExpressionPanner.h"
#include "Materials/MaterialExpressionSingleLayerWaterMaterialOutput.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimZambeziOrganicTerrainNormalsTest,
    "RaftSim.M9.FZambeziOrganicTerrainNormals",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimZambeziOrganicTerrainNormalsTest::RunTest(const FString& Parameters)
{
    TArray<FVector> Vertices;
    Vertices.Reserve(9);
    for (int32 Y = 0; Y < 3; ++Y)
    {
        for (int32 X = 0; X < 3; ++X)
        {
            Vertices.Emplace(
                static_cast<float>(X) * 100.0f,
                static_cast<float>(Y) * 100.0f,
                static_cast<float>(X) * 10.0f + static_cast<float>(Y) * 20.0f);
        }
    }

    const TArray<FVector> Normals =
        RaftSimEditorEnvironment::ComputePreviewGridHeightfieldNormals(
            Vertices,
            3);
    const FVector ExpectedNormal = FVector(-0.1f, -0.2f, 1.0f).GetSafeNormal();
    TestEqual(TEXT("Every grid vertex receives one normal"), Normals.Num(), 9);
    for (int32 Index = 0; Index < Normals.Num(); ++Index)
    {
        TestTrue(
            FString::Printf(TEXT("Planar grid normal %d has no triangle bias"), Index),
            FVector::DotProduct(Normals[Index], ExpectedNormal) > 0.9999f);
    }

    const TArray<FVector> InvalidNormals =
        RaftSimEditorEnvironment::ComputePreviewGridHeightfieldNormals(
            Vertices,
            4);
    TestEqual(
        TEXT("An invalid grid still returns a safe normal for every vertex"),
        InvalidNormals.Num(),
        9);
    TestTrue(
        TEXT("Invalid grid fallback is upright"),
        InvalidNormals[4].Equals(FVector::UpVector));
    return !HasAnyErrors();
}

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
    auto TestVectorParameter = [this, Instance](
        const TCHAR* Label,
        const TCHAR* ParameterName,
        const FLinearColor& ExpectedValue)
    {
        FLinearColor Value = FLinearColor::Black;
        TestTrue(
            FString::Printf(TEXT("%s parameter is bound"), Label),
            Instance->GetVectorParameterValue(
                FMaterialParameterInfo(ParameterName), Value));
        TestTrue(
            FString::Printf(TEXT("%s uses the renderer-reviewed value"), Label),
            Value.Equals(ExpectedValue, 0.0001f));
    };
    TestScalarParameter(TEXT("Base color scale"), TEXT("BaseColorScale"), 0.78f);
    TestScalarParameter(TEXT("Opacity"), TEXT("Opacity"), 0.48f);
    TestScalarParameter(TEXT("Roughness"), TEXT("Roughness"), 0.50f);
    TestScalarParameter(TEXT("Specular"), TEXT("Specular"), 0.26f);
    TestScalarParameter(TEXT("Normal intensity"), TEXT("NormalIntensity"), 0.04f);
    TestScalarParameter(
        TEXT("Reflection fill"), TEXT("ReflectionFillIntensity"), 0.02f);
    TestScalarParameter(
        TEXT("Emissive fill"), TEXT("EmissiveFillScale"), 0.0f);
    TestScalarParameter(
        TEXT("Surface variation"), TEXT("SurfaceVariationStrength"), 0.04f);
    TestVectorParameter(
        TEXT("Sediment surface tint"),
        TEXT("SurfaceTint"),
        FLinearColor(0.028f, 0.078f, 0.032f, 0.0f));
    TestVectorParameter(
        TEXT("Physical scattering"),
        TEXT("ScatteringCoefficients"),
        FLinearColor(0.00025f, 0.00090f, 0.00035f, 0.0f));
    TestVectorParameter(
        TEXT("Physical absorption"),
        TEXT("AbsorptionCoefficients"),
        FLinearColor(0.0150f, 0.0050f, 0.0180f, 0.0f));
    TestVectorParameter(
        TEXT("Behind-water sediment transmission"),
        TEXT("ColorScaleBehindWater"),
        FLinearColor(0.12f, 0.22f, 0.10f, 0.0f));
    return !HasAnyErrors();
}

#endif
