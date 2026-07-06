#if WITH_DEV_AUTOMATION_TESTS

#include "Dom/JsonObject.h"
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace
{
TSharedPtr<FJsonObject> LoadMilestone25Json(FAutomationTestBase& Test, const FString& FullPath)
{
    FString JsonText;
    if (!FFileHelper::LoadFileToString(JsonText, *FullPath))
    {
        Test.AddError(FString::Printf(TEXT("Missing Milestone 25 JSON: %s"), *FullPath));
        return nullptr;
    }

    TSharedPtr<FJsonObject> Root;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonText);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        Test.AddError(FString::Printf(TEXT("Invalid Milestone 25 JSON: %s"), *FullPath));
        return nullptr;
    }

    return Root;
}

TSharedPtr<FJsonObject> LoadMilestone25ContentJson(FAutomationTestBase& Test, const FString& ContentRelativePath)
{
    return LoadMilestone25Json(
        Test,
        FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectContentDir(), ContentRelativePath))
    );
}

bool TestMilestone25ArrayCount(
    FAutomationTestBase& Test,
    const TSharedPtr<FJsonObject>& Root,
    const TCHAR* FieldName,
    int32 ExpectedCount
)
{
    const TArray<TSharedPtr<FJsonValue>>* Values = nullptr;
    if (!Root->TryGetArrayField(FieldName, Values) || Values == nullptr)
    {
        Test.AddError(FString::Printf(TEXT("Missing Milestone 25 array field: %s"), FieldName));
        return false;
    }

    Test.TestEqual(FString::Printf(TEXT("%s count"), FieldName), Values->Num(), ExpectedCount);
    return Values->Num() == ExpectedCount;
}

bool TestMilestone25AllGateChecksPassed(
    FAutomationTestBase& Test,
    const TSharedPtr<FJsonObject>& Gate,
    int32 ExpectedCount
)
{
    const TArray<TSharedPtr<FJsonValue>>* GateChecks = nullptr;
    if (!Gate->TryGetArrayField(TEXT("gate_checks"), GateChecks) || GateChecks == nullptr)
    {
        Test.AddError(TEXT("Milestone 25 gate must declare gate_checks."));
        return false;
    }

    Test.TestEqual(TEXT("gate check count"), GateChecks->Num(), ExpectedCount);
    for (const TSharedPtr<FJsonValue>& CheckValue : *GateChecks)
    {
        const TSharedPtr<FJsonObject> Check = CheckValue->AsObject();
        if (!Check.IsValid())
        {
            Test.AddError(TEXT("Every Milestone 25 gate check must be an object."));
            return false;
        }

        Test.TestTrue(Check->GetStringField(TEXT("check_id")), Check->GetBoolField(TEXT("passed")));

        const TArray<TSharedPtr<FJsonValue>>* Evidence = nullptr;
        if (!Check->TryGetArrayField(TEXT("evidence"), Evidence) || Evidence == nullptr || Evidence->Num() == 0)
        {
            Test.AddError(FString::Printf(TEXT("Gate check has no evidence: %s"), *Check->GetStringField(TEXT("check_id"))));
            return false;
        }
    }

    return true;
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimMilestone25ReleaseReadinessGateTest,
    "RaftSim.Milestone25.ReleaseReadinessGate",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter
)

bool FRaftSimMilestone25ReleaseReadinessGateTest::RunTest(const FString& Parameters)
{
    const TSharedPtr<FJsonObject> Gate = LoadMilestone25ContentJson(
        *this,
        TEXT("RaftSim/Automation/release_readiness_gate.json")
    );
    if (!Gate.IsValid())
    {
        return false;
    }

    TestEqual(
        TEXT("gate schema"),
        Gate->GetStringField(TEXT("schema")),
        FString(TEXT("raftsim.unreal.release_readiness_gate.v1"))
    );
    TestEqual(
        TEXT("automation module"),
        Gate->GetStringField(TEXT("automation_module")),
        FString(TEXT("RaftSimAutomation"))
    );
    TestEqual(
        TEXT("automation test name"),
        Gate->GetStringField(TEXT("automation_test_name")),
        FString(TEXT("RaftSim.Milestone25.ReleaseReadinessGate"))
    );
    TestEqual(TEXT("milestone25 todo count"), Gate->GetIntegerField(TEXT("milestone25_todo_count")), 7);
    TestMilestone25AllGateChecksPassed(*this, Gate, 7);
    TestMilestone25ArrayCount(*this, Gate, TEXT("external_signoff_required_before_shipping"), 7);
    TestMilestone25ArrayCount(*this, Gate, TEXT("automation_commands"), 2);

    const TSharedPtr<FJsonObject>* RequiredManifests = nullptr;
    if (!Gate->TryGetObjectField(TEXT("required_manifests"), RequiredManifests)
        || RequiredManifests == nullptr
        || !RequiredManifests->IsValid())
    {
        AddError(TEXT("Milestone 25 gate must declare required_manifests."));
        return false;
    }

    const TSharedPtr<FJsonObject> Plan = LoadMilestone25ContentJson(
        *this,
        (*RequiredManifests)->GetStringField(TEXT("release_readiness_plan"))
    );
    if (!Plan.IsValid())
    {
        return false;
    }

    TestEqual(
        TEXT("plan schema"),
        Plan->GetStringField(TEXT("schema")),
        FString(TEXT("raftsim.unreal.release_readiness_plan.v1"))
    );
    TestEqual(TEXT("plan milestone"), Plan->GetIntegerField(TEXT("milestone")), 25);
    TestMilestone25ArrayCount(*this, Plan, TEXT("target_platform_tiers"), 3);
    TestMilestone25ArrayCount(*this, Plan, TEXT("profiling_optimization_matrix"), 11);
    TestMilestone25ArrayCount(*this, Plan, TEXT("scalability_modes"), 5);
    TestMilestone25ArrayCount(*this, Plan, TEXT("release_workflows"), 8);
    TestMilestone25ArrayCount(*this, Plan, TEXT("qa_automation_lanes"), 10);
    TestMilestone25ArrayCount(*this, Plan, TEXT("polish_lanes"), 11);
    TestMilestone25ArrayCount(*this, Plan, TEXT("release_or_defer_decisions"), 6);
    TestMilestone25ArrayCount(*this, Plan, TEXT("release_gate_requirements"), 7);

    const TSharedPtr<FJsonObject> PassPolicy = Plan->GetObjectField(TEXT("pass_policy"));
    TestTrue(TEXT("profiles systems"), PassPolicy->GetBoolField(TEXT("profiles_all_milestone25_systems")));
    TestTrue(TEXT("defines scalability"), PassPolicy->GetBoolField(TEXT("defines_desktop_vr_and_handheld_scalability")));
    TestTrue(TEXT("locks workflows"), PassPolicy->GetBoolField(TEXT("locks_release_asset_audio_ai_source_and_compliance_workflows")));
    TestTrue(TEXT("hardens QA"), PassPolicy->GetBoolField(TEXT("hardens_qa_automation_lanes")));
    TestTrue(TEXT("covers polish"), PassPolicy->GetBoolField(TEXT("covers_player_polish_lanes")));
    TestTrue(TEXT("records decisions"), PassPolicy->GetBoolField(TEXT("records_release_or_defer_decisions")));
    TestTrue(TEXT("gates external signoff"), PassPolicy->GetBoolField(TEXT("gates_release_on_external_signoff_evidence")));

    const FString ReportPath = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(FPaths::ProjectDir(), TEXT("../physics/reports/milestone25/release_readiness_gate.json"))
    );
    const TSharedPtr<FJsonObject> Report = LoadMilestone25Json(*this, ReportPath);
    if (!Report.IsValid())
    {
        return false;
    }

    TestEqual(
        TEXT("report schema"),
        Report->GetStringField(TEXT("schema")),
        FString(TEXT("raftsim.report.milestone25.release_readiness_gate.v1"))
    );
    TestMilestone25ArrayCount(*this, Report, TEXT("gate_results"), 7);
    TestMilestone25ArrayCount(*this, Report, TEXT("shipping_blockers"), 7);

    const TSharedPtr<FJsonObject> GatePassPolicy = Gate->GetObjectField(TEXT("pass_policy"));
    TestTrue(TEXT("all milestone items covered"), GatePassPolicy->GetBoolField(TEXT("all_seven_milestone25_items_covered")));
    TestTrue(TEXT("external signoff still blocks shipping"), GatePassPolicy->GetBoolField(TEXT("external_signoff_still_blocks_shipping")));

    return true;
}

#endif
