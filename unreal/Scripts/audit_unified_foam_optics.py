"""Fresh-load verification of the bounded optical change and ownership equation."""
from pathlib import Path
import hashlib
import json
import re
import unreal

ROOT=Path(__file__).resolve().parents[2]
BASE='/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulCrestReview'


def main():
    lib=unreal.MaterialEditingLibrary
    source=unreal.load_asset(BASE);mat=unreal.load_asset(BASE+'_OpticsReview')
    assert source and mat
    nodes=list(lib.get_material_expressions(mat))
    def named(label):
        found=[n for n in nodes if isinstance(n,unreal.MaterialExpressionCustom) and str(n.get_editor_property('description'))==label]
        assert len(found)==1,label
        return found[0]
    def inputs(node):
        return dict(zip(map(str,lib.get_material_expression_input_names(node)),lib.get_inputs_for_material_expression(mat,node)))
    gate=named('Legacy drift foam only outside GPU ownership')
    coverage=named('Single transported foam coverage authority')
    def equation(node):
        code=str(node.get_editor_property('code')).split('return')[0]
        code=''.join(line.split('//')[0] for line in code.splitlines())
        return re.sub(r'\s+','',code)
    assert equation(gate)==equation(coverage),'Ownership units/border/fade mismatch'
    for pin in ('World','Center','Basis','Domain','Enable'):
        assert inputs(gate)[pin]==inputs(coverage)[pin],pin
    consumers=[]
    for node in nodes:
        if gate not in inputs(node).values():continue
        assert isinstance(node,unreal.MaterialExpressionMultiply)
        assert inputs(node)['A']==gate
        consumers.append(str(inputs(node)['B'].get_editor_property('parameter_name')))
    assert set(consumers)=={'LiveDriftFoamOpacity','LiveDriftFoamRoughness','LiveDriftFoamSurfaceGlow'} and len(consumers)==3
    def signature(material,root):
        records={}
        def visit(node):
            if node is None or node.get_name() in records:return
            children=list(lib.get_inputs_for_material_expression(material,node))
            item=dict(kind=node.get_class().get_name(),children=[n.get_name() if n else None for n in children])
            if isinstance(node,unreal.MaterialExpressionCustom):item['code']=str(node.get_editor_property('code'))
            records[node.get_name()]=item
            for child in children:visit(child)
        visit(root);return records
    for prop in (unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET,unreal.MaterialProperty.MP_NORMAL,unreal.MaterialProperty.MP_OPACITY):
        assert signature(mat,lib.get_material_property_input_node(mat,prop))==signature(source,lib.get_material_property_input_node(source,prop)),str(prop)
    assert sum(isinstance(n,unreal.MaterialExpressionPreviousFrameSwitch) for n in nodes)==2
    path=ROOT/('unreal/Content/'+(BASE+'_OpticsReview').removeprefix('/Game/')+'.uasset')
    report=dict(passed=True,asset_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),same_ownership_equation=True,
                optical_consumers=consumers,unchanged_geometry_normal_opacity=True,previous_frame_switches=2,
                scope='Saved optical graph and exact fade equivalence, not full scene acceptance')
    (ROOT/'docs/reconstruction-review-2026-09-07/unified-foam-optics-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    unreal.log('Fresh-load unified foam optics audit passed')


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
