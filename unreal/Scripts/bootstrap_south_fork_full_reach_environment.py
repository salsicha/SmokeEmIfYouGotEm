"""Regenerate and validate the saved South Fork full-reach environment."""

import unreal


unreal.log("bootstrap_south_fork_full_reach_environment: authoring full reach")
unreal.SystemLibrary.execute_console_command(
    None, "RaftSim.CreateSouthForkFullReachEnvironment"
)
unreal.log("bootstrap_south_fork_full_reach_environment: done")
