"""Rebuild the render/collision terrain tiles whose submerged vertices change.

The normal FullReach ground is 390 coarse tiles (256 m) and 51 captured
context tiles (1024 m), each a source-exact 2 m triangle mesh whose vertex
heights index one grid (source_grid_vertex_index). This keeps every tile's
vertex XY, triangles and index unchanged and only re-reads the heights from a
discharge-consistent bed grid, so the rendered and colliding riverbed is the
same surface the hydraulic cook samples. Unchanged tiles are not rewritten.

Numpy only. Args: bed_dir output_dir
Writes output_dir/{coarse,context1024}/<tile>.npz plus manifest.json in the
source tile-manifest format (only changed tiles listed).
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
SETS = (
    ('coarse', BASE / 'composite_terrain/render_tiles/manifest.json', BASE / 'composite_terrain/manifest.json'),
    ('context1024', BASE / 'source_context_extension/render_tiles_1024m/manifest.json', BASE / 'source_context_extension/manifest.json'),
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bed_dir', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    assert not out.exists(), 'Fresh output required'
    bed_manifest = json.loads((args.bed_dir / 'manifest.json').read_text())
    bed_path = ROOT / bed_manifest['outputs']['coarse_bed']['path']
    assert sha(bed_path) == bed_manifest['outputs']['coarse_bed']['sha256']
    with np.load(bed_path) as a:
        bed = a['coarse_bed_navd88_m']
    bx0, by0 = bed_manifest['grid']['first_vertex_utm_m']
    cell = bed_manifest['grid']['cell_m']
    prior_path = ROOT / bed_manifest['inputs']['previous_prior_bed']['path']
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from tiff_numpy import read_geotiff
    prior, _, _ = read_geotiff(prior_path)
    coordinates = json.loads((BASE / 'playable_route/coordinate_map.json').read_text())
    datum = coordinates['vertical_datum_m']
    out.mkdir(parents=True)
    summary = {}
    for label, manifest_path, grid_manifest_path in SETS:
        source = json.loads(manifest_path.read_text())
        grid = json.loads(grid_manifest_path.read_text())['grid']
        gx0, gy0 = grid['first_vertex_utm_m']
        gshape = grid['shape']
        col_offset = int(round((gx0 - bx0) / cell)); row_offset = int(round((by0 - gy0) / cell))
        assert grid['cell_m'] == cell and row_offset == 0 and col_offset >= 0
        sub = out / label; sub.mkdir()
        records, changed_vertices, max_change = [], 0, 0.0
        for tile in source['tiles']:
            path = ROOT / tile['path']
            assert sha(path) == tile['sha256'], tile['name']
            with np.load(path) as a:
                xyz, tri, index = a['xyz_local_m'].copy(), a['triangles'], a['source_grid_vertex_index']
            r, c = np.divmod(index, gshape[1])
            # The source tile heights must equal the previous prior grid (proves the index mapping).
            old = prior[r + row_offset, c + col_offset].astype(np.float64) - datum
            assert np.array_equal(old, xyz[:, 2]), f'{tile["name"]}: tile heights differ from the previous grid'
            new = bed[r + row_offset, c + col_offset].astype(np.float64) - datum
            assert np.isfinite(new).all()
            delta = new - xyz[:, 2]
            if not np.any(delta != 0):
                continue
            xyz[:, 2] = new
            target = sub / (tile['name'] + '.npz')
            np.savez_compressed(target, xyz_local_m=xyz, triangles=tri, source_grid_vertex_index=index)
            row = dict(tile)
            row.update(path=target.relative_to(ROOT).as_posix(), sha256=sha(target), retained_source_path=tile['path'],
                       retained_source_sha256=tile['sha256'], changed_vertex_count=int((delta != 0).sum()),
                       maximum_absolute_height_change_m=float(np.abs(delta).max()))
            records.append(row)
            changed_vertices += int((delta != 0).sum()); max_change = max(max_change, float(np.abs(delta).max()))
        report = dict(schema=source.get('schema', 'raftsim.south_fork.cartesian_terrain_tiles.v1'),
                      revision='discharge-consistent submerged bed', source_tile_manifest=manifest_path.relative_to(ROOT).as_posix(),
                      source_tile_manifest_sha256=sha(manifest_path), bed_manifest=(args.bed_dir / 'manifest.json').resolve().relative_to(ROOT).as_posix(),
                      bed_manifest_sha256=sha(args.bed_dir / 'manifest.json'), vertex_xy_triangles_and_indices_unchanged=True,
                      only_changed_tiles_listed=True, unchanged_tile_count=len(source['tiles']) - len(records),
                      changed_vertex_count=changed_vertices, maximum_absolute_height_change_m=max_change,
                      no_simplification=True, normal_map_integrated=False, tiles=records)
        (sub / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
        summary[label] = dict(changed_tiles=len(records), of=len(source['tiles']), changed_vertices=changed_vertices, max_change_m=max_change)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
