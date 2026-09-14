"""Compare EP and continuous-envelope mass transport at ALL recorded crossings.

Replays the original EP-coupled 16-step trajectories unchanged. Only compares
mass operators on their states; it does NOT evolve the new transport or fix
the independently confirmed pressure-gradient discontinuities.
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
from extremum_preserving_transport import ExtremumPreservingTransport
from continuous_extremum_transport import ContinuousExtremumTransport
from pressure_cut_endpoint_reference import exact_endpoint_cuts


def run(reference):
    seed=reference['seed'];state,b=fixture(seed,'smooth',64);h=state[...,0];u=state[...,1:]/h[...,None];dx=.25;dt=.0005
    assert hashlib.sha256(state.tobytes()).hexdigest()==reference['source_state_sha256']
    k,_=metric(make(h,b,dx),rational=True);root=np.sqrt(h)[...,None]
    v=(k@(root*u).ravel()).reshape(u.shape)/root;events=[]
    for index in range(16):
        hh,vv,_=rk2_step(h,b,v,dx,dt)
        for event in reference['events']:
            step=round((event['interpolated_time']-event['fraction']*dt)/dt)
            if step!=index:continue
            probes=[]
            for original in event['probes']:
                eps=original['relative_epsilon'];old=[];new=[]
                for sign in (-1,1):
                    fraction=event['fraction']+sign*eps
                    ph=h+fraction*(hh-h);pv=v+fraction*(vv-v)
                    layer=evaluate(make(ph,b,dx),pv)['layer_velocity']
                    old.append(ExtremumPreservingTransport(ph,b,layer,dx,periodic=True))
                    new.append(ContinuousExtremumTransport(ph,b,layer,dx,periodic=True))
                old_gap=float(abs(old[1].mass_rate-old[0].mass_rate).max())
                if abs(old_gap-original['mass_rate_jump'])>1e-12:
                    raise AssertionError('Original EP crossing states/actions changed')
                probes.append(dict(relative_epsilon=eps,original_mass_rate_jump=old_gap,
                    continuous_mass_rate_jump=float(abs(new[1].mass_rate-new[0].mass_rate).max()),
                    continuous_retained_face_jump=max(float(abs(c['retained']-a['retained']).max())
                        for a,c in zip(new[0].faces,new[1].faces))))
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
        records=records,new_transport_time_evolution_or_pressure_or_gameplay_accepted=False,
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('audit_continuous_transport_crossings.py','continuous_extremum_transport.py',
                'extremum_preserving_transport.py','positive_rational_velocity_stage.py')})
    with args.report.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
