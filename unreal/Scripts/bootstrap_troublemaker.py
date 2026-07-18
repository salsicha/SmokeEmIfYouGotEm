"""Generate the Troublemaker rapid map (release-1.0-plan.md P3)."""
import unreal
unreal.log("bootstrap_troublemaker: creating L_Troublemaker")
unreal.SystemLibrary.execute_console_command(None, "RaftSim.CreateTroublemakerMap")
unreal.log("bootstrap_troublemaker: done")
