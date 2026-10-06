"""Disjoint source-exact hydraulic cores, with interior wet-edge context.

Copies existing 1 m samples only. No interpolated terrain, velocity, settled
stage, discharge or playable promotion is supplied by this geometry manifest.
"""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach'
FIELDS = ('bed_navd88_m','captured_surface_navd88_m','captured_water_mask','terrain_owner')
EDGES = dict(west=(-1,0),east=(1,0),south=(0,-1),north=(0,1))


def main():
    from scipy.spatial import cKDTree
    source = BASE/'hydraulic_regions_context/manifest.json'
    output = BASE/'coupled_geometry'
    assert not output.exists(), 'Preserve earlier geometry evidence; use an explicit new revision'
    manifest = json.loads(source.read_text())
    assert manifest['completed'] and manifest['grid_spacing_m'] == 1.
    records = manifest['regions']
    centers = np.asarray([r['center_utm_m'] for r in records],dtype=np.int64)
    route = json.loads((BASE/'playable_route/coordinate_map.json').read_text())
    points = np.asarray(route['points'])
    origin = np.asarray(route['origin_utm_m'])
    tree = cKDTree(points[:,1:3]+origin)
    cores, provenance = {}, {}
    checked_sources = set()

    def load_core(key):
        center = np.asarray(key)*80
        # A full 80x80 core must be copied from one existing 321x321 packet.
        candidates = np.flatnonzero(np.max(np.abs(centers-center),axis=1)<=120)
        if not len(candidates):
            raise ValueError(f'Existing source context cannot cover new core {key}; no extrapolation allowed')
        index = min(candidates,key=lambda i: np.max(np.abs(centers[i]-center)))
        record = records[index]
        path = ROOT/record['geometry_file']
        if index not in checked_sources:
            assert hashlib.sha256(path.read_bytes()).hexdigest() == record['geometry_sha256']
            checked_sources.add(index)
        offset = center-40-(centers[index]-160)
        col,row = map(int,offset)
        assert 0<=col and 0<=row and col+80<=321 and row+80<=321
        with np.load(path,allow_pickle=False) as arrays:
            fields = {name: arrays[name][row:row+80,col:col+80].copy() for name in FIELDS}
        assert all(value.shape==(80,80) for value in fields.values())
        assert np.isfinite(fields[FIELDS[0]]).all() and np.isfinite(fields[FIELDS[1]]).all()
        cores[key] = fields
        provenance[key] = dict(source_geometry_file=record['geometry_file'],source_geometry_sha256=record['geometry_sha256'],
                               source_slice_row_column=[row,col],copied_without_interpolation=True)

    def wet_edges(key):
        water = cores[key]['captured_water_mask'].astype(bool)
        for edge,index in dict(west=(slice(None),0),east=(slice(None),-1),south=(0,slice(None)),north=(-1,slice(None))).items():
            delta = EDGES[edge]
            neighbor = (key[0]+delta[0],key[1]+delta[1])
            if neighbor in cores:
                continue
            active = np.flatnonzero(water[index])
            if not len(active):
                continue
            xy = np.column_stack((np.full(len(active),0 if edge=='west' else 79),active)) if edge in ('west','east') else np.column_stack((active,np.full(len(active),0 if edge=='south' else 79)))
            xy = xy+np.asarray(key)*80-40
            distance, closest = tree.query(xy)
            endpoint = 'upstream' if np.all(closest==0) else 'downstream' if np.all(closest==len(points)-1) else None
            yield edge,neighbor,dict(endpoint=endpoint,captured_wet_cells=len(active),
                nearest_axis_station_range_m=[float(points[closest,0].min()),float(points[closest,0].max())],
                maximum_axis_distance_m=float(distance.max()))

    original_keys = {tuple(center//80) for center in centers}
    assert len(original_keys)==len(centers) and np.all(centers%80==0)
    for key in sorted(original_keys):
        load_core(key)
    iterations = 0
    while True:
        missing = {neighbor for key in list(cores) for _,neighbor,info in wet_edges(key) if info['endpoint'] is None}
        if not missing:
            break
        iterations += 1
        if iterations>8:
            raise ValueError('Interior wet-core expansion did not converge; inspect source context')
        for key in sorted(missing):
            load_core(key)
        print(f'Interior closure iteration {iterations}: added {len(missing)} source-exact cores',flush=True)
    output.mkdir()
    result = dict(schema='raftsim.cartesian_hydraulic_core_geometry.v1',
        source_manifest_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        coordinate_map_sha256=hashlib.sha256((BASE/'hydraulic_regions_context/coordinate_map.json').read_bytes()).hexdigest(),
        grid_spacing_m=1.,core_shape=[80,80],world_origin_utm_m=origin.tolist(),
        vertical_datum_navd88_m=manifest['vertical_datum_navd88_m'],
        original_core_count=len(original_keys),added_interior_context_core_count=len(cores)-len(original_keys),
        interior_closure_iterations=iterations,source_packets_hash_checked=len(checked_sources),
        regions=[],open_geometry_edges=[],completed=False,hydraulic_state_solved=False,
        physical_boundary_conditions_determined=False,normal_map_integrated=False)
    wet_count = 0
    for i,key in enumerate(sorted(cores)):
        name=f'core_{i:04d}'
        path=output/(name+'.npz')
        np.savez_compressed(path,**cores[key])
        center=np.asarray(key)*80
        wet_count += int(cores[key]['captured_water_mask'].sum())
        result['regions'].append(dict(name=name,center_utm_m=center.tolist(),grid_origin_local_m=(center-40-origin).tolist(),
            geometry_file=path.relative_to(ROOT).as_posix(),geometry_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            added_interior_context=key not in original_keys,**provenance[key]))
        for edge,_,info in wet_edges(key):
            assert info['endpoint'] is not None
            result['open_geometry_edges'].append(dict(region=name,edge=edge,**info))
    result.update(completed=True,core_count=len(cores),cell_count=len(cores)*6400,captured_wet_cell_count=wet_count,
        remaining_interior_wet_exterior_faces=0,
        notes='Endpoint classification is nearest-axis geometry, not a prescribed flow or stage. Original core arrays retained exactly; extra interior cores use captured source context. No source geometry edits.')
    (output/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='regions'},indent=2),flush=True)


if __name__ == '__main__':
    main()
