"""Evidence-based Futaleufu Terminator reach (Sentinel-2 10 m, Copernicus GLO-30, labelled inference).

Checks the archived sources, the Terminator location audit, the exported
runtime data set, its GLO-30 surface anchors, and its agreement with the
editor catalog/runtime config. Numpy only.
"""
from __future__ import annotations

import hashlib
import json
import re
import struct
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "physics/data/real_world/futaleufu_river_chile"
SOURCES = DATA / "futaleufu_sources_2026_09"
SCEN = DATA / "scenario_terminator_evidence_2026"
COOKED = SCEN / "cooked_flow_fields"
EVIDENCE = SCEN / "evidence"
TERRAIN = DATA / "terrain/terminator_evidence_2026"
EDITOR = REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private"
Q_PLANNING = 400.0


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_sources_are_archived_with_provenance() -> None:
    manifest = _json(SOURCES / "manifest.json")
    assert "OpenStreetMap" in manifest["sources"]["osm"]["title"]
    assert "bed" in manifest["not_measured"]
    for rel, digest in manifest["files"].items():
        assert _sha(REPO_ROOT / rel) == digest, rel
    evidence = _json(EVIDENCE / "evidence_manifest.json")
    for name, digest in evidence["inputs"]["glo30"].items():
        assert _sha(DATA / "terrain/source" / name) == digest, name


def test_terminator_is_the_persistent_whitewater_at_its_chainage() -> None:
    audit = _json(EVIDENCE / "terminator_location_audit.json")
    runs = audit["persistent_whitewater_runs"]
    predicted = audit["gorafting_chainage"]["predicted_osm_km"]
    strongest = max(runs, key=lambda r: r["mean_white_px"])
    assert strongest["osm_km"][0] - 0.2 <= predicted <= strongest["osm_km"][1] + 0.2
    assert audit["el_trono_check"]["runs_containing"], "the indicator must fire at the OSM El Trono node"
    reach = _json(EVIDENCE / "evidence_manifest.json")["statistics"]["reach_osm_chain_m"]
    assert reach[0] < strongest["osm_km"][0] * 1000 and strongest["osm_km"][1] * 1000 < reach[1]


def test_cooked_fields_are_complete_conservative_and_settled() -> None:
    manifest = _json(COOKED / "manifest.json")
    assert manifest["schema"] == "raftsim.cooked_flow_fields.v1"
    solver = manifest["solver"]
    assert (solver["solver_mode"], solver["flux_scheme"], solver["spatial_order"]) == ("finite_volume", "hll", 2)
    assert solver["bed_slope_source_scale"] == 1.0 and solver["feature_strength_scale"] == 0.0
    (band,) = manifest["bands"]
    assert band["band_id"] == "high_runnable_400cms" and band["discharge_target_m3s"] == Q_PLANNING
    grid = manifest["grid"]
    for name, meta in band["arrays"].items():
        path = COOKED / meta["file"]
        assert _sha(path) == meta["sha256"], name
        assert list(np.load(path).shape) == meta["shape"] == [grid["ny"], grid["nx"]]
    steady = band["discharge_steady_m3s"]
    assert "face mass flux" in steady["method"]
    for side in ("west", "mid", "east"):
        assert abs(steady[side] / Q_PLANNING - 1.0) < 0.03, side
    assert band["convergence"]["p95_abs_dh_m"] < 0.03
    for key in ("presentation_baseline", "observed_whitewater"):
        path = COOKED / band[key]["file"]
        assert _sha(path) == band[key]["sha256"]
        magic, version, width, rows = struct.unpack("<IIii", path.read_bytes()[:16])
        assert (magic, version, width, rows) == (0x52534246, 1, grid["ny"], grid["nx"])
    assert "not predicted by the solver" in band["observed_whitewater"]["provenance"]


def test_glo30_anchors_and_labels() -> None:
    compare = _json(EVIDENCE / "cook_compare.json")
    anchors = compare["measured_anchors"]
    # GLO-30 edited water surface (TanDEM-X epoch, flow unknown): about +-2 m.
    assert len(anchors) >= 8 and all(abs(a["error_m"]) < 2.0 for a in anchors)
    manifest = _json(COOKED / "manifest.json")
    inferred = " ".join(manifest["provenance"]["inferred"])
    for label in ("bed", "discharge", "surface between anchors", "boulders"):
        assert label in inferred
    evidence = _json(EVIDENCE / "evidence_manifest.json")
    assert evidence["inferred"] is True and evidence["accepted"] is False
    assert "inferred" in evidence["class_codes"]["2"] and "canopy" in evidence["class_codes"]["0"]
    profile = _json(EVIDENCE / "evidence_profile.json")
    levels = [a["elevation_m"] for a in profile["anchors"]]
    assert levels == sorted(levels, reverse=True)


def test_coordinate_map_is_geographic_and_unfolded() -> None:
    cmap = _json(TERRAIN / "terminator_evidence_runtime_coordinate_map.json")
    assert cmap["schema"] == "raftsim.curved_river_coordinate_map.v1"
    assert cmap["world_y_sign"] == -1 and cmap["vertical_datum_m"] == 150.0
    assert "32718" in cmap["horizontal_crs"]
    points = np.array(cmap["points"], dtype=float)
    station, xy, left = points[:, 0], points[:, 1:3], points[:, 3:5]
    assert np.all(np.diff(station) > 0)
    assert np.allclose(np.linalg.norm(left, axis=1), 1.0, atol=1e-6)
    length = np.hypot(*np.diff(xy, axis=0).T).sum()
    assert abs(length - (station[-1] - station[0])) / (station[-1] - station[0]) < 0.005


def test_catalog_runtime_and_backdrop_match_the_export() -> None:
    terrain = _json(TERRAIN / "terminator_evidence_terrain_manifest.json")
    landscape = terrain["landscape"]
    assert _sha(TERRAIN / "terminator_evidence_heightfield_2017.png") == terrain["outputs"]["heightfield_sha256"]
    catalog = (EDITOR / "Environment/RaftSimEditorEnvironmentCatalog.cpp").read_text(encoding="utf-8")
    block = catalog[catalog.index("terminator_evidence_2026/terminator_evidence_heightfield_2017.png"):]
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
    assert f"FutaleufuBackdropTranslationCm({tx:.1f}, {ty:.1f}, {tz:.1f})" in build
    geometry = (EDITOR / "Landscape/RaftSimEditorLandscapeGeometry.cpp").read_text(encoding="utf-8")
    assert "scenario_terminator_evidence_2026/cooked_flow_fields" in geometry
    assert 'FName(TEXT("high_runnable_400cms"))' in geometry
    grid = _json(COOKED / "manifest.json")["grid"]
    assert f"constexpr float kFutaleufuTerminatorReachStationM = {(grid['nx'] - 1) * grid['dx_m']:.1f}f;" in geometry


def test_launch_station_is_in_calm_cooked_water() -> None:
    manifest = _json(COOKED / "manifest.json")
    (band,) = manifest["bands"]
    grid = manifest["grid"]
    geometry = (EDITOR / "Landscape/RaftSimEditorLandscapeGeometry.cpp").read_text(encoding="utf-8")
    launch = float(re.search(r"kFutaleufuTerminatorLaunchStationM = ([0-9.]+)f;", geometry).group(1))
    col = int(round((launch - grid["origin_x_m"]) / grid["dx_m"]))
    h = np.load(COOKED / band["arrays"]["h"]["file"])[:, col]
    u = np.load(COOKED / band["arrays"]["u"]["file"])[:, col]
    assert (h > 1.0).sum() * grid["dy_m"] > 20.0
    assert np.abs(u[h > 1.0]).max() < 3.0
