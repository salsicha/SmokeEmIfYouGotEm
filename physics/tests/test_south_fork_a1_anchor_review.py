import json
from pathlib import Path

from raftsim.south_fork_a1_anchor_review import (
    FULL_REACH_ANCHOR_REVIEW_RELATIVE_PATH,
    build_south_fork_a1_full_reach_anchor_review,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_review() -> dict:
    return json.loads(
        (REPO_ROOT / FULL_REACH_ANCHOR_REVIEW_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_south_fork_a1_anchor_review_is_reproducible():
    generated = build_south_fork_a1_full_reach_anchor_review(REPO_ROOT)
    committed = _load_review()

    assert generated == committed
    assert committed["schema"] == (
        "raftsim.south_fork.a1_full_reach_anchor_review.v1"
    )
    assert committed["status"] == (
        "blocked_source_mile_anchors_recorded_exact_geometry_pending_review"
    )
    assert committed["production_promoted"] is False
    assert "Link-only factual indexing" in committed["rights_policy"]


def test_south_fork_a1_anchor_review_records_source_mile_anchors():
    review = _load_review()
    anchors = {anchor["anchor_id"]: anchor for anchor in review["anchor_reviews"]}

    assert set(anchors) == {
        "chili_bar_put_in",
        "coloma_bridge_checkpoint",
        "salmon_falls_folsom_reservoir_takeout",
    }
    chili = anchors["chili_bar_put_in"]
    coloma = anchors["coloma_bridge_checkpoint"]
    folsom = anchors["salmon_falls_folsom_reservoir_takeout"]

    assert chili["source_mile_evidence"][0]["published_river_mile"] == 0.0
    assert chili["current_seed_lon_lat"] == [-120.7199431, 38.7786168]
    assert coloma["source_mile_evidence"][0]["published_river_mile"] == 5.6
    assert coloma["source_mile_evidence"][0]["station_m"] == 9012.3264
    assert folsom["source_mile_evidence"][0]["published_river_mile"] == 20.5
    assert folsom["source_mile_evidence"][0]["station_m"] == 32991.552
    assert folsom["source_mile_evidence"][1]["published_river_mile"] == 21.0
    assert folsom["source_mile_evidence"][1]["station_m"] == 33796.224
    assert folsom["source_mile_window"]["delta_m"] == 804.672


def test_south_fork_a1_anchor_review_preserves_coloma_as_unresolved():
    review = _load_review()
    anchors = {anchor["anchor_id"]: anchor for anchor in review["anchor_reviews"]}
    coloma = anchors["coloma_bridge_checkpoint"]
    validation = coloma["shortest_path_validation"]

    assert validation["nearest_graph_node_distance_m"] == 56.304918
    assert validation["graph_station_from_chili_bar_m"] == 5250.41934
    assert validation["published_coloma_checkpoint_m"] == 9012.3264
    assert validation["graph_minus_published_checkpoint_m"] == -3761.90706
    assert validation["shortest_path_does_not_validate_published_checkpoint"] is True
    assert validation["anchor_identity_requires_review"] is True
    assert coloma["validation_status"] == (
        "shortest_path_does_not_validate_source_checkpoint"
    )
    assert "not a final rejection" in coloma["interpretation"]


def test_south_fork_a1_anchor_review_blocks_promotion():
    review = _load_review()
    source_ids = {source["source_id"] for source in review["source_leads"]}
    gate = review["promotion_gate"]

    assert source_ids == {
        "south_fork_american_rivers_mile_guide",
        "south_fork_americanwhitewater_map",
    }
    assert gate["can_promote_full_reach_centerline"] is False
    assert gate["can_enable_south_fork_editor_geometry"] is False
    assert gate["can_bind_solver_windows"] is False
    assert gate["can_regenerate_rapid_stationing"] is False
    assert len(review["decisions_needed"]) == 4
    assert "20.5-mile vs 21.0-mile" in review["decisions_needed"][1]
