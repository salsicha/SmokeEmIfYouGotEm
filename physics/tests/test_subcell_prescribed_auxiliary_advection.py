from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from scipy.integrate import quad

from subcell_affine_dry_fan import AffineDryFan
from subcell_prescribed_auxiliary_advection import PrescribedAuxiliaryAdvection
from test_subcell_affine_dry_fan import rectangle
from test_subcell_affine_front_pressure import fixture
from test_subcell_front_auxiliary_transport import U, V, independent_profile
from test_subcell_front_profile_transport import numerical_velocity


def make(fan=None, fragments=None, time=None):
    if fan is None:
        fan, fragments, time = fixture()
    return PrescribedAuxiliaryAdvection(fan, fragments, time,
                                        boundary='prescribed-fan-velocity')


def dot(a, b, zero):
    assert len(a) == len(b)
    return sum((x*y for x, y in zip(a, b)), zero)


def quadrature(fan, t, face, ju, jv, channel):
    """Independent pointwise factors, not the implementation's moment matrix."""
    profile, cuts, n, origin = independent_profile(fan, t)
    a, b = np.array(face['first'][:2], float), np.array(face['last'][:2], float)
    normal = np.array((b[1]-a[1], a[0]-b[0]))
    q0, dq = n@(a-origin), n@(b-a)
    knots = [(q-q0)/dq for q in cuts if dq and 0 < (q-q0)/dq < 1]
    bu, bv = (np.array(fan.gradient, float)@np.array(j[1:], float) for j in (ju, jv))
    def integrand(s):
        p = a+s*(b-a)
        h = profile(p)[0]
        product = ((h*float(ju[0])-1.5*bu)*(h*float(jv[0])-1.5*bv)+.75*bu*bv
                   if channel == 'factor' else float(ju[1]*jv[1]+ju[2]*jv[2]))
        return h*(numerical_velocity(fan, t, p)@normal)*product
    return quad(integrand, 0, 1, points=knots, epsabs=1e-12)[0]


@pytest.mark.parametrize('channel', ('factor', 'difference'))
def test_signed_per_face_work_and_bilinear_green_identity_match_quadrature(channel):
    fan, fragments, t = fixture(); op = make(fan, fragments, t); c = op.connections
    qu, qv = c.fluxes, tuple(F(i+1, 17) for i in range(len(c.fluxes)))
    ru, rv = op.apply(U, qu, channel=channel), op.apply(V, qv, channel=channel)
    assert op.apply(U, channel=channel) == ru
    assert not ru['inflow_or_radiation_or_coupled_pde_or_gameplay_accepted']
    assert ru['spatial_operator_rhs_sign'] == -1
    u, v = c.state(U, qu), c.state(V, qv)
    expected = 0.
    exact_boundary_pairing = c.zero
    for fu, fv in zip(ru['faces'], rv['faces']):
        expected += quadrature(fan, t, fu, fu['jet'], fv['jet'], channel)
        exact_boundary_pairing += dot(fv['jet'], fu['jet_action'], c.zero)
        exact_boundary_pairing += dot(fu['jet'], fv['jet_action'], c.zero)
        actual = fu['outward_auxiliary_energy_flux']
        assert float(actual) == pytest.approx(
            quadrature(fan, t, fu, fu['jet'], fu['jet'], channel)/2, abs=3e-12)
    actual = dot(v, ru['augmented_action'], c.zero)+dot(u, rv['augmented_action'], c.zero)
    assert actual == exact_boundary_pairing
    assert float(actual) == pytest.approx(expected, abs=3e-11)
    assert dot(u, ru['augmented_action'], c.zero) == ru['outward_auxiliary_energy_flux']
    assert ru['interior_work']+ru['flux_coordinate_work'] == ru['outward_auxiliary_energy_flux']
    values = [f['outward_auxiliary_energy_flux'] for f in ru['faces']]
    assert any(x < 0 for x in values) and any(x > 0 for x in values)
    if channel == 'factor':
        assert ru['flux_coordinate_work'] != 0
    else:
        assert ru['flux_coordinate_work'] == 0


@pytest.mark.parametrize('channel', ('factor', 'difference'))
def test_exterior_action_is_half_gradient_of_signed_quadratic_not_residual_fitted(channel):
    op = make(); c = op.connections
    u, v = c.state(U), c.state(V, tuple(F(i+1, 19) for i in range(len(c.fluxes))))
    def split(state):
        return c.profile.pairs(state[:c.velocity_size]), state[c.velocity_size:]
    plus = tuple(a+b for a, b in zip(u, v)); minus = tuple(a-b for a, b in zip(u, v))
    fp = op.exterior(*split(plus), channel=channel)['outward_auxiliary_energy_flux']
    fm = op.exterior(*split(minus), channel=channel)['outward_auxiliary_energy_flux']
    action = op.exterior(U, channel=channel)['augmented_action']
    assert (fp-fm)/4 == dot(v, action, c.zero)
    # The independently retained skew operator is exactly the ONLY difference.
    full = op.apply(U, channel=channel)['augmented_action']
    if channel == 'factor':
        old = c.factor_connection(U)['augmented_action']
    else:
        old = c.profile.vector(c.profile.difference_force(U))+(c.zero,)*len(c.fluxes)
    assert tuple(a-b for a, b in zip(full, action)) == old


@pytest.mark.parametrize('channel', ('factor', 'difference'))
def test_winding_hanging_edges_and_subdivided_exterior_preserve_physical_work(channel):
    fan = AffineDryFan((0, 0), (1, 0), 1, (F(1, 3), F(1, 7)), 0, (0, 0))
    fragments = (rectangle(x0=-1, x1=0), rectangle(x0=0, x1=1, y0=-1, y1=0),
                 rectangle(x0=0, x1=1, y0=0, y1=1), rectangle(x0=4, x1=5))
    t = F(1, 5); velocity = (U[0], U[1], V[0])
    op = make(fan, fragments, t)
    reversed_op = make(fan, tuple(replace(f, polygon=tuple(reversed(f.polygon))) for f in fragments), t)
    first = op.apply(velocity, channel=channel)
    assert first == reversed_op.apply(velocity, channel=channel)
    assert op.connections.geometry.active == (0, 1, 2)
    # Split an actual source edge without splitting its owner/velocity space.
    a, b, *rest = fragments[0].polygon
    middle = tuple((x+y)/2 for x, y in zip(a, b))
    subdivided = (replace(fragments[0], polygon=(a, middle, b, *rest)), *fragments[1:])
    second = make(fan, subdivided, t).apply(velocity, channel=channel)
    assert first['velocity_action'] == second['velocity_action']
    assert first['outward_auxiliary_energy_flux'] == second['outward_auxiliary_energy_flux']
    assert first['flux_coordinate_work'] == second['flux_coordinate_work']


@pytest.mark.parametrize('channel', ('factor', 'difference'))
def test_positive_subfloat_water_and_dry_owners_are_not_zeroed(channel):
    fan = AffineDryFan((0, 0), (1, 0), 1, (0, 0), 0, (0, 0), gravity=1)
    t, epsilon = F(1, 10), F(1, 10**400)
    wet = rectangle(x0=2*t-epsilon, x1=2*t, y0=0, y1=1)
    dry = rectangle(x0=4, x1=5)
    op = make(fan, (wet, dry), t)
    assert op.connections.geometry.active == (0,)
    result = op.apply((U[0],), channel=channel)
    assert result['outward_auxiliary_energy_flux'] != 0
    assert float(result['outward_auxiliary_energy_flux']) == 0
    empty = make(fan, (dry,), t).apply((), channel=channel)
    assert empty['faces'] == empty['augmented_action'] == ()
    assert empty['outward_auxiliary_energy_flux'] == 0


@pytest.mark.parametrize('channel', ('factor', 'difference'))
def test_zero_advecting_trace_has_no_exterior_work(channel):
    # Stationary wet plateau; probe velocities do NOT redefine transport.
    fan = AffineDryFan((0, 0), (1, 0), 1, (0, 0), 0, (0, 0), gravity=1)
    op = make(fan, (rectangle(x0=-3, x1=-2),), F(1, 10))
    result = op.exterior((U[0],), channel=channel)
    assert all(x == 0 for x in result['augmented_action'])
    assert result['outward_auxiliary_energy_flux'] == 0


def test_invalid_channel_boundary_velocity_and_flux_dimensions_fail_closed():
    fan, fragments, t = fixture(); op = make(fan, fragments, t)
    with pytest.raises(ValueError):
        PrescribedAuxiliaryAdvection(fan, fragments, t, boundary='radiation')
    for channel in ('', 'factor+difference', None):
        with pytest.raises(ValueError):
            op.apply(U, channel=channel)
    for bad in ((), (U[0],), ((float('nan'), 0), U[1])):
        with pytest.raises(ValueError):
            op.apply(bad, channel='factor')
    for bad in ((), (0,)*(len(op.connections.fluxes)+1),
                (float('inf'),)*len(op.connections.fluxes)):
        with pytest.raises(ValueError):
            op.apply(U, bad, channel='factor')


def test_both_original_pressure_poles_keep_signed_exterior_and_port_work():
    from subcell_affine_moving_pressure import AffineMovingPressureMetric
    op = make(); c = op.connections
    metric = AffineMovingPressureMetric.from_trace(c.trace)
    state = metric.evaluate(metric.physical_momentum(U), ((0, 0), (0, 0)))
    assert len(state['poles']) == 2
    for pole in state['poles']:
        assert pole['exact_residual_zero']
        for channel in ('factor', 'difference'):
            result = op.apply(pole['auxiliary_velocity'], channel=channel)
            assert result['interior_work']+result['flux_coordinate_work'] == result['outward_auxiliary_energy_flux']
