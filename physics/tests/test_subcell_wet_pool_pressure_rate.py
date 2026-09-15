import numpy as np
import pytest
from types import SimpleNamespace

from test_subcell_wet_pool_pressure import partition
from subcell_wet_pool_pressure import WetPoolPressureSystem, harmonic_area, piecewise_column_integral
from subcell_wet_pool_pressure_rate import WetPoolPressureRate, harmonic_area_rate, dual_direction
from finite_depth_pressure_reference import LENGTHS


@pytest.mark.parametrize('stages', [(.3, .7), (.7, .3), (.3, .3), (2., 2.1), (-.2, .7), (.003, 20.)])
@pytest.mark.parametrize('bed', [(0., 0.), (0., 1.)])
def test_harmonic_direction_matches_independent_stage_probes(stages, bed):
    segment = np.array([[0., bed[0]], [1., bed[1]]])
    direction = np.array([.17, -.11])
    step = 1e-6
    low, high = np.array(stages)-step*direction, np.array(stages)+step*direction
    expected = (harmonic_area(segment, *high, 0., 0.)-harmonic_area(segment, *low, 0., 0.))/(2*step)
    actual = harmonic_area_rate(segment, *stages, 0., 0., *direction)
    np.testing.assert_allclose(actual, expected, atol=2e-10, rtol=2e-7)


def test_thin_harmonic_stage_partials_and_level_dry_event():
    flat = np.array([[0., 220.], [1., 220.]])
    slope = np.array([[0., 220.], [1., 221.]])
    for h in (1e-10, 1e-50, 1e-150):
        np.testing.assert_allclose(harmonic_area_rate(flat, h, 1., 220., 220., 0., 1.),
                                   2*(h/(1+h))**2, atol=0., rtol=1e-13)
        np.testing.assert_allclose(harmonic_area_rate(slope, h, 1., 220., 220., 1., 0.),
                                   2*h, atol=0., rtol=1e-9)
        np.testing.assert_allclose(harmonic_area_rate(slope, h, h, 220., 220., 1., 1.),
                                   h, atol=0., rtol=1e-13)
    with pytest.raises(ValueError, match='Level-dry'):
        harmonic_area_rate(flat, 0., 1., 220., 220., 1., 0.)


def test_volume_probe_has_independent_stages_preserves_source_and_rejects_events():
    pools, _, _, _ = partition(lambda x, y: 1-abs(x), .37)
    volumes = np.array([p['volume'] for p in pools.pools])
    probe = pools.volume_probe(volumes*[1.01, .99])
    assert probe.pools[0]['parent_stage_offset'] != probe.pools[1]['parent_stage_offset']
    np.testing.assert_array_equal([p['volume'] for p in pools.pools], volumes)
    assert probe.maximum_volume_error is None
    np.testing.assert_allclose(probe.reassembled_volumes.sum(), sum(p['volume'] for p in probe.pools))
    for old, new in zip(pools.pools, probe.pools):
        np.testing.assert_allclose(old['momentum']/old['volume'], new['momentum']/new['volume'])
        assert old['storage'] is new['storage']
    for values in (volumes*10, volumes*0, volumes[:, None], volumes*np.nan):
        with pytest.raises(ValueError):
            pools.volume_probe(values)
    system = WetPoolPressureSystem(probe, float(LENGTHS[0]))
    assert system.maximum_wall_column_partition_error < 1e-13
    assert not system.connections


def fixture(kind):
    if kind == 'split':
        # Four wet pools, two on each side of a same-cell ridge, with shared
        # faces along y and reflecting physical walls in both directions.
        return partition(lambda x, y: 1-abs(x)+.03*y, .37, (2, 1), (2., 1.), (0., -.5))[0]
    if kind == 'flat':
        return partition(lambda x, y: 0*x, np.array([[.8, 1.1], [.9, 1.2]]),
                         (2, 2), (.5, .5), (-.25, -.25), (True, True))[0]
    return partition(lambda x, y: .2*x+.1*y, .23, (2, 2), (.5, .5), (-.25, -.25))[0]


@pytest.mark.parametrize('kind', ['split', 'flat', 'slope'])
@pytest.mark.parametrize('length', LENGTHS)
def test_complete_pressure_direction_is_symmetric_and_matches_perturbed_operator(kind, length):
    pools = fixture(kind)
    volumes = np.array([p['volume'] for p in pools.pools])
    rng = np.random.default_rng(2501)
    vd = volumes*rng.uniform(-.3, .3, len(volumes))
    system = WetPoolPressureSystem(pools, float(length))
    rate = WetPoolPressureRate(system, vd[:, None])
    a, b = rng.normal(size=(2, len(volumes), 1, 2))
    assert abs(np.sum(a*rate.apply(b))-np.sum(b*rate.apply(a))) < 1e-12
    step = 1e-5
    low = WetPoolPressureSystem(pools.volume_probe(volumes-step*vd), float(length))
    high = WetPoolPressureSystem(pools.volume_probe(volumes+step*vd), float(length))
    fd = (high.apply(a)-low.apply(a))/(2*step)
    np.testing.assert_allclose(rate.apply(a), fd, atol=3e-9, rtol=3e-8)
    np.testing.assert_array_equal(WetPoolPressureRate(system, vd[:, None]*0).apply(a), 0.)


@pytest.mark.parametrize('kind', ['split', 'flat', 'slope'])
def test_original_poles_dual_energy_and_physical_momentum_direction(kind):
    pools = fixture(kind)
    volume = np.array([p['volume'] for p in pools.pools])
    rng = np.random.default_rng(2502)
    v, vt = rng.normal(size=(2, len(volume), 1, 2))
    vd = volume*rng.uniform(-.3, .3, len(volume))
    value = dual_direction(pools, v, vd[:, None], vt)
    step = 1e-5
    low = dual_direction(pools.volume_probe(volume-step*vd), v-step*vt, vd[:, None]*0)
    high = dual_direction(pools.volume_probe(volume+step*vd), v+step*vt, vd[:, None]*0)
    for key in ('kinetic', 'potential', 'total', 'physical_momentum'):
        fd = (high[key]-low[key])/(2*step)
        np.testing.assert_allclose(value[key+'_rate'], fd, atol=2e-9, rtol=2e-8)
    for record in value['poles']:
        assert record['solve']['relative_residual'] < 2e-5
        assert record['direction_solve']['relative_residual'] < 2e-5
        assert record['solve']['iterations'] <= 40
        assert record['direction_solve']['iterations'] <= 40
    assert not value['nonlinear_or_wetting_or_time_or_gameplay_accepted']


def test_rate_rejects_malformed_volume_direction():
    pools = fixture('split')
    system = WetPoolPressureSystem(pools, .4)
    for vd in (np.zeros(len(pools.pools)), np.full(system.h.shape, np.nan)):
        with pytest.raises(ValueError, match='volume direction'):
            WetPoolPressureRate(system, vd)


def test_matrix_direction_is_linear_and_centered_probes_converge_before_roundoff():
    pools = fixture('slope')
    volume = np.array([p['volume'] for p in pools.pools])
    rng = np.random.default_rng(2503)
    first, second = rng.uniform(-.3, .3, (2, len(volume)))*volume
    system = WetPoolPressureSystem(pools, float(LENGTHS[0]))
    q = rng.normal(size=(*system.h.shape, 2))
    actual = WetPoolPressureRate(system, first[:, None]).apply(q)
    combined = WetPoolPressureRate(system, (first+second)[:, None]).apply(q)
    np.testing.assert_allclose(combined, actual+WetPoolPressureRate(system, second[:, None]).apply(q), atol=1e-13)
    errors = []
    for step in (.02, .01, .005):
        low = WetPoolPressureSystem(pools.volume_probe(volume-step*first), float(LENGTHS[0]))
        high = WetPoolPressureSystem(pools.volume_probe(volume+step*first), float(LENGTHS[0]))
        errors.append(np.linalg.norm((high.apply(q)-low.apply(q))/(2*step)-actual))
    assert errors[0]/errors[1] > 3.9
    assert errors[1]/errors[2] > 3.9


def test_coverage_oracle_handles_adjacent_float_knots_but_rejects_multiple_pools():
    form = dict(stage_offset=1., datum=0.)
    pools = SimpleNamespace(pools=[dict(form=form), dict(form=form)])
    lo, hi = .125, np.nextafter(.125, 1.)
    first = [(0, np.array([[0., 0.], [hi, 0.]])), (0, np.array([[lo, 0.], [1., 0.]]))]
    assert piecewise_column_integral(pools, first) == 1.
    # Original trace values are not welded by the union-area check.
    assert first[0][1][1, 0] == hi
    assert first[1][1][0, 0] == lo
    with pytest.raises(ValueError, match='incompatible pool traces'):
        piecewise_column_integral(pools, [first[0], (1, first[1][1])])
    conflict = first[1][1].copy(); conflict[:, 1] = .1
    with pytest.raises(ValueError, match='incompatible pool traces'):
        piecewise_column_integral(pools, [first[0], (0, conflict)])
    dry = SimpleNamespace(pools=[dict(form=dict(stage_offset=-.1, datum=0.)),
                                 dict(form=dict(stage_offset=-.2, datum=0.))])
    assert piecewise_column_integral(dry, [first[0], (1, first[1][1])]) == 0.
