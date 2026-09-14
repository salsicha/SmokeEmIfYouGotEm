"""Guarded, coverage-preserving narrower foam borders on the playable parent."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import integrate_south_fork_local_froth as old
from integrate_south_fork_coverage_preserving_froth import graphs
from raftsim_material_graph_signature import canonical_graph
ROOT = old.ROOT
BASELINE = '26aa5029c579afad38fd603f96df9da304bd32ed338097d2580c9a29545ea82a'
REPORT = ROOT/'unreal/Saved/RaftSimValidation/south-fork-filtered-froth-install-v1-20260912.json'
BACKUP = REPORT.with_suffix('.backup.zip')
HELPER = ROOT/'unreal/Plugins/RaftSim/Shaders/Private/RaftSimFilteredFrothCells.ush'
CODE = HELPER.read_text()+'\nfloat2 worldM=(FrothUV+FrothOrigin.xy)*3;\nfloat footprintM=max(length(ddx(worldM)),length(ddy(worldM)));\nRaftSimFrothCells cells; return cells.Sample(VertexFoam.r,OpticalDensity,worldM,FrothFlow.xy,FrothTime,footprintM);\n'


def main():
    lib = unreal.MaterialEditingLibrary
    material = unreal.load_asset(old.PATH)
    assert material
    nodes = list(lib.get_material_expressions(material))
    coverage, = [n for n in nodes if n.get_editor_property('desc') == 'SouthForkTransportedFoamOpticsV1']
    if 'RaftSimAuditFilteredFroth' in unreal.SystemLibrary.get_command_line():
        expected = json.loads(REPORT.read_text())
        assert old.sha(old.FILE) == expected['material_sha256']
        assert coverage.get_editor_property('code') == CODE
        assert canonical_graph(graphs(material)) == canonical_graph(expected['saved_graphs'])
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        assert old.sha(old.FILE) == expected['material_sha256']
        commandlet = 'RaftSimAuditFilteredFrothCommandlet' in unreal.SystemLibrary.get_command_line()
        output = REPORT.with_name('south-fork-filtered-froth-fresh-'+('v2' if commandlet else 'v1')+'-20260912.json')
        assert not output.exists()
        output.write_text(json.dumps(dict(read_only=True, all_six_graphs_exact=True,
            material_sha256=old.sha(old.FILE), visual_accepted=False), indent=2)+'\n')
        return
    assert 'RaftSimIntegrateFilteredFroth' in unreal.SystemLibrary.get_command_line()
    assert old.sha(old.FILE) == BASELINE and not REPORT.exists() and not BACKUP.exists()
    before = graphs(material)
    node_before = {n.get_name(): old.graph(material, n)[n.get_name()] for n in nodes}
    consumers = [n.get_name() for n in nodes if coverage in old.links(material, n).values()]
    assert len(consumers) == 4
    assert old.links(material, coverage)['FrothFlow'].get_editor_property('coordinate_index') == 3
    protected = [ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap',
        ROOT/'unreal/Saved/SaveGames/RaftSimVerticalSlice.sav',
        ROOT/'unreal/Content/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround.uasset']
    protected += list((ROOT/'unreal/Content/__ExternalActors__/RaftSim/Maps/L_SouthForkAmerican_FullReach').rglob('*.uasset'))
    hashes = {p: old.sha(p) for p in protected}
    with zipfile.ZipFile(BACKUP, 'x', zipfile.ZIP_DEFLATED) as archive:
        archive.write(old.FILE, old.FILE.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(BACKUP) as archive:
        assert hashlib.sha256(archive.read(old.FILE.relative_to(ROOT).as_posix())).hexdigest() == BASELINE
    coverage.set_editor_property('code', CODE)
    for node in nodes:
        expected = node_before[node.get_name()].copy()
        if node == coverage:
            expected['code'] = CODE
        assert old.graph(material, node)[node.get_name()] == expected, node.get_name()
    after = graphs(material)
    for key in ('MP_WORLD_POSITION_OFFSET', 'MP_NORMAL', 'MP_OPACITY_MASK'):
        assert canonical_graph(before[key]) == canonical_graph(after[key]), key
    assert [n.get_name() for n in nodes if coverage in old.links(material, n).values()] == consumers
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    for p, digest in hashes.items():
        assert old.sha(p) == digest, str(p)
    REPORT.write_text(json.dumps(dict(material=old.PATH, previous_sha256=BASELINE,
        material_sha256=old.sha(old.FILE), helper_sha256=old.sha(HELPER), backup_sha256=old.sha(BACKUP),
        protected_file_count=len(hashes), all_other_nodes_exact=True, optical_consumers=consumers,
        saved_graphs=graphs(material), visual_accepted=False, physical_accepted=False), indent=2)+'\n')


if __name__ == '__main__':
    try:
        main()
    finally:
        # Python commandlets exit normally when the script returns. Do not
        # request an interactive editor shutdown from that execution mode.
        if '-run=pythonscript' not in unreal.SystemLibrary.get_command_line().lower():
            unreal.SystemLibrary.quit_editor()
