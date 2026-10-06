"""Regenerate the project-owned raft, crew, and spray material assets.

Run after the editor modules have loaded so the authoring console command is
registered.  The PythonScript commandlet exits when this synchronous script
returns, avoiding fragile semicolon-chained ``-ExecCmds`` startup commands.
"""

import unreal


COMMAND = "RaftSim.CreateRaftCrewMaterials"

unreal.log(f"create_raft_crew_materials: executing {COMMAND}")
unreal.SystemLibrary.execute_console_command(None, COMMAND)
unreal.log("create_raft_crew_materials: done")
