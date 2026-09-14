"""Guarded optical-only correction on the current playable South Fork parent."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import integrate_south_fork_local_froth as old
from raftsim_material_graph_signature import canonical_graph

ROOT=old.ROOT
BASELINE='e4e9b2f331c702e09f3d7a01566440da4674b88e06f283e8aa41951ae023d4c3'
REPORT=ROOT/'unreal/Saved/RaftSimValidation/south-fork-coverage-froth-install-v1-20260912.json'
BACKUP=REPORT.with_suffix('.backup.zip')
HELPER=ROOT/'unreal/Plugins/RaftSim/Shaders/Private/RaftSimFoamCoverage.ush'
CODE=HELPER.read_text()+'\nRaftSimFoamCoverageOptics optics; return optics.Sample(VertexFoam.r,OpticalDensity,Lace);\n'


def graphs(material):
    lib=unreal.MaterialEditingLibrary
    return {name:old.graph(material,lib.get_material_property_input_node(material,getattr(unreal.MaterialProperty,name)))
            for name in ('MP_WORLD_POSITION_OFFSET','MP_NORMAL','MP_BASE_COLOR','MP_ROUGHNESS','MP_OPACITY','MP_OPACITY_MASK')}


def main():
    lib=unreal.MaterialEditingLibrary
    material=unreal.load_asset(old.PATH)
    assert material
    nodes=list(lib.get_material_expressions(material))
    coverage,=[n for n in nodes if n.get_editor_property('desc')=='SouthForkTransportedFoamOpticsV1']
    if 'RaftSimAuditCoverageFroth' in unreal.SystemLibrary.get_command_line():
        expected=json.loads(REPORT.read_text())
        assert old.sha(old.FILE)==expected['material_sha256']
        assert coverage.get_editor_property('code')==CODE
        assert canonical_graph(graphs(material))==canonical_graph(expected['saved_graphs'])
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        assert old.sha(old.FILE)==expected['material_sha256']
        result=REPORT.with_name('south-fork-coverage-froth-fresh-v2-20260912.json')
        assert not result.exists()
        result.write_text(json.dumps(dict(read_only=True,all_six_graphs_exact=True,
            material_sha256=old.sha(old.FILE),visual_accepted=False),indent=2)+'\n')
        return
    assert 'RaftSimIntegrateCoverageFroth' in unreal.SystemLibrary.get_command_line()
    assert old.sha(old.FILE)==BASELINE and not REPORT.exists() and not BACKUP.exists()
    before=graphs(material)
    all_before={n.get_name():old.graph(material,n)[n.get_name()] for n in nodes}
    consumers=[n.get_name() for n in nodes if coverage in old.links(material,n).values()]
    assert len(consumers)==4
    authority=old.links(material,coverage)['VertexFoam']
    assert authority.get_editor_property('desc')=='SouthForkMovingFoamAuthorityV1'
    lace=old.links(material,coverage)['Lace']
    texture=old.links(material,lace)['LaceTexture'].get_editor_property('texture')
    assert not texture.get_editor_property('srgb'), 'Mean calibration needs linear lace'
    protected=[ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap',
               ROOT/'unreal/Saved/SaveGames/RaftSimVerticalSlice.sav',
               ROOT/'unreal/Content/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround.uasset']
    protected+=list((ROOT/'unreal/Content/__ExternalActors__/RaftSim/Maps/L_SouthForkAmerican_FullReach').rglob('*.uasset'))
    hashes={p:old.sha(p) for p in protected}
    with zipfile.ZipFile(BACKUP,'x',zipfile.ZIP_DEFLATED) as archive:
        archive.write(old.FILE,old.FILE.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(BACKUP) as archive:
        assert hashlib.sha256(archive.read(old.FILE.relative_to(ROOT).as_posix())).hexdigest()==BASELINE
    coverage.set_editor_property('code',CODE)
    for n in nodes:
        actual=old.graph(material,n)[n.get_name()]
        expected=all_before[n.get_name()].copy()
        if n==coverage:expected['code']=CODE
        assert actual==expected,n.get_name()
    after=graphs(material)
    for name in ('MP_WORLD_POSITION_OFFSET','MP_NORMAL','MP_OPACITY_MASK'):
        assert canonical_graph(before[name])==canonical_graph(after[name]),name
    assert [n.get_name() for n in nodes if coverage in old.links(material,n).values()]==consumers
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert unreal.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False)
    for path,digest in hashes.items():assert old.sha(path)==digest,str(path)
    REPORT.write_text(json.dumps(dict(material=old.PATH,previous_sha256=BASELINE,
        material_sha256=old.sha(old.FILE),helper_sha256=old.sha(HELPER),backup_sha256=old.sha(BACKUP),
        all_other_nodes_exact=True,protected_file_count=len(hashes),optical_consumers=consumers,
        texture_srgb=False,texture_compression=str(texture.get_editor_property('compression_settings')),
        saved_graphs=graphs(material),visual_accepted=False,physical_accepted=False),indent=2)+'\n')


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
