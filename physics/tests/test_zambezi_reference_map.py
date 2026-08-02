import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from raftsim.named_rapid_registry import build_editor_markers
from raftsim.zambezi_reference_map import (
    CATALOG_RELATIVE,
    COOKED_FIELDS_RELATIVE,
    COORDINATE_MAP_RELATIVE,
    HEIGHT_IMAGE_SHA256,
    OUTPUT_RELATIVE,
    RAPID_MAP_SHA256,
    REFERENCE_HEIGHTFIELD_SIZE,
    REFERENCE_MESH_SIZE,
    RUNTIME_BREAKING_DOWNSTREAM_FROUDE_MAX,
    RUNTIME_BREAKING_UPSTREAM_FROUDE_MIN,
    RUNTIME_COORDINATE_MAX_CORRIDOR_EDGE_STEP_M,
    RUNTIME_GRID_DX_M,
    RUNTIME_FIRST_RAPID_CONTROL_STATION_M,
    RUNTIME_LAUNCH_STATION_M,
    RUNTIME_MINIMUM_SAFE_LAUNCH_APRON_M,
    RUNTIME_PRESENTATION_SAMPLE_SPACING_M,
    SCENARIO_RELATIVE,
    build_runtime_coordinate_map,
    build_rapid_map_digitization,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_supplied_reference_sources_and_digitized_rapid_order_are_locked():
    assert _sha256(REPO_ROOT / "zambezi_batoka_heightmap.png") == HEIGHT_IMAGE_SHA256
    assert _sha256(REPO_ROOT / "victoria-falls-rapids-map.pdf") == RAPID_MAP_SHA256
    digitization = build_rapid_map_digitization(REPO_ROOT)
    assert digitization["rapid_count"] == 25
    assert [rapid["rapid_number"] for rapid in digitization["rapids"]] == [
        str(number) for number in range(1, 26)
    ]
    assert digitization["rapids"][0]["pdf_label"] == "The Wall"
    assert digitization["rapids"][-1]["pdf_label"] == "Rapid 25"
    assert digitization["rapids"][0]["station_m"] == 0.0
    assert digitization["rapids"][-1]["station_m"] == 27358.848
    increments = np.diff([rapid["station_m"] for rapid in digitization["rapids"]])
    assert increments.min() > 0.0
    assert increments.max() / increments.min() > 4.0
    assert all(
        not rapid["production_authoritative"] for rapid in digitization["rapids"]
    )


def test_committed_reference_bundle_is_self_consistent_and_not_physics_authority():
    root = REPO_ROOT / OUTPUT_RELATIVE
    manifest = _load(root / "source_and_conversion_manifest.json")
    assert manifest["production_promoted"] is False
    assert manifest["terrain_authority"]["policy"].startswith("Copernicus DEM remains")
    assert manifest["height_conversion"]["overlay_rejected_fraction"] > 0.1
    assert manifest["height_conversion"]["overlay_rejected_fraction"] < 0.4

    artifacts = manifest["artifacts"]
    for artifact in artifacts.values():
        path = REPO_ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]

    heightfield_path = REPO_ROOT / artifacts["heightfield_16bit"]["path"]
    with Image.open(heightfield_path) as heightfield:
        assert heightfield.size == REFERENCE_HEIGHTFIELD_SIZE
        values = np.asarray(heightfield)
    assert values.dtype in (np.dtype("uint16"), np.dtype("int32"))
    assert int(values.max()) - int(values.min()) > 50000

    mesh = artifacts["morphology_mesh"]
    assert mesh["grid_size"] == list(REFERENCE_MESH_SIZE)
    assert mesh["vertex_count"] == REFERENCE_MESH_SIZE[0] * REFERENCE_MESH_SIZE[1]
    assert mesh["triangle_count"] == (
        (REFERENCE_MESH_SIZE[0] - 1) * (REFERENCE_MESH_SIZE[1] - 1) * 2
    )
    assert mesh["physics_authority"] is False
    assert mesh["collision_authority"] is False


def test_zambezi_scenario_and_named_rapid_markers_use_pdf_relative_stationing():
    scenario = _load(REPO_ROOT / SCENARIO_RELATIVE)
    assert scenario["rapid_count"] == 25
    assert scenario["production_promoted"] is False
    assert scenario["gameplay"]["runnable"] is True
    assert scenario["gameplay"]["portfolio_role"] == "runnable_river"
    assert scenario["gameplay"]["runnable_tier"] == "reference_free_run"
    assert scenario["gameplay"]["runtime_coordinate_map"] == (
        COORDINATE_MAP_RELATIVE.as_posix()
    )
    assert scenario["gameplay"]["runtime_cooked_fields"] == (
        COOKED_FIELDS_RELATIVE.as_posix()
    )
    assert scenario["rapids"][8]["mandatory_commercial_portage"] is True
    assert (
        sum(rapid["mandatory_commercial_portage"] for rapid in scenario["rapids"]) == 1
    )
    assert scenario["route_variants"][0]["start_rapid"] == "1"
    assert scenario["route_variants"][0]["end_rapid"] == "25"
    assert {source["source_id"] for source in scenario["route_evidence"]} == {
        "zambezi_whitewater_guidebook",
        "zambezi_shearwater_operator_guide",
        "zambezi_victoria_falls_guide",
    }
    assert (
        scenario["route_variants"][1]["source_id"]
        == "zambezi_shearwater_operator_guide"
    )
    assert scenario["route_variants"][2]["source_id"] == "zambezi_victoria_falls_guide"
    assert len(scenario["acceptance_gates"]) >= 5

    player_catalog = _load(
        REPO_ROOT / "unreal/Content/RaftSim/UI/river_selection_catalog.json"
    )
    assert player_catalog["source_model"] == (
        "physics/data/real_world/player_selection_model.json"
    )
    player_entry = next(
        river
        for river in player_catalog["sections"]
        if river["river_id"] == "zambezi_batoka_gorge"
    )
    assert player_entry["frontend_scenario_id"] == "zambezi_reference_run"
    assert player_entry["portfolio_role"] == "runnable_river"
    assert player_entry["runnable"] is True
    assert player_entry["runnable_tier"] == "reference_free_run"
    runtime_acceptance = player_entry["runtime_acceptance"]
    assert runtime_acceptance["result"] == "pass"
    assert runtime_acceptance["safe_launch_apron"] == (
        "raftsim.zambezi.safe_launch_apron.v1"
    )
    assert runtime_acceptance["initial_settle_upright"] is True
    assert runtime_acceptance["all_forward_upright"] is True
    assert runtime_acceptance["attached_crew_count"] == 5
    assert runtime_acceptance["swimmer_count"] == 0

    source_model = _load(REPO_ROOT / player_catalog["source_model"])
    source_entry = next(
        river
        for region in source_model["regions"]
        for river in region["rivers"]
        if river["river_id"] == "zambezi_batoka_gorge"
    )
    assert source_entry["portfolio_role"] == "runnable_river"
    assert source_entry["runnable"] is True
    assert source_entry["runnable_tier"] == "reference_free_run"
    source_section = source_entry["sections"][0]
    assert source_section["scenario_id"] == "zambezi_reference_run"
    assert source_section["map_package"] == player_entry["map_package"]
    assert source_section["flow_bands"][0]["runnable"] is True

    catalog = _load(REPO_ROOT / CATALOG_RELATIVE)
    generated = build_editor_markers(catalog, REPO_ROOT)
    zambezi = next(
        river
        for river in generated["rivers"]
        if river["river_id"] == "zambezi_batoka_gorge"
    )
    assert len(zambezi["markers"]) == 25
    assert all(
        marker["stationing"]["station_kind"]
        == "stylized_map_relative_spacing_scaled_to_published_run_length"
        for marker in zambezi["markers"]
    )
    assert [marker["stationing"]["station_m"] for marker in zambezi["markers"]] == [
        rapid["station_m"] for rapid in scenario["rapids"]
    ]


def test_zambezi_runtime_coordinate_map_and_procedural_water_are_runnable():
    scenario = _load(REPO_ROOT / SCENARIO_RELATIVE)
    coordinate_map = _load(REPO_ROOT / COORDINATE_MAP_RELATIVE)
    assert coordinate_map == build_runtime_coordinate_map(REPO_ROOT)
    assert coordinate_map["schema"] == "raftsim.curved_river_coordinate_map.v1"
    assert coordinate_map["station_domain_m"][0] == 0.0
    assert 29900.0 <= coordinate_map["station_domain_m"][1] <= 30100.0
    assert len(coordinate_map["points"]) > 5000
    assert coordinate_map["maximum_runtime_corridor_edge_step_m"] <= (
        RUNTIME_COORDINATE_MAX_CORRIDOR_EDGE_STEP_M
    )

    cooked_root = REPO_ROOT / COOKED_FIELDS_RELATIVE
    manifest = _load(cooked_root / "manifest.json")
    assert manifest["schema"] == "raftsim.cooked_flow_fields.v1"
    assert manifest["production_promoted"] is False
    assert manifest["bands"][0]["band_id"] == "normal_big_water"
    assert manifest["bands"][0]["convergence"]["converged"] is False
    assert manifest["generator"].endswith("feature_tagged_hydraulic_seed.v3")
    assert manifest["grid"]["dx_m"] == RUNTIME_GRID_DX_M == 5.0
    assert manifest["procedural_infill"]["authority"].startswith(
        "gameplay_reference_only"
    )
    arrays = manifest["bands"][0]["arrays"]
    loaded = {}
    for name, metadata in arrays.items():
        path = cooked_root / metadata["file"]
        assert _sha256(path) == metadata["sha256"]
        loaded[name] = np.load(path, allow_pickle=False)
        assert list(loaded[name].shape) == metadata["shape"]
    assert loaded["wet_mask"].dtype == np.uint8
    assert loaded["wet_mask"].mean() > 0.4
    assert np.isfinite(loaded["bed"]).all()
    assert np.isfinite(loaded["h"]).all()
    assert float(loaded["h"].max()) > 3.0
    assert float(loaded["u"].max()) > 3.0
    assert float(loaded["h"].max()) < 5.0
    assert float(np.hypot(loaded["u"], loaded["v"]).max()) < 8.0

    contract = manifest["procedural_infill"]["hydraulic_transition_contract"]
    assert contract["schema"] == ("raftsim.zambezi.procedural_hydraulic_transitions.v1")
    assert contract["runtime_station_resolution_m"] == 5.0
    assert contract["presentation_sample_spacing_m"] == (
        RUNTIME_PRESENTATION_SAMPLE_SPACING_M
    )
    assert contract["upstream_froude_minimum"] == (RUNTIME_BREAKING_UPSTREAM_FROUDE_MIN)
    assert contract["tailwater_froude_maximum"] == (
        RUNTIME_BREAKING_DOWNSTREAM_FROUDE_MAX
    )
    assert contract["rapid_transition_count"] == 25
    assert contract["all_rapid_transitions_detected"] is True
    assert [row["rapid_number"] for row in contract["transitions"]] == [
        str(number) for number in range(1, 26)
    ]
    assert all(not row["production_authoritative"] for row in contract["transitions"])
    assert all(
        row["upstream_froude"] >= RUNTIME_BREAKING_UPSTREAM_FROUDE_MIN
        and row["tailwater_froude"] <= RUNTIME_BREAKING_DOWNSTREAM_FROUDE_MAX
        for row in contract["transitions"]
    )
    rapid_9 = contract["transitions"][8]
    assert rapid_9["mandatory_commercial_portage"] is True
    assert contract["rapid_9_policy"].startswith("hazard_visualization_only")

    launch_apron = manifest["procedural_infill"]["safe_launch_apron"]
    assert launch_apron["schema"] == "raftsim.zambezi.safe_launch_apron.v1"
    assert launch_apron["raft_spawn_station_m"] == RUNTIME_LAUNCH_STATION_M
    assert launch_apron["first_rapid_control_station_m"] == (
        RUNTIME_FIRST_RAPID_CONTROL_STATION_M
    )
    assert launch_apron["safe_subcritical_clearance_m"] >= (
        RUNTIME_MINIMUM_SAFE_LAUNCH_APRON_M
    )
    assert launch_apron["maximum_centerline_froude_before_approach"] <= (
        RUNTIME_BREAKING_DOWNSTREAM_FROUDE_MAX
    )
    assert launch_apron["production_authoritative"] is False
    assert scenario["gameplay"]["safe_launch_apron"] == launch_apron
    assert contract["transitions"][0]["control_station_m"] == (
        RUNTIME_FIRST_RAPID_CONTROL_STATION_M
    )

    center_row = loaded["h"].shape[0] // 2
    station_m = np.arange(loaded["h"].shape[1]) * RUNTIME_GRID_DX_M
    center_h = loaded["h"][center_row]
    center_u = loaded["u"][center_row]
    center_v = loaded["v"][center_row]
    launch_start_index = int(RUNTIME_LAUNCH_STATION_M / RUNTIME_GRID_DX_M)
    launch_end_index = int(
        launch_apron["first_rapid_approach_start_station_m"] / RUNTIME_GRID_DX_M
    )
    launch_froude = np.hypot(
        center_u[launch_start_index:launch_end_index],
        center_v[launch_start_index:launch_end_index],
    ) / np.sqrt(
        9.80665 * np.maximum(center_h[launch_start_index:launch_end_index], 1.0e-6)
    )
    assert float(launch_froude.max()) <= RUNTIME_BREAKING_DOWNSTREAM_FROUDE_MAX
    for row in contract["transitions"]:
        control_station_m = float(row["control_station_m"])
        sampled_station_m = np.arange(
            max(0.0, control_station_m - 15.0),
            control_station_m + 25.0 + 0.5 * RUNTIME_PRESENTATION_SAMPLE_SPACING_M,
            RUNTIME_PRESENTATION_SAMPLE_SPACING_M,
        )
        sampled_h = np.interp(sampled_station_m, station_m, center_h)
        sampled_speed = np.hypot(
            np.interp(sampled_station_m, station_m, center_u),
            np.interp(sampled_station_m, station_m, center_v),
        )
        sampled_froude = sampled_speed / np.sqrt(
            9.80665 * np.maximum(sampled_h, 1.0e-6)
        )
        assert np.any(
            (sampled_froude[:-1] >= RUNTIME_BREAKING_UPSTREAM_FROUDE_MIN)
            & (sampled_froude[1:] <= RUNTIME_BREAKING_DOWNSTREAM_FROUDE_MAX)
        )


def test_zambezi_reference_map_is_in_the_shipping_cook_and_regeneration_contracts():
    map_package = "/Game/RaftSim/Maps/L_Zambezi"
    promoted_map = REPO_ROOT / "unreal/Content/RaftSim/Maps/L_Zambezi.umap"
    assert promoted_map.is_file()
    assert promoted_map.stat().st_size > 1_000_000
    default_game = (REPO_ROOT / "unreal/Config/DefaultGame.ini").read_text(
        encoding="utf-8"
    )
    assert f'+MapsToCook=(FilePath="{map_package}")' in default_game

    frontend_source = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimUI/Private/"
        "RaftSimVerticalSliceFrontend.cpp"
    ).read_text(encoding="utf-8")
    assert 'TEXT("zambezi_reference_run")' in frontend_source
    assert 'TEXT("Zambezi: Boiling Pot to Mukuni Beach")' in frontend_source
    assert 'TEXT("Runnable Reference Free Run:' in frontend_source
    assert 'TEXT("/Game/RaftSim/Maps/L_Zambezi")' in frontend_source

    module_header = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Public/RaftSimEditorModule.h"
    ).read_text(encoding="utf-8")
    module_cpp = (
        REPO_ROOT
        / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/RaftSimEditorModule.cpp"
    ).read_text(encoding="utf-8")
    automation_cpp = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Commands/"
        "RaftSimEditorEnvironmentAutomation.cpp"
    ).read_text(encoding="utf-8")
    assert "LandscapeImportCandidateRiverFilter" in module_header
    assert "RaftSimLandscapeImportCandidateRiverId=" in module_cpp
    assert "LandscapeImportCandidateRiverFilter" in automation_cpp

    for relative in ("unreal/Scripts/package_mac.sh", "unreal/Scripts/package_win.ps1"):
        packaging_script = (REPO_ROOT / relative).read_text(encoding="utf-8")
        assert "L_Zambezi.umap" in packaging_script
        assert "RaftSimCreateLandscapeImportCandidateMaps" in packaging_script
        assert "RaftSimLandscapeImportCandidateRiverId=zambezi_batoka_gorge" in (
            packaging_script
        )


def test_unreal_candidate_binds_the_zambezi_scenario_and_builds_editor_markers():
    internal = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorEnvironmentInternal.h"
    ).read_text(encoding="utf-8")
    catalog_cpp = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorEnvironmentCatalog.cpp"
    ).read_text(encoding="utf-8")
    build_cpp = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/"
        "RaftSimEditorLandscapeBuild.cpp"
    ).read_text(encoding="utf-8")
    geometry_cpp = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/"
        "RaftSimEditorLandscapeGeometry.cpp"
    ).read_text(encoding="utf-8")
    director_cpp = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Rivers/"
        "RaftSimEditorZambeziDirector.cpp"
    ).read_text(encoding="utf-8")
    foliage_cpp = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Landscape/"
        "RaftSimEditorLandscapeFoliage.cpp"
    ).read_text(encoding="utf-8")
    lighting_cpp = (
        REPO_ROOT / "unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/Environment/"
        "RaftSimEditorNearFieldAndLighting.cpp"
    ).read_text(encoding="utf-8")
    assert "ScenarioRelativePath" in internal
    assert SCENARIO_RELATIVE.as_posix() in catalog_cpp
    assert "AddLandscapeCandidateScenarioMarkers" in build_cpp
    assert "AddLandscapeCandidateRunnableGameplay" in build_cpp
    assert "RaftSim_ZambeziRapid_" in geometry_cpp
    assert "RaftSim_Zambezi_PlayerRaft" in geometry_cpp
    assert "bRecenterHydraulicCrux = false" in geometry_cpp
    assert "RaftSimGlobalRiverStationAuthority" in geometry_cpp
    assert "RaftSimSafeLaunchApron" in geometry_cpp
    assert "ApplyZambeziBatokaVisualTerrainTreatment" in build_cpp
    assert "AddZambeziAdaptiveNearFieldTerrain" in build_cpp
    assert "RaftSimZambeziAdaptiveNearFieldTerrainV1" in geometry_cpp
    assert "RaftSimSourceConditionedTerrain" in geometry_cpp
    assert "RaftSimProtectedDryShoreline" in geometry_cpp
    assert "RaftSimNearFieldSelfShadowSuppressed" in geometry_cpp
    assert (
        "LoadOrCreatePhysicalSourceTerrainRenderMaterial(Candidate, true, true)"
        in build_cpp
    )
    assert "RaftSimProceduralVisualMorphology" in director_cpp
    assert "RaftSimNonCollisionRenderSurface" in director_cpp
    assert "ShorelineDryBufferCm = 2800.0f" in director_cpp
    assert "NearBankMorphologyReachBeyondWaterCm = 14800.0f" in director_cpp
    assert "NearBankRoundedSlopeMaskStart = 0.055f" in director_cpp
    assert "MorphologyOffsetClampCm = 280.0f" in director_cpp
    assert "ClosestCenterlinePoint" in director_cpp
    assert "SegmentLengthSquared" in director_cpp
    assert "RaftSimBatokaOrganicMorphologyV15" in director_cpp
    assert "RaftSimBatokaHeightAwareFacetReconstructionV15" in director_cpp
    assert "RaftSimProtectedShorelineBuffer" in director_cpp
    assert "MorphologyStats.NearBankModifiedVertexCount <= 0" in build_cpp
    assert "MorphologyStats.MinimumModifiedCenterlineDistanceCm + 0.5f" in build_cpp
    assert "CreateZambeziOpaqueVegetationAssets" in foliage_cpp
    assert "M_RaftSim_Zambezi_OpaqueVegetation" in foliage_cpp
    assert "Material->BlendMode = BLEND_Opaque" in foliage_cpp
    assert "Material->TwoSided = false" in foliage_cpp
    assert "AmbientOcclusion->R = 1.0f" in foliage_cpp
    assert "ShadowFloor->R = 0.09f" in foliage_cpp
    assert "FLinearColor(0.085f, 0.135f, 0.034f, 1.0f)" in foliage_cpp
    assert "RaftSimOpaqueVolumetricVegetation" in foliage_cpp
    assert "RaftSimProceduralVegetationFallback" in foliage_cpp
    assert "RaftSimSlopeScreenedPlacement" in foliage_cpp
    assert "GetLandscapeSlopeDegrees" in foliage_cpp
    assert "ZambeziEvidenceBankMosaicInstanceCount = 1200" in foliage_cpp
    assert "ZambeziOrganicBankMosaic" in foliage_cpp
    assert "RaftSimCameraVisibleBankCover" in foliage_cpp
    assert "InstancesPerLongitudinalLane" in foliage_cpp
    assert "ZambeziEvidenceWoodyInstanceCount = 240" in foliage_cpp
    assert "ZambeziEvidenceWoodySlopeCeilingDegrees = 24.0f" in foliage_cpp
    assert "ZambeziCameraRiparianTree" in foliage_cpp
    assert "ZambeziCameraUmbrellaTree" in foliage_cpp
    assert "ZambeziCameraThornScrub" in foliage_cpp
    assert "RaftSimCameraVisibleWoodyEcology" in foliage_cpp
    assert "RaftSimOrganicWoodyBankLayer" in foliage_cpp
    assert "RaftSimWoodySlopeCeiling24Degrees" in foliage_cpp
    assert "ZambeziRunnableLaunchBankCoverInstanceCount = 1800" in foliage_cpp
    assert "ZambeziRunnableLaunchWoodyInstanceCount = 192" in foliage_cpp
    assert "RaftSimZambeziAtmosphereV1" in lighting_cpp
    assert "RaftSimAtmosphereSunLight" in lighting_cpp
    assert "RaftSimSourceAwareDrySeasonSky" in lighting_cpp
    assert "RaftSimVolumetricGorgeHaze" in lighting_cpp
    assert "InstancesPerWoodyLane" in foliage_cpp
    assert "CandidateIndex < 40" in foliage_cpp
    assert "BestSlopeDegrees > ZambeziEvidenceWoodySlopeCeilingDegrees" in foliage_cpp

    validation = _load(
        REPO_ROOT
        / "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
        "zambezi_reference_scenario_map_validation.json"
    )
    assert validation["passed"] is True
    assert validation["scenario_marker_count"] == 25
    assert validation["rapid_numbers"] == list(range(1, 26))
    assert validation["mandatory_portage_actor"] == (
        "RaftSim_ZambeziRapid_9_Commercial_Suicide"
    )
    assert validation["runnable"]["player_raft_count"] == 1
    assert validation["runnable"]["water_config_count"] == 1
    assert validation["runnable"]["game_mode"].endswith("RaftSimVerticalSliceGameMode")
    assert validation["visual_terrain"]["authority"] == (
        "source_conditioned_plus_bounded_procedural_render_only"
    )
    assert validation["visual_terrain"]["conditioned_tile_count"] == 4
    assert all(
        "BatokaV12_WorldAligned" in tile["material"]
        for tile in validation["visual_terrain"]["tiles"]
    )
    assert all(
        "NO_COLLISION" in tile["collision_enabled"]
        for tile in validation["visual_terrain"]["tiles"]
    )
    assert validation["schema"].endswith(".v13")
    assert validation["runtime_hydraulics"]["preserves_global_river_stations"] is True
    assert validation["runtime_hydraulics"]["rapid_count"] == 25
    assert validation["runtime_hydraulics"]["rapid_9_policy"].startswith(
        "hazard_visualization_only"
    )
    assert validation["runtime_hydraulics"]["safe_launch_apron_tagged"] is True
    assert validation["visual_terrain"]["morphology_contract"] == (
        "v15_organic_basalt_with_100m_polyline_shoreline_protection_"
        "full_strength_by_220m_and_central_difference_grid_normals_"
        "plus_height_aware_source_facet_reconstruction"
    )
    assert validation["visual_terrain"]["active_water_half_width_m"] == 72.0
    assert validation["visual_terrain"]["protected_shoreline_radius_m"] == 100.0
    assert validation["visual_terrain"]["minimum_dry_bank_buffer_m"] == 26.56
    assert validation["visual_terrain"]["full_strength_morphology_radius_m"] == 220.0
    assert (
        validation["visual_terrain"]["maximum_visual_treatment_vertical_offset_m"]
        == 2.8
    )
    assert all(
        "RaftSimBatokaOrganicMorphologyV15" in tile["tags"]
        and "RaftSimBatokaHeightAwareFacetReconstructionV15" in tile["tags"]
        and "RaftSimProtectedShorelineBuffer" in tile["tags"]
        for tile in validation["visual_terrain"]["tiles"]
    )
    adaptive = validation["visual_terrain"]["adaptive_near_field"]
    assert adaptive["actor_count"] == 2
    assert adaptive["station_window_m"] == [0.0, 1000.0]
    assert adaptive["grid_spacing_m"] == 5.0
    assert adaptive["maximum_dry_shoreline_infill_m"] == 1.8
    assert adaptive["maximum_procedural_refinement_m"] == 0.96
    assert all(
        "NO_COLLISION" in actor["collision_enabled"]
        and actor["cast_shadow"] is False
        and "RaftSimSourceConditionedTerrain" in actor["tags"]
        and "RaftSimProtectedDryShoreline" in actor["tags"]
        and "RaftSimNearFieldSelfShadowSuppressed" in actor["tags"]
        for actor in adaptive["actors"]
    )
    assert validation["lighting"]["atmosphere_actor_count"] == 4
    atmosphere_tags = {
        tag
        for actor in validation["lighting"]["atmosphere_actors"]
        for tag in actor["tags"]
    }
    assert {
        "RaftSimAtmosphereSunLight",
        "RaftSimCapturedGorgeSkyFill",
        "RaftSimSourceAwareDrySeasonSky",
        "RaftSimVolumetricGorgeHaze",
    } <= atmosphere_tags
    assert validation["water_surface"]["component_count"] == 1
    assert validation["water_surface"]["shading_model_contract"] == ("SingleLayerWater")
    assert validation["vegetation"]["component_count"] == 12
    assert validation["vegetation"]["instance_count"] == 8927
    assert validation["vegetation"]["camera_visible_bank_cover_component_count"] == 1
    assert validation["vegetation"]["camera_visible_bank_cover_instance_count"] == 1200
    assert validation["vegetation"]["camera_visible_woody_component_count"] == 3
    assert validation["vegetation"]["camera_visible_woody_instance_count"] == 232
    assert validation["vegetation"]["camera_visible_woody_target_instance_count"] == 240
    assert validation["vegetation"]["camera_visible_woody_slope_rejection_count"] == 8
    assert (
        validation["vegetation"]["camera_visible_woody_slope_ceiling_degrees"] == 24.0
    )
    assert validation["vegetation"]["legacy_zambezi_pve_actor_count"] == 0
    assert validation["vegetation"]["runnable_launch_bank_cover_component_count"] == 1
    assert validation["vegetation"]["runnable_launch_bank_cover_instance_count"] == 1721
    assert (
        validation["vegetation"]["runnable_launch_bank_cover_target_instance_count"]
        == 1800
    )
    assert validation["vegetation"]["runnable_launch_woody_component_count"] == 3
    assert validation["vegetation"]["runnable_launch_woody_instance_count"] == 174
    assert (
        validation["vegetation"]["runnable_launch_woody_target_instance_count"] == 192
    )
    assert sorted(
        component["instance_count"]
        for component in validation["vegetation"]["components"]
        if "RaftSimRunnableLaunchWoodyEcology" in component["tags"]
    ) == [43, 44, 87]
    assert sorted(
        component["instance_count"]
        for component in validation["vegetation"]["components"]
        if "RaftSimRunnableLaunchBankEcologyV1" not in component["tags"]
    ) == [57, 58, 117, 700, 1200, 1400, 1400, 2100]
    assert all(
        "M_RaftSim_Zambezi_OpaqueVegetation" in component["material"]
        for component in validation["vegetation"]["components"]
    )
    assert all(
        "NO_COLLISION" in component["collision_enabled"]
        for component in validation["vegetation"]["components"]
    )
    mosaic = next(
        component
        for component in validation["vegetation"]["components"]
        if "ZambeziOrganicBankMosaic" in component["actor_label"]
    )
    assert "RaftSimCameraVisibleBankCover" in mosaic["tags"]
    assert "RaftSimOrganicBankMosaic" in mosaic["tags"]
    assert "SavannaGroundCover_A_OpaqueV1" in mosaic["static_mesh"]
    woody = [
        component
        for component in validation["vegetation"]["components"]
        if "RaftSimCameraVisibleWoodyEcology" in component["tags"]
    ]
    assert len(woody) == 3
    assert sorted(component["instance_count"] for component in woody) == [
        57,
        58,
        117,
    ]
    assert all(
        "RaftSimOrganicWoodyBankLayer" in component["tags"] for component in woody
    )
    assert all(
        "RaftSimWoodySlopeCeiling24Degrees" in component["tags"] for component in woody
    )
