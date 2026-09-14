"""Original closed energy fixtures with the connected scalar proposal.

The rational inverse-response metric is an unproven nonlinear extension.
Positive rates reject assuming it an invariant; they do not prove that no
other energy exists. No dissipation, projection, solver or gate changes.
"""
import argparse
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_reconstructed_closed_energy import fixture
import total_depth_bank_replay as bank
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_pressure_rates import PressureGeometryRate
from reconstructed_nonlinear_pressure import nonlinear_pressure
from reconstructed_energy_reference import energy_rate
from periodic_connected_scalar_reference import periodic_connected_gradients
from pressure_cut_endpoint_reference import exact_endpoint_cuts


def run(seed,resolution):
    state,bed=fixture(seed,'smooth',resolution)
    h=state[...,0];u=state[...,1:]/h[...,None];dx=16./resolution
    fv,cfl=bank.rate(state,bed,dx,second_order=True,periodic=True,shoreline_limiter='unscaled')
    g=ReconstructedPressureGeometry(h,bed,dx,periodic=True,
        pressure_trace='integrated_column',bed_quadrature='shared_bottom')
    tangent=PressureGeometryRate(g,bed,fv[...,0]);cases=[]
    for rational in (False,True):
        for connected in (False,True):
            with periodic_connected_gradients() if connected else nullcontext():
                pressure,details=nonlinear_pressure(g,u,fv[...,0],fv[...,1:],rational=rational,preconditioner='block')
            full=fv.copy();full[...,1:]+=pressure
            erate=energy_rate(g,tangent,u,full[...,1:],rational=rational)
            cases.append(dict(model='rational_sgn' if rational else 'sgn',connected=connected,
                energy_rate=erate,rate_per_unit_width=erate['total']/dx,
                pressure_residuals=[p['relative_residual'] for p in details['poles']],
                pressure_gate_passed=all(p['relative_residual']<2e-5 for p in details['poles']),
                actual_state_rate_sha256=hashlib.sha256(full.tobytes()).hexdigest()))
    return dict(seed=seed,resolution=resolution,cfl_s=cfl,
        state_sha256=hashlib.sha256(state.tobytes()).hexdigest(),cases=cases)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--resolution',type=int,choices=(16,32,64,128),required=True)
    args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    records=[]
    with exact_endpoint_cuts():
        for seed in range(2200,2208):
            record=run(seed,args.resolution);records.append(record)
            print(json.dumps(dict(seed=seed,cases=[dict(model=c['model'],connected=c['connected'],
                rate_per_unit_width=c['rate_per_unit_width']) for c in record['cases']])),flush=True)
    result=dict(scope=__doc__,records=records,
        pressure_gates_passed=all(c['pressure_gate_passed'] for r in records for c in r['cases']),
        nonlinear_energy_or_history_or_gameplay_accepted=False,
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('audit_connected_closed_energy.py','periodic_connected_scalar_reference.py',
                'connected_depth_weighted_scalar_gradient.py','depth_weighted_scalar_gradient.py',
                'audit_reconstructed_closed_energy.py','reconstructed_energy_reference.py')})
    with args.report.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
