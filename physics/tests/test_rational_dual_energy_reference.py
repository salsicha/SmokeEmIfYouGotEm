import numpy as np
import pytest
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_pressure_rates import PressureGeometryRate
from reconstructed_energy_reference import energy
from finite_depth_pressure_reference import response,LENGTHS,WEIGHTS
from rational_dual_energy_reference import evaluate,factor_direction
from reconstructed_acceleration_system import ReconstructedAccelerationSystem


def make(h,bed,dx=.5,periodic=True):
    return ReconstructedPressureGeometry(h,bed,dx,periodic=periodic,
        pressure_trace='integrated_column',bed_quadrature='shared_bottom')


def fixture(seed):
    rng=np.random.default_rng(seed);h=rng.uniform(.8,2.,(3,4));bed=rng.uniform(0,.15,h.shape)
    v=rng.normal(size=(*h.shape,2))*.3;ht=rng.normal(size=h.shape)*.03
    return h,bed,v,ht


def test_legendre_dual_matches_existing_inverse_response_metric():
    h,b,v,ht=fixture(6211);g=make(h,b);original=[a.copy() for a in (h,b,v,ht)]
    actual=evaluate(g,v,tangent=PressureGeometryRate(g,b,ht))
    assert actual['total']==pytest.approx(energy(g,actual['layer_velocity'],rational=True),abs=2e-12,rel=0)
    np.testing.assert_array_equal([p['length'] for p in actual['poles']],LENGTHS)
    np.testing.assert_array_equal([p['weight'] for p in actual['poles']],WEIGHTS)
    assert all(p['iterations']<=40 and p['relative_residual']<2e-5 for p in actual['poles'])
    for a,before in zip((h,b,v,ht),original):np.testing.assert_array_equal(a,before)


@pytest.mark.parametrize('seed',(6212,6213,6214))
def test_full_dual_direction_against_independent_state_finite_difference(seed):
    h,b,v,ht=fixture(seed);g=make(h,b);result=evaluate(g,v,tangent=PressureGeometryRate(g,b,ht))
    vt=np.random.default_rng(seed+100).normal(size=v.shape)*.03
    predicted=result['depth_direction']['total']+np.sum(result['canonical_gradient_flux']*vt)*g.dx**2
    errors=[]
    for epsilon in (1e-2,1e-3):
        values=[evaluate(make(h+s*epsilon*ht,b),v+s*epsilon*vt)['total'] for s in (-1,1)]
        errors.append(abs((values[1]-values[0])/(2*epsilon)-predicted))
    assert errors[-1]<2e-8 and errors[-1]<errors[0]/30


def test_factor_tangent_matches_independent_finite_difference():
    h,b,z,ht=fixture(6215);g=make(h,b);t=PressureGeometryRate(g,b,ht)
    actual=factor_direction(g,t,z)
    epsilon=1e-5
    a=ReconstructedAccelerationSystem(make(h-epsilon*ht,b),float(LENGTHS[0]))
    c=ReconstructedAccelerationSystem(make(h+epsilon*ht,b),float(LENGTHS[0]))
    for predicted,before,after in zip(actual,(a.w(z),a.v(z)),(c.w(z),c.v(z))):
        np.testing.assert_allclose(predicted,(after-before)/(2*epsilon),atol=2e-10,rtol=0)


def test_uniform_depth_retains_original_two_pole_discrete_dispersion():
    n=32;dx=.5;h=np.full((1,n),1.25);b=np.zeros_like(h)
    phase=2*np.pi*3*np.arange(n)/n;v=np.zeros((*h.shape,2));v[...,0]=np.sin(phase)
    result=evaluate(make(h,b,dx),v)
    k_discrete=np.sin(2*np.pi*3/n)/dx
    np.testing.assert_allclose(result['layer_velocity'],response(1.25*k_discrete)*v,atol=2e-13,rtol=0)


def test_missing_dry_and_open_closures_are_explicitly_rejected():
    h,b,v,ht=fixture(6216)
    with pytest.raises(ValueError):evaluate(make(h,b,periodic=False),v)
    h[0,0]=0
    with pytest.raises(ValueError):evaluate(make(h,b),v)
