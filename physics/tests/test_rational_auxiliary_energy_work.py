"""Independent local checks; these do not waive stress energy failures."""
import numpy as np
import pytest
from rational_auxiliary_energy_work import graph_exchange, local_work, stationary_density
from rational_primal_energy import evaluate
from patch_pressure_preconditioner import PatchPressureSystem
from smooth_rational_velocity_stage import make


@pytest.mark.parametrize('shape', ((1,1),(1,2),(2,3),(3,4),(1,19)))
def test_graph_exchange_matches_factor_adjoint_locally(shape):
    rng = np.random.default_rng(9741)
    h = 1+rng.random(shape)
    g = make(h, .3*rng.normal(size=shape), .5)
    system = PatchPressureSystem(g, .1)
    a, b = rng.normal(size=(2, *shape))
    x = rng.normal(size=(*shape, 2))
    measured = graph_exchange(system, a, b, x)
    expected = (a*system.w(x)+.75*b*system.v(x)
                - np.sum(x*(system.transpose_w(a)+.75*system.transpose_v(b)), axis=-1))
    np.testing.assert_allclose(measured, expected, rtol=1e-12, atol=1e-12)
    assert abs(measured.sum()) < 1e-11


@pytest.mark.parametrize('shape', ((1,2),(2,3),(3,4),(1,19)))
def test_local_density_derivative_not_just_total_energy(shape):
    rng = np.random.default_rng(9742)
    h = 1+rng.random(shape)
    bed = .2*rng.normal(size=shape)
    p = .2*rng.normal(size=(*shape, 2))
    ht = .1*rng.normal(size=shape)
    pt = .1*rng.normal(size=p.shape)
    originals = [a.copy() for a in (h, bed, p, ht, pt)]
    r = local_work(make(h, bed, .5), p, ht, pt)
    eps = 2e-5
    densities = []
    for sign in (-1, 1):
        moved = make(h+sign*eps*ht, bed, .5)
        pm = p+sign*eps*pt
        densities.append(stationary_density(moved, pm, evaluate(moved, pm)))
    finite_difference = (densities[1]-densities[0])/(2*eps)
    np.testing.assert_allclose(r['local_energy_rate'], finite_difference, rtol=1e-7, atol=1e-8)
    assert r['local_balance_error'] < 1e-10
    assert abs(r['integrated_auxiliary_exchange']) < 1e-10
    assert r['coordinate_work_error'] < 1e-10
    assert not r['energy_conservation_or_gameplay_accepted']
    for actual, original in zip((h, bed, p, ht, pt), originals):
        np.testing.assert_array_equal(actual, original)


def test_invalid_direction_rejected():
    g = make(np.ones((1,3)), np.zeros((1,3)), .5)
    with pytest.raises(ValueError):
        local_work(g, np.zeros((1,3,2)), np.ones((3,)), np.zeros((1,3,2)))
