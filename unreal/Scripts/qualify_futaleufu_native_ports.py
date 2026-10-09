"""Bounded, resource-guarded native full-route cold-start qualification.

Checks actual saved states and clock, not an offline substitute. Short-time
success is not a settled river, boat test, native map or 20 FPS acceptance.
"""
import argparse
import ctypes
import json
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np

from build_futaleufu_continuous_water_domain import (
    ROOT, PREFIX, sha, FutaleufuBed, connected_tiles, observe_branches)
from prepare_futaleufu_hydraulic_ports import FACES

# PowerShell 7 where installed, otherwise the built-in Windows PowerShell;
# both provide Get-CimInstance and ConvertTo-Json for the process guards.
POWERSHELL = shutil.which('pwsh') or shutil.which('powershell') or 'powershell'


class MemoryStatus(ctypes.Structure):
    _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[
        (name,ctypes.c_ulonglong) for name in ('total_physical','available_physical','total_commit','available_commit',
                                             'total_virtual','available_virtual','extended_virtual')]


def resources():
    state=MemoryStatus();state.length=ctypes.sizeof(state)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(state)):
        raise OSError('Cannot read Windows resource guard')
    return dict(available_physical_bytes=state.available_physical,available_commit_bytes=state.available_commit,
                free_disk_bytes=shutil.disk_usage(ROOT).free)


def run(packages,solver,output,steps=200):
    packages,solver,output=[Path(p).resolve() for p in (packages,solver,output)]
    output.relative_to(ROOT)
    if output.exists() or not isinstance(steps,int) or not 20<=steps<=200 or steps%20:
        raise ValueError('Fresh output and bounded 20-multiple native steps (20..200) required')
    if sha(solver)!='fb2624bb8cb210142ae17741c5358c86a48d6f42c60eedab64715def53c6e558':
        raise ValueError('Use the existing source-verified Cartesian executable')
    active=subprocess.run([POWERSHELL,'-NoProfile','-Command',
        "Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(UnrealEditor|UnrealEditor-Cmd|raftsim_cartesian_cook|UnrealBuildTool)\\.exe$' } | Select-Object ProcessId,Name | ConvertTo-Json -Compress"],
        capture_output=True,text=True,check=True)
    if active.stdout.strip(): raise ValueError('Shared engine/cook work active; no duplicate or interruption')
    manifest_path=packages/'manifest.json';m=json.loads(manifest_path.read_text())
    if m.get('schema')!='raftsim.cartesian_flow_cook.v1' or m['dt_seconds']!=.01:
        raise ValueError('Reviewed native Cartesian packages required')
    pins={ROOT/p:h for p,h in m['sources_sha256'].items()}
    for p in (manifest_path,solver,Path(__file__).resolve()):pins[p]=sha(p)
    for row in m['inputs']:
        for name,h in row['files'].items():pins[packages/row['name']/name]=h
    def verify():
        for p,h in pins.items():
            if sha(p)!=h:raise ValueError('Changed native qualification input: '+str(p))
    verify()
    size=m['grid']['tile_cells'];cells=len(m['packages'])*size*size
    initial=resources();storage=cells*3*8*(steps//20+2)
    if (min(initial['available_physical_bytes'],initial['available_commit_bytes'])<6*1024**3
            or initial['free_disk_bytes']<40*1024**3+storage+1024**3):
        raise ValueError('Insufficient native-run resource headroom')
    output.mkdir(parents=True)
    def save(name,value): (output/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    command=[str(solver),str(manifest_path),str(output/'native'),str(steps),'20','4']
    save('request.json',dict(command=command,steps=steps,dt_seconds=.01,cells=cells,initial_resources=initial,
         sources_sha256={p.relative_to(ROOT).as_posix():h for p,h in pins.items()},timeout_seconds=3600))
    started=time.monotonic();failure=None;minimum=initial.copy()
    with (output/'native.log').open('x') as log:
        child=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        save('launch.json',dict(pid=child.pid));print('Native coupled cook PID '+str(child.pid),flush=True)
        while child.poll() is None:
            try:child.wait(timeout=5.)
            except subprocess.TimeoutExpired:
                r=resources();minimum={k:min(minimum[k],r[k]) for k in r}
                if min(r['available_physical_bytes'],r['available_commit_bytes'])<3*1024**3:failure='Owned cook resource floor reached'
                if r['free_disk_bytes']<40*1024**3:failure='Owned cook disk reserve reached'
                if time.monotonic()-started>3600:failure='Owned cook exceeded one-hour bound'
                if failure:
                    child.terminate();child.wait(timeout=30);break
    code=child.returncode
    result=dict(exit_code=code,elapsed_seconds=time.monotonic()-started,minimum_resources=minimum,
        steps=steps,native_time_seconds=steps*.01,settled_hydraulics=False,normal_map_integrated=False,packaged_fps_verified=False)
    if failure or code or not (output/'native/completed.json').is_file():
        result['failure']=failure or 'Native failure; retain log and full failure state'
        save('failure.json',result);raise RuntimeError(result)
    try:
        frames=[];native=output/'native'
        reference=FutaleufuBed(ROOT/'tmp/futaleufu-continuous-source-window-v2',
            PREFIX/'hydrology/channel_profile_2026_10_v2',PREFIX/'hydrography/confluence_network_2026_10_v1/network.json',depth_m=1.8)
        keys=[tuple(k) for k in m['tile_indices']]
        tile_set=set(keys)
        open_faces={(r['tile_index'],r['edge']) for r in m['boundary_probes']}
        for step in range(0,steps+1,20):
            folder=native/('frame_%06d'%step);receipt=json.loads((folder/'complete.json').read_text())
            if receipt['step']!=step or abs(receipt['time_seconds']-step*.01)>1e-10:
                raise ValueError('Actual native clock/frame sequence differs')
            a={k:np.load(folder/(k+'.npy'),mmap_mode='r',allow_pickle=False) for k in ('h','u','v')}
            if any(v.shape!=(len(keys)*size,size) or not np.isfinite(v).all() for v in a.values()):
                raise ValueError('Saved native field incomplete/nonfinite')
            h,u,v=(a[k] for k in ('h','u','v'))
            if h.min()<0 or h.max()>10 or np.hypot(u,v).max()>20:raise ValueError('Saved native state violates unchanged gates')
            if step==0:
                if np.any(u) or np.any(v):raise ValueError('Cold start has nonzero interior velocities')
                for i,name in enumerate(m['packages']):
                    with np.load(packages/name/'initial_state.npz',allow_pickle=False) as z:
                        if not np.array_equal(h[i*size:(i+1)*size],z['depth']):raise ValueError('Native initial depth differs from packages')
            labels,offset,counts=connected_tiles({key:h[i*size:(i+1)*size]>.05 for i,key in enumerate(keys)})
            observations,common=observe_branches(reference,labels,offset,m['horizontal_origin_utm18s_m'],1.)
            wet_closed_faces=[]
            for i,key in enumerate(keys):
                for edge,(sl,delta,_,_) in FACES.items():
                    if (key[0]+delta[0],key[1]+delta[1]) in tile_set or (i,edge) in open_faces:continue
                    values=h[i*size:(i+1)*size][sl]
                    if np.any(values>.05):wet_closed_faces.append(dict(tile=list(key),edge=edge,maximum_depth_m=float(values.max())))
            if receipt['maximum_step_residual_m3']>.001*.01:raise ValueError('Native conservation gate failed')
            frames.append(dict(step=step,time_seconds=receipt['time_seconds'],volume_m3=float(h.sum()),
                maximum_depth_m=float(h.max()),maximum_speed_mps=float(np.hypot(u,v).max()),
                common_original_route_components=common,dry_original_route_sections=[r for r in observations if not r['wet_components']],
                original_route_connected=bool(common),conservation_residual_m3=receipt['conservation_residual_m3'],
                wet_closed_exterior_faces=wet_closed_faces,
                maximum_step_residual_m3=receipt['maximum_step_residual_m3'],exterior_fluxes=receipt['exterior_fluxes'],
                fields_sha256={k:sha(folder/(k+'.npy')) for k in a}))
        verify();result['frames']=frames
        result['original_route_connected_all_frames']=all(f['original_route_connected'] for f in frames)
        result['closed_exterior_banks_dry_all_frames']=all(not f['wet_closed_exterior_faces'] for f in frames)
        result['native_initial_state_exact']=True
        save('completion.json',result);print(json.dumps({k:v for k,v in result.items() if k!='frames'}),flush=True)
    except Exception as exc:
        result['failure']=str(exc);save('failure.json',result);raise
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('packages','solver','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--steps',type=int,default=200)
    a=p.parse_args();run(a.packages,a.solver,a.out,a.steps)
