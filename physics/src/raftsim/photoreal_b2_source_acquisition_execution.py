"""Build the B2 photoreal source-acquisition execution plan."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .photoreal_b2_source_acquisition_preflight import (
    B2_SOURCE_ACQUISITION_PREFLIGHT_RELATIVE_PATH,
    build_b2_source_acquisition_preflight,
)
from .photoreal_b2_source_storage_decision import (
    B2_SOURCE_STORAGE_DECISION_VALIDATION_REPORT_RELATIVE_PATH,
    build_b2_source_storage_decision_validation_report,
)


B2_SOURCE_ACQUISITION_EXECUTION_PLAN_RELATIVE_PATH = (
    "physics/data/real_world/photoreal_b2_source_acquisition_execution_plan.json"
)
B2_SOURCE_ACQUISITION_EXECUTION_PLAN_SCHEMA = (
    "raftsim.photoreal.b2_source_acquisition_execution_plan.v1"
)


def build_b2_source_acquisition_execution_plan(
    storage_decision_result_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a storage-policy-aware plan without downloading source assets."""

    preflight = build_b2_source_acquisition_preflight()
    storage_report = build_b2_source_storage_decision_validation_report(
        storage_decision_result_payload
    )
    storage_valid = storage_report["storage_decision_valid"]
    local_downloads_allowed = storage_report["promotion_permissions"][
        "can_enable_local_cc0_downloads"
    ]
    source_binary_commits_allowed = storage_report["promotion_permissions"][
        "can_commit_cc0_source_binaries"
    ]
    tasks = [
        _execution_task(
            task,
            storage_valid,
            local_downloads_allowed,
            source_binary_commits_allowed,
        )
        for task in preflight["cc0_download_tasks"]
    ]
    executable_task_count = sum(1 for task in tasks if task["execution_allowed_now"])
    return {
        "schema": B2_SOURCE_ACQUISITION_EXECUTION_PLAN_SCHEMA,
        "generated_on": "2026-07-16",
        "status": (
            "b2_source_acquisition_policy_valid_per_asset_source_selection_required"
            if storage_valid
            else "b2_source_acquisition_execution_blocked_missing_storage_decision"
        ),
        "production_promoted": False,
        "source_preflight": B2_SOURCE_ACQUISITION_PREFLIGHT_RELATIVE_PATH,
        "source_storage_validation_report": (
            B2_SOURCE_STORAGE_DECISION_VALIDATION_REPORT_RELATIVE_PATH
        ),
        "storage_decision": {
            "storage_decision_valid": storage_valid,
            "chosen_option_id": storage_report["chosen_option_id"],
            "validation_error_count": storage_report["validation_error_count"],
            "local_cc0_downloads_allowed_by_policy": local_downloads_allowed,
            "cc0_source_binary_commits_allowed_by_policy": source_binary_commits_allowed,
            "download_execution_policy": storage_report["download_execution_policy"],
            "errors": storage_report["errors"],
        },
        "summary": {
            "cc0_task_count": len(tasks),
            "local_download_policy_allowed_count": sum(
                1 for task in tasks if task["local_download_allowed_by_storage_policy"]
            ),
            "source_binary_commit_policy_allowed_count": sum(
                1
                for task in tasks
                if task["source_binary_commit_allowed_by_storage_policy"]
            ),
            "per_asset_source_selection_complete_count": sum(
                1 for task in tasks if task["per_asset_source_selection_complete"]
            ),
            "executable_task_count": executable_task_count,
            "blocked_task_count": len(tasks) - executable_task_count,
        },
        "acquisition_tasks": tasks,
        "execution_gate": {
            "downloads_allowed_now": executable_task_count > 0,
            "download_command_emitted": False,
            "source_binary_commits_allowed_now": False,
            "hash_reports_allowed_now": storage_valid,
            "import_reports_allowed_now": storage_valid,
            "requires_valid_storage_decision": not storage_valid,
            "requires_per_asset_source_selection": True,
            "requires_source_hash_sidecar": True,
            "requires_import_capture_review_after_download": True,
            "blocking_reasons": _execution_gate_blockers(storage_valid),
        },
        "promotion_gate": {
            "can_mark_any_b2_asset_set_promotion_ready": False,
            "can_substitute_corridor_assets_from_execution_plan": False,
            "can_skip_source_hash_report": False,
            "can_skip_import_capture_review": False,
        },
    }


def write_b2_source_acquisition_execution_plan(repo_root: Path) -> Path:
    payload = build_b2_source_acquisition_execution_plan()
    path = repo_root / B2_SOURCE_ACQUISITION_EXECUTION_PLAN_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _execution_task(
    task: dict[str, Any],
    storage_valid: bool,
    local_downloads_allowed: bool,
    source_binary_commits_allowed: bool,
) -> dict[str, Any]:
    remaining = _remaining_requirements(storage_valid)
    return {
        "execution_task_id": task["task_id"].replace(
            "cc0_source_download_preflight",
            "cc0_source_acquisition_execution",
        ),
        "source_preflight_task_id": task["task_id"],
        "river_id": task["river_id"],
        "display_name": task["display_name"],
        "selection_manifest": task["selection_manifest"],
        "candidate_id": task["candidate_id"],
        "asset_need_id": task["asset_need_id"],
        "asset_url": task["asset_url"],
        "license_class": task["license_class"],
        "repo_binary_policy": task["repo_binary_policy"],
        "planned_source_root_env": task["planned_source_root_env"],
        "storage_decision_valid": storage_valid,
        "local_download_allowed_by_storage_policy": local_downloads_allowed,
        "source_binary_commit_allowed_by_storage_policy": source_binary_commits_allowed,
        "per_asset_source_selection_complete": False,
        "source_file_list_recorded": False,
        "expected_byte_size_recorded": False,
        "source_hash_sidecar_required": True,
        "import_capture_review_required": True,
        "execution_allowed_now": False,
        "required_before_execute": remaining,
        "blocked_reason": (
            "Storage decision is incomplete or inconsistent."
            if not storage_valid
            else "Per-asset source resolution, file list, expected byte size, target source root, and hash sidecar evidence are not recorded."
        ),
    }


def _remaining_requirements(storage_valid: bool) -> list[str]:
    requirements = [
        "choose exact source resolution and file formats",
        "record source file list and expected byte size",
        "record target reviewed source root outside the public repo when local-only",
        "record license snapshot URL and retrieval date",
        "populate source-hash sidecar after download",
    ]
    if not storage_valid:
        return ["record valid B2 source-binary storage decision result", *requirements]
    return requirements


def _execution_gate_blockers(storage_valid: bool) -> list[str]:
    blockers = [
        "No per-asset exact source file selections, expected byte sizes, source roots, or retrieval dates are recorded.",
        "No source-hash sidecar evidence has been merged for the selected files.",
        "No isolated Unreal import/capture review has been attached for any acquired source.",
    ]
    if not storage_valid:
        return ["The B2 source-binary storage decision result is not valid.", *blockers]
    return blockers
