"""Extend Pacuare search-location evidence using actual public bridge crossings.

No invented bridge midpoint, guide-distance extrapolation, rapid boundary,
IGN/SNIT data, proprietary waypoint export, or normal-map promotion.
"""
import argparse
import bisect
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from register_pacuare_catalog_locations import DATA, ROOT, ROUTE, EVIDENCE, controls, sha, validate_route

CAPTURE=DATA/'huacas_sources_2026_10/osm'
WAYS=(37612797,1269147862)
GUIDE='https://gorafting.com/costa-rica/pacuare-river/'


def bridge_points(path, identity):
    root=ET.parse(path).getroot()
    ways=root.findall('way')
    if len(ways)!=1 or ways[0].get('id')!=str(identity):
        raise ValueError('Exact captured OSM bridge identity required')
    way=ways[0];tags={t.get('k'):t.get('v') for t in way.findall('tag')}
    if tags.get('ref')!='32' or tags.get('bridge')!='yes' or tags.get('highway')!='trunk':
        raise ValueError('Captured feature is not the Highway 32 road bridge')
    nodes={n.get('id'):(float(n.get('lon')),float(n.get('lat'))) for n in root.findall('node')}
    if len(nodes)!=len(root.findall('node')):raise ValueError('Duplicate captured node')
    points=[nodes[n.get('ref')] for n in way.findall('nd')]
    if len(points)<2 or any(not math.isfinite(x) or abs(x)>(180 if i==0 else 90)
                            for p in points for i,x in enumerate(p)):
        raise ValueError('Finite complete bridge geometry required')
    return points,dict(osm_way_id=identity,osm_version=int(way.get('version')),
                       osm_timestamp=way.get('timestamp'),tags=tags)


def crossing(route, bridge):
    cross=lambda a,b:a[0]*b[1]-a[1]*b[0]
    hits=[]
    for index,(a,b) in enumerate(zip(route,route[1:])):
        d=(b[0]-a[0],b[1]-a[1])
        for c,e in zip(bridge,bridge[1:]):
            v=(e[0]-c[0],e[1]-c[1]);q=(c[0]-a[0],c[1]-a[1]);den=cross(d,v)
            if abs(den)<1e-15:continue
            t,u=cross(q,v)/den,cross(q,d)/den
            if 0<=t<=1 and 0<=u<=1:
                station=float(a[2]+t*(b[2]-a[2]))
                if not any(abs(h['source_chain_m']-station)<1e-6 for h in hits):
                    hits.append(dict(source_chain_m=station,route_segment_index=index,
                        lon_lat=[float(a[k]+t*d[k]) for k in (0,1)]))
    if len(hits)!=1:raise ValueError('One unambiguous bridge/river crossing required')
    return hits[0]


def search_point(km, lower, upper, route):
    if not (math.isfinite(km) and lower['guide_km']<=km<=upper['guide_km'] and
            lower['guide_km']<upper['guide_km'] and lower['source_chain_m']<upper['source_chain_m']):
        raise ValueError('Increasing bracketing controls required; no extrapolation')
    ratio=(km-lower['guide_km'])/(upper['guide_km']-lower['guide_km'])
    station=lower['source_chain_m']+ratio*(upper['source_chain_m']-lower['source_chain_m'])
    axis=[r[2] for r in route]
    if not axis[0]<=station<=axis[-1]:raise ValueError('Search point outside captured route')
    i=min(max(bisect.bisect_right(axis,station)-1,0),len(route)-2)
    t=(station-axis[i])/(axis[i+1]-axis[i])
    return dict(source_chain_m=station,lon_lat=[float(route[i][k]+t*(route[i+1][k]-route[i][k])) for k in (0,1)])


def build():
    paths=[ROUTE,EVIDENCE,Path(__file__).resolve(),ROOT/'physics/scripts/register_pacuare_catalog_locations.py']
    paths += [CAPTURE/f'highway32_way_{way}_2026_10_08.osm' for way in WAYS]
    pins={p:sha(p) for p in paths}
    data=json.loads(ROUTE.read_text());evidence=json.loads(EVIDENCE.read_text())
    route=validate_route(data);anchors=controls(data,evidence);lower=anchors[-1]
    if lower['osm_node_id']!=13805044421 or lower['guide_km']!=22.67:
        raise ValueError('Reviewed Dos Montanas lower control required')
    km=dict(evidence['guide_rapid_km'])['Las Ranitas']
    alternatives=[]
    for identity in WAYS:
        points,source=bridge_points(CAPTURE/f'highway32_way_{identity}_2026_10_08.osm',identity)
        upper=dict(guide_km=26.01,**source,**crossing(route,points))
        alternatives.append(dict(highway_control=upper,search_location=search_point(km,lower,upper,route)))
    if any(sha(p)!=h for p,h in pins.items()):raise ValueError('Bridge registration input changed')
    stations=[a['search_location']['source_chain_m'] for a in alternatives]
    return dict(schema='raftsim.pacuare.highway_bridge_search_registration.v1',review_date='2026-10-08',
        guide_url=GUIDE,guide_origin=evidence['guide_origin'],rapid='Las Ranitas',guide_km=km,
        lower_control=lower,alternatives=alternatives,
        search_station_span_m=[min(stations),max(stations)],
        span_qualification='Difference between two mapped bridge-span interpretations, NOT a confidence interval or rapid length. Guide-distance and source-route errors remain unquantified.',
        method='Each actual bridge/river segment intersection brackets the guide point with Dos Montanas; linear registration, no extrapolation or averaging.',
        source_chain_frame=data['chainage'],sources_sha256={p.relative_to(ROOT).as_posix():h for p,h in pins.items()},
        bridge_source_urls=[f'https://api.openstreetmap.org/api/0.6/way/{w}/full' for w in WAYS],
        rights='Bridge and route geometry: ODbL 1.0, (c) OpenStreetMap contributors, https://www.openstreetmap.org/copyright. Guide facts indexed by link only; no guide text, pixels or proprietary waypoint export redistributed.',
        rapid_boundary_coordinates=None,runtime_placement_authorized=False,production_promoted=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():parser.error('Fresh registration path required')
    result=build();args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2,allow_nan=False)
    print(json.dumps(dict(rapid=result['rapid'],search_station_span_m=result['search_station_span_m'],runtime_placement_authorized=False)))
