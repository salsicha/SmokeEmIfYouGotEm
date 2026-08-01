from pathlib import Path
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


def test_pacuare_water_is_isolated_moving_and_non_displacing():
    source = WATER_SOURCE.read_text(encoding="utf-8")
    base = BASE_SOURCE.read_text(encoding="utf-8")

    assert "M_RaftSim_Pacuare_RainforestSingleLayerWater" in source
    assert "MSM_SingleLayerWater" in source
    assert "UMaterialExpressionSingleLayerWaterMaterialOutput" in source
    assert source.count("AddNormalSample(") == 2
    assert "0.00042f" in source
    assert "0.00210f" in source
    assert "EditorOnlyData->WorldPositionOffset" not in source
    assert "Landscape->Import" not in source
    assert "SetCollision" not in source
    assert (
        'Spec.RiverId == TEXT("pacuare") ? '
        "LoadOrCreatePacuareRainforestWaterParent"
    ) in base


def test_pacuare_manifest_records_physical_optics_and_render_only_authority():
    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))["candidates"][0]

    assert candidate["river_id"] == "pacuare"
    assert candidate["water_material_parent"] == (
        "/Game/RaftSim/Environment/PacuareRun/Water/Materials/"
        "M_RaftSim_Pacuare_RainforestSingleLayerWater"
    )
    assert candidate["water_shading_model"] == "SingleLayerWater"
    assert candidate["water_volume_parameter_status"] == (
        "active_on_pacuare_isolated_parent"
    )
    assert candidate["water_surface_opacity"] == 0.28
    assert candidate["water_render_width_scale"] == 1.05
    assert candidate["water_render_normal_up_blend"] == 0.82
    assert candidate["water_render_displacement_scale"] == 0.20
    assert candidate["water_solver_render_geometry_collision_enabled"] is False
    assert candidate["water_solver_visualization_field_enable"] == 0.0
    assert candidate["water_material_promotion_status"] == (
        "review_only_requires_visual_guide_solver_hazard_and_performance_validation"
    )
