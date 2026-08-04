#include "Environment/RaftSimEditorEnvironmentInternal.h"

#include "Engine/Texture2D.h"
#include "Materials/MaterialExpressionAppendVector.h"
#include "Materials/MaterialExpressionComponentMask.h"
#include "Materials/MaterialExpressionConstant3Vector.h"
#include "Materials/MaterialExpressionMax.h"
#include "Materials/MaterialExpressionLinearInterpolate.h"
#include "Materials/MaterialExpressionNoise.h"
#include "Materials/MaterialExpressionPanner.h"
#include "Materials/MaterialExpressionPerInstanceCustomData.h"
#include "Materials/MaterialExpressionSingleLayerWaterMaterialOutput.h"
#include "Materials/MaterialExpressionTextureCoordinate.h"
#include "Materials/MaterialExpressionTextureObjectParameter.h"
#include "Materials/MaterialExpressionVertexColor.h"
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
    FRaftSimZambeziOrganicBasaltMaterialTest,
    "RaftSim.M9.FZambeziOrganicBasaltMaterial",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimZambeziOrganicBasaltMaterialTest::RunTest(const FString& Parameters)
{
    UMaterial* Material = LoadObject<UMaterial>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/LandscapeCandidates/"
             "M_RaftSim_Zambezi_BatokaV12_WorldAlignedTerrainReview."
             "M_RaftSim_Zambezi_BatokaV12_WorldAlignedTerrainReview"));
    TestNotNull(TEXT("Runnable Batoka terrain material exists"), Material);
    if (!Material)
    {
        return false;
    }

    TestEqual(TEXT("Batoka terrain stays opaque"), Material->BlendMode, BLEND_Opaque);
    TestTrue(
        TEXT("Batoka terrain stays Default Lit"),
        Material->GetShadingModels().HasShadingModel(MSM_DefaultLit));
    TestTrue(TEXT("Batoka terrain remains two-sided"), Material->TwoSided);
    TestFalse(
        TEXT("World-aligned Batoka normals stay in world space"),
        Material->bTangentSpaceNormal);

    TMap<FName, float> ScalarDefaults;
    TMap<FName, FLinearColor> VectorDefaults;
    TSet<FName> TextureObjectParameters;
    int32 NoiseCount = 0;
    int32 MacroScaleCount = 0;
    int32 SecondaryMacroScaleCount = 0;
    int32 DetailScaleCount = 0;
    int32 VertexRedMaskCount = 0;
    int32 VertexRedBlendCount = 0;
    const UMaterialExpressionComponentMask* VertexRedMask = nullptr;
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
        if (const UMaterialExpressionTextureObjectParameter* TextureObject =
                Cast<UMaterialExpressionTextureObjectParameter>(Expression.Get()))
        {
            TextureObjectParameters.Add(TextureObject->ParameterName);
        }
        NoiseCount += Cast<UMaterialExpressionNoise>(Expression.Get()) ? 1 : 0;
        if (const UMaterialExpressionComponentMask* Mask =
                Cast<UMaterialExpressionComponentMask>(Expression.Get()))
        {
            if (Cast<UMaterialExpressionVertexColor>(Mask->Input.Expression) &&
                Mask->R && !Mask->G && !Mask->B && !Mask->A)
            {
                VertexRedMask = Mask;
                ++VertexRedMaskCount;
            }
        }
        if (const UMaterialExpressionConstant3Vector* Constant =
                Cast<UMaterialExpressionConstant3Vector>(Expression.Get()))
        {
            MacroScaleCount += Constant->Constant.Equals(
                FLinearColor(5000.0f, 5000.0f, 5000.0f, 1.0f), 0.01f) ? 1 : 0;
            SecondaryMacroScaleCount += Constant->Constant.Equals(
                FLinearColor(8300.0f, 8300.0f, 8300.0f, 1.0f), 0.01f) ? 1 : 0;
            DetailScaleCount += Constant->Constant.Equals(
                FLinearColor(480.0f, 480.0f, 480.0f, 1.0f), 0.01f) ? 1 : 0;
        }
    }

    for (const TObjectPtr<UMaterialExpression>& Expression :
         Material->GetExpressionCollection().Expressions)
    {
        if (const UMaterialExpressionLinearInterpolate* Lerp =
                Cast<UMaterialExpressionLinearInterpolate>(Expression.Get()))
        {
            VertexRedBlendCount += Lerp->Alpha.Expression == VertexRedMask ? 1 : 0;
        }
    }

    TestEqual(TEXT("Three world-space mineral and erosion fields break repetition"), NoiseCount, 3);
    TestTrue(TEXT("Four primary 50 m macro channels remain"), MacroScaleCount >= 4);
    TestEqual(TEXT("One 83 m secondary macro color projection exists"), SecondaryMacroScaleCount, 1);
    TestEqual(TEXT("Three 4.8 m detail projections remain coherent"), DetailScaleCount, 3);
    TestEqual(
        TEXT("Conditioned wet-bank material has one vertex-red mask"),
        VertexRedMaskCount,
        1);
    TestEqual(
        TEXT("Three material properties bind the conditioned vertex-red mask"),
        VertexRedBlendCount,
        3);
    TestTrue(
        TEXT("Secondary macro texture projection is bound"),
        TextureObjectParameters.Contains(TEXT("BatokaAerialRocks02WorldAlignedSecondaryAlbedo")));

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
    TestScalar(TEXT("BatokaMacroAntiTileStrength"), 0.78f);
    TestScalar(TEXT("BatokaWeatheringVariationStrength"), 0.28f);
    TestScalar(TEXT("BatokaMineralShadowScale"), 0.62f);
    TestScalar(TEXT("BatokaMineralHighlightScale"), 0.96f);
    TestScalar(TEXT("BatokaMacroWeight"), 0.91f);
    TestScalar(TEXT("BatokaTerrainColorCoverageFloor"), 0.78f);
    TestScalar(TEXT("BatokaDetailColorScale"), 0.72f);
    TestScalar(TEXT("BatokaDetailColorWeight"), 0.16f);
    TestScalar(TEXT("BatokaErosionShadowScaleV18"), 0.70f);
    TestScalar(TEXT("BatokaErosionHighlightScaleV18"), 0.98f);
    TestScalar(TEXT("BatokaDetailNormalWeight"), 0.38f);
    TestScalar(TEXT("BatokaDetailRoughnessWeight"), 0.30f);
    TestScalar(TEXT("BatokaWetBankAlbedoScale"), 0.62f);
    TestScalar(TEXT("BatokaWetBankRoughness"), 0.27f);
    TestScalar(TEXT("BatokaWetBankSpecular"), 0.34f);

    const FLinearColor* BasaltTint = VectorDefaults.Find(TEXT("BatokaBasaltTint"));
    const FLinearColor* WeatheredTint =
        VectorDefaults.Find(TEXT("BatokaWeatheredInterflowTint"));
    TestNotNull(TEXT("Dark basalt tint exists"), BasaltTint);
    TestNotNull(TEXT("Weathered interflow tint exists"), WeatheredTint);
    if (BasaltTint)
    {
        TestTrue(
            TEXT("Basalt is blue-gray and substantially darker than the old tan response"),
            BasaltTint->Equals(FLinearColor(0.27f, 0.29f, 0.31f, 1.0f), 0.0001f));
    }
    if (WeatheredTint)
    {
        TestTrue(
            TEXT("Weathering stays a bounded brown accent"),
            WeatheredTint->Equals(FLinearColor(0.45f, 0.34f, 0.30f, 1.0f), 0.0001f));
    }
    const FLinearColor* WetBankTint = VectorDefaults.Find(TEXT("BatokaWetBankTint"));
    TestNotNull(TEXT("Conditioned wet-bank tint exists"), WetBankTint);
    if (WetBankTint)
    {
        TestTrue(
            TEXT("Wet-bank tint remains a bounded cool mineral multiplier"),
            WetBankTint->Equals(
                FLinearColor(0.78f, 0.82f, 0.86f, 1.0f),
                0.0001f));
    }
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimZambeziTalusMaterialTest,
    "RaftSim.M9.FZambeziTalusMaterial",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimZambeziTalusMaterialTest::RunTest(const FString& Parameters)
{
    UMaterialInstanceConstant* Instance = LoadObject<UMaterialInstanceConstant>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/ZambeziRun/Rocks/Materials/"
             "MI_RaftSim_Zambezi_BasaltTalusV1."
             "MI_RaftSim_Zambezi_BasaltTalusV1"));
    TestNotNull(TEXT("Zambezi launch-talus material instance exists"), Instance);
    if (!Instance)
    {
        return false;
    }

    UMaterial* Parent = Cast<UMaterial>(Instance->Parent);
    TestNotNull(TEXT("Zambezi launch talus uses a material parent"), Parent);
    if (!Parent)
    {
        return false;
    }
    TestEqual(
        TEXT("Zambezi launch talus uses the project-owned mineral parent"),
        Parent->GetPathName(),
        FString(TEXT("/Game/RaftSim/Materials/M_RaftSim_RiverBoulder."
                     "M_RaftSim_RiverBoulder")));
    TestEqual(TEXT("Talus remains opaque"), Parent->BlendMode, BLEND_Opaque);
    TestTrue(
        TEXT("Talus remains Default Lit"),
        Parent->GetShadingModels().HasShadingModel(MSM_DefaultLit));

    int32 PerInstanceWaterlineCount = 0;
    int32 WaterlineResolverCount = 0;
    for (const TObjectPtr<UMaterialExpression>& Expression :
         Parent->GetExpressionCollection().Expressions)
    {
        if (const UMaterialExpressionPerInstanceCustomData* CustomData =
                Cast<UMaterialExpressionPerInstanceCustomData>(Expression.Get()))
        {
            if (CustomData->DataIndex == 0 &&
                FMath::IsNearlyEqual(
                    CustomData->ConstDefaultValue,
                    -1.0e7f,
                    1.0f))
            {
                ++PerInstanceWaterlineCount;
            }
        }
        WaterlineResolverCount +=
            Cast<UMaterialExpressionMax>(Expression.Get()) ? 1 : 0;
    }
    TestEqual(
        TEXT("One fail-closed per-instance waterline channel exists"),
        PerInstanceWaterlineCount,
        1);
    TestTrue(
        TEXT("Scalar and per-instance waterlines resolve through Max"),
        WaterlineResolverCount >= 1);

    auto TestScalarParameter = [this, Instance](
                                   const TCHAR* Label,
                                   const TCHAR* ParameterName,
                                   float ExpectedValue,
                                   float Tolerance)
    {
        float Value = 0.0f;
        TestTrue(
            FString::Printf(TEXT("%s parameter is bound"), Label),
            Instance->GetScalarParameterValue(
                FMaterialParameterInfo(ParameterName), Value));
        TestTrue(
            FString::Printf(
                TEXT("%s keeps the authored value %.2f (actual %.2f)"),
                Label,
                ExpectedValue,
                Value),
            FMath::IsNearlyEqual(Value, ExpectedValue, Tolerance));
    };
    TestScalarParameter(
        TEXT("Reviewed-source blend"),
        TEXT("RockVisualSourceBlend"),
        0.42f,
        0.001f);
    TestScalarParameter(
        TEXT("Dry-bank waterline fail-safe"),
        TEXT("RockWaterlineZCm"),
        -1.0e7f,
        1.0f);
    TestScalarParameter(
        TEXT("Conditioned shoreline wet-band width"),
        TEXT("RockWetBandWidthCm"),
        220.0f,
        0.001f);
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimZambeziDefaultLitWaterTest,
    "RaftSim.M9.FZambeziDefaultLitWater",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimZambeziDefaultLitWaterTest::RunTest(const FString& Parameters)
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
                     "M_RaftSim_Zambezi_DefaultLitWater."
                     "M_RaftSim_Zambezi_DefaultLitWater")));
    TestTrue(
        TEXT("Zambezi water uses capture-accepted Default Lit shading"),
        Parent->GetShadingModels().HasShadingModel(MSM_DefaultLit));
    TestFalse(
        TEXT("Rejected Single Layer Water shading stays inactive"),
        Parent->GetShadingModels().HasShadingModel(MSM_SingleLayerWater));
    TestEqual(TEXT("Zambezi water remains an opaque surface"),
        Parent->BlendMode, BLEND_Opaque);

    int32 PannerCount = 0;
    int32 CrossCurrentCoordinateSwapCount = 0;
    int32 ShortWavelengthNormalCoordinateCount = 0;
    int32 WaterOutputCount = 0;
    for (const TObjectPtr<UMaterialExpression>& Expression :
         Parent->GetExpressionCollection().Expressions)
    {
        PannerCount += Cast<UMaterialExpressionPanner>(Expression.Get()) ? 1 : 0;
        CrossCurrentCoordinateSwapCount +=
            Cast<UMaterialExpressionAppendVector>(Expression.Get()) ? 1 : 0;
        if (const UMaterialExpressionTextureCoordinate* TextureCoordinate =
                Cast<UMaterialExpressionTextureCoordinate>(Expression.Get()))
        {
            const bool bFirstLayer =
                FMath::IsNearlyEqual(TextureCoordinate->UTiling, 2.40f) &&
                FMath::IsNearlyEqual(TextureCoordinate->VTiling, 6.20f);
            const bool bSecondLayer =
                FMath::IsNearlyEqual(TextureCoordinate->UTiling, 4.10f) &&
                FMath::IsNearlyEqual(TextureCoordinate->VTiling, 10.30f);
            ShortWavelengthNormalCoordinateCount +=
                bFirstLayer || bSecondLayer ? 1 : 0;
        }
        WaterOutputCount +=
            Cast<UMaterialExpressionSingleLayerWaterMaterialOutput>(Expression.Get())
            ? 1
            : 0;
    }
    TestEqual(TEXT("Two opposed normal layers move independently"), PannerCount, 2);
    TestEqual(
        TEXT("One normal layer swaps axes for cross-current breakup"),
        CrossCurrentCoordinateSwapCount,
        1);
    TestEqual(
        TEXT("Two short-wavelength normal coordinates replace long comb grooves"),
        ShortWavelengthNormalCoordinateCount,
        2);
    TestEqual(TEXT("Rejected water-volume output is absent"), WaterOutputCount, 0);

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
    TestScalarParameter(TEXT("Base color scale"), TEXT("BaseColorScale"), 1.08f);
    TestScalarParameter(TEXT("Roughness"), TEXT("Roughness"), 0.34f);
    TestScalarParameter(TEXT("Specular"), TEXT("Specular"), 0.38f);
    TestScalarParameter(TEXT("Normal intensity"), TEXT("NormalIntensity"), 0.16f);
    TestScalarParameter(
        TEXT("Reflection fill"), TEXT("ReflectionFillIntensity"), 0.08f);
    TestScalarParameter(
        TEXT("Emissive fill"), TEXT("EmissiveFillScale"), 0.32f);
    TestScalarParameter(
        TEXT("Surface variation"), TEXT("SurfaceVariationStrength"), 0.14f);
    TestVectorParameter(
        TEXT("Sediment surface tint"),
        TEXT("SurfaceTint"),
        FLinearColor(0.055f, 0.115f, 0.050f, 0.0f));
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimZambeziLiveTransmittingWaterTest,
    "RaftSim.M9.FZambeziLiveTransmittingWater",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimZambeziLiveTransmittingWaterTest::RunTest(
    const FString& Parameters)
{
    FString AuthoringSummary;
    UMaterialInstanceConstant* Instance =
        RaftSimEditorEnvironment::LoadOrCreateZambeziBatokaLiveWaterV2Instance(
            AuthoringSummary);
    TestNotNull(
        TEXT("Zambezi river-local live-volume authoring succeeds"),
        Instance);
    if (!Instance)
    {
        AddError(AuthoringSummary);
        return false;
    }

    TestNotNull(TEXT("Zambezi live-volume parent exists"), Instance->Parent.Get());
    if (Instance->Parent)
    {
        TestEqual(
            TEXT("Zambezi uses shared raft-transmitting volume water"),
            Instance->Parent->GetPathName(),
            FString(TEXT(
                "/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/"
                "M_RaftSim_SouthForkRaftTransmissionWater."
                "M_RaftSim_SouthForkRaftTransmissionWater")));
    }

    bool bHasCoverageFeather = false;
    bool bHasOpticalCoverageFeather = false;
    bool bHasOpticalDepthResponse = false;
    if (UMaterial* ParentMaterial = Instance->Parent
            ? Instance->Parent->GetMaterial()
            : nullptr)
    {
        for (const TObjectPtr<UMaterialExpression>& Expression :
             ParentMaterial->GetExpressionCollection().Expressions)
        {
            bHasCoverageFeather |= Expression &&
                Expression->Desc == TEXT("RaftSimLiveVolumeBankCoverage");
            bHasOpticalCoverageFeather |= Expression &&
                Expression->Desc ==
                    TEXT("RaftSimLiveVolumeBankOpticalCoverage");
            bHasOpticalDepthResponse |= Expression &&
                Expression->Desc == TEXT("RaftSimOpticalDepthResponse");
        }
    }
    TestTrue(
        TEXT("Zambezi volume parent consumes smooth wet-cell bank coverage"),
        bHasCoverageFeather);
    TestTrue(
        TEXT("Zambezi volume parent fades complete bank optical volume"),
        bHasOpticalCoverageFeather);
    TestTrue(
        TEXT("Shared volume parent exposes a bounded optical-depth response"),
        bHasOpticalDepthResponse);

    UTexture* FlowNormal = nullptr;
    UTexture* FoamLace = nullptr;
    TestTrue(
        TEXT("Zambezi live volume binds its first-party flow normal"),
        Instance->GetTextureParameterValue(
            FMaterialParameterInfo(TEXT("WaterFlowNormalPrimary")),
            FlowNormal));
    TestTrue(
        TEXT("Zambezi live volume binds its solver-masked foam lace"),
        Instance->GetTextureParameterValue(
            FMaterialParameterInfo(TEXT("WhitewaterFoamLace")),
            FoamLace));
    TestTrue(
        TEXT("Zambezi flow normal is river-local"),
        FlowNormal && FlowNormal->GetPathName().Contains(
            TEXT("T_RaftSim_ZambeziBatokaWaterV1_FlowNormal")));
    TestTrue(
        TEXT("Zambezi foam lace is river-local"),
        FoamLace && FoamLace->GetPathName().Contains(
            TEXT("T_RaftSim_ZambeziBatokaWaterV1_FoamLace")));

    if (const UTexture2D* FlowNormal2D = Cast<UTexture2D>(FlowNormal))
    {
        TestEqual(
            TEXT("Zambezi flow normal imports as normal-map data"),
            FlowNormal2D->CompressionSettings,
            TC_Normalmap);
        TestFalse(TEXT("Zambezi flow normal stays linear"), FlowNormal2D->SRGB);
        TestEqual(TEXT("Zambezi flow normal mirrors in X"), FlowNormal2D->AddressX, TA_Mirror);
        TestEqual(TEXT("Zambezi flow normal mirrors in Y"), FlowNormal2D->AddressY, TA_Mirror);
    }
    if (const UTexture2D* FoamLace2D = Cast<UTexture2D>(FoamLace))
    {
        TestEqual(
            TEXT("Zambezi foam lace imports as mask data"),
            FoamLace2D->CompressionSettings,
            TC_Masks);
        TestFalse(TEXT("Zambezi foam lace stays linear"), FoamLace2D->SRGB);
        TestEqual(TEXT("Zambezi foam lace mirrors in X"), FoamLace2D->AddressX, TA_Mirror);
        TestEqual(TEXT("Zambezi foam lace mirrors in Y"), FoamLace2D->AddressY, TA_Mirror);
    }

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
            FString::Printf(TEXT("%s keeps its authored value"), ParameterName),
            FMath::IsNearlyEqual(Value, ExpectedValue, 0.001f));
    };
    TestScalar(TEXT("HydraulicFoamCoverageGain"), 0.72f);
    TestScalar(TEXT("SpeedAerationFraction"), 0.14f);
    TestScalar(TEXT("FoamRoughness"), 0.78f);
    TestScalar(TEXT("FallbackSkyReflectionFloor"), 0.07f);
    TestScalar(TEXT("FallbackSkyReflectionVariation"), 0.26f);
    TestScalar(TEXT("RippleGrazingFloor"), 0.72f);
    TestScalar(TEXT("SlickRoughnessScale"), 0.96f);
    TestScalar(TEXT("FresnelSpecular"), 0.018f);
    TestScalar(TEXT("SlickNormalFloor"), 0.82f);
    TestScalar(TEXT("LiveVolumeBankCoverageFloor"), 0.0f);
    return !HasAnyErrors();
}

#endif
