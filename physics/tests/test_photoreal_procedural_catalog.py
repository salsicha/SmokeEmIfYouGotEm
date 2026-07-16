# ruff: noqa: F405

from photoreal_test_support import *  # noqa: F401,F403


def test_first_party_procedural_environment_asset_plan_covers_required_layers():
    plan = json.loads(ASSET_PLAN_PATH.read_text(encoding="utf-8"))

    assert (
        plan["schema"] == "raftsim.unreal.first_party_procedural_environment_assets.v1"
    )
    assert plan["policy"]["first_party_geometry_and_materials_allowed"] is True
    assert (
        plan["policy"][
            "third_party_photos_social_media_and_footage_not_used_as_texture_or_training_sources_without_explicit_rights"
        ]
        is True
    )
    assert (
        plan["policy"][
            "procedural_layers_must_not_hide_hazards_rescue_targets_or_physics_failures"
        ]
        is True
    )

    required_layers = set(plan["required_target_layers"])
    covered_layers = {
        target_layer
        for recipe in plan["global_recipes"]
        for target_layer in recipe["target_layers"]
    }
    assert required_layers == covered_layers
    assert {
        "canyon_walls_and_valley_banks",
        "riverbed_and_shallow_shelves",
        "wet_boulders_and_contact_rocks",
        "shore_vegetation_and_deadfall",
        "tropical_canopy_and_understory",
        "water_surface_depth_turbidity_and_current_cues",
        "foam_spray_mist_and_waterfalls",
        "raft_foreground_and_oar_rig_silhouette",
        "river_specific_lighting_atmosphere_and_camera",
    }.issubset(required_layers)

    river_overrides = {river["river_id"]: river for river in plan["river_overrides"]}
    assert set(river_overrides) == {"american_south_fork", "colorado_river", "pacuare"}
    assert (
        "wet_dark_boulders_moss_leaf_litter_and_talus"
        in river_overrides["pacuare"]["priority_overrides"]
    )
    assert (
        "sandbar_and_wet_bank_release_variants"
        in river_overrides["colorado_river"]["priority_overrides"]
    )
    assert (
        "summer_commercial_flow_foam_and_exposed_rock_variants"
        in river_overrides["american_south_fork"]["priority_overrides"]
    )
    assert (
        "translucent_surface_glints_foam_flecks_canyon_haze_and_rainforest_spray_mist"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "source_drape_vertex_color_terrain_material_blend"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "source_drape_albedo_normalization"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_feathered_source_drape_microtiles"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "flow_aware_bank_undercut_shelf_relief"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "terrain_proxy_luma_floor"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "shadowless_terrain_albedo_review_capture_material"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_irregular_shoreline_edge_breakup"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_source_masked_shoreline_lip_overhang_edge_breakup"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "mask_aware_ground_cover_and_canopy_cards"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "biome_specific_deadfall_grass_root_ecology_props"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_biome_foliage_silhouette_proxy_layers"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_dense_biome_foliage_layer_proxy_clusters"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_instanced_procedural_foliage_equivalent_scaffold"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_procedural_leaf_cluster_geometry"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_organic_canopy_leaf_spray_breakup"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_organic_branch_frond_lattice_foliage"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_fine_twig_canopy_lace_foliage"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_photographic_foliage_tone_calibration"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_foliage_crown_depth_and_leaflet_breakup"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_procedural_only_foliage_review_path"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_procedural_canopy_height_massing_profile"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_procedural_canopy_tone_shadow_profile"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_foliage_card_canopy_artifact_demotion"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_square_foliage_source_card_artifact_demotion"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_remaining_square_card_cull"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_blocky_bank_ecology_and_sphere_foliage_cull"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_source_masked_bank_bar_microgeometry"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_near_field_riverbed_debris_and_pebble_dressing"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "guide_seat_foliage_setback_and_scale_tuning"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "flow_aware_waterline_pebble_scatter"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_irregular_rock_geometry_variants"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_boulder_wetness_abrasion_moss_surface_variants"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_boulder_crevice_shadow_and_albedo_tuning"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "near_camera_boulder_readability_clearance"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "near_camera_boulder_occlusion_demotion"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "lit_vertex_color_water_gradients"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_lit_water_normal_response_scaffold"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_photographic_water_exposure_calibration"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_photographic_color_grade_palette_compression"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_near_field_water_surface_grain"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_near_camera_water_macro_ripple_mottle"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_base_water_depth_current_grading"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_base_water_flow_thread_texture"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_base_water_center_guide_stripe_breakup"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_base_water_cross_channel_breakup"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_base_water_residual_center_seam_erase"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_dark_micro_ripple_artifact_demotion"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_flow_cued_water_foam_slick_mottle"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "flow_aware_water_mesh_undulation"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_smoothed_near_field_water_surface_faceting_demotion"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "flow_band_depth_texture_ribbons"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "flow_aware_water_surface_chop_and_turbidity_patches"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_turbidity_depth_patch_artifact_demotion"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "flow_aware_micro_ripple_glints"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "near_frame_water_ribbon_occlusion_demotion"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_water_shader_depth_reflection_refraction_scaffold"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_shallow_water_clarity_and_aeration_layer"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_flow_dependent_hydraulic_aeration_spray"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "near_camera_water_scaffold_readability_clearance"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "low_occlusion_far_field_water_shader_scaffold"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_remaining_water_overlay_slab_demotion"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_pale_water_foam_slash_demotion"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_long_dark_water_streak_demotion"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_current_streak_waterline_artifact_demotion"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_central_water_scaffold_plate_demotion"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_material_recipe_manifest_required"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "softened_source_drape_overlay"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "source_aware_bank_breakup_texture_patches"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "soft_feathered_terrain_material_patches"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_terrain_material_layer_facets_and_slope_shadow_patches"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_landscape_nanite_material_layer_scaffold"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_terrain_erosion_rill_and_bank_gully_detail"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_lit_terrain_vertex_color_material"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "soft_lit_terrain_vertex_color_review_material"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_photographic_terrain_emissive_calibration"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_terrain_contrast_and_normal_calibration"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_bounded_terrain_ambient_fill"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_base_terrain_material_grain_and_microrelief"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_source_aware_terrain_photo_mottle_and_microrelief"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_source_conditioned_far_bank_albedo_calibration"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_broad_slope_terrain_exposure_fill"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_source_aware_macro_terrain_ridge_facets"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_source_aware_terrain_slope_facet_texture"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_source_aware_terrain_surface_granularity"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_source_aware_riparian_canopy_mass_texture"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_rainforest_river_eye_slope_texture"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_source_overlay_plate_artifact_demotion"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_demoted_terrain_overlay_striping"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_source_drape_smoothing_pass"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_segmented_wet_bank_ribbons"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_graphic_waterline_ribbon_demotion"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_near_frame_shoreline_scaffold_demotion"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_pale_bank_shoreline_scaffold_slash_demotion"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_demoted_source_detail_contours"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_post_contour_terrain_readability_fill"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "boulder_contact_foam_lace"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "pacuare_waterfall_curtain_plunge_mist_and_runout_proxies"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "river_specific_cloud_haze_and_horizon_backdrop_cards"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_source_aware_sky_gradient_and_atmosphere_depth_layers"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_guide_seat_raft_and_oar_foreground_proxies"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_refined_raft_oar_foreground_proxy"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_rounded_raft_oar_foreground_proxy"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_tagged_river_eye_foreground_proxy_cull"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_river_eye_near_field_dressing_cull"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_dedicated_river_eye_downstream_capture_camera"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_centerline_following_river_eye_capture_camera"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_low_luma_foreground_raft_proxy_demotion"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_textured_river_eye_center_artifact_cover"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "photoreal_capture_quality_review_blockers_recorded"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_post_seam_water_surface_grain"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_water_luma_floor_blocker_reduction"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_low_specular_water_capture_material_tuning"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_capture_camera_flat_blue_field_reduction"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_foreground_raft_luma_blocker_reduction"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_near_field_water_source_tile_demotion"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_near_field_water_patch_tile_breakup_demotion"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_continuous_near_field_water_current_blend"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_water_review_material_source_texture_tile_cull"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_near_field_inboard_bank_shelf_cull"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_near_camera_inwater_debris_occlusion_cull"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_integrated_base_water_chroma_microbreakup"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_source_aware_tapered_water_chroma_microbreakup"
        not in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_capture_quality_water_texture_fleck_cards"
        not in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_integrated_water_fleck_microtexture"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_integrated_water_bank_entropy_edge_detail"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_integrated_river_eye_water_entropy_mottle"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        plan["unreal_integration"]["material_recipe_manifest"]
        == "unreal/Content/RaftSim/Rendering/first_party_procedural_material_recipes.json"
    )
    assert set(plan["unreal_integration"]["capture_manifest_fields"]) == {
        "procedural_asset_plan",
        "procedural_material_recipe_plan",
        "first_party_material_texture_atlas_manifest",
        "first_party_material_instance_candidate_manifest",
        "first_party_material_texture_asset_root",
        "first_party_material_texture_asset_status",
        "first_party_atlas_sampler_review_material",
        "first_party_atlas_sampler_review_material_status",
        "first_party_material_instance_review_asset_root",
        "first_party_material_instance_review_asset_status",
        "first_party_material_instance_scene_assignment_status",
        "source_conditioned_material_map_manifest",
        "source_conditioned_material_texture_asset_root",
        "source_conditioned_material_texture_asset_status",
        "source_conditioned_material_instance_binding_status",
    }
    assert plan["unreal_integration"]["material_texture_atlas_manifest"] == str(
        TEXTURE_ATLAS_MANIFEST_RELATIVE_PATH
    )
    assert plan["unreal_integration"][
        "source_conditioned_material_map_manifest"
    ] == str(SOURCE_CONDITIONED_MATERIAL_MAP_MANIFEST_RELATIVE_PATH)
    assert (
        plan["unreal_integration"]["source_conditioned_material_map_status"]
        == "generated_review_gated_source_conditioned_material_maps_not_lifelike"
    )
    assert plan["unreal_integration"]["source_conditioned_material_map_summary"] == {
        "river_count": 3,
        "map_count": 12,
        "map_size_px": 2048,
        "map_ids": [
            "macro_albedo",
            "material_zones",
            "ao_roughness_height",
            "normal_detail",
        ],
    }
    assert plan["unreal_integration"][
        "source_conditioned_material_texture_asset_root"
    ] == str(SOURCE_CONDITIONED_MATERIAL_TEXTURE_ASSET_ROOT_RELATIVE_PATH)
    assert (
        plan["unreal_integration"]["source_conditioned_material_texture_asset_status"]
        == SOURCE_CONDITIONED_MATERIAL_TEXTURE_ASSET_STATUS
    )
    assert (
        plan["unreal_integration"][
            "source_conditioned_material_instance_binding_status"
        ]
        == "bound_to_review_material_instance_parameters_with_regenerated_capture_review_not_lifelike"
    )
    assert (
        plan["unreal_integration"]["material_instance_candidate_manifest"]
        == "unreal/Content/RaftSim/Rendering/first_party_material_instance_candidates.json"
    )
    assert (
        "first_party_importable_material_texture_atlas_candidates"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_material_texture_atlas_vertex_color_application"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_material_texture_atlas_normal_packed_surface_response"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "source_conditioned_material_map_manifest_recorded"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "source_conditioned_macro_albedo_material_maps_recorded"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "source_conditioned_material_zone_maps_recorded"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "source_conditioned_ao_roughness_height_maps_recorded"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "source_conditioned_normal_detail_maps_recorded"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "source_conditioned_normal_detail_material_blend_recorded"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "source_conditioned_material_texture2d_review_assets_declared"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "source_conditioned_material_instance_texture_bindings_recorded"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "source_conditioned_material_zone_weight_controls_recorded"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "source_conditioned_shader_graph_sampler_wiring_recorded"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_material_instance_candidate_manifest_required"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_material_instance_review_assets_created"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_material_texture2d_review_assets_created"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_material_instance_texture_asset_bindings_recorded"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_atlas_sampler_review_parent_material_created"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_material_shader_graph_sampler_wiring_recorded"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "first_party_material_instance_scene_assignment_recorded"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        plan["unreal_integration"]["material_texture_asset_root"]
        == "unreal/Content/RaftSim/Rendering/ProceduralTextureAtlases/Textures"
    )
    assert (
        plan["unreal_integration"]["material_texture_asset_status"]
        == "created_unreal_texture2d_review_assets_bound_to_material_instance_candidates_not_lifelike"
    )
    assert (
        plan["unreal_integration"]["material_instance_review_asset_root"]
        == "unreal/Content/RaftSim/Materials/MaterialInstances"
    )
    assert (
        plan["unreal_integration"]["material_instance_review_asset_status"]
        == "created_unreal_material_instance_constant_review_assets_with_texture_bindings_sampler_parent_and_scene_assignment_not_lifelike"
    )
    assert (
        plan["unreal_integration"]["atlas_sampler_review_material"]
        == "unreal/Content/RaftSim/Materials/M_RaftSim_AtlasSampleReview.uasset"
    )
    assert (
        REPO_ROOT / plan["unreal_integration"]["atlas_sampler_review_material"]
    ).exists()
    assert (
        plan["unreal_integration"]["atlas_sampler_review_material_status"]
        == "created_unreal_atlas_sampler_review_parent_material_not_lifelike"
    )
    assert plan["unreal_integration"]["photoreal_capture_quality_review"] == str(
        CAPTURE_QUALITY_REVIEW_RELATIVE_PATH
    )
    assert (
        plan["unreal_integration"]["photoreal_capture_quality_review_status"]
        == EXPECTED_CAPTURE_QUALITY_STATUS
    )
    assert (
        plan["unreal_integration"]["photoreal_capture_quality_summary"]["capture_count"]
        == 6
    )
    assert (
        plan["unreal_integration"]["photoreal_capture_quality_summary"][
            "blocking_capture_count"
        ]
        == 6
    )
    assert (
        plan["unreal_integration"]["photoreal_capture_quality_summary"][
            "blocker_counts"
        ][EXPECTED_CAPTURE_BLOCKER_ID]
        == 6
    )
    assert plan["unreal_integration"]["photoreal_human_lifelike_review_handoff"] == str(
        HUMAN_LIFELIKE_REVIEW_HANDOFF_RELATIVE_PATH
    )
    assert (
        plan["unreal_integration"]["photoreal_human_lifelike_review_handoff_status"]
        == "awaiting_human_lifelike_review_not_approved"
    )
    assert (
        plan["unreal_integration"]["photoreal_human_lifelike_review_handoff_summary"][
            "open_human_review_gate_count"
        ]
        == 21
    )
    assert plan["unreal_integration"]["photoreal_human_lifelike_review_packet"] == str(
        HUMAN_LIFELIKE_REVIEW_PACKET_RELATIVE_PATH
    )
    assert (
        plan["unreal_integration"]["photoreal_human_lifelike_review_packet_status"]
        == "awaiting_human_lifelike_review_not_approved"
    )
    assert plan["unreal_integration"][
        "photoreal_human_lifelike_review_packet_summary"
    ] == {
        "river_count": 3,
        "capture_count": 6,
        "review_domain_count": 7,
        "open_human_review_gate_count": 21,
    }
    assert plan["unreal_integration"][
        "photoreal_human_lifelike_review_results_template"
    ] == str(HUMAN_LIFELIKE_REVIEW_RESULTS_TEMPLATE_RELATIVE_PATH)
    assert (
        plan["unreal_integration"][
            "photoreal_human_lifelike_review_results_template_status"
        ]
        == "awaiting_external_human_review_inputs_not_approved"
    )
    assert plan["unreal_integration"][
        "photoreal_human_lifelike_review_results_template_summary"
    ] == {
        "river_count": 3,
        "capture_count": 6,
        "review_domain_count": 7,
        "open_review_result_count": 21,
        "approved_river_count": 0,
    }
    assert (
        "first_party_integrated_corridor_water_terrain_capture_grade"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "automated_capture_quality_gate_passed_without_proxy_blockers"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "photoreal_human_lifelike_review_handoff_recorded"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "photoreal_human_lifelike_review_packet_recorded"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "zero_blocker_capture_set_review_packet_markdown_recorded"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "photoreal_human_lifelike_review_results_template_recorded"
        in plan["unreal_integration"]["current_renderer_coverage"]
    )
    assert (
        "shader_graph_sampler_wiring_for_albedo_normal_ao_roughness_height_atlas_maps"
        not in plan["unreal_integration"]["missing_renderer_coverage_before_lifelike"]
    )
    assert (
        "automated_capture_quality_gate_passed_without_proxy_blockers"
        not in plan["unreal_integration"]["missing_renderer_coverage_before_lifelike"]
    )
    assert (
        "human_art_guide_and_geospatial_lifelike_review_after_automated_gate"
        in plan["unreal_integration"]["missing_renderer_coverage_before_lifelike"]
    )
    assert (
        "replace_visible_capture_quality_water_fleck_cards_with_integrated_water_material_or_vfx"
        not in plan["unreal_integration"]["missing_renderer_coverage_before_lifelike"]
    )
    assert (
        "production_material_instances_using_texture_atlases_normal_ao_roughness_height_or_rights_cleared_equivalent_maps"
        in plan["unreal_integration"]["missing_renderer_coverage_before_lifelike"]
    )
    assert (
        "review_material_instance_scene_assignment_capture_review_and_production_promotion"
        in plan["unreal_integration"]["missing_renderer_coverage_before_lifelike"]
    )
    assert (
        "unreal_texture_asset_import_settings_for_first_party_atlases_or_rights_cleared_equivalent_maps"
        not in plan["unreal_integration"]["missing_renderer_coverage_before_lifelike"]
    )


def test_first_party_procedural_material_recipe_catalog_covers_rivers_and_layers():
    asset_plan = json.loads(ASSET_PLAN_PATH.read_text(encoding="utf-8"))
    material_plan = json.loads(MATERIAL_RECIPE_PATH.read_text(encoding="utf-8"))

    assert (
        material_plan["schema"]
        == "raftsim.unreal.first_party_procedural_material_recipes.v1"
    )
    assert (
        material_plan["parent_asset_plan"]
        == "unreal/Content/RaftSim/Rendering/first_party_procedural_environment_assets.json"
    )
    assert material_plan["review_swatch_manifest"] == str(SWATCH_MANIFEST_RELATIVE_PATH)
    assert material_plan["importable_texture_atlas_manifest"] == str(
        TEXTURE_ATLAS_MANIFEST_RELATIVE_PATH
    )
    assert material_plan["source_conditioned_material_map_manifest"] == str(
        SOURCE_CONDITIONED_MATERIAL_MAP_MANIFEST_RELATIVE_PATH
    )
    assert (
        material_plan["source_conditioned_material_map_status"]
        == "generated_review_gated_source_conditioned_material_maps_not_lifelike"
    )
    assert material_plan["source_conditioned_material_map_summary"]["river_count"] == 3
    assert material_plan["source_conditioned_material_map_summary"]["map_count"] == 12
    assert (
        "normal_detail"
        in material_plan["source_conditioned_material_map_summary"]["map_ids"]
    )
    assert material_plan["source_conditioned_material_texture_asset_root"] == str(
        SOURCE_CONDITIONED_MATERIAL_TEXTURE_ASSET_ROOT_RELATIVE_PATH
    )
    assert (
        material_plan["source_conditioned_material_texture_asset_status"]
        == SOURCE_CONDITIONED_MATERIAL_TEXTURE_ASSET_STATUS
    )
    assert (
        material_plan["source_conditioned_material_instance_binding_status"]
        == "bound_to_review_material_instance_parameters_with_regenerated_capture_review_not_lifelike"
    )
    assert (
        material_plan["material_instance_candidate_manifest"]
        == "unreal/Content/RaftSim/Rendering/first_party_material_instance_candidates.json"
    )
    assert (
        material_plan["policy"]["third_party_photo_texture_use_without_item_rights"]
        is False
    )
    assert (
        material_plan["policy"][
            "procedural_materials_must_preserve_hazard_and_rescue_readability"
        ]
        is True
    )
    assert (
        material_plan["policy"][
            "water_visuals_must_not_hide_physics_or_conservation_failures"
        ]
        is True
    )

    required_layers = set(asset_plan["required_target_layers"])
    covered_layers = {
        target_layer
        for recipe in material_plan["material_recipes"]
        for target_layer in recipe["target_layers"]
    }
    assert required_layers == covered_layers

    preview_materials = {
        material["material_path"]
        for material in material_plan["active_preview_materials"]
    }
    preview_materials_by_path = {
        material["material_path"]: material
        for material in material_plan["active_preview_materials"]
    }
    assert {
        "/Game/RaftSim/Materials/M_RaftSim_TerrainVertexColorLitPreview",
        "/Game/RaftSim/Materials/M_RaftSim_VertexColorPreview",
        "/Game/RaftSim/Materials/M_RaftSim_LitColorPreview",
        "/Game/RaftSim/Materials/M_RaftSim_VertexColorWaterPreview",
        "/Game/RaftSim/Materials/M_RaftSim_TranslucentColorPreview",
    }.issubset(preview_materials)
    for material_path in {
        "/Game/RaftSim/Materials/M_RaftSim_TerrainVertexColorLitPreview",
        "/Game/RaftSim/Materials/M_RaftSim_VertexColorPreview",
        "/Game/RaftSim/Materials/M_RaftSim_LitColorPreview",
        "/Game/RaftSim/Materials/M_RaftSim_VertexColorWaterPreview",
    }:
        assert (
            "first_party_material_texture_atlas_albedo_vertex_color_tints"
            in preview_materials_by_path[material_path]["current_use"]
        )
        assert (
            "first_party_material_texture_atlas_normal_packed_surface_response"
            in preview_materials_by_path[material_path]["current_use"]
        )

    river_ids = {"american_south_fork", "colorado_river", "pacuare"}
    assert {
        profile["river_id"] for profile in material_plan["river_profiles"]
    } == river_ids

    recipe_ids = {recipe["recipe_id"] for recipe in material_plan["material_recipes"]}
    assert {
        "terrain_bank_layered_material",
        "wet_boulder_contact_material_set",
        "biome_foliage_groundcover_materials",
        "flow_dependent_water_surface_material",
        "foam_spray_mist_atmosphere_materials",
        "raft_foreground_review_materials",
    }.issubset(recipe_ids)

    for recipe in material_plan["material_recipes"]:
        assert set(recipe["river_bindings"]) == river_ids
        assert recipe["preview_fallback_material"] in preview_materials
        assert recipe["required_source_inputs"]
        assert recipe["tunable_parameters"]
        assert recipe["promotion_gate"]

    terrain_recipe = next(
        recipe
        for recipe in material_plan["material_recipes"]
        if recipe["recipe_id"] == "terrain_bank_layered_material"
    )
    wet_boulder_recipe = next(
        recipe
        for recipe in material_plan["material_recipes"]
        if recipe["recipe_id"] == "wet_boulder_contact_material_set"
    )
    water_recipe = next(
        recipe
        for recipe in material_plan["material_recipes"]
        if recipe["recipe_id"] == "flow_dependent_water_surface_material"
    )
    pacuare_terrain = terrain_recipe["river_bindings"]["pacuare"]
    raft_recipe = next(
        recipe
        for recipe in material_plan["material_recipes"]
        if recipe["recipe_id"] == "raft_foreground_review_materials"
    )
    foliage_recipe = next(
        recipe
        for recipe in material_plan["material_recipes"]
        if recipe["recipe_id"] == "biome_foliage_groundcover_materials"
    )
    atmosphere_recipe = next(
        recipe
        for recipe in material_plan["material_recipes"]
        if recipe["recipe_id"] == "foam_spray_mist_atmosphere_materials"
    )
    assert (
        terrain_recipe["preview_fallback_material"]
        == "/Game/RaftSim/Materials/M_RaftSim_TerrainVertexColorLitPreview"
    )
    assert "lit_terrain_vertex_color_roughness" in terrain_recipe["procedural_tokens"]
    assert "source_drape_albedo_normalization" in terrain_recipe["procedural_tokens"]
    assert "source_drape_microtile_feathering" in terrain_recipe["procedural_tokens"]
    assert "terrain_lit_microtile_edge_fade" in terrain_recipe["procedural_tokens"]
    assert "mask_sampled_microtile_mottle" in terrain_recipe["procedural_tokens"]
    assert "source_drape_microtile_size" in terrain_recipe["tunable_parameters"]
    assert "source_drape_microtile_edge_feather" in terrain_recipe["tunable_parameters"]
    assert "source_drape_microtile_weight" in terrain_recipe["tunable_parameters"]
    assert "terrain_proxy_luma_floor" in terrain_recipe["procedural_tokens"]
    assert "soft_feathered_terrain_patch_edges" in terrain_recipe["procedural_tokens"]
    assert (
        "flow_aware_bank_undercut_shelf_relief" in terrain_recipe["procedural_tokens"]
    )
    assert "soft_lit_terrain_review_mode" in terrain_recipe["procedural_tokens"]
    assert (
        "photographic_terrain_emissive_calibration"
        in terrain_recipe["procedural_tokens"]
    )
    assert "terrain_contrast_luma_floor" in terrain_recipe["procedural_tokens"]
    assert "proxy_terrain_normal_softening" in terrain_recipe["procedural_tokens"]
    assert "bounded_terrain_ambient_fill" in terrain_recipe["procedural_tokens"]
    assert "base_terrain_material_grain" in terrain_recipe["procedural_tokens"]
    assert "base_terrain_microrelief" in terrain_recipe["procedural_tokens"]
    assert "source_masked_terrain_mottle" in terrain_recipe["procedural_tokens"]
    assert "source_aware_terrain_photo_mottle" in terrain_recipe["procedural_tokens"]
    assert "source_conditioned_far_bank_albedo" in terrain_recipe["procedural_tokens"]
    assert (
        "source_conditioned_far_bank_microrelief" in terrain_recipe["procedural_tokens"]
    )
    assert (
        "source_conditioned_terrain_luma_target" in terrain_recipe["procedural_tokens"]
    )
    assert "broad_slope_terrain_exposure_fill" in terrain_recipe["procedural_tokens"]
    assert "broad_slope_terrain_luma_target" in terrain_recipe["procedural_tokens"]
    assert (
        "broad_slope_terrain_low_frequency_relief"
        in terrain_recipe["procedural_tokens"]
    )
    assert "broad_slope_source_drape_fill" in terrain_recipe["procedural_tokens"]
    assert (
        "broad_slope_sun_face_and_ambient_crease_variation"
        in terrain_recipe["procedural_tokens"]
    )
    assert (
        "source_aware_terrain_slope_facet_texture"
        in terrain_recipe["procedural_tokens"]
    )
    assert (
        "source_aware_terrain_slope_facet_relief" in terrain_recipe["procedural_tokens"]
    )
    assert (
        "slope_facet_sun_face_and_crease_color" in terrain_recipe["procedural_tokens"]
    )
    assert (
        "source_aware_terrain_surface_granularity"
        in terrain_recipe["procedural_tokens"]
    )
    assert (
        "terrain_granularity_mineral_leaf_litter_flecks"
        in terrain_recipe["procedural_tokens"]
    )
    assert "terrain_granularity_microrelief" in terrain_recipe["procedural_tokens"]
    assert (
        "source_aware_riparian_canopy_mass_texture"
        in terrain_recipe["procedural_tokens"]
    )
    assert "riparian_canopy_understory_shadow" in terrain_recipe["procedural_tokens"]
    assert "riparian_canopy_leaf_highlight" in terrain_recipe["procedural_tokens"]
    assert (
        "source_aware_riparian_canopy_mass_relief"
        in terrain_recipe["procedural_tokens"]
    )
    assert "rainforest_river_eye_slope_texture" in terrain_recipe["procedural_tokens"]
    assert (
        "rainforest_river_eye_root_vein_mottle" in terrain_recipe["procedural_tokens"]
    )
    assert (
        "rainforest_river_eye_slope_microrelief" in terrain_recipe["procedural_tokens"]
    )
    assert (
        "source_overlay_plate_artifact_demotion" in terrain_recipe["procedural_tokens"]
    )
    assert (
        "demoted_source_aerial_microtile_weight" in terrain_recipe["procedural_tokens"]
    )
    assert (
        "terrain_material_overlay_plate_demotion" in terrain_recipe["procedural_tokens"]
    )
    assert (
        "landscape_nanite_overlay_plate_demotion" in terrain_recipe["procedural_tokens"]
    )
    assert "pale_bank_material_slash_demotion" in terrain_recipe["procedural_tokens"]
    assert (
        "pale_landscape_scaffold_slash_demotion" in terrain_recipe["procedural_tokens"]
    )
    assert "bank_cliff_mineral_speckle" in terrain_recipe["procedural_tokens"]
    assert (
        "mask_guided_leaf_litter_or_sand_mottle" in terrain_recipe["procedural_tokens"]
    )
    assert "demoted_terrain_overlay_striping" in terrain_recipe["procedural_tokens"]
    assert "source_drape_smoothing_pass" in terrain_recipe["procedural_tokens"]
    assert "segmented_wet_bank_ribbons" in terrain_recipe["procedural_tokens"]
    assert "graphic_waterline_ribbon_demotion" in terrain_recipe["procedural_tokens"]
    assert (
        "pale_shoreline_slash_artifact_demotion" in terrain_recipe["procedural_tokens"]
    )
    assert (
        "photographic_waterline_visibility_breakup"
        in terrain_recipe["procedural_tokens"]
    )
    assert (
        "near_frame_shoreline_scaffold_demotion" in terrain_recipe["procedural_tokens"]
    )
    assert "demoted_source_detail_contours" in terrain_recipe["procedural_tokens"]
    assert (
        "post_contour_terrain_readability_fill" in terrain_recipe["procedural_tokens"]
    )
    assert "wet_bank_ribbon_segment_breakup" in terrain_recipe["tunable_parameters"]
    assert "wet_bank_ribbon_width" in terrain_recipe["tunable_parameters"]
    assert "wet_bank_ribbon_color_gain" in terrain_recipe["tunable_parameters"]
    assert (
        "graphic_waterline_ribbon_visibility_gain"
        in terrain_recipe["tunable_parameters"]
    )
    assert (
        "graphic_waterline_ribbon_width_scale" in terrain_recipe["tunable_parameters"]
    )
    assert "near_frame_shoreline_ribbon_gain" in terrain_recipe["tunable_parameters"]
    assert "near_frame_shoreline_ribbon_width" in terrain_recipe["tunable_parameters"]
    assert "source_detail_contour_band_count" in terrain_recipe["tunable_parameters"]
    assert "post_contour_terrain_ambient_fill" in terrain_recipe["tunable_parameters"]
    assert "bank_toe_undercut_depth" in terrain_recipe["tunable_parameters"]
    assert "waterline_shelf_lift" in terrain_recipe["tunable_parameters"]
    assert "terrain_emissive_lift" in terrain_recipe["tunable_parameters"]
    assert "terrain_specular_gain" in terrain_recipe["tunable_parameters"]
    assert "terrain_patch_edge_feather_width" in terrain_recipe["tunable_parameters"]
    assert "terrain_patch_center_feature_blend" in terrain_recipe["tunable_parameters"]
    assert "terrain_patch_feature_blend_limit" in terrain_recipe["tunable_parameters"]
    assert (
        "proxy_terrain_normal_softening_blend" in terrain_recipe["tunable_parameters"]
    )
    assert "terrain_ambient_fill" in terrain_recipe["tunable_parameters"]
    assert (
        "base_terrain_material_grain_strength" in terrain_recipe["tunable_parameters"]
    )
    assert "base_terrain_microrelief_cm" in terrain_recipe["tunable_parameters"]
    assert "terrain_photo_mottle_strength" in terrain_recipe["tunable_parameters"]
    assert "far_bank_source_drape_gain" in terrain_recipe["tunable_parameters"]
    assert (
        "source_conditioned_far_bank_albedo_strength"
        in terrain_recipe["tunable_parameters"]
    )
    assert (
        "source_conditioned_far_bank_microrelief_cm"
        in terrain_recipe["tunable_parameters"]
    )
    assert (
        "source_conditioned_terrain_luma_target" in terrain_recipe["tunable_parameters"]
    )
    assert (
        "broad_slope_terrain_exposure_fill_strength"
        in terrain_recipe["tunable_parameters"]
    )
    assert "broad_slope_terrain_luma_target" in terrain_recipe["tunable_parameters"]
    assert (
        "broad_slope_terrain_low_frequency_relief_cm"
        in terrain_recipe["tunable_parameters"]
    )
    assert "broad_slope_source_drape_gain" in terrain_recipe["tunable_parameters"]
    assert (
        "broad_slope_material_variation_strength"
        in terrain_recipe["tunable_parameters"]
    )
    assert (
        "source_aware_terrain_slope_facet_texture_strength"
        in terrain_recipe["tunable_parameters"]
    )
    assert (
        "source_aware_terrain_slope_facet_relief_cm"
        in terrain_recipe["tunable_parameters"]
    )
    assert "slope_facet_strata_breakup_strength" in terrain_recipe["tunable_parameters"]
    assert (
        "source_aware_terrain_surface_granularity_strength"
        in terrain_recipe["tunable_parameters"]
    )
    assert (
        "terrain_surface_granularity_relief_cm" in terrain_recipe["tunable_parameters"]
    )
    assert (
        "terrain_surface_granularity_cell_scale" in terrain_recipe["tunable_parameters"]
    )
    assert (
        "riparian_canopy_mass_texture_strength" in terrain_recipe["tunable_parameters"]
    )
    assert (
        "riparian_canopy_understory_shadow_gain" in terrain_recipe["tunable_parameters"]
    )
    assert "riparian_canopy_leaf_highlight_gain" in terrain_recipe["tunable_parameters"]
    assert "riparian_canopy_mass_relief_cm" in terrain_recipe["tunable_parameters"]
    assert (
        "rainforest_river_eye_slope_texture_strength"
        in terrain_recipe["tunable_parameters"]
    )
    assert (
        "rainforest_river_eye_slope_relief_cm" in terrain_recipe["tunable_parameters"]
    )
    assert "source_overlay_microtile_density" in terrain_recipe["tunable_parameters"]
    assert (
        "source_overlay_microtile_edge_lift_cm" in terrain_recipe["tunable_parameters"]
    )
    assert "source_overlay_plate_contrast_gain" in terrain_recipe["tunable_parameters"]
    assert (
        "terrain_material_overlay_plate_demotion"
        in terrain_recipe["tunable_parameters"]
    )
    assert (
        "landscape_nanite_overlay_plate_demotion"
        in terrain_recipe["tunable_parameters"]
    )
    assert (
        "pale_shoreline_slash_artifact_demotion" in terrain_recipe["tunable_parameters"]
    )
    assert "pale_bank_material_slash_demotion" in terrain_recipe["tunable_parameters"]
    assert (
        "pale_landscape_scaffold_slash_demotion" in terrain_recipe["tunable_parameters"]
    )
    assert "bank_cliff_mottle_scale_m" in terrain_recipe["tunable_parameters"]
    assert "terrain_photo_mottle_microrelief_cm" in terrain_recipe["tunable_parameters"]
    assert "base_terrain_mesh_resolution" in terrain_recipe["tunable_parameters"]
    assert "terrain_overlay_actor_count" in terrain_recipe["tunable_parameters"]
    assert "terrain_overlay_stripe_contrast" in terrain_recipe["tunable_parameters"]
    assert "source_drape_luma_clamp" in terrain_recipe["tunable_parameters"]
    assert "source_drape_tile_density" in terrain_recipe["tunable_parameters"]
    assert (
        "terrain_overlay_smoothing_actor_count" in terrain_recipe["tunable_parameters"]
    )
    assert "terrain_patch_height_feather" in terrain_recipe["tunable_parameters"]
    assert "irregular_shoreline_edge_breakup" in terrain_recipe["procedural_tokens"]
    assert "waterline_scallop_shadow" in terrain_recipe["procedural_tokens"]
    assert "source_masked_bank_toe_deposit" in terrain_recipe["procedural_tokens"]
    assert "shoreline_edge_patch_count" in terrain_recipe["tunable_parameters"]
    assert "shoreline_edge_patch_width" in terrain_recipe["tunable_parameters"]
    assert "shoreline_edge_patch_length" in terrain_recipe["tunable_parameters"]
    assert "terrain_erosion_rill" in terrain_recipe["procedural_tokens"]
    assert "bank_gully_shadow" in terrain_recipe["procedural_tokens"]
    assert "downslope_deposit_rim" in terrain_recipe["procedural_tokens"]
    assert "source_masked_bank_bar_microgeometry" in terrain_recipe["procedural_tokens"]
    assert "exposed_bar_micro_pebbles" in terrain_recipe["procedural_tokens"]
    assert "bank_slope_material_flakes" in terrain_recipe["procedural_tokens"]
    assert "source_masked_shoreline_lip_overhang" in terrain_recipe["procedural_tokens"]
    assert "irregular_waterline_bank_lip" in terrain_recipe["procedural_tokens"]
    assert "wet_edge_overhang_shadow" in terrain_recipe["procedural_tokens"]
    assert "near_field_riverbed_debris_cards" in terrain_recipe["procedural_tokens"]
    assert "near_field_waterline_pebble_dressing" in terrain_recipe["procedural_tokens"]
    assert (
        "source_mask_biased_near_field_debris_placement"
        in terrain_recipe["procedural_tokens"]
    )
    assert "terrain_erosion_rill_count" in terrain_recipe["tunable_parameters"]
    assert "terrain_erosion_rill_width" in terrain_recipe["tunable_parameters"]
    assert "terrain_erosion_rill_length" in terrain_recipe["tunable_parameters"]
    assert "exposed_bar_micro_pebble_density" in terrain_recipe["tunable_parameters"]
    assert "bank_slope_material_flake_density" in terrain_recipe["tunable_parameters"]
    assert "shoreline_lip_overhang_density" in terrain_recipe["tunable_parameters"]
    assert "shoreline_lip_overhang_width" in terrain_recipe["tunable_parameters"]
    assert (
        "shoreline_lip_overhang_water_overlap" in terrain_recipe["tunable_parameters"]
    )
    assert "near_field_riverbed_debris_density" in terrain_recipe["tunable_parameters"]
    assert "near_field_waterline_pebble_density" in terrain_recipe["tunable_parameters"]
    assert "near_field_debris_waterline_bias" in terrain_recipe["tunable_parameters"]
    assert "source_masked_microgeometry_scale" in terrain_recipe["tunable_parameters"]
    assert "microgeometry_wetness_blend" in terrain_recipe["tunable_parameters"]
    assert (
        "shadowless_terrain_albedo_review_capture"
        in terrain_recipe["procedural_tokens"]
    )
    assert "flow_aware_water_mesh_undulation" in water_recipe["procedural_tokens"]
    assert "water_mesh_undulation_amplitude_cm" in water_recipe["tunable_parameters"]
    assert "standing_wave_mesh_amplitude_cm" in water_recipe["tunable_parameters"]
    assert "flow_aware_micro_ripple_glints" in water_recipe["procedural_tokens"]
    assert "bounded_lit_water_normal_response" in water_recipe["procedural_tokens"]
    assert "low_emissive_water_fill" in water_recipe["procedural_tokens"]
    assert "water_roughness_specular_constants" in water_recipe["procedural_tokens"]
    assert "micro_ripple_glint_density" in water_recipe["tunable_parameters"]
    assert (
        "near_frame_water_ribbon_occlusion_demotion"
        in water_recipe["procedural_tokens"]
    )
    assert "pale_foam_slash_artifact_demotion" in water_recipe["procedural_tokens"]
    assert "near_frame_shallow_water_band_demotion" in water_recipe["procedural_tokens"]
    assert "shallow_water_edge_band_demotion" in water_recipe["procedural_tokens"]
    assert "near_frame_water_ribbon_gain" in water_recipe["tunable_parameters"]
    assert "near_frame_water_ribbon_width" in water_recipe["tunable_parameters"]
    assert "pale_foam_slash_artifact_demotion" in water_recipe["tunable_parameters"]
    assert "near_frame_shallow_water_band_gain" in water_recipe["tunable_parameters"]
    assert "near_frame_shallow_water_band_width" in water_recipe["tunable_parameters"]
    assert "shallow_water_clarity_band" in water_recipe["procedural_tokens"]
    assert "source_masked_shallow_bed_reveal" in water_recipe["procedural_tokens"]
    assert "aeration_bubble_lace" in water_recipe["procedural_tokens"]
    assert "flow_dependent_hydraulic_aeration_mats" in water_recipe["procedural_tokens"]
    assert "flow_dependent_wave_train_foam_lace" in water_recipe["procedural_tokens"]
    assert "shallow_water_edge_band_width" in water_recipe["tunable_parameters"]
    assert (
        "shallow_water_edge_band_visibility_gain" in water_recipe["tunable_parameters"]
    )
    assert "shallow_water_bed_reveal_strength" in water_recipe["tunable_parameters"]
    assert "aeration_bubble_lace_density" in water_recipe["tunable_parameters"]
    assert "aeration_bubble_lace_opacity" in water_recipe["tunable_parameters"]
    assert "hydraulic_aeration_mat_density" in water_recipe["tunable_parameters"]
    assert "hydraulic_aeration_mat_opacity" in water_recipe["tunable_parameters"]
    assert "flow_dependent_foam_lace_density" in water_recipe["tunable_parameters"]
    assert "hazard_readability_foam_opacity_limit" in water_recipe["tunable_parameters"]
    assert "low_occlusion_far_field_water_scaffold" in water_recipe["procedural_tokens"]
    assert "remaining_water_overlay_slab_demotion" in water_recipe["procedural_tokens"]
    assert "water_overlay_color_reblend" in water_recipe["procedural_tokens"]
    assert "shortened_current_streak_overlays" in water_recipe["procedural_tokens"]
    assert "long_dark_water_streak_demotion" in water_recipe["procedural_tokens"]
    assert "current_streak_artifact_demotion" in water_recipe["procedural_tokens"]
    assert "waterline_rail_artifact_demotion" in water_recipe["procedural_tokens"]
    assert "central_water_scaffold_plate_demotion" in water_recipe["procedural_tokens"]
    assert "base_water_slick_color_reblend" in water_recipe["procedural_tokens"]
    assert "water_scaffold_far_field_start_m" in water_recipe["tunable_parameters"]
    assert "water_scaffold_reflection_blend" in water_recipe["tunable_parameters"]
    assert "water_scaffold_ribbon_width" in water_recipe["tunable_parameters"]
    assert "water_overlay_slab_opacity_limit" in water_recipe["tunable_parameters"]
    assert "water_overlay_slab_near_frame_start_m" in water_recipe["tunable_parameters"]
    assert "current_streak_length_scale" in water_recipe["tunable_parameters"]
    assert "current_streak_artifact_gain" in water_recipe["tunable_parameters"]
    assert "waterline_rail_artifact_gain" in water_recipe["tunable_parameters"]
    assert "flow_texture_rail_artifact_gain" in water_recipe["tunable_parameters"]
    assert "shallow_edge_rail_artifact_gain" in water_recipe["tunable_parameters"]
    assert "central_water_scaffold_plate_gain" in water_recipe["tunable_parameters"]
    assert "long_dark_water_streak_gain" in water_recipe["tunable_parameters"]
    assert "water_line_artifact_color_reblend" in water_recipe["tunable_parameters"]
    assert "flow_dependent_spray_beads" in atmosphere_recipe["procedural_tokens"]
    assert (
        "source_masked_spray_bead_placement" in atmosphere_recipe["procedural_tokens"]
    )
    assert "flow_dependent_spray_gain" in atmosphere_recipe["tunable_parameters"]
    assert "spray_bead_density" in atmosphere_recipe["tunable_parameters"]
    assert "spray_bead_opacity_limit" in atmosphere_recipe["tunable_parameters"]
    assert "crevice_shadow_facet" in wet_boulder_recipe["procedural_tokens"]
    assert "muted_top_highlight" in wet_boulder_recipe["procedural_tokens"]
    assert "review_frame_boulder_clearance" in wet_boulder_recipe["procedural_tokens"]
    assert "near_camera_boulder_darkening" in wet_boulder_recipe["procedural_tokens"]
    assert (
        "near_camera_boulder_occlusion_demotion"
        in wet_boulder_recipe["procedural_tokens"]
    )
    assert (
        "near_field_waterline_contact_pebbles"
        in wet_boulder_recipe["procedural_tokens"]
    )
    assert (
        "source_mask_biased_wet_contact_microstones"
        in wet_boulder_recipe["procedural_tokens"]
    )
    assert "near_camera_boulder_scale" in wet_boulder_recipe["tunable_parameters"]
    assert (
        "near_camera_boulder_highlight_gain" in wet_boulder_recipe["tunable_parameters"]
    )
    assert (
        "near_field_waterline_contact_pebble_density"
        in wet_boulder_recipe["tunable_parameters"]
    )
    assert "wet_contact_microstone_size" in wet_boulder_recipe["tunable_parameters"]
    assert "procedural_leaf_cluster_lobes" in foliage_recipe["procedural_tokens"]
    assert "leaf_cluster_lobe_count" in foliage_recipe["tunable_parameters"]
    assert "leaf_cluster_color_variance" in foliage_recipe["tunable_parameters"]
    assert "organic_leaf_spray_lobes" in foliage_recipe["procedural_tokens"]
    assert "organic_canopy_breakup" in foliage_recipe["procedural_tokens"]
    assert "organic_branch_frond_lattice" in foliage_recipe["procedural_tokens"]
    assert "fine_twig_canopy_lace" in foliage_recipe["procedural_tokens"]
    assert "fine_leaflet_silhouette_breakup" in foliage_recipe["procedural_tokens"]
    assert "foliage_crown_depth_shadow" in foliage_recipe["procedural_tokens"]
    assert "leaflet_color_breakup" in foliage_recipe["procedural_tokens"]
    assert "mask_guided_crown_occlusion" in foliage_recipe["procedural_tokens"]
    assert "procedural_branch_ribbons" in foliage_recipe["procedural_tokens"]
    assert "procedural_leaf_diamond_fronds" in foliage_recipe["procedural_tokens"]
    assert (
        "photographic_foliage_tone_calibration" in foliage_recipe["procedural_tokens"]
    )
    assert "reduced_proxy_foliage_emissive_lift" in foliage_recipe["procedural_tokens"]
    assert "muted_leaf_tip_highlights" in foliage_recipe["procedural_tokens"]
    assert "stylized_pcg_sample_foliage_disabled" in foliage_recipe["procedural_tokens"]
    assert (
        "first_party_procedural_only_foliage_review"
        in foliage_recipe["procedural_tokens"]
    )
    assert (
        "procedural_canopy_height_massing_profile"
        in foliage_recipe["procedural_tokens"]
    )
    assert (
        "river_specific_crown_height_width_bias" in foliage_recipe["procedural_tokens"]
    )
    assert "procedural_canopy_tone_compression" in foliage_recipe["procedural_tokens"]
    assert "procedural_crown_shadow_profile" in foliage_recipe["procedural_tokens"]
    assert "river_specific_canopy_tone_anchor" in foliage_recipe["procedural_tokens"]
    assert (
        "foliage_card_canopy_artifact_demotion" in foliage_recipe["procedural_tokens"]
    )
    assert "canopy_blob_scale_demotion" in foliage_recipe["procedural_tokens"]
    assert "foliage_card_visibility_breakup" in foliage_recipe["procedural_tokens"]
    assert "organic_leaf_spray_count" in foliage_recipe["tunable_parameters"]
    assert "near_field_leaf_litter_debris_cards" in foliage_recipe["procedural_tokens"]
    assert (
        "waterline_vegetation_mask_debris_bias" in foliage_recipe["procedural_tokens"]
    )
    assert (
        "near_field_leaf_litter_debris_density" in foliage_recipe["tunable_parameters"]
    )
    assert (
        "near_field_debris_leaf_color_variance" in foliage_recipe["tunable_parameters"]
    )
    assert "organic_leaf_spray_lobe_scale" in foliage_recipe["tunable_parameters"]
    assert "organic_leaf_spray_color_variance" in foliage_recipe["tunable_parameters"]
    assert "organic_branch_frond_branch_count" in foliage_recipe["tunable_parameters"]
    assert "organic_branch_frond_leaf_count" in foliage_recipe["tunable_parameters"]
    assert "organic_branch_frond_width" in foliage_recipe["tunable_parameters"]
    assert "organic_branch_frond_color_variance" in foliage_recipe["tunable_parameters"]
    assert "fine_twig_lace_density" in foliage_recipe["tunable_parameters"]
    assert "fine_leaflet_scale" in foliage_recipe["tunable_parameters"]
    assert "fine_twig_lace_color_variance" in foliage_recipe["tunable_parameters"]
    assert "foliage_crown_depth_shadow_strength" in foliage_recipe["tunable_parameters"]
    assert "leaflet_breakup_density" in foliage_recipe["tunable_parameters"]
    assert "leaflet_color_variance" in foliage_recipe["tunable_parameters"]
    assert "foliage_material_emissive_lift" in foliage_recipe["tunable_parameters"]
    assert "leaf_tip_highlight_gain" in foliage_recipe["tunable_parameters"]
    assert "biome_foliage_base_tint" in foliage_recipe["tunable_parameters"]
    assert (
        "stylized_sample_foliage_disable_gate" in foliage_recipe["tunable_parameters"]
    )
    assert "procedural_canopy_height_profile" in foliage_recipe["tunable_parameters"]
    assert (
        "procedural_canopy_massing_width_scale" in foliage_recipe["tunable_parameters"]
    )
    assert "procedural_trunk_height_profile" in foliage_recipe["tunable_parameters"]
    assert "procedural_canopy_tone_compression" in foliage_recipe["tunable_parameters"]
    assert "procedural_canopy_shadow_profile" in foliage_recipe["tunable_parameters"]
    assert "river_specific_canopy_tone_anchor" in foliage_recipe["tunable_parameters"]
    assert "foliage_card_visibility_gain" in foliage_recipe["tunable_parameters"]
    assert "canopy_blob_scale_demotion" in foliage_recipe["tunable_parameters"]
    assert "leaf_card_width_scale" in foliage_recipe["tunable_parameters"]
    water_recipe = next(
        recipe
        for recipe in material_plan["material_recipes"]
        if recipe["recipe_id"] == "flow_dependent_water_surface_material"
    )
    assert "near_camera_water_scaffold_clearance" in water_recipe["procedural_tokens"]
    assert "photographic_water_albedo_calibration" in water_recipe["procedural_tokens"]
    assert "reduced_water_emissive_lift" in water_recipe["procedural_tokens"]
    assert "manual_capture_exposure_bias" in water_recipe["procedural_tokens"]
    assert "near_field_water_surface_grain" in water_recipe["procedural_tokens"]
    assert (
        "near_camera_bottom_center_water_wedge_demotion"
        in water_recipe["procedural_tokens"]
    )
    assert (
        "near_camera_upstream_water_capture_apron" in water_recipe["procedural_tokens"]
    )
    assert "baked_river_ribbon_fine_ripples" in water_recipe["procedural_tokens"]
    assert "near_field_dark_slicks" in water_recipe["procedural_tokens"]
    assert "base_water_depth_current_grading" in water_recipe["procedural_tokens"]
    assert "base_water_current_tongue" in water_recipe["procedural_tokens"]
    assert "base_water_sediment_threads" in water_recipe["procedural_tokens"]
    assert "base_water_sky_threads" in water_recipe["procedural_tokens"]
    assert "base_water_flow_thread_texture" in water_recipe["procedural_tokens"]
    assert "base_water_flow_thread_relief" in water_recipe["procedural_tokens"]
    assert "base_water_flow_thread_foam_glint" in water_recipe["procedural_tokens"]
    assert "flow_cued_foam_slick_mottle" in water_recipe["procedural_tokens"]
    assert (
        "near_field_water_patch_tile_breakup_demotion"
        in water_recipe["procedural_tokens"]
    )
    assert (
        "continuous_near_field_water_current_blend" in water_recipe["procedural_tokens"]
    )
    assert (
        "water_review_material_source_texture_tile_cull"
        in water_recipe["procedural_tokens"]
    )
    assert (
        "integrated_river_eye_water_entropy_mottle" in water_recipe["procedural_tokens"]
    )
    assert "river_eye_current_bed_foam_mottle" in water_recipe["procedural_tokens"]
    assert "base_river_ribbon_foam_seed" in water_recipe["procedural_tokens"]
    assert "flow_volume_slick_variation" in water_recipe["procedural_tokens"]
    assert "water_material_emissive_lift" in water_recipe["tunable_parameters"]
    assert "capture_exposure_bias" in water_recipe["tunable_parameters"]
    assert "sun_sky_intensity_balance" in water_recipe["tunable_parameters"]
    assert "near_field_water_surface_grain_gain" in water_recipe["tunable_parameters"]
    assert (
        "near_camera_bottom_center_water_wedge_demotion"
        in water_recipe["tunable_parameters"]
    )
    assert (
        "near_camera_bottom_center_water_wedge_luma_floor"
        in water_recipe["tunable_parameters"]
    )
    assert (
        "near_camera_upstream_water_apron_start_m" in water_recipe["tunable_parameters"]
    )
    assert "fine_ripple_amplitude_cm" in water_recipe["tunable_parameters"]
    assert "river_ribbon_mesh_resolution" in water_recipe["tunable_parameters"]
    assert "base_water_current_tongue_contrast" in water_recipe["tunable_parameters"]
    assert "base_water_sediment_thread_strength" in water_recipe["tunable_parameters"]
    assert "base_water_sky_thread_strength" in water_recipe["tunable_parameters"]
    assert (
        "base_water_flow_thread_texture_strength" in water_recipe["tunable_parameters"]
    )
    assert "base_water_flow_thread_relief_cm" in water_recipe["tunable_parameters"]
    assert (
        "base_water_flow_thread_foam_glint_strength"
        in water_recipe["tunable_parameters"]
    )
    assert "water_foam_slick_mottle_strength" in water_recipe["tunable_parameters"]
    assert (
        "near_field_water_patch_tile_breakup_demotion_gain"
        in water_recipe["tunable_parameters"]
    )
    assert (
        "continuous_near_field_water_current_blend_strength"
        in water_recipe["tunable_parameters"]
    )
    assert (
        "water_review_material_source_texture_tile_cull_gain"
        in water_recipe["tunable_parameters"]
    )
    assert (
        "integrated_river_eye_water_entropy_mottle_strength"
        in water_recipe["tunable_parameters"]
    )
    assert "river_eye_water_entropy_cell_mix" in water_recipe["tunable_parameters"]
    assert (
        "water_review_material_atlas_blend_weight" in water_recipe["tunable_parameters"]
    )
    assert (
        "water_review_material_source_conditioned_weight"
        in water_recipe["tunable_parameters"]
    )
    assert "flow_cued_foam_seed_scale" in water_recipe["tunable_parameters"]
    assert "river_ribbon_slick_darkening" in water_recipe["tunable_parameters"]
    assert "source_aware_sky_gradient_bands" in atmosphere_recipe["procedural_tokens"]
    assert "sun_warmth_veil" in atmosphere_recipe["procedural_tokens"]
    assert "atmospheric_depth_sheets" in atmosphere_recipe["procedural_tokens"]
    assert (
        "photographic_capture_palette_compression"
        in atmosphere_recipe["procedural_tokens"]
    )
    assert "bounded_capture_film_grain_dither" in atmosphere_recipe["procedural_tokens"]
    assert (
        "photographic_color_grade_palette_compression_active"
        in atmosphere_recipe["unreal_status"]
    )
    assert "sky_gradient_band_count" in atmosphere_recipe["tunable_parameters"]
    assert "sky_horizon_warmth_strength" in atmosphere_recipe["tunable_parameters"]
    assert "atmosphere_depth_sheet_opacity" in atmosphere_recipe["tunable_parameters"]
    assert "capture_saturation" in atmosphere_recipe["tunable_parameters"]
    assert "capture_contrast" in atmosphere_recipe["tunable_parameters"]
    assert "capture_exposure_bias" in atmosphere_recipe["tunable_parameters"]
    assert "capture_film_grain_intensity" in atmosphere_recipe["tunable_parameters"]
    assert "capture_film_grain_scale" in atmosphere_recipe["tunable_parameters"]
    assert "horizontal_tube_orientation" in raft_recipe["procedural_tokens"]
    assert "horizontal_bow_strip" in raft_recipe["procedural_tokens"]
    assert "flat_outboard_oar_shafts" in raft_recipe["procedural_tokens"]
    assert "low_occlusion_oar_blades" in raft_recipe["procedural_tokens"]
    assert "tube_seam_highlights" in raft_recipe["procedural_tokens"]
    assert "rounded_tube_bow_frame_oar_shafts" in raft_recipe["procedural_tokens"]
    assert "demoted_floor_occlusion" in raft_recipe["procedural_tokens"]
    assert "tagged_river_eye_foreground_proxy_cull" in raft_recipe["procedural_tokens"]
    assert "low_luma_oar_blade_and_shaft_demotion" in raft_recipe["procedural_tokens"]
    assert "near_field_water_source_tile_demotion" in raft_recipe["procedural_tokens"]
    assert "near_field_inboard_bank_shelf_cull" in raft_recipe["procedural_tokens"]
    assert (
        "near_camera_inwater_debris_occlusion_cull" in raft_recipe["procedural_tokens"]
    )
    assert (
        "guide_seat_placeholder_foreground_capture_cull"
        in raft_recipe["tunable_parameters"]
    )
    assert (
        "rounded_first_party_raft_oar_foreground_proxy_active"
        in raft_recipe["unreal_status"]
    )
    assert "rounded_foreground_proxy_radius" in raft_recipe["tunable_parameters"]
    assert "foreground_proxy_luma_floor" in raft_recipe["tunable_parameters"]
    assert "river_eye_hidden_actor_tag_cull" in raft_recipe["tunable_parameters"]
    assert (
        "near_field_water_source_tile_demotion_gain"
        in raft_recipe["tunable_parameters"]
    )
    assert (
        "near_field_bank_shelf_inboard_clearance" in raft_recipe["tunable_parameters"]
    )
    assert (
        "near_camera_debris_active_water_clearance" in raft_recipe["tunable_parameters"]
    )
    assert "SINAC forest-cover lead" in pacuare_terrain["source_evidence"]
