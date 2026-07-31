"""Regenerate only the skeletal-compatible production crew wetsuit material."""

import unreal


COMMAND = "RaftSim.CreateProductionCrewWetsuitMaterial"

unreal.log(f"create_production_crew_wetsuit_material: executing {COMMAND}")
unreal.SystemLibrary.execute_console_command(None, COMMAND)
unreal.log("create_production_crew_wetsuit_material: done")
