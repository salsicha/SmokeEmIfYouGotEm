from pathlib import Path
import hashlib
import json


REPO_ROOT = Path(__file__).resolve().parents[2]
WATER_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
    "RaftSimEditorPacuareWaterMaterial.cpp"
)
BASE_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
    "RaftSimEditorMaterialsBase.cpp"
)
MANIFEST = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "landscape_candidate_manifest_pacuare.json"
)
REVIEW = MANIFEST.with_name(
    "pacuare_default_lit_depth_composition_rejection_review.json"
)
LANDSCAPE_BUILD_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/"
    "RaftSimEditorLandscapeBuild.cpp"
)
TERRAIN_AUTHORING_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
    "RaftSimEditorTerrainAuthoring.cpp"
)


def test_pacuare_water_is_isolated_moving_and_non_displacing():
    source = WATER_SOURCE.read_text(encoding="utf-8")
    base = BASE_SOURCE.read_text(encoding="utf-8")

    assert "M_RaftSim_Pacuare_RainforestDefaultLitWater" in source
    assert "MSM_DefaultLit" in source
    assert "UMaterialExpressionSingleLayerWaterMaterialOutput" not in source
    assert "Single Layer Water remains rejected by capture" in source
    assert source.count("AddNormalSample(") == 2
    assert "0.00042f" in source
    assert "0.00210f" in source
    assert "EditorOnlyData->WorldPositionOffset" not in source
    assert "Landscape->Import" not in source
    assert "SetCollision" not in source
    assert "procedural reference-infill bathymetry" not in source
    assert (
        'Spec.RiverId == TEXT("pacuare") ? '
        "LoadOrCreatePacuareRainforestWaterParent"
    ) in base


def test_pacuare_manifest_records_capture_accepted_render_only_water():
    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))["candidates"][0]

    assert candidate["river_id"] == "pacuare"
    assert candidate["water_material_parent"] == (
        "/Game/RaftSim/Environment/PacuareRun/Water/Materials/"
        "M_RaftSim_Pacuare_RainforestDefaultLitWater"
    )
    assert candidate["water_shading_model"] == "DefaultLit"
    assert candidate["water_volume_parameter_status"] == (
        "inactive_single_layer_evaluation_values_retained_in_manifest_only"
    )
    assert candidate["water_surface_opacity"] == 1.0
    assert candidate["water_single_layer_capture_decision"] == (
        "rejected_on_pacuare_after_direct_material_isolation_and_"
        "procedural_reference_infill_bathymetry_bracket"
    )
    assert candidate["water_single_layer_failure_artifact"] == (
        "hard_near_camera_horizontal_depth_composition_band"
    )
    assert candidate["water_conditioned_bathymetry_bracket_status"] == (
        "rejected_did_not_remove_foreground_band_or_river_right_white_patch"
    )
    assert candidate["water_conditioned_bathymetry_active"] is False
    assert candidate["water_render_width_scale"] == 1.35
    assert candidate["water_render_normal_up_blend"] == 0.82
    assert candidate["water_render_displacement_scale"] == 0.20
    assert candidate["water_solver_render_geometry_collision_enabled"] is False
    assert candidate["water_solver_visualization_field_enable"] == 1.0
    assert candidate["water_solver_visualization_field_status"] == (
        "pacuare_cooked_field_capture_visualization_bound_review_only_not_"
        "production_promoted"
    )
    assert candidate["water_solver_visualization_field_texture_count"] == 1
    assert candidate["water_solver_surface_relief_cap_cm"] == 18.0
    assert candidate["water_solver_foam_status"] == (
        "capture_only_cooked_speed_froude_masked_noncolliding_surface_bound_"
        "hidden_in_game"
    )
    assert candidate["water_material_promotion_status"] == (
        "review_only_requires_visual_guide_solver_hazard_and_performance_validation"
    )


def test_pacuare_rejected_infill_is_absent_and_review_is_hash_locked():
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    build_source = LANDSCAPE_BUILD_SOURCE.read_text(encoding="utf-8")
    terrain_source = TERRAIN_AUTHORING_SOURCE.read_text(encoding="utf-8")

    assert review["status"] == (
        "accepted_technical_visual_correction_photoreal_promotion_rejected"
    )
    assert review["decision"]["shading_model"] == "DefaultLit"
    assert review["decision"]["single_layer_water_active"] is False
    assert review["decision"]["render_width_scale"] == 1.35
    assert "AddPacuareConditionedRenderBathymetry" not in build_source
    assert "AddPacuareShorelineGapInfill" not in build_source
    assert "RaftSimPacuareDefaultLitWater" in terrain_source
    assert "RaftSimSingleLayerWaterCaptureRejected" in terrain_source

    for capture in review["retained_captures"]:
        path = REPO_ROOT / capture["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == capture["sha256"]
