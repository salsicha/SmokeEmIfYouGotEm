"""Observed rock on the Futaleufu and Chilko banks and Huacas Falls on the Pacuare (2026-09-30)."""
import hashlib
import json
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "physics/data/real_world"
ROCKS = {
    "futaleufu": DATA / "futaleufu_river_chile/terrain/terminator_evidence_2026/terminator_evidence_observed_rock_placement.json",
    "chilko": DATA / "chilko_river_bc/terrain/lava_canyon_evidence_2023/lava_canyon_evidence_2023_observed_rock_placement.json",
}
PACUARE = DATA / "pacuare_river_costa_rica/terrain/huacas_evidence_2017"


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_observed_rock_follows_its_observations_and_stays_out_of_the_water():
    for river, path in ROCKS.items():
        rock = _json(path)
        assert rock["schema"] == "raftsim.observed_rock_placement.v1", river
        assert rock["terrain_or_hydraulic_geometry_modified"] is False
        assert _sha(REPO_ROOT / rock["inputs"]["observations"]) == rock["inputs"]["observations_sha256"]
        assert _sha(REPO_ROOT / rock["inputs"]["cooked_manifest"]) == rock["inputs"]["cooked_manifest_sha256"]
        rows = np.array(rock["instances"], float)
        assert rows.shape[1] == 10 and len(rows) == sum(z["placed"] for z in rock["zones"])
        assert all(z["observation"] for z in rock["zones"])
        assert rows[:, 7].min() >= 0 and rows[:, 7].max() <= 5
        assert (rows[:, 3] > 0).all() and (rows[:, 5] > 0).all()
    futa = {z["id"]: z for z in _json(ROCKS["futaleufu"])["zones"]}
    assert futa["top_bend_cliff"]["side"] == "right" and futa["right_bend_left_outcrop"]["side"] == "left"
    chilko = {z["id"]: z for z in _json(ROCKS["chilko"])["zones"]}
    assert chilko["talus_fan_2700_right"]["span"] == [2640, 2790]


def test_huacas_falls_is_recorded_and_painted():
    fall = _json(PACUARE / "huacas_evidence_observed_waterfall.json")
    assert fall["schema"] == "raftsim.observed_waterfall.v1" and fall["side"] == "right"
    assert 30.0 <= fall["lip_height_above_water_m"] <= 46.0
    assert fall["terrain_or_hydraulic_geometry_modified"] is False
    tm = _json(PACUARE / "huacas_evidence_terrain_manifest.json")
    assert tm["observed_waterfall"]["record"] == "huacas_evidence_observed_waterfall.json"
    assert _sha(REPO_ROOT / tm["outputs"]["drape"]) == tm["outputs"]["drape_sha256"]
    canopy = _json(PACUARE / "huacas_evidence_canopy_placement.json")
    assert canopy["statistics"]["removed_on_huacas_falls"] == fall["canopy_removed_trees_shrubs"]


def test_pacuare_rainforest_is_closed_and_layered_and_keeps_the_falls_clear():
    canopy = _json(PACUARE / "huacas_evidence_canopy_placement.json")
    tm = _json(PACUARE / "huacas_evidence_terrain_manifest.json")
    fall = _json(PACUARE / "huacas_evidence_observed_waterfall.json")
    structure = canopy["rainforest_structure"]
    assert structure["inferred"] is True
    stats = canopy["statistics"]
    kinds = [row[6] for row in canopy["instances"]]
    assert kinds.count(2) == stats["sub_canopy_count"] > 10000
    assert stats["canopy_tree_count"] + stats["sub_canopy_count"] == len(canopy["instances"])
    # overlapping crowns (radius ~ neighbour spacing) and a tall stand
    assert stats["crown_radius_m_p10_p50_p90"][1] >= 6.0
    assert 22.0 <= stats["height_m_p10_p50_p90"][1] <= 35.0
    assert len(canopy["understory"]) >= 1.8 * stats["canopy_tree_count"]
    # nothing stands on the Huacas Falls fall line
    base, lip = np.array(fall["base_cm"]) / 100.0, np.array(fall["lip_cm"]) / 100.0
    v = lip - base
    for rows in (canopy["instances"], canopy["understory"]):
        xy = np.array(rows, dtype=float)[:, :2] / 100.0
        u = np.clip(((xy - base) @ v) / (v @ v), 0, 1)
        assert np.hypot(*(xy - (base + u[:, None] * v)).T).min() >= 7.0
    # the forest floor under the crowns is shaded, and the drape hash is recorded
    assert tm["forest_floor_shade"]["shaded_share"] > 0.6
    assert _sha(REPO_ROOT / tm["outputs"]["drape"]) == tm["outputs"]["drape_sha256"]
    assert canopy["inputs"]["terrain_manifest_sha256"] == _sha(PACUARE / "huacas_evidence_terrain_manifest.json")
