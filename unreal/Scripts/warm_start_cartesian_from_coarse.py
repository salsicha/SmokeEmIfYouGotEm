"""Warm-start a fine Cartesian cook package from a settled coarse pre-cook.

The coarse frame (build_cartesian_coarse_settle.py, same tiles) gives the
water surface and depth-averaged velocity. They are interpolated bilinearly
across the whole lattice (dry coarse cells excluded) onto every fine cell
centre. Fine depth is that surface above the fine bed, and fine velocity the
interpolated current. Bed, boundaries, inlet discharge profiles, outflow
stages and roughness are the fine package's own, unchanged: only the
initial state differs from a cold start. The fine cook still has to settle
the local detail the coarse grid could not resolve.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path

import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lattice(manifest):
    keys = [tuple(k) for k in manifest['tile_indices']]
    xs, ys = [k[0] for k in keys], [k[1] for k in keys]
    return keys, min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1


def bilinear(field, valid, x, y):
    """NaN-free bilinear sample of field at fractional cell coordinates, ignoring invalid cells."""
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    total = np.zeros(x.shape)
    weight = np.zeros(x.shape)
    ny, nx = field.shape
    for dy, wy in ((0, 1 - fy), (1, fy)):
        for dx, wx in ((0, 1 - fx), (1, fx)):
            xi = np.clip(x0 + dx, 0, nx - 1)
            yi = np.clip(y0 + dy, 0, ny - 1)
            ok = valid[yi, xi]
            w = wx * wy * ok
            total += w * np.where(ok, field[yi, xi], 0.0)
            weight += w
    return np.where(weight > 1e-12, total / np.maximum(weight, 1e-12), np.nan)


def build(fine, coarse, frame, output, wet_depth):
    fine, coarse, frame, output = (Path(p).resolve() for p in (fine, coarse, frame, output))
    if output.exists():
        raise ValueError('Fresh output directory required')
    fine_manifest = json.loads((fine / 'manifest.json').read_text())
    coarse_manifest = json.loads((coarse / 'manifest.json').read_text())
    if fine_manifest['packages'] != coarse_manifest['packages']:
        raise ValueError('Coarse and fine packages must share tiles and order')
    keys, x0, y0, nx_t, ny_t = lattice(fine_manifest)
    fine_cells = fine_manifest['grid']['tile_cells']
    k = coarse_manifest['coarse_settle']['factor']
    coarse_cells = fine_cells // k
    h_c = np.load(frame / 'h.npy')
    u_c = np.load(frame / 'u.npy')
    v_c = np.load(frame / 'v.npy')
    # Global coarse rasters on the tile lattice (rows increase north).
    shape = (ny_t * coarse_cells, nx_t * coarse_cells)
    eta = np.full(shape, np.nan)
    depth = np.zeros(shape)
    vel_u, vel_v = np.zeros(shape), np.zeros(shape)
    for ordinal, (name, key) in enumerate(zip(coarse_manifest['packages'], keys)):
        rows = slice(ordinal * coarse_cells, (ordinal + 1) * coarse_cells)
        bed = np.load(coarse / name / 'bed.npy')
        gy, gx = (key[1] - y0) * coarse_cells, (key[0] - x0) * coarse_cells
        block = (slice(gy, gy + coarse_cells), slice(gx, gx + coarse_cells))
        h = h_c[rows]
        depth[block] = h
        eta[block] = bed + h
        vel_u[block], vel_v[block] = u_c[rows], v_c[rows]
    wet = depth > wet_depth
    output.mkdir(parents=True)
    inputs = []
    cold_volume = warm_volume = 0.0
    # Closed exterior banks (tile edges with no neighbour and no inlet/outlet)
    # must start exactly dry: the runtime export requires them so, and the
    # cold start had them so. Interpolation may leave a film there.
    present = set(keys)
    ports = {(p['tile_index'], p['edge']) for p in fine_manifest['boundary_probes']}
    edges = {'west': (-1, 0, np.s_[:, :2]), 'east': (1, 0, np.s_[:, -2:]),
             'south': (0, -1, np.s_[:2, :]), 'north': (0, 1, np.s_[-2:, :])}
    dried_cells, dried_volume = 0, 0.0
    centre = (np.arange(fine_cells) + 0.5) / k - 0.5  # fine cell centres in coarse-cell units within a tile
    for ordinal, (name, key) in enumerate(zip(fine_manifest['packages'], keys)):
        source = fine / name
        target = output / name
        target.mkdir()
        for item in ('scenario.json', 'bed.npy', 'features.json', 'probes.json'):
            # Unchanged inputs are hard-linked (fresh directories only, never
            # edited in place); copy where links are unavailable.
            try:
                os.link(source / item, target / item)
            except OSError:
                (target / item).write_bytes((source / item).read_bytes())
        bed = np.load(source / 'bed.npy')
        with np.load(source / 'initial_state.npz') as state:
            cold_volume += float(state['depth'].sum())
        gx = (key[0] - x0) * coarse_cells + centre
        gy = (key[1] - y0) * coarse_cells + centre
        x, y = np.meshgrid(gx, gy)
        surface = bilinear(eta, wet, x, y)
        h = np.where(np.isfinite(surface), np.maximum(surface - bed, 0.0), 0.0)
        u = np.where(h > 0, bilinear(vel_u, wet, x, y), 0.0)
        v = np.where(h > 0, bilinear(vel_v, wet, x, y), 0.0)
        u, v = np.nan_to_num(u), np.nan_to_num(v)
        for edge, (dx, dy, band) in edges.items():
            if (key[0] + dx, key[1] + dy) in present or (ordinal, edge) in ports:
                continue
            dried_cells += int(np.count_nonzero(h[band]))
            dried_volume += float(h[band].sum())
            h[band] = 0.0
        # The native solver zeroes velocity where depth is at most 1e-6 m (the
        # wet mask below) when it loads a state; match it so the declared start
        # is exactly the state the cook writes as its first frame.
        u, v = np.where(h > 1e-6, u, 0.0), np.where(h > 1e-6, v, 0.0)
        if h.max() > 10 or np.hypot(u, v).max() > 20:
            raise ValueError('Warm start exceeds the native depth/speed gates in ' + name)
        warm_volume += float(h.sum())
        np.savez_compressed(target / 'initial_state.npz', depth=h, eta=bed + h, u=u, v=v, hu=h * u, hv=h * v, wet=h > 1e-6)
        inputs.append(dict(name=name, files={f: sha(target / f) for f in
                                             ('scenario.json', 'bed.npy', 'initial_state.npz', 'features.json', 'probes.json')}))
    # The exact frame-0 arrays the native cook will write (tiles stacked in
    # package order), so a bounded run's start can be checked byte for byte.
    stacked = {name: [] for name in 'huv'}
    for name in fine_manifest['packages']:
        with np.load(output / name / 'initial_state.npz') as state:
            for field, key in (('h', 'depth'), ('u', 'u'), ('v', 'v')):
                stacked[field].append(np.asarray(state[key], dtype='<f8'))
    start_hashes = {}
    for field, parts in stacked.items():
        buffer = io.BytesIO()
        np.save(buffer, np.concatenate(parts))
        start_hashes[field] = hashlib.sha256(buffer.getvalue()).hexdigest()
    report = dict(fine_manifest)
    report.update(inputs=inputs, initial_time_seconds=0.0,
                  restart=dict(source_arrays_sha256=start_hashes, source_time_seconds=0.0,
                               kind='warm_start_from_coarse_pre_cook'),
                  initial_state='Warm start: settled coarse pre-cook surface and current interpolated onto the fine bed',
                  warm_start=dict(fine_manifest_sha256=sha(fine / 'manifest.json'), coarse_manifest_sha256=sha(coarse / 'manifest.json'),
                                  coarse_frame=str(frame), coarse_frame_h_sha256=sha(frame / 'h.npy'), factor=k,
                                  wet_depth_m=wet_depth, cold_volume_m3=cold_volume, warm_volume_m3=warm_volume,
                                  closed_bank_cells_dried=dried_cells, closed_bank_volume_removed_m3=dried_volume),
                  settled_hydraulics=False, normal_map_integrated=False)
    (output / 'manifest.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(tiles=len(inputs), cold_volume_m3=cold_volume, warm_volume_m3=warm_volume,
                          closed_bank_cells_dried=dried_cells, closed_bank_volume_removed_m3=dried_volume)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fine', required=True, type=Path)
    parser.add_argument('--coarse', required=True, type=Path)
    parser.add_argument('--frame', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--wet-depth', type=float, default=0.02)
    args = parser.parse_args()
    build(args.fine, args.coarse, args.frame, args.out, args.wet_depth)
