import json
from pathlib import Path

from raftsim.south_fork_a1_flow_window_review import (
    FULL_REACH_FLOW_WINDOW_REVIEW_RELATIVE_PATH,
    build_south_fork_a1_full_reach_flow_window_review,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_review() -> dict:
    return json.loads(
        (REPO_ROOT / FULL_REACH_FLOW_WINDOW_REVIEW_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_south_fork_a1_full_reach_flow_window_review_is_reproducible():
    generated = build_south_fork_a1_full_reach_flow_window_review(REPO_ROOT)
    committed = _load_review()

    assert generated == committed
    assert committed["schema"] == (
        "raftsim.south_fork.a1_full_reach_flow_window_review.v1"
    )
    assert committed["status"] == (
        "full_reach_flow_windows_attached_review_gated_not_promoted"
    )
    assert committed["production_promoted"] is False


def test_south_fork_a1_full_reach_flow_window_review_attaches_official_sources():
    review = _load_review()
    sources = review["official_source_selection"]
    evidence = review["evidence_windows"]

    assert sources["primary_station_id"] == "CBR"
    assert sources["secondary_station_id"] == "A25"
    assert "USGS 11445500" in sources["usgs_screening"][
        "inactive_or_no_current_series_site"
    ]
    assert evidence["thirty_day_context"]["summary"]["valid_day_count"] == 31
    assert evidence["water_year_2026_to_date"]["summary"]["valid_flow_day_count"] == 279
    assert evidence["multiyear_context"]["summary"]["valid_flow_day_count"] == 1740
    assert evidence["multiyear_context"]["summary"]["flow_peak_max_cfs"] == 38489.0


def test_south_fork_a1_full_reach_flow_window_review_records_band_frequency():
    review = _load_review()
    bands = {band["flow_band"]: band for band in review["reviewed_flow_bands"]}

    assert set(bands) == {"low_runnable", "median_runnable", "high_runnable"}
    assert bands["low_runnable"]["planning_discharge_cfs"] == 900.0
    assert bands["median_runnable"]["planning_discharge_cfs"] == 1600.0
    assert bands["high_runnable"]["planning_discharge_cfs"] == 3000.0
    assert bands["low_runnable"]["water_year_2026_to_date"][
        "days_peak_ge_threshold"
    ] == 245
    assert bands["median_runnable"]["water_year_2026_to_date"][
        "days_peak_ge_threshold"
    ] == 182
    assert bands["high_runnable"]["water_year_2026_to_date"][
        "days_peak_ge_threshold"
    ] == 48
    assert bands["high_runnable"]["multiyear_context"][
        "days_peak_ge_threshold"
    ] == 364
    assert all(
        band["full_reach_decision"]
        == "attached_for_full_reach_review_but_not_accepted_for_gameplay_or_visual_tuning"
        for band in bands.values()
    )


def test_south_fork_a1_full_reach_flow_window_review_stays_gate_locked():
    review = _load_review()
    scope = review["full_reach_scope"]
    policy = review["flow_dependent_feature_tuning_policy"]
    gate = review["promotion_gate"]

    assert scope["route_candidate_count"] == 2
    assert scope["named_rapid_candidate_count"] == 20
    assert scope["can_promote_full_reach_flow_bands"] is False
    assert policy["feature_forcing_allowed_now"] is False
    assert policy["feature_forcing_default_scale"] == 0.0
    assert gate["can_promote_flow_bands"] is False
    assert gate["can_bind_unreal_flow_variants"] is False
    assert gate["can_approve_named_rapid_water_windows"] is False
    assert gate["can_enable_feature_forcing_for_review_runs"] is False
    assert len(gate["exit_criteria"]) == 5
