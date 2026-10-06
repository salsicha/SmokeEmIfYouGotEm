"""Bind source-exact hydraulic XY to the full river world, not river chainage."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'


def main():
    source = BASE/'hydraulic_regions_context/manifest.json'
    regions = json.loads(source.read_text())
    audit = json.loads((source.parent/'overlap_audit.json').read_text())
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert regions['completed'] and audit['manifest_sha256'] == digest
    assert audit['shared_values_bit_identical']
    extent = regions['region_extent_m']
    origins = [r['grid_origin_local_m'] for r in regions['regions']]
    bounds = [min(p[0] for p in origins), min(p[1] for p in origins),
              max(p[0]+extent[0] for p in origins), max(p[1]+extent[1] for p in origins)]
    result = dict(schema='raftsim.cartesian_water_coordinate_map.v1',
                  hydraulic_bounds_m=bounds, world_y_sign=-1,
                  vertical_datum_m=regions['vertical_datum_navd88_m'],
                  world_origin_utm_m=regions['world_origin_utm_m'],
                  source_geometry_regions_sha256=digest,
                  progress_coordinate_map=(BASE/'playable_route/coordinate_map.json').relative_to(ROOT).as_posix(),
                  notes='Hydraulic x=east, y=north relative to world origin; neither is downstream progress. Bounds are broad phase, not wet coverage.',
                  hydraulic_state_solved=False, normal_map_integrated=False)
    output = source.parent/'coordinate_map.json'
    assert not output.exists(), 'Preserve coordinate-map revisions'
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
