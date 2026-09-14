"""Independently measure slopes of actual submitted triangles; not an acceptance gate."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np

VERTEX_FIELDS = ['id', 'x_cm', 'y_cm', 'carrier_z_cm', 'coarse_crest_cm', 'fine_correction_cm', 'detail_cm']
SOURCE_FIELDS = ['id', 'field_x_m', 'field_y_m', 'clipping_wet', 'source_bed_plus_depth_m', 'source_depth_m']
SOURCE_FIELDS_V2 = SOURCE_FIELDS + ['target_base_m', 'target_full_m']


def read_table(path, fields):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.reader(stream)
        if next(reader, None) != fields:
            raise ValueError('Unexpected fields: ' + str(path))
        rows = []
        for row in reader:
            if len(row) != len(fields):
                raise ValueError('Incomplete row: ' + str(path))
            rows.append([float(v) for v in row])
    result = np.asarray(rows, dtype=float)
    if result.ndim != 2 or not np.isfinite(result).all():
        raise ValueError('Empty/nonfinite table: ' + str(path))
    return result


def gradients(xy, values):
    """Exact plane gradient from three vertices; coordinates and heights in metres."""
    a, b = xy[:, 1] - xy[:, 0], xy[:, 2] - xy[:, 0]
    determinant = a[:, 0]*b[:, 1] - a[:, 1]*b[:, 0]
    if np.any(determinant == 0):
        raise ValueError('Zero projected area')
    da, db = values[:, 1] - values[:, 0], values[:, 2] - values[:, 0]
    return np.stack(((da*b[:, 1]-db*a[:, 1])/determinant,
                     (a[:, 0]*db-b[:, 0]*da)/determinant), axis=1)


def raw_stage(points, source, nx, ny, sign, value_column=4):
    """Original source-lattice triangle interpolation, only inside fully wet cells."""
    grid = source.reshape(ny, nx, source.shape[1])
    xs, ys = grid[0, :, 1], grid[:, 0, 2]
    dx, dy = xs[1]-xs[0], ys[1]-ys[0]
    if dx <= 0 or dy <= 0 or not np.allclose(np.diff(xs), dx, rtol=0, atol=1e-7) or not np.allclose(np.diff(ys), dy, rtol=0, atol=1e-7):
        raise ValueError('Nonuniform source lattice')
    if not np.array_equal(grid[:, :, 1], np.broadcast_to(xs, (ny, nx))) or not np.array_equal(grid[:, :, 2], np.broadcast_to(ys[:, None], (ny, nx))):
        raise ValueError('Wrong source lattice ordering')
    q = (points*np.array([1., sign])-np.array([xs[0], ys[0]]))/np.array([dx, dy])
    valid = (q[:, 0] >= 0) & (q[:, 1] >= 0) & (q[:, 0] <= nx-1) & (q[:, 1] <= ny-1)
    # Safe indexing only; outside points remain invalid, not extrapolated.
    cell = np.minimum(np.maximum(np.floor(q).astype(int), 0), [nx-2, ny-2])
    u, v = (q-cell).T
    a = cell[:, 1]*nx+cell[:, 0]
    corners = np.stack((a, a+1, a+nx, a+nx+1), axis=1)
    valid &= (source[corners, 3] == 1).all(axis=1)
    z = source[corners, value_column]
    height = np.where(u+v <= 1, z[:, 0]*(1-u-v)+z[:, 2]*v+z[:, 1]*u,
                      z[:, 1]*(1-v)+z[:, 2]*(1-u)+z[:, 3]*(u+v-1))
    height[~valid] = np.nan
    return height, valid


def summarize(meta, vertices, triangles, source, radius):
    version = meta.get('schema')
    if version not in ('raftsim.submitted_carrier_shape.v1', 'raftsim.submitted_carrier_shape.v2'):
        raise ValueError('Wrong schema')
    source_width = 8 if version.endswith('.v2') else 6
    for table, width in [(vertices, 7), (triangles, 3), (source, source_width)]:
        if table.ndim != 2 or table.shape[1] != width or not np.isfinite(table).all():
            raise ValueError('Invalid/nonfinite table')
    n, nx, ny = meta['active_vertices'], meta['source_nx'], meta['source_ny']
    for key in ['world_seconds', 'detail_sequence', 'render_lift_cm', 'focus_x_cm', 'focus_y_cm']:
        if not np.isfinite(meta[key]):
            raise ValueError('Nonfinite metadata')
    if n != len(vertices) or meta['triangles'] != len(triangles) or meta['buffer_vertices'] < n:
        raise ValueError('Incomplete submitted mesh')
    if not np.array_equal(vertices[:, 0], np.arange(n)) or not np.array_equal(source[:, 0], np.arange(nx*ny)):
        raise ValueError('Missing/reordered source or active IDs')
    if np.any(triangles != np.floor(triangles)) or np.any(triangles < 0) or np.any(triangles >= n):
        raise ValueError('Invalid/reserved index')
    if nx < 2 or ny < 2 or meta['world_y_sign'] not in (-1, 1) or not np.isfinite(radius) or radius <= 0:
        raise ValueError('Invalid grid/radius')
    if not np.isin(source[:, 3], [0, 1]).all() or np.any(source[:, 5] < 0):
        raise ValueError('Invalid raw wet/depth values')
    t = triangles.astype(int)
    xy = vertices[t, 1:3]*.01
    edge1, edge2 = xy[:, 1]-xy[:, 0], xy[:, 2]-xy[:, 0]
    areas = np.abs(edge1[:, 0]*edge2[:, 1]-edge1[:, 1]*edge2[:, 0])*.5
    centers = xy.mean(axis=1)
    focus = np.array([meta['focus_x_cm'], meta['focus_y_cm']])*.01
    nearby = np.linalg.norm(centers-focus, axis=1) <= radius
    keep = nearby & (areas > 0)
    if not keep.any():
        raise ValueError('No nondegenerate nearby triangles')
    selected = np.flatnonzero(keep)
    t, xy, areas, centers = t[keep], xy[keep], areas[keep], centers[keep]
    height = dict(carrier=vertices[:, 3]*.01,
                  crest=(vertices[:, 4]+vertices[:, 5])*.01,
                  detail=vertices[:, 6]*.01)
    height['base_residual'] = height['carrier']-height['crest']-meta['render_lift_cm']*.01
    height['displayed'] = height['carrier']+height['detail']
    g = {key: gradients(xy, value[t]) for key, value in height.items()}
    raw, valid = raw_stage(vertices[:, 1:3]*.01, source, nx, ny, meta['world_y_sign'])
    raw_valid = valid[t].all(axis=1)
    raw_g = gradients(xy[raw_valid], raw[t[raw_valid]])
    source_parts = {'cached_source': raw_g}
    if source_width == 8:
        target, target_valid = raw_stage(vertices[:, 1:3]*.01, source, nx, ny, meta['world_y_sign'], 6)
        if not np.array_equal(valid, target_valid):
            raise ValueError('Different source/target comparison domains')
        target_g = gradients(xy[raw_valid], target[t[raw_valid]])
        source_parts['target_minus_source'] = target_g-raw_g
        source_parts['submitted_base_minus_target'] = g['base_residual'][raw_valid]-target_g
    else:
        source_parts['submitted_base_minus_source'] = g['base_residual'][raw_valid]-raw_g
    source_closure = (float(np.max(np.abs(sum(source_parts.values())-g['base_residual'][raw_valid])))
                      if raw_valid.any() else None)
    slope = np.linalg.norm(g['displayed'], axis=1)
    degrees = np.degrees(np.arctan(slope))
    residual = np.max(np.abs(g['displayed']-g['base_residual']-g['crest']-g['detail']))
    groups = []
    for low, high in [(0, 10), (10, 30), (30, 60), (60, 90)]:
        mask = (degrees >= low) & (degrees < high)
        area = float(areas[mask].sum())
        component_projection = {}
        if area:
            direction = g['displayed'][mask]/np.maximum(slope[mask, None], 1e-30)
            for key in ['base_residual', 'crest', 'detail']:
                component_projection[key] = float(np.sum(areas[mask]*np.sum(g[key][mask]*direction, axis=1))/area)
        compared = mask[raw_valid]
        compared_area = float(areas[raw_valid][compared].sum())
        source_projection = {}
        if compared_area:
            direction = g['displayed'][raw_valid][compared]/np.maximum(slope[raw_valid][compared, None], 1e-30)
            for key, values in source_parts.items():
                source_projection[key] = float(np.sum(areas[raw_valid][compared]*np.sum(values[compared]*direction, axis=1))/compared_area)
        groups.append(dict(slope_degrees=[low, high], triangles=int(mask.sum()), projected_area_m2=area,
                           area_weighted_signed_gradient_along_displayed_slope=component_projection,
                           source_comparison_triangles=int(compared.sum()), source_comparison_area_m2=compared_area,
                           source_comparison_signed_gradient_along_displayed_slope=source_projection))
    top = np.flatnonzero(areas >= 1e-4)
    top = top[np.argsort(-slope[top])[:12]]
    raw_lookup = {int(i): gradient.tolist() for i, gradient in zip(np.flatnonzero(raw_valid), raw_g)}
    return dict(accepted=False, scope=meta['scope'], radius_m=radius, focus_world_m=focus.tolist(),
        world_seconds=meta['world_seconds'], detail_sequence=meta['detail_sequence'],
        selected_triangles=len(t), zero_projected_area_nearby=int((nearby & ~keep).sum()),
        projected_area_m2=float(areas.sum()), maximum_gradient_component_sum_error=float(residual),
        maximum_source_component_sum_error=source_closure,
        target_scope=meta.get('target_scope', 'Pre-temporal targets unavailable in historical v1 capture.'),
        component_max_absolute_height_m={k: float(np.max(np.abs(v[np.unique(t)]))) for k, v in height.items()},
        raw_comparison_triangles=int(raw_valid.sum()), raw_comparison_projected_area_m2=float(areas[raw_valid].sum()),
        maximum_raw_triangle_slope=float(np.max(np.linalg.norm(raw_g, axis=1))) if len(raw_g) else None,
        slope_groups=groups,
        steepest_triangles_at_least_one_square_centimeter=[dict(triangle=int(selected[i]),
            center_world_m=centers[i].tolist(), projected_area_m2=float(areas[i]), slope_degrees=float(degrees[i]),
            component_gradient={key: value[i].tolist() for key, value in g.items()},
            raw_source_triangle_gradient=raw_lookup.get(int(i))) for i in top],
        limitations='Slope bins describe geometry, not calibrated wave quality. Base residual includes temporal history, clipping and other relief. The raw_source comparison interpolates the cached source bed-plus-depth sum, only in fully wet/available/connected source cells; it need not have the displayed temporal age and is not a new native sample. No wet-boundary extrapolation. CPU presented detail is not an observed render-thread/GPU exposure. No terrain occlusion or photographic acceptance.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--radius-m', type=float, default=30.)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    paths = [args.capture]+[Path(str(args.capture)+suffix) for suffix in ('.vertices.csv', '.triangles.csv', '.source.csv')]
    meta = json.loads(paths[0].read_text(encoding='utf-8-sig'))
    result = summarize(meta, read_table(paths[1], VERTEX_FIELDS), read_table(paths[2], ['a', 'b', 'c']),
                       read_table(paths[3], SOURCE_FIELDS_V2 if meta.get('schema') == 'raftsim.submitted_carrier_shape.v2' else SOURCE_FIELDS), args.radius_m)
    result['input_sha256'] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({k: result[k] for k in ['selected_triangles', 'detail_sequence', 'maximum_gradient_component_sum_error', 'slope_groups']}))


if __name__ == '__main__':
    main()
