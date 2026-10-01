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
