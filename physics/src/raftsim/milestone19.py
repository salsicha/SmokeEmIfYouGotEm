"""Milestone 19 Chaos/Jolt runtime evaluation artifacts."""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CHAOS_AUTOMATION_MANIFEST_SCHEMA = "raftsim.unreal.chaos_automation_fixtures.v1"
CHAOS_REPLAY_SUMMARY_SCHEMA = "raftsim.unreal.chaos_fixture_replay_summary.v1"
CHAOS_SUMMARY_SCHEMA = "raftsim.unreal.chaos_fixture_summary.v1"
CHAOS_RUNTIME_ID = "UnrealChaos"
CHAOS_EXPORT_DECISION = "automation_fixture_export_complete_not_authority_evidence"
JOLT_SMOKE_HARNESS_MANIFEST_SCHEMA = "raftsim.native.jolt_smoke_harness.v1"
JOLT_REPLAY_SUMMARY_SCHEMA = "raftsim.native.jolt_fixture_replay_summary.v1"
JOLT_SUMMARY_SCHEMA = "raftsim.native.jolt_fixture_summary.v1"
JOLT_RUNTIME_ID = "Jolt"
JOLT_EXPORT_DECISION = "native_jolt_smoke_harness_export_complete_not_authority_evidence"
CHAOS_JOLT_COMPARISON_SCHEMA = "raftsim.runtime_eval.chaos_vs_jolt_comparison.v1"
CHAOS_JOLT_COMPARISON_DECISION = "blocked_pending_measured_runtime_telemetry"
AUTHORITY_SELECTION_SCHEMA = "raftsim.runtime_eval.authority_selection.v1"
AUTHORITY_SELECTION_DECISION = "custom_reduced_runtime_fallback_selected_for_vertical_slice"
FALLBACK_RUNTIME_ID = "CustomReducedRigidBody"
COMPARISON_DIMENSIONS = (
    "determinism",
    "cpu_cost",
    "contact_quality",
    "outcome_stability",
    "swimmer_state",
    "authoring_debug_ergonomics",
)


@dataclass(frozen=True, slots=True)
class ChaosAutomationExport:
    manifest: dict[str, Any]
    summary: dict[str, Any]
    replays: tuple[dict[str, Any], ...]
    markdown: str


@dataclass(frozen=True, slots=True)
class JoltSmokeHarnessExport:
    manifest: dict[str, Any]
    summary: dict[str, Any]
    replays: tuple[dict[str, Any], ...]
    markdown: str


@dataclass(frozen=True, slots=True)
class ChaosJoltComparisonReport:
    report: dict[str, Any]
    markdown: str


@dataclass(frozen=True, slots=True)
class RuntimeAuthoritySelectionReport:
    report: dict[str, Any]
    markdown: str


def load_runtime_evaluation_contract(path: Path) -> dict[str, Any]:
    """Load the shared Chaos/Jolt runtime evaluation contract."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "raftsim.unreal.chaos_jolt_runtime_evaluation.v1":
        raise ValueError(f"unsupported contract schema: {payload.get('schema')!r}")
    return payload


def build_chaos_automation_export(
    contract: dict[str, Any],
    *,
    source_contract_path: str = "unreal/Content/RaftSim/Physics/chaos_jolt_runtime_evaluation.json",
    manifest_output_path: str = "unreal/Content/RaftSim/Physics/chaos_automation_fixtures.json",
    summary_output_path: str = "physics/reports/milestone19/chaos/summary.json",
    replay_output_dir: str = "physics/reports/milestone19/chaos/replays",
) -> ChaosAutomationExport:
    """Build the Unreal Chaos fixture manifest plus replay/summary artifacts.

    The generated files are automation inputs and export schemas. They are not
    runtime pass evidence until Unreal executes the fixtures and replaces the
    schema placeholder frames with measured Chaos telemetry.
    """

    shared = contract["shared_fixture_contract"]
    fixed_step_seconds = float(shared["fixed_step_seconds"])
    duration_seconds = float(shared["duration_seconds"])
    required_fields = tuple(shared["telemetry_required"])
    fixtures = tuple(
        fixture for fixture in contract["fixtures"] if CHAOS_RUNTIME_ID in fixture["applies_to"]
    )
    if not fixtures:
        raise ValueError("contract has no UnrealChaos fixtures")

    manifest_fixtures: list[dict[str, Any]] = []
    replay_summaries: list[dict[str, Any]] = []
    summary_fixtures: list[dict[str, Any]] = []

    for index, fixture in enumerate(fixtures):
        fixture_id = fixture["fixture_id"]
        variants = _expand_parameter_sweep(fixture.get("parameter_sweep", {}))
        step_count = _fixture_step_count(fixture, fixed_step_seconds, duration_seconds)
        sample_steps = _sample_steps(step_count)
        replay_path = f"{replay_output_dir}/{fixture_id}.replay_summary.json"
        automation_test_name = (
            f"Project.RaftSim.Milestone19.Chaos.{_automation_name_suffix(fixture_id)}"
        )

        manifest_entry = {
            "fixture_id": fixture_id,
            "title": fixture["title"],
            "automation_test_name": automation_test_name,
            "unreal_target": {
                "runtime": CHAOS_RUNTIME_ID,
                "test_type": "EditorContext | EngineFilter",
                "fixture_map": f"/RaftSim/Physics/RuntimeEval/Chaos/{fixture_id}",
                "functional_test_actor": "BP_RaftSimChaosRuntimeFixture",
                "debug_overlay_capture": (
                    f"Saved/Automation/RaftSim/Chaos/{fixture_id}_overlay.png"
                ),
            },
            "source_contract": source_contract_path,
            "fixed_step_seconds": fixed_step_seconds,
            "duration_seconds": round(step_count * fixed_step_seconds, 6),
            "step_count": step_count,
            "parameter_case_count": len(variants),
            "parameter_cases": variants,
            "setup": fixture["setup"],
            "metrics": fixture["metrics"],
            "pass_gates": fixture["pass_gates"],
            "telemetry_required": list(required_fields),
            "exports": {
                "summary": summary_output_path,
                "replay_summary": replay_path,
                "full_telemetry_stream": (
                    f"Saved/Automation/RaftSim/Chaos/{fixture_id}.telemetry.jsonl"
                ),
            },
            "status": "ready_for_unreal_automation_execution",
            "authoritative_evidence": False,
        }
        manifest_fixtures.append(manifest_entry)

        replay = _build_replay_summary(
            fixture=fixture,
            fixture_index=index,
            variants=variants,
            required_fields=required_fields,
            fixed_step_seconds=fixed_step_seconds,
            step_count=step_count,
            sample_steps=sample_steps,
            source_contract_path=source_contract_path,
            runtime_id=CHAOS_RUNTIME_ID,
            replay_schema=CHAOS_REPLAY_SUMMARY_SCHEMA,
            status="schema_placeholder_ready_for_unreal_automation_execution",
            telemetry_stream_dir="Saved/Automation/RaftSim/Chaos",
        )
        replay_summaries.append(replay)

        summary_fixtures.append(
            {
                "fixture_id": fixture_id,
                "automation_test_name": automation_test_name,
                "parameter_case_count": len(variants),
                "step_count": step_count,
                "replay_summary": replay_path,
                "telemetry_fields_present_in_schema_samples": _sample_has_required_fields(
                    replay, required_fields
                ),
                "pass_gate_count": len(fixture["pass_gates"]),
                "metrics": fixture["metrics"],
                "status": "ready_for_unreal_automation_execution",
                "authoritative_evidence": False,
            }
        )

    total_parameter_cases = sum(item["parameter_case_count"] for item in summary_fixtures)
    manifest = {
        "schema": CHAOS_AUTOMATION_MANIFEST_SCHEMA,
        "source_contract": source_contract_path,
        "target_runtime": CHAOS_RUNTIME_ID,
        "decision": CHAOS_EXPORT_DECISION,
        "summary": (
            "Unreal Chaos automation fixtures generated from the shared Chaos/Jolt "
            "runtime evaluation contract. These fixtures export schema-compatible "
            "telemetry/replay summaries but do not select Chaos as authoritative."
        ),
        "fixed_step_seconds": fixed_step_seconds,
        "water_source": shared["water_source"],
        "telemetry_required": list(required_fields),
        "global_pass_gates": shared["global_pass_gates"],
        "automation_export": {
            "summary": summary_output_path,
            "replay_dir": replay_output_dir,
            "manifest": manifest_output_path,
        },
        "fixtures": manifest_fixtures,
    }

    summary = {
        "schema": CHAOS_SUMMARY_SCHEMA,
        "source_contract": source_contract_path,
        "automation_manifest": manifest_output_path,
        "runtime_id": CHAOS_RUNTIME_ID,
        "decision": CHAOS_EXPORT_DECISION,
        "fixture_count": len(fixtures),
        "expanded_parameter_case_count": total_parameter_cases,
        "replay_summary_count": len(replay_summaries),
        "telemetry_required": list(required_fields),
        "all_fixture_samples_match_required_telemetry": all(
            item["telemetry_fields_present_in_schema_samples"] for item in summary_fixtures
        ),
        "authority_selection_allowed": False,
        "runtime_passed_fixture_suite": False,
        "status": "ready_for_unreal_automation_execution",
        "fixtures": summary_fixtures,
        "notes": [
            "This artifact completes the Chaos automation fixture export, not the Chaos authority decision.",
            "Unreal must execute the generated fixture map/tests and replace schema placeholder telemetry before Chaos can be ranked against Jolt.",
            "The custom C++ water solver remains authoritative water; Chaos consumes water snapshots and may not mutate water state.",
        ],
    }
    markdown = _summary_markdown(summary)
    return ChaosAutomationExport(
        manifest=manifest,
        summary=summary,
        replays=tuple(replay_summaries),
        markdown=markdown,
    )


def build_jolt_smoke_harness_export(
    contract: dict[str, Any],
    *,
    source_contract_path: str = "unreal/Content/RaftSim/Physics/chaos_jolt_runtime_evaluation.json",
    manifest_output_path: str = "physics/cpp/tests/jolt_smoke_harness_manifest.json",
    summary_output_path: str = "physics/reports/milestone19/jolt/summary.json",
    replay_output_dir: str = "physics/reports/milestone19/jolt/replays",
) -> JoltSmokeHarnessExport:
    """Build the native Jolt smoke-harness manifest and report artifacts.

    The harness path is source-controlled and buildable without vendoring the
    Jolt SDK. It validates that the native executable can consume the shared
    fixture contract and emit schema-compatible placeholder summaries; real
    Jolt authority evidence still requires linking/running the Jolt SDK path.
    """

    shared = contract["shared_fixture_contract"]
    fixed_step_seconds = float(shared["fixed_step_seconds"])
    duration_seconds = float(shared["duration_seconds"])
    required_fields = tuple(shared["telemetry_required"])
    fixtures = tuple(
        fixture for fixture in contract["fixtures"] if JOLT_RUNTIME_ID in fixture["applies_to"]
    )
    if not fixtures:
        raise ValueError("contract has no Jolt fixtures")

    harness_fixtures: list[dict[str, Any]] = []
    replay_summaries: list[dict[str, Any]] = []
    summary_fixtures: list[dict[str, Any]] = []

    for index, fixture in enumerate(fixtures):
        fixture_id = fixture["fixture_id"]
        variants = _expand_parameter_sweep(fixture.get("parameter_sweep", {}))
        step_count = _fixture_step_count(fixture, fixed_step_seconds, duration_seconds)
        sample_steps = _sample_steps(step_count)
        replay_path = f"{replay_output_dir}/{fixture_id}.replay_summary.json"
        harness_case_name = f"jolt::{fixture_id}"

        harness_entry = {
            "fixture_id": fixture_id,
            "title": fixture["title"],
            "harness_case_name": harness_case_name,
            "native_target": {
                "runtime": JOLT_RUNTIME_ID,
                "cmake_target": "raftsim_jolt_smoke_harness",
                "source": "physics/cpp/tools/jolt_smoke_harness.cpp",
                "sdk_dependency_status": "not_vendored_placeholder_path",
                "execution": (
                    "raftsim_jolt_smoke_harness physics/cpp/tests/jolt_smoke_harness_manifest.json"
                ),
            },
            "source_contract": source_contract_path,
            "fixed_step_seconds": fixed_step_seconds,
            "duration_seconds": round(step_count * fixed_step_seconds, 6),
            "step_count": step_count,
            "parameter_case_count": len(variants),
            "parameter_cases": variants,
            "setup": fixture["setup"],
            "metrics": fixture["metrics"],
            "pass_gates": fixture["pass_gates"],
            "telemetry_required": list(required_fields),
            "exports": {
                "summary": summary_output_path,
                "replay_summary": replay_path,
                "full_telemetry_stream": f"outputs/runtime_eval/jolt/{fixture_id}.telemetry.jsonl",
            },
            "status": "ready_for_native_smoke_harness_execution",
            "authoritative_evidence": False,
        }
        harness_fixtures.append(harness_entry)

        replay = _build_replay_summary(
            fixture=fixture,
            fixture_index=index,
            variants=variants,
            required_fields=required_fields,
            fixed_step_seconds=fixed_step_seconds,
            step_count=step_count,
            sample_steps=sample_steps,
            source_contract_path=source_contract_path,
            runtime_id=JOLT_RUNTIME_ID,
            replay_schema=JOLT_REPLAY_SUMMARY_SCHEMA,
            status="schema_placeholder_ready_for_native_smoke_harness_execution",
            telemetry_stream_dir="outputs/runtime_eval/jolt",
        )
        replay_summaries.append(replay)

        summary_fixtures.append(
            {
                "fixture_id": fixture_id,
                "harness_case_name": harness_case_name,
                "parameter_case_count": len(variants),
                "step_count": step_count,
                "replay_summary": replay_path,
                "telemetry_fields_present_in_schema_samples": _sample_has_required_fields(
                    replay, required_fields
                ),
                "pass_gate_count": len(fixture["pass_gates"]),
                "metrics": fixture["metrics"],
                "status": "ready_for_native_smoke_harness_execution",
                "authoritative_evidence": False,
            }
        )

    total_parameter_cases = sum(item["parameter_case_count"] for item in summary_fixtures)
    manifest = {
        "schema": JOLT_SMOKE_HARNESS_MANIFEST_SCHEMA,
        "source_contract": source_contract_path,
        "target_runtime": JOLT_RUNTIME_ID,
        "decision": JOLT_EXPORT_DECISION,
        "summary": (
            "Native Jolt smoke harness generated from the shared Chaos/Jolt "
            "runtime evaluation contract. The harness is source-controlled and "
            "schema-compatible, but Jolt SDK physics results are still pending."
        ),
        "fixed_step_seconds": fixed_step_seconds,
        "water_source": shared["water_source"],
        "telemetry_required": list(required_fields),
        "global_pass_gates": shared["global_pass_gates"],
        "native_harness": {
            "cmake_target": "raftsim_jolt_smoke_harness",
            "source": "physics/cpp/tools/jolt_smoke_harness.cpp",
            "manifest": manifest_output_path,
            "sdk_dependency_status": "not_vendored_placeholder_path",
            "summary": summary_output_path,
            "replay_dir": replay_output_dir,
        },
        "fixtures": harness_fixtures,
    }

    summary = {
        "schema": JOLT_SUMMARY_SCHEMA,
        "source_contract": source_contract_path,
        "native_harness_manifest": manifest_output_path,
        "runtime_id": JOLT_RUNTIME_ID,
        "decision": JOLT_EXPORT_DECISION,
        "fixture_count": len(fixtures),
        "expanded_parameter_case_count": total_parameter_cases,
        "replay_summary_count": len(replay_summaries),
        "telemetry_required": list(required_fields),
        "all_fixture_samples_match_required_telemetry": all(
            item["telemetry_fields_present_in_schema_samples"] for item in summary_fixtures
        ),
        "authority_selection_allowed": False,
        "runtime_passed_fixture_suite": False,
        "status": "ready_for_native_smoke_harness_execution",
        "fixtures": summary_fixtures,
        "notes": [
            "This artifact completes the native Jolt smoke harness export, not the Jolt authority decision.",
            "The harness target is buildable without vendoring Jolt and validates contract/schema plumbing first.",
            "Measured Jolt physics telemetry must replace placeholder frames before Jolt can be ranked against Chaos.",
        ],
    }
    markdown = _summary_markdown(summary, title="Milestone 19 Jolt Smoke Harness Export")
    return JoltSmokeHarnessExport(
        manifest=manifest,
        summary=summary,
        replays=tuple(replay_summaries),
        markdown=markdown,
    )


def write_chaos_automation_export(
    *,
    contract_path: Path,
    manifest_path: Path,
    report_dir: Path,
) -> ChaosAutomationExport:
    """Generate and write the Chaos automation manifest and report artifacts."""

    source_contract_path = _display_path(contract_path)
    manifest_output_path = _display_path(manifest_path)
    summary_path = report_dir / "summary.json"
    replay_dir = report_dir / "replays"
    export = build_chaos_automation_export(
        load_runtime_evaluation_contract(contract_path),
        source_contract_path=source_contract_path,
        manifest_output_path=manifest_output_path,
        summary_output_path=_display_path(summary_path),
        replay_output_dir=_display_path(replay_dir),
    )

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    replay_dir.mkdir(parents=True, exist_ok=True)

    _write_json(manifest_path, export.manifest)
    _write_json(summary_path, export.summary)
    (report_dir / "summary.md").write_text(export.markdown, encoding="utf-8")
    for replay in export.replays:
        replay_path = replay_dir / f"{replay['fixture_id']}.replay_summary.json"
        _write_json(replay_path, replay)
    return export


def write_jolt_smoke_harness_export(
    *,
    contract_path: Path,
    manifest_path: Path,
    report_dir: Path,
) -> JoltSmokeHarnessExport:
    """Generate and write the Jolt native smoke harness and report artifacts."""

    source_contract_path = _display_path(contract_path)
    manifest_output_path = _display_path(manifest_path)
    summary_path = report_dir / "summary.json"
    replay_dir = report_dir / "replays"
    export = build_jolt_smoke_harness_export(
        load_runtime_evaluation_contract(contract_path),
        source_contract_path=source_contract_path,
        manifest_output_path=manifest_output_path,
        summary_output_path=_display_path(summary_path),
        replay_output_dir=_display_path(replay_dir),
    )

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    replay_dir.mkdir(parents=True, exist_ok=True)

    _write_json(manifest_path, export.manifest)
    _write_json(summary_path, export.summary)
    (report_dir / "summary.md").write_text(export.markdown, encoding="utf-8")
    for replay in export.replays:
        replay_path = replay_dir / f"{replay['fixture_id']}.replay_summary.json"
        _write_json(replay_path, replay)
    return export


def build_chaos_jolt_comparison_report(
    *,
    contract: dict[str, Any],
    chaos_summary: dict[str, Any],
    jolt_summary: dict[str, Any],
    source_contract_path: str = "unreal/Content/RaftSim/Physics/chaos_jolt_runtime_evaluation.json",
    chaos_summary_path: str = "physics/reports/milestone19/chaos/summary.json",
    jolt_summary_path: str = "physics/reports/milestone19/jolt/summary.json",
) -> ChaosJoltComparisonReport:
    """Compare Chaos and Jolt fixture exports without selecting authority."""

    contract_fixture_ids = tuple(fixture["fixture_id"] for fixture in contract["fixtures"])
    chaos_fixtures = {fixture["fixture_id"]: fixture for fixture in chaos_summary["fixtures"]}
    jolt_fixtures = {fixture["fixture_id"]: fixture for fixture in jolt_summary["fixtures"]}
    fixture_rows = []
    for fixture_id in contract_fixture_ids:
        chaos_fixture = chaos_fixtures[fixture_id]
        jolt_fixture = jolt_fixtures[fixture_id]
        fixture_rows.append(
            {
                "fixture_id": fixture_id,
                "chaos_status": chaos_fixture["status"],
                "jolt_status": jolt_fixture["status"],
                "parameter_case_count_match": (
                    chaos_fixture["parameter_case_count"] == jolt_fixture["parameter_case_count"]
                ),
                "step_count_match": chaos_fixture["step_count"] == jolt_fixture["step_count"],
                "metrics_match": tuple(chaos_fixture["metrics"]) == tuple(jolt_fixture["metrics"]),
                "ready_for_measured_runtime_comparison": (
                    chaos_fixture["telemetry_fields_present_in_schema_samples"]
                    and jolt_fixture["telemetry_fields_present_in_schema_samples"]
                ),
                "evidence_state": "schema_placeholder_only",
            }
        )

    fixture_coverage_match = (
        set(chaos_fixtures) == set(jolt_fixtures) == set(contract_fixture_ids)
    )
    measured_evidence_available = (
        chaos_summary.get("runtime_passed_fixture_suite", False)
        and jolt_summary.get("runtime_passed_fixture_suite", False)
        and chaos_summary.get("authority_selection_allowed", False)
        and jolt_summary.get("authority_selection_allowed", False)
    )
    dimension_rankings = [
        _pending_dimension_ranking(dimension, chaos_summary, jolt_summary)
        for dimension in COMPARISON_DIMENSIONS
    ]
    report = {
        "schema": CHAOS_JOLT_COMPARISON_SCHEMA,
        "source_contract": source_contract_path,
        "inputs": {
            "chaos_summary": chaos_summary_path,
            "jolt_summary": jolt_summary_path,
        },
        "decision": CHAOS_JOLT_COMPARISON_DECISION,
        "fixture_coverage_match": fixture_coverage_match,
        "measured_evidence_available": measured_evidence_available,
        "authority_selection_allowed": False,
        "runtime_passed_fixture_suite": False,
        "fixture_count": len(contract_fixture_ids),
        "fixtures": fixture_rows,
        "dimension_rankings": dimension_rankings,
        "overall_ranking": [
            {
                "runtime": CHAOS_RUNTIME_ID,
                "rank": "tie_pending_measured_telemetry",
                "can_be_authoritative_now": False,
                "reason": "Chaos has fixture exports but no measured Chaos telemetry suite yet.",
            },
            {
                "runtime": JOLT_RUNTIME_ID,
                "rank": "tie_pending_measured_telemetry",
                "can_be_authoritative_now": False,
                "reason": "Jolt has a native smoke harness path but no measured Jolt SDK telemetry suite yet.",
            },
        ],
        "recommendation": (
            "Do not select Chaos or Jolt for scoring-critical raft/contact/swimmer authority yet. "
            "Run the generated Chaos automation fixtures and native Jolt smoke harness, replace "
            "placeholder frames with measured telemetry, then regenerate this comparison."
        ),
    }
    return ChaosJoltComparisonReport(report=report, markdown=_comparison_markdown(report))


def write_chaos_jolt_comparison_report(
    *,
    contract_path: Path,
    chaos_summary_path: Path,
    jolt_summary_path: Path,
    output_json: Path,
    output_md: Path,
) -> ChaosJoltComparisonReport:
    """Generate and write the Chaos-vs-Jolt comparison report."""

    report = build_chaos_jolt_comparison_report(
        contract=load_runtime_evaluation_contract(contract_path),
        chaos_summary=json.loads(chaos_summary_path.read_text(encoding="utf-8")),
        jolt_summary=json.loads(jolt_summary_path.read_text(encoding="utf-8")),
        source_contract_path=_display_path(contract_path),
        chaos_summary_path=_display_path(chaos_summary_path),
        jolt_summary_path=_display_path(jolt_summary_path),
    )
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output_json, report.report)
    output_md.write_text(report.markdown, encoding="utf-8")
    return report


def build_runtime_authority_selection_report(
    *,
    comparison_report: dict[str, Any],
    comparison_report_path: str = "physics/reports/milestone19/chaos_vs_jolt_comparison.json",
) -> RuntimeAuthoritySelectionReport:
    """Select the first vertical-slice runtime authority from current evidence."""

    chaos_or_jolt_ready = (
        comparison_report.get("authority_selection_allowed", False)
        and comparison_report.get("runtime_passed_fixture_suite", False)
        and comparison_report.get("measured_evidence_available", False)
    )
    if chaos_or_jolt_ready:
        decision = "runtime_candidate_ready_for_manual_selection"
        selected_runtime = "manual_review_required"
        selection_basis = "Measured Chaos/Jolt fixture evidence is available."
    else:
        decision = AUTHORITY_SELECTION_DECISION
        selected_runtime = FALLBACK_RUNTIME_ID
        selection_basis = (
            "Chaos and Jolt fixture exports exist, but the comparison report blocks "
            "authority selection because measured runtime telemetry has not replaced "
            "schema placeholder frames."
        )

    report = {
        "schema": AUTHORITY_SELECTION_SCHEMA,
        "decision": decision,
        "selected_runtime": selected_runtime,
        "selection_scope": "first_unreal_vertical_slice_raft_contact_swimmer_authority",
        "water_authority": "custom_cxx_shallow_water_solver",
        "comparison_report": comparison_report_path,
        "selection_basis": selection_basis,
        "chaos_status": "visual_and_non_authoritative_only_pending_measured_fixture_results",
        "jolt_status": "candidate_pending_measured_jolt_sdk_fixture_results",
        "custom_reduced_status": "selected_fallback_until_chaos_or_jolt_passes_measured_fixture_suite",
        "chrono_status": "high_fidelity_reference_and_research_only",
        "chaos_or_jolt_authority_selection_allowed": chaos_or_jolt_ready,
        "milestone19_closed": not chaos_or_jolt_ready,
        "replacement_conditions": [
            "Run measured Unreal Chaos automation fixtures over the shared contract.",
            "Run measured native Jolt SDK/plugin fixtures over the shared contract.",
            "Regenerate the Chaos-vs-Jolt comparison with non-placeholder telemetry.",
            "Select Chaos or Jolt only if the comparison report allows scoring-critical authority.",
        ],
        "unreal_manifest_updates": {
            "raft_dynamics_runtime": "unreal/Content/RaftSim/Physics/raft_dynamics_runtime.json",
            "physics_authority_policy": "unreal/Content/RaftSim/Physics/physics_authority_policy.json",
            "fixed_step_bridge": "unreal/Content/RaftSim/Physics/fixed_step_bridge.json",
        },
    }
    return RuntimeAuthoritySelectionReport(report=report, markdown=_selection_markdown(report))


def write_runtime_authority_selection_report(
    *,
    comparison_report_path: Path,
    output_json: Path,
    output_md: Path,
) -> RuntimeAuthoritySelectionReport:
    """Generate and write the Milestone 19 runtime authority decision."""

    report = build_runtime_authority_selection_report(
        comparison_report=json.loads(comparison_report_path.read_text(encoding="utf-8")),
        comparison_report_path=_display_path(comparison_report_path),
    )
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output_json, report.report)
    output_md.write_text(report.markdown, encoding="utf-8")
    return report


def _expand_parameter_sweep(sweep: dict[str, Any]) -> list[dict[str, Any]]:
    if not sweep:
        return [{}]

    keys = tuple(sweep)
    values = [
        value if isinstance(value, list) else [value]
        for value in (sweep[key] for key in keys)
    ]
    cases = []
    for case_index, combo in enumerate(itertools.product(*values)):
        case = {key: combo[index] for index, key in enumerate(keys)}
        case["case_id"] = f"case_{case_index:03d}"
        cases.append(case)
    return cases


def _fixture_step_count(
    fixture: dict[str, Any], fixed_step_seconds: float, default_duration_seconds: float
) -> int:
    sweep = fixture.get("parameter_sweep", {})
    if "step_count" in sweep:
        values = sweep["step_count"]
        return int(values[0] if isinstance(values, list) else values)
    if "duration_seconds" in sweep:
        values = sweep["duration_seconds"]
        duration_seconds = float(values[0] if isinstance(values, list) else values)
    else:
        duration_seconds = default_duration_seconds
    raw_steps = duration_seconds / fixed_step_seconds
    rounded_steps = round(raw_steps)
    if abs(raw_steps - rounded_steps) < 1.0e-3:
        return int(rounded_steps)
    return int(math.ceil(raw_steps))


def _sample_steps(step_count: int) -> tuple[int, ...]:
    if step_count <= 1:
        return (0,)
    middle = max(1, step_count // 2)
    last = max(0, step_count - 1)
    return tuple(dict.fromkeys((0, middle, last)))


def _build_replay_summary(
    *,
    fixture: dict[str, Any],
    fixture_index: int,
    variants: list[dict[str, Any]],
    required_fields: tuple[str, ...],
    fixed_step_seconds: float,
    step_count: int,
    sample_steps: tuple[int, ...],
    source_contract_path: str,
    runtime_id: str,
    replay_schema: str,
    status: str,
    telemetry_stream_dir: str,
) -> dict[str, Any]:
    representative_case = variants[0] if variants else {}
    frames = [
        _schema_sample_frame(
            fixture_id=fixture["fixture_id"],
            fixture_index=fixture_index,
            step_index=step,
            fixed_step_seconds=fixed_step_seconds,
            parameter_case=representative_case,
            runtime_id=runtime_id,
        )
        for step in sample_steps
    ]
    return {
        "schema": replay_schema,
        "runtime_id": runtime_id,
        "fixture_id": fixture["fixture_id"],
        "source_contract": source_contract_path,
        "status": status,
        "authoritative_evidence": False,
        "fixed_step_seconds": fixed_step_seconds,
        "step_count": step_count,
        "sampled_step_count": len(frames),
        "parameter_case_count": len(variants),
        "representative_parameter_case": representative_case,
        "telemetry_required": list(required_fields),
        "sample_frames": frames,
        "replay_reproduction": {
            "full_telemetry_stream": f"{telemetry_stream_dir}/{fixture['fixture_id']}.telemetry.jsonl",
            "determinism_hash_scope": "gameplay-state telemetry, contacts, raft pose, and fixture inputs",
            "replace_placeholder_frames_after_runtime_run": True,
        },
    }


def _schema_sample_frame(
    *,
    fixture_id: str,
    fixture_index: int,
    step_index: int,
    fixed_step_seconds: float,
    parameter_case: dict[str, Any],
    runtime_id: str,
) -> dict[str, Any]:
    phase = step_index * fixed_step_seconds
    contact_active = step_index > 0
    outcome = _placeholder_outcome(fixture_id, step_index)
    return {
        "runtime_id": runtime_id,
        "fixture_id": fixture_id,
        "step_index": step_index,
        "time_seconds": round(phase, 6),
        "sample_kind": "schema_placeholder",
        "parameter_case_id": parameter_case.get("case_id", "case_000"),
        "raft_pose": {
            "x_m": round(0.25 * step_index * fixed_step_seconds, 6),
            "y_m": round((fixture_index - 2) * 0.05, 6),
            "z_m": 0.0,
            "roll_deg": round(0.1 * fixture_index, 6),
            "pitch_deg": 0.0,
            "yaw_deg": round(0.02 * step_index, 6),
        },
        "raft_linear_velocity": {
            "x_mps": round(1.0 + fixture_index * 0.1, 6),
            "y_mps": 0.0,
            "z_mps": 0.0,
        },
        "raft_angular_velocity": {
            "roll_dps": 0.0,
            "pitch_dps": 0.0,
            "yaw_dps": round(0.05 * fixture_index, 6),
        },
        "contact_points": _placeholder_contacts(fixture_id, contact_active),
        "contact_impulses": [round(10.0 + fixture_index, 6)] if contact_active else [],
        "contact_material": _placeholder_contact_material(fixture_id),
        "crew_state": {
            "seated": 8 if fixture_id != "crew_ejection_swimmer_transition" else 7,
            "at_risk": fixture_id == "crew_ejection_swimmer_transition",
            "scripted_high_side": fixture_id == "pin_release_wrap_proxy",
        },
        "swimmer_state": {
            "active": fixture_id == "crew_ejection_swimmer_transition" and contact_active,
            "state": "swimming"
            if fixture_id == "crew_ejection_swimmer_transition" and contact_active
            else "none",
        },
        "pin_state": {
            "active": fixture_id == "pin_release_wrap_proxy" and contact_active,
            "load_n": round(250.0 + fixture_index * 25.0, 6)
            if fixture_id == "pin_release_wrap_proxy" and contact_active
            else 0.0,
        },
        "release_state": {
            "active": fixture_id == "pin_release_wrap_proxy" and step_index > 1,
            "trigger": "scripted_high_side"
            if fixture_id == "pin_release_wrap_proxy" and step_index > 1
            else "none",
        },
        "outcome": outcome,
        "runtime_cpu_ms": 0.0,
        "determinism_hash": _determinism_hash(runtime_id, fixture_id, step_index, parameter_case),
    }


def _placeholder_contacts(fixture_id: str, active: bool) -> list[dict[str, Any]]:
    if not active:
        return []
    return [
        {
            "body_a": "standard_14ft_paddle_raft",
            "body_b": _placeholder_contact_material(fixture_id),
            "position_m": {"x": 0.0, "y": 0.0, "z": 0.0},
            "normal": {"x": -1.0, "y": 0.0, "z": 0.0},
        }
    ]


def _placeholder_contact_material(fixture_id: str) -> str:
    if "shelf" in fixture_id or "grounding" in fixture_id:
        return "bed_grounding_inelastic_default"
    if "pin" in fixture_id or "rock" in fixture_id:
        return "rock_elastic_default"
    if "crowded" in fixture_id:
        return "mixed_non_authoritative_scene"
    return "runtime_eval_default"


def _placeholder_outcome(fixture_id: str, step_index: int) -> str:
    if step_index == 0:
        return "initialized"
    if fixture_id == "pin_release_wrap_proxy":
        return "pinned_or_releasing"
    if fixture_id == "crew_ejection_swimmer_transition":
        return "ejected_to_swimmer"
    if fixture_id == "shallow_shelf_grounding":
        return "grounding_or_release"
    if fixture_id == "runtime_cost_crowded_scene":
        return "profiling_scene_active"
    return "contact_response_active"


def _sample_has_required_fields(replay: dict[str, Any], required_fields: tuple[str, ...]) -> bool:
    return all(required in replay["sample_frames"][0] for required in required_fields)


def _automation_name_suffix(fixture_id: str) -> str:
    return "".join(part.capitalize() for part in fixture_id.split("_"))


def _determinism_hash(
    runtime_id: str, fixture_id: str, step_index: int, parameter_case: dict[str, Any]
) -> str:
    payload = json.dumps(
        {
            "runtime": runtime_id,
            "fixture": fixture_id,
            "step": step_index,
            "case": parameter_case,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _summary_markdown(
    summary: dict[str, Any],
    *,
    title: str = "Milestone 19 Chaos Automation Fixture Export",
) -> str:
    lines = [
        f"# {title}",
        "",
        f"Decision: `{summary['decision']}`",
        "",
        (
            f"Exported {summary['fixture_count']} {summary['runtime_id']} fixtures with "
            f"{summary['expanded_parameter_case_count']} expanded parameter cases and "
            f"{summary['replay_summary_count']} replay summaries."
        ),
        "",
        "These files are automation-ready fixtures, not authority evidence. The runtime still needs to execute the generated fixtures and replace placeholder telemetry frames with measured results before it can be ranked against the other candidate.",
        "",
        "## Fixtures",
        "",
    ]
    for fixture in summary["fixtures"]:
        lines.append(
            "- "
            f"`{fixture['fixture_id']}`: {fixture['parameter_case_count']} parameter cases, "
            f"{fixture['step_count']} fixed steps, replay `{fixture['replay_summary']}`."
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            *[f"- {note}" for note in summary["notes"]],
            "",
        ]
    )
    return "\n".join(lines)


def _pending_dimension_ranking(
    dimension: str, chaos_summary: dict[str, Any], jolt_summary: dict[str, Any]
) -> dict[str, Any]:
    return {
        "dimension": dimension,
        "winner": "insufficient_measured_evidence",
        "rankings": [
            {
                "runtime": chaos_summary["runtime_id"],
                "rank": "tie_pending_measured_telemetry",
                "score": None,
                "evidence_state": "schema_placeholder_only",
            },
            {
                "runtime": jolt_summary["runtime_id"],
                "rank": "tie_pending_measured_telemetry",
                "score": None,
                "evidence_state": "schema_placeholder_only",
            },
        ],
        "required_next_evidence": _dimension_next_evidence(dimension),
    }


def _dimension_next_evidence(dimension: str) -> tuple[str, ...]:
    requirements = {
        "determinism": (
            "determinism_hash_mismatch_count",
            "contact_event_sequence_mismatch_count",
            "outcome_mismatch_count",
        ),
        "cpu_cost": (
            "mean_cpu_ms_per_step",
            "p95_cpu_ms_per_step",
            "max_cpu_ms_per_step",
            "telemetry_bytes_per_second",
        ),
        "contact_quality": (
            "peak_contact_impulse_n_s",
            "max_bed_penetration_m",
            "scrape_impulse_n_s",
            "pin_duration_seconds",
        ),
        "outcome_stability": (
            "bounce_scrape_or_pin_classification",
            "release_or_stick_outcome",
            "flip_or_release_outcome",
            "outcome_mismatch_count",
        ),
        "swimmer_state": (
            "ejection_trigger_step",
            "crew_state_sequence",
            "swimmer_position_error_m",
            "time_to_water_contact_seconds",
        ),
        "authoring_debug_ergonomics": (
            "debug_overlay_capture",
            "headless_summary",
            "fixture_iteration_time",
            "replay_explainability",
        ),
    }
    return requirements[dimension]


def _comparison_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Milestone 19 Chaos-vs-Jolt Comparison",
        "",
        f"Decision: `{report['decision']}`",
        "",
        report["recommendation"],
        "",
        "## Dimension Rankings",
        "",
    ]
    for dimension in report["dimension_rankings"]:
        lines.append(
            f"- `{dimension['dimension']}`: {dimension['winner']} "
            f"({', '.join(dimension['required_next_evidence'])})."
        )
    lines.extend(
        [
            "",
            "## Fixture Coverage",
            "",
            f"- Fixture coverage match: `{report['fixture_coverage_match']}`.",
            f"- Measured evidence available: `{report['measured_evidence_available']}`.",
            f"- Authority selection allowed: `{report['authority_selection_allowed']}`.",
            "",
        ]
    )
    return "\n".join(lines)


def _selection_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Milestone 19 Runtime Authority Selection",
        "",
        f"Decision: `{report['decision']}`",
        "",
        f"Selected runtime: `{report['selected_runtime']}`",
        "",
        report["selection_basis"],
        "",
        "## Runtime Status",
        "",
        f"- Chaos: {report['chaos_status']}.",
        f"- Jolt: {report['jolt_status']}.",
        f"- Custom reduced: {report['custom_reduced_status']}.",
        f"- Chrono: {report['chrono_status']}.",
        "",
        "## Replacement Conditions",
        "",
        *[f"- {condition}" for condition in report["replacement_conditions"]],
        "",
    ]
    return "\n".join(lines)


def _display_path(path: Path) -> str:
    return path.as_posix()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
