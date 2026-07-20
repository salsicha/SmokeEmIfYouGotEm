#if WITH_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "Dom/JsonObject.h"
#include "HAL/FileManager.h"
#include "Materials/MaterialInterface.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "../RaftSimContentLockDirector.h"
#include "RaftSimWaterRuntimeAdapter.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

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
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PhotorealRiverTerrain.M_RaftSim_PhotorealRiverTerrain"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_Asphalt.M_RaftSim_Asphalt"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_Timber.M_RaftSim_Timber"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_RiverBoulder.M_RaftSim_RiverBoulder"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_RaftTube.M_RaftSim_RaftTube"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_RaftFloor.M_RaftSim_RaftFloor"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_Wetsuit.M_RaftSim_Wetsuit"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_Skin.M_RaftSim_Skin"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_Helmet.M_RaftSim_Helmet"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PaddleShaft.M_RaftSim_PaddleShaft"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PaddleBlade.M_RaftSim_PaddleBlade"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_CrewPFD.M_RaftSim_CrewPFD"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PFD_Red.M_RaftSim_PFD_Red"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PFD_Yellow.M_RaftSim_PFD_Yellow"),
        TEXT("/Game/RaftSim/Materials/M_RaftSim_PFD_Blue.M_RaftSim_PFD_Blue")
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
