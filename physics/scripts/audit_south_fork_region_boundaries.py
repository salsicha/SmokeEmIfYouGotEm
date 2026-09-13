"""Describe captured wet boundary geometry before choosing hydraulic closures.

No inflow direction, settled stage or discharge is inferred from this audit.
It explicitly checks whether the old west-inlet / bank-side assumption applies.
"""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/hydraulic_regions_context'


def main():
    source = BASE/'manifest.json'
    manifest = json.loads(source.read_text())
    output = BASE/'boundary_geometry_audit.json'
    assert manifest['completed'] and not output.exists()
    regions = []
    slices = dict(west=(slice(None),0),east=(slice(None),-1),south=(0,slice(None)),north=(-1,slice(None)))
    for record in manifest['regions']:
        path = ROOT/record['geometry_file']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['geometry_sha256']
        with np.load(path,allow_pickle=False) as arrays:
            water, surface = arrays['captured_water_mask'].astype(bool), arrays['captured_surface_navd88_m']
        edges = {}
        for edge, index in slices.items():
            wet, elevations = water[index], surface[index]
            starts = np.flatnonzero(np.diff(np.r_[False,wet].astype(int)) == 1)
            ends = np.flatnonzero(np.diff(np.r_[wet,False].astype(int)) == -1)
            assert len(starts) == len(ends)
            segments = [dict(first_cell=int(a),last_cell=int(b),
                             captured_surface_min_navd88_m=float(elevations[a:b+1].min()),
                             captured_surface_max_navd88_m=float(elevations[a:b+1].max()))
                        for a,b in zip(starts,ends)]
            edges[edge] = dict(captured_wet_cells=int(wet.sum()),segments=segments)
        regions.append(dict(name=record['name'],edges=edges,
                            active_edges=[edge for edge,value in edges.items() if value['captured_wet_cells']]))
    report = dict(source_manifest_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  region_count=len(regions),
                  regions_with_north_or_south_water=sum(bool(set(r['active_edges']) & {'north','south'}) for r in regions),
                  regions_with_no_west_water=sum('west' not in r['active_edges'] for r in regions),
                  regions_with_multiple_wet_segments_on_one_edge=sum(any(len(e['segments'])>1 for e in r['edges'].values()) for r in regions),
                  wet_edge_counts={edge:sum(edge in r['active_edges'] for r in regions) for edge in slices},
                  regions=regions,
                  captured_surface_is_not_settled_hydraulic_stage=True,
                  boundary_flow_directions_determined=False,hydraulic_state_solved=False,
                  normal_map_integrated=False)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='regions'},indent=2))


if __name__ == '__main__':
    main()
