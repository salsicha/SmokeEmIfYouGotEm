"""One calibration step for the inferred Hance rapid bed (numpy only).

Reads compare_hance_cook.py's textured-surface errors (cooked eta minus the
2021 DEM over whitewater, per 10 m station bin) and writes a bed correction
for build_hance_evidence_grid.py --bed-correction: delta = -relax * error,
Gaussian-smoothed along the station (--sigma-m), applied only within
--reach-m of a textured bin (elsewhere 0), converted from the scenario
station to the evidence station, and added to any previous correction.
With --fill-from-reference, stations away from textured bins use the cooked
median surface minus the evidence reference surface (the target the inferred
bed was derived from) with --reference-relax.
Only inferred (class 2) cells use it; measured bed never changes.
"""
import argparse
import json
from pathlib import Path

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('compare', type=Path)
    ap.add_argument('scenario_root', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--previous', type=Path, default=None)
    ap.add_argument('--relax', type=float, default=0.8)
    ap.add_argument('--reach-m', type=float, default=25.0)
    ap.add_argument('--max-step-m', type=float, default=1.0)
    ap.add_argument('--sigma-m', type=float, default=15.0)
    ap.add_argument('--fill-from-reference', action='store_true')
    ap.add_argument('--reference-relax', type=float, default=0.6)
    args = ap.parse_args()
    assert not args.output.exists()
    r = json.loads((args.compare / 'compare.json').read_text())
    bins = np.array(r['textured_surface_error_m']['by_bin'])
    ref = np.load(args.scenario_root / 'reference.npz')
    st = ref['station']; evs = ref['evidence_station']
    delta = np.zeros_like(st); have = np.zeros_like(st, bool)
    for s0, e in bins:
        m = (st >= s0) & (st < s0 + 10)
        delta[m] = -args.relax * e; have[m] = True
    sig = args.sigma_m / (st[1] - st[0]); rad = int(np.ceil(3 * sig))
    k = np.exp(-0.5 * (np.arange(-rad, rad + 1) / sig) ** 2)
    num = np.convolve(np.pad(delta, rad), k, mode='valid'); den = np.convolve(np.pad(have.astype(float), rad), k, mode='valid')
    near = np.zeros_like(have)
    for j in np.nonzero(have)[0]:
        near |= np.abs(st - st[j]) <= args.reach_m
    smooth = np.where(near & (den > 1e-6), num / np.maximum(den, 1e-6), 0.0)
    if args.fill_from_reference:
        prof = np.load(args.compare / 'profiles.npz')
        err = prof['cook_median'] - ref['ws_reference']
        err = np.where(np.isfinite(err), err, 0.0)
        fill = np.convolve(np.pad(-args.reference_relax * err, rad, mode='edge'), k / k.sum(), mode='valid')
        smooth = np.where(near, smooth, fill)
    smooth = np.clip(smooth, -args.max_step_m, args.max_step_m)
    order = np.argsort(evs)
    ev_grid = np.arange(0.0, float(np.ceil(evs.max() / 2) * 2) + 2.0, 2.0)
    step = np.interp(ev_grid, evs[order], smooth[order], left=0.0, right=0.0)
    if args.previous:
        prev = np.load(args.previous)
        step = step + np.interp(ev_grid, prev['station'], prev['delta'], left=0.0, right=0.0)
    np.savez(args.output, station=ev_grid, delta=step)
    print(json.dumps(dict(bins=len(bins), step_min_max=[float(smooth.min()), float(smooth.max())],
                          cumulative_min_max=[float(step.min()), float(step.max())]), indent=1))


if __name__ == '__main__':
    main()
