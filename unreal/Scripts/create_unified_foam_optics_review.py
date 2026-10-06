"""Remove the remaining legacy drift coat only inside the persistent GPU window."""
from pathlib import Path
import hashlib
import json
import unreal

ROOT=Path(__file__).resolve().parents[2]
SOURCE='/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulCrestReview'
DEST=SOURCE+'_OpticsReview'


def main():
    lib=unreal.MaterialEditingLibrary
    if unreal.EditorAssetLibrary.does_asset_exist(DEST):raise RuntimeError('Preserve prior review')
    source_file=ROOT/('unreal/Content/'+SOURCE.removeprefix('/Game/')+'.uasset')
    source_hash=hashlib.sha256(source_file.read_bytes()).hexdigest()
    mat=unreal.EditorAssetLibrary.duplicate_asset(SOURCE,DEST)
    if mat is None:raise RuntimeError('Missing source')
    nodes=list(lib.get_material_expressions(mat))
    def inputs(node):
        return dict(zip(map(str,lib.get_material_expression_input_names(node)),lib.get_inputs_for_material_expression(mat,node)))
    finals=[n for n in nodes if isinstance(n,unreal.MaterialExpressionCustom) and
            str(n.get_editor_property('description'))=='Single transported foam coverage authority']
    if len(finals)!=1:raise RuntimeError('Final foam authority mismatch')
    candidates=[]
    for node in nodes:
        if not isinstance(node,unreal.MaterialExpressionMultiply):continue
        pins=inputs(node); gain=pins.get('B')
        if isinstance(gain,unreal.MaterialExpressionScalarParameter) and str(gain.get_editor_property('parameter_name'))=='LiveDriftFoamOpacity':
            candidates.append(pins['A'])
    if len(candidates)!=1:raise RuntimeError('Legacy drift color branch mismatch')
    legacy=candidates[0]
    gate=lib.create_material_expression(mat,unreal.MaterialExpressionCustom)
    gate.set_editor_property('description','Legacy drift foam only outside GPU ownership')
    gate.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    gate.set_editor_property('code','''float2 xy=(World.xy-Center.xy)*0.01;
float2 river=float2(dot(xy,Basis.xy),dot(xy,Basis.zw));
float2 uv=(river-Domain.xy)/Domain.zw;
float2 edge=min(uv,1-uv)*Domain.zw-0.25;
float ownership=smoothstep(0,4,min(edge.x,edge.y))*Enable;
return Legacy*(1-ownership);''')
    final_inputs=inputs(finals[0])
    connections=[('Legacy',legacy)]+[(n,final_inputs[n]) for n in ('World','Center','Basis','Domain','Enable')]
    pins=[]
    for name,_ in connections:
        pin=unreal.CustomInput();pin.set_editor_property('input_name',name);pins.append(pin)
    gate.set_editor_property('inputs',pins)
    for name,node in connections:
        output='' if name=='Legacy' else str(lib.get_input_node_output_name_for_material_expression(finals[0],node))
        if not lib.connect_material_expressions(node,output,gate,name):raise RuntimeError(name)
    # The saved material also retains a fourth consumer outside these live
    # optical trees. Do not rewrite disconnected/other-property graph history.
    optical_nodes=set()
    def optical_visit(node):
        if node is None or node.get_name() in optical_nodes:return
        optical_nodes.add(node.get_name())
        for child in lib.get_inputs_for_material_expression(mat,node):optical_visit(child)
    for prop in (unreal.MaterialProperty.MP_BASE_COLOR,unreal.MaterialProperty.MP_ROUGHNESS,unreal.MaterialProperty.MP_EMISSIVE_COLOR):
        optical_visit(lib.get_material_property_input_node(mat,prop))
    changed=[];preserved_non_optical=[]
    for node in nodes:
        for pin,child in inputs(node).items():
            if child==legacy:
                if node.get_name() not in optical_nodes:
                    preserved_non_optical.append(dict(node=node.get_name(),pin=pin));continue
                if not lib.connect_material_expressions(gate,'',node,'' if pin=='None' else pin):raise RuntimeError('Rewire')
                changed.append(dict(node=node.get_name(),pin=pin))
    if len(changed)!=3:raise RuntimeError('Expected only legacy color, roughness and glow consumers')
    lib.recompile_material(mat)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    if not unreal.EditorAssetLibrary.save_loaded_asset(mat,only_if_is_dirty=False):raise RuntimeError('Save')
    assert hashlib.sha256(source_file.read_bytes()).hexdigest()==source_hash
    source=unreal.load_asset(SOURCE)
    def signature(material,root):
        records={}
        def visit(node):
            if node is None or node.get_name() in records:return
            children=list(lib.get_inputs_for_material_expression(material,node))
            record=dict(kind=node.get_class().get_name(),children=[n.get_name() if n else None for n in children])
            if isinstance(node,unreal.MaterialExpressionCustom):record['code']=str(node.get_editor_property('code'))
            records[node.get_name()]=record
            for child in children:visit(child)
        visit(root)
        return records
    for prop in (unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET,unreal.MaterialProperty.MP_NORMAL,unreal.MaterialProperty.MP_OPACITY):
        assert signature(mat,lib.get_material_property_input_node(mat,prop))==signature(source,lib.get_material_property_input_node(source,prop)),str(prop)
    report=dict(material=DEST,source_sha256=source_hash,source_unchanged=True,changed=changed,preserved_non_optical=preserved_non_optical,
                preserved=['WPO graph','normal graph','opacity graph','final simulated foam','grid and solver','outside-window legacy coat'],
                visual_accepted=False,performance_accepted=False)
    (ROOT/'docs/reconstruction-review-2026-09-07/unified-foam-optics-setup.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    unreal.log('Unified foam optics candidate saved; source and geometry unchanged')


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
