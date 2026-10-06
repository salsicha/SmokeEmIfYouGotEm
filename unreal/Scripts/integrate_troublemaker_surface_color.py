"""Apply registered NAIP bank color and source-classed rock appearance in play."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import unreal

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
from configure_playable_troublemaker_foam import graph_signature
ASSETS='/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker'
PARENT='/Game/RaftSim/Environment/SouthForkFullReach/Dressing/Materials/M_RaftSim_SouthForkBoulderDressing'
DEST=ASSETS+'/M_TroublemakerCapturedGround'
INSTANCE=ASSETS+'/MI_TroublemakerGround'
NAIP=ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/sources/troublemaker_naip.png'
DATA=ROOT/'unreal/SourceArt/RaftSim/TroublemakerSurfaceAuthority'
REPORT=ROOT/'unreal/Saved/RaftSimValidation/troublemaker-surface-color-20260912.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(NAIP)=='45b885eca1711307ba94738700c4dd538130fe7e84b0834829984f041513b2e3'
metadata=json.loads((DATA/'manifest.json').read_text())
assert sha(DATA/'T_TroublemakerSurfaceAuthority.png')==metadata['texture_sha256']
extent=json.loads(NAIP.with_name('troublemaker_naip_export.json').read_text())['extent']
assert extent['spatialReference']['wkid']==32610
assert not unreal.EditorAssetLibrary.does_asset_exist(DEST),'Inspect existing integration first'
protected={}
for p in (ROOT/'unreal/Content/RaftSim/Maps/L_SouthFork_Troublemaker.umap',ROOT/'unreal/Content/RaftSim/Environment/SouthForkRockRegisteredCandidate20260907/SM_TroublemakerSurveyCandidate.uasset'):
    protected[str(p.relative_to(ROOT))]=sha(p)
instance_file=ROOT/('unreal/Content/'+INSTANCE.removeprefix('/Game/')+'.uasset')
old_sha=sha(instance_file)
backup=ROOT/'tmp/troublemaker-ground-material-backup'/f'{old_sha}.uasset'
backup.parent.mkdir(exist_ok=True)
if not backup.exists():shutil.copy2(instance_file,backup)
lib=unreal.MaterialEditingLibrary
ground=unreal.EditorAssetLibrary.duplicate_asset(PARENT,DEST)
assert isinstance(ground,unreal.Material)
props={k:getattr(unreal.MaterialProperty,'MP_'+k) for k in ('NORMAL','ROUGHNESS','WORLD_POSITION_OFFSET')}
before={k:graph_signature(ground,p) for k,p in props.items()}
base=lib.get_material_property_input_node(ground,unreal.MaterialProperty.MP_BASE_COLOR)
assert base
def imported(path,name,data=False):
    task=unreal.AssetImportTask();task.filename=str(path);task.destination_path=ASSETS
    task.destination_name=name;task.automated=True;task.replace_existing=False;task.save=False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    assert len(task.imported_object_paths)==1
    tex=unreal.load_asset(task.imported_object_paths[0]);assert isinstance(tex,unreal.Texture2D)
    tex.set_editor_property('srgb',not data)
    tex.set_editor_property('address_x',unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property('address_y',unreal.TextureAddress.TA_CLAMP)
    if data:tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_MASKS)
    assert unreal.EditorAssetLibrary.save_loaded_asset(tex,only_if_is_dirty=False)
    return tex
image=imported(NAIP,'T_TroublemakerNAIP')
mask=imported(DATA/'T_TroublemakerSurfaceAuthority.png','T_TroublemakerSurfaceAuthority',True)
world=lib.create_material_expression(ground,unreal.MaterialExpressionWorldPosition)
normal=lib.create_material_expression(ground,unreal.MaterialExpressionVertexNormalWS)
def custom(code,names,kind):
    node=lib.create_material_expression(ground,unreal.MaterialExpressionCustom)
    node.set_editor_property('code',code);node.set_editor_property('output_type',kind)
    pins=[]
    for name in names:
        p=unreal.CustomInput();p.set_editor_property('input_name',name);pins.append(p)
    node.set_editor_property('inputs',pins);return node
origin=metadata['origin_utm_m'];left,bottom,right,top=metadata['local_bounds_m']
photo_uv=custom(f'return float2((P.x*.01+{origin[0]-extent["xmin"]:.12f})/{extent["xmax"]-extent["xmin"]:.12f},(P.y*.01+{extent["ymax"]-origin[1]:.12f})/{extent["ymax"]-extent["ymin"]:.12f});',['P'],unreal.CustomMaterialOutputType.CMOT_FLOAT2)
mask_uv=custom(f'return float2((P.x*.01-({left:.12f}))/{right-left:.12f},(P.y*.01+{top:.12f})/{top-bottom:.12f});',['P'],unreal.CustomMaterialOutputType.CMOT_FLOAT2)
for uv in (photo_uv,mask_uv):assert lib.connect_material_expressions(world,'',uv,'P')
def sample(tex,uv,data=False):
    node=lib.create_material_expression(ground,unreal.MaterialExpressionTextureSample)
    node.set_editor_property('texture',tex)
    node.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_MASKS if data else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    assert lib.connect_material_expressions(uv,'',node,'UVs');return node
photo=sample(image,photo_uv);classes=sample(mask,mask_uv,True)
color=custom('''
// Registered orthophoto color is not an intrinsic albedo measurement: it
// contains capture lighting, canopy and roofs. Keep it off inferred water,
// and use the existing seamless rock PBR on steep, occluded side faces.
float luma=dot(Detail,float3(.2126,.7152,.0722));
float3 rock=luma*float3(.92,.98,1.0);
float3 base=lerp(Detail,rock,saturate(Classes.g));
float drape=saturate(Classes.r)*smoothstep(.45,.88,abs(N.z));
return lerp(base,Photo*(.85+.15*saturate(luma/.12)),drape);
''',['Detail','Photo','Classes','N'],unreal.CustomMaterialOutputType.CMOT_FLOAT3)
color.set_editor_property('description','Registered captured bank color V1')
for node,out,pin in ((base,'','Detail'),(photo,'RGB','Photo'),(classes,'RGB','Classes'),(normal,'','N')):
    assert lib.connect_material_expressions(node,out,color,pin)
assert lib.connect_material_property(color,'',unreal.MaterialProperty.MP_BASE_COLOR)
assert {k:graph_signature(ground,p) for k,p in props.items()}==before
lib.recompile_material(ground)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
assert unreal.EditorAssetLibrary.save_loaded_asset(ground,only_if_is_dirty=False)
instance=unreal.load_asset(INSTANCE);assert isinstance(instance,unreal.MaterialInstanceConstant)
assert instance.get_editor_property('parent').get_path_name().split('.')[0]==PARENT
lib.set_material_instance_parent(instance,ground)
assert unreal.EditorAssetLibrary.save_loaded_asset(instance,only_if_is_dirty=False)
for name,digest in protected.items():assert sha(ROOT/name)==digest
REPORT.write_text(json.dumps({'normal_playable_map':'/Game/RaftSim/Maps/L_SouthFork_Troublemaker',
    'material':DEST,'instance':INSTANCE,'instance_before_sha256':old_sha,'instance_after_sha256':sha(instance_file),
    'instance_backup':str(backup),'source_naip_sha256':sha(NAIP),'authority':metadata,
    'protected_assets':protected,'protected_graphs':before,'geometry_collision_flow_unchanged':True,
    'appearance_not_calibrated_albedo':True,'photographic_canopy_shadows_remain':True,
    'visual_accepted':False},indent=2)+'\n')
unreal.log(f'Registered bank surface integrated into normal play: {REPORT}')
