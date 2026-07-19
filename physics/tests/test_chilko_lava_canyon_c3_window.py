"""Behavioral tests for the Lava Canyon (Chilko) reach-local C3 water-window package."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from raftsim.chilko_lava_canyon_c3_window import (
    FLOW_BAND_IDS,
    RAPID_STATION_M,
    SCENARIO_ROOT_RELATIVE,
    LavaCanyonBedParameters,
    _load_final_frame_fields,
    adopt_lava_canyon_station,
    build_lava_canyon_window_geometry,
    evaluate_lava_canyon_behavior,
    generate_lava_canyon_scenario2_5d,
    lava_canyon_solver_config,
    load_flow_bands,
    rib_stations,
)
from raftsim.scenario2_5d import read_scenario2_5d_package

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_ROOT = REPO_ROOT / SCENARIO_ROOT_RELATIVE

#: sha256 of the committed MRDEM-30 corridor DTM (terrain source clip manifest).
DTM_SHA256 = "589f3a58ec158e7b3f09f9b3823328b45e4bbade601a754147983055eed6faeb"


@pytest.fixture(scope="module")
def committed_packages() -> dict[str, object]:
    packages = {}
    for band_id in FLOW_BAND_IDS:
        package_dir = SCENARIO_ROOT / band_id
        if not (package_dir / "scenario.json").exists():
            pytest.skip("Lava Canyon scenario packages are not committed yet.")
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
        assert scenario.metadata.provenance["dem_ground_sample_m"] == pytest.approx(30.0)
        assert scenario.metadata.provenance["production_promoted"] is False
        assert scenario.metadata.provenance["pending_human_review"] is True


def test_adopted_station_is_deterministic_upper_canyon_anchor():
    station, slope = adopt_lava_canyon_station(REPO_ROOT)
    # The committed adopted station is the deterministic upper-canyon max-sustained
    # descent anchor, re-derivable from the route DEM profile.
    assert station == pytest.approx(RAPID_STATION_M)
    assert slope > 0.0  # a genuine descent


def test_committed_packages_carry_interpreted_feature_set(committed_packages):
    # The Chilko catalog records published feature *tags* only for Lava Canyon (no
    # C1 sub-feature inventory), so the package feature set is an honest author
    # interpretation of those tags -- assert it is present, interpreted, and placed
    # in-grid, not equal to a surveyed inventory.
    expected_ids = {
        "entry_tongue",
        "continuous_wave_train",
        "basalt_canyon_constriction_upper",
        "basalt_canyon_constriction_lower",
        "midstream_broach_rock",
        "boulder_controls",
        "canyon_wall_lateral",
        "exit_runout_wave_train",
        "limited_recovery_eddy",
        "wood_hazard_shore",
    }
    for scenario in committed_packages.values():
        package_ids = {feature.metadata["subfeature_id"] for feature in scenario.features}
        assert package_ids == expected_ids
        assert len(scenario.features) == 10
        for feature in scenario.features:
            assert feature.metadata["interpreted_bed_geometry"] is True
            assert feature.metadata["source"].endswith("Lava Canyon:feature_tags_interpreted")
            assert scenario.grid.contains(feature.center)


def test_bed_geometry_expresses_continuous_wave_train(committed_packages):
    p = LavaCanyonBedParameters()
    geo = build_lava_canyon_window_geometry(REPO_ROOT)
    grid = geo.grid
    xs = grid.x_coordinates()
    ys = grid.y_coordinates()
    surf = geo.surface_profile[np.newaxis, :]
    depth_below_surface = surf - geo.bed

    def gap(x_range, y_range):
        cols = (xs >= x_range[0]) & (xs <= x_range[1])
        rows = (ys >= y_range[0]) & (ys <= y_range[1])
        return depth_below_surface[np.ix_(rows, cols)]

    def bed_region(x_range, y_range):
        cols = (xs >= x_range[0]) & (xs <= x_range[1])
        rows = (ys >= y_range[0]) & (ys <= y_range[1])
        return geo.bed[np.ix_(rows, cols)]

    # The wave train is a periodic sill train: each rib crest sits shallower (nearer
    # the surface) than the deeper troughs between ribs.  Compare rib-crest gap to
    # the trough gap halfway between adjacent ribs.  The scattered boulder field
    # perturbs individual trough samples, so assert on the aggregate (the rib crests
    # are shallower on the whole) plus a clear majority of individual ribs.
    ribs = [rx for rx in rib_stations(p) if p.train_x[0] + 20 <= rx <= p.train_x[1] - 20]
    assert len(ribs) >= 8  # a continuous train of sills
    rib_gaps = [float(np.median(gap((rx - 1.0, rx + 1.0), (-6.0, 6.0)))) for rx in ribs]
    trough_gaps = [
        float(np.median(gap((rx + p.rib_wavelength_m / 2 - 1.0, rx + p.rib_wavelength_m / 2 + 1.0), (-6.0, 6.0))))
        for rx in ribs
    ]
    assert float(np.median(rib_gaps)) < float(np.median(trough_gaps))
    shallower = sum(1 for rib_gap, trough_gap in zip(rib_gaps, trough_gaps) if rib_gap < trough_gap)
    assert shallower >= 0.6 * len(ribs)  # a clear majority of ribs are shallow sills

    # The basalt-canyon constriction walls stand above the water surface, pinching
    # the channel.
    for cx in p.constriction_x:
        wall = bed_region((cx - 4.0, cx + 4.0), (p.constriction_inner_half_width_m + 4.0, 30.0))
        core = bed_region((cx - 4.0, cx + 4.0), (-4.0, 4.0))
        assert float(np.median(wall)) > float(np.median(core)) + 1.0

    # The limited-recovery eddy is carved below the surface on river-left.
    eddy = gap(p.recovery_eddy_x, p.recovery_eddy_y)
    assert float(np.median(eddy)) > 0.5


def test_generation_is_deterministic(committed_packages):
    regenerated = generate_lava_canyon_scenario2_5d(REPO_ROOT, "median_runnable")
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
        pytest.skip("Lava Canyon window manifest is not committed yet.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    honesty = manifest["honesty"]
    assert honesty["bed_geometry_authority"] == "interpreted_bed_geometry"
    assert "cannot resolve in-channel rocks" in honesty["dem_cannot_resolve_in_channel_rocks"]
    assert "feature tags" in honesty["no_committed_feature_inventory"] or "feature *tags*" in honesty["no_committed_feature_inventory"]
    assert "pending_human_review" in honesty["station_adoption"]
    assert honesty["production_promoted"] is False
    assert honesty["pending_human_review"] is True
    assert manifest["conditioning"]["monotone_downstream"] is True
    assert manifest["conditioning"]["terrain_source"] == "nrcan_mrdem30_dtm_30m_ground_sample_epsg4326_clip"
    assert manifest["sources"]["dem_sha256"] == DTM_SHA256
    assert manifest["geometry"]["catalog_point_to_channel_snap_distance_m"] < 40.0


def test_behavioral_validation_report_passes_headline_gate():
    report_path = SCENARIO_ROOT / "behavioral_validation.json"
    if not report_path.exists():
        pytest.skip("Lava Canyon behavioral validation report is not committed yet.")
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
            assert fields["h"].shape == (41, 301)
            assert float(fields["h"].min()) >= 0.0
    headline = report["headline_gate"]
    assert headline["continuous_wave_train_at_reference"] is True
    assert headline["constrictions_accelerate_at_reference"] is True
    assert headline["continuous_wave_train_at_high"] is True
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
    config = lava_canyon_solver_config(executable, steps=2000, frame_interval=500)
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
    evaluation = evaluate_lava_canyon_behavior(scenario, fields, "median_runnable")
    checks = evaluation["checks"]
    assert checks["mass_positivity"]["passed"] is True
    # 100 s of settling is enough for the continuous standing-wave train to be
    # present; the committed report holds the full-length runs at all three bands.
    assert checks["continuous_wave_train_forms"]["passed"] is True
