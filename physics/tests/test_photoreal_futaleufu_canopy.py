# ruff: noqa: F405

from photoreal_test_support import *  # noqa: F401,F403


def test_ue_pve_futaleufu_beech_variants_are_headlessly_structurally_evaluated():
    editor_source = EDITOR_MODULE_PATH.read_text(encoding="utf-8")
    build_rules = EDITOR_BUILD_RULES_PATH.read_text(encoding="utf-8")
    plugin = json.loads(RAFTSIM_PLUGIN_PATH.read_text(encoding="utf-8"))
    source_manifest = json.loads(
        PVE_FUTALEUFU_BEECH_SOURCE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    reports = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in PVE_FUTALEUFU_BEECH_REPORT_PATHS
    ]

    assert "RaftSim.EvaluateProceduralBeechCandidate" in editor_source
    assert "RaftSim.InspectProceduralVegetationSample" in editor_source
    assert "Tree_European_Beech_01/Instances" in editor_source
    assert "PVGrowthDataLoaderSettings" in editor_source
    assert "UPCGDefaultExecutionSource" in editor_source
    assert "installed_unreal_engine_sample_evaluation_only" in editor_source
    for dependency in (
        "PCG",
        "ProceduralVegetation",
        "Chaos",
        "GeometryCollectionEngine",
    ):
        assert f'"{dependency}"' in build_rules
    plugin_dependencies = {entry["Name"] for entry in plugin["Plugins"]}
    assert {"PCG", "ProceduralVegetationEditor"}.issubset(plugin_dependencies)

    assert source_manifest["status"] == (
        "installed_engine_sample_hash_locked_local_visual_rejected_no_corridor_substitution"
    )
    assert source_manifest["production_promoted"] is False
    assert source_manifest["engine_version"] == "5.8"
    assert len(source_manifest["source_files"]) == 4
    assert (
        source_manifest["evaluation_contract"]["content_copied_into_repository"]
        is False
    )
    assert source_manifest["evaluation_contract"]["required_rhi"] == "offscreen_metal"
    assert source_manifest["evaluation_contract"]["null_rhi_supported"] is False
    assert (
        source_manifest["rights_boundary"]["open_source_redistribution_approved"]
        is False
    )
    assert source_manifest["species_boundary"]["native_futaleufu_species"] is False
    assert source_manifest["species_boundary"]["nothofagus_identity"] is False
    assert source_manifest["visual_review"]["status"] == (
        "rejected_at_isolated_visual_gate_no_corridor_substitution"
    )
    assert (REPO_ROOT / source_manifest["visual_review"]["report"]).is_file()
    assert source_manifest["visual_review"]["local_capture_count"] == 12
    assert source_manifest["visual_review"]["local_capture_files_committed"] is False
    for source in source_manifest["source_files"]:
        assert len(source["sha256"]) == 64
        assert source["bytes"] > 9_000_000
        assert (REPO_ROOT / source["structural_report"]).is_file()

    assert [report["variant"] for report in reports] == [
        "Beech_01",
        "Beech_02",
        "Beech_03",
        "Beech_04",
    ]
    assert {report["status"] for report in reports} == {
        "structurally_generated_local_review_export_ready_not_visual_or_production_promoted"
    }
    assert {report["engine_version"] for report in reports} == {"5.8"}
    assert {
        report["generated_collection"]["foliage_mesh_count"] for report in reports
    } == {5}
    assert [
        report["generated_collection"]["foliage_instance_count"] for report in reports
    ] == [
        765,
        815,
        201,
        389,
    ]
    for report in reports:
        generated = report["generated_collection"]
        assert generated["transform_count"] == 1
        assert generated["vertex_count"] > 50_000
        assert generated["triangle_count"] > 100_000
        assert len(generated["foliage_meshes"]) == 5
        local_export = report["local_review_export"]
        assert (
            local_export["status"]
            == "trunk_nanite_asset_and_foliage_template_generated_locally"
        )
        assert local_export["git_policy"] == (
            "generated_files_are_ignored_and_must_not_be_open_source_redistributed"
        )
        assert local_export["trunk_asset"].startswith(
            "/Game/RaftSim/Environment/GeneratedLocalReview/PVEFutaleufuEuropeanBeech/"
        )
        assert local_export["foliage_template"].startswith(
            "unreal/Saved/RaftSimPveReview/FutaleufuEuropeanBeech/"
        )
        validation = local_export["asset_validation"]
        assert validation["passed"] is True
        assert validation["nanite_enabled"] is True
        assert validation["nanite_shape_preservation"] == "preserve_area"
        assert validation["vertex_count_lod0"] > 3_000
        assert validation["triangle_count_lod0"] > 5_000
        assert validation["material_slot_count"] > 0
        assert (
            validation["non_null_material_count"] == validation["material_slot_count"]
        )
        assert all(size_cm > 0.0 for size_cm in validation["bounds_size_cm"])
        assert 800.0 < validation["bounds_size_cm"][2] < 2_600.0
        visual = report["local_visual_review"]
        assert (
            visual["status"]
            == "isolated_three_view_capture_ready_for_human_material_review"
        )
        assert (
            visual["git_policy"] == "generated_map_and_captures_are_local_and_ignored"
        )
        assert visual["foliage_mesh_count"] == 5
        assert visual["foliage_instance_count"] == generated["foliage_instance_count"]
        assert len(visual["captures"]) == 3
        assert report["rights_boundary"].startswith(
            "installed_unreal_engine_sample_evaluation_only"
        )
        assert report["species_boundary"].startswith("fagus_sylvatica_structure_analog")

    active_manifest = LANDSCAPE_CANDIDATE_MANIFEST_PATH.read_text(encoding="utf-8")
    assert "european_beech" not in active_manifest.lower()

    visual_review = json.loads(
        PVE_FUTALEUFU_BEECH_VISUAL_REVIEW_PATH.read_text(encoding="utf-8")
    )
    assert (
        visual_review["status"]
        == "rejected_at_isolated_visual_gate_no_corridor_substitution"
    )
    assert visual_review["production_promoted"] is False
    assert visual_review["corridor_substitution_performed"] is False
    assert visual_review["review_contract"]["rhi"] == "offscreen Metal"
    assert visual_review["review_contract"]["map_check_errors"] == 0
    assert visual_review["review_contract"]["map_check_warnings"] == 0
    assert len(visual_review["variants"]) == 4
    assert all(variant["decision"] == "reject" for variant in visual_review["variants"])
    assert all(len(variant["captures"]) == 3 for variant in visual_review["variants"])
    assert all(
        len(capture["sha256"]) == 64
        for variant in visual_review["variants"]
        for capture in variant["captures"]
    )
    assert len(visual_review["next_asset_requirements"]) == 5


def test_futaleufu_native_canopy_authoring_contract_is_ecological_and_first_party():
    spec = json.loads(
        FUTALEUFU_NATIVE_CANOPY_AUTHORING_SPEC_PATH.read_text(encoding="utf-8")
    )
    assert spec["status"] == (
        "coigue_candidate_reviewed_second_cypress_stratum_v13_donor_rejected_v14_opaque_geometry_pending"
    )
    assert spec["production_promoted"] is False
    assert len(spec["sources"]) == 6
    assert {band["id"] for band in spec["forest_bands"]} == {
        "low_valley_evergreen",
        "high_valley_lenga",
        "north_east_cordillera_cypress",
    }
    species = {
        entry["scientific_name"]
        for band in spec["forest_bands"]
        for entry in band["canopy_species"]
    }
    assert species == {
        "Nothofagus dombeyi",
        "Laureliopsis philippiana",
        "Podocarpus nubigenus",
        "Lomatia hirsuta",
        "Nothofagus pumilio",
        "Nothofagus antarctica",
        "Nothofagus betuloides",
        "Austrocedrus chilensis",
    }
    coigue = spec["coigue_reference_architecture"]
    assert coigue["adult_height_max_m"] == 40.0
    assert coigue["trunk_diameter_max_m"] == 2.5
    assert coigue["leaf_length_cm"] == [2.0, 3.5]
    contract = spec["first_party_asset_contract"]
    assert contract["minimum_species_count"] == 8
    assert contract["minimum_age_classes"] == 3
    assert len(contract["required_strata"]) == 7
    assert contract["target_height_classes_m"][-1] == [22.0, 40.0]
    gates = spec["promotion_gates"]
    assert "150 m proxy" in gates["isolated_views"]
    assert (
        "third-party source or derived content copied without redistribution approval"
        in (gates["automatic_reject_conditions"])
    )
    second_stratum = spec["second_canopy_stratum_decision"]
    assert second_stratum["scientific_name"] == "Austrocedrus chilensis"
    assert (
        second_stratum["decision"]
        == "selected_for_project_owned_isolated_asset_authoring"
    )
    assert second_stratum["production_promoted"] is False
    assert second_stratum["authoring_manifest"] == str(
        FUTALEUFU_CORDILLERA_CYPRESS_AUTHORING_MANIFEST_PATH.relative_to(REPO_ROOT)
    )


def test_futaleufu_cordillera_cypress_contract_is_local_bounded_and_first_party():
    manifest = json.loads(
        FUTALEUFU_CORDILLERA_CYPRESS_AUTHORING_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    assert (
        manifest["schema"] == "raftsim.unreal.futaleufu_cordillera_cypress_authoring.v1"
    )
    assert manifest["status"] == (
        "v17_project_graph_open_form_generated_visual_promotion_rejected"
    )
    assert manifest["production_promoted"] is False
    assert manifest["corridor_substitution_allowed"] is False
    assert manifest["species"]["scientific_name"] == "Austrocedrus chilensis"
    assert {source["publisher"] for source in manifest["authority_sources"]} == {
        "Corporacion Nacional Forestal (CONAF)",
        "Ministerio del Medio Ambiente de Chile, SIMBIO",
        "Instituto Forestal de Chile (INFOR)",
    }
    rights = manifest["provenance_and_rights_boundary"]
    assert rights["external_images_vendored"] is False
    assert rights["external_geometry_vendored"] is False
    assert rights["external_texture_pixels_vendored"] is False
    donors = {entry["id"]: entry for entry in manifest["morphology_donor_audit"]}
    assert set(donors) == {
        "polyhaven_fir_tree_01_cc0",
        "fab_western_red_cedar_tree_01",
        "fab_cypress_tree_collection",
    }
    assert donors["polyhaven_fir_tree_01_cc0"]["license"] == "CC0 1.0 Universal"
    assert donors["polyhaven_fir_tree_01_cc0"]["purchase_required"] is False
    assert (
        donors["polyhaven_fir_tree_01_cc0"]["v13_direct_geometry_donor_passed"] is False
    )
    assert (
        donors["polyhaven_fir_tree_01_cc0"]["legacy_import_bounds_contract_valid"]
        is False
    )
    assert donors["fab_western_red_cedar_tree_01"]["state"] == (
        "link_only_not_purchased_or_vendored"
    )
    assert all(not donor["native_species_claim_allowed"] for donor in donors.values())
    placement = manifest["ecological_placement_contract"]
    assert placement["source_authority_elevation_m"] == [400.0, 1500.0]
    assert placement["initial_corridor_review_elevation_m"] == [400.0, 900.0]
    assert placement["required_geographic_aspects"] == ["north", "northeast", "east"]
    assert placement["true_north_transform_required"] is True
    assert placement["maximum_share_of_total_corridor_canopy_review_heuristic"] <= 0.18
    asset = manifest["asset_contract"]
    assert asset["texture_candidate_manifest"] == str(
        FUTALEUFU_CORDILLERA_CYPRESS_TEXTURE_MANIFEST_PATH.relative_to(REPO_ROOT)
    )
    assert len(asset["adult_variants"]) == 5
    assert len(asset["intermediate_variants"]) == 3
    assert "layered branch sprays" in asset["foliage_representation"]
    assert (
        "tile-bounded transparent RGB mip padding" in asset["texture_requirements"][2]
    )
    assert "V23" in asset["shadow_policy"]
    rejects = manifest["promotion_gates"]["automatic_reject_conditions"]
    assert "uniform corridor-wide distribution" in rejects
    assert "placement without a verified true-north transform" in rejects


def test_futaleufu_cordillera_cypress_textures_are_reproducible_review_candidates():
    manifest = json.loads(
        FUTALEUFU_CORDILLERA_CYPRESS_TEXTURE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    assert (
        manifest["schema"] == "raftsim.unreal.futaleufu_cordillera_cypress_textures.v3"
    )
    assert manifest["status"] == (
        "first_party_cypress_texture_candidates_ready_for_isolated_unreal_review"
    )
    assert manifest["production_promoted"] is False
    assert manifest["corridor_use_allowed"] is False
    assert manifest["species"]["scientific_name"] == "Austrocedrus chilensis"

    generator_path = (
        REPO_ROOT / "physics/src/raftsim/futaleufu_cordillera_cypress_assets.py"
    )
    for source in manifest["sources"].values():
        source_path = REPO_ROOT / source["path"]
        assert source_path.is_file()
        assert _sha256(source_path) == source["sha256"]
        assert source["generator_path"] == str(generator_path.relative_to(REPO_ROOT))
        assert source["generator_sha256"] == _sha256(generator_path)
        assert source["input_images_used"] is False

    parameters = manifest["procedural_parameters"]
    assert parameters["seed"] == 18427
    assert parameters["output_size_px"] == 2048
    assert (parameters["atlas_columns"], parameters["atlas_rows"]) == (4, 4)
    assert parameters["supersample"] == 2
    assert parameters["generated_pixels_are_botanical_measurements"] is False

    mip_padding = manifest["derivation"]["spray_rgb_mip_padding"]
    assert mip_padding["padding_pixels"] == 24
    assert mip_padding["alpha_threshold_255"] == 2
    assert (mip_padding["atlas_columns"], mip_padding["atlas_rows"]) == (4, 4)
    assert mip_padding["tile_boundary_crossing_allowed"] is False
    assert mip_padding["alpha_preserved_byte_for_byte"] is True
    assert mip_padding["nontransparent_rgb_preserved_byte_for_byte"] is True
    assert len(mip_padding["alpha_sha256"]) == 64
    assert len(mip_padding["nontransparent_rgb_sha256"]) == 64
    assert mip_padding["padded_transparent_pixel_count"] > 700_000
    assert (
        0
        < mip_padding["transparent_nonzero_rgb_pixel_count"]
        <= (mip_padding["padded_transparent_pixel_count"])
    )

    assert set(manifest["maps"]) == {
        "bark_albedo",
        "bark_normal",
        "bark_ao_roughness_height",
        "spray_albedo_opacity",
        "spray_normal",
        "spray_ao_roughness_subsurface",
    }
    for map_data in manifest["maps"].values():
        path = REPO_ROOT / map_data["path"]
        assert path.is_file()
        assert _sha256(path) == map_data["sha256"]
        assert (map_data["width"], map_data["height"]) == (2048, 2048)
        assert map_data["status"].endswith("not_production_promoted")

    bark = Image.open(REPO_ROOT / manifest["maps"]["bark_albedo"]["path"]).convert(
        "RGB"
    )
    assert (
        bark.crop((0, 0, 1, bark.height)).tobytes()
        == bark.crop((bark.width - 1, 0, bark.width, bark.height)).tobytes()
    )
    assert (
        bark.crop((0, 0, bark.width, 1)).tobytes()
        == bark.crop((0, bark.height - 1, bark.width, bark.height)).tobytes()
    )

    sprays = Image.open(REPO_ROOT / manifest["maps"]["spray_albedo_opacity"]["path"])
    assert sprays.mode == "RGBA"
    alpha = sprays.getchannel("A")
    assert alpha.getextrema() == (0, 255)
    assert 0.07 < ImageStat.Stat(alpha).mean[0] / 255.0 < 0.14
    assert manifest["maps"]["spray_albedo_opacity"]["unreal_address_mode"] == "clamp"
    atlas = manifest["unreal_contract"]["atlas_layout"]
    assert (atlas["columns"], atlas["rows"]) == (4, 4)
    assert atlas["branch_spray_tiles"] == list(range(16))
    assert manifest["unreal_contract"]["shadow_policy"].startswith(
        "off for initial isolated"
    )

    boundary = manifest["provenance_and_fidelity_boundary"]
    assert boundary["project_owned_generated_sources"] is True
    assert boundary["external_images_or_data_vendored"] is False
    assert boundary["generated_pixels_are_not_botanical_measurements"] is True
    assert boundary["isolated_visual_review_required"] is True
    assert boundary["corridor_use_before_visual_acceptance_forbidden"] is True


def test_futaleufu_cordillera_cypress_v43_isolates_component_shadow_parity():
    editor_source = EDITOR_MODULE_PATH.read_text(encoding="utf-8")
    structural_report = json.loads(
        FUTALEUFU_CORDILLERA_CYPRESS_V32_REPORT_PATH.read_text(encoding="utf-8")
    )
    review = json.loads(
        FUTALEUFU_CORDILLERA_CYPRESS_V43_REVIEW_PATH.read_text(encoding="utf-8")
    )
    for token in (
        "SetFutaleufuMergedGeometryComponentParityMode",
        "bHlodMergedComponentParityReview",
        'TEXT("RaftSim_PveCypressMergedGeometrySplitHlod")',
        'TEXT("RaftSimMergedGeometrySplitBark")',
        'TEXT("RaftSimMergedGeometrySplitFoliage")',
        "UDynamicMeshComponent",
        "DeleteTrianglesByMaterialID",
        "hlod_merged_component_parity_contract",
        "bark_casts_static_and_dynamic_shadow_foliage_casts_none",
    ):
        assert token in editor_source

    hlod = structural_report["local_multi_view_atlas_hlod"]
    contract = hlod["hlod_merged_component_parity_contract"]
    assert contract["enabled"] is True
    assert contract["source_map"].endswith(
        "L_FutaleufuTerminator_PhysicalCorridorCandidate"
    )
    assert contract["saved_map_modified"] is False
    assert (
        contract["landscape_water_collision_solver_or_gameplay_authority_modified"]
        is False
    )
    assert contract["camera_radius_cm"] == 2450.0
    assert contract["warmup_frames_per_representation"] == 8
    assert contract["sun_actor_label"] == "RaftSim_Sun_LumenPreview"
    assert contract["sun_original_transform_restored"] is True
    assert contract["light_modes"] == ["frontlit", "backlit"]
    assert contract["representations_per_light"] == [
        "source_reference",
        "merged_single_no_shadow",
        "merged_split_no_shadow",
        "merged_split_source_shadow",
    ]
    assert contract["merged_geometry_vertex_count"] == 1_354_592
    assert contract["merged_geometry_triangle_count"] == 1_213_857
    assert contract["merged_geometry_material_slot_count"] == 2
    assert contract["merged_geometry_section_count"] == 2
    assert contract["bark_material_slot_count"] == 1
    assert contract["foliage_material_slot_count"] == 1
    assert contract["component_partition"] == (
        "exact static mesh copied twice and non-owner triangles deleted by source "
        "material ID"
    )
    assert contract["material_identity"] == "source parent materials preserved"
    assert contract["material_state"] == (
        "identical source-coverage temporal parameters on single and split controls"
    )
    assert contract["shadow_partition_basis"] == "material ID"
    assert contract["source_component_shadow_provenance_preserved"] is False
    assert contract["single_component_shadow_policy"] == (
        "bark_and_foliage_no_cast_shadow"
    )
    assert contract["split_no_shadow_policy"] == "bark_and_foliage_no_cast_shadow"
    assert contract["split_source_shadow_policy"] == (
        "bark_casts_static_and_dynamic_shadow_foliage_casts_none"
    )
    assert contract["collision_and_overlap"] is False
    assert contract["temporal_handoff_evaluated"] is False
    assert contract["wall_clock_performance_evaluated"] is False
    assert contract["capture_count"] == 8
    assert len(contract["captures"]) == 8
    assert (
        structural_report["local_visual_review"][
            "hlod_merged_component_parity_capture_count"
        ]
        == 8
    )

    assert review["schema"] == (
        "raftsim.unreal.futaleufu_cypress_merged_component_parity_review.v43"
    )
    assert review["status"] == (
        "material_id_component_partition_validated_shadow_ownership_rejected"
    )
    assert review["merged_component_parity_contract_passed"] is True
    assert review["light_direction_response_gate_passed"] is True
    measurements = review["measurements"]
    assert measurements["component_partition_tolerance"] == {
        "minimum_silhouette_iou": 0.985,
        "acceptable_area_ratio": [0.99, 1.01],
        "acceptable_luminance_ratio": [0.98, 1.02],
        "maximum_mean_channel_delta": 2.0,
        "rationale": (
            "independent scene-capture TAA histories may move threshold-edge pixels "
            "while area, overlap luminance, and channel delta remain near identical"
        ),
    }
    assert set(measurements["per_light"]) == {"frontlit", "backlit"}
    assert set(measurements["frontlit_to_backlit_directional_response"]) == set(
        contract["representations_per_light"]
    )
    for light_mode in ("frontlit", "backlit"):
        per_light = measurements["per_light"][light_mode]
        assert set(per_light["source_comparisons"]) == {
            "merged_single_no_shadow",
            "merged_split_no_shadow",
            "merged_split_source_shadow",
        }
        partition_geometry = per_light["single_to_split_no_shadow_partition"][
            "broad_roi_silhouette_and_photometry"
        ]
        partition_photometry = per_light["single_to_split_no_shadow_partition"][
            "fixed_overlap_photometry"
        ]
        assert (
            partition_geometry["source_hlod_silhouette_intersection_over_union"]
            >= 0.985
        )
        assert (
            0.99 <= partition_geometry["hlod_to_source_silhouette_area_ratio"] <= 1.01
        )
        assert (
            0.98 <= partition_photometry["candidate_to_source_luminance_ratio"] <= 1.02
        )
        assert partition_photometry["mean_absolute_channel_delta"] <= 2.0
        assert all(
            reduction < 0.0 for reduction in per_light["source_shadow_effect"].values()
        )

    assert review["component_partition_gate_passed"] is True
    assert review["source_shadow_policy_parity_gate_passed"] is False
    assert review["backlit_source_shadow_improvement_gate_passed"] is False
    assert review["material_id_shadow_ownership_rejected_gate_passed"] is True
    assert review["component_material_shadow_parity_gate_passed"] is False
    assert "source-provenance split" in review["decision"]["next_step"]
    assert review["reduced_geometry_gate_passed"] is False
    assert review["temporal_handoff_gate_passed"] is False
    assert review["source_art_cleanup_gate_passed"] is False
    assert review["lit_art_review_passed"] is False
    assert review["hazard_readability_gate_passed"] is False
    assert review["wall_clock_performance_gate_passed"] is False
    assert review["production_promoted"] is False
    assert review["corridor_substitution_allowed"] is False
    assert review["regenerate_other_forms_allowed"] is False

    assert FUTALEUFU_CORDILLERA_CYPRESS_V43_CONTACT_SHEET_PATH.is_file()
    with Image.open(FUTALEUFU_CORDILLERA_CYPRESS_V43_CONTACT_SHEET_PATH) as contact:
        assert contact.size == (1270, 496)
        assert contact.mode == "RGB"


def test_futaleufu_native_canopy_textures_are_reproducible_review_candidates():
    manifest = json.loads(
        FUTALEUFU_NATIVE_CANOPY_TEXTURE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    assert manifest["schema"] == "raftsim.unreal.futaleufu_native_canopy_textures.v3"
    assert (
        manifest["status"]
        == "first_party_coigue_texture_candidates_ready_for_isolated_unreal_review"
    )
    assert manifest["production_promoted"] is False
    mip_padding = manifest["derivation"]["leaf_rgb_mip_padding"]
    assert mip_padding["padding_pixels"] == 24
    assert mip_padding["alpha_threshold_255"] == 2
    assert mip_padding["atlas_columns"] == 4
    assert mip_padding["atlas_rows"] == 4
    assert mip_padding["tile_boundary_crossing_allowed"] is False
    assert mip_padding["alpha_preserved_byte_for_byte"] is True
    assert mip_padding["nontransparent_rgb_preserved_byte_for_byte"] is True
    assert len(mip_padding["alpha_sha256"]) == 64
    assert len(mip_padding["nontransparent_rgb_sha256"]) == 64
    assert mip_padding["padded_transparent_pixel_count"] > 100_000
    assert mip_padding["transparent_nonzero_rgb_pixel_count"] == (
        mip_padding["padded_transparent_pixel_count"]
    )
    assert manifest["species"]["scientific_name"] == "Nothofagus dombeyi"
    assert set(manifest["maps"]) == {
        "bark_albedo",
        "bark_normal",
        "bark_ao_roughness_height",
        "leaf_albedo_opacity",
        "leaf_normal",
        "leaf_ao_roughness_subsurface",
    }
    for map_data in manifest["maps"].values():
        path = REPO_ROOT / map_data["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == map_data["sha256"]
        assert (map_data["width"], map_data["height"]) == (2048, 2048)
        assert map_data["status"].endswith("not_production_promoted")

    bark = Image.open(REPO_ROOT / manifest["maps"]["bark_albedo"]["path"]).convert(
        "RGB"
    )
    assert (
        bark.crop((0, 0, 1, bark.height)).tobytes()
        == bark.crop((bark.width - 1, 0, bark.width, bark.height)).tobytes()
    )
    assert (
        bark.crop((0, 0, bark.width, 1)).tobytes()
        == bark.crop((0, bark.height - 1, bark.width, bark.height)).tobytes()
    )

    leaves = Image.open(REPO_ROOT / manifest["maps"]["leaf_albedo_opacity"]["path"])
    assert leaves.mode == "RGBA"
    alpha = leaves.getchannel("A")
    alpha_extrema = alpha.getextrema()
    assert alpha_extrema == (0, 255)
    assert 0.08 < ImageStat.Stat(alpha).mean[0] / 255.0 < 0.35
    assert manifest["maps"]["leaf_albedo_opacity"]["unreal_address_mode"] == "clamp"
    leaf_source = manifest["sources"]["leaf_atlas_chroma"]
    assert leaf_source["input_images_used"] is True
    assert leaf_source["reference_image"].endswith(
        "coigue_leaf_atlas_chroma_source_v1.png"
    )
    atlas = manifest["unreal_contract"]["leaf_atlas_layout"]
    assert (atlas["columns"], atlas["rows"]) == (4, 4)
    assert atlas["single_leaf_tiles"] == list(range(12))
    assert atlas["tiny_twig_tiles"] == list(range(12, 16))
    assert "masked leaf microcards" in manifest["unreal_contract"]["nanite"]
    boundary = manifest["provenance_and_fidelity_boundary"]
    assert boundary["project_owned_generated_sources"] is True
    assert boundary["external_images_or_data_vendored"] is False
    assert boundary["corridor_use_before_visual_acceptance_forbidden"] is True


def test_futaleufu_native_canopy_reviews_reject_v1_through_v22_without_corridor_promotion():
    report = json.loads(
        FUTALEUFU_NATIVE_CANOPY_PROTOTYPE_REPORT_PATH.read_text(encoding="utf-8")
    )
    texture_manifest = json.loads(
        FUTALEUFU_NATIVE_CANOPY_TEXTURE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    v1_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_VISUAL_REVIEW_PATH.read_text(encoding="utf-8")
    )
    v2_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V2_VISUAL_REVIEW_PATH.read_text(encoding="utf-8")
    )
    v3_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V3_VISUAL_REVIEW_PATH.read_text(encoding="utf-8")
    )
    v4_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V4_VISUAL_REVIEW_PATH.read_text(encoding="utf-8")
    )
    v5_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V5_VISUAL_REVIEW_PATH.read_text(encoding="utf-8")
    )
    v6_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V6_VISUAL_REVIEW_PATH.read_text(encoding="utf-8")
    )
    v7_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V7_VISUAL_REVIEW_PATH.read_text(encoding="utf-8")
    )
    v8_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V8_VISUAL_REVIEW_PATH.read_text(encoding="utf-8")
    )
    v9_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V9_VISUAL_REVIEW_PATH.read_text(encoding="utf-8")
    )
    v10_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V10_VISUAL_REVIEW_PATH.read_text(encoding="utf-8")
    )
    v11_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V11_PERFORMANCE_REVIEW_PATH.read_text(encoding="utf-8")
    )
    v12_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V12_RUNTIME_LOD_REVIEW_PATH.read_text(encoding="utf-8")
    )
    v13_report = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V13_CORRIDOR_COMPARISON_REPORT_PATH.read_text(
            encoding="utf-8"
        )
    )
    v13_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V13_CORRIDOR_VISUAL_REVIEW_PATH.read_text(
            encoding="utf-8"
        )
    )
    v14_report = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V14_INSTANCED_MATERIAL_COMPARISON_REPORT_PATH.read_text(
            encoding="utf-8"
        )
    )
    v14_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V14_INSTANCED_MATERIAL_VISUAL_REVIEW_PATH.read_text(
            encoding="utf-8"
        )
    )
    v15_report = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V15_RENDER_DIAGNOSTIC_REPORT_PATH.read_text(
            encoding="utf-8"
        )
    )
    v15_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V15_RENDER_DIAGNOSTIC_VISUAL_REVIEW_PATH.read_text(
            encoding="utf-8"
        )
    )
    v16_report = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V16_OPACITY_DIAGNOSTIC_REPORT_PATH.read_text(
            encoding="utf-8"
        )
    )
    v16_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V16_OPACITY_DIAGNOSTIC_VISUAL_REVIEW_PATH.read_text(
            encoding="utf-8"
        )
    )
    v17_report = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V17_LIGHTING_DIAGNOSTIC_REPORT_PATH.read_text(
            encoding="utf-8"
        )
    )
    v17_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V17_LIGHTING_DIAGNOSTIC_VISUAL_REVIEW_PATH.read_text(
            encoding="utf-8"
        )
    )
    v18_report = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V18_LIGHT_RIG_DIAGNOSTIC_REPORT_PATH.read_text(
            encoding="utf-8"
        )
    )
    v18_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V18_LIGHT_RIG_DIAGNOSTIC_VISUAL_REVIEW_PATH.read_text(
            encoding="utf-8"
        )
    )
    v19_report = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V19_REFLECTANCE_DIAGNOSTIC_REPORT_PATH.read_text(
            encoding="utf-8"
        )
    )
    v19_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V19_REFLECTANCE_DIAGNOSTIC_VISUAL_REVIEW_PATH.read_text(
            encoding="utf-8"
        )
    )
    v20_report = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V20_SHADING_MODEL_DIAGNOSTIC_REPORT_PATH.read_text(
            encoding="utf-8"
        )
    )
    v20_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V20_SHADING_MODEL_DIAGNOSTIC_VISUAL_REVIEW_PATH.read_text(
            encoding="utf-8"
        )
    )
    v21_report = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V21_MIP_PADDING_DIAGNOSTIC_REPORT_PATH.read_text(
            encoding="utf-8"
        )
    )
    v21_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V21_MIP_PADDING_DIAGNOSTIC_VISUAL_REVIEW_PATH.read_text(
            encoding="utf-8"
        )
    )
    v22_report = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V22_OPACITY_SELECTION_DIAGNOSTIC_REPORT_PATH.read_text(
            encoding="utf-8"
        )
    )
    v22_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V22_OPACITY_SELECTION_DIAGNOSTIC_VISUAL_REVIEW_PATH.read_text(
            encoding="utf-8"
        )
    )
    v23_report = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V23_BOUNDED_SHADOW_DIAGNOSTIC_REPORT_PATH.read_text(
            encoding="utf-8"
        )
    )
    v23_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V23_BOUNDED_SHADOW_DIAGNOSTIC_VISUAL_REVIEW_PATH.read_text(
            encoding="utf-8"
        )
    )
    v24_report = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V24_DENSE_COMPARISON_REPORT_PATH.read_text(
            encoding="utf-8"
        )
    )
    v24_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V24_DENSE_VISUAL_REVIEW_PATH.read_text(encoding="utf-8")
    )
    v25_report = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V25_AREA_SAMPLED_COMPARISON_REPORT_PATH.read_text(
            encoding="utf-8"
        )
    )
    v25_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V25_AREA_SAMPLED_VISUAL_REVIEW_PATH.read_text(
            encoding="utf-8"
        )
    )
    v26_report = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V26_WORLD_STABLE_COMPARISON_REPORT_PATH.read_text(
            encoding="utf-8"
        )
    )
    v26_review = json.loads(
        FUTALEUFU_NATIVE_CANOPY_V26_WORLD_STABLE_VISUAL_REVIEW_PATH.read_text(
            encoding="utf-8"
        )
    )

    assert (
        report["schema"] == "raftsim.unreal.futaleufu_native_canopy_prototype_review.v7"
    )
    assert report["production_promoted"] is False
    assert (
        report["prototype_revision"]
        == "v12_far_corridor_lod_and_hism_density_benchmark"
    )
    assert report["capture_gate"]["status"] == (
        "forty_isolated_views_and_512_tree_runtime_benchmark_captured"
    )
    assert report["capture_gate"]["form_count"] == 8
    assert report["capture_gate"]["views_per_form"] == 5
    assert len(report["capture_gate"]["captures"]) == 40
    forms = report["crown_forms"]
    assert [form["id"] for form in forms] == [
        "open_grown_adult",
        "forest_grown_adult",
        "storm_damaged_adult",
        "competition_lean_adult",
        "crown_gap_adult",
        "intermediate",
        "intermediate_suppressed",
        "intermediate_released",
    ]
    assert [form["life_stage"] for form in forms].count("adult") == 5
    assert [form["life_stage"] for form in forms].count("intermediate") == 3
    assert [form["seed_offset"] for form in forms] == [
        0,
        3907,
        5903,
        7901,
        9901,
        1907,
        11903,
        13901,
    ]
    assert len({form["trunk"]["asset"] for form in forms}) == 8
    assert len({form["foliage"]["asset"] for form in forms}) == 8
    assert all(
        not form[role]["nanite_enabled"]
        for form in forms
        for role in (
            "trunk",
            "branchlets",
            "foliage",
            "far_foliage",
            "runtime_far_foliage",
        )
    )
    forms_by_id = {form["id"]: form for form in forms}
    open_form = forms_by_id["open_grown_adult"]
    forest_form = forms_by_id["forest_grown_adult"]
    storm_form = forms_by_id["storm_damaged_adult"]
    competition_form = forms_by_id["competition_lean_adult"]
    crown_gap_form = forms_by_id["crown_gap_adult"]
    intermediate_form = forms_by_id["intermediate"]
    suppressed_form = forms_by_id["intermediate_suppressed"]
    released_form = forms_by_id["intermediate_released"]
    assert open_form["trunk"]["render_vertices"] == 2560
    assert open_form["branchlets"]["source_vertices"] == 287376
    assert open_form["branchlets"]["render_vertices"] == 468872
    assert (
        open_form["branchlets"]["render_triangles"]
        == open_form["branchlets"]["source_triangles"]
    )
    assert open_form["foliage"]["source_card_count"] == 41184
    assert open_form["far_foliage"]["source_card_count"] == 90432
    assert open_form["runtime_far_foliage"]["source_card_count"] == 15072
    assert open_form["runtime_far_foliage"]["render_triangles"] == 30144
    assert intermediate_form["foliage"]["source_card_count"] == 38016
    assert intermediate_form["far_foliage"]["source_card_count"] == 80640
    assert forest_form["foliage"]["source_card_count"] == 34848
    assert forest_form["far_foliage"]["source_card_count"] == 72288
    assert storm_form["topology"]["deterministically_damaged_branches"] == 6
    assert storm_form["topology"]["near_foliage_anchors"] == 177
    assert storm_form["foliage"]["source_card_count"] == 31152
    assert storm_form["damage_modulo"] == 4
    assert storm_form["damaged_branch_length_scale"] == pytest.approx(0.38)
    assert competition_form["trunk_lean_top_cm"] == [260, -150]
    assert competition_form["suppressed_sector_half_width_degrees"] == 70
    assert competition_form["suppressed_sector_length_scale"] == pytest.approx(0.28)
    assert crown_gap_form["crown_gap_center_t"] == pytest.approx(0.45)
    assert crown_gap_form["crown_gap_length_scale"] == pytest.approx(0.32)
    assert suppressed_form["crown_width_scale"] == pytest.approx(0.48)
    assert suppressed_form["topology"]["near_foliage_anchors"] == 180
    assert released_form["asymmetry_scale"] == pytest.approx(1.70)
    assert released_form["trunk_lean_top_cm"] == [-120, 100]
    assert all(
        form["foliage"]["render_vertices"] == form["foliage"]["source_vertices"]
        for form in forms
    )
    assert report["lod_handoff"]["overlap_cm"] == 800.0
    assert report["lod_handoff"]["runtime_far_card_stride"] == 6
    assert report["lod_handoff"]["runtime_far_card_scale"] == pytest.approx(1.28)
    assert report["leaf_contract"]["wind_parameters"] == [
        "WindIntensity",
        "WindWeight",
        "WindSpeed",
    ]
    assert all(form["topology"]["floating_near_card_count"] == 0 for form in forms)
    assert all(form["topology"]["branchlets_per_parent_shoot"] == 8 for form in forms)
    assert all(
        form["topology"]["tertiary_branches_per_branchlet"] == 3 for form in forms
    )
    assert all(
        form["topology"]["attached_leaf_cards_per_branchlet"] == 22 for form in forms
    )
    assert [form["topology"]["near_foliage_anchors"] for form in forms] == [
        234,
        198,
        177,
        216,
        216,
        216,
        180,
        207,
    ]
    assert report["leaf_contract"]["visible_leaf_length_cm"] == [2.0, 3.5]
    assert report["leaf_contract"]["primary_tip_radius_cm"] == [7.0, 3.2, 0.8]
    assert report["leaf_contract"]["terminal_twig_collar_radius_cm"] == [3.2, 1.4, 0.72]
    assert report["leaf_contract"]["branchlet_length_cm"] == [24, 40]
    assert report["photometry"]["method"].endswith("no emissive fill")
    assert report["photometry"]["front_fill_intensity"] == 0.75
    assert report["photometry"]["back_fill_intensity"] == 0.38
    assert report["photometry"]["emissive_fill"] is False
    assert report["photometry"]["bark_ao_influence"] == 0.28
    assert report["photometry"]["leaf_ao_influence"] == 0.55
    assert all(form["routing"]["near_clearance_contract_passed"] for form in forms)
    assert all(
        form["routing"]["unresolved_branchlet_clearance_count"] == 0 for form in forms
    )
    assert all(
        form["routing"]["unresolved_tertiary_clearance_count"] == 0 for form in forms
    )
    assert sum(form["routing"]["rerouted_branchlet_count"] for form in forms) == 16
    assert sum(form["routing"]["rerouted_tertiary_count"] for form in forms) == 902
    assert (
        min(form["routing"]["minimum_near_branchlet_clearance_cm"] for form in forms)
        >= 1.2
    )
    assert (
        min(form["routing"]["minimum_near_tertiary_clearance_cm"] for form in forms)
        >= 0.6
    )

    assert (
        v1_review["schema"] == "raftsim.unreal.futaleufu_native_canopy_visual_review.v1"
    )
    assert (
        v1_review["status"]
        == "rejected_at_closeup_material_gate_no_corridor_substitution"
    )
    assert v1_review["production_promoted"] is False
    assert v1_review["corridor_substitution_performed"] is False
    v1_rejection_text = " ".join(v1_review["rejection_reasons"])
    assert "visibly flat and intersecting" in v1_rejection_text
    assert "bark material renders too dark" in v1_rejection_text

    assert (
        v2_review["schema"] == "raftsim.unreal.futaleufu_native_canopy_visual_review.v2"
    )
    assert (
        v2_review["status"]
        == "rejected_at_morphology_and_closeup_gate_no_corridor_substitution"
    )
    assert v2_review["production_promoted"] is False
    assert v2_review["corridor_substitution_performed"] is False
    assert len(v2_review["captures"]) == 5

    assert (
        v3_review["schema"] == "raftsim.unreal.futaleufu_native_canopy_visual_review.v3"
    )
    assert (
        v3_review["status"]
        == "rejected_at_shoot_density_and_crown_mass_gate_no_corridor_substitution"
    )
    assert v3_review["production_promoted"] is False
    assert v3_review["corridor_substitution_performed"] is False
    assert len(v3_review["captures"]) == 5
    v3_rejection_text = " ".join(v3_review["rejection_reasons"])
    assert "branchlets are overlong" in v3_rejection_text
    assert "tiered and sparse" in v3_rejection_text
    assert (
        v4_review["schema"] == "raftsim.unreal.futaleufu_native_canopy_visual_review.v4"
    )
    assert (
        v4_review["status"]
        == "rejected_at_closeup_ramification_and_variant_gate_no_corridor_substitution"
    )
    assert v4_review["production_promoted"] is False
    assert v4_review["corridor_substitution_performed"] is False
    assert v4_review["review_contract"]["material_compile_errors"] == 0
    assert len(v4_review["captures"]) == 5
    assert all(len(capture["sha256"]) == 64 for capture in v4_review["captures"])
    v4_rejection_text = " ".join(v4_review["rejection_reasons"])
    assert "crowded branch origins" in v4_rejection_text
    assert "repeated horizontal shelves" in v4_rejection_text
    assert (
        v5_review["schema"] == "raftsim.unreal.futaleufu_native_canopy_visual_review.v5"
    )
    assert (
        v5_review["status"]
        == "rejected_at_junction_photometry_and_variant_gate_no_corridor_substitution"
    )
    assert v5_review["production_promoted"] is False
    assert v5_review["corridor_substitution_performed"] is False
    assert v5_review["review_contract"]["material_compile_errors"] == 0
    assert len(v5_review["captures"]) == 5
    assert all(len(capture["sha256"]) == 64 for capture in v5_review["captures"])
    v5_rejection_text = " ".join(v5_review["rejection_reasons"])
    assert "abrupt cylindrical main-limb cutoff" in v5_rejection_text
    assert "forest-grown adult" in v5_rejection_text
    assert (
        v6_review["schema"] == "raftsim.unreal.futaleufu_native_canopy_visual_review.v6"
    )
    assert (
        v6_review["status"]
        == "rejected_at_photometry_and_variant_gate_no_corridor_substitution"
    )
    assert v6_review["production_promoted"] is False
    assert v6_review["corridor_substitution_performed"] is False
    assert v6_review["junction_contract"]["radius_increases_between_generations"] == 0
    assert v6_review["review_contract"]["material_compile_errors"] == 0
    assert len(v6_review["captures"]) == 5
    assert all(len(capture["sha256"]) == 64 for capture in v6_review["captures"])
    v6_rejection_text = " ".join(v6_review["rejection_reasons"])
    assert "forest-grown adult" in v6_rejection_text
    assert "too dark" in v6_rejection_text
    assert (
        v7_review["schema"] == "raftsim.unreal.futaleufu_native_canopy_visual_review.v7"
    )
    assert (
        v7_review["status"]
        == "rejected_at_family_density_and_ecology_gate_no_corridor_substitution"
    )
    assert v7_review["production_promoted"] is False
    assert v7_review["corridor_substitution_performed"] is False
    assert v7_review["crown_form_contract"]["transformed_copy_count"] == 0
    assert (
        v7_review["crown_form_contract"]["full_ecology_variant_contract_satisfied"]
        is False
    )
    assert v7_review["photometry_contract"]["emissive_fill"] is False
    assert v7_review["review_contract"]["material_compile_errors"] == 0
    assert len(v7_review["captures"]) == 15
    assert all(len(capture["sha256"]) == 64 for capture in v7_review["captures"])
    assert {capture["form"] for capture in v7_review["captures"]} == {
        "open_grown_adult",
        "intermediate",
        "forest_grown_adult",
    }
    assert all(
        capture["path"] in report["capture_gate"]["captures"]
        for capture in v7_review["captures"]
    )
    assert (
        v8_review["schema"] == "raftsim.unreal.futaleufu_native_canopy_visual_review.v8"
    )
    assert v8_review["status"] == (
        "rejected_at_closeup_temporal_performance_and_ecology_gate_no_corridor_substitution"
    )
    assert v8_review["production_promoted"] is False
    assert v8_review["corridor_substitution_performed"] is False
    assert v8_review["family_contract"]["adult_captured"] == 5
    assert v8_review["family_contract"]["intermediate_captured"] == 3
    assert v8_review["family_contract"]["transformed_copy_count"] == 0
    assert v8_review["family_contract"]["species_count_authoring_threshold_met"] is True
    assert v8_review["family_contract"]["full_mixed_ecology_contract_met"] is False
    assert (
        v8_review["texture_residency_contract"][
            "white_fallback_quad_regression_present"
        ]
        is False
    )
    assert v8_review["texture_residency_contract"]["texture_no_miplevel_warnings"] == 0
    assert v8_review["review_contract"]["material_compile_errors"] == 0
    assert v8_review["review_contract"]["capture_count"] == 40
    assert v8_review["review_contract"]["review_spacing_cm"] == 500000
    assert len(v8_review["capture_hashes"]) == 40
    assert all(len(digest) == 64 for digest in v8_review["capture_hashes"].values())
    assert set(v8_review["capture_hashes"]) == set(report["capture_gate"]["captures"])
    assert (
        v9_review["schema"] == "raftsim.unreal.futaleufu_native_canopy_visual_review.v9"
    )
    assert v9_review["status"] == (
        "rejected_at_branch_intersection_temporal_performance_and_ecology_gate_no_corridor_substitution"
    )
    assert v9_review["production_promoted"] is False
    assert v9_review["corridor_substitution_performed"] is False
    assert (
        v9_review["foreground_topology_contract"]["branchlets_per_parent_shoot_v9"] == 8
    )
    assert (
        v9_review["foreground_topology_contract"]["tertiary_branches_per_branchlet_v9"]
        == 3
    )
    assert (
        v9_review["foreground_topology_contract"][
            "attached_leaf_cards_per_branchlet_v9"
        ]
        == 22
    )
    assert (
        v9_review["foreground_topology_contract"]["open_grown_leaf_cards_v9"] == 41184
    )
    assert (
        v9_review["foreground_topology_contract"]["foreground_density_gate_improved"]
        is True
    )
    assert (
        v9_review["foreground_topology_contract"]["branch_intersection_gate_passed"]
        is False
    )
    assert v9_review["photometry_contract"]["emissive_fill"] is False
    assert (
        v9_review["photometry_contract"]["bark_readable_in_both_turntable_azimuths"]
        is True
    )
    assert v9_review["review_contract"]["capture_count"] == 40
    assert v9_review["review_contract"]["texture_no_miplevel_warnings"] == 0
    assert len(v9_review["capture_hashes"]) == 40
    assert all(len(digest) == 64 for digest in v9_review["capture_hashes"].values())
    assert set(v9_review["capture_hashes"]) == set(report["capture_gate"]["captures"])
    assert (
        v10_review["schema"]
        == "raftsim.unreal.futaleufu_native_canopy_visual_review.v10"
    )
    assert v10_review["status"] == (
        "rejected_at_projected_topology_temporal_performance_and_ecology_gate_no_corridor_substitution"
    )
    assert v10_review["production_promoted"] is False
    assert v10_review["corridor_substitution_performed"] is False
    routing_contract = v10_review["routing_contract"]
    assert routing_contract["near_branchlet_required_clearance_cm"] == 1.2
    assert routing_contract["near_tertiary_required_clearance_cm"] == 0.6
    assert routing_contract["rerouted_branchlet_count"] == 16
    assert routing_contract["rerouted_tertiary_count"] == 902
    assert routing_contract["unresolved_branchlet_clearance_count"] == 0
    assert routing_contract["unresolved_tertiary_clearance_count"] == 0
    assert routing_contract["forms_passing_contract"] == 8
    assert routing_contract["physical_near_centerline_clearance_gate_passed"] is True
    assert routing_contract["photoreal_closeup_topology_gate_passed"] is False
    assert v10_review["review_contract"]["validated_generated_assets"] == 41
    assert v10_review["review_contract"]["capture_count"] == 40
    assert len(v10_review["capture_hashes"]) == 40
    assert all(len(digest) == 64 for digest in v10_review["capture_hashes"].values())
    assert set(v10_review["capture_hashes"]) == set(report["capture_gate"]["captures"])
    performance = report["performance_instrumentation"]
    assert performance["family_exclusive_resource_bytes"] == 367918128
    assert performance["family_render_vertices_lod0"] == 6961948
    assert performance["family_render_triangles_lod0"] == 3859140
    assert (
        19_000_000
        <= performance["runtime_far_family_exclusive_resource_bytes"]
        <= 21_000_000
    )
    assert performance["runtime_far_family_render_vertices_lod0"] == 435064
    assert performance["runtime_far_family_render_triangles_lod0"] == 223592
    assert performance["runtime_far_family_resource_reduction_fraction"] > 0.94
    assert performance["static_mesh_assets"] == 40
    assert performance["capture_wall_time_valid"] is True
    assert performance["capture_wall_time"]["sample_count"] == 40
    assert performance["capture_wall_time"]["minimum_ms"] > 0
    assert performance["frame_cycle_counters_valid"] is False
    assert performance["game_thread_frame_time"]["maximum_ms"] == 0
    assert len(performance["capture_samples"]) == 40
    assert (
        v11_review["schema"]
        == "raftsim.unreal.futaleufu_native_canopy_performance_review.v11"
    )
    assert v11_review["production_promoted"] is False
    assert v11_review["corridor_substitution_performed"] is False
    assert (
        v11_review["performance_contract"]["family_exclusive_resource_bytes"]
        == 367918128
    )
    assert v11_review["performance_contract"]["capture_sample_count"] == 40
    assert v11_review["performance_contract"]["frame_cycle_counters_valid"] is False
    assert (
        v11_review["performance_contract"]["packaged_desktop_benchmark_passed"] is False
    )
    assert v11_review["performance_contract"]["packaged_vr_benchmark_passed"] is False
    assert v11_review["evidence_integrity"]["capture_hashes_match_v10"] is True
    assert v11_review["evidence_integrity"]["routing_unresolved_conflicts"] == 0
    assert v12_review["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_runtime_lod_review.v12"
    )
    assert v12_review["status"] == (
        "runtime_far_lod_technical_candidate_accepted_corridor_and_production_promotion_rejected"
    )
    assert v12_review["production_promoted"] is False
    assert v12_review["corridor_substitution_performed"] is False
    assert v12_review["runtime_far_lod_retained"] is True
    assert (
        v12_review["performance_contract"][
            "runtime_far_family_exclusive_resource_bytes"
        ]
        == 20264400
    )
    assert v12_review["performance_contract"][
        "runtime_far_family_resource_reduction_fraction"
    ] == pytest.approx(0.94492144187035)
    assert (
        v12_review["performance_contract"]["corridor_density_visual_capture_passed"]
        is True
    )
    assert (
        v12_review["performance_contract"]["corridor_density_performance_budget_passed"]
        is False
    )
    runtime_capture = REPO_ROOT / v12_review["capture_evidence"]["capture"]
    assert runtime_capture.is_file()
    assert _sha256(runtime_capture) == v12_review["capture_evidence"]["sha256"]
    assert v12_review["capture_evidence"]["tree_instance_count"] == 512
    assert v12_review["capture_evidence"]["hism_component_count"] == 16
    assert len(v12_review["accepted_findings"]) == 5
    assert len(v12_review["rejection_reasons"]) == 6
    assert len(v12_review["next_iteration_requirements"]) == 5
    assert v13_report["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_corridor_comparison.v1"
    )
    assert v13_report["status"] == (
        "paired_source_masked_transient_corridor_comparison_captured_pending_human_review"
    )
    assert v13_report["production_promoted"] is False
    assert v13_report["source_map_modified"] is False
    assert v13_report["collision_or_gameplay_authority_modified"] is False
    placement = v13_report["placement_contract"]
    assert placement["target_tree_count_per_view"] == 1200
    assert placement["river_setback_m"] == 65
    assert placement["minimum_spacing_m"] == 15
    assert placement["minimum_vegetation_mask"] == pytest.approx(0.34)
    assert placement["maximum_water_mask"] == pytest.approx(0.28)
    assert placement["maximum_slope_degrees"] == 39
    assert placement["near_full_representation_max_distance_m"] == 300
    assert placement["mid_representation_max_distance_m"] == 500
    for stats_key in ("guide_seat_stats", "river_eye_stats"):
        stats = v13_report[stats_key]
        assert stats["accepted_tree_count"] == 1200
        assert stats["near_full_tree_count"] > 0
        assert stats["mid_tree_count"] > 0
        assert stats["runtime_far_tree_count"] > 0
        assert stats["hidden_fallback_pve_actor_count"] == 4
        assert stats["mean_accepted_vegetation_mask"] >= 0.34
        assert stats["mean_accepted_water_mask"] <= 0.28
        assert stats["maximum_accepted_slope_degrees"] <= 39
        assert 100 <= stats["minimum_accepted_elevation_m"]
        assert stats["maximum_accepted_elevation_m"] <= 900
    assert v13_report["guide_seat_stats"]["near_full_tree_count"] == 50
    assert v13_report["guide_seat_stats"]["mid_tree_count"] == 126
    assert v13_report["guide_seat_stats"]["runtime_far_tree_count"] == 1024
    assert v13_report["river_eye_stats"]["near_full_tree_count"] == 40
    assert v13_report["river_eye_stats"]["mid_tree_count"] == 157
    assert v13_report["river_eye_stats"]["runtime_far_tree_count"] == 1003
    assert v13_review["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_corridor_visual_review.v13"
    )
    assert v13_review["status"] == (
        "source_masked_corridor_placement_validated_visual_substitution_rejected_not_lifelike"
    )
    assert v13_review["production_promoted"] is False
    assert v13_review["corridor_substitution_performed"] is False
    assert v13_review["runtime_far_lod_retained"] is True
    assert v13_review["placement_pipeline_retained"] is True
    assert (
        v13_review["placement_contract_result"]["placement_pipeline_gate_passed"]
        is True
    )
    assert (
        v13_review["placement_contract_result"]["corridor_visual_gate_passed"] is False
    )
    assert len(v13_review["accepted_findings"]) == 4
    assert len(v13_review["rejection_reasons"]) == 6
    assert len(v13_review["next_iteration_requirements"]) == 5
    for view in v13_review["capture_evidence"].values():
        for role in ("baseline", "comparison"):
            capture = REPO_ROOT / view[role]
            assert capture.is_file()
            assert _sha256(capture) == view[f"{role}_sha256"]
        assert view["dimensions_px"] == [1280, 720]
        assert view["changed_pixel_fraction"] > 0.04
        assert view["comparison_green_dominant_fraction"] < (
            view["baseline_green_dominant_fraction"] * 0.1
        )
    assert v14_report["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_corridor_comparison.v2"
    )
    assert (
        v14_report["material_contract"]["bark_instanced_static_meshes_usage_persisted"]
        is True
    )
    assert (
        v14_report["material_contract"]["leaf_instanced_static_meshes_usage_persisted"]
        is True
    )
    assert v14_report["guide_seat_stats"] == v13_report["guide_seat_stats"]
    assert v14_report["river_eye_stats"] == v13_report["river_eye_stats"]
    assert v14_review["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_instanced_material_review.v14"
    )
    assert v14_review["status"] == (
        "instanced_material_usage_persisted_visual_result_pixel_identical_corridor_promotion_rejected"
    )
    assert v14_review["production_promoted"] is False
    assert v14_review["corridor_substitution_performed"] is False
    assert v14_review["instanced_material_contract_retained"] is True
    assert v14_review["hypothesis"]["supported"] is False
    for view in v14_review["capture_evidence"].values():
        for revision in ("v13", "v14"):
            capture = REPO_ROOT / view[revision]
            assert capture.is_file()
            assert _sha256(capture) == view[f"{revision}_sha256"]
        assert view["v13_sha256"] == view["v14_sha256"]
        assert view["dimensions_px"] == [1280, 720]
        assert view["changed_pixel_fraction_v13_to_v14"] == 0
        assert view["mean_absolute_rgb_delta_v13_to_v14"] == [0, 0, 0]
    assert v15_report["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_render_diagnostic.v15"
    )
    assert v15_report["status"] == (
        "controlled_leaf_shadow_and_opaque_card_diagnostics_captured_pending_human_review"
    )
    assert v15_report["production_promoted"] is False
    assert v15_report["source_map_modified"] is False
    assert v15_report["collision_or_gameplay_authority_modified"] is False
    assert v15_report["placement_counts_identical_between_render_modes"] is True
    assert v15_report["captures"]["all_captured"] is True
    for stats in v15_report["placement_stats"].values():
        assert stats["accepted_tree_count"] == 1200
        assert stats["hidden_fallback_pve_actor_count"] == 4
    assert v15_review["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_render_diagnostic_review.v15"
    )
    assert v15_review["production_promoted"] is False
    assert v15_review["corridor_substitution_performed"] is False
    conclusions = v15_review["diagnostic_conclusions"]
    assert conclusions["leaf_shadows_cause_elongated_ground_smears"] is True
    assert conclusions["leaf_shadow_disable_restores_crown_visibility"] is False
    assert conclusions["opaque_leaf_override_reveals_retained_crown_geometry"] is True
    assert (
        conclusions["missing_hism_instances_or_distance_geometry_is_primary_cause"]
        is False
    )
    assert (
        conclusions["native_masked_leaf_material_path_is_primary_visibility_failure"]
        is True
    )
    for view in v15_review["capture_evidence"].values():
        for role in (
            "native_reference",
            "native_leaves_no_shadow",
            "opaque_leaves_no_shadow",
        ):
            capture = REPO_ROOT / view[role]
            assert capture.is_file()
            assert _sha256(capture) == view[f"{role}_sha256"]
        assert view["dimensions_px"] == [1280, 720]
        assert view["changed_pixel_fraction_native_to_shadowless"] > 0
        assert view["changed_pixel_fraction_shadowless_to_opaque"] > 0.02
        green = view["green_dominant_fraction"]
        assert green["opaque_leaves_no_shadow"] > green["native_leaves_no_shadow"] * 100
    assert v16_report["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_same_shader_opacity_diagnostic.v16"
    )
    assert v16_report["status"] == (
        "same_shader_alpha_scale_and_constant_opacity_diagnostics_captured_pending_human_review"
    )
    assert v16_report["placement_counts_identical_between_render_modes"] is True
    texture_contract = v16_report["leaf_texture_contract"]
    assert texture_contract["has_alpha_channel"] is True
    assert texture_contract["compression_no_alpha"] is False
    assert texture_contract["scale_mips_for_alpha_coverage"] is True
    assert texture_contract["alpha_coverage_thresholds_rgba"] == [0, 0, 0, 0.5]
    assert texture_contract["sharpen5_mips"] is True
    assert texture_contract["never_stream"] is True
    assert texture_contract["virtual_texture_streaming"] is False
    assert v16_report["leaf_material_contract"]["default_leaf_opacity_scale"] == 1
    assert v16_report["leaf_material_contract"]["default_leaf_opacity_override"] == 0
    assert v16_review["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_same_shader_opacity_review.v16"
    )
    assert v16_review["production_promoted"] is False
    assert v16_review["opacity_parameters_retained_with_neutral_defaults"] is True
    v16_conclusions = v16_review["diagnostic_conclusions"]
    assert v16_conclusions["alpha_scale_4_restores_crown_silhouette"] is True
    assert v16_conclusions["alpha_scale_4_nearly_matches_constant_opacity"] is True
    assert v16_conclusions["alpha_scale_4_is_bounded_visual_candidate"] is False
    assert (
        v16_conclusions["native_two_sided_foliage_response_remains_near_black"] is True
    )
    assert v16_conclusions["source_leaf_rgb_is_intrinsically_black"] is False
    for view in v16_review["capture_evidence"].values():
        for role in (
            "shadowless_native_reference",
            "alpha_scale_4",
            "constant_opacity",
        ):
            capture = REPO_ROOT / view[role]
            assert capture.is_file()
            assert _sha256(capture) == view[f"{role}_sha256"]
        assert view["dimensions_px"] == [1280, 720]
        assert view["changed_pixel_fraction_shadowless_native_to_alpha_scale_4"] > 0.03
        assert view["changed_pixel_fraction_alpha_scale_4_to_constant_opacity"] < 0.001
    assert v17_report["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_lighting_diagnostic.v17"
    )
    assert v17_report["status"] == (
        "controlled_ao_normal_and_diagnostic_emissive_splits_captured_pending_human_review"
    )
    assert v17_report["production_promoted"] is False
    assert v17_report["placement_counts_identical_between_render_modes"] is True
    assert v17_report["captures"]["all_captured"] is True
    defaults = v17_report["retained_neutral_material_defaults"]
    assert defaults["LeafAOInfluence"] == pytest.approx(0.55)
    assert defaults["LeafNormalStrength"] == 1
    assert defaults["LeafDiagnosticEmissive"] == 0
    assert v17_review["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_lighting_diagnostic_review.v17"
    )
    assert v17_review["production_promoted"] is False
    assert v17_review["neutral_material_defaults_retained"] is True
    v17_conclusions = v17_review["diagnostic_conclusions"]
    assert v17_conclusions["ambient_occlusion_is_primary_darkness_cause"] is False
    assert v17_conclusions["sampled_leaf_normals_are_primary_darkness_cause"] is False
    assert (
        v17_conclusions["diagnostic_emissive_proves_source_color_reaches_shader"]
        is True
    )
    assert v17_conclusions["diagnostic_emissive_is_promotion_eligible"] is False
    for view in v17_review["capture_evidence"].values():
        for role in ("alpha4_reference", "ao_off", "flat_normal", "emissive_035"):
            capture = REPO_ROOT / view[role]
            assert capture.is_file()
            assert _sha256(capture) == view[f"{role}_sha256"]
        assert view["dimensions_px"] == [1280, 720]
        assert view["changed_pixel_fraction_vs_alpha4_reference"]["ao_off"] < 0.00001
        assert view["changed_pixel_fraction_vs_alpha4_reference"]["flat_normal"] < 0.001
        assert view["changed_pixel_fraction_vs_alpha4_reference"]["emissive_035"] > 0.01
    assert v18_report["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_corridor_light_rig_diagnostic.v18"
    )
    assert v18_report["status"] == (
        "controlled_baseline_fill_and_skylight_splits_captured_pending_human_review"
    )
    assert v18_report["production_promoted"] is False
    assert v18_report["source_map_modified"] is False
    assert v18_report["placement_counts_identical_between_render_modes"] is True
    assert v18_report["captures"]["all_captured"] is True
    assert v18_review["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_corridor_light_rig_review.v18"
    )
    assert v18_review["production_promoted"] is False
    assert v18_review["saved_corridor_photometry_modified"] is False
    v18_conclusions = v18_review["diagnostic_conclusions"]
    assert v18_conclusions["transient_fill_lights_affect_scene"] is True
    assert (
        v18_conclusions["transient_fill_lights_restore_readable_green_crowns"] is False
    )
    assert v18_conclusions["skylight_310_capture_differs_from_baseline"] is False
    assert (
        v18_conclusions["global_corridor_brightness_is_primary_darkness_cause"] is False
    )
    for view in v18_review["capture_evidence"].values():
        for role in ("baseline", "isolated_fill", "skylight_310"):
            capture = REPO_ROOT / view[role]
            assert capture.is_file()
            assert _sha256(capture) == view[f"{role}_sha256"]
        assert view["dimensions_px"] == [1280, 720]
        assert view["changed_pixel_fraction_vs_baseline"]["isolated_fill"] > 0.25
        assert view["changed_pixel_fraction_vs_baseline"]["skylight_310"] == 0
        assert view["baseline_sha256"] == view["skylight_310_sha256"]
        assert view["restored_crown_metrics"]["isolated_fill_dark_fraction"] > 0.70
    assert v19_report["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_reflectance_diagnostic.v19"
    )
    assert v19_report["status"] == (
        "controlled_basecolor_transmission_and_interaction_splits_captured_pending_human_review"
    )
    assert v19_report["production_promoted"] is False
    assert v19_report["source_map_modified"] is False
    assert v19_report["placement_counts_identical_between_render_modes"] is True
    assert v19_report["captures"]["all_captured"] is True
    assert v19_review["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_reflectance_review.v19"
    )
    assert v19_review["production_promoted"] is False
    assert v19_review["neutral_material_defaults_retained"] is True
    v19_conclusions = v19_review["diagnostic_conclusions"]
    assert v19_conclusions["base_color_reflectance_changes_crown_response"] is True
    assert v19_conclusions["white_transmission_alone_restores_readable_crowns"] is False
    assert v19_conclusions["base_color_and_transmission_interact"] is True
    assert v19_conclusions["combined_override_is_promotion_eligible"] is False
    for view in v19_review["capture_evidence"].values():
        for role in ("reference", "basecolor_236", "white_transmission", "combined"):
            capture = REPO_ROOT / view[role]
            assert capture.is_file()
            assert _sha256(capture) == view[f"{role}_sha256"]
        assert view["dimensions_px"] == [1280, 720]
        crown = view["restored_crown_metrics"]
        assert crown["basecolor_236_green_dominant_fraction"] > (
            crown["reference_green_dominant_fraction"] * 10
        )
        assert crown["combined_green_dominant_fraction"] > (
            crown["basecolor_236_green_dominant_fraction"]
        )
        assert crown["combined_dark_fraction"] > 0.40
    assert v20_report["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_shading_model_diagnostic.v20"
    )
    assert v20_report["status"] == (
        "same_texture_defaultlit_pairs_captured_pending_human_review"
    )
    assert v20_report["production_promoted"] is False
    assert v20_report["source_map_modified"] is False
    assert v20_report["placement_counts_identical_between_render_modes"] is True
    assert v20_report["captures"]["all_captured"] is True
    assert v20_review["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_shading_model_review.v20"
    )
    assert v20_review["native_twosidedfoliage_retained"] is True
    assert v20_review["defaultlit_diagnostic_promoted"] is False
    v20_conclusions = v20_review["diagnostic_conclusions"]
    assert v20_conclusions["defaultlit_restores_readable_green_crowns"] is False
    assert v20_conclusions["twosidedfoliage_is_primary_darkness_cause"] is False
    assert (
        v20_conclusions["transparent_black_rgb_mip_bleed_requires_controlled_fix"]
        is True
    )
    for view in v20_review["capture_evidence"].values():
        for role in (
            "twosided_118",
            "defaultlit_118",
            "twosided_236",
            "defaultlit_236",
        ):
            capture = REPO_ROOT / view[role]
            assert capture.is_file()
            assert _sha256(capture) == view[f"{role}_sha256"]
        assert view["dimensions_px"] == [1280, 720]
        crown = view["restored_crown_metrics"]
        assert crown["defaultlit_118_green_dominant_fraction"] < (
            crown["twosided_118_green_dominant_fraction"]
        )
        assert crown["defaultlit_236_green_dominant_fraction"] < (
            crown["twosided_236_green_dominant_fraction"]
        )
        assert (
            crown["defaultlit_236_dark_fraction"] > crown["twosided_236_dark_fraction"]
        )
    assert v21_report["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_mip_padding_diagnostic.v21"
    )
    assert v21_report["status"] == (
        "alpha_preserved_rgb_padded_native_pair_captured_pending_human_review"
    )
    assert v21_report["production_promoted"] is False
    assert v21_report["source_map_modified"] is False
    assert v21_report["captures"]["all_captured"] is True
    padding = v21_report["padding_contract"]
    manifest_padding = texture_manifest["derivation"]["leaf_rgb_mip_padding"]
    assert padding["alpha_sha256"] == manifest_padding["alpha_sha256"]
    assert (
        padding["nontransparent_rgb_sha256"]
        == manifest_padding["nontransparent_rgb_sha256"]
    )
    assert (
        padding["padded_transparent_pixel_count"]
        == manifest_padding["padded_transparent_pixel_count"]
    )
    assert v21_review["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_mip_padding_review.v21"
    )
    assert v21_review["rgb_mip_padding_source_fix_retained"] is True
    assert v21_review["neutral_twosidedfoliage_defaults_retained"] is True
    v21_conclusions = v21_review["diagnostic_conclusions"]
    assert (
        v21_conclusions["transparent_black_rgb_mip_bleed_was_primary_color_loss_cause"]
        is True
    )
    assert v21_conclusions["rgb_padding_restores_green_crown_response"] is True
    assert v21_conclusions["source_alpha_changed"] is False
    for view in v21_review["capture_evidence"].values():
        for role in ("reference", "rgb_padded"):
            capture = REPO_ROOT / view[role]
            assert capture.is_file()
            assert _sha256(capture) == view[f"{role}_sha256"]
        assert view["dimensions_px"] == [1280, 720]
        crown = view["restored_crown_metrics"]
        assert crown["rgb_padded_green_dominant_fraction"] > 0.65
        assert crown["rgb_padded_green_dominant_fraction"] > (
            crown["reference_green_dominant_fraction"] * 30
        )
        assert crown["rgb_padded_dark_fraction"] < crown["reference_dark_fraction"]
    assert v22_report["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_opacity_selection_diagnostic.v22"
    )
    assert v22_report["status"] == (
        "rgb_padded_alpha2_and_alpha3_pairs_captured_pending_human_review"
    )
    assert v22_report["production_promoted"] is False
    assert v22_report["placement_counts_identical_between_render_modes"] is True
    assert v22_report["captures"]["all_captured"] is True
    assert v22_review["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_opacity_selection_review.v22"
    )
    assert v22_review["selected_corridor_candidate_opacity_scale"] == 2
    assert v22_review["neutral_material_default_retained"] is True
    v22_conclusions = v22_review["diagnostic_conclusions"]
    assert v22_conclusions["alpha2_preserves_registered_crown_continuity"] is True
    assert v22_conclusions["alpha2_and_alpha3_are_pixel_identical"] is True
    assert v22_conclusions["alpha2_is_production_promoted"] is False
    for view in v22_review["capture_evidence"].values():
        for role in ("alpha4_reference", "alpha2", "alpha3"):
            capture = REPO_ROOT / view[role]
            assert capture.is_file()
            assert _sha256(capture) == view[f"{role}_sha256"]
        assert view["dimensions_px"] == [1280, 720]
        assert view["alpha2_sha256"] == view["alpha3_sha256"]
        assert view["changed_pixel_fraction_alpha2_vs_alpha3"] == 0
        assert view["restored_crown_metrics_alpha2"]["green_dominant_fraction"] > 0.86
        assert view["restored_crown_metrics_alpha2"]["dark_fraction"] < 0.01
    assert v23_report["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_bounded_shadow_diagnostic.v23"
    )
    assert v23_report["status"] == (
        "alpha2_bounded_near_shadow_pair_captured_pending_artifact_review"
    )
    assert v23_report["production_promoted"] is False
    assert v23_report["source_map_modified"] is False
    assert v23_report["captures"]["all_captured"] is True
    shadow_policy = v23_report["bounded_shadow_policy"]
    assert shadow_policy["LeafOpacityScale"] == 2
    assert shadow_policy["shadowed_leaf_representation"] == "near_only"
    assert shadow_policy["cast_dynamic_shadow"] is True
    assert shadow_policy["cast_static_shadow"] is False
    assert shadow_policy["cast_contact_shadow"] is False
    assert shadow_policy["affect_distance_field_lighting"] is False
    assert shadow_policy["affect_dynamic_indirect_lighting"] is False
    assert shadow_policy["mid_leaf_cast_shadow"] is False
    assert shadow_policy["runtime_far_leaf_cast_shadow"] is False
    assert v23_review["schema"] == (
        "raftsim.unreal.futaleufu_native_canopy_bounded_shadow_review.v23"
    )
    assert v23_review["bounded_shadow_candidate_retained"] is False
    assert v23_review["alpha2_no_shadow_candidate_retained"] is True
    v23_conclusions = v23_review["diagnostic_conclusions"]
    assert v23_conclusions["v15_elongated_ground_carpet_recurred"] is False
    assert (
        v23_conclusions["bounded_shadow_causes_unacceptable_crown_self_darkening"]
        is True
    )
    assert v23_conclusions["bounded_shadow_is_production_promoted"] is False
    for view in v23_review["capture_evidence"].values():
        for role in (
            "no_shadow_reference",
            "bounded_shadow",
            "v15_native_shadow_reference",
            "v15_native_no_shadow",
            "v15_opaque_no_shadow",
        ):
            capture = REPO_ROOT / view[role]
            assert capture.is_file()
            assert _sha256(capture) == view[f"{role}_sha256"]
        assert view["dimensions_px"] == [1280, 720]
        assert view["off_crown_ground_shadow"]["v23_to_v15_recurrence_ratio"] < 0.002
        crown = view["shadow_affected_region"]
        assert crown["bounded_shadow_dark_fraction"] > 0.36
        assert crown["bounded_shadow_green_dominant_fraction"] < 0.01
        assert (
            crown["bounded_shadow_dark_fraction"]
            > crown["no_shadow_dark_fraction"] * 50
        )
    assert v24_report["schema"] == (
        "raftsim.unreal.futaleufu_dense_canopy_comparison.v1"
    )
    assert v24_report["status"] == (
        "paired_v24_sparse_dense_source_masked_canopy_captured_pending_human_review"
    )
    assert v24_report["production_promoted"] is False
    assert v24_report["source_map_modified"] is False
    assert v24_report["landscape_or_collision_modified"] is False
    assert v24_report["hydrodynamic_or_gameplay_authority_modified"] is False
    assert v24_report["captures"]["all_captured"] is True
    placement = v24_report["placement_statistics"]
    for view_name in ("sparse_guide_seat", "sparse_river_eye"):
        assert placement[view_name]["dense_local_review"] is False
        assert placement[view_name]["target_tree_count"] == 1200
        assert placement[view_name]["accepted_tree_count"] == 1200
        assert placement[view_name]["minimum_spacing_m"] == 15
        assert placement[view_name]["river_setback_m"] == 65
        assert placement[view_name]["maximum_lateral_offset_m"] == 300
    for view_name in ("dense_guide_seat", "dense_river_eye"):
        assert placement[view_name]["dense_local_review"] is True
        assert placement[view_name]["target_tree_count"] == 9000
        assert placement[view_name]["accepted_tree_count"] == 9000
        assert placement[view_name]["minimum_spacing_m"] == pytest.approx(6.5)
        assert placement[view_name]["river_setback_m"] == 24
        assert placement[view_name]["maximum_lateral_offset_m"] == 750
        assert placement[view_name]["hidden_fallback_pve_actor_count"] == 4
    assert v24_review["schema"] == ("raftsim.unreal.futaleufu_dense_canopy_review.v24")
    assert v24_review["status"] == (
        "density_response_validated_centerline_row_artifacts_and_scene_quality_failed_candidate_rejected"
    )
    assert v24_review["production_promoted"] is False
    assert v24_review["dense_camera_local_profile_retained"] is False
    v24_conclusions = v24_review["diagnostic_conclusions"]
    assert v24_conclusions["dense_profile_reached_target_count_in_both_views"] is True
    assert (
        v24_conclusions["dense_profile_materially_changes_visible_canopy_coverage"]
        is True
    )
    assert v24_conclusions["dense_profile_produces_continuous_lifelike_forest"] is False
    assert (
        v24_conclusions["centerline_parallel_row_and_trunk_fence_artifacts_present"]
        is True
    )
    assert v24_conclusions["whole_image_dark_coverage_regressed"] is True
    for view in v24_review["capture_evidence"].values():
        for role in ("sparse", "dense"):
            capture = REPO_ROOT / view[role]
            assert capture.is_file()
            assert _sha256(capture) == view[f"{role}_sha256"]
        assert view["dimensions_px"] == [1280, 720]
        assert view["dense_tree_count"] == 9000
        assert view["changed_pixel_fraction"] > 0.04
        assert view["dense_dark_fraction"] > view["sparse_dark_fraction"]
    assert v25_report["schema"] == (
        "raftsim.unreal.futaleufu_area_sampled_canopy_comparison.v1"
    )
    assert v25_report["status"] == (
        "paired_v25_centerline_area_sampled_canopy_captured_pending_human_review"
    )
    assert v25_report["production_promoted"] is False
    assert v25_report["source_map_modified"] is False
    assert v25_report["landscape_or_collision_modified"] is False
    assert v25_report["hydrodynamic_or_gameplay_authority_modified"] is False
    assert v25_report["captures"]["all_captured"] is True
    v25_placement = v25_report["placement_statistics"]
    for view_name in ("centerline_guide_seat", "centerline_river_eye"):
        assert v25_placement[view_name]["dense_local_review"] is True
        assert v25_placement[view_name]["area_sampled_review"] is False
        assert v25_placement[view_name]["accepted_tree_count"] == 9000
        assert v25_placement[view_name]["sampling_half_extent_m"] == 0
    for view_name in ("area_sampled_guide_seat", "area_sampled_river_eye"):
        view = v25_placement[view_name]
        assert view["dense_local_review"] is True
        assert view["area_sampled_review"] is True
        assert view["target_tree_count"] == 9000
        assert view["accepted_tree_count"] == 9000
        assert view["minimum_spacing_m"] == pytest.approx(6.5)
        assert view["river_setback_m"] == 24
        assert view["sampling_half_extent_m"] == 1100
        assert view["minimum_accepted_river_distance_m"] >= 24
        assert view["rejected_river_setback_count"] > 0
        assert view["rejected_stand_density_count"] > 0
        assert view["hidden_fallback_pve_actor_count"] == 4
    assert v25_review["schema"] == (
        "raftsim.unreal.futaleufu_area_sampled_canopy_review.v25"
    )
    assert v25_review["status"] == (
        "two_dimensional_topology_validated_source_mask_band_and_scene_quality_failed_candidate_rejected"
    )
    assert v25_review["production_promoted"] is False
    assert v25_review["area_sampled_topology_retained"] is True
    v25_conclusions = v25_review["diagnostic_conclusions"]
    assert (
        v25_conclusions["area_sampled_profile_reached_target_count_in_both_views"]
        is True
    )
    assert v25_conclusions["true_nearest_centerline_setback_enforced"] is True
    assert v25_conclusions["centerline_parallel_row_artifact_reduced"] is True
    assert v25_conclusions["source_mask_band_artifact_resolved"] is False
    assert v25_conclusions["continuous_lifelike_mixed_forest_produced"] is False
    for view in v25_review["capture_evidence"].values():
        for role in ("centerline", "area_sampled"):
            capture = REPO_ROOT / view[role]
            assert capture.is_file()
            assert _sha256(capture) == view[f"{role}_sha256"]
        assert view["dimensions_px"] == [1280, 720]
        assert view["centerline_tree_count"] == 9000
        assert view["area_sampled_tree_count"] == 9000
        assert view["changed_pixel_fraction"] > 0.08
        assert view["minimum_accepted_river_distance_m"] >= 24
    assert v26_report["schema"] == (
        "raftsim.unreal.futaleufu_world_stable_canopy_comparison.v1"
    )
    assert v26_report["status"] == (
        "paired_v26_camera_local_world_stable_canopy_captured_identical_world_placement_pending_human_review"
    )
    assert v26_report["production_promoted"] is False
    assert v26_report["source_map_modified"] is False
    assert v26_report["landscape_or_collision_modified"] is False
    assert v26_report["hydrodynamic_or_gameplay_authority_modified"] is False
    assert v26_report["world_stable_placement_fingerprints_match"] is True
    assert v26_report["captures"]["all_captured"] is True
    v26_placement = v26_report["placement_statistics"]
    world_stable_fingerprints = set()
    for view_name in ("world_stable_guide_seat", "world_stable_river_eye"):
        view = v26_placement[view_name]
        assert view["dense_local_review"] is False
        assert view["area_sampled_review"] is False
        assert view["world_stable_review"] is True
        assert view["candidate_count"] == 148909
        assert view["target_tree_count"] == 24000
        assert view["accepted_tree_count"] == 24000
        assert view["minimum_spacing_m"] == pytest.approx(6.5)
        assert view["river_setback_m"] == 24
        assert view["sampling_along_half_extent_m"] == 3000
        assert view["sampling_cross_half_extent_m"] == 1100
        assert view["occupancy_field_resolution"] == 512
        assert view["occupancy_feather_distance_m"] == 180
        assert view["minimum_accepted_river_distance_m"] >= 24
        assert view["hidden_fallback_pve_actor_count"] == 4
        world_stable_fingerprints.add(view["placement_fingerprint_fnv1a64"])
    assert world_stable_fingerprints == {"f30715fa74aee851"}
    assert v26_review["schema"] == (
        "raftsim.unreal.futaleufu_world_stable_canopy_review.v26"
    )
    assert v26_review["status"] == (
        "world_stability_validated_feather_settings_and_scene_quality_failed_candidate_rejected"
    )
    assert v26_review["production_promoted"] is False
    assert v26_review["world_stable_coordinate_contract_retained"] is True
    assert v26_review["spatial_occupancy_field_mechanism_retained"] is True
    assert v26_review["v26_occupancy_feather_settings_retained"] is False
    assert v26_review["world_stability_evidence"]["fingerprints_match"] is True
    v26_conclusions = v26_review["diagnostic_conclusions"]
    assert (
        v26_conclusions["world_stable_profile_reached_target_count_in_both_views"]
        is True
    )
    assert v26_conclusions["guide_and_river_eye_placement_fingerprints_match"] is True
    assert (
        v26_conclusions["corrected_curvilinear_domain_covers_both_review_reaches"]
        is True
    )
    assert (
        v26_conclusions["spatial_occupancy_feather_resolves_source_mask_bands"] is False
    )
    for view in v26_review["capture_evidence"].values():
        for role in ("camera_local", "world_stable"):
            capture = REPO_ROOT / view[role]
            assert capture.is_file()
            assert _sha256(capture) == view[f"{role}_sha256"]
        assert view["dimensions_px"] == [1280, 720]
        assert view["changed_pixel_fraction"] > 0.11
    editor_source = EDITOR_MODULE_PATH.read_text(encoding="utf-8")
    editor_header = EDITOR_MODULE_HEADER_PATH.read_text(encoding="utf-8")
    assert "RaftSim.CaptureFutaleufuNativeCanopyCorridorComparison" in editor_source
    assert "AddFutaleufuCanopyCorridorComparisonInstances" in editor_source
    assert "RaftSim_ExternalReviewOnly" in editor_source
    assert "CaptureFutaleufuNativeCanopyCorridorComparison" in editor_header
    assert "RaftSim.CaptureFutaleufuDenseCanopyComparison" in editor_source
    assert "RaftSimCaptureFutaleufuDenseCanopyComparison" in editor_source
    assert "CaptureFutaleufuDenseCanopyComparison" in editor_header
    assert "RaftSim.CaptureFutaleufuAreaSampledCanopyComparison" in editor_source
    assert "RaftSimCaptureFutaleufuAreaSampledCanopyComparison" in editor_source
    assert "CaptureFutaleufuAreaSampledCanopyComparison" in editor_header
    assert "bAreaSampledReview" in editor_source
    assert "RejectedStandDensityCount" in editor_source
    assert "RaftSim.CaptureFutaleufuWorldStableCanopyComparison" in editor_source
    assert "RaftSimCaptureFutaleufuWorldStableCanopyComparison" in editor_source
    assert "CaptureFutaleufuWorldStableCanopyComparison" in editor_header
    assert "bWorldStableReview" in editor_source
    assert "PlacementFingerprint" in editor_source
    assert "OccupancyFieldResolution = 512" in editor_source
    assert "SetMaterialUsage(MATUSAGE_InstancedStaticMeshes)" in editor_source
    assert "EnsureFutaleufuNativeCanopyInstancedMaterialUsage" in editor_source
    assert "RaftSim.CaptureFutaleufuNativeCanopyRenderDiagnostics" in editor_source
    assert "EFutaleufuCanopyCorridorRenderMode::NativeLeavesNoShadow" in editor_source
    assert "EFutaleufuCanopyCorridorRenderMode::OpaqueLeavesNoShadow" in editor_source
    assert "CaptureFutaleufuNativeCanopyRenderDiagnostics" in editor_header
    assert "RaftSim.CaptureFutaleufuNativeCanopyOpacityDiagnostics" in editor_source
    assert "LeafOpacityScale" in editor_source
    assert "LeafOpacityOverride" in editor_source
    assert "CaptureFutaleufuNativeCanopyOpacityDiagnostics" in editor_header
    assert "RaftSim.CaptureFutaleufuNativeCanopyLightingDiagnostics" in editor_source
    assert "LeafNormalStrength" in editor_source
    assert "LeafDiagnosticEmissive" in editor_source
    assert "CaptureFutaleufuNativeCanopyLightingDiagnostics" in editor_header
    assert (
        "RaftSim.CaptureFutaleufuNativeCanopyCorridorLightRigDiagnostics"
        in editor_source
    )
    assert "ApplyFutaleufuCanopyCorridorLightingTreatment" in editor_source
    assert "CaptureFutaleufuNativeCanopyCorridorLightRigDiagnostics" in editor_header
    assert "RaftSim.CaptureFutaleufuNativeCanopyReflectanceDiagnostics" in editor_source
    assert (
        "NativeAlphaScaleFourBaseColorDoubleTransmissionWhiteNoShadow" in editor_source
    )
    assert "CaptureFutaleufuNativeCanopyReflectanceDiagnostics" in editor_header
    assert (
        "RaftSim.CaptureFutaleufuNativeCanopyShadingModelDiagnostics" in editor_source
    )
    assert (
        "RaftSim.CaptureFutaleufuNativeCanopyBoundedShadowDiagnostics" in editor_source
    )
    assert "NativeAlphaScaleTwoBoundedShadow" in editor_source
    assert "SetCastContactShadow(false)" in editor_source
    assert "SetAffectDistanceFieldLighting(false)" in editor_source
    assert "SetAffectDynamicIndirectLighting(false)" in editor_source
    assert "CaptureFutaleufuNativeCanopyBoundedShadowDiagnostics" in editor_header
    assert "M_RaftSim_FutaleufuCoigue_Leaves_DefaultLitDiagnostic" in editor_source
    assert "CaptureFutaleufuNativeCanopyShadingModelDiagnostics" in editor_header
    assert "RaftSim.CaptureFutaleufuNativeCanopyMipPaddingDiagnostics" in editor_source
    assert "alpha_preserved_byte_for_byte" in editor_source
    assert "CaptureFutaleufuNativeCanopyMipPaddingDiagnostics" in editor_header
    assert (
        "RaftSim.CaptureFutaleufuNativeCanopyOpacitySelectionDiagnostics"
        in editor_source
    )
    assert "NativeAlphaScaleTwoNoShadow" in editor_source
    assert "CaptureFutaleufuNativeCanopyOpacitySelectionDiagnostics" in editor_header
    assert all(len(capture["sha256"]) == 64 for capture in v2_review["captures"])
    assert v2_review["nanite_comparison"]["masked_foliage_selected_path"] == (
        "nanite_disabled_full_source_geometry_retained"
    )
    v2_rejection_text = " ".join(v2_review["rejection_reasons"])
    assert "conifer-like silhouette" in v2_rejection_text
    assert "volumetric card field" in v2_rejection_text
    assert len(v2_review["next_iteration_requirements"]) == 4
