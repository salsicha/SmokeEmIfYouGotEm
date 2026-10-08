"""Native-pixel full-route water evidence, without a fabricated flow or bed.

Use the existing Terminator optical thresholds on each captured date. Retain
nodata, isolated patches and route gaps. Neither spectral water classification
nor a DSM median is a surveyed bank or a measured water stage.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import shapely
from scipy.ndimage import label, distance_transform_edt

from build_futaleufu_corridor_sources import sha, ROOT, ROUTE

BANDS=('blue','green','red','nir')


def classify(raw):
    values=[np.asarray(raw[k]) for k in BANDS]
    if any(a.ndim!=2 or a.shape!=values[0].shape or a.dtype!=np.dtype('uint16') for a in values):
        raise ValueError('Aligned native uint16 optical bands required')
    valid=np.logical_and.reduce([a!=0 for a in values])
    if raw['valid'].dtype.kind!='b' or not np.array_equal(raw['valid'],valid):
        raise ValueError('Recorded validity differs from original nodata')
    b,g,r,n=[a.astype(np.float32)*.0001-.1 for a in values]
    bright=valid&(b>.22)&(g>.22)&(r>.18)&(abs(b-r)<.12)
    wet=valid&(((g-n)/np.maximum(g+n,1e-3)>.05)|bright)
    return valid,wet,bright


def consensus(valid,wet,bright):
    valid,wet,bright=map(np.asarray,(valid,wet,bright))
    if (valid.ndim!=3 or valid.shape[0]!=3 or wet.shape!=valid.shape or bright.shape!=valid.shape or
            any(a.dtype.kind!='b' for a in (valid,wet,bright)) or np.any(wet&~valid) or np.any(bright&~wet)):
        raise ValueError('Three aligned dates of valid water/bright observations required')
    counts=valid.sum(axis=0).astype('u1');wc=wet.sum(axis=0).astype('u1');bc=bright.sum(axis=0).astype('u1')
    # An unavailable date never counts as dry, and one date cannot establish
    # repeated evidence. Preserve the denominator as well as the vote count.
    repeated=(counts>=2)&(wc>=2)
    return counts,wc,bc,repeated


def route_components(repeated,distance,*,half_width_m=150.,seed_distance_m=10.):
    repeated,distance=np.asarray(repeated),np.asarray(distance)
    if (repeated.ndim!=2 or repeated.dtype.kind!='b' or distance.shape!=repeated.shape or
            not np.isfinite(distance).all() or np.any(distance<0) or
            not 0<seed_distance_m<=half_width_m):
        raise ValueError('Native mask and finite route distances required')
    candidates=repeated&(distance<=half_width_m)
    groups,count=label(candidates,structure=np.ones((3,3),dtype=np.uint8))
    near=np.unique(groups[candidates&(distance<=seed_distance_m)])
    near=near[near!=0]
    return candidates&np.isin(groups,near),groups,int(count)


def build(folder,out):
    folder,out=Path(folder).resolve(),Path(out).resolve()
    if out.exists():raise ValueError('Fresh full-route water reference required')
    manifest_path=folder/'manifest.json';m=json.loads(manifest_path.read_text())
    if m.get('schema')!='raftsim.futaleufu_continuous_sources.v1' or m['grid']['epsg']!=32718:
        raise ValueError('Verified Futaleufu native source window required')
    pins={manifest_path:sha(manifest_path)}
    for relative,digest in m['sources_sha256'].items():
        p=(ROOT/relative).resolve();p.relative_to(ROOT)
        if sha(p)!=digest:raise ValueError('Changed original source')
        pins[p]=digest
    if ROUTE.resolve() not in pins:
        raise ValueError('Source window must bind the complete route chart')
    chart=json.loads(ROUTE.read_text());points=np.array(chart['points'])
    route_info=ROUTE.parent/'manifest.json';pins[route_info]=sha(route_info)
    info=json.loads(route_info.read_text())
    source_stations=np.asarray(info['source_to_projected_stations_m'])
    indices=np.searchsorted(points[:,0],source_stations)
    if np.any(indices>=len(points)) or not np.array_equal(points[indices,0],source_stations):
        raise ValueError('Full chart must retain every captured route vertex')
    xy=points[indices,1:3]+chart['horizontal_origin_m']
    line=shapely.LineString(xy)
    if abs(line.length-m['route_length_m'])>.01:raise ValueError('Source window and full route disagree')
    confluence=info['confluence']['route_station_m']
    shape=tuple(m['grid']['shape']);t=m['grid']['transform']
    if t[0]!=10 or t[4]!=-10 or t[1]!=0 or t[3]!=0:raise ValueError('Native north-up ten-metre grid required')
    rows,cols=np.indices(shape);east=t[2]+(cols+.5)*10;north=t[5]-(rows+.5)*10
    geometry=shapely.points(east,north)
    distance=shapely.distance(geometry,line);station=shapely.line_locate_point(line,geometry)
    dates=[];valid=[];wet=[];bright=[]
    for item in m['optical']:
        p=(folder/item['file']).resolve();p.relative_to(folder)
        if sha(p)!=item['sha256']:raise ValueError('Changed cropped optical data')
        pins[p]=item['sha256']
        with np.load(p,allow_pickle=False) as z:v,w,b=classify(dict(z))
        if v.shape!=shape:raise ValueError('Optical shape differs from native grid')
        valid.append(v);wet.append(w);bright.append(b);dates.append(item['datetime'])
    counts,wc,bc,repeated=consensus(valid,wet,bright)
    associated,groups,ngroups=route_components(repeated,distance)
    p=folder/m['dsm']['file']
    if sha(p)!=m['dsm']['sha256']:raise ValueError('Changed DSM')
    pins[p]=m['dsm']['sha256']
    with np.load(p,allow_pickle=False) as z:dsm=z['dsm_m']
    if dsm.shape!=shape or not np.isfinite(dsm).all():raise ValueError('Finite aligned DSM required')
    # Keep raw medians and missing bins: no interpolation, monotonic fit,
    # guessed discharge, bank widening or channel cut in this evidence layer.
    edges=np.unique(np.r_[np.arange(0,line.length,50.),confluence,line.length])
    interior=associated&(distance_transform_edt(associated)*10>=20)
    bins=np.searchsorted(edges,station,side='right')-1
    profile=[]
    for i,(a,b) in enumerate(zip(edges[:-1],edges[1:])):
        own=(bins==i)&(station>0)&(station<line.length)
        water=own&associated;inside=water&interior
        values=dsm[inside]
        profile.append(dict(start_m=float(a),end_m=float(b),branch='rio_azul' if b<=confluence else 'futaleufu_mainstem',
            associated_water_pixels=int(water.sum()),interior_dsm_pixels=int(inside.sum()),
            repeated_bright_pixels=int((water&(bc>=2)).sum()),
            raw_dsm_interior_median_m=float(np.median(values)) if len(values)>=2 else None))
    if not all(sha(p)==h for p,h in pins.items()):raise ValueError('Source changed while classifying')
    out.mkdir(parents=True)
    np.savez_compressed(out/'water_reference.npz',valid_dates=counts,water_dates=wc,bright_dates=bc,
        repeated_water=repeated,route_associated_water=associated,component=groups,
        source_route_station_m=station,source_route_distance_m=distance)
    report=dict(schema='raftsim.futaleufu_corridor_water_reference.v1',grid=m['grid'],
        sources_sha256={str(p.relative_to(ROOT)):h for p,h in pins.items()},
        artifact_sha256=sha(out/'water_reference.npz'),dates=dates,confluence_station_m=confluence,
        route_length_m=float(line.length),connected_candidate_components=ngroups,
        associated_components=int(len(np.unique(groups[associated]))),
        associated_water_pixels=int(associated.sum()),native_unknown_observations=int((3-counts).sum()),
        profile=profile,empty_water_bins=sum(r['associated_water_pixels']==0 for r in profile),
        absent_dsm_median_bins=sum(r['raw_dsm_interior_median_m'] is None for r in profile),
        thresholds=dict(ndwi_gt=.05,bright_blue_gt=.22,bright_green_gt=.22,bright_red_gt=.18,
                        bright_blue_red_difference_lt=.12,water_support_dates_at_least=2,
                        route_half_width_m=150,component_seed_distance_m=10),
        authority='Spectral classification and raw DSM context only, not surveyed banks, stage, bathymetry, or named-rapid geometry.',
        attribution=dict(optical=m['optical_attribution'],optical_license=m['optical_license'],
            route='OpenStreetMap contributors, ODbL-1.0',
            dsm_license_url=m['dsm']['license_url'],
            dsm_distribution_requires_article_6_notices=True),
        limitations=['Same established Terminator optical thresholds; native ten-metre cells unchanged.',
            'Eight-connected components associated within ten metres of captured route; disconnected gaps retained.',
            'Bright pixels are appearance evidence, not proof of whitewater or a rapid boundary.',
            'Optical dates are not cloud screened here; unknown local flows remain unknown.',
            'DSM includes canopy and edited water; missing interior medians are not filled.'],
        discharge_assigned=False,terrain_modified=False,installed_in_engine=False,full_river_complete=False)
    (out/'manifest.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sources',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();r=build(a.sources,a.out)
    print(json.dumps({k:r[k] for k in ('route_length_m','associated_water_pixels','associated_components',
        'empty_water_bins','absent_dsm_median_bins','native_unknown_observations')}))
