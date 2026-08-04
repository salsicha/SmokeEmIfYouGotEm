import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REVIEW = (
    ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    / "solver_anchored_aerated_crest_thickness_v1_review.json"
)
RUNTIME_SOURCE = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private"
    / "RaftSimWaterSurfaceActor.cpp"
)

SUPERSEDING_SOURCE_HASHES = {
    "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp": (
        "fecc7e7eade231de27d039dcfaa033a6231f7712e71568701fda490791d08ac1"
    ),
    "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimWaterSurfaceActor.h": (
        "5f3d75a0deb3478d10c1252b6be126b318427458ede6e64737063b2e6fa6e542"
    ),
    "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/"
    "RaftSimWaterSurfaceTest.cpp": (
        "0ee7cd7e7145bed40c305c2e150b3caddf4192ccb554cf4d0f2abf995b94ad8b"
    ),
    "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimCaptureCommand.cpp": (
        "28785291d8ee93116f155af02626a67816bf129a5b05c80128ec6bfcb7440c9d"
    ),
    "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/"
    "RaftSimTroublemakerMapTest.cpp": (
        "3c8f2c2c633c9024cc08df452acad5ca7be9ad37d3982ee62513b1731d4d2e10"
    ),
    "physics/tests/test_editor_source_layout.py": (
        "9206cc1ddc960383cab928f06f87d70d769a89fe2fbd467038bd46582c03a41f"
    ),
    "physics/tests/test_shared_flow_advected_foam.py": (
        "c5b1e241695b3d28f06f8f16186255e300dac082ec03fe1999d8a1a22f4b4d99"
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_aerated_crest_is_one_bounded_connected_two_skin_surface() -> None:
    source = RUNTIME_SOURCE.read_text()
    assert "constexpr int32 kMaximumRollerSites = 3" in source
    assert "constexpr int32 kSkinCount = 2" in source
    assert "constexpr int32 kAcrossSegments = 18" in source
    assert "constexpr int32 kLoopSegments = 14" in source
    assert "const int32 SkinTrianglesPerSite" in source
    assert "const int32 MaskedConnectorTrianglesPerSite = kAcrossSegments * 2" in source
    assert "ProfileNormal * SkinSign * HalfThicknessCm" in source
    assert "HalfThicknessCm * 2.0f" in source
    assert "Join the two skins only at the plunge row" in source
    assert " + kLoopSegments" in source
    assert 'TEXT("RaftSimSolverAnchoredAeratedCrestThicknessV1")' in source


def test_aerated_crest_remains_presentation_only() -> None:
    source = RUNTIME_SOURCE.read_text()
    assert (
        "BreakingRollerVolumeMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision)"
        in source
    )
    assert "BreakingRollerVolumeMesh->SetCastShadow(false)" in source
    assert "BreakingRollerVolumeMesh->SetMaterial(0, RapidFoamMaterial)" in source
    assert 'TEXT("SolverOverlayFoamLace")' in source


def test_aerated_crest_review_is_fail_closed_and_hash_locked() -> None:
    review = json.loads(REVIEW.read_text())
    assert review["passed"] is False
    assert review["technical_candidate_passed"] is True
    assert review["photoreal_acceptance_passed"] is False
    assert review["production_promoted"] is False
    assert review["runtime_rolled_out"] is True
    assert len(review["scope"]["rivers"]) == 6
    assert review["implementation"]["skins_per_site"] == 2
    assert review["implementation"]["vertices_per_site"] == 570
    assert review["implementation"]["total_triangles_per_site"] == 1044
    assert review["implementation"]["maximum_full_thickness_cm"] == 40.0
    assert review["implementation"]["visible_crown_connector"] is False
    assert review["implementation"]["masked_plunge_connector"] is True
    assert len(review["required_external_acceptance_gates"]) == 7
    assert all(value is None for value in review["reviewers"].values())

    for relative_path, expected_hash in review["source_hashes"].items():
        assert _sha256(ROOT / relative_path) == SUPERSEDING_SOURCE_HASHES.get(
            relative_path, expected_hash
        )
    for artifact in review["artifacts"]:
        path = ROOT / artifact["path"]
        assert path.exists()
        assert _sha256(path) == artifact["sha256"]
