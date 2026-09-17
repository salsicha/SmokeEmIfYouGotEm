"""Isolate paired optical flow on the current carrier; preserve all other nodes."""
import json
from pathlib import Path
import sys
import zipfile
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import integrate_south_fork_local_froth as source
from raftsim_material_graph_signature import canonical_graph

DEST = '/Game/RaftSim/Environment/GeneratedLocalReview/PairedFoamFlow/M_SouthForkPairedFoamFlow'
REPORT = source.ROOT/'tmp/south-fork-paired-foam-flow-material-v1-20260917.json'
INCLUDE = '/Plugin/RaftSimWaterDetail/Private/RaftSimRegisteredFoamFlow.ush'
CODE = 'return RaftSimRegisteredFoamFlow(Texture,FlowTexture,World.xy*float2(.01,.01*Sign),CPUFlow.xy,Enable);'


def main():
    install = 'RaftSimInstallPairedFoamFlow' in unreal.SystemLibrary.get_command_line()
    report = REPORT.with_name('south-fork-paired-foam-flow-install-v1-20260917.json') if install else REPORT
    if report.exists() or (not install and unreal.EditorAssetLibrary.does_asset_exist(DEST)):
        raise RuntimeError('Preserve previous review evidence')
    before_hash = source.sha(source.FILE)
    if before_hash != '44c07f419a3a0a9f27f420871e4f1594184e57476de0960e560337ce6a93b31d':
        raise RuntimeError('Unreviewed playable material revision')
    lib = unreal.MaterialEditingLibrary
    backup = report.with_suffix('.backup.zip')
    if install:
        with zipfile.ZipFile(backup, 'x', zipfile.ZIP_DEFLATED) as archive:
            archive.write(source.FILE, source.FILE.relative_to(source.ROOT).as_posix())
        with zipfile.ZipFile(backup) as archive:
            import hashlib
            assert hashlib.sha256(archive.read(source.FILE.relative_to(source.ROOT).as_posix())).hexdigest() == before_hash
    material = unreal.load_asset(source.PATH) if install else unreal.EditorAssetLibrary.duplicate_asset(source.PATH, DEST)
    assert material
    nodes = list(lib.get_material_expressions(material))
    coverage, = [n for n in nodes if n.get_editor_property('desc') == 'SouthForkTransportedFoamOpticsV1']
    authority = source.links(material, coverage)['VertexFoam']
    assert authority.get_editor_property('desc') == 'SouthForkMovingFoamAuthorityV1'
    old_flow = source.links(material, coverage)['FrothFlow']
    assert old_flow.get_editor_property('coordinate_index') == 3
    before = {n.get_name(): source.graph(material, n)[n.get_name()] for n in nodes}
    protected = ('MP_WORLD_POSITION_OFFSET', 'MP_NORMAL', 'MP_OPACITY_MASK')
    def graphs():
        return canonical_graph({p: source.graph(material, lib.get_material_property_input_node(
            material, getattr(unreal.MaterialProperty, p))) for p in protected})
    protected_before = graphs()
    inputs = source.links(material, authority)
    texture = lib.create_material_expression(material, unreal.MaterialExpressionTextureObjectParameter)
    texture.set_editor_property('parameter_name', 'StatefulFoamFlowTexture')
    texture.set_editor_property('texture', inputs['Texture'].get_editor_property('texture'))
    texture.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    flow = lib.create_material_expression(material, unreal.MaterialExpressionCustom)
    flow.set_editor_property('desc', 'SouthForkPairedFoamFlowV1')
    flow.set_editor_property('code', CODE)
    flow.set_editor_property('include_file_paths', [INCLUDE])
    flow.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT2)
    connections = dict(CPUFlow=old_flow, FlowTexture=texture,
                       **{k: inputs[k] for k in ('Texture', 'World', 'Sign', 'Enable')})
    pins = []
    for name in connections:
        pin = unreal.CustomInput(); pin.set_editor_property('input_name', name); pins.append(pin)
    flow.set_editor_property('inputs', pins)
    for name, node in connections.items():
        assert lib.connect_material_expressions(node, '', flow, name)
    assert lib.connect_material_expressions(flow, '', coverage, 'FrothFlow')
    for node in nodes:
        expected = before[node.get_name()].copy()
        if node == coverage:
            expected['inputs'] = dict(expected['inputs'], FrothFlow=flow.get_name())
        assert canonical_graph(source.graph(material, node)[node.get_name()]) == canonical_graph(expected), node.get_name()
    assert graphs() == protected_before
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    if not install:
        assert source.sha(source.FILE) == before_hash
    destination = source.PATH if install else DEST
    with report.open('x', encoding='utf-8') as output:
        json.dump(dict(material=destination, source_sha256=before_hash, source_unchanged=not install,
            backup=str(backup) if install else None,
            material_sha256=source.sha(source.ROOT/'unreal/Content'/(destination.removeprefix('/Game/')+'.uasset')),
            helper_sha256=source.sha(source.ROOT/'unreal/Plugins/RaftSim/Shaders/Private/RaftSimRegisteredFoamFlow.ush'),
            all_old_nodes_exact_except_coverage_flow_input=True, protected_graphs=protected_before,
            flow_graph=canonical_graph(source.graph(material, flow)),
            visual_accepted=False, physical_accepted=False, release_accepted=False), output, indent=2)
    unreal.log('Paired optical flow material saved: '+str(report))


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
