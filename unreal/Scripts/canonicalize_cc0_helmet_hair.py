"""Rigid-bind the CC0 helmet-contained head island to the head bone.

This deterministic post-process lets an already generated MPFB FBX be
canonicalized without downloading or redistributing the GPL build extension.
The primary generator applies the same rule before export; this script exists
to rebuild the checked-in FBXs from their current rights-tracked source files.

Run from Blender::

    blender --background --python canonicalize_cc0_helmet_hair.py -- \
      --input source.fbx --output canonical.fbx
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import bpy


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    script_args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(script_args)


def _clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def _material_vertex_indices(mesh: bpy.types.Object, term: str) -> set[int]:
    matching_materials = {
        index
        for index, material in enumerate(mesh.data.materials)
        if material is not None and term in material.name.casefold()
    }
    if len(matching_materials) != 1:
        raise RuntimeError(
            f"Expected one named {term} material on {mesh.name}; "
            f"found {matching_materials}"
        )
    return {
        vertex_index
        for polygon in mesh.data.polygons
        if polygon.material_index in matching_materials
        for vertex_index in polygon.vertices
    }


def _connected_material_region(
    mesh: bpy.types.Object,
    term: str,
    seed_indices: set[int],
) -> set[int]:
    """Expand seeds through matching polygons without crossing material seams."""
    matching_materials = {
        index
        for index, material in enumerate(mesh.data.materials)
        if material is not None and term in material.name.casefold()
    }
    polygons = [
        set(polygon.vertices)
        for polygon in mesh.data.polygons
        if polygon.material_index in matching_materials
    ]
    vertex_to_polygons: dict[int, list[int]] = {}
    for polygon_index, vertices in enumerate(polygons):
        for vertex_index in vertices:
            vertex_to_polygons.setdefault(vertex_index, []).append(polygon_index)

    region = set(seed_indices)
    pending = list(seed_indices)
    visited_polygons: set[int] = set()
    while pending:
        vertex_index = pending.pop()
        for polygon_index in vertex_to_polygons.get(vertex_index, ()):
            if polygon_index in visited_polygons:
                continue
            visited_polygons.add(polygon_index)
            for connected_index in polygons[polygon_index]:
                if connected_index not in region:
                    region.add(connected_index)
                    pending.append(connected_index)
    return region


def _rigid_bind_helmet_head_island(mesh: bpy.types.Object) -> dict[str, int]:
    head_group = mesh.vertex_groups.get("head")
    if head_group is None:
        raise RuntimeError(f"{mesh.name} has no head vertex group")
    hair_indices = _material_vertex_indices(mesh, "hair")
    if not hair_indices:
        raise RuntimeError(f"{mesh.name} has an empty hair section")

    skin_indices = _material_vertex_indices(mesh, "skin")
    facial_skin_seeds = {
        index
        for index in skin_indices
        if any(
            assignment.group == head_group.index and assignment.weight >= 0.75
            for assignment in mesh.data.vertices[index].groups
        )
    }
    facial_skin_indices = _connected_material_region(
        mesh, "skin", facial_skin_seeds
    )
    if not facial_skin_indices or not facial_skin_indices.issubset(skin_indices):
        raise RuntimeError(f"{mesh.name} has no connected facial skin region")
    detail_indices = set()
    for term in ("eyes", "brows"):
        detail_indices.update(_material_vertex_indices(mesh, term))
    island_indices = hair_indices | facial_skin_indices | detail_indices
    sorted_indices = sorted(island_indices)
    for group in mesh.vertex_groups:
        group.remove(sorted_indices)
    head_group.add(sorted_indices, 1.0, "REPLACE")

    names = {group.index: group.name for group in mesh.vertex_groups}
    for index in sorted_indices:
        assignments = {
            names[assignment.group]: assignment.weight
            for assignment in mesh.data.vertices[index].groups
            if assignment.weight > 1.0e-6
        }
        if assignments != {"head": 1.0}:
            raise RuntimeError(
                f"Helmet-head vertex {index} retained non-rigid weights: {assignments}"
            )
    return {
        "hair": len(hair_indices),
        "facial_skin_seeds": len(facial_skin_seeds),
        "facial_skin": len(facial_skin_indices),
        "eye_brow": len(detail_indices),
        "total": len(island_indices),
    }


def main() -> None:
    args = _arguments()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    _clear_scene()
    bpy.ops.import_scene.fbx(filepath=str(input_path))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    rigs = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    if len(meshes) != 1 or len(rigs) != 1:
        raise RuntimeError(
            f"Expected one joined mesh and one rig; found meshes={len(meshes)}, rigs={len(rigs)}"
        )
    body = meshes[0]
    rig = rigs[0]
    island_counts = _rigid_bind_helmet_head_island(body)

    # Blender's FBX importer expresses a centimeter-authored file as
    # centimeter-valued mesh/rest data under 0.01 object scales. Re-exporting
    # those transforms verbatim applies the centimeter conversion twice and
    # Unreal receives a 1.8 cm character. Restore the generator's pre-export
    # state: centimeter-valued data, unit object scales, and a scene whose
    # declared unit is one centimeter.
    body.scale = (1.0, 1.0, 1.0)
    rig.scale = (1.0, 1.0, 1.0)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.length_unit = "CENTIMETERS"
    bpy.context.scene.unit_settings.scale_length = 0.01

    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    body.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.fbx(
        filepath=str(output_path),
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        apply_scale_options="FBX_SCALE_ALL",
        global_scale=1.0,
        apply_unit_scale=True,
        axis_forward="-Y",
        axis_up="Z",
        add_leaf_bones=False,
        use_armature_deform_only=True,
        bake_anim=False,
        path_mode="COPY",
        embed_textures=False,
    )
    print(
        "RAFTSIM_CC0_HELMET_HAIR_COMPLETE",
        f"input={input_path}",
        f"output={output_path}",
        f"hair_vertices={island_counts['hair']}",
        f"facial_skin_seed_vertices={island_counts['facial_skin_seeds']}",
        f"facial_skin_vertices={island_counts['facial_skin']}",
        f"eye_brow_vertices={island_counts['eye_brow']}",
        f"head_island_vertices={island_counts['total']}",
        f"bones={len(rig.data.bones)}",
        "unit_scale=centimeter",
    )


if __name__ == "__main__":
    main()
