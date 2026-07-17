"""Execution packet for D6 external-engine flexible raft measurements."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .flexible_raft_d6 import (
    D6_BEHAVIORAL_SUITE_RELATIVE_PATH,
    D6_CHAOS_MEASURED_RESULTS_MERGE_REPORT_RELATIVE_PATH,
    D6_CHAOS_MEASURED_RESULTS_SIDECAR_TEMPLATE_RELATIVE_PATH,
    D6_COMPLIANT_MEASURED_RESULTS_MERGE_REPORT_RELATIVE_PATH,
    D6_COMPLIANT_MEASURED_RESULTS_SIDECAR_TEMPLATE_RELATIVE_PATH,
    D6_COMPARISON_REPORT_RELATIVE_PATH,
    D6_FIXTURE_INPUT_PACKAGE_RELATIVE_PATH,
    D6_MEASURED_RESULTS_TEMPLATE_RELATIVE_PATH,
    D6_MEASUREMENT_MANIFEST_RELATIVE_PATH,
    D6_TARGET_POLICIES,
    build_flexible_raft_d6_comparison_report,
    build_flexible_raft_d6_fixture_input_package,
    build_flexible_raft_d6_measurement_manifest,
)
from .scenario2_5d import RaftParameters2_5D


D6_EXECUTION_PACKET_RELATIVE_PATH = (
    "physics/data/calibration/flexible_raft_d6_execution_packet.json"
)
D6_EXECUTION_PACKET_SCHEMA = "raftsim.flexible_raft.d6_external_engine_execution_packet.v1"


def build_flexible_raft_d6_execution_packet(
    parameters: RaftParameters2_5D | None = None,
) -> dict[str, Any]:
    """Build the fail-closed execution packet for external D6 engine runs."""

    manifest = build_flexible_raft_d6_measurement_manifest(parameters)
    fixture_package = build_flexible_raft_d6_fixture_input_package(parameters)
    report = build_flexible_raft_d6_comparison_report(parameters=parameters)
    target_statuses = _target_status_lookup(report)
    jobs = [
        _execution_job(task, target_statuses[(task["target_id"], task["fixture_id"])])
        for task in manifest["tasks"]
    ]
    adapter_groups = [
        _adapter_group(target_id, jobs)
        for target_id in manifest["required_targets"]
    ]
    pending_jobs = [
        job
        for job in jobs
        if job["current_comparison_report_state"]["status"]
        == "missing_measured_result"
    ]
    return {
        "schema": D6_EXECUTION_PACKET_SCHEMA,
        "generated_on": "2026-07-16",
        "status": "external_engine_execution_packet_ready_measurements_missing",
        "d6_complete": False,
        "production_promoted": False,
        "source_artifacts": {
            "behavioral_suite": D6_BEHAVIORAL_SUITE_RELATIVE_PATH,
            "measurement_manifest": D6_MEASUREMENT_MANIFEST_RELATIVE_PATH,
            "fixture_input_package": D6_FIXTURE_INPUT_PACKAGE_RELATIVE_PATH,
            "measured_results_template": D6_MEASURED_RESULTS_TEMPLATE_RELATIVE_PATH,
            "compliant_measured_results_sidecar_template": (
                D6_COMPLIANT_MEASURED_RESULTS_SIDECAR_TEMPLATE_RELATIVE_PATH
            ),
            "compliant_measured_results_merge_report": (
                D6_COMPLIANT_MEASURED_RESULTS_MERGE_REPORT_RELATIVE_PATH
            ),
            "chaos_measured_results_sidecar_template": (
                D6_CHAOS_MEASURED_RESULTS_SIDECAR_TEMPLATE_RELATIVE_PATH
            ),
            "chaos_measured_results_merge_report": (
                D6_CHAOS_MEASURED_RESULTS_MERGE_REPORT_RELATIVE_PATH
            ),
            "comparison_report": D6_COMPARISON_REPORT_RELATIVE_PATH,
        },
        "summary": {
            "fixture_count": manifest["fixture_count"],
            "target_count": manifest["target_count"],
            "execution_job_count": len(jobs),
            "pending_external_job_count": len(pending_jobs),
            "committed_report_missing_target_count": report["missing_target_count"],
            "all_measurements_present": report["all_measurements_present"],
            "comparison_passed": report["comparison_passed"],
            "python_only_can_satisfy_d6": False,
            "can_promote_d6_now": False,
        },
        "local_preparation_checks": {
            "can_generate_fixture_inputs": True,
            "can_generate_empty_measured_results_template": True,
            "can_generate_empty_target_sidecar_templates": True,
            "can_validate_target_sidecars_before_merge": True,
            "can_regenerate_pending_report": True,
            "can_run_external_measurement_gate_with_python_only": False,
            "reason": (
                "The D1-D5 Python reference is the comparison source, not an "
                "external measured engine result. D6 needs independent measured "
                "outputs from a reviewed compliant runner and Unreal Chaos."
            ),
        },
        "adapter_groups": adapter_groups,
        "execution_jobs": jobs,
        "post_measurement_workflow": [
            {
                "step": "run_external_engine_jobs",
                "required_job_count": len(jobs),
                "allowed_to_skip_jobs": False,
            },
            {
                "step": "populate_target_sidecars",
                "sidecar_templates": {
                    "project_chrono_or_reviewed_compliant_model": (
                        D6_COMPLIANT_MEASURED_RESULTS_SIDECAR_TEMPLATE_RELATIVE_PATH
                    ),
                    "unreal_chaos_rigid_baseline": (
                        D6_CHAOS_MEASURED_RESULTS_SIDECAR_TEMPLATE_RELATIVE_PATH
                    ),
                },
                "required_fixture_count_per_sidecar": manifest["fixture_count"],
                "allowed_to_hand_edit_standard_template_before_sidecar_validation": False,
            },
            {
                "step": "validate_and_merge_target_sidecars",
                "commands": {
                    "project_chrono_or_reviewed_compliant_model": (
                        "uv run --no-sync python "
                        "physics/src/raftsim/examples/"
                        "merge_flexible_raft_d6_compliant_measured_results.py "
                        "--compliant-sidecar <compliant-sidecar.json> "
                        "--output <merged-measured-results.json> "
                        "--report <compliant-merge-report.json>"
                    ),
                    "unreal_chaos_rigid_baseline": (
                        "uv run --no-sync python "
                        "physics/src/raftsim/examples/"
                        "merge_flexible_raft_d6_chaos_measured_results.py "
                        "--chaos-sidecar <chaos-sidecar.json> "
                        "--base-measured-results <merged-measured-results.json> "
                        "--output <merged-measured-results.json> "
                        "--report <chaos-merge-report.json>"
                    ),
                },
                "merge_reports": {
                    "project_chrono_or_reviewed_compliant_model": (
                        D6_COMPLIANT_MEASURED_RESULTS_MERGE_REPORT_RELATIVE_PATH
                    ),
                    "unreal_chaos_rigid_baseline": (
                        D6_CHAOS_MEASURED_RESULTS_MERGE_REPORT_RELATIVE_PATH
                    ),
                },
            },
            {
                "step": "populate_measured_results_template",
                "target_template": D6_MEASURED_RESULTS_TEMPLATE_RELATIVE_PATH,
                "required_fields": [
                    "source_report",
                    "telemetry_sha256",
                    "engine_version",
                    "metrics",
                ],
            },
            {
                "step": "regenerate_comparison_report",
                "command": (
                    "uv run --no-sync python "
                    "physics/src/raftsim/examples/generate_flexible_raft_d6_comparison_report.py "
                    "--measured-results <populated-measured-results.json> "
                    "--output <review-report.json>"
                ),
                "must_not_overwrite_committed_pending_report_until_reviewed": True,
            },
            {
                "step": "manual_review_and_promotion_decision",
                "required_reviews": [
                    "physics",
                    "Unreal integration",
                    "deterministic replay",
                    "guide/safety gameplay",
                ],
                "may_mark_d6_complete_before_review": False,
            },
        ],
        "blocked_actions_until_jobs_pass": [
            "marking D6 complete",
            "using flexible tube deformation for scoring-critical gameplay",
            "declaring Project Chrono/reviewed-compliant parity",
            "declaring Unreal Chaos rigid-baseline agreement",
            "re-approving rapid pin, flip, wrap, or rescue outcomes from D6 alone",
        ],
        "promotion_gate": {
            "may_mark_d6_complete": False,
            "may_drive_runtime_gameplay": False,
            "requires_all_jobs_present": True,
            "requires_comparison_report_review": True,
            "fixture_input_package_status": fixture_package["status"],
            "reason": (
                "This packet only makes the external run queue executable and "
                "auditable. It does not provide the missing external measurements."
            ),
        },
    }


def write_flexible_raft_d6_execution_packet(repo_root: Path) -> Path:
    """Write the committed D6 external-engine execution packet."""

    payload = build_flexible_raft_d6_execution_packet()
    path = repo_root / D6_EXECUTION_PACKET_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _target_status_lookup(report: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    statuses: dict[tuple[str, str], dict[str, Any]] = {}
    for fixture in report["fixtures"]:
        for target in fixture["targets"]:
            statuses[(target["target_id"], fixture["fixture_id"])] = target
    return statuses


def _execution_job(
    task: dict[str, Any],
    target_status: dict[str, Any],
) -> dict[str, Any]:
    return {
        "job_id": task["task_id"],
        "target_id": task["target_id"],
        "fixture_id": task["fixture_id"],
        "status": "pending_external_engine_run",
        "comparison_mode": task["comparison_mode"],
        "metric_deltas_are_failures": task["metric_deltas_are_failures"],
        "fixture_input_package": D6_FIXTURE_INPUT_PACKAGE_RELATIVE_PATH,
        "expected_result_template_path": task["expected_result_template_path"],
        "source_fixture_objective": task["source_fixture_objective"],
        "required_metric_paths": task["required_metric_paths"],
        "required_metric_count": task["required_metric_count"],
        "required_d5_replay_channels": task["required_d5_replay_channels"],
        "required_evidence": {
            "source_report": {
                "required": True,
                "description": "Reviewed engine run report or external measurement artifact.",
            },
            "telemetry_sha256": {
                "required": True,
                "description": "64-character SHA-256 for the exported telemetry/replay payload.",
            },
            "engine_version": {
                "required": True,
                "description": "External engine build, runner commit, or reviewed model version.",
            },
            "metrics": {
                "required": True,
                "metric_paths": task["required_metric_paths"],
            },
        },
        "current_comparison_report_state": {
            "status": target_status["status"],
            "passed": target_status["passed"],
            "report_path": D6_COMPARISON_REPORT_RELATIVE_PATH,
        },
        "guardrails": {
            "may_substitute_python_reference": False,
            "may_promote_fixture": False,
            "may_ignore_missing_metric": False,
            "may_ignore_missing_provenance": False,
            "must_preserve_fixture_input_semantics": True,
        },
    }


def _adapter_group(target_id: str, jobs: list[dict[str, Any]]) -> dict[str, Any]:
    target_jobs = [job for job in jobs if job["target_id"] == target_id]
    policy = D6_TARGET_POLICIES[target_id]
    if target_id == "project_chrono_or_reviewed_compliant_model":
        runner_family = "reviewed_compliant_reference"
        acceptance = (
            "Every numeric metric must match the Python D1-D5 reference within "
            "the recorded D6 absolute/relative tolerance, with provenance complete."
        )
        sidecar_template = D6_COMPLIANT_MEASURED_RESULTS_SIDECAR_TEMPLATE_RELATIVE_PATH
        merge_report = D6_COMPLIANT_MEASURED_RESULTS_MERGE_REPORT_RELATIVE_PATH
        merge_command = (
            "uv run --no-sync python "
            "physics/src/raftsim/examples/"
            "merge_flexible_raft_d6_compliant_measured_results.py"
        )
    elif target_id == "unreal_chaos_rigid_baseline":
        runner_family = "unreal_chaos_rigid_baseline"
        acceptance = (
            "Every fixture must be measured and hash-recorded. Metric deltas are "
            "baseline evidence rather than compliant-reference failures."
        )
        sidecar_template = D6_CHAOS_MEASURED_RESULTS_SIDECAR_TEMPLATE_RELATIVE_PATH
        merge_report = D6_CHAOS_MEASURED_RESULTS_MERGE_REPORT_RELATIVE_PATH
        merge_command = (
            "uv run --no-sync python "
            "physics/src/raftsim/examples/"
            "merge_flexible_raft_d6_chaos_measured_results.py"
        )
    else:
        raise ValueError(f"Unsupported D6 target id: {target_id}")
    return {
        "target_id": target_id,
        "runner_family": runner_family,
        "job_count": len(target_jobs),
        "comparison_mode": policy["comparison_mode"],
        "metric_deltas_are_failures": policy["metric_deltas_are_failures"],
        "pending_job_count": sum(
            job["current_comparison_report_state"]["status"]
            == "missing_measured_result"
            for job in target_jobs
        ),
        "adapter_must_not_substitute_python_reference": True,
        "required_external_runner": True,
        "acceptance_summary": acceptance,
        "measured_results_sidecar_template": sidecar_template,
        "measured_results_merge_report": merge_report,
        "sidecar_merge_command": merge_command,
        "job_ids": [job["job_id"] for job in target_jobs],
    }
