import math
import csv

import pytest

from raftsim.math3d import Quaternion, Vec3
from raftsim.pyclaw_reference import build_initial_pyclaw_reference_result
from raftsim.raft_coupling2_5d import (
    PaddleBladePose2_5D,
    RaftSamplePatch,
    RaftState6DoF,
    WaterField2_5D,
    build_default_raft_mass_properties,
    compare_raft_force_samples,
    sample_buoyancy_forces,
    sample_grounding_forces,
    sample_hydrodynamic_forces,
    sample_paddle_blade,
    sample_total_raft_forces,
    sum_force_contributions,
)
from raftsim.scenario2_5d import FixtureScenario2_5DParameters, RaftParameters2_5D, generate_fixture_scenario2_5d


def test_raft_state_advances_linear_and_angular_motion():
    state = RaftState6DoF(
        position=Vec3(1.0, 2.0, 3.0),
        linear_velocity=Vec3(2.0, 0.0, 0.0),
        angular_velocity=Vec3(0.0, 0.0, 1.0),
    )

    advanced = state.advance(0.5, linear_acceleration=Vec3(0.0, 2.0, 0.0))

    assert advanced.position.is_close(Vec3(2.0, 2.5, 3.0))
    assert advanced.linear_velocity.is_close(Vec3(2.0, 1.0, 0.0))
    assert math.isclose(advanced.orientation.norm, 1.0)


def test_raft_state_rejects_negative_timestep():
    with pytest.raises(ValueError):
        RaftState6DoF().advance(-0.1)


def test_world_point_and_point_velocity_include_rotation():
    state = RaftState6DoF(
        position=Vec3(10.0, 0.0, 0.0),
        orientation=Quaternion.from_axis_angle(Vec3(0.0, 0.0, 1.0), math.pi * 0.5),
        linear_velocity=Vec3(1.0, 0.0, 0.0),
        angular_velocity=Vec3(0.0, 0.0, 2.0),
    )

    point = state.world_point(Vec3(1.0, 0.0, 0.0))
    velocity = state.point_velocity(Vec3(1.0, 0.0, 0.0))

    assert point.is_close(Vec3(10.0, 1.0, 0.0), abs_tol=1.0e-9)
    assert velocity.is_close(Vec3(-1.0, 0.0, 0.0), abs_tol=1.0e-9)


def test_default_mass_properties_include_crew_inertia_and_samples():
    params = RaftParameters2_5D(mass_kg=400.0, guide_mass_kg=90.0, passenger_mass_kg=70.0, passenger_count=4)

    properties = build_default_raft_mass_properties(params)

    assert properties.total_mass_kg == 770.0
    assert properties.inverse_mass == pytest.approx(1.0 / 770.0)
    assert properties.inertia_diagonal_kg_m2.x > 0.0
    assert properties.inertia_diagonal_kg_m2.y > properties.inertia_diagonal_kg_m2.x
    assert properties.gravity == Vec3(0.0, 0.0, -9.81)
    assert properties.guide_offset.x < 0.0
    assert len(properties.passenger_offsets) == 4
    assert len(properties.sample_patches) == 14
    assert {patch.kind for patch in properties.sample_patches} == {"left_tube", "right_tube", "floor"}


def test_sample_patch_requires_positive_area_and_normalizes_normal():
    patch = RaftSamplePatch("test", Vec3(), 1.0, Vec3(0.0, 0.0, 2.0))

    assert patch.local_normal == Vec3(0.0, 0.0, 1.0)
    with pytest.raises(ValueError):
        RaftSamplePatch("bad", Vec3(), 0.0)


def test_water_field_samples_solver_neutral_fields_and_feature_tags():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="dam_break", nx=16, ny=8))
    field = WaterField2_5D.from_scenario_initial_state(scenario)
    feature = scenario.features[0]

    sample = field.sample(feature.center[0], feature.center[1])

    assert scenario.initial_state.eta.min() <= sample.surface_height <= scenario.initial_state.eta.max()
    assert sample.depth > 0.0
    assert sample.wet is True
    assert sample.velocity.z == 0.0
    assert sample.normal.magnitude == pytest.approx(1.0)
    assert sample.roughness == scenario.roughness
    assert "ledge" in sample.feature_tags


def test_buoyancy_forces_push_submerged_samples_upward():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="flat_pool", nx=12, ny=8))
    water = WaterField2_5D.from_scenario_initial_state(scenario)
    properties = build_default_raft_mass_properties(scenario.raft)
    state = RaftState6DoF(position=Vec3(5.0, 0.0, 0.8))

    contributions = sample_buoyancy_forces(state, properties, water)
    total_force, total_torque = sum_force_contributions(contributions)

    assert contributions
    assert total_force.z > 0.0
    assert math.isfinite(total_torque.x)
    assert all(contribution.metadata["submerged_depth"] > 0.0 for contribution in contributions)


def test_hydrodynamic_forces_include_drag_and_vertical_damping():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="uniform_channel", nx=12, ny=8))
    water = WaterField2_5D.from_scenario_initial_state(scenario)
    properties = build_default_raft_mass_properties(scenario.raft)
    state = RaftState6DoF(position=Vec3(5.0, 0.0, 1.0), linear_velocity=Vec3(0.0, 0.0, -1.0))

    contributions = sample_hydrodynamic_forces(state, properties, water, slope_force_scale=0.0)
    total_force, _ = sum_force_contributions(contributions)

    assert contributions
    assert total_force.x > 0.0
    assert total_force.z > 0.0


def test_grounding_forces_push_up_and_apply_friction():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="bed_step", nx=12, ny=8))
    water = WaterField2_5D.from_scenario_initial_state(scenario)
    properties = build_default_raft_mass_properties(scenario.raft)
    state = RaftState6DoF(position=Vec3(6.0, 0.0, -0.2), linear_velocity=Vec3(2.0, 0.0, -1.0))

    contributions = sample_grounding_forces(state, properties, water)
    total_force, _ = sum_force_contributions(contributions)

    assert contributions
    assert total_force.z > 0.0
    assert total_force.x < 0.0
    assert any("ledge" in contribution.metadata["feature_tags"] for contribution in contributions)


def test_paddle_blade_sample_reports_depth_and_relative_velocity():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="uniform_channel", nx=12, ny=8))
    water = WaterField2_5D.from_scenario_initial_state(scenario)
    state = RaftState6DoF(position=Vec3(5.0, 0.0, 1.0), linear_velocity=Vec3(1.0, 0.0, 0.0))
    blade = PaddleBladePose2_5D(local_position=Vec3(0.0, 0.8, -0.6), local_velocity=Vec3(-1.0, 0.0, -0.5))

    sample = sample_paddle_blade(state, blade, water)

    assert sample.submerged is True
    assert sample.depth > 0.0
    assert sample.water_velocity.x > 0.0
    assert sample.relative_velocity.z < 0.0
    assert sample.blade_velocity.x == pytest.approx(0.0)


def test_raft_forces_sample_from_pyclaw_frame_output(tmp_path):
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="flat_pool", nx=12, ny=8))
    result = build_initial_pyclaw_reference_result(scenario)
    output_dir = result.write_output(tmp_path / "pyclaw")
    water = WaterField2_5D.from_pyclaw_frame_npz(scenario, str(output_dir / "frames" / "frame_0000.npz"))
    properties = build_default_raft_mass_properties(scenario.raft)
    state = RaftState6DoF(position=Vec3(5.0, 0.0, 0.8))

    contributions = sample_total_raft_forces(state, properties, water)
    total_force, _ = sum_force_contributions(contributions)

    assert contributions
    assert total_force.z > 0.0
    assert any(contribution.name.startswith("buoyancy") for contribution in contributions)


def test_raft_forces_sample_from_cpp_frame_csv(tmp_path):
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="flat_pool", nx=8, ny=6))
    frame_path = tmp_path / "frame_0000.csv"
    with frame_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["row", "col", "x", "y", "h", "eta", "u", "v", "hu", "hv", "wet", "normal_x", "normal_y", "normal_z", "froude"])
        for row in range(scenario.grid.ny):
            for col in range(scenario.grid.nx):
                x = scenario.grid.origin_x + col * scenario.grid.dx
                y = scenario.grid.origin_y + row * scenario.grid.dy
                h = scenario.initial_state.depth[row, col]
                u = scenario.initial_state.u[row, col]
                v = scenario.initial_state.v[row, col]
                writer.writerow([row, col, x, y, h, scenario.initial_state.eta[row, col], u, v, h * u, h * v, 1, 0.0, 0.0, 1.0, 0.0])
    water = WaterField2_5D.from_cpp_frame_csv(scenario, str(frame_path))
    properties = build_default_raft_mass_properties(scenario.raft)
    state = RaftState6DoF(position=Vec3(3.0, 0.0, 0.8))

    contributions = sample_total_raft_forces(state, properties, water)
    total_force, _ = sum_force_contributions(contributions)

    assert contributions
    assert total_force.z > 0.0


def test_raft_force_comparison_reports_envelopes_trajectory_and_outcome():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="flat_pool", nx=12, ny=8))
    water = WaterField2_5D.from_scenario_initial_state(scenario)
    properties = build_default_raft_mass_properties(scenario.raft)
    state = RaftState6DoF(position=Vec3(5.0, 0.0, 0.8))

    comparison = compare_raft_force_samples(water, water, state, properties, dt=1.0 / 60.0)

    assert comparison.outcome_match is True
    assert comparison.reference.outcome == "floating"
    assert comparison.force_delta.magnitude == 0.0
    assert comparison.torque_delta.magnitude == 0.0
    assert comparison.trajectory_position_delta == 0.0
    assert comparison.trajectory_velocity_delta == 0.0
