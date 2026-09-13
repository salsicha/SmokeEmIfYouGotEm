"""Guarded two-shader optical renewal revision; fresh audit uses same script."""
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
BASELINE = '55c30b54276dfbab3356c2712bfe112c6b449daa35fb8d02c2c105cfe58d03fc'
REPORT = ROOT/'unreal/Saved/RaftSimValidation/south-fork-short-flow-integration-v1-20260912.json'
FRESH = REPORT.with_name('south-fork-short-flow-fresh-v1-20260912.json')
BACKUP = REPORT.with_name('south-fork-before-short-flow-v1-20260912.zip')


def protected(material):
    # Only the two explicitly named custom shader bodies may change anywhere
    # in these dependency graphs. All other code, values and links must match.
    graph = dict(optics=normals.protected_graphs(material), normal=canonical_graph(foam.graph(material,
        unreal.MaterialEditingLibrary.get_material_property_input_node(material, unreal.MaterialProperty.MP_NORMAL))))
    nodes = {n.get_name():n for n in unreal.MaterialEditingLibrary.get_material_expressions(material)}
    def walk(value):
        if not isinstance(value, dict):
            return value
        result = {}
        for key, item in value.items():
            if key in nodes and nodes[key].get_editor_property('desc') in (
                    'SouthForkCurrentGradientNormalV1', 'SouthForkLocalFoamLaceV1'):
                item = dict(item)
                item['code'] = 'ONLY_AUTHORIZED_SHADER_BODY'
            result[key] = walk(item)
        return result
    return walk(graph)


def main():
    command = unreal.SystemLibrary.get_command_line()
    audit = 'RaftSimAuditShortFlow' in command
    assert audit or 'RaftSimIntegrateShortFlow' in command
    if audit:
        assert not FRESH.exists()
        previous = json.loads(REPORT.read_text())
        assert foam.sha(foam.FILE) == previous['material_sha256']
        assert {str(p.relative_to(ROOT)):foam.sha(p) for p in (foam.SHADER,normals.SHADER)} == previous['shader_sha256']
        result = normals.verify(unreal.load_asset(foam.PATH))
        assert result == previous['verified']
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        assert foam.sha(foam.FILE) == previous['material_sha256']
        FRESH.write_text(json.dumps(dict(verified=result, fresh_process=True, read_only=True,
            material_sha256=previous['material_sha256'], visual_accepted=False),indent=2)+'\n')
        unreal.log(f'Fresh short local-flow audit passes: {FRESH}')
        return
    assert not REPORT.exists() and not BACKUP.exists() and foam.sha(foam.FILE) == BASELINE
    old = json.loads(normals.REPORT.read_text())
    material = unreal.load_asset(foam.PATH)
    before = protected(material)
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
    result = normals.verify(material)
    assert protected(material) == before
    assert result['local_foam']['expression_count'] == old['verified']['local_foam']['expression_count']
    unreal.SystemLibrary.execute_console_command(world,'RaftSim.RefreshSouthForkCurrentNormals')
    assert normals.verify(material) == result and protected(material) == before
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert unreal.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False)
    for p,digest in hashes.items():
        assert foam.sha(p) == digest, str(p)
    REPORT.write_text(json.dumps(dict(verified=result, material_before_sha256=BASELINE,
        material_sha256=foam.sha(foam.FILE), shader_sha256={str(p.relative_to(ROOT)):foam.sha(p) for p in (foam.SHADER,normals.SHADER)},
        only_two_shader_bodies_changed=True, parameters_links_physics_assets_profile_unchanged=True,
        refresh_idempotent=True, backup_sha256=foam.sha(BACKUP), optical_renewal_seconds=1,
        visual_accepted=False),indent=2)+'\n')
    unreal.log(f'Short local-flow renewal verified: {REPORT}')


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
