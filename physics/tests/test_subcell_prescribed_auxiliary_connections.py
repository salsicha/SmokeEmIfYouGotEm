from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from scipy.integrate import quad

from subcell_affine_dry_fan import AffineDryFan
from subcell_prescribed_auxiliary_connections import PrescribedAuxiliaryConnections
from test_subcell_affine_dry_fan import rectangle
from test_subcell_affine_front_pressure import fixture
from test_subcell_front_auxiliary_transport import U, V, independent_profile, volume_quad
from test_subcell_front_profile_transport import numerical_velocity


def make(fan=None, fragments=None, time=None):
    if fan is None:
        fan,fragments,time=fixture()
    return PrescribedAuxiliaryConnections(fan,fragments,time,boundary='prescribed-fan-velocity')


def dot(a,b,z):
    return sum((x*y for x,y in zip(a,b)),z)


@pytest.mark.parametrize('method,old', (
    ('volume_connection','volume_factor_force'),
    ('factor_connection','factor_force'), ('time_connection','time_commutator')))
def test_zero_trace_reduces_exactly_to_existing_reflecting_interior(method,old):
    op=make()
    result=getattr(op,method)(U,(0,)*len(op.fluxes))
    assert result['velocity_action']==getattr(op.profile,old)(U)
    assert result['interior_work']==result['flux_coordinate_work']==0
    assert not result['advective_exterior_closure_or_coupled_pde_or_gameplay_accepted']


@pytest.mark.parametrize('method', ('volume_connection','factor_connection','time_connection'))
def test_nonzero_prescribed_ports_have_exact_self_and_bilinear_work_balance(method):
    op=make()
    qu=op.fluxes
    qv=tuple(F(i+1,13) for i in range(len(qu)))
    u,v=op.state(U,qu),op.state(V,qv)
    ru,rv=getattr(op,method)(U,qu),getattr(op,method)(V,qv)
    assert getattr(op,method)(U)==ru
    assert ru['interior_work'] != 0
    assert ru['interior_work']==-ru['flux_coordinate_work']
    assert dot(v,ru['augmented_action'],op.zero)+dot(u,rv['augmented_action'],op.zero)==0


def test_prescribed_lift_and_fixed_flux_geometry_rate_are_distinct_from_flux_rate_work():
    op=make(); g=op.geometry; state=op.state(U)
    closed=op.profile.divergence(op.profile.vector(U))
    assert op.apply_divergence(state)==tuple(a+b for a,b in zip(closed,op.trace.lift))
    fixed=op.apply_divergence(state,rate=True)
    closed_rate=op.profile.divergence(op.profile.vector(U),rate=True)
    imposed=[op.zero]*len(g.active)
    for face in op.trace.boundary_faces:
        imposed[face['row']]+=face['outward_mass_flux_rate']/g.volumes[face['row']]
    assert any(x != 0 for x in imposed)
    assert tuple(a+b for a,b in zip(fixed,imposed))==tuple(
        a+b for a,b in zip(closed_rate,op.trace.lift_rate))


def test_volume_and_shared_face_work_match_independent_profile_quadrature():
    fan,fragments,t=fixture(); op=make(fan,fragments,t)
    qu=op.fluxes; qv=tuple(F(i+1,17) for i in range(len(qu)))
    u,v=op.state(U,qu),op.state(V,qv)
    du,dv=[np.array(list(map(float,op.apply_divergence(s)))) for s in (u,v)]
    bed=np.array(fan.gradient,float)
    uu,vv=np.array(U,float),np.array(V,float)
    profile=independent_profile(fan,t)
    expected=0.
    for i,fragment in enumerate(fragments):
        def integrand(x,y,h,ht,grad):
            fu,fv=h*du[i]-1.5*(bed@uu[i]),h*dv[i]-1.5*(bed@vv[i])
            advh=numerical_velocity(fan,t,(x,y))@grad
            return .5*h*advh*(fv*du[i]-dv[i]*fu)
        expected+=volume_quad(fragment,profile,integrand)
    volume=op.volume_connection(U,qu)['augmented_action']
    assert float(dot(v,volume,op.zero))==pytest.approx(expected,abs=2e-11)
    state,cuts,n,origin=profile
    face_work=0.
    for face in op.profile.faces:
        l,r=face['left'],face['right']
        a,b=np.array(face['first'][:2],float),np.array(face['last'][:2],float)
        normal=np.array((b[1]-a[1],a[0]-b[0]))
        q0,dq=n@(a-origin),n@(b-a)
        knots=[(q-q0)/dq for q in cuts if dq and 0<(q-q0)/dq<1]
        def integrand(s):
            p=a+s*(b-a); h=state(p)[0]
            f=lambda field,div,i:h*div[i]-1.5*(bed@field[i])
            paired=f(vv,dv,l)*f(uu,du,r)-f(vv,dv,r)*f(uu,du,l)
            paired+=.75*((bed@vv[l])*(bed@uu[r])-(bed@vv[r])*(bed@uu[l]))
            return .5*h*(numerical_velocity(fan,t,p)@normal)*paired
        face_work+=quad(integrand,0,1,points=knots,epsabs=2e-12)[0]
    action=op.factor_connection(U,qu)['augmented_action']
    assert float(dot(v,tuple(a-b for a,b in zip(action,volume)),op.zero))==pytest.approx(face_work,abs=2e-11)


def test_time_connection_matches_fresh_fixed_flux_divergence_and_volume_quadrature():
    fan,fragments,t=fixture(); op=make(fan,fragments,t)
    qu=op.fluxes; qv=tuple(F(i+1,17) for i in range(len(qu)))
    u,v=op.state(U,qu),op.state(V,qv)
    du,dv=[np.array(list(map(float,op.apply_divergence(s)))) for s in (u,v)]
    step=F(1,1000000)
    before,after=make(fan,fragments,t-step),make(fan,fragments,t+step)
    # Freeze q at the central state. Taking each new fan's q(t) here would
    # test a different derivative and silently include the exterior q_t work.
    rates=[]
    for velocity,q in ((U,qu),(V,qv)):
        low=before.apply_divergence(before.state(velocity,q))
        high=after.apply_divergence(after.state(velocity,q))
        rates.append(np.array([float((b-a)/(2*step)) for a,b in zip(low,high)]))
    dtu,dtv=rates
    bed=np.array(fan.gradient,float); uu,vv=np.array(U,float),np.array(V,float)
    expected=0.
    for i,fragment in enumerate(fragments):
        def integrand(x,y,h,ht,grad):
            fu,fv=h*du[i]-1.5*(bed@uu[i]),h*dv[i]-1.5*(bed@vv[i])
            fut,fvt=ht*du[i]+h*dtu[i],ht*dv[i]+h*dtv[i]
            return .5*h*(fv*fut-fvt*fu)
        expected+=volume_quad(fragment,independent_profile(fan,t),integrand)
    actual=dot(v,op.time_connection(U,qu)['augmented_action'],op.zero)
    assert float(actual)==pytest.approx(expected,abs=2e-8)


def test_winding_dry_owners_and_subfloat_water_preserve_ports():
    fan,fragments,t=fixture()
    a=make(fan,fragments,t)
    b=make(fan,tuple(replace(f,polygon=tuple(reversed(f.polygon))) for f in fragments),t)
    assert a.fluxes==b.fluxes
    for method in ('volume_connection','factor_connection','time_connection'):
        assert getattr(a,method)(U)==getattr(b,method)(U)
    tiny=AffineDryFan((0,0),(1,0),F(1,10**400),(F(1,3),0),0,(0,0),gravity=1)
    pieces=(rectangle(x0=-2,x1=-1),rectangle(x0=4,x1=5))
    c=make(tiny,pieces,F(1,10))
    assert c.geometry.active==(0,)
    assert any(q != 0 and float(q)==0 for q in c.fluxes)
    assert c.time_connection((U[0],))['interior_work']+c.time_connection((U[0],))['flux_coordinate_work']==0
    dry=make(tiny,(pieces[1],),F(1,10))
    for method in ('volume_connection','factor_connection','time_connection'):
        assert getattr(dry,method)(())['augmented_action']==()


def test_invalid_boundary_dimensions_and_nonfinite_flux_refuse():
    fan,fragments,t=fixture(); op=make(fan,fragments,t)
    with pytest.raises(ValueError):
        PrescribedAuxiliaryConnections(fan,fragments,t,boundary='open')
    for q in ((),(0,)*(len(op.fluxes)+1),[float('nan')]*len(op.fluxes),[float('inf')]*len(op.fluxes)):
        with pytest.raises(ValueError):
            op.time_connection(U,q)
    with pytest.raises(ValueError):
        op.factor_connection((U[0],))


def test_augmented_primitives_cannot_silently_truncate_bad_vectors():
    op=make(); state=op.state(U)
    for bad in (state[:-1],state+(op.zero,),[float('nan')]*op.size):
        with pytest.raises(ValueError):
            op.apply_divergence(bad)
        with pytest.raises(ValueError):
            op.result(state,bad)
    for bad in ((),(0,)*(len(op.geometry.active)+1)):
        with pytest.raises(ValueError):
            op.transpose(bad)


def test_both_original_pressure_pole_states_keep_explicit_flux_work():
    from subcell_affine_moving_pressure import AffineMovingPressureMetric
    op=make()
    metric=AffineMovingPressureMetric.from_trace(op.trace)
    state=metric.evaluate(metric.physical_momentum(U),((0,0),(0,0)))
    assert len(state['poles'])==2
    for pole in state['poles']:
        assert pole['exact_residual_zero']
        for method in ('volume_connection','factor_connection','time_connection'):
            result=getattr(op,method)(pole['auxiliary_velocity'])
            assert result['interior_work'] != 0
            assert result['interior_work']+result['flux_coordinate_work']==0
