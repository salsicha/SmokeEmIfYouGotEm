"""Same original sixteen physical states: equivalent positive primal metric.

No new time trajectory or source conversion is accepted. The exact original
physical momentum is the input; mass direction uses its original velocity.
Dense original K, original dual Legendre gradient, and finite differences are
independent controls. Local positive energy does not prove conserved fluxes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from audit_reconstructed_closed_energy import fixture
from reconstructed_energy_reference import metric
from rational_dual_energy_reference import evaluate as dual
from reverse_rational_depth_gradient import depth_gradient as dual_gradient
from smooth_pressure_geometry import SmoothPressureGeometryRate
from smooth_pressure_reverse import smooth_coefficient_reverse
from smooth_rational_velocity_stage import make
from continuous_extremum_transport import ContinuousExtremumTransport
from rational_primal_energy import evaluate,depth_gradient,K0,BETAS,ALPHAS,ZERO_RESPONSE_EXACT


def run(seed,n):
    source,bed=fixture(seed,'smooth',n);h=source[...,0];p=source[...,1:];u=p/h[...,None];dx=16/n
    g=make(h,bed,dx);ht=ContinuousExtremumTransport(h,bed,u,dx,periodic=True).mass_rate
    tangent=SmoothPressureGeometryRate(g,bed,ht)
    start=time.perf_counter();k,_=metric(g,rational=True);dense_seconds=time.perf_counter()-start
    root=np.sqrt(h)[...,None];q=p/root;v_dense=(k@q.ravel()).reshape(p.shape)/root
    start=time.perf_counter();r=evaluate(g,p,tangent=tangent);primal_seconds=time.perf_counter()-start
    a,_=depth_gradient(g,p,r,ht)
    old=dual(g,v_dense,preconditioner='patch');old_a,_=dual_gradient(g,v_dense,old,ht,reverse_coefficients=smooth_coefficient_reverse)
    legendre=2*9.81*(h+bed)-old_a
    dense_energy=(.5*q.ravel()@k@q.ravel()+np.sum(9.81*h*(.5*h+bed)))*dx**2
    recovered=dual(g,r['canonical_velocity'],preconditioner='patch')['canonical_gradient_flux']
    probes=[]
    for eps in (1e-3,1e-4,1e-5):
        values=[evaluate(make(h+sign*eps*ht,bed,dx),p)['total'] for sign in (-1,1)]
        derivative=(values[1]-values[0])/(2*eps)
        probes.append(dict(epsilon=eps,fixed_physical_momentum_energy_direction=derivative,
            error=abs(derivative-r['depth_direction']['total'])))
    chain=abs(np.sum(a*ht)*dx**2-r['depth_direction']['total'])
    return dict(seed=seed,resolution=n,source_state_sha256=hashlib.sha256(source.tobytes()).hexdigest(),
        canonical_velocity_error_vs_original_dense=float(abs(r['canonical_velocity']-v_dense).max()),
        physical_momentum_roundtrip_error=float(abs(recovered-p).max()),
        energy_error_vs_original_dense=abs(r['total']-dense_energy),
        minimum_local_kinetic_density=float(r['kinetic_density'].min()),
        positive_energy_contraction_error=r['positive_energy_contraction_error'],
        depth_gradient_error_vs_original_legendre=float(abs(a-legendre).max()),
        independent_chain_rule_error=float(chain),
        maximum_inverse_metric_residual=max(pole['relative_residual'] for pole in r['poles']),
        chain_rule_gate_passed=bool(chain<=1e-10*max(1.,abs(r['depth_direction']['total']))),
        final_direction_gate_passed=bool(probes[-1]['error']<=1e-7),
        probes=probes,dense_reference_seconds_shared_load=dense_seconds,
        primal_energy_and_direction_seconds_shared_load=primal_seconds,
        full_physical_flux_or_history_or_gameplay_accepted=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    names=('audit_rational_primal_energy.py','rational_primal_energy.py','reverse_rational_depth_gradient.py',
           'rational_dual_energy_reference.py','patch_pressure_preconditioner.py',
           'smooth_pressure_geometry.py','smooth_pressure_reverse.py','reconstructed_energy_reference.py')
    hashes=lambda:{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in names}
    original=hashes();records=[]
    for n in (64,128):
        for seed in range(2200,2208):
            r=run(seed,n);records.append(r);print(json.dumps(r),flush=True)
    if hashes()!=original:raise RuntimeError('Implementation changed during audit')
    with args.report.open('x') as stream:
        json.dump(dict(scope=__doc__,inverse_parameters=dict(k0=K0,betas=BETAS,alphas=ALPHAS,
                       exact_original_zero_response=ZERO_RESPONSE_EXACT),records=records,
                       implementation_hashes=original),stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
