"""Read-only buffer coverage, production-bed and existing-canopy impact audit."""
import argparse
import json
from pathlib import Path

import numpy as np
import shapely

from build_futaleufu_continuous_water_domain import ROOT, PREFIX, LandscapeTriangles, sha
from futaleufu_corridor_bed import FutaleufuBed, NAMES
from build_futaleufu_buffer_profile import SAMPLES, SECTIONS


def cross_sections(line, arrays, stations, padding=5.):
    for station in stations:
        c = np.asarray(line.interpolate(station).coords)[0]
        d = np.asarray(line.interpolate(min(station+1,line.length)).coords)[0]-np.asarray(line.interpolate(max(station-1,0)).coords)[0]
        n = np.array([-d[1],d[0]])/np.linalg.norm(d)
        lo,hi = [np.interp(station,arrays['station_m'],arrays[k]) for k in ('left_m','right_m')]
        yield c+np.linspace(lo-padding,hi+padding,int(np.ceil(hi-lo+2*padding))+1)[:,None]*n


def run(sources, network, profile, terrain, canopy, output):
    sources,network,profile,terrain,canopy,output = [Path(p).resolve() for p in
        (sources,network,profile,terrain,canopy,output)]
    output.relative_to(ROOT)
    if output.exists(): raise ValueError('Fresh audit output required')
    parent_profile = PREFIX/'hydrology/channel_profile_2026_10_v2'
    parent_network = PREFIX/'hydrography/confluence_network_2026_10_v1/network.json'
    m = json.loads((profile/'manifest.json').read_text())
    pins = {p:sha(p) for p in (profile/'manifest.json',profile/'profile.npz',network,
        parent_profile/'manifest.json',parent_profile/'profile.npz',parent_network,canopy,Path(__file__).resolve())}
    new = FutaleufuBed(sources,profile,network,depth_m=1.8)
    old = FutaleufuBed(sources,parent_profile,parent_network,depth_m=1.8)
    t = LandscapeTriangles(terrain)
    pins[terrain/'manifest.json'] = t.manifest_sha256
    if (t.manifest.get('river_id')!='futaleufu_river_chile'
            or m['hydraulic_buffers']['parent_profile_sha256']!=sha(parent_profile/'profile.npz')):
        raise ValueError('Reviewed terrain and retained parent profile required')
    with np.load(parent_profile/'profile.npz',allow_pickle=False) as z: previous = dict(z)
    with np.load(profile/'profile.npz',allow_pickle=False) as z: current = dict(z)
    branches = {}
    for j,(name,line) in enumerate(zip(NAMES,new.lines)):
        r = m['hydraulic_buffers']['branches'][name]
        a,b = r['preserved_interior_sample_slice']; offset = r['interior_station_offset_m']
        for key in SAMPLES:
            old_values = previous[name+'_'+key]
            expected = old_values+offset if key=='station_m' else old_values
            if not np.array_equal(current[name+'_'+key][a:b],expected):
                raise ValueError('Interior profile altered: '+name+' '+key)
        for key in SECTIONS:
            old_values = previous[name+'_'+key]; size = len(old_values)
            actual = current[name+'_'+key][-size:] if j<2 else current[name+'_'+key][:size]
            expected = old_values+offset if key=='section_station_m' else old_values
            if not np.array_equal(actual,expected): raise ValueError('Interior section evidence altered')
        length = r['length_m']; start = 0. if j<2 else line.length-length
        stations = np.arange(start+1,start+length,2.)
        sections = list(cross_sections(line,new.arrays[name],stations))
        q = np.concatenate(sections); z = t.sample(q); values = new.sample(q)
        if not np.isfinite(z).all(): raise ValueError('Buffer banks leave encoded terrain')
        wet = values['bed_owned']&(values['height_m']<values['reference_m']-.05)
        owned = values['bed_owned']; position = 0; dry_sections = []
        for station,section in zip(stations,sections):
            if not wet[position:position+len(section)].any(): dry_sections.append(float(station))
            position += len(section)
        # A transect with some wet samples is not face connectivity or boat
        # clearance. Retain unresolved bank samples instead of erasing them.
        branch = dict(profile_values_preserved=True,section_evidence_preserved=True,
            width_coverage_queries=len(q),encoded_terrain_missing=0,transects=len(sections),
            completely_dry_constructed_transects=dry_sections,owned_queries=int(owned.sum()),
            cut_limit_queries=int(values['cut_limit_reached'].sum()),
            unresolved_above_stage_queries=int(values['unresolved_above_stage'].sum()),
            existing_encoded_wet_queries=int((owned&(z<values['reference_m']-.05)).sum()),
            inferred_constructed_wet_queries=int(wet.sum()),
            maximum_inferred_cut_m=float(np.max(values['source_height_m']-values['height_m'])),
            terrain_chunks=np.unique(np.floor((q-t.origin)/t.span).astype(int),axis=0).tolist())
        # Check the entire retained arm, including its exact old endpoint.
        old_line = old.lines[j]
        retained_s = np.unique(np.r_[0.,np.arange(20.,old_line.length,20.),old_line.length])
        retained_q = np.concatenate(list(cross_sections(old_line,old.arrays[name],retained_s,padding=0.)))
        before,after = old.sample(retained_q),new.sample(retained_q)
        delta = after['height_m']-before['height_m']; changed = abs(delta)>1e-7
        projected = shapely.line_locate_point(old_line,shapely.points(retained_q[changed]))
        branch.update(retained_bed_queries=len(retained_q),retained_bed_changed_queries=int(changed.sum()),
            retained_bed_max_change_m=float(np.max(abs(delta))),
            retained_bed_change_station_interval_m=[float(projected.min()),float(projected.max())] if len(projected) else None)
        branches[name] = branch
        print(name+': '+json.dumps({k:v for k,v in branch.items() if k!='terrain_chunks'}),flush=True)
    placement = json.loads(canopy.read_text())
    if placement['terrain_manifest_sha256']!=t.manifest_sha256: raise ValueError('Canopy belongs to different terrain')
    instances = [v for c in placement['chunks'] for v in c['instances']]
    if len(instances)!=placement['instance_count']: raise ValueError('Canopy count mismatch')
    locations = np.array([r['location_cm'][:2] for r in instances])
    xy = locations/[100.,-100.]+placement['horizontal_origin_m']
    clearance = shapely.distance(shapely.points(xy),new.bed_polygon)
    required = np.maximum(12.,np.array([r['crown_bound_radius_m'] for r in instances])+8.)
    conflicts = np.flatnonzero(clearance<required)
    vegetation = dict(instances_checked=len(instances),new_clearance_conflicts=len(conflicts),
        minimum_new_water_clearance_m=float(clearance.min()),
        conflicts=[dict(flat_instance_index=int(i),easting_northing_m=xy[i].tolist(),
            clearance_m=float(clearance[i]),required_m=float(required[i])) for i in conflicts],
        instances_modified=False,engine_map_modified=False)
    print('canopy: '+json.dumps({k:v for k,v in vegetation.items() if k!='conflicts'}),flush=True)
    for bed in (old,new):
        for rel,h in bed.receipt['sources_sha256'].items():
            p=ROOT/rel
            if sha(p)!=h: raise ValueError('Bed source changed during audit')
            pins[p]=h
    t.verify_unchanged()
    if any(sha(p)!=h for p,h in pins.items()): raise ValueError('Audit input changed')
    result = dict(schema='raftsim.futaleufu_hydraulic_buffer_support.v1',
        sources_sha256={p.relative_to(ROOT).as_posix():h for p,h in pins.items()},branches=branches,
        canopy=vegetation,terrain_modified=False,engine_map_modified=False,
        measured_bed=False,hydraulic_flow_validated=False,packaged_performance_validated=False,
        limitations=['Transect coverage is not connected water-cell validation.',
            'Inferred bed has shoreline taper; remaining above-stage samples are reported, not forced wet.',
            'Removing old endpoint caps can change bed at original gameplay endpoints. Quantified separately from exact retained stage/width profiles.',
            'Existing canopy conflicts require exclusion or re-placement before native installation.'])
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('sources','network','profile','terrain','canopy','out'): p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();run(a.sources,a.network,a.profile,a.terrain,a.canopy,a.out)
