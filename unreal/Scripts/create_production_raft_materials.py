"""Regenerate only the runtime wet-coated raft tube and floor materials."""

import unreal


COMMAND = "RaftSim.CreateProductionRaftMaterials"

unreal.log(f"create_production_raft_materials: executing {COMMAND}")
unreal.SystemLibrary.execute_console_command(None, COMMAND)
unreal.log("create_production_raft_materials: done")
