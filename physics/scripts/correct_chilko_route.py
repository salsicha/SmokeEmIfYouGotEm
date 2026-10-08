"""Replace reviewed obsolete FWA branches, preserving all other source vertices.

This selects existing official network geometry and explicitly recorded local
inferred joins. It does not infer a rapid's identity or turn a single-line
stream into surveyed banks. The 20 m half-width is an explicit planform
construction hypothesis for the replacement segments, including their joins.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from pyproj import Transformer
from shapely.geometry import LineString

SCHEMA = 'raftsim.chilko_reviewed_branch_route.v1'
PROJECT = Transformer.from_crs(4326, 3157, always_xy=True)
JOINS_M = .02
REVIEWED_OBJECT_PATHS = (
    (16261065, 16257216, 16255253, 16259663, 16250852, 16258439, 16259586),
    (16247743, 16247905, 16258257, 16256522, 16250325, 16257949, 16253230, 16252785),
)
ACTIVE_OBJECT_PATHS = ((16261065,16257216,16255253,16247905,16258257,16256522,
                       16250325,16257949,16253230,16252785),)
ACTIVE_CONNECTORS = {'16255253:16247905': [125]}
ALIGNMENT_EVIDENCE = Path(__file__).resolve().parents[1]/'data/real_world/chilko_river_bc/production_corridor/chilko_river_lodge_to_taseko_junction/hydrography/route_alignment_evidence_2026_10_07.json'


def retirement_evidence(spec, parent_hash):
    """Read the pre-existing dated image review, never a solved wet mask."""
    if (spec.get('policy')!='retire_reviewed_bar_branches_outside_inferred_active_corridor_v1' or
            spec.get('measured_banks') is not False):
        raise ValueError('Unsupported contemporary planform hypothesis')
    path=Path(spec['evidence']['path'])
    if sha(path)!=spec['evidence']['sha256']:raise ValueError('Changed source-image alignment evidence')
    data=json.loads(path.read_text())
    if (data.get('schema')!='raftsim.chilko_route_alignment_evidence.v1' or
            data.get('route_sha256')!=parent_hash or data.get('observation_crs')!='EPSG:32610' or
            data.get('source_scene',{}).get('id')!='S2B_10UDC_20231020_0_L2A' or
            data.get('named_rapid_placement_authorized') is not False or
            data.get('automatic_route_replacement_authorized') is not False or
            [r['id'] for r in data['observations']]!=['upstream_bar_loop','downstream_bar_loop']):
        raise ValueError('Different or unsupported image-reviewed branch areas')
    bounds=np.asarray([r['inspection_bounds_m'] for r in data['observations']],dtype=float)
    if (bounds.shape!=(2,4) or not np.isfinite(bounds).all() or
            np.any(bounds[:,2:]<=bounds[:,:2]) or np.any(bounds[:,2:]-bounds[:,:2]>500)):
        raise ValueError('Bounded original image-review rectangles required')
    image_receipt=Path(spec['image_capture']['path'])
    if (sha(image_receipt)!=spec['image_capture']['sha256'] or
            spec['image_capture']['sha256']!=data['source_scene']['local_capture_receipt_sha256']):
        raise ValueError('Changed dated image capture')
    capture=json.loads(image_receipt.read_text())
    scene=next(r for r in capture['items'] if r['id']==data['source_scene']['id'])
    folder=image_receipt.parent/scene['id']
    if sha(folder/'item.json')!=scene['item_sha256']:raise ValueError('Changed image scene metadata')
    for asset in scene['assets']:
        if sha(folder/(asset['name']+'.tif'))!=asset['sha256']:
            raise ValueError('Changed captured image pixels')
    return data


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def projected(points):
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 2 or not np.isfinite(points).all():
        raise ValueError('Finite two-dimensional source coordinates required')
    if (np.abs(points[:,0])>180).any() or (np.abs(points[:,1])>90).any():
        raise ValueError('Geographic longitude/latitude coordinates required')
    result=np.column_stack(PROJECT.transform(points[:, 0], points[:, 1]))
    if not np.isfinite(result).all():raise ValueError('Invalid source projection')
    return result


def route_points(data):
    features = data.get('features', [])
    if (data.get('type') != 'FeatureCollection' or len(features) != 1 or
            features[0]['geometry']['type'] != 'LineString'):
        raise ValueError('One source-route LineString required')
    points = np.asarray(features[0]['geometry']['coordinates'], dtype=float)
    xy = projected(points)
    if len(points) < 2 or not LineString(xy).is_simple or (np.linalg.norm(np.diff(xy, axis=0), axis=1) <= 0).any():
        raise ValueError('Simple nondegenerate source route required')
    return points


def stitch(parent_points, network, paths, connectors=None):
    """Trace explicitly reviewed ordered edges, never choose a shortest shortcut."""
    parent_points = np.asarray(parent_points, dtype=float)
    connectors={} if connectors is None else connectors
    used_connectors=set()
    parent_xy = projected(parent_points)
    crs=network.get('crs',{}).get('properties',{}).get('name')
    if (network.get('type')!='FeatureCollection' or
            crs not in (None,'EPSG:4326','urn:ogc:def:crs:EPSG::4326','urn:ogc:def:crs:OGC:1.3:CRS84')):
        raise ValueError('Geographic source-network FeatureCollection required')
    lookup = {}
    for feature in network['features']:
        key = feature['properties']['OBJECTID']
        if key in lookup: raise ValueError('Duplicate source network object')
        lookup[key] = feature
    changes = []
    for ids in paths:
        if len(ids) < 1 or len(set(ids)) != len(ids): raise ValueError('Unique ordered branch edges required')
        parts = []; joins=[]; previous=None
        for key in ids:
            feature = lookup[key]
            if (feature['geometry']['type'] != 'LineString' or
                    feature['properties']['WATERSHED_KEY'] != 356364103):
                raise ValueError('Unrelated branch identity')
            points = np.asarray(feature['geometry']['coordinates'], dtype=float)
            if points.ndim != 2 or points.shape[1] not in (2, 3) or not np.isfinite(points).all():
                raise ValueError('Finite geographic line vertices required')
            # FWA WFS includes cartographic Z. Terrain keeps its independently
            # captured CGVD2013 elevations; do not treat network Z as bathymetry.
            points = points[:, :2]
            # Source FWA lines are downstream-to-upstream here, but verify
            # connectivity instead of assuming digitisation direction globally.
            if not parts:
                end_xy = projected(points[[0, -1]])
                d = np.linalg.norm(end_xy[:, None, :] - parent_xy[None, :, :], axis=-1)
                if d.min() > JOINS_M: raise ValueError('Branch does not start on an existing source vertex')
                end, start_index = np.unravel_index(d.argmin(), d.shape)
                points = points if end == 0 else points[::-1]
            else:
                d = np.linalg.norm(projected(points[[0, -1]]) - projected(parts[-1][-1:])[0], axis=-1)
                connector_key=f'{previous}:{key}'
                if d.min() > JOINS_M and connector_key not in connectors:
                    raise ValueError('Disconnected reviewed branch edges')
                points = points if d.argmin() == 0 else points[::-1]
                if connector_key in connectors:
                    via=connectors[connector_key]
                    if (not via or any(type(i) is not int or not 0<=i<len(parent_points) for i in via)):
                        raise ValueError('Explicit original source vertices required for inferred joins')
                    bridge=np.concatenate([parts[-1][-1:],parent_points[via],points[:1]])
                    lengths=np.linalg.norm(np.diff(projected(bridge),axis=0),axis=1)
                    if (lengths<=JOINS_M).any() or (lengths>250.).any():
                        raise ValueError('Inferred channel joins exceed reviewed local bound')
                    joins.append(dict(between_objects=[previous,key],parent_via_vertices=via,
                                      segment_lengths_m=lengths.tolist(),measured_geometry=False))
                    parts.append(bridge);used_connectors.add(connector_key)
            parts.append(points)
            previous=key
        replacement = np.concatenate([parts[0], *[p[1:] for p in parts[1:]]])
        end_distance = np.linalg.norm(parent_xy - projected(replacement[-1:])[0], axis=1)
        end_index = int(end_distance.argmin())
        if end_distance[end_index] > JOINS_M or end_index <= start_index:
            raise ValueError('Replacement must rejoin downstream source vertex')
        # Preserve original endpoint coordinates exactly, within source rounding.
        snap = np.linalg.norm(projected(replacement[[0, -1]]) - parent_xy[[start_index, end_index]], axis=1)
        replacement[[0, -1]] = parent_points[[start_index, end_index]]
        if not LineString(projected(replacement)).is_simple:
            raise ValueError('Replacement branch intersects itself')
        changes.append(dict(start_vertex=int(start_index), end_vertex=end_index,
                            object_ids=list(ids), endpoint_snap_m=snap.tolist(), points=replacement))
        if joins:changes[-1]['inferred_connectors']=joins
    if used_connectors!=set(connectors):raise ValueError('Unused or unrelated inferred connector')
    changes.sort(key=lambda row: row['start_vertex'])
    if any(a['end_vertex'] > b['start_vertex'] for a, b in zip(changes, changes[1:])):
        raise ValueError('Overlapping branch replacements')
    chunks=[]; last=0
    for row in changes:
        chunks.extend([parent_points[last:row['start_vertex']], row['points'][:-1]])
        last=row['end_vertex']
    chunks.append(parent_points[last:]); result=np.concatenate(chunks)
    result_xy=projected(result); line=LineString(result_xy)
    if not line.is_simple or (np.linalg.norm(np.diff(result_xy,axis=0),axis=1)<=0).any():
        raise ValueError('Corrected complete route intersects or duplicates itself')
    # Bound source-domain displacement; not a claim of position accuracy.
    if not LineString(parent_xy).buffer(256.).covers(line):
        raise ValueError('Branch leaves reviewed original-route terrain corridor')
    return result, changes


def lineage(route):
    """Verify original source, ordered official edges, and complete output bytes."""
    route=Path(route).resolve(); path=route.with_suffix('.route.json')
    data=json.loads(path.read_text())
    if (data.get('schema')!=SCHEMA or data.get('route_sha256')!=sha(route) or
            data.get('linear_branch_half_width_m')!=20. or data.get('measured_banks') is not False):
        raise ValueError('Unsupported corrected-route lineage or width hypothesis')
    connectors=data.get('connectors',{})
    expected_paths=ACTIVE_OBJECT_PATHS if connectors==ACTIVE_CONNECTORS else REVIEWED_OBJECT_PATHS
    if connectors not in ({},ACTIVE_CONNECTORS) or tuple(tuple(row['object_ids']) for row in data['replacements']) != expected_paths:
        raise ValueError('Branch selection was not reviewed against source imagery')
    parent=Path(data['parent_route']['path']); network=Path(data['network']['path'])
    if sha(parent)!=data['parent_route']['sha256'] or sha(network)!=data['network']['sha256']:
        raise ValueError('Corrected-route source changed')
    rebuilt,changes=stitch(route_points(json.loads(parent.read_text())),json.loads(network.read_text()),
                          [row['object_ids'] for row in data['replacements']],connectors)
    if not np.array_equal(rebuilt,route_points(json.loads(route.read_text()))):
        raise ValueError('Route does not reproduce reviewed official branches')
    expected=[{k:v for k,v in row.items() if k!='points'} for row in changes]
    if expected!=data['replacements']: raise ValueError('Changed replacement anchors or source precision')
    if 'planform_retirement' in data:
        if connectors!=ACTIVE_CONNECTORS:raise ValueError('Bar retirement requires the reviewed active channel')
        retirement_evidence(data['planform_retirement'],data['parent_route']['sha256'])
    return data, changes


def compatible_capture_route(route, source_sha256):
    if sha(route)==source_sha256:return True
    if not Path(route).with_suffix('.route.json').exists():return False
    data,_=lineage(route)
    return data['parent_route']['sha256']==source_sha256


def build(parent,network,out,bridge_topology_connectors=False,retire_reviewed_bar_branches=False):
    parent,network,out=map(lambda p:Path(p).resolve(),(parent,network,out))
    receipt_path=out.with_suffix('.route.json')
    if out.exists() or receipt_path.exists():raise ValueError('Fresh corrected route required')
    retirement=None
    if retire_reviewed_bar_branches:
        if not bridge_topology_connectors:raise ValueError('Reviewed active channel required before branch retirement')
        evidence=json.loads(ALIGNMENT_EVIDENCE.read_text())
        image_receipt=Path(__file__).resolve().parents[2]/evidence['source_scene']['local_capture_receipt']
        retirement=dict(policy='retire_reviewed_bar_branches_outside_inferred_active_corridor_v1',
            evidence=dict(path=str(ALIGNMENT_EVIDENCE.resolve()),sha256=sha(ALIGNMENT_EVIDENCE)),
            image_capture=dict(path=str(image_receipt.resolve()),sha256=sha(image_receipt)),
            measured_banks=False,
            qualification='Only the two pre-reviewed exposed-bar rectangles; retain the inferred active-channel corridor, preserve original source polygons elsewhere. No native wet field is used as a reference.')
        retirement_evidence(retirement,sha(parent))
    parent_data=json.loads(parent.read_text())
    paths=ACTIVE_OBJECT_PATHS if bridge_topology_connectors else REVIEWED_OBJECT_PATHS
    connectors=ACTIVE_CONNECTORS if bridge_topology_connectors else {}
    result,changes=stitch(route_points(parent_data),json.loads(network.read_text()),paths,connectors)
    data=dict(type='FeatureCollection',features=[dict(type='Feature',properties=dict(
        river_id='chilko_river_bc',source='FWA network branches selected against 2023-10-20 Sentinel imagery',
        geometry_authority='Official FWA branch vertices and explicitly listed inferred channel joins; not surveyed banks or rapid boundaries',
        license='Open Government Licence - British Columbia'),
        geometry=dict(type='LineString',coordinates=result.tolist()))])
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,indent=2)+'\n')
    receipt=dict(schema=SCHEMA,parent_route=dict(path=str(parent),sha256=sha(parent)),
        network=dict(path=str(network),sha256=sha(network)),route_sha256=sha(out),
        replacements=[{k:v for k,v in row.items() if k!='points'} for row in changes],
        connectors=connectors,
        selection_image='S2B_10UDC_20231020_0_L2A',
        selection_basis='Reviewed original and all-branch overlays in tmp/chilko-sentinel-source-v1 and tmp/chilko-all-branch-network-source-v1.png',
        route_length_m=LineString(projected(result)).length,
        parent_route_length_m=LineString(projected(route_points(parent_data))).length,
        linear_branch_half_width_m=20.,measured_banks=False,
        width_policy='20 m half-width on replacement segments, including explicitly inferred joins, supplements original mapped river polygons; inferred construction extent, not observed bank positions',
        qualification='Selection fixes two known local route errors only; no global imagery audit, named rapid identity or hydraulic acceptance',
        engine_validated=False)
    if retirement is not None:receipt['planform_retirement']=retirement
    receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
    lineage(out)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('parent','network','out'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--bridge-topology-connectors',action='store_true',help='Use reviewed inferred channel joins instead of transverse network topology links')
    p.add_argument('--retire-reviewed-bar-branches',action='store_true',help='Retire obsolete mapped footprints only inside the two existing dated image-review areas; retain explicit inferred channel width')
    args=p.parse_args();print(json.dumps(build(args.parent,args.network,args.out,args.bridge_topology_connectors,args.retire_reviewed_bar_branches),indent=2))
