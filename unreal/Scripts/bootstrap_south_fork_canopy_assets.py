"""Regenerate only project-owned South Fork native-species canopy assets."""

import unreal

unreal.log("bootstrap_south_fork_canopy_assets: authoring canopy assets")
unreal.SystemLibrary.execute_console_command(
    None, "RaftSim.RefreshSouthForkGeneratedCanopyAssets"
)
unreal.log("bootstrap_south_fork_canopy_assets: done")
