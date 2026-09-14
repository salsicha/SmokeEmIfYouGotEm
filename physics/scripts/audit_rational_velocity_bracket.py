"""All eight original smooth states in the proposed closed variational stage.

Original layer velocity is converted, not reinterpreted, as canonical velocity.
The NEW transport direction is reported distinctly from original FV; no history
is resumed from it and no existing failed assertion is replaced.
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
from rational_velocity_bracket_reference import stage
import total_depth_bank_replay as bank
from pressure_cut_endpoint_reference import exact_endpoint_cuts


def make(h,b,dx):
    return ReconstructedPressureGeometry(h,b,dx,periodic=True,
        pressure_trace='integrated_column',bed_quadrature='shared_bottom')


def run(seed):
    state,b=fixture(seed,'smooth',64);h=state[...,0];u=state[...,1:]/h[...,None];dx=.25
    g=make(h,b,dx);k,_=metric(g,rational=True);root=np.sqrt(h)[...,None]
    v=(k@(root*u).ravel()).reshape(u.shape)/root
    started=perf_counter();result=stage(g,v);elapsed=perf_counter()-started
    fv,_=bank.rate(state,b,dx,second_order=True,periodic=True,shoreline_limiter='unscaled')
    probes=[]
    for eps in (1e-3,1e-4,1e-5):
        values=[]
        for sign in (-1,1):
            hh=h+sign*eps*result['depth_rate'];vv=v+sign*eps*result['canonical_velocity_rate']
            values.append(evaluate(make(hh,b,dx),vv)['total'])
        measured=(values[1]-values[0])/(2*eps)
        probes.append(dict(epsilon=eps,energy_direction=measured,
            error=abs(measured-result['energy_rate'])))
    return dict(seed=seed,source_state_sha256=hashlib.sha256(state.tobytes()).hexdigest(),
        energy_rate=result['energy_rate'],net_mass_rate=result['net_mass_rate'],
        branch_chain_rule_error=result['branch_chain_rule_error'],rotational_work=result['rotational_work'],
        layer_velocity_recovery_error=float(abs(result['layer_velocity']-u).max()),
        maximum_mass_rate_difference_from_original_FV=float(abs(result['depth_rate']-fv[...,0]).max()),
        stage_wall_seconds_shared_load=elapsed,probes=probes,
        original_energy_direction_gate_passed=bool(probes[-1]['error']<1e-7),
        pressure_residuals=result['pressure_residuals'],
        original_fv_transport_preserved=False,full_evolution_or_gameplay_accepted=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    records=[]
    with exact_endpoint_cuts():
        for seed in range(2200,2208):
            record=run(seed);records.append(record);print(json.dumps(record),flush=True)
    result=dict(scope=__doc__,records=records,original_failures_superseded=False,
        original_fv_or_wetting_or_breaking_or_gameplay_accepted=False,
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('audit_rational_velocity_bracket.py','rational_velocity_bracket_reference.py',
                'rational_dual_energy_reference.py','reconstructed_pressure_rates.py',
                'reconstructed_pressure_geometry.py','reconstructed_energy_reference.py')})
    with args.report.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
