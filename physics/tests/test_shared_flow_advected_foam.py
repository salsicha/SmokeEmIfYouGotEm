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
    "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/RaftSimEditorMaterialsBase.cpp": (
        "a9c76ffdf199c6deb42d5b0553f5de2aaf77abefa7f5b2bcbfeb64700e536d5f"
    ),
    "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Tests/RaftSimEditorZambeziWaterTest.cpp": (
        "4037533415156d0d7cb5270dbdfaeaa0bf8a63a26c70f2b6aa75d51849f9bf69"
    ),
    "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp": (
        "ed5cd8a0397a2fc4d453c66871392d11f96cf56b526a29a3045ca1b00c7cbba4"
    ),
    "physics/tests/test_editor_source_layout.py": (
        "a96866c9be97ba8c8de00c9f04b7ccb03186efd80ab50ed87e4589de693208c6"
    ),
}

SUPERSEDING_ARTIFACT_HASHES = {
    "unreal/Content/RaftSim/Materials/LandscapeCandidates/M_RaftSim_SolverFieldFoamCandidate.uasset": (
        "96cae44cf9b54a8aa563583de0823df5eae164ee192e1997340e7b6295db5d56"
    ),
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/shared_flow_advected_foam_v1_native.json": (
        "de9cd54f3671da6c0fa6676699bdb588b956e73b56d28619fa4284ee705c61b2"
    ),
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/shared_flow_advected_foam_v1_p2_p4.json": (
        "842466540f12cd4b4648503f6e4f356233c61f63a8766a760953a962dd0524b9"
    ),
}


def test_shared_foam_is_lit_multiscale_and_solver_masked() -> None:
    source = MATERIAL_SOURCE.read_text()
    assert "Material->SetShadingModel(MSM_DefaultLit)" in source
    assert 'TEXT("RaftSimSolverCurrentAdvectedFoamPrimary")' in source
    assert 'TEXT("RaftSimSolverCurrentAdvectedFoamDetail")' in source
    assert 'TEXT("RaftSimFlowAdvectedMultiscaleFoamV1")' in source
    assert source.count('ParameterName = TEXT("SolverOverlayFoamLace")') >= 2
    assert 'CollectionParameter(TEXT("RaftSimFoamAdvectionMeters"), false)' in source
    assert "FoamPrimaryAdvectionUv->A.Expression = FoamAdvectionRiverMeters" in source
    assert "FoamDetailAdvectionUv->A.Expression = FoamAdvectionRiverMeters" in source
    assert "SolverMaskedLace->A.Expression = VertexColor" in source
    assert "SolverMaskedLace->A.OutputIndex = 4" in source
    assert (
        "SolverMaskedLace->B.Expression = FlowAdvectedMultiscaleLace" in source
    )
    assert "OcclusionSafeFoamMask->B.Expression = RaftExclusion" in source
    assert "Material->OpacityMaskClipValue = 0.01f" in source


def test_shared_foam_does_not_move_solver_or_physics_authority() -> None:
    runtime = RUNTIME_SOURCE.read_text()
    assert "SourceFoam[Index]" in runtime
    assert "VertexColors[Index].R = FinalFoam" in runtime
    assert "FocusedFoam * VertexColors[Index].A" in runtime
    assert "SmoothRapidFoamCoverage(" in runtime
    assert "FoamCoverage >= 0.01f" in runtime
    assert "RaftSimFoamAdvectionMeters" in runtime
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
        assert hashlib.sha256(path.read_bytes()).hexdigest() == (
            SUPERSEDING_ARTIFACT_HASHES.get(artifact["path"], artifact["sha256"])
        )
