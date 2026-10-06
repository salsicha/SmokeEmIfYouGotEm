"""Read-only material graph receipt; does not recompile or save any asset."""
import json
from pathlib import Path
import unreal

root = Path(__file__).resolve().parents[2]
paths = [
    '/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/M_RaftSim_SouthForkRaftTransmissionWaterV4',
    '/Game/RaftSim/Materials/M_RaftSim_SolverOverlayFoam',
]
results = []
try:
    for path in paths:
        asset = unreal.load_asset(path)
        entry = dict(path=path, loaded=asset is not None, nodes=[])
        if isinstance(asset, unreal.Material):
            for node in unreal.MaterialEditingLibrary.get_material_expressions(asset):
                if isinstance(node, unreal.MaterialExpressionCustom):
                    entry['nodes'].append(dict(kind='custom', description=node.get_editor_property('description'), code=node.get_editor_property('code')))
                elif isinstance(node, unreal.MaterialExpressionScalarParameter):
                    entry['nodes'].append(dict(kind='scalar', name=str(node.get_editor_property('parameter_name')), default=node.get_editor_property('default_value')))
        results.append(entry)
    destination = root / 'tmp/playable-feature-foam-graph-v1.json'
    if destination.exists():
        raise RuntimeError('Preserve previous receipt; choose a fresh output')
    destination.write_text(json.dumps(results, indent=2), encoding='utf-8')
finally:
    unreal.SystemLibrary.quit_editor()
