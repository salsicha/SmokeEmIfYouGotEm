"""Blender background export of the interpreted Troublemaker rock envelope.

Same frame, winding and authored 45-degree crease shading as
``export_troublemaker_dem_rock_cap.py`` (the installed solid), applied to the
envelope produced by ``physics/scripts/build_troublemaker_rock_envelope.py``.
Topology, XY, the internal floor and the wall footprint are identical to the
installed solid; only dry roof heights above the nearby cooked water margin
differ, and those heights are interpretation, not measurement.

Usage:
  blender --background --factory-startup --python export_troublemaker_rock_envelope.py -- \
      --envelope tmp/rock-envelope-20260926/rock_envelope_v2.npz --output tmp/rock-envelope-20260926/export_v2
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'physics/scripts'))
from rock_corner_normals import corner_normals  # noqa: E402

CREASE_DEGREES = 45.0  # same authored shading as the installed solid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--envelope', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    envelope = args.envelope.resolve()
    report_path = Path(str(envelope) + '.json')
    source = json.loads(report_path.read_text())
    if hashlib.sha256(envelope.read_bytes()).hexdigest() != source['output_sha256']:
        raise ValueError('Envelope archive does not match its build report')
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / 'tmp') or out.exists():
        raise ValueError('Fresh project tmp export directory required')
    with np.load(envelope, allow_pickle=False) as data:
        original = data['solid_vertices_m']
        faces = data['solid_triangles']
        kinds = data['solid_face_kind']
    vertices = original * np.array([100.0, -100.0, 100.0])
    reflected_faces = faces[:, [0, 2, 1]]
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 0.01
    mesh = bpy.data.meshes.new('CapturedRockEnvelope')
    mesh.from_pydata(vertices.tolist(), [], reflected_faces.tolist())
    mesh.update()
    obj = bpy.data.objects.new('SM_CapturedRockEnvelope', mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    normals, shading = corner_normals(vertices, reflected_faces, kinds, CREASE_DEGREES)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    mesh.normals_split_custom_set(normals.reshape(-1, 3).tolist())
    actual = np.array([v.co[:] for v in mesh.vertices], dtype=np.float32)
    actual_faces = np.array([p.vertices[:] for p in mesh.polygons])
    assert np.array_equal(actual, vertices.astype(np.float32))
    assert np.array_equal(actual_faces, reflected_faces)
    out.mkdir(parents=True)
    path = out / 'SM_CapturedRockEnvelope.fbx'
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True, object_types={'MESH'},
        global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS',
        axis_forward='Y', axis_up='Z', bake_anim=False, add_leaf_bones=False,
        use_mesh_modifiers=False, mesh_smooth_type='OFF')
    shading['source_vertices_sha256'] = hashlib.sha256(original.tobytes()).hexdigest()
    shading['source_triangles_sha256'] = hashlib.sha256(faces.tobytes()).hexdigest()
    shading['corner_normals_sha256'] = hashlib.sha256(normals.tobytes()).hexdigest()
    shading['import_normals_required'] = True
    report = dict(
        schema='raftsim.troublemaker_rock_envelope_export.v1',
        envelope=envelope.relative_to(ROOT).as_posix(), envelope_sha256=source['output_sha256'],
        source_cap_sha256=source['source_cap_sha256'],
        fbx=path.relative_to(ROOT).as_posix(),
        fbx_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        vertex_count=len(vertices), triangle_count=len(faces),
        expected_unreal_bounds_cm=[(original.min(axis=0) * 100).tolist(),
                                   (original.max(axis=0) * 100).tolist()],
        actor_scale=[1, -1, 1], shading=shading,
        roof_heights_interpreted=True, faces_measured=False, decimated=False)
    (out / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
