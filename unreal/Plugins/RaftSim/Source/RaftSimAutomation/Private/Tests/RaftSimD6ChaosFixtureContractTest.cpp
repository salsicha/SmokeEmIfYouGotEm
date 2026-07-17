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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimD6ChaosRunnerExportBundleTest,
    "RaftSim.D6.ChaosRunnerExportBundle",
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

bool LoadD6ChaosFixtureContract(
    FAutomationTestBase& Test,
    TSharedPtr<FJsonObject>& OutRoot
)
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
        Test.AddError(FString::Printf(TEXT("Missing D6 Chaos fixture contract: %s"), *ContractPath));
        return false;
    }

    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ContractText);
    if (!FJsonSerializer::Deserialize(Reader, OutRoot) || !OutRoot.IsValid())
    {
        Test.AddError(TEXT("D6 Chaos fixture contract is not valid JSON."));
        return false;
    }

    return true;
}

FString D6RepoRootPath()
{
    return FPaths::ConvertRelativePathToFull(
        FPaths::Combine(FPaths::ProjectDir(), TEXT(".."))
    );
}

bool LoadD6JsonFile(
    FAutomationTestBase& Test,
    const FString& FullPath,
    const FString& Label,
    TSharedPtr<FJsonObject>& OutRoot
)
{
    FString JsonText;
    if (!FFileHelper::LoadFileToString(JsonText, *FullPath))
    {
        Test.AddError(FString::Printf(TEXT("Missing %s JSON: %s"), *Label, *FullPath));
        return false;
    }

    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonText);
    if (!FJsonSerializer::Deserialize(Reader, OutRoot) || !OutRoot.IsValid())
    {
        Test.AddError(FString::Printf(TEXT("%s JSON is invalid: %s"), *Label, *FullPath));
        return false;
    }

    return true;
}

TSharedPtr<FJsonObject> FindD6ChaosFixtureJob(
    FAutomationTestBase& Test,
    const TSharedPtr<FJsonObject>& Root,
    const FString& FixtureId
)
{
    const TArray<TSharedPtr<FJsonValue>>* Jobs = nullptr;
    if (!Root->TryGetArrayField(TEXT("jobs"), Jobs) || Jobs == nullptr)
    {
        Test.AddError(TEXT("D6 Chaos fixture contract must contain a jobs array."));
        return nullptr;
    }

    for (const TSharedPtr<FJsonValue>& JobValue : *Jobs)
    {
        const TSharedPtr<FJsonObject> Job = JobValue->AsObject();
        if (!Job.IsValid())
        {
            Test.AddError(TEXT("Every D6 Chaos job entry must be a JSON object."));
            return nullptr;
        }

        FString JobFixtureId;
        if (
            Job->TryGetStringField(TEXT("fixture_id"), JobFixtureId)
            && JobFixtureId == FixtureId
        )
        {
            return Job;
        }
    }

    Test.AddError(FString::Printf(TEXT("Missing D6 Chaos fixture job: %s"), *FixtureId));
    return nullptr;
}

bool ValidateD6ChaosFixtureJob(
    FAutomationTestBase& Test,
    const FString& FixtureId,
    const FString& ExpectedAutomationTestName
)
{
    TSharedPtr<FJsonObject> Root;
    if (!LoadD6ChaosFixtureContract(Test, Root))
    {
        return false;
    }

    const TSharedPtr<FJsonObject> Job = FindD6ChaosFixtureJob(Test, Root, FixtureId);
    if (!Job.IsValid())
    {
        return false;
    }

    Test.TestEqual(
        FString::Printf(TEXT("%s automation_test_name"), *FixtureId),
        Job->GetStringField(TEXT("automation_test_name")),
        ExpectedAutomationTestName
    );
    Test.TestEqual(
        FString::Printf(TEXT("%s status"), *FixtureId),
        Job->GetStringField(TEXT("status")),
        FString(TEXT("ready_for_unreal_runner_implementation_pending"))
    );
    Test.TestEqual(
        FString::Printf(TEXT("%s runtime"), *FixtureId),
        Job->GetStringField(TEXT("runtime")),
        FString(TEXT("UnrealChaos"))
    );
    Test.TestTrue(
        FString::Printf(TEXT("%s requires telemetry_sha256"), *FixtureId),
        JsonStringArrayContains(Job, TEXT("required_output_fields"), TEXT("telemetry_sha256"))
    );
    Test.TestTrue(
        FString::Printf(TEXT("%s requires metrics"), *FixtureId),
        JsonStringArrayContains(Job, TEXT("required_output_fields"), TEXT("metrics"))
    );
    Test.TestTrue(
        FString::Printf(TEXT("%s requires determinism hash"), *FixtureId),
        JsonStringArrayContains(Job, TEXT("required_telemetry_fields"), TEXT("determinism_hash"))
    );

    const TArray<TSharedPtr<FJsonValue>>* RequiredMetricPaths = nullptr;
    if (
        !Job->TryGetArrayField(TEXT("required_metric_paths"), RequiredMetricPaths)
        || RequiredMetricPaths == nullptr
        || RequiredMetricPaths->Num() == 0
    )
    {
        Test.AddError(FString::Printf(TEXT("D6 Chaos fixture job %s must declare required metrics."), *FixtureId));
        return false;
    }

    const TSharedPtr<FJsonObject>* Guardrails = nullptr;
    if (!Job->TryGetObjectField(TEXT("guardrails"), Guardrails) || Guardrails == nullptr)
    {
        Test.AddError(FString::Printf(TEXT("D6 Chaos fixture job %s must declare guardrails."), *FixtureId));
        return false;
    }
    Test.TestFalse(
        FString::Printf(TEXT("%s may_promote_fixture"), *FixtureId),
        (*Guardrails)->GetBoolField(TEXT("may_promote_fixture"))
    );
    Test.TestFalse(
        FString::Printf(TEXT("%s may_drive_scoring_critical_physics"), *FixtureId),
        (*Guardrails)->GetBoolField(TEXT("may_drive_scoring_critical_physics"))
    );
    Test.TestFalse(
        FString::Printf(TEXT("%s may_substitute_python_reference"), *FixtureId),
        (*Guardrails)->GetBoolField(TEXT("may_substitute_python_reference"))
    );
    Test.TestTrue(
        FString::Printf(TEXT("%s must_export_64_hex_telemetry_sha256"), *FixtureId),
        (*Guardrails)->GetBoolField(TEXT("must_export_64_hex_telemetry_sha256"))
    );
    Test.TestTrue(
        FString::Printf(TEXT("%s must_preserve_fixture_input_semantics"), *FixtureId),
        (*Guardrails)->GetBoolField(TEXT("must_preserve_fixture_input_semantics"))
    );

    return true;
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

bool FRaftSimD6ChaosRunnerExportBundleTest::RunTest(const FString& Parameters)
{
    TSharedPtr<FJsonObject> ContractRoot;
    if (!LoadD6ChaosFixtureContract(*this, ContractRoot))
    {
        return false;
    }

    const TSharedPtr<FJsonObject>* AutomationExport = nullptr;
    if (
        !ContractRoot->TryGetObjectField(TEXT("automation_export"), AutomationExport)
        || AutomationExport == nullptr
    )
    {
        AddError(TEXT("D6 Chaos contract must declare automation_export."));
        return false;
    }

    const FString RepoRoot = D6RepoRootPath();
    const FString SummaryPath = FPaths::Combine(
        RepoRoot,
        (*AutomationExport)->GetStringField(TEXT("summary"))
    );
    const FString SidecarPath = FPaths::Combine(
        RepoRoot,
        (*AutomationExport)->GetStringField(TEXT("measured_results_sidecar"))
    );

    TSharedPtr<FJsonObject> SummaryRoot;
    if (!LoadD6JsonFile(*this, SummaryPath, TEXT("D6 Chaos runner summary"), SummaryRoot))
    {
        return false;
    }
    TSharedPtr<FJsonObject> SidecarRoot;
    if (!LoadD6JsonFile(*this, SidecarPath, TEXT("D6 Chaos runner sidecar"), SidecarRoot))
    {
        return false;
    }

    TestEqual(
        TEXT("runner summary schema"),
        SummaryRoot->GetStringField(TEXT("schema")),
        FString(TEXT("raftsim.flexible_raft.d6_chaos_runner_summary.v1"))
    );
    TestEqual(
        TEXT("runner summary status"),
        SummaryRoot->GetStringField(TEXT("status")),
        FString(TEXT("chaos_runner_output_pending_no_measurements_recorded"))
    );
    TestFalse(TEXT("runner summary d6_complete"), SummaryRoot->GetBoolField(TEXT("d6_complete")));
    TestFalse(
        TEXT("runner summary production_promoted"),
        SummaryRoot->GetBoolField(TEXT("production_promoted"))
    );
    TestEqual(
        TEXT("runner sidecar path"),
        SummaryRoot->GetStringField(TEXT("runner_output_sidecar")),
        (*AutomationExport)->GetStringField(TEXT("measured_results_sidecar"))
    );
    TestEqual(
        TEXT("runner summary fixture_count"),
        static_cast<int32>(SummaryRoot->GetIntegerField(TEXT("fixture_count"))),
        RequiredD6FixtureIds.Num()
    );
    TestEqual(
        TEXT("runner summary filled_fixture_count"),
        static_cast<int32>(SummaryRoot->GetIntegerField(TEXT("filled_fixture_count"))),
        0
    );
    TestEqual(
        TEXT("runner summary invalid_fixture_count"),
        static_cast<int32>(SummaryRoot->GetIntegerField(TEXT("invalid_fixture_count"))),
        RequiredD6FixtureIds.Num()
    );
    TestFalse(
        TEXT("runner can_merge_sidecar"),
        SummaryRoot->GetBoolField(TEXT("can_merge_sidecar"))
    );

    const TSharedPtr<FJsonObject>* SummaryPromotionGate = nullptr;
    if (
        !SummaryRoot->TryGetObjectField(TEXT("promotion_gate"), SummaryPromotionGate)
        || SummaryPromotionGate == nullptr
    )
    {
        AddError(TEXT("D6 Chaos runner summary must declare promotion_gate."));
        return false;
    }
    TestFalse(
        TEXT("runner may_mark_d6_complete"),
        (*SummaryPromotionGate)->GetBoolField(TEXT("may_mark_d6_complete"))
    );
    TestFalse(
        TEXT("runner may_merge_into_measured_results_template"),
        (*SummaryPromotionGate)->GetBoolField(TEXT("may_merge_into_measured_results_template"))
    );

    const TArray<TSharedPtr<FJsonValue>>* Jobs = nullptr;
    if (!SummaryRoot->TryGetArrayField(TEXT("jobs"), Jobs) || Jobs == nullptr)
    {
        AddError(TEXT("D6 Chaos runner summary must contain jobs."));
        return false;
    }
    TestEqual(TEXT("runner job count"), Jobs->Num(), RequiredD6FixtureIds.Num());

    TSet<FString> SeenFixtureIds;
    for (const TSharedPtr<FJsonValue>& JobValue : *Jobs)
    {
        const TSharedPtr<FJsonObject> Job = JobValue->AsObject();
        if (!Job.IsValid())
        {
            AddError(TEXT("Every D6 Chaos runner job entry must be a JSON object."));
            return false;
        }

        const FString FixtureId = Job->GetStringField(TEXT("fixture_id"));
        SeenFixtureIds.Add(FixtureId);
        TestFalse(
            FString::Printf(TEXT("%s ready_for_sidecar_merge"), *FixtureId),
            Job->GetBoolField(TEXT("ready_for_sidecar_merge"))
        );
        TestEqual(
            FString::Printf(TEXT("%s blocking_reason"), *FixtureId),
            Job->GetStringField(TEXT("blocking_reason")),
            FString(TEXT("real_unreal_chaos_measurement_not_recorded"))
        );
        TestEqual(
            FString::Printf(TEXT("%s recorded_metric_count"), *FixtureId),
            static_cast<int32>(Job->GetIntegerField(TEXT("recorded_metric_count"))),
            0
        );
    }

    for (const FString& FixtureId : RequiredD6FixtureIds)
    {
        TestTrue(
            FString::Printf(TEXT("runner jobs contain %s"), *FixtureId),
            SeenFixtureIds.Contains(FixtureId)
        );
    }

    TestEqual(
        TEXT("sidecar schema"),
        SidecarRoot->GetStringField(TEXT("schema")),
        FString(TEXT("raftsim.flexible_raft.d6_chaos_measured_results_sidecar.v1"))
    );
    TestEqual(
        TEXT("sidecar status"),
        SidecarRoot->GetStringField(TEXT("status")),
        FString(TEXT("chaos_runner_output_pending_no_measurements_recorded"))
    );
    TestEqual(
        TEXT("sidecar filled_result_count"),
        static_cast<int32>(SidecarRoot->GetIntegerField(TEXT("filled_result_count"))),
        0
    );

    const TSharedPtr<FJsonObject>* Results = nullptr;
    if (!SidecarRoot->TryGetObjectField(TEXT("results"), Results) || Results == nullptr)
    {
        AddError(TEXT("D6 Chaos runner sidecar must contain results."));
        return false;
    }
    for (const FString& FixtureId : RequiredD6FixtureIds)
    {
        const TSharedPtr<FJsonObject>* Result = nullptr;
        if (!(*Results)->TryGetObjectField(FixtureId, Result) || Result == nullptr)
        {
            AddError(FString::Printf(TEXT("Missing D6 Chaos sidecar result: %s"), *FixtureId));
            return false;
        }
        TestEqual(
            FString::Printf(TEXT("%s sidecar result status"), *FixtureId),
            (*Result)->GetStringField(TEXT("status")),
            FString(TEXT("not_measured"))
        );
        TestEqual(
            FString::Printf(TEXT("%s source_report"), *FixtureId),
            (*Result)->GetStringField(TEXT("source_report")),
            FString()
        );
        TestEqual(
            FString::Printf(TEXT("%s telemetry_sha256"), *FixtureId),
            (*Result)->GetStringField(TEXT("telemetry_sha256")),
            FString()
        );
        TestEqual(
            FString::Printf(TEXT("%s engine_version"), *FixtureId),
            (*Result)->GetStringField(TEXT("engine_version")),
            FString()
        );
    }

    return true;
}

#define RAFTSIM_D6_CHAOS_FIXTURE_JOB_TEST(TestClass, TestPath, FixtureId) \
    IMPLEMENT_SIMPLE_AUTOMATION_TEST( \
        TestClass, \
        TestPath, \
        EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter \
    ) \
    bool TestClass::RunTest(const FString& Parameters) \
    { \
        return ValidateD6ChaosFixtureJob(*this, FString(TEXT(FixtureId)), FString(TEXT(TestPath))); \
    }

RAFTSIM_D6_CHAOS_FIXTURE_JOB_TEST(
    FRaftSimD6ChaosStaticSeatLoadSagTest,
    "RaftSim.D6.Chaos.StaticSeatLoadSag",
    "static_seat_load_sag"
)

RAFTSIM_D6_CHAOS_FIXTURE_JOB_TEST(
    FRaftSimD6ChaosTravelingCrewShiftTest,
    "RaftSim.D6.Chaos.TravelingCrewShift",
    "traveling_crew_shift"
)

RAFTSIM_D6_CHAOS_FIXTURE_JOB_TEST(
    FRaftSimD6ChaosRockPinchWrapTest,
    "RaftSim.D6.Chaos.RockPinchWrap",
    "rock_pinch_wrap"
)

RAFTSIM_D6_CHAOS_FIXTURE_JOB_TEST(
    FRaftSimD6ChaosUpstreamTubeOverwashFlipTest,
    "RaftSim.D6.Chaos.UpstreamTubeOverwashFlip",
    "upstream_tube_overwash_flip"
)

RAFTSIM_D6_CHAOS_FIXTURE_JOB_TEST(
    FRaftSimD6ChaosTimedHighSideSaveTest,
    "RaftSim.D6.Chaos.TimedHighSideSave",
    "timed_high_side_save"
)

RAFTSIM_D6_CHAOS_FIXTURE_JOB_TEST(
    FRaftSimD6ChaosPostContactRecoveryTest,
    "RaftSim.D6.Chaos.PostContactRecovery",
    "post_contact_recovery"
)

RAFTSIM_D6_CHAOS_FIXTURE_JOB_TEST(
    FRaftSimD6ChaosPressureFlowSweepsTest,
    "RaftSim.D6.Chaos.PressureFlowSweeps",
    "pressure_flow_sweeps"
)

#undef RAFTSIM_D6_CHAOS_FIXTURE_JOB_TEST

#endif
