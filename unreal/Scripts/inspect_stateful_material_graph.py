"""Read-only graph inventory for the GPU coarse-attribute conversion."""
from pathlib import Path
import json
import unreal

root=Path(__file__).resolve().parents[2]
try:
    material=unreal.load_asset('/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulDetailReview')
    lib=unreal.MaterialEditingLibrary
    nodes=[]
    for item in lib.get_material_expressions(material):
        record=dict(name=item.get_name(),kind=item.get_class().get_name(),inputs=[])
        names=lib.get_material_expression_input_names(item)
        inputs=lib.get_inputs_for_material_expression(material,item)
        for name,node in zip(names,inputs):
            record['inputs'].append(dict(pin=str(name),node=node.get_name() if node else None,
                output=str(lib.get_input_node_output_name_for_material_expression(item,node)) if node else None))
        if isinstance(item,unreal.MaterialExpressionTextureCoordinate):record['coordinate_index']=item.get_editor_property('coordinate_index')
        if isinstance(item,unreal.MaterialExpressionCustom):
            record['description']=item.get_editor_property('description');record['code']=item.get_editor_property('code')
        nodes.append(record)
    (root/'docs/reconstruction-review-2026-09-07/stateful-material-graph.json').write_text(json.dumps(nodes,indent=2),encoding='utf-8')
finally:
    unreal.SystemLibrary.quit_editor()
