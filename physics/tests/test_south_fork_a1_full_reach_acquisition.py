import json
from pathlib import Path

from raftsim.south_fork_a1_full_reach_acquisition import (
    FULL_REACH_ACQUISITION_RELATIVE_PATH,
    FULL_REACH_REVIEW_ENVELOPE_WGS84,
    build_south_fork_a1_full_reach_acquisition_plan,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_plan() -> dict:
    return json.loads(
        (REPO_ROOT / FULL_REACH_ACQUISITION_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_south_fork_a1_full_reach_acquisition_plan_is_reproducible():
    generated = build_south_fork_a1_full_reach_acquisition_plan(REPO_ROOT)
    committed = _load_plan()

    assert generated == committed
    assert committed["schema"] == (
        "raftsim.south_fork.a1_full_reach_acquisition_plan.v1"
    )
    assert committed["status"] == "planned_no_source_downloaded_not_geometry_authority"
    assert committed["production_promoted"] is False
    assert committed["review_envelope_wgs84"] == FULL_REACH_REVIEW_ENVELOPE_WGS84
    assert committed["review_envelope_policy"][
        "must_clip_to_reviewed_anchors_before_promotion"
    ] is True


def test_south_fork_a1_full_reach_acquisition_records_metadata_probe():
    plan = _load_plan()
    probe = plan["metadata_probe_2026_07_16"]
    results = {result["source_class"]: result for result in probe["results"]}

    assert probe["status"] == "metadata_only_no_archives_tiles_or_media_downloaded"
    assert set(results) == {"hydrography", "terrain_dem_or_lidar", "aerial_imagery"}
    assert results["hydrography"]["http_status"] == 200
    assert results["hydrography"]["item_total"] == 38
    assert results["terrain_dem_or_lidar"]["http_status"] == 200
    assert results["terrain_dem_or_lidar"]["item_total"] == 0
    assert results["aerial_imagery"]["http_status"] == 200
    assert results["aerial_imagery"]["item_total"] == 0
    assert "bbox=-121.12,38.68,-120.7,38.86" in results["hydrography"][
        "query_url"
    ]
    assert "USGS 3DEP ImageServer" in results["terrain_dem_or_lidar"]["next_action"]
    assert "USDA/APFO NAIP ImageServer" in results["aerial_imagery"]["next_action"]


def test_south_fork_a1_full_reach_acquisition_keeps_anchor_gates_explicit():
    plan = _load_plan()
    anchors = {
        anchor["anchor_id"]: anchor for anchor in plan["anchor_review_targets"]
    }

    assert set(anchors) == {
        "chili_bar_put_in",
        "coloma_bridge_checkpoint",
        "folsom_reservoir_takeout",
    }
    assert anchors["chili_bar_put_in"]["current_seed_lon_lat"] == [
        -120.7199431,
        38.7786168,
    ]
    assert anchors["coloma_bridge_checkpoint"]["published_station_m"] == 9012.3264
    assert anchors["coloma_bridge_checkpoint"]["published_station_miles"] == 5.6
    assert anchors["coloma_bridge_checkpoint"][
        "maximum_allowed_station_delta_m_before_manual_review"
    ] == 250.0
    assert anchors["folsom_reservoir_takeout"]["current_seed_lon_lat"] is None
    assert (
        anchors["folsom_reservoir_takeout"]["current_seed_status"]
        == "missing_exact_anchor"
    )
    assert anchors["folsom_reservoir_takeout"]["published_run_length_m"] == 33796.224
    assert anchors["folsom_reservoir_takeout"]["published_run_length_miles"] == 21.0


def test_south_fork_a1_full_reach_acquisition_records_source_pull_classes():
    plan = _load_plan()
    source_classes = {
        item["source_class"]: item for item in plan["source_pull_queue"]
    }

    assert set(source_classes) == {
        "hydrography",
        "terrain_dem_or_lidar",
        "aerial_imagery",
        "flow_history",
        "guide_and_access_review",
    }
    assert (
        source_classes["hydrography"]["status"]
        == "metadata_probe_passed_products_available"
    )
    assert "bbox=-121.12,38.68,-120.7,38.86" in source_classes["hydrography"]["url"]
    assert source_classes["terrain_dem_or_lidar"]["status"] == (
        "tnm_metadata_zero_hits_use_official_3dep_image_service"
    )
    assert source_classes["terrain_dem_or_lidar"]["target_artifacts"] == [
        "terrain/full_reach_3dep_tile_manifest.json",
        "terrain/full_reach_windowed_heightfields/",
    ]
    assert source_classes["aerial_imagery"]["status"] == (
        "tnm_metadata_zero_hits_use_official_naip_image_service"
    )
    assert source_classes["aerial_imagery"]["target_artifacts"] == [
        "imagery/full_reach_naip_tile_manifest.json",
        "imagery/full_reach_windowed_drapes/",
    ]
    assert (
        source_classes["flow_history"]["status"]
        == "attached_but_needs_full_window_review"
    )
    assert (
        source_classes["guide_and_access_review"]["status"]
        == "planned_link_and_annotation_only"
    )


def test_south_fork_a1_full_reach_acquisition_blocks_geometry_promotion():
    plan = _load_plan()
    gate = plan["promotion_gate"]
    requirements = {
        item["requirement"]: item["acceptance"]
        for item in plan["route_solution_requirements"]
    }

    assert gate["can_enable_south_fork_editor_geometry"] is False
    assert gate["can_bind_meat_grinder_troublemaker_solver_windows"] is False
    assert len(gate["exit_criteria"]) == 5
    assert (
        "Select a directed South Fork American mainstem graph from Chili Bar to Folsom Reservoir."
        in requirements
    )
    assert (
        "Validate Coloma checkpoint before projecting Gorge rapids."
        in requirements
    )
    assert "within 250 m" in requirements[
        "Validate Coloma checkpoint before projecting Gorge rapids."
    ]
    assert "review/named_rapid_station_alignment_review.json" in plan["planned_outputs"]
    assert "unreal/Content/RaftSim/River/named_rapid_editor_geometry.geojson" in plan[
        "planned_outputs"
    ]
