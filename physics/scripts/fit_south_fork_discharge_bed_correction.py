"""Fit the settled-surface depth correction for the discharge-consistent bed.

Section cooks settle from their upstream cut downward, so a surface bias is
only meaningful where a station bin already passes the authored discharge.
For those settled bins this relates the cooked-minus-captured surface error
to the bed design (centreline depth H, pool weight) and fits one fractional
depth factor c on non-pool bins: depth_needed ~ (1 + c) * H_design. It writes
a combined bias file for build_south_fork_discharge_bed.py: the measured
settled bias where available, otherwise c * H_design.

Args: output.npz --pair ANALYSIS_DIR BED_DIR [--pair ...]
"""
import argparse
import json
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--pair', nargs=2, action='append', required=True, metavar=('ANALYSIS', 'BED'))
    parser.add_argument('--design-bed', type=Path, required=True, help='bed whose design the combined bias will correct')
    args = parser.parse_args()
    ratios, rows = [], []
    measured = {}
    for analysis, bed in args.pair:
        b = np.load(Path(analysis) / 'bias.npz')
        d = json.loads((Path(bed) / 'design.json').read_text())
        centers = np.array(d['station_center_m']); H = np.array(d['centerline_depth_m']); wp = np.array(d['pool_weight'])
        st = b['station']; raw = b['raw_bias']; used = b['used'].astype(bool)
        Hs = np.interp(st, centers, H); ws = np.interp(st, centers, wp)
        sel = used & np.isfinite(raw)
        for s, e, h, w in zip(st[sel], raw[sel], Hs[sel], ws[sel]):
            rows.append((s, e, h, w))
            measured[round(float(s), 1)] = float(e)
    rows = np.array(rows)
    riffle = rows[:, 3] < 0.01
    c = float(np.median(rows[riffle, 1] / rows[riffle, 2]))
    pool_err = float(np.median(rows[~riffle, 1])) if (~riffle).any() else None
    print('settled bins', len(rows), 'non-pool', int(riffle.sum()), 'fractional depth factor c = %.3f' % c,
          'median non-pool error %.3f m, median pool error %s' % (np.median(rows[riffle, 1]), pool_err))
    for lo, hi in ((0.2, 0.5), (0.5, 0.8), (0.8, 1.2), (1.2, 2.3)):
        m = riffle & (rows[:, 2] >= lo) & (rows[:, 2] < hi)
        if m.any():
            print('  H %.1f-%.1f m: n=%d median error %.3f m, median ratio %.3f' % (lo, hi, m.sum(), np.median(rows[m, 1]), np.median(rows[m, 1] / rows[m, 2])))
    d = json.loads((args.design_bed / 'design.json').read_text())
    centers = np.array(d['station_center_m']); H = np.array(d['centerline_depth_m']); wp = np.array(d['pool_weight'])
    Hn = np.array(d['normal_depth_m'])
    # Pools are stage-controlled by the next riffle (settled pool error ~0):
    # only the normal-depth (riffle) share of the design is scaled.
    model = c * Hn * (1.0 - wp)
    combined = model.copy()
    key = np.round(centers, 1)
    have = np.array([k in measured for k in key])
    combined[have] = [measured[k] for k in key[have]]
    kern = np.exp(-0.5 * (np.arange(-9, 10) / 3.0) ** 2); kern /= kern.sum()
    smooth = np.convolve(np.pad(combined, 9, mode='edge'), kern, mode='valid')
    np.savez(args.output, station=centers, bias=smooth, measured=have, fractional_factor=c)
    print('bins measured %d of %d; combined bias median %.3f, p5/p95 %s' % (have.sum(), len(centers), np.median(smooth), np.percentile(smooth, [5, 95]).round(3)))


if __name__ == '__main__':
    main()
