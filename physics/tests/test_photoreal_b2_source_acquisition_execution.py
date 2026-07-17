import json
from pathlib import Path

from raftsim.examples.generate_photoreal_b2_source_acquisition_execution import (
    main as generate_b2_source_acquisition_execution_main,
)
from raftsim.photoreal_b2_source_acquisition_execution import (
    B2_SOURCE_ACQUISITION_EXECUTION_PLAN_RELATIVE_PATH,
    B2_SOURCE_ACQUISITION_EXECUTION_PLAN_SCHEMA,
    build_b2_source_acquisition_execution_plan,
)
from raftsim.photoreal_b2_source_acquisition_preflight import (
    build_b2_source_acquisition_preflight,
)
from raftsim.photoreal_b2_source_storage_decision import (
    build_b2_source_storage_decision_result_template,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_execution_plan() -> dict:
    return json.loads(
        (REPO_ROOT / B2_SOURCE_ACQUISITION_EXECUTION_PLAN_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_b2_source_acquisition_execution_plan_is_reproducible_and_blocked():
    generated = build_b2_source_acquisition_execution_plan()
    committed = _load_execution_plan()

    assert generated == committed
    assert committed["schema"] == B2_SOURCE_ACQUISITION_EXECUTION_PLAN_SCHEMA
    assert committed["status"] == (
        "b2_source_acquisition_execution_blocked_missing_storage_decision"
    )
    assert committed["storage_decision"]["storage_decision_valid"] is False
    assert committed["summary"]["cc0_task_count"] == 22
    assert committed["summary"]["executable_task_count"] == 0
    assert committed["execution_gate"]["downloads_allowed_now"] is False
    assert committed["execution_gate"]["source_binary_commits_allowed_now"] is False
    assert committed["promotion_gate"]["can_mark_any_b2_asset_set_promotion_ready"] is False


def test_b2_source_acquisition_execution_plan_covers_preflight_cc0_tasks():
    plan = build_b2_source_acquisition_execution_plan()
    preflight = build_b2_source_acquisition_preflight()

    expected_task_ids = {task["task_id"] for task in preflight["cc0_download_tasks"]}
    tasks = {task["source_preflight_task_id"]: task for task in plan["acquisition_tasks"]}
    assert set(tasks) == expected_task_ids
    for task in tasks.values():
        assert task["execution_task_id"].endswith("cc0_source_acquisition_execution")
        assert task["asset_url"].startswith("https://polyhaven.com/a/")
        assert task["planned_source_root_env"].startswith("RAFTSIM_REVIEWED_")
        assert task["storage_decision_valid"] is False
        assert task["local_download_allowed_by_storage_policy"] is False
        assert task["source_binary_commit_allowed_by_storage_policy"] is False
        assert task["execution_allowed_now"] is False
        assert "record valid B2 source-binary storage decision result" in task[
            "required_before_execute"
        ]


def test_b2_source_acquisition_execution_plan_accepts_local_only_storage_policy_but_keeps_per_asset_blocker():
    plan = build_b2_source_acquisition_execution_plan(_complete_local_only_result())

    assert plan["status"] == (
        "b2_source_acquisition_policy_valid_per_asset_source_selection_required"
    )
    assert plan["storage_decision"]["storage_decision_valid"] is True
    assert plan["storage_decision"]["chosen_option_id"] == "local_only_hash_report_public_repo"
    assert plan["summary"]["local_download_policy_allowed_count"] == 22
    assert plan["summary"]["source_binary_commit_policy_allowed_count"] == 0
    assert plan["summary"]["per_asset_source_selection_complete_count"] == 0
    assert plan["summary"]["executable_task_count"] == 0
    assert plan["execution_gate"]["hash_reports_allowed_now"] is True
    assert plan["execution_gate"]["import_reports_allowed_now"] is True
    assert plan["execution_gate"]["downloads_allowed_now"] is False
    assert plan["promotion_gate"]["can_substitute_corridor_assets_from_execution_plan"] is False
    for task in plan["acquisition_tasks"]:
        assert task["storage_decision_valid"] is True
        assert task["local_download_allowed_by_storage_policy"] is True
        assert task["source_binary_commit_allowed_by_storage_policy"] is False
        assert task["per_asset_source_selection_complete"] is False
        assert task["execution_allowed_now"] is False
        assert "choose exact source resolution and file formats" in task[
            "required_before_execute"
        ]


def test_b2_source_acquisition_execution_plan_preserves_invalid_storage_errors():
    payload = _complete_local_only_result()
    payload["decision_result"]["generated_map_versioning_policy"] = "prune_generated_maps"
    plan = build_b2_source_acquisition_execution_plan(payload)

    assert plan["storage_decision"]["storage_decision_valid"] is False
    assert plan["summary"]["local_download_policy_allowed_count"] == 0
    assert {
        "field": "generated_map_versioning_policy",
        "reason": "generated_maps_must_remain_versioned",
    } in plan["storage_decision"]["errors"]
    assert plan["execution_gate"]["requires_valid_storage_decision"] is True


def test_b2_source_acquisition_execution_cli_writes_policy_sidecar(tmp_path):
    storage_result = _complete_local_only_result()
    storage_result_path = tmp_path / "valid_storage_decision_result.json"
    output_path = tmp_path / "b2_source_acquisition_execution_plan.json"
    storage_result_path.write_text(json.dumps(storage_result), encoding="utf-8")

    exit_code = generate_b2_source_acquisition_execution_main(
        [
            "--storage-decision-result",
            str(storage_result_path),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["storage_decision"]["storage_decision_valid"] is True
    assert payload["summary"]["local_download_policy_allowed_count"] == 22
    assert payload["summary"]["source_binary_commit_policy_allowed_count"] == 0
    assert payload["summary"]["executable_task_count"] == 0


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
