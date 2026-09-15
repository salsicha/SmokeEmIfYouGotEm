"""Guarded combined irregular coverage/lit normal experiment, not acceptance.

Restore outside Unreal with raftsim_restore_material_backup.py, then fresh-audit.
"""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import integrate_south_fork_froth_micro_normal as micro
from raftsim_material_graph_signature import canonical_graph

old = micro.old
ROOT = old.ROOT
REPORT = ROOT/'unreal/Saved/RaftSimValidation/south-fork-combined-froth-install-v1-20260915.json'
BACKUP = REPORT.with_suffix('.backup.zip')
IRREGULAR = ROOT/'unreal/Plugins/RaftSim/Shaders/Private/RaftSimIrregularFrothCells.ush'
IRREGULAR_SHA = '0af97a746e2f79a3b77c55609cb7694f309f5ca968d1cbbf3f8be436996dd04e'
MARKER = 'SouthForkCombinedFrothNormalV1'


def main():
    command = unreal.SystemLibrary.get_command_line()
    lib = unreal.MaterialEditingLibrary
    material = unreal.load_asset(old.PATH)
    assert material and material.get_editor_property('tangent_space_normal')
    protection = json.loads((ROOT/'unreal/Saved/RaftSimValidation/south-fork-carrier-ground-v2-20260914.json').read_text())
    protected = dict(protection['protected_sha256'])
    protected.update({str(ROOT/'unreal/Content'/(p.removeprefix('/Game/')+'.uasset')):h
        for p,h in protection['protected_actor_packages'].items()})
    for p,h in protected.items():
        assert old.sha(Path(p)) == h, p
    before = micro.graphs(material)
    if 'RaftSimAuditCombinedFroth' in command or 'RaftSimAuditRestoredCombinedFroth' in command:
        restored = 'RaftSimAuditRestoredCombinedFroth' in command
        expected = json.loads((REPORT.with_name('south-fork-combined-froth-restored-v1-20260915.json') if restored else REPORT).read_text())
        output = REPORT.with_name('south-fork-combined-froth-'+('restored-' if restored else '')+'fresh-v1-20260915.json')
        assert not output.exists() and old.sha(old.FILE) == expected['material_sha256']
        assert canonical_graph(before) == canonical_graph(expected['saved_graphs'])
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        assert old.sha(old.FILE) == expected['material_sha256']
        output.write_text(json.dumps(dict(read_only=True, restored=restored, eight_graphs_exact=True,
            protected_files=len(protected), material_sha256=old.sha(old.FILE), visual_or_physical_accepted=False), indent=2)+'\n')
        return
    assert 'RaftSimInstallCombinedFroth' in command
    assert old.sha(old.FILE) == micro.BASELINE and not REPORT.exists() and not BACKUP.exists()
    assert old.sha(micro.HELPER) == micro.QUALIFIED_HELPER and old.sha(IRREGULAR) == IRREGULAR_SHA
    native_path = ROOT/'tmp/combined-froth-native-v1-20260915/index.json'
    native = json.loads(native_path.read_text(encoding='utf-8-sig'))
    assert native['failed'] == 0 and native['succeeded'] == 6 and native['notRun'] == 0
    assert {t['fullTestPath'] for t in native['tests'] if t['state'] == 'Success'} == {
        'RaftSim.WaterDetail.FrothMicroNormalGPU', 'RaftSim.WaterDetail.IrregularFrothGPU',
        'RaftSim.WaterDetail.FoamCoverageOpticsGPU','RaftSim.WaterDetail.RegisteredFoamClockGPU',
        'RaftSim.Water.FoamCommittedEvolution','RaftSim.M4.ShorelineFineCrest'}
    baseline = json.loads(micro.REPORT.read_text())
    assert canonical_graph(before) == canonical_graph(baseline['original_graphs'])
    nodes = list(lib.get_material_expressions(material))
    assert not any(n.get_editor_property('desc') in (MARKER, micro.MARKER) for n in nodes)
    coverage, = [n for n in nodes if n.get_editor_property('desc') == 'SouthForkTransportedFoamOpticsV1']
    inputs = old.links(material, coverage)
    assert inputs['VertexFoam'].get_editor_property('desc') == 'SouthForkMovingFoamAuthorityV1'
    assert inputs['FrothTime'].get_editor_property('desc') == 'SouthForkCommittedFrothTimeV1'
    assert inputs['FrothFlow'].get_editor_property('coordinate_index') == 3
    consumers = [n.get_name() for n in nodes if coverage in old.links(material,n).values()]
    assert len(consumers) == 4
    originals = {n.get_name(): old.graph(material,n)[n.get_name()] for n in nodes}
    with zipfile.ZipFile(BACKUP,'x',zipfile.ZIP_DEFLATED) as archive:
        archive.write(old.FILE,old.FILE.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(BACKUP) as archive:
        assert hashlib.sha256(archive.read(old.FILE.relative_to(ROOT).as_posix())).hexdigest() == micro.BASELINE
    code = IRREGULAR.read_text()+'\nfloat2 worldM=(FrothUV+FrothOrigin.xy)*3;\nfloat footprintM=max(length(ddx(worldM)),length(ddy(worldM)));\nRaftSimFrothCells cells; return cells.Sample(VertexFoam.r,OpticalDensity,worldM,FrothFlow.xy,FrothTime,footprintM);\n'
    coverage.set_editor_property('code',code)
    base = lib.get_material_property_input_node(material,unreal.MaterialProperty.MP_NORMAL)
    detail = lib.create_material_expression(material,unreal.MaterialExpressionCustom)
    detail.set_editor_property('desc',MARKER)
    detail.set_editor_property('code',micro.CODE)
    detail.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    sources = dict(BaseNormalTS=base,Coverage=coverage,**{key:inputs[key] for key in ('FrothUV','FrothOrigin','FrothFlow','FrothTime')})
    pins=[]
    for name in sources:
        pin=unreal.CustomInput();pin.set_editor_property('input_name',name);pins.append(pin)
    detail.set_editor_property('inputs',pins)
    for name,node in sources.items():
        assert lib.connect_material_expressions(node,'',detail,name)
    assert lib.connect_material_property(detail,'',unreal.MaterialProperty.MP_NORMAL)
    for node in nodes:
        expected=originals[node.get_name()].copy()
        if node == coverage: expected['code']=code
        assert old.graph(material,node)[node.get_name()] == expected, node.get_name()
    after=micro.graphs(material)
    for name in micro.PROPERTIES:
        expected=canonical_graph(before[name])
        if coverage.get_name() in expected: expected[coverage.get_name()]['code']=code
        assert expected == canonical_graph(after[name]), name
    assert [n.get_name() for n in nodes if coverage in old.links(material,n).values()] == consumers
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert unreal.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False)
    for p,h in protected.items(): assert old.sha(Path(p)) == h,p
    REPORT.write_text(json.dumps(dict(material=old.PATH,material_sha256=old.sha(old.FILE),
        original_graphs=before,saved_graphs=after,native_report_sha256=old.sha(native_path),
        normal_helper_sha256=old.sha(micro.HELPER),coverage_helper_sha256=old.sha(IRREGULAR),
        original_optical_consumers=consumers,protected_files=len(protected),
        only_coverage_code_and_normal_output_changed=True,visual_or_physical_accepted=False),indent=2)+'\n')


if __name__ == '__main__':
    try: main()
    finally: unreal.SystemLibrary.quit_editor()
