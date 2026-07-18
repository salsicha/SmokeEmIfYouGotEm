// D6 measured-results export test (release-1.0-plan.md section 5 A-3 / P2):
// runs the seven committed D6 fixtures through the C++ D1-D4 flexible-raft
// port, writes the measured-results sidecars consumed by the physics-side
// flexible_raft_d6 comparison harness, and asserts numeric parity between the
// UE compliant pass and the committed Python reference metrics.

#if WITH_DEV_AUTOMATION_TESTS

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "RaftSimFlexibleRaftD6MeasuredExport.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FRaftSimD6UeMeasuredExportTest,
    "RaftSim.D6.UEMeasuredExport",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter
)

namespace
{

const TArray<FString> UeExportRequiredFixtureIds = {
    TEXT("static_seat_load_sag"),
    TEXT("traveling_crew_shift"),
    TEXT("rock_pinch_wrap"),
    TEXT("upstream_tube_overwash_flip"),
    TEXT("timed_high_side_save"),
    TEXT("post_contact_recovery"),
    TEXT("pressure_flow_sweeps"),
};

FString UeExportRepoRoot()
{
    return FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectDir(), TEXT("..")));
}

bool LoadJsonObjectFromFile(
    FAutomationTestBase& Test,
    const FString& FullPath,
    const FString& Label,
    TSharedPtr<FJsonObject>& OutRoot)
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

// Mirror of _flatten_numeric_metrics (flexible_raft_d6.py): numeric leaves
// keyed by dotted/indexed paths, booleans excluded.
void FlattenNumericMetrics(
    const TSharedPtr<FJsonValue>& Value,
    const FString& Prefix,
    TMap<FString, double>& OutFlattened)
{
    if (!Value.IsValid())
    {
        return;
    }
    switch (Value->Type)
    {
    case EJson::Object:
    {
        const TSharedPtr<FJsonObject> Object = Value->AsObject();
        TArray<TPair<FString, TSharedPtr<FJsonValue>>> SortedPairs;
        for (const auto& Pair : Object->Values)
        {
            SortedPairs.Emplace(FString(*Pair.Key), Pair.Value);
        }
        SortedPairs.Sort(
            [](const TPair<FString, TSharedPtr<FJsonValue>>& A,
               const TPair<FString, TSharedPtr<FJsonValue>>& B)
            {
                return A.Key < B.Key;
            });
        for (const TPair<FString, TSharedPtr<FJsonValue>>& Pair : SortedPairs)
        {
            const FString ChildPrefix = Prefix.IsEmpty() ? Pair.Key : Prefix + TEXT(".") + Pair.Key;
            FlattenNumericMetrics(Pair.Value, ChildPrefix, OutFlattened);
        }
        break;
    }
    case EJson::Array:
    {
        const TArray<TSharedPtr<FJsonValue>>& Items = Value->AsArray();
        for (int32 Index = 0; Index < Items.Num(); ++Index)
        {
            FlattenNumericMetrics(
                Items[Index], FString::Printf(TEXT("%s[%d]"), *Prefix, Index), OutFlattened);
        }
        break;
    }
    case EJson::Number:
        OutFlattened.Add(Prefix, Value->AsNumber());
        break;
    default:
        break;
    }
}

bool IsLower64Hex(const FString& Value)
{
    if (Value.Len() != 64)
    {
        return false;
    }
    for (const TCHAR Character : Value)
    {
        const bool bValid =
            (Character >= TEXT('0') && Character <= TEXT('9'))
            || (Character >= TEXT('a') && Character <= TEXT('f'));
        if (!bValid)
        {
            return false;
        }
    }
    return true;
}

} // namespace

bool FRaftSimD6UeMeasuredExportTest::RunTest(const FString& Parameters)
{
    const FString RepoRoot = UeExportRepoRoot();

    const FRaftSimD6MeasuredExportResult Export = RaftSimFlexD6::RunMeasuredExport(RepoRoot);
    if (!Export.bSuccess)
    {
        AddError(FString::Printf(TEXT("D6 UE measured export failed: %s"), *Export.ErrorMessage));
        return false;
    }
    TestEqual(TEXT("fixture count"), Export.FixtureCount, UeExportRequiredFixtureIds.Num());
    TestEqual(
        TEXT("compliant filled count"), Export.CompliantFilledCount, UeExportRequiredFixtureIds.Num());
    TestEqual(
        TEXT("baseline filled count"), Export.BaselineFilledCount, UeExportRequiredFixtureIds.Num());

    // Load the committed Python reference suite and both exported sidecars.
    TSharedPtr<FJsonObject> SuiteRoot;
    if (!LoadJsonObjectFromFile(
            *this,
            FPaths::Combine(
                RepoRoot, TEXT("physics/data/calibration/flexible_raft_d6_behavioral_suite.json")),
            TEXT("D6 behavioral suite"),
            SuiteRoot))
    {
        return false;
    }
    TSharedPtr<FJsonObject> CompliantSidecar;
    if (!LoadJsonObjectFromFile(
            *this, Export.CompliantSidecarPath, TEXT("UE compliant sidecar"), CompliantSidecar))
    {
        return false;
    }
    TSharedPtr<FJsonObject> BaselineSidecar;
    if (!LoadJsonObjectFromFile(
            *this, Export.ChaosBaselineSidecarPath, TEXT("UE chaos-baseline sidecar"), BaselineSidecar))
    {
        return false;
    }

    TestEqual(
        TEXT("compliant sidecar schema"),
        CompliantSidecar->GetStringField(TEXT("schema")),
        FString(TEXT("raftsim.flexible_raft.d6_compliant_measured_results_sidecar.v1")));
    TestEqual(
        TEXT("compliant sidecar target"),
        CompliantSidecar->GetStringField(TEXT("target_id")),
        FString(TEXT("project_chrono_or_reviewed_compliant_model")));
    TestEqual(
        TEXT("baseline sidecar schema"),
        BaselineSidecar->GetStringField(TEXT("schema")),
        FString(TEXT("raftsim.flexible_raft.d6_chaos_measured_results_sidecar.v1")));
    TestEqual(
        TEXT("baseline sidecar target"),
        BaselineSidecar->GetStringField(TEXT("target_id")),
        FString(TEXT("unreal_chaos_rigid_baseline")));

    const TSharedPtr<FJsonObject> CompliantResults = CompliantSidecar->GetObjectField(TEXT("results"));
    const TSharedPtr<FJsonObject> BaselineResults = BaselineSidecar->GetObjectField(TEXT("results"));
    if (!CompliantResults.IsValid() || !BaselineResults.IsValid())
    {
        AddError(TEXT("Exported sidecars must contain results objects."));
        return false;
    }

    const TArray<TSharedPtr<FJsonValue>>& SuiteFixtures = SuiteRoot->GetArrayField(TEXT("fixtures"));
    TestEqual(TEXT("suite fixture count"), SuiteFixtures.Num(), UeExportRequiredFixtureIds.Num());

    // D6 tolerance band (flexible_raft_d6.py): abs 1e-6 + rel 5%. The port is
    // asserted much tighter here to prove genuine numeric parity.
    constexpr double AbsoluteTolerance = 1.0e-6;
    constexpr double RelativeTolerance = 1.0e-9;

    for (const TSharedPtr<FJsonValue>& FixtureValue : SuiteFixtures)
    {
        const TSharedPtr<FJsonObject> Fixture = FixtureValue->AsObject();
        const FString FixtureId = Fixture->GetStringField(TEXT("fixture_id"));
        TestTrue(
            FString::Printf(TEXT("fixture id %s is expected"), *FixtureId),
            UeExportRequiredFixtureIds.Contains(FixtureId));

        const TSharedPtr<FJsonObject>* CompliantRecord = nullptr;
        if (!CompliantResults->TryGetObjectField(FixtureId, CompliantRecord) || CompliantRecord == nullptr)
        {
            AddError(FString::Printf(TEXT("Compliant sidecar missing fixture %s"), *FixtureId));
            return false;
        }
        const TSharedPtr<FJsonObject>* BaselineRecord = nullptr;
        if (!BaselineResults->TryGetObjectField(FixtureId, BaselineRecord) || BaselineRecord == nullptr)
        {
            AddError(FString::Printf(TEXT("Baseline sidecar missing fixture %s"), *FixtureId));
            return false;
        }

        for (const TSharedPtr<FJsonObject>* Record : {CompliantRecord, BaselineRecord})
        {
            TestEqual(
                FString::Printf(TEXT("%s record status"), *FixtureId),
                (*Record)->GetStringField(TEXT("status")),
                FString(TEXT("measured_engine_output")));
            TestTrue(
                FString::Printf(TEXT("%s telemetry_sha256 is 64-hex"), *FixtureId),
                IsLower64Hex((*Record)->GetStringField(TEXT("telemetry_sha256"))));
            TestFalse(
                FString::Printf(TEXT("%s engine_version recorded"), *FixtureId),
                (*Record)->GetStringField(TEXT("engine_version")).IsEmpty());
            TestFalse(
                FString::Printf(TEXT("%s source_report recorded"), *FixtureId),
                (*Record)->GetStringField(TEXT("source_report")).IsEmpty());
        }

        // Flatten reference and measured metric trees.
        TMap<FString, double> ReferenceMetrics;
        FlattenNumericMetrics(
            MakeShared<FJsonValueObject>(Fixture->GetObjectField(TEXT("python_reference_metrics"))),
            FString(),
            ReferenceMetrics);
        TMap<FString, double> CompliantMetrics;
        FlattenNumericMetrics(
            MakeShared<FJsonValueObject>((*CompliantRecord)->GetObjectField(TEXT("metrics"))),
            FString(),
            CompliantMetrics);
        TMap<FString, double> BaselineMetrics;
        FlattenNumericMetrics(
            MakeShared<FJsonValueObject>((*BaselineRecord)->GetObjectField(TEXT("metrics"))),
            FString(),
            BaselineMetrics);

        TestTrue(
            FString::Printf(TEXT("%s reference metric count > 0"), *FixtureId),
            ReferenceMetrics.Num() > 0);

        for (const TPair<FString, double>& Reference : ReferenceMetrics)
        {
            // Baseline target: every required metric path must be recorded
            // (deltas are recorded, not failed).
            if (!BaselineMetrics.Contains(Reference.Key))
            {
                AddError(FString::Printf(
                    TEXT("%s baseline metrics missing path %s"), *FixtureId, *Reference.Key));
                continue;
            }

            // Compliant target: bounded numeric equivalence with the Python
            // reference, asserted tightly.
            const double* Measured = CompliantMetrics.Find(Reference.Key);
            if (Measured == nullptr)
            {
                AddError(FString::Printf(
                    TEXT("%s compliant metrics missing path %s"), *FixtureId, *Reference.Key));
                continue;
            }
            const double AbsDelta = FMath::Abs(*Measured - Reference.Value);
            const double Tolerance =
                AbsoluteTolerance
                + RelativeTolerance * FMath::Max(FMath::Abs(Reference.Value), FMath::Abs(*Measured));
            TestTrue(
                FString::Printf(
                    TEXT("%s %s within tolerance (reference=%.17g measured=%.17g delta=%.3g)"),
                    *FixtureId,
                    *Reference.Key,
                    Reference.Value,
                    *Measured,
                    AbsDelta),
                AbsDelta <= Tolerance);
        }
    }

    return true;
}

#endif
