"""Wetted widths along the Chilko evidence reach: LiDAR, Sentinel-2 and cooks (numpy only).

Per --bin-m of evidence station:
- LiDAR: the flight-day wetted cells of the evidence grid (measured, 1 m;
  lake-outlet flow 57 falling to 33 m3/s over the flights);
- Sentinel-2: sub-pixel water fraction from the 10 m NIR band,
  f = clip((NIR_land - NIR) / (NIR_land - NIR_water), 0, 1), with NIR_water the
  5th percentile over the LiDAR channel core and NIR_land the per-bin median of
  a 25-60 m ring outside the LiDAR water; whitewater pixels count as water.
  Summed over pixels within --corridor-m of the LiDAR water (measured
  appearance; the method's own bias is read from the scenes of the LiDAR
  flight period);
- cooks: wet cells of a raftsim_water_solver frame on the curvilinear grid,
  at the flow of an image date (model output).
Width = area / bin length. Output: JSON (per-bin table and summary ratios).
"""
import argparse
import json
from pathlib import Path

import numpy as np

from build_pacuare_evidence_dressing import dilate
from build_pacuare_evidence_grid import edt_inside
from export_hance_evidence_runtime import read_frame


def nearest_station(E, N, cl):
    """Station of the nearest midline point (1-2 m spacing) for each (E, N)."""
    out = np.empty(E.shape)
    for k in range(0, E.size, 4096):
        e = E.ravel()[k:k + 4096, None]; n = N.ravel()[k:k + 4096, None]
        d2 = (e - cl[None, :, 0]) ** 2 + (n - cl[None, :, 1]) ** 2
        out.ravel()[k:k + 4096] = cl[np.argmin(d2, axis=1), 2]
    return out


def s2_width(npz, item, ev, X0, Y1, NX, NY, cl, bins, corridor_m):
    z = np.load(npz); w = item['window_utm_m']
    B, G, R, N = [z[k].astype(np.float64) * 1e-4 - 0.1 for k in ('blue', 'green', 'red', 'nir')]
    valid = (z['nir'] > 0) & (z['red'] > 0)
    white = (B > 0.20) & (G > 0.20) & (R > 0.16) & (np.abs(B - R) < 0.12)
    H, W = N.shape
    e = w['xmin'] + (np.arange(W) + 0.5) * 10.0; n = w['ymax'] - (np.arange(H) + 0.5) * 10.0
    E, Nn = np.meshgrid(e, n)
    c = np.floor(E - X0).astype(int); r = np.floor(Y1 - Nn).astype(int)
    inside = (c >= 0) & (c < NX) & (r >= 0) & (r < NY)
    cc, rr = np.clip(c, 0, NX - 1), np.clip(r, 0, NY - 1)
    river = ev['river']
    dist_out = edt_inside(~river)            # metres from the LiDAR water (0 inside)
    dist_in = edt_inside(river)              # metres inside the LiDAR water
    d_out = np.where(inside, dist_out[rr, cc], np.inf)
    d_in = np.where(inside, dist_in[rr, cc], 0.0)
    near = inside & (d_out <= 70.0)
    pst = np.full(E.shape, np.nan)
    pst[near] = nearest_station(E[near], Nn[near], cl)
    core = inside & valid & (d_in >= 6.0) & ~white
    if core.sum() < 5:
        return None
    nir_w = float(np.percentile(N[core], 5))
    out = []
    for b0 in bins[:-1]:
        b1 = b0 + (bins[1] - bins[0])
        inbin = inside & (pst >= b0) & (pst < b1)
        corr = inbin & (d_out <= corridor_m)
        ring = inbin & valid & (d_out >= 25.0) & (d_out <= 60.0)
        if corr.sum() == 0 or not valid[corr].all() or ring.sum() < 10:
            out.append(None); continue
        nir_l = float(np.median(N[ring]))
        f = np.clip((nir_l - N[corr]) / max(nir_l - nir_w, 1e-3), 0.0, 1.0)
        f = np.where(white[corr], 1.0, f)
        out.append(float(f.sum() * 100.0 / (b1 - b0)))
    return dict(nir_water=nir_w, widths=out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('evidence', type=Path)
    ap.add_argument('--s2', nargs=3, action='append', default=[], metavar=('NPZ', 'FETCH_MANIFEST', 'FLOW_M3S'))
    ap.add_argument('--cook', nargs=3, action='append', default=[], metavar=('SCENARIO_ROOT', 'RUN_DIR', 'FLOW_M3S'))
    ap.add_argument('--bin-m', type=float, default=250.0)
    ap.add_argument('--corridor-m', type=float, default=30.0)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    evm = json.loads((args.evidence / 'manifest.json').read_text())
    X0, Y1, NX, NY = evm['grid']['x0'], evm['grid']['y_top'], evm['grid']['nx'], evm['grid']['ny']
    ev = np.load(args.evidence / 'evidence_grid.npz')
    st = ev['station'].astype(np.float64)  # defined on the LiDAR channel only
    cl = np.asarray(json.loads((args.evidence / 'centreline.json').read_text())['points_xy_station'], np.float64)
    s0, s1 = evm['statistics']['reach_station_m']
    bins = np.arange(s0, s1 + 1e-6, args.bin_m)
    if bins[-1] < s1 - 1:
        bins = np.append(bins, bins[-1] + args.bin_m)
    L = args.bin_m
    lid = [float(((st >= b) & (st < b + L) & ev['river']).sum() / L) for b in bins[:-1]]
    table = dict(bin_start_evidence_station_m=bins[:-1].tolist(), lidar_flight_width_m=lid)
    summary = {}
    for npz, fm, q in args.s2:
        item = next(i for i in json.loads(Path(fm).read_text())['items'] if i['npz'] == Path(npz).name)
        res = s2_width(npz, item, ev, X0, Y1, NX, NY, cl, bins, args.corridor_m)
        key = f"s2_{item['datetime'][:10]}_{float(q):g}cms"
        if res is None:
            summary[key] = 'reach not covered'; continue
        table[key] = res['widths']
        ok = [(s, l) for s, l in zip(res['widths'], lid) if s is not None and l > 0]
        summary[key] = dict(flow_m3s=float(q), bins=len(ok), nir_water=res['nir_water'],
                            median_width_m=float(np.median([s for s, _ in ok])) if ok else None,
                            median_ratio_to_lidar=float(np.median([s / l for s, l in ok])) if ok else None)
    for root, run, q in args.cook:
        root, run = Path(root), Path(run)
        sc = json.loads((root / 'scenario/scenario.json').read_text())
        ny, nx, d = sc['grid']['ny'], sc['grid']['nx'], sc['grid']['dx']
        frames = sorted((run / 'frames').glob('frame_*.csv'))
        f = read_frame(frames[-1], ny, nx)
        ref = np.load(root / 'reference.npz')
        wx, wy = ref['world_x'], ref['world_y']
        s_off = json.loads((root / 'build_report.json').read_text())['evidence_station_range'][0]
        cst = np.broadcast_to(np.arange(nx) * d + s_off, (ny, nx))  # evidence station of each cooked column
        dxc, dyc = np.gradient(wx, axis=1), np.gradient(wy, axis=1); dxr, dyr = np.gradient(wx, axis=0), np.gradient(wy, axis=0)
        area = np.abs(dxc * dyr - dyc * dxr)
        wet = (f['wet'] > 0.5) & (f['h'] > 0.02)
        widths = [float((area * (wet & (cst >= b) & (cst < b + L))).sum() / L) for b in bins[:-1]]
        key = f'cook_{float(q):g}cms'
        table[key] = widths
        summary[key] = dict(flow_m3s=float(q), median_width_m=float(np.median(widths)),
                            median_ratio_to_lidar=float(np.median([c / l for c, l in zip(widths, lid) if l > 0])))
        for sk, sv in list(table.items()):
            if sk.startswith('s2_') and sk.endswith(f'_{float(q):g}cms'):
                ok = [(c, s) for c, s in zip(widths, sv) if s is not None and s > 0]
                summary[key]['median_ratio_to_' + sk] = float(np.median([c / s for c, s in ok])) if ok else None
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(dict(schema='raftsim.chilko.width_check.v1', method=__doc__.strip(), bin_m=L,
                                        corridor_m=args.corridor_m, summary=summary, table=table), indent=1) + '\n')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
