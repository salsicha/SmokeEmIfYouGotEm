"""Read saved playable-map water bindings and optical flow consumers; never save assets."""
import hashlib
import json
import os
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[2]
MAPS = ('L_SouthForkAmerican_FullReach', 'L_SouthFork_Troublemaker',
        'L_Hance', 'L_LavaCanyon', 'L_Terminator', 'L_UpperHuacas',
        'L_Zambezi', 'L_ZambeziUpperGorge')


def material_inventory(material):
    parents = []
    while isinstance(material, unreal.MaterialInstance):
        parents.append(material.get_path_name())
        material = material.get_editor_property('parent')
    if not material:
        return dict(parents=parents, missing=True)
    lib = unreal.MaterialEditingLibrary
    consumers = []
    for node in lib.get_material_expressions(material):
        if not isinstance(node, unreal.MaterialExpressionCustom):
            continue
        inputs = {}
        for pin, source in zip(lib.get_material_expression_input_names(node),
                               lib.get_inputs_for_material_expression(material, node)):
            if source:
                row = dict(node=source.get_name(), kind=source.get_class().get_name())
                if isinstance(source, unreal.MaterialExpressionTextureCoordinate):
                    row['coordinate_index'] = source.get_editor_property('coordinate_index')
                inputs[str(pin)] = row
        consumers.append(dict(node=node.get_name(), desc=str(node.get_editor_property('desc')),
                              code=str(node.get_editor_property('code')), inputs=inputs))
    return dict(parents=parents, material=material.get_path_name(), consumers=consumers)


def main():
    output = (ROOT / os.environ['RAFTSIM_FEATURE_INVENTORY']).resolve()
    if not output.is_relative_to(ROOT/'tmp') or output.exists():
        raise ValueError('Fresh repository-local tmp report required')
    results = []
    editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    for name in MAPS:
        level = '/Game/RaftSim/Maps/'+name
        path = ROOT/'unreal/Content/RaftSim/Maps'/(name+'.umap')
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        if not editor.load_level(level):
            raise RuntimeError('Cannot load '+level)
        descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
        selected = [d for d in descs if d.native_class and d.native_class.get_name() in
                    ('RaftSimRiverWaterConfig', 'RaftSimRunManager')]
        if selected:
            unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in selected])
        actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
        configs = [a for a in actors if a.get_class().get_name() == 'RaftSimRiverWaterConfig']
        row = dict(level=level, map_sha256=before, configs=[],
                   partition_rock_actors=sum(bool(d.native_class) and d.native_class.get_name() == 'RaftSimRockObstacleActor' for d in descs),
                   loaded_rock_actors=sum(a.get_class().get_name() == 'RaftSimRockObstacleActor' for a in actors))
        for actor in configs:
            properties = {p: str(actor.get_editor_property(p)) for p in
                          ('cooked_fields_dir', 'coordinate_map_path', 'flow_band',
                           'streaming_manifest_path', 'live_volume_core_material_override')}
            properties['material_graph'] = material_inventory(
                actor.get_editor_property('live_volume_core_material_override'))
            row['configs'].append(properties)
        if hashlib.sha256(path.read_bytes()).hexdigest() != before:
            raise RuntimeError('Read-only inventory changed '+level)
        results.append(row)
        unreal.log('SHARED_WATER_INVENTORY '+name+' configs='+str(len(configs)))
    output.write_text(json.dumps(dict(schema='raftsim.shared_water_map_inventory.v1',
                                     saved_assets=False, maps=results), indent=2)+'\n')


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
