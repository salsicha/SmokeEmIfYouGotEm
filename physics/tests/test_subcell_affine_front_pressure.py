from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from scipy.integrate import quad

from subcell_affine_dry_fan import AffineDryFan
from subcell_affine_front_pressure import face_metric, FrontPressureGeometry
from subcell_exact_geometry import clip
from test_subcell_affine_dry_fan import rectangle


def system(fan,fragments,t):
    return FrontPressureGeometry(fan,fragments,t,outer_boundary='reflecting')


@pytest.mark.parametrize('normal',[(1,0),(3,4),(-2,1)])
def test_face_columns_and_analytic_rates_match_independent_quadrature(normal):
    fan=AffineDryFan((0,0),normal,F(3,4),(F(2,5),-F(1,7)),3,(F(1,5),-F(1,8)))
    a=(-F(3,2),-F(2,5));b=(F(3,2),F(1,3));t=F(1,5)
    xyz=lambda p:(*p,fan.bed+sum(s*x for s,x in zip(fan.gradient,p)))
    result=face_metric(fan,xyz(a),xyz(b),t)
    n=np.array(normal,float);g=float(fan.gravity);dt=float(t);depth=.75
    un=float(n@np.array(list(map(float,fan.velocity))));c=np.sqrt(g*depth*(n@n))
    acceleration=g*float(n@np.array(list(map(float,fan.gradient))))
    qa,qb=float(n@np.array(list(map(float,a)))),float(n@np.array(list(map(float,b))))
    head=(un-c)*dt-acceleration*dt*dt/2;front=(un+2*c)*dt-acceleration*dt*dt/2
    def integrand(s,rate=False):
        q=qa+(qb-qa)*s
        if q<=head:return 0. if rate else depth
        if q>=front:return 0.
        L=un+2*c-q/dt-acceleration*dt/2
        return 2*L*(q/(dt*dt)-acceleration/2)/(9*g*(n@n)) if rate else L*L/(9*g*(n@n))
    knots=[(q-qa)/(qb-qa) for q in (head,front) if 0<(q-qa)/(qb-qa)<1]
    for key,rate in [('parameter_depth_integral',False),('parameter_depth_rate',True)]:
        expected=quad(lambda s:integrand(s,rate),0,1,points=knots,epsabs=1e-12)[0]
        assert float(result[key])==pytest.approx(expected,rel=2e-13,abs=1e-13)
    reverse=face_metric(fan,xyz(b),xyz(a),t)
    for key in ('column_normal','column_normal_rate'):
        assert all(x==-y for x,y in zip(result[key],reverse[key]))
    middle=tuple((x+y)/2 for x,y in zip(xyz(a),xyz(b)))
    pieces=[face_metric(fan,xyz(a),middle,t),face_metric(fan,middle,xyz(b),t)]
    for key in ('column_normal','column_normal_rate'):
        assert tuple(x+y for x,y in zip(pieces[0][key],pieces[1][key]))==result[key]


def fixture():
    fan=AffineDryFan((0,0),(3,4),F(7,10),(F(1,3),-F(1,4)),2,(F(1,5),-F(1,7)))
    source=rectangle(x0=-F(1,5),x1=F(2,5),slope=fan.gradient,bed=2)
    fragments=tuple(replace(source,source_id=i,polygon=clip(source.polygon,0,F(1,10),side))
                    for i,side in enumerate((False,True)))
    return fan,fragments,F(1,5)


def test_shared_divergence_has_exact_mass_weighting_and_pressure_adjoint():
    fan,fragments,t=fixture();s=system(fan,fragments,t)
    common=[f for f in s.faces if len(f['owners'])==2]
    assert len(common)==1 and common[0]['parameter_depth_integral']>0
    # Off-diagonal shared weights have the same mass-weighted coefficient.
    assert s.volumes[0]*s.divergence[0][2]==-s.volumes[1]*s.divergence[1][0]
    for i in range(4):
        for j in range(4):
            assert s.kinetic[i][j]==s.kinetic[j][i]
            assert s.kinetic_rate[i][j]==s.kinetic_rate[j][i]
    u=(F(1,3),-F(2,5),F(1,7),F(2,9));v=(F(2,5),F(1,3),-F(1,4),F(3,7))
    left=sum(u[i]*s.kinetic[i][j]*v[j] for i in range(4) for j in range(4))
    right=sum(v[i]*s.kinetic[i][j]*u[j] for i in range(4) for j in range(4))
    assert left==right
    work=s.work((u[:2],u[2:]),((0,0),(0,0)))
    assert work['energy']>0 and work['local_metric_time_work']!=0 and work['divergence_time_work']!=0
    assert not work['interacting_front_or_open_boundary_or_full_dynamics_or_gameplay_accepted']


def test_complete_time_work_matches_refined_independent_energy_differences():
    fan,fragments,t=fixture();u=((F(1,3),-F(2,5)),(F(1,7),F(2,9)))
    ud=((F(2,5),F(1,3)),(-F(1,4),F(3,7)))
    work=system(fan,fragments,t).work(u,ud);errors=[]
    for divisor in (200,400,800):
        eps=t/divisor;values=[]
        for sign in (-1,1):
            shifted=tuple(tuple(x+sign*eps*y for x,y in zip(a,b)) for a,b in zip(u,ud))
            values.append(system(fan,fragments,t+sign*eps).work(shifted,((0,0),(0,0)))['energy'])
        errors.append(abs(float((values[1]-values[0])/(2*eps)-work['energy_rate'])))
    assert all(a/b>3.8 for a,b in zip(errors,errors[1:]))
    assert errors[-1]<1e-6
    # Omitting either changing geometry term must be detectable, not a pass
    # manufactured by recomputing only G_t from the volume rate.
    assert errors[-1]<abs(float(work['divergence_time_work']))/100
    assert errors[-1]<abs(float(work['local_metric_time_work']))/100


def test_hanging_original_vertices_and_winding_do_not_create_interior_walls():
    fan=AffineDryFan((0,0),(1,0),1,(0,0),0,(0,0))
    left=rectangle(x0=-1,x1=0,y0=-1,y1=1)
    right=[rectangle(x0=0,x1=1,y0=a,y1=b) for a,b in ((-1,0),(0,1))]
    s=system(fan,(left,*right),F(1,5))
    assert len([f for f in s.faces if len(f['owners'])==2])==3
    flipped=system(fan,tuple(replace(f,polygon=tuple(reversed(f.polygon))) for f in (left,*right)),F(1,5))
    assert s.divergence==flipped.divergence and s.kinetic==flipped.kinetic
    assert s.kinetic_rate==flipped.kinetic_rate


def test_dry_owners_are_absent_and_positive_subfloat_geometry_is_retained():
    fan=AffineDryFan((0,0),(1,0),F(2,10**400),(0,0),0,(0,0),gravity=1)
    wet=rectangle(x0=-1,x1=1);dry=rectangle(x0=2,x1=3)
    s=system(fan,(wet,dry),F(1,10**200))
    assert s.active==(0,) and s.volumes[0]>0 and float(s.volumes[0])==0
    work=s.work(((1,0),),((0,0),))
    assert work['energy']>0 and float(work['energy'])==0
    with pytest.raises(ValueError):s.work(((1,0),(0,0)),((0,0),(0,0)))
    empty=system(fan,(dry,),F(1,10**200))
    assert empty.active==() and empty.work((),())['energy_rate']==0


def test_wrong_plane_overlap_and_implicit_boundary_are_rejected():
    fan,fragments,t=fixture()
    with pytest.raises(ValueError,match='boundary'):FrontPressureGeometry(fan,fragments,t,outer_boundary='open')
    with pytest.raises(ValueError,match='Overlapping'):system(fan,(fragments[0],fragments[0]),t)
    original=rectangle(slope=fan.gradient,bed=2)
    with pytest.raises(ValueError,match='Overlapping'):system(fan,(original,fragments[0]),t)
    with pytest.raises(ValueError,match='affine bed'):face_metric(fan,(0,0,99),(1,0,99),t)


def test_uniform_wet_limit_retains_original_column_weighted_pressure_form():
    fan=AffineDryFan((100,0),(1,0),2,(0,0),0,(0,0))
    fragments=(rectangle(x0=0,x1=1,y0=0,y1=1),rectangle(x0=1,x1=2,y0=0,y1=1))
    s=system(fan,fragments,F(1,10))
    assert s.volumes==(2,2) and s.volume_rates==(0,0)
    assert s.divergence==[[F(1,2),0,F(1,2),0],[-F(1,2),0,-F(1,2),0]]
    for i in range(4):
        for j in range(4):
            assert s.kinetic[i][j]==(4 if i%2==j%2==0 else 0)
            assert s.kinetic_rate[i][j]==0
    assert s.work(((1,3),(2,4)),((0,0),(0,0)))['energy']==18


def test_independent_time_audit_catches_missing_divergence_work():
    from audit_south_fork_affine_front_pressure import temporal_check
    fan,fragments,t=fixture();geometry=system(fan,fragments,t)
    result=temporal_check(fan,fragments,t,geometry)
    assert result['passed'] and len(result['refinements'])>=2
    assert result['relative_gate']==F(1,10**10)
    geometry.kinetic_rate=geometry.metric_rate
    assert not temporal_check(fan,fragments,t,geometry)['passed']


def test_crossing_and_partial_source_overlap_are_rejected_without_welding():
    fan=AffineDryFan((0,0),(1,0),1,(0,0),0,(0,0))
    a=rectangle(x0=-1,x1=1,y0=-F(1,4),y1=F(1,4))
    b=rectangle(x0=-F(1,4),x1=F(1,4),y0=-1,y1=1)
    with pytest.raises(ValueError,match='Overlapping'):system(fan,(a,b),F(1,5))
    almost=replace(a,polygon=tuple((x+F(2)-F(1,10**400),y,z) for x,y,z in a.polygon))
    with pytest.raises(ValueError,match='Overlapping'):system(fan,(a,almost),F(1,5))


def test_assembled_energy_matches_independent_face_and_volume_quadrature():
    fan,fragments,t=fixture();u=np.array([[1/3,-2/5],[1/7,2/9]])
    g=9.81;dt=.2;n=np.array([3.,4.]);slope=np.array([.2,-1/7]);c=np.sqrt(g*.7*25)
    acceleration=g*float(n@slope)
    def h(x,y):
        q=3*x+4*y;xi=q/dt+acceleration*dt/2
        assert -c<xi<2*c
        return (2*c-xi)**2/(9*g*25)
    nodes,weights=np.polynomial.legendre.leggauss(4)
    energy=0.
    for owner,(x0,x1) in enumerate(((-.2,.1),(.1,.4))):
        dx=x1-x0;xc=(x0+x1)/2
        samples=[(xc+dx*a/2,b/2,dx*wa*wb/4) for a,wa in zip(nodes,weights) for b,wb in zip(nodes,weights)]
        volume=sum(h(x,y)*w for x,y,w in samples)
        corners=((x0,-.5),(x1,-.5),(x1,.5),(x0,.5));flux=0.
        for a,b in zip(corners,corners[1:]+corners[:1]):
            outward=np.array([b[1]-a[1],a[0]-b[0]])
            shared=a[0]==b[0]==.1
            difference=(u[1-owner]-u[owner])/2 if shared else -u[owner]
            column=quad(lambda s:h(a[0]+s*(b[0]-a[0]),a[1]+s*(b[1]-a[1])),0,1,epsabs=1e-13)[0]
            flux+=column*float(outward@difference)
        divergence=flux/volume;bu=float(slope@u[owner])
        energy+=sum(.5*w*h(x,y)*((h(x,y)*divergence-1.5*bu)**2+.75*bu*bu) for x,y,w in samples)
    actual=system(fan,fragments,t).work(u,((0,0),(0,0)))['energy']
    assert float(actual)==pytest.approx(energy,rel=2e-13,abs=1e-14)
