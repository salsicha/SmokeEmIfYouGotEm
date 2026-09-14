"""Trace original MC pressure branches on the unchanged short RK2 controls.

This diagnoses the retained temporal-refinement defect. It does not change
pressure reconstruction, replace trajectories, align steps to an event, or
qualify full river evolution. Branch bisection uses actual endpoint states.
"""
import argparse
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
import numpy as np
from audit_reconstructed_closed_energy import fixture
from audit_reverse_rational_stage import make
from reconstructed_energy_reference import metric
from positive_rational_velocity_stage import stage,rk2_step
from pressure_cut_endpoint_reference import exact_endpoint_cuts
from rational_dual_energy_reference import evaluate
from reconstructed_pressure_rates import PressureGeometryRate
from extremum_preserving_transport import ExtremumPreservingTransport,ep_slope


def branch(h,b,axis,point,kind):
    p=list(point);q=list(point)
    p[axis]=(p[axis]-1)%h.shape[axis];q[axis]=(q[axis]+1)%h.shape[axis]
    p,q=tuple(p),tuple(q)
    back=F(float(h[point]))-F(float(h[p]));front=F(float(h[q]))-F(float(h[point]))
    if kind=='surface':
        back+=F(float(b[point]))-F(float(b[p]))
        front+=F(float(b[q]))-F(float(b[point]))
    candidates=(2*back,(back+front)/2,2*front)
    if all(v>=0 for v in candidates):return min(range(3),key=lambda j:candidates[j])
    if all(v<=0 for v in candidates):return max(range(3),key=lambda j:candidates[j])
    return -1


def signature(h,b):
    return {(axis,point,kind):branch(h,b,axis,point,kind)
        for axis in (1,0) if h.shape[axis]>1
        for point in np.ndindex(h.shape) for kind in ('depth','surface')}


def crossing(h0,v0,h1,v1,b,dx,key,start_time,dt):
    axis,point,kind=key;initial=branch(h0,b,*key)
    low,high=0.,1.
    for _ in range(40):
        mid=.5*(low+high);hh=h0+mid*(h1-h0)
        if branch(hh,b,*key)==initial:low=mid
        else:high=mid
    location=.5*(low+high);probes=[]
    # Relative distances on the SAME crossing segment. These probes measure
    # continuity; they do not substitute for the existing energy/time gates.
    for eps in (1e-3,1e-4,1e-5):
        if location-eps<=0 or location+eps>=1:continue
        states=[];values=[]
        for sign in (-1,1):
            fraction=location+sign*eps
            hh=h0+fraction*(h1-h0);vv=v0+fraction*(v1-v0)
            states.append((hh,vv));values.append(stage(make(hh,b,dx),vv))
        left,right=values
        extra={}
        if eps==1e-5:
            at=np.unravel_index(np.argmax(abs(right['depth_energy_gradient']-left['depth_energy_gradient'])),h0.shape)
            basis=np.zeros_like(h0);basis[at]=1.;independent=[]
            for (hh,vv),result in zip(states,values):
                gg=make(hh,b,dx)
                independent.append(evaluate(gg,vv,tangent=PressureGeometryRate(gg,b,basis))['depth_direction']['total']/dx**2)
            extra['independent_depth_gradient']=dict(point=list(map(int,at)),
                left=independent[0],right=independent[1],jump=independent[1]-independent[0],
                maximum_reverse_error=max(abs(independent[j]-values[j]['depth_energy_gradient'][at]) for j in (0,1)))
            ta,tb=[ExtremumPreservingTransport(hh,b,r['layer_velocity'],dx,periodic=True)
                for (hh,_),r in zip(states,values)]
            ha,hb=states[0][0],states[1][0]
            extra['transport_changes']=dict(
                maximum_retained_face_jump=max(float(abs(fb['retained']-fa['retained']).max()) for fa,fb in zip(ta.faces,tb.faces)),
                maximum_face_flux_jump=max(float(abs(fb['flux']-fa['flux']).max()) for fa,fb in zip(ta.faces,tb.faces)),
                maximum_layer_velocity_jump=float(abs(right['layer_velocity']-left['layer_velocity']).max()),
                maximum_ep_depth_slope_jump=max(float(abs(ep_slope(hb,ax)-ep_slope(ha,ax)).max()) for ax in (0,1)),
                maximum_ep_surface_slope_jump=max(float(abs(ep_slope(hb,ax,b)-ep_slope(ha,ax,b)).max()) for ax in (0,1)))
        probes.append(dict(relative_epsilon=eps,
            depth_state_gap=float(abs(states[1][0]-states[0][0]).max()),
            canonical_state_gap=float(abs(states[1][1]-states[0][1]).max()),
            depth_energy_gradient_jump=float(abs(right['depth_energy_gradient']-left['depth_energy_gradient']).max()),
            canonical_rate_jump=float(abs(right['canonical_velocity_rate']-left['canonical_velocity_rate']).max()),
            mass_rate_jump=float(abs(right['depth_rate']-left['depth_rate']).max()),
            energy_gap=right['energy']-left['energy'],
            maximum_chain_rule_error=max(left['branch_chain_rule_error'],right['branch_chain_rule_error']),**extra))
    return dict(axis=axis,point=list(point),kind=kind,initial_branch=initial,
        final_branch=branch(h1,b,*key),fraction=location,
        interpolated_time=start_time+location*dt,probes=probes,
        interpretation='linear state-segment crossing, not an exact trajectory event time')


def run(seed):
    state,b=fixture(seed,'smooth',64);h=state[...,0];u=state[...,1:]/h[...,None];dx=.25
    k,_=metric(make(h,b,dx),rational=True);root=np.sqrt(h)[...,None]
    v=(k@(root*u).ravel()).reshape(u.shape)/root
    events=[];dt=.0005;sig=signature(h,b)
    for index in range(16):
        hh,vv,_=rk2_step(h,b,v,dx,dt);after=signature(hh,b)
        changed=[key for key in sig if sig[key]!=after[key]]
        for key in changed:
            event=crossing(h,v,hh,vv,b,dx,key,index*dt,dt)
            events.append(event);print(json.dumps(dict(event='branch_crossing',seed=seed,**event)),flush=True)
        h,v,sig=hh,vv,after
    return dict(seed=seed,source_state_sha256=hashlib.sha256(state.tobytes()).hexdigest(),
        endpoint_sha256=hashlib.sha256(h.tobytes()+v.tobytes()).hexdigest(),events=events,
        endpoint_time=.008,dt=dt,original_trajectory_preserved=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    records=[]
    with exact_endpoint_cuts():
        for seed in range(2200,2208):
            r=run(seed);records.append(r)
            print(json.dumps(dict(event='branch_trace_complete',seed=seed,crossings=len(r['events']))),flush=True)
    report=dict(scope=__doc__,records=records,full_evolution_or_gameplay_accepted=False,
        implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('audit_positive_rational_branch_crossings.py','positive_rational_velocity_stage.py',
                'extremum_preserving_transport.py','reverse_rational_depth_gradient.py',
                'rational_dual_energy_reference.py','reconstructed_pressure_rates.py')})
    with args.report.open('x') as stream:json.dump(report,stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
