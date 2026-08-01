"""Verify the generated Zambezi reference-run map and gameplay bootstrap."""

from __future__ import annotations

import json
from pathlib import Path
import traceback

import unreal


MAP_PACKAGE = (
    "/Game/RaftSim/Maps/EnvironmentPreviews/LandscapeCandidates/"
    "L_ZambeziBatokaGorge_PhysicalCorridorCandidate"
)
REPORT_RELATIVE = Path(
    "docs/environment-captures/photoreal_river_previews/landscape_candidates/"
    "zambezi_reference_scenario_map_validation.json"
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    report_path = repo_root / REPORT_RELATIVE
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report: dict[str, object] = {
        "schema": "raftsim.unreal.zambezi_reference_scenario_map_validation.v11",
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
                    "pitch_degrees": round(rotation.pitch, 3),
                    "yaw_degrees": round(rotation.yaw, 3),
                }
            )
        rejected_high_density_bank_actors = [
            actor.get_actor_label()
            for actor in actors
            if "RaftSimZambeziHighDensityBank"
            in {str(tag) for tag in actor.tags}
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
        portages = [row for row in marker_rows if "RaftSimMandatoryPortage" in row["tags"]]
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
                    "collision_enabled": str(mesh.get_collision_enabled()) if mesh else None,
                    "cast_shadow": bool(
                        mesh.get_editor_property("cast_shadow")
                    ) if mesh else None,
                }
            )
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
            if "RaftSimZambeziOpaqueVegetation"
            in {str(tag) for tag in actor.tags}
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
            sorted(str(tag) for tag in water_config.tags)
            if water_config
            else []
        )
        preserves_global_river_stations = bool(
            water_config
            and not water_config.get_editor_property("recenter_hydraulic_crux")
            and "RaftSimGlobalRiverStationAuthority" in water_config_tags
        )
        safe_launch_apron_tagged = bool(
            water_config and "RaftSimSafeLaunchApron" in water_config_tags
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
                "mandatory_portage_actor": portages[0]["actor_label"] if portages else None,
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
                    "authority": "procedural_render_only",
                    "physics_and_collision_authority": "source_copernicus_landscape",
                    "morphology_contract": (
                        "v15_organic_basalt_with_100m_polyline_shoreline_"
                        "protection_full_strength_by_220m_and_central_"
                        "difference_grid_normals_plus_height_aware_source_"
                        "facet_reconstruction"
                    ),
                    "active_water_half_width_m": 72.0,
                    "protected_shoreline_radius_m": 100.0,
                    "minimum_dry_bank_buffer_m": 26.56,
                    "full_strength_morphology_radius_m": 220.0,
                    "maximum_visual_treatment_vertical_offset_m": 2.8,
                    "maximum_source_facet_reconstruction_offset_m": 3.2,
                    "inside_protected_radius_reconstruction_minimum_height_"
                    "above_local_water_m": 6.0,
                    "conditioned_tile_count": len(terrain_rows),
                    "coarse_source_self_shadow_policy": (
                        "disabled_on_noncolliding_visual_tiles_only"
                    ),
                    "tiles": sorted(terrain_rows, key=lambda row: row["actor_label"]),
                },
                "lighting": {
                    "authority": "presentation_only_no_physics_effect",
                    "source_facet_amplification_control": (
                        "zambezi_specific_gorge_aligned_sun"
                    ),
                    "required_pitch_degrees": -48.0,
                    "required_yaw_degrees": -90.0,
                    "directional_lights": sun_rows,
                },
                "water_surface": {
                    "authority": "render_only_source_aligned_physical_corridor",
                    "shading_model_contract": "SingleLayerWater",
                    "normal_motion_contract": "two_opposed_panned_atlas_layers",
                    "component_count": len(water_surface_rows),
                    "components": water_surface_rows,
                },
                "vegetation": {
                    "authority": "procedural_render_only_no_exact_species_claim",
                    "material_contract": "opaque_one_sided_vertex_color_no_alpha_cards",
                    "component_count": len(vegetation_rows),
                    "instance_count": sum(
                        int(row["instance_count"]) for row in vegetation_rows
                    ),
                    "legacy_zambezi_pve_actor_count": len(
                        legacy_zambezi_pve_actors
                    ),
                    "legacy_zambezi_pve_actors": sorted(
                        legacy_zambezi_pve_actors
                    ),
                    "components": sorted(
                        vegetation_rows, key=lambda row: row["actor_label"]
                    ),
                },
            }
        )
        vegetation_by_label = {
            row["actor_label"]: int(row["instance_count"])
            for row in vegetation_rows
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
            int(row["instance_count"])
            for row in camera_visible_bank_cover_rows
        )
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
            int(row["instance_count"])
            for row in camera_visible_woody_rows
        )
        report["vegetation"]["camera_visible_woody_target_instance_count"] = 240
        report["vegetation"]["camera_visible_woody_slope_rejection_count"] = (
            240
            - int(
                report["vegetation"][
                    "camera_visible_woody_instance_count"
                ]
            )
        )
        report["vegetation"]["camera_visible_woody_slope_ceiling_degrees"] = 24.0
        report["vegetation"]["camera_visible_woody_placement_contract"] = (
            "deterministic_40_candidate_visible_bank_search_with_hard_slope_ceiling"
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
            and not rejected_high_density_bank_actors
            and len(terrain_rows) == 4
            and all(row["procedural_mesh_count"] == 1 for row in terrain_rows)
            and all(
                "BatokaV12_WorldAligned" in str(row["material"])
                for row in terrain_rows
            )
            and all(
                "NO_COLLISION" in str(row["collision_enabled"])
                for row in terrain_rows
            )
            and all(not row["cast_shadow"] for row in terrain_rows)
            and all(
                "RaftSimNonCollisionRenderSurface" in row["tags"]
                and "RaftSimBatokaWorldAlignedTerrain" in row["tags"]
                and "RaftSimBatokaOrganicMorphologyV15" in row["tags"]
                and "RaftSimBatokaHeightAwareFacetReconstructionV15"
                in row["tags"]
                and "RaftSimCoarseSourceSelfShadowSuppressed" in row["tags"]
                and "RaftSimProtectedShorelineBuffer" in row["tags"]
                for row in terrain_rows
            )
            and len(water_surface_rows) == 1
            and water_surface_rows[0]["procedural_mesh_count"] == 1
            and "MI_RaftSim_Zambezi_PhysicalCorridorWaterCandidate"
            in str(water_surface_rows[0]["material"])
            and "M_RaftSim_Zambezi_SingleLayerWater"
            in str(water_surface_rows[0]["parent_material"])
            and "NO_COLLISION"
            in str(water_surface_rows[0]["collision_enabled"])
            and "RaftSimNonCollisionRenderSurface"
            in water_surface_rows[0]["tags"]
            and "RaftSimPhysicalCorridorWater"
            in water_surface_rows[0]["tags"]
            and "RaftSimZambeziSingleLayerWater"
            in water_surface_rows[0]["tags"]
            and "RaftSimMovingMultiScaleWaterNormals"
            in water_surface_rows[0]["tags"]
            and len(vegetation_rows) == 8
            and sum(int(row["instance_count"]) for row in vegetation_rows) == 7032
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
            and len(camera_visible_woody_rows) == 3
            and sum(
                int(row["instance_count"])
                for row in camera_visible_woody_rows
            )
            == 232
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
            and not legacy_zambezi_pve_actors
            and all(row["component_count"] == 1 for row in vegetation_rows)
            and all(
                "M_RaftSim_Zambezi_OpaqueVegetation" in str(row["material"])
                for row in vegetation_rows
            )
            and all(
                "OpaqueV1" in str(row["static_mesh"])
                for row in vegetation_rows
            )
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
            raise RuntimeError("Generated Zambezi scenario marker contract did not pass")
        unreal.log(
            f"Zambezi reference run validation passed with {len(markers)} markers, "
            f"{len(player_rafts)} raft, {len(water_configs)} runtime water config, "
            f"{len(terrain_rows)} conditioned visual-terrain tiles, "
            f"{len(water_surface_rows)} validated Single Layer Water ribbon, and "
            f"{sum(int(row['instance_count']) for row in vegetation_rows)} "
            "opaque vegetation instances, including 1200 camera-visible "
            "organic bank-cover and 232 camera-visible woody instances"
        )
    except Exception as error:
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        unreal.log_error(report["traceback"])
    finally:
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        unreal.log(f"Zambezi scenario map validation report: {report_path}")
        unreal.SystemLibrary.quit_editor()


main()
