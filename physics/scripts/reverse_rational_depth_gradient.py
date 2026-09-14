"""Analytic local reverse depth derivative for the research dual energy.

Forward MC/cut branch decisions use exact represented rational inputs and
the actual supplied mass direction. Reverse accumulation uses floating
adjoints, not a bit-exact or GPU claim. Original D/E actions, poles and CG
remain untouched. Positive periodic domains only; no dry/open closure.
"""
from fractions import Fraction as F
import numpy as np
from pressure_cut_face_reference import represented_float


class Tape:
    def __init__(self):self.nodes=[]
    def node(self,value,direction=F(0),parents=()):
        node=Node(self,F(value),F(direction),parents,len(self.nodes));self.nodes.append(node);return node
    def reverse(self,seeds):
        adj=np.zeros(len(self.nodes))
        for node,weight in seeds:adj[node.index]+=weight
        for node in reversed(self.nodes):
            value=adj[node.index]
            if value:
                for parent,partial in node.parents:
                    adj[parent.index]+=value*represented_float(partial)
        if not np.isfinite(adj).all():raise ValueError('Reverse derivative exceeds storage range')
        return adj


class Node:
    def __init__(self,tape,value,direction,parents,index):
        self.tape,self.value,self.direction,self.parents,self.index=tape,value,direction,parents,index
    def coerce(self,other):return other if isinstance(other,Node) else self.tape.node(other)
    def __add__(self,other):
        b=self.coerce(other)
        return self.tape.node(self.value+b.value,self.direction+b.direction,((self,F(1)),(b,F(1))))
    __radd__=__add__
    def __neg__(self):return self.tape.node(-self.value,-self.direction,((self,F(-1)),))
    def __sub__(self,other):return self+-self.coerce(other)
    def __rsub__(self,other):return self.coerce(other)+-self
    def __mul__(self,other):
        b=self.coerce(other)
        return self.tape.node(self.value*b.value,self.direction*b.value+self.value*b.direction,
            ((self,b.value),(b,self.value)))
    __rmul__=__mul__
    def __truediv__(self,other):
        b=self.coerce(other)
        if not b.value:raise ValueError('Unsupported zero column in positive reverse control')
        return self.tape.node(self.value/b.value,(self.direction*b.value-self.value*b.direction)/(b.value*b.value),
            ((self,1/b.value),(b,-self.value/(b.value*b.value))))
    @property
    def key(self):return self.value,self.direction


def limited(back,front):
    candidates=(2*back,(back+front)/2,2*front);zero=(F(0),F(0))
    if all(c.key>=zero for c in candidates):return min(candidates,key=lambda c:c.key)
    if all(c.key<=zero for c in candidates):return max(candidates,key=lambda c:c.key)
    return back.tape.node(0)


def positive(node):return node if node.key>(F(0),F(0)) else node.tape.node(0)


def coefficient_reverse(geometry,mass_direction,adjoints,*,polynomial_builder=None):
    g=geometry;h=g.h;ht=np.asarray(mass_direction,dtype=float)
    if not g.periodic or np.any(h<=0) or ht.shape!=h.shape or not np.isfinite(ht).all():
        raise ValueError('Reverse control requires positive periodic original depth/direction')
    tape=Tape();depth={p:tape.node(float(h[p]),float(ht[p])) for p in np.ndindex(h.shape)}
    seeds=[];discrepancy={key:0. for key in ('aa','ab','own','other','shared_b')}
    for component,axis in enumerate((1,0)):
        n=h.shape[axis]
        if n==1:continue
        polys={}
        for p in np.ndindex(h.shape):
            if polynomial_builder is not None:
                polys[p]=polynomial_builder(depth,g,axis,p)
                continue
            a=list(p);b=list(p);a[axis]=(p[axis]-1)%n;b[axis]=(p[axis]+1)%n;a=tuple(a);b=tuple(b)
            back=depth[p]-depth[a];front=depth[b]-depth[p]
            dh=limited(back,front)
            de=limited(back+(F(float(g.bed[p]))-F(float(g.bed[a]))),
                front+(F(float(g.bed[b]))-F(float(g.bed[p]))))
            polys[p]=(dh,de)
        for p in np.ndindex(h.shape):
            q=list(p);q[axis]=(p[axis]+1)%n;q=tuple(q)
            hi,hj=depth[p],depth[q];dhi,dei=polys[p];dhj,dej=polys[q]
            ha=hi+dhi/2;hb=hj-dhj/2
            jump=(F(float(g.bed[q]))-F(float(g.bed[p])))-(dei-dhi+dej-dhj)/2
            fa=positive(ha-positive(jump));fb=positive(hb-positive(-jump))
            def cut(height,retained):
                if height.value<=0:raise ValueError('Positive owner has unsupported reconstructed column')
                r=retained/height
                return r*r*(3-2*r),-height*r*r*(1-r)
            aa,ca=cut(ha,fa);ab,cb=cut(hb,fb)
            own=hi/(hi+hj);other=hj/(hi+hj)
            values=dict(aa=aa,ab=ab,own=own,other=other,shared_b=own*other*(cb-ca))
            for key,node in values.items():
                seeds.append((node,float(adjoints[component][key][p])))
                discrepancy[key]=max(discrepancy[key],abs(represented_float(node.value)-g.edges[component][key][p]))
    adj=tape.reverse(seeds)
    result=np.empty_like(h)
    for p,node in depth.items():result[p]=adj[node.index]
    return result,dict(tape_nodes=len(tape.nodes),coefficient_value_discrepancy=discrepancy)


def depth_gradient(geometry,canonical_velocity,response,mass_direction,*,reverse_coefficients=None):
    """Energy density derivative; cell area is applied by the caller's dot product."""
    g=geometry;h=g.h
    if not g.periodic or np.any(h<=0):raise ValueError('Positive periodic reverse domain required')
    root=np.sqrt(h);v=np.asarray(canonical_velocity,dtype=float)
    if v.shape!=(*h.shape,2) or not np.isfinite(v).all():raise ValueError('Invalid canonical field')
    a=.5*np.sum(v*response['layer_velocity'],axis=-1)+9.81*(h+g.bed)
    terms=[(pole['normalized_auxiliary_velocity'],-pole['weight']*pole['length']) for pole in response['poles']]
    return factor_depth_gradient(g,mass_direction,terms,a,reverse_coefficients=reverse_coefficients)


def factor_depth_gradient(geometry,mass_direction,terms,base,*,reverse_coefficients=None):
    """Accumulate sum(scale*(Wz.W_tz+.75*Vz.V_tz)) into a depth gradient.

    Signed coefficients describe an energy derivative, not replacement poles.
    The original dual caller supplies -weight*length; the equivalent primal
    energy supplies positive partial-fraction coefficients. Same local reverse.
    """
    g=geometry;h=g.h;root=np.sqrt(h)
    if not g.periodic or np.any(h<=0):raise ValueError('Positive periodic factor reverse domain required')
    a=np.array(g._scalar(base),copy=True)
    adjoints=[{key:np.zeros_like(h) for key in ('aa','ab','own','other','shared_b')} for _ in (0,1)]
    for z,scale in terms:
        z=np.asarray(z,dtype=float)
        if z.shape!=(*h.shape,2) or not np.isfinite(z).all() or not np.isfinite(scale):
            raise ValueError('Invalid normalized energy factor')
        u=z/root[...,None]
        d,e=g.kinematic_components(u);w=root*(h*d-1.5*e);vv=root*e
        ad=scale*root*h*w;ae=scale*root*(-1.5*w+.75*vv)
        # L(-ad,ae)=D.T*ad+E.T*ae, including the original physical bed slope.
        adj_u=g.gradient_traction(-ad,ae)
        a+=scale*((w*w+.75*vv*vv)/(2*h)+w*root*d)-np.sum(adj_u*u,axis=-1)/(2*h)
        for component,(axis,edge) in enumerate(zip((1,0),g.edges)):
            ui=u[...,component];uj=np.roll(ui,-1,axis)
            face=edge['own']*ui+edge['other']*uj
            ddi=np.roll(ad,-1,axis);eei=np.roll(ae,-1,axis)
            common=(ad*edge['aa']-ddi*edge['ab'])/g.dx
            adjoints[component]['aa']+=ad*face/g.dx
            adjoints[component]['ab']-=ddi*face/g.dx
            adjoints[component]['own']+=common*ui
            adjoints[component]['other']+=common*uj
            adjoints[component]['shared_b']+=(ae-eei)*(uj-ui)/g.dx
    reverse=coefficient_reverse if reverse_coefficients is None else reverse_coefficients
    contribution,detail=reverse(g,mass_direction,adjoints)
    result=a+contribution
    if not np.isfinite(result).all():raise ValueError('Reverse depth gradient exceeds storage range')
    return result,detail
