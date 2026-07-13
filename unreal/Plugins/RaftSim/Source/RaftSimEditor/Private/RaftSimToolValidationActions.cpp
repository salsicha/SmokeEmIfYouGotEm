#include "RaftSimToolValidationActions.h"

#include "Editor.h"
#include "HAL/PlatformFileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "UObject/Package.h"

namespace
{
FText MakeActionText(const TCHAR* Text)
{
    return FText::FromString(FString(Text));
}

FString BoolString(bool bValue)
{
    return bValue ? TEXT("true") : TEXT("false");
}

FString EscapeJson(const FString& Value)
{
    FString Escaped = Value.Replace(TEXT("\\"), TEXT("\\\\"));
    Escaped = Escaped.Replace(TEXT("\""), TEXT("\\\""));
    Escaped = Escaped.Replace(TEXT("\n"), TEXT("\\n"));
    return Escaped;
}

bool WriteActionRecord(const FRaftSimToolValidationAction& Action, const FString& Status, const FString& Summary, FString& OutRecordPath)
{
    const FString OutputRoot = FPaths::ConvertRelativePathToFull(
        FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("RaftSim/ToolValidation")));
    IFileManager::Get().MakeDirectory(*OutputRoot, true);
    OutRecordPath = FPaths::Combine(OutputRoot, Action.ActionId.ToString() + TEXT(".json"));

    FString EvidenceJson;
    for (int32 Index = 0; Index < Action.RequiredEvidence.Num(); ++Index)
    {
        EvidenceJson += FString::Printf(
            TEXT("%s\"%s\""),
            Index == 0 ? TEXT("") : TEXT(", "),
            *EscapeJson(Action.RequiredEvidence[Index]));
    }

    const FString Record = FString::Printf(
        TEXT("{\n")
        TEXT("  \"action_id\": \"%s\",\n")
        TEXT("  \"tool_id\": \"%s\",\n")
        TEXT("  \"status\": \"%s\",\n")
        TEXT("  \"summary\": \"%s\",\n")
        TEXT("  \"source_manifest\": \"%s\",\n")
        TEXT("  \"report_path\": \"%s\",\n")
        TEXT("  \"requires_editor_automation\": %s,\n")
        TEXT("  \"blocks_promotion\": %s,\n")
        TEXT("  \"required_evidence\": [%s]\n")
        TEXT("}\n"),
        *EscapeJson(Action.ActionId.ToString()),
        *EscapeJson(Action.ToolId.ToString()),
        *EscapeJson(Status),
        *EscapeJson(Summary),
        *EscapeJson(Action.SourceManifest),
        *EscapeJson(Action.ReportPath),
        *BoolString(Action.bRequiresEditorAutomation),
        *BoolString(Action.bBlocksPromotion),
        *EvidenceJson);

    return FFileHelper::SaveStringToFile(Record, *OutRecordPath);
}

bool ValidateRequiredEvidence(const FRaftSimToolValidationAction& Action, FString& OutMissing)
{
    TArray<FString> Missing;

    for (const FString& Evidence : Action.RequiredEvidence)
    {
        const FString Resolved = RaftSimEditorValidation::ResolveWorkspacePath(Evidence);
        if (!FPaths::FileExists(Resolved) && !FPaths::DirectoryExists(Resolved))
        {
            Missing.Add(Evidence);
        }
    }

    if (!Action.SourceManifest.IsEmpty())
    {
        const FString Resolved = RaftSimEditorValidation::ResolveWorkspacePath(Action.SourceManifest);
        if (!FPaths::FileExists(Resolved) && !FPaths::DirectoryExists(Resolved))
        {
            Missing.Add(Action.SourceManifest);
        }
    }

    if (!Missing.IsEmpty())
    {
        OutMissing = FString::Join(Missing, TEXT(", "));
        return false;
    }

    return true;
}
} // namespace

void URaftSimToolValidationActionRunner::Configure(URaftSimToolValidationActionRegistry* InRegistry)
{
    Registry = InRegistry;
}

FRaftSimToolValidationActionResult URaftSimToolValidationActionRunner::RunAction(FName ActionId)
{
    FRaftSimToolValidationActionResult Result;
    Result.ActionId = ActionId;

    const FRaftSimToolValidationAction* Action = FindAction(ActionId);
    if (!Action)
    {
        Result.Message.MessageId = TEXT("unknown_validation_action");
        Result.Message.Severity = ERaftSimToolValidationSeverity::Blocking;
        Result.Message.Summary = NSLOCTEXT(
            "RaftSimToolValidationActions",
            "UnknownAction",
            "Validation action is not registered.");
        Result.Message.bBlocksExport = true;
        return Result;
    }

    return RaftSimEditorValidation::ExecuteAction(*Action);
}

bool URaftSimToolValidationActionRunner::CanRunAction(FName ActionId) const
{
    const FRaftSimToolValidationAction* Action = FindAction(ActionId);
    return Action && (!Action->SourceManifest.IsEmpty() || !Action->ReportPath.IsEmpty());
}

const FRaftSimToolValidationAction* URaftSimToolValidationActionRunner::FindAction(FName ActionId) const
{
    if (!Registry)
    {
        return nullptr;
    }

    return Registry->Actions.FindByPredicate(
        [ActionId](const FRaftSimToolValidationAction& Action)
        {
            return Action.ActionId == ActionId;
        });
}

namespace RaftSimEditorValidation
{
TArray<FRaftSimToolValidationAction> BuildDefaultValidationActions()
{
    TArray<FRaftSimToolValidationAction> Actions;

    auto AddAction = [&Actions](
                         FName ActionId,
                         FName ToolId,
                         ERaftSimToolValidationActionKind Kind,
                         const TCHAR* DisplayName,
                         const TCHAR* SourceManifest,
                         const TCHAR* ReportPath,
                         const TCHAR* CommandPreview,
                         TArray<FString> RequiredEvidence,
                         bool bRequiresEditorAutomation,
                         bool bBlocksPromotion)
    {
        FRaftSimToolValidationAction Action;
        Action.ActionId = ActionId;
        Action.ToolId = ToolId;
        Action.ActionKind = Kind;
        Action.DisplayName = MakeActionText(DisplayName);
        Action.SourceManifest = SourceManifest;
        Action.ReportPath = ReportPath;
        Action.CommandPreview = CommandPreview;
        Action.RequiredEvidence = MoveTemp(RequiredEvidence);
        Action.bRequiresEditorAutomation = bRequiresEditorAutomation;
        Action.bBlocksPromotion = bBlocksPromotion;
        Actions.Add(MoveTemp(Action));
    };

    AddAction(
        TEXT("source_checks"),
        TEXT("GeospatialValidator"),
        ERaftSimToolValidationActionKind::SourceCheck,
        TEXT("Validate Source"),
        TEXT("unreal/Content/RaftSim/River/geospatial_import_pipeline.json"),
        TEXT("physics/reports/milestone24/alpha_expansion_gate.json"),
        TEXT("Validate JSON source manifests, CRS metadata, rights/provenance, and source catalog links."),
        {TEXT("physics/data/real_world/source_catalog.json"), TEXT("unreal/Content/RaftSim/River/geospatial_import_pipeline.json")},
        false,
        true);

    AddAction(
        TEXT("deterministic_export"),
        TEXT("RapidRiverEditor"),
        ERaftSimToolValidationActionKind::DeterministicExport,
        TEXT("Export Deterministically"),
        TEXT("unreal/Content/RaftSim/Tools/rapid_river_editor_shell.json"),
        TEXT("unreal/Content/RaftSim/River/round_trip_validation.json"),
        TEXT("Export JSON/GeoJSON editor artifacts with stable ordering and manifest-recorded provenance."),
        {
            TEXT("unreal/Content/RaftSim/River/rapid_river_editor.json"),
            TEXT("unreal/Content/RaftSim/River/traceable_river_data_assets.json"),
            TEXT("unreal/Content/RaftSim/River/named_rapid_editor_markers.json"),
            TEXT("unreal/Content/RaftSim/River/named_rapid_editor_geometry.geojson"),
            TEXT("unreal/Content/RaftSim/Automation/named_rapid_simulator_review_runs.json")},
        false,
        true);

    AddAction(
        TEXT("regenerate_solver_package"),
        TEXT("RapidRiverEditor"),
        ERaftSimToolValidationActionKind::SolverPackageRegeneration,
        TEXT("Regenerate Solver Package"),
        TEXT("unreal/Content/RaftSim/River/round_trip_validation.json"),
        TEXT("physics/reports/milestone20/report_set_lock.json"),
        TEXT("Regenerate solver-facing arrays and comparison inputs from exported river editor data."),
        {
            TEXT("unreal/Content/RaftSim/River/round_trip_validation.json"),
            TEXT("unreal/Content/RaftSim/Automation/named_rapid_simulator_review_runs.json"),
            TEXT("physics/reports/milestone16/full_cpp_validation_gate.json")},
        true,
        true);

    AddAction(
        TEXT("stitched_window_validation"),
        TEXT("GeospatialValidator"),
        ERaftSimToolValidationActionKind::StitchedWindowValidation,
        TEXT("Validate Stitched Window"),
        TEXT("unreal/Content/RaftSim/River/reach_local_streaming.json"),
        TEXT("unreal/Content/RaftSim/River/round_trip_validation.json"),
        TEXT("Confirm reach-local authoring windows export stitched whole-window fields and conservation summaries."),
        {TEXT("unreal/Content/RaftSim/River/reach_local_streaming.json"), TEXT("unreal/Content/RaftSim/River/round_trip_validation.json")},
        false,
        true);

    AddAction(
        TEXT("live_water_smoke"),
        TEXT("ReplayDebugViewer"),
        ERaftSimToolValidationActionKind::LiveWaterSmoke,
        TEXT("Run Live-Water Smoke"),
        TEXT("unreal/Content/RaftSim/Automation/live_water_smoke_suite.json"),
        TEXT("physics/reports/milestone20/live_water_unreal_smoke_suite.json"),
        TEXT("Automation RunTests RaftSim.Milestone20.LiveWaterSmokeSuite"),
        {TEXT("unreal/Content/RaftSim/Automation/live_water_smoke_suite.json"), TEXT("physics/reports/milestone20/report_set_lock.json")},
        true,
        true);

    AddAction(
        TEXT("round_trip_validation"),
        TEXT("RapidRiverEditor"),
        ERaftSimToolValidationActionKind::RoundTripValidation,
        TEXT("Run Round Trip"),
        TEXT("unreal/Content/RaftSim/River/round_trip_validation.json"),
        TEXT("unreal/Content/RaftSim/River/round_trip_validation.json"),
        TEXT("Validate that Unreal exports can regenerate solver packages, GeoClaw/C++ inputs, and fidelity overlays."),
        {TEXT("unreal/Content/RaftSim/River/round_trip_validation.json"), TEXT("unreal/Content/RaftSim/River/south_fork_first_river_editor_pass.json")},
        false,
        true);

    AddAction(
        TEXT("open_latest_report"),
        TEXT("VerticalSliceLauncher"),
        ERaftSimToolValidationActionKind::OpenReport,
        TEXT("Open Latest Report"),
        TEXT("unreal/Content/RaftSim/Automation/vertical_slice_acceptance_gate.json"),
        TEXT("physics/reports/milestone23/vertical_slice_acceptance_gate.json"),
        TEXT("Open the latest linked validation or acceptance report for reviewer inspection."),
        {TEXT("physics/reports/milestone23/vertical_slice_acceptance_gate.json"), TEXT("physics/reports/milestone24/alpha_expansion_gate.json")},
        false,
        false);

    return Actions;
}

const FRaftSimToolValidationAction* FindDefaultValidationAction(FName ActionId)
{
    static TArray<FRaftSimToolValidationAction> Actions = BuildDefaultValidationActions();
    return Actions.FindByPredicate(
        [ActionId](const FRaftSimToolValidationAction& Action)
        {
            return Action.ActionId == ActionId;
        });
}

FString ResolveWorkspacePath(const FString& SourcePath)
{
    if (FPaths::IsRelative(SourcePath))
    {
        const FString ProjectDir = FPaths::ConvertRelativePathToFull(FPaths::ProjectDir());
        const FString RepoRoot = FPaths::ConvertRelativePathToFull(FPaths::Combine(ProjectDir, TEXT("..")));

        if (SourcePath.StartsWith(TEXT("unreal/")) || SourcePath.StartsWith(TEXT("physics/")) ||
            SourcePath.StartsWith(TEXT("docs/")) || SourcePath == TEXT("TODO.md"))
        {
            return FPaths::ConvertRelativePathToFull(FPaths::Combine(RepoRoot, SourcePath));
        }

        return FPaths::ConvertRelativePathToFull(FPaths::Combine(ProjectDir, SourcePath));
    }

    return FPaths::ConvertRelativePathToFull(SourcePath);
}

FRaftSimToolValidationActionResult ExecuteAction(const FRaftSimToolValidationAction& Action)
{
    FRaftSimToolValidationActionResult Result;
    Result.ActionId = Action.ActionId;
    Result.Message.MessageId = Action.ActionId;
    Result.Message.SourcePath = !Action.ReportPath.IsEmpty() ? Action.ReportPath : Action.SourceManifest;

    FString MissingEvidence;
    if (!ValidateRequiredEvidence(Action, MissingEvidence))
    {
        Result.Message.Severity = ERaftSimToolValidationSeverity::Blocking;
        Result.Message.Summary = FText::Format(
            NSLOCTEXT(
                "RaftSimToolValidationActions",
                "MissingEvidence",
                "{0} cannot run because required evidence is missing: {1}"),
            Action.DisplayName,
            FText::FromString(MissingEvidence));
        Result.Message.bBlocksExport = true;
        return Result;
    }

    FString Summary = FString::Printf(TEXT("%s executed; evidence files are present."), *Action.DisplayName.ToString());

    if (Action.ActionKind == ERaftSimToolValidationActionKind::OpenReport && !Action.ReportPath.IsEmpty())
    {
        const FString ResolvedReport = ResolveWorkspacePath(Action.ReportPath);
        FPlatformProcess::LaunchFileInDefaultExternalApplication(*ResolvedReport);
        Summary = FString::Printf(TEXT("%s opened report: %s"), *Action.DisplayName.ToString(), *Action.ReportPath);
    }
    else if (Action.ActionKind == ERaftSimToolValidationActionKind::LiveWaterSmoke && GEditor)
    {
        const TCHAR* Command = TEXT("Automation RunTests RaftSim.Milestone20.LiveWaterSmokeSuite");
        GEditor->Exec(nullptr, Command);
        Summary = FString::Printf(TEXT("%s dispatched Unreal automation command: %s"), *Action.DisplayName.ToString(), Command);
    }

    FString RecordPath;
    WriteActionRecord(Action, TEXT("executed"), Summary, RecordPath);

    Result.bAccepted = true;
    Result.Message.Severity = Action.bBlocksPromotion ? ERaftSimToolValidationSeverity::Warning : ERaftSimToolValidationSeverity::Info;
    Result.Message.Summary = FText::FromString(Summary);
    Result.Message.bBlocksExport = false;
    return Result;
}
} // namespace RaftSimEditorValidation
