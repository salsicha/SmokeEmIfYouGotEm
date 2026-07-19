"""Behavioral tests for the Upper Huacas (Pacuare) reach-local C3 water-window package."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from raftsim.pacuare_upper_huacas_c3_window import (
    FLOW_BAND_IDS,
    INTERPRETED_BAND_DISCHARGE_M3S,
    RAPID_STATION_M,
    SCENARIO_ROOT_RELATIVE,
    UpperHuacasBedParameters,
    _load_final_frame_fields,
    build_upper_huacas_window_geometry,
    evaluate_upper_huacas_behavior,
    generate_upper_huacas_scenario2_5d,
    upper_huacas_solver_config,
)
from raftsim.scenario2_5d import read_scenario2_5d_package

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_ROOT = REPO_ROOT / SCENARIO_ROOT_RELATIVE
DEM_SHA256 = "068e212e279fe5361076ec3c0100a763472712ca7c2aa7bfb2083b8d5637ed41"


@pytest.fixture(scope="module")
def committed_packages() -> dict[str, object]:
    packages = {}
    for band_id in FLOW_BAND_IDS:
        package_dir = SCENARIO_ROOT / band_id
        if not (package_dir / "scenario.json").exists():
            pytest.skip("Upper Huacas scenario packages are not committed yet.")
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
        assert grid.nx == 301
        assert grid.ny == 40
        assert scenario.metadata.flow_band == band_id
        prov = scenario.metadata.provenance
        assert prov["anchor_preview_station_m"] == pytest.approx(RAPID_STATION_M)
        assert prov["stationing_authority"] == "published_map_order_only"
        assert prov["bed_geometry_authority"] == "interpreted_bed_geometry"
        assert prov["dem_cannot_resolve_in_channel_rocks"] is True
        assert prov["dem_ground_resolution_m"] == pytest.approx(30.0)
        assert prov["discharge_authority"] == "interpreted_planning_value_not_gauge_calibrated"
        assert prov["production_promoted"] is False
        assert prov["pending_human_review"] is True


def test_committed_packages_carry_interpreted_features_from_catalog_tags(committed_packages):
    """The corridor is order-only (no C1 subfeature inventory); features are
    interpreted from the committed Upper Huacas feature_tags."""

    catalog = json.loads(
        (REPO_ROOT / "physics/data/real_world/named_rapid_source_catalog.json").read_text(encoding="utf-8")
    )
    upper_huacas = next(
        rapid
        for river in catalog["rivers"]
        for rapid in river.get("rapids", [])
        if rapid.get("name") == "Upper Huacas"
    )
    catalog_tags = set(upper_huacas["feature_tags"])
    assert catalog_tags  # the catalog entry carries feature_tags, not a subfeature inventory
    for scenario in committed_packages.values():
        assert len(scenario.features) == 9
        for feature in scenario.features:
            assert feature.metadata["interpreted_bed_geometry"] is True
            assert feature.metadata["source"] == "named_rapid_source_catalog.v1:Upper Huacas:feature_tags"
            # every authored feature tag is drawn from the committed catalog tag set
            assert feature.metadata["feature_tag"] in catalog_tags
            assert scenario.grid.contains(feature.center)


def test_bed_geometry_expresses_headline_features(committed_packages):
    scenario = committed_packages["rainfed_runnable_planning"]
    p = UpperHuacasBedParameters()
    bed = scenario.bed
    grid = scenario.grid
    xs = grid.x_coordinates()
    ys = grid.y_coordinates()

    def region(x_range, y_range):
        cols = (xs >= x_range[0]) & (xs <= x_range[1])
        rows = (ys >= y_range[0]) & (ys <= y_range[1])
        return bed[np.ix_(rows, cols)]

    # The main river-wide drop is a pourover: the near-surface sill crest stands
    # well above the plunge-pool floor just below it (the drop that trips the hydraulic).
    sill = region((p.drop_x - 1.0, p.drop_x + 1.0), (-2.0, 2.0))
    pool = region((p.drop_x + 4.0, p.drop_x + 10.0), (-3.0, 3.0))
    assert float(sill.max()) - float(pool.min()) > 1.0

    # The secondary pourover is likewise a sill standing above its plunge pool.
    hx, hy = p.second_hole_center
    sill2 = region((hx - 1.0, hx + 1.0), (hy - 2.0, hy + 2.0))
    pool2 = region((hx + 4.0, hx + 10.0), (hy - 3.0, hy + 3.0))
    assert float(sill2.max()) - float(pool2.min()) > 0.8

    # The gorge walls stand well above the conditioned channel: compare depth
    # below the conditioned surface so the longitudinal drop does not confound it.
    geo = build_upper_huacas_window_geometry(REPO_ROOT)
    surf = geo.surface_profile[np.newaxis, :]
    gap = surf - geo.bed  # positive = below surface (channel), negative = above (walls)

    def surface_gap(x_range, y_range):
        cols = (xs >= x_range[0]) & (xs <= x_range[1])
        rows = (ys >= y_range[0]) & (ys <= y_range[1])
        return gap[np.ix_(rows, cols)]

    wall_gap = surface_gap((200.0, 400.0), (25.0, 39.0))
    channel_gap = surface_gap((200.0, 400.0), (-6.0, 6.0))
    assert float(np.median(wall_gap)) < float(np.median(channel_gap))  # walls stand above the channel


def test_generation_is_deterministic(committed_packages):
    regenerated = generate_upper_huacas_scenario2_5d(REPO_ROOT, "rainfed_runnable_planning")
    committed = committed_packages["rainfed_runnable_planning"]
    np.testing.assert_array_equal(regenerated.bed, committed.bed)
    np.testing.assert_array_equal(regenerated.initial_state.depth, committed.initial_state.depth)
    np.testing.assert_array_equal(regenerated.initial_state.u, committed.initial_state.u)
    assert regenerated.metadata.provenance["stage_west_m"] == committed.metadata.provenance["stage_west_m"]


def test_flow_band_boundaries_scale_with_interpreted_discharge(committed_packages):
    stages = {}
    for band_id, scenario in committed_packages.items():
        west = next(b for b in scenario.boundaries if b.edge == "west")
        east = next(b for b in scenario.boundaries if b.edge == "east")
        assert west.kind == "inflow"
        assert east.kind == "outflow"
        assert west.metadata["target_discharge_m3s"] == pytest.approx(INTERPRETED_BAND_DISCHARGE_M3S[band_id])
        stages[band_id] = west.stage
    assert (
        stages["clear_season_low_planning"]
        < stages["rainfed_runnable_planning"]
        < stages["rainy_season_high_planning"]
    )


def test_window_manifest_records_honesty_labels():
    manifest_path = SCENARIO_ROOT / "window_manifest.json"
    if not manifest_path.exists():
        pytest.skip("Upper Huacas window manifest is not committed yet.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    honesty = manifest["honesty"]
    assert honesty["bed_geometry_authority"] == "interpreted_bed_geometry"
    assert "GLO-30" in honesty["dem_cannot_resolve_in_channel_rocks"]
    assert "order-only" in honesty["stationing_authority"]
    assert "interpreted planning values" in honesty["flow_bands"]
    assert "slope-bounded" in honesty["slope_bound"]
    assert honesty["production_promoted"] is False
    assert honesty["pending_human_review"] is True
    assert manifest["conditioning"]["monotone_downstream"] is True
    assert manifest["conditioning"]["mean_slope_bound_applied"] is True
    assert manifest["sources"]["dem_sha256"] == DEM_SHA256
    assert manifest["geometry"]["catalog_point_to_channel_snap_distance_m"] < 150.0


def test_behavioral_validation_report_passes_headline_gate():
    report_path = SCENARIO_ROOT / "behavioral_validation.json"
    if not report_path.exists():
        pytest.skip("Upper Huacas behavioral validation report is not committed yet.")
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
    assert headline["main_drop_hydraulic_at_reference"] is True
    assert headline["secondary_pourover_at_reference"] is True
    assert headline["gorge_constriction_gradient_at_reference"] is True
    assert headline["passed"] is True
    # The flow_sensitive exit wave train is recorded per band as an informational
    # signal (not a headline gate); its flow-dependence gap is documented honestly.
    for band_id in FLOW_BAND_IDS:
        exit_check = report["bands"][band_id]["checks"]["exit_wave_train_forms"]
        assert exit_check["headline_gate"] is False
    assert "exit_wave_train_flow_dependence_gap" in report["honesty"]


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

    scenario = committed_packages["rainfed_runnable_planning"]
    config = upper_huacas_solver_config(executable, steps=2000, frame_interval=500)
    from raftsim.dual_solver import run_cpp_solver_scenario

    result = run_cpp_solver_scenario(
        SCENARIO_ROOT / "rainfed_runnable_planning",
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
    evaluation = evaluate_upper_huacas_behavior(scenario, fields, "rainfed_runnable_planning")
    checks = evaluation["checks"]
    assert checks["mass_positivity"]["passed"] is True
    # 100 s of settling is enough for the main river-wide drop pourover hydraulic,
    # the offset secondary pourover, and the gorge-constriction gradient signature
    # to be present; the committed report holds the 4000-step (200 s) runs.
    assert checks["main_drop_hydraulic_forms"]["passed"] is True
    assert checks["secondary_pourover_forms"]["passed"] is True
    assert checks["gorge_constriction_gradient_elevated"]["passed"] is True
