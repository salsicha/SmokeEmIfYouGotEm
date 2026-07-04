"""Milestone 20 Unreal production foundation artifacts."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MILESTONE20_REPORT_SET_LOCK_SCHEMA = "raftsim.milestone20.report_set_lock.v1"
MILESTONE20_REPORT_SET_LOCK_DECISION = (
    "accepted_milestone16_report_set_locked_target_profiles_pass"
)
MILESTONE20_UNREAL_REGRESSION_IMPORT_SCHEMA = (
    "raftsim.unreal.regression_fixture_import.v1"
)
MILESTONE20_TRACEABLE_DATA_ASSETS_SCHEMA = "raftsim.unreal.traceable_river_data_assets.v1"

MILESTONE16_SOURCE_REPORTS = (
    "physics/reports/milestone16/cpp_solver_runs.json",
    "physics/reports/milestone16/cpp_solver_runs.md",
    "physics/reports/milestone16/full_cpp_validation_gate.json",
    "physics/reports/milestone16/full_cpp_validation_gate.md",
    "physics/reports/milestone16/geoclaw_cpp_comparisons.json",
    "physics/reports/milestone16/geoclaw_cpp_comparisons.md",
    "physics/reports/milestone16/geoclaw_reference_runs.json",
    "physics/reports/milestone16/geoclaw_reference_runs.md",
    "physics/reports/milestone16/geometry_validation.json",
    "physics/reports/milestone16/geometry_validation.md",
    "physics/reports/milestone16/raft_coupling_validation.json",
    "physics/reports/milestone16/raft_coupling_validation.md",
    "physics/reports/milestone16/regression_promotion_manifest.json",
    "physics/reports/milestone16/regression_promotion_manifest.md",
    "physics/reports/milestone16/runtime_profile.json",
    "physics/reports/milestone16/runtime_profile.md",
)

MILESTONE16_READINESS_ARTIFACTS = (
    "physics/data/readiness/milestone_16/cpp_solver_summary.json",
    "physics/data/readiness/milestone_16/geoclaw_cpp_comparison_summary.json",
    "physics/data/readiness/milestone_16/geoclaw_reference_summary.json",
    "physics/data/readiness/milestone_16/geoclaw_to_unreal_readiness_report.json",
    "physics/data/readiness/milestone_16/geoclaw_to_unreal_readiness_report.md",
    "physics/data/readiness/milestone_16/geometry_validation_summary.json",
    "physics/data/readiness/milestone_16/raft_coupling_validation_summary.json",
    "physics/data/readiness/milestone_16/regression_promotion_summary.json",
    "physics/data/readiness/milestone_16/runtime_profile_summary.json",
)

MILESTONE20_SUPPORTING_ARTIFACTS = (
    "physics/config/runtime_budgets.json",
    "docs/physics-runtime-budgets.md",
)

MILESTONE18_UNREAL_IMPORT_REPORTS = (
    (
        "remaining_geometry_closure",
        "geometry_closure",
        "physics/reports/milestone18/remaining_geometry_closure.json",
    ),
    (
        "geoclaw_cpp_failure_triage_matrix",
        "failure_triage_closure",
        "physics/reports/milestone18/geoclaw_cpp_failure_triage_matrix.json",
    ),
    (
        "pin_release_fixture",
        "pin_release_gameplay_guardrail",
        "physics/reports/milestone18/pin_release_fixture.json",
    ),
    (
        "raft_coupling_agreement_closure",
        "raft_coupling_agreement_closure",
        "physics/reports/milestone18/raft_coupling_agreement_closure.json",
    ),
)

MILESTONE20_CASCADING_DATA_ASSETS = (
    ("low_runnable", "reduced", "cg_low/reduced"),
    ("low_runnable", "finite_volume", "cg_low/finite_volume"),
    ("median_runnable", "reduced", "cg_med/reduced"),
    ("median_runnable", "finite_volume", "cg_med/finite_volume"),
    ("high_runnable", "reduced", "cg_high/reduced"),
    ("high_runnable", "finite_volume", "cg_high/finite_volume"),
)


@dataclass(frozen=True, slots=True)
class Milestone20ReportSetLock:
    """Generated lock file and human-readable summary."""

    report: dict[str, Any]
    markdown: str


@dataclass(frozen=True, slots=True)
class Milestone20UnrealRegressionImport:
    """Generated Unreal automation import manifest for accepted water fixtures."""

    manifest: dict[str, Any]


@dataclass(frozen=True, slots=True)
class Milestone20TraceableDataAssets:
    """Generated Unreal traceable river data asset manifest."""

    manifest: dict[str, Any]


def build_report_set_lock(repo_root: Path) -> Milestone20ReportSetLock:
    """Build the accepted Milestone 16 report-set lock and profile summary."""

    root = repo_root.resolve()
    artifacts = [
        *_artifact_entries(root, MILESTONE16_SOURCE_REPORTS, group="milestone16_source_report"),
        *_artifact_entries(
            root, MILESTONE16_READINESS_ARTIFACTS, group="milestone16_readiness_package"
        ),
        *_artifact_entries(root, MILESTONE20_SUPPORTING_ARTIFACTS, group="runtime_budget_contract"),
    ]
    runtime_profile_path = root / "physics/reports/milestone16/runtime_profile.json"
    full_gate_path = root / "physics/reports/milestone16/full_cpp_validation_gate.json"
    readiness_path = (
        root / "physics/data/readiness/milestone_16/geoclaw_to_unreal_readiness_report.json"
    )
    runtime_profile = _read_json(runtime_profile_path)
    full_gate = _read_json(full_gate_path)
    readiness = _read_json(readiness_path)

    profile_confirmation = _build_target_profile_confirmation(
        runtime_profile=runtime_profile,
        budget_config=_read_json(root / "physics/config/runtime_budgets.json"),
    )
    source_gate_passed = bool(full_gate.get("passed")) and full_gate.get("decision") == "PASS"
    readiness_passed = bool(readiness.get("passed")) and (
        readiness.get("decision", {}).get("approved_for_unreal_production_start") is True
    )
    passed = bool(
        source_gate_passed
        and readiness_passed
        and profile_confirmation["all_profiles_passed"]
        and profile_confirmation["deterministic_replay"]["passed"]
    )
    report = {
        "schema": MILESTONE20_REPORT_SET_LOCK_SCHEMA,
        "decision": MILESTONE20_REPORT_SET_LOCK_DECISION if passed else "blocked",
        "passed": passed,
        "lock": {
            "lock_hash": _lock_hash(artifacts),
            "artifact_count": len(artifacts),
            "source_report_count": len(MILESTONE16_SOURCE_REPORTS),
            "readiness_artifact_count": len(MILESTONE16_READINESS_ARTIFACTS),
            "supporting_artifact_count": len(MILESTONE20_SUPPORTING_ARTIFACTS),
            "hash_algorithm": "sha256",
        },
        "source_gate": {
            "report": _display_path(full_gate_path),
            "decision": full_gate.get("decision"),
            "passed": source_gate_passed,
            "component_count": full_gate.get("component_count"),
            "passed_component_count": full_gate.get("passed_component_count"),
            "blocked_component_count": full_gate.get("blocked_component_count"),
        },
        "readiness_gate": {
            "report": _display_path(readiness_path),
            "status": readiness.get("decision", {}).get("status"),
            "approved_for_unreal_production_start": readiness.get("decision", {}).get(
                "approved_for_unreal_production_start"
            ),
            "passed": readiness_passed,
            "required_next_actions": readiness.get("decision", {}).get(
                "required_next_actions", []
            ),
        },
        "target_profile_confirmation": profile_confirmation,
        "production_use": {
            "live_water_unreal_bridge_foundation_unblocked": passed,
            "authoritative_water_source": "custom_cxx_shallow_water_solver",
            "report_manifest_loading_required": True,
            "physical_device_capture_status": "not_recorded_in_repo",
            "physical_device_capture_policy": (
                "Replace or extend this lock with measured desktop, VR, and handheld "
                "device telemetry before release hardening or platform sign-off. The "
                "committed evidence confirms target budget profiles, not lab hardware IDs."
            ),
        },
        "artifacts": artifacts,
        "notes": [
            "The lock hash covers the accepted Milestone 16 source reports, packaged readiness summaries, and runtime budget contract.",
            "Runtime profile evidence is repeated here by evaluating every committed Milestone 16 profile record against desktop, VR, and handheld budget profiles.",
            "This artifact is the manifest Unreal live-water bridge work should load until a newer accepted report-set lock supersedes it.",
        ],
    }
    return Milestone20ReportSetLock(report=report, markdown=_report_set_lock_markdown(report))


def write_report_set_lock(
    *,
    repo_root: Path,
    output_json: Path,
    output_md: Path,
) -> Milestone20ReportSetLock:
    """Generate and write the Milestone 20 report-set lock artifacts."""

    lock = build_report_set_lock(repo_root)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output_json, lock.report)
    output_md.write_text(lock.markdown, encoding="utf-8")
    return lock


def build_unreal_regression_fixture_import(repo_root: Path) -> Milestone20UnrealRegressionImport:
    """Build the Unreal automation import manifest for promoted water fixtures."""

    root = repo_root.resolve()
    report_lock = _read_json(root / "physics/reports/milestone20/report_set_lock.json")
    m16_registry_path = root / "physics/regression_fixtures/milestone16/registry.json"
    m16_registry = _read_json(m16_registry_path)
    m17_report_path = root / "physics/reports/milestone17/analytic_fixture_validation.json"
    m17_report = _read_json(m17_report_path)

    m16_fixtures = [_m16_unreal_fixture(entry) for entry in m16_registry["entries"]]
    m17_fixtures = [_m17_unreal_fixture(comparison) for comparison in m17_report["comparisons"]]
    m18_fixtures = [_m18_unreal_fixture(root, fixture_id, category, path) for fixture_id, category, path in MILESTONE18_UNREAL_IMPORT_REPORTS]
    total_fixture_count = len(m16_fixtures) + len(m17_fixtures) + len(m18_fixtures)

    manifest = {
        "schema": MILESTONE20_UNREAL_REGRESSION_IMPORT_SCHEMA,
        "accepted_report_set_lock": {
            "manifest": "physics/reports/milestone20/report_set_lock.json",
            "lock_hash": report_lock["lock"]["lock_hash"],
        },
        "live_water_bridge_manifest": "unreal/Content/RaftSim/Physics/live_water_bridge.json",
        "automation_module": "RaftSimAutomation",
        "automation_test_prefix": "RaftSim.Milestone20.LiveWaterRegression",
        "comparison_modes": [
            "replayed_water_field_vs_accepted_cpp_output",
            "live_water_field_vs_accepted_cpp_output",
        ],
        "source_milestones": {
            "milestone16": {
                "registry": "physics/regression_fixtures/milestone16/registry.json",
                "source_report": "physics/reports/milestone16/regression_promotion_manifest.json",
                "fixture_count": len(m16_fixtures),
                "categories": _count_by(m16_fixtures, "category"),
                "suites": _count_by(m16_fixtures, "suite"),
                "fixtures": m16_fixtures,
            },
            "milestone17": {
                "source_report": "physics/reports/milestone17/analytic_fixture_validation.json",
                "fixture_count": len(m17_fixtures),
                "passed_count": m17_report["passed_count"],
                "fixtures": m17_fixtures,
            },
            "milestone18": {
                "fixture_count": len(m18_fixtures),
                "source_reports": [path for _, _, path in MILESTONE18_UNREAL_IMPORT_REPORTS],
                "fixtures": m18_fixtures,
            },
        },
        "total_fixture_count": total_fixture_count,
        "pass_policy": {
            "report_manifest_lock_must_match": True,
            "replayed_fields_must_match_accepted_cpp_outputs": True,
            "live_fields_must_match_accepted_cpp_outputs": True,
            "stitched_whole_window_outputs_required_for_reach_local_content": True,
            "feature_forcing_must_remain_off_unless_manifest_recorded": True,
        },
        "status": "ready_for_unreal_automation_execution",
    }
    return Milestone20UnrealRegressionImport(manifest=manifest)


def write_unreal_regression_fixture_import(
    *,
    repo_root: Path,
    output_json: Path,
) -> Milestone20UnrealRegressionImport:
    """Generate and write the Unreal water regression fixture import manifest."""

    generated = build_unreal_regression_fixture_import(repo_root)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output_json, generated.manifest)
    return generated


def build_traceable_unreal_data_assets(repo_root: Path) -> Milestone20TraceableDataAssets:
    """Build the Unreal traceable river data-asset manifest."""

    root = repo_root.resolve()
    report_lock = _read_json(root / "physics/reports/milestone20/report_set_lock.json")
    regression_import = _read_json(
        root / "unreal/Content/RaftSim/Automation/water_regression_fixture_import.json"
    )
    assets: list[dict[str, Any]] = [
        {
            "asset_id": "solver_neutral_milestone16_registry",
            "asset_class": "URaftSimTraceableRiverDataAsset",
            "kind": "solver_neutral_scenario_collection",
            "display_name": "Milestone 16 Solver-Neutral Regression Scenario Registry",
            "source_paths": [
                "physics/regression_fixtures/milestone16/registry.json",
                "physics/reports/milestone16/regression_promotion_manifest.json",
            ],
            "fixture_count": regression_import["source_milestones"]["milestone16"]["fixture_count"],
            "category_counts": regression_import["source_milestones"]["milestone16"]["categories"],
            "traceability": {
                "accepted_report_set_lock": "physics/reports/milestone20/report_set_lock.json",
                "unreal_regression_import": "unreal/Content/RaftSim/Automation/water_regression_fixture_import.json",
            },
        }
    ]
    assets.extend(_cascading_data_asset(root, flow_band, solver_mode, scenario_slug) for flow_band, solver_mode, scenario_slug in MILESTONE20_CASCADING_DATA_ASSETS)
    assets.extend(
        [
            {
                "asset_id": "south_fork_american_source_manifest",
                "asset_class": "URaftSimTraceableRiverDataAsset",
                "kind": "geospatial_source_manifest",
                "display_name": "South Fork American Chili Bar Source Manifest",
                "source_paths": [
                    "physics/data/real_world/south_fork_american_chili_bar/source_manifest.json"
                ],
                "coordinate_reference_systems": _read_json(
                    root
                    / "physics/data/real_world/south_fork_american_chili_bar/source_manifest.json"
                ).get("coordinate_reference_systems", {}),
                "traceability": {
                    "corridor_package": "physics/data/real_world/south_fork_american_chili_bar/corridor_package_manifest.json",
                    "validation_matrix": "physics/data/real_world/south_fork_american_chili_bar/validation_matrix.json",
                },
            },
            {
                "asset_id": "south_fork_american_unreal_corridor_package",
                "asset_class": "URaftSimTraceableRiverDataAsset",
                "kind": "unreal_corridor_package",
                "display_name": "South Fork American Chili Bar Unreal Corridor Package",
                "source_paths": [
                    "physics/data/real_world/south_fork_american_chili_bar/corridor_package_manifest.json"
                ],
                "unreal_ready_artifacts": _read_json(
                    root
                    / "physics/data/real_world/south_fork_american_chili_bar/corridor_package_manifest.json"
                ).get("unreal_ready_artifacts", {}),
                "traceability": {
                    "source_manifest": "physics/data/real_world/south_fork_american_chili_bar/source_manifest.json",
                    "validation_matrix": "physics/data/real_world/south_fork_american_chili_bar/validation_matrix.json",
                },
            },
        ]
    )

    manifest = {
        "schema": MILESTONE20_TRACEABLE_DATA_ASSETS_SCHEMA,
        "asset_class": "URaftSimTraceableRiverDataAsset",
        "accepted_report_set_lock": {
            "manifest": "physics/reports/milestone20/report_set_lock.json",
            "lock_hash": report_lock["lock"]["lock_hash"],
        },
        "source_manifests": {
            "regression_import": "unreal/Content/RaftSim/Automation/water_regression_fixture_import.json",
            "live_water_bridge": "unreal/Content/RaftSim/Physics/live_water_bridge.json",
            "production_foundation": "unreal/Content/RaftSim/Production/production_foundation.json",
        },
        "data_assets": assets,
        "asset_count": len(assets),
        "traceability_rules": [
            "Every data asset must point back to repo-relative source paths and the accepted report-set lock.",
            "Reach-local grid assets must include ghost-zone metadata and stitched whole-window validation outputs.",
            "Geospatial and corridor package assets must preserve CRS/provenance and validation-matrix paths.",
            "Unreal may cache or convert these assets, but converted assets cannot replace the source manifests.",
        ],
        "status": "ready_for_unreal_data_asset_loading",
    }
    return Milestone20TraceableDataAssets(manifest=manifest)


def write_traceable_unreal_data_assets(
    *,
    repo_root: Path,
    output_json: Path,
) -> Milestone20TraceableDataAssets:
    """Generate and write the Unreal traceable river data-asset manifest."""

    generated = build_traceable_unreal_data_assets(repo_root)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output_json, generated.manifest)
    return generated


def _artifact_entries(root: Path, paths: tuple[str, ...], *, group: str) -> list[dict[str, Any]]:
    return [_artifact_entry(root, path, group=group) for path in paths]


def _m16_unreal_fixture(entry: dict[str, Any]) -> dict[str, Any]:
    artifact_id = str(entry["artifact_id"])
    return {
        "fixture_id": artifact_id,
        "milestone": 16,
        "category": entry["category"],
        "suite": entry.get("suite", "unknown"),
        "gate_scenario_id": entry.get("gate_scenario_id"),
        "solver_mode": entry.get("solver_mode"),
        "case_id": entry.get("case_id"),
        "scenario_package": _physics_path(entry.get("scenario_package")),
        "accepted_manifest": _physics_path(entry.get("manifest")),
        "accepted_reports": {
            key: _physics_path(value)
            for key, value in sorted(entry.get("reports", {}).items())
        },
        "source_report": _physics_path(entry.get("source_report")),
        "automation_test_name": _automation_test_name("M16", artifact_id),
        "comparison_modes": [
            "replayed_water_field_vs_accepted_cpp_output",
            "live_water_field_vs_accepted_cpp_output",
        ],
    }


def _m17_unreal_fixture(comparison: dict[str, Any]) -> dict[str, Any]:
    fixture_id = comparison["fixture_id"]
    return {
        "fixture_id": f"milestone17/{fixture_id}",
        "milestone": 17,
        "category": "analytic_guardrail",
        "suite": "analytic",
        "title": comparison.get("title"),
        "tolerance_tier": comparison.get("tolerance_tier"),
        "scenario_package": _physics_path(comparison.get("scenario_package")),
        "reference_path": _physics_path(comparison.get("reference_path")),
        "source_report": "physics/reports/milestone17/analytic_fixture_validation.json",
        "metric_count": len(comparison.get("metrics", [])),
        "automation_test_name": _automation_test_name("M17", fixture_id),
        "comparison_modes": [
            "live_initial_or_replayed_field_vs_analytic_reference",
        ],
    }


def _m18_unreal_fixture(root: Path, fixture_id: str, category: str, source_report: str) -> dict[str, Any]:
    report = _read_json(root / source_report)
    decision = report.get("decision")
    passed = bool(report.get("passed", decision == "PASS"))
    summary = report.get("summary", {})
    return {
        "fixture_id": f"milestone18/{fixture_id}",
        "milestone": 18,
        "category": category,
        "suite": "closure",
        "source_report": source_report,
        "schema_version": report.get("schema_version"),
        "decision": decision,
        "passed": passed,
        "summary": summary if isinstance(summary, dict) else {},
        "automation_test_name": _automation_test_name("M18", fixture_id),
        "comparison_modes": [
            "unreal_replay_summary_vs_closure_report",
            "live_water_summary_vs_closure_report",
        ],
    }


def _cascading_data_asset(
    root: Path, flow_band: str, solver_mode: str, scenario_slug: str
) -> dict[str, Any]:
    scenario_root = (
        Path("physics/regression_fixtures/milestone16/geoclaw_cpp")
        / scenario_slug
        / "scenario"
    )
    metadata_path = scenario_root / "cascading_metadata.json"
    metadata = _read_json(root / metadata_path)
    stitched = metadata["validation_outputs"]["stitched_whole_window"]
    reach_grids = metadata["reach_local_grids"]
    upstream_ghost_cells = [int(grid["upstream_ghost_cells"]) for grid in reach_grids]
    downstream_ghost_cells = [int(grid["downstream_ghost_cells"]) for grid in reach_grids]
    asset_id = f"south_fork_cascading_{flow_band}_{solver_mode}"
    return {
        "asset_id": asset_id,
        "asset_class": "URaftSimTraceableRiverDataAsset",
        "kind": "reach_local_grid_with_stitched_validation",
        "display_name": f"South Fork Cascading {flow_band} {solver_mode}",
        "flow_band": flow_band,
        "solver_mode": solver_mode,
        "source_paths": [
            str(scenario_root / "scenario.json"),
            str(metadata_path),
            str(scenario_root / stitched["manifest"]),
        ],
        "scenario_package": str(scenario_root),
        "reach_local_grid_count": len(reach_grids),
        "reach_ids": [grid["reach_id"] for grid in reach_grids],
        "ghost_zone_policy": {
            "min_upstream_ghost_cells": min(upstream_ghost_cells),
            "max_upstream_ghost_cells": max(upstream_ghost_cells),
            "min_downstream_ghost_cells": min(downstream_ghost_cells),
            "max_downstream_ghost_cells": max(downstream_ghost_cells),
            "source": str(metadata_path),
        },
        "stitched_validation": {
            "required": True,
            "schema_version": stitched["schema_version"],
            "manifest": str(scenario_root / stitched["manifest"]),
            "fields": str(scenario_root / stitched["fields"]),
            "conservation_summary": str(scenario_root / stitched["conservation_summary"]),
            "probes": str(scenario_root / stitched["probes"]),
            "raft_transition_checkpoints": str(
                scenario_root / stitched["raft_transition_checkpoints"]
            ),
        },
        "traceability": {
            "regression_registry": "physics/regression_fixtures/milestone16/registry.json",
            "source_report": "physics/reports/milestone16/regression_promotion_manifest.json",
        },
    }


def _physics_path(path: object) -> str | None:
    if path in (None, ""):
        return None
    value = str(path)
    if value.startswith(("physics/", "unreal/", "docs/")):
        return value
    return f"physics/{value}"


def _automation_test_name(milestone: str, fixture_id: str) -> str:
    cleaned = "".join(char if char.isalnum() else "_" for char in fixture_id).strip("_")
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return f"RaftSim.Milestone20.LiveWaterRegression.{milestone}.{cleaned}"


def _count_by(fixtures: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for fixture in fixtures:
        value = str(fixture.get(key, "unknown"))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _artifact_entry(root: Path, relative_path: str, *, group: str) -> dict[str, Any]:
    path = root / relative_path
    if not path.exists():
        raise FileNotFoundError(f"required Milestone 20 lock artifact is missing: {relative_path}")
    data = path.read_bytes()
    return {
        "path": relative_path,
        "group": group,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _build_target_profile_confirmation(
    *, runtime_profile: dict[str, Any], budget_config: dict[str, Any]
) -> dict[str, Any]:
    records = runtime_profile.get("records", [])
    if not isinstance(records, list) or not records:
        raise ValueError("runtime_profile records must be a non-empty list")

    profiles: list[dict[str, Any]] = []
    profile_configs = budget_config.get("profiles", {})
    for profile_id in sorted(profile_configs):
        config = profile_configs[profile_id]
        profile_records = []
        for record in records:
            if not isinstance(record, dict):
                continue
            result = record.get("budget_results", {}).get(profile_id)
            if isinstance(result, dict):
                profile_records.append((record, result))
        if not profile_records:
            raise ValueError(f"runtime_profile has no budget results for profile {profile_id!r}")
        runtime_values = [
            float(result["runtime_ms_per_tick"])
            for _, result in profile_records
            if "runtime_ms_per_tick" in result
        ]
        passed_count = sum(1 for _, result in profile_records if bool(result.get("passed")))
        max_budget_values = [float(result["max_runtime_budget_ms"]) for _, result in profile_records]
        profiles.append(
            {
                "profile": profile_id,
                "render_target_hz": config.get("render_target_hz"),
                "physics_tick_hz": config.get("physics_tick_hz"),
                "record_count": len(profile_records),
                "passed_count": passed_count,
                "failed_count": len(profile_records) - passed_count,
                "passed": passed_count == len(profile_records),
                "water_solver_budget_ms": config.get("water_solver_ms"),
                "max_runtime_budget_ms": round(max(max_budget_values), 6),
                "mean_runtime_ms_per_tick": round(statistics.fmean(runtime_values), 6),
                "p95_runtime_ms_per_tick": round(_percentile(runtime_values, 95), 6),
                "max_runtime_ms_per_tick": round(max(runtime_values), 6),
            }
        )

    replays = runtime_profile.get("deterministic_replay", [])
    if not isinstance(replays, list):
        raise ValueError("runtime_profile deterministic_replay must be a list")
    replay_passed_count = sum(
        1 for replay in replays if isinstance(replay, dict) and bool(replay.get("passed"))
    )
    return {
        "source_report": "physics/reports/milestone16/runtime_profile.json",
        "budget_config": runtime_profile.get("budget_config"),
        "cpp_solver": runtime_profile.get("cpp_solver"),
        "evidence_scope": (
            "committed_milestone16_runtime_records_evaluated_against_target_budget_profiles"
        ),
        "physical_hardware_capture_status": "not_recorded_in_repo",
        "run_count": len(records),
        "all_profiles_passed": all(profile["passed"] for profile in profiles),
        "profiles": profiles,
        "deterministic_replay": {
            "group_count": len(replays),
            "passed_count": replay_passed_count,
            "failed_count": len(replays) - replay_passed_count,
            "passed": replay_passed_count == len(replays),
        },
    }


def _percentile(values: list[float], percentile: int) -> float:
    if not values:
        raise ValueError("cannot compute percentile of empty values")
    ordered = sorted(values)
    index = math.ceil((percentile / 100.0) * len(ordered)) - 1
    return ordered[max(0, min(index, len(ordered) - 1))]


def _lock_hash(artifacts: list[dict[str, Any]]) -> str:
    payload = [
        {"path": artifact["path"], "sha256": artifact["sha256"]}
        for artifact in sorted(artifacts, key=lambda item: item["path"])
    ]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _report_set_lock_markdown(report: dict[str, Any]) -> str:
    target = report["target_profile_confirmation"]
    lines = [
        "# Milestone 20 Report Set Lock",
        "",
        f"Decision: `{report['decision']}`",
        "",
        (
            f"Locked {report['lock']['artifact_count']} artifacts with SHA-256 lock "
            f"`{report['lock']['lock_hash']}`."
        ),
        "",
        "## Source Gates",
        "",
        (
            f"- Milestone 16 full C++ validation gate: `{report['source_gate']['decision']}`, "
            f"{report['source_gate']['passed_component_count']} of "
            f"{report['source_gate']['component_count']} components passed."
        ),
        (
            "- GeoClaw-to-Unreal readiness gate: "
            f"`{report['readiness_gate']['status']}`, "
            f"approved={report['readiness_gate']['approved_for_unreal_production_start']}."
        ),
        "",
        "## Target Profile Confirmation",
        "",
        (
            f"Runtime evidence scope: `{target['evidence_scope']}`. Physical hardware "
            f"capture status: `{target['physical_hardware_capture_status']}`."
        ),
        "",
        "| Profile | Records | Passed | Mean ms/tick | P95 ms/tick | Max ms/tick | Max Budget |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for profile in target["profiles"]:
        lines.append(
            f"| {profile['profile']} | {profile['record_count']} | "
            f"{profile['passed_count']} | {profile['mean_runtime_ms_per_tick']:.6f} | "
            f"{profile['p95_runtime_ms_per_tick']:.6f} | "
            f"{profile['max_runtime_ms_per_tick']:.6f} | "
            f"{profile['max_runtime_budget_ms']:.6f} |"
        )
    replay = target["deterministic_replay"]
    lines.extend(
        [
            "",
            "## Deterministic Replay",
            "",
            (
                f"{replay['passed_count']} of {replay['group_count']} deterministic replay "
                f"groups passed."
            ),
            "",
            "## Production Use",
            "",
            (
                "The live-water Unreal bridge can use this lock as its accepted report "
                "manifest. Physical desktop, VR, and handheld device captures should "
                "replace or extend it before platform release sign-off."
            ),
            "",
            "## Notes",
            "",
            *[f"- {note}" for note in report["notes"]],
            "",
        ]
    )
    return "\n".join(lines)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    for candidate in (resolved.parent, *resolved.parents):
        if (candidate / "TODO.md").exists():
            return str(resolved.relative_to(candidate))
    return str(resolved.relative_to(Path.cwd().resolve()))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
