"""Check the digitised Batoka Gorge rapid stations against Sentinel-2 whitewater (numpy only).

The 25 rapid stations in scenario_zambezi_run/scenario.json come from
digitising a stylised, non-georeferenced rapid map. This audit measures, for
every --bin-m of route station (production_corridor route_stationing.json),
the Sentinel-2 whitewater and wet pixel counts in a --box-m box on the route,
on each archived date (Victoria Falls flows 203-2,794 m3/s), reports the
persistent whitewater runs (whitewater on every low-water date), and gives
each digitised rapid the nearest run and its offset.

Output: a JSON report (per-bin counts per date, runs, per-rapid offsets).
"""
import argparse
import json
from pathlib import Path

import numpy as np

from geo_frames import tm_forward, utm

ROOT = Path(__file__).resolve().parents[2]
Z = ROOT / 'physics/data/real_world/zambezi_batoka_gorge'
SRC = Z / 'zambezi_sources_2026_09'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--bin-m', type=float, default=100.0)
    ap.add_argument('--box-m', type=float, default=110.0)
    ap.add_argument('--min-white-px', type=int, default=6, help='whitewater pixels per box for a rapid bin, on every low-water date')
    ap.add_argument('--low-water-max-m3s', type=float, default=1000.0)
    args = ap.parse_args()
    fm = json.loads((SRC / 'sentinel2/fetch_manifest.json').read_text())
    flows = {i['id']: i['victoria_falls_flow_m3s'] for i in json.loads((SRC / 'manifest.json').read_text())['sources']['sentinel2']['items']}
    route = json.loads((Z / 'production_corridor/boiling_pot_to_mukuni_beach/hydrography/route_stationing.json').read_text())
    lon = np.array([s['lon'] for s in route['samples']]); lat = np.array([s['lat'] for s in route['samples']])
    sta = np.array([s['station_m'] for s in route['samples']])
    x, y = tm_forward(lon, lat, utm(35, south=True))
    bins = np.arange(0.0, sta[-1], args.bin_m)
    bx = np.interp(bins + args.bin_m / 2, sta, x); by = np.interp(bins + args.bin_m / 2, sta, y)
    half = int(round(args.box_m / 20.0))
    per_date = {}
    for it in fm['items']:
        w = it['window_utm_m']; z = np.load(SRC / 'sentinel2' / it['npz'])
        B, G, R, N = [z[k].astype(np.float32) * 1e-4 - 0.1 for k in ('blue', 'green', 'red', 'nir')]
        white = (B > 0.20) & (G > 0.20) & (R > 0.16) & (np.abs(B - R) < 0.12)
        water = ((G - N) / np.maximum(G + N, 1e-3) > 0.05) | white
        wet_n, white_n = [], []
        for cx, cy in zip(bx, by):
            c0 = int((cx - w['xmin']) / 10); r0 = int((w['ymax'] - cy) / 10)
            rs, cs = slice(max(r0 - half, 0), r0 + half + 1), slice(max(c0 - half, 0), c0 + half + 1)
            wet_n.append(int(water[rs, cs].sum())); white_n.append(int(white[rs, cs].sum()))
        per_date[it['datetime'][:10]] = dict(flow_m3s=flows[it['id']], wet_px=wet_n, white_px=white_n)
    low = [d for d, v in per_date.items() if v['flow_m3s'] <= args.low_water_max_m3s]
    rapid = np.array([all(per_date[d]['white_px'][i] >= args.min_white_px for d in low) for i in range(len(bins))])
    runs, i = [], 0
    while i < len(bins):
        if rapid[i]:
            j = i
            while j + 1 < len(bins) and rapid[j + 1]:
                j += 1
            runs.append(dict(station_m=[float(bins[i]), float(bins[j] + args.bin_m)],
                             mean_white_px_low_water=float(np.mean([per_date[d]['white_px'][k] for d in low for k in range(i, j + 1)]))))
            i = j + 1
        else:
            i += 1
    scen = json.loads((Z / 'scenario_zambezi_run/scenario.json').read_text())
    rapids = []
    for r in scen['rapids']:
        s = r['station_m']
        best = min(runs, key=lambda u: 0.0 if u['station_m'][0] <= s <= u['station_m'][1]
                   else min(abs(s - u['station_m'][0]), abs(s - u['station_m'][1]))) if runs else None
        off = None if best is None else (0.0 if best['station_m'][0] <= s <= best['station_m'][1]
                                         else (best['station_m'][0] - s if s < best['station_m'][0] else best['station_m'][1] - s))
        rapids.append(dict(number=r['rapid_number'], name=r['display_name'], difficulty=r['difficulty_label'], digitised_station_m=s,
                           nearest_run_m=None if best is None else best['station_m'], offset_to_run_m=off))
    report = dict(
        schema='raftsim.zambezi.rapid_location_audit.v1',
        method=(f'Sentinel-2 pixels in a {args.box_m:.0f} m box on the route per {args.bin_m:.0f} m of station; whitewater = blue > 0.20, '
                'green > 0.20, red > 0.16, |blue - red| < 0.12 (surface reflectance); wet = NDWI > 0.05 or whitewater; a rapid bin has '
                f'>= {args.min_white_px} whitewater pixels on every date with Victoria Falls flow <= {args.low_water_max_m3s:.0f} m3/s'),
        dates=per_date and list(per_date), low_water_dates=low, bins_station_m=bins.tolist(), per_date=per_date,
        persistent_whitewater_runs=runs, digitised_rapids=rapids,
        note='the route is the OSM-derived production centreline; the digitised stations are from a stylised map (not georeferenced)')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(dict(runs=runs, rapids=[(r['number'], r['name'], r['digitised_station_m'], r['offset_to_run_m']) for r in rapids]), indent=1))


if __name__ == '__main__':
    main()
