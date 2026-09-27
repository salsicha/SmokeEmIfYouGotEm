"""Evidence-based Pacuare Huacas-Pinball reach (IGN contours/banks/orthophoto, labelled inference).

Checks the archived sources, the exported runtime data set, its measured
water-surface anchors, and its agreement with the editor catalog/runtime
config. Numpy only.
"""
from __future__ import annotations

import hashlib
import json
import re
import struct
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "physics/data/real_world/pacuare_river_costa_rica"
SOURCES = DATA / "huacas_sources_2026_09"
SCEN = DATA / "scenario_huacas_evidence_2017"
COOKED = SCEN / "cooked_flow_fields"
EVIDENCE = SCEN / "evidence"
TERRAIN = DATA / "terrain/huacas_evidence_2017"
EDITOR = REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private"
Q_PLANNING = 45.0


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_sources_are_archived_with_provenance() -> None:
    manifest = _json(SOURCES / "manifest.json")
    assert "IGN" in manifest["sources"]["ign5_vectors"]["title"]
    assert "unclear" in manifest["sources"]["ign5_vectors"]["licence"]
    assert "not_measured" in manifest and "bed" in manifest["not_measured"]
    for rel, digest in manifest["files"].items():
        assert _sha(REPO_ROOT / rel) == digest, rel


def test_cooked_fields_are_complete_conservative_and_settled() -> None:
    manifest = _json(COOKED / "manifest.json")
    assert manifest["schema"] == "raftsim.cooked_flow_fields.v1"
    solver = manifest["solver"]
    assert (solver["solver_mode"], solver["flux_scheme"], solver["spatial_order"]) == ("finite_volume", "hll", 2)
    assert solver["bed_slope_source_scale"] == 1.0 and solver["feature_strength_scale"] == 0.0
    (band,) = manifest["bands"]
    assert band["band_id"] == "rainfed_runnable_45cms" and band["discharge_target_m3s"] == Q_PLANNING
    grid = manifest["grid"]
    for name, meta in band["arrays"].items():
        path = COOKED / meta["file"]
        assert _sha(path) == meta["sha256"], name
        array = np.load(path)
        assert list(array.shape) == meta["shape"] == [grid["ny"], grid["nx"]]
        assert array.flags["C_CONTIGUOUS"]
    # Exact face mass flux (the cell-centre h*u sum overstates transport on
    # this steep wet/dry reach and is kept only as a labelled diagnostic).
    steady = band["discharge_steady_m3s"]
    assert "face mass flux" in steady["method"]
    for side in ("west", "mid", "east"):
        assert abs(steady[side] / Q_PLANNING - 1.0) < 0.03, side
    assert "diagnostic" in band["discharge_cell_centre_hu_sum_m3s"]["note"]
    assert band["convergence"]["p95_abs_dh_m"] < 0.03
    for key in ("presentation_baseline", "observed_whitewater"):
        path = COOKED / band[key]["file"]
        assert _sha(path) == band[key]["sha256"]
        magic, version, width, rows = struct.unpack("<IIii", path.read_bytes()[:16])
        assert (magic, version, width, rows) == (0x52534246, 1, grid["ny"], grid["nx"])
    assert "not predicted by the solver" in band["observed_whitewater"]["provenance"]


def test_measured_anchors_and_labels() -> None:
    compare = _json(EVIDENCE / "cook_compare.json")
    anchors = compare["measured_anchors"]
    # Contour-crossing anchors (IGN 10 m contours; station placement +-30 m on
    # a 1.6% slope): the calibrated cook must sit within their uncertainty.
    assert len(anchors) >= 3 and all(abs(a["error_m"]) < 0.5 for a in anchors)
    manifest = _json(COOKED / "manifest.json")
    inferred = " ".join(manifest["provenance"]["inferred"])
    for label in ("bed", "discharge", "surface between contour crossings", "boulders"):
        assert label in inferred
    evidence = _json(EVIDENCE / "evidence_manifest.json")
    assert evidence["inferred"] is True and evidence["accepted"] is False
    assert "inferred" in evidence["class_codes"]["2"] and "inferred" in evidence["class_codes"]["4"]
    profile = _json(EVIDENCE / "evidence_profile.json")
    levels = [a["elevation_m"] for a in profile["anchors"]]
    assert levels == sorted(levels, reverse=True) and 180.0 in levels and 150.0 in levels


def test_coordinate_map_is_geographic_and_unfolded() -> None:
    cmap = _json(TERRAIN / "huacas_evidence_runtime_coordinate_map.json")
    assert cmap["schema"] == "raftsim.curved_river_coordinate_map.v1"
    assert cmap["world_y_sign"] == -1 and cmap["vertical_datum_m"] == 150.0
    points = np.array(cmap["points"], dtype=float)
    station, xy, left = points[:, 0], points[:, 1:3], points[:, 3:5]
    assert np.all(np.diff(station) > 0)
    assert np.allclose(np.linalg.norm(left, axis=1), 1.0, atol=1e-6)
    length = np.hypot(*np.diff(xy, axis=0).T).sum()
    assert abs(length - (station[-1] - station[0])) / (station[-1] - station[0]) < 0.005


def test_catalog_runtime_and_backdrop_match_the_export() -> None:
    terrain = _json(TERRAIN / "huacas_evidence_terrain_manifest.json")
    landscape = terrain["landscape"]
    assert _sha(TERRAIN / "huacas_evidence_heightfield_2017.png") == terrain["outputs"]["heightfield_sha256"]
    catalog = (EDITOR / "Environment/RaftSimEditorEnvironmentCatalog.cpp").read_text(encoding="utf-8")
    block = catalog[catalog.index("huacas_evidence_2017/huacas_evidence_heightfield_2017.png"):]
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
    assert f"PacuareBackdropTranslationCm({tx:.1f}, {ty:.1f}, {tz:.1f})" in build
    geometry = (EDITOR / "Landscape/RaftSimEditorLandscapeGeometry.cpp").read_text(encoding="utf-8")
    assert "scenario_huacas_evidence_2017/cooked_flow_fields" in geometry
    assert 'FName(TEXT("rainfed_runnable_45cms"))' in geometry
    manifest = _json(COOKED / "manifest.json")
    grid = manifest["grid"]
    reach = (grid["nx"] - 1) * grid["dx_m"]
    assert f"constexpr float kPacuareHuacasReachStationM = {reach:.1f}f;" in geometry


def test_launch_station_is_in_deep_calm_cooked_water() -> None:
    manifest = _json(COOKED / "manifest.json")
    (band,) = manifest["bands"]
    grid = manifest["grid"]
    geometry = (EDITOR / "Landscape/RaftSimEditorLandscapeGeometry.cpp").read_text(encoding="utf-8")
    launch = float(re.search(r"kPacuareHuacasLaunchStationM = ([0-9.]+)f;", geometry).group(1))
    col = int(round((launch - grid["origin_x_m"]) / grid["dx_m"]))
    h = np.load(COOKED / band["arrays"]["h"]["file"])[:, col]
    u = np.load(COOKED / band["arrays"]["u"]["file"])[:, col]
    assert (h > 1.0).sum() * grid["dy_m"] > 15.0
    assert np.abs(u[h > 1.0]).max() < 1.5


def test_evidence_dressing_is_labelled_and_inside_the_landscape() -> None:
    terrain = _json(TERRAIN / "huacas_evidence_terrain_manifest.json")["landscape"]
    canopy = _json(TERRAIN / "huacas_evidence_canopy_placement.json")
    assert canopy["schema"] == "raftsim.pacuare.huacas_evidence_canopy.v1"
    assert canopy["positions_from_imagery"] and not canopy["tree_inventory_surveyed"]
    assert canopy["species_heights_and_forms_inferred"] and "INFERRED" in canopy["understory_mesh"]
    assert canopy["inputs"]["terrain_manifest_sha256"] == _sha(TERRAIN / "huacas_evidence_terrain_manifest.json")
    stats = canopy["statistics"]
    assert len(canopy["instances"]) == stats["instance_count"] >= 20000
    assert len(canopy["understory"]) == stats["understory_count"]
    rocks = _json(TERRAIN / "huacas_evidence_rock_placement.json")
    assert rocks["schema"] == "raftsim.pacuare.huacas_evidence_rocks.v1" and "INFERRED" in rocks["method"]
    assert len(rocks["instances"]) == rocks["instance_count"] >= 700
    assert rocks["evidence_grid_sha256"] == canopy["inputs"]["evidence_grid_sha256"]
    span_x, span_y = terrain["horizontal_span_x_m"] * 100.0, terrain["horizontal_span_y_m"] * 100.0
    for rows in (canopy["instances"], canopy["understory"], rocks["instances"]):
        xy = np.array(rows, dtype=float)[:, :2]
        assert (xy[:, 0] >= 0).all() and (xy[:, 0] <= span_x).all() and (np.abs(xy[:, 1]) <= span_y / 2).all()
