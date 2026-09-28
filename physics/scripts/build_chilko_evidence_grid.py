"""Evidence grid for the Chilko River, Bidwell Rapid to White Mile (numpy only).

Sources (physics/data/real_world/chilko_river_bc): LidarBC 1 m bare-earth DEM
(2023; a crop made by crop_lidarbc_dem.py, NAD83(CSRS) / UTM 10N, CGVD2013
heights), four Sentinel-2 L2A windows at gauged flows, the BC Freshwater
Atlas corridor route (chainage) and HYDAT daily flows. The reach is corridor
chainage 43.9-47.9 km: Bidwell Rapid (a persistent Sentinel-2 whitewater run
at 44.6-44.8 km, about 5 km below Bidwell Creek as the guidebooks describe)
to the head of White Mile.

What is measured and what is inferred:
- terrain: the LiDAR DEM (measured, 1 m; bare earth);
- water surface: the DEM over the river is the water surface on the flight
  days (2023-09-18 to 2023-10-06; lake-outlet flow 57 falling to 33 m3/s):
  the median of channel-interior cells per 5 m of station, forced
  non-increasing (measured; flow known only as that range);
- wetted extent: cells within --wet-tolerance-m of that surface, connected to
  the channel (measured at the flight flow);
- whitewater: Sentinel-2 bright neutral water, mean over the four dates
  (measured appearance at 70-167 m3/s);
- bed: discharge-consistent depth below the surface for --discharge-m3s on a
  smooth section (INFERRED; LiDAR does not see through the water);
- submerged boulders at the upstream edges of whitewater patches (INFERRED).
Emergent rocks and bars above the flight-day surface are LiDAR terrain.

Outputs (the Pacuare/Futaleufu layout, for build_curvilinear_river_scenario.py).
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from build_futaleufu_evidence_grid import bilinear, label_near
from build_pacuare_evidence_grid import arc_resample, edt_inside, foam_boulders, gauss_smooth, pava_nonincreasing, project
from geo_frames import tm_forward, utm
from png_numpy import write_png

ROOT = Path(__file__).resolve().parents[2]
RIVER = ROOT / 'physics/data/real_world/chilko_river_bc'
SRC = RIVER / 'chilko_sources_2026_09'
ROUTE = RIVER / 'production_corridor/chilko_river_lodge_to_taseko_junction/hydrography/route_centerline.geojson'
UTM10 = utm(10)
G = 9.81


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--lidar', type=Path, required=True, help='crop_lidarbc_dem.py .npz (with its .json beside it)')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--chain-m', type=float, nargs=2, default=(43900.0, 47900.0))
    ap.add_argument('--margin-m', type=float, default=350.0)
    ap.add_argument('--discharge-m3s', type=float, default=45.0)
    ap.add_argument('--n-pool', type=float, default=0.035)
    ap.add_argument('--n-rapid', type=float, default=0.05)
    ap.add_argument('--min-slope', type=float, default=0.001)
    ap.add_argument('--wet-tolerance-m', type=float, default=0.15)
    ap.add_argument('--anchor-spacing-m', type=float, default=100.0)
    ap.add_argument('--boulder-crest-below-ws-m', type=float, default=0.3)
    ap.add_argument('--bed-correction', type=Path)
    args = ap.parse_args()
    out = args.out.resolve()
    assert not out.exists(), 'fresh output folder required'
    Q = args.discharge_m3s
    s0, s1 = args.chain_m

    # ---------------- FWA route (corridor chainage) in UTM 10N
    rj = json.loads(ROUTE.read_text())
    geom = rj['features'][0]['geometry'] if 'features' in rj else rj['geometry']
    lonlat = np.array(geom['coordinates'])[:, :2]
    rx, ry = tm_forward(lonlat[:, 0], lonlat[:, 1], UTM10)
    rc = np.r_[0, np.cumsum(np.hypot(np.diff(rx), np.diff(ry)))]
    S = np.arange(max(s0 - 1500, 0), min(s1 + 1500, rc[-1]), 4.0)
    X = gauss_smooth(np.interp(S, rc, rx), 3.0); Y = gauss_smooth(np.interp(S, rc, ry), 3.0)
    tx, ty = np.gradient(X), np.gradient(Y); tn = np.hypot(tx, ty)
    LX, LY = -ty / tn, tx / tn

    # ---------------- window (north up, 1 m) inside the LiDAR crop
    lz = np.load(args.lidar); lmeta = json.loads(args.lidar.with_suffix('.json').read_text())
    lx0, ly1 = float(lz['x0']), float(lz['y_top']); lh = lz['height_m']
    rs = (S >= s0) & (S <= s1)
    X0 = float(np.floor(X[rs].min() - args.margin_m)); X1 = float(np.ceil(X[rs].max() + args.margin_m))
    Y0 = float(np.floor(Y[rs].min() - args.margin_m)); Y1 = float(np.ceil(Y[rs].max() + args.margin_m))
    NX, NY = int(X1 - X0), int(Y1 - Y0)
    c0, r0 = int(X0 - lx0), int(ly1 - Y1)
    assert c0 >= 0 and r0 >= 0 and c0 + NX <= lh.shape[1] and r0 + NY <= lh.shape[0], 'window must lie inside the LiDAR crop'
    dem = lh[r0:r0 + NY, c0:c0 + NX].astype(np.float64)
    assert np.isfinite(dem).all(), 'LiDAR gap inside the window'
    print(f'window {X0:.0f}-{X1:.0f} E, {Y0:.0f}-{Y1:.0f} N ({NX} x {NY} m)', flush=True)
    xc = X0 + np.arange(NX) + 0.5; yc = Y1 - np.arange(NY) - 0.5

    def cells(px, py):
        c = np.floor(px - X0).astype(int); r = np.floor(Y1 - py).astype(int)
        ok = (c >= 0) & (c < NX) & (r >= 0) & (r < NY)
        return r, c, ok

    # ---------------- rough surface and wetted extent from the route
    lat_s = np.arange(-60, 61, 1.0)
    low = np.full(len(S), np.nan)
    for i in range(len(S)):
        r, c, ok = cells(X[i] + lat_s * LX[i], Y[i] + lat_s * LY[i])
        if ok.sum() > 20:
            low[i] = np.percentile(dem[r[ok], c[ok]], 3)
    have = np.isfinite(low)
    ws0 = np.interp(np.arange(len(S)), np.nonzero(have)[0], pava_nonincreasing(low[have], np.ones(have.sum())))
    ws0_at = lambda chain: np.interp(chain, S, ws0)
    # route station of every cell (nearest route sample, coarse) for the rough mask
    CE, CN = np.meshgrid(xc, yc)
    rough_st, rough_lat = project(CE.ravel(), CN.ravel(), X, Y, S, LX, LY)
    rough_st = rough_st.reshape(NY, NX); rough_lat = rough_lat.reshape(NY, NX)
    near = np.abs(rough_lat) < 100
    wet0 = near & (dem <= ws0_at(rough_st) + 0.25)
    seed = np.zeros((NY, NX), bool)
    r, c, ok = cells(X, Y); seed[r[ok], c[ok]] = True
    wet0 = label_near(wet0, seed)

    # ---------------- midline from the wetted extent along route normals
    mids = []
    lat_m = np.arange(-120, 121, 1.0)
    for i in range(0, len(S), 2):
        r, c, ok = cells(X[i] + lat_m * LX[i], Y[i] + lat_m * LY[i])
        if ok.sum() < len(lat_m) * 0.8:
            continue
        v = np.zeros(len(lat_m), bool); v[ok] = wet0[r[ok], c[ok]]
        if not v.any():
            continue
        edges = np.flatnonzero(np.diff(np.r_[0, v.astype(int), 0]))
        runs = list(zip(edges[::2], edges[1::2] - 1))
        best = min(runs, key=lambda ab: 0 if lat_m[ab[0]] <= 0 <= lat_m[ab[1]] else min(abs(lat_m[ab[0]]), abs(lat_m[ab[1]])))
        if min(abs(lat_m[best[0]]), abs(lat_m[best[1]])) > 40 and not lat_m[best[0]] <= 0 <= lat_m[best[1]]:
            continue
        m = 0.5 * (lat_m[best[0]] + lat_m[best[1]])
        mids.append((X[i] + m * LX[i], Y[i] + m * LY[i]))
    mids = np.array(mids)
    mxs, mys, _ = arc_resample(gauss_smooth(mids[:, 0], 4.0), gauss_smooth(mids[:, 1], 4.0), 1.0)
    mxs, mys = gauss_smooth(mxs, 10.0), gauss_smooth(mys, 10.0)
    mxs, mys, _ = arc_resample(mxs, mys, 1.0)
    mchain = np.maximum.accumulate(project(mxs, mys, X, Y, S, LX, LY)[0])
    mS = np.arange(len(mxs), dtype=float)
    mtx, mty = np.gradient(mxs), np.gradient(mys); mtn = np.hypot(mtx, mty)
    mLX, mLY = -mty / mtn, mtx / mtn
    M = len(mxs)

    # ---------------- station / lateral per cell (quad painting on the midline)
    st_grid = np.full((NY, NX), np.nan); lat_grid = np.full((NY, NX), np.nan)
    LMAX = 250.0
    for i in range(M - 1):
        pts = np.array([[mxs[i] + a * mLX[i], mys[i] + a * mLY[i]] for a in (-LMAX, LMAX)] +
                       [[mxs[i + 1] + a * mLX[i + 1], mys[i + 1] + a * mLY[i + 1]] for a in (LMAX, -LMAX)])
        a0 = max(int(np.floor(pts[:, 0].min() - X0)), 0); a1 = min(int(np.ceil(pts[:, 0].max() - X0)), NX)
        b0 = max(int(np.floor(Y1 - pts[:, 1].max())), 0); b1 = min(int(np.ceil(Y1 - pts[:, 1].min())), NY)
        if a1 <= a0 or b1 <= b0:
            continue
        ex = CE[b0:b1, a0:a1]; ey = CN[b0:b1, a0:a1]
        a_ = (ex - mxs[i]) * mtx[i] / mtn[i] + (ey - mys[i]) * mty[i] / mtn[i]
        seglen = np.hypot(mxs[i + 1] - mxs[i], mys[i + 1] - mys[i])
        lat_ = (ex - mxs[i]) * mLX[i] + (ey - mys[i]) * mLY[i]
        inq = (a_ >= 0) & (a_ < seglen) & (np.abs(lat_) <= LMAX)
        sub_s = st_grid[b0:b1, a0:a1]; sub_l = lat_grid[b0:b1, a0:a1]
        closer = inq & (~np.isfinite(sub_l) | (np.abs(lat_) < np.abs(sub_l)))
        sub_s[closer] = mS[i] + a_[closer] * (mS[i + 1] - mS[i]) / max(seglen, 1e-9)
        sub_l[closer] = lat_[closer]
    del CE, CN
    st_i = np.clip(np.round(np.nan_to_num(st_grid, nan=-1)).astype(int), -1, M - 1)

    # ---------------- measured water surface: LiDAR over the channel interior per 5 m
    interior = wet0 & (edt_inside(wet0) >= 3) & (st_i >= 0)
    b5 = np.where(interior, st_i // 5, -1)
    nb5 = M // 5 + 1
    h5 = np.full(nb5, np.nan); n5 = np.zeros(nb5)
    order = np.argsort(b5.ravel()); keys = b5.ravel()[order]; vals = dem.ravel()[order]
    starts = np.searchsorted(keys, np.arange(nb5)); ends = np.searchsorted(keys, np.arange(nb5), side='right')
    for k in range(nb5):
        if ends[k] - starts[k] >= 8:
            h5[k] = np.median(vals[starts[k]:ends[k]]); n5[k] = ends[k] - starts[k]
    have5 = np.isfinite(h5)
    ws5 = np.full(nb5, np.nan)
    ws5[have5] = pava_nonincreasing(h5[have5], n5[have5])
    ws_m = np.interp(np.arange(M), np.nonzero(have5)[0] * 5.0 + 2.5, ws5[have5])
    ws_cell = np.where(np.isfinite(st_grid), ws_m[np.clip(st_i, 0, M - 1)], np.nan)
    river = label_near(np.isfinite(ws_cell) & (np.abs(np.nan_to_num(lat_grid, nan=1e9)) < 120) &
                       (dem <= np.nan_to_num(ws_cell, nan=-1e9) + args.wet_tolerance_m), seed | wet0 & interior)
    channel = river.copy()
    reach = (mchain >= s0) & (mchain <= s1)
    reach_idx = np.nonzero(reach)[0]
    a_st = np.arange(reach_idx[0] - args.anchor_spacing_m, reach_idx[-1] + args.anchor_spacing_m + 1, args.anchor_spacing_m)
    a_st = a_st[(a_st >= 0) & (a_st < M)]
    a_z = ws_m[a_st.astype(int)]
    keep = np.r_[True, np.diff(a_z) < -0.01]
    a_st, a_z = a_st[keep], a_z[keep]

    # ---------------- Sentinel-2 whitewater (appearance) and colour on the 1 m grid
    fm = json.loads((SRC / 'sentinel2/fetch_manifest.json').read_text())
    white_frac = np.zeros((NY, NX)); rgb = None; dates = []
    for it in fm['items']:
        w = it['window_utm_m']; z = np.load(SRC / 'sentinel2' / it['npz'])
        B, Gn, R = [z[k].astype(np.float32) * 1e-4 - 0.1 for k in ('blue', 'green', 'red')]
        white = (B > 0.20) & (Gn > 0.20) & (R > 0.16) & (np.abs(B - R) < 0.12)
        fc = (xc - w['xmin']) / 10.0 - 0.5; fr = (w['ymax'] - yc) / 10.0 - 0.5
        FR, FC = np.meshgrid(fr, fc, indexing='ij')
        white_frac += bilinear(white.astype(np.float32), FR, FC)
        if it['datetime'][:10] == '2023-08-16':
            rgb = np.stack([bilinear(np.clip(ch / 0.25, 0, 1) ** (1 / 2.2), FR, FC) for ch in (R, Gn, B)], -1)
            rgb = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
        dates.append(it['datetime'][:10])
        del FR, FC
    white_frac /= len(fm['items'])
    foam = river & (white_frac >= 0.25)
    rocks = np.zeros_like(river); bars = np.zeros_like(river)
    wet_at = np.bincount(st_i[river & (st_i >= 0)], minlength=M).astype(float)
    foam_at = np.bincount(st_i[foam & (st_i >= 0)], minlength=M).astype(float)
    share = gauss_smooth(np.where(wet_at > 3, foam_at / np.maximum(wet_at, 1), 0.0), 6.0)

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
    haveb = sum_f53 > 0
    Hn = np.full(nb, np.nan)
    Hn[haveb] = (Q * nman[haveb] * 2.0 / (np.sqrt(slope[haveb]) * sum_f53[haveb])) ** 0.6
    hc = ((Q / np.maximum(width, 1.0)) ** 2 / G) ** (1 / 3)
    mean_f = np.where(haveb, np.bincount(s_bin[rv], weights=fshape_all[rv], minlength=nb) / np.maximum(np.bincount(s_bin[rv], minlength=nb), 1), 1.0)
    Hn = np.where(haveb, np.maximum(Hn, hc / np.maximum(mean_f, 0.3)), np.nan)
    Hn = gauss_smooth(np.interp(np.arange(nb), np.nonzero(haveb)[0], Hn[haveb]), 3.0)
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
                        lidar=dem.astype(np.float32), bathy2014=np.full((NY, NX), np.nan, np.float32), class_code=cls, river=river,
                        channel=channel, foam=foam, rocks=rocks, bars=bars, station=station_grid, lateral=lat_grid.astype(np.float32),
                        ws=np.where(channel, ws_cell, np.nan).astype(np.float32), white_fraction=white_frac.astype(np.float32))
    np.savez_compressed(out / 'sentinel2_rgb.npz', rgb=rgb)
    sel = (mS >= reach_idx[0] - 400) & (mS <= reach_idx[-1] + 400)
    (out / 'centreline.json').write_text(json.dumps(dict(
        schema='raftsim.chilko.lava_canyon_midline.v1', crs='EPSG:3157 NAD83(CSRS) / UTM zone 10N',
        method='midline of the LiDAR-surface wetted extent along the FWA route normals (Gaussian sigma 10 m), 1 m arc length; '
               'station = midline arc length from its upstream start',
        reach_station_m=[float(reach_idx[0]), float(reach_idx[-1])],
        points_xy_station=[[float(a), float(b_), float(c)] for a, b_, c in zip(mxs[sel][::2], mys[sel][::2], mS[sel][::2])],
        corridor_chain_m=[float(v) for v in mchain[sel][::2]])) + '\n')
    centers = np.arange(nb) * 2.0
    (out / 'profile.json').write_text(json.dumps(dict(
        station_center_m=centers.tolist(), ws_reference_m=wsb.tolist(), ws_reference_method='lidar_2023_water_surface_pava_5m',
        anchors=[dict(station_m=float(s_), corridor_chain_m=float(np.interp(s_, mS, mchain)), elevation_m=float(z_)) for s_, z_ in zip(a_st, a_z)],
        lidar_surface_5m=[[k * 5.0 + 2.5, float(h5[k]), float(ws5[k])] for k in range(nb5) if np.isfinite(h5[k])],
        whitewater_share=[float(v) for v in share[::2]], slope=slope.tolist(), normal_depth_m=Hn.tolist(), manning_n=nman.tolist(),
        wetted_width_m=width.tolist())) + '\n')
    (out / 'boulders.json').write_text(json.dumps(dict(
        schema='raftsim.chilko.inferred_boulders.v1', inferred=True, crest_below_ws_m=args.boulder_crest_below_ws_m,
        method='one boulder per lateral cluster of the upstream edge of each >= 4 m2 Sentinel-2 whitewater patch (10 m imagery, '
               'bilinear to 1 m) over inferred bed, shifted upstream by its radius; crest at the surface minus the margin',
        boulders=boulders, emergent_rocks=[]), indent=1) + '\n')
    inreach = rv & (station_grid >= reach_idx[0]) & (station_grid <= reach_idx[-1])
    stats = dict(window=dict(x0=X0, y_top=Y1, nx=NX, ny=NY), channel_cells=int(channel.sum()), wetted_cells=int(river.sum()),
                 whitewater_cells=int(foam.sum()), reach_station_m=[float(reach_idx[0]), float(reach_idx[-1])],
                 reach_corridor_chain_m=[float(mchain[reach_idx[0]]), float(mchain[reach_idx[-1]])],
                 ws_reach_m=[float(ws_m[reach_idx[0]]), float(ws_m[reach_idx[-1]])],
                 anchors=[(float(s_), float(z_)) for s_, z_ in zip(a_st, a_z)],
                 inferred_depth_m_p10_p50_p90=np.percentile((ws_cell - bed)[inreach & (cls == 2)], [10, 50, 90]).tolist(),
                 wetted_width_reach_m_p10_p50_p90=np.percentile(width[reach_idx[0] // 2:reach_idx[-1] // 2], [10, 50, 90]).tolist(),
                 foam_boulders=len(boulders), sentinel2_dates=dates)
    manifest = dict(
        schema='raftsim.chilko.lava_canyon_evidence_grid.v1', crs='EPSG:3157 NAD83(CSRS) / UTM zone 10N',
        vertical='CGVD2013 orthometric metres (LidarBC)',
        grid=dict(x0=X0, y_top=Y1, nx=NX, ny=NY, cell_m=1.0),
        inputs=dict(lidar_crop=dict(npz=args.lidar.name, sha256=sha(args.lidar), tiles=lmeta['tiles']),
                    sentinel2={it['npz']: it['npz_sha256'] for it in fm['items']},
                    route=dict(path=ROUTE.relative_to(ROOT).as_posix(), sha256=sha(ROUTE))),
        sources_manifest_sha256=sha(SRC / 'manifest.json'),
        class_codes={'0': 'dry ground: LidarBC 1 m bare-earth DEM (measured), including emergent rocks and bars above the flight-day surface',
                     '2': 'bed: discharge-consistent depth below the LiDAR water surface (inferred)',
                     '4': 'submerged boulder: location from Sentinel-2 whitewater, height from a pour-over assumption (inferred)'},
        parameters=dict(discharge_m3s=Q, discharge_source=('LiDAR flight window 2023-09-18 to 2023-10-06: 08MA002 lake-outlet flow 57 to 33 m3/s '
                                                            '(mean about 45); tributary gain to the reach unmeasured'),
                        n_pool=args.n_pool, n_rapid=args.n_rapid, min_slope=args.min_slope, wet_tolerance_m=args.wet_tolerance_m,
                        anchor_spacing_m=args.anchor_spacing_m, chain_m=list(args.chain_m), margin_m=args.margin_m,
                        boulder_crest_below_ws_m=args.boulder_crest_below_ws_m,
                        bed_correction=None if corr is None else args.bed_correction.resolve().relative_to(ROOT).as_posix(),
                        bed_correction_sha256=None if corr is None else sha(args.bed_correction)),
        statistics=stats, inferred=True, accepted=False)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    img = rgb.copy()
    img[river & ~foam] = (img[river & ~foam] * 0.5 + np.array([0, 40, 120]) * 0.5).astype(np.uint8)
    img[foam] = (255, 255, 255)
    img[cls == 4] = (230, 60, 60)
    write_png(out / 'classes.png', img[::2, ::2])
    gy, gx = np.gradient(dem); n = np.dstack([-gx, gy, np.ones_like(dem)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    shade = np.clip(n @ (np.array([-0.5, 0.5, 0.7]) / np.linalg.norm([-0.5, 0.5, 0.7])), 0, 1)
    depth = np.clip(np.nan_to_num(ws_cell - bed) / 5.0, 0, 1)
    rgbd = np.dstack([shade * 210] * 3)
    rgbd[river] = np.stack([20 + 0 * depth, 60 + 120 * (1 - depth), 120 + 135 * depth], -1)[river]
    write_png(out / 'terrain_depth.png', rgbd[::2, ::2].astype(np.uint8))
    print(json.dumps(stats, indent=1))


if __name__ == '__main__':
    main()
