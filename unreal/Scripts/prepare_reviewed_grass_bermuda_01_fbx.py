"""Prepare Poly Haven Grass Bermuda 01 FBX for Unreal without zero-area forms.

Run with Blender in background mode. The source FBX contains two intentionally
single-blade objects whose polygons collapse under Unreal's FBX conversion and
can assert in the unattended editor. This script removes only those named
objects and exports every other publisher-authored mesh unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy


SOURCE_SHA256 = (
    "ec188edf028e1a76ed2e63f7483165ea765f0212b317e4b73fdc3d64610500cd"
)
REMOVED_OBJECTS = {
    "grass_bermuda_01_single_a",
    "grass_bermuda_01_single_b",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def arguments() -> argparse.Namespace:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(args)


def main() -> None:
    args = arguments()
    source = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve()
    report_path = args.report.expanduser().resolve()
    if sha256(source) != SOURCE_SHA256:
        raise RuntimeError("Grass Bermuda 01 source FBX hash mismatch")

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(source), use_anim=False)

    imported_meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    imported_names = {obj.name for obj in imported_meshes}
    missing_removed = REMOVED_OBJECTS - imported_names
    if missing_removed:
        raise RuntimeError(f"Expected degenerate source forms missing: {sorted(missing_removed)}")
    for name in sorted(REMOVED_OBJECTS):
        bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)

    retained = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if len(retained) < 18:
        raise RuntimeError(f"Expected at least 18 retained mesh forms, found {len(retained)}")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in retained:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = retained[0]

    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=str(output),
        use_selection=True,
        object_types={"MESH"},
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Y",
        axis_up="Z",
        bake_anim=False,
        add_leaf_bones=False,
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        path_mode="STRIP",
    )
    report = {
        "schema": "raftsim.reviewed_grass_bermuda_01_fbx_prep.v1",
        "source": str(source),
        "source_sha256": SOURCE_SHA256,
        "output": str(output),
        "output_sha256": sha256(output),
        "removed_zero_area_forms": sorted(REMOVED_OBJECTS),
        "retained_mesh_forms": sorted(obj.name for obj in retained),
        "retained_mesh_form_count": len(retained),
        "geometry_or_material_authorship_changed": False,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
