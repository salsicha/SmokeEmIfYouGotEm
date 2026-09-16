"""Native query expectations from the actual exported candidate atlas."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
from south_fork_rock_union import sha

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'unreal/Scripts'))
from audit_carrier_source_epochs import exact_cells


def wet_flags(depth):
    """Retain BOTH contracts; native sample visibility is not solver dryness.

    FRaftSimLiveWaterWindow::Sample uses Depth > 1e-4 for bWet. The source
    solver/atlas uses 1e-6. Neither threshold nor physical depth is changed.
    """
    if not np.isfinite(depth) or depth<0:raise ValueError('Finite nonnegative depth required')
    return dict(solver_wet=bool(depth>1.e-6),native_sample_wet=bool(depth>1.e-4))


def prepare(export,probes_path,output):
    export=Path(export).resolve();probes_path=Path(probes_path).resolve();output=Path(output).resolve()
    if output.exists() or not output.is_relative_to(ROOT/'tmp'):raise ValueError('Fresh project tmp expectations required')
    probes=json.loads(probes_path.read_text());atlas_path=export/'atlas/manifest.json'
    atlas=json.loads(atlas_path.read_text());stream_path=export/'streaming_manifest.json';stream=json.loads(stream_path.read_text())
    if atlas['dry_tolerance']!=1.e-6:raise ValueError('Changed solver dry threshold')
    if atlas['terrain_union']['cap_sha256']!=probes['source_cap_sha256']:raise ValueError('Different source solid in atlas')
    if atlas['terrain_union'].get('terrain_revision')!=probes.get('terrain_revision'):
        raise ValueError('Different registered bed revision in atlas and collision probes')
    rows=[p for p in probes['combined'] if p['kind']=='union_hydraulic_cell']
    points=np.array([p['world_position_cm'][:2] for p in rows])*[.01,-.01]
    cells=exact_cells(points,[t['origin_m'] for t in atlas['tiles']],atlas['tile_shape'],atlas['grid_spacing_m'])
    if np.any(cells<0):raise ValueError('Union query is outside the actual modeled state')
    fields={};dependencies={}
    for name,meta in atlas['arrays'].items():
        path=(atlas_path.parent/meta['file']).resolve()
        if sha(path)!=meta['sha256']:raise ValueError('Changed atlas array: '+name)
        values=np.load(path,allow_pickle=False,mmap_mode='r')
        fields[name]=values[cells[:,0]*80+cells[:,1],cells[:,2]]
        dependencies[path.relative_to(ROOT).as_posix()]=meta['sha256']
    candidates=[];desired=(points.min(axis=0)+points.max(axis=0))*.5
    # Leave four real cells around every query, inside the unchanged 224 m crop.
    admissible_low=points.max(axis=0)-108;admissible_high=points.min(axis=0)+108
    for window in stream['windows']:
        for rect in window['valid_live_center_bounds_m']:
            low=np.maximum(rect[:2],admissible_low);high=np.minimum(rect[2:],admissible_high)
            if np.any(low>high):continue
            center=np.clip(desired,low,high)
            candidates.append((float(np.sum((center-desired)**2)),window['cooked_fields_manifest'],center))
    if not candidates:raise ValueError('No validated full runtime window contains all collision cells')
    _,manifest,center=min(candidates,key=lambda p:(p[0],p[1]))
    for i,row in enumerate(rows):
        if abs(fields['bed'][i]*100-row['world_position_cm'][2])>1.e-8:
            raise ValueError('Actual exported runtime bed differs from collision source')
        row['expected_runtime']=dict(bed_m=float(fields['bed'][i]),depth_m=float(fields['h'][i]),
            surface_m=float(fields['bed'][i]+fields['h'][i]),u_mps=float(fields['u'][i]),
            world_v_mps=-float(fields['v'][i]),**wet_flags(fields['h'][i]))
    coordinates=ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/hydraulic_regions_context/coordinate_map.json'
    result=dict(source_probe_sha256=sha(probes_path),atlas_manifest=atlas_path.relative_to(ROOT).as_posix(),
        atlas_sha256=sha(atlas_path),streaming_manifest_sha256=sha(stream_path),
        fields_manifest=manifest,fields_manifest_sha256=sha(ROOT/manifest),window_center_m=center.tolist(),
        coordinate_map=coordinates.relative_to(ROOT).as_posix(),coordinate_map_sha256=sha(coordinates),
        array_dependencies=dependencies,source_time_seconds=atlas['source_time_seconds'],queries=rows,
        solver_dry_threshold_m=1.e-6,native_sample_wet_threshold_m=1.e-4,
        hydraulic_settling_accepted=False,playable_integrated=False)
    output.write_text(json.dumps(result,indent=2)+'\n')
    return {k:v for k,v in result.items() if k not in ('queries','array_dependencies')}|dict(query_count=len(rows))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('export',type=Path)
    p.add_argument('--probes',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(prepare(a.export,a.probes,a.output),indent=2),flush=True)
