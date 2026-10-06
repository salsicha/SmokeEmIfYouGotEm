"""Read actual playable parent graphs without saving or changing any asset."""
import hashlib
import json
import os
from pathlib import Path
import sys
import unreal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from integrate_south_fork_local_froth import graph, links
from raftsim_material_graph_signature import canonical_graph

PARENTS = (
    '/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/M_RaftSim_SouthForkRaftTransmissionWaterV4',
    '/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/M_TroublemakerWater',
    '/Game/RaftSim/Environment/ColoradoRun/Water/Materials/M_RaftSim_ColoradoCurrentWaterV3',
    '/Game/RaftSim/Environment/PacuareRun/Water/Materials/M_RaftSim_PacuareCurrentWaterV2',
    '/Game/RaftSim/Environment/FutaleufuRun/Water/Materials/M_RaftSim_FutaleufuCurrentWaterV5',
    '/Game/RaftSim/Environment/ChilkoRun/Water/Materials/M_RaftSim_ChilkoCurrentWaterV4',
)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    report = (ROOT / os.environ['RAFTSIM_FROTH_INVENTORY_REPORT']).resolve()
    if not report.is_relative_to(ROOT / 'tmp') or report.exists():
        raise RuntimeError('Fresh repository-local report required')
    lib = unreal.MaterialEditingLibrary
    rows = []
    for path in PARENTS:
        file = ROOT / 'unreal/Content' / (path.removeprefix('/Game/') + '.uasset')
        before = sha(file)
        material = unreal.load_asset(path)
        if not isinstance(material, unreal.Material):
            raise RuntimeError('Expected actual playable parent: ' + path)
        nodes = list(lib.get_material_expressions(material))
        parameters, customs = [], []
        for node in nodes:
            if isinstance(node, (unreal.MaterialExpressionScalarParameter,
                                 unreal.MaterialExpressionVectorParameter)):
                parameters.append(dict(name=str(node.get_editor_property('parameter_name')),
                                       value=str(node.get_editor_property('default_value'))))
            if isinstance(node, unreal.MaterialExpressionCustom):
                customs.append(dict(name=node.get_name(), desc=str(node.get_editor_property('desc')),
                                    code=str(node.get_editor_property('code')),
                                    inputs={k: v.get_name() if v else None for k, v in links(material, node).items()}))
        roots = {}
        for name in ('BASE_COLOR', 'ROUGHNESS', 'SPECULAR', 'NORMAL', 'OPACITY',
                     'OPACITY_MASK', 'EMISSIVE_COLOR', 'WORLD_POSITION_OFFSET'):
            prop = getattr(unreal.MaterialProperty, 'MP_' + name)
            node = lib.get_material_property_input_node(material, prop)
            roots[name] = dict(root=node.get_name() if node else None,
                              nodes=canonical_graph(graph(material, node)))
        if sha(file) != before:
            raise RuntimeError('Read-only inventory changed source bytes')
        rows.append(dict(material=path, sha256=before, source_unchanged=True,
                         tangent_space_normal=bool(material.get_editor_property('tangent_space_normal')),
                         parameters=parameters, custom_nodes=customs, roots=roots))
    report.write_text(json.dumps(dict(schema='raftsim.playable_froth_parent_inventory.v1',
                                     scope='Actual saved parent graphs, not runtime MID overrides, GPU pixels or physical/FPS acceptance.',
                                     read_only=True, materials=rows), indent=2) + '\n')
    unreal.log('Read-only playable froth inventory: ' + str(report))


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
