"""Retain physical conservation failures; energy alone cannot qualify a solver."""
import numpy as np
import pytest
from audit_smooth_stage_momentum import run
from smooth_rational_velocity_stage import make,stage
from continuous_extremum_transport import ContinuousExtremumTransport


@pytest.mark.parametrize('n',(64,128))
@pytest.mark.parametrize('seed',(2200,2202,2204,2206))
def test_original_periodic_flat_profiles_conserve_physical_momentum(seed,n):
    r=run(seed,n)
    assert r['momentum_identity_error']<1e-10
    # Same zero-momentum-rate criterion as the retained full audit.
    assert np.max(abs(np.array(r['momentum_rate'])))<1e-10


def test_flat_resting_depth_variation_has_zero_net_pressure_force():
    h=np.array([[1.,2.,4.]]);b=np.zeros_like(h);v=np.zeros((*h.shape,2));dx=.5
    r=stage(make(h,b,dx),v)
    np.testing.assert_array_equal(r['depth_rate'],0.)
    actual=np.sum(h[...,None]*r['canonical_velocity_rate'],axis=(0,1))*dx**2
    # Independent reduction of the current donor-adjoint pressure term. This
    # localizes the defect to the mass/force pairing, not a pole solve error.
    t=ContinuousExtremumTransport(h,b,v,dx,periodic=True)
    predicted=-9.81*dx*np.sum(t.faces[0]['retained']*(np.roll(h,-1,1)-h))
    assert abs(actual[0]-predicted)<1e-12
    assert np.max(abs(actual))<1e-10
