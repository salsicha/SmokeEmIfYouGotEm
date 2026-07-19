"""Behavioral tests for the Hance reach-local C3 water-window package."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from raftsim.colorado_hance_c3_window import (
    FLOW_BAND_IDS,
    PUBLISHED_RIVER_MILE,
    RAPID_STATION_M,
    REFERENCE_BAND_ID,
    SCENARIO_ROOT_RELATIVE,
    HanceBedParameters,
    _load_final_frame_fields,
    build_hance_window_geometry,
    evaluate_hance_behavior,
    generate_hance_scenario2_5d,
    hance_solver_config,
    load_flow_bands,
)
from raftsim.scenario2_5d import read_scenario2_5d_package

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_ROOT = REPO_ROOT / SCENARIO_ROOT_RELATIVE

#: The Colorado catalog carries only feature_tags for Hance (no per-feature
#: inventory), so the interpreted sub-features are mapped back to the tags they
#: express.  Every tag must be covered by at least one authored sub-feature.
TAG_TO_SUBFEATURES = {
    "boulder_garden": {"hance_boulder_garden"},
    "multiple_moves": {"left_entry_move_rock", "right_entry_move_rock"},
    "holes": {"upper_left_hole", "lower_right_hole"},
    "low_flow_difficulty": {"low_water_pin_rock"},
}


@pytest.fixture(scope="module")
def committed_packages() -> dict[str, object]:
    packages = {}
    for band_id in FLOW_BAND_IDS:
        package_dir = SCENARIO_ROOT / band_id
        if not (package_dir / "scenario.json").exists():
            pytest.skip("Hance scenario packages are not committed yet.")
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
        assert scenario.metadata.provenance["published_river_mile"] == pytest.approx(PUBLISHED_RIVER_MILE)
        assert scenario.metadata.provenance["bed_geometry_authority"] == "interpreted_bed_geometry"
        assert scenario.metadata.provenance["dem_cannot_resolve_in_channel_rocks"] is True
        assert scenario.metadata.provenance["hance_outside_committed_corridor"] is True
        assert scenario.metadata.provenance["imposed_longitudinal_gradient"] is True
        assert scenario.metadata.provenance["flow_bands_are_planning_placeholders"] is True
        assert scenario.metadata.provenance["production_promoted"] is False
        assert scenario.metadata.provenance["pending_human_review"] is True


def test_committed_packages_cover_all_catalog_feature_tags(committed_packages):
    catalog = json.loads(
        (REPO_ROOT / "physics/data/real_world/named_rapid_source_catalog.json").read_text(encoding="utf-8")
    )
    hance = next(
        rapid
        for river in catalog["rivers"]
        for rapid in river.get("rapids", [])
        if rapid.get("name") == "Hance"
    )
    catalog_tags = set(hance["feature_tags"])
    # The catalog has feature_tags but no per-feature inventory for Hance.
    assert "feature_inventory" not in hance
    assert catalog_tags == set(TAG_TO_SUBFEATURES)
    for scenario in committed_packages.values():
        package_ids = {feature.metadata["subfeature_id"] for feature in scenario.features}
        assert len(scenario.features) == 10
        for tag, expected in TAG_TO_SUBFEATURES.items():
            assert expected <= package_ids, tag
        for feature in scenario.features:
            assert feature.metadata["interpreted_bed_geometry"] is True
            assert "interpreted" in feature.metadata["source"]
            assert scenario.grid.contains(feature.center)


def test_bed_geometry_expresses_headline_features(committed_packages):
    scenario = committed_packages[REFERENCE_BAND_ID]
    p = HanceBedParameters()
    bed = scenario.bed
    grid = scenario.grid
    xs = grid.x_coordinates()
    ys = grid.y_coordinates()

    def region(x_range, y_range):
        cols = (xs >= x_range[0]) & (xs <= x_range[1])
        rows = (ys >= y_range[0]) & (ys <= y_range[1])
        return bed[np.ix_(rows, cols)]

    # The boulder garden runs shallow: its bed sits close under the conditioned
    # water surface (a raised shelf), unlike the deep parabolic channel carve of
    # the smoother approach reach.  Compare depth-below-surface so the imposed
    # longitudinal drop through the window does not confound the test.
    geo = build_hance_window_geometry(REPO_ROOT)
    surf = geo.surface_profile[np.newaxis, :]
    depth_below_surface = surf - geo.bed

    def surface_gap(x_range, y_range):
        cols = (xs >= x_range[0]) & (xs <= x_range[1])
        rows = (ys >= y_range[0]) & (ys <= y_range[1])
        return depth_below_surface[np.ix_(rows, cols)]

    garden_gap = surface_gap((p.garden_x[0] + 20.0, p.garden_x[1] - 20.0), (-8.0, 8.0))
    approach_gap = surface_gap((40.0, 110.0), (-6.0, 6.0))
    assert float(np.median(garden_gap)) < float(np.median(approach_gap))

    # The main drop is a pourover: the near-surface sill crest stands well above
    # the plunge-pool floor just below it (the drop that trips the hydraulic).
    sill = region((p.main_drop_x - 1.0, p.main_drop_x + 1.0), (-4.0, 4.0))
    pool = region((p.main_drop_x + 5.0, p.main_drop_x + 14.0), (-4.0, 4.0))
    assert float(sill.max()) - float(pool.min()) > 1.5

    # Each offset hole is a pourover too (sill above pool).
    for hx, hy in (p.upper_hole_center, p.lower_hole_center):
        hsill = region((hx - 1.0, hx + 1.0), (hy - 2.0, hy + 2.0))
        hpool = region((hx + 4.0, hx + 10.0), (hy - 3.0, hy + 3.0))
        assert float(hsill.max()) - float(hpool.min()) > 1.0

    # The low-water pin rock is a local high standing above the runout channel.
    rock = region((p.low_water_rock[0] - 2.0, p.low_water_rock[0] + 2.0),
                  (p.low_water_rock[1] - 2.0, p.low_water_rock[1] + 2.0))
    channel = region((p.low_water_rock[0] - 2.0, p.low_water_rock[0] + 2.0), (-18.0, -12.0))
    assert float(rock.max()) > float(channel.min()) + 0.5

    # A scattered boulder field: the garden bed (depth-below-surface, detrended of
    # the longitudinal drop) is rougher -- higher std -- than the smooth approach carve.
    assert float(np.std(garden_gap)) > float(np.std(approach_gap))


def test_generation_is_deterministic(committed_packages):
    regenerated = generate_hance_scenario2_5d(REPO_ROOT, REFERENCE_BAND_ID)
    committed = committed_packages[REFERENCE_BAND_ID]
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
    assert (
        stages["low_release_planning"]
        < stages["moderate_release_planning"]
        < stages["high_release_planning"]
    )


def test_window_manifest_records_honesty_labels():
    manifest_path = SCENARIO_ROOT / "window_manifest.json"
    if not manifest_path.exists():
        pytest.skip("Hance window manifest is not committed yet.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    honesty = manifest["honesty"]
    assert honesty["bed_geometry_authority"] == "interpreted_bed_geometry"
    assert "cannot resolve in-channel rocks" in honesty["dem_cannot_resolve_in_channel_rocks"]
    assert "river mile 77.1" in honesty["hance_outside_committed_corridor"]
    assert "imposed" in honesty["imposed_longitudinal_gradient"].lower()
    assert "not a survey" in honesty["boulder_garden_bed"]
    assert "feature_tags" in honesty["feature_inventory"]
    assert "placeholder" in honesty["flow_bands_are_planning_placeholders"].lower()
    assert honesty["production_promoted"] is False
    assert honesty["pending_human_review"] is True
    assert manifest["conditioning"]["monotone_downstream"] is True
    assert manifest["conditioning"]["interpreted_longitudinal_profile"] is True
    # The conditioned profile carries the imposed Hance-class drop the flat raw
    # tailwater DEM does not.
    assert manifest["conditioning"]["conditioned_profile_drop_m"] > 4.0
    assert manifest["sources"]["dem_sha256"] == (
        "01a6a73ac541db5143b587f861aff64f49479fde68f063b2bafb3b6b0a962e2d"
    )
    assert manifest["geometry"]["catalog_point_to_channel_snap_distance_m"] < 100.0


def test_behavioral_validation_report_passes_headline_gate():
    report_path = SCENARIO_ROOT / "behavioral_validation.json"
    if not report_path.exists():
        pytest.skip("Hance behavioral validation report is not committed yet.")
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
    assert headline["boulder_garden_roughness_at_reference"] is True
    assert headline["runout_wave_train_at_high"] is True
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

    scenario = committed_packages[REFERENCE_BAND_ID]
    config = hance_solver_config(executable, steps=2000, frame_interval=500)
    from raftsim.dual_solver import run_cpp_solver_scenario

    result = run_cpp_solver_scenario(
        SCENARIO_ROOT / REFERENCE_BAND_ID,
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
    evaluation = evaluate_hance_behavior(scenario, fields, REFERENCE_BAND_ID)
    checks = evaluation["checks"]
    assert checks["mass_positivity"]["passed"] is True
    # 100 s of settling is enough for the main-drop pourover hydraulic and the
    # boulder-garden roughness signature to be present; the committed report holds
    # the full-length runs at all three bands.
    assert checks["main_drop_hydraulic_forms"]["passed"] is True
    assert checks["boulder_garden_roughness_elevated"]["passed"] is True
