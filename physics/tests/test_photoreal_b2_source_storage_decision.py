import json
from pathlib import Path

from raftsim.photoreal_b2_source_acquisition_preflight import (
    build_b2_source_acquisition_preflight,
)
from raftsim.photoreal_b2_source_storage_decision import (
    B2_SOURCE_STORAGE_DECISION_RELATIVE_PATH,
    B2_SOURCE_STORAGE_DECISION_RESULT_TEMPLATE_RELATIVE_PATH,
    B2_SOURCE_STORAGE_DECISION_RESULT_TEMPLATE_SCHEMA,
    B2_SOURCE_STORAGE_DECISION_SCHEMA,
    B2_SOURCE_STORAGE_DECISION_VALIDATION_REPORT_RELATIVE_PATH,
    B2_SOURCE_STORAGE_DECISION_VALIDATION_REPORT_SCHEMA,
    build_b2_source_storage_decision_result_template,
    build_b2_source_storage_decision_validation_report,
    build_b2_source_storage_decision,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_decision_packet() -> dict:
    return json.loads(
        (REPO_ROOT / B2_SOURCE_STORAGE_DECISION_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _load_result_template() -> dict:
    return json.loads(
        (REPO_ROOT / B2_SOURCE_STORAGE_DECISION_RESULT_TEMPLATE_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _load_validation_report() -> dict:
    return json.loads(
        (
            REPO_ROOT / B2_SOURCE_STORAGE_DECISION_VALIDATION_REPORT_RELATIVE_PATH
        ).read_text(encoding="utf-8")
    )


def test_b2_source_storage_decision_is_reproducible_and_fail_closed():
    generated = build_b2_source_storage_decision()
    committed = _load_decision_packet()

    assert generated == committed
    assert committed["schema"] == B2_SOURCE_STORAGE_DECISION_SCHEMA
    assert committed["status"] == (
        "owner_storage_policy_decision_required_downloads_remain_disabled"
    )
    mode = committed["current_operating_mode"]
    assert mode["mode"] == "local_only_until_owner_storage_decision"
    assert mode["downloads_allowed_now"] is False
    assert mode["source_binaries_allowed_in_repo_now"] is False
    assert mode["import_reports_allowed_in_repo_now"] is True
    assert mode["hash_manifests_allowed_in_repo_now"] is True
    assert "GitLab mirror is already failing LFS uploads" in mode["reason"]


def test_b2_source_storage_decision_options_are_explicit():
    packet = build_b2_source_storage_decision()
    options = {option["option_id"]: option for option in packet["decision_options"]}

    assert set(options) == {
        "local_only_hash_report_public_repo",
        "commit_all_cc0_source_binaries_after_storage_capacity",
        "hybrid_commit_small_local_only_large",
    }
    assert options["local_only_hash_report_public_repo"][
        "recommended_until_gitlab_quota_resolved"
    ] is True
    assert options["local_only_hash_report_public_repo"][
        "source_binaries_committed"
    ] is False
    assert options["commit_all_cc0_source_binaries_after_storage_capacity"][
        "source_binaries_committed"
    ] is True
    assert options["hybrid_commit_small_local_only_large"][
        "source_binaries_committed"
    ] == "size_threshold_dependent"


def test_b2_source_storage_decision_matches_preflight_counts():
    packet = build_b2_source_storage_decision()
    preflight = build_b2_source_acquisition_preflight()

    scope = packet["pending_scope"]
    assert scope["river_count"] == preflight["river_count"] == 5
    assert scope["selection_manifest_count"] == preflight["selection_manifest_count"]
    assert scope["cc0_download_task_count"] == preflight["cc0_download_task_count"] == 22
    assert scope["fab_local_only_slot_count"] == preflight["fab_local_only_slot_count"] == 16
    assert scope["first_party_entry_count"] == preflight["first_party_entry_count"] == 6
    assert sum(scope["cc0_download_tasks_by_river"].values()) == 22


def test_b2_source_storage_decision_covers_every_cc0_task():
    packet = build_b2_source_storage_decision()
    preflight = build_b2_source_acquisition_preflight()
    expected_task_ids = {task["task_id"] for task in preflight["cc0_download_tasks"]}
    decision_requirements = {
        task["task_id"]: task for task in packet["cc0_task_decision_requirements"]
    }

    assert set(decision_requirements) == expected_task_ids
    for task in decision_requirements.values():
        assert task["asset_url"].startswith("https://polyhaven.com/a/")
        assert "record owner storage approval for source binaries" in task[
            "required_before_download"
        ]
        assert "record SHA-256 hash for every source file" in task[
            "required_before_commit"
        ]


def test_b2_source_storage_decision_records_owner_fields_and_guardrails():
    packet = build_b2_source_storage_decision()
    decision = packet["required_owner_decision"]

    assert decision["decision_id"] == "b2_cc0_source_binary_storage_policy"
    assert "chosen_option_id" in decision["required_fields"]
    assert "gitlab_storage_resolution" in decision["required_fields"]
    assert "lfs_retention_policy" in decision["required_fields"]
    assert any("GitLab mirror rejects LFS uploads" in rule for rule in packet["guardrails"])
    assert any("Fab Standard source binaries stay local-only" in rule for rule in packet["guardrails"])


def test_b2_source_storage_decision_result_template_is_reproducible_and_empty():
    generated = build_b2_source_storage_decision_result_template()
    committed = _load_result_template()

    assert generated == committed
    assert committed["schema"] == B2_SOURCE_STORAGE_DECISION_RESULT_TEMPLATE_SCHEMA
    assert committed["status"] == (
        "empty_owner_storage_policy_result_downloads_remain_disabled"
    )
    result = committed["decision_result"]
    assert result["chosen_option_id"] == ""
    assert result["decision_owner"] == ""
    assert result["generated_map_versioning_policy"] == "keep_versioning_generated_maps"
    assert result["fab_standard_policy"] == "local_only"
    gate = committed["promotion_gate"]
    assert gate["can_enable_local_cc0_downloads"] is False
    assert gate["can_commit_cc0_source_binaries"] is False


def test_b2_source_storage_decision_validation_blocks_empty_result():
    generated = build_b2_source_storage_decision_validation_report()
    committed = _load_validation_report()

    assert generated == committed
    assert committed["schema"] == B2_SOURCE_STORAGE_DECISION_VALIDATION_REPORT_SCHEMA
    assert committed["status"] == (
        "owner_storage_policy_result_incomplete_downloads_remain_disabled"
    )
    assert committed["storage_decision_valid"] is False
    assert committed["validation_error_count"] >= 9
    reasons = {error["reason"] for error in committed["errors"]}
    assert {
        "chosen_option_not_allowed_or_missing",
        "required_field_empty",
        "max_source_bundle_bytes_must_be_nonnegative_integer",
        "decision_evidence_missing",
    }.issubset(reasons)
    permissions = committed["promotion_permissions"]
    assert permissions["can_enable_local_cc0_downloads"] is False
    assert permissions["can_commit_cc0_source_binaries"] is False
    assert permissions["can_mark_any_b2_asset_set_promotion_ready"] is False


def test_b2_source_storage_decision_validation_accepts_local_only_policy():
    report = build_b2_source_storage_decision_validation_report(
        _complete_local_only_result()
    )

    assert report["status"] == (
        "owner_storage_policy_result_valid_b2_source_execution_unblocked"
    )
    assert report["storage_decision_valid"] is True
    assert report["validation_error_count"] == 0
    permissions = report["promotion_permissions"]
    assert permissions["can_enable_local_cc0_downloads"] is True
    assert permissions["can_commit_cc0_source_binaries"] is False
    assert permissions["can_commit_hash_reports"] is True
    assert permissions["can_commit_import_reports"] is True
    assert permissions["can_run_local_isolated_imports"] is True
    assert permissions["can_promote_b2_from_storage_decision_alone"] is False
    policy = report["download_execution_policy"]
    assert policy["downloads_allowed_now"] is True
    assert policy["source_binary_commits_allowed_now"] is False
    assert policy["generated_map_versioning_policy"] == "keep_versioning_generated_maps"


def test_b2_source_storage_decision_validation_rejects_unresolved_commit_policy():
    payload = _complete_local_only_result()
    payload["decision_result"].update(
        {
            "chosen_option_id": "commit_all_cc0_source_binaries_after_storage_capacity",
            "source_binary_commit_scope": (
                "cc0_source_binaries_committed_after_storage_capacity"
            ),
            "gitlab_storage_resolution": "quota_still_failing",
        }
    )
    report = build_b2_source_storage_decision_validation_report(payload)

    assert report["storage_decision_valid"] is False
    assert {
        "field": "gitlab_storage_resolution",
        "reason": "gitlab_capacity_must_be_resolved_before_committing_sources",
    } in report["errors"]


def test_b2_source_storage_decision_validation_rejects_generated_map_policy_change():
    payload = _complete_local_only_result()
    payload["decision_result"]["generated_map_versioning_policy"] = "prune_generated_maps"
    report = build_b2_source_storage_decision_validation_report(payload)

    assert report["storage_decision_valid"] is False
    assert {
        "field": "generated_map_versioning_policy",
        "reason": "generated_maps_must_remain_versioned",
    } in report["errors"]


def _complete_local_only_result() -> dict:
    payload = build_b2_source_storage_decision_result_template()
    payload["decision_result"].update(
        {
            "chosen_option_id": "local_only_hash_report_public_repo",
            "decision_owner": "owner",
            "decision_date": "2026-07-16",
            "max_source_bundle_bytes_without_extra_approval": 0,
            "gitlab_storage_resolution": "not_required_for_local_only",
            "lfs_retention_policy": "no_third_party_source_binaries_committed",
            "rollback_policy": "delete local source root and regenerate hash reports",
            "source_binary_commit_scope": (
                "cc0_source_binaries_local_only_hashes_and_reports_committed"
            ),
            "generated_map_versioning_policy": "keep_versioning_generated_maps",
            "fab_standard_policy": "local_only",
            "evidence": ["review/b2_source_storage_owner_decision.md"],
            "notes": "synthetic complete test payload",
        }
    )
    return payload
