"""Evidence grid for the Futaleufu Terminator reach (numpy only).

Sources (archived in physics/data/real_world/futaleufu_river_chile/
futaleufu_sources_2026_09 and terrain/source): Sentinel-2 L2A 10 m mosaics
(2020-02-20, 2024-02-19, 2026-01-04), Copernicus GLO-30 (1 arc-second DSM,
EGM2008 heights; TanDEM-X 2011-2015 with water bodies edited flat and
monotonic), and the OSM centreline with chainage. Frame: UTM 18S
(EPSG:32718) metres.

The Terminator has no published coordinate. Its GoRafting chainage puts it
near OSM 74.2 km; the Sentinel-2 whitewater agrees (the largest persistent
whitewater between 66 and 80 km lies at 74.0-75.0 km on all three dates, and
the same test lights up at the OSM El Trono node).

What is measured and what is inferred:
- wetted extent: water (NDWI) or whitewater in at least two of the three
  Sentinel-2 dates, bilinear from 10 m to 1 m (measured, +-5 m edges);
- whitewater: bright neutral water pixels, mean over the dates (measured
  appearance; flows on the image dates unknown);
- water-surface anchors: the GLO-30 edited water surface along the midline
  (median of channel-interior cells per 50 m, forced non-increasing), every
  --anchor-spacing-m (measured with editing: TanDEM-X epoch, flow unknown,
  about +-2 m);
- surface between anchors: each drop spread by the whitewater share plus a
  small base weight (INFERRED);
- terrain: GLO-30 bicubic beyond --bank-blend-m of the water; the bank zone
  between is harmonic between the water edge (at the surface) and GLO-30
  (INFERRED shape). GLO-30 is a surface model: forest canopy is included;
- bed: discharge-consistent depth on a smooth section for --discharge-m3s
  (INFERRED; the planning flow is not the unknown image-date flow);
- submerged boulders at the upstream edges of whitewater patches (INFERRED);
  rocks and bars are not resolvable at 10 m and are left out.

Outputs (the Pacuare builder's layout, for build_curvilinear_river_scenario.py):
evidence_grid.npz, centreline.json, profile.json, boulders.json,
manifest.json and review PNGs.
"""
import argparse
import hashlib
import json
from collections import deque
from pathlib import Path

import numpy as np

from build_pacuare_evidence_grid import (arc_resample, box_mean, edt_inside, foam_boulders, gauss_smooth,
                                         harmonic_fill, pava_nonincreasing, project)
from geo_frames import tm_forward, tm_inverse, utm
from png_numpy import write_png
from tiff_numpy import read_geotiff

ROOT = Path(__file__).resolve().parents[2]
RIVER = ROOT / 'physics/data/real_world/futaleufu_river_chile'
SRC = RIVER / 'futaleufu_sources_2026_09'
DEM_TILES = [RIVER / 'terrain/source/copernicus_dem_glo30_S44_W073.tif', RIVER / 'terrain/source/copernicus_dem_glo30_S44_W072.tif']
UTM18S = utm(18, south=True)
G = 9.81


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_glo30():
    """Mosaic of the two 1x1 degree tiles (west first); pixel-is-point, 1 arc-second."""
    tiles = [read_geotiff(p) for p in DEM_TILES]
    (a, ma, _), (b, mb, _) = tiles
    assert ma['corner_utm_m'] == (-73.0, -43.0) and mb['corner_utm_m'] == (-72.0, -43.0)
    step = ma['cell_m'][0]
    # the tiles share their boundary column (pixel-is-point); drop the duplicate
    dem = np.hstack([a[:, :-1], b]).astype(np.float64) if a.shape[1] == 3601 else np.hstack([a, b]).astype(np.float64)
    return dem, -73.0, -43.0, step


def catmull_rom(grid, fr, fc):
    """Bicubic (Catmull-Rom) sample of grid at fractional row/col."""
    r0 = np.floor(fr).astype(int); c0 = np.floor(fc).astype(int)
    tr = fr - r0; tc = fc - c0

    def w(t):
        return [(-t ** 3 + 2 * t ** 2 - t) / 2, (3 * t ** 3 - 5 * t ** 2 + 2) / 2, (-3 * t ** 3 + 4 * t ** 2 + t) / 2, (t ** 3 - t ** 2) / 2]
    wr, wc = w(tr), w(tc)
    out = np.zeros(fr.shape)
    H, W = grid.shape
    for i in range(4):
        rr = np.clip(r0 - 1 + i, 0, H - 1)
        for j in range(4):
            out += wr[i] * wc[j] * grid[rr, np.clip(c0 - 1 + j, 0, W - 1)]
    return out


def bilinear(grid, fr, fc):
    H, W = grid.shape
    r0 = np.clip(np.floor(fr).astype(int), 0, H - 2); c0 = np.clip(np.floor(fc).astype(int), 0, W - 2)
    tr = np.clip(fr - r0, 0, 1); tc = np.clip(fc - c0, 0, 1)
    return (grid[r0, c0] * (1 - tr) * (1 - tc) + grid[r0, c0 + 1] * (1 - tr) * tc
            + grid[r0 + 1, c0] * tr * (1 - tc) + grid[r0 + 1, c0 + 1] * tr * tc)


def label_near(mask, seed):
    """Cells of mask 8-connected to any seed cell."""
    H, W = mask.shape
    out = np.zeros_like(mask)
    q = deque(zip(*np.nonzero(mask & seed)))
    for r, c in q:
        out[r, c] = True
    while q:
        r, c = q.popleft()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                r2, c2 = r + dr, c + dc
                if 0 <= r2 < H and 0 <= c2 < W and mask[r2, c2] and not out[r2, c2]:
                    out[r2, c2] = True; q.append((r2, c2))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--chain-m', type=float, nargs=2, default=(72900.0, 75300.0))
    ap.add_argument('--margin-m', type=float, default=350.0)
    ap.add_argument('--discharge-m3s', type=float, default=400.0)
    ap.add_argument('--n-pool', type=float, default=0.035)
    ap.add_argument('--n-rapid', type=float, default=0.05)
    ap.add_argument('--pool-weight', type=float, default=0.04)
    ap.add_argument('--min-slope', type=float, default=0.001)
    ap.add_argument('--anchor-spacing-m', type=float, default=200.0)
    ap.add_argument('--bank-blend-m', type=float, default=30.0)
    ap.add_argument('--boulder-crest-below-ws-m', type=float, default=0.4)
    ap.add_argument('--bed-correction', type=Path)
    ap.add_argument('--observed-rapids', type=Path,
                    help='observed-rapid catalogue (observed_rapid_features.py schema): its "rapids" (evidence station frame) '
                         'concentrate the fall between anchors like photographed whitewater, and may run supercritical')
    ap.add_argument('--rapid-depth-floor', type=float, default=0.7,
                    help='inside catalogued rapids the inferred depth may fall to this many critical depths (elsewhere 1)')
    ap.add_argument('--skip-anchor-stations', type=float, nargs='*', default=[],
                    help='drop these surface anchors (evidence stations) when they contradict an observed rapid position')
    args = ap.parse_args()
    out = args.out.resolve()
    assert not out.exists(), 'fresh output folder required'
    Q = args.discharge_m3s
    s0, s1 = args.chain_m

    # ---------------- OSM centreline (chainage) in UTM 18S
    cld = json.loads((SRC / 'osm/futaleufu_centreline.json').read_text(encoding='utf-8'))
    cl = np.array(cld['centreline_lon_lat_chain'])
    ext = (cl[:, 2] > s0 - 2000) & (cl[:, 2] < s1 + 2000)
    ox, oy = tm_forward(cl[ext, 0], cl[ext, 1], UTM18S); oc = cl[ext, 2]
    S = np.arange(oc[0], oc[-1], 4.0)
    X = gauss_smooth(np.interp(S, oc, ox), 3.0); Y = gauss_smooth(np.interp(S, oc, oy), 3.0)
    tx, ty = np.gradient(X), np.gradient(Y); tn = np.hypot(tx, ty)
    LX, LY = -ty / tn, tx / tn

    # ---------------- window (north up, 1 m) around the reach
    rs = (S >= s0) & (S <= s1)
    X0 = float(np.floor(X[rs].min() - args.margin_m)); X1 = float(np.ceil(X[rs].max() + args.margin_m))
    Y0 = float(np.floor(Y[rs].min() - args.margin_m)); Y1 = float(np.ceil(Y[rs].max() + args.margin_m))
    NX, NY = int(X1 - X0), int(Y1 - Y0)
    print(f'window {X0:.0f}-{X1:.0f} E, {Y0:.0f}-{Y1:.0f} N ({NX} x {NY} m)', flush=True)
    xc = X0 + np.arange(NX) + 0.5; yc = Y1 - np.arange(NY) - 0.5

    # ---------------- Sentinel-2: water / whitewater fractions on the 1 m grid
    fm = json.loads((SRC / 'sentinel2/fetch_manifest.json').read_text())
    wet_frac = np.zeros((NY, NX)); white_frac = np.zeros((NY, NX)); rgb = None
    dates = []
    for it in fm['items']:
        w = it['window_utm_m']; z = np.load(SRC / 'sentinel2' / it['npz'])
        refl = {k: z[k].astype(np.float32) * 1e-4 - 0.1 for k in ('blue', 'green', 'red', 'nir')}
        B, Gn, R, N = refl['blue'], refl['green'], refl['red'], refl['nir']
        ndwi = (Gn - N) / np.maximum(Gn + N, 1e-3)
        white = (B > 0.22) & (Gn > 0.22) & (R > 0.18) & (np.abs(B - R) < 0.12)
        water = (ndwi > 0.05) | white
        fc = (xc - w['xmin']) / 10.0 - 0.5; fr = (w['ymax'] - yc) / 10.0 - 0.5
        FR, FC = np.meshgrid(fr, fc, indexing='ij')
        wet_frac += bilinear(water.astype(np.float32), FR, FC)
        white_frac += bilinear(white.astype(np.float32), FR, FC)
        if it is fm['items'][-1]:
            rgb = np.stack([bilinear(np.clip(c / 0.25, 0, 1) ** (1 / 2.2), FR, FC) for c in (R, Gn, B)], -1)
            rgb = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
        dates.append(it['datetime'][:10])
        del FR, FC
    wet_frac /= len(fm['items']); white_frac /= len(fm['items'])

    # ---------------- midline from the wetted extent along OSM normals
    wet_any = wet_frac >= 0.5
    mids, widths, mS = [], [], []
    lat_s = np.arange(-150, 151, 1.0)
    for i in range(0, len(S), 2):
        px = X[i] + lat_s * LX[i]; py = Y[i] + lat_s * LY[i]
        c = np.floor(px - X0).astype(int); r = np.floor(Y1 - py).astype(int)
        ok = (c >= 0) & (c < NX) & (r >= 0) & (r < NY)
        if ok.sum() < len(lat_s) * 0.8:
            continue
        v = np.zeros(len(lat_s), bool); v[ok] = wet_any[r[ok], c[ok]]
        if not v.any():
            continue
        # wet runs; take the one containing / nearest the OSM line
        edges = np.flatnonzero(np.diff(np.r_[0, v.astype(int), 0]))
        runs = list(zip(edges[::2], edges[1::2] - 1))
        best = min(runs, key=lambda ab: 0 if lat_s[ab[0]] <= 0 <= lat_s[ab[1]] else min(abs(lat_s[ab[0]]), abs(lat_s[ab[1]])))
        if min(abs(lat_s[best[0]]), abs(lat_s[best[1]])) > 60 and not lat_s[best[0]] <= 0 <= lat_s[best[1]]:
            continue
        m = 0.5 * (lat_s[best[0]] + lat_s[best[1]])
        mids.append((X[i] + m * LX[i], Y[i] + m * LY[i])); widths.append(lat_s[best[1]] - lat_s[best[0]] + 1); mS.append(S[i])
    mids = np.array(mids)
    mx_, my_ = gauss_smooth(mids[:, 0], 6.0), gauss_smooth(mids[:, 1], 6.0)
    mxs, mys, _ = arc_resample(mx_, my_, 1.0)
    mxs, mys = gauss_smooth(mxs, 12.0), gauss_smooth(mys, 12.0)
    mxs, mys, _ = arc_resample(mxs, mys, 1.0)
    mchain = np.maximum.accumulate(project(mxs, mys, X, Y, S, LX, LY)[0])
    mS_osm = np.arange(len(mxs), dtype=float)
    mtx, mty = np.gradient(mxs), np.gradient(mys); mtn = np.hypot(mtx, mty)
    mLX, mLY = -mty / mtn, mtx / mtn
    M = len(mxs)

    # ---------------- station / lateral per cell (quad painting on the midline)
    CE, CN = np.meshgrid(xc, yc)
    st_grid = np.full((NY, NX), np.nan); lat_grid = np.full((NY, NX), np.nan)
    LMAX = 250.0
    # Nearest point on the midline, with each segment's foot clamped to its
    # ends. Projecting only onto segment interiors left a wedge with no
    # station outside every vertex (widest at the hairpins); those cells had
    # no water surface, kept raw GLO-30 heights and stood as pinnacles in the
    # river, and at hairpins a cell beside one limb took the other limb's
    # station 200 m away. The clamped foot (the vertex itself) covers the
    # wedge, and comparing true distances keeps each cell on its nearest limb.
    WEDGE_MARGIN = 60
    for i in range(M - 1):
        pts = np.array([[mxs[i] + a * mLX[i], mys[i] + a * mLY[i]] for a in (-LMAX, LMAX)] +
                       [[mxs[i + 1] + a * mLX[i + 1], mys[i + 1] + a * mLY[i + 1]] for a in (LMAX, -LMAX)])
        c0 = max(int(np.floor(pts[:, 0].min() - X0)) - WEDGE_MARGIN, 0)
        c1 = min(int(np.ceil(pts[:, 0].max() - X0)) + WEDGE_MARGIN, NX)
        r0 = max(int(np.floor(Y1 - pts[:, 1].max())) - WEDGE_MARGIN, 0)
        r1 = min(int(np.ceil(Y1 - pts[:, 1].min())) + WEDGE_MARGIN, NY)
        if c1 <= c0 or r1 <= r0:
            continue
        ex = CE[r0:r1, c0:c1]; ey = CN[r0:r1, c0:c1]
        a_ = (ex - mxs[i]) * mtx[i] / mtn[i] + (ey - mys[i]) * mty[i] / mtn[i]
        seglen = np.hypot(mxs[i + 1] - mxs[i], mys[i + 1] - mys[i])
        lat_ = (ex - mxs[i]) * mLX[i] + (ey - mys[i]) * mLY[i]
        a_c = np.clip(a_, 0.0, seglen)
        dist = np.hypot(ex - mxs[i] - a_c * mtx[i] / mtn[i], ey - mys[i] - a_c * mty[i] / mtn[i])
        lat_c = np.where(lat_ >= 0.0, dist, -dist)
        inq = dist <= LMAX
        sub_s = st_grid[r0:r1, c0:c1]; sub_l = lat_grid[r0:r1, c0:c1]
        closer = inq & (~np.isfinite(sub_l) | (dist < np.abs(sub_l)))
        sub_s[closer] = mS_osm[i] + a_c[closer] * (mS_osm[i + 1] - mS_osm[i]) / max(seglen, 1e-9)
        sub_l[closer] = lat_c[closer]
    del CE, CN

    # ---------------- river: wetted cells connected to the midline
    wet = wet_any & np.isfinite(lat_grid) & (np.abs(np.nan_to_num(lat_grid, nan=1e9)) < 150)
    seed = np.zeros((NY, NX), bool)
    mc = np.floor(mxs - X0).astype(int); mr = np.floor(Y1 - mys).astype(int)
    ok = (mc >= 0) & (mc < NX) & (mr >= 0) & (mr < NY)
    seed[mr[ok], mc[ok]] = True
    river = label_near(wet, seed)
    channel = river.copy()
    foam = river & (white_frac >= 0.3)
    rocks = np.zeros_like(river); bars = np.zeros_like(river)

    # ---------------- GLO-30 on the window and the edited water surface
    dem_g, lon0, lat0, step = load_glo30()
    rows_all = []
    glo = np.zeros((NY, NX))
    for r0 in range(0, NY, 256):
        CEb, CNb = np.meshgrid(xc, yc[r0:r0 + 256])
        lon, lat = tm_inverse(CEb, CNb, UTM18S)
        glo[r0:r0 + 256] = catmull_rom(dem_g, (lat0 - lat) / step, (lon - lon0) / step)
    del dem_g
    st_i = np.clip(np.round(np.nan_to_num(st_grid, nan=-1)).astype(int), -1, M - 1)
    interior = river & (edt_inside(river) >= 8)
    b50 = np.where(interior & (st_i >= 0), st_i // 50, -1)
    nb50 = M // 50 + 1
    h50 = np.full(nb50, np.nan); n50 = np.zeros(nb50)
    for k in range(nb50):
        v = glo[b50 == k]
        if len(v) >= 20:
            h50[k] = np.median(v); n50[k] = len(v)
    have = np.isfinite(h50)
    h_pava = np.full(nb50, np.nan)
    h_pava[have] = pava_nonincreasing(h50[have], n50[have])
    reach = (mchain >= s0) & (mchain <= s1)
    reach_idx = np.nonzero(reach)[0]
    a_st, a_z = [], []
    kstep = max(int(round(args.anchor_spacing_m / 50.0)), 1)
    k_lo = int(np.floor((reach_idx[0] - args.anchor_spacing_m) / 50.0))
    k_hi = int(np.ceil((reach_idx[-1] + args.anchor_spacing_m) / 50.0))
    for k in range(max(k_lo, 0), min(k_hi, nb50 - 1) + 1, kstep):
        if np.isfinite(h_pava[k]):
            a_st.append(k * 50.0 + 25.0); a_z.append(float(h_pava[k]))
    a_st, a_z = np.array(a_st), np.array(a_z)
    keep = np.r_[True, np.diff(a_z) < -0.05]
    a_st, a_z = a_st[keep], a_z[keep]
    skipped = [float(a) for a in a_st if any(abs(a - s) < 1.0 for s in args.skip_anchor_stations)]
    if skipped:
        keep = np.array([not any(abs(a - s) < 1.0 for s in args.skip_anchor_stations) for a in a_st])
        a_st, a_z = a_st[keep], a_z[keep]
    assert np.all(np.diff(a_z) < 0) and len(a_z) >= 3, 'anchors must fall downstream'

    # ---------------- surface between anchors: drops distributed by whitewater (inferred)
    wet_at = np.bincount(st_i[river & (st_i >= 0)], minlength=M).astype(float)
    foam_at = np.bincount(st_i[foam & (st_i >= 0)], minlength=M).astype(float)
    share = gauss_smooth(np.where(wet_at > 3, foam_at / np.maximum(wet_at, 1), 0.0), 6.0)
    # Observed rapids (outfitter, guidebook, video observations) that Sentinel-2's 10 m
    # pixels do not resolve concentrate the fall as its whitewater does: a class-weighted
    # share over each rapid's span, 10 m ramps (inferred, labelled).
    share_cat = np.zeros(M)
    rapids_used = []
    if args.observed_rapids:
        cat = json.loads(args.observed_rapids.read_text(encoding='utf-8'))
        assert str(cat.get('rapid_station_frame', cat.get('station_frame'))).startswith('evidence'),             'observed rapids must be in the evidence station frame'
        idx_m = np.arange(M, dtype=float)
        for r in cat.get('rapids', []):
            a0 = float(r['station_m']); a1 = a0 + float(r['length_m'])
            ramp = np.clip(np.minimum(idx_m - (a0 - 10.0), (a1 + 10.0) - idx_m) / 10.0, 0.0, 1.0)
            share_cat = np.maximum(share_cat, float(r['share']) * ramp)
            rapids_used.append(dict(id=r['id'], span_m=[a0, a1], share=float(r['share'])))
    share = np.maximum(share, share_cat)
    w = args.pool_weight + share
    ws_m = np.full(M, np.nan)
    for i in range(len(a_st) - 1):
        j0, j1 = int(round(a_st[i])), int(round(a_st[i + 1]))
        c = np.concatenate([[0.0], np.cumsum(w[j0:j1])])
        ws_m[j0:j1 + 1] = a_z[i] - (a_z[i] - a_z[i + 1]) * c / c[-1]
    fin = np.isfinite(ws_m)
    assert fin[reach_idx].all(), "reach must lie between two surface anchors"
    # outside the anchored span: the last anchor slope
    s_lo, s_hi = np.nonzero(fin)[0][[0, -1]]
    g_lo = (a_z[0] - a_z[1]) / (a_st[1] - a_st[0]); g_hi = (a_z[-2] - a_z[-1]) / (a_st[-1] - a_st[-2])
    idx = np.arange(M)
    ws_m = np.where(idx < s_lo, ws_m[s_lo] + g_lo * (s_lo - idx), ws_m)
    ws_m = np.where(idx > s_hi, ws_m[s_hi] - g_hi * (idx - s_hi), ws_m)
    ws_cell = np.where(np.isfinite(st_grid), ws_m[np.clip(st_i, 0, M - 1)], np.nan)

    # ---------------- terrain: GLO-30 beyond the bank zone, harmonic bank zone (inferred)
    dist_r = edt_inside(~river)
    far = dist_r >= args.bank_blend_m
    fixed = river | far | ~np.isfinite(ws_cell)
    fval = np.where(river, ws_cell, glo)
    dem = harmonic_fill(np.nan_to_num(fval), fixed)
    bank = ~fixed
    dem = np.where(bank, np.maximum(dem, np.nan_to_num(ws_cell) + 0.3 * np.clip(dist_r / 3.0, 0, 1)), dem)

    # ---------------- inferred bed: discharge-consistent depth on a smooth section
    e = edt_inside(river)
    s_bin = np.clip(st_i // 2, 0, None)
    nb = M // 2 + 1
    rv = river & (st_i >= 0)
    width = np.bincount(s_bin[rv], minlength=nb) / 2.0
    halfw = np.maximum(np.interp(np.arange(nb), np.nonzero(width > 0)[0], width[width > 0]) / 2.0, 1.0)
    fshape_all = np.zeros((NY, NX))
    fshape_all[rv] = np.sqrt(np.clip(e[rv] / halfw[s_bin[rv]], 0.02, 1.0))
    sum_f53 = np.bincount(s_bin[rv], weights=fshape_all[rv] ** (5 / 3), minlength=nb)
    wsb = ws_m[np.clip(np.arange(nb) * 2, 0, M - 1)]
    slope = np.clip(-np.gradient(gauss_smooth(wsb, 5.0), 2.0), args.min_slope, None)
    sh_b = share[np.clip(np.arange(nb) * 2, 0, M - 1)]
    nman = args.n_pool + (args.n_rapid - args.n_pool) * np.clip((sh_b - 0.05) / 0.20, 0, 1)
    have = sum_f53 > 0
    Hn = np.full(nb, np.nan)
    Hn[have] = (Q * nman[have] * 2.0 / (np.sqrt(slope[have]) * sum_f53[have])) ** 0.6
    hc = ((Q / np.maximum(width, 1.0)) ** 2 / G) ** (1 / 3)
    mean_f = np.where(have, np.bincount(s_bin[rv], weights=fshape_all[rv], minlength=nb) / np.maximum(np.bincount(s_bin[rv], minlength=nb), 1), 1.0)
    floor = 1.0 / np.maximum(mean_f, 0.3)
    in_rapid = share_cat[np.clip(np.arange(nb) * 2, 0, M - 1)] >= 0.1
    floor = np.where(in_rapid, args.rapid_depth_floor * floor, floor)
    Hn = np.where(have, np.maximum(Hn, hc * floor), np.nan)
    Hn = gauss_smooth(np.interp(np.arange(nb), np.nonzero(have)[0], Hn[have]), 3.0)
    corr = np.load(args.bed_correction) if args.bed_correction else None
    bed = dem.copy()
    cls = np.zeros((NY, NX), np.uint8)
    bed_rv = ws_cell[rv] - np.maximum(Hn[s_bin[rv]] * fshape_all[rv], 0.05)
    if corr is not None:
        bed_rv = np.minimum(bed_rv + np.interp(st_grid[rv], corr['station'], corr['delta']), ws_cell[rv] - 0.05)
    bed[rv] = bed_rv; cls[rv] = 2
    ws_grid = np.where(rv, ws_cell, np.nan)
    bed, cls, boulders = foam_boulders(bed, cls, foam, rocks, ws_grid, st_grid, mxs, mys, X0, Y1, args.boulder_crest_below_ws_m)

    # ---------------- outputs
    out.mkdir(parents=True)
    station_grid = np.where(rv, st_grid, np.nan).astype(np.float32)
    np.savez_compressed(out / 'evidence_grid.npz', bed=bed.astype(np.float32), dem2021=dem.astype(np.float32), dem=dem.astype(np.float32),
                        glo30=glo.astype(np.float32), bathy2014=np.full((NY, NX), np.nan, np.float32), class_code=cls, river=river,
                        channel=channel, foam=foam, rocks=rocks, bars=bars, station=station_grid, lateral=lat_grid.astype(np.float32),
                        ws=np.where(channel, ws_cell, np.nan).astype(np.float32), wet_fraction=wet_frac.astype(np.float32),
                        white_fraction=white_frac.astype(np.float32))
    np.savez_compressed(out / 'sentinel2_rgb.npz', rgb=rgb)
    sel = (mS_osm >= reach_idx[0] - 400) & (mS_osm <= reach_idx[-1] + 400)
    (out / 'centreline.json').write_text(json.dumps(dict(
        schema='raftsim.futaleufu.terminator_midline.v1', crs='EPSG:32718 WGS 84 / UTM zone 18S',
        method='midline of the Sentinel-2 wetted extent along OSM normals (Gaussian sigma 12 m), 1 m arc length; '
               'station = midline arc length from its upstream start',
        reach_station_m=[float(reach_idx[0]), float(reach_idx[-1])],
        points_xy_station=[[float(a), float(b_), float(c)] for a, b_, c in zip(mxs[sel][::2], mys[sel][::2], mS_osm[sel][::2])],
        osm_chain_m=[float(v) for v in mchain[sel][::2]])) + '\n')
    centers = np.arange(nb) * 2.0
    (out / 'profile.json').write_text(json.dumps(dict(
        station_center_m=centers.tolist(), ws_reference_m=wsb.tolist(), ws_reference_method='glo30_edited_water_surface_whitewater_weighted',
        anchors=[dict(station_m=float(s_), osm_chain_m=float(np.interp(s_, mS_osm, mchain)), elevation_m=float(z_)) for s_, z_ in zip(a_st, a_z)],
        glo30_water_surface_50m=[[k * 50.0 + 25.0, float(h50[k]), float(h_pava[k])] for k in range(nb50) if np.isfinite(h50[k])],
        whitewater_share=[float(v) for v in share[::2]], slope=slope.tolist(), normal_depth_m=Hn.tolist(), manning_n=nman.tolist(),
        wetted_width_m=width.tolist())) + '\n')
    (out / 'boulders.json').write_text(json.dumps(dict(
        schema='raftsim.futaleufu.inferred_boulders.v1', inferred=True, crest_below_ws_m=args.boulder_crest_below_ws_m,
        method='one boulder per lateral cluster of the upstream edge of each >= 4 m2 Sentinel-2 whitewater patch (10 m imagery, '
               'bilinear to 1 m) over inferred bed, shifted upstream by its radius; crest at the surface minus the margin',
        boulders=boulders, emergent_rocks=[]), indent=1) + '\n')
    inreach = rv & (station_grid >= reach_idx[0]) & (station_grid <= reach_idx[-1])
    stats = dict(window=dict(x0=X0, y_top=Y1, nx=NX, ny=NY), channel_cells=int(channel.sum()), wetted_cells=int(river.sum()),
                 whitewater_cells=int(foam.sum()), emergent_rock_cells=0, bar_cells=0,
                 reach_station_m=[float(reach_idx[0]), float(reach_idx[-1])],
                 reach_osm_chain_m=[float(mchain[reach_idx[0]]), float(mchain[reach_idx[-1]])],
                 ws_reach_m=[float(ws_m[reach_idx[0]]), float(ws_m[reach_idx[-1]])],
                 anchors=[(float(s_), float(z_)) for s_, z_ in zip(a_st, a_z)],
                 inferred_depth_m_p10_p50_p90=np.percentile((ws_cell - bed)[inreach & (cls == 2)], [10, 50, 90]).tolist(),
                 wetted_width_reach_m_p10_p50_p90=np.percentile(width[reach_idx[0] // 2:reach_idx[-1] // 2], [10, 50, 90]).tolist(),
                 foam_boulders=len(boulders), emergent_rocks=0, sentinel2_dates=dates)
    manifest = dict(
        schema='raftsim.futaleufu.terminator_evidence_grid.v1', crs='EPSG:32718 WGS 84 / UTM zone 18S',
        vertical='EGM2008 orthometric metres (Copernicus GLO-30)',
        grid=dict(x0=X0, y_top=Y1, nx=NX, ny=NY, cell_m=1.0),
        inputs=dict(sentinel2={it['npz']: it['npz_sha256'] for it in fm['items']},
                    glo30={p.name: sha(p) for p in DEM_TILES},
                    centreline=dict(path=str((SRC / 'osm/futaleufu_centreline.json').relative_to(ROOT).as_posix()),
                                    sha256=sha(SRC / 'osm/futaleufu_centreline.json'))),
        sources_manifest_sha256=sha(SRC / 'manifest.json'),
        class_codes={'0': 'dry ground: Copernicus GLO-30 (measured surface model, includes forest canopy) beyond the bank zone; '
                              'bank zone harmonic between the water edge and GLO-30 (inferred shape)',
                     '2': 'bed: discharge-consistent depth for the planning discharge (inferred)',
                     '4': 'submerged boulder: location from Sentinel-2 whitewater, height from a pour-over assumption (inferred)'},
        parameters=dict(discharge_m3s=Q, discharge_source='existing high_runnable planning band (not measured; DGA records not downloaded)',
                        n_pool=args.n_pool, n_rapid=args.n_rapid, pool_weight=args.pool_weight, min_slope=args.min_slope,
                        anchor_spacing_m=args.anchor_spacing_m, bank_blend_m=args.bank_blend_m, chain_m=list(args.chain_m),
                        margin_m=args.margin_m, boulder_crest_below_ws_m=args.boulder_crest_below_ws_m,
                        station_projection='nearest point on the midline (segment feet clamped to their ends)',
                        bed_correction=None if corr is None else args.bed_correction.resolve().relative_to(ROOT).as_posix(),
                        bed_correction_sha256=None if corr is None else sha(args.bed_correction),
                        observed_rapids=None if not args.observed_rapids else args.observed_rapids.resolve().relative_to(ROOT).as_posix(),
                        observed_rapids_sha256=None if not args.observed_rapids else sha(args.observed_rapids),
                        rapid_depth_floor_critical_depths=args.rapid_depth_floor if args.observed_rapids else None,
                        rapids=rapids_used, skipped_anchor_stations_m=skipped),
        statistics=stats, inferred=True, accepted=False)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')

    # review: Sentinel-2 colour with the wetted extent, whitewater and boulders
    img = rgb.copy()
    img[river & ~foam] = (img[river & ~foam] * 0.5 + np.array([0, 40, 120]) * 0.5).astype(np.uint8)
    img[foam] = (255, 255, 255)
    img[cls == 4] = (230, 60, 60)
    write_png(out / 'classes.png', img[::2, ::2])
    depth = np.where(river, ws_cell - bed, np.nan)
    dimg = np.clip(np.nan_to_num(depth) / 8.0, 0, 1)
    shade = np.clip((dem - np.nanmin(dem)) / max(np.nanmax(dem) - np.nanmin(dem), 1e-6), 0, 1)
    rgbd = np.stack([shade * 200, shade * 200, shade * 200], -1)
    rgbd[river] = np.stack([20 + 0 * dimg, 60 + 120 * (1 - dimg), 120 + 135 * dimg], -1)[river]
    write_png(out / 'terrain_depth.png', rgbd[::2, ::2].astype(np.uint8))
    print(json.dumps(stats, indent=1))


if __name__ == '__main__':
    main()
