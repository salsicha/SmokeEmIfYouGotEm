"""Regenerate the rights-tracked CC0 skin and shared corneal eye materials."""

import unreal


COMMAND = "RaftSim.CreateProductionCC0SkinMaterials"
unreal.SystemLibrary.execute_console_command(None, COMMAND)
unreal.log(f"Executed {COMMAND}")
