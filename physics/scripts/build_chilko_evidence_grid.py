"""Evidence grid for an explicitly selected Chilko construction window.

Sources (physics/data/real_world/chilko_river_bc): LidarBC 1 m bare-earth DEM
(2023; a crop made by crop_lidarbc_dem.py, NAD83(CSRS) / UTM 10N, CGVD2013
heights), four Sentinel-2 L2A windows at gauged flows, the BC Freshwater
Atlas corridor route (chainage) and HYDAT daily flows. The former implicit
43.9-47.9 km window was incorrectly identified as Bidwell-to-White Mile.
Published representative points place those rapids farther upstream; see the
October 6 location ledger. Explicit chainage selects construction coverage,
not surveyed rapid boundaries. Bright-water patches do not establish names.

What is measured and what is inferred:
- terrain: the LiDAR DEM (measured, 1 m; bare earth);
- water surface reference: medians of DEM candidate channel-interior cells
  per 5 m, forced non-increasing (INFERRED, not a hydraulic-surface survey);
  flight window 2023-09-18 to 2023-10-06, lake-outlet flow 57 to 33 m3/s;
- wetted extent: cells within --wet-tolerance-m of that surface, connected to
  the channel (INFERRED, not an independently measured shoreline);
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
from pyproj import Transformer

from build_futaleufu_evidence_grid import bilinear, label_near
from build_pacuare_evidence_grid import arc_resample, edt_inside, foam_boulders, gauss_smooth, pava_nonincreasing
from project_nearest_route import project
from geo_frames import utm
from png_numpy import write_png

ROOT = Path(__file__).resolve().parents[2]
RIVER = ROOT / 'physics/data/real_world/chilko_river_bc'
SRC = RIVER / 'chilko_sources_2026_09'
LOCATIONS = RIVER / 'observed_rapids/catalog_location_evidence_2026_10_06.json'
ROUTE = RIVER / 'production_corridor/chilko_river_lodge_to_taseko_junction/hydrography/route_centerline.geojson'
# Retained for the legacy colour-report import; new geometry uses explicit CRS transforms.
UTM10 = utm(10)
G = 9.81


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_construction_chain(chain, route_length):
    values = np.asarray(chain, dtype=float)
    if (values.shape != (2,) or not np.isfinite(values).all() or
            not 0 <= values[0] < values[1] <= route_length):
        raise ValueError('Explicit ordered construction interval must lie inside the FWA route')
    return values


def imagery_sampling_grid(xc, yc, item):
    """Map DEM cell centres to the actual captured raster, not requested bounds."""
    east, north = np.meshgrid(xc, yc)
    return imagery_sampling_points(east, north, item)


def imagery_sampling_points(east, north, item):
    """Map aligned EPSG:3157 coordinates to verified Sentinel pixel centres."""
    if item.get('epsg') != 32610:
        raise ValueError('Expected captured Sentinel-2 WGS84 / UTM zone 10N')
    reference = item['bands']['blue']
    for name in ('blue', 'green', 'red', 'nir'):
        band = item['bands'][name]
        if any(band[key] != reference[key] for key in ('x0', 'y0', 'cell_m', 'shape')):
            raise ValueError('Sentinel-2 RGB bands must share their actual raster grid')
        shape = np.asarray(band['shape'])
        if (shape.shape != (2,) or np.any(shape < 2) or
                np.any(shape != shape.astype(int)) or band['cell_m'] != 10 or
                not np.isfinite([band['x0'], band['y0']]).all()):
            raise ValueError('Invalid captured RGB raster geometry')
        radiometry = band['raster_bands'][0]
        if (radiometry.get('scale') != 0.0001 or radiometry.get('offset') != -0.1 or
                radiometry.get('nodata') != 0):
            raise ValueError('Unrecognized Sentinel-2 reflectance encoding')
    east, north = np.asarray(east, dtype=float), np.asarray(north, dtype=float)
    if east.shape != north.shape or not east.size:
        raise ValueError('Expected nonempty aligned terrain coordinate arrays')
    east, north = Transformer.from_crs(3157, 32610, always_xy=True).transform(east, north)
    fc = (east - reference['x0']) / reference['cell_m'] - .5
    fr = (reference['y0'] - north) / reference['cell_m'] - .5
    rows, cols = reference['shape']
    # bilinear() clamps. Refuse instead of inventing evidence beyond pixel centres.
    if (not np.isfinite(fr).all() or not np.isfinite(fc).all() or
            fr.min() < 0 or fc.min() < 0 or fr.max() > rows - 1 or fc.max() > cols - 1):
        raise ValueError('Construction window exceeds captured Sentinel-2 cell-centre coverage')
    return fr, fc


def supported_channel_core(strict, interior, water_support, dem, surface):
    """Retain low-relief channel interior, never infer new banks from coarse imagery.

    The 0.25 m allowance is the existing rough-mask tolerance. The DEM-derived
    or independently mapped river interior was already eroded by three metres;
    higher terrain and isolated spectral water cannot enter through this rule.
    This remains explicit bed/shore inference, not measured flight-day shoreline.
    """
    return (interior & ~strict & np.isfinite(surface) &
            (water_support >= .5) & (dem <= surface + .25))


def load_river_planform(path, x0, y_top, nx, ny):
    from affine import Affine
    from rasterio.features import rasterize
    from rasterio.warp import transform_geom
    from capture_chilko_fwa_polygon import validate_polygon
    metadata = json.loads(path.with_suffix('.json').read_text())
    if (metadata.get('schema') != 'raftsim.chilko_fwa_polygon_capture.v1' or
            metadata.get('horizontal_crs') != 'EPSG:4326' or metadata.get('sha256') != sha(path)):
        raise ValueError('Unverified FWA planform identity or coordinate frame')
    data = json.loads(path.read_text())
    validate_polygon(data, metadata['waterbody_key'])
    geometry = transform_geom('EPSG:4326', 'EPSG:3157', data['features'][0]['geometry'])
    mask = rasterize([(geometry, 1)], out_shape=(ny, nx),
                     transform=Affine(1, 0, x0, 0, -1, y_top)).astype(bool)
    if not mask.any():
        raise ValueError('Captured planform does not cover construction window')
    return mask


def correct_inferred_bed(bed, classes, station, surface, correction):
    """Calibrate class-2 bed only, after source and inferred rocks are fixed."""
    source_station = np.asarray(correction['station'], dtype=float)
    delta = np.asarray(correction['delta'], dtype=float)
    if (source_station.ndim != 1 or len(source_station) < 2 or
            delta.shape != source_station.shape or
            not np.isfinite(source_station).all() or not np.isfinite(delta).all() or
            not np.all(np.diff(source_station) > 0)):
        raise ValueError('Bed correction requires finite, increasing station samples')
    if any(a.shape != bed.shape for a in (classes, station, surface)):
        raise ValueError('Bed correction arrays must share one grid')
    apply = classes == 2
    if not all(np.isfinite(a[apply]).all() for a in (bed, station, surface)):
        raise ValueError('Inferred bed correction cells lack finite reference coordinates')
    result = bed.copy()
    result[apply] = np.minimum(
        bed[apply] + np.interp(station[apply], source_station, delta),
        surface[apply] - .05)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--lidar', type=Path, required=True, help='crop_lidarbc_dem.py .npz (with its .json beside it)')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--chain-m', type=float, nargs=2, required=True,
                    help='Explicit FWA construction interval; not named-rapid boundaries')
    ap.add_argument('--margin-m', type=float, default=350.0)
    ap.add_argument('--discharge-m3s', type=float, default=45.0)
    ap.add_argument('--n-pool', type=float, default=0.035)
    ap.add_argument('--n-rapid', type=float, default=0.05)
    ap.add_argument('--min-slope', type=float, default=0.001)
    ap.add_argument('--wet-tolerance-m', type=float, default=0.15)
    ap.add_argument('--anchor-spacing-m', type=float, default=100.0)
    ap.add_argument('--boulder-crest-below-ws-m', type=float, default=0.3)
    ap.add_argument('--bed-correction', type=Path)
    ap.add_argument('--river-polygon', type=Path,
                    help='Hash-verified official FWA planform; additional inferred-core support, not a stage survey')
    args = ap.parse_args()
    out = args.out.resolve()
    assert not out.exists(), 'fresh output folder required'
    Q = args.discharge_m3s
    s0, s1 = args.chain_m

    # ---------------- FWA route (corridor chainage) in UTM 10N
    rj = json.loads(ROUTE.read_text())
    geom = rj['features'][0]['geometry'] if 'features' in rj else rj['geometry']
    lonlat = np.array(geom['coordinates'])[:, :2]
    rx, ry = Transformer.from_crs(4326, 3157, always_xy=True).transform(lonlat[:, 0], lonlat[:, 1])
    rc = np.r_[0, np.cumsum(np.hypot(np.diff(rx), np.diff(ry)))]
    validate_construction_chain(args.chain_m, rc[-1])
    S = np.arange(max(s0 - 1500, 0), min(s1 + 1500, rc[-1]), 4.0)
    X = gauss_smooth(np.interp(S, rc, rx), 3.0); Y = gauss_smooth(np.interp(S, rc, ry), 3.0)
    tx, ty = np.gradient(X), np.gradient(Y); tn = np.hypot(tx, ty)
    LX, LY = -ty / tn, tx / tn

    # ---------------- window (north up, 1 m) inside the LiDAR crop
    lz = np.load(args.lidar); lmeta = json.loads(args.lidar.with_suffix('.json').read_text())
    if (lmeta.get('mixed_resolution_terrain', False) or
            lmeta.get('npz_sha256') != sha(args.lidar) or
            lmeta.get('crs') != 'EPSG:3157 NAD83(CSRS) / UTM zone 10N' or
            lmeta.get('vertical') != 'CGVD2013 (EPSG:6647)' or
            lmeta.get('cell_m') != 1. or float(lz['cell_m']) != 1.):
        raise ValueError('Lidar crop identity, datum or one-metre spacing not verified')
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
    fm = json.loads((SRC / 'sentinel2/fetch_manifest.json').read_text())
    for item in fm['items']:
        imagery_sampling_grid(xc, yc, item)
        if sha(SRC / 'sentinel2' / item['npz']) != item['npz_sha256']:
            raise ValueError('Captured Sentinel-2 input has changed')
        with np.load(SRC / 'sentinel2' / item['npz']) as captured:
            for name in ('blue', 'green', 'red', 'nir'):
                values = captured[name]
                if list(values.shape) != item['bands'][name]['shape'] or np.any(values == 0):
                    raise ValueError('Captured RGB shape mismatch or unmasked nodata')

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

    # ---------------- inferred surface reference: DEM over candidate channel interior
    # A bare-earth DEM over water is not a measured hydraulic surface or bathymetry.
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

    # Spectral support is checked in addition to (not instead of) the fine DEM
    # core. These higher-flow dates cannot independently define flight-day banks.
    white_frac = np.zeros((NY, NX)); water_support = np.zeros((NY, NX))
    rgb = None; dates = []
    for it in fm['items']:
        with np.load(SRC / 'sentinel2' / it['npz']) as z:
            B, Gn, R, N = [z[k].astype(np.float32) * 1e-4 - 0.1
                           for k in ('blue', 'green', 'red', 'nir')]
        white = (B > 0.20) & (Gn > 0.20) & (R > 0.16) & (np.abs(B - R) < 0.12)
        spectral_water = ((Gn - N) / np.maximum(Gn + N, 1e-6) > .1) & (N < .12)
        FR, FC = imagery_sampling_grid(xc, yc, it)
        white_frac += bilinear(white.astype(np.float32), FR, FC)
        water_support += bilinear(spectral_water.astype(np.float32), FR, FC)
        if it['datetime'][:10] == '2023-08-16':
            rgb = np.stack([bilinear(np.clip(ch / 0.25, 0, 1) ** (1 / 2.2), FR, FC) for ch in (R, Gn, B)], -1)
            rgb = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
        dates.append(it['datetime'][:10])
        del FR, FC
    white_frac /= len(fm['items']); water_support /= len(fm['items'])
    strict = (np.isfinite(ws_cell) & (np.abs(np.nan_to_num(lat_grid, nan=1e9)) < 120) &
              (dem <= np.nan_to_num(ws_cell, nan=-1e9) + args.wet_tolerance_m))
    planform_core = np.zeros_like(interior)
    if args.river_polygon:
        mapped = load_river_planform(args.river_polygon, X0, Y1, NX, NY)
        planform_core = (edt_inside(mapped) >= 3) & (np.abs(np.nan_to_num(lat_grid, nan=1e9)) < 120)
    retained_core = supported_channel_core(strict, interior | planform_core, water_support, dem, ws_cell)
    river = label_near(strict | retained_core, seed | wet0 & interior)
    channel = river.copy()
    reach = (mchain >= s0) & (mchain <= s1)
    reach_idx = np.nonzero(reach)[0]
    a_st = np.arange(reach_idx[0] - args.anchor_spacing_m, reach_idx[-1] + args.anchor_spacing_m + 1, args.anchor_spacing_m)
    a_st = a_st[(a_st >= 0) & (a_st < M)]
    a_z = ws_m[a_st.astype(int)]
    keep = np.r_[True, np.diff(a_z) < -0.01]
    a_st, a_z = a_st[keep], a_z[keep]

    # ---------------- Sentinel-2 whitewater (appearance) and colour on the 1 m grid
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
    bed[rv] = bed_rv; cls[rv] = 2
    ws_grid = np.where(rv, ws_cell, np.nan)
    bed, cls, boulders = foam_boulders(bed, cls, foam, rocks, ws_grid, st_grid, mxs, mys, X0, Y1, args.boulder_crest_below_ws_m)
    # Infer rocks once from the uncalibrated construction bed. Moving this above
    # foam_boulders changes its seed-admission threshold and invents extra rocks
    # during a supposedly depth-only calibration.
    if corr is not None:
        bed = correct_inferred_bed(bed, cls, st_grid, ws_cell, corr)

    # ---------------- outputs
    out.mkdir(parents=True)
    station_grid = np.where(rv, st_grid, np.nan).astype(np.float32)
    np.savez_compressed(out / 'evidence_grid.npz', bed=bed.astype(np.float32), dem2021=dem.astype(np.float32), dem=dem.astype(np.float32),
                        lidar=dem.astype(np.float32), bathy2014=np.full((NY, NX), np.nan, np.float32), class_code=cls, river=river,
                        channel=channel, foam=foam, rocks=rocks, bars=bars, station=station_grid, lateral=lat_grid.astype(np.float32),
                        ws=np.where(channel, ws_cell, np.nan).astype(np.float32), white_fraction=white_frac.astype(np.float32),
                        spectral_water_support=water_support.astype(np.float32), retained_inferred_core=retained_core & river,
                        mapped_planform_core=planform_core)
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
        station_center_m=centers.tolist(), ws_reference_m=wsb.tolist(), ws_reference_method='inferred_dem_channel_surface_pava_5m_not_water_survey',
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
                 foam_boulders=len(boulders), sentinel2_dates=dates,
                 retained_inferred_core_cells=int((retained_core & river).sum()))
    manifest = dict(
        schema='raftsim.chilko.lava_canyon_evidence_grid.v1', crs='EPSG:3157 NAD83(CSRS) / UTM zone 10N',
        vertical='CGVD2013 orthometric metres (LidarBC)',
        grid=dict(x0=X0, y_top=Y1, nx=NX, ny=NY, cell_m=1.0),
        inputs=dict(lidar_crop=dict(npz=args.lidar.name, sha256=sha(args.lidar), tiles=lmeta['tiles']),
                    sentinel2={it['npz']: it['npz_sha256'] for it in fm['items']},
                    route=dict(path=ROUTE.relative_to(ROOT).as_posix(), sha256=sha(ROUTE)),
                    river_planform=None if not args.river_polygon else dict(
                        path=args.river_polygon.resolve().relative_to(ROOT).as_posix(),
                        sha256=sha(args.river_polygon), metadata_sha256=sha(args.river_polygon.with_suffix('.json')))),
        sources_manifest_sha256=sha(SRC / 'manifest.json'),
        sampling=dict(route_transform='EPSG:4326 to EPSG:3157, always_xy',
                      imagery_transform='EPSG:3157 to EPSG:32610, always_xy',
                      imagery_origin='captured band x0/y0/cell_m, not requested crop bounds',
                      imagery_manifest_sha256=sha(SRC / 'sentinel2/fetch_manifest.json'),
                      generator_sha256=sha(Path(__file__)),
                      hydraulic_surface_measured=False),
        geographic_scope=dict(kind='explicit_fwa_construction_interval_not_rapid_bounds',
                              location_ledger=LOCATIONS.relative_to(ROOT).as_posix(),
                              location_ledger_sha256=sha(LOCATIONS),
                              rapid_names_assigned=False,
                              supersedes_interpretation='Old 43.9-47.9 km Bidwell/White Mile identification is rejected'),
        class_codes={'0': 'dry ground: LidarBC 1 m bare-earth DEM (measured), including emergent rocks and bars above the flight-day surface',
                     '2': 'bed: discharge-consistent depth below an inferred DEM-derived surface reference (not bathymetric survey)',
                     '4': 'submerged boulder: location from Sentinel-2 whitewater, height from a pour-over assumption (inferred)'},
        parameters=dict(discharge_m3s=Q, discharge_source=('LiDAR flight window 2023-09-18 to 2023-10-06: 08MA002 lake-outlet flow 57 to 33 m3/s '
                                                            '(mean about 45); tributary gain to the reach unmeasured'),
                        n_pool=args.n_pool, n_rapid=args.n_rapid, min_slope=args.min_slope, wet_tolerance_m=args.wet_tolerance_m,
                        anchor_spacing_m=args.anchor_spacing_m, chain_m=list(args.chain_m), margin_m=args.margin_m,
                        boulder_crest_below_ws_m=args.boulder_crest_below_ws_m,
                        retained_core_rule=dict(ndwi_min=.1, nir_max=.12, mean_spectral_support_min=.5,
                                                rough_interior_erosion_m=3., dem_surface_allowance_m=.25,
                                                mapped_planform_core_erosion_m=3. if args.river_polygon else None,
                                                independent_shoreline_measurement=False),
                        bed_correction=None if corr is None else args.bed_correction.resolve().relative_to(ROOT).as_posix(),
                        bed_correction_scope='class_2_only_after_boulder_inference',
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
