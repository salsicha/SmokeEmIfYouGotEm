"""Fail-closed compliant-reference runner export bundle for D6 fixtures."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .flexible_raft_d6 import (
    D6_COMPLIANT_MEASURED_RESULTS_MERGE_REPORT_RELATIVE_PATH,
    D6_COMPLIANT_MEASURED_RESULTS_SIDECAR_SCHEMA,
    REQUIRED_D6_FIXTURE_IDS,
    build_flexible_raft_d6_compliant_measured_results_merge_report,
    build_flexible_raft_d6_compliant_measured_results_sidecar_template,
)
from .flexible_raft_d6_execution_packet import (
    D6_EXECUTION_PACKET_RELATIVE_PATH,
    build_flexible_raft_d6_execution_packet,
)


D6_COMPLIANT_RUNNER_SIDECAR_RELATIVE_PATH = (
    "physics/reports/d6/compliant/flexible_raft_d6_compliant_measured_results.json"
)
D6_COMPLIANT_RUNNER_SUMMARY_RELATIVE_PATH = "physics/reports/d6/compliant/summary.json"
D6_COMPLIANT_RUNNER_REPLAY_DIR_RELATIVE_PATH = "physics/reports/d6/compliant/replays"
D6_COMPLIANT_RUNNER_SUMMARY_SCHEMA = (
    "raftsim.flexible_raft.d6_compliant_runner_summary.v1"
)
_COMPLIANT_TARGET_ID = "project_chrono_or_reviewed_compliant_model"


def build_flexible_raft_d6_compliant_runner_sidecar() -> dict[str, Any]:
    """Build the committed compliant-reference runner output placeholder."""

    sidecar = deepcopy(
        build_flexible_raft_d6_compliant_measured_results_sidecar_template()
    )
    sidecar.update(
        {
            "status": "compliant_runner_output_pending_no_measurements_recorded",
            "filled_result_count": 0,
            "source_automation_summary_path": D6_COMPLIANT_RUNNER_SUMMARY_RELATIVE_PATH,
            "source_runner_output_path": D6_COMPLIANT_RUNNER_SIDECAR_RELATIVE_PATH,
            "runner_output_state": (
                "pending_real_project_chrono_or_reviewed_compliant_measurements"
            ),
        }
    )
    sidecar["promotion_gate"] = {
        "may_mark_d6_complete": False,
        "may_drive_runtime_gameplay": False,
        "may_merge_into_measured_results_template": False,
        "reason": (
            "This is the committed Project Chrono/reviewed-compliant runner "
            "output placeholder. Every fixture remains not_measured until an "
            "external compliant runner writes real metric values, source "
            "reports, engine version, and 64-hex telemetry hashes."
        ),
    }
    return sidecar


def build_flexible_raft_d6_compliant_runner_summary(
    sidecar_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the fail-closed summary for compliant-reference output paths."""

    execution_packet = build_flexible_raft_d6_execution_packet()
    sidecar = sidecar_payload or build_flexible_raft_d6_compliant_runner_sidecar()
    merge_report = build_flexible_raft_d6_compliant_measured_results_merge_report(
        sidecar
    )
    results = sidecar.get("results") if isinstance(sidecar.get("results"), dict) else {}
    fixture_validity = {
        report["fixture_id"]: report["valid"]
        for report in merge_report["fixture_reports"]
    }
    jobs = []
    for job in execution_packet["execution_jobs"]:
        if job["target_id"] != _COMPLIANT_TARGET_ID:
            continue
        fixture_id = job["fixture_id"]
        record = results.get(fixture_id, {})
        metrics = record.get("metrics") if isinstance(record, dict) else {}
        metric_count = (
            len(_flatten_numeric_metrics(metrics)) if isinstance(metrics, dict) else 0
        )
        ready_for_merge = bool(fixture_validity.get(fixture_id, False))
        jobs.append(
            {
                "fixture_id": fixture_id,
                "job_id": job["job_id"],
                "comparison_mode": job["comparison_mode"],
                "metric_deltas_are_failures": job["metric_deltas_are_failures"],
                "expected_result_record_path": job["expected_result_template_path"],
                "required_metric_count": len(job["required_metric_paths"]),
                "required_metric_paths": list(job["required_metric_paths"]),
                "required_d5_replay_channels": list(job["required_d5_replay_channels"]),
                "recorded_metric_count": metric_count,
                "sidecar_result_status": (
                    record.get("status", "missing_result_record")
                    if isinstance(record, dict)
                    else "missing_result_record"
                ),
                "ready_for_sidecar_merge": ready_for_merge,
                "blocking_reason": (
                    "manual_review_pending"
                    if ready_for_merge
                    else "real_compliant_reference_measurement_not_recorded"
                ),
            }
        )

    return {
        "schema": D6_COMPLIANT_RUNNER_SUMMARY_SCHEMA,
        "generated_on": "2026-07-17",
        "status": (
            "compliant_measurements_recorded_manual_review_pending"
            if merge_report["can_merge"]
            else "compliant_runner_output_pending_no_measurements_recorded"
        ),
        "d6_complete": False,
        "production_promoted": False,
        "runtime": sidecar.get("runtime", "ProjectChronoOrReviewedCompliantReference"),
        "runtime_id": sidecar.get("runtime_id"),
        "engine_version": sidecar.get("engine_version"),
        "source_execution_packet_path": D6_EXECUTION_PACKET_RELATIVE_PATH,
        "source_sidecar_schema": sidecar.get("schema"),
        "runner_output_sidecar": D6_COMPLIANT_RUNNER_SIDECAR_RELATIVE_PATH,
        "runner_replay_dir": D6_COMPLIANT_RUNNER_REPLAY_DIR_RELATIVE_PATH,
        "runner_summary": D6_COMPLIANT_RUNNER_SUMMARY_RELATIVE_PATH,
        "merge_report_path": D6_COMPLIANT_MEASURED_RESULTS_MERGE_REPORT_RELATIVE_PATH,
        "fixture_count": len(REQUIRED_D6_FIXTURE_IDS),
        "filled_fixture_count": merge_report["filled_fixture_count"],
        "invalid_fixture_count": merge_report["invalid_fixture_count"],
        "missing_fixture_count": merge_report["missing_fixture_count"],
        "can_merge_sidecar": merge_report["can_merge"],
        "expected_sidecar_schema": D6_COMPLIANT_MEASURED_RESULTS_SIDECAR_SCHEMA,
        "required_fixture_ids": list(REQUIRED_D6_FIXTURE_IDS),
        "jobs": jobs,
        "promotion_gate": {
            "may_mark_d6_complete": False,
            "may_drive_runtime_gameplay": False,
            "may_merge_into_measured_results_template": merge_report["can_merge"],
            "reason": (
                "All seven compliant fixture records are measured and mergeable; "
                "D6 remains fail-closed until the two-target comparison and manual "
                "physics/integration/replay/guide-safety review are complete."
                if merge_report["can_merge"]
                else "The compliant-reference output paths are schema-compatible, "
                "but all seven fixtures need real compliant measurements before merge."
            ),
        },
    }


def write_flexible_raft_d6_compliant_runner_export(
    repo_root: Path,
) -> tuple[Path, Path]:
    """Write placeholders without replacing genuine compliant measurements."""

    sidecar_path = repo_root / D6_COMPLIANT_RUNNER_SIDECAR_RELATIVE_PATH
    summary_path = repo_root / D6_COMPLIANT_RUNNER_SUMMARY_RELATIVE_PATH
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    (repo_root / D6_COMPLIANT_RUNNER_REPLAY_DIR_RELATIVE_PATH).mkdir(
        parents=True,
        exist_ok=True,
    )
    if sidecar_path.is_file():
        existing = json.loads(sidecar_path.read_text(encoding="utf-8"))
        merge_report = build_flexible_raft_d6_compliant_measured_results_merge_report(
            existing
        )
        if merge_report["can_merge"]:
            _write_json(
                summary_path,
                build_flexible_raft_d6_compliant_runner_summary(existing),
            )
            return sidecar_path, summary_path

    sidecar = build_flexible_raft_d6_compliant_runner_sidecar()
    summary = build_flexible_raft_d6_compliant_runner_summary(sidecar)
    _write_json(sidecar_path, sidecar)
    _write_json(summary_path, summary)
    return sidecar_path, summary_path


def write_flexible_raft_d6_compliant_runner_sidecar_payload(
    output_path: Path,
    payload: dict[str, Any],
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output_path, payload)
    return output_path


def write_flexible_raft_d6_compliant_runner_summary_payload(
    output_path: Path,
    payload: dict[str, Any],
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output_path, payload)
    return output_path


def _flatten_numeric_metrics(
    payload: dict[str, Any],
    *,
    prefix: str = "",
) -> dict[str, float]:
    flattened: dict[str, float] = {}
    for key, value in payload.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            flattened[path] = float(value)
        elif isinstance(value, dict):
            flattened.update(_flatten_numeric_metrics(value, prefix=path))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                item_path = f"{path}[{index}]"
                if isinstance(item, bool):
                    continue
                if isinstance(item, (int, float)):
                    flattened[item_path] = float(item)
                elif isinstance(item, dict):
                    flattened.update(_flatten_numeric_metrics(item, prefix=item_path))
    return flattened


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
