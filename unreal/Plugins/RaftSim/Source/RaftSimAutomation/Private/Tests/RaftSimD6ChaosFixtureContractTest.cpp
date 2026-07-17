#if WITH_DEV_AUTOMATION_TESTS

#include "Containers/Set.h"
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimD6ChaosFixtureContractTest,
    "RaftSim.D6.ChaosFixtureContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter
)

namespace
{
const TArray<FString> RequiredD6FixtureIds = {
    TEXT("static_seat_load_sag"),
    TEXT("traveling_crew_shift"),
    TEXT("rock_pinch_wrap"),
    TEXT("upstream_tube_overwash_flip"),
    TEXT("timed_high_side_save"),
    TEXT("post_contact_recovery"),
    TEXT("pressure_flow_sweeps"),
};

bool JsonStringArrayContains(
    const TSharedPtr<FJsonObject>& Object,
    const FString& FieldName,
    const FString& ExpectedValue
)
{
    const TArray<TSharedPtr<FJsonValue>>* Values = nullptr;
    if (!Object->TryGetArrayField(FieldName, Values) || Values == nullptr)
    {
        return false;
    }
    for (const TSharedPtr<FJsonValue>& Value : *Values)
    {
        if (Value.IsValid() && Value->AsString() == ExpectedValue)
        {
            return true;
        }
    }
    return false;
}
}

bool FRaftSimD6ChaosFixtureContractTest::RunTest(const FString& Parameters)
{
    const FString ContractPath = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(
            FPaths::ProjectContentDir(),
            TEXT("RaftSim/Physics/flexible_raft_d6_chaos_fixture_contract.json")
        )
    );

    FString ContractText;
    if (!FFileHelper::LoadFileToString(ContractText, *ContractPath))
    {
        AddError(FString::Printf(TEXT("Missing D6 Chaos fixture contract: %s"), *ContractPath));
        return false;
    }

    TSharedPtr<FJsonObject> Root;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ContractText);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        AddError(TEXT("D6 Chaos fixture contract is not valid JSON."));
        return false;
    }

    TestEqual(
        TEXT("schema"),
        Root->GetStringField(TEXT("schema")),
        FString(TEXT("raftsim.flexible_raft.d6_chaos_fixture_contract.v1"))
    );
    TestEqual(TEXT("runtime"), Root->GetStringField(TEXT("runtime")), FString(TEXT("UnrealChaos")));
    TestEqual(
        TEXT("status"),
        Root->GetStringField(TEXT("status")),
        FString(TEXT("chaos_fixture_contract_ready_runner_implementation_pending"))
    );
    TestFalse(TEXT("d6_complete"), Root->GetBoolField(TEXT("d6_complete")));
    TestFalse(TEXT("production_promoted"), Root->GetBoolField(TEXT("production_promoted")));
    TestEqual(TEXT("job_count"), static_cast<int32>(Root->GetIntegerField(TEXT("job_count"))), 7);

    const TArray<TSharedPtr<FJsonValue>>* FixtureIds = nullptr;
    if (!Root->TryGetArrayField(TEXT("required_fixture_ids"), FixtureIds) || FixtureIds == nullptr)
    {
        AddError(TEXT("D6 Chaos fixture contract must declare required_fixture_ids."));
        return false;
    }
    TestEqual(TEXT("required fixture id count"), FixtureIds->Num(), RequiredD6FixtureIds.Num());
    for (const FString& FixtureId : RequiredD6FixtureIds)
    {
        TestTrue(
            FString::Printf(TEXT("required_fixture_ids contains %s"), *FixtureId),
            JsonStringArrayContains(Root, TEXT("required_fixture_ids"), FixtureId)
        );
    }

    const TSharedPtr<FJsonObject>* PromotionGate = nullptr;
    if (!Root->TryGetObjectField(TEXT("promotion_gate"), PromotionGate) || PromotionGate == nullptr)
    {
        AddError(TEXT("D6 Chaos fixture contract must declare a promotion_gate object."));
        return false;
    }
    TestFalse(TEXT("may_mark_d6_complete"), (*PromotionGate)->GetBoolField(TEXT("may_mark_d6_complete")));
    TestFalse(TEXT("may_drive_runtime_gameplay"), (*PromotionGate)->GetBoolField(TEXT("may_drive_runtime_gameplay")));
    TestFalse(TEXT("may_substitute_python_reference"), (*PromotionGate)->GetBoolField(TEXT("may_substitute_python_reference")));

    const TArray<TSharedPtr<FJsonValue>>* Jobs = nullptr;
    if (!Root->TryGetArrayField(TEXT("jobs"), Jobs) || Jobs == nullptr)
    {
        AddError(TEXT("D6 Chaos fixture contract must contain a jobs array."));
        return false;
    }
    TestEqual(TEXT("job array count"), Jobs->Num(), RequiredD6FixtureIds.Num());

    TSet<FString> SeenFixtureIds;
    for (const TSharedPtr<FJsonValue>& JobValue : *Jobs)
    {
        const TSharedPtr<FJsonObject> Job = JobValue->AsObject();
        if (!Job.IsValid())
        {
            AddError(TEXT("Every D6 Chaos job entry must be a JSON object."));
            return false;
        }

        FString FixtureId;
        if (!Job->TryGetStringField(TEXT("fixture_id"), FixtureId) || FixtureId.IsEmpty())
        {
            AddError(TEXT("D6 Chaos job is missing fixture_id."));
            return false;
        }
        SeenFixtureIds.Add(FixtureId);

        TestEqual(
            FString::Printf(TEXT("%s status"), *FixtureId),
            Job->GetStringField(TEXT("status")),
            FString(TEXT("ready_for_unreal_runner_implementation_pending"))
        );
        TestEqual(
            FString::Printf(TEXT("%s runtime"), *FixtureId),
            Job->GetStringField(TEXT("runtime")),
            FString(TEXT("UnrealChaos"))
        );
        TestEqual(
            FString::Printf(TEXT("%s comparison mode"), *FixtureId),
            Job->GetStringField(TEXT("comparison_mode")),
            FString(TEXT("baseline_delta_recording"))
        );
        TestFalse(
            FString::Printf(TEXT("%s metric_deltas_are_failures"), *FixtureId),
            Job->GetBoolField(TEXT("metric_deltas_are_failures"))
        );
        TestTrue(
            FString::Printf(TEXT("%s requires telemetry_sha256"), *FixtureId),
            JsonStringArrayContains(Job, TEXT("required_output_fields"), TEXT("telemetry_sha256"))
        );
        TestTrue(
            FString::Printf(TEXT("%s requires metrics"), *FixtureId),
            JsonStringArrayContains(Job, TEXT("required_output_fields"), TEXT("metrics"))
        );
        TestTrue(
            FString::Printf(TEXT("%s requires determinism hash"), *FixtureId),
            JsonStringArrayContains(Job, TEXT("required_telemetry_fields"), TEXT("determinism_hash"))
        );

        const TSharedPtr<FJsonObject>* Guardrails = nullptr;
        if (!Job->TryGetObjectField(TEXT("guardrails"), Guardrails) || Guardrails == nullptr)
        {
            AddError(FString::Printf(TEXT("D6 Chaos job %s must declare guardrails."), *FixtureId));
            return false;
        }
        TestFalse(
            FString::Printf(TEXT("%s may_promote_fixture"), *FixtureId),
            (*Guardrails)->GetBoolField(TEXT("may_promote_fixture"))
        );
        TestFalse(
            FString::Printf(TEXT("%s may_drive_scoring_critical_physics"), *FixtureId),
            (*Guardrails)->GetBoolField(TEXT("may_drive_scoring_critical_physics"))
        );
        TestFalse(
            FString::Printf(TEXT("%s may_substitute_python_reference"), *FixtureId),
            (*Guardrails)->GetBoolField(TEXT("may_substitute_python_reference"))
        );
        TestTrue(
            FString::Printf(TEXT("%s must_preserve_fixture_input_semantics"), *FixtureId),
            (*Guardrails)->GetBoolField(TEXT("must_preserve_fixture_input_semantics"))
        );
    }

    for (const FString& FixtureId : RequiredD6FixtureIds)
    {
        TestTrue(
            FString::Printf(TEXT("D6 Chaos jobs contain %s"), *FixtureId),
            SeenFixtureIds.Contains(FixtureId)
        );
    }

    return true;
}

#endif
