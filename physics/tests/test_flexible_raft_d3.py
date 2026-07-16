import json
from pathlib import Path

import pytest

from raftsim.flexible_raft_d2 import solve_seat_load_coupled_tube_d2
from raftsim.flexible_raft_d3 import (
    D3_OVERWASH_FIXTURE_RELATIVE_PATH,
    D3_OVERWASH_SCHEMA,
    _synthetic_water_field,
    build_overwash_flip_d3_fixture,
    evaluate_overwash_flip_d3,
)
from raftsim.math3d import Vec3
from raftsim.raft_coupling2_5d import (
    CrewAction2_5D,
    RaftState6DoF,
    build_default_crew_seats2_5d,
    build_default_raft_mass_properties,
)
from raftsim.scenario2_5d import RaftParameters2_5D


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_overwash_d3_fixture_is_reproducible():
    generated = build_overwash_flip_d3_fixture()
    committed = json.loads(
        (REPO_ROOT / D3_OVERWASH_FIXTURE_RELATIVE_PATH).read_text(encoding="utf-8")
    )

    assert generated == committed
    assert committed["schema"] == D3_OVERWASH_SCHEMA
    assert committed["scoring_authority_enabled"] is False
    assert committed["model_contract"]["accepted_water_sampler_coupled"] == "WaterField2_5D"


def test_calm_water_does_not_overtop_depressed_tubes():
    params, neutral = _neutral_d2_solve()
    water = _synthetic_water_field(surface_height_m=0.05, velocity=Vec3())

    solve = evaluate_overwash_flip_d3(neutral, water, parameters=params)

    assert solve.scoring_authority_enabled is False
    assert solve.total_overtopping_flux_m3_s == pytest.approx(0.0)
    assert solve.total_retained_water_mass_kg == pytest.approx(0.0)
    assert solve.reference_flip_risk is False


def test_incoming_starboard_water_overtops_upstream_tube_segments():
    params, neutral = _neutral_d2_solve()
    water = _synthetic_water_field(surface_height_m=0.20, velocity=Vec3(0.0, -2.4, 0.0))

    solve = evaluate_overwash_flip_d3(neutral, water, parameters=params)
    starboard_flux = sum(
        segment.overtopping_flux_m3_s
        for segment in solve.segment_overwash
        if segment.segment_id.startswith("starboard_")
    )
    port_flux = sum(
        segment.overtopping_flux_m3_s
        for segment in solve.segment_overwash
        if segment.segment_id.startswith("port_")
    )

    assert solve.total_overtopping_flux_m3_s > 0.0
    assert starboard_flux > 0.0
    assert port_flux == pytest.approx(0.0)
    assert solve.retained_water_roll_moment_nm > 0.0


def test_high_side_action_changes_reference_flip_margin():
    params = RaftParameters2_5D(passenger_count=4)
    properties = build_default_raft_mass_properties(params)
    seats = build_default_crew_seats2_5d(params)
    water = _synthetic_water_field(surface_height_m=0.20, velocity=Vec3(0.0, -2.4, 0.0))
    neutral_tube = solve_seat_load_coupled_tube_d2(
        RaftState6DoF(position=Vec3(3.0, 2.0, 0.0)),
        properties,
        seats,
        parameters=params,
    )
    high_side_tube = solve_seat_load_coupled_tube_d2(
        RaftState6DoF(position=Vec3(3.0, 2.0, 0.0)),
        properties,
        seats,
        tuple(CrewAction2_5D(seat.seat_id, high_side_direction=1) for seat in seats),
        parameters=params,
    )

    neutral = evaluate_overwash_flip_d3(neutral_tube, water, parameters=params)
    high_side = evaluate_overwash_flip_d3(high_side_tube, water, parameters=params)

    assert high_side.reference_flip_threshold_nm > neutral.reference_flip_threshold_nm
    assert high_side.reference_flip_margin_nm != pytest.approx(neutral.reference_flip_margin_nm)


def test_retained_water_drains_when_overtopping_stops():
    params, neutral = _neutral_d2_solve()
    starboard_water = _synthetic_water_field(surface_height_m=0.20, velocity=Vec3(0.0, -2.4, 0.0))
    calm_water = _synthetic_water_field(surface_height_m=0.05, velocity=Vec3())
    first = evaluate_overwash_flip_d3(neutral, starboard_water, parameters=params)
    retained = {
        segment.segment_id: segment.retained_water_volume_m3
        for segment in first.segment_overwash
    }

    drained = evaluate_overwash_flip_d3(
        neutral,
        calm_water,
        parameters=params,
        previous_retained_volume_by_segment=retained,
    )

    assert drained.total_overtopping_flux_m3_s == pytest.approx(0.0)
    assert drained.total_drainage_flux_m3_s > 0.0
    assert drained.total_retained_water_volume_m3 < first.total_retained_water_volume_m3


def test_overwash_d3_rejects_invalid_solver_parameters():
    params, neutral = _neutral_d2_solve()
    water = _synthetic_water_field(surface_height_m=0.05, velocity=Vec3())

    with pytest.raises(ValueError, match="dt"):
        evaluate_overwash_flip_d3(neutral, water, parameters=params, dt=0.0)
    with pytest.raises(ValueError, match="flux_coefficient"):
        evaluate_overwash_flip_d3(neutral, water, parameters=params, flux_coefficient=-1.0)


def _neutral_d2_solve():
    params = RaftParameters2_5D(passenger_count=4)
    properties = build_default_raft_mass_properties(params)
    seats = build_default_crew_seats2_5d(params)
    solve = solve_seat_load_coupled_tube_d2(
        RaftState6DoF(position=Vec3(3.0, 2.0, 0.0)),
        properties,
        seats,
        parameters=params,
    )
    return params, solve
