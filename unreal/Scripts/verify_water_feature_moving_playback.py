"""Read-only reopen of delivered moving-tank playback: every sampled pose."""
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
    parser.add_argument('--surface', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    scene = bpy.context.scene; playback = Path(bpy.data.filepath)
    if playback.name != 'moving-tank.blend' or (scene.frame_start, scene.frame_end, scene.render.fps) != (1, 21, 50):
        raise ValueError('Delivered playback context differs from physical samples')
    report = json.loads(args.surface.read_text())
    pins = {str(playback.resolve()): digest(playback), str(args.surface.resolve()): digest(args.surface),
            str(Path(__file__).resolve()): digest(__file__), **report['outputs_sha256']}
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Physical playback inputs changed')
    if any(mod.type == 'FLUID' for obj in scene.objects for mod in obj.modifiers):
        raise ValueError('Unexpected fluid domain: do not access cache RNA')
    if any(image.source == 'FILE' for image in bpy.data.images):
        raise ValueError('Playback has an external image dependency')
    arrays = {key: np.load(report['arrays'][key], allow_pickle=False) for key in ('poses', 'faces', 'markers')}
    liquid = bpy.data.objects['Computed moving liquid (preliminary slosh calibration)']
    if liquid.modifiers or len(liquid.data.vertices) != arrays['poses'].shape[1]:
        raise ValueError('Actual sampled boundary changed')
    if abs(liquid.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['IOR'].default_value-1.333) > 1e-6:
        raise ValueError('Water material changed')
    faces = np.array([p.vertices[:] for p in liquid.data.polygons])
    if not np.array_equal(faces, arrays['faces']):
        raise ValueError('Saved surface topology changed')
    edges = {}
    for face in faces:
        for a, b in zip(face, np.roll(face, -1)):
            key = tuple(sorted((int(a), int(b)))); edges[key] = edges.get(key, 0)+1
    if any(count != 2 for count in edges.values()):
        raise ValueError('Saved boundary has an open or nonmanifold edge')
    errors = []; marker_error = 0.
    for i, expected in enumerate(arrays['poses']):
        scene.frame_set(i+1); evaluated = liquid.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh = evaluated.to_mesh()
        try:
            actual = np.array([v.co[:] for v in mesh.vertices]); error = float(np.max(np.abs(actual-expected)))
        finally:
            evaluated.to_mesh_clear()
        if error > 2e-7:
            raise ValueError('Reopened engine pose differs from actual computed curved boundary')
        errors.append(error)
        for j, expected_marker in enumerate(arrays['markers'][i]):
            obj = bpy.data.objects[f'Material node marker {j} (diagnostic only)']
            marker_error = max(marker_error, float(np.max(np.abs(np.array(obj.location)-expected_marker))))
    if marker_error > 2e-7:
        raise ValueError('Reopened marker differs from computed material node')
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Read-only verification changed physical evidence')
    result = dict(complete=True, accepted=False, dependency_sha256=pins, poses_checked=21,
        maximum_float32_pose_error_m=max(errors), maximum_marker_error_m=marker_error,
        closed_boundary=True, display_vertices=len(liquid.data.vertices), display_triangles=len(faces),
        simulation_domains=0, external_images=0, embedded_geometry=True,
        scope='Delivered sampled Blender playback readback only: no between-frame fluid simulation or feature acceptance.')
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    print('DELIVERED_MOVING_PLAYBACK_VERIFIED', max(errors), marker_error, flush=True)


if __name__ == '__main__':
    main()
