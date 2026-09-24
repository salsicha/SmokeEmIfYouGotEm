"""Read-only, zero-step numerical tile flux localization of a completed cook.

Uses coupled native ghost exchange, not cell-centred transport. Tile control
volumes are not river cross-sections. Endpoint rates are not interval averages.
No boundary tuning, settling acceptance, or playable promotion is performed.
"""
import argparse
import json
from pathlib import Path
import subprocess

import numpy as np

from audit_cartesian_cook_snapshot import digest


def require(value, message):
    if not value:
        raise ValueError(message)


def face_accounting(grids, fluxes):
    """Cancel shared faces once; retain actual exterior faces and seam residuals."""
    require(len(grids) > 0, 'empty grids')
    g = grids[0]
    dimensions = ('nx', 'ny', 'dx', 'dy')
    require(all(all(a[k] == g[k] for k in dimensions) for a in grids), 'unequal grids')
    require(all(np.isfinite(g[k]) and g[k] > 0 for k in dimensions), 'invalid grid')
    xy = np.array([(a['origin_x'], a['origin_y']) for a in grids], dtype=float)
    require(np.isfinite(xy).all(), 'nonfinite origin')
    lattice = (xy-xy[0]) / [g['nx']*g['dx'], g['ny']*g['dy']]
    require(np.max(np.abs(lattice-np.rint(lattice))) < 1.e-8, 'off-lattice tile')
    keys = list(map(tuple, np.rint(lattice).astype(int)))
    require(len(set(keys)) == len(keys), 'duplicate tile')
    lookup = {key: i for i, key in enumerate(keys)}
    f = np.asarray(fluxes, dtype=float)
    require(f.shape == (len(grids), 4) and np.isfinite(f).all(), 'invalid fluxes')
    exterior, seams = [], []
    offsets = ((-1, 0), (1, 0), (0, -1), (0, 1))
    for i, (x, y) in enumerate(keys):
        for edge, (dx, dy) in enumerate(offsets):
            other = lookup.get((x+dx, y+dy))
            if other is None:
                exterior.append(dict(tile_index=i, edge=('west', 'east', 'south', 'north')[edge],
                                     inward_flux_m3s=float(f[i, edge])))
            elif other > i:
                seams.append(float(f[i, edge]+f[other, edge ^ 1]))
    outer = sum(a['inward_flux_m3s'] for a in exterior)
    residual = sum(seams)
    require(abs(float(f.sum())-outer-residual) < 1.e-8, 'face accounting does not close')
    return dict(exterior_faces=exterior, exterior_net_inflow_m3s=outer,
                shared_face_pairs=len(seams), shared_face_net_residual_m3s=residual,
                maximum_shared_face_mismatch_m3s=max(map(abs, seams), default=0.))


def run(cook, before, after, solver):
    require(after > before >= 0, 'increasing nonnegative steps required')
    original = Path((cook/'input_manifest_path.txt').read_text().strip())
    if not original.is_absolute():
        original = Path(__file__).resolve().parents[2]/original
    require(digest(original) == digest(cook/'input_manifest.json'), 'changed cook manifest')
    manifest = json.loads(original.read_text())
    names = manifest['packages']
    require(len(set(names)) == len(names), 'duplicate package')
    inputs = {a['name']: a for a in manifest['inputs']}
    grids = []
    for name in names:
        require(Path(name).name == name and name not in ('.', '..'), 'unsafe package name')
        for filename, expected in inputs[name]['files'].items():
            require(digest(original.parent/name/filename) == expected, f'changed input: {name}/{filename}')
        grids.append(json.loads((original.parent/name/'scenario.json').read_text())['grid'])
    records, volumes, reports = [], [], []
    for step in (before, after):
        frame = cook/f'frame_{step:06d}'
        record = json.loads((frame/'complete.json').read_text())
        require(record['step'] == step and record['snapshot'], 'incomplete/wrong snapshot')
        hashes = {k: digest(frame/f'{k}.npy') for k in ('h', 'u', 'v')}
        command = [str(solver.resolve()), str(original.resolve()), str(frame.resolve()),
                   *map(str, range(len(names)))]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        report = json.loads(result.stdout)
        require(report['solver_steps_run'] == 0 and report['state_unchanged'], 'not read-only')
        require(report['time_seconds'] == record['time_seconds'], 'time mismatch')
        tiles = report['tiles']
        require([a['tile_index'] for a in tiles] == list(range(len(names))), 'missing/reordered tile')
        accounting = face_accounting(grids, [a['inward_flux_m3s'] for a in tiles])
        require(accounting['maximum_shared_face_mismatch_m3s'] < 1.e-8, 'shared numerical faces disagree')
        exterior = {(a['tile_index'], a['edge']): a['inward_flux_m3s'] for a in accounting['exterior_faces']}
        for probe, expected in zip(manifest['boundary_probes'], record['exterior_fluxes'], strict=True):
            require(abs(exterior[probe['tile_index'], probe['edge']]-expected) < 1.e-8, 'native cook probe mismatch')
        require(all(digest(frame/f'{k}.npy') == value for k, value in hashes.items()), 'snapshot modified')
        volume = np.array([a['volume_m3'] for a in tiles])
        require(abs(float(volume.sum())-record['volume_m3']) < 1.e-6, 'volume mismatch')
        reports.append(dict(step=step, snapshot_sha256=hashes, native=report, accounting=accounting))
        records.append(record)
        volumes.append(volume)
    seconds = records[1]['time_seconds']-records[0]['time_seconds']
    require(np.isfinite(seconds) and seconds > 0, 'invalid elapsed time')
    rates = (volumes[1]-volumes[0])/seconds
    rows = []
    for i, name in enumerate(names):
        endpoint = [sum(r['native']['tiles'][i]['inward_flux_m3s']) for r in reports]
        rows.append(dict(tile_index=i, package=name, grid=grids[i],
                         storage_rate_m3s=float(rates[i]),
                         endpoint_net_inflow_m3s=endpoint))
    closure = float((volumes[1]-volumes[0]).sum())-(records[1]['boundary_volume_m3']-records[0]['boundary_volume_m3'])
    require(abs(closure) < 1.e-6, 'integrated storage/exterior closure failed')
    return dict(schema='raftsim.cartesian_tile_flux_audit.v1', solver_sha256=digest(solver),
                input_manifest_sha256=digest(original), solver_steps_run=0,
                settling_accepted=False, normal_map_integrated=False,
                scope='tile control volumes, not river sections; instantaneous endpoint flux is not interval mean',
                seconds=seconds, storage_rate_m3s=float(rates.sum()),
                integrated_closure_residual_m3=closure, snapshots=reports,
                tiles_by_storage_rate=sorted(rows, key=lambda a: a['storage_rate_m3s']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cook', type=Path)
    parser.add_argument('before', type=int)
    parser.add_argument('after', type=int)
    parser.add_argument('--solver', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    require(not args.report.exists(), 'fresh report required')
    report = run(args.cook, args.before, args.after, args.solver)
    with args.report.open('x') as out:
        json.dump(report, out, indent=2, allow_nan=False)
        out.write('\n')
    print(json.dumps({k: report[k] for k in ('solver_steps_run', 'storage_rate_m3s', 'integrated_closure_residual_m3')}))
