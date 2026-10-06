"""Read the actual normal-playable carrier graph and its optical inputs."""
import hashlib
import json
from pathlib import Path
import unreal

ROOT=Path(__file__).resolve().parents[2]
PATH='/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/M_TroublemakerWater'
material=unreal.load_asset(PATH)
assert isinstance(material,unreal.Material)
lib=unreal.MaterialEditingLibrary
records={}
for node in lib.get_material_expressions(material):
    record={'kind':node.get_class().get_name()}
    for key in ('parameter_name','default_value','description','code','texture','r','const_a','const_b','constant','coordinate_index'):
        try: record[key]=str(node.get_editor_property(key))
        except Exception: pass
    record['inputs']=dict(zip(map(str,lib.get_material_expression_input_names(node)),
        [n.get_name() if n else None for n in lib.get_inputs_for_material_expression(material,node)]))
    records[node.get_name()]=record
roots={}
for label in ('BASE_COLOR','ROUGHNESS','OPACITY','EMISSIVE_COLOR','NORMAL','WORLD_POSITION_OFFSET','SPECULAR'):
    prop=getattr(unreal.MaterialProperty,'MP_'+label)
    node=lib.get_material_property_input_node(material,prop)
    roots[label]={'node':node.get_name() if node else None,'output':lib.get_material_property_input_node_output_name(material,prop)}
path=ROOT/('unreal/Content/'+PATH.removeprefix('/Game/')+'.uasset')
out=ROOT/'unreal/Saved/RaftSimValidation/playable-troublemaker-optics-20260912.json'
out.write_text(json.dumps({'material':PATH,'asset_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
    'blend_mode':str(material.get_editor_property('blend_mode')),
    'lighting_mode':str(material.get_editor_property('translucency_lighting_mode')),
    'roots':roots,'nodes':records,'modified':False},indent=2)+'\n')
unreal.log(f'Actual playable optics read: {len(records)} expressions; {out}')
