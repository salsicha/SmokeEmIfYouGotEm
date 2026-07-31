"""Author RaftSim's self-contained offline MetaHuman archetype skin.

This command uses only project-owned microdetail textures and installed Unreal
core assets. It does not request cloud rigging, texture synthesis, or account
authentication.
"""

import unreal


unreal.log("create_offline_metahuman_skin_material: begin")
unreal.SystemLibrary.execute_console_command(
    None,
    "RaftSim.CreateOfflineMetaHumanSkinMaterial",
)
unreal.log("create_offline_metahuman_skin_material: complete")
