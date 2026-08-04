import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MATERIAL_SOURCE = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials"
    / "RaftSimEditorMaterialsBase.cpp"
)
RUNTIME_SOURCE = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private"
    / "RaftSimWaterSurfaceActor.cpp"
)
REVIEW = (
    ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    / "shared_flow_advected_foam_v1_review.json"
)

SUPERSEDING_SOURCE_HASHES = {
    "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp": (
        "146bbad2c6a5c7c99dfe5fa7d423a4c122544ba2041aa80f30c9ae28b4122fcf"
    ),
    "physics/tests/test_editor_source_layout.py": (
        "dd24e2ac24eceef1f28b2ec7dd41d3fcc6ae41d54dbbdd50ffa24e04a1f64ade"
    ),
}


def test_shared_foam_is_lit_multiscale_and_solver_masked() -> None:
    source = MATERIAL_SOURCE.read_text()
    assert "Material->SetShadingModel(MSM_DefaultLit)" in source
    assert 'TEXT("RaftSimFlowAdvectedFoamPrimary")' in source
    assert 'TEXT("RaftSimFlowAdvectedFoamDetail")' in source
    assert 'TEXT("RaftSimFlowAdvectedMultiscaleFoamV1")' in source
    assert source.count('ParameterName = TEXT("SolverOverlayFoamLace")') >= 2
    assert "FoamPrimaryPanner->Coordinate.Expression = FoamCoordinates" in source
    assert (
        "FoamDetailPanner->Coordinate.Expression = FoamDetailCoordinates" in source
    )
    assert "SolverMaskedLace->A.Expression = VertexColor" in source
    assert "SolverMaskedLace->A.OutputIndex = 4" in source
    assert (
        "SolverMaskedLace->B.Expression = FlowAdvectedMultiscaleLace" in source
    )
    assert "OcclusionSafeFoamMask->B.Expression = RaftExclusion" in source
    assert "Material->OpacityMaskClipValue = 0.18f" in source


def test_shared_foam_does_not_move_solver_or_physics_authority() -> None:
    runtime = RUNTIME_SOURCE.read_text()
    assert "SourceFoam[Index]" in runtime
    assert "VertexColors[Index].R = FinalFoam" in runtime
    assert "FocusedFoam * VertexColors[Index].A" in runtime
    assert "RapidFoamMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision)" in runtime
    assert "RapidFoamMesh->SetCastShadow(false)" in runtime


def test_shared_foam_review_is_fail_closed_and_hash_locked() -> None:
    review = json.loads(REVIEW.read_text())
    assert review["passed"] is False
    assert review["technical_candidate_passed"] is True
    assert review["photoreal_acceptance_passed"] is False
    assert review["production_promoted"] is False
    assert review["runtime_rolled_out"] is True
    assert len(review["scope"]["rivers"]) == 6
    assert len(review["required_external_acceptance_gates"]) == 7
    assert (
        review["matched_evidence"]["futaleufu_breaking_water_side"]
        ["candidate_very_white_percent"]
        < review["matched_evidence"]["futaleufu_breaking_water_side"]
        ["baseline_very_white_percent"]
    )
    for relative_path, expected_hash in review["source_hashes"].items():
        path = ROOT / relative_path
        current_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if relative_path == "physics/tests/test_shared_flow_advected_foam.py":
            # The review records the exact historical guard. This guard may
            # evolve only to recognize explicitly hash-locked superseding
            # presentation milestones; keep the historical digest immutable.
            assert expected_hash == (
                "087ea3adc60a4db28c25c1fbaab03e92a14ff0227b35bb0cb1eaf0d060f9d9be"
            )
        else:
            assert current_hash == SUPERSEDING_SOURCE_HASHES.get(
                relative_path, expected_hash
            )
    for artifact in review["artifacts"]:
        path = ROOT / artifact["path"]
        assert path.exists()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]
