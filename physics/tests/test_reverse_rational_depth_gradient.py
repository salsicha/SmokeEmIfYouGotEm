import numpy as np
import pytest
from reconstructed_pressure_geometry import ReconstructedPressureGeometry
from reconstructed_pressure_rates import PressureGeometryRate
from rational_dual_energy_reference import evaluate
from rational_velocity_bracket_reference import stage as basis_stage
from reverse_rational_velocity_stage import stage as reverse_stage
from reverse_rational_depth_gradient import depth_gradient,coefficient_reverse


def make(h,b):
    return ReconstructedPressureGeometry(h,b,.5,periodic=True,
        pressure_trace='integrated_column',bed_quadrature='shared_bottom')


@pytest.mark.parametrize('shape',[(3,4),(1,7),(2,4)])
def test_full_gradient_and_stage_match_independent_basis_reference(shape):
    rng=np.random.default_rng(7321);h=rng.uniform(.8,2.,shape);b=rng.uniform(0,.1,shape)
    v=rng.normal(size=(*shape,2))*.2;g=make(h,b)
    expected=basis_stage(g,v);actual=reverse_stage(g,v)
    for key in ('depth_energy_gradient','depth_rate','canonical_velocity_rate'):
        np.testing.assert_allclose(actual[key],expected[key],atol=3e-12,rtol=0)
    assert abs(actual['energy_rate'])<2e-12
    assert actual['branch_chain_rule_error']<2e-12


def test_reverse_face_adjoint_matches_original_directional_coefficients():
    rng=np.random.default_rng(7322);h=rng.uniform(.8,2.,(3,4));b=rng.uniform(0,.15,h.shape)
    ht=rng.normal(size=h.shape)*.02;g=make(h,b);t=PressureGeometryRate(g,b,ht)
    seeds=[{key:rng.normal(size=h.shape) for key in ('aa','ab','own','other','shared_b')} for _ in (0,1)]
    actual,detail=coefficient_reverse(g,ht,seeds)
    expected=sum(np.sum(seed[key]*edge[key]) for seed,edge in zip(seeds,t.edges) for key in seed)
    assert abs(np.sum(actual*ht)-expected)<2e-12
    assert max(detail['coefficient_value_discrepancy'].values())<2e-14


def test_actual_tied_branch_direction_is_retained_not_averaged():
    h=np.ones((3,4));b=np.array([[0,.1,.2,.1]]*3);g=make(h,b)
    rng=np.random.default_rng(7323);ht=rng.normal(size=h.shape)*.02
    seeds=[{key:rng.normal(size=h.shape) for key in ('aa','ab','own','other','shared_b')} for _ in (0,1)]
    a,_=coefficient_reverse(g,ht,seeds);t=PressureGeometryRate(g,b,ht)
    expected=sum(np.sum(seed[key]*edge[key]) for seed,edge in zip(seeds,t.edges) for key in seed)
    assert abs(np.sum(a*ht)-expected)<2e-12


def test_variable_bed_resting_lake_and_unchanged_arrays():
    rng=np.random.default_rng(7324);b=rng.uniform(0,.1,(3,4));h=2.-b;v=np.zeros((*h.shape,2))
    before=[a.copy() for a in (h,b,v)];actual=reverse_stage(make(h,b),v)
    np.testing.assert_array_equal(actual['depth_rate'],0.)
    np.testing.assert_allclose(actual['canonical_velocity_rate'],0.,atol=1e-13,rtol=0)
    for a,c in zip((h,b,v),before):np.testing.assert_array_equal(a,c)


@pytest.mark.parametrize('seed',(7325,7326))
def test_original_blocked_and_partial_cut_columns_match_basis(seed):
    rng=np.random.default_rng(seed);h=np.exp(rng.uniform(np.log(.01),np.log(.5),(3,4)))
    b=rng.uniform(0,2.,h.shape);v=rng.normal(size=(*h.shape,2))*.03;g=make(h,b)
    assert any(np.any(edge['aa']==0)|np.any(edge['ab']==0) for edge in g.edges)
    expected=basis_stage(g,v);actual=reverse_stage(g,v)
    np.testing.assert_allclose(actual['depth_energy_gradient'],expected['depth_energy_gradient'],atol=3e-12,rtol=0)
    np.testing.assert_allclose(actual['canonical_velocity_rate'],expected['canonical_velocity_rate'],atol=3e-12,rtol=0)
    assert abs(actual['energy_rate'])<2e-12
