import numpy as np
import pytest
from smooth_pressure_geometry import SmoothPressureGeometry as Geometry,SmoothPressureGeometryRate as Rate
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from smooth_pressure_reverse import smooth_coefficient_reverse
from reverse_rational_depth_gradient import depth_gradient
from rational_dual_energy_reference import evaluate


@pytest.mark.parametrize('shape',[(3,4),(1,7),(2,4)])
def test_geometry_moments_adjoint_and_independent_tangent(shape):
    rng=np.random.default_rng(10101);h=rng.uniform(.8,2.,shape);b=rng.uniform(0,.2,shape);g=Geometry(h,b,.5,periodic=True)
    u=rng.normal(size=(*shape,2));p=rng.normal(size=shape);q=rng.normal(size=shape)
    d,e=g.kinematic_components(u)
    assert abs(np.sum(g.gradient_traction(p,q)*u)-np.sum(-p*d+q*e))<2e-13
    _,ones=g.kinematic_components(np.ones_like(u))
    np.testing.assert_allclose(ones,g.physical_slope.sum(axis=-1),atol=2e-14,rtol=0)
    ht=rng.normal(size=shape)*.02;t=Rate(g,b,ht);eps=1e-5
    ga=Geometry(h-eps*ht,b,.5,periodic=True);gb=Geometry(h+eps*ht,b,.5,periodic=True)
    for axis in (0,1):
        for key in t.edges[axis]:
            np.testing.assert_allclose((gb.edges[axis][key]-ga.edges[axis][key])/(2*eps),t.edges[axis][key],atol=2e-10,rtol=0)


def test_reverse_gradient_agrees_with_independent_direction_and_basis():
    rng=np.random.default_rng(10102);h=rng.uniform(.8,2.,(3,4));b=rng.uniform(0,.2,h.shape)
    v=rng.normal(size=(*h.shape,2))*.2;ht=rng.normal(size=h.shape)*.02;g=Geometry(h,b,.5,periodic=True)
    a,_=depth_gradient(g,v,evaluate(g,v),ht,reverse_coefficients=smooth_coefficient_reverse)
    for point in np.ndindex(h.shape):
        basis=np.zeros_like(h);basis[point]=1.
        expected=evaluate(g,v,tangent=Rate(g,b,basis))['depth_direction']['total']/.25
        assert abs(a[point]-expected)<3e-12


def test_flat_bed_original_operators_and_positive_columns_at_large_contrast():
    h=np.array([[1.,2.**-500,3.,.001,4.,2.,7.]])
    b=np.zeros_like(h);g=Geometry(h,b,.5,periodic=True)
    for p in g.polynomials:
        assert np.all(p['hm']>=.5*h) and np.all(p['hp']>=.5*h)
    # Regular flat-bed control: same original integrated pressure actions.
    h=np.array([[1.,1.2,1.4,1.3,1.1,1.,.9]])
    g=Geometry(h,b,.5,periodic=True)
    old=ReconstructedPressureGeometry(h,b,.5,periodic=True,pressure_trace='integrated_column',bed_quadrature='shared_bottom')
    rng=np.random.default_rng(10103);u=rng.normal(size=(*h.shape,2))
    for actual,expected in zip(g.kinematic_components(u),old.kinematic_components(u)):
        np.testing.assert_array_equal(actual,expected)
    with pytest.raises(ValueError,match='positive'):Geometry(np.zeros_like(h),b,.5,periodic=True)
    with pytest.raises(ValueError,match='periodic'):Geometry(h,b,.5,periodic=False)


def test_unrepresentable_positive_polynomial_is_rejected_not_silently_zeroed():
    h=np.array([[1.,2.**-1070,3.,4.]])
    with pytest.raises(ValueError,match='storage range'):
        Geometry(h,np.zeros_like(h),.5,periodic=True)
