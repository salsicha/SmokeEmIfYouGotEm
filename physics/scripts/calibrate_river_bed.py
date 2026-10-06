"""One calibration step for an inferred river bed (numpy only).

Reads compare_river_cook.py's per-station cooked median surface and the
evidence reference surface, and writes a bed correction for the evidence
builder's --bed-correction: delta = -relax * (cooked - reference),
Gaussian-smoothed along the station (--sigma-m), clipped per step, converted
from the scenario station to the evidence station and added to any previous
correction. Only inferred (class 2) cells use it.
"""
import argparse
import json
from pathlib import Path

import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('compare', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--previous', type=Path, default=None)
    ap.add_argument('--relax', type=float, default=0.7)
    ap.add_argument('--sigma-m', type=float, default=15.0)
    ap.add_argument('--max-step-m', type=float, default=1.0)
    args = ap.parse_args()
    assert not args.output.exists()
    p = np.load(args.compare / 'profiles.npz')
    st, evs = p['station'], p['evidence_station']
    err = p['cook_median'] - p['ws_reference']
    err = np.where(np.isfinite(err), err, 0.0)
    sig = args.sigma_m / (st[1] - st[0]); rad = int(np.ceil(3 * sig))
    k = np.exp(-0.5 * (np.arange(-rad, rad + 1) / sig) ** 2); k /= k.sum()
    step = np.clip(np.convolve(np.pad(-args.relax * err, rad, mode='edge'), k, mode='valid'), -args.max_step_m, args.max_step_m)
    order = np.argsort(evs)
    ev_grid = np.arange(float(np.floor(evs.min() / 2) * 2), float(np.ceil(evs.max() / 2) * 2) + 2.0, 2.0)
    delta = np.interp(ev_grid, evs[order], step[order])
    if args.previous:
        prev = np.load(args.previous)
        delta = delta + np.interp(ev_grid, prev['station'], prev['delta'])
    np.savez(args.output, station=ev_grid, delta=delta)
    print(json.dumps(dict(step_min_max=[float(step.min()), float(step.max())], cumulative_min_max=[float(delta.min()), float(delta.max())],
                          error_median_abs=float(np.median(np.abs(err)))), indent=1))


if __name__ == '__main__':
    main()
