import json
from pathlib import Path

from raftsim.south_fork_a1_official_access_geometry_review import (
    FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_DISCREPANCY_REVIEW_RELATIVE_PATH,
    FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_LEADS_GEOJSON_RELATIVE_PATH,
    build_south_fork_a1_official_access_geometry_discrepancy_review,
    build_south_fork_a1_official_access_geometry_leads_geojson,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_review() -> dict:
    return json.loads(
        (
            REPO_ROOT / FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_DISCREPANCY_REVIEW_RELATIVE_PATH
        ).read_text(encoding="utf-8")
    )


def _load_geojson() -> dict:
    return json.loads(
        (REPO_ROOT / FULL_REACH_OFFICIAL_ACCESS_GEOMETRY_LEADS_GEOJSON_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_south_fork_a1_official_access_geometry_review_is_reproducible():
    generated = build_south_fork_a1_official_access_geometry_discrepancy_review(
        REPO_ROOT
    )
    committed = _load_review()

    assert generated == committed
    assert (
        committed["schema"]
        == "raftsim.south_fork.a1_official_access_geometry_discrepancy_review.v1"
    )
    assert (
        committed["status"]
        == "official_access_geometry_disagrees_with_current_nhd_downstream_candidates"
    )
    assert committed["production_promoted"] is False


def test_south_fork_a1_official_access_geometry_review_records_primary_takeout_lead():
    review = _load_review()
    primary = review["primary_official_access_geometry_lead"]

    assert primary["name"] == "Salmon Falls  Lower Water Raft Take-out"
    assert primary["fid"] == 50927
    assert primary["gisid"] == "GIS0005556"
    assert primary["lon_lat"] == [-121.043513366612, 38.7717445614809]
    assert primary["review_role"] == "primary_official_downstream_access_geometry_lead"
    assert review["source"]["license"] == "Creative Commons Attribution"
    assert review["source"]["http_status"] == 200


def test_south_fork_a1_official_access_geometry_review_rejects_current_nhd_candidates():
    review = _load_review()

    assert review["summary"]["candidate_point_count"] == 2
    assert review["summary"]["official_access_record_count"] == 5
    assert review["summary"]["rejected_candidate_count"] == 2
    assert (
        review["summary"]["current_nhd_candidate_points_can_be_selected_as_exact_anchor"]
        is False
    )
    assert review["summary"]["replacement_or_reanchored_endpoint_required"] is True
    assert review["summary"]["minimum_distance_to_any_official_access_m"] > 9600.0
    assert review["summary"]["minimum_distance_to_primary_raft_takeout_m"] > 10400.0
    for comparison in review["candidate_comparisons"]:
        assert comparison["candidate_geometry_status"] == "rejected_for_exact_anchor_review"
        assert comparison["nearest_official_access"]["distance_m"] > 9600.0
        assert comparison["primary_raft_takeout_distance_m"] > 10400.0


def test_south_fork_a1_official_access_geometry_leads_geojson_is_reproducible():
    generated = build_south_fork_a1_official_access_geometry_leads_geojson(REPO_ROOT)
    committed = _load_geojson()

    assert generated == committed
    assert (
        committed["schema"]
        == "raftsim.south_fork.a1_official_access_geometry_leads.geojson.v1"
    )
    assert committed["type"] == "FeatureCollection"
    assert committed["candidate_feature_count_from_prior_geojson"] == 3
    assert len(committed["features"]) == 7
    assert [feature["geometry"]["type"] for feature in committed["features"]].count("Point") == 5
    assert [feature["geometry"]["type"] for feature in committed["features"]].count(
        "LineString"
    ) == 2
    for feature in committed["features"]:
        assert feature["properties"]["production_promoted"] is False
        assert feature["properties"]["can_bind_editor_geometry"] is False
        assert feature["properties"]["can_bind_solver_windows"] is False


def test_south_fork_a1_official_access_geometry_review_blocks_promotion():
    gate = _load_review()["promotion_gate"]

    assert gate["can_select_current_nhd_downstream_candidate"] is False
    assert gate["can_select_official_parking_point_without_bank_review"] is False
    assert gate["can_crop_to_final_downstream_anchor"] is False
    assert gate["can_promote_full_reach_centerline"] is False
    assert gate["can_restation_named_rapids"] is False
    assert gate["can_import_unreal_full_reach_landscape"] is False
    assert gate["can_bind_named_rapid_geometry"] is False
    assert gate["can_bind_solver_windows"] is False
