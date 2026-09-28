"""Evidence-based Chilko Lava Canyon reach (LidarBC 1 m, Sentinel-2, HYDAT, VRI; labelled inference).

Checks the archived sources, the archived LiDAR, the calibration against the
LiDAR water surface, the exported runtime data set, the VRI canopy and its
agreement with the editor catalog/runtime config. Numpy only.
"""
from __future__ import annotations

import hashlib
import json
import re
import struct
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "physics/data/real_world/chilko_river_bc"
SOURCES = DATA / "chilko_sources_2026_09"
SCEN = DATA / "scenario_lava_canyon_evidence_2023"
COOKED = SCEN / "cooked_flow_fields"
EVIDENCE = SCEN / "evidence"
TERRAIN = DATA / "terrain/lava_canyon_evidence_2023"
EDITOR = REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private"
BAND = "summer_runnable_93cms"
Q_BAND = 93.0


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_sources_are_archived_with_provenance() -> None:
    manifest = _json(SOURCES / "manifest.json")
    assert "LidarBC" in manifest["sources"]["lidar"]["title"]
    assert "Vegetation Resources Inventory" in manifest["sources"]["vri"]["title"]
    assert "bed" in manifest["not_measured"]
    for rel, digest in manifest["files"].items():
        assert _sha(REPO_ROOT / rel) == digest, rel
    tiles = {t["file"]: t["sha256"] for t in manifest["sources"]["lidar"]["tiles"]}
    evidence = _json(EVIDENCE / "evidence_manifest.json")
    for tile in evidence["inputs"]["lidar_crop"]["tiles"]:
        assert tiles[tile["file"]] == tile["sha256"], tile["file"]
    for name, digest in evidence["inputs"]["sentinel2"].items():
        assert _sha(SOURCES / "sentinel2" / name) == digest, name


def test_archived_lidar_decodes_to_the_evidence_terrain() -> None:
    terrain = _json(TERRAIN / "lava_canyon_evidence_2023_terrain_manifest.json")
    window = np.load(REPO_ROOT / terrain["outputs"]["lidar_window"])
    assert _sha(REPO_ROOT / terrain["outputs"]["lidar_window"]) == terrain["outputs"]["lidar_window_sha256"]
    height = float(window["base_m"]) + np.cumsum(window["height_delta_cm"].astype(np.int64), axis=1) / 100.0
    grid = _json(EVIDENCE / "evidence_manifest.json")["grid"]
    assert height.shape == (grid["ny"], grid["nx"])
    assert (float(window["x0"]), float(window["y_top"])) == (grid["x0"], grid["y_top"])
    assert 800.0 < height.min() and height.max() < 1200.0
    surround = np.load(REPO_ROOT / terrain["outputs"]["lidar_surround"])
    assert float(surround["cell_m"]) == 20.0 and np.isfinite(surround["height_m"]).all()
    assert "Open Government Licence - British Columbia" in terrain["archived_lidar"]["licence"]


def test_bidwell_rapid_is_the_whitewater_and_the_lidar_drop() -> None:
    calib = _json(EVIDENCE / "calibration_compare.json")
    bins = calib["whitewater_vs_froude_by_250m"]
    strongest = max(bins, key=lambda b: b["evidence_whitewater_share"])
    assert 700.0 <= strongest["station_m"] <= 1000.0
    anchors = sorted(calib["measured_anchors"], key=lambda a: a["scenario_station_m"])
    drops = [(b["scenario_station_m"], a["elevation_m"] - b["elevation_m"]) for a, b in zip(anchors, anchors[1:])]
    station, drop = max(drops, key=lambda d: d[1])
    assert 800.0 <= station <= 1000.0 and drop > 2.0
    reach = _json(EVIDENCE / "evidence_manifest.json")["statistics"]["reach_corridor_chain_m"]
    assert reach == [43900.0, 47900.0]


def test_calibration_reproduces_the_lidar_water_surface() -> None:
    calib = _json(EVIDENCE / "calibration_compare.json")
    assert calib["discharge_target_m3s"] == 45.0
    anchors = calib["measured_anchors"]
    # LiDAR flight-day water surface (1 m DEM, flow 57 falling to 33 m3/s).
    assert len(anchors) >= 30 and all(abs(a["error_m"]) < 0.6 for a in anchors)
    assert abs(calib["reference_surface_error_m"]["median"]) < 0.15
    assert calib["wet_iou"] > 0.88
    assert abs(calib["discharge_m3s"]["outlet_face"] / 45.0 - 1.0) < 0.03
    evidence = _json(EVIDENCE / "evidence_manifest.json")
    assert evidence["accepted"] is False
    assert "inferred" in evidence["class_codes"]["2"].lower() and "measured" in evidence["class_codes"]["0"]
    assert evidence["parameters"]["bed_correction"] and _sha(EVIDENCE / "bed_correction.npz") == evidence["parameters"]["bed_correction_sha256"]


def test_cooked_fields_are_complete_conservative_and_settled() -> None:
    manifest = _json(COOKED / "manifest.json")
    assert manifest["schema"] == "raftsim.cooked_flow_fields.v1"
    solver = manifest["solver"]
    assert (solver["solver_mode"], solver["flux_scheme"], solver["spatial_order"]) == ("finite_volume", "hll", 2)
    assert solver["bed_slope_source_scale"] == 1.0 and solver["feature_strength_scale"] == 0.0
    (band,) = manifest["bands"]
    assert band["band_id"] == BAND and band["discharge_target_m3s"] == Q_BAND
    grid = manifest["grid"]
    for name, meta in band["arrays"].items():
        path = COOKED / meta["file"]
        assert _sha(path) == meta["sha256"], name
        assert list(np.load(path).shape) == meta["shape"] == [grid["ny"], grid["nx"]]
    steady = band["discharge_steady_m3s"]
    assert "face mass flux" in steady["method"]
    for side in ("west", "mid", "east"):
        assert abs(steady[side] / Q_BAND - 1.0) < 0.03, side
    assert band["convergence"]["p95_abs_dh_m"] < 0.03
    for key in ("presentation_baseline", "observed_whitewater"):
        path = COOKED / band[key]["file"]
        assert _sha(path) == band[key]["sha256"]
        magic, version, width, rows = struct.unpack("<IIii", path.read_bytes()[:16])
        assert (magic, version, width, rows) == (0x52534246, 1, grid["ny"], grid["nx"])
    assert "not predicted by the solver" in band["observed_whitewater"]["provenance"]
    inferred = " ".join(manifest["provenance"]["inferred"])
    for label in ("bed", "boulders", "roughness", "tributary"):
        assert label in inferred


def test_coordinate_map_is_geographic_and_unfolded() -> None:
    cmap = _json(TERRAIN / "lava_canyon_evidence_2023_runtime_coordinate_map.json")
    assert cmap["schema"] == "raftsim.curved_river_coordinate_map.v1"
    assert cmap["world_y_sign"] == -1 and cmap["vertical_datum_m"] == 850.0
    assert "3157" in cmap["horizontal_crs"]
    points = np.array(cmap["points"], dtype=float)
    station, xy, left = points[:, 0], points[:, 1:3], points[:, 3:5]
    assert np.all(np.diff(station) > 0)
    assert np.allclose(np.linalg.norm(left, axis=1), 1.0, atol=1e-6)
    length = np.hypot(*np.diff(xy, axis=0).T).sum()
    assert abs(length - (station[-1] - station[0])) / (station[-1] - station[0]) < 0.005


def test_vri_canopy_follows_the_inventory() -> None:
    placement = _json(TERRAIN / "lava_canyon_evidence_2023_canopy_placement.json")
    assert placement["schema"] == "raftsim.chilko.lava_canyon_evidence_canopy.v1"
    assert _sha(REPO_ROOT / placement["inputs"]["vri"]) == placement["inputs"]["vri_sha256"]
    assert placement["cover_from_inventory"] and not placement["positions_from_imagery"]
    rows = np.array(placement["instances"], dtype=float)
    assert len(rows) >= 60000
    by_poly = {p["feature"]: p for p in placement["polygons"]}
    assert sum(p["trees"] for p in by_poly.values()) == len(rows)
    for p in by_poly.values():
        if p["trees"]:
            closure = p["crown_closure_pct"] / 100.0
            # crown closure x area / crown area, never above the inventory's stems per hectare
            assert p["trees"] <= (p["stems_per_ha"] or 1e9) * p["area_in_window_ha"] + 1
            assert closure > 0
    heights = rows[:, 4]
    assert 5.0 < np.median(heights) < 25.0
    assert (rows[:, 5] == 1).mean() > 0.95  # the inventory is conifer (pine, Douglas-fir, spruce)


def test_catalog_runtime_and_backdrop_match_the_export() -> None:
    terrain = _json(TERRAIN / "lava_canyon_evidence_2023_terrain_manifest.json")
    landscape = terrain["landscape"]
    assert _sha(TERRAIN / "lava_canyon_evidence_2023_heightfield_2017.png") == terrain["outputs"]["heightfield_sha256"]
    catalog = (EDITOR / "Environment/RaftSimEditorEnvironmentCatalog.cpp").read_text(encoding="utf-8")
    block = catalog[catalog.index("lava_canyon_evidence_2023/lava_canyon_evidence_2023_heightfield_2017.png"):]
    block = block[: block.index("}")]
    relief = float(re.search(r"TargetReliefCm = ([0-9.]+)f", block).group(1))
    offset = float(re.search(r"WorldVerticalOffsetCm = (-?[0-9.]+)f", block).group(1))
    assert abs(relief - landscape["target_relief_cm"]) < 0.01
    assert abs(offset - landscape["world_vertical_offset_cm"]) < 0.01
    assert f"HorizontalSpanXCm = {landscape['horizontal_span_x_m'] * 100:.1f}f" in block
    assert f"HorizontalSpanYCm = {landscape['horizontal_span_y_m'] * 100:.1f}f" in block
    backdrop = terrain["backdrop"]
    assert _sha(REPO_ROOT / backdrop["mesh"]) == terrain["outputs"]["backdrop_mesh_sha256"]
    build = (EDITOR / "Landscape/RaftSimEditorLandscapeBuild.cpp").read_text(encoding="utf-8")
    tx, ty, tz = backdrop["actor_translation_cm"]
    assert f"ChilkoBackdropTranslationCm({tx:.1f}, {ty:.1f}, {tz:.1f})" in build
    geometry = (EDITOR / "Landscape/RaftSimEditorLandscapeGeometry.cpp").read_text(encoding="utf-8")
    assert "scenario_lava_canyon_evidence_2023/cooked_flow_fields" in geometry
    assert f'FName(TEXT("{BAND}"))' in geometry
    grid = _json(COOKED / "manifest.json")["grid"]
    assert f"constexpr float kChilkoLavaCanyonReachStationM = {(grid['nx'] - 1) * grid['dx_m']:.1f}f;" in geometry


def test_launch_station_is_in_cooked_water_above_the_rapid() -> None:
    manifest = _json(COOKED / "manifest.json")
    (band,) = manifest["bands"]
    grid = manifest["grid"]
    geometry = (EDITOR / "Landscape/RaftSimEditorLandscapeGeometry.cpp").read_text(encoding="utf-8")
    launch = float(re.search(r"kChilkoLavaCanyonLaunchStationM = ([0-9.]+)f;", geometry).group(1))
    assert launch < 750.0  # above Bidwell Rapid's whitewater
    col = int(round((launch - grid["origin_x_m"]) / grid["dx_m"]))
    h = np.load(COOKED / band["arrays"]["h"]["file"])[:, col]
    u = np.load(COOKED / band["arrays"]["u"]["file"])[:, col]
    assert (h > 0.8).sum() * grid["dy_m"] > 14.0
    assert np.abs(u[h > 0.8]).max() < 3.5
