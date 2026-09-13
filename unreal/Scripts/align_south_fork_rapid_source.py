"""Bind the full-river rapid to the geometry already used by its hydraulic bed.

One existing external actor changes mesh reference. No new scenario, mesh
deformation, source-asset edits, material edits or user-profile writes.
"""
import hashlib
import json
from pathlib import Path
import zipfile
import unreal

ROOT = Path(__file__).resolve().parents[2]
LEVEL = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
OLD = '/Game/RaftSim/Environment/SouthForkRockRegisteredCandidate20260907/SM_TroublemakerSurveyCandidate'
NEW = '/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround'
ACTOR = 'StaticMeshActor_UAID_04421A89ABE5ED0003_2136936984'
MAP_SHA = '09dcd41fd37013cbb2fc0d4e94de952ca45731937b517aad0e518d8922afec2d'
PROFILE_SHA = '181d1e570485d1ec3139aec4e1d9b56d0a420fd107ce5a94218368324207f5b1'
NEW_ASSET_SHA = '6aec899c1dad1d26b8410813637f705c4fdd2552d5b4db718bb974eb6fa51a4a'
GEOMETRY_SHA = '8bdf1a586e7bd2536eaf25a982763efd9e5a558e7172fd7897b8ae0ecc8fe06b'
REPORT = ROOT/'unreal/Saved/RaftSimValidation/south-fork-rapid-source-alignment-v1-20260912.json'
BACKUP = ROOT/'unreal/Saved/RaftSimValidation/south-fork-rapid-before-source-alignment-v1-20260912.zip'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text())


def package_file(package):
    assert package.startswith('/Game/') and '..' not in package.split('/')
    return ROOT/'unreal/Content'/(package.removeprefix('/Game/')+'.uasset')


def xyz(value):
    return [value.x, value.y, value.z]


def main():
    assert 'RaftSimAlignSouthForkRapidSource' in unreal.SystemLibrary.get_command_line()
    assert not REPORT.exists() and not BACKUP.exists(), 'Do not repeat a map mutation blindly'
    map_file = ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'
    profile = ROOT/'unreal/Saved/SaveGames/RaftSimVerticalSlice.sav'
    assert sha(map_file) == MAP_SHA and sha(profile) == PROFILE_SHA
    assert sha(package_file(NEW)) == NEW_ASSET_SHA
    old_asset_sha = sha(package_file(OLD))
    base = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
    composite = read(base/'composite_terrain/manifest.json')
    export = read(ROOT/'unreal/SourceArt/RaftSim/TroublemakerInferredRockFlanks20260912/manifest.json')
    evidence = read(ROOT/'unreal/Saved/RaftSimValidation/troublemaker-inferred-flanks-integration-20260912.json')
    audit = read(ROOT/'tmp/troublemaker-inferred-rock-flanks-20260912/sampling-audit.json')
    assert composite['registered_rapid_sha256'] == export['source_geometry_sha256'] == evidence['source_geometry_sha256'] == audit['source_geometry_sha256'] == GEOMETRY_SHA
    assert sha(base/'composite_terrain/troublemaker_registered_source.npz') == GEOMETRY_SHA
    assert evidence['mesh_sha256'] == NEW_ASSET_SHA and evidence['maximum_collision_error_cm'] <= .1
    assert sha(ROOT/export['fbx']) == export['fbx_sha256']
    assembly = read(ROOT/'unreal/Saved/RaftSimValidation/south-fork-normal-assembly-v1-20260912.json')
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level(LEVEL)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    descriptors = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    assert len(descriptors) == 455
    target = next(d for d in descriptors if str(d.name) == ACTOR)
    package = str(target.actor_package)
    previous = next(row for row in assembly['external_packages'] if row['package'] == package)
    assert sha(package_file(package)) == previous['sha256'], 'Target actor changed since assembly'
    before = {str(d.actor_package): sha(package_file(str(d.actor_package))) for d in descriptors}
    with zipfile.ZipFile(BACKUP, 'x', zipfile.ZIP_DEFLATED) as archive:
        for path in (map_file, package_file(package)):
            archive.write(path, path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(BACKUP) as archive:
        for path, digest in ((map_file, MAP_SHA), (package_file(package), before[package])):
            assert hashlib.sha256(archive.read(path.relative_to(ROOT).as_posix())).hexdigest() == digest
    unreal.WorldPartitionBlueprintLibrary.load_actors([target.guid])
    ground = next(a for a in actors.get_all_level_actors() if a.get_name() == ACTOR)
    component = ground.static_mesh_component
    assert component.static_mesh.get_path_name().split('.')[0] == OLD
    assert 'RaftSimPhysicalGround' in [str(tag) for tag in ground.tags]
    position, scale = xyz(ground.get_actor_location()), xyz(ground.get_actor_scale3d())
    placement = read(base/'playable_route/troublemaker_placement.json')
    assert position == placement['translation_from_existing_rapid_world_cm'] and scale == [1., -1., 1.]
    rotation = ground.get_actor_rotation()
    assert rotation.pitch == rotation.yaw == rotation.roll == 0.
    material = component.get_material(0).get_path_name()
    mesh = unreal.load_asset(NEW)
    assert mesh and mesh.get_num_triangles(0) == export['triangle_count'] == 803842
    ground.modify(); component.modify()
    assert component.set_static_mesh(mesh)
    assert component.get_material(0).get_path_name() == material
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    # Verify exact changed triangles and original anchors at the full-river
    # transform. This source-only trace does not claim combined traversal.
    probes = list(audit['exact_changed_triangle_probes_cm'])
    probes += [[p['position_cm'][0], -p['position_cm'][1], p['position_cm'][2]] for p in export['collision_probes_cm']]
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    ignore = [a for a in actors.get_all_level_actors() if a != ground]
    maximum = 0.
    for x, y, z in probes:
        x += position[0]; y += position[1]; z += position[2]
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x,y,z+1000), unreal.Vector(x,y,z-1000),
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, ignore, unreal.DrawDebugTrace.NONE, False)
        values = hit.to_tuple() if hit else None
        assert values and values[0], ('Missing source collision', x,y,z)
        error = abs(values[5].z-z)
        assert error <= .1, ('Source collision mismatch', x,y,z,error)
        maximum = max(maximum,error)
    assert levels.save_current_level()
    assert unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,False)
    assert levels.load_level('/Game/RaftSim/Maps/L_RaftSimTestTank')
    assert levels.load_level(LEVEL)
    unreal.WorldPartitionBlueprintLibrary.load_actors([target.guid])
    reloaded = next(a for a in actors.get_all_level_actors() if a.get_name() == ACTOR)
    assert reloaded.static_mesh_component.static_mesh.get_path_name().split('.')[0] == NEW
    assert xyz(reloaded.get_actor_location()) == position and xyz(reloaded.get_actor_scale3d()) == scale
    assert reloaded.static_mesh_component.get_material(0).get_path_name() == material
    for name, digest in before.items():
        if name != package: assert sha(package_file(name)) == digest, ('Unrelated actor changed',name)
    assert len(unreal.WorldPartitionBlueprintLibrary.get_actor_descs()) == 455
    assert sha(package_file(NEW)) == NEW_ASSET_SHA and sha(package_file(OLD)) == old_asset_sha
    assert sha(profile) == PROFILE_SHA
    assert all(str(s.scenario_id) != 'troublemaker_challenge' for s in unreal.RaftSimProgressionLibrary.get_scenario_catalog())
    result = dict(schema='raftsim.south_fork.rapid_source_alignment.v1', level=LEVEL, actor=ACTOR,
        actor_package=package, previous_mesh=OLD, mesh=NEW, mesh_sha256=NEW_ASSET_SHA,
        source_geometry_sha256=GEOMETRY_SHA, hydraulic_rapid_geometry_sha256=composite['registered_rapid_sha256'],
        source_collision_probe_count=len(probes), maximum_source_collision_error_cm=maximum,
        collision_scope='Changed triangles and original anchors, target mesh only at full-river placement; combined gameplay separate.',
        transform_unchanged=True, material_unchanged=True, profile_unchanged=True, source_assets_unchanged=True,
        unrelated_actor_packages_unchanged=True, reload_verified=True, no_rapid_scenario=True,
        previous_map_sha256=MAP_SHA, map_sha256=sha(map_file), actor_package_sha256=sha(package_file(package)),
        backup=str(BACKUP.relative_to(ROOT)), backup_sha256=sha(BACKUP), full_scene_accepted=False)
    REPORT.write_text(json.dumps(result,indent=2)+'\n')
    unreal.log(f'Full-river rapid source alignment verified: {REPORT}')


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
