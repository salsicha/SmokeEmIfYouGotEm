# ruff: noqa: F405

from photoreal_test_support import *  # noqa: F401,F403


def test_photoreal_environment_manifests_reference_procedural_asset_plan():
    source_plan = json.loads(SOURCE_PLAN_PATH.read_text(encoding="utf-8"))
    gap_register = json.loads(GAP_REGISTER_PATH.read_text(encoding="utf-8"))
    art_research = json.loads(ART_SOURCE_RESEARCH_PATH.read_text(encoding="utf-8"))
    capture_manifest = json.loads(CAPTURE_MANIFEST_PATH.read_text(encoding="utf-8"))
    capture_quality_review = json.loads(
        CAPTURE_QUALITY_REVIEW_PATH.read_text(encoding="utf-8")
    )
    flow_variant_capture_plan = json.loads(
        FLOW_VARIANT_CAPTURE_PLAN_PATH.read_text(encoding="utf-8")
    )
    flow_variant_capture_manifest = json.loads(
        FLOW_VARIANT_CAPTURE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    flow_variant_capture_quality_review = json.loads(
        FLOW_VARIANT_CAPTURE_QUALITY_REVIEW_PATH.read_text(encoding="utf-8")
    )
    flow_variant_human_lifelike_review_handoff = json.loads(
        FLOW_VARIANT_HUMAN_LIFELIKE_REVIEW_HANDOFF_PATH.read_text(encoding="utf-8")
    )
    flow_variant_environment_performance_review = json.loads(
        FLOW_VARIANT_ENVIRONMENT_PERFORMANCE_REVIEW_PATH.read_text(encoding="utf-8")
    )

    asset_plan = "unreal/Content/RaftSim/Rendering/first_party_procedural_environment_assets.json"
    material_plan = (
        "unreal/Content/RaftSim/Rendering/first_party_procedural_material_recipes.json"
    )
    swatch_manifest = str(SWATCH_MANIFEST_RELATIVE_PATH)
    texture_atlas_manifest = str(TEXTURE_ATLAS_MANIFEST_RELATIVE_PATH)
    source_conditioned_material_map_manifest = str(
        SOURCE_CONDITIONED_MATERIAL_MAP_MANIFEST_RELATIVE_PATH
    )
    source_conditioned_material_map_status = (
        "generated_review_gated_source_conditioned_material_maps_not_lifelike"
    )
    source_conditioned_material_map_summary = {
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
    source_conditioned_material_texture_asset_root = str(
        SOURCE_CONDITIONED_MATERIAL_TEXTURE_ASSET_ROOT_RELATIVE_PATH
    )
    source_conditioned_material_texture_asset_status = (
        SOURCE_CONDITIONED_MATERIAL_TEXTURE_ASSET_STATUS
    )
    source_conditioned_material_instance_binding_status = "bound_to_review_material_instance_parameters_with_regenerated_capture_review_not_lifelike"
    texture_asset_root = (
        "unreal/Content/RaftSim/Rendering/ProceduralTextureAtlases/Textures"
    )
    texture_asset_status = "created_unreal_texture2d_review_assets_bound_to_material_instance_candidates_not_lifelike"
    atlas_sampler_material = (
        "unreal/Content/RaftSim/Materials/M_RaftSim_AtlasSampleReview.uasset"
    )
    atlas_sampler_status = (
        "created_unreal_atlas_sampler_review_parent_material_not_lifelike"
    )
    scene_assignment_status = (
        "assigned_review_material_instances_to_preview_map_surface_proxies_not_lifelike"
    )
    material_instance_candidate_manifest = (
        "unreal/Content/RaftSim/Rendering/first_party_material_instance_candidates.json"
    )
    geospatial_attachment_ledger = (
        "physics/data/real_world/production_geospatial_attachment_ledger.json"
    )
    geospatial_attachment_audit = (
        "physics/data/real_world/production_geospatial_source_attachment_audit.json"
    )
    additional_source_leads_review = (
        "physics/data/real_world/production_additional_source_leads_review.json"
    )
    production_flow_variant_intake = (
        "physics/data/real_world/production_flow_variant_intake.json"
    )
    flow_variant_capture_plan_path = str(FLOW_VARIANT_CAPTURE_PLAN_RELATIVE_PATH)
    flow_variant_capture_plan_status = (
        "band_named_flow_variant_captures_available_not_lifelike_approved"
    )
    flow_variant_capture_manifest_path = "docs/environment-captures/photoreal_river_previews/flow_variant_capture_manifest.json"
    flow_variant_capture_manifest_status = (
        "all_band_named_flow_variant_previews_captured_not_lifelike_approved"
    )
    flow_variant_capture_quality_review_path = str(
        FLOW_VARIANT_CAPTURE_QUALITY_REVIEW_RELATIVE_PATH
    )
    flow_variant_capture_quality_review_status = (
        EXPECTED_FLOW_VARIANT_CAPTURE_QUALITY_STATUS
    )
    flow_variant_human_lifelike_review_handoff_path = str(
        FLOW_VARIANT_HUMAN_LIFELIKE_REVIEW_HANDOFF_RELATIVE_PATH
    )
    flow_variant_human_lifelike_review_handoff_status = (
        "awaiting_flow_variant_human_lifelike_review_not_approved"
    )
    flow_variant_environment_performance_review_path = str(
        FLOW_VARIANT_ENVIRONMENT_PERFORMANCE_REVIEW_RELATIVE_PATH
    )
    flow_variant_environment_performance_review_status = (
        "awaiting_measured_flow_variant_desktop_vr_performance_capture_not_approved"
    )
    production_visual_source_acquisition_queue = (
        "physics/data/real_world/production_visual_source_acquisition_queue.json"
    )
    production_visual_source_item_intake = (
        "physics/data/real_world/production_visual_source_item_intake.json"
    )
    capture_quality_review_path = str(CAPTURE_QUALITY_REVIEW_RELATIVE_PATH)
    capture_quality_review_status = EXPECTED_CAPTURE_QUALITY_STATUS
    human_lifelike_review_handoff_path = str(
        HUMAN_LIFELIKE_REVIEW_HANDOFF_RELATIVE_PATH
    )
    human_lifelike_review_handoff_status = "awaiting_human_lifelike_review_not_approved"
    human_lifelike_review_packet_path = str(HUMAN_LIFELIKE_REVIEW_PACKET_RELATIVE_PATH)
    human_lifelike_review_packet_status = "awaiting_human_lifelike_review_not_approved"
    human_lifelike_review_packet_summary = {
        "river_count": 3,
        "capture_count": 6,
        "review_domain_count": 7,
        "open_human_review_gate_count": 21,
    }
    human_lifelike_review_results_template_path = str(
        HUMAN_LIFELIKE_REVIEW_RESULTS_TEMPLATE_RELATIVE_PATH
    )
    human_lifelike_review_results_template_status = (
        "awaiting_external_human_review_inputs_not_approved"
    )
    human_lifelike_review_results_template_summary = {
        "river_count": 3,
        "capture_count": 6,
        "review_domain_count": 7,
        "open_review_result_count": 21,
        "approved_river_count": 0,
    }
    assert source_plan["first_party_procedural_asset_plan"] == asset_plan
    assert source_plan["first_party_procedural_material_recipe_plan"] == material_plan
    assert source_plan["first_party_material_swatch_manifest"] == swatch_manifest
    assert (
        source_plan["first_party_material_texture_atlas_manifest"]
        == texture_atlas_manifest
    )
    assert (
        source_plan["production_flow_variant_intake"] == production_flow_variant_intake
    )
    assert (
        source_plan["photoreal_flow_variant_capture_plan"]
        == flow_variant_capture_plan_path
    )
    assert (
        source_plan["flow_variant_capture_manifest"]
        == flow_variant_capture_manifest_path
    )
    assert (
        source_plan["flow_variant_capture_manifest_status"]
        == flow_variant_capture_manifest_status
    )
    assert (
        source_plan["flow_variant_capture_quality_review"]
        == flow_variant_capture_quality_review_path
    )
    assert (
        source_plan["flow_variant_capture_quality_review_status"]
        == flow_variant_capture_quality_review_status
    )
    assert (
        source_plan["flow_variant_human_lifelike_review_handoff"]
        == flow_variant_human_lifelike_review_handoff_path
    )
    assert (
        source_plan["flow_variant_human_lifelike_review_handoff_status"]
        == flow_variant_human_lifelike_review_handoff_status
    )
    assert (
        source_plan["flow_variant_environment_performance_review"]
        == flow_variant_environment_performance_review_path
    )
    assert (
        source_plan["flow_variant_environment_performance_review_status"]
        == flow_variant_environment_performance_review_status
    )
    assert (
        source_plan["source_conditioned_material_map_manifest"]
        == source_conditioned_material_map_manifest
    )
    assert (
        source_plan["source_conditioned_material_map_status"]
        == source_conditioned_material_map_status
    )
    assert (
        source_plan["source_conditioned_material_texture_asset_root"]
        == source_conditioned_material_texture_asset_root
    )
    assert (
        source_plan["source_conditioned_material_texture_asset_status"]
        == source_conditioned_material_texture_asset_status
    )
    assert (
        source_plan["source_conditioned_material_instance_binding_status"]
        == source_conditioned_material_instance_binding_status
    )
    assert source_plan["first_party_material_texture_asset_root"] == texture_asset_root
    assert (
        source_plan["first_party_material_texture_asset_status"] == texture_asset_status
    )
    assert (
        source_plan["first_party_atlas_sampler_review_material"]
        == atlas_sampler_material
    )
    assert (
        source_plan["first_party_atlas_sampler_review_material_status"]
        == atlas_sampler_status
    )
    assert (
        source_plan["first_party_material_instance_scene_assignment_status"]
        == scene_assignment_status
    )
    assert (
        source_plan["first_party_material_instance_candidate_manifest"]
        == material_instance_candidate_manifest
    )
    assert source_plan["geospatial_attachment_ledger"] == geospatial_attachment_ledger
    assert (
        source_plan["geospatial_source_attachment_audit"] == geospatial_attachment_audit
    )
    assert (
        source_plan["additional_source_leads_review"] == additional_source_leads_review
    )
    assert (
        source_plan["production_visual_source_acquisition_queue"]
        == production_visual_source_acquisition_queue
    )
    assert (
        source_plan["production_visual_source_item_intake"]
        == production_visual_source_item_intake
    )
    assert (
        source_plan["photoreal_capture_quality_review"] == capture_quality_review_path
    )
    assert (
        source_plan["photoreal_capture_quality_review_status"]
        == capture_quality_review_status
    )
    assert (
        source_plan["photoreal_human_lifelike_review_handoff"]
        == human_lifelike_review_handoff_path
    )
    assert (
        source_plan["photoreal_human_lifelike_review_handoff_status"]
        == human_lifelike_review_handoff_status
    )
    assert (
        source_plan["photoreal_human_lifelike_review_packet"]
        == human_lifelike_review_packet_path
    )
    assert (
        source_plan["photoreal_human_lifelike_review_packet_status"]
        == human_lifelike_review_packet_status
    )
    assert (
        source_plan["photoreal_human_lifelike_review_results_template"]
        == human_lifelike_review_results_template_path
    )
    assert (
        source_plan["photoreal_human_lifelike_review_results_template_status"]
        == human_lifelike_review_results_template_status
    )
    assert GEOSPATIAL_ATTACHMENT_LEDGER_PATH.exists()
    assert GEOSPATIAL_ATTACHMENT_AUDIT_PATH.exists()
    assert ADDITIONAL_SOURCE_LEADS_REVIEW_PATH.exists()
    assert PRODUCTION_FLOW_VARIANT_INTAKE_PATH.exists()
    assert FLOW_VARIANT_CAPTURE_PLAN_PATH.exists()
    assert FLOW_VARIANT_CAPTURE_MANIFEST_PATH.exists()
    assert FLOW_VARIANT_CAPTURE_QUALITY_REVIEW_PATH.exists()
    assert FLOW_VARIANT_HUMAN_LIFELIKE_REVIEW_HANDOFF_PATH.exists()
    assert FLOW_VARIANT_ENVIRONMENT_PERFORMANCE_REVIEW_PATH.exists()
    assert PRODUCTION_VISUAL_SOURCE_ACQUISITION_QUEUE_PATH.exists()
    assert PRODUCTION_VISUAL_SOURCE_ITEM_INTAKE_PATH.exists()
    assert SOURCE_CONDITIONED_MATERIAL_MAP_MANIFEST_PATH.exists()
    assert CAPTURE_QUALITY_REVIEW_PATH.exists()
    assert HUMAN_LIFELIKE_REVIEW_HANDOFF_PATH.exists()
    assert HUMAN_LIFELIKE_REVIEW_PACKET_PATH.exists()
    assert HUMAN_LIFELIKE_REVIEW_RESULTS_TEMPLATE_PATH.exists()
    assert (
        source_plan["unreal_generation"]["first_party_procedural_asset_plan"]
        == asset_plan
    )
    assert (
        source_plan["unreal_generation"]["first_party_procedural_material_recipe_plan"]
        == material_plan
    )
    assert (
        source_plan["unreal_generation"]["first_party_material_swatch_manifest"]
        == swatch_manifest
    )
    assert (
        source_plan["unreal_generation"]["first_party_material_texture_atlas_manifest"]
        == texture_atlas_manifest
    )
    assert (
        source_plan["unreal_generation"]["source_conditioned_material_map_manifest"]
        == source_conditioned_material_map_manifest
    )
    assert (
        source_plan["unreal_generation"]["source_conditioned_material_map_status"]
        == source_conditioned_material_map_status
    )
    assert (
        source_plan["unreal_generation"]["source_conditioned_material_map_summary"]
        == source_conditioned_material_map_summary
    )
    assert (
        source_plan["unreal_generation"][
            "source_conditioned_material_texture_asset_root"
        ]
        == source_conditioned_material_texture_asset_root
    )
    assert (
        source_plan["unreal_generation"][
            "source_conditioned_material_texture_asset_status"
        ]
        == source_conditioned_material_texture_asset_status
    )
    assert (
        source_plan["unreal_generation"][
            "source_conditioned_material_instance_binding_status"
        ]
        == source_conditioned_material_instance_binding_status
    )
    assert (
        source_plan["unreal_generation"]["first_party_material_texture_asset_root"]
        == texture_asset_root
    )
    assert (
        source_plan["unreal_generation"]["first_party_material_texture_asset_status"]
        == texture_asset_status
    )
    assert (
        source_plan["unreal_generation"]["first_party_atlas_sampler_review_material"]
        == atlas_sampler_material
    )
    assert (
        source_plan["unreal_generation"][
            "first_party_atlas_sampler_review_material_status"
        ]
        == atlas_sampler_status
    )
    assert (
        source_plan["unreal_generation"][
            "first_party_material_instance_scene_assignment_status"
        ]
        == scene_assignment_status
    )
    assert (
        source_plan["unreal_generation"][
            "first_party_material_instance_candidate_manifest"
        ]
        == material_instance_candidate_manifest
    )
    assert (
        source_plan["unreal_generation"]["production_flow_variant_intake"]
        == production_flow_variant_intake
    )
    assert (
        source_plan["unreal_generation"]["photoreal_flow_variant_capture_plan"]
        == flow_variant_capture_plan_path
    )
    assert (
        source_plan["unreal_generation"]["photoreal_flow_variant_capture_plan_status"]
        == flow_variant_capture_plan_status
    )
    assert (
        source_plan["unreal_generation"]["photoreal_flow_variant_capture_plan_summary"]
        == flow_variant_capture_plan["summary"]
    )
    assert (
        source_plan["unreal_generation"]["flow_variant_capture_manifest"]
        == flow_variant_capture_manifest_path
    )
    assert (
        source_plan["unreal_generation"]["flow_variant_capture_manifest_status"]
        == flow_variant_capture_manifest_status
    )
    assert source_plan["unreal_generation"][
        "flow_variant_capture_manifest_capture_count"
    ] == len(flow_variant_capture_manifest["captures"])
    assert (
        source_plan["unreal_generation"]["flow_variant_capture_quality_review"]
        == flow_variant_capture_quality_review_path
    )
    assert (
        source_plan["unreal_generation"]["flow_variant_capture_quality_review_status"]
        == flow_variant_capture_quality_review_status
    )
    assert (
        source_plan["unreal_generation"]["flow_variant_capture_quality_review_summary"]
        == flow_variant_capture_quality_review["summary"]
    )
    assert (
        source_plan["unreal_generation"]["flow_variant_human_lifelike_review_handoff"]
        == flow_variant_human_lifelike_review_handoff_path
    )
    assert (
        source_plan["unreal_generation"][
            "flow_variant_human_lifelike_review_handoff_status"
        ]
        == flow_variant_human_lifelike_review_handoff_status
    )
    assert (
        source_plan["unreal_generation"][
            "flow_variant_human_lifelike_review_handoff_summary"
        ]
        == flow_variant_human_lifelike_review_handoff["summary"]
    )
    assert (
        source_plan["unreal_generation"]["flow_variant_environment_performance_review"]
        == flow_variant_environment_performance_review_path
    )
    assert (
        source_plan["unreal_generation"][
            "flow_variant_environment_performance_review_status"
        ]
        == flow_variant_environment_performance_review_status
    )
    assert (
        source_plan["unreal_generation"][
            "flow_variant_environment_performance_review_summary"
        ]
        == flow_variant_environment_performance_review["summary"]
    )
    assert (
        source_plan["unreal_generation"]["production_visual_source_acquisition_queue"]
        == production_visual_source_acquisition_queue
    )
    assert (
        source_plan["unreal_generation"]["production_visual_source_item_intake"]
        == production_visual_source_item_intake
    )
    assert (
        source_plan["unreal_generation"]["photoreal_capture_quality_review"]
        == capture_quality_review_path
    )
    assert (
        source_plan["unreal_generation"]["photoreal_capture_quality_review_status"]
        == capture_quality_review_status
    )
    assert (
        source_plan["unreal_generation"]["photoreal_capture_quality_summary"]
        == capture_quality_review["summary"]
    )
    assert (
        source_plan["unreal_generation"]["photoreal_human_lifelike_review_handoff"]
        == human_lifelike_review_handoff_path
    )
    assert (
        source_plan["unreal_generation"][
            "photoreal_human_lifelike_review_handoff_status"
        ]
        == human_lifelike_review_handoff_status
    )
    assert (
        source_plan["unreal_generation"][
            "photoreal_human_lifelike_review_handoff_summary"
        ]
        == json.loads(HUMAN_LIFELIKE_REVIEW_HANDOFF_PATH.read_text(encoding="utf-8"))[
            "summary"
        ]
    )
    assert (
        source_plan["unreal_generation"]["photoreal_human_lifelike_review_packet"]
        == human_lifelike_review_packet_path
    )
    assert (
        source_plan["unreal_generation"][
            "photoreal_human_lifelike_review_packet_status"
        ]
        == human_lifelike_review_packet_status
    )
    assert (
        source_plan["unreal_generation"][
            "photoreal_human_lifelike_review_packet_summary"
        ]
        == human_lifelike_review_packet_summary
    )
    assert (
        source_plan["unreal_generation"][
            "photoreal_human_lifelike_review_results_template"
        ]
        == human_lifelike_review_results_template_path
    )
    assert (
        source_plan["unreal_generation"][
            "photoreal_human_lifelike_review_results_template_status"
        ]
        == human_lifelike_review_results_template_status
    )
    assert (
        source_plan["unreal_generation"][
            "photoreal_human_lifelike_review_results_template_summary"
        ]
        == human_lifelike_review_results_template_summary
    )
    assert (
        source_plan["photoreal_flow_variant_capture_plan"]
        == flow_variant_capture_plan_path
    )
    assert (
        source_plan["photoreal_flow_variant_capture_plan_status"]
        == flow_variant_capture_plan_status
    )
    assert (
        source_plan["flow_variant_capture_manifest"]
        == flow_variant_capture_manifest_path
    )
    assert (
        source_plan["flow_variant_capture_manifest_status"]
        == flow_variant_capture_manifest_status
    )
    assert (
        source_plan["flow_variant_capture_quality_review"]
        == flow_variant_capture_quality_review_path
    )
    assert (
        source_plan["flow_variant_capture_quality_review_status"]
        == flow_variant_capture_quality_review_status
    )
    assert (
        source_plan["flow_variant_human_lifelike_review_handoff"]
        == flow_variant_human_lifelike_review_handoff_path
    )
    assert (
        source_plan["flow_variant_human_lifelike_review_handoff_status"]
        == flow_variant_human_lifelike_review_handoff_status
    )
    assert (
        source_plan["flow_variant_environment_performance_review"]
        == flow_variant_environment_performance_review_path
    )
    assert (
        source_plan["flow_variant_environment_performance_review_status"]
        == flow_variant_environment_performance_review_status
    )
    assert (
        "approved_first_party_procedural_asset_recipes_or_rights_cleared_equivalent_assets"
        in source_plan["unreal_generation"]["final_acceptance"]
    )
    assert (
        "approved_first_party_material_recipe_manifest_or_rights_cleared_material_assets"
        in source_plan["unreal_generation"]["final_acceptance"]
    )
    assert (
        "approved_first_party_texture_atlas_import_or_rights_cleared_texture_assets"
        in source_plan["unreal_generation"]["final_acceptance"]
    )
    assert (
        "production_material_instances_using_albedo_normal_ao_roughness_height_maps"
        in source_plan["unreal_generation"]["final_acceptance"]
    )
    assert (
        "approved_unreal_material_instances_using_atlas_maps_or_rights_cleared_equivalent_textures"
        in source_plan["unreal_generation"]["final_acceptance"]
    )
    assert (
        "automated_capture_quality_gate_passed_without_proxy_blockers"
        in source_plan["unreal_generation"]["final_acceptance"]
    )
    assert (
        "approved_item_level_visual_source_acquisition_queue_promotions"
        in source_plan["unreal_generation"]["final_acceptance"]
    )
    assert (
        "approved_visual_source_item_intake_promotions"
        in source_plan["unreal_generation"]["final_acceptance"]
    )
    assert (
        "approved_flow_variant_intake_promotions"
        in source_plan["unreal_generation"]["final_acceptance"]
    )
    assert (
        "approved_band_named_flow_variant_capture_review"
        in source_plan["unreal_generation"]["final_acceptance"]
    )
    assert (
        "first_party_procedural_lit_vertex_color_water_gradients_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_lit_water_normal_response_scaffold_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_mask_aware_ground_cover_and_canopy_cards_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "guide_seat_foliage_setback_and_scale_tuning_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_procedural_material_recipe_manifest_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_material_review_swatches_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_material_texture_atlas_manifest_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "source_conditioned_material_map_manifest_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "source_conditioned_macro_albedo_material_maps_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "source_conditioned_material_zone_maps_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "source_conditioned_ao_roughness_height_maps_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "source_conditioned_normal_detail_material_maps_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "source_conditioned_normal_detail_material_blend_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "photoreal_flow_variant_capture_plan_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "source_conditioned_material_texture2d_review_assets_declared_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "source_conditioned_material_instance_texture_bindings_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "source_conditioned_material_zone_weight_controls_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "source_conditioned_shader_graph_sampler_wiring_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_material_texture_atlas_vertex_color_application_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_material_instance_candidate_manifest_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_material_instance_review_assets_created_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_material_texture2d_review_assets_created_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_material_instance_texture_asset_bindings_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_atlas_sampler_review_parent_material_created_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_material_shader_graph_sampler_wiring_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_material_instance_scene_assignment_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "photoreal_capture_quality_review_blockers_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_integrated_corridor_water_terrain_capture_grade_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "automated_capture_quality_gate_passed_without_proxy_blockers_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "photoreal_human_lifelike_review_handoff_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "photoreal_human_lifelike_review_packet_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "zero_blocker_capture_set_human_review_domains_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "zero_blocker_capture_set_review_packet_markdown_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "photoreal_human_lifelike_review_results_template_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "production_flow_variant_intake_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "production_visual_source_acquisition_queue_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "production_visual_source_item_intake_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        source_plan["unreal_generation"][
            "first_party_material_instance_review_asset_root"
        ]
        == "unreal/Content/RaftSim/Materials/MaterialInstances"
    )
    assert (
        source_plan["unreal_generation"][
            "first_party_material_instance_review_asset_status"
        ]
        == "created_unreal_material_instance_constant_review_assets_with_texture_bindings_sampler_parent_and_scene_assignment_not_lifelike_pending_capture_guide_review_hazard_readability_performance_evidence_and_production_promotion"
    )
    assert (
        "first_party_atlas_normal_ao_roughness_height_preview_response_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "softened_source_drape_overlay_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "source_drape_albedo_normalization_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_feathered_source_drape_microtiles_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "flow_aware_bank_undercut_shelf_relief_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "source_aware_bank_breakup_texture_patches_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_irregular_shoreline_edge_breakup_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_source_masked_shoreline_lip_overhang_edge_breakup_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "soft_feathered_terrain_material_patches_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_terrain_material_layer_facets_and_slope_shadow_patches_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_landscape_nanite_material_layer_scaffold_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_terrain_erosion_rill_and_bank_gully_detail_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_lit_terrain_vertex_color_material_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "soft_lit_terrain_vertex_color_review_material_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_photographic_terrain_emissive_calibration_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_terrain_contrast_and_normal_calibration_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_bounded_terrain_ambient_fill_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_source_aware_terrain_photo_mottle_and_microrelief_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_source_conditioned_far_bank_albedo_calibration_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_broad_slope_terrain_exposure_fill_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_source_aware_macro_terrain_ridge_facets_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_source_aware_terrain_slope_facet_texture_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_source_aware_terrain_surface_granularity_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_source_aware_riparian_canopy_mass_texture_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_rainforest_river_eye_slope_texture_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_source_overlay_plate_artifact_demotion_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_procedural_only_foliage_review_path_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_procedural_canopy_height_massing_profile_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_procedural_canopy_tone_shadow_profile_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_foliage_card_canopy_artifact_demotion_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_square_foliage_source_card_artifact_demotion_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_remaining_square_card_cull_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_base_terrain_material_grain_and_microrelief_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_demoted_terrain_overlay_striping_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_source_drape_smoothing_pass_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_segmented_wet_bank_ribbons_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_graphic_waterline_ribbon_demotion_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_pale_bank_shoreline_scaffold_slash_demotion_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_demoted_source_detail_contours_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_post_contour_terrain_readability_fill_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_source_masked_bank_bar_microgeometry_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_near_field_riverbed_debris_and_pebble_dressing_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "terrain_proxy_luma_floor_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "shadowless_terrain_albedo_review_capture_material_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "flow_aware_waterline_pebble_scatter_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_irregular_rock_geometry_variants_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_boulder_wetness_abrasion_moss_surface_variants_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_boulder_crevice_shadow_and_albedo_tuning_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "near_camera_boulder_readability_clearance_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "near_camera_boulder_occlusion_demotion_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "flow_aware_water_mesh_undulation_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_smoothed_near_field_water_surface_faceting_demotion_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "flow_band_depth_texture_ribbons_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "flow_aware_water_surface_chop_and_turbidity_patches_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_turbidity_depth_patch_artifact_demotion_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "flow_aware_micro_ripple_glints_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "near_frame_water_ribbon_occlusion_demotion_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_near_frame_shoreline_scaffold_demotion_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_water_shader_depth_reflection_refraction_scaffold_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_shallow_water_clarity_and_aeration_layer_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "near_camera_water_scaffold_readability_clearance_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "low_occlusion_far_field_water_shader_scaffold_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_remaining_water_overlay_slab_demotion_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_pale_water_foam_slash_demotion_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_long_dark_water_streak_demotion_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_current_streak_waterline_artifact_demotion_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_central_water_scaffold_plate_demotion_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_base_water_center_guide_stripe_breakup_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_base_water_cross_channel_breakup_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_base_water_residual_center_seam_erase_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_dark_micro_ripple_artifact_demotion_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_photographic_water_exposure_calibration_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_photographic_color_grade_palette_compression_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_near_field_water_surface_grain_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_near_camera_water_macro_ripple_mottle_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_near_camera_bottom_center_water_wedge_demotion_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_near_camera_upstream_water_capture_apron_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_base_water_depth_current_grading_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_base_water_flow_thread_texture_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_flow_cued_water_foam_slick_mottle_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_integrated_base_water_chroma_microbreakup_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_integrated_water_fleck_microtexture_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_integrated_water_bank_entropy_edge_detail_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_integrated_river_eye_water_entropy_mottle_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_flow_dependent_hydraulic_aeration_spray_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "biome_specific_deadfall_grass_root_ecology_props_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_biome_foliage_silhouette_proxy_layers_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_dense_biome_foliage_layer_proxy_clusters_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_instanced_procedural_foliage_equivalent_scaffold_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_blocky_bank_ecology_and_sphere_foliage_cull_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_procedural_leaf_cluster_geometry_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_organic_canopy_leaf_spray_breakup_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_organic_branch_frond_lattice_foliage_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_fine_twig_canopy_lace_foliage_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_photographic_foliage_tone_calibration_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_foliage_crown_depth_and_leaflet_breakup_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "boulder_contact_foam_lace_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "pacuare_waterfall_curtain_plunge_mist_and_runout_proxies_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "river_specific_cloud_haze_and_horizon_backdrop_cards_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_source_aware_sky_gradient_and_atmosphere_depth_layers_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_guide_seat_raft_and_oar_foreground_proxies_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_refined_raft_oar_foreground_proxy_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_rounded_raft_oar_foreground_proxy_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_tagged_river_eye_foreground_proxy_cull_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_guide_seat_foreground_proxy_capture_cull_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_river_eye_near_field_dressing_cull_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_dedicated_river_eye_downstream_capture_camera_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_centerline_following_river_eye_capture_camera_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_low_luma_foreground_raft_proxy_demotion_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_near_field_water_source_tile_demotion_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_near_field_water_patch_tile_breakup_demotion_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_continuous_near_field_water_current_blend_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_water_review_material_source_texture_tile_cull_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_near_field_inboard_bank_shelf_cull_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_near_camera_inwater_debris_occlusion_cull_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "first_party_textured_river_eye_center_artifact_cover_recorded"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    assert (
        "approved_raft_and_oar_foreground_art"
        in source_plan["unreal_generation"]["final_acceptance"]
    )
    assert (
        "geospatial_attachment_ledger_visible_in_capture_manifest"
        in source_plan["unreal_generation"]["first_pass_acceptance"]
    )
    rivers = {river["river_id"]: river for river in source_plan["rivers"]}
    south_fork_artifacts = {
        artifact["artifact_id"]
        for artifact in rivers["american_south_fork"]["source_sample_artifacts"]
    }
    assert (
        "south_fork_cdec_seasonal_window_review_wy2026_to_2026_07_06"
        in south_fork_artifacts
    )
    assert (
        "south_fork_cdec_multiyear_flow_review_2021_10_01_2026_07_06"
        in south_fork_artifacts
    )
    assert "south_fork_source_metadata_review" in south_fork_artifacts
    colorado_artifacts = {
        artifact["artifact_id"]
        for artifact in rivers["colorado_river"]["source_sample_artifacts"]
    }
    assert "colorado_source_metadata_review" in colorado_artifacts
    pacuare_artifacts = {
        artifact["artifact_id"]
        for artifact in rivers["pacuare"]["source_sample_artifacts"]
    }
    assert "pacuare_source_metadata_review" in pacuare_artifacts
    assert "pacuare_high_resolution_scene_metadata_review" in pacuare_artifacts
    assert "pacuare_landsat_product_access_gate_review" in pacuare_artifacts
    assert "pacuare_local_imagery_alternative_source_review" in pacuare_artifacts
    assert "pacuare_sentinel_cog_thumbnail_review" in pacuare_artifacts
    assert "pacuare_sentinel_cog_access_probe" in pacuare_artifacts
    assert "pacuare_sentinel_tci_review_preview" in pacuare_artifacts
    assert "pacuare_sentinel_tci_16phr_review_preview" in pacuare_artifacts
    assert "pacuare_sentinel_corridor_tile_coverage_review" in pacuare_artifacts
    assert "pacuare_sentinel_corridor_bbox_clip_review" in pacuare_artifacts
    assert "pacuare_sentinel_corridor_bbox_scl_qa_review" in pacuare_artifacts
    assert "pacuare_sentinel_cleaner_scene_search_review" in pacuare_artifacts
    assert "pacuare_sentinel_20250320_scl_qa_review" in pacuare_artifacts
    assert "pacuare_sentinel_20250320_tci_bbox_clip_review" in pacuare_artifacts
    assert "pacuare_sentinel_augmented_source_drape_preview" in pacuare_artifacts
    assert "pacuare_sentinel_20250320_draft_bank_window_review" in pacuare_artifacts
    assert "pacuare_sentinel_20250305_draft_bank_scl_probe" in pacuare_artifacts
    assert "pacuare_sentinel_20240204_draft_bank_scl_probe" in pacuare_artifacts
    assert "pacuare_sentinel_20240204_draft_bank_tci_review" in pacuare_artifacts
    assert "pacuare_sentinel_20240224_draft_bank_scl_probe" in pacuare_artifacts

    assert (
        gap_register["canonical_inputs"]["first_party_procedural_environment_assets"]
        == asset_plan
    )
    assert (
        gap_register["canonical_inputs"]["first_party_procedural_material_recipes"]
        == material_plan
    )
    assert (
        gap_register["canonical_inputs"]["first_party_material_swatches"]
        == swatch_manifest
    )
    assert (
        gap_register["canonical_inputs"]["first_party_material_texture_atlases"]
        == texture_atlas_manifest
    )
    assert (
        gap_register["canonical_inputs"]["production_flow_variant_intake"]
        == production_flow_variant_intake
    )
    assert (
        gap_register["canonical_inputs"]["source_conditioned_material_map_manifest"]
        == source_conditioned_material_map_manifest
    )
    assert (
        gap_register["canonical_inputs"]["source_conditioned_material_map_status"]
        == source_conditioned_material_map_status
    )
    assert (
        gap_register["canonical_inputs"]["source_conditioned_material_map_summary"]
        == source_conditioned_material_map_summary
    )
    assert (
        gap_register["canonical_inputs"][
            "source_conditioned_material_texture_asset_root"
        ]
        == source_conditioned_material_texture_asset_root
    )
    assert (
        gap_register["canonical_inputs"][
            "source_conditioned_material_texture_asset_status"
        ]
        == source_conditioned_material_texture_asset_status
    )
    assert (
        gap_register["canonical_inputs"][
            "source_conditioned_material_instance_binding_status"
        ]
        == source_conditioned_material_instance_binding_status
    )
    assert (
        gap_register["canonical_inputs"]["first_party_material_texture_assets"]
        == texture_asset_root
    )
    assert (
        gap_register["canonical_inputs"]["first_party_material_texture_asset_status"]
        == texture_asset_status
    )
    assert (
        gap_register["canonical_inputs"]["first_party_atlas_sampler_review_material"]
        == atlas_sampler_material
    )
    assert (
        gap_register["canonical_inputs"][
            "first_party_atlas_sampler_review_material_status"
        ]
        == atlas_sampler_status
    )
    assert (
        gap_register["canonical_inputs"][
            "first_party_material_instance_scene_assignment_status"
        ]
        == scene_assignment_status
    )
    assert (
        gap_register["canonical_inputs"]["first_party_material_instance_candidates"]
        == material_instance_candidate_manifest
    )
    assert (
        gap_register["canonical_inputs"]["geospatial_attachment_ledger"]
        == geospatial_attachment_ledger
    )
    assert (
        gap_register["canonical_inputs"]["geospatial_source_attachment_audit"]
        == geospatial_attachment_audit
    )
    assert (
        gap_register["canonical_inputs"]["additional_source_leads_review"]
        == additional_source_leads_review
    )
    assert (
        gap_register["canonical_inputs"]["production_visual_source_acquisition_queue"]
        == production_visual_source_acquisition_queue
    )
    assert (
        gap_register["canonical_inputs"]["production_visual_source_item_intake"]
        == production_visual_source_item_intake
    )
    assert (
        gap_register["canonical_inputs"]["photoreal_capture_quality_review"]
        == capture_quality_review_path
    )
    assert (
        gap_register["canonical_inputs"]["photoreal_capture_quality_review_status"]
        == capture_quality_review_status
    )
    assert (
        gap_register["canonical_inputs"]["photoreal_human_lifelike_review_handoff"]
        == human_lifelike_review_handoff_path
    )
    assert (
        gap_register["canonical_inputs"][
            "photoreal_human_lifelike_review_handoff_status"
        ]
        == human_lifelike_review_handoff_status
    )
    assert (
        gap_register["canonical_inputs"]["photoreal_human_lifelike_review_packet"]
        == human_lifelike_review_packet_path
    )
    assert (
        gap_register["canonical_inputs"][
            "photoreal_human_lifelike_review_packet_status"
        ]
        == human_lifelike_review_packet_status
    )
    assert (
        gap_register["canonical_inputs"][
            "photoreal_human_lifelike_review_packet_summary"
        ]
        == human_lifelike_review_packet_summary
    )
    assert (
        gap_register["canonical_inputs"][
            "photoreal_human_lifelike_review_results_template"
        ]
        == human_lifelike_review_results_template_path
    )
    assert (
        gap_register["canonical_inputs"][
            "photoreal_human_lifelike_review_results_template_status"
        ]
        == human_lifelike_review_results_template_status
    )
    assert (
        gap_register["canonical_inputs"][
            "photoreal_human_lifelike_review_results_template_summary"
        ]
        == human_lifelike_review_results_template_summary
    )
    terrain_target = next(
        target
        for target in gap_register["global_visual_replacement_targets"]
        if target["target"] == "terrain_and_banks"
    )
    assert (
        "first_party_procedural_asset_recipe_coverage_or_rights_cleared_equivalent_assets"
        in terrain_target["required_before_lifelike"]
    )
    assert (
        "first_party_procedural_material_recipe_manifest_coverage_or_rights_cleared_material_assets"
        in terrain_target["required_before_lifelike"]
    )
    assert (
        "first_party_material_swatch_review_or_rights_cleared_material_reference"
        in terrain_target["required_before_lifelike"]
    )
    assert (
        "first_party_importable_texture_atlas_review_or_rights_cleared_texture_assets"
        in terrain_target["required_before_lifelike"]
    )
    assert (
        "reviewed_in_engine_first_party_texture_atlas_application_or_rights_cleared_equivalent_materials"
        in terrain_target["required_before_lifelike"]
    )
    assert (
        "reviewed_bound_unreal_texture2d_material_instances_or_rights_cleared_equivalent_materials"
        in terrain_target["required_before_lifelike"]
    )
    assert (
        "reviewed_atlas_sampler_parent_material_or_rights_cleared_equivalent_shader_graph"
        in terrain_target["required_before_lifelike"]
    )
    assert (
        "review_material_instance_scene_assignment_capture_review_and_production_promotion"
        in terrain_target["required_before_lifelike"]
    )
    assert (
        "automated_capture_quality_gate_passed_without_proxy_blockers"
        in terrain_target["required_before_lifelike"]
    )
    assert (
        "approved_unreal_material_instances_from_candidate_manifest_or_rights_cleared_equivalent_materials"
        in terrain_target["required_before_lifelike"]
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"]["plan"]
        == asset_plan
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "material_recipe_plan"
        ]
        == material_plan
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "material_swatch_manifest"
        ]
        == swatch_manifest
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "material_texture_atlas_manifest"
        ]
        == texture_atlas_manifest
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "source_conditioned_material_map_manifest"
        ]
        == source_conditioned_material_map_manifest
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "source_conditioned_material_map_status"
        ]
        == source_conditioned_material_map_status
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "source_conditioned_material_map_summary"
        ]
        == source_conditioned_material_map_summary
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "source_conditioned_material_texture_asset_root"
        ]
        == source_conditioned_material_texture_asset_root
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "source_conditioned_material_texture_asset_status"
        ]
        == source_conditioned_material_texture_asset_status
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "source_conditioned_material_instance_binding_status"
        ]
        == source_conditioned_material_instance_binding_status
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "material_texture_asset_root"
        ]
        == texture_asset_root
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "material_texture_asset_status"
        ]
        == texture_asset_status
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "texture_atlas_unreal_import_status"
        ]
        == "nine_unreal_texture2d_review_assets_created_with_recorded_import_settings_not_lifelike_evidence"
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "atlas_sampler_review_material"
        ]
        == atlas_sampler_material
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "atlas_sampler_review_material_status"
        ]
        == atlas_sampler_status
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "shader_graph_sampler_wiring_status"
        ]
        == "review_parent_material_samples_albedo_normal_ao_roughness_height_atlases_with_preview_color_vertex_color_weight_and_roughness_floor_not_lifelike_evidence"
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "material_instance_candidate_manifest"
        ]
        == material_instance_candidate_manifest
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "texture_atlas_renderer_application_status"
        ]
        == "albedo_tiles_sampled_into_preview_vertex_colors_for_terrain_water_boulders_foliage_and_raft_oars_review_only_not_lifelike_evidence"
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "texture_atlas_normal_packed_renderer_application_status"
        ]
        == "normal_and_packed_ao_roughness_height_tiles_sampled_into_bounded_preview_surface_response_and_tiny_microrelief_review_only_not_lifelike_evidence"
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "material_instance_candidate_status"
        ]
        == "candidate_paths_created_as_unreal_material_instance_constant_review_assets_with_bound_texture2d_atlases_sampler_parent_and_scene_assignment_not_promoted_to_lifelike_materials"
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "material_instance_review_asset_root"
        ]
        == "unreal/Content/RaftSim/Materials/MaterialInstances"
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "material_instance_review_asset_status"
        ]
        == "created_unreal_material_instance_constant_review_assets_with_texture_bindings_sampler_parent_and_scene_assignment_not_lifelike"
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "photoreal_capture_quality_review"
        ]
        == capture_quality_review_path
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "photoreal_capture_quality_review_status"
        ]
        == capture_quality_review_status
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "photoreal_capture_quality_blockers"
        ]
        == capture_quality_review["summary"]["blocker_counts"]
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "photoreal_human_lifelike_review_handoff"
        ]
        == human_lifelike_review_handoff_path
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "photoreal_human_lifelike_review_handoff_status"
        ]
        == human_lifelike_review_handoff_status
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "photoreal_human_lifelike_review_packet"
        ]
        == human_lifelike_review_packet_path
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "photoreal_human_lifelike_review_packet_status"
        ]
        == human_lifelike_review_packet_status
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "photoreal_human_lifelike_review_packet_summary"
        ]
        == human_lifelike_review_packet_summary
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "photoreal_human_lifelike_review_results_template"
        ]
        == human_lifelike_review_results_template_path
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "photoreal_human_lifelike_review_results_template_status"
        ]
        == human_lifelike_review_results_template_status
    )
    assert (
        art_research["first_party_procedural_equivalent_decision_2026_07_06"][
            "photoreal_human_lifelike_review_results_template_summary"
        ]
        == human_lifelike_review_results_template_summary
    )
    assert capture_manifest["procedural_asset_plan"] == asset_plan
    assert capture_manifest["procedural_material_recipe_plan"] == material_plan
    assert (
        capture_manifest["first_party_material_texture_atlas_manifest"]
        == texture_atlas_manifest
    )
    assert (
        capture_manifest["first_party_material_instance_candidate_manifest"]
        == material_instance_candidate_manifest
    )
    assert (
        capture_manifest["first_party_material_texture_asset_root"]
        == texture_asset_root
    )
    assert (
        capture_manifest["first_party_material_texture_asset_status"]
        == texture_asset_status
    )
    assert (
        capture_manifest["first_party_atlas_sampler_review_material"]
        == atlas_sampler_material
    )
    assert (
        capture_manifest["first_party_atlas_sampler_review_material_status"]
        == atlas_sampler_status
    )
    assert (
        capture_manifest["first_party_material_instance_scene_assignment_status"]
        == scene_assignment_status
    )
    assert (
        capture_manifest["first_party_material_instance_review_asset_root"]
        == "unreal/Content/RaftSim/Materials/MaterialInstances"
    )
    assert (
        capture_manifest["first_party_material_instance_review_asset_status"]
        == "created_unreal_material_instance_constant_review_assets_with_texture_bindings_sampler_parent_and_scene_assignment_not_lifelike"
    )
    assert (
        capture_manifest["geospatial_attachment_ledger"] == geospatial_attachment_ledger
    )
    assert all(
        "flow-dependent hydraulic aeration/spray mats and beads"
        in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "source-conditioned far-bank albedo/microrelief calibration"
        in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "first-party photographic color-grade palette compression"
        in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "broad-slope terrain exposure fill and relief" in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "source-aware macro terrain ridge/facet relief" in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "minimized source overlay plate artifacts" in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "graphic waterline ribbon demotion" in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "remaining water overlay slab demotion" in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "long dark water streak demotion" in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "current streak and waterline rail artifact demotion"
        in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "central water scaffold plate demotion" in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "base-water center guide-stripe breakup" in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "base-water cross-channel breakup" in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "base-water residual center-seam erase" in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "turbidity-depth patch artifact demotion" in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "dark micro-ripple artifact demotion" in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "first-party procedural-only foliage review path with stylized PCG sample tree meshes disabled"
        in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "first-party procedural canopy height and massing profile"
        in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "first-party procedural canopy tone compression and shadow profile"
        in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "first-party foliage card/canopy artifact demotion" in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "square foliage/source-card artifact demotion" in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "remaining square card cull" in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "first-party near-field riverbed pebble/debris dressing"
        in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "first-party source-masked shoreline lip/overhang edge breakup"
        in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "first-party source-aware terrain surface granularity"
        in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "first-party material texture atlas albedo tiles are sampled"
        in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
    assert all(
        "normal plus packed AO/roughness/height atlases drive bounded preview material response"
        in capture["fidelity_note"]
        for capture in capture_manifest["captures"]
    )
