"""Fail closed when production CC0 facial detail is detached from the head.

The validator accepts either a generated Blender scene or an exported FBX.  It
normalizes distances by the character height so the same limits apply to the
meter-valued Blender source and Unreal-ready centimeter FBX data.

Run from Blender::

    blender --background --python validate_cc0_head_detail_attachment.py -- \
      --input RaftSim_CC0_Guide.fbx --report guide_attachment.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
import sys
import traceback

import bpy
from mathutils import Quaternion, Vector
from mathutils.kdtree import KDTree


DETAIL_LIMITS = {
    "eyes": {"median": 0.010, "p95": 0.015, "centroid": 0.020},
    "brows": {"median": 0.010, "p95": 0.015, "centroid": 0.020},
    "hair": {"median": 0.025, "p95": 0.055, "centroid": 0.050},
}


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--report")
    script_args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(script_args)


def _clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def _load(path: Path) -> None:
    if path.suffix.casefold() == ".blend":
        bpy.ops.wm.open_mainfile(filepath=str(path))
    elif path.suffix.casefold() == ".fbx":
        _clear_scene()
        bpy.ops.import_scene.fbx(filepath=str(path))
    else:
        raise ValueError(f"Unsupported character source: {path}")


def _production_mesh() -> bpy.types.Object:
    candidates = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        names = {
            material.name.casefold()
            for material in obj.data.materials
            if material is not None
        }
        if all(any(term in name for name in names) for term in ("skin", "eyes", "brows", "hair")):
            candidates.append(obj)
    if len(candidates) != 1:
        raise RuntimeError(
            "Expected one joined production mesh with Skin/Eyes/Brows/Hair sections; "
            f"found {[candidate.name for candidate in candidates]}"
        )
    return candidates[0]


def _material_vertices(mesh: bpy.types.Object, term: str) -> set[int]:
    slots = {
        index
        for index, material in enumerate(mesh.data.materials)
        if material is not None and term in material.name.casefold()
    }
    if len(slots) != 1:
        raise RuntimeError(
            f"Expected one {term} material slot on {mesh.name}; found {sorted(slots)}"
        )
    vertices = {
        vertex_index
        for polygon in mesh.data.polygons
        if polygon.material_index in slots
        for vertex_index in polygon.vertices
    }
    if not vertices:
        raise RuntimeError(f"{mesh.name} has an empty {term} section")
    return vertices


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round((len(ordered) - 1) * fraction)))
    return ordered[index]


def _vector_tuple(value: Vector) -> list[float]:
    return [round(component, 8) for component in value]


def _transform_record(obj: bpy.types.Object) -> dict[str, object]:
    return {
        "location": _vector_tuple(obj.location),
        "rotation_euler": _vector_tuple(obj.rotation_euler),
        "scale": _vector_tuple(obj.scale),
        "matrix_world": [
            [round(component, 8) for component in row]
            for row in obj.matrix_world
        ],
    }


def _section_statistics(
    positions_by_index: list[Vector],
    indices: set[int],
    head_skin_tree: KDTree,
    body_height: float,
) -> dict[str, object]:
    positions = [positions_by_index[index] for index in sorted(indices)]
    distances = [head_skin_tree.find(position)[2] / body_height for position in positions]
    centroid = sum(positions, Vector()) / len(positions)
    centroid_distance = head_skin_tree.find(centroid)[2] / body_height
    minimum = Vector(tuple(min(position[axis] for position in positions) for axis in range(3)))
    maximum = Vector(tuple(max(position[axis] for position in positions) for axis in range(3)))
    return {
        "vertices": len(positions),
        "bounds_min": _vector_tuple(minimum),
        "bounds_max": _vector_tuple(maximum),
        "centroid": _vector_tuple(centroid),
        "nearest_head_skin_normalized": {
            "median": round(statistics.median(distances), 8),
            "p95": round(_percentile(distances, 0.95), 8),
            "maximum": round(max(distances), 8),
            "centroid": round(centroid_distance, 8),
        },
    }


def _evaluated_positions(mesh: bpy.types.Object) -> list[Vector]:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated_object = mesh.evaluated_get(depsgraph)
    evaluated_mesh = evaluated_object.to_mesh(
        preserve_all_data_layers=True, depsgraph=depsgraph
    )
    try:
        if len(evaluated_mesh.vertices) != len(mesh.data.vertices):
            raise RuntimeError(
                f"{mesh.name} changes topology during evaluation: "
                f"source={len(mesh.data.vertices)} evaluated={len(evaluated_mesh.vertices)}"
            )
        return [
            evaluated_object.matrix_world @ vertex.co
            for vertex in evaluated_mesh.vertices
        ]
    finally:
        evaluated_object.to_mesh_clear()


def _head_rig(mesh: bpy.types.Object) -> bpy.types.Object:
    rigs = {
        modifier.object
        for modifier in mesh.modifiers
        if modifier.type == "ARMATURE" and modifier.object is not None
    }
    if len(rigs) != 1:
        raise RuntimeError(
            f"Expected one armature modifier on {mesh.name}; "
            f"found {[rig.name for rig in rigs]}"
        )
    rig = next(iter(rigs))
    if rig.pose.bones.get("head") is None:
        raise RuntimeError(f"{rig.name} has no poseable head bone")
    return rig


def _section_snapshot(
    positions: list[Vector],
    head_skin_indices: set[int],
    material_indices: dict[str, set[int]],
    body_height: float,
) -> dict[str, object]:
    tree = KDTree(len(head_skin_indices))
    for tree_index, vertex_index in enumerate(sorted(head_skin_indices)):
        tree.insert(positions[vertex_index], tree_index)
    tree.balance()
    return {
        term: _section_statistics(
            positions, material_indices[term], tree, body_height
        )
        for term in DETAIL_LIMITS
    }


def _reference_skin_pairs(
    positions: list[Vector],
    skin_indices: set[int],
    material_indices: dict[str, set[int]],
) -> dict[str, dict[int, int]]:
    skin_tree = KDTree(len(skin_indices))
    for vertex_index in sorted(skin_indices):
        skin_tree.insert(positions[vertex_index], vertex_index)
    skin_tree.balance()
    return {
        term: {
            detail_index: skin_tree.find(positions[detail_index])[1]
            for detail_index in sorted(material_indices[term])
        }
        for term in DETAIL_LIMITS
    }


def _paired_skin_statistics(
    positions: list[Vector],
    pairs: dict[str, dict[int, int]],
    body_height: float,
) -> dict[str, object]:
    result = {}
    for term, section_pairs in pairs.items():
        distances = [
            (positions[detail_index] - positions[skin_index]).length / body_height
            for detail_index, skin_index in section_pairs.items()
        ]
        result[term] = {
            "vertices": len(distances),
            "median_normalized": round(statistics.median(distances), 8),
            "p95_normalized": round(_percentile(distances, 0.95), 8),
            "maximum_normalized": round(max(distances), 8),
        }
    return result


def _append_failures(
    failures: list[str],
    label: str,
    sections: dict[str, object],
) -> None:
    for term, limits in DETAIL_LIMITS.items():
        actual = sections[term]["nearest_head_skin_normalized"]
        for metric, limit in limits.items():
            if actual[metric] > limit:
                failures.append(
                    f"{label}.{term}.{metric}={actual[metric]:.6f} exceeds "
                    f"{limit:.6f} character heights"
                )


def _validate(path: Path) -> dict[str, object]:
    _load(path)
    mesh = _production_mesh()
    all_positions = _evaluated_positions(mesh)
    minimum = Vector(tuple(min(position[axis] for position in all_positions) for axis in range(3)))
    maximum = Vector(tuple(max(position[axis] for position in all_positions) for axis in range(3)))
    extents = maximum - minimum
    body_height = max(extents)
    if body_height <= 0.0:
        raise RuntimeError(f"{mesh.name} has zero bounds")

    skin_indices = _material_vertices(mesh, "skin")
    head_group = mesh.vertex_groups.get("head")
    if head_group is None:
        raise RuntimeError(f"{mesh.name} has no head vertex group")
    head_skin_indices = {
        index
        for index in skin_indices
        if any(
            assignment.group == head_group.index and assignment.weight >= 0.50
            for assignment in mesh.data.vertices[index].groups
        )
    }
    if not head_skin_indices:
        raise RuntimeError(f"{mesh.name} has no head-weighted Skin vertices")

    material_indices = {
        term: _material_vertices(mesh, term)
        for term in DETAIL_LIMITS
    }
    raw_positions = [mesh.matrix_world @ vertex.co for vertex in mesh.data.vertices]
    raw_sections = _section_snapshot(
        raw_positions, head_skin_indices, material_indices, body_height
    )
    sections = _section_snapshot(
        all_positions, head_skin_indices, material_indices, body_height
    )
    reference_skin_pairs = _reference_skin_pairs(
        all_positions, skin_indices, material_indices
    )
    paired_reference_sections = _paired_skin_statistics(
        all_positions, reference_skin_pairs, body_height
    )
    failures = []
    _append_failures(failures, "raw_reference_pose", raw_sections)
    _append_failures(failures, "reference_pose", sections)

    # A reference-pose proximity check cannot catch facial sections that are
    # accidentally imported on the root bone. Move the head by a large,
    # deterministic fraction of body height and repeat the evaluated-geometry
    # test. Correctly skinned eyes, brows and helmet-contained hair remain
    # attached to the deformed Skin island; root-bound detail is left behind.
    rig = _head_rig(mesh)
    reference_mesh_transform = _transform_record(mesh)
    reference_rig_transform = _transform_record(rig)
    head = rig.pose.bones["head"]
    synthetic_rotation_degrees = 58.0
    head.rotation_mode = "QUATERNION"
    head.rotation_quaternion = (
        Quaternion(Vector((1.0, 0.0, 0.0)), math.radians(synthetic_rotation_degrees))
        @ head.rotation_quaternion
    )
    bpy.context.scene.frame_set(bpy.context.scene.frame_current)
    bpy.context.view_layer.update()
    posed_positions = _evaluated_positions(mesh)
    normalized_head_skin_displacements = [
        (posed_positions[index] - all_positions[index]).length / body_height
        for index in sorted(head_skin_indices)
    ]
    median_head_skin_displacement = statistics.median(
        normalized_head_skin_displacements
    )
    if median_head_skin_displacement < 0.025:
        failures.append(
            "synthetic_head_pose.skin_median_displacement="
            f"{median_head_skin_displacement:.6f} is below 0.025000 character heights"
        )
    posed_sections = _section_snapshot(
        posed_positions, head_skin_indices, material_indices, body_height
    )
    paired_posed_sections = _paired_skin_statistics(
        posed_positions, reference_skin_pairs, body_height
    )
    _append_failures(failures, "synthetic_head_pose", posed_sections)
    for term, limits in DETAIL_LIMITS.items():
        paired = paired_posed_sections[term]
        for metric in ("median", "p95"):
            actual = paired[f"{metric}_normalized"]
            if actual > limits[metric]:
                failures.append(
                    f"synthetic_head_pose.{term}.paired_skin_{metric}="
                    f"{actual:.6f} exceeds {limits[metric]:.6f} character heights"
                )

    report = {
        "schema_version": 2,
        "input": str(path),
        "mesh": mesh.name,
        "mesh_transform": reference_mesh_transform,
        "rig_transform": reference_rig_transform,
        "body_bounds_min": _vector_tuple(minimum),
        "body_bounds_max": _vector_tuple(maximum),
        "normalization_extent": round(body_height, 8),
        "head_skin_vertices": len(head_skin_indices),
        "raw_reference_sections": raw_sections,
        "sections": sections,
        "paired_reference_skin": paired_reference_sections,
        "synthetic_head_pose": {
            "local_x_rotation_degrees": synthetic_rotation_degrees,
            "head_skin_median_displacement_normalized": round(
                median_head_skin_displacement, 8
            ),
            "sections": posed_sections,
            "paired_reference_skin": paired_posed_sections,
        },
        "limits": DETAIL_LIMITS,
        "status": "passed" if not failures else "failed",
        "failures": failures,
    }
    return report


def main() -> None:
    args = _arguments()
    input_path = Path(args.input).resolve()
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    report = _validate(input_path)
    payload = json.dumps(report, indent=2, sort_keys=True)
    if args.report:
        report_path = Path(args.report).resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(payload + "\n", encoding="utf-8")
    print("RAFTSIM_CC0_HEAD_DETAIL_ATTACHMENT", payload)
    if report["failures"]:
        raise RuntimeError("; ".join(report["failures"]))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
