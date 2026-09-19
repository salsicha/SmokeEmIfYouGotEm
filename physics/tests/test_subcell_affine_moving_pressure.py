from fractions import Fraction as F

import numpy as np
import pytest

from subcell_affine_dry_fan import AffineDryFan, Radical
from subcell_affine_moving_pressure import AffineMovingPressureMetric
from subcell_front_prescribed_trace import FrontPrescribedTrace
from subcell_moving_pressure_metric import MovingPressureMetric
from test_subcell_affine_dry_fan import rectangle
from test_subcell_moving_pressure_metric import floats


def trace(t=F(1, 5)):
    fan = AffineDryFan((0, 0), (3, 4), 1, (F(1, 3), -F(1, 4)), 2, (F(1, 5), -F(1, 7)), gravity=1)
    fragments = tuple(rectangle(x0=a, x1=b, y0=-F(1, 10), y1=F(1, 10), slope=fan.gradient, bed=2)
                      for a, b in ((-F(1, 10), 0), (0, F(1, 10))))
    return FrontPrescribedTrace(fan, fragments, t, boundary='prescribed-fan-velocity')


U = ((F(1, 3), -F(2, 5)), (F(1, 7), F(2, 9)))
P = ((F(1, 30), -F(1, 20)), (F(1, 70), F(2, 90)))
PT = ((F(1, 50), F(1, 30)), (-F(1, 40), F(3, 70)))
ZERO = ((0, 0), (0, 0))


def test_affine_roundtrip_original_poles_and_direct_local_boundary_energy():
    boundary = trace()
    m = AffineMovingPressureMetric.from_trace(boundary)
    p = m.physical_momentum(U)
    result = m.evaluate(p, PT)
    assert result['canonical_velocity'] == U
    assert any(q != 0 for q in m.offset)
    assert m.dual_constant < 0
    homogeneous = MovingPressureMetric(boundary.geometry.volumes, boundary.geometry.volume_rates,
                                      boundary.geometry.kinetic, boundary.geometry.kinetic_rate)
    assert homogeneous.physical_momentum(U) != p  # Missing trace changes physical momentum.
    assert [(p['length'], p['weight']) for p in m.poles] == [(p['length'], p['weight']) for p in homogeneous.poles]
    assert m.physical == homogeneous.physical
    independent = result['positive_energy_terms'][0]
    for pole, term in zip(result['poles'], result['positive_energy_terms'][1:]):
        a = m.vector(pole['auxiliary_velocity'])
        local = boundary.evaluate(pole['auxiliary_velocity'], pole['auxiliary_velocity_rate'])
        expected = pole['weight']*(sum((mass*x*x for mass, x in zip(m.mass, a)), m.zero)/2
                                  +pole['length']*local['kinetic_energy'])
        assert term == expected
        independent += expected
        assert pole['exact_residual_zero'] and pole['exact_rate_residual_zero']
    assert result['kinetic_energy'] == independent > 0
    assert result['positive_auxiliary_energy_rate'] == result['kinetic_energy_rate']
    assert not result['native_40cg_or_nonlinear_force_or_open_boundary_or_gameplay_accepted']


def test_independent_dense_affine_poles_and_legendre_energy():
    m = AffineMovingPressureMetric.from_trace(trace())
    v = floats(U).ravel()
    mass, linear = np.array(list(map(float, m.mass))), np.array(list(map(float, m.linear)))
    p, dual = float(m.constant)*mass*v, float(m.constant)*np.dot(mass*v, v)/2
    for pole in m.poles:
        length, weight = float(pole['length']), float(pole['weight'])
        h = np.diag(mass)+length*floats(m.kinetic)
        rhs = mass*v-length*linear
        a = np.linalg.solve(h, rhs)
        p += weight*mass*a
        dual += weight*(np.dot(rhs, a)/2-length*float(m.boundary_constant))
    result = m.evaluate(m.physical_momentum(U), ZERO)
    np.testing.assert_allclose(floats(m.physical_momentum(U)).ravel(), p, rtol=2e-13, atol=1e-16)
    assert float(result['kinetic_energy']) == pytest.approx(np.dot(p, v)-dual, rel=2e-13, abs=1e-16)


def test_physical_energy_gradient_is_canonical_velocity_with_boundary_shift():
    m = AffineMovingPressureMetric.from_trace(trace())
    result = m.evaluate(P, ZERO)
    for row in range(2):
        for axis in range(2):
            before, after = [list(p) for p in P], [list(p) for p in P]
            before[row][axis] -= 1
            after[row][axis] += 1
            difference = (m.evaluate(after, ZERO)['kinetic_energy']-m.evaluate(before, ZERO)['kinetic_energy'])/2
            assert difference == result['canonical_velocity'][row][axis]


def test_full_time_work_and_velocity_rate_converge_against_independent_time_differences():
    t = F(1, 5)
    m = AffineMovingPressureMetric.from_trace(trace(t))
    result, errors = m.evaluate(P, PT), []
    for divisor in (400, 800, 1600):
        dt, sides = t/divisor, []
        for sign in (-1, 1):
            p = tuple(tuple(x+sign*dt*y for x, y in zip(a, b)) for a, b in zip(P, PT))
            sides.append(AffineMovingPressureMetric.from_trace(trace(t+sign*dt)).evaluate(p, ZERO))
        difference = (sides[1]['kinetic_energy']-sides[0]['kinetic_energy'])/(2*dt)
        errors.append(abs(float(difference-result['kinetic_energy_rate'])))
        velocity_rate = (floats(sides[1]['canonical_velocity'])-floats(sides[0]['canonical_velocity']))/(2*float(dt))
    assert all(a/b > 3.8 for a, b in zip(errors, errors[1:]))
    assert errors[-1] < 2e-6
    np.testing.assert_allclose(velocity_rate, floats(result['canonical_velocity_rate']), rtol=2e-5, atol=2e-6)
    assert result['kinetic_energy_rate'] == result['momentum_work']+result['geometry_time_work']
    assert errors[-1] < abs(float(m.dot(m.vector(result['canonical_velocity']), m.offset_rate)))/100


def test_zero_trace_recovers_all_original_physical_quantities_exactly():
    g = trace().geometry
    original = MovingPressureMetric(g.volumes, g.volume_rates, g.kinetic, g.kinetic_rate)
    lifted = AffineMovingPressureMetric(g.volumes, g.volume_rates, g.kinetic, g.kinetic_rate, (0,)*4, (0,)*4, 0, 0)
    assert lifted.evaluate(P, PT) == original.evaluate(P, PT)
    assert lifted.physical_momentum(U) == original.physical_momentum(U)


@pytest.mark.parametrize('field', ('offset', 'offset_rate', 'dual_constant_rate'))
def test_missing_boundary_terms_cannot_pass_independent_reconstruction(field):
    m = AffineMovingPressureMetric.from_trace(trace())
    if field == 'dual_constant_rate':
        m.dual_constant_rate = m.zero
    else:
        setattr(m, field, (m.zero,)*4)
    with pytest.raises(ValueError, match='reconstruction|energy or time work'):
        m.evaluate(P, PT)


def test_subfloat_positive_mass_and_quadratic_field_are_not_dried_or_rounded():
    for mass in (F(1, 10**400), Radical(2, 2, 1)):
        c = mass*mass*mass
        # Positive exact square: C=diag(c,c), l=(c,-c), k=c.
        m = AffineMovingPressureMetric((mass,), (0,), ((c, 0), (0, c)), ((0, 0), (0, 0)),
                                      (c, -c), (0, 0), c, 0)
        v = ((F(2, 3), -F(1, 4)),)
        result = m.evaluate(m.physical_momentum(v), ((0, 0),))
        assert result['canonical_velocity'] == v and result['kinetic_energy'] > 0
        assert result['kinetic_energy_rate'] == 0
    dry = AffineMovingPressureMetric((), (), (), (), (), (), 0, 0)
    assert dry.evaluate((), ())['kinetic_energy'] == 0


def test_invalid_affine_shape_and_unbounded_or_negative_energy_rejected():
    base = ((1,), (0,), ((1, 0), (0, 0)), ((0, 0), (0, 0)))
    for linear, rate, constant in (((1,), (0, 0), 1), ((0, 0), (0,), 1),
                                   ((0, 0), (0, 0), -1), ((0, 1), (0, 0), 1),
                                   ((2, 0), (0, 0), 1)):
        with pytest.raises(ValueError):
            AffineMovingPressureMetric(*base, linear, rate, constant, 0)
