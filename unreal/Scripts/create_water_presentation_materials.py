"""Regenerate only the broad river-water and contact-water VFX materials.

Run this through Unreal Editor with ``-ExecutePythonScript``.  Keeping this
path separate from ``create_contact_evidence_materials.py`` prevents a water
presentation iteration from deleting or rebuilding the independently reviewed
project-owned D4 evidence boulder package.
"""

import unreal


COMMANDS = (
    "RaftSim.CreatePhotorealRiverWaterMaterial",
    "RaftSim.CreateWaterVfxMaterial",
    "RaftSim.CreateNiagaraWaterVfxSystems",
)

for command in COMMANDS:
    unreal.log(f"create_water_presentation_materials: executing {command}")
    unreal.SystemLibrary.execute_console_command(None, command)

unreal.log("create_water_presentation_materials: done")
