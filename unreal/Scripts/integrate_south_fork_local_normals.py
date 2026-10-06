"""Guarded normal-only local-current migration, with a fresh read-only mode."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import integrate_south_fork_local_froth as foam
from raftsim_material_graph_signature import canonical_graph

ROOT = foam.ROOT
BASELINE = 'd55e5cdc8831cf9c084f4e9516eff0f225fa0c6b76444722d4832e2b2a254c3b'
SHADER = ROOT/'unreal/Shaders/Private/RaftSimLocalCurrentNormal.hlsl'
REPORT = ROOT/'unreal/Saved/RaftSimValidation/south-fork-local-normal-integration-v1-20260912.json'
FRESH = REPORT.with_name('south-fork-local-normal-fresh-v1-20260912.json')
BACKUP = REPORT.with_name('south-fork-before-local-normal-v1-20260912.zip')


def protected_graphs(material):
    lib = unreal.MaterialEditingLibrary
    return canonical_graph({name: foam.graph(material, lib.get_material_property_input_node(
        material, getattr(unreal.MaterialProperty, name))) for name in (
        'MP_WORLD_POSITION_OFFSET', 'MP_OPACITY_MASK', 'MP_BASE_COLOR', 'MP_ROUGHNESS', 'MP_OPACITY')})


def verify(material, flow_index=1):
    lib = unreal.MaterialEditingLibrary
    normal = lib.get_material_property_input_node(material, unreal.MaterialProperty.MP_NORMAL)
    assert normal.get_editor_property('desc') == 'SouthForkCurrentGradientNormalV1'
    assert normal.get_editor_property('code') == SHADER.read_text()
    assert normal.get_editor_property('output_type') == unreal.CustomMaterialOutputType.CMOT_FLOAT3
    inputs = foam.links(material, normal)
    assert set(inputs) == {'UV', 'Origin', 'Foam', 'Strength', 'Flow', 'TimeSeconds'}
    assert inputs['UV'].get_editor_property('coordinate_index') == 0
    assert 'RaftSimFullPrecisionRiverUV' in inputs['UV'].get_editor_property('desc')
    assert inputs['Flow'].get_editor_property('coordinate_index') == flow_index
    assert inputs['TimeSeconds'].get_class().get_name() == 'MaterialExpressionTime'
    assert str(inputs['Origin'].get_editor_property('parameter_name')) == 'RaftSimWaterUVOrigin'
    assert str(inputs['Strength'].get_editor_property('parameter_name')) == 'SouthForkCurrentNormalStrength'
    assert abs(inputs['Strength'].get_editor_property('default_value')-.18) < 1.e-7
    graph = canonical_graph(foam.graph(material, normal))
    assert 'RaftSimFoamAdvectionMeters' not in str(graph)
    local_foam = canonical_graph(foam.verify(material, flow_index))
    return dict(normal_graph=graph, local_foam=local_foam,
                protected_graphs=protected_graphs(material))


def main():
    command = unreal.SystemLibrary.get_command_line()
    audit = 'RaftSimAuditLocalNormals' in command
    assert audit or 'RaftSimIntegrateLocalNormals' in command
    if audit:
        assert not FRESH.exists()
        previous = json.loads(REPORT.read_text())
        assert foam.sha(foam.FILE) == previous['material_sha256']
        assert foam.sha(SHADER) == previous['shader_sha256']
        material = unreal.load_asset(foam.PATH)
        result = verify(material)
        assert result == previous['verified']
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        assert foam.sha(foam.FILE) == previous['material_sha256']
        FRESH.write_text(json.dumps(dict(verified=result, material_sha256=previous['material_sha256'],
            fresh_process=True, read_only=True, visual_accepted=False), indent=2)+'\n')
        unreal.log(f'Fresh local-current normal audit passes: {FRESH}')
        return
    assert not REPORT.exists() and not BACKUP.exists() and foam.sha(foam.FILE) == BASELINE
    protected = [ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap',
        ROOT/'unreal/Saved/SaveGames/RaftSimVerticalSlice.sav',
        ROOT/'unreal/Content/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround.uasset']
    protected += list((ROOT/'unreal/Content/__ExternalActors__/RaftSim/Maps/L_SouthForkAmerican_FullReach').rglob('*.uasset'))
    hashes = {path:foam.sha(path) for path in protected}
    assert hashes[protected[0]] == 'db3080cc87f82bafbcb5403757fead35ca6b7a5d4b52dc74c35548d5faf7abb6'
    material = unreal.load_asset(foam.PATH)
    before = protected_graphs(material)
    previous_foam = canonical_graph(foam.verify(material))
    with zipfile.ZipFile(BACKUP, 'x', zipfile.ZIP_DEFLATED) as archive:
        archive.write(foam.FILE, foam.FILE.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(BACKUP) as archive:
        assert hashlib.sha256(archive.read(foam.FILE.relative_to(ROOT).as_posix())).hexdigest() == BASELINE
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.SystemLibrary.execute_console_command(world, 'RaftSim.RefreshSouthForkCurrentNormals')
    result = verify(material)
    assert result['protected_graphs'] == before
    # Exactly two normal-only inputs are added; foam's dependency graph stays unchanged.
    assert result['local_foam']['expression_count'] == previous_foam['expression_count']+2
    previous_foam['expression_count'] += 2
    assert result['local_foam'] == previous_foam
    unreal.SystemLibrary.execute_console_command(world, 'RaftSim.RefreshSouthForkCurrentNormals')
    assert verify(material) == result
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    for path, digest in hashes.items():
        assert foam.sha(path) == digest, str(path)
    REPORT.write_text(json.dumps(dict(verified=result, material_before_sha256=BASELINE,
        material_sha256=foam.sha(foam.FILE), shader_sha256=foam.sha(SHADER),
        protected_graphs_unchanged=True, map_actors_ground_and_profile_unchanged=True,
        refresh_idempotent=True, backup=str(BACKUP.relative_to(ROOT)), backup_sha256=foam.sha(BACKUP),
        scope='Normal-only local frozen-flow optical renewal; not displaced fluid geometry.',
        visual_accepted=False), indent=2)+'\n')
    unreal.log(f'Local-current normal migration verified: {REPORT}')


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
