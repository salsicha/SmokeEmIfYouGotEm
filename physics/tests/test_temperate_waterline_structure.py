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
REVIEW = EVIDENCE_ROOT / "chilko_futaleufu_temperate_waterline_structure_v1_review.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_temperate_waterline_generator_is_bounded_and_non_authoritative() -> None:
    source = FOLIAGE_SOURCE.read_text(encoding="utf-8")

    for token in (
        "TemperateWaterlineStructureTargetInstanceCount = 1440",
        "TemperateWaterlineStructureMinimumInstanceCount = 1250",
        "TemperateWaterlineStructureSlopeCeilingDegrees = 55.0f",
        "CandidateIndex < 72",
        "VisibleRiverHalfWidth + 60.0f",
        "GetMinimumCenterlineDistanceCm(CandidatePoint)",
        "GetLandscapeHeight(BestPoint.X, BestPoint.Y)",
        'TEXT("RaftSimTemperateWaterlineStructureV1")',
        'TEXT("RaftSimProceduralSourceGapFill")',
        'TEXT("RaftSimGenericRockAnalogNoLithologyAuthority")',
        'TEXT("RaftSimOutsideProtectedSolverStrip")',
        'TEXT("RaftSimNonCollisionRenderSurface")',
        'TEXT("RaftSimPresentationOnlyNoHydraulicAuthority")',
    ):
        assert token in source

    assert "bSouthFork || bZambezi || bFutaleufu || bChilko" in source
    assert "Landscape->Import" not in source[source.index("int32 TemperateWaterlinePlacedCount") :]


def test_runtime_map_contract_counts_and_disclaims_waterline_structure() -> None:
    source = MAP_TEST_SOURCE.read_text(encoding="utf-8")

    assert 'TEXT("RaftSimTemperateWaterlineStructureV1")' in source
    assert "WaterlineStructureActorCount" in source
    assert "WaterlineStructureInstanceCount >= 1250" in source
    assert 'TEXT("RaftSimOutsideProtectedSolverStrip")' in source
    assert 'TEXT("RaftSimPresentationOnlyNoHydraulicAuthority")' in source
    assert "ECollisionEnabled::NoCollision" in source


def test_saved_temperate_maps_record_dense_full_route_structure() -> None:
    expected = {
        "futaleufu_terminator": {
            "manifest": "landscape_candidate_manifest_futaleufu_terminator.json",
            "minimum_centerline_distance_cm": 2400.0 * 1.18 + 60.0,
            "boulder_instance_count": 1620,
        },
        "chilko_river_lava_canyon": {
            "manifest": "landscape_candidate_manifest_chilko_river_lava_canyon.json",
            "minimum_centerline_distance_cm": 1800.0 * 1.20 + 60.0,
            "boulder_instance_count": 8820,
        },
    }

    for river_id, contract in expected.items():
        candidate = json.loads(
            (EVIDENCE_ROOT / contract["manifest"]).read_text(encoding="utf-8")
        )["candidates"][0]
        assert candidate["river_id"] == river_id
        assert candidate["landscape_dressing_external_review_rock_mesh_count"] == 6
        assert candidate["landscape_dressing_boulder_instance_count"] == contract[
            "boulder_instance_count"
        ]
        assert candidate["landscape_dressing_temperate_waterline_status"] == (
            "source_grounded_rights_reviewed_cc0_six_variant_"
            "organic_waterline_structure_v1_captured"
        )
        assert (
            candidate["landscape_dressing_temperate_waterline_target_instance_count"]
            == 1440
        )
        assert candidate["landscape_dressing_temperate_waterline_instance_count"] == 1440
        assert (
            candidate[
                "landscape_dressing_temperate_waterline_rejected_placement_count"
            ]
            == 0
        )
        assert candidate[
            "landscape_dressing_temperate_waterline_minimum_centerline_distance_cm"
        ] >= contract["minimum_centerline_distance_cm"]
        assert candidate[
            "landscape_dressing_temperate_waterline_maximum_slope_degrees"
        ] <= 55.0
        assert candidate["landscape_dressing_temperate_waterline_authority"] == (
            "presentation_only_procedural_source_gap_fill_no_lithology_collision_"
            "bathymetry_hydraulic_or_raft_force_authority"
        )


def test_temperate_waterline_review_is_a_complete_fail_closed_historical_record() -> None:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == (
        "raftsim.environment.temperate_waterline_structure_review.v1"
    )
    assert review["status"] == (
        "technical_candidate_retained_photoreal_and_external_review_open"
    )
    assert review["passed"] is False
    assert review["decision"]["reference_runnable"] is True
    assert review["decision"]["technical_candidate_passed"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["terrain_collision_changed"] is False
    assert review["decision"]["hydraulics_changed"] is False
    assert review["decision"]["bathymetry_changed"] is False
    assert review["decision"]["raft_forces_changed"] is False
    assert len(review["remaining_photoreal_defects"]) >= 8
    assert len(review["required_external_acceptance_gates"]) == 6

    for artifact in review["retained_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert len(artifact["sha256"]) == 64
        # Runnable maps, manifests, and fixed captures are intentionally
        # versioned in place by later retained milestones. V1 preserves their
        # hashes as historical evidence; only the immutable external source
        # manifest remains byte-locked by this superseded review.
        if path.name == "polyhaven_rock_moss_set_01_source_manifest.json":
            assert _sha256(path) == artifact["sha256"]
