"""Read-only inventory before moving captured reconstruction into gameplay."""
import json
from pathlib import Path
import unreal

level = '/Game/RaftSim/Maps/Review/Geographic/SouthForkRegisteredRockPlayable'
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert levels.load_level(level)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert world.get_path_name().split('.')[0] == level
rows = []
for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    row = {'name': actor.get_name(), 'class': actor.get_class().get_name(),
           'location': str(actor.get_actor_location()), 'rotation': str(actor.get_actor_rotation()),
           'scale': str(actor.get_actor_scale3d()), 'tags': list(map(str, actor.tags))}
    if row['class'] == 'RaftSimRiverWaterConfig':
        names = ('cooked_fields_dir coordinate_map_path streaming_manifest_path flow_band '
                 'window_center_m window_extent_m recenter_hydraulic_crux enable_moving_window_streaming '
                 'map_provides_terrain live_solver_owns_runtime_rendering enable_live_solver_volume_core '
                 'live_volume_core_material_override live_presentation_standing_wave_scale '
                 'live_presentation_hydraulic_relief_scale enable_live_raft_local_fluid_heightfield '
                 'enable_live_presentation_surface_smoothing')
    elif row['class'] == 'RaftSimWaterSurfaceActor':
        names = ('water_material fixed_curved_grid fixed_curved_grid_center_station_meters '
                 'curved_grid_length_meters curved_grid_width_meters curved_grid_edge_blend_meters')
    else:
        names = ''
    for name in names.split():
        row[name] = str(actor.get_editor_property(name))
    if isinstance(actor, unreal.StaticMeshActor):
        component = actor.static_mesh_component
        row['mesh'] = component.static_mesh.get_path_name()
        row['materials'] = [component.get_material(i).get_path_name() for i in range(component.get_num_materials())]
    rows.append(row)
settings = world.get_world_settings()
result = {'level': level, 'game_mode': str(settings.get_editor_property('default_game_mode')), 'actors': rows}
output = Path(unreal.Paths.project_saved_dir()) / 'RaftSimValidation/southfork-playable-dependencies-20260912.json'
output.write_text(json.dumps(result, indent=2))
unreal.log(f'Captured playable dependencies: {output}')
