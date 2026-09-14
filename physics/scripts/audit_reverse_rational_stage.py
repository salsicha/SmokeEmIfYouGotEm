"""Paired old-basis/reverse research stages on all original smooth profiles.

Alternating call order, same original state, canonical conversion and pressure
gates. This is CPU research timing under shared load, never desktop FPS or
native budget acceptance. Both implementations change original FV transport.
"""
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter
import numpy as np
from audit_reconstructed_closed_energy import fixture
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_energy_reference import metric
from rational_dual_energy_reference import evaluate
from rational_velocity_bracket_reference import stage as basis_stage
from reverse_rational_velocity_stage import stage as reverse_stage
from pressure_cut_endpoint_reference import exact_endpoint_cuts


def make(h,b,dx):
    return ReconstructedPressureGeometry(h,b,dx,periodic=True,
        pressure_trace='integrated_column',bed_quadrature='shared_bottom')


def run(seed,resolution):
    state,b=fixture(seed,'smooth',resolution);h=state[...,0];u=state[...,1:]/h[...,None];dx=16/resolution
    g=make(h,b,dx);k,_=metric(g,rational=True);root=np.sqrt(h)[...,None]
    v=(k@(root*u).ravel()).reshape(u.shape)/root
    order=['basis','reverse'] if seed%2==0 else ['reverse','basis']
    if resolution>64:order=['reverse']
    results={};timings={}
    for name in order:
        started=perf_counter();results[name]=(basis_stage if name=='basis' else reverse_stage)(g,v)
        timings[name]=perf_counter()-started
    result=results['reverse'];differences={}
    if 'basis' in results:
        for key in ('depth_energy_gradient','depth_rate','canonical_velocity_rate','layer_velocity','flux'):
            error=float(abs(result[key]-results['basis'][key]).max());differences[key]=error
            if error>3e-12:raise AssertionError('Reverse differs from basis field: '+key)
    probes=[]
    for eps in (1e-3,1e-4,1e-5):
        values=[]
        for sign in (-1,1):
            hh=h+sign*eps*result['depth_rate'];vv=v+sign*eps*result['canonical_velocity_rate']
            values.append(evaluate(make(hh,b,dx),vv)['total'])
        measured=(values[1]-values[0])/(2*eps)
        probes.append(dict(epsilon=eps,energy_direction=measured,error=abs(measured-result['energy_rate'])))
    return dict(seed=seed,resolution=resolution,source_state_sha256=hashlib.sha256(state.tobytes()).hexdigest(),
        call_order=order,stage_seconds_shared_load=timings,basis_field_maximum_errors=differences,
        energy_rate=result['energy_rate'],net_mass_rate=result['net_mass_rate'],
        branch_chain_rule_error=result['branch_chain_rule_error'],reverse=result['reverse'],
        probes=probes,original_energy_direction_gate_passed=bool(probes[-1]['error']<1e-7),
        pressure_residuals=result['pressure_residuals'],original_fv_transport_preserved=False,
        full_evolution_or_gameplay_accepted=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--resolution',type=int,choices=(64,128),default=64);args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    records=[]
    with exact_endpoint_cuts():
        for seed in range(2200,2208):
            record=run(seed,args.resolution);records.append(record);print(json.dumps(record),flush=True)
    report=dict(scope=__doc__,records=records,original_failures_superseded=False,
        native_or_FPS_or_full_history_accepted=False,
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('audit_reverse_rational_stage.py','reverse_rational_depth_gradient.py',
                'reverse_rational_velocity_stage.py','rational_velocity_bracket_reference.py',
                'rational_dual_energy_reference.py','reconstructed_pressure_rates.py')})
    with args.report.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
