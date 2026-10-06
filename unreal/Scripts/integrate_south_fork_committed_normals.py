"""One existing playable normal-clock connection; preserve all other nodes."""
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
BASELINE = 'e0c9613bc16125c0f991dc29c6421359cd0fbd6903ab0481657ed544bca55f2c'
REPORT = ROOT/'unreal/Saved/RaftSimValidation/south-fork-committed-normal-install-v1-20260914.json'
BACKUP = REPORT.with_suffix('.backup.zip')
FRESH = REPORT.with_name('south-fork-committed-normal-fresh-v1-20260914.json')


def main():
    lib = unreal.MaterialEditingLibrary
    material = unreal.load_asset(old.PATH)
    assert material
    nodes = list(lib.get_material_expressions(material))
    normal, = [n for n in nodes if n.get_editor_property('desc') == 'SouthForkCurrentGradientNormalV1']
    clock, = [n for n in nodes if n.get_editor_property('desc') == 'SouthForkCommittedFrothTimeV1']
    lace, = [n for n in nodes if n.get_editor_property('desc') == 'SouthForkLocalFoamLaceV1']
    coverage, = [n for n in nodes if n.get_editor_property('desc') == 'SouthForkTransportedFoamOpticsV1']
    normal_root = lib.get_material_property_input_node(material, unreal.MaterialProperty.MP_NORMAL)
    assert normal.get_name() in old.graph(material, normal_root)
    # The saved parent composes this optical normal with registered detail.
    # Preserve that root and its other branch; only rewire the reachable clock.
    assert old.links(material, lace)['TimeSeconds'] == clock
    assert old.links(material, coverage)['FrothTime'] == clock
    command = unreal.SystemLibrary.get_command_line()
    if 'RaftSimAuditCommittedNormals' in command:
        expected = json.loads(REPORT.read_text())
        assert not FRESH.exists() and old.sha(old.FILE) == expected['material_sha256']
        assert old.links(material, normal)['TimeSeconds'] == clock
        assert canonical_graph(graphs(material)) == canonical_graph(expected['saved_graphs'])
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        assert old.sha(old.FILE) == expected['material_sha256']
        FRESH.write_text(json.dumps(dict(read_only=True, same_clock_for_normal_lace_coverage=True,
            all_six_saved_graphs_exact=True, material_sha256=old.sha(old.FILE),
            visual_or_physical_accepted=False), indent=2)+'\n')
        return
    assert 'RaftSimIntegrateCommittedNormals' in command
    assert old.sha(old.FILE) == BASELINE and not REPORT.exists() and not BACKUP.exists()
    assert old.links(material, normal)['TimeSeconds'].get_class().get_name() == 'MaterialExpressionTime'
    before = graphs(material)
    node_before = {n.get_name(): old.graph(material, n)[n.get_name()] for n in nodes}
    protected = [ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap',
        ROOT/'unreal/Saved/SaveGames/RaftSimVerticalSlice.sav',
        ROOT/'unreal/Content/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround.uasset']
    protected += list((ROOT/'unreal/Content/__ExternalActors__/RaftSim/Maps/L_SouthForkAmerican_FullReach').rglob('*.uasset'))
    hashes = {p: old.sha(p) for p in protected}
    with zipfile.ZipFile(BACKUP, 'x', zipfile.ZIP_DEFLATED) as archive:
        archive.write(old.FILE, old.FILE.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(BACKUP) as archive:
        assert hashlib.sha256(archive.read(old.FILE.relative_to(ROOT).as_posix())).hexdigest() == BASELINE
    assert lib.connect_material_expressions(clock, '', normal, 'TimeSeconds')
    assert len(lib.get_material_expressions(material)) == len(nodes)
    for node in nodes:
        expected = node_before[node.get_name()].copy()
        if node == normal:
            expected['inputs'] = dict(expected['inputs'], TimeSeconds=clock.get_name())
        assert old.graph(material, node)[node.get_name()] == expected, node.get_name()
    after = graphs(material)
    assert lib.get_material_property_input_node(material, unreal.MaterialProperty.MP_NORMAL) == normal_root
    for name in before:
        if name != 'MP_NORMAL': assert canonical_graph(before[name]) == canonical_graph(after[name]), name
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    for path, sha in hashes.items(): assert old.sha(path) == sha, str(path)
    REPORT.write_text(json.dumps(dict(material=old.PATH, previous_sha256=BASELINE,
        material_sha256=old.sha(old.FILE), backup_sha256=old.sha(BACKUP),
        protected_file_count=len(hashes), existing_nodes_unchanged_except_normal_time=True,
        new_expression_count=0, same_clock_for_normal_lace_coverage=True,
        saved_graphs=graphs(material), visual_or_physical_accepted=False), indent=2)+'\n')


if __name__ == '__main__':
    try: main()
    finally: unreal.SystemLibrary.quit_editor()
