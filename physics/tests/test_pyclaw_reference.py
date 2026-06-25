import json

import numpy as np
import pytest

from raftsim.examples.run_pyclaw_reference import main as pyclaw_main
from raftsim.pyclaw_reference import (
    PyClawAvailability,
    PyClawRunConfig,
    PyClawUnavailableError,
    build_initial_pyclaw_reference_result,
    canonical_pyclaw_scenarios,
    check_pyclaw_availability,
    frame_from_scenario_initial_state,
    run_pyclaw_reference,
)
from raftsim.scenario2_5d import (
    FixtureScenario2_5DParameters,
    ProceduralScenario2_5DParameters,
    generate_fixture_scenario2_5d,
    generate_procedural_scenario2_5d,
)


def test_pyclaw_availability_check_is_machine_readable():
    status = check_pyclaw_availability()

    assert isinstance(status.available, bool)
    assert status.reason
    assert "available" in status.to_json_dict()


def test_initial_frame_exports_reference_fields():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="uniform_channel", nx=18, ny=8))
    frame = frame_from_scenario_initial_state(scenario)

    assert frame.h.shape == scenario.grid.shape
    assert frame.eta.shape == scenario.grid.shape
    assert frame.normal_x.shape == scenario.grid.shape
    assert frame.normal_y.shape == scenario.grid.shape
    assert frame.normal_z.shape == scenario.grid.shape
    assert frame.froude.shape == scenario.grid.shape
    np.testing.assert_allclose(frame.h, scenario.initial_state.depth)
    np.testing.assert_allclose(frame.eta, scenario.bed + scenario.initial_state.depth)
    assert frame.mass(scenario) > 0.0


def test_initial_reference_result_writes_expected_artifacts(tmp_path):
    scenario = generate_procedural_scenario2_5d(ProceduralScenario2_5DParameters(seed=4, nx=32, ny=18, feature_count=9))
    result = build_initial_pyclaw_reference_result(
        scenario,
        availability=PyClawAvailability(False, "test unavailable"),
    )
    output_dir = result.write_output(tmp_path / "reference")

    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "validation.json").exists()
    assert (output_dir / "frames" / "frame_0000.npz").exists()
    assert (output_dir / "probes" / "upstream_center.csv").exists()
    assert (output_dir / "cross_sections" / "mid_cross_section.npz").exists()
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["scenario_id"] == scenario.metadata.scenario_id
    assert manifest["frames"] == ["frames/frame_0000.npz"]


def test_canonical_pyclaw_scenario_set_includes_fixtures_and_procedural():
    scenarios = canonical_pyclaw_scenarios(seed=6)
    ids = [scenario.metadata.scenario_id for scenario in scenarios]

    assert len(scenarios) == 7
    assert "flat_pool_seed_6" in ids
    assert "wet_dry_shoreline_seed_6" in ids
    assert "procedural_rapid_seed_6" in ids
    assert all(scenario.validate().passed for scenario in scenarios)


def test_pyclaw_cli_check_allows_unavailable_environment():
    exit_code = pyclaw_main(["--check", "--allow-unavailable"])

    assert exit_code == 0


def test_pyclaw_cli_writes_unavailable_report_when_dependency_missing(tmp_path):
    status = check_pyclaw_availability()
    if status.available:
        pytest.skip("PyClaw is installed; unavailable-report path is not active.")

    exit_code = pyclaw_main(
        [
            "--fixture",
            "flat_pool",
            "--allow-unavailable",
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "pyclaw_unavailable.json").exists()


def test_pyclaw_reference_run_reports_missing_dependency_when_unavailable():
    status = check_pyclaw_availability()
    if status.available:
        pytest.skip("PyClaw is installed; missing-dependency path is not active.")
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="flat_pool", nx=12, ny=8))

    with pytest.raises(PyClawUnavailableError):
        run_pyclaw_reference(scenario, config=PyClawRunConfig(num_output_times=1))
