"""Resume an independently audited complete snapshot from an interrupted cook.

The original failed producer and restart_authorized=False audit remain intact.
Only interruption by an ownership/resource guard is recoverable here. This
never promotes hydraulic fields or changes physical inputs or acceptance gates.
"""
import argparse
import copy
import json
import math
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np

from qualify_futaleufu_native_ports import ROOT, sha, resources
from qualify_chilko_full_native import busy
from continue_futaleufu_native_flow import require_launch_headroom
from resume_futaleufu_native_checkpoint import exact_state, watchdog_failure
from audit_futaleufu_native_snapshots import snapshot_schedule, completed_prefix, producer_outcome

SOLVER_SHA='fb2624bb8cb210142ae17741c5358c86a48d6f42c60eedab64715def53c6e558'
INTERRUPTIONS={
    'Shared engine/build/cook appeared; stopped only owned checkpoint continuation',
    'Owned cook resource floor reached', 'Owned cook disk reserve reached',
    'Owned cook four-hour bound reached',
}


def recovery_checkpoint(audit, failure, request, manifest, complete_steps):
    if (audit.get('schema')!='raftsim.futaleufu_native_continuation_audit.v1' or
        audit.get('producer_outcome')!='interrupted' or audit.get('terminal_run_audited') is not False or
        audit.get('restart_authorized') is not False or audit.get('errors')!=[] or
        audit.get('numerical_geographic_checks_passed') is not True or
        failure.get('failure') not in INTERRUPTIONS or failure.get('exit_code')==0):
        raise ValueError('Independently audited guard interruption required')
    expected=snapshot_schedule(request,manifest)
    frames=audit.get('frames',[])
    if (not frames or not complete_steps or complete_steps!=expected[:len(complete_steps)] or
        [f.get('step') for f in frames]!=complete_steps):
        raise ValueError('Exact audited complete snapshot prefix required')
    for frame in frames:
        clock=frame.get('time_seconds')
        if (not isinstance(clock,(int,float)) or isinstance(clock,bool) or not math.isfinite(clock) or
            abs(clock-(manifest['initial_time_seconds']+frame['step']*.01))>1e-7 or
            not frame.get('common_original_route_components') or frame.get('dry_cross_sections')!=[] or
            frame.get('wet_closed_exterior_faces')!=[]):
            raise ValueError('Audited snapshot clock, connectivity or shoreline failed')
        hashes=frame.get('arrays_sha256',{})
        if (set(hashes)!= {'h','u','v'} or any(not isinstance(h,str) or len(h)!=64 or
            any(c not in '0123456789abcdef' for c in h) for h in hashes.values())):
            raise ValueError('Exact native array hashes required')
    return frames[-1]


def run(audit_path, solver, output):
    audit_path,solver,output=[Path(p).resolve() for p in (audit_path,solver,output)]
    for path in (audit_path,solver,output):path.relative_to(ROOT/'tmp')
    if output.exists():raise ValueError('Fresh recovery output required')
    if sha(solver)!=SOLVER_SHA:raise ValueError('Existing source-verified Cartesian solver required')
    require_launch_headroom(resources(),busy())
    audit=json.loads(audit_path.read_text())
    previous=(ROOT/audit['native_run']).resolve();previous.relative_to(ROOT/'tmp')
    native=previous/'native'
    outcome,terminal=producer_outcome(previous)
    if outcome!='interrupted' or (native/'completed.json').exists():
        raise ValueError('Preserved interrupted producer required')
    source=Path((native/'input_manifest_path.txt').read_text().strip()).resolve()
    source.relative_to(ROOT/'tmp')
    if sha(source)!=sha(native/'input_manifest.json'):raise ValueError('Native input manifest changed')
    manifest=json.loads(source.read_text());request=json.loads((previous/'request.json').read_text())
    if (manifest.get('schema')!='raftsim.cartesian_flow_cook.v1' or
        manifest.get('grid',{}).get('cell_m')!=1.):raise ValueError('Reviewed full one-metre domain required')
    steps=completed_prefix(native,snapshot_schedule(request,manifest),False)
    last=recovery_checkpoint(audit,json.loads(terminal.read_text()),request,manifest,steps)
    frame=native/('frame_%06d'%last['step'])
    receipt=json.loads((frame/'complete.json').read_text())
    if receipt['time_seconds']!=last['time_seconds']:raise ValueError('Audited snapshot clock changed')
    pins={}
    for name,digest in audit['sources_sha256'].items():
        path=(ROOT/name).resolve();path.relative_to(ROOT);pins[path]=digest
    # These must already belong to the independent audit, not acquire new hashes
    # here after being changed. A partial later snapshot is never selected.
    for path in (source,terminal,previous/'request.json',frame/'complete.json'):
        if path not in pins or sha(path)!=pins[path]:raise ValueError('Missing or changed audited receipt')
    for key,digest in last['arrays_sha256'].items():
        path=frame/(key+'.npy')
        if pins.get(path)!=digest:raise ValueError('Snapshot hash differs from audited source set')
    for path in (audit_path,solver,Path(__file__).resolve(),
                 ROOT/'unreal/Scripts/qualify_chilko_full_native.py',
                 ROOT/'unreal/Scripts/resume_futaleufu_native_checkpoint.py',
                 ROOT/'unreal/Scripts/continue_futaleufu_native_flow.py',
                 ROOT/'unreal/Scripts/audit_futaleufu_native_snapshots.py'):
        digest=sha(path)
        if path in pins and pins[path]!=digest:raise ValueError('Historical source changed')
        pins[path]=digest

    def verify():
        for path,digest in pins.items():
            if sha(path)!=digest:raise ValueError('Changed recovery input: '+str(path))
        if (producer_outcome(previous)[0]!='interrupted' or (native/'completed.json').exists() or
            completed_prefix(native,snapshot_schedule(request,manifest),False)!=steps):
            raise ValueError('Interrupted producer state changed')

    verify();require_launch_headroom(resources(),busy())
    size=manifest['grid']['tile_cells']
    state={k:np.load(frame/(k+'.npy'),mmap_mode='r',allow_pickle=False) for k in ('h','u','v')}
    exact_state(state['h'],state['u'],state['v'],(len(manifest['packages'])*size,size))
    output.mkdir(parents=True)
    def save(name,value):
        with (output/name).open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2,allow_nan=False)
    started=time.monotonic();child=None;stage='checkpoint_preparation';minimum=resources()
    try:
        packages=output/'packages';packages.mkdir()
        updated=copy.deepcopy(manifest);updated['inputs']=[]
        for i,name in enumerate(manifest['packages']):
            if i%64==0:require_launch_headroom(resources(),busy())
            before=(source.parent/name).resolve();before.relative_to(source.parent)
            after=(packages/name).resolve();after.relative_to(packages)
            after.mkdir()
            for filename in ('bed.npy','scenario.json','features.json','probes.json'):
                shutil.copyfile(before/filename,after/filename)
                if sha(before/filename)!=sha(after/filename):raise ValueError('Physical input copy changed')
            h,u,v=[state[k][i*size:(i+1)*size] for k in ('h','u','v')]
            bed=np.load(after/'bed.npy',allow_pickle=False)
            np.savez_compressed(after/'initial_state.npz',depth=h,eta=bed+h,u=u,v=v,hu=h*u,hv=h*v,wet=h>1e-6)
            with np.load(after/'initial_state.npz',allow_pickle=False) as saved:
                if any(not np.array_equal(saved[k],a) for k,a in (('depth',h),('u',u),('v',v))):
                    raise ValueError('Exact checkpoint serialization changed')
            updated['inputs'].append(dict(name=name,files={f:sha(after/f) for f in
                ('bed.npy','scenario.json','features.json','probes.json','initial_state.npz')}))
        updated.update(initial_time_seconds=receipt['time_seconds'],
            initial_state='Exact independently audited interrupted checkpoint; no reconstructed velocities',
            restart=dict(source_frame=frame.relative_to(ROOT).as_posix(),source_time_seconds=receipt['time_seconds'],
                source_arrays_sha256=last['arrays_sha256'],added_tiles=0,physical_inputs_unchanged=True),
            interrupted_recovery=dict(producer=previous.relative_to(ROOT).as_posix(),
                failure_sha256=pins[terminal],audit_sha256=pins[audit_path],
                original_terminal_run_audited=False,original_audit_restart_authorized=False),
            sources_sha256={p.relative_to(ROOT).as_posix():h for p,h in pins.items()})
        target=packages/'manifest.json'
        with target.open('x') as stream:json.dump(updated,stream,indent=2,allow_nan=False)
        pins[target]=sha(target)
        for row in updated['inputs']:
            pins.update({packages/row['name']/f:h for f,h in row['files'].items()})
        command=[str(solver),str(target),str(output/'native'),'30000','3000','4']
        save('request.json',dict(command=command,steps=30000,snapshot_interval_steps=3000,dt_seconds=.01,
            source_time_seconds=receipt['time_seconds'],target_time_seconds=receipt['time_seconds']+300.,
            maximum_wall_seconds=4*3600,source_audit_sha256=pins[audit_path],
            recovery='Exact audited snapshot from interrupted guard-owned producer; original failure preserved'))
        stage='prelaunch';verify();require_launch_headroom(resources(),busy())
        minimum=resources();save('prelaunch.json',dict(resources=minimum,shared_work=[]))
        stage='native_advance';native_started=time.monotonic()
        with (output/'native.log').open('x') as log:
            child=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            save('launch.json',dict(pid=child.pid));print('Recovered native checkpoint PID '+str(child.pid),flush=True)
            while child.poll() is None:
                try:child.wait(timeout=5)
                except subprocess.TimeoutExpired:pass
                current=resources();active=busy(child.pid);elapsed=time.monotonic()-native_started
                minimum={k:min(minimum[k],current[k]) for k in current}
                with (output/'resources.jsonl').open('a') as stream:
                    stream.write(json.dumps(dict(elapsed_seconds=elapsed,resources=current,shared_work=active))+'\n')
                reason=watchdog_failure(current,active,elapsed)
                if reason:raise RuntimeError(reason)
        if child.returncode or not (output/'native/completed.json').is_file():
            raise RuntimeError('Native state gate failed; preserve failure fields')
        stage='restart_equality_review';first=output/'native/frame_000000'
        if (json.loads((first/'complete.json').read_text())['time_seconds']!=receipt['time_seconds'] or
            any(sha(first/(k+'.npy'))!=last['arrays_sha256'][k] for k in state)):
            raise ValueError('Native restart fields or clock changed')
        verify()
        save('completed.json',dict(exit_code=0,native_restart_fields_and_clock_exact=True,
            recovered_interrupted_checkpoint=True,source_time_seconds=receipt['time_seconds'],
            elapsed_seconds=time.monotonic()-started,minimum_resources=minimum,
            saved_state_geographic_audit_pending=True,settled_hydraulics=False,
            normal_map_integrated=False,packaged_fps_verified=False))
        print('Recovered native advance complete; independent geographic audit still required',flush=True)
    except Exception as exc:
        if child is not None and child.poll() is None:child.terminate();child.wait(timeout=30)
        save('failure.json',dict(stage=stage,failure=str(exc),exit_code=None if child is None else child.returncode,
            native_process_started=child is not None,elapsed_seconds=time.monotonic()-started,
            minimum_resources=minimum,settled_hydraulics=False,normal_map_integrated=False,packaged_fps_verified=False))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('audit','solver','out'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();run(args.audit,args.solver,args.out)
