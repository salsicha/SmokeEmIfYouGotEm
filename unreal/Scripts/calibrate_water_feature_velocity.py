"""Small no-contact free-fall check for the installed Blender particle API.

Calibrates readback velocity units against displacement; not feature validation.
"""
import argparse
import json
from pathlib import Path
import sys

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_water_feature_lab import box


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--resolution', type=int, default=80)
    parser.add_argument('--domain-xy', type=float, nargs=2, default=[6., 1.6],
                        help='Match horizontal domain dimensions; vertical bounds stay -0.1..2.8 m')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if not 48 <= args.resolution <= 160:
        parser.error('Resolution must match a supported laboratory case (48..160)')
    if not all(np.isfinite(args.domain_xy)) or not (2 <= args.domain_xy[0] <= 6 and 1 <= args.domain_xy[1] <= 6):
        parser.error('Domain x must be 2..6 m and y 1..6 m')
    args.output.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.gravity = (0., 0., -9.80665)
    scene.render.fps = 24
    scene.frame_end = 12
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=.3,
                                       location=(args.domain_xy[0]/2, 0., 2.2))
    source = bpy.context.object
    mod = source.modifiers.new('Initially stationary liquid', 'FLUID')
    mod.fluid_type = 'FLOW'
    mod.flow_settings.flow_type = 'LIQUID'
    mod.flow_settings.flow_behavior = 'GEOMETRY'
    domain = box('Calibration domain', (0., -args.domain_xy[1]/2, -.1),
                 (args.domain_xy[0], args.domain_xy[1]/2, 2.8))
    mod = domain.modifiers.new('FLIP calibration', 'FLUID')
    mod.fluid_type = 'DOMAIN'
    settings = mod.domain_settings
    settings.domain_type = 'LIQUID'
    settings.resolution_max = args.resolution
    settings.flip_ratio = .95
    settings.cache_type = 'ALL'
    settings.cache_frame_start = 1
    settings.cache_frame_end = 12
    settings.cache_directory = str((args.output/'cache').resolve())
    settings.cache_resumable = True
    settings.timesteps_min = 2
    settings.timesteps_max = 8
    settings.cfl_condition = 2.
    settings.use_collision_border_top = False
    bpy.context.view_layer.objects.active = domain
    bpy.ops.wm.save_as_mainfile(filepath=str((args.output/'calibration.blend').resolve()))
    result = bpy.ops.fluid.bake_all()
    if 'FINISHED' not in result or not settings.has_cache_baked_data:
        raise RuntimeError('Incomplete calibration bake')
    rows = []
    for frame in range(1, 13):
        scene.frame_set(frame)
        obj = domain.evaluated_get(bpy.context.evaluated_depsgraph_get())
        ps = obj.particle_systems[0]
        count = len(ps.particles)
        pos, vel = np.empty(count*3, np.float32), np.empty(count*3, np.float32)
        ps.particles.foreach_get('location', pos)
        ps.particles.foreach_get('velocity', vel)
        pos, vel = pos.reshape(-1, 3), vel.reshape(-1, 3)
        if not count or pos[:, 2].min() < .3:
            raise RuntimeError('Missing particles or contact invalidated free fall')
        state = obj.modifiers[0].domain_settings
        nx, ny, nz = state.domain_resolution
        grid = np.array(state.velocity_grid[:]).reshape(nz, ny, nx, 3)
        origin = np.array(obj.matrix_world @ state.start_point)
        centroid = pos.mean(axis=0)
        ijk = np.floor((centroid-origin)/np.array(state.cell_size)).astype(int)
        i, j, k = ijk
        center_velocity = grid[k, j, i]/state.resolution_max
        rows.append(dict(frame=frame, seconds=(frame-1)/24,
                         centroid_m=pos.mean(axis=0).tolist(),
                         mean_velocity_raw=vel.mean(axis=0).tolist(),
                         interior_grid_velocity_div_resolution=center_velocity.tolist(), count=count))
    t = np.array([row['seconds'] for row in rows])
    z = np.array([row['centroid_m'][2] for row in rows])
    v = np.array([row['mean_velocity_raw'][2] for row in rows])
    fit = np.polyfit(t, z, 2)
    acceleration = float(2*fit[0])
    raw_slope = float(np.polyfit(t, v, 1)[0])
    scale = acceleration/raw_slope
    max_residual = float(np.max(np.abs(np.polyval(fit, t)-z)))
    grid_v = np.array([row['interior_grid_velocity_div_resolution'][2] for row in rows])
    grid_relative_error = float(np.max(np.abs(grid_v-v))/max(np.max(np.abs(v)), 1e-9))
    report = dict(blender=bpy.app.version_string, domain_dimensions_m=[*args.domain_xy, 2.9],
        resolution=args.resolution, fps=24, requested_gravity_mps2=-9.80665,
        fitted_centroid_acceleration_mps2=acceleration,
        raw_velocity_slope_per_second=raw_slope,
        inferred_raw_velocity_to_mps=scale,
        maximum_quadratic_position_residual_m=max_residual,
        gravity_relative_error=abs(acceleration+9.80665)/9.80665,
        grid_to_particle_peak_relative_error=grid_relative_error,
        passed=abs(acceleration+9.80665)/9.80665 < .05 and max_residual < .01 and grid_relative_error < .05,
        scope='Only this Blender build, domain size, time scale and resolution. Not hydraulic feature acceptance.',
        frames=rows)
    (args.output/'calibration.json').write_text(json.dumps(report, indent=2))
    print('VELOCITY_CALIBRATION', json.dumps({k:v for k,v in report.items() if k != 'frames'}))


if __name__ == '__main__':
    main()
