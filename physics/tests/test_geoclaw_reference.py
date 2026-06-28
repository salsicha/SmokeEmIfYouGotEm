import json
import csv

import pytest

from raftsim.comparison import compare_dual_solver_diagnostics, compare_dual_solver_fields
from raftsim.examples.run_geoclaw_reference import main as geoclaw_main
from raftsim.geoclaw_reference import (
    GEOCLAW_CANONICAL_FIXTURES,
    GEOCLAW_CANONICAL_SUITE_SCHEMA,
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
    export_canonical_geoclaw_scenarios,
    export_rafting_geoclaw_scenarios,
    export_geoclaw_scenario,
    frame_from_geoclaw_initial_state,
    normalize_geoclaw_fixed_grid_output,
    rafting_geoclaw_scenarios,
    write_geoclaw_setup_report,
)
from raftsim.scenario2_5d import FixtureScenario2_5DParameters, generate_fixture_scenario2_5d


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
    assert (result.output_dir / "setrun.py").exists()
    assert (result.output_dir / "topography" / "bed_topography.xyz").exists()
    assert (result.output_dir / "initial_state" / "initial_water_state.npz").exists()
    assert (result.output_dir / "initial_state" / "qinit.xyz").exists()
    assert (result.output_dir / "roughness" / "manning_n.npy").exists()
    assert (result.output_dir / "boundaries" / "boundaries.json").exists()
    assert (result.output_dir / "amr" / "amr_regions.json").exists()
    assert (result.output_dir / "fgout" / "fgout_grids.json").exists()
    assert (result.output_dir / "shared_scenario" / "scenario.json").exists()


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


def _write_json(path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
