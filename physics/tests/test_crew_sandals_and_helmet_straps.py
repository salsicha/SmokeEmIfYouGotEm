"""Source-art and runtime contracts for the crew's river sandals and the
helmet retention straps fitted to each wearer."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EQUIPMENT = REPO_ROOT / "unreal/SourceArt/RaftSim/Equipment"
CONTENT = REPO_ROOT / "unreal/Content/RaftSim/Equipment/Production"
SCRIPTS = REPO_ROOT / "unreal/Scripts"
RAFT_SOURCE = REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft"
WEARERS = ["Crew01", "Crew02", "Crew03", "Crew04", "Guide"]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_river_sandals_are_fitted_to_the_cc0_feet_and_hash_locked() -> None:
    manifest = json.loads((EQUIPMENT / "ProductionRiverSandal/production_river_sandal_manifest.json").read_text(encoding="utf-8"))
    assert manifest["material_slots"] == ["SandalSole", "SandalFootbed", "SandalStrap", "SandalHardware"]
    assert manifest["construction"]["straps"] == ["toe", "instep", "heel"]
    assert len(manifest["source_inputs"]) == 5
    for side in ("L", "R"):
        entry = manifest["meshes"][f"SM_RaftSim_RiverSandal_{side}"]
        assert _sha256(REPO_ROOT / entry["fbx"]) == entry["fbx_sha256"]
        low, high = entry["bounds_cm"]["min"], entry["bounds_cm"]["max"]
        # Centred on the ankle: a foot long, a hand wide, wholly below it.
        assert 22.0 <= high[0] - low[0] <= 30.0
        assert 9.0 <= high[1] - low[1] <= 13.0
        assert high[2] <= 0.5 and low[2] < -8.0
        assert (CONTENT / f"SM_RaftSim_RiverSandal_{side}.uasset").is_file()
    left, right = (manifest["meshes"][f"SM_RaftSim_RiverSandal_{s}"]["bounds_cm"] for s in "LR")
    # Mirror images: the big-toe side swaps with the foot.
    assert left["min"][1] == -right["max"][1] and left["max"][1] == -right["min"][1]

    build = (SCRIPTS / "build_production_river_sandal.py").read_text(encoding="utf-8")
    assert "REFERENCE_ANKLE_TO_BALL_CM = 12.0" in build
    assert "REFERENCE_ANKLE_HEIGHT_CM = 7.05" in build
    avatar = (RAFT_SOURCE / "Private/RaftSimCrewAvatarActor.cpp").read_text(encoding="utf-8")
    # The runtime fit uses the same reference foot as the generator.
    assert "ReferenceAnkleToBallCm = 12.0f" in avatar
    assert "ReferenceAnkleHeightCm = 7.05f" in avatar
    assert "SM_RaftSim_RiverSandal_L" in avatar and "SM_RaftSim_RiverSandal_R" in avatar
    visual = (RAFT_SOURCE / "Private/RaftSimCC0CrewVisualActor.cpp").read_text(encoding="utf-8")
    # Bare feet stand at rest size and turn with their sandals.
    assert "bBareFeet ? 1.0f : kHiddenFootBoneScale" in visual
    assert "GetFootwearYawDegrees(Pose, bLeft)" in visual


def test_helmet_straps_are_fitted_under_each_wearers_chin() -> None:
    manifest = json.loads((EQUIPMENT / "ProductionHelmet/Straps/production_helmet_straps_manifest.json").read_text(encoding="utf-8"))
    assert manifest["material_slots"] == ["HelmetWebbing", "HelmetHardware"]
    for wearer in WEARERS:
        entry = manifest["meshes"][f"SM_RaftSim_HelmetStraps_{wearer}"]
        assert _sha256(REPO_ROOT / entry["fbx"]) == entry["fbx_sha256"]
        assert entry["min_skin_clearance_cm"] > 0.0
        # The chin strap passes under the chin, well below the shell rim.
        assert entry["chin_point"][2] < -12.0
        assert (CONTENT / f"SM_RaftSim_HelmetStraps_{wearer}.uasset").is_file()
    # The generator places each head with the game's own helmet fit.
    straps = (SCRIPTS / "build_production_helmet_straps.py").read_text(encoding="utf-8")
    visual = (RAFT_SOURCE / "Private/RaftSimCC0CrewVisualActor.cpp").read_text(encoding="utf-8")
    assert "CrewHelmetAnchorDropsCm[] = {3.0f, 4.0f, 4.0f, 4.0f}" in visual
    assert "CrewHelmetAnchorBackCm[] = {5.0f, 5.5f, 5.0f, 5.0f}" in visual
    assert "CrewHelmetFitScale = 0.84f" in visual
    assert "GuideHelmetFitScale = 0.90f" in visual
    assert '("Crew01", 3.0, 5.0, 0.84)' in straps and '("Guide", 5.0, 5.5, 0.90)' in straps
    # The shared shell no longer carries the face and chin straps.
    helmet = (SCRIPTS / "build_production_whitewater_helmet.py").read_text(encoding="utf-8")
    assert "ChinBuckle" not in helmet
    avatar = (RAFT_SOURCE / "Private/RaftSimCrewAvatarActor.cpp").read_text(encoding="utf-8")
    assert "ProductionHelmetStraps->SetupAttachment(ProductionHelmet)" in avatar
    assert "SM_RaftSim_HelmetStraps_%s" in avatar
