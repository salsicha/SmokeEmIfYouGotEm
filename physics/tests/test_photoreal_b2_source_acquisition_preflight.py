import json
from pathlib import Path

from raftsim.photoreal_b2_source_acquisition_preflight import (
    B2_SOURCE_ACQUISITION_PREFLIGHT_RELATIVE_PATH,
    B2_SOURCE_ACQUISITION_PREFLIGHT_SCHEMA,
    SELECTION_BUILDERS,
    build_b2_source_acquisition_preflight,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_preflight() -> dict:
    return json.loads(
        (REPO_ROOT / B2_SOURCE_ACQUISITION_PREFLIGHT_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_b2_source_acquisition_preflight_is_reproducible_and_disabled():
    generated = build_b2_source_acquisition_preflight()
    committed = _load_preflight()

    assert generated == committed
    assert committed["schema"] == B2_SOURCE_ACQUISITION_PREFLIGHT_SCHEMA
    assert committed["river_count"] == 5
    assert committed["selection_manifest_count"] == 5
    assert committed["candidate_asset_count"] == 46
    assert committed["cc0_download_task_count"] == 22
    assert committed["fab_local_only_slot_count"] == 16
    assert committed["first_party_entry_count"] == 6
    assert committed["execution_gate"]["downloads_allowed_now"] is False
    assert committed["execution_gate"]["imports_allowed_now"] is False
    assert committed["execution_gate"]["source_binaries_allowed_in_repo_now"] is False
    assert committed["execution_gate"]["requires_owner_size_storage_decision"] is True


def test_b2_source_acquisition_preflight_covers_selected_cc0_candidates():
    preflight = build_b2_source_acquisition_preflight()
    expected_task_ids = set()
    expected_urls = set()
    for _, _, build_selection in SELECTION_BUILDERS:
        selection = build_selection()
        for candidate in selection["candidate_assets"]:
            if (
                candidate["source_family"] == "Poly Haven"
                and candidate["status"]
                == "selected_for_download_hash_import_and_isolated_review"
            ):
                expected_task_ids.add(
                    f"{selection['river_id']}:{candidate['candidate_id']}:"
                    "cc0_source_download_preflight"
                )
                expected_urls.add(candidate["asset_url"])

    tasks = {task["task_id"]: task for task in preflight["cc0_download_tasks"]}
    assert set(tasks) == expected_task_ids
    assert {task["asset_url"] for task in tasks.values()} == expected_urls

    for task in tasks.values():
        assert task["asset_url"].startswith("https://polyhaven.com/a/")
        assert task["execution_allowed"] is False
        assert task["repo_commit_allowed_now"] is False
        assert task["planned_source_root_env"].startswith("RAFTSIM_REVIEWED_")
        assert "record owner storage approval for source binaries" in task[
            "required_before_execute"
        ]
        assert "record SHA-256 hash for every source file" in task[
            "required_before_commit"
        ]


def test_b2_source_acquisition_preflight_keeps_fab_local_only():
    preflight = build_b2_source_acquisition_preflight()

    for slot in preflight["fab_local_only_slots"]:
        assert slot["asset_url"].startswith("https://www.fab.com/search?q=")
        assert slot["download_into_public_repo_allowed"] is False
        assert slot["commit_source_binaries_allowed"] is False
        assert slot["repo_binary_policy"] == "do_not_commit_source_binaries"
        assert slot["license_class"] == (
            "fab_standard_local_only_until_item_terms_prove_redistributable"
        )


def test_b2_source_acquisition_preflight_preserves_first_party_fallbacks():
    preflight = build_b2_source_acquisition_preflight()
    entries = {
        entry["candidate_id"]: entry for entry in preflight["first_party_entries"]
    }

    assert {
        "first_party_south_fork_biome_fallback_v1",
        "first_party_colorado_biome_fallback_v1",
        "first_party_pacuare_biome_fallback_v1",
        "first_party_futaleufu_biome_fallback_v1",
        "first_party_chilko_biome_fallback_v1",
        "project_owned_futaleufu_sapling_fern_strata_v1",
    } == set(entries)
    assert all(entry["can_cover_external_asset_gap"] for entry in entries.values())
    assert not any(
        entry["can_replace_human_lifelike_review"] for entry in entries.values()
    )


def test_b2_source_acquisition_preflight_manifest_paths_exist():
    preflight = build_b2_source_acquisition_preflight()
    manifest_paths = {
        selection["relative_path"] for selection in preflight["selection_manifests"]
    }

    assert len(manifest_paths) == 5
    assert all((REPO_ROOT / path).exists() for path in manifest_paths)
