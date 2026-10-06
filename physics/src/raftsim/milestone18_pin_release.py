"""Milestone 18 pin-release fixture: crew weight shift and swimmer release on a pinned raft."""
from __future__ import annotations

from typing import Any
from raftsim.feature_validation import build_crew_overboard_fixtures2_5d, evaluate_crew_overboard_fixture2_5d
from raftsim.math3d import Vec3
from raftsim.raft_coupling2_5d import CrewAction2_5D, CrewWeightTelemetry2_5D, build_default_crew_seats2_5d, build_default_raft_mass_properties, evaluate_crew_weight_distribution2_5d
from raftsim.milestone18 import (Milestone18PinReleaseFixtureReport, Milestone18PinReleaseFlowCase, Milestone18PinReleaseResponsePath, _base_release_drive_n, _check, _pin_release_outcome)


def build_milestone18_pin_release_fixture_report(
    *,
    fixture_id: str = "midstream_wrap_pin_release",
    obstruction_kind: str = "midstream_wrap_rock",
    station_m: float = 42.0,
    lateral_offset_m: float = 0.85,
    action_window_s: float = 0.75,
    feature_forcing_strength_scale: float = 0.0,
    notes: tuple[str, ...] = (),
) -> Milestone18PinReleaseFixtureReport:
    """Build the dedicated Milestone 18 flow-dependent pin/release fixture report."""

    if action_window_s <= 0.0:
        raise ValueError("action_window_s must be positive.")
    if feature_forcing_strength_scale < 0.0:
        raise ValueError("feature_forcing_strength_scale must be non-negative.")
    properties = build_default_raft_mass_properties()
    seats = build_default_crew_seats2_5d()
    neutral = evaluate_crew_weight_distribution2_5d(properties, seats)
    high_side_recovery_actions = tuple(
        CrewAction2_5D(seat.seat_id, high_side_direction=1, brace=True, recovery=True)
        for seat in seats
    )
    release = evaluate_crew_weight_distribution2_5d(properties, seats, high_side_recovery_actions)
    rescue_fixture = next(
        fixture for fixture in build_crew_overboard_fixtures2_5d() if fixture.fixture_id == "pin_failed_rescue"
    )
    failed_rescue = evaluate_crew_overboard_fixture2_5d(
        rescue_fixture,
        rescue_delay_s=rescue_fixture.failed_rescue_delay_s,
    )
    flow_cases = (
        _pin_release_flow_case(
            flow_band="low_scrape",
            discharge_cms=38.0,
            water_depth_m=0.48,
            approach_velocity_mps=1.15,
            approach_angle_deg=18.0,
            raft_orientation_deg=12.0,
            contact_normal=(0.93, -0.37),
            wrap_depth_m=0.16,
            side_load_n=1450.0,
            pin_force_n=2350.0,
            stickiness_factor=0.45,
            neutral=neutral,
            release=release,
            action_window_s=action_window_s,
            response_paths=("no_action_scrape",),
        ),
        _pin_release_flow_case(
            flow_band="runnable_sticky",
            discharge_cms=82.0,
            water_depth_m=0.92,
            approach_velocity_mps=2.05,
            approach_angle_deg=31.0,
            raft_orientation_deg=34.0,
            contact_normal=(0.72, -0.69),
            wrap_depth_m=0.58,
            side_load_n=3300.0,
            pin_force_n=3825.0,
            stickiness_factor=1.20,
            neutral=neutral,
            release=release,
            action_window_s=action_window_s,
            response_paths=("no_action_pin", "timed_high_side_release", "late_high_side_failed_rescue"),
            failed_rescue=failed_rescue,
        ),
        _pin_release_flow_case(
            flow_band="high_washout",
            discharge_cms=146.0,
            water_depth_m=1.42,
            approach_velocity_mps=3.05,
            approach_angle_deg=24.0,
            raft_orientation_deg=20.0,
            contact_normal=(0.84, -0.54),
            wrap_depth_m=0.24,
            side_load_n=2600.0,
            pin_force_n=2750.0,
            stickiness_factor=0.52,
            neutral=neutral,
            release=release,
            action_window_s=action_window_s,
            response_paths=("no_action_washout",),
        ),
    )
    proxy_separation = {
        "passed": True,
        "excluded_proxy_families": ["shallow_shelf", "boulder_impacts"],
        "distinct_obstruction_geometry": True,
        "requires_wrap_depth": True,
        "requires_flow_response": True,
        "requires_failed_rescue_path": True,
        "notes": [
            "This fixture is a wrap/pin release lane, not shallow-shelf grounding or generic boulder-impact proxy coverage."
        ],
    }
    default_notes = (
        "Feature forcing is recorded but left off for this closure fixture; release behavior comes from flow band, pin load, crew weight distribution, and rescue timing.",
        "The runnable_sticky band is intentionally the sticky band: low flow scrapes through and high flow washes out.",
    )
    return Milestone18PinReleaseFixtureReport(
        fixture_id=fixture_id,
        obstruction_kind=obstruction_kind,
        station_m=station_m,
        lateral_offset_m=lateral_offset_m,
        action_window_s=action_window_s,
        feature_forcing_strength_scale=feature_forcing_strength_scale,
        proxy_separation=proxy_separation,
        flow_cases=flow_cases,
        notes=notes or default_notes,
    )


def _pin_release_flow_case(
    *,
    flow_band: str,
    discharge_cms: float,
    water_depth_m: float,
    approach_velocity_mps: float,
    approach_angle_deg: float,
    raft_orientation_deg: float,
    contact_normal: tuple[float, float],
    wrap_depth_m: float,
    side_load_n: float,
    pin_force_n: float,
    stickiness_factor: float,
    neutral: CrewWeightTelemetry2_5D,
    release: CrewWeightTelemetry2_5D,
    action_window_s: float,
    response_paths: tuple[str, ...],
    failed_rescue: Any | None = None,
) -> Milestone18PinReleaseFlowCase:
    paths = tuple(
        _pin_release_response_path(
            path_id=path_id,
            flow_band=flow_band,
            pin_force_n=pin_force_n,
            side_load_n=side_load_n,
            stickiness_factor=stickiness_factor,
            neutral=neutral,
            release=release,
            action_window_s=action_window_s,
            failed_rescue=failed_rescue,
        )
        for path_id in response_paths
    )
    checks = (
        _check("flow_band_recorded", bool(flow_band), 1.0 if flow_band else 0.0, 1.0),
        _check("positive_discharge", discharge_cms > 0.0, discharge_cms, 0.0),
        _check("positive_depth", water_depth_m > 0.0, water_depth_m, 0.0),
        _check("wrap_depth_recorded", wrap_depth_m > 0.0, wrap_depth_m, 0.0),
        _check("side_load_recorded", side_load_n > 0.0, side_load_n, 0.0),
        _check("pin_force_recorded", pin_force_n > 0.0, pin_force_n, 0.0),
    )
    return Milestone18PinReleaseFlowCase(
        flow_band=flow_band,
        discharge_cms=discharge_cms,
        water_depth_m=water_depth_m,
        approach_velocity_mps=approach_velocity_mps,
        approach_angle_deg=approach_angle_deg,
        raft_orientation_deg=raft_orientation_deg,
        contact_normal=contact_normal,
        wrap_depth_m=wrap_depth_m,
        side_load_n=side_load_n,
        pin_force_n=pin_force_n,
        stickiness_factor=stickiness_factor,
        response_paths=paths,
        checks=checks,
    )


def _pin_release_response_path(
    *,
    path_id: str,
    flow_band: str,
    pin_force_n: float,
    side_load_n: float,
    stickiness_factor: float,
    neutral: CrewWeightTelemetry2_5D,
    release: CrewWeightTelemetry2_5D,
    action_window_s: float,
    failed_rescue: Any | None,
) -> Milestone18PinReleaseResponsePath:
    if path_id in {"timed_high_side_release", "late_high_side_failed_rescue"}:
        telemetry = release
        response_delay = 0.42 if path_id == "timed_high_side_release" else 1.05
        release_drive = _crew_release_drive_n(pin_force_n, side_load_n, neutral, telemetry)
    else:
        telemetry = neutral
        response_delay = None
        release_drive = _base_release_drive_n(pin_force_n, side_load_n)
    pin_margin = pin_force_n - telemetry.recovery_thresholds.pin_threshold_n
    release_margin = release_drive - telemetry.recovery_thresholds.release_threshold_n
    window_margin = None if response_delay is None else action_window_s - response_delay
    swimmer = _swimmer_summary(failed_rescue) if path_id == "late_high_side_failed_rescue" and failed_rescue is not None else None
    outcome = _pin_release_outcome(
        path_id=path_id,
        flow_band=flow_band,
        stickiness_factor=stickiness_factor,
        pin_margin=pin_margin,
        release_margin=release_margin,
        window_margin=window_margin,
        swimmer=swimmer,
    )
    checks = _pin_release_path_checks(
        path_id=path_id,
        flow_band=flow_band,
        outcome=outcome,
        stickiness_factor=stickiness_factor,
        pin_margin=pin_margin,
        release_margin=release_margin,
        window_margin=window_margin,
        telemetry=telemetry,
        swimmer=swimmer,
    )
    return Milestone18PinReleaseResponsePath(
        path_id=path_id,
        response_delay_s=response_delay,
        outcome=outcome,
        pin_margin_n=pin_margin,
        release_margin_n=release_margin,
        action_window_margin_s=window_margin,
        crew_weight=_crew_weight_summary(telemetry),
        swimmer=swimmer,
        checks=checks,
    )


def _crew_release_drive_n(
    pin_force_n: float,
    side_load_n: float,
    neutral: CrewWeightTelemetry2_5D,
    telemetry: CrewWeightTelemetry2_5D,
) -> float:
    threshold_gain = max(
        0.0,
        neutral.recovery_thresholds.release_threshold_n - telemetry.recovery_thresholds.release_threshold_n,
    )
    crew_action_gain = (
        telemetry.high_side_count * 55.0
        + telemetry.brace_count * 35.0
        + telemetry.recovery_count * 60.0
    )
    return _base_release_drive_n(pin_force_n, side_load_n) + 1500.0 + threshold_gain + crew_action_gain


def _pin_release_path_checks(
    *,
    path_id: str,
    flow_band: str,
    outcome: str,
    stickiness_factor: float,
    pin_margin: float,
    release_margin: float,
    window_margin: float | None,
    telemetry: CrewWeightTelemetry2_5D,
    swimmer: dict[str, object] | None,
) -> tuple[dict[str, object], ...]:
    if path_id == "no_action_pin":
        return (
            _check("sticky_flow_band", stickiness_factor >= 1.0, stickiness_factor, 1.0),
            _check("no_action_pins", outcome == "pinned" and pin_margin >= 0.0, pin_margin, 0.0),
            _check("release_margin_negative_without_action", release_margin < 0.0, release_margin, 0.0),
            _check("crew_action_absent", telemetry.active_action_count == 0, float(telemetry.active_action_count), 0.0),
        )
    if path_id == "timed_high_side_release":
        return (
            _check("timed_response_inside_window", (window_margin or -1.0) >= 0.0, window_margin or -1.0, 0.0),
            _check("release_margin_positive", release_margin >= 0.0, release_margin, 0.0),
            _check("crew_actions_recorded", telemetry.high_side_count > 0 and telemetry.recovery_count > 0, float(telemetry.active_action_count), 1.0),
            _check("outcome_released", outcome == "released", 1.0 if outcome == "released" else 0.0, 1.0),
        )
    if path_id == "late_high_side_failed_rescue":
        rescue_completed = bool(swimmer and swimmer.get("rescue_completed"))
        return (
            _check("late_response_misses_window", (window_margin or 1.0) < 0.0, window_margin or 1.0, 0.0),
            _check("failed_rescue_recorded", swimmer is not None and not rescue_completed, 0.0 if rescue_completed else 1.0, 1.0),
            _check("swimmer_state_recorded", bool(swimmer and swimmer.get("states")), 1.0 if swimmer and swimmer.get("states") else 0.0, 1.0),
            _check("outcome_failed_rescue", outcome == "failed_rescue", 1.0 if outcome == "failed_rescue" else 0.0, 1.0),
        )
    if path_id == "no_action_scrape":
        return (
            _check("low_flow_less_sticky", flow_band == "low_scrape" and stickiness_factor < 0.7, stickiness_factor, 0.7),
            _check("low_flow_not_pinned", pin_margin < 0.0, pin_margin, 0.0),
            _check("outcome_scraped_clear", outcome == "scraped_clear", 1.0 if outcome == "scraped_clear" else 0.0, 1.0),
        )
    if path_id == "no_action_washout":
        return (
            _check("high_flow_washes_out", flow_band == "high_washout" and stickiness_factor < 0.7, stickiness_factor, 0.7),
            _check("washout_not_pinned", pin_margin < 0.0, pin_margin, 0.0),
            _check("outcome_flushed_washout", outcome == "flushed_washout", 1.0 if outcome == "flushed_washout" else 0.0, 1.0),
        )
    return (_check("known_path", False, 0.0, 1.0),)


def _crew_weight_summary(telemetry: CrewWeightTelemetry2_5D) -> dict[str, object]:
    return {
        "occupied_seat_count": telemetry.occupied_seat_count,
        "active_action_count": telemetry.active_action_count,
        "high_side_count": telemetry.high_side_count,
        "brace_count": telemetry.brace_count,
        "recovery_count": telemetry.recovery_count,
        "combined_center_of_gravity_offset": _vec_json(telemetry.combined_center_of_gravity_offset),
        "roll_moment_nm": telemetry.roll_moment_nm,
        "contact_loading": {
            "lateral_bias": telemetry.contact_loading.lateral_bias,
            "left_tube_normal_load_n": telemetry.contact_loading.left_tube_normal_load_n,
            "right_tube_normal_load_n": telemetry.contact_loading.right_tube_normal_load_n,
        },
        "recovery_thresholds": {
            "pin_threshold_n": telemetry.recovery_thresholds.pin_threshold_n,
            "release_threshold_n": telemetry.recovery_thresholds.release_threshold_n,
            "flip_threshold_nm": telemetry.recovery_thresholds.flip_threshold_nm,
            "pin_threshold_multiplier": telemetry.recovery_thresholds.pin_threshold_multiplier,
            "release_threshold_multiplier": telemetry.recovery_thresholds.release_threshold_multiplier,
            "flip_threshold_multiplier": telemetry.recovery_thresholds.flip_threshold_multiplier,
        },
    }


def _swimmer_summary(telemetry: Any) -> dict[str, object]:
    return {
        "fixture_id": telemetry.fixture_id,
        "trigger_kind": telemetry.trigger_kind,
        "states": list(telemetry.states),
        "overboard_triggered": telemetry.overboard_triggered,
        "rescue_completed": telemetry.rescue_completed,
        "swimmer_world_position": _vec_json(telemetry.swimmer_world_position),
        "swimmer_distance_m": telemetry.swimmer_distance_m,
        "time_in_water_s": telemetry.time_in_water_s,
        "rescue_method": telemetry.rescue_method,
        "failed_reason": telemetry.failed_reason,
        "fatigue_delta": telemetry.fatigue_delta,
        "trust_delta": telemetry.trust_delta,
        "safety_score_delta": telemetry.safety_score_delta,
    }


def _vec_json(value: Vec3) -> dict[str, float]:
    return {"x": value.x, "y": value.y, "z": value.z}
