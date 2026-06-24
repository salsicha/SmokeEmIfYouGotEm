import json

import numpy as np

from raftsim.scenario2_5d import (
    FixtureScenario2_5DParameters,
    ProceduralScenario2_5DParameters,
    generate_fixture_scenario2_5d,
    generate_procedural_scenario2_5d,
    read_scenario2_5d_package,
)


def test_fixture_generation_is_deterministic_for_seed():
    params = FixtureScenario2_5DParameters(fixture="uniform_channel", seed=7, nx=24, ny=12)
    first = generate_fixture_scenario2_5d(params)
    second = generate_fixture_scenario2_5d(params)

    assert first.to_json_dict() == second.to_json_dict()
    np.testing.assert_allclose(first.bed, second.bed)
    np.testing.assert_allclose(first.initial_state.depth, second.initial_state.depth)
    np.testing.assert_allclose(first.initial_state.u, second.initial_state.u)
    assert first.validate().passed


def test_scenario_package_round_trips(tmp_path):
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="dam_break", seed=3, nx=20, ny=10)
    )
    output_dir = scenario.write_package(tmp_path / "dam_break")
    loaded = read_scenario2_5d_package(output_dir)

    assert (output_dir / "scenario.json").exists()
    assert (output_dir / "bed.npy").exists()
    assert (output_dir / "initial_state.npz").exists()
    assert (output_dir / "features.json").exists()
    assert (output_dir / "probes.json").exists()
    assert loaded.to_json_dict() == scenario.to_json_dict()
    np.testing.assert_allclose(loaded.bed, scenario.bed)
    np.testing.assert_allclose(loaded.initial_state.depth, scenario.initial_state.depth)
    np.testing.assert_array_equal(loaded.initial_state.wet, scenario.initial_state.wet)
    assert loaded.validate().passed


def test_fixture_semantics_cover_core_schema_cases():
    dam = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="dam_break", nx=20, ny=10))
    left_depth = dam.initial_state.depth[:, : dam.grid.nx // 2].mean()
    right_depth = dam.initial_state.depth[:, dam.grid.nx // 2 :].mean()
    assert left_depth > right_depth

    shoreline = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="wet_dry_shoreline", nx=20, ny=10)
    )
    assert shoreline.initial_state.wet.any()
    assert (~shoreline.initial_state.wet).any()

    constriction = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="constriction", nx=32, ny=16)
    )
    assert any(feature.kind == "constriction" for feature in constriction.features)
    assert constriction.initial_state.u.max() > constriction.initial_state.u[:, 0].mean()


def test_scenario_json_points_to_solver_neutral_files(tmp_path):
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="bed_step", nx=18, ny=8))
    output_dir = scenario.write_package(tmp_path / "bed_step")
    data = json.loads((output_dir / "scenario.json").read_text(encoding="utf-8"))

    assert data["schema_version"] == "raftsim.scenario2_5d.v0"
    assert data["metadata"]["scenario_type"] == "fixture"
    assert data["array_files"]["bed"] == "bed.npy"
    assert data["array_files"]["initial_state"] == "initial_state.npz"
    assert data["array_files"]["features"] == "features.json"
    assert data["array_files"]["probes"] == "probes.json"


def test_procedural_generation_is_deterministic_for_seed():
    params = ProceduralScenario2_5DParameters(seed=21, nx=40, ny=24, feature_count=9)
    first = generate_procedural_scenario2_5d(params)
    second = generate_procedural_scenario2_5d(params)

    assert first.metadata.scenario_type == "procedural"
    assert first.to_json_dict() == second.to_json_dict()
    np.testing.assert_allclose(first.bed, second.bed)
    np.testing.assert_allclose(first.initial_state.depth, second.initial_state.depth)
    np.testing.assert_allclose(first.initial_state.u, second.initial_state.u)
    np.testing.assert_allclose(first.initial_state.v, second.initial_state.v)
    assert first.validate().passed


def test_procedural_scenario_has_rafting_features_and_banks():
    scenario = generate_procedural_scenario2_5d(
        ProceduralScenario2_5DParameters(seed=5, nx=48, ny=28, difficulty=0.7, feature_count=12)
    )
    feature_kinds = {feature.kind for feature in scenario.features}

    assert len(scenario.features) == 12
    assert {"rock", "constriction", "hole", "wave_train"}.issubset(feature_kinds)
    assert scenario.initial_state.wet.any()
    assert (~scenario.initial_state.wet).any()
    assert scenario.initial_state.u.max() > scenario.initial_state.u[:, 0].mean()
    assert len(scenario.probes) > 4


def test_procedural_package_round_trips(tmp_path):
    scenario = generate_procedural_scenario2_5d(ProceduralScenario2_5DParameters(seed=13, nx=36, ny=20))
    output_dir = scenario.write_package(tmp_path / "procedural")
    loaded = read_scenario2_5d_package(output_dir)

    assert loaded.to_json_dict() == scenario.to_json_dict()
    np.testing.assert_allclose(loaded.bed, scenario.bed)
    np.testing.assert_allclose(loaded.initial_state.depth, scenario.initial_state.depth)
    assert loaded.validate().passed
