"""Export only additive context triangles, retaining every existing mesh."""
import hashlib
import json
import argparse
from pathlib import Path
import numpy as np
from south_fork_composite_terrain import CompositeTerrainSampler, coarse_mesh_tiles

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
EXT = BASE/'source_context_extension'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tile-quads', type=int, default=128)
    args = parser.parse_args()
    assert args.tile_quads in (128, 512)
    source = json.loads((EXT/'manifest.json').read_text())
    terrain = CompositeTerrainSampler(BASE/'composite_terrain', EXT)
    coordinates = json.loads((BASE/'playable_route/coordinate_map.json').read_text())
    out = EXT/('render_tiles' if args.tile_quads == 128 else 'render_tiles_1024m')
    assert not out.exists(), 'Keep existing tile exports'
    out.mkdir()
    records = []
    for tile in coarse_mesh_tiles(terrain.coarse, terrain.supplemental_quads,
        terrain.x0, terrain.y0, terrain.cell, coordinates['vertical_datum_m'], tile_quads=args.tile_quads):
        prefix = 'context' if args.tile_quads == 128 else 'context1024'
        name = f"{prefix}_{tile['row']:04d}_{tile['col']:04d}"
        path = out/(name+'.npz')
        np.savez_compressed(path, xyz_local_m=tile['xyz_local_m'], triangles=tile['triangles'],
            source_grid_vertex_index=tile['source_grid_vertex_index'])
        offset = np.asarray(tile['origin_utm_m'])-coordinates['origin_utm_m']
        records.append(dict(name=name, path=path.relative_to(ROOT).as_posix(),
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(), origin_utm_m=tile['origin_utm_m'],
            actor_translation_cm=[offset[0]*100,-offset[1]*100,0.], actor_scale=[1.,-1.,1.],
            vertex_count=len(tile['xyz_local_m']),triangle_count=len(tile['triangles'])))
    assert sum(t['triangle_count'] for t in records) == source['supplemental_triangle_count']
    report = dict(schema='raftsim.south_fork.cartesian_terrain_tiles.v1',
        source_composite_manifest_sha256=hashlib.sha256((EXT/'manifest.json').read_bytes()).hexdigest(),
        source_coordinate_map_sha256=hashlib.sha256((BASE/'playable_route/coordinate_map.json').read_bytes()).hexdigest(),
        no_simplification=True, additive_only=True, no_overlap_with_original_terrain=True,
        maximum_tile_width_m=args.tile_quads*terrain.cell,
        normal_map_integrated=False, tiles=records)
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(tiles=len(records),triangles=sum(t['triangle_count'] for t in records)),indent=2))


if __name__ == '__main__':
    main()
