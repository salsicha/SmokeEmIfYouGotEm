"""Read-only inventory of the normal South Fork scene before reconstruction.

No assets, maps, or profiles are saved. The report identifies the exact actor
and runtime configuration migration surface, including partition ownership.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
LEVEL = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
OUTPUT = ROOT/'unreal/Saved/RaftSimValidation/south-fork-normal-integration-inventory-v3-20260912.json'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def encode(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, unreal.Object):
        return value.get_path_name()
    if isinstance(value, unreal.Vector):
        return [value.x, value.y, value.z]
    if isinstance(value, unreal.Vector2D):
        return [value.x, value.y]
    if isinstance(value, unreal.Rotator):
        return [value.pitch, value.yaw, value.roll]
    return str(value)


def main():
    protected = [ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap',
                 ROOT/'unreal/Saved/SaveGames/RaftSimVerticalSlice.sav']
    before = {str(p.relative_to(ROOT)): digest(p) for p in protected}
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level(LEVEL)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name().split('.')[0] == LEVEL
    # get_all_level_actors sees only loaded actors. Partition descriptors are
    # the on-disk inventory, including terrain/vegetation cells not loaded at
    # the put-in. Do not mistake their absence in memory for absent terrain.
    descriptors = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    assert descriptors is not None, 'Partition descriptor inventory unavailable'
    descriptor_rows = []
    for desc in descriptors:
        package = str(desc.actor_package)
        assert package.startswith('/Game/')
        package_file = ROOT/'unreal/Content'/(package.removeprefix('/Game/')+'.uasset')
        assert package_file.is_file(), package
        descriptor_rows.append(dict(name=str(desc.name), label=str(desc.label),
            actor_class=desc.native_class.get_name(), package=package,
            package_sha256=digest(package_file), spatially_loaded=desc.is_spatially_loaded,
            editor_only=desc.actor_is_editor_only,
            bounds=[encode(desc.bounds.min), encode(desc.bounds.max)]))
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    properties = {
        'RaftSimRiverWaterConfig': '''cooked_fields_dir coordinate_map_path streaming_manifest_path
            flow_band window_center_m window_extent_m recenter_hydraulic_crux enable_moving_window_streaming
            moving_window_station_extent_m moving_window_lateral_extent_m moving_window_advance_m
            map_provides_terrain live_solver_owns_runtime_rendering enable_live_solver_volume_core
            live_volume_core_material_override live_presentation_standing_wave_scale
            live_presentation_hydraulic_relief_scale enable_live_raft_local_fluid_heightfield
            enable_live_presentation_surface_smoothing enable_live_rapid_surface_refinement
            live_rapid_surface_subdivision''',
        'RaftSimWaterSurfaceActor': '''water_material fixed_curved_grid fixed_curved_grid_center_station_meters
            fixed_cartesian_grid_center_north_meters curved_grid_length_meters curved_grid_width_meters
            curved_grid_edge_blend_meters vertex_spacing_meters''',
        'RaftSimRunManager': 'progress_coordinate_map_path start_station_m finish_station_m scenario_id',
    }
    rows = []
    for actor in actors:
        kind = actor.get_class().get_name()
        row = dict(name=actor.get_name(), label=actor.get_actor_label(), actor_class=kind,
                   path=actor.get_path_name(), location=encode(actor.get_actor_location()),
                   rotation=encode(actor.get_actor_rotation()), scale=encode(actor.get_actor_scale3d()),
                   tags=list(map(str, actor.tags)))
        row['configuration'] = {name: encode(actor.get_editor_property(name))
                                for name in properties.get(kind, '').split()}
        if isinstance(actor, unreal.StaticMeshActor):
            component = actor.static_mesh_component
            mesh = component.static_mesh
            row['mesh'] = mesh.get_path_name() if mesh else None
            row['materials'] = [material.get_path_name() if material else None
                                for material in (component.get_material(i)
                                for i in range(component.get_num_materials()))]
            row['collision_profile'] = str(component.get_collision_profile_name())
        rows.append(row)
    report = dict(level=LEVEL, actor_count=len(rows),
                  actor_classes=dict(Counter(row['actor_class'] for row in rows)),
                  descriptor_count=len(descriptor_rows),
                  descriptor_classes=dict(Counter(row['actor_class'] for row in descriptor_rows)),
                  descriptors=descriptor_rows,
                  game_mode=encode(world.get_world_settings().get_editor_property('default_game_mode')),
                  actors=rows, protected_files=before, saved_nothing=True,
                  reconstruction_integrated=False)
    for path in protected:
        assert digest(path) == before[str(path.relative_to(ROOT))]
    OUTPUT.write_text(json.dumps(report, indent=2)+'\n')
    unreal.log(f'Normal South Fork read-only inventory: {OUTPUT}')


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
