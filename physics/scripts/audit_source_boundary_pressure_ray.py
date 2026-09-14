"""Physical two-pole force on the retained failed variable-bed scalar ray.

Keep the old raw Q/C failure visible. Evaluate pressure and conserved momentum
forcing, whose vanishing depth weights differ from unweighted scalar traces.
No depth/bed changes, epsilon replacement of the dry state, or new solve gates.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from reconstructed_pressure_geometry import ReconstructedPressureGeometry as Geometry
from source_supported_pressure_reference import solve
from pressure_cut_endpoint_reference import exact_endpoint_cuts


def make(h,bed,dx):
    return Geometry(h,bed,dx,pressure_trace='integrated_column',bed_quadrature='shared_bottom')


def ray(flat):
    n=5;dx=1/n
    y,x=np.meshgrid((np.arange(n+6)-2.5)*dx,(np.arange(n+6)-2.5)*dx,indexing='ij')
    h=np.where(x<.25,0.,1.);bed=np.zeros_like(x) if flat else .125*np.maximum(x,0)+.0625*y
    state=np.stack((h,h*(.2+x),h*(.3+y)),axis=-1)
    rate=np.zeros_like(state);rate[...,0]=.125;rate[...,1]=.0625;rate[...,2]=-.03125
    core=(slice(3,-3),slice(3,-3));trace=np.zeros((4*n,2))
    force,detail=solve(make(h[core],bed[core],dx),state[core],state,bed,rate,trace)
    dry=h[core]==0
    if np.any(force[dry]!=0):raise AssertionError('Physical dry force is not exactly zero')
    cases=[]
    for eps in (2.**-8,2.**-16,2.**-24,2.**-48,2.**-64):
        later=state+eps*rate
        actual,details=solve(make(later[core][...,0],bed[core],dx),later[core],later,bed,rate,trace)
        delta=actual-force
        index=np.unravel_index(np.argmax(abs(delta)),delta.shape)
        cases.append(dict(epsilon=eps,maximum_force_error=float(abs(delta).max()),
            maximum_originally_wet_force_error=float(abs(delta[~dry]).max()),
            maximum_originally_dry_force=float(abs(actual[dry]).max()),
            largest_error_index=list(map(int,index)),pressure_residuals=[p['relative_residual'] for p in details['poles']],
            force_sha256=hashlib.sha256(actual.tobytes()).hexdigest()))
    return dict(flat=flat,limit_force_sha256=hashlib.sha256(force.tobytes()).hexdigest(),
        limit_pressure_residuals=[p['relative_residual'] for p in detail['poles']],
        limit_dry_force_exactly_zero=True,cases=cases,
        original_2pow_minus24_physical_force_within_1e_minus6=cases[2]['maximum_force_error']<1e-6,
        raw_scalar_failure_superseded=False,full_history_or_energy_or_gameplay_accepted=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    cases=[]
    with exact_endpoint_cuts():
        for flat in (True,False):
            case=ray(flat);cases.append(case);print(json.dumps(case),flush=True)
    result=dict(cases=cases,scope=__doc__,implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ('source_supported_pressure_reference.py','source_supported_scalar_boundary.py','audit_source_boundary_pressure_ray.py',
                     'reconstructed_nonlinear_pressure.py')})
    with args.report.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
