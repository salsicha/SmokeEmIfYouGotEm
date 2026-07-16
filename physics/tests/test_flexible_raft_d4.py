import json
from pathlib import Path

import pytest

from raftsim.flexible_raft_d2 import solve_seat_load_coupled_tube_d2
from raftsim.flexible_raft_d4 import (
    D4_ROCK_CONTACT_FIXTURE_RELATIVE_PATH,
    D4_ROCK_CONTACT_SCHEMA,
    RockObstacleD4,
    build_rock_contact_wrap_pin_d4_fixture,
    evaluate_rock_contact_wrap_pin_d4,
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


def test_rock_contact_d4_fixture_is_reproducible():
    generated = build_rock_contact_wrap_pin_d4_fixture()
    committed = json.loads(
        (REPO_ROOT / D4_ROCK_CONTACT_FIXTURE_RELATIVE_PATH).read_text(encoding="utf-8")
    )

    assert generated == committed
    assert committed["schema"] == D4_ROCK_CONTACT_SCHEMA
    assert committed["scoring_authority_enabled"] is False
    assert committed["model_contract"]["accepted_water_fields_modified"] is False


def test_clear_boulder_produces_no_contact_or_water_mutation():
    _, tube = _neutral_d2_solve()

    solve = evaluate_rock_contact_wrap_pin_d4(
        tube,
        (RockObstacleD4("far_clear", Vec3(0.0, 4.5, 0.0), 0.25),),
    )

    assert solve.contacts == ()
    assert solve.total_holding_force_n == pytest.approx(0.0)
    assert solve.water_field_modified is False
    assert solve.scoring_authority_enabled is False


def test_single_boulder_indents_bounded_tube_and_records_release_support():
    _, tube = _neutral_d2_solve()

    solve = evaluate_rock_contact_wrap_pin_d4(
        tube,
        (RockObstacleD4("single_starboard", Vec3(0.54, 1.22, 0.0), 0.18),),
        max_indentation_m=0.22,
    )

    assert len(solve.contacts) >= 1
    contact = max(solve.contacts, key=lambda item: item.indentation_m)
    assert contact.segment_id.startswith("starboard_")
    assert contact.indentation_m <= 0.22
    assert contact.normal_force_n > 0.0
    assert contact.friction_force_n > 0.0
    assert contact.pressure_release_support_n > 0.0
    assert contact.release_resistance_n < contact.holding_force_n


def test_wide_boulder_wraps_multiple_segments_and_can_pin():
    _, tube = _neutral_d2_solve()

    solve = evaluate_rock_contact_wrap_pin_d4(
        tube,
        (RockObstacleD4("wide_wrap", Vec3(0.0, 1.0, 0.0), 1.45, 0.82),),
    )

    assert len(solve.contacts) >= 3
    assert solve.wrapping_contact_count >= 3
    assert solve.total_holding_force_n > 0.0
    assert solve.pinned_obstacle_count >= 1
    assert solve.min_release_margin_n < 0.0


def test_high_side_changes_pressure_dependent_release_margin():
    params = RaftParameters2_5D(passenger_count=4)
    properties = build_default_raft_mass_properties(params)
    seats = build_default_crew_seats2_5d(params)
    state = RaftState6DoF(position=Vec3(3.0, 2.0, 0.0), linear_velocity=Vec3(0.0, 0.7, 0.0))
    neutral_tube = solve_seat_load_coupled_tube_d2(state, properties, seats, parameters=params)
    high_side_tube = solve_seat_load_coupled_tube_d2(
        state,
        properties,
        seats,
        tuple(CrewAction2_5D(seat.seat_id, high_side_direction=1) for seat in seats),
        parameters=params,
    )
    obstacle = (RockObstacleD4("wide_wrap", Vec3(0.0, 1.0, 0.0), 1.45, 0.82),)

    neutral = evaluate_rock_contact_wrap_pin_d4(neutral_tube, obstacle, parameters=params)
    high_side = evaluate_rock_contact_wrap_pin_d4(high_side_tube, obstacle, parameters=params)

    assert high_side.min_release_margin_n != pytest.approx(neutral.min_release_margin_n)
    assert sum(contact.pressure_release_support_n for contact in neutral.contacts) > 0.0
    assert all(
        contact.release_resistance_n < contact.holding_force_n
        for contact in high_side.contacts
    )


def test_post_contact_shape_recovery_decays_previous_indentation():
    _, tube = _neutral_d2_solve()

    solve = evaluate_rock_contact_wrap_pin_d4(
        tube,
        (),
        previous_indentation_by_segment={"starboard_2": 0.12},
        dt=1.0 / 30.0,
        recovery_rate_per_s=2.4,
    )

    assert len(solve.contacts) == 1
    contact = solve.contacts[0]
    assert contact.recovering is True
    assert contact.indentation_m < 0.12
    assert contact.holding_force_n == pytest.approx(0.0)
    assert solve.recovering_contact_count == 1


def test_rock_contact_d4_rejects_invalid_inputs():
    _, tube = _neutral_d2_solve()

    with pytest.raises(ValueError, match="radius_m"):
        RockObstacleD4("bad", Vec3(), 0.0)
    with pytest.raises(ValueError, match="dt"):
        evaluate_rock_contact_wrap_pin_d4(tube, (), dt=0.0)
    with pytest.raises(ValueError, match="pressure_release_area"):
        evaluate_rock_contact_wrap_pin_d4(tube, (), pressure_release_area_m2=-0.1)


def _neutral_d2_solve():
    params = RaftParameters2_5D(passenger_count=4)
    properties = build_default_raft_mass_properties(params)
    seats = build_default_crew_seats2_5d(params)
    solve = solve_seat_load_coupled_tube_d2(
        RaftState6DoF(position=Vec3(3.0, 2.0, 0.0), linear_velocity=Vec3(0.0, 0.7, 0.0)),
        properties,
        seats,
        parameters=params,
    )
    return params, solve
