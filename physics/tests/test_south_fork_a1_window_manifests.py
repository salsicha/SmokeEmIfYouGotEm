import json
from pathlib import Path

from raftsim.south_fork_a1_window_manifests import (
    FULL_REACH_WINDOW_MANIFEST_INDEX_RELATIVE_PATH,
    build_south_fork_a1_full_reach_window_source_manifests,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_index() -> dict:
    return json.loads(
        (REPO_ROOT / FULL_REACH_WINDOW_MANIFEST_INDEX_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _load_manifest(path: str) -> dict:
    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def test_south_fork_a1_window_manifest_index_is_reproducible():
    generated = build_south_fork_a1_full_reach_window_source_manifests(REPO_ROOT)
    generated_index = {key: value for key, value in generated.items() if key != "manifests"}
    committed = _load_index()

    assert generated_index == committed
    assert committed["schema"] == "raftsim.south_fork.a1_full_reach_window_source_manifest_index.v1"
    assert committed["status"] == "per_window_source_manifests_generated_stitched_validation_pending"
    assert committed["production_promoted"] is False


def test_south_fork_a1_window_manifests_cover_all_windows_and_sources():
    index = _load_index()

    assert index["summary"]["window_count"] == 8
    assert index["summary"]["source_manifest_count"] == 8
    assert index["summary"]["all_sources_present"] is True
    assert index["summary"]["can_enter_stitched_validation_review"] is True
    assert index["summary"]["can_promote_full_reach_corridor"] is False
    assert len(index["window_manifests"]) == 8
    window_ids = {entry["window_id"] for entry in index["window_manifests"]}
    assert "below_full_run_alias_33796_41500m" in window_ids
    assert "salmon_falls_takeout_approach_41500_49077m" in window_ids
    for entry in index["window_manifests"]:
        assert len(entry["terrain_sha256"]) == 64
        assert len(entry["aerial_sha256"]) == 64
        assert entry["manifest_path"].endswith("/manifest.json")
        assert entry["can_enter_stitched_validation_review"] is True
        assert entry["production_promoted"] is False


def test_south_fork_a1_per_window_manifests_record_terms_crs_resolution_and_gates():
    index = _load_index()

    for entry in index["window_manifests"]:
        manifest = _load_manifest(entry["manifest_path"])
        dem = manifest["source_artifacts"]["dem"]
        aerial = manifest["source_artifacts"]["aerial"]

        assert manifest["schema"] == "raftsim.south_fork.a1_full_reach_window_source_manifest.v1"
        assert manifest["status"] == "source_files_attached_derivatives_pending_review_gated"
        assert manifest["production_promoted"] is False
        assert dem["coordinate_reference_system"] == "EPSG:3857 Web Mercator export grid"
        assert aerial["coordinate_reference_system"] == "EPSG:3857 Web Mercator export grid"
        assert dem["dimensions"] == [2048, 2048]
        assert aerial["dimensions"] == [4096, 4096]
        assert dem["pixel_resolution_m_approx"][0] > 0.0
        assert aerial["pixel_resolution_m_approx"][0] > 0.0
        assert dem["rights"].startswith("U.S. Public Domain")
        assert aerial["rights"].startswith("U.S. Public Domain")
        assert "3DEPElevation/ImageServer/exportImage" in dem["official_export_url"]
        assert "NAIP/USDA_CONUS_PRIME/ImageServer/exportImage" in aerial["official_export_url"]
        assert manifest["promotion_gate"]["can_generate_window_derivatives"] is True
        assert manifest["promotion_gate"]["can_enter_stitched_validation_review"] is True
        assert manifest["promotion_gate"]["can_import_unreal_landscape"] is False
        assert manifest["promotion_gate"]["can_bind_solver_windows"] is False
