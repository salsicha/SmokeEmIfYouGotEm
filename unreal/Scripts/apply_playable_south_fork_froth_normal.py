"""Add flow-carried lit microrelief to South Fork's existing playable material.

Only the final normal changes. Preserve coverage, WPO, source, depth, collision
and previous-frame roots. Dimensions are optical authoring, not surveyed bubbles.
"""
import hashlib
import json
from pathlib import Path
import shutil
import unreal

ROOT = Path(__file__).resolve().parents[2]
ASSET = '/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/M_RaftSim_SouthForkRaftTransmissionWaterV4'
MARKER = 'SouthForkPlayableFrothMicroNormalV1'


def main():
    lib = unreal.MaterialEditingLibrary
    material = unreal.load_asset(ASSET)
    if not isinstance(material, unreal.Material):
        raise RuntimeError('Playable South Fork material missing')
    nodes = lib.get_material_expressions(material)
    if any(isinstance(n, unreal.MaterialExpressionCustom) and str(n.get_editor_property('description')) == MARKER for n in nodes):
        raise RuntimeError('Already applied; preserve the original receipt')
    coverage = [n for n in nodes if isinstance(n, unreal.MaterialExpressionCustom) and 'RaftSimFrothCells cells;' in n.get_editor_property('code')]
    if len(coverage) != 1:
        raise RuntimeError('Expected exactly one final transported foam coverage')
    coverage = coverage[0]
    inputs = dict(zip((str(n) for n in lib.get_material_expression_input_names(coverage)), lib.get_inputs_for_material_expression(material, coverage)))
    flow, clock = inputs['FrothFlow'], inputs['FrothTime']
    signs = [n for n in nodes if isinstance(n, unreal.MaterialExpressionScalarParameter) and str(n.get_editor_property('parameter_name')) == 'StatefulDetailWorldYSign']
    if len(signs) != 1 or not flow or not clock:
        raise RuntimeError('Expected paired source-coordinate flow and clock')
    tangent = bool(material.get_editor_property('tangent_space_normal'))
    normal = lib.get_material_property_input_node(material, unreal.MaterialProperty.MP_NORMAL)
    normal_output = lib.get_material_property_input_node_output_name(material, unreal.MaterialProperty.MP_NORMAL)
    protected = [getattr(unreal.MaterialProperty, name) for name in (
        'MP_BASE_COLOR', 'MP_METALLIC', 'MP_SPECULAR', 'MP_ROUGHNESS',
        'MP_EMISSIVE_COLOR', 'MP_OPACITY', 'MP_OPACITY_MASK',
        'MP_WORLD_POSITION_OFFSET', 'MP_SUBSURFACE_COLOR',
        'MP_AMBIENT_OCCLUSION', 'MP_REFRACTION')]
    roots = {str(p): (lib.get_material_property_input_node(material, p), lib.get_material_property_input_node_output_name(material, p)) for p in protected}
    original = ROOT / ('unreal/Content/' + ASSET.removeprefix('/Game/') + '.uasset')
    receipt_dir = ROOT / 'tmp/south-fork-playable-froth-normal-v1'
    if receipt_dir.exists():
        raise RuntimeError('Preserve previous receipt and backup')
    receipt_dir.mkdir()
    before = hashlib.sha256(original.read_bytes()).hexdigest()
    shutil.copy2(original, receipt_dir / original.name)
    world = lib.create_material_expression(material, unreal.MaterialExpressionWorldPosition)
    world.set_editor_property('world_position_shader_offset', unreal.WorldPositionIncludedOffsets.WPT_EXCLUDE_ALL_SHADER_OFFSETS)
    micro = lib.create_material_expression(material, unreal.MaterialExpressionCustom)
    micro.set_editor_property('description', MARKER)
    micro.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    shader = (ROOT / 'unreal/Plugins/RaftSim/Shaders/Private/RaftSimFrothMicroNormal.ush').read_text()
    code = shader + '\nfloat2 position=World.xy*.01;\nfloat footprint=max(length(ddx(position)),length(ddy(position)));\n'
    code += 'float3 baseWorld=mul(Base,Parameters.TangentToWorld);\n' if tangent else 'float3 baseWorld=Base;\n'
    code += 'RaftSimFrothMicroNormal cells; float3 normal=cells.Sample(baseWorld,Coverage,position,Flow.xy*float2(1,Sign),Clock,footprint);\n'
    code += 'return mul(normal,transpose(Parameters.TangentToWorld));' if tangent else 'return normal;'
    micro.set_editor_property('code', code)
    pins = []
    for name in ('Base', 'Coverage', 'World', 'Flow', 'Clock', 'Sign'):
        pin = unreal.CustomInput(); pin.set_editor_property('input_name', name); pins.append(pin)
    micro.set_editor_property('inputs', pins)
    for name, node, output in [('Base', normal, str(normal_output)), ('Coverage', coverage, ''), ('World', world, ''), ('Flow', flow, ''), ('Clock', clock, ''), ('Sign', signs[0], '')]:
        if not lib.connect_material_expressions(node, output, micro, name):
            raise RuntimeError('Failed to connect ' + name)
    if not lib.connect_material_property(micro, '', unreal.MaterialProperty.MP_NORMAL):
        raise RuntimeError('Final normal connection failed')
    for p in protected:
        assert roots[str(p)] == (lib.get_material_property_input_node(material, p), lib.get_material_property_input_node_output_name(material, p)), str(p)
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    if not unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False):
        raise RuntimeError('Material save failed')
    report = dict(asset=ASSET, original_sha256=before, modified_sha256=hashlib.sha256(original.read_bytes()).hexdigest(), tangent_space_normal=tangent, protected_property_roots_unchanged=True, shader_sha256=hashlib.sha256(shader.encode()).hexdigest(), scope='Lit authored foam microrelief only. No coverage, source, geometry, support, collision or momentum change. Engine views and FPS still required.')
    (receipt_dir / 'receipt.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('Playable South Fork froth normal saved; all other material property roots preserved')


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
