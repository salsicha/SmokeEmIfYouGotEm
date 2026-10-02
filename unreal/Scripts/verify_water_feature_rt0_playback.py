"""Reopen delivered Blender playback and verify every actual sampled pose.

No simulation domains/cache edits, resave or render. Writes only a new receipt.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy
import numpy as np


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--motion', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    scene = bpy.context.scene; path = Path(bpy.data.filepath)
    if path.name != 'gravity-control.blend' or scene.frame_start != 1 or scene.frame_end != 21 or scene.render.fps != 50:
        raise ValueError('Delivered discrete physical playback context changed')
    motion = json.loads(args.motion.read_text()); poses = np.load(motion['arrays']['poses'], allow_pickle=False)
    pins = {str(path.resolve()): digest(path), str(args.motion.resolve()): digest(args.motion),
        str(Path(__file__).resolve()): digest(__file__), **motion['outputs_sha256']}
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Delivered physical playback changed')
    if any(mod.type == 'FLUID' for obj in scene.objects for mod in obj.modifiers):
        raise ValueError('Unexpected simulation domain: do not access cache settings')
    if any(image.source == 'FILE' for image in bpy.data.images):
        raise ValueError('Playback must not depend on external image assets')
    obj = bpy.data.objects['RT0 free-flight parcel (NOT waterfall acceptance)']
    if len(obj.data.vertices) != 8 or len(obj.data.polygons) != 12:
        raise ValueError('Liquid boundary topology changed')
    if abs(obj.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['IOR'].default_value-1.333) > 1e-6:
        raise ValueError('Water material IOR changed')
    errors = []
    for i, expected in enumerate(poses):
        scene.frame_set(i+1); evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh = evaluated.to_mesh()
        try:
            xyz = np.array([v.co[:] for v in mesh.vertices]); error = float(np.max(np.abs(xyz-expected)))
        finally:
            evaluated.to_mesh_clear()
        if error > 2e-7:
            raise ValueError('Reopened playback differs from computed physical pose')
        errors.append(error)
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Read-only playback check modified evidence')
    result = dict(complete=True, accepted=False, dependency_sha256=pins, poses_checked=21,
        maximum_float32_pose_error_m=max(errors), embedded_geometry=True, simulation_domains=0, external_images=0,
        scope='Reopened delivered engine playback matches all discrete physical gravity-control poses, not between-frame dynamics or accepted waterfall visuals.')
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    print('DELIVERED_RT0_PLAYBACK_VERIFIED', max(errors), flush=True)


if __name__ == '__main__':
    main()
