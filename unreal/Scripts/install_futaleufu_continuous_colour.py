"""Install pinned full-corridor colour on the existing terrain candidate only.

Run with RAFTSIM_CONTINUOUS_COLOUR_MANIFEST naming the generated manifest.
Never changes geometry, collision, source textures, or the normal L_Terminator.
"""
import hashlib
import json
import os
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[2]
LEVEL = '/Game/RaftSim/Maps/Continuous/L_Futaleufu_ContinuousTerrainV1'
TEXTURE = '/Game/RaftSim/Rendering/FutaleufuContinuous/T_FutaleufuCapturedColour20260104'
MATERIAL = '/Game/RaftSim/Materials/Catalog/M_FutaleufuContinuousGroundV2'


def main():
    path = ROOT/os.environ['RAFTSIM_CONTINUOUS_COLOUR_MANIFEST']
    receipt = json.loads(path.read_text())
    if (receipt['schema'] != 'raftsim.futaleufu_continuous_colour.v1'
            or receipt['horizontal_origin_m'] != [739986.,5195961.5]
            or receipt['world_y_sign'] != -1 or receipt['grid']['epsg'] != 32718
            or receipt['capture_datetime'] != '2026-01-04T14:44:49.998000Z'):
        raise RuntimeError('Unreviewed full-river colour identity/frame')
    image = (path.parent/receipt['image']).resolve();image.relative_to(path.parent.resolve())
    if hashlib.sha256(image.read_bytes()).hexdigest() != receipt['image_sha256']:
        raise RuntimeError('Changed captured image')
    # Independently reconstruct native pixel-edge registration, rather than
    # trusting an arbitrary scale/offset in a supplied manifest.
    h,w = receipt['grid']['shape'];t = receipt['grid']['transform']
    if t[:2] != [10,0] or t[3:5] != [0,-10]:raise RuntimeError('Invalid native grid')
    scale = [1/(w*1000),1/(h*1000)]
    offset = [(739986.-t[2])/(w*10),(t[5]-5195961.5)/(h*10)]
    if receipt['world_cm_to_uv'] != dict(scale_xy=scale,offset_xy=offset):
        raise RuntimeError('Registration does not match captured pixels')
    if unreal.EditorAssetLibrary.does_asset_exist(MATERIAL) or unreal.EditorAssetLibrary.does_asset_exist(TEXTURE):
        raise RuntimeError('Preserve existing assets; use an explicitly reviewed new version')
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(LEVEL):raise RuntimeError('Terrain candidate load failed')
    descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
    unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    proxies = [a for a in actors.get_all_level_actors() if isinstance(a,unreal.LandscapeStreamingProxy)]
    if len(proxies) != 177:raise RuntimeError('Incomplete actual resident terrain')
    # Refuse image-edge clamping as a substitute for missing source coverage.
    for actor in proxies:
        centre,extent = actor.get_actor_bounds(False)
        for x in (centre.x-extent.x,centre.x+extent.x):
            for y in (centre.y-extent.y,centre.y+extent.y):
                u,v=x*scale[0]+offset[0],y*scale[1]+offset[1]
                if not (0<=u<=1 and 0<=v<=1):raise RuntimeError('Terrain lies outside captured colour')
    task = unreal.AssetImportTask();task.filename=str(image)
    task.destination_path,task.destination_name=TEXTURE.rsplit('/',1)
    task.automated=True;task.replace_existing=False;task.save=False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture=unreal.load_asset(TEXTURE)
    if not isinstance(texture,unreal.Texture2D):raise RuntimeError('Texture import failed')
    texture.set_editor_property('srgb',True)
    texture.set_editor_property('address_x',unreal.TextureAddress.TA_CLAMP)
    texture.set_editor_property('address_y',unreal.TextureAddress.TA_CLAMP)
    texture.set_editor_property('lod_group',unreal.TextureGroup.TEXTUREGROUP_WORLD)
    # Padding would alter geographical UVs. Keep the exact native rectangle;
    # this small 844x652 image is deliberately resident, without forced padding.
    texture.set_editor_property('power_of_two_mode',unreal.TexturePowerOfTwoSetting.NONE)
    texture.set_editor_property('never_stream',True)
    if (texture.blueprint_get_size_x(),texture.blueprint_get_size_y()) != (w,h):raise RuntimeError('Changed image dimensions')
    folder,name=MATERIAL.rsplit('/',1)
    material=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,folder,unreal.Material,unreal.MaterialFactoryNew())
    lib=unreal.MaterialEditingLibrary
    def node(cls,**values):
        obj=lib.create_material_expression(material,cls)
        for k,v in values.items():obj.set_editor_property(k,v)
        return obj
    def connect(a,b,pin,output=''):
        if not lib.connect_material_expressions(a,output,b,pin):raise RuntimeError('Material connection failed: '+pin)
    world=node(unreal.MaterialExpressionWorldPosition)
    xy=node(unreal.MaterialExpressionComponentMask,r=True,g=True,b=False,a=False);connect(world,xy,'')
    s=node(unreal.MaterialExpressionConstant2Vector,r=scale[0],g=scale[1])
    mul=node(unreal.MaterialExpressionMultiply);connect(xy,mul,'A');connect(s,mul,'B')
    off=node(unreal.MaterialExpressionConstant2Vector,r=offset[0],g=offset[1])
    uv=node(unreal.MaterialExpressionAdd);connect(mul,uv,'A');connect(off,uv,'B')
    sample=node(unreal.MaterialExpressionTextureSampleParameter2D,texture=texture,parameter_name='CapturedColour')
    connect(uv,sample,'UVs')
    if not lib.connect_material_property(sample,'RGB',unreal.MaterialProperty.MP_BASE_COLOR):raise RuntimeError('Colour connection failed')
    rough=node(unreal.MaterialExpressionConstant,r=.86)
    if not lib.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS):raise RuntimeError('Roughness connection failed')
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    for asset in (texture,material):
        if not unreal.EditorAssetLibrary.save_loaded_asset(asset,only_if_is_dirty=False):raise RuntimeError('Asset save failed')
    components=0
    for actor in actors.get_all_level_actors():
        if isinstance(actor,unreal.LandscapeProxy):
            actor.set_editor_property('landscape_material',material)
            for component in actor.get_components_by_class(unreal.LandscapeComponent):
                component.set_editor_property('override_material',material);components+=1
    if components != 177:raise RuntimeError('Unexpected render component count')
    if not levels.save_current_level():raise RuntimeError('Candidate save failed')
    # Save only this world's external actor packages, not arbitrary dirty work.
    for actor in proxies:
        if actor.get_editor_property('landscape_material') != material:raise RuntimeError('Material registration failed')
    report=dict(material=MATERIAL,texture=TEXTURE,manifest_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                registered_proxies=len(proxies),registered_components=components,world_cm_to_uv=receipt['world_cm_to_uv'],
                terrain_geometry_modified=False,normal_playable_map_modified=False)
    (path.parent/'native_install.json').write_text(json.dumps(report,indent=2))
    unreal.log('RAFTSIM_CONTINUOUS_COLOUR_INSTALLED '+json.dumps(report))


if __name__ == '__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
