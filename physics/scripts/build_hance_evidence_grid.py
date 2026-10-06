"""Hance Rapid evidence grid: measured ground, measured pools, inferred rapid bed.

Frame: NAD83(2011) / Arizona Central (EPSG:6404) metres, 1 m cells, window
x 211300-213800, y 559088-560300; heights are NAD83(2011) ellipsoid heights
(all sources share them). Built only from the archived sources in
physics/data/real_world/colorado_river_grand_canyon_rowing/hance_sources_2026_09.

Per cell class (class_code):
  0 dry ground            2021 photogrammetric DEM (measured)
  1 measured bed          2014 multibeam/singlebeam/total-station DEM (measured)
  2 inferred bed          discharge-consistent inference, no sonar (inferred)
  3 emergent rock         wet channel, imagery says dry: 2021 DEM top (measured)

Water outline at 8,000 cfs: 2021 imagery (NDWI > 0.15 plus bright unsaturated
foam next to water), largest component through the window.

Water surface WS(s): 2021 DEM over water, per-5 m-station median, made
non-increasing downstream (pool-adjacent violators) and lightly smoothed.
Photogrammetry over moving water is noisy (p10-p90 ~1 m); treated as the
reference surface, not a measurement of every wave.

Inferred depth (class 2): Manning strip normal depth per 5 m bin,
H = (Q n / (S^0.5 sum f^(5/3) dA))^(3/5), bank shape f = min(1, d/L),
L = max(3, 0.3 half-width), Q = 226.5 m3/s (8,000 cfs, the 2021 flight flow),
n = 0.058 (the scenario's published effective roughness) where S >= 0.004,
0.035 in pools. The measured-minus-inferred difference is diffused from
sonar coverage into the gap (decay length 25 m) so inferred bed meets the
measured bed continuously.

Numpy only. Output: <out>/evidence_grid.npz, centreline.json, manifest.json.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'physics/scripts'))
from tiff_numpy import read_geotiff  # noqa: E402

SRC = ROOT / 'physics/data/real_world/colorado_river_grand_canyon_rowing/hance_sources_2026_09'
X0, Y1, NX, NY = 211300.0, 560300.0, 2500, 1212
Q = 226.534772736
N_RAPID, N_POOL, S_RAPID = 0.058, 0.035, 0.004
BIN = 5.0
BATHY_CORNER = (197656.0, 577525.0)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def shifted_or(mask, k):
    out = mask.copy()
    for _ in range(k):
        o = out.copy()
        o[1:] |= out[:-1]; o[:-1] |= out[1:]; o[:, 1:] |= out[:, :-1]; o[:, :-1] |= out[:, 1:]
        out = o
    return out


def edt_inside(mask, max_k=120):
    """Approximate Euclidean distance (cells) to the nearest False cell (chamfer 3-4)."""
    big = 10 ** 6
    d = np.where(mask, big, 0).astype(np.int64)
    H, W = d.shape
    for _ in range(2):
        for r in range(1, H):
            d[r, :] = np.minimum(d[r, :], d[r - 1, :] + 3)
            d[r, 1:] = np.minimum(d[r, 1:], d[r - 1, :-1] + 4)
            d[r, :-1] = np.minimum(d[r, :-1], d[r - 1, 1:] + 4)
        for r in range(H - 2, -1, -1):
            d[r, :] = np.minimum(d[r, :], d[r + 1, :] + 3)
            d[r, 1:] = np.minimum(d[r, 1:], d[r + 1, :-1] + 4)
            d[r, :-1] = np.minimum(d[r, :-1], d[r + 1, 1:] + 4)
        for c in range(1, W):
            d[:, c] = np.minimum(d[:, c], d[:, c - 1] + 3)
        for c in range(W - 2, -1, -1):
            d[:, c] = np.minimum(d[:, c], d[:, c + 1] + 3)
    return d / 3.0


def pava_nonincreasing(y, w):
    """Weighted isotonic regression, non-increasing."""
    vals, wts, cnt = [], [], []
    for yi, wi in zip(y, w):
        vals.append(yi); wts.append(wi); cnt.append(1)
        while len(vals) > 1 and vals[-2] < vals[-1]:
            v = (vals[-2] * wts[-2] + vals[-1] * wts[-1]) / (wts[-2] + wts[-1])
            wts[-2] += wts[-1]; cnt[-2] += cnt[-1]; vals[-2] = v
            vals.pop(); wts.pop(); cnt.pop()
    return np.repeat(vals, cnt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('output', type=Path)
    ap.add_argument('--n-rapid', type=float, default=N_RAPID, help='Manning n for inferred depth where S >= 0.004')
    ap.add_argument('--critical-depth-floor', action='store_true',
                    help='inferred depth never below critical depth of the bin (controls pass through critical flow)')
    ap.add_argument('--bed-correction', type=Path, default=None,
                    help='npz with evidence station (m) and delta (m) added to the inferred base bed (cook calibration)')
    ap.add_argument('--foam-boulders', action='store_true',
                    help='inferred submerged boulders at the upstream edge of imagery whitewater patches (class 4)')
    ap.add_argument('--boulder-crest-below-ws-m', type=float, default=0.25)
    ap.add_argument('--ws-reference', choices=('water_median', 'textured_edge'), default='water_median',
                    help='water_median: DEM median over imagery water (v1); textured_edge: whitewater DEM and '
                         'dry-DEM/wet-bathymetry waterline pairs only')
    args = ap.parse_args()
    out = args.output.resolve()
    assert not out.exists(), 'fresh output required'
    manifest_src = json.loads((SRC / 'manifest.json').read_text())
    dem = np.load(SRC / 'dem_2021/dem2021_hance_1m.npz')['elevation_ellipsoid_m'].astype(np.float64)
    assert dem.shape == (NY, NX)
    # --- imagery -> 1 m water/foam mask
    img, g, _ = read_geotiff(SRC / 'imagery_2021/hance_broad_0p5m.tif')
    assert g['corner_utm_m'] == (X0, Y1) and g['cell_m'] == (0.5, 0.5)
    I = img.astype(np.float32).reshape(NY, 2, NX, 2, 4).mean((1, 3))
    R, G, B, N = I[..., 0], I[..., 1], I[..., 2], I[..., 3]
    valid = I.sum(-1) > 0
    ndwi = (G - N) / np.maximum(G + N, 1)
    mx = np.max(I[..., :3], -1)
    sat = (mx - np.min(I[..., :3], -1)) / np.maximum(mx, 1)
    water = valid & (ndwi > 0.15)
    foam = valid & shifted_or(water, 15) & (sat < 0.18) & ((R + G + B) / 3 > 22000)
    wet = water | foam
    seed = np.zeros_like(wet); seed[:, :3] = wet[:, :3]; seed[:, -3:] = wet[:, -3:]
    for it in range(20000):
        grown = seed.copy()
        grown[1:] |= seed[:-1]; grown[:-1] |= seed[1:]; grown[:, 1:] |= seed[:, :-1]; grown[:, :-1] |= seed[:, 1:]
        grown &= wet
        if it % 50 == 0 and np.array_equal(grown, seed):
            break
        seed = grown
    river = seed
    # channel = river plus enclosed dry islands/rocks (holes in the river)
    outside = np.zeros_like(river); outside[0, :] = ~river[0, :]; outside[-1, :] = ~river[-1, :]
    for it in range(20000):
        grown = outside.copy()
        grown[1:] |= outside[:-1]; grown[:-1] |= outside[1:]; grown[:, 1:] |= outside[:, :-1]; grown[:, :-1] |= outside[:, 1:]
        grown &= ~river
        if it % 50 == 0 and np.array_equal(grown, outside):
            break
        outside = grown
    channel = ~outside
    rocks = channel & ~river
    # --- bathymetry on the grid (integer-aligned)
    bathy_raw, bg, _ = read_geotiff_7z(SRC / 'bathymetry_2014/dem.7z')
    bx0, by0 = bg['corner_utm_m']
    c0, r0 = int(round(X0 - bx0)), int(round(by0 - Y1))
    bath = bathy_raw[r0:r0 + NY, c0:c0 + NX].astype(np.float64)
    bath[(bath < 0) | (bath > 5000)] = np.nan
    if bath.shape != (NY, NX):  # the survey raster ends inside the window: pad with NaN
        pad = np.full((NY, NX), np.nan); pad[:bath.shape[0], :bath.shape[1]] = bath; bath = pad
    del bathy_raw
    # --- centreline: river is monotone in x here; column centre of the channel
    cols = np.arange(NX)
    cy = np.array([np.nonzero(channel[:, c])[0].mean() if channel[:, c].any() else np.nan for c in cols])
    ok = np.isfinite(cy)
    cy = np.interp(cols, cols[ok], cy[ok])
    k = np.ones(61) / 61
    cy = np.convolve(np.pad(cy, 30, mode='edge'), k, mode='valid')
    px = X0 + cols + 0.5; py = Y1 - (cy + 0.5)
    seg = np.hypot(np.diff(px), np.diff(py))
    s_from_west = np.concatenate([[0.0], np.cumsum(seg)])
    station_c = s_from_west[-1] - s_from_west  # 0 at the upstream (east) end
    # station per cell = station of the nearest centreline sample (search +-60 columns)
    rr, cc = np.nonzero(channel)
    ex = X0 + cc + 0.5; ny = Y1 - (rr + 0.5)
    best = np.full(len(rr), np.inf); bi = np.zeros(len(rr), int)
    for dc in range(-60, 61, 2):
        j = np.clip(cc + dc, 0, NX - 1)
        dd = (ex - px[j]) ** 2 + (ny - py[j]) ** 2
        u = dd < best; best[u] = dd[u]; bi[u] = j[u]
    station = station_c[bi]
    # --- water surface profile from the DEM over open water
    wr, wc = np.nonzero(river)
    cell_index = -np.ones((NY, NX), int); cell_index[rr, cc] = np.arange(len(rr))
    st_river = station[cell_index[wr, wc]]
    dem_river = dem[wr, wc]
    nb = int(np.ceil(station_c.max() / BIN)) + 1
    b = np.clip((st_river / BIN).astype(int), 0, nb - 1)
    med = np.full(nb, np.nan); cnt = np.bincount(b, minlength=nb)
    order = np.argsort(b, kind='stable'); splits = np.cumsum(cnt)[:-1]
    for kk, idx in enumerate(np.split(order, splits)):
        v = dem_river[idx]; v = v[np.isfinite(v)]
        if len(v) >= 10:
            med[kk] = np.median(v)
    centers = (np.arange(nb) + 0.5) * BIN
    obs_kind = np.where(np.isfinite(med), 'water_median', 'none').astype(object)
    if args.ws_reference == 'textured_edge':
        # The DEM is less accurate on water (metadata); over calm clear water the
        # stereo match lands near the bed and reads low. Use only surfaces with
        # their own texture: whitewater, and the waterline between a dry 2021
        # DEM cell and its wet neighbour's measured 2014 bed.
        obs = np.full(nb, np.nan); wts = np.zeros(nb)
        fr_, fc_ = np.nonzero(foam & river)
        fst = station[cell_index[fr_, fc_]]; fb = np.clip((fst / BIN).astype(int), 0, nb - 1)
        fcnt = np.bincount(fb, minlength=nb)
        pv, ps = [], []
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            r1, c1 = np.nonzero(~channel)
            r2, c2 = r1 - dr, c1 - dc
            ok = (r2 >= 0) & (r2 < NY) & (c2 >= 0) & (c2 < NX)
            r1, c1, r2, c2 = r1[ok], c1[ok], r2[ok], c2[ok]
            ok = river[r2, c2] & np.isfinite(dem[r1, c1]) & np.isfinite(bath[r2, c2])
            r1, c1, r2, c2 = r1[ok], c1[ok], r2[ok], c2[ok]
            gap = dem[r1, c1] - bath[r2, c2]
            ok = (gap > 0) & (gap < 1.0)  # steep banks put the dry cell far above the waterline
            pv.append(0.5 * (dem[r1[ok], c1[ok]] + bath[r2[ok], c2[ok]])); ps.append(station[cell_index[r2[ok], c2[ok]]])
        pv = np.concatenate(pv); pb = np.clip((np.concatenate(ps) / BIN).astype(int), 0, nb - 1)
        pcnt = np.bincount(pb, minlength=nb)
        for kk in range(nb):
            if fcnt[kk] >= 10 and fcnt[kk] >= 0.05 * cnt[kk]:  # isolated bright cells in pools are glint
                v = dem[fr_[fb == kk], fc_[fb == kk]]; v = v[np.isfinite(v)]
                if len(v) >= 10:
                    obs[kk] = np.median(v); wts[kk] = len(v); obs_kind[kk] = 'whitewater'
                    continue
            if pcnt[kk] >= 5:
                obs[kk] = np.median(pv[pb == kk]); wts[kk] = pcnt[kk]; obs_kind[kk] = 'edge_pair'
            else:
                obs_kind[kk] = 'none'
        med, cnt = obs, np.maximum(wts, 1).astype(int)
    good = np.isfinite(med)
    med_i = np.interp(centers, centers[good], med[good])
    weights = np.where(good, cnt, 1) if args.ws_reference == 'textured_edge' else np.maximum(cnt, 1)
    ws = pava_nonincreasing(med_i, weights.astype(float))
    ws = np.convolve(np.pad(ws, 3, mode='edge'), np.ones(7) / 7, mode='valid')
    slope = np.clip(-np.gradient(ws, BIN), 0.0005, 0.05)
    slope = np.convolve(np.pad(slope, 4, mode='edge'), np.ones(9) / 9, mode='valid')
    # --- inferred depth (discharge-consistent)
    dist = edt_inside(channel)  # metres to the channel edge
    d_cells = dist[rr, cc]
    cb = np.clip((station / BIN).astype(int), 0, nb - 1)
    halfw = np.zeros(nb); np.maximum.at(halfw, cb, d_cells)
    L = np.maximum(3.0, 0.3 * np.convolve(np.pad(halfw, 2, mode='edge'), np.ones(5) / 5, mode='valid'))
    f = np.clip(d_cells / L[cb], 0.0, 1.0)
    K = np.bincount(cb, weights=f ** (5 / 3), minlength=nb) / BIN
    K = np.maximum(np.convolve(np.pad(K, 2, mode='edge'), np.ones(5) / 5, mode='valid'), 1e-3)
    n = np.where(slope >= S_RAPID, args.n_rapid, N_POOL)
    Hn = np.clip((Q * n / (np.sqrt(slope) * K)) ** 0.6, 0.3, 12.0)
    if args.critical_depth_floor:
        # strip-model critical depth: h_c = (q^2/g)^(1/3) with q = Q / wetted width of the bin
        width = np.maximum(np.bincount(b, minlength=nb) / BIN, 5.0)
        width = np.convolve(np.pad(width, 2, mode='edge'), np.ones(5) / 5, mode='valid')
        Hn = np.maximum(Hn, (Q * Q / (9.81 * width * width)) ** (1 / 3))
    Hn = np.convolve(np.pad(Hn, 3, mode='edge'), np.ones(7) / 7, mode='valid')
    ws_cell = np.interp(station, centers, ws)
    inferred = ws_cell - np.interp(station, centers, Hn) * f
    # --- blend: diffuse measured-minus-inferred into the gap
    corr = np.zeros((NY, NX)); have = np.zeros((NY, NX), bool)
    measured = np.isfinite(bath[rr, cc]) & river[rr, cc]
    corr[rr[measured], cc[measured]] = bath[rr[measured], cc[measured]] - inferred[measured]
    have[rr[measured], cc[measured]] = True
    val = np.where(have, corr, 0.0); wgt = have.astype(float)
    for _ in range(60):  # ~25 m decay with the 0.96 factor over 3-neighbour steps
        v2 = val.copy(); w2 = wgt.copy()
        for a, bsl in (((slice(1, None), slice(None)), (slice(None, -1), slice(None))),
                       ((slice(None, -1), slice(None)), (slice(1, None), slice(None))),
                       ((slice(None), slice(1, None)), (slice(None), slice(None, -1))),
                       ((slice(None), slice(None, -1)), (slice(None), slice(1, None)))):
            v2[a] += 0.96 * val[bsl]; w2[a] += 0.96 * wgt[bsl]
        val = np.where(have, corr, v2 / 5.0); wgt = np.where(have, 1.0, w2 / 5.0)
        val = np.where(channel, val, 0.0); wgt = np.where(channel, wgt, 0.0)
    diffused = np.where(wgt > 1e-6, val / np.maximum(wgt, 1e-6), 0.0) * np.clip(wgt, 0, 1)
    bed = dem.copy()
    cls = np.zeros((NY, NX), np.uint8)
    inferred_bed = inferred + diffused[rr, cc]
    correction = None
    if args.bed_correction:
        correction = np.load(args.bed_correction)
        inferred_bed = inferred_bed + np.interp(station, correction['station'], correction['delta'])
    inferred_bed = np.minimum(inferred_bed, ws_cell - 0.05)
    use_meas = measured
    bed_ch = np.where(use_meas, bath[rr, cc], inferred_bed)
    rock = rocks[rr, cc]
    bed_ch = np.where(rock, dem[rr, cc], bed_ch)
    bed[rr, cc] = bed_ch
    cls[rr, cc] = np.where(rock, 3, np.where(use_meas, 1, 2))
    boulders = []
    if args.foam_boulders:
        ws_grid = np.full((NY, NX), np.nan); ws_grid[rr, cc] = ws_cell
        bed, cls, boulders = add_foam_boulders(bed, cls, foam & river, rocks, ws_grid, px, py, args.boulder_crest_below_ws_m)
    # --- outputs
    station_grid = np.full((NY, NX), np.nan, np.float32); station_grid[rr, cc] = station
    out.mkdir(parents=True)
    np.savez_compressed(out / 'evidence_grid.npz', bed=bed.astype(np.float32), dem2021=dem.astype(np.float32),
                        bathy2014=bath.astype(np.float32), class_code=cls, river=river, channel=channel, foam=foam & river,
                        rocks=rocks, station=station_grid)
    (out / 'boulders.json').write_text(json.dumps(dict(
        schema='raftsim.colorado.hance_inferred_boulders.v1',
        method='one boulder per lateral cluster of the upstream edge of each >= 4 m2 whitewater patch over inferred bed '
               '(2021 imagery), shifted upstream by its radius; patches within 3 m of an emergent rock are explained by '
               'that rock and skipped; crest at the reference surface minus the stated margin (pour-over assumption)',
        inferred=True, crest_below_ws_m=args.boulder_crest_below_ws_m, boulders=boulders), indent=1) + '\n')
    cl = dict(schema='raftsim.colorado.hance_centreline.v1', crs='EPSG:6404', points_xy_station=[[float(a), float(b_), float(c)] for a, b_, c in zip(px[::2], py[::2], station_c[::2])])
    (out / 'centreline.json').write_text(json.dumps(cl) + '\n')
    prof = dict(station_center_m=centers.tolist(), dem_water_median_m=[None if not np.isfinite(v) else float(v) for v in med],
                ws_reference_m=ws.tolist(), ws_observation=obs_kind.tolist(), ws_reference_method=args.ws_reference, slope=slope.tolist(), normal_depth_m=Hn.tolist(), manning_n=n.tolist(),
                cells_per_bin=cnt.tolist())
    (out / 'profile.json').write_text(json.dumps(prof) + '\n')
    stats = dict(river_cells=int(river.sum()), channel_cells=int(channel.sum()), emergent_rock_cells=int(rocks.sum()),
                 measured_bed_cells=int((cls == 1).sum()), inferred_bed_cells=int((cls == 2).sum()),
                 reach_length_m=float(station_c.max()), ws_upstream_m=float(ws[2]), ws_downstream_m=float(ws[-3]),
                 inferred_depth_m_p10_p50_p90=np.percentile(ws_cell[~use_meas & ~rock] - inferred_bed[~use_meas & ~rock], [10, 50, 90]).tolist(),
                 measured_depth_m_p10_p50_p90=np.percentile(ws_cell[use_meas] - bath[rr[use_meas], cc[use_meas]], [10, 50, 90]).tolist())
    manifest = dict(schema='raftsim.colorado.hance_evidence_grid.v1', crs='EPSG:6404 NAD83(2011) / Arizona Central',
                    vertical='NAD83(2011) ellipsoid heights', grid=dict(x0=X0, y_top=Y1, nx=NX, ny=NY, cell_m=1.0),
                    sources_manifest_sha256=sha(SRC / 'manifest.json'),
                    class_codes={'0': 'dry ground, 2021 DEM (measured)', '1': 'bed, 2014 sonar/total station (measured)',
                                 '2': 'bed, discharge-consistent inference (inferred)', '3': 'emergent rock top, 2021 DEM (measured)',
                                 '4': 'submerged boulder: location from 2021 imagery whitewater, height from a pour-over assumption (inferred)'},
                    parameters=dict(discharge_m3s=Q, ws_reference=args.ws_reference, manning_n_rapid=args.n_rapid, critical_depth_floor=args.critical_depth_floor,
                                    foam_boulders=len(boulders), bed_correction=None if correction is None else str(args.bed_correction),
                                    bed_correction_sha256=None if correction is None else sha(args.bed_correction), manning_n_pool=N_POOL, rapid_slope_threshold=S_RAPID,
                                    bin_m=BIN, ndwi_threshold=0.15, diffusion_decay='60 iterations, factor 0.96'),
                    statistics=stats, measured_bathymetry_epoch='2014-05', surface_epoch='2021-05/06 at ~8,000 cfs',
                    inferred=True, accepted=False)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(stats, indent=1))


def add_foam_boulders(bed, cls, foam, rocks, ws_grid, px, py, crest_below):
    """Inferred submerged boulders from imagery whitewater (class 4).

    Whitewater forms just downstream of an obstacle, so each patch's upstream
    edge marks where flow breaks. Patches are 8-connected components of the
    1 m foam mask; the flow direction is the smoothed centreline tangent.
    """
    from collections import deque
    H, W = foam.shape
    lab = -np.ones((H, W), int); comps = []
    for r0, c0 in zip(*np.nonzero(foam)):
        if lab[r0, c0] >= 0:
            continue
        q = deque([(r0, c0)]); lab[r0, c0] = len(comps); pix = []
        while q:
            r, c = q.popleft(); pix.append((r, c))
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    r2, c2 = r + dr, c + dc
                    if 0 <= r2 < H and 0 <= c2 < W and foam[r2, c2] and lab[r2, c2] < 0:
                        lab[r2, c2] = len(comps); q.append((r2, c2))
        comps.append(np.array(pix))
    near_rock = shifted_or(rocks, 3)
    comps = sorted((p for p in comps if len(p) >= 4), key=len, reverse=True)
    seeds = []
    for k, p in enumerate(comps):
        if np.mean(cls[p[:, 0], p[:, 1]] == 2) <= 0.5:
            continue
        x = X0 + p[:, 1] + 0.5; y = Y1 - p[:, 0] - 0.5
        j = int(np.argmin((px - x.mean()) ** 2 + (py - y.mean()) ** 2))
        a0, a1 = max(j - 15, 0), min(j + 15, len(px) - 1)
        t = np.array([px[a0] - px[a1], py[a0] - py[a1]]); t /= np.linalg.norm(t)  # downstream = towards lower columns
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
        w = np.where(d < rad, np.cos(0.5 * np.pi * d / rad) ** 2, 0.0)
        sub = bed[rs, cs]; cap = np.where(np.isfinite(ws_grid[rs, cs]), ws_grid[rs, cs] - crest_below, sub)
        new = np.where((cls[rs, cs] == 2) | (cls[rs, cs] == 4), np.minimum(sub + q['height_m'] * w, np.maximum(sub, cap)), sub)
        raised = new > sub + 0.05
        bed[rs, cs] = new; cls[rs, cs] = np.where(raised, 4, cls[rs, cs])
    return bed, cls, seeds


def read_geotiff_7z(path):
    """Read the single GeoTIFF inside a 7z archive via Windows bsdtar into memory."""
    import subprocess, tempfile, os
    tmp = Path(tempfile.mkdtemp(prefix='hance7z_'))
    subprocess.run([r'C:\Windows\System32\tar.exe', '-xf', str(path), '-C', str(tmp)], check=True)
    tif = next(p for p in tmp.rglob('*.tif'))
    arr, g, nd = read_geotiff(tif)
    for p in tmp.rglob('*'):
        if p.is_file():
            p.unlink()
    return arr, g, nd


if __name__ == '__main__':
    main()
