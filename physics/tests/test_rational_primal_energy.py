"""Same-metric inverse factors, not new physics/flux acceptance."""
import numpy as np
import pytest
from rational_primal_energy import evaluate,depth_gradient,K0,BETAS,ALPHAS
from rational_dual_energy_reference import evaluate as dual
from finite_depth_pressure_reference import LENGTHS,WEIGHTS
from reconstructed_energy_reference import metric
from smooth_rational_velocity_stage import make
from smooth_pressure_geometry import SmoothPressureGeometryRate


def test_scalar_inverse_of_original_response():
    x=np.r_[0.,np.logspace(-12,12,161)]
    original=1-float(WEIGHTS.sum())+sum(w/(1+l*x) for w,l in zip(WEIGHTS,LENGTHS))
    inverse=K0+sum(a*x/(1+b*x) for a,b in zip(ALPHAS,BETAS))
    np.testing.assert_allclose(inverse*original,1.,rtol=0,atol=2e-14)
    assert min(*ALPHAS,*BETAS,K0)>0


@pytest.mark.parametrize('shape',((3,4),(1,19),(9,2)))
def test_original_dense_metric_and_fixed_physical_gradient(shape):
    rng=np.random.default_rng(9601);h=1+rng.random(shape);b=.2*rng.normal(size=shape)
    p=.4*rng.normal(size=(*shape,2));ht=.1*rng.normal(size=shape);g=make(h,b,.5)
    tangent=SmoothPressureGeometryRate(g,b,ht);r=evaluate(g,p,tangent=tangent)
    k,kt=metric(g,tangent,rational=True);q=(p/np.sqrt(h)[...,None]).ravel()
    expected_v=(k@q).reshape(p.shape)/np.sqrt(h)[...,None]
    np.testing.assert_allclose(r['canonical_velocity'],expected_v,rtol=1e-11,atol=1e-11)
    expected=(.5*q@k@q+np.sum(9.81*h*(.5*h+b)))*.25
    assert abs(r['total']-expected)<1e-10
    assert np.min(r['kinetic_density'])>=0
    assert r['positive_energy_contraction_error']<1e-10
    a,_=depth_gradient(g,p,r,ht)
    assert abs(np.sum(a*ht)*.25-r['depth_direction']['total'])<1e-10
    qt=(-.5*(ht/h)[...,None]*p/np.sqrt(h)[...,None]).ravel()
    dense_direction=(qt@k@q+.5*q@kt@q+np.sum(9.81*(h+b)*ht))*.25
    assert abs(r['depth_direction']['total']-dense_direction)<1e-10
    eps=1e-5
    values=[evaluate(make(h+sign*eps*ht,b,.5),p)['total'] for sign in (-1,1)]
    assert abs((values[1]-values[0])/(2*eps)-dense_direction)<1e-7
    recovered=dual(g,r['canonical_velocity'],preconditioner='patch')['canonical_gradient_flux']
    np.testing.assert_allclose(recovered,p,rtol=1e-11,atol=1e-11)


@pytest.mark.parametrize('seed',(7325,7326))
def test_original_rough_blocked_pressure_columns(seed):
    rng=np.random.default_rng(seed);h=np.exp(rng.uniform(np.log(.01),np.log(.5),(3,4)))
    b=rng.uniform(0,2.,h.shape);g=make(h,b,.5);p=h[...,None]*rng.normal(size=(*h.shape,2))*.03
    r=evaluate(g,p);k,_=metric(g,rational=True);q=(p/np.sqrt(h)[...,None]).ravel()
    np.testing.assert_allclose(r['canonical_velocity'],(k@q).reshape(p.shape)/np.sqrt(h)[...,None],rtol=1e-11,atol=1e-11)


def test_flat_constant_physical_velocity_and_input_rejection():
    h=np.array([[1.,2.,4.]]);g=make(h,np.zeros_like(h),.5);p=h[...,None]*np.array([.3,-.2])
    r=evaluate(g,p)
    np.testing.assert_allclose(r['canonical_velocity'],np.broadcast_to([.3,-.2],p.shape),rtol=0,atol=1e-12)
    with pytest.raises(ValueError):evaluate(g,np.zeros((3,2)))
    with pytest.raises(ValueError):evaluate(g,p,preconditioner='shift')
