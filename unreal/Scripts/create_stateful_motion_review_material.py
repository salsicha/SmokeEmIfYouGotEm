"""Retain the GPU-carrier baseline; add actual previous-render-frame WPO inputs."""
from pathlib import Path
import hashlib
import json
import unreal

ROOT=Path(__file__).resolve().parents[2]
SOURCE='/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulGPUCarrierReview'
DEST='/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulMotionReview'


def main():
    lib=unreal.MaterialEditingLibrary
    if unreal.EditorAssetLibrary.does_asset_exist(DEST):raise RuntimeError('Retain existing evidence: destination exists')
    immutable=[ROOT/'unreal/Content/RaftSim/Maps/Review/SouthForkRegisteredRockPlayable.umap',
        ROOT/'unreal/Content/RaftSim/Maps/Review/SouthForkSurveyPlayable.umap',
        ROOT/'unreal/Content/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulGPUCarrierReview.uasset']
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in immutable}
    material=unreal.EditorAssetLibrary.duplicate_asset(SOURCE,DEST)
    if material is None:raise RuntimeError('Duplicate failed')
    original=list(lib.get_material_expressions(material))
    replacements={}
    for label,texture_pin,parameter_name in [
        ('Authoritative macro band 0','Atlas','PreviousMacroSurfaceAtlas'),
        ('World-registered persistent detail sample','Detail','PreviousStatefulDetailTexture')]:
        found=[n for n in original if isinstance(n,unreal.MaterialExpressionCustom) and str(n.get_editor_property('description'))==label]
        if len(found)!=1:raise RuntimeError('Expected one '+label)
        current=found[0]
        texture=lib.create_material_expression(material,unreal.MaterialExpressionTextureObjectParameter)
        texture.set_editor_property('parameter_name',parameter_name)
        texture.set_editor_property('texture',unreal.load_asset('/Engine/EngineResources/Black'))
        previous=lib.create_material_expression(material,unreal.MaterialExpressionCustom)
        for field in ('code','output_type','inputs','include_file_paths'):
            previous.set_editor_property(field,current.get_editor_property(field))
        previous.set_editor_property('description','Previous rendered frame: '+label)
        for name,node in zip(lib.get_material_expression_input_names(current),lib.get_inputs_for_material_expression(material,current)):
            if node is None:raise RuntimeError('Unbound input '+str(name))
            source=texture if str(name)==texture_pin else node
            output='' if str(name)==texture_pin else str(lib.get_input_node_output_name_for_material_expression(current,node))
            if not lib.connect_material_expressions(source,output,previous,str(name)):raise RuntimeError('Previous input failed')
        switch=lib.create_material_expression(material,unreal.MaterialExpressionPreviousFrameSwitch)
        if not lib.connect_material_expressions(current,'',switch,'Current Frame'):raise RuntimeError('Current switch failed')
        if not lib.connect_material_expressions(previous,'',switch,'Previous Frame'):raise RuntimeError('Previous switch failed')
        replacements[current.get_name()]=switch
    rewired=[]
    for item in original:
        for pin,node in zip(lib.get_material_expression_input_names(item),lib.get_inputs_for_material_expression(material,item)):
            if node is None or node.get_name() not in replacements:continue
            if str(lib.get_input_node_output_name_for_material_expression(item,node))!='':raise RuntimeError('Unexpected sample swizzle')
            if not lib.connect_material_expressions(replacements[node.get_name()],'',item,str(pin)):raise RuntimeError('Rewire failed')
            rewired.append([item.get_name(),str(pin),node.get_name()])
    material.set_editor_property('output_translucent_velocity',True)
    material.set_editor_property('is_translucency_velocity_from_depth',False)
    errors=lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    if errors:raise RuntimeError('Material compile errors: '+str(errors))
    if not unreal.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False):raise RuntimeError('Save failed')
    if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in hashes.items()):raise RuntimeError('Immutable source changed')
    report=dict(material=DEST,unchanged=hashes,rewired=rewired,output_translucent_velocity=True,
        is_translucency_velocity_from_depth=False,history_cadence='after rendered frame, independent of solver steps',
        lattice_rebuild_history='reset to new current macro geometry',visual_accepted=False,performance_accepted=False)
    (ROOT/'docs/reconstruction-review-2026-09-07/stateful-motion-material-setup.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    unreal.log('Stateful motion review material saved; baseline assets unchanged')


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
