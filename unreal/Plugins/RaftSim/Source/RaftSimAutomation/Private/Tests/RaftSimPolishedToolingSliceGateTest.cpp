#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimPolishedToolingSliceGateManifestTest,
    "RaftSim.Milestone25A.PolishedToolingSliceGateManifest",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter
)

bool FRaftSimPolishedToolingSliceGateManifestTest::RunTest(const FString& Parameters)
{
    const FString ManifestPath = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(
            FPaths::ProjectContentDir(),
            TEXT("RaftSim/Automation/polished_tooling_slice_gate.json")
        )
    );

    FString ManifestText;
    if (!FFileHelper::LoadFileToString(ManifestText, *ManifestPath))
    {
        AddError(FString::Printf(TEXT("Missing polished tooling slice gate manifest: %s"), *ManifestPath));
        return false;
    }

    TSharedPtr<FJsonObject> Root;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ManifestText);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        AddError(TEXT("Polished tooling slice gate manifest is not valid JSON."));
        return false;
    }

    TestEqual(
        TEXT("schema"),
        Root->GetStringField(TEXT("schema")),
        FString(TEXT("raftsim.unreal.polished_tooling_slice_gate.v1"))
    );
    TestEqual(TEXT("automation_module"), Root->GetStringField(TEXT("automation_module")), FString(TEXT("RaftSimAutomation")));
    TestEqual(
        TEXT("automation_test_name"),
        Root->GetStringField(TEXT("automation_test_name")),
        FString(TEXT("RaftSim.Milestone25A.PolishedToolingSliceGateManifest"))
    );
    TestEqual(TEXT("tool_count"), Root->GetIntegerField(TEXT("tool_count")), 5);
    TestEqual(TEXT("validation_action_count"), Root->GetIntegerField(TEXT("validation_action_count")), 7);

    const TArray<TSharedPtr<FJsonValue>>* ToolSurfaces = nullptr;
    if (!Root->TryGetArrayField(TEXT("tool_surfaces"), ToolSurfaces)
        || ToolSurfaces == nullptr
        || ToolSurfaces->Num() != 5)
    {
        AddError(TEXT("Polished tooling gate must declare five tool surfaces."));
        return false;
    }

    const TArray<TSharedPtr<FJsonValue>>* GateChecks = nullptr;
    if (!Root->TryGetArrayField(TEXT("gate_checks"), GateChecks)
        || GateChecks == nullptr
        || GateChecks->Num() != 7)
    {
        AddError(TEXT("Polished tooling gate must declare seven gate checks."));
        return false;
    }

    for (const TSharedPtr<FJsonValue>& CheckValue : *GateChecks)
    {
        const TSharedPtr<FJsonObject> Check = CheckValue->AsObject();
        if (!Check.IsValid())
        {
            AddError(TEXT("Every polished tooling gate check must be an object."));
            return false;
        }

        TestTrue(Check->GetStringField(TEXT("check_id")), Check->GetBoolField(TEXT("passed")));
    }

    return true;
}

#endif
