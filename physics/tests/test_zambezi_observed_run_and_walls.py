"""The 30 km Zambezi run's observed rapids and the upper gorge's reconstructed walls (2026-09-30)."""
import hashlib
import json
import struct
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
Z = REPO_ROOT / "physics/data/real_world/zambezi_batoka_gorge"
CATALOGUE = Z / "observed_rapids/batoka_run_observed_rapids.json"
RESEARCH = Z / "observed_rapids/batoka_run_observations_2026_09_30.json"
SCENARIO = Z / "scenario_zambezi_run/scenario.json"
COOKED = Z / "scenario_zambezi_run/runtime/cooked_flow_fields"
TERRAIN = Z / "terrain/upper_gorge_evidence_2025"


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_every_rapid_has_an_observed_station_with_evidence():
    cat = _json(CATALOGUE)
    assert cat["schema"] == "raftsim.observed_rapid_features.v1" and cat["station_frame"] == "scenario"
    assert cat["observations_sha256"] == _sha(RESEARCH)
    stations = cat["rapid_stations"]
    assert [s["rapid_number"] for s in stations] == [str(n) for n in range(1, 26)]
    controls = [s["control_station_m"] for s in stations]
    assert np.diff(controls).min() >= 150.0
    for s in stations:
        assert s["evidence"] and s["confidence"]
        if s["rapid_number"] != "1":       # Rapid 1's control stays at 160 m behind the launch apron
            assert s["span_m"][0] - 60.0 <= s["control_station_m"] <= s["span_m"][1]
    # Stairway's lip, not the tailrace cascade at 2.7 km; Rapid 25 before the take-out
    assert 3100.0 <= controls[4] <= 3200.0
    assert controls[-1] < cat["take_out"]["finish_station_m"] <= 29000.0
    research = _json(RESEARCH)
    assert len(research["rapids"]) == 25


def test_scenario_and_procedural_controls_follow_the_observed_stations():
    cat = _json(CATALOGUE)
    scenario = _json(SCENARIO)
    manifest = _json(COOKED / "manifest.json")
    contract = manifest["procedural_infill"]["hydraulic_transition_contract"]
    for seen, rapid, row in zip(cat["rapid_stations"], scenario["rapids"], contract["transitions"]):
        assert rapid["station_m"] == seen["control_station_m"]
        assert row["observed_station_m"] == seen["control_station_m"]
        if seen["rapid_number"] != "1":     # Rapid 1 keeps its control behind the launch apron
            assert abs(row["control_station_m"] - seen["control_station_m"]) <= 2.5
    assert contract["all_rapid_transitions_detected"] is True
    stream = _json(COOKED.parent / "moving_water_streaming.json")
    assert stream["full_reach_transit_seed"]["cooked_fields_manifest_sha256"] == _sha(COOKED / "manifest.json")


def test_each_rapid_is_a_central_tongue_between_slow_shelves():
    # Not a bank-to-bank jump across the 144 m reference channel: the control
    # is supercritical in the tongue while the shelves beside it stay slow.
    manifest = _json(COOKED / "manifest.json")
    grid = manifest["grid"]
    h, u = np.load(COOKED / "h.npy"), np.load(COOKED / "u.npy")
    lateral = grid["origin_y_m"] + np.arange(grid["ny"]) * grid["dy_m"]
    centre = int(np.argmin(np.abs(lateral)))
    margin = (np.abs(lateral) >= 50.0) & (h[:, 0] > 0.05)
    froude = np.where(h > 0.05, u / np.sqrt(9.81 * np.maximum(h, 1e-3)), 0.0)
    for row in manifest["procedural_infill"]["hydraulic_transition_contract"]["transitions"]:
        col = int(round(row["control_station_m"] / grid["dx_m"])) - 1
        assert froude[centre, col] > 1.1, row
        assert froude[margin, col].max() < 0.6, row


def test_observed_whitewater_layer_covers_every_rapid():
    side = _json(COOKED / "observed_whitewater_normal_big_water.json")
    path = COOKED / side["file"]
    assert side["render_only"] is True and _sha(path) == side["sha256"]
    assert side["catalogue"]["sha256"] == _sha(CATALOGUE)
    assert side["procedural_field"]["manifest_sha256"] == _sha(COOKED / "manifest.json")
    magic, version, width, rows = struct.unpack("<IIii", path.read_bytes()[:16])
    assert (magic, version, width, rows) == (0x52534246, 1, side["columns"], side["rows"])
    named = [p for p in side["per_rapid"] if p["id"].startswith("r") and p["id"][1:].split("_")[0].isdigit()]
    assert all(p["mean_whitewater"] > 0.05 for p in named)
    numbers = {p["id"][1:].split("_")[0] for p in named}
    assert numbers == {str(n) for n in range(1, 26)}


def test_upper_gorge_walls_are_recorded_and_hydraulics_unchanged():
    tm = _json(TERRAIN / "upper_gorge_evidence_2025_terrain_manifest.json")
    walls = tm["gorge_walls"]
    assert walls["hydraulics_changed"] is False
    assert walls["heightfield_samples_clamped_to_committed_range"] == 0
    stats = walls["statistics"]
    assert stats["zone_cells"]["3"] > 100000 and stats["min_height_above_water_m"] >= 0.6
    assert stats["terrain_min_max_m"] == stats["input_terrain_min_max_m"]
    assert len(walls["beaches"]) == 4
    for key in ("heightfield", "drape", "backdrop_mesh"):
        assert _sha(REPO_ROOT / tm["outputs"][key]) == tm["outputs"][key + "_sha256"]
    canopy = _json(TERRAIN / "upper_gorge_evidence_2025_canopy_placement.json")
    assert canopy["inputs"]["evidence_grid_sha256"] == tm["inputs"]["evidence_grid_sha256"]
    assert canopy["statistics"]["cliff_cells_excluded"] > 0
    assert len(canopy["instances"]) + len(canopy["understory"]) == 11044
    # October (dry season): the leaf state comes from the October Sentinel-2 NDVI.
    leaf = canopy["october_leaf_state"]
    forms = [row[5] for row in canopy["instances"]]
    assert sorted(set(forms)) == [0, 2, 3]
    assert forms.count(0) == leaf["trees"]["green"] and forms.count(2) == leaf["trees"]["leafless"]
    assert forms.count(0) < 0.3 * len(forms), "most of the gorge woodland is leafless or dry in October"
    assert all(len(row) == 6 and row[5] in (0, 1) for row in canopy["understory"])
