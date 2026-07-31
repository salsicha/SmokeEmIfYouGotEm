"""Import and regenerate only the project-owned river-boulder material."""

import unreal


COMMAND = "RaftSim.CreateRiverBoulderMaterial"

unreal.log(f"create_river_boulder_material: executing {COMMAND}")
unreal.SystemLibrary.execute_console_command(None, COMMAND)
unreal.log("create_river_boulder_material: done")
