"""Read the canopy-updated saved map's real water/route bindings; save no assets."""
import json
import os
from pathlib import Path
import sys

import unreal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'physics/scripts'))
from package_runtime_bundle import sha


def main():
    output = (ROOT / os.environ['RAFTSIM_CANOPY_BINDINGS_REPORT']).resolve()
    if not output.is_relative_to(ROOT / 'tmp') or output.exists():
        raise ValueError('Fresh local binding report required')
    bundle = json.loads((ROOT / 'physics/data/runtime_bundles/south_fork_source_matched_v2/manifest.json').read_text())
    canopy_path = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/chili_bar/canopy_20260918/integration_audit.json'
    canopy = json.loads(canopy_path.read_text())
    level = '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach'
    map_path = ROOT / 'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap'
    if canopy['passed'] is not True or sha(map_path) != canopy['map_sha256']:
        raise ValueError('Map differs from independently reloaded canopy integration')
    before = {row['path']: sha(ROOT / row['path']) for row in bundle['saved_scene_assets']}
    for row in bundle['saved_scene_assets'][1:]:
        if before[row['path']] != row['sha256']:
            raise ValueError('Water/route actor changed; map-only rebind is unsafe')
    if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(level):
        raise ValueError('Saved map failed to load')
    descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
    relevant = [d for d in descs if d.native_class.get_name() in ('RaftSimRiverWaterConfig', 'RaftSimRunManager')]
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in relevant])
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    config, = [a for a in actors if a.get_class().get_name() == 'RaftSimRiverWaterConfig']
    manager, = [a for a in actors if a.get_class().get_name() == 'RaftSimRunManager']
    entries = dict(streaming_manifest=str(config.get_editor_property('streaming_manifest_path')),
        initial_fields_manifest=str(config.get_editor_property('cooked_fields_dir')).rstrip('/')+'/manifest.json',
        hydraulic_coordinate_map=str(config.get_editor_property('coordinate_map_path')),
        route_coordinate_map=str(manager.get_editor_property('progress_coordinate_map_path')))
    if entries != bundle['entrypoints']:
        raise ValueError('Saved runtime entrypoints changed')
    bindings = {}
    for actor in (config, manager):
        desc, = [d for d in relevant if str(d.name) == actor.get_name()]
        package = str(desc.actor_package)
        path = 'unreal/Content/'+package.removeprefix('/Game/')+'.uasset'
        if path not in before:
            raise ValueError('Saved actor package changed')
        bindings[actor.get_class().get_name()] = dict(actor_name=actor.get_name(), package=package, sha256=sha(ROOT/path))
    if any(sha(ROOT/name) != digest for name, digest in before.items()):
        raise ValueError('Read-only reload changed saved bytes')
    output.write_text(json.dumps(dict(schema='raftsim.saved_runtime_bindings.v1', level=level,
        map_sha256=sha(map_path), bindings=bindings, entrypoints=entries, saved_assets=False,
        canopy_reload_sha256=sha(canopy_path)), indent=2)+'\n')
    unreal.log('CANOPY_RUNTIME_BINDINGS_VERIFIED '+str(output))


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
