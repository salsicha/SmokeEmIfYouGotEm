"""Behavioral tests for the Troublemaker reach-local C3 water-window package."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from raftsim.scenario2_5d import read_scenario2_5d_package
from raftsim.troublemaker_c3_window import (
    FLOW_BAND_IDS,
    RAPID_STATION_M,
    SCENARIO_ROOT_RELATIVE,
    TroublemakerBedParameters,
    _load_final_frame_fields,
    evaluate_troublemaker_behavior,
    generate_troublemaker_scenario2_5d,
    load_flow_bands,
    troublemaker_solver_config,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_ROOT = REPO_ROOT / SCENARIO_ROOT_RELATIVE


@pytest.fixture(scope="module")
def committed_packages() -> dict[str, object]:
    packages = {}
    for band_id in FLOW_BAND_IDS:
        package_dir = SCENARIO_ROOT / band_id
        if not (package_dir / "scenario.json").exists():
            pytest.skip("Troublemaker scenario packages are not committed yet.")
        packages[band_id] = read_scenario2_5d_package(package_dir)
    return packages


def test_committed_packages_have_window_geometry_and_validate(committed_packages):
    for band_id, scenario in committed_packages.items():
        validation = scenario.validate()
        assert validation.passed, validation.summary_lines()
        grid = scenario.grid
        assert grid.dx == pytest.approx(2.0)
        assert grid.dy == pytest.approx(2.0)
        assert (grid.nx - 1) * grid.dx == pytest.approx(600.0)
        assert scenario.metadata.flow_band == band_id
        assert scenario.metadata.provenance["adopted_axis_station_m"] == pytest.approx(RAPID_STATION_M)
        assert scenario.metadata.provenance["bed_geometry_authority"] == "interpreted_bed_geometry"
        assert scenario.metadata.provenance["dem_cannot_resolve_in_channel_rocks"] is True
        assert scenario.metadata.provenance["production_promoted"] is False
        assert scenario.metadata.provenance["pending_human_review"] is True


def test_committed_packages_carry_all_seventeen_c1_subfeatures(committed_packages):
    catalog = json.loads(
        (REPO_ROOT / "physics/data/real_world/named_rapid_source_catalog.json").read_text(encoding="utf-8")
    )
    troublemaker = next(
        rapid
        for river in catalog["rivers"]
        for rapid in river.get("rapids", [])
        if rapid.get("name") == "Troublemaker"
    )
    catalog_ids = {entry["subfeature_id"] for entry in troublemaker["feature_inventory"]}
    for scenario in committed_packages.values():
        package_ids = {feature.metadata["subfeature_id"] for feature in scenario.features}
        assert package_ids == catalog_ids
        assert len(scenario.features) == 17
        for feature in scenario.features:
            assert feature.metadata["interpreted_bed_geometry"] is True
            assert scenario.grid.contains(feature.center)


def test_bed_geometry_expresses_headline_features(committed_packages):
    scenario = committed_packages["median_runnable"]
    p = TroublemakerBedParameters()
    bed = scenario.bed
    grid = scenario.grid
    xs = grid.x_coordinates()
    ys = grid.y_coordinates()

    def region(x_range, y_range):
        cols = (xs >= x_range[0]) & (xs <= x_range[1])
        rows = (ys >= y_range[0]) & (ys <= y_range[1])
        return bed[np.ix_(rows, cols)]

    # Entry island crests above the surrounding right-channel invert.
    island = region((p.island_x_center - 4.0, p.island_x_center + 4.0), (p.island_y_center - 3.0, p.island_y_center + 3.0))
    right_channel = region((p.island_x_center - 4.0, p.island_x_center + 4.0), (-11.0, -6.0))
    assert float(island.max()) - float(right_channel.min()) > 1.5

    # The gut ledge crest drops into a deeper plunge pool.
    ledge = region((p.gut_x - 2.0, p.gut_x), (-3.0, 3.0))
    pool = region((p.gut_pool_x[0] + 2.0, p.gut_pool_x[1] - 2.0), (-4.0, 4.0))
    assert float(ledge.min()) - float(pool.min()) > 0.6

    # Gunsight rock is a local high splitting two lower chutes.
    rock = region((p.gunsight_x - 2.0, p.gunsight_x + 2.0), (p.gunsight_y - 2.0, p.gunsight_y + 2.0))
    left_chute = region((p.gunsight_x - 2.0, p.gunsight_x + 4.0), p.gunsight_left_chute_y)
    right_chute = region((p.gunsight_x - 2.0, p.gunsight_x + 4.0), p.gunsight_right_chute_y)
    assert float(rock.max()) > float(left_chute.min()) + 2.0
    assert float(rock.max()) > float(right_chute.min()) + 2.0

    # The sneak slot is carved below its berm.
    slot = region((p.sneak_x[0] + 10.0, p.sneak_x[1] - 10.0), p.sneak_y)
    berm = region((p.sneak_x[0] + 10.0, p.sneak_x[1] - 10.0), p.sneak_berm_y)
    assert float(np.median(berm)) - float(np.median(slot)) > 0.5


def test_generation_is_deterministic(committed_packages):
    regenerated = generate_troublemaker_scenario2_5d(REPO_ROOT, "median_runnable")
    committed = committed_packages["median_runnable"]
    np.testing.assert_array_equal(regenerated.bed, committed.bed)
    np.testing.assert_array_equal(regenerated.initial_state.depth, committed.initial_state.depth)
    np.testing.assert_array_equal(regenerated.initial_state.u, committed.initial_state.u)
    assert regenerated.metadata.provenance["stage_west_m"] == committed.metadata.provenance["stage_west_m"]


def test_flow_band_boundaries_scale_with_committed_presets(committed_packages):
    bands = load_flow_bands(REPO_ROOT)
    stages = {}
    for band_id, scenario in committed_packages.items():
        west = next(b for b in scenario.boundaries if b.edge == "west")
        east = next(b for b in scenario.boundaries if b.edge == "east")
        assert west.kind == "inflow"
        assert east.kind == "outflow"
        assert west.metadata["target_discharge_m3s"] == pytest.approx(float(bands[band_id]["discharge_m3s"]))
        stages[band_id] = west.stage
    assert stages["low_runnable"] < stages["median_runnable"] < stages["high_runnable"]


def test_window_manifest_records_honesty_labels():
    manifest_path = SCENARIO_ROOT / "window_manifest.json"
    if not manifest_path.exists():
        pytest.skip("Troublemaker window manifest is not committed yet.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    honesty = manifest["honesty"]
    assert honesty["bed_geometry_authority"] == "interpreted_bed_geometry"
    assert "cannot resolve in-channel rocks" in honesty["dem_cannot_resolve_in_channel_rocks"]
    assert honesty["production_promoted"] is False
    assert honesty["pending_human_review"] is True
    assert manifest["conditioning"]["monotone_downstream"] is True
    assert manifest["sources"]["dem_sha256"] == (
        "ebb6682d52a6a011854b4679d43ba56f1a1d62642852cce9e045b805820e59f0"
    )
    assert manifest["geometry"]["catalog_point_to_channel_snap_distance_m"] < 100.0


def test_behavioral_validation_report_passes_headline_gate():
    report_path = SCENARIO_ROOT / "behavioral_validation.json"
    if not report_path.exists():
        pytest.skip("Troublemaker behavioral validation report is not committed yet.")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["solver"]["solver_mode"] == "finite_volume"
    assert report["solver"]["flux_scheme"] == "hll"
    assert report["solver"]["spatial_order"] == 2
    assert report["solver"]["disable_fixture_calibrations"] is True
    assert report["solver"]["feature_strength_scale"] == 0.0
    for band_id in FLOW_BAND_IDS:
        band = report["bands"][band_id]
        assert band["checks"]["mass_positivity"]["passed"] is True
        capture = SCENARIO_ROOT / band["field_capture"]
        assert capture.exists()
        with np.load(capture) as fields:
            assert fields["h"].shape == (40, 301)
            assert float(fields["h"].min()) >= 0.0
    headline = report["headline_gate"]
    assert headline["gut_hydraulic_at_reference"] is True
    assert headline["right_diagonal_gradient_at_reference"] is True
    assert headline["sneak_passable_at_low"] is True
    assert headline["passed"] is True


def test_genuine_solver_run_reproduces_headline_behavior(tmp_path, committed_packages):
    """Short genuine-solver smoke: order-2 HLL FV, calibrations disabled."""

    cmake = shutil.which("cmake")
    compiler = shutil.which("c++") or shutil.which("clang++") or shutil.which("g++")
    if cmake is None or compiler is None:
        pytest.skip("CMake and a C++ compiler are required for the native solver behavioral test.")

    physics_dir = Path(__file__).resolve().parents[1]
    build_dir = physics_dir / "cpp" / "build"
    executable = build_dir / "raftsim_water_solver"
    if not executable.exists():
        subprocess.run([cmake, "-S", str(physics_dir / "cpp"), "-B", str(build_dir)], check=True)
        subprocess.run([cmake, "--build", str(build_dir)], check=True)

    scenario = committed_packages["median_runnable"]
    config = troublemaker_solver_config(executable, steps=900, frame_interval=300)
    from raftsim.dual_solver import run_cpp_solver_scenario

    result = run_cpp_solver_scenario(
        SCENARIO_ROOT / "median_runnable",
        output_dir=tmp_path / "run",
        config=config,
    )
    assert result.returncode == 0, result.stderr
    run_dir = result.output_dir
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["solver_mode"] == "finite_volume"
    assert manifest["flux_scheme"] == "hll"
    assert manifest["spatial_order"] == 2
    assert manifest["disable_fixture_calibrations"] is True

    fields = _load_final_frame_fields(run_dir, scenario.grid)
    fields.pop("solver_manifest")
    evaluation = evaluate_troublemaker_behavior(scenario, fields, "median_runnable")
    checks = evaluation["checks"]
    assert checks["mass_positivity"]["passed"] is True
    # 45 s of settling is enough for the ledge hydraulic and the diagonal
    # gradient to be present; the committed report holds the full-length runs.
    assert checks["gut_hydraulic_forms"]["passed"] is True
    assert checks["right_diagonal_gradient_elevated"]["passed"] is True
