"""Short actual evolution of all original 64-cell smooth profiles.

Same source states/canonical conversion, no reset/projection/clamp. Three fixed
time resolutions to 0.008 s are a new diagnostic, not the requested 9-second
moving-source history or a qualification of wetting, shocks or gameplay.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_reconstructed_closed_energy import fixture
from audit_reverse_rational_stage import make
from reconstructed_energy_reference import metric
from rational_dual_energy_reference import evaluate
from positive_rational_velocity_stage import rk2_step
from pressure_cut_endpoint_reference import exact_endpoint_cuts


def run(seed):
    state,b=fixture(seed,'smooth',64);h=state[...,0];u=state[...,1:]/h[...,None];dx=.25
    k,_=metric(make(h,b,dx),rational=True);root=np.sqrt(h)[...,None]
    v=(k@(root*u).ravel()).reshape(u.shape)/root
    initial=evaluate(make(h,b,dx),v)['total'];runs=[];endpoints=[]
    for steps in (4,8,16):
        dt=.008/steps;hh=h.copy();vv=v.copy();records=[]
        for index in range(steps):
            hh,vv,detail=rk2_step(hh,b,vv,dx,dt);records.append(detail)
        final=evaluate(make(hh,b,dx),vv)['total'];endpoints.append((hh,vv))
        runs.append(dict(steps=steps,dt=dt,elapsed_seconds=steps*dt,
            minimum_depth=float(hh.min()),mass_change=float(np.sum(hh-h))*dx**2,
            initial_energy=initial,final_energy=final,energy_change=final-initial,
            maximum_stage_energy_rate=max(r['maximum_stage_energy_rate'] for r in records),
            maximum_stage_chain_rule_error=max(r['maximum_stage_chain_rule_error'] for r in records),
            maximum_pressure_residual=max(r['maximum_pressure_residual'] for r in records),
            endpoint_sha256=hashlib.sha256(hh.tobytes()+vv.tobytes()).hexdigest()))
        print(json.dumps(dict(event='evolution_resolution',seed=seed,**runs[-1])),flush=True)
    changes=[]
    for a,c in zip(endpoints,endpoints[1:]):
        changes.append(dict(depth_l1=float(np.mean(abs(a[0]-c[0]))),
            canonical_velocity_l1=float(np.mean(abs(a[1]-c[1])))))
    return dict(seed=seed,source_state_sha256=hashlib.sha256(state.tobytes()).hexdigest(),runs=runs,
        consecutive_endpoint_differences=changes,
        temporal_ratios={key:changes[0][key]/changes[1][key] for key in changes[0]},
        full_history_or_wetting_or_gameplay_accepted=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    records=[]
    with exact_endpoint_cuts():
        for seed in range(2200,2208):records.append(run(seed))
    report=dict(scope=__doc__,records=records,
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('audit_positive_rational_evolution.py','positive_rational_velocity_stage.py',
                'extremum_preserving_transport.py','hydrostatic_energy_transport.py')})
    with args.report.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
