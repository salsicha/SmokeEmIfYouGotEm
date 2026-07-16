import json
from pathlib import Path

from raftsim.photoreal_asset_intake_b1 import RIVER_ASSET_NEEDS
from raftsim.photoreal_south_fork_asset_selection_b2 import (
    SOUTH_FORK_B2_ASSET_SELECTION_RELATIVE_PATH,
    SOUTH_FORK_B2_ASSET_SELECTION_SCHEMA,
    SOUTH_FORK_RIVER_ID,
    build_south_fork_b2_asset_selection,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_manifest() -> dict:
    return json.loads(
        (REPO_ROOT / SOUTH_FORK_B2_ASSET_SELECTION_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_south_fork_b2_asset_selection_is_reproducible_and_not_promoted():
    generated = build_south_fork_b2_asset_selection()
    committed = _load_manifest()

    assert generated == committed
    assert committed["schema"] == SOUTH_FORK_B2_ASSET_SELECTION_SCHEMA
    assert committed["river_id"] == SOUTH_FORK_RIVER_ID
    assert committed["production_promoted"] is False
    assert committed["assets_downloaded"] is False
    assert committed["assets_imported"] is False
    assert committed["corridor_substitution_allowed"] is False
    assert committed["promotion_gate"]["can_substitute_corridor_assets"] is False


def test_south_fork_b2_asset_selection_covers_all_b1_asset_needs():
    manifest = build_south_fork_b2_asset_selection()
    expected_needs = {
        asset_need_id
        for asset_need_id, _ in RIVER_ASSET_NEEDS[SOUTH_FORK_RIVER_ID]["asset_needs"]
    }
    coverage = {
        entry["asset_need_id"]: entry for entry in manifest["asset_need_coverage"]
    }

    assert set(coverage) == expected_needs
    for entry in coverage.values():
        assert entry["candidate_ids"]
        assert entry["has_first_party_fallback"] is True
        assert entry["promotion_status"] == (
            "blocked_pending_source_hashes_import_captures_and_reviews"
        )

    assert coverage["granite_metamorphic_boulders"]["has_cc0_download_candidate"] is True
    assert coverage["dry_grass_bank_materials"]["has_cc0_download_candidate"] is True
    assert coverage["sierra_oak_gray_pine_foliage"]["has_local_only_selection_slot"] is True
    assert coverage["chaparral_shrub_understory"]["has_local_only_selection_slot"] is True


def test_south_fork_b2_asset_selection_enforces_license_boundaries():
    manifest = build_south_fork_b2_asset_selection()
    candidates = {candidate["candidate_id"]: candidate for candidate in manifest["candidate_assets"]}

    for candidate in candidates.values():
        if candidate["source_family"] == "Fab":
            assert candidate["repo_binary_policy"] == "do_not_commit_source_binaries"
            assert candidate["status"] == "local_only_exact_item_selection_pending"
            assert candidate["license_class"] == (
                "fab_standard_local_only_until_item_terms_prove_redistributable"
            )
        if candidate["source_family"] == "Poly Haven" and candidate["status"].startswith(
            "selected_for_download"
        ):
            assert candidate["asset_url"].startswith("https://polyhaven.com/a/")
            assert candidate["license_class"] == (
                "cc0_committable_after_hash_and_attribution_snapshot"
            )
            assert "download source bundle from exact asset URL" in candidate[
                "required_before_import"
            ]
            assert "desktop and VR performance measurements" in candidate[
                "required_before_promotion"
            ]

    assert candidates["fab_blue_oak_gray_pine_hero_foliage_slot"]["asset_need_id"] == (
        "sierra_oak_gray_pine_foliage"
    )
    assert candidates["fab_chaparral_shrub_understory_slot"]["asset_need_id"] == (
        "chaparral_shrub_understory"
    )


def test_south_fork_b2_asset_selection_preserves_rejected_tree_evidence():
    manifest = build_south_fork_b2_asset_selection()
    candidates = {candidate["candidate_id"]: candidate for candidate in manifest["candidate_assets"]}

    for candidate_id in ("polyhaven_fir_tree_01_1k", "polyhaven_tree_small_02_1k"):
        candidate = candidates[candidate_id]
        assert candidate["status"] == (
            "rejected_visual_promotion_retain_as_import_pipeline_evidence"
        )
        evidence = REPO_ROOT / candidate["review_evidence"]
        assert evidence.exists()
        review = json.loads(evidence.read_text(encoding="utf-8"))
        assert review["production_promoted"] is False
        assert "rejected" in review["status"]
