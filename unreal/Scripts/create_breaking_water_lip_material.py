"""Author and audit the project-owned solver-breaking-water lip material."""

import unreal


COMMAND = "RaftSim.CreateBreakingWaterLipMaterial"
ASSET_PATH = "/Game/RaftSim/Materials/M_RaftSim_BreakingWaterLip"

unreal.log(f"create_breaking_water_lip_material: executing {COMMAND}")
unreal.SystemLibrary.execute_console_command(None, COMMAND)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
material = unreal.EditorAssetLibrary.load_asset(ASSET_PATH)
if not isinstance(material, unreal.Material):
    raise RuntimeError(f"breaking-water lip material did not load: {ASSET_PATH}")
if material.get_editor_property("blend_mode") != unreal.BlendMode.BLEND_TRANSLUCENT:
    raise RuntimeError("breaking-water lip material is not translucent")
if not bool(material.get_editor_property("two_sided")):
    raise RuntimeError("breaking-water lip material is not two-sided")
used_texture_names = {
    texture.get_name()
    for texture in unreal.MaterialEditingLibrary.get_material_used_textures(material)
}
required_textures = {
    "T_RaftSim_SouthForkWater_FoamLace",
    "T_RaftSim_SouthForkWater_FlowNormal",
}
if not required_textures.issubset(used_texture_names):
    # NullRHI can leave get_material_used_textures empty even after dependency
    # compilation. Confirm the serialized hard references from the asset
    # registry instead; both checks describe the same authored package graph.
    texture_paths = {
        "T_RaftSim_SouthForkWater_FoamLace": (
            "/Game/RaftSim/Environment/SouthForkFullReach/Water/Textures/"
            "T_RaftSim_SouthForkWater_FoamLace"
        ),
        "T_RaftSim_SouthForkWater_FlowNormal": (
            "/Game/RaftSim/Environment/SouthForkFullReach/Water/Textures/"
            "T_RaftSim_SouthForkWater_FlowNormal"
        ),
    }
    missing_references = []
    for texture_name, texture_path in texture_paths.items():
        referencers = unreal.EditorAssetLibrary.find_package_referencers_for_asset(
            texture_path,
            load_assets_to_confirm=True,
        )
        if ASSET_PATH not in referencers:
            missing_references.append(texture_name)
    if missing_references:
        raise RuntimeError(
            "breaking-water lip package lacks project-owned texture references: "
            f"{missing_references}; material API reported {sorted(used_texture_names)}"
        )
unreal.log(
    "create_breaking_water_lip_material: complete "
    f"textures={sorted(used_texture_names)}"
)
