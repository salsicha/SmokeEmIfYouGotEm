"""Behavioral validation of the committed Troublemaker C3 cooked flow fields package.

This is the authored-scenario-window counterpart to
``test_cooked_flow_fields.py``. It checks the same v1 schema the UE loader reads,
plus the additions the Troublemaker window requires: the manifest records the
Manning n each band was solved with, and convergence is recorded honestly (the
strong authored hydraulics keep feature-scale cells unsteady, so the converged
flag is only asserted to be self-consistent with the recorded windows, never
forced true).
"""

import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from raftsim.cooked_flow_fields import (
    COOKED_ARRAY_CONTRACT,
    COOKED_FLOW_FIELDS_SCHEMA,
    ConvergenceThresholds,
    ConvergenceWindow,
    load_cooked_flow_field_band,
    read_cooked_flow_fields_manifest,
    sha256_of_file,
    validate_cooked_flow_fields_package,
)
from raftsim.scenario2_5d import read_scenario2_5d_package
from raftsim.troublemaker_c3_window import FLOW_BAND_IDS

SCENARIO_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "real_world"
    / "south_fork_american_chili_bar"
    / "scenario_troublemaker"
)
PACKAGE_DIR = SCENARIO_ROOT / "cooked_flow_fields"


@pytest.fixture(scope="module")
def manifest() -> dict:
    return read_cooked_flow_fields_manifest(PACKAGE_DIR)


def test_manifest_declares_v1_schema_and_all_three_bands(manifest):
    assert manifest["schema"] == COOKED_FLOW_FIELDS_SCHEMA
    band_ids = [band["band_id"] for band in manifest["bands"]]
    assert band_ids == list(FLOW_BAND_IDS)
    assert manifest["river_id"] == "south_fork_american_chili_bar"
    assert manifest["section_id"] == "troublemaker_station_8368m_c3_window"
    assert manifest["window_id"] == "troublemaker_station_8368m_c3_window"
    assert manifest["rapid_name"] == "Troublemaker"
    # Provenance is carried through honestly: interpreted bed, pending review.
    provenance = manifest["window_provenance"]
    assert provenance["bed_geometry_authority"] == "interpreted_bed_geometry"
    assert provenance["pending_human_review"] is True
    assert provenance["production_promoted"] is False


def test_manifest_grid_matches_committed_scenario_packages(manifest):
    scenario = json.loads((SCENARIO_ROOT / "median_runnable" / "scenario.json").read_text(encoding="utf-8"))
    grid = manifest["grid"]
    assert grid["nx"] == scenario["grid"]["nx"] == 301
    assert grid["ny"] == scenario["grid"]["ny"] == 40
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
    # The window was authored/validated with full roughness and bed-slope source.
    assert solver["roughness_scale"] == 1.0
    assert solver["bed_slope_source_scale"] == 1.0
    assert solver["simulated_seconds"] == pytest.approx(solver["steps"] * solver["fixed_dt_s"])
    assert len(solver["binary_sha256"]) == 64


def test_manifest_records_roughness_per_band(manifest):
    """The window's Manning n is recorded per band (the Chili Bar manifest omitted it)."""

    window_manifest = json.loads((SCENARIO_ROOT / "window_manifest.json").read_text(encoding="utf-8"))
    authored_manning_n = window_manifest["window_parameters"]["roughness_manning_n"]
    roughness_scale = manifest["solver"]["roughness_scale"]
    for band in manifest["bands"]:
        assert "manning_n" in band, band["band_id"]
        assert "effective_manning_n" in band, band["band_id"]
        # Base Manning n matches the committed scenario package roughness...
        scenario = read_scenario2_5d_package(SCENARIO_ROOT / band["band_id"])
        assert band["manning_n"] == pytest.approx(scenario.roughness)
        assert band["manning_n"] == pytest.approx(authored_manning_n)
        # ...and the effective value is what the solver applied (n * scale).
        assert band["effective_manning_n"] == pytest.approx(band["manning_n"] * roughness_scale)
        assert band["manning_n"] > 0.0


def test_package_validates_clean_and_detects_tampering(tmp_path):
    assert validate_cooked_flow_fields_package(PACKAGE_DIR) == []

    tampered = tmp_path / "tampered"
    shutil.copytree(PACKAGE_DIR, tampered)
    victim = tampered / "median_runnable" / "u.npy"
    array = np.load(victim)
    array[0, 0] += 1.0
    np.save(victim, array)
    problems = validate_cooked_flow_fields_package(tampered)
    assert any("median_runnable/u" in problem and "sha256" in problem for problem in problems)


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


@pytest.mark.parametrize("band_id", FLOW_BAND_IDS)
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

    # Mass positivity: depth never negative, and the window holds real water.
    assert h.min() >= 0.0
    volume_m3 = h.sum() * grid["dx_m"] * grid["dy_m"]
    assert volume_m3 > 1000.0

    # Wet fraction sanity: the window is a partly-wet channel (banks stay dry in
    # this DEM valley frame), the mask agrees with the recorded stats, wet cells
    # carry positive depth, and dry cells carry no momentum.
    wet_fraction = wet.mean()
    assert 0.0 < wet_fraction < 1.0
    assert wet_fraction == pytest.approx(band["field_stats"]["wet_fraction"])
    assert h[wet].min() > 0.0
    dry = ~wet
    if dry.any():
        assert np.abs(u[dry]).max() == 0.0
        assert np.abs(v[dry]).max() == 0.0

    # Velocity bounds: plausible white-water speeds, matching recorded stats.
    speed = np.hypot(u, v)
    assert speed.max() < 15.0
    assert speed.max() == pytest.approx(band["field_stats"]["speed_max_m_per_s"], rel=1e-5)

    # Bed grid matches the committed authored band package to float32 rounding.
    committed_bed = np.load(SCENARIO_ROOT / band_id / "bed.npy")
    np.testing.assert_array_equal(bed, committed_bed.astype(np.float32))

    # The cooked state flows downstream on the whole: positive discharge at the
    # west, mid, and east cross-sections, consistent with the manifest record.
    for section, value in band["discharge_steady_m3s"].items():
        assert value > 0.0, section
    mid = h.shape[1] // 2
    assert (h[:, mid] * u[:, mid]).sum() * grid["dy_m"] == pytest.approx(
        band["discharge_steady_m3s"]["mid"], rel=1e-5
    )


def test_bands_are_ordered_by_target_discharge(manifest):
    targets = [band["discharge_target_m3s"] for band in manifest["bands"]]
    assert targets == sorted(targets)
    # cfs targets recorded too, and consistent with the m3/s ordering.
    cfs = [band["discharge_target_cfs"] for band in manifest["bands"]]
    assert cfs == sorted(cfs)


@pytest.mark.parametrize("band_id", FLOW_BAND_IDS)
def test_convergence_evidence_is_recorded_and_self_consistent(manifest, band_id):
    band = next(entry for entry in manifest["bands"] if entry["band_id"] == band_id)
    convergence = band["convergence"]
    thresholds = ConvergenceThresholds(**convergence["thresholds"])
    windows = [ConvergenceWindow(**window) for window in convergence["windows"]]

    assert len(windows) >= thresholds.consecutive_windows_required
    assert convergence["final_window"] == convergence["windows"][-1]

    # The converged flag must be honest: recompute it from the recorded windows.
    # (It is expected to be False for this window -- the authored gut ledge/jump
    # and rock wakes keep the max-abs residual above the strict pilot thresholds
    # even after the bulk flow reaches steady state -- so we assert honesty, not
    # a forced pass.)
    recomputed = all(
        thresholds.window_passes(window)
        for window in windows[-thresholds.consecutive_windows_required :]
    )
    assert convergence["converged"] == recomputed


def test_loader_rejects_unknown_schema(tmp_path):
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "manifest.json").write_text(
        json.dumps({"schema": "raftsim.cooked_flow_fields.v999"}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="Unsupported cooked flow fields schema"):
        read_cooked_flow_fields_manifest(package)
