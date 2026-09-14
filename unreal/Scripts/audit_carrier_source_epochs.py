"""Compare immutable cook epochs at exact captured source vertices, not acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_submitted_carrier_shape import read_table, SOURCE_FIELDS_V2, gradients, raw_stage


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def exact_cells(points, origins, shape, spacing):
    """Return (tile,row,col), or -1 for missing/off-grid points. Never round to water."""
    points, origins = np.asarray(points, float), np.asarray(origins, float)
    ny, nx = shape
    if (points.ndim != 2 or points.shape[1] != 2 or origins.ndim != 2 or origins.shape[1] != 2
            or not np.isfinite(points).all() or not np.isfinite(origins).all()
            or ny < 2 or nx < 2 or not np.isfinite(spacing) or spacing <= 0):
        raise ValueError('Invalid source coordinates/grid')
    result = np.full((len(points), 3), -1, dtype=int)
    for tile, origin in enumerate(origins):
        index = (points-origin)/spacing
        rounded = np.rint(index)
        use = ((rounded >= 0).all(1) & (rounded < [nx, ny]).all(1)
               & (np.max(abs(index-rounded), axis=1)*spacing <= 1e-6))
        if (result[use, 0] >= 0).any():
            raise ValueError('Overlapping source cells')
        result[use] = np.column_stack((np.full(use.sum(), tile), rounded[use, 1], rounded[use, 0])).astype(int)
    return result


def common_triangles(source, nx, ny, early, late, focus, radius):
    if len(source) != nx*ny or not np.isfinite(radius) or radius <= 0:
        raise ValueError('Invalid source size/radius')
    root = np.arange(nx*ny).reshape(ny, nx)[:-1, :-1].ravel()
    triangles = np.concatenate((np.stack((root, root+1, root+nx), 1),
                                np.stack((root+1, root+nx+1, root+nx), 1)))
    xy = source[triangles, 1:3]
    keep = ((np.linalg.norm(xy.mean(1)-focus, axis=1) <= radius)
            & np.isfinite(early[triangles]).all(1) & np.isfinite(late[triangles]).all(1)
            & (early[triangles] > 1e-4).all(1) & (late[triangles] > 1e-4).all(1)
            & (source[triangles, 3] == 1).all(1))
    return triangles[keep]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('atlas', type=Path)
    parser.add_argument('cook', type=Path)
    parser.add_argument('step', type=int)
    parser.add_argument('--state-audit', type=Path, required=True)
    parser.add_argument('--bank-audit', type=Path, required=True)
    parser.add_argument('--radius-m', type=float, default=30.)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    meta, atlas = read(args.capture), read(args.atlas)
    if meta['schema'] != 'raftsim.submitted_carrier_shape.v2' or atlas['schema'] != 'raftsim.cartesian_state_atlas.v1':
        raise ValueError('Unsupported input schema')
    source_path = Path(str(args.capture)+'.source.csv')
    source = read_table(source_path, SOURCE_FIELDS_V2)
    nx, ny = meta['source_nx'], meta['source_ny']
    if not np.array_equal(source[:, 0], np.arange(nx*ny)) or meta['world_y_sign'] not in (-1, 1):
        raise ValueError('Incomplete/malformed captured lattice')
    if not np.isin(source[:, 3], [0, 1]).all() or (source[:, 5] < 0).any():
        raise ValueError('Invalid captured wet/depth fields')
    # Reuse the independently tested lattice-order/uniformity validation.
    raw_stage(source[:, 1:3]*[1, meta['world_y_sign']], source, nx, ny, meta['world_y_sign'])
    original = Path((args.cook/'input_manifest_path.txt').read_text().strip())
    if not original.is_absolute():
        original = Path(__file__).resolve().parents[2]/original
    if sha(original) != sha(args.cook/'input_manifest.json'):
        raise ValueError('Cook input changed')
    manifest = read(original)
    if manifest['vertical_datum_navd88_m'] != atlas['source_elevation_datum_m']:
        raise ValueError('Different source datums')
    frame = args.cook/f'frame_{args.step:06d}'
    complete, state_audit, bank_audit = read(frame/'complete.json'), read(args.state_audit), read(args.bank_audit)
    late_path = frame/'h.npy'
    if (not complete['snapshot'] or complete['step'] != args.step or not state_audit['passed']
            or not bank_audit['all_artificial_banks_exactly_dry']):
        raise ValueError('Completed snapshot and both independent audits required')
    for audit in (state_audit, bank_audit):
        if audit['step'] != args.step or audit['time_seconds'] != complete['time_seconds'] or audit['input_manifest_sha256'] != sha(original):
            raise ValueError('Mismatched snapshot audit')
    if sha(late_path) != state_audit['arrays']['h']['sha256'] or sha(late_path) != bank_audit['h_sha256']:
        raise ValueError('Snapshot changed after audits')
    paths = [args.capture, source_path, args.atlas, original, frame/'complete.json',
             args.state_audit, args.bank_audit, late_path]
    fields = {}
    for key in ('bed', 'h'):
        record = atlas['arrays'][key]
        path = (args.atlas.parent/record['file']).resolve()
        if sha(path) != record['sha256']:
            raise ValueError('Atlas field hash mismatch')
        value = np.load(path, mmap_mode='r', allow_pickle=False)
        if list(value.shape) != record['shape'] or value.dtype != np.dtype('<f8') or not np.isfinite(value).all():
            raise ValueError('Invalid atlas array')
        fields[key] = value
        paths.append(path)
    origins = [tile['origin_m'] for tile in atlas['tiles']]
    shape, spacing = atlas['tile_shape'], atlas['grid_spacing_m']
    grids = []
    for package, guard in zip(manifest['packages'], manifest['inputs'], strict=True):
        path = original.parent/package/'scenario.json'
        if package != guard['name'] or sha(path) != guard['files']['scenario.json']:
            raise ValueError('Cook grid changed')
        grids.append(read(path)['grid'])
    if any([g['ny'], g['nx']] != shape or g['dx'] != spacing or g['dy'] != spacing for g in grids):
        raise ValueError('Different source lattice spacing')
    cells = exact_cells(source[:, 1:3], origins, shape, spacing)
    late_cells = exact_cells(source[:, 1:3], [[g['origin_x'], g['origin_y']] for g in grids], shape, spacing)
    available = (cells[:, 0] >= 0) & (late_cells[:, 0] >= 0)
    tile, row, col = cells[available].T
    lt, lr, lc = late_cells[available].T
    bed, early, late = (np.full(len(source), np.nan) for _ in range(3))
    bed[available] = fields['bed'][tile*shape[0]+row, col]
    early[available] = fields['h'][tile*shape[0]+row, col]
    late_field = np.load(late_path, mmap_mode='r', allow_pickle=False)
    if late_field.shape != (len(grids)*shape[0], shape[1]) or late_field.dtype != np.dtype('<f8'):
        raise ValueError('Invalid late field')
    late[available] = late_field[lt*shape[0]+lr, lc]
    for owner in np.unique(lt):
        path = original.parent/manifest['packages'][owner]/'bed.npy'
        if sha(path) != manifest['inputs'][owner]['files']['bed.npy']:
            raise ValueError('Cook bed changed')
        values = np.load(path, mmap_mode='r', allow_pickle=False)
        use = lt == owner
        if not np.array_equal(values[lr[use], lc[use]], bed[available][use]):
            raise ValueError('Compared geometry differs between epochs')
        paths.append(path)
    if (early[available] < 0).any() or (late[available] < 0).any():
        raise ValueError('Negative source depth')
    focus = np.array([meta['focus_x_cm'], meta['focus_y_cm']*meta['world_y_sign']])*.01
    triangles = common_triangles(source, nx, ny, early, late, focus, args.radius_m)
    if not len(triangles):
        raise ValueError('No common wet triangles')
    xy = source[triangles, 1:3]
    a, b = xy[:, 1]-xy[:, 0], xy[:, 2]-xy[:, 0]
    areas = abs(a[:, 0]*b[:, 1]-a[:, 1]*b[:, 0])*.5
    statistics = {}
    for label, stage in dict(bed=bed, early=bed+early, late=bed+late, captured=source[:, 4]).items():
        slopes = np.degrees(np.arctan(np.linalg.norm(gradients(xy, stage[triangles]), axis=1)))
        statistics[label] = dict(area_at_least_30_degrees_m2=float(areas[slopes >= 30].sum()),
                                 maximum_degrees=float(slopes.max()))
    used = np.unique(triangles)
    report = dict(schema='raftsim.carrier_source_epoch_comparison.v1', accepted=False, early_time_seconds=atlas['source_time_seconds'],
        late_time_seconds=complete['time_seconds'], captured_world_seconds=meta['world_seconds'],
        radius_m=args.radius_m, common_wet_triangles=len(triangles), common_wet_area_m2=float(areas.sum()),
        common_used_vertices=len(used), unavailable_or_off_lattice_vertices=int((~available).sum()),
        maximum_captured_bed_error_m=float(abs(source[used, 4]-source[used, 5]-bed[used]).max()),
        source_geometry_equal_at_compared_cells=True,
        absolute_depth_change_quantiles_m=np.quantile(abs(late[used]-early[used]), [0, .5, .95, 1]).tolist(),
        signed_late_minus_early_depth_quantiles_m=np.quantile(late[used]-early[used], [0, .5, .95, 1]).tolist(),
        source_triangle_slopes=statistics, input_sha256={str(p.resolve()): sha(p) for p in paths},
        scope='Exact source lattice vertices only; shared wet triangle subset at both epochs and in the capture. Bed values match exactly between immutable epochs. Not rendered triangles, no dry/off-grid extrapolation, no pixel matching, settling, visual/physical acceptance or runtime promotion. Quantiles describe shared used vertices, not the whole river.')
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    print(json.dumps({k: v for k, v in report.items() if k != 'input_sha256'}, indent=2))


if __name__ == '__main__':
    main()
