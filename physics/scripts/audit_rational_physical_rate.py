"""Original 16 smooth profiles: physical rate/energy-coordinate audit.

No source reset or new solver. Evaluate the unqualified smooth coupled stage,
then transform its complete derivative to physical momentum analytically.
Compare independent physical-momentum finite differences and both energy
coordinate expressions. Retain momentum failures; the bridge is not a fix.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_reconstructed_closed_energy import fixture
from reconstructed_energy_reference import metric
from rational_dual_energy_reference import evaluate
from rational_physical_momentum_rate import physical_rate
from smooth_rational_velocity_stage import make,stage


def run(seed,n,derivative_preconditioner='block',primal_preconditioner='block'):
    source,bed=fixture(seed,'smooth',n);h=source[...,0];u=source[...,1:]/h[...,None];dx=16/n
    g=make(h,bed,dx);k,_=metric(g,rational=True);root=np.sqrt(h)[...,None]
    v=(k@(root*u).ravel()).reshape(u.shape)/root
    r=stage(g,v);ht=r['depth_rate'];vt=r['canonical_velocity_rate']
    transformed=physical_rate(g,v,ht,vt,derivative_preconditioner=derivative_preconditioner,
                              primal_preconditioner=primal_preconditioner);pt=transformed['momentum_rate']
    probes=[]
    for eps in (1e-3,1e-4,1e-5):
        values=[]
        for sign in (-1,1):
            values.append(evaluate(make(h+sign*eps*ht,bed,dx),v+sign*eps*vt,
                                   preconditioner=primal_preconditioner)['canonical_gradient_flux'])
        fd=(values[1]-values[0])/(2*eps)
        probes.append(dict(epsilon=eps,maximum_physical_rate_error=float(abs(fd-pt).max())))
    total=np.sum(pt,axis=(0,1))*dx**2
    canonical_total=np.sum(ht[...,None]*v+h[...,None]*vt,axis=(0,1))*dx**2
    scale=max(1.,abs(transformed['canonical_energy_rate']),abs(transformed['physical_energy_rate']))
    return dict(seed=seed,resolution=n,source_state_sha256=hashlib.sha256(source.tobytes()).hexdigest(),
        source_physical_velocity_recovery_error=float(abs(r['layer_velocity']-u).max()),
        physical_total_momentum_rate=total.tolist(),canonical_total_momentum_rate=canonical_total.tolist(),
        flat_bed=bool(np.all(bed==0)),
        flat_bed_momentum_gate_passed=bool(abs(total).max()<1e-10) if np.all(bed==0) else None,
        local_difference_from_canonical_momentum_rate=float(abs(pt-(ht[...,None]*v+h[...,None]*vt)).max()),
        canonical_energy_rate=transformed['canonical_energy_rate'],
        physical_energy_rate=transformed['physical_energy_rate'],
        energy_coordinate_error=transformed['energy_coordinate_error'],
        scaled_energy_coordinate_gate_passed=bool(transformed['energy_coordinate_error']<=1e-10*scale),
        maximum_derivative_pole_residual=max(p['relative_residual'] for p in transformed['poles']),
        maximum_primal_pole_residual=max(transformed['primal_pressure_residuals']),
        probes=probes,physical_solver_or_gameplay_accepted=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--derivative-preconditioner',choices=('block','patch'),default='block')
    parser.add_argument('--primal-preconditioner',choices=('block','patch'),default='block');args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    names=('audit_rational_physical_rate.py','rational_physical_momentum_rate.py',
           'smooth_rational_velocity_stage.py','smooth_pressure_geometry.py',
           'smooth_pressure_reverse.py','reverse_rational_depth_gradient.py',
           'rational_dual_energy_reference.py','reconstructed_acceleration_system.py','patch_pressure_preconditioner.py')
    hashes=lambda:{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in names}
    original=hashes();records=[]
    for n in (64,128):
        for seed in range(2200,2208):
            r=run(seed,n,args.derivative_preconditioner,args.primal_preconditioner);records.append(r);print(json.dumps(r),flush=True)
    if hashes()!=original:raise RuntimeError('Implementation changed while audit was running')
    with args.report.open('x') as stream:
        json.dump(dict(scope=__doc__,derivative_preconditioner=args.derivative_preconditioner,
                       primal_preconditioner=args.primal_preconditioner,
                       records=records,implementation_hashes=original),stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
