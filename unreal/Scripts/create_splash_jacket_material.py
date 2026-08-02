"""Rebuild and audit only the production splash-jacket Cloth material."""

import unreal


MATERIAL_PATH = "/Game/RaftSim/Materials/M_RaftSim_SplashJacket"
EXPECTED_TEXTURE_NAMES = {
    "T_RaftSim_PfdRipstop_Albedo",
    "T_RaftSim_PfdRipstop_Normal",
    "T_RaftSim_PfdRipstop_AORoughnessHeight",
}


unreal.log("create_splash_jacket_material: begin")
unreal.SystemLibrary.execute_console_command(
    None,
    "RaftSim.CreateSplashJacketMaterial",
)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

material = unreal.EditorAssetLibrary.load_asset(MATERIAL_PATH)
if not isinstance(material, unreal.Material):
    raise RuntimeError(f"splash-jacket material did not load: {MATERIAL_PATH}")
if material.get_editor_property("blend_mode") != unreal.BlendMode.BLEND_OPAQUE:
    raise RuntimeError("splash-jacket material is not opaque")
if (
    material.get_editor_property("shading_model")
    != unreal.MaterialShadingModel.MSM_CLOTH
):
    raise RuntimeError("splash-jacket material does not use Cloth shading")
used_textures = unreal.MaterialEditingLibrary.get_material_used_textures(material)
used_texture_names = {texture.get_name() for texture in used_textures}
if used_texture_names != EXPECTED_TEXTURE_NAMES:
    raise RuntimeError(
        "splash-jacket material does not use the complete ripstop set: "
        f"{sorted(used_texture_names)}"
    )

unreal.log(
    "create_splash_jacket_material: complete "
    f"textures={len(used_texture_names)} shading=MSM_Cloth"
)
