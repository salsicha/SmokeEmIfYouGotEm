"""Measured colour of the Chilko's water from Sentinel-2 L2A (numpy only).

The rendered Lava Canyon water reads deep blue; the Chilko carries glacial
flour from Chilko Lake and photographs turquoise-green. This measures the
water-leaving colour the optics should reproduce.

Pixels: 10 m Sentinel-2 L2A surface reflectance (DN * 1e-4 - 0.1) within one
pixel of the BC Freshwater Atlas route centreline, that are water (NDWI > 0.2
and NIR < 0.05, which also caps the forest share of a mixed bank pixel) and
not whitewater. The window also holds ponds and oxbows; the centreline
restriction keeps them out. Reported per image date (with the 08MA002
lake-outlet flow): the median R, G, B reflectance of the whole route in the
window and of the Lava Canyon evidence reach (corridor chainage 43.9-47.9
km), and the channel ratios R/G and B/G, which do not depend on exposure.

Limits: 10 m pixels on a 25-40 m canyon river mix bank, shadow and water, so
absolute reflectance is approximate; the ratios are the target. L2A is
atmospherically corrected but not corrected for sun glint or adjacency.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from build_chilko_evidence_grid import ROUTE, SRC, UTM10
from geo_frames import tm_forward

ROOT = Path(__file__).resolve().parents[2]
REACH_CHAIN_M = (43900.0, 47900.0)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    rj = json.loads(ROUTE.read_text())
    geom = rj['features'][0]['geometry'] if 'features' in rj else rj['geometry']
    lonlat = np.array(geom['coordinates'])[:, :2]
    rx, ry = tm_forward(lonlat[:, 0], lonlat[:, 1], UTM10)
    rc = np.r_[0, np.cumsum(np.hypot(np.diff(rx), np.diff(ry)))]
    S = np.arange(0.0, rc[-1], 2.0); X = np.interp(S, rc, rx); Y = np.interp(S, rc, ry)
    fm = json.loads((SRC / 'sentinel2/fetch_manifest.json').read_text())
    flows = {it['id']: it for it in json.loads((SRC / 'manifest.json').read_text())['sources']['sentinel2']['items']}
    dates = []
    for it in fm['items']:
        z = np.load(SRC / 'sentinel2' / it['npz']); w = it['window_utm_m']
        B, G, R, N = [z[k].astype(np.float32) * 1e-4 - 0.1 for k in ('blue', 'green', 'red', 'nir')]
        ny, nx = B.shape
        near = np.zeros((ny, nx), bool); chain = np.full((ny, nx), np.nan)
        inwin = (X > w['xmin']) & (X < w['xmax']) & (Y > w['ymin']) & (Y < w['ymax'])
        for x, y, s in zip(X[inwin], Y[inwin], S[inwin]):
            c = int((x - w['xmin']) / 10.0); r = int((w['ymax'] - y) / 10.0)
            near[max(r - 1, 0):r + 2, max(c - 1, 0):c + 2] = True
            chain[max(r - 1, 0):r + 2, max(c - 1, 0):c + 2] = s
        water = ((G - N) / np.maximum(G + N, 1e-6) > 0.2) & (N < 0.05)
        white = (B > 0.20) & (G > 0.20) & (R > 0.16) & (np.abs(B - R) < 0.12)
        route = near & water & ~white
        reach = route & (chain >= REACH_CHAIN_M[0]) & (chain <= REACH_CHAIN_M[1])

        def stats(m):
            if not m.any():
                return None
            r, g, b = (float(np.median(c[m])) for c in (R, G, B))
            return dict(pixels=int(m.sum()), median_reflectance_rgb=[r, g, b], red_over_green=r / g, blue_over_green=b / g)

        dates.append(dict(image=it['id'], date=it['datetime'][:10], flow_08MA002_m3s=flows[it['id']]['flow_08MA002_m3s'],
                          npz_sha256=sha(SRC / 'sentinel2' / it['npz']), route_in_window=stats(route), lava_canyon_reach=stats(reach)))
    ratios = np.array([[d['route_in_window']['red_over_green'], d['route_in_window']['blue_over_green']] for d in dates])
    green_dominant = bool((ratios[:, 1] <= 1.0).all() and (ratios[:, 0] < ratios[:, 1]).all())
    report = dict(
        schema='raftsim.chilko.sentinel2_water_colour.v1', generator='physics/scripts/measure_chilko_water_colour.py',
        method=__doc__.strip().split('\n\n')[1].replace('\n', ' '),
        route=dict(path=ROUTE.relative_to(ROOT).as_posix(), sha256=sha(ROUTE)), reach_chainage_m=list(REACH_CHAIN_M),
        dates=dates,
        summary=dict(route_red_over_green_min_max=[float(ratios[:, 0].min()), float(ratios[:, 0].max())],
                     route_blue_over_green_min_max=[float(ratios[:, 1].min()), float(ratios[:, 1].max())],
                     green_ge_blue_gt_red_on_every_date=green_dominant),
        measured=True, limits=__doc__.strip().split('\n\n')[2].replace('\n', ' '))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    for d in dates:
        a, b = d['route_in_window'], d['lava_canyon_reach']
        print(d['date'], d['flow_08MA002_m3s'], 'route', a['pixels'], ['%.3f' % v for v in a['median_reflectance_rgb']],
              'R/G %.2f B/G %.2f' % (a['red_over_green'], a['blue_over_green']),
              '| reach', b and b['pixels'], b and ['%.3f' % v for v in b['median_reflectance_rgb']])


if __name__ == '__main__':
    main()
