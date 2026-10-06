"""Read-only candidate bed/tile consistency audit; not engine acceptance.

Checks every retained or replacement tile against its declared grid, including
the 71-column coarse/context offset. Never imports assets or starts a cook.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def verified(path, expected):
    require(sha(path) == expected, f'Hash mismatch: {path}')
    return path


def tile_check(old, new, prior, bed, grid_shape, offset, datum):
    """Verify an entire tile, including unchanged vertices; return changed count."""
    xyz, revised = old['xyz_local_m'], new['xyz_local_m']
    require(xyz.shape == revised.shape, 'Vertex shape changed')
    require(np.array_equal(xyz[:, :2], revised[:, :2]), 'Vertex XY changed')
    for key in ('triangles', 'source_grid_vertex_index'):
        require(np.array_equal(old[key], new[key]), f'{key} changed')
    index = old['source_grid_vertex_index']
    require(np.issubdtype(index.dtype, np.integer), 'Noninteger grid indices')
    require(np.all((index >= 0) & (index < np.prod(grid_shape))), 'Grid index out of bounds')
    rows, cols = np.divmod(index, grid_shape[1])
    rows, cols = rows + offset[0], cols + offset[1]
    expected_old = prior[rows, cols].astype(np.float64) - datum
    expected_new = bed[rows, cols].astype(np.float64) - datum
    require(np.isfinite(expected_new).all(), 'Nonfinite bed')
    require(np.array_equal(xyz[:, 2], expected_old), 'Prior/grid mismatch')
    require(np.array_equal(revised[:, 2], expected_new), 'Candidate/grid mismatch')
    delta = revised[:, 2] - xyz[:, 2]
    return int(np.count_nonzero(delta)), float(np.max(np.abs(delta), initial=0))


def grid_check(prior, bed, mask, grid, rectangle):
    require(prior.shape == bed.shape == mask.shape == tuple(grid['shape']), 'Grid shape mismatch')
    require(prior.dtype == bed.dtype, 'Bed dtype changed')
    x0, y0 = grid['first_vertex_utm_m']
    cell = grid['cell_m']
    east = x0 + np.arange(bed.shape[1]) * cell
    xmin, ymin, xmax, ymax = rectangle
    protected_cols = (east >= xmin) & (east <= xmax)
    counts = dict(changed_grid_vertices=0, dry_vertices_checked=0, protected_vertices_checked=0,
                  retained_nodata_vertices=0)
    # Chunking avoids large temporary arrays while another session cooks.
    for start in range(0, bed.shape[0], 128):
        stop = min(start + 128, bed.shape[0])
        a, b, m = prior[start:stop], bed[start:stop], mask[start:stop]
        finite = np.isfinite(a)
        require(np.array_equal(finite, np.isfinite(b)), 'Finite grid coverage changed')
        require(a[~finite].tobytes() == b[~finite].tobytes(), 'Nodata values changed')
        dry = m == 0
        require(a[dry].tobytes() == b[dry].tobytes(), 'Dry grid vertices changed')
        north = y0 - np.arange(start, stop) * cell
        protected = ((north >= ymin) & (north <= ymax))[:, None] & protected_cols[None, :]
        require(a[protected].tobytes() == b[protected].tobytes(), 'Protected rapid grid changed')
        counts['changed_grid_vertices'] += int(np.count_nonzero(a[finite] != b[finite]))
        counts['retained_nodata_vertices'] += int(np.count_nonzero(~finite))
        counts['dry_vertices_checked'] += int(np.count_nonzero(dry))
        counts['protected_vertices_checked'] += int(np.count_nonzero(protected))
    return counts


def audit(candidate):
    manifests = {label: candidate / label / 'manifest.json' for label in ('coarse', 'context1024')}
    reports = {label: json.loads(path.read_text()) for label, path in manifests.items()}
    first = reports['coarse']
    bed_manifest_path = verified(ROOT / first['bed_manifest'], first['bed_manifest_sha256'])
    manifest = json.loads(bed_manifest_path.read_text())
    for report in reports.values():
        require(report['bed_manifest_sha256'] == first['bed_manifest_sha256'], 'Mixed bed versions')
    from tiff_numpy import read_geotiff
    inputs = manifest['inputs']
    prior, _, _ = read_geotiff(verified(ROOT / inputs['previous_prior_bed']['path'], inputs['previous_prior_bed']['sha256']))
    mask, _, _ = read_geotiff(verified(ROOT / inputs['water_mask']['path'], inputs['water_mask']['sha256']))
    verified(ROOT / inputs['captured_surface']['path'], inputs['captured_surface']['sha256'])
    route = json.loads(verified(ROOT / inputs['route']['path'], inputs['route']['sha256']).read_text())
    output = manifest['outputs']['coarse_bed']
    with np.load(verified(ROOT / output['path'], output['sha256'])) as archive:
        bed = archive[output['array']]
    result = dict(schema='raftsim.south_fork.discharge_bed_tile_audit.v1',
                  bed_manifest_sha256=first['bed_manifest_sha256'], bed_sha256=output['sha256'],
                  grid=grid_check(prior, bed, mask, manifest['grid'], manifest['parameters']['protected_rectangle_utm_m']),
                  tile_sets={}, engine_assets_checked=False, collision_checked=False,
                  cooked_fields_checked=False, normal_launch_checked=False,
                  full_reconstruction_accepted=False, measured_bathymetry=False)
    for label, report in reports.items():
        source_path = verified(ROOT / report['source_tile_manifest'], report['source_tile_manifest_sha256'])
        source = json.loads(source_path.read_text())
        grid_dir = 'composite_terrain' if label == 'coarse' else 'source_context_extension'
        grid = json.loads((BASE / grid_dir / 'manifest.json').read_text())['grid']
        require(grid['cell_m'] == manifest['grid']['cell_m'], 'Cell size mismatch')
        gx, gy = grid['first_vertex_utm_m']
        bx, by = manifest['grid']['first_vertex_utm_m']
        offset_f = np.array([(by - gy), (gx - bx)]) / grid['cell_m']
        require(np.array_equal(offset_f, np.rint(offset_f)), 'Nonintegral grid offset')
        offset = np.rint(offset_f).astype(int)
        require(np.all(offset >= 0) and np.all(offset + grid['shape'] <= np.array(bed.shape)), 'Grid offset outside bed')
        replacements = {tile['name']: tile for tile in report['tiles']}
        require(len(replacements) == len(report['tiles']), 'Duplicate replacement tile')
        source_names = {tile['name'] for tile in source['tiles']}
        require(set(replacements) <= source_names, 'Unknown replacement tile')
        count, maximum, vertices = 0, 0.0, 0
        for tile in source['tiles']:
            old_path = verified(ROOT / tile['path'], tile['sha256'])
            replacement = replacements.get(tile['name'])
            new_path = old_path
            if replacement:
                require(replacement['retained_source_path'] == tile['path'] and replacement['retained_source_sha256'] == tile['sha256'], 'Wrong retained source')
                # All source metadata (origin, actor transform, bounds, topology
                # counts) must be retained; only file path/hash are replaced.
                for key, value in tile.items():
                    if key not in ('path', 'sha256'):
                        require(replacement[key] == value, f'{tile["name"]}: metadata changed: {key}')
                new_path = verified(ROOT / replacement['path'], replacement['sha256'])
            with np.load(old_path) as old, np.load(new_path) as new:
                changed, delta = tile_check(old, new, prior, bed, grid['shape'], offset, route['vertical_datum_m'])
                vertices += len(old['xyz_local_m'])
            require(bool(changed) == bool(replacement), f'{tile["name"]}: replacement coverage mismatch')
            if replacement:
                require(changed == replacement['changed_vertex_count'] and delta == replacement['maximum_absolute_height_change_m'], 'Tile change statistics mismatch')
            count += changed
            maximum = max(maximum, delta)
        require(count == report['changed_vertex_count'] and maximum == report['maximum_absolute_height_change_m'], 'Set change statistics mismatch')
        require(len(source['tiles']) - len(replacements) == report['unchanged_tile_count'], 'Unchanged tile count mismatch')
        # All neighboring tile vertices reference the same exact global grid;
        # equal indexed heights also establish shared-vertex continuity.
        result['tile_sets'][label] = dict(tiles_checked=len(source['tiles']), replacements=len(replacements),
                                         vertices_checked=vertices, changed_vertex_occurrences=count,
                                         maximum_height_change_m=maximum, grid_offset_row_col=offset.tolist(),
                                         candidate_manifest_sha256=sha(manifests[label]))
    result['passed'] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    require(not args.report.exists(), 'Fresh report required')
    result = audit(args.candidate)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
