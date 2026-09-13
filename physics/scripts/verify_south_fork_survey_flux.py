"""Audit actual numerical domain-face flux against a tiny conservative step."""
from pathlib import Path
import sys
import json
import subprocess
import runpy
import argparse
import hashlib
from dataclasses import replace

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'physics/src'))
import numpy as np
from raftsim.scenario2_5d import read_scenario2_5d_package
from south_fork_survey_sanity import check_frame


def verified_solver_sha(work, run):
    """An old command path is not proof that its binary is still the same."""
    registration=json.loads((work/'registration.json').read_text())
    executable=Path(run['command'][0])
    if not executable.is_absolute():executable=ROOT/executable
    actual=hashlib.sha256(executable.read_bytes()).hexdigest()
    if actual!=registration['solver_binary_sha256']:
        raise ValueError('Flux audit binary differs from the completed cook')
    return actual


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--label',default='')
    parser.add_argument('--cell', type=float, choices=(0.5, 1.0), default=1.0)
    parser.add_argument('--work', type=Path)
    parser.add_argument('--report', type=Path)
    args=parser.parse_args()
    work=ROOT/f'tmp/south-fork-survey-hydraulics/{args.cell:g}m-mixed-inlet'
    if args.label: work=work.with_name(work.name+'-'+args.label)
    suffix=('' if args.cell == 1.0 else f'-{args.cell:g}m') + ('-'+args.label if args.label else '')
    report_path=ROOT/f'docs/reconstruction-review-2026-09-06/troublemaker_numerical_boundary_flux{suffix}.json'
    if bool(args.work) != bool(args.report):
        raise ValueError('Explicit work and report paths must be provided together')
    if args.work:
        work, report_path = args.work.resolve(), args.report.resolve()
        if not work.is_relative_to(ROOT/'tmp') or not report_path.is_relative_to(ROOT):
            raise ValueError('Explicit audit paths must stay within the project')
    audit=work/'boundary_flux_audit'
    if audit.exists() or report_path.exists():
        raise FileExistsError('Preserve the existing flux audit; do not overwrite its evidence')
    run=json.loads((work/'run_result.json').read_text())
    solver_sha=verified_solver_sha(work,run)
    original=read_scenario2_5d_package(next((work/'scenario').glob('*/scenario.json')))
    folder=ROOT/run['output_dir']
    manifest=json.loads((folder/'manifest.json').read_text())
    source=folder/manifest['frames'][-1]
    validate=runpy.run_path(str(ROOT/'physics/scripts/audit_troublemaker_hydraulic_spinup.py'))['validated_frame_state']
    raw=np.genfromtxt(source,delimiter=',',names=True)
    if not check_frame(raw)['passed']:
        raise ValueError('Flux audit endpoint fails survey sanity bounds')
    state=validate(original,raw)
    audit.mkdir(exist_ok=False)
    scenario=replace(original,fixed_dt=1e-6,duration=1e-6,initial_state=state,
        metadata=replace(original.metadata,scenario_id='survey_final_state_flux_audit'))
    package=audit/'scenario'; scenario.write_package(package)
    command=list(run['command'])
    for key,value in (('--scenario',str(package)),('--output',str(audit/'solver')),('--steps','1'),('--frame-interval','1')):
        command[command.index(key)+1]=value
    inspected=subprocess.run([*command,'--inspect-boundary-flux'],capture_output=True,text=True,check=True)
    flux=json.loads(inspected.stdout)
    subprocess.run(command,capture_output=True,text=True,check=True)
    final=np.genfromtxt(audit/'solver/survey_final_state_flux_audit/frames/frame_0001.csv',delimiter=',',names=True)
    measured=(float(final['h'].sum())-float(state.depth.sum()))*scenario.grid.dx*scenario.grid.dy/scenario.fixed_dt
    target=45.3069545472
    checks={'inflow_matches_target':abs(flux['west']-target)<1e-8,
        'side_boundaries_do_not_leak':abs(flux['north'])+abs(flux['south'])<1e-8,
        'face_flux_matches_volume_derivative':abs(measured-flux['net'])<1e-3}
    report={'status':'numerical_face_flux_audit','checks':checks,'passed':all(checks.values()),
        'numerical_boundary_fluxes_m3s':flux,'measured_volume_derivative_m3s':measured,
        'instantaneous_outflow_within_2_percent_of_target':abs(-flux['east']-target)<.02*target,
        'scope':'Conservation check, not steady-flow acceptance. Instantaneous outflow may differ while storage changes; mean-flow settling is reported separately.',
        'source_geometry_sha256':original.metadata.provenance['geometry_sha256'],
        'source_bed_sampling':original.metadata.provenance.get('bed_sampling','bilinear'),
        'source_frame':source.relative_to(ROOT).as_posix(),
        'source_frame_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'source_solver_binary_sha256':solver_sha,'production_promoted':False}
    with report_path.open('x',encoding='utf-8') as output:
        json.dump(report,output,indent=2,allow_nan=False)
    print(json.dumps(report,indent=2))
    if not report['passed']: raise SystemExit(1)


if __name__=='__main__':main()
