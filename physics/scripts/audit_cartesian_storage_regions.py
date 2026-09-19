"""Localize changing water storage in completed Cartesian snapshots (read-only).

Nearest route-sample station bands partition every cell, including dry terrain.
They are attribution regions, NOT cross-sections or measured/numerical fluxes.
No equilibrium, outlet calibration, or playable acceptance is inferred.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from audit_cartesian_cook_snapshot import digest


def require(condition, message):
    if not condition:
        raise ValueError(message)


def partition(grids, points, band_m):
    points = np.asarray(points, dtype=float)
    require(points.ndim == 2 and points.shape[0] >= 2 and points.shape[1] >= 3,
            "route needs station/east/north samples")
    require(np.isfinite(points).all() and np.all(np.diff(points[:, 0]) > 0),
            "route must be finite with increasing stations")
    require(points[0, 0] == 0 and np.isfinite(band_m) and band_m > 0,
            "route starts at zero; band width must be positive")
    dimensions = {(g['ny'], g['nx'], g['dx'], g['dy']) for g in grids}
    require(len(dimensions) == 1, "stacked grids must have identical dimensions")
    ny, nx, dx, dy = dimensions.pop()
    require(min(ny, nx, dx, dy) > 0, "grid dimensions must be positive")
    origins = np.array([(g['origin_x'], g['origin_y']) for g in grids])
    require(np.isfinite(origins).all(), "grid origins must be finite")
    lattice = (origins - origins.min(axis=0)) / [nx*dx, ny*dy]
    require(np.max(np.abs(lattice - np.rint(lattice))) < 1.e-8,
            "tiles must share a lattice")
    require(len(set(map(tuple, np.rint(lattice).astype(int)))) == len(grids),
            "duplicate tile ownership")
    # RaftSim GridSpec origin is the first CELL CENTER, not its lower corner.
    # Match solver_diagnostics.cpp and the captured-geometry preparation.
    offsets = np.stack(np.meshgrid(np.arange(nx)*dx,
                                  np.arange(ny)*dy), axis=-1).reshape(-1, 2)
    tree = cKDTree(points[:, 1:3])
    bands = []
    for origin in origins:
        _, nearest = tree.query(origin + offsets, workers=1)
        bands.append(np.floor(points[nearest, 0]/band_m).astype(np.int32))
    return np.concatenate(bands), (len(grids)*ny, nx), dx*dy


def compare_storage(before, after, labels, area, seconds):
    before, after, labels = (np.asarray(a).reshape(-1) for a in (before, after, labels))
    require(before.shape == after.shape == labels.shape, "partition/state shape mismatch")
    require(np.isfinite(before).all() and np.isfinite(after).all(), "nonfinite depth")
    require(np.all(before >= 0) and np.all(after >= 0), "negative depth")
    require(labels.dtype.kind in 'iu' and np.all(labels >= 0), "invalid region labels")
    require(np.isfinite(seconds) and seconds > 0 and np.isfinite(area) and area > 0,
            "positive finite time and cell area required")
    change = after-before
    n = int(labels.max())+1
    storage = np.bincount(labels, weights=change*area, minlength=n)
    counts = np.bincount(labels, minlength=n)
    require(abs(float(storage.sum())-float(change.sum()*area)) < 1.e-6,
            "regional storage does not close")
    regions = []
    for label in range(n):
        mask = labels == label
        wet = mask & (before > .01) & (after > .01)
        values = change[wet]
        regions.append(dict(band=label, cells=int(counts[label]),
                            storage_change_m3=float(storage[label]),
                            storage_rate_m3s=float(storage[label]/seconds),
                            common_wet_cells=int(values.size),
                            common_wet_stage_change_m=(dict(zip(
                                ('p05', 'median', 'p95'),
                                map(float, np.quantile(values, [.05, .5, .95]))))
                                if values.size else None)))
    return dict(storage_change_m3=float(storage.sum()),
                storage_rate_m3s=float(storage.sum()/seconds), regions=regions)


def run(cook, route, steps, band_m):
    require(len(steps) >= 2 and all(b > a for a, b in zip(steps, steps[1:])),
            "at least two strictly increasing steps required")
    original = Path((cook/'input_manifest_path.txt').read_text().strip())
    if not original.is_absolute():
        original = Path(__file__).resolve().parents[2]/original
    copied = cook/'input_manifest.json'
    require(digest(original) == digest(copied), "input manifest changed")
    manifest = json.loads(copied.read_text())
    require(len(set(manifest['packages'])) == len(manifest['packages']), "duplicate package")
    inputs = {entry['name']: entry for entry in manifest['inputs']}
    scenarios, beds = [], []
    for name in manifest['packages']:
        package = original.parent/name
        for filename in ('scenario.json', 'bed.npy'):
            require(digest(package/filename) == inputs[name]['files'][filename],
                    f"changed input: {name}/{filename}")
        scenario = json.loads((package/'scenario.json').read_text())
        bed = np.load(package/'bed.npy', allow_pickle=False)
        g = scenario['grid']
        require(bed.shape == (g['ny'], g['nx']) and np.isfinite(bed).all(), "invalid bed")
        scenarios.append(scenario)
        beds.append(bed)
    route_record = json.loads(route.read_text())
    require(route_record['horizontal_crs'] == 'EPSG:32610', "unexpected route CRS")
    labels, shape, area = partition([s['grid'] for s in scenarios],
                                    route_record['points'], band_m)
    bed = np.concatenate(beds)
    frames, states = [], []
    for step in steps:
        frame = cook/f'frame_{step:06d}'
        record = json.loads((frame/'complete.json').read_text())
        require(record['snapshot'] and record['step'] == step, "incomplete/wrong snapshot")
        require(all(np.isfinite(record[key]) for key in (
            'time_seconds', 'volume_m3', 'boundary_volume_m3')), "nonfinite frame metadata")
        h = np.load(frame/'h.npy', mmap_mode='r', allow_pickle=False)
        require(h.shape == shape and h.dtype == np.dtype('<f8'), "invalid depth layout")
        require(np.isfinite(h).all() and np.all(h >= 0), "invalid depth")
        volume = float(h.sum(dtype=np.float64)*area)
        require(abs(volume-record['volume_m3']) < 1.e-6, "native volume mismatch")
        record = dict(record, h_sha256=digest(frame/'h.npy'))
        frames.append(record)
        states.append(h)
    comparisons = []
    pairs = list(zip(range(len(steps)-1), range(1, len(steps))))
    if len(steps) > 2:
        pairs.append((0, len(steps)-1))
    ny = scenarios[0]['grid']['ny']
    for a, b in pairs:
        elapsed = frames[b]['time_seconds']-frames[a]['time_seconds']
        expected_elapsed = (steps[b]-steps[a])*manifest['dt_seconds']
        require(abs(elapsed-expected_elapsed) < 1.e-5, "snapshot clock/step mismatch")
        result = compare_storage(states[a], states[b], labels, area, elapsed)
        boundary_change = frames[b]['boundary_volume_m3']-frames[a]['boundary_volume_m3']
        closure = result['storage_change_m3']-boundary_change
        require(abs(closure) < 1.e-5, "storage/integrated exterior-flux closure failed")
        tiles = ((states[b]-states[a]).reshape(len(scenarios), -1).sum(axis=1)*area)
        result.update(from_step=steps[a], to_step=steps[b], elapsed_seconds=elapsed,
                      integrated_exterior_volume_m3=boundary_change,
                      exterior_closure_error_m3=closure,
                      largest_storage_losses=[dict(package=manifest['packages'][i],
                                                   storage_change_m3=float(tiles[i]))
                                              for i in np.argsort(tiles)[:10]])
        comparisons.append(result)
    edges = []
    selectors = {'west': (slice(None), 0), 'east': (slice(None), -1),
                 'south': (0, slice(None)), 'north': (-1, slice(None))}
    for probe in manifest['boundary_probes']:
        owner, edge = probe['tile_index'], probe['edge']
        selection = selectors[edge]
        tile_bed = bed[owner*ny:(owner+1)*ny][selection]
        samples = []
        for frame, h in zip(frames, states):
            depth = h[owner*ny:(owner+1)*ny][selection]
            wet = depth > .01
            stage = (tile_bed+depth)[wet]
            samples.append(dict(step=frame['step'], wet_cells=int(wet.sum()),
                                stage_m=(dict(zip(('min', 'median', 'max'),
                                                  map(float, [stage.min(), np.median(stage), stage.max()])))
                                         if stage.size else None)))
        edges.append(dict(probe=probe, samples=samples))
    return dict(schema='raftsim.cartesian_storage_regions.v1',
                input_manifest_sha256=digest(copied), route_sha256=digest(route),
                cook=str(cook), route=str(route), band_m=band_m, cells=int(labels.size),
                region_definition='Nearest route sample; endpoint context goes to endpoint band. '
                                  'Native east/north, no world-Y reflection. Not flux cross-sections.',
                passed=True, settling_accepted=False, frames=frames,
                comparisons=comparisons, physical_boundary_cell_stages=edges,
                limitations=['Storage localization does not identify the physical cause.',
                             'Static bed means depth change equals stage change at common-wet cells.',
                             'Boundary-cell stages are not prescribed ghost stages or numerical face flux.',
                             'No measured bathymetry, outlet calibration, or playable acceptance.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cook', type=Path)
    parser.add_argument('route', type=Path)
    parser.add_argument('--steps', nargs='+', type=int, required=True)
    parser.add_argument('--band-m', type=float, default=1000.)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    result = run(args.cook.resolve(), args.route.resolve(), args.steps, args.band_m)
    with args.report.open('x', encoding='utf-8') as output:
        json.dump(result, output, indent=2, allow_nan=False)
        output.write('\n')
    print(json.dumps({key: result[key] for key in ('passed', 'cells', 'settling_accepted')}))


if __name__ == '__main__':
    main()
