"""Run with -ExecutePythonScript; optional -RaftSimRefreshColoradoWater saves water assets."""
import json
from pathlib import Path
import unreal

if "-RaftSimRefreshColoradoWater" in unreal.SystemLibrary.get_command_line():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.SystemLibrary.execute_console_command(world, "RaftSim.RefreshColoradoHanceWaterMaterials")

root = "/Game/RaftSim/Environment/ColoradoRun/Water/Materials/"
instance = unreal.load_asset(root + "MI_RaftSim_ColoradoHance_LiveVolumeWaterV2")
parent = instance.get_editor_property("parent")
assert parent.get_name() == "M_RaftSim_ColoradoCurrentWaterV3", parent.get_path_name()
expressions = unreal.MaterialEditingLibrary.get_material_expressions(parent)
detail = [e for e in expressions if e.get_class().get_name() == "MaterialExpressionCustom"
          and e.get_editor_property("desc") == "ColoradoCurrentGradientNormalV1"]
assert len(detail) == 1
cutoffs = [e for e in expressions if e.get_class().get_name() == "MaterialExpressionConstant"
           and e.get_editor_property("desc") == "ColoradoResolvedAerationCutoff"]
assert len(cutoffs) == 1 and abs(cutoffs[0].get_editor_property("r") + 0.04) < 1e-6
code = detail[0].get_editor_property("code")
assert "- Current.xy" in code and "ddx(p)" in code and "ddy(p)" in code
assert "sin(" not in code and "WaveClock" not in code
output = Path(unreal.Paths.project_saved_dir()) / "RaftSimValidation/colorado-current-water.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps({"instance": instance.get_path_name(), "parent": parent.get_path_name(), "foam_cutoff": 0.04,
                             "normal_code": code, "expression_count": len(expressions)}, indent=2), encoding="utf-8")
unreal.log(f"Colorado water audit passed: {output}")
