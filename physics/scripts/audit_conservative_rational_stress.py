"""Original eight flat profiles: conservative stress AND separate energy gates.

No source changes, no momentum/energy projection. Full variable-bed/dry/history
and nonlinear-energy qualification remains required before any river use.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_reconstructed_closed_energy import fixture
from reconstructed_energy_reference import metric
from smooth_rational_velocity_stage import make
from conservative_rational_stress import stress_stage,stress_stage_physical


def run(seed,n,metric_source='dense'):
    source,bed=fixture(seed,'smooth',n);h=source[...,0];u=source[...,1:]/h[...,None];dx=16/n
    g=make(h,bed,dx)
    if metric_source=='primal':
        r=stress_stage_physical(g,source[...,1:])
    elif metric_source=='dense':
        k,_=metric(g,rational=True);root=np.sqrt(h)[...,None]
        v=(k@(root*u).ravel()).reshape(u.shape)/root;r=stress_stage(g,v)
    else:raise ValueError('Unknown physical state preparation')
    momentum=np.sum(r['physical_momentum_rate'],axis=(0,1))*dx**2
    return dict(seed=seed,resolution=n,source_state_sha256=hashlib.sha256(source.tobytes()).hexdigest(),
        source_physical_velocity_recovery_error=float(abs(r['momentum']/h[...,None]-u).max()),
        physical_total_momentum_rate=momentum.tolist(),
        momentum_conservation_gate_passed=bool(abs(momentum).max()<1e-10),
        local_momentum_flux_error=r['local_momentum_flux_error'],
        auxiliary_momentum_identity_error=r['auxiliary_momentum_identity_error'],
        net_mass_rate=float(np.sum(r['depth_rate'])*dx**2),
        energy_rate=r['energy_rate'],energy_rate_per_unit_width=r['energy_rate']/dx,
        energy_conservation_gate_passed=bool(abs(r['energy_rate'])<1e-10),
        energy_coordinate_error=r['energy_coordinate_error'],
        centered_mass_control_energy_rate=r['centered_mass_control_energy_rate'],
        donor_incremental_energy_rate=r['donor_incremental_energy_rate'],
        energy_work_split_error=r['energy_work_split_error'],
        mass_only_forward_euler_bound=r['mass_only_forward_euler_bound'],
        maximum_derivative_residual=max(p['relative_residual'] for p in r['poles']),
        all_required_physics_or_gameplay_accepted=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--metric-source',choices=('dense','primal'),default='dense');args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    names=('audit_conservative_rational_stress.py','conservative_rational_stress.py',
           'rational_physical_momentum_rate.py','rational_dual_energy_reference.py',
           'patch_pressure_preconditioner.py','smooth_pressure_geometry.py',
           'smooth_pressure_reverse.py','reverse_rational_depth_gradient.py',
           'continuous_extremum_transport.py','extremum_preserving_transport.py','hydrostatic_energy_transport.py',
           'rational_primal_energy.py')
    hashes=lambda:{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in names}
    original=hashes();records=[]
    for n in (64,128):
        for seed in (2200,2202,2204,2206):
            r=run(seed,n,args.metric_source);records.append(r);print(json.dumps(r),flush=True)
    if hashes()!=original:raise RuntimeError('Implementation changed during audit')
    with args.report.open('x') as stream:
        json.dump(dict(scope=__doc__,metric_source=args.metric_source,records=records,
                       implementation_hashes=original),stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
