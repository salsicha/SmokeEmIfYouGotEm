# ruff: noqa: F405

from photoreal_test_support import *  # noqa: F401,F403


def test_unreal_environment_automation_run_report_records_material_gate_capture():
    report = json.loads(AUTOMATION_RUN_REPORT_PATH.read_text(encoding="utf-8"))

    assert report["schema"] == "raftsim.unreal.environment_automation_run.v1"
    assert report["status"] == "succeeded_preview_only_not_lifelike"
    assert report["build_result"]["status"] == "succeeded"
    assert report["build_result"]["compiled_module"] == "RaftSimEditor"
    assert report["automation_result"]["status"] == "succeeded"
    assert (
        report["automation_result"]["required_material_instance_candidate_manifest"]
        == "unreal/Content/RaftSim/Rendering/first_party_material_instance_candidates.json"
    )
    assert (
        report["automation_result"]["material_instance_review_asset_status"]
        == "18_created_unreal_material_instance_constant_review_assets_with_texture_bindings_sampler_parent_and_scene_assignment_not_lifelike"
    )
    assert (
        report["automation_result"]["atlas_sampler_review_material"]
        == "unreal/Content/RaftSim/Materials/M_RaftSim_AtlasSampleReview.uasset"
    )
    assert (
        REPO_ROOT / report["automation_result"]["atlas_sampler_review_material"]
    ).exists()
    assert (
        report["automation_result"]["atlas_sampler_review_material_status"]
        == "created_unreal_atlas_sampler_review_parent_material_not_lifelike"
    )
    assert (
        report["automation_result"]["material_texture_asset_root"]
        == "unreal/Content/RaftSim/Rendering/ProceduralTextureAtlases/Textures"
    )
    assert (
        report["automation_result"]["material_texture_asset_status"]
        == "9_created_unreal_texture2d_review_assets_bound_to_material_instance_candidates_not_lifelike"
    )
    assert len(report["automation_result"]["saved_material_texture_assets"]) == 9
    assert all(
        (REPO_ROOT / asset_path).exists()
        for asset_path in report["automation_result"]["saved_material_texture_assets"]
    )
    assert (
        len(report["automation_result"]["saved_material_instance_review_assets"]) == 18
    )
    assert all(
        (REPO_ROOT / asset_path).exists()
        for asset_path in report["automation_result"][
            "saved_material_instance_review_assets"
        ]
    )
    assert (
        report["automation_result"]["required_material_recipe_plan"]
        == "unreal/Content/RaftSim/Rendering/first_party_procedural_material_recipes.json"
    )
    assert (
        report["automation_result"]["required_geospatial_attachment_ledger"]
        == "physics/data/real_world/production_geospatial_attachment_ledger.json"
    )
    assert len(report["automation_result"]["saved_maps"]) == 3
    assert report["renderer_update"]["softened_source_drape_overlay"] is True
    assert report["renderer_update"]["boulder_contact_foam_lace"] is True
    assert (
        report["renderer_update"]["guide_seat_foliage_setback_and_scale_tuning"] is True
    )
    assert (
        report["renderer_update"]["source_aware_bank_breakup_texture_patches"] is True
    )
    assert (
        report["renderer_update"]["first_party_irregular_shoreline_edge_breakup"]
        is True
    )
    assert report["renderer_update"]["soft_feathered_terrain_material_patches"] is True
    assert report["renderer_update"]["source_drape_albedo_normalization"] is True
    assert (
        report["renderer_update"]["first_party_feathered_source_drape_microtiles"]
        is True
    )
    assert report["renderer_update"]["flow_aware_bank_undercut_shelf_relief"] is True
    assert report["renderer_update"]["terrain_proxy_luma_floor"] is True
    assert (
        report["renderer_update"]["shadowless_terrain_albedo_review_capture_material"]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_terrain_material_layer_facets_and_slope_shadow_patches"
        ]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_landscape_nanite_material_layer_scaffold"
        ]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_terrain_erosion_rill_and_bank_gully_detail"
        ]
        is True
    )
    assert (
        report["renderer_update"]["first_party_lit_terrain_vertex_color_material"]
        is True
    )
    assert (
        report["renderer_update"]["soft_lit_terrain_vertex_color_review_material"]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_photographic_terrain_emissive_calibration"
        ]
        is True
    )
    assert (
        report["renderer_update"]["first_party_terrain_contrast_and_normal_calibration"]
        is True
    )
    assert report["renderer_update"]["first_party_bounded_terrain_ambient_fill"] is True
    assert (
        report["renderer_update"][
            "first_party_base_terrain_material_grain_and_microrelief"
        ]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_source_aware_terrain_photo_mottle_and_microrelief"
        ]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_source_conditioned_far_bank_albedo_calibration"
        ]
        is True
    )
    assert (
        report["renderer_update"]["first_party_broad_slope_terrain_exposure_fill"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_source_aware_macro_terrain_ridge_facets"]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_source_aware_terrain_slope_facet_texture"
        ]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_source_aware_terrain_surface_granularity"
        ]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_source_aware_riparian_canopy_mass_texture"
        ]
        is True
    )
    assert (
        report["renderer_update"]["first_party_source_overlay_plate_artifact_demotion"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_demoted_terrain_overlay_striping"]
        is True
    )
    assert report["renderer_update"]["first_party_source_drape_smoothing_pass"] is True
    assert report["renderer_update"]["first_party_segmented_wet_bank_ribbons"] is True
    assert (
        report["renderer_update"]["first_party_graphic_waterline_ribbon_demotion"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_near_frame_shoreline_scaffold_demotion"]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_pale_bank_shoreline_scaffold_slash_demotion"
        ]
        is True
    )
    assert (
        report["renderer_update"]["first_party_demoted_source_detail_contours"] is True
    )
    assert (
        report["renderer_update"]["first_party_post_contour_terrain_readability_fill"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_source_masked_bank_bar_microgeometry"]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_source_masked_shoreline_lip_overhang_edge_breakup"
        ]
        is True
    )
    assert (
        report["renderer_update"]["biome_specific_deadfall_grass_root_ecology_props"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_biome_foliage_silhouette_proxy_layers"]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_dense_biome_foliage_layer_proxy_clusters"
        ]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_instanced_procedural_foliage_equivalent_scaffold"
        ]
        is True
    )
    assert (
        report["renderer_update"]["first_party_procedural_leaf_cluster_geometry"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_organic_canopy_leaf_spray_breakup"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_organic_branch_frond_lattice_foliage"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_fine_twig_canopy_lace_foliage"] is True
    )
    assert (
        report["renderer_update"]["first_party_photographic_foliage_tone_calibration"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_foliage_crown_depth_and_leaflet_breakup"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_procedural_only_foliage_review_path"]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_procedural_canopy_height_massing_profile"
        ]
        is True
    )
    assert (
        report["renderer_update"]["first_party_procedural_canopy_tone_shadow_profile"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_foliage_card_canopy_artifact_demotion"]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_square_foliage_source_card_artifact_demotion"
        ]
        is True
    )
    assert report["renderer_update"]["first_party_remaining_square_card_cull"] is True
    assert (
        report["renderer_update"][
            "first_party_blocky_bank_ecology_and_sphere_foliage_cull"
        ]
        is True
    )
    assert report["renderer_update"]["flow_aware_waterline_pebble_scatter"] is True
    assert (
        report["renderer_update"]["first_party_irregular_rock_geometry_variants"]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_boulder_wetness_abrasion_moss_surface_variants"
        ]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_boulder_crevice_shadow_and_albedo_tuning"
        ]
        is True
    )
    assert (
        report["renderer_update"]["near_camera_boulder_readability_clearance"] is True
    )
    assert report["renderer_update"]["near_camera_boulder_occlusion_demotion"] is True
    assert report["renderer_update"]["flow_aware_water_mesh_undulation"] is True
    assert report["renderer_update"]["flow_band_depth_texture_ribbons"] is True
    assert (
        report["renderer_update"]["flow_aware_water_surface_chop_and_turbidity_patches"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_turbidity_depth_patch_artifact_demotion"]
        is True
    )
    assert report["renderer_update"]["flow_aware_micro_ripple_glints"] is True
    assert (
        report["renderer_update"]["near_frame_water_ribbon_occlusion_demotion"] is True
    )
    assert (
        report["renderer_update"][
            "first_party_water_shader_depth_reflection_refraction_scaffold"
        ]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_shallow_water_clarity_and_aeration_layer"
        ]
        is True
    )
    assert (
        report["renderer_update"]["near_camera_water_scaffold_readability_clearance"]
        is True
    )
    assert (
        report["renderer_update"]["low_occlusion_far_field_water_shader_scaffold"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_remaining_water_overlay_slab_demotion"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_pale_water_foam_slash_demotion"] is True
    )
    assert (
        report["renderer_update"]["first_party_long_dark_water_streak_demotion"] is True
    )
    assert (
        report["renderer_update"][
            "first_party_current_streak_waterline_artifact_demotion"
        ]
        is True
    )
    assert (
        report["renderer_update"]["first_party_central_water_scaffold_plate_demotion"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_lit_water_normal_response_scaffold"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_photographic_water_exposure_calibration"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_near_field_water_surface_grain"] is True
    )
    assert (
        report["renderer_update"]["first_party_near_camera_water_macro_ripple_mottle"]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_near_camera_bottom_center_water_wedge_demotion"
        ]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_near_camera_upstream_water_capture_apron"
        ]
        is True
    )
    assert (
        report["renderer_update"]["first_party_base_water_depth_current_grading"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_base_water_flow_thread_texture"] is True
    )
    assert (
        report["renderer_update"]["first_party_base_water_center_guide_stripe_breakup"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_base_water_cross_channel_breakup"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_base_water_residual_center_seam_erase"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_dark_micro_ripple_artifact_demotion"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_flow_cued_water_foam_slick_mottle"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_flow_dependent_hydraulic_aeration_spray"]
        is True
    )
    assert (
        report["renderer_update"][
            "pacuare_waterfall_curtain_plunge_mist_and_runout_proxies"
        ]
        is True
    )
    assert (
        report["renderer_update"][
            "river_specific_cloud_haze_and_horizon_backdrop_cards"
        ]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_source_aware_sky_gradient_and_atmosphere_depth_layers"
        ]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_guide_seat_raft_and_oar_foreground_proxies"
        ]
        is True
    )
    assert (
        report["renderer_update"]["first_party_refined_raft_oar_foreground_proxy"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_rounded_raft_oar_foreground_proxy"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_tagged_river_eye_foreground_proxy_cull"]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_dedicated_river_eye_downstream_capture_camera"
        ]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_centerline_following_river_eye_capture_camera"
        ]
        is True
    )
    assert (
        report["renderer_update"]["first_party_rainforest_river_eye_slope_texture"]
        is True
    )
    assert (
        report["renderer_update"]["first_party_river_eye_near_field_dressing_cull"]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_integrated_river_eye_water_entropy_mottle"
        ]
        is True
    )
    assert (
        report["renderer_update"]["first_party_low_luma_foreground_raft_proxy_demotion"]
        is True
    )
    assert (
        report["renderer_update"]["raft_hidden_river_eye_foreground_proxy_hard_hide"]
        is True
    )
    assert (
        report["renderer_update"]["raft_hidden_river_eye_primitive_component_hard_hide"]
        is True
    )
    assert (
        report["renderer_update"]["raft_hidden_river_eye_center_artifact_cover"] is True
    )
    assert (
        report["renderer_update"][
            "raft_hidden_river_eye_textured_center_artifact_cover"
        ]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_material_texture2d_review_assets_created"
        ]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_material_instance_texture_asset_bindings_recorded"
        ]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_atlas_sampler_review_parent_material_created"
        ]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_material_shader_graph_sampler_wiring_recorded"
        ]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_material_instance_scene_assignment_recorded"
        ]
        is True
    )
    assert (
        report["renderer_update"]["first_party_near_field_water_source_tile_demotion"]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_near_field_water_patch_tile_breakup_demotion"
        ]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_continuous_near_field_water_current_blend"
        ]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_water_review_material_source_texture_tile_cull"
        ]
        is True
    )
    assert (
        report["renderer_update"]["first_party_near_field_inboard_bank_shelf_cull"]
        is True
    )
    assert (
        report["renderer_update"][
            "first_party_near_camera_inwater_debris_occlusion_cull"
        ]
        is True
    )
    assert (
        report["renderer_update"]["photoreal_capture_quality_review_blockers_recorded"]
        is True
    )
    assert (
        report["renderer_update"][
            "automated_capture_quality_gate_passed_without_proxy_blockers"
        ]
        is False
    )
    assert (
        report["automation_result"]["material_instance_scene_assignment_status"]
        == "assigned_review_material_instances_to_preview_map_surface_proxies_not_lifelike"
    )
    assert (
        report["renderer_update"]["first_party_material_instance_review_assets_created"]
        is True
    )
    assert len(report["capture_pixel_sanity"]) == 6
    assert all(
        capture["nonblank"] is True for capture in report["capture_pixel_sanity"]
    )
    assert report["post_capture_quality_review"]["path"] == str(
        CAPTURE_QUALITY_REVIEW_RELATIVE_PATH
    )
    assert (
        report["post_capture_quality_review"]["status"]
        == "captures_reviewed_preview_only_not_lifelike_quality_blockers_recorded"
    )
    assert report["post_capture_quality_review"]["summary"]["capture_count"] == 6
    assert (
        report["post_capture_quality_review"]["summary"]["blocking_capture_count"] == 6
    )
    assert "preview-only" in report["current_decision"]


def test_photoreal_capture_quality_review_records_human_review_candidate_gate():
    review = json.loads(CAPTURE_QUALITY_REVIEW_PATH.read_text(encoding="utf-8"))

    assert review == build_capture_quality_review(REPO_ROOT)
    assert review["schema"] == "raftsim.unreal.photoreal_capture_quality_review.v1"
    assert review["status"] == EXPECTED_CAPTURE_QUALITY_STATUS
    assert (
        review["source_capture_manifest"]
        == "docs/environment-captures/photoreal_river_previews/environment_capture_manifest.json"
    )
    assert review["policy"]["metrics_are_blockers_not_lifelike_approval"] is True
    assert (
        review["policy"]["human_guide_geospatial_and_art_review_still_required"] is True
    )
    assert (
        review["policy"][
            "water_visuals_must_not_hide_hazards_rescue_targets_or_physics_failures"
        ]
        is True
    )

    assert review["summary"]["capture_count"] == 6
    assert review["summary"]["blocking_capture_count"] == 6
    assert review["summary"]["blocker_counts"][EXPECTED_CAPTURE_BLOCKER_ID] == 6
    assert set(review["summary"]["per_river"]) == {
        "american_south_fork",
        "colorado_river",
        "pacuare",
    }
    assert all(
        river["status"] == EXPECTED_CAPTURE_STATUS
        for river in review["summary"]["per_river"].values()
    )
    assert "remain preview-only" in review["current_decision"]

    thresholds = review["thresholds"]
    blocker_ids_by_capture = {
        capture["capture"]: {blocker["id"] for blocker in capture["blockers"]}
        for capture in review["captures"]
    }
    for capture in review["captures"]:
        capture_path = REPO_ROOT / capture["capture"]
        metrics = capture["metrics"]

        assert capture_path.exists()
        assert _sha256(capture_path) == capture["sha256"]
        assert capture["status"] == EXPECTED_CAPTURE_STATUS
        blocker_ids = blocker_ids_by_capture[capture["capture"]]
        assert EXPECTED_CAPTURE_BLOCKER_ID in blocker_ids
        assert metrics["source_size"] == [1280, 720]
        assert metrics["analysis_size"] == [320, 180]
        assert "visible_proxy_water_overlay_geometry" not in blocker_ids
        assert "visible_proxy_water_card_geometry" not in blocker_ids
        assert "faceted_proxy_water_surface_mesh" not in blocker_ids
        assert ("excess_low_gradient_area" in blocker_ids) is (
            metrics["low_gradient_fraction"]
            > thresholds["max_low_gradient_fraction_for_lifelike_review"]
        )
        assert (
            metrics["quantized_entropy_bits"]
            < thresholds["min_quantized_entropy_bits_for_lifelike_review"]
        )
        assert "large_flat_blue_field" not in blocker_ids
        assert "dark_foreground_proxy" not in blocker_ids
        assert ("low_luma_variation" in blocker_ids) is (
            metrics["luma_std"] < thresholds["min_luma_std_for_lifelike_review"]
        )
        assert ("low_edge_density" in blocker_ids) is (
            metrics["edge_density"] < thresholds["min_edge_density_for_lifelike_review"]
        )
        assert (
            metrics["flat_blue_field_fraction"]
            <= thresholds["max_flat_blue_field_fraction_for_lifelike_review"]
        )
        assert (
            metrics["bottom_center_dark_fraction"]
            <= thresholds["max_bottom_center_dark_fraction_for_lifelike_review"]
        )


def test_photoreal_environment_performance_review_records_desktop_vr_gate():
    review = json.loads(
        PHOTOREAL_ENVIRONMENT_PERFORMANCE_REVIEW_PATH.read_text(encoding="utf-8")
    )

    assert review == build_photoreal_environment_performance_review(REPO_ROOT)
    assert (
        review["schema"] == "raftsim.unreal.photoreal_environment_performance_review.v1"
    )
    assert (
        review["status"]
        == "awaiting_measured_desktop_vr_performance_capture_not_approved"
    )
    assert (
        review["source_capture_manifest"]
        == "docs/environment-captures/photoreal_river_previews/environment_capture_manifest.json"
    )
    assert review["source_capture_quality_review"] == str(
        CAPTURE_QUALITY_REVIEW_RELATIVE_PATH
    )
    assert review["source_runtime_budgets"] == "physics/config/runtime_budgets.json"
    assert review["policy"]["static_inventory_is_not_performance_approval"] is True
    assert (
        review["policy"]["desktop_and_vr_profiles_required_before_production_playable"]
        is True
    )
    assert (
        review["policy"][
            "performance_must_not_trade_away_hazard_rescue_or_water_readability"
        ]
        is True
    )

    assert review["summary"] == {
        "river_count": 3,
        "profile_count": 6,
        "profile_ids": ["desktop", "vr"],
        "measured_profile_count": 0,
        "open_profile_measurement_count": 6,
        "automated_capture_blocking_count": 6,
        "approved_river_count": 0,
    }
    assert "does not pass the performance gate" in review["current_decision"]

    shared_inventory = review["shared_asset_inventory"]
    assert shared_inventory["first_party_material_texture_assets"]["file_count"] >= 9
    assert (
        shared_inventory["source_conditioned_material_texture_assets"]["file_count"]
        >= 12
    )
    assert shared_inventory["material_instance_review_assets"]["file_count"] >= 18
    assert all(inventory["total_bytes"] > 0 for inventory in shared_inventory.values())

    assert {river["river_id"] for river in review["rivers"]} == {
        "american_south_fork",
        "colorado_river",
        "pacuare",
    }
    capture_review = json.loads(CAPTURE_QUALITY_REVIEW_PATH.read_text(encoding="utf-8"))
    blocker_count_by_capture = {
        capture["capture"]: len(capture["blockers"])
        for capture in capture_review["captures"]
    }
    for river in review["rivers"]:
        assert (
            river["status"]
            == "static_capture_inventory_recorded_performance_measurement_required"
        )
        assert river["approved_for_production_playable"] is False
        assert "not production-playable" in river["current_decision"]
        inventory = river["static_inventory"]
        map_asset = inventory["map_asset"]
        assert map_asset["exists"] is True
        assert map_asset["size_bytes"] > 0
        assert map_asset["sha256"]
        assert len(inventory["captures"]) == 2
        assert inventory["total_capture_png_bytes"] > 0
        for capture in inventory["captures"]:
            assert capture["exists"] is True
            assert capture["sha256"]
            assert capture["size_bytes"] > 0
            assert capture["source_size"] == [1280, 720]
            assert (
                capture["automated_blocker_count"]
                == blocker_count_by_capture[capture["capture"]]
            )
            assert capture["automated_status"] == EXPECTED_CAPTURE_STATUS
        assert {profile["profile_id"] for profile in river["profiles"]} == {
            "desktop",
            "vr",
        }
        for profile in river["profiles"]:
            assert profile["status"] == "requires_measured_unreal_profile_capture"
            assert profile["approved"] is False
            assert profile["evidence_attached"] is False
            assert profile["target_frame_time_ms"] > 0
            assert all(
                value is None for value in profile["required_measurements"].values()
            )
            assert profile["blocking_open_measurements"]


def test_photoreal_human_lifelike_review_handoff_records_open_review_domains():
    handoff = json.loads(HUMAN_LIFELIKE_REVIEW_HANDOFF_PATH.read_text(encoding="utf-8"))
    capture_review = json.loads(CAPTURE_QUALITY_REVIEW_PATH.read_text(encoding="utf-8"))

    assert handoff == build_human_lifelike_review_handoff(REPO_ROOT)
    assert (
        handoff["schema"] == "raftsim.unreal.photoreal_human_lifelike_review_handoff.v1"
    )
    assert handoff["status"] == "awaiting_human_lifelike_review_not_approved"
    assert (
        handoff["source_capture_manifest"]
        == "docs/environment-captures/photoreal_river_previews/environment_capture_manifest.json"
    )
    assert handoff["source_capture_quality_review"] == str(
        CAPTURE_QUALITY_REVIEW_RELATIVE_PATH
    )
    assert handoff["source_performance_review"] == str(
        PHOTOREAL_ENVIRONMENT_PERFORMANCE_REVIEW_RELATIVE_PATH
    )
    assert (
        handoff["source_reference_media_review_queue"]
        == "physics/data/real_world/reference_media_review_queue.json"
    )
    assert (
        handoff["policy"]["automated_metrics_do_not_approve_lifelike_visuals"] is True
    )
    assert (
        handoff["policy"]["all_review_domains_must_be_approved_before_lifelike_status"]
        is True
    )

    assert handoff["summary"]["river_count"] == 3
    assert handoff["summary"]["capture_count"] == 6
    assert handoff["summary"]["candidate_capture_count"] == 0
    assert handoff["summary"]["automated_blocking_capture_count"] == 6
    assert handoff["summary"]["human_approved_capture_count"] == 0
    assert handoff["summary"]["open_human_review_gate_count"] == 21
    assert set(handoff["summary"]["per_river"]) == {
        "american_south_fork",
        "colorado_river",
        "pacuare",
    }

    review_domain_ids = {domain["domain_id"] for domain in handoff["review_domains"]}
    assert review_domain_ids == {
        "art_direction_visual_lifelike",
        "guide_hydraulic_fidelity",
        "geospatial_source_alignment",
        "rights_and_reference_media",
        "hazard_and_rescue_readability",
        "production_material_asset_promotion",
        "desktop_and_vr_performance",
    }
    assert all(domain["approved"] is False for domain in handoff["review_domains"])

    reviewed_capture_hashes = {
        capture["sha256"] for capture in capture_review["captures"]
    }
    for river in handoff["rivers"]:
        assert river["review_status"] == "awaiting_human_lifelike_review_not_approved"
        assert river["readiness"] == "preview_only_not_lifelike"
        assert len(river["captures"]) == 2
        assert len(river["open_review_gates"]) == 7
        assert len(river["reference_media_review_targets"]) >= 3
        assert river["source_inputs_for_review"]["aerial_drape_image"]
        assert river["source_inputs_for_review"]["terrain_relief_image"]
        assert river["source_inputs_for_review"]["water_mask_image"]
        assert river["flow_context"]["flow_band_id"]
        assert "Automated capture-quality blockers remain" in river["current_decision"]

        for gate in river["open_review_gates"]:
            assert gate["status"] == "open_pending_human_review_or_production_evidence"
            assert gate["approved"] is False
            assert gate["domain_id"] in review_domain_ids

        for capture in river["captures"]:
            assert capture["automated_status"] == EXPECTED_CAPTURE_STATUS
            assert EXPECTED_CAPTURE_BLOCKER_ID in {
                blocker["id"] for blocker in capture["automated_blockers"]
            }
            assert capture["human_review_status"] == "not_reviewed"
            assert (
                capture["approval_status"] == "not_approved_for_lifelike_or_production"
            )
            assert capture["sha256"] in reviewed_capture_hashes
            assert (REPO_ROOT / capture["capture"]).exists()


def test_photoreal_human_lifelike_review_packet_embeds_capture_review_context():
    packet = HUMAN_LIFELIKE_REVIEW_PACKET_PATH.read_text(encoding="utf-8")

    assert packet == build_human_lifelike_review_packet_markdown(REPO_ROOT)
    assert "# Photoreal Human Lifelike Review Packet" in packet
    assert "Status: `awaiting_human_lifelike_review_not_approved`" in packet
    assert "## Required Review Domains" in packet
    assert "## River Review Sheets" in packet
    assert "## Final Promotion Rule" in packet
    assert "Decision:" in packet
    assert "not approved as lifelike or production-ready" in packet
    assert "/Users/" not in packet
    assert str(HUMAN_LIFELIKE_REVIEW_HANDOFF_RELATIVE_PATH) in packet
    assert str(CAPTURE_QUALITY_REVIEW_RELATIVE_PATH) in packet
    assert str(PHOTOREAL_ENVIRONMENT_PERFORMANCE_REVIEW_RELATIVE_PATH) in packet
    assert str(HUMAN_LIFELIKE_REVIEW_RESULTS_TEMPLATE_RELATIVE_PATH) in packet

    assert packet.count("### ") == 3
    assert packet.count("![") == 6
    for image_name in {
        "american_south_fork_guide_seat_downstream.png",
        "american_south_fork_river_eye_downstream.png",
        "colorado_river_guide_seat_downstream.png",
        "colorado_river_river_eye_downstream.png",
        "pacuare_guide_seat_downstream.png",
        "pacuare_river_eye_downstream.png",
    }:
        assert image_name in packet

    for domain_title in {
        "Art Direction Visual Lifelike",
        "Guide Hydraulic Fidelity",
        "Geospatial Source Alignment",
        "Rights And Reference Media",
        "Hazard And Rescue Readability",
        "Production Material Asset Promotion",
        "Desktop And Vr Performance",
    }:
        assert f"**{domain_title}**" in packet

    for river_title in {
        "South Fork American River (`american_south_fork`)",
        "Colorado River Grand Canyon (`colorado_river`)",
        "Pacuare River Rainforest (`pacuare`)",
    }:
        assert f"### {river_title}" in packet


def test_photoreal_human_lifelike_review_results_template_is_ready_for_external_reviewers():
    template = json.loads(
        HUMAN_LIFELIKE_REVIEW_RESULTS_TEMPLATE_PATH.read_text(encoding="utf-8")
    )

    assert template == build_human_lifelike_review_results_template(REPO_ROOT)
    assert (
        template["schema"]
        == "raftsim.unreal.photoreal_human_lifelike_review_results_template.v1"
    )
    assert template["status"] == "awaiting_external_human_review_inputs_not_approved"
    assert template["source_handoff"] == str(
        HUMAN_LIFELIKE_REVIEW_HANDOFF_RELATIVE_PATH
    )
    assert template["source_packet"] == str(HUMAN_LIFELIKE_REVIEW_PACKET_RELATIVE_PATH)
    assert template["source_capture_quality_review"] == str(
        CAPTURE_QUALITY_REVIEW_RELATIVE_PATH
    )
    assert template["source_performance_review"] == str(
        PHOTOREAL_ENVIRONMENT_PERFORMANCE_REVIEW_RELATIVE_PATH
    )
    assert template["policy"]["do_not_self_approve_with_automated_metrics"] is True
    assert (
        template["policy"]["reviewer_identity_role_and_date_required_for_approval"]
        is True
    )
    assert (
        template["policy"][
            "evidence_links_or_artifacts_required_for_each_domain_approval"
        ]
        is True
    )
    assert (
        template["policy"][
            "hazard_rescue_and_physics_readability_block_lifelike_promotion"
        ]
        is True
    )

    assert template["summary"] == {
        "river_count": 3,
        "capture_count": 6,
        "review_domain_count": 7,
        "open_review_result_count": 21,
        "approved_river_count": 0,
    }
    assert {river["river_id"] for river in template["rivers"]} == {
        "american_south_fork",
        "colorado_river",
        "pacuare",
    }
    for river in template["rivers"]:
        assert river["review_status"] == "not_reviewed_not_approved"
        assert len(river["captures"]) == 2
        assert len(river["domain_results"]) == 7
        assert river["final_river_decision"]["status"] == "not_reviewed"
        assert river["final_river_decision"]["approved_for_lifelike"] is False
        assert (
            river["final_river_decision"]["approved_for_production_playable"] is False
        )
        for capture in river["captures"]:
            assert capture["human_review_status"] == "not_reviewed"
            assert (
                capture["approval_status"] == "not_approved_for_lifelike_or_production"
            )
            assert (REPO_ROOT / capture["capture"]).exists()
        for result in river["domain_results"]:
            assert result["status"] == "not_reviewed"
            assert result["approved"] is False
            assert result["reviewer_name"] == ""
            assert result["reviewer_role_or_credential"] == ""
            assert result["review_date"] == ""
            assert result["required_evidence"]
            assert result["evidence_links_or_artifacts"] == []
            assert result["blockers"] == []
            assert result["follow_up_actions"] == []
