"""Run the vertical-slice bootstrap console commands (release-1.0-plan.md P1).

Invoke via:
UnrealEditor-Cmd <uproject> -stdout -FullStdOutLogOutput -unattended -nop4 \
    -nosplash -RenderOffscreen -NoSound -run=pythonscript \
    -script="bootstrap_vertical_slice.py"
or -ExecutePythonScript="<path>". Each console command runs synchronously.
"""

import unreal

for command in (
    "RaftSim.CreateVerticalSliceInputAssets",
    "RaftSim.CreateVerticalSliceCoreMaps",
):
    unreal.log(f"bootstrap_vertical_slice: executing {command}")
    unreal.SystemLibrary.execute_console_command(None, command)

unreal.log("bootstrap_vertical_slice: done")
