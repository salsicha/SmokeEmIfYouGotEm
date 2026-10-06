"""Refresh the shared GPU-fluid water parent and every river-local instance."""

import unreal


COMMAND = "RaftSim.RefreshAllRiverFluidMaterials"

unreal.log(f"refresh_all_river_fluid_materials: executing {COMMAND}")
unreal.SystemLibrary.execute_console_command(None, COMMAND)
unreal.log("refresh_all_river_fluid_materials: done")
