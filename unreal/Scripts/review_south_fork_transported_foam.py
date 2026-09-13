"""Install and audit transported foam optics in the normal playable parent."""
import json
from pathlib import Path
import unreal

PATH = '/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/M_RaftSim_SouthForkRaftTransmissionWaterV4'
lib = unreal.MaterialEditingLibrary
material = unreal.load_asset(PATH)
assert material


def inputs(node):
    return dict(zip(map(str, lib.get_material_expression_input_names(node)),
                    lib.get_inputs_for_material_expression(material, node)))


def graph(node, result=None):
    result = {} if result is None else result
    if node is None or node.get_name() in result:
        return result
    links = inputs(node)
    row = {'class': node.get_class().get_name(),
           'inputs': {pin: child.get_name() if child else None for pin, child in links.items()}}
    for prop in ('code', 'r', 'default_value', 'parameter_name', 'u_tiling', 'v_tiling'):
        try:
            row[prop] = str(node.get_editor_property(prop))
        except Exception:
            pass
    result[node.get_name()] = row
    for child in links.values():
        graph(child, result)
    return result


def protected_graphs():
    return {name: graph(lib.get_material_property_input_node(material, getattr(unreal.MaterialProperty, name)))
            for name in ('MP_WORLD_POSITION_OFFSET', 'MP_OPACITY_MASK', 'MP_NORMAL')}


before = protected_graphs()
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(world, 'RaftSim.RefreshSouthForkCurrentNormals')
assert protected_graphs() == before, 'Foam optics changed geometry, wet coverage or normals'
expressions = lib.get_material_expressions(material)
coverage, = [node for node in expressions
             if node.get_editor_property('desc') == 'SouthForkTransportedFoamOpticsV1']
links = inputs(coverage)
assert set(links) == {'Legacy', 'VertexFoam', 'Lace', 'OpticalDensity'}, links
assert links['VertexFoam'].get_class().get_name() == 'MaterialExpressionVertexColor'
assert str(links['Lace'].get_editor_property('parameter_name')) == 'WhitewaterFoamLace'
lace_graph = graph(links['Lace'])
assert any(row.get('parameter_name') == 'RaftSimFoamAdvectionMeters' for row in lace_graph.values())
consumers = [node.get_name() for node in expressions if coverage in inputs(node).values()]
assert len(consumers) == 4, consumers  # colour, roughness, opacity, water scattering
code = coverage.get_editor_property('code')
assert 'saturate(VertexFoam.r)' in code and 'fwidth(Lace.r)' in code
assert 'Legacy' not in code and 'Speed' not in code
count = len(expressions)
unreal.SystemLibrary.execute_console_command(world, 'RaftSim.RefreshSouthForkCurrentNormals')
assert len(lib.get_material_expressions(material)) == count
assert protected_graphs() == before
lib.recompile_material(material)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
assert unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
output = Path(unreal.Paths.project_saved_dir()) / 'RaftSimValidation/southfork-transported-foam-20260912.json'
output.write_text(json.dumps({'material': PATH, 'protected_graphs_unchanged': True,
    'current_advected_lace': True, 'optical_consumers': consumers,
    'expression_count': count, 'refresh_idempotent': True, 'code': code,
    'appearance_parameters_measured': False, 'physical_acceptance': False}, indent=2))
unreal.log(f'South Fork transported foam optical audit passed: {output}')
