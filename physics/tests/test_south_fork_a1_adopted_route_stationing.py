import json
from pathlib import Path

from raftsim.south_fork_a1_adopted_route_stationing import (
    build_south_fork_a1_adopted_route_geojson,
    build_south_fork_a1_adopted_route_stationing,
)
from raftsim.south_fork_a1_stationing import (
    A1_ADOPTION_DECISION_SOURCE,
    FULL_REACH_ADOPTED_ROUTE_GEOJSON_RELATIVE_PATH,
    FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(relative_path: str) -> dict:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def test_adopted_route_stationing_is_reproducible_and_records_the_decision():
    generated = build_south_fork_a1_adopted_route_stationing(REPO_ROOT)
    committed = _load(FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH)

    assert generated == committed
    assert committed["schema"] == "raftsim.south_fork.a1_adopted_route_stationing.v1"
    assert committed["status"] == (
        "adopted_official_access_anchor_route_stationing_active"
    )
    assert committed["production_promoted"] is False

    decision = committed["decision"]
    assert decision["decision_source"] == A1_ADOPTION_DECISION_SOURCE
    assert decision["decision_source"] == "release-1.0-plan-v2 §6, July 17 2026"
    assert decision["decision_id"] == "south_fork_a1_source_mile_access_authority"
    assert len(decision["rejected_anchor_candidates"]) == 2
    assert all(
        candidate["disposition"]
        == "rejected_as_anchor_retained_as_alias_metadata"
        and candidate["distance_to_official_raft_takeout_m"] > 9000.0
        for candidate in decision["rejected_anchor_candidates"]
    )
    assert decision["supersedes_promotion_gates_in"]
    assert "no evidence is deleted" in decision["evidence_policy"]


def test_adopted_downstream_anchor_is_the_official_salmon_falls_takeout():
    committed = _load(FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH)
    anchor = committed["downstream_anchor"]

    assert anchor["name"] == "Salmon Falls  Lower Water Raft Take-out"
    assert anchor["fid"] == 50927
    assert anchor["gisid"] == "GIS0005556"
    assert anchor["authority"] == "california_state_parks_parking_points"
    assert anchor["station_m"] == 49077.732
    assert anchor["snap_distance_m"] == 117.705
    assert anchor["pending_human_review"]["blocking"] is False
    assert anchor["pending_human_review"]["review_batch"] == "p7_owner_review_packet"

    axis = committed["station_axis"]
    assert axis["axis_id"] == "adopted_nhd_directed_mainstem_chain_v1"
    assert axis["adopted_route_length_m"] == 49077.732
    assert axis["cross_check"]["matches_divergence_audit"] is True
    assert axis["cross_check"]["delta_m"] == 0.0


def test_published_miles_are_alias_metadata_with_recorded_divergence():
    committed = _load(FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH)
    aliases = committed["published_mile_aliases"]

    assert aliases["alias_policy"] == (
        "published_river_miles_are_alias_metadata_not_anchors"
    )
    assert "not used as anchors" in aliases["divergence_note"]
    by_miles = {alias["published_miles"]: alias for alias in aliases["aliases"]}
    assert set(by_miles) == {20.5, 21.0}
    assert all(alias["rejected_as_anchor"] is True for alias in aliases["aliases"])
    assert by_miles[20.5]["station_m_on_adopted_axis"] == 32991.552
    assert by_miles[21.0]["station_m_on_adopted_axis"] == 33796.224
    # These reproduce the committed source-mile divergence audit exactly.
    assert by_miles[21.0]["remaining_axis_distance_to_adopted_anchor_m"] == 15281.508
    assert by_miles[21.0]["geodesic_distance_to_adopted_anchor_m"] == 10426.611
    assert by_miles[20.5]["remaining_axis_distance_to_adopted_anchor_m"] == 16086.18
    assert aliases["excess_axis_length_after_published_full_run_m"] == 15281.508


def test_all_20_rapids_station_on_the_adopted_axis_without_fabricated_geometry():
    committed = _load(FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH)
    rapids = committed["rapid_stations"]
    summary = committed["rapid_station_summary"]

    assert len(rapids) == 20
    assert summary["rapid_count"] == 20
    assert summary["stations_monotonic_increasing"] is True
    assert summary["order_interpolation_used"] is False
    assert summary["all_stations_within_adopted_route"] is True

    assert rapids[0]["name"] == "Chili Bar Hole"
    assert rapids[0]["station_m"] == 0.0
    assert rapids[-1]["name"] == "Surprise"
    assert rapids[-1]["station_m"] == 31060.3392
    troublemaker = next(rapid for rapid in rapids if rapid["name"] == "Troublemaker")
    assert troublemaker["station_m"] == 8368.5888
    assert all(
        rapid["stationing_basis"]
        == "published_mile_alias_projected_along_adopted_axis"
        and rapid["exact_geometry_status"]
        == "stationing_only_exact_geometry_authoring_pending_p3_p4"
        and rapid["pending_human_review"] is True
        and rapid["review_batch"] == "p7_owner_review_packet"
        and len(rapid["lon_lat"]) == 2
        for rapid in rapids
    )


def test_adoption_unblocks_stationing_and_binding_but_promotes_no_realism_claims():
    committed = _load(FULL_REACH_ADOPTED_ROUTE_STATIONING_RELATIVE_PATH)
    gate = committed["promotion_gate"]

    assert gate["can_use_adopted_axis_for_stationing"] is True
    assert gate["can_restation_named_rapids"] is True
    assert gate["can_crop_to_final_downstream_anchor"] is True
    assert gate["can_bind_solver_windows"] is True
    assert gate["can_bind_named_rapid_geometry"] is False
    assert gate["can_import_unreal_full_reach_landscape"] is False
    assert gate["can_claim_photoreal_or_gameplay_realism"] is False

    reviews = committed["pending_human_review"]
    assert {item["review_id"] for item in reviews} == {
        "salmon_falls_takeout_bank_landing_confirmation",
        "rapid_station_realism_guide_confirmation",
        "published_mile_alias_divergence_note_review",
        "flow_band_guide_outfitter_validation",
    }
    assert all(
        item["blocking"] is False
        and item["review_batch"] == "p7_owner_review_packet"
        for item in reviews
    )


def test_adopted_route_geojson_matches_the_stationing_artifact():
    generated = build_south_fork_a1_adopted_route_geojson(REPO_ROOT)
    committed = _load(FULL_REACH_ADOPTED_ROUTE_GEOJSON_RELATIVE_PATH)

    assert generated == committed
    assert committed["schema"] == "raftsim.south_fork.a1_adopted_route.geojson.v1"
    assert committed["decision_source"] == A1_ADOPTION_DECISION_SOURCE
    assert committed["production_promoted"] is False
    assert committed["feature_count"] == 25

    by_kind: dict[str, int] = {}
    for feature in committed["features"]:
        kind = feature["properties"]["marker_kind"]
        by_kind[kind] = by_kind.get(kind, 0) + 1
    assert by_kind == {
        "adopted_upstream_anchor": 1,
        "adopted_downstream_anchor_official_access": 1,
        "adopted_route_centerline": 1,
        "published_mile_alias": 2,
        "named_rapid_station_adopted_axis": 20,
    }
    route = next(
        feature
        for feature in committed["features"]
        if feature["properties"]["marker_kind"] == "adopted_route_centerline"
    )
    assert route["properties"]["station_end_m"] == 49077.732
    assert route["properties"]["point_count"] == len(
        route["geometry"]["coordinates"]
    )
    assert "photoreal or gameplay realism claims" in committed["policy"][
        "forbidden_use"
    ]
