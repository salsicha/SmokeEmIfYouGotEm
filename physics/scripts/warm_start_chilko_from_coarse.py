"""Warm-start full-resolution Chilko inputs from a settled coarse pre-cook.

The coarse frame (build_chilko_coarse_settle.py) gives the water surface and
depth-averaged current. They are interpolated bilinearly in grid index
space, using wet coarse cells only, onto every fine cell centre. Fine depth
is that surface above the unchanged fine bed (optionally lowered to equal
conveyance on the fine bed, --conveyance-match). Velocity is zero wherever the
fine depth is at most the solver's 1e-6 m dry tolerance, matching what the
native solver does when it loads a state.

Everything else in the inputs folder is copied unchanged: geography, bed,
reference, friction, boundaries and scenario identity. The build report
records the warm start, so the existing review and export apply as they are.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from native_frame_io import load_frame, native_frame_paths  # noqa: E402

DRY = 1e-6
COPIED = ('coordinate_map.json', 'reference.npz', 'scenario/scenario.json', 'scenario/bed.npy',
          'scenario/features.json', 'scenario/probes.json')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bilinear(field, valid, y, x):
    """Bilinear sample at fractional (row, col) index coordinates over valid cells only."""
    y0, x0 = np.floor(y).astype(int), np.floor(x).astype(int)
    fy, fx = y - y0, x - x0
    ny, nx = field.shape
    total = np.zeros(np.broadcast(y, x).shape)
    weight = np.zeros_like(total)
    for dy, wy in ((0, 1 - fy), (1, fy)):
        for dx, wx in ((0, 1 - fx), (1, fx)):
            yi, xi = np.clip(y0 + dy, 0, ny - 1), np.clip(x0 + dx, 0, nx - 1)
            ok = valid[yi, xi]
            w = wx * wy * ok
            total += w * np.where(ok, field[yi, xi], 0.0)
            weight += w
    return np.where(weight > 1e-12, total / np.maximum(weight, 1e-12), np.nan)


def conveyance_levels(coarse_h, coarse_bed, fine_bed, k, iterations=40):
    """Per coarse cell, the water level on its k x k fine cells with the same mean conveyance.

    A coarse cell's bed is the block mean, so a narrow channel becomes wider
    and shallower and needs more water for the same discharge. Under one
    energy slope, Manning conveyance per unit width scales with h^(5/3); the
    level eta* with mean(max(eta* - b_fine, 0)^(5/3)) = h_coarse^(5/3) carries
    the coarse cell's discharge on the real bed. Returns eta* (NaN where dry).
    """
    ny, nx = coarse_h.shape
    pad, pad_x = ny * k - fine_bed.shape[0], nx * k - fine_bed.shape[1]
    beds = np.pad(fine_bed, ((0, pad), (0, pad_x)), constant_values=np.inf)
    beds = beds.reshape(ny, k, nx, k).transpose(0, 2, 1, 3).reshape(ny, nx, k * k)
    real = np.isfinite(beds)
    target = coarse_h ** (5 / 3)
    lo = np.where(real, beds, np.inf).min(axis=2)
    hi = coarse_bed + coarse_h + np.where(real, np.abs(beds - coarse_bed[..., None]), 0).max(axis=2)
    for _ in range(iterations):
        mid = 0.5 * (lo + hi)
        depth = np.where(real, np.maximum(mid[..., None] - np.where(real, beds, 0), 0.0), 0.0)
        mean = (depth ** (5 / 3)).sum(axis=2) / real.sum(axis=2)
        low = mean < target
        lo, hi = np.where(low, mid, lo), np.where(low, hi, mid)
    return np.where(coarse_h > 0, 0.5 * (lo + hi), np.nan)


def build(inputs, coarse, out, frame_index=-1, wet_depth=0.02, frame=None, conveyance_match=False):
    inputs, coarse, out = (Path(p).resolve() for p in (inputs, coarse, out))
    if out.exists():
        raise ValueError('Fresh warm-start inputs directory required')
    scenario = json.loads((inputs / 'scenario/scenario.json').read_text())
    grid = scenario['grid']
    bed = np.load(inputs / 'scenario/bed.npy')
    coarse_scenario = json.loads((coarse / 'scenario/scenario.json').read_text())
    settle = coarse_scenario['metadata']['coarse_settle']
    if settle['source_bed_sha256'] != sha(inputs / 'scenario/bed.npy') or \
            settle['source_scenario_sha256'] != sha(inputs / 'scenario/scenario.json'):
        raise ValueError('Coarse pre-cook was built from different inputs')
    k = settle['factor']
    cgrid = coarse_scenario['grid']
    cook = coarse / 'native' / coarse_scenario['metadata']['scenario_id']
    if frame is None:
        native = json.loads((cook / 'manifest.json').read_text())
        frame_path = native_frame_paths(cook, native)[frame_index]
    else:
        # An explicit saved frame of a stopped run, which has no manifest.
        frame_path = Path(frame).resolve()
        frame_path.relative_to(cook / 'frames')
    frame = load_frame(frame_path, (cgrid['ny'], cgrid['nx']))
    cbed = np.load(coarse / 'scenario/bed.npy')
    if not np.allclose(frame['eta'] - frame['h'], cbed, atol=1e-6):
        raise ValueError('Coarse frame does not match its bed')
    wet = frame['h'] > wet_depth
    rows, cols = np.indices(bed.shape)
    # Fine cell (r, c) centre in coarse index units: coarse cell 0 is centred
    # on fine index (k - 1) / 2 in both directions.
    cy, cx = (rows - (k - 1) * 0.5) / k, (cols - (k - 1) * 0.5) / k
    surface = bilinear(frame['eta'], wet, cy, cx)
    lowering = None
    if conveyance_match:
        level = conveyance_levels(np.where(wet, frame['h'], 0.0), cbed, bed, k)
        drop = np.where(wet & np.isfinite(level), frame['eta'] - level, 0.0)
        lowering = np.nan_to_num(bilinear(drop, wet, cy, cx))
        surface = surface - lowering
    h = np.where(np.isfinite(surface), np.maximum(surface - bed, 0.0), 0.0)
    u = np.nan_to_num(bilinear(frame['u'], wet, cy, cx))
    v = np.nan_to_num(bilinear(frame['v'], wet, cy, cx))
    if conveyance_match:
        # Manning under one slope: velocity scales with h^(2/3) of the coarse depth.
        coarse_depth = np.nan_to_num(bilinear(frame['h'], wet, cy, cx))
        ratio = np.where(coarse_depth > 1e-3, (h / np.maximum(coarse_depth, 1e-3)) ** (2 / 3), 0.0)
        u, v = u * np.minimum(ratio, 3.0), v * np.minimum(ratio, 3.0)
    wet_fine = h > DRY
    h = np.where(wet_fine, h, 0.0)
    u, v = np.where(wet_fine, u, 0.0), np.where(wet_fine, v, 0.0)
    if not (np.isfinite(h).all() and np.isfinite(u).all() and np.isfinite(v).all()):
        raise ValueError('Nonfinite warm start')
    out.mkdir(parents=True)
    for name in COPIED:
        (out / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(inputs / name, out / name)
    np.savez_compressed(out / 'scenario/initial_state.npz', depth=h, eta=bed + h, u=u, v=v,
                        hu=h * u, hv=h * v, wet=wet_fine)
    with np.load(inputs / 'scenario/initial_state.npz') as cold:
        cold_volume = float(cold['depth'].sum() * grid['dx'] * grid['dy'])
    report = copy.deepcopy(json.loads((inputs / 'build_report.json').read_text()))
    report['coarse_warm_start'] = dict(
        source_inputs=str(inputs), source_inputs_sha256={n: sha(inputs / n) for n in COPIED + ('scenario/initial_state.npz', 'build_report.json')},
        coarse_scenario_sha256=sha(coarse / 'scenario/scenario.json'), coarse_frame=str(frame_path),
        coarse_frame_sha256=sha(frame_path), factor=k, wet_depth_m=wet_depth,
        conveyance_match=bool(conveyance_match),
        surface_lowering_m=None if lowering is None else dict(
            median=float(np.median(lowering[h > DRY])), p95=float(np.percentile(lowering[h > DRY], 95))),
        cold_volume_m3=cold_volume, warm_volume_m3=float(h.sum() * grid['dx'] * grid['dy']),
        policy='Coarse-settled surface and current interpolated onto the unchanged fine bed; '
               'geography, friction, boundaries and scenario identity unchanged.')
    (out / 'build_report.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    summary = {key: value for key, value in report['coarse_warm_start'].items() if key != 'source_inputs_sha256'}
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', required=True, type=Path)
    parser.add_argument('--coarse', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--frame-index', type=int, default=-1)
    parser.add_argument('--wet-depth', type=float, default=0.02)
    parser.add_argument('--frame', type=Path, help='explicit saved coarse frame instead of --frame-index')
    parser.add_argument('--conveyance-match', action='store_true',
                        help='lower the surface per coarse cell to the fine level with equal mean conveyance')
    args = parser.parse_args()
    build(args.inputs, args.coarse, args.out, args.frame_index, args.wet_depth, args.frame, args.conveyance_match)
