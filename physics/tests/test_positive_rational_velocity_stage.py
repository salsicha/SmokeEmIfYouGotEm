import numpy as np
import pytest
import test_rational_velocity_bracket_reference as original
from positive_rational_velocity_stage import stage,rk2_step
from rational_dual_energy_reference import evaluate


@pytest.mark.parametrize('seed',(6301,6302,6303))
def test_original_energy_and_independent_direction_controls(monkeypatch,seed):
    monkeypatch.setattr(original,'stage',stage)
    original.test_nonlinear_closed_stage_energy_and_independent_state_direction(seed)


def test_stationary_lake_inputs_unchanged_and_mass_step_positive():
    rng=np.random.default_rng(9310);b=rng.uniform(0,.1,(3,4));h=2.-b;v=np.zeros((*h.shape,2))
    before=[a.copy() for a in (h,b,v)]
    result=stage(original.make(h,b),v)
    np.testing.assert_array_equal(result['depth_rate'],0.)
    np.testing.assert_allclose(result['canonical_velocity_rate'],0.,atol=1e-13,rtol=0)
    for a,c in zip((h,b,v),before):np.testing.assert_array_equal(a,c)
    v=rng.normal(size=v.shape)*.2;result=stage(original.make(h,b),v)
    dt=min(.01,.9*result['mass_only_forward_euler_bound'])
    assert np.all(h+dt*result['depth_rate']>=0)


def test_dry_pressure_not_silently_accepted():
    h=np.ones((3,4));h[1,1]=0.;b=np.zeros_like(h);v=np.zeros((*h.shape,2))
    with pytest.raises(ValueError,match='positive'):
        stage(original.make(h,b),v)


@pytest.mark.parametrize('seed',(7325,7326))
def test_original_rough_bed_positive_cut_states(seed):
    rng=np.random.default_rng(seed);h=np.exp(rng.uniform(np.log(.01),np.log(.5),(3,4)))
    b=rng.uniform(0,2.,h.shape);v=rng.normal(size=(*h.shape,2))*.03
    g=original.make(h,b)
    assert any(np.any(edge['aa']==0)|np.any(edge['ab']==0) for edge in g.edges)
    r=stage(g,v)
    assert abs(r['energy_rate'])<2e-12
    assert r['branch_chain_rule_error']<2e-12
    assert abs(r['net_mass_rate'])<2e-14


def test_rk2_matches_two_original_stages_without_changing_inputs():
    rng=np.random.default_rng(9311);h=rng.uniform(.8,2.,(3,4));b=rng.uniform(0,.1,h.shape)
    v=rng.normal(size=(*h.shape,2))*.1;dt=.001
    before=[a.copy() for a in (h,b,v)]
    r0=stage(original.make(h,b),v)
    h1=h+dt*r0['depth_rate'];v1=v+dt*r0['canonical_velocity_rate']
    r1=stage(original.make(h1,b),v1)
    actual_h,actual_v,detail=rk2_step(h,b,v,.5,dt)
    np.testing.assert_array_equal(actual_h,.5*h+.5*(h1+dt*r1['depth_rate']))
    np.testing.assert_array_equal(actual_v,.5*v+.5*(v1+dt*r1['canonical_velocity_rate']))
    assert abs(float(np.sum(actual_h-h)))<2e-14
    assert np.all(actual_h>0)
    for a,c in zip((h,b,v),before):np.testing.assert_array_equal(a,c)
    with pytest.raises(ValueError,match='positive step'):rk2_step(h,b,v,.5,0.)
    with pytest.raises(ValueError,match='draining'):
        rk2_step(h,b,v,.5,1.01*r0['mass_only_forward_euler_bound'])
