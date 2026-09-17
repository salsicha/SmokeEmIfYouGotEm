from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from scipy.integrate import quad

from subcell_affine_dry_fan import AffineDryFan
from subcell_exact_geometry import clip
from test_subcell_affine_dry_fan import rectangle


def vector(r):return (r['volume_rate'],*r['momentum_rate'],r['energy_rate_per_density'])
def budget(r):return (r['volume'],*r['momentum'],r['energy_per_density'])
def magnitude(v):return -v if v<0 else v


def test_original_interface_mass_momentum_energy_and_reverse_credit():
    fan=AffineDryFan((0,0),(1,0),1,(0,F(3,10)),5,(0,0))
    a,b=(0,-F(1,2),5),(0,F(1,2),5)
    r=fan.face_flux(a,b,F(1,10));back=fan.face_flux(b,a,F(1,10))
    mass=F(8,27)*fan.c
    assert r['volume_rate']==mass
    assert r['momentum_rate']==(F(8,27)*fan.gravity,mass*F(3,10))
    assert r['energy_rate_per_density']==mass*(F(9,200)+F(2,3)*fan.gravity+5*fan.gravity)
    assert vector(back)==tuple(-x for x in vector(r))


@pytest.mark.parametrize('u',[-10,0,10])
def test_wet_fan_dry_crossings_match_independent_polynomial_quadrature(u):
    fan=AffineDryFan((0,0),(1,0),F(3,4),(u,F(1,5)),2,(F(1,4),-F(1,7)))
    t=F(1,5);a=(-3,-F(1,2),2-F(3,4)+F(1,14));b=(3,F(1,2),2+F(3,4)-F(1,14))
    r=fan.face_flux(a,b,t)
    g=float(fan.gravity);c=np.sqrt(g*.75);dt=float(t)
    an=np.array([1.,-6.]);p0=np.array(list(map(float,a)));p1=np.array(list(map(float,b)))
    def direct(s):
        p=p0+(p1-p0)*s;xi=(p[0]+g*.25*dt*dt/2)/dt
        if xi>=u+2*c:return np.zeros(4)
        if xi<=u-c:h=.75;velocity=np.array([u-g*.25*dt,.2+g*dt/7])
        else:h=(u+2*c-xi)**2/(9*g);velocity=np.array([(u+2*c+2*xi)/3-g*.25*dt,.2+g*dt/7])
        un=float(velocity@an);pressure=.5*g*h*h
        energy=h*(.5*float(velocity@velocity)+.5*g*h+g*p[2])
        return np.r_[h*un,h*velocity*un+pressure*an,un*(energy+pressure)]
    points=[((speed*dt-g*.25*dt*dt/2)+3)/6 for speed in (u-c,u+2*c)]
    expected=[quad(lambda s:direct(s)[j],0,1,points=[s for s in points if 0<s<1],epsabs=1e-11)[0] for j in range(4)]
    np.testing.assert_allclose(list(map(float,vector(r))),expected,rtol=1e-12,atol=1e-11)


@pytest.mark.parametrize('slope',[-F(1,5),0,F(1,4)])
def test_fixed_control_volume_rates_match_independent_boundary_budget_derivative(slope):
    u=F(2,5);fan=AffineDryFan((0,0),(1,0),1,(u,0),3,(slope,0));t=F(1,10)
    r=fan.boundary_rates(rectangle(slope=(slope,0),bed=3),t)
    g=fan.gravity;a=g*slope;w=u-a*t;mass=2+u*t-a*t*t/2
    assert r['volume_rate']==w
    assert r['momentum_rate']==(w*w+g/2-a*mass,0)
    assert r['energy_rate_per_density']==w*(w*w/2+g*(1+3-2*slope))


def test_local_rates_match_independent_integrated_state_time_derivative():
    fan=AffineDryFan((0,0),(3,4),F(7,10),(F(1,3),-F(1,4)),2,(F(1,5),-F(1,7)))
    fragment=rectangle(x0=-F(1,5),x1=F(2,5),slope=fan.gradient,bed=2);t=F(1,5)
    expected=vector(fan.boundary_rates(fragment,t));errors=[]
    for divisor in (100,200,400,800):
        eps=t/divisor
        a,b=budget(fan.integrate(fragment,t-eps)),budget(fan.integrate(fragment,t+eps))
        errors.append(max(abs(float((y-x)/(2*eps)-z)) for x,y,z in zip(a,b,expected)))
    assert all(a/b>3.8 for a,b in zip(errors,errors[1:]))
    assert errors[-1]<2e-5


def test_source_split_edge_subdivision_and_winding_preserve_same_conservative_rates():
    fan=AffineDryFan((0,0),(3,4),F(7,10),(F(1,3),-F(1,4)),2,(F(1,5),-F(1,7)))
    source=rectangle(slope=fan.gradient,bed=2);t=F(1,5)
    whole=fan.boundary_rates(source,t)
    parts=[fan.boundary_rates(replace(source,polygon=clip(source.polygon,0,F(1,5),side)),t) for side in (False,True)]
    assert tuple(a+b for a,b in zip(vector(parts[0]),vector(parts[1])))==vector(whole)
    assert vector(fan.boundary_rates(replace(source,polygon=tuple(reversed(source.polygon))),t))==vector(whole)
    a,b=source.polygon[:2];mid=tuple((x+y)/2 for x,y in zip(a,b))
    assert tuple(x+y for x,y in zip(vector(fan.face_flux(a,mid,t)),vector(fan.face_flux(mid,b,t))))==vector(fan.face_flux(a,b,t))


def test_energy_datum_shift_changes_flux_by_same_mass_flux():
    fan=AffineDryFan((0,0),(1,0),1,(0,0),5,(0,0));a,b=(0,-1,5),(0,1,5)
    base=fan.face_flux(a,b,F(1,10));shift=fan.face_flux(a,b,F(1,10),energy_datum=100)
    assert shift['energy_rate_per_density']==base['energy_rate_per_density']-100*fan.gravity*base['volume_rate']


def test_positive_subfloat_flux_and_common_zero_at_front_are_retained():
    fan=AffineDryFan((0,0),(1,0),F(2,10**400),(0,0),0,(0,0),gravity=1)
    r=fan.face_flux((0,0,0),(0,1,0),F(1,10**200))
    assert r['volume_rate']>0 and float(r['volume_rate'])==0
    assert r['energy_rate_per_density']>0
    dry=fan.face_flux((1,0,0),(1,1,0),F(1,10**200))
    assert vector(dry)==(0,0,0,0)


def test_invalid_edges_and_time_are_rejected():
    fan=AffineDryFan((0,0),(1,0),1,(0,0),0,(0,0))
    for a,b,t in (((0,0,0),(0,0,0),1),((0,0,0),(0,1,1),1),((0,0,0),(0,1,0),0)):
        with pytest.raises(ValueError):fan.face_flux(a,b,t)


def test_time_balance_audit_rejects_corrupted_rates_without_relaxing_gate():
    from audit_south_fork_affine_front_predictor import temporal_balance
    fan=AffineDryFan((0,0),(1,0),1,(0,0),0,(0,0));source=rectangle();t=F(1,10)
    rates=fan.boundary_rates(source,t)
    good=temporal_balance(fan,source,t,0,rates)
    assert good['passed'] and [r['divisor'] for r in good['refinements']]==[256,512]
    bad=temporal_balance(fan,source,t,0,dict(rates,volume_rate=rates['volume_rate']+1))
    assert not bad['passed'] and len(bad['refinements'])==7
    assert bad['relative_gate']==F(1,10**10)


def test_zero_scale_time_probe_does_not_hide_subfloat_ghost_water():
    from audit_south_fork_affine_front_predictor import temporal_balance
    fan=AffineDryFan((0,0),(1,0),1,(0,0),0,(0,0));source=rectangle(x0=10,x1=11);t=F(1,10)
    rates=fan.boundary_rates(source,t)
    assert vector(rates)==(0,0,0,0)
    bad=temporal_balance(fan,source,t,0,dict(rates,volume_rate=fan.zero+F(1,10**400)))
    assert not bad['passed']
    assert all(r['scaled_errors'][0] is None for r in bad['refinements'])
