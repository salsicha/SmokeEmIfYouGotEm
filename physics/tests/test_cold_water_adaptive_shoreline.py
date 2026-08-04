import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REVIEW_PATH = (
    ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
    / "cold_water_adaptive_shoreline_v1_review.json"
)
GEOMETRY_SOURCE = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape"
    / "RaftSimEditorLandscapeGeometry.cpp"
)
BUILD_SOURCE = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape"
    / "RaftSimEditorLandscapeBuild.cpp"
)
MAP_TEST_SOURCE = (
    ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests"
    / "RaftSimTroublemakerMapTest.cpp"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _review() -> dict:
    return json.loads(REVIEW_PATH.read_text())


def test_adaptive_shoreline_review_is_fail_closed() -> None:
    review = _review()
    assert review["passed"] is False
    assert review["status"] == "rejected_not_retained_last_accepted_maps_restored"
    decision = review["decision"]
    assert decision["technical_mesh_candidate_passed"] is True
    assert decision["visual_shoreline_improvement_passed"] is False
    assert decision["no_new_artifact_gate_passed"] is False
    assert decision["candidate_source_retained"] is False
    assert decision["candidate_map_packages_retained"] is False
    assert decision["candidate_material_packages_retained"] is False
    assert len(review["required_external_acceptance_gates"]) == 6


def test_rejected_shoreline_code_is_not_active() -> None:
    for source in (GEOMETRY_SOURCE, BUILD_SOURCE, MAP_TEST_SOURCE):
        text = source.read_text()
        assert "AddColdWaterAdaptiveShorelineTerrain" not in text
        assert "RaftSimColdWaterAdaptiveShorelineV1" not in text


def test_last_accepted_maps_and_materials_are_hash_locked() -> None:
    review = _review()["restored_release_assets"]
    expected = {
        "terminator_map_sha256": ROOT / "unreal/Content/RaftSim/Maps/L_Terminator.umap",
        "lava_canyon_map_sha256": ROOT / "unreal/Content/RaftSim/Maps/L_LavaCanyon.umap",
        "futaleufu_physical_terrain_material_sha256": (
            ROOT
            / "unreal/Content/RaftSim/Materials/LandscapeCandidates"
            / "M_RaftSim_Futaleufu_PhysicalSourceTerrainRender.uasset"
        ),
        "chilko_physical_terrain_material_sha256": (
            ROOT
            / "unreal/Content/RaftSim/Materials/LandscapeCandidates"
            / "M_RaftSim_Chilko_PhysicalSourceTerrainRender.uasset"
        ),
    }
    for key, path in expected.items():
        assert _sha256(path) == review[key]


def test_rejection_evidence_is_hash_locked() -> None:
    for artifact in _review()["retained_artifacts"]:
        path = ROOT / artifact["path"]
        assert path.exists()
        assert _sha256(path) == artifact["sha256"]


def test_review_does_not_credit_water_delta_as_shoreline_progress() -> None:
    evidence = _review()["matched_evidence"]
    bank = evidence["bank_closeup"]
    breaking = evidence["breaking_water_side"]
    assert bank["water_rows_400_719"]["changed2pct_fraction"] > 0.90
    assert bank["bank_transition_rows_250_379"]["edge08_after"] < bank[
        "bank_transition_rows_250_379"
    ]["edge08_before"]
    assert breaking["bank_transition_rows_250_379"]["edge08_after"] < breaking[
        "bank_transition_rows_250_379"
    ]["edge08_before"]
