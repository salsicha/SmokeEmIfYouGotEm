"""Regenerate the presentation-safe live solver surface material."""

import unreal


COMMAND = "RaftSim.CreateLiveRiverSurfaceMaterial"

unreal.log(f"create_live_river_surface_material: executing {COMMAND}")
unreal.SystemLibrary.execute_console_command(None, COMMAND)
unreal.log("create_live_river_surface_material: done")
