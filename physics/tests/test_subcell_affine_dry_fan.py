from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from scipy.integrate import quad

from subcell_affine_dry_fan import Radical, AffineDryFan
from subcell_exact_geometry import SourceFragment, clip


def rectangle(x0=-2,x1=2,y0=-F(1,2),y1=F(1,2),slope=(0,0),bed=0):
    return SourceFragment(11,tuple((F(x),F(y),F(bed)+F(slope[0])*x+F(slope[1])*y)
                                  for x,y in ((x0,y0),(x1,y0),(x1,y1),(x0,y1))),tuple(map(F,slope)))


def test_quadratic_field_predicates_and_division_are_exact_without_cancellation():
    x=Radical(2,0,1)
    assert x*x==2 and x/2==1/x
    assert x>1 and x<2 and -x<-1
    for a,b in ((3,-2),(-3,2),(1,1),(-1,-1),(0,1),(1,0)):
        v=Radical(2,a,b)
        assert v/v==1 and (v>0)==(float(v)>0)
    assert Radical(F(9,4),2,4)==8
    with pytest.raises(ZeroDivisionError): x/0
    with pytest.raises(ValueError): x+Radical(3,0,1)
    tiny=F(1,10**400)
    assert Radical(2,tiny)>0 and float(Radical(2,tiny))==0


@pytest.mark.parametrize('u',[-10,0,F(2,5),10])
def test_branches_keep_original_depth_and_physical_rarefaction(u):
    fan=AffineDryFan((0,0),(1,0),1,(u,F(3,10)),0,(0,0))
    t=F(1,10);c=float(fan.c)
    for xi in (float(u)-c-1,float(u)-c/2,float(u)+c,float(u)+2*c+1):
        h,v=fan.state((F(float(t)*xi),0),t)
        if xi<float(u)-c:
            assert h==1 and v[0]==u
        elif xi>float(u)+2*c:
            assert h==0 and v==(0,0)
        else:
            np.testing.assert_allclose(float(h),(float(u)+2*c-xi)**2/(9*9.81),rtol=1e-14)
            np.testing.assert_allclose(float(v[0]),(float(u)+2*c+2*xi)/3,rtol=1e-14)
            assert v[1]==F(3,10)


def test_donor_loss_and_dry_gain_share_mass_momentum_and_energy():
    fan=AffineDryFan((0,0),(1,0),1,(0,F(3,10)),5,(0,0))
    t=F(1,10);whole=rectangle(bed=5)
    left=replace(whole,polygon=clip(whole.polygon,0,F(0),False))
    right=replace(whole,polygon=clip(whole.polygon,0,F(0),True))
    before=fan.integrate(whole,0);a=fan.integrate(left,t);b=fan.integrate(right,t)
    assert b['volume']==F(8,27)*fan.c*t
    assert a['volume']+b['volume']==before['volume']
    assert a['momentum'][0]+b['momentum'][0]-before['momentum'][0]==fan.gravity*t/2
    assert a['momentum'][1]+b['momentum'][1]==before['momentum'][1]
    assert a['energy_per_density']+b['energy_per_density']==before['energy_per_density']
    # Same existing instantaneous interface law integrated for the homogeneous case.
    assert b['momentum'][0]==F(8,27)*fan.gravity*t
    assert b['energy_per_density']==b['volume']*(F(9,200)+F(2,3)*fan.gravity+5*fan.gravity)


@pytest.mark.parametrize('slope',[-F(1,5),F(1,4)])
@pytest.mark.parametrize('u',[0,F(2,5),-F(1,2)])
def test_finite_affine_bed_budgets_match_independent_boundary_and_bed_integrals(slope,u):
    fan=AffineDryFan((0,0),(1,0),1,(u,0),3,(slope,0))
    t=F(1,10);g=fan.gravity;a=g*slope;L=F(2)
    fragment=rectangle(slope=(slope,0),bed=3)
    before=fan.integrate(fragment,0);after=fan.integrate(fragment,t)
    # Until both ends remain outside the fan, integrate known uniform upstream
    # fluxes at x=-L and -g*slope*total volume(t) over the fixed control volume.
    inflow=u*t-a*t*t/2
    pressure_advection=u*u*t-u*a*t*t+a*a*t**3/3+g*t/2
    bed_impulse=-a*(L*t+u*t*t/2-a*t**3/6)
    energy_in=(u**3*t-3*u*u*a*t*t/2+u*a*a*t**3-a**3*t**4/4)/2
    energy_in+=g*(1+3-slope*L)*inflow
    assert after['volume']-before['volume']==inflow
    assert after['momentum'][0]-before['momentum'][0]==pressure_advection+bed_impulse
    assert after['energy_per_density']-before['energy_per_density']==energy_in
    assert after['bed_force'][0]==-a*after['volume']


def test_actual_state_satisfies_two_dimensional_swe_with_affine_bed():
    fan=AffineDryFan((0,0),(3,4),F(7,10),(F(1,3),-F(1,4)),2,(F(1,5),-F(1,7)))
    def quantities(x,y,t):
        h,v=fan.state((x,y),t);h=float(h);v=np.array(list(map(float,v)))
        q=np.r_[h,h*v]
        flux=[np.r_[h*v[j],h*v*v[j]+.5*float(fan.gravity)*h*h*np.eye(2)[j]] for j in range(2)]
        return q,flux
    errors=[]
    x,y,t=.04,.02,.2
    for eps in (1e-3,5e-4,2.5e-4):
        qt=(quantities(x,y,t+eps)[0]-quantities(x,y,t-eps)[0])/(2*eps)
        dx=(quantities(x+eps,y,t)[1][0]-quantities(x-eps,y,t)[1][0])/(2*eps)
        dy=(quantities(x,y+eps,t)[1][1]-quantities(x,y-eps,t)[1][1])/(2*eps)
        q,_=quantities(x,y,t)
        residual=qt+dx+dy+np.r_[0,float(fan.gravity)*q[0]*np.array(list(map(float,fan.gradient)))]
        errors.append(np.linalg.norm(residual))
    assert all(a/b>3.9 for a,b in zip(errors,errors[1:]))
    assert errors[-1]<2e-5


def test_source_partition_rotation_normal_scaling_and_energy_datum():
    fan=AffineDryFan((0,0),(1,0),1,(F(1,3),F(1,5)),3,(F(1,4),F(1,7)))
    fragment=rectangle(slope=fan.gradient,bed=3);t=F(1,10)
    whole=fan.integrate(fragment,t)
    parts=[fan.integrate(replace(fragment,polygon=clip(fragment.polygon,0,F(1,10),side)),t) for side in (False,True)]
    for key in ('volume','energy_per_density'):
        assert parts[0][key]+parts[1][key]==whole[key]
    assert all(parts[0]['momentum'][j]+parts[1]['momentum'][j]==whole['momentum'][j] for j in range(2))
    move=lambda p:(-p[1]+F(10**12),p[0]-F(10**12),p[2]+F(10**15))
    rotated=replace(fragment,polygon=tuple(move(p) for p in reversed(fragment.polygon)),gradient=(-fan.gradient[1],fan.gradient[0]))
    other=AffineDryFan((10**12,-10**12),(0,1),1,(-fan.velocity[1],fan.velocity[0]),3+10**15,rotated.gradient)
    moved=other.integrate(rotated,t,energy_datum=10**15)
    assert moved['volume']==whole['volume'] and moved['energy_per_density']==whole['energy_per_density']
    assert moved['momentum']==(-whole['momentum'][1],whole['momentum'][0])
    shifted=fan.integrate(fragment,t,energy_datum=12)
    assert shifted['energy_per_density']==whole['energy_per_density']-12*fan.gravity*whole['volume']
    scaled=AffineDryFan((0,0),(5,0),1,fan.velocity,3,fan.gradient).integrate(fragment,t)
    # Equivalent radical fields have different radicands; compare expanded
    # coefficients after sqrt(25*d)=5*sqrt(d), without floating conversion.
    for key in ('volume','energy_per_density'):
        assert scaled[key].a==whole[key].a and 5*scaled[key].b==whole[key].b


def test_positive_subfloat_fan_mass_is_not_deleted():
    fan=AffineDryFan((0,0),(1,0),F(1,10**400),(0,0),0,(0,0),gravity=1)
    r=fan.integrate(rectangle(x0=0,x1=1),F(1,10**200))
    assert r['volume']>0 and float(r['volume'])==0
    assert r['energy_per_density']>0
    assert not r['spatially_varying_or_dispersive_or_gameplay_accepted']


def test_irrational_tiny_wave_speed_is_not_rounded_before_state_or_budget():
    fan=AffineDryFan((0,0),(1,0),F(2,10**400),(0,0),0,(0,0),gravity=1)
    assert 0<float(fan.c)<2e-200
    r=fan.integrate(rectangle(x0=0,x1=1),F(1,10**200))
    assert r['volume']>0 and float(r['volume'])==0


def test_integrated_shape_matches_independent_direct_depth_quadrature():
    fan=AffineDryFan((0,0),(1,0),F(3,4),(F(2,5),0),2,(F(1,5),0))
    t=.2;c=np.sqrt(9.81*.75);a=9.81*.2
    head=(.4-c)*t-a*t*t/2;front=(.4+2*c)*t-a*t*t/2
    def h(x):
        if x<=head:return .75
        if x>=front:return 0
        xi=(x+a*t*t/2)/t
        return (.4+2*c-xi)**2/(9*9.81)
    expected=quad(h,-.2,.7,points=[p for p in (head,front) if -.2<p<.7],epsabs=1e-13)[0]
    r=fan.integrate(rectangle(x0=F(-1,5),x1=F(7,10),slope=(F(1,5),0),bed=2),F(1,5))
    np.testing.assert_allclose(float(r['volume']),expected,rtol=1e-13,atol=1e-14)


def test_invalid_state_and_original_bed_changes_reject():
    for depth,normal in ((0,(1,0)),(-1,(1,0)),(1,(0,0)),(float('nan'),(1,0))):
        with pytest.raises(ValueError): AffineDryFan((0,0),normal,depth,(0,0),0,(0,0))
    fan=AffineDryFan((0,0),(1,0),1,(0,0),0,(0,0))
    with pytest.raises(ValueError): fan.integrate(rectangle(),-1)
    with pytest.raises(ValueError,match='different original affine'): fan.integrate(rectangle(slope=(1,0)),F(1,10))
    concave=SourceFragment(1,((0,0,0),(2,0,0),(1,F(1,2),0),(2,1,0),(0,1,0)),(0,0))
    with pytest.raises(ValueError,match='Convex original'):fan.integrate(concave,F(1,10))
