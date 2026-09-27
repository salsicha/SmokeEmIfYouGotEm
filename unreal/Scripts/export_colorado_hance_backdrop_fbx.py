"""Blender: export the Hance 3DEP terrain backdrop mesh as FBX.

Input: physics/data/real_world/colorado_river_grand_canyon_rowing/terrain/hance_evidence_2021/
hance_evidence_terrain_manifest.json (its `backdrop` block and the mesh .npz written
by physics/scripts/export_hance_evidence_runtime.py). Same vertex convention and
FBX options as the South Fork backdrops: local metres east/north/height, Blender
Y negated, centimetre units; the imported mesh is X east, Y north, and the actor
scale (1, -1, 1) maps it to Unreal +Y south.

Run: blender --background --python unreal/Scripts/export_colorado_hance_backdrop_fbx.py -- --output-dir <new dir>
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TERRAIN = ROOT / 'physics/data/real_world/colorado_river_grand_canyon_rowing/terrain/hance_evidence_2021'
ASSET_NAME = 'SM_RaftSim_ColoradoHance_3DEPBackdrop'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    out = args.output_dir.resolve()
    assert out.is_relative_to(ROOT / 'unreal/SourceArt') and not out.exists(), 'use a new explicit export folder'
    manifest_path = TERRAIN / 'hance_evidence_terrain_manifest.json'
    terrain = json.loads(manifest_path.read_text())
    backdrop = terrain['backdrop']
    mesh_path = ROOT / terrain['outputs']['backdrop_mesh']
    assert sha(mesh_path) == terrain['outputs']['backdrop_mesh_sha256']
    with np.load(mesh_path) as data:
        xyz, triangles = data['xyz_local_m'], data['triangles']
    out.mkdir(parents=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = .01
    material = bpy.data.materials.new('ColoradoHanceBackdrop')
    mesh = bpy.data.meshes.new(ASSET_NAME)
    mesh.from_pydata((xyz * [100, -100, 100]).tolist(), [], triangles.tolist())
    mesh.update()
    obj = bpy.data.objects.new(ASSET_NAME, mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    fbx = out / (ASSET_NAME + '.fbx')
    bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, object_types={'MESH'},
                             global_scale=1., apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS',
                             axis_forward='Y', axis_up='Z', bake_anim=False, add_leaf_bones=False,
                             use_mesh_modifiers=True, mesh_smooth_type='FACE')
    record = dict(schema='raftsim.colorado.hance_backdrop_fbx.v1', asset_name=ASSET_NAME,
                  fbx=fbx.relative_to(ROOT).as_posix(), fbx_sha256=sha(fbx),
                  source_mesh=terrain['outputs']['backdrop_mesh'], source_mesh_sha256=terrain['outputs']['backdrop_mesh_sha256'],
                  terrain_manifest=manifest_path.relative_to(ROOT).as_posix(), terrain_manifest_sha256=sha(manifest_path),
                  drape=terrain['outputs']['backdrop_drape'], drape_sha256=terrain['outputs']['backdrop_drape_sha256'],
                  drape_uv=backdrop['drape']['uv'], vertex_count=int(len(xyz)), triangle_count=int(len(triangles)),
                  expected_mesh_bounds_cm=[(xyz.min(axis=0) * 100).tolist(), (xyz.max(axis=0) * 100).tolist()],
                  actor_translation_cm=backdrop['actor_translation_cm'], actor_scale=backdrop['actor_scale'])
    (out / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')
    print('RAFTSIM_HANCE_BACKDROP_FBX', json.dumps(dict(fbx=record['fbx'], triangles=record['triangle_count'])))


main()
