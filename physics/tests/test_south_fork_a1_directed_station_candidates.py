import json
from pathlib import Path

from raftsim.south_fork_a1_directed_station_candidates import (
    FULL_REACH_DIRECTED_STATION_CANDIDATES_RELATIVE_PATH,
    build_south_fork_a1_directed_station_candidates,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_candidates() -> dict:
    return json.loads(
        (REPO_ROOT / FULL_REACH_DIRECTED_STATION_CANDIDATES_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_south_fork_a1_directed_station_candidates_are_reproducible():
    generated = build_south_fork_a1_directed_station_candidates(REPO_ROOT)
    committed = _load_candidates()

    assert generated == committed
    assert committed["schema"] == (
        "raftsim.south_fork.a1_directed_station_candidates.v1"
    )
    assert committed["status"] == (
        "review_only_directed_nhd_station_candidates_not_promoted"
    )
    assert committed["production_promoted"] is False


def test_south_fork_a1_directed_station_candidates_record_chain_shape():
    candidates = _load_candidates()
    direction = candidates["direction_evidence"]

    assert direction["flowdir_values"] == [1]
    assert direction["source_record_count"] == 198
    assert direction["directed_edge_count_from_chili_bar"] == 184
    assert direction["upstream_of_chili_bar_edge_count"] == 14
    assert direction["branch_node_count"] == 0
    assert direction["merge_node_count"] == 0
    assert direction["route_axis_length_m"] == 63584.57365
    assert direction["catalog_full_run_length_m"] == 33796.224
    assert direction["route_axis_exceeds_catalog_full_run"] is True
    assert direction["terminal_node_lon_lat"] == [-121.1396311, 38.7112784]


def test_south_fork_a1_directed_station_candidates_record_anchor_points():
    candidates = _load_candidates()
    anchors = candidates["source_anchor_station_candidates"]
    coloma = anchors["coloma_bridge_checkpoint"]
    downstream = anchors["downstream_source_window"]
    lower = downstream["minimum_source_mile_candidate"]
    upper = downstream["maximum_source_mile_candidate"]

    assert coloma["published_river_mile"] == 5.6
    assert coloma["station_m"] == 9012.3264
    assert coloma["lon_lat"] == [-120.7812546, 38.7718837]
    assert coloma["current_seed_station_m"] == 5250.41934
    assert coloma["current_seed_minus_candidate_station_m"] == -3761.90706
    assert coloma["current_seed_to_candidate_geodesic_distance_m"] == 1722.344
    assert coloma["validation_status"] == (
        "candidate_review_point_generated_current_seed_still_unresolved"
    )

    assert lower["published_river_mile"] == 20.5
    assert lower["station_m"] == 32991.552
    assert lower["lon_lat"] == [-120.938291, 38.8220775]
    assert upper["published_river_mile"] == 21.0
    assert upper["station_m"] == 33796.224
    assert upper["lon_lat"] == [-120.9441395, 38.8246066]
    assert downstream["window_length_m"] == 804.672


def test_south_fork_a1_directed_station_candidates_keep_rapids_review_only():
    candidates = _load_candidates()
    rapids = {
        rapid["name"]: rapid
        for rapid in candidates["named_rapid_station_candidates"]
    }
    gate = candidates["promotion_gate"]

    assert len(rapids) == 20
    troublemaker = rapids["Troublemaker"]
    assert troublemaker["published_river_mile"] == 5.2
    assert troublemaker["station_m"] == 8368.5888
    assert troublemaker["lon_lat"] == [-120.7767335, 38.7763812]
    assert troublemaker["can_bind_editor_geometry"] is False
    assert troublemaker["can_bind_solver_window"] is False
    assert all(
        rapid["geometry_status"]
        == "review_candidate_from_directed_nhd_chain_not_authoritative"
        for rapid in rapids.values()
    )
    assert gate["can_enable_south_fork_editor_geometry"] is False
    assert gate["can_bind_meat_grinder_troublemaker_solver_windows"] is False
    assert gate["can_restation_catalog_from_candidates"] is False
