"""Validate dual depth variation on the ORIGINAL eight smooth wet controls.

Convert each original layer velocity using the existing inverse-response
metric; do not relabel layer velocity as canonical velocity. Depth probes hold
the resulting canonical velocity fixed. No evolved state or corrected force
is produced and earlier wetting/energy failures remain unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_reconstructed_closed_energy import fixture
import total_depth_bank_replay as bank
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_pressure_rates import PressureGeometryRate
from reconstructed_energy_reference import metric,energy
from rational_dual_energy_reference import evaluate
from pressure_cut_endpoint_reference import exact_endpoint_cuts


def make(h,b,dx):
    return ReconstructedPressureGeometry(h,b,dx,periodic=True,
        pressure_trace='integrated_column',bed_quadrature='shared_bottom')


def run(seed,resolution):
    state,bed=fixture(seed,'smooth',resolution);before=state.copy();h=state[...,0]
    u=state[...,1:]/h[...,None];dx=16/resolution;g=make(h,bed,dx)
    fv,cfl=bank.rate(state,bed,dx,second_order=True,periodic=True,shoreline_limiter='unscaled')
    root=np.sqrt(h)[...,None];k,_=metric(g,rational=True)
    v=(k@(root*u).ravel()).reshape(u.shape)/root
    result=evaluate(g,v,tangent=PressureGeometryRate(g,bed,fv[...,0]))
    direction=result['depth_direction'];probes=[]
    for epsilon in (1e-3,1e-4,1e-5):
        values=[]
        for sign in (-1,1):
            later=h+sign*epsilon*fv[...,0]
            values.append(evaluate(make(later,bed,dx),v)['total'])
        measured=(values[1]-values[0])/(2*epsilon)
        probes.append(dict(epsilon=epsilon,measured_depth_direction=measured,
            absolute_error=abs(measured-direction['total']),
            error_if_pole_variation_omitted=abs(measured-direction['mass_normalization']-direction['potential'])))
    if not np.array_equal(state,before):raise AssertionError('Original source fixture changed')
    return dict(seed=seed,resolution=resolution,cfl_s=cfl,
        source_state_sha256=hashlib.sha256(state.tobytes()).hexdigest(),
        source_fv_rate_sha256=hashlib.sha256(fv.tobytes()).hexdigest(),
        canonical_velocity_sha256=hashlib.sha256(v.tobytes()).hexdigest(),
        original_layer_velocity_recovery_max_error=float(abs(result['layer_velocity']-u).max()),
        dual_primal_energy_error=abs(result['total']-energy(g,u,rational=True)),
        direction=direction,probes=probes,
        pressure_residuals=[p['relative_residual'] for p in result['poles']],
        last_probe_within_original_energy_direction_gate=bool(probes[-1]['absolute_error']<1e-7),
        nonlinear_time_evolution_or_gameplay_accepted=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    records=[]
    with exact_endpoint_cuts():
        for seed in range(2200,2208):
            record=run(seed,64);records.append(record);print(json.dumps(record),flush=True)
    report=dict(scope=__doc__,records=records,
        original_failures_superseded=False,native_or_full_history_accepted=False,
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('rational_dual_energy_reference.py','audit_rational_dual_variation.py',
                'reconstructed_energy_reference.py','reconstructed_acceleration_system.py',
                'reconstructed_pressure_rates.py','finite_depth_pressure_reference.py')})
    with args.report.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
