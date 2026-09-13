"""Install one lit transported-foam response on the normal captured carrier.

Only color/roughness/specular/emissive outputs change. Geometry, opacity,
wet-bank/hull masks and the existing current-carried normal graph are preserved.
"""
import hashlib
import json
from pathlib import Path
import shutil
import unreal

ROOT=Path(__file__).resolve().parents[2]
PATH='/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/M_TroublemakerWater'
FILE=ROOT/('unreal/Content/'+PATH.removeprefix('/Game/')+'.uasset')
REPORT=ROOT/'unreal/Saved/RaftSimValidation/playable-troublemaker-foam-setup-20260912.json'
BASELINE='2116ce61b4aa0af240bda57b6ae62fabe146f7cbd413f39e834b2532358501f5'
MARKER='Captured single transported foam optics V1'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def graph_signature(material, prop):
    lib=unreal.MaterialEditingLibrary
    records={}
    def visit(node):
        if node is None: return None
        name=node.get_name()
        if name in records: return name
        record={'kind':node.get_class().get_name()}; records[name]=record
        for key in ('code','description','parameter_name','r','g','b','a','const_a','const_b','coordinate_index','u_tiling','v_tiling'):
            try: record[key]=str(node.get_editor_property(key))
            except Exception: pass
        if isinstance(node,unreal.MaterialExpressionScalarParameter): record['default']=float(node.get_editor_property('default_value'))
        if isinstance(node,unreal.MaterialExpressionVectorParameter):
            v=node.get_editor_property('default_value');record['default']=[v.r,v.g,v.b,v.a]
        if isinstance(node,unreal.MaterialExpressionTextureSampleParameter2D):
            tex=node.get_editor_property('texture'); record['texture']=tex.get_path_name() if tex else None
        record['inputs']=dict(zip(map(str,lib.get_material_expression_input_names(node)),
            [visit(n) for n in lib.get_inputs_for_material_expression(material,node)]))
        return name
    return {'root':visit(lib.get_material_property_input_node(material,prop)),
            'output':lib.get_material_property_input_node_output_name(material,prop),'nodes':records}


def main():
    lib=unreal.MaterialEditingLibrary
    material=unreal.load_asset(PATH)
    assert isinstance(material,unreal.Material)
    nodes=list(lib.get_material_expressions(material))
    assert not any(isinstance(n,unreal.MaterialExpressionCustom) and str(n.get_editor_property('description'))==MARKER for n in nodes), 'Already installed; run fresh audit instead'
    assert sha(FILE)==BASELINE, 'Unreviewed input material identity'
    backup=ROOT/'tmp/troublemaker-foam-material-backup'/f'{BASELINE}.uasset'
    backup.parent.mkdir(exist_ok=True)
    if not backup.exists(): shutil.copy2(FILE,backup)
    assert sha(backup)==BASELINE
    protected=[ROOT/'unreal/Content/RaftSim/Maps/L_SouthFork_Troublemaker.umap',
        ROOT/'unreal/Content/RaftSim/Environment/SouthForkRockRegisteredCandidate20260907/SM_TroublemakerSurveyCandidate.uasset']
    protected_hashes={str(p.relative_to(ROOT)):sha(p) for p in protected}
    props={k:getattr(unreal.MaterialProperty,'MP_'+k) for k in ('OPACITY','NORMAL','WORLD_POSITION_OFFSET')}
    before={k:graph_signature(material,v) for k,v in props.items()}
    def parameter(name):
        found=[n for n in nodes if isinstance(n,(unreal.MaterialExpressionScalarParameter,unreal.MaterialExpressionVectorParameter,unreal.MaterialExpressionTextureSampleParameter2D)) and str(n.get_editor_property('parameter_name'))==name]
        assert len(found)==1,name
        return found[0]
    by_name={n.get_name():n for n in nodes}
    water=by_name['MaterialExpressionLinearInterpolate_1']
    assert isinstance(water,unreal.MaterialExpressionLinearInterpolate)
    assert parameter('LiveReflectedSkyColor') in lib.get_inputs_for_material_expression(material,water)
    lace=parameter('WhitewaterFrothLaceLight')
    assert lib.get_inputs_for_material_expression(material,lace)[0]
    vertex=lib.create_material_expression(material,unreal.MaterialExpressionVertexColor)
    density=lib.create_material_expression(material,unreal.MaterialExpressionScalarParameter)
    density.set_editor_property('parameter_name','CapturedFoamOpticalDensity');density.set_editor_property('default_value',3.0)
    foam=lib.create_material_expression(material,unreal.MaterialExpressionCustom)
    foam.set_editor_property('description',MARKER)
    code=ROOT/'unreal/Shaders/Private/RaftSimCapturedFoamOptics.hlsl'
    foam.set_editor_property('code',code.read_text())
    foam.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    pins=[]
    for name in ('TransportedFoam','Lace','OpticalDensity'):
        pin=unreal.CustomInput();pin.set_editor_property('input_name',name);pins.append(pin)
    foam.set_editor_property('inputs',pins)
    for node,output,name in ((vertex,'R','TransportedFoam'),(lace,'R','Lace'),(density,'','OpticalDensity')):
        assert lib.connect_material_expressions(node,output,foam,name)
    def scalar(name,value):
        node=lib.create_material_expression(material,unreal.MaterialExpressionScalarParameter)
        node.set_editor_property('parameter_name',name);node.set_editor_property('default_value',value);return node
    consumers={}
    for label,a,b in (('BASE_COLOR',water,parameter('WhitewaterFrothColor')),
                       ('ROUGHNESS',parameter('LiveWaterRoughness'),scalar('CapturedFoamRoughness',.72)),
                       ('SPECULAR',parameter('LiveWaterSpecular'),scalar('CapturedFoamSpecular',.25))):
        lerp=lib.create_material_expression(material,unreal.MaterialExpressionLinearInterpolate)
        for node,pin in ((a,'A'),(b,'B'),(foam,'Alpha')):
            assert lib.connect_material_expressions(node,'',lerp,pin)
        assert lib.connect_material_property(lerp,'',getattr(unreal.MaterialProperty,'MP_'+label))
        consumers[label]=lerp.get_name()
    zero=lib.create_material_expression(material,unreal.MaterialExpressionConstant)
    zero.set_editor_property('r',0.0)
    assert lib.connect_material_property(zero,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    after={k:graph_signature(material,v) for k,v in props.items()}
    assert before==after, 'Physical coverage, hull, normal or WPO changed'
    lib.recompile_material(material)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    assert unreal.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False)
    for p,digest in protected_hashes.items(): assert sha(ROOT/p)==digest,p
    REPORT.write_text(json.dumps({'material':PATH,'before_sha256':BASELINE,'after_sha256':sha(FILE),
        'backup':str(backup),'shader_sha256':sha(code),'protected_assets':protected_hashes,
        'protected_graphs':before,'optical_consumers':consumers,'emissive_zero':True,
        'no_new_surface_or_foam_source':True,'visual_or_performance_accepted':False},indent=2)+'\n')
    unreal.log(f'Normal playable transported foam installed: {REPORT}')


if __name__=='__main__': main()
