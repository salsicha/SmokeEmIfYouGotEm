"""Observed-rapid catalogues on the five evidence reaches and the layers built from them.

Each reach's catalogue (outfitter, guidebook, trip-report and video observations)
must name its sources for every feature; the render-only observed-whitewater
layer the game loads must record the catalogue it was raised to (by hash); and
the two reaches whose beds carry reconstructed features (Zambezi upper gorge,
Futaleufu Terminator) must record the catalogue in their evidence manifests.
Numpy only.
"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "physics/data/real_world"
FEATURE_TYPES = {"ledge_hole", "pour_over", "boulder", "rock_garden", "wave_train", "lateral", "diagonal",
                 "constriction", "drop", "whitewater_boulders", "sill"}
CATALOGUES = {
    "zambezi": DATA / "zambezi_batoka_gorge/observed_rapids/upper_gorge_observed_rapids.json",
    "futaleufu": DATA / "futaleufu_river_chile/observed_rapids/terminator_observed_rapids.json",
    "chilko": DATA / "chilko_river_bc/observed_rapids/lava_canyon_observed_rapids.json",
    "pacuare": DATA / "pacuare_river_costa_rica/observed_rapids/huacas_observed_rapids.json",
    "hance": DATA / "colorado_river_grand_canyon_rowing/observed_rapids/hance_observed_rapids.json",
}
CURVED_EXPORTS = {
    "futaleufu": DATA / "futaleufu_river_chile/scenario_terminator_evidence_2026",
    "chilko": DATA / "chilko_river_bc/scenario_lava_canyon_evidence_2023",
    "pacuare": DATA / "pacuare_river_costa_rica/scenario_huacas_evidence_2017",
    "hance": DATA / "colorado_river_grand_canyon_rowing/scenario_hance_evidence_2021",
}
ZAMBEZI_REGION = DATA / "zambezi_batoka_gorge/scenario_upper_gorge_evidence_2025/cartesian_runtime/region_upper_gorge"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_catalogues_name_sources_for_every_feature() -> None:
    for river, path in CATALOGUES.items():
        cat = _json(path)
        assert cat["schema"] == "raftsim.observed_rapid_features.v1", river
        assert cat["discharge_m3s"] > 0 and cat["station_frame"] in ("scenario", "evidence"), river
        assert cat["rapids"] and cat["features"], river
        for rapid in cat["rapids"]:
            assert rapid["length_m"] > 0 and rapid.get("rapid_class"), (river, rapid["id"])
        for feature in cat["features"]:
            assert feature["type"] in FEATURE_TYPES, (river, feature["id"])
            assert feature["sources"], (river, feature["id"])
            assert all(s.get("url") or s.get("type") for s in feature["sources"]), (river, feature["id"])
        research = sorted(path.parent.glob("*_observations_2026_09_29.json"))
        assert research and (research[0].with_suffix(".md")).exists(), river
        assert "banks_terrain_vegetation" in _json(research[0]), river


def test_curved_map_layers_record_their_catalogue() -> None:
    for river, export in CURVED_EXPORTS.items():
        cooked = export / "cooked_flow_fields"
        (band,) = _json(cooked / "manifest.json")["bands"]
        record = band["observed_whitewater"]
        layer = cooked / record["file"]
        assert _sha(layer) == record["sha256"], river
        magic, version = struct.unpack("<II", layer.read_bytes()[:8])
        assert (magic, version) == (0x52534246, 1), river
        catalogue = record["catalogue"]
        assert (REPO_ROOT / catalogue["path"]).resolve() == CATALOGUES[river].resolve(), river
        assert catalogue["sha256"] == _sha(CATALOGUES[river]), river
        assert catalogue["cells_raised"] > 0 and record["cells_with_whitewater"] >= catalogue["cells_raised"], river
        assert "not predicted by the solver" in record["provenance"], river
        assert "render-only" in record["use"] and "never gameplay" in record["use"], river
        streaming = _json(export / "runtime/moving_water_streaming.json")
        seed = streaming.get("full_reach_transit_seed")
        if seed:
            assert seed["cooked_fields_manifest_sha256"] == _sha(cooked / "manifest.json"), river


def test_zambezi_cartesian_layer_is_loaded_and_records_its_catalogue() -> None:
    sidecar = _json(ZAMBEZI_REGION / "observed_whitewater_low_water_283cms.json")
    assert sidecar["schema"] == "raftsim.cartesian_observed_whitewater.v1" and sidecar["render_only"] is True
    assert _sha(ZAMBEZI_REGION / sidecar["file"]) == sidecar["sha256"]
    assert sidecar["catalogue"]["path"] == CATALOGUES["zambezi"].relative_to(REPO_ROOT).as_posix()
    assert sidecar["catalogue"]["sha256"] == _sha(CATALOGUES["zambezi"])
    assert sidecar["cells_with_whitewater"] > sidecar["photographed"]["cells_with_whitewater"]
    geometry = (REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/"
                "RaftSimEditorLandscapeGeometry.cpp").read_text(encoding="utf-8")
    note = geometry.index("(export_cartesian_observed_whitewater.py) that floors displayed foam.")
    block = geometry[geometry.rindex("if (bZambeziUpperGorge)", 0, note):note + 200]
    assert "cartesian_runtime/streaming_manifest.json" in block and "bEnableCookedFarFieldWater = true" in block
    assert block[block.index("floors displayed foam."):].split("\n")[1].strip() == "WaterConfig->ObservedWhitewaterGain = 0.9f;"


def test_reconstructed_beds_record_the_catalogue() -> None:
    for river, evidence in (
            ("zambezi", DATA / "zambezi_batoka_gorge/scenario_upper_gorge_evidence_2025/evidence/evidence_manifest.json"),
            ("futaleufu", DATA / "futaleufu_river_chile/scenario_terminator_evidence_2026/evidence/evidence_manifest.json")):
        manifest = _json(evidence)
        record = manifest["observed_rapid_features"]
        assert record["catalogue_sha256"] == _sha(CATALOGUES[river]), river
        assert record["features"] == len(_json(CATALOGUES[river])["features"]) == len(record["imprint"]), river
        assert "5" in manifest["class_codes"] and "observations" in manifest["class_codes"]["5"], river
