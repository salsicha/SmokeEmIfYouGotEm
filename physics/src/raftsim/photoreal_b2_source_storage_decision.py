"""Build the B2 source-binary storage decision packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .photoreal_b2_source_acquisition_preflight import (
    B2_SOURCE_ACQUISITION_PREFLIGHT_RELATIVE_PATH,
    build_b2_source_acquisition_preflight,
)


B2_SOURCE_STORAGE_DECISION_RELATIVE_PATH = (
    "physics/data/real_world/photoreal_b2_source_storage_decision_packet.json"
)
B2_SOURCE_STORAGE_DECISION_RESULT_TEMPLATE_RELATIVE_PATH = (
    "physics/data/real_world/photoreal_b2_source_storage_decision_result_template.json"
)
B2_SOURCE_STORAGE_DECISION_VALIDATION_REPORT_RELATIVE_PATH = (
    "physics/data/real_world/photoreal_b2_source_storage_decision_validation_report.json"
)
B2_SOURCE_STORAGE_DECISION_SCHEMA = "raftsim.photoreal.b2_source_storage_decision.v1"
B2_SOURCE_STORAGE_DECISION_RESULT_TEMPLATE_SCHEMA = (
    "raftsim.photoreal.b2_source_storage_decision_result_template.v1"
)
B2_SOURCE_STORAGE_DECISION_VALIDATION_REPORT_SCHEMA = (
    "raftsim.photoreal.b2_source_storage_decision_validation_report.v1"
)

_LOCAL_ONLY_SCOPE = "cc0_source_binaries_local_only_hashes_and_reports_committed"
_COMMIT_ALL_SCOPE = "cc0_source_binaries_committed_after_storage_capacity"
_HYBRID_SCOPE = "small_cc0_source_binaries_committed_large_local_only"
_GITLAB_RESOLVED = "resolved_with_capacity"
_LOCAL_ONLY_GITLAB_STATE = "not_required_for_local_only"
_GENERATED_MAP_POLICY = "keep_versioning_generated_maps"


def build_b2_source_storage_decision() -> dict[str, Any]:
    """Build a fail-closed decision packet for B2 source-binary storage."""

    preflight = build_b2_source_acquisition_preflight()
    cc0_tasks = preflight["cc0_download_tasks"]
    river_counts = _river_counts(cc0_tasks)
    return {
        "schema": B2_SOURCE_STORAGE_DECISION_SCHEMA,
        "generated_on": "2026-07-16",
        "status": "owner_storage_policy_decision_required_downloads_remain_disabled",
        "source_preflight": B2_SOURCE_ACQUISITION_PREFLIGHT_RELATIVE_PATH,
        "current_operating_mode": {
            "mode": "local_only_until_owner_storage_decision",
            "downloads_allowed_now": False,
            "source_binaries_allowed_in_repo_now": False,
            "import_reports_allowed_in_repo_now": True,
            "hash_manifests_allowed_in_repo_now": True,
            "reason": (
                "The five-river B2 queue contains many third-party source bundles "
                "and the GitLab mirror is already failing LFS uploads because the "
                "project exceeds allocated storage."
            ),
        },
        "pending_scope": {
            "river_count": preflight["river_count"],
            "selection_manifest_count": preflight["selection_manifest_count"],
            "cc0_download_task_count": preflight["cc0_download_task_count"],
            "fab_local_only_slot_count": preflight["fab_local_only_slot_count"],
            "first_party_entry_count": preflight["first_party_entry_count"],
            "cc0_download_tasks_by_river": river_counts,
        },
        "decision_options": [
            _local_only_option(),
            _commit_all_cc0_option(),
            _hybrid_option(),
        ],
        "required_owner_decision": {
            "decision_id": "b2_cc0_source_binary_storage_policy",
            "must_choose_one_option_id": [
                "local_only_hash_report_public_repo",
                "commit_all_cc0_source_binaries_after_storage_capacity",
                "hybrid_commit_small_local_only_large",
            ],
            "required_fields": [
                "chosen_option_id",
                "decision_owner",
                "decision_date",
                "max_source_bundle_bytes_without_extra_approval",
                "gitlab_storage_resolution",
                "lfs_retention_policy",
                "rollback_policy",
            ],
            "blocks": [
                "executing any B2 CC0 source download task into a committed source root",
                "committing any B2 third-party source binary",
                "running promotion import reports that assume committed source binaries",
                "marking any B2 asset set as promotion-ready",
            ],
        },
        "guardrails": [
            "Fab Standard source binaries stay local-only regardless of the CC0 storage decision.",
            "First-party generated assets may be committed only with recipe, tool version, seed, and hash manifests.",
            "No B2 source binary can be committed while the GitLab mirror rejects LFS uploads for quota.",
            "No corridor substitution is allowed from local-only source binaries without committed hash and import reports.",
            "Promotion captures must cite the exact source policy used for every visible third-party asset.",
        ],
        "cc0_task_decision_requirements": [
            {
                "task_id": task["task_id"],
                "river_id": task["river_id"],
                "candidate_id": task["candidate_id"],
                "asset_need_id": task["asset_need_id"],
                "asset_url": task["asset_url"],
                "required_before_download": task["required_before_execute"],
                "required_before_commit": task["required_before_commit"],
            }
            for task in cc0_tasks
        ],
    }


def write_b2_source_storage_decision(repo_root: Path) -> Path:
    payload = build_b2_source_storage_decision()
    path = repo_root / B2_SOURCE_STORAGE_DECISION_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def build_b2_source_storage_decision_result_template() -> dict[str, Any]:
    """Build an empty owner decision result template for B2 storage policy."""

    packet = build_b2_source_storage_decision()
    return {
        "schema": B2_SOURCE_STORAGE_DECISION_RESULT_TEMPLATE_SCHEMA,
        "generated_on": "2026-07-16",
        "status": "empty_owner_storage_policy_result_downloads_remain_disabled",
        "production_promoted": False,
        "source_decision_packet": B2_SOURCE_STORAGE_DECISION_RELATIVE_PATH,
        "allowed_option_ids": packet["required_owner_decision"][
            "must_choose_one_option_id"
        ],
        "decision_result": {
            "chosen_option_id": "",
            "decision_owner": "",
            "decision_date": "",
            "max_source_bundle_bytes_without_extra_approval": None,
            "gitlab_storage_resolution": "",
            "lfs_retention_policy": "",
            "rollback_policy": "",
            "source_binary_commit_scope": "",
            "generated_map_versioning_policy": _GENERATED_MAP_POLICY,
            "fab_standard_policy": "local_only",
            "evidence": [],
            "notes": "",
        },
        "validation_contract": {
            "template_is_empty": True,
            "owner_must_choose_one_allowed_option": True,
            "generated_maps_remain_versioned": True,
            "generated_map_policy_does_not_authorize_third_party_source_binaries": True,
            "fab_standard_sources_remain_local_only": True,
            "gitlab_capacity_required_before_committing_any_cc0_source_binary": True,
            "validated_local_only_decision_allows_local_downloads_hashes_and_import_reports_only": True,
        },
        "promotion_gate": {
            "can_enable_local_cc0_downloads": False,
            "can_commit_cc0_source_binaries": False,
            "can_commit_hash_reports": False,
            "can_commit_import_reports": False,
            "can_run_local_isolated_imports": False,
            "can_mark_any_b2_asset_set_promotion_ready": False,
        },
    }


def write_b2_source_storage_decision_result_template(repo_root: Path) -> Path:
    payload = build_b2_source_storage_decision_result_template()
    path = repo_root / B2_SOURCE_STORAGE_DECISION_RESULT_TEMPLATE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def build_b2_source_storage_decision_validation_report(
    result_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate an owner storage-policy result without promoting B2 assets."""

    packet = build_b2_source_storage_decision()
    payload = (
        result_payload
        if result_payload is not None
        else build_b2_source_storage_decision_result_template()
    )
    decision = payload["decision_result"]
    errors = _decision_errors(decision, packet)
    valid = not errors
    chosen_option_id = decision.get("chosen_option_id", "")
    commit_scope = decision.get("source_binary_commit_scope", "")
    can_commit_binaries = valid and commit_scope in {_COMMIT_ALL_SCOPE, _HYBRID_SCOPE}
    return {
        "schema": B2_SOURCE_STORAGE_DECISION_VALIDATION_REPORT_SCHEMA,
        "generated_on": "2026-07-16",
        "status": (
            "owner_storage_policy_result_valid_b2_source_execution_unblocked"
            if valid
            else "owner_storage_policy_result_incomplete_downloads_remain_disabled"
        ),
        "production_promoted": False,
        "source_decision_packet": B2_SOURCE_STORAGE_DECISION_RELATIVE_PATH,
        "source_result_template": B2_SOURCE_STORAGE_DECISION_RESULT_TEMPLATE_RELATIVE_PATH,
        "storage_decision_valid": valid,
        "validation_error_count": len(errors),
        "chosen_option_id": chosen_option_id,
        "errors": errors,
        "promotion_permissions": {
            "can_enable_local_cc0_downloads": valid,
            "can_commit_cc0_source_binaries": can_commit_binaries,
            "can_commit_hash_reports": valid,
            "can_commit_import_reports": valid,
            "can_run_local_isolated_imports": valid,
            "can_mark_any_b2_asset_set_promotion_ready": False,
            "can_promote_b2_from_storage_decision_alone": False,
        },
        "download_execution_policy": _download_execution_policy(decision, valid),
        "promotion_gate": {
            "can_skip_source_hash_report": False,
            "can_skip_import_capture_review": False,
            "can_skip_per_river_promotion_decision": False,
            "next_after_valid_result": [
                "regenerate_b2_source_acquisition_execution_plan",
                "run allowed local or LFS-backed CC0 downloads one asset at a time",
                "populate source hash report with exact files and SHA-256 values",
                "run isolated Unreal import/capture review before per-river promotion",
            ],
        },
    }


def write_b2_source_storage_decision_validation_report(repo_root: Path) -> Path:
    payload = build_b2_source_storage_decision_validation_report()
    path = repo_root / B2_SOURCE_STORAGE_DECISION_VALIDATION_REPORT_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _river_counts(tasks: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for task in tasks:
        river_id = task["river_id"]
        counts[river_id] = counts.get(river_id, 0) + 1
    return dict(sorted(counts.items()))


def _decision_errors(
    decision: dict[str, Any],
    packet: dict[str, Any],
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    allowed_options = set(packet["required_owner_decision"]["must_choose_one_option_id"])
    chosen_option = decision.get("chosen_option_id", "")
    if chosen_option not in allowed_options:
        errors.append(_error("chosen_option_id", "chosen_option_not_allowed_or_missing"))
    for field in (
        "decision_owner",
        "decision_date",
        "gitlab_storage_resolution",
        "lfs_retention_policy",
        "rollback_policy",
        "source_binary_commit_scope",
    ):
        if not decision.get(field):
            errors.append(_error(field, "required_field_empty"))
    max_bytes = decision.get("max_source_bundle_bytes_without_extra_approval")
    if not isinstance(max_bytes, int) or max_bytes < 0:
        errors.append(
            _error(
                "max_source_bundle_bytes_without_extra_approval",
                "max_source_bundle_bytes_must_be_nonnegative_integer",
            )
        )
    if decision.get("generated_map_versioning_policy") != _GENERATED_MAP_POLICY:
        errors.append(
            _error(
                "generated_map_versioning_policy",
                "generated_maps_must_remain_versioned",
            )
        )
    if decision.get("fab_standard_policy") != "local_only":
        errors.append(_error("fab_standard_policy", "fab_standard_must_remain_local_only"))
    if not decision.get("evidence"):
        errors.append(_error("evidence", "decision_evidence_missing"))
    _scope_errors(decision, chosen_option, errors)
    return errors


def _scope_errors(
    decision: dict[str, Any],
    chosen_option: str,
    errors: list[dict[str, str]],
) -> None:
    scope = decision.get("source_binary_commit_scope", "")
    gitlab = decision.get("gitlab_storage_resolution", "")
    if chosen_option == "local_only_hash_report_public_repo":
        if scope != _LOCAL_ONLY_SCOPE:
            errors.append(_error("source_binary_commit_scope", "local_only_scope_required"))
        if gitlab != _LOCAL_ONLY_GITLAB_STATE:
            errors.append(
                _error("gitlab_storage_resolution", "local_only_gitlab_state_required")
            )
    elif chosen_option == "commit_all_cc0_source_binaries_after_storage_capacity":
        if scope != _COMMIT_ALL_SCOPE:
            errors.append(_error("source_binary_commit_scope", "commit_all_scope_required"))
        if gitlab != _GITLAB_RESOLVED:
            errors.append(
                _error(
                    "gitlab_storage_resolution",
                    "gitlab_capacity_must_be_resolved_before_committing_sources",
                )
            )
    elif chosen_option == "hybrid_commit_small_local_only_large":
        if scope != _HYBRID_SCOPE:
            errors.append(_error("source_binary_commit_scope", "hybrid_scope_required"))
        if gitlab != _GITLAB_RESOLVED:
            errors.append(
                _error(
                    "gitlab_storage_resolution",
                    "gitlab_capacity_must_be_resolved_before_committing_sources",
                )
            )
        if decision.get("max_source_bundle_bytes_without_extra_approval") == 0:
            errors.append(
                _error(
                    "max_source_bundle_bytes_without_extra_approval",
                    "hybrid_threshold_must_be_positive",
                )
            )


def _download_execution_policy(decision: dict[str, Any], valid: bool) -> dict[str, Any]:
    if not valid:
        return {
            "downloads_allowed_now": False,
            "source_binary_commits_allowed_now": False,
            "reason": "storage decision result is incomplete or inconsistent",
        }
    scope = decision["source_binary_commit_scope"]
    return {
        "downloads_allowed_now": True,
        "source_binary_commits_allowed_now": scope in {_COMMIT_ALL_SCOPE, _HYBRID_SCOPE},
        "source_binary_commit_scope": scope,
        "generated_map_versioning_policy": decision["generated_map_versioning_policy"],
        "fab_standard_policy": decision["fab_standard_policy"],
    }


def _error(field: str, reason: str) -> dict[str, str]:
    return {"field": field, "reason": reason}


def _local_only_option() -> dict[str, Any]:
    return {
        "option_id": "local_only_hash_report_public_repo",
        "label": "Keep CC0 source binaries local-only; commit hashes, import reports, and derived review captures.",
        "recommended_until_gitlab_quota_resolved": True,
        "source_binaries_committed": False,
        "hash_reports_committed": True,
        "import_reports_committed": True,
        "pros": [
            "Avoids adding large source bundles while the mirror is over quota.",
            "Still preserves provenance, exact file hashes, and importer reproducibility.",
            "Allows isolated local review to continue one asset at a time.",
        ],
        "cons": [
            "Future collaborators must reacquire exact source bundles from recorded URLs.",
            "Offline rebuilds depend on local source-root retention.",
            "Long-term archival is weaker than committed source bundles.",
        ],
    }


def _commit_all_cc0_option() -> dict[str, Any]:
    return {
        "option_id": "commit_all_cc0_source_binaries_after_storage_capacity",
        "label": "Commit approved CC0 source binaries through Git LFS after storage capacity is fixed.",
        "recommended_until_gitlab_quota_resolved": False,
        "source_binaries_committed": True,
        "hash_reports_committed": True,
        "import_reports_committed": True,
        "pros": [
            "Strongest reproducibility and archival story for CC0 inputs.",
            "Collaborators can rebuild from the repository without external reacquisition.",
            "Matches the owner preference to keep generated maps versioned, if extended to CC0 source assets.",
        ],
        "cons": [
            "Cannot proceed while GitLab LFS upload is failing for storage quota.",
            "High storage and clone/cache cost for geometry-heavy asset bundles.",
            "Requires explicit LFS retention and pruning policy before scale-out.",
        ],
    }


def _hybrid_option() -> dict[str, Any]:
    return {
        "option_id": "hybrid_commit_small_local_only_large",
        "label": "Commit small CC0 texture/source bundles; keep large geometry bundles local-only with hashes.",
        "recommended_until_gitlab_quota_resolved": False,
        "source_binaries_committed": "size_threshold_dependent",
        "hash_reports_committed": True,
        "import_reports_committed": True,
        "pros": [
            "Balances reproducibility against storage pressure.",
            "Can preserve small texture/material sources while avoiding huge model bundles.",
            "Creates a clear threshold for future asset-intake automation.",
        ],
        "cons": [
            "Requires a bright-line byte threshold and per-asset classification.",
            "Rebuild behavior differs by asset size class.",
            "Still cannot commit any LFS source binaries until the GitLab quota is resolved.",
        ],
    }
