"""Author photoreal water material, then regenerate river maps with it + lighting."""
import unreal
unreal.log("bootstrap_photoreal: authoring water material")
unreal.SystemLibrary.execute_console_command(None, "RaftSim.CreatePhotorealMaterials")
unreal.log("bootstrap_photoreal: regenerating river maps")
unreal.SystemLibrary.execute_console_command(None, "RaftSim.CreateRiverMaps")
unreal.log("bootstrap_photoreal: done")
