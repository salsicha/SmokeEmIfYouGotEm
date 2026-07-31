"""Regenerate only the five rights-tracked production CC0 skin materials."""

import unreal


COMMAND = "RaftSim.CreateProductionCC0SkinMaterials"
unreal.SystemLibrary.execute_console_command(None, COMMAND)
unreal.log(f"Executed {COMMAND}")
