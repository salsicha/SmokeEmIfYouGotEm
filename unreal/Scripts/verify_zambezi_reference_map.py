"""Verify the generated Zambezi reference-run map and gameplay bootstrap."""

from __future__ import annotations

import json
from pathlib import Path
import traceback

import unreal

MAP_PACKAGE = "/Game/RaftSim/Maps/L_Zambezi"
REPORT_RELATIVE = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_reference_scenario_map_validation.json"
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    report_path = repo_root / REPORT_RELATIVE
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report: dict[str, object] = {
        "schema": "raftsim.unreal.zambezi_reference_scenario_map_validation.v20",
        "map_package": MAP_PACKAGE,
        "passed": False,
    }
    try:
        world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PACKAGE)
        if not world:
            raise RuntimeError(f"Could not load {MAP_PACKAGE}")
        subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        if not subsystem:
            raise RuntimeError("EditorActorSubsystem is unavailable")
        actors = list(subsystem.get_all_level_actors())
        sun_actors = [
            actor
            for actor in actors
            if actor.get_actor_label() == "RaftSim_Sun_LumenPreview"
            and actor.get_class().get_name() == "DirectionalLight"
        ]
        sun_rows = []
        for actor in sun_actors:
            rotation = actor.get_actor_rotation()
            sun_rows.append(
                {
                    "actor_label": actor.get_actor_label(),
                    "tags": sorted(str(tag) for tag in actor.tags),
                    "pitch_degrees": round(rotation.pitch, 3),
                    "yaw_degrees": round(rotation.yaw, 3),
                }
            )
        rejected_high_density_bank_actors = [
            actor.get_actor_label()
            for actor in actors
            if "RaftSimZambeziHighDensityBank" in {str(tag) for tag in actor.tags}
        ]
        markers = [
            actor
            for actor in actors
            if actor.get_actor_label().startswith("RaftSim_ZambeziRapid_")
        ]
        marker_rows = []
        for actor in markers:
            tags = sorted(str(tag) for tag in actor.tags)
            marker_rows.append(
                {
                    "actor_label": actor.get_actor_label(),
                    "tags": tags,
                    "location_cm": [
                        round(actor.get_actor_location().x, 3),
                        round(actor.get_actor_location().y, 3),
                        round(actor.get_actor_location().z, 3),
                    ],
                }
            )
        portages = [
            row for row in marker_rows if "RaftSimMandatoryPortage" in row["tags"]
        ]
        player_rafts = [
            actor
            for actor in actors
            if actor.get_actor_label() == "RaftSim_Zambezi_PlayerRaft"
            and actor.get_class().get_name() == "RaftSimRaftActor"
        ]
        water_configs = [
            actor
            for actor in actors
            if actor.get_actor_label() == "RaftSim_Zambezi_RuntimeWaterConfig"
            and actor.get_class().get_name() == "RaftSimRiverWaterConfig"
        ]
        player_starts = [
            actor
            for actor in actors
            if actor.get_actor_label() == "RaftSim_GuideSeat_PlayerStart"
            and actor.get_class().get_name() == "PlayerStart"
        ]
        terrain_actors = [
            actor
            for actor in actors
            if "RaftSimProceduralVisualMorphology" in {str(tag) for tag in actor.tags}
        ]
        terrain_rows = []
        for actor in terrain_actors:
            components = actor.get_components_by_class(unreal.ProceduralMeshComponent)
            mesh = components[0] if components else None
            material = mesh.get_material(0) if mesh else None
            terrain_rows.append(
                {
                    "actor_label": actor.get_actor_label(),
                    "tags": sorted(str(tag) for tag in actor.tags),
                    "procedural_mesh_count": len(components),
                    "material": material.get_path_name() if material else None,
                    "collision_enabled": (
                        str(mesh.get_collision_enabled()) if mesh else None
                    ),
                    "cast_shadow": (
                        bool(mesh.get_editor_property("cast_shadow")) if mesh else None
                    ),
                }
            )
        adaptive_near_field_terrain_actors = [
            actor
            for actor in actors
            if "RaftSimZambeziAdaptiveNearFieldTerrainV1"
            in {str(tag) for tag in actor.tags}
        ]
        adaptive_near_field_terrain_rows = []
        for actor in adaptive_near_field_terrain_actors:
            components = actor.get_components_by_class(unreal.ProceduralMeshComponent)
            mesh = components[0] if components else None
            material = mesh.get_material(0) if mesh else None
            adaptive_near_field_terrain_rows.append(
                {
                    "actor_label": actor.get_actor_label(),
                    "tags": sorted(str(tag) for tag in actor.tags),
                    "procedural_mesh_count": len(components),
                    "material": material.get_path_name() if material else None,
                    "collision_enabled": (
                        str(mesh.get_collision_enabled()) if mesh else None
                    ),
                    "cast_shadow": (
                        bool(mesh.get_editor_property("cast_shadow")) if mesh else None
                    ),
                }
            )
        atmosphere_actors = [
            actor
            for actor in actors
            if "RaftSimZambeziAtmosphereV1" in {str(tag) for tag in actor.tags}
        ]
        atmosphere_rows = [
            {
                "actor_label": actor.get_actor_label(),
                "class": actor.get_class().get_name(),
                "tags": sorted(str(tag) for tag in actor.tags),
            }
            for actor in atmosphere_actors
        ]
        water_surface_actors = [
            actor
            for actor in actors
            if actor.get_actor_label()
            == "RaftSim_PhysicalCorridorRiverRibbon_zambezi_batoka_gorge"
        ]
        water_surface_rows = []
        for actor in water_surface_actors:
            components = actor.get_components_by_class(unreal.ProceduralMeshComponent)
            mesh = components[0] if components else None
            material = mesh.get_material(0) if mesh else None
            parent = (
                material.get_editor_property("parent")
                if material and isinstance(material, unreal.MaterialInstanceConstant)
                else None
            )
            water_surface_rows.append(
                {
                    "actor_label": actor.get_actor_label(),
                    "tags": sorted(str(tag) for tag in actor.tags),
                    "procedural_mesh_count": len(components),
                    "material": material.get_path_name() if material else None,
                    "parent_material": parent.get_path_name() if parent else None,
                    "collision_enabled": (
                        str(mesh.get_collision_enabled()) if mesh else None
                    ),
                }
            )
        vegetation_actors = [
            actor
            for actor in actors
            if "RaftSimZambeziOpaqueVegetation" in {str(tag) for tag in actor.tags}
        ]
        vegetation_rows = []
        for actor in vegetation_actors:
            components = actor.get_components_by_class(
                unreal.HierarchicalInstancedStaticMeshComponent
            )
            component = components[0] if components else None
            material = component.get_material(0) if component else None
            static_mesh = (
                component.get_editor_property("static_mesh") if component else None
            )
            vegetation_rows.append(
                {
                    "actor_label": actor.get_actor_label(),
                    "tags": sorted(str(tag) for tag in actor.tags),
                    "component_count": len(components),
                    "instance_count": (
                        component.get_instance_count() if component else 0
                    ),
                    "static_mesh": (
                        static_mesh.get_path_name() if static_mesh else None
                    ),
                    "material": material.get_path_name() if material else None,
                    "collision_enabled": (
                        str(component.get_collision_enabled()) if component else None
                    ),
                    "cast_shadow": (
                        bool(component.get_editor_property("cast_shadow"))
                        if component
                        else None
                    ),
                }
            )
        launch_talus_actors = [
            actor
            for actor in actors
            if "RaftSimRunnableLaunchTalusV1" in {str(tag) for tag in actor.tags}
        ]
        launch_talus_rows = []
        for actor in launch_talus_actors:
            components = actor.get_components_by_class(
                unreal.HierarchicalInstancedStaticMeshComponent
            )
            component = components[0] if components else None
            material = component.get_material(0) if component else None
            parent = (
                material.get_editor_property("parent")
                if material
                and isinstance(material, unreal.MaterialInstanceConstant)
                else None
            )
            static_mesh = (
                component.get_editor_property("static_mesh") if component else None
            )
            custom_data_values = (
                [
                    float(value)
                    for value in component.get_editor_property(
                        "per_instance_sm_custom_data"
                    )
                ]
                if component
                else []
            )
            launch_talus_rows.append(
                {
                    "actor_label": actor.get_actor_label(),
                    "tags": sorted(str(tag) for tag in actor.tags),
                    "component_count": len(components),
                    "instance_count": (
                        component.get_instance_count() if component else 0
                    ),
                    "static_mesh": (
                        static_mesh.get_path_name() if static_mesh else None
                    ),
                    "material": material.get_path_name() if material else None,
                    "parent_material": parent.get_path_name() if parent else None,
                    "collision_enabled": (
                        str(component.get_collision_enabled()) if component else None
                    ),
                    "cast_shadow": (
                        bool(component.get_editor_property("cast_shadow"))
                        if component
                        else None
                    ),
                    "num_custom_data_floats": (
                        int(component.get_editor_property("num_custom_data_floats"))
                        if component
                        else 0
                    ),
                    "custom_data_value_count": len(custom_data_values),
                    "conditioned_waterline_min_z_cm": (
                        round(min(custom_data_values), 3)
                        if custom_data_values
                        else None
                    ),
                    "conditioned_waterline_max_z_cm": (
                        round(max(custom_data_values), 3)
                        if custom_data_values
                        else None
                    ),
                }
            )
        legacy_zambezi_pve_actors = [
            actor.get_actor_label()
            for actor in actors
            if "zambezi_batoka_gorge" in actor.get_actor_label()
            and "LandscapeCandidate_PveWhole" in actor.get_actor_label()
        ]
        world_settings = world.get_world_settings()
        default_game_mode = (
            world_settings.get_editor_property("default_game_mode")
            if world_settings
            else None
        )
        game_mode_path = (
            default_game_mode.get_path_name() if default_game_mode else None
        )
        water_config = water_configs[0] if len(water_configs) == 1 else None
        water_config_tags = (
            sorted(str(tag) for tag in water_config.tags) if water_config else []
        )
        preserves_global_river_stations = bool(
            water_config
            and not water_config.get_editor_property("recenter_hydraulic_crux")
            and "RaftSimGlobalRiverStationAuthority" in water_config_tags
        )
        safe_launch_apron_tagged = bool(
            water_config and "RaftSimSafeLaunchApron" in water_config_tags
        )
        live_volume_material = (
            water_config.get_editor_property("live_volume_core_material_override")
            if water_config
            else None
        )
        live_flow_normal = (
            water_config.get_editor_property("live_water_flow_normal_texture")
            if water_config
            else None
        )
        live_foam_lace = (
            water_config.get_editor_property("live_water_foam_lace_texture")
            if water_config
            else None
        )
        solver_owned_water = bool(
            water_config
            and water_config.get_editor_property(
                "live_solver_owns_runtime_rendering"
            )
        )
        live_volume_core_enabled = bool(
            water_config
            and water_config.get_editor_property("enable_live_solver_volume_core")
        )
        rapid_numbers = []
        for row in marker_rows:
            suffix = str(row["actor_label"]).removeprefix("RaftSim_ZambeziRapid_")
            rapid_numbers.append(int(suffix.split("_", 1)[0]))
        report.update(
            {
                "actor_count": len(actors),
                "scenario_marker_count": len(markers),
                "rapid_numbers": sorted(rapid_numbers),
                "mandatory_portage_marker_count": len(portages),
                "mandatory_portage_actor": (
                    portages[0]["actor_label"] if portages else None
                ),
                "markers": sorted(marker_rows, key=lambda row: row["actor_label"]),
                "runnable": {
                    "player_raft_count": len(player_rafts),
                    "water_config_count": len(water_configs),
                    "player_start_count": len(player_starts),
                    "game_mode": game_mode_path,
                },
                "runtime_hydraulics": {
                    "authority": (
                        "feature_tagged_procedural_reference_only_not_validated_"
                        "real_world_hydraulics"
                    ),
                    "global_river_station_alignment": (
                        "preserved_no_hydraulic_crux_recentering"
                    ),
                    "preserves_global_river_stations": (
                        preserves_global_river_stations
                    ),
                    "water_config_tags": water_config_tags,
                    "rapid_count": 25,
                    "safe_launch_apron_tagged": safe_launch_apron_tagged,
                    "rapid_9_policy": (
                        "hazard_visualization_only_mandatory_commercial_portage_"
                        "not_a_runnable_line"
                    ),
                },
                "visual_terrain": {
                    "authority": "source_conditioned_plus_bounded_procedural_render_only",
                    "physics_and_collision_authority": "source_copernicus_landscape",
                    "morphology_contract": (
                        "v18_exposure_safe_organic_basalt_with_wet_bank_protection_and_"
                        "height_aware_upper_dry_scarp_infill_plus_central_"
                        "difference_grid_normals_and_source_facet_reconstruction"
                    ),
                    "active_water_half_width_m": 72.0,
                    "protected_shoreline_radius_m": 100.0,
                    "minimum_dry_bank_buffer_m": 26.56,
                    "full_strength_morphology_radius_m": 220.0,
                    "maximum_visual_treatment_vertical_offset_m": 4.4,
                    "maximum_source_facet_reconstruction_offset_m": 3.2,
                    "inside_protected_radius_reconstruction_minimum_height_"
                    "above_local_water_m": 6.0,
                    "conditioned_tile_count": len(terrain_rows),
                    "coarse_source_self_shadow_policy": (
                        "disabled_on_noncolliding_visual_tiles_only"
                    ),
                    "tiles": sorted(terrain_rows, key=lambda row: row["actor_label"]),
                    "adaptive_near_field": {
                        "authority": (
                            "source_conditioned_surface_with_bounded_"
                            "procedural_dry_shoreline_and_basalt_erosion_infill"
                        ),
                        "station_window_m": [0.0, 1000.0],
                        "grid_spacing_m": 5.0,
                        "maximum_lateral_extent_m": 600.0,
                        "active_water_half_width_m": 72.0,
                        "inner_dry_bank_buffer_m": 3.0,
                        "maximum_dry_shoreline_infill_m": 1.8,
                        "maximum_procedural_refinement_m": 0.96,
                        "minimum_rendered_dry_clearance_m": 0.295,
                        "wet_bank_contract": (
                            "conditioned_profile_vertex_red_render_only_"
                            "irregular_1.75m_to_3.25m_procedural_stain_ceiling"
                        ),
                        "wet_bank_authority": (
                            "procedural_presentation_only_no_measured_wet_bank_"
                            "collision_or_hydraulic_authority"
                        ),
                        "physics_and_collision_authority": (
                            "source_copernicus_landscape_only"
                        ),
                        "actor_count": len(adaptive_near_field_terrain_rows),
                        "actors": sorted(
                            adaptive_near_field_terrain_rows,
                            key=lambda row: row["actor_label"],
                        ),
                    },
                },
                "lighting": {
                    "authority": "presentation_only_no_physics_effect",
                    "source_facet_amplification_control": (
                        "zambezi_specific_gorge_aligned_exposure_safe_sun_v18"
                    ),
                    "required_pitch_degrees": -48.0,
                    "required_yaw_degrees": -90.0,
                    "directional_lights": sun_rows,
                    "atmosphere_contract": (
                        "zambezi_specific_sun_linked_dry_season_sky_"
                        "captured_gorge_fill_and_volumetric_haze"
                    ),
                    "atmosphere_actor_count": len(atmosphere_rows),
                    "atmosphere_actors": sorted(
                        atmosphere_rows, key=lambda row: row["actor_label"]
                    ),
                },
                "water_surface": {
                    "authority": (
                        "solver_wet_cell_geometry_with_render_only_transmitting_"
                        "optics_and_capture_only_static_editor_ribbon"
                    ),
                    "gameplay_shading_contract": "solver_owned_transmitting_volume_core",
                    "bank_edge_contract": (
                        "vertex_alpha_feathered_single_layer_water_volume_v2"
                    ),
                    "reflection_contract": (
                        "v18_rough_local_response_with_restrained_sky_floor_and_"
                        "no_calm_detail_overlay"
                    ),
                    "capture_shading_model_contract": "DefaultLit",
                    "capture_normal_motion_contract": "two_opposed_panned_atlas_layers",
                    "solver_owned_runtime_rendering": solver_owned_water,
                    "live_volume_core_enabled": live_volume_core_enabled,
                    "live_volume_material": (
                        live_volume_material.get_path_name()
                        if live_volume_material
                        else None
                    ),
                    "live_flow_normal": (
                        live_flow_normal.get_path_name() if live_flow_normal else None
                    ),
                    "live_foam_lace": (
                        live_foam_lace.get_path_name() if live_foam_lace else None
                    ),
                    "calm_detail_coverage": (
                        float(
                            water_config.get_editor_property(
                                "live_surface_calm_coverage"
                            )
                        )
                        if water_config
                        else None
                    ),
                    "active_detail_coverage": (
                        float(
                            water_config.get_editor_property(
                                "live_surface_active_coverage"
                            )
                        )
                        if water_config
                        else None
                    ),
                    "presentation_smoothing_enabled": bool(
                        water_config
                        and water_config.get_editor_property(
                            "enable_live_presentation_surface_smoothing"
                        )
                    ),
                    "presentation_smoothing_strength": (
                        float(
                            water_config.get_editor_property(
                                "live_presentation_surface_smoothing_strength"
                            )
                        )
                        if water_config
                        else None
                    ),
                    "bank_blend_m": (
                        float(
                            water_config.get_editor_property(
                                "live_surface_bank_blend_meters"
                            )
                        )
                        if water_config
                        else None
                    ),
                    "component_count": len(water_surface_rows),
                    "components": water_surface_rows,
                },
                "launch_talus": {
                    "authority": (
                        "presentation_only_generic_rock_analog_no_lithology_"
                        "collision_hydraulic_or_raft_force_authority"
                    ),
                    "asset_rights_status": (
                        "rights_reviewed_cc0_poly_haven_rock_moss_set_01_"
                        "six_variant_visual_analog"
                    ),
                    "material_contract": (
                        "zambezi_specific_project_owned_desaturated_mineral_"
                        "retone_v1_over_rights_reviewed_cc0_microstructure_"
                        "with_per_instance_conditioned_profile_waterline_"
                        "and_dry_scalar_fail_safe"
                    ),
                    "wet_band_width_m": 2.2,
                    "placement_contract": (
                        "deterministic_128_candidate_search_approximately_"
                        "118m_to_993m_downstream_with_full_route_clearance_"
                        "dry_height_and_hard_slope_gates"
                    ),
                    "target_instance_count": 360,
                    "instance_count": sum(
                        int(row["instance_count"]) for row in launch_talus_rows
                    ),
                    "rejected_placement_count": 360
                    - sum(int(row["instance_count"]) for row in launch_talus_rows),
                    "slope_ceiling_degrees": 48.0,
                    "target_height_range_m": [0.95, 5.20],
                    "component_count": len(launch_talus_rows),
                    "components": sorted(
                        launch_talus_rows, key=lambda row: row["actor_label"]
                    ),
                },
                "vegetation": {
                    "authority": "procedural_render_only_no_exact_species_claim",
                    "material_contract": "opaque_one_sided_vertex_color_no_alpha_cards",
                    "component_count": len(vegetation_rows),
                    "instance_count": sum(
                        int(row["instance_count"]) for row in vegetation_rows
                    ),
                    "legacy_zambezi_pve_actor_count": len(legacy_zambezi_pve_actors),
                    "legacy_zambezi_pve_actors": sorted(legacy_zambezi_pve_actors),
                    "components": sorted(
                        vegetation_rows, key=lambda row: row["actor_label"]
                    ),
                },
            }
        )
        vegetation_by_label = {
            row["actor_label"]: int(row["instance_count"]) for row in vegetation_rows
        }
        camera_visible_bank_cover_rows = [
            row
            for row in vegetation_rows
            if "RaftSimCameraVisibleBankCover" in row["tags"]
            and "RaftSimOrganicBankMosaic" in row["tags"]
        ]
        report["vegetation"]["camera_visible_bank_cover_component_count"] = len(
            camera_visible_bank_cover_rows
        )
        report["vegetation"]["camera_visible_bank_cover_instance_count"] = sum(
            int(row["instance_count"]) for row in camera_visible_bank_cover_rows
        )
        full_corridor_ground_cover_rows = [
            row
            for row in vegetation_rows
            if "ZambeziOpaqueGroundCover" in row["actor_label"]
        ]
        report["vegetation"][
            "ground_cover_shadow_policy"
        ] = "disabled_on_full_corridor_camera_mosaic_and_launch_cover"
        camera_visible_woody_rows = [
            row
            for row in vegetation_rows
            if "RaftSimCameraVisibleWoodyEcology" in row["tags"]
            and "RaftSimOrganicWoodyBankLayer" in row["tags"]
        ]
        report["vegetation"]["camera_visible_woody_component_count"] = len(
            camera_visible_woody_rows
        )
        report["vegetation"]["camera_visible_woody_instance_count"] = sum(
            int(row["instance_count"]) for row in camera_visible_woody_rows
        )
        report["vegetation"]["camera_visible_woody_target_instance_count"] = 240
        report["vegetation"]["camera_visible_woody_slope_rejection_count"] = 240 - int(
            report["vegetation"]["camera_visible_woody_instance_count"]
        )
        report["vegetation"]["camera_visible_woody_slope_ceiling_degrees"] = 24.0
        report["vegetation"][
            "camera_visible_woody_placement_contract"
        ] = "deterministic_40_candidate_visible_bank_search_with_hard_slope_ceiling"
        runnable_launch_bank_cover_rows = [
            row
            for row in vegetation_rows
            if "RaftSimRunnableLaunchBankEcologyV1" in row["tags"]
            and "RaftSimRunnableLaunchBankCover" in row["tags"]
        ]
        report["vegetation"]["runnable_launch_bank_cover_component_count"] = len(
            runnable_launch_bank_cover_rows
        )
        report["vegetation"]["runnable_launch_bank_cover_instance_count"] = sum(
            int(row["instance_count"]) for row in runnable_launch_bank_cover_rows
        )
        report["vegetation"]["runnable_launch_bank_cover_target_instance_count"] = 7200
        report["vegetation"]["runnable_launch_bank_cover_rejection_count"] = 7200 - int(
            report["vegetation"]["runnable_launch_bank_cover_instance_count"]
        )
        report["vegetation"]["runnable_launch_bank_cover_slope_ceiling_degrees"] = 42.0
        report["vegetation"][
            "runnable_launch_bank_cover_shadow_policy"
        ] = "disabled_on_noncolliding_ground_cover_only"
        report["vegetation"]["runnable_launch_bank_cover_placement_contract"] = (
            "v18_lower_energy_short_cover_two_morphology_deterministic_96_"
            "candidate_target_offset_mosaic_"
            "approximately_55m_to_955m_downstream_with_12m_to_180m_dry_"
            "bank_spread_12km_cull_range_full_route_clearance_dry_height_"
            "and_hard_slope_gates"
        )
        runnable_launch_woody_rows = [
            row
            for row in vegetation_rows
            if "RaftSimRunnableLaunchBankEcologyV1" in row["tags"]
            and "RaftSimRunnableLaunchWoodyEcology" in row["tags"]
        ]
        report["vegetation"]["runnable_launch_woody_component_count"] = len(
            runnable_launch_woody_rows
        )
        report["vegetation"]["runnable_launch_woody_instance_count"] = sum(
            int(row["instance_count"]) for row in runnable_launch_woody_rows
        )
        report["vegetation"]["runnable_launch_woody_target_instance_count"] = 640
        report["vegetation"]["runnable_launch_woody_rejection_count"] = 640 - int(
            report["vegetation"]["runnable_launch_woody_instance_count"]
        )
        report["vegetation"]["runnable_launch_woody_slope_ceiling_degrees"] = 34.0
        report["vegetation"][
            "runnable_launch_woody_shadow_policy"
        ] = "disabled_on_launch_window_only_to_prevent_camera_wall_streaks"
        report["vegetation"]["runnable_launch_woody_placement_contract"] = (
            "deterministic_160_candidate_target_offset_mosaic_approximately_"
            "155m_to_955m_downstream_with_35m_to_200m_dry_bank_spread_"
            "12km_cull_range_full_route_clearance_dry_height_and_hard_"
            "slope_gates"
        )
        passed = (
            len(markers) == 25
            and sorted(rapid_numbers) == list(range(1, 26))
            and len(portages) == 1
            and "_9_Commercial_Suicide" in str(portages[0]["actor_label"])
            and all("RaftSimScenarioMarker" in row["tags"] for row in marker_rows)
            and all("RaftSimZambeziRun" in row["tags"] for row in marker_rows)
            and len(player_rafts) == 1
            and len(water_configs) == 1
            and preserves_global_river_stations
            and safe_launch_apron_tagged
            and len(player_starts) == 1
            and str(game_mode_path).endswith("RaftSimVerticalSliceGameMode")
            and len(sun_rows) == 1
            and abs(float(sun_rows[0]["pitch_degrees"]) + 48.0) <= 0.01
            and abs(float(sun_rows[0]["yaw_degrees"]) + 90.0) <= 0.01
            and "RaftSimAtmosphereSunLight" in sun_rows[0]["tags"]
            and len(atmosphere_rows) == 4
            and sum(
                "RaftSimAtmosphereSunLight" in row["tags"] for row in atmosphere_rows
            )
            == 1
            and sum(
                "RaftSimCapturedGorgeSkyFill" in row["tags"] for row in atmosphere_rows
            )
            == 1
            and sum(
                "RaftSimSourceAwareDrySeasonSky" in row["tags"]
                for row in atmosphere_rows
            )
            == 1
            and sum(
                "RaftSimVolumetricGorgeHaze" in row["tags"] for row in atmosphere_rows
            )
            == 1
            and not rejected_high_density_bank_actors
            and len(terrain_rows) == 4
            and all(row["procedural_mesh_count"] == 1 for row in terrain_rows)
            and all(
                "BatokaV12_WorldAligned" in str(row["material"]) for row in terrain_rows
            )
            and len(adaptive_near_field_terrain_rows) == 2
            and all(
                row["procedural_mesh_count"] == 1
                and "NO_COLLISION" in str(row["collision_enabled"])
                and not row["cast_shadow"]
                and row["material"]
                and "RaftSimSourceConditionedTerrain" in row["tags"]
                and "RaftSimProceduralInfill" in row["tags"]
                and "RaftSimProtectedDryShoreline" in row["tags"]
                and "RaftSimNonCollisionRenderSurface" in row["tags"]
                and "RaftSimNearFieldSelfShadowSuppressed" in row["tags"]
                and "RaftSimConditionedWaterlineWetBankV1" in row["tags"]
                and "RaftSimVertexRedWetBankMask" in row["tags"]
                and "RaftSimProceduralWetBankNoMeasuredAuthority" in row["tags"]
                for row in adaptive_near_field_terrain_rows
            )
            and all(
                "NO_COLLISION" in str(row["collision_enabled"]) for row in terrain_rows
            )
            and all(not row["cast_shadow"] for row in terrain_rows)
            and all(
                "RaftSimNonCollisionRenderSurface" in row["tags"]
                and "RaftSimBatokaWorldAlignedTerrain" in row["tags"]
                and "RaftSimBatokaOrganicMorphologyV17" in row["tags"]
                and "RaftSimBatokaHeightAwareFacetReconstructionV17" in row["tags"]
                and "RaftSimBatokaUpperDryScarpInfillV17" in row["tags"]
                and "RaftSimBatokaExposureSafeScarpV18" in row["tags"]
                and "RaftSimCoarseSourceSelfShadowSuppressed" in row["tags"]
                and "RaftSimProtectedShorelineBuffer" in row["tags"]
                for row in terrain_rows
            )
            and len(water_surface_rows) == 1
            and solver_owned_water
            and live_volume_core_enabled
            and live_volume_material is not None
            and "MI_RaftSim_ZambeziBatoka_LiveVolumeWaterV2"
            in live_volume_material.get_path_name()
            and live_flow_normal is not None
            and "T_RaftSim_ZambeziBatokaWaterV1_FlowNormal"
            in live_flow_normal.get_path_name()
            and live_foam_lace is not None
            and "T_RaftSim_ZambeziBatokaWaterV1_FoamLace"
            in live_foam_lace.get_path_name()
            and float(
                water_config.get_editor_property("live_surface_calm_coverage")
            ) <= 0.001
            and abs(
                float(
                    water_config.get_editor_property("live_surface_active_coverage")
                )
                - 0.06
            ) <= 0.001
            and abs(
                float(water_config.get_editor_property("live_surface_roughness"))
                - 0.66
            ) <= 0.001
            and abs(
                float(water_config.get_editor_property("live_surface_specular"))
                - 0.15
            ) <= 0.001
            and abs(
                float(
                    water_config.get_editor_property("live_sky_reflection_strength")
                )
                - 0.055
            ) <= 0.001
            and abs(
                float(water_config.get_editor_property("live_ripple_strength"))
                - 0.48
            ) <= 0.001
            and bool(
                water_config.get_editor_property(
                    "enable_live_presentation_surface_smoothing"
                )
            )
            and abs(
                float(
                    water_config.get_editor_property(
                        "live_presentation_surface_smoothing_strength"
                    )
                )
                - 0.62
            ) <= 0.001
            and abs(
                float(
                    water_config.get_editor_property(
                        "live_surface_bank_blend_meters"
                    )
                )
                - 7.5
            ) <= 0.001
            and "RaftSimZambeziTransmittingWaterV2" in water_config_tags
            and "RaftSimOpacityFeatheredVolumeEdgeV2" in water_config_tags
            and "RaftSimRestrainedSolarGlareV2" in water_config_tags
            and "RaftSimZambeziLocalizedReflectionWaterV18" in water_config_tags
            and water_surface_rows[0]["procedural_mesh_count"] == 1
            and "MI_RaftSim_Zambezi_PhysicalCorridorWaterCandidate"
            in str(water_surface_rows[0]["material"])
            and "M_RaftSim_Zambezi_DefaultLitWater"
            in str(water_surface_rows[0]["parent_material"])
            and "NO_COLLISION" in str(water_surface_rows[0]["collision_enabled"])
            and "RaftSimNonCollisionRenderSurface" in water_surface_rows[0]["tags"]
            and "RaftSimPhysicalCorridorWater" in water_surface_rows[0]["tags"]
            and "RaftSimZambeziDefaultLitWater" in water_surface_rows[0]["tags"]
            and "RaftSimSingleLayerWaterCaptureRejected"
            in water_surface_rows[0]["tags"]
            and "RaftSimMovingMultiScaleWaterNormals" in water_surface_rows[0]["tags"]
            and "RaftSimCaptureOnlyStaticWater" in water_surface_rows[0]["tags"]
            and "RaftSimLiveSolverWaterOwnsRuntimeRendering"
            in water_surface_rows[0]["tags"]
            and len(launch_talus_rows) == 6
            and sum(int(row["instance_count"]) for row in launch_talus_rows) == 360
            and all(row["component_count"] == 1 for row in launch_talus_rows)
            and all(row["cast_shadow"] for row in launch_talus_rows)
            and all(
                int(row["num_custom_data_floats"]) == 1
                and int(row["custom_data_value_count"])
                == int(row["instance_count"])
                and row["conditioned_waterline_min_z_cm"] is not None
                and float(row["conditioned_waterline_min_z_cm"]) > -1.0e6
                and row["conditioned_waterline_max_z_cm"] is not None
                and float(row["conditioned_waterline_max_z_cm"])
                >= float(row["conditioned_waterline_min_z_cm"])
                for row in launch_talus_rows
            )
            and all(
                "NO_COLLISION" in str(row["collision_enabled"])
                for row in launch_talus_rows
            )
            and all(
                "RockMossSet01" in str(row["static_mesh"])
                and "MI_RaftSim_Zambezi_BasaltTalusV1"
                in str(row["material"])
                and "M_RaftSim_RiverBoulder"
                in str(row["parent_material"])
                for row in launch_talus_rows
            )
            and all(
                "RaftSimRunnableLaunchTalusV1" in row["tags"]
                and "RaftSimZambeziBasaltAnalogMaterialV1" in row["tags"]
                and "RaftSimProjectOwnedMineralRetone" in row["tags"]
                and "RaftSimRightsReviewedCC0RockAnalog" in row["tags"]
                and "RaftSimProceduralGeologyFallback" in row["tags"]
                and "RaftSimGenericRockAnalogNoLithologyAuthority" in row["tags"]
                and "RaftSimSourceLandscapeGrounded" in row["tags"]
                and "RaftSimDryBankPlacement" in row["tags"]
                and "RaftSimSlopeScreenedPlacement" in row["tags"]
                and "RaftSimNonCollisionRenderSurface" in row["tags"]
                and "RaftSimPresentationOnlyNoHydraulicAuthority" in row["tags"]
                and "RaftSimConditionedWaterlineWetBankV1" in row["tags"]
                and "RaftSimPerInstanceConditionedWaterline" in row["tags"]
                and "RaftSimProceduralWetBankNoMeasuredAuthority" in row["tags"]
                for row in launch_talus_rows
            )
            and len(vegetation_rows) == 13
            and any(
                "ZambeziOpaqueRiparianTree" in label and count == 2100
                for label, count in vegetation_by_label.items()
            )
            and any(
                "ZambeziOpaqueUmbrellaTree" in label and count == 1400
                for label, count in vegetation_by_label.items()
            )
            and any(
                "ZambeziOpaqueThornScrub" in label and count == 1400
                for label, count in vegetation_by_label.items()
            )
            and any(
                "ZambeziOpaqueGroundCover" in label and count == 700
                for label, count in vegetation_by_label.items()
            )
            and any(
                "ZambeziOrganicBankMosaic" in label and count == 1200
                for label, count in vegetation_by_label.items()
            )
            and len(camera_visible_bank_cover_rows) == 1
            and int(camera_visible_bank_cover_rows[0]["instance_count"]) == 1200
            and not camera_visible_bank_cover_rows[0]["cast_shadow"]
            and len(full_corridor_ground_cover_rows) == 1
            and not full_corridor_ground_cover_rows[0]["cast_shadow"]
            and len(camera_visible_woody_rows) == 3
            and sum(int(row["instance_count"]) for row in camera_visible_woody_rows)
            == 232
            and all(row["cast_shadow"] for row in camera_visible_woody_rows)
            and any(
                "ZambeziCameraRiparianTree" in label and count == 58
                for label, count in vegetation_by_label.items()
            )
            and any(
                "ZambeziCameraUmbrellaTree" in label and count == 57
                for label, count in vegetation_by_label.items()
            )
            and any(
                "ZambeziCameraThornScrub" in label and count == 117
                for label, count in vegetation_by_label.items()
            )
            and all(
                "RaftSimWoodySlopeCeiling24Degrees" in row["tags"]
                for row in camera_visible_woody_rows
            )
            and len(runnable_launch_bank_cover_rows) == 2
            and sum(
                int(row["instance_count"])
                for row in runnable_launch_bank_cover_rows
            ) >= 4500
            and all(
                not row["cast_shadow"]
                and "RaftSimGroundCoverSelfShadowSuppressed" in row["tags"]
                and "RaftSimOrganicGroundCoverMorphologyV2" in row["tags"]
                and "RaftSimZambeziLowerEnergyLaunchEcologyV18" in row["tags"]
                for row in runnable_launch_bank_cover_rows
            )
            and len(runnable_launch_woody_rows) == 3
            and sum(int(row["instance_count"]) for row in runnable_launch_woody_rows)
            >= 560
            and all(not row["cast_shadow"] for row in runnable_launch_woody_rows)
            and all(
                "RaftSimWoodySlopeCeiling34Degrees" in row["tags"]
                and "RaftSimRunnableLaunchWoodyShadowSuppressed" in row["tags"]
                for row in runnable_launch_woody_rows
            )
            and not legacy_zambezi_pve_actors
            and all(row["component_count"] == 1 for row in vegetation_rows)
            and all(
                "M_RaftSim_Zambezi_OpaqueVegetation" in str(row["material"])
                for row in vegetation_rows
            )
            and all("OpaqueV" in str(row["static_mesh"]) for row in vegetation_rows)
            and all(
                "NO_COLLISION" in str(row["collision_enabled"])
                for row in vegetation_rows
            )
            and all(
                "RaftSimOpaqueVolumetricVegetation" in row["tags"]
                and "RaftSimNonCollisionRenderSurface" in row["tags"]
                and "RaftSimProceduralVegetationFallback" in row["tags"]
                and "RaftSimSlopeScreenedPlacement" in row["tags"]
                for row in vegetation_rows
            )
        )
        report["passed"] = passed
        if not passed:
            raise RuntimeError(
                "Generated Zambezi scenario marker contract did not pass"
            )
        unreal.log(
            f"Zambezi reference run validation passed with {len(markers)} markers, "
            f"{len(player_rafts)} raft, {len(water_configs)} runtime water config, "
            f"{len(terrain_rows)} conditioned visual-terrain tiles, "
            f"{len(adaptive_near_field_terrain_rows)} adaptive near-field banks, "
            f"{len(water_surface_rows)} capture-only Default Lit water ribbon plus "
            "one solver-owned transmitting gameplay core, and "
            f"{sum(int(row['instance_count']) for row in launch_talus_rows)} "
            "runnable-launch dry-bank rock analogs, plus "
            f"{sum(int(row['instance_count']) for row in vegetation_rows)} "
            "opaque vegetation instances, including 1200 camera-visible "
            "organic bank-cover, 232 camera-visible woody instances, "
            f"{sum(int(row['instance_count']) for row in runnable_launch_bank_cover_rows)} "
            "runnable-launch bank-cover instances, and "
            f"{sum(int(row['instance_count']) for row in runnable_launch_woody_rows)} "
            "runnable-launch woody instances"
        )
    except Exception as error:
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        unreal.log_error(report["traceback"])
    finally:
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        unreal.log(f"Zambezi scenario map validation report: {report_path}")
        unreal.SystemLibrary.quit_editor()


main()
