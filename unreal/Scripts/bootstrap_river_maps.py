"""Generate all five runnable river maps (five-river-simulation-plan.md)."""
import unreal
unreal.log("bootstrap_river_maps: creating river maps")
unreal.SystemLibrary.execute_console_command(None, "RaftSim.CreateRiverMaps")
unreal.log("bootstrap_river_maps: done")
