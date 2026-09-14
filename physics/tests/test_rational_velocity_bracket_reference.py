import numpy as np
import pytest
from rational_velocity_bracket_reference import stage,gradient,divergence
from rational_dual_energy_reference import evaluate
from reconstructed_pressure_geometry import ReconstructedPressureGeometry


def make(h,b):
    return ReconstructedPressureGeometry(h,b,.5,periodic=True,
        pressure_trace='integrated_column',bed_quadrature='shared_bottom')


def test_periodic_adjoint_and_rotational_work_identity():
    rng=np.random.default_rng(6300);f=rng.normal(size=(4,5));v=rng.normal(size=(4,5,2))
    assert abs(np.sum(gradient(f,.5)*v)+np.sum(f*divergence(v,.5)))<2e-14


@pytest.mark.parametrize('seed',(6301,6302,6303))
def test_nonlinear_closed_stage_energy_and_independent_state_direction(seed):
    rng=np.random.default_rng(seed);h=rng.uniform(.8,2.,(3,4));b=rng.uniform(0,.1,h.shape)
    v=rng.normal(size=(*h.shape,2))*.2;g=make(h,b);result=stage(g,v)
    assert abs(result['energy_rate'])<2e-12
    assert abs(result['net_mass_rate'])<2e-14
    assert abs(result['rotational_work'])<2e-14
    eps=1e-4;values=[]
    for sign in (-1,1):
        hh=h+sign*eps*result['depth_rate'];vv=v+sign*eps*result['canonical_velocity_rate']
        values.append(evaluate(make(hh,b),vv)['total'])
    assert abs((values[1]-values[0])/(2*eps))<1e-7
    assert result['original_fv_transport_preserved'] is False
    assert result['nonlinear_history_or_wetting_or_breaking_or_gameplay_accepted'] is False


def test_stationary_variable_bed_lake_and_control_size_rejection():
    rng=np.random.default_rng(6304);b=rng.uniform(0,.1,(3,4));h=2.-b
    result=stage(make(h,b),np.zeros((*h.shape,2)))
    np.testing.assert_array_equal(result['depth_rate'],0.)
    np.testing.assert_allclose(result['canonical_velocity_rate'],0.,atol=1e-13,rtol=0)
    with pytest.raises(ValueError,match='bounded control'):
        stage(make(np.ones((9,9)),np.zeros((9,9))),np.zeros((9,9,2)))
