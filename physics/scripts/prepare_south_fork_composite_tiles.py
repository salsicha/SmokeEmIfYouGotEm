"""Prepare non-overlapping full-river mesh packets for native asset import."""
import hashlib
import json
from pathlib import Path
import numpy as np
from south_fork_composite_terrain import CompositeTerrainSampler, coarse_mesh_tiles

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'


def main():
    terrain = CompositeTerrainSampler(BASE/'composite_terrain')
    coordinates = json.loads((BASE/'playable_route/coordinate_map.json').read_text())
    out = BASE/'composite_terrain/render_tiles'
    if out.exists():
        raise ValueError('Existing tile packet needs an explicit revision, not overwrite')
    out.mkdir()
    records = []
    for tile in coarse_mesh_tiles(terrain.coarse, terrain.valid_quads, terrain.x0, terrain.y0,
                                 terrain.cell, coordinates['vertical_datum_m']):
        name = f"coarse_{tile['row']:04d}_{tile['col']:04d}"
        path = out/(name+'.npz')
        np.savez_compressed(path, xyz_local_m=tile['xyz_local_m'], triangles=tile['triangles'],
                            source_grid_vertex_index=tile['source_grid_vertex_index'])
        offset = np.asarray(tile['origin_utm_m'])-coordinates['origin_utm_m']
        records.append(dict(name=name, path=path.relative_to(ROOT).as_posix(),
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            origin_utm_m=tile['origin_utm_m'], actor_translation_cm=[offset[0]*100, -offset[1]*100, 0.],
            actor_scale=[1., -1., 1.], vertex_count=len(tile['xyz_local_m']), triangle_count=len(tile['triangles'])))
    assert sum(t['triangle_count'] for t in records) == terrain.manifest['coarse_triangle_count']
    report = dict(schema='raftsim.south_fork.cartesian_terrain_tiles.v1',
        source_composite_manifest_sha256=hashlib.sha256((BASE/'composite_terrain/manifest.json').read_bytes()).hexdigest(),
        source_coordinate_map_sha256=hashlib.sha256((BASE/'playable_route/coordinate_map.json').read_bytes()).hexdigest(),
        maximum_tile_width_m=256., no_simplification=True, original_coarse_diagonals_preserved=True,
        full_river_coverage=True, rapid_and_seam_are_separate_components=True,
        normal_map_integrated=False, tiles=records)
    (out/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(tile_count=len(records), triangle_count=sum(t['triangle_count'] for t in records),
        manifest=(out/'manifest.json').relative_to(ROOT).as_posix()), indent=2))


if __name__ == '__main__':
    main()
