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
REVIEW = EVIDENCE_ROOT / "chilko_futaleufu_temperate_bank_ecology_v4_review.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_v4_generator_has_real_morphology_and_dry_bank_bounds() -> None:
    source = FOLIAGE_SOURCE.read_text(encoding="utf-8")

    for token in (
        "TemperateNearBankEcologyTargetInstanceCount = 1800",
        "TemperateNearBankEcologyMinimumInstanceCount = 1600",
        "TemperateNearBankEcologySlopeCeilingDegrees = 38.0f",
        "SM_RaftSim_Temperate_BroadleafTree_B_OpaqueV1",
        "SM_RaftSim_Temperate_ConiferTree_B_OpaqueV1",
        "SM_RaftSim_Temperate_RiparianShrub_B_OpaqueV1",
        "SM_RaftSim_Temperate_GroundCover_B_OpaqueV1",
        "bSecondaryMorphology",
        "CandidateIndex < 64",
        "GetMinimumCenterlineDistanceCm(CandidatePoint)",
        "GetConditionedWaterWorldZ(CandidateLogicalX)",
        'TEXT("RaftSimTemperateBankEcologyV4")',
        'TEXT("RaftSimTemperateNearBankEcologyV4")',
        'TEXT("RaftSimOutsideProtectedSolverStrip")',
        'TEXT("RaftSimNoSpeciesOrEcologyAuthority")',
    ):
        assert token in source

    near_bank_start = source.index("int32 TemperateNearBankPlacedCount")
    assert "Landscape->Import" not in source[near_bank_start:]


def test_v4_runtime_map_contract_requires_eight_forms_and_near_bank_density() -> None:
    source = MAP_TEST_SOURCE.read_text(encoding="utf-8")

    assert 'TEXT("RaftSimTemperateBankEcologyV4")' in source
    assert 'TEXT("RaftSimTemperateMorphologyVariantFamily")' in source
    assert 'TEXT("RaftSimTemperateNearBankEcologyV4")' in source
    assert "OpaqueVegetationActorCount" in source
    assert "OpaqueVegetationActorCount," in source
    assert "NearBankEcologyActorCount" in source
    assert "NearBankEcologyInstanceCount >= 1600" in source
    assert "ECollisionEnabled::NoCollision" in source


def test_v4_saved_manifests_record_complete_bank_ecology() -> None:
    for manifest_name, river_id in (
        ("landscape_candidate_manifest_futaleufu_terminator.json", "futaleufu_terminator"),
        (
            "landscape_candidate_manifest_chilko_river_lava_canyon.json",
            "chilko_river_lava_canyon",
        ),
    ):
        candidate = json.loads(
            (EVIDENCE_ROOT / manifest_name).read_text(encoding="utf-8")
        )["candidates"][0]
        assert candidate["river_id"] == river_id
        assert candidate["landscape_dressing_converted_species_static_mesh_count"] == 8
        assert candidate["landscape_dressing_temperate_morphology_mesh_count"] == 8
        assert candidate["landscape_dressing_temperate_near_bank_status"] == (
            "source_grounded_dry_bank_grass_forb_shrub_ecology_v4_captured"
        )
        assert candidate["landscape_dressing_temperate_near_bank_target_instance_count"] == 1800
        assert candidate["landscape_dressing_temperate_near_bank_instance_count"] == 1800
        assert candidate["landscape_dressing_temperate_near_bank_rejected_placement_count"] == 0
        assert candidate["landscape_dressing_foliage_instance_count"] == 8000
        assert candidate["landscape_dressing_canopy_tree_instance_count"] == 4650
        assert candidate["landscape_dressing_understory_instance_count"] == 3350
        assert candidate["landscape_dressing_temperate_near_bank_maximum_slope_degrees"] <= 38.0
        assert candidate["landscape_dressing_temperate_near_bank_authority"] == (
            "presentation_only_procedural_source_gap_fill_no_species_survey_"
            "collision_hydraulic_or_raft_force_authority"
        )


def test_v4_review_is_hash_locked_and_fail_closed() -> None:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == "raftsim.environment.temperate_bank_ecology_review.v4"
    assert review["passed"] is False
    assert review["runtime_artifacts_promoted"] is True
    assert review["photoreal_production_promoted"] is False
    assert review["decision"]["reference_runnable"] is True
    assert review["decision"]["technical_candidate_passed"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["terrain_geometry_changed"] is False
    assert review["decision"]["terrain_collision_changed"] is False
    assert review["decision"]["water_geometry_changed"] is False
    assert review["decision"]["hydraulics_changed"] is False
    assert review["decision"]["bathymetry_changed"] is False
    assert review["decision"]["raft_forces_changed"] is False
    assert len(review["remaining_photoreal_defects"]) >= 7
    assert len(review["required_external_acceptance_gates"]) == 6

    for artifact in review["retained_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]
