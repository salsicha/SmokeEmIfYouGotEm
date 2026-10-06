"""Regenerate only project-owned raft and crew materials for review/builds."""

import unreal

unreal.log("bootstrap_raft_crew_materials: authoring production materials")
unreal.SystemLibrary.execute_console_command(None, "RaftSim.CreateRaftCrewMaterials")
unreal.log("bootstrap_raft_crew_materials: done")
