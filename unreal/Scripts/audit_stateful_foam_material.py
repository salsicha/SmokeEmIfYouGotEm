"""Read-only graph invariants for the single-authority foam material."""
from pathlib import Path
import hashlib
import json
import unreal

ROOT=Path(__file__).resolve().parents[2]
try:
    lib=unreal.MaterialEditingLibrary
    prefix='/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_'
    previous=unreal.load_asset(prefix+'StatefulMotionReview')
    material=unreal.load_asset(prefix+'StatefulFoamReview')
    if material is None or previous is None:raise RuntimeError('Both comparison materials required')
    def reachable(mat,root):
        found={}
        def visit(node):
            if node is None or node.get_name() in found:return
            found[node.get_name()]=node
            for child in lib.get_inputs_for_material_expression(mat,node):visit(child)
        visit(root)
        return found
    def wpo_signature(mat):
        root=lib.get_material_property_input_node(mat,unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
        records=[]
        for node in reachable(mat,root).values():
            entry=dict(name=node.get_name(),kind=node.get_class().get_name(),inputs=[])
            for pin,child in zip(lib.get_material_expression_input_names(node),lib.get_inputs_for_material_expression(mat,node)):
                entry['inputs'].append([str(pin),child.get_name() if child else None,
                    str(lib.get_input_node_output_name_for_material_expression(node,child)) if child else None])
            if isinstance(node,unreal.MaterialExpressionCustom):
                entry.update(code=str(node.get_editor_property('code')),kind_output=str(node.get_editor_property('output_type')))
            records.append(entry)
        return sorted(records,key=lambda e:e['name'])
    assert wpo_signature(material)==wpo_signature(previous),'WPO graph changed with foam'
    expressions=list(lib.get_material_expressions(material))
    owned=[n for n in expressions if isinstance(n,unreal.MaterialExpressionCustom) and str(n.get_editor_property('description'))=='Single transported foam coverage authority']
    assert len(owned)==1 and owned[0].get_editor_property('output_type')==unreal.CustomMaterialOutputType.CMOT_FLOAT1
    coverage=owned[0]
    properties={}
    for prop,label in [(unreal.MaterialProperty.MP_BASE_COLOR,'base_color'),
                       (unreal.MaterialProperty.MP_ROUGHNESS,'roughness'),
                       (unreal.MaterialProperty.MP_OPACITY,'opacity')]:
        root=lib.get_material_property_input_node(material,prop)
        nodes=reachable(material,root)
        assert coverage.get_name() in nodes,label+' bypasses foam authority'
        labels=[str(n.get_editor_property('description')) for n in nodes.values() if isinstance(n,unreal.MaterialExpressionCustom)]
        assert 'Current-transported froth color' not in labels
        assert 'Current-transported froth roughness' not in labels
        properties[label]=len(nodes)
    coverage_inputs=dict((str(p),n) for p,n in zip(lib.get_material_expression_input_names(coverage),lib.get_inputs_for_material_expression(material,coverage)))
    old=coverage_inputs['Base']
    assert isinstance(old,unreal.MaterialExpressionClamp),'Fallback is not final legacy coverage'
    old_consumers=[n.get_name() for n in expressions if old in lib.get_inputs_for_material_expression(material,n)]
    assert old_consumers==[coverage.get_name()],'Legacy coverage still feeds a second foam path'
    assert material.get_editor_property('output_translucent_velocity')
    assert not material.get_editor_property('is_translucency_velocity_from_depth')
    assert sum(isinstance(n,unreal.MaterialExpressionPreviousFrameSwitch) for n in expressions)==2
    path=ROOT/'unreal/Content/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulFoamReview.uasset'
    report=dict(passed=True,material=material.get_path_name(),asset_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        wpo_graph_unchanged=True,previous_frame_switches=2,old_final_coverage_consumers=old_consumers,
        property_reachable_node_counts=properties,scope='Graph wiring only; not photographic or motion acceptance')
    (ROOT/'docs/reconstruction-review-2026-09-07/stateful-foam-graph-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    unreal.log('Stateful foam graph audit passed: one final coverage, unchanged WPO/history, no additive foam coat')
finally:
    unreal.SystemLibrary.quit_editor()
