# ruff: noqa: F405

from photoreal_test_support import *  # noqa: F401,F403


def test_first_party_material_swatch_manifest_records_review_only_pngs():
    material_plan = json.loads(MATERIAL_RECIPE_PATH.read_text(encoding="utf-8"))
    swatch_manifest = json.loads(
        MATERIAL_SWATCH_MANIFEST_PATH.read_text(encoding="utf-8")
    )

    assert (
        swatch_manifest["schema"]
        == "raftsim.unreal.first_party_material_swatch_manifest.v1"
    )
    assert (
        swatch_manifest["status"]
        == "review_only_first_party_procedural_material_swatches_generated_not_lifelike_capture"
    )
    assert (
        swatch_manifest["material_recipe_plan"]
        == "unreal/Content/RaftSim/Rendering/first_party_procedural_material_recipes.json"
    )
    assert "not production texture sets" in swatch_manifest["current_decision"]

    river_ids = {"american_south_fork", "colorado_river", "pacuare"}
    recipe_ids = {recipe["recipe_id"] for recipe in material_plan["material_recipes"]}
    assert {swatch["river_id"] for swatch in swatch_manifest["swatches"]} == river_ids

    for swatch in swatch_manifest["swatches"]:
        swatch_path = REPO_ROOT / swatch["path"]
        assert swatch_path.exists()
        assert _sha256(swatch_path) == swatch["sha256"]
        with Image.open(swatch_path) as image:
            assert image.size == (swatch["width"], swatch["height"]) == (960, 720)
            assert image.mode == "RGB"
        assert set(swatch["recipe_ids"]) == recipe_ids
        assert (
            swatch["status"]
            == "review_only_first_party_procedural_material_swatch_not_lifelike_capture"
        )


def test_first_party_material_texture_atlas_manifest_records_importable_review_only_pngs():
    material_plan = json.loads(MATERIAL_RECIPE_PATH.read_text(encoding="utf-8"))
    atlas_manifest = json.loads(
        MATERIAL_TEXTURE_ATLAS_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    atlas_generator_source = (
        REPO_ROOT / "physics/src/raftsim/procedural_material_swatches.py"
    ).read_text(encoding="utf-8")

    assert (
        atlas_manifest["schema"]
        == "raftsim.unreal.first_party_material_texture_atlas_manifest.v1"
    )
    assert (
        atlas_manifest["status"]
        == "unreal_texture2d_review_assets_created_from_first_party_procedural_atlases_not_lifelike_capture"
    )
    assert (
        atlas_manifest["material_recipe_plan"]
        == "unreal/Content/RaftSim/Rendering/first_party_procedural_material_recipes.json"
    )
    assert atlas_manifest["material_swatch_manifest"] == str(
        SWATCH_MANIFEST_RELATIVE_PATH
    )
    assert atlas_manifest["unreal_texture_asset_root"] == (
        "unreal/Content/RaftSim/Rendering/ProceduralTextureAtlases/Textures"
    )
    assert (
        atlas_manifest["unreal_texture_asset_status"]
        == "created_unreal_texture2d_review_assets_bound_to_material_instance_candidates_not_lifelike"
    )
    assert atlas_manifest["policy"]["third_party_photo_texture_inputs_used"] is False
    assert (
        atlas_manifest["policy"]["social_media_or_footage_texture_inputs_used"] is False
    )
    assert atlas_manifest["policy"]["atlas_outputs_are_first_party_procedural"] is True
    assert (
        atlas_manifest["policy"]["atlas_import_does_not_mark_any_river_lifelike"]
        is True
    )
    assert "not lifelike screenshot evidence" in atlas_manifest["current_decision"]
    assert atlas_manifest["map_semantics"]["ao_roughness_height"].startswith(
        "Packed RGB map"
    )
    assert "_apply_material_microtexture" in atlas_generator_source
    assert "_hash_unit" in atlas_generator_source
    assert "atlas-photo-microtexture" in atlas_generator_source

    river_ids = {"american_south_fork", "colorado_river", "pacuare"}
    recipe_ids = [recipe["recipe_id"] for recipe in material_plan["material_recipes"]]
    assert [
        tile["recipe_id"] for tile in atlas_manifest["recipe_tile_layout"]
    ] == recipe_ids
    assert {atlas["river_id"] for atlas in atlas_manifest["atlases"]} == river_ids

    for atlas in atlas_manifest["atlases"]:
        assert atlas["width"] == 1536
        assert atlas["height"] == 1024
        assert atlas["tile_size"] == 512
        assert (
            atlas["status"]
            == "created_unreal_texture2d_review_assets_from_importable_first_party_procedural_atlas_not_lifelike_capture"
        )
        assert atlas["recipe_ids"] == recipe_ids
        assert set(atlas["maps"]) == {"albedo", "normal", "ao_roughness_height"}
        expected_import_settings = {
            "albedo": ("TC_Default", True, "TEXTUREGROUP_World"),
            "normal": ("TC_Normalmap", False, "TEXTUREGROUP_WorldNormalMap"),
            "ao_roughness_height": ("TC_Masks", False, "TEXTUREGROUP_World"),
        }
        for map_kind, atlas_map in atlas["maps"].items():
            atlas_path = REPO_ROOT / atlas_map["path"]
            assert atlas_path.exists()
            assert _sha256(atlas_path) == atlas_map["sha256"]
            with Image.open(atlas_path) as image:
                assert image.size == (atlas["width"], atlas["height"])
                assert image.mode == "RGB"
            texture_asset = atlas_map["unreal_texture_asset"]
            assert (
                texture_asset["status"]
                == "created_unreal_texture2d_review_asset_not_lifelike"
            )
            assert texture_asset["source_png"] == atlas_map["path"]
            assert texture_asset["path"].startswith(
                "/Game/RaftSim/Rendering/ProceduralTextureAtlases/Textures/"
            )
            assert (REPO_ROOT / texture_asset["asset_file"]).exists()
            compression, srgb, lod_group = expected_import_settings[map_kind]
            assert (
                texture_asset["import_settings"]["compression_settings"] == compression
            )
            assert texture_asset["import_settings"]["srgb"] is srgb
            assert texture_asset["import_settings"]["lod_group"] == lod_group
            assert (
                texture_asset["import_settings"]["mip_gen_settings"]
                == "TMGS_FromTextureGroup"
            )
            assert (
                texture_asset["import_settings"]["source_pixel_format"] == "TSF_BGRA8"
            )


def test_source_conditioned_material_map_manifest_records_review_gated_source_maps():
    manifest = json.loads(
        SOURCE_CONDITIONED_MATERIAL_MAP_MANIFEST_PATH.read_text(encoding="utf-8")
    )

    assert manifest["schema"] == "raftsim.unreal.source_conditioned_material_maps.v1"
    assert (
        manifest["status"]
        == "generated_review_gated_source_conditioned_material_maps_not_lifelike"
    )
    assert manifest["source_capture_manifest"] == (
        "docs/environment-captures/photoreal_river_previews/environment_capture_manifest.json"
    )
    assert manifest["unreal_texture_asset_root"] == str(
        SOURCE_CONDITIONED_MATERIAL_TEXTURE_ASSET_ROOT_RELATIVE_PATH
    )
    assert (
        manifest["unreal_texture_asset_status"]
        == SOURCE_CONDITIONED_MATERIAL_TEXTURE_ASSET_STATUS
    )
    assert (
        manifest["unreal_material_instance_binding_status"]
        == "bound_to_review_material_instance_parameters_with_regenerated_capture_review_not_lifelike"
    )
    assert manifest["policy"]["source_inputs_are_manifest_recorded"] is True
    assert manifest["policy"]["third_party_social_or_outfitter_media_used"] is False
    assert manifest["policy"]["maps_are_review_gated_not_lifelike_evidence"] is True
    assert (
        manifest["policy"][
            "material_maps_must_not_hide_hazards_rescue_targets_or_physics_failures"
        ]
        is True
    )
    assert "Source-drape-colored" in manifest["map_semantics"]["macro_albedo"]
    assert manifest["map_semantics"]["material_zones"].startswith(
        "RGB material-zone weights"
    )
    assert manifest["map_semantics"]["ao_roughness_height"].startswith("Packed RGB map")
    assert manifest["map_semantics"]["normal_detail"].startswith(
        "Tangent-space normal-detail"
    )
    detail_model = manifest["source_conditioned_detail_model"]
    assert detail_model["model_id"] == "source_luma_wet_vegetation_microdetail_v2"
    assert "aerial_drape_luma_local_contrast" in detail_model["source_inputs"]
    assert "water_mask_wet_edge_band" in detail_model["source_inputs"]
    assert (
        "maps_do_not_create_or_hide_hydraulic_geometry" in detail_model["safety_bounds"]
    )
    assert "less like smooth DEM-only proxies" in detail_model["intended_visual_delta"]
    assert set(manifest["unreal_sampled_parameters"]) == {
        "SourceConditionedMacroAlbedo",
        "SourceConditionedMaterialZones",
        "SourceConditionedAORoughnessHeight",
        "SourceConditionedNormalDetail",
        "SourceConditionedZoneWeights",
        "SourceConditionedMacroAlbedoWeight",
        "SourceConditionedSurfaceResponseWeight",
        "SourceConditionedNormalDetailWeight",
    }
    assert "not lifelike approval" in manifest["current_decision"]

    river_ids = {"american_south_fork", "colorado_river", "pacuare"}
    assert {river["river_id"] for river in manifest["rivers"]} == river_ids
    for river in manifest["rivers"]:
        assert (
            river["status"]
            == "generated_review_gated_source_conditioned_material_maps_not_lifelike"
        )
        assert river["flow_band_id"]
        assert set(river["source_inputs"]) == {
            "aerial_drape_image",
            "terrain_relief_image",
            "heightfield_preview_image",
            "water_mask_image",
            "vegetation_mask_image",
        }
        for source_input in river["source_inputs"].values():
            assert (REPO_ROOT / source_input).exists()
        assert set(river["maps"]) == {
            "macro_albedo",
            "material_zones",
            "ao_roughness_height",
            "normal_detail",
        }
        assert "in-engine material assignment" in river["promotion_gate"]
        expected_import_settings = {
            "macro_albedo": (
                "SourceConditionedMacroAlbedo",
                "TC_Default",
                True,
                "TEXTUREGROUP_World",
            ),
            "material_zones": (
                "SourceConditionedMaterialZones",
                "TC_Masks",
                False,
                "TEXTUREGROUP_World",
            ),
            "ao_roughness_height": (
                "SourceConditionedAORoughnessHeight",
                "TC_Masks",
                False,
                "TEXTUREGROUP_World",
            ),
            "normal_detail": (
                "SourceConditionedNormalDetail",
                "TC_Normalmap",
                False,
                "TEXTUREGROUP_WorldNormalMap",
            ),
        }
        for map_id, map_record in river["maps"].items():
            map_path = REPO_ROOT / map_record["path"]
            assert map_path.exists()
            assert _sha256(map_path) == map_record["sha256"]
            assert map_record["width"] == 2048
            assert map_record["height"] == 2048
            parameter, compression, srgb, lod_group = expected_import_settings[map_id]
            texture_asset = map_record["unreal_texture_asset"]
            assert texture_asset["path"].startswith(
                "/Game/RaftSim/Rendering/SourceConditionedMaterialMaps/Textures/"
            )
            assert texture_asset["asset_file"].startswith(
                str(SOURCE_CONDITIONED_MATERIAL_TEXTURE_ASSET_ROOT_RELATIVE_PATH)
            )
            assert (REPO_ROOT / texture_asset["asset_file"]).exists()
            assert texture_asset["parameter"] == parameter
            assert texture_asset["source_png"] == map_record["path"]
            assert (
                texture_asset["status"]
                == "created_unreal_texture2d_review_asset_not_lifelike"
            )
            assert (
                texture_asset["import_settings"]["compression_settings"] == compression
            )
            assert texture_asset["import_settings"]["srgb"] is srgb
            assert texture_asset["import_settings"]["lod_group"] == lod_group
            assert (
                texture_asset["import_settings"]["mip_gen_settings"]
                == "TMGS_FromTextureGroup"
            )
            assert (
                texture_asset["import_settings"]["source_pixel_format"] == "TSF_BGRA8"
            )
            with Image.open(map_path) as image:
                assert image.size == (2048, 2048)
                assert image.mode == "RGB"
                extrema = image.convert("RGB").getextrema()
                assert all(
                    channel_max > channel_min for channel_min, channel_max in extrema
                )
                if map_id == "material_zones":
                    means = ImageStat.Stat(image.convert("RGB")).mean
                    assert means[0] > 30.0
                    assert means[2] > 20.0


def test_first_party_production_detail_texture_manifest_records_seamless_pbr_candidates():
    manifest = json.loads(
        PRODUCTION_DETAIL_TEXTURE_MANIFEST_PATH.read_text(encoding="utf-8")
    )

    assert (
        manifest["schema"] == "raftsim.unreal.first_party_production_detail_textures.v1"
    )
    assert (
        manifest["status"]
        == "first_party_terrain_detail_candidates_generated_and_unreal_bound_not_lifelike"
    )
    assert manifest["unreal_texture_asset_root"] == str(
        PRODUCTION_DETAIL_TEXTURE_ASSET_ROOT_RELATIVE_PATH
    )
    assert manifest["policy"]["first_party_generated_sources_only"] is True
    assert manifest["policy"]["third_party_photos_or_social_media_used"] is False
    assert (
        manifest["policy"]["terrain_detail_does_not_drive_water_or_hydraulic_geometry"]
        is True
    )
    assert {river["river_id"] for river in manifest["rivers"]} == {
        "american_south_fork",
        "colorado_river",
        "pacuare",
    }

    for river in manifest["rivers"]:
        source = REPO_ROOT / river["source"]["path"]
        assert source.exists()
        assert _sha256(source) == river["source"]["sha256"]
        assert river["source"]["input_images_used"] is False
        assert set(river["maps"]) == {"albedo", "normal", "ao_roughness_height"}
        assert 0.7 <= river["material_parameters"]["TerrainDetailAlbedoWeight"] <= 0.8
        assert 0.0 < river["material_parameters"]["TerrainDetailNormalWeight"] <= 0.25
        assert (
            0.0
            < river["material_parameters"]["TerrainDetailSurfaceResponseWeight"]
            <= 0.25
        )
        for map_id, map_data in river["maps"].items():
            path = REPO_ROOT / map_data["path"]
            assert path.exists()
            assert _sha256(path) == map_data["sha256"]
            with Image.open(path) as image:
                assert image.size == (1024, 1024)
                assert image.mode == "RGB"
                left = list(image.crop((0, 0, 1, image.height)).get_flattened_data())
                right = list(
                    image.crop(
                        (image.width - 1, 0, image.width, image.height)
                    ).get_flattened_data()
                )
                top = list(image.crop((0, 0, image.width, 1)).get_flattened_data())
                bottom = list(
                    image.crop(
                        (0, image.height - 1, image.width, image.height)
                    ).get_flattened_data()
                )
                assert left == right
                assert top == bottom
            asset = map_data["unreal_texture_asset"]
            assert asset["path"].startswith(
                "/Game/RaftSim/Rendering/ProductionDetailTextures/Textures/"
            )
            assert (REPO_ROOT / asset["asset_file"]).exists()
            assert asset["source_png"] == map_data["path"]
            if map_id == "albedo":
                assert asset["import_settings"]["srgb"] is True
                assert asset["import_settings"]["compression_settings"] == "TC_Default"
            elif map_id == "normal":
                assert asset["import_settings"]["srgb"] is False
                assert (
                    asset["import_settings"]["compression_settings"] == "TC_Normalmap"
                )
            else:
                assert asset["import_settings"]["srgb"] is False
                assert asset["import_settings"]["compression_settings"] == "TC_Masks"


def test_environment_capture_manifest_records_rendered_production_detail_inputs():
    capture_manifest = json.loads(CAPTURE_MANIFEST_PATH.read_text(encoding="utf-8"))
    production_detail_manifest = json.loads(
        PRODUCTION_DETAIL_TEXTURE_MANIFEST_PATH.read_text(encoding="utf-8")
    )

    assert capture_manifest["production_detail_texture_manifest"] == str(
        PRODUCTION_DETAIL_TEXTURE_MANIFEST_RELATIVE_PATH
    )
    assert capture_manifest["production_detail_texture_asset_root"] == str(
        PRODUCTION_DETAIL_TEXTURE_ASSET_ROOT_RELATIVE_PATH
    )
    assert (
        capture_manifest["production_detail_texture_asset_status"]
        == production_detail_manifest["unreal_integration"]["asset_status"]
    )

    detail_by_river = {
        river["river_id"]: river for river in production_detail_manifest["rivers"]
    }
    expected_source_terrain_geometry = {
        "american_south_fork": {
            "source_terrain_macro_amplitude_cm": 620.0,
            "source_terrain_local_relief_amplitude_cm": 620.0,
            "source_terrain_seam_feather_uv": 0.03,
            "source_terrain_normal_softening_blend": 0.52,
        },
        "colorado_river": {
            "source_terrain_macro_amplitude_cm": 2200.0,
            "source_terrain_local_relief_amplitude_cm": 1500.0,
            "source_terrain_seam_feather_uv": 0.035,
            "source_terrain_normal_softening_blend": 0.38,
        },
        "pacuare": {
            "source_terrain_macro_amplitude_cm": 1500.0,
            "source_terrain_local_relief_amplitude_cm": 1050.0,
            "source_terrain_seam_feather_uv": 0.035,
            "source_terrain_normal_softening_blend": 0.42,
        },
    }
    assert {capture["river_id"] for capture in capture_manifest["captures"]} == set(
        detail_by_river
    )
    for capture in capture_manifest["captures"]:
        detail_maps = detail_by_river[capture["river_id"]]["maps"]
        assert capture["terrain_detail_albedo_image"] == detail_maps["albedo"]["path"]
        assert capture["terrain_detail_normal_image"] == detail_maps["normal"]["path"]
        assert (
            capture["terrain_detail_ao_roughness_height_image"]
            == detail_maps["ao_roughness_height"]["path"]
        )
        assert (REPO_ROOT / capture["terrain_detail_albedo_image"]).exists()
        assert (REPO_ROOT / capture["terrain_detail_normal_image"]).exists()
        assert (
            REPO_ROOT / capture["terrain_detail_ao_roughness_height_image"]
        ).exists()
        for parameter, expected_value in expected_source_terrain_geometry[
            capture["river_id"]
        ].items():
            assert capture[parameter] == expected_value
        assert (
            "source DEM/heightfield geometry uses bilinear sampling"
            in capture["fidelity_note"]
        )
        assert 0.26 <= capture["water_material_emissive_fill_scale"] <= 0.28
        assert 0.18 <= capture["water_material_roughness_scale"] <= 0.22
        assert 0.28 <= capture["water_material_roughness_floor"] <= 0.34
        assert 0.18 <= capture["water_material_specular_level"] <= 0.22
        assert 0.22 <= capture["water_material_normal_intensity"] <= 0.36
        assert 0.12 <= capture["water_mesh_normal_up_blend"] <= 0.18
        assert "river ribbon preserves normals" in capture["fidelity_note"]


def test_photoreal_review_rollups_match_authoritative_capture_evidence():
    base_review = json.loads(CAPTURE_QUALITY_REVIEW_PATH.read_text(encoding="utf-8"))
    flow_review = json.loads(
        FLOW_VARIANT_CAPTURE_QUALITY_REVIEW_PATH.read_text(encoding="utf-8")
    )
    asset_plan = json.loads(ASSET_PLAN_PATH.read_text(encoding="utf-8"))
    source_plan = json.loads(SOURCE_PLAN_PATH.read_text(encoding="utf-8"))
    art_research = json.loads(ART_SOURCE_RESEARCH_PATH.read_text(encoding="utf-8"))
    gap_register = json.loads(GAP_REGISTER_PATH.read_text(encoding="utf-8"))

    detail_manifest = str(PRODUCTION_DETAIL_TEXTURE_MANIFEST_RELATIVE_PATH)
    detail_asset_root = str(PRODUCTION_DETAIL_TEXTURE_ASSET_ROOT_RELATIVE_PATH)
    detail_asset_status = "created_unreal_first_party_terrain_detail_texture_candidates_bound_to_review_material_not_lifelike"
    production_detail_checkpoint_id = "production_detail_material_checkpoint_2026_07_09"
    source_terrain_checkpoint_id = "source_terrain_geometry_checkpoint_2026_07_09"
    checkpoint_id = "water_light_response_checkpoint_2026_07_09"

    assert (
        asset_plan["unreal_integration"]["photoreal_capture_quality_summary"]
        == base_review["summary"]
    )
    assert (
        source_plan["unreal_generation"]["photoreal_capture_quality_summary"]
        == base_review["summary"]
    )
    assert (
        source_plan["unreal_generation"]["flow_variant_capture_quality_review_summary"]
        == flow_review["summary"]
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "photoreal_capture_quality_blockers"
        ]
        == base_review["summary"]["blocker_counts"]
    )

    for checkpoint in (
        asset_plan["unreal_integration"][checkpoint_id],
        source_plan["unreal_generation"][checkpoint_id],
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            checkpoint_id
        ],
        gap_register[checkpoint_id],
    ):
        assert checkpoint["production_detail_texture_manifest"] == detail_manifest
        assert checkpoint["production_detail_texture_asset_root"] == detail_asset_root
        assert (
            checkpoint["production_detail_texture_asset_status"] == detail_asset_status
        )
        assert checkpoint["base_capture_quality_summary"] == base_review["summary"]
        assert (
            checkpoint["flow_variant_capture_quality_summary"] == flow_review["summary"]
        )
        assert (
            "synthetic_capture_film_grain_disabled"
            in checkpoint["renderer_corrections"]
        )
        assert (
            "source_heightfield_bilinear_sampling_and_center_seam_feathering"
            in checkpoint["renderer_corrections"]
        )
        assert (
            "dedicated_default_lit_water_parent_isolated_from_atlas_terrain_parent"
            in checkpoint["renderer_corrections"]
        )
        assert (
            "tile_safe_first_party_water_normal_atlas_sampling"
            in checkpoint["renderer_corrections"]
        )

    assert (
        asset_plan["unreal_integration"][production_detail_checkpoint_id][
            "superseded_by"
        ]
        == checkpoint_id
    )
    assert (
        asset_plan["unreal_integration"][source_terrain_checkpoint_id]["superseded_by"]
        == checkpoint_id
    )
    water_checkpoint = asset_plan["unreal_integration"][checkpoint_id]
    comparison = water_checkpoint[
        "comparison_to_committed_production_detail_checkpoint"
    ]
    assert comparison["committed_checkpoint"] == "4fb76ae4f"
    assert comparison["prior_base_blocker_counts"]["excess_low_gradient_area"] == 6
    assert comparison["current_base_blocker_counts"]["excess_low_gradient_area"] == 5
    assert (
        comparison["prior_flow_variant_blocker_counts"]["excess_low_gradient_area"]
        == 19
    )
    assert (
        comparison["current_flow_variant_blocker_counts"]["excess_low_gradient_area"]
        == 17
    )
    assert comparison["excess_low_gradient_area_delta"] == {
        "base": -1,
        "flow_variant": -2,
    }
    source_comparison = water_checkpoint["comparison_to_source_terrain_checkpoint"]
    assert source_comparison["checkpoint"] == source_terrain_checkpoint_id
    assert (
        source_comparison["prior_base_blocker_counts"]["excess_low_gradient_area"] == 5
    )
    assert (
        source_comparison["current_base_blocker_counts"]["excess_low_gradient_area"]
        == 5
    )
    assert (
        source_comparison["prior_flow_variant_blocker_counts"][
            "excess_low_gradient_area"
        ]
        == 18
    )
    assert (
        source_comparison["current_flow_variant_blocker_counts"][
            "excess_low_gradient_area"
        ]
        == 17
    )
    assert source_comparison["excess_low_gradient_area_delta"] == {
        "base": 0,
        "flow_variant": -1,
    }


def test_first_party_material_instance_candidate_manifest_binds_each_atlas_tile():
    atlas_manifest = json.loads(
        MATERIAL_TEXTURE_ATLAS_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    source_map_manifest = json.loads(
        SOURCE_CONDITIONED_MATERIAL_MAP_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    production_detail_manifest = json.loads(
        PRODUCTION_DETAIL_TEXTURE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    candidate_manifest = json.loads(
        MATERIAL_INSTANCE_CANDIDATE_MANIFEST_PATH.read_text(encoding="utf-8")
    )

    assert (
        candidate_manifest["schema"]
        == "raftsim.unreal.first_party_material_instance_candidates.v1"
    )
    assert (
        candidate_manifest["status"]
        == "candidate_unreal_material_instance_texture_bindings_shader_parent_scene_assignment_and_review_assets_created_not_lifelike"
    )
    assert candidate_manifest["material_texture_atlas_manifest"] == str(
        TEXTURE_ATLAS_MANIFEST_RELATIVE_PATH
    )
    assert candidate_manifest["material_texture_asset_root"] == (
        "unreal/Content/RaftSim/Rendering/ProceduralTextureAtlases/Textures"
    )
    assert (
        candidate_manifest["material_texture_asset_status"]
        == "created_unreal_texture2d_review_assets_bound_to_material_instance_candidates_not_lifelike"
    )
    assert candidate_manifest["source_conditioned_material_map_manifest"] == str(
        SOURCE_CONDITIONED_MATERIAL_MAP_MANIFEST_RELATIVE_PATH
    )
    assert candidate_manifest["source_conditioned_material_texture_asset_root"] == str(
        SOURCE_CONDITIONED_MATERIAL_TEXTURE_ASSET_ROOT_RELATIVE_PATH
    )
    assert (
        candidate_manifest["source_conditioned_material_texture_asset_status"]
        == SOURCE_CONDITIONED_MATERIAL_TEXTURE_ASSET_STATUS
    )
    assert candidate_manifest["production_detail_texture_manifest"] == str(
        PRODUCTION_DETAIL_TEXTURE_MANIFEST_RELATIVE_PATH
    )
    assert candidate_manifest["production_detail_texture_asset_root"] == str(
        PRODUCTION_DETAIL_TEXTURE_ASSET_ROOT_RELATIVE_PATH
    )
    assert (
        candidate_manifest["production_detail_texture_asset_status"]
        == "created_unreal_first_party_terrain_detail_texture_candidates_bound_to_review_material_not_lifelike"
    )
    assert (
        candidate_manifest["source_conditioned_material_instance_binding_status"]
        == "bound_to_review_material_instance_parameters_with_regenerated_capture_review_not_lifelike"
    )
    assert (
        candidate_manifest["material_instance_review_asset_status"]
        == "created_unreal_material_instance_constant_review_assets_with_texture_bindings_sampler_parent_and_scene_assignment_not_lifelike"
    )
    assert candidate_manifest["atlas_sampler_review_material"] == (
        "unreal/Content/RaftSim/Materials/M_RaftSim_AtlasSampleReview.uasset"
    )
    assert (REPO_ROOT / candidate_manifest["atlas_sampler_review_material"]).exists()
    assert (
        candidate_manifest["atlas_sampler_review_material_status"]
        == "created_unreal_atlas_sampler_review_parent_material_not_lifelike"
    )
    assert (
        candidate_manifest["policy"]["candidate_paths_do_not_mark_any_river_lifelike"]
        is True
    )
    assert (
        candidate_manifest["policy"][
            "review_assets_created_do_not_mark_any_river_lifelike"
        ]
        is True
    )
    assert (
        candidate_manifest["policy"]["scene_assignments_do_not_mark_any_river_lifelike"]
        is True
    )
    assert (
        candidate_manifest["policy"][
            "source_conditioned_material_maps_are_review_gated_not_lifelike"
        ]
        is True
    )
    assert (
        candidate_manifest["policy"][
            "source_conditioned_material_zone_weights_must_preserve_hazard_readability"
        ]
        is True
    )
    assert (
        candidate_manifest["material_instance_scene_assignment_status"]
        == "assigned_review_material_instances_to_preview_map_surface_proxies_not_lifelike"
    )
    assert "M_RaftSim_AtlasSampleReview" in candidate_manifest["current_decision"]
    assert set(candidate_manifest["map_bindings"]) == {
        "AlbedoAtlas",
        "NormalAtlas",
        "AORoughnessHeightAtlas",
        "AtlasTileOrigin",
        "AtlasTileScale",
        "PreviewColor",
        "VertexColorWeight",
        "RoughnessFloor",
        "EmissiveFillScale",
        "SpecularLevel",
        "SourceConditionedMacroAlbedo",
        "SourceConditionedMaterialZones",
        "SourceConditionedAORoughnessHeight",
        "SourceConditionedNormalDetail",
        "SourceConditionedZoneWeights",
        "SourceConditionedMacroAlbedoWeight",
        "SourceConditionedSurfaceResponseWeight",
        "SourceConditionedNormalDetailWeight",
        "TerrainDetailAlbedo",
        "TerrainDetailNormal",
        "TerrainDetailAORoughnessHeight",
        "TerrainDetailUvScaleOffset",
        "TerrainDetailUvScale",
        "TerrainDetailUvOffset",
        "TerrainDetailAlbedoWeight",
        "TerrainDetailNormalWeight",
        "TerrainDetailSurfaceResponseWeight",
    }

    atlas_by_river = {atlas["river_id"]: atlas for atlas in atlas_manifest["atlases"]}
    source_maps_by_river = {
        river["river_id"]: river["maps"] for river in source_map_manifest["rivers"]
    }
    production_detail_by_river = {
        river["river_id"]: river for river in production_detail_manifest["rivers"]
    }
    tile_layout = {
        tile["recipe_id"]: tile for tile in atlas_manifest["recipe_tile_layout"]
    }
    expected_pairs = {
        (atlas["river_id"], recipe_id)
        for atlas in atlas_manifest["atlases"]
        for recipe_id in atlas["recipe_ids"]
    }
    assert {
        (candidate["river_id"], candidate["recipe_id"])
        for candidate in candidate_manifest["candidates"]
    } == expected_pairs

    for candidate in candidate_manifest["candidates"]:
        atlas = atlas_by_river[candidate["river_id"]]
        tile = tile_layout[candidate["recipe_id"]]
        assert (
            candidate["status"]
            == "created_unreal_material_instance_review_asset_with_texture_bindings_sampler_parent_and_scene_assignment_not_lifelike"
        )
        assert candidate["material_instance_path"].startswith(
            "/Game/RaftSim/Materials/MaterialInstances/"
        )
        expected_asset_file = (
            "unreal/Content/"
            + candidate["material_instance_path"].removeprefix("/Game/")
            + ".uasset"
        )
        assert candidate["created_asset_file"] == expected_asset_file
        assert (REPO_ROOT / candidate["created_asset_file"]).exists()
        is_water = candidate["recipe_id"] == "flow_dependent_water_surface_material"
        expected_parent_path = (
            "/Game/RaftSim/Materials/M_RaftSim_VertexColorWaterPreview"
            if is_water
            else "/Game/RaftSim/Materials/M_RaftSim_AtlasSampleReview"
        )
        assert candidate["parent_preview_material"] == expected_parent_path
        sampler_parent = candidate["atlas_sampler_review_material"]
        assert (
            sampler_parent["path"]
            == "/Game/RaftSim/Materials/M_RaftSim_AtlasSampleReview"
        )
        assert (
            sampler_parent["asset_file"]
            == "unreal/Content/RaftSim/Materials/M_RaftSim_AtlasSampleReview.uasset"
        )
        assert (REPO_ROOT / sampler_parent["asset_file"]).exists()
        assert (
            sampler_parent["status"]
            == "created_unreal_atlas_sampler_review_parent_material_not_lifelike"
        )
        assert set(sampler_parent["sampled_parameters"]) == {
            "AlbedoAtlas",
            "NormalAtlas",
            "AORoughnessHeightAtlas",
            "SourceConditionedMacroAlbedo",
            "SourceConditionedMaterialZones",
            "SourceConditionedAORoughnessHeight",
            "SourceConditionedNormalDetail",
            "TerrainDetailAlbedo",
            "TerrainDetailNormal",
            "TerrainDetailAORoughnessHeight",
        }
        assert set(sampler_parent["tuning_parameters"]) == {
            "AtlasTileOriginScale",
            "AtlasBlendWeight",
            "NormalIntensity",
            "RoughnessScale",
            "HeightScale",
            "PreviewColor",
            "VertexColorWeight",
            "RoughnessFloor",
            "SourceConditionedZoneWeights",
            "SourceConditionedMacroAlbedoWeight",
            "SourceConditionedSurfaceResponseWeight",
            "SourceConditionedNormalDetailWeight",
            "AtlasTileOrigin",
            "AtlasTileScale",
            "TerrainDetailUvScale",
            "TerrainDetailUvOffset",
            "TerrainDetailAlbedoWeight",
            "TerrainDetailNormalWeight",
            "TerrainDetailSurfaceResponseWeight",
        }
        assert "close-range albedo" in sampler_parent["output_wiring"]["BaseColor"]
        assert "close-range tangent normal" in sampler_parent["output_wiring"]["Normal"]
        assert (
            "packed detail red channel"
            in sampler_parent["output_wiring"]["AmbientOcclusion"]
        )
        assert (
            "packed detail green channel"
            in sampler_parent["output_wiring"]["Roughness"]
        )
        assert (
            "packed detail blue channel"
            in sampler_parent["output_wiring"]["PixelDepthOffset"]
        )
        assert (
            "no material graph component mask reads vector alpha"
            in sampler_parent["output_wiring"]["uv_compile_policy"]
        )
        review_parent = candidate["review_parent_material"]
        assert review_parent["path"] == expected_parent_path
        assert (REPO_ROOT / review_parent["asset_file"]).exists()
        if is_water:
            assert (
                review_parent["status"]
                == "created_unreal_default_lit_water_review_parent_material_not_lifelike"
            )
            assert review_parent["sampled_parameters"] == ["NormalAtlas"]
            assert set(review_parent["tuning_parameters"]) == {
                "AtlasTileOrigin",
                "AtlasTileScale",
                "NormalIntensity",
                "RoughnessScale",
                "RoughnessFloor",
                "EmissiveFillScale",
                "SpecularLevel",
            }
            assert "water normal atlas" in review_parent["output_wiring"]["Normal"]
        else:
            assert review_parent == sampler_parent
        assert candidate["atlas_tile_rect_px"] == {
            "x": tile["x"],
            "y": tile["y"],
            "width": tile["width"],
            "height": tile["height"],
        }
        assert (
            candidate["texture_bindings"]["AlbedoAtlas"]["path"]
            == atlas["maps"]["albedo"]["path"]
        )
        assert (
            candidate["texture_bindings"]["AlbedoAtlas"]["sha256"]
            == atlas["maps"]["albedo"]["sha256"]
        )
        assert (
            candidate["texture_bindings"]["NormalAtlas"]["path"]
            == atlas["maps"]["normal"]["path"]
        )
        assert (
            candidate["texture_bindings"]["NormalAtlas"]["sha256"]
            == atlas["maps"]["normal"]["sha256"]
        )
        assert (
            candidate["texture_bindings"]["AORoughnessHeightAtlas"]["path"]
            == atlas["maps"]["ao_roughness_height"]["path"]
        )
        assert (
            candidate["texture_bindings"]["AORoughnessHeightAtlas"]["sha256"]
            == atlas["maps"]["ao_roughness_height"]["sha256"]
        )
        assert (
            candidate["texture_asset_bindings"]["AlbedoAtlas"]
            == atlas["maps"]["albedo"]["unreal_texture_asset"]
        )
        assert (
            candidate["texture_asset_bindings"]["NormalAtlas"]
            == atlas["maps"]["normal"]["unreal_texture_asset"]
        )
        assert (
            candidate["texture_asset_bindings"]["AORoughnessHeightAtlas"]
            == atlas["maps"]["ao_roughness_height"]["unreal_texture_asset"]
        )
        source_maps = source_maps_by_river[candidate["river_id"]]
        assert candidate["source_conditioned_texture_bindings"] == {
            "SourceConditionedMacroAlbedo": {
                "path": source_maps["macro_albedo"]["path"],
                "sha256": source_maps["macro_albedo"]["sha256"],
            },
            "SourceConditionedMaterialZones": {
                "path": source_maps["material_zones"]["path"],
                "sha256": source_maps["material_zones"]["sha256"],
            },
            "SourceConditionedAORoughnessHeight": {
                "path": source_maps["ao_roughness_height"]["path"],
                "sha256": source_maps["ao_roughness_height"]["sha256"],
            },
            "SourceConditionedNormalDetail": {
                "path": source_maps["normal_detail"]["path"],
                "sha256": source_maps["normal_detail"]["sha256"],
            },
        }
        assert candidate["source_conditioned_texture_asset_bindings"] == {
            "SourceConditionedMacroAlbedo": source_maps["macro_albedo"][
                "unreal_texture_asset"
            ],
            "SourceConditionedMaterialZones": source_maps["material_zones"][
                "unreal_texture_asset"
            ],
            "SourceConditionedAORoughnessHeight": source_maps["ao_roughness_height"][
                "unreal_texture_asset"
            ],
            "SourceConditionedNormalDetail": source_maps["normal_detail"][
                "unreal_texture_asset"
            ],
        }
        production_detail = production_detail_by_river[candidate["river_id"]]
        assert candidate["production_detail_texture_bindings"] == {
            map_data["unreal_texture_asset"]["parameter"]: {
                "path": map_data["path"],
                "sha256": map_data["sha256"],
            }
            for map_data in production_detail["maps"].values()
        }
        for binding in candidate["texture_bindings"].values():
            bound_path = REPO_ROOT / binding["path"]
            assert bound_path.exists()
            assert _sha256(bound_path) == binding["sha256"]
        for binding in candidate["source_conditioned_texture_bindings"].values():
            bound_path = REPO_ROOT / binding["path"]
            assert bound_path.exists()
            assert _sha256(bound_path) == binding["sha256"]
        for binding in candidate["texture_asset_bindings"].values():
            assert binding["path"].startswith(
                "/Game/RaftSim/Rendering/ProceduralTextureAtlases/Textures/"
            )
            assert (REPO_ROOT / binding["asset_file"]).exists()
        for binding in candidate["source_conditioned_texture_asset_bindings"].values():
            assert binding["path"].startswith(
                "/Game/RaftSim/Rendering/SourceConditionedMaterialMaps/Textures/"
            )
            assert (REPO_ROOT / binding["asset_file"]).exists()
            assert binding["source_png"]
        for binding in candidate["production_detail_texture_asset_bindings"].values():
            assert binding["path"].startswith(
                "/Game/RaftSim/Rendering/ProductionDetailTextures/Textures/"
            )
            assert (REPO_ROOT / binding["asset_file"]).exists()
            assert binding["source_png"]
        origin_scale = candidate["expected_parameters"]["AtlasTileOriginScale"]
        assert origin_scale == [
            tile["x"] / atlas["width"],
            tile["y"] / atlas["height"],
            tile["width"] / atlas["width"],
            tile["height"] / atlas["height"],
        ]
        review_params = candidate["review_asset_parameters"]
        assert review_params["AtlasTileIndex"] == candidate["atlas_tile_index"]
        assert review_params["AtlasTileOriginScale"] == origin_scale
        assert review_params["AtlasTileOrigin"] == origin_scale[:2]
        assert review_params["AtlasTileScale"] == origin_scale[2:]
        assert review_params["ReviewAssetOnlyNotLifelike"] == 1.0
        assert review_params["TextureBindingsReviewOnlyNotLifelike"] == 1.0
        assert review_params["SamplerParentReviewOnlyNotLifelike"] == 1.0
        assert review_params["SceneAssignmentReviewOnlyNotLifelike"] == 1.0
        assert "PreviewColor" in review_params
        assert "VertexColorWeight" in review_params
        assert "RoughnessFloor" in review_params
        assert "RoughnessScaleValue" in review_params
        if is_water:
            assert "EmissiveFillScale" in review_params
            assert "SpecularLevel" in review_params
        else:
            assert "EmissiveFillScale" not in review_params
            assert "SpecularLevel" not in review_params
        assert "SourceConditionedZoneWeights" in review_params
        assert "SourceConditionedMacroAlbedoWeight" in review_params
        assert "SourceConditionedSurfaceResponseWeight" in review_params
        assert "SourceConditionedNormalDetailWeight" in review_params
        assert "TerrainDetailUvScale" in review_params
        assert "TerrainDetailUvOffset" in review_params
        assert "TerrainDetailAlbedoWeight" in review_params
        assert "TerrainDetailNormalWeight" in review_params
        assert "TerrainDetailSurfaceResponseWeight" in review_params
        assert (
            review_params["SourceConditionedMaterialAssignmentReviewOnlyNotLifelike"]
            == 1.0
        )
        assert (
            review_params["AtlasBlendWeight"]
            == "wired_to_atlas_sampler_review_material_base_color_lerp_conservative_preview_weight"
        )
        if is_water:
            assert (
                review_params["NormalIntensity"]
                == candidate["material_response_parameters"]["NormalIntensity"]
            )
        else:
            assert (
                review_params["NormalIntensity"]
                == "wired_to_atlas_sampler_review_material_normal_blend"
            )
        assert (
            review_params["RoughnessScale"]
            == "wired_to_atlas_sampler_review_material_packed_green_channel_with_roughness_floor"
        )
        assert (
            review_params["HeightScale"]
            == "wired_to_atlas_sampler_review_material_packed_blue_channel_preview_pixel_depth_offset"
        )
        material_response = candidate["material_response_parameters"]
        assert (
            review_params["RoughnessScaleValue"] == material_response["RoughnessScale"]
        )
        assert review_params["RoughnessFloor"] == material_response["RoughnessFloor"]
        if is_water:
            assert (
                review_params["EmissiveFillScale"]
                == material_response["EmissiveFillScale"]
            )
            assert review_params["SpecularLevel"] == material_response["SpecularLevel"]

    expected_water_response = {
        "american_south_fork": {
            "RoughnessScale": 0.18,
            "RoughnessFloor": 0.28,
            "EmissiveFillScale": 0.26,
            "SpecularLevel": 0.22,
            "MeshNormalUpBlend": 0.15,
            "NormalIntensity": 0.32,
        },
        "colorado_river": {
            "RoughnessScale": 0.22,
            "RoughnessFloor": 0.34,
            "EmissiveFillScale": 0.28,
            "SpecularLevel": 0.18,
            "MeshNormalUpBlend": 0.18,
            "NormalIntensity": 0.22,
        },
        "pacuare": {
            "RoughnessScale": 0.18,
            "RoughnessFloor": 0.30,
            "EmissiveFillScale": 0.26,
            "SpecularLevel": 0.22,
            "MeshNormalUpBlend": 0.12,
            "NormalIntensity": 0.36,
        },
    }
    water_candidates = {
        candidate["river_id"]: candidate
        for candidate in candidate_manifest["candidates"]
        if candidate["recipe_id"] == "flow_dependent_water_surface_material"
    }
    assert set(water_candidates) == set(expected_water_response)
    for river_id, expected_response in expected_water_response.items():
        assert (
            water_candidates[river_id]["material_response_parameters"]
            == expected_response
        )
