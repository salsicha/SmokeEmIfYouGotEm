"""Guarded local-current optical lace installation; no geometry/coverage edits."""
import hashlib
import json
from pathlib import Path
import zipfile
import unreal

ROOT = Path(__file__).resolve().parents[2]
PATH = '/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/M_RaftSim_SouthForkRaftTransmissionWaterV4'
FILE = ROOT/'unreal/Content'/(PATH.removeprefix('/Game/')+'.uasset')
BASELINE = 'f54dce684f494e5ae64d5fbd3ef9a5fb78435bcb251f1aab1e5d332c107f72de'
REPORT = ROOT/'unreal/Saved/RaftSimValidation/south-fork-local-froth-integration-v2-20260912.json'
BACKUP = REPORT.with_name('south-fork-before-local-froth-v2-20260912.zip')
SHADER = ROOT/'unreal/Shaders/Private/RaftSimLocalFoamLace.hlsl'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def links(material, node):
    lib = unreal.MaterialEditingLibrary
    return dict(zip(map(str, lib.get_material_expression_input_names(node)),
                    lib.get_inputs_for_material_expression(material, node)))


def graph(material, node, result=None):
    result = {} if result is None else result
    if node is None or node.get_name() in result:
        return result
    children = links(material, node)
    row = dict(kind=node.get_class().get_name(), inputs={k:v.get_name() if v else None for k,v in children.items()})
    for key in ('code', 'parameter_name', 'coordinate_index', 'u_tiling', 'v_tiling', 'default_value', 'r', 'g', 'b', 'a', 'texture'):
        try:
            row[key] = str(node.get_editor_property(key))
        except Exception:
            pass
    result[node.get_name()] = row
    for child in children.values():
        graph(material, child, result)
    return result


def protected_graphs(material):
    lib = unreal.MaterialEditingLibrary
    return {name: graph(material, lib.get_material_property_input_node(material, getattr(unreal.MaterialProperty, name)))
            for name in ('MP_WORLD_POSITION_OFFSET', 'MP_OPACITY_MASK', 'MP_NORMAL')}


def verify(material, flow_index=1):
    lib = unreal.MaterialEditingLibrary
    nodes = list(lib.get_material_expressions(material))
    local, = [n for n in nodes if n.get_editor_property('desc') == 'SouthForkLocalFoamLaceV1']
    coverage, = [n for n in nodes if n.get_editor_property('desc') == 'SouthForkTransportedFoamOpticsV1']
    inputs = links(material, local)
    assert set(inputs) == {'UV', 'Origin', 'Flow', 'TimeSeconds', 'LaceTexture'}
    assert inputs['UV'].get_editor_property('coordinate_index') == 0
    assert 'RaftSimFullPrecisionRiverUV' in inputs['UV'].get_editor_property('desc')
    assert inputs['Flow'].get_editor_property('coordinate_index') == flow_index
    assert inputs['TimeSeconds'].get_class().get_name() == 'MaterialExpressionTime'
    assert str(inputs['Origin'].get_editor_property('parameter_name')) == 'RaftSimWaterUVOrigin'
    assert str(inputs['LaceTexture'].get_editor_property('parameter_name')) == 'WhitewaterFoamLace'
    assert inputs['LaceTexture'].get_editor_property('texture')
    assert local.get_editor_property('code') == SHADER.read_text()
    assert local.get_editor_property('output_type') == unreal.CustomMaterialOutputType.CMOT_FLOAT3
    assert 'lerp(cellsB, cellsA, saturate(Lace.b))' in coverage.get_editor_property('code')
    assert links(material, coverage)['Lace'] == local
    consumers = [n.get_name() for n in nodes if coverage in links(material, n).values()]
    assert len(consumers) == 4
    assert 'RaftSimFoamAdvectionMeters' not in str(graph(material, local))
    assert links(material, coverage)['VertexFoam'].get_class().get_name() == 'MaterialExpressionVertexColor'
    return dict(expression_count=len(nodes), optical_consumers=consumers, local_lace_graph=graph(material, local))


def main():
    assert 'RaftSimIntegrateLocalFroth' in unreal.SystemLibrary.get_command_line()
    assert not REPORT.exists() and not BACKUP.exists() and sha(FILE) == BASELINE
    protected = [ROOT/'unreal/Content/RaftSim/Maps/L_SouthForkAmerican_FullReach.umap',
        ROOT/'unreal/Saved/SaveGames/RaftSimVerticalSlice.sav',
        ROOT/'unreal/Content/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround.uasset']
    protected += list((ROOT/'unreal/Content/__ExternalActors__/RaftSim/Maps/L_SouthForkAmerican_FullReach').rglob('*.uasset'))
    hashes = {path:sha(path) for path in protected}
    assert hashes[protected[0]] == 'db3080cc87f82bafbcb5403757fead35ca6b7a5d4b52dc74c35548d5faf7abb6'
    material = unreal.load_asset(PATH)
    assert material
    before = protected_graphs(material)
    with zipfile.ZipFile(BACKUP, 'x', zipfile.ZIP_DEFLATED) as archive:
        archive.write(FILE, FILE.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(BACKUP) as archive:
        assert hashlib.sha256(archive.read(FILE.relative_to(ROOT).as_posix())).hexdigest() == BASELINE
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.SystemLibrary.execute_console_command(world, 'RaftSim.RefreshSouthForkCurrentNormals')
    assert protected_graphs(material) == before, 'Local optical lace changed protected graph'
    result = verify(material)
    unreal.SystemLibrary.execute_console_command(world, 'RaftSim.RefreshSouthForkCurrentNormals')
    assert verify(material) == result and protected_graphs(material) == before
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    for path, digest in hashes.items():
        assert sha(path) == digest, str(path)
    result.update(material=PATH, material_before_sha256=BASELINE, material_sha256=sha(FILE),
        shader_sha256=sha(SHADER), protected_graphs=before, protected_graphs_unchanged=True,
        map_actors_ground_and_profile_unchanged=True, refresh_idempotent=True,
        backup=str(BACKUP.relative_to(ROOT)), backup_sha256=sha(BACKUP),
        scope='Optical local frozen-flow two-phase backtrace; transported foam amount unchanged.',
        photoreal_accepted=False, physical_acceptance=False)
    REPORT.write_text(json.dumps(result, indent=2)+'\n')
    unreal.log(f'South Fork local froth material verified: {REPORT}')


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
