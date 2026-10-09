"""Coarsen a Cartesian native cook package for a fast settling pre-cook.

A full river at 1 m cells and 0.01 s steps takes days of wall time to fill
and settle from its construction depths. The same domain coarsened inside
each tile (k x k fine cells per coarse cell) keeps every tile footprint,
neighbour and physical boundary edge, so the native solver settles the whole
river k^3 times faster with unchanged physics. Its steady state then
warm-starts the fine cook (warm_start_cartesian_from_coarse.py); it is never
a runtime field itself.

Per k x k block: bed is the mean bed; depth keeps the block's water volume;
velocity keeps its momentum (discharge-weighted). Inlet ghost profiles are
averaged the same way, so each coarse inlet face carries exactly the fine
face's discharge. Outflow stages, bank edges and Manning roughness are
copied unchanged.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def block_mean(array, k):
    ny, nx = array.shape
    return array.reshape(ny // k, k, nx // k, k).mean(axis=(1, 3))


def coarsen_tile(folder, output, k, dt):
    scenario = json.loads((folder / 'scenario.json').read_text())
    grid = scenario['grid']
    nx, ny = grid['nx'], grid['ny']
    if nx % k or ny % k or grid['dx'] != grid['dy']:
        raise ValueError('Tile cells must divide by the coarsening factor')
    bed = np.load(folder / 'bed.npy')
    with np.load(folder / 'initial_state.npz') as state:
        h, u, v = state['depth'], state['u'], state['v']
    coarse_h = block_mean(h, k)
    wet = coarse_h > 1e-9
    momentum_u, momentum_v = block_mean(h * u, k), block_mean(h * v, k)
    coarse_u = np.where(wet, momentum_u / np.where(wet, coarse_h, 1.0), 0.0)
    coarse_v = np.where(wet, momentum_v / np.where(wet, coarse_h, 1.0), 0.0)
    coarse_bed = block_mean(bed, k)
    output.mkdir(parents=True)
    np.save(output / 'bed.npy', coarse_bed)
    np.savez_compressed(output / 'initial_state.npz', depth=coarse_h, eta=coarse_bed + coarse_h, u=coarse_u, v=coarse_v,
                        hu=coarse_h * coarse_u, hv=coarse_h * coarse_v, wet=coarse_h > 1e-6)
    for name in ('features.json', 'probes.json'):
        (output / name).write_bytes((folder / name).read_bytes())
    coarse = copy.deepcopy(scenario)
    spacing = grid['dx'] * k
    coarse['grid'] = dict(nx=nx // k, ny=ny // k, dx=spacing, dy=spacing,
                          origin_x=grid['origin_x'] - grid['dx'] / 2 + spacing / 2,
                          origin_y=grid['origin_y'] - grid['dy'] / 2 + spacing / 2)
    coarse['fixed_dt'] = dt
    coarse['metadata'] = dict(scenario['metadata'], generator='build_cartesian_coarse_settle.py',
                              description='Coarse settling pre-cook of ' + scenario['metadata']['scenario_id'] + '; never a runtime field')
    for boundary in coarse['boundaries']:
        cells = boundary.get('ghost_cells')
        if not cells:
            continue
        ghosts = np.asarray(cells, float).reshape(2, -1, 4)
        n = ghosts.shape[1]
        if n % k:
            raise ValueError('Ghost edge must divide by the coarsening factor')
        layers = []
        for layer in ghosts:
            blocks = layer.reshape(n // k, k, 4)
            depth = blocks[:, :, 1].mean(axis=1)
            flowing = depth > 1e-12
            safe = np.where(flowing, depth, 1.0)
            gu = np.where(flowing, (blocks[:, :, 1] * blocks[:, :, 2]).mean(axis=1) / safe, 0.0)
            gv = np.where(flowing, (blocks[:, :, 1] * blocks[:, :, 3]).mean(axis=1) / safe, 0.0)
            layers.append(np.c_[blocks[:, :, 0].mean(axis=1), depth, gu, gv])
        boundary['ghost_cells'] = np.concatenate(layers).tolist()
    (output / 'scenario.json').write_text(json.dumps(coarse, indent=2, allow_nan=False) + '\n')
    files = {f: sha(output / f) for f in ('scenario.json', 'bed.npy', 'initial_state.npz', 'features.json', 'probes.json')}
    return float((h.sum()) * grid['dx'] * grid['dy']), float(coarse_h.sum() * spacing * spacing), files


def build(source, output, k, dt):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError('Fresh output directory required')
    manifest = json.loads((source / 'manifest.json').read_text())
    if manifest.get('schema') != 'raftsim.cartesian_flow_cook.v1':
        raise ValueError('Cartesian cook package required')
    output.mkdir(parents=True)
    fine_volume = coarse_volume = 0.0
    inputs = []
    for name in manifest['packages']:
        fine, coarse, files = coarsen_tile(source / name, output / name, k, dt)
        fine_volume += fine
        coarse_volume += coarse
        inputs.append(dict(name=name, files=files))
    if abs(fine_volume - coarse_volume) > 1e-6 * max(fine_volume, 1.0):
        raise ValueError('Coarsening changed the water volume')
    report = dict(manifest)
    report.update(dt_seconds=dt, inputs=inputs, grid=dict(cell_m=manifest['grid']['cell_m'] * k,
                                                          tile_cells=manifest['grid']['tile_cells'] // k),
                  coarse_settle=dict(source_manifest=str(source / 'manifest.json'), source_manifest_sha256=sha(source / 'manifest.json'),
                                     factor=k, initial_volume_m3=coarse_volume,
                                     purpose='Settling pre-cook to warm-start the fine cook; never a runtime field'),
                  settled_hydraulics=False, normal_map_integrated=False)
    (output / 'manifest.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(tiles=len(inputs), factor=k, dt_seconds=dt, volume_m3=coarse_volume)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--factor', type=int, default=4)
    parser.add_argument('--dt', type=float, default=0.05)
    args = parser.parse_args()
    build(args.source, args.out, args.factor, args.dt)
