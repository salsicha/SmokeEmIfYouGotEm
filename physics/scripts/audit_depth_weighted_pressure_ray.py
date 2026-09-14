"""Compare original and proposed scalar coupling on the unchanged physical ray.

Both original pressure poles, state/rates, bed, trace and residual gates remain.
The original Q/C test and the new coarse-grid refinement failure are not waived.
No native integration or full-history/energy qualification is claimed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_source_boundary_pressure_ray import ray
from pressure_cut_endpoint_reference import exact_endpoint_cuts
from depth_weighted_scalar_gradient import depth_weighted_forcing,DepthWeightedScalarGradient


def convergence():
    results=[]
    for n in (16,32,64,128,256):
        dx=1/n
        y,x=np.meshgrid((np.arange(n+6)-2.5)*dx,(np.arange(n+6)-2.5)*dx,indexing='ij')
        h=np.where(x<.25,0.,1.+x);g=DepthWeightedScalarGradient(h,dx)
        actual=g.gradient(np.sin(2*x)+np.cos(y))
        exact=np.stack((2*np.cos(2*x),-np.sin(y)),axis=-1)
        core=(x>=.25)&(x<=1)&(y>=0)&(y<=1)
        error=float(abs(actual[core]-exact[core]).max())
        results.append(dict(n=n,maximum_error=error,previous_ratio=None if not results else results[-1]['maximum_error']/error,
            rank_two_core=all(np.all(rank[core]==2) for rank in g.ranks)))
    return results


def main():
    global depth_weighted_forcing, DepthWeightedScalarGradient
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--connected', action='store_true');args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    if args.connected:
        from connected_depth_weighted_scalar_gradient import connected_depth_weighted_forcing, ConnectedDepthWeightedScalarGradient
        depth_weighted_forcing=connected_depth_weighted_forcing
        DepthWeightedScalarGradient=ConnectedDepthWeightedScalarGradient
    original=[];candidate=[]
    with exact_endpoint_cuts():
        for flat in (True,False):
            result=ray(flat);original.append(result);print(json.dumps(dict(kind='original',result=result)),flush=True)
        with depth_weighted_forcing():
            for flat in (True,False):
                result=ray(flat);candidate.append(result);print(json.dumps(dict(kind='candidate',result=result)),flush=True)
    tests=convergence();print(json.dumps(dict(convergence=tests)),flush=True)
    names=['depth_weighted_scalar_gradient.py','connected_depth_weighted_scalar_gradient.py','source_supported_scalar_boundary.py','source_supported_pressure_reference.py',
        'reconstructed_nonlinear_pressure.py','reconstructed_pressure_geometry.py','reconstructed_pressure_rates.py',
        'audit_source_boundary_pressure_ray.py','pressure_cut_endpoint_reference.py']
    result=dict(scope=__doc__,original=original,candidate=candidate,convergence=tests,connected=args.connected,
        original_tests_replaced=False,coarse_16_to_32_ratio_passed=tests[1]['previous_ratio']>3.5,
        full_history_energy_or_playable_accepted=False,
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in names})
    with args.report.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
