import json
from pathlib import Path

import pytest

from raftsim.flexible_raft_d2 import (
    D2_SEAT_LOAD_FIXTURE_RELATIVE_PATH,
    D2_SEAT_LOAD_SCHEMA,
    build_seat_load_coupled_tube_d2_fixture,
    solve_seat_load_coupled_tube_d2,
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


def test_seat_load_d2_fixture_is_reproducible():
    generated = build_seat_load_coupled_tube_d2_fixture()
    committed = json.loads(
        (REPO_ROOT / D2_SEAT_LOAD_FIXTURE_RELATIVE_PATH).read_text(encoding="utf-8")
    )

    assert generated == committed
    assert committed["schema"] == D2_SEAT_LOAD_SCHEMA
    assert committed["scoring_authority_enabled"] is False
    assert committed["model_contract"]["gameplay_scoring_authority"].startswith("disabled")


def test_neutral_crew_loads_sag_local_tubes_without_scoring_authority():
    params = RaftParameters2_5D(mass_kg=400.0, guide_mass_kg=90.0, passenger_mass_kg=70.0, passenger_count=4)
    properties = build_default_raft_mass_properties(params)
    seats = build_default_crew_seats2_5d(params)

    solve = solve_seat_load_coupled_tube_d2(
        RaftState6DoF(),
        properties,
        seats,
        parameters=params,
    )

    assert solve.scoring_authority_enabled is False
    assert len(solve.seat_loads) == 5
    assert solve.crew_telemetry.total_crew_mass_kg == pytest.approx(370.0)
    assert solve.tube_solve.tube_solve.total_applied_load_n == pytest.approx(370.0 * 9.81)
    assert solve.port_freeboard_loss_m == pytest.approx(solve.starboard_freeboard_loss_m)
    assert solve.port_total_freeboard_loss_m == pytest.approx(
        solve.starboard_total_freeboard_loss_m,
        rel=0.04,
    )
    assert solve.max_seat_freeboard_loss_m > 0.0


def test_high_side_actions_shift_freeboard_to_starboard_tube():
    params = RaftParameters2_5D(passenger_count=4)
    properties = build_default_raft_mass_properties(params)
    seats = build_default_crew_seats2_5d(params)
    neutral = solve_seat_load_coupled_tube_d2(
        RaftState6DoF(),
        properties,
        seats,
        parameters=params,
    )

    high_side = solve_seat_load_coupled_tube_d2(
        RaftState6DoF(),
        properties,
        seats,
        tuple(CrewAction2_5D(seat.seat_id, high_side_direction=1) for seat in seats),
        parameters=params,
    )

    assert high_side.crew_telemetry.high_side_count == high_side.crew_telemetry.occupied_seat_count
    assert high_side.tube_solve.tube_solve.roll_load_bias_nm > neutral.tube_solve.tube_solve.roll_load_bias_nm
    assert high_side.starboard_total_freeboard_loss_m > high_side.port_total_freeboard_loss_m
    assert all(seat.high_side_direction == 1 for seat in high_side.seat_loads)
    assert any(seat.target_segment_id.startswith("starboard_") for seat in high_side.seat_loads)


def test_lean_and_brace_change_local_loads_and_freeboard():
    params = RaftParameters2_5D(passenger_count=4)
    properties = build_default_raft_mass_properties(params)
    seats = build_default_crew_seats2_5d(params)
    neutral = solve_seat_load_coupled_tube_d2(
        RaftState6DoF(),
        properties,
        seats,
        parameters=params,
    )
    braced_port = solve_seat_load_coupled_tube_d2(
        RaftState6DoF(),
        properties,
        seats,
        tuple(
            CrewAction2_5D(
                seat.seat_id,
                lean_offset=Vec3(0.0, -1.5, 0.0),
                brace=seat.role == "passenger",
            )
            for seat in seats
        ),
        parameters=params,
    )

    assert braced_port.crew_telemetry.brace_count == 4
    assert braced_port.port_freeboard_loss_m > neutral.port_freeboard_loss_m
    assert braced_port.port_total_freeboard_loss_m > braced_port.starboard_total_freeboard_loss_m
    assert braced_port.tube_solve.tube_solve.roll_load_bias_nm < neutral.tube_solve.tube_solve.roll_load_bias_nm
    assert any(seat.lean_was_clamped for seat in braced_port.seat_loads)
    assert sum(seat.force_n for seat in braced_port.seat_loads) > sum(
        seat.force_n for seat in neutral.seat_loads
    )


def test_seat_load_d2_rejects_negative_downforce_settings():
    params = RaftParameters2_5D(passenger_count=1)
    properties = build_default_raft_mass_properties(params)
    seats = build_default_crew_seats2_5d(params)

    with pytest.raises(ValueError, match="brace_downforce_fraction"):
        solve_seat_load_coupled_tube_d2(
            RaftState6DoF(),
            properties,
            seats,
            parameters=params,
            brace_downforce_fraction=-0.1,
        )
