import numpy as np

from raftsim.feature_validation import (
    validate_eddy_line_case,
    validate_hole_case,
    validate_lateral_wave_case,
    validate_standing_wave_case,
)
from raftsim.math3d import Vec3
from raftsim.raft_coupling2_5d import RaftState6DoF, WaterField2_5D, build_default_raft_mass_properties
from raftsim.scenario2_5d import Feature2_5D, FixtureScenario2_5DParameters, generate_fixture_scenario2_5d


def test_standing_wave_validation_classifies_surf_case():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="uniform_channel", nx=12, ny=8))
    water = WaterField2_5D.from_scenario_initial_state(scenario)
    eta = water.eta + np.exp(-((np.arange(water.shape[1])[None, :] - 6.0) ** 2) / 8.0) * 0.2
    water = WaterField2_5D(
        origin_x=water.origin_x,
        origin_y=water.origin_y,
        dx=water.dx,
        dy=water.dy,
        bed=water.bed,
        depth=water.depth,
        eta=eta,
        u=water.u,
        v=water.v,
        wet=water.wet,
        normal_x=water.normal_x,
        normal_y=water.normal_y,
        normal_z=np.ones_like(water.normal_z),
        roughness=water.roughness,
        features=water.features,
    )
    properties = build_default_raft_mass_properties(scenario.raft)
    state = RaftState6DoF(position=Vec3(6.0, 0.0, 0.8), linear_velocity=Vec3(float(water.u[4, 6]), 0.0, 0.0))

    result = validate_standing_wave_case(water, state, properties, crest_lift_threshold=0.01)

    assert result.feature == "standing_wave"
    assert result.outcome == "surf"
    assert result.passed


def test_hole_validation_detects_retention_and_boil_lift():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="flat_pool", nx=12, ny=8))
    water = WaterField2_5D.from_scenario_initial_state(scenario)
    eta = water.eta.copy()
    u = water.u.copy()
    normal_z = water.normal_z.copy()
    center = (6, 4)
    eta[center[1], center[0]] -= 0.2
    u[:, :] = 0.0
    normal_z[center[1], center[0]] = 0.82
    water = WaterField2_5D(
        origin_x=water.origin_x,
        origin_y=water.origin_y,
        dx=water.dx,
        dy=water.dy,
        bed=water.bed,
        depth=water.depth,
        eta=eta,
        u=u,
        v=water.v,
        wet=water.wet,
        normal_x=water.normal_x,
        normal_y=water.normal_y,
        normal_z=normal_z,
        roughness=0.08,
        features=(Feature2_5D("hole", (6.0, water.origin_y + 4 * water.dy), radius=2.0, strength=1.0),),
    )
    properties = build_default_raft_mass_properties(scenario.raft)
    state = RaftState6DoF(position=Vec3(6.0, water.origin_y + 4 * water.dy, 0.8))

    result = validate_hole_case(water, state, properties, boil_lift_threshold=0.1)

    assert result.feature == "hole"
    assert result.outcome == "retentive_hole"
    assert result.passed


def test_lateral_wave_validation_detects_side_impulse_and_roll_torque():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="flat_pool", nx=14, ny=10))
    water = WaterField2_5D.from_scenario_initial_state(scenario)
    center_x = 7.0
    center_y = water.origin_y + 5 * water.dy
    eta = water.eta.copy()
    v = water.v.copy()
    normal_y = water.normal_y.copy()
    normal_z = water.normal_z.copy()
    for row in range(water.shape[0]):
        y = water.origin_y + row * water.dy
        offset = (y - center_y) / max(water.dy, 1.0e-9)
        influence = np.exp(-(offset * offset) / 3.0)
        v[row, :] = 0.9 * influence
        eta[row, :] += 0.08 * offset * influence
        normal_y[row, :] = -0.12 * influence
        normal_z[row, :] = np.sqrt(np.maximum(1.0 - normal_y[row, :] ** 2, 0.01))
    water = WaterField2_5D(
        origin_x=water.origin_x,
        origin_y=water.origin_y,
        dx=water.dx,
        dy=water.dy,
        bed=water.bed,
        depth=water.depth,
        eta=eta,
        u=water.u,
        v=v,
        wet=water.wet,
        normal_x=water.normal_x,
        normal_y=normal_y,
        normal_z=normal_z,
        roughness=water.roughness,
        features=(Feature2_5D("lateral", (center_x, center_y), radius=2.0, strength=1.0),),
    )
    properties = build_default_raft_mass_properties(scenario.raft)
    state = RaftState6DoF(position=Vec3(center_x, center_y, 0.8))

    result = validate_lateral_wave_case(water, state, properties)

    assert result.feature == "lateral_wave"
    assert result.outcome == "side_surf"
    assert result.passed


def test_eddy_line_validation_detects_yaw_and_roll_coupling():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="flat_pool", nx=14, ny=10))
    water = WaterField2_5D.from_scenario_initial_state(scenario)
    center_x = 7.0
    center_y = water.origin_y + 5 * water.dy
    eta = water.eta.copy()
    u = water.u.copy()
    normal_y = water.normal_y.copy()
    normal_z = water.normal_z.copy()
    for row in range(water.shape[0]):
        y = water.origin_y + row * water.dy
        side = np.tanh((center_y - y) / 0.55)
        u[row, :] = 0.35 + 0.75 * side
        eta[row, :] += 0.05 * side
        normal_y[row, :] = -0.10 * np.exp(-((y - center_y) ** 2) / 2.0)
        normal_z[row, :] = np.sqrt(np.maximum(1.0 - normal_y[row, :] ** 2, 0.01))
    water = WaterField2_5D(
        origin_x=water.origin_x,
        origin_y=water.origin_y,
        dx=water.dx,
        dy=water.dy,
        bed=water.bed,
        depth=water.depth,
        eta=eta,
        u=u,
        v=water.v,
        wet=water.wet,
        normal_x=water.normal_x,
        normal_y=normal_y,
        normal_z=normal_z,
        roughness=water.roughness,
        features=(Feature2_5D("eddy_line", (center_x, center_y), radius=2.0, strength=1.0),),
    )
    properties = build_default_raft_mass_properties(scenario.raft)
    state = RaftState6DoF(position=Vec3(center_x, center_y, 0.8))

    result = validate_eddy_line_case(water, state, properties)

    assert result.feature == "eddy_line"
    assert result.outcome == "eddy_coupled"
    assert result.passed
