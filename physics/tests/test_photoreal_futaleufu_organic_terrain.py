from pathlib import Path
import json


REPO_ROOT = Path(__file__).resolve().parents[2]
MATERIAL_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
    "RaftSimEditorFutaleufuMaterial.cpp"
)
BASE_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
    "RaftSimEditorMaterialsBase.cpp"
)
MANIFEST = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "landscape_candidate_manifest_futaleufu_terminator.json"
)


def test_futaleufu_organic_material_is_default_lit_and_non_displacing():
    material_source = MATERIAL_SOURCE.read_text(encoding="utf-8")
    base_source = BASE_SOURCE.read_text(encoding="utf-8")

    assert "BuildFutaleufuOrganicTemperateBaseColor" in material_source
    assert base_source.count("BuildFutaleufuOrganicTemperateBaseColor") == 1
    assert 'Candidate.PreviewSpec.RiverId == TEXT("futaleufu_terminator")' in (
        base_source
    )
    assert "bUsesDefaultLitLandscape ? MSM_DefaultLit : MSM_Unlit" in base_source
    assert "WorldPositionOffset" not in material_source
    assert "Landscape->Import" not in material_source
    assert "SetCollision" not in material_source


def test_futaleufu_organic_material_has_three_incommensurate_world_scales():
    source = MATERIAL_SOURCE.read_text(encoding="utf-8")

    assert "Noise(0.00018f, 3)" in source
    assert "Noise(0.00071f, 3)" in source
    assert "Noise(0.00420f, 2)" in source
    assert source.count("UMaterialExpressionNoise* ") >= 4
    assert "FutaleufuWetGraniteSlopeStart" in source
    assert "FutaleufuWetGraniteSlopeGain" in source
    assert "FutaleufuLeafLitterTint" in source
    assert "FutaleufuMossTint" in source
    assert "FutaleufuWetGraniteTint" in source
    assert "FutaleufuLichenGraniteTint" in source


def test_futaleufu_generated_manifest_records_shading_and_authority_separation():
    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))["candidates"][0]

    assert candidate["river_id"] == "futaleufu_terminator"
    assert candidate["landscape_material_shading_model"] == "DefaultLit"
    assert candidate["landscape_material_organic_surface_status"].startswith(
        "futaleufu_v1_three_scale_world_space"
    )
    assert candidate["landscape_material_organic_world_noise_scales_per_cm"] == [
        0.00018,
        0.00071,
        0.0042,
    ]
    assert candidate["landscape_material_geometry_authority_status"] == (
        "shade_only_no_world_position_offset_no_collision_or_solver_change"
    )
    assert candidate["landscape_material_promotion_status"] == (
        "review_only_not_lifelike_not_gameplay_promoted"
    )
