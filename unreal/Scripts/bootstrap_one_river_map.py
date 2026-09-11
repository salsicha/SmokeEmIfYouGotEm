"""Regenerate one compact prototype map; require an explicit supported name.

This overwrites that prototype map. South Fork and Zambezi have dedicated
full-reach builders and must not be routed through this utility.
"""
import os
import unreal

names = {name.lower(): name for name in ('Hance', 'UpperHuacas', 'Terminator', 'LavaCanyon')}
requested = os.environ.get("RAFTSIM_RIVER_FILTER", "").strip().removeprefix('L_').lower()
if requested not in names:
    raise ValueError('Set RAFTSIM_RIVER_FILTER to Hance, UpperHuacas, Terminator, or LavaCanyon; empty filters are not allowed')
flt = names[requested]
unreal.log(f"bootstrap_one_river_map: filter={flt}")
unreal.SystemLibrary.execute_console_command(None, f"RaftSim.CreateRiverMaps {flt}".strip())
unreal.log("bootstrap_one_river_map: done")
