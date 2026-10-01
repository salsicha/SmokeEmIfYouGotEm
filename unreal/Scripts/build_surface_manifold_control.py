"""Native short curvature control of new surface dynamics, not liquid/foam CFD.

Two imposed spheres and new markers compare tangent-speed preservation with
projection-only damping. No original eddy particle is used or modified.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_surface_manifold import SurfaceState, initialize, step, tangent
from build_water_feature_lab import material, aim, box

RADIUS, SPEED, FPS, STEPS = .03, .09, 24, 48


def surface(points, seconds):
    length = np.linalg.norm(points, axis=1)
    return length-RADIUS, points/length[:, None]


def solve(steps, rotate):
    angles = np.array([-.5, -.2, .1, .4])
    positions = RADIUS*np.column_stack([np.sin(angles), np.zeros(4), np.cos(angles)])
    velocities = SPEED*np.column_stack([np.cos(angles), np.zeros(4), -np.sin(angles)])
    state = initialize(positions, velocities, surface)
    rows = [dict(seconds=0., positions=state.positions.tolist(), speed=state.tangent_speed.tolist())]
    residual, correction = 0., 0.
    for index in range(steps):
        if not rotate:
            normal = state.positions/np.linalg.norm(state.positions, axis=1)[:, None]
            velocity = tangent(state.velocities, normal)
            predictor = state.positions+(2/steps)*velocity
            position = RADIUS*predictor/np.linalg.norm(predictor, axis=1)[:, None]
            velocity = tangent(velocity, position/RADIUS)
            state = SurfaceState(position, velocity, np.linalg.norm(velocity, axis=1))
            report = dict(maximum_residual_m=float(np.abs(surface(position, 0.)[0]).max()),
                          maximum_correction_m=float(np.linalg.norm(position-predictor, axis=1).max()))
        else:
            state, report = step(state, surface, 2*index/steps, 2/steps)
        residual = max(residual, report['maximum_residual_m'])
        correction = max(correction, report['maximum_correction_m'])
        rows.append(dict(seconds=2*(index+1)/steps, positions=state.positions.tolist(),
                         speed=state.tangent_speed.tolist()))
    exact = RADIUS*np.column_stack([np.sin(angles+2*SPEED/RADIUS), np.zeros(4),
                                    np.cos(angles+2*SPEED/RADIUS)])
    return rows, dict(maximum_constraint_error_m=residual, maximum_step_correction_m=correction,
        maximum_final_geodesic_error_m=float(np.linalg.norm(state.positions-exact, axis=1).max()),
        final_speed_ratio=(state.tangent_speed/SPEED).tolist(), steps=steps, accepted=False)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists() or shutil.disk_usage(args.output.parent).free < 1024**3:
        raise ValueError('Fresh output and one GiB reserve required')
    rows, corrected = solve(STEPS, True)
    naive, projection = solve(STEPS, False)
    refinement = [solve(n, True)[1] for n in (STEPS, STEPS*2, STEPS*4)]
    errors = [r['maximum_final_geodesic_error_m'] for r in refinement]
    assert errors[1] < errors[0]/3.8 and errors[2] < errors[1]/3.8
    assert max(abs(s-1) for s in corrected['final_speed_ratio']) < 1e-12
    assert corrected['maximum_constraint_error_m'] < 1e-10
    assert max(projection['final_speed_ratio']) < .8
    args.output.mkdir(parents=True, exist_ok=False)
    audit = dict(complete=True, accepted=False, corrected=corrected, projection_only=projection,
        projection_control='Free-flight tangent predictor, radial closest-point position projection, then velocity projected to the new tangent plane. Distinct from the old-normal constraint solve; not a Mantaflow replay.',
        refinement=refinement, scope='Exact imposed sphere/geodesic numerical control. Not wet-foam forces, surface tension, gas volume, liquid coupling or a physical spherical liquid equilibrium.')
    (args.output/'dynamics.json').write_text(json.dumps(audit, indent=2))
    (args.output/'trajectories.json').write_text(json.dumps(dict(corrected=rows, projection_only=naive), indent=2))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.render.fps, scene.frame_end = FPS, STEPS+1
    sphere_mat = material('Imposed constraint surface - not simulated water', (.08, .19, .28), .3)
    marker_mat = material('New numerical surface markers', (.94, .98, 1.), .3)
    amber_mat = material('Projection-only control markers', (1., .25, .04), .3)
    expected = {}
    for label, center, sequence, marker in [('Corrected', (-.044, 0., .031), rows, marker_mat),
                                           ('Projection only', (.044, 0., .031), naive, amber_mat)]:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=RADIUS, location=center)
        obj = bpy.context.object
        obj.name = label+' imposed sphere'
        obj.data.materials.append(sphere_mat)
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
        for index in range(4):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=.0012)
            obj = bpy.context.object
            obj.name = f'{label} marker {index}'
            obj.data.materials.append(marker)
            expected[obj.name] = [np.array(row['positions'][index])+center for row in sequence]
            for frame, position in enumerate(expected[obj.name], 1):
                obj.location = position
                obj.keyframe_insert('location', frame=frame)
            for layer in obj.animation_data.action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for curve in bag.fcurves:
                            for key in curve.keyframe_points:
                                key.interpolation = 'LINEAR'
    floor = box('Stationary reference floor', (-.2, -.15, -.006), (.2, .15, -.001))
    floor.data.materials.append(material('Neutral reference', (.09, .11, .14), .8))
    scene.world = bpy.data.worlds.new('Declared studio - not measured site lighting')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.6, .7, .85, 1.)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .3
    bpy.ops.object.light_add(type='AREA', location=(-.05, -.08, .16))
    bpy.context.object.data.energy, bpy.context.object.data.size = 2., .13
    aim(bpy.context.object, (0., 0., .03))
    bpy.ops.object.camera_add(location=(0., -.24, .15))
    scene.camera = bpy.context.object
    aim(scene.camera, (0., 0., .035))
    scene.camera.data.type, scene.camera.data.ortho_scale = 'ORTHO', .175
    scene.camera.data.clip_start = .0001
    def caption(body, x, y, size):
        bpy.ops.object.text_add()
        obj = bpy.context.object
        obj.data.body, obj.data.size = body, size
        obj.rotation_euler = scene.camera.rotation_euler
        obj.location = scene.camera.matrix_world @ Vector((x, y, -.12))
        mat = bpy.data.materials.get('Caption') or bpy.data.materials.new('Caption')
        mat.use_nodes = True
        shader = mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = (.95, .97, 1., 1.)
        shader.inputs['Emission Color'].default_value = (.95, .97, 1., 1.)
        shader.inputs['Emission Strength'].default_value = 1.
        obj.data.materials.append(mat)
    bpy.context.view_layer.update()
    caption('SURFACE DYNAMICS CONTROL | 2s\nImposed geometry; NOT physical foam or liquid', -.08, .038, .003)
    caption('Constraint + rotation\nTangent speed retained', -.077, -.041, .003)
    caption('Closest point + velocity projection\nTangent speed decays', .008, -.041, .0027)
    worst, half_residual = 0., 0.
    for frame in np.arange(1., STEPS+1.5, .5):
        whole, fraction = int(frame), frame-int(frame)
        scene.frame_set(whole, subframe=fraction)
        for name, sequence in expected.items():
            first = sequence[whole-1]
            predicted = first if not fraction else (first+sequence[whole])/2
            position = np.array(bpy.data.objects[name].matrix_world.translation)
            worst = max(worst, float(np.linalg.norm(position-predicted)))
            center = np.array([-.044 if name.startswith('Corrected') else .044, 0., .031])
            half_residual = max(half_residual, abs(np.linalg.norm(position-center)-RADIUS))
    assert worst < 1e-8
    # Half-frame chord interpolation is NOT exactly on the curved manifold.
    audit.update(native_positions_checked=97, maximum_native_position_error_m=worst,
                 maximum_native_half_frame_constraint_error_m=half_residual)
    scene.frame_set(1)
    scene.render.engine = 'CYCLES'
    scene.cycles.samples, scene.cycles.use_denoising = 48, True
    scene.render.resolution_x, scene.render.resolution_y = 800, 450
    scene.render.image_settings.file_format = 'PNG'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    if not any(device.type == 'OPTIX' for device in prefs.devices):
        raise RuntimeError('OptiX unavailable')
    for device in prefs.devices:
        device.use = device.type == 'OPTIX'
    scene.cycles.device = 'GPU'
    blend = (args.output/'feature.blend').resolve()
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    audit['source_blend_sha256'] = sha(blend)
    (args.output/'dynamics.json').write_text(json.dumps(audit, indent=2))
    frames = []
    report = dict(complete=False, simulation_fps=FPS, frames=frames, source_blend=str(blend),
        source_blend_sha256=sha(blend), secondary_particles_hidden=False,
        model='Fresh numerical surface constraint with tangent-speed preservation, compared at equal dt',
        limitations='Imposed spherical manifold and nonphysical markers, not foam appearance or fluid dynamics. No SPH, gas pressure, entrainment, film drainage, bursting or two-way liquid coupling. Half-frame linear interpolation is off the sphere and measured separately. Playback FPS is not game performance.',
        diagnostics_only=True, physical_accuracy_accepted=False, visual_accuracy_accepted=False)
    for frame in range(1, STEPS, 2):
        if shutil.disk_usage(args.output).free < 1024**3:
            raise RuntimeError('Disk reserve reached; preserve partial render')
        scene.frame_set(frame)
        image = (args.output/f'frame-{frame:04d}.png').resolve()
        scene.render.filepath = str(image)
        start = time.monotonic()
        bpy.ops.render.render(write_still=True)
        frames.append(dict(frame=frame, image=str(image), sha256=sha(image),
                           render_seconds=time.monotonic()-start))
        report['complete'] = len(frames) == STEPS//2
        (args.output/'frames.json').write_text(json.dumps(report, indent=2))
        print('MANIFOLD_FRAME', json.dumps(frames[-1]), flush=True)
    print('SURFACE_CONTROL_AUDIT', json.dumps(audit), flush=True)


if __name__ == '__main__':
    main()
