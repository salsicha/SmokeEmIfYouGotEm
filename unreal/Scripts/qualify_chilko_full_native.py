"""Load/save the entire completed Chilko grid in the production native solver.

This measures a full-domain initial frame before a costly timed cook. It does
not establish settled flow, navigability, rendered terrain or game performance.
No historical source, physical input, extent or acceptance gate is changed.
"""
import argparse
import json
from pathlib import Path
import subprocess
import time

import numpy as np

from qualify_futaleufu_native_ports import ROOT, sha, resources
from continue_futaleufu_native_flow import shared_native_work
from build_chilko_completed_corridor_inputs import require_idle_headroom, watchdog_failure
from native_frame_io import NativeFrameStore, native_frame_paths
from review_chilko_continuous_cook import validate_native, validate_frame, validate_initial_frame

SOLVER_SHA='356f1af32946d69b7ccd55c2cd8390da4ea2095bf2c32a915316e7d8b9ab1dc8'
FLAGS=['--solver-mode','finite_volume','--boundary-mode','scenario','--flux-scheme','hll',
       '--spatial-order','2','--cfl','0.2','--feature-strength-scale','0','--roughness-scale','1',
       '--bed-slope-source-scale','1','--no-preserve-initial-mass','--disable-fixture-calibrations',
       '--stream-output','--progress']


def busy(owned=None):
    rows=shared_native_work(owned)
    result=subprocess.run(['pwsh','-NoProfile','-Command',
        "Get-CimInstance Win32_Process -Filter \"Name = 'raftsim_water_solver.exe'\" | "
        'Select-Object ProcessId,Name | ConvertTo-Json -Compress'],capture_output=True,text=True,check=True)
    other=json.loads(result.stdout) if result.stdout.strip() else []
    if isinstance(other,dict):other=[other]
    return rows+[r for r in other if r['ProcessId']!=owned]


def validate_inputs(completion, report, scenario):
    grid=scenario.get('grid',{})
    if (completion.get('exit_code')!=0 or completion.get('inputs_unchanged') is not True or
        completion.get('full_route_inputs') is not True or
        report.get('full_route_hydraulic_inputs') is not True or report.get('full_route_chart') is not True or
        report.get('complete_source_route_length_m')!=55723.04503105954 or
        report.get('stations')!=25552 or report.get('lateral_cells')!=257 or
        any(grid.get(k)!=v for k,v in dict(nx=25552,ny=257,dx=2.,dy=2.).items()) or
        scenario.get('metadata',{}).get('river_id')!='chilko_river_bc' or
        scenario.get('feature_count')!=0 or scenario.get('fixed_dt')!=.05):
        raise ValueError('Completed unchanged full Chilko input grid required')
    identifier=scenario['metadata'].get('scenario_id','')
    if not identifier or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_' for c in identifier):
        raise ValueError('Safe native scenario identifier required')


def validate_execution(log, identifier):
    expected={'scenario_id':identifier,'solver':'raftsim_water_cpp_v1',
              'steps':'0','frames':'1','validation_passed':'true'}
    for key,value in expected.items():
        matches=[line.split('=',1)[1] for line in log.splitlines() if line.startswith(key+'=')]
        if matches!=[value]:
            raise ValueError('Native initialization execution receipt mismatch: '+key)


def run(inputs, input_job, solver, job):
    inputs,input_job,solver,job=[Path(p).resolve() for p in (inputs,input_job,solver,job)]
    for p in (inputs,input_job,solver,job):p.relative_to(ROOT/'tmp')
    if job.exists():raise ValueError('Fresh qualification job required')
    if sha(solver)!=SOLVER_SHA:raise ValueError('Use the source-matching seed-ownership native solver')
    completion_path=input_job/'completed.json'
    if (input_job/'failure.json').exists():raise ValueError('Conflicting input completion/failure receipts')
    completion=json.loads(completion_path.read_text())
    report=json.loads((inputs/'build_report.json').read_text())
    scenario=json.loads((inputs/'scenario/scenario.json').read_text())
    validate_inputs(completion,report,scenario)
    pins={completion_path:sha(completion_path),solver:sha(solver)}
    for name,digest in completion['files_sha256'].items():
        path=(inputs/name).resolve();path.relative_to(inputs);pins[path]=digest
    required=['build_report.json','coordinate_map.json','reference.npz','scenario/scenario.json',
              'scenario/bed.npy','scenario/initial_state.npz','scenario/features.json','scenario/probes.json']
    if any(inputs/name not in pins for name in required):raise ValueError('Incomplete input completion hashes')
    for path in (Path(__file__).resolve(),ROOT/'physics/scripts/native_frame_io.py',
                 ROOT/'physics/scripts/review_chilko_continuous_cook.py',
                 ROOT/'unreal/Scripts/build_chilko_completed_corridor_inputs.py',
                 ROOT/'unreal/Scripts/continue_futaleufu_native_flow.py'):
        pins[path]=sha(path)
    def verify():
        for path,digest in pins.items():
            if sha(path)!=digest:raise ValueError('Changed qualification input: '+str(path))
    verify();require_idle_headroom(resources(),busy())
    job.mkdir(parents=True)
    def save(name,value):
        with (job/name).open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2,allow_nan=False)
    command=[str(solver),'--scenario',str(inputs/'scenario'),'--output',str(job/'native'),
             '--steps','0','--frame-interval','1',*FLAGS]
    save('request.json',dict(command=command,steps=0,full_domain_cells=25552*257,
        source_sha256={p.relative_to(ROOT).as_posix():h for p,h in pins.items()},
        purpose='Full-domain initialization/output/resource qualification, not a timed cook',maximum_seconds=1800))
    child=None;started=time.monotonic();minimum=resources();stage='prelaunch'
    try:
        verify();require_idle_headroom(resources(),busy())
        stage='native_initial_frame'
        with (job/'native.log').open('x') as log:
            child=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            save('launch.json',dict(pid=child.pid));print('Full Chilko native initialization PID '+str(child.pid),flush=True)
            while child.poll() is None:
                try:child.wait(timeout=5)
                except subprocess.TimeoutExpired:pass
                current=resources();active=busy(child.pid);elapsed=time.monotonic()-started
                minimum={k:min(minimum[k],current[k]) for k in current}
                with (job/'resources.jsonl').open('a') as stream:
                    stream.write(json.dumps(dict(elapsed_seconds=elapsed,resources=current,shared_work=active))+'\n')
                failure=watchdog_failure(current,active,elapsed)
                if failure or elapsed>1800:raise RuntimeError(failure or 'Bounded initialization time exceeded')
        if child.returncode!=0:raise RuntimeError('Native initialization failed; inspect native.log')
        validate_execution((job/'native.log').read_text(),scenario['metadata']['scenario_id'])
        stage='complete_frame_review';require_idle_headroom(resources(),busy())
        cook=job/'native'/scenario['metadata']['scenario_id']
        native=json.loads((cook/'manifest.json').read_text());validation=json.loads((cook/'validation.json').read_text())
        validate_native(native,validation,scenario)
        frames=native_frame_paths(cook,native)
        if len(frames)!=1 or native.get('frame_storage')!='streamed_lossless_gzip_csv_v1':
            raise ValueError('Exactly one complete lossless initial frame required')
        shape=(257,25552);bed=np.load(inputs/'scenario/bed.npy',mmap_mode='r',allow_pickle=False)
        with NativeFrameStore(job) as store, np.load(inputs/'scenario/initial_state.npz',allow_pickle=False) as initial:
            frame=store.load(frames[0],shape)
            validate_frame(frame,bed,scenario['grid']);validate_initial_frame(frame,initial)
        verify()
        save('completed.json',dict(exit_code=0,full_domain_cells=25552*257,actual_native_steps=0,
            initial_fields_and_grid_verified=True,frame_bytes=frames[0].stat().st_size,
            frame_sha256=sha(frames[0]),native_manifest_sha256=sha(cook/'manifest.json'),
            native_execution_sha256=sha(job/'native.log'),
            native_validation_sha256=sha(cook/'validation.json'),minimum_observed_resources=minimum,
            elapsed_seconds=time.monotonic()-started,inputs_unchanged=True,
            timed_cook_completed=False,hydraulic_solution=False,engine_validated=False,packaged_fps_verified=False))
        print('Full Chilko native initial frame verified',flush=True)
    except Exception as exc:
        if child is not None and child.poll() is None:child.terminate();child.wait(timeout=30)
        save('failure.json',dict(stage=stage,failure=str(exc),elapsed_seconds=time.monotonic()-started,
            minimum_observed_resources=minimum,native_process_started=child is not None))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('inputs','input-job','solver','job'):parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args();run(args.inputs,args.input_job,args.solver,args.job)
