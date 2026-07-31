"""Author and verify the isolated connected-contact-water V6 review material."""

import unreal


COMMAND = "RaftSim.CreateConnectedContactWaterV6ReviewMaterial"
ASSET_PATH = (
    "/Game/RaftSim/VFX/Water/ConnectedContactWaterV6Review/"
    "M_RaftSim_ConnectedContactWater_V6Review"
)
REQUIRED_TEXTURES = {
    "T_RaftSim_WaterParticleV5Review_SubUV",
    "T_RaftSim_SouthForkWater_FoamLace",
    "T_RaftSim_SouthForkWater_FlowNormal",
}

unreal.log(f"create_connected_contact_water_v6_review_material: executing {COMMAND}")
unreal.SystemLibrary.execute_console_command(None, COMMAND)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

material = unreal.EditorAssetLibrary.load_asset(ASSET_PATH)
if not isinstance(material, unreal.Material):
    raise RuntimeError(f"connected V6 review material did not load: {ASSET_PATH}")
if material.get_editor_property("blend_mode") != unreal.BlendMode.BLEND_TRANSLUCENT:
    raise RuntimeError("connected V6 review material is not translucent")
if not bool(material.get_editor_property("two_sided")):
    raise RuntimeError("connected V6 review material is not two-sided")
used_textures = {
    texture.get_name()
    for texture in unreal.MaterialEditingLibrary.get_material_used_textures(material)
}
missing = REQUIRED_TEXTURES - used_textures
if missing:
    # NullRHI can report no used textures even though the material package has
    # serialized hard references. Confirm the same dependency graph through
    # the asset registry before failing closed.
    texture_paths = {
        "T_RaftSim_WaterParticleV5Review_SubUV": (
            "/Game/RaftSim/VFX/Water/PhotographicSubUVV5Review/Textures/"
            "T_RaftSim_WaterParticleV5Review_SubUV"
        ),
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
    for texture_name in sorted(missing):
        referencers = unreal.EditorAssetLibrary.find_package_referencers_for_asset(
            texture_paths[texture_name], load_assets_to_confirm=True
        )
        if ASSET_PATH not in referencers:
            missing_references.append(texture_name)
    if missing_references:
        raise RuntimeError(
            "connected V6 review material is missing serialized texture inputs: "
            f"{missing_references}; used={sorted(used_textures)}"
        )
if not unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False):
    raise RuntimeError("connected V6 review material did not save")

unreal.log(
    "create_connected_contact_water_v6_review_material: complete "
    f"textures={sorted(used_textures)}"
)
