from fractions import Fraction as F
import numpy as np
import pytest

from subcell_transfer_events import integrate


def test_frozen_chain_accepts_inflow_before_conservative_drying():
    # Node 1 is not isolated: it drains later than V1/out1 because node 0 feeds it.
    value = integrate([1., 1., 0.], [(0, 1, 2.), (1, 2, 3.)], 1.)
    assert value['volume'] == [0, 0, 2]
    assert value['events'] == [dict(time=F(1, 2), regions=[0]), dict(time=F(2, 3), regions=[1])]
    assert value['transfers'] == [(0, 1, 1), (1, 2, 2)]
    assert value['exposure'][0] == F(1, 4)
    assert value['exposure'][1] == F(5, 12)


def test_empty_reservoir_routes_inflow_without_creating_water():
    value = integrate([1., 0., 0.], [(0, 1, 1.), (1, 2, 4.)], 2.)
    assert value['volume'] == [0, 0, 1]
    assert value['transfers'] == [(0, 1, 1), (1, 2, 1)]


def test_supplied_cycle_and_unsupplied_cycle_use_different_routing():
    value = integrate([1., 0., 0., 0., 0.], [(0, 1, 1.), (1, 2, 10.),
        (2, 1, 1.), (3, 4, 3.), (4, 3, 3.)], 2.)
    assert sum(value['volume']) == 1
    assert value['volume'][0] == value['volume'][1] == 0
    assert value['volume'][2] == 1
    assert all(a < 3 and b < 3 for a, b, _ in value['transfers'])


def test_scaled_chain_has_identical_events_without_a_depth_floor():
    baseline = integrate([1., 1., 0.], [(0, 1, 2.), (1, 2, 3.)], 1.)
    scale = 2.**-900
    tiny = integrate([scale, scale, 0.], [(0, 1, 2*scale), (1, 2, 3*scale)], 1.)
    assert tiny['events'] == baseline['events']
    assert tiny['volume'] == [v*F(scale) for v in baseline['volume']]


def test_part_interval_and_exact_semigroup_for_constant_network():
    edges = [(0, 1, 2.), (1, 2, 3.)]
    first = integrate([1., 1., 0.], edges, .25)
    assert first['volume'] == [F(1, 2), F(3, 4), F(3, 4)]
    second = integrate(first['volume'], edges, .75)
    assert second['volume'] == integrate([1., 1., 0.], edges, 1.)['volume']


def test_actual_south_fork_failed_chain_routes_all_four_original_volumes():
    # Step-18 original incident ledger, not independently deleted tiny cells.
    # The five receivers track only the parcels from this no-external-inflow
    # chain; this does not approximate their full outside-coupled river state.
    v = [2.1890458223615698e-247, 2.0950628474373184e-249,
         9.44972313341925e-253, 1.0039206862370189e-254]+[0.]*5
    edges = [(0, 4, 4.613768667608291e-165), (0, 1, 2.070666951894242e-166),
             (1, 5, 2.4031524833514948e-166), (1, 2, 8.987750414438672e-168),
             (2, 6, 1.5153934181800253e-210), (2, 3, 6.98892143471895e-169),
             (3, 7, 9.131916671821778e-170), (3, 8, 2.15846479468258e-169)]
    result = integrate(v, edges, .02)
    assert result['volume'][:4] == [0]*4
    assert min(result['volume'][4:]) > 0
    assert sum(result['volume'][4:]) == sum(map(F, v))
    assert {i for e in result['events'] for i in e['regions']} == {0, 1, 2, 3}
    assert all(result['incoming'][i] > 0 for i in (1, 2, 3))


@pytest.mark.parametrize('seed', [9301, 9302, 9303])
def test_random_network_exact_incident_mass_and_nonnegativity(seed):
    rng = np.random.default_rng(seed)
    v = rng.integers(0, 10, 8).astype(float)
    edges = [(a, b, float(rng.integers(1, 10))) for a in range(8) for b in range(8)
             if a != b and rng.random() < .3]
    result = integrate(v, edges, 3.)
    assert sum(result['volume']) == sum(map(F, v))
    assert min(result['volume']) >= 0
    for i in range(8):
        assert result['volume'][i] == F(v[i])+result['incoming'][i]-result['outgoing'][i]


def test_random_frozen_network_semigroup_keeps_exact_fractional_state():
    for seed in range(20):
        rng = np.random.default_rng(seed)
        v = rng.integers(0, 4, 6).astype(float)
        edges = [(a, b, float(rng.integers(1, 8))) for a in range(6) for b in range(6)
                 if a != b and rng.random() < .4]
        whole = integrate(v, edges, 2.)
        first = integrate(v, edges, .25)
        second = integrate(first['volume'], edges, 1.75)
        assert second['volume'] == whole['volume'], seed
        assert all(a+b == c for a, b, c in zip(first['exposure'], second['exposure'], whole['exposure'])), seed
        assert all(a+b == c for a, b, c in zip(first['incoming'], second['incoming'], whole['incoming'])), seed
