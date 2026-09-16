"""Create an isolated provenance view of the CURRENT single carrier; no source edits."""
import json
from pathlib import Path
import sys

import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import integrate_south_fork_local_froth as source
from raftsim_material_graph_signature import canonical_graph

DEST = '/Game/RaftSim/Environment/GeneratedLocalReview/CurrentFoamAudit/M_CurrentSouthForkFoamAudit'
REPORT = source.ROOT / 'tmp/south-fork-current-foam-audit-material-v1-20260915.json'


def main():
    if REPORT.exists() or unreal.EditorAssetLibrary.does_asset_exist(DEST):
        raise RuntimeError('Preserve existing diagnostic evidence')
    before_hash = source.sha(source.FILE)
    if before_hash != '44c07f419a3a0a9f27f420871e4f1594184e57476de0960e560337ce6a93b31d':
        raise RuntimeError('Unreviewed playable material revision')
    material = unreal.EditorAssetLibrary.duplicate_asset(source.PATH, DEST)
    if not material:
        raise RuntimeError('Failed to duplicate current playable parent')
    lib = unreal.MaterialEditingLibrary
    properties = ('BASE_COLOR', 'ROUGHNESS', 'SPECULAR', 'OPACITY', 'OPACITY_MASK', 'NORMAL', 'WORLD_POSITION_OFFSET')
    def graphs():
        return canonical_graph({p: source.graph(material, lib.get_material_property_input_node(
            material, getattr(unreal.MaterialProperty, 'MP_' + p))) for p in properties})
    before = graphs()
    nodes = list(lib.get_material_expressions(material))
    coverage, = [n for n in nodes if n.get_editor_property('desc') == 'SouthForkTransportedFoamOpticsV1']
    authority = source.links(material, coverage)['VertexFoam']
    if authority.get_editor_property('desc') != 'SouthForkMovingFoamAuthorityV1':
        raise RuntimeError('Wrong foam authority')
    inputs = source.links(material, authority)
    debug = lib.create_material_expression(material, unreal.MaterialExpressionCustom)
    debug.set_editor_property('description', 'Current foam provenance: R final, G GPU ownership, B GPU coverage')
    debug.set_editor_property('code', 'float weight=RaftSimRegisteredDetailWindowWeight(Texture,World.xy*float2(0.01,0.01*Sign))*Enable; return float3(Final,weight,Detail.a);')
    debug.set_editor_property('include_file_paths', ['/Plugin/RaftSimWaterDetail/Private/RaftSimRegisteredDetailSample.ush'])
    debug.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    connections = dict(Final=coverage, **{p: inputs[p] for p in ('Texture', 'World', 'Sign', 'Enable', 'Detail')})
    pins = []
    for name in connections:
        pin = unreal.CustomInput(); pin.set_editor_property('input_name', name); pins.append(pin)
    debug.set_editor_property('inputs', pins)
    for name, node in connections.items():
        assert lib.connect_material_expressions(node, '', debug, name)
    material.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    assert lib.connect_material_property(debug, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    assert graphs() == before, 'Diagnostic changed source geometry, normal or optical input graphs'
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    assert source.sha(source.FILE) == before_hash
    with REPORT.open('x', encoding='utf-8') as out:
        json.dump(dict(material=DEST, source_material=source.PATH, source_sha256=before_hash,
            diagnostic_sha256=source.sha(source.ROOT/'unreal/Content'/(DEST.removeprefix('/Game/')+'.uasset')),
            source_unchanged=True, protected_graphs=before, same_carrier=True,
            channels=dict(red='final optical foam coverage', green='GPU window ownership', blue='resolved GPU foam coverage'),
            scope='Unlit diagnostic only; tone mapping prevents numerical interpretation of screenshot RGB. Not a visual candidate.'), out, indent=2)
        out.write('\n')
    unreal.log('Current single-carrier foam provenance diagnostic saved: ' + str(REPORT))


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
