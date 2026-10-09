"""Advance the complete qualified Chilko domain; retain every native snapshot.

Large native outputs and bounded review scratch use a fresh system-temp folder,
not the space-constrained project volume. Both volumes retain a 40 GiB reserve.
This is a first timed full-domain advance, not settled-flow or game acceptance.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

import numpy as np

from qualify_chilko_full_native import ROOT, SOLVER_SHA, FLAGS, busy, sha, resources, validate_inputs
from build_chilko_completed_corridor_inputs import require_idle_headroom, watchdog_failure
from native_frame_io import NativeFrameStore, native_frame_paths
from review_chilko_continuous_cook import validate_native, validate_frame, inlet_outlet_wet_path

CELLS=25552*257
STEPS=200
INTERVAL=20


def require_qualification(completion):
    if (completion.get('exit_code')!=0 or completion.get('full_domain_cells')!=CELLS or
        completion.get('actual_native_steps')!=0 or completion.get('initial_fields_and_grid_verified') is not True or
        completion.get('inputs_unchanged') is not True or
        not isinstance(completion.get('frame_bytes'),int) or completion['frame_bytes']<=0):
        raise ValueError('Successful unchanged complete-domain initialization required')


def validate_execution(log, identifier):
    for key,value in dict(scenario_id=identifier,solver='raftsim_water_cpp_v1',steps=str(STEPS),
                          frames=str(1+STEPS//INTERVAL),validation_passed='true').items():
        if [s.split('=',1)[1] for s in log.splitlines() if s.startswith(key+'=')]!=[value]:
            raise ValueError('Native timed execution differs: '+key)


def scratch_requirement(initial_frame_bytes):
    # Twice the measured compressed size per snapshot plus three full numeric
    # frame maps. This is planning headroom, not a cap on recorded field values.
    return 40*1024**3+2*(1+STEPS//INTERVAL)*initial_frame_bytes+3*CELLS*15*8


def run(inputs,input_job,qualification,solver,job):
    inputs,input_job,qualification,solver,job=[Path(p).resolve() for p in
                                              (inputs,input_job,qualification,solver,job)]
    for path in (inputs,input_job,qualification,solver,job):path.relative_to(ROOT/'tmp')
    if job.exists():raise ValueError('Fresh full-domain advance job required')
    if (qualification/'failure.json').exists() or (input_job/'failure.json').exists():
        raise ValueError('Do not reuse failed or conflicting source receipts')
    completed=json.loads((qualification/'completed.json').read_text());require_qualification(completed)
    request=json.loads((qualification/'request.json').read_text())
    input_completion=json.loads((input_job/'completed.json').read_text())
    report=json.loads((inputs/'build_report.json').read_text())
    scenario=json.loads((inputs/'scenario/scenario.json').read_text())
    validate_inputs(input_completion,report,scenario)
    if sha(solver)!=SOLVER_SHA:raise ValueError('Source-matching qualified native solver required')
    pins={}
    for name,digest in request['source_sha256'].items():
        path=(ROOT/name).resolve();path.relative_to(ROOT);pins[path]=digest
    for name,digest in input_completion['files_sha256'].items():
        path=(inputs/name).resolve();path.relative_to(inputs)
        if pins.get(path)!=digest:raise ValueError('Qualification belongs to different input fields')
    if pins.get(solver)!=SOLVER_SHA:raise ValueError('Qualification belongs to a different solver')
    initial=qualification/'native'/scenario['metadata']['scenario_id']/'frames/frame_0000.csv.gz'
    pins[initial]=completed['frame_sha256']
    for path in (qualification/'completed.json',qualification/'request.json',Path(__file__).resolve()):pins[path]=sha(path)
    def verify():
        for path,digest in pins.items():
            if sha(path)!=digest:raise ValueError('Changed full-domain advance input: '+str(path))
    verify();require_idle_headroom(resources(),busy())
    scratch_parent=Path(tempfile.gettempdir()).resolve()
    if shutil.disk_usage(scratch_parent).free<scratch_requirement(completed['frame_bytes']):
        raise ValueError('System-temp volume lacks full snapshot and review headroom')
    job.mkdir(parents=True)
    scratch=Path(tempfile.mkdtemp(prefix='raftsim-chilko-full-native-',dir=scratch_parent)).resolve()
    scratch.relative_to(scratch_parent)
    def save(name,value):
        with (job/name).open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2,allow_nan=False)
    command=[str(solver),'--scenario',str(inputs/'scenario'),'--output',str(scratch),
             '--steps',str(STEPS),'--frame-interval',str(INTERVAL),*FLAGS]
    save('request.json',dict(command=command,native_output=str(scratch),full_domain_cells=CELLS,
        steps=STEPS,frame_interval=INTERVAL,expected_snapshots=1+STEPS//INTERVAL,
        requested_simulation_seconds=STEPS*scenario['fixed_dt'],maximum_wall_seconds=8*3600,
        source_sha256={p.relative_to(ROOT).as_posix():h for p,h in pins.items()},
        storage_policy='Fresh system-temp native output retained; project and output volumes both keep forty GiB',
        initial_scratch_free_bytes=shutil.disk_usage(scratch).free))
    started=time.monotonic();child=None;minimum=resources();scratch_min=shutil.disk_usage(scratch).free;stage='prelaunch'
    def guard():
        nonlocal minimum,scratch_min
        current=resources();active=busy(child.pid if child is not None else None)
        free=shutil.disk_usage(scratch).free;scratch_min=min(scratch_min,free)
        minimum={k:min(minimum[k],current[k]) for k in current};elapsed=time.monotonic()-started
        with (job/'resources.jsonl').open('a') as stream:
            stream.write(json.dumps(dict(elapsed_seconds=elapsed,resources=current,
                scratch_free_bytes=free,shared_work=active))+'\n')
        reason=watchdog_failure(current,active,elapsed)
        if reason or free<40*1024**3:raise RuntimeError(reason or 'System-temp disk reserve reached')
    try:
        verify();require_idle_headroom(resources(),busy());guard();stage='native_advance'
        with (job/'native.log').open('x') as log:
            child=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            save('launch.json',dict(pid=child.pid));print('Full Chilko timed native advance PID '+str(child.pid),flush=True)
            while child.poll() is None:
                try:child.wait(timeout=5)
                except subprocess.TimeoutExpired:pass
                guard()
        if child.returncode:raise RuntimeError('Native timed advance failed; inspect preserved log and fields')
        validate_execution((job/'native.log').read_text(),scenario['metadata']['scenario_id'])
        stage='complete_snapshot_review';cook=scratch/scenario['metadata']['scenario_id']
        native=json.loads((cook/'manifest.json').read_text());validation=json.loads((cook/'validation.json').read_text())
        validate_native(native,validation,scenario);frames=native_frame_paths(cook,native,minimum=11)
        if len(frames)!=11 or native.get('frame_storage')!='streamed_lossless_gzip_csv_v1':
            raise ValueError('All eleven complete lossless snapshots required')
        if sha(frames[0])!=completed['frame_sha256']:raise ValueError('Native initial frame differs from qualification')
        bed=np.load(inputs/'scenario/bed.npy',mmap_mode='r',allow_pickle=False);snapshots=[]
        for i,path in enumerate(frames):
            guard()
            with NativeFrameStore(scratch) as store:
                frame=store.load(path,(257,25552));validate_frame(frame,bed,scenario['grid'])
                snapshots.append(dict(step=i*INTERVAL,time_seconds=i*INTERVAL*scenario['fixed_dt'],
                    path=str(path),bytes=path.stat().st_size,sha256=sha(path),
                    maximum_depth_m=float(frame['h'].max()),
                    maximum_speed_mps=float(np.hypot(frame['u'],frame['v']).max()),
                    inlet_to_outlet_wet_path=inlet_outlet_wet_path(frame)))
            print('Verified full snapshot '+str(i)+'/'+str(len(frames)-1),flush=True)
        guard();verify()
        save('completed.json',dict(exit_code=0,full_domain_cells=CELLS,actual_native_steps=STEPS,
            timed_cook_completed=True,simulation_seconds=STEPS*scenario['fixed_dt'],snapshots=snapshots,
            native_manifest_sha256=sha(cook/'manifest.json'),native_validation_sha256=sha(cook/'validation.json'),
            native_execution_sha256=sha(job/'native.log'),inputs_unchanged=True,
            minimum_observed_resources=minimum,minimum_scratch_free_bytes=scratch_min,
            elapsed_seconds=time.monotonic()-started,geographic_review_pending=True,
            settled_hydraulics=False,engine_validated=False,packaged_fps_verified=False))
        print('Full-domain timed snapshots verified; geographic/settling review remains',flush=True)
    except Exception as exc:
        if child is not None and child.poll() is None:child.terminate();child.wait(timeout=30)
        save('failure.json',dict(stage=stage,failure=str(exc),native_output=str(scratch),
            native_process_started=child is not None,exit_code=None if child is None else child.returncode,
            elapsed_seconds=time.monotonic()-started,minimum_observed_resources=minimum,
            minimum_scratch_free_bytes=scratch_min,engine_validated=False,packaged_fps_verified=False))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('inputs','input-job','qualification','solver','job'):parser.add_argument('--'+key,type=Path,required=True)
    a=parser.parse_args();run(a.inputs,a.input_job,a.qualification,a.solver,a.job)
