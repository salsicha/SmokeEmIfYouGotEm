"""Rebuild and audit the five open-shell production river-helmet materials."""

from __future__ import annotations

import unreal


MATERIAL_PATHS = (
    "/Game/RaftSim/Materials/M_RaftSim_Helmet",
    "/Game/RaftSim/Materials/M_RaftSim_Helmet_Red",
    "/Game/RaftSim/Materials/M_RaftSim_Helmet_Yellow",
    "/Game/RaftSim/Materials/M_RaftSim_Helmet_White",
    "/Game/RaftSim/Materials/M_RaftSim_GuideHelmet",
)
AUXILIARY_STATIC_MATERIAL_PATHS = (
    "/Game/RaftSim/Materials/M_RaftSim_PFDWebbing",
    "/Game/RaftSim/Materials/M_RaftSim_PaddleShaft",
)

unreal.log("create_production_helmet_materials: begin")
unreal.SystemLibrary.execute_console_command(
    None,
    "RaftSim.CreateProductionHelmetMaterials",
)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

for asset_path in MATERIAL_PATHS:
    material = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"helmet material did not load: {asset_path}")
    used_textures = unreal.MaterialEditingLibrary.get_material_used_textures(material)
    if used_textures:
        raise RuntimeError(
            f"{asset_path} unexpectedly uses textures: "
            f"{[texture.get_path_name() for texture in used_textures]}"
        )
    if not bool(material.get_editor_property("two_sided")):
        raise RuntimeError(f"{asset_path} would cull the open shell interior")
    if material.get_editor_property("blend_mode") != unreal.BlendMode.BLEND_OPAQUE:
        raise RuntimeError(f"{asset_path} is not opaque")
    unreal.log(f"RaftSim helmet audit: {asset_path} stable open-shell material")

for asset_path in (*MATERIAL_PATHS, *AUXILIARY_STATIC_MATERIAL_PATHS):
    material = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"production helmet material did not load: {asset_path}")
    if not bool(material.get_editor_property("used_with_nanite")):
        raise RuntimeError(f"{asset_path} lacks its persisted Nanite usage permutation")

unreal.log(
    "create_production_helmet_materials: complete "
    f"shell_materials={len(MATERIAL_PATHS)} auxiliary_materials="
    f"{len(AUXILIARY_STATIC_MATERIAL_PATHS)}"
)
