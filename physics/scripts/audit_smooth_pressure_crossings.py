"""Smooth-stage continuity on every ORIGINAL recorded crossing segment.

Preserves original EP-coupled trajectories and their canonical probe states.
The candidate is evaluated at those canonical states; its recovered layer
velocity may differ because its pressure metric differs. This diagnostic is
not a new physical-source trajectory or a gameplay qualification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_reconstructed_closed_energy import fixture
from audit_reverse_rational_stage import make as old_make
from reconstructed_energy_reference import metric
from positive_rational_velocity_stage import rk2_step as old_step
from smooth_rational_velocity_stage import make,stage
from smooth_pressure_geometry import SmoothPressureGeometryRate
from rational_dual_energy_reference import evaluate
from pressure_cut_endpoint_reference import exact_endpoint_cuts


def run(reference):
    seed=reference['seed'];state,b=fixture(seed,'smooth',64);h=state[...,0];u=state[...,1:]/h[...,None];dx=.25;dt=.0005
    assert hashlib.sha256(state.tobytes()).hexdigest()==reference['source_state_sha256']
    k,_=metric(old_make(h,b,dx),rational=True);root=np.sqrt(h)[...,None]
    v=(k@(root*u).ravel()).reshape(u.shape)/root;events=[]
    for index in range(16):
        hh,vv,_=old_step(h,b,v,dx,dt)
        for event in reference['events']:
            step=round((event['interpolated_time']-event['fraction']*dt)/dt)
            if step!=index:continue
            probes=[]
            for original in event['probes']:
                eps=original['relative_epsilon'];values=[];states=[]
                for sign in (-1,1):
                    fraction=event['fraction']+sign*eps
                    ph=h+fraction*(hh-h);pv=v+fraction*(vv-v);g=make(ph,b,dx)
                    states.append((g,pv));values.append(stage(g,pv))
                left,right=values;extra={}
                if eps==1e-5:
                    at=np.unravel_index(np.argmax(abs(right['depth_energy_gradient']-left['depth_energy_gradient'])),h.shape)
                    direction=np.zeros_like(h);direction[at]=1.;independent=[]
                    for g,pv in states:
                        independent.append(evaluate(g,pv,tangent=SmoothPressureGeometryRate(g,b,direction))['depth_direction']['total']/dx**2)
                    extra['maximum_independent_gradient_error']=max(abs(independent[j]-values[j]['depth_energy_gradient'][at]) for j in (0,1))
                probes.append(dict(relative_epsilon=eps,
                    original_canonical_rate_jump=original['canonical_rate_jump'],
                    depth_energy_gradient_jump=float(abs(right['depth_energy_gradient']-left['depth_energy_gradient']).max()),
                    canonical_rate_jump=float(abs(right['canonical_velocity_rate']-left['canonical_velocity_rate']).max()),
                    mass_rate_jump=float(abs(right['depth_rate']-left['depth_rate']).max()),
                    maximum_chain_rule_error=max(left['branch_chain_rule_error'],right['branch_chain_rule_error']),**extra))
            result=dict(point=event['point'],kind=event['kind'],interpolated_time=event['interpolated_time'],probes=probes)
            events.append(result);print(json.dumps(dict(seed=seed,**result)),flush=True)
        h,v=hh,vv
    endpoint=hashlib.sha256(h.tobytes()+v.tobytes()).hexdigest()
    if endpoint!=reference['endpoint_sha256']:raise AssertionError('Original trajectory endpoint changed')
    return dict(seed=seed,source_state_sha256=reference['source_state_sha256'],endpoint_sha256=endpoint,
        events=events,original_endpoint_preserved=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trace',type=Path,required=True);parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    reference=json.loads(args.trace.read_text());records=[]
    with exact_endpoint_cuts():
        for r in reference['records']:records.append(run(r))
    report=dict(scope=__doc__,reference_trace_sha256=hashlib.sha256(args.trace.read_bytes()).hexdigest(),
        records=records,physical_velocity_preserved_in_candidate_probes=False,
        full_history_or_dry_pressure_or_gameplay_accepted=False,
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('audit_smooth_pressure_crossings.py','smooth_pressure_geometry.py',
                'smooth_pressure_reverse.py','smooth_rational_velocity_stage.py','reverse_rational_depth_gradient.py')})
    with args.report.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
