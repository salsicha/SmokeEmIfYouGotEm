"""Verify a positive nonlinear rational-metric rate independently in state space.

This is a counterexample to assuming the inverse frozen linear-response metric
is automatically a nonlinear invariant, NOT proof that no other energy exists.
Finite differences use the actual full FV plus two-pole momentum direction.
No evolution, source modification, energy projection or gate relaxation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import total_depth_bank_replay as bank
from audit_reconstructed_closed_energy import fixture
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_pressure_rates import PressureGeometryRate
from reconstructed_nonlinear_pressure import nonlinear_pressure
from reconstructed_energy_reference import energy,energy_rate
from difference_scalar_gradient_reference import difference_scalar_gradients
from pressure_cut_endpoint_reference import exact_endpoint_cuts


def make(h,bed,dx):
    return ReconstructedPressureGeometry(h,bed,dx,periodic=True,
        pressure_trace='integrated_column',bed_quadrature='shared_bottom')


def check(seed,resolution):
    state,bed=fixture(seed,'smooth',resolution);dx=16/resolution
    h=state[...,0];u=state[...,1:]/h[...,None];g=make(h,bed,dx)
    fv,cfl=bank.rate(state,bed,dx,second_order=True,periodic=True,shoreline_limiter='unscaled')
    tangent=PressureGeometryRate(g,bed,fv[...,0])
    with difference_scalar_gradients():
        force,details=nonlinear_pressure(g,u,fv[...,0],fv[...,1:],rational=True,preconditioner='block')
    rate=fv.copy();rate[...,1:]+=force
    predicted=energy_rate(g,tangent,u,rate[...,1:],rational=True)
    differences=[]
    for epsilon in (1e-3,1e-4,1e-5):
        values=[]
        for sign in (-1,1):
            later=state+sign*epsilon*rate;hh=later[...,0]
            if np.any(hh<=0):raise ValueError('Directional check leaves positive support')
            values.append(energy(make(hh,bed,dx),later[...,1:]/hh[...,None],rational=True))
        measured=(values[1]-values[0])/(2*epsilon)
        differences.append(dict(epsilon=epsilon,finite_difference_rate=measured,
            absolute_error=abs(measured-predicted['total'])))
    return dict(seed=seed,resolution=resolution,cell_m=dx,cfl_s=cfl,
        scalar='difference_scalar',model='rational_sgn',predicted=predicted,
        per_unit_transverse_width=predicted['total']/dx,finite_differences=differences,
        input_state_sha256=hashlib.sha256(state.tobytes()).hexdigest(),
        full_rate_sha256=hashlib.sha256(rate.tobytes()).hexdigest(),
        pressure_residuals=[p['relative_residual'] for p in details['poles']],
        positive_rate_independently_verified=predicted['total']>1e-8 and all(v['finite_difference_rate']>0 for v in differences)
            and differences[-1]['absolute_error']<1e-7,
        nonlinear_energy_qualified=False,gameplay_accepted=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    results=[]
    with exact_endpoint_cuts():
        for seed in (2204,2205):
            result=check(seed,64);results.append(result);print(json.dumps(result),flush=True)
    report=dict(cases=results,scope=__doc__,implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ('audit_rational_energy_direction.py','reconstructed_energy_reference.py','audit_reconstructed_closed_energy.py')})
    with args.report.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
