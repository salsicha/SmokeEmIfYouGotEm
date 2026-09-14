"""Physical momentum check on the ORIGINAL four flat-bed smooth controls.

On a periodic flat bed the pressure metric preserves the constant physical
velocity mode, so integral h*v equals integral h*u. Compare their instantaneous
rates and independent state-direction probes. Energy/mass passes do not waive
physical momentum conservation. No source or model is changed by this audit.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_reconstructed_closed_energy import fixture
from reconstructed_energy_reference import metric
from rational_dual_energy_reference import evaluate
from smooth_rational_velocity_stage import make,stage


def run(seed,n):
    state,b=fixture(seed,'smooth',n);h=state[...,0];u=state[...,1:]/h[...,None];dx=16/n;area=dx**2
    if np.any(b!=0):raise ValueError('Zero external bed-force control required')
    g=make(h,b,dx);k,_=metric(g,rational=True);root=np.sqrt(h)[...,None]
    v=(k@(root*u).ravel()).reshape(u.shape)/root;r=stage(g,v)
    physical=np.sum(r['flux'],axis=(0,1))*area;canonical=np.sum(h[...,None]*v,axis=(0,1))*area
    rate=np.sum(r['depth_rate'][...,None]*v+h[...,None]*r['canonical_velocity_rate'],axis=(0,1))*area
    probes=[]
    for eps in (1e-3,1e-4,1e-5):
        values=[]
        for sign in (-1,1):
            hh=h+sign*eps*r['depth_rate'];vv=v+sign*eps*r['canonical_velocity_rate']
            values.append(np.sum(evaluate(make(hh,b,dx),vv)['canonical_gradient_flux'],axis=(0,1))*area)
        measured=(values[1]-values[0])/(2*eps)
        probes.append(dict(epsilon=eps,physical_momentum_direction=measured.tolist(),
            error_vs_canonical_rate=float(abs(measured-rate).max())))
    return dict(seed=seed,resolution=n,source_state_sha256=hashlib.sha256(state.tobytes()).hexdigest(),
        physical_momentum=physical.tolist(),canonical_momentum=canonical.tolist(),
        momentum_identity_error=float(abs(physical-canonical).max()),momentum_rate=rate.tolist(),
        energy_rate=r['energy_rate'],net_mass_rate=r['net_mass_rate'],probes=probes,
        zero_momentum_rate_control_passed=bool(abs(rate).max()<1e-10),
        physical_model_or_gameplay_accepted=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    records=[]
    for n in (64,128):
        for seed in (2200,2202,2204,2206):
            r=run(seed,n);records.append(r);print(json.dumps(r),flush=True)
    report=dict(scope=__doc__,records=records,implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ('audit_smooth_stage_momentum.py','smooth_rational_velocity_stage.py','smooth_pressure_geometry.py',
            'continuous_extremum_transport.py','rational_dual_energy_reference.py')})
    with args.report.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
