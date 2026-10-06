"""Evidence grid for the Pacuare Huacas-Pinball reach (numpy only).

Sources (physics/data/real_world/pacuare_river_costa_rica/huacas_sources_2026_09,
extracted by the caller): IGN Costa Rica 1:5,000 contours (10 m) and river-bank
lines (hydrography D01), the 2014-2017 1:5,000 orthophoto (WMTS z18 mosaic,
~1 m effective), and the OSM centreline with chainage. Frame: CRTM05
(EPSG:5367) metres; heights are IGN orthometric metres.

What is measured and what is inferred:
- banks / wetted extent: IGN bank lines (compiled from the same photographs);
- terrain: harmonic interpolation between the 10 m contours, with the water
  edge held at the water surface (interpolation between measured contours);
- water-surface anchors: a contour at level L runs beside the river only where
  the water is below L, so the upstream-most station where an L contour comes
  within a few metres of a bank is where the surface crosses L (measured; the
  crossing stations are stable for 8-25 m bank distances);
- surface between anchors: each 10 m drop is distributed along the reach by
  the orthophoto whitewater share plus a small base slope (INFERRED: rapids
  steep, pools flat);
- bed: discharge-consistent depth for the planning discharge (not measured;
  no gauge) on a parabolic section (INFERRED);
- emergent rocks: orthophoto rock pixels inside the channel, tops at the water
  surface plus a size-scaled height (location measured, height INFERRED);
- submerged boulders: upstream edges of whitewater patches, crest below the
  surface (INFERRED, as for Hance).

Outputs (Hance-compatible, for build_curvilinear_river_scenario.py):
evidence_grid.npz (bed, dem, class_code, river, channel, foam, rocks, station,
lateral), centreline.json, profile.json, boulders.json, manifest.json and
review PNGs.
"""
import argparse
import hashlib
import json
from collections import deque
from pathlib import Path

import numpy as np

from geo_frames import CRTM05, lonlat_to_merc, tm_forward, tm_inverse
from png_numpy import write_png

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'physics/data/real_world/pacuare_river_costa_rica/huacas_sources_2026_09'
G = 9.81


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def densify(p, step):
    seg = np.diff(p, axis=0)
    n = np.maximum(np.ceil(np.hypot(*seg.T) / step), 1).astype(int)
    parts = [a + np.linspace(0, 1, k, endpoint=False)[:, None] * s for a, s, k in zip(p[:-1], seg, n)]
    return np.vstack(parts + [p[-1:]])


def gauss_smooth(v, sigma):
    r = int(np.ceil(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    return np.convolve(np.pad(v, r, mode='edge'), k, mode='valid')


def arc_resample(x, y, step):
    s = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(x), np.diff(y)))])
    t = np.arange(0.0, s[-1], step)
    return np.interp(t, s, x), np.interp(t, s, y), t


def project(px, py, X, Y, S, LX, LY):
    """Nearest centreline sample: station and signed lateral (river-left positive)."""
    out_s = np.empty(len(px)); out_l = np.empty(len(px))
    for k in range(0, len(px), 1024):
        d2 = (px[k:k + 1024, None] - X[None]) ** 2 + (py[k:k + 1024, None] - Y[None]) ** 2
        j = d2.argmin(1)
        out_s[k:k + 1024] = S[j]
        out_l[k:k + 1024] = (px[k:k + 1024] - X[j]) * LX[j] + (py[k:k + 1024] - Y[j]) * LY[j]
    return out_s, out_l


def pava_nonincreasing(y, w):
    """Weighted isotonic (non-increasing) regression."""
    vals, wts, cnt = [], [], []
    for yi, wi in zip(y, w):
        vals.append(yi); wts.append(wi); cnt.append(1)
        while len(vals) > 1 and vals[-2] < vals[-1]:
            v = (vals[-2] * wts[-2] + vals[-1] * wts[-1]) / (wts[-2] + wts[-1])
            vals[-2:] = [v]; wts[-2:] = [wts[-2] + wts[-1]]; cnt[-2:] = [cnt[-2] + cnt[-1]]
    return np.repeat(vals, cnt)


def harmonic_fill(fixed_val, fixed, tol_m=1e-4, max_iter=8000):
    """Laplace interpolation with fixed (Dirichlet) cells and reflecting borders:
    coarse-to-fine Jacobi start, then conjugate gradients to convergence
    (Jacobi alone left terraces: flat benches between contour lines)."""
    x0 = harmonic_start(fixed_val, fixed)
    free = ~fixed
    F = np.where(fixed, fixed_val, 0.0)

    def nsum(a):
        p = np.pad(a, 1, mode='edge')
        return p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]

    def A(u):
        return np.where(free, 4.0 * u - nsum(u), 0.0)
    b = np.where(free, nsum(F), 0.0)
    x = np.where(free, x0, 0.0)
    r = b - A(x); p = r.copy(); rs = float((r * r).sum())
    target = tol_m * tol_m * max(int(free.sum()), 1)  # RMS residual per free cell, metres
    it = 0
    for it in range(max_iter):
        Ap = A(p); alpha = rs / max(float((p * Ap).sum()), 1e-30)
        x += alpha * p; r -= alpha * Ap
        rs_new = float((r * r).sum())
        if rs_new < target:
            break
        p = r + (rs_new / rs) * p; rs = rs_new
    print(f'harmonic CG: {it + 1} iterations, RMS residual {np.sqrt(rs_new / max(int(free.sum()), 1)):.2e} m', flush=True)
    return np.where(fixed, fixed_val, x)


def harmonic_start(fixed_val, fixed, levels=(16, 8, 4, 2), iters=(400, 300, 200, 100)):
    """Coarse-to-fine Jacobi (block means as coarse constraints): a start for CG."""
    H, W = fixed.shape
    sol = None
    for lev, it in zip(levels, iters):
        Hc, Wc = -(-H // lev), -(-W // lev)
        pv = np.zeros((Hc * lev, Wc * lev)); pf = np.zeros_like(pv)
        pv[:H, :W] = np.where(fixed, fixed_val, 0.0); pf[:H, :W] = fixed
        cnt = pf.reshape(Hc, lev, Wc, lev).sum((1, 3))
        cval = np.where(cnt > 0, pv.reshape(Hc, lev, Wc, lev).sum((1, 3)) / np.maximum(cnt, 1), 0.0)
        cfix = cnt > 0
        if sol is None:
            cur = np.full((Hc, Wc), cval[cfix].mean())
        else:
            ph, pw = sol.shape
            cur = np.repeat(np.repeat(sol, 2, 0), 2, 1)[:Hc, :Wc]
            if cur.shape != (Hc, Wc):
                cur = np.pad(cur, ((0, Hc - cur.shape[0]), (0, Wc - cur.shape[1])), mode='edge')
        cur = np.where(cfix, cval, cur)
        for _ in range(it):
            p = np.pad(cur, 1, mode='edge')
            cur = np.where(cfix, cval, 0.25 * (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]))
        sol = cur
    last = levels[-1]
    return np.repeat(np.repeat(sol, last, 0), last, 1)[:H, :W]


def components(mask):
    H, W = mask.shape
    lab = -np.ones((H, W), int); comps = []
    for r0, c0 in zip(*np.nonzero(mask)):
        if lab[r0, c0] >= 0:
            continue
        q = deque([(r0, c0)]); lab[r0, c0] = len(comps); pix = []
        while q:
            r, c = q.popleft(); pix.append((r, c))
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    r2, c2 = r + dr, c + dc
                    if 0 <= r2 < H and 0 <= c2 < W and mask[r2, c2] and lab[r2, c2] < 0:
                        lab[r2, c2] = len(comps); q.append((r2, c2))
        comps.append(np.array(pix))
    return comps, lab


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--contours', type=Path, required=True)
    ap.add_argument('--hydrography', type=Path, required=True)
    ap.add_argument('--centreline', type=Path, required=True, help='OSM centreline JSON (extract_osm_river_centreline.py)')
    ap.add_argument('--ortho', type=Path, required=True, help='WMTS mosaic npz (fetch_wmts_corridor.py)')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--chain-m', type=float, nargs=2, default=(81950.0, 84450.0))
    ap.add_argument('--margin-m', type=float, default=330.0)
    ap.add_argument('--discharge-m3s', type=float, default=45.0)
    ap.add_argument('--n-pool', type=float, default=0.035)
    ap.add_argument('--n-rapid', type=float, default=0.05)
    ap.add_argument('--pool-weight', type=float, default=0.04,
                    help='weight of a whitewater-free metre when distributing each 10 m drop (a metre with whitewater share f weighs this + f)')
    ap.add_argument('--min-slope', type=float, default=0.0008, help='slope floor for the normal-depth estimate')
    ap.add_argument('--anchor-bank-distance-m', type=float, default=10.0)
    ap.add_argument('--bar-top-m', type=float, default=0.6, help='gravel bar crest above the surface (inferred)')
    ap.add_argument('--bar-ramp-m', type=float, default=6.0, help='distance over which bars rise from +0.1 m to the crest')
    ap.add_argument('--boulder-crest-below-ws-m', type=float, default=0.25)
    ap.add_argument('--bed-correction', type=Path)
    args = ap.parse_args()
    out = args.out.resolve()
    assert not out.exists(), 'fresh output folder required'
    Q = args.discharge_m3s

    # ---------------- centreline (OSM, chainage) in CRTM05
    cld = json.loads(args.centreline.read_text(encoding='utf-8'))
    cl = np.array(cld['centreline_lon_lat_chain'])
    s0, s1 = args.chain_m
    ext = (cl[:, 2] > s0 - 3000) & (cl[:, 2] < s1 + 3000)
    ox, oy = tm_forward(cl[ext, 0], cl[ext, 1], CRTM05); oc = cl[ext, 2]
    S = np.arange(oc[0], oc[-1], 2.0)
    X = np.interp(S, oc, ox); Y = np.interp(S, oc, oy)
    tx, ty = np.gradient(X), np.gradient(Y); tn = np.hypot(tx, ty)
    LX, LY = -ty / tn, tx / tn

    # ---------------- IGN bank lines along the river
    hyd = json.loads(args.hydrography.read_text(encoding='utf-8'))['features']
    bank, bank_id = [], []
    for f in hyd:
        if f['properties']['layer'] != 'D01':
            continue
        p = np.array(f['geometry']['coordinates'])[:, :2]
        ps, pl = project(p[:, 0], p[:, 1], X, Y, S, LX, LY)
        near = np.abs(pl) < 80
        if near.mean() > 0.6 and np.ptp(ps[near]) > 100:
            d = densify(p, 1.0)
            bank.append(d); bank_id.append(np.full(len(d), len(bank_id)))
    bank = np.vstack(bank); bank_id = np.concatenate(bank_id)
    # Midline from the banks alone (the OSM line leaves the channel in
    # places): pair each bank point with the nearest point of a different
    # bank line 4-150 m away, take the midpoints, and their median per 6 m of
    # OSM chainage (OSM only orders them).
    sub = bank[::2]; sid = bank_id[::2]
    tan = np.zeros_like(sub)
    for u in np.unique(sid):
        m_ = sid == u
        if m_.sum() > 1:
            tan[m_] = np.gradient(sub[m_], axis=0)
    tan /= np.maximum(np.hypot(tan[:, 0], tan[:, 1]), 1e-9)[:, None]
    mids = []
    for k in range(0, len(sub), 256):
        dx = sub[None, :, 0] - sub[k:k + 256, None, 0]; dy = sub[None, :, 1] - sub[k:k + 256, None, 1]
        d = np.hypot(dx, dy)
        # partner on another line, across the channel (pair vector near-normal to this bank)
        cosang = np.abs(dx * tan[k:k + 256, None, 0] + dy * tan[k:k + 256, None, 1]) / np.maximum(d, 1e-9)
        d[(sid[k:k + 256, None] == sid[None, :]) | (d < 4) | (cosang > 0.5)] = np.inf
        j = d.argmin(1); dj = d[np.arange(len(j)), j]
        ok = dj < 150
        mids.append(0.5 * (sub[k:k + 256][ok] + sub[j[ok]]))
    mids = np.vstack(mids)
    ms_, _ = project(mids[:, 0], mids[:, 1], X, Y, S, LX, LY)
    bins = np.floor(ms_ / 6.0).astype(int)
    ub = np.unique(bins)
    cxm = np.array([np.median(mids[bins == u, 0]) for u in ub]); cym = np.array([np.median(mids[bins == u, 1]) for u in ub])
    order = np.argsort(ub)
    mx_, my_ = gauss_smooth(cxm[order], 2.0), gauss_smooth(cym[order], 2.0)
    mxs, mys, _ = arc_resample(mx_, my_, 1.0)
    mxs, mys = gauss_smooth(mxs, 12.0), gauss_smooth(mys, 12.0)
    mxs, mys, _ = arc_resample(mxs, mys, 1.0)
    # OSM chainage of each midline sample, forced monotonic (the OSM line
    # wanders onto the banks); stations below are midline arc length.
    mchain = np.maximum.accumulate(project(mxs, mys, X, Y, S, LX, LY)[0])
    mS_osm = np.arange(len(mxs), dtype=float)
    mtx, mty = np.gradient(mxs), np.gradient(mys); mtn = np.hypot(mtx, mty)
    mLX, mLY = -mty / mtn, mtx / mtn
    # bank offsets in the midline frame
    ms_b, ml_b = project(bank[:, 0], bank[:, 1], mxs, mys, mS_osm, mLX, mLY)
    M = len(mxs)
    mleft = np.full(M, np.nan); mright = np.full(M, np.nan)
    bidx = np.clip(np.round(np.interp(ms_b, mS_osm, np.arange(M))).astype(int), 0, M - 1)
    for i in range(M):
        m = np.abs(bidx - i) <= 2
        lp = ml_b[m & (ml_b > 0) & (ml_b < 90)]; rp = ml_b[m & (ml_b < 0) & (ml_b > -90)]
        if len(lp): mleft[i] = lp.min()
        if len(rp): mright[i] = rp.max()
    gd = np.isfinite(mleft) & np.isfinite(mright)
    mleft = gauss_smooth(np.interp(np.arange(M), np.nonzero(gd)[0], mleft[gd]), 2.0)
    mright = gauss_smooth(np.interp(np.arange(M), np.nonzero(gd)[0], mright[gd]), 2.0)

    # ---------------- window (north up, 1 m)
    reach = (mchain >= s0) & (mchain <= s1)
    rx, ry = mxs[reach], mys[reach]
    X0 = float(np.floor(rx.min() - args.margin_m)); X1 = float(np.ceil(rx.max() + args.margin_m))
    Y0 = float(np.floor(ry.min() - args.margin_m)); Y1 = float(np.ceil(ry.max() + args.margin_m))
    NX, NY = int(X1 - X0), int(Y1 - Y0)
    CE, CN = np.meshgrid(X0 + np.arange(NX) + 0.5, Y1 - np.arange(NY) - 0.5)
    print(f'window {X0:.0f}-{X1:.0f} E, {Y0:.0f}-{Y1:.0f} N ({NX} x {NY} m)', flush=True)

    # ---------------- station / lateral for every cell near the river (quad painting on the midline)
    st_grid = np.full((NY, NX), np.nan); lat_grid = np.full((NY, NX), np.nan)
    LMAX = 160.0
    for i in range(M - 1):
        pts = np.array([[mxs[i] + a * mLX[i], mys[i] + a * mLY[i]] for a in (-LMAX, LMAX)] +
                       [[mxs[i + 1] + a * mLX[i + 1], mys[i + 1] + a * mLY[i + 1]] for a in (LMAX, -LMAX)])
        c0 = int(np.floor(pts[:, 0].min() - X0)); c1 = int(np.ceil(pts[:, 0].max() - X0))
        r0 = int(np.floor(Y1 - pts[:, 1].max())); r1 = int(np.ceil(Y1 - pts[:, 1].min()))
        c0, c1, r0, r1 = max(c0, 0), min(c1, NX), max(r0, 0), min(r1, NY)
        if c1 <= c0 or r1 <= r0:
            continue
        ex = CE[r0:r1, c0:c1]; ey = CN[r0:r1, c0:c1]
        a_ = (ex - mxs[i]) * mtx[i] / mtn[i] + (ey - mys[i]) * mty[i] / mtn[i]
        seglen = np.hypot(mxs[i + 1] - mxs[i], mys[i + 1] - mys[i])
        lat_ = (ex - mxs[i]) * mLX[i] + (ey - mys[i]) * mLY[i]
        inq = (a_ >= 0) & (a_ < seglen) & (np.abs(lat_) <= LMAX)
        sub_s = st_grid[r0:r1, c0:c1]; sub_l = lat_grid[r0:r1, c0:c1]
        closer = inq & (~np.isfinite(sub_l) | (np.abs(lat_) < np.abs(sub_l)))
        sub_s[closer] = mS_osm[i] + a_[closer] * (mS_osm[i + 1] - mS_osm[i]) / max(seglen, 1e-9)
        sub_l[closer] = lat_[closer]
    fi = np.clip(np.round(np.interp(np.nan_to_num(st_grid, nan=mS_osm[0]), mS_osm, np.arange(M))).astype(int), 0, M - 1)
    river = np.isfinite(lat_grid) & (lat_grid <= mleft[fi]) & (lat_grid >= mright[fi])

    # ---------------- orthophoto on the window
    om = np.load(args.ortho)
    rgba, b = om['rgba'], om['bounds_epsg3857']
    lon, lat = tm_inverse(CE, CN, CRTM05)
    mx, my = lonlat_to_merc(lon, lat)
    pc = np.clip(((mx - b[0]) / (b[2] - b[0]) * rgba.shape[1]).astype(int), 0, rgba.shape[1] - 1)
    pr = np.clip(((b[3] - my) / (b[3] - b[1]) * rgba.shape[0]).astype(int), 0, rgba.shape[0] - 1)
    rgb = rgba[pr, pc, :3]; ortho_valid = rgba[pr, pc, 3] > 0
    del lon, lat, mx, my, pc, pr
    f_ = rgb.astype(np.float32)
    mxc, mnc = f_.max(-1), f_.min(-1); sat = (mxc - mnc) / np.maximum(mxc, 1)
    R, Gc, B = f_[..., 0], f_[..., 1], f_[..., 2]
    # IGN active channel (bank lines): wetted water, gravel bars and rocks.
    # Classes inside it from the ~1 m orthophoto: whitewater is bright and
    # neutral/cool; gravel and boulders are bright and warm. Bright
    # components are dry bars when large, bank-attached and smooth (5 m local
    # brightness std < 22); textured bright patches (boulder gardens, single
    # rocks) are emergent rocks.
    channel = river
    lum = 0.3 * R + 0.59 * Gc + 0.11 * B
    lmean = box_mean(lum, 2); lstd = np.sqrt(np.maximum(box_mean(lum * lum, 2) - lmean ** 2, 0))
    veg = (Gc > R + 4) & (Gc > B + 4)
    white = channel & ortho_valid & (mnc > 132) & (sat < 0.26) & (B >= R - 10)
    bright = channel & ortho_valid & ~white & (mxc > 125) & ~(veg & (mxc < 150))
    comps, _lab = components(bright)
    edge = channel & ~(np.roll(channel, 1, 0) & np.roll(channel, -1, 0) & np.roll(channel, 1, 1) & np.roll(channel, -1, 1))
    bars = np.zeros_like(channel); rocks = np.zeros_like(channel)
    rock_comps = []
    for pix in comps:
        rr_, cc_ = pix[:, 0], pix[:, 1]
        if len(pix) > 120 and edge[rr_, cc_].any() and lstd[rr_, cc_].mean() < 22:
            bars[rr_, cc_] = True
        else:
            rocks[rr_, cc_] = True
            rock_comps.append(pix)
    vegin = channel & ortho_valid & veg & (mxc > 60) & ~white & ~bright
    river = channel & ~bars & ~rocks & ~vegin
    foam = white & river

    # ---------------- water-surface anchors: contour level crossings
    cont = json.loads(args.contours.read_text(encoding='utf-8'))['features']
    by_level = {}
    for f in cont:
        z = float(f['properties']['elevacion'])
        p = np.array(f['geometry']['coordinates'])[:, :2]
        if len(p) >= 2:
            by_level.setdefault(z, []).append(densify(p, 2.0))
    anchors = []
    for z in sorted(by_level):
        q = np.vstack(by_level[z])
        dmin = np.full(len(q), np.inf)
        for k in range(0, len(bank), 512):
            dmin = np.minimum(dmin, np.hypot(q[:, None, 0] - bank[None, k:k + 512, 0], q[:, None, 1] - bank[None, k:k + 512, 1]).min(1))
        near = q[dmin < args.anchor_bank_distance_m]
        if not len(near):
            continue
        ns, nl = project(near[:, 0], near[:, 1], mxs, mys, mS_osm, mLX, mLY)
        ok = (np.abs(nl) < 90) & (ns > 5) & (ns < M - 5)
        if ok.any():
            anchors.append((float(ns[ok].min()), z, int(ok.sum())))
    anchors.sort()
    a_st = np.array([a[0] for a in anchors]); a_z = np.array([a[1] for a in anchors])
    keep = np.r_[True, np.diff(a_z) < 0] & np.r_[np.diff(a_st) > 20, True]
    a_st, a_z = a_st[keep], a_z[keep]
    assert np.all(np.diff(a_z) < 0), 'anchors must fall downstream'

    # ---------------- surface between anchors: drops distributed by whitewater (inferred)
    st_i = np.clip(np.round(np.nan_to_num(st_grid, nan=-1)).astype(int), -1, M - 1)
    wet_at = np.bincount(st_i[river & (st_i >= 0)], minlength=M).astype(float)
    foam_at = np.bincount(st_i[foam & (st_i >= 0)], minlength=M).astype(float)
    share = np.where(wet_at > 3, foam_at / np.maximum(wet_at, 1), 0.0)
    share = gauss_smooth(share, 6.0)
    w = args.pool_weight + share
    ws_m = np.full(M, np.nan)
    for i in range(len(a_st) - 1):
        j0, j1 = int(round(a_st[i])), int(round(a_st[i + 1]))
        c = np.concatenate([[0.0], np.cumsum(w[j0:j1])])
        ws_m[j0:j1 + 1] = a_z[i] - (a_z[i] - a_z[i + 1]) * c / c[-1]
    fin = np.isfinite(ws_m)
    ws_m = np.interp(np.arange(M), np.nonzero(fin)[0], ws_m[fin])
    reach_idx = np.nonzero(reach)[0]
    assert fin[reach_idx].all(), 'reach must lie between two surface anchors'
    ws_cell = np.where(np.isfinite(st_grid), ws_m[np.clip(st_i, 0, M - 1)], np.nan)

    # ---------------- terrain: harmonic interpolation between contours, water edge at the surface
    fixed = np.zeros((NY, NX), bool); fval = np.zeros((NY, NX))
    for z, lines in by_level.items():
        for q in lines:
            qq = densify(q, 0.7)
            c = np.floor(qq[:, 0] - X0).astype(int); r = np.floor(Y1 - qq[:, 1]).astype(int)
            ok = (c >= 0) & (c < NX) & (r >= 0) & (r < NY)
            fixed[r[ok], c[ok]] = True; fval[r[ok], c[ok]] = z
    fixed &= ~channel
    fixed |= channel
    # Gravel bars (dry in the photo) as a beach profile: surface + 0.1 m at
    # the water's edge rising to + args.bar_top_m over args.bar_ramp_m
    # (inferred: the photographs give their extent, not their height).
    bar_rise = 0.1 + (args.bar_top_m - 0.1) * np.clip(edt_inside(bars) / args.bar_ramp_m, 0, 1)
    fval = np.where(channel, np.where(bars, ws_cell + bar_rise, ws_cell), fval)
    dem = harmonic_fill(fval, fixed)
    # Harmonic interpolation creases at every contour line (piecewise linear
    # across them); lighting shows the creases. Smooth by about 4.5 m away
    # from the channel (the contours' own accuracy is a few metres), fading
    # to none within 3 m of the water edge.
    dist_ch = edt_inside(~channel)
    sm = dem
    for _ in range(3):
        sm = box_mean(sm, 4)
    wsm = np.clip((dist_ch - 3.0) / 12.0, 0, 1)
    dem = wsm * sm + (1 - wsm) * dem
    dem = np.where(channel, np.where(bars, ws_cell + bar_rise, ws_cell), dem)

    # ---------------- inferred bed: discharge-consistent depth on a smooth section
    e = edt_inside(river)
    s_bin = np.clip(st_i // 2, 0, None)
    nb = M // 2 + 1
    rv = river & (st_i >= 0)
    width = np.bincount(s_bin[rv], minlength=nb) / 2.0
    fshape_all = np.zeros((NY, NX))
    halfw = np.maximum(np.interp(np.arange(nb), np.nonzero(width > 0)[0], width[width > 0]) / 2.0, 1.0)
    fshape_all[rv] = np.sqrt(np.clip(e[rv] / halfw[s_bin[rv]], 0.02, 1.0))
    sum_f53 = np.bincount(s_bin[rv], weights=fshape_all[rv] ** (5 / 3), minlength=nb)
    wsb = ws_m[np.clip(np.arange(nb) * 2, 0, M - 1)]
    slope = np.clip(-np.gradient(gauss_smooth(wsb, 5.0), 2.0), args.min_slope, None)
    sh_b = share[np.clip(np.arange(nb) * 2, 0, M - 1)]
    nman = args.n_pool + (args.n_rapid - args.n_pool) * np.clip((sh_b - 0.05) / 0.20, 0, 1)
    have = sum_f53 > 0
    Hn = np.full(nb, np.nan)
    Hn[have] = (Q * nman[have] * 2.0 / (np.sqrt(slope[have]) * sum_f53[have])) ** 0.6
    q_unit = Q / np.maximum(width, 1.0)
    hc = (q_unit ** 2 / G) ** (1 / 3)
    mean_f = np.where(have, np.bincount(s_bin[rv], weights=fshape_all[rv], minlength=nb) / np.maximum(np.bincount(s_bin[rv], minlength=nb), 1), 1.0)
    Hn = np.where(have, np.maximum(Hn, hc / np.maximum(mean_f, 0.3)), np.nan)
    Hn = np.interp(np.arange(nb), np.nonzero(have)[0], Hn[have])
    Hn = gauss_smooth(Hn, 3.0)
    corr = None
    if args.bed_correction:
        corr = np.load(args.bed_correction)
    bed = dem.copy()
    cls = np.zeros((NY, NX), np.uint8)
    depth = Hn[s_bin[rv]] * fshape_all[rv]
    bed_rv = ws_cell[rv] - np.maximum(depth, 0.05)
    if corr is not None:
        bed_rv = np.minimum(bed_rv + np.interp(st_grid[rv], corr['station'], corr['delta']), ws_cell[rv] - 0.05)
    bed[rv] = bed_rv; cls[rv] = 2
    # emergent rocks: tops at the surface plus a size-scaled height (inferred), dome shaped
    rock_tops = []
    er = edt_inside(rocks)
    for pix in rock_comps:
        r_, c_ = pix[:, 0], pix[:, 1]
        if not np.isfinite(ws_cell[r_, c_]).all():
            continue
        htop = float(np.clip(0.45 * np.sqrt(len(pix)), 0.3, 1.5))
        emax = max(er[r_, c_].max(), 1.0)
        bed[r_, c_] = ws_cell[r_, c_] + htop * np.sqrt(np.clip(er[r_, c_] / emax, 0, 1))
        cls[r_, c_] = 3
        rock_tops.append(dict(x=float(X0 + c_.mean() + 0.5), y=float(Y1 - r_.mean() - 0.5), area_m2=int(len(pix)), height_m=htop))
    ws_grid = np.where(rv, ws_cell, np.nan)
    bed, cls, boulders = foam_boulders(bed, cls, foam, rocks, ws_grid, st_grid, mxs, mys, X0, Y1, args.boulder_crest_below_ws_m)

    # ---------------- outputs
    out.mkdir(parents=True)
    station_grid = np.where(rv, st_grid, np.nan).astype(np.float32)
    np.savez_compressed(out / 'evidence_grid.npz', bed=bed.astype(np.float32), dem2021=dem.astype(np.float32), dem=dem.astype(np.float32),
                        bathy2014=np.full((NY, NX), np.nan, np.float32), class_code=cls, river=river, channel=channel,
                        foam=foam, rocks=rocks, bars=bars, station=station_grid, lateral=lat_grid.astype(np.float32),
                        ws=np.where(channel, ws_cell, np.nan).astype(np.float32))
    sel = (mS_osm >= reach_idx[0] - 400) & (mS_osm <= reach_idx[-1] + 400)
    (out / 'centreline.json').write_text(json.dumps(dict(
        schema='raftsim.pacuare.huacas_midline.v1', crs='EPSG:5367 CR05 / CRTM05',
        method='midline between the IGN bank lines (Gaussian sigma 12 m), 1 m arc length; station = midline arc length from its upstream start',
        reach_station_m=[float(reach_idx[0]), float(reach_idx[-1])],
        points_xy_station=[[float(a), float(b_), float(c)] for a, b_, c in zip(mxs[sel][::2], mys[sel][::2], mS_osm[sel][::2])],
        osm_chain_m=[float(v) for v in mchain[sel][::2]])) + '\n')
    centers = np.arange(nb) * 2.0
    (out / 'profile.json').write_text(json.dumps(dict(
        station_center_m=centers.tolist(), ws_reference_m=wsb.tolist(), ws_reference_method='contour_level_crossings_whitewater_weighted',
        anchors=[dict(station_m=float(s_), osm_chain_m=float(np.interp(s_, mS_osm, mchain)), elevation_m=float(z_)) for s_, z_ in zip(a_st, a_z)],
        whitewater_share=[float(v) for v in share[::2]], slope=slope.tolist(), normal_depth_m=Hn.tolist(), manning_n=nman.tolist(),
        wetted_width_m=width.tolist())) + '\n')
    (out / 'boulders.json').write_text(json.dumps(dict(
        schema='raftsim.pacuare.inferred_boulders.v1', inferred=True, crest_below_ws_m=args.boulder_crest_below_ws_m,
        method='one boulder per lateral cluster of the upstream edge of each >= 4 m2 orthophoto whitewater patch over inferred bed, '
               'shifted upstream by its radius; crest at the surface minus the margin (pour-over assumption)',
        boulders=boulders, emergent_rocks=rock_tops), indent=1) + '\n')
    inreach = rv & (station_grid >= reach_idx[0]) & (station_grid <= reach_idx[-1])
    stats = dict(window=dict(x0=X0, y_top=Y1, nx=NX, ny=NY), channel_cells=int(channel.sum()), wetted_cells=int(river.sum()),
                 whitewater_cells=int(foam.sum()), emergent_rock_cells=int(rocks.sum()), bar_cells=int(bars.sum()),
                 reach_station_m=[float(reach_idx[0]), float(reach_idx[-1])],
                 reach_osm_chain_m=[float(mchain[reach_idx[0]]), float(mchain[reach_idx[-1]])],
                 ws_reach_m=[float(ws_m[reach_idx[0]]), float(ws_m[reach_idx[-1]])],
                 anchors=[(float(s_), float(z_)) for s_, z_ in zip(a_st, a_z)],
                 inferred_depth_m_p10_p50_p90=np.percentile((ws_cell - bed)[inreach & (cls == 2)], [10, 50, 90]).tolist(),
                 wetted_width_reach_m_p10_p50_p90=np.percentile(width[reach_idx[0] // 2:reach_idx[-1] // 2], [10, 50, 90]).tolist(),
                 foam_boulders=len(boulders), emergent_rocks=len(rock_tops))
    manifest = dict(
        schema='raftsim.pacuare.huacas_evidence_grid.v1', crs='EPSG:5367 CR05 / CRTM05', vertical='IGN orthometric metres (contours)',
        grid=dict(x0=X0, y_top=Y1, nx=NX, ny=NY, cell_m=1.0),
        inputs={k: dict(path=str(v), sha256=sha(v)) for k, v in (('contours', args.contours), ('hydrography', args.hydrography),
                                                                 ('centreline', args.centreline), ('ortho_mosaic', args.ortho))},
        sources_manifest_sha256=sha(SRC / 'manifest.json'),
        class_codes={'0': 'dry ground: interpolated between IGN 10 m contours (measured contours, interpolated surface); gravel bars (extent from '
                              'the orthophoto) at the surface + 0.1 m at the water rising to the bar crest (inferred height)',
                     '2': 'bed: discharge-consistent depth for the planning discharge (inferred)',
                     '3': 'emergent rock: location from the orthophoto (measured), top height from its size (inferred)',
                     '4': 'submerged boulder: location from orthophoto whitewater, height from a pour-over assumption (inferred)'},
        parameters=dict(discharge_m3s=Q, discharge_source='existing rainfed_runnable_planning band (not measured; no gauge)',
                        n_pool=args.n_pool, n_rapid=args.n_rapid, pool_weight=args.pool_weight, min_slope=args.min_slope,
                        anchor_bank_distance_m=args.anchor_bank_distance_m, chain_m=list(args.chain_m), margin_m=args.margin_m,
                        bar_top_m=args.bar_top_m, bar_ramp_m=args.bar_ramp_m,
                        bed_correction=None if corr is None else str(args.bed_correction),
                        bed_correction_sha256=None if corr is None else sha(args.bed_correction)),
        statistics=stats, inferred=True, accepted=False)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    review(out, rgb, river, foam, rocks, bars, dem, bed, ws_cell, cls, centers, wsb, a_st, a_z, share[::2], reach_idx)
    print(json.dumps(stats, indent=1))


def box_mean(a, r):
    p = np.pad(a, r, mode='edge'); c = np.pad(p.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    n = 2 * r + 1
    return (c[n:, n:] - c[:-n, n:] - c[n:, :-n] + c[:-n, :-n]) / (n * n)


def edt_inside(mask):
    """Approximate Euclidean distance (cells) to the nearest False cell (chamfer 3-4)."""
    d = np.where(mask, 10 ** 6, 0).astype(np.int64)
    H, W = d.shape
    for _ in range(2):
        for r in range(1, H):
            d[r] = np.minimum(d[r], d[r - 1] + 3)
            d[r, 1:] = np.minimum(d[r, 1:], d[r - 1, :-1] + 4); d[r, :-1] = np.minimum(d[r, :-1], d[r - 1, 1:] + 4)
        for r in range(H - 2, -1, -1):
            d[r] = np.minimum(d[r], d[r + 1] + 3)
            d[r, 1:] = np.minimum(d[r, 1:], d[r + 1, :-1] + 4); d[r, :-1] = np.minimum(d[r, :-1], d[r + 1, 1:] + 4)
        for c in range(1, W):
            d[:, c] = np.minimum(d[:, c], d[:, c - 1] + 3)
        for c in range(W - 2, -1, -1):
            d[:, c] = np.minimum(d[:, c], d[:, c + 1] + 3)
    return d / 3.0


def foam_boulders(bed, cls, foam, rocks, ws_grid, st_grid, mxs, mys, X0, Y1, crest_below):
    """Inferred submerged boulders (class 4) at the upstream edges of whitewater patches."""
    H, W = foam.shape
    comps, _ = components(foam)
    near_rock = rocks.copy()
    for _ in range(3):
        o = near_rock.copy(); o[1:] |= near_rock[:-1]; o[:-1] |= near_rock[1:]; o[:, 1:] |= near_rock[:, :-1]; o[:, :-1] |= near_rock[:, 1:]
        near_rock = o
    seeds = []
    for k, p in enumerate(sorted((p for p in comps if len(p) >= 4), key=len, reverse=True)):
        x = X0 + p[:, 1] + 0.5; y = Y1 - p[:, 0] - 0.5
        st = st_grid[p[:, 0], p[:, 1]]
        if not np.isfinite(st).any():
            continue
        j = int(np.clip(np.nanmean(st), 0, len(mxs) - 1))
        a0, a1 = max(j - 15, 0), min(j + 15, len(mxs) - 1)
        t = np.array([mxs[a1] - mxs[a0], mys[a1] - mys[a0]]); t /= np.linalg.norm(t)  # downstream
        nrm = np.array([-t[1], t[0]])
        a = x * t[0] + y * t[1]; b = x * nrm[0] + y * nrm[1]
        edge = a <= a.min() + 1.5
        order = np.argsort(b[edge]); eb = b[edge][order]; ex = x[edge][order]; ey = y[edge][order]
        groups, start = [], 0
        for i in range(1, len(eb) + 1):
            if i == len(eb) or eb[i] - eb[i - 1] > 1.5 or eb[i] - eb[start] > 3.0:
                groups.append(slice(start, i)); start = i
        width = b.max() - b.min() + 1.0
        radius = float(np.clip(0.5 * width, 1.0, 2.5)) if len(groups) == 1 else 1.5
        for gsl in groups:
            sx = ex[gsl].mean() - t[0] * radius; sy = ey[gsl].mean() - t[1] * radius
            c, r = int(sx - X0), int(Y1 - sy)
            if not (0 <= r < H and 0 <= c < W) or cls[r, c] != 2 or near_rock[r, c] or not np.isfinite(ws_grid[r, c]):
                continue
            if any((sx - q['x']) ** 2 + (sy - q['y']) ** 2 < 2.5 ** 2 for q in seeds):
                continue
            hb = ws_grid[r, c] - crest_below - bed[r, c]
            if hb < 0.3:
                continue
            seeds.append(dict(x=float(sx), y=float(sy), radius_m=radius, crest_m=float(ws_grid[r, c] - crest_below),
                              base_m=float(bed[r, c]), height_m=float(hb), patch_area_m2=int(len(p)), patch_rank=k))
    bed = bed.copy(); cls = cls.copy()
    for q in seeds:
        rad = q['radius_m']; c0, r0 = int(q['x'] - X0), int(Y1 - q['y'])
        rs = slice(max(r0 - 4, 0), min(r0 + 5, H)); cs = slice(max(c0 - 4, 0), min(c0 + 5, W))
        yy, xx = np.mgrid[rs, cs]
        d = np.hypot(X0 + xx + 0.5 - q['x'], Y1 - yy - 0.5 - q['y'])
        wgt = np.where(d < rad, np.cos(0.5 * np.pi * d / rad) ** 2, 0.0)
        sub = bed[rs, cs]; cap = np.where(np.isfinite(ws_grid[rs, cs]), ws_grid[rs, cs] - crest_below, sub)
        new = np.where((cls[rs, cs] == 2) | (cls[rs, cs] == 4), np.minimum(sub + q['height_m'] * wgt, np.maximum(sub, cap)), sub)
        raised = new > sub + 0.05
        bed[rs, cs] = new; cls[rs, cs] = np.where(raised, 4, cls[rs, cs])
    return bed, cls, seeds


def review(out, rgb, river, foam, rocks, bars, dem, bed, ws_cell, cls, centers, wsb, a_st, a_z, share, reach_idx):
    img = rgb.copy()
    img[river & ~foam] = (img[river & ~foam] * 0.5 + np.array([0, 40, 120]) * 0.5).astype(np.uint8)
    img[foam] = (255, 255, 255); img[rocks] = (230, 120, 40)
    img[bars] = (img[bars] * 0.4 + np.array([220, 210, 40]) * 0.6).astype(np.uint8)
    write_png(out / 'classes.png', img[::2, ::2])
    gy, gx = np.gradient(dem)
    s_ = np.arctan(np.hypot(gx, gy)); asp = np.arctan2(-gx, gy)
    hs = np.clip(np.sin(np.radians(45)) * np.cos(s_) + np.cos(np.radians(45)) * np.sin(s_) * np.cos(np.radians(315) - asp), 0, 1)
    shade = (np.stack([hs] * 3, -1) * 255).astype(np.uint8)
    dep = np.where(cls == 2, ws_cell - bed, np.nan)
    t = np.clip(np.nan_to_num(dep, nan=0) / 3.0, 0, 1)
    col = np.stack([40 * (1 - t), 90 + 60 * (1 - t), 140 + 110 * t], -1).astype(np.uint8)
    shade[cls == 2] = col[cls == 2]; shade[cls == 3] = (230, 120, 40); shade[cls == 4] = (250, 60, 60)
    write_png(out / 'terrain_depth.png', shade[::2, ::2])
    Wd, Hd = 1000, 360
    chart = np.full((Hd, Wd, 3), 255, np.uint8)
    lo_s, hi_s = float(reach_idx[0]) - 300, float(reach_idx[-1]) + 300
    zlo, zhi = wsb[(centers >= lo_s) & (centers <= hi_s)].min() - 5, wsb[(centers >= lo_s) & (centers <= hi_s)].max() + 5
    def xy(s, z):
        return int((s - lo_s) / (hi_s - lo_s) * (Wd - 1)), int((zhi - z) / (zhi - zlo) * (Hd - 1))
    for s, z, sh in zip(centers, wsb, share):
        if lo_s <= s <= hi_s:
            x, y = xy(s, z); chart[max(y - 1, 0):y + 2, x] = (20, 60, 200)
            yb = Hd - 1 - int(sh * 200); chart[yb:Hd, x] = (200, 200, 200)
    for s, z in zip(a_st, a_z):
        if lo_s <= s <= hi_s:
            x, y = xy(s, z); chart[max(y - 4, 0):y + 5, max(x - 4, 0):x + 5] = (220, 30, 30)
    for s in (reach_idx[0], reach_idx[-1]):
        x, _ = xy(s, zlo); chart[:, x] = (0, 160, 0)
    write_png(out / 'profile.png', chart)

if __name__ == '__main__':
    main()
