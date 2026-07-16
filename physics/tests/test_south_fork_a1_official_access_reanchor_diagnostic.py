import json
from pathlib import Path

from raftsim.south_fork_a1_official_access_reanchor_diagnostic import (
    FULL_REACH_OFFICIAL_ACCESS_REANCHOR_DIAGNOSTIC_RELATIVE_PATH,
    FULL_REACH_OFFICIAL_ACCESS_REANCHOR_ROUTE_GEOJSON_RELATIVE_PATH,
    build_south_fork_a1_official_access_reanchor_diagnostic,
    build_south_fork_a1_official_access_reanchor_route_geojson,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_diagnostic() -> dict:
    return json.loads(
        (
            REPO_ROOT / FULL_REACH_OFFICIAL_ACCESS_REANCHOR_DIAGNOSTIC_RELATIVE_PATH
        ).read_text(encoding="utf-8")
    )


def _load_geojson() -> dict:
    return json.loads(
        (REPO_ROOT / FULL_REACH_OFFICIAL_ACCESS_REANCHOR_ROUTE_GEOJSON_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_south_fork_a1_official_access_reanchor_diagnostic_is_reproducible():
    generated = build_south_fork_a1_official_access_reanchor_diagnostic(REPO_ROOT)
    committed = _load_diagnostic()

    assert generated == committed
    assert (
        committed["schema"]
        == "raftsim.south_fork.a1_official_access_reanchor_diagnostic.v1"
    )
    assert (
        committed["status"]
        == "official_access_seed_snaps_to_nhd_pool_but_route_length_disagrees_with_published_run"
    )
    assert committed["production_promoted"] is False


def test_south_fork_a1_official_access_reanchor_diagnostic_snaps_seed_but_blocks_route():
    diagnostic = _load_diagnostic()
    official_seed = diagnostic["official_access_seed"]
    route = diagnostic["route_path"]

    assert official_seed["name"] == "Salmon Falls  Lower Water Raft Take-out"
    assert official_seed["nearest_graph_node_distance_m"] == 117.705
    assert official_seed["snaps_to_candidate_pool_within_warning_threshold"] is True
    assert route["path_edge_count"] == 169
    assert route["path_geometry_length_m"] > 49000.0
    assert route["path_geometry_length_miles"] > 30.0
    assert route["published_run_length_miles"] == 21.0
    assert route["geometry_minus_published_run_length_m"] > 15000.0
    assert route["length_disagrees_with_published_run"] is True


def test_south_fork_a1_official_access_reanchor_route_geojson_is_reproducible():
    generated = build_south_fork_a1_official_access_reanchor_route_geojson(REPO_ROOT)
    committed = _load_geojson()

    assert generated == committed
    assert (
        committed["schema"]
        == "raftsim.south_fork.a1_official_access_reanchor_route.geojson.v1"
    )
    assert committed["type"] == "FeatureCollection"
    assert committed["production_promoted"] is False
    assert len(committed["features"]) == 3
    route = next(
        feature
        for feature in committed["features"]
        if feature["id"] == "chili_bar_to_official_salmon_falls_access_nhd_path"
    )
    assert route["geometry"]["type"] == "LineString"
    assert route["properties"]["path_edge_count"] == 169
    assert route["properties"]["path_point_count"] > 160
    assert route["properties"]["can_bind_editor_geometry"] is False
    assert route["properties"]["can_bind_solver_windows"] is False


def test_south_fork_a1_official_access_reanchor_diagnostic_blocks_promotion():
    gate = _load_diagnostic()["promotion_gate"]

    assert gate["can_use_official_seed_for_route_reanchor_planning"] is True
    assert gate["can_promote_reanchored_route"] is False
    assert gate["can_crop_to_final_downstream_anchor"] is False
    assert gate["can_restation_named_rapids"] is False
    assert gate["can_import_unreal_full_reach_landscape"] is False
    assert gate["can_bind_named_rapid_geometry"] is False
    assert gate["can_bind_solver_windows"] is False
