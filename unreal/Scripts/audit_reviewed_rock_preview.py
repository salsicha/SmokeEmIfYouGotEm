"""Read-only diagnostics for the isolated reviewed-rock renderer preview.

The report records mesh UV API availability, material expression wiring, and
texture import settings without modifying or saving any Unreal asset.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOT = "/Game/RaftSim/Experiments/RockMossSet01_BakedScale"
MESH_PATH = (
    f"{ROOT}/SM_RockMossSet01_BakedScale_rock_moss_set_01_rock04"
)
MATERIAL_PATH = f"{ROOT}/M_RockMossSet01_PhysicalPreview"
TEXTURE_PATHS = (
    f"{ROOT}/T_RockMossSet01_BaseColor_PhysicalPreview",
    f"{ROOT}/T_RockMossSet01_NormalGL_PhysicalPreview",
    f"{ROOT}/T_RockMossSet01_Roughness_PhysicalPreview",
)


def _stable(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    getter = getattr(value, "get_path_name", None)
    if callable(getter):
        return getter()
    return str(value)


def _properties(asset: object, names: tuple[str, ...]) -> dict[str, object]:
    values = {}
    for name in names:
        try:
            values[name] = _stable(asset.get_editor_property(name))
        except Exception as error:
            values[name] = {"unavailable": str(error)}
    return values


mesh = unreal.EditorAssetLibrary.load_asset(MESH_PATH)
material = unreal.EditorAssetLibrary.load_asset(MATERIAL_PATH)
textures = [unreal.EditorAssetLibrary.load_asset(path) for path in TEXTURE_PATHS]
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError(f"missing static mesh: {MESH_PATH}")
if not isinstance(material, unreal.Material):
    raise RuntimeError(f"missing material: {MATERIAL_PATH}")
if not all(isinstance(texture, unreal.Texture2D) for texture in textures):
    raise RuntimeError("one or more reviewed-rock preview textures are missing")

diagnostics_dir = Path(unreal.Paths.project_saved_dir()) / "Diagnostics"
diagnostics_dir.mkdir(parents=True, exist_ok=True)
exported_base_color = diagnostics_dir / "m9_reviewed_rock_base_color_export.png"
export_task = unreal.AssetExportTask()
export_task.object = textures[0]
export_task.filename = str(exported_base_color)
export_task.exporter = unreal.TextureExporterPNG()
export_task.automated = True
export_task.prompt = False
export_task.replace_identical = True
texture_exported = unreal.Exporter.run_asset_export_task(export_task)

subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
mesh_description = mesh.get_static_mesh_description(0)
expressions = unreal.MaterialEditingLibrary.get_material_expressions(material)
uv_count = subsystem.get_num_uv_channels(mesh, 0)
vertex_instance_count = mesh_description.get_vertex_instance_count()
uv_ranges = []
for uv_index in range(uv_count):
    minimum = [float("inf"), float("inf")]
    maximum = [float("-inf"), float("-inf")]
    valid_count = 0
    for instance_index in range(vertex_instance_count):
        instance_id = unreal.VertexInstanceID(instance_index)
        if not mesh_description.is_vertex_instance_valid(instance_id):
            continue
        uv = mesh_description.get_vertex_instance_uv(instance_id, uv_index)
        minimum[0] = min(minimum[0], uv.x)
        minimum[1] = min(minimum[1], uv.y)
        maximum[0] = max(maximum[0], uv.x)
        maximum[1] = max(maximum[1], uv.y)
        valid_count += 1
    uv_ranges.append(
        {
            "channel": uv_index,
            "valid_vertex_instances": valid_count,
            "minimum": minimum,
            "maximum": maximum,
        }
    )

material_inputs = {}
for label, property_ in (
    ("base_color", unreal.MaterialProperty.MP_BASE_COLOR),
    ("normal", unreal.MaterialProperty.MP_NORMAL),
    ("roughness", unreal.MaterialProperty.MP_ROUGHNESS),
):
    node = unreal.MaterialEditingLibrary.get_material_property_input_node(
        material, property_
    )
    material_inputs[label] = {
        "node": node.get_name() if node is not None else None,
        "class": node.get_class().get_name() if node is not None else None,
        "output": unreal.MaterialEditingLibrary.get_material_property_input_node_output_name(
            material, property_
        ),
    }
report = {
    "schema": "raftsim.m9.reviewed_rock_preview_audit.v1",
    "read_only": True,
    "asset_mutation": False,
    "mesh": {
        "path": mesh.get_path_name(),
        "triangles_lod0": mesh.get_num_triangles(0),
        "vertices_lod0": mesh.get_num_vertices(0),
        "uv_channel_count": uv_count,
        "uv_ranges": uv_ranges,
        "static_materials": [
            slot.material_interface.get_path_name()
            if slot.material_interface is not None else None
            for slot in mesh.static_materials
        ],
        "mesh_uv_api": sorted(name for name in dir(mesh) if "uv" in name.lower()),
        "mesh_description_api": [],
        "mesh_description_candidates": sorted(
            name for name in dir(mesh) if "description" in name.lower()
        ),
        "subsystem_mesh_description_candidates": sorted(
            name for name in dir(subsystem) if "description" in name.lower()
        ),
        "subsystem_uv_api": sorted(
            name for name in dir(subsystem) if "uv" in name.lower()
        ),
    },
    "material": {
        "path": material.get_path_name(),
        "property_inputs": material_inputs,
        "used_textures": [
            texture.get_path_name()
            for texture in unreal.MaterialEditingLibrary.get_material_used_textures(
                material
            )
        ],
        "expressions": [
            {
                "name": expression.get_name(),
                "class": expression.get_class().get_name(),
                "properties": _properties(
                    expression,
                    ("r", "texture", "sampler_type", "const_a", "const_b"),
                ),
                "inputs": [
                    input_expression.get_name()
                    for input_expression in
                    unreal.MaterialEditingLibrary.get_inputs_for_material_expression(
                        material, expression
                    )
                    if input_expression is not None
                ],
            }
            for expression in expressions
        ],
    },
    "textures": [
        {
            "path": texture.get_path_name(),
            "properties": _properties(
                texture,
                (
                    "srgb",
                    "compression_settings",
                    "flip_green_channel",
                    "address_x",
                    "address_y",
                    "lod_group",
                ),
            ),
            "size_x": texture.blueprint_get_size_x(),
            "size_y": texture.blueprint_get_size_y(),
        }
        for texture in textures
    ],
    "base_color_export": {
        "path": str(exported_base_color),
        "succeeded": texture_exported,
        "errors": list(export_task.errors),
    },
}

output_path = diagnostics_dir / "m9_reviewed_rock_preview_audit.json"
output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
unreal.log(f"audit_reviewed_rock_preview: wrote {output_path}")
