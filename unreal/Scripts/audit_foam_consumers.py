"""Read-only walk of actual saved optical consumers, not just a node label."""
from pathlib import Path
import json
import unreal

ROOT=Path(__file__).resolve().parents[2]


def main():
    mat=unreal.load_asset('/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulCrestReview')
    lib=unreal.MaterialEditingLibrary
    records={}
    def visit(node):
        if node is None:return None
        name=node.get_name()
        if name in records:return name
        record=dict(kind=node.get_class().get_name(),inputs={})
        records[name]=record
        if isinstance(node,unreal.MaterialExpressionCustom):
            record.update(label=str(node.get_editor_property('description')),code=str(node.get_editor_property('code')))
        if isinstance(node,(unreal.MaterialExpressionScalarParameter,unreal.MaterialExpressionVectorParameter)):
            record['parameter']=str(node.get_editor_property('parameter_name'))
            record['default']=str(node.get_editor_property('default_value'))
        if isinstance(node,unreal.MaterialExpressionConstant):record['value']=node.get_editor_property('r')
        for pin,source in zip(lib.get_material_expression_input_names(node),lib.get_inputs_for_material_expression(mat,node)):
            record['inputs'][str(pin)]=visit(source)
        return name
    roots={}
    for label,prop in [('base_color',unreal.MaterialProperty.MP_BASE_COLOR),('roughness',unreal.MaterialProperty.MP_ROUGHNESS),
                       ('opacity',unreal.MaterialProperty.MP_OPACITY),('emissive',unreal.MaterialProperty.MP_EMISSIVE_COLOR),
                       ('refraction',unreal.MaterialProperty.MP_REFRACTION)]:
        roots[label]=visit(lib.get_material_property_input_node(mat,prop))
    drift_parents=[]
    for node in lib.get_material_expressions(mat):
        for pin,child in zip(lib.get_material_expression_input_names(node),lib.get_inputs_for_material_expression(mat,node)):
            if child and child.get_name()=='MaterialExpressionMultiply_122':
                drift_parents.append(dict(node=node.get_name(),pin=str(pin),kind=node.get_class().get_name(),
                    children=[n.get_name() if n else None for n in lib.get_inputs_for_material_expression(mat,node)]))
    (ROOT/'docs/reconstruction-review-2026-09-07/foam-consumer-graph.json').write_text(json.dumps(dict(roots=roots,nodes=records,all_drift_parents=drift_parents),indent=2),encoding='utf-8')
    unreal.log('Saved optical graph read without modification')


if __name__=='__main__':
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
