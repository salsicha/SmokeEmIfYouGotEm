import json
from pathlib import Path

from raftsim.south_fork_a1_source_mile_access_options import (
    FULL_REACH_SOURCE_MILE_ACCESS_OPTION_MATRIX_RELATIVE_PATH,
    FULL_REACH_SOURCE_MILE_ACCESS_OPTION_POINTS_GEOJSON_RELATIVE_PATH,
    build_south_fork_a1_source_mile_access_option_matrix,
    build_south_fork_a1_source_mile_access_option_points_geojson,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_matrix() -> dict:
    return json.loads(
        (REPO_ROOT / FULL_REACH_SOURCE_MILE_ACCESS_OPTION_MATRIX_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def _load_geojson() -> dict:
    return json.loads(
        (
            REPO_ROOT / FULL_REACH_SOURCE_MILE_ACCESS_OPTION_POINTS_GEOJSON_RELATIVE_PATH
        ).read_text(encoding="utf-8")
    )


def test_south_fork_a1_source_mile_access_option_matrix_is_reproducible():
    generated = build_south_fork_a1_source_mile_access_option_matrix(REPO_ROOT)
    committed = _load_matrix()

    assert generated == committed
    assert committed["schema"] == "raftsim.south_fork.a1_source_mile_access_option_matrix.v1"
    assert committed["status"] == "source_mile_access_options_ready_for_review_no_route_promoted"
    assert committed["production_promoted"] is False


def test_south_fork_a1_source_mile_access_option_matrix_measures_all_official_access_seeds():
    matrix = _load_matrix()
    options = {option["option_id"]: option for option in matrix["official_access_options"]}

    assert len(options) == 5
    assert matrix["summary"]["official_access_option_count"] == 5
    assert matrix["summary"]["options_within_snap_warning_threshold"] == 4
    assert matrix["summary"]["manual_snap_review_count"] == 1
    assert matrix["summary"]["source_mile_conflict_count"] == 4
    assert matrix["summary"]["all_access_options_conflict_with_published_source_miles"] is True
    assert matrix["summary"]["minimum_source_station_miles"] > 30.0
    assert matrix["summary"]["maximum_source_station_miles"] > 32.0
    primary = options["official_access_50927"]
    assert primary["name"] == "Salmon Falls  Lower Water Raft Take-out"
    assert primary["source_station_miles"] == 30.495
    assert primary["nearest_graph_node_distance_m"] == 117.705
    assert primary["review_status"] == "official_access_seed_snaps_but_source_mile_conflict"


def test_south_fork_a1_source_mile_access_options_compare_published_conventions():
    matrix = _load_matrix()

    assert [item["published_miles"] for item in matrix["published_source_mile_conventions"]] == [
        20.5,
        21.0,
    ]
    for option in matrix["official_access_options"]:
        deltas = {delta["convention_id"]: delta for delta in option["convention_deltas"]}
        assert set(deltas) == {
            "salmon_falls_20_5_mile_basis",
            "full_run_21_0_mile_basis",
        }
        assert deltas["full_run_21_0_mile_basis"]["absolute_delta_m"] > 14000.0
        assert deltas["full_run_21_0_mile_basis"]["within_one_mile"] is False
        assert option["can_promote_as_final_anchor"] is False
        assert option["can_select_without_guide_geospatial_review"] is False


def test_south_fork_a1_source_mile_access_option_points_geojson_is_reproducible():
    generated = build_south_fork_a1_source_mile_access_option_points_geojson(REPO_ROOT)
    committed = _load_geojson()

    assert generated == committed
    assert (
        committed["schema"]
        == "raftsim.south_fork.a1_source_mile_access_option_points.geojson.v1"
    )
    assert committed["type"] == "FeatureCollection"
    assert committed["production_promoted"] is False
    assert len(committed["features"]) == 5
    for feature in committed["features"]:
        assert feature["geometry"]["type"] == "Point"
        assert feature["properties"]["production_promoted"] is False
        assert feature["properties"]["can_bind_editor_geometry"] is False
        assert feature["properties"]["can_bind_solver_windows"] is False


def test_south_fork_a1_source_mile_access_option_matrix_blocks_promotion():
    gate = _load_matrix()["promotion_gate"]

    assert gate["can_select_endpoint_from_matrix_alone"] is False
    assert gate["can_promote_current_nhd_route"] is False
    assert gate["can_crop_to_final_downstream_anchor"] is False
    assert gate["can_restation_named_rapids"] is False
    assert gate["can_import_unreal_full_reach_landscape"] is False
    assert gate["can_bind_named_rapid_geometry"] is False
    assert gate["can_bind_solver_windows"] is False
