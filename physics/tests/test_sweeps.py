import json

import pytest

from raftsim.sweeps import (
    ParameterSweepCandidate,
    default_parameter_sweep_candidates,
    run_raft_force_parameter_sweep,
)
from raftsim.scenario2_5d import FixtureScenario2_5DParameters, generate_fixture_scenario2_5d


def test_default_parameter_sweep_candidates_cover_required_axes():
    candidates = default_parameter_sweep_candidates((0.5, 1.0, 1.5))
    labels = {candidate.label for candidate in candidates}

    assert "baseline" in labels
    assert "roughness_scale_0p5" in labels
    assert "feature_strength_scale_1p5" in labels
    assert "raft_drag_scale_0p5" in labels
    assert "buoyancy_density_scale_1p5" in labels
    assert "grounding_friction_scale_0p5" in labels
    assert "contact_stiffness_scale_1p5" in labels
    assert "contact_damping_scale_0p5" in labels
    assert len(candidates) == 15


def test_parameter_sweep_candidates_reject_non_positive_scales():
    with pytest.raises(ValueError):
        ParameterSweepCandidate("bad", roughness_scale=0.0)
    with pytest.raises(ValueError):
        default_parameter_sweep_candidates((1.0, -1.0))


def test_run_raft_force_parameter_sweep_records_force_response(tmp_path):
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="uniform_channel", nx=10, ny=6, duration=0.25)
    )
    candidates = (
        ParameterSweepCandidate("baseline"),
        ParameterSweepCandidate("more_buoyancy", buoyancy_density_scale=1.25),
    )

    report = run_raft_force_parameter_sweep(scenario, candidates=candidates)
    report_path = report.write_json(tmp_path / "parameter_sweep.json")
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    baseline, more_buoyancy = report.results
    assert report.scenario_id == scenario.metadata.scenario_id
    assert payload["candidate_count"] == 2
    assert baseline.candidate.label == "baseline"
    assert more_buoyancy.total_force[2] > baseline.total_force[2]
    assert baseline.contribution_count > 0
    assert baseline.max_contribution_force > 0.0


def test_run_raft_force_parameter_sweep_requires_candidates():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="flat_pool", nx=6, ny=4))

    with pytest.raises(ValueError):
        run_raft_force_parameter_sweep(scenario, candidates=())
