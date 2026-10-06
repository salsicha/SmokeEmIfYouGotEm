"""Author the installed baked MetaHuman face shader with RaftSim's PPE crop."""

import unreal


unreal.log("create_cropped_metahuman_face_material: begin")
unreal.SystemLibrary.execute_console_command(
    None,
    "RaftSim.CreateCroppedMetaHumanFaceMaterial",
)
unreal.log("create_cropped_metahuman_face_material: complete")
