"""Regenerate only the water and project-owned D4 evidence-rock materials."""

import unreal


COMMANDS = (
    "RaftSim.CreatePhotorealRiverWaterMaterial",
    "RaftSim.CreateRiverBoulderMaterial",
)

# Recreate the boulder package rather than mutating an older expression graph
# in place. UE serializes expression UObjects as package exports, so merely
# disconnecting/removing a legacy normal sample can leave its unavailable
# texture reference behind and break a clean Shipping cook.
BOULDER_ASSET = "/Game/RaftSim/Materials/M_RaftSim_RiverBoulder"
if unreal.EditorAssetLibrary.does_asset_exist(BOULDER_ASSET):
    unreal.log(f"create_contact_evidence_materials: deleting stale {BOULDER_ASSET}")
    if not unreal.EditorAssetLibrary.delete_asset(BOULDER_ASSET):
        raise RuntimeError(f"Could not delete stale material asset: {BOULDER_ASSET}")

for command in COMMANDS:
    unreal.log(f"create_contact_evidence_materials: executing {command}")
    unreal.SystemLibrary.execute_console_command(None, command)

unreal.log("create_contact_evidence_materials: done")
