from fractions import Fraction as F

import numpy as np
import pytest

from finite_depth_pressure_reference import LENGTHS, WEIGHTS
from subcell_affine_dry_fan import AffineDryFan, Radical
from subcell_affine_front_pressure import FrontPressureGeometry
from subcell_moving_pressure_metric import MovingPressureMetric, PositiveSolve
from test_subcell_affine_dry_fan import rectangle


def geometry(t=F(1,5)):
    fan=AffineDryFan((0,0),(3,4),1,(F(1,3),-F(1,4)),2,(F(1,5),-F(1,7)),gravity=1)
    fragments=tuple(rectangle(x0=a,x1=b,y0=-F(1,10),y1=F(1,10),slope=fan.gradient,bed=2)
                    for a,b in ((-F(1,10),0),(0,F(1,10))))
    return FrontPressureGeometry(fan,fragments,t,outer_boundary='reflecting')


def metric(g):return MovingPressureMetric(g.volumes,g.volume_rates,g.kinetic,g.kinetic_rate)
def floats(a):return np.array([[float(v) for v in row] for row in a])


def test_original_normalized_two_pole_map_matches_independent_dense_oracle():
    g=geometry();m=metric(g);mass=np.repeat(list(map(float,g.volumes)),2)
    root=np.sqrt(mass);q=floats(g.kinetic)/root[:,None]/root[None,:]
    s=(1-float(np.sum(WEIGHTS)))*np.eye(4)
    for length,weight in zip(LENGTHS,WEIGHTS):s+=weight*np.linalg.inv(np.eye(4)+length*q)
    expected=root[:,None]*s*root[None,:]
    np.testing.assert_allclose(floats(m.physical),expected,rtol=2e-13,atol=1e-17)
    assert [p['length'] for p in m.poles]==list(map(lambda x:F(float(x)),LENGTHS))
    assert [p['weight'] for p in m.poles]==list(map(lambda x:F(float(x)),WEIGHTS))
    assert m.constant==F(1-float(np.sum(WEIGHTS)))


def test_physical_canonical_roundtrip_positive_energy_and_both_original_poles():
    m=metric(geometry());v=((F(1,3),-F(2,5)),(F(1,7),F(2,9)))
    p=m.physical_momentum(v);r=m.evaluate(p,((0,0),(0,0)))
    assert r['canonical_velocity']==v and r['kinetic_energy']>0
    assert r['geometry_time_work']!=0 and r['momentum_work']==0
    assert r['kinetic_energy_rate']==r['geometry_time_work']
    assert len(r['poles'])==2 and all(p['exact_residual_zero'] for p in r['poles'])
    assert all(p['exact_rate_residual_zero'] for p in r['poles'])
    assert r['exact_original_momentum_and_rate_reconstruction']
    assert sum(r['positive_energy_terms'])==r['kinetic_energy']
    assert r['positive_auxiliary_energy_rate']==r['kinetic_energy_rate']
    assert not r['native_40cg_or_nonlinear_force_or_open_boundary_or_gameplay_accepted']
    for i in range(2):
        for axis in range(2):
            assert r['canonical_momentum'][i][axis]==m.mass[2*i]*v[i][axis]
            assert r['layer_velocity'][i][axis]==p[i][axis]/m.mass[2*i]


def test_full_physical_momentum_time_chain_rule_matches_independent_refinement():
    t=F(1,5);p=((F(1,30),-F(1,20)),(F(1,70),F(2,90)))
    pd=((F(1,50),F(1,30)),(-F(1,40),F(3,70)))
    m=metric(geometry(t));r=m.evaluate(p,pd);errors=[]
    for divisor in (200,400,800,1600,3200):
        eps=t/divisor;values=[];velocities=[]
        for sign in (-1,1):
            state=tuple(tuple(x+sign*eps*y for x,y in zip(a,b)) for a,b in zip(p,pd))
            result=metric(geometry(t+sign*eps)).evaluate(state,((0,0),(0,0)))
            values.append(result['kinetic_energy']);velocities.append(result['canonical_velocity'])
        errors.append(abs(float((values[1]-values[0])/(2*eps)-r['kinetic_energy_rate'])))
        difference=np.array([[float((velocities[1][i][j]-velocities[0][i][j])/(2*eps)) for j in range(2)] for i in range(2)])
    assert all(a/b>3.8 for a,b in zip(errors,errors[1:]))
    assert errors[-1]<1e-6
    np.testing.assert_allclose(difference,floats(r['canonical_velocity_rate']),rtol=1e-5,atol=1e-6)
    assert errors[-1]<abs(float(r['geometry_time_work']))/100
    assert errors[-1]<abs(float(r['momentum_work']))/100


def test_missing_volume_normalizations_cannot_pass_the_physical_chain_rule():
    g=geometry();m=metric(g);bad=MovingPressureMetric(g.volumes,(0,0),g.kinetic,g.kinetic_rate)
    p=((F(1,30),-F(1,20)),(F(1,70),F(2,90)))
    correct=m.evaluate(p,((0,0),(0,0)));wrong=bad.evaluate(p,((0,0),(0,0)))
    assert abs(float(correct['kinetic_energy_rate']-wrong['kinetic_energy_rate']))>1e-4
    assert correct['canonical_velocity']==wrong['canonical_velocity']
    assert correct['canonical_velocity_rate']!=wrong['canonical_velocity_rate']


def test_represented_zero_mode_is_retained_without_refitting_constant():
    v=F(7,10);m=MovingPressureMetric((v,),(F(1,3),),((0,0),(0,0)),((0,0),(0,0)))
    s0=m.constant+sum(p['weight'] for p in m.poles)
    assert s0==1  # Preserve the implemented sum, not c replaced by exact 1/15.
    assert m.constant!=F(1,15)
    p=((F(2,5),-F(1,3)),);r=m.evaluate(p,((0,0),))
    assert r['canonical_velocity']==tuple(tuple(x/(s0*v) for x in pair) for pair in p)
    assert r['kinetic_energy']==sum(x*x for x in p[0])/(2*s0*v)
    assert r['kinetic_energy_rate']==-sum(x*x for x in p[0])*F(1,3)/(2*s0*v*v)


def test_positive_subfloat_mass_is_not_converted_to_dry_or_clamped():
    v=F(1,10**400);c=v*v*v
    m=MovingPressureMetric((v,),(0,),((c,0),(0,c)),((0,0),(0,0)))
    p=((v,-2*v),);r=m.evaluate(p,((0,0),))
    assert r['kinetic_energy']>0 and float(r['kinetic_energy'])==0
    assert r['layer_velocity']==((1,-2),)
    assert all(q['exact_residual_zero'] for q in r['poles'])
    assert r['kinetic_energy_rate']==0
    dry=MovingPressureMetric((),(),(),())
    assert dry.evaluate((),())['kinetic_energy']==0
    with pytest.raises(ValueError):dry.evaluate(((0,0),),((0,0),))


def test_quadratic_field_momentum_does_not_take_a_float_round_trip():
    v=Radical(2,2,1);rate=Radical(2,0,1)
    m=MovingPressureMetric((v,),(rate,),((v,0),(0,2*v)),((rate,0),(0,2*rate)))
    original=((Radical(2,1,1),Radical(2,2,-1)),)
    p=m.physical_momentum(original)
    assert m.evaluate(p,((0,0),))['canonical_velocity']==original


def test_invalid_mass_shape_symmetry_and_pressure_pivots_are_rejected():
    for volumes in ((0,),(-1,), (float('nan'),)):
        with pytest.raises((ValueError,OverflowError)):
            MovingPressureMetric(volumes,(0,),((0,0),(0,0)),((0,0),(0,0)))
    with pytest.raises(ValueError):MovingPressureMetric((1,),(0,),((0,1),(0,0)),((0,0),(0,0)))
    with pytest.raises(ValueError):MovingPressureMetric((1,),(),((0,0),(0,0)),((0,0),(0,0)))
    with pytest.raises(ValueError,match='pivot'):PositiveSolve(((1,2),(2,1)),F(0))
    for c in (((-F(1,10),0),(0,0)),((0,F(1,10)),(F(1,10),0))):
        with pytest.raises(ValueError):MovingPressureMetric((1,),(0,),c,((0,0),(0,0)))
    singular=PositiveSolve(((0,0),(0,1)),F(0),allow_semidefinite=True)
    with pytest.raises(ValueError,match='Singular'):singular.solve((0,1))


def test_original_pole_reconstruction_rejects_a_corrupted_metric_time_matrix():
    m=metric(geometry());m.physical_rate[0][0]+=1
    with pytest.raises(ValueError,match='reconstruction'):
        m.evaluate(((F(1,30),-F(1,20)),(F(1,70),F(2,90))),((0,0),(0,0)))
