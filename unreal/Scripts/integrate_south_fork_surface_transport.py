"""Bind only local optical detail to effective foam-backtrace UV3."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import integrate_south_fork_local_normals as normals
from raftsim_material_graph_signature import canonical_graph

foam = normals.foam
ROOT = foam.ROOT
BASELINE = '3733e083d8e388227c82442cfbfcdc1b95a6eac8eb666ef6d9832796c3d23d4b'
REPORT = ROOT/'unreal/Saved/RaftSimValidation/south-fork-surface-transport-integration-v1-20260912.json'
FRESH = REPORT.with_name('south-fork-surface-transport-fresh-v1-20260912.json')
BACKUP = REPORT.with_name('south-fork-before-surface-transport-v1-20260912.zip')
MARKERS = {'SouthForkCurrentGradientNormalV1','SouthForkLocalFoamLaceV1'}


def normalized_graphs(material):
    nodes = list(unreal.MaterialEditingLibrary.get_material_expressions(material))
    customs = [n for n in nodes if n.get_editor_property('desc') in MARKERS]
    assert len(customs) == 2
    flow_nodes = {foam.links(material,n)['Flow'].get_name() for n in customs}
    assert len(flow_nodes) == 2
    graphs = dict(optics=normals.protected_graphs(material),normal=canonical_graph(foam.graph(material,
        unreal.MaterialEditingLibrary.get_material_property_input_node(material,unreal.MaterialProperty.MP_NORMAL))))
    def walk(value):
        if not isinstance(value,dict):
            return value
        result = {}
        for key,item in value.items():
            if key in flow_nodes:
                item = dict(item)
                assert item['coordinate_index'] in ('1','3')
                item['coordinate_index'] = 'AUTHORIZED_OPTICAL_FLOW_CHANNEL'
            if key == 'code' and isinstance(item,str):
                item = '\n'.join(line for line in item.splitlines() if not line.lstrip().startswith('//'))
            result[key] = walk(item)
        return result
    return walk(graphs)


def physics_graphs(material):
    lib = unreal.MaterialEditingLibrary
    return canonical_graph({name:foam.graph(material,lib.get_material_property_input_node(
        material,getattr(unreal.MaterialProperty,name))) for name in ('MP_WORLD_POSITION_OFFSET','MP_OPACITY_MASK')})


def main():
    command = unreal.SystemLibrary.get_command_line()
    audit = 'RaftSimAuditSurfaceTransport' in command
    assert audit or 'RaftSimIntegrateSurfaceTransport' in command
    if audit:
        assert not FRESH.exists()
        previous = json.loads(REPORT.read_text())
        assert foam.sha(foam.FILE) == previous['material_sha256']
        assert {str(p.relative_to(ROOT)):foam.sha(p) for p in (foam.SHADER,normals.SHADER)} == previous['shader_sha256']
        result = normals.verify(unreal.load_asset(foam.PATH),flow_index=3)
        assert result == previous['verified']
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        assert foam.sha(foam.FILE) == previous['material_sha256']
        FRESH.write_text(json.dumps(dict(verified=result,material_sha256=previous['material_sha256'],
            fresh_process=True,read_only=True,visual_accepted=False),indent=2)+'\n')
        unreal.log(f'Fresh surface-transport material audit passes: {FRESH}')
        return
    assert not REPORT.exists() and not BACKUP.exists() and foam.sha(foam.FILE) == BASELINE
    material = unreal.load_asset(foam.PATH)
    before,physics = normalized_graphs(material),physics_graphs(material)
    # UV3 was unused by protected geometry/coverage branches before this change.
    assert not any(row.get('coordinate_index') == '3' for graph in physics.values() for row in graph.values())
    count = len(unreal.MaterialEditingLibrary.get_material_expressions(material))
    protected_files = [ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap',
        ROOT/'unreal/Saved/SaveGames/RaftSimVerticalSlice.sav',
        ROOT/'unreal/Content/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround.uasset']
    protected_files += list((ROOT/'unreal/Content/__ExternalActors__/RaftSim/Maps/L_SouthForkAmerican_FullReach').rglob('*.uasset'))
    hashes = {p:foam.sha(p) for p in protected_files}
    with zipfile.ZipFile(BACKUP,'x',zipfile.ZIP_DEFLATED) as archive:
        archive.write(foam.FILE,foam.FILE.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(BACKUP) as archive:
        assert hashlib.sha256(archive.read(foam.FILE.relative_to(ROOT).as_posix())).hexdigest() == BASELINE
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.SystemLibrary.execute_console_command(world,'RaftSim.RefreshSouthForkCurrentNormals')
    result = normals.verify(material,flow_index=3)
    assert normalized_graphs(material) == before
    assert physics_graphs(material) == physics
    assert len(unreal.MaterialEditingLibrary.get_material_expressions(material)) == count
    unreal.SystemLibrary.execute_console_command(world,'RaftSim.RefreshSouthForkCurrentNormals')
    assert normals.verify(material,flow_index=3) == result
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert unreal.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False)
    for p,digest in hashes.items():
        assert foam.sha(p) == digest, str(p)
    REPORT.write_text(json.dumps(dict(verified=result,material_before_sha256=BASELINE,
        material_sha256=foam.sha(foam.FILE),shader_sha256={str(p.relative_to(ROOT)):foam.sha(p) for p in (foam.SHADER,normals.SHADER)},
        only_two_optical_flow_channels_and_comments_changed=True,geometry_and_coverage_graphs_exact=True,
        map_actors_ground_profile_unchanged=True,refresh_idempotent=True,backup_sha256=foam.sha(BACKUP),
        visual_accepted=False),indent=2)+'\n')
    unreal.log(f'Surface-transport material migration verified: {REPORT}')


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
