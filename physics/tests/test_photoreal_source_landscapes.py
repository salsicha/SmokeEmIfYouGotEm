# ruff: noqa: F405

from photoreal_test_support import *  # noqa: F401,F403


def test_source_landscape_candidates_are_imported_audited_and_captured():
    editor_source = EDITOR_MODULE_PATH.read_text(encoding="utf-8")
    build_rules = EDITOR_BUILD_RULES_PATH.read_text(encoding="utf-8")
    unreal_project = json.loads(UNREAL_PROJECT_PATH.read_text(encoding="utf-8"))
    engine_config = UNREAL_ENGINE_CONFIG_PATH.read_text(encoding="utf-8")
    manifest = json.loads(LANDSCAPE_CANDIDATE_MANIFEST_PATH.read_text(encoding="utf-8"))
    species_manifest_path = (
        REPO_ROOT
        / "unreal/Content/RaftSim/Environment/BiomeSpecies/pve_species_conversion_manifest.json"
    )
    species_manifest = json.loads(species_manifest_path.read_text(encoding="utf-8"))

    assert '"Landscape"' in build_rules
    assert '"LandscapeEditor"' in build_rules
    assert '"MeshUtilities"' in build_rules
    assert 'TEXT("RaftSim.CreateLandscapeImportCandidateMaps")' in editor_source
    assert 'TEXT("RaftSimCreateLandscapeImportCandidateMaps")' in editor_source
    assert "const int32 LandscapeSize = Candidate.LandscapeSize" in editor_source
    assert "Candidate.bPhysicalScaleSourceCorridor ? 2 : 1" in editor_source
    assert "constexpr int32 SubsectionSizeQuads = 63" in editor_source
    assert 'GetHeightmapFormatByExtension(TEXT(".png"))' in editor_source
    assert (
        "FLandscapeFileResolution ExpectedResolution(LandscapeSize, LandscapeSize)"
        in editor_source
    )
    assert "Landscape->Import(" in editor_source
    assert "ApplyPreviewOnlyLandscapeChannelBurn" in editor_source
    assert "SegmentLengthCm / CenterSampleSpacingCm" in editor_source
    assert "const int32 CrossSteps = bChilkoSourceScale ? 16 : 32" in editor_source
    assert "bounded render-only current relief" in editor_source
    assert "bPhysicalCorridor ? 5000.0f : -1600.0f" in editor_source
    assert "const float CurrentThread" in editor_source
    assert "const float FineCurrent" in editor_source
    assert "AddLandscapeCandidatePhysicalBankCorridorMesh" in editor_source
    assert "RaftSim_PhysicalCorridorDenseSourceTerrainTile_%02d_%s" in editor_source
    assert "bInternationalPhysicalCorridor" in editor_source
    assert "? 1250.0f" in editor_source
    assert "Candidate.HorizontalSpanXCm > 500000.0f ? 2500.0f : 400.0f" in editor_source
    assert "constexpr int32 TileCountX = 4" in editor_source
    assert "LoadOrCreatePhysicalSourceTerrainRenderMaterial" in editor_source
    assert 'TEXT("M_RaftSim_%s_PhysicalSourceTerrainRender")' in editor_source
    assert 'TEXT("/Game/RaftSim/Rendering/PhysicalCorridor/Textures")' in editor_source
    assert "lees_ferry_reach_2200_4700m/derived" in editor_source
    assert 'TEXT("colorado_lees_ferry_reach")' in editor_source
    assert "const FPhysicalCorridorTextureSpec PhysicalCorridors[]" in editor_source
    assert 'TEXT("PhysicalSourceAlbedo")' in editor_source
    assert 'TEXT("PhysicalSourceNormal")' in editor_source
    assert 'TEXT("PhysicalSourceAORoughnessHeight")' in editor_source
    assert 'TEXT("ForestFloorDetailAlbedo")' in editor_source
    assert 'TEXT("ForestFloorDetailNormal")' in editor_source
    assert 'TEXT("ForestFloorDetailRoughness")' in editor_source
    assert 'TEXT("RockGroundDetailAlbedo")' in editor_source
    assert 'TEXT("RockGroundDetailNormal")' in editor_source
    assert 'TEXT("RockGroundDetailRoughness")' in editor_source
    assert (
        "DetailCoordinates->UTiling = Candidate.HorizontalSpanXCm / DetailTileSizeCm"
        in editor_source
    )
    assert (
        "DetailCoordinates->VTiling = Candidate.HorizontalSpanYCm / DetailTileSizeCm"
        in editor_source
    )
    assert (
        "RockCoordinates->UTiling = Candidate.HorizontalSpanXCm / RockTileSizeCm"
        in editor_source
    )
    assert (
        "RockCoordinates->VTiling = Candidate.HorizontalSpanYCm / RockTileSizeCm"
        in editor_source
    )
    assert "DetailAlbedoWeight->R = bZambezi ? 0.16f" in editor_source
    assert "DetailNormalWeight->R = bBatokaWorldAlignedReview" in editor_source
    assert "? 0.0f" in editor_source
    assert "bZambezi ? 0.30f" in editor_source
    assert "DetailRoughnessWeight->R = 0.38f" in editor_source
    assert "RockAlbedoWeight->R = bZambezi ? 0.20f" in editor_source
    assert "RockNormalWeight->R = bZambezi ? 0.38f" in editor_source
    assert "RockRoughnessWeight->R = 0.44f" in editor_source
    assert "RockSlopeStart->R = bRockCanyon ? 0.10f : 0.16f" in editor_source
    assert "RockSlopeGain->R = 3.3f" in editor_source
    assert "SourceNormalWeight->R = 0.0f" in editor_source
    assert "colorado_lees_ferry_reach_terrain_albedo_2048.png" in editor_source
    assert "bRockCanyon ? 0.05f : 0.24f" in editor_source
    assert "bRockCanyon ? 0.04f : 0.18f" in editor_source
    assert "RenderReliefCapCm = bZambezi ? 420.0f" in editor_source
    assert "bFutaleufu ? 240.0f : 180.0f" in editor_source
    assert "0.250f, 0.365f, 230.0f, 150.0f" in editor_source
    assert "0.450f, 0.565f, 175.0f, 125.0f" in editor_source
    assert (
        "ConnectPreviewMaterialVectorInput(EditorOnlyData->Normal, ValidatedNormal)"
        in editor_source
    )
    assert "ValidatedAmbientOcclusion" in editor_source
    assert "UVs.Add(FVector2D(SourceU, SourceV))" in editor_source
    assert "VertexColorWeight->R = bZambezi ? 0.16f" in editor_source
    assert "DetailTileSizeCm = bZambezi ? 1800.0f" in editor_source
    assert "SourceAoWeight->R = (bZambezi || bFutaleufu) ? 0.18f" in editor_source
    assert "SourceAlbedo.SampleRawBilinear(SourceU, SourceV)" in editor_source
    assert "EHeightfieldSource::Editor).Get(0.0f)" in editor_source
    assert "non-self-intersecting dense source-terrain tiles" in editor_source
    assert "Landscape->SetActorHiddenInGame(true)" in editor_source
    assert "LandscapeComponent->SetVisibility(false, true)" in editor_source
    assert "LandscapeComponent->SetHiddenInGame(true, true)" in editor_source
    assert "Landscape remains the collision and height-query authority" in editor_source
    assert "MATUSAGE_Nanite" in editor_source
    assert "MATUSAGE_StaticLighting" in editor_source
    assert "UMaterialExpressionLandscapeLayerCoords" in editor_source
    assert "FRaftSimLandscapeMaterialCandidateSettings" in editor_source
    assert "MacroMappingScale = 1008.0f" in editor_source
    assert "WetBankArtifactSuppressionGain" in editor_source
    assert "WetBankBlendMaskAmplified" in editor_source
    for texture_parameter in (
        "SourceConditionedMacroAlbedo",
        "SourceConditionedMaterialZones",
        "SourceConditionedAORoughnessHeight",
        "SourceConditionedNormalDetail",
        "TerrainDetailAlbedo",
        "TerrainDetailAORoughnessHeight",
        "TerrainDetailNormal",
    ):
        assert f'TEXT("{texture_parameter}")' in editor_source
    assert "Nanite::AuditMaterials" in editor_source
    assert (
        "render_then_finish_compilation_recreate_landscape_components_render_again"
        in editor_source
    )
    assert editor_source.count("CaptureComponent->CaptureScene();") >= 2
    assert "GShaderCompilingManager->FinishAllCompilation()" in editor_source
    assert "LandscapeProxy->RecreateComponentsState()" in editor_source
    enabled_plugins = {
        plugin["Name"]
        for plugin in unreal_project["Plugins"]
        if plugin.get("Enabled") is True
    }
    assert "ProceduralVegetationEditor" in enabled_plugins
    assert "PCG" in enabled_plugins
    assert "r.Nanite.Foliage=1" in engine_config
    assert species_manifest["status"] == (
        "complete_engine_sample_species_converted_for_isolated_landscape_evaluation"
    )
    assert species_manifest["source_engine_version"] == "UE 5.8"
    assert species_manifest["external_asset_downloaded"] is False
    assert len(species_manifest["conversions"]) == 4
    assert len(species_manifest["promotion_blockers"]) == 5
    assert "UHierarchicalInstancedStaticMeshComponent" in editor_source
    assert "EHeightfieldSource::Editor" in editor_source
    assert "FRaftSimLandscapeCandidateFoliageSettings" in editor_source
    assert "LoadOrCreateLandscapeCandidateFoliageMaterialInstance" in editor_source
    assert "BindLandscapeCandidateFoliageMaterial" in editor_source
    assert 'TEXT("BaseColor Tint Leaves")' in editor_source
    assert 'TEXT("Translucency Tint Leaves")' in editor_source
    assert 'SlotName.Equals(TEXT("TwoSided")' in editor_source
    assert "LoadOrCreateLandscapeCandidatePveStaticMesh" in editor_source
    assert "ConvertMeshesToStaticMesh" in editor_source
    assert "PVE_Deciduous_Tree_01.PVE_Deciduous_Tree_01" in editor_source
    assert "PVE_Conifer_01.PVE_Conifer_01" in editor_source
    assert "PVE_Deciduous_Shrub_01.PVE_Deciduous_Shrub_01" in editor_source
    assert "PVE_Plant_01.PVE_Plant_01" in editor_source
    assert "Leaf_Twig_01.Leaf_Twig_01" not in editor_source
    assert "Conifer_Twig_01.Conifer_Twig_01" not in editor_source
    assert "constexpr int32 RingCount = 8" in editor_source
    assert "constexpr int32 SegmentCount = 20" in editor_source
    assert "Triangles.Add(SegmentIndex + NextSegment)" not in editor_source
    assert "LoadOrCreateLandscapeCandidateSolverSurfaceWaterParent" in editor_source
    assert "Material->SetShadingModel(MSM_DefaultLit)" in editor_source
    assert "Material->SetMaterialUsage(MATUSAGE_Water)" in editor_source
    assert "FScopedSingleLayerWaterCaptureReflectionOverride" not in editor_source
    assert "CaptureComponent->bAlwaysPersistRenderingState = true" in editor_source
    assert "EReflectionSourceType::CapturedScene" in editor_source
    for water_parameter in (
        "SurfaceTint",
        "VertexTintWeight",
        "WaterNormalAtlas",
        "ReflectionFillIntensity",
        "ReflectionTint",
        "SolverVisualizationNormal",
        "SolverVisualizationFields",
    ):
        assert f'TEXT("{water_parameter}")' in editor_source

    assert manifest["schema"] == "raftsim.unreal.landscape_import_candidate_manifest.v1"
    assert (
        manifest["status"] == "five_source_landscape_candidates_captured_review_gated"
    )
    assert (
        manifest["canonical_importer"]
        == "Unreal LandscapeEditor PNG heightmap file format"
    )
    assert len(manifest["candidates"]) == 5
    assert {candidate["river_id"] for candidate in manifest["candidates"]} == {
        "american_south_fork",
        "colorado_river",
        "pacuare",
        "zambezi_batoka_gorge",
        "futaleufu_terminator",
    }

    expected_material_assets = {
        "american_south_fork": (
            "unreal/Content/RaftSim/Materials/LandscapeCandidates/"
            "M_RaftSim_americansouthfork_physicalcorridor_SourceLandscapeCandidate.uasset"
        ),
        "colorado_river": (
            "unreal/Content/RaftSim/Materials/LandscapeCandidates/"
            "M_RaftSim_coloradoriver_physicalcorridor_SourceLandscapeCandidate.uasset"
        ),
        "pacuare": (
            "unreal/Content/RaftSim/Materials/LandscapeCandidates/"
            "M_RaftSim_pacuare_SourceLandscapeCandidate.uasset"
        ),
        "zambezi_batoka_gorge": (
            "unreal/Content/RaftSim/Materials/LandscapeCandidates/"
            "M_RaftSim_zambezibatokagorge_physicalcorridor_SourceLandscapeCandidate.uasset"
        ),
        "futaleufu_terminator": (
            "unreal/Content/RaftSim/Materials/LandscapeCandidates/"
            "M_RaftSim_futaleufuterminator_physicalcorridor_SourceLandscapeCandidate.uasset"
        ),
    }
    expected_detail_mapping_scales = {
        "american_south_fork": 96.0,
        "colorado_river": 144.0,
        "pacuare": 112.0,
        "zambezi_batoka_gorge": 152.0,
        "futaleufu_terminator": 116.0,
    }
    expected_dressing_counts = {
        "american_south_fork": {
            "boulders": 180,
            "foliage": 12000,
            "trunks": 0,
        },
        "colorado_river": {
            "boulders": 180,
            "foliage": 800,
            "trunks": 0,
        },
        "pacuare": {
            "boulders": 48,
            "foliage": 420,
            "trunks": 0,
        },
        "zambezi_batoka_gorge": {
            "boulders": 180,
            "foliage": 5600,
            "trunks": 0,
        },
        "futaleufu_terminator": {
            "boulders": 180,
            "foliage": 12000,
            "trunks": 0,
        },
    }
    expected_foliage_material_settings = {
        "american_south_fork": {
            "asset_name": "AmericanSouthFork",
            "broadleaf_front_tint": [0.86, 1.18, 0.72],
            "broadleaf_back_tint": [0.62, 0.91, 0.48],
            "broadleaf_transmission_tint": [0.48, 0.80, 0.36],
            "conifer_front_tint": [0.72, 1.00, 0.52],
            "conifer_back_tint": [0.48, 0.74, 0.32],
            "conifer_transmission_tint": [0.36, 0.62, 0.24],
            "roughness_strength": 0.68,
            "normal_strength": 0.65,
        },
        "colorado_river": {
            "asset_name": "ColoradoRiver",
            "broadleaf_front_tint": [0.96, 1.04, 0.58],
            "broadleaf_back_tint": [0.74, 0.82, 0.40],
            "broadleaf_transmission_tint": [0.62, 0.72, 0.34],
            "conifer_front_tint": [0.82, 0.90, 0.48],
            "conifer_back_tint": [0.64, 0.72, 0.34],
            "conifer_transmission_tint": [0.54, 0.62, 0.30],
            "roughness_strength": 0.82,
            "normal_strength": 0.52,
        },
        "pacuare": {
            "asset_name": "Pacuare",
            "broadleaf_front_tint": [0.70, 1.15, 0.62],
            "broadleaf_back_tint": [0.46, 0.86, 0.42],
            "broadleaf_transmission_tint": [0.34, 0.72, 0.30],
            "conifer_front_tint": [0.60, 1.00, 0.50],
            "conifer_back_tint": [0.40, 0.76, 0.34],
            "conifer_transmission_tint": [0.30, 0.64, 0.26],
            "roughness_strength": 0.74,
            "normal_strength": 0.58,
        },
        "zambezi_batoka_gorge": {
            "asset_name": "Zambezi",
            "broadleaf_front_tint": [0.92, 1.02, 0.48],
            "broadleaf_back_tint": [0.66, 0.76, 0.30],
            "broadleaf_transmission_tint": [0.56, 0.68, 0.24],
            "conifer_front_tint": [0.72, 1.00, 0.52],
            "conifer_back_tint": [0.48, 0.74, 0.32],
            "conifer_transmission_tint": [0.36, 0.62, 0.24],
            "roughness_strength": 0.82,
            "normal_strength": 0.50,
        },
        "futaleufu_terminator": {
            "asset_name": "Futaleufu",
            "broadleaf_front_tint": [0.66, 1.10, 0.56],
            "broadleaf_back_tint": [0.42, 0.78, 0.38],
            "broadleaf_transmission_tint": [0.32, 0.66, 0.30],
            "conifer_front_tint": [0.54, 0.92, 0.48],
            "conifer_back_tint": [0.34, 0.68, 0.30],
            "conifer_transmission_tint": [0.36, 0.62, 0.24],
            "roughness_strength": 0.76,
            "normal_strength": 0.60,
        },
    }
    expected_riverbed_settings = {
        "american_south_fork": {
            "riverbed_blend_weight": 0.18,
            "wet_bank_blend_weight": 0.24,
            "riverbed_roughness": 0.78,
            "riverbed_color_scale": [0.22, 0.32, 0.28],
            "wet_bank_color_scale": [0.52, 0.56, 0.50],
        },
        "colorado_river": {
            "riverbed_blend_weight": 0.78,
            "wet_bank_blend_weight": 0.58,
            "riverbed_roughness": 0.84,
            "riverbed_color_scale": [0.36, 0.28, 0.20],
            "wet_bank_color_scale": [0.58, 0.44, 0.34],
        },
        "pacuare": {
            "riverbed_blend_weight": 0.84,
            "wet_bank_blend_weight": 0.72,
            "riverbed_roughness": 0.72,
            "riverbed_color_scale": [0.22, 0.30, 0.24],
            "wet_bank_color_scale": [0.42, 0.50, 0.40],
        },
        "zambezi_batoka_gorge": {
            "riverbed_blend_weight": 0.74,
            "wet_bank_blend_weight": 0.62,
            "riverbed_roughness": 0.86,
            "riverbed_color_scale": [0.20, 0.20, 0.16],
            "wet_bank_color_scale": [0.36, 0.38, 0.30],
        },
        "futaleufu_terminator": {
            "riverbed_blend_weight": 0.86,
            "wet_bank_blend_weight": 0.74,
            "riverbed_roughness": 0.74,
            "riverbed_color_scale": [0.28, 0.34, 0.32],
            "wet_bank_color_scale": [0.44, 0.52, 0.48],
        },
    }
    expected_water_settings = {
        "american_south_fork": {
            "base_color_scale": 1.00,
            "surface_tint": [0.025, 0.120, 0.100],
            "vertex_tint_weight": 0.72,
            "reflection_fill_intensity": 0.26,
            "reflection_tint": [0.36, 0.52, 0.60],
            "opacity": 0.30,
            "phase_g": 0.15,
            "render_width_scale": 1.35,
            "render_normal_up_blend": 0.52,
            "render_displacement_scale": 0.70,
        },
        "colorado_river": {
            "base_color_scale": 1.20,
            "surface_tint": [0.22, 0.24, 0.15],
            "vertex_tint_weight": 0.55,
            "reflection_fill_intensity": 0.10,
            "reflection_tint": [0.38, 0.44, 0.46],
            "opacity": 0.55,
            "phase_g": 0.05,
            "render_width_scale": 1.17,
            "render_normal_up_blend": 0.60,
            "render_displacement_scale": 0.55,
        },
        "pacuare": {
            "base_color_scale": 1.00,
            "surface_tint": [0.018, 0.095, 0.065],
            "vertex_tint_weight": 0.62,
            "reflection_fill_intensity": 0.15,
            "reflection_tint": [0.32, 0.48, 0.54],
            "opacity": 0.40,
            "phase_g": 0.25,
            "render_width_scale": 1.45,
            "render_normal_up_blend": 0.48,
            "render_displacement_scale": 0.78,
        },
        "zambezi_batoka_gorge": {
            "base_color_scale": 1.10,
            "surface_tint": [0.13, 0.16, 0.065],
            "vertex_tint_weight": 0.58,
            "reflection_fill_intensity": 0.16,
            "reflection_tint": [0.40, 0.46, 0.39],
            "opacity": 0.52,
            "phase_g": 0.15,
            "render_width_scale": 1.24,
            "render_normal_up_blend": 0.52,
            "render_displacement_scale": 0.70,
        },
        "futaleufu_terminator": {
            "base_color_scale": 1.08,
            "surface_tint": [0.012, 0.20, 0.24],
            "vertex_tint_weight": 0.66,
            "reflection_fill_intensity": 0.16,
            "reflection_tint": [0.40, 0.60, 0.68],
            "opacity": 0.50,
            "phase_g": 0.15,
            "render_width_scale": 1.30,
            "render_normal_up_blend": 0.52,
            "render_displacement_scale": 0.70,
        },
    }
    expected_photographic_capture_settings = {
        "american_south_fork": {
            "sun_intensity": 5.20,
            "skylight_intensity": 1.25,
            "fog_density": 0.0025,
            "exposure_bias": -0.32,
            "saturation": 1.06,
            "contrast": 1.04,
            "sharpen": 0.24,
            "vignette": 0.06,
        },
        "colorado_river": {
            "sun_intensity": 5.40,
            "skylight_intensity": 2.10,
            "fog_density": 0.0016,
            "exposure_bias": -0.12,
            "saturation": 1.04,
            "contrast": 1.03,
            "sharpen": 0.26,
            "vignette": 0.06,
        },
        "pacuare": {
            "sun_intensity": 4.60,
            "skylight_intensity": 1.45,
            "fog_density": 0.0075,
            "exposure_bias": -0.18,
            "saturation": 1.04,
            "contrast": 1.03,
            "sharpen": 0.22,
            "vignette": 0.05,
        },
        "zambezi_batoka_gorge": {
            "sun_intensity": 5.30,
            "skylight_intensity": 1.65,
            "fog_density": 0.0038,
            "exposure_bias": -0.18,
            "saturation": 1.04,
            "contrast": 1.04,
            "sharpen": 0.24,
            "vignette": 0.06,
        },
        "futaleufu_terminator": {
            "sun_intensity": 4.75,
            "skylight_intensity": 1.55,
            "fog_density": 0.0055,
            "exposure_bias": -0.16,
            "saturation": 1.05,
            "contrast": 1.04,
            "sharpen": 0.24,
            "vignette": 0.06,
        },
    }
    water_parent_asset = REPO_ROOT / (
        "unreal/Content/RaftSim/Materials/LandscapeCandidates/"
        "M_RaftSim_SolverSurfaceWaterCandidate.uasset"
    )
    assert water_parent_asset.is_file()
    solver_foam_asset = REPO_ROOT / (
        "unreal/Content/RaftSim/Materials/LandscapeCandidates/"
        "M_RaftSim_SolverFieldFoamCandidate.uasset"
    )
    assert solver_foam_asset.is_file()

    for candidate in manifest["candidates"]:
        is_south_fork_physical_corridor = candidate["river_id"] == "american_south_fork"
        is_source_scale_physical_corridor = candidate["river_id"] in {
            "american_south_fork",
            "colorado_river",
            "zambezi_batoka_gorge",
            "futaleufu_terminator",
        }
        has_reviewed_rocks = candidate["river_id"] in {
            "american_south_fork",
            "zambezi_batoka_gorge",
            "futaleufu_terminator",
        }
        assert candidate["status"] == "captured_source_landscape_import_candidate"
        expected_photometry = expected_photographic_capture_settings[
            candidate["river_id"]
        ]
        assert candidate["photographic_capture_status"] == (
            "river_specific_recorded_capture_photometry_no_camera_film_grain"
        )
        for setting_name, expected_value in expected_photometry.items():
            assert candidate[f"photographic_{setting_name}"] == expected_value
        assert candidate["photographic_film_grain_intensity"] == 0.0
        assert candidate["heightfield_format"] == "16-bit grayscale PNG"
        assert candidate["heightfield_width_px"] == (
            2017 if is_source_scale_physical_corridor else 1009
        )
        assert candidate["heightfield_height_px"] == (
            2017 if is_source_scale_physical_corridor else 1009
        )
        assert candidate["component_count_total"] == 256
        assert candidate["num_subsections"] == (
            2 if is_source_scale_physical_corridor else 1
        )
        assert candidate["subsection_size_quads"] == 63
        if is_source_scale_physical_corridor:
            assert candidate["preview_channel_modified_sample_count"] == 0
            assert candidate["channel_burn_policy"] == (
                "source_manifest_recorded_bounded_hydrologic_channel_conditioning"
            )
            assert candidate["channel_burn_promotion_status"] == (
                "review_gated_derived_geometry_not_solver_or_surveyed_bathymetry"
            )
        else:
            assert candidate["channel_burn_policy"] == (
                "preview_only_analytic_channel_burn_for_landscape_import_validation"
            )
            assert candidate["channel_burn_promotion_status"] == (
                "not_solver_geometry_not_geospatially_approved_not_for_gameplay"
            )
        assert candidate["landscape_material_status"] == (
            "source_conditioned_macro_zones_plus_first_party_close_range_detail_review_candidate"
        )
        assert candidate["landscape_material_texture_asset_count"] == 7
        assert (
            candidate["landscape_material_zone_parameter"]
            == "SourceConditionedMaterialZones"
        )
        assert candidate["landscape_material_zone_semantics"] == (
            "rgb_r_terrain_wet_bank_g_vegetation_b_visible_water"
        )
        assert candidate["landscape_material_macro_mapping_scale"] == (
            2016.0 if is_source_scale_physical_corridor else 1008.0
        )
        assert candidate["landscape_material_detail_mapping_scale"] == (
            expected_detail_mapping_scales[candidate["river_id"]]
        )
        assert 0.0 < candidate["landscape_material_detail_albedo_weight"] <= 0.25
        assert 0.0 < candidate["landscape_material_detail_normal_weight"] <= 0.40
        assert (
            0.0 < candidate["landscape_material_detail_surface_response_weight"] <= 0.40
        )
        assert 0.0 <= candidate["landscape_material_emissive_fill_scale"] <= 0.06
        assert 0.0 <= candidate["landscape_material_specular_level"] <= 0.20
        expected_riverbed = expected_riverbed_settings[candidate["river_id"]]
        assert candidate["landscape_material_riverbed_blend_weight"] == (
            expected_riverbed["riverbed_blend_weight"]
        )
        assert candidate["landscape_material_wet_bank_blend_weight"] == (
            expected_riverbed["wet_bank_blend_weight"]
        )
        assert candidate["landscape_material_wet_bank_artifact_suppression_gain"] == 2.4
        assert candidate["landscape_material_riverbed_roughness"] == (
            expected_riverbed["riverbed_roughness"]
        )
        assert candidate["landscape_material_riverbed_color_scale"] == (
            expected_riverbed["riverbed_color_scale"]
        )
        assert candidate["landscape_material_wet_bank_color_scale"] == (
            expected_riverbed["wet_bank_color_scale"]
        )
        assert candidate["landscape_material_zone_conditioning_policy"].startswith(
            "source_visible_water_darkens_submerged_riverbed"
        )
        assert candidate["landscape_material_wet_bank_artifact_policy"] == (
            "saturate_existing_source_feather_band_to_suppress_bright_albedo_rails_without_"
            "widening_water_mask_or_adding_geometry"
        )
        assert candidate["landscape_material_promotion_status"] == (
            "review_only_not_lifelike_not_gameplay_promoted"
        )
        expected_dressing_status = (
            "source_mask_placed_complete_pve_species_and_rights_reviewed_rock_comparison_captured"
            if has_reviewed_rocks
            else "source_mask_placed_complete_pve_species_and_dense_irregular_rock_evaluation_captured"
        )
        assert candidate["landscape_dressing_status"] == expected_dressing_status
        assert candidate["landscape_dressing_asset_count"] == (
            13 if is_south_fork_physical_corridor else (10 if has_reviewed_rocks else 4)
        )
        assert candidate["landscape_dressing_source_species_skeletal_mesh_count"] == 4
        assert candidate["landscape_dressing_converted_species_static_mesh_count"] == 4
        assert candidate["landscape_dressing_external_review_source_manifest"] == (
            "unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/FirTree01_1K/"
            "polyhaven_fir_tree_01_source_manifest.json"
        )
        assert candidate[
            "landscape_dressing_external_review_broadleaf_source_manifest"
        ] == (
            "unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/TreeSmall02_1K/"
            "polyhaven_tree_small_02_source_manifest.json"
        )
        assert candidate[
            "landscape_dressing_external_review_conifer_source_manifest"
        ] == (candidate["landscape_dressing_external_review_source_manifest"])
        assert candidate["landscape_dressing_external_review_rock_source_manifest"] == (
            "unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/RockMossSet01_1K/"
            "polyhaven_rock_moss_set_01_source_manifest.json"
        )
        assert candidate["landscape_dressing_external_review_pine_source_manifest"] == (
            "unreal/Content/RaftSim/Environment/ExternalReview/PolyHaven/PineTree01_1K/"
            "polyhaven_pine_tree_01_source_manifest.json"
        )
        assert len(candidate["landscape_dressing_external_review_pine_assets"]) == 3
        if has_reviewed_rocks:
            assert candidate["landscape_dressing_external_review_asset_count"] == (
                9 if is_south_fork_physical_corridor else 6
            )
            assert candidate["landscape_dressing_external_review_rock_mesh_count"] == 6
            assert candidate["landscape_dressing_external_review_pine_mesh_count"] == (
                3 if is_south_fork_physical_corridor else 0
            )
            if is_south_fork_physical_corridor:
                assert candidate["landscape_dressing_external_review_status"] == (
                    "rights_reviewed_cc0_six_rock_and_three_pine_sets_loaded_with_explicit_"
                    "materials_for_isolated_south_fork_visual_comparison"
                )
            else:
                assert candidate["landscape_dressing_external_review_status"] == (
                    "rights_reviewed_cc0_six_rock_set_loaded_with_explicit_materials_for_"
                    "isolated_river_visual_comparison"
                )
            assert candidate["landscape_dressing_external_review_rock_status"] == (
                "six_meshes_nanite_and_material_validated_visual_comparison_only"
            )
            assert candidate["landscape_dressing_external_review_pine_status"] == (
                "three_meshes_physical_scale_nanite_and_materials_validated_sparse_visual_"
                "comparison_only"
                if is_south_fork_physical_corridor
                else "no_reviewed_pine_asset_selected_for_this_river"
            )
        else:
            assert candidate["landscape_dressing_external_review_asset_count"] == 0
            assert candidate["landscape_dressing_external_review_rock_mesh_count"] == 0
            assert candidate["landscape_dressing_external_review_pine_mesh_count"] == 0
            assert candidate["landscape_dressing_external_review_status"] == (
                "no_external_review_asset_selected_for_this_river"
            )
            assert candidate["landscape_dressing_external_review_rock_status"] == (
                "no_reviewed_rock_asset_selected_for_this_river"
            )
            assert candidate["landscape_dressing_external_review_pine_status"] == (
                "no_reviewed_pine_asset_selected_for_this_river"
            )
        assert candidate["landscape_dressing_external_review_asset"] == ""
        assert candidate["landscape_dressing_external_review_broadleaf_asset"] == ""
        assert candidate["landscape_dressing_external_review_conifer_asset"] == ""
        assert candidate["landscape_dressing_broadleaf_asset"] == (
            "/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_DeciduousTree01_Static"
        )
        assert candidate["landscape_dressing_conifer_asset"] == (
            "/Game/RaftSim/Environment/BiomeSpecies/SM_RaftSim_PVE_Conifer01_Static"
        )
        expected_instance_implementation = (
            "complete_pve_species_hierarchical_instancing_plus_rights_reviewed_six_variant_"
            "nanite_rock_and_sparse_three_variant_pine_hierarchical_instancing"
            if is_south_fork_physical_corridor
            else (
                "complete_pve_species_hierarchical_instancing_plus_rights_reviewed_six_variant_"
                "nanite_rock_hierarchical_instancing"
                if has_reviewed_rocks
                else "complete_pve_species_skeletal_to_static_conversion_plus_hierarchical_"
                "instancing_and_dense_irregular_procedural_boulders"
            )
        )
        assert candidate["landscape_dressing_instance_implementation"] == (
            expected_instance_implementation
        )
        assert len(candidate["landscape_dressing_source_species_skeletal_assets"]) == 4
        assert len(candidate["landscape_dressing_converted_species_static_assets"]) == 4
        for species_asset in candidate[
            "landscape_dressing_converted_species_static_assets"
        ]:
            species_path = REPO_ROOT / (
                "unreal/Content" + species_asset.removeprefix("/Game") + ".uasset"
            )
            assert species_path.is_file()
        expected_dressing = expected_dressing_counts[candidate["river_id"]]
        assert (
            candidate["landscape_dressing_boulder_instance_count"]
            == expected_dressing["boulders"]
        )
        assert (
            candidate["landscape_dressing_foliage_instance_count"]
            == expected_dressing["foliage"]
        )
        assert (
            candidate["landscape_dressing_canopy_tree_instance_count"]
            + candidate["landscape_dressing_understory_instance_count"]
            == expected_dressing["foliage"]
        )
        if candidate["river_id"] == "colorado_river":
            assert candidate["landscape_dressing_canopy_tree_instance_count"] == 0
        else:
            assert candidate["landscape_dressing_canopy_tree_instance_count"] > 0
        assert candidate["landscape_dressing_understory_instance_count"] > 0
        assert (
            candidate["landscape_dressing_trunk_instance_count"]
            == expected_dressing["trunks"]
        )
        assert candidate["landscape_dressing_trunk_asset"] is None
        assert candidate["landscape_dressing_source_mask_status"] == (
            "water_and_vegetation_masks_loaded_and_used_for_candidate_selection"
        )
        expected_foliage_material = expected_foliage_material_settings[
            candidate["river_id"]
        ]
        assert candidate["landscape_dressing_foliage_material_status"] == (
            "three_river_specific_texture_preserving_two_sided_foliage_slots_bound_one_"
            "complete_species_native_material_retained"
        )
        assert candidate["landscape_dressing_foliage_material_asset_count"] == 3
        assert candidate["landscape_dressing_foliage_material_bound_slot_count"] >= 3
        assert (
            candidate["landscape_dressing_native_foliage_material_fallback_slot_count"]
            == 1
        )
        for material_kind in ("broadleaf", "conifer", "understory"):
            expected_object_path = (
                "/Game/RaftSim/Materials/LandscapeCandidates/"
                f"MI_RaftSim_{expected_foliage_material['asset_name']}_"
                f"{material_kind.title()}_BiomeFoliageCandidate"
            )
            assert candidate[f"landscape_dressing_{material_kind}_material_asset"] == (
                expected_object_path
            )
            assert (
                REPO_ROOT
                / (
                    "unreal/Content"
                    + expected_object_path.removeprefix("/Game")
                    + ".uasset"
                )
            ).is_file()
        manifest_setting_names = {
            "broadleaf_front_tint": "landscape_dressing_broadleaf_front_tint",
            "broadleaf_back_tint": "landscape_dressing_broadleaf_back_tint",
            "broadleaf_transmission_tint": "landscape_dressing_broadleaf_transmission_tint",
            "conifer_front_tint": "landscape_dressing_conifer_front_tint",
            "conifer_back_tint": "landscape_dressing_conifer_back_tint",
            "conifer_transmission_tint": "landscape_dressing_conifer_transmission_tint",
            "roughness_strength": "landscape_dressing_foliage_roughness_strength",
            "normal_strength": "landscape_dressing_foliage_normal_strength",
        }
        for setting_name, manifest_name in manifest_setting_names.items():
            assert candidate[manifest_name] == expected_foliage_material[setting_name]
        assert candidate["procedural_vegetation_editor_plugin_enabled"] is True
        assert candidate["nanite_foliage_project_setting_enabled"] is True
        assert candidate["landscape_dressing_boulder_mesh_nanite_enabled"] is (
            has_reviewed_rocks
        )
        assert candidate["landscape_dressing_broadleaf_mesh_nanite_enabled"] is True
        assert candidate["landscape_dressing_conifer_mesh_nanite_enabled"] is True
        assert candidate["landscape_dressing_understory_mesh_nanite_enabled"] is True
        expected_promotion_status = (
            "rights_reviewed_rock_and_pine_visual_comparison_only_not_geology_ecology_guide_"
            "performance_or_gameplay_promoted"
            if is_south_fork_physical_corridor
            else (
                "rights_reviewed_rock_visual_comparison_only_not_geology_ecology_guide_"
                "performance_or_gameplay_promoted"
                if has_reviewed_rocks
                else "complete_pve_sample_species_geometry_evaluation_only_requires_biome_specific_"
                "pve_exports_production_rock_asset_guide_and_performance_review"
            )
        )
        assert (
            candidate["landscape_dressing_promotion_status"]
            == expected_promotion_status
        )
        expected_water = expected_water_settings[candidate["river_id"]]
        assert candidate["water_material_status"] == (
            "solver_surface_default_lit_candidate_bound_and_captured"
        )
        assert candidate["water_shading_model"] == "DefaultLit"
        assert candidate["water_blend_mode"] == "Opaque"
        assert (
            candidate["water_custom_output"]
            == "none_surface_only_solver_conditioned_shading"
        )
        assert candidate["water_volume_parameter_status"] == (
            "inactive_single_layer_evaluation_values_retained_in_manifest_only"
        )
        assert candidate["water_material_bound_component_count"] == 1
        assert candidate["water_base_color_scale"] == expected_water["base_color_scale"]
        assert candidate["water_surface_tint"] == expected_water["surface_tint"]
        assert (
            candidate["water_vertex_tint_weight"]
            == expected_water["vertex_tint_weight"]
        )
        assert (
            candidate["water_reflection_fill_intensity"]
            == expected_water["reflection_fill_intensity"]
        )
        assert candidate["water_reflection_tint"] == expected_water["reflection_tint"]
        assert candidate["water_surface_opacity"] == 1.0
        assert (
            candidate["water_render_width_scale"]
            == expected_water["render_width_scale"]
        )
        assert (
            candidate["water_render_normal_up_blend"]
            == expected_water["render_normal_up_blend"]
        )
        assert (
            candidate["water_render_displacement_scale"]
            == expected_water["render_displacement_scale"]
        )
        assert candidate["water_near_camera_synthetic_wedge_fill_enabled"] is False
        assert candidate["water_near_camera_synthetic_wedge_fill_policy"] == (
            "disabled_for_solver_surface_water_candidates_legacy_diagnostic_branch_retained"
        )
        assert candidate["water_solver_visualization_field_manifest"] == str(
            SOLVER_VISUALIZATION_FIELD_MANIFEST_RELATIVE_PATH
        )
        assert candidate["water_solver_visualization_authority"] == (
            "review_only_noncolliding_render_geometry_and_material_derivative_does_not_change_"
            "solver_collision_raft_forces_or_feature_forcing"
        )
        assert candidate["water_solver_render_geometry_collision_enabled"] is False
        assert candidate["water_solver_foam_material"] == (
            "/Game/RaftSim/Materials/LandscapeCandidates/M_RaftSim_SolverFieldFoamCandidate"
        )
        if is_south_fork_physical_corridor:
            assert candidate["solver_rapid_river_eye_capture"].endswith(
                "american_south_fork_solver_rapid_river_eye_downstream.png"
            )
            assert candidate["solver_rapid_capture_status"] == (
                "captured_physical_corridor_midreach_geometry_review_without_solver_field"
            )
            assert candidate["water_solver_visualization_field_status"] == (
                "disabled_for_physical_corridor_until_solver_grid_georeferencing_is_validated"
            )
            assert candidate["water_solver_visualization_field_texture_count"] == 0
            assert (
                candidate["water_solver_visualization_field_feature_strength_scale"]
                is None
            )
            assert candidate["water_solver_visualization_field_enable"] == 0.0
            assert candidate["water_solver_macro_normal_weight"] == 0.0
            assert candidate["water_solver_depth_color_weight"] == 0.0
            assert candidate["water_solver_field_roughness_weight"] == 0.0
            assert candidate["water_solver_froude_aeration_weight"] == 0.0
            assert candidate["water_solver_speed_visual_gain"] == 1.50
            assert candidate["water_solver_froude_visual_gain"] == 3.00
            assert candidate["water_solver_surface_relief_scale"] == 0.09
            assert candidate["water_solver_surface_relief_cap_cm"] == 36.0
            assert candidate["water_solver_analytic_displacement_residual_scale"] == 1.0
            assert candidate["water_solver_foam_status"] == (
                "disabled_until_physical_corridor_solver_grid_georeferencing_is_validated"
            )
            assert candidate["water_solver_foam_max_opacity"] == 0.0
            assert candidate["water_solver_foam_surface_offset_cm"] == 0.0
        elif is_source_scale_physical_corridor:
            assert candidate["solver_rapid_river_eye_capture"] == ""
            assert candidate["solver_rapid_capture_status"] == (
                "not_available_without_river_specific_validated_solver_field"
            )
            assert candidate["water_solver_visualization_field_status"] == (
                "disabled_for_physical_corridor_until_solver_grid_georeferencing_is_validated"
            )
            assert candidate["water_solver_visualization_field_texture_count"] == 0
            assert (
                candidate["water_solver_visualization_field_feature_strength_scale"]
                is None
            )
            assert candidate["water_solver_visualization_field_enable"] == 0.0
            assert candidate["water_solver_macro_normal_weight"] == 0.0
            assert candidate["water_solver_depth_color_weight"] == 0.0
            assert candidate["water_solver_field_roughness_weight"] == 0.0
            assert candidate["water_solver_froude_aeration_weight"] == 0.0
            assert candidate["water_solver_speed_visual_gain"] == 0.0
            assert candidate["water_solver_froude_visual_gain"] == 0.0
            assert candidate["water_solver_surface_relief_scale"] == 0.0
            assert candidate["water_solver_surface_relief_cap_cm"] == 0.0
            assert candidate["water_solver_analytic_displacement_residual_scale"] == 1.0
            assert candidate["water_solver_foam_status"] == (
                "disabled_until_physical_corridor_solver_grid_georeferencing_is_validated"
            )
            assert candidate["water_solver_foam_max_opacity"] == 0.0
            assert candidate["water_solver_foam_surface_offset_cm"] == 0.0
        else:
            assert candidate["solver_rapid_river_eye_capture"] == ""
            assert candidate["solver_rapid_capture_status"] == (
                "not_available_without_river_specific_validated_solver_field"
            )
            assert candidate["water_solver_visualization_field_status"] == (
                "not_available_for_river_no_cross_river_field_reuse"
            )
            assert candidate["water_solver_visualization_field_texture_count"] == 0
            assert (
                candidate["water_solver_visualization_field_feature_strength_scale"]
                is None
            )
            assert candidate["water_solver_visualization_field_enable"] == 0.0
            assert candidate["water_solver_macro_normal_weight"] == 0.0
            assert candidate["water_solver_depth_color_weight"] == 0.0
            assert candidate["water_solver_field_roughness_weight"] == 0.0
            assert candidate["water_solver_froude_aeration_weight"] == 0.0
            assert candidate["water_solver_speed_visual_gain"] == 0.0
            assert candidate["water_solver_froude_visual_gain"] == 0.0
            assert candidate["water_solver_surface_relief_scale"] == 0.0
            assert candidate["water_solver_surface_relief_cap_cm"] == 0.0
            assert candidate["water_solver_analytic_displacement_residual_scale"] == 1.0
            assert candidate["water_solver_foam_status"] == (
                "not_available_without_river_specific_validated_solver_field"
            )
            assert candidate["water_solver_foam_max_opacity"] == 0.0
            assert candidate["water_solver_foam_surface_offset_cm"] == 0.0
        assert 0.0 <= candidate["water_emissive_fill_scale"] <= 0.10
        assert 0.0 < candidate["water_roughness"] <= 0.45
        assert 0.0 < candidate["water_normal_intensity"] <= 0.90
        assert candidate["water_normal_atlas_sampling_policy"] == (
            "half_period_dual_sample_crossfade_prevents_frac_tile_boundaries"
        )
        assert candidate["water_normal_atlas_phase_offset"] == 0.5
        assert candidate["water_inactive_single_layer_refraction_ior"] == 1.333
        assert (
            candidate["water_inactive_single_layer_phase_g"]
            == expected_water["phase_g"]
        )
        assert candidate["water_reflection_capture_policy"].startswith(
            "default_lit_surface_uses_movable_skylight"
        )
        assert candidate["water_material_promotion_status"] == (
            "review_only_requires_visual_guide_solver_hazard_and_performance_validation"
        )
        water_instance_asset = REPO_ROOT / (
            "unreal/Content"
            + candidate["water_material_asset"].split(".")[0].removeprefix("/Game")
            + ".uasset"
        )
        assert water_instance_asset.is_file()
        assert candidate["material_usage_contract"] == (
            "static_lighting_non_nanite_physical_corridor_review"
            if is_source_scale_physical_corridor
            else "nanite_and_static_lighting"
        )
        assert candidate["material_bound_component_count"] == 256
        assert candidate["material_binding_status"] == "all_source_components_bound"
        assert candidate["nanite_enabled"] is (not is_source_scale_physical_corridor)
        assert candidate["nanite_component_count"] == (
            0 if is_source_scale_physical_corridor else 4
        )
        assert candidate["nanite_material_slot_count"] == (
            0 if is_source_scale_physical_corridor else 256
        )
        assert candidate["nanite_material_bound_slot_count"] == (
            0 if is_source_scale_physical_corridor else 256
        )
        assert candidate["nanite_material_audit_error_count"] == 0
        assert candidate["nanite_representation_status"] == (
            "disabled_for_physical_corridor_after_captured_nanite_hole_regression"
            if is_source_scale_physical_corridor
            else "enabled_and_built_up_to_date"
        )
        assert candidate["capture_shader_warmup_policy"] == (
            "render_then_finish_compilation_recreate_landscape_components_render_again"
        )
        assert candidate["promotion_status"] == (
            "review_gated_isolated_candidate_not_enabled_for_gameplay_or_active_previews"
        )

        assert (REPO_ROOT / candidate["source_heightfield"]).is_file()
        assert (REPO_ROOT / candidate["source_heightfield_manifest"]).is_file()
        assert (REPO_ROOT / candidate["unreal_import_contract"]).is_file()
        assert (REPO_ROOT / candidate["guide_seat_capture"]).is_file()
        assert (REPO_ROOT / candidate["river_eye_capture"]).is_file()
        if candidate["solver_rapid_river_eye_capture"]:
            assert (REPO_ROOT / candidate["solver_rapid_river_eye_capture"]).is_file()
        assert (REPO_ROOT / expected_material_assets[candidate["river_id"]]).is_file()
        # Candidate maps are regenerable diagnostics and no longer versioned
        # (docs/generated-artifact-retention-policy.md, July 17 revision).
        assert candidate["map_package"].startswith("/Game/RaftSim/Maps/")


def test_production_visual_source_acquisition_queue_is_rights_gated_for_all_rivers():
    queue = json.loads(
        PRODUCTION_VISUAL_SOURCE_ACQUISITION_QUEUE_PATH.read_text(encoding="utf-8")
    )

    assert queue["schema"] == "raftsim.production_visual_source_acquisition_queue.v1"
    assert (
        queue["status"]
        == "rights_gated_visual_source_queue_recorded_no_third_party_media_downloaded"
    )
    assert queue["policy"]["official_sources_first"] is True
    assert (
        queue["policy"][
            "social_media_and_public_photo_sites_link_only_until_explicit_item_rights_clear"
        ]
        is True
    )
    assert (
        queue["policy"][
            "no_scraping_downloading_training_or_packaging_third_party_media_without_rights"
        ]
        is True
    )
    assert (
        queue["policy"][
            "visual_sources_must_not_hide_hazards_rescue_targets_or_physics_failures"
        ]
        is True
    )

    official_source_ids = {
        source["source_id"] for source in queue["reviewed_official_source_leads"]
    }
    assert {
        "blm_south_fork_american_recreation_map_photo_lead",
        "cdec_chili_bar_cbr_live_and_historical_flow",
        "nps_grand_canyon_river_trip_and_media_leads",
        "nps_grand_canyon_public_domain_photo_broll_archive",
        "usbr_glen_canyon_water_operations_release_context",
        "snit_cr_ogc_pacuare_orthophoto_environment_hydrology_nodes",
    }.issubset(official_source_ids)

    official_river_ids = {
        river_id
        for source in queue["reviewed_official_source_leads"]
        for river_id in source["river_ids"]
    }
    assert official_river_ids == {"american_south_fork", "colorado_river", "pacuare"}
    assert any(
        "seasonal_flow_or_release_history" in source["source_classes"]
        for source in queue["reviewed_official_source_leads"]
    )
    assert any(
        "aerial_or_satellite_imagery" in source["source_classes"]
        for source in queue["reviewed_official_source_leads"]
    )
    assert any(
        "official_photo_reference_leads" in source["source_classes"]
        for source in queue["reviewed_official_source_leads"]
    )

    social_queue_ids = {
        item["queue_id"] for item in queue["social_and_public_media_link_queue"]
    }
    assert social_queue_ids == {
        "american_south_fork_public_social_reference_search",
        "colorado_grand_canyon_public_social_reference_search",
        "pacuare_public_social_reference_search",
    }
    for item in queue["social_and_public_media_link_queue"]:
        assert (
            item["allowed_use_before_rights_clearance"]
            == "manual_visual_questions_only"
        )
        assert item["blocked_until"].startswith("explicit_item_rights")
        assert "source_url" in item["must_record_per_item"]
        assert "license_or_written_permission" in item["must_record_per_item"]
        assert "allowed_use" in item["must_record_per_item"]
        assert item["search_targets"]

    assert set(queue["per_river_next_actions"]) == {
        "american_south_fork",
        "colorado_river",
        "pacuare",
    }
    assert "Promote exact source layers and media items" in queue["next_checkpoint"]


def test_production_visual_source_item_intake_records_unpromoted_item_level_gates():
    intake = json.loads(
        PRODUCTION_VISUAL_SOURCE_ITEM_INTAKE_PATH.read_text(encoding="utf-8")
    )

    assert intake["schema"] == "raftsim.production_visual_source_item_intake.v1"
    assert (
        intake["status"]
        == "item_level_intake_slots_recorded_no_media_downloaded_no_items_promoted"
    )
    assert (
        intake["source_acquisition_queue"]
        == "physics/data/real_world/production_visual_source_acquisition_queue.json"
    )
    assert intake["policy"]["item_level_metadata_required_before_art_use"] is True
    assert intake["policy"]["no_media_downloaded_or_packaged_by_this_manifest"] is True
    assert (
        intake["policy"][
            "no_social_media_scraping_training_texture_extraction_or_photogrammetry_without_explicit_rights"
        ]
        is True
    )
    assert (
        intake["policy"][
            "promotion_requires_guide_or_oarsman_review_and_hazard_rescue_readability_check"
        ]
        is True
    )

    assert intake["summary"] == {
        "river_count": 3,
        "intake_item_count": 9,
        "official_source_item_count": 5,
        "first_party_or_permission_request_count": 4,
        "promoted_item_count": 0,
        "media_files_downloaded": 0,
        "rights_cleared_for_asset_use": 0,
        "per_river_item_count": {
            "american_south_fork": 3,
            "colorado_river": 3,
            "pacuare": 3,
        },
    }

    required_fields = set(intake["required_fields_before_promotion"])
    assert {
        "source_url",
        "creator_or_responsible_institution",
        "license_or_written_permission",
        "flow_or_release_or_rain_context",
        "guide_oarsman_or_local_reviewer",
        "hazard_rescue_readability_notes",
        "final_promotion_decision",
    }.issubset(required_fields)
    assert (
        "production_texture_or_material_source" in intake["blocked_uses_until_promoted"]
    )
    assert (
        "AI_training_or_style_reference_dataset"
        in intake["blocked_uses_until_promoted"]
    )

    items_by_id = {item["item_id"]: item for item in intake["intake_items"]}
    assert set(items_by_id) == {
        "south_fork_blm_map_pdf_access_context",
        "south_fork_cdec_cbr_low_medium_high_flow_windows",
        "south_fork_first_party_field_capture_request",
        "colorado_nps_public_domain_photo_archive_selection",
        "colorado_usbr_usgs_release_and_gauge_pairing",
        "colorado_first_party_or_permitted_boater_media_request",
        "pacuare_snit_orthophoto_and_environment_layer_selection",
        "pacuare_public_social_and_creator_permission_candidates",
        "pacuare_first_party_outfitter_capture_request",
    }
    assert {item["river_id"] for item in intake["intake_items"]} == {
        "american_south_fork",
        "colorado_river",
        "pacuare",
    }
    for item in intake["intake_items"]:
        assert item["promotion_decision"] == "not_promoted"
        assert item["current_status"]
        assert item["missing_metadata"]
        assert item["blocked_uses"]

    assert (
        items_by_id["south_fork_cdec_cbr_low_medium_high_flow_windows"][
            "known_metadata"
        ]["station_id"]
        == "CBR"
    )
    assert (
        "USGS-09380000 Colorado River at Lees Ferry"
        in items_by_id["colorado_usbr_usgs_release_and_gauge_pairing"][
            "known_metadata"
        ]["related_gauge_leads"]
    )
    assert (
        "Ortofoto"
        in items_by_id["pacuare_snit_orthophoto_and_environment_layer_selection"][
            "known_metadata"
        ]["candidate_nodes"]
    )
    assert "Fill exact item URLs/layers/windows" in intake["next_checkpoint"]
