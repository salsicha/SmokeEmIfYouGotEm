"""Captured endpoint buffers outside the unchanged Futaleufu gameplay route.

Extends only at original OSM vertices. No tangent extrapolation, fabricated
bank width, stage, bathymetry or flow. A separate profile/bed construction is
required before these buffers can become native hydraulic boundary faces.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np

from build_futaleufu_continuous_water_domain import ROOT, PREFIX, LandscapeTriangles, sha
from build_futaleufu_continuous_route import vertices
from geo_frames import tm_forward, utm

RIVER = ROOT/'physics/data/real_world/futaleufu_river_chile'


def verify_captured_text(raw, expected):
    # The historical manifest hashed LF, while the retained LFS object has
    # CRLF. Only that exact byte substitution is allowed; geometry, whitespace
    # other than CRLF, and every source value remain covered by the old hash.
    raw.decode('utf-8')
    actual=hashlib.sha256(raw).hexdigest()
    lf=hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()
    if expected not in (actual,lf):
        raise ValueError('Captured route text differs beyond CRLF line endings')
    return dict(raw_sha256=actual,historical_sha256=expected,lf_sha256=lf,
        only_crlf_normalization_needed=actual!=expected,source_file_modified=False)


def extend_interval(points, start, end, minimum, *, before=False, after=False):
    points = vertices(points)
    if (isinstance(start,bool) or isinstance(end,bool) or not isinstance(start,(int,np.integer))
            or not isinstance(end,(int,np.integer)) or not 0<=start<end<len(points)
            or isinstance(minimum,bool) or not np.isfinite(minimum) or minimum<=0):
        raise ValueError('Ordered source interval and positive finite buffer required')
    station = np.r_[0.,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
    first, last = start, end
    if before:
        while first>0 and station[start]-station[first]<minimum:
            first-=1
        if station[start]-station[first]<minimum:
            raise ValueError('Insufficient captured upstream geometry')
    if after:
        while last<len(points)-1 and station[last]-station[end]<minimum:
            last+=1
        if station[last]-station[end]<minimum:
            raise ValueError('Insufficient captured downstream geometry')
    return first,last,points[first:last+1].copy(),dict(
        upstream_added_m=float(station[start]-station[first]),
        downstream_added_m=float(station[last]-station[end]),
        retained_vertex_interval_in_buffer=[start-first,end-first])


def exact_interval(points, retained):
    points, retained = vertices(points), vertices(retained)
    starts = np.flatnonzero(np.all(points==retained[0],axis=1))
    matches = [int(i) for i in starts if i+len(retained)<=len(points)
               and np.array_equal(points[i:i+len(retained)],retained)]
    if len(matches)!=1:
        raise ValueError('Exactly one complete ordered captured subchain required')
    return matches[0],matches[0]+len(retained)-1


def build(network_path, source_folder, terrain_folder, output, minimum=300.):
    network_path, source_folder, terrain_folder, output = map(Path,
        (network_path,source_folder,terrain_folder,output))
    if output.exists():
        raise ValueError('Fresh hydraulic buffer output required')
    old = json.loads(network_path.read_text())
    source_path = source_folder/'manifest.json'
    source = json.loads(source_path.read_text())
    corridor_path = PREFIX/'manifest.json'
    corridor = json.loads(corridor_path.read_text())
    ways_path = RIVER/'hydrography/source/osm_futaleufu_river_ways.json'
    main_path = RIVER/'futaleufu_sources_2026_09/osm/futaleufu_centreline.json'
    expected = next(r['sha256'] for r in corridor['source_records'] if r['path']==ways_path.relative_to(ROOT).as_posix())
    text_receipt=verify_captured_text(ways_path.read_bytes(),expected)
    if old.get('schema')!='raftsim.futaleufu_confluence_network.v1':
        raise ValueError('Captured three-arm network required')
    if old['sources_sha256'].get(source_path.resolve().relative_to(ROOT).as_posix())!=sha(source_path):
        raise ValueError('Buffer source window differs from the original network')
    pins = {ROOT/p:h for p,h in old['sources_sha256'].items()}
    pins.update({p.resolve():sha(p) for p in (network_path,source_path,corridor_path,ways_path,main_path,Path(__file__),
        ROOT/'physics/scripts/geo_frames.py',ROOT/'physics/scripts/build_futaleufu_continuous_route.py')})
    def verify():
        for path,digest in pins.items():
            path.resolve().relative_to(ROOT)
            if sha(path)!=digest:
                raise ValueError('Changed captured buffer input: '+str(path))
    verify()
    ways=json.loads(ways_path.read_text(encoding='utf-8'))
    azul=[e for e in ways['elements'] if e.get('type')=='way' and e['id']==213541728]
    if len(azul)!=1:
        raise ValueError('Unambiguous retained Azul source way required')
    project=lambda ll:np.column_stack(tm_forward(ll[:,0],ll[:,1],utm(18,south=True)))
    azul_xy=project(np.array([[p['lon'],p['lat']] for p in azul[0]['geometry']]))
    main=json.loads(main_path.read_text(encoding='utf-8'))
    main_xy=project(np.asarray(main['centreline_lon_lat_chain'])[:,:2])
    terrain=LandscapeTriangles(terrain_folder)
    if (terrain.manifest.get('river_id')!='futaleufu_river_chile'
            or source['grid']['epsg']!=32718 or source['grid']['transform'][:2]!=[10.,0.]):
        raise ValueError('Reviewed Futaleufu source frame required')
    t=source['grid']['transform'];rows,cols=source['grid']['shape']
    lower=np.array([t[2]+5,t[5]-(rows-.5)*10]);upper=np.array([t[2]+(cols-.5)*10,t[5]-5])
    result=copy.deepcopy(old);result['branches']={};buffers={}
    for name,branch in old['branches'].items():
        original=np.asarray(branch['points_station_easting_northing_m'])[:,1:]
        whole=azul_xy if name=='rio_azul' else main_xy
        start,end=exact_interval(whole,original)
        first,last,xy,info=extend_interval(whole,start,end,minimum,
            before=name!='downstream_mainstem',after=name=='downstream_mainstem')
        a,b=info['retained_vertex_interval_in_buffer']
        if not np.array_equal(xy[a:b+1],original):
            raise ValueError('Buffer changed retained branch geometry')
        margin=float(np.min(np.c_[xy-lower,upper-xy]))
        if margin<20.:
            raise ValueError('Captured buffer lacks 20 m source-pixel context: '+name)
        station=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(xy,axis=0),axis=1))]
        if not np.array_equal(xy[-1 if name!='downstream_mainstem' else 0],old['junction']['easting_northing_m']):
            raise ValueError('Buffer moved the captured junction')
        dense=np.unique(np.r_[np.arange(0,station[-1],2.),station])
        query=np.c_[np.interp(dense,station,xy[:,0]),np.interp(dense,station,xy[:,1])]
        present=np.isfinite(terrain.sample(query))
        indices=np.floor((query[~present]-terrain.origin)/terrain.span).astype(int)
        info.update(source_vertex_interval=[first,last],original_source_vertex_interval=[start,end],
            source_pixel_context_m=margin,centreline_terrain_queries=len(query),
            centreline_terrain_missing=int((~present).sum()),
            missing_centreline_terrain_chunks=np.unique(indices,axis=0).tolist(),
            retained_geometry_exact=True)
        buffers[name]=info
        result['branches'][name]=dict(direction=branch['direction'],
            points_station_easting_northing_m=np.c_[station,xy].tolist(),
            length_m=float(station[-1]),source_vertex_count=len(xy),
            source_window_margin_m=margin)
    result['sources_sha256']={p.resolve().relative_to(ROOT).as_posix():h for p,h in pins.items()}
    result['upstream_mainstem_source_vertex_interval']=buffers['upstream_mainstem']['source_vertex_interval']
    result['downstream_mainstem_source_vertex_interval']=buffers['downstream_mainstem']['source_vertex_interval']
    result['junction']['hydraulic_rio_azul_station_m']=result['branches']['rio_azul']['length_m']
    result['hydraulic_buffers']=dict(minimum_requested_m=minimum,branches=buffers,
        azul_source_text_verification=text_receipt,
        parent_network_sha256=sha(network_path),terrain_manifest_sha256=terrain.manifest_sha256,
        gameplay_route_modified=False,profile_extended=False,terrain_extended=False,
        boundary_faces_authored=False,scope='Captured geometry only; native source-bound buffer profiles and bed remain to construct')
    result['limitations'].append('Endpoint buffers retain original source vertices; centreline terrain coverage is not proof of full-width bank support.')
    verify();terrain.verify_unchanged()
    output.mkdir(parents=True)
    (output/'network.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result['hydraulic_buffers'],indent=2),flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('network','sources','terrain','out'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--minimum-buffer-m',type=float,default=300.)
    a=parser.parse_args();build(a.network,a.sources,a.terrain,a.out,a.minimum_buffer_m)
