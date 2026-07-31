"""Regenerate the source-conditioned South Fork Single Layer Water material."""

import unreal


COMMAND = "RaftSim.CreatePhotorealRiverWaterMaterial"

unreal.log(f"create_photoreal_river_water_material: executing {COMMAND}")
unreal.SystemLibrary.execute_console_command(None, COMMAND)
unreal.log("create_photoreal_river_water_material: done")
