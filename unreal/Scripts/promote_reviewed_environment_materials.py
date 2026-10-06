"""Persist reviewed environment usages and repair masked foliage shadows."""

import unreal


COMMAND = "RaftSim.PromoteReviewedEnvironmentMaterials"

unreal.log(f"promote_reviewed_environment_materials: executing {COMMAND}")
unreal.SystemLibrary.execute_console_command(None, COMMAND)
unreal.log("promote_reviewed_environment_materials: done")
