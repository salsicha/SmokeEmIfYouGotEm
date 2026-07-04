#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimChaosAutomationFixturesManifestTest,
    "RaftSim.Milestone19.ChaosAutomationFixturesManifest",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter
)

bool FRaftSimChaosAutomationFixturesManifestTest::RunTest(const FString& Parameters)
{
    const FString ManifestPath = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(
            FPaths::ProjectContentDir(),
            TEXT("RaftSim/Physics/chaos_automation_fixtures.json")
        )
    );

    FString ManifestText;
    if (!FFileHelper::LoadFileToString(ManifestText, *ManifestPath))
    {
        AddError(FString::Printf(TEXT("Missing Chaos automation manifest: %s"), *ManifestPath));
        return false;
    }

    TSharedPtr<FJsonObject> Root;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ManifestText);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        AddError(TEXT("Chaos automation manifest is not valid JSON."));
        return false;
    }

    TestEqual(
        TEXT("target_runtime"),
        Root->GetStringField(TEXT("target_runtime")),
        FString(TEXT("UnrealChaos"))
    );
    TestEqual(
        TEXT("decision"),
        Root->GetStringField(TEXT("decision")),
        FString(TEXT("automation_fixture_export_complete_not_authority_evidence"))
    );

    const TArray<TSharedPtr<FJsonValue>>* Fixtures = nullptr;
    if (!Root->TryGetArrayField(TEXT("fixtures"), Fixtures) || Fixtures == nullptr)
    {
        AddError(TEXT("Chaos automation manifest must contain a fixtures array."));
        return false;
    }

    TestEqual(TEXT("fixture count"), Fixtures->Num(), 6);

    for (const TSharedPtr<FJsonValue>& FixtureValue : *Fixtures)
    {
        const TSharedPtr<FJsonObject> Fixture = FixtureValue->AsObject();
        if (!Fixture.IsValid())
        {
            AddError(TEXT("Every Chaos automation fixture entry must be a JSON object."));
            return false;
        }

        FString FixtureId;
        if (!Fixture->TryGetStringField(TEXT("fixture_id"), FixtureId) || FixtureId.IsEmpty())
        {
            AddError(TEXT("Chaos automation fixture is missing fixture_id."));
            return false;
        }

        TestEqual(
            FString::Printf(TEXT("%s status"), *FixtureId),
            Fixture->GetStringField(TEXT("status")),
            FString(TEXT("ready_for_unreal_automation_execution"))
        );
        TestFalse(
            FString::Printf(TEXT("%s authoritative_evidence"), *FixtureId),
            Fixture->GetBoolField(TEXT("authoritative_evidence"))
        );

        const TArray<TSharedPtr<FJsonValue>>* TelemetryFields = nullptr;
        if (!Fixture->TryGetArrayField(TEXT("telemetry_required"), TelemetryFields)
            || TelemetryFields == nullptr
            || TelemetryFields->Num() == 0)
        {
            AddError(
                FString::Printf(
                    TEXT("Chaos automation fixture %s must declare required telemetry fields."),
                    *FixtureId
                )
            );
            return false;
        }
    }

    return true;
}

#endif
