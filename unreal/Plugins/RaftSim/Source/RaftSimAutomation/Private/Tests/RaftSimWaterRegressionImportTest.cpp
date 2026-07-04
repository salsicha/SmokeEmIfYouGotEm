#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimWaterRegressionImportManifestTest,
    "RaftSim.Milestone20.WaterRegressionImportManifest",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter
)

bool FRaftSimWaterRegressionImportManifestTest::RunTest(const FString& Parameters)
{
    const FString ManifestPath = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(
            FPaths::ProjectContentDir(),
            TEXT("RaftSim/Automation/water_regression_fixture_import.json")
        )
    );

    FString ManifestText;
    if (!FFileHelper::LoadFileToString(ManifestText, *ManifestPath))
    {
        AddError(FString::Printf(TEXT("Missing water regression import manifest: %s"), *ManifestPath));
        return false;
    }

    TSharedPtr<FJsonObject> Root;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ManifestText);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        AddError(TEXT("Water regression import manifest is not valid JSON."));
        return false;
    }

    TestEqual(
        TEXT("schema"),
        Root->GetStringField(TEXT("schema")),
        FString(TEXT("raftsim.unreal.regression_fixture_import.v1"))
    );
    TestEqual(TEXT("automation_module"), Root->GetStringField(TEXT("automation_module")), FString(TEXT("RaftSimAutomation")));
    TestEqual(TEXT("total_fixture_count"), Root->GetIntegerField(TEXT("total_fixture_count")), 109);

    const TArray<TSharedPtr<FJsonValue>>* ComparisonModes = nullptr;
    if (!Root->TryGetArrayField(TEXT("comparison_modes"), ComparisonModes)
        || ComparisonModes == nullptr
        || ComparisonModes->Num() != 2)
    {
        AddError(TEXT("Water regression import manifest must declare two comparison modes."));
        return false;
    }

    const TSharedPtr<FJsonObject>* SourceMilestones = nullptr;
    if (!Root->TryGetObjectField(TEXT("source_milestones"), SourceMilestones)
        || SourceMilestones == nullptr
        || !SourceMilestones->IsValid())
    {
        AddError(TEXT("Water regression import manifest must declare source_milestones."));
        return false;
    }

    const TSharedPtr<FJsonObject>* Milestone16 = nullptr;
    const TSharedPtr<FJsonObject>* Milestone17 = nullptr;
    const TSharedPtr<FJsonObject>* Milestone18 = nullptr;
    if (!(*SourceMilestones)->TryGetObjectField(TEXT("milestone16"), Milestone16)
        || !(*SourceMilestones)->TryGetObjectField(TEXT("milestone17"), Milestone17)
        || !(*SourceMilestones)->TryGetObjectField(TEXT("milestone18"), Milestone18)
        || Milestone16 == nullptr
        || Milestone17 == nullptr
        || Milestone18 == nullptr
        || !Milestone16->IsValid()
        || !Milestone17->IsValid()
        || !Milestone18->IsValid())
    {
        AddError(TEXT("Water regression import manifest must declare Milestone 16/17/18 groups."));
        return false;
    }

    TestEqual(TEXT("Milestone 16 fixture count"), (*Milestone16)->GetIntegerField(TEXT("fixture_count")), 98);
    TestEqual(TEXT("Milestone 17 fixture count"), (*Milestone17)->GetIntegerField(TEXT("fixture_count")), 7);
    TestEqual(TEXT("Milestone 18 fixture count"), (*Milestone18)->GetIntegerField(TEXT("fixture_count")), 4);
    return true;
}

#endif
