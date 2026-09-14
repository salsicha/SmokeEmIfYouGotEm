"""Original smooth profiles and energy probes with new EP transport.

No new acceptance threshold, source reset or gameplay promotion. Includes
original 32/64/128 mass-refinement probes using their unchanged test function.
"""
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter
import numpy as np
from audit_reconstructed_closed_energy import fixture
from audit_reverse_rational_stage import make
from reconstructed_energy_reference import metric
from rational_dual_energy_reference import evaluate
from positive_rational_velocity_stage import stage
from pressure_cut_endpoint_reference import exact_endpoint_cuts
from extremum_preserving_transport import ExtremumPreservingTransport


def run(seed,n):
    state,b=fixture(seed,'smooth',n);h=state[...,0];u=state[...,1:]/h[...,None];dx=16/n
    g=make(h,b,dx);k,_=metric(g,rational=True);root=np.sqrt(h)[...,None]
    v=(k@(root*u).ravel()).reshape(u.shape)/root
    start=perf_counter();r=stage(g,v);seconds=perf_counter()-start
    probes=[]
    for eps in (1e-3,1e-4,1e-5):
        values=[]
        for sign in (-1,1):
            hh=h+sign*eps*r['depth_rate'];vv=v+sign*eps*r['canonical_velocity_rate']
            values.append(evaluate(make(hh,b,dx),vv)['total'])
        measured=(values[1]-values[0])/(2*eps)
        probes.append(dict(epsilon=eps,energy_direction=measured,error=abs(measured-r['energy_rate'])))
    return dict(seed=seed,resolution=n,source_state_sha256=hashlib.sha256(state.tobytes()).hexdigest(),
        energy_rate=r['energy_rate'],net_mass_rate=r['net_mass_rate'],
        branch_chain_rule_error=r['branch_chain_rule_error'],pressure_residuals=r['pressure_residuals'],
        probes=probes,original_energy_direction_gate_passed=bool(probes[-1]['error']<1e-7),
        mass_only_forward_euler_bound=r['mass_only_forward_euler_bound'],
        layer_velocity_recovery_error=float(abs(u-r['layer_velocity']).max()),
        stage_seconds_shared_load=seconds)


def refinement():
    errors=[]
    for n in (32,64,128):
        dx=2*np.pi/n;x=(np.arange(n)+.5)*dx
        h=(1+.2*np.sin(x+.31))[None];b=.1*np.cos(x+.13)[None]
        u=np.zeros((*h.shape,2));u[...,0]=1+.1*np.cos(x+.47)
        expected=-(.2*np.cos(x+.31)*(1+.1*np.cos(x+.47))-.1*h[0]*np.sin(x+.47))
        r=ExtremumPreservingTransport(h,b,u,dx,periodic=True)
        errors.append(float(np.mean(abs(r.mass_rate[0]-expected))))
    ratios=[a/b for a,b in zip(errors,errors[1:])]
    return dict(errors=errors,ratios=ratios,original_gate_passed=bool(min(ratios)>3.2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    records=[]
    with exact_endpoint_cuts():
        for n in (64,128):
            for seed in range(2200,2208):
                r=run(seed,n);records.append(r);print(json.dumps(r),flush=True)
    report=dict(scope=__doc__,records=records,refinement=refinement(),
        full_evolution_or_dry_pressure_or_native_or_gameplay_accepted=False,
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('audit_positive_rational_stage.py','positive_rational_velocity_stage.py',
                'extremum_preserving_transport.py','hydrostatic_energy_transport.py',
                'reverse_rational_depth_gradient.py','rational_dual_energy_reference.py')})
    with args.report.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)
    print(json.dumps({'refinement':report['refinement']}),flush=True)


if __name__=='__main__':main()
