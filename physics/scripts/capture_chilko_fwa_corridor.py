"""Capture all same-watershed FWA river polygons along the full Chilko route.

These mapped branches are not acquisition-day shoreline, surveyed bathymetry
or named rapid boundaries. Preserve full geometries and stable source IDs.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import shapely
from pyproj import Transformer
from shapely.geometry import shape, LineString
from shapely.ops import transform

from capture_chilko_fwa_polygon import LAYER, CATALOGUE, validate_polygon
from fetch_colorado_catalog_sources import read, validate_json
from plan_lidarbc_corridor_capture import route_xy

WATERSHED = 356364103
MAIN_WATERBODY = 328961612
SCHEMA = 'raftsim.chilko_fwa_corridor_capture.v1'


def validate_collection(data, expected_keys, watershed=WATERSHED):
    if data.get('type')!='FeatureCollection' or data.get('exceededTransferLimit'):
        raise ValueError('Incomplete FWA river polygon collection')
    keys=[];objects=[];polygons=[]
    for feature in data.get('features',[]):
        p=feature.get('properties',{});key=p.get('WATERBODY_KEY');oid=p.get('OBJECTID')
        if (not isinstance(key,int) or not isinstance(oid,int) or
                p.get('WATERSHED_KEY')!=watershed or p.get('FEATURE_CODE')!='GA24850000'):
            raise ValueError('Unexpected Chilko watershed or river feature identity')
        validate_polygon(dict(type='FeatureCollection',features=[feature]),key)
        polygon=shape(feature['geometry'])
        if not polygon.is_valid or polygon.is_empty:raise ValueError('Invalid original FWA geometry')
        keys.append(key);objects.append(oid);polygons.append(polygon)
    if (not keys or len(set(keys))!=len(keys) or len(set(objects))!=len(objects) or
            sorted(keys)!=sorted(expected_keys) or MAIN_WATERBODY not in keys):
        raise ValueError('Incomplete, duplicate or unrelated FWA river identities')
    merged=shapely.union_all(polygons)
    if not merged.is_valid:raise ValueError('Invalid combined source planform')
    return merged


def capture(route,out,buffer_m=1000.):
    if out.suffix!='.geojson' or out.exists() or out.with_suffix('.json').exists():
        raise ValueError('Fresh corridor GeoJSON and receipt required')
    if not 100<=buffer_m<=1000:raise ValueError('Bounded corridor buffer required')
    route_digest=hashlib.sha256(route.read_bytes()).hexdigest()
    line=LineString(route_xy(route));bounds=line.buffer(buffer_m).bounds
    base=dict(where=f'WATERSHED_KEY={WATERSHED}',geometry=','.join(map(str,bounds)),
        geometryType='esriGeometryEnvelope',inSR=3157,spatialRel='esriSpatialRelIntersects')
    ids_url=LAYER+'/query?'+urlencode(dict(base,f='json',returnIdsOnly='true'))
    ids_raw=read(ids_url);ids=validate_json(ids_raw).get('objectIds')
    if not isinstance(ids,list) or not ids or len(ids)>10000 or len(set(ids))!=len(ids):
        raise ValueError('Missing or unbounded object ID catalogue')
    features=[];requests=[]
    for start in range(0,len(ids),100):
        subset=sorted(ids)[start:start+100]
        url=LAYER+'/query?'+urlencode(dict(f='geojson',objectIds=','.join(map(str,subset)),
            outSR=4326,outFields='*',returnGeometry='true'))
        raw=read(url);data=validate_json(raw)
        if (data.get('type')!='FeatureCollection' or data.get('exceededTransferLimit') or
                sorted(f.get('properties',{}).get('OBJECTID',-1) for f in data.get('features',[]))!=subset):
            raise ValueError('Incomplete FWA object page')
        features.extend(data['features']);requests.append(dict(url=url,sha256=hashlib.sha256(raw).hexdigest(),object_ids=subset))
    data=dict(type='FeatureCollection',features=features)
    keys=[f['properties']['WATERBODY_KEY'] for f in features]
    validate_collection(data,keys)
    # Envelope query is conservative. Retain only exact corridor intersections,
    # but retain each original full polygon without clipping or simplification.
    project=Transformer.from_crs(4326,3157,always_xy=True).transform
    corridor=line.buffer(buffer_m)
    selected=[f for f in features if transform(project,shape(f['geometry'])).intersects(corridor)]
    data['features']=sorted(selected,key=lambda f:f['properties']['OBJECTID'])
    keys=sorted(f['properties']['WATERBODY_KEY'] for f in selected)
    validate_collection(data,keys)
    raw=(json.dumps(data,allow_nan=False)+'\n').encode()
    receipt=dict(schema=SCHEMA,acquired_utc=datetime.now(timezone.utc).isoformat(),
        source_layer=LAYER,catalogue_url=CATALOGUE,ids_query=ids_url,
        ids_response_sha256=hashlib.sha256(ids_raw).hexdigest(),requests=requests,
        horizontal_crs='EPSG:4326',selection_crs='EPSG:3157',buffer_m=buffer_m,
        selection_policy='All same-watershed river polygons intersecting exact full source-route buffer; full original geometries retained',
        route=str(route.resolve()),route_sha256=route_digest,
        watershed_key=WATERSHED,main_waterbody_key=MAIN_WATERBODY,waterbody_keys=keys,
        object_ids=sorted(f['properties']['OBJECTID'] for f in selected),
        queried_count=len(ids),selected_count=len(selected),sha256=hashlib.sha256(raw).hexdigest(),
        licence_url='https://www2.gov.bc.ca/gov/content/data/open-data/open-government-licence-bc',
        attribution='Contains information licensed under the Open Government Licence - British Columbia',
        qualification='Mapped river area, including separate branch polygons; not flight-day shoreline, measured depth, named rapid bounds or solved flow',
        engine_validated=False)
    if hashlib.sha256(route.read_bytes()).hexdigest()!=route_digest:
        raise ValueError('Source route changed during FWA capture')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw)
    out.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--route',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();r=capture(a.route,a.out)
    print(json.dumps({k:v for k,v in r.items() if k not in ('requests','waterbody_keys','object_ids')},indent=2))
