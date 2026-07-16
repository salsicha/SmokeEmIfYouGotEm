import json
from pathlib import Path

from raftsim.photoreal_b2_source_acquisition_preflight import (
    build_b2_source_acquisition_preflight,
)
from raftsim.photoreal_b2_source_storage_decision import (
    B2_SOURCE_STORAGE_DECISION_RELATIVE_PATH,
    B2_SOURCE_STORAGE_DECISION_SCHEMA,
    build_b2_source_storage_decision,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_decision_packet() -> dict:
    return json.loads(
        (REPO_ROOT / B2_SOURCE_STORAGE_DECISION_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
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
