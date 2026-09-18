"""Shared pressure geometry and physical-time work of one evolving dry fan.

Uses the existing depth-weighted intercell divergence and vertical kinetic
Gram form, now on the actual quadratic-depth profile. Exact source edges are
split at original vertices, never welded through projected coordinates. This
is a pressure-geometry component, not an interacting-front/open-river solver.
Reflecting outer pressure boundaries must be explicitly requested.
"""
from fractions import Fraction as F

from subcell_affine_dry_fan import _line_integral, _clip
from subcell_affine_front_metric import front_metric


def face_metric(fan, first, last, time):
    """Integral of h and h_t times the directed edge normal and length.

    Parametric integration avoids taking a rounded length/unit normal. Moving
    dry-edge terms vanish and fan-head terms cancel because depth is continuous.
    A reversed edge gives exactly the opposite column and column-time rate.
    """
    a,b=tuple(map(F,first)),tuple(map(F,last));t=F(time)
    if len(a)!=3 or len(b)!=3 or a[:2]==b[:2] or t<=0:
        raise ValueError('Distinct original XYZ endpoints and positive time required')
    if any(p[2]!=fan.bed+sum(s*(x-o) for s,x,o in zip(fan.gradient,p,fan.origin)) for p in (a,b)):
        raise ValueError('Pressure face leaves the original affine bed')
    head,front,linear,_,_=fan._profile(t)
    acceleration=fan.gravity*sum(n*s for n,s in zip(fan.normal,fan.gradient))
    linear_rate=lambda p:fan._coordinate(p)/(t*t)-acceleration/2
    qa,qb=fan._coordinate(a),fan._coordinate(b)
    cuts=[fan.zero,fan.zero+1]
    if qa!=qb:
        for bound in (head,front):
            value=(bound-qa)/(qb-qa)
            if 0<value<1:cuts.append(value)
    point=lambda s:tuple(x+(y-x)*s for x,y in zip(a,b))
    integral=rate=fan.zero
    cuts=sorted(cuts)
    for low,high in zip(cuts,cuts[1:]):
        q=fan._coordinate(point((low+high)/2))
        if q>=front:continue
        if q<=head:
            integral+=(high-low)*fan.depth
        else:
            ends=(point(low),point(high));coefficient=F(1,9)/(fan.gravity*fan.norm2)
            integral+=(high-low)*coefficient*_line_integral(ends,[linear,linear],fan.zero)
            rate+=2*(high-low)*coefficient*_line_integral(ends,[linear,linear_rate],fan.zero)
    normal=(b[1]-a[1],a[0]-b[0])
    return dict(parameter_depth_integral=integral,parameter_depth_rate=rate,
                column_normal=tuple(n*integral for n in normal),
                column_normal_rate=tuple(n*rate for n in normal))


def _edges(fragments):
    """Exact conforming source-edge membership, including hanging vertices."""
    for i,fragment in enumerate(fragments):
        for other in fragments[:i]:
            polygon=fragment.polygon;boundary=other.polygon
            orientation=sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(boundary,boundary[1:]+boundary[:1]))
            for a,b in zip(boundary,boundary[1:]+boundary[:1]):
                polygon=_clip(polygon,lambda p:(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]),orientation>0)
            if sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(polygon,polygon[1:]+polygon[:1]))!=0:
                raise ValueError('Overlapping original source interiors')
    vertices=set(p for f in fragments for p in f.polygon)
    membership={}
    for owner,fragment in enumerate(fragments):
        polygon=fragment.polygon
        signed=sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(polygon,polygon[1:]+polygon[:1]))
        if signed<0:polygon=tuple(reversed(polygon))
        for a,b in zip(polygon,polygon[1:]+polygon[:1]):
            if a[:2]==b[:2]:continue
            axis=0 if a[0]!=b[0] else 1
            cuts={F(0),F(1)}
            for p in vertices:
                s=(p[axis]-a[axis])/(b[axis]-a[axis])
                if 0<s<1 and all(p[j]==a[j]+s*(b[j]-a[j]) for j in range(3)):cuts.add(s)
            points=[tuple(x+s*(y-x) for x,y in zip(a,b)) for s in sorted(cuts)]
            for first,last in zip(points,points[1:]):
                key=tuple(sorted((first,last)))
                owners=membership.setdefault(key,[])
                if owners and (len(owners)>1 or owners[0][1:]==(first,last)):
                    raise ValueError('Overlapping or nonmanifold original source edges')
                owners.append((owner,first,last))
    return tuple(tuple(owners) for owners in membership.values())


def _zero_matrix(n,zero):
    return [[zero for _ in range(n)] for _ in range(n)]


class FrontPressureGeometry:
    """K=J^T G J and its complete time derivative, before mass normalization.

    G retains all actual depth moments. J contains the common column-weighted
    divergence plus the two velocity components. Both J_t and G_t contribute;
    replacing G_t by a hydrostatic volume derivative is not valid for a fan.
    Dry source fragments own no unknown and are never assigned a dry velocity.
    """
    def __init__(self, fan, fragments, time, *, outer_boundary):
        if outer_boundary!='reflecting':
            raise ValueError('Explicit reflecting pressure boundary required; open closure is not supplied')
        self.fragments=tuple(fragments)
        if not self.fragments:raise ValueError('Original source fragments required')
        self.forms=tuple(front_metric(fan,f,time) for f in self.fragments)
        self.active=tuple(i for i,f in enumerate(self.forms) if f['depth_moments'][1]>0)
        positions={owner:i for i,owner in enumerate(self.active)}
        self.volumes=tuple(self.forms[i]['depth_moments'][1] for i in self.active)
        self.volume_rates=tuple(self.forms[i]['depth_moment_rates'][0] for i in self.active)
        n=len(self.active);zero=fan.zero;self.zero=zero
        self.divergence=[[zero]*(2*n) for _ in range(n)]
        self.divergence_rate=[[zero]*(2*n) for _ in range(n)]
        self.edges=_edges(self.fragments)
        self.faces=[]
        for owners in self.edges:
            left,a,b=owners[0];face=face_metric(fan,a,b,time)
            self.faces.append(dict(owners=tuple(o[0] for o in owners),first=a,last=b,**face))
            if face['parameter_depth_integral']==0:
                if face['parameter_depth_rate']!=0:raise ValueError('Dry pressure support has a nonzero time rate')
                continue
            if any(o[0] not in positions for o in owners):
                raise ValueError('Positive face column lacks positive source volume')
            li=positions[left]
            # Same fan has the same trace on both sides: its harmonic column
            # is exactly h, not an independently fitted mean-depth substitute.
            for owner,_,_ in owners:
                row=positions[owner];v=self.volumes[row];vd=self.volume_rates[row]
                divisor=2 if len(owners)==2 else 1
                for axis in range(2):
                    area=face['column_normal'][axis];ad=face['column_normal_rate'][axis]
                    weight=area/(divisor*v);wd=(ad-area*vd/v)/(divisor*v)
                    self.divergence[row][2*li+axis]-=weight
                    self.divergence_rate[row][2*li+axis]-=wd
                    if len(owners)==2:
                        ri=positions[owners[1][0]]
                        self.divergence[row][2*ri+axis]+=weight
                        self.divergence_rate[row][2*ri+axis]+=wd
        self.kinetic=_zero_matrix(2*n,zero)
        self.kinetic_rate=_zero_matrix(2*n,zero)
        self.metric_rate=_zero_matrix(2*n,zero)
        self.divergence_geometry_rate=_zero_matrix(2*n,zero)
        for row,owner in enumerate(self.active):
            j=[self.divergence[row][:],[zero]*(2*n),[zero]*(2*n)]
            jd=[self.divergence_rate[row][:],[zero]*(2*n),[zero]*(2*n)]
            j[1][2*row]=zero+1;j[2][2*row+1]=zero+1
            g=self.forms[owner]['gram'];gd=self.forms[owner]['gram_rate']
            for a in range(2*n):
                for b in range(2*n):
                    value=sum((j[k][a]*g[k][l]*j[l][b] for k in range(3) for l in range(3)),zero)
                    metric=sum((j[k][a]*gd[k][l]*j[l][b] for k in range(3) for l in range(3)),zero)
                    geometry=sum((jd[k][a]*g[k][l]*j[l][b]+j[k][a]*g[k][l]*jd[l][b]
                                  for k in range(3) for l in range(3)),zero)
                    self.kinetic[a][b]+=value
                    self.metric_rate[a][b]+=metric
                    self.divergence_geometry_rate[a][b]+=geometry
                    self.kinetic_rate[a][b]+=metric+geometry

    def work(self, velocity, velocity_rate):
        """Complete kinetic work in physical velocity coordinates; no PDE fix."""
        velocity=tuple(tuple(pair) for pair in velocity)
        velocity_rate=tuple(tuple(pair) for pair in velocity_rate)
        u=tuple(F(x) for pair in velocity for x in pair)
        ud=tuple(F(x) for pair in velocity_rate for x in pair)
        n=2*len(self.active)
        if len(u)!=n or len(ud)!=n or any(len(pair)!=2 for pair in (*velocity,*velocity_rate)):
            raise ValueError('Two velocity components per active original source required')
        contract=lambda a,m,b:sum((a[i]*m[i][j]*b[j] for i in range(n) for j in range(n)),self.zero)
        energy=contract(u,self.kinetic,u)/2
        metric=contract(u,self.metric_rate,u)/2
        geometry=contract(u,self.divergence_geometry_rate,u)/2
        velocity_work=contract(ud,self.kinetic,u)
        if energy<0:raise ValueError('Negative original pressure kinetic form')
        return dict(energy=energy,local_metric_time_work=metric,divergence_time_work=geometry,
                    velocity_time_work=velocity_work,energy_rate=metric+geometry+velocity_work,
                    interacting_front_or_open_boundary_or_full_dynamics_or_gameplay_accepted=False)
