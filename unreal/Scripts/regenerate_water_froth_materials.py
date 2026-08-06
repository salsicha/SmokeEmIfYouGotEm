"""Regenerate the authored river-water material and the shared transmission
parent after froth-graph changes (release-review 2026-08-06 whitewater work).

Order matters: the authored source material must be rebuilt first; the parent
is a duplicate of it and must be recreated afterwards (delete the saved
parent .uasset before running so LoadOrCreate recreates it from the updated
source)."""

import unreal

for command in (
    "RaftSim.CreatePhotorealRiverWaterMaterial",
    "RaftSim.CreateSouthForkTransmissionWater",
):
    unreal.log(f"RaftSim froth regen: {command}")
    unreal.SystemLibrary.execute_console_command(None, command)
