"""Positive-domain C1 pressure-energy reconstruction RESEARCH candidate.

For centered undivided depth/surface slopes c,e, let f=4h^2/(4h^2+c^2)
and (dh,deta)=f*(c,e). This rational polynomial is smooth for h>0 and
|dh|<=h, so both reconstructed depth endpoints are >=h/2 without changing h.
The shared bed coefficient Cb-Ca is C1 across the original hydrostatic cuts,
even though Ca and Cb separately have one-sided derivatives at zero bed jump.

No absolute depth floor, added mass, MC branch or slope-mask switch is used in
this strictly-positive periodic research domain. Exactly dry/open domains are
rejected; no full wetting, entropy, physical-model or native acceptance.
"""
from fractions import Fraction as F
import numpy as np
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_pressure_rates import PressureGeometryRate,positive_dual
from pressure_cut_face_reference import cut_pressure_column,represented_float
from total_depth_nonlinear_pressure import geometric_bed_slope


def polynomial_jet(h,b,ht,axis,point):
    """Independent explicit rational value/tangent; not reverse-mode AD."""
    p=list(point);q=list(point)
    p[axis]=(p[axis]-1)%h.shape[axis];q[axis]=(q[axis]+1)%h.shape[axis]
    p,q=tuple(p),tuple(q)
    hi=F(float(h[point]));ti=F(float(ht[point]));zi=F(float(b[point]))
    c=(F(float(h[q]))-F(float(h[p])))/2
    e=c+(F(float(b[q]))-F(float(b[p])))/2
    ct=(F(float(ht[q]))-F(float(ht[p])))/2
    numerator=4*hi*hi;denominator=numerator+c*c
    nt=8*hi*ti;denominator_t=nt+2*c*ct
    f=numerator/denominator;ft=(nt*denominator-numerator*denominator_t)/(denominator*denominator)
    return hi,zi,ti,f*c,f*e,ft*c+f*ct,ft*e+f*ct


def assemble(h,b,ht):
    edges=[];rates=[];polynomials=[]
    for axis in (1,0):
        keys=('aa','ab','ca','cb','own','other','shared_b')
        edge={key:np.zeros_like(h) for key in keys};rate={key:np.zeros_like(h) for key in keys}
        poly={key:np.zeros_like(h) for key in ('hm','hp','ha','hb','fa','fb','dh','deta')}
        jets={p:polynomial_jet(h,b,ht,axis,p) for p in np.ndindex(h.shape)}
        for p,(hi,zi,ti,dh,de,dh_t,de_t) in jets.items():
            poly['hm'][p]=represented_float(hi-dh/2);poly['hp'][p]=represented_float(hi+dh/2)
            poly['dh'][p]=represented_float(dh);poly['deta'][p]=represented_float(de)
            if h.shape[axis]==1:
                for key in ('ha','hb','fa','fb'):poly[key][p]=float(hi)
                continue
            q=list(p);q[axis]=(q[axis]+1)%h.shape[axis];q=tuple(q)
            hj,zj,tj,dj,ej,dj_t,ej_t=jets[q]
            ha,hb=hi+dh/2,hj-dj/2;ha_t,hb_t=ti+dh_t/2,tj-dj_t/2
            jump=zj-zi-(de-dh+ej-dj)/2;jump_t=-(de_t-dh_t+ej_t-dj_t)/2
            ja,ja_t=positive_dual(jump,jump_t);jb,jb_t=positive_dual(-jump,-jump_t)
            fa,fa_t=positive_dual(ha-ja,ha_t-ja_t);fb,fb_t=positive_dual(hb-jb,hb_t-jb_t)
            values={};directions={}
            for side,height,wet,height_t,wet_t in (('a',ha,fa,ha_t,fa_t),('b',hb,fb,hb_t,fb_t)):
                ac=cut_pressure_column(height,F(1),F(0),wet,height_rate=height_t,retained_height_rate=wet_t)
                cc=cut_pressure_column(height,F(0),F(1),wet,height_rate=height_t,retained_height_rate=wet_t)
                values['a'+side]=ac.transmitted;values['c'+side]=cc.transmitted
                directions['a'+side]=ac.transmitted_rate;directions['c'+side]=cc.transmitted_rate
            total=hi+hj;own=hi/total;other=hj/total
            own_t=(ti*hj-hi*tj)/(total*total);other_t=-own_t
            values.update(own=own,other=other,shared_b=own*other*(values['cb']-values['ca']))
            directions.update(own=own_t,other=other_t,
                shared_b=(own_t*other+own*other_t)*(values['cb']-values['ca'])
                    +own*other*(directions['cb']-directions['ca']))
            for key in keys:
                edge[key][p]=represented_float(values[key]);rate[key][p]=represented_float(directions[key])
            for key,value in (('ha',ha),('hb',hb),('fa',fa),('fb',fb)):poly[key][p]=represented_float(value)
        edge['local_p']=np.zeros_like(h);edge['local_b']=poly['deta']-poly['dh']
        edges.append(edge);rates.append(rate);polynomials.append(poly)
    return edges,rates,polynomials


class SmoothPressureGeometry(ReconstructedPressureGeometry):
    def __init__(self,depth,bed,dx,*,periodic):
        h=np.asarray(depth,dtype=float);b=np.asarray(bed,dtype=float)
        if (periodic is not True or h.ndim!=2 or not h.size or b.shape!=h.shape
                or not np.isfinite(h).all() or np.any(h<=0) or not np.isfinite(b).all()
                or not np.isfinite(dx) or dx<=0):
            raise ValueError('Smooth research pressure requires a positive finite periodic domain')
        self.h=h.copy();self.bed=b.copy();self.dx=float(dx);self.periodic=True
        self.pressure_trace='integrated_column';self.bed_quadrature='shared_bottom'
        self.physical_slope=geometric_bed_slope(b,dx,True)
        self.edges,_,self.polynomials=assemble(h,b,np.zeros_like(h))
        for component,edge in enumerate(self.edges):edge['physical_b']=self.physical_slope[...,component].copy()
        for array in (self.h,self.bed,self.physical_slope):array.flags.writeable=False
        for collection in (*self.edges,*self.polynomials):
            for array in collection.values():array.flags.writeable=False


class SmoothPressureGeometryRate(PressureGeometryRate):
    def __init__(self,geometry,bed,mass_rate):
        g=geometry;ht=np.asarray(mass_rate,dtype=float)
        if (not isinstance(g,SmoothPressureGeometry) or ht.shape!=g.h.shape or not np.isfinite(ht).all()
                or not np.array_equal(bed,g.bed)):
            raise ValueError('Tangent must use the same smooth geometry and original bed')
        self.geometry=g;self.source_geometry=g;self.one_sided=False
        self.mass_rate=ht.copy();self.mass_rate.flags.writeable=False
        _,self.edges,_=assemble(g.h,g.bed,ht)
        for edge in self.edges:
            for array in edge.values():array.flags.writeable=False
