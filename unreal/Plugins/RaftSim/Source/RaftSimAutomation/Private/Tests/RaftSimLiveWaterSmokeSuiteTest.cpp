#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimLiveWaterSmokeSuiteManifestTest,
    "RaftSim.Milestone20.LiveWaterSmokeSuiteManifest",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter
)

bool FRaftSimLiveWaterSmokeSuiteManifestTest::RunTest(const FString& Parameters)
{
    const FString ManifestPath = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(
            FPaths::ProjectContentDir(),
            TEXT("RaftSim/Automation/live_water_smoke_suite.json")
        )
    );

    FString ManifestText;
    if (!FFileHelper::LoadFileToString(ManifestText, *ManifestPath))
    {
        AddError(FString::Printf(TEXT("Missing live-water smoke suite manifest: %s"), *ManifestPath));
        return false;
    }

    TSharedPtr<FJsonObject> Root;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ManifestText);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        AddError(TEXT("Live-water smoke suite manifest is not valid JSON."));
        return false;
    }

    TestEqual(
        TEXT("schema"),
        Root->GetStringField(TEXT("schema")),
        FString(TEXT("raftsim.unreal.live_water_smoke_suite.v1"))
    );
    TestEqual(
        TEXT("automation_test_name"),
        Root->GetStringField(TEXT("automation_test_name")),
        FString(TEXT("RaftSim.Milestone20.LiveWaterSmokeSuite"))
    );
    TestEqual(TEXT("status"), Root->GetStringField(TEXT("status")), FString(TEXT("ready_for_unreal_automation_execution")));

    const TArray<TSharedPtr<FJsonValue>>* Checks = nullptr;
    if (!Root->TryGetArrayField(TEXT("checks"), Checks) || Checks == nullptr)
    {
        AddError(TEXT("Live-water smoke suite manifest must contain checks."));
        return false;
    }
    TestEqual(TEXT("check count"), Checks->Num(), 7);
    for (const TSharedPtr<FJsonValue>& CheckValue : *Checks)
    {
        const TSharedPtr<FJsonObject> Check = CheckValue->AsObject();
        if (!Check.IsValid())
        {
            AddError(TEXT("Every live-water smoke check must be an object."));
            return false;
        }
        TestTrue(Check->GetStringField(TEXT("check_id")), Check->GetBoolField(TEXT("passed")));
    }

    const TArray<TSharedPtr<FJsonValue>>* TargetProfiles = nullptr;
    if (!Root->TryGetArrayField(TEXT("target_profiles"), TargetProfiles)
        || TargetProfiles == nullptr
        || TargetProfiles->Num() != 3)
    {
        AddError(TEXT("Live-water smoke suite must declare desktop, VR, and handheld target profiles."));
        return false;
    }

    return true;
}

#endif
