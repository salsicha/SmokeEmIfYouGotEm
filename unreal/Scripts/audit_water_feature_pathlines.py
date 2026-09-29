"""Integrate diagnostic tracers through cached primary-particle velocity samples.

These are reconstructed pathlines, NOT identities tracked across FLIP particle
reseeding. Never modifies the bake or projects a path back into the liquid.
"""
import argparse
import json
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils.kdtree import KDTree


class SampleField:
    def __init__(self, obj, scale, support):
        ps = next(p for p in obj.particle_systems if p.name == 'Liquid')
        count = len(ps.particles)
        if not count:
            raise ValueError('Missing primary particle cache')
        pos = np.empty(count*3, np.float32)
        vel = np.empty(count*3, np.float32)
        ps.particles.foreach_get('location', pos)
        ps.particles.foreach_get('velocity', vel)
        self.vel = vel.reshape(-1, 3)*scale
        if not np.isfinite(pos).all() or not np.isfinite(self.vel).all():
            raise ValueError('Nonfinite particle field')
        self.tree = KDTree(count)
        for i, p in enumerate(pos.reshape(-1, 3)):
            self.tree.insert(p, i)
        self.tree.balance()
        self.support = support

    def sample(self, p):
        neighbors = self.tree.find_n(p, 12)
        near = [(i, d) for _, i, d in neighbors if d <= self.support]
        if len(near) < 4:
            return None
        weights = np.array([1/max(d, .001)**2 for _, d in near])
        return np.average(self.vel[[i for i, _ in near]], axis=0, weights=weights)


def interpolate(a, b, p, t):
    va, vb = a.sample(p), b.sample(p)
    if va is None or vb is None:
        return None
    return (1-t)*va+t*vb


def outside(p, bounds):
    if not (0 < p[0] < 5.5 and -.8 < p[1] < .8 and 0 < p[2] < 2.8):
        return 'left wetted-domain/bed/drain bounds'
    if np.all(p >= bounds[0]) and np.all(p <= bounds[1]):
        return 'entered authored solid'
    return None


def advance(track, a, b, frame, fps, substeps, bounds):
    if track['stopped']:
        return
    p = np.array(track['positions_m'][-1], dtype=float)
    dt = 1/(fps*substeps)
    for j in range(substeps):
        v = interpolate(a, b, p, j/substeps)
        if v is None:
            track['stopped'] = 'insufficient local liquid-particle support'
            break
        midpoint = p+.5*dt*v
        reason = outside(midpoint, bounds)
        vm = None if reason else interpolate(a, b, midpoint, (j+.5)/substeps)
        if vm is None:
            track['stopped'] = reason or 'insufficient midpoint liquid-particle support'
            break
        candidate = p+dt*vm
        reason = outside(candidate, bounds)
        if reason:
            track['stopped'] = reason
            break
        p = candidate
    if track['stopped']:
        track['stop_frame'] = frame+(j/substeps)
    else:
        track['positions_m'].append(p.tolist())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--calibration', type=Path, required=True)
    parser.add_argument('--start', type=int, default=168)
    parser.add_argument('--end', type=int, default=288)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    setup = json.loads((Path(bpy.data.filepath).parent/'setup.json').read_text())
    cal = json.loads(args.calibration.read_text())
    if setup['case'] != 'eddy' or not 1 <= args.start < args.end <= setup['frames']:
        raise ValueError('Requires eddy case and cached frame interval')
    if not cal['passed'] or any(cal[k] != setup[k] for k in ('resolution', 'fps')) or cal['domain_dimensions_m'] != setup['dimensions_m'] or cal['blender'] != bpy.app.version_string:
        raise ValueError('Mismatched velocity calibration')
    seeds = [[float(x), float(y), z] for x in np.linspace(3.2, 4.6, 6)
             for y in np.linspace(.05, .65, 4) for z in (.15, .25)]
    # Repeat every seed with halved integration step, not a selected good path.
    tracks = [[dict(seed_m=p, positions_m=[p], stopped=None) for p in seeds]
              for _ in (4, 8)]
    bounds = np.array(setup['obstacle_bounds_m'])
    support = 2*setup['approximate_cell_m']

    def field(frame):
        bpy.context.scene.frame_set(frame)
        obj = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        return SampleField(obj, cal['inferred_raw_velocity_to_mps'], support)

    a = field(args.start)
    for frame in range(args.start, args.end):
        b = field(frame+1)
        for substeps, group in zip((4, 8), tracks):
            for track in group:
                advance(track, a, b, frame, setup['fps'], substeps, bounds)
        a = b
        if frame % 24 == 0:
            print('PATHLINE_FRAME', frame+1, 'active', [sum(t['stopped'] is None for t in g) for g in tracks], flush=True)
    comparisons = []
    for coarse, fine in zip(*tracks):
        n = min(len(coarse['positions_m']), len(fine['positions_m']))
        error = np.linalg.norm(np.array(coarse['positions_m'][:n])-np.array(fine['positions_m'][:n]), axis=1)
        comparisons.append(dict(seed_m=coarse['seed_m'], common_frames=n,
                                maximum_step_halving_difference_m=float(error.max())))
    report = dict(source_blend=bpy.data.filepath, start_frame=args.start,
        end_frame=args.end, fps=setup['fps'], neighbor_count=12,
        minimum_supported_neighbors=4, support_radius_m=support,
        substeps=[4, 8], tracks=tracks, step_halving=comparisons,
        accepted=False, limitations='Diagnostic tracers through spatially smoothed primary-particle velocities, linearly interpolated in time. Not tracked FLIP particle identities or exact solver trajectories; not validated surface-foam paths. Stops on insufficient narrow-band support or solid/domain bounds; never clamps or projects. No automatic closed-circulation acceptance.')
    args.output.write_text(json.dumps(report, indent=2))
    print('PATHLINE_RESULT', str(args.output), [sum(t['stopped'] is None for t in g) for g in tracks], flush=True)


if __name__ == '__main__':
    main()
