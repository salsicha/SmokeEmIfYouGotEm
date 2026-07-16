import json
from pathlib import Path

from raftsim.south_fork_a1_downstream_anchor_decision import (
    FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_CANDIDATES_GEOJSON_RELATIVE_PATH,
    FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_PACKET_RELATIVE_PATH,
    build_south_fork_a1_downstream_anchor_decision_geojson,
    build_south_fork_a1_downstream_anchor_decision_packet,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_packet() -> dict:
    return json.loads(
        (REPO_ROOT / FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_PACKET_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _load_geojson() -> dict:
    return json.loads(
        (
            REPO_ROOT / FULL_REACH_DOWNSTREAM_ANCHOR_DECISION_CANDIDATES_GEOJSON_RELATIVE_PATH
        ).read_text(encoding="utf-8")
    )


def test_south_fork_a1_downstream_anchor_decision_packet_is_reproducible():
    generated = build_south_fork_a1_downstream_anchor_decision_packet(REPO_ROOT)
    committed = _load_packet()

    assert generated == committed
    assert committed["schema"] == "raftsim.south_fork.a1_downstream_anchor_decision_packet.v1"
    assert committed["status"] == "decision_packet_ready_exact_anchor_not_selected"
    assert committed["production_promoted"] is False


def test_south_fork_a1_downstream_anchor_decision_options_record_20_5_and_21_0_candidates():
    packet = _load_packet()
    options = packet["options"]

    assert len(options) == 2
    assert [option["published_river_mile"] for option in options] == [20.5, 21.0]
    assert options[0]["station_id"] == "salmon_falls_bridge_takeout_published_20_5_miles"
    assert options[1]["station_id"] == "full_run_downstream_window_published_21_0_miles"
    assert packet["candidate_window"]["minimum_station_m"] == 32991.552
    assert packet["candidate_window"]["maximum_station_m"] == 33796.224
    assert packet["candidate_window"]["station_delta_m"] == 804.672
    assert packet["decision_required"]["exact_anchor_selected"] is False
    assert len(packet["decision_required"]["must_record_before_promotion"]) == 6


def test_south_fork_a1_downstream_anchor_decision_visual_inputs_are_hash_locked():
    packet = _load_packet()
    visual = packet["visual_review_inputs"]

    assert visual["lower_gorge_window"]["window_id"] == "lower_gorge_to_salmon_falls_28500_32991m"
    assert visual["anchor_review_window"]["window_id"] == "salmon_falls_folsom_review_32991_33796m"
    for window in visual.values():
        assert len(window["edge_report"]["sha256"]) == 64
        for artifact in window["derived_artifacts"].values():
            assert len(artifact["sha256"]) == 64
            assert (REPO_ROOT / artifact["path"]).exists()


def test_south_fork_a1_downstream_anchor_decision_geojson_is_reproducible_and_review_gated():
    generated = build_south_fork_a1_downstream_anchor_decision_geojson(REPO_ROOT)
    committed = _load_geojson()

    assert generated == committed
    assert committed["type"] == "FeatureCollection"
    assert committed["status"] == "decision_packet_ready_exact_anchor_not_selected"
    assert len(committed["features"]) == 3
    assert [feature["geometry"]["type"] for feature in committed["features"]] == [
        "Point",
        "Point",
        "LineString",
    ]
    for feature in committed["features"]:
        assert feature["properties"]["can_bind_editor_geometry"] is False
        assert feature["properties"]["can_bind_solver_windows"] is False
        assert feature["properties"]["production_promoted"] is False


def test_south_fork_a1_downstream_anchor_decision_blocks_promotion():
    packet = _load_packet()
    gate = packet["promotion_gate"]

    assert gate["can_select_anchor_without_human_review"] is False
    assert gate["can_crop_to_final_downstream_anchor"] is False
    assert gate["can_promote_full_reach_centerline"] is False
    assert gate["can_regenerate_rapid_stationing"] is False
    assert gate["can_import_unreal_full_reach_landscape"] is False
    assert gate["can_bind_named_rapid_geometry"] is False
    assert gate["can_bind_solver_windows"] is False
