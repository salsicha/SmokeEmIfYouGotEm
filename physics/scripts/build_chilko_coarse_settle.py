"""Build a coarse single-grid pre-cook of a Chilko construction scenario.

The full Chilko corridor (25,552 x 257 cells at 2 m) advances about 0.01
simulated seconds per wall second, so settling it from its 1D conveyance
start would take days. This writes the same reach on a grid `factor` times
coarser in both directions, for settling only:
- bed: block mean over the real fine cells (the lateral padding needed to
  make the row count divisible is not given invented ground);
- initial state: block-mean depth (volume preserving) and depth-weighted
  velocity (momentum preserving);
- inflow ghost cells: the same block averages, so the inflow discharge is
  unchanged;
- outflow stage, banks, roughness (g n^2) and solver settings unchanged;
- timestep scaled by the factor (the native solver keeps its CFL limit).

The result is only a settling aid. warm_start_chilko_from_coarse.py carries
its surface and current back to the full-resolution inputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def blocks(fine, factor, weights=None):
    """Block sums over real cells; rows are padded with zero weight."""
    ny, nx = fine.shape
    pad = (-ny) % factor
    if nx % factor:
        raise ValueError('Station count must divide by the factor')
    w = np.ones_like(fine) if weights is None else weights
    f = np.pad(fine * w, ((0, pad), (0, 0)))
    w = np.pad(w, ((0, pad), (0, 0)))
    shape = (f.shape[0] // factor, factor, nx // factor, factor)
    return f.reshape(shape).sum(axis=(1, 3)), w.reshape(shape).sum(axis=(1, 3))


def coarse_ghosts(ghosts, ny, factor):
    """Ghost cells are [bed, h, u, v], one layer of ny rows after another."""
    g = np.asarray(ghosts, float)
    layers = g.shape[0] // ny
    if g.shape != (layers * ny, 4):
        raise ValueError('Unexpected ghost-cell layout')
    out = []
    pad = (-ny) % factor
    for layer in g.reshape(layers, ny, 4):
        b, h, u, v = (np.pad(layer[:, k], (0, pad)) for k in range(4))
        real = np.pad(np.ones(ny), (0, pad))
        rows = lambda a: a.reshape(-1, factor).sum(axis=1)
        n, hs = rows(real), rows(h)
        hb = rows(b * real) / n
        hc = hs / n
        uc = np.where(hs > 0, rows(h * u) / np.where(hs > 0, hs, 1), 0.0)
        vc = np.where(hs > 0, rows(h * v) / np.where(hs > 0, hs, 1), 0.0)
        out.extend(np.c_[hb, hc, uc, vc].tolist())
    return out


def build(inputs, factor, out):
    inputs, out = Path(inputs).resolve(), Path(out).resolve()
    if out.exists():
        raise ValueError('Fresh coarse scenario directory required')
    source = inputs / 'scenario'
    scenario = json.loads((source / 'scenario.json').read_text())
    grid = scenario['grid']
    if grid['dx'] != grid['dy']:
        raise ValueError('Square cells required')
    bed = np.load(source / 'bed.npy')
    with np.load(source / 'initial_state.npz') as state:
        h, u, v = (np.asarray(state[k], float) for k in ('depth', 'u', 'v'))
    ny, nx = bed.shape
    bed_sum, count = blocks(bed, factor)
    bed_c = bed_sum / count
    h_sum, _ = blocks(h, factor)
    h_c = h_sum / count
    hu, _ = blocks(h * u, factor)
    hv, _ = blocks(h * v, factor)
    u_c = np.where(h_sum > 0, hu / np.where(h_sum > 0, h_sum, 1), 0.0)
    v_c = np.where(h_sum > 0, hv / np.where(h_sum > 0, h_sum, 1), 0.0)
    wet = h_c > 1e-6
    h_c = np.where(wet, h_c, 0.0)
    u_c, v_c = np.where(wet, u_c, 0.0), np.where(wet, v_c, 0.0)
    target = out / 'scenario'
    target.mkdir(parents=True)
    np.save(target / 'bed.npy', bed_c)
    np.savez_compressed(target / 'initial_state.npz', depth=h_c, eta=bed_c + h_c, u=u_c, v=v_c,
                        hu=h_c * u_c, hv=h_c * v_c, wet=wet)
    for name in ('features.json', 'probes.json'):
        shutil.copyfile(source / name, target / name)
    coarse = json.loads(json.dumps(scenario))
    half = (factor - 1) * 0.5 * grid['dx']
    coarse['grid'] = dict(nx=nx // factor, ny=bed_c.shape[0], dx=grid['dx'] * factor, dy=grid['dy'] * factor,
                          origin_x=grid['origin_x'] + half, origin_y=grid['origin_y'] + half)
    coarse['fixed_dt'] = scenario['fixed_dt'] * factor
    for boundary in coarse['boundaries']:
        if boundary['kind'] == 'discharge_profile':
            if boundary['edge'] not in ('west', 'east'):
                raise ValueError('Only end inflows are supported')
            boundary['ghost_cells'] = coarse_ghosts(boundary['ghost_cells'], ny, factor)
        elif boundary['kind'] not in ('outflow', 'bank', 'wall'):
            raise ValueError('Unsupported boundary for a coarse pre-cook')
    coarse['metadata']['scenario_id'] = scenario['metadata']['scenario_id'] + '_coarse_k%d' % factor
    coarse['metadata']['description'] = 'Coarse settling pre-cook only; not a runtime or review input'
    coarse['metadata']['coarse_settle'] = dict(
        factor=factor, source_inputs=str(inputs), source_scenario_sha256=sha(source / 'scenario.json'),
        source_bed_sha256=sha(source / 'bed.npy'), source_initial_state_sha256=sha(source / 'initial_state.npz'),
        fine_shape=[ny, nx], padded_rows=(-ny) % factor,
        fine_volume_m3=float(h.sum() * grid['dx'] * grid['dy']),
        coarse_volume_m3=float(h_c.sum() * grid['dx'] * grid['dy'] * factor ** 2))
    (target / 'scenario.json').write_text(json.dumps(coarse, indent=2, allow_nan=False) + '\n')
    print(json.dumps(coarse['metadata']['coarse_settle'], indent=2))
    return coarse


def restart(coarse, out, run_seconds, frame=None, splice_from_m=None, splice_state=None, inlet_scale=1.0):
    """Continue a coarse pre-cook from a saved native frame (default: its last).

    The scenario, bed and boundaries are copied unchanged; only the initial
    state is the frame's exact depth and velocity. The coarse_settle record
    gains the frame it restarted from, so a warm start can trace its history.

    With splice_from_m, columns from that station downstream instead take
    splice_state (an initial_state.npz on the same coarse grid). This is only
    an initial guess for settling: a settled upstream reach can rejoin a
    downstream start without waiting for one slow refill front.

    inlet_scale multiplies the inflow ghost velocities relative to the
    ORIGINAL coarse boundary (depths unchanged), to fill a deficit faster.
    A settle must end with a stage at 1.0, the original boundary.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from native_frame_io import load_frame, native_frame_paths
    coarse, out = Path(coarse).resolve(), Path(out).resolve()
    if out.exists():
        raise ValueError('Fresh coarse restart directory required')
    scenario = json.loads((coarse / 'scenario/scenario.json').read_text())
    grid = scenario['grid']
    cook = coarse / 'native' / scenario['metadata']['scenario_id']
    if frame is None:
        native = json.loads((cook / 'manifest.json').read_text())
        frame_path = native_frame_paths(cook, native)[-1]
    else:
        frame_path = Path(frame).resolve()
        frame_path.relative_to(cook / 'frames')
    frame = load_frame(frame_path, (grid['ny'], grid['nx']))
    bed = np.load(coarse / 'scenario/bed.npy')
    if not np.allclose(frame['eta'] - frame['h'], bed, atol=1e-6):
        raise ValueError('Frame does not match the coarse bed')
    h = np.asarray(frame['h'], float)
    wet = h > 1e-6
    h = np.where(wet, h, 0.0)
    u, v = np.where(wet, frame['u'], 0.0), np.where(wet, frame['v'], 0.0)
    splice = None
    if splice_from_m is not None:
        with np.load(splice_state) as other:
            if not np.allclose(other['eta'] - other['depth'], bed, atol=1e-6):
                raise ValueError('Splice state does not match the coarse bed')
            column = int(np.ceil((splice_from_m - grid['origin_x']) / grid['dx']))
            if not 0 < column < grid['nx']:
                raise ValueError('Splice station outside the grid')
            h[:, column:] = other['depth'][:, column:]
            u[:, column:] = other['u'][:, column:]
            v[:, column:] = other['v'][:, column:]
        wet = h > 1e-6
        u, v = np.where(wet, u, 0.0), np.where(wet, v, 0.0)
        splice = dict(from_station_m=float(splice_from_m), column=column, state=str(Path(splice_state).resolve()),
                      state_sha256=sha(splice_state))
    target = out / 'scenario'
    target.mkdir(parents=True)
    for name in ('bed.npy', 'features.json', 'probes.json'):
        shutil.copyfile(coarse / 'scenario' / name, target / name)
    np.savez_compressed(target / 'initial_state.npz', depth=h, eta=bed + h, u=u, v=v, hu=h * u, hv=h * v, wet=wet)
    if not run_seconds > 0:
        raise ValueError('Positive simulated seconds of the continued run required')
    if not inlet_scale > 0:
        raise ValueError('Positive inlet scale required')
    original = scenario['metadata']['coarse_settle'].setdefault('original_boundaries', scenario['boundaries'])
    boundaries = json.loads(json.dumps(original))
    for boundary in boundaries:
        if boundary['kind'] == 'discharge_profile':
            boundary['ghost_cells'] = [[b, h, u * inlet_scale, v * inlet_scale] for b, h, u, v in boundary['ghost_cells']]
    scenario['boundaries'] = boundaries
    elapsed = scenario['metadata']['coarse_settle'].get('elapsed_seconds', 0.0)
    scenario['metadata']['coarse_settle'] = dict(
        scenario['metadata']['coarse_settle'], restarted_from=str(frame_path), restarted_from_sha256=sha(frame_path),
        elapsed_seconds=elapsed + run_seconds, splice=splice, inlet_scale=inlet_scale)
    (target / 'scenario.json').write_text(json.dumps(scenario, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(restarted_from=str(frame_path), elapsed_seconds=scenario['metadata']['coarse_settle']['elapsed_seconds'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, help='Full-resolution inputs folder to coarsen')
    parser.add_argument('--restart', type=Path, help='Coarse pre-cook folder to continue from its last frame')
    parser.add_argument('--run-seconds', type=float, help='With --restart: simulated seconds the continued run covered')
    parser.add_argument('--frame', type=Path, help='With --restart: an explicit saved frame instead of the last')
    parser.add_argument('--splice-from-m', type=float, help='With --restart: station from which --splice-state is used')
    parser.add_argument('--splice-state', type=Path, help='With --restart: initial_state.npz on the same coarse grid')
    parser.add_argument('--inlet-scale', type=float, default=1.0, help='With --restart: inflow multiple of the original boundary')
    parser.add_argument('--factor', type=int, default=4)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if (args.inputs is None) == (args.restart is None):
        parser.error('Give exactly one of --inputs or --restart')
    if args.restart:
        restart(args.restart, args.out, args.run_seconds or 0.0, args.frame, args.splice_from_m, args.splice_state,
                args.inlet_scale)
    else:
        build(args.inputs, args.factor, args.out)
