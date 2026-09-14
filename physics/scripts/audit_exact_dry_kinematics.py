"""Independent rational face oracle for the retained dry-cell D^2 defect.

Evaluate the original MC polynomial and pressure transfer A=r^2(3-2r)
directly on represented h/bed inputs. An ordered (value, right derivative)
pair evaluates the actual entering ray at zero, without a positive-depth
replacement. No native, source, solver or test-tolerance changes.
"""
import argparse
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
import numpy as np
from reconstructed_pressure_geometry import ReconstructedPressureGeometry as Geometry
from directional_pressure_geometry import DirectionalPressureGeometry


def add(a,b):return a[0]+b[0],a[1]+b[1]
def sub(a,b):return a[0]-b[0],a[1]-b[1]
def scale(a,s):return a[0]*s,a[1]*s
ZERO=(F(0),F(0))


def limited(a,b):
    candidates=(scale(a,2),scale(add(a,b),F(1,2)),scale(b,2))
    if all(c>=ZERO for c in candidates):return min(candidates)
    if all(c<=ZERO for c in candidates):return max(candidates)
    return ZERO


def ratio_limit(a,b):
    if b[0]:return a[0]/b[0]
    if b[1]:return a[1]/b[1]
    if a!=ZERO:raise ValueError('Nonzero numerator without supported column')
    return F(0)


def oracle(depth,bed,mass_rate,velocity):
    shape=depth.shape
    d=np.empty(shape,dtype=object);d.fill(F(0));faces=[]
    for axis in (1,0):
        polys={}
        for p in np.ndindex(shape):
            h=(F(float(depth[p])),F(float(mass_rate[p])));z=F(float(bed[p]))
            dh=de=ZERO
            if h>ZERO and 0<p[axis]<shape[axis]-1:
                lo=list(p);hi=list(p);lo[axis]-=1;hi[axis]+=1;lo=tuple(lo);hi=tuple(hi)
                a=(F(float(depth[lo])),F(float(mass_rate[lo])))
                b=(F(float(depth[hi])),F(float(mass_rate[hi])))
                if a>ZERO and b>ZERO:
                    back=sub(h,a);front=sub(b,h)
                    dh=limited(back,front)
                    de=limited(add(back,(z-F(float(bed[lo])),F(0))),
                               add(front,(F(float(bed[hi]))-z,F(0))))
            polys[p]=(h,z,dh,de)
        for p in np.ndindex(shape):
            if p[axis]==shape[axis]-1:continue
            q=list(p);q[axis]+=1;q=tuple(q)
            hi,zi,dhi,dei=polys[p];hj,zj,dhj,dej=polys[q]
            ha=add(hi,scale(dhi,F(1,2)));hb=sub(hj,scale(dhj,F(1,2)))
            jump=sub((zj-zi,F(0)),scale(add(sub(dei,dhi),sub(dej,dhj)),F(1,2)))
            ra=max(ZERO,sub(ha,max(ZERO,jump)))
            rb=max(ZERO,sub(hb,max(ZERO,scale(jump,-1))))
            ar=ratio_limit(ra,ha);br=ratio_limit(rb,hb)
            aa=ar*ar*(3-2*ar);ab=br*br*(3-2*br)
            total=add(hi,hj);own=ratio_limit(hi,total);other=ratio_limit(hj,total)
            component=1-axis
            face_u=own*F(float(velocity[p][component]))+other*F(float(velocity[q][component]))
            d[p]+=aa*face_u;d[q]-=ab*face_u
            faces.append(dict(axis=axis,owner=list(p),neighbor=list(q),
                jump_value=str(jump[0]),jump_rate=str(jump[1]),
                ha_value=str(ha[0]),ha_rate=str(ha[1]),hb_value=str(hb[0]),hb_rate=str(hb[1]),
                retained_ratio_a=str(ar),retained_ratio_b=str(br),
                aa=str(aa),ab=str(ab),face_velocity=str(face_u)))
    return np.array(d.tolist(),dtype=float),faces


def fixture():
    n=5;dx=1/n
    y,x=np.meshgrid((np.arange(n+6)-2.5)*dx,(np.arange(n+6)-2.5)*dx,indexing='ij')
    h=np.where(x<.25,0.,1.);bed=.125*np.maximum(x,0)+.0625*y
    state=np.stack((h,h*(.2+x),h*(.3+y)),axis=-1)[3:-3,3:-3].copy()
    rates=np.empty_like(state);rates[...,0]=.125;rates[...,1]=.0625;rates[...,2]=-.03125
    return state,bed[3:-3,3:-3].copy(),rates,dx


def run():
    state,bed,rates,dx=fixture();cases=[];target=(3,0);limit=None
    for power in (None,8,16,24,48,56,64):
        current=state.copy() if power is None else state+2.**-power*rates
        h=current[...,0]
        u=np.divide(current[...,1:],h[...,None],out=np.zeros_like(current[...,1:]),where=h[...,None]>0)
        ht=np.zeros_like(h)
        g=Geometry(h,bed,dx,pressure_trace='integrated_column',bed_quadrature='shared_bottom')
        if power is None:
            ht=rates[...,0];g=DirectionalPressureGeometry(g,ht)
            u[h==0]=rates[...,1:][h==0]/rates[...,0][h==0,None]
        expected,faces=oracle(h,bed,ht,u);expected/=dx
        actual,_=g.kinematic_components(u)
        if limit is None:limit=expected.copy()
        incident=[face for face in faces if list(target) in (face['owner'],face['neighbor'])]
        cases.append(dict(epsilon_power=power,maximum_oracle_discrepancy=float(abs(expected-actual).max()),
            original_D_at_target=float(actual[target]),oracle_D_at_target=float(expected[target]),
            target_D_squared_error=float(expected[target]**2-limit[target]**2),
            original_target_D_squared_error=float(actual[target]**2-limit[target]**2),
            target_incident_faces=incident))
    return dict(target=list(target),cases=cases,
        input_state_sha256=hashlib.sha256(state.tobytes()).hexdigest(),
        input_bed_sha256=hashlib.sha256(bed.tobytes()).hexdigest(),
        original_probe_gate_replaced=False,native_or_full_history_accepted=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.report.exists():raise FileExistsError(args.report)
    result=run();result['scope']=__doc__
    result['implementation_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with args.report.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
    for case in result['cases']:print(json.dumps({k:v for k,v in case.items() if k!='target_incident_faces'}),flush=True)


if __name__=='__main__':main()
