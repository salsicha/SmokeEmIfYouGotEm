"""Compare the rest mesh and skin weights of two exported character FBX files.

Run from Blender::

    blender --background --python diagnose_character_fbx.py -- old.fbx new.fbx

This is a diagnostic only: it does not modify either source file.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys

import bpy
from mathutils.kdtree import KDTree


def _args() -> tuple[Path, Path]:
    script_args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(script_args) != 2:
        raise SystemExit("usage: diagnose_character_fbx.py -- old.fbx new.fbx")
    return Path(script_args[0]).resolve(), Path(script_args[1]).resolve()


def _clear() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def _load(path: Path):
    _clear()
    bpy.ops.import_scene.fbx(filepath=str(path))
    body = max(
        (obj for obj in bpy.context.scene.objects if obj.type == "MESH"),
        key=lambda obj: len(obj.data.vertices),
    )
    coordinates = [vertex.co.copy() for vertex in body.data.vertices]
    group_names = {group.index: group.name for group in body.vertex_groups}
    weights = [
        {
            group_names[assignment.group]: assignment.weight
            for assignment in vertex.groups
            if assignment.weight > 1.0e-6
        }
        for vertex in body.data.vertices
    ]
    return body.name, coordinates, weights


def main() -> None:
    old_path, new_path = _args()
    old_name, old_coordinates, old_weights = _load(old_path)
    new_name, new_coordinates, new_weights = _load(new_path)

    tree = KDTree(len(new_coordinates))
    for index, coordinate in enumerate(new_coordinates):
        tree.insert(coordinate, index)
    tree.balance()

    distance_buckets: Counter[str] = Counter()
    changed_weights = 0
    changed_head_weights = 0
    max_weight_delta = 0.0
    matched_body_vertices = 0
    for coordinate, expected in zip(old_coordinates, old_weights):
        _nearest, index, distance = tree.find(coordinate)
        if distance <= 1.0e-4:
            distance_buckets["exact"] += 1
            matched_body_vertices += 1
        elif distance <= 1.0e-2:
            distance_buckets["near"] += 1
        else:
            distance_buckets["different"] += 1
            continue
        actual = new_weights[index]
        delta = max(
            (abs(expected.get(name, 0.0) - actual.get(name, 0.0))
             for name in expected.keys() | actual.keys()),
            default=0.0,
        )
        max_weight_delta = max(max_weight_delta, delta)
        if delta > 1.0e-4:
            changed_weights += 1
            if expected.get("head", 0.0) > 0.0 or actual.get("head", 0.0) > 0.0:
                changed_head_weights += 1

    print(
        "RAFTSIM_CHARACTER_FBX_DIAGNOSTIC",
        f"old={old_path}",
        f"new={new_path}",
        f"old_mesh={old_name}",
        f"new_mesh={new_name}",
        f"old_vertices={len(old_coordinates)}",
        f"new_vertices={len(new_coordinates)}",
        f"matched={matched_body_vertices}",
        f"distance_buckets={dict(distance_buckets)}",
        f"changed_weights={changed_weights}",
        f"changed_head_weights={changed_head_weights}",
        f"max_weight_delta={max_weight_delta:.8f}",
    )


if __name__ == "__main__":
    main()
