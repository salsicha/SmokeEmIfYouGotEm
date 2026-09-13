"""Locate physical wet exits of source-exact, disjoint Cartesian core tiles.

No terrain edits, flow directions, settled stage or production promotion.
This checks actual 1 m core faces before choosing river exterior conditions.
"""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'


def main():
    source = BASE/'hydraulic_regions_context/manifest.json'
    output = source.parent/'disjoint_core_boundary_audit.json'
    assert not output.exists(), 'Retain previous core-boundary evidence'
    manifest = json.loads(source.read_text())
    assert manifest['completed'] and manifest['grid_spacing_m'] == 1.
    assert manifest['supplemental_regions'] == []
    records = manifest['regions']
    keys = [tuple(np.rint(np.asarray(r['center_utm_m'])/80).astype(int)) for r in records]
    assert len(set(keys)) == len(keys)
    lookup = {key: i for i, key in enumerate(keys)}
    route = json.loads((BASE/'playable_route/coordinate_map.json').read_text())
    points = np.asarray(route['points'])
    from scipy.spatial import cKDTree
    tree = cKDTree(points[:, 1:3]+np.asarray(route['origin_utm_m']))
    directions = dict(west=(-1,0), east=(1,0), south=(0,-1), north=(0,1))
    indices = dict(west=(slice(120,200),120),east=(slice(120,200),199),
                   south=(120,slice(120,200)),north=(199,slice(120,200)))
    exterior = []
    wet_cells = positive_depth_cells = shared_faces = 0
    owners = {str(k): 0 for k in (1,2,3,4)}
    for i, (record,key) in enumerate(zip(records,keys)):
        path = ROOT/record['geometry_file']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['geometry_sha256']
        assert np.array_equal(np.asarray(record['center_utm_m']), np.asarray(key)*80)
        with np.load(path, allow_pickle=False) as arrays:
            bed = arrays['bed_navd88_m']
            surface = arrays['captured_surface_navd88_m']
            water = arrays['captured_water_mask'].astype(bool)
            owner = arrays['terrain_owner'][120:200,120:200]
        depth = np.where(water,np.maximum(0.,surface-bed),0.)
        assert bed.shape == surface.shape == water.shape == (321,321)
        assert np.isfinite(bed).all() and np.isfinite(surface).all()
        wet_cells += int(water[120:200,120:200].sum())
        positive_depth_cells += int((depth[120:200,120:200]>1.e-6).sum())
        for k in owners:
            owners[k] += int((owner==int(k)).sum())
        for edge, delta in directions.items():
            neighbor = (key[0]+delta[0],key[1]+delta[1])
            if neighbor in lookup:
                shared_faces += 1
                continue
            index = indices[edge]
            wet = water[index]
            h = depth[index]
            active = np.flatnonzero(wet | (h>1.e-6))
            if len(active):
                lower = np.asarray(record['center_utm_m'])-40
                xy = np.column_stack((np.full(len(active),0 if edge=='west' else 79),active)) if edge in ('west','east') else np.column_stack((active,np.full(len(active),0 if edge=='south' else 79)))
                xy = xy+lower
                distance, closest = tree.query(xy)
                station_range = [float(points[closest,0].min()),float(points[closest,0].max())]
                max_distance = float(distance.max())
            else:
                station_range, max_distance = None, None
            exterior.append(dict(region=record['name'],edge=edge,
                captured_wet_cells=int(wet.sum()),positive_depth_cells=int((h>1.e-6).sum()),
                initial_wet_area_m2=float(h.sum()), nearest_axis_station_range_m=station_range,
                maximum_axis_distance_m=max_distance))
        if (i+1)%100 == 0:
            print(f'Checked {i+1}/{len(records)} exact core tiles',flush=True)
    active_edges = [e for e in exterior if e['captured_wet_cells'] or e['positive_depth_cells']]
    report = dict(source_manifest_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        core_tile_shape=[80,80],source_crop_half_open=[120,200],tile_count=len(records),
        cell_count=len(records)*80*80,captured_wet_cells=wet_cells,positive_initial_depth_cells=positive_depth_cells,
        terrain_owner_counts=owners,internal_shared_faces=shared_faces//2,
        exterior_face_count=len(exterior),exterior_wet_face_count=len(active_edges),
        exterior_captured_wet_cells=sum(e['captured_wet_cells'] for e in exterior),
        exterior_positive_depth_cells=sum(e['positive_depth_cells'] for e in exterior),
        active_exterior_faces=active_edges,
        source_arrays_changed=False,hydraulic_state_solved=False,normal_map_integrated=False,
        physical_boundary_conditions_determined=False,
        notes='Source-exact disjoint core geometry only. If external faces are all dry, putting inflow on a tile edge would not connect to the captured river; physical endpoints require separate treatment.')
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__':
    main()
