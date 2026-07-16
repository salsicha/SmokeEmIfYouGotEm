import json
from pathlib import Path

from raftsim.south_fork_a1_source_mile_access_decision import (
    FULL_REACH_SOURCE_MILE_ACCESS_DECISION_PACKET_RELATIVE_PATH,
    FULL_REACH_SOURCE_MILE_ACCESS_DECISION_SCHEMA,
    build_south_fork_a1_source_mile_access_decision_packet,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_packet() -> dict:
    return json.loads(
        (
            REPO_ROOT / FULL_REACH_SOURCE_MILE_ACCESS_DECISION_PACKET_RELATIVE_PATH
        ).read_text(encoding="utf-8")
    )


def test_south_fork_a1_source_mile_access_decision_packet_is_reproducible():
    generated = build_south_fork_a1_source_mile_access_decision_packet(REPO_ROOT)
    committed = _load_packet()

    assert generated == committed
    assert committed["schema"] == FULL_REACH_SOURCE_MILE_ACCESS_DECISION_SCHEMA
    assert committed["status"] == (
        "source_mile_access_decision_required_route_promotion_blocked"
    )
    assert committed["production_promoted"] is False


def test_south_fork_a1_source_mile_access_decision_packet_summarizes_evidence():
    evidence = _load_packet()["evidence_summary"]

    assert evidence["official_access_option_count"] == 5
    assert evidence["options_within_snap_warning_threshold"] == 4
    assert evidence["source_mile_conflict_count"] == 4
    assert evidence["manual_snap_review_count"] == 1
    assert evidence["all_access_options_conflict_with_published_source_miles"] is True
    assert evidence["primary_access_option_id"] == "official_access_50927"
    assert evidence["primary_access_source_station_miles"] == 30.495
    assert evidence["primary_access_snap_distance_m"] == 117.705
    assert evidence["official_access_source_station_miles"] == 30.495
    assert evidence["excess_source_path_after_21_miles_m"] > 15_000.0
    assert evidence["geodesic_21_mile_point_to_official_access_m"] > 10_000.0
    assert evidence["published_breakpoint_count"] == 2


def test_south_fork_a1_source_mile_access_decision_options_are_explicit():
    packet = _load_packet()
    options = {option["option_id"]: option for option in packet["decision_options"]}

    assert set(options) == {
        "retain_official_access_with_separate_simulation_station_axis",
        "select_guide_approved_access_endpoint_and_regenerate_route",
        "replace_current_nhd_axis_with_reviewed_centerline",
        "split_published_mile_convention_from_simulation_and_publication_axes",
    }
    assert options[
        "retain_official_access_with_separate_simulation_station_axis"
    ]["endpoint_option_id"] == "official_access_50927"
    assert options[
        "select_guide_approved_access_endpoint_and_regenerate_route"
    ]["candidate_option_ids"] == [
        "official_access_50817",
        "official_access_50924",
        "official_access_50927",
        "official_access_50930",
        "official_access_50933",
    ]
    assert all(
        option["route_promotion_allowed_without_review"] is False
        for option in options.values()
    )
    assert all(option["requires_route_regeneration"] is True for option in options.values())


def test_south_fork_a1_source_mile_access_decision_required_fields_block_regeneration():
    packet = _load_packet()
    record = packet["required_decision_record"]

    assert record["decision_id"] == "south_fork_a1_source_mile_access_authority"
    assert "selected_downstream_endpoint_lon_lat_or_centerline_geometry" in record[
        "required_fields"
    ]
    assert "simulation_station_axis_policy" in record["required_fields"]
    assert "published_mile_convention_policy" in record["required_fields"]
    assert "guide_reviewer" in record["required_fields"]
    assert "geospatial_reviewer" in record["required_fields"]
    assert "restationing all 20 South Fork named rapids" in record["blocks"]
    assert "binding any South Fork full-reach solver window" in record["blocks"]


def test_south_fork_a1_source_mile_access_decision_blocks_current_route_promotion():
    packet = _load_packet()
    mode = packet["current_operating_mode"]
    gate = packet["promotion_gate"]

    assert mode["mode"] == "review_only_no_endpoint_or_station_axis_selected"
    assert mode["can_promote_route_now"] is False
    assert mode["can_regenerate_corridor_windows_now"] is False
    assert mode["can_restation_named_rapids_now"] is False
    assert mode["can_bind_solver_windows_now"] is False
    assert gate["can_promote_current_nhd_route"] is False
    assert gate["can_select_endpoint_from_decision_packet_alone"] is False
    assert gate["can_crop_to_final_downstream_anchor"] is False
    assert gate["can_restation_named_rapids"] is False
    assert gate["can_bind_solver_windows"] is False


def test_south_fork_a1_source_mile_access_decision_has_post_decision_regeneration_plan():
    steps = {
        step["step_id"]: step
        for step in _load_packet()["post_decision_regeneration_plan"]
    }

    assert set(steps) == {
        "a1_regenerate_directed_route",
        "a1_regenerate_corridor_windows",
        "a1_restation_catalog_and_editor_markers",
        "a1_bind_first_solver_windows",
    }
    assert "simulation_station_axis_policy" in steps[
        "a1_regenerate_directed_route"
    ]["requires_decision_fields"]
    assert "guide_reviewer" in steps[
        "a1_restation_catalog_and_editor_markers"
    ]["requires_decision_fields"]
