#include "Dom/JsonObject.h"
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "../RaftSimContentLockDirector.h"
#include "RaftSimSaveSubsystem.h"
#include "RaftSimVerticalSliceFrontend.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM9ReleaseManifestContractTest,
    "RaftSim.M9.AReleaseManifestContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM9ReleaseCandidateQATest,
    "RaftSim.M9.BReleaseCandidateQA",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimM9FutureSaveProtectionTest,
    "RaftSim.M9.CFutureSaveProtection",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

namespace
{
bool ParseJsonText(const FString& Text, TSharedPtr<FJsonObject>& OutRoot)
{
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Text);
    return FJsonSerializer::Deserialize(Reader, OutRoot) && OutRoot.IsValid();
}
}

bool FRaftSimM9ReleaseManifestContractTest::RunTest(const FString&)
{
    const FString ManifestPath = FPaths::Combine(
        FPaths::ProjectContentDir(),
        TEXT("RaftSim/Production/m9_release_candidate_manifest.json"));
    FString Text;
    TestTrue(TEXT("tracked M9 release manifest loads"),
        FFileHelper::LoadFileToString(Text, *ManifestPath));
    TSharedPtr<FJsonObject> Root;
    if (!ParseJsonText(Text, Root))
    {
        AddError(TEXT("M9 release manifest is not valid JSON"));
        return false;
    }
    TestEqual(TEXT("release version is locked"),
        Root->GetStringField(TEXT("release_version")), FString(TEXT("1.0.0-rc1")));
    TestEqual(TEXT("release branch is locked"),
        Root->GetStringField(TEXT("release_branch")), FString(TEXT("release/1.0")));
    const TSharedPtr<FJsonObject>* Evidence = nullptr;
    TestTrue(TEXT("immutable evidence map is present"),
        Root->TryGetObjectField(TEXT("required_evidence"), Evidence) && Evidence != nullptr);
    TestTrue(TEXT("promotion rule requires every evidence lane"),
        Root->GetStringField(TEXT("promotion_rule")).Contains(TEXT("every required_evidence")));
    return true;
}

bool FRaftSimM9ReleaseCandidateQATest::RunTest(const FString&)
{
    FString ReportJson;
    const bool bPassed = ARaftSimContentLockDirector::RunReleaseCandidateQA(ReportJson);
    TestTrue(TEXT("logical release-candidate QA passes"), bPassed);
    TSharedPtr<FJsonObject> Root;
    if (!ParseJsonText(ReportJson, Root))
    {
        AddError(TEXT("release-candidate QA did not emit valid JSON"));
        return false;
    }
    TestEqual(TEXT("release QA schema"), Root->GetStringField(TEXT("schema")),
        FString(TEXT("raftsim.m9.release_candidate_qa.v1")));
    TestTrue(TEXT("release QA report passes"), Root->GetBoolField(TEXT("passed")));
    const TSharedPtr<FJsonObject>* Gates = nullptr;
    TestTrue(TEXT("release QA gates are present"),
        Root->TryGetObjectField(TEXT("gates"), Gates) && Gates != nullptr);
    return true;
}

bool FRaftSimM9FutureSaveProtectionTest::RunTest(const FString&)
{
    URaftSimVerticalSliceSaveGame* Save = NewObject<URaftSimVerticalSliceSaveGame>();
    Save->SaveVersion = URaftSimSaveSubsystem::CurrentSaveVersion + 1;
    Save->CompletedScenarioIds.Add(TEXT("future_progress"));
    Save->Settings.UiScale = 8.0f;

    TestFalse(TEXT("newer save is not writable by this build"),
        URaftSimSaveSubsystem::NormalizeSave(Save));
    TestEqual(TEXT("newer version is not downgraded"), Save->SaveVersion,
        URaftSimSaveSubsystem::CurrentSaveVersion + 1);
    TestEqual(TEXT("newer settings are not normalized"), Save->Settings.UiScale, 8.0f);
    TestTrue(TEXT("newer progress remains intact"),
        Save->CompletedScenarioIds.Contains(TEXT("future_progress")));
    return true;
}

#endif
