from copy import deepcopy
from fractions import Fraction as F

import pytest

from subcell_front_pressure_variation import FrontPressureVariation
from test_subcell_moving_pressure_metric import geometry, metric
from test_subcell_front_pressure_variation import P, PD


@pytest.fixture
def original():
    g=geometry();m=metric(g)
    return g,m,m.evaluate(P,PD)


def test_original_solved_unknowns_reproduce_every_derivative_without_resolving(original):
    g,m,state=original
    expected=FrontPressureVariation(g,m,P)
    def forbidden(*args,**kwargs):raise AssertionError('Original solve must not be repeated')
    m.solve_physical.solve=forbidden
    for pole in m.poles:pole['auxiliary_map']=None
    actual=FrontPressureVariation(g,m,P,solved_state=state)
    for name in ('momentum_gradient','mass_gradient','kinetic_gradient','gram_gradients',
                 'divergence_gradients','volume_gradient','face_column_gradients',
                 'depth_moment_gradients','bed_gradient_gradients',
                 'canonical_momentum_gradient','canonical_depth_moment_gradients',
                 'canonical_face_column_gradients','canonical_bed_gradient_gradients'):
        assert getattr(actual,name)==getattr(expected,name),name
    assert actual.time_work(PD)==expected.time_work(PD)
    assert actual.time_work(state['canonical_momentum_rate'],momentum_coordinate='canonical')['energy_direction']==state['kinetic_energy_rate']


@pytest.mark.parametrize('kind',('velocity','auxiliary','length','weight','order','missing','shape','momentum'))
def test_original_equations_reject_corrupted_cached_unknowns(original,kind):
    g,m,state=original;state=deepcopy(state);p=P
    if kind in ('velocity','shape'):
        values=[list(row) for row in state['canonical_velocity']]
        if kind=='velocity':values[0][0]+=F(1,10**400)
        else:values[0].pop()
        state['canonical_velocity']=values
    elif kind=='auxiliary':
        values=[list(row) for row in state['poles'][0]['auxiliary_velocity']]
        values[1][1]+=F(1,10**400)
        state['poles'][0]['auxiliary_velocity']=values
    elif kind in ('length','weight'):state['poles'][0][kind]+=F(1,10**400)
    elif kind=='order':state['poles'].reverse()
    elif kind=='missing':state['poles'].pop()
    elif kind=='momentum':p=((P[0][0]+F(1,10**400),P[0][1]),P[1])
    with pytest.raises(ValueError):FrontPressureVariation(g,m,p,solved_state=state)


def test_success_flags_are_not_used_as_a_substitute_for_equations(original):
    g,m,state=original;state=deepcopy(state)
    state['exact_original_momentum_and_rate_reconstruction']=False
    for pole in state['poles']:
        pole['exact_residual_zero']=False
        pole['exact_rate_residual_zero']=False
    actual=FrontPressureVariation(g,m,P,solved_state=state)
    assert actual.time_work(PD)['energy_direction']==state['kinetic_energy_rate']


def test_matching_unknowns_do_not_allow_a_different_metric_geometry(original):
    g,m,state=original
    with pytest.raises(ValueError,match='Matching original source'):
        FrontPressureVariation(geometry(F(21,100)),m,P,solved_state=state)
