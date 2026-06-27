import json

import pytest

from raftsim.dual_solver import CppSolverRunConfig, CppSolverRunResult
from raftsim.profiling import (
    profile_cpp_solver_runs,
    profile_probe_export_runs,
    profile_pyclaw_reference_runs,
    profile_raft_coupling_runs,
)
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


def test_profile_cpp_solver_runs_records_target_runtime_cost(tmp_path):
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="uniform_channel", nx=8, ny=5, duration=0.25)
    )
    clock_values = iter((1.0, 1.2, 2.0, 2.4))
    output_dirs = []

    def fake_runner(scenario_arg, *, output_dir, config):
        output_dirs.append(output_dir)
        assert scenario_arg is scenario
        assert config.steps == 4
        run_dir = output_dir / "cpp_solver" / scenario.metadata.scenario_id
        run_dir.mkdir(parents=True)
        manifest_path = run_dir / "manifest.json"
        validation_path = run_dir / "validation.json"
        manifest_path.write_text(json.dumps({"frames": ["frames/frame_0000.csv", "frames/frame_0001.csv"]}), encoding="utf-8")
        validation_path.write_text(json.dumps({"passed": True}), encoding="utf-8")
        return CppSolverRunResult(
            command=("raftsim_water_solver",),
            returncode=0,
            stdout="",
            stderr="",
            output_dir=run_dir,
            manifest_path=manifest_path,
            validation_path=validation_path,
            runtime_seconds=0.125,
        )

    report = profile_cpp_solver_runs(
        (scenario,),
        config=CppSolverRunConfig(executable=tmp_path / "raftsim_water_solver", steps=4, frame_interval=2),
        repetitions=2,
        output_dir=tmp_path / "runs",
        runner=fake_runner,
        clock=lambda: next(clock_values),
    )

    assert len(report.runs) == 2
    assert report.solver == "cpp_reduced"
    assert report.total_runtime_seconds == 0.25
    assert report.mean_runtime_seconds == 0.125
    assert report.runs[0].output_frames == 2
    assert report.runs[0].seconds_per_simulated_second == pytest.approx(0.5)
    assert report.runs[0].cell_seconds_per_simulated_second == pytest.approx(0.125 / (0.25 * 40))
    assert report.runs[0].validation_passed is True
    assert report.runs[0].run_status["profile_wall_seconds"] == pytest.approx(0.2)
    assert output_dirs == [
        tmp_path / "runs" / scenario.metadata.scenario_id / "rep_00",
        tmp_path / "runs" / scenario.metadata.scenario_id / "rep_01",
    ]


def test_profile_cpp_solver_runs_requires_repetitions(tmp_path):
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="flat_pool", nx=6, ny=4))

    with pytest.raises(ValueError):
        profile_cpp_solver_runs(
            (scenario,),
            config=CppSolverRunConfig(executable=tmp_path / "raftsim_water_solver"),
            repetitions=0,
        )


def test_profile_raft_coupling_runs_records_sampling_cost():
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="uniform_channel", nx=8, ny=5, duration=0.25)
    )
    clock_values = iter((3.0, 3.3))

    report = profile_raft_coupling_runs(
        (scenario,),
        repetitions=1,
        samples_per_run=3,
        clock=lambda: next(clock_values),
    )

    assert report.solver == "raft_coupling"
    assert len(report.runs) == 1
    assert report.runs[0].runtime_seconds == pytest.approx(0.3)
    assert report.runs[0].output_frames == 3
    assert report.runs[0].validation_passed is True
    assert report.runs[0].run_status["samples_per_run"] == 3
    assert report.runs[0].run_status["last_contribution_count"] > 0


def test_profile_raft_coupling_runs_requires_positive_samples():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="flat_pool", nx=6, ny=4))

    with pytest.raises(ValueError):
        profile_raft_coupling_runs((scenario,), samples_per_run=0)


def test_profile_probe_export_runs_records_export_cost(tmp_path):
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="flat_pool", nx=8, ny=5, duration=0.25)
    )
    clock_values = iter((4.0, 4.5))

    report = profile_probe_export_runs(
        (scenario,),
        config=PyClawRunConfig(num_output_times=1),
        repetitions=1,
        output_dir=tmp_path / "exports",
        clock=lambda: next(clock_values),
    )

    run_dir = tmp_path / "exports" / scenario.metadata.scenario_id / "rep_00"
    assert report.solver == "probe_export"
    assert report.runs[0].runtime_seconds == pytest.approx(0.5)
    assert report.runs[0].output_frames == 1
    assert report.runs[0].run_status["probe_count"] > 0
    assert report.runs[0].run_status["cross_section_count"] > 0
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "probes" / "upstream_center.csv").exists()


def test_profile_probe_export_runs_requires_repetitions():
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="flat_pool", nx=6, ny=4))

    with pytest.raises(ValueError):
        profile_probe_export_runs((scenario,), repetitions=0)
