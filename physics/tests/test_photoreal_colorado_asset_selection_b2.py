import json
from pathlib import Path

from raftsim.photoreal_asset_intake_b1 import RIVER_ASSET_NEEDS
from raftsim.photoreal_colorado_asset_selection_b2 import (
    COLORADO_B2_ASSET_SELECTION_RELATIVE_PATH,
    COLORADO_B2_ASSET_SELECTION_SCHEMA,
    COLORADO_RIVER_ID,
    build_colorado_b2_asset_selection,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_manifest() -> dict:
    return json.loads(
        (REPO_ROOT / COLORADO_B2_ASSET_SELECTION_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_colorado_b2_asset_selection_is_reproducible_and_not_promoted():
    generated = build_colorado_b2_asset_selection()
    committed = _load_manifest()

    assert generated == committed
    assert committed["schema"] == COLORADO_B2_ASSET_SELECTION_SCHEMA
    assert committed["river_id"] == COLORADO_RIVER_ID
    assert committed["production_promoted"] is False
    assert committed["assets_downloaded"] is False
    assert committed["assets_imported"] is False
    assert committed["corridor_substitution_allowed"] is False
    assert committed["promotion_gate"]["can_substitute_corridor_assets"] is False


def test_colorado_b2_asset_selection_covers_all_b1_asset_needs():
    manifest = build_colorado_b2_asset_selection()
    expected_needs = {
        asset_need_id
        for asset_need_id, _ in RIVER_ASSET_NEEDS[COLORADO_RIVER_ID]["asset_needs"]
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

    assert (
        coverage["grand_canyon_layered_cliff_materials"][
            "has_cc0_download_candidate"
        ]
        is True
    )
    assert coverage["sand_beach_materials"]["has_cc0_download_candidate"] is True
    assert (
        coverage["desert_scrub_riparian_foliage"]["has_local_only_selection_slot"]
        is True
    )
    assert coverage["lava_falls_basalt"]["has_local_only_selection_slot"] is True


def test_colorado_b2_asset_selection_enforces_license_boundaries():
    manifest = build_colorado_b2_asset_selection()
    candidates = {
        candidate["candidate_id"]: candidate
        for candidate in manifest["candidate_assets"]
    }

    for candidate in candidates.values():
        if candidate["source_family"] == "Fab":
            assert candidate["repo_binary_policy"] == "do_not_commit_source_binaries"
            assert candidate["status"] == "local_only_exact_item_selection_pending"
            assert candidate["license_class"] == (
                "fab_standard_local_only_until_item_terms_prove_redistributable"
            )
        if candidate["source_family"] == "Poly Haven":
            assert candidate["asset_url"].startswith("https://polyhaven.com/a/")
            assert candidate["status"] == (
                "selected_for_download_hash_import_and_isolated_review"
            )
            assert candidate["license_class"] == (
                "cc0_committable_after_hash_and_attribution_snapshot"
            )
            assert "download source bundle from exact asset URL" in candidate[
                "required_before_import"
            ]
            assert "desktop and VR performance measurements" in candidate[
                "required_before_promotion"
            ]

    assert candidates["fab_grand_canyon_layered_cliff_hero_slot"]["asset_need_id"] == (
        "grand_canyon_layered_cliff_materials"
    )
    assert candidates["fab_desert_scrub_tamarisk_willow_cactus_slot"][
        "asset_need_id"
    ] == "desert_scrub_riparian_foliage"
    assert candidates["fab_lava_falls_basalt_slot"]["asset_need_id"] == (
        "lava_falls_basalt"
    )


def test_colorado_b2_asset_selection_records_geology_caveats():
    manifest = build_colorado_b2_asset_selection()
    candidates = {
        candidate["candidate_id"]: candidate
        for candidate in manifest["candidate_assets"]
    }

    assert "not Grand Canyon stratigraphy authority" in candidates[
        "polyhaven_rock_face"
    ]["notes"]
    assert "not a Grand Canyon geology or color authority" in candidates[
        "polyhaven_aerial_rocks_02"
    ]["notes"]
    assert candidates["first_party_colorado_biome_fallback_v1"][
        "status"
    ] == "required_fallback_until_external_assets_pass"
