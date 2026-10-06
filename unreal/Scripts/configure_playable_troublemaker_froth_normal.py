"""Give normal-playable transported froth lit bubble relief, not another sheet."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import unreal

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
from configure_playable_troublemaker_foam import graph_signature
PATH='/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/M_TroublemakerWater'
FILE=ROOT/('unreal/Content/'+PATH.removeprefix('/Game/')+'.uasset')
BASE='0b13bf122ea85264b219c536c61067a6c31597e5b438e6b66e844d01a2e8a864'
MARKER='Captured transported froth normal V1'
REPORT=ROOT/'unreal/Saved/RaftSimValidation/playable-froth-normal-setup-20260912.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
lib=unreal.MaterialEditingLibrary
material=unreal.load_asset(PATH)
assert isinstance(material,unreal.Material)
assert material.get_editor_property('tangent_space_normal')
nodes=list(lib.get_material_expressions(material))
assert not any(isinstance(n,unreal.MaterialExpressionCustom) and str(n.get_editor_property('description'))==MARKER for n in nodes),'Already installed; inspect report'
assert sha(FILE)==BASE,'Input changed; inspect before overwriting'
backup=ROOT/'tmp/troublemaker-foam-material-backup'/f'{BASE}.uasset'
if not backup.exists(): shutil.copy2(FILE,backup)
assert sha(backup)==BASE
props={key:getattr(unreal.MaterialProperty,'MP_'+key) for key in ('BASE_COLOR','ROUGHNESS','SPECULAR','OPACITY','EMISSIVE_COLOR','WORLD_POSITION_OFFSET')}
before={k:graph_signature(material,p) for k,p in props.items()}
old_normal=lib.get_material_property_input_node(material,unreal.MaterialProperty.MP_NORMAL)
assert old_normal and isinstance(old_normal,unreal.MaterialExpressionCustom)
assert str(old_normal.get_editor_property('description'))=='Survey current-carried aperiodic ripple normal V2'
foam=[n for n in nodes if isinstance(n,unreal.MaterialExpressionCustom) and str(n.get_editor_property('description'))=='Captured single transported foam optics V1']
lace=[n for n in nodes if isinstance(n,unreal.MaterialExpressionTextureSampleParameter2D) and str(n.get_editor_property('parameter_name'))=='WhitewaterFrothLaceLight']
assert len(foam)==len(lace)==1
position=lib.create_material_expression(material,unreal.MaterialExpressionWorldPosition)
amount=lib.create_material_expression(material,unreal.MaterialExpressionScalarParameter)
amount.set_editor_property('parameter_name','CapturedFrothReliefCm');amount.set_editor_property('default_value',1.2)
normal=lib.create_material_expression(material,unreal.MaterialExpressionCustom)
normal.set_editor_property('description',MARKER)
shader=ROOT/'unreal/Shaders/Private/RaftSimCapturedFrothNormal.hlsl'
normal.set_editor_property('code',shader.read_text())
normal.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT3)
pins=[]
for name in ('BaseNormalTS','WorldPositionCm','Foam','Lace','ReliefCm'):
    pin=unreal.CustomInput();pin.set_editor_property('input_name',name);pins.append(pin)
normal.set_editor_property('inputs',pins)
for node,output,pin in ((old_normal,'','BaseNormalTS'),(position,'','WorldPositionCm'),(foam[0],'','Foam'),(lace[0],'R','Lace'),(amount,'','ReliefCm')):
    assert lib.connect_material_expressions(node,output,normal,pin)
assert lib.connect_material_property(normal,'',unreal.MaterialProperty.MP_NORMAL)
assert {k:graph_signature(material,p) for k,p in props.items()}==before
lib.recompile_material(material)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
assert lib.get_material_property_input_node(material,unreal.MaterialProperty.MP_NORMAL)==normal
assert old_normal in lib.get_inputs_for_material_expression(material,normal)
assert unreal.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False)
REPORT.write_text(json.dumps({'material':PATH,'before_sha256':BASE,'after_sha256':sha(FILE),
    'shader_sha256':sha(shader),'backup':str(backup),'protected_graphs':before,
    'normal_node':normal.get_name(),'underlying_ripple_retained':old_normal.get_name(),
    'relief_cm':1.2,'appearance_choice_not_measured_bubble_height':True,
    'geometry_coverage_foam_sources_unchanged':True,'visual_accepted':False},indent=2)+'\n')
unreal.log(f'Playable froth normal installed: {REPORT}')
