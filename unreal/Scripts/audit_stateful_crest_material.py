"""Read-only persistent crest graph checks after saving/reloading the asset."""
from pathlib import Path
import hashlib
import json
import unreal

ROOT = Path(__file__).resolve().parents[2]


def main():
    lib = unreal.MaterialEditingLibrary
    prefix = '/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_'
    material = unreal.load_asset(prefix + 'StatefulCrestReview')
    source = unreal.load_asset(prefix + 'StatefulFoamReview')
    if material is None or source is None:
        raise RuntimeError('Both comparison materials are required')
    nodes = list(lib.get_material_expressions(material))
    def labelled(label):
        found = [n for n in nodes if isinstance(n, unreal.MaterialExpressionCustom)
                 and str(n.get_editor_property('description')) == label]
        assert len(found) == 1, label
        return found[0]
    def inputs(node):
        return dict(zip(map(str, lib.get_material_expression_input_names(node)),
                        lib.get_inputs_for_material_expression(material, node)))
    current = labelled('Authoritative macro band 0')
    previous = labelled('Previous rendered frame: Authoritative macro band 0')
    for node, texture in [(current, 'MacroSurfaceAtlas'), (previous, 'PreviousMacroSurfaceAtlas')]:
        assert 'RaftSimCrestMacroSample' in str(node.get_editor_property('code'))
        assert str(inputs(node)['Atlas'].get_editor_property('parameter_name')) == texture
    normal = labelled('GPU macro normal with existing detail')
    interp = inputs(normal)['CrestSlope']
    assert isinstance(interp, unreal.MaterialExpressionVertexInterpolator)
    slope = labelled('Shared fine crest world slope correction')
    assert ',false).yz' in str(slope.get_editor_property('code')), 'Must add full crest slope to crest-free base normal'
    assert inputs(interp)['VS'] == slope
    assert inputs(slope)['Atlas'] == inputs(current)['Atlas']
    assert all(n is not None for n in inputs(normal).values()), 'Missing normal input'
    assert sum(isinstance(n, unreal.MaterialExpressionPreviousFrameSwitch) for n in nodes) == 2
    assert material.get_editor_property('output_translucent_velocity')
    assert not material.get_editor_property('is_translucency_velocity_from_depth')
    def signature(mat, root):
        records = {}
        def visit(node):
            if node is None or node.get_name() in records:
                return
            children = list(lib.get_inputs_for_material_expression(mat, node))
            record = dict(kind=node.get_class().get_name(), children=[n.get_name() if n else None for n in children])
            if isinstance(node, unreal.MaterialExpressionCustom):
                record['code'] = str(node.get_editor_property('code'))
            records[node.get_name()] = record
            for child in children:
                visit(child)
        visit(root)
        return records
    for prop in (unreal.MaterialProperty.MP_BASE_COLOR, unreal.MaterialProperty.MP_ROUGHNESS, unreal.MaterialProperty.MP_OPACITY):
        assert signature(material, lib.get_material_property_input_node(material, prop)) == signature(source, lib.get_material_property_input_node(source, prop)), str(prop)
    path = ROOT / 'unreal/Content/RaftSim/Environment/SouthForkSurveyCandidate/M_RaftSim_LiveRiverSurface_StatefulCrestReview.uasset'
    report = dict(passed=True, asset_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  current_and_previous_atlas_bindings=True, vertex_only_slope=True,
                  foam_color_roughness_opacity_graphs_unchanged=True, previous_frame_switches=2,
                  scope='Saved graph wiring, not photographic acceptance')
    (ROOT / 'docs/reconstruction-review-2026-09-07/stateful-crest-normal-graph-audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('Saved fine-crest graph audit passed')


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
