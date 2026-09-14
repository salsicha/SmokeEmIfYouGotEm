"""Local geometry transfer versus independent forward and reverse derivatives."""
import numpy as np
import pytest
from rational_geometry_energy_exchange import complete_local_work
from smooth_rational_velocity_stage import make


@pytest.mark.parametrize('shape', ((1,1),(1,2),(2,3),(3,4),(1,19)))
def test_complete_cellwise_work_and_local_support(shape):
    rng = np.random.default_rng(9761)
    h = 1+rng.random(shape)
    b = .2*rng.normal(size=shape)
    p = .2*rng.normal(size=(*shape,2))
    ht, pt = .1*rng.normal(size=shape), .1*rng.normal(size=p.shape)
    copies = [a.copy() for a in (h,b,p,ht,pt)]
    r = complete_local_work(make(h,b,.5), p, ht, pt)
    for key in ('maximum_factor_value_error','maximum_forward_work_error',
                'maximum_reverse_gradient_error','maximum_graph_balance_error',
                'complete_local_balance_error'):
        assert r[key] < 1e-10, (key,r[key])
    assert r['maximum_local_depth_nodes'] <= 9
    assert abs(r['integrated_geometry_exchange']) < 1e-10
    for original, actual in zip(copies,(h,b,p,ht,pt)):
        np.testing.assert_array_equal(original,actual)
    assert not r['energy_conservation_or_gameplay_accepted']


@pytest.mark.parametrize('seed', (7325,7326))
def test_original_rough_blocked_columns(seed):
    rng = np.random.default_rng(seed)
    h = np.exp(rng.uniform(np.log(.01),np.log(.5),(3,4)))
    b = rng.uniform(0,2.,h.shape)
    p = h[...,None]*rng.normal(size=(*h.shape,2))*.03
    ht, pt = .01*h*rng.normal(size=h.shape), .01*p
    r = complete_local_work(make(h,b,.5),p,ht,pt)
    assert r['maximum_factor_value_error'] < 1e-10
    assert r['maximum_forward_work_error'] < 1e-10
    assert r['maximum_reverse_gradient_error'] < 1e-10
    assert r['complete_local_balance_error'] < 1e-10


def test_shape_mismatch_rejected():
    with pytest.raises(ValueError):
        complete_local_work(make(np.ones((1,3)),np.zeros((1,3)),.5),
                            np.zeros((1,3,2)),np.zeros((3,)),np.zeros((1,3,2)))
