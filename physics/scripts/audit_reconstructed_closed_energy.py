"""Closed periodic full-FV energy controls, not open-river or model acceptance.

Standard SGN uses its completed-square reconstructed energy. The rational model
is also evaluated using the inverse frozen linear-response metric extended to
nonlinear states, explicitly NOT an established invariant. No source resets,
artificial dissipation, new solver, pressure gate changes, or state projection.
"""
import argparse
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import numpy as np
import total_depth_bank_replay as bank
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_pressure_rates import PressureGeometryRate
from reconstructed_nonlinear_pressure import nonlinear_pressure
from reconstructed_energy_reference import energy_rate
from difference_scalar_gradient_reference import difference_scalar_gradients
from pressure_cut_endpoint_reference import exact_endpoint_cuts


def fixture(seed, family='rough', resolution=32):
    rng=np.random.default_rng(seed);shape=(3,4)
    if family=='smooth':
        x=2*np.pi*(np.arange(resolution)+.5)/resolution
        phase=rng.uniform(0,2*np.pi,6)
        h=(1.5+.35*np.sin(x+phase[0])+.15*np.cos(2*x+phase[1]))[None]
        bed=(.2*np.sin(x+phase[2]))[None] if seed%2 else np.zeros_like(h)
        u=np.zeros((*h.shape,2))
        u[...,0]=2.+.6*np.sin(x+phase[3])+.3*np.cos(2*x+phase[4])+.1*np.sin(3*x+phase[5])
        return np.concatenate((h[...,None],h[...,None]*u),axis=-1),bed
    # A fixed family spans fully positive depth contrasts and rough topography;
    # no dry cells, exterior sources or hidden boundary work enter this control.
    h=np.exp(rng.uniform(np.log(.015),np.log(2.),shape))
    bed=rng.uniform(0,.8,shape) if seed%2 else np.zeros(shape)
    u=rng.normal(size=(*shape,2))*1.5
    return np.concatenate((h[...,None],h[...,None]*u),axis=-1),bed


def run(seed, family='rough', resolution=32):
    state,bed=fixture(seed,family,resolution);h=state[...,0];u=state[...,1:]/h[...,None]
    dx=16./resolution if family=='smooth' else .5
    fv,cfl=bank.rate(state,bed,dx,second_order=True,periodic=True,shoreline_limiter='unscaled')
    g=ReconstructedPressureGeometry(h,bed,dx,periodic=True,
        pressure_trace='integrated_column',bed_quadrature='shared_bottom')
    tangent=PressureGeometryRate(g,bed,fv[...,0])
    cases=[]
    for rational in (False,True):
        for mode in ('original','difference_scalar'):
            with difference_scalar_gradients() if mode=='difference_scalar' else nullcontext():
                pressure,details=nonlinear_pressure(g,u,fv[...,0],fv[...,1:],rational=rational,preconditioner='block')
            full=fv.copy();full[...,1:]+=pressure
            rate=energy_rate(g,tangent,u,full[...,1:],rational=rational)
            original_fv=energy_rate(g,tangent,u,fv[...,1:],rational=rational)
            cases.append(dict(model='rational_sgn' if rational else 'sgn',scalar=mode,
                energy_rate=rate,without_pressure_rate=original_fv,
                rate_per_unit_transverse_width=rate['total']/dx if family=='smooth' else None,
                pressure_residuals=[p['relative_residual'] for p in details['poles']],
                pressure_gate_passed=all(p['relative_residual']<2e-5 for p in details['poles']),
                total_rate_positive=rate['total']>1e-10,
                state_rate_sha256=hashlib.sha256(full.tobytes()).hexdigest()))
    return dict(seed=seed,shape=list(h.shape),cell_m=dx,minimum_depth_m=float(h.min()),
        transverse_width_m=h.shape[0]*dx,
        maximum_depth_m=float(h.max()),maximum_speed_mps=float(np.linalg.norm(u,axis=-1).max()),
        variable_bed=bool(np.any(bed)),cfl_s=cfl,net_mass_rate=float(fv[...,0].sum()*dx**2),
        state_sha256=hashlib.sha256(state.tobytes()).hexdigest(),cases=cases)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True);parser.add_argument('--cases',type=int,default=32)
    parser.add_argument('--family',choices=('rough','smooth'),default='rough')
    parser.add_argument('--resolution',type=int,choices=(16,32,64,128),default=32)
    args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    if not 1<=args.cases<=256:raise ValueError('Bounded fixed control family required')
    records=[]
    with exact_endpoint_cuts():
        for seed in range(2200,2200+args.cases):
            record=run(seed,args.family,args.resolution);records.append(record)
            print(json.dumps(dict(event='closed_energy_case',seed=seed,
                rates=[dict(model=c['model'],scalar=c['scalar'],rate=c['energy_rate']['total'])
                       for c in record['cases']])),flush=True)
    summary=[]
    for model in ('sgn','rational_sgn'):
        for mode in ('original','difference_scalar'):
            matched=[(r['seed'],c) for r in records for c in r['cases'] if c['model']==model and c['scalar']==mode]
            worst=max(matched,key=lambda pair:pair[1]['energy_rate']['total'])
            summary.append(dict(model=model,scalar=mode,positive_cases=sum(c['total_rate_positive'] for _,c in matched),
                total_cases=len(matched),largest_rate_seed=worst[0],largest_rate=worst[1]['energy_rate']['total']))
    result=dict(family=args.family,resolution=args.resolution if args.family=='smooth' else None,
        cases=records,summary=summary,pressure_gates_passed=all(c['pressure_gate_passed'] for r in records for c in r['cases']),
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('reconstructed_energy_reference.py','audit_reconstructed_closed_energy.py',
                         'reconstructed_pressure_geometry.py','reconstructed_pressure_rates.py',
                         'reconstructed_nonlinear_pressure.py','total_depth_bank_replay.py')},
        nonlinear_energy_or_history_qualified=False,open_boundary_or_gameplay_accepted=False,
        limitations='Fully positive small periodic instantaneous controls only. Actual FV/pressure forcing is unchanged. '
        'SGN completed-square energy is distinguished from the nonlinear rational-response metric extension. '
        'Negative sample rates do not prove stability; positive rational-metric rates do not alone prove the model lacks another energy.')
    with args.report.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
    print(json.dumps(dict(summary=summary,pressure_gates_passed=result['pressure_gates_passed']),indent=2),flush=True)


if __name__=='__main__':main()
