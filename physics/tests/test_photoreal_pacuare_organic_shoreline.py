import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FOLIAGE_SOURCE = REPO_ROOT / (
    "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/"
    "RaftSimEditorLandscapeFoliage.cpp"
)
MAP_TEST_SOURCE = REPO_ROOT / (
    "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/"
    "RaftSimTroublemakerMapTest.cpp"
)
REVIEW_PATH = REPO_ROOT / (
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "pacuare_organic_shoreline_v1_review.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_pacuare_organic_shoreline_source_is_dense_and_authority_bounded():
    source = FOLIAGE_SOURCE.read_text(encoding="utf-8")
    assert "PacuareOrganicShorelineRockTargetInstanceCount = 2600" in source
    assert "PacuareOrganicShorelineGroundCoverTargetInstanceCount = 5200" in source
    assert "PacuareOrganicShorelineShrubTargetInstanceCount = 1200" in source
    assert "PacuareOrganicShorelineRockSlopeCeilingDegrees = 50.0f" in source
    assert "PacuareOrganicShorelineGroundCoverSlopeCeilingDegrees = 44.0f" in source
    assert "PacuareOrganicShorelineShrubSlopeCeilingDegrees = 38.0f" in source
    for contract_tag in (
        "RaftSimPacuareOrganicShorelineV1",
        "RaftSimSourceLandscapeGrounded",
        "RaftSimOutsideProtectedSolverStrip",
        "RaftSimNonCollisionRenderSurface",
        "RaftSimPresentationOnlyNoHydraulicAuthority",
        "RaftSimGenericRockAnalogNoLithologyAuthority",
        "RaftSimNoSpeciesOrEcologyAuthority",
    ):
        assert contract_tag in source
    assert "const float VisibleRiverHalfWidth" in source
    assert "GetMinimumCenterlineDistanceCm" in source
    assert "GetConditionedWaterWorldZ" in source
    assert "GetLandscapeSlopeDegrees" in source


def test_pacuare_runtime_gate_audits_saved_shoreline_instances():
    source = MAP_TEST_SOURCE.read_text(encoding="utf-8")
    assert "Pacuare organic shoreline has eight dedicated morphology actors" in source
    assert "OrganicShorelineRockInstanceCount >= 2350" in source
    assert "OrganicShorelineGroundCoverInstanceCount >= 4700" in source
    assert "OrganicShorelineShrubInstanceCount >= 1050" in source
    assert "Pacuare organic shoreline remains non-colliding" in source
    assert "Pacuare organic shoreline disclaims hydraulic authority" in source


def test_pacuare_organic_shoreline_review_is_honest_and_hash_locked():
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    assert review["status"] == (
        "retained_technical_visual_improvement_photoreal_promotion_open"
    )
    assert review["passed"] is False
    decision = review["decision"]
    assert decision["reference_runnable"] is True
    assert decision["technical_candidate_passed"] is True
    assert decision["photoreal_acceptance_passed"] is False
    for unchanged_contract in (
        "landscape_geometry_changed",
        "landscape_collision_changed",
        "cooked_fields_changed",
        "wet_dry_mask_changed",
        "bathymetry_changed",
        "hydraulics_changed",
        "raft_forces_changed",
    ):
        assert decision[unchanged_contract] is False

    runtime = review["runtime_contract"]
    assert runtime["placed_moss_rock_instances"] == 2600
    assert runtime["placed_short_ground_cover_instances"] == 5200
    assert runtime["placed_shrub_instances"] == 1200
    assert runtime["rejected_placements"] == 0
    assert runtime["dedicated_actor_count"] == 8
    assert runtime["minimum_centerline_distance_cm"] >= 1770.0
    assert runtime["maximum_placed_slope_degrees"] < 30.0
    assert runtime["collision"] is False

    metrics = review["matched_capture_metrics"]
    for view in ("guide_seat", "river_eye"):
        result = metrics[view]
        assert (
            result["green_dominant_fraction_after"]
            > result["green_dominant_fraction_before"]
        )
        assert result["edge_fraction_after"] > result["edge_fraction_before"]
        assert result["near_black_fraction_after"] > result["near_black_fraction_before"]
    assert len(review["remaining_photoreal_defects"]) >= 6
    assert len(review["required_external_acceptance_gates"]) == 6

    for artifact in review["retained_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file(), artifact["path"]
        assert _sha256(path) == artifact["sha256"], artifact["path"]
