"""Check actual face-flux conservation of a sane diagnostic replay endpoint.

This is not a steady-flow, resolution or visual acceptance test.
"""
from pathlib import Path
from dataclasses import replace
import argparse
import hashlib
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tmp/south-fork-geospatial-deps'))
sys.path.insert(0,str(ROOT/'physics/src'))
import numpy as np
from raftsim.scenario2_5d import read_scenario2_5d_package
from audit_troublemaker_hydraulic_spinup import validated_frame_state
from south_fork_survey_sanity import check_frame


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay',type=Path,required=True)
    args=parser.parse_args()
    work=args.replay.resolve()
    report=json.loads((work/'replay.json').read_text())
    if not report.get('all_saved_frames_sane'):
        raise ValueError('Do not rehabilitate a rejected replay through its endpoint')
    command=list(report['command'])
    if hashlib.sha256(Path(command[0]).read_bytes()).hexdigest()!=report['binary_sha256']:
        raise ValueError('Replay binary changed')
    source_scenario=read_scenario2_5d_package(work/'scenario/scenario.json')
    last=report['frames'][-1]
    source=work/'solver'/source_scenario.metadata.scenario_id/last['frame']
    if hashlib.sha256(source.read_bytes()).hexdigest()!=last['sha256']:
        raise ValueError('Replay endpoint changed')
    raw=np.genfromtxt(source,delimiter=',',names=True)
    if not check_frame(raw)['passed']:
        raise ValueError('Endpoint fails numerical sanity')
    state=validated_frame_state(source_scenario,raw)
    audit=work/'face-flux-audit'
    audit.mkdir(exist_ok=False)
    scenario=replace(source_scenario,fixed_dt=1e-6,duration=1e-6,initial_state=state,
        metadata=replace(source_scenario.metadata,scenario_id='bank_spike_flux_audit'))
    scenario.write_package(audit/'scenario')
    for key,value in (('--scenario',str(audit/'scenario')),('--output',str(audit/'solver')),
                      ('--steps','1'),('--frame-interval','1')):
        command[command.index(key)+1]=value
    flux=json.loads(subprocess.run([*command,'--inspect-boundary-flux'],check=True,capture_output=True,text=True).stdout)
    subprocess.run(command,check=True,capture_output=True,text=True)
    final=np.genfromtxt(audit/'solver/bank_spike_flux_audit/frames/frame_0001.csv',delimiter=',',names=True)
    derivative=(float(final['h'].sum())-float(state.depth.sum()))*scenario.grid.dx*scenario.grid.dy/scenario.fixed_dt
    target=float(command[command.index('--experimental-west-discharge')+1])
    checks={'inflow_matches_target':abs(flux['west']-target)<1e-8,
        'no_side_leak':abs(flux['north'])+abs(flux['south'])<1e-8,
        'net_flux_matches_volume_derivative':abs(derivative-flux['net'])<1e-3}
    result={'scope':__doc__.strip(),'checks':checks,'passed':all(checks.values()),
        'source_replay':work.relative_to(ROOT).as_posix(),'source_frame_sha256':last['sha256'],
        'binary_sha256':report['binary_sha256'],'numerical_flux_m3s':flux,
        'volume_derivative_m3s':derivative,'production_promoted':False}
    (audit/'report.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps(result,indent=2))
    if not result['passed']:
        raise SystemExit(1)


if __name__=='__main__':main()
