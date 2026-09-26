"""Point the normal FullReach water config at a new runtime export, or inventory it.

RAFTSIM_BIND_MODE=set: load the map, load the RaftSimRiverWaterConfig actor,
set streaming_manifest_path and cooked_fields_dir to the export given by
RAFTSIM_RUNTIME_EXPORT (repo-relative; same initial window id as before) and
save only that actor's package. Coordinate maps and the run manager are not
changed. Writes RAFTSIM_BIND_REPORT (fresh tmp JSON) with before/after values.

RAFTSIM_BIND_MODE=inventory: read-only; writes the
raftsim.saved_runtime_bindings.v1 inventory used by package_runtime_bundle.py.
"""
import hashlib
import json
import os
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
LEVEL = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
MAP_PATH = 'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load():
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL)
    descs = [d for d in unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
             if d.native_class.get_name() in ('RaftSimRiverWaterConfig', 'RaftSimRunManager')]
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    config, = [a for a in actors if a.get_class().get_name() == 'RaftSimRiverWaterConfig']
    manager, = [a for a in actors if a.get_class().get_name() == 'RaftSimRunManager']
    return descs, config, manager


def entries(config, manager):
    return dict(streaming_manifest=str(config.get_editor_property('streaming_manifest_path')),
                initial_fields_manifest=str(config.get_editor_property('cooked_fields_dir')).rstrip('/') + '/manifest.json',
                hydraulic_coordinate_map=str(config.get_editor_property('coordinate_map_path')),
                route_coordinate_map=str(manager.get_editor_property('progress_coordinate_map_path')))


def package_file(desc):
    return 'unreal/Content/' + str(desc.actor_package).removeprefix('/Game/') + '.uasset'


def main():
    mode = os.environ['RAFTSIM_BIND_MODE']
    report_path = ROOT / os.environ['RAFTSIM_BIND_REPORT']
    assert report_path.is_relative_to(ROOT / 'tmp') and not report_path.exists()
    descs, config, manager = load()
    before = entries(config, manager)
    if mode == 'set':
        export = os.environ['RAFTSIM_RUNTIME_EXPORT'].rstrip('/')
        stream = export + '/streaming_manifest_coverage_checked.json'
        window = before['initial_fields_manifest'].rsplit('/', 2)[-2]
        fields_dir = export + '/' + window
        assert (ROOT / stream).is_file() and (ROOT / fields_dir / 'manifest.json').is_file()
        desc, = [d for d in descs if str(d.name) == config.get_name()]
        path = ROOT / package_file(desc)
        package_before = sha(path)
        config.modify()
        config.set_editor_property('streaming_manifest_path', stream)
        config.set_editor_property('cooked_fields_dir', fields_dir)
        assert unreal.EditorAssetLibrary.save_loaded_asset(config, only_if_is_dirty=False) or \
            unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, True)
        after = entries(config, manager)
        assert after['streaming_manifest'] == stream and after['initial_fields_manifest'] == fields_dir + '/manifest.json'
        assert after['hydraulic_coordinate_map'] == before['hydraulic_coordinate_map'] and after['route_coordinate_map'] == before['route_coordinate_map']
        result = dict(mode=mode, level=LEVEL, before=before, after=after, config_package=package_file(desc),
                      config_package_sha256_before=package_before, config_package_sha256_after=sha(path),
                      map_sha256=sha(ROOT / MAP_PATH), coordinate_maps_changed=False, run_manager_changed=False)
    else:
        bindings = {}
        for actor in (config, manager):
            desc, = [d for d in descs if str(d.name) == actor.get_name()]
            bindings[actor.get_class().get_name()] = dict(actor_name=actor.get_name(), package=str(desc.actor_package),
                                                         sha256=sha(ROOT / package_file(desc)))
        result = dict(schema='raftsim.saved_runtime_bindings.v1', level=LEVEL, map_sha256=sha(ROOT / MAP_PATH),
                      bindings=bindings, entrypoints=before, saved_assets=False)
    report_path.write_text(json.dumps(result, indent=2) + '\n')
    unreal.log('RAFTSIM_DISCHARGE_BED_BIND ' + json.dumps(dict(mode=mode, entrypoints=result.get('after', result.get('entrypoints')))))


if __name__ == '__main__':
    main()
