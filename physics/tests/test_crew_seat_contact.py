"""Runtime wiring and recorded actual-engine seat-contact regressions."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private"


def test_seat_uses_rendered_body_and_tube_triangles():
    raft = (PRIVATE / "RaftSimRaftActor.cpp").read_text(encoding="utf-8")
    seat = raft.split("void ARaftSimRaftActor::AttachAvatarToSeat(")[1].split(
        "void ARaftSimRaftActor::InitializeCrewSeatingForValidation")[0]
    assert seat.index("SetAvatarAction") < seat.index("ComputeRenderedSeatOriginZCm")
    assert "Avatar->GetSeatedContactPointsLocalCm()" in seat
    assert "RenderedContactCompressionCm = 1.0f" in seat
    body = (PRIVATE / "RaftSimCC0CrewVisualActor.cpp").read_text(encoding="utf-8")
    sampling = body.split("GetSeatedContactPointsLocalCm() const")[1].split("void ARaftSimCC0")[0]
    assert "GetParentActor()" in sampling  # actor owner can be the raft, not the avatar
    assert "GetSkinnedVertexPosition" in sampling
    assert "GetVertexData()" in sampling
    importer = (ROOT / "unreal/Scripts/import_cc0_production_characters.py").read_text(encoding="utf-8")
    assert 'subsystem.set_allow_cpu_access(mesh, True)' in importer


def test_recorded_five_character_contact_in_three_poses():
    # A recorded evidence gate, not a replacement for rerunning the UE capture.
    evidence = ROOT / "docs/crew-review-2026-09-06/seat-contact"
    report = json.loads((evidence / "capture.json").read_text())
    assert report["status"] == "complete"
    assert len(report["characters"]) == 5
    assert len(report["transformed_raft_clearances_cm"]) == 5
    assert all(abs(value + 1.0) <= 0.05 for value in report["transformed_raft_clearances_cm"])
    for character in report["characters"]:
        assert character["sample_count"] >= 50
        assert set(character["images"]) == {"side", "rear", "upper"}
        assert {pose["action"] for pose in character["poses"]} == {
            "SEATED_IDLE", "FORWARD_STROKE", "BRACE"}
        for pose in character["poses"]:
            assert pose["finite"]
            assert -1.5 <= pose["clearance_cm"] <= 0.25
    cpu = json.loads((evidence / "cpu-access.json").read_text())
    assert len(cpu) == 5 and all(row["cpu_access_requested"] and row["saved"] for row in cpu)
