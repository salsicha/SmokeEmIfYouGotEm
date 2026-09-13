"""Fresh saved-graph verification, including unchanged coverage and geometry."""
from pathlib import Path
import json
import sys
import unreal
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'unreal/Scripts'))
from configure_playable_troublemaker_foam import PATH,FILE,REPORT,MARKER,sha,graph_signature

data=json.loads(REPORT.read_text())
froth_path=ROOT/'unreal/Saved/RaftSimValidation/playable-froth-normal-setup-20260912.json'
froth=json.loads(froth_path.read_text()) if froth_path.exists() else None
assert sha(FILE)==(froth['after_sha256'] if froth else data['after_sha256'])
if froth: assert froth['before_sha256']==data['after_sha256']
mat=unreal.load_asset(PATH);lib=unreal.MaterialEditingLibrary
nodes=list(lib.get_material_expressions(mat))
foam=[n for n in nodes if isinstance(n,unreal.MaterialExpressionCustom) and str(n.get_editor_property('description'))==MARKER]
assert len(foam)==1
foam=foam[0]
code=ROOT/'unreal/Shaders/Private/RaftSimCapturedFoamOptics.hlsl'
assert str(foam.get_editor_property('code'))==code.read_text()
for label,expected in data['protected_graphs'].items():
    actual=graph_signature(mat,getattr(unreal.MaterialProperty,'MP_'+label))
    if froth and label=='NORMAL':
        # The declared froth extension retains the exact previous ripple
        # subgraph; verify every old node, not merely the root name.
        assert all(actual['nodes'].get(k)==v for k,v in expected['nodes'].items())
        root=lib.get_material_property_input_node(mat,unreal.MaterialProperty.MP_NORMAL)
        assert root.get_name()==froth['normal_node']
        assert str(root.get_editor_property('code'))==(ROOT/'unreal/Shaders/Private/RaftSimCapturedFrothNormal.hlsl').read_text()
        assert foam in lib.get_inputs_for_material_expression(mat,root)
        for prop,signature in froth['protected_graphs'].items():
            assert graph_signature(mat,getattr(unreal.MaterialProperty,'MP_'+prop))==signature,prop
    else:
        assert actual==expected,label
for label,name in data['optical_consumers'].items():
    node=lib.get_material_property_input_node(mat,getattr(unreal.MaterialProperty,'MP_'+label))
    assert node.get_name()==name
    assert dict(zip(map(str,lib.get_material_expression_input_names(node)),lib.get_inputs_for_material_expression(mat,node)))['Alpha']==foam
emissive=lib.get_material_property_input_node(mat,unreal.MaterialProperty.MP_EMISSIVE_COLOR)
assert isinstance(emissive,unreal.MaterialExpressionConstant) and emissive.get_editor_property('r')==0
from verify_troublemaker_surface_history import verify_protected_assets
terrain_revision=verify_protected_assets(data['protected_assets'])
out=ROOT/('unreal/Saved/RaftSimValidation/playable-troublemaker-froth-fresh-20260912.json' if froth else 'unreal/Saved/RaftSimValidation/playable-troublemaker-foam-fresh-20260912.json')
out.write_text(json.dumps({'passed':True,'saved_asset_sha256':sha(FILE),'shared_optical_consumers':list(data['optical_consumers']),
    'opacity_wpo_unchanged':True,'original_ripple_subgraph_unchanged':True,'transported_froth_normal':bool(froth),'emissive_zero':True,'map_and_ground_unchanged':not bool(terrain_revision),
    'explicit_terrain_revision_verified':bool(terrain_revision),
    'physical_or_visual_acceptance':False},indent=2)+'\n')
unreal.log(f'Fresh normal playable foam audit passed: {out}')
