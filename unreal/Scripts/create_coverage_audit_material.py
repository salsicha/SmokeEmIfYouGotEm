"""Isolated unlit provenance view on the SAME animated carrier, not a visual candidate."""
from pathlib import Path
import hashlib
import json
import unreal

ROOT = Path(__file__).resolve().parents[2]
SOURCE = '/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulCrestReview'
DEST = SOURCE + '_CoverageAudit'


def main():
    lib = unreal.MaterialEditingLibrary
    if unreal.EditorAssetLibrary.does_asset_exist(DEST):
        raise RuntimeError('Preserve existing diagnostic evidence; destination exists')
    source_file = ROOT / ('unreal/Content/'+SOURCE.removeprefix('/Game/')+'.uasset')
    source_hash = hashlib.sha256(source_file.read_bytes()).hexdigest()
    material = unreal.EditorAssetLibrary.duplicate_asset(SOURCE,DEST)
    if material is None: raise RuntimeError('Missing source')
    nodes = list(lib.get_material_expressions(material))
    coverage = [n for n in nodes if isinstance(n,unreal.MaterialExpressionCustom)
                and str(n.get_editor_property('description'))=='Single transported foam coverage authority']
    if len(coverage)!=1: raise RuntimeError('Expected exactly one final foam authority')
    coverage = coverage[0]
    inputs = dict(zip(map(str,lib.get_material_expression_input_names(coverage)),
                      lib.get_inputs_for_material_expression(material,coverage)))
    assert inputs['Base'] and inputs['Detail']
    wpo = lib.get_material_property_input_node(material,unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    wpo_output = lib.get_material_property_input_node_output_name(material,unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    debug = lib.create_material_expression(material,unreal.MaterialExpressionCustom)
    debug.set_editor_property('description','Audit R final foam G legacy foam B GPU foam')
    debug.set_editor_property('code','return float3(Final,Legacy,Detail.w);')
    debug.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    pins=[]
    for name in ('Final','Legacy','Detail'):
        pin=unreal.CustomInput();pin.set_editor_property('input_name',name);pins.append(pin)
    debug.set_editor_property('inputs',pins)
    for name,node in [('Final',coverage),('Legacy',inputs['Base']),('Detail',inputs['Detail'])]:
        if not lib.connect_material_expressions(node,'',debug,name): raise RuntimeError(name)
    material.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
    if not lib.connect_material_property(debug,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR): raise RuntimeError('Emissive')
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert lib.get_material_property_input_node(material,unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)==wpo
    assert lib.get_material_property_input_node_output_name(material,unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)==wpo_output
    assert sum(isinstance(n,unreal.MaterialExpressionPreviousFrameSwitch) for n in nodes)==2
    if not unreal.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False): raise RuntimeError('Save')
    assert hashlib.sha256(source_file.read_bytes()).hexdigest()==source_hash
    report=dict(material=DEST,source_sha256=source_hash,source_unchanged=True,
                channels=dict(red='final foam coverage',green='legacy final coverage before replacement',blue='resolved GPU foam'),
                same_wpo_root=True,previous_frame_switches=2,shading='Unlit',
                scope='Diagnostic only. Tone mapping prevents treating captured RGB as linear scalar measurements.')
    (ROOT/'docs/reconstruction-review-2026-09-07/coverage-audit-material.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    unreal.log('Coverage provenance audit material saved; rendering candidate unchanged')


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
