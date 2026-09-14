"""Guarded optical-only candidate install/readback/restore on playable South Fork."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import unreal

sys.path.insert(0,str(Path(__file__).resolve().parent))
import integrate_south_fork_local_froth as old
from integrate_south_fork_coverage_preserving_froth import graphs
from raftsim_material_graph_signature import canonical_graph

ROOT=old.ROOT
BASELINE='adb56123f1e07c7cdfe2f6cd0da2db1c2e44f12d8ebb147a640ad9899a73c0c3'
REPORT=ROOT/'unreal/Saved/RaftSimValidation/south-fork-irregular-froth-install-v1-20260914.json'
BACKUP=REPORT.with_suffix('.backup.zip')
HELPER=ROOT/'unreal/Plugins/RaftSim/Shaders/Private/RaftSimIrregularFrothCells.ush'
CODE=HELPER.read_text()+'\nfloat2 worldM=(FrothUV+FrothOrigin.xy)*3;\nfloat footprintM=max(length(ddx(worldM)),length(ddy(worldM)));\nRaftSimFrothCells cells; return cells.Sample(VertexFoam.r,OpticalDensity,worldM,FrothFlow.xy,FrothTime,footprintM);\n'


def main():
    command=unreal.SystemLibrary.get_command_line();lib=unreal.MaterialEditingLibrary
    material=unreal.load_asset(old.PATH);assert material
    nodes=list(lib.get_material_expressions(material))
    coverage,=[n for n in nodes if n.get_editor_property('desc')=='SouthForkTransportedFoamOpticsV1']
    clock,=[n for n in nodes if n.get_editor_property('desc')=='SouthForkCommittedFrothTimeV1']
    authority=old.links(material,coverage)['VertexFoam']
    assert authority.get_editor_property('desc')=='SouthForkMovingFoamAuthorityV1'
    assert old.links(material,coverage)['FrothTime']==clock
    consumers=[n.get_name() for n in nodes if coverage in old.links(material,n).values()]
    assert len(consumers)==4
    before=graphs(material)
    all_before={n.get_name():old.graph(material,n)[n.get_name()] for n in nodes}
    protected=[ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap',
        ROOT/'unreal/Saved/SaveGames/RaftSimVerticalSlice.sav',
        ROOT/'unreal/Content/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround.uasset']
    protected+=list((ROOT/'unreal/Content/__ExternalActors__/RaftSim/Maps/L_SouthForkAmerican_FullReach').rglob('*.uasset'))
    hashes={p:old.sha(p) for p in protected}
    if 'RaftSimAuditRestoredIrregularFroth' in command:
        installed=json.loads(REPORT.read_text())
        restored=json.loads(REPORT.with_name('south-fork-irregular-froth-restored-v1-20260914.json').read_text())
        fresh=REPORT.with_name('south-fork-irregular-froth-restored-fresh-v1-20260914.json')
        assert not fresh.exists() and restored['restored']
        assert old.sha(old.FILE)==restored['material_sha256']
        assert coverage.get_editor_property('code')==installed['original_code']
        assert canonical_graph(before)==canonical_graph(installed['original_graphs'])
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        assert old.sha(old.FILE)==restored['material_sha256']
        for path,sha in hashes.items():assert old.sha(path)==sha,str(path)
        fresh.write_text(json.dumps(dict(read_only=True,restored=True,
            all_six_original_graphs_exact=True,material_sha256=old.sha(old.FILE),
            protected_file_count=len(hashes),visual_or_physical_accepted=False),indent=2)+'\n');return
    if 'RaftSimAuditIrregularFroth' in command:
        expected=json.loads(REPORT.read_text());fresh=REPORT.with_name('south-fork-irregular-froth-fresh-v1-20260914.json')
        assert not fresh.exists() and old.sha(old.FILE)==expected['material_sha256']
        assert coverage.get_editor_property('code')==CODE
        assert canonical_graph(before)==canonical_graph(expected['saved_graphs'])
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        assert old.sha(old.FILE)==expected['material_sha256']
        fresh.write_text(json.dumps(dict(read_only=True,all_six_graphs_exact=True,
            source_clock_and_consumers_unchanged=True,material_sha256=old.sha(old.FILE),
            visual_or_physical_accepted=False),indent=2)+'\n');return
    restore='RaftSimRestoreIrregularFroth' in command
    if restore:
        expected=json.loads(REPORT.read_text())
        assert old.sha(old.FILE)==expected['material_sha256']
        assert canonical_graph(before)==canonical_graph(expected['saved_graphs'])
        desired=expected['original_code']
        output=REPORT.with_name('south-fork-irregular-froth-restored-v1-20260914.json')
        assert not output.exists()
    else:
        assert 'RaftSimInstallIrregularFroth' in command
        # Installation is forbidden until the actual GPU qualification passes.
        tests=json.loads((ROOT/'unreal/Saved/RaftSimValidation/irregular-froth-native-v4-20260914/index.json').read_text(encoding='utf-8-sig'))
        assert tests['failed']==0 and tests['succeeded']==4 and tests['notRun']==0
        assert {t['fullTestPath'] for t in tests['tests'] if t['state']=='Success'}=={
            'RaftSim.Water.FoamCommittedEvolution','RaftSim.WaterDetail.FoamCoverageOpticsGPU',
            'RaftSim.WaterDetail.IrregularFrothGPU','RaftSim.WaterDetail.RegisteredFoamClockGPU'}
        assert old.sha(HELPER)=='0af97a746e2f79a3b77c55609cb7694f309f5ca968d1cbbf3f8be436996dd04e'
        assert old.sha(old.FILE)==BASELINE and not REPORT.exists() and not BACKUP.exists()
        with zipfile.ZipFile(BACKUP,'x',zipfile.ZIP_DEFLATED) as archive:
            archive.write(old.FILE,old.FILE.relative_to(ROOT).as_posix())
        with zipfile.ZipFile(BACKUP) as archive:
            assert hashlib.sha256(archive.read(old.FILE.relative_to(ROOT).as_posix())).hexdigest()==BASELINE
        desired=CODE;output=REPORT
    original_code=coverage.get_editor_property('code');coverage.set_editor_property('code',desired)
    assert len(lib.get_material_expressions(material))==len(nodes)
    for n in nodes:
        expected_node=all_before[n.get_name()].copy()
        if n==coverage:expected_node['code']=desired
        assert old.graph(material,n)[n.get_name()]==expected_node,n.get_name()
    after=graphs(material)
    for key in ('MP_WORLD_POSITION_OFFSET','MP_NORMAL','MP_OPACITY_MASK'):
        assert canonical_graph(before[key])==canonical_graph(after[key]),key
    if restore:assert canonical_graph(after)==canonical_graph(expected['original_graphs'])
    assert [n.get_name() for n in nodes if coverage in old.links(material,n).values()]==consumers
    lib.recompile_material(material);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert unreal.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False)
    for path,sha in hashes.items():assert old.sha(path)==sha,str(path)
    output.write_text(json.dumps(dict(material=old.PATH,restored=restore,
        previous_sha256=expected['material_sha256'] if restore else BASELINE,
        material_sha256=old.sha(old.FILE),helper_sha256=old.sha(HELPER),
        original_code=original_code,original_graphs=before,saved_graphs=graphs(material),
        protected_file_count=len(hashes),source_clock_and_other_nodes_exact=True,
        optical_consumers=consumers,visual_or_physical_accepted=False),indent=2)+'\n')


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
