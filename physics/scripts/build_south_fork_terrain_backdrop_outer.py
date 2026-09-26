"""Build the outer South Fork terrain backdrop from the repository's 3DEP windows.

The inner backdrop (build_south_fork_terrain_backdrop.py) covers only the 2 m
context grid, which has data in a band around the corridor; beyond it the world
still ended in sky (for example the Coloma valley seen from 9 km). The eight
full-reach windows already hold USGS 3DEP DEM exports
(`production_corridor/full_reach_windows/*/source/3dep_dem.tif`, EPSG:3857,
NAVD88 metres) that reach several kilometres further. This samples them on a
16 m UTM lattice aligned with the context grid, using the finest window that
covers each point; no data is invented beyond the windows.

Inside the context grid the outer mesh is emitted only in a one-cell band along
its edge, where each vertex takes min(3DEP, context-grid minimum over the cell
support) minus the margin, so it stays below the inner backdrop and the
detailed tiles. Registration is checked against the context grid's captured
surface where both exist. Output: backdrop.npz + manifest.json in the render-tile
convention consumed by export_south_fork_composite_tiles.py.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'physics/scripts'))
from build_south_fork_terrain_backdrop import window_min  # noqa: E402
from tiff_numpy import read_geotiff  # noqa: E402

FULL = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
WINDOWS = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/production_corridor/full_reach_windows'
BED = FULL / 'discharge_bed_20260926/bed/coarse_bed_navd88_m.npz'
SURFACE = FULL / 'source_context_extension/captured_surface_navd88_m.tif'
CONTEXT_MANIFEST = FULL / 'source_context_extension/manifest.json'
WORLD_ORIGIN_UTM = (689237.0, 4293073.0)
DATUM_M = 220.0


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# Same WGS84 UTM/Web Mercator formulas as build_south_fork_naip_drape.py
# (that module imports bpy, so they are repeated here).
def utm_to_lonlat(e, n, zone=10):
    a, f, k0 = 6378137.0, 1 / 298.257223563, 0.9996
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    x = e - 500000.0
    m = n / k0
    mu = m / (a * (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256))
    e1 = (1 - np.sqrt(1 - e2)) / (1 + np.sqrt(1 - e2))
    phi1 = (mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * np.sin(2 * mu)
            + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * np.sin(4 * mu)
            + (151 * e1 ** 3 / 96) * np.sin(6 * mu) + (1097 * e1 ** 4 / 512) * np.sin(8 * mu))
    s, c, t = np.sin(phi1), np.cos(phi1), np.tan(phi1)
    n1 = a / np.sqrt(1 - e2 * s * s)
    t1 = t * t
    c1 = ep2 * c * c
    r1 = a * (1 - e2) / (1 - e2 * s * s) ** 1.5
    d = x / (n1 * k0)
    lat = phi1 - (n1 * t / r1) * (d ** 2 / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * ep2) * d ** 4 / 24
                                  + (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * ep2 - 3 * c1 ** 2) * d ** 6 / 720)
    lon0 = np.radians(-183.0 + 6.0 * zone)
    lon = lon0 + (d - (1 + 2 * t1 + c1) * d ** 3 / 6
                  + (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * ep2 + 24 * t1 ** 2) * d ** 5 / 120) / c
    return lon, lat


def lonlat_to_mercator(lon, lat):
    r = 6378137.0
    return r * lon, r * np.log(np.tan(np.pi / 4 + lat / 2))


def mercator_to_lonlat(x, y):
    r = 6378137.0
    return x / r, 2.0 * np.arctan(np.exp(y / r)) - np.pi / 2.0


def lonlat_to_utm(lon, lat, zone=10):
    """Forward WGS84 transverse Mercator (Snyder series), for window extents only."""
    a, f, k0 = 6378137.0, 1 / 298.257223563, 0.9996
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    lon0 = np.radians(-183.0 + 6.0 * zone)
    n = a / np.sqrt(1 - e2 * np.sin(lat) ** 2)
    t = np.tan(lat) ** 2
    c = ep2 * np.cos(lat) ** 2
    aa = np.cos(lat) * (lon - lon0)
    m = a * ((1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * lat
             - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * np.sin(2 * lat)
             + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * np.sin(4 * lat)
             - (35 * e2 ** 3 / 3072) * np.sin(6 * lat))
    e = k0 * n * (aa + (1 - t + c) * aa ** 3 / 6 + (5 - 18 * t + t * t + 72 * c - 58 * ep2) * aa ** 5 / 120) + 500000.0
    nn = k0 * (m + n * np.tan(lat) * (aa * aa / 2 + (5 - t + 9 * c + 4 * c * c) * aa ** 4 / 24
                                      + (61 - 58 * t + t * t + 600 * c - 330 * ep2) * aa ** 6 / 720))
    return e, nn


def bilinear(arr, fx, fy):
    """Sample arr at fractional pixel-centre coordinates; NaN outside or on NaN."""
    h, w = arr.shape
    x0 = np.floor(fx).astype(np.int64)
    y0 = np.floor(fy).astype(np.int64)
    inside = (x0 >= 0) & (y0 >= 0) & (x0 < w - 1) & (y0 < h - 1)
    out = np.full(fx.shape, np.nan)
    xi, yi = x0[inside], y0[inside]
    tx, ty = fx[inside] - xi, fy[inside] - yi
    v00 = arr[yi, xi]; v01 = arr[yi, xi + 1]; v10 = arr[yi + 1, xi]; v11 = arr[yi + 1, xi + 1]
    out[inside] = (v00 * (1 - tx) * (1 - ty) + v01 * tx * (1 - ty) + v10 * (1 - tx) * ty + v11 * tx * ty)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--spacing-cells', type=int, default=8, help='2 m context cells per outer lattice step')
    parser.add_argument('--margin-m', type=float, default=3.0)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'physics/data') and not out.exists(), 'Use a new explicit output folder'
    grid = json.loads(CONTEXT_MANIFEST.read_text())['grid']
    e0, n0 = grid['first_vertex_utm_m']
    cell = float(grid['cell_m'])
    step = args.spacing_cells
    spacing = step * cell

    windows = []
    for path in sorted(WINDOWS.glob('*/source/3dep_dem.tif')):
        arr, geo, nodata = read_geotiff(path)
        arr = arr.astype(np.float64)
        if nodata is not None:
            arr[arr == nodata] = np.nan
        arr[(arr < -100) | (arr > 5000)] = np.nan
        cx, cy = geo['cell_m']
        x0, y0 = geo['corner_utm_m']  # EPSG:3857 tiepoint (reader field name is CRS-agnostic)
        manifest = json.loads((path.parent.parent / 'manifest.json').read_text())
        req = manifest['bounds']['epsg3857_buffered']
        mx, my = (req[0] + req[2]) / 2, (req[1] + req[3]) / 2
        half = max(req[2] - req[0], req[3] - req[1]) / 2
        tiff_extent = [x0, y0 - arr.shape[0] * cy, x0 + arr.shape[1] * cx, y0]
        square_extent = [mx - half, my - half, mx + half, my + half]
        windows.append(dict(name=path.parent.parent.name, path=path, arr=arr, x0=x0, y0=y0, cx=cx, cy=cy,
                            sha256=sha(path), tiff_extent=tiff_extent,
                            square_extent_difference_m=float(max(abs(a - b) for a, b in zip(tiff_extent, square_extent)))))
    windows.sort(key=lambda w: w['cx'])  # finest first
    corners_e, corners_n = [], []
    for w in windows:
        ex = w['tiff_extent']
        xs = np.array([ex[0], ex[2], ex[0], ex[2]]); ys = np.array([ex[1], ex[1], ex[3], ex[3]])
        lon, lat = mercator_to_lonlat(xs, ys)
        e, n = lonlat_to_utm(lon, lat)
        corners_e += list(e); corners_n += list(n)
    col_lo = int(np.floor((min(corners_e) - e0) / spacing)); col_hi = int(np.ceil((max(corners_e) - e0) / spacing))
    row_lo = int(np.floor((n0 - max(corners_n)) / spacing)); row_hi = int(np.ceil((n0 - min(corners_n)) / spacing))
    cols = np.arange(col_lo, col_hi + 1); rows = np.arange(row_lo, row_hi + 1)
    east = e0 + cols * spacing; north = n0 - rows * spacing
    ee, nn = np.meshgrid(east, north)
    lon, lat = utm_to_lonlat(ee, nn)
    mx, my = lonlat_to_mercator(lon, lat)
    dem = np.full(ee.shape, np.nan)
    source_index = np.full(ee.shape, -1, dtype=np.int64)
    for index, w in enumerate(windows):
        fx = (mx - w['x0']) / w['cx'] - 0.5
        fy = (w['y0'] - my) / w['cy'] - 0.5
        sample = bilinear(w['arr'], fx, fy)
        take = np.isnan(dem) & np.isfinite(sample)
        dem[take] = sample[take]
        source_index[take] = index

    with np.load(BED) as data:
        bed = data['coarse_bed_navd88_m'].astype(np.float32)
    lowest = window_min(bed, step)
    surface, _, _ = read_geotiff(SURFACE)
    surface = surface.astype(np.float64)
    # Lattice vertices that coincide with context grid vertices.
    grid_r = rows * step; grid_c = cols * step
    in_grid = ((grid_r >= 0) & (grid_r < bed.shape[0]))[:, None] & ((grid_c >= 0) & (grid_c < bed.shape[1]))[None, :]
    rr = np.clip(grid_r, 0, bed.shape[0] - 1); cc = np.clip(grid_c, 0, bed.shape[1] - 1)
    context_valid = in_grid & np.isfinite(bed[np.ix_(rr, cc)])
    context_low = np.where(in_grid, lowest[np.ix_(rr, cc)], np.nan).astype(np.float64)
    dry_surface = np.where(in_grid, surface[np.ix_(rr, cc)], np.nan)
    dry = in_grid & np.isfinite(dry_surface) & np.isfinite(bed[np.ix_(rr, cc)]) & \
        (np.abs(bed[np.ix_(rr, cc)] - dry_surface) < 1e-3)
    del lowest, surface
    registration = (dem - dry_surface)[dry & np.isfinite(dem)]

    heights = dem - args.margin_m
    heights = np.where(context_valid, np.fmin(heights, context_low - args.margin_m), heights)
    valid = np.isfinite(heights)
    index = -np.ones(heights.shape, dtype=np.int64)
    index[valid] = np.arange(int(valid.sum()))
    a = index[:-1, :-1]; b = index[:-1, 1:]; c = index[1:, :-1]; d = index[1:, 1:]
    covered = context_valid[:-1, :-1] & context_valid[:-1, 1:] & context_valid[1:, :-1] & context_valid[1:, 1:]
    quad = (a >= 0) & (b >= 0) & (c >= 0) & (d >= 0) & ~covered
    tri = np.concatenate([np.stack([a[quad], b[quad], c[quad]], 1), np.stack([b[quad], d[quad], c[quad]], 1)])
    xyz_all = np.stack([ee[valid] - east[0], nn[valid] - north[0], heights[valid] - DATUM_M], 1)
    used = np.zeros(len(xyz_all), dtype=bool); used[tri.ravel()] = True
    remap = -np.ones(len(xyz_all), dtype=np.int64); remap[used] = np.arange(int(used.sum()))
    xyz = xyz_all[used]; tri = remap[tri]
    out.mkdir(parents=True)
    mesh_path = out / 'backdrop.npz'
    np.savez_compressed(mesh_path, xyz_local_m=xyz, triangles=tri)
    origin = [float(east[0]), float(north[0])]
    used_windows = sorted({int(i) for i in source_index[valid & ~np.isnan(dem)].ravel()})
    manifest = dict(
        schema='raftsim.south_fork.cartesian_terrain_tiles.v1',
        purpose='always-loaded non-colliding outer terrain backdrop from repository 3DEP windows',
        measured_source='USGS 3DEP DEM window exports (EPSG:3857, NAVD88 m) already in the repository',
        inferred_presentation=True, collision=False, no_simplification=False,
        spacing_m=spacing, margin_m=args.margin_m,
        sources=[dict(name=w['name'], path=str(w['path'].relative_to(ROOT).as_posix()), sha256=w['sha256'],
                      cell_epsg3857_m=w['cx'], tiff_extent_epsg3857=w['tiff_extent'],
                      tiff_vs_square_request_extent_difference_m=w['square_extent_difference_m'])
                 for w in windows],
        windows_contributing=[windows[i]['name'] for i in used_windows],
        context_bed=str(BED.relative_to(ROOT).as_posix()), context_bed_sha256=sha(BED),
        registration_vs_context_dry_surface=dict(
            vertices=int(registration.size),
            median_m=float(np.median(registration)) if registration.size else None,
            p10_m=float(np.percentile(registration, 10)) if registration.size else None,
            p90_m=float(np.percentile(registration, 90)) if registration.size else None,
            mean_abs_m=float(np.mean(np.abs(registration))) if registration.size else None),
        band_rule='inside the context grid only the edge band is emitted; vertices there take min(3DEP, context minimum) - margin',
        tiles=[dict(name='terrain_backdrop_outer_%dm' % int(spacing), path=str(mesh_path.relative_to(ROOT).as_posix()),
                    sha256=sha(mesh_path), origin_utm_m=origin,
                    actor_translation_cm=[(origin[0] - WORLD_ORIGIN_UTM[0]) * 100.0, -(origin[1] - WORLD_ORIGIN_UTM[1]) * 100.0, 0.0],
                    actor_scale=[1.0, -1.0, 1.0], vertex_count=int(len(xyz)), triangle_count=int(len(tri)))])
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(dict(registration=manifest['registration_vs_context_dry_surface'],
                          windows=[(w['name'][:24], round(w['square_extent_difference_m'], 2)) for w in windows],
                          vertices=len(xyz), triangles=len(tri)), indent=1))


if __name__ == '__main__':
    main()
