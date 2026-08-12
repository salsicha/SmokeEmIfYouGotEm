#if WITH_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "Dom/JsonObject.h"
#include "AssetCompilingManager.h"
#include "Engine/Texture2D.h"
#include "HAL/FileManager.h"
#include "Engine/StaticMesh.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpressionTextureCoordinate.h"
#include "Materials/MaterialInstanceConstant.h"
#include "Materials/MaterialInterface.h"
#include "MaterialShared.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "../RaftSimContentLockDirector.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "StaticMeshResources.h"

#include <limits>

namespace
{
FString RepoPath(const FString& RelativePath)
{
    return FPaths::ConvertRelativePathToFull(
        FPaths::Combine(FPaths::ProjectDir(), TEXT(".."), RelativePath));
}

TSharedPtr<FJsonObject> LoadJson(
    FAutomationTestBase& Test, const FString& Path, const FString& Label)
{
    FString Text;
    if (!Test.TestTrue(Label + TEXT(" exists"), FFileHelper::LoadFileToString(Text, *Path)))
    {
        return nullptr;
    }
    TSharedPtr<FJsonObject> Root;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Text);
    if (!Test.TestTrue(
            Label + TEXT(" parses"),
            FJsonSerializer::Deserialize(Reader, Root) && Root.IsValid()))
    {
        return nullptr;
    }
    return Root;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM8GpuTimingPlausibilityTest,
    "RaftSim.M8.DGpuTimingPlausibility",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimM8GpuTimingPlausibilityTest::RunTest(const FString& Parameters)
{
    TestTrue(TEXT("Normal GPU timing is accepted"),
        ARaftSimContentLockDirector::IsGpuTimingSamplePlausible(12.8f, 14.2f));
    TestTrue(TEXT("Long GPU timing inside the one-second floor is retained"),
        ARaftSimContentLockDirector::IsGpuTimingSamplePlausible(750.0f, 14.2f));
    TestTrue(TEXT("A real long wall-clock stall permits a matching GPU stall"),
        ARaftSimContentLockDirector::IsGpuTimingSamplePlausible(5000.0f, 400.0f));
    TestFalse(TEXT("An impossible stale multi-second GPU timer is rejected"),
        ARaftSimContentLockDirector::IsGpuTimingSamplePlausible(89478.0f, 14.8f));
    TestFalse(TEXT("Negative GPU timing is rejected"),
        ARaftSimContentLockDirector::IsGpuTimingSamplePlausible(-1.0f, 14.2f));
    TestFalse(TEXT("Non-finite GPU timing is rejected"),
        ARaftSimContentLockDirector::IsGpuTimingSamplePlausible(
            std::numeric_limits<float>::infinity(), 14.2f));
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM8PackagedRapidMatrixTest,
    "RaftSim.M8.APackagedRapidMatrix",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimM8PackagedRapidMatrixTest::RunTest(const FString& Parameters)
{
    FString Report;
    const bool bPassed = ARaftSimContentLockDirector::RunRapidMatrixRegression(Report);
    TestTrue(TEXT("All 20 named rapids at three flow bands pass the shipping adapter"), bPassed);

    const FString ReportPath = FPaths::Combine(
        FPaths::ProjectSavedDir(), TEXT("Validation/m8_editor_rapid_regression.json"));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(ReportPath), true);
    TestTrue(TEXT("Editor matrix evidence is saved"),
        FFileHelper::SaveStringToFile(Report, *ReportPath));

    const TSharedPtr<FJsonObject> Root = LoadJson(*this, ReportPath, TEXT("Matrix report"));
    if (!Root.IsValid())
    {
        return false;
    }
    TestEqual(TEXT("Rapid count"), Root->GetIntegerField(TEXT("rapid_count")), 20);
    TestEqual(TEXT("Case count"), Root->GetIntegerField(TEXT("case_count")), 60);
    TestEqual(TEXT("Passed case count"), Root->GetIntegerField(TEXT("passed_case_count")), 60);
    TestTrue(TEXT("Live solver is compiled"), Root->GetBoolField(TEXT("live_solver_compiled")));
    TestTrue(TEXT("Matrix report passes"), Root->GetBoolField(TEXT("passed")));
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM8RuntimeDataAndMaterialsTest,
    "RaftSim.M8.BRuntimeDataAndMaterials",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimM8RuntimeDataAndMaterialsTest::RunTest(const FString& Parameters)
{
    const FString HydraulicManifest = URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(
        TEXT("physics/data/real_world/south_fork_american_chili_bar/full_hydraulics/manifest.json"));
    const FString CoordinateMap = URaftSimWaterRuntimeAdapter::ResolveRuntimeDataPath(
        TEXT("physics/data/real_world/south_fork_american_chili_bar/production_corridor/"
             "photoreal_environment/river_coordinate_map.json"));
    TestTrue(TEXT("Runtime hydraulic manifest resolves"), FPaths::FileExists(HydraulicManifest));
    TestTrue(TEXT("Runtime river coordinate map resolves"), FPaths::FileExists(CoordinateMap));

    const TCHAR* RequiredMaterials[] = {
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverWater.M_RaftSim_PhotorealRiverWater"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_LiveRiverSurface.M_RaftSim_LiveRiverSurface"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverTerrain.M_RaftSim_PhotorealRiverTerrain"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_Asphalt.M_RaftSim_Asphalt"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_Timber.M_RaftSim_Timber"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_RiverBoulder.M_RaftSim_RiverBoulder"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_RaftTube.M_RaftSim_RaftTube"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_RaftFloor.M_RaftSim_RaftFloor"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_RaftFloorReadable.M_RaftSim_RaftFloorReadable"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_Wetsuit.M_RaftSim_Wetsuit"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_Skin.M_RaftSim_Skin"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_Helmet.M_RaftSim_Helmet"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PaddleShaft.M_RaftSim_PaddleShaft"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PaddleBlade.M_RaftSim_PaddleBlade"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_CrewPFD.M_RaftSim_CrewPFD"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PFD_Red.M_RaftSim_PFD_Red"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PFD_Yellow.M_RaftSim_PFD_Yellow"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PFD_Blue.M_RaftSim_PFD_Blue"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_RaftRigging.M_RaftSim_RaftRigging"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_SplashJacket.M_RaftSim_SplashJacket"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PFDWebbing.M_RaftSim_PFDWebbing"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_BootRubber.M_RaftSim_BootRubber"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_GuideHelmet.M_RaftSim_GuideHelmet")
    };
    for (const TCHAR* Path : RequiredMaterials)
    {
        UMaterialInterface* Material = LoadObject<UMaterialInterface>(nullptr, Path);
        TestNotNull(FString::Printf(TEXT("Material loads: %s"), Path), Material);
        if (Material != nullptr)
        {
            TestTrue(
                FString::Printf(TEXT("Material persists instanced-mesh usage: %s"), Path),
                Material->GetUsageByFlag(MATUSAGE_InstancedStaticMeshes));
        }
    }

    UMaterialInterface* LiveWaterMaterial = LoadObject<UMaterialInterface>(
        nullptr,
        TEXT("/Game/RaftSim/Materials/M_RaftSim_LiveRiverSurface."
             "M_RaftSim_LiveRiverSurface"));
    TestNotNull(TEXT("Hydraulically weighted live-water material loads"), LiveWaterMaterial);
    if (LiveWaterMaterial)
    {
        float CalmCoverage = 0.0f;
        float ActiveCoverage = 0.0f;
        float FoamCoverageGain = 0.0f;
        float SpeedCoverageGain = 0.0f;
        float SpeedCoverageThresholdBias = 0.0f;
        float FlowAdvectionScale = 0.0f;
        FLinearColor ShallowSurfaceColor = FLinearColor::Black;
        FLinearColor DeepSurfaceColor = FLinearColor::Black;
        TestTrue(TEXT("Calm live-water coverage resolves"),
            LiveWaterMaterial->GetScalarParameterValue(
                FMaterialParameterInfo(TEXT("CalmLiveSurfaceCoverage")),
                CalmCoverage));
        TestTrue(TEXT("Active live-water coverage resolves"),
            LiveWaterMaterial->GetScalarParameterValue(
                FMaterialParameterInfo(TEXT("ActiveLiveSurfaceCoverage")),
                ActiveCoverage));
        TestTrue(TEXT("Foam coverage gain resolves"),
            LiveWaterMaterial->GetScalarParameterValue(
                FMaterialParameterInfo(TEXT("HydraulicCoverageFoamGain")),
                FoamCoverageGain));
        TestTrue(TEXT("Speed coverage gain resolves"),
            LiveWaterMaterial->GetScalarParameterValue(
                FMaterialParameterInfo(TEXT("HydraulicCoverageSpeedGain")),
                SpeedCoverageGain));
        TestTrue(TEXT("Ordinary-current coverage threshold resolves"),
            LiveWaterMaterial->GetScalarParameterValue(
                FMaterialParameterInfo(TEXT("HydraulicCoverageSpeedThresholdBias")),
                SpeedCoverageThresholdBias));
        TestTrue(TEXT("Solver flow-advection scale resolves"),
            LiveWaterMaterial->GetScalarParameterValue(
                FMaterialParameterInfo(TEXT("LiveFlowAdvectionScale")),
                FlowAdvectionScale));
        TestTrue(TEXT("Shallow live-water surface colour resolves"),
            LiveWaterMaterial->GetVectorParameterValue(
                FMaterialParameterInfo(TEXT("LiveShallowSurfaceColor")),
                ShallowSurfaceColor));
        TestTrue(TEXT("Deep live-water surface colour resolves"),
            LiveWaterMaterial->GetVectorParameterValue(
                FMaterialParameterInfo(TEXT("LiveDeepSurfaceColor")),
                DeepSurfaceColor));
        TestTrue(TEXT("Calm water leaves the authored volume visible"),
            FMath::IsNearlyEqual(CalmCoverage, 0.0f, KINDA_SMALL_NUMBER));
        TestTrue(TEXT("Hydraulically active overlay remains presentation-bounded"),
            FMath::IsNearlyEqual(ActiveCoverage, 0.03f, KINDA_SMALL_NUMBER));
        TestTrue(TEXT("Foam contributes strongly to live coverage"),
            FMath::IsNearlyEqual(FoamCoverageGain, 0.95f, KINDA_SMALL_NUMBER));
        TestTrue(TEXT("Ordinary solver speed contributes strongly to live coverage"),
            FMath::IsNearlyEqual(SpeedCoverageGain, 3.2f, KINDA_SMALL_NUMBER) &&
                FMath::IsNearlyEqual(
                    SpeedCoverageThresholdBias, -0.03f, KINDA_SMALL_NUMBER));
        TestTrue(TEXT("Live detail advects at physical solver speed by default"),
            FMath::IsNearlyEqual(FlowAdvectionScale, 1.0f, KINDA_SMALL_NUMBER));

        UMaterial* LiveWaterBaseMaterial = Cast<UMaterial>(LiveWaterMaterial);
        TestNotNull(TEXT("Live-water interface is a base material"), LiveWaterBaseMaterial);
        bool bHasSolverVelocityUv = false;
        bool bHasPrimarySolverAdvection = false;
        bool bHasCrossSolverAdvection = false;
        if (LiveWaterBaseMaterial)
        {
            for (const TObjectPtr<UMaterialExpression>& Expression :
                 LiveWaterBaseMaterial->GetExpressionCollection().Expressions)
            {
                if (const UMaterialExpressionTextureCoordinate* TexCoord =
                        Cast<UMaterialExpressionTextureCoordinate>(Expression.Get()))
                {
                    bHasSolverVelocityUv |=
                        TexCoord->CoordinateIndex == 1 &&
                        TexCoord->Desc == TEXT("RaftSimSolverVelocityMpsUV1");
                }
                bHasPrimarySolverAdvection |= Expression &&
                    Expression->Desc == TEXT("RaftSimSolverVelocityAdvectionPrimary");
                bHasCrossSolverAdvection |= Expression &&
                    Expression->Desc == TEXT("RaftSimSolverVelocityAdvectionCross");
            }
        }
        TestTrue(TEXT("Live material reads solver velocity from UV1"), bHasSolverVelocityUv);
        TestTrue(TEXT("Primary ripple layer is solver-velocity advected"),
            bHasPrimarySolverAdvection);
        TestTrue(TEXT("Cross ripple layer is solver-velocity advected"),
            bHasCrossSolverAdvection);
        TestTrue(TEXT("Shallow live overlay uses calibrated gray-green radiance"),
            ShallowSurfaceColor.Equals(
                FLinearColor(0.115f, 0.185f, 0.175f, 1.0f), KINDA_SMALL_NUMBER));
        TestTrue(TEXT("Deep live overlay remains darker than shallow water"),
            DeepSurfaceColor.R < ShallowSurfaceColor.R &&
                DeepSurfaceColor.G < ShallowSurfaceColor.G &&
                DeepSurfaceColor.B < ShallowSurfaceColor.B);
        if (FApp::CanEverRender())
        {
            FAssetCompilingManager::Get().FinishAllCompilation();
            FMaterialResource* LiveWaterResource = LiveWaterBaseMaterial
                ? LiveWaterBaseMaterial->GetMaterialResource(GMaxRHIShaderPlatform)
                : nullptr;
            TestNotNull(TEXT("Live-water material has a platform shader resource"),
                LiveWaterResource);
            if (LiveWaterResource)
            {
#if WITH_EDITOR
                TestTrue(TEXT("Live-water material has no platform compile errors"),
                    LiveWaterResource->GetCompileErrors().IsEmpty());
#endif
            }
        }
    }

    const TCHAR* RequiredTerrainMicrodetailTextures[] = {
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/RockGround_4K/"
             "T_RockGround_BaseColor_4K.T_RockGround_BaseColor_4K"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/RockGround_4K/"
             "T_RockGround_NormalGL_4K.T_RockGround_NormalGL_4K"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/RockGround_4K/"
             "T_RockGround_Roughness_4K.T_RockGround_Roughness_4K"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/ForestGround03_4K/"
             "T_ForestGround03_BaseColor_4K.T_ForestGround03_BaseColor_4K"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/ForestGround03_4K/"
             "T_ForestGround03_NormalGL_4K.T_ForestGround03_NormalGL_4K"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/ForestGround03_4K/"
             "T_ForestGround03_Roughness_4K.T_ForestGround03_Roughness_4K"),
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/Textures/"
             "T_RaftSim_SouthForkWater_FlowNormal."
             "T_RaftSim_SouthForkWater_FlowNormal")
    };
    for (const TCHAR* Path : RequiredTerrainMicrodetailTextures)
    {
        UTexture2D* Texture = LoadObject<UTexture2D>(nullptr, Path);
        TestNotNull(
            FString::Printf(TEXT("Terrain/water microdetail texture loads: %s"), Path),
            Texture);
    }
    UTexture2D* FlowNormalTexture = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Water/Textures/"
             "T_RaftSim_SouthForkWater_FlowNormal."
             "T_RaftSim_SouthForkWater_FlowNormal"));
    TestNotNull(TEXT("Project-owned river flow normal loads"), FlowNormalTexture);
    if (FlowNormalTexture)
    {
        TestEqual(TEXT("River flow normal uses normal-map compression"),
            FlowNormalTexture->CompressionSettings, TC_Normalmap);
        TestFalse(TEXT("River flow normal samples in linear space"), FlowNormalTexture->SRGB);
        TestEqual(TEXT("River flow normal mirrors horizontally without seams"),
            FlowNormalTexture->AddressX, TA_Mirror);
        TestEqual(TEXT("River flow normal mirrors vertically without seams"),
            FlowNormalTexture->AddressY, TA_Mirror);
    }
    UTexture2D* FarFieldMacroTexture = LoadObject<UTexture2D>(
        nullptr,
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Terrain/MacroTextures/"
             "T_RaftSim_far_field_00_MacroAlbedo."
             "T_RaftSim_far_field_00_MacroAlbedo"));
    TestNotNull(TEXT("Far-field source macro texture loads"), FarFieldMacroTexture);
    if (FarFieldMacroTexture)
    {
#if WITH_EDITORONLY_DATA
        TestEqual(
            TEXT("Far-field source macro retains distant detail with sharpened mips"),
            FarFieldMacroTexture->MipGenSettings,
            TMGS_Sharpen4);
#else
        TestTrue(
            TEXT("Far-field source macro retains a cooked mip chain"),
            FarFieldMacroTexture->GetNumMips() > 1);
#endif
        TestTrue(
            TEXT("Far-field source macro stays resident for short gameplay captures"),
            FarFieldMacroTexture->NeverStream);
    }

    struct FTerrainMaterialExpectation
    {
        const TCHAR* Path;
        float SourceMacroInfluence;
        float RockAlbedoStrength;
    };
    const FTerrainMaterialExpectation TerrainMaterialExpectations[] = {
        {
            TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Terrain/Materials/"
                 "MI_RaftSim_south_fork_00_Terrain."
                 "MI_RaftSim_south_fork_00_Terrain"),
            0.44f,
            0.52f,
        },
        {
            TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Terrain/Materials/"
                 "MI_RaftSim_far_field_00_Terrain."
                 "MI_RaftSim_far_field_00_Terrain"),
            0.92f,
            0.50f,
        },
    };
    for (const FTerrainMaterialExpectation& Expectation : TerrainMaterialExpectations)
    {
        UMaterialInstanceConstant* Instance = LoadObject<UMaterialInstanceConstant>(
            nullptr, Expectation.Path);
        TestNotNull(
            FString::Printf(TEXT("Terrain material instance loads: %s"), Expectation.Path),
            Instance);
        if (!Instance)
        {
            continue;
        }
        float SourceMacroInfluence = 0.0f;
        float RockAlbedoStrength = 0.0f;
        FLinearColor FarFieldSourceMacroTone = FLinearColor::Transparent;
        TestTrue(TEXT("Source macro influence resolves"),
            Instance->GetScalarParameterValue(
                FMaterialParameterInfo(TEXT("SourceMacroInfluence")),
                SourceMacroInfluence));
        TestTrue(TEXT("Rock albedo strength resolves"),
            Instance->GetScalarParameterValue(
                FMaterialParameterInfo(TEXT("RockAlbedoStrength")),
                RockAlbedoStrength));
        TestTrue(TEXT("Far-field source macro tone resolves"),
            Instance->GetVectorParameterValue(
                FMaterialParameterInfo(TEXT("FarFieldSourceMacroTone")),
                FarFieldSourceMacroTone));
        TestTrue(TEXT("Source macro influence matches the corridor/far-field policy"),
            FMath::IsNearlyEqual(
                SourceMacroInfluence, Expectation.SourceMacroInfluence, KINDA_SMALL_NUMBER));
        TestTrue(TEXT("Rock albedo strength matches the corridor/far-field policy"),
            FMath::IsNearlyEqual(
                RockAlbedoStrength, Expectation.RockAlbedoStrength, KINDA_SMALL_NUMBER));
        TestTrue(TEXT("Corridor edge and far field share the same source tone"),
            FarFieldSourceMacroTone.Equals(
                FLinearColor(0.62f, 0.68f, 0.60f, 1.0f), KINDA_SMALL_NUMBER));
    }

    const TCHAR* ReviewedNaniteMaterials[] = {
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/"
             "M_PineTree01_Bark.M_PineTree01_Bark"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/"
             "M_PineTree01_Needles.M_PineTree01_Needles"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/"
             "M_PineTree01_NeedlesMasked.M_PineTree01_NeedlesMasked"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/"
             "M_PineTree01_TrunkA.M_PineTree01_TrunkA"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/"
             "M_PineTree01_TrunkB.M_PineTree01_TrunkB"),
        TEXT("/Game/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/"
             "M_PineTree01_TrunkC.M_PineTree01_TrunkC")
    };
    for (const TCHAR* Path : ReviewedNaniteMaterials)
    {
        UMaterialInterface* Material = LoadObject<UMaterialInterface>(nullptr, Path);
        TestNotNull(FString::Printf(TEXT("Reviewed material loads: %s"), Path), Material);
        if (Material != nullptr)
        {
            TestTrue(
                FString::Printf(TEXT("Reviewed material persists Nanite usage: %s"), Path),
                Material->GetUsageByFlag(MATUSAGE_Nanite));
            TestTrue(
                FString::Printf(TEXT("Reviewed material persists instance usage: %s"), Path),
                Material->GetUsageByFlag(MATUSAGE_InstancedStaticMeshes));
        }
    }

    const TCHAR* GeneratedCanopyMeshes[] = {
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
             "SM_RaftSim_SouthForkPonderosaPineA_Billboard."
             "SM_RaftSim_SouthForkPonderosaPineA_Billboard"),
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
             "SM_RaftSim_SouthForkPonderosaPineB_Billboard."
             "SM_RaftSim_SouthForkPonderosaPineB_Billboard"),
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
             "SM_RaftSim_SouthForkPonderosaPineC_Billboard."
             "SM_RaftSim_SouthForkPonderosaPineC_Billboard"),
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
             "SM_RaftSim_SouthForkInteriorLiveOak_Billboard."
             "SM_RaftSim_SouthForkInteriorLiveOak_Billboard"),
        TEXT("/Game/RaftSim/Environment/SouthForkFullReach/Canopy/Meshes/"
             "SM_RaftSim_SouthForkWhiteAlder_Billboard."
             "SM_RaftSim_SouthForkWhiteAlder_Billboard")
    };
    for (const TCHAR* Path : GeneratedCanopyMeshes)
    {
        UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, Path);
        TestNotNull(FString::Printf(TEXT("Generated canopy loads: %s"), Path), Mesh);
        const FStaticMeshRenderData* RenderData = Mesh ? Mesh->GetRenderData() : nullptr;
        TestTrue(
            FString::Printf(TEXT("Generated canopy has render data: %s"), Path),
            RenderData != nullptr && !RenderData->LODResources.IsEmpty());
        if (RenderData && !RenderData->LODResources.IsEmpty())
        {
            const FStaticMeshLODResources& Lod = RenderData->LODResources[0];
            const uint32 VertexCount =
                Lod.VertexBuffers.PositionVertexBuffer.GetNumVertices();
            const uint32 IndexCount = Lod.IndexBuffer.GetNumIndices();
            TestTrue(
                FString::Printf(TEXT("Generated canopy uses at least two crossed planes: %s"), Path),
                VertexCount >= 8);
            TestTrue(
                FString::Printf(TEXT("Generated canopy radial topology is complete: %s"), Path),
                IndexCount >= 12 && VertexCount % 4 == 0 && IndexCount % 6 == 0);
        }
    }
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM8ContentLockTest,
    "RaftSim.M8.CContentLock",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FRaftSimM8ContentLockTest::RunTest(const FString& Parameters)
{
    FString ProjectDescriptor;
    TestTrue(TEXT("Project descriptor loads"), FFileHelper::LoadFileToString(
        ProjectDescriptor, *(FPaths::ProjectDir() / TEXT("SmokeEmIfYouGotEm.uproject"))));
    TSharedPtr<FJsonObject> DescriptorRoot;
    const TSharedRef<TJsonReader<>> DescriptorReader =
        TJsonReaderFactory<>::Create(ProjectDescriptor);
    TestTrue(TEXT("Project descriptor parses"),
        FJsonSerializer::Deserialize(DescriptorReader, DescriptorRoot) &&
        DescriptorRoot.IsValid());
    bool bOpenXRFound = false;
    bool bOpenXRDisabled = false;
    const TArray<TSharedPtr<FJsonValue>>* Plugins = nullptr;
    if (DescriptorRoot.IsValid() && DescriptorRoot->TryGetArrayField(TEXT("Plugins"), Plugins))
    {
        for (const TSharedPtr<FJsonValue>& PluginValue : *Plugins)
        {
            const TSharedPtr<FJsonObject> Plugin = PluginValue->AsObject();
            if (Plugin.IsValid() && Plugin->GetStringField(TEXT("Name")) == TEXT("OpenXR"))
            {
                bOpenXRFound = true;
                bOpenXRDisabled = !Plugin->GetBoolField(TEXT("Enabled"));
                break;
            }
        }
    }
    TestTrue(TEXT("OpenXR plugin entry exists"), bOpenXRFound);
    TestTrue(TEXT("OpenXR is disabled for 1.0"), bOpenXRDisabled);
    TestFalse(TEXT("Project description does not advertise 1.0 VR"),
        ProjectDescriptor.Contains(TEXT("VR support")));

    FString EngineConfig;
    TestTrue(TEXT("Engine config loads"), FFileHelper::LoadFileToString(
        EngineConfig, *(FPaths::ProjectConfigDir() / TEXT("DefaultEngine.ini"))));
    TestTrue(TEXT("HMD startup is disabled"), EngineConfig.Contains(TEXT("bEnableHMD=False")));
    TestTrue(TEXT("Irradiance-field radiance probes use the qualified resolution"),
        EngineConfig.Contains(TEXT("r.Lumen.IrradianceFieldGather.ProbeResolution=8")));
    TestTrue(TEXT("Irradiance-field occlusion probes match radiance probes"),
        EngineConfig.Contains(
            TEXT("r.Lumen.IrradianceFieldGather.OcclusionProbeResolution=8")));
    TestTrue(TEXT("Irradiance-field update budget remains bounded"),
        EngineConfig.Contains(
            TEXT("r.Lumen.IrradianceFieldGather.NumProbesToTraceBudget=50")));

    for (const FString& LicensePath : {
        RepoPath(TEXT("LICENSE")),
        RepoPath(TEXT("LICENSE-CONTENT.md")),
        RepoPath(TEXT("NOTICE.md")),
        RepoPath(TEXT("CREDITS.md"))})
    {
        TestTrue(FString::Printf(TEXT("Release rights file exists: %s"), *LicensePath),
            FPaths::FileExists(LicensePath));
    }

    const TSharedPtr<FJsonObject> Geography = LoadJson(
        *this,
        RepoPath(TEXT("physics/data/real_world/south_fork_american_chili_bar/"
                      "production_corridor/procedural_completion/manifest.json")),
        TEXT("Procedural geography manifest"));
    if (Geography.IsValid())
    {
        const TSharedPtr<FJsonObject> Acceptance = Geography->GetObjectField(TEXT("acceptance"));
        const TSharedPtr<FJsonObject> Authority = Geography->GetObjectField(TEXT("authority_policy"));
        TestTrue(TEXT("Full reach has no terrain voids"),
            Acceptance->GetBoolField(TEXT("full_reach_continuous")));
        TestTrue(TEXT("Procedural infill is explicitly labelled"),
            Acceptance->GetBoolField(TEXT("procedural_infill_explicitly_labelled")));
        TestTrue(TEXT("Procedural geography is not represented as surveyed"),
            Authority->GetBoolField(TEXT("never_claim_as_surveyed")));
        TestTrue(TEXT("Procedural geography is not for navigation"),
            Authority->GetBoolField(TEXT("not_for_navigation")));
        TestTrue(TEXT("Procedural seed is recorded"), Geography->GetIntegerField(TEXT("seed")) != 0);
    }

    const TSharedPtr<FJsonObject> FullReachBuild = LoadJson(
        *this,
        FPaths::ProjectContentDir() /
            TEXT("RaftSim/Environment/SouthForkFullReach/full_reach_environment_build_manifest.json"),
        TEXT("Full-reach environment build manifest"));
    if (FullReachBuild.IsValid())
    {
        TestTrue(TEXT("World Partition actor identities are deterministic"),
            FullReachBuild->GetBoolField(TEXT("deterministic_actor_guids")));
        TestTrue(TEXT("Deterministic actor identity set is populated"),
            FullReachBuild->GetIntegerField(TEXT("deterministic_actor_guid_count")) > 0);
        TestTrue(TEXT("External actor object names are deterministic"),
            FullReachBuild->GetBoolField(TEXT("deterministic_actor_object_names")));
        TestTrue(TEXT("Terminal visual water continuation is present"),
            FullReachBuild->GetBoolField(TEXT("terminal_visual_water_continuation")));
        TestTrue(TEXT("Terminal visual water has no gameplay collision"),
            !FullReachBuild->GetBoolField(
                TEXT("terminal_visual_water_affects_gameplay_collision")));
        TestTrue(TEXT("Terminal visual water does not affect hydraulics"),
            !FullReachBuild->GetBoolField(
                TEXT("terminal_visual_water_affects_hydraulics")));
        TestTrue(TEXT("Coarse shoreline holes receive procedural visual completion"),
            FullReachBuild->GetBoolField(
                TEXT("procedural_shoreline_completion_applied")));
        TestTrue(TEXT("Shoreline completion rule is explicitly non-authoritative"),
            FullReachBuild->GetStringField(
                TEXT("procedural_shoreline_completion_rule")).Contains(
                    TEXT("no collision or hydraulics")));
        const TSharedPtr<FJsonObject> FullReachMetrics =
            FullReachBuild->GetObjectField(TEXT("metrics"));
        TestTrue(TEXT("Procedural shoreline completion changed generated geometry"),
            FullReachMetrics->GetIntegerField(
                TEXT("procedural_shoreline_completion_vertices")) > 0);
        TestTrue(TEXT("Sub-cell shorelines use terrain-clipped transition cells"),
            FullReachMetrics->GetIntegerField(
                TEXT("procedural_shoreline_transition_cells")) > 0);
        TestEqual(TEXT("Deterministic actor GUID/name counts agree"),
            FullReachBuild->GetIntegerField(TEXT("deterministic_actor_object_name_count")),
            FullReachBuild->GetIntegerField(TEXT("deterministic_actor_guid_count")));
        const TSharedPtr<FJsonObject> InferredRelief =
            FullReachBuild->GetObjectField(TEXT("procedural_far_field_microrelief"));
        TestEqual(
            TEXT("Far-field relief is explicitly procedural"),
            InferredRelief->GetStringField(TEXT("algorithm")),
            FString(TEXT("world_space_slope_conditioned_domain_warped_ridged_fractal_v2")));
        TestTrue(TEXT("Far-field relief is non-colliding"),
            !InferredRelief->GetBoolField(TEXT("affects_gameplay_collision")));
        TestTrue(TEXT("Far-field relief does not affect hydraulics"),
            !InferredRelief->GetBoolField(TEXT("affects_hydraulics")));
        TestTrue(TEXT("Far-field relief stays below five metres"),
            InferredRelief->GetNumberField(TEXT("maximum_amplitude_m")) < 5.0);
        TestTrue(TEXT("Far-field ridges stay mesh-resolvable"),
            InferredRelief->GetNumberField(TEXT("ridge_wavelength_m")) >= 90.0);
        TestTrue(TEXT("Far-field domain warp remains bounded"),
            InferredRelief->GetNumberField(TEXT("maximum_domain_warp_m")) <= 32.0);
        TestTrue(TEXT("Far-field relief weights preserve the amplitude cap"),
            InferredRelief->GetNumberField(TEXT("broad_weight")) +
                    InferredRelief->GetNumberField(TEXT("detail_weight")) +
                    InferredRelief->GetNumberField(TEXT("ridge_weight")) <=
                1.0 + KINDA_SMALL_NUMBER);
    }

    const TSharedPtr<FJsonObject> Lock = LoadJson(
        *this,
        FPaths::ProjectContentDir() / TEXT("RaftSim/Production/m8_content_lock_manifest.json"),
        TEXT("M8 content lock manifest"));
    if (Lock.IsValid())
    {
        TestEqual(TEXT("Content lock schema"), Lock->GetStringField(TEXT("schema")),
            FString(TEXT("raftsim.m8.content_lock.v1")));
        TestTrue(TEXT("Content lock passes"), Lock->GetBoolField(TEXT("passed")));
        TestEqual(TEXT("Locked rapid count"), Lock->GetIntegerField(TEXT("rapid_count")), 20);
        TestEqual(TEXT("Locked rapid/flow count"), Lock->GetIntegerField(TEXT("rapid_flow_case_count")), 60);
    }
    return !HasAnyErrors();
}

#endif
