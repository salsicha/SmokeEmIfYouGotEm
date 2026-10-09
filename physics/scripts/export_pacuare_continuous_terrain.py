"""Encode the stitched full-run Pacuare evidence on the continuous terrain lattice.

Input is a stitched evidence folder (stitch_pacuare_evidence_segments.py).
Its bed array is the interpolated contour ground away from the river and the
inferred bed in it; cells no segment covers are NaN. A chunk is written only
when every one of its vertices has source evidence; partially covered chunks
are listed, never extrapolated or clamped.

Heights are IGN orthometric metres, encoded from a 0 m base: the run descends
from about 350 m to below 100 m, under the common 200 m base. Water inputs
must sample these triangles (build_curvilinear_river_scenario.py
--terrain-manifest), not resample the evidence.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates

from export_colorado_continuous_terrain import (
    VERTICES, HEIGHT_RANGE, LandscapeTriangles, sha, write_png_u16)

RIVER_ID = 'pacuare_river_costa_rica'
CRS = 'EPSG:5367'
VERTICAL = 'IGN Costa Rica orthometric heights'
HEIGHT_BASE = 0.


def encode(height):
    if not np.isfinite(height).all() or np.any(height < HEIGHT_BASE) or np.any(height > HEIGHT_BASE + HEIGHT_RANGE):
        raise ValueError('Terrain height outside the encoding; never clamp')
    return np.rint((height - HEIGHT_BASE) / HEIGHT_RANGE * 65535).astype('uint16')


def export(evidence, out, origin, datum, spacing=2.0):
    evidence, out = Path(evidence).resolve(), Path(out).resolve()
    if out.exists():
        raise ValueError('Fresh terrain export required')
    origin = np.asarray(origin, float)
    if spacing not in (1.0, 2.0):
        raise ValueError('Continuous terrain spacing must be 1 or 2 m')
    SPACING = float(spacing)
    SPAN = (VERTICES - 1) * SPACING
    if origin.shape != (2,) or not np.isfinite(origin).all() or not np.isfinite(datum):
        raise ValueError('Invalid geographic frame')
    manifest_path, grid_path = evidence / 'manifest.json', evidence / 'evidence_grid.npz'
    m = json.loads(manifest_path.read_text())
    if (m.get('schema') not in ('raftsim.pacuare.full_run_evidence_grid.v1', 'raftsim.pacuare.huacas_evidence_grid.v1')
            or not str(m.get('crs', '')).startswith('EPSG:5367') or m['grid'].get('cell_m') != 1):
        raise ValueError('Unsupported Pacuare evidence frame')
    g = m['grid']
    x0, y1, nx, ny = g['x0'], g['y_top'], int(g['nx']), int(g['ny'])
    with np.load(grid_path, allow_pickle=False) as arrays:
        bed = arrays['bed'].astype(float)
    if bed.shape != (ny, nx):
        raise ValueError('Evidence grid shape differs from its manifest')
    receipt = dict(manifest=str(manifest_path), manifest_sha256=sha(manifest_path),
                   grid=str(grid_path), grid_sha256=sha(grid_path))
    lo = np.floor((np.array([x0 + .5, y1 - ny + .5]) - origin) / SPAN).astype(int)
    hi = np.floor((np.array([x0 + nx - .5, y1 - .5]) - origin) / SPAN).astype(int)
    prepared, missing = [], []
    for i in range(lo[0], hi[0] + 1):
        for j in range(lo[1], hi[1] + 1):
            west, south = origin + np.array([i, j]) * SPAN
            east, north = np.meshgrid(west + np.arange(VERTICES) * SPACING, south + SPAN - np.arange(VERTICES) * SPACING)
            rows, cols = y1 - north - .5, east - x0 - .5
            inside = (rows >= 0) & (rows <= ny - 1) & (cols >= 0) & (cols <= nx - 1)
            if not inside.any():
                continue
            height = np.full(rows.shape, np.nan)
            height[inside] = map_coordinates(bed, [rows[inside], cols[inside]], order=1, mode='constant',
                                             cval=np.nan, prefilter=False)
            # Bilinear weights reach the neighbouring cells; any NaN there
            # leaves the vertex without full source support.
            if not np.isfinite(height).all():
                if np.isfinite(height).any():
                    missing.append(dict(chunk=[int(i), int(j)], missing_vertices=int((~np.isfinite(height)).sum())))
                continue
            prepared.append((int(i), int(j), float(west), float(south + SPAN), encode(height)))
    if not prepared:
        raise ValueError('No completely source-backed terrain chunks')
    out.mkdir(parents=True)
    chunks = []
    for i, j, west, north, encoded in prepared:
        name = f'height_{i}_{j}.png'
        write_png_u16(out / name, encoded)
        chunks.append(dict(chunk=[i, j], heightfield=name, sha256=sha(out / name), origin_m=[west, north],
                           world_northwest_xy_cm=[i * SPAN * 100, -(j + 1) * SPAN * 100]))
    result = dict(schema='raftsim.continuous_landscape.v1', river_id=RIVER_ID, horizontal_crs=CRS,
        vertical_reference=VERTICAL, world_y_sign=-1, horizontal_origin_m=origin.tolist(), vertical_datum_m=float(datum),
        evidence_source=receipt, geographic_scope=dict(reach_osm_chain_m=m.get('statistics', {}).get('reach_osm_chain_m')),
        landscape=dict(vertices=VERTICES, spacing_m=SPACING, span_m=SPAN, subsections_per_component=2,
            quads_per_subsection=63, height_base_m=HEIGHT_BASE, height_range_m=HEIGHT_RANGE,
            actor_z_cm=(HEIGHT_BASE + HEIGHT_RANGE * 32768 / 65535 - datum) * 100,
            scale_xyz=[SPACING * 100, SPACING * 100, HEIGHT_RANGE * 100 / 512 * 65536 / 65535]),
        shared_edge_max_encoded_difference=0, chunks=chunks, incomplete_source_chunks=missing,
        scope='Full-run Pacuare terrain: ground interpolated between IGN 10 m contours (measured contours), '
              'bed inferred; no rapid bounds assigned',
        vegetation_complete=False, engine_validated=False, full_river_complete=False)
    (out / 'manifest.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    LandscapeTriangles(out)  # re-read hashes, lattice and every shared edge
    if sha(manifest_path) != receipt['manifest_sha256'] or sha(grid_path) != receipt['grid_sha256']:
        raise ValueError('Evidence changed during terrain export; candidate must not be used')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--origin', type=float, nargs=2, required=True)
    p.add_argument('--vertical-datum-m', type=float, required=True)
    p.add_argument('--spacing', type=float, default=2.0,
                   help='lattice spacing; 1 m resolves narrow riffle channels the 2 m lattice raises')
    a = p.parse_args()
    r = export(a.evidence, a.out, a.origin, a.vertical_datum_m, a.spacing)
    print(json.dumps(dict(chunks=len(r['chunks']), incomplete_chunks=len(r['incomplete_source_chunks']))))
