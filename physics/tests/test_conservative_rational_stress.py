"""Local conservative component tests, with an independent energy gate."""
import numpy as np
import pytest
from conservative_rational_stress import stress_stage,stress_stage_physical,negative_divergence
from smooth_rational_velocity_stage import make
from finite_depth_pressure_reference import response


@pytest.mark.parametrize('shape',((1,7),(7,1),(3,4),(2,11)))
def test_local_physical_flux_and_positive_mass_component(shape):
    rng=np.random.default_rng(9538);h=1+rng.random(shape);v=.2*rng.normal(size=(*shape,2))
    r=stress_stage(make(h,np.zeros_like(h),.5),v)
    assert r['auxiliary_momentum_identity_error']<1e-10
    assert r['local_momentum_flux_error']<1e-10
    np.testing.assert_allclose(np.sum(r['physical_momentum_rate'],axis=(0,1)),0.,rtol=0,atol=1e-10)
    np.testing.assert_allclose(negative_divergence(r['physical_momentum_fluxes'],.5),r['physical_momentum_rate'],rtol=0,atol=1e-10)
    assert abs(r['depth_rate'].sum())<1e-10
    assert np.min(h+.9*r['mass_only_forward_euler_bound']*r['depth_rate'])>=0
    assert r['energy_coordinate_error']<1e-10
    assert r['energy_work_split_error']<1e-10


@pytest.mark.parametrize('axis',(0,1))
def test_rest_reflection_and_flow_reversal(axis):
    h=np.array([[1.,2.,4.]])
    if axis==0:h=h.T
    g=make(h,np.zeros_like(h),.5);zero=np.zeros((*h.shape,2));rest=stress_stage(g,zero)
    np.testing.assert_allclose(np.sum(rest['physical_momentum_rate'],axis=(0,1)),0.,atol=1e-10)
    flipped=stress_stage(make(np.flip(h,axis).copy(),np.zeros_like(h),.5),zero)
    expected=np.flip(rest['canonical_velocity_rate'],axis).copy();expected[...,1-axis]*=-1
    np.testing.assert_allclose(expected,flipped['canonical_velocity_rate'],atol=1e-10)
    for sign in (-1,1):
        v=zero.copy();v[...,1-axis]=sign*2.**-28;r=stress_stage(g,v)
        np.testing.assert_allclose(r['canonical_velocity_rate'],rest['canonical_velocity_rate'],atol=1e-10)


def test_two_pole_linear_wave_response_retained():
    n=32;dx=.25;depth=1.5;theta=2*np.pi*2*np.arange(n)/n;mode=np.cos(theta)[None,:]
    eps=1e-5;values=[]
    for sign in (-1,1):
        h=depth+sign*eps*np.sin(theta)[None,:]
        values.append(stress_stage(make(h,np.zeros_like(h),dx),np.zeros((*h.shape,2)))['physical_momentum_rate'][...,0])
    measured=np.sum(((values[1]-values[0])/(2*eps))*mode)/np.sum(mode*mode)
    k=np.sin(2*np.pi*2/n)/dx
    expected=-9.81*depth*k*response(depth*k)
    assert abs(measured-expected)<1e-7


def test_unqualified_variable_bed_not_silently_flattened():
    with pytest.raises(ValueError):
        stress_stage(make(np.ones((1,3)),np.array([[0.,.1,0.]]),.5),np.zeros((1,3,2)))


@pytest.mark.parametrize('shape',((1,19),(3,4)))
def test_physical_entry_matches_dense_preparation_without_mutation(shape):
    from reconstructed_energy_reference import metric
    rng=np.random.default_rng(9604);h=1+rng.random(shape);bed=np.zeros_like(h)
    p=h[...,None]*rng.normal(size=(*shape,2))*.2;before=[a.copy() for a in (h,bed,p)]
    g=make(h,bed,.5);k,_=metric(g,rational=True);root=np.sqrt(h)[...,None]
    v=(k@(p/root).ravel()).reshape(p.shape)/root
    old=stress_stage(g,v);new=stress_stage_physical(g,p)
    for key in ('physical_momentum_rate','depth_rate','canonical_velocity_rate'):
        np.testing.assert_allclose(new[key],old[key],rtol=1e-10,atol=1e-10)
    assert abs(new['energy_rate']-old['energy_rate'])<1e-10
    assert new['source_momentum_roundtrip_error']<1e-10
    for value,original in zip((h,bed,p),before):np.testing.assert_array_equal(value,original)
