"""Behavioral validation of the committed South Fork cooked flow fields package."""

import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from raftsim.cooked_flow_fields import (
    COOKED_ARRAY_CONTRACT,
    COOKED_FLOW_FIELDS_SCHEMA,
    SOUTH_FORK_COOKED_BAND_IDS,
    ConvergenceThresholds,
    ConvergenceWindow,
    load_cooked_flow_field_band,
    read_cooked_flow_fields_manifest,
    sha256_of_file,
    validate_cooked_flow_fields_package,
)
from raftsim.real_world import default_player_selections, generate_real_world_scenario2_5d

PACKAGE_DIR = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "real_world"
    / "south_fork_american_chili_bar"
    / "cooked_flow_fields"
)
SCENARIO_DIR = PACKAGE_DIR.parent / "scenario"


@pytest.fixture(scope="module")
def manifest() -> dict:
    return read_cooked_flow_fields_manifest(PACKAGE_DIR)


def test_manifest_declares_v1_schema_and_all_three_bands(manifest):
    assert manifest["schema"] == COOKED_FLOW_FIELDS_SCHEMA
    band_ids = [band["band_id"] for band in manifest["bands"]]
    assert band_ids == list(SOUTH_FORK_COOKED_BAND_IDS)
    assert manifest["river_id"] == "american_south_fork"
    assert manifest["section_id"] == "chili_bar_to_coloma"


def test_manifest_grid_matches_committed_scenario_package(manifest):
    scenario = json.loads((SCENARIO_DIR / "scenario.json").read_text(encoding="utf-8"))
    grid = manifest["grid"]
    assert grid["nx"] == scenario["grid"]["nx"]
    assert grid["ny"] == scenario["grid"]["ny"]
    assert grid["dx_m"] == scenario["grid"]["dx"]
    assert grid["dy_m"] == scenario["grid"]["dy"]
    assert grid["origin_x_m"] == scenario["grid"]["origin_x"]
    assert grid["origin_y_m"] == scenario["grid"]["origin_y"]
    assert grid["crs"] == scenario["metadata"]["coordinate_reference_system"]
    assert grid["layout"] == "row_major_c_order"
    assert grid["downstream_axis"] == "+x"


def test_manifest_records_genuine_solver_configuration(manifest):
    solver = manifest["solver"]
    assert solver["solver"] == "raftsim_water_cpp_v1"
    assert solver["solver_mode"] == "finite_volume"
    assert solver["flux_scheme"] == "hll"
    assert solver["spatial_order"] == 2
    assert solver["disable_fixture_calibrations"] is True
    assert solver["feature_strength_scale"] == 0.0
    assert solver["simulated_seconds"] == pytest.approx(solver["steps"] * solver["fixed_dt_s"])
    assert len(solver["binary_sha256"]) == 64


def test_package_validates_clean_and_detects_tampering(tmp_path):
    assert validate_cooked_flow_fields_package(PACKAGE_DIR) == []

    tampered = tmp_path / "tampered"
    shutil.copytree(PACKAGE_DIR, tampered)
    victim = tampered / "median_runnable" / "h.npy"
    array = np.load(victim)
    array[0, 0] += 1.0
    np.save(victim, array)
    problems = validate_cooked_flow_fields_package(tampered)
    assert any("median_runnable/h" in problem and "sha256" in problem for problem in problems)


def test_array_files_match_manifest_hashes_shapes_and_dtypes(manifest):
    grid = manifest["grid"]
    for band in manifest["bands"]:
        assert set(band["arrays"]) == set(COOKED_ARRAY_CONTRACT)
        for name, spec in band["arrays"].items():
            path = PACKAGE_DIR / spec["file"]
            assert path.exists(), spec["file"]
            assert sha256_of_file(path) == spec["sha256"]
            array = np.load(path)
            assert list(array.shape) == spec["shape"] == [grid["ny"], grid["nx"]]
            assert str(array.dtype) == spec["dtype"] == COOKED_ARRAY_CONTRACT[name]["dtype"]


@pytest.mark.parametrize("band_id", SOUTH_FORK_COOKED_BAND_IDS)
def test_band_fields_are_physically_sane(manifest, band_id):
    arrays = load_cooked_flow_field_band(PACKAGE_DIR, band_id)
    band = next(entry for entry in manifest["bands"] if entry["band_id"] == band_id)
    grid = manifest["grid"]

    h = arrays["h"].astype(np.float64)
    u = arrays["u"].astype(np.float64)
    v = arrays["v"].astype(np.float64)
    bed = arrays["bed"].astype(np.float64)
    wet = arrays["wet_mask"].astype(bool)

    for name in ("h", "u", "v", "bed"):
        assert np.isfinite(arrays[name]).all(), name

    # Mass positivity: depth never negative, and the band holds real water volume.
    assert h.min() >= 0.0
    volume_m3 = h.sum() * grid["dx_m"] * grid["dy_m"]
    assert volume_m3 > 1000.0

    # Wet fraction sanity: a runnable river window is mostly wet, and the mask
    # agrees with the manifest's recorded stats and the depth field.
    wet_fraction = wet.mean()
    assert 0.5 <= wet_fraction <= 1.0
    assert wet_fraction == pytest.approx(band["field_stats"]["wet_fraction"])
    assert h[wet].min() > 0.0
    dry = ~wet
    if dry.any():
        assert np.abs(u[dry]).max() == 0.0
        assert np.abs(v[dry]).max() == 0.0

    # Velocity bounds: plausible white-water speeds, matching recorded stats.
    speed = np.hypot(u, v)
    assert speed.max() < 12.0
    assert speed.max() == pytest.approx(band["field_stats"]["speed_max_m_per_s"], rel=1e-5)

    # Bed grid matches the deterministic scenario generator for this band to
    # float32 rounding (each band has its own bed datum via its depth preset;
    # the committed scenario package is the median variant).
    selection = next(s for s in default_player_selections() if s.flow_band == band_id)
    scenario_bed = generate_real_world_scenario2_5d(selection).bed
    np.testing.assert_array_equal(bed, scenario_bed.astype(np.float32))
    if band_id == "median_runnable":
        committed_bed = np.load(SCENARIO_DIR / "bed.npy")
        np.testing.assert_array_equal(bed, committed_bed.astype(np.float32))

    # The cooked state flows downstream on the whole: positive discharge at the
    # west, mid, and east cross-sections, consistent with the manifest record.
    for section, value in band["discharge_steady_m3s"].items():
        assert value > 0.0, section
    mid = h.shape[1] // 2
    assert (h[:, mid] * u[:, mid]).sum() * grid["dy_m"] == pytest.approx(
        band["discharge_steady_m3s"]["mid"], rel=1e-5
    )


def test_bands_are_ordered_by_discharge(manifest):
    steady = [band["discharge_steady_m3s"]["mid"] for band in manifest["bands"]]
    targets = [band["discharge_target_m3s"] for band in manifest["bands"]]
    assert steady == sorted(steady)
    assert targets == sorted(targets)


@pytest.mark.parametrize("band_id", SOUTH_FORK_COOKED_BAND_IDS)
def test_convergence_evidence_is_recorded_and_self_consistent(manifest, band_id):
    band = next(entry for entry in manifest["bands"] if entry["band_id"] == band_id)
    convergence = band["convergence"]
    thresholds = ConvergenceThresholds(**convergence["thresholds"])
    windows = [ConvergenceWindow(**window) for window in convergence["windows"]]

    assert len(windows) >= thresholds.consecutive_windows_required
    assert convergence["final_window"] == convergence["windows"][-1]

    # The converged flag must be honest: recompute it from the recorded windows.
    recomputed = all(
        thresholds.window_passes(window)
        for window in windows[-thresholds.consecutive_windows_required :]
    )
    assert convergence["converged"] == recomputed

    # The committed package is expected to have converged; if regeneration ever
    # produces a non-converged band this test fails loudly rather than shipping it.
    assert convergence["converged"] is True


def test_loader_rejects_unknown_schema(tmp_path):
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "manifest.json").write_text(
        json.dumps({"schema": "raftsim.cooked_flow_fields.v999"}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="Unsupported cooked flow fields schema"):
        read_cooked_flow_fields_manifest(package)
