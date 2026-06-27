import numpy as np

from raftsim.feature_validation import validate_standing_wave_case
from raftsim.math3d import Vec3
from raftsim.raft_coupling2_5d import RaftState6DoF, WaterField2_5D, build_default_raft_mass_properties
from raftsim.scenario2_5d import FixtureScenario2_5DParameters, generate_fixture_scenario2_5d


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
