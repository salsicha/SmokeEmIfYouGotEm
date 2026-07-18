import json
from pathlib import Path

from raftsim.south_fork_a1_window_source_pulls import (
    FULL_REACH_WINDOW_SOURCE_PULL_PLAN_RELATIVE_PATH,
    build_south_fork_a1_window_source_pull_plan,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_plan() -> dict:
    return json.loads(
        (REPO_ROOT / FULL_REACH_WINDOW_SOURCE_PULL_PLAN_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_south_fork_a1_window_source_pull_plan_is_reproducible():
    generated = build_south_fork_a1_window_source_pull_plan(REPO_ROOT)
    committed = _load_plan()

    assert generated == committed
    assert committed["schema"] == "raftsim.south_fork.a1_window_source_pull_plan.v1"
    assert committed["status"] == "bounded_window_source_requests_planned_not_downloaded"
    assert committed["production_promoted"] is False
    assert committed["policy"]["downloads_performed"] is False


def test_south_fork_a1_window_source_pull_plan_covers_every_window():
    plan = _load_plan()
    summary = plan["coverage_summary"]
    windows = plan["windows"]

    assert summary["window_count"] == 8
    assert summary["planned_download_count"] == 0
    assert summary["planned_request_count"] == 16
    assert summary["all_windows_have_terrain_and_imagery_requests"] is True
    assert windows[0]["window_id"] == "chili_bar_existing_pilot_0_2500m"
    assert windows[-1]["window_id"] == "salmon_falls_takeout_approach_41500_49077m"
    assert windows[-1]["station_end_m"] == 49077.732
    assert windows[0]["existing_artifact"].endswith("chili_bar_reach_0_2500m/manifest.json")
    assert all(window["route_point_count"] > 0 for window in windows)


def test_south_fork_a1_window_source_pull_plan_records_route_basis_per_window():
    plan = _load_plan()
    basis_by_id = {window["window_id"]: window["route_basis"] for window in plan["windows"]}

    assert plan["inputs"]["adopted_route_geojson"].endswith("full_reach_adopted_route.geojson")
    for window in plan["windows"]:
        if window["station_end_m"] <= 33796.224:
            assert basis_by_id[window["window_id"]] == (
                "directed_route_clip_21_0_mile_candidate"
            )
        else:
            assert basis_by_id[window["window_id"]] == "adopted_route_axis"
    assert basis_by_id["below_full_run_alias_33796_41500m"] == "adopted_route_axis"
    assert basis_by_id["salmon_falls_takeout_approach_41500_49077m"] == "adopted_route_axis"


def test_south_fork_a1_window_source_pull_plan_uses_bounded_official_services():
    plan = _load_plan()
    for window in plan["windows"]:
        terrain = window["terrain_3dep_export"]
        aerial = window["aerial_naip_export"]
        bbox = window["bounds_epsg3857_buffered"]

        assert len(bbox) == 4
        assert bbox[0] < bbox[2]
        assert bbox[1] < bbox[3]
        assert "3DEPElevation/ImageServer/exportImage" in terrain["query_url"]
        assert "NAIP/USDA_CONUS_PRIME/ImageServer/exportImage" in aerial["query_url"]
        assert "bboxSR=3857" in terrain["query_url"]
        assert "imageSR=3857" in aerial["query_url"]
        assert terrain["downloaded"] is False
        assert aerial["downloaded"] is False
        assert window["production_promoted"] is False


def test_south_fork_a1_window_source_pull_plan_blocks_promotion():
    plan = _load_plan()
    gate = plan["promotion_gate"]

    assert gate["can_download_without_review"] is False
    assert gate["can_promote_source_assets"] is False
    assert gate["can_generate_full_reach_landscapes"] is False
    assert len(gate["exit_criteria"]) == 4
