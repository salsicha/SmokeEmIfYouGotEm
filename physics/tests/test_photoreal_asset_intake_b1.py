import json
from pathlib import Path

from raftsim.photoreal_asset_intake_b1 import (
    B1_ASSET_INTAKE_RELATIVE_PATH,
    build_photoreal_asset_intake_b1,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_intake() -> dict:
    return json.loads(
        (REPO_ROOT / B1_ASSET_INTAKE_RELATIVE_PATH).read_text(encoding="utf-8")
    )


def test_photoreal_asset_intake_b1_is_reproducible():
    generated = build_photoreal_asset_intake_b1()
    committed = _load_intake()

    assert generated == committed
    assert committed["schema"] == "raftsim.photoreal.asset_intake_b1.v1"
    assert committed["status"] == (
        "survey_baseline_and_intake_contract_recorded_not_assets_imported"
    )
    assert committed["production_promoted"] is False


def test_photoreal_asset_intake_b1_records_license_boundaries():
    intake = _load_intake()
    licenses = intake["license_classes"]
    source_urls = {source["source_family"]: source["url"] for source in intake["license_sources_checked"]}

    assert source_urls["Fab"] == "https://www.fab.com/eula"
    assert source_urls["Poly Haven"] == "https://polyhaven.com/license"
    assert licenses[
        "fab_standard_local_only_until_item_terms_prove_redistributable"
    ]["may_commit_source_binaries"] is False
    assert licenses[
        "cc0_committable_after_hash_and_attribution_snapshot"
    ]["may_commit_source_binaries"] is True
    assert licenses["first_party_committable"]["requires_recipe_or_prompt_manifest"] is True


def test_photoreal_asset_intake_b1_has_per_river_shopping_lists():
    intake = _load_intake()
    rivers = {river["river_id"]: river for river in intake["river_shopping_lists"]}

    assert set(rivers) == {
        "south_fork_american_chili_bar",
        "colorado_river_grand_canyon_rowing",
        "pacuare_river_costa_rica",
        "futaleufu_river_chile",
        "chilko_river_lava_canyon",
    }
    for river in rivers.values():
        assert len(river["asset_needs"]) >= 4
        for need in river["asset_needs"]:
            families = {
                candidate["source_family"]: candidate
                for candidate in need["source_candidates"]
            }
            assert set(families) == {"Fab", "Poly Haven", "First-party procedural"}
            assert families["Fab"]["repo_binary_policy"] == "do_not_commit_source_binaries"
            assert families["Poly Haven"]["license_class"] == (
                "cc0_committable_after_hash_and_attribution_snapshot"
            )


def test_photoreal_asset_intake_b1_hardens_import_contract():
    intake = _load_intake()
    contract = intake["intake_hardening_contract"]
    gate = intake["promotion_gate"]

    assert contract["existing_local_source_root_pattern"] == (
        "RAFTSIM_REVIEWED_*_SOURCE_ROOT"
    )
    assert "classify alpha/opacity textures as masks" in contract["new_importers_must"]
    assert "60 m river-distance capture" in contract["isolated_gate_required"]
    assert "150 m river-distance capture" in contract["isolated_gate_required"]
    assert intake["zambezi_policy"]["portfolio_role"] == (
        "additional_active_environment_backlogged"
    )
    assert gate["b1_complete_for_planning"] is True
    assert gate["assets_imported"] is False
    assert gate["can_promote_any_river_asset_set"] is False
