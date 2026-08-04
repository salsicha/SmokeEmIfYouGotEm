from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FULL_REACH_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
    "RaftSimEditorSouthForkFullReach.cpp"
)
MICRORELIEF_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
    "RaftSimEditorSouthForkBankMicrorelief.cpp"
)
BUILD_MANIFEST = (
    REPO_ROOT
    / "unreal/Content/RaftSim/Environment/SouthForkFullReach/"
    "full_reach_environment_build_manifest.json"
)
REVIEW = (
    REPO_ROOT
    / "docs/environment-captures/south_fork_full_reach/"
    "m9_bank_microrelief_v1/review.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_bank_microrelief_is_bounded_dry_only_and_non_authoritative() -> None:
    source = MICRORELIEF_SOURCE.read_text(encoding="utf-8")
    full_reach = FULL_REACH_SOURCE.read_text(encoding="utf-8")

    for token in (
        "MinimumBankDistanceM = 14.0f",
        "MaximumBankDistanceM = 112.0f",
        "MaximumSourceSlope = 0.58f",
        "MaximumWetMask = 0.10f",
        "MaximumDisplacementCm = 42.0f",
        "world_space_phase_continuity",
        'TEXT("wet_cells_emitted"), false',
        'TEXT("affects_gameplay_collision"), false',
        'TEXT("affects_hydraulics"), false',
    ):
        assert token in source
    assert "RaftSimSouthForkDryBankMicroreliefV1" in full_reach
    assert "ECollisionEnabled::NoCollision" in full_reach
    assert "Component->SetCastShadow(false)" in full_reach
    assert "RaftSimDiagnosticHideSouthForkBankMicrorelief" in full_reach


def test_generated_manifest_records_real_geometry_budget() -> None:
    manifest = load_json(BUILD_MANIFEST)
    contract = manifest["dry_bank_microrelief"]
    metrics = manifest["metrics"]

    assert manifest["source_registered_dry_bank_microrelief_v1"] is True
    assert contract["presentation_spacing_m"] == 2
    assert contract["source_spacing_m"] == 4
    assert contract["wet_cells_emitted"] is False
    assert contract["affects_gameplay_collision"] is False
    assert contract["affects_hydraulics"] is False
    assert 5 <= metrics["dry_bank_microrelief_patches"] <= 10
    assert metrics["dry_bank_microrelief_vertices"] == 179896
    assert metrics["dry_bank_microrelief_triangles"] == 219056
    assert metrics["dry_bank_microrelief_maximum_displacement_cm"] == 42


def test_saved_map_assets_and_exact_camera_review_are_hash_locked() -> None:
    review = load_json(REVIEW)

    assert review["passed"] is False
    assert review["technical_candidate_passed"] is True
    assert review["photoreal_acceptance_passed"] is False
    assert review["promotion_allowed"] is False
    assert review["review_decision"]["accepted"] is True
    assert review["review_decision"]["observed_shoreline_regression"] is False
    assert review["review_decision"]["observed_floating_shadow_shelf"] is False
    assert len(review["objective_capture_comparison"]) == 5
    assert len(review["photoreal_rejection_reasons"]) >= 5
    assert len(review["open_gates"]) == 7

    presentation_assets = list(
        (
            REPO_ROOT
            / "unreal/Content/RaftSim/Environment/SouthForkFullReach/Terrain/"
            "Presentation"
        ).glob("SM_*_BankMicroreliefV1_*.uasset")
    )
    assert len(presentation_assets) == 6

    for artifact in review["hash_locked_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert sha256(path) == artifact["sha256"]
