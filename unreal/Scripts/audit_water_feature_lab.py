"""Inspect cached FLIP particle motion without rendering or modifying the bake.

This is a kinematic diagnostic, not mass balance or calibrated CFD validation.
"""
import argparse
import json
from pathlib import Path
import sys

import bpy
import numpy as np


def region(points, velocity, lo, hi, scale=None):
    keep = np.all((points >= lo) & (points < hi), axis=1)
    sample = velocity[keep]
    result = dict(bounds_m=[lo, hi], particles=int(keep.sum()))
    if len(sample):
        result.update(mean_velocity_raw=sample.mean(axis=0).tolist(),
                      median_velocity_raw=np.median(sample, axis=0).tolist(),
                      negative_x_fraction=float(np.mean(sample[:, 0] < 0.)),
                      speed_p95_raw=float(np.percentile(np.linalg.norm(sample, axis=1), 95)))
        if scale is not None:
            result.update(mean_velocity_mps_estimate=(sample.mean(axis=0)*scale).tolist(),
                          median_velocity_mps_estimate=(np.median(sample, axis=0)*scale).tolist())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frames', type=int, nargs='+', default=[96, 120, 144, 168])
    parser.add_argument('--calibration', type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    root = Path(bpy.data.filepath).parent
    setup = json.loads((root/'setup.json').read_text())
    scale = None
    if args.calibration:
        calibration = json.loads(args.calibration.read_text())
        if not calibration['passed'] or any([
            calibration['blender'] != bpy.app.version_string,
            calibration['resolution'] != setup['resolution'],
            calibration['fps'] != setup['fps'],
            calibration['domain_dimensions_m'] != setup['dimensions_m']]):
            raise ValueError('Calibration does not cover this scene configuration')
        scale = calibration['inferred_raw_velocity_to_mps']
    rows = []
    for frame in args.frames:
        bpy.context.scene.frame_set(frame)
        domain = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        ps = next(p for p in domain.particle_systems if p.name == 'Liquid')
        count = len(ps.particles)
        if not count:
            raise RuntimeError('No primary particle cache')
        positions = np.empty(count*3, dtype=np.float32)
        velocities = np.empty_like(positions)
        ps.particles.foreach_get('location', positions)
        ps.particles.foreach_get('velocity', velocities)
        positions, velocities = positions.reshape(-1, 3), velocities.reshape(-1, 3)
        if not np.isfinite(positions).all() or not np.isfinite(velocities).all():
            raise ValueError('Nonfinite particle data')
        shelf = setup['ledge_height_m']
        tail = setup['nominal_tailwater_m']
        rows.append(dict(frame=frame, particle_count=count,
            position_bounds_m=[positions.min(axis=0).tolist(), positions.max(axis=0).tolist()],
            source=region(positions, velocities, [.8, -.5, shelf+.05], [1.5, .5, shelf+.3], scale),
            falling_sheet=region(positions, velocities, [1.8, -.5, .65], [2.7, .5, 1.05], scale),
            surface_return=region(positions, velocities, [1.9, -.5, tail-.15], [3.3, .5, tail+.2], scale),
            submerged_outflow=region(positions, velocities, [1.9, -.5, .08], [3.3, .5, tail-.2], scale)))
    result = dict(case=setup['case'], source_blend=bpy.data.filepath, frames=rows,
                  velocity_units=('Raw Blender API values plus estimates scaled by the matched free-fall calibration'
                                  if scale is not None else 'Blender particle API raw; NOT verified meters per second'),
                  calibrated_scale=scale,
                  calibration_file=None if args.calibration is None else str(args.calibration.resolve()),
                  supersedes='kinematics.json: that first diagnostic incorrectly labeled raw API velocities m/s',
                  physical_accuracy_accepted=False,
                  caveat='Without calibration only directions are meaningful. Fixed surface bands may miss the evolving roller. FLIP particles are narrow-band and do not uniformly sample interior water. Not volumetric flux or mass conservation.')
    args.output.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
