"""Review candidate Futaleufu whitewater along the captured OSM centreline.

GoRafting's approximate river-km chainage
(El Trono 27.5, Terminator 39.25) with El Trono at OSM 62.40 km puts it near
OSM 74.2 km. This audit measures, for every 100 m of OSM chainage between
--from-km and --to-km, the Sentinel-2 wet (NDWI > 0.05 or whitewater) and
whitewater pixel counts in a 170 m box on the centreline, on each archived
date, and reports the persistent whitewater runs. The same test at the OSM El
Trono node checks the indicator.

Output: a JSON report (per-bin counts per date, runs, the check at El Trono).
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from geo_frames import tm_forward, utm
from futaleufu_imagery import grid, load_reflectance, sampling_points

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'physics/data/real_world/futaleufu_river_chile/futaleufu_sources_2026_09'


def count_box(water, white, valid, east, north, item, radius=8):
    """Count a complete native-grid box; unknown support is never dry land."""
    rows, cols = sampling_points(east, north, item)
    r0, c0 = int(np.floor(rows + .5)), int(np.floor(cols + .5))
    if (r0-radius < 0 or c0-radius < 0 or
            r0+radius >= valid.shape[0] or c0+radius >= valid.shape[1]):
        return None, None, None
    region = np.s_[r0-radius:r0+radius+1, c0-radius:c0+radius+1]
    unknown = int((~valid[region]).sum())
    if unknown:
        return None, None, unknown
    return int(water[region].sum()), int(white[region].sum()), 0


def bin_centres(chain, east, north, bins, width=100.):
    """Interpolate on source segments; sparse OSM vertices are not data gaps."""
    chain,east,north,bins=map(lambda a:np.asarray(a,dtype=float),(chain,east,north,bins))
    if (chain.ndim!=1 or len(chain)<2 or east.shape!=chain.shape or north.shape!=chain.shape or
            bins.ndim!=1 or not len(bins) or np.any(np.diff(chain)<=0) or
            np.any(np.diff(bins)<=0) or not all(np.isfinite(a).all() for a in (chain,east,north,bins)) or
            not np.isfinite(width) or width<=0 or bins[0]<chain[0] or bins[-1]+width>chain[-1]):
        raise ValueError('Ordered in-route bins and finite source-segment coordinates required')
    centres=bins+width/2.
    return np.interp(centres,chain,east),np.interp(centres,chain,north)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--from-km', type=float, default=60.0)
    ap.add_argument('--to-km', type=float, default=82.0)
    ap.add_argument('--min-white-px', type=int, default=8, help='whitewater pixels per 170 m box for a rapid bin, on every date')
    args = ap.parse_args()
    if args.out.exists():ap.error('Fresh report path required; preserve earlier evidence')
    if (not np.isfinite([args.from_km, args.to_km]).all() or
            args.to_km <= args.from_km or args.min_white_px < 1):
        ap.error('Finite increasing chainage and a positive pixel threshold required')
    fm = json.loads((SRC / 'sentinel2/fetch_manifest.json').read_text(encoding='utf-8'))
    cld = json.loads((SRC / 'osm/futaleufu_centreline.json').read_text(encoding='utf-8'))
    cl = np.array(cld['centreline_lon_lat_chain'])
    x, y = tm_forward(cl[:, 0], cl[:, 1], utm(18, south=True)); ch = cl[:, 2]
    bins = np.arange(args.from_km * 1000, args.to_km * 1000, 100.0)
    centres_east,centres_north=bin_centres(ch,x,y,bins)
    per_date = {}
    for it in fm['items']:
        meta = grid(it)
        reflectance, valid = load_reflectance(SRC / 'sentinel2', it)
        B, G, R, N = [reflectance[k] for k in ('blue', 'green', 'red', 'nir')]
        white = (B > 0.22) & (G > 0.22) & (R > 0.18) & (np.abs(B - R) < 0.12)
        water = ((G - N) / np.maximum(G + N, 1e-3) > 0.05) | white
        wet_n, white_n, unknown_n = [], [], []
        for east,north in zip(centres_east,centres_north):
            wet, bright, unknown = count_box(water, white, valid, east, north, it)
            wet_n.append(wet); white_n.append(bright); unknown_n.append(unknown)
        per_date[it['datetime'][:10]] = dict(wet_px=wet_n, white_px=white_n,
            unknown_px=unknown_n, npz_sha256=it['npz_sha256'],
            native_grid=dict(x0=meta['x0'], y0=meta['y0'], cell_m=meta['cell_m']))
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
        schema='raftsim.futaleufu.terminator_location_audit.v3',
        sources_sha256={str(p.relative_to(SRC)): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in (SRC/'sentinel2/fetch_manifest.json', SRC/'osm/futaleufu_centreline.json')},
        method='Sentinel-2 pixels in a 170 m box at each 100 m bin midpoint interpolated on the captured OSM segments; whitewater = blue > 0.22, green > 0.22, '
               'red > 0.18, |blue - red| < 0.12 (surface reflectance); wet = NDWI > 0.05 or whitewater',
        dates=dates, bins_osm_km=(bins / 1000).tolist(), per_date=per_date, min_white_px=args.min_white_px,
        sampling_centres_utm18s_m=np.c_[centres_east,centres_north].tolist(),
        sampling_policy='Linear interpolation along source-segment chainage; no centreline smoothing or endpoint extrapolation',
        persistent_whitewater_runs=runs,
        el_trono_check=dict(osm_node_km=trono / 1000 if trono else None,
                            runs_containing=[r for r in runs if trono and r['osm_km'][0] * 1000 <= trono + 100 and r['osm_km'][1] * 1000 >= trono - 100]),
        gorafting_chainage=dict(el_trono_km=27.5, terminator_km=39.25, predicted_osm_km=(trono / 1000 + 39.25 - 27.5) if trono else None),
        named_location_accepted=False,
        conclusion='Persistent bright-water candidates for geographic review only. Approximate guide distances and spectral brightness do not establish a unique named rapid or its boundaries. Image-date discharge is unverified; clouds, bank brightness and other rapids require visual review.')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(dict(runs=runs, el_trono=report['el_trono_check'], predicted=report['gorafting_chainage']), indent=1))


if __name__ == '__main__':
    main()
