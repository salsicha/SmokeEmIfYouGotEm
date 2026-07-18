import json
from pathlib import Path

from raftsim.south_fork_a1_stationing import (
    A1_ADOPTION_DECISION_SOURCE,
    A1_STATUS_RELATIVE_PATH,
    FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH,
    build_south_fork_a1_stationing_repair_status,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_status() -> dict:
    return json.loads((REPO_ROOT / A1_STATUS_RELATIVE_PATH).read_text(encoding="utf-8"))


def test_south_fork_a1_stationing_status_is_reproducible():
    generated = build_south_fork_a1_stationing_repair_status(REPO_ROOT)
    committed = _load_status()

    assert generated == committed
    assert committed["schema"] == "raftsim.south_fork.a1_stationing_repair_status.v1"
    assert (
        committed["status"]
        == "adopted_official_access_anchor_full_reach_stationing_active"
    )
    assert committed["decision_source"] == A1_ADOPTION_DECISION_SOURCE
    assert committed["decision_source"] == "release-1.0-plan-v2 §6, July 17 2026"
    assert committed["production_promoted"] is False
    assert "exact rapid geometry" in committed["do_not_use_for"]
    assert "photoreal or gameplay realism claims" in committed["do_not_use_for"]


def test_south_fork_a1_records_the_adopted_anchor_and_axis():
    status = _load_status()
    adopted = status["adopted_route_stationing"]

    assert adopted["artifact"] == FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH
    assert adopted["artifact_status"] == (
        "adopted_official_access_anchor_route_stationing_active"
    )
    assert adopted["decision_source"] == A1_ADOPTION_DECISION_SOURCE
    assert adopted["station_axis_id"] == "adopted_nhd_directed_mainstem_chain_v1"
    assert adopted["downstream_anchor_name"] == (
        "Salmon Falls  Lower Water Raft Take-out"
    )
    assert adopted["downstream_anchor_fid"] == 50927
    assert adopted["downstream_anchor_authority"] == (
        "california_state_parks_parking_points"
    )
    assert adopted["downstream_anchor_station_m"] == 49077.732
    assert adopted["adopted_route_length_m"] == 49077.732
    assert adopted["published_mile_alias_policy"] == (
        "published_river_miles_are_alias_metadata_not_anchors"
    )
    assert "aliases" in adopted["published_mile_divergence_note"]
    assert adopted["rapid_station_count"] == 20
    assert adopted["order_interpolation_used"] is False


def test_south_fork_a1_stations_all_rapids_on_the_adopted_axis():
    status = _load_status()
    scaffold = status["catalog_stationing_scaffold"]

    assert scaffold["stationing_authority"] == "published_river_miles"
    assert scaffold["station_axis"] == "adopted_nhd_directed_mainstem_chain_v1"
    assert scaffold["published_mile_role"] == (
        "alias_metadata_with_recorded_divergence"
    )
    assert scaffold["rapid_count"] == 20
    assert scaffold["rapid_mile_min"] == 0.0
    assert scaffold["rapid_mile_max"] == 19.3
    assert scaffold["downstreammost_catalog_rapid"] == "Surprise"
    assert scaffold["all_rapids_have_published_miles"] is True
    assert scaffold["run_length_m"] == 33796.224
    assert scaffold["adopted_route_length_m"] == 49077.732

    rapids = scaffold["rapid_stations"]
    rapid_names = [rapid["name"] for rapid in rapids]
    assert rapid_names[:2] == ["Chili Bar Hole", "Meat Grinder"]
    assert "Troublemaker" in rapid_names
    assert rapid_names[-1] == "Surprise"
    assert {rapid["exact_geometry_status"] for rapid in rapids} == {
        "stationed_on_adopted_axis_exact_geometry_pending_p3_p4"
    }
    assert all(
        rapid["pending_human_review"] is True
        and rapid["review_batch"] == "p7_owner_review_packet"
        and len(rapid["lon_lat_on_adopted_axis"]) == 2
        for rapid in rapids
    )
    stations = [rapid["station_m_on_adopted_axis"] for rapid in rapids]
    assert all(earlier < later for earlier, later in zip(stations, stations[1:]))
    assert stations[-1] == 31060.3392


def test_south_fork_a1_preserves_rejected_candidate_evidence_and_coverage_gap():
    status = _load_status()
    geometry = status["current_geometry_evidence"]
    coverage = status["current_source_coverage"]

    assert geometry["alignment_status"] == "failed_alignment_binding_disabled"
    assert geometry["candidate_declared_length_m"] == 26204.692
    assert geometry["published_chili_bar_to_coloma_length_m"] == 9012.3264
    assert geometry["candidate_covers_catalog_full_run_length"] is False
    assert geometry["geometry_binding_enabled"] is False
    assert geometry["adopted_axis_stationing_enabled"] is True
    assert "retained as evidence" in geometry["candidate_disposition"]

    assert coverage["nhd_extract_is_full_reach"] is False
    assert coverage["full_reach_extract_supports_adopted_axis"] is True
    assert coverage["production_corridor_reach_id"] == "chili_bar_0_2500m"
    assert coverage["production_corridor_point_count"] == 799
    assert coverage["production_corridor_station_range_m"] == [0.0, 2531.325]
    assert "not an anchor blocker" in coverage["coverage_gap"]
    assert "Resolved July 17 2026" in coverage["coverage_gap"]
    window_coverage = coverage["full_reach_window_coverage"]
    assert window_coverage["window_count"] == 8
    assert window_coverage["covered_station_end_m"] == 49077.732
    assert window_coverage["covers_adopted_axis"] is True
    assert window_coverage["all_source_files_present"] is True


def test_south_fork_a1_acceptance_is_unblocked_with_p7_batched_reviews():
    status = _load_status()
    flow = status["flow_evidence"]
    acceptance = {
        entry["requirement"]: entry["status"] for entry in status["a1_acceptance"]
    }

    assert flow["primary_candidate"] == "CDEC CBR American River at Chili Bar"
    assert flow["reviewed_band_count"] == 3
    assert [band["planning_discharge_cfs"] for band in flow["reviewed_bands"]] == [
        900.0,
        1600.0,
        3000.0,
    ]
    assert "P7 owner packet" in flow["review_routing"]

    assert acceptance[
        "Fix NHD flowline conflict and re-anchor Chili Bar plus Folsom take-out."
    ] == "adopted"
    assert acceptance[
        "Extend corridor to the full Chili Bar-to-Folsom reach."
    ] == "extended_full_axis_window_sources_attached"
    assert acceptance["Attach official low/reference/high flow bands."] == (
        "attached_pending_human_review_non_blocking"
    )
    assert acceptance[
        "Re-station all 20 catalog markers with no order interpolation."
    ] == "stationed_on_adopted_axis_no_order_interpolation"
    assert acceptance[
        "Exit gate: conflict resolved and zero South Fork markers use order interpolation."
    ] == "met_for_stationing"

    reviews = status["pending_human_review"]
    assert len(reviews) == 4
    assert all(
        item["blocking"] is False
        and item["review_batch"] == "p7_owner_review_packet"
        for item in reviews
    )
