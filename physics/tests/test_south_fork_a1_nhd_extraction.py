import json
from pathlib import Path

from raftsim.south_fork_a1_nhd_extraction import (
    FULL_REACH_NHD_GEOJSON_RELATIVE_PATH,
    FULL_REACH_NHD_MANIFEST_RELATIVE_PATH,
    SOURCE_ZIP_SHA256,
    SOURCE_ZIP_SIZE_BYTES,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(relative_path: str) -> dict:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def test_south_fork_a1_nhd_extract_manifest_records_verified_source_zip():
    manifest = _load(FULL_REACH_NHD_MANIFEST_RELATIVE_PATH)

    assert manifest["schema"] == (
        "raftsim.south_fork.a1_full_reach_nhd_named_flowline_extract.manifest.v1"
    )
    assert (
        manifest["status"]
        == "official_nhd_hu8_named_flowlines_extracted_review_gated_not_route"
    )
    assert manifest["source_archive"]["committed_to_repo"] is False
    assert manifest["source_archive"]["sha256"] == SOURCE_ZIP_SHA256
    assert manifest["source_archive"]["expected_sha256"] == SOURCE_ZIP_SHA256
    assert manifest["source_archive"]["size_bytes"] == SOURCE_ZIP_SIZE_BYTES
    assert manifest["source_archive"]["expected_size_bytes"] == SOURCE_ZIP_SIZE_BYTES
    assert manifest["outputs"]["geojson"] == FULL_REACH_NHD_GEOJSON_RELATIVE_PATH
    assert manifest["review_gates"][-1] == (
        "Do not bind editor markers or solver windows to this candidate pool directly."
    )


def test_south_fork_a1_nhd_extract_preserves_named_candidate_pool_not_route():
    manifest = _load(FULL_REACH_NHD_MANIFEST_RELATIVE_PATH)
    geojson = _load(FULL_REACH_NHD_GEOJSON_RELATIVE_PATH)

    assert geojson["schema"] == (
        "raftsim.south_fork.a1_full_reach_nhd_named_flowline_extract.geojson.v1"
    )
    assert geojson["status"] == "review_gated_named_flowline_pool_not_ordered_route"
    assert geojson["source"]["source_archive_committed"] is False
    assert geojson["source"]["sha256"] == SOURCE_ZIP_SHA256
    assert geojson["source"]["layer"] == "NHDFlowline"
    assert geojson["selection"] == manifest["selection"]

    selection = geojson["selection"]
    assert selection["gnis_name"] == "South Fork American River"
    assert selection["named_record_count_in_hu8"] == 586
    assert selection["selected_record_count"] == 198
    assert selection["selected_length_km_source_sum"] == 65.786574
    assert selection["review_envelope_wgs84"] == {
        "min_lon": -121.12,
        "min_lat": 38.68,
        "max_lon": -120.7,
        "max_lat": 38.86,
    }
    assert selection["selected_bounds_wgs84"] == {
        "min_lon": -121.1396311,
        "min_lat": 38.7054284,
        "max_lon": -120.698556,
        "max_lat": 38.82511,
    }


def test_south_fork_a1_nhd_extract_features_keep_source_ids_and_block_promotion():
    geojson = _load(FULL_REACH_NHD_GEOJSON_RELATIVE_PATH)
    features = geojson["features"]

    assert len(features) == 198
    assert {feature["geometry"]["type"] for feature in features} == {"LineString"}
    assert {
        feature["properties"]["gnis_name"] for feature in features
    } == {"South Fork American River"}
    assert {
        feature["properties"]["geometry_status"] for feature in features
    } == {"named_flowline_source_candidate_not_ordered_route"}
    assert all(
        feature["properties"]["permanent_identifier"]
        and feature["properties"]["reachcode"]
        and feature["properties"]["source_record_number"] > 0
        for feature in features
    )
    assert "candidate pool" in geojson["promotion_gate"]
