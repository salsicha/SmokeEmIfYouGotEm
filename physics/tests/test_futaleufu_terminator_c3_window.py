"""Behavioral tests for the Futaleufú Terminator reach-local C3 water-window package."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from raftsim.futaleufu_terminator_c3_window import (
    FLOW_BAND_IDS,
    HEIGHTFIELD_SHA256,
    RAPID_STATION_M,
    SCENARIO_ROOT_RELATIVE,
    TerminatorBedParameters,
    _load_final_frame_fields,
    build_terminator_window_geometry,
    evaluate_terminator_behavior,
    generate_terminator_scenario2_5d,
    load_flow_bands,
    terminator_solver_config,
)
from raftsim.scenario2_5d import read_scenario2_5d_package

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_ROOT = REPO_ROOT / SCENARIO_ROOT_RELATIVE


@pytest.fixture(scope="module")
def committed_packages() -> dict[str, object]:
    packages = {}
    for band_id in FLOW_BAND_IDS:
        package_dir = SCENARIO_ROOT / band_id
        if not (package_dir / "scenario.json").exists():
            pytest.skip("Terminator scenario packages are not committed yet.")
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
        assert scenario.metadata.provenance["route_order_station_m"] == pytest.approx(RAPID_STATION_M)
        assert scenario.metadata.provenance["bed_geometry_authority"] == "interpreted_bed_geometry"
        assert scenario.metadata.provenance["dem_cannot_resolve_in_channel_rocks"] is True
        assert scenario.metadata.provenance["production_promoted"] is False
        assert scenario.metadata.provenance["pending_human_review"] is True


def test_committed_packages_carry_interpreted_terminator_features(committed_packages):
    # Terminator carries published feature_tags but no committed C1 sub-feature
    # inventory, so every in-channel feature is honestly-labeled interpreted
    # geometry (not matched against a catalog inventory).
    catalog = json.loads(
        (REPO_ROOT / "physics/data/real_world/named_rapid_source_catalog.json").read_text(encoding="utf-8")
    )
    terminator = next(
        rapid
        for river in catalog["rivers"]
        for rapid in river.get("rapids", [])
        if rapid.get("name") == "Terminator"
    )
    assert "feature_inventory" not in terminator  # feature_tags only
    for scenario in committed_packages.values():
        assert len(scenario.features) == 11
        subfeature_ids = {feature.metadata["subfeature_id"] for feature in scenario.features}
        assert {"terminator_hole", "flip_wave_train", "river_left_sneak_line"} <= subfeature_ids
        for feature in scenario.features:
            assert feature.metadata["interpreted_bed_geometry"] is True
            assert "feature_tags_interpreted" in feature.metadata["source"]
            assert scenario.grid.contains(feature.center)


def test_bed_geometry_expresses_headline_features(committed_packages):
    scenario = committed_packages["median_runnable"]
    p = TerminatorBedParameters()
    bed = scenario.bed
    grid = scenario.grid
    xs = grid.x_coordinates()
    ys = grid.y_coordinates()

    def region(x_range, y_range):
        cols = (xs >= x_range[0]) & (xs <= x_range[1])
        rows = (ys >= y_range[0]) & (ys <= y_range[1])
        return bed[np.ix_(rows, cols)]

    # Each hole is a pourover: the near-surface sill crest stands well above the
    # plunge-pool floor just below it (the drop that trips the hydraulic).
    for center, hw in ((p.hole_center, p.hole_half_width_m), (p.hole2_center, p.hole2_half_width_m)):
        hx, hy = center
        sill = region((hx - 1.0, hx + 1.0), (hy - 2.0, hy + 2.0))
        pool = region((hx + 4.0, hx + 10.0), (hy - 3.0, hy + 3.0))
        assert float(sill.max()) - float(pool.min()) > 1.0

    # The river-left sneak slot is carved below its separating berm.
    slot = region((p.sneak_x[0] + 12.0, p.sneak_x[1] - 12.0), p.sneak_y)
    berm = region((p.sneak_x[0] + 12.0, p.sneak_x[1] - 12.0), p.sneak_berm_y)
    assert float(np.median(berm)) - float(np.median(slot)) > 0.5

    # The entry marker boulder is a local high above the tongue chute to its left.
    rock = region((p.marker_rock_x - 2.0, p.marker_rock_x + 2.0), (p.marker_rock_y - 2.0, p.marker_rock_y + 2.0))
    tongue = region(p.tongue_x, (-4.0, 4.0))
    assert float(rock.max()) > float(tongue.min()) + 1.0


def test_generation_is_deterministic(committed_packages):
    regenerated = generate_terminator_scenario2_5d(REPO_ROOT, "median_runnable")
    committed = committed_packages["median_runnable"]
    np.testing.assert_array_equal(regenerated.bed, committed.bed)
    np.testing.assert_array_equal(regenerated.initial_state.depth, committed.initial_state.depth)
    np.testing.assert_array_equal(regenerated.initial_state.u, committed.initial_state.u)
    assert regenerated.metadata.provenance["stage_west_m"] == committed.metadata.provenance["stage_west_m"]


def test_flow_bands_are_derived_from_corridor_planning_bands(committed_packages):
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
    # The three bands map to the corridor's DGA planning bands.
    assert bands["low_runnable"]["source_planning_band"] == "low_technical"
    assert bands["median_runnable"]["source_planning_band"] == "normal_runnable"
    assert bands["high_runnable"]["source_planning_band"] == "high_big_water"


def test_window_manifest_records_honesty_labels():
    manifest_path = SCENARIO_ROOT / "window_manifest.json"
    if not manifest_path.exists():
        pytest.skip("Terminator window manifest is not committed yet.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    honesty = manifest["honesty"]
    assert honesty["bed_geometry_authority"] == "interpreted_bed_geometry"
    assert "cannot resolve" in honesty["dem_cannot_resolve_in_channel_rocks"]
    assert "GLO-30" in honesty["dem_cannot_resolve_in_channel_rocks"]
    assert honesty["production_promoted"] is False
    assert honesty["pending_human_review"] is True
    assert manifest["conditioning"]["monotone_downstream"] is True
    assert manifest["sources"]["heightfield_sha256"] == HEIGHTFIELD_SHA256
    assert manifest["geometry"]["axis_to_heightfield_thalweg_offset_m"] < 100.0


def test_geometry_conditioning_agrees_with_committed_corridor_profile():
    geo = build_terminator_window_geometry(REPO_ROOT)
    report = geo.conditioning_report
    # The C3 conditioned profile agrees with the corridor's own committed
    # conditioned-surface drop to within a fraction of a metre, and the slope bound
    # is retained but inactive on this ~1.3% reach.
    assert abs(report["conditioned_profile_drop_m"] - report["committed_corridor_surface_drop_m"]) < 1.0
    assert report["mean_slope_bound_applied"] is False
    assert report["monotone_downstream"] is True


def test_behavioral_validation_report_passes_headline_gate():
    report_path = SCENARIO_ROOT / "behavioral_validation.json"
    if not report_path.exists():
        pytest.skip("Terminator behavioral validation report is not committed yet.")
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
            assert fields["h"].shape == (43, 301)
            assert float(fields["h"].min()) >= 0.0
    headline = report["headline_gate"]
    assert headline["terminator_hole_at_reference"] is True
    assert headline["flip_wave_train_at_high"] is True
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
    config = terminator_solver_config(executable, steps=2000, frame_interval=500)
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
    evaluation = evaluate_terminator_behavior(scenario, fields, "median_runnable")
    checks = evaluation["checks"]
    assert checks["mass_positivity"]["passed"] is True
    # 100 s of settling is enough for the Terminator-hole pourover hydraulic (the
    # supercritical sill face plus the plunge-pool surface recovery) and the
    # flip-wave-train surface-gradient signature to be present; the committed report
    # holds the bounded-settle runs at all three bands.
    assert checks["terminator_hole_forms"]["passed"] is True
    assert checks["flip_wave_train_forms"]["passed"] is True
