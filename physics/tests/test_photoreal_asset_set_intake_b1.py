import json
from pathlib import Path

from raftsim.photoreal_asset_intake_b1 import RIVER_ASSET_NEEDS
from raftsim.photoreal_asset_set_intake_b1 import (
    B1_ASSET_SET_INTAKE_RELATIVE_PATH,
    build_photoreal_asset_set_intake_b1,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_photoreal_asset_set_intake_b1_is_reproducible():
    generated = build_photoreal_asset_set_intake_b1(REPO_ROOT)
    committed = json.loads(
        (REPO_ROOT / B1_ASSET_SET_INTAKE_RELATIVE_PATH).read_text(encoding="utf-8")
    )

    assert generated == committed
    assert committed["schema"] == "raftsim.photoreal.asset_set_intake_b1.v1"
    assert committed["assets_imported"] is False
    assert committed["production_promoted"] is False


def test_photoreal_asset_set_intake_b1_has_one_command_per_asset_set():
    manifest = build_photoreal_asset_set_intake_b1(REPO_ROOT)
    expected_count = sum(len(river["asset_needs"]) for river in RIVER_ASSET_NEEDS.values())
    asset_sets = manifest["asset_sets"]

    assert manifest["asset_set_count"] == expected_count == 20
    assert len(asset_sets) == expected_count
    assert len({asset_set["asset_set_id"] for asset_set in asset_sets}) == expected_count
    assert all("UnrealEditor-Cmd RaftSim.uproject" in asset_set["command"]["template"] for asset_set in asset_sets)
    assert all(asset_set["command"]["script"].startswith("unreal/Scripts/") for asset_set in asset_sets)


def test_photoreal_asset_set_intake_b1_enforces_license_boundaries():
    manifest = build_photoreal_asset_set_intake_b1(REPO_ROOT)

    assert manifest["global_importer_hardening"]["may_commit_fab_standard_source_binaries"] is False
    for asset_set in manifest["asset_sets"]:
        assert asset_set["promotion_allowed"] is False
        assert asset_set["license_boundary"]["fab_standard"].startswith("local_only")
        assert asset_set["license_boundary"]["poly_haven"].startswith("cc0")
        policies = {candidate["source_family"]: candidate for candidate in asset_set["source_candidates"]}
        assert policies["Fab"]["repo_binary_policy"] == "do_not_commit_source_binaries"
        assert "may_commit" in policies["Poly Haven"]["repo_binary_policy"]


def test_photoreal_asset_set_intake_b1_records_importer_hardening_rules():
    manifest = build_photoreal_asset_set_intake_b1(REPO_ROOT)
    hardening = manifest["global_importer_hardening"]

    assert hardening["alpha_opacity_textures_as_masks"] is True
    assert hardening["masked_foliage_nanite_disabled_by_default"] is True
    assert hardening["nanite_preserve_area_only_for_reviewed_opaque_woody_or_rock"] is True
    assert hardening["procedural_fallback_required"] is True
    for asset_set in manifest["asset_sets"]:
        assert asset_set["importer_hardening"]["alpha_opacity_textures_as_masks"] is True
        assert asset_set["importer_hardening"]["procedural_fallback_required"] is True
        assert "map_check_zero_errors" in asset_set["importer_hardening"]["isolated_gate_required"]
