"""Load hash-verified original single-body or complete corridor FWA geometry."""
import hashlib
import json
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import shape, LineString, box
from shapely.ops import transform
import shapely

from capture_chilko_fwa_polygon import validate_polygon
from capture_chilko_fwa_corridor import validate_collection, SCHEMA, WATERSHED, MAIN_WATERBODY
from correct_chilko_route import compatible_capture_route, lineage, projected, retirement_evidence


def retire_bar_footprints(polygon,active_corridor,evidence):
    """Local inferred current extent; preserve historical mapping outside review.

    Removing an obsolete water footprint restores original ground to the bed
    builder. It never raises that ground or clips a native water solution.
    """
    if not polygon.is_valid or not active_corridor.is_valid:
        raise ValueError('Valid source and active corridor required')
    converter=Transformer.from_crs(evidence['observation_crs'],3157,always_xy=True).transform
    areas=shapely.union_all([transform(converter,box(*row['inspection_bounds_m']))
                             for row in evidence['observations']])
    retired=areas.difference(active_corridor)
    result=polygon.difference(retired)
    if (not result.is_valid or result.is_empty or
            not result.difference(polygon).is_empty or
            not polygon.difference(result).difference(areas).is_empty):
        raise ValueError('Retirement must preserve all source mapping outside reviewed areas')
    return result


def load_planform(path, route=None):
    path=Path(path);raw=path.read_bytes();m=json.loads(path.with_suffix('.json').read_text())
    if m.get('horizontal_crs')!='EPSG:4326' or m.get('sha256')!=hashlib.sha256(raw).hexdigest():
        raise ValueError('Unverified source planform frame or bytes')
    data=json.loads(raw)
    if m.get('schema')=='raftsim.chilko_fwa_polygon_capture.v1':
        validate_polygon(data,m['waterbody_key']);polygon=shape(data['features'][0]['geometry'])
    elif m.get('schema')==SCHEMA:
        if (m.get('watershed_key')!=WATERSHED or m.get('main_waterbody_key')!=MAIN_WATERBODY or
                m.get('selected_count')!=len(data.get('features',[])) or
                sorted(m.get('object_ids',[]))!=sorted(f['properties']['OBJECTID'] for f in data['features'])):
            raise ValueError('Unverified corridor river identities')
        expected_route=Path(route) if route is not None else Path(m['route'])
        if not compatible_capture_route(expected_route,m.get('route_sha256')):
            raise ValueError('Planform collection is for a different route')
        polygon=validate_collection(data,m['waterbody_keys'])
    else:raise ValueError('Unreviewed planform capture schema')
    if not polygon.is_valid:raise ValueError('Invalid source polygon; never silently repair')
    polygon=transform(Transformer.from_crs(4326,3157,always_xy=True).transform,polygon)
    if route is not None and Path(route).with_suffix('.route.json').exists():
        # Source FWA polygons are unchanged. Single-line active branches need an
        # explicitly INFERRED construction footprint; never call this surveyed
        # water extent or silently promote flooded cells into the reference.
        receipt,changes=lineage(route)
        footprints=[LineString(projected(row['points'])).buffer(receipt['linear_branch_half_width_m'])
                    for row in changes]
        polygon=shapely.union_all([polygon,*footprints])
        if 'planform_retirement' in receipt:
            evidence=retirement_evidence(receipt['planform_retirement'],receipt['parent_route']['sha256'])
            polygon=retire_bar_footprints(polygon,shapely.union_all(footprints),evidence)
        if not polygon.is_valid:raise ValueError('Invalid derived branch planform')
    return polygon


def route_planform_policy(route):
    path=Path(route).with_suffix('.route.json')
    if not path.exists():return dict(kind='original_FWA_polygons')
    receipt,_=lineage(route)
    policy=dict(kind='original_FWA_plus_reviewed_linear_branch_width_inference',
        route_lineage_manifest=str(path.resolve()),route_lineage_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        linear_branch_half_width_m=receipt['linear_branch_half_width_m'],measured_banks=False)
    if 'planform_retirement' in receipt:
        policy['kind']='original_FWA_with_image_reviewed_bar_retirement_and_inferred_channel'
        policy['planform_retirement']=receipt['planform_retirement']
    return policy
