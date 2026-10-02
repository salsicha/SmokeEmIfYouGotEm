"""Render actual saved RT0 translation poses; no liquid simulation/cache edits.

Run in a fresh headless Blender process. Physical scene FPS 50; presentation
slowdown and benchmark limits must be stated when assembling the animation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import bpy
import numpy as np
from mathutils import Vector


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def aim(obj, point):
    obj.rotation_euler = (Vector(point)-obj.location).to_track_quat('-Z', 'Y').to_euler()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--motion', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frames', type=int, default=21)

    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    motion = json.loads(args.motion.read_text()); hashes = {str(args.motion.resolve()): digest(args.motion),
        str(Path(__file__).resolve()): digest(__file__), **motion['outputs_sha256']}
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Pinned motion changed')
    poses = np.load(motion['arrays']['poses'], allow_pickle=False)
    if not 1 <= args.frames <= len(poses):
        raise ValueError('Declared saved pose count required')
    poses = poses[:args.frames]
    faces = np.load(motion['arrays']['boundary_faces'], allow_pickle=False)
    # Orient actual surface outward from the liquid center, without rounding,
    # beveling, skin enlargement or changing the simulation surface.
    center = poses[0].mean(axis=0); triangles = []
    for row in faces:
        tri = list(row); p = poses[0, row]
        if np.dot(np.cross(p[1]-p[0], p[2]-p[0]), p.mean(axis=0)-center) < 0:
            tri[1], tri[2] = tri[2], tri[1]
        triangles.append(tri)
    bpy.ops.wm.read_factory_settings(use_empty=True); scene = bpy.context.scene
    mesh = bpy.data.meshes.new('Exact pressure liquid boundary'); mesh.from_pydata(poses[0].tolist(), [], triangles); mesh.update()
    obj = bpy.data.objects.new('RT0 free-flight parcel (NOT waterfall acceptance)', mesh); scene.collection.objects.link(obj)
    obj.shape_key_add(name='Basis')
    for i, positions in enumerate(poses):
        key = obj.shape_key_add(name=f'Physical t={i*.02:.2f}s')
        for target, xyz in zip(key.data, positions):
            target.co = xyz
        for frame, value in ((max(1, i), 0.), (i+1, 1.), (i+2, 0.)):
            key.value = value; key.keyframe_insert('value', frame=frame)
    # Frames are stored samples, not arbitrary interpolated acceleration.
    water = bpy.data.materials.new('Water IOR 1.333, no foam invented'); water.use_nodes = True
    bsdf = water.node_tree.nodes.get('Principled BSDF'); bsdf.inputs['Base Color'].default_value = (.72, .92, .98, 1.)
    bsdf.inputs['Roughness'].default_value = .065; bsdf.inputs['IOR'].default_value = 1.333
    bsdf.inputs['Transmission Weight'].default_value = 1.; obj.data.materials.append(water)
    # Background and a metric ground reference remain clear of every pose.
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0., 1.3, .6), rotation=(np.pi/2, 0., 0.))
    backdrop = bpy.context.object; mat = bpy.data.materials.new('Neutral backdrop'); mat.use_nodes = True
    mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.025, .045, .07, 1.)
    mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .85
    backdrop.data.materials.append(mat)
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0., 0., -.12)); floor = bpy.context.object; floor.data.materials.append(mat)
    bpy.ops.object.camera_add(location=(1.6, -3., 1.35)); cam = bpy.context.object; aim(cam, (0., 0., .65))
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.5; scene.camera = cam
    for pos, power, size in (((-1.2, -1.8, 2.2), 40., 1.5), ((1., .8, 1.6), 60., 1.), ((.5, -1., .3), 10., 1.)):
        bpy.ops.object.light_add(type='AREA', location=pos); lamp = bpy.context.object; lamp.data.energy = power; lamp.data.shape = 'DISK'; lamp.data.size = size; aim(lamp, (0., 0., .7))
    scene.world = bpy.data.worlds.new('Laboratory world'); scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.25, .35, .48, 1.)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .4
    scene.render.engine = 'CYCLES'; scene.cycles.samples = 24; scene.cycles.use_denoising = True
    scene.render.resolution_x = 640; scene.render.resolution_y = 560; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'; scene.render.fps = 50; scene.frame_start = 1; scene.frame_end = len(poses)
    scene.view_settings.view_transform = 'AgX'; scene.render.film_transparent = False
    args.output.mkdir(); frames = []; started = time.perf_counter(); errors = []
    blend = args.output/'gravity-control.blend'; bpy.ops.wm.save_as_mainfile(filepath=str(blend.resolve()))
    for i, expected in enumerate(poses):
        scene.frame_set(i+1); deps = bpy.context.evaluated_depsgraph_get(); actual = obj.evaluated_get(deps).to_mesh()
        try:
            xyz = np.array([p.co[:] for p in actual.vertices]); error = float(np.max(np.abs(xyz-expected)))
        finally:
            obj.evaluated_get(deps).to_mesh_clear()
        if error > 2e-7:
            raise ValueError('Rendered geometry differs from saved physical pose')
        errors.append(error); path = args.output/f'frame-{i:03d}.png'; scene.render.filepath = str(path.resolve())
        bpy.ops.render.render(write_still=True); frames.append(str(path.resolve())); print('RENDERED_RT0', i, error, flush=True)
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError('Renderer changed physical evidence')
    report = dict(complete=True, accepted=False, frames=frames, playback=str(blend.resolve()), dependency_sha256=hashes,
        outputs_sha256={p: digest(p) for p in [*frames, str(blend.resolve())]},
        maximum_float32_render_pose_error_m=max(errors), physical_frame_seconds=.02,
        total_render_seconds=time.perf_counter()-started,
        preview_only=args.frames != 21,
        scope='Actual saved free-flight gravity-control geometry, not accepted waterfall/splash. Playback physical FPS 50; APNG presentation slowdown must be labelled.')
    with (args.output/'report.json').open('x') as stream:
        json.dump(report, stream, indent=2); stream.write('\n')


if __name__ == '__main__':
    main()


