"""Localize a variable-bed entering-ray failure without changing tolerances."""
import argparse
import json
from pathlib import Path
import numpy as np
from fractions import Fraction as F
from reconstructed_pressure_geometry import ReconstructedPressureGeometry as Geometry
from reconstructed_pressure_rates import PressureGeometryRate
from directional_pressure_geometry import DirectionalPressureGeometry
from source_supported_scalar_boundary import SourceSupportedScalarBoundary


def make(h, bed, dx):
    return Geometry(h, bed, dx, pressure_trace='integrated_column', bed_quadrature='shared_bottom')


def exact_dry_bed_gaps(h,bed):
    """Independent represented-input MC reconstruction, no rounded h+bed."""
    def mc(a,b):
        if a>0 and b>0:return min(2*a,(a+b)/2,2*b)
        if a<0 and b<0:return max(2*a,(a+b)/2,2*b)
        return F(0)
    result=[]
    for axis in (1,0):
        def poly(point):
            hi,zi=F(float(h[point])),F(float(bed[point]));dh=de=F(0)
            if 0<point[axis]<h.shape[axis]-1:
                a=list(point);a[axis]-=1;a=tuple(a)
                b=list(point);b[axis]+=1;b=tuple(b)
                dh=mc(hi-F(float(h[a])),F(float(h[b]))-hi)
                de=mc(hi-F(float(h[a]))+zi-F(float(bed[a])),
                      F(float(h[b]))-hi+F(float(bed[b]))-zi)
            return hi,zi,dh,de
        for point in np.ndindex(h.shape):
            if point[axis]==h.shape[axis]-1:continue
            neighbor=list(point);neighbor[axis]+=1;neighbor=tuple(neighbor)
            hi,zi,dhi,dei=poly(point);hj,zj,dhj,dej=poly(neighbor)
            jump=zj-zi-(dei-dhi+dej-dhj)/2
            if hi==0 and hj==0 and jump!=0:
                result.append(dict(axis=axis,index=list(point),exact_jump=str(jump),
                    jump_m=float(jump),positive_column_reaches_gap_seconds=float(abs(jump)/F(1,8))))
    return result


def ray_case(flat):
    n=5; dx=1/n
    y,x=np.meshgrid((np.arange(n+6)-2.5)*dx,(np.arange(n+6)-2.5)*dx,indexing='ij')
    h=np.where(x<.25,0.,1.); bed=np.zeros_like(x) if flat else .125*np.maximum(x,0)+.0625*y
    state=np.stack((h,h*(.2+x),h*(.3+y)),axis=-1)
    rate=np.zeros_like(state);rate[...,0]=.125;rate[...,1]=.0625;rate[...,2]=-.03125
    core=(slice(3,-3),slice(3,-3));trace=np.zeros((4*n,2))
    g=DirectionalPressureGeometry(make(h[core],bed[core],dx),rate[core][...,0])
    b=SourceSupportedScalarBoundary(g,state[core],state,bed,full_rate=rate)
    expected=b.forcing(g.tangent,trace)
    results=[]
    # Preserve the original three failing probes, then examine smaller rays.
    # Tiny nonzero jumps in represented non-dyadic bed coordinates can make
    # those original probes pre-asymptotic; this does not erase their failures.
    for eps in (2.**-8,2.**-16,2.**-24,2.**-48,2.**-64):
        later=state+eps*rate;gg=make(later[core][...,0],bed[core],dx)
        bb=SourceSupportedScalarBoundary(gg,later[core],later,bed)
        tangent=PressureGeometryRate(gg,gg.bed,rate[core][...,0])
        actual=bb.forcing(tangent,trace)
        fields=[]
        for name,a,e in zip(('quadratic','curvature','advective'),actual,expected):
            index=np.unravel_index(np.argmax(abs(a-e)),a.shape)
            fields.append(dict(field=name,max_error=float(abs(a-e).max()),index=list(map(int,index)),
                actual=float(a[index]),limit=float(e[index])))
        coefficient_errors={}
        for label,a,e in [('interior',gg,g),('extended',bb.extended,b.extended)]:
            for axis,(aa,ee) in enumerate(zip(a.edges,e.edges)):
                for key in aa:
                    diff=abs(aa[key]-ee[key])
                    if diff.max()>1e-5:
                        index=np.unravel_index(np.argmax(diff),diff.shape)
                        coefficient_errors[f'{label}_{axis}_{key}']=dict(error=float(diff.max()),
                            index=list(map(int,index)),actual=float(aa[key][index]),limit=float(ee[key][index]))
        results.append(dict(epsilon=eps,fields=fields,coefficient_errors=coefficient_errors))
    return dict(flat=flat,results=results,original_interior_dry_bed_gaps=exact_dry_bed_gaps(h[core],bed[core]),
        original_three_probe_test_passed=all(f['max_error']<1e-6 for f in results[2]['fields']),
        smallest_probe_within_same_tolerance=all(f['max_error']<1e-6 for f in results[-1]['fields']),
        full_wetting_or_solver_qualified=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    result=dict(cases=[ray_case(True),ray_case(False)],native_or_gameplay_accepted=False)
    with args.report.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
