"""Install the displayed-frame froth clock, preserving water/contact graphs."""
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
REPORT = ROOT/'unreal/Saved/RaftSimValidation/south-fork-committed-froth-install-v1-20260913.json'
BACKUP = REPORT.with_suffix('.backup.zip')
INCLUDE = '/Plugin/RaftSimWaterDetail/Private/RaftSimRegisteredFoamTime.ush'
CODE = 'return RaftSimRegisteredFoamPhase(Texture,World.xy*float2(.01,.01*Sign),CPUClock.xy,Enable);'


def main():
    lib = unreal.MaterialEditingLibrary
    material = unreal.load_asset(old.PATH)
    nodes = list(lib.get_material_expressions(material))
    coverage, = [n for n in nodes if n.get_editor_property('desc') == 'SouthForkTransportedFoamOpticsV1']
    lace, = [n for n in nodes if n.get_editor_property('desc') == 'SouthForkLocalFoamLaceV1']
    authority, = [n for n in nodes if n.get_editor_property('desc') == 'SouthForkMovingFoamAuthorityV1']
    command = unreal.SystemLibrary.get_command_line()
    if 'RaftSimAuditCommittedFroth' in command:
        expected = json.loads(REPORT.read_text())
        assert old.sha(old.FILE) == expected['material_sha256']
        clock, = [n for n in nodes if n.get_editor_property('desc') == 'SouthForkCommittedFrothTimeV1']
        assert old.links(material, coverage)['FrothTime'] == clock
        assert old.links(material, lace)['TimeSeconds'] == clock
        assert clock.get_editor_property('code') == CODE
        assert list(clock.get_editor_property('include_file_paths')) == [INCLUDE]
        assert canonical_graph(graphs(material)) == canonical_graph(expected['saved_graphs'])
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        assert old.sha(old.FILE) == expected['material_sha256']
        output = REPORT.with_name('south-fork-committed-froth-fresh-v1-20260913.json')
        assert not output.exists()
        output.write_text(json.dumps(dict(read_only=True, all_six_graphs_exact=True,
            material_sha256=old.sha(old.FILE), visual_accepted=False), indent=2)+'\n')
        return
    assert 'RaftSimIntegrateCommittedFroth' in command
    assert old.sha(old.FILE) == BASELINE and not REPORT.exists() and not BACKUP.exists()
    assert old.links(material, coverage)['FrothTime'].get_class().get_name() == 'MaterialExpressionTime'
    before = graphs(material)
    node_before = {n.get_name(): old.graph(material, n)[n.get_name()] for n in nodes}
    consumers = [n.get_name() for n in nodes if coverage in old.links(material, n).values()]
    assert len(consumers) == 4
    source = old.links(material, authority)
    assert all(source[k] for k in ('Texture', 'World', 'Sign', 'Enable'))
    protected = [ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap',
        ROOT/'unreal/Saved/SaveGames/RaftSimVerticalSlice.sav',
        ROOT/'unreal/Content/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround.uasset']
    protected += list((ROOT/'unreal/Content/__ExternalActors__/RaftSim/Maps/L_SouthForkAmerican_FullReach').rglob('*.uasset'))
    hashes = {p: old.sha(p) for p in protected}
    with zipfile.ZipFile(BACKUP, 'x', zipfile.ZIP_DEFLATED) as archive:
        archive.write(old.FILE, old.FILE.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(BACKUP) as archive:
        assert hashlib.sha256(archive.read(old.FILE.relative_to(ROOT).as_posix())).hexdigest() == BASELINE
    cpu = lib.create_material_expression(material, unreal.MaterialExpressionVectorParameter, -1600, 1400)
    cpu.set_editor_property('parameter_name', 'RaftSimCPUFoamClock')
    cpu.set_editor_property('default_value', unreal.LinearColor(0, 0, 0, 0))
    clock = lib.create_material_expression(material, unreal.MaterialExpressionCustom, -1300, 1400)
    clock.set_editor_property('desc', 'SouthForkCommittedFrothTimeV1')
    clock.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    clock.set_editor_property('code', CODE)
    clock.set_editor_property('include_file_paths', [INCLUDE])
    inputs = []
    for name in ('CPUClock', 'Texture', 'World', 'Sign', 'Enable'):
        entry = unreal.CustomInput()
        entry.set_editor_property('input_name', name)
        inputs.append(entry)
    clock.set_editor_property('inputs', inputs)
    assert lib.connect_material_expressions(cpu, '', clock, 'CPUClock')
    for name in ('Texture', 'World', 'Sign', 'Enable'):
        assert lib.connect_material_expressions(source[name], '', clock, name)
    assert lib.connect_material_expressions(clock, '', coverage, 'FrothTime')
    assert lib.connect_material_expressions(clock, '', lace, 'TimeSeconds')
    for node in nodes:
        expected = node_before[node.get_name()].copy()
        if node in (coverage, lace):
            key = 'FrothTime' if node == coverage else 'TimeSeconds'
            expected['inputs'] = dict(expected['inputs'], **{key: clock.get_name()})
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
        material_sha256=old.sha(old.FILE), backup_sha256=old.sha(BACKUP),
        protected_file_count=len(hashes), all_other_nodes_exact=True,
        optical_consumers=consumers, saved_graphs=graphs(material),
        visual_accepted=False, physical_accepted=False), indent=2)+'\n')


if __name__ == '__main__':
    main()
