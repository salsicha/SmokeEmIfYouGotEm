"""Refresh and inspect the material used by normal South Fork gameplay."""
import json
from pathlib import Path
import unreal

path = '/Game/RaftSim/Environment/SouthForkFullReach/Water/Materials/M_RaftSim_SouthForkRaftTransmissionWaterV4'
material = unreal.load_asset(path)
assert material
library = unreal.MaterialEditingLibrary

def preserved_inputs():
    properties = ('MP_BASE_COLOR', 'MP_ROUGHNESS', 'MP_OPACITY',
                  'MP_OPACITY_MASK', 'MP_WORLD_POSITION_OFFSET')
    return {name: str(library.get_material_property_input_node(
        material, getattr(unreal.MaterialProperty, name))) for name in properties}

def constants():
    return {e.get_name(): e.get_editor_property('r')
            for e in library.get_material_expressions(material)
            if e.get_class().get_name() == 'MaterialExpressionConstant'}

before_inputs, before_constants = preserved_inputs(), constants()
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(world, 'RaftSim.RefreshSouthForkCurrentNormals')
assert preserved_inputs() == before_inputs
assert constants() == before_constants, 'Normal refresh changed a foam/geometry constant'
expressions = library.get_material_expressions(material)
normal = library.get_material_property_input_node(material, unreal.MaterialProperty.MP_NORMAL)
assert normal.get_editor_property('desc') == 'SouthForkCurrentGradientNormalV1'
code = normal.get_editor_property('code')
assert 'n.simplexGradient(a)' in code and 'n.simplexGradient(b)' in code
assert '- Current.xy' in code and 'ddx(p)' in code and 'ddy(p)' in code
assert 'sin(' not in code and 'WaveClock' not in code
inputs = {str(entry.get_editor_property('input_name')): entry
          for entry in normal.get_editor_property('inputs')}
assert set(inputs) == {'UV', 'Origin', 'Current', 'Foam', 'Strength'}, set(inputs)
count = len(expressions)
unreal.SystemLibrary.execute_console_command(world, 'RaftSim.RefreshSouthForkCurrentNormals')
assert len(library.get_material_expressions(material)) == count, 'Refresh added duplicate nodes'
assert preserved_inputs() == before_inputs and constants() == before_constants
library.recompile_material(material)
assert unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
output = Path(unreal.Paths.project_saved_dir()) / 'RaftSimValidation/southfork-current-normal-20260912.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps({'material': path, 'normal_code': code,
    'preserved_inputs': before_inputs, 'preserved_constant_count': len(before_constants),
    'expression_count': count, 'refresh_idempotent': True,
    'normal_playable_parent_updated': True}, indent=2), encoding='utf-8')
unreal.log(f'South Fork playable current normal audit passed: {output}')
