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
AUTOMATION_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Commands/"
    "RaftSimEditorEnvironmentAutomation.cpp"
)
NATIVE_TEST_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Tests/"
    "RaftSimEditorPacuareTerrainTest.cpp"
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
MANIFEST = EVIDENCE_ROOT / "landscape_candidate_manifest_pacuare.json"
REVIEW = EVIDENCE_ROOT / "pacuare_forest_floor_structure_v1_review.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_automation_report(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def test_generator_builds_four_solid_deterministic_forest_floor_forms() -> None:
    source = FOLIAGE_SOURCE.read_text(encoding="utf-8")

    for token in (
        "PacuareForestFloorLeafLitterTargetInstanceCount = 2600",
        "PacuareForestFloorLeafLitterMinimumInstanceCount = 2350",
        "PacuareForestFloorWoodyTargetInstanceCount = 700",
        "PacuareForestFloorWoodyMinimumInstanceCount = 620",
        "PacuareForestFloorDeterministicSeed = 18437",
        "CandidateIndex < 32",
        "SM_RaftSim_Pacuare_FoldedLeafLitter_A_ForestFloorV1",
        "SM_RaftSim_Pacuare_FoldedLeafLitter_B_ForestFloorV1",
        "SM_RaftSim_Pacuare_ButtressRoot_A_ForestFloorV1",
        "SM_RaftSim_Pacuare_Deadwood_A_ForestFloorV1",
        'TEXT("RaftSimPacuareForestFloorV1")',
        'TEXT("RaftSimSourceLandscapeGrounded")',
        'TEXT("RaftSimOutsideProtectedSolverStrip")',
        'TEXT("RaftSimNonCollisionRenderSurface")',
        'TEXT("RaftSimNoSpeciesOrEcologyAuthority")',
        'TEXT("RaftSimNoTerrainCollisionOrWaterAuthority")',
    ):
        assert token in source


def test_native_and_map_load_gates_cover_assets_counts_and_authority() -> None:
    native_source = NATIVE_TEST_SOURCE.read_text(encoding="utf-8")
    map_source = MAP_TEST_SOURCE.read_text(encoding="utf-8")

    assert "RaftSim.M9.FPacuareForestFloorStructure" in native_source
    for threshold in ("430", "810", "420", "790", "250", "240", "300"):
        assert threshold in native_source
    for token in (
        "ForestFloorActorCount",
        "ForestFloorLeafInstanceCount",
        "ForestFloorRootInstanceCount",
        "ForestFloorDeadwoodInstanceCount",
        "RaftSimPacuareForestFloorV1",
        "RaftSimNoTerrainCollisionOrWaterAuthority",
        "ECollisionEnabled::NoCollision",
    ):
        assert token in map_source


def test_automation_and_saved_manifest_record_fail_closed_placement() -> None:
    automation_source = AUTOMATION_SOURCE.read_text(encoding="utf-8")
    for token in (
        "landscape_dressing_pacuare_forest_floor_status",
        "landscape_dressing_pacuare_forest_floor_authority",
        "landscape_dressing_pacuare_forest_floor_mesh_count",
        "landscape_dressing_pacuare_forest_floor_deterministic_seed",
        "landscape_dressing_pacuare_forest_floor_instance_count",
        "landscape_dressing_pacuare_forest_floor_placement_contract",
        "no_species_ecology_terrain_collision_water_hydraulic_bathymetric_"
        "or_raft_force_authority",
    ):
        assert token in automation_source

    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))["candidates"][0]
    assert candidate["river_id"] == "pacuare"
    assert candidate["map_package"] == "/Game/RaftSim/Maps/L_UpperHuacas"
    assert candidate["runnable_gameplay_status"] == (
        "reference_runnable_upper_huacas_live_cooked_water_player_raft_and_game_mode"
    )
    assert candidate["landscape_dressing_asset_count"] == 18
    assert candidate["landscape_dressing_pacuare_forest_floor_mesh_count"] == 4
    assert candidate["landscape_dressing_pacuare_forest_floor_deterministic_seed"] == 18437
    assert candidate["landscape_dressing_pacuare_forest_floor_target_instance_count"] == 3300
    assert candidate["landscape_dressing_pacuare_forest_floor_instance_count"] == 3300
    assert candidate["landscape_dressing_pacuare_forest_floor_rejected_placement_count"] == 0
    assert candidate["landscape_dressing_pacuare_forest_floor_minimum_centerline_distance_cm"] >= 1777.5
    assert candidate["landscape_dressing_pacuare_forest_floor_maximum_slope_degrees"] <= 36.0
    assert candidate["landscape_dressing_pacuare_forest_floor_forms"] == [
        "folded_leaf_litter_a",
        "folded_leaf_litter_b",
        "buttress_root_a",
        "deadwood_a",
    ]
    authority = candidate["landscape_dressing_pacuare_forest_floor_authority"]
    for exclusion in (
        "no_species_ecology",
        "terrain_collision",
        "water_hydraulic",
        "bathymetric",
        "raft_force_authority",
    ):
        assert exclusion in authority


def test_retained_native_and_all_river_reports_are_green() -> None:
    m9 = _read_automation_report(
        EVIDENCE_ROOT / "pacuare_forest_floor_structure_v1_m9_tests.json"
    )
    p4 = _read_automation_report(
        EVIDENCE_ROOT
        / "pacuare_forest_floor_structure_v1_p4_river_map_loads.json"
    )

    assert len(m9["tests"]) == 6
    assert {test["testDisplayName"] for test in m9["tests"]} == {
        "FPacuareForestFloorStructure",
        "FPacuareLiveTransmittingWater",
        "FPacuareOpaqueRainforestVegetation",
        "FPacuareOrganicRainforestTerrain",
        "FPacuareRainforestDefaultLitWater",
        "FPacuareScannedFernUnderstory",
    }
    assert len(p4["tests"]) == 6
    assert {test["testDisplayName"] for test in p4["tests"]} == {
        "L_Hance",
        "L_LavaCanyon",
        "L_Terminator",
        "L_Troublemaker",
        "L_UpperHuacas",
        "L_Zambezi",
    }
    for report in (m9, p4):
        assert report["failed"] == 0
        assert all(test["state"] == "Success" for test in report["tests"])
        assert all(test["errors"] == 0 for test in report["tests"])


def test_review_is_hash_locked_fail_closed_and_honest() -> None:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))

    assert review["schema"] == (
        "raftsim.environment.pacuare_forest_floor_structure_review.v1"
    )
    assert review["passed"] is False
    assert review["runtime_artifacts_promoted"] is True
    assert review["photoreal_production_promoted"] is False
    assert review["decision"]["reference_runnable"] is True
    assert review["decision"]["technical_candidate_passed"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["implementation"]["total_instances"] == 3300
    assert review["implementation"]["rejected_placements"] == 0
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
