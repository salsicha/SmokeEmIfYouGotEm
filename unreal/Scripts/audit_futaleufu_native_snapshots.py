"""Audit immutable short/long native runs, including interrupted checkpoints.

An interrupted producer can leave a useful snapshot but cannot earn terminal,
settled-flow, map or restart authorization. No missing states are synthesized.
The historical short-run auditor remains untouched while another job pins it.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np

import audit_futaleufu_native_continuation as checks
from build_futaleufu_continuous_water_domain import ROOT, PREFIX, sha, FutaleufuBed, connected_tiles, observe_branches
from continue_futaleufu_native_flow import require_launch_headroom, resources, shared_native_work


def snapshot_schedule(request, manifest):
    steps=request.get('steps'); command=request.get('command')
    if type(steps) is not int or steps not in (3000,30000):
        raise ValueError('Reviewed native step count required')
    interval=steps//10
    if (not isinstance(command,list) or len(command)!=6 or
            command[3:5]!=[str(steps),str(interval)] or command[5]!='4'):
        raise ValueError('Declared schedule differs from native command')
    if ('snapshot_interval_steps' in request and
            (type(request['snapshot_interval_steps']) is not int or request['snapshot_interval_steps']!=interval)):
        raise ValueError('Declared snapshot interval differs from native command')
    initial=manifest.get('initial_time_seconds')
    if (not isinstance(initial,(int,float)) or isinstance(initial,bool) or not math.isfinite(initial) or initial<0 or
            request.get('source_time_seconds')!=initial or request.get('dt_seconds')!=.01 or
            manifest.get('dt_seconds')!=.01):
        raise ValueError('Exact native restart clock and timestep required')
    if 'target_time_seconds' in request:
        target=request['target_time_seconds']
        if (not isinstance(target,(int,float)) or isinstance(target,bool) or not math.isfinite(target) or
                abs(target-(initial+steps*.01))>1e-8):
            raise ValueError('Declared target clock differs from native schedule')
    return list(range(0,steps+1,interval))


def completed_prefix(native, expected, successful):
    actual=[]
    for folder in native.glob('frame_*'):
        if not (folder/'complete.json').is_file():continue
        suffix=folder.name.removeprefix('frame_')
        if len(suffix)!=6 or not suffix.isdigit():raise ValueError('Invalid completed frame name')
        actual.append(int(suffix))
    actual.sort()
    if not actual or actual!=expected[:len(actual)]:
        raise ValueError('Missing, unexpected or noncontiguous complete snapshots')
    if successful and actual!=expected:raise ValueError('Successful run is missing requested snapshots')
    return actual


def producer_outcome(run):
    completed,failure=run/'completed.json',run/'failure.json'
    if completed.is_file()==failure.is_file():
        raise ValueError('Exactly one terminal producer receipt required; never audit a live producer')
    path=completed if completed.is_file() else failure
    receipt=json.loads(path.read_text())
    if path==completed:
        if receipt.get('exit_code')!=0 or receipt.get('native_restart_fields_and_clock_exact') is not True:
            raise ValueError('Producer did not validate successful restart and completion')
        return 'completed',path
    if not isinstance(receipt.get('failure'),str) or not receipt['failure']:
        raise ValueError('Interrupted producer requires its preserved failure explanation')
    return 'interrupted',path


def audit(run, output):
    run,output=Path(run).resolve(),Path(output).resolve()
    run.relative_to(ROOT);output.relative_to(ROOT)
    if output.exists():raise ValueError('Fresh audit output required')
    outcome,terminal_path=producer_outcome(run)
    require_launch_headroom(resources(),shared_native_work())
    native=run/'native'
    source=Path((native/'input_manifest_path.txt').read_text().strip()).resolve()
    source.relative_to(ROOT)
    if sha(source)!=sha(native/'input_manifest.json'):raise ValueError('Native input manifest changed')
    manifest=json.loads(source.read_text());request=json.loads((run/'request.json').read_text())
    if manifest.get('schema')!='raftsim.cartesian_flow_cook.v1' or manifest['grid']['cell_m']!=1.:
        raise ValueError('Reviewed one-metre native domain required')
    expected=snapshot_schedule(request,manifest)
    steps=completed_prefix(native,expected,outcome=='completed')
    pins={ROOT/p:h for p,h in manifest['sources_sha256'].items()}
    for path in (source,run/'request.json',terminal_path,Path(__file__).resolve(),Path(checks.__file__).resolve()):
        pins[path]=sha(path)
    for row in manifest['inputs']:
        pins.update({source.parent/row['name']/f:h for f,h in row['files'].items()})
    def verify():
        if any(sha(p)!=h for p,h in pins.items()):raise ValueError('Audited source or snapshot changed')
        if producer_outcome(run)[0]!=outcome or completed_prefix(native,expected,outcome=='completed')!=steps:
            raise ValueError('Producer terminal state or completed snapshot set changed')
    verify()
    reference=FutaleufuBed(ROOT/'tmp/futaleufu-continuous-source-window-v2',
        PREFIX/'hydrology/channel_profile_2026_10_v2',
        PREFIX/'hydrography/confluence_network_2026_10_v1/network.json',depth_m=1.8)
    size=manifest['grid']['tile_cells'];keys=[tuple(k) for k in manifest['tile_indices']]
    shape=(len(keys)*size,size);frames=[];errors=[];initial=None
    for step in steps:
        require_launch_headroom(resources(),shared_native_work())
        folder=native/('frame_%06d'%step);receipt_path=folder/'complete.json'
        pins[receipt_path]=sha(receipt_path);receipt=json.loads(receipt_path.read_text())
        checks.validate_receipt(receipt,step,manifest['initial_time_seconds'],manifest['dt_seconds'])
        arrays={}
        for name in ('h','u','v'):
            path=folder/(name+'.npy');pins[path]=sha(path)
            arrays[name]=np.load(path,mmap_mode='r',allow_pickle=False)
        if any(a.shape!=shape or not np.isfinite(a).all() for a in arrays.values()):
            raise ValueError('Incomplete or nonfinite snapshot arrays')
        h,u,v=(arrays[k] for k in ('h','u','v'));speed=np.hypot(u,v)
        if h.min()<0 or h.max()>10 or speed.max()>20:raise ValueError('Native depth/speed gate failed')
        volume=float(h.sum())
        if abs(volume-receipt['volume_m3'])>1e-6:raise ValueError('Saved volume differs from native receipt')
        if initial is None:
            initial=arrays;initial_volume=volume;restart=manifest['restart']
            if (any(pins[folder/(k+'.npy')]!=restart['source_arrays_sha256'][k] for k in arrays) or
                    receipt['time_seconds']!=restart['source_time_seconds']):
                raise ValueError('Exact restart fields or clock changed')
        if abs((volume-initial_volume)-receipt['boundary_volume_m3']-receipt['conservation_residual_m3'])>1e-6:
            raise ValueError('Integrated volume and boundary flux disagree')
        labels,offset,_=connected_tiles({key:h[i*size:(i+1)*size]>.05 for i,key in enumerate(keys)})
        observations,common=observe_branches(reference,labels,offset,manifest['horizontal_origin_utm18s_m'],1.)
        closed=checks.closed_wet_faces(h,keys,size,manifest['boundary_probes'])
        balance=checks.boundary_balance(manifest['boundary_probes'],receipt['exterior_fluxes'],manifest['inlet_budget'])
        dry=[r for r in observations if not r['wet_components']]
        if not common or dry:errors.append(dict(step=step,reason='Original route disconnected'))
        if closed:errors.append(dict(step=step,reason='Unintended wet exterior banks'))
        wet=h>.05
        row=dict(step=step,time_seconds=receipt['time_seconds'],volume_m3=volume,
            maximum_depth_m=float(h.max()),maximum_speed_mps=float(speed.max()),wet_cells=int(wet.sum()),
            wet_speed_percentiles_mps=np.percentile(speed[wet],[10,50,90,99]).tolist() if wet.any() else [],
            common_original_route_components=common,original_cross_sections=len(observations),dry_cross_sections=dry,
            wet_closed_exterior_faces=closed,boundary_balance=balance,
            maximum_step_residual_m3=receipt['maximum_step_residual_m3'],
            cumulative_mass_residual_m3=receipt['conservation_residual_m3'],storage_change_from_restart_m3=volume-initial_volume,
            maximum_depth_change_from_restart_m=float(np.max(np.abs(h-initial['h']))),
            arrays_sha256={k:pins[folder/(k+'.npy')] for k in arrays})
        if frames:row['interval_storage_rate_m3s']=(volume-frames[-1]['volume_m3'])/(row['time_seconds']-frames[-1]['time_seconds'])
        frames.append(row)
        print('Audited immutable native snapshot %d at %.2f seconds'%(step,receipt['time_seconds']),flush=True)
    verify()
    report=dict(schema='raftsim.futaleufu_native_continuation_audit.v1',native_run=run.relative_to(ROOT).as_posix(),
        producer_outcome=outcome,terminal_run_audited=outcome=='completed',requested_steps=request['steps'],
        snapshot_interval_steps=expected[1],errors=errors,numerical_geographic_checks_passed=not errors,frames=frames,
        assumptions='400 m3/s total (30 Azul + 370 mainstem) is inferred construction, not local gauging',
        scope='Complete immutable native snapshots only; an interrupted checkpoint is not a completed run or authorization to resume',
        restart_authorized=False,settled_hydraulics=False,normal_map_integrated=False,packaged_fps_verified=False,
        sources_sha256={p.relative_to(ROOT).as_posix():h for p,h in pins.items()})
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2,allow_nan=False)
    print(json.dumps(dict(producer_outcome=outcome,frames=len(frames),final_time_seconds=frames[-1]['time_seconds'],errors=errors)),flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();result=audit(args.run,args.out)
    if result['errors']:raise SystemExit(1)
