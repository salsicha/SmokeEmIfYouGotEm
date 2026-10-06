"""Interpreted rock envelope for the Troublemaker captured-rock solid.

The installed solid (``original_return_rock_cap.npz``) triangulates individual
2019 LiDAR returns selected in 0.5 m bins with a 1 m maximum edge. About a
third of its roof is steeper than 60 degrees: narrow 1.5-2.5 m pyramids that
render as a field of spikes and stand up to 2.5 m above the 1 m hydraulic bed
cooked from the same geometry. Most selected returns are class 1
(unclassified), so vegetation or noise returns cannot be excluded per point.

This script does NOT relabel or delete returns. It derives an explicitly
interpreted envelope: the grey-scale morphological opening of the roof TIN by
a paraboloid of radius ``RADIUS_M``. LiDAR cannot see through rock, so the rock
surface lies at or below every return; the opening is the highest surface at
or below the returns whose convex curvature radius is at least ``RADIUS_M``.
The radius is fixed a priori at the capture's own resolution limit (the 1 m
maximum triangle edge): convex features narrower than that are not resolved
by the sampling, so the capture cannot distinguish them from single-return
artefacts.

Consistency with the installed hydraulics (the cooked bed/flow arrays are not
modified):
* a vertex in a 1 m cell that is dry in every retained frame of the installed
  4900-5400 s cook may only be lowered while staying at least
  ``WATER_MARGIN_M`` above the highest cooked water surface of any wet cell
  within ``WET_RADIUS_M``, so no dry rock newly meets the rendered water;
* a vertex in a cell the solver keeps wet may be lowered, but never below that
  cell's hydraulic bed. The solver already has water flowing there, so a
  sub-cell spike standing above the water was the inconsistency, not the
  lowered envelope.
Topology, XY, the internal floor and the inferred walls' footprint are
unchanged; wall tops follow their boundary roof vertices.

Run with any Python that has numpy (for example Blender's bundled Python).
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
CAP = BASE / 'full_reach/source_matched_20260917/original_return_rock_cap.npz'
CAP_MANIFEST = BASE / 'full_reach/source_matched_20260917/rock_cap_manifest.json'
HYDRAULIC_MAP = BASE / 'full_reach/hydraulic_regions_context/coordinate_map.json'
ATLAS = ROOT / 'tmp/control-ablation-runtime-4950s-v1-20260917/atlas'
COOK = ROOT / 'tmp/control-ablation-4900to5400s-workers8-v1-20260917'
CAP_SHA256 = '78f77b67c64dc98094522ad2a8362edd0bfeab422816c90dc668e2cc5dd2baeb'

RADIUS_M = 1.0          # a priori: the capture's 1 m maximum triangle edge
GRID_M = 0.1            # raster spacing for the opening
WINDOW_M = 2.5          # paraboloid penalty 3.1 m at the window edge
WET_RADIUS_M = 1.5      # nearby water that bounds how far a vertex may drop
WATER_MARGIN_M = 0.3    # lowered rock stays this far above nearby cooked water
DRY_TOLERANCE_M = 1e-3


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rasterize_tin(vertices, triangles, spacing):
    lo = vertices[:, :2].min(axis=0) - spacing
    hi = vertices[:, :2].max(axis=0) + spacing
    nx = int(np.ceil((hi[0] - lo[0]) / spacing)) + 1
    ny = int(np.ceil((hi[1] - lo[1]) / spacing)) + 1
    grid = np.full((ny, nx), np.nan)
    for tri in triangles:
        p = vertices[tri]
        x0, y0 = p[:, :2].min(axis=0)
        x1, y1 = p[:, :2].max(axis=0)
        i0, i1 = int(np.floor((x0 - lo[0]) / spacing)), int(np.ceil((x1 - lo[0]) / spacing))
        j0, j1 = int(np.floor((y0 - lo[1]) / spacing)), int(np.ceil((y1 - lo[1]) / spacing))
        ii, jj = np.meshgrid(np.arange(i0, i1 + 1), np.arange(j0, j1 + 1))
        px = lo[0] + ii * spacing
        py = lo[1] + jj * spacing
        (ax, ay), (bx, by), (cx, cy) = p[0, :2], p[1, :2], p[2, :2]
        det = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(det) < 1e-12:
            continue
        l0 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / det
        l1 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / det
        l2 = 1.0 - l0 - l1
        inside = (l0 >= -1e-9) & (l1 >= -1e-9) & (l2 >= -1e-9)
        z = l0 * p[0, 2] + l1 * p[1, 2] + l2 * p[2, 2]
        sub = grid[jj[inside], ii[inside]]
        grid[jj[inside], ii[inside]] = np.where(np.isnan(sub), z[inside], np.fmax(sub, z[inside]))
    return grid, lo


def paraboloid_opening(grid, spacing, radius, window):
    """Grey opening by the structuring function s(d) = -d^2 / (2 radius)."""
    reach = int(np.ceil(window / spacing))
    offsets = [(dj, di) for dj in range(-reach, reach + 1) for di in range(-reach, reach + 1)
               if (dj * dj + di * di) * spacing * spacing <= window * window]
    ny, nx = grid.shape
    big = 1e9
    f = np.where(np.isnan(grid), big, grid)
    pad = reach
    fp = np.pad(f, pad, constant_values=big)
    eroded = np.full_like(f, big)
    for dj, di in offsets:
        pen = (dj * dj + di * di) * spacing * spacing / (2.0 * radius)
        eroded = np.minimum(eroded, fp[pad + dj:pad + dj + ny, pad + di:pad + di + nx] + pen)
    eroded = np.where(np.isnan(grid), -big, eroded)
    ep = np.pad(eroded, pad, constant_values=-big)
    opened = np.full_like(f, -big)
    for dj, di in offsets:
        pen = (dj * dj + di * di) * spacing * spacing / (2.0 * radius)
        opened = np.maximum(opened, ep[pad + dj:pad + dj + ny, pad + di:pad + di + nx] - pen)
    return np.where(np.isnan(grid), np.nan, np.minimum(opened, grid))


def bilinear(grid, lo, spacing, xy):
    fx = (xy[:, 0] - lo[0]) / spacing
    fy = (xy[:, 1] - lo[1]) / spacing
    i = np.clip(np.floor(fx).astype(int), 0, grid.shape[1] - 2)
    j = np.clip(np.floor(fy).astype(int), 0, grid.shape[0] - 2)
    tx, ty = fx - i, fy - j
    corners = np.stack([grid[j, i], grid[j, i + 1], grid[j + 1, i], grid[j + 1, i + 1]], axis=1)
    weights = np.stack([(1 - tx) * (1 - ty), tx * (1 - ty), (1 - tx) * ty, tx * ty], axis=1)
    valid = np.isfinite(corners)
    num = np.where(valid, corners * weights, 0).sum(axis=1)
    den = np.where(valid, weights, 0).sum(axis=1)
    return np.where(den > 0, num / np.maximum(den, 1e-12), np.nan)


def hydraulic_context(vertices_xy, cap_origin, hyd_origin):
    manifest = json.loads((ATLAS / 'manifest.json').read_text())
    tile = manifest['tile_shape']
    origins = np.array([t['origin_m'] for t in manifest['tiles']])
    bed = np.load(ATLAS / 'bed.npy').reshape(-1, tile[0], tile[1])
    hx = vertices_xy[:, 0] + cap_origin[0] - hyd_origin[0]
    hy = vertices_xy[:, 1] + cap_origin[1] - hyd_origin[1]
    cell_bed = np.full(len(hx), np.nan)
    for k in range(len(hx)):
        t = np.flatnonzero((origins[:, 0] <= hx[k]) & (hx[k] < origins[:, 0] + tile[1]) &
                           (origins[:, 1] <= hy[k]) & (hy[k] < origins[:, 1] + tile[0]))
        if len(t):
            t = t[0]
            cell_bed[k] = bed[t][int(hy[k] - origins[t, 1]), int(hx[k] - origins[t, 0])]
    lo = np.array([hx.min(), hy.min()]) - WET_RADIUS_M - 1
    hi = np.array([hx.max(), hy.max()]) + WET_RADIUS_M + 1
    near = np.flatnonzero((origins[:, 0] <= hi[0]) & (origins[:, 0] + tile[1] >= lo[0]) &
                          (origins[:, 1] <= hi[1]) & (origins[:, 1] + tile[0] >= lo[1]))
    frames = sorted(p for p in COOK.iterdir() if p.is_dir() and p.name.startswith('frame_'))
    wet_any = np.zeros(len(hx), bool)
    own_cell_wet = np.zeros(len(hx), bool)
    max_eta = np.full(len(hx), -np.inf)
    for frame in frames:
        h = np.load(frame / 'h.npy', mmap_mode='r').reshape(-1, tile[0], tile[1])
        cx, cy, ce = [], [], []
        for t in near:
            depth = np.asarray(h[t])
            jj, ii = np.nonzero(depth > DRY_TOLERANCE_M)
            cx.append(origins[t, 0] + ii + 0.5)
            cy.append(origins[t, 1] + jj + 0.5)
            ce.append(bed[t][jj, ii] + depth[jj, ii])
        cx, cy, ce = map(np.concatenate, (cx, cy, ce))
        for k in range(len(hx)):
            # distance to the wet cell square, not just its centre
            dx = np.maximum(np.abs(cx - hx[k]) - 0.5, 0)
            dy = np.maximum(np.abs(cy - hy[k]) - 0.5, 0)
            mask = dx * dx + dy * dy <= WET_RADIUS_M ** 2
            if np.any((np.abs(cx - hx[k]) <= 0.5) & (np.abs(cy - hy[k]) <= 0.5)):
                own_cell_wet[k] = True
            if mask.any():
                wet_any[k] = True
                max_eta[k] = max(max_eta[k], ce[mask].max())
    return cell_bed, wet_any, own_cell_wet, max_eta, [f.name for f in frames]


def roof_steepness(vertices, triangles):
    a = vertices[triangles[:, 1]] - vertices[triangles[:, 0]]
    b = vertices[triangles[:, 2]] - vertices[triangles[:, 0]]
    n = np.cross(a, b)
    area = 0.5 * np.linalg.norm(n, axis=1)
    angle = np.degrees(np.arccos(np.clip(np.abs(n[:, 2]) / np.maximum(2 * area, 1e-12), 0, 1)))
    stats = {f'area_steeper_than_{t}deg_m2': float(area[angle > t].sum()) for t in (30, 45, 60, 75)}
    stats['roof_area_m2'] = float(area.sum())
    return stats


def build(output):
    if sha256(CAP) != CAP_SHA256:
        raise ValueError('Installed rock cap archive changed')
    manifest = json.loads(CAP_MANIFEST.read_text())
    cap_origin = manifest['origin_utm_and_vertical_datum_m']
    hyd = json.loads(HYDRAULIC_MAP.read_text())
    if hyd['vertical_datum_m'] != cap_origin[2]:
        raise ValueError('Vertical datum mismatch')
    with np.load(CAP, allow_pickle=False) as data:
        cap = {k: data[k] for k in data.files}
    roof = cap['vertices_m']
    tris = cap['triangles']
    solid = cap['solid_vertices_m']
    n_roof = len(roof)
    if not np.array_equal(solid[:n_roof], roof):
        raise ValueError('Solid does not start with the roof vertices')

    grid, lo = rasterize_tin(roof, tris, GRID_M)
    opened = paraboloid_opening(grid, GRID_M, RADIUS_M, WINDOW_M)
    envelope_z = bilinear(opened, lo, GRID_M, roof[:, :2])
    envelope_z = np.where(np.isfinite(envelope_z), np.minimum(envelope_z, roof[:, 2]), roof[:, 2])

    cell_bed, wet_near, own_wet, max_eta, frames = hydraulic_context(
        roof[:, :2], cap_origin, hyd['world_origin_utm_m'])
    wet_floor = np.where(np.isfinite(cell_bed), cell_bed, roof[:, 2])
    floor = np.minimum(roof[:, 2], np.where(own_wet, wet_floor, max_eta + WATER_MARGIN_M))
    new_z = np.maximum(envelope_z, floor)
    if np.any(new_z > roof[:, 2] + 1e-12):
        raise AssertionError('Envelope may only lower captured heights')

    new_roof = roof.copy()
    new_roof[:, 2] = new_z
    new_solid = solid.copy()
    new_solid[:n_roof] = new_roof
    lowered = roof[:, 2] - new_z
    changed = lowered > 1e-9
    kind = cap['solid_face_kind']
    near_water = changed & np.isfinite(max_eta)
    report = dict(
        schema='raftsim.troublemaker_rock_envelope.v2',
        status='interpreted_envelope_candidate',
        source_cap=CAP.relative_to(ROOT).as_posix(), source_cap_sha256=CAP_SHA256,
        method='grey opening of the roof TIN by a paraboloid; lower-only; hydraulic invariance constraints',
        radius_m=RADIUS_M,
        radius_basis='a priori: capture 1 m maximum triangle edge (unresolved convex scale)',
        raster_spacing_m=GRID_M, window_m=WINDOW_M, wet_radius_m=WET_RADIUS_M,
        cook_frames=frames, roof_vertices=int(n_roof),
        water_margin_m=WATER_MARGIN_M,
        vertices_changed=int(changed.sum()), vertices_in_wet_cells=int(own_wet.sum()),
        vertices_with_water_within_radius=int(wet_near.sum()),
        vertices_held_by_water_margin=int((~own_wet & (floor > envelope_z)).sum()),
        vertices_held_by_wet_cell_bed=int((own_wet & (floor > envelope_z)).sum()),
        wet_cell_vertices_lowered=int((own_wet & (roof[:, 2] - np.maximum(envelope_z, floor) > 1e-9)).sum()),
        lowering_m_percentiles={str(p): float(np.percentile(lowered[changed], p))
                                for p in (50, 90, 99, 100)} if changed.any() else {},
        min_height_above_near_water_of_changed_dry_m=float(np.min((new_z - max_eta)[near_water & ~own_wet]))
        if (near_water & ~own_wet).any() else None,
        roof_before=roof_steepness(roof, tris), roof_after=roof_steepness(new_roof, tris),
        topology_unchanged=True, xy_unchanged=True, walls_footprint_unchanged=True,
        wall_triangles=int((kind == 2).sum()),
        faces_measured=False, captured_returns_modified=False,
        provenance='Captured returns are unchanged in the source archive. Roof heights of changed '
                   'vertices are an interpreted rock envelope (inference), not measured rock surface.')
    np.savez(output, solid_vertices_m=new_solid, solid_triangles=cap['solid_triangles'],
             solid_face_kind=kind, roof_original_z_m=roof[:, 2], roof_lowered_m=lowered,
             roof_in_wet_cell=own_wet, roof_water_within_radius=wet_near, roof_cell_bed_m=cell_bed, roof_max_near_eta_m=max_eta)
    report['output'] = Path(output).resolve().relative_to(ROOT).as_posix()
    report['output_sha256'] = sha256(output)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Refusing to overwrite an existing envelope')
    result = build(args.output)
    Path(str(args.output) + '.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
