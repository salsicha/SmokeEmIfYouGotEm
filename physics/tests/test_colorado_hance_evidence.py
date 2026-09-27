"""Evidence-based Hance reach (2021 DEM/imagery, 2014 sonar, labelled inference).

Checks the archived sources, the exported runtime data set and its agreement
with the editor catalog/runtime config. Numpy only.
"""
from __future__ import annotations

import hashlib
import json
import struct
import re
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "physics/data/real_world/colorado_river_grand_canyon_rowing"
SOURCES = DATA / "hance_sources_2026_09"
COOKED = DATA / "scenario_hance_evidence_2021/cooked_flow_fields"
EVIDENCE = DATA / "scenario_hance_evidence_2021/evidence"
TERRAIN = DATA / "terrain/hance_evidence_2021"
EDITOR = REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private"
Q_8000_CFS = 226.534772736


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_sources_are_archived_with_provenance() -> None:
    manifest = _json(SOURCES / "manifest.json")
    assert manifest["horizontal_crs"].startswith("NAD83(2011) / Arizona Central")
    assert "ellipsoid" in manifest["vertical_datum"]
    assert manifest["not_measured"].startswith("bed inside the rapid")
    for rel, digest in manifest["files"].items():
        assert _sha(REPO_ROOT / rel) == digest, rel


def test_cooked_fields_are_complete_conservative_and_settled() -> None:
    manifest = _json(COOKED / "manifest.json")
    assert manifest["schema"] == "raftsim.cooked_flow_fields.v1"
    assert manifest["source_elevation_datum_m"] == 0.0
    solver = manifest["solver"]
    assert (solver["solver_mode"], solver["flux_scheme"], solver["spatial_order"]) == ("finite_volume", "hll", 2)
    assert solver["bed_slope_source_scale"] == 1.0 and solver["feature_strength_scale"] == 0.0
    (band,) = manifest["bands"]
    assert band["band_id"] == "steady_8000cfs_2021"
    assert band["discharge_target_m3s"] == Q_8000_CFS
    grid = manifest["grid"]
    for name, meta in band["arrays"].items():
        path = COOKED / meta["file"]
        assert _sha(path) == meta["sha256"], name
        array = np.load(path)
        assert list(array.shape) == meta["shape"] == [grid["ny"], grid["nx"]]
        assert array.dtype == np.dtype(meta["dtype"])
        assert array.flags["C_CONTIGUOUS"]
    for side in ("west", "mid", "east"):
        assert abs(band["discharge_steady_m3s"][side] / Q_8000_CFS - 1.0) < 0.03
    assert band["convergence"]["p95_abs_dh_m"] < 0.01
    baseline = COOKED / band["presentation_baseline"]["file"]
    assert _sha(baseline) == band["presentation_baseline"]["sha256"]
    assert baseline.read_bytes()[:4] == (0x52534246).to_bytes(4, "little")


def test_inference_is_labelled_and_validation_recorded() -> None:
    manifest = _json(COOKED / "manifest.json")
    inferred = " ".join(manifest["provenance"]["inferred"])
    assert "bed inside the rapid" in inferred and "boulders" in inferred
    evidence = _json(EVIDENCE / "evidence_manifest.json")
    assert evidence["inferred"] is True and evidence["accepted"] is False
    assert "4" in evidence["class_codes"] and "inferred" in evidence["class_codes"]["4"]
    boulders = _json(EVIDENCE / "inferred_boulders.json")
    assert boulders["inferred"] is True and len(boulders["boulders"]) > 50
    compare = _json(EVIDENCE / "cook_compare.json")
    assert compare["textured_surface_error_m"]["median_abs"] < 0.25
    assert compare["wet_extent"]["iou"] > 0.9
    assert abs(compare["discharge_m3s"]["section_p5_p50_p95"][1] / Q_8000_CFS - 1.0) < 0.03


def test_coordinate_map_is_geographic_and_unfolded() -> None:
    cmap = _json(TERRAIN / "hance_evidence_runtime_coordinate_map.json")
    assert cmap["schema"] == "raftsim.curved_river_coordinate_map.v1"
    assert cmap["world_y_sign"] == -1 and cmap["vertical_datum_m"] == 740.0
    points = np.array(cmap["points"], dtype=float)
    station, xy, left = points[:, 0], points[:, 1:3], points[:, 3:5]
    assert np.all(np.diff(station) > 0)
    length = np.hypot(*np.diff(xy, axis=0).T).sum()
    assert abs(length - (station[-1] - station[0])) / (station[-1] - station[0]) < 0.005
    for sign in (1.0, -1.0):
        edge = xy + sign * 256.0 * left / np.linalg.norm(left, axis=1, keepdims=True)
        assert np.hypot(*np.diff(edge, axis=0).T).max() <= 16.0


def test_catalog_and_runtime_match_the_exported_terrain() -> None:
    terrain = _json(TERRAIN / "hance_evidence_terrain_manifest.json")
    landscape = terrain["landscape"]
    assert _sha(TERRAIN / "hance_evidence_heightfield_2017.png") == terrain["outputs"]["heightfield_sha256"]
    catalog = (EDITOR / "Environment/RaftSimEditorEnvironmentCatalog.cpp").read_text(encoding="utf-8")
    block = catalog[catalog.index("hance_evidence_2021/hance_evidence_heightfield_2017.png"):]
    block = block[: block.index("}")]
    relief = float(re.search(r"TargetReliefCm = ([0-9.]+)f", block).group(1))
    offset = float(re.search(r"WorldVerticalOffsetCm = (-?[0-9.]+)f", block).group(1))
    assert abs(relief - landscape["target_relief_cm"]) < 0.01
    assert abs(offset - landscape["world_vertical_offset_cm"]) < 0.01
    assert "LandscapeSize = 2017" in block and "HorizontalSpanXCm = 250000.0f" in block
    assert "HorizontalSpanYCm = 121200.0f" in block and "bUseSolverVisualizationFields = false" in block
    # Outside the corridor DEM the Landscape is measured 3DEP, and the
    # builder places the 3DEP backdrop where the export put it.
    assert "USGS 3DEP 10 m" in terrain["composition"]["nan_fill"]
    assert -24.5 < terrain["dep_3dep"]["offset_to_ellipsoid_m"] < -22.0
    backdrop = terrain["backdrop"]
    assert _sha(REPO_ROOT / backdrop["mesh"]) == terrain["outputs"]["backdrop_mesh_sha256"]
    assert backdrop["collision"] is False and backdrop["actor_scale"] == [1.0, -1.0, 1.0]
    build = (EDITOR / "Landscape/RaftSimEditorLandscapeBuild.cpp").read_text(encoding="utf-8")
    tx, ty, tz = backdrop["actor_translation_cm"]
    assert f"BackdropTranslationCm({tx:.1f}, {ty:.1f}, {tz:.1f})" in build
    assert "SetActorScale3D(FVector(1.0, -1.0, 1.0))" in build
    geometry = (EDITOR / "Landscape/RaftSimEditorLandscapeGeometry.cpp").read_text(encoding="utf-8")
    assert "scenario_hance_evidence_2021/cooked_flow_fields" in geometry
    assert 'FName(TEXT("steady_8000cfs_2021"))' in geometry
    assert "constexpr float kColoradoHanceLaunchStationM = 520.0f;" in geometry


def test_observed_whitewater_field_is_labelled_appearance_evidence() -> None:
    manifest = _json(COOKED / "manifest.json")
    (band,) = manifest["bands"]
    observed = band["observed_whitewater"]
    path = COOKED / observed["file"]
    assert _sha(path) == observed["sha256"]
    assert "not predicted by the solver" in observed["provenance"] and "never gameplay" in observed["use"]
    header = path.read_bytes()[:24]
    magic, version, width, rows = struct.unpack("<IIii", header[:16])
    grid = manifest["grid"]
    assert (magic, version, width, rows) == (0x52534246, 1, grid["ny"], grid["nx"])
    stream = _json(DATA / "scenario_hance_evidence_2021/runtime/moving_water_streaming.json")
    assert stream["full_reach_transit_seed"]["cooked_fields_manifest_sha256"] == _sha(COOKED / "manifest.json")
    audit = _json(DATA / "scenario_hance_evidence_2021/evidence/whitewater_indicator_audit.json")
    best = max(r["iou"] for r in audit["indicators"].values())
    assert best < 0.2 and audit["indicators"]["froude"]["iou"] < best  # why the photo, not the cook, places it
    geometry = (EDITOR / "Landscape/RaftSimEditorLandscapeGeometry.cpp").read_text(encoding="utf-8")
    assert "WaterConfig->ObservedWhitewaterGain = 0.9f;" in geometry


def test_launch_station_is_in_deep_cooked_water() -> None:
    manifest = _json(COOKED / "manifest.json")
    (band,) = manifest["bands"]
    grid = manifest["grid"]
    h = np.load(COOKED / band["arrays"]["h"]["file"])
    col = int(round((520.0 - grid["origin_x_m"]) / grid["dx_m"]))
    column = h[:, col]
    assert (column > 1.0).sum() * grid["dy_m"] > 40.0  # a wide, deep pool at the put-in
