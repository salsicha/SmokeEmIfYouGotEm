"""Build the always-loaded South Fork terrain backdrop (numpy only).

The normal FullReach map has only its 441 detailed terrain tiles, streamed by
World Partition within 2 km of the view; there is no far-field terrain. Beyond
that range the world ended in sky, so distant ridges read as floating shards of
terrain and trees. This builds one coarse, non-colliding presentation mesh from
the same 2 m context grid the tiles use, guaranteed to lie below every detailed
tile surface so it can only show where no tile is loaded.

Heights: each backdrop vertex takes the minimum of the discharge-consistent bed
grid (dry cells are the captured surface; wet cells are the inferred bed) over
every 2 m vertex of the backdrop cells it touches, minus a margin. Any point of
a backdrop triangle is a convex combination of its corners, each no higher than
the lowest source vertex of that cell minus the margin, so the backdrop is below
the detailed tile surface everywhere (the tiles interpolate those same source
vertices). Ridges are therefore lowered by up to the local relief within one
backdrop cell: presentation inference, not measured terrain.

Output (explicit new folder): backdrop.npz (xyz_local_m, triangles) in the tile
convention (local x = E - E0, local y = N - N0, z = NAVD88 - 220 m), manifest.json
in the render-tile manifest schema consumed by export_south_fork_composite_tiles.py.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FULL = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
BED = FULL / 'discharge_bed_20260926/bed/coarse_bed_navd88_m.npz'
CONTEXT_MANIFEST = FULL / 'source_context_extension/manifest.json'
WORLD_ORIGIN_UTM = (689237.0, 4293073.0)
DATUM_M = 220.0
# Troublemaker's retained high-resolution ground and its canopy are always
# loaded and are not on the 2 m grid; never draw a backdrop under them.
TROUBLEMAKER_EXCLUSION_UTM = (683625.25 - 64.0, 4296533.75 - 64.0, 683984.75 + 64.0, 4296813.25 + 64.0)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def window_min(grid, radius):
    """Minimum over a (2r+1)^2 window, NaN-aware (NaN only if every cell is NaN)."""
    filled = np.where(np.isfinite(grid), grid, np.inf)
    out = filled.copy()
    # Separable running minimum: rows then columns.
    tmp = filled.copy()
    for k in range(1, radius + 1):
        tmp[k:, :] = np.minimum(tmp[k:, :], filled[:-k, :])
        tmp[:-k, :] = np.minimum(tmp[:-k, :], filled[k:, :])
    out = tmp.copy()
    for k in range(1, radius + 1):
        out[:, k:] = np.minimum(out[:, k:], tmp[:, :-k])
        out[:, :-k] = np.minimum(out[:, :-k], tmp[:, k:])
    out[np.isinf(out)] = np.nan
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--stride', type=int, default=8, help='2 m source cells per backdrop cell')
    parser.add_argument('--margin-m', type=float, default=1.5)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'physics/data') and not out.exists(), 'Use a new explicit output folder'
    context = json.loads(CONTEXT_MANIFEST.read_text())
    grid = context['grid']
    e0, n0 = grid['first_vertex_utm_m']
    cell = float(grid['cell_m'])
    with np.load(BED) as data:
        bed = data['coarse_bed_navd88_m'].astype(np.float32)
    assert list(bed.shape) == list(grid['shape']), (bed.shape, grid['shape'])
    stride = args.stride
    # Every source vertex of the two backdrop cells on each side of a vertex.
    lowest = window_min(bed, stride)
    rows = np.arange(0, bed.shape[0], stride)
    cols = np.arange(0, bed.shape[1], stride)
    if rows[-1] != bed.shape[0] - 1:
        rows = np.append(rows, bed.shape[0] - 1)
    if cols[-1] != bed.shape[1] - 1:
        cols = np.append(cols, bed.shape[1] - 1)
    heights = lowest[np.ix_(rows, cols)].astype(np.float64) - args.margin_m
    del lowest
    east = e0 + cols * cell
    north = n0 - rows * cell
    ee, nn = np.meshgrid(east, north)
    ex = TROUBLEMAKER_EXCLUSION_UTM
    excluded = (ee >= ex[0]) & (ee <= ex[2]) & (nn >= ex[1]) & (nn <= ex[3])
    valid = np.isfinite(heights) & ~excluded
    index = -np.ones(heights.shape, dtype=np.int64)
    index[valid] = np.arange(int(valid.sum()))
    xyz = np.stack([ee[valid] - e0, nn[valid] - n0, heights[valid] - DATUM_M], axis=1)
    a = index[:-1, :-1]; b = index[:-1, 1:]; c = index[1:, :-1]; d = index[1:, 1:]
    quad = (a >= 0) & (b >= 0) & (c >= 0) & (d >= 0)
    # Same diagonal and winding sense as the source tiles (NW-NE-SW / NE-SE-SW).
    tri = np.concatenate([np.stack([a[quad], b[quad], c[quad]], 1), np.stack([b[quad], d[quad], c[quad]], 1)])
    used = np.zeros(len(xyz), dtype=bool)
    used[tri.ravel()] = True
    remap = -np.ones(len(xyz), dtype=np.int64)
    remap[used] = np.arange(int(used.sum()))
    xyz = xyz[used]
    tri = remap[tri]
    out.mkdir(parents=True)
    mesh_path = out / 'backdrop.npz'
    np.savez_compressed(mesh_path, xyz_local_m=xyz.astype(np.float64), triangles=tri.astype(np.int64))
    # Guarantee check against the full-resolution source (sampled at every
    # 2 m vertex): bilinear-on-triangles backdrop height minus bed height.
    clearances = []
    for r0 in range(0, len(rows) - 1):
        r_lo, r_hi = rows[r0], rows[r0 + 1]
        block = bed[r_lo:r_hi + 1, :cols[-1] + 1].astype(np.float64)
        rr = np.arange(r_lo, r_hi + 1)[:, None]
        cc = np.arange(0, cols[-1] + 1)[None, :]
        bc = np.clip(np.searchsorted(cols, cc, side='right') - 1, 0, len(cols) - 2)
        fr = (rr - r_lo) / float(r_hi - r_lo)
        fc = (cc - cols[bc]) / (cols[bc + 1] - cols[bc]).astype(np.float64)
        h00 = heights[r0][bc]; h01 = heights[r0][bc + 1]; h10 = heights[r0 + 1][bc]; h11 = heights[r0 + 1][bc + 1]
        upper = fr + fc <= 1.0
        interp = np.where(upper, h00 + fc * (h01 - h00) + fr * (h10 - h00),
                          h11 + (1 - fc) * (h10 - h11) + (1 - fr) * (h01 - h11))
        check = np.isfinite(interp) & np.isfinite(block)
        clearances.append((block - interp)[check])
    clearance = np.concatenate(clearances)
    manifest = dict(
        schema='raftsim.south_fork.cartesian_terrain_tiles.v1',
        purpose='always-loaded non-colliding terrain backdrop beyond the World Partition loading range',
        inferred_presentation=True, measured=False, collision=False,
        source_bed=str(BED.relative_to(ROOT).as_posix()), source_bed_sha256=sha(BED),
        source_context_manifest_sha256=sha(CONTEXT_MANIFEST),
        stride_source_cells=stride, spacing_m=stride * cell, margin_m=args.margin_m,
        troublemaker_exclusion_utm_m=list(TROUBLEMAKER_EXCLUSION_UTM),
        minimum_clearance_below_source_m=float(clearance.min()),
        median_clearance_below_source_m=float(np.median(clearance)),
        p99_clearance_below_source_m=float(np.percentile(clearance, 99)),
        checked_source_vertices=int(clearance.size),
        no_simplification=False,
        tiles=[dict(name='terrain_backdrop_%dm' % int(stride * cell), path=str(mesh_path.relative_to(ROOT).as_posix()),
                    sha256=sha(mesh_path), origin_utm_m=[e0, n0],
                    actor_translation_cm=[(e0 - WORLD_ORIGIN_UTM[0]) * 100.0, -(n0 - WORLD_ORIGIN_UTM[1]) * 100.0, 0.0],
                    actor_scale=[1.0, -1.0, 1.0], vertex_count=int(len(xyz)), triangle_count=int(len(tri)))])
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({k: manifest[k] for k in ('spacing_m', 'margin_m', 'minimum_clearance_below_source_m',
                                                  'median_clearance_below_source_m', 'p99_clearance_below_source_m',
                                                  'checked_source_vertices')}), flush=True)
    print('vertices', len(xyz), 'triangles', len(tri))


if __name__ == '__main__':
    main()
