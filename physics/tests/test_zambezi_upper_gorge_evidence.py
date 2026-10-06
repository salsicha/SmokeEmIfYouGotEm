"""Evidence-based Zambezi upper gorge on a map-aligned grid (Sentinel-2, GLO-30, ZRA flows; labelled inference).

Checks the archived sources and rapid audit, the Cartesian cook (anchors,
face-flux discharge, settling), the runtime atlas/region/streaming data the
game loads (including the runtime's own load gates), the progress map and
the terrain export. Numpy only.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "physics/data/real_world/zambezi_batoka_gorge"
SOURCES = DATA / "zambezi_sources_2026_09"
SCEN = DATA / "scenario_upper_gorge_evidence_2025"
RT = SCEN / "cartesian_runtime"
EVIDENCE = SCEN / "evidence"
TERRAIN = DATA / "terrain/upper_gorge_evidence_2025"
Q = 283.0


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_sources_and_flow_are_archived() -> None:
    manifest = _json(SOURCES / "manifest.json")
    for rel, digest in manifest["files"].items():
        assert _sha(REPO_ROOT / rel) == digest, rel
    flows = {r["date"]: r["flow_m3s"] for r in _json(SOURCES / "hydrometric/zra_victoria_falls_daily_flows.json")["series"]}
    assert flows["2025-10-03"] == Q
    evidence = _json(EVIDENCE / "evidence_manifest.json")
    assert evidence["parameters"]["discharge_m3s"] == Q and evidence["accepted"] is False
    for name, digest in evidence["inputs"]["sentinel2"].items():
        assert _sha(SOURCES / "sentinel2" / name) == digest, name


def test_reach_holds_the_audited_stairway_whitewater() -> None:
    audit = _json(DATA / "reference/rapid_location_audit_2026_09.json")
    runs = audit["persistent_whitewater_runs"]
    stairway = next(r for r in audit["digitised_rapids"] if r["name"] == "Stairway to Heaven")
    run = stairway["nearest_run_m"]
    reach = _json(EVIDENCE / "evidence_manifest.json")["statistics"]["reach_route_chain_m"]
    assert reach[0] < run[0] and run[1] < reach[1]
    assert any(r["station_m"] == run for r in runs)


def test_cook_meets_anchors_discharge_and_settling() -> None:
    compare = _json(EVIDENCE / "cook_compare.json")
    anchors = [a for a in compare["measured_anchors"] if a["error_m"] is not None]
    # GLO-30 edited water surface: about +-2 m.
    assert len(anchors) >= 8 and all(abs(a["error_m"]) < 2.0 for a in anchors)
    q = compare["discharge_m3s"]
    assert abs(q["inflow_faces"] / Q - 1) < 1e-6 and abs(q["outflow_face"] / Q - 1) < 0.03
    assert compare["convergence"]["p95_abs_dh_m"] < 0.03
    assert abs(compare["conservation_residual_m3"]) < 1.0
    cook = _json(EVIDENCE / "cook_manifest.json")
    assert cook["schema"] == "raftsim.cartesian_flow_cook.v1" and not cook["measured_bathymetry"]


def test_runtime_atlas_region_and_streaming_pass_the_runtime_gates() -> None:
    atlas = _json(RT / "atlas/manifest.json")
    assert atlas["schema"] == "raftsim.cartesian_state_atlas.v1"
    T = atlas["tile_shape"][0]
    arrays = {k: np.load(RT / "atlas" / v["file"]) for k, v in atlas["arrays"].items()}
    for k, v in atlas["arrays"].items():
        assert _sha(RT / "atlas" / v["file"]) == v["sha256"], k
    n = len(atlas["tiles"])
    assert all(a.shape == (n * T, T) and a.dtype == np.dtype("<f8") for a in arrays.values())
    h = arrays["h"]
    assert h.min() >= 0 and h.max() <= 10 and np.hypot(arrays["u"], arrays["v"]).max() <= 20
    # no wet cell on an artificial exterior face (RaftSimLiveWaterWindow.cpp LoadSharedCartesianAtlas)
    D = atlas["grid_spacing_m"]
    keys = {(round((t["origin_m"][0] - atlas["tiles"][0]["origin_m"][0]) / (T * D)),
             round((t["origin_m"][1] - atlas["tiles"][0]["origin_m"][1]) / (T * D))): i for i, t in enumerate(atlas["tiles"])}
    physical = {(f["tile_index"], f["edge"]) for f in atlas["physical_exterior_faces"]}
    faces = dict(west=((-1, 0), np.s_[:, 0]), east=((1, 0), np.s_[:, -1]), south=((0, -1), np.s_[0, :]), north=((0, 1), np.s_[-1, :]))
    for (ki, kj), i in keys.items():
        tile = h[i * T:(i + 1) * T]
        for edge, ((di, dj), sl) in faces.items():
            if (ki + di, kj + dj) in keys:
                continue
            if (tile[sl] != 0).any():
                assert (i, edge) in physical, (i, edge)
    region = _json(RT / "region_upper_gorge/manifest.json")
    assert region["coordinate_system"] == "cartesian_east_north_m" and region["solver"]["runtime_cartesian_coupled_config"]
    (band,) = region["bands"]
    assert band["shared_cartesian_state"]["sha256"] == _sha(RT / "atlas/manifest.json")
    stream = _json(RT / "streaming_manifest.json")
    assert stream["schema"] == "raftsim.cartesian_water_streaming.v1"
    assert stream["roughness_manning"] == region["solver"]["roughness_manning"]
    assert stream["grid_spacing_m"] == D == region["grid"]["dx_m"]
    ext = stream["live_window_extent_m"][0]
    (window,) = stream["windows"]
    b = window["hydraulic_bounds_m"]
    half = ext / 2 + stream["source_context_cells"] * D
    for x0, y0, x1, y1 in window["valid_live_center_bounds_m"]:
        assert b[0] <= x0 - half and x1 + half <= b[2] and b[1] <= y0 - half and y1 + half <= b[3]
    assert stream["coverage"]["raft_water_cells_coverable_share"] > 0.9


def test_progress_map_loads_and_coordinate_map_is_cartesian() -> None:
    cmap = _json(RT / "coordinate_map.json")
    assert cmap["schema"] == "raftsim.cartesian_water_coordinate_map.v1" and cmap["world_y_sign"] == -1
    prog = _json(RT / "progress_coordinate_map.json")
    pts = np.array(prog["points"], dtype=float)
    station, xy, left = pts[:, 0], pts[:, 1:3], pts[:, 3:5]
    assert np.all(np.diff(station) > 0)
    assert np.allclose(np.linalg.norm(left, axis=1), 1.0, atol=1e-6)
    length = np.hypot(*np.diff(xy, axis=0).T).sum()
    assert abs(length - (station[-1] - station[0])) / (station[-1] - station[0]) < 0.005
    for sgn in (-1, 1):
        edge = xy + sgn * 256 * left
        assert np.hypot(*np.diff(edge, axis=0).T).max() <= 16.0


def test_terrain_export_is_consistent() -> None:
    terrain = _json(TERRAIN / "upper_gorge_evidence_2025_terrain_manifest.json")
    for key in ("heightfield", "drape", "backdrop_mesh", "backdrop_drape", "local_centerline"):
        assert _sha(REPO_ROOT / terrain["outputs"][key]) == terrain["outputs"][key + "_sha256"], key
    assert terrain["landscape"]["runtime_vertical_datum_m"] == _json(RT / "coordinate_map.json")["vertical_datum_m"]


def test_launch_is_calm_valid_cartesian_water() -> None:
    water = _json(TERRAIN / "upper_gorge_evidence_2025_terrain_manifest.json")["water"]
    launch = water["launch"]
    assert launch["depth_m"] >= 1.0 and launch["speed_mps"] < 2.5
    x, y = launch["local_xy_m"]
    stream = _json(RT / "streaming_manifest.json")
    (window,) = stream["windows"]
    # a live window clamped to the nearest valid centre holds the raft with its margin
    hold = stream["live_window_extent_m"][0] / 2 - stream["minimum_raft_interior_margin_m"]
    assert any(max(x0 - x, x - x1, y0 - y, y - y1, 0.0) < hold for x0, y0, x1, y1 in window["valid_live_center_bounds_m"])
    stations = np.array(_json(RT / "progress_coordinate_map.json")["points"])[:, 0]
    assert stations[0] < launch["station_m"] < water["finish_station_m"] < stations[-1]


def test_editor_catalog_runtime_and_backdrop_match_the_export() -> None:
    editor = REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private"
    terrain = _json(TERRAIN / "upper_gorge_evidence_2025_terrain_manifest.json")
    landscape = terrain["landscape"]
    catalog = (editor / "Environment/RaftSimEditorEnvironmentCatalog.cpp").read_text(encoding="utf-8")
    block = catalog[catalog.index("upper_gorge_evidence_2025/upper_gorge_evidence_2025_heightfield_2017.png"):]
    block = block[: block.index("Candidates.Add")]
    assert abs(float(re.search(r"TargetReliefCm = ([0-9.]+)f", block).group(1)) - landscape["target_relief_cm"]) < 0.01
    assert abs(float(re.search(r"WorldVerticalOffsetCm = (-?[0-9.]+)f", block).group(1))
               - landscape["world_vertical_offset_cm"]) < 0.01
    assert f"HorizontalSpanXCm = {landscape['horizontal_span_x_m'] * 100:.1f}f" in block
    assert f"HorizontalSpanYCm = {landscape['horizontal_span_y_m'] * 100:.1f}f" in block
    tx, ty, tz = terrain["backdrop"]["actor_translation_cm"]
    build = (editor / "Landscape/RaftSimEditorLandscapeBuild.cpp").read_text(encoding="utf-8")
    assert f"ZambeziBackdropTranslationCm({tx:.1f}, {ty:.1f}, {tz:.1f})" in build
    geometry = (editor / "Landscape/RaftSimEditorLandscapeGeometry.cpp").read_text(encoding="utf-8")
    water = terrain["water"]
    launch = float(re.search(r"kZambeziUpperGorgeLaunchStationM = ([0-9.]+)f;", geometry).group(1))
    finish = float(re.search(r"kZambeziUpperGorgeFinishStationM = ([0-9.]+)f;", geometry).group(1))
    assert abs(launch - water["launch"]["station_m"]) < 0.5 and finish == water["finish_station_m"]
    for rel in ("cartesian_runtime/coordinate_map.json", "cartesian_runtime/streaming_manifest.json",
                "cartesian_runtime/progress_coordinate_map.json", "cartesian_runtime/region_upper_gorge"):
        assert rel in geometry, rel
    assert 'FName(TEXT("low_water_283cms"))' in geometry
    frontend = (REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimUI/Private/RaftSimVerticalSliceFrontend.cpp").read_text(
        encoding="utf-8")
    scenario = frontend.split('TEXT("zambezi_upper_gorge_challenge")', 1)[1].split("};", 1)[0]
    assert f"{launch:.1f}f, {finish:.1f}f)" in scenario and "L_ZambeziUpperGorge" in scenario
    # Packaged builds stage the Cartesian runtime folder.
    water_build = (REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimWater/RaftSimWater.Build.cs").read_text(
        encoding="utf-8")
    assert '"physics/data/real_world/zambezi_batoka_gorge/scenario_upper_gorge_evidence_2025/cartesian_runtime"' in water_build
    # The Cartesian far field (the atlas beyond the live window) is a config opt-in.
    runtime = (REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp").read_text(
        encoding="utf-8")
    assert "RiverWaterConfig->bEnableCookedFarFieldWater &&\n          WaterAdapter && WaterAdapter->HasCartesianWaterCoordinates()" in runtime
