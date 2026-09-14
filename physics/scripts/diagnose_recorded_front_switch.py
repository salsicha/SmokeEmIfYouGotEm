"""Inspect candidate front decisions on two nearby evolved states, without edits."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import audit_live_temporal_evolution as temporal
from audit_recorded_stages import read_records
from breaking_front_reference import dispersion_fraction


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path); parser.add_argument('states', type=Path)
    parser.add_argument('--interval', type=int, required=True); parser.add_argument('--trial', type=int, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    metadata = json.loads(args.trace.read_text()); source_bytes = Path(metadata['source']).read_bytes()
    source = json.loads(source_bytes)
    if not metadata.get('completed') or not metadata.get('final_state_exact_to_live'):
        raise ValueError('Unqualified recorded trace')
    if not 0 <= args.interval < len(source['observations'])-1 or args.trial < 0:
        raise ValueError('Invalid recorded trial index')
    trial, stages, *_ = next(r for r in read_records(metadata, Path(metadata['binary']).read_bytes())
                             if r[0]['interval']==args.interval and r[0]['trial']==args.trial)
    a,b = temporal.observations(dict(schema='raftsim.live_temporal_boundary_inputs.v1',
        first=source['observations'][args.interval],second=source['observations'][args.interval+1]))
    _, boundary = temporal.boundary_provider(a,b)
    es,eb,trace = boundary(trial['begin']-a['native_seconds'],None)
    cases = []
    with np.load(args.states, allow_pickle=False) as archive:
        if archive['source_sha256'].item() != hashlib.sha256(source_bytes).hexdigest():
            raise ValueError('States belong to another live source')
        cpu = archive[str(args.trial)+'_input']
    for name,state in [('gpu',stages[0]['state'][...,:3].astype(float)),('cpu',cpu)]:
        captured = {}; original = temporal.bank.nonlinear_pressure_force
        def capture(*values, **kwargs):
            captured['pairs'] = [v.copy() for v in values[4]]
            return np.zeros_like(values[2]), []
        try:
            temporal.bank.nonlinear_pressure_force = capture
            rate,_ = temporal.bank.rate(state,a['bed'],a['cell_meters'],exterior=(es,eb),
                pressure_boundary=trace,breaking_model='hybrid_front',**temporal.KW)
        finally: temporal.bank.nonlinear_pressure_force = original
        fronts = []
        fraction,stats = dispersion_fraction(state[...,0],a['bed'],rate[...,0],captured['pairs'],
                                             a['cell_meters'],on_front=fronts.append)
        cases.append(dict(name=name,fronts=fronts,stats=stats,fraction=fraction))
    error=abs(cases[0]['fraction']-cases[1]['fraction']); cells=np.argwhere(error>.5)
    rows = {1:set(map(int,cells[:,0])),0:set(map(int,cells[:,1]))}
    for case in cases:
        case.pop('fraction')
        case['fronts']=[f for f in case['fronts'] if f['row'] in rows[f['axis']]]
    report=dict(trial=trial,maximum_fraction_error=float(error.max()),switched_cells=cells.tolist(),cases=cases)
    with args.report.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)
    print(json.dumps(report,indent=2,allow_nan=False))


if __name__=='__main__':main()
