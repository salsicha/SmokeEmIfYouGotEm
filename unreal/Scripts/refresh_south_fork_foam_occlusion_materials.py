"""Refresh only the shared transmitting-water and raft occlusion materials."""

import unreal


unreal.log("refresh_south_fork_foam_occlusion_materials: refreshing materials")
unreal.SystemLibrary.execute_console_command(
    None, "RaftSim.RefreshSouthForkFoamOcclusionMaterials"
)
unreal.log("refresh_south_fork_foam_occlusion_materials: done")
