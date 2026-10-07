"""Verify original/conditioned terrain identity and sample the entire FWA route.

This is terrain provenance and continuity evidence, not hydraulic, named-rapid,
boat-motion, or packaged-game acceptance.
"""
import argparse
import json
from pathlib import Path
import numpy as np

from chilko_corridor_terrain import CorridorTerrain
from mosaic_lidarbc_crops import sha
from plan_lidarbc_corridor_capture import route_xy


def check_tile(original, derived):
    """Validate actual arrays, not just the output's native-preservation flag."""
    h, k = original['height_m'], original['source_kind']
    out, kinds = derived['height_m'], derived['source_kind']
    if h.shape != out.shape or k.shape != kinds.shape or h.dtype != out.dtype or k.dtype != kinds.dtype:
        raise ValueError('Source and derived terrain layouts differ')
    altered = kinds == 3
    if not np.isin(k,[0,1,2]).all() or not np.isin(kinds,[0,1,2,3]).all() or np.any(altered & (k!=2)):
        raise ValueError('Only coarse fallback may acquire inferred transition provenance')
    if not np.array_equal(k[~altered], kinds[~altered]) or not np.array_equal(h[~altered],out[~altered],equal_nan=True):
        raise ValueError('Terrain outside inferred transition changed')
    for key, values in original.items():
        if key not in ('height_m','source_kind') and (key not in derived or not np.array_equal(values,derived[key],equal_nan=True)):
            raise ValueError('Captured terrain provenance changed')
    if altered.any():
        delta = derived.get('seam_correction_m')
        if (delta is None or delta.shape!=h.shape or not np.isfinite(delta).all() or
                np.any(delta[~altered]) or not np.array_equal((h+delta)[altered],out[altered])):
            raise ValueError('Recorded correction disagrees with derived terrain')
    return int((k==1).sum()), int(altered.sum())


def audit(source, conditioned, route, out):
    if out.exists(): raise ValueError('Fresh audit output required')
    a,b=CorridorTerrain(source),CorridorTerrain(conditioned)
    am,bm=a.manifest,b.manifest
    if (a.conditioned or not b.conditioned or set(a.entries)!=set(b.entries) or
            bm['source_terrain']['sha256']!=sha(a.folder/'manifest.json') or
            am['route_sha256']!=sha(route) or bm['route_sha256']!=am['route_sha256']):
        raise ValueError('Unrelated terrain candidates or changed FWA route')
    native, inferred = 0,0
    for key in a.entries:
        pa,ra=a.entries[key];pb,rb=b.entries[key]
        if sha(pa)!=ra['sha256'] or sha(pb)!=rb['sha256'] or rb['source_sha256']!=ra['sha256']:
            raise ValueError('Terrain hash mismatch')
        with np.load(pa,allow_pickle=False) as za,np.load(pb,allow_pickle=False) as zb:
            n,i=check_tile({k:za[k] for k in za.files},{k:zb[k] for k in zb.files})
        native+=n;inferred+=i
        if i!=rb['conditioned_pixels']:raise ValueError('Inferred pixel count mismatch')
    xy=route_xy(route);s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(xy,axis=0),axis=1))]
    station=np.r_[np.arange(0,s[-1],1.),s[-1]]
    points=np.c_[np.interp(station,s,xy[:,0]),np.interp(station,s,xy[:,1])]
    original,original_kind=a.sample(points);height,kind=b.sample(points)
    if not np.isfinite(original).all() or not np.isfinite(height).all():
        raise ValueError('Missing route terrain support')
    if not np.array_equal(original[original_kind==1],height[original_kind==1]):
        raise ValueError('Native route interpolation changed')
    transitions=np.flatnonzero(original_kind[1:]!=original_kind[:-1])
    joins=[]
    for i in transitions:
        near=(station>=station[i]-25)&(station<=station[i]+25)
        joins.append(dict(station_m=float(station[i]),original_kind=[int(original_kind[i]),int(original_kind[i+1])],
            raw_delta_m=float(original[i+1]-original[i]),conditioned_delta_m=float(height[i+1]-height[i]),
            nearby_raw_max_step_m=float(np.max(np.abs(np.diff(original[near])))),
            nearby_conditioned_max_step_m=float(np.max(np.abs(np.diff(height[near]))))))
    out.mkdir(parents=True)
    np.savez_compressed(out/'route_samples.npz',station_m=station,xy_m=points,
        original_height_m=original,conditioned_height_m=height,original_kind=original_kind,conditioned_kind=kind)
    result=dict(schema='raftsim.chilko_corridor_terrain_audit.v1',
        source_manifest_sha256=sha(a.folder/'manifest.json'),conditioned_manifest_sha256=sha(b.folder/'manifest.json'),
        route_sha256=sha(route),route_length_m=float(s[-1]),route_samples=len(station),
        native_pixels_verified_unchanged=native,inferred_transition_pixels=inferred,
        missing_route_samples=0,original_source_transitions=joins,
        route_samples_sha256=sha(out/'route_samples.npz'),terrain_provenance_passed=True,
        hydraulic_validation=False,engine_validation=False,named_rapid_boundaries_verified=False)
    (out/'audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','conditioned','route','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(audit(a.source,a.conditioned,a.route,a.out),indent=2))
