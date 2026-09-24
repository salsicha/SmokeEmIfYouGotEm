"""Verify saved range and unchanged native water/route bindings after map-only fix."""
import json
from pathlib import Path
import sys
import unreal
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'physics/scripts'))
from package_runtime_bundle import sha

def main():
    output = ROOT/'tmp/terrain-range-saved-bindings-v1-20260924.json'
    assert not output.exists()
    bundle = json.loads((ROOT/'physics/data/runtime_bundles/south_fork_source_matched_v2/manifest.json').read_text())
    mutation = json.loads((ROOT/'unreal/Saved/RaftSimValidation/south-fork-terrain-range-normal-v1-20260924.json').read_text())
    before = {r['path']: sha(ROOT/r['path']) for r in bundle['saved_scene_assets']}
    level = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
    map_path = 'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'
    assert before[map_path] == mutation['map_after_sha256']
    assert all(before[r['path']] == r['sha256'] for r in bundle['saved_scene_assets'] if r['path'] != map_path)
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(level)
    layer = unreal.find_object(None, level+'.L_SouthForkAmerican_FullReach:PersistentLevel.WorldSettings.WorldPartition_0.WorldPartitionRuntimeHashSet_1.RuntimePartitionLHGrid_0')
    assert layer and layer.get_editor_property('LoadingRange') == 200000
    descs = [d for d in unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
             if d.native_class.get_name() in ('RaftSimRiverWaterConfig', 'RaftSimRunManager')]
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    config, = [a for a in actors if a.get_class().get_name() == 'RaftSimRiverWaterConfig']
    manager, = [a for a in actors if a.get_class().get_name() == 'RaftSimRunManager']
    entries = dict(streaming_manifest=str(config.get_editor_property('streaming_manifest_path')),
        initial_fields_manifest=str(config.get_editor_property('cooked_fields_dir')).rstrip('/')+'/manifest.json',
        hydraulic_coordinate_map=str(config.get_editor_property('coordinate_map_path')),
        route_coordinate_map=str(manager.get_editor_property('progress_coordinate_map_path')))
    assert entries == bundle['entrypoints']
    bindings = {}
    for actor in (config, manager):
        desc, = [d for d in descs if str(d.name) == actor.get_name()]
        package = str(desc.actor_package)
        path = 'unreal/Content/'+package.removeprefix('/Game/')+'.uasset'
        assert path in before
        bindings[actor.get_class().get_name()] = dict(actor_name=actor.get_name(), package=package, sha256=sha(ROOT/path))
    assert all(sha(ROOT/p) == h for p,h in before.items())
    output.write_text(json.dumps(dict(schema='raftsim.saved_runtime_bindings.v1', level=level,
        map_sha256=before[map_path], bindings=bindings, entrypoints=entries, saved_assets=False,
        main_partition_loading_range_cm=200000), indent=2)+'\n')

if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
