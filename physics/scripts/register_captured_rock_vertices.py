"""Keep selected LiDAR rock returns at their captured XY, not raster centres.

This produces a mesh-only candidate, deliberately not a hydraulic raster. A
regular-raster sampler must not consume it. Original dry ground, inferred bed
and filled gaps remain unchanged; rock faces between returns remain inferred.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tmp/south-fork-geospatial-deps'))
import numpy as np
from south_fork_mesh_sampling import grid_triangles


def oriented_quad_triangles(east, north):
    """Preserve grid connectivity, switching only an invalid local diagonal."""
    if east.shape != north.shape or east.ndim != 2 or min(east.shape) < 2:
        raise ValueError('Matching two-dimensional coordinate arrays required')
    if not np.isfinite(east).all() or not np.isfinite(north).all():
        raise ValueError('Coordinates must be finite')
    rows, cols = east.shape
    faces = grid_triangles(rows, cols)
    xy = np.column_stack((east.ravel(), north.ravel()))
    n = len(faces)//2

    def areas(triangles):
        p, q, r = (xy[triangles[:, i]] for i in range(3))
        return (q[:, 0]-p[:, 0])*(r[:, 1]-p[:, 1]) - (q[:, 1]-p[:, 1])*(r[:, 0]-p[:, 0])

    # North decreases with raster row; Blender later reverses north for FBX.
    signed = -areas(faces)
    invalid = (signed[:n] <= 1e-9) | (signed[n:] <= 1e-9)
    a, b, c = (faces[:n, i] for i in range(3))
    d = b + cols
    alt1, alt2 = np.column_stack((a, b, d)), np.column_stack((a, d, c))
    faces[:n][invalid] = alt1[invalid]
    faces[n:][invalid] = alt2[invalid]
    final = -areas(faces)
    if np.any(final <= 1e-9):
        raise ValueError(f'{np.count_nonzero(final <= 1e-9)} folded/degenerate triangles; no candidate accepted')
    return faces, dict(changed_quad_diagonals=int(invalid.sum()),
        minimum_projected_triangle_area_m2=float(final.min()/2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT/'tmp/south-fork-rock-gap-candidate-20260907')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if not source.is_relative_to(ROOT) or not output.is_relative_to(ROOT) or output.exists():
        raise ValueError('Source and fresh output must be inside the project')
    manifest = json.loads((source/'manifest.json').read_text())
    parent_raster = ROOT/manifest['shared_geometry_path']
    if hashlib.sha256(parent_raster.read_bytes()).hexdigest() != manifest['shared_geometry_sha256']:
        raise ValueError('Source raster identity changed')
    with np.load(source/'engine_mesh_source.npz') as data:
        packed = {key: data[key].copy() for key in data.files}
    reference = {key: packed[key].copy() for key in ('east_m', 'north_m', 'z_m')}
    import rasterio
    with rasterio.open(parent_raster) as ds:
        affine = ds.transform
    point_path = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/classified_lidar_returns.npz'
    with np.load(point_path) as points:
        east, north, height = (points[key] for key in ('utm_easting_m', 'utm_northing_m', 'navd88_m'))
        col, row = (~affine)*(east, north)
        col, row = np.floor(col).astype(int), np.floor(row).astype(int)
        rows, cols = packed['z_m'].shape
        valid = (row >= 0)&(row < rows)&(col >= 0)&(col < cols)
        valid &= np.isin(points['classification'], [1,2,10])
        valid &= (points['height_above_flattened_surface_m'] > .3)&(points['height_above_flattened_surface_m'] < 8)
        indices = np.flatnonzero(valid)
        indices = indices[packed['authority'][row[indices], col[indices]] == 3]
        cells = row[indices]*cols+col[indices]
        # Stable tie-break by original point index; exact same lower-envelope
        # selection as the raster builder, but retain that return's true XY.
        order = np.lexsort((indices, height[indices], cells))
        sorted_cells = cells[order]
        first = np.r_[True, sorted_cells[1:] != sorted_cells[:-1]]
        chosen = indices[order[first]]
        chosen_cells = sorted_cells[first]
        rock_cells = np.flatnonzero(packed['authority'].ravel() == 3)
        if not np.array_equal(chosen_cells, rock_cells):
            raise ValueError('Not every previously supported rock cell has its original return')
        datum = manifest['vertical_origin_navd88_m']
        if not np.allclose(packed['z_m'].ravel()[rock_cells]+datum, height[chosen], rtol=0, atol=3e-5):
            raise ValueError('Selected returns disagree with the recorded lower envelope')
        for key, values in (('east_m', east[chosen]-manifest['origin_utm_m'][0]),
                            ('north_m', north[chosen]-manifest['origin_utm_m'][1])):
            packed[key].ravel()[rock_cells] = values
        # Keep recorded heights byte-identical. Their only discrepancy from
        # the source return is the existing float32 quantization (<0.03 mm).
        xy_shift = np.hypot(packed['east_m']-reference['east_m'], packed['north_m']-reference['north_m'])
        if xy_shift.max() > manifest['cell_m']/np.sqrt(2)+1e-7:
            raise ValueError('A return moved outside its original source cell')
        packed['rock_source_return_index'] = chosen
    faces, stats = oriented_quad_triangles(packed['east_m'], packed['north_m'])
    packed['triangles'] = faces
    packed['nominal_east_axis_m'] = reference['east_m'][0, :]
    packed['nominal_north_axis_m'] = reference['north_m'][:, 0]
    untouched = packed['authority'] != 3
    if any(not np.array_equal(packed[k][untouched], reference[k][untouched]) for k in reference):
        raise ValueError('Ground, inferred bed or gap interpolation changed')
    if not np.array_equal(packed['z_m'], reference['z_m']):
        raise ValueError('Recorded heights changed')
    output.mkdir(parents=True, exist_ok=False)
    target = output/'registered_mesh_source.npz'
    np.savez_compressed(target, **packed)
    report = dict(schema='raftsim.captured_rock_xy_mesh_candidate.v1',
        status='mesh_candidate_requires_sampling_hydraulics_collision_and_visual_validation',
        source_geometry_format='irregular_xy_triangle_mesh_not_regular_raster',
        mesh_path=target.relative_to(ROOT).as_posix(), mesh_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        parent_raster_sha256=manifest['shared_geometry_sha256'],
        parent_mesh_sha256=hashlib.sha256((source/'engine_mesh_source.npz').read_bytes()).hexdigest(),
        parent_mesh_path=(source/'engine_mesh_source.npz').relative_to(ROOT).as_posix(),
        original_returns_sha256=hashlib.sha256(point_path.read_bytes()).hexdigest(),
        original_return_count=int(len(chosen)),
        max_rock_xy_registration_correction_m=float(xy_shift.max()),
        mean_rock_xy_registration_correction_m=float(xy_shift.ravel()[rock_cells].mean()),
        all_recorded_heights_unchanged=True, non_rock_vertices_unchanged=True,
        origin_utm_m=manifest['origin_utm_m'], vertical_origin_navd88_m=datum,
        faces_between_returns_authority='inferred interpolation, not surveyed continuous boulder surfaces',
        submerged_bed_authority=manifest['submerged_bed_authority'],
        registered_rapid_identity_verified=False, hydraulic_validation_passed=False,
        game_integrated=False, production_promoted=False, **stats)
    (output/'manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
