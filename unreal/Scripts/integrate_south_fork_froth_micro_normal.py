"""Guarded normal-only candidate install, fresh audit and semantic restoration."""
import json
from pathlib import Path
import sys
import zipfile
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import integrate_south_fork_local_froth as old
from raftsim_material_graph_signature import canonical_graph

ROOT = old.ROOT
BASELINE = '44c07f419a3a0a9f27f420871e4f1594184e57476de0960e560337ce6a93b31d'
HELPER = ROOT/'unreal/Plugins/RaftSim/Shaders/Private/RaftSimFrothMicroNormal.ush'
QUALIFIED_HELPER = '03e410a33c5be1bccfae38896320d9613fd2875855e6687347f4428971255767'
REPORT = ROOT/'unreal/Saved/RaftSimValidation/south-fork-froth-micro-normal-install-v1-20260915.json'
BACKUP = REPORT.with_suffix('.backup.zip')
MARKER = 'SouthForkFrothMicroNormalV1'
CODE = HELPER.read_text()+'''
float2 worldM=(FrothUV+FrothOrigin.xy)*3;
float footprintM=max(length(ddx(worldM)),length(ddy(worldM)));
RaftSimFrothMicroNormal detail;
return detail.Sample(BaseNormalTS,Coverage,worldM,FrothFlow.xy,FrothTime,footprintM);
'''
PROPERTIES = ('MP_WORLD_POSITION_OFFSET','MP_BASE_COLOR','MP_ROUGHNESS','MP_SPECULAR',
              'MP_OPACITY','MP_OPACITY_MASK','MP_EMISSIVE_COLOR')


def graphs(material):
    lib = unreal.MaterialEditingLibrary
    return {name: old.graph(material, lib.get_material_property_input_node(material, getattr(unreal.MaterialProperty, name)))
            for name in (*PROPERTIES, 'MP_NORMAL')}


def main():
    lib = unreal.MaterialEditingLibrary
    command = unreal.SystemLibrary.get_command_line()
    material = unreal.load_asset(old.PATH)
    assert material and material.get_editor_property('tangent_space_normal')
    nodes = list(lib.get_material_expressions(material))
    coverage, = [n for n in nodes if n.get_editor_property('desc') == 'SouthForkTransportedFoamOpticsV1']
    inputs = old.links(material, coverage)
    assert inputs['VertexFoam'].get_editor_property('desc') == 'SouthForkMovingFoamAuthorityV1'
    assert inputs['FrothTime'].get_editor_property('desc') == 'SouthForkCommittedFrothTimeV1'
    assert inputs['FrothFlow'].get_editor_property('coordinate_index') == 3
    protected_report = json.loads((ROOT/'unreal/Saved/RaftSimValidation/south-fork-carrier-ground-v2-20260914.json').read_text())
    protected = dict(protected_report['protected_sha256'])
    protected.update({str(ROOT/'unreal/Content'/(name.removeprefix('/Game/')+'.uasset')): digest
                      for name, digest in protected_report['protected_actor_packages'].items()})
    for path, digest in protected.items():
        assert old.sha(Path(path)) == digest, path
    before = graphs(material)
    if 'RaftSimAuditFrothMicroNormal' in command or 'RaftSimAuditRestoredFrothMicroNormal' in command:
        restored = 'RaftSimAuditRestoredFrothMicroNormal' in command
        expected = json.loads((REPORT.with_name('south-fork-froth-micro-normal-restored-v1-20260915.json') if restored else REPORT).read_text())
        output = REPORT.with_name('south-fork-froth-micro-normal-'+('restored-' if restored else '')+'fresh-v1-20260915.json')
        assert not output.exists() and old.sha(old.FILE) == expected['material_sha256']
        assert canonical_graph(before) == canonical_graph(expected['saved_graphs'])
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        assert old.sha(old.FILE) == expected['material_sha256']
        output.write_text(json.dumps(dict(read_only=True, restored=restored, eight_graphs_exact=True,
            material_sha256=old.sha(old.FILE), visual_or_physical_accepted=False), indent=2)+'\n')
        return
    restore = 'RaftSimRestoreFrothMicroNormal' in command
    old_nodes = {n.get_name(): old.graph(material,n)[n.get_name()] for n in nodes}
    if restore:
        expected = json.loads(REPORT.read_text())
        assert old.sha(old.FILE) == expected['material_sha256']
        assert canonical_graph(before) == canonical_graph(expected['saved_graphs'])
        detail, = [n for n in nodes if n.get_editor_property('desc') == MARKER]
        base = old.links(material, detail)['BaseNormalTS']
        assert lib.connect_material_property(base,'',unreal.MaterialProperty.MP_NORMAL)
        lib.delete_material_expression(material,detail)
        output = REPORT.with_name('south-fork-froth-micro-normal-restored-v1-20260915.json')
        assert not output.exists()
        assert canonical_graph(graphs(material)) == canonical_graph(expected['original_graphs'])
    else:
        assert 'RaftSimInstallFrothMicroNormal' in command
        native = json.loads((ROOT/'tmp/froth-micro-normal-native-v1-20260915/index.json').read_text(encoding='utf-8-sig'))
        assert native['failed'] == 0 and native['succeeded'] == 5 and native['notRun'] == 0
        assert {t['fullTestPath'] for t in native['tests'] if t['state'] == 'Success'} == {
            'RaftSim.WaterDetail.FrothMicroNormalGPU','RaftSim.WaterDetail.FoamCoverageOpticsGPU',
            'RaftSim.WaterDetail.RegisteredFoamClockGPU','RaftSim.Water.FoamCommittedEvolution','RaftSim.M4.ShorelineFineCrest'}
        assert old.sha(HELPER) == QUALIFIED_HELPER
        assert old.sha(old.FILE) == BASELINE and not REPORT.exists() and not BACKUP.exists()
        assert not any(n.get_editor_property('desc') == MARKER for n in nodes)
        base = lib.get_material_property_input_node(material,unreal.MaterialProperty.MP_NORMAL)
        assert base.get_editor_property('desc') == 'SouthForkCurrentGradientNormalV1'
        with zipfile.ZipFile(BACKUP,'x',zipfile.ZIP_DEFLATED) as archive:
            archive.write(old.FILE,old.FILE.relative_to(ROOT).as_posix())
        detail = lib.create_material_expression(material,unreal.MaterialExpressionCustom)
        detail.set_editor_property('desc',MARKER)
        detail.set_editor_property('code',CODE)
        detail.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT3)
        sources = dict(BaseNormalTS=base,Coverage=coverage,**{key: inputs[key] for key in ('FrothUV','FrothOrigin','FrothFlow','FrothTime')})
        pins = []
        for name in sources:
            pin=unreal.CustomInput();pin.set_editor_property('input_name',name);pins.append(pin)
        detail.set_editor_property('inputs',pins)
        for name, node in sources.items():
            assert lib.connect_material_expressions(node,'',detail,name)
        assert lib.connect_material_property(detail,'',unreal.MaterialProperty.MP_NORMAL)
        for node in nodes:
            assert old.graph(material,node)[node.get_name()] == old_nodes[node.get_name()], node.get_name()
        output = REPORT
    after = graphs(material)
    for name in PROPERTIES:
        assert canonical_graph(before[name]) == canonical_graph(after[name]), name
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert unreal.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False)
    for path, digest in protected.items():
        assert old.sha(Path(path)) == digest, path
    output.write_text(json.dumps(dict(material=old.PATH, restored=restore, material_sha256=old.sha(old.FILE),
        helper_sha256=old.sha(HELPER),original_graphs=before,saved_graphs=after,protected_files=len(protected),
        only_normal_output_changed=True, existing_nodes_unchanged=not restore, visual_or_physical_accepted=False),indent=2)+'\n')


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
