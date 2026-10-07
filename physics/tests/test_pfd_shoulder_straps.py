"""Source-art contracts for the PFD's per-wearer shoulder straps and the
guide's flip line, both fitted to the production vest shell."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EQUIPMENT = REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment"
SCRIPTS = REPO_ROOT / "unreal/Scripts"
PFD_MANIFEST = EQUIPMENT / "ProductionPfd/production_whitewater_pfd_manifest.json"
STRAPS_MANIFEST = EQUIPMENT / "ProductionPfd/ShoulderStraps/production_pfd_shoulder_straps_manifest.json"
FLIP_LINE_MANIFEST = EQUIPMENT / "ProductionFlipLine/production_guide_flip_line_manifest.json"
WEARERS = ["Crew01", "Crew02", "Crew03", "Crew04", "Guide"]
PFD_SLOTS = ["PfdShell", "PfdWebbing", "PfdHardware", "PfdReflective", "PfdLabel"]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_shoulder_straps_are_fitted_to_each_wearer_and_meet_the_vest_mounts() -> None:
    pfd = json.loads(PFD_MANIFEST.read_text(encoding="utf-8"))
    straps = json.loads(STRAPS_MANIFEST.read_text(encoding="utf-8"))
    # The shared shell no longer carries padded straps, only their mounts.
    assert pfd["construction"]["padded_shoulder_straps"] == 0
    assert pfd["construction"]["shoulder_strap_anchors"] == 2
    assert straps["material_slots"] == PFD_SLOTS
    assert straps["fitted_to_pfd"]["fbx_sha256"] == pfd["fbx_sha256"]
    assert straps["fitted_to_pfd"]["generator_version"] == pfd["generator_version"]
    for source in straps["source_inputs"]:
        assert _sha256(REPO_ROOT / source["path"]) == source["sha256"]
    # Narrow straps inboard over the trapezius, so a raised paddling arm's
    # deltoid passes outboard of them.
    construction = straps["construction"]
    assert construction["padded_width_cm"] <= 4.0
    assert construction["strap_plane_y_cm"] == pfd["shoulder_straps"]["strap_plane_y_cm"]
    assert construction["strap_plane_y_cm"] + 0.5 * construction["padded_width_cm"] <= 15.0
    assert 0.0 < construction["skin_gap_cm"] <= 0.5
    assert _sha256(REPO_ROOT / straps["blend"]) == straps["blend_sha256"]
    for wearer in WEARERS:
        entry = straps["meshes"][f"SM_RaftSim_PfdShoulderStraps_{wearer}"]
        assert _sha256(REPO_ROOT / entry["fbx"]) == entry["fbx_sha256"]
        for side in ("+1", "-1"):
            assert entry["straps"][side]["min_skin_gap_cm"] > 0.0
        # From the chest tab, over the shoulder, down to the back anchor.
        assert entry["bounds_min_cm"][2] < pfd["fit"]["panel_tops_cm"]["back"]
        assert entry["bounds_max_cm"][2] > pfd["fit"]["panel_tops_cm"]["front_tab"]

    build = (SCRIPTS / "build_production_pfd_shoulder_straps.py").read_text(encoding="utf-8")
    assert 'DUMP_WEARERS = ("Crew01", "Crew02", "Crew04", "Crew03", "Guide")' in build
    assert 'apply_scale_options="FBX_SCALE_ALL"' in build
    importer = (SCRIPTS / "import_production_pfd_shoulder_straps.py").read_text(encoding="utf-8")
    assert 'DESTINATION = "/Game/RaftSim/Equipment/Production"' in importer
    assert "fitted_to_pfd" in importer


def test_guide_flip_line_is_fitted_to_the_current_vest() -> None:
    pfd = json.loads(PFD_MANIFEST.read_text(encoding="utf-8"))
    flip = json.loads(FLIP_LINE_MANIFEST.read_text(encoding="utf-8"))
    assert flip["material_slots"] == ["FlipLineWebbing", "FlipLineHardware"]
    assert flip["fitted_to_pfd"]["fbx_sha256"] == pfd["fbx_sha256"]
    assert flip["construction"]["wraps"] == 2
    assert flip["construction"]["locking_carabiners"] == 1
    assert flip["open_edges"] == 0
    for key in ("fbx", "blend"):
        assert _sha256(REPO_ROOT / flip[key]) == flip[f"{key}_sha256"]
