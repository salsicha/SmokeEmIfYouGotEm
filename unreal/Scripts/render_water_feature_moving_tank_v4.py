"""Moving-tank views v4: uncropped diagnostic tank, unchanged computed motion."""
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


def material(name, color, roughness, transmission=0., ior=1.45):
    mat = bpy.data.materials.new(name); mat.use_nodes = True; node = mat.node_tree.nodes['Principled BSDF']
    node.inputs['Base Color'].default_value = (*color, 1.); node.inputs['Roughness'].default_value = roughness
    node.inputs['Transmission Weight'].default_value = transmission; node.inputs['IOR'].default_value = ior
    return mat


def cube(name, center, dimensions, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center); obj = bpy.context.object; obj.name = name
    obj.dimensions = dimensions; obj.data.materials.append(mat); return obj


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--surface', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frames', type=int, default=21)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    report = json.loads(args.surface.read_text()); pins = {str(args.surface.resolve()): digest(args.surface),
        str(Path(__file__).resolve()): digest(__file__), **report['outputs_sha256']}
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Qualified actual surface changed')
    poses = np.load(report['arrays']['poses'], allow_pickle=False); faces = np.load(report['arrays']['faces'], allow_pickle=False)
    markers = np.load(report['arrays']['markers'], allow_pickle=False)
    if not 1 <= args.frames <= len(poses):
        raise ValueError('Declared discrete physical views required')
    bpy.ops.wm.read_factory_settings(use_empty=True); scene = bpy.context.scene
    mesh = bpy.data.meshes.new('Actual moving curved-boundary samples'); mesh.from_pydata(poses[0].tolist(), [], faces.tolist()); mesh.update()
    liquid = bpy.data.objects.new('Computed moving liquid (preliminary slosh calibration)', mesh); scene.collection.objects.link(liquid)
    for p in liquid.data.polygons:
        p.use_smooth = True  # lighting normals only, no geometry smoothing.
    mesh.set_sharp_from_angle(angle=np.pi/4)  # Do not blend normals across 90-degree wall/bed contacts.
    liquid.shape_key_add(name='Basis')
    for i, pose in enumerate(poses):
        key = liquid.shape_key_add(name=f'Computed physical t={i*.02:.2f}s')
        for point, xyz in zip(key.data, pose):
            point.co = xyz
        for frame, value in ((max(1, i), 0.), (i+1, 1.), (i+2, 0.)):
            key.value = value; key.keyframe_insert('value', frame=frame)
    water = material('Clear water, no invented whitewater', (.82, .95, .99), .06, 1., 1.333)
    absorption = water.node_tree.nodes.new('ShaderNodeVolumeAbsorption'); absorption.inputs['Color'].default_value = (.64, .85, .94, 1.)
    absorption.inputs['Density'].default_value = .12
    water.node_tree.links.new(absorption.outputs['Volume'], water.node_tree.nodes['Material Output'].inputs['Volume'])
    liquid.data.materials.append(water)
    glass = material('Laboratory glass walls', (.94, .98, 1.), .08, 1., 1.45)
    stone = material('Illuminated metric tank bed (authored diagnostic apparatus)', (.45, .5, .55), .85)
    nodes = stone.node_tree.nodes; links = stone.node_tree.links
    checker = nodes.new('ShaderNodeTexChecker'); checker.inputs['Scale'].default_value = 10.
    checker.inputs['Color1'].default_value = (.45, .5, .55, 1.)
    checker.inputs['Color2'].default_value = (.18, .22, .26, 1.)
    coordinates = nodes.new('ShaderNodeTexCoord'); links.new(coordinates.outputs['Generated'], checker.inputs['Vector'])
    bed_node = nodes['Principled BSDF']; links.new(checker.outputs['Color'], bed_node.inputs['Base Color'])
    links.new(checker.outputs['Color'], bed_node.inputs['Emission Color']); bed_node.inputs['Emission Strength'].default_value = .8
    cube('Bed top exactly z=0', (.5, .3, -.02), (1.04, .64, .04), stone)
    for name, center, dims in (('Left wall inside x=0', (-.005, .3, .29), (.01, .62, .58)),
                               ('Right wall inside x=1', (1.005, .3, .29), (.01, .62, .58)),
                               ('Front wall inside y=0', (.5, -.005, .29), (1., .01, .58)),
                               ('Back wall inside y=.6', (.5, .605, .29), (1., .01, .58))):
        cube(name, center, dims, glass)
    tracer = material('Orange diagnostic material-node marker, NOT foam', (.9, .18, .035), .35)
    marker_objects = []
    for index in range(markers.shape[1]):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=.004, location=markers[0, index])
        obj = bpy.context.object; obj.name = f'Material node marker {index} (diagnostic only)'; obj.data.materials.append(tracer)
        for i, pose in enumerate(markers):
            obj.location = pose[index]; obj.keyframe_insert('location', frame=i+1)
        marker_objects.append(obj)
    floor = material('Dark studio floor', (.16, .2, .26), .9)
    bpy.ops.mesh.primitive_plane_add(size=200, location=(.5, .3, -.043)); bpy.context.object.data.materials.append(floor)
    bpy.ops.object.camera_add(location=(1.35, -1.2, 2.2)); camera = bpy.context.object; aim(camera, (.5, .3, .28))
    camera.data.type = 'ORTHO'; camera.data.ortho_scale = 1.85; scene.camera = camera
    for pos, power, size in (((-.5, -1.2, 2.), 120., 1.5), ((1.4, 1.2, 1.8), 180., 1.2), ((.7, -.5, .9), 40., .8)):
        bpy.ops.object.light_add(type='AREA', location=pos); lamp = bpy.context.object; lamp.data.energy = power; lamp.data.size = size; aim(lamp, (.5, .3, .3))
    scene.world = bpy.data.worlds.new('Laboratory'); scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.2, .27, .36, 1.)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .7
    scene.render.engine = 'CYCLES'; scene.cycles.samples = 16; scene.cycles.use_denoising = True
    scene.cycles.use_adaptive_sampling = True; scene.cycles.adaptive_threshold = .04; scene.cycles.adaptive_min_samples = 4
    scene.cycles.max_bounces = 20; scene.cycles.transmission_bounces = 16; scene.cycles.transparent_max_bounces = 16
    scene.render.resolution_x = 760; scene.render.resolution_y = 520; scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'AgX'; scene.render.image_settings.file_format = 'PNG'
    scene.render.fps = 50; scene.frame_start = 1; scene.frame_end = 21; scene.frame_set(1)
    args.output.mkdir(); blend = args.output/'moving-tank.blend'; bpy.ops.wm.save_as_mainfile(filepath=str(blend.resolve()))
    started = time.perf_counter(); frames = []; errors = []
    for i in range(args.frames):
        scene.frame_set(i+1); evaluated = liquid.evaluated_get(bpy.context.evaluated_depsgraph_get()); actual = evaluated.to_mesh()
        try:
            xyz = np.array([p.co[:] for p in actual.vertices]); error = float(np.max(np.abs(xyz-poses[i])))
        finally:
            evaluated.to_mesh_clear()
        if error > 2e-7:
            raise ValueError('Actual engine geometry differs from physical curved-boundary samples')
        for index, obj in enumerate(marker_objects):
            if np.max(np.abs(np.array(obj.location)-markers[i, index])) > 2e-7:
                raise ValueError('Engine marker not at computed material node')
        errors.append(error); path = args.output/f'frame-{i:03d}.png'; scene.render.filepath = str(path.resolve())
        bpy.ops.render.render(write_still=True); frames.append(str(path.resolve())); print('MOVING_TANK_ENGINE_VIEW', i, error, flush=True)
    if any(digest(p) != sha for p, sha in pins.items()):
        raise ValueError('Rendering modified physical liquid')
    result = dict(complete=True, accepted=False, frames=frames, playback=str(blend.resolve()),
        dependency_sha256=pins, outputs_sha256={p: digest(p) for p in [*frames, str(blend.resolve())]},
        maximum_float32_pose_error_m=max(errors), total_render_seconds=time.perf_counter()-started,
        preview_only=args.frames != 21, scope='Actual 3D curved moving-tank samples; diagnostic orange material-node markers, NOT foam. Preliminary sloshing calibration, not through-flow standing-wave or feature acceptance.')
    with (args.output/'report.json').open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')


if __name__ == '__main__':
    main()
