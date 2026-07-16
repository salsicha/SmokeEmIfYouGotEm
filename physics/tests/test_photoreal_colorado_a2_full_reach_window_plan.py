import json
from pathlib import Path

from raftsim.colorado_a2_full_reach_window_plan import (
    COLORADO_A2_FULL_REACH_WINDOW_PLAN_RELATIVE_PATH,
    COLORADO_A2_FULL_REACH_WINDOW_PLAN_SCHEMA,
    COLORADO_RIVER_ID,
    FULL_REACH_WINDOW_COUNT,
    MAX_A2_WINDOW_LENGTH_M,
    MIN_A2_WINDOW_LENGTH_M,
    build_colorado_a2_full_reach_window_plan,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_plan() -> dict:
    return json.loads(
        (REPO_ROOT / COLORADO_A2_FULL_REACH_WINDOW_PLAN_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_colorado_a2_full_reach_window_plan_is_reproducible_and_fail_closed():
    generated = build_colorado_a2_full_reach_window_plan(REPO_ROOT)
    committed = _load_plan()

    assert generated == committed
    assert committed["schema"] == COLORADO_A2_FULL_REACH_WINDOW_PLAN_SCHEMA
    assert committed["river_id"] == COLORADO_RIVER_ID
    assert committed["status"] == (
        "a2_full_reach_window_plan_recorded_no_source_download_no_promotion"
    )
    assert committed["production_promoted"] is False
    assert committed["full_reach_source_pull_ready"] is False
    assert committed["unreal_import_allowed"] is False
    assert committed["rapid_stationing_promotion_allowed"] is False
    assert committed["solver_window_binding_allowed"] is False
    assert committed["promotion_gate"]["can_promote_a2"] is False


def test_colorado_a2_windows_cover_the_full_run_without_monolithic_corridor():
    plan = build_colorado_a2_full_reach_window_plan(REPO_ROOT)
    windows = plan["source_windows"]

    assert len(windows) == FULL_REACH_WINDOW_COUNT
    assert windows[0]["station_start_m"] == 0.0
    assert windows[-1]["station_end_m"] == plan["run_length_m"]
    assert any(window["existing_pilot_overlap"] for window in windows)
    assert sum(1 for window in windows if window["existing_pilot_overlap"]) == 1

    for previous, current in zip(windows[:-1], windows[1:], strict=True):
        assert previous["station_end_m"] == current["station_start_m"]
    for window in windows:
        assert MIN_A2_WINDOW_LENGTH_M <= window["window_length_m"] <= MAX_A2_WINDOW_LENGTH_M
        assert window["source_bbox_status"] == "pending_full_centerline_and_canyon_working_crs"
        assert window["promotion_status"] == "blocked_pending_source_pull_window_bbox_and_review"


def test_colorado_a2_assigns_every_cataloged_major_rapid_to_a_review_window():
    plan = build_colorado_a2_full_reach_window_plan(REPO_ROOT)
    windows_by_id = {window["window_id"]: window for window in plan["source_windows"]}
    assignments = plan["rapid_assignments"]
    assigned_names = {assignment["name"] for assignment in assignments}

    assert len(assignments) == 15
    assert {
        "Badger Creek",
        "Soap Creek",
        "House Rock",
        "Hance",
        "Sockdolager",
        "Horn Creek",
        "Granite",
        "Hermit",
        "Crystal",
        "Upset",
        "Lava Falls",
    }.issubset(assigned_names)
    for assignment in assignments:
        assert assignment["assigned_window_id"] in windows_by_id
        assert assignment["exact_stationing_promoted"] is False
        assert assignment["editor_binding_enabled"] is False
        assert assignment["solver_window_enabled"] is False
        assert assignment["stationing_status"].startswith("published_mile_only")
        assert "oarsman or guide line/feature review" in assignment[
            "required_reviews_before_promotion"
        ]

    summary = plan["rapid_assignment_summary"]
    assert summary["all_rapids_have_window"] is True
    assert summary["all_rapids_blocked_from_promotion"] is True
    assert summary["critical_rapid_count"] == 9
    assert "Lava Falls" in summary["critical_rapid_names"]
    assert any(window["review_priority"] == "critical" for window in windows_by_id.values())


def test_colorado_a2_records_source_requirements_before_any_download_or_import():
    plan = build_colorado_a2_full_reach_window_plan(REPO_ROOT)
    requirements = {
        requirement["requirement_id"]: requirement
        for requirement in plan["full_reach_source_requirements"]
    }

    assert set(requirements) == {
        "full_length_centerline",
        "terrain_dem",
        "aerial_imagery",
        "major_rapid_hydraulic_maps",
        "release_flow_context",
    }
    assert requirements["terrain_dem"]["source_family"] == "USGS 3DEP"
    assert requirements["aerial_imagery"]["source_family"] == "USDA NAIP"
    assert requirements["full_length_centerline"]["required_before"] == (
        "window_bbox_generation"
    )
    assert len(plan["promotion_gate"]["blocking_reasons"]) == 4
    assert any(
        "Generate per-window USGS 3DEP/NAIP source-pull requests" in action
        for action in plan["promotion_gate"]["next_required_actions"]
    )
