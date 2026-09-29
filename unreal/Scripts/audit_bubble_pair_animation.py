"""Evaluate the actual native pair shape-key rig, including half-frame poses.

Without --saved-scene this builds the production rig in memory only. That mode
does not prove file round-trip, rendered appearance, or coupled 3D equilibrium.
"""
import argparse
import json
from pathlib import Path
import sys
import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_bubble_pair_lab import create_pair_animation, geometry, mesh_volume


def coords(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        values = np.empty(len(mesh.vertices)*3, dtype=np.float32)
        mesh.vertices.foreach_get('co', values)
        return values.reshape((-1, 3)).astype(float)
    finally:
        evaluated.to_mesh_clear()


def run(data, saved_scene):
    scene = bpy.context.scene
    if saved_scene:
        objects = [bpy.data.objects[name] for name in
                   ('Connected pair water', 'Left film', 'Right film')]
        assert scene.render.fps == data['fps']
        assert scene.frame_start == 1 and scene.frame_end == len(data['frames'])
    else:
        objects, _, _ = create_pair_animation(data)
        scene.render.fps = data['fps']
        scene.frame_start = 1
        scene.frame_end = len(data['frames'])
    expected = []
    faces = None
    for row in data['frames']:
        water, current_faces, films, _ = geometry(data['equilibrium'], row['distance_m'])
        if faces is not None:
            assert current_faces == faces
        faces = current_faces
        expected.append([np.asarray(array) for array in (water, films[0][0], films[1][0])])
    rows = []
    for step in range(2*len(expected)-1):
        index, half = divmod(step, 2)
        frame = 1+index
        scene.frame_set(frame, subframe=half*.5)
        arrays = [coords(obj) for obj in objects]
        target = expected[index] if not half else [
            (a+b)*.5 for a, b in zip(expected[index], expected[index+1])]
        errors = [float(np.max(np.abs(a-b))) for a, b in zip(arrays, target)]
        assert max(errors) < 5e-9, errors
        water_volume = mesh_volume(arrays[0], faces)
        assert water_volume > 0
        film_gap = float(arrays[2][:, 0].min()-arrays[1][:, 0].max())
        assert film_gap > 0
        # The same weights used for render interpolation must remain a convex
        # combination: no default Bezier overshoot, inflation or snap-back.
        for obj in objects:
            weights = np.array([key.value for key in obj.data.shape_keys.key_blocks[1:]])
            np.testing.assert_allclose(weights.sum(), 1., atol=1e-6)
            assert weights.min() >= 0 and weights.max() <= 1
        rows.append(dict(frame=frame+half*.5, maximum_coordinate_error_m=max(errors),
                         water_volume_m3=water_volume, film_gap_m=film_gap))
    volumes = np.array([r['water_volume_m3'] for r in rows])
    drift = float(np.ptp(volumes)/volumes[0])
    assert drift < .003, drift
    return dict(saved_scene_checked=saved_scene, evaluated_poses=rows,
                relative_water_volume_range=drift,
                water_volume_range_in_single_bubble_volumes=float(np.ptp(volumes)/
                    data['equilibrium']['model']['nominal_gas_volume_m3']),
                physical_accuracy_accepted=False, visual_accuracy_accepted=False,
                scope='Native shape keys, full and half frames, no film overlap; not a flow simulation or paired pressure-balance validation.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--migration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--saved-scene', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    report = run(json.loads(args.migration.read_text()), args.saved_scene)
    args.output.write_text(json.dumps(report, indent=2))
    print('PAIR_NATIVE_ANIMATION', json.dumps(report), flush=True)
