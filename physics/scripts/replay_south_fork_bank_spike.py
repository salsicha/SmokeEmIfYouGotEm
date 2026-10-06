"""Bounded diagnostic replay of a rejected survey history, never an export gate.

Preserve the complete original domain/bed/forcing; only restart state and output
cadence change. A binary override is an explicit numerical A/B experiment.
"""
from pathlib import Path
from dataclasses import replace
import argparse
import hashlib
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tmp/south-fork-geospatial-deps'))
sys.path.insert(0, str(ROOT/'physics/src'))
import numpy as np
from raftsim.scenario2_5d import read_scenario2_5d_package
from audit_troublemaker_hydraulic_spinup import validated_frame_state
from south_fork_survey_sanity import check_frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--binary', type=Path)
    parser.add_argument('--frame', type=int, default=4)
    parser.add_argument('--steps', type=int, default=210)
    args = parser.parse_args()
    if args.frame < 0 or not 1 <= args.steps <= 300:
        raise ValueError('Bounded replay requires a nonnegative frame and 1..300 steps')
    if args.output.exists():
        raise FileExistsError('Preserve prior experiment evidence')
    work = args.run.resolve()
    run = json.loads((work/'run_result.json').read_text())
    reg = json.loads((work/'registration.json').read_text())
    scenario = read_scenario2_5d_package(next((work/'scenario').glob('*/scenario.json')))
    grid = scenario.grid
    if ((grid.nx,grid.ny)!=(542,322) or grid.dx!=0.5 or grid.dy!=0.5 or
        abs(grid.origin_x+135.25)>1e-9 or abs(grid.origin_y+80.25)>1e-9 or
        reg.get('bed_sampling')!='render_triangles'):
        raise ValueError('This recorded hotspot requires the registered half-metre triangle grid')
    if any(b.hydrograph for b in scenario.boundaries):
        raise ValueError('Clock-reset replay requires constant boundaries')
    command = list(run['command'])
    if command[command.index('--feature-strength-scale')+1] != '0':
        raise ValueError('Clock-reset replay requires disabled time-dependent features')
    folder = ROOT/run['output_dir']
    manifest = json.loads((folder/'manifest.json').read_text())
    if args.frame >= len(manifest['frames']):
        raise ValueError('Requested restart frame is not present')
    source = (folder/manifest['frames'][args.frame]).resolve()
    if not source.is_relative_to(folder.resolve()):
        raise ValueError('Frame escaped source directory')
    raw = np.genfromtxt(source, delimiter=',', names=True)
    if not check_frame(raw)['passed']:
        raise ValueError('Choose a sane preceding state, not the rejected spike')
    state = validated_frame_state(scenario, raw)
    scenario = replace(scenario, initial_state=state, duration=args.steps*scenario.fixed_dt)
    binary = args.binary.resolve() if args.binary else Path(command[0])
    binary_sha = hashlib.sha256(binary.read_bytes()).hexdigest()
    if not args.binary and binary_sha != reg['solver_binary_sha256']:
        raise ValueError('Original replay binary changed')
    args.output.mkdir(parents=True)
    package = args.output/'scenario'
    scenario.write_package(package)
    command[0] = str(binary)
    for key, value in (('--scenario',str(package.resolve())),
                       ('--output',str((args.output/'solver').resolve())),
                       ('--steps',str(args.steps)), ('--frame-interval','10')):
        command[command.index(key)+1] = value
    metadata = {'source_run':work.relative_to(ROOT).as_posix(),
        'source_frame':source.relative_to(ROOT).as_posix(),
        'source_frame_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'source_registration_sha256':hashlib.sha256((work/'registration.json').read_bytes()).hexdigest(),
        'binary_sha256':binary_sha, 'binary_override':bool(args.binary),
        'source_time_seconds':args.frame*int(run['command'][run['command'].index('--frame-interval')+1])*scenario.fixed_dt,
        'command':command, 'production_promoted':False}
    (args.output/'replay.json').write_text(json.dumps(metadata,indent=2))
    start = time.perf_counter()
    result = subprocess.run(command,capture_output=True,text=True)
    metadata.update(returncode=result.returncode, runtime_seconds=time.perf_counter()-start,
                    stdout=result.stdout,stderr=result.stderr)
    (args.output/'replay.json').write_text(json.dumps(metadata,indent=2))
    if result.returncode:
        raise RuntimeError(result.stderr)
    output = args.output/'solver'/scenario.metadata.scenario_id
    frames = json.loads((output/'manifest.json').read_text())['frames']
    reports = []
    for index, name in enumerate(frames):
        frame = output/name
        data = np.genfromtxt(frame,delimiter=',',names=True)
        speed = np.hypot(data['u'],data['v'])
        peak = data[int(np.argmax(speed))]
        target = data[(data['row']==104)&(data['col']==230)][0]
        record = lambda row:{key:float(row[key]) for key in ('row','col','x','y','h','eta','u','v','hu','hv')}
        reports.append({'time_seconds':metadata['source_time_seconds']+min(index*10,args.steps)*scenario.fixed_dt,
            'frame':name,'sha256':hashlib.sha256(frame.read_bytes()).hexdigest(),
            'sanity':check_frame(data),'peak':record(peak),'target':record(target)})
    metadata.update(frames=reports,all_saved_frames_sane=all(r['sanity']['passed'] for r in reports),
                    scope='Diagnostic restart; not bitwise checkpoint, convergence or production acceptance')
    (args.output/'replay.json').write_text(json.dumps(metadata,indent=2,allow_nan=False))
    print(json.dumps({k:v for k,v in metadata.items() if k!='frames'},indent=2),flush=True)


if __name__ == '__main__':
    main()
