import json
import csv
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from raftsim.comparison import compare_dual_solver_diagnostics, compare_dual_solver_fields
from raftsim.dual_solver import CppSolverRunResult
from raftsim.examples.compare_cpp_to_geoclaw_reference import main as compare_cpp_geoclaw_main
from raftsim.examples.run_geoclaw_reference import main as geoclaw_main
from raftsim.geoclaw_reference import (
    GEOCLAW_CANONICAL_FIXTURES,
    GEOCLAW_CANONICAL_SUITE_SCHEMA,
    GEOCLAW_CASCADING_NORMALIZED_OUTPUT_SCHEMA,
    GEOCLAW_CASCADING_SUITE_SCHEMA,
    GEOCLAW_EXPORT_SCHEMA,
    GEOCLAW_NORMALIZED_OUTPUT_SCHEMA,
    GEOCLAW_RAFTING_CASES,
    GEOCLAW_RAFTING_SUITE_SCHEMA,
    GEOCLAW_REQUIRED_MODULES,
    GeoClawExportConfig,
    GeoClawAvailability,
    build_geoclaw_setup_report,
    canonical_geoclaw_scenarios,
    check_geoclaw_availability,
    export_cascading_geoclaw_scenarios,
    export_canonical_geoclaw_scenarios,
    export_geoclaw_cascading_package,
    export_rafting_geoclaw_scenarios,
    export_geoclaw_scenario,
    frame_from_geoclaw_initial_state,
    normalize_geoclaw_cascading_fixed_grid_output,
    normalize_geoclaw_fixed_grid_output,
    rafting_geoclaw_scenarios,
    write_geoclaw_setup_report,
)
from raftsim.real_world import generate_south_fork_american_cascading_scenario2_5d
from raftsim.scenario2_5d import (
    BoundaryHydrographSample2_5D,
    FixtureScenario2_5DParameters,
    generate_fixture_scenario2_5d,
)


def test_geoclaw_availability_check_is_machine_readable():
    status = check_geoclaw_availability()

    assert isinstance(status.available, bool)
    assert status.reason
    assert status.required_modules == GEOCLAW_REQUIRED_MODULES
    assert "available" in status.to_json_dict()
    assert "missing_modules" in status.to_json_dict()
    assert "missing_executables" in status.to_json_dict()


def test_geoclaw_setup_report_includes_docs_and_install_hints():
    report = build_geoclaw_setup_report(
        GeoClawAvailability(
            False,
            "test missing",
            required_modules=GEOCLAW_REQUIRED_MODULES,
            missing_modules=("clawpack.geoclaw",),
        )
    )
    data = report.to_json_dict()

    assert "pip install" in data["install_hint"]
    assert "gfortran" in data["system_dependency_hint"]
    assert any("geoclaw" in doc for doc in data["reference_docs"])
    assert data["availability"]["missing_modules"] == ("clawpack.geoclaw",)


def test_geoclaw_cli_check_allows_unavailable_environment(tmp_path):
    exit_code = geoclaw_main(["--check", "--allow-unavailable", "--output-dir", str(tmp_path)])

    assert exit_code == 0
    assert (tmp_path / "geoclaw_setup_report.json").exists()


def test_geoclaw_setup_report_writes_json(tmp_path):
    status = GeoClawAvailability(
        False,
        "test unavailable",
        required_modules=GEOCLAW_REQUIRED_MODULES,
        missing_modules=("clawpack.geoclaw",),
    )
    report_path = write_geoclaw_setup_report(tmp_path, status)

    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert data["availability"]["available"] is False
    assert data["availability"]["missing_modules"] == ["clawpack.geoclaw"]


def test_geoclaw_cli_fails_when_unavailable_without_override():
    status = check_geoclaw_availability()
    if status.available:
        pytest.skip("GeoClaw is installed; unavailable CLI path is not active.")

    assert geoclaw_main(["--check"]) == 1


def test_geoclaw_exporter_writes_solver_specific_files(tmp_path):
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="uniform_channel", seed=11, nx=18, ny=10)
    )
    result = export_geoclaw_scenario(
        scenario,
        tmp_path / "geoclaw" / scenario.metadata.scenario_id,
        config=GeoClawExportConfig(num_output_times=4),
    )
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

    assert manifest["schema"] == GEOCLAW_EXPORT_SCHEMA
    assert manifest["scenario_id"] == scenario.metadata.scenario_id
    assert manifest["files"]["makefile"] == "Makefile"
    assert manifest["files"]["qinit_fortran"] == "qinit.f90"
    assert manifest["files"]["boundary_adapter"] == "bc2amr.f90"
    assert manifest["boundary_semantics"]["bc_lower"] == ["user", "wall"]
    assert manifest["boundary_semantics"]["bc_upper"] == ["extrap", "wall"]
    west_boundary = manifest["boundary_semantics"]["edges"][0]
    assert west_boundary["edge"] == "west"
    assert west_boundary["geoclaw_code"] == "user"
    assert west_boundary["enforced_state"]["depth"] == pytest.approx(1.25)
    assert west_boundary["enforced_state"]["velocity"] == [1.4, 0.0]
    assert (result.output_dir / "Makefile").exists()
    assert (result.output_dir / "setrun.py").exists()
    assert (result.output_dir / "qinit.f90").exists()
    assert (result.output_dir / "bc2amr.f90").exists()
    assert (result.output_dir / "b.tt1").exists()
    assert (result.output_dir / "initial_state" / "initial_water_state.npz").exists()
    assert (result.output_dir / "initial_state" / "qinit.xyz").exists()
    assert (result.output_dir / "roughness" / "manning_n.npy").exists()
    assert (result.output_dir / "boundaries" / "boundaries.json").exists()
    assert (result.output_dir / "amr" / "amr_regions.json").exists()
    assert (result.output_dir / "fgout" / "fgout_grids.json").exists()
    assert (result.output_dir / "shared_scenario" / "scenario.json").exists()


def test_geoclaw_exporter_writes_runnable_app_files(tmp_path):
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="uniform_channel", seed=12, nx=18, ny=10)
    )
    result = export_geoclaw_scenario(
        scenario,
        tmp_path / "geoclaw" / scenario.metadata.scenario_id,
        config=GeoClawExportConfig(num_output_times=4),
    )

    makefile = (result.output_dir / "Makefile").read_text(encoding="utf-8")
    setrun = (result.output_dir / "setrun.py").read_text(encoding="utf-8")
    qinit = (result.output_dir / "qinit.f90").read_text(encoding="utf-8")
    topo_first_line = (result.output_dir / "b.tt1").read_text(encoding="utf-8").splitlines()[0]

    assert "Makefile.geoclaw" in makefile
    assert "./qinit.f90" in makefile
    assert "./bc2amr.f90" in makefile
    assert "EXCLUDE_SOURCES = $(GEOLIB)/bc2amr.f90" in makefile
    assert "rundata.fgout_data.fgout_grids = [fgout]" in setrun
    assert "setrun(package).write()" in setrun
    assert "clawdata.bc_lower = ['user', 'wall']" in setrun
    assert "clawdata.bc_upper = ['extrap', 'wall']" in setrun
    assert "b.tt1" in setrun
    assert "../initial_state/qinit.xyz" in qinit
    assert "read(unit,*,iostat=ios)" in qinit
    assert not topo_first_line.startswith("#")
    bc2amr = (result.output_dir / "bc2amr.f90").read_text(encoding="utf-8")
    assert "subroutine bc2amr" in bc2amr
    assert "west_has_depth = .true." in bc2amr
    assert "west_has_velocity = .true." in bc2amr
    assert "call apply_raftsim_boundary(1" in bc2amr


def test_geoclaw_exporter_records_no_adapter_when_boundaries_are_native(tmp_path):
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="flat_pool", seed=13, nx=18, ny=12)
    )
    result = export_geoclaw_scenario(scenario, tmp_path / "geoclaw" / scenario.metadata.scenario_id)
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    makefile = (result.output_dir / "Makefile").read_text(encoding="utf-8")

    assert manifest["files"]["boundary_adapter"] is None
    assert manifest["boundary_semantics"]["requires_user_boundary_adapter"] is False
    assert manifest["boundary_semantics"]["bc_lower"] == ["wall", "wall"]
    assert manifest["boundary_semantics"]["bc_upper"] == ["wall", "wall"]
    assert not (result.output_dir / "bc2amr.f90").exists()
    assert "./bc2amr.f90" not in makefile


def test_geoclaw_exporter_rejects_unapplied_boundary_hydrographs(tmp_path):
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="uniform_channel", seed=14, nx=18, ny=12)
    )
    west = scenario.boundaries[0]
    dynamic_west = replace(
        west,
        hydrograph=(
            BoundaryHydrographSample2_5D(time=0.0, depth=1.25, velocity=(1.4, 0.0)),
            BoundaryHydrographSample2_5D(time=4.0, depth=1.4, velocity=(1.7, 0.0)),
        ),
    )
    dynamic_scenario = replace(scenario, boundaries=(dynamic_west, *scenario.boundaries[1:]))

    with pytest.raises(ValueError, match="dynamic hydrograph"):
        export_geoclaw_scenario(dynamic_scenario, tmp_path / "geoclaw" / scenario.metadata.scenario_id)


def test_geoclaw_exporter_records_fixed_grid_times(tmp_path):
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="bed_step", seed=3, nx=16, ny=8, duration=5.0)
    )
    result = export_geoclaw_scenario(scenario, tmp_path / "bed_step", config=GeoClawExportConfig(num_output_times=5))
    fgout = json.loads((result.output_dir / "fgout" / "fgout_grids.json").read_text(encoding="utf-8"))

    grid = fgout["grids"][0]
    assert grid["x"]["num_cells"] == scenario.grid.nx
    assert grid["y"]["num_cells"] == scenario.grid.ny
    assert grid["times"] == [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    assert "froude" in grid["fields"]


def test_geoclaw_cli_exports_fixture(tmp_path):
    exit_code = geoclaw_main(
        [
            "--fixture",
            "flat_pool",
            "--seed",
            "7",
            "--nx",
            "14",
            "--ny",
            "8",
            "--allow-unavailable",
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "flat_pool_seed_7" / "manifest.json").exists()


def test_geoclaw_cli_exports_south_fork_flow_band(tmp_path):
    exit_code = geoclaw_main(
        [
            "--south-fork-flow-band",
            "low_runnable",
            "--south-fork-difficulty",
            "beginner",
            "--nx",
            "18",
            "--ny",
            "10",
            "--num-output-times",
            "2",
            "--amr-min-level",
            "2",
            "--amr-max-level",
            "2",
            "--allow-unavailable",
            "--output-dir",
            str(tmp_path),
        ]
    )
    scenario_id = "american_south_fork_chili_bar_to_coloma_low_runnable_beginner"
    manifest = json.loads((tmp_path / scenario_id / "manifest.json").read_text(encoding="utf-8"))

    assert exit_code == 0
    assert manifest["scenario_metadata"]["flow_band"] == "low_runnable"
    assert manifest["scenario_metadata"]["difficulty_preset"] == "beginner"
    assert manifest["config"]["amr_min_level"] == 2
    assert manifest["config"]["amr_max_level"] == 2


def test_canonical_geoclaw_scenarios_include_extended_fixtures():
    scenarios = canonical_geoclaw_scenarios(seed=6)
    ids = [scenario.metadata.scenario_id for scenario in scenarios]

    assert len(scenarios) == 8
    assert tuple(scenario.metadata.fixture_kind for scenario in scenarios) == GEOCLAW_CANONICAL_FIXTURES
    assert "sloping_manning_channel_seed_6" in ids
    assert "drop_ledge_seed_6" in ids
    assert all(scenario.validate().passed for scenario in scenarios)


def test_export_canonical_geoclaw_scenarios_writes_suite_manifest(tmp_path):
    suite = export_canonical_geoclaw_scenarios(
        tmp_path / "canonical",
        seed=2,
        config=GeoClawExportConfig(num_output_times=2),
    )
    manifest = json.loads(suite.manifest_path.read_text(encoding="utf-8"))

    assert manifest["schema"] == GEOCLAW_CANONICAL_SUITE_SCHEMA
    assert manifest["scenario_count"] == 8
    assert manifest["fixtures"] == list(GEOCLAW_CANONICAL_FIXTURES)
    assert len(manifest["exports"]) == 8
    assert all((suite.output_dir / export["manifest"]).exists() for export in manifest["exports"])


def test_geoclaw_cli_exports_canonical_fixture_suite(tmp_path):
    exit_code = geoclaw_main(
        [
            "--all-fixtures",
            "--seed",
            "3",
            "--allow-unavailable",
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "canonical_geoclaw_seed_3" / "canonical_suite_manifest.json").exists()


def test_rafting_geoclaw_scenarios_include_feature_cases_and_real_world_flows():
    scenarios = rafting_geoclaw_scenarios(seed=20)
    synthetic = [scenario for scenario in scenarios if scenario.metadata.scenario_type == "procedural"]
    real_world = [scenario for scenario in scenarios if scenario.metadata.scenario_type == "real_world"]

    assert [scenario.metadata.provenance["geoclaw_rafting_case"] for scenario in synthetic] == list(GEOCLAW_RAFTING_CASES)
    assert {scenario.metadata.flow_band for scenario in real_world} == {
        "low_runnable",
        "median_runnable",
        "high_runnable",
    }
    assert len(scenarios) == 9
    assert all(scenario.validate().passed for scenario in scenarios)


def test_export_rafting_geoclaw_scenarios_writes_suite_manifest(tmp_path):
    suite = export_rafting_geoclaw_scenarios(
        tmp_path / "rafting",
        seed=4,
        config=GeoClawExportConfig(num_output_times=2),
    )
    manifest = json.loads(suite.manifest_path.read_text(encoding="utf-8"))

    assert manifest["schema"] == GEOCLAW_RAFTING_SUITE_SCHEMA
    assert manifest["scenario_count"] == 9
    assert manifest["synthetic_cases"] == list(GEOCLAW_RAFTING_CASES)
    assert set(manifest["real_world_flow_bands"]) == {"low_runnable", "median_runnable", "high_runnable"}
    assert all((suite.output_dir / export["manifest"]).exists() for export in manifest["exports"])


def test_geoclaw_cli_exports_rafting_suite(tmp_path):
    exit_code = geoclaw_main(
        [
            "--rafting-suite",
            "--seed",
            "5",
            "--allow-unavailable",
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "rafting_geoclaw_seed_5" / "rafting_suite_manifest.json").exists()


def test_geoclaw_cascading_export_preserves_reach_drop_metadata(tmp_path):
    package = generate_south_fork_american_cascading_scenario2_5d(nx=72, ny=28, duration=0.5)
    export = export_geoclaw_cascading_package(
        package,
        tmp_path / "cascading_export",
        config=GeoClawExportConfig(num_output_times=2),
    )
    manifest = json.loads(export.manifest_path.read_text(encoding="utf-8"))

    assert manifest["schema"] == GEOCLAW_EXPORT_SCHEMA
    assert manifest["cascading_package"]["reach_count"] == 7
    assert manifest["cascading_package"]["drop_transition_count"] == 1
    assert "shared_cascading_package/cascading_metadata.json" in export.files
    assert (export.output_dir / "shared_cascading_package" / "cascading_annotations.npz").exists()


def test_export_cascading_geoclaw_scenarios_writes_suite_manifest(tmp_path):
    suite = export_cascading_geoclaw_scenarios(
        tmp_path / "cascading_suite",
        config=GeoClawExportConfig(num_output_times=2),
        nx=72,
        ny=28,
        duration=0.5,
    )
    manifest = json.loads(suite.manifest_path.read_text(encoding="utf-8"))

    assert manifest["schema"] == GEOCLAW_CASCADING_SUITE_SCHEMA
    assert manifest["scenario_count"] == 3
    assert manifest["flow_bands"] == ["low_runnable", "median_runnable", "high_runnable"]
    assert all((suite.output_dir / export["manifest"]).exists() for export in manifest["exports"])


def test_normalize_geoclaw_cascading_fixed_grid_output_writes_reach_windows(tmp_path):
    package = generate_south_fork_american_cascading_scenario2_5d(nx=72, ny=28, duration=0.5)
    export = export_geoclaw_cascading_package(
        package,
        tmp_path / "cascading_export",
        config=GeoClawExportConfig(num_output_times=2),
    )
    normalized = normalize_geoclaw_cascading_fixed_grid_output(export.output_dir, tmp_path / "cascading_normalized")
    manifest = json.loads(normalized.manifest_path.read_text(encoding="utf-8"))
    first_reach_frame = tmp_path / "cascading_normalized" / manifest["reach_windows"][0]["frames"][0]

    assert manifest["schema"] == GEOCLAW_CASCADING_NORMALIZED_OUTPUT_SCHEMA
    assert manifest["stitched_manifest"] == "stitched/manifest.json"
    assert normalized.reach_window_count == 7
    assert normalized.drop_transition_window_count == 1
    assert first_reach_frame.exists()
    with np.load(first_reach_frame) as data:
        assert data["h"].shape[0] == package.scenario.grid.ny
        assert data["h"].shape[1] < package.scenario.grid.nx


def test_geoclaw_cli_exports_cascading_suite(tmp_path):
    exit_code = geoclaw_main(
        [
            "--cascading-suite",
            "--allow-unavailable",
            "--nx",
            "72",
            "--ny",
            "28",
            "--num-output-times",
            "2",
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "south_fork_cascading_geoclaw" / "cascading_suite_manifest.json").exists()


def test_geoclaw_initial_state_frame_exports_normalized_fields():
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="uniform_channel", seed=15, nx=18, ny=10)
    )
    frame = frame_from_geoclaw_initial_state(scenario)

    assert frame.h.shape == scenario.grid.shape
    assert frame.eta.shape == scenario.grid.shape
    assert frame.normal_x.shape == scenario.grid.shape
    assert frame.normal_y.shape == scenario.grid.shape
    assert frame.normal_z.shape == scenario.grid.shape
    assert frame.froude.shape == scenario.grid.shape
    assert frame.mass(scenario) > 0.0


def test_normalize_geoclaw_fixed_grid_output_writes_frozen_schema(tmp_path):
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="uniform_channel", seed=16, nx=18, ny=10)
    )
    export = export_geoclaw_scenario(scenario, tmp_path / "export")
    normalized = normalize_geoclaw_fixed_grid_output(export.output_dir, tmp_path / "normalized")
    manifest = json.loads(normalized.manifest_path.read_text(encoding="utf-8"))

    assert manifest["schema"] == GEOCLAW_NORMALIZED_OUTPUT_SCHEMA
    assert manifest["frames"] == ["frames/frame_0000.npz"]
    assert manifest["run_status"]["mode"] == "export_initial_state_only"
    assert (normalized.output_dir / "validation.json").exists()
    assert (normalized.output_dir / "probes" / "upstream_center.csv").exists()
    assert (normalized.output_dir / "cross_sections" / "mid_cross_section.npz").exists()


def test_normalize_geoclaw_fixed_grid_output_reads_npz_frames(tmp_path):
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="uniform_channel", seed=17, nx=18, ny=10)
    )
    export = export_geoclaw_scenario(scenario, tmp_path / "export")
    fgout_dir = export.output_dir / "fgout_frames"
    fgout_dir.mkdir()
    frame = frame_from_geoclaw_initial_state(scenario, time=1.25)
    frame.write_npz(fgout_dir / "frame_0001.npz")

    normalized = normalize_geoclaw_fixed_grid_output(export.output_dir, tmp_path / "normalized")
    manifest = json.loads(normalized.manifest_path.read_text(encoding="utf-8"))

    assert manifest["run_status"]["mode"] == "fgout_npz"
    assert manifest["frames"] == ["frames/frame_0000.npz"]
    assert normalized.frame_count == 1


def test_geoclaw_cli_normalizes_export(tmp_path):
    scenario = generate_fixture_scenario2_5d(FixtureScenario2_5DParameters(fixture="flat_pool", seed=18, nx=14, ny=8))
    export = export_geoclaw_scenario(scenario, tmp_path / "export")
    exit_code = geoclaw_main(["--normalize-export", str(export.output_dir), "--output-dir", str(tmp_path / "normalized")])

    assert exit_code == 0
    assert (tmp_path / "normalized" / "manifest.json").exists()


def test_geoclaw_cli_runs_existing_export_with_normalization(monkeypatch, tmp_path, capsys):
    class FakeRunResult:
        scenario_id = "fake_geoclaw"
        export_dir = tmp_path / "export"
        returncode = 0
        frame_count = 2
        passed = True

    class FakeNormalizedResult:
        scenario_id = "fake_geoclaw"
        manifest_path = tmp_path / "export" / "normalized" / "manifest.json"
        frame_count = 2

    calls = {}

    def fake_run(export_dir, *, config, export_config):
        calls["run"] = (export_dir, config.timeout_seconds, config.make_target, export_config.num_output_times)
        return FakeRunResult()

    def fake_normalize(export_dir, output_dir=None, *, config=None):
        calls["normalize"] = (export_dir, output_dir, config.num_output_times)
        return FakeNormalizedResult()

    monkeypatch.setattr("raftsim.examples.run_geoclaw_reference.run_geoclaw_export", fake_run)
    monkeypatch.setattr("raftsim.examples.run_geoclaw_reference.normalize_geoclaw_fixed_grid_output", fake_normalize)

    exit_code = geoclaw_main(["--run-export", str(tmp_path / "export"), "--num-output-times", "2"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert calls["run"] == (tmp_path / "export", 300.0, ".output", 2)
    assert calls["normalize"] == (tmp_path / "export", tmp_path / "export" / "normalized", 2)
    assert "run_frames=2" in output
    assert "normalized_frames=2" in output


def test_comparison_harness_accepts_geoclaw_reference_manifest(tmp_path):
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="flat_pool", seed=19, nx=12, ny=8)
    )
    scenario_dir = scenario.write_package(tmp_path / "scenario" / scenario.metadata.scenario_id)
    export = export_geoclaw_scenario(scenario, tmp_path / "geoclaw_export")
    normalized = normalize_geoclaw_fixed_grid_output(export.output_dir, tmp_path / "geoclaw_normalized")
    frame = frame_from_geoclaw_initial_state(scenario)
    cpp_dir = tmp_path / "cpp_solver" / scenario.metadata.scenario_id
    _write_cpp_frame_csv(cpp_dir / "frames" / "frame_0000.csv", frame)
    _write_json(
        cpp_dir / "manifest.json",
        {
            "frames": ["frames/frame_0000.csv"],
            "probes": [],
            "cross_sections": [],
        },
    )
    _write_json(
        tmp_path / "dual_solver_manifest.json",
        {
            "scenario_id": scenario.metadata.scenario_id,
            "scenario_package": str(scenario_dir.relative_to(tmp_path)),
            "geoclaw": {
                "solver": "geoclaw",
                "output_dir": str(normalized.output_dir.relative_to(tmp_path)),
                "manifest": str(normalized.manifest_path.relative_to(tmp_path)),
                "validation": str((normalized.output_dir / "validation.json").relative_to(tmp_path)),
                "runtime_seconds": 0.0,
            },
            "cpp": {
                "output_dir": str(cpp_dir.relative_to(tmp_path)),
                "manifest": str((cpp_dir / "manifest.json").relative_to(tmp_path)),
                "validation": str((cpp_dir / "validation.json").relative_to(tmp_path)),
                "runtime_seconds": 0.0,
            },
        },
    )

    field_report = compare_dual_solver_fields(tmp_path)
    diagnostic_report = compare_dual_solver_diagnostics(tmp_path)

    assert field_report.frame_comparisons[0].reference_solver == "geoclaw"
    assert field_report.frame_comparisons[0].field_errors[0].linf == 0.0
    assert diagnostic_report.reference_solver == "geoclaw"
    assert diagnostic_report.pyclaw.solver == "geoclaw"


def test_cpp_geoclaw_cli_wires_existing_normalized_reference(monkeypatch, tmp_path):
    scenario = generate_fixture_scenario2_5d(
        FixtureScenario2_5DParameters(fixture="flat_pool", seed=20, nx=12, ny=8)
    )
    scenario_dir = scenario.write_package(tmp_path / "scenario" / scenario.metadata.scenario_id)
    export = export_geoclaw_scenario(scenario, tmp_path / "geoclaw_export")
    normalized = normalize_geoclaw_fixed_grid_output(export.output_dir, tmp_path / "geoclaw_normalized")
    frame = frame_from_geoclaw_initial_state(scenario)

    def fake_run_cpp_solver_scenario(scenario_or_path, *, output_dir, config):
        cpp_dir = tmp_path / "comparison" / "cpp_solver" / scenario.metadata.scenario_id
        _write_cpp_frame_csv(cpp_dir / "frames" / "frame_0000.csv", frame)
        _write_json(
            cpp_dir / "manifest.json",
            {
                "frames": ["frames/frame_0000.csv"],
                "probes": [],
                "cross_sections": [],
            },
        )
        _write_json(cpp_dir / "validation.json", {"passed": True})
        return CppSolverRunResult(
            command=("fake_cpp",),
            returncode=0,
            stdout="",
            stderr="",
            output_dir=cpp_dir,
            manifest_path=cpp_dir / "manifest.json",
            validation_path=cpp_dir / "validation.json",
            runtime_seconds=0.01,
        )

    monkeypatch.setattr(
        "raftsim.examples.compare_cpp_to_geoclaw_reference.run_cpp_solver_scenario",
        fake_run_cpp_solver_scenario,
    )

    exit_code = compare_cpp_geoclaw_main(
        [
            "--scenario-dir",
            str(scenario_dir),
            "--geoclaw-normalized",
            str(normalized.output_dir),
            "--cpp-solver",
            str(tmp_path / "fake_cpp"),
            "--output-dir",
            str(tmp_path / "comparison"),
        ]
    )
    manifest = json.loads((tmp_path / "comparison" / "dual_solver_manifest.json").read_text(encoding="utf-8"))

    assert exit_code == 0
    assert manifest["geoclaw"]["solver"] == "geoclaw"
    assert manifest["runtime"]["cpp_runtime_seconds"] == 0.01
    assert (tmp_path / "comparison" / "field_comparison.json").exists()
    assert (tmp_path / "comparison" / "probe_comparison.json").exists()
    assert (tmp_path / "comparison" / "diagnostic_comparison.json").exists()
    assert (tmp_path / "comparison" / "threshold_evaluation.json").exists()


def test_cpp_geoclaw_cli_loads_committed_fixture_registry(monkeypatch, tmp_path):
    physics_dir = Path(__file__).resolve().parents[1]
    registry = (
        physics_dir
        / "data"
        / "real_world"
        / "south_fork_american_chili_bar"
        / "geoclaw_reference"
        / "amr_2_3"
        / "fixture_registry.json"
    )
    fixture_dir = registry.parent / "low_runnable"

    def fake_run_cpp_solver_scenario(scenario_or_path, *, output_dir, config):
        cpp_dir = tmp_path / "registry_comparison" / "cpp_solver" / scenario_or_path.metadata.scenario_id
        _write_cpp_frame_csv_from_npz(cpp_dir / "frames" / "frame_0000.csv", fixture_dir / "frames" / "frame_0000.npz")
        _write_cpp_frame_csv_from_npz(cpp_dir / "frames" / "frame_0001.csv", fixture_dir / "frames" / "frame_0004.npz")
        _write_json(
            cpp_dir / "manifest.json",
            {
                "frames": ["frames/frame_0000.csv", "frames/frame_0001.csv"],
                "probes": [],
                "cross_sections": [],
            },
        )
        _write_json(cpp_dir / "validation.json", {"passed": True})
        return CppSolverRunResult(
            command=("fake_cpp",),
            returncode=0,
            stdout="",
            stderr="",
            output_dir=cpp_dir,
            manifest_path=cpp_dir / "manifest.json",
            validation_path=cpp_dir / "validation.json",
            runtime_seconds=0.01,
        )

    monkeypatch.setattr(
        "raftsim.examples.compare_cpp_to_geoclaw_reference.run_cpp_solver_scenario",
        fake_run_cpp_solver_scenario,
    )

    exit_code = compare_cpp_geoclaw_main(
        [
            "--fixture-registry",
            str(registry),
            "--flow-band",
            "low_runnable",
            "--cpp-solver",
            str(tmp_path / "fake_cpp"),
            "--output-dir",
            str(tmp_path / "registry_comparison"),
        ]
    )
    manifest = json.loads((tmp_path / "registry_comparison" / "dual_solver_manifest.json").read_text(encoding="utf-8"))

    assert exit_code == 0
    assert manifest["scenario_id"] == "american_south_fork_chili_bar_to_coloma_low_runnable_beginner"
    assert manifest["geoclaw"]["manifest"].endswith("low_runnable/manifest.json")
    assert (tmp_path / "registry_comparison" / "threshold_evaluation.json").exists()


def _write_cpp_frame_csv(path, frame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "row",
        "col",
        "h",
        "eta",
        "u",
        "v",
        "hu",
        "hv",
        "wet",
        "normal_x",
        "normal_y",
        "normal_z",
        "froude",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for row in range(frame.h.shape[0]):
            for col in range(frame.h.shape[1]):
                writer.writerow(
                    [
                        row,
                        col,
                        frame.h[row, col],
                        frame.eta[row, col],
                        frame.u[row, col],
                        frame.v[row, col],
                        frame.hu[row, col],
                        frame.hv[row, col],
                        int(frame.wet[row, col]),
                        frame.normal_x[row, col],
                        frame.normal_y[row, col],
                        frame.normal_z[row, col],
                        frame.froude[row, col],
                    ]
                )


def _write_cpp_frame_csv_from_npz(path, frame_path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with np.load(frame_path) as data:
        columns = [
            "row",
            "col",
            "h",
            "eta",
            "u",
            "v",
            "hu",
            "hv",
            "wet",
            "normal_x",
            "normal_y",
            "normal_z",
            "froude",
        ]
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(columns)
            h = data["h"]
            for row in range(h.shape[0]):
                for col in range(h.shape[1]):
                    writer.writerow(
                        [
                            row,
                            col,
                            data["h"][row, col],
                            data["eta"][row, col],
                            data["u"][row, col],
                            data["v"][row, col],
                            data["hu"][row, col],
                            data["hv"][row, col],
                            int(data["wet"][row, col]),
                            data["normal_x"][row, col],
                            data["normal_y"][row, col],
                            data["normal_z"][row, col],
                            data["froude"][row, col],
                        ]
                    )


def _write_json(path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
