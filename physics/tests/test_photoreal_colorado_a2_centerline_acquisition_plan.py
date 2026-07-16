import json
from pathlib import Path

from raftsim.colorado_a2_centerline_acquisition_plan import (
    COLORADO_A2_CENTERLINE_ACQUISITION_PLAN_RELATIVE_PATH,
    COLORADO_A2_CENTERLINE_ACQUISITION_PLAN_SCHEMA,
    COLORADO_RIVER_ID,
    FULL_REACH_REVIEW_ENVELOPE_WGS84,
    build_colorado_a2_centerline_acquisition_plan,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_plan() -> dict:
    return json.loads(
        (REPO_ROOT / COLORADO_A2_CENTERLINE_ACQUISITION_PLAN_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_colorado_a2_centerline_acquisition_plan_is_reproducible_and_fail_closed():
    generated = build_colorado_a2_centerline_acquisition_plan(REPO_ROOT)
    committed = _load_plan()

    assert generated == committed
    assert committed["schema"] == COLORADO_A2_CENTERLINE_ACQUISITION_PLAN_SCHEMA
    assert committed["river_id"] == COLORADO_RIVER_ID
    assert committed["status"] == "planned_no_source_downloaded_not_centerline_or_crs_authority"
    assert committed["production_promoted"] is False
    assert committed["source_downloads_allowed"] is False
    assert committed["centerline_binding_allowed"] is False
    assert committed["source_window_bbox_generation_allowed"] is False
    assert committed["rapid_stationing_promotion_allowed"] is False
    assert committed["promotion_gate"]["can_download_full_reach_sources"] is False
    assert committed["promotion_gate"]["can_promote_a2_centerline"] is False


def test_colorado_a2_centerline_plan_records_the_current_scope_gap():
    plan = build_colorado_a2_centerline_acquisition_plan(REPO_ROOT)
    scope_gap = plan["current_scope_gap"]

    assert scope_gap["existing_editor_binding_max_station_m"] == 4700.0
    assert scope_gap["planned_run_length_m"] == 451420.0
    assert scope_gap["planned_run_length_river_miles"] > 280.0
    assert scope_gap["a2_window_count_waiting_for_bboxes"] == 23
    assert scope_gap["existing_source_manifest_bounds_status"] == (
        "pilot_and_partial_canyon_bounds_insufficient_for_pearce_ferry_full_run"
    )
    assert plan["review_envelope_wgs84"] == FULL_REACH_REVIEW_ENVELOPE_WGS84
    assert plan["review_envelope_policy"][
        "must_clip_to_reviewed_centerline_before_download"
    ] is True


def test_colorado_a2_centerline_plan_keeps_endpoints_and_crs_review_gated():
    plan = build_colorado_a2_centerline_acquisition_plan(REPO_ROOT)
    endpoints = {
        endpoint["anchor_id"]: endpoint for endpoint in plan["endpoint_review_targets"]
    }

    assert set(endpoints) == {"lees_ferry_put_in", "pearce_ferry_takeout"}
    assert endpoints["lees_ferry_put_in"]["current_seed_lon_lat"] == [
        -111.5167285,
        36.8777351,
    ]
    assert endpoints["lees_ferry_put_in"]["current_seed_status"].startswith("NHD pilot")
    assert endpoints["pearce_ferry_takeout"]["current_seed_lon_lat"] is None
    assert endpoints["pearce_ferry_takeout"]["current_seed_status"] == "missing_exact_anchor"

    crs_ids = {candidate["crs_id"] for candidate in plan["working_crs_candidates"]}
    assert crs_ids == {"EPSG:26912", "local_river_mile_station_axis"}
    for candidate in plan["working_crs_candidates"]:
        assert candidate["status"].startswith("candidate_needs")
    assert plan["promotion_gate"]["working_crs_selected"] is False
    assert plan["promotion_gate"]["pearce_ferry_anchor_reviewed"] is False


def test_colorado_a2_centerline_plan_names_source_candidates_and_outputs():
    plan = build_colorado_a2_centerline_acquisition_plan(REPO_ROOT)
    source_candidates = {
        candidate["candidate_id"]: candidate for candidate in plan["centerline_source_candidates"]
    }
    outputs = {output["artifact"]: output for output in plan["planned_outputs"]}

    assert set(source_candidates) == {
        "usgs_3dhp_or_nhd_full_reach",
        "nps_or_gcmrc_river_mile_reference",
        "usgs_hydraulic_maps_major_rapids",
    }
    assert source_candidates["usgs_3dhp_or_nhd_full_reach"]["query_url"].startswith(
        "https://tnmaccess.nationalmap.gov/api/v1/products?"
    )
    assert source_candidates["usgs_hydraulic_maps_major_rapids"]["query_url"] == (
        "https://pubs.usgs.gov/imap/1897j/"
    )
    assert len(plan["source_request_prerequisites"]) == 5
    assert any(
        artifact.endswith("full_reach_source_pull_plan.json") for artifact in outputs
    )
    assert all(output["status"] == "not_generated" for output in outputs.values())
