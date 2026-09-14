"""Same-operator primal response: independent dense and tangent checks."""
import numpy as np
import pytest
from finite_depth_pressure_reference import LENGTHS, WEIGHTS
from reconstructed_acceleration_system import ReconstructedAccelerationSystem
from rational_dual_energy_reference import evaluate
from smooth_rational_velocity_stage import make
from smooth_pressure_geometry import SmoothPressureGeometryRate


@pytest.mark.parametrize('shape',((3,4),(1,19),(9,2)))
def test_patch_primal_matches_dense_same_operator_and_depth_tangent(shape):
    rng=np.random.default_rng(9531);h=1+rng.random(shape);b=.2*rng.normal(size=shape)
    v=rng.normal(size=(*shape,2));ht=.1*rng.normal(size=shape);g=make(h,b,.4)
    t=SmoothPressureGeometryRate(g,b,ht);r=evaluate(g,v,tangent=t,preconditioner='patch')
    q=np.sqrt(h)[...,None]*v;exact=(1-WEIGHTS.sum())*q
    for length,weight,pole in zip(LENGTHS,WEIGHTS,r['poles']):
        system=ReconstructedAccelerationSystem(g,float(length));columns=[]
        for i in range(v.size):
            basis=np.zeros_like(v);basis.ravel()[i]=1.;columns.append(system.apply(basis).ravel())
        z=np.linalg.solve(np.array(columns).T,q.ravel()).reshape(v.shape)
        np.testing.assert_allclose(pole['normalized_auxiliary_velocity'],z,rtol=1e-11,atol=1e-11)
        assert pole['iterations']<=40
        assert pole['relative_residual']<1e-11
        exact+=weight*z
    np.testing.assert_allclose(r['canonical_gradient_flux'],np.sqrt(h)[...,None]*exact,rtol=1e-11,atol=1e-11)
    eps=1e-5
    values=[evaluate(make(h+sign*eps*ht,b,.4),v,preconditioner='patch')['total'] for sign in (-1,1)]
    assert abs((values[1]-values[0])/(2*eps)-r['depth_direction']['total'])<1e-7


def test_default_is_original_block_and_invalid_scheme_rejected():
    h=np.array([[1.,2.,4.]]);g=make(h,np.zeros_like(h),.5)
    v=np.array([[[1.,.3],[2.,-.1],[3.,.2]]])
    original=evaluate(g,v);explicit=evaluate(g,v,preconditioner='block')
    np.testing.assert_array_equal(original['canonical_gradient_flux'],explicit['canonical_gradient_flux'])
    with pytest.raises(ValueError):evaluate(g,v,preconditioner='diagonal-shift')
