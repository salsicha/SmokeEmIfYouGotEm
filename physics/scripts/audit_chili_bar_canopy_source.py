"""Independently replay EVERY provider node against the retained canopy crop."""
import argparse
import hashlib
import json
from pathlib import Path

import laspy
import numpy as np
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
OUT = BASE/'chili_bar/canopy_20260918'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError('Retain prior source audit')
    source_path = OUT/'source.json'
    source = json.loads(source_path.read_text())
    paths = {}
    for key,record in source['provider_sources'].items():
        path = (ROOT/record['file']).resolve()
        assert path.is_relative_to(ROOT) and sha(path) == record['sha256'], key
        assert path.stat().st_size == record['bytes']
        paths[key] = path
    for name,digest in source['sources'].items():
        path = (ROOT/name).resolve()
        assert path.is_relative_to(ROOT) and sha(path) == digest
    payload = OUT/'classified_returns.npz'
    assert sha(payload) == source['payload_sha256']
    metadata = json.loads(paths['ept.json'].read_text())
    footprint = source['bounds_utm_m']
    project = Transformer.from_crs(32610,3857,always_xy=True)
    crop = project.transform_bounds(*(footprint[key] for key in ('xmin','ymin','xmax','ymax')))
    # A separate traversal implementation, not the extraction helper.
    complete_nodes, pending, visited = {}, ['0-0-0-0'], set()
    bounds = metadata['bounds']
    while pending:
        key = pending.pop()
        assert key not in visited
        visited.add(key)
        page = json.loads(paths['ept-hierarchy/'+key+'.json'].read_text())
        assert page[key] > 0
        for node,count in page.items():
            depth,x,y,z = map(int,node.split('-'))
            widths = [(bounds[i+3]-bounds[i])/2**depth for i in range(3)]
            left,bottom = bounds[0]+x*widths[0],bounds[1]+y*widths[1]
            if left > crop[2] or left+widths[0] < crop[0] or bottom > crop[3] or bottom+widths[1] < crop[1]:
                continue
            if count == -1:
                pending.append(node)
            else:
                assert count > 0 and node not in complete_nodes
                complete_nodes[node] = count
    names = sorted(complete_nodes,key=lambda key:tuple(map(int,key.split('-'))))
    assert names == [row['node'] for row in source['provider_node_headers']]
    assert {name for name in paths if name.startswith('ept-data/')} == {'ept-data/'+name+'.laz' for name in names}
    with np.load(payload,allow_pickle=False) as archive:
        data = {key:archive[key] for key in ('east_m','north_m','navd88_m','classification','source_node',
            'source_record','provider_xyz_integer','gps_time','point_source_id')}
    index = data['source_node']
    assert np.all(index[1:] >= index[:-1]) and len(index) == source['return_count']
    to_utm = Transformer.from_crs(3857,32610,always_xy=True)
    verified = 0
    for node_index,name in enumerate(names):
        cloud = laspy.read(paths['ept-data/'+name+'.laz'])
        assert len(cloud) == complete_nodes[name]
        east,north = to_utm.transform(np.asarray(cloud.x),np.asarray(cloud.y))
        mask = ((east >= footprint['xmin']) & (east < footprint['xmax']) & (north > footprint['ymin'])
                & (north <= footprint['ymax']) & (np.asarray(cloud.withheld) == 0))
        ids = np.flatnonzero(mask)
        start,stop = np.searchsorted(index,[node_index,node_index+1])
        assert stop-start == len(ids)
        np.testing.assert_array_equal(data['source_record'][start:stop],ids)
        expected = dict(east_m=east[ids],north_m=north[ids],navd88_m=np.asarray(cloud.z)[ids],
            classification=np.asarray(cloud.classification)[ids],gps_time=np.asarray(cloud.gps_time)[ids],
            point_source_id=np.asarray(cloud.point_source_id)[ids],
            provider_xyz_integer=np.column_stack((cloud.X[ids],cloud.Y[ids],cloud.Z[ids])))
        for key,values in expected.items():
            np.testing.assert_array_equal(data[key][start:stop],values,err_msg=f'{name}: {key}')
        verified += len(ids)
        if node_index % 100 == 0:
            print('Verified full source node',node_index+1,'/',len(names),flush=True)
    assert verified == len(index)
    report = dict(schema='raftsim.chili_bar.ept_source_audit.v1',passed=True,
        source_manifest_sha256=sha(source_path),payload_sha256=sha(payload),provider_nodes=len(names),
        source_points_before_crop=sum(complete_nodes.values()),retained_nonwithheld_points=verified,
        full_resolution_hierarchy_independently_replayed=True,every_record_replayed_exactly=True,
        source_hashes_unchanged=True,original_las_record_identity_claimed=False,
        measured_tree_inventory=False,placement_or_visual_acceptance=False)
    with args.report.open('x') as stream:
        json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(report),flush=True)


if __name__ == '__main__':
    main()
