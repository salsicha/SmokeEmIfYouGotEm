"""Install one verified, source-consistent terrain/rock/water revision normally.

Requires -RaftSimInstallSourceMatchedSouthFork plus explicit preflight/report
paths. Exact scene packages are archived before mutation. New production meshes
are duplicates with exact native collision sources, not reimports or overlays
of the old terrain. This incremental delivery is NOT physical/visual acceptance.
"""
import json
import os
from pathlib import Path
import sys
import zipfile

import unreal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'physics/scripts'))
from prepare_south_fork_joint_preview import Dependencies, asset_file, require
from package_runtime_bundle import sha

LEVEL = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
DEST = '/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SourceMatched20260917/'


def xyz(value):
    return [value.x, value.y, value.z]


def native(mesh, expected_hash, count):
    result = json.loads(unreal.RaftSimGroundSourceLibrary.audit_collision_source(mesh))
    require(result['available'] is True and result['allow_cpu_access'] is True and
            result['collision_lod'] == 0 and result['triangle_count'] == count and
            result['collision_source_sha256'] == expected_hash,
            'Duplicated mesh differs from native verified source')
    require(mesh.get_num_triangles(0) == count, 'Incomplete render fallback')
    return result


def main():
    require('-RaftSimInstallSourceMatchedSouthFork' in unreal.SystemLibrary.get_command_line(),
            'Explicit normal-scene installation required')
    preflight_path = (ROOT / os.environ['RAFTSIM_RECONSTRUCTION_LAUNCH_REPORT']).resolve()
    output = (ROOT / os.environ['RAFTSIM_RECONSTRUCTION_INSTALL_REPORT']).resolve()
    require(output.is_relative_to(ROOT / 'tmp') and not output.exists(), 'Fresh local installation receipt required')
    backup = output.with_suffix('.before.zip')
    require(not backup.exists(), 'Preserve previous transaction backup; do not blindly repeat')
    preflight = json.loads(preflight_path.read_text())
    require(preflight['schema'] == 'raftsim.south_fork_reconstruction_launch_preflight.v1' and
            preflight['passed'] is True and preflight['saved_assets'] is False and
            len(preflight['launches']) == 5 and
            all(not row['failures'] and row['solver_steps'] == 120 for row in preflight['launches']),
            'All five actual native launch checks required')
    deps = Dependencies(ROOT)
    descriptor = deps.read(ROOT / preflight['descriptor'], preflight['descriptor_sha256'])
    require(descriptor['target_level'] == LEVEL and descriptor['schema'] == 'raftsim.south_fork_joint_preview.v2',
            'Source-matched full-river descriptor required')
    for name, digest in descriptor['dependencies'].items():
        deps.add(ROOT / name, digest)
    collision = deps.read(ROOT / descriptor['collision_audit'])
    terrain = collision['terrain_replacement']
    stage = deps.read(ROOT / descriptor['render_stage'])
    require(collision['failures'] == [] and terrain['saved_mesh_verified'] is True and
            terrain['original_actor_reused'] is True and terrain['second_ground_actor_added'] is False,
            'Verified replacement rather than overlay required')
    for name, digest in preflight['protected_files'].items():
        deps.add(ROOT / name, digest)
    # Recoverable exact files, including the profile (which is never modified).
    with zipfile.ZipFile(backup, 'x', zipfile.ZIP_DEFLATED) as archive:
        for name in preflight['protected_files']:
            archive.write(ROOT / name, name)
    with zipfile.ZipFile(backup) as archive:
        import hashlib
        for name, digest in preflight['protected_files'].items():
            require(hashlib.sha256(archive.read(name)).hexdigest() == digest, 'Backup verification failed')

    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    require(levels.load_level(LEVEL), 'Normal scene load failed')
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    descriptors = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    before_desc = {str(row.name): row for row in descriptors}
    require(terrain['replacement_actor'] in before_desc, 'Original terrain actor missing')
    unreal.WorldPartitionBlueprintLibrary.load_actors([before_desc[terrain['replacement_actor']].guid])
    actors = {actor.get_name(): actor for actor in actors_api.get_all_level_actors()}
    original = actors[terrain['replacement_actor']]
    component = original.static_mesh_component
    require(component.static_mesh.get_path_name().split('.')[0] == terrain['original_mesh_asset'],
            'Normal terrain already changed')
    require(xyz(original.get_actor_location()) == descriptor['translation_cm'] and
            xyz(original.get_actor_scale3d()) == [1., -1., 1.], 'Original terrain transform changed')
    material = component.get_material(0)
    require(material.get_path_name() == descriptor['material_asset'], 'Original material changed')
    config, = [a for a in actors.values() if a.get_class().get_name() == 'RaftSimRiverWaterConfig']
    manager, = [a for a in actors.values() if a.get_class().get_name() == 'RaftSimRunManager']
    full, = [row for row in preflight['launches'] if row['scenario_id'] == 'south_fork_full_descent']
    require(float(manager.get_editor_property('start_station_m')) == 120. and
            float(manager.get_editor_property('finish_station_m')) == 33280., 'Full descent contract changed')
    require(len([d for d in descriptors if d.native_class.get_name() == 'RaftSimWaterSurfaceActor']) == 1,
            'Exactly one existing water carrier required')
    for prop in ('map_provides_terrain', 'live_solver_owns_runtime_rendering', 'enable_moving_window_streaming'):
        require(config.get_editor_property(prop), 'Normal runtime contract changed: ' + prop)
    meshes = []
    for source, name, expected_hash, count in (
        (terrain['mesh_asset'], 'SM_SourceMatchedGround', terrain['revised_native_source']['collision_source_sha256'], terrain['triangle_count']),
        (descriptor['mesh_asset'].split('.')[0], 'SM_CapturedRockInferredFlanks', collision['saved_candidate_source_sha256'], stage['triangle_count'])):
        destination = DEST + name
        require(not asset_file(destination).exists() and not unreal.EditorAssetLibrary.does_asset_exist(destination),
                'Never overwrite an existing production mesh')
        source_mesh = unreal.load_asset(source)
        native(source_mesh, expected_hash, count)
        mesh = unreal.EditorAssetLibrary.duplicate_asset(source, destination)
        require(isinstance(mesh, unreal.StaticMesh), 'Production duplication failed')
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        proof = native(mesh, expected_hash, count)
        require(mesh.get_material(0) == material, 'Duplicate changed original material')
        require(unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False), 'Production mesh save failed')
        meshes.append(dict(mesh=mesh, asset=destination, sha256=sha(asset_file(destination)), native_source=proof))

    original.modify()
    component.modify()
    require(component.set_static_mesh(meshes[0]['mesh']), 'Terrain replacement failed')
    # Persist the exact fallback policy; do not rely on the old asset-name hook.
    component.set_editor_property('disallow_nanite', True)
    component.set_collision_profile_name('BlockAll')
    cap = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*descriptor['translation_cm']))
    cap.modify()
    cap.root_component.modify()
    cap.set_actor_label('SouthFork_Troublemaker_CapturedRock_InferredFlanks')
    cap.root_component.set_editor_property('relative_location', unreal.Vector(*descriptor['translation_cm']))
    cap.root_component.set_editor_property('relative_scale3d', unreal.Vector(1., -1., 1.))
    cap.root_component.set_editor_property('relative_rotation', unreal.Rotator(pitch=0., yaw=0., roll=0.))
    cap.tags = [unreal.Name('RaftSimPhysicalGround'), unreal.Name('RaftSimSouthForkReconstruction20260912')]
    require(cap.static_mesh_component.set_static_mesh(meshes[1]['mesh']), 'Rock installation failed')
    cap.static_mesh_component.set_material(0, material)
    cap.static_mesh_component.set_collision_profile_name('BlockAll')
    cap.static_mesh_component.set_editor_property('disallow_nanite', True)
    cap.static_mesh_component.set_mobility(unreal.ComponentMobility.STATIC)
    config.modify()
    changes = dict(cooked_fields_dir=full['initial_fields_manifest'].rsplit('/', 1)[0],
        streaming_manifest_path=descriptor['streaming_manifest'], coordinate_map_path=descriptor['coordinate_map'],
        window_center_m=unreal.Vector2D(*full['window_center_m']))
    for key, value in changes.items():
        config.set_editor_property(key, value)
    # No player/savegame, catalog, route, launch transform, surface or material edits.
    require(levels.save_current_level(), 'Normal map save failed')
    require(unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, False), 'External actor save failed')
    cap_name = cap.get_name()
    allowed = {('unreal/Content/' + str(before_desc[a.get_name()].actor_package)[6:] + '.uasset')
               for a in (original, config)}
    map_name = 'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'
    allowed.add(map_name)
    for name, digest in preflight['protected_files'].items():
        if name not in allowed:
            require(sha(ROOT / name) == digest, 'Unrelated saved package changed: ' + name)
    for name, digest in descriptor['dependencies'].items():
        require(sha(ROOT / name) == digest, 'Source dependency changed: ' + name)
    report = dict(schema='raftsim.south_fork_source_matched_install.v1', level=LEVEL,
        preflight=preflight_path.relative_to(ROOT).as_posix(), preflight_sha256=sha(preflight_path),
        descriptor=preflight['descriptor'], descriptor_sha256=preflight['descriptor_sha256'],
        backup=backup.relative_to(ROOT).as_posix(), backup_sha256=sha(backup),
        original_terrain_actor=original.get_name(), new_rock_actor=cap_name,
        terrain_asset=meshes[0]['asset'], rock_asset=meshes[1]['asset'],
        meshes=[{k: v for k, v in row.items() if k != 'mesh'} for row in meshes],
        config_actor=config.get_name(), normal_map_saved=True, reloaded_in_fresh_process=False,
        source_time_seconds=descriptor['source_time_seconds'],
        source_dependencies_unchanged=True, unrelated_packages_unchanged=True,
        settled_hydraulics=False, visual_accepted=False, performance_accepted=False,
        source_provenance='Captured exposed rock retained. Revised submerged bed and rock flanks are inferred, not surveyed.',
        changed_saved_files={name: sha(ROOT/name) for name in sorted(allowed)})
    output.write_text(json.dumps(report, indent=2)+'\n')
    unreal.log('Normal South Fork source-matched scene saved; fresh reload required: ' + str(output))


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
