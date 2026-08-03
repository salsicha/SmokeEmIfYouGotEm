from pathlib import Path
import hashlib
import json


REPO_ROOT = Path(__file__).resolve().parents[2]
MATERIAL_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
    "RaftSimEditorPacuareMaterial.cpp"
)
BASE_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Materials/"
    "RaftSimEditorMaterialsBase.cpp"
)
FOLIAGE_SOURCE = (
    REPO_ROOT
    / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/"
    "RaftSimEditorLandscapeFoliage.cpp"
)
MANIFEST = (
    REPO_ROOT
    / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "landscape_candidate_manifest_pacuare.json"
)
VEGETATION_REVIEW = MANIFEST.with_name(
    "pacuare_opaque_rainforest_vegetation_v1_review.json"
)


def test_pacuare_organic_material_is_river_local_and_non_displacing():
    material_source = MATERIAL_SOURCE.read_text(encoding="utf-8")
    base_source = BASE_SOURCE.read_text(encoding="utf-8")

    assert "BuildPacuareOrganicRainforestBaseColor" in material_source
    assert base_source.count("BuildPacuareOrganicRainforestBaseColor") == 1
    assert (
        'Candidate.PreviewSpec.RiverId == TEXT("pacuare") ? '
        "BuildPacuareOrganicRainforestBaseColor"
    ) in base_source
    assert 'Candidate.PreviewSpec.RiverId == TEXT("pacuare")' in base_source
    assert 'Candidate.PreviewSpec.RiverId == TEXT("colorado_river")' in base_source
    assert "bUsesDefaultLitLandscape ? MSM_DefaultLit : MSM_Unlit" in base_source
    assert "WorldPositionOffset" not in material_source
    assert "Landscape->Import" not in material_source
    assert "SetCollision" not in material_source


def test_pacuare_organic_material_has_three_incommensurate_world_scales():
    source = MATERIAL_SOURCE.read_text(encoding="utf-8")

    assert "Noise(0.00021f, 3)" in source
    assert "Noise(0.00095f, 3)" in source
    assert "Noise(0.00350f, 2)" in source
    assert source.count("UMaterialExpressionNoise* ") >= 4
    assert "PacuareWetRockSlopeStart" in source
    assert "PacuareWetRockSlopeGain" in source
    assert "PacuareLeafLitterTint" in source
    assert "PacuareMossTint" in source
    assert "PacuareWetRockTint" in source


def test_pacuare_generated_manifest_records_shading_and_authority_separation():
    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))["candidates"][0]

    assert candidate["river_id"] == "pacuare"
    assert candidate["landscape_material_shading_model"] == "DefaultLit"
    assert candidate["landscape_material_organic_surface_status"].startswith(
        "pacuare_v1_three_scale_world_space"
    )
    assert candidate["landscape_material_organic_world_noise_scales_per_cm"] == [
        0.00021,
        0.00095,
        0.0035,
    ]
    assert candidate["landscape_material_geometry_authority_status"] == (
        "shade_only_no_world_position_offset_no_collision_or_solver_change"
    )
    assert candidate["landscape_material_promotion_status"] == (
        "review_only_not_lifelike_not_gameplay_promoted"
    )


def test_pacuare_opaque_rainforest_replaces_alpha_card_sources():
    source = FOLIAGE_SOURCE.read_text(encoding="utf-8")

    assert "CreatePacuareOpaqueRainforestVegetationAssets" in source
    assert "M_RaftSim_Pacuare_OpaqueRainforestVegetation" in source
    for asset_name in (
        "SM_RaftSim_Pacuare_CanopyTree_A_OpaqueV2",
        "SM_RaftSim_Pacuare_CanopyTree_B_OpaqueV2",
        "SM_RaftSim_Pacuare_RiparianShrub_A_OpaqueV2",
        "SM_RaftSim_Pacuare_RainforestGroundCover_A_OpaqueV2",
    ):
        assert asset_name in source
    assert "RaftSimPacuareOpaqueRainforestV1" in source
    assert "RaftSimNoSpeciesOrEcologyAuthority" in source
    assert "bZambezi || bPacuare || bOpaqueTemperate" in source


def test_pacuare_manifest_records_opaque_volumetric_dressing_contract():
    candidate = json.loads(MANIFEST.read_text(encoding="utf-8"))["candidates"][0]

    assert candidate["river_id"] == "pacuare"
    assert candidate["landscape_dressing_status"] == (
        "source_mask_placed_project_owned_opaque_volumetric_vegetation_and_"
        "rock_dressing_captured"
    )
    assert candidate["landscape_dressing_source_species_skeletal_mesh_count"] == 0
    assert candidate["landscape_dressing_source_species_skeletal_assets"] == []
    assert candidate["landscape_dressing_converted_species_static_mesh_count"] == 4
    converted_assets = candidate[
        "landscape_dressing_converted_species_static_assets"
    ]
    assert len(converted_assets) == 4
    for object_path in converted_assets:
        package_path = object_path.split(".", 1)[0]
        asset_path = REPO_ROOT / (
            "unreal/Content" + package_path.removeprefix("/Game") + ".uasset"
        )
        assert asset_path.is_file()
        assert "/PacuareRun/Vegetation/Meshes/" in object_path
        assert "PVE" not in object_path

    expected_material = (
        "/Game/RaftSim/Environment/PacuareRun/Vegetation/Materials/"
        "M_RaftSim_Pacuare_OpaqueRainforestVegetation."
        "M_RaftSim_Pacuare_OpaqueRainforestVegetation"
    )
    assert candidate["landscape_dressing_foliage_material_status"] == (
        "one_project_owned_opaque_one_sided_vertex_color_material_bound_to_four_"
        "volumetric_species_no_alpha_cards"
    )
    assert candidate["landscape_dressing_foliage_material_asset_count"] == 1
    assert candidate["landscape_dressing_foliage_material_bound_slot_count"] == 4
    assert (
        candidate["landscape_dressing_native_foliage_material_fallback_slot_count"]
        == 0
    )
    for field in (
        "landscape_dressing_broadleaf_material_asset",
        "landscape_dressing_conifer_material_asset",
        "landscape_dressing_understory_material_asset",
    ):
        assert candidate[field] == expected_material
    assert candidate["landscape_dressing_external_review_rock_mesh_count"] == 6
    assert candidate["landscape_dressing_boulder_instance_count"] == 2780
    assert candidate["landscape_dressing_foliage_instance_count"] == 18400
    assert candidate["landscape_dressing_canopy_tree_instance_count"] == 5993
    assert candidate["landscape_dressing_understory_instance_count"] == 12407
    assert candidate["landscape_dressing_promotion_status"] == (
        "opaque_volumetric_procedural_fallback_removes_alpha_card_artifacts_but_"
        "requires_species_ecology_guide_visual_and_performance_review"
    )


def test_pacuare_opaque_rainforest_review_is_hash_locked_and_fail_closed():
    review = json.loads(VEGETATION_REVIEW.read_text(encoding="utf-8"))

    assert review["status"] == (
        "accepted_alpha_card_removal_photoreal_promotion_rejected"
    )
    assert review["decision"]["source_skeletal_mesh_count"] == 0
    assert review["decision"]["alpha_card_source_count"] == 0
    assert review["decision"]["collision"] is False
    assert review["decision"]["nanite"] is True
    assert len(review["photoreal_rejection_reasons"]) >= 5
    assert all(
        comparison["bright_card_green_pixel_fraction_after"]
        < comparison["bright_card_green_pixel_fraction_before"] * 0.02
        for comparison in review["objective_capture_comparison"]
    )
    assert all(
        comparison["near_black_pixel_fraction_after"]
        < comparison["near_black_pixel_fraction_before"] * 0.55
        for comparison in review["objective_capture_comparison"]
    )
    for capture in review["retained_captures"]:
        path = REPO_ROOT / capture["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == capture["sha256"]
