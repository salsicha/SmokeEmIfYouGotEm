"""Locate the Futaleufu Terminator along the OSM centreline from Sentinel-2 whitewater (numpy only).

The Terminator has no published coordinate. GoRafting's river-km chainage
(El Trono 27.5, Terminator 39.25) with El Trono at OSM 62.40 km puts it near
OSM 74.2 km. This audit measures, for every 100 m of OSM chainage between
--from-km and --to-km, the Sentinel-2 wet (NDWI > 0.05 or whitewater) and
whitewater pixel counts in a 170 m box on the centreline, on each archived
date, and reports the persistent whitewater runs. The same test at the OSM El
Trono node checks the indicator.

Output: a JSON report (per-bin counts per date, runs, the check at El Trono).
"""
import argparse
import json
from pathlib import Path

import numpy as np

from geo_frames import tm_forward, utm

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'physics/data/real_world/futaleufu_river_chile/futaleufu_sources_2026_09'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--from-km', type=float, default=60.0)
    ap.add_argument('--to-km', type=float, default=82.0)
    ap.add_argument('--min-white-px', type=int, default=8, help='whitewater pixels per 170 m box for a rapid bin, on every date')
    args = ap.parse_args()
    fm = json.loads((SRC / 'sentinel2/fetch_manifest.json').read_text())
    cld = json.loads((SRC / 'osm/futaleufu_centreline.json').read_text(encoding='utf-8'))
    cl = np.array(cld['centreline_lon_lat_chain'])
    x, y = tm_forward(cl[:, 0], cl[:, 1], utm(18, south=True)); ch = cl[:, 2]
    bins = np.arange(args.from_km * 1000, args.to_km * 1000, 100.0)
    per_date = {}
    for it in fm['items']:
        w = it['window_utm_m']; z = np.load(SRC / 'sentinel2' / it['npz'])
        B, G, R, N = [z[k].astype(np.float32) * 1e-4 - 0.1 for k in ('blue', 'green', 'red', 'nir')]
        white = (B > 0.22) & (G > 0.22) & (R > 0.18) & (np.abs(B - R) < 0.12)
        water = ((G - N) / np.maximum(G + N, 1e-3) > 0.05) | white
        wet_n, white_n = [], []
        for s0 in bins:
            k = (ch >= s0) & (ch < s0 + 100)
            if not k.any():
                wet_n.append(None); white_n.append(None); continue
            c0 = int((x[k].mean() - w['xmin']) / 10); r0 = int((w['ymax'] - y[k].mean()) / 10)
            rs, cs = slice(max(r0 - 8, 0), r0 + 9), slice(max(c0 - 8, 0), c0 + 9)
            wet_n.append(int(water[rs, cs].sum())); white_n.append(int(white[rs, cs].sum()))
        per_date[it['datetime'][:10]] = dict(wet_px=wet_n, white_px=white_n)
    dates = list(per_date)
    rapid = np.array([all(per_date[d]['white_px'][i] is not None and per_date[d]['white_px'][i] >= args.min_white_px for d in dates)
                      for i in range(len(bins))])
    runs = []
    i = 0
    while i < len(bins):
        if rapid[i]:
            j = i
            while j + 1 < len(bins) and rapid[j + 1]:
                j += 1
            mean_white = float(np.mean([per_date[d]['white_px'][k] for d in dates for k in range(i, j + 1)]))
            runs.append(dict(osm_km=[bins[i] / 1000, (bins[j] + 100) / 1000], mean_white_px=mean_white))
            i = j + 1
        else:
            i += 1
    nodes = {n['tags'].get('name'): n['chain_m'] for n in cld['nodes'] if n['tags'].get('name')}
    trono = nodes.get('El Trono')
    report = dict(
        schema='raftsim.futaleufu.terminator_location_audit.v1',
        method='Sentinel-2 pixels in a 170 m box on the OSM centreline per 100 m of chainage; whitewater = blue > 0.22, green > 0.22, '
               'red > 0.18, |blue - red| < 0.12 (surface reflectance); wet = NDWI > 0.05 or whitewater',
        dates=dates, bins_osm_km=(bins / 1000).tolist(), per_date=per_date, min_white_px=args.min_white_px,
        persistent_whitewater_runs=runs,
        el_trono_check=dict(osm_node_km=trono / 1000 if trono else None,
                            runs_containing=[r for r in runs if trono and r['osm_km'][0] * 1000 <= trono + 100 and r['osm_km'][1] * 1000 >= trono - 100]),
        gorafting_chainage=dict(el_trono_km=27.5, terminator_km=39.25, predicted_osm_km=(trono / 1000 + 39.25 - 27.5) if trono else None),
        conclusion='the Terminator is the persistent whitewater run nearest the predicted OSM km (measured appearance; the imaged flows are unknown)')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(dict(runs=runs, el_trono=report['el_trono_check'], predicted=report['gorafting_chainage']), indent=1))


if __name__ == '__main__':
    main()
