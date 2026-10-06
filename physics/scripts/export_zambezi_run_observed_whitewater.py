"""Observed whitewater for the 30 km Zambezi reference run (L_Zambezi), as a render-only layer (numpy only).

    export_zambezi_run_observed_whitewater.py <catalogue.json> [--row-m 2] [--column-m 4] [--preview out.png]

The reference run's water is a procedural seed (scenario_zambezi_run: a 5 m x 10 m
curved field with one bounded hydraulic jump per rapid), not a cook. Its jumps
break weakly, so in play most of the 25 rapids showed little whitewater. This
writes the rapids' expected whitewater from an observed-rapid catalogue
(outfitter, guidebook, trip report and video observations, with the Sentinel-2
whitewater runs used to set spans) as the curved-map observed-whitewater layer
the runtime already reads (LoadObservedWhitewaterFieldFromFile, RSBF v1, rows
along station, columns along lateral, energy = whitewater fraction). Built with
export_cartesian_observed_whitewater.catalogue_whitewater: broken water across
each rapid by class, a white core behind every hole and pour-over, crest caps
along wave trains and bands along laterals and diagonals, all feathered.

The catalogue is in the scenario frame (the run's curved station and lateral,
lateral positive to river left). The layer is written beside the procedural
field as observed_whitewater_normal_big_water.bin with a sidecar JSON; the
procedural field and its manifest are not changed. Appearance evidence only:
it floors the displayed foam and never reaches forces, contact or gameplay.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np

from export_cartesian_observed_whitewater import catalogue_whitewater
from png_numpy import write_png

ROOT = Path(__file__).resolve().parents[2]
COOKED = ROOT / 'physics/data/real_world/zambezi_batoka_gorge/scenario_zambezi_run/runtime/cooked_flow_fields'
BAND = 'normal_big_water'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_rsbf(path, stations, lat0, dlat, elev, frac, wet):
    tmp = str(path) + '.tmp'
    with open(tmp, 'wb') as fb:
        fb.write(struct.pack('<IIiiff', 0x52534246, 1, elev.shape[1], elev.shape[0], float(lat0), float(dlat)))
        for arr, fmt in ((stations, '<f4'), (elev, '<f4'), (frac, '<f4'), (wet, 'u1')):
            flat = np.ascontiguousarray(arr).astype(fmt).ravel()
            fb.write(struct.pack('<i', flat.size)); fb.write(flat.tobytes())
    Path(tmp).replace(path)


def bilinear(field, x0, dx, y0, dy, st, lat):
    """Sample a (ny, nx) field at station st (x) and lateral lat (y), clamped."""
    ny, nx = field.shape
    fx = np.clip((st - x0) / dx, 0, nx - 1.000001); fy = np.clip((lat - y0) / dy, 0, ny - 1.000001)
    i = np.floor(fx).astype(int); j = np.floor(fy).astype(int); a = fx - i; b = fy - j
    return ((1 - a) * (1 - b) * field[j, i] + a * (1 - b) * field[j, i + 1]
            + (1 - a) * b * field[j + 1, i] + a * b * field[j + 1, i + 1])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('catalogue', type=Path)
    ap.add_argument('--row-m', type=float, default=2.0)
    ap.add_argument('--column-m', type=float, default=4.0)
    ap.add_argument('--preview', type=Path)
    ap.add_argument('--core-half-width-m', type=float, default=18.0,
                    help='half-width of the low-water river that each rapid\'s broken water fills')
    ap.add_argument('--core-feather-m', type=float, default=16.0)
    args = ap.parse_args()
    manifest = json.loads((COOKED / 'manifest.json').read_text())
    g = manifest['grid']
    wet_mask = np.load(COOKED / 'wet_mask.npy').astype(float)
    surface = np.load(COOKED / 'bed.npy').astype(float) + np.load(COOKED / 'h.npy').astype(float)
    cat = json.loads(args.catalogue.read_text(encoding='utf-8'))
    assert cat.get('station_frame') == 'scenario', 'the catalogue must be in the run (scenario) frame'
    x_end = g['origin_x_m'] + (g['nx'] - 1) * g['dx_m']
    y0 = g['origin_y_m']; y1 = y0 + (g['ny'] - 1) * g['dy_m']
    stations = np.arange(g['origin_x_m'], x_end + 0.5 * args.row_m, args.row_m)
    lats = np.arange(y0, y1 + 0.5 * args.column_m, args.column_m)
    assert len(lats) <= 512 and len(stations) <= 200000
    ST, LAT = np.meshgrid(stations, lats, indexing='ij')
    wet_f = bilinear(wet_mask, g['origin_x_m'], g['dx_m'], y0, g['dy_m'], ST, LAT)
    # A layer corner that reads dry makes the runtime sample nothing, so keep
    # the layer wet half a solver cell beyond the procedural wet edge; the
    # carrier only samples it at wet vertices anyway.
    wet = wet_f > 0.0
    inside = wet_f >= 0.5
    elev = bilinear(surface, g['origin_x_m'], g['dx_m'], y0, g['dy_m'], ST, LAT)
    # The procedural channel is ~144 m wide everywhere; the low-water river is
    # 30-60 m. Each rapid's broken water (by class) is confined to that
    # central width with feathered edges, so the margins read as eddies and
    # boils; the observed holes, waves and laterals keep their own footprints.
    broken = catalogue_whitewater(ST, LAT, inside, dict(rapids=cat.get('rapids', []), features=[]))
    features = catalogue_whitewater(ST, LAT, inside, dict(rapids=[], features=cat.get('features', [])))
    t = np.clip((np.abs(LAT) - args.core_half_width_m) / max(args.core_feather_m, 1e-6), 0.0, 1.0)
    envelope = 1.0 - t * t * (3.0 - 2.0 * t)
    frac = np.maximum(broken * envelope, features)
    frac = np.where(inside, np.clip(frac, 0.0, 1.0), 0.0)
    out = COOKED / f'observed_whitewater_{BAND}.bin'
    write_rsbf(out, stations.astype(np.float32), float(lats[0]), args.column_m, elev.astype(np.float32),
               frac.astype(np.float32), wet.astype(np.uint8))
    per_rapid = []
    for r in cat.get('rapids', []):
        sel = (ST >= r['station_m']) & (ST <= r['station_m'] + r['length_m']) & inside
        core = sel & (np.abs(LAT) <= args.core_half_width_m)
        per_rapid.append(dict(id=r['id'], station_m=r['station_m'], length_m=r['length_m'],
                              mean_whitewater=round(float(frac[core].mean()), 4) if core.any() else 0.0,
                              mean_whitewater_full_width=round(float(frac[sel].mean()), 4) if sel.any() else 0.0,
                              cells_over_half=int((frac[sel] > 0.5).sum())))
    side = dict(
        schema='raftsim.curved_observed_whitewater.v1',
        generator='physics/scripts/export_zambezi_run_observed_whitewater.py',
        file=out.name, sha256=sha(out),
        layout='RSBF v1: rows = run station, columns = lateral (positive river left) from the lateral origin at the column '
               'spacing; elevation = procedural water surface; energy = whitewater fraction 0-1; wet = procedural wet mask '
               'dilated half a solver cell',
        frame='scenario_zambezi_run curved coordinates (river_coordinate_map.json)',
        row_m=args.row_m, column_m=args.column_m, rows=len(stations), columns=len(lats), lateral_origin_m=float(lats[0]),
        broken_water_core=dict(half_width_m=args.core_half_width_m, feather_m=args.core_feather_m,
                               note='rapid broken water confined to the low-water river width (30-60 m observed) inside the '
                                    '~144 m procedural channel; feature footprints are not confined'),
        procedural_field=dict(manifest='manifest.json', manifest_sha256=sha(COOKED / 'manifest.json')),
        catalogue=dict(path=args.catalogue.resolve().relative_to(ROOT).as_posix(), sha256=sha(args.catalogue),
                       rapids=len(cat.get('rapids', [])), features=len(cat.get('features', []))),
        cells_with_whitewater=int((frac > 0.05).sum()), per_rapid=per_rapid,
        render_only=True,
        note='appearance evidence: floors the displayed foam; never reaches forces, contact or gameplay. The procedural '
             'field (bed, h, u, v) is unchanged.')
    (COOKED / f'observed_whitewater_{BAND}.json').write_text(json.dumps(side, indent=1) + '\n')
    if args.preview:
        # station runs left to right, compressed 4:1 so 30 km fits
        k = 4
        v = frac[::k].T; w = wet[::k].T
        img = np.zeros(v.shape + (3,), np.uint8); img[..., 2] = np.where(w, 110, 0)
        img = (img * (1 - v[..., None]) + 255 * v[..., None]).astype(np.uint8)
        write_png(args.preview, img[::-1])
    print(json.dumps(dict(rows=len(stations), columns=len(lats), cells_with_whitewater=side['cells_with_whitewater'],
                          rapids=[(p['id'], p['mean_whitewater']) for p in per_rapid]), indent=1))


if __name__ == '__main__':
    main()
