from __future__ import annotations

import hashlib
import json
from pathlib import Path

from _capture_evidence import assert_capture_recorded


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
NATIVE_TEST_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Tests/"
    "RaftSimEditorPacuareTerrainTest.cpp"
)
AUTOMATION_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Commands/"
    "RaftSimEditorEnvironmentAutomation.cpp"
)
MATERIAL_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
    "RaftSimEditorPhotorealMaterials.cpp"
)
EVIDENCE_ROOT = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
)
MANIFEST = EVIDENCE_ROOT / "landscape_candidate_manifest_pacuare.json"
REVIEW = EVIDENCE_ROOT / "pacuare_scanned_fern_understory_v1_review.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_generator_replaces_most_pacuare_groundcover_with_reviewed_ferns() -> None:
    source = FOLIAGE_SOURCE.read_text(encoding="utf-8")

    for asset in (
        "SM_Fern02_fern_02_a",
        "SM_Fern02_fern_02_b",
        "SM_Fern02_fern_02_c",
        "SM_Fern02_fern_02_d",
    ):
        assert asset in source
    for token in (
        "PacuareScannedFernTargetInstanceCount = 3640",
        "PacuareScannedFernMinimumInstanceCount = 3300",
        "FamilyIndex % 10 < 7",
        "PacuareScannedFernPlacedCount >=",
        'TEXT("RaftSimPacuareScannedFernUnderstoryV1")',
        'TEXT("RaftSimRightsReviewedCC0UnderstoryAnalog")',
        'TEXT("RaftSimNoSpeciesOrEcologyAuthority")',
        'TEXT("RaftSimSourceLandscapeGrounded")',
        'TEXT("RaftSimOutsideProtectedSolverStrip")',
        'TEXT("RaftSimNonCollisionRenderSurface")',
        'TEXT("RaftSimPresentationOnlyNoHydraulicAuthority")',
    ):
        assert token in source


def test_runtime_contract_counts_scanned_ferns_inside_total_bank_cover() -> None:
    source = MAP_TEST_SOURCE.read_text(encoding="utf-8")

    for token in (
        "ScannedFernActorCount",
        "ScannedFernInstanceCount >= 3300",
        "OrganicShorelineGroundCoverInstanceCount >= 4700",
        "RaftSimPacuareScannedFernUnderstoryV1",
        "RaftSimRightsReviewedCC0UnderstoryAnalog",
        "ECollisionEnabled::NoCollision",
    ):
        assert token in source


def test_native_and_manifest_contracts_validate_four_scanned_assets() -> None:
    native_source = NATIVE_TEST_SOURCE.read_text(encoding="utf-8")
    automation_source = AUTOMATION_SOURCE.read_text(encoding="utf-8")
    material_source = MATERIAL_SOURCE.read_text(encoding="utf-8")

    assert "RaftSim.M9.FPacuareScannedFernUnderstory" in native_source
    assert "M_Fern02_Fronds" in native_source
    assert "FutaleufuTemperateForestSet_1K" in native_source
    assert "M_Fern02_Fronds.M_Fern02_Fronds" in material_source
    assert "PromoteReviewedScannedUnderstoryMaterials" in material_source
    assert "PromoteReviewedScannedUnderstoryMaterials" in FOLIAGE_SOURCE.read_text(
        encoding="utf-8"
    )
    assert "MATUSAGE_InstancedStaticMeshes" in native_source
    assert "MATUSAGE_Nanite" in native_source
    for token in (
        "landscape_dressing_pacuare_scanned_fern_status",
        "landscape_dressing_pacuare_scanned_fern_mesh_count",
        "landscape_dressing_pacuare_scanned_fern_target_instance_count",
        "landscape_dressing_pacuare_scanned_fern_instance_count",
        "no_pacuare_species_ecology_geography_collision_hydraulic_or_raft_force_authority",
    ):
        assert token in automation_source


def test_saved_manifest_records_scanned_fern_mix_and_runnable_map() -> None:
    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))["candidates"][0]

    assert candidate["river_id"] == "pacuare"
    assert candidate["map_package"] == "/Game/RaftSim/Maps/L_UpperHuacas"
    assert candidate["runnable_gameplay_status"] == (
        "reference_runnable_upper_huacas_live_cooked_water_player_raft_and_game_mode"
    )
    assert candidate["landscape_dressing_asset_count"] == 14
    assert candidate["landscape_dressing_external_review_asset_count"] == 10
    assert candidate["landscape_dressing_pacuare_scanned_fern_status"] == (
        "four_scanned_fern_meshes_nanite_and_material_validated_for_"
        "source_grounded_near_bank_review_candidate"
    )
    assert candidate["landscape_dressing_pacuare_scanned_fern_mesh_count"] == 4
    assert (
        candidate["landscape_dressing_pacuare_scanned_fern_target_instance_count"]
        == 3640
    )
    assert candidate["landscape_dressing_pacuare_scanned_fern_instance_count"] == 3640
    assert candidate["landscape_dressing_foliage_instance_count"] == 18400
    assert candidate["landscape_dressing_canopy_tree_instance_count"] == 5993
    assert candidate["landscape_dressing_understory_instance_count"] == 12407


def test_review_is_hash_locked_fail_closed_and_preserves_authority() -> None:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == (
        "raftsim.environment.pacuare_scanned_fern_understory_review.v1"
    )
    assert review["passed"] is False
    assert review["runtime_artifacts_promoted"] is True
    assert review["photoreal_production_promoted"] is False
    assert review["decision"]["technical_candidate_passed"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["implementation"]["scanned_fern_instances"] == 3640
    assert review["implementation"]["procedural_groundcover_instances"] == 1560
    assert review["implementation"]["total_groundcover_instances"] == 5200
    for key in (
        "terrain_geometry_changed",
        "terrain_collision_changed",
        "water_geometry_changed",
        "cooked_fields_changed",
        "hydraulics_changed",
        "bathymetry_changed",
        "raft_forces_changed",
    ):
        assert review["decision"][key] is False
    assert len(review["remaining_photoreal_defects"]) >= 8
    assert len(review["required_external_acceptance_gates"]) == 6
    for artifact in review["retained_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        if artifact.get("hash_locked", True):
            assert _sha256(path) == artifact["sha256"]
        if path.suffix == ".png":
            assert_capture_recorded(path)
