"""Read-only saved continuous-scene bindings for the verified runtime packager.

RAFTSIM_CONTINUOUS_LEVEL selects an existing World Partition level.
RAFTSIM_CONTINUOUS_INVENTORY is a fresh repo tmp JSON; no asset is saved.
"""
import json
import os
from pathlib import Path
import sys
import unreal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'physics/scripts'))
from package_runtime_bundle import sha, logical_path, validate_coordinate_map


def main():
    level = os.environ['RAFTSIM_CONTINUOUS_LEVEL']
    if not level.startswith('/Game/'):
        raise ValueError('Project level required')
    map_path = ROOT/logical_path('unreal/Content/'+level[6:]+'.umap')
    report = (ROOT/os.environ['RAFTSIM_CONTINUOUS_INVENTORY']).resolve()
    if not report.is_relative_to(ROOT/'tmp') or report.exists():
        raise ValueError('Fresh tmp inventory required')
    before = {map_path: sha(map_path)}
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(level)
    descs = [d for d in unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
             if d.native_class.get_name() in ('RaftSimRiverWaterConfig', 'RaftSimRunManager')]
    for desc in descs:
        name = logical_path('unreal/Content/'+str(desc.actor_package).removeprefix('/Game/')+'.uasset')
        before[ROOT/name] = sha(ROOT/name)
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    config, = [a for a in actors if a.get_class().get_name() == 'RaftSimRiverWaterConfig']
    manager, = [a for a in actors if a.get_class().get_name() == 'RaftSimRunManager']
    hydraulic = str(config.get_editor_property('coordinate_map_path'))
    route_override = str(manager.get_editor_property('progress_coordinate_map_path'))
    # Matches RunManager::GetProgressCoordinates: only curved hydraulics can
    # supply the progress axis when the saved override is empty.
    coordinates = json.loads((ROOT/logical_path(hydraulic)).read_text())
    validate_coordinate_map(coordinates)
    if not route_override and coordinates['schema'] != 'raftsim.curved_river_coordinate_map.v1':
        raise ValueError('Cartesian water cannot provide a fallback progress route')
    entries = dict(streaming_manifest=str(config.get_editor_property('streaming_manifest_path')),
        initial_fields_manifest=str(config.get_editor_property('cooked_fields_dir')).rstrip('/')+'/manifest.json',
        hydraulic_coordinate_map=hydraulic, route_coordinate_map=route_override or hydraulic)
    bindings = {}
    for actor in (config, manager):
        desc, = [d for d in descs if str(d.name) == actor.get_name()]
        name = 'unreal/Content/'+str(desc.actor_package).removeprefix('/Game/')+'.uasset'
        bindings[actor.get_class().get_name()] = dict(actor_name=actor.get_name(),
            package=str(desc.actor_package), sha256=sha(ROOT/name))
    assert all(sha(path) == digest for path, digest in before.items())
    result = dict(schema='raftsim.saved_runtime_bindings.v1', level=level,
        map_sha256=before[map_path], bindings=bindings, entrypoints=entries, saved_assets=False,
        route_uses_curved_hydraulic_fallback=not bool(route_override),
        flow_band=str(config.get_editor_property('flow_band')),
        physical_acceptance=False, packaged_execution_verified=False)
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open('x') as stream:
        json.dump(result, stream, indent=2)
    unreal.log('RAFTSIM_CONTINUOUS_RUNTIME_INVENTORY '+str(report))


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
