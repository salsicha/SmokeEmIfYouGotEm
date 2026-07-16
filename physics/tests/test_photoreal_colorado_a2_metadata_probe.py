import json
from pathlib import Path

from raftsim.colorado_a2_metadata_probe import (
    COLORADO_A2_METADATA_PROBE_RELATIVE_PATH,
    COLORADO_A2_METADATA_PROBE_SCHEMA,
    build_colorado_a2_metadata_probe,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_probe() -> dict:
    return json.loads(
        (REPO_ROOT / COLORADO_A2_METADATA_PROBE_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_colorado_a2_metadata_probe_is_reproducible_and_fail_closed():
    generated = build_colorado_a2_metadata_probe()
    committed = _load_probe()

    assert generated == committed
    assert committed["schema"] == COLORADO_A2_METADATA_PROBE_SCHEMA
    assert committed["status"] == "metadata_probe_recorded_no_source_download_no_promotion"
    assert committed["production_promoted"] is False
    assert committed["source_downloads_allowed"] is False
    assert committed["centerline_binding_allowed"] is False
    assert committed["unreal_import_allowed"] is False
    assert committed["promotion_gate"]["source_archives_or_rasters_downloaded"] is False
    assert committed["promotion_gate"]["can_promote_centerline_or_windows"] is False


def test_colorado_a2_metadata_probe_records_official_tnm_counts_and_hashes():
    probe = build_colorado_a2_metadata_probe()
    results = {result["source_class"]: result for result in probe["results"]}

    assert results["hydrography"]["total"] == 94
    assert results["hydrography"]["returned_item_count"] == 50
    assert results["hydrography"]["raw_response_bytes"] == 155455
    assert results["hydrography"]["raw_response_sha256"] == (
        "6abd6af5332e92dff8ce6fbafedfa3d0b00e47c915f42c904465d55e7807c604"
    )
    assert "published 20250918" in results["hydrography"]["representative_titles"][0]
    assert results["terrain_dem_or_lidar"]["total"] == 0
    assert results["terrain_dem_or_lidar"]["raw_response_sha256"] == (
        "e10fcbd722f8452dac5a68a01f53e51c2d905ad55cb5fe8a59f9d798c325063b"
    )
    assert results["aerial_imagery"]["total"] == 0
    assert results["aerial_imagery"]["raw_response_sha256"] == (
        "28f286d7dab16ee0cc56a20e6f9ce6199fc4d6e5129eaaa37834ba0bdf140f66"
    )


def test_colorado_a2_metadata_probe_routes_zero_hit_sources_to_bounded_exports():
    probe = build_colorado_a2_metadata_probe()
    results = {result["source_class"]: result for result in probe["results"]}

    assert "tnmaccess.nationalmap.gov" in results["hydrography"]["query_url"]
    assert "bbox=-114.35,35.65,-111.45,36.95" in results["hydrography"]["query_url"]
    assert "USGS 3DEP ImageServer" in results["terrain_dem_or_lidar"]["next_action"]
    assert "USDA/APFO NAIP ImageServer" in results["aerial_imagery"]["next_action"]
    assert probe["promotion_gate"]["hydrography_products_available_for_review"] is True
    assert probe["promotion_gate"]["terrain_product_metadata_available"] is False
    assert probe["promotion_gate"]["naip_product_metadata_available"] is False
    assert probe["promotion_gate"]["full_reach_source_pull_urls_generated"] is False
