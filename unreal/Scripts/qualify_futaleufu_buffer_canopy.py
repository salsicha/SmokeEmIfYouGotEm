"""Preserve valid canopy transforms; exclude buffer conflicts in a new candidate.

Does not alter the saved engine map or claim native collision/FPS validation.
"""
import argparse
import copy
import json
from pathlib import Path

import numpy as np
import shapely

from build_futaleufu_continuous_water_domain import ROOT, LandscapeTriangles, sha
from futaleufu_corridor_bed import FutaleufuBed


def eligible(clearance, radius, ground_change):
    clearance,radius,ground_change = np.broadcast_arrays(clearance,radius,ground_change)
    return (np.isfinite(clearance)&np.isfinite(radius)&np.isfinite(ground_change)
            &(radius>0)&(clearance>=np.maximum(12.,radius+8.))&(abs(ground_change)<=1e-7))


def run(sources, network, profile, terrain, canopy, output):
    sources,network,profile,terrain,canopy,output = [Path(p).resolve() for p in
        (sources,network,profile,terrain,canopy,output)]
    output.relative_to(ROOT)
    if output.exists(): raise ValueError('Fresh canopy candidate output required')
    parent = json.loads(canopy.read_text())
    t = LandscapeTriangles(terrain)
    if (parent.get('schema')!='raftsim.futaleufu_continuous_canopy.v1'
            or parent['terrain_manifest_sha256']!=t.manifest['hydraulic_buffer_terrain']['parent_manifest_sha256']
            or parent['horizontal_origin_m']!=t.manifest['horizontal_origin_m']
            or parent['vertical_datum_m']!=150. or parent['world_y_sign']!=-1):
        raise ValueError('Matching native canopy/terrain lineage and frame required')
    bed = FutaleufuBed(sources,profile,network,depth_m=1.8)
    for k,v in bed.receipt.items():
        if k=='sources_sha256':
            if any(t.manifest['evidence_source'][k].get(p)!=h for p,h in v.items()):
                raise ValueError('Canopy and terrain bind different bed sources')
        elif t.manifest['evidence_source'].get(k)!=v:
            raise ValueError('Canopy and terrain use different bed construction')
    pins = {Path(p).resolve():h for p,h in parent['sources_sha256'].items()}
    pins.update({ROOT/p:h for p,h in bed.receipt['sources_sha256'].items()})
    pins.update({p:sha(p) for p in (canopy,terrain/'manifest.json',Path(__file__).resolve())})
    def verify():
        for p,h in pins.items():
            if sha(p)!=h: raise ValueError('Changed canopy dependency: '+str(p))
    verify()
    rows = [r for c in parent['chunks'] for r in c['instances']]
    if len(rows)!=parent['instance_count']: raise ValueError('Parent canopy count mismatch')
    xy = np.array([r['location_cm'][:2] for r in rows])/[100.,-100.]+parent['horizontal_origin_m']
    radii = np.array([r['crown_bound_radius_m'] for r in rows])
    clearance = shapely.distance(shapely.points(xy),bed.bed_polygon)
    # Existing stored ground is the exact parent triangle sample, not the mesh
    # origin (which includes the mesh's bottom-bound offset).
    ground = t.sample(xy)
    old_ground = np.array([r['ground_cm'] for r in rows])/100.+150.
    keep = eligible(clearance,radii,ground-old_ground)
    if not keep.any(): raise ValueError('No unchanged valid canopy remains')
    result = copy.deepcopy(parent); counts=[0]*len(parent['meshes']); index=0; exclusions=[]
    chunks=[]
    for c in parent['chunks']:
        retained=[]
        for r in c['instances']:
            if keep[index]:
                row=copy.deepcopy(r);row['source_water_clearance_m']=float(clearance[index])
                retained.append(row);counts[row['mesh']]+=1
            else:
                exclusions.append(dict(parent_flat_index=index,chunk=c['chunk'],
                    clearance_m=float(clearance[index]),required_m=float(max(12.,radii[index]+8)),
                    ground_change_m=float(ground[index]-old_ground[index]) if np.isfinite(ground[index]) else None))
            index+=1
        if retained: chunks.append(dict(chunk=c['chunk'],instances=retained))
    result.update(chunks=chunks,instance_count=sum(counts),instances_per_mesh=counts,
        terrain_manifest_sha256=t.manifest_sha256,sources_sha256={str(p):h for p,h in pins.items()},
        source_water_minimum_clearance_m=float(clearance[keep].min()),
        minimum_crown_bound_clearance_m=float((clearance-radii)[keep].min()),
        native_grounding_verified=False,rendered_validated=False,packaged_performance_validated=False,
        hydraulic_buffer_update=dict(parent_placement_sha256=sha(canopy),excluded_instances=exclusions,
            retained_transforms_exact=True,retained_ground_change_max_m=float(abs(ground[keep]-old_ground[keep]).max()),
            native_map_modified=False,exclusion_scope='This candidate only; original placements and native map retained'))
    verify();t.verify_unchanged()
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')
    print(json.dumps(dict(parent_instances=len(rows),retained=sum(counts),excluded=len(exclusions),
        minimum_water_clearance_m=result['source_water_minimum_clearance_m'],
        minimum_crown_clearance_m=result['minimum_crown_bound_clearance_m'],
        maximum_retained_ground_change_m=result['hydraulic_buffer_update']['retained_ground_change_max_m'])),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('sources','network','profile','terrain','canopy','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();run(a.sources,a.network,a.profile,a.terrain,a.canopy,a.out)
