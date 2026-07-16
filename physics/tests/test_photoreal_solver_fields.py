# ruff: noqa: F405

from photoreal_test_support import *  # noqa: F401,F403


def test_cpp_solver_visualization_fields_are_provenance_locked_and_unreal_bound():
    manifest = json.loads(
        SOLVER_VISUALIZATION_FIELD_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    editor_source = EDITOR_MODULE_PATH.read_text(encoding="utf-8")

    assert manifest["schema"] == "raftsim.unreal.cpp_solver_visualization_fields.v2"
    assert manifest["status"] == (
        "reference_playback_visualization_fields_generated_for_south_fork_review"
    )
    assert manifest["river_id"] == "american_south_fork"
    assert manifest["flow_band"] == "median"
    assert manifest["solver"] == "raftsim_water_cpp_v1"
    assert manifest["solver_mode"] == "finite_volume"
    assert manifest["source_frame_index"] == 8
    assert manifest["source_grid"] == {
        "row_count": 20,
        "column_count": 56,
        "cell_count": 1120,
        "x_extent_m": [0.0, 220.0],
        "y_extent_m": [-19.0, 19.0],
        "wet_cell_count": 863,
    }
    for artifact in manifest["source_artifacts"].values():
        artifact_path = REPO_ROOT / artifact["path"]
        assert artifact_path.is_file()
        assert artifact_path.stat().st_size == artifact["size_bytes"]
        assert _sha256(artifact_path) == artifact["sha256"]

    evidence = manifest["visualization_source_evidence"]
    assert evidence["feature_strength_scale"] == 0
    assert evidence["boundary_mode"] == "scenario"
    assert evidence["flux_scheme"] == "hll"
    assert evidence["threshold_tier"] == "unreal_prototype"
    assert evidence["parity_mode"] == "reference_playback"
    assert evidence["solver_approval_passed"] is False
    assert evidence["full_gate_passed"] is False
    assert evidence["live_water_approved"] is False
    assert len(evidence["report_set_lock_hash"]) == 64
    assert manifest["normalization"]["caps"] == {
        "depth_m": 6.0,
        "speed_mps": 10.0,
        "froude": 7.0,
        "surface_relief_m": 4.0,
    }
    relief = manifest["surface_relief_derivation"]
    assert relief["source_field"] == "eta"
    assert relief["render_height_scale"] == 0.09
    assert relief["render_height_cap_cm"] == 36.0
    assert relief["wet_cell_clipped_fraction"] == 0.0
    for field_id, field_range in manifest["field_ranges"].items():
        assert field_range[0] <= field_range[1], field_id
        assert all(value == value for value in field_range), field_id

    expected_texture_paths = {
        "surface_normal": REPO_ROOT / SOLVER_VISUALIZATION_NORMAL_RELATIVE_PATH,
        "depth_speed_froude": REPO_ROOT / SOLVER_VISUALIZATION_PACKED_RELATIVE_PATH,
    }
    for texture_id, texture_path in expected_texture_paths.items():
        texture = manifest["textures"][texture_id]
        assert texture_path.is_file()
        assert texture["path"] == str(texture_path.relative_to(REPO_ROOT))
        assert _sha256(texture_path) == texture["sha256"]
        with Image.open(texture_path) as image:
            assert image.mode == ("RGB" if texture_id == "surface_normal" else "RGBA")
            assert image.size == (1024, 512)
            extrema = image.getextrema()
            assert all(
                channel_max > channel_min for channel_min, channel_max in extrema
            )
            if texture_id == "surface_normal":
                assert extrema[2][0] >= 224

    policy = manifest["authority_policy"]
    assert policy["physical_authority"] == "none_reference_playback_visualization_only"
    assert policy["source_runtime_candidate"] == "custom_cxx_shallow_water_solver"
    assert policy["parity_mode"] == "reference_playback"
    assert policy["live_water_approved"] is False
    assert policy["derivative_scope"] == (
        "review_only_noncolliding_render_geometry_and_material_response_on_landscape_candidate_ribbon"
    )
    assert policy["feature_forcing_enabled"] is False
    assert policy["changes_collision_or_raft_forces"] is False
    assert policy["changes_solver_state"] is False
    assert policy["may_hide_conservation_or_parity_failures"] is False
    assert manifest["render_binding"]["river_scope"] == ["american_south_fork"]
    assert manifest["render_binding"]["other_river_status"] == (
        "not_bound_until_equivalent_river_specific_playback_or_solver_exports_exist"
    )
    assert manifest["render_binding"]["feature_weights"]["macro_normal"] == 0.22
    assert manifest["render_binding"]["feature_weights"]["froude_aeration"] == 0.34
    assert manifest["render_binding"]["visual_decode_gains"] == {
        "speed": 1.5,
        "froude": 3.0,
        "policy": "bounded_decode_of_fixed_physical_normalization_not_feature_forcing",
    }
    foam = manifest["render_binding"]["foam_overlay"]
    assert foam["max_opacity"] == 0.72
    assert foam["surface_offset_cm"] == 1.4
    assert foam["collision_enabled"] is False
    assert (
        foam["policy"]
        == "procedural_breakup_is_confined_to_validated_hydraulic_aeration_mask"
    )
    rapid_capture = manifest["sampling"]["solver_rapid_capture"]
    assert (
        rapid_capture["camera_solver_u"]
        < 20.0 / 55.0
        < rapid_capture["target_solver_u"]
    )

    for token in (
        "GetSolverVisualizationFieldTextureAssetSpecs",
        "CreateSolverVisualizationFieldTextureAssets",
        "SolverVisualizationFields",
        "SolverVisualizationNormal",
        "SolverFieldEnable",
        "SolverMacroNormalWeight",
        "SolverDepthColorWeight",
        "SolverFieldRoughnessWeight",
        "SolverFroudeAerationWeight",
        "SolverSpeedVisualGain",
        "SolverFroudeVisualGain",
        "SolverSurfaceReliefScale",
        "SampleRawBilinear",
        "bCompressionNoAlpha",
        "T_RaftSim_AmericanSouthFork_CppSolverSurfaceNormal",
        "T_RaftSim_AmericanSouthFork_CppSolverDepthSpeedFroude",
        "TA_Clamp",
        "!bUsePhysicalCandidateShading",
        "RaftSim_SolverRapid_RiverEyeCaptureCamera",
        "LoadOrCreateLandscapeCandidateSolverFoamMaterial",
        "M_RaftSim_SolverFieldFoamCandidate",
        "RaftSim_SolverFieldFoam_",
        "SolverFoamBreakupNoise",
        "SolverFoamOpacity",
    ):
        assert token in editor_source
