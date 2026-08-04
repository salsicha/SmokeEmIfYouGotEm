import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.named_rapid_registry import build_editor_markers
from raftsim.zambezi_reference_map import (
    CATALOG_RELATIVE,
    COOKED_FIELDS_RELATIVE,
    COORDINATE_MAP_RELATIVE,
    HEIGHT_IMAGE_SHA256,
    OUTPUT_RELATIVE,
    RAPID_MAP_SHA256,
    REFERENCE_HEIGHTFIELD_SIZE,
    REFERENCE_MESH_SIZE,
    RUNTIME_BREAKING_DOWNSTREAM_FROUDE_MAX,
    RUNTIME_BREAKING_UPSTREAM_FROUDE_MIN,
    RUNTIME_COORDINATE_MAX_CORRIDOR_EDGE_STEP_M,
    RUNTIME_GRID_DX_M,
    RUNTIME_FIRST_RAPID_CONTROL_STATION_M,
    RUNTIME_LAUNCH_STATION_M,
    RUNTIME_MINIMUM_SAFE_LAUNCH_APRON_M,
    RUNTIME_PRESENTATION_SAMPLE_SPACING_M,
    SCENARIO_RELATIVE,
    build_runtime_coordinate_map,
    build_rapid_map_digitization,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNABLE_RELEASE_REVIEW = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_runnable_release_head_v13_review.json"
)
LIVE_WATER_V2_REVIEW = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_live_transmitting_water_v2_review.json"
)
RAPID_VFX_V1_REVIEW = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_solver_driven_rapid_vfx_v1_review.json"
)
REFINED_LIVE_SURFACE_V1_REVIEW = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_refined_live_surface_v1_review.json"
)
CONNECTED_PLUNGE_V1_REVIEW = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_connected_plunge_v1_review.json"
)
NONPERIODIC_LIVE_WAVE_V1_REVIEW = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_nonperiodic_live_wave_v1_review.json"
)
ORGANIC_UPPER_SCARP_V17_REVIEW = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_organic_upper_scarp_v17_review.json"
)
LAUNCH_OPTICAL_NATURALISM_V18_REVIEW = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_launch_optical_naturalism_v18_review.json"
)
STRATIFIED_ECOLOGY_V19_REVIEW = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_launch_stratified_ecology_v19_review.json"
)
RUNNABLE_ZAMBEZI_MAP_PATH = "unreal/Content/RaftSim/Maps/L_Zambezi.umap"
V17_SUPERSEDED_HISTORICAL_PATHS = {
    RUNNABLE_ZAMBEZI_MAP_PATH,
    (
        "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
        "zambezi_reference_scenario_map_validation.json"
    ),
    (
        "unreal/Content/RaftSim/Environment/ZambeziRun/Vegetation/Meshes/"
        "SM_RaftSim_Zambezi_RiparianTree_A_OpaqueV1.uasset"
    ),
    (
        "unreal/Content/RaftSim/Environment/ZambeziRun/Vegetation/Meshes/"
        "SM_RaftSim_Zambezi_UmbrellaTree_B_OpaqueV1.uasset"
    ),
    (
        "unreal/Content/RaftSim/Environment/ZambeziRun/Vegetation/Meshes/"
        "SM_RaftSim_Zambezi_ThornScrub_A_OpaqueV1.uasset"
    ),
    (
        "unreal/Content/RaftSim/Environment/ZambeziRun/Vegetation/Meshes/"
        "SM_RaftSim_Zambezi_SavannaGroundCover_A_OpaqueV1.uasset"
    ),
    (
        "unreal/Content/RaftSim/Environment/ZambeziRun/Vegetation/Meshes/"
        "SM_RaftSim_Zambezi_SavannaGroundCover_B_OpaqueV2.uasset"
    ),
    (
        "docs/environment-captures/photoreal_river_previews/"
        "landscape_candidates/zambezi_batoka_gorge_guide_seat_downstream.png"
    ),
    (
        "docs/environment-captures/photoreal_river_previews/"
        "landscape_candidates/zambezi_batoka_gorge_river_eye_downstream.png"
    ),
    (
        "unreal/Content/RaftSim/Environment/ZambeziRun/Water/Materials/"
        "MI_RaftSim_ZambeziBatoka_LiveVolumeWaterV2.uasset"
    ),
    (
        "unreal/Content/RaftSim/Materials/LandscapeCandidates/"
        "M_RaftSim_Zambezi_BatokaV12_WorldAlignedTerrainReview.uasset"
    ),
    (
        "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorEnvironmentCatalog.cpp"
    ),
    (
        "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorNearFieldAndLighting.cpp"
    ),
    (
        "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/"
        "RaftSimEditorLandscapeFoliage.cpp"
    ),
    (
        "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/"
        "RaftSimEditorLandscapeGeometry.cpp"
    ),
    (
        "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
        "RaftSimEditorBatokaMaterial.cpp"
    ),
    (
        "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
        "RaftSimEditorMaterialsBase.cpp"
    ),
    (
        "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
        "RaftSimEditorZambeziWaterMaterial.cpp"
    ),
    (
        "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Rivers/"
        "RaftSimEditorZambeziDirector.cpp"
    ),
    (
        "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Tests/"
        "RaftSimEditorZambeziWaterTest.cpp"
    ),
    "physics/tests/test_zambezi_reference_map.py",
}
LATER_WATER_MILESTONE_SUPERSEDED_PATHS = {
    "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp",
    "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterVfxActor.cpp",
    "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimWaterSurfaceActor.h",
    "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/"
    "RaftSimWaterSurfaceTest.cpp",
    "unreal/Plugins/RaftSim/Source/RaftSimAutomation/Private/Tests/"
    "RaftSimTroublemakerMapTest.cpp",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_historical_artifact_unchanged(relative: str, expected: str) -> None:
    # Earlier reviews retain hashes that were current when they were recorded.
    # V17 intentionally supersedes only the generated map, its audit, and this
    # evolving contract runner; replacement artifacts are independently locked
    # by the V17 review below.
    if (
        relative in V17_SUPERSEDED_HISTORICAL_PATHS
        or relative in LATER_WATER_MILESTONE_SUPERSEDED_PATHS
    ):
        return
    assert _sha256(REPO_ROOT / relative) == expected


def test_zambezi_release_head_runnable_review_is_hash_locked():
    review = _load(REPO_ROOT / RUNNABLE_RELEASE_REVIEW)
    assert review["schema"] == "raftsim.zambezi.runnable_release_head_review.v9"
    assert review["recorded_local_date"] == "2026-08-04"
    assert review["verified_base_commit"] == (
        "e6b15680a4fa9914dbfb8e3ee0e43918b359d5fa"
    )
    assert review["result"] == "pass"
    assert review["classification"] == "runnable_reference_free_run"
    assert review["production_fidelity_promoted"] is False
    assert review["verification_context"] == {
        "reason": (
            "Reaffirm the V19-regenerated Zambezi package as player-facing "
            "runnable river 6 after adding fail-closed elevation-stratified "
            "launch ecology and matched visual evidence."
        ),
        "map_runtime_package_changed_since_v12": True,
        "player_selector_metadata_changed_since_v12": True,
        "frontend_scenario_mapping_changed_since_v12": False,
        "supersedes_review": (
            "docs/environment-captures/photoreal_river_previews/"
            "landscape_candidates/zambezi_runnable_release_head_v12_review.json"
        ),
    }
    assert review["player_path"] == {
        "game_mode": "Free Run",
        "display_name": "Zambezi: Boiling Pot to Mukuni Beach",
        "river_id": "zambezi_batoka_gorge",
        "scenario_id": "zambezi_reference_run",
        "map_package": "/Game/RaftSim/Maps/L_Zambezi",
        "runnable_river_ordinal": 6,
        "runnable_river_count": 6,
        "tier": "reference_free_run",
        "availability": "free_run",
    }

    expected_hashes = {
        "unreal/Content/RaftSim/Maps/L_Zambezi.umap": (
            "dd2a48c94618ff17c98bfe14024fc0642437a1ec91576ef482d8a71221997ff9"
        ),
        (
            "docs/environment-captures/photoreal_river_previews/"
            "landscape_candidates/zambezi_reference_scenario_map_validation.json"
        ): (
            "a65fabfb996e8c50905343e40a392c97576b3d9b754e4f90812b06bc9ae0abb5"
        ),
        "unreal/Content/RaftSim/Environment/ZambeziRun/Water/Materials/"
        "MI_RaftSim_ZambeziBatoka_LiveVolumeWaterV2.uasset": (
            "3cae052632413b6fcb7163237f7882bced8bdfac74bc2ff0d2fce5e00e228d3b"
        ),
        "unreal/Content/RaftSim/UI/river_selection_catalog.json": (
            "fa2c5e80c9d266ef9c886a73817f4dcc059ee5754cf3643c1a8355d4c0651e69"
        ),
        "unreal/Content/RaftSim/UI/m6_game_progression_manifest.json": (
            "35d7cb4f7070f781333b001f9a5d1098c77415d32886b062c1d3c5a8584352c8"
        ),
        "physics/data/real_world/player_selection_model.json": (
            "aac98ef3b0346f7bb178ad65ce4b93b6c14920f464782a151df3b4d9a4486a27"
        ),
        "physics/data/real_world/zambezi_batoka_gorge/scenario_zambezi_run/"
        "scenario.json": (
            "ffa3d6b8f4f1c8d6c098c348af904676df694ab8e3875b8d9a45cee35ad9cab9"
        ),
        "unreal/Config/DefaultGame.ini": (
            "6893114b91d1647e8e7d0232e3a8970fd49e0b2fc80b263ba5df4014f62b7999"
        ),
        (
            "unreal/Plugins/RaftSim/Source/RaftSimUI/Private/"
            "RaftSimVerticalSliceFrontend.cpp"
        ): (
            "bedbc86c1edc9cb334d31daa585c860deb8ed6f612da4c0efa3a15beab4e8ce9"
        ),
        (
            "unreal/Source/SmokeEmIfYouGotEm/Tests/"
            "RaftSimM6GameProgressionTest.cpp"
        ): (
            "f30a40d2a2f63c180cf70d6ce20cee1c3e24a443ca5d069d11235f6d94130be2"
        ),
    }
    locked_hashes = {
        entry["path"]: entry["sha256"]
        for entry in review["hash_locked_runtime_contract"]
    }
    assert locked_hashes == expected_hashes
    for relative, expected in expected_hashes.items():
        assert _sha256(REPO_ROOT / relative) == expected

    assert review["registry_assertions"] == {
        "river_selection_catalog_portfolio_role": "runnable_river",
        "river_selection_catalog_runnable": True,
        "river_selection_catalog_tier": "reference_free_run",
        "river_selection_catalog_availability": "free_run",
        "progression_manifest_lists_zambezi": True,
        "progression_manifest_runnable": True,
        "progression_manifest_availability": "free_run",
        "both_runtime_manifests_link_this_review": True,
        "frontend_catalog_lists_zambezi": True,
        "shipping_cook_lists_zambezi": True,
        "versioned_map_present": True,
        "superseded_preview_is_player_path": False,
    }
    assert review["verification"]["editor_build"]["result"] == "success"
    assert review["verification"]["focused_python_contracts"]["passed"] == 26
    assert review["verification"]["career_catalog"]["result"] == "success"
    assert review["verification"]["progression_migration"]["result"] == "success"
    assert review["verification"]["zambezi_map_load"]["test"] == (
        "RaftSim.P4.RiverMapLoads.L_Zambezi"
    )
    assert review["verification"]["zambezi_map_load"]["performed"] == 1
    assert review["verification"]["zambezi_map_load"]["result"].startswith(
        "success"
    )
    assert review["verification"]["zambezi_map_load"]["zambezi_mapcheck_errors"] == 0
    assert review["verification"]["zambezi_map_load"]["zambezi_mapcheck_warnings"] == 0
    assert review["verification"]["live_zambezi_map"] == {
        "map_package": "/Game/RaftSim/Maps/L_Zambezi",
        "game_mode": "RaftSimVerticalSliceGameMode",
        "coordinate_map_points": 5908,
        "surface_vertices": 10465,
        "surface_triangles": 20480,
        "wet_vertices": 10465,
        "active_breaking_sites": 10,
        "rapid_foam_vertices": 631,
        "rapid_foam_visible": True,
        "volume_core_enabled": True,
        "volume_core_triangles": 16896,
        "standing_wave_absolute_max_m": 0.1046,
        "hydraulic_relief_absolute_max_m": 0.0896,
        "surface_smoothing_enabled": True,
        "surface_smoothing_strength": 0.62,
        "bank_blend_m": 7.5,
    }
    assert review["verification"]["saved_map_evidence"]["schema"] == (
        "raftsim.unreal.zambezi_reference_scenario_map_validation.v21"
    )
    assert review["verification"]["saved_map_evidence"]["vegetation_instances"] == 14316
    assert review["verification"]["saved_map_evidence"][
        "runnable_launch_ground_cover_instances"
    ] == 6512
    assert review["verification"]["saved_map_evidence"][
        "runnable_launch_woody_instances"
    ] == 772
    assert len(review["open_external_acceptance_gates"]) == 7

    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert RUNNABLE_RELEASE_REVIEW.as_posix() in readme
    assert "Zambezi, Batoka Gorge" in readme


def test_zambezi_v19_stratified_ecology_review_and_evidence_are_hash_locked():
    review = _load(REPO_ROOT / STRATIFIED_ECOLOGY_V19_REVIEW)
    assert review["schema"] == (
        "raftsim.environment.zambezi_launch_stratified_ecology_review.v19"
    )
    assert review["passed"] is False
    assert review["decision"]["technical_candidate_retained"] is True
    assert review["decision"]["six_strata_fail_closed"] is True
    assert review["decision"]["launch_camera_face_mosaic_passed"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["implementation"]["ground_cover"]["placed_instances"] == 6512
    assert review["implementation"]["ground_cover"]["stratum_counts"] == [
        978,
        1200,
        1200,
        734,
        1200,
        1200,
    ]
    assert review["implementation"]["woody"]["placed_instances"] == 772
    assert review["implementation"]["woody"]["stratum_counts"] == [
        139,
        122,
        140,
        112,
        108,
        151,
    ]
    assert review["implementation"]["woody"][
        "launch_camera_face_placed_instances"
    ] == 132
    for artifact in review["hash_locked_retained_artifacts"]:
        assert _sha256(REPO_ROOT / artifact["path"]) == artifact["sha256"]


def test_zambezi_live_water_v2_review_and_matched_evidence_are_hash_locked():
    review = _load(REPO_ROOT / LIVE_WATER_V2_REVIEW)
    assert review["schema"] == (
        "raftsim.environment.zambezi_live_transmitting_water_review.v2"
    )
    assert review["passed"] is False
    assert review["decision"]["technical_candidate_passed"] is True
    assert review["decision"]["rectangular_bank_seam_reduced"] is True
    assert review["decision"]["launch_glare_reduced"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["hydraulics_changed"] is False
    assert review["decision"]["wet_dry_mask_changed"] is False
    assert review["decision"]["bathymetry_changed"] is False
    assert review["decision"]["collision_or_raft_forces_changed"] is False

    comparison = review["fixed_camera_comparison"]
    assert comparison["retained_water_luminance_p95"] < (
        comparison["baseline_water_luminance_p95"]
    )
    assert comparison["retained_water_fraction_over_0_90"] < (
        comparison["baseline_water_fraction_over_0_90"] * 0.20
    )
    assert comparison["retained_water_fraction_over_0_95"] == 0.0
    assert comparison["retained_right_bank_vertical_edge_p99"] < (
        comparison["baseline_right_bank_vertical_edge_p99"]
    )
    assert comparison["retained_right_bank_strong_edge_fraction"] < (
        comparison["baseline_right_bank_strong_edge_fraction"]
    )

    locked_artifacts = {
        entry["path"]: entry["sha256"] for entry in review["retained_artifacts"]
    }
    for relative, expected in locked_artifacts.items():
        _assert_historical_artifact_unchanged(relative, expected)

    assert len(review["required_external_acceptance_gates"]) == 7
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert LIVE_WATER_V2_REVIEW.as_posix() in readme


def test_zambezi_solver_driven_rapid_vfx_review_is_hash_locked():
    review = _load(REPO_ROOT / RAPID_VFX_V1_REVIEW)
    assert review["schema"] == (
        "raftsim.environment.zambezi_solver_driven_rapid_vfx_review.v1"
    )
    assert review["passed"] is False
    assert review["decision"]["technical_candidate_retained"] is True
    assert review["decision"]["bounded_multi_site_coverage_passed"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["water_or_hydraulic_authority_changed"] is False
    assert review["implementation"]["active_site_budget_before"] == 2
    assert review["implementation"]["active_site_budget_after"] == 6
    assert review["implementation"]["preallocated_site_pool"] == 8
    assert review["runtime_evidence"]["active_breaking_sites"] == 8
    assert review["runtime_evidence"]["active_rapid_aerosol_emitters"] == 6
    assert review["runtime_evidence"]["active_rapid_roller_emitters"] == 6
    for key in ("baseline", "retained", "vfx_off_control"):
        artifact = review["visual_evidence"][key]
        assert _sha256(REPO_ROOT / artifact["path"]) == artifact["sha256"]
    for relative, expected in review["hash_locked_unchanged_authority"].items():
        _assert_historical_artifact_unchanged(relative, expected)
    for relative, expected in review["changed_source_hashes"].items():
        if relative in LATER_WATER_MILESTONE_SUPERSEDED_PATHS:
            continue
        assert _sha256(REPO_ROOT / relative) == expected
    assert len(review["required_external_acceptance_gates"]) == 7
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert RAPID_VFX_V1_REVIEW.as_posix() in readme


def test_zambezi_refined_live_surface_review_is_hash_locked_and_honest():
    review = _load(REPO_ROOT / REFINED_LIVE_SURFACE_V1_REVIEW)
    assert review["schema"] == (
        "raftsim.environment.zambezi_refined_live_surface_review.v1"
    )
    assert review["passed"] is False
    assert review["decision"]["technical_candidate_retained"] is True
    assert review["decision"]["all_six_river_maps_runnable"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["cooked_water_or_hydraulic_authority_changed"] is False
    assert review["implementation"]["base_analysis_spacing_m"] == 3.0
    assert review["implementation"]["resolved_render_spacing_m"] == 1.5
    assert review["implementation"]["analysis_stride_vertices"] == 2
    assert (
        review["implementation"]["bounded_theoretical_standing_wave_envelope_m"]
        <= 0.248
    )
    assert review["runtime_evidence"]["p4_all_six_river_maps"]["result"] == (
        "6/6 passed"
    )
    assert len(review["runtime_evidence"]["p4_all_six_river_maps"]["maps"]) == 6
    metrics = review["visual_evidence"]["descriptive_water_frame_metrics"]
    assert metrics["retained_highpass_absolute_mean"] > (
        metrics["baseline_highpass_absolute_mean"]
    )
    assert metrics["retained_edge_fraction_over_0_04"] > (
        metrics["baseline_edge_fraction_over_0_04"]
    )
    for key in ("baseline", "retained"):
        artifact = review["visual_evidence"][key]
        assert _sha256(REPO_ROOT / artifact["path"]) == artifact["sha256"]
    for relative, expected in review["hash_locked_unchanged_authority"].items():
        _assert_historical_artifact_unchanged(relative, expected)
    for relative, expected in review["changed_source_hashes"].items():
        if relative in LATER_WATER_MILESTONE_SUPERSEDED_PATHS:
            continue
        assert _sha256(REPO_ROOT / relative) == expected
    assert len(review["remaining_photoreal_defects"]) >= 5
    assert len(review["required_external_acceptance_gates"]) == 7
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert REFINED_LIVE_SURFACE_V1_REVIEW.as_posix() in readme


def test_zambezi_connected_plunge_review_is_hash_locked_and_honest():
    review = _load(REPO_ROOT / CONNECTED_PLUNGE_V1_REVIEW)
    assert review["schema"] == (
        "raftsim.environment.zambezi_connected_plunge_review.v1"
    )
    assert review["passed"] is False
    assert review["decision"]["technical_candidate_retained"] is True
    assert review["decision"]["all_six_river_maps_runnable"] is True
    assert review["decision"]["connected_production_water_contract_passed"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["map_or_content_package_changed"] is False
    assert review["decision"]["collision_buoyancy_d3_or_d4_changed"] is False
    assert review["implementation"]["selected_sites"] == (
        "three strongest accepted interior solver sites"
    )
    assert review["implementation"]["maximum_triangle_budget"] == 1512
    assert review["implementation"]["collision"] is False
    assert review["implementation"]["affects_water_sampling"] is False
    assert review["runtime_evidence"]["p4_all_river_map_loads"]["result"] == (
        "6/6 passed"
    )
    maps = review["runtime_evidence"]["p4_all_river_map_loads"]["maps"]
    assert len(maps) == 6
    assert all(
        0 < evidence["connected_curtain_triangles"] <= 1512
        for evidence in maps.values()
    )
    metrics = review["visual_evidence"]["fixed_camera"]["river_band_metrics"]
    assert metrics["retained_edge_fraction_over_0_04"] > (
        metrics["baseline_edge_fraction_over_0_04"]
    )
    assert metrics["retained_highpass_absolute_mean"] > (
        metrics["baseline_highpass_absolute_mean"]
    )
    for camera in ("fixed_camera", "solver_side_camera"):
        for key in ("baseline", "retained"):
            artifact = review["visual_evidence"][camera][key]
            assert _sha256(REPO_ROOT / artifact["path"]) == artifact["sha256"]
    for relative, expected in review["changed_source_hashes"].items():
        if relative in LATER_WATER_MILESTONE_SUPERSEDED_PATHS:
            continue
        assert _sha256(REPO_ROOT / relative) == expected
    assert len(review["rejected_iterations"]) == 4
    assert len(review["remaining_photoreal_defects"]) >= 5
    assert len(review["required_external_acceptance_gates"]) == 7
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert CONNECTED_PLUNGE_V1_REVIEW.as_posix() in readme


def test_zambezi_nonperiodic_live_wave_review_is_hash_locked_and_honest():
    review = _load(REPO_ROOT / NONPERIODIC_LIVE_WAVE_V1_REVIEW)
    assert review["schema"] == (
        "raftsim.environment.zambezi_nonperiodic_live_wave_review.v1"
    )
    assert review["passed"] is False
    assert review["decision"]["technical_candidate_retained"] is True
    assert review["decision"]["all_six_river_maps_runnable"] is True
    assert review["decision"]["former_dominant_periodic_band_removed"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert review["decision"]["map_or_content_package_changed"] is False
    assert review["decision"]["cooked_water_or_hydraulic_authority_changed"] is False
    assert review["decision"]["collision_buoyancy_d3_or_d4_changed"] is False
    implementation = review["implementation"]
    assert implementation["maximum_individual_active_band_m"] <= 0.065
    assert implementation["bounded_theoretical_standing_wave_envelope_m"] <= 0.168
    assert implementation["affects_water_sampling"] is False
    assert implementation["affects_collision"] is False
    assert implementation["affects_buoyancy_or_forces"] is False
    maps = review["runtime_evidence"]["p4_all_river_map_loads"]["maps"]
    assert review["runtime_evidence"]["p4_all_river_map_loads"]["result"] == (
        "6/6 passed"
    )
    assert len(maps) == 6
    assert all(
        evidence["standing_wave_abs_max_m"] <= 0.168 for evidence in maps.values()
    )
    camera = review["visual_evidence"]["fixed_camera"]
    assert camera["retained"]["standing_wave_abs_max_m"] < (
        camera["baseline"]["standing_wave_abs_max_m"]
    )
    assert camera["comparison"]["standing_wave_maximum_reduction_fraction"] > 0.5
    for key in ("baseline", "retained"):
        artifact = camera[key]
        assert _sha256(REPO_ROOT / artifact["path"]) == artifact["sha256"]
    assert review["map_integrity"]["path"] == RUNNABLE_ZAMBEZI_MAP_PATH
    assert review["map_integrity"]["sha256"] == (
        "28613a7b823f2fe90f35cd1ccb2ec2f9207fb5fb39bf0cc85ddb9e521e1db599"
    )
    for relative, expected in review["changed_source_hashes"].items():
        _assert_historical_artifact_unchanged(relative, expected)
    assert len(review["remaining_photoreal_defects"]) >= 6
    assert len(review["required_external_acceptance_gates"]) == 7
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert NONPERIODIC_LIVE_WAVE_V1_REVIEW.as_posix() in readme


def test_zambezi_organic_upper_scarp_v17_review_is_hash_locked_and_honest():
    review = _load(REPO_ROOT / ORGANIC_UPPER_SCARP_V17_REVIEW)
    assert review["schema"] == (
        "raftsim.environment.zambezi_organic_upper_scarp_review.v17"
    )
    assert review["passed"] is False
    assert review["decision"]["technical_candidate_retained"] is True
    assert review["decision"]["height_aware_upper_dry_scarp_infill_passed"] is True
    assert review["decision"]["wet_bank_protection_passed"] is True
    assert review["decision"]["launch_cover_distribution_improved"] is True
    assert review["decision"]["rejected_talus_shadow_wedge_removed"] is True
    assert review["decision"]["photoreal_acceptance_passed"] is False
    assert (
        review["decision"]["source_landscape_collision_or_height_authority_changed"]
        is False
    )
    assert (
        review["decision"]["water_geometry_wet_dry_mask_or_solver_state_changed"]
        is False
    )
    assert review["decision"]["raft_collision_buoyancy_or_forces_changed"] is False
    generated = review["generated_map_evidence"]
    assert generated["upper_cliff_modified_inside_horizontal_radius_vertex_count"] > 0
    assert (
        generated[
            "minimum_upper_cliff_modified_inside_radius_height_above_local_water_m"
        ]
        >= 6.0
    )
    assert generated["map_check_errors"] == 0
    assert generated["map_check_warnings"] == 0
    matched = review["matched_visual_evidence"]
    for key in ("baseline", "retained"):
        artifact = matched[key]
        assert _sha256(REPO_ROOT / artifact["path"]) == artifact["sha256"]
    rejected = review["rejected_bracket"]
    assert _sha256(REPO_ROOT / rejected["path"]) == rejected["sha256"]
    assert rejected["pixels_below_0_18_luminance"] == {
        "baseline": 0,
        "rejected": 2016,
        "retained": 0,
    }
    for artifact in review["hash_locked_retained_artifacts"]:
        if artifact["path"] not in V17_SUPERSEDED_HISTORICAL_PATHS:
            assert _sha256(REPO_ROOT / artifact["path"]) == artifact["sha256"]
    assert review["validation"] == {
        "editor_build": "pass",
        "map_generation": "pass",
        "saved_map_audit": (
            "pass_25_markers_1_raft_1_runtime_water_4_conditioned_visual_tiles_"
            "12843_opaque_vegetation_instances"
        ),
        "python_zambezi_contracts": "13/13_passed",
        "focused_native_environment_tests": (
            "RaftSim.P2.WaterSurfaceRenders_1/1_passed"
        ),
        "all_six_river_map_loads": "RaftSim.P4.RiverMapLoads_6/6_passed",
    }
    assert len(review["external_gates_remaining"]) == 7


def test_zambezi_launch_optical_naturalism_v18_review_is_hash_locked_and_honest():
    review = _load(REPO_ROOT / LAUNCH_OPTICAL_NATURALISM_V18_REVIEW)
    assert review["schema"] == (
        "raftsim.environment.zambezi_launch_optical_naturalism_review.v18"
    )
    assert review["passed"] is False
    assert review["decision"] == {
        "technical_candidate_retained": True,
        "launch_water_clipping_reduced": True,
        "sun_facing_scarp_energy_reduced": True,
        "lower_energy_launch_cover_passed": True,
        "photoreal_acceptance_passed": False,
        "terrain_collision_or_height_authority_changed": False,
        "water_geometry_wet_dry_mask_or_solver_state_changed": False,
        "raft_collision_buoyancy_or_forces_changed": False,
    }
    evidence = review["matched_visual_evidence"]
    for key in ("baseline", "retained"):
        artifact = evidence[key]
        assert _sha256(REPO_ROOT / artifact["path"]) == artifact["sha256"]
    metrics = evidence["descriptive_luminance_metrics"]
    assert metrics["retained"]["water_p95"] < metrics["baseline"]["water_p95"]
    assert metrics["retained"]["water_pixels_above_0_90_fraction"] < (
        metrics["baseline"]["water_pixels_above_0_90_fraction"] * 0.10
    )
    assert metrics["retained"]["left_water_pixels_above_0_90_fraction"] < (
        metrics["baseline"]["left_water_pixels_above_0_90_fraction"] * 0.10
    )
    assert metrics["retained"]["scarp_p95"] < metrics["baseline"]["scarp_p95"]
    assert review["generated_map_evidence"]["launch_ground_cover"] == {
        "target_instances": 7200,
        "placed_instances": 7200,
        "rejected_instances": 0,
        "maximum_selected_slope_degrees": 41.98,
    }
    for artifact in review["hash_locked_retained_artifacts"]:
        _assert_historical_artifact_unchanged(
            artifact["path"], artifact["sha256"]
        )
    assert review["validation"]["saved_map_audit"] == (
        "pass_25_markers_1_raft_1_runtime_water_4_conditioned_visual_tiles_"
        "14843_opaque_vegetation_instances"
    )
    assert len(review["external_gates_remaining"]) == 7
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert LAUNCH_OPTICAL_NATURALISM_V18_REVIEW.as_posix() in readme


def test_supplied_reference_sources_and_digitized_rapid_order_are_locked():
    assert _sha256(REPO_ROOT / "zambezi_batoka_heightmap.png") == HEIGHT_IMAGE_SHA256
    assert _sha256(REPO_ROOT / "victoria-falls-rapids-map.pdf") == RAPID_MAP_SHA256
    digitization = build_rapid_map_digitization(REPO_ROOT)
    assert digitization["rapid_count"] == 25
    assert [rapid["rapid_number"] for rapid in digitization["rapids"]] == [
        str(number) for number in range(1, 26)
    ]
    assert digitization["rapids"][0]["pdf_label"] == "The Wall"
    assert digitization["rapids"][-1]["pdf_label"] == "Rapid 25"
    assert digitization["rapids"][0]["station_m"] == 0.0
    assert digitization["rapids"][-1]["station_m"] == 27358.848
    increments = np.diff([rapid["station_m"] for rapid in digitization["rapids"]])
    assert increments.min() > 0.0
    assert increments.max() / increments.min() > 4.0
    assert all(
        not rapid["production_authoritative"] for rapid in digitization["rapids"]
    )


def test_committed_reference_bundle_is_self_consistent_and_not_physics_authority():
    root = REPO_ROOT / OUTPUT_RELATIVE
    manifest = _load(root / "source_and_conversion_manifest.json")
    assert manifest["production_promoted"] is False
    assert manifest["terrain_authority"]["policy"].startswith("Copernicus DEM remains")
    assert manifest["height_conversion"]["overlay_rejected_fraction"] > 0.1
    assert manifest["height_conversion"]["overlay_rejected_fraction"] < 0.4

    artifacts = manifest["artifacts"]
    for artifact in artifacts.values():
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]

    heightfield_path = REPO_ROOT / artifacts["heightfield_16bit"]["path"]
    with Image.open(heightfield_path) as heightfield:
        assert heightfield.size == REFERENCE_HEIGHTFIELD_SIZE
        values = np.asarray(heightfield)
    assert values.dtype in (np.dtype("uint16"), np.dtype("int32"))
    assert int(values.max()) - int(values.min()) > 50000

    mesh = artifacts["morphology_mesh"]
    assert mesh["grid_size"] == list(REFERENCE_MESH_SIZE)
    assert mesh["vertex_count"] == REFERENCE_MESH_SIZE[0] * REFERENCE_MESH_SIZE[1]
    assert mesh["triangle_count"] == (
        (REFERENCE_MESH_SIZE[0] - 1) * (REFERENCE_MESH_SIZE[1] - 1) * 2
    )
    assert mesh["physics_authority"] is False
    assert mesh["collision_authority"] is False


def test_zambezi_scenario_and_named_rapid_markers_use_pdf_relative_stationing():
    scenario = _load(REPO_ROOT / SCENARIO_RELATIVE)
    assert scenario["rapid_count"] == 25
    assert scenario["production_promoted"] is False
    assert scenario["gameplay"]["runnable"] is True
    assert scenario["gameplay"]["portfolio_role"] == "runnable_river"
    assert scenario["gameplay"]["runnable_tier"] == "reference_free_run"
    assert scenario["gameplay"]["runtime_coordinate_map"] == (
        COORDINATE_MAP_RELATIVE.as_posix()
    )
    assert scenario["gameplay"]["runtime_cooked_fields"] == (
        COOKED_FIELDS_RELATIVE.as_posix()
    )
    assert scenario["rapids"][8]["mandatory_commercial_portage"] is True
    assert (
        sum(rapid["mandatory_commercial_portage"] for rapid in scenario["rapids"]) == 1
    )
    assert scenario["route_variants"][0]["start_rapid"] == "1"
    assert scenario["route_variants"][0]["end_rapid"] == "25"
    assert {source["source_id"] for source in scenario["route_evidence"]} == {
        "zambezi_whitewater_guidebook",
        "zambezi_shearwater_operator_guide",
        "zambezi_victoria_falls_guide",
    }
    assert (
        scenario["route_variants"][1]["source_id"]
        == "zambezi_shearwater_operator_guide"
    )
    assert scenario["route_variants"][2]["source_id"] == "zambezi_victoria_falls_guide"
    assert len(scenario["acceptance_gates"]) >= 5

    player_catalog = _load(
        REPO_ROOT / "unreal/Content/RaftSim/UI/river_selection_catalog.json"
    )
    assert player_catalog["source_model"] == (
        "physics/data/real_world/player_selection_model.json"
    )
    player_entry = next(
        river
        for river in player_catalog["sections"]
        if river["river_id"] == "zambezi_batoka_gorge"
    )
    assert player_entry["frontend_scenario_id"] == "zambezi_reference_run"
    assert player_entry["portfolio_role"] == "runnable_river"
    assert player_entry["runnable"] is True
    assert player_entry["runnable_tier"] == "reference_free_run"
    assert player_entry["availability"] == "free_run"
    assert player_entry["runnable_release_review"] == (
        RUNNABLE_RELEASE_REVIEW.as_posix()
    )
    runtime_acceptance = player_entry["runtime_acceptance"]
    assert runtime_acceptance["result"] == "pass"
    assert runtime_acceptance["safe_launch_apron"] == (
        "raftsim.zambezi.safe_launch_apron.v1"
    )
    assert runtime_acceptance["initial_settle_upright"] is True
    assert runtime_acceptance["all_forward_upright"] is True
    assert runtime_acceptance["attached_crew_count"] == 5
    assert runtime_acceptance["swimmer_count"] == 0

    source_model = _load(REPO_ROOT / player_catalog["source_model"])
    source_entry = next(
        river
        for region in source_model["regions"]
        for river in region["rivers"]
        if river["river_id"] == "zambezi_batoka_gorge"
    )
    assert source_entry["portfolio_role"] == "runnable_river"
    assert source_entry["runnable"] is True
    assert source_entry["runnable_tier"] == "reference_free_run"
    source_section = source_entry["sections"][0]
    assert source_section["scenario_id"] == "zambezi_reference_run"
    assert source_section["map_package"] == player_entry["map_package"]
    assert source_section["flow_bands"][0]["runnable"] is True

    catalog = _load(REPO_ROOT / CATALOG_RELATIVE)
    generated = build_editor_markers(catalog, REPO_ROOT)
    zambezi = next(
        river
        for river in generated["rivers"]
        if river["river_id"] == "zambezi_batoka_gorge"
    )
    assert len(zambezi["markers"]) == 25
    assert all(
        marker["stationing"]["station_kind"]
        == "stylized_map_relative_spacing_scaled_to_published_run_length"
        for marker in zambezi["markers"]
    )
    assert [marker["stationing"]["station_m"] for marker in zambezi["markers"]] == [
        rapid["station_m"] for rapid in scenario["rapids"]
    ]


def test_zambezi_runtime_coordinate_map_and_procedural_water_are_runnable():
    scenario = _load(REPO_ROOT / SCENARIO_RELATIVE)
    coordinate_map = _load(REPO_ROOT / COORDINATE_MAP_RELATIVE)
    assert coordinate_map == build_runtime_coordinate_map(REPO_ROOT)
    assert coordinate_map["schema"] == "raftsim.curved_river_coordinate_map.v1"
    assert coordinate_map["station_domain_m"][0] == 0.0
    assert 29900.0 <= coordinate_map["station_domain_m"][1] <= 30100.0
    assert len(coordinate_map["points"]) > 5000
    assert coordinate_map["maximum_runtime_corridor_edge_step_m"] <= (
        RUNTIME_COORDINATE_MAX_CORRIDOR_EDGE_STEP_M
    )

    cooked_root = REPO_ROOT / COOKED_FIELDS_RELATIVE
    manifest = _load(cooked_root / "manifest.json")
    assert manifest["schema"] == "raftsim.cooked_flow_fields.v1"
    assert manifest["production_promoted"] is False
    assert manifest["bands"][0]["band_id"] == "normal_big_water"
    assert manifest["bands"][0]["convergence"]["converged"] is False
    assert manifest["generator"].endswith("feature_tagged_hydraulic_seed.v3")
    assert manifest["grid"]["dx_m"] == RUNTIME_GRID_DX_M == 5.0
    assert manifest["procedural_infill"]["authority"].startswith(
        "gameplay_reference_only"
    )
    arrays = manifest["bands"][0]["arrays"]
    loaded = {}
    for name, metadata in arrays.items():
        path = cooked_root / metadata["file"]
        assert _sha256(path) == metadata["sha256"]
        loaded[name] = np.load(path, allow_pickle=False)
        assert list(loaded[name].shape) == metadata["shape"]
    assert loaded["wet_mask"].dtype == np.uint8
    assert loaded["wet_mask"].mean() > 0.4
    assert np.isfinite(loaded["bed"]).all()
    assert np.isfinite(loaded["h"]).all()
    assert float(loaded["h"].max()) > 3.0
    assert float(loaded["u"].max()) > 3.0
    assert float(loaded["h"].max()) < 5.0
    assert float(np.hypot(loaded["u"], loaded["v"]).max()) < 8.0

    contract = manifest["procedural_infill"]["hydraulic_transition_contract"]
    assert contract["schema"] == ("raftsim.zambezi.procedural_hydraulic_transitions.v1")
    assert contract["runtime_station_resolution_m"] == 5.0
    assert contract["presentation_sample_spacing_m"] == (
        RUNTIME_PRESENTATION_SAMPLE_SPACING_M
    )
    assert contract["upstream_froude_minimum"] == (RUNTIME_BREAKING_UPSTREAM_FROUDE_MIN)
    assert contract["tailwater_froude_maximum"] == (
        RUNTIME_BREAKING_DOWNSTREAM_FROUDE_MAX
    )
    assert contract["rapid_transition_count"] == 25
    assert contract["all_rapid_transitions_detected"] is True
    assert [row["rapid_number"] for row in contract["transitions"]] == [
        str(number) for number in range(1, 26)
    ]
    assert all(not row["production_authoritative"] for row in contract["transitions"])
    assert all(
        row["upstream_froude"] >= RUNTIME_BREAKING_UPSTREAM_FROUDE_MIN
        and row["tailwater_froude"] <= RUNTIME_BREAKING_DOWNSTREAM_FROUDE_MAX
        for row in contract["transitions"]
    )
    rapid_9 = contract["transitions"][8]
    assert rapid_9["mandatory_commercial_portage"] is True
    assert contract["rapid_9_policy"].startswith("hazard_visualization_only")

    launch_apron = manifest["procedural_infill"]["safe_launch_apron"]
    assert launch_apron["schema"] == "raftsim.zambezi.safe_launch_apron.v1"
    assert launch_apron["raft_spawn_station_m"] == RUNTIME_LAUNCH_STATION_M
    assert launch_apron["first_rapid_control_station_m"] == (
        RUNTIME_FIRST_RAPID_CONTROL_STATION_M
    )
    assert launch_apron["safe_subcritical_clearance_m"] >= (
        RUNTIME_MINIMUM_SAFE_LAUNCH_APRON_M
    )
    assert launch_apron["maximum_centerline_froude_before_approach"] <= (
        RUNTIME_BREAKING_DOWNSTREAM_FROUDE_MAX
    )
    assert launch_apron["production_authoritative"] is False
    assert scenario["gameplay"]["safe_launch_apron"] == launch_apron
    assert contract["transitions"][0]["control_station_m"] == (
        RUNTIME_FIRST_RAPID_CONTROL_STATION_M
    )

    center_row = loaded["h"].shape[0] // 2
    station_m = np.arange(loaded["h"].shape[1]) * RUNTIME_GRID_DX_M
    center_h = loaded["h"][center_row]
    center_u = loaded["u"][center_row]
    center_v = loaded["v"][center_row]
    launch_start_index = int(RUNTIME_LAUNCH_STATION_M / RUNTIME_GRID_DX_M)
    launch_end_index = int(
        launch_apron["first_rapid_approach_start_station_m"] / RUNTIME_GRID_DX_M
    )
    launch_froude = np.hypot(
        center_u[launch_start_index:launch_end_index],
        center_v[launch_start_index:launch_end_index],
    ) / np.sqrt(
        9.80665 * np.maximum(center_h[launch_start_index:launch_end_index], 1.0e-6)
    )
    assert float(launch_froude.max()) <= RUNTIME_BREAKING_DOWNSTREAM_FROUDE_MAX
    for row in contract["transitions"]:
        control_station_m = float(row["control_station_m"])
        sampled_station_m = np.arange(
            max(0.0, control_station_m - 15.0),
            control_station_m + 25.0 + 0.5 * RUNTIME_PRESENTATION_SAMPLE_SPACING_M,
            RUNTIME_PRESENTATION_SAMPLE_SPACING_M,
        )
        sampled_h = np.interp(sampled_station_m, station_m, center_h)
        sampled_speed = np.hypot(
            np.interp(sampled_station_m, station_m, center_u),
            np.interp(sampled_station_m, station_m, center_v),
        )
        sampled_froude = sampled_speed / np.sqrt(
            9.80665 * np.maximum(sampled_h, 1.0e-6)
        )
        assert np.any(
            (sampled_froude[:-1] >= RUNTIME_BREAKING_UPSTREAM_FROUDE_MIN)
            & (sampled_froude[1:] <= RUNTIME_BREAKING_DOWNSTREAM_FROUDE_MAX)
        )


def test_zambezi_reference_map_is_in_the_shipping_cook_and_regeneration_contracts():
    map_package = "/Game/RaftSim/Maps/L_Zambezi"
    promoted_map = REPO_ROOT / "unreal/Content/RaftSim/Maps/L_Zambezi.umap"
    assert promoted_map.is_file()
    assert promoted_map.stat().st_size > 1_000_000
    default_game = (REPO_ROOT / "unreal/Config/DefaultGame.ini").read_text(
        encoding="utf-8"
    )
    assert f'+MapsToCook=(FilePath="{map_package}")' in default_game

    progression_manifest = _load(
        REPO_ROOT / "unreal/Content/RaftSim/UI/m6_game_progression_manifest.json"
    )
    free_run = progression_manifest["game_modes"]["free_run"]
    assert free_run["runnable_river_count"] == 6
    runnable_rivers = free_run["runnable_rivers"]
    assert len(runnable_rivers) == free_run["runnable_river_count"]
    assert {river["river_id"] for river in runnable_rivers} == {
        "south_fork_american_chili_bar",
        "colorado_river_grand_canyon_rowing",
        "pacuare_river_costa_rica",
        "futaleufu_river_chile",
        "chilko_river_lava_canyon",
        "zambezi_batoka_gorge",
    }
    zambezi = next(
        river
        for river in runnable_rivers
        if river["river_id"] == "zambezi_batoka_gorge"
    )
    assert zambezi == {
        "river_id": "zambezi_batoka_gorge",
        "scenario_id": "zambezi_reference_run",
        "map_package": map_package,
        "tier": "reference_free_run",
        "runnable": True,
        "availability": "free_run",
        "runnable_release_review": RUNNABLE_RELEASE_REVIEW.as_posix(),
    }

    frontend_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimUI/Private/"
        "RaftSimVerticalSliceFrontend.cpp"
    ).read_text(encoding="utf-8")
    assert 'TEXT("zambezi_reference_run")' in frontend_source
    assert 'TEXT("Zambezi: Boiling Pot to Mukuni Beach")' in frontend_source
    assert 'TEXT("Runnable Reference Free Run:' in frontend_source
    assert 'TEXT("/Game/RaftSim/Maps/L_Zambezi")' in frontend_source

    progression_test_source = (
        REPO_ROOT
        / "unreal/Source/SmokeEmIfYouGotEm/Tests/RaftSimM6GameProgressionTest.cpp"
    ).read_text(encoding="utf-8")
    assert 'FindScenario(TEXT("zambezi_reference_run")' in progression_test_source
    assert 'FName(TEXT("/Game/RaftSim/Maps/L_Zambezi"))' in progression_test_source
    assert "L_ZambeziBatokaGorge_PhysicalCorridorCandidate" not in (
        progression_test_source
    )

    module_header = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Public/RaftSimEditorModule.h"
    ).read_text(encoding="utf-8")
    module_cpp = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/RaftSimEditorModule.cpp"
    ).read_text(encoding="utf-8")
    automation_cpp = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Commands/"
        "RaftSimEditorEnvironmentAutomation.cpp"
    ).read_text(encoding="utf-8")
    assert "LandscapeImportCandidateRiverFilter" in module_header
    assert "RaftSimLandscapeImportCandidateRiverId=" in module_cpp
    assert "LandscapeImportCandidateRiverFilter" in automation_cpp

    for relative in ("unreal/Scripts/package_mac.sh", "unreal/Scripts/package_win.ps1"):
        packaging_script = (REPO_ROOT / relative).read_text(encoding="utf-8")
        assert "L_Zambezi.umap" in packaging_script
        assert "RaftSimCreateLandscapeImportCandidateMaps" in packaging_script
        assert "RaftSimLandscapeImportCandidateRiverId=zambezi_batoka_gorge" in (
            packaging_script
        )


def test_unreal_candidate_binds_the_zambezi_scenario_and_builds_editor_markers():
    internal = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorEnvironmentInternal.h"
    ).read_text(encoding="utf-8")
    catalog_cpp = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorEnvironmentCatalog.cpp"
    ).read_text(encoding="utf-8")
    build_cpp = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/"
        "RaftSimEditorLandscapeBuild.cpp"
    ).read_text(encoding="utf-8")
    geometry_cpp = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/"
        "RaftSimEditorLandscapeGeometry.cpp"
    ).read_text(encoding="utf-8")
    director_cpp = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Rivers/"
        "RaftSimEditorZambeziDirector.cpp"
    ).read_text(encoding="utf-8")
    foliage_cpp = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/"
        "RaftSimEditorLandscapeFoliage.cpp"
    ).read_text(encoding="utf-8")
    lighting_cpp = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorNearFieldAndLighting.cpp"
    ).read_text(encoding="utf-8")
    automation_cpp = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Commands/"
        "RaftSimEditorEnvironmentAutomation.cpp"
    ).read_text(encoding="utf-8")
    assert "ScenarioRelativePath" in internal
    assert SCENARIO_RELATIVE.as_posix() in catalog_cpp
    assert "AddLandscapeCandidateScenarioMarkers" in build_cpp
    assert "AddLandscapeCandidateRunnableGameplay" in build_cpp
    assert "RaftSim_ZambeziRapid_" in geometry_cpp
    assert "RaftSim_Zambezi_PlayerRaft" in geometry_cpp
    assert "bRecenterHydraulicCrux = false" in geometry_cpp
    assert "RaftSimGlobalRiverStationAuthority" in geometry_cpp
    assert "RaftSimSafeLaunchApron" in geometry_cpp
    assert "ApplyZambeziBatokaVisualTerrainTreatment" in build_cpp
    assert "AddZambeziAdaptiveNearFieldTerrain" in build_cpp
    assert "RaftSimZambeziAdaptiveNearFieldTerrainV1" in geometry_cpp
    assert "RaftSimSourceConditionedTerrain" in geometry_cpp
    assert "RaftSimProtectedDryShoreline" in geometry_cpp
    assert "RaftSimNearFieldSelfShadowSuppressed" in geometry_cpp
    assert "RaftSimConditionedWaterlineWetBankV1" in geometry_cpp
    assert "RaftSimVertexRedWetBankMask" in geometry_cpp
    assert "WetStainCeilingCm" in geometry_cpp
    assert (
        "LoadOrCreatePhysicalSourceTerrainRenderMaterial(Candidate, true, true)"
        in build_cpp
    )
    assert "RaftSimProceduralVisualMorphology" in director_cpp
    assert "RaftSimNonCollisionRenderSurface" in director_cpp
    assert "ShorelineDryBufferCm = 2800.0f" in director_cpp
    assert "NearBankMorphologyReachBeyondWaterCm = 14800.0f" in director_cpp
    assert "NearBankRoundedSlopeMaskStart = 0.055f" in director_cpp
    assert "MorphologyOffsetClampCm = 280.0f" in director_cpp
    assert "UpperCliffMorphologyOffsetClampCm = 440.0f" in director_cpp
    assert "UpperCliffMorphologyStartAboveWaterCm = 600.0f" in director_cpp
    assert "UpperCliffMorphologyFullStrengthAboveWaterCm = 1800.0f" in director_cpp
    assert "ClosestCenterlinePoint" in director_cpp
    assert "SegmentLengthSquared" in director_cpp
    assert "RaftSimBatokaOrganicMorphologyV17" in director_cpp
    assert "RaftSimBatokaHeightAwareFacetReconstructionV17" in director_cpp
    assert "RaftSimBatokaUpperDryScarpInfillV17" in director_cpp
    assert "RaftSimProtectedShorelineBuffer" in director_cpp
    assert "MorphologyProtectionFade" in director_cpp
    assert "UpperButtressOffsetCm" in director_cpp
    assert "MorphologyStats.NearBankModifiedVertexCount <= 0" in build_cpp
    assert (
        "MorphologyStats.UpperCliffModifiedInsideProtectedRadiusVertexCount <= 0"
        in build_cpp
    )
    assert (
        "MorphologyStats.MinimumUpperCliffModifiedInsideRadiusHeightAboveWaterCm"
        in build_cpp
    )
    assert "CreateZambeziOpaqueVegetationAssets" in foliage_cpp
    assert "M_RaftSim_Zambezi_OpaqueVegetation" in foliage_cpp
    assert "Material->BlendMode = BLEND_Opaque" in foliage_cpp
    assert "Material->TwoSided = false" in foliage_cpp
    assert "AmbientOcclusion->R = 1.0f" in foliage_cpp
    assert "ShadowFloor->R = ShadowFillStrength" in foliage_cpp
    assert (
        'ZambeziVegetationMaterialPath,\n        TEXT("Zambezi"),\n        0.09f'
        in foliage_cpp
    )
    assert "FLinearColor(0.060f, 0.088f, 0.022f, 1.0f)" in foliage_cpp
    assert "RaftSimOpaqueVolumetricVegetation" in foliage_cpp
    assert "RaftSimProceduralVegetationFallback" in foliage_cpp
    assert "RaftSimSlopeScreenedPlacement" in foliage_cpp
    assert "GetLandscapeSlopeDegrees" in foliage_cpp
    assert "ZambeziEvidenceBankMosaicInstanceCount = 1200" in foliage_cpp
    assert "ZambeziOrganicBankMosaic" in foliage_cpp
    assert "RaftSimCameraVisibleBankCover" in foliage_cpp
    assert "InstancesPerLongitudinalLane" in foliage_cpp
    assert "ZambeziEvidenceWoodyInstanceCount = 240" in foliage_cpp
    assert "ZambeziEvidenceWoodySlopeCeilingDegrees = 24.0f" in foliage_cpp
    assert "ZambeziCameraRiparianTree" in foliage_cpp
    assert "ZambeziCameraUmbrellaTree" in foliage_cpp
    assert "ZambeziCameraThornScrub" in foliage_cpp
    assert "RaftSimCameraVisibleWoodyEcology" in foliage_cpp
    assert "RaftSimOrganicWoodyBankLayer" in foliage_cpp
    assert "RaftSimWoodySlopeCeiling24Degrees" in foliage_cpp
    assert "ZambeziRunnableLaunchBankCoverInstanceCount = 7200" in foliage_cpp
    assert "ZambeziRunnableLaunchMinimumBankCoverInstanceCount = 4500" in foliage_cpp
    assert "ZambeziRunnableLaunchWoodyInstanceCount = 640" in foliage_cpp
    assert "ZambeziRunnableLaunchCameraFaceWoodyInstanceCount = 240" in foliage_cpp
    assert "ZambeziRunnableLaunchMinimumCameraFaceWoodyInstanceCount = 120" in foliage_cpp
    assert "ZambeziRunnableLaunchMinimumWoodyInstanceCount = 560" in foliage_cpp
    assert "ZambeziRunnableLaunchEcologyStratumCount = 6" in foliage_cpp
    assert "ZambeziRunnableLaunchMinimumGroundCoverPerStratum = 450" in foliage_cpp
    assert "ZambeziRunnableLaunchMinimumWoodyPerStratum = 45" in foliage_cpp
    assert "ZambeziRunnableLaunchGroundCoverSlopeCeilingDegrees = 42.0f" in foliage_cpp
    assert "ZambeziRunnableLaunchWoodySlopeCeilingDegrees = 34.0f" in foliage_cpp
    assert "SM_RaftSim_Zambezi_SavannaGroundCover_B_OpaqueV2" in foliage_cpp
    assert "RaftSimOrganicGroundCoverMorphologyV2" in foliage_cpp
    assert "RaftSimZambeziLowerEnergyLaunchEcologyV18" in foliage_cpp
    assert "RaftSimZambeziElevationStratifiedEcologyV19" in foliage_cpp
    assert "RaftSimEcologyStratumCustomDataV1" in foliage_cpp
    assert "RaftSimZambeziLaunchCameraFaceMosaicV19" in foliage_cpp
    assert "CandidateIndex < 256" in foliage_cpp
    assert "CandidateIndex < 400" in foliage_cpp
    assert "CandidateIndex < 320" in foliage_cpp
    assert "Component->SetCullDistances(0, 120000)" in foliage_cpp
    assert "TargetAdditionalOffset" in foliage_cpp
    assert "TargetDryHeightAboveWaterCm" in foliage_cpp
    assert "SlopeDegrees - TargetSlopeDegrees" in foliage_cpp
    assert (
        "one_project_owned_opaque_one_sided_vertex_color_material_bound_to_five_"
        "volumetric_morphology_meshes_no_alpha_cards" in automation_cpp
    )
    assert "ZambeziRunnableLaunchTalusInstanceCount = 360" in foliage_cpp
    assert "ZambeziRunnableLaunchTalusReviewedSourceBlend = 0.42f" in foliage_cpp
    assert "ZambeziRunnableLaunchTalusWetBandWidthCm = 220.0f" in foliage_cpp
    assert "SetNumCustomDataFloats(1)" in foliage_cpp
    assert "SetCustomDataValue(" in foliage_cpp
    assert "RaftSimPerInstanceConditionedWaterline" in foliage_cpp
    assert "MI_RaftSim_Zambezi_BasaltTalusV1" in foliage_cpp
    assert "RaftSimRunnableLaunchTalusV1" in foliage_cpp
    assert "RaftSimZambeziBasaltAnalogMaterialV1" in foliage_cpp
    assert "RaftSimProjectOwnedMineralRetone" in foliage_cpp
    assert "RaftSimGenericRockAnalogNoLithologyAuthority" in foliage_cpp
    assert "RaftSimPresentationOnlyNoHydraulicAuthority" in foliage_cpp
    assert "RaftSimZambeziAtmosphereV1" in lighting_cpp
    assert "RaftSimAtmosphereSunLight" in lighting_cpp
    assert "RaftSimSourceAwareDrySeasonSky" in lighting_cpp
    assert "RaftSimVolumetricGorgeHaze" in lighting_cpp
    assert "InstancesPerWoodyLane" in foliage_cpp
    assert "CandidateIndex < 40" in foliage_cpp
    assert "BestSlopeDegrees > ZambeziEvidenceWoodySlopeCeilingDegrees" in foliage_cpp

    live_water_cpp = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
        "RaftSimEditorZambeziWaterMaterial.cpp"
    ).read_text(encoding="utf-8")
    texture_builder_cpp = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
        "RaftSimEditorPhotorealTextureAssets.cpp"
    ).read_text(encoding="utf-8")
    runtime_water_cpp = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/"
        "RaftSimWaterSurfaceActor.cpp"
    ).read_text(encoding="utf-8")
    assert "bSolverOwnedRuntimeWater = bReachLocalRun || bZambezi" in geometry_cpp
    assert "LoadOrCreateZambeziBatokaLiveWaterV2Instance" in geometry_cpp
    assert "bEnableLiveSolverVolumeCore = true" in geometry_cpp
    assert "RaftSimZambeziTransmittingWaterV2" in geometry_cpp
    assert "RaftSimOpacityFeatheredVolumeEdgeV2" in geometry_cpp
    assert "RaftSimRestrainedSolarGlareV2" in geometry_cpp
    assert "RaftSimSolverMaskedFoamLace" in geometry_cpp
    assert "RaftSimNoSolverStateMutation" in geometry_cpp
    assert "MI_RaftSim_ZambeziBatoka_LiveVolumeWaterV2" in live_water_cpp
    assert "LiveVolumeBankCoverageFloor" in live_water_cpp
    assert "M_RaftSim_SouthForkRaftTransmissionWater" in live_water_cpp
    assert "BuildZambeziBatokaWaterTextureAssets" in texture_builder_cpp
    assert "ZambeziBatokaWaterV1" in texture_builder_cpp
    assert "RiverWaterConfig->LiveWaterScattering" in runtime_water_cpp
    assert "RiverWaterConfig->LiveWaterAbsorption" in runtime_water_cpp
    assert "RiverWaterConfig->LiveRiverbedColorScale" in runtime_water_cpp
    assert "RiverPresentationSubdivision = 2" in (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/"
        "RaftSimWaterSurfaceActor.h"
    ).read_text(encoding="utf-8")
    assert "ResolvedVertexSpacingMeters" in runtime_water_cpp
    assert "PresentationAnalysisStride" in runtime_water_cpp
    assert "const float PrimaryPacket" in runtime_water_cpp
    assert "const float PrimaryPhase" in runtime_water_cpp
    assert "const float SecondaryPhase" in runtime_water_cpp
    assert "const float DetailPhase" in runtime_water_cpp
    assert "const float CrossPhase" in runtime_water_cpp
    assert "0.065f" in runtime_water_cpp

    source_art = REPO_ROOT / "unreal/SourceArt/RaftSim/Water/ZambeziBatoka"
    expected_assets = {
        "T_RaftSim_ZambeziBatoka_FlowNormalV1": (
            "48352e03d2e535876ddd783cd249b4628938c264b965bd66951d4053540da716",
            "normal_map",
        ),
        "T_RaftSim_ZambeziBatoka_FoamLaceV1": (
            "1fc472ef1d21fbee5f6659281a0327705edc8914766c803eb29b354f8d17e5b3",
            "mask",
        ),
    }
    for asset_name, (expected_sha256, expected_compression) in expected_assets.items():
        texture_path = source_art / f"{asset_name}.png"
        provenance = _load(source_art / f"{asset_name}.provenance.json")
        assert texture_path.is_file()
        assert _sha256(texture_path) == expected_sha256
        assert provenance["schema"] == (
            "raftsim.first_party.generated_texture_provenance.v1"
        )
        assert provenance["project_ownership"] == "first-party generated project asset"
        assert provenance["texture"]["sha256"] == expected_sha256
        assert provenance["texture"]["width"] == 1254
        assert provenance["texture"]["height"] == 1254
        assert provenance["texture"]["addressing"] == "mirror_x_mirror_y"
        assert provenance["texture"]["srgb"] is False
        assert provenance["texture"]["compression"] == expected_compression
        assert "no hydraulic" in provenance["asset_role"]

    validation = _load(
        REPO_ROOT
        / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
        "zambezi_reference_scenario_map_validation.json"
    )
    assert validation["passed"] is True
    assert validation["scenario_marker_count"] == 25
    assert validation["rapid_numbers"] == list(range(1, 26))
    assert validation["mandatory_portage_actor"] == (
        "RaftSim_ZambeziRapid_9_Commercial_Suicide"
    )
    assert validation["runnable"]["player_raft_count"] == 1
    assert validation["runnable"]["water_config_count"] == 1
    assert validation["runnable"]["game_mode"].endswith("RaftSimVerticalSliceGameMode")
    assert validation["visual_terrain"]["authority"] == (
        "source_conditioned_plus_bounded_procedural_render_only"
    )
    assert validation["visual_terrain"]["conditioned_tile_count"] == 4
    assert all(
        "BatokaV12_WorldAligned" in tile["material"]
        for tile in validation["visual_terrain"]["tiles"]
    )
    assert all(
        "NO_COLLISION" in tile["collision_enabled"]
        for tile in validation["visual_terrain"]["tiles"]
    )
    assert validation["schema"].endswith(".v21")
    assert validation["runtime_hydraulics"]["preserves_global_river_stations"] is True
    assert validation["runtime_hydraulics"]["rapid_count"] == 25
    assert validation["runtime_hydraulics"]["rapid_9_policy"].startswith(
        "hazard_visualization_only"
    )
    assert validation["runtime_hydraulics"]["safe_launch_apron_tagged"] is True
    assert validation["visual_terrain"]["morphology_contract"] == (
        "v18_exposure_safe_organic_basalt_with_wet_bank_protection_and_height_aware_"
        "upper_dry_scarp_infill_plus_central_difference_grid_normals_"
        "and_source_facet_reconstruction"
    )
    assert validation["visual_terrain"]["active_water_half_width_m"] == 72.0
    assert validation["visual_terrain"]["protected_shoreline_radius_m"] == 100.0
    assert validation["visual_terrain"]["minimum_dry_bank_buffer_m"] == 26.56
    assert validation["visual_terrain"]["full_strength_morphology_radius_m"] == 220.0
    assert (
        validation["visual_terrain"]["maximum_visual_treatment_vertical_offset_m"]
        == 4.4
    )
    assert all(
        "RaftSimBatokaOrganicMorphologyV17" in tile["tags"]
        and "RaftSimBatokaHeightAwareFacetReconstructionV17" in tile["tags"]
        and "RaftSimBatokaUpperDryScarpInfillV17" in tile["tags"]
        and "RaftSimProtectedShorelineBuffer" in tile["tags"]
        for tile in validation["visual_terrain"]["tiles"]
    )
    adaptive = validation["visual_terrain"]["adaptive_near_field"]
    assert adaptive["actor_count"] == 2
    assert adaptive["station_window_m"] == [0.0, 1000.0]
    assert adaptive["grid_spacing_m"] == 5.0
    assert adaptive["maximum_dry_shoreline_infill_m"] == 1.8
    assert adaptive["maximum_procedural_refinement_m"] == 0.96
    assert adaptive["wet_bank_contract"].startswith(
        "conditioned_profile_vertex_red_render_only"
    )
    assert adaptive["wet_bank_authority"].startswith(
        "procedural_presentation_only_no_measured"
    )
    assert all(
        "NO_COLLISION" in actor["collision_enabled"]
        and actor["cast_shadow"] is False
        and "RaftSimSourceConditionedTerrain" in actor["tags"]
        and "RaftSimProtectedDryShoreline" in actor["tags"]
        and "RaftSimNearFieldSelfShadowSuppressed" in actor["tags"]
        and "RaftSimConditionedWaterlineWetBankV1" in actor["tags"]
        and "RaftSimVertexRedWetBankMask" in actor["tags"]
        and "RaftSimProceduralWetBankNoMeasuredAuthority" in actor["tags"]
        for actor in adaptive["actors"]
    )
    assert validation["lighting"]["atmosphere_actor_count"] == 4
    atmosphere_tags = {
        tag
        for actor in validation["lighting"]["atmosphere_actors"]
        for tag in actor["tags"]
    }
    assert {
        "RaftSimAtmosphereSunLight",
        "RaftSimCapturedGorgeSkyFill",
        "RaftSimSourceAwareDrySeasonSky",
        "RaftSimVolumetricGorgeHaze",
    } <= atmosphere_tags
    assert validation["water_surface"]["component_count"] == 1
    assert validation["water_surface"]["solver_owned_runtime_rendering"] is True
    assert validation["water_surface"]["live_volume_core_enabled"] is True
    assert validation["water_surface"]["gameplay_shading_contract"] == (
        "solver_owned_transmitting_volume_core"
    )
    assert validation["water_surface"]["capture_shading_model_contract"] == (
        "DefaultLit"
    )
    assert "MI_RaftSim_ZambeziBatoka_LiveVolumeWaterV2" in (
        validation["water_surface"]["live_volume_material"]
    )
    assert validation["water_surface"]["bank_edge_contract"] == (
        "vertex_alpha_feathered_single_layer_water_volume_v2"
    )
    assert "T_RaftSim_ZambeziBatokaWaterV1_FlowNormal" in (
        validation["water_surface"]["live_flow_normal"]
    )
    assert "T_RaftSim_ZambeziBatokaWaterV1_FoamLace" in (
        validation["water_surface"]["live_foam_lace"]
    )
    assert validation["water_surface"]["calm_detail_coverage"] < 0.10
    assert validation["water_surface"]["active_detail_coverage"] < 0.20
    assert validation["water_surface"]["presentation_smoothing_enabled"] is True
    assert (
        abs(validation["water_surface"]["presentation_smoothing_strength"] - 0.62)
        <= 0.001
    )
    assert abs(validation["water_surface"]["bank_blend_m"] - 7.5) <= 0.001
    assert all(
        "RaftSimCaptureOnlyStaticWater" in component["tags"]
        and "RaftSimLiveSolverWaterOwnsRuntimeRendering" in component["tags"]
        for component in validation["water_surface"]["components"]
    )
    talus = validation["launch_talus"]
    assert talus["component_count"] == 6
    assert talus["target_instance_count"] == 360
    assert talus["instance_count"] == 360
    assert talus["rejected_placement_count"] == 0
    assert talus["slope_ceiling_degrees"] == 48.0
    assert talus["target_height_range_m"] == [0.95, 5.20]
    assert talus["wet_band_width_m"] == 2.2
    assert "per_instance_conditioned_profile_waterline" in talus["material_contract"]
    assert sorted(component["instance_count"] for component in talus["components"]) == [
        60,
        60,
        60,
        60,
        60,
        60,
    ]
    assert all(
        "NO_COLLISION" in component["collision_enabled"]
        and component["cast_shadow"] is True
        and "RockMossSet01" in component["static_mesh"]
        and "MI_RaftSim_Zambezi_BasaltTalusV1" in component["material"]
        and "M_RaftSim_RiverBoulder" in component["parent_material"]
        and "RaftSimRunnableLaunchTalusV1" in component["tags"]
        and "RaftSimZambeziBasaltAnalogMaterialV1" in component["tags"]
        and "RaftSimProjectOwnedMineralRetone" in component["tags"]
        and "RaftSimGenericRockAnalogNoLithologyAuthority" in component["tags"]
        and "RaftSimNonCollisionRenderSurface" in component["tags"]
        and "RaftSimPresentationOnlyNoHydraulicAuthority" in component["tags"]
        and "RaftSimConditionedWaterlineWetBankV1" in component["tags"]
        and "RaftSimPerInstanceConditionedWaterline" in component["tags"]
        and "RaftSimProceduralWetBankNoMeasuredAuthority" in component["tags"]
        and component["num_custom_data_floats"] == 1
        and component["custom_data_value_count"] == component["instance_count"]
        and component["conditioned_waterline_min_z_cm"] > -1.0e6
        and component["conditioned_waterline_max_z_cm"]
        >= component["conditioned_waterline_min_z_cm"]
        for component in talus["components"]
    )
    assert validation["vegetation"]["component_count"] == 13
    assert validation["vegetation"]["camera_visible_bank_cover_component_count"] == 1
    assert validation["vegetation"]["camera_visible_bank_cover_instance_count"] == 1200
    assert validation["vegetation"]["camera_visible_woody_component_count"] == 3
    assert validation["vegetation"]["camera_visible_woody_instance_count"] == 232
    assert validation["vegetation"]["camera_visible_woody_target_instance_count"] == 240
    assert validation["vegetation"]["camera_visible_woody_slope_rejection_count"] == 8
    assert (
        validation["vegetation"]["camera_visible_woody_slope_ceiling_degrees"] == 24.0
    )
    assert validation["vegetation"]["legacy_zambezi_pve_actor_count"] == 0
    assert validation["vegetation"]["runnable_launch_bank_cover_component_count"] == 2
    assert validation["vegetation"]["runnable_launch_bank_cover_instance_count"] >= 4500
    assert (
        validation["vegetation"]["runnable_launch_bank_cover_target_instance_count"]
        == 7200
    )
    assert validation["vegetation"]["runnable_launch_bank_cover_instance_count"] == 6512
    assert validation["vegetation"]["runnable_launch_bank_cover_stratum_counts"] == [
        978,
        1200,
        1200,
        734,
        1200,
        1200,
    ]
    assert validation["vegetation"][
        "runnable_launch_bank_cover_minimum_per_stratum"
    ] == 450
    assert validation["vegetation"]["runnable_launch_woody_component_count"] == 3
    assert validation["vegetation"]["runnable_launch_woody_instance_count"] >= 560
    assert (
        validation["vegetation"]["runnable_launch_woody_target_instance_count"] == 880
    )
    assert validation["vegetation"]["runnable_launch_woody_instance_count"] == 772
    assert validation["vegetation"]["runnable_launch_woody_rejection_count"] == 108
    assert validation["vegetation"]["runnable_launch_woody_stratum_counts"] == [
        139,
        122,
        140,
        112,
        108,
        151,
    ]
    assert validation["vegetation"][
        "runnable_launch_woody_minimum_per_stratum"
    ] == 45
    assert (
        validation["vegetation"]["runnable_launch_bank_cover_slope_ceiling_degrees"]
        == 42.0
    )
    assert (
        validation["vegetation"]["runnable_launch_woody_slope_ceiling_degrees"] == 34.0
    )
    launch_ground_cover = [
        component
        for component in validation["vegetation"]["components"]
        if "RaftSimRunnableLaunchBankCover" in component["tags"]
    ]
    assert len(launch_ground_cover) == 2
    assert all(
        "RaftSimOrganicGroundCoverMorphologyV2" in component["tags"]
        and "RaftSimZambeziLowerEnergyLaunchEcologyV18" in component["tags"]
        and "RaftSimZambeziElevationStratifiedEcologyV19" in component["tags"]
        and "RaftSimEcologyStratumCustomDataV1" in component["tags"]
        and component["num_custom_data_floats"] == 1
        and component["custom_data_value_count"] == component["instance_count"]
        and "SavannaGroundCover_" in component["static_mesh"]
        for component in launch_ground_cover
    )
    launch_woody = [
        component
        for component in validation["vegetation"]["components"]
        if "RaftSimRunnableLaunchWoodyEcology" in component["tags"]
    ]
    assert len(launch_woody) == 3
    assert all(
        "RaftSimZambeziElevationStratifiedEcologyV19" in component["tags"]
        and "RaftSimZambeziLaunchCameraFaceMosaicV19" in component["tags"]
        and "RaftSimEcologyStratumCustomDataV1" in component["tags"]
        and component["num_custom_data_floats"] == 1
        and component["custom_data_value_count"] == component["instance_count"]
        and sum(component["ecology_stratum_counts"])
        == component["instance_count"]
        for component in launch_woody
    )
    assert sorted(
        component["instance_count"]
        for component in validation["vegetation"]["components"]
        if "RaftSimRunnableLaunchBankEcologyV1" not in component["tags"]
    ) == [57, 58, 117, 700, 1200, 1400, 1400, 2100]
    assert all(
        "M_RaftSim_Zambezi_OpaqueVegetation" in component["material"]
        for component in validation["vegetation"]["components"]
    )
    assert all(
        "NO_COLLISION" in component["collision_enabled"]
        for component in validation["vegetation"]["components"]
    )
    mosaic = next(
        component
        for component in validation["vegetation"]["components"]
        if "ZambeziOrganicBankMosaic" in component["actor_label"]
    )
    assert "RaftSimCameraVisibleBankCover" in mosaic["tags"]
    assert "RaftSimOrganicBankMosaic" in mosaic["tags"]
    assert "SavannaGroundCover_A_OpaqueV1" in mosaic["static_mesh"]
    woody = [
        component
        for component in validation["vegetation"]["components"]
        if "RaftSimCameraVisibleWoodyEcology" in component["tags"]
    ]
    assert len(woody) == 3
    assert sorted(component["instance_count"] for component in woody) == [
        57,
        58,
        117,
    ]
    assert all(
        "RaftSimOrganicWoodyBankLayer" in component["tags"] for component in woody
    )
    assert all(
        "RaftSimWoodySlopeCeiling24Degrees" in component["tags"] for component in woody
    )
