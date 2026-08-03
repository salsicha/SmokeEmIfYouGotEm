from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FOLIAGE_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/"
    "RaftSimEditorLandscapeFoliage.cpp"
)
MAP_TEST_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/"
    "RaftSimTroublemakerMapTest.cpp"
)
EVIDENCE_ROOT = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
)
MANIFEST = EVIDENCE_ROOT / "landscape_candidate_manifest_chilko_river_lava_canyon.json"
REVIEW = EVIDENCE_ROOT / "chilko_organic_shoreline_v1_review.json"
V2_REVIEW = EVIDENCE_ROOT / "chilko_nonrepeating_wet_bank_v2_review.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_generator_is_chilko_only_grounded_and_non_authoritative() -> None:
    source = FOLIAGE_SOURCE.read_text(encoding="utf-8")

    for token in (
        "ChilkoOrganicShorelineGravelTargetInstanceCount = 7200",
        "ChilkoOrganicShorelineGravelMinimumInstanceCount = 6800",
        "ChilkoOrganicShorelineGravelSlopeCeilingDegrees = 42.0f",
        "ChilkoOrganicShorelineGroundCoverTargetInstanceCount = 8400",
        "ChilkoOrganicShorelineGroundCoverMinimumInstanceCount = 7900",
        "ChilkoOrganicShorelineGroundCoverSlopeCeilingDegrees = 32.0f",
        "ActiveRiverHalfWidth * 1.03f",
        "CandidateIndex < 48",
        "GetMinimumCenterlineDistanceCm(CandidatePoint)",
        "GetConditionedWaterWorldZ(CandidateLogicalX)",
        "ChilkoOrganicShorelineStartStationCm = 250.0f",
        "ChilkoOrganicShorelineEndStationCm = 59750.0f",
        'TEXT("RaftSimChilkoOrganicShorelineV2")',
        'TEXT("RaftSimChilkoShorelineGravel")',
        'TEXT("RaftSimChilkoShorelineGroundCover")',
        'TEXT("RaftSimGenericRockAnalogNoLithologyAuthority")',
        'TEXT("RaftSimNoSpeciesOrEcologyAuthority")',
        'TEXT("RaftSimOutsideProtectedSolverStrip")',
        'TEXT("RaftSimPresentationOnlyNoHydraulicAuthority")',
    ):
        assert token in source

    start = source.index("int32 ChilkoShorelineGravelPlacedCount")
    assert "Landscape->Import" not in source[start:]


def test_runtime_map_contract_counts_and_disclaims_both_families() -> None:
    source = MAP_TEST_SOURCE.read_text(encoding="utf-8")

    assert 'TEXT("RaftSimChilkoOrganicShorelineV2")' in source
    assert "OrganicShorelineActorCount" in source
    assert "OrganicShorelineGravelActorCount" in source
    assert "OrganicShorelineGravelInstanceCount >= 6800" in source
    assert "OrganicShorelineGroundCoverActorCount" in source
    assert "OrganicShorelineGroundCoverInstanceCount >= 7900" in source
    assert 'TEXT("RaftSimGenericRockAnalogNoLithologyAuthority")' in source
    assert 'TEXT("RaftSimNoSpeciesOrEcologyAuthority")' in source
    assert "ECollisionEnabled::NoCollision" in source


def test_saved_chilko_manifest_records_complete_organic_shoreline() -> None:
    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))["candidates"][0]

    assert candidate["river_id"] == "chilko_river_lava_canyon"
    assert candidate["landscape_dressing_boulder_instance_count"] == 8820
    assert candidate["landscape_dressing_foliage_instance_count"] == 16400
    assert candidate["landscape_dressing_understory_instance_count"] == 11750
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_gravel_status"
    ] == (
        "source_grounded_rights_reviewed_cc0_six_variant_full_runnable_reach_"
        "organic_shoreline_gravel_v2_captured"
    )
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_gravel_target_instance_count"
    ] == 7200
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_gravel_instance_count"
    ] == 7200
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_gravel_rejected_placement_count"
    ] == 0
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_gravel_minimum_centerline_distance_cm"
    ] >= 1800.0 * 1.03 + 45.0
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_gravel_maximum_slope_degrees"
    ] <= 42.0
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_ground_cover_status"
    ] == "source_grounded_full_runnable_reach_short_meadow_ground_cover_v2_captured"
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_ground_cover_target_instance_count"
    ] == 8400
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_ground_cover_instance_count"
    ] == 8400
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_ground_cover_rejected_placement_count"
    ] == 0
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_ground_cover_minimum_centerline_distance_cm"
    ] >= 1800.0 * 1.03 + 85.0
    assert candidate[
        "landscape_dressing_chilko_organic_shoreline_ground_cover_maximum_slope_degrees"
    ] <= 32.0


def test_review_retains_measured_breakup_but_rejects_photoreal_acceptance() -> None:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == "raftsim.environment.chilko_organic_shoreline_review.v1"
    assert review["passed"] is False
    assert review["decision"]["reference_runnable"] is True
    assert review["decision"]["organic_shoreline_v1_retained"] is True
    assert review["decision"]["initial_far_bank_small_scale_tuning_rejected"] is True
    assert review["decision"]["technical_candidate_passed"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["terrain_geometry_changed"] is False
    assert review["decision"]["terrain_collision_changed"] is False
    assert review["decision"]["water_geometry_changed"] is False
    assert review["decision"]["hydraulics_changed"] is False
    assert review["decision"]["bathymetry_changed"] is False
    assert review["decision"]["raft_forces_changed"] is False
    assert len(review["remaining_photoreal_defects"]) >= 8
    assert len(review["required_external_acceptance_gates"]) == 6

    comparison = review["visual_comparison"]
    baseline = comparison["baseline_transmitting_water_v2"]
    retained = comparison["retained_organic_shoreline_v1"]
    assert retained["bank_green_dominant_fraction"] > baseline[
        "bank_green_dominant_fraction"
    ] * 1.5
    assert retained["bank_edge_fraction"] > baseline["bank_edge_fraction"] * 1.6
    assert retained["bank_mean_edge_magnitude"] > baseline[
        "bank_mean_edge_magnitude"
    ] * 1.4

    capture = REPO_ROOT / retained["path"]
    assert capture.is_file()
    assert _sha256(capture) == retained["sha256"]


def test_v2_review_locks_full_reach_correction_and_stays_fail_closed() -> None:
    review = json.loads(V2_REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == (
        "raftsim.environment.chilko_nonrepeating_wet_bank_review.v2"
    )
    assert review["status"] == (
        "technical_candidate_retained_photoreal_and_external_review_open"
    )
    assert review["passed"] is False
    assert review["decision"]["reference_runnable"] is True
    assert review["decision"]["technical_candidate_passed"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["organic_shoreline_v1_full_route_claim_superseded"] is True
    assert review["decision"]["v1_placement_end_station_m"] == 253.0
    assert review["decision"]["v2_placement_station_range_m"] == [2.5, 597.5]
    assert review["implementation"]["material"]["world_position_offset_connected"] is False
    assert review["implementation"]["full_reach_shoreline"][
        "gravel_placed_instance_count"
    ] == 7200
    assert review["implementation"]["full_reach_shoreline"][
        "ground_cover_placed_instance_count"
    ] == 8400
    assert len(review["remaining_photoreal_defects"]) >= 8
    assert len(review["required_external_acceptance_gates"]) == 6
    assert "does not claim increased global edge density" in review[
        "matched_visual_check"
    ]["verdict"]

    for artifact in review["retained_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]
