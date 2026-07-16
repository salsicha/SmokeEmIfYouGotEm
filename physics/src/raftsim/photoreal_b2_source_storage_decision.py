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
B2_SOURCE_STORAGE_DECISION_SCHEMA = "raftsim.photoreal.b2_source_storage_decision.v1"


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


def _river_counts(tasks: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for task in tasks:
        river_id = task["river_id"]
        counts[river_id] = counts.get(river_id, 0) + 1
    return dict(sorted(counts.items()))


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
