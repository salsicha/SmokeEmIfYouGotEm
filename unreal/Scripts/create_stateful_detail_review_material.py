"""Bind the persistent GPU height/slopes/foam to the existing single carrier."""
from pathlib import Path
import hashlib
import json
import unreal
ROOT=Path(__file__).resolve().parents[2]
SOURCE='/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_CurrentNormalReviewV2'
DEST='/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulDetailReview'


def main():
    if unreal.EditorAssetLibrary.does_asset_exist(DEST):raise RuntimeError('Keep existing candidate evidence; no overwrite')
    source=unreal.load_asset(SOURCE)
    if not isinstance(source,unreal.Material) or not source.get_editor_property('tangent_space_normal'):
        raise RuntimeError('Expected the tangent-space single-carrier V2 material')
    immutable=[ROOT/'unreal/Content/RaftSim/Maps/Review/SouthForkRegisteredRockPlayable.umap',
        ROOT/'unreal/Content/RaftSim/Maps/Review/SouthForkSurveyPlayable.umap',
        ROOT/'unreal/Content/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_CurrentNormalReviewV2.uasset']
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in immutable}
    material=unreal.EditorAssetLibrary.duplicate_asset(SOURCE,DEST)
    if material is None:raise RuntimeError('Material duplication failed')
    lib=unreal.MaterialEditingLibrary
    def expression(cls):return lib.create_material_expression(material,cls)
    def parameter(cls,name,value):
        item=expression(cls);item.set_editor_property('parameter_name',name);item.set_editor_property('default_value',value);return item
    enabled=parameter(unreal.MaterialExpressionScalarParameter,'StatefulDetailEnable',0.0)
    center=parameter(unreal.MaterialExpressionVectorParameter,'StatefulDetailCenterCm',unreal.LinearColor(0,0,0,0))
    basis=parameter(unreal.MaterialExpressionVectorParameter,'StatefulDetailBasis',unreal.LinearColor(1,0,0,1))
    domain=parameter(unreal.MaterialExpressionVectorParameter,'StatefulDetailDomainM',unreal.LinearColor(-32.25,-32.25,64,64))
    world=expression(unreal.MaterialExpressionWorldPosition)
    world.set_editor_property('world_position_shader_offset',unreal.WorldPositionIncludedOffsets.WPT_EXCLUDE_ALL_SHADER_OFFSETS)
    texture=expression(unreal.MaterialExpressionTextureObjectParameter)
    texture.set_editor_property('parameter_name','StatefulDetailTexture')
    texture.set_editor_property('texture',unreal.load_asset('/Engine/EngineResources/Black'))
    def custom(label,code,kind,inputs):
        item=expression(unreal.MaterialExpressionCustom);item.set_editor_property('description',label)
        item.set_editor_property('code',code);item.set_editor_property('output_type',kind)
        pins=[]
        for name,_,_ in inputs:
            pin=unreal.CustomInput();pin.set_editor_property('input_name',name);pins.append(pin)
        item.set_editor_property('inputs',pins)
        for name,node,output in inputs:
            if not lib.connect_material_expressions(node,output,item,name):raise RuntimeError('Cannot connect '+label+'/'+name)
        return item
    sample=custom('World-registered persistent detail sample',
        '''float2 xy=(World.xy-Center.xy)*0.01;
float2 river=float2(dot(xy,Basis.xy),dot(xy,Basis.zw));
float2 uv=(river-Domain.xy)/Domain.zw;
float inside=all(uv>=0)&&all(uv<=1) ? 1 : 0;
return Texture2DSampleLevel(Detail,DetailSampler,saturate(uv),0)*Enable*inside;''',
        unreal.CustomMaterialOutputType.CMOT_FLOAT4,
        [('World',world,''),('Center',center,'RGBA'),('Basis',basis,'RGBA'),('Domain',domain,'RGBA'),('Detail',texture,''),('Enable',enabled,'')])
    properties=[(unreal.MaterialProperty.MP_NORMAL,'GPU detail slope',
        'float3 slope=float3(Basis.xy*Detail.y+Basis.zw*Detail.z,0); return normalize(Base-TransformWorldVectorToTangent(Parameters.TangentToWorld,slope));',unreal.CustomMaterialOutputType.CMOT_FLOAT3),
        (unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET,'GPU detail surface displacement',
        'return Base+float3(0,0,100*Detail.x);',unreal.CustomMaterialOutputType.CMOT_FLOAT3),
        (unreal.MaterialProperty.MP_BASE_COLOR,'Current-transported froth color',
        'return lerp(Base,float3(0.82,0.87,0.84),0.75*Detail.w);',unreal.CustomMaterialOutputType.CMOT_FLOAT3),
        (unreal.MaterialProperty.MP_ROUGHNESS,'Current-transported froth roughness',
        'return lerp(Base,0.9,Detail.w);',unreal.CustomMaterialOutputType.CMOT_FLOAT1)]
    for prop,label,code,kind in properties:
        old=lib.get_material_property_input_node(material,prop)
        old_output=lib.get_material_property_input_node_output_name(material,prop)
        if old is None:
            if prop!=unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET:raise RuntimeError('Missing existing '+label)
            old=expression(unreal.MaterialExpressionConstant3Vector);old_output=''
        node=custom(label,code,kind,[('Base',old,old_output),('Detail',sample,''),('Basis',basis,'RGBA')])
        if not lib.connect_material_property(node,'',prop):raise RuntimeError('Cannot bind '+label)
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    if not unreal.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False):raise RuntimeError('Candidate save failed')
    if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in hashes.items()):raise RuntimeError('Immutable source changed')
    (ROOT/'docs/reconstruction-review-2026-09-07/stateful-detail-material-setup.json').write_text(json.dumps(dict(
        material=DEST,source_material=SOURCE,unchanged=hashes,default_enabled=False,
        second_surface_added=False,visual_accepted=False,performance_accepted=False),indent=2),encoding='utf-8')
    unreal.log('Stateful detail material created, default off; original maps and material unchanged')


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
