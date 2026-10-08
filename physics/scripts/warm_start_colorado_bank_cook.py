"""Fresh bank-edit candidate seeded from reviewed flow; NOT exact continuation.

Only bounded raised-bank geometry is eligible. Keep the previous wet surface,
recompute depth against the new bed, and retain velocity where water remains.
No water is added, no field is called solved, and fresh native review is required.
"""
import argparse
import copy
import json
from pathlib import Path
import shutil

import numpy as np

from build_colorado_catalog_evidence import ROOT, sha
from continue_colorado_catalog_cook import restart_state
from review_colorado_catalog_cook import load_frame


def bank_state(frame, old_bed, new_bed, grid):
    original=restart_state(frame,old_bed,grid)
    new_bed=np.asarray(new_bed,dtype=float)
    if new_bed.shape!=old_bed.shape or not np.isfinite(new_bed).all():
        raise ValueError('Aligned finite new bed required')
    delta=new_bed-old_bed
    if np.any(delta < -1e-8) or np.any(delta > 1.01):
        raise ValueError('Only bounded positive bank edits may warm start')
    changed=delta!=0
    if not changed.any():raise ValueError('Use exact continuation for unchanged geometry')
    if np.any(delta[changed]<0):raise ValueError('Bank candidate may not lower terrain')
    state={k:v.copy() for k,v in original.items()}
    h=np.maximum(frame['eta'][changed]-new_bed[changed],0.)
    # A dry original cell stays dry; this is not a source of new water.
    h=np.minimum(h,frame['h'][changed])
    wet=h>1e-6
    state['depth'][changed]=h
    state['eta'][changed]=new_bed[changed]+h
    for k in ('u','v'):state[k][changed]=np.where(wet,frame[k][changed],0.)
    state['hu'][changed]=h*state['u'][changed]
    state['hv'][changed]=h*state['v'][changed]
    state['wet'][changed]=wet
    return state,dict(changed_bed_cells=int(changed.sum()),maximum_raise_m=float(delta.max()),
        newly_dry_cells=int(((frame['h']>1e-6)&~state['wet']).sum()),
        removed_water_volume_m3=float((frame['h']-state['depth']).sum()*grid['dx']*grid['dy']),
        unchanged_cells_preserved_exactly=True)


def checked_inputs(folder):
    report=json.loads((folder/'build_report.json').read_text())
    for name,digest in report['files_sha256'].items():
        path=(folder/name).resolve();path.relative_to(folder)
        if sha(path)!=digest:raise ValueError('Changed candidate input')
    return report,json.loads((folder/'scenario/scenario.json').read_text())


def verify_source_bank_edit(old,new):
    left,right=old.get('source_inputs',[]),new.get('source_inputs',[])
    if not left or len(left)!=len(right):raise ValueError('Matching registered source cores required')
    receipts=[]
    for a,b in zip(left,right):
        reports=[];grids=[]
        for row in (a,b):
            path=ROOT/row['path']/'build_report.json'
            if sha(path)!=row['sha256']:raise ValueError('Changed source core')
            report=json.loads(path.read_text());reports.append(report)
            folder=ROOT/report['construction_directory'];m=json.loads((folder/'manifest.json').read_text())
            if sha(folder/'evidence_grid.npz')!=m['evidence_grid_sha256']:
                raise ValueError('Changed source construction grid')
            with np.load(folder/'evidence_grid.npz',allow_pickle=False) as z:grids.append(dict(z))
            receipts.append(dict(manifest=str(folder/'manifest.json'),sha256=sha(folder/'manifest.json')))
        if reports[0]['source_profile']!=reports[1]['source_profile']:
            raise ValueError('Different source registration')
        a,b=grids
        if a.keys()!=b.keys():raise ValueError('Different source fields')
        for key in a:
            if key not in ('bed_ellipsoid_m','inferred_shore_stabilization_mask','class_code'):
                np.testing.assert_array_equal(a[key],b[key])
        delta=b['bed_ellipsoid_m']-a['bed_ellipsoid_m'];changed=delta!=0
        allowed=b['inferred_shore_stabilization_mask']&~b['classified_water_mask']
        if np.any(changed&~allowed) or np.any(delta<0) or np.any(delta>1.01):
            raise ValueError('Unbounded or non-bank source edit')
        np.testing.assert_array_equal(a['bed_ellipsoid_m'][a['measured_pool_bed_mask']],
                                      b['bed_ellipsoid_m'][a['measured_pool_bed_mask']])
    return receipts


def prepare(candidate,previous,cook,review,out):
    candidate,previous,cook,review,out=[Path(p).resolve() for p in (candidate,previous,cook,review,out)]
    if out.exists():raise ValueError('Fresh bank-edit warm-start directory required')
    new,sc=checked_inputs(candidate);old,old_sc=checked_inputs(previous)
    if sc['grid']!=old_sc['grid'] or sc['roughness']!=old_sc['roughness']:
        raise ValueError('Warm start must keep grid and resistance')
    if (candidate/'coordinate_map.json').read_bytes()!=(previous/'coordinate_map.json').read_bytes():
        raise ValueError('Different geographic coordinate mapping')
    with np.load(candidate/'reference.npz') as a,np.load(previous/'reference.npz') as b:
        if set(a.files)!=set(b.files):raise ValueError('Different reference fields')
        for key in a.files:np.testing.assert_array_equal(a[key],b[key])
    if [b['kind'] for b in sc['boundaries']]!=[b['kind'] for b in old_sc['boundaries']]:
        raise ValueError('Different boundary policy')
    if sc['boundaries'][0]['metadata']['target_discharge_m3s']!=old_sc['boundaries'][0]['metadata']['target_discharge_m3s']:
        raise ValueError('Different target discharge')
    receipt=json.loads(review.read_text());native=json.loads((cook/'manifest.json').read_text())
    validation=json.loads((cook/'validation.json').read_text())
    if receipt['native_manifest']!=native or receipt['name']!=old['name']:
        raise ValueError('Unrelated reviewed native source')
    for key in ('discharge_abs_p95_below_5percent','settling_depth_p95_below_3cm'):
        if receipt['construction_screen'].get(key) is not True:raise ValueError('Unsettled source flow')
    if (native['solver_mode']!='finite_volume' or native['boundary_mode']!='scenario' or
            native['scenario_id']!=old_sc['metadata']['scenario_id'] or
            not validation['passed'] or not validation['finite_state'] or validation['velocity_limit_reached'] or
            native['feature_strength_scale']!=0 or native['preserve_initial_mass'] or
            not native['disable_fixture_calibrations']):raise ValueError('Unsupported native source')
    frame_name=receipt['comparison_frames'][-1]
    if Path(frame_name).name!=frame_name or sha(cook/'frames'/frame_name)!=receipt['frame_sha256'][frame_name]:
        raise ValueError('Changed reviewed frame')
    source_receipts=verify_source_bank_edit(old,new)
    old_bed=np.load(previous/'scenario/bed.npy');bed=np.load(candidate/'scenario/bed.npy')
    frame=load_frame(cook/'frames'/frame_name,old_bed.shape);grid=sc['grid']
    x=grid['origin_x']+np.arange(grid['nx'])*grid['dx']
    y=grid['origin_y']+np.arange(grid['ny'])*grid['dy']
    if not np.array_equal(frame['x'],np.broadcast_to(x,old_bed.shape)) or not np.array_equal(frame['y'],np.broadcast_to(y[:,None],old_bed.shape)):
        raise ValueError('Native source is on another grid')
    state,stats=bank_state(frame,old_bed,bed,grid)
    out.mkdir(parents=True)
    for name in new['files_sha256']:
        target=out/name;target.parent.mkdir(parents=True,exist_ok=True)
        if name.replace('\\','/')!='scenario/initial_state.npz':shutil.copyfile(candidate/name,target)
    np.savez_compressed(out/'scenario/initial_state.npz',**state)
    result=copy.deepcopy(new)
    result['bed_edit_warm_start']=dict(previous_inputs=str(previous),candidate_inputs=str(candidate),
        previous_report_sha256=sha(previous/'build_report.json'),candidate_report_sha256=sha(candidate/'build_report.json'),
        source_review=str(review),source_review_sha256=sha(review),source_frame=str(cook/'frames'/frame_name),
        source_frame_sha256=sha(cook/'frames'/frame_name),source_construction_receipts=source_receipts,
        policy='Raised-bank warm start; retain old wet surface, reduce depth and momentum on changed terrain; unchanged cells exact. Not an exact continuation or accepted field.',
        statistics=stats,requires_fresh_native_review=True)
    checked_inputs(candidate);checked_inputs(previous)
    result['files_sha256']={p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()}
    (out/'build_report.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(stats,indent=2));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('candidate','previous','cook','review','out'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();prepare(*(getattr(a,k) for k in ('candidate','previous','cook','review','out')))
