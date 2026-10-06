"""Export a small exact-bed hydraulic snapshot for offline 3D liquid review.

This is a straightened local patch, not surveyed terrain or a replacement for
the live solver. Boundary confinement and startup must be reviewed separately.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_troublemaker_hydraulic_spinup import validated_frame_state
from raftsim.scenario2_5d import read_scenario2_5d_package


def export(scenario_path, frame, output, bounds):
    if output.exists():
        raise ValueError('Refusing to overwrite review input')
    x0, x1, y0, y1 = bounds
    if not all(np.isfinite(bounds)) or not 3 <= x1-x0 <= 20 or not 3 <= y1-y0 <= 20:
        raise ValueError('Review patch must be 3–20 m on each horizontal axis')
    scenario = read_scenario2_5d_package(scenario_path)
    state = validated_frame_state(scenario, np.genfromtxt(frame, delimiter=',', names=True))
    grid = scenario.grid
    xs = grid.origin_x + np.arange(grid.nx)*grid.dx
    ys = grid.origin_y + np.arange(grid.ny)*grid.dy
    cols = np.flatnonzero((xs >= x0) & (xs <= x1))
    rows = np.flatnonzero((ys >= y0) & (ys <= y1))
    if len(cols) < 4 or len(rows) < 4 or x0 < xs[0] or x1 > xs[-1] or y0 < ys[0] or y1 > ys[-1]:
        raise ValueError('Patch outside source or insufficient grid samples')
    selection = np.ix_(rows, cols)
    bed = scenario.bed[selection]
    depth = state.depth[selection]
    eta = state.eta[selection]
    u, v = state.u[selection], state.v[selection]
    if not np.all(depth[:, 0] > .1) or np.any(u[:, 0] <= 0):
        raise ValueError('Choose an entirely wet, downstream-flowing inlet strip')
    if not np.all(depth > .025):
        raise ValueError('The diagnostic fill requires a fully wet patch deeper than 0.025 m')
    z0 = float(bed.min())
    result = dict(schema='raftsim.local_liquid_review.v1', production_promoted=False,
        photorealism_accepted=False, units='metres, seconds, m/s',
        source_scenario=str(scenario_path.resolve()), source_frame=str(frame.resolve()),
        source_frame_sha256=hashlib.sha256(frame.read_bytes()).hexdigest(),
        source_origin_station_lateral_datum=[float(xs[cols[0]]), float(ys[rows[0]]), z0],
        interpretation='Local station/lateral axes straightened; closed side walls; no surveyed or gameplay authority.',
        dx=grid.dx, dy=grid.dy, nx=len(cols), ny=len(rows),
        bed=(bed-z0).tolist(), eta=(eta-z0).tolist(), u=u.tolist(), v=v.tolist(),
        inlet_section_flux_m3s=float(np.sum(.5*(depth[:-1, 0]*u[:-1, 0]+depth[1:, 0]*u[1:, 0]))*grid.dy))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        json.dump(result, stream, indent=2)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', type=Path, required=True)
    parser.add_argument('--frame', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--bounds', type=float, nargs=4, required=True)
    args = parser.parse_args()
    result = export(args.scenario, args.frame, args.output, args.bounds)
    print(json.dumps({k:v for k,v in result.items() if k not in ('bed','eta','u','v')}, indent=2))
