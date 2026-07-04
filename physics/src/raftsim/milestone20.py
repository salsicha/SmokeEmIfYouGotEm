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


@dataclass(frozen=True, slots=True)
class Milestone20ReportSetLock:
    """Generated lock file and human-readable summary."""

    report: dict[str, Any]
    markdown: str


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


def _artifact_entries(root: Path, paths: tuple[str, ...], *, group: str) -> list[dict[str, Any]]:
    return [_artifact_entry(root, path, group=group) for path in paths]


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
