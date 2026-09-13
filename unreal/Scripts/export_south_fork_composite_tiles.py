"""Blender: export full-river source-exact tiles with small local coordinates."""
import hashlib
import json
import argparse
import sys
from pathlib import Path
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/composite_terrain/render_tiles/manifest.json'
OUT = ROOT/'unreal/SourceArt/RaftSim/SouthForkCompositeTerrain20260912/Tiles'


def main():
    global SOURCE, OUT
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-manifest', type=Path, default=SOURCE)
    parser.add_argument('--output-dir', type=Path, default=OUT)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    SOURCE, OUT = args.source_manifest.resolve(), args.output_dir.resolve()
    assert SOURCE.is_relative_to(ROOT/'physics/data') and OUT.is_relative_to(ROOT/'unreal/SourceArt')
    manifest = json.loads(SOURCE.read_text())
    assert not OUT.exists(), 'Use a new explicit export revision, not overwrite'
    OUT.mkdir(parents=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = .01
    material = bpy.data.materials.new('SouthForkCompositeTerrain')
    records = []
    for index, tile in enumerate(manifest['tiles']):
        source = ROOT/tile['path']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == tile['sha256']
        with np.load(source) as data:
            xyz, triangles = data['xyz_local_m'], data['triangles']
        name = 'SM_SouthFork_'+tile['name']
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata((xyz*[100, -100, 100]).tolist(), [], triangles.tolist())
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        mesh.materials.append(material)
        for polygon in mesh.polygons:
            polygon.use_smooth = True
        path = OUT/(name+'.fbx')
        bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={'MESH'},
            global_scale=1., apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS',
            axis_forward='Y', axis_up='Z', bake_anim=False, add_leaf_bones=False,
            use_mesh_modifiers=True, mesh_smooth_type='FACE')
        record = dict(tile, asset_name=name, fbx=path.relative_to(ROOT).as_posix(),
            fbx_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            expected_unreal_bounds_cm=[(xyz.min(axis=0)*100).tolist(), (xyz.max(axis=0)*100).tolist()])
        selected = triangles[np.linspace(0, len(triangles)-1, min(8, len(triangles))).astype(int)]
        record['local_engine_collision_probes_cm'] = (xyz[selected].mean(axis=1)*[100, -100, 100]).tolist()
        records.append(record)
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.meshes.remove(mesh)
        if index % 25 == 0:
            print(f'Exported full-river terrain tile {index+1}/{len(manifest["tiles"])}', flush=True)
    output = dict(source_tile_manifest_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        no_simplification=True, normal_map_integrated=False, tiles=records)
    (OUT/'manifest.json').write_text(json.dumps(output, indent=2)+'\n')
    print(f'Completed {len(records)} source-exact full-river tile exports', flush=True)


if __name__ == '__main__':
    main()
