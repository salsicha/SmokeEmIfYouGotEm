from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = (
    REPO_ROOT / "docs/environment-captures/south_fork_full_reach"
)
REVIEW_PATH = EVIDENCE_ROOT / "m9_upper_t_grip_contact_v1_review.json"
ROSTER_PATH = EVIDENCE_ROOT / "m9_upper_t_grip_contact_v1_roster_metrics.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_upper_t_grip_uses_bounded_distal_pad_contact_not_a_radial_cage() -> None:
    source = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
        "RaftSimMetaHumanCrewVisualActor.cpp"
    ).read_text(encoding="utf-8")
    header = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/"
        "RaftSimMetaHumanCrewVisualActor.h"
    ).read_text(encoding="utf-8")
    automation = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/"
        "RaftSimM5ProductionQualityTest.cpp"
    ).read_text(encoding="utf-8")
    capture = (
        REPO_ROOT / "unreal/Scripts/capture_metahuman_production_roster.py"
    ).read_text(encoding="utf-8")

    assert "PaddleTGripPadCenterRadiusCm = 2.95f" in source
    assert "PaddleTGripUsableHalfLengthCm = 5.65f" in source
    assert "ApplyUpperFingerPadToTGrip" in source
    assert "ApplyUpperOpposedThumbPadToTGrip" in source
    assert "Correcting only the distal pad" in source
    assert "SetSegmentBone(SecondName, ThirdName, SecondCm, TargetPadCm)" in source
    assert "FMath::Clamp" in source
    assert "MeasureUpperTGripThumbOppositionDot" in source
    assert "GetMaximumUpperTGripFingerContactErrorCm" in header
    assert "GetMaximumUpperTGripThumbContactErrorCm" in header
    assert "GetMaximumUpperTGripThumbOppositionDot" in header
    assert "without a whole-chain radial cage" in automation
    assert "GetMaximumUpperTGripThumbOppositionDot() <= -0.95f" in automation
    assert "runtime_upper_t_grip_finger_contact_error_cm" in capture
    assert "runtime_upper_t_grip_thumb_contact_error_cm" in capture
    assert "runtime_upper_t_grip_thumb_opposition_dot" in capture


def test_runtime_roster_closes_all_five_upper_t_grips() -> None:
    roster = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
    assert roster["schema"] == "raftsim.m9.upper_t_grip_contact.runtime.v1"
    assert roster["status"] == "capture_complete"
    assert roster["captured_character_count"] == 5
    assert {character["name"] for character in roster["characters"]} == {
        "MHC_RaftSim_Guide",
        "MHC_RaftSim_Crew_01",
        "MHC_RaftSim_Crew_02",
        "MHC_RaftSim_Crew_03",
        "MHC_RaftSim_Crew_04",
    }
    assert max(
        character["palm_anchor_error_cm"] for character in roster["characters"]
    ) <= 0.25
    assert max(
        character["lower_finger_contact_error_cm"]
        for character in roster["characters"]
    ) <= 0.25
    assert max(
        character["lower_thumb_contact_error_cm"]
        for character in roster["characters"]
    ) <= 0.25
    assert max(
        character["upper_finger_contact_error_cm"]
        for character in roster["characters"]
    ) <= 0.25
    assert max(
        character["upper_thumb_contact_error_cm"]
        for character in roster["characters"]
    ) <= 0.25
    assert max(
        character["upper_thumb_opposition_dot"]
        for character in roster["characters"]
    ) <= -0.95
    assert all(character["localized_glove"] for character in roster["characters"])


def test_upper_t_grip_review_is_hash_locked_and_fail_closed() -> None:
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    assert review["schema"] == "raftsim.m9.upper_t_grip_contact_review.v1"
    assert review["passed"] is False
    assert review["technical_candidate_passed"] is True
    assert review["photoreal_acceptance_passed"] is False
    assert review["human_approved"] is False
    assert review["promotion_allowed"] is False
    assert review["implementation"]["upper_t_grip_hands"] == 5
    assert review["implementation"]["contact_constrained_upper_finger_chains"] == 20
    assert review["implementation"]["contact_constrained_upper_thumb_pads"] == 5
    assert review["implementation"]["physics_or_gameplay_changes"] is False

    runtime = review["runtime_roster_metrics"]
    assert _sha256(REPO_ROOT / runtime["report"]) == runtime["report_sha256"]
    for path, expected_hash in review["renderer_evidence"]["candidate"].values():
        assert _sha256(REPO_ROOT / path) == expected_hash
    for path, expected_hash in review["implementation_sha256"].items():
        assert _sha256(REPO_ROOT / path) == expected_hash


def test_native_m5_upper_t_grip_gate_passed_without_warnings() -> None:
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    validation = review["validation"]["m5"]
    report_path = REPO_ROOT / validation["report"]
    assert _sha256(report_path) == validation["report_sha256"]
    report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    assert report["succeeded"] == 1
    assert report["succeededWithWarnings"] == 0
    assert report["failed"] == 0
    assert report["tests"][0]["fullTestPath"] == (
        "RaftSim.M5.CrewAvatarPoseProduction"
    )


def test_all_six_runnable_maps_pass_after_shared_character_change() -> None:
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    validation = review["validation"]["p4_all_rivers"]
    report_path = REPO_ROOT / validation["report"]
    assert _sha256(report_path) == validation["report_sha256"]
    report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    assert report["succeeded"] + report["succeededWithWarnings"] == 6
    assert report["failed"] == 0
    assert report["notRun"] == 0
    assert report["inProcess"] == 0
    assert {test["fullTestPath"] for test in report["tests"]} == {
        "RaftSim.P4.RiverMapLoads.L_Hance",
        "RaftSim.P4.RiverMapLoads.L_LavaCanyon",
        "RaftSim.P4.RiverMapLoads.L_Terminator",
        "RaftSim.P4.RiverMapLoads.L_Troublemaker",
        "RaftSim.P4.RiverMapLoads.L_UpperHuacas",
        "RaftSim.P4.RiverMapLoads.L_Zambezi",
    }
    assert all(test["errors"] == 0 for test in report["tests"])
