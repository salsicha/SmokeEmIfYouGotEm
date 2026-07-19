"""Regenerate a single river map by name filter. Set RAFTSIM_RIVER_FILTER env."""
import os, unreal
flt = os.environ.get("RAFTSIM_RIVER_FILTER", "")
unreal.log(f"bootstrap_one_river_map: filter={flt}")
unreal.SystemLibrary.execute_console_command(None, f"RaftSim.CreateRiverMaps {flt}".strip())
unreal.log("bootstrap_one_river_map: done")
