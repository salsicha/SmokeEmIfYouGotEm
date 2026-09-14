"""Diagnose the retained smooth-refinement failure; no alternative is qualified.

The original 32/64/128 probe and 3.2 ratios are unchanged. Finer grids and
uncut/unlimited expressions are additional diagnostic controls only. The latter
do not have dry-bank or positivity acceptance and must not become gameplay.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from hydrostatic_energy_transport import HydrostaticEnergyTransport
from total_depth_bank_replay import mc, hydrostatic_faces


def run(n):
    dx=2*np.pi/n;x=(np.arange(n)+.5)*dx
    h=(1+.2*np.sin(x+.31))[None];b=.1*np.cos(x+.13)[None]
    u=np.zeros((*h.shape,2));u[...,0]=1+.1*np.cos(x+.47)
    expected=-(.2*np.cos(x+.31)*(1+.1*np.cos(x+.47))-.1*h[0]*np.sin(x+.47))
    t=HydrostaticEnergyTransport(h,b,u,dx,periodic=True)
    uf=t.faces[0]['own']*u[...,0]+t.faces[0]['other']*np.roll(u[...,0],-1,1)
    dh=mc(h,1,True);de=mc(h,1,True,other=b)
    limited=(h+.5*dh)*uf
    # Remove MC limiting only in this diagnostic expression. Never replace the
    # actual transport or its gates with this non-positive control.
    ch=.5*(np.roll(h,-1,1)-np.roll(h,1,1))
    ce=ch+.5*(np.roll(b,-1,1)-np.roll(b,1,1))
    *_,fa,fb=hydrostatic_faces(h,b,ch,ce,1,True)
    unlimited=fa[:,1:]*uf
    fluxes={'original':t.faces[0]['flux'],'uncut_mc':limited,
            'unlimited_cut':unlimited,'unlimited_uncut':(h+.5*ch)*uf}
    errors={}
    for name,flux in fluxes.items():
        rate=-(flux-np.roll(flux,1,1))/dx
        errors[name]=dict(l1=float(np.mean(abs(rate[0]-expected))),
                          linf=float(np.max(abs(rate[0]-expected))))
    removal=limited-t.faces[0]['flux']
    delta_rate=-(removal-np.roll(removal,1,1))/dx
    eta_limited=abs(de-ce)>1e-14
    h_limited=abs(dh-ch)>1e-14
    return dict(resolution=n,errors=errors,mc_limited_depth_cells=int(h_limited.sum()),
        mc_limited_surface_cells=int(eta_limited.sum()),
        maximum_cut_flux_removal=float(removal.max()),
        cut_rate_difference_l1=float(np.mean(abs(delta_rate))),
        source_state_sha256=hashlib.sha256(np.stack((h,b,u[...,0])).tobytes()).hexdigest())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    records=[run(n) for n in (32,64,128,256,512,1024)]
    ratios={name:[a['errors'][name]['l1']/b['errors'][name]['l1']
        for a,b in zip(records,records[1:])] for name in records[0]['errors']}
    report=dict(scope=__doc__,records=records,l1_refinement_ratios=ratios,
        original_refinement_gate_passed=bool(min(ratios['original'][:2])>3.2),
        dry_pressure_or_time_evolution_or_gameplay_accepted=False,
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('audit_hydrostatic_energy_transport.py','hydrostatic_energy_transport.py')})
    with args.report.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
