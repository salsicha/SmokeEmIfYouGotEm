"""Reload the saved normal river, verify its bindings, correct launch heading.

The Python Rotator positional constructor is not FRotator's C++ ordering.
Use named angles and archive the affected current packages before correction.
"""
import hashlib
import json
import math
from pathlib import Path
import zipfile
import unreal

ROOT = Path(__file__).resolve().parents[2]
ASSEMBLY = ROOT/'unreal/Saved/RaftSimValidation/south-fork-normal-assembly-v1-20260912.json'
OUTPUT = ROOT/'unreal/Saved/RaftSimValidation/south-fork-normal-reload-v1-20260912.json'
BACKUP = ROOT/'unreal/Saved/RaftSimValidation/south-fork-launch-transform-before-v2-20260912.zip'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def package_file(package):
    assert package.startswith('/Game/')
    return ROOT/'unreal/Content'/(package.removeprefix('/Game/')+'.uasset')


def xyz(value):
    return [value.x, value.y, value.z]


def main():
    assert not OUTPUT.exists()
    assembly = json.loads(ASSEMBLY.read_text())
    for row in assembly['external_packages']:
        assert sha(package_file(row['package'])) == row['sha256']
    profile = ROOT/'unreal/Saved/SaveGames/RaftSimVerticalSlice.sav'
    assert sha(profile) == '181d1e570485d1ec3139aec4e1d9b56d0a420fd107ce5a94218368324207f5b1'
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert levels.load_level(assembly['level'])
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = subsystem.get_all_level_actors()
    descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    assert len(descs) == 455
    kinds = [desc.native_class.get_name() for desc in descs]
    assert kinds.count('StaticMeshActor') == 443 and kinds.count('RaftSimRockObstacleActor') == 0
    assert kinds.count('RaftSimWaterSurfaceActor') == kinds.count('RaftSimRunManager') == 1

    def one(kind):
        values = [actor for actor in actors if actor.get_class().get_name() == kind]
        assert len(values) == 1, (kind, len(values))
        return values[0]

    config, run, surface = one('RaftSimRiverWaterConfig'), one('RaftSimRunManager'), one('RaftSimWaterSurfaceActor')
    raft, start = one('RaftSimRaftActor'), one('PlayerStart')
    assert config.get_editor_property('streaming_manifest_path') == assembly['streaming_manifest']
    assert run.get_editor_property('progress_coordinate_map_path') == assembly['route_coordinate_map']
    assert run.get_editor_property('start_station_m') == 120. and run.get_editor_property('finish_station_m') == 33280.
    for prop in ('map_provides_terrain', 'live_solver_owns_runtime_rendering', 'enable_live_solver_volume_core',
                 'enable_live_shared_breaking_relief', 'enable_moving_window_streaming'):
        assert config.get_editor_property(prop), prop
    assert surface.get_editor_property('vertex_spacing_meters') == 1.
    assert surface.get_editor_property('river_presentation_subdivision') == 1
    assert xyz(surface.get_actor_location()) == [0., 0., 0.]
    for actor in (config, run, surface, raft, start):
        assert not actor.get_editor_property('is_spatially_loaded'), actor.get_name()
    route = unreal.RaftSimWaterRuntimeAdapter()
    assert route.configure_river_coordinate_map(assembly['route_coordinate_map'])
    a = route.river_to_world_position(unreal.Vector2D(120., 0.), 220.)
    b = route.river_to_world_position(unreal.Vector2D(121., 0.), 220.)
    yaw = math.degrees(math.atan2(b.y-a.y, b.x-a.x))
    rotation = unreal.Rotator(pitch=0., yaw=yaw, roll=0.)
    assert rotation.yaw == yaw and rotation.pitch == rotation.roll == 0.
    changed = []
    with zipfile.ZipFile(BACKUP, 'x', zipfile.ZIP_DEFLATED) as archive:
        for actor in (raft, start):
            desc = next(desc for desc in descs if str(desc.name) == actor.get_name())
            path = package_file(str(desc.actor_package))
            archive.write(path, path.relative_to(ROOT).as_posix())
            old = actor.get_actor_rotation()
            changed.append(dict(actor=actor.get_name(), package=str(desc.actor_package),
                old_location_cm=xyz(actor.get_actor_location()), new_location_cm=assembly['raft_start_cm'],
                old_pitch_yaw_roll=[old.pitch, old.yaw, old.roll], new_pitch_yaw_roll=[0., yaw, 0.]))
            actor.modify()
            root = actor.root_component
            root.modify()
            root.set_editor_property('relative_location', unreal.Vector(*assembly['raft_start_cm']))
            root.set_editor_property('relative_rotation', rotation)
            assert xyz(actor.get_actor_location()) == assembly['raft_start_cm']
            assert abs(actor.get_actor_rotation().yaw-yaw) < .001
    assert levels.save_current_level()
    assert unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, False)
    # In-memory transforms are insufficient: the first assembly exposed a
    # root-component serialization mismatch. Reload from disk before passing.
    assert levels.load_level('/Game/RaftSim/Maps/L_RaftSimTestTank')
    assert levels.load_level(assembly['level'])
    actors = subsystem.get_all_level_actors()
    for kind in ('RaftSimRaftActor', 'PlayerStart'):
        actor = one(kind)
        actual_rotation = actor.get_actor_rotation()
        assert xyz(actor.get_actor_location()) == assembly['raft_start_cm'], ('Unsaved launch position', kind)
        assert abs(actual_rotation.yaw-yaw) < .001 and abs(actual_rotation.pitch) < .001 and abs(actual_rotation.roll) < .001
    allowed = {row['package'] for row in changed}
    for row in assembly['external_packages']:
        if row['package'] not in allowed:
            assert sha(package_file(row['package'])) == row['sha256'], row['package']
    assert sha(profile) == '181d1e570485d1ec3139aec4e1d9b56d0a420fd107ce5a94218368324207f5b1'
    report = dict(level=assembly['level'], descriptor_count=len(descs), source_terrain_actor_count=443,
        runtime_binding_reload_verified=True, launch_transform_reloaded=True, one_water_actor=True, rendered_source_spacing_m=1.,
        heading_corrections=changed, heading_backup=str(BACKUP.relative_to(ROOT)),
        profile_unchanged=True, unaffected_packages_unchanged=True, full_scene_accepted=False,
        map_sha256=sha(ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'),
        external_packages=[dict(package=str(desc.actor_package), sha256=sha(package_file(str(desc.actor_package)))) for desc in descs])
    OUTPUT.write_text(json.dumps(report, indent=2)+'\n')
    unreal.log(f'Normal South Fork reload and launch heading verified: {OUTPUT}')


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
