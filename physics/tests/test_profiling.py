import json

import pytest

from raftsim.profiling import profile_pyclaw_reference_runs
from raftsim.pyclaw_reference import PyClawAvailability, PyClawRunConfig, build_initial_pyclaw_reference_result
from raftsim.scenario2_5d import FixtureScenario2_5DParameters, generate_fixture_scenario2_5d


def test_profile_pyclaw_reference_runs_records_research_loop_cost(tmp_path):
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="flat_pool", nx=6, ny=4, duration=0.5)
    )
    clock_values = iter((10.0, 12.0, 20.0, 23.0))
    output_dirs = []

    def fake_runner(scenario_arg, *, config, output_dir=None):
        output_dirs.append(output_dir)
        assert scenario_arg is scenario
        assert config.num_output_times == 1
        return build_initial_pyclaw_reference_result(
            scenario_arg,
            config=config,
            availability=PyClawAvailability(False, "test runner"),
        )

    report = profile_pyclaw_reference_runs(
        (scenario,),
        config=PyClawRunConfig(num_output_times=1),
        repetitions=2,
        output_dir=tmp_path / "runs",
        runner=fake_runner,
        clock=lambda: next(clock_values),
    )

    assert len(report.runs) == 2
    assert report.total_runtime_seconds == 5.0
    assert report.mean_runtime_seconds == 2.5
    assert report.max_runtime_seconds == 3.0
    assert report.runs[0].runtime_seconds == 2.0
    assert report.runs[0].seconds_per_simulated_second == pytest.approx(4.0)
    assert report.runs[0].cell_seconds_per_simulated_second == pytest.approx(2.0 / (0.5 * 24))
    assert output_dirs == [
        tmp_path / "runs" / scenario.metadata.scenario_id / "rep_00",
        tmp_path / "runs" / scenario.metadata.scenario_id / "rep_01",
    ]

    report_path = report.write_json(tmp_path / "pyclaw_profile.json")
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["solver"] == "pyclaw"
    assert payload["summary"]["run_count"] == 2
    assert payload["runs"][0]["scenario_id"] == scenario.metadata.scenario_id


def test_profile_pyclaw_reference_runs_requires_repetitions():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="flat_pool", nx=6, ny=4))

    with pytest.raises(ValueError):
        profile_pyclaw_reference_runs((scenario,), repetitions=0)
