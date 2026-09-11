"""Create opt-in GPU coarse-attribute interpolation; retain earlier evidence."""
from pathlib import Path
import hashlib
import json
import unreal

ROOT=Path(__file__).resolve().parents[2]
SOURCE='/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulDetailReview'
DEST='/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulGPUCarrierReview'
SAFE_MACRO_NORMAL_CODE='float3 n=Macro.xyz*rsqrt(max(dot(Macro.xyz,Macro.xyz),1.e-8)); float3 coarse=TransformWorldVectorToTangent(Parameters.TangentToWorld,n); return normalize(lerp(Base,coarse+Base-float3(0,0,1),Enable));'

def main():
    lib=unreal.MaterialEditingLibrary
    if unreal.EditorAssetLibrary.does_asset_exist(DEST):raise RuntimeError('Retain existing evidence: destination already exists')
    immutable=[ROOT/'unreal/Content/RaftSim/Maps/Review/SouthForkRegisteredRockPlayable.umap',
        ROOT/'unreal/Content/RaftSim/Maps/Review/SouthForkSurveyPlayable.umap',
        ROOT/'unreal/Content/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulDetailReview.uasset']
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in immutable}
    material=unreal.EditorAssetLibrary.duplicate_asset(SOURCE,DEST)
    if material is None:raise RuntimeError('Duplicate failed')
    original=list(lib.get_material_expressions(material))
    def expression(cls):return lib.create_material_expression(material,cls)
    def parameter(cls,name,value):
        node=expression(cls);node.set_editor_property('parameter_name',name);node.set_editor_property('default_value',value);return node
    enabled=parameter(unreal.MaterialExpressionScalarParameter,'MacroSurfaceEnable',0.0)
    size=parameter(unreal.MaterialExpressionVectorParameter,'MacroGridSize',unreal.LinearColor(2,2,0,0))
    atlas=expression(unreal.MaterialExpressionTextureObjectParameter)
    atlas.set_editor_property('parameter_name','MacroSurfaceAtlas');atlas.set_editor_property('texture',unreal.load_asset('/Engine/EngineResources/Black'))
    coordinates=expression(unreal.MaterialExpressionTextureCoordinate);coordinates.set_editor_property('coordinate_index',3)
    def custom(label,code,kind,inputs,includes=False):
        node=expression(unreal.MaterialExpressionCustom);node.set_editor_property('description',label)
        node.set_editor_property('code',code);node.set_editor_property('output_type',kind)
        if includes:node.set_editor_property('include_file_paths',['/Plugin/RaftSimWaterDetail/Private/RaftSimMacroSurfaceSample.ush'])
        pins=[]
        for name,_,_ in inputs:
            pin=unreal.CustomInput();pin.set_editor_property('input_name',name);pins.append(pin)
        node.set_editor_property('inputs',pins)
        for name,source,output in inputs:
            if not lib.connect_material_expressions(source,output,node,name):raise RuntimeError('Cannot connect '+label+'/'+name)
        return node
    samples=[custom('Authoritative macro band '+str(band),
        f'return RaftSimMacroSample(Atlas,GridPosition,int2(Size.xy),{band});',unreal.CustomMaterialOutputType.CMOT_FLOAT4,
        [('Atlas',atlas,''),('GridPosition',coordinates,''),('Size',size,'RGBA')],True) for band in range(4)]
    replacements={}
    for item in original:
        if isinstance(item,unreal.MaterialExpressionVertexColor):
            blended=custom('Linear hydraulic color, GPU spatial interpolation',
                'return lerp(float4(RGB,Alpha),Macro,Enable);',unreal.CustomMaterialOutputType.CMOT_FLOAT4,
                [('RGB',item,''),('Alpha',item,'A'),('Macro',samples[2],''),('Enable',enabled,'')])
            rgb=custom('Macro color RGB','return Color.rgb;',unreal.CustomMaterialOutputType.CMOT_FLOAT3,[('Color',blended,'')])
            alpha=custom('Macro wet coverage','return Color.a;',unreal.CustomMaterialOutputType.CMOT_FLOAT1,[('Color',blended,'')])
            replacements[item.get_name()]={'':rgb,'A':alpha}
        elif isinstance(item,unreal.MaterialExpressionTextureCoordinate) and item.get_editor_property('coordinate_index') in (1,2):
            if item.get_editor_property('u_tiling')!=1 or item.get_editor_property('v_tiling')!=1:raise RuntimeError('Unexpected scaled dynamic UV')
            swizzle='xy' if item.get_editor_property('coordinate_index')==1 else 'zw'
            node=custom('GPU macro dynamic UV '+swizzle,f'return lerp(Base,Macro.{swizzle},Enable);',unreal.CustomMaterialOutputType.CMOT_FLOAT2,
                [('Base',item,''),('Macro',samples[3],''),('Enable',enabled,'')])
            replacements[item.get_name()]={'':node}
    rewired=[]
    for item in original:
        names=lib.get_material_expression_input_names(item);inputs=lib.get_inputs_for_material_expression(material,item)
        for pin,source in zip(names,inputs):
            if source is None or source.get_name() not in replacements:continue
            output=str(lib.get_input_node_output_name_for_material_expression(item,source))
            if output not in replacements[source.get_name()]:raise RuntimeError('Unsupported original output '+output)
            target=replacements[source.get_name()][output]
            if not lib.connect_material_expressions(target,'',item,'' if str(pin)=='None' else str(pin)):raise RuntimeError('Input rewire failed')
            rewired.append([item.get_name(),str(pin),source.get_name(),output])
    world=expression(unreal.MaterialExpressionWorldPosition)
    world.set_editor_property('world_position_shader_offset',unreal.WorldPositionIncludedOffsets.WPT_EXCLUDE_ALL_SHADER_OFFSETS)
    for prop,label,code,band in [
        (unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET,'GPU macro world surface','return Base+Enable*(Macro.xyz-World);',0),
        (unreal.MaterialProperty.MP_NORMAL,'GPU macro normal with existing detail',
         SAFE_MACRO_NORMAL_CODE,1)]:
        old=lib.get_material_property_input_node(material,prop);output=lib.get_material_property_input_node_output_name(material,prop)
        if old is None:raise RuntimeError('Missing existing '+label)
        node=custom(label,code,unreal.CustomMaterialOutputType.CMOT_FLOAT3,
            [('Base',old,output),('Macro',samples[band],''),('World',world,''),('Enable',enabled,'')])
        if not lib.connect_material_property(node,'',prop):raise RuntimeError('Property rewire failed')
    errors=lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    if errors:raise RuntimeError('Material compilation errors: '+str(errors))
    if not unreal.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False):raise RuntimeError('Save failed')
    if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in hashes.items()):raise RuntimeError('Immutable source changed')
    (ROOT/'docs/reconstruction-review-2026-09-07/stateful-gpu-carrier-material-setup.json').write_text(json.dumps(dict(
        material=DEST,unchanged=hashes,rewired=rewired,default_enabled=False,visual_accepted=False,performance_accepted=False),indent=2),encoding='utf-8')
    unreal.log('Stateful GPU carrier material created; original material/maps unchanged')

if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
