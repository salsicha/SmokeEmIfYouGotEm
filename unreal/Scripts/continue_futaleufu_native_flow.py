"""Continue an accepted short native run without changing its physical inputs.

Restart states and clock come from actual saved native arrays. No interpolation,
velocity seed, terrain change, new tile, source-flow change or relaxed gate.
"""
import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np

from qualify_futaleufu_native_ports import ROOT, sha, resources, POWERSHELL


def shared_native_work(owned_pid=None):
    """Read actual processes; never interrupt another task or trust stale locks."""
    active = subprocess.run([POWERSHELL, '-NoProfile', '-Command',
        "Get-CimInstance Win32_Process | Where-Object { "
        "$_.Name -match '^(UnrealEditor|UnrealEditor-Cmd|raftsim_cartesian_cook|UnrealBuildTool)\\.exe$' -or "
        "($_.Name -eq 'dotnet.exe' -and $_.CommandLine -match 'UnrealBuildTool|AutomationTool') -or "
        "($_.Name -eq 'cmd.exe' -and $_.CommandLine -match 'Engine[\\/]Build[\\/]BatchFiles[\\/](Build|RunUAT).bat') "
        "} | Select-Object ProcessId,Name,PrivatePageCount | ConvertTo-Json -Compress"],
        capture_output=True, text=True, check=True)
    rows = json.loads(active.stdout) if active.stdout.strip() else []
    if isinstance(rows, dict): rows = [rows]
    return [row for row in rows if row['ProcessId'] != owned_pid]


def require_launch_headroom(current, busy):
    if busy: raise ValueError('Existing engine/build/cook work; do not overlap')
    if (min(current['available_physical_bytes'], current['available_commit_bytes']) < 6*1024**3
            or current['free_disk_bytes'] < 43*1024**3):
        raise ValueError('Native continuation resource allowance unavailable')


def runtime_guard_failure(current, busy, elapsed):
    if busy: return 'Shared engine/build/cook appeared; stopped only owned continuation'
    if min(current['available_physical_bytes'], current['available_commit_bytes']) < 3*1024**3:
        return 'Owned native resource floor reached'
    if current['free_disk_bytes'] < 40*1024**3: return 'Owned native disk reserve reached'
    if elapsed > 3600: return 'Owned native continuation exceeded one-hour bound'
    return None


def prepare(previous,output):
    previous,output=Path(previous).resolve(),Path(output).resolve()
    output.relative_to(ROOT)
    if output.exists():raise ValueError('Fresh exact-state continuation required')
    qualified=json.loads((previous/'completion.json').read_text())
    if (qualified['exit_code']!=0 or not qualified['original_route_connected_all_frames']
            or not qualified['closed_exterior_banks_dry_all_frames']):
        raise ValueError('Prior native run requires connected route and dry exterior banks')
    native=previous/'native';source=Path((native/'input_manifest_path.txt').read_text().strip()).resolve()
    source.relative_to(ROOT)
    if sha(source)!=sha(native/'input_manifest.json'):raise ValueError('Prior input manifest changed')
    manifest=json.loads(source.read_text());last=qualified['frames'][-1]
    frame=native/('frame_%06d'%last['step']);complete=json.loads((frame/'complete.json').read_text())
    if complete['time_seconds']!=last['time_seconds']:raise ValueError('Prior native clock differs from receipt')
    pins={ROOT/p:h for p,h in manifest['sources_sha256'].items()}
    for p in (source,previous/'completion.json',frame/'complete.json',Path(__file__).resolve()):pins[p]=sha(p)
    a={}
    for k in ('h','u','v'):
        path=frame/(k+'.npy');pins[path]=last['fields_sha256'][k]
        if sha(path)!=pins[path]:raise ValueError('Prior actual native state changed')
        a[k]=np.load(path,mmap_mode='r',allow_pickle=False)
    size=manifest['grid']['tile_cells'];shape=(len(manifest['packages'])*size,size)
    if any(v.shape!=shape or not np.isfinite(v).all() for v in a.values()):raise ValueError('Incomplete actual native state')
    if a['h'].min()<0 or a['h'].max()>10 or np.hypot(a['u'],a['v']).max()>20:raise ValueError('Restart state violates native gates')
    if shutil.disk_usage(ROOT).free<42*1024**3:raise ValueError('40 GiB reserve and restart allowance required')
    for row in manifest['inputs']:
        for name,h in row['files'].items():pins[source.parent/row['name']/name]=h
    def verify():
        for p,h in pins.items():
            if sha(p)!=h:raise ValueError('Continuation source changed: '+str(p))
    verify();output.mkdir(parents=True)
    result=copy.deepcopy(manifest);result['inputs']=[]
    for i,name in enumerate(manifest['packages']):
        before=source.parent/name;after=output/name;after.mkdir()
        for filename in ('bed.npy','scenario.json','features.json','probes.json'):
            shutil.copyfile(before/filename,after/filename)
        # Physical scenario and boundaries remain byte-identical. Change only
        # their nonphysical description so the restart is not called a cold start.
        scenario=json.loads((after/'scenario.json').read_text())
        scenario['metadata']['description']='Exact full-route native checkpoint continuation; not settled or gameplay accepted'
        (after/'scenario.json').write_text(json.dumps(scenario,indent=2,allow_nan=False)+'\n')
        old_scenario=json.loads((before/'scenario.json').read_text())
        check=copy.deepcopy(scenario);check['metadata']['description']=old_scenario['metadata']['description']
        if check!=old_scenario:raise ValueError('Physical restart scenario changed')
        h,u,v=[a[k][i*size:(i+1)*size] for k in ('h','u','v')]
        bed=np.load(after/'bed.npy',allow_pickle=False)
        np.savez_compressed(after/'initial_state.npz',depth=h,eta=bed+h,u=u,v=v,hu=h*u,hv=h*v,wet=h>1e-6)
        with np.load(after/'initial_state.npz',allow_pickle=False) as z:
            if any(not np.array_equal(z[field],values) for field,values in (('depth',h),('u',u),('v',v))):
                raise ValueError('Serialized restart state is not bit-exact')
        result['inputs'].append(dict(name=name,files={f:sha(after/f) for f in ('scenario.json','bed.npy','initial_state.npz','features.json','probes.json')}))
    verify()
    result.update(initial_time_seconds=complete['time_seconds'],initial_state='Bit-exact native checkpoint states; physical inputs unchanged',
        restart=dict(source_manifest=source.relative_to(ROOT).as_posix(),source_manifest_sha256=sha(source),
            source_frame=frame.relative_to(ROOT).as_posix(),source_time_seconds=complete['time_seconds'],
            source_arrays_sha256={k:sha(frame/(k+'.npy')) for k in a},added_tiles=0,physical_inputs_unchanged=True),
        sources_sha256={p.relative_to(ROOT).as_posix():h for p,h in pins.items()})
    (output/'manifest.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print('Serialized exact native restart at '+str(result['initial_time_seconds'])+' seconds',flush=True)
    return result


def run(previous,solver,output,steps=3000):
    previous,solver,output=[Path(p).resolve() for p in (previous,solver,output)]
    output.relative_to(ROOT)
    if output.exists() or steps!=3000:raise ValueError('Fresh bounded 30-second continuation required')
    if sha(solver)!='fb2624bb8cb210142ae17741c5358c86a48d6f42c60eedab64715def53c6e558':raise ValueError('Verified native executable required')
    r=resources()
    require_launch_headroom(r, shared_native_work())
    output.mkdir(parents=True)
    m=prepare(previous,output/'packages');input_path=output/'packages/manifest.json'
    pins={ROOT/p:h for p,h in m['sources_sha256'].items()}
    pins[input_path]=sha(input_path);pins[solver]=sha(solver)
    for row in m['inputs']:
        for f,h in row['files'].items():pins[output/'packages'/row['name']/f]=h
    def save(name,value):(output/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    command=[str(solver),str(input_path),str(output/'native'),str(steps),'300','4']
    save('request.json',dict(command=command,steps=steps,dt_seconds=.01,source_time_seconds=m['initial_time_seconds'],
        inputs_sha256={p.relative_to(ROOT).as_posix():h for p,h in pins.items()},initial_resources=r,timeout_seconds=3600))
    # Preparing thousands of exact checkpoint packages can take minutes. The
    # pre-prepare check is not permission to launch into subsequently started work.
    try:
        if any(sha(p)!=h for p,h in pins.items()):raise ValueError('Continuation input changed before launch')
        busy=shared_native_work();r=resources()
        save('prelaunch.json',dict(resources=r,shared_work=busy))
        require_launch_headroom(r,busy)
    except Exception as error:
        save('failure.json',dict(stage='prelaunch',native_process_started=False,failure=str(error)))
        raise
    start=time.monotonic();failure=None;minimum=r.copy()
    with (output/'native.log').open('x') as log:
        child=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        save('launch.json',dict(pid=child.pid));print('Native continuation PID '+str(child.pid),flush=True)
        while child.poll() is None:
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                r=resources();minimum={k:min(minimum[k],r[k]) for k in r}
                try:
                    busy=shared_native_work(child.pid)
                    sample=dict(elapsed_seconds=time.monotonic()-start,resources=r,shared_work=busy)
                    with (output/'resources.jsonl').open('a') as telemetry:
                        telemetry.write(json.dumps(sample,allow_nan=False)+'\n')
                    failure=runtime_guard_failure(r,busy,sample['elapsed_seconds'])
                except Exception as error:
                    failure='Native guard observation failed: '+str(error)
                if failure:child.terminate();child.wait(timeout=30);break
    result=dict(exit_code=child.returncode,elapsed_seconds=time.monotonic()-start,minimum_resources=minimum,
        source_time_seconds=m['initial_time_seconds'],target_time_seconds=m['initial_time_seconds']+steps*.01,
        settled_hydraulics=False,normal_map_integrated=False,packaged_fps_verified=False)
    if failure or child.returncode or not (output/'native/completed.json').is_file():
        result['failure']=failure or 'Native state gate failed; full failure fields retained'
        save('failure.json',result);raise RuntimeError(result)
    initial=output/'native/frame_000000'
    initial_receipt=json.loads((initial/'complete.json').read_text())
    frame=ROOT/m['restart']['source_frame']
    if initial_receipt['time_seconds']!=m['initial_time_seconds']:raise ValueError('Native restart clock changed')
    for k in ('h','u','v'):
        if sha(initial/(k+'.npy'))!=sha(frame/(k+'.npy')):raise ValueError('Native restart field bytes changed')
    if any(sha(p)!=h for p,h in pins.items()):raise ValueError('Native continuation inputs changed')
    result['native_restart_fields_and_clock_exact']=True
    result['saved_state_geographic_audit_pending']=True
    save('completed.json',result);print(json.dumps(result),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('previous','solver','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();run(a.previous,a.solver,a.out)
