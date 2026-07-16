import json
from pathlib import Path

from raftsim.photoreal_asset_intake_b1 import RIVER_ASSET_NEEDS
from raftsim.photoreal_futaleufu_asset_selection_b2 import (
    FUTALEUFU_B2_ASSET_SELECTION_RELATIVE_PATH,
    FUTALEUFU_B2_ASSET_SELECTION_SCHEMA,
    FUTALEUFU_RIVER_ID,
    build_futaleufu_b2_asset_selection,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_manifest() -> dict:
    return json.loads(
        (REPO_ROOT / FUTALEUFU_B2_ASSET_SELECTION_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_futaleufu_b2_asset_selection_is_reproducible_and_not_promoted():
    generated = build_futaleufu_b2_asset_selection()
    committed = _load_manifest()

    assert generated == committed
    assert committed["schema"] == FUTALEUFU_B2_ASSET_SELECTION_SCHEMA
    assert committed["river_id"] == FUTALEUFU_RIVER_ID
    assert committed["production_promoted"] is False
    assert committed["assets_downloaded"] is False
    assert committed["assets_imported"] is False
    assert committed["corridor_substitution_allowed"] is False
    assert committed["promotion_gate"]["can_substitute_corridor_assets"] is False


def test_futaleufu_b2_asset_selection_covers_all_b1_asset_needs():
    manifest = build_futaleufu_b2_asset_selection()
    expected_needs = {
        asset_need_id
        for asset_need_id, _ in RIVER_ASSET_NEEDS[FUTALEUFU_RIVER_ID]["asset_needs"]
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

    canopy = coverage["nothofagus_coigue_canopy_or_reviewed_analog"]
    assert canopy["has_local_only_selection_slot"] is True
    assert canopy["has_cc0_download_candidate"] is False

    near_bank = coverage["near_bank_sapling_fern_strata"]
    assert near_bank["has_cc0_download_candidate"] is True
    assert near_bank["has_project_owned_review_candidate"] is True

    assert coverage["patagonian_granite_boulders"][
        "has_cc0_download_candidate"
    ] is True
    assert coverage["patagonian_granite_boulders"][
        "has_local_only_selection_slot"
    ] is True
    assert coverage["turquoise_wet_bank_materials"][
        "has_cc0_download_candidate"
    ] is True
    assert coverage["turquoise_wet_bank_materials"][
        "has_local_only_selection_slot"
    ] is True


def test_futaleufu_b2_asset_selection_enforces_license_boundaries():
    manifest = build_futaleufu_b2_asset_selection()
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

    retained = candidates["project_owned_futaleufu_sapling_fern_strata_v1"]
    assert retained["source_family"] == "Project-owned procedural"
    assert retained["status"] == "retained_review_evidence_not_production_promoted"
    assert (REPO_ROOT / retained["review_evidence"]).exists()


def test_futaleufu_b2_asset_selection_records_canopy_and_geology_caveats():
    manifest = build_futaleufu_b2_asset_selection()
    candidates = {
        candidate["candidate_id"]: candidate
        for candidate in manifest["candidate_assets"]
    }

    assert "owner ecology-analog decision" in candidates[
        "fab_futaleufu_nothofagus_coigue_canopy_slot"
    ]["notes"]
    assert "not a replacement for Nothofagus/coigue canopy" in candidates[
        "polyhaven_fern_02"
    ]["notes"]
    assert "not Patagonia granite geology authority" in candidates[
        "polyhaven_mountainside"
    ]["notes"]

    for source_path in manifest["source_contracts"].values():
        if source_path.endswith(".md") or source_path.endswith(".json"):
            assert (REPO_ROOT / source_path).exists()
