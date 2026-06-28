import json

import pytest

from raftsim.examples.run_geoclaw_reference import main as geoclaw_main
from raftsim.geoclaw_reference import (
    GEOCLAW_CANONICAL_FIXTURES,
    GEOCLAW_CANONICAL_SUITE_SCHEMA,
    GEOCLAW_EXPORT_SCHEMA,
    GEOCLAW_REQUIRED_MODULES,
    GeoClawExportConfig,
    GeoClawAvailability,
    build_geoclaw_setup_report,
    canonical_geoclaw_scenarios,
    check_geoclaw_availability,
    export_canonical_geoclaw_scenarios,
    export_geoclaw_scenario,
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
