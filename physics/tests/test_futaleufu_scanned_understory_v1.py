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
EVIDENCE_ROOT = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates"
)
MANIFEST = EVIDENCE_ROOT / "landscape_candidate_manifest_futaleufu_terminator.json"
REVIEW = EVIDENCE_ROOT / "futaleufu_scanned_understory_v1_review.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_scanned_understory_generator_is_bounded_to_small_near_bank_assets() -> None:
    source = FOLIAGE_SOURCE.read_text(encoding="utf-8")

    for asset in (
        "SM_FirSapling_fir_sapling_a",
        "SM_FirSapling_fir_sapling_b",
        "SM_FirSapling_fir_sapling_c",
        "SM_Fern02_fern_02_a",
        "SM_Fern02_fern_02_b",
        "SM_Fern02_fern_02_c",
        "SM_Fern02_fern_02_d",
    ):
        assert asset in source
    assert "SM_FirSaplingMedium" not in source
    for token in (
        "ValidateFutaleufuScannedUnderstoryMaterials",
        "PatchIndex % 5 != 0",
        "FutaleufuScannedUnderstoryPlacedCount >= 1200",
        'TEXT("RaftSimFutaleufuScannedNearBankUnderstoryV1")',
        'TEXT("RaftSimRightsReviewedCC0UnderstoryAnalog")',
        'TEXT("RaftSimSourceLandscapeGrounded")',
        'TEXT("RaftSimOutsideProtectedSolverStrip")',
        'TEXT("RaftSimNonCollisionRenderSurface")',
        'TEXT("RaftSimNoSpeciesOrEcologyAuthority")',
        'TEXT("RaftSimNoHydraulicAuthority")',
    ):
        assert token in source


def test_runtime_contract_requires_scanned_understory_without_canopy_promotion() -> None:
    source = MAP_TEST_SOURCE.read_text(encoding="utf-8")

    assert "ScannedUnderstoryActorCount" in source
    assert "ScannedUnderstoryInstanceCount >= 1200" in source
    assert "ScannedUnderstoryActorCount," in source
    assert "RaftSimRightsReviewedCC0UnderstoryAnalog" in source
    assert "RaftSimOpaqueVolumetricVegetation" in source
    assert "ECollisionEnabled::NoCollision" in source


def test_saved_manifest_records_mixed_understory_and_preserved_canopy() -> None:
    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))["candidates"][0]

    assert candidate["river_id"] == "futaleufu_terminator"
    assert candidate["landscape_dressing_asset_count"] == 21
    assert candidate["landscape_dressing_external_review_asset_count"] == 13
    assert candidate["landscape_dressing_futaleufu_scanned_understory_status"] == (
        "seven_small_fir_and_fern_meshes_nanite_and_material_validated_for_"
        "source_grounded_near_bank_review_candidate"
    )
    assert candidate["landscape_dressing_futaleufu_scanned_understory_mesh_count"] == 7
    assert (
        candidate["landscape_dressing_futaleufu_scanned_understory_instance_count"]
        == 1440
    )
    assert candidate["landscape_dressing_futaleufu_medium_fir_canopy_excluded"] is True
    assert candidate["landscape_dressing_futaleufu_project_owned_canopy_preserved"] is True
    assert candidate["landscape_dressing_temperate_near_bank_instance_count"] == 1800
    assert candidate["landscape_dressing_foliage_instance_count"] == 8000
    assert candidate["landscape_dressing_canopy_tree_instance_count"] == 4650
    assert candidate["landscape_dressing_understory_instance_count"] == 3350


def test_scanned_understory_review_is_hash_locked_and_fail_closed() -> None:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == "raftsim.environment.futaleufu_scanned_understory_review.v1"
    assert review["passed"] is False
    assert review["runtime_artifacts_promoted"] is True
    assert review["photoreal_production_promoted"] is False
    assert review["decision"]["technical_candidate_passed"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["medium_fir_canopy_promoted"] is False
    assert review["decision"]["project_owned_canopy_preserved"] is True
    for key in (
        "terrain_geometry_changed",
        "terrain_collision_changed",
        "water_geometry_changed",
        "hydraulics_changed",
        "bathymetry_changed",
        "raft_forces_changed",
    ):
        assert review["decision"][key] is False
    assert len(review["remaining_photoreal_defects"]) >= 5
    assert len(review["required_external_acceptance_gates"]) == 6
    for artifact in review["retained_artifacts"]:
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        if artifact.get("hash_locked", True):
            assert _sha256(path) == artifact["sha256"]
        if path.suffix == ".png":
            assert_capture_recorded(path)
