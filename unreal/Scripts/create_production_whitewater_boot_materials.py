"""Build and assign dedicated PBR materials for the production river boot."""

from __future__ import annotations

import json
from pathlib import Path

import unreal


REPO_ROOT = Path(__file__).resolve().parents[2]
MATERIAL_ROOT = "/Game/RaftSim/Materials"
BOOT_ASSET_PATH = (
    "/Game/RaftSim/Equipment/Production/"
    "SM_RaftSim_WhitewaterRiverBoot"
)
TEXTURE_ROOT = "/Game/RaftSim/Equipment/Textures"
REPORT_PATH = (
    REPO_ROOT
    / "unreal/Saved/RaftSimValidation/m9/production-whitewater-river-boot-materials.json"
)


def disconnect_and_clear(material: unreal.Material) -> None:
    material.modify()
    for property_ in (
        unreal.MaterialProperty.MP_BASE_COLOR,
        unreal.MaterialProperty.MP_NORMAL,
        unreal.MaterialProperty.MP_ROUGHNESS,
        unreal.MaterialProperty.MP_AMBIENT_OCCLUSION,
        unreal.MaterialProperty.MP_SPECULAR,
        unreal.MaterialProperty.MP_METALLIC,
    ):
        unreal.MaterialEditingLibrary.disconnect_material_property(material, property_)
    unreal.MaterialEditingLibrary.delete_all_material_expressions(material)


def load_or_create(name: str) -> unreal.Material:
    material = unreal.load_asset(f"{MATERIAL_ROOT}/{name}")
    if not isinstance(material, unreal.Material):
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, MATERIAL_ROOT, unreal.Material, unreal.MaterialFactoryNew()
        )
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"Could not create production river-boot material {name}")
    disconnect_and_clear(material)
    material.set_editor_property("two_sided", False)
    return material


def constant(material: unreal.Material, value: float, x: int, y: int):
    expression = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, x, y
    )
    expression.r = value
    return expression


def build_upper() -> unreal.Material:
    material = load_or_create("M_RaftSim_RiverBootUpper")
    albedo = unreal.load_asset(f"{TEXTURE_ROOT}/T_RaftSim_WetsuitNeoprene_Albedo")
    normal = unreal.load_asset(f"{TEXTURE_ROOT}/T_RaftSim_WetsuitNeoprene_Normal")
    packed = unreal.load_asset(
        f"{TEXTURE_ROOT}/T_RaftSim_WetsuitNeoprene_AORoughnessHeight"
    )
    if not all(isinstance(item, unreal.Texture2D) for item in (albedo, normal, packed)):
        raise RuntimeError("Project-owned neoprene texture set is incomplete")

    albedo_sample = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, -700, -180
    )
    albedo_sample.texture = albedo
    albedo_sample.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_COLOR
    tint = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -700, 20
    )
    tint.constant = unreal.LinearColor(0.048, 0.052, 0.058, 1.0)
    tinted = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionMultiply, -390, -120
    )
    normal_sample = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, -700, 220
    )
    normal_sample.texture = normal
    normal_sample.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
    packed_sample = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, -700, 420
    )
    packed_sample.texture = packed
    packed_sample.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_MASKS
    specular = constant(material, 0.24, -390, 520)

    unreal.MaterialEditingLibrary.connect_material_expressions(
        albedo_sample, "RGB", tinted, "A"
    )
    unreal.MaterialEditingLibrary.connect_material_expressions(tint, "", tinted, "B")
    unreal.MaterialEditingLibrary.connect_material_property(
        tinted, "", unreal.MaterialProperty.MP_BASE_COLOR
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        normal_sample, "RGB", unreal.MaterialProperty.MP_NORMAL
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        packed_sample, "G", unreal.MaterialProperty.MP_ROUGHNESS
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        packed_sample, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        specular, "", unreal.MaterialProperty.MP_SPECULAR
    )
    return material


def build_rubber() -> unreal.Material:
    material = load_or_create("M_RaftSim_RiverBootRubber")
    base = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -420, -80
    )
    base.constant = unreal.LinearColor(0.034, 0.036, 0.040, 1.0)
    roughness = constant(material, 0.62, -420, 90)
    specular = constant(material, 0.28, -420, 230)
    unreal.MaterialEditingLibrary.connect_material_property(
        base, "", unreal.MaterialProperty.MP_BASE_COLOR
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        roughness, "", unreal.MaterialProperty.MP_ROUGHNESS
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        specular, "", unreal.MaterialProperty.MP_SPECULAR
    )
    return material


def compile_and_save(material: unreal.Material) -> None:
    material.modify()
    if not unreal.MaterialEditingLibrary.has_material_usage(
        material, unreal.MaterialUsage.MATUSAGE_NANITE
    ):
        unreal.MaterialEditingLibrary.set_base_material_usage(
            material, unreal.MaterialUsage.MATUSAGE_NANITE, True
        )
    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    errors = unreal.MaterialEditingLibrary.recompile_material(material)
    if errors:
        raise RuntimeError(
            f"{material.get_name()} failed to compile: "
            + "; ".join(str(error) for error in errors)
        )
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    if not bool(material.get_editor_property("used_with_nanite")):
        raise RuntimeError(
            f"{material.get_name()} lacks its persisted Nanite usage permutation"
        )


def main() -> None:
    unreal.log("create_production_whitewater_boot_materials: begin")
    upper = build_upper()
    rubber = build_rubber()
    for material in (upper, rubber):
        compile_and_save(material)

    mesh = unreal.load_asset(BOOT_ASSET_PATH)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError("Production river-boot static mesh is absent")
    mesh.set_material(0, upper)
    mesh.set_material(1, rubber)
    mesh.set_material(2, rubber)
    mesh.modify()
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

    report = {
        "schema_version": 1,
        "status": "production_river_boot_materials_built_and_assigned",
        "boot_asset": mesh.get_path_name(),
        "material_slots": [
            {
                "slot": str(slot.material_slot_name),
                "material": slot.material_interface.get_path_name()
                if slot.material_interface
                else None,
            }
            for slot in mesh.static_materials
        ],
        "upper": {
            "material": upper.get_path_name(),
            "nanite_usage_persisted": bool(
                upper.get_editor_property("used_with_nanite")
            ),
            "project_owned_texture_set": "WetsuitNeoprene",
            "base_tint_linear": [0.048, 0.052, 0.058],
            "specular": 0.24,
        },
        "rubber": {
            "material": rubber.get_path_name(),
            "nanite_usage_persisted": bool(
                rubber.get_editor_property("used_with_nanite")
            ),
            "base_color_linear": [0.034, 0.036, 0.040],
            "roughness": 0.62,
            "specular": 0.28,
        },
        "runtime_boundary": (
            "Visual materials only; no crew pose, mass, water, D3/D4, collision, "
            "raft, rescue or progression authority."
        ),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(
        "RAFTSIM_PRODUCTION_RIVER_BOOT_MATERIALS="
        + json.dumps(report, sort_keys=True)
    )
    unreal.log("create_production_whitewater_boot_materials: complete")


if __name__ == "__main__":
    main()


