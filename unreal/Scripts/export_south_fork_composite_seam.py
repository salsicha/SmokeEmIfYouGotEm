"""Blender export of the exact inferred join, in the existing rapid asset frame."""
import hashlib
import json
from pathlib import Path
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/composite_terrain'
OUT = ROOT/'unreal/SourceArt/RaftSim/SouthForkCompositeTerrain20260912'


def main():
    manifest = json.loads((BASE/'manifest.json').read_text())
    source = BASE/'troublemaker_seam.npz'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest['artifacts'][source.name]
    assert not OUT.exists(), 'Use a new export directory for a new geometry revision'
    with np.load(source) as data:
        xyz = data['xyz_navd88_utm_m'].copy()
        faces = data['triangles'][:, [0, 2, 1]].copy()
    xyz -= np.r_[manifest['rapid_origin_utm_m'], manifest['rapid_datum_navd88_m']]
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = .01
    mesh = bpy.data.meshes.new('SouthForkInferredRapidJoin')
    mesh.from_pydata((xyz*[100, -100, 100]).tolist(), [], faces.tolist())
    mesh.update()
    obj = bpy.data.objects.new('SM_SouthForkTroublemakerJoin', mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    mesh.materials.append(bpy.data.materials.new('InferredJoin'))
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    OUT.mkdir(parents=True)
    path = OUT/'SM_SouthForkTroublemakerJoin.fbx'
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={'MESH'},
        global_scale=1., apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS',
        axis_forward='Y', axis_up='Z', bake_anim=False, add_leaf_bones=False, use_mesh_modifiers=True)
    report = dict(fbx=path.relative_to(ROOT).as_posix(), fbx_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        source_geometry_sha256=manifest['artifacts'][source.name], vertex_count=len(xyz), triangle_count=len(faces),
        expected_unreal_bounds_cm=[(xyz.min(axis=0)*100).tolist(), (xyz.max(axis=0)*100).tolist()],
        existing_rapid_actor_scale=[1, -1, 1], full_river_actor_translation_source='full_reach/playable_route/troublemaker_placement.json',
        seam_is_inferred=True, normal_map_integrated=False)
    (OUT/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
