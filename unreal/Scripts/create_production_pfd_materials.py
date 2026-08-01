"""Rebuild and audit the four high-visibility production PFD materials."""

import unreal


MATERIAL_PATHS = (
    "/Game/RaftSim/Materials/M_RaftSim_CrewPFD",
    "/Game/RaftSim/Materials/M_RaftSim_PFD_Red",
    "/Game/RaftSim/Materials/M_RaftSim_PFD_Yellow",
    "/Game/RaftSim/Materials/M_RaftSim_PFD_Blue",
)
EXPECTED_TEXTURE_NAMES = {
    "T_RaftSim_PfdRipstop_Albedo",
    "T_RaftSim_PfdRipstop_Normal",
    "T_RaftSim_PfdRipstop_AORoughnessHeight",
}


unreal.log("create_production_pfd_materials: begin")
unreal.SystemLibrary.execute_console_command(
    None,
    "RaftSim.CreateProductionPfdMaterials",
)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

for asset_path in MATERIAL_PATHS:
    material = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"production PFD material did not load: {asset_path}")
    if not bool(material.get_editor_property("used_with_nanite")):
        raise RuntimeError(f"{asset_path} lacks its persisted Nanite usage permutation")
    if material.get_editor_property("blend_mode") != unreal.BlendMode.BLEND_OPAQUE:
        raise RuntimeError(f"{asset_path} is not opaque")
    if (
        material.get_editor_property("shading_model")
        != unreal.MaterialShadingModel.MSM_CLOTH
    ):
        raise RuntimeError(f"{asset_path} does not use the cloth/fuzz shading model")
    used_textures = unreal.MaterialEditingLibrary.get_material_used_textures(material)
    used_texture_names = {texture.get_name() for texture in used_textures}
    if used_texture_names != EXPECTED_TEXTURE_NAMES:
        raise RuntimeError(
            f"{asset_path} does not use the complete PFD ripstop set: "
            f"{sorted(used_texture_names)}"
        )

unreal.log(
    f"create_production_pfd_materials: complete materials={len(MATERIAL_PATHS)}"
)
