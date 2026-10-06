"""Use -ExecutePythonScript; -RaftSimRefreshPacuareWater explicitly saves water assets."""
import json
from pathlib import Path
import unreal

if "-RaftSimRefreshPacuareWater" in unreal.SystemLibrary.get_command_line():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.SystemLibrary.execute_console_command(world, "RaftSim.RefreshPacuareCurrentWater")

root = "/Game/RaftSim/Environment/PacuareRun/Water/Materials/"
instance = unreal.load_asset(root + "MI_RaftSim_PacuareUpperHuacas_LiveVolumeWaterV1")
parent = instance.get_editor_property("parent")
assert parent.get_name() == "M_RaftSim_PacuareCurrentWaterV2", parent.get_path_name()
expressions = unreal.MaterialEditingLibrary.get_material_expressions(parent)
detail = [e for e in expressions if e.get_class().get_name() == "MaterialExpressionCustom"
          and e.get_editor_property("desc") == "PacuareCurrentGradientNormalV1"]
cutoff = [e for e in expressions if e.get_class().get_name() == "MaterialExpressionConstant"
          and e.get_editor_property("desc") == "PacuareResolvedAerationCutoff"]
assert len(detail) == len(cutoff) == 1
assert abs(cutoff[0].get_editor_property("r") + 0.06) < 1e-6
assert unreal.MaterialEditingLibrary.get_material_property_input_node(parent, unreal.MaterialProperty.MP_NORMAL) == detail[0]
code = detail[0].get_editor_property("code")
assert "- Current.xy" in code and "ddx(p)" in code and "ddy(p)" in code
assert "sin(" not in code and "WaveClock" not in code
output = Path(unreal.Paths.project_saved_dir()) / "RaftSimValidation/pacuare-current-water.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps({"instance": instance.get_path_name(), "parent": parent.get_path_name(),
                             "foam_cutoff": 0.06, "normal_code": code,
                             "expression_count": len(expressions)}, indent=2), encoding="utf-8")
unreal.log(f"Pacuare current water audit passed: {output}")
