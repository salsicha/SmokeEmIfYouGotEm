"""Install verified reconstruction into the existing South Fork scenario.

Requires -RaftSimAssembleNormalSouthFork. Exact old packages are archived first;
all combined collision/launch checks run before saving. No source asset edits,
profile writes, new scenario, or automatic overwrite of a previous assembly.
"""
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import zipfile

import unreal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'physics/scripts'))
from prepare_south_fork_scene_assembly import prepare

MANIFEST = ROOT/'tmp/south-fork-full-scene-assembly-600s-v4-20260912.json'
REPORT = ROOT/'unreal/Saved/RaftSimValidation/south-fork-normal-assembly-v1-20260912.json'
BACKUP = ROOT/'unreal/Saved/RaftSimValidation/south-fork-pre-reconstruction-20260912.zip'
REPLACE_CLASSES = {'StaticMeshActor', 'RaftSimRockObstacleActor', 'Actor', 'SphereReflectionCapture'}


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def package_file(package):
    assert package.startswith('/Game/')
    return ROOT/'unreal/Content'/(package.removeprefix('/Game/')+'.uasset')


def vector(value):
    return [value.x, value.y, value.z]


def main():
    assert 'RaftSimAssembleNormalSouthFork' in unreal.SystemLibrary.get_command_line()
    assert not REPORT.exists(), 'Inspect prior result; never repeat a scene mutation blindly'
    manifest = read(MANIFEST)
    inventory = read(ROOT/manifest['map_inventory'])
    # Re-run the full file/geometry/datum/source-state preflight immediately
    # before this map operation, not merely trust a previous summary.
    actual = prepare((ROOT/manifest['runtime_streaming_manifest']).parent,
                     ROOT/manifest['map_inventory'])
    assert actual == manifest
    assert shutil.disk_usage(ROOT).free > 768*1024**2, 'Preserve cook/output headroom'
    files = {Path(name): digest for name, digest in inventory['protected_files'].items()}
    for desc in inventory['descriptors']:
        files[package_file(desc['package']).relative_to(ROOT)] = desc['package_sha256']
    if not BACKUP.exists():
        with zipfile.ZipFile(BACKUP, 'x', zipfile.ZIP_DEFLATED) as archive:
            for path, digest in files.items():
                assert sha(ROOT/path) == digest
                archive.write(ROOT/path, path.as_posix())
    with zipfile.ZipFile(BACKUP) as archive:
        for path, digest in files.items():
            assert hashlib.sha256(archive.read(path.as_posix())).hexdigest() == digest

    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level(manifest['target_level'])
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name().split('.')[0] == manifest['target_level']
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    descriptors = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    assert len(descriptors) == inventory['descriptor_count']
    descriptor_by_name = {str(desc.name): desc for desc in descriptors}
    actors = {actor.get_name(): actor for actor in subsystem.get_all_level_actors()}
    for desc in inventory['descriptors']:
        assert desc['name'] in descriptor_by_name
        assert descriptor_by_name[desc['name']].native_class.get_name() == desc['actor_class']

    def one(kind):
        matches = [actor for actor in actors.values() if actor.get_class().get_name() == kind]
        assert len(matches) == 1, (kind, len(matches))
        return matches[0]

    config, raft, start = one('RaftSimRiverWaterConfig'), one('RaftSimRaftActor'), one('PlayerStart')
    contracts = read(ROOT/manifest['session_contracts'])
    catalog = {str(row.scenario_id): row for row in unreal.RaftSimProgressionLibrary.get_scenario_catalog()}
    for row in contracts['sessions']:
        item = catalog[row['id']]
        assert abs(item.start_station_m-row['start_m']) < .002
        assert abs(item.finish_station_m-row['finish_m']) < .002
        assert str(item.level_name) == manifest['target_level']
    assert 'troublemaker_challenge' not in catalog

    # Sample the real native runtime before touching the old scene. Python
    # only chooses an admissible initial crop; normal play independently uses
    # the shared native launch/checkpoint selector and validates wetness again.
    route = unreal.RaftSimWaterRuntimeAdapter()
    assert route.configure_river_coordinate_map(manifest['route_coordinate_map'])
    position = route.river_to_world_position(unreal.Vector2D(120., 0.), 220.)
    ahead = route.river_to_world_position(unreal.Vector2D(121., 0.), 220.)
    assert isinstance(position, unreal.Vector) and isinstance(ahead, unreal.Vector)
    stream = read(ROOT/manifest['runtime_streaming_manifest'])
    px, py = position.x/100., -position.y/100.
    candidates = []
    for window in stream['windows']:
        for xmin, ymin, xmax, ymax in window['valid_live_center_bounds_m']:
            cx, cy = min(max(px, xmin), xmax), min(max(py, ymin), ymax)
            if max(abs(cx-px), abs(cy-py)) <= 104.:
                candidates.append(((cx-px)**2+(cy-py)**2, window['cooked_fields_manifest'], cx, cy))
    assert candidates
    _, fields_manifest, cx, cy = min(candidates)
    water = unreal.RaftSimWaterRuntimeAdapter()
    runtime = unreal.RaftSimWaterRuntimeConfig()
    runtime.require_accepted_report_manifest = False
    runtime.enable_deterministic_capture = False
    water.configure(runtime)
    assert water.configure_river_coordinate_map(manifest['hydraulic_coordinate_map'])
    fields = fields_manifest.rsplit('/', 1)[0]
    assert water.configure_moving_river_window(fields, 'median_runnable',
        unreal.Vector2D(cx, cy), unreal.Vector2D(*stream['live_window_extent_m']), stream['roughness_manning'])
    sample = water.sample_water_at_world_position(position)
    # Python returns None on the native false result; the public sample has
    # bWet but no separate bValid field.
    assert sample is not None and sample.wet, 'Initial real source point must be wet'
    position.z = sample.surface_height_meters*100.+40.
    rotation = unreal.Rotator(pitch=0., yaw=math.degrees(math.atan2(ahead.y-position.y, ahead.x-position.x)), roll=0.)

    removed = []
    for desc in inventory['descriptors']:
        kind = desc['actor_class']
        if kind in REPLACE_CLASSES or kind.endswith('ReflectionCapture'):
            # Loading every obsolete water LOD at once starts simultaneous
            # multi-gigabyte distance-field builds. Retire saved actors one
            # at a time; their exact original packages are already archived.
            guid = descriptor_by_name[desc['name']].guid
            if desc['name'] not in actors:
                unreal.WorldPartitionBlueprintLibrary.load_actors([guid])
                actor = next(actor for actor in subsystem.get_all_level_actors() if actor.get_name() == desc['name'])
            else:
                actor = actors.pop(desc['name'])
            assert actor.get_class().get_name() == kind
            removed.append(dict(name=desc['name'], label=desc['label'], package=desc['package'], actor_class=kind))
            assert subsystem.destroy_actor(actor)
            unreal.WorldPartitionBlueprintLibrary.unload_actors([guid])
            if len(removed) % 8 == 0:
                unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
                unreal.SystemLibrary.collect_garbage()
    assert len(removed) == 308, 'Unexpected legacy replacement scope'
    material = unreal.load_asset(manifest['terrain_actors'][0]['material_override'])
    assert material
    placed, probes = [], []
    exports = {}
    for index, row in enumerate(manifest['terrain_actors']):
        mesh = unreal.load_asset(row['asset'])
        assert mesh and mesh.get_num_triangles(0) == row['expected_triangle_count']
        actor = subsystem.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*row['translation_cm']))
        actor.set_actor_label('SouthFork_'+row['role']+'_'+row['asset'].rsplit('/', 1)[-1])
        actor.set_actor_scale3d(unreal.Vector(*row['scale']))
        assert max(abs(a-b) for a, b in zip(vector(actor.get_actor_location()), row['translation_cm'])) < .001
        actor.tags = [unreal.Name('RaftSimPhysicalGround'), unreal.Name('RaftSimSouthForkReconstruction20260912')]
        component = actor.static_mesh_component
        component.set_static_mesh(mesh)
        component.set_material(0, material)
        component.set_collision_profile_name('BlockAll')
        component.set_mobility(unreal.ComponentMobility.STATIC)
        export = exports.setdefault(row['export_manifest'], read(ROOT/row['export_manifest']))
        if row['role'] in ('coarse_terrain', 'captured_context'):
            tile = next(tile for tile in export['tiles'] if tile['asset_name'] == row['asset'].rsplit('/', 1)[-1])
            local_probes = tile['local_engine_collision_probes_cm']
        elif row['role'] == 'retained_rapid':
            # This export predates geographic reflection: its probes are in
            # the original +Y actor frame. The geographic-stage audit contains
            # the correctly reflected probes, including triangle interiors.
            geographic = read(ROOT/'docs/reconstruction-review-2026-09-07/geographic-scene/staging.json')
            assert geographic['source_geometry_sha256'] == export['source_geometry_sha256']
            assert geographic['terrain_actor_scale'] == row['scale']
            local_probes = [probe['position_cm'] for probe in geographic['collision_probes']]
            expected = {(probe['position_cm'][0], -probe['position_cm'][1], probe['position_cm'][2])
                        for probe in export['collision_probes_cm']}
            assert expected.issubset(set(map(tuple, local_probes)))
        else:
            seam = read(ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/composite_terrain/engine_seam_probes.json')
            local_probes = seam['local_rapid_engine_cm']
        for point in local_probes:
            probes.append((row['role'], unreal.Vector(*point)+unreal.Vector(*row['translation_cm'])))
        placed.append(dict(name=actor.get_name(), asset=row['asset'], role=row['role'],
            translation_cm=vector(actor.get_actor_location()), scale=vector(actor.get_actor_scale3d()),
            triangle_count=mesh.get_num_triangles(0)))
        if index % 50 == 0:
            unreal.log(f'Normal South Fork terrain placement {index+1}/443')

    config_values = dict(cooked_fields_dir=fields, coordinate_map_path=manifest['hydraulic_coordinate_map'],
        streaming_manifest_path=manifest['runtime_streaming_manifest'], flow_band=unreal.Name('median_runnable'),
        window_center_m=unreal.Vector2D(cx, cy), window_extent_m=224., recenter_hydraulic_crux=False,
        enable_moving_window_streaming=True, moving_window_station_extent_m=224., moving_window_lateral_extent_m=224.,
        moving_window_advance_m=80., map_provides_terrain=True, live_solver_owns_runtime_rendering=True,
        enable_live_solver_volume_core=True, enable_live_shared_breaking_relief=True,
        live_presentation_standing_wave_scale=0., live_presentation_hydraulic_relief_scale=1.,
        enable_live_rapid_surface_refinement=False, live_rapid_surface_subdivision=1,
        enable_live_raft_local_fluid_heightfield=True,
        live_volume_core_material_override=unreal.load_asset('/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/M_RaftSim_SouthForkRaftTransmissionWaterV4'))
    assert config_values['live_volume_core_material_override']
    for name, value in config_values.items():
        config.set_editor_property(name, value)
    for actor in (raft, start):
        actor.modify()
        actor.root_component.modify()
        actor.root_component.set_editor_property('relative_location', position)
        actor.root_component.set_editor_property('relative_rotation', rotation)
        actor.set_editor_property('is_spatially_loaded', False)
    config.set_editor_property('is_spatially_loaded', False)
    manager = subsystem.spawn_actor_from_class(unreal.load_class(None, '/Script/SmokeEmIfYouGotEm.RaftSimRunManager'), position)
    manager.set_editor_property('is_spatially_loaded', False)
    manager.set_editor_property('progress_coordinate_map_path', manifest['route_coordinate_map'])
    manager.set_editor_property('scenario_id', unreal.Name('south_fork_full_descent'))
    manager.set_editor_property('start_station_m', 120.)
    manager.set_editor_property('finish_station_m', 33280.)
    # Carrier vertices are already world-frame coordinates; its actor must
    # remain identity so the route origin is never applied a second time.
    surface = subsystem.spawn_actor_from_class(unreal.RaftSimWaterSurfaceActor, unreal.Vector(0., 0., 0.))
    surface.set_editor_property('is_spatially_loaded', False)
    surface.set_editor_property('vertex_spacing_meters', 1.)
    surface.set_editor_property('river_presentation_subdivision', 1)
    surface.set_editor_property('curved_grid_length_meters', 224.)
    surface.set_editor_property('curved_grid_width_meters', 224.)
    surface.set_editor_property('fixed_curved_grid', False)
    world.get_world_settings().set_editor_property('default_game_mode',
        unreal.load_class(None, '/Script/SmokeEmIfYouGotEm.RaftSimVerticalSliceGameMode'))

    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    ignore = [actor for actor in subsystem.get_all_level_actors() if not isinstance(actor, unreal.StaticMeshActor)]
    errors = {}
    for role, query in probes:
        hit = unreal.SystemLibrary.line_trace_single(world, query+unreal.Vector(0, 0, 1000),
            query-unreal.Vector(0, 0, 1000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            False, ignore, unreal.DrawDebugTrace.NONE, False)
        values = hit.to_tuple() if hit else None
        assert values and values[0], ('Missing combined collision', role, vector(query))
        error = abs(values[5].z-query.z)
        assert error < .1, ('Combined collision differs from source', role, vector(query), error)
        errors.setdefault(role, []).append(error)
    # No profile or source mesh/material writes are part of this operation.
    for row in manifest['terrain_actors']:
        assert sha(package_file(row['asset'])) == row['asset_sha256']
    save_path = ROOT/'unreal/Saved/SaveGames/RaftSimVerticalSlice.sav'
    save_sha = inventory['protected_files'][str(save_path.relative_to(ROOT))]
    assert sha(save_path) == save_sha
    assert levels.save_current_level()
    assert unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, False)
    assert sha(save_path) == save_sha
    after = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    result = dict(schema='raftsim.south_fork.normal_scene_assembly.v1', level=manifest['target_level'],
        assembly_manifest=str(MANIFEST.relative_to(ROOT)), assembly_sha256=sha(MANIFEST),
        recoverable_original_packages=str(BACKUP.relative_to(ROOT)), backup_sha256=sha(BACKUP),
        removed_legacy_actors=removed, terrain_actors=placed, descriptor_count=len(after),
        collision={role: dict(count=len(values), maximum_height_error_cm=max(values)) for role, values in errors.items()},
        raft_start_cm=vector(position), raft_yaw_degrees=rotation.yaw,
        route_coordinate_map=manifest['route_coordinate_map'], streaming_manifest=manifest['runtime_streaming_manifest'],
        source_time_seconds=manifest['source_time_seconds'], source_assets_unchanged=True, profile_unchanged=True,
        map_sha256=sha(ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'),
        normal_map_saved=True, no_rapid_scenario=True, settled_hydraulics=False,
        actual_game_traversal_verified=False, full_scene_accepted=False,
        external_packages=[dict(package=str(desc.actor_package), sha256=sha(package_file(str(desc.actor_package)))) for desc in after])
    REPORT.write_text(json.dumps(result, indent=2)+'\n')
    unreal.log(f'Normal South Fork reconstruction saved: {REPORT}')


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
