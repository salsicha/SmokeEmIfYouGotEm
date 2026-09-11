"""Use -ExecutePythonScript; optional -RaftSimRefreshFutaleufuWater saves scoped assets."""
import json
from pathlib import Path
import unreal

if "-RaftSimRefreshFutaleufuWater" in unreal.SystemLibrary.get_command_line():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.SystemLibrary.execute_console_command(world, "RaftSim.RefreshFutaleufuCurrentWater")

root = "/Game/RaftSim/Environment/FutaleufuRun/Water/Materials/"
instance = unreal.load_asset(root + "MI_RaftSim_FutaleufuTerminator_LiveVolumeWaterV3")
parent = instance.get_editor_property("parent")
assert parent.get_name() == "M_RaftSim_FutaleufuCurrentWaterV5", parent.get_path_name()
expressions = unreal.MaterialEditingLibrary.get_material_expressions(parent)
detail = [e for e in expressions if e.get_class().get_name() == "MaterialExpressionCustom"
          and e.get_editor_property("desc") == "FutaleufuCurrentGradientNormalV1"]
cutoffs = [e for e in expressions if e.get_class().get_name() == "MaterialExpressionConstant"
           and e.get_editor_property("desc") == "FutaleufuResolvedAerationCutoff"]
assert len(detail) == len(cutoffs) == 1
assert abs(cutoffs[0].get_editor_property("r") + 0.07) < 1e-6
assert unreal.MaterialEditingLibrary.get_material_property_input_node(parent, unreal.MaterialProperty.MP_NORMAL) == detail[0]
code = detail[0].get_editor_property("code")
assert "- Current.xy" in code and "ddx(p)" in code and "ddy(p)" in code
assert "sin(" not in code and "WaveClock" not in code
assert "n.simplexGradient(a)" in code and "n.simplexGradient(b)" in code
assert "n.gradient(" not in code
output = Path(unreal.Paths.project_saved_dir()) / "RaftSimValidation/futaleufu-current-water.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps({"instance": instance.get_path_name(), "parent": parent.get_path_name(),
                             "foam_cutoff": 0.07, "normal_code": code,
                             "expression_count": len(expressions)}, indent=2), encoding="utf-8")
unreal.log(f"Futaleufu current water audit passed: {output}")
