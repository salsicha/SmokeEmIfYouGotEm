"""Infer only captured hydraulic buffers; retain every interior profile value.

Uses the established native optical/DSM and mapped-bank policy. An old stage
endpoint is a hard join constraint, not a pseudo-observation. Never refits the
playable route, invents discharge, or claims the inferred DSM is bathymetry.
"""
import argparse
import copy
import json
from pathlib import Path

import numpy as np
import shapely
from scipy.ndimage import distance_transform_edt

from build_futaleufu_channel_profile import (
    ROOT, sha, classify, consensus, route_components, choose_stage,
    stage_anchors, fill_spans, load_planform, mapped_span)
from build_futaleufu_hydraulic_buffers import exact_interval

NAMES = ('rio_azul', 'upstream_mainstem', 'downstream_mainstem')
SAMPLES = ('station_m', 'stage_m', 'easting_m', 'northing_m', 'left_m',
           'right_m', 'bank_span_mapped')
SECTIONS = ('raw_section_stage_m', 'fitted_section_stage_m',
            'section_station_m', 'spectral_span_interpolated')


def splice_profile(old, extra, incoming):
    """Join once; the old arrays always own the shared endpoint."""
    if not isinstance(incoming, bool) or set(old) != set(SAMPLES+SECTIONS) or set(extra) != set(old):
        raise ValueError('Complete aligned profile arrays and direction required')
    for group in (old, extra):
        for keys in (SAMPLES, SECTIONS):
            length = len(group[keys[0]])
            if any(np.asarray(group[k]).ndim != 1 or len(group[k]) != length
                   or not np.isfinite(group[k]).all() for k in keys):
                raise ValueError('Finite aligned profile arrays required')
        s = group['station_m']
        if (len(s) < 2 or s[0] != 0 or np.any(np.diff(s) <= 0)
                or np.any(np.diff(group['stage_m']) > 1e-8)
                or np.any(group['right_m'] <= group['left_m'])):
            raise ValueError('Ordered complete monotone profile and positive spans required')
    oi, ei = (0, -1) if incoming else (-1, 0)
    for key in ('stage_m', 'easting_m', 'northing_m', 'left_m', 'right_m'):
        if old[key][oi] != extra[key][ei]:
            raise ValueError('Buffer endpoint does not exactly match existing profile: '+key)
    offset = float(extra['station_m'][-1] if incoming else old['station_m'][-1])
    result = {}
    for key in SAMPLES+SECTIONS:
        interior, buffer = old[key].copy(), extra[key].copy()
        if key in ('station_m', 'section_station_m'):
            if incoming: interior += offset
            else: buffer += offset
        if key in SAMPLES:
            result[key] = np.r_[buffer[:-1], interior] if incoming else np.r_[interior, buffer[1:]]
        else:
            result[key] = np.r_[buffer, interior] if incoming else np.r_[interior, buffer]
    a = len(extra['station_m'])-1 if incoming else 0
    b = a+len(old['station_m'])
    for key in SAMPLES:
        expected = old[key]+offset if key == 'station_m' and incoming else old[key]
        if not np.array_equal(result[key][a:b], expected):
            raise ValueError('Splice modified retained interior profile')
    return result, [a, b]


def build(sources, network_path, profile_folder, output):
    sources, network_path, profile_folder, output = [Path(p).resolve() for p in
        (sources, network_path, profile_folder, output)]
    output.relative_to(ROOT)
    if output.exists(): raise ValueError('Fresh buffer profile output required')
    source_path, parent_path = sources/'manifest.json', profile_folder/'manifest.json'
    source, network, parent = [json.loads(p.read_text(encoding='utf-8')) for p in
                              (source_path, network_path, parent_path)]
    if (source.get('schema') != 'raftsim.futaleufu_continuous_sources.v1'
            or network.get('schema') != 'raftsim.futaleufu_confluence_network.v1'
            or parent.get('schema') != 'raftsim.futaleufu_channel_profile.v1'
            or set(network['branches']) != set(NAMES)):
        raise ValueError('Reviewed Futaleufu sources, buffers and parent profile required')
    pins = {}
    for item in (source, network, parent):
        for rel, digest in item['sources_sha256'].items():
            path = (ROOT/rel).resolve(); path.relative_to(ROOT)
            if path in pins and pins[path] != digest: raise ValueError('Conflicting source pins')
            pins[path] = digest
    for path in (source_path, network_path, parent_path, Path(__file__).resolve()):
        pins[path] = sha(path)
    for name in ('build_futaleufu_channel_profile.py', 'build_futaleufu_corridor_water_reference.py',
                 'futaleufu_planform.py', 'build_pacuare_evidence_grid.py'):
        path = ROOT/'physics/scripts'/name; pins[path] = sha(path)
    data_path = profile_folder/'profile.npz'; pins[data_path] = parent['profile_sha256']
    old_network_paths = [p for p,h in pins.items()
                         if h == network['hydraulic_buffers']['parent_network_sha256']]
    if len(old_network_paths) != 1: raise ValueError('Unambiguous retained network required')
    old_network_path = old_network_paths[0]
    if parent['sources_sha256'].get(old_network_path.relative_to(ROOT).as_posix()) != sha(old_network_path):
        raise ValueError('Parent profile must bind original network')
    if any(item['sources_sha256'].get(source_path.relative_to(ROOT).as_posix()) != sha(source_path)
           for item in (network,parent)):
        raise ValueError('Profiles must share exactly the same native source window')
    def verify():
        for p,h in pins.items():
            if sha(p) != h: raise ValueError('Changed profile input: '+str(p))
    verify()
    old_network = json.loads(old_network_path.read_text())
    with np.load(data_path, allow_pickle=False) as z: old_arrays = {k:z[k].copy() for k in z.files}
    t = source['grid']['transform']; shape = tuple(source['grid']['shape'])
    if source['grid']['epsg'] != 32718 or t[:2] != [10.,0.] or t[3:5] != [0.,-10.]:
        raise ValueError('Native north-up 10 m UTM18S grid required')
    valid, wet, bright = [], [], []
    for item in source['optical']:
        path = (sources/item['file']).resolve(); path.relative_to(sources)
        pins[path] = item['sha256']
        if sha(path) != pins[path]: raise ValueError('Changed optical pixels')
        with np.load(path, allow_pickle=False) as z: v,w,b = classify(dict(z))
        if v.shape != shape: raise ValueError('Native optical shape mismatch')
        valid.append(v); wet.append(w); bright.append(b)
    _,_,_,repeated = consensus(valid,wet,bright)
    path = (sources/source['dsm']['file']).resolve(); path.relative_to(sources)
    pins[path] = source['dsm']['sha256']
    if sha(path) != pins[path]: raise ValueError('Changed DSM pixels')
    with np.load(path, allow_pickle=False) as z: dsm = z['dsm_m'].copy()
    if dsm.shape != shape or not np.isfinite(dsm).all(): raise ValueError('Finite aligned DSM required')
    plan_path = ROOT/parent['mapped_planform_source']
    if pins.get(plan_path) != sha(plan_path): raise ValueError('Unbound mapped bank source')
    planform = shapely.union_all([g for _,_,g in load_planform(plan_path)])
    lines = [shapely.LineString(np.asarray(network['branches'][n]['points_station_easting_northing_m'])[:,1:]) for n in NAMES]
    row,col = np.indices(shape); east,north = t[2]+(col+.5)*10,t[5]-(row+.5)*10
    points = shapely.points(east,north)
    distance = np.array([shapely.distance(points,line) for line in lines])
    owner = distance.argmin(axis=0)
    associated,_,_ = route_components(repeated,distance.min(axis=0))
    interior = associated & (distance_transform_edt(associated)*10 >= 20)
    arrays = {}; summaries = {}; buffer_receipts = {}
    for j,(name,line) in enumerate(zip(NAMES,lines)):
        incoming = j < 2
        old = {k:old_arrays[name+'_'+k] for k in SAMPLES+SECTIONS}
        retained = np.asarray(old_network['branches'][name]['points_station_easting_northing_m'])[:,1:]
        first,last = exact_interval(np.asarray(line.coords),retained)
        lengths = np.r_[0.,np.cumsum(np.linalg.norm(np.diff(np.asarray(line.coords),axis=0),axis=1))]
        if (incoming and last != len(line.coords)-1) or (not incoming and first != 0):
            raise ValueError('Only exterior branch extension is allowed')
        start,end = (0.,lengths[first]) if incoming else (lengths[last],line.length)
        length = float(end-start)
        if length < 300: raise ValueError('At least 300 m captured hydraulic buffer required')
        station = shapely.line_locate_point(line,points)
        foot = shapely.get_coordinates(shapely.line_interpolate_point(line,station).ravel()).reshape(*shape,2)
        before = shapely.line_interpolate_point(line,np.maximum(station-1,0))
        after = shapely.line_interpolate_point(line,np.minimum(station+1,line.length))
        dx,dy = shapely.get_x(after)-shapely.get_x(before),shapely.get_y(after)-shapely.get_y(before)
        lateral = ((east-foot[...,0])*(-dy)+(north-foot[...,1])*dx)/np.hypot(dx,dy)
        edges = np.r_[np.arange(0,length,50.),length]
        records = []; left = []; right = []
        for a,b in zip(edges[:-1],edges[1:]):
            own = (owner==j)&(station>=start+a)&(station<start+b)&(station>0)&(station<line.length)
            water = own&associated; inner = water&interior; near = own&(distance[j]<=20)
            value,weight,kind = choose_stage(dsm[inner],dsm[water],dsm[near])
            lo,hi = np.percentile(lateral[water],[5,95])+[-5,5] if water.sum()>=2 else (np.nan,np.nan)
            left.append(lo); right.append(hi)
            records.append(dict(start_m=float(a),end_m=float(b),kind=kind,raw_dsm_stage_m=value,
                weight=weight,interior_pixels=int(inner.sum()),water_pixels=int(water.sum()),
                near_route_pixels=int(near.sum()),raw_left_m=float(lo) if np.isfinite(lo) else None,
                raw_right_m=float(hi) if np.isfinite(hi) else None))
        join = -1 if not incoming else 0
        anchors = stage_anchors(records,length,float(old['stage_m'][join]),incoming)
        anchor_s = [r['station_m'] for r in anchors]; anchor_z = [r['inferred_stage_m'] for r in anchors]
        support_s = np.r_[0.,anchor_s,length]
        support_z = np.r_[anchor_z[0] if incoming else old['stage_m'][-1],anchor_z,
                          old['stage_m'][0] if incoming else anchor_z[-1]]
        s = np.unique(np.r_[np.arange(0,length,10.),length])
        center = shapely.get_coordinates(shapely.line_interpolate_point(line,start+s))
        before = shapely.get_coordinates(shapely.line_interpolate_point(line,np.maximum(start+s-1,0)))
        after = shapely.get_coordinates(shapely.line_interpolate_point(line,np.minimum(start+s+1,line.length)))
        tangent = after-before; normal = np.c_[-tangent[:,1],tangent[:,0]]/np.linalg.norm(tangent,axis=1)[:,None]
        middle = (edges[:-1]+edges[1:])/2
        if name != 'rio_azul':
            spans = [mapped_span(planform,c,n) for c,n in zip(center,normal)]
            if any(v is None for v in spans): raise ValueError('Buffer leaves captured mapped banks: '+name)
            lo,hi = np.asarray(spans).T; inferred = np.zeros(len(middle),bool)
        else:
            # The exact old endpoint is a join support, not a new observation.
            # Require native water support elsewhere; never invent a width.
            ss = np.r_[middle,length] if incoming else np.r_[0.,middle]
            ll = np.r_[left,old['left_m'][join]] if incoming else np.r_[old['left_m'][join],left]
            rr = np.r_[right,old['right_m'][join]] if incoming else np.r_[old['right_m'][join],right]
            filled_l,filled_r,flags = fill_spans(ss,ll,rr)
            lo,hi = np.interp(s,ss,filled_l),np.interp(s,ss,filled_r)
            inferred = flags[:-1] if incoming else flags[1:]
        z = np.interp(s,support_s,support_z)
        ei = -1 if incoming else 0
        join_bank_delta = [float(lo[ei]-old['left_m'][join]),float(hi[ei]-old['right_m'][join])]
        # Old endpoint owns the seam even if the newly available route tangent
        # changes the mapped perpendicular cross section right at that vertex.
        center[ei] = [old['easting_m'][join],old['northing_m'][join]]
        lo[ei],hi[ei],z[ei] = old['left_m'][join],old['right_m'][join],old['stage_m'][join]
        fitted = np.interp(middle,support_s,support_z)
        extra = dict(station_m=s,stage_m=z,easting_m=center[:,0],northing_m=center[:,1],
            left_m=lo,right_m=hi,bank_span_mapped=np.full(len(s),name!='rio_azul',bool),
            raw_section_stage_m=np.array([r['raw_dsm_stage_m'] for r in records]),
            fitted_section_stage_m=fitted,section_station_m=middle,spectral_span_interpolated=inferred)
        merged,interval = splice_profile(old,extra,incoming)
        if abs(merged['station_m'][-1]-line.length)>1e-6: raise ValueError('Full buffered length mismatch')
        arrays.update({name+'_'+k:v for k,v in merged.items()})
        for r,value,flag in zip(records,fitted,inferred):
            r.update(inferred_stage_m=float(value),stage_adjustment_m=float(value-r['raw_dsm_stage_m']),
                     spectral_span_interpolated=bool(flag))
        receipt = dict(length_m=length,sections=records,stage_anchors=anchors,
            preserved_interior_sample_slice=interval,retained_values_exact=True,
            interior_station_offset_m=length if incoming else 0.,
            bank_join_delta_before_preserving_original_m=join_bank_delta,
            maximum_stage_adjustment_m=float(np.max(abs(fitted-extra['raw_section_stage_m']))),
            stage_start_m=float(z[0]),stage_end_m=float(z[-1]),
            width_m_p10_p50_p90=np.percentile(hi-lo,[10,50,90]).tolist(),
            fallback_stage_sections=sum(r['kind']=='near_route_dsm_fallback' for r in records))
        buffer_receipts[name] = receipt
        summaries[name] = dict(length_m=float(line.length),samples=len(merged['station_m']),
            stage_start_m=float(merged['stage_m'][0]),stage_end_m=float(merged['stage_m'][-1]),
            parent_branch_manifest=parent_path.relative_to(ROOT).as_posix(),hydraulic_buffer=receipt)
        print(name+': '+json.dumps({k:v for k,v in receipt.items() if k not in ('sections','stage_anchors')}),flush=True)
    verify()
    report = copy.deepcopy(parent)
    report.update(sources_sha256={p.relative_to(ROOT).as_posix():h for p,h in pins.items()},
        branches=summaries,hydraulic_buffers=dict(parent_profile_sha256=parent['profile_sha256'],
        retained_interior_values_exact=True,branches=buffer_receipts))
    report['limitations'].append('Only hydraulic endpoint buffers were newly inferred. Interior stage/bank samples remain exact; station origins shift on incoming arms. No flow, new bed, or engine acceptance implied.')
    report['construction_policy']['buffer_join'] = 'Hard original endpoint stage and bank constraints; no interior refit. Original sections retained in pinned parent manifest.'
    output.mkdir(parents=True)
    np.savez_compressed(output/'profile.npz',**arrays)
    report['profile_sha256'] = sha(output/'profile.npz')
    (output/'manifest.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('sources','network','profile','out'): p.add_argument('--'+name,type=Path,required=True)
    a = p.parse_args(); build(a.sources,a.network,a.profile,a.out)
