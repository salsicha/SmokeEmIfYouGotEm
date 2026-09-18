from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from scipy.integrate import quad

from subcell_affine_dry_fan import AffineDryFan
from subcell_front_auxiliary_transport import FrontAuxiliaryTransport
from subcell_front_profile_transport import (
    FrontProfileTransport, face_advection_moments, profile_depth_advection)
from test_subcell_affine_dry_fan import rectangle
from test_subcell_affine_front_pressure import fixture
from test_subcell_front_auxiliary_transport import U, V, independent_profile, volume_quad


def numerical_velocity(fan, time, point):
    n, slope, origin, u = (np.asarray(x, float) for x in
                           (fan.normal, fan.gradient, fan.origin, fan.velocity))
    g, t, h = float(fan.gravity), float(time), float(fan.depth)
    n2, un = n@n, n@u
    xi = n@(np.asarray(point)-origin)/t+g*(n@slope)*t/2
    c = np.sqrt(g*h*n2)
    if xi <= un-c:
        return u-g*slope*t
    if xi >= un+2*c:
        return np.zeros(2)
    return u-un*n/n2+n*(un+2*c+2*xi)/(3*n2)-g*slope*t


@pytest.mark.parametrize('normal', ((1, 0), (3, 4), (-2, 1)))
def test_signed_face_moments_quadrature_reversal_and_partition(normal):
    fan = AffineDryFan((0, 0), normal, F(3, 4), (F(2, 5), -F(1, 7)), 3, (F(1, 5), -F(1, 8)))
    xyz = lambda x, y: (x, y, fan.bed+fan.gradient[0]*x+fan.gradient[1]*y)
    a, b, t = xyz(-F(3, 2), -F(2, 5)), xyz(F(3, 2), F(1, 3)), F(1, 5)
    actual = face_advection_moments(fan, a, b, t)
    state, cuts, n, origin = independent_profile(fan, t)
    start, end = np.asarray(a[:2], float), np.asarray(b[:2], float)
    normal_measure = np.array((end[1]-start[1], start[0]-end[0]))
    q0, dq = n@(start-origin), n@(end-start)
    knots = [(q-q0)/dq for q in cuts if dq and 0 < (q-q0)/dq < 1]
    for k, value in enumerate(actual, 1):
        def integrand(s):
            p = start+s*(end-start)
            return state(p)[0]**k*(numerical_velocity(fan, t, p)@normal_measure)
        expected = quad(integrand, 0, 1, points=knots, epsabs=1e-12)[0]
        assert float(value) == pytest.approx(expected, abs=2e-13, rel=2e-13)
    assert actual == tuple(-v for v in face_advection_moments(fan, b, a, t))
    middle = tuple(x+F(2, 7)*(y-x) for x, y in zip(a, b))
    left, right = face_advection_moments(fan, a, middle, t), face_advection_moments(fan, middle, b, t)
    assert actual == tuple(x+y for x, y in zip(left, right))
    assert actual[0] == fan.face_flux(a, b, t)['volume_rate']


def test_connection_matches_independent_volume_quadrature_and_is_not_owner_mean():
    fan, fragments, t = fixture()
    op = FrontProfileTransport(fan, fragments, t, outer_boundary='reflecting')
    mean = FrontAuxiliaryTransport(fan, fragments, t, op.owner_mean_velocity, outer_boundary='reflecting')
    for i, fragment in enumerate(fragments):
        expected = volume_quad(fragment, independent_profile(fan, t),
            lambda x, y, h, ht, grad: h*(numerical_velocity(fan, t, (x, y))@grad))
        assert float(op.profile_depth_advection[i]) == pytest.approx(expected, abs=2e-12)
    assert op.connection != mean.connection
    assert any(a['matrix'] != b['matrix'] for a, b in zip(op.faces, mean.faces))


@pytest.mark.parametrize('method', ('factor_force', 'volume_factor_force', 'difference_force', 'time_commutator'))
def test_exact_skew_and_direct_ledgers_with_profile_transport(method):
    fan, fragments, t = fixture()
    op = FrontProfileTransport(fan, fragments, t, outer_boundary='reflecting')
    u, v = op.vector(U), op.vector(V)
    au, av = (op.vector(getattr(op, method)(w)) for w in (U, V))
    assert sum((a*b for a, b in zip(u, au)), op.zero) == 0
    assert sum((a*b+c*d for a, b, c, d in zip(v, au, u, av)), op.zero) == 0
    if method in ('factor_force', 'time_commutator'):
        assert getattr(op, method+'_ledger')(U).action() == op.pairs(au)


def test_common_conservative_receipts_match_analytic_mass_and_independent_time_differences():
    fan, fragments, t = fixture()
    op = FrontProfileTransport(fan, fragments, t, outer_boundary='reflecting')
    rates = op.shallow_water_rates()
    assert rates['volume_rate'] == op.geometry.volume_rates
    dt = F(1, 100000)
    for i, fragment in enumerate(fragments):
        before, after = (fan.integrate(fragment, at) for at in (t-dt, t+dt))
        for axis in range(2):
            expected = float((after['momentum'][axis]-before['momentum'][axis])/(2*dt))
            assert float(rates['momentum_rate'][i][axis]) == pytest.approx(expected, abs=2e-8)
        expected = float((after['energy_per_density']-before['energy_per_density'])/(2*dt))
        assert float(rates['energy_rate_per_density'][i]) == pytest.approx(expected, abs=3e-7)
    for axis in range(2):
        assert sum((m[axis] for m in rates['momentum_rate']), op.zero) == (
            sum((m[axis] for m in rates['bed_force']), op.zero)
            -sum((f['momentum_rate'][axis] for f in rates['exterior_faces']), op.zero))
    assert sum(rates['volume_rate'], op.zero) == -sum(
        (f['volume_rate'] for f in rates['exterior_faces']), op.zero)
    for face in op.faces:
        common, = [f for f in op.profile_faces if f['owners'] == face['owners']
                   and f['first'] == face['first'] and f['last'] == face['last']]
        assert face['mass_flux'] == common['volume_rate']
    assert not rates['coupled_dispersive_or_open_pressure_or_gameplay_accepted']


def test_hanging_edges_reversal_and_dry_owner_do_not_change_receipts():
    fan = AffineDryFan((0, 0), (1, 0), 1, (0, 0), 0, (0, 0))
    fragments = (rectangle(x0=-1, x1=0), rectangle(x0=0, x1=1, y0=-1, y1=0),
                 rectangle(x0=0, x1=1, y0=0, y1=1), rectangle(x0=4, x1=5))
    first = FrontProfileTransport(fan, fragments, F(1, 5), outer_boundary='reflecting')
    second = FrontProfileTransport(fan, tuple(replace(f, polygon=tuple(reversed(f.polygon))) for f in fragments),
                                   F(1, 5), outer_boundary='reflecting')
    assert first.geometry.active == (0, 1, 2)
    assert first.shallow_water_rates() == second.shallow_water_rates()
    assert first.shallow_water_rates()['volume_rate'][3] == 0
    assert first.shallow_water_rates()['momentum_rate'][3] == (0, 0)
    assert first.factor_force(first.owner_mean_velocity) == second.factor_force(second.owner_mean_velocity)


def test_energy_datum_shift_is_exact_mass_work_not_an_energy_reset():
    fan, fragments, t = fixture()
    a = FrontProfileTransport(fan, fragments, t, outer_boundary='reflecting').shallow_water_rates()
    datum = F(1723, 100)
    b = FrontProfileTransport(fan, fragments, t, outer_boundary='reflecting', energy_datum=datum).shallow_water_rates()
    assert a['momentum_rate'] == b['momentum_rate']
    assert a['volume_rate'] == b['volume_rate']
    assert tuple(y-x for x, y in zip(a['energy_rate_per_density'], b['energy_rate_per_density'])) == tuple(
        -fan.gravity*datum*m for m in a['volume_rate'])


def test_uniform_depth_and_dry_regions_have_no_spatial_connection():
    fan = AffineDryFan((0, 0), (1, 0), 1, (0, 0), 2, (F(1, 5), -F(1, 7)))
    for low, high in ((-3, -2), (4, 5)):
        f = rectangle(x0=low, x1=high, bed=2, slope=fan.gradient)
        assert profile_depth_advection(fan, f, F(1, 10)) == 0


def test_positive_subfloat_front_strip_is_not_deleted_or_averaged():
    fan = AffineDryFan((0, 0), (1, 0), 1, (0, 0), 0, (0, 0), gravity=1)
    t, epsilon = F(1, 10), F(1, 10**400)
    front = 2*t
    fragment = rectangle(x0=front-epsilon, x1=front, y0=0, y1=1)
    op = FrontProfileTransport(fan, (fragment,), t, outer_boundary='reflecting')
    assert op.geometry.active == (0,)
    assert op.geometry.volumes[0] > 0
    assert float(op.geometry.volumes[0]) == 0
    a, b = (front-epsilon, F(0), F(0)), (front-epsilon, F(1), F(0))
    assert all(m > 0 for m in face_advection_moments(fan, a, b, t))
    assert op.profile_depth_advection[0] < 0
    assert op.shallow_water_rates()['volume_rate'][0] > 0


def test_invalid_time_bed_and_open_pressure_are_rejected():
    fan, fragments, t = fixture()
    with pytest.raises(ValueError):
        FrontProfileTransport(fan, fragments, t, outer_boundary='open')
    for at in (0, -1):
        with pytest.raises(ValueError):
            profile_depth_advection(fan, fragments[0], at)
    with pytest.raises(ValueError):
        profile_depth_advection(fan, replace(fragments[0], gradient=(0, 0)), t)
