import json
from pathlib import Path

from raftsim.south_fork_a1_route_graph import (
    FULL_REACH_ROUTE_GRAPH_DIAGNOSTIC_RELATIVE_PATH,
    build_south_fork_a1_route_graph_diagnostic,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_diagnostic() -> dict:
    return json.loads(
        (REPO_ROOT / FULL_REACH_ROUTE_GRAPH_DIAGNOSTIC_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_south_fork_a1_route_graph_diagnostic_is_reproducible():
    generated = build_south_fork_a1_route_graph_diagnostic(REPO_ROOT)
    committed = _load_diagnostic()

    assert generated == committed
    assert committed["schema"] == (
        "raftsim.south_fork.a1_full_reach_nhd_route_graph_diagnostic.v1"
    )
    assert committed["status"] == (
        "blocked_shortest_path_does_not_validate_coloma_checkpoint_"
        "and_folsom_anchor_missing"
    )
    assert committed["production_promoted"] is False


def test_south_fork_a1_route_graph_records_connected_pool_not_route():
    diagnostic = _load_diagnostic()
    source_pool = diagnostic["source_pool"]

    assert source_pool["feature_count"] == 198
    assert source_pool["node_count"] == 199
    assert source_pool["component_count"] == 1
    assert source_pool["component_node_counts"] == [199]
    assert source_pool["candidate_pool_is_single_connected_component"] is True
    assert source_pool["candidate_pool_is_ordered_route"] is False
    assert source_pool["selected_length_km_source_sum"] == 65.786574


def test_south_fork_a1_route_graph_preserves_anchor_mismatch():
    diagnostic = _load_diagnostic()
    anchors = diagnostic["anchor_diagnostics"]
    chili = anchors["chili_bar_put_in"]
    coloma = anchors["current_coloma_access_seed"]
    folsom = anchors["folsom_reservoir_takeout"]

    assert chili["nearest_graph_node_distance_m"] == 0.0
    assert chili["seed_lon_lat"] == [-120.7199431, 38.7786168]
    assert coloma["nearest_graph_node_distance_m"] == 56.304918
    assert coloma["graph_station_from_chili_bar_m"] == 5250.41934
    assert coloma["published_coloma_checkpoint_m"] == 9012.3264
    assert coloma["graph_minus_published_checkpoint_m"] == -3761.90706
    assert coloma["path_edge_count"] == 39
    assert coloma["shortest_path_does_not_validate_published_checkpoint"] is True
    assert coloma["anchor_identity_requires_review"] is True
    assert "does not by itself prove" in coloma["interpretation"]
    assert len(coloma["path_source_record_indices"]) == 39
    assert folsom["seed_status"] == "missing_exact_anchor"
    assert folsom["published_run_length_m"] == 33796.224


def test_south_fork_a1_route_graph_blocks_promotion_until_anchor_repair():
    diagnostic = _load_diagnostic()
    extent = diagnostic["graph_extent_diagnostic"]
    gate = diagnostic["promotion_gate"]

    assert extent["farthest_reachable_station_m"] == 63584.57365
    assert extent["farthest_minus_published_run_length_m"] == 29788.34965
    assert "directed route graph" in extent["interpretation"]
    assert gate["can_enable_south_fork_editor_geometry"] is False
    assert gate["can_bind_solver_windows"] is False
    assert gate["next_required_actions"] == [
        "Resolve whether the Coloma seed, graph traversal, or source-mile reference is causing the checkpoint mismatch.",
        "Attach an exact reviewed Salmon Falls/Folsom Reservoir take-out anchor.",
        "Solve a directed path through the named-flowline pool and clip it to reviewed anchors.",
        "Regenerate rapid stationing only after the Coloma checkpoint and full-run length checks pass.",
    ]
